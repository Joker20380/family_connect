# ANDROID-HARNESS-ACCEPTANCE-1 — PASS

## Final expanded-scope result — PASS

Replacement validation SHA `986323ecef112fcc421a22263e6fbfc9d6cf1922`; parent
`6d1bddaa886d7320faa7b8ea978a55167c5c0981`; new CI-only tag `diag-owner-beta69-ci2`.
Only that tag was pushed, no branch or publication tag. Existing tags immutable.
Six-file review is retained in `review-six-files.json`, exact patch in
`six-file.patch`, committed file hashes in `source-hashes.json`, clean source bundle
in `validation-source.bundle` under the session's `android-harness-acceptance-1/resume2/`.
Main checkout's unrelated changes preserved; source runtime and beta69/code69
unchanged. Friends build variant remains beta65/code65; public/catalog/invitation
versions are unchanged. APK/native rebuilds carry new source
provenance; this is not a claim of byte identity with an older built APK.

### Exact-SHA local gates

| Gate | Result |
| --- | --- |
| Exact six-file scope / no production dependencies / diff check | PASS |
| Fresh source-bound fixtures / complete Python3.13.16 + Go1.26.0 | 1809 passed,26 skipped,2 warnings;79 fixture hashes verified |
| Both Python lockfiles | 26 unique installed pins verified |
| Full Go1.26.1 default / diagnostic race / callback matrices | PASS |
| Deterministic mux single-core isolated/package/suite | 50/20/10 PASS |
| Callback ACK write-completion / private token / hop-local RTP | PASS, unchanged |
| Public golden / privacy / isolation / source guards | PASS;43 source guards |
| JVM diagnostics and primary/self-suppression cleanup | 7/7 PASS |
| Exact-method forced ENETUNREACH network selection | 100 corrected cases PASS; original negative controls retained |
| Callback readiness / exact VPN binding / dual-stack echoes | 100 cases per simulation PASS; full emulator also PASS |
| Owner/Friends native metadata, ELF/exports/alignment | PASS; normal native all4 ABIs built |
| Owner/Friends unit tests and lint | 258 each; zero failures/errors/skips/lint errors |
| Unsigned package and embedded native verification | PASS |
| Production debug/owner/Friends DEX excludes test helpers/classes | PASS |
| Standalone JVM, host cgo/default/race, routing, host TCP, AWG | PASS |
| Emulator TCP, AWG, Auto lifecycle and Android cleanup | PASS;48 reported,28 executed,20 existing assumption skips;7 cleanup cases |
| Local synthetic HTTP fixture | 30 completed HTTP requests,38 DNS observations |
| Post-instrumentation process restart / control/RNS conformance | PASS;30 configurations,15 ACKs,32 structure refusals,4 authenticated-cipher refusals |
| Beta67/beta68 sealed artifacts | Hash-preserved |

Local emulator used exact committed test sources and freshly source-bound native
payloads. Every device operation selected emulator-5560; connected physical device
untouched. Emulator stopped and peer contexts/processes closed. No failed lifecycle
iteration or workflow was retried. Pre-test wrapper/sandbox/preflight receipts remain
in the evidence directory. Generated evidence was hash-verified and archived out of
the source tree before the clean-tree CI selection gate; no source change was needed.

### Complete hosted acceptance

- [Android diagnostic acceptance](https://github.com/Joker20380/family_connect/actions/runs/37635226335): complete workflow PASS,
  emulator lifecycle, runtime summary, control/RNS conformance and artifact steps PASS.
- [Client builds](https://github.com/Joker20380/family_connect/actions/runs/37635226241): complete workflow PASS, including full Android
  lifecycle/Friends acceptance, post-instrumentation control check, restricted native/
  gateway build, unsigned ARM64 package, exact release-payload verification and uploads.
- [Owner diagnostic pair acceptance](https://github.com/Joker20380/family_connect/actions/runs/37635226230): complete workflow PASS,
  source-bound native, unsigned packages, matching gateway and payload verification.
- Retained full17-workflow gate PASS, all attempt1, exact replacement SHA.
- Client builds `release` and TCP pilot `release`/`setup_release` explicitly SKIPPED;
  no distribution workflow. Job/step snapshots and artifact IDs/digests retained.

Hosted artifact verification here refers to the successful workflow verification and
upload steps plus artifact API metadata; no offline signing or deployment is implied.
Historical TCP remains NON_REPRODUCED_HISTORICAL_FAILURE, not reopened. No new TCP
failure reproduced; beta69 remains unimplicated. No beta70 or version/code change.
No release signing, owner/physical install, gateway deployment, arming, physical
Telemost experiment or Krasnodar test. No public/invitation version changed, no new
rollout/rollback pair promoted; existing deployed versions and rollback paths remain.
RTP-IDENTITY-FREEZE-1 may resume from the accepted replacement SHA. Its later
artifact sealing/signing/deployment gates are separate and were not performed here.

**Exactly one recommended next step:** resume RTP-IDENTITY-FREEZE-1 from the accepted
replacement SHA, carrying forward these complete local and hosted receipts.


## Historical expanded-scope checkpoint — superseded by final PASS

User authorized all six existing androidTest files. Replacement validation SHA:
986323ecef112fcc421a22263e6fbfc9d6cf1922, parent6d1bddaa886d7320faa7b8ea978a55167c5c0981.
Commit adds exactly six files' corrections (219 insertions/11 deletions); complete
candidate is the previous accepted beta69 + deterministic Go mux test + these six.
No other main-checkout changes imported. Detached clean source and Git bundle
retained at android-harness-acceptance-1/resume2/validation-source.bundle.

Six-file review/source hashes confirm androidTest-only dependencies, unchanged
assertions/transport timeouts, bounded diagnostics and primary/self-suppression
cleanup protection. Full source-bound Python1809 passed/26 skipped, Go default
and diagnostic race, callback matrices, mux50/20/10,43 source guards,7 JVM cleanup
regressions, exact-method network/readiness/binding simulations, native metadata/
ELF/exports, owner/Friends258 unit tests each, lint and packaging PASS.
Historical replay is not reopened. No production/version/protocol/RTP/Reliable/ACK
change; beta69/code69 remains unimplicated. Full48-case emulator acceptance is
running; complete hosted acceptance remains pending and no PASS is claimed yet.

Infrastructure receipts retained: first default Go attempt denied loopback socket
creation inside sandbox; unchanged exact-SHA suite passed outside sandbox. Missing
/tmp toolchains restored with pinned Go/NDK and original Python3.13.16 checksum,
both lockfiles verified. A wrapper path-resolution error occurred before readiness
test execution and was corrected; source/test predicates unchanged. Emulator
preflight initially stopped before device actions because another device was
connected. Verified AGP8.9.2 ANDROID_SERIAL filtering now restricts tests and all
ADB actions to new disposable emulator-5560; other devices remain untouched.

Conditional CI runner is authorized to push only new diag-owner-beta69-ci2 after
all local gates pass. Release/distribution condition checks remain mandatory.
No signing, owner installation, gateway deploy, arming or physical experiment.
No deployment or new rollback path; old deployed versions/rollback paths unchanged.
Previous sections below remain historical evidence, not the current scope decision.

## Historical scope review after TCP-LOW-PERTURBATION-REPLAY-1 PASS

This section supersedes the historical blocking disposition below, not its evidence.
Historical TCP: NON_REPRODUCED_HISTORICAL_FAILURE, no longer independently blocking.
No replay requested or performed and no new TCP failure observed in this review.

The current requested three-file correction is NOT self-contained:

- AutoRuntimeTest calls TcpTrafficDiagnostics.cleanup.
- TcpRuntimeTest calls TcpTrafficDiagnostics and TcpNetworkEvidence.
- Both helper files are untracked in the main checkout and absent from committed
  validation6d1bddaa886d7320faa7b8ea978a55167c5c0981.
- TcpTrafficDiagnosticsTest is also untracked; it contains the seven accepted
  cleanup/diagnostic regressions, not part of the requested three-file allowlist.

Committing only the three named files would leave unresolved Java references.
No failing build was needed or claimed to establish this source dependency.
Adding those files would exceed the explicit scope; relocating their code into
the three files would alter rather than merely review the accepted correction.
Neither was done without scope clarification. Historical clean candidate retained.

Review: Auto selects another eligible non-VPN Internet network after IOException,
preserving control-response assertions. AWG/WG readiness uses a registered VPN
callback, expected source address and dual-stack default routes, a bounded15s wait,
callback unregistration and explicit socket binding. Existing UDP predicates and
timeouts remain. Auto/TCP use primary-preserving cleanup, including activity finish;
the helper avoids self/duplicate suppression. Grouped stop/profile-clear actions
remain grouped, so this is not a claim that each clear runs after stop throws.
TCP retains HTTP200/body-suffix predicates, six requests per traffic invocation,
10s connect/15s read limits, original source binding and no HTTP retry. Added
diagnostics cap response8192 bytes, preview80 chars, receipt3800 chars, network
inventory/probes6 with1s connect limits. Current rich variant includes pre-request
snapshots and success receipts; it is not the minimal replay variant. No assertion
weakening or broad timeout increase found. Helper implementation is required for
these findings; a three-file-only tree cannot provide them.

No production/runtime/protocol/RTP identity/Reliable/ACK/transport or version
change made. Accepted Go mux fixture hash remains
1eae8164d4e59523b311ef82c4ca2ef354f8db8f80153ebddff5d4e7e0a04480.
Owner candidate beta69/code69 remains unchanged and unimplicated; Friends/default
remains65. Working-tree git diff --check PASS. No replacement SHA was created;
therefore fresh exact-SHA source/JVM/Android/lifecycle/readiness/ENETUNREACH/
isolation/full-local gates are NOT RUN, not inherited from prior receipts.

No new CI-only tag or hosted workflow started. Android diagnostic and Client
builds acceptance, post-instrumentation control/conformance and payload gates
remain NOT RUN for a replacement. Historical runs37597746736/37597746771 failed;
historical ci1 release jobs were skipped. No current-run skip verification is
claimed. No signing, owner installation, gateway deployment, arming, Telemost
physical experiment or Krasnodar test. No new rollout/rollback path; existing
deployed versions and rollback paths are unchanged. Freeze may not resume yet.

Receipt: state-client-build/field65-export16/android-harness-acceptance-1/
resume-scope-blocker.json. Prior receipts remain intact.

**One recommended next step:** authorize the two existing test-only helper files
and TcpTrafficDiagnosticsTest alongside the three reviewed instrumentation files.

## Historical attempt — FAIL (superseded disposition)

## Mandatory precommit STOP

No replacement validation SHA was created. Original candidate remains
`6d1bddaa886d7320faa7b8ea978a55167c5c0981`; beta69/code69 unchanged.
An isolated clean clone retains that HEAD, without the uncommitted overlay.
The previously reviewed overlay and its receipts remain in the earlier investigation
directory and main checkout. No new test/runtime source edits, commits, tags,
pushes, hosted runs, signing, release changes, owner installation, gateway deployment,
arming, physical Telemost experiment or Krasnodar test occurred.

## Three-file review

The existing overlay relative to6d1bddaa is exactly:
1. `clients/android/app/src/androidTest/java/com/familyconnect/app/AutoRuntimeTest.java`
2. `clients/android/app/src/androidTest/java/com/familyconnect/app/AwgRuntimeTest.java`
3. `clients/android/app/src/androidTest/java/com/familyconnect/app/TcpRuntimeTest.java`

Diff38 insertions/5 deletions; no production, version, wire/protocol, RTP identity,
Reliable/ACK or transport change. Existing data assertions/retry counts and transport
timeouts are unchanged. The bounded15s VPN callback wait is test synchronization,
not a broad timeout increase. Diff whitespace check passes. Nothing from the dirty
root checkout was imported into the clean clone.

## TCP rerun before any source change

Used the already-validated `final-test.apk`, not a new TCP modification. Dedicated
API35 emulator-5560 only, existing exact-SHA CI debug runtime payload locally debug
re-signed for instrumentation. No physical phone actions.

Runtime SHA256:
`7bf76976ada6cb35e7178c23892c88688a8ab956a755a3e8e43a8f1be45e26c1`.
Instrumentation SHA256:
`4822f50595dc22ff6f41d084032d7373c19e7648048377c82f481e9cf759930f`.
All195 non-META-INF runtime entries were previously verified equal to the original
CI artifact; no fresh beta69 runtime binary was substituted.

| Repeat | Result | Duration | Fixture HTTP / DNS |
| --- | --- | --- | --- |
| acceptance-tcp-before-1 | PASS | 48.145s | 18 / 56 |
| acceptance-tcp-before-2 | PASS | 46.352s | 18 / 42 |
| acceptance-tcp-before-3 | FAIL, preserved primary | 32.046s | 12 / 24 |

The orchestration asserted each instrumentation result and stopped immediately
after repeat3 failed. No fourth run or retry was attempted.

Preserved initiating exception:

```text
java.lang.AssertionError
    at org.junit.Assert.fail(Assert.java:87)
    at org.junit.Assert.assertTrue(Assert.java:42)
    at org.junit.Assert.assertTrue(Assert.java:53)
    at com.familyconnect.app.TcpRuntimeTest.traffic(TcpRuntimeTest.java:26)
    at com.familyconnect.app.TcpRuntimeTest.realityDataSwitchCancelRevokeAndProtectedStorage(TcpRuntimeTest.java:43)
```

Guest log13:10:24.516 records the final TCP transition after AWG;
13:10:24.783 records test failure. The source line contains both
`assertTrue(reply.contains(" 200 "))` and `assertTrue(reply.endsWith(nonce))`.
There is no message, failed-predicate identifier or response body in the receipt.
Do not infer an empty reply, network failure, protocol bug or runtime regression
from that ambiguous line. This is not the earlier ENETUNREACH exception.
Cleanup did not replace this particular primary; no suppressed exception is reported.

The earlier `corrected-full-1` failure, masked by profile-clear cleanup, is retained
and hashed again. A TCP failure has recurred, but identical causality with that old
masked failure is NOT established. Per the requested policy it is now blocking,
not historical/non-blocking. No speculative fix was applied.

## Primary-exception regression review

`review_cleanup.py` extracts the actual Auto/TCP catch/finally tails and compiles
them with small JVM cleanup doubles. It injects an initiating IOException, failing
cleanup, and an optional failing activity-finish callback. This is a harness-only
regression review, not an explanation of the TCP traffic failure.

- TCP stop failure alone: original initiating exception preserved.
- Auto and TCP activity-finish failure: primary is replaced by the finish exception.
- Auto reset and stop throwing the same exception object: self-suppression raises
  IllegalArgumentException and masks the primary even without a finish error.

Therefore unconditional primary preservation is **not accepted**. The checks and
results are retained. They are not silently weakened, and no correction was made
after the independent mandatory TCP STOP. Awg's remaining cleanup paths were not
fully acceptance-tested after the STOP.

## Gates and source state

| Gate | Result |
| --- | --- |
| Exact existing three-file scope / runtime isolation / whitespace | PASS |
| Primary preservation for observed TCP failure | PASS |
| Universal cleanup primary-preservation regression | FAIL |
| Required fresh TCP-only repeated acceptance | FAIL,2/3 passed |
| Replacement commit and exact-SHA affected acceptance | NOT REACHED |
| New CI-only tag | NOT CREATED |
| Android diagnostic complete hosted workflow | NOT RUN |
| Client builds complete hosted workflow | NOT RUN |
| Hosted post-instrumentation conformance/artifacts | NOT RUN |
| New publication/release jobs skipped | N/A: no new workflow/jobs exist |
| RTP-IDENTITY-FREEZE-1 may resume | NO |

Prior source guards, replay, local instrumentation and original hosted receipts
remain historical; none is relabeled as acceptance on a nonexistent replacement SHA.
Both original hosted failures remain unchanged. Beta69 itself is still not proven
responsible: no runtime regression has been demonstrated or ruled out by this STOP.
No full release/local gates were launched after the failed prerequisite.

## Evidence, cleanup and next step

New review/STOP evidence:
`state-client-build/field65-export16/android-harness-acceptance-1/`.
Includes `tcp-before.log`, `cleanup-review.json`, `review_cleanup.py`, source clone,
last-run synthetic peer log/result, and hashes of old/new TCP receipts.
Complete per-run instrumentation/logcat/results remain under
`state-client-build/field65-export16/android-emulator-network-1/acceptance-tcp-before-{1,2,3}/`.

The runner stopped the pilot and synthetic peer processes after each run. Final
fixture ports51820/51821/51900/51902 show no listeners; emulator-5560 was stopped.
Final guest `ip link show` returned Permission denied; no positive final interface
inventory is claimed. No host routes or physical-device state were changed.
No new deployment exists to roll back; previous validation and beta67/beta68
release/deployment state remain untouched. Existing three-file overlay is unchanged.

**One recommended next step:** investigate the preserved TCP primary failure with
bounded response/assertion diagnostics, without changing runtime or blindly rerunning
acceptance, before revising the harness or creating the replacement SHA.
