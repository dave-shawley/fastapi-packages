# fastapi-runner

This context describes the vocabulary used by the reusable FastAPI runner,
OAuth JWT library, and their tutorial applications. It distinguishes
application-owned behavior from shared lifecycle, authentication, state,
error, and logging contracts.

## Application integration

**Application**:
The installed Python distribution that owns routes, domain behavior, and
application-specific configuration.
_Avoid_: library, runner

**Configuration hook**:
A callable that receives a `FastAPI` application and registers application
behavior before the application starts serving requests.
_Avoid_: settings hook, setup callback

**Lifespan hook**:
An application-lifetime async context manager that brackets startup and
shutdown work and may yield one application-scoped value.
_Avoid_: request dependency, startup callback

**Lifespan**:
The single ASGI lifespan callable composed by the runner from the application's
lifespan hooks.
_Avoid_: lifespan map, lifespan registry

**LifespanMap**:
The FastAPI dependency helper that retrieves the value yielded by one registered
lifespan hook while preserving that value's static type.
_Avoid_: lifespan state dictionary, request state

## Request behavior

**Application state**:
Library-owned state attached to the FastAPI application for configuration that
lasts for the application's lifetime.
_Avoid_: lifespan state

**Request state**:
Library-owned state attached to the ASGI request scope for information belonging
to one in-flight request.
_Avoid_: application state, user state

**Principal ID**:
An explicit, application-selected identifier for the authenticated human,
service account, or API client associated with a request.
_Avoid_: credential, Starlette identity, user name

**Problem detail**:
The structured `application/problem+json` error document returned by the
runner's default HTTP and validation error handlers.
_Avoid_: error payload, exception body

**Access log**:
The structured record emitted for a served HTTP request, including request,
response, duration, and optional principal information.
_Avoid_: audit log, authentication log

## OAuth JWT authentication

**Authorization server**:
The OAuth server that issues authorization grants and access tokens for a
trusted issuer and publishes the metadata or keys needed to verify them.
_Avoid_: identity provider, authentication service

**Trusted issuer**:
An authorization server identified by an exact `iss` value whose access tokens
and verification keys the application has explicitly chosen to accept.
_Avoid_: issuer URL, trusted identity provider

**Discovery mode**:
The configured method for retrieving verification information for a trusted
issuer: OAuth authorization-server metadata or a direct JWKS document.
_Avoid_: issuer locator, automatic discovery

**Token profile**:
The set of header, claim, cryptographic, and temporal requirements selected by
an access token's `typ` value, such as the initial `at+jwt` profile.
_Avoid_: token flavor, JWT mode

**Validated access token**:
A bearer JWT whose profile, issuer, audience, signature, required claims, and
temporal validity have passed the library's checks; it is not an authorization
decision.
_Avoid_: authorized token, authenticated user

**Key snapshot**:
A complete set of verification keys retrieved together for one trusted issuer,
with retrieval metadata and a validity interval that determine whether it may
be used.
_Avoid_: key list, stale key cache
