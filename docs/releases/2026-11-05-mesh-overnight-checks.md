# MESH overnight checks — 5 November 2026

## Scope and retained delivery

Owner explicitly authorized unattended stability checks overnight. Selected scope is
the existing MESH incident: paired-DNS loss, disconnect/recovery, both-node equivalence,
weak-link tests and bounded sustained observations. No public rollout or unrelated PLAN
successor. Android118 remains the exact signed owner build from
[its qualification receipt](2026-11-05-android118-signaling-diagnostics.md); public113/
catalog7 and desktops are unchanged. Both NL nodes retain gateway70e6c0fc. No new version,
gateway binary, credential policy, timeout, retry limit or owner admission is changed.

Local evidence root is `state-client-build/mesh-overnight-20261105/`, ignored/private.
No private identifiers, profiles, product databases or raw journals are committed.
Existing unrelated dirty documentation and untracked work are retained.

## Initial observation and independently attributed maintenance interruption

A new30-minute diagnostic observation starts00:11:59UTC on the existing118/NL2 session.
This is a new characterization run, not a retry that erases the earlier7/8 DNS failure.
Its first round passes8 wire DNS,2 Android hostname HTTPS and2 exact-NL2 egress checks.
The initial session subsequently fails: phone first cause00:13:19.709UTC is
RELIABLE_FRAME_TIMEOUT/RELIABLE_EXHAUSTION. No preceding WebSocket/ICE failure is recorded.
VPN capture remains open; normal automatic recovery is observed CONNECTED on a new
session at00:14:40.897UTC, without an operator Connect/Disconnect or network mutation.
Sampled RESTORING starts00:13:24.548UTC; this is not uninterrupted stability.

Independent systemd and exact-session gateway records establish the immediate cause:

| Event | UTC |
| --- | --- |
| RU scheduled credential renewal starts | 00:12:30.836 |
| NL1 bootstrap stopping / stopped | 00:12:56.009 / 00:12:56.174 |
| NL2 bootstrap stopping / stopped | 00:12:58.548 / 00:12:58.579 |
| NL2 exact session parent cancellation | 00:12:58.555 |
| NL1 / NL2 new bootstrap start | 00:13:25.664 / 00:13:27.740 |
| RU renewal finishes, result COMMITTED | 00:13:37.042 |

New running PIDs are1436865/1252999, both executable hashes still70e6c0fc and systemd
NRestarts0. NRestarts0 alone is not proof of no stop/start; this scheduled operation is
not counted as an automatic crash restart. No assistant restart was issued. The existing
controller explicitly permits approved leaf/CRL scheduled maintenance with unknown
session inventory and zero_downtime=false, then quiesces the readers. Authentication,
expiry, revocation and coordinated publication must not be weakened to hide this outage.
No perpetual timer pause or unsafely extended credentials are introduced.

The broad bootstrap journal query reaches its3000-entry bound; it is not used to claim
an exhaustive historical restart inventory. Exact current-session evidence and the
separate RU renewal journal cover this interruption. The earlier117 WebSocket read error
and118 paired-DNS timeout are not reclassified as renewal failures without evidence.

## Completed isolated regressions

The following are local checks, not substitutes for physical handset/provider acceptance.
Counts include repeated runs and subtests; they are not summed as distinct product cases.

| Check | Result |
| --- | --- |
| TCP/DNS mux, reliable stream, protected underlay, whole-device and diagnostic packages; race, three repetitions | 990 PASS; three optional performance skips |
| Focused real-Pion/RTP/signaling and receive-stall checks; race, three repetitions | 216 PASS |
| Patched pinned-Xray/gVisor DNS packet boundary; race,100 repetitions | 200 PASS |
| All packet-boundary tests; race,10 repetitions | 30 PASS |
| Explicit paced subprocess link,256/512/1000kbit, windows8/32, reverse rate one quarter, drops/retransmissions; race, twice | 12 scenarios PASS,14 including parent tests |
| Pion ICE outage/recovery and head-loss cases; race, three repetitions | 42 PASS; three credential-dependent live-provider skips |
| Explicit offline performance matrix,40ms modeled delay; race | 28 scenarios PASS,29 including parent |
| New paired A/AAAA DNS under authenticated loss/reordering/duplication and concurrent TCP bulk; race,20 repetitions | 20 PASS |
| Credential/maintenance/multi-gateway/recovery/publication Python tests in isolated root container | 397 PASS,5 optional provenance/native skips |

The new source regression uses distinct IDs per A/AAAA pair, shared wire IDs within
each pair,16 concurrent requests, byte-exact bulk echo, exercised retransmissions,
zero DNS mismatch/error/timeout and subsequent progress on the same authenticated
session. It adds coverage, not a reproduction or correction of the handset timeout.
The earlier20-run all-identical-ID characterization also passes and is retained separately.

The initial paced command omitted its opt-in and skipped that matrix; the explicit
enabled run above is the evidence. Python prerequisites are also retained honestly:
the first user-space run fails root ownership requirements; the first container run
fails because `/tmp` is writable by others and `/usr/bin/python3` is absent. The corrected
disposable container uses a root-owned non-writable-by-others test parent and the normal
Python interpreter path. All27 control/identity lockfile pins match. No product permission
checks are mocked, removed or relaxed. Source is read-only, network is disabled and only
synthetic state is created; production profiles/databases are not mounted.

## Final bounded observations and additional checks

The original observation completes in1838.917s with114 samples and seven traffic rounds.
All56 wire-DNS,14 Android HTTPS and14 exact-NL2 egress cases succeed, but its uninterrupted
session gate remains **FAIL** because of the recorded maintenance interruption. A separate
636.150s continuation on the recovered session completes three more rounds, all passing,
with42 samples. This continuation is not mislabeled a new30-minute gate.

Across the two recordings, the recovered session is sampled unchanged and healthy from
00:14:40.897 to00:53:18.780UTC: **2317.883s /38m37.883s**,144 samples and nine post-recovery
traffic rounds. Total observed traffic is80/80 wire-DNS,20/20 Android HTTPS and20/20 exact
NL2-egress checks. No operator reconnect, shaping, loss injection or network setting change
is performed. This supports bounded post-recovery continuity on the normal link, not
both-node weak-link acceptance or proof that the earlier single DNS timeout was fixed.
Final diagnostic counters retain66 unknown_stream events, zero dns_unmatched/DNS errors,
75 retransmissions and73 recovery timeouts; nonzero counters are not hidden or assigned
an unproven cause. No new terminal signaling/ICE failure is observed in this segment.

Final consented phone readback retains118, the same Support ID, CONNECTED/native2/NONE,
open VPN capture and no synthetic probe. Exact recovered-session server correlation is
untruncated: NL2 has748 matching records and NL1 zero; both processes remain active with
PIDs1436865/1252999 and identical70e6c0fc executables. No claim that the phone tested NL1.

The150ms offline matrix also passes28 scenarios/29 tests under race. Two additional
credential cases pass using accepted118 source13e0b37 and checker SHA256
`a29815dbf94db34325425ed79904afbbfcdf88dd071384e2c696c0d891f61ff7`: coordinated operational
authority compatibility in the isolated root container, and publication/native validation
under the required non-root publisher identity. The latter initially rejects UID0 as
designed; it passes in the correctly pinned non-root environment without a source change.
Thus399 selected Python cases have executed successfully; three exact historical generic-
snapshot archive cases remain skipped, not accepted by substitution.

At00:44:38UTC a read-only public download verifies normal system-trusted HTTPS, the offline
catalog signature/lease, exact repository catalog bytes, version113/sequence7/minSDK27,
and the complete50,273,696-byte APK SHA256
`6078d0610272c5eb1b8008d330f9e646163b90b89df180b4bd56fd8ae4edc094`.
Owner118 remains distinct from public113. No public file, catalog or invitation is changed.

## Source checkpoint and CI limitations

Regression/documentation source `ff9c602c484700b30705efd348c5db5ca1cf304c` is committed,
pushed and remote main verified. It changes a Go test and documentation, not production
Android/carrier code. No installer from this new CI run is signed, installed or published.

[Client builds41942402171](https://github.com/Joker20380/family_connect/actions/runs/41942402171)
finishes **FAIL**: Linux, Windows and Windows compatibility pass, but the Android emulator
job fails `InvitationRuntimeTest.browsableLinksReuseActivityAndRejectMalformedToken`
at line53 (expected synthetic invitation token, observed empty input). Downloaded runtime
diagnostics ZIP SHA256 `c2aa15546dd27769c1362633a32e7a4a67bc49d19679e0f7c6fd5056016a9283`
confirms this assertion; it is not a demonstrated MESH data-plane failure. Runtime XML
contains76 entries, one failure and29 skips. No rerun-to-green or unrelated invitation
code correction is performed. Accepted installed118/13e0b37 remains unchanged.
[phase0 41942402154](https://github.com/Joker20380/family_connect/actions/runs/41942402154)
also fails at source-pinned release fixture provisioning and isolated failover-stack build,
before the corresponding full tests. Therefore no full-CI or release acceptance is claimed.

## Remaining gates and next work

- Remove the maintenance-induced connection interruption through an explicitly designed,
  authenticated renewal transition. Preserve expiry/revocation, publication atomicity and
  rollback invariants; merely disabling renewal or lengthening credentials is not a fix.
- Attribute/reproduce the retained118 paired-DNS timeout and117 WebSocket read failure.
  Later80/80 DNS successes do not erase the earlier failure or establish its cause.
- Run physical slow/lossy and sustained acceptance on **both** NL nodes. This run keeps
  the existing NL2 connection and does not exercise a physical NL1 switch, a weak handset
  radio or a60-minute observation. Isolated models are not replacements for these gates.
- Retain CI failures and unavailable exact historical/provider fixtures separately.
  Do not promote118, manufacture119 or start an unrelated queued task from this checkpoint.

## Rollback and cleanup

No product/server mutation needs rollback in this checkpoint. The ordinary-UID synthetic
probe is removed after each observation and verified absent in the final readback.
Do not uninstall/reset the product, reenroll, evict an
owner, disable expiry checks or change ordinary AWG/TCP services. Continue phone diagnostics
only while the normal in-app USB grant remains authorized; broad task permission is not
an access-control bypass. Source/documentation rollback is an ordinary non-force revert.
