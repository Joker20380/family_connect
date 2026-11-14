# CI-RUNNER-COMPLETION-1 — 14 November 2026

## Entry / scope

Baseline main248b18818ff380f5e65564c5c05c61da23a97e04. Original checkout's dirty
documentation/untracked files preserved; clean existing5b0f worktree and agreed
branch used. No production install, Android build, payment or message.

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

## Diagnostic candidate (not a fix / not acceptance)

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
