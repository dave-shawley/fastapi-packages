import typing as t
from collections import abc

import fastapi
import pydantic


class ProblemDetailBody(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra='allow')
    type: str = 'about:blank'
    title: str
    status: int
    detail: t.Annotated[
        str | None, pydantic.Field(exclude_if=lambda x: x is None)
    ] = None


class ValidationErrorBody(ProblemDetailBody):
    errors: dict[str, list[str]] = {}


ErrorUpdater = abc.Callable[
    [fastapi.Request, Exception, ProblemDetailBody], None
]


class ApplicationState(pydantic.BaseModel):
    """Application-level library state.

    This is stored as state on the Starlette application and used
    to configure library behavior. The state object is initialized
    in [entrypoint.create_app][fastapi_runner.entrypoint.create_app].
    """

    error_updater: ErrorUpdater | None = None


class RequestState(t.TypedDict, total=False):
    """Per-request state stored in the ASGI scope.

    This is the **per-request** information that the library
    uses. It contains the authoritative values for the in-flight
    request and overrides other behaviors.
    """

    principal_id: str | None
    disable_access_log: t.NotRequired[bool]
