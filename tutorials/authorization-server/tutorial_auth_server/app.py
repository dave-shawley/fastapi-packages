import contextlib
from collections import abc

import fastapi

import fastapi_runner.lifespan
from tutorial_auth_server import auth, keys, metadata


class ServerState: ...


@contextlib.asynccontextmanager
async def server_lifespan(
    _app: fastapi.FastAPI,
) -> abc.AsyncGenerator[ServerState]:
    yield ServerState()


def lifespans() -> abc.Generator[fastapi_runner.lifespan.LifespanHook]:
    yield from [
        server_lifespan,
        auth.auth_server_lifespan,
        keys.keyset_lifespan,
    ]


def configure(app: fastapi.FastAPI) -> None:
    app.include_router(auth.router)
    app.include_router(keys.router)
    app.include_router(metadata.router)
