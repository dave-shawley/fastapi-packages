# fastapi-runner

`fastapi-runner` provides shared FastAPI application setup and a Uvicorn
application factory. It keeps cross-cutting behavior in a reusable library
while the application package owns its routes and application-specific
lifecycle hooks.

This package is a member of the repository's uv workspace, but it is otherwise
freestanding: its package metadata, source tree, tests, and README are all
under this directory. It can be built as its own source distribution and wheel
for a future PyPI release.

## Application discovery

`app_factory()` selects an installed application using the `FASTAPI_RUNNER_APPLICATION`
environment variable. The value is a Python distribution name, not a module
path. That distribution must define exactly one `configure` entry point in the
`fastapi_runner` group and may define a `lifespans` entry point.

For example, an application package can declare:

```toml
[project.entry-points.fastapi_runner]
configure = "my_app.app:configure"
lifespans = "my_app.app:lifespans"
```

The hooks are called as follows:

- `configure(app)` registers routes and other application-specific behavior.
- `lifespans()` yields async context-manager hooks for startup and shutdown.
- Each lifespan hook may accept no arguments or the `FastAPI` application.

Run the generic factory with Uvicorn:

```console
FASTAPI_RUNNER_APPLICATION=my-app uvicorn \
  --factory fastapi_runner.entrypoint:app_factory
```

The distribution named by `FASTAPI_RUNNER_APPLICATION` and `fastapi-runner` must both be
installed in the environment.

## Creating an application directly

Applications and tests that do not need distribution-based discovery can use
`create_app()` directly:

```python
from collections import abc

import fastapi
import fastapi_runner.entrypoint
import fastapi_runner.lifespan


def configure(app: fastapi.FastAPI) -> None:
    """Add application-specific behavior."""


def lifespans() -> abc.Generator[fastapi_runner.lifespan.LifespanHook]:
    """Yield the application lifespan hooks."""


app = fastapi_runner.entrypoint.create_app(
    configure=configure,
    lifespan_generator=lifespans,
)
```

Both entry points install the same shared application behavior:

- CORS middleware configured through the `FASTAPI_RUNNER_CORS_` environment prefix;
- problem-detail responses for HTTP and validation errors;
- an application state hook for customizing problem-detail bodies;
- access logging, with the documentation routes excluded by default; and
- a composable lifespan for application startup and shutdown hooks.

Applications can use `fastapi_runner.lifespan.LifespanMap` as a FastAPI
dependency to retrieve the value returned by a registered lifespan hook:

```python
import contextlib
import typing as t

import fastapi

from fastapi_runner.lifespan import LifespanMap


class State:
    """State that is maintained for the application lifetime."""


@contextlib.asynccontextmanager
async def state_lifespan() -> t.AsyncGenerator[State]:
    yield State()


def get_state(*, lifespan: LifespanMap) -> t.Any:
    return lifespan.get_state(state_lifespan)


def status(*, state: t.Annotated[State, fastapi.Depends(get_state)]) -> State:
    return state
```

The application may raise `fastapi_runner.errors.ProblemDetailError` when it
needs to provide a complete problem-detail document. The default error
handlers also allow an application to update the generated body through the
`fastapi_runner_error_updater` callback on `app.state`.

Use `fastapi_runner.middleware.disable_access_log` on an endpoint when its
requests should not produce an access-log record.

## Customization

### Logging

The default logging configuration is based on the
[Common Logging Format](https://en.wikipedia.org/wiki/Common_Log_Format). The
`fastapi_runner.middleware.AccessLogMiddleware` uses the logger named
`api-runner.access` to log access records. I decided to push the field
configuration into the logging configuration (see packaging/log-config.json)
though I may change that in the future depending on ergonomics. The current
implemention creates a log record with the following custom fields that are
accessed using `%(name)s` in the format record.

| Field              | Description                                       |
| ------------------ | ------------------------------------------------- |
| `%(bytes_sent)s`   | Number of bytes sent in the response              |
| `%(client)s`       | Formatted client address                          |
| `%(duration)s`     | Formatted duration of the request in milliseconds |
| `%(http_version)s` | HTTP version                                      |
| `%(method)s`       | HTTP request method                               |
| `%(path)s`         | Request path                                      |
| `%(status_code)s`  | Numeric status code or `-`                        |
| `%(user_agent)s`   | User agent string or `-`                          |

The formatted lines as configured by _packaging/log-config.json_ look like:

```
2026-10-08 11:44:26,328 WARNING api-runner.access: 192.168.215.1:52540 - "GET /missing HTTP/1.1" 404 22
```

I moved the date out of the log message so that it fits into the general log format.
You can customize the message format to fit your needs by adjusting the formatter
attached to the `api-runner.access` logger.

The `FASTAPI_RUNNER_ACCESS_LOG` environment variable can be set to `no` to disable
access logging. There is currently no way to change the access logger name.

## Development

From the repository root, the shared justfile provides the normal development
commands:

```console
just test
just analyze
just format
```

Run only this library's tests directly when iterating on the package:

```console
uv run --package fastapi-runner pytest libraries/fastapi-runner/tests -q
```

Build its release artifacts from the repository root:

```console
uv build --package=fastapi-runner --sdist --wheel --clear
```

The artifacts are placed in the repository's `dist/` directory. Publishing is
intentionally separate from the development recipes so each library can adopt
its own release and PyPI workflow.
