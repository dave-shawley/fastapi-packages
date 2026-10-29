# Build a minimal application

This tutorial creates the smallest application package that can be discovered
by `fastapi-runner`.

## Configure the application

```python
import fastapi


def configure(app: fastapi.FastAPI) -> None:
    @app.get('/health')
    def health() -> dict[str, str]:
        return {'status': 'ok'}
```

Register that function in the application's `pyproject.toml`:

```toml
[project.entry-points.fastapi_runner]
configure = "my_app.app:configure"
```

## Start it

```console
FASTAPI_RUNNER_APPLICATION=my-app \
  uvicorn --factory fastapi_runner.entrypoint:app_factory
```

The factory reads `FASTAPI_RUNNER_APPLICATION`, locates the installed
distribution, loads exactly one `configure` hook, and creates the FastAPI
application with the shared middleware and error handlers.

Continue with [Configure CORS](../how-to/cors.md) or the
[configuration and lifespan explanation](../explanation/hooks.md).
