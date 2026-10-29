import fastapi


def configure(app: fastapi.FastAPI) -> None:
    @app.get('/cors')
    def cors() -> dict[str, str]:
        return {'status': 'cors configured'}
