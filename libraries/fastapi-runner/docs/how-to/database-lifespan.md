# Manage database connections with a lifespan

Keep an application-scoped database resource in an async context manager. The
hook owns both setup and cleanup; the dependency helper retrieves its yielded
value for request handlers.

```python
import contextlib
from collections import abc

import fastapi

import fastapi_runner.lifespan


@contextlib.asynccontextmanager
async def database_lifespan(
    _app: fastapi.FastAPI,
) -> abc.AsyncGenerator[Database]:
    database = Database.connect()
    try:
        yield database
    finally:
        database.close()


def get_database(
    lifespan: fastapi_runner.lifespan.LifespanMap,
) -> Database:
    return lifespan.get_state(database_lifespan)


DatabaseDependency = fastapi.Annotated[Database, fastapi.Depends(get_database)]
```

Yield `None` when a hook only brackets side effects. See
[Typed lifespan state](../explanation/lifespan-state.md) for the hook identity
and type-inference rules.
