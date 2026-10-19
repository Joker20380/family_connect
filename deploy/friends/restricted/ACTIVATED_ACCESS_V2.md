# Activated-device access v2 — private beta control plane

19 October local /18 October UTC: the exact-base API and compatible RU/NL management
are installed with explicit v2 policy. Authority18 is committed, same-key and same
Family/gateway. This is not yet an end-to-end APK upgrade acceptance: see the
[private beta delivery record](../../../docs/releases/2026-10-19-existing-users-private-beta-1.md).

**Do not switch the policy file in isolation.** Management/API/configuration form
one version-pinned cohort. Old grant-only writers cannot safely replace this cohort.
The historical candidate-only findings remain in the dated preflight report.

## Separate entitlement from credential validity

The candidate recognizes an explicit operator-only policy:

```json
{"version":2,"eligibility":"all_activated"}
```

This is intentionally not the legacy `{"devices":["*"]}` auto-grant mode.
Legacy files/constructor behavior remain unchanged. Unknown, mixed, duplicate or
mistyped fields fail closed; requests cannot choose their own admission policy.

In v2:

- Entitlement derives from an existing non-revoked device and its non-revoked
  activation invitation. No anonymous access, identity replacement or re-enrollment.
- A successful proof is still required. Identity/WireGuard binding, nonce purpose,
  expiry, one-time use and revalidation between challenge and fetch remain enforced.
- No `restricted_grants` row is created for a newly eligible device. A virtual
  issuance record supplies the signed Family/minimum revision and no entitlement
  expiry; this record is not a new database grant or an indefinite certificate.
- Existing grant revocations, wrong-Family bindings and revisions below the signed
  floor still deny access. Existing valid higher revisions are retained. V2 explicitly
  stops treating an old finite FIELD grant's expiry as the user's entitlement expiry;
  the stored row is not modified. Returning to legacy policy restores its old expiry
  semantics, which may deny access and is not a guaranteed operational rollback.
- Issued certificates remain tracked in `restricted_certificates`. CRL publication
  checks the same effective authorization, including devices without legacy grants.
  Device/invitation revocation prevents new issuance and includes issued certificates
  in the next CRL; it is not an instantaneous claim about remote active sessions.
- Issuer/CRL/certificate/directory validity and security floors remain enforced.
  An expired CRL makes issuance unavailable, not anonymous and not permanently
  unauthorized. After fresh valid material, the same activated identity can refresh
  without another grant. The accepted maximum remains14400s; no TTL extension.
- Support lookup reports `ELIGIBLE` separately from readiness. It must not equate
  policy eligibility with a valid TLS chain, native READY or working Telemost traffic.
  Old manual FIELD enable/disable fails closed on the v2 schema.

The API wire response remains version1. Beta85 changes service-path selection and
presentation, not identity/storage or native transport. No public updater is changed.

## Installed management and lifecycle

The exact API archive is `e986f98e70ff7f1abc2678566dd360bb6555583f2e1744ea985c63699bcb3ef7`;
both management source manifests are `c67332cfff9aeafd90690c13518f55a75ef9687ceadb464624263657ff005ff2`.
The management adapter uses the API's effective activated-device predicate, including
explicit device/invitation/grant revocations. Certificates without legacy grants are
tracked and included in revocation planning. V2 ignores only legacy trial expiry,
not revocation, binding or revision checks. No fabricated grants are inserted.

Admission mode is bound to both nodes/snapshots; mixed mode fails closed. Schema2,
CLEANED history and floors remain unchanged. Serialized publication retains the
existing forward recovery/commit receipts; no database rollback is an allowed repair.
Scheduled inspection and the operator CLI also select the explicit v2 validator.

See [operational lifecycle](EXISTING_USERS_LIFECYCLE.md) for finite90-day authority,
4h leaf/CRL, scheduled refresh, operator deadlines and physical test limits.

## Rollout and rollback gates

For subsequent authorized cutovers, after tests and exact package verification, use the existing
coordinated maintenance barrier. Preserve the previous source/configuration and
private database snapshot using the established custody procedure. Install compatible
management/API sources, switch policy as part of the observed transaction, validate
strict served chain and both current directories, restore the previous scheduling
state, then verify a newly eligible device's proof/fetch/ACK. Do not publish the APK
or ask for repeated CONNECT attempts to compensate for a server authorization error.

A legacy rollback cannot simply restore the former two-device list: newly issued
certificates may still be valid and their revocation must be published with increasing
floors before removing the new policy. Restoring an expired issuer/CRL or reverting
the database is not safe rollback. Rollback acceptance is still outstanding.

## Local validation

`tests/test_restricted_activation_policy.py` exercises strict policy loading,
existing/new activated devices, no grant writes, legacy expiry semantics, explicit
revocation, wrong Family/revision, nonce/replay and identity binding, material refresh
after more than four hours, CRL inclusion and support eligibility/readiness separation.

`tests/test_restricted_activation_http.py` runs the packaged HTTP archive on isolated
loopback: old-policy rejection followed by v2 issuance without re-enrollment/grant,
revocation between proof steps, request/configuration negatives and a real synthetic
four-hour CRL. No production identities, provider rooms or physical clients.

See [dated results and limits](../../../docs/releases/2026-10-18-telemost-all-activated-preflight.md).
