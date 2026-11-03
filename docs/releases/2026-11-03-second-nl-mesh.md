# FLEET-BOOTSTRAP-2 — second Amsterdam MESH integration

## Current result

**RESUMED: permanent MESH2 first, then Android update; SOURCE CHECKPOINT, NOT DEPLOYED.**
The latest owner request explicitly selects second-server activation followed by the update.
The intervening [connection-quality work](2026-11-03-mesh-slow-link.md) is source-checked
and must be included with the picker fix in the resulting release, not published as111.
No permanent second-node runtime or new APK has been deployed. Owner explicitly
asks to finish MESH2 using the separately supplied credential. This supersedes the
question-only interpretation in the earlier [picker report](2026-11-03-android-node-picker.md).
No claim that source publication enables MESH on an installed client.

## Resumed production preparation

Read-only SSH confirms the current RU node configuration at
`/var/lib/fc-profile-control/pinned-venv-cutover/node.json` uses the source-pinned
`renewal-overlay-e822b391a43d` API and only the AMS1 snapshot route. Credential-renewal
and directory-sync timers remain active. AMS2 retains its ordinary AWG/TCP directories;
no permanent restricted service/directory was found. Historical failed transient units
were not restarted or mistaken for the current timer result. No deployment was attempted.

The new optional `scheduled_evaluate.py --gateway-routes` source path supports exactly
Amsterdam1/2 with separately pinned SSH destinations and expected signed identities.
It preserves the existing primary CLI route and rejects duplicate identities/hosts.
Both snapshots must have the current shared Family/CA/revision/CRL, valid gateway leaf
role/key/identity, a non-revoked serial and a valid replay floor. The secondary root-signed
delegation must be distinct and current. Each directory is validated for its own node,
time and monotonic publication; same-time changed contents and older directories fail
closed. Subsecond instants are retained. Provider URLs/certificates/keys are not printed.

Directory-only mode writes only the corresponding existing directory file under the
RU maintenance lock. An in-flight maintenance owner prevents reads/writes. A failed
node keeps its previous file while the healthy node can synchronize; the overall result
is non-success (`GATEWAY_CHECK_REQUIRED`, exit75), never fallback to the first node.
Near-expiry credential warnings remain in per-node receipts. This mode does not issue
certificates, publish CRLs, restart services or perform the missing multi-node transaction.
It is not installed or configured on production and does not make an old pair-only
renewal controller safe for an active second MESH gateway.

Validation in the locked control/identity environment:
- 58 focused route/snapshot/directory tests PASS.
- 164 broader maintenance, package and profile-snapshot tests PASS,1 explicit native
 fixture skip. That check then separately PASSed with the retained exact beta111 carrier
 source and locked Go toolchain: existing identity delivery through two renewals, including
 75-day authority age. Total165 distinct selected tests PASS; no outstanding skip.
- Closed renewal package preserves source hashes and reproducibility, imports the new
 path against its pinned API, and retains legacy CLI/RU–NL renewal checks.
- No physical Telemost/Family data-plane acceptance is claimed by these synthetic tests.

Private logs: `state-client-build/mesh2-production-20261103/`. At16:38UTC exact142ee46
Client builds41672473840 had passed the Android15 runtime stage and was running the
Android8.1 lifecycle stage; unsigned final ARM64 artifact acceptance remained pending.
Linux GTK interaction and phase0 setup failures remain separate, not waived or repaired.

Follow-up source review aligns leaf revision validation with native Family TLS: a leaf
revision above the configured minimum is valid; below-floor/malformed revisions are not.
Final combined locked selection: **168 PASS,0 skips**, including the accepted beta111
native delivery validator. Initial optional skip and earlier logs remain retained.
Checkpoint `c902e79db115199c98a19708fd46e34e245b5c89` is pushed and remote main verified.
At16:46UTC Android job126044369850 had passed API35/API27 and the pinned native build;
unsigned ARM64 packaging was running. No final artifact or public release acceptance is
inferred from intermediate CI steps. This candidate still has111 version metadata and
must not replace the immutable published111 APK.

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

## Android source checkpoint

Backend commit `e7d2739f2f1c15632532e0c6e47c4184beb8dd51` is pushed and remote-verified.
The Android follow-up adds `RestrictedGateway` target validation and response unwrapping
outside the existing HTTPS/relay selection policy. Primary/legacy requests are unchanged;
secondary requests cannot silently accept a primary, unwrapped or malformed response.
No redirect, proof retry, enrollment route or authorization bypass is added.

Secondary readiness uses its own encrypted file, AndroidKeyStore key and AEAD associated
data; primary filenames/aliases remain exactly the same. Receipt files, refresh futures,
restart reconciliation, observations and denial flags are also separate. Existing
`RestrictedCache` checks are retained independently; no reset or relaxed antirollback
comparison permits switching nodes. `AutomaticConnection` propagates an explicit node
to `RestrictedTunnelEngine`, readiness fetch/ACK, cache and native delivery setup.
Default Auto/chat paths still use primary readiness. UI admission is deliberately NOT
enabled: the country-only MESH picker and ordinary-only explicit-node UI guard remain
until permanent runtime/renewal and real connection acceptance are complete.

Validation:

- JVM **410 debug +405 Friends PASS**, including target wrapping, wrong-node/legacy
  response rejection, relay preservation, no retry, endpoint bounds and separate cache
  replay/denial floors. Friends lint **0 errors/56 warnings**; APK/test APK build PASS.
- **88 Python contract/closed-artifact checks PASS**, including the exact pinned offline
  sync/HTTP/native ACK fixture previously skipped. Current fixtures bind backend commit
  e7d2739 and the packager's required Go1.26.0. The initial invocation lacked fixture
  environment variables. The generic fixture preparer also cannot rebuild the old HTTP
  fixture with today's additional gateway-location template; the already retained exact
  historical artifact was SHA-verified and supplied instead. No history pin or test was
  weakened, and the unrelated historical packager behavior was not changed.
- Disposable read-only-overlay emulators **API27 and API35 prepare/recover PASS** in
  separate instrumentation processes with force-stop between them. Real AndroidKeyStore
  stores both synthetic values independently; primary aliases remain compatible;
  substituting ciphertext, losing the secondary file or key fails closed and cannot
  regenerate/reset it. Primary ciphertext stays byte-identical. Owned synthetic files
  and aliases are removed after recovery; raw instrumentation status0 confirmed, not
  an assumption skip. No user keys or profiles were imported into these tests.
- UI regression API27 **4/4 PASS**; API35 first **3/4**, failing the existing messenger-tab
  open timeout, then **4/4 PASS** after app force-stop without source changes. Activity
  launch was accepted and no Java crash was captured; root cause is not established.
  First failure is retained, not erased by the repeat or claimed repaired.

Only locally CI-signed x86_64 development APKs using the unchanged111 version metadata
were installed on disposable overlays. Their signer differs from the base emulator
installation, so reinstall used only those disposable overlays; immutable public111
and real installations are untouched. These artifacts must never be distributed as111.
This is neither an API27/API35 full transport matrix nor new-platform release acceptance.

## Mandatory remaining gates

1. Permanent secondary profile and distinct identity, canonical custody and pinned runtime;
   provider credential validation without disclosure. Preserve primary/ordinary services.
2. Coordinated renewal, directory sync, shared CRL/revocation propagation and fencing;
   no secondary gateway left accepting stale material after a primary maintenance event.
   Test interruption/restart/reconciliation and independent failure isolation.
3. Live acceptance of the implemented client routing/storage slice, including active-session
   switching, cancellation, restoration and legacy cache preservation; qualify UI activation.
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
