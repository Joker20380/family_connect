# 17 November2026 — IOS-DEVELOPMENT-HANDOFF-1

iOS source gate PASS; development candidate, not physical VPN acceptance.
[Final exact-head CI, artifact and integration receipt in PR42](https://github.com/Joker20380/family_connect/pull/42#issuecomment-6940824604)
is authoritative for subsequent documentation heads and ordinary merge. A pending
receipt is not integration PASS. Owner selected startup coordination, provider
lifecycle, VPN manager, secure synthetic-material handoff and development build.
Base remote main bda954fb27ad7115b8c373929cf3e80e84992175 unchanged since PR41.
All5 post-merge workflows SUCCESS (43999095437/95720/95477/95425/95469).
[PR41 exact d02fce99 final acceptance](https://github.com/Joker20380/family_connect/pull/41#issuecomment-6935466490)
remains accepted; new work needs its own checks. Dirty original checkout preserved.

## Requested RU readback first — no recovery

At05:20:30UTC, AWG/TCP inactive/PID0 since01:03:56UTC. Watcher auto-restart/PID0,
432 restarts; later snapshots can temporarily show active while its restart fails.
Bounded single-current-journal read01:02:30–01:05:15 returns24 manager events:
AWG stop01:03:56.231823, TCP stop.250286; both exit successfully; watcher exits1
at.466839, result exit-code. Restart attempts fail after about30s. No watchdog event
appears in this selected window; this is not a whole-history exclusion.

First-failure file1979 bytes, SHA256
e5d769ec262cbbf15defb2d779741d5140ec048a11dd1a343df0d0f64c3263a2:
mode watch, phase persist_file, boundary after, reason TRANSPORT_OPERATION_DEADLINE,
budget8s, elapsed9.593906831s. decision_state file_fsync takes9.538853733s,
self CPU0.00031s,0 major faults,3 voluntary switches; replace_completed=false.
The preceding engine queries take0.005055/0.032449/0.004255s. This identifies the
operation crossing the deadline, not why the block/filesystem sync took so long.
Do not substitute the older watchdog-only attribution for this captured failure.

Current IO PSI full avg10/60/300=2.94/3.51/3.50%; memory full averages0;
memory available1210MiB of1962MiB, swap used478MiB, disk6.8GiB free. These later
snapshots do not attribute the01:03 delay to provider, OOM, another service or our
diagnostics. No broad journal scan, DB/profile/key read, observer, backup, restore,
restart, server policy or neighbouring service operation. RU remains down; a
separately selected guarded recovery/latency investigation is needed, not a longer
deadline or a durability bypass disguised as a fix.

## Startup baseline

Added the requested deterministic real NativeSession(mode1) regression: hold network
configuration completion, cancel native only, bounded wait for terminal, release
configure(nil), require one startup error/no pump/zero handles. Old implementation
is retained in checkpoint `2ea1f6f2e9c995e9611c7648cac87630951a1dc7`.
macOS run44023861642 builds both unsigned targets successfully, then **fails**
`isolated.cancelled-native-must-not-start-successfully` with handles0, exactly as
predicted. Downloaded artifact14302731166 ZIP SHA256
`a01da92536bc1da02a35fb0d731bd4d5962894375501b5c510b9534e5bb1a47e`.
No unchanged retry. This is baseline failure evidence, not acceptance.

Implementation candidate0.0.1/build2 adds native serialized CommitStart after
settings completion; fresh control-queue status; stop returns retained first error.
Provider generation cleanup joins native resources, isolates old callbacks, and
blocks overlap while a system settings callback remains outstanding. Manager uses
load/find/save/reload/session APIs; status is observed NEVPNStatus, not start return.
Keychain immutable bundle/reference handoff, strict offline existing trust checks,
AfterFirstUnlockThisDeviceOnly policy and parameterized manual development signing
are implemented. No common Android/desktop transport runtime change. New Swift
checks cover deterministic stale handoff, settings error, provider cleanup/recreate,
fake preferences save/reload/permission errors and fake Keychain denial/corruption.
These models do not prove system VPN preferences or interprocess Keychain sharing.
Go tests generate fresh synthetic certs/CRLs in memory, never stored as artifacts.
No old assertion or test budget weakened; a new10s initial path eligibility deadline
is distinct from unchanged180s native startup.

Self-review follow-up: preserve BridgeFailure numeric code across NSError/process
boundary, read actual last disconnect error with generation guards, expose file
import failure safely, test cancellation during reload as well as save, and verify
development provisioning grants with synthetic Python models (including a valid
App ID prefix different from Team ID).9 project/provisioning tests pass locally.
This is not real signing or cross-process Keychain acceptance.

Candidatea9e27770/run44026144720: device/simulator builds PASS; original requested
native-end-during-configure regression PASS. New stale-worker test then failed
`isolated.native-terminal`: its helper incorrectly treated **Stopped=4** as a live
state (ABI already documents1/2/3/4). Artifact14304015353 ZIP SHA256
`385e10180fe4eec91354d66235b2d7254ec609d5b8636e1cd2fb85462c18c242`.
Correct the helper to require state4 or a negative failure, preserving its3s limit
and all no-pump/exactly-once/cleanup assertions. Also map positive stopped state
to Closed(-2) in Swift error reporting. This changes no native ABI or test budget.
Signing self-review additionally rejects a lone profile parameter and verifies
the final signed app/extension identifiers, Team, grants and expanded Info values.
10 Python tests and20 repetitions of new Go trust/commit race tests pass locally.

b7ebab4d PR run44026619810 failed the **unchanged untagged** shared packet test
TestDNSPairedDatagramsReuseSourcePort at dns_test.go:126, UDP read timeout under
its existing1s deadline (test elapsed1.37s). Tagged packet and new Go bridge tests
passed in that run; device/simulator build was not reached. Log-only artifact
14302894331 ZIP SHA256 `6b630b04d95f556f3460d727309c43737cb94c9759473301a7debad9684341b3`.
Cause of that timing failure is not proven. No assertion/deadline/common runtime
change or unchanged retry; subsequent heads contain actual reviewed iOS fixes.
UI review adds safe operation-stage context for save/consent, reload and start
errors, and descriptive numeric native errors without material values.

Cross-language format review found Go encoding/json accepts case-insensitive
field aliases while Swift Codable does not. Require the exact four outer import
keys before decoding; reject Version/version shadowing rather than validate one
value in Go and consume another in Swift. Synthetic case-alias/case-shadow tests
exercise this agreement. Import also runs Swift decoding before storing, so base64
or format accepted by only one decoder cannot become an unusable stored item.
Existing common profile/trust parsing is unchanged.

3c36a571 push run44029055867 failed the same paired-DNS positive completion test,
this time tagged (1.07s); new bridge/trust tests passed. Artifact14304108782 ZIP
SHA256 `411c70d2b8eb9097eb7088cf98780015487888369b0938d7f8f81071ac064f1f`.
This repeats the1s harness sensitivity but does not prove host scheduling versus
packet-loss cause. No unchanged run was retried. The paired fixture's positive
completion budget is now explicitly **1s → 3s**, matching the previously accepted
positive DNS/TCP fixture budget; it is a bounded correctness check, not a1s product
latency SLA. Both exact A/AAAA replies, distinct IDs, source-port reuse and two
queries remain mandatory. Add checked full writes and per-response elapsed/budget/
query-count/error diagnostics. No skips/retries, no negative-UDP/cancel/startup
budget changes, and no transport/runtime change. A genuinely lost reply still
fails within3s. This test-only common-file change is qualified tagged and untagged;
do not describe it as proof of a network performance improvement or a loss fix.

7b915ddb iOS push44030127738 and PR44030134489 both PASS, but mandatory Client
builds PR44030134337 failed the unchanged carrier test
TestLocalCompletionDeadlinesRepeatedGenerations (`local_deadline_test.go:55`):
expected local DeadlineExceeded, got `reliable stream: remote reset` (0.82s test).
Artifact14304304964 SHA256 `344f729db14e11dbae148b7239262ab09854b188e597e80dbbbddb78dd1e8138`.
Inspection shows both peers used MaxAge150ms: the fixture deliberately stalls a
DATA write, blocking subsequent local ACK writes; the receiving peer's idle/handshake
deadline can send RESET before the local completion deadline. This is a competing
terminal cause in the fixture, not evidence the new iOS code changed ReliableStream.
Isolate the peer with MaxAge1s. Keep the **sender**150ms completion deadline,
500ms assertion,1s parent context, exact DeadlineExceeded, zero retransmissions
and repeated-generation checks unchanged. Do not accept ErrReset as an alternative
or alter runtime first-error selection. Only the peer test setup changes. A local
30-repeat race run of the original fixture passed; that does not erase its CI
failure or prove the precise scheduling of the remote reset.
The isolated-peer version also passes30 repetitions under `-race` locally
(60.236s), with the sender deadline and all assertions retained.

The same7b915ddb Linux control PR run44030134438 fails an unrelated desktop
teardown invariant: `test_control_completion_interruptions_are_bounded[prepare-deadline]`
observes13 process descriptors versus14 at entry (`test_chat_public_completion.py:23`).
Standard context:5794 passed,276 skipped,1 teardown error; root258 and snapshot314
98 pass. Artifact14304439543 SHA256
`75058ec35c9d9c22d09bfc91d6175abf55874796c9789307ca63ea1a1f38a98c`.
This is not an iOS failure or a proven leak; cause of the descriptor disappearance
is unproven. Do not change unrelated desktop assertions or retry this head for green.
The subsequent head changes the reviewed carrier fixture, not desktop runtime.

### Qualified intermediate iOS source7b915ddb

Exact head `7b915ddbadb5aa4c248e7c9e9d57333f0146e348`: macOS PR run44030134489
and push44030127738 PASS. Artifact14304543162 (79,930,391 bytes), ZIP SHA256
`7c87bb82ab9639e7ad3d29c02b68f50c46ce07ac0ba16891d33f157f17ee56b1`;
all208 manifest file hashes verified after download. Unsigned device arm64 and
separate simulator arm64 builds, native symbols, nine Swift/C/Go isolated test
groups and zero surviving handles PASS. Screenshot inspected: development controls
and NOT_RUN/ordinary-routing warnings present; no material values displayed.
This qualifies this iOS source only, not the failed common gates or later heads.

Toolchain: macOS15.8.2 runner image20261104.0514.1, Xcode16.4/16F6, SDK18.5,
Swift6.1.2, clang17.0.0, Go1.26.1, Python3.15.2. Both Go targets are **ios/arm64**;
C triples `arm64-apple-ios16.0` and `arm64-apple-ios16.0-simulator` respectively.
Same408-package/31-module closure and required notices/sources/patches retained.
Paired DNS replies completed at403.105/403.441ms tagged and335.983/336.365ms
untagged, with two queries and29-byte exact replies in each. These observations
do not explain prior1s failures or establish a performance SLA.

## Qualified development candidate

Source `fb13d23b138ca16ce969ad24d1f3d093ba641f0a`, development0.0.1/build2:
[PR macOS44032183193](https://github.com/Joker20380/family_connect/actions/runs/44032183193)
and [push macOS44032176415](https://github.com/Joker20380/family_connect/actions/runs/44032176415)
PASS. [Unsigned artifact14305768210](https://github.com/Joker20380/family_connect/actions/runs/44032183193/artifacts/14305768210)
is79,931,780 bytes; downloaded ZIP SHA256
`5363ef4dd9511615bfcf4c192289cd6b9f956f97fbc0504a524bb67028feee89`.
All208 per-file hashes match. Actual runner image20261112.0539.3, macOS15.8.2;
Xcode16.4/16F6, Swift6.1.2, clang17.0.0, Go1.26.1, SDK18.5 unchanged.

| Gate | Observed result |
| --- | --- |
| iPhone build | PASS unsigned app + embedded Packet Tunnel extension; ios/arm64, device platform |
| Simulator build | PASS separate ios/arm64 simulator platform; iPhone16/iOS18.5 runtime |
| MESH linkage/call | PASS real C exports, Go session/packet code and unchanged408-package/31-module closure |
| Startup regression | PASS real native cancellation while configure is held, one error/no pump/zero handles; baseline failure retained |
| Async boundary | PASS stale worker/control, configure error, late callback, cancellation, packet copy/family/queue and first-error checks |
| Provider lifecycle | PASS isolated generation cleanup/recreation/settings lease; not installed extension execution |
| Manager/Keychain | PASS isolated adapters/models + real Go synthetic trust validation; not system preferences or provisioned sharing |
| Simulator suite | PASS all nine named groups, handles0; ad-hoc runtime copy only, retained artifacts unsigned |
| Local source checks | PASS10 Python project/provisioning tests; Go race/strict-import tests and30 isolated-peer repetitions; public-source/docs guards |
| Mandatory integration CI | Final exact source and all outcomes recorded in the linked PR42 receipt; not inferred from iOS PASS |

Both native archives remain actually linked into the products, not unused sidecars.
Live mode still uses bootstrap/admission, Family TLS, ReliableStream, mux/DNS,
Telemost VP8/RTP and the existing packet engine; no Android JNI copy, new carrier,
direct fallback or production credential is introduced. The simulator fixture is
not a Telemost connection or a system TUN. Notices, source archives, original and
endpoint patches remain in the artifact; this is procedural, not bitwise reproducibility.

Author self-review5934075934 reviewed this source (not independent approval).
At this documentation checkpoint the broader gates are still running. Their final
exact-head receipts, any failure and merge decision remain visible at the stable
PR42 link, without rewriting the failed attempts above or retrying unchanged runs.

## Owner handoff and remaining gate

Source preparation can proceed to an explicitly authorized **signed development
prototype**, not to a user VPN claim. The owner must supply/confirm:
- A specific iPhone model and actual iOS build, compatible authorized Mac/Xcode,
  device trust and Developer Mode. SDK18.5 does not qualify every newer phone.
- Apple Team and app/extension bundle IDs, granted packet-tunnel and shared
  app-specific Keychain capabilities, Apple Development identity and two valid
  device provisioning profiles. Keep all private signing material outside Git/CI.
- Disposable agreed test Family identity/CA/admission/directory and controlled
  IPv4 network access. Authenticate test material out of band; no production identity.

[Concrete signing/install commands and bounded five-step device plan](../../clients/ios/README.md#development-signing-and-installation--owner-mac-only)
cover consent/save/reload, unique own configuration, extension launch and Keychain,
then one real MESH startup before routes/recursion/containment and stop/restart tests.
Whitelist trial is separate and follows those gates. Do not put secrets in chat,
screenshots, CI or shared logs. No purchases/accounts are created by this task.

Real VPN preference installation, extension launch, interprocess Keychain sharing,
development signing/install, physical routes/recursion/leaks/memory/background,
Telemost and whitelist are all **NOT_RUN**. IPv4 IP_BOUND_IF and NWPathMonitor remain
experimental; IPv6-only/NAT64 and enforced routes are unsupported. No always-on or
kill switch; stopping can restore ordinary OS routing. No guaranteed erasure of
all Swift/Go secret copies. Public beta126/catalog9 and production unchanged.
Rollback is source revert; this development stage is not a rollout. RU availability
and underlying fsync latency remain a separate unresolved operational matter.
