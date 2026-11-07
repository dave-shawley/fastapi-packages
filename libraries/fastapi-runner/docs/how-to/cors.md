# Configure CORS

`create_app()` installs CORS middleware from the `FASTAPI_RUNNER_CORS_`
settings namespace. CORS is enabled automatically when at least one origin is
configured. With no origins, the middleware is disabled because it could not
serve a cross-origin browser client. Set `FASTAPI_RUNNER_CORS_ENABLED=true` to
explicitly enable it, or `false` to disable it, regardless of the origin list.

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
