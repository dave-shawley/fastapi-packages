# Tutorial applications

Each directory in this collection is a small, runnable application used by the `fastapi-runner` documentation.
They are workspace members, so they share the repository's interpreter, dependency constraints, formatters, and
test commands; they are not independently published packages. Each of the applications are intentionally
focused on one integration concern.

The _compose.yaml_ file defines services with local port bindings for each of the tutorial applications. Running
`docker compose up --build -d` will build each of the tutorials, run them inside of docker, and expose their ports
as well-known local ports.

| Tutorial          | Port |
| ----------------- | ---- |
| access-logging    | 8102 |
| cors              | 8101 |
| database-lifespan | 8103 |
| error-reporting   | 8104 |
| jwt               | 8105 |

## access-logging

Shows how to inject a principal ID into the access log. This example injects a hardcoded value. Requests to
`http://127.0.0.1:8102/principal` set the principal segment in the access log to "tutorial-user". Requests to
`http://127.0.0.1:8102/health` do not show up in the access log at all. You will want to watch the logs for the
application when making requests:

```shell
docker compose logs --tail=0 --follow access-logging
```

## cors

Simple application that enables CORS with a specific origin restriction to `http://127.0.0.1`. It is available at
`http://127.0.0.1:8101/`.

**Successful CORS preflight request**

```shell
curl --verbose --request OPTIONS -H "Origin: http://127.0.0.1" -H "Access-Control-Request-Method: GET" http://127.0.0.1:8101/cors
```

**Failing CORS preflight request**

```shell
curl --verbose --request OPTIONS -H "Origin: http://127.0.0.2" -H "Access-Control-Request-Method: GET" http://127.0.0.1:8101/cors
```

## database-lifespan

The `database_lifespan` function is a simple example of how to use the `lifespan` parameter to manage a scoped
connection like a database. The `status` function (invoked by `http://127.0.0.1:8103/status`) uses FastAPI
dependency injection to retrieve the database connection and return its status.

## error-reporting

The `error_handler` function simply raises a generic FastAPI exception. THe installed `update_error` function
is called after the library catches the exception and translates it into a Problem Detail error. The application
function can mutate the error before it is returned to the client. In this case, It sets the `type` and injects
a `detail` field if the `x-request-id` header is present.

## jwt

This application verifies ES256 bearer tokens using the same application-owned JWT dependency pattern as the
example application. Provide `AUTH_KEY` through the environment or a secret mounted at `/var/run/secrets/auth_key`
before starting it. The `/authenticated` endpoint returns the token principal and scopes.
