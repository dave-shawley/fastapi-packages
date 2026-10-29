---
title: None
---

# FastAPI Runner

`fastapi-runner` provides the shared application factory, middleware, error
handling, request state, and composable lifespan behavior that belongs in more
than one FastAPI service. Your application package still owns its routes,
configuration hook, authentication, and domain-specific lifespan hooks.

## Install

Install the pre-release from PyPI:

```console
uv add fastapi-runner --prerelease=allow
```

For a local checkout, use the workspace package instead:

```console
uv add --editable ../../libraries/fastapi-runner
```

## Run an application

An application distribution exposes a `configure` entry point and optionally a
`lifespans` entry point in the `fastapi_runner` group:

```toml
[project.entry-points.fastapi_runner]
configure = "my_app.app:configure"
lifespans = "my_app.app:lifespans"
```

Start the generic factory with Uvicorn:

```console
FASTAPI_RUNNER_APPLICATION=my-app \
  uvicorn --factory fastapi_runner.entrypoint:app_factory
```

The [Learn](learn/minimal-app.md) tutorial builds this application from
scratch. The [How-to guides](how-to/cors.md) cover the individual integration
points, while [Reference](reference/entrypoint.md) documents the supported
symbols.
