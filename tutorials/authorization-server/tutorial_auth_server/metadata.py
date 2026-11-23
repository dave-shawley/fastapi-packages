import fastapi
import pydantic

import fastapi_runner.types
import tutorial_auth_server.config

router = fastapi.APIRouter()


class ServerMetadata(pydantic.BaseModel):
    issuer: str
    authorization_endpoint: fastapi_runner.types.StarletteUrl
    token_endpoint: fastapi_runner.types.StarletteUrl
    jwks_uri: fastapi_runner.types.StarletteUrl
    response_types_supported: list[str]
    scopes_supported: list[str]
    token_endpoint_auth_signing_alg_values_supported: list[str]
    token_endpoint_auth_methods_supported: list[str]


@router.get(
    '/.well-known/oauth-authorization-server',
    name='authorization-server-metadata',
    summary='RFC-8414 authorization server metadata',
)
async def auth_server_metadata(request: fastapi.Request) -> ServerMetadata:
    settings = tutorial_auth_server.config.AuthSettings()
    return ServerMetadata.model_validate(
        {
            'issuer': settings.issuer,
            'authorization_endpoint': request.url_for('oauth2-authorize'),
            'token_endpoint': request.url_for('oauth2-token'),
            'jwks_uri': request.url_for('jwks'),
            'response_types_supported': ['code'],
            'scopes_supported': [],
            'token_endpoint_auth_signing_alg_values_supported': ['ES256'],
            'token_endpoint_auth_methods_supported': ['client_secret_basic'],
        }
    )
