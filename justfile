@_help:
    just --list

[doc("Set up a newly cloned repo")]
@setup:
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
