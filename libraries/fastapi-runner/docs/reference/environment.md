# Environment variables

The library reads the environment variables listed here. Variables are grouped
by the settings namespace that owns them. List values use JSON arrays, such as
`'["https://www.example.com"]'`.

## Application settings

These settings are read by `app_factory()`.

| Variable                     | Type    | Default  | Description                                                                                           |
| ---------------------------- | ------- | -------- | ----------------------------------------------------------------------------------------------------- |
| `FASTAPI_RUNNER_APPLICATION` | string  | required | Name of the installed Python distribution that provides the `fastapi_runner` `configure` entry point. |
| `FASTAPI_RUNNER_ACCESS_LOG`  | boolean | `true`   | Install the access logging middleware.                                                                |

## CORS settings

These settings are read when `create_app()` builds the application, including
when it is called by `app_factory()`.

| Variable                                    | Type                  | Default                                           | Description                                                                                                                                          |
| ------------------------------------------- | --------------------- | ------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| `FASTAPI_RUNNER_CORS_ENABLED`               | boolean               | automatic                                         | When omitted, CORS is enabled if `FASTAPI_RUNNER_CORS_ALLOW_ORIGINS` contains at least one origin. An explicit value overrides automatic enablement. |
| `FASTAPI_RUNNER_CORS_ALLOW_ORIGINS`         | JSON array of strings | `[]`                                              | Origins allowed to make cross-origin browser requests.                                                                                               |
| `FASTAPI_RUNNER_CORS_ALLOW_METHODS`         | JSON array of strings | `DELETE`, `GET`, `HEAD`, `OPTIONS`, `POST`, `PUT` | HTTP methods allowed for CORS requests.                                                                                                              |
| `FASTAPI_RUNNER_CORS_ALLOW_HEADERS`         | JSON array of strings | `[]`                                              | Request headers allowed for CORS requests.                                                                                                           |
| `FASTAPI_RUNNER_CORS_ALLOW_CREDENTIALS`     | boolean               | `false`                                           | Allow credentials in cross-origin requests.                                                                                                          |
| `FASTAPI_RUNNER_CORS_EXPOSE_HEADERS`        | JSON array of strings | `[]`                                              | Response headers exposed to browser clients.                                                                                                         |
| `FASTAPI_RUNNER_CORS_MAX_AGE`               | integer               | `600`                                             | Seconds that browsers may cache a successful CORS preflight response.                                                                                |
| `FASTAPI_RUNNER_CORS_ALLOW_PRIVATE_NETWORK` | boolean               | `false`                                           | Allow requests made to a private network from a public context.                                                                                      |

For example:

```console
FASTAPI_RUNNER_APPLICATION=my-app \
FASTAPI_RUNNER_CORS_ALLOW_ORIGINS='["https://www.example.com"]' \
FASTAPI_RUNNER_CORS_ALLOW_METHODS='["GET", "POST"]' \
uvicorn --factory fastapi_runner.entrypoint:app_factory
```

Applications that call `create_app()` directly can set
`FASTAPI_RUNNER_CORS_*` variables in the same way. The
`FASTAPI_RUNNER_APPLICATION` and `FASTAPI_RUNNER_ACCESS_LOG` settings apply only
to distribution discovery through `app_factory()`; direct callers pass the
application hook and access-log choice as Python arguments.
