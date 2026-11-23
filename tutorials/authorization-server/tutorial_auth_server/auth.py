import base64
import contextlib
import datetime
import enum
import secrets
import time
import typing as t
import uuid
from collections import abc

import fastapi
import jwt
import pydantic
import starlette.datastructures
import starlette.responses

import fastapi_runner.lifespan
import fastapi_runner.types
import tutorial_auth_server.config
import tutorial_auth_server.keys
import tutorial_auth_server.types

router = fastapi.APIRouter(prefix='/oauth2')

type AuthCode = str
type ClientState = str
type AccessToken = str
type RefreshToken = str
type ClientId = str


@pydantic.dataclasses.dataclass()
class _ClientInfo:
    client_id: ClientId
    client_secret: pydantic.SecretStr
    redirect_uri: fastapi_runner.types.StarletteUrl


@pydantic.dataclasses.dataclass()
class _AuthCodeState:
    code: AuthCode
    state: ClientState | None
    requested_scopes: str
    requested_resource: str
    redirect_uri: fastapi_runner.types.StarletteUrl
    client_id: ClientId


class _TokenInfo(pydantic.BaseModel):
    access_token: AccessToken
    refresh_token: RefreshToken
    expires_in: int


class _Token:
    def __init__(self, requested_scopes: str, requested_resource: str) -> None:
        self.access_token = self._create_access_token(
            audience=requested_resource,
            scopes=[s.strip() for s in requested_scopes.split()],
        )
        self.refresh_token = secrets.token_urlsafe(32)
        self.scopes = [s.strip() for s in requested_scopes.split()]
        self.expiration = datetime.datetime.now(
            datetime.UTC
        ) + datetime.timedelta(minutes=10)

    def _create_access_token(
        self, *, audience: str, scopes: list[str]
    ) -> AccessToken:
        now = int(time.time())
        settings = tutorial_auth_server.config.AuthSettings()
        token_data = tutorial_auth_server.types.AccessTokenPayload(
            iss=settings.issuer,
            exp=(
                now
                + settings.access_token_lifetime
                + settings.access_token_leeway_seconds
            ),
            aud=[audience],
            sub='the-authorized-user',
            client_id=settings.client_id,
            iat=(now - settings.access_token_leeway_seconds),
            jti=str(uuid.uuid4()),
            scope=' '.join(scopes),
        )
        metadata = settings.signing_key
        return jwt.encode(
            token_data.model_dump(mode='python'),
            key=settings.key.get_secret_value(),
            algorithm=('ES256' if metadata.kty == 'EC' else 'RS256'),
            headers={'kid': metadata.kid, 'typ': 'at+jwt'},
        )

    @property
    def expires_in(self) -> int:
        secs = (
            self.expiration - datetime.datetime.now(datetime.UTC)
        ).total_seconds()
        if secs < 0:
            return 0
        return int(secs)

    def info(self) -> _TokenInfo:
        return _TokenInfo(
            access_token=self.access_token,
            refresh_token=self.refresh_token,
            expires_in=self.expires_in,
        )


class AuthServerState:
    def __init__(self, issuer: str, resource: str) -> None:
        self._issuer = issuer
        self._resource = resource
        self._client_info: dict[str, _ClientInfo] = {}
        self._auth_codes: dict[AuthCode, _AuthCodeState] = {}
        self._tokens: dict[AccessToken, _Token] = {}

    @property
    def issuer(self) -> str:
        return self._issuer

    @property
    def resource(self) -> str:
        return self._resource

    def add_client_info(
        self,
        client_id: ClientId,
        client_secret: str,
        redirect_uri: fastapi_runner.types.StarletteUrl,
    ) -> None:
        if client_id in self._client_info:
            raise RuntimeError(f'Client {client_id} is already registered')
        self._client_info[client_id] = _ClientInfo(
            client_id,
            client_secret,
            redirect_uri,
        )

    def generate_auth_code(
        self,
        client_id: str,
        requested_scopes: str,
        redirect_uri: str,
        state: ClientState | None,
        requested_resource: str,
    ) -> AuthCode:
        try:
            client_info = self._client_info[client_id]
        except KeyError:
            raise OAuth2Error(
                400,
                OAuthErrorCode.unauthorized_client,
                'Invalid client ID',
                state,
            ) from None
        if redirect_uri != str(client_info.redirect_uri):
            raise OAuth2Error(
                400,
                OAuthErrorCode.invalid_request,
                'Invalid redirect URI',
                state,
            ) from None

        code = secrets.token_urlsafe(32)
        self._auth_codes[code] = _AuthCodeState(
            client_id=client_info.client_id,
            code=code,
            state=state,
            requested_scopes=requested_scopes,
            requested_resource=requested_resource,
            redirect_uri=client_info.redirect_uri,
        )
        return code

    def redeem_auth_code(
        self,
        client_id: str,
        client_secret: pydantic.SecretStr,
        code: AuthCode,
        redirect_uri: starlette.datastructures.URL,
        requested_resource: str | None,
    ) -> _TokenInfo:
        try:
            auth_state = self._auth_codes.pop(code)
        except KeyError:
            raise OAuth2Error(
                status=400,
                error=OAuthErrorCode.invalid_request,
                description='Invalid auth code',
                state=None,
            ) from None

        if redirect_uri != auth_state.redirect_uri:
            raise OAuth2Error(
                status=400,
                error=OAuthErrorCode.invalid_request,
                description='Invalid redirect URI',
                state=None,
            ) from None
        if client_id != auth_state.client_id:
            raise OAuth2Error(
                status=400,
                error=OAuthErrorCode.unauthorized_client,
                description='Invalid client information',
                state=None,
            ) from None

        client = self._client_info[client_id]
        if client_secret != client.client_secret:
            raise OAuth2Error(
                status=400,
                error=OAuthErrorCode.unauthorized_client,
                description='Invalid client information',
                state=None,
            ) from None

        if (
            requested_resource
            and requested_resource != auth_state.requested_resource
        ):
            raise OAuth2Error(
                status=400,
                error=OAuthErrorCode.invalid_target,
                description='Invalid requested resource',
                state=None,
            ) from None

        new_token = _Token(
            requested_scopes=auth_state.requested_scopes,
            requested_resource=auth_state.requested_resource,
        )
        self._tokens[new_token.access_token] = new_token

        return self._tokens[new_token.access_token].info()


@contextlib.asynccontextmanager
async def auth_server_lifespan() -> abc.AsyncGenerator[AuthServerState]:
    config = tutorial_auth_server.config.AuthSettings()
    state = AuthServerState(config.issuer, config.resource)
    state.add_client_info(
        config.client_id,
        config.client_secret.get_secret_value(),
        starlette.datastructures.URL('https://example.com/oauth/redirect'),
    )
    yield state


class OAuthErrorCode(enum.StrEnum):
    invalid_request = 'invalid_request'
    unauthorized_client = 'unauthorized_client'
    access_denied = 'access_denied'
    unsupported_response_type = 'unsupported_response_type'
    invalid_scope = 'invalid_scope'
    server_error = 'server_error'
    temporary_unavailable = 'temporary_unavailable'
    invalid_target = 'invalid_target'


class OAuth2Error(fastapi.HTTPException):
    def __init__(
        self,
        status: int,
        error: OAuthErrorCode,
        description: str,
        state: str | None,
    ) -> None:
        super().__init__(status_code=status, detail=description)
        self.error = error
        self.error_description = description
        self.state = state


@router.get(
    '/authorize',
    name='oauth2-authorize',
    summary='OAuth 2 authorization endpoint',
)
async def authorize(  # noqa: PLR0913 PLR0917
    response_type: str,
    client_id: str,
    redirect_uri: str,
    scope: str,
    state: ClientState | None = None,
    resource: str | None = None,
    *,
    lifespan_map: fastapi_runner.lifespan.LifespanMap,
) -> fastapi.Response:
    state_data = lifespan_map.get_state(auth_server_lifespan)

    if response_type != 'code':
        raise OAuth2Error(
            400,
            OAuthErrorCode.unsupported_response_type,
            'Only "code" response type is supported',
            state,
        )
    if resource and resource != state_data.resource:
        raise OAuth2Error(
            400,
            OAuthErrorCode.invalid_target,
            'Invalid resource',
            state,
        )

    code = state_data.generate_auth_code(
        client_id,
        scope,
        redirect_uri=redirect_uri,
        requested_resource=state_data.resource,
        state=state,
    )
    redir_url = starlette.datastructures.URL(redirect_uri)
    redir_url = redir_url.remove_query_params(('code', 'state'))
    redir_url = redir_url.include_query_params(code=code)
    if state is not None:
        redir_url = redir_url.include_query_params(state=state)

    return starlette.responses.RedirectResponse(url=str(redir_url))


class TokenRequest(pydantic.BaseModel):
    grant_type: str
    code: str
    redirect_uri: fastapi_runner.types.StarletteUrl
    resource: str | None = None


@router.post('/token', name='oauth2-token', summary='OAuth 2 token endpoint')
async def token(
    request: fastapi.Request,
    *,
    auth: t.Annotated[
        str | None, fastapi.Header(alias='Authorization')
    ] = None,
    lifespan_map: fastapi_runner.lifespan.LifespanMap,
) -> fastapi.Response:
    state_data = lifespan_map.get_state(auth_server_lifespan)
    if auth is None or not auth.startswith('Basic '):
        challenge = f'Basic realm="oauth", issuer="{state_data.issuer}"'
        raise fastapi.HTTPException(
            status_code=401,
            headers={'www-authenticate': challenge},
        )
    decoded = base64.b64decode(auth[6:]).decode()
    client_id, client_secret = decoded.split(':')

    form_data = await request.form()
    token_request = TokenRequest.model_validate(form_data)
    if token_request.grant_type != 'authorization_code':
        raise OAuth2Error(
            400,
            OAuthErrorCode.invalid_request,
            'Unsupported grant type',
            None,
        )

    token = state_data.redeem_auth_code(
        client_id,
        pydantic.SecretStr(client_secret),
        token_request.code,
        redirect_uri=token_request.redirect_uri,
        requested_resource=token_request.resource,
    )
    return fastapi.Response(
        content=token.model_dump_json().encode('utf-8'),
        headers={'content-type': 'application/at+jwt'},
    )
