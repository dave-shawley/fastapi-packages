import contextlib
import logging
import typing as t

import fastapi.security
import jwt
import jwt.types
import pydantic_settings

import fastapi_runner.lifespan
import fastapi_runner.state


def _require_str(value: object) -> str:
    if isinstance(value, str):
        return value
    raise TypeError(f'str expected, found {type(value)}')


class AuthSettings(pydantic_settings.BaseSettings):
    model_config = {'secrets_dir': ['/var/run/secrets', 'runtime/secrets']}
    auth_key: str
    auth_audience: str | None = None
    auth_leeway: float = 0


class JWTClaims:
    def __init__(self, claims: dict[str, object]) -> None:
        scope = claims.get('scope', '')
        if not isinstance(scope, str):
            raise TypeError(f'scope must be a string, found {type(scope)}')
        self.principal = _require_str(claims['sub'])
        self.scopes = scope.split(' ')
        self.claims = claims


bearer_scheme = fastapi.security.OAuth2AuthorizationCodeBearer(
    authorizationUrl='auth', tokenUrl='token'
)


class AuthState:
    def __init__(self, settings: AuthSettings) -> None:
        self.verification_key = settings.auth_key
        self.audience: list[str] | None = None
        self.jwt_options: jwt.types.Options = {
            'require': ['exp', 'iat', 'sub'],
            'verify_exp': True,
            'verify_iat': True,
        }
        if settings.auth_audience:
            self.jwt_options['require'].append('aud')
            self.jwt_options['verify_aud'] = True
            self.audience = [settings.auth_audience]


@contextlib.asynccontextmanager
async def auth_lifespan() -> t.AsyncGenerator[AuthState]:
    cfg = AuthSettings()
    state = AuthState(cfg)
    try:
        yield state
    finally:
        pass


def authenticate(
    lifespan: fastapi_runner.lifespan.LifespanMap,
    token: t.Annotated[str, fastapi.Depends(bearer_scheme)],
    request: fastapi.Request,
) -> JWTClaims:
    state = lifespan.get_state(auth_lifespan)
    try:
        decoded = jwt.decode(
            token,
            state.verification_key,
            algorithms=['ES256'],
            audience=state.audience,
            options=state.jwt_options,
        )
    except jwt.exceptions.InvalidTokenError as err:
        logger = logging.getLogger(__name__).getChild('authenticate')
        logger.warning('Ignoring token: %s', err)
        raise bearer_scheme.make_not_authenticated_error() from None

    claims = JWTClaims(decoded)
    fastapi_runner.state.set_principal_id(claims.principal, request=request)
    return claims


AuthenticatedClaims = t.Annotated[
    JWTClaims,
    fastapi.Depends(bearer_scheme),
    fastapi.Depends(authenticate),
]
