FROM python:3.14-slim AS builder

ENV \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NATIVE_TLS=1 \
    UV_NO_MANAGED_PYTHON=1 \
    UV_PROJECT_ENVIRONMENT=/app \
    UV_FROZEN=1 \
    UV_PYTHON_DOWNLOADS=never \
    VIRTUAL_ENV=/app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/
COPY /pyproject.toml /uv.lock /README.md /source/
COPY /libraries/ /source/libraries/
COPY /tutorials/ /source/tutorials/
RUN uv sync --directory /source --no-dev --no-default-groups --no-editable --extra otel --frozen

#
# `package-builder` stage extends the `builder` stage by installing a specific application
#
FROM builder AS package-builder
ARG APP_PATH=tutorials
ARG APPLICATION
COPY $APP_PATH/$APPLICATION/ /source/$APP_PATH/$APPLICATION/
RUN uv sync --directory /source/$APP_PATH/$APPLICATION --no-editable --frozen --no-dev --inexact

#
# `webapp` stage copies the installed environment discarding `/source` and other build-time artifacts
# The application is run using `uvicorn` with the `fastapi_runner` entrypoint. The installed application
# needs to include an entrypoint for the runner.
#
FROM python:3.14-slim AS webapp
ARG APPLICATION
EXPOSE 8000
ENV \
    FASTAPI_RUNNER_APPLICATION="$APPLICATION" \
	OTEL_LOGS_EXPORTER=none \
	OTEL_METRICS_EXPORTER=none \
	OTEL_PROPAGATORS=tracecontext,baggage \
	OTEL_RESOURCE_ATTRIBUTES="service.name=$APPLICATION" \
	OTEL_TRACES_EXPORTER=none \
    PATH="/app/bin:$PATH" \
    UVICORN_ACCESS_LOG="no" \
    UVICORN_HOST="0.0.0.0" \
    UVICORN_LOG_CONFIG="/config/log-config.json" \
    UVICORN_SERVER_HEADER="no" \
    UVICORN_PROXY_HEADERS="yes" \
    UVICORN_WORKERS="1" \
    UVICORN_WS="none" \
    VIRTUAL_ENV="/app"

VOLUME /config
COPY --from=package-builder /app /app
COPY ./packaging/log-config.json /config/log-config.json
CMD [ "/app/bin/opentelemetry-instrument", "/app/bin/uvicorn", "--factory", "fastapi_runner.entrypoint:app_factory" ]
