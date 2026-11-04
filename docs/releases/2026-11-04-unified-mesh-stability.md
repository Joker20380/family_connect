# Unified MESH runtime and Android116 — 4 November 2026

**Current:** both NL gateways run identical70e6c0fc; guarded delivery and independent
canonical/seed/profile/process checks PASS. Android116 exact CI and downloaded
artifact/UI qualification PASS, still unsigned. Owner115/public113/catalog7 unchanged.
Physical stability acceptance OPEN; protected signing/in-place116 is the next gate.

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
passes, then17 failures/13 passes over30 race repetitions on unchanged source.
These tests are not
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

## Guarded runtime delivery —20:28–20:29UTC

Qualification checkpoint `880fcb3d6d9bb2ae14a78b10ff98be9ffbe5d7ed` is pushed
and remote-verified before activation. Common RU writer pauses with9820s credential
headroom and an8-minute automatic-resume watchdog. NL2 activates20:28:04UTC;
independent canary check passes20:28:27 before NL1 activates20:28:34. Independent
post-checks pass20:28:56/58 and a separate three-host inventory confirms:

| Node | Running `/proc/PID/exe` SHA256 | PID / restarts |
| --- | --- | --- |
| NL1 |`70e6c0fc1b920ad308e24667be94f674c34979dab6aa518e1a8194fff7c131b6`|1219052 /0|
| NL2 |`70e6c0fc1b920ad308e24667be94f674c34979dab6aa518e1a8194fff7c131b6`|1150135 /0|

Both use `/usr/local/lib/fc-profile-tools/unified-a597d2a/gateway`, active and
boot-disabled as before. Each node receives one controlled MESH stop/start, new
executable/locator/snapshot pins and a fresh unexpired seed. Exact profile bytes,
node-specific identities/paths, publisher policy and ordinary-service states/PIDs
remain unchanged. RU configuration/HTTP also remains unchanged; nothing touches
neighbouring services. Independent readback validates current canonical directory
contracts, not just the deployment command's exit code.

Common-writer evaluate returns `NOOP`; renewal and directory timers resume active,
the temporary watchdog is cancelled. Old binaries remain at their node-specific
cleanup-3a2584b2-primary/secondary paths with original8769eadf/5bcb32ea hashes.
Per-node rollback custody is `/var/lib/fc-profile-control/mesh-unified-a597d2a-20261104/`:
before-locator/config/snapshot/unit bytes, metadata and guarded operation receipts.
No rollback is needed; never restore identity/database state when reverting runtime.

At20:33:36/37UTC, more than five minutes after both activations, independent
checks still find the same PIDs/hash, zero restarts, fresh valid directories,
unchanged profiles and ordinary services. Separate final fleet inventory is
retained. This bounded service observation is not sustained phone/traffic evidence.

Normal-TLS HTTPS readback of the Android catalog remains byte-identical, SHA256
`2283a89ffa05e6ad439858f111f7272993b4e46e652c9efa11b44158b9f01b30`
(public113/sequence7). No public installer/catalog/invitation change, new signature,
phone installation or phone input is performed. The running-byte mismatch is closed;
the original physical media loss and exact busy-holder attribution are still open.
Remaining selected work: exact116 CI/artifact qualification, protected signing and
in-place delivery when permitted, then fresh consented paired quiet/loss/reconnect/
DNS/HTTPS evidence on each node. Do not mark full stability from deployment alone.

## Android version boundary

Candidate source becomes `0.1.18-beta116`/code116, retaining API27 compatibility,
the115 DNS/cleanup fixes and adding idle ACK expiry with guarded Android recovery.
It is **built and qualified, but not signed, installed or distributed**. Owner remains the
previously signed115, last observed OFF/capture closed19:39:10UTC; no fresh phone
readback in this source step. Public/invitation/updater113/catalog7 remains
immutable. Linux0.2.11 and Windows0.2.16/catalog12 are unchanged. No new download
link is published; the qualified unsigned checksum is recorded below.

## Android116 exact qualification —20:54UTC

Client builds41905046530 **attempt1 succeeds** on sourcea597d2a; Android job
126837410230 passes native/race/contracts, JVM/lint and API35/API27 instrumentation.
The four downloaded ZIPs match GitHub metadata digests and exact source/run bindings:

| Artifact | GitHub ID | ZIP SHA256 |
| --- | ---: | --- |
| ARM64 |13362476454|`948810f1f77e82d3bf8d74ef63182abd871f9ae58393b63b5544a63f58d5c63c`|
| Debug/JVM |13361758196|`d9c60f74be09bb97666a731b4fc41077739958d303db959c04f5b56369419297`|
| Runtime |13362491418|`988fcbf8310556de14e21795e05de5fc6b9dce45211183942b850605fb459d1e`|
| UI |13362431564|`ca3b2df8349408a60cf45761b14d410fc40d19b2590a7dbabb312f4ceeb8cdd4`|

Qualified unsigned Friends0.1.18-beta116/code116,50,260,237 bytes, SHA256
`754b1298a8b6f9bfc9f4bddc6c8662df0fa0917cea81046737cac20826b9b473`.
Package `com.familyconnect.app.friends`, ARM64, minSDK27/target35, non-debuggable;
12 native libraries, source/tree/JNI receipts, ELF/ZIP16K alignment, audio sources/
licenses and disabled provisioning verify. Debug419 and Friends414 JVM cases pass
without failures/skips. Runtime evidence:

| Runtime | Debug passed/skipped | Friends passed/skipped |
| --- | ---: | ---: |
| API35 / Android15 |28/25|19/4|
| API27 / Android8.1 |27/26|18/5|

Required picker, language, voice and legacy compatibility cases execute; conditional
skips remain explicit. Eight fresh screenshots are visually reviewed: RU/EN and
large-text three-node lists, green/orange load squares, failed controls, CPU-only
labels and legacy Codec2 text. These are emulator results, not a physical Huawei test.
Separate phase0/control fixture failures remain recorded; this is not whole-CI PASS.
Protected existing-key signing and in-place owner delivery remain undone. No public
catalog/installer/invitation update or new download link is authorized by this result.

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
