# Typed lifespan state

FastAPI accepts one application lifespan callable. `Lifespan` composes the
application's hooks and stores each yielded value under the hook object itself.
`LifespanMap` is the dependency annotation that retrieves that object during a
request.

```python
def get_database(
    lifespan: fastapi_runner.lifespan.LifespanMap,
) -> Database:
    return lifespan.get_state(database_lifespan)
```

The same hook object must be registered and used for lookup. The callable is
the map key—not a string, class name, or returned value—so the generic
`get_state()` method can infer the yielded type without a caller-written
`cast()`.

If the app was not created with the runner's lifespan, or a dependency asks for
an unregistered hook, FastAPI receives an internal-server-error response. A
hook may yield `None` when it only brackets setup and teardown.
