import contextlib
import os
import typing as t
from collections import abc
from importlib import metadata

import fastapi.exceptions
import fastapi.middleware.cors
import pydantic_settings

from fastapi_runner import error_handling, errors, lifespan, middleware, types


class CORSSettings(pydantic_settings.BaseSettings):
    model_config = {'env_prefix': 'CORS_'}
    allow_credentials: bool = False
    allow_headers: list[str] = []
    allow_methods: list[str] = [
        'DELETE',
        'GET',
        'HEAD',
        'OPTIONS',
        'POST',
        'PUT',
    ]
    allow_origins: list[str] = []
    allow_private_network: bool = False
    enabled: bool = True
    expose_headers: list[str] = []
    max_age: int = 600


ConfigHook = abc.Callable[[fastapi.FastAPI], None]
LifespanGenerator = abc.Callable[[], abc.Generator[lifespan.LifespanHook]]


def app_factory() -> fastapi.FastAPI:
    """Configurable application factory.

    Use this function with `uvicorn` as a factory to create an
    application instance based on the `APPLICATION` environment
    variable. It identifies the python distribution to import.
    The distribution configures `fastapi_runner` entry points
    named `configure` and (optionally) `lifespans` that match
    the `ConfigHook` and `LifespanGenerator` types.
    """
    try:
        application = os.environ['APPLICATION']
    except KeyError:
        raise errors.ApplicationConfigurationError(
            'APPLICATION environment variable is required'
        ) from None

    try:
        distribution = metadata.distribution(application)
    except metadata.PackageNotFoundError:
        raise errors.ApplicationConfigurationError(
            f'APPLICATION={application!r} does not identify an installed '
            'Python distribution'
        ) from None

    configure, lifespan_generator = _load_hooks(distribution)

    return create_app(
        configure=configure,
        lifespan_generator=lifespan_generator,
    )


def create_app(
    *,
    configure: ConfigHook | None = None,
    lifespan_generator: LifespanGenerator | None = None,
) -> fastapi.FastAPI:
    """Create a FastAPI application instance using hooks

    This method creates an application instance using the supplied
    hooks. In addition to setting up a composable lifespan, the
    CORS and access logging middlewares are installed and several
    error handlers are configured.

    Args:
        configure: A hook that configures the application.
        lifespan_generator: A generator that yields lifespan hooks.

    Returns:
        A FastAPI application instance.
    """

    span = lifespan.Lifespan()
    if lifespan_generator is not None:
        for hook in lifespan_generator():
            span.add_lifespan(hook)

    app = fastapi.FastAPI(lifespan=span)

    cors_settings = CORSSettings()
    if cors_settings.enabled:
        app.add_middleware(
            fastapi.middleware.cors.CORSMiddleware,
            allow_credentials=cors_settings.allow_credentials,
            allow_headers=cors_settings.allow_headers,
            allow_methods=cors_settings.allow_methods,
            allow_origins=cors_settings.allow_origins,
            allow_private_network=cors_settings.allow_private_network,
            expose_headers=cors_settings.expose_headers,
            max_age=cors_settings.max_age,
        )

    # Overrideable to customize error document creation.
    state = t.cast('types.AppStateShape', app.state)
    state.fastapi_runner_error_updater = None

    # Add custom error handlers for specific exception
    # types BEFORE invoking the application level configure
    # so that the app can replace, override, whatever.
    app.add_exception_handler(
        fastapi.exceptions.RequestValidationError,
        error_handling.validation_error_handler,
    )

    # Let the application configure its routes
    if configure is not None:
        configure(app)

    # Add the problem details translator last to ensure that
    # unexpected exceptions are translated.
    app.add_exception_handler(
        fastapi.exceptions.HTTPException,
        error_handling.problem_details_translator,
    )

    # The AccessLogMiddleware should ALWAYS be added last
    app.add_middleware(
        middleware.AccessLogMiddleware,
        ignored_paths=('/docs', '/openapi.json', '/redoc'),
    )

    return app


def _load_hooks(
    distribution: metadata.Distribution,
) -> tuple[ConfigHook, LifespanGenerator | None]:
    entry_points = distribution.entry_points.select(group='fastapi_runner')
    num_eps = len(entry_points.select(name='configure'))
    if num_eps != 1:
        raise ValueError(
            f'Expected exactly one configure entrypoint in fastapi_runner'
            f' group, but found {num_eps} in {distribution.name!r}'
        )

    configure = t.cast('ConfigHook', entry_points['configure'].load())
    lifespan_generator: LifespanGenerator | None = None
    with contextlib.suppress(KeyError):
        lifespan_generator = t.cast(
            'LifespanGenerator', entry_points['lifespans'].load()
        )

    return configure, lifespan_generator
