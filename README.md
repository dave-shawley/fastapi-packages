# FastAPI packages

This repository is a monorepo for reusable FastAPI libraries and the local
applications used to develop and demonstrate them. Reusable code lives under
`libraries/`; tutorial applications under `tutorials/` are not intended to be
published to PyPI.

## Repository structure

```text
.
├── tutorials/                # Local integration applications
├── libraries/
│   └── fastapi-runner/       # Independently distributable library
├── packaging/                # Dockerfile and logging configuration
├── justfile                  # Common development commands
├── pyproject.toml            # Workspace and shared development config
└── uv.lock                   # Root workspace lockfile
```

The root project is a non-package uv workspace. Its workspace members include
the independently distributable libraries and the local tutorial applications.
Each library has its own `pyproject.toml`, package metadata, source tree, tests,
and README; tutorials are workspace applications used for integration testing,
documentation, and container examples.

The root `pyproject.toml` supplies shared development dependencies, uv
workspace constraints, and tool configuration. The root lockfile resolves all
workspace libraries and tutorials.

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

Build and run the tutorial applications with Docker Compose:

```console
docker compose -f tutorials/compose.yaml up --build
```

The Compose file exposes each tutorial on a documented local port. For example,
the CORS tutorial is available at:

```console
curl http://127.0.0.1:8101/cors
```

## Building libraries

Build a library from the repository root by naming the uv workspace package:

```console
uv build --package=fastapi-runner --sdist --wheel --clear
```

The source distribution and wheel are written to `dist/`. Library metadata,
including its version, dependencies, and README, belongs in that library's
directory. This keeps each workspace library suitable for a future independent
PyPI release. `just build` also builds the tutorial images.
