import contextlib
import datetime
import logging
import typing as t
from collections import abc

import fastapi.security
import pydantic

import example.auth
import fastapi_runner.lifespan

Status = t.Literal['running', 'starting', 'stopping']


class State(pydantic.BaseModel):
    status: Status = 'starting'
    started: datetime.datetime


def _get_state(*, span: fastapi_runner.lifespan.LifespanMap) -> State:
    return span.get_state(state_lifespan)


def status(*, state: t.Annotated[State, fastapi.Depends(_get_state)]) -> State:
    return state


@contextlib.asynccontextmanager
async def state_lifespan() -> abc.AsyncGenerator[State]:
    logger = logging.getLogger('application')
    state = State(started=datetime.datetime.now(tz=datetime.UTC))
    logger.info('started at %s', state.started)
    try:
        state.status = 'running'
        yield state
    finally:
        logger.info('stopping')
        state.status = 'stopping'


def authenticated_action(*, claims: example.auth.AuthenticatedClaims) -> None:
    logger = logging.getLogger('application')
    logger.info('authorized for %r', claims.scopes)
    logger.info('authorized as %r', claims.principal)


def lifespans() -> abc.Generator[fastapi_runner.lifespan.LifespanHook]:
    yield from [state_lifespan, example.auth.auth_lifespan]


def configure(app: fastapi.FastAPI) -> None:
    app.add_api_route('/authenticated', authenticated_action)
    app.add_api_route('/status', status)
