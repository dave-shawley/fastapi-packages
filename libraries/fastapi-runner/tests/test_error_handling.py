import json
import typing as t
import unittest.mock

import fastapi.exceptions
import fastapi.testclient
import pydantic

from fastapi_runner import entrypoint, error_handling, errors, types


class ErrorHandlingTests(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.app = entrypoint.create_app()
        self.request = fastapi.Request(scope={'type': 'http', 'app': self.app})

    def test_runtime_enforcement(self) -> None:
        @error_handling.typesafe_error_handler
        def handler(
            _request: fastapi.Request, _exc: RuntimeError
        ) -> fastapi.Response:
            return fastapi.Response()

        with self.assertRaises(TypeError):
            handler(self.request, OSError())
        handler(self.request, RuntimeError())

        # this is run during static type checking and NOT testing
        t.assert_type(handler(self.request, RuntimeError()), fastapi.Response)

    def test_problem_details_translation(self) -> None:
        source = fastapi.exceptions.HTTPException(status_code=404)
        response = error_handling.problem_details_translator(
            unittest.mock.Mock(spec=fastapi.Request), source
        )
        self.assertEqual(404, response.status_code)
        self.assertEqual(
            'application/problem+json', response.headers['content-type']
        )

        body = json.loads(bytes(response.body).decode('utf-8'))
        self.assertEqual('Not Found', body['title'])
        self.assertEqual(404, body['status'])
        self.assertEqual('about:blank', body['type'])

    def test_problem_details_passthru(self) -> None:
        source = errors.ProblemDetailError(
            status_code=404,
            title='NOT FOUND',
            type='https://errors.example.com/not-found',
        )
        response = error_handling.problem_details_translator(
            self.request, source
        )
        self.assertEqual(404, response.status_code)
        self.assertEqual(
            'application/problem+json', response.headers['content-type']
        )

        body = json.loads(bytes(response.body).decode('utf-8'))
        self.assertEqual('NOT FOUND', body['title'])
        self.assertEqual(404, body['status'])
        self.assertEqual('https://errors.example.com/not-found', body['type'])

    def test_validation_failure_translator(self) -> None:

        class RequestBody(pydantic.BaseModel):
            flag: bool
            number: int = 0

        @self.app.post('/')
        def handler(
            *,
            _h: t.Annotated[str, fastapi.Header(alias='header-name')],
            _r: RequestBody,
        ) -> None:
            pass

        with fastapi.testclient.TestClient(self.app) as client:
            response = client.post('/', json={'number': 'not-a-number'})
            self.assertEqual(422, response.status_code)
            self.assertEqual(
                'application/problem+json', response.headers['content-type']
            )

        body = response.json()
        self.assertEqual('Validation Error', body['title'])
        self.assertEqual(422, body['status'])
        self.assertEqual('about:blank', body['type'])
        self.assertEqual(['body.number'], body['errors']['int_parsing'])
        self.assertCountEqual(
            ['body.flag', 'header.header-name'], body['errors']['missing']
        )

    def test_validation_failure_with_custom_updater(self) -> None:
        def updater(
            _r: fastapi.Request, _e: Exception, body: types.ProblemDetailBody
        ) -> None:
            body.status = 400
            body.type = '/errors/custom-error'

        @self.app.get('/')
        def get(
            *, _h: t.Annotated[str, fastapi.Header(alias='api-key')]
        ) -> None:
            return None

        self.app.state.fastapi_runner_error_updater = updater
        with fastapi.testclient.TestClient(self.app) as client:
            response = client.get('/')
            self.assertEqual(400, response.status_code)
            self.assertEqual(
                'application/problem+json', response.headers['content-type']
            )

        body = response.json()
        self.assertEqual('/errors/custom-error', body['type'])
