export UV_FROZEN := "1"
runtime_dir := justfile_directory() / 'runtime'
secrets_dir := runtime_dir / 'secrets'

@_help:
    just --list

[doc("Set up a newly cloned repo")]
@setup: _env _secrets
    command -v dprint>/dev/null || ( echo 'Install dprint from https://dprint.dev'; exit 1 )
    uv sync --quiet --all-extras --all-groups --all-packages
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
build: docs setup
    uv build --package=fastapi-runner --sdist --wheel --clear
    docker build -f packaging/Dockerfile --target builder -t dave-shawley/fastapi-builder:local .
    docker compose -f tutorials/compose.yaml build

[doc("Run the tutorial applications in compose")]
tutorials-up: _secrets
    docker compose -f tutorials/compose.yaml up -d

[doc("Stop the tutorial applications in compose")]
tutorials-down:
    docker compose -f tutorials/compose.yaml down --remove-orphans --volumes

[doc("Remove generated files")]
clean: tutorials-down
    - rm -fr {{ runtime_dir }}

[doc("Build documentation")]
docs: setup
    uv run --package=fastapi-runner --directory=libraries/fastapi-runner zensical build --clean

_env:
    #!/usr/bin/env sh
    set -e
    mkdir -p {{ runtime_dir }}
    cat > {{ runtime_dir / '.env' }} <<EOF
    AUTH_AUDIENCE=https://api.example.com
    OTEL_LOGS_EXPORTER=none
    OTEL_METRICS_EXPORTER=none
    OTEL_TRACES_EXPORTER=none
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
