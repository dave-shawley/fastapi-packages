# Configure access logging

Access logging is enabled by default. Set
`FASTAPI_RUNNER_ACCESS_LOG=false` to disable it for an application.

The middleware writes records through `api-runner.access`. An application can
add an explicit principal ID after authenticating a request:

```python
import fastapi

import fastapi_runner.state


def authenticate(request: fastapi.Request) -> None:
    # Replace this with application-owned token validation.
    fastapi_runner.state.set_principal_id('account-123', request=request)
```

Use the decorator when an endpoint should never produce an access record:

```python
import fastapi_runner.middleware


@fastapi_runner.middleware.disable_access_log
def health() -> dict[str, str]:
    return {'status': 'ok'}
```

Configure the final log format in the logging configuration attached to the
`api-runner.access` logger.
