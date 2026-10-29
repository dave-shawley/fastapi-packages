# Configure CORS

`create_app()` installs CORS middleware from the `FASTAPI_RUNNER_CORS_`
settings namespace. The defaults are restrictive: CORS is enabled, but no
origins, methods, or headers are allowed until configured.

For a local frontend, configure the application environment like this:

```console
FASTAPI_RUNNER_CORS_ALLOW_ORIGINS='["http://localhost:5173"]' \
FASTAPI_RUNNER_CORS_ALLOW_METHODS='["GET", "POST"]' \
FASTAPI_RUNNER_APPLICATION=my-app \
uvicorn --factory fastapi_runner.entrypoint:app_factory
```

Use `FASTAPI_RUNNER_CORS_ENABLED=false` to disable the middleware entirely.
Other supported settings include `ALLOW_HEADERS`, `ALLOW_CREDENTIALS`,
`EXPOSE_HEADERS`, `MAX_AGE`, and `ALLOW_PRIVATE_NETWORK`.
