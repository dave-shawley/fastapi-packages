# Customize error reporting

The default handlers return RFC 9457-style `application/problem+json` bodies.
Install an application-level updater when the application needs additional
fields or a different problem type.

```python
import fastapi

import fastapi_runner.error_handling
import fastapi_runner.types


def update_error(
    request: fastapi.Request,
    exc: Exception,
    body: fastapi_runner.types.ProblemDetailBody,
) -> None:
    body.type = 'https://example.com/problems/api-error'
    body.extra_context = {'request_id': request.headers.get('x-request-id')}


def configure(app: fastapi.FastAPI) -> None:
    fastapi_runner.error_handling.set_error_updater(app, update_error)
```

Raise `fastapi_runner.errors.ProblemDetailError` when a route needs to provide
a complete problem-detail document. Use
`typesafe_error_handler` when registering a handler whose exception parameter
should remain precisely typed.
