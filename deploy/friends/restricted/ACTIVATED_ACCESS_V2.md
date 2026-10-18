# Activated-device access v2 — source candidate, not deployed

The owner requested replacing per-tester FIELD admission, not repairing its old
one-hour writer. All ordinarily activated Family Connect devices should be eligible;
the owner controls distribution of the research APK. This document does not claim
that production access has already changed.

**Do not switch the live policy file in isolation.** The installed current4h
management controller still implements finite-grant renewal and recovery. It must
be adapted and verified with this candidate before either API or policy activation.

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

The API wire response remains version1; no Android APK/schema/update catalog is changed.

## Remaining management rewrite

The live controller source was inspected, not patched or redeployed in this task.
The source candidate solves HTTP entitlement; it is **not** a replacement production
maintenance system. Necessary next changes are concrete:

1. Share the effective activated-device/revocation/revision predicate with management;
   do not maintain a second, divergent authorization implementation.
2. Stop using finite legacy grant expiry as v2 readiness/renewal authorization. Keep
   ordinary identity records and explicit revocations authoritative. Preserve all
   old rows/floors; do not reset the database or fabricate a historical checkpoint.
3. Adapt revocation planning for issued certificates whose devices have no legacy
   grant. The installed `GrantDatabase.plan` assumes each certificate has such a row;
   replacing the old1h validator alone does not satisfy this contract.
4. Bind access-policy mode to both nodes, source manifests, committed snapshots and
   recovery. An old controller or mixed-mode deployment must reject before writes.
   Exercise crash/retry/concurrent-enrollment and policy-change fencing.
5. Retain coordinated RU/NL publication, monotonic CRL/revisions and offline authority
   signing. Short-lived crypto renewal must not require re-authorizing each tester.
   Current live CRL failure needs fresh interval diagnosis and supported recovery;
   local API tests do not repair that failure.

## Rollout and rollback gates

After shared-controller tests and exact package verification, use the existing
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
