import typing as t
from collections import abc

import fastapi
import pydantic
import starlette.datastructures
from pydantic import annotated_handlers, json_schema
from pydantic_core import core_schema


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


def _validate_starlette_url(
    value: str | starlette.datastructures.URL,
) -> starlette.datastructures.URL:
    match value:
        case str():
            return starlette.datastructures.URL(value)
        case starlette.datastructures.URL():
            return value
        case _:
            raise ValueError('Value must be a string or starlette URL')


def _get_starlette_core_schema(
    _typ: type, _handler: annotated_handlers.GetCoreSchemaHandler
) -> core_schema.CoreSchema:
    validator = core_schema.no_info_plain_validator_function(
        _validate_starlette_url
    )
    return core_schema.json_or_python_schema(
        validator, validator, serialization=core_schema.to_string_ser_schema()
    )


def _get_starlette_json_schema(
    _typ: type, _handler: annotated_handlers.GetJsonSchemaHandler
) -> json_schema.JsonSchemaValue:
    return {'type': 'string', 'format': 'uri'}


StarletteUrl = t.Annotated[
    starlette.datastructures.URL,
    pydantic.GetPydanticSchema(
        _get_starlette_core_schema, _get_starlette_json_schema
    ),
]
