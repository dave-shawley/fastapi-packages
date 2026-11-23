# Use the tutorial authorization server as a test-only issuer

The monorepo's authorization-server tutorial is an independent application
that implements the local OAuth authorization-code flow, RFC 8414 metadata,
and JSON Web Key Set (JWKS) endpoints. The OAuth JWT library may depend on it
through its development dependency group for integration tests, but the tutorial
is never a runtime or published-library dependency and does not depend back on the
verifier module.

This keeps one realistic issuer implementation for exposition and validation
without creating a workspace cycle or duplicating an authorization server in
the library's tests.

## References

- [RFC 8414: OAuth 2.0 Authorization Server Metadata](https://www.rfc-editor.org/rfc/rfc8414)
