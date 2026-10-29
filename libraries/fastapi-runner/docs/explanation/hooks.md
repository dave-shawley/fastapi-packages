# The configuration and lifespan hook model

`fastapi-runner` separates reusable application setup from application-owned
behavior with two entry points:

1. `configure(app)` registers routes, dependencies, and other application
   behavior.
2. `lifespans()` yields async context-manager hooks for application-lifetime
   resources.

The distribution must expose exactly one `configure` entry point in the
`fastapi_runner` group. The `lifespans` entry point is optional. Each hook may
accept no arguments or the `FastAPI` application.

The runner composes the yielded hooks into one `Lifespan` object and passes it
to FastAPI. Hooks are entered in registration order and cleaned up in reverse
order. This lets independent features own their setup and teardown without
competing to replace FastAPI's single `lifespan=` callable.

Environment settings are a separate contract: application discovery uses the
`FASTAPI_RUNNER_` namespace, while CORS uses `FASTAPI_RUNNER_CORS_`.
