import fastapi

import fastapi_runner.error_handling
import fastapi_runner.errors
import fastapi_runner.types


def update_error(
    request: fastapi.Request,
    _exc: Exception,
    body: fastapi_runner.types.ProblemDetailBody,
) -> None:
    body.type = 'https://example.test/problems/tutorial-error'
    body.detail = request.headers.get('x-request-id')


def error_handler() -> None:
    raise fastapi.HTTPException(400)


def configure(app: fastapi.FastAPI) -> None:
    fastapi_runner.error_handling.set_error_updater(app, update_error)
    app.add_api_route('/error', error_handler)
