runtime_dir := justfile_directory() / 'runtime'
secrets_dir := runtime_dir / 'secrets'

@_help:
    just --list

[doc("Set up a newly cloned repo")]
@setup: _env _secrets
    command -v dprint>/dev/null || ( echo 'Install dprint from https://dprint.dev'; exit 1 )
    uv sync --quiet --all-extras --all-groups --all-packages --frozen
    uv run pre-commit install --install-hooks --overwrite >/dev/null

[doc("Run static analysis tools")]
analyze *FILES: setup
    #!/usr/bin/env sh
    set -e
    uv run ruff check {{ FILES }}
    uv run pyrefly check . # always analyze complete context
    dprint check --allow-no-files {{ FILES }}

[doc("Format files")]
format *FILES: setup
    dprint fmt --allow-no-files {{ FILES }}

[doc("Run tests")]
test *ARGS: setup
    uv run coverage run -m pytest {{ ARGS }}
    @[ -z '{{ ARGS }}' ] && uv run coverage report

[doc("Build distributions")]
build: setup
    uv build --package=fastapi-runner --sdist --wheel --clear
    docker build -f packaging/Dockerfile --target builder -t dave-shawley/fastapi-builder:local .
    docker build -f packaging/Dockerfile --target webapp --build-arg APPLICATION=example-app -t dave-shawley/fastapi-example-app:local .

[doc("Run the example application in compose")]
compose-up: _secrets
    docker compose up -d example-app

[doc("Run the example application in compose")]
compose-down:
    docker compose down --remove-orphans --volumes

[doc("Remove generated files")]
clean: compose-down
    - rm -fr {{ runtime_dir }}

_env:
    #!/usr/bin/env sh
    set -e
    mkdir -p {{ runtime_dir }}
    cat > {{ runtime_dir / '.env' }} <<EOF
    AUTH_AUDIENCE=https://api.example.com
    OTEL_LOGS_EXPORTER=none
    OTEL_METRICS_EXPORTER=none
    OTEL_TRACES_EXPORTER=none
    FASTAPI_RUNNER_APPLICATION=example-app
    UVICORN_ACCESS_LOG=no
    UVICORN_LOG_CONFIG=packaging/log-config.json
    UVICORN_SERVER_HEADER=no
    UVICORN_PROXY_HEADERS=yes
    UVICORN_WORKERS=1
    UVICORN_WS=none
    EOF

@_secrets:
    mkdir -p {{ secrets_dir }}
    test -e {{ secrets_dir / 'auth_key' }} || openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:prime256v1 -out {{ secrets_dir / 'auth_key' }}
    chmod 0600 {{ secrets_dir / 'auth_key' }}
    test -e {{ secrets_dir / 'auth_key.pub' }} || openssl pkey -in runtime/secrets/auth_key -pubout -out {{ secrets_dir / 'auth_key.pub' }}
