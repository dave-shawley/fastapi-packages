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


class AppStateShape(t.Protocol):
    fastapi_runner_error_updater: (
        abc.Callable[[fastapi.Request, Exception, ProblemDetailBody], None]
        | None
    )
