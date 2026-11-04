# FLEET-BOOTSTRAP-2 — second Amsterdam MESH integration

Current: [permanent fleet activation and live data-plane](#permanent-fleet-activation-and-live-data-plane).
Earlier checkpoints below retain their original timing, not simultaneous active NEXTs.

## Permanent canonical secondary installation

3 November19:51UTC: **INSTALLED / INACTIVE**, not a production acceptance PASS.
The new AMS2 identity received its own75-minute bootstrap leaf from the current RU
issuer, using only public identity/delegation input. The issuer key stayed on RU;
the existing offline-signed secondary delegation and shared CRL floor27259 validated.
Neither existing identity, grants, assignments, CA nor revocation state changed.

On185.10.158.196, the permanent root-controlled profile and locator are installed under
`/etc/fc-canonical-mesh2/`. The dedicated reader/publisher account has UID/GID993;
profile0640 and parent0750 are root-controlled, the directory publisher parent is01770,
and lock/transaction custody remains root0700 outside the publisher directory. No fake
directory was created. Gateway9d41f1dc… and snapshot4373585a… are installed in the fixed
root-owned tools directory; the qualified renewal package remains private/root-owned.

Actual final-account Python3.12 runtime/dependency/package pinning PASS. A fixed forced
SSH launcher accepts only `restricted-sync`; the existing RU sync public key has no
shell, forwarding, PTY or user-rc authority. The RU private SSH key did not leave RU.
The target uses the already accepted AMS2 host pin, with strict checking. The narrow
sudo helper takes no arguments and uses one pinned node configuration/source package.
Actual RU→AMS2 `inspect` and public-gateway RPC PASS, with no private key in responses.
SSH command override and sudo argument override reject; final reader can read required
public/profile routes but cannot write profiles, locator, snapshot configuration or
executables, or read private node-control files.

First install stopped before launcher/unit creation: umask077 made the newly-created
tools ancestor0700, so the real-account package probe correctly rejected it. Readback
confirmed the cause. Only that newly-created ancestor was changed to0755; continuation
then passed construction, canonical boundary, runtime and systemd verification. The
failed first attempt remains in private evidence, not erased or reported as first-pass.

The bootstrap unit is installed but disabled/inactive; provider credential is absent.
Ordinary AWG/TCP PIDs/restart counts are unchanged. AMS1 runtime/profile/forced route and
the RU active pair controller are unchanged. No selector, Android version or catalog
change. Private receipts/scripts/keys remain ignored under `state-client-build`.
Rollback at this checkpoint is to leave the new unit disabled/inactive and exclude it
from the active pair configuration; do not delete custody or lower any replay floor.
Next: coordinated single-writer cutover, genuine provider directories and first confirmed
fleet checkpoint; real READY/Family TLS/DNS/HTTPS/AMS2 egress and negative/cleanup gates;
only afterward enable selection and publish the new immutable Android build.

## Production gateway projection and AMS2 prerequisites

3 November18:47UTC continuation; **SOURCE/PREPARATION CHECKPOINT, NOT MESH2 ACTIVATION**.
The installed gateway is the282-member accepted canonical/P1 source capsule. Building
generic main would omit its four-member speed policy, diagnostic instrumentation and
other accepted runtime integration. `scripts/slow_link_gateway_source.py` verifies the
entire accepted inventory and manifest, applies only the five reviewed patch members,
and imports fourteen tests plus the timestamp vector from exact142ee46. It rejects
modified/missing/extra/linked source members, changed patches and wider source changes.
The source output is private, exclusive and unbound; it contains no operational permit
or configuration. Existing startup, identity/admission, chat and profile-reader sources
remain byte-identical. Performance accounting now reports the adaptive send allowance;
the slow-consumer fixture fills its actual four-frame initial window, with unchanged
backpressure/close assertions and new growth/loss counter coverage.

- Accepted manifest SHA256: `27b54a9dd167c3b6af639bb03864f4d7d121c0e8b96c90eccb45a198c936f117`.
- Baseline rebuild equals installed SHA256: `f8ff517804c8cc425b172c821630274ce39ccfa9a3e79328db3e8a626f45ebef`.
- Two prototype candidate builds equal SHA256: `9d41f1dc1a716c0ecb6d85d0613b6cc35a173b7399fbb2b8d75d871c577a6bc1`.
- Same Go1.26.1/linux-amd64/CGO1/`fc_perf_diagnostic`/trimpath/buildvcs=false contract.
-20 Python projection/source checks PASS. Production-tag race selection across
  ReliableStream, Telemost, RoomBroker, FamilySession, bootstrap, bootstrap-broker and
  TCPForward:677 tests/subtests PASS,49 optional skips,0 failures.
- The first non-race production-tag selection passed all seven packages. A repeated
  JSON run reports675 PASS/49 skips and a slot-release failure (two test/subtest failures).
  Thirty repetitions on the unchanged baseline reproduce the same admission/batch slot
  timing problem:123 PASS/27 test/subtest failures. No TCPForward production source changed.
  Untagged diagnostic export/counter failures also reproduce on the baseline. The initial
  prototype invocation additionally lacked the timestamp fixture and the existing
  `FC_EXPECT_SEED_OBSERVABILITY=1` harness flag; both were supplied, not bypassed.
  These results are not an all-green historical suite or a waived release gate.

Fresh AMS2 identity/private key and a sequence1 secondary delegation are retained only
in local0700/0600 custody. Delegation uses the existing Family/CA/revision floor and
existing offline control-root signer; no primary/rehearsal identity was cloned and no
root key was transmitted. No secondary leaf/profile was installed or published yet.

AMS2 now has a separate dormant `/opt/apps/family_connect/friends-restricted-runtime/venv`:
Python3.12.3, rns1.5.1, cryptography46.0.7, pyserial3.5, cffi2.1.1, pycparser3.0.
Installation used a hash-checked offline wheel bundle, exact hashed requirements and
`pip check`; import/version probes PASS. Archive SHA256:
`689ee9136a754349991d0ab15bb37dc44e71f0f51e4f0961ab74e5d59e0c99e9`.
Private input/receipt staging is `/var/lib/fc-profile-control/mesh2-python-20261103/`.
AWG/TCP remain active with identical PIDs/restart counts;0 units created/started.
Primary MESH remains active with0 restarts. RU/AMS1 configs, renewal writers, provider
environment and gateway binaries were not changed. Private local evidence stays under
`state-client-build/mesh2-cutover-20261103/`, outside Git and CI.

Remaining: exact committed projection/readback, secondary canonical custody/profile and
forced snapshot/renewal route, common writer cutover and committed fleet checkpoint,
real READY/FamilyTLS/DNS/HTTPS/expected egress plus negative/cleanup/slow-link acceptance,
then selector activation and a new immutable Android version. Android111/catalog6,
Windows0.2.16/catalog12 and public Linux0.2.11 remain unchanged. No installer/tag changed.
Rollback at this checkpoint means retaining the old active writer/gateway and leaving
the new runtime dormant; do not remove or overwrite its retained custody. No production
cutover has occurred, so no service rollback is required. Later cutover must retain the
exact old executable/configuration and respect shared CRL/profile replay floors.

### Exact source and runtime compatibility —3 November19:02UTC

Projection source `eb0b5e68e49deed699983cf8ca3a6188a7bf82ca` pushed and remote main
verified. Two builds from its freshly materialized290-file source/vector inventory match
the prototype SHA256 `9d41f1dc1a716c0ecb6d85d0613b6cc35a173b7399fbb2b8d75d871c577a6bc1`.
Both new performance/adaptive-window regressions also PASS on that exact materialization.
The binary and exactfcb3116 renewal capsule are staged separately at
`/var/lib/fc-profile-control/mesh2-eb0b5e68e49d/` on AMS2. Source/package hashes, native
`--help` and Python renewal CLI checks PASS; no configuration, unit, key route or service
was installed/started. AWG/TCP PID/restart snapshots stayed identical.

Additional exact-candidate race qualification uses public111's unchanged128 production
carrier files at40e6c6c, its original VP8 subprocess helper and only the added reviewed
Family process harness. Candidate→candidate, candidate→111,111→candidate and111→111
all PASS mutually verified Family TLS with256KiB byte-exact UDP echo. Independently,
all four real Pion VP8/RTP/DTLS pairings PASS207 byte-exact exchanges per pair. Six
wall-clock paced cases PASS at256/64,512/128 and1000/250kbit with windows8/32; roughly
59/36/25s per case. Family selection12 tests/subtests and VP8 selection5 PASS,0 skips.
These are local process/network tests, not live provider/handset acceptance or a promise
of configured line-rate throughput. An overstrict initial harness comparison expected
the new VP8 test runner in111; readback verified the original111 helper instead. Runtime
production sources remained unchanged; no baseline APK was installed or modified.

The old snapshot launcher hard-coded Python3.14. Added explicit `python_minor: "3.12"`
for the Ubuntu24.04 secondary, while omission retains3.14 and its existing pin shape.
Unreviewed minors, diagnostic-version fallback, mismatched executable/venv/import minor,
changed dependency versions, unsafe permissions and reused primary-runtime pins reject.
The snapshot capsule alone now declares minimum3.12; maintenance's3.13 floor is unchanged.
No installed primary launcher/configuration or service was changed.

Validation:123 selected Python cases PASS (98 launcher,5 package,20 prior projection);
265 profile/canonical-source/snapshot/multi-gateway/expired-recovery cases PASS on real
Python3.12.3 in a network-disabled, read-only-source root container. Only synthetic state
and two hash-verified source-only archives entered that container. Its first collection
lacked the desktop parser source; that dependency was added, not skipped.5 updated
package cases additionally PASS there, including2 repeated snapshot cases. On actual
AMS2 the non-root `nobody` account passes isolated runtime/import/DAC inspection twice
with identical pins; default3.14 rejects the3.12 environment. This verifies runtime
access, not the still-unprovisioned final gateway account/profile/forced command.

Runtime compatibility source `ae2737f375fc48c4e026a87166a221e978fbbf1c` pushed and
remote main verified. The exact committed launcher matches the AMS2-qualified bytes.
Two exact-source unbound snapshot packages are identical (26 members,171092 bytes),
SHA256 `4373585a7a16499ee0cae95fca2beb644f799153345ab4677ae0f2a927e18657`, manifest
SHA256 `7ce941497a16a9b88d0a685c02d9ca6bb6cbc3ad5feb108718fb5e1f7fab6e16`.
The package is staged alongside the candidate gateway on AMS2, not installed as an
SSH command. Actual Python3.12 `-I -B` help and rejection of config/profile/write-action
overrides PASS. Final AMS2 readback: AWG/TCP active,0 restarts; restricted-bootstrap
`LoadState=not-found`, inactive. No provider token was transmitted in this continuation.

Public versions, primary runtime and controller remain unchanged. Next: provision the
canonical secondary profile/account/forced snapshot and renewal routes, establish the
single coordinated writer and fleet checkpoint, then live provider data-plane/rejection/
cleanup acceptance before selector or Android publication. Dormant artifacts and private
identity are retained for this work; rollback remains leaving them inactive, not deleting
custody or reverting shared replay floors. No release tag or signing catalog changed.

## Current result

**RESUMED: permanent MESH2 first, then Android update; SOURCE CHECKPOINT, NOT DEPLOYED.**
The latest owner request explicitly selects second-server activation followed by the update.
The intervening [connection-quality work](2026-11-03-mesh-slow-link.md) is source-checked
and must be included with the picker fix in the resulting release, not published as111.
No permanent second-node runtime or new APK has been deployed. Owner explicitly
asks to finish MESH2 using the separately supplied credential. This supersedes the
question-only interpretation in the earlier [picker report](2026-11-03-android-node-picker.md).
No claim that source publication enables MESH on an installed client.

## Expired-authority fleet recovery —3 November

Completed the source contract that remained open below. A schema4 offline request binds
both root-signed historical snapshots and successor delegations, their independent replay
floors, distinct identities, one shared CA/CRL, the last committed fleet checkpoint and
the exact current RU/AMS1/AMS2 state. One root-signed bundle covers the entire operation;
the root key stays offline. Pair-only signatures cannot authorize a fleet. Historical
validation does not make expired credentials live-valid: every candidate still passes
strict current-time validation. Existing grants, private keys and identity bindings remain.

The same controller performs thirteen acquire/quiesce/prepare/stage/promote steps across
three nodes. All commit receipts must match; both fresh gateway directories must reach
RU before its API resumes. Recovery requires explicit outage approval, a confirmed fleet
checkpoint and explicit roll-forward after interruption. A failed/unreachable secondary
cannot produce a successful partial commit. An unreachable node before acquisition is
not stopped or modified; already owned readers are fenced. Expired signed approval does
not become reusable on resume, and there is no automatic fallback to expired profiles.

Validation:60 recovery tests PASS, covering all nineteen controller interruption points,
seven secondary transport-failure points and reconnection, mismatched readback, malformed/
partial/swapped signatures, wrong operation, stale state/checkpoint, missing outage approval,
expired approval during partial publication, unchanged-secondary checkpoint fallback,
independent delegation sequences and retained client revocations/CRL entries. The real
runtime CLI request/apply/resume and offline signer FD entry point are included. The other
359 selected user-space/native/package checks PASS, including the accepted beta111 native
compatibility check. Private evidence: `state-client-build/mesh2-expired-recovery-20261103/`.
Network-disabled read-only root-container selection387 PASS, including151 fleet cases
repeated from user space;655 distinct selected cases PASS,0 skips. Canonical ownership,
DAC, source pinning and packaged profile construction checks use synthetic profiles and
a synthetic package containing these sources, never production private material.
Initial test-fixture failures are retained: pre-acquisition node ownership, a mocked-clock
identity selecting real nanoseconds, and a client certificate allowed to expire before its
revocation was materialized. Corrected the fixtures, not production security assertions.

Read-only RU audit still reports the existing active pair-only pinned source, active renewal
and directory timers and active candidate API with0 restarts. Dormant staging is recorded
below; active services/profiles, private publisher credential, Android version/signature/
catalog and invitation page remain unchanged.
Remaining gates: coordinated activation with fresh secondary configuration,
fresh permanent AMS2 runtime/custody, real traffic/rejection/cancel/slow-link/cleanup checks,
selector activation and new immutable Android>111/catalog>6. Preserve primary/ordinary
services and their private rollback evidence; never downgrade a serving fleet to a pair-only
writer. Source-only work requires no production rollback. Public versions remain
Android111/catalog6, Windows0.2.16/catalog12, Linux0.2.11; owner-local Linux0.2.12~l03.2.13.
This section supersedes the expired-recovery source gap below, not the live acceptance gate.

### Exact package and dormant production staging

Source `fcb311641457165405dc85fa070aaa4b1464e185` committed, pushed and remote main
verified. Two archives built independently from that exact commit are byte-identical:
archive SHA256 `85d47242fc178178aa3371a6ea849c63b59d3c38363ac9d4d2fbc0b6b5068fc9`,
module-set SHA256 `e9fd31754bdf50c95842a1644f86ddb328b839ec1e0c9454daf08d3e9d17f0cc`,
API SHA256 `1f1d2c8e56119c58a44fd3edf7cedf167f6761b7c81a6023e8b600a6049720e4`.
12 canonical root/profile/source checks PASS against the exact package; these repeat
existing cases, not12 additional distinct tests. Package has no production configuration
or operation permit. Private archive/receipts remain in the evidence directory above.

The archive is staged separately on RU and AMS1 at
`/var/lib/fc-profile-control/mesh2-fcb3116414571654/`. Every archive member is regular,
path-bounded and SHA-verified before extraction; staged directories/files are0700/0600.
Separate `node-candidate.json` files preserve existing live paths, custody, admission and
units while pinning the new module/API bytes. Exact-package node construction/inspection
PASS against both real canonical installations. No live profile or active config is replaced.
The local staging helper initially failed syntax checking before contacting either host;
its quoting was corrected before staging, with no partial first upload.

RU's separate `controller-readonly.json` is deliberately still schema1 and points at the
existing forced AMS1 route/source. Evaluation with the staged controller returns **NOOP**,
no due items/alerts, files_changed0, remote_writes0, restarts0. This proves read-only
compatibility with the active pair, not a three-node cutover or scheduled-cycle acceptance.
Active node/controller configuration hashes remain unchanged; renewal/directory timers
and candidate API remain active, API restarts0. No AMS2 files or services are touched.

Staging rollback is simply to leave these unreferenced candidates unused; all active
launchers, forced routes, timers and their prior source pins remain in place. Preserve
the candidate receipts and original private configuration for the later coordinated
cutover. Do not point a serving fleet back at the pair writer. Permanent AMS2 activation,
real data-plane acceptance and Android publication remain unfinished.

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

**Acceptance gap at this checkpoint (source contract now completed above):** recovery when the fleet's root-signed authority has
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
Existing unrelated working-tree changes remain untouched. That checkpoint's next work was
whole-fleet expired-authority recovery, now implemented above; it did not select an unrelated
queued task or immediate APK publication. Production activation and Android update remain unfinished.

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
This earlier source slice needed no runtime rollback because it was not installed. A later rollout
must retain the previous exact API package, additive migration receipt and renewal
configuration; do not restore product DB or roll published catalogs backwards.

## Permanent fleet activation and live data-plane

**3 November20:27UTC — active runtime and committed writer, acceptance still incomplete.**
Permanent AMS2 uses the distinct canonical identity, isolated Python3.12 runtime and
production-preserving slow-link gateway documented above. Its root-only `provider.env`
now holds the independently supplied retained publisher token. Original local material
was labelled `DISPOSABLE_FLEET_REHEARSAL` and remains unchanged; permanent use follows
the owner's subsequent explicit request to use that retained token and finish MESH2,
not reuse of a retired rehearsal permit, gateway identity or certificate. No primary
provider environment was copied. Provider conference/seed creation succeeded.

The existing RU writer was quiesced before switching to exactfcb3116 schema2 fleet
configuration. AMS1's fixed helper now uses the same reviewed renewal source with its
existing canonical profile/locator. Its old launcher, gateway executable and identity
remain unchanged. AMS2 has an independent pinned forced route. RU carries the secondary
signed delegation and a genuine directory fetched over that route. The new renewal and
directory unit drop-ins select one common writer and two explicitly bound directory
routes; both timers were restored active. The disabled legacy sync timer stays disabled.

`mesh2-first-fleet-20261103` reached **COMMITTED**, `commit_decided=true`, no first cause,
after acquiring/quiescing RU, NL and NL2. It renewed the short initial secondary leaf;
the common CRL remained floor27259 because it was not due. Follow-up fleet evaluation
was NOOP,0 writes/restarts, with roughly9123s headroom. HTTP and primary MESH underwent
one controlled stop/start for that transaction; ordinary AWG/TCP were not restarted.
The secondary bootstrap is currently active but still disabled for boot. No automatic
pair rollback is safe after a committed fleet checkpoint: preserve common authority,
CRL/profile floors, both identities and committed transaction state.

Actual private synthetic device-role probe, issued by the existing RU issuer in place
without product registration/grant/assignment writes, used the real authenticated seed
directory and then an unavailable ordinary control address. Provider VP8 bootstrap,
Family admission and bootstrap-close-before-dedicated all succeeded. Dedicated MESH
passed4 HTTPS streams and3 DNS probes. A second positive probe after the explicitly
recorded cleanup restart also verified Cloudflare's observed public egress exactly
equals the second Amsterdam node. Only the equality boolean is in the public receipt;
raw trace, ephemeral rooms, identity/profile and client key stay in ignored private state.
Wrong-gateway seed refresh rejects without creating a cache. Forced SSH command override,
sudo argument override and publisher-write-to-canonical-profile probes also reject.

**Failures and remaining cleanup gate:** an immediate follow-up after the first successful
probe failed `bootstrap_protocol_rejected`; gateway evidence is challenge-stage
`context_deadline` while the same synthetic identity still owned its previous lease.
The CLI bootstrap path has no direct room-cancel call; however production closure also
requires investigation, so this is not declared a harness-only cause or repaired behavior.
Normal broker lease lifetime is10min; ownership must not be bypassed/preempted to make
the test green. One secondary-only restart explicitly cleared the synthetic session
after writer quiescence, then timers were restored. Its first preflight found an active
directory oneshot and stopped; readback confirmed it finished before the corrected retry.
Two direct-broker probe attempts returned `control_rejected` with no created lease:
port18444 serves the authenticated seed directory, not the direct room-control API.
The subsequent correct seed-fallback egress probe passed. Expiry/resource cleanup and
normal reconnect still need independent acceptance, without service restarts.

Two installation checks stopped safely: the strict atomic helper refused `provider.env`
under the intentional01770 publisher directory, before writing it; reconciled absence
and installed only a root0600 file with O_EXCL/fsync. AMS1 post-write validation imported
a snapshot module absent from the renewal API capsule; byte-exact helper/config readback,
unchanged profile and real forced RPC/fleet transaction subsequently verified the change.
Neither failure was erased or retried blindly.

Backend candidate is **built, not installed**: SHA256
`e2ed4ca6b41e134516a7fa33210cc71e80bc62c09efc370d56ecd4c6d4e6bfd9`,
two reproducible builds, identical zip membership; only `control/friends/restricted.py`
and `control/friends/readiness_receipts.py` differ from livefce2340 and match exacte7d2739.
Every other member remains byte-identical, including paid/ordinary dispatch. CLI check
passes. First focused run:100 PASS,3 optional skips,1 failure in the time-sensitive
owner-product receipt test; it is retained for triage, not called a green suite.
Unmodified repeat:101 PASS,3 optional skips. The fixture timestamps its receipt before
constructing the observer; crossing a wall-clock second can violate its opened-at guard.
No production time guard was relaxed and no unrelated runtime patch was applied.
Additive `gateway_binding` migration, guarded activation and listener/product readiness
remain pending. Do not restore a live product database as a code rollback.

Android still111/catalog6; no new APK, version/tag/catalog or MESH picker activation.
Public Windows0.2.16/catalog12 and Linux0.2.11 remain unchanged. Remaining selected work:
cleanup/reconnect gate; backend migration/readiness acceptance; secondary boot enablement;
Android selector/new-version CI including API27/API35, artifact verification, offline
signing, immutable publication and public download/catalog readback. Operational recovery
must keep the common writer or use its explicit fleet recovery; do not reinstate the old
two-node writer against the committed three-node state. All private receipts are under
`state-client-build/mesh2-cutover-20261103/` or root-only server staging, outside Git/CI.

## Bounded RESET write source checkpoint

3 November21:28UTC. After the successful20:24 egress probe, AMS2 emitted
`EXPIRED/lifetime_expired` and `dedicated_resources_closed` around20:34 without
another restart. This proves eventual cleanup, not immediate reconnect. RU renewal
and directory timers were read back active/waiting, last oneshots successful.
Intermittent SSH banner/post-authentication timeouts remain recorded; larger inspection
commands were not assumed to have completed. No mutation was blindly replayed.

`reliablestream.Close` sent its final RESET through an asynchronous carrier queue and
immediately closed the carrier. A deterministic queued endpoint fails before the fix
in both legacy-data and completed-data modes: the RESET has no completion registration.
The correction observes the actual local write before closing the endpoint, using the
existing100ms deadline. A stalled writer remains bounded and cannot start an expired
RESET. This is local-write confirmation, not a remote acknowledgement or guaranteed
delivery through packet loss. No wire, retry, lease, admission or ownership change.

Validation:20 race repetitions of the new close cases PASS; complete race packages
`reliablestream`, `localwrite`, `familysession`, `roombroker` PASS. The first combined
command also named nonexistent `./bootstrapbroker` and exited1; corrected
`./cmd/bootstrap-broker` PASS. Selected close/queue/cancellation/cleanup cases in
`bootstrap` and `telemost` PASS. An earlier private Family-close experiment first failed
on a local TLS close-notify error; after asserting actual peer closure, both unchanged
and reordered variants passed3 race repetitions. That experiment does not justify
changing Family TLS close order and no such change is included.

Actual-provider qualification remains FAIL/INCOMPLETE, all attempts retained privately:

- 20:59:56 candidate start: Family authentication and descriptor received, then no
  `bootstrap_closed_before_dedicated`; returned `descriptor_expired` after136.545s.
  Gateway failed its unclaimed dedicated Family session. Cleanup-delay cause still open.
- 21:06 candidate: bootstrap protocol rejection before descriptor; no data-plane probe.
- 21:12:51 unchanged-stream baseline with the same private watchdog: bootstrap closed,
  dedicated carrier connected, then Family authentication failed after63.059s overall.
  Server trace starts Family TLS21:13:18.492 and closes21:13:48.495, its30s deadline;
  carrier-established trace is later21:13:32.798. This is evidence of a consumed
  pre-peer handshake budget, not proof of a complete fix or certificate diagnosis.
- 21:19:22 candidate: seed connect failed after7.329s; no descriptor/Family/data plane.

Watchdog arms only after descriptor delivery; neither later attempt reproduced that
delay, so no goroutine dump was produced. The queued-RESET correction is not installed
and does not close these live gates. Synthetic leaf issuance refreshed only the same
private probe identity; product registration/grants/assignments were verified unchanged.
The30min follow-up leaf expires21:28:02UTC and must not be reused after expiry.

Backend readiness overlay remains built-only (`e2ed4ca6…bfd9`), no DB migration or HTTP
activation. Its focused suite first had one timestamp-sensitive existing UI-recorder
failure, then101 PASS/3 optional skips unchanged; that failure is not hidden. Newer
source/overlay does not mean deployed. Public Android111/catalog6 HTTPS bytes match
the repository catalog (`ca3e6c63…1df`); no new version, tag, signing or public install.
AMS2 remains active/boot-disabled on `9d41f1dc…6bc1`; AMS1 and ordinary AWG/TCP remain
unchanged. Source rollback is a normal revert, not replacement of immutable artifacts.
Operational rollback retains the committed common fleet writer and both canonical
identities; use explicit fleet recovery, never restore the old pair writer or product DB.
Remaining gates: repeat actual-provider connect/cleanup without restart, backend
readiness/migration, secondary boot enablement, exact new-version Android CI/API27/API35,
offline signing and immutable catalog/download verification. No queued successor starts.

## Idle RTP gap source correction

3 November21:53UTC. RESET correction47b76f494b66a4f7508bb3ae08d8ffd1c7b5d137
was pushed and its remote main SHA verified. Five additional focused race repetitions
PASS. A fresh30min leaf for the same synthetic identity expires21:58:05UTC; no new
product registration, grants or assignments. Private probes force normal control
unavailable and use the genuine secondary directory/provider, not a direct-room bypass.

- 21:29:16 probe: Family TLS,4 HTTPS/3 DNS and AMS2 egress PASS,46.819s overall.
- 21:30:37 repeat: FAIL after120.018s, server confirms challenge/context_deadline;
  no new dedicated descriptor. No restart or ownership takeover was used.
- 21:39:27 server emits FAILED/authorization_changed then dedicated_resources_closed
  for the retained first session. This was not immediate peer-close or a demonstrated
  lifetime-expired event. PID554442/NRestarts0 unchanged across these observations.
- 21:39:45 probe: Family TLS,4 HTTPS/3 DNS and AMS2 egress PASS,43.307s overall.
  Private instrumentation confirms both final RESET local writes returned success.
  It does not confirm receipt at the server. No post-descriptor watchdog dump occurred.

A private fault test drops RESET after successful local completion and reproduces
remote-session retention in5 race repetitions. This proves the local-write guarantee
is insufficient under loss, not where the live RESET was lost. Runtime sender/receiver
evidence is still required; previous cleanup-delay and handshake failures remain open.

Receiver review found a separate concrete defect: `reorderBuffer` checked its750ms
gap timeout only on the next RTP push. A complete final carrier frame behind a missing
packet could remain buffered indefinitely if the sender stopped. Two production-loop
tests (normal sequence and wrap-around), with only the track-reader parameter extracted
to an interface, fail on unchanged behavior at2s. The correction arms Pion's actual RTP
read deadline for the current gap and releases available packets when it expires,
without waiting for another network packet. A subsequent gap gets its own full750ms;
empty/recovered buffers clear the read deadline. Existing sequence/window bounds,
frame validation, Family authentication, lease ownership and policy are unchanged.

Acceptance:5 repeated race runs of new idle-gap and existing RTP-reorder cases PASS;
3 repeated real local Pion RTP/DTLS tests with deliberately omitted sequence101 and
no packet after102 PASS. Full `go test -race -p=1 ./telemost ./bootstrap` PASS (35.759s/
3.531s); the idle-gap cases also PASS with `fc_perf_diagnostic`. Local Pion is not
real-provider or phone acceptance. The production capsule
projection helper/patch and deployed gateway do not yet contain either new transport
correction; a generic-main gateway must not replace the accepted canonical/P1 runtime.

CI41721843205/source47b76f4: JVM control, restricted carrier race and readiness contracts
PASS; native Android support-library build PASS. At observation, Android runtime/release
steps were unfinished; Windows primary job PASS. Linux fails the real GTK poll/Disconnect
gate:48 PASS/2 FAIL in `test_old_connect_completion_cannot_replace_new_disconnect`
(AWG/TCP), expecting country alias `nl` while actual selected node is `nl-amsterdam-1`.
No Linux code/test/workflow is changed or gate weakened in this source slice. Subsequent
source pushes may supersede an in-flight run; neither this run nor local tests count as
accepted exact-version release CI. No111 binary/catalog replacement or new tag.

Final small RU readback: renewal/directory timers active/waiting, oneshots inactive with
Result=success/ExecMainStatus0. A separate coordinator-file read timed out; retain the
prior confirmed COMMITTED transaction, do not invent latest transaction evidence.
AMS2 remains active/boot-disabled, backend overlay built-only, public versions unchanged.
Final secondary readback confirms the last synthetic session emits
FAILED/authorization_changed21:49:58.581 followed by dedicated_resources_closed
21:49:58.591. This is eventual remote cleanup, not immediate disconnect acceptance.
MESH PID554442, AWG6206 and TCP6146 remain active with0 restarts; only MESH is
boot-disabled. Source36ce71365e3393419073430eebf6824baed140be is pushed and remote main
SHA verified. Raw profiles, journals, watchdogs and source experiments remain private.
Rollback stays a normal source revert plus explicit common-fleet recovery for
runtime changes; no product DB restore, old pair writer or identity cloning. Next is
exact production projection/build/live cleanup acceptance, then backend/selector/Android
release gates already listed above, not a different queued task.


## Close and idle production projection

3 November continuation, source-only checkpoint. The production projection now includes
47b76f4 bounded final RESET local-write completion and36ce713 idle RTP reader wakeup.
Review found the accepted capsule retains a100ms gap timeout and drop-on-window-overflow,
whereas generic main uses750ms and a different window drain policy. This narrow rollout
preserves the production100ms budget/window policy and its packet-pacing observation;
it does not silently import the other main-branch differences. Earlier750ms source
qualification describes main, not the previously deployed capsule. Eight patch members
are allowed in total; all other accepted source is inventory/hash protected. Two new
test files come from their exact source commits alongside the fourteen142ee46 inputs.

17 projection guards PASS; exact accepted inventory projection PASS (291 carrier files
plus one timestamp vector). The first hand-assembled single-context patch was rejected
before output; regenerated full-context patch applies cleanly without relaxed checks.
Production-tag race packages reliablestream/localwrite/telemost/bootstrap/familysession/
roombroker PASS. These are prototype-source checks, not exact committed binary or live
acceptance. Private logs/source remain under the existing mesh2-cutover state directory.
No production file, writer, profile, selector, version, installer or catalog changed.

Remaining: exact committed deterministic builds, public111 mixed-version Family/VP8
and paced-link checks; controlled secondary-only upgrade preserving canonical publisher
binding and common-fleet coordination; repeated actual-provider sessions and timely
remote cleanup without restart. RESET is still best-effort remote delivery. Backend
migration/readiness, boot enablement, selector and new immutable Android follow only
after acceptance. Rollback before activation is simply leaving9d41f1dc installed; a
later runtime rollback must restore its matching locator/config binding, not credentials,
replay floors, product databases or the retired pair writer. Linux CI's two selector
expectation failures remain open; no mandatory release gate is waived.

### Linux mandatory GUI gate repair

The two hosted failures reproduce unchanged in an isolated GTK/Xvfb/D-Bus container:
the test still expects country alias `nl`, although AWG/TCP now select explicit nodes.
The corrected test covers both Amsterdam1/2 for both transports, retains every stale
completion/owner/operation-generation/up-down assertion, and checks the exact selected
node passed to connect. Production UI code is unchanged. Full poll/Disconnect plus
gateway-selector GUI files:54 PASS (existing315 deprecation warnings),0 skips. Initial
container extraction with capabilities dropped rejected archive ownership restoration;
retry uses `--no-same-owner`, without weakening container isolation. Hosted CI is still
required; this is not a new Linux installation or a waived release gate.


## Close/idle secondary runtime upgrade

Projectiona4b64966cde3006c68ec9d9071dcc457a6aebf1f and GUI correction70f63b84d507db2d16cd2354db8f5a654e611745
are pushed and remote-SHA verified. Exact292-file materialization built twice (second
with forced rebuild) to SHA256 `2fc165776a7bffa5a2f15fdd0bf36cb15caaf69d33070e4cb34a7685e2386558`.
Gateway-command production-tag race PASS in addition to the six carrier packages.
Mixed public111/current Family TLS and actual local Pion VP8 four pairings each PASS;
six asymmetric paced256/64,512/128,1000/250kbit window8/32 cases PASS with exercised
DATA loss/retransmission and byte-exact262144-byte transfer. Local Pion idle deadline
also PASS. This is compatibility/lab acceptance, not a handset/provider claim.

Direct RU SSH repeatedly timed out, including banner exchange. Strictly pinned access
through the authorized primary Amsterdam host succeeded; no host-key/auth relaxation.
A private short-path multiplexed connection avoids repeated setup. A first long control
socket path was rejected locally before establishing the master. Dormant secondary
upload initially used an unsupported `dd` flag; readback confirmed no file, then an
exclusive guarded upload succeeded and remote SHA matched. No active binary changed
in either failed staging attempt.

22:17:32UTC common renewal/directory timers paused with an8-minute automatic resume
safety timer. Confirmed COMMITTED coordinator, no active owner and CRL headroom10122s.
22:17:37 secondary upgrade PASS: new immutable tools path
`/usr/local/lib/fc-profile-tools/mesh2-a4b64966cde3/gateway`; existing executable retained.
Canonical locator publisher contract and its snapshot/node configuration bindings are
updated consistently. New locator SHA256
`34ef7bc49ea72476823f6ef1c8eb1516447c868be73ce1d451590aefd24b1dc8`.
Fresh provider seed, service-account CLI, unit validation and actual `/proc` executable
SHA PASS. MESH PID582708/NRestarts0, active and still boot-disabled. AWG6206/TCP6146
and their restart counts, private profile bytes and original gateway binary unchanged.
No primary MESH, normal VPN, HTTP backend, grant/assignment or product-state change.

22:18:58UTC common timers resumed and safety timer stopped. Exact RU inspection equals
pre-upgrade state. Three-node coordinator evaluate returns NOOP, due[], headroom leaf6127s/
CRL10038s, files_changed0/remote_writes0/restarts0. Existing LEAF_T_MINUS_120M advisory
retained; remote alert delivery UNAVAILABLE. New30-minute leaf for the same synthetic
probe identity expires22:47:11; no product registration/grant/assignment change.
Actual-provider repeated-connect and remote cleanup acceptance is now running, not PASS.

Rollback is secondary-only restoration of the retained previous unit, locator and
snapshot/node configuration bytes/metadata plus old9d41f1dc executable, under a new
coordinated writer window. Backups/receipts live in root-only
`/var/lib/fc-profile-control/mesh2-close-idle-a4b64966cde3`. Do not restore profiles,
credentials, databases, floors or the retired pair writer. The upgrade script contains
bounded failure rollback; it was not needed during the successful activation.

Client builds41728661709/70f63b8: hosted Linux job126240977565 PASS; Windows in progress,
Android skipped by change scope, not accepted for a new Android release. Separate Linux
internal candidate41728661787 fails its accepted-source package gate; no overall CI
or Linux candidate PASS claim. Public Android111/catalog6, Windows0.2.16/catalog12 and
Linux0.2.11 remain unchanged. Backend overlay remains built-only; selection/publication
is still gated on repeated actual-provider acceptance and exact-version release CI.


## Bounded RESET repeat source

Installed2fc16577 alone did not solve remote cleanup.22:19:32 probe passed Family TLS/
4 HTTPS/3 DNS in34.727s but lacked its egress check: Go overlay absolute paths used the
physical checkout while Go used its logical PWD. No egress acceptance is claimed for
that run. Building with physical PWD activates the two probe-only CLI overlays and
verifies the marker in the executable.22:21:41 exact-carrier repeat then failed at120.016s;
server challenge/context_deadline confirms retained ownership. First resources closed
22:29:40 after authorization_changed, not timely peer release.

A private diagnostic client added only500ms post-write grace.22:29:41 Family/4 HTTPS/
3 DNS/expected AMS2 egress PASS44.613s; immediate repeat22:30:26 fails120.015s. It was
not shipped. Its resources closed22:36:13 during scheduled common renewal, not peer
cleanup. Coordinator's scheduled22:35:48 operation completed COMMITTED with no first
cause; secondary restarted22:36:40, new seed22:36:42, PID591182/NRestarts0. AWG6206/
TCP6146 unchanged. The retry experiment's first read-only seed refresh overlapped that
maintenance and returned control_unavailable; no traffic run occurred. A new normal
30-minute leaf for the same synthetic identity expires23:09:48, with no registry/grant
mutation, and a fresh genuine seed was fetched after confirmed writer completion.

A second private prototype sends five identical RESETs spaced100ms apart, awaiting
local-write completion for each, before carrier teardown. Three consecutive runs:
22:40:31/53.345s,22:41:24/39.314s,22:42:03/39.290s all PASS Family TLS,4 HTTPS/3 DNS and
Cloudflare-verified AMS2 egress. Each records ten successful local RESET writes across
bootstrap/dedicated closes. Server PID591182 is unchanged across all three; dedicated
resources close22:41:24.312,22:42:03.641,22:42:42.893 before the next connect. Existing
terminal mapping emits FAILED/gateway_session_failed on peer reset; do not relabel this
as a graceful CLOSED event. No takeover/restart/identity replacement was used between
these runs. Exact SFU packet-loss location is not proven by these observations.

Production source converts that experiment to a hard500ms total budget, at most five
identical RESETs,100ms local-write cap and100ms spacing. A failed/stalled local write
stops retries, avoiding extra queued work. The old100ms total bound changes explicitly;
wire format, epochs, DATA retries/windows, admission and lease ownership do not change.
Close remains abort, NOT reliable FIN/drain or proof of remote delivery under total
loss. New first-reset/first-four-reset loss cases fail on baseline; total-loss test also
fails its attempt-count assertion. After correction, five focused race repetitions PASS
and seven full package race regressions PASS: reliable/localwrite/Family/room broker/
bootstrap/Telemost/gateway command. All-loss coverage retains bounded local cleanup
without inventing remote cleanup; existing stalled-writer test forbids retry buildup.

These successful provider runs use the private prototype, not the newly bounded exact
shipping implementation. Next is committed-source projection/compatibility and exact
live acceptance; neither new Android nor new server retry code is installed yet.
Installed gateway remains2fc16577 with its matching canonical binding. Rollback boundary
is unchanged. Public Android catalog HTTPS readback is byte-identicalca3e6c63…/sequence6.
Client builds41728661709/70f63b8 completed SUCCESS for scoped Linux/Windows/compatibility;
Android and release skipped, not new-Android acceptance. Separate Linux candidate
packaging failure remains recorded. Private prototypes/logs/profiles remain outside Git.

### Bounded repeat projection checkpoint

Sourcebd67843f980ede602cf3aeeefa5f31e23ac6711a is pushed/remote-verified. First push failed
on temporary GitHub DNS resolution; ordinary non-force retry succeeded, with no history
rewrite. Projection now includes the bounded repeat while preserving the same eight
reviewed source members, accepted pacing instrumentation and100ms RTP gap policy. Two
close test inputs pinbd67843 and idle-RTP coverage remains pinned36ce713.17 projection
guards and exact accepted-inventory patching PASS. During editing, the patch hash guard
correctly rejected the intermediate patch before its helper pin was updated; no output
or runtime change resulted. Exact committed builds/compatibility and live acceptance of
this bounded implementation remain next; the installed gateway is still2fc16577.

## Exact bounded RESET runtime and reconnect acceptance

3 November23:05UTC (4 November locally). Exact projection source
`d2c2a45b9f898e51416bef1e52d2f4f474a76f9b` is pushed and remote main verified.
Its293-file materialization preserves the accepted eight-member boundary. Two clean
gateway builds, including a forced rebuild, match SHA256
`566cbc96621c348e188aa50ffa54d6cf7bfce6274f8a214d3b0c227e743bb219`.
Seven production-tag race packages PASS: reliable15.748s, localwrite1.023s,
Family26.029s, room broker1.454s, bootstrap3.570s, Telemost56.706s and command2.279s.
All four public111/current Family pairings and four actual Pion VP8 pairings PASS;
all six256/64,512/128,1000/250kbit paced cases (windows8/32) and idle-RTP deadline PASS.
The probe uses that exact carrier plus only two private CLI egress-observation overlays,
built from physical PWD with the marker checked; probe SHA256
`7ea4ad28b1180dbf1d4ff14e054295b8af41230161bf1e355b183ac2b2e88391`.

Initial SSH multiplex socket disappeared before the pause command. Readback confirmed
no new window or safety timer, both common timers active: no mutation was inferred.
A foreground pinned multiplex session restored transport. The22:59:35 coordinated
window stopped only the common timers with an8-minute automatic-resume safeguard.
The secondary activation's immediate `/proc/PID/exe` hash assertion failed after start;
the guarded handler restored the previous unit/locator/config, retained both immutable
binaries, and restarted2fc16577. Readback confirms previous hash/PID601757 and an explicit
rollback receipt. This failed attempt is not counted as acceptance. RU inspection stayed
unchanged; controller NOOP and timer resume22:59:49 completed. No private profile or
ordinary service changed. The exact transient executable was not captured, so its
identity/cause is not claimed as proven.

A fresh window23:01:29 uses bounded startup observation rather than asserting the
executable hash immediately. It still requires the exact candidate executable and a
fresh valid seed within100s; no hash or canonical guard is bypassed. Secondary upgrade
completes23:01:35 at `/usr/local/lib/fc-profile-tools/mesh2-d2c2a45b9f89/gateway`,
PID602868/NRestarts0. Locator SHA256
`de1220595d7b3e673d65871830f5c6f13df7bacfbb96a5fd42509ae5255cd12f` matches snapshot and
node-fleet bindings. Profile bytes unchanged; AWG6206/TCP6146 remain active/enabled with
zero restarts. MESH remains active/boot-disabled pending the remaining product gate.
RU before/after inspection matches, three-node evaluation returns NOOP/due[]/alerts[],
leaf and CRL7470s with files_changed0/remote_writes0/restarts0. Both common timers resume
23:01:46 and the safety timer is stopped. The retired pair writer stays retired.

Three consecutive real-provider probes of the bounded exact implementation, with normal
control intentionally unavailable after a genuine seed refresh, PASS:

| Start UTC | Seconds | Family | HTTPS | DNS | Expected AMS2 egress | Resources closed UTC |
| --- | ---: | --- | ---: | ---: | --- | --- |
|23:02:09.948|42.200|PASS|4/4|3/3|PASS|23:02:51.791|
|23:02:52.148|43.595|PASS|4/4|3/3|PASS|23:03:35.390|
|23:03:35.743|37.986|PASS|4/4|3/3|PASS|23:04:13.391|

Gateway journal has exactly three bootstrap and dedicated Family admissions, three
ACTIVE sessions, three dedicated-resource closes, zero bootstrap rejections and only
PID602868 throughout. No restart, ownership preemption or identity replacement between
these attempts. Each close precedes the next attempt. Existing terminal mapping emits
FAILED/gateway_session_failed for peer RESET; this is not relabelled graceful CLOSED.
All forwards/probes terminate. Synthetic identity, profile and raw provider logs remain
private. This is exact CLI/provider reconnect acceptance, not an Android handset/product
test and not a guarantee under total RESET loss or prolonged low-bandwidth field use.

Rollback for this secondary version requires a coordinated common-writer window and
the root-only `mesh2-reset-repeat-d2c2a45b9f89-r2` backup/receipt set, restoring matching
2fc16577 unit, locator, snapshot and node bindings, then exact executable/fresh-seed
checks and common-writer resume. Do not restore private profiles, DB/CRL history or
the retired pair writer. Earlier failed-window backups remain separate evidence.

Backend preflight confirms live HTTP stillfce2340, active/PID480966/NRestarts0, secondary
issuer/directory present and additive `gateway_binding` column still absent. The
e2ed4ca6 overlay remains built-only; no DB or HTTP activation yet. Public Android111/
catalog6, Windows0.2.16/catalog12, Linux0.2.11 and owner Linux0.2.12~l03.2.13 unchanged.
CI41734068017/sourcebd67843: Linux/Windows/compatibility PASS; Android build/JVM/lint/
carrier contracts PASS but emulator/release stages still running at this checkpoint.
No new-version CI, signing, public artifact or selector acceptance is claimed. Next is
backend migration/readiness, client routing/storage live acceptance and qualified boot/
selector activation, then immutable Android delivery under the existing release gates.

4 November follow-up: node-scoped HTTP and additive migration are installed; Android112
is a separate candidate, not a public release. See the
[current rollout, qualification and remaining gates](2026-11-04-mesh2-android112.md).
