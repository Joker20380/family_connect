# Unified MESH runtime and Android116 — 4 November 2026

## Selected scope

Owner explicitly selects stability work and the same MESH implementation on both
Netherlands servers. This supersedes the earlier instruction to preserve distinct
transport implementations. It does **not** merge node identities, credentials,
canonical paths, grants, seeds or egress configuration. No neighbouring service,
unrelated queued task or public client rollout is selected.

Target: one reproducibly built canonical gateway executable, identical SHA256 on
NL1 and NL2, with adaptive reliable recovery, transient-ICE tolerance, bounded RTP
gap expiry, repeated RESET cleanup and the new idle ACK deadline. Preserve current
wire/authentication/canonical-reader contracts and the common renewal writer.

## Initial readback and source reconciliation

Read-only20:05UTC inventory confirms:

| Node | Running binary SHA256 | PID / restarts |
| --- | --- | --- |
| NL1 |`8769eadfa88850c41fc0d90a9dcc4749f2e949de36dfd95bb606c32c404b3c30`|1143052 /0|
| NL2 |`5bcb32ea138325fbe3c788e2500d5054073ffc8df589e1cd1e83ed31c0946638`|1115161 /0|

Both MESH services are active and boot-disabled; ordinary AWG/TCP services and RU
HTTP remain active, common RU renewal/directory timers active. No mutation yet.

Exact284/294-member source inventories differ in seven production files:
ReliableStream engine/performance/stream and Telemost RTP/session/signaling/trace.
NL1 still has fixed retry timing, terminal handling of transient ICE disconnect,
single-shot RESET and arrival-driven RTP-gap expiry. NL2 contains the already
qualified slow-link/repeated-RESET corrections. The canonical identity, profile
reader and broker policy sources match. This proves implementation drift, **not
an observed incompatible wire format or the full cause of the physical outage**.

`scripts/unified_mesh_gateway_source.py` pins both complete manifests, rejects
unreviewed production differences or missing predecessor members, selects the
qualified secondary implementation as the common base, and applies only the
reviewed `2bc4258` idle-ACK production delta. It retains canonical/performance
code rather than replacing the capsule with generic main. Every output gets one
manifest with both predecessor hashes and committed regression inputs. No live
configuration or deployment permit is embedded. Private source capsules remain
outside Git; the narrow patch and materializer are tracked.

Projection and predecessor safety checks:59 PASS across the new common-source
helper and existing cleanup/slow-link helpers. Real capsule materialization,
binary reproduction and runtime acceptance are pending at this checkpoint.

Combined source/release contracts:118 PASS,1 unrelated Windows case deselected.
Initial release check retained58 PASS/1 FAIL because the Android106 preservation
guard lacked the reviewed2bc4258 idle-reason hashes. Only DiagnosticRing,
RestrictedTrace and RestrictedRecovery overrides were updated after checking the
exact three-line production delta; unchanged UI and other handler pins remain.
Both real predecessor inventories and the narrow production projection also
validate locally; committed materialization/builds follow the source checkpoint.

## Exact common build and qualification

Source checkpoint `a597d2ad203ccbb894df07c7fafdf33a71d40b12` is pushed and
remote-SHA verified. The297-member common capsule has manifest SHA256
`c0007c082072e2968598f62ff88f4b395d7c0a7ccc9fb1d5fdaed261255f8545`.
Go1.26.1/CGO1, `fc_perf_diagnostic`, `-trimpath -buildvcs=false` reproduces the
accepted secondary `5bcb32ea` exactly. Two common builds are byte-identical:
`70e6c0fc1b920ad308e24667be94f674c34979dab6aa518e1a8194fff7c131b6`.

Production-tag selections, with fresh disposable Family credentials where needed:

| Gate | PASS test/subtest events | Skips |
| --- | ---: | ---: |
| Core ReliableStream/media/Family/broker/trace race |428|28|
| Bootstrap race,3 repetitions excluding two inherited assertions |297|3|
| Idle/ACK/loss/transient/RESET/cleanup race,10 repetitions |710|10|
| Negative auth/ownership/deadline and real Python seed serialization,5 repetitions |75|0|
| Mixed115 Family TLS and six paced links |12|0|
| Mixed115 real Pion DTLS/RTP,3 repetitions |15|0|
| Public113 native mixed Family/Pion,3 repetitions |27|0|
| Candidate116 native mixed Family/Pion,3 repetitions |27|0|
| Isolated root canonical-reader boundary,3 repetitions |75|0|

Paced links exercise256/512/1000kbit/s,8/32-frame windows, asymmetric reverse rate,
injected DATA loss and byte-exact262144-byte transfers in each direction. Mixed
tests use exact published113 sourced2882cd, installed115 source86c5f9d and116
sourcea597d2a, both endpoint directions. These are local-process protocol tests,
not Android/provider acceptance. Canonical root tests run against synthetic
temporary profiles on NL2, verify read/no-write boundaries, and remove the isolated
harness; no production profile or service is altered by that check.

Retained non-green evidence: first untagged suite has421 PASS/28 skips and two
performance-export failures because the diagnostic build tag was omitted. The
correct production-tag selection passes. The original ProductIdentity diagnostic
assertions fail on both unchanged secondary and candidate (seven failure events
each); negative authorization boundaries themselves pass. The inherited busy
test's direct error equality remains timing-sensitive: candidate4/5 failures
with the same wrapped `bootstrap_protocol_rejected` reason, predecessor first5/5
passes; repeated predecessor evidence is retained separately. These tests are not
silently relabelled PASS. No admission/error/retry policy is relaxed.
Local root/live/provider/subprocess skips are not physical acceptance; separate
root and paced/publication selections exercise their otherwise skipped gates.

The identical binary is staged on both nodes; read-only preflight confirms exact
old executable, locator/config pins, service-user execution and >10000s credential
headroom. Services still run their old executables at this qualification checkpoint.
Guarded common-writer pause, NL2 canary then NL1 activation and final readback follow.
Android Client builds41905046530 is in progress on exacta597d2a. Readiness contract
41905046756 passes; separate phase041905046579 and Linux control41905046527 fail.
No whole-CI or Android release PASS is claimed.

## Android version boundary

Candidate source becomes `0.1.18-beta116`/code116, retaining API27 compatibility,
the115 DNS/cleanup fixes and adding idle ACK expiry with guarded Android recovery.
It is **not yet built, signed, installed or distributed**. Owner remains the
previously signed115, last observed OFF/capture closed19:39:10UTC; no fresh phone
readback in this source step. Public/invitation/updater113/catalog7 remains
immutable. Linux0.2.11 and Windows0.2.16/catalog12 are unchanged. No new download
link or installer checksum exists until exact artifacts pass qualification.

## Required gates and order

1. Materialize the common capsule from the committed helper; reproduce the
   accepted predecessor and build the candidate twice with Go1.26.1/CGO1 and
   `fc_perf_diagnostic`, `-trimpath -buildvcs=false`. Preserve both old binaries.
2. Run idle, slow-link, transient-ICE, RESET, bootstrap authorization, ownership
   and canonical-policy gates. Exercise mixed old/current peers, including the
   installed115 native source, and paced synthetic links; distinguish local
   protocol/transport evidence from live provider/phone acceptance. Retain known
   inherited fixture failures and optional skips, not blanket PASS labels.
3. Stage the **same binary bytes** on NL2 first, then NL1. Before each change,
   validate exact current executable/locator/config pins, credential headroom,
   canonical service-user access and absence of a competing owned operation.
   Pause the common writer with automatic-resume watchdog, keep node operation
   locks and change executable/locator/snapshot pins atomically under custody.
4. Require new seeds and independent `/proc/PID/exe` readback with equal hashes,
   no restart loops, unchanged identity/profile bytes and ordinary-service PIDs.
   Resume and evaluate the common writer; preserve disabled boot state until
   its separate product gate. No public APK publication follows automatically.
5. Android116 requires exact hosted CI/API27/API35, artifact source/licenses/ABI/
   16K/provenance and UI review, then protected existing-key offline signing and
   in-place installation/readback. No data clear, reenrollment or consent bypass.
6. Only then run consented paired quiet/loss/reconnect and DNS/normal-TLS egress
   checks on each selected node. Track initial media/ICE loss and the previously
   unproven physical busy-holder attribution; CONNECTED or equal server hashes
   alone do not prove stability or guarantee every network/application.

## Rollback and evidence custody

On failed runtime activation, restore only that node's saved executable/locator/
unit/config references under the same writer pause and operation lock, verify a
fresh seed, and resume the common writer. Never restore product DB, client profile
or authority/key state. Preserve each node's own old hash until the shared runtime
is accepted; do not substitute the other node's old baseline as a rollback.
An Android repair uses a higher immutable versionCode while retaining identity.

Current private work/evidence directory:
`state-client-build/mesh-unified-20261104/`. No token, profile, source capsule,
raw user export, private key, signing vault or database is committed.
The earlier [idle source proof](2026-11-04-mesh-idle-ack-cleanup.md) and
[physical115 failure](2026-11-04-android115-mesh-cleanup.md#physical115-paired-acceptance--manual-cleanup-pass-traffic-fail)
remain retained; this checkpoint does not mark those physical failures resolved.
