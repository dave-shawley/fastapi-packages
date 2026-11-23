import pathlib

import pydantic
import pydantic_settings

from fastapi_oauth_jwt import types


class Settings(pydantic.BaseModel):
    trusted_issuers: list[types.TrustedIssuer] = []


class EnvSettings(pydantic_settings.BaseSettings):
    model_config = {
        'env_prefix': 'FASTAPI_OAUTH_JWT_',
    }
    trusted_issuer_fils: list[pathlib.Path]
