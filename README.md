# Production-ready Uvicorn runner for FastAPI applications

`fastapi-runner` provides the common application setup for a FastAPI service
and a factory that can load an application from its installed Python
distribution. The application package owns its routes and lifecycle hooks;
the runner owns the shared middleware, error handling, and Uvicorn entrypoint.

## Application factory pattern

The runner is deliberately split into two layers:

1. `app_factory()` reads the `APPLICATION` environment variable, finds the
   installed distribution with that name, and loads its `fastapi_runner`
   entry points.
2. `create_app()` builds the `FastAPI` instance, installs the shared behavior,
   registers the application lifespan hooks, and calls the application's
   `configure` hook.

The application is therefore selected by package metadata rather than by
hard-coding an import path in the runner. The flow is:

```text
APPLICATION=example-app
        |
        v
metadata.distribution("example-app")
        |
        v
fastapi_runner entry points
        |
        +--> configure(app)
        |
        +--> lifespans()  [optional]
        |
        v
create_app(...) -> FastAPI instance
```

`configure` is required and must occur exactly once. `lifespans` is optional;
when present, it yields context-manager hooks that are entered during startup
and exited during shutdown.

## Using the runner directly

Applications that do not need distribution-based discovery can call
`create_app()` themselves:

```python
from fastapi_runner.entrypoint import create_app

app = create_app(
    configure=configure,
    lifespan_generator=lifespans,
)
```

This uses the same shared setup as `app_factory()`. The `app_factory()` form is
useful when the launcher should remain generic and the selected application is
chosen through deployment configuration. This is most useful for testing
applications that use the runner.

## Shared application setup

`create_app()` currently provides:

- configurable CORS middleware;
- validation and HTTP exception handlers that produce problem-detail
  responses;
- access logging middleware, excluding the standard documentation routes;
- a composable FastAPI lifespan for application startup and shutdown hooks.

The goal of the library is to move the cross-cutting concerns from application
code. The runner ensures that the environment that the application runs in is
consistent across all FastAPI applications.

The factory raises an `ApplicationConfigurationError` when `APPLICATION` is
missing or does not identify an installed distribution. A malformed package
with zero or multiple `configure` entry points is also rejected during
startup.

## Development

From the repository root:

```console
uv sync
just test
just analyze
```
