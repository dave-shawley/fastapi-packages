# FastAPI packages

This repository is a monorepo for reusable FastAPI libraries and the local
applications used to develop and demonstrate them. Reusable code lives under
`libraries/`; applications under `apps/` are not intended to be published to
PyPI.

## Repository structure

```text
.
├── apps/
│   └── example-app/          # Local demo application; its own uv project
├── libraries/
│   └── fastapi-runner/       # Independently distributable library
├── packaging/                # Dockerfile and logging configuration
├── justfile                  # Common development commands
├── pyproject.toml            # Workspace and shared development config
└── uv.lock                   # Root workspace lockfile
```

The root project is a non-package uv workspace. Its workspace members are the
projects in `libraries/`. Each library has its own `pyproject.toml`, package
metadata, source tree, tests, and README so it can be built and distributed
independently. A future library can be added as another workspace member
without making it part of an application distribution.

`apps/example-app` is deliberately separate from the root workspace. It has
its own `pyproject.toml` and `uv.lock`, and refers to `fastapi-runner` through a
local path while the library is being developed. Applications are useful for
local integration testing, examples, and container images; they are not
workspace packages intended for PyPI.

The root `pyproject.toml` supplies shared development dependencies, uv
workspace constraints, and tool configuration. The root lockfile resolves the
workspace libraries. The example application maintains its own lockfile
because it is an independently managed application project.

## fastapi-runner

[`libraries/fastapi-runner`](libraries/fastapi-runner) is the first reusable
library in the repository. It provides shared FastAPI application setup and a
Uvicorn factory that discovers an application from its installed distribution.
See its [README](libraries/fastapi-runner/README.md) for the library API and
integration contract.

The application selected by the factory is configured with the `APPLICATION`
environment variable. Its installed distribution must provide one
`configure` entry point in the `fastapi_runner` group and may provide a
`lifespans` entry point. This lets the runner remain reusable while each
application owns its routes and application-specific lifecycle hooks.

## Development

Install Python 3.14, [uv](https://docs.astral.sh/uv/), [just](https://just.systems/),
and [dprint](https://dprint.dev/). From the repository root, set up the
workspace and pre-commit hooks with:

```console
just setup
```

The justfile is the authoritative list of common tasks. `just --list` displays
the available recipes:

```console
just analyze [FILES...]   # Ruff, Pyrefly, and dprint checks
just format [FILES...]    # Format selected files with dprint
just test [ARGS...]       # Run pytest with coverage
just build                # Build fastapi-runner and local Docker images
```

The recipes call uv from the repository root and operate on the workspace
libraries. `analyze` always runs Pyrefly against the complete repository
context, even when file arguments limit the Ruff and dprint checks. `test`
prints a coverage report when no pytest arguments are supplied.

Run the example application locally with its own environment:

```console
cd apps/example-app
uv sync --frozen
APPLICATION=example-app uv run uvicorn \
  --factory fastapi_runner.entrypoint:app_factory \
  --log-config ../../packaging/log-config.json
```

Then visit `http://127.0.0.1:8000/status` or use:

```console
curl http://127.0.0.1:8000/status
```

The example demonstrates a `configure` hook that registers the `/status`
route and a `lifespans` hook that exposes application state through
`fastapi_runner.lifespan.LifespanMap`.

## Building libraries

Build a library from the repository root by naming the uv workspace package:

```console
uv build --package=fastapi-runner --sdist --wheel --clear
```

The source distribution and wheel are written to `dist/`. Library metadata,
including its version, dependencies, and README, belongs in that library's
directory. This keeps each workspace library suitable for a future independent
PyPI release. `just build` currently performs this library build and also
builds the local Docker builder and example application images.
