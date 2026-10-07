import collections
import functools
import inspect
import typing as t
from collections import abc

import fastapi.exceptions

from fastapi_runner import errors, types


class ValidationErrorShape(t.TypedDict, total=False):
    """The shape of `fastapi.exceptions.ValidationError.errors()`"""

    type: t.Required[str]
    loc: t.Required[abc.Sequence[str]]
    msg: t.Required[str]


def _ensure_declared_exception_type[T: Exception, R](
    exc: Exception, handler: abc.Callable[[fastapi.Request, T], R]
) -> t.TypeGuard[T]:
    """Type guard that ensures the exc type matches the handler.

    This is used in `typesafe_error_handler` to adapt the exception
    parameter in the FastAPI error handler to the precise type.
    """
    params = tuple(inspect.signature(handler).parameters)
    exception_param = params[1]
    expected = t.get_type_hints(handler)[exception_param]
    return (
        isinstance(expected, type)
        and issubclass(expected, Exception)
        and isinstance(exc, expected)
    )


def typesafe_error_handler[T: Exception, RT](
    handler: abc.Callable[[fastapi.Request, T], RT],
) -> abc.Callable[[fastapi.Request, Exception], RT]:
    """Adapt a type-safe error handler to a generic error hook.

    FastAPI uses a generic `Exception` in exception handlers
    even though the precise type is specified in the
    `add_exception_handler` call. This decorator exposes the
    more generic parameter type while ensuring that the precise
    type is checked at runtime before calling the handler.

    Args:
        handler: The error handler function to adapt.

    Returns:
        A wrapper function that accepts an `Exception` and
        type narrows *before* calling `handler`.

    """

    @functools.wraps(handler)
    def wrapper(request: fastapi.Request, exc: Exception) -> RT:
        if _ensure_declared_exception_type(exc, handler):
            return handler(request, exc)
        raise TypeError(f'Expected {T.__name__}, got {exc.__class__.__name__}')

    return wrapper


@typesafe_error_handler
def problem_details_translator(
    request: fastapi.Request, exc: fastapi.exceptions.HTTPException
) -> fastapi.Response:
    """Translate HTTP exceptions to Problem Details bodies.

    The response shape matches `types.ProblemDetailBody` with the
    default status and title coming from `exc` properties.
    Applications should define the `fastapi_runner_error_updater`
    attribute on the state as a callable that updates the error
    body to match application expectations.

    """
    error_body: types.ProblemDetailBody
    if isinstance(exc, errors.ProblemDetailError):
        error_body = exc.body
    else:
        error_body = types.ProblemDetailBody.model_validate(
            {
                'status': exc.status_code,
                'title': exc.detail,
            }
        )

    app_state = t.cast('types.AppStateShape', request.app.state)
    if app_state.fastapi_runner_error_updater is not None:
        app_state.fastapi_runner_error_updater(request, exc, error_body)

    return fastapi.Response(
        media_type='application/problem+json',
        status_code=exc.status_code,
        content=error_body.model_dump_json(),
    )


@typesafe_error_handler
def validation_error_handler(
    request: fastapi.Request, exc: fastapi.exceptions.ValidationException
) -> fastapi.Response:
    """Customize validation error handling.

    Maps validation errors to the `errors` response body field.
    It is a mapping from the error type to a list of error locations
    where the type can be any string. The standard values are
    defined by the `pydantic_core.ErrorType` literal type. However,
    a `pydantic_core.PydanticCustomError` exception can be raised
    to set the error type to an arbitrary string.

    The application error update hook can be used to further
    customize the error response body.

    """
    error_body = types.ValidationErrorBody.model_validate(
        {
            'status': 422,
            'title': 'Validation Error',
            'errors': {},
        }
    )

    errors: dict[str, list[str]] = collections.defaultdict(list[str])
    err: ValidationErrorShape
    for err in exc.errors():
        errors[err['type']].append('.'.join(err['loc']))
    error_body.errors.update(errors)

    app_state = t.cast('types.AppStateShape', request.app.state)
    if app_state.fastapi_runner_error_updater is not None:
        app_state.fastapi_runner_error_updater(request, exc, error_body)

    return fastapi.Response(
        media_type='application/problem+json',
        status_code=error_body.status,
        content=error_body.model_dump_json(),
    )
