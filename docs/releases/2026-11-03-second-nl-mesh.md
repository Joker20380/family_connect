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

## Shared-authority follow-up —3 November17:20UTC

The leaf/CRL checkpoint `7d3fac77a765cc7e9f28fbe6a6e688c9bb2d2047` is committed,
pushed and remote main verified. Follow-up source now supports **planned** offline
authority renewal before expiry for the whole fleet. RU produces one request with
two independent delegation successors referencing the exact same renewed issuer CA.
The offline-only signer validates both scopes and returns two signed handoffs; the
root key never enters the server package. Both handoffs must match the operation,
predecessors, membership and common successor CA. Missing/swapped/partial handoffs,
wrong Family/gateway/operation, expired bundles and incoherent CA requests are rejected.
Delegation sequences may differ and each advances by one; issuer/gateway keys and
admissions remain unchanged. Planned authority renewal still requires explicit operator
maintenance approval; the leaf/CRL schedule cannot silently approve that outage.

Both RU delegation files and both gateway profiles participate in the same durable
transaction. Tests include faults between individual authority-file writes, rollback
before commit, roll-forward after commit and a subsequent ordinary leaf/CRL cycle.
Explicit registry-overlay recovery now also handles an expired secondary leaf when
the primary leaf is still valid. It preserves only validated append-only device/invite
additions, retains all historical/restricted-state checks, verifies both gateway
snapshots and leaves every reader stopped. It does not silently change historical rows.

Checks:358 selected user-space/native/package cases PASS, plus one independent-sequence/
operator-approval case PASS;326 isolated-root cases PASS, including90 fleet cases also
covered in user space.595 distinct selected cases PASS,0 skips; repeated cases are not
counted twice. The accepted beta111 native compatibility check is included. Source
packages in these tests are synthetic fixtures, not installed production artifacts.

**Remaining acceptance gap:** recovery when the fleet's root-signed authority has
already expired is still rejected before writes. Planned renewal and expired-authority
recovery are different operations; the former does not prove the latter. Finish this
contract before replacing the production writer, then run permanent AMS2 and real
data-plane acceptance before Android publication. Existing ordinary AWG/TCP and primary
MESH services, installed/public versions and catalogs were not changed in this turn.
The preceding slice's unsupported planned-handoff/registry-overlay boundaries below
describe that checkpoint only and are superseded by this section.

### Exact source/package readback

Source `e96334deb3f654d95a3a37de2e69a2276f1fb395` committed, pushed and remote main
verified. Two independently packaged archives from that exact committed source are
byte-identical, with absent production configuration and no operation permit.
Archive SHA256 `88fba405c5494aece6a1ef8cdf4b264fd00a0fcdc69de411652af6bdf3eb445c`;
module-set SHA256 `cfab7cab89411fd440979c000683883860a573d5ea9fb2dfc84f57c15da923c9`;
pinned API SHA256 `4779cb3be76b2efdeb45efadf75d8e320a0aedfc602540ff0fc4cc48ae478d8c`.
12 canonical profile/source-construction cases PASS against this exact archive in the
isolated root container, including both gateway slots and tamper rejection. These are
repeat validations, not12 additional distinct cases. Archive and private receipts remain
under `state-client-build/mesh2-renewal-20261103/`; nothing was installed or distributed.
Existing unrelated working-tree changes remain untouched. Next selected work remains
whole-fleet expired-authority recovery, not an unrelated queued task or immediate APK
publication. Production activation and Android update are still unfinished.

## Coordinated renewal source —3 November17:10UTC

Implemented an opt-in three-node transaction rather than a second independent writer.
All node configurations carry the same distinct `gateway_ids` map (`NL`, `NL2`) and
their own `gateway_slot`; wire RPC roles remain `RU`/`NL`. Runtime controller schema2
adds a separately pinned secondary SSH/source route and retains the existing RU state
directory/lock. Legacy pair mode remains available only for non-fleet configurations.
A pair-only controller refuses opted-in fleet nodes before acquisition or service stops.

RU prepares one shared CRL/grant plan and two gateway-specific leaf successors. Both
signed delegations bind the same Family/CA/revision floor, distinct gateway identities
and keys; certificate role/SAN/revocation and profile replay floors are checked before
mutation. Only a due secondary leaf can renew without unnecessary primary/CRL changes.
Stage/promote/readback/commit require all three identical plan/CRL receipts. Both
gateways resume first; their independently validated fresh directories must be read
back on RU before its API resumes. Revocation advances one shared CRL sequence.

Tests cover interruption before/after commit, missing/wrong secondary receipts,
secondary RPC failures and reconnection, stale/incorrect gateway material, immutable
keys/identities, incomplete directory receipts and expired-secondary fenced rollback.
An unreachable secondary after commit leaves RU fenced until reconciliation succeeds;
no automatic fallback substitutes primary credentials for the second gateway.

**Incomplete production gate:** multi-gateway offline authority handoff and expired
authority recovery, plus historical registry-overlay recovery, explicitly fail closed.
They are not claimed as implemented by this leaf/CRL slice. Do not deploy this slice
alone or switch the active pair writer to schema2 yet. No permanent runtime, selector,
server configuration, Android version, signature or public catalog changed.
Public versions remain Android111/catalog6, Windows0.2.16/catalog12, Linux0.2.11;
owner-local Linux0.2.12~l03.2.13 is not a public rollout.

Private validation evidence: `state-client-build/mesh2-renewal-20261103/`.
An initial broad invocation incorrectly included root-DAC tests as UID1000; those
permission assertions were not relaxed. Root suites moved to a network-disabled,
read-only container with sanitized source and synthetic profiles. Initial container
setup omitted the client Python imports and retained exact snapshot archive; both
fixtures were supplied without changing their assertions or production material.
Final checks: **334 PASS** in the locked control/identity user-space environment,
including66 multi-gateway transaction/runtime tests and the accepted beta111 native
compatibility validator; **236 PASS** in the isolated root container, including source
pinning/canonical profile construction for both gateway slots. **570 PASS,0 skips**
across the disjoint final selections. Package fixtures are synthetic source commits,
not a released production artifact. Whitespace checks PASS.

Rollout remains gated by complete shared-authority/recovery acceptance, source-pinned
package qualification, fresh permanent identity/runtime and real READY/TLS/DNS/HTTPS,
egress, negative/revoke/cancel/shaped-link and cleanup checks. Only then enable selector
visibility and build a new immutable Android version above111/catalog sequence above6.
Rollback must preserve the current pair services/configuration and private backup
evidence; do not downgrade an active fleet to a pair-only writer while AMS2 serves MESH.
No rollback is needed for this source-only checkpoint because nothing was installed.

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

### Android CI/artifact readback —16:50UTC

Exact source142ee46 Android job126044369850 in run41672473840 is **completed/success**,
including API27/API35 runtime, pinned native build and final unsigned Friends packaging.
The overall workflow is **failure** on its Linux GTK job; Windows/compatibility PASS,
release job skipped. This is not an all-platform or public-release PASS.

Downloaded artifact13250802064, ZIP57292031bytes,
SHA256 `b0ae3a199d91e8084a00eaa900f404c1f5600db496f482b7649b40decd37f947`.
Unsigned APK50248193bytes,
SHA256 `ad15a285bc5393b0d2f66db845e65b40120841dacf67a98474d006d4a50c99a5`;
CI native SHA256 `4681dd3d594ff1c237b82f0340995b6428c8cb2ca7a09d7bae5620ca0a7d5bdf`.
Receipt/source/tree/native payload, production tags, pinned Xray, package identity,
ARM64-only, minSDK27/target35, unsigned status and all12 native libraries'16K PT_LOAD
alignment verified locally. The CI native hash differs from the separately retained
local build; each matches its own source-bound manifest. Bitwise cross-host reproducibility
is not claimed. First local badging assertion expected `sdkVersion`; aapt2 reports
`minSdkVersion`. Corrected the reader without modifying APK bytes; both outcomes retained.

**Not distributable as111:** it still has beta111/code111 metadata and different bytes
from the immutable public111. No signing, installation, tag/catalog/invitation publication
or server update was performed. Production MESH2 acceptance and a fresh higher-version
client build/delivery remain required. Source changes through0775711 were pushed and
remote main verified; existing unrelated working-tree changes remain untouched.

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
