# Typesafe error handlers

FastAPI registers exception handlers through a generic exception boundary, but
the handler implementation usually knows the specific exception type it
expects. `typesafe_error_handler` adapts that precise function to FastAPI's
generic callable while checking the exception type before invocation.

```python
@fastapi_runner.error_handling.typesafe_error_handler
def handle_not_found(
    request: fastapi.Request,
    exc: NotFoundError,
) -> fastapi.Response: ...
```

The decorator preserves the handler metadata and prevents an incorrectly
typed exception from reaching the implementation. The same pattern is used by
the library's HTTP and validation error handlers.
