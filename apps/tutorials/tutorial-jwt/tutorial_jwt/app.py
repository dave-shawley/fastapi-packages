from collections import abc

import fastapi

import fastapi_runner.lifespan
import tutorial_jwt.auth


def authenticated(
    *, claims: tutorial_jwt.auth.AuthenticatedClaims
) -> dict[str, str | list[str]]:
    return {'principal': claims.principal, 'scopes': claims.scopes}


def lifespans() -> abc.Generator[fastapi_runner.lifespan.LifespanHook]:
    yield tutorial_jwt.auth.auth_lifespan


def configure(app: fastapi.FastAPI) -> None:
    app.add_api_route('/authenticated', authenticated)
