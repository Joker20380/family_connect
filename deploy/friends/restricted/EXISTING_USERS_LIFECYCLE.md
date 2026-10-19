# Existing users: private beta lifecycle and recovery

Current implementation/readbacks: [19 October delivery](../../../docs/releases/2026-10-19-existing-users-private-beta-1.md).
This replaces a per-user FIELD calendar, not cryptographic validity checks.

| Layer | Policy and maintenance |
|---|---|
| Entitlement | Existing activated, non-revoked registration, invitation and key proof; no trial expiry or new grant. Explicit revocations still deny. |
| Root | Existing offline root, never exported to RU/NL; each concrete delegation reviewed and signed through the vault workflow. |
| Delegation / same-key CA | Finite90days in explicit v2 mode, same Family/gateway scope and minimum revision. Operator renewal target by day60; advisory with14days remaining; existing6h hard gate remains. |
| Gateway/client leaf, CRL | At most4h, bounded by issuer validity. Existing approved controller renews leaf/CRL at90min remaining; revocation changes also make CRL due. No individual entitlement re-approval. |
| Directory | Actual runtime-bound publication, propagated RU/NL and validated independently. Its own expiry does not extend leaf/CRL. No manufactured timestamps or rollback. |
| Client readiness | Existing foreground/prewarm/reconnect refresh and native encrypted import/ACK; expiry and floors remain enforced. No new transport retries or endless polling. |
| HTTPS service certificate | Existing certificate-renew timer, separate from Family authority; no new TLS bypass. |

Authority18 was issued18 October2026 22:36:48UTC and expires16 January2027
22:36:48UTC. Plan operator renewal **by17 December2026 22:36:48UTC**; the
14-day advisory starts2 January2027 22:36:48UTC. The hard6h gate is16 January2027
16:36:48UTC, not a recommended maintenance appointment. These are shared operator
duties, not user registration/extension windows. External CRITICAL alert delivery
is still unavailable; the operator must monitor the existing controller receipts.
No new unattended root signing or background scheduler was created.

Ninety days is a bounded operational delegation, not an indefinite certificate.
It removes daily root ceremonies while leaving30days between the planned renewal
target and expiry. It increases issuer-compromise exposure compared with the old
one-day experiment. Same Family/gateway scope, explicit revocations, increasing
authority/CRL floors, short issued leaves and offline root custody mitigate but do
not eliminate that risk. Issuer compromise requires deliberate root-authorized
recovery/revocation, not silently lengthening validity. Validators on both nodes and
the existing native material validator were tested with the finite operational CA.

## Service paths on Android

- Normal initial preparation uses verified HTTPS on the underlay with the existing
  identity proof. When the app's MESH VPN is actually connected and healthy, its
  readiness HTTPS uses the ordinary VPN network instead of forced underlay binding.
- If the initial challenge fails with a network I/O error, the client may select the
  already pinned RNS control channel and keep the complete proof/fetch/ACK exchange
  on that channel. Only four fixed readiness paths are allowed; the relay forwards
  to the existing fixed HTTPS API with certificate verification. It issues no rights.
- Authentication/TLS-validation failures do not trigger fallback. An ambiguous
  state-changing proof POST is not blindly replayed on another path. Existing bounded
  request/refresh deadlines remain; synthetic local integration covers two identities.
- Reconnect can use still-valid encrypted material. When cached material expires,
  the ordinary authenticated readiness exchange can use HTTPS or the pinned control
  path. Expired credentials never become acceptable. If neither authorized path is
  reachable, recovery remains unavailable until connectivity returns; this is not a
  FIELD entitlement expiry and is not solved by re-enrollment.

No claim is made that direct TCP4242 is reachable on every restricted operator, or
that a root/CRL-valid session can start without any available network path. Physical
fallback under such restrictions and long unattended phone runs remain separate
acceptance evidence, not inferred from loopback tests. On19 October local, beta86
initial physical Connect/READY/DNS/HTTPS passed, then a normal scheduled rotation
committed and the client imported CRL27125. Subsequent TUN DNS failed twice. Thus
the current delivery is NOT_READY pending client recovery evidence; successful
automatic server renewal and fresh READY are not proof of restored application traffic.

## Publication, interruption and recovery

Use the installed version-pinned controller and existing serialized RU/NL operation
barrier. The approved scheduled scope covers leaf/CRL (including v2 revocations),
not unattended authority signing. It may briefly restart the existing gateway;
zero-downtime renewal is not claimed. Clients retain their identity and reconnect
through the existing mechanism. A running timer alone is not a renewal receipt.

Read the durable transaction and current committed snapshots before any retry.
Preserve CRL/authority/revision floors and revoked records after partial publication.
Forward-resume the exact operation through the existing controller. Never restore
the saved database, old credentials or the legacy grant-only API to make a check pass.
The private cutover snapshot is evidence/recovery custody, not permission to roll
security state backwards. The old Schema2 handoff history remains terminal.

The RNS extension is stateless and has a separate source transaction/backup. Its
launcher verifies the complete preview manifest before opening provider connections.
Rollback of that extension must restore the matching source cohort and manifest,
not weaken the verifier; keep RNS identity/state untouched. Loss of this extension
removes the fallback path but must not relax API authentication.

## Acceptance boundaries

Controlled-clock fixtures cover existing independent identities at day0/2/77,
revocation and normal same-key authority renewal at day60. Native public-material
validation uses its supported test clock. These are not months of physical uptime,
physical future-dated TLS handshakes, or months of unattended operation. One automatic
server renewal after this deployment is now observed and independently read back.
Beta86 export proves SESSION_READY/CONNECTED after rotation, then a separate carrier
loss and a terminal authenticated startup closure; two TUN DNS controls failed.
Beta87 corrects only that bounded-recovery classification. Sustained end-to-end
recovery is not accepted from these observations or local tests. Consult the delivery
report for the latest live receipt and the outstanding client recovery gate.
