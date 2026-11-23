import datetime
import enum
import typing as t
from collections import abc

import pydantic
from cryptography.hazmat.primitives.asymmetric import ec

type VerificationKeyType = ec.EllipticCurvePublicKey


class DiscoverMode(enum.StrEnum):
    JWKS_URL = 'jwks_url'
    METADATA_URL = 'metadata_url'
    NONE = 'none'


class TrustedIssuer(pydantic.BaseModel):
    """Which issues do we trust and where are their keys?"""

    issuer: str
    discovery_mode: DiscoverMode = DiscoverMode.NONE
    key_retrieval_url: str | None = None


class VerificationKey(pydantic.BaseModel):
    """Parsed public key material and metadata"""

    kid: str
    issuer: str
    key: VerificationKeyType

    @pydantic.computed_field
    @property
    def jwt_thumbprint(self) -> str:
        """Thumbprint of the key as defined in RFC7638"""
        return 'TODO'


class KeySnapshot(pydantic.BaseModel):
    """Snapshot of keys from a specific trusted issuer"""

    issuer: str
    keys: list[VerificationKey]
    retrieved_at: datetime.datetime
    valid_until: datetime.datetime
    retrieved_from: str


class KeyProvider(t.Protocol):
    """Runtime provider for key information"""

    async def get_candidates(
        self, issuer: str, kid: str, alg: str
    ) -> abc.Iterable[VerificationKey]: ...
