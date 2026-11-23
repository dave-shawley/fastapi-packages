# Use strict token profiles and delegate JOSE operations

The verifier dispatches validation by the JWT `typ` header through an internal
policy structure. The first supported profile is strict RFC 9068 `at+jwt`; an
unknown type is rejected rather than falling back to generic JWT validation.
PyJWT together with `cryptography` owns JOSE parsing, key conversion, and
cryptographic verification, allowing this module to concentrate on trusted
issuer selection, profile policy, and the validated access-token interface.

## Considered options

- Accept generic JWTs with configurable claim checks.
- Implement JOSE parsing and cryptography inside this module.
- Use a narrow profile dispatcher and rely on the established PyJWT and
  `cryptography` libraries.

The third option keeps the security-sensitive cryptographic implementation
behind a replaceable internal seam and avoids making this module a second JOSE
implementation.

## References

- [RFC 9068: JSON Web Token (JWT) Profile for OAuth 2.0 Access Tokens](https://www.rfc-editor.org/rfc/rfc9068)
