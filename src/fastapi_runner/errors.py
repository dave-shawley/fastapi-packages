import fastapi

from fastapi_runner import types


class ApplicationConfigurationError(RuntimeError):
    pass


class ProblemDetailError(fastapi.HTTPException):
    def __init__(
        self,
        status_code: int,
        *,
        title: str,
        type: str,  # noqa: A002 -- using type to ensure it is not in `body`
        **body: object,
    ) -> None:
        super().__init__(status_code=status_code, detail=title)
        self.body = types.ProblemDetailBody.model_validate(
            {
                'type': type,
                'title': title,
                'status': status_code,
                **body,
            }
        )
