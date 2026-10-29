import contextlib
import typing as t
from collections import abc

import fastapi

import fastapi_runner.lifespan


class DatabaseState:
    def __init__(self) -> None:
        self.connected = False

    def connect(self) -> None:
        self.connected = True

    def close(self) -> None:
        self.connected = False


@contextlib.asynccontextmanager
async def database_lifespan(
    _app: fastapi.FastAPI,
) -> abc.AsyncGenerator[DatabaseState]:
    database = DatabaseState()
    database.connect()
    try:
        yield database
    finally:
        database.close()


def get_database(
    lifespan: fastapi_runner.lifespan.LifespanMap,
) -> DatabaseState:
    return lifespan.get_state(database_lifespan)


# See https://fastapi.tiangolo.com/tutorial/dependencies/#share-annotated-dependencies
Database = t.Annotated[DatabaseState, fastapi.Depends(get_database)]


def lifespans() -> abc.Generator[fastapi_runner.lifespan.LifespanHook]:
    yield database_lifespan


def status(*, db: Database) -> dict[str, dict[str, bool]]:
    return {'db': {'connected': db.connected}}


def configure(app: fastapi.FastAPI) -> None:
    app.add_api_route('/status', status)
