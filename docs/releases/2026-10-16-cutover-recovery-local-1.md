# CUTOVER-RECOVERY-LOCAL-1 — bounded Android restoration candidate

**RESULT=LOCAL_CANDIDATE_PASS_WITH_LIMITS; LIVE_RECOVERY=NOT_TESTED; INSTALLED=NO.**
The owner approved implementing recovery and then installing the checked changes.
This checkpoint implements the Android restoration fix independently of the earlier
ReliableStream throughput candidate. It is not a combined speed/recovery deployment.

## Evidence and exact boundary

The retained [export10 analysis](2026-10-16-ui60-owner-call-drop-export10.md) already
establishes one scheduled maintenance interruption of SESSION_S9, followed by reuse
of the old runtime directory and `SEED_ADMISSION/DEADLINE`. `BOOTSTRAP_UNAVAILABLE`
then stops restoration. A later manual connection working is consistent with this
failure path; it does not prove a universal ten-minute session timer or explain every
reported call drop. No new phone/server observations or historical log search occur.

| Identity | Value |
|---|---|
| Review parent | `b10d9cac393e78b764ab193da7ba7bbbed4ac367` |
| Retained UI60-4 source inventory, not Git SHA | `e90893aee5fdc04aae1cacd296d5291ca8a743350de42334b290f08504c48fce` |
| Candidate cumulative source inventory, not Git SHA | `ea9312d013aac02a190a06b8ad9091e1245ef63a994db6618054dde27739c0d4` |
| Client recovery patch SHA256 | `2d614975643d909d554c0a75d05d1db85e06951d3ebede74fa2fe8b76100b962` |
| Last verified installed signed APK; not read again here | `1bf56c381e76913d77c4dc518961020d82d2bfec33da69777a504b7569be15ef` |
| Candidate version | `0.1.18-research84-ui60-4-recovery1`, code84 |
| Final unsigned APK SHA256 / size | `7774249a4c6a99c3ffb8af24daa1ac0d76b5d5a14a3436bdb5ed2b8b451678c2` /55,992,668bytes |
| New signed APK | NOT_CREATED |
| Retained native bytes | `be70a66ccc2bcbf0478915fd414c32de3bedb2a0ae0c3222a53e65eebd0a92b2` |
| Native source/build inventory | `b36c4a21ee6cf04acb192a0e6d140fa565b3e5ae75f6fc8d028d029c3152781d` |
| Gateway executable, last confirmed; not queried/changed here | `a537257162348afc35b1ebc08755d8c5dc1cd90e74c49e3987fb3eb81885e61f` |

Working source is an isolated copy of retained UI60-4, not root main, the publication
tree's historical product files, or the fast-retransmit derivative. All49 baseline
inventory entries are verified first. Eight changed files: six Java product files,
one new JVM test file and the private versionName in Gradle. VersionCode, minSdk31,
ARM64, permissions, UI/map, JNI/native producer and all Go sources remain unchanged.
The existing native producer/provenance checks remain enabled.

## Implemented behavior

1. `AutomaticConnection` passes restoration state into its new restricted engine.
   Existing callers/chat and an ordinary initial warm-start keep their previous mode.
2. `RestrictedBootstrap` distinguishes a temporary readiness fetch failure **with a
   still validated usable cache** from authorization/trust/import/unknown failures.
   `FriendsRestricted` carries this flag in its per-fetch immutable selection, not
   the process-wide display string. Shared prewarm still uses the existing single
   pending future and normal proof/import/ACK path.
3. During restoration only, a cached response after failed refresh is not used to
   start another native session. It schedules a bounded retry with another normal
   authenticated refresh. Nothing deletes the cache or blocks a chat consumer from
   its normal warm-start selection. A successful authenticated response may still
   describe an old runtime until publication finishes; refresh is not proof of a
   live directory.
4. A completed, handle-matching native `SEED_ADMISSION/DEADLINE|IO_DEADLINE` can also
   permit a delayed restoration retry. It requires the initial `STARTUP_CALLER`
   observation, matching error, LIVE/DEADLINE context and `stop_at_observation=NONE`.
   A later `CLEANUP` is allowed only with an observed timestamp at/after that failure.
   Cancellation, startup-budget/local stops, mismatched/missing evidence, HELLO wait,
   Family/certificate/credential/protocol failures and missing JNI do not gain retries.
5. `ConnectivityOrchestrator.Rejected` retains the existing failure category and
   attached startup cause; its narrow extra retry flag is not a new success state.
   Only restoration of an already connected session can use it. At most **two
   additional delayed bootstrap recovery series** are allowed before FAILED; success
   resets this per-outage counter. Existing backoff30/60/120s-cap and per-candidate/
   connect budgets stay unchanged. No blanket retry of `BOOTSTRAP_UNAVAILABLE`.
6. Every attempt uses existing cleanup, interrupt checks and one-owner sequencing.
   AUTH/OFF prevent further opens; cleanup failure stops recovery. The blocking VPN
   guard remains until ordinary disconnect. Native stats are consumed only at the
   two existing engine call sites; there is no extra reader or polling frequency.

The new retry allowance changes **client recovery policy deliberately**, not transport
wire, queues, security or server admission policy. Existing NETWORK/TRANSPORT_UNAVAILABLE
backoff behavior is not converted to a new finite lifetime. The two-series cap applies
to the new bootstrap allowance, not all possible network losses over app lifetime.

### Tradeoff and boundaries

Restoration now requires successful readiness refresh rather than falling back to a
valid cache after a refresh outage. This can delay recovery in a restricted underlay
where control access remains unavailable even though a cached runtime might work.
Initial warm-start/cache behavior remains intact. An expired, denied, invalid or
missing cache does not gain retry permission merely because fetch timed out. No
expired material is used, no floors reset, and no manual credential recovery occurs.

The historical failure is before lease acquisition, so an early exchange tag is not
expected there. HELLO wait is intentionally not reclassified: exact holder evidence
is still needed for that separate case. Normal correlation/export privacy and their
retention limits remain unchanged; new attempts are not relabelled manual CONNECTs.
The latest startup scalar can be replaced by the next attempt as before; this patch
does not introduce an all-attempt failure archive. The original cause/observation
used for the decision and the existing bounded failure/recovery events are preserved
within their own surfaces. Do not claim every intermediate attempt's full startup
record will survive a later normal export.

## Local validation

The new `CutoverRecoveryTest` combines the real Java orchestrator, refresh selector,
cache/import path and startup projector with synthetic Host/readiness/native records.
It is not real Android/provider/Family TLS or a measured speed test. Coverage includes
temporary refresh outage → new directory, still-published old directory → seed
deadline → refreshed retry, exact cap/backoff, successful budget reset, initial
CONNECT, AUTH/invalid/expired/revoked state, OFF/cleanup, independent cache consumer,
attempt matching, and first failure before later cleanup.

Targeted existing JVM/export/UI suites plus full unsigned assemble reuse the exact
accepted library. Final batch: **97/97 PASS**, followed by a fixed second execution
of **14/14 new recovery tests PASS**, no skips. Full Gradle assemble and vital lint
PASS; ordinary native/source provenance guard PASS. APK readback confirms package
`com.familyconnect.app.friends`, code84, minSdk31/target35, ARM64, non-debuggable,
unchanged permissions, alignment PASS and unsigned status. All packaged shared
libraries and `assets/restricted-build.json` match retained UI60-4 exactly. DEX/app
source provenance changes belong to this new Java artifact, not a native rebuild.
The APK verifier initially lacked Java on PATH; the runner now supplies the retained
JDK explicitly. No signature verification success was inferred from that failed
tool invocation; final `apksigner verify` rejects the unsigned artifact as expected.

[Safe source/test/build receipts](../../research/cutover-recovery-20261016/README.md)
include an exact eight-file patch round-trip and2,004 other unchanged source files
(Git metadata and Gradle-generated `clients/android/build` reports excluded).
Two preliminary build invocations were deliberately stopped during
source review (late native cleanup and persisted denial cases); they are not PASS or
retry-until-pass results. The first completed build ran97 tests:83 existing plus6 new
passed,8 new cases failed because their synthetic fetch skipped the required receipt
challenge/authorized transitions, so the initial fixture connection never succeeded.
Only that fixture was corrected, with an explicit initial-CONNECTED assertion added;
the product import/authentication guard was not weakened. This failed run and both
stopped-run receipts remain private; final validation is a separate fixed batch.

CPU quota is half one core, with no emulator, start below75°C and stop at85°C; a
finite runner deadline also stops the owned process group. Final batch362.435s,
peak77°C, normal exit0; the two stopped batches peak64/65°C and the failed-fixture
batch peak77°C. No thermal cutoff was reached. Product performance is not inferred
from thermal-constrained build timing.

## Installation and remaining work

No signing, ADB, installation, CONNECT, export, SSH, gateway/credential operation or
public distribution occurs in this local checkpoint. Final live VPN state is **NOT
OBSERVED**, not asserted OFF. The last verified installed UI60-4 remains the known
artifact; no current-device identity is inferred from that old receipt.

The owner wants installation after checks. This recovery-only unsigned APK is not
presented as containing the [throughput candidate](2026-10-16-reliable-fast-recovery-local-1.md).
Before a combined installation, finish its full TLS/mux/VP8/mixed-peer and reordering
checks, build/verify the combined native/APK, then use the existing previous-key
signing workflow. Preserve the signed UI60-4 backup; code84 is not raised here. Fresh
package/signer/version/VPN-OFF metadata is required before any replace-install;
an unexpectedly newer artifact must not be overwritten. No forced restart, hidden
CONNECT or production fault is part of validation.

Live recovery, handset speed, field restriction coverage, handoff, supervisor and
release remain unproven/open. Previous bounded acceptance applies only to its exact
earlier artifacts and time window. Historical reports are not rewritten.

Actions: one isolated recovery derivative; four build batches (two intentionally
stopped, one fixture-failure batch, one final PASS batch), five Gradle invocations,
two completed unsigned assemblies; three actual JVM runs (97 with8 fixture failures,
then97 PASS and14 PASS). Native/gateway rebuilds0; signing/install/rollback0;
ADB/SSH/CONNECT/export/restart/maintenance/deployment0; emulator0; public release,
catalog/main/workflow changes0. Phone and gateway are not polled or changed here.
