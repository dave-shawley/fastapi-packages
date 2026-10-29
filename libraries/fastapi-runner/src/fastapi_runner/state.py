import re
import typing
import typing as t

import fastapi
import starlette.datastructures
import starlette.types

from fastapi_runner import types


class RequestStateNotInitializedError(RuntimeError):
    """The per-request state has not been initialized."""


APPLICATION_STATE_ATTR = 'fastapi_runner_state'
REQUEST_STATE_KEY = 'fastapi_runner_request_state'


def _default_request_state() -> types.RequestState:
    return {'principal_id': None}


def initialize_application_state(
    state: starlette.datastructures.State,
) -> None:
    if not hasattr(state, APPLICATION_STATE_ATTR):
        setattr(state, APPLICATION_STATE_ATTR, types.ApplicationState())


def get_application_state(
    state: starlette.datastructures.State,
) -> types.ApplicationState:
    return getattr(state, APPLICATION_STATE_ATTR, types.ApplicationState())


def require_application_state(
    state: starlette.datastructures.State,
) -> types.ApplicationState:
    if not hasattr(state, APPLICATION_STATE_ATTR):
        raise AttributeError('Application state not initialized')
    return getattr(state, APPLICATION_STATE_ATTR)


def initialize_request_state(
    scope: starlette.types.Scope,
) -> starlette.types.Scope:
    """Initialize the per-request state in the ASGI scope."""
    if REQUEST_STATE_KEY in scope:
        return scope
    new_scope = dict(scope)
    new_scope[REQUEST_STATE_KEY] = _default_request_state()
    return new_scope


def get_request_state(scope: starlette.types.Scope) -> types.RequestState:
    """Get request state from the ASGI scope.

    This will return a blank state if the ASGI scope does not
    contain a per-request state object. Use
    [require_request_state][fastapi_runner.state.require_request_state]
    if you need a reference to the per-request state.

    """
    request_state = scope.get(REQUEST_STATE_KEY, _default_request_state())
    for k, v in _default_request_state().items():
        request_state.setdefault(k, v)
    return request_state


def require_request_state(scope: starlette.types.Scope) -> types.RequestState:
    """Get the required per-request state from the ASGI scope.

    This will raise a
    [RequestStateNotInitializedError][fastapi_runner.state.RequestStateNotInitializedError]
    if the ASGI
    scope does not contain a per-request state object. See
    [get_request_state][fastapi_runner.state.get_request_state] if you always
    want a state object even
    if it is blank.

    """
    try:
        return scope[REQUEST_STATE_KEY]
    except KeyError:
        raise RequestStateNotInitializedError() from None


_CONTROL_CHARACTERS = re.compile(r'[\x00-\x1f\x7f]')


@typing.overload
def set_principal_id(
    principal_id: str | None, *, request: fastapi.Request
) -> None: ...


@typing.overload
def set_principal_id(
    principal_id: str | None, *, scope: starlette.types.Scope
) -> None: ...


def set_principal_id(
    principal_id: str | None,
    *,
    request: fastapi.Request | None = None,
    scope: starlette.types.Scope | None = None,
) -> None:
    """Store the principal ID in the per-request state."""
    if request is None:
        if scope is None:
            raise RuntimeError('request or scope are required')
        request_scope = scope
    elif scope is None:
        request_scope = request.scope
    else:
        raise RuntimeError('request and scope are mutually exclusive')

    if principal_id is None:
        pass
    elif not isinstance(principal_id, str):
        raise TypeError('principal_id must be a string or None')
    elif not principal_id:
        raise ValueError('principal_id cannot be an empty string')
    elif _CONTROL_CHARACTERS.search(principal_id):
        raise ValueError('principal_id cannot contain control characters')

    t.assert_type(principal_id, str | None)
    require_request_state(request_scope)['principal_id'] = principal_id
