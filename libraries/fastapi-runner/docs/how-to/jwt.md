# Integrate JWT access tokens

JWT verification belongs to the application. A lifespan hook is a convenient
place to load the verification key and policy once, while the authentication
dependency validates each request and records an explicit principal ID.

```python
def authenticate(
    lifespan: fastapi_runner.lifespan.LifespanMap,
    token: t.Annotated[str, fastapi.Depends(bearer_scheme)],
    request: fastapi.Request,
) -> JWTClaims:
    state = lifespan.get_state(auth_lifespan)
    claims = verify_token(token, state)
    fastapi_runner.state.set_principal_id(claims.principal, request=request)
    return claims
```

The repository's `tutorials/jwt` contains the complete ES256
verification example, including secret-backed key configuration and
`JWTClaims`.

Keep token issuance, key rotation, claims policy, and authorization rules in
the application that owns the identity system.
