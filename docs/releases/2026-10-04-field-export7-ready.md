# FIELD export(7): fresh post-renewal tester readiness — 2026-10-04

## Input and boundaries

User supplied `FamilyConnect-diagnostics(7).json`,50598bytes, SHA256
`95697e262f5be1d2e898d9b2fdb5502a66e57949f4cdc75b74d9262e63d103b7`.
Support ID FC-YHQB-9VJN; reported version `0.1.18-beta61`/code61. This version pair
alone does not attest installed APK bytes/signature or distinguish original61/r2.
Accepted r2 artifact remains [independently verified](2026-10-04-beta61-r2-direct-delivery.md).
This task only reads client/server evidence and updates documentation. No APK rebuild,
signing, installation, server mutation, mobile test, security bypass or admission change.

## Client evidence

Latest ring contains128 events08:43:28.606–08:58:11.834UTC, WIFI/CONNECTED,
AWG SUCCESS;125 recorded DNS_PROBE_OK events. This is evidence of the recorded
successful probes, not proof of uninterrupted availability between samples.

| Client UTC04.10 | Readiness event |
|---|---|
| 08:44:55.981 | NATIVE_VALIDATION_FAILED |
| 08:49:55.924 | NATIVE_VALIDATION_FAILED |
| 08:58:11.277 | READY |

Final client readiness READY, bootstrap directory USABLE. Wi-Fi connection ID
`22ee62e1-f540-4edf-b45c-96c6757664ec`, incident ID
`0e4944f6-1157-48d9-9c5d-fda52c9deb4c`.

The persisted `incident` object equals export(6)'s incident object exactly: old
08:28 mobile attempt, connection `11cea884-22ce-4b90-8e67-e365320539af`, incident
`c7594804-0855-4748-becb-6f68cac4c9f9`. It is not a new failed mobile test.
Both records have empty restricted_session/history; no new restricted session or
session_tag exists in this export. No evidence of a regression of session-tag parsing.

The client failures align with the [previously recorded authenticated failure ACKs](2026-10-04-field-export6-readiness.md#authorized-prerequisite-restoration).
Client event times precede the respective integer server fetch timestamps; this is
consistent with the previously identified time-validation lead, but does not measure
clock offset or identify the exact failed native branch. Do not infer that later READY
proves the intermittent import defect permanently fixed or that the original transport
disconnect is fixed. No validator/clock/credential-lifetime change was made.

## Independent live server evidence

RU09:01:24UTC, tester's normal authenticated readiness flow:

- Challenge08:58:10UTC, fetch08:58:11UTC, ACK08:58:12UTC.
- App beta61/code61, READY, provisioning/bootstrap PRESENT_VALID,
  orchestrator_usable=true, failure_reason=NONE.
- Same grant revision1; delivery minimum CRL3556; expiry**09:12:39UTC**.
- Exactly2 devices admitted/non-revoked; owner receipt remains expired and is not
  substituted for tester readiness.

NL09:01:27UTC:

- Restricted gateway active, PID3757156/restarts0, same accepted diagnostic binary
  `b9b7d542e6f196e2ffcfb9e913f1d065cf83529bb29726ec93daca740a241217`.
- Actually served certificate matches profile and verifies against the issuer;
  expiry09:39:30UTC, authority expiry14:13:53UTC.
- RU/NL directory bytes match SHA256
  `541fd9aeabd0ef8a53fd0c4ffed77403c0e43efd45d43c237b3aee9d44dac49a`,
  issued08:39:34.925582899UTC, expires09:34:32.702517154UTC.
- Signed CRL3563 matches on both hosts, expiry09:16:24UTC. Existing RU sync timer
  active, service last exit0. The delivery's earlier CRL3556 is its recorded floor,
  not evidence that background sync must stop advancing.
- RU beta60 discovery and invitation-page hashes remain unchanged
  (`6e5817dc…` and `014ebdbd…`). No distribution/updater write performed; signed
  catalog's independent public verification remains in the preceding report.

Safe private receipts: `state-client-build/field61-r2-diag7/`. Bounded privacy screen
PASS: expected export/event schema, empty session payloads, no URL/private-key/Bearer
pattern; not a universal detector of all possible secret encodings. Raw client
exports, credentials, profiles and product database are not committed.

## Decision and next step

Post-renewal tester readiness gate now passes for the observed short-lived window.
Within that window, disconnect the existing Wi-Fi AWG session, switch to mobile data
and perform exactly one ordinary Auto connection attempt. Export immediately after
failure/disconnect before another attempt and collect only bounded structured gateway
events for that interval. A successful AWG/TCP fallback is not restricted-session proof;
the actual selected transport and session lifecycle must be established from evidence.

If the attempt is delayed, recheck fresh tester READY/ACK and gateway/issuer/CRL/directory
before testing. Do not rely on this report after expiry or clear data/reenroll to retry.
No new invitation, FIELD expansion or production beta60 change. Original restricted
disconnect/RKN attribution and intermittent native-validation cause remain open.

No runtime rollback is needed for this read-only task. Existing credential-renewal
rollback restrictions remain: never restore expired credentials as healthy or lower
security floors. Documentation link/diff checks are the applicable local validation;
no product code changed and no product build/test suite was rerun.
