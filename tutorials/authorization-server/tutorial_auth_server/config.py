import base64
import functools
import json
import typing as t
import urllib.parse

import pydantic
import pydantic_settings
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

from tutorial_auth_server import types


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode('ascii').rstrip('=')


class AuthSettings(pydantic_settings.BaseSettings):
    model_config = {
        'env_prefix': 'AUTH_',
        'secrets_dir': ['/var/run/secrets', 'runtime/secrets'],
    }
    key: pydantic.SecretStr
    issuer: str = 'http://127.0.0.1:8000'
    resource: str = 'https://example.com/api'
    client_id: str = 'tutorial-client-id'
    client_secret: pydantic.SecretStr = pydantic.SecretStr(
        'not a great secret'
    )
    access_token_leeway_seconds: t.Annotated[
        int, pydantic.Field(ge=0, lt=300)
    ] = 60
    access_token_lifetime: t.Annotated[
        int, pydantic.Field(ge=300, lt=86400)
    ] = 3600

    @pydantic.field_validator('issuer', mode='after')
    @classmethod
    def validate_issuer(cls, value: str) -> str:
        """Implementation does not allow for an issuer path"""
        parsed = urllib.parse.urlparse(value)
        if parsed.scheme not in ('http', 'https'):
            raise ValueError('issuer must be an HTTP/HTTPS URL')
        if parsed.path not in ('', '/'):
            raise ValueError('issuer must not have a path')
        return value.rstrip('/')

    @pydantic.computed_field
    @functools.cached_property
    def signing_key(self) -> types.SupportKeyTypes:
        """JWK representation of the signing key"""
        key = serialization.load_pem_private_key(
            self.key.get_secret_value().encode('ascii'), password=None
        )
        match key:
            case ec.EllipticCurvePrivateKey():
                pub_key = key.public_key()
                numbers = pub_key.public_numbers()
                jwk = {
                    'crv': f'P-{pub_key.key_size}',
                    'kty': 'EC',
                    'x': _b64url(numbers.x.to_bytes(32, 'big')),
                    'y': _b64url(numbers.y.to_bytes(32, 'big')),
                }
                canonical = json.dumps(
                    jwk, sort_keys=True, separators=(',', ':')
                ).encode('utf-8')
                digest = hashes.Hash(hashes.SHA256())
                digest.update(canonical)
                kid = _b64url(digest.finalize())
                return types.EllipticalCurveKey.model_validate(
                    {'kid': kid, 'use': 'sig', **jwk}
                )
            case _ as unexpected:
                raise RuntimeError(f'Unexpected key type: {unexpected!r}')
