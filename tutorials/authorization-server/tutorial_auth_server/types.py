import enum
import typing as t

import pydantic


class _KeyUse(enum.StrEnum):
    """https://www.rfc-editor.org/info/rfc7517/#section-4.2"""

    SIG = 'sig'
    ENC = 'enc'


class KeyMetadata[Kty: str](pydantic.BaseModel):
    kid: str
    kty: Kty
    use: _KeyUse


class EllipticalCurveKey(KeyMetadata[t.Literal['EC']]):
    x: str
    y: str
    crv: str


class RSAKey(KeyMetadata[t.Literal['RSA']]):
    pass


SupportKeyTypes = t.Annotated[
    EllipticalCurveKey | RSAKey, pydantic.Field(discriminator='kty')
]


class JWKSet(pydantic.BaseModel):
    keys: list[SupportKeyTypes]


class AccessTokenPayload(pydantic.BaseModel):
    iss: str
    exp: int
    aud: list[str]
    sub: str
    client_id: str
    iat: int
    jti: str
    scope: str
