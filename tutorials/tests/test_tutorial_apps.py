import asyncio
import importlib
import typing as t

import fastapi.routing

import fastapi_runner.lifespan
from fastapi_runner import entrypoint

TUTORIALS = {
    'tutorial_access_logging.app': '/health',
    'tutorial_cors.app': '/cors',
    'tutorial_database_lifespan.app': '/status',
    'tutorial_error_reporting.app': '/error',
    'tutorial_jwt.app': '/authenticated',
}


def _routes(app: object) -> set[str]:
    return {
        route.path
        for route in t.cast('fastapi.FastAPI', app).routes
        if isinstance(route, fastapi.routing.APIRoute)
    }


def test_each_tutorial_builds_an_application() -> None:
    for module_name, expected_route in TUTORIALS.items():
        module = importlib.import_module(module_name)
        lifespan_generator = getattr(module, 'lifespans', None)
        app = entrypoint.create_app(
            configure=module.configure,
            lifespan_generator=lifespan_generator,
        )

        if expected_route not in _routes(app):
            raise AssertionError(f'{expected_route} is not registered')


def test_database_tutorial_enters_and_exits_its_lifespan() -> None:
    module = importlib.import_module('tutorial_database_lifespan.app')
    app = entrypoint.create_app(
        configure=module.configure,
        lifespan_generator=module.lifespans,
    )

    async def check_lifespan() -> None:
        async with app.router.lifespan_context(app) as context:
            span = t.cast(
                'fastapi_runner.lifespan.Lifespan',
                t.cast('dict[str, object]', context)['lifespan_data'],
            )
            database = span.get_state(module.database_lifespan)
            if not database.connected:
                raise AssertionError('database did not connect')
        if database.connected:
            raise AssertionError('database did not close')

    asyncio.run(check_lifespan())
