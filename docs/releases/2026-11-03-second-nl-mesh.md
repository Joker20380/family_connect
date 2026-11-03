# FLEET-BOOTSTRAP-2 — second Amsterdam MESH integration

## Current result

**IN PROGRESS; first backend source slice qualified, NOT DEPLOYED.** Owner explicitly
asks to finish MESH2 using the separately supplied credential. This supersedes the
question-only interpretation in the earlier [picker report](2026-11-03-android-node-picker.md).
No claim that source publication enables MESH on an installed client.

## Reconciled evidence

- [Physical rehearsal and reboot](2026-11-02-fleet-bootstrap-2-reboot.md) already proved
  room/join/READY/Family registration/TLS/DNS/HTTPS/expected egress on the second VPS.
  Those temporary services and leaf materials were retired after acceptance. This is
  not a hardware or provider incompatibility, nor permanent-production acceptance.
- The separate publisher input exists locally,0600, with a nonempty token and scope.
  Only presence/schema metadata was inspected; no token or room URL was printed,
  transmitted, copied to a server or committed. Current provider validity was not
  rechecked. Fresh runtime/leaf identities are required; no retired permit is extended.
- Read-only SSH to AMS2 using its existing strict owner-accepted host pin finds both
  ordinary services active with0 restarts; permanent restricted bootstrap and its
  production directory are absent. No ordinary connection was changed.
- Read-only RU inspection confirms existing primary readiness and a source-pinned
  renewal/directory-sync installation. It is a two-role RU/NL controller, not an already
  deployed multi-gateway renewal mechanism. Do not launch two writers against its state.

## Qualified source slice

Existing restricted-readiness endpoints accept an optional exact wrapper:
`{"gateway_id":"nl-amsterdam-2","request":{...existing request...}}`.
Successful targeted replies use `{"gateway_id":"nl-amsterdam-2","response":{...}}`.
The inner delivery remains schema1 for the native validator. Untargeted requests are
byte-shape compatible with existing clients; explicit Amsterdam1 addresses the same
primary authority. Only the two existing Amsterdam identifiers are allowed. The JSON
wrapper survives the existing bounded readiness relay without new routes or relying
on headers that the relay does not forward. It does not change provider, transport,
enrollment, proof signing or admission policy.

Secondary public issuer/directory material is loaded from the configured restricted
root's `gateways/nl-amsterdam-2/` directory. Root signature, validity, identical Family,
authority and minimum revision, and a distinct gateway identity are required. Shared
issuer key, admission policy and CRL stay at the existing authority root; no gateway
private key is cloned. Missing, mismatched or symlinked secondary material fails closed
without disabling the legacy route. Shared device certificates and entitlement records
are retained, not reenrolled or reassigned.

Secondary challenge purposes bind the explicit node and its signed gateway identity.
Import correlations/ACKs carry the same server-side binding; a proof or receipt issued
for one node cannot be used on the other, and a failed cross-node attempt does not
consume a valid proof. The additive receipt migration defaults old rows to the legacy
primary binding. Existing primary challenge/ACK purposes are unchanged. Migration is
explicitly required before deploying this source; it has NOT run on production.

## Validation

Locked control/identity Python environment and locked Go toolchain:

`python -m pytest -q tests/test_restricted_gateway_selection.py tests/test_friends_restricted.py tests/test_readiness_receipts.py tests/test_readiness_ack_artifacts.py tests/test_android_challenge_contract.py tests/test_restricted_activation_http.py tests/test_paid_beta_readiness.py tests/test_restricted_correlation.py tests/test_readiness_relay.py`

With `FC_TEST_GO` set: **265 PASS,2 optional environment skips**. Includes both targeted
deliveries through the actual Go native material validator, legacy compatibility,
packaged HTTP and relay forwarding, migration replay, mismatched signatures/Family/CA/
revision/identity, symlinks, absent material, cross-node/replayed proofs and ACKs,
gateway identity replacement, device/invitation/grant and shared certificate revocation,
and identity/entitlement conservation. No real provider or user traffic in this suite.
Initial failures exposed an expired-readback regression and an incorrect test expectation
for the cryptography exception; both corrected. An interim header-based prototype was
discarded before publication because the readiness relay does not forward that header.

## Mandatory remaining gates

1. Permanent secondary profile and distinct identity, canonical custody and pinned runtime;
   provider credential validation without disclosure. Preserve primary/ordinary services.
2. Coordinated renewal, directory sync, shared CRL/revocation propagation and fencing;
   no secondary gateway left accepting stale material after a primary maintenance event.
   Test interruption/restart/reconciliation and independent failure isolation.
3. Client route propagation, per-node encrypted readiness/receipt namespaces and independent
   rollback floors, including restart, switching, cancellation and legacy cache preservation.
   Never silently substitute primary readiness for a request targeting the second node.
4. Real external MESH READY/registration/TLS/DNS/HTTPS/AMS2 egress plus rejection/cleanup,
   current-user and ordinary-path conservation, then enable the qualified selector.
5. Deliver a new immutable Android version greater than111, with the pending picker fix,
   exact platform/API27/API35/native/artifact gates, existing-key offline signing, an
   increasing signed update sequence and full public download/invitation readback.

## Versions and rollback

Android0.1.18-beta111/code111/catalog6 stays public, Windows0.2.16/catalog12 unchanged,
Linux public0.2.11 and owner-installed0.2.12~l03.2.13 unchanged. No APK or client version
changed, no release tag/catalog/invitation publication, no production writes/restarts.
Existing [111 delivery/rollback](2026-11-03-android-update-incident.md#beta111-publication-and-readback)
and [ordinary admission](2026-11-02-second-nl-ordinary-live.md) remain in force.
Current slice needs no runtime rollback because it is not installed. A later rollout
must retain the previous exact API package, additive migration receipt and renewal
configuration; do not restore product DB or roll published catalogs backwards.
