# Use a runner-independent ASGI lifespan seam

The OAuth JWT module exposes a FastAPI-compatible lifespan callable and a bound
request dependency without requiring `fastapi-runner`. Its state is published
through ASGI lifespan state, while a future `fastapi-runner[oauth2-jwt]` extra
will adapt that state to `LifespanMap` and enforce integration ordering. This
keeps the core module reusable while making the runner integration an explicit
adapter rather than an implicit dependency.

## Considered options

- Require `fastapi-runner` at runtime.
- Make the application manage startup and shutdown methods directly.
- Use the ASGI lifespan protocol as the core seam and adapt it to the runner.

The third option preserves framework compatibility and keeps lifecycle
composition visible to the application.
