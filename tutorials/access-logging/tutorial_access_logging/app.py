import fastapi

import fastapi_runner.middleware
import fastapi_runner.state


@fastapi_runner.middleware.disable_access_log
def health() -> dict[str, str]:
    return {'status': 'ok'}


def principal(request: fastapi.Request) -> dict[str, str | None]:
    fastapi_runner.state.set_principal_id('tutorial-user', request=request)
    return {'principal': 'tutorial-user'}


def configure(app: fastapi.FastAPI) -> None:
    app.add_api_route('/health', health)
    app.add_api_route('/principal', principal)
