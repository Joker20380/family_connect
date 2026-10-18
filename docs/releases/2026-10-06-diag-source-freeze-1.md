# DIAG-SOURCE-FREEZE-1 — PASS

## Final closeout — 06.10

Normal-native stale provenance eliminated using the pinned authoritative builder;
OWNER-DIAGNOSTIC-PACKAGING-1 PASS and complete verify-apk.py PASS. Clean scoped
commit5327deb414ae8aa77ce2f9490fd99c9485eba740, tagdiag-owner-beta66-ci2,
all17 hosted workflows PASS. Existing Python/F1–F6/A–E receipts retained; Android,
native and downloaded package checks accepted. Beta66/code66 ownerDiagnostic is
signed with the accepted Friends-compatible signer, matching JNI/gateway sealed.
DIAG-PAIR-DEPLOY-1 is now allowed to START, not executed by this task.
[Exact artifact hashes, signer, immutable manifest and limitations](2026-10-06-normal-native-provenance-1.md).
No owner install/deploy/credentials/READY/arming/physical/soak/tester/public changes.

## Historical STOP evidence (superseded, preserved)

2026-10-06. **OWNER DIAGNOSTIC ONLY. Normal-native package provenance STOP.** No accepted
immutable successor pair exists. Do not begin DIAG-PAIR-DEPLOY-1.

## OWNER-DIAGNOSTIC-PACKAGING-1 follow-up — FAIL

[Precise baseline/input table, correction, hashes and receipts](2026-10-06-owner-diagnostic-packaging-1.md).
This supersedes the missing-input STOP without erasing it. Owner composition now
uses separate ignored JNI/assets output and preserves restricted native bytes.
Clean local acceptance candidate02f7eb9618bf1b5105cea7433a0c687dd9e452b1 contains
only the32 diagnostic paths plus .gitignore and package checker/tests. It is NOT
an accepted freeze/release commit and was not pushed. Original HEAD/index preserved.

Fresh owner/default JNI and unsigned APK builds pass. Owner/Friends258 unit tests
each pass; lint0errors,36/37warnings. Manifest package/version/non-debuggable and
DUMP-protected owner-only receiver pass. Restricted P1–P7 checks pass; owner JNI
ddb730d1192e700bbac6997deac0febf149d2b0e4cdf8a8cf75dbc0c2df89e69 matches packaged
bytes, schema1, source revision and clean native VCS metadata.

Mandatory standard normal-native verifier then FAILS: tcp_source_sha256 expected
be122bb32c4ecf59a6c3d49aaa2a8015e61562cd4123ef65b0278974dc05d988, but reused
awg-build.json records f5ec5e4908e56ebd595f1b96bf5d83fafad996105a75a73f9bbd4ee469eec1a6.
Original/scoped TCP source is identical. This is stale generated normal-native
provenance, not an excluded control change or a restricted JNI packaging failure.
Stopped as requested; no acceptance widening or metadata relabeling.

DIAG-SOURCE-FREEZE-1 stays PARTIAL. No accepted source freeze, hosted CI, gateway,
signing or pair manifest. DIAG-PAIR-DEPLOY-1 NOT allowed. Next rebuild authoritative
normal AWG/TCP generated inputs from exact scope and repeat complete APK acceptance.
No install/deploy/renewal/READY/arming/physical/soak/tester/public-channel operation.
Unchanged prior Go/Python/race/A–E/F1–F6 receipts retained; timing PASS unchanged.

## NATIVE-AUTHORITY-TIME-1 follow-up — 06.10

**NATIVE-AUTHORITY-TIME-1 = PASS; DIAG-SOURCE-FREEZE-1 = PARTIAL.**
[Full causal investigation, UTC trace and contract](2026-10-06-native-authority-time-1.md).
This supersedes the Python STOP below without erasing its failed receipts.

The preserved excluded readiness/control patch changes issuance from now to now-5
and the cap from now+lifetime to issued_at+lifetime. The old test fixture's directory
ceiling is now+lifetime-1, explaining exactly-4s.20 fresh mixed-process runs all fail
at-4s;5 controlled1.25s delays do not change it. Minimal module overlays isolate the
fetch calculation; neither ACK nor CRL-only changes produce this offset.
Authority JSON and native validation preserve integer absolute expiry exactly;
native accepts at expiry-1 and rejects at expiry. No security window is widened.

Disposable baseline8d04632 plus the same32 allowlisted diagnostic source files,
excluding unrelated control/test/docs edits: isolated test20/20 PASS; complete native
compatibility file19 PASS ×3; official-fixture full Python **1793 passed,26 skipped**.
No product source, assertion, clock or tolerance changed. This fixes the acceptance
input scope, not the excluded control branch. Mixed compatibility remains17 PASS/
2 FAIL. The copied32 files match the previous STOP byte-for-byte; original control
work and Git index are preserved. No freeze commit is implied by the test snapshot.

Remaining gates resumed at packaging input review. Gradle's resolved source providers
show ownerDiagnostic has main/AWG/ownerDiagnostic JNI/assets roots, but not Friends'
restricted-generated roots. Its present inputs contain neither libfc_restricted.so
nor restricted-build.json. `packaging-preflight.log` is a successful metadata query;
`packaging-preflight.json` records FAIL/NOT_READY of the input-presence gate, not an
APK build failure or a new timing regression. Native outputs have not been produced
for this variant; a future build must explicitly stage newly built owner-tagged JNI
and matching schema1/source_revision metadata in its inputs. Do not reuse beta65 or
default native bytes. No packaging correction was folded into this timing task.

Private receipts live under the existing evidence directory's
`native-authority-time-1/`; `snapshot.json`, repetition summaries, full-scoped.json,
native-mixed.json/native-scoped.json, packaging-preflight.json and final-closeout.json
bind the inputs and outcomes. Full Python log SHA256:
`03d8521758ef6ce02b4635c00ea304f801265e56e83a11ec2fe6caba2933b298`.
Working-copy scoped secret checks, source preservation and diff whitespace PASS.
These are not a post-staging source guard, release CI receipt or pair manifest.

Draft ownerDiagnostic beta66/code66/schema1, baseline8d04632 and required signer
67a90d1b remain unchanged. No frozen successor, accepted APK/JNI/gateway hashes,
signature, hosted CI, installation/deployment/renewal/READY/physical test/soak or
tester contact. No public beta65/default/catalog/invitation changes. No runtime
rollback needed. Next integrate owner-only native inputs, rerun only affected gates,
then complete clean-scoped freeze/CI/build/signature/pair verification. Existing
unchanged Android/Go/race source receipts are retained, not gratuitously rerun.
**DIAG-PAIR-DEPLOY-1 remains NOT allowed to start.**

## Resume after quota cleanup — 06.10, 04:36–04:52 UTC

**DIAG-SOURCE-FREEZE-1 = PARTIAL. DIAG-PAIR-DEPLOY-1 is NOT allowed to start.**
This section supersedes the initial Android STOP and pending-test entries below;
the original inventory, allowlists, safety contract and historical receipts remain.

Entry check: `/tmp` had about14GiB available, but `/tmp/fc-boot1-tools` had been
removed. Restored checksum-verified Gradle8.11.1, Temurin17, Android API35/build-tools35
and Go1.26.1 into ignored `diag-source-freeze-1/resume-tools`; Go1.26.0 additionally
restored because the official release-fixture builder explicitly requires it.
No project source edited. Before testing, every scoped hash matched the previous
`final-closeout.json`. Baseline HEAD remains
`8d046321039d0bd1e18ecc1af979ff90f591e029`; no scoped commit/tag/push or hosted CI run.
Latest deployment/release was checked through existing project receipts only;
no fresh phone, gateway or public-artifact probe was made.

### Fresh acceptance receipts

All filenames below are relative to the existing ignored evidence directory
`state-client-build/field65-export16/diag-source-freeze-1/`.

| Gate | Fresh result / receipt |
| --- | --- |
| Previously blocked ownerDiagnostic unit/lint | PASS,258 tests/41 suites,0 failures/errors/skips; lint0errors/36warnings; `android-acceptance-resume.log` and `.json` |
| Default Friends unit/lint | PASS,258 tests/41 suites,0 failures/errors/skips; lint0errors/37warnings; `default-android-resume.log`, exit0 |
| Standalone control JVM | PASS,171 tests/24 suites,0 failures/errors/skips; `control-jvm-resume.log`, exit0 |
| Default-disabled executable | PASS `default-disabled-resume.log` and `.json` |
| F1–F6 and actual Stream one-shot/retry hook | PASS with race detector, `fault-focused-race-resume.log` and `.json` |
| Full plain Go / full default race | PASS `go-full-resume.log`, `go-full-race-resume.log`, corresponding JSON receipts |
| Full diagnostic-tag race | PASS `diagnostic-full-race-resume.log` and `.json` |
| Explicit A–E and retained identity cases | PASS `ae-focused-resume.log`, exit0; both DATA48/58 × logical/carrier/frame/duplicate/late_message/late_rtp, unbound-write negative case, attempts0..8 identity cases and virtual-clock cases |
| Native packet race | PASS `native-packet-resume-r2.log`, exit0, retained pinned Xray fixture |
| Full Python, official fixtures | FAIL/STOP `python-full-r2-resume.log` and `.json`:905 passed,26 skipped,1 failed; remaining tests not run |
| Clean-scoped export/commit, hosted CI, successor JNI/gateway/APK | NOT COMPLETED / NOT STARTED |
| Offline signing, artifact verification, immutable pair manifest | NOT STARTED |

The F1–F6 and A–E source paths are byte-identical to the prior STOP snapshot;
these are fresh local synthetic tests, not old PASS receipts or physical results.
F4 still verifies a fresh recorder, not an Android process restart. These tests
do not establish runtime JNI/access denial, installed behavior or field recovery.
Full Python executes the preserved mixed working tree with official HEAD-pinned
fixtures; it is NOT proof of acceptance of a clean allowlisted export.

Generated ownerDiagnostic BuildConfig and merged manifest confirm package
`com.familyconnect.app.friends`, version`0.1.18-beta66`/code66, DEBUG=false and
the DUMP-protected receiver. Default Friends BuildConfig remains beta65/code65,
DEBUG=false; its merged manifest has no OwnerFaultReceiver. This is generated
metadata, NOT APK/package/JNI verification. No immutable version reservation made.

### New STOP, not another quota error

At04:52:10UTC the correctly provisioned Python run stopped at
`tests/test_native_authority_compat.py:105`,
`test_long_testing_window_preserves_native_expiry_checks`:

```text
assert response['expires_at'] == now + 3599
actual:   1791265925 = 1791262330 + 3595
expected: 1791265929 = 1791262330 + 3599
```

Log SHA256:
`3e29c0278ed32467f0072be4048bcb4dc5e467e558ee8da83493ae0c5950ffe1`.
This is an assertion failure, not disk quota, sandbox networking or TestClient stall.
The preserved, explicitly excluded dirty `control/friends/restricted.py` and
`restricted_admin.py` change expiry calculations to use clock-skew-adjusted issue
time. That is relevant source context, not a completed clean-baseline attribution.
No test weakening, unrelated code repair, retry-to-green, staging or freeze followed.

Setup-only failed attempts are retained separately, not reported as PASS:
`native-packet-resume.log` used the wrong module cwd (corrected in r2);
`python-full-resume.log` lacked FC_TEST_HTTP_SHA256 (835 passed/40 skipped before
KeyError); `python-fixtures-resume.log` rejected Go1.26.1 before tests.
The official fixture preparation then PASSED with Go1.26.0 in
`python-fixtures-r2-resume.log`. Python packages match both control and identity
lockfiles; `pip check` passed. Locally extracted nginx runs isolated test fixtures,
not a system service. No production operations were used to repair test setup.

### Preservation, remaining gates and rollback

`resume-before-docs.json` and `resume-final-closeout.json` bind source/log hashes,
test-suite totals and the preserved original inventory/closeout. Source-only
working-copy secret scan and preservation checks pass; Git index remains empty.
They are NOT a post-staging guard, frozen-source receipt or accepted pair manifest.
Only STATUS, PLAN and this existing report are updated outside ignored evidence.

No new accepted JNI/gateway/signed APK or artifact hashes exist. The candidate
remains draft ownerDiagnostic beta66/code66 with fault-control schema1 and required
signer`67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
Historical unsigned beta65 diagnostic artifacts are not promoted or substituted.
No installation, deployment, restart, credential renewal, READY, phone fault
arming, Telemost physical run, soak, Krasnodar contact, public beta65 replacement,
or default/catalog/invitation mutation. Test fixture binaries are not pair artifacts.

No runtime rollback is needed. Restored tools/caches and new receipts remain under
ignored task evidence; old inventory and logs are unchanged. Do not reset shared
files or delete previous evidence. Resolve the Python failure/source-scope attribution
without importing excluded control work, then complete required clean-scoped gates,
guarded freeze/commit, exact-source CI, JNI/gateway/unsigned APK builds, offline
accepted-signer verification and the commit/APK/signer/JNI/gateway/schema/CI pair
manifest. All deployment and physical gates stay closed until that succeeds.

## Initial STOP record (historical; resume above supersedes gate status)

## Source inventory and attribution

Actual repository root is `/home/joker/PycharmProjects/family_connect`; the session
cwd is its ignored `state-client-build/field65-export16` subdirectory.
Before source changes, HEAD and remote main both were
`8d046321039d0bd1e18ecc1af979ff90f591e029`. Inventory found36 tracked dirty and17
untracked files (53 total). No staged changes. No reset/clean/checkout/stash,
commit, branch, push or publication was performed.

Private local evidence directory:
`state-client-build/field65-export16/diag-source-freeze-1/`.
`source-inventory.json` records every pre-edit dirty/untracked path, status,
size, SHA256 and classification. It is an inventory, NOT a pair manifest.

Existing diagnostic allowlist (21 files, including its evidence report):

| Area | Exact paths |
| --- | --- |
| Attempt propagation / Reliable | `carrier/reliablestream/stream.go`, `carrier/reliablestream/head_loss_test.go` |
| Bounded metadata ring / projection | `carrier/sessiontrace/boundary.go`, `carrier/sessiontrace/boundary_test.go`, `carrier/sessiontrace/delivery.go`, `carrier/sessiontrace/trace.go` |
| RTP writer/receiver and assembly | `carrier/telemost/boundary.go`, `carrier/telemost/msg.go`, `carrier/telemost/rtp.go`, `carrier/telemost/session.go`, `carrier/telemost/signaling.go` |
| A–E and existing harness adaptation | `carrier/telemost/head_loss_test.go`, `carrier/telemost/local_process_test.go`, `carrier/telemost/performance_test.go`, `carrier/telemost/session_test.go` |
| Android privacy-safe projection | `clients/android/app/src/main/java/com/familyconnect/app/RestrictedDelivery.java`, `clients/android/app/src/main/java/com/familyconnect/app/RestrictedTrace.java`, `clients/android/app/src/test/java/com/familyconnect/app/RestrictedBoundaryTest.java` |
| Offline projection | `scripts/correlate_restricted.py`, `tests/test_restricted_boundaries.py` |
| Evidence | `docs/releases/2026-10-06-field65-data-hole-1.md` |

Mixed documentation: `docs/STATUS.md`, `docs/PLAN.md`, `docs/README.md`. Never stage
these whole files automatically: they contain unrelated historical work. Only
task hunks from STATUS/PLAN are newly authorized by this task; README untouched.

Unrelated and untouched: `control/friends/{readiness_receipts,restricted,restricted_admin}.py`,
`tests/test_friends_restricted.py`, `tests/test_restricted_test_window.py`,
`tests/test_restricted_clock_skew.py`, `deploy/friends/restricted/GATEWAY_RENEWAL.md`,
three root README files, client/getting-started guides, `docs/releases.md`, and
the other pre-existing release reports. Full exact path list is in inventory;
no unrelated file is included in the diagnostic allowlist.

New/extended draft implementation allowlist:

- `carrier/sessiontrace/fault_receipt.go`, `carrier/sessiontrace/fault_enabled.go`,
  `carrier/sessiontrace/fault_disabled.go`, `carrier/sessiontrace/fault_enabled_test.go`,
  `carrier/sessiontrace/fault_disabled_test.go`.
- `carrier/reliablestream/fault_runtime_test.go`; additional task hunks in the
  already listed `stream.go` and `sessiontrace/trace.go`.
- `pilot/android-restricted/native/fault.go`, `pilot/android-restricted/native/bridge.c`,
  `pilot/android-restricted/build.py`.
- `clients/android/app/build.gradle`,
  `clients/android/app/src/ownerDiagnostic/AndroidManifest.xml`,
  `clients/android/app/src/ownerDiagnostic/java/com/familyconnect/app/OwnerFaultReceiver.java`.
- New report here and only the new STATUS/PLAN sections.

## Draft operational contract

Schema1, fixed target `outbound_data_attempt0_after_established`, direction tx,
first eligible DATA only. Explicit-sequence selection is not implemented. A later
DATA is no longer eligible after consumption. The hook is in production Stream
transmit, not in a test fixture; it skips one endpoint send while retaining the
normal Reliable pending entry and unmodified retry/RTO/pacing. Attempt1+ proceeds.
ACK takes a separate branch. Telemost application/WebSocket heartbeats and media
keepalives bypass this hook; signaling is unchanged. Arming is refused until both
FAMILY_TLS and GATEWAY_SESSION are ESTABLISHED, excluding bootstrap establishment.
No wire/TLS/Mux/TUN changes.

Implementation requires Go tag `fc_owner_diagnostic`; without it, FaultCommand
always returns DISABLED and DropDiagnostic always returns false. This is a source
boundary, not yet a verified final default-build binary. Diagnostic recorder
starts DISARMED; explicit arm generates a random128-bit generation. A single
mutex protects arm/match/consume. Receipt includes schema, target, state, armed,
consumed, count, sequence and timestamps. No payload, destination or credential
field or user-controlled echoed string. Receipt survives trace-ring eviction.
One arm maximum per recorder/session (even explicit disarm cannot rearm it).
Match sets consumed=true/count1/armed=false/stateDISARMED. Close/failure disarms.
No persisted arm, environment flag or startup auto-arm; a new process/session
creates fresh disarmed state. F4 tests a fresh recorder, not an Android restart.

Android entry is only in `ownerDiagnostic` source set. Its exported receiver
requires platform `android.permission.DUMP`, excluding ordinary application
senders; ADB shell is the intended future operator. The receiver calls JNI only
for fixed arm/status/disarm commands and returns the bounded JSON receipt as an
ordered-broadcast result. Default Friends manifest/class has no receiver, and
default native code has a disabled stub. No phone command was executed.
JNI/manifest runtime behavior still needs Android acceptance; do not describe
these draft sources as an accepted physical operational control.

## Version, signing and provenance

Draft `ownerDiagnostic` variant: package inherited from Friends
`com.familyconnect.app.friends`, code66, name`0.1.18-beta66`, label
`OWNER DIAGNOSTIC ONLY`, debuggable=false, no debug signingConfig. Default remains
beta65/code65.66 is the next local code; remote main equals baseline and no beta66
tag was returned by the narrow tag check. This is NOT a complete remote release
inventory or immutable reservation. No APK manifest/ABI/BuildConfig was verified:
Gradle did not reach configuration/tasks successfully.

No new exact source commit, JNI, gateway or signed APK exists. New hashes and
signer verification: **NOT AVAILABLE**. No artifact signing attempted. Accepted
prior owner signer from DIAG-PAIR-PREP-1 is
`67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`;
this is the required compatibility anchor, not a signature on a new APK.
Historical unsigned beta65 diagnostic bytes must NOT be substituted as the pair.
Build flag/source_revision metadata was added, but clean Go vcs provenance,
packaging checks and immutable private pair manifest are unfinished.

## Checks and STOP

Local logs in the evidence directory:

| Gate | Result / receipt |
| --- | --- |
| Pre-change full Go | PASS `go-baseline.log` |
| Pre-change full default race | PASS `go-baseline-race.log` |
| F1–F6 plus Reliable, diagnostic tag/race | PASS `fault-tests.log` |
| Full diagnostic-tag race, including A–E and actual runtime hook/retry | PASS `diagnostic-full-race.log` |
| gofmt, working diff whitespace | Applied / PASS before STOP |
| Android unit/lint ownerDiagnostic | FAILED before tasks; `android-acceptance.log` |
| Post-change default-disabled executable regression | Added, NOT RUN |
| Post-change plain full Go / native packet / JVM / Python | NOT RUN |
| JNI / gateway / diagnostic APK / packaging | NOT BUILT or accepted |
| Exact-source hosted CI | NOT STARTED; no new run IDs |
| Signing / pair manifest | NOT STARTED |

Closeout-only checks after STOP: working-copy scoped secret scan PASS (no blocked
paths), all pre-existing unrelated file hashes unchanged, Git index unchanged,
`git diff --check` PASS. Local links for STATUS/PLAN/this report PASS (zero errors);
external links were enumerated, not fetched. `draft-closeout.json` captures source
and log hashes before this final documentation summary; `final-closeout.json`
captures the final documentation state. Neither file is an accepted pair manifest
or substitutes for the required post-staging index source guard.

The initial sandbox and Go command failed with `Disk quota exceeded` in /tmp.
Moving Go TMPDIR to the ignored evidence directory recovered both Go suites.
Android command used project-disk TMPDIR and java.io.tmpdir, but existing
GRADLE_USER_HOME still resides under `/tmp/fc-boot1-tools/gradle-home`.
Gradle failed creating its BuildLifecycleAwareVirtualFileSystem with
`java.io.IOException: Disk quota exceeded`, exit1, before unit/lint tasks.
No Android assertion failed or passed. Per explicit acceptance-failure STOP,
no further build/freeze/CI/signing attempted. No other users caches were deleted.

## Public state, rollback and remaining gates

Nothing installed, deployed or restarted. No credential renewal, fresh READY/ACK,
phone arming, Telemost physical session, soak, impairment, Krasnodar, WB/VK or
catalog/invitation/public upload. Public beta65 bytes/channels were not modified
by this task; no fresh remote artifact/runtime verification is claimed. Prior
deployment/signer receipts remain historical evidence only.

No runtime rollback needed. Local draft rollback must reverse only this task
diff and remove only its new source files, preserving the pre-edit inventory
and all DATA-HOLE/unrelated dirty work. Do not reset whole shared files.

Recommended next step: move/recreate isolated Gradle writable home/cache/scratch
on a filesystem with verified quota headroom, retaining existing logs, then
resume DIAG-SOURCE-FREEZE-1 gates. Review variant manifest and BuildConfig version,
ABI, JNI bridge, receipt projection/runtime access denial, and default binary.
Run all required gates against exact scoped source; stage only allowlisted
changes/hunks, run index source guard, commit, obtain exact-source CI artifacts,
offline sign with accepted signer and verify matching clean JNI/gateway metadata.
Only then create the immutable private pair manifest and consider PASS.
DIAG-PAIR-DEPLOY-1 is **NOT AUTHORIZED TO START ON THESE RESULTS**.
