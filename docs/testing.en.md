# Verification and acceptance

[Русский](testing.ru.md) · [Guide](../README.en.md)

## Automated checks

`cargo test --manifest-path core/Cargo.toml --locked` checks Ed25519 verification, wrong root,
modified bytes, expiry/future timestamps, epoch/issuance rollback, duplicate identity and relay
non-exit declarations. `python -m pytest -q` checks the control-plane verifier and schema.
Python-generated catalog signatures are additionally consumed by Rust in every integration run.

Docker builds run Rust and Python tests. GitHub Actions runs unit checks and the laboratory
integration scripts; a workflow definition is not evidence that a specific CI run has passed.

## Integration scripts

| Script | Acceptance |
|---|---|
| `scripts/test_failover.sh` | Kill relay A during a 16 MiB transfer; verify checksum/content, mTLS and one retained inner QUIC connection |
| `scripts/test_auth.sh` | CA-issued outsider certificate is rejected by the relay because it is absent from membership |
| `scripts/test_offline.sh` | Obtain signed cache, stop control API, start a new client and finish the transfer using valid cached state |
| `scripts/test_revocation.py` | Remove the synthetic client during a transfer, observe authorization closure, then re-enroll at a newer epoch |

Run in sequence, not concurrently: fault tests modify shared lab state. Scripts restore stopped
services and membership, but the catalog's epoch remains advanced. Unit checks validate expiry;
the offline integration test does not wait 15 minutes to test expiry of a live session.

Results are written under ignored `artifacts/`. Reviewed non-secret JSON results may be copied
into `docs/` with their generation/version explicitly stated. The old
`phase0-failover-result.json` describes the earlier shared-token version, not current mTLS.

## What this does not prove

The single Docker-host experiment is not a throughput benchmark or a multi-country network test.
The gateway intentionally paces generated test data. It does not demonstrate Android TUN,
DNS/IPv6 leak protection, gateway failover, hardware key protection, censorship resistance,
volunteer anti-abuse hardening, perfect transport recovery or production availability targets.

The reported connection count refers to the one inner QUIC connection, not to the two separate
outer relay connections. No reconnect/resume of the application download is used to claim
inner-session survival.
