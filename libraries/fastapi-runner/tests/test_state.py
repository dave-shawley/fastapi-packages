import unittest.mock

import fastapi
import starlette.datastructures
import starlette.types

from fastapi_runner import state


class SetPrincipalIdTests(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.scope = state.initialize_request_state({})
        self.request: fastapi.Request = unittest.mock.Mock(
            spec=fastapi.Request,
            scope=self.scope,
        )

    def test_mutually_exclusive_request_and_scope(self) -> None:
        with self.assertRaises(RuntimeError, msg='args are required'):
            state.set_principal_id('foo')  # type: ignore[no-matching-overload]
        # this is technically duplicative
        with self.assertRaises(RuntimeError, msg='one is required'):
            state.set_principal_id('foo', request=None, scope=None)  # type: ignore[no-matching-overload]
        with self.assertRaises(RuntimeError, msg='both cannot be provided'):
            state.set_principal_id(  # type: ignore[no-matching-overload]
                'foo', request=self.request, scope=self.scope
            )

    def test_non_string_principal_id(self) -> None:
        with self.assertRaises(TypeError):
            state.set_principal_id(1234, request=self.request)  # type: ignore[no-matching-overload]

    def test_empty_string_principal_id(self) -> None:
        with self.assertRaises(ValueError):
            state.set_principal_id('', request=self.request)

    def test_control_characters_in_principal_id(self) -> None:
        for ctrl_character in list(range(0x1F)) + [0x7F]:
            with (
                self.subTest(f'control character {hex(ctrl_character)}'),
                self.assertRaises(ValueError),
            ):
                state.set_principal_id(
                    f'foo{chr(ctrl_character)}', request=self.request
                )

    def test_using_explicit_scope(self) -> None:
        state.set_principal_id('foo', scope=self.scope)
        request_state = state.require_request_state(self.scope)
        self.assertEqual(request_state['principal_id'], 'foo')

    def test_using_request_scope(self) -> None:
        state.set_principal_id('foo', request=self.request)
        request_state = state.require_request_state(self.request.scope)
        self.assertEqual(request_state['principal_id'], 'foo')

    def test_clearing_principal_id(self) -> None:
        state.set_principal_id('foo', scope=self.scope)
        state.set_principal_id(None, scope=self.scope)
        request_state = state.require_request_state(self.request.scope)
        self.assertIsNone(request_state['principal_id'])


class StateManagementTests(unittest.TestCase):
    def test_application_state(self) -> None:
        app_state = starlette.datastructures.State()
        self.assertNotHasAttr(app_state, state.APPLICATION_STATE_ATTR)

        # get_application_state does not raise and returns a
        # unique empty state object when uninitialized
        self.assertIsNot(
            state.get_application_state(app_state),
            state.get_application_state(app_state),
            'get_application_state returns a new, disconnected state',
        )

        # require_application_state raises when uninitialized
        with self.assertRaises(AttributeError):
            state.require_application_state(app_state)

        # initialize_application_state stores a new state object
        state.initialize_application_state(app_state)
        self.assertHasAttr(app_state, state.APPLICATION_STATE_ATTR)
        init_state = getattr(app_state, state.APPLICATION_STATE_ATTR)
        self.assertIs(state.get_application_state(app_state), init_state)

        # initialize_application_state does not overwrite an existing
        # state object. IOW, it is idempotent.
        state.initialize_application_state(app_state)
        self.assertIs(
            state.get_application_state(app_state),
            init_state,
            'initialize_application_state should be idempotent',
        )

    def test_request_state(self) -> None:
        scope: starlette.types.Scope = {}
        self.assertNotIn(state.REQUEST_STATE_KEY, scope)

        # get_request_state does not raise and returns a unique
        # empty state object when uninitialized
        self.assertIsNot(
            state.get_request_state(scope),
            state.get_request_state(scope),
            'get_request_state returns a new, disconnected state',
        )
        self.assertNotIn(state.REQUEST_STATE_KEY, scope)

        # require_request_state raises when uninitialized
        with self.assertRaises(state.RequestStateNotInitializedError):
            state.require_request_state(scope)

        # initialize_request_state returns a new scope with
        # the state object
        new_scope = state.initialize_request_state(scope)
        self.assertIsNot(new_scope, scope)
        self.assertIn(state.REQUEST_STATE_KEY, new_scope)
        self.assertNotIn(state.REQUEST_STATE_KEY, scope)
        init_state = new_scope[state.REQUEST_STATE_KEY]
        self.assertIs(state.get_request_state(new_scope), init_state)

        # initialize_request_state returns the same scope
        # when already initialized
        next_scope = state.initialize_request_state(new_scope)
        self.assertIs(next_scope, new_scope)
