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

`app_factory()` selects an installed application using the `APPLICATION`
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
APPLICATION=my-app uvicorn \
  --factory fastapi_runner.entrypoint:app_factory
```

The distribution named by `APPLICATION` and `fastapi-runner` must both be
installed in the environment.

## Creating an application directly

Applications and tests that do not need distribution-based discovery can use
`create_app()` directly:

```python
from fastapi_runner.entrypoint import create_app

app = create_app(
    configure=configure,
    lifespan_generator=lifespans,
)
```

Both entry points install the same shared application behavior:

- CORS middleware configured through the `CORS_` environment prefix;
- problem-detail responses for HTTP and validation errors;
- an application state hook for customizing problem-detail bodies;
- access logging, with the documentation routes excluded by default; and
- a composable lifespan for application startup and shutdown hooks.

Applications can use `fastapi_runner.lifespan.LifespanMap` as a FastAPI
dependency to retrieve the value returned by a registered lifespan hook:

```python
import typing as t

import fastapi

from fastapi_runner.lifespan import LifespanMap


def get_state(*, lifespan: LifespanMap) -> t.Any:
    return lifespan.get_state(state_lifespan)


def status(*, state: t.Annotated[t.Any, fastapi.Depends(get_state)]) -> t.Any:
    return state
```

The application may raise `fastapi_runner.errors.ProblemDetailError` when it
needs to provide a complete problem-detail document. The default error
handlers also allow an application to update the generated body through the
`fastapi_runner_error_updater` callback on `app.state`.

Use `fastapi_runner.middleware.disable_access_log` on an endpoint when its
requests should not produce an access-log record.

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
