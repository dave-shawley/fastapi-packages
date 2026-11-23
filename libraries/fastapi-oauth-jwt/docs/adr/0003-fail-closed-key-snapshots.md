# Verify only from complete, fail-closed key snapshots

Metadata and JSON Web Key Set (JWKS) retrieval produces an atomic complete
snapshot for each trusted issuer. The cache honors HTTP freshness information
within configured bounds, primes snapshots during startup without making
transient retrieval failures fatal, refreshes once for an unknown `kid`, and
never verifies with an expired snapshot or mixes keys from different snapshots.

This favors a predictable trust contract over indefinite availability. A
previous snapshot may be retained for refresh and diagnostics, but it is not
cryptographic authority after its validity interval ends.

## References

- [RFC 7517: JSON Web Key (JWK)](https://www.rfc-editor.org/rfc/rfc7517)
