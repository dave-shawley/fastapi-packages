import base64
import contextlib
import typing as t
from collections import abc

import fastapi

import fastapi_runner.lifespan
from tutorial_auth_server import config, types

router = fastapi.APIRouter()


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode('ascii').rstrip('=')


class _KeySetState:
    def __init__(self) -> None:
        self.keys: dict[str, types.SupportKeyTypes] = {}

    def add_key(self, key: types.SupportKeyTypes) -> None:
        self.keys = {key.kid: key}

    def __getitem__(self, kid: str) -> types.SupportKeyTypes:
        return self.keys[kid].model_copy()


@contextlib.asynccontextmanager
async def keyset_lifespan() -> abc.AsyncGenerator[_KeySetState]:
    settings = config.AuthSettings()
    state = _KeySetState()
    state.add_key(settings.signing_key)
    yield state


def _get_keyset(
    lifespan_map: fastapi_runner.lifespan.LifespanMap,
) -> _KeySetState:
    return lifespan_map.get_state(keyset_lifespan)


type KeySet = t.Annotated[_KeySetState, fastapi.Depends(_get_keyset)]


@router.get('/jwks.json', name='jwks', summary='RFC7517 JSON Web Key Set')
async def get_keyset(keyset: KeySet) -> types.JWKSet:
    return types.JWKSet.model_validate({'keys': list(keyset.keys.values())})
