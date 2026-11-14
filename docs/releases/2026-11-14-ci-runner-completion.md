# CI-RUNNER-COMPLETION-1 — 14 November 2026

## Final result / integration

**COMPLETE for CI command completion; no production deployment.** Separate commits:
diagnostic60b3ff87acdd03f896df7e5c6ac613f0c35e2dc0 and correction
fd1d87941888f33773cab9e015a57358f0e67d39. Integration is the ordinary, history-preserving
[PR32](https://github.com/Joker20380/family_connect/pull/32) merge receipt. This report
update is documentation-only; executable qualification is on fd1d8794, not an assertion
that every later documentation SHA reran the suite. No mandatory CI protection bypass.
Original dirty checkout retained; source/pins/runtime and public beta125 unchanged.

Cause: after collection stdout became visible in21cfe5e5, megabyte parametrized
inventory lines reached the hosted console. The enclosing runner continued processing
that output long after our command, cleanup, wrapper and tee had all exited normally.
The bounded-console correction restores external completion. This establishes the
output-handling boundary, not a specific unprofiled internal GitHub runner matcher.

All requested final gates passed; **not a claim that all repository workflows are
green**. The unrelated Client builds appimagetool HTTP403 and an earlier readiness
timing failure are explicitly retained below. No tests/assertions were weakened.

## Entry / scope

Baseline main248b18818ff380f5e65564c5c05c61da23a97e04. Original checkout's dirty
documentation/untracked files preserved; clean existing5b0f worktree and agreed
branch used. No production install, new Android release, payment or message.

On ac3479bfa4f8b190826182fb9633d78a7fdfb993: phase043591863104/job132438099847
and Linux43591863123/job132438784552 timed out externally after25min. Each had
standard/root/snapshot314 rc0 and coverage PASS; later cargo/GTK/package skipped.
Actual failover/auth/offline/revocation132438099607 PASS separately. Retained phase0
artifact14115497288 SHA25638f336c896770969e03ba09d3fec44feeef063ad62eeaa8b294ac67332cacafa
contains4,750,501-byte full log ending with coverage PASS. This does not establish
cleanup, interpreter, wrapper or tee completion. No cause inferred from that line.

At15:07UTC source38e9f403 phase043606003930/tests132480665060 and Linux43606003884/
132480664898 were still IN_PROGRESS; actual failover132480665285 completed PASS,
including all four substantive scripts, not just the Docker build.

## Historical preparation checkpoint (before artifact arrival)

Monotonic lifecycle JSONL records inventory/context/coverage/cleanup/launcher and
wrapper return. Bash records both real pipeline exit codes, including nonzero.
Existing full log retained with tee. A bounded monitor takes one process/pipe-owner
snapshot10s after coverage or at15min, exits by1490s; outer25min timeout unchanged.
It reads only proc stat, pipe symlinks/access flags; never argv/env/file contents.
No test exclusions, source pin updates or dependency changes. Receipt coverage and
outer completion are separate. Local real-process tests check exit0/7 and safe
identification of pipe writers. Hosted evidence remains pending.

Diagnostic commit60b3ff87acdd03f896df7e5c6ac613f0c35e2dc0 was pushed/remote verified.
One diagnostic candidate, no manual reruns: phase043608832012/tests132489150366,
Linux43608832034/job132490566049. Its real failover132489150109 completed PASS,
including all four scripts. At16:09UTC outer pytest steps still pending. Live phase0
log still ends inside a megabyte inventory parameter ID; not at cleanup. Existing
raw artifact has18,627 lines, max1,048,685 bytes/line. The local identical4,750,501
byte log traverses the original tee pipeline in31ms, rc0 and byte-identical artifact.
History21cfe5e5 exposed collect-only stdout (previously discarded); all six CI chain
files are unchanged betweenac3479bf and38e9f403. This narrows the output-handling
mechanism, but final lifecycle/artifact evidence and bounded-output hosted result
are still required before causal/acceptance closure.

The candidate changes only console representation: bounded streaming relay after
tee emits a line-number/length/SHA reference for lines over2048 bytes. Full log bytes
remain in the artifact, including failed collection diagnostics. No truncation of
inventory, test input, assertions or failure artifact. Shell records command/tee/
console actual exit codes and propagates errors.31 local lifecycle/context/fixture
checks PASS: real process exit0/7 with1MiB output and exact full artifact, tee failure,
wrapper exit, inherited pipe vs parent completion and safe process evidence.
No timeout increase, new dependency, historical hash or test exclusion.

Newer observer source38e9f403 Linux43606003884/job132480664898 became CANCELLED
at15:44:33UTC, without artifact/downstream completion; it is not a completed PASS
or the originalac3479bf timeout. No manual cancel/rerun was issued. Its phase0 tests
were still running at15:58; failover132480665285 remains a completed PASS.

## Completed evidence: where time was lost

Raw diagnostic60b3ff87 phase043608832012/tests132489150366 eventually returned an
outer timeout. The hosted step lasted15:14:05–16:47:32UTC (93m27s despite its25min
limit). Artifact14122553861 proves the actual pipeline had already finished in
667.867542s, with command0/tee0, contexts5840/258/98 all0 and coverage PASS:

| Monotonic phase | Seconds |
| --- | ---: |
| wrapper child start | 295.588721 |
| inventory start / end | 295.711488 / 304.949108 |
| standard / root / snapshot end | 950.747423 / 960.569673 / 963.400565 |
| coverage end | 963.400976 |
| cleanup start / end | 963.401090 / 963.401778 |
| launcher end / wrapper child return / wrapper end | 963.401878 / 963.424755 / 963.424898 |
| pipeline end, command0 / tee0 | 963.456262 |

Cleanup cost0.689ms; wrapper and tee returned within56ms of coverage. Log/lifecycle
artifact timestamps are15:25UTC. The monitor correctly produced no process snapshot:
pipeline_end arrived before its10s post-coverage trigger, so no unfinished inner
process or pipe holder existed to diagnose. A regression separately exercises a
parent that exits7 while its child still holds the pipe, proving this distinction.
The actual diagnostic excludes TemporaryDirectory cleanup, Python shutdown, inherited
pipe/tee EOF as the stall in this run. It does not infer success from a PASS string.

Raw artifact maximum line1,048,685 bytes; earlier4,750,501-byte log has18,627 lines.
Local replay through original tee:31ms, rc0, exact bytes retained. Bounded streaming
relay:85ms, console1,240,476 bytes/max1104-byte line,28 replacements; raw artifact
unchanged. Only console lines over2048 bytes become length/line/SHA references.
The relay uses8192-byte reads/bounded buffering; all short diagnostics stay visible.
Full diagnostics remain in artifacts even on collection/child/tee failure.

Observer-source phase043606003930/tests132480665060 also finally FAILED externally:
artifact14121561572 shows5837/258/98 rc0, coverage PASS, no failed/error test IDs,
cargo skipped. Receipt source345e86694430c9474c6f36efd9d3330dc34af6cb is its PR
test-merge, not ac3479bf. Linux132480664898 cancellation remains separate, not PASS.

## Exact-source acceptance

PR test-mergefcaa3cdd1ef23c20afae7ca78b788b1a01385b44 and sourcefd1d8794 have the
identical tree5dd86423e1f318e056a2b0cc91ed1a0ce0677ff8 (verified by Git). No result
from the earlier source substitutes for these completed jobs:

| Run / job | Completed checks |
| --- | --- |
| phase043614512799 / tests132506529152 | Full-suite16:16:19–16:24:46UTC,507s, SUCCESS; cargo16:24:47–16:25:12 SUCCESS |
| Linux control43614512824 /132506529441 | Full-suite16:16:32–16:25:11UTC,519s, SUCCESS; GTK/render/interaction/recovery/TCP, paired packaging, extracted outside-checkout GUI/recovery/digest and artifact uploads SUCCESS |
| phase043614512799 / failover132506528873 | Completed17:04:44UTC; Docker build, provision, actual failover/auth/offline/revocation, upload and teardown SUCCESS |

Both outer receipts distinguish coverage_pass=true from completed=true; actual
command/tee/console return0. Contexts5847/258/98 each return0, no failure/error IDs.
Monotonic pipeline durations506.624s/519.047s; cleanup0.670ms/0.252ms.
Collection hashes: standard551e09708fe1b5de2098ecd123d854c9d9397c8d517974cffe235a237f23c9dc;
root672e7c7784d2c49ba472f2d4e325d9742a2fff36faf0053d98883ac003d95ae3;
snapshot314a463d77b0f38a1200ba7aecf3622d35eba7bfd71ad8df6f1ffd50275ad45e3fc.
Counter comparison of raw inventories: ac3479bf6164→fd1d8794 6203, **zero removals**,
only29 RU observer and10 CI regressions added. Root/snapshot inventory hashes unchanged.
All assertions, historical fixture/reference hashes, lockfiles, UID separation,
Python3.13/3.14 contexts, inventory equality and25min timeout retained.

Local31 lifecycle/context/fixture checks PASS, full collection6203 PASS, bash syntax
and whitespace checks PASS. Actual exits0/7, megabyte lines with byte-exact artifact,
tee failure, wrapper return, delayed EOF and safe pipe-owner metadata are covered.
Review: staged source/tests/workflows inspected for resource ownership, nonzero
propagation, bounded evidence, privacy and unchanged gates/pins; self-review, not an
independent-agent approval. No product-code change or production rollback required.

Downloaded archives verified against GitHub SHA256:

| Artifact | SHA256 |
| --- | --- |
| diagnostic14122553861 | 4cc38a52aee4ec59177e07e28655d3d1b220968dee938883a58e52a5ac86c835 |
| source38 phase014121561572 | 42a27786282dfda215210988482f80ef26112ef1657835fd37a9a21b4378b2d7 |
| final phase014122590020 | 3e318cf3b8cb93f0a8c4f2bc45476606e37b7e6296010976435badb0b6ead7d2 |
| final control14121594247 | c1ec297a73b5ac79221c71fe3682839c4807ed3c0412cb5d39dbc3f9ad7b5577 |
| final failover14123086670 | 994daa6bd293196a330b2dffb3078f31d24944a6b27afa57dba074b0e5fcf909 |
| paired packages14122011970 | d6bbe395ad7c16f06a6993ff5983b6d8a0122b688f640cd91080a75df48c0efc |
| conformance14121529960 | ad63da4e52e3e099d55f6db783fd40425674933cca8757e51630438d10714044 |

Preview896af6b7365e0a64 archive235cac5925d938ae3bf60655f28f330b7b18afb869bc7115be7d25a517c5c719:
all35 manifest file digests verified. Legacy0.2.11 archive
1d7a8de2650a91e82306a40bba5d18b9a71fc9659744647065f3e55f25496c47 retains exactly
six files. These are CI artifacts, not published/installed versions. Failover receipt:
16MiB hash match, one path switch, mutual TLS; offline16MiB hash match; unauthorized
peer rejected; revocation closed in1.116s with client exit1. No user data involved.
Private artifacts/receipts remain in `/mnt/data/fc-ci-runner-completion-20261114`.

## Separate failures, not concealed by acceptance

- Same-source push43614433337/failover132506280739 failed during Docker fullsuite:
  `tests/test_friends_http_evidence.py::test_readiness_bounded_and_no_retry_in_gate`,
  line141 expected2..4 attempts within150ms, observed1. Existing test/helper unchanged;
  standard had1 failure, root/snapshot PASS; wrapper correctly propagated1. Its actual
  failover scripts were SKIPPED, not passed. Artifact14121898396 SHA256
  dacc4cdc24ef15d97909602fa0063460926353eb3ced8ffc77be7be560096267 retained.
  Same test passes in both final hosted direct suites, local targeted run and the
  completed PR Docker gate. First-probe timing cause is unprofiled; no timeout/assertion
  change or blanket rerun. This failed attempt remains a timing-sensitive follow-up.
- Client builds43614512789/linux132506592194 failed16:17:27UTC in `Install appimagetool`:
  first download from GitHub AppImage/appimagetool asset715388534 returned HTTP403,
  curl22. Linux desktop tests/GTK/recovery preceding it passed; AppImage/DEB and later
  extracted checks in that workflow were skipped. The requested Linux control package
  gate above did complete. No evidence establishes why GitHub returned403; do not label
  it rate limiting without headers. Client workflow/pins unchanged, no blind rerun.
  Windows/compat/Android jobs passed, release skipped; no new APK release requested.

Both requested workflows (phase0 and Linux control) completed SUCCESS on final
executable source. Windows control/readiness also passed. Repository-wide CI is not
universally green; external AppImage download and timing-sensitive readiness remain
separate, unselected follow-ups, not hidden mandatory checks for a release.

## RU read-only handoff

One entry extraction15:07UTC using existing refined helper and NEW label
`ci-entry-20261114-1506`. Unit active/exited, MainPID0, Resultsuccess. Final reason
sample_cost_limit after1171.44765s; no gateway failure/lost indications; tracer rc0,
empty error file.538 cycles/2152 fsync/1076 rename; not causal proof. No restart,
extension or change to original15Nov14:19:16UTC hard ceiling.

Private directory:
`/mnt/data/fc-ru-persistence-pressure-20261114/extracted-refined-ci-entry-20261114-1506`.
start SHA2562680c3a4bbd32d59ee39df08d58b83f416e63c92cdc58af7d5374f1006f36ff5;
final SHA256911a8f16e9a5ac2cdd7cc1d19cf9e1f0b366b53dc56941dc39505e2ab4e7e660;
empty errors SHA256e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855.
No slow receipt exists in this window. RU stays CAUSE_OPEN, final analysis separate.
No scheduled collection/analysis job exists. Next RU action: analyze this final
window against its retained start/first-window evidence; no need to wait for15Nov.
If another readback is needed, use a NEW label, e.g.:
`python3 /mnt/data/fc-ru-persistence-pressure-20261114/collect_refined_result.py final-review-20261115`.
Original handoff checkpoint remains15Nov after15:20Brussels; never restart observer.

Exit extraction with NEW label `ci-exit-20261114-1713` is retained separately under
`/mnt/data/fc-ru-persistence-pressure-20261114/extracted-refined-ci-exit-20261114-1713`.
Unit remains active/exited/MainPID0/Resultsuccess; same sample_cost_limit stop,
elapsed1171.44765s, tracer rc0, no failure/lost indications. All three SHA256 above
match the entry extraction; no slow receipt appeared. This is observer readback,
not a fresh VPN reachability test or diagnosis of RU's historical stops. Original
deadline/limits unchanged. Next RU action can analyze these final files now; if a
further readback is needed at15Nov after15:20Brussels, the exact command above uses
a fresh label/directory. No automatic extraction or analysis is scheduled.
