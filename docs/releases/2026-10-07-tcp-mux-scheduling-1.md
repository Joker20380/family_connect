# TCP-MUX-SCHEDULING-1 — PASS

## Classification and scope

Primary classification: **SINGLE_CORE_SENSITIVITY**, a **pre-existing TEST_FLAKE**.
No evidence of a beta69 runtime regression. No production code was changed.
This is offline investigation/test correction, not release acceptance or rollout.

Unmodified comparison sources:

- beta68: `1abaa3a8a9ba8ad9fa2a71c126620175b713c321`.
- beta69 validation: `763c3b326c5710c39a7cbd681f4160d9ce8fb1f8`.

Both isolated checkouts remain clean. Their tcpforward trees, Go module/lock files
and mux implementation/tests are identical. The ten-file beta69 delta changes
only diagnostic-tagged `sessiontrace/correlation.go` in production Go code; that
file is excluded from this default build. Other changes are tests in other
packages, Android version metadata and documentation. None changes this default
mux path, timers, channels, buffering, cleanup or goroutine scheduling.
The mux test predates beta68 (introduced at `a22742a9d389d33e3e88d14001b47942e5ef7418`).

## Exact failure and causal evidence

Package: `github.com/Joker20380/family_connect/carrier/tcpforward`.
Test: `TestMuxSlowConsumerAndInteractive`, original `mux_test.go:212`.
Assertion: after `slow.Reset()`, `<-written` must be non-nil; actual result nil,
reported as `blocked writer did not fail`. Repeated failures took0.03–0.10s,
not the3s buffer-fill timeout,1s interactive limit or15s fixture deadline.

The test launches a goroutine writing4MiB to a loopback TCP echo target. It polls
the reverse receive buffer until65536bytes, samples the buffered result channel
once to check noncompletion, then completes a separate interactive stream before
resetting the slow stream. The loopback target, forwarding readers/writers and
mux send/receive loops run concurrently. Forward credit is replenished when the
server reads its mux buffer, independently of the client's reverse receive window.
Kernel TCP buffers can therefore accept the whole finite write before Reset.

Test-only observation overlays retained before-reset stats. Every observed nil
write result (beta69:29; beta68:40) had already accepted exactly4194304bytes.
Example: State=open, Sent=4194304, ReceiveBuffered=65536, context=nil immediately
before Reset; State=reset afterwards. `Write` legitimately returns nil once its
payload is fully queued. Reset cannot retroactively fail a completed write.
The earlier noncompletion sample is not synchronization with the later reset.

The failure occurs after explicit Reset and BEFORE testing cleanup. Fixture
WaitGroup cleanup waits after closing listener/connections; there is no evidence
of WaitGroup misuse, cleanup/assertion overlap or context expiry in this failure.
Race instrumentation changes timing; it detects no data race in the tested runs.

## Unchanged-source reproduction matrix

Go1.26.1; serial compilation `-p=1`, no test cache (`-count` supplied).
Detected/default runtime:12 CPUs, GOMAXPROCS12. Counts below are selected-test
**pass/fail**, including occurrences within package/mux repetitions.

| Source | GOMAXPROCS | Isolated50 | Package20 | Mux suite10 |
| --- | ---: | ---: | ---: | ---: |
| beta69 | 1 | 21/29 | 12/8 | 7/3 |
| beta69 | 2 | 50/0 | 20/0 | 10/0 |
| beta69 | default12 | 50/0 | 20/0 | 10/0 |
| beta68 | 1 | 30/20 | 16/4 | 8/2 |
| beta68 | 2 | 50/0 | 20/0 | 10/0 |
| beta68 | default12 | 50/0 | 20/0 | 10/0 |

All66 selected failures were the exact same reset assertion. No failure occurred
in the earlier buffer-bound, early noncompletion or interactive-starvation checks.
Original isolated race50 and package race1 passed on EACH source atCPU1/default12.
Unchanged beta69 full default suite passed once atCPU1 and once atdefault12;
these individual green runs do not erase the demonstrated flake.

### Host-suspend exception retained, not hidden

The first beta68/default package20 batch additionally failed
`TestMuxAuthenticatedLossReorderDuplicate`, `mux_integration_test.go:43`,
`TCP forwarding reset`. System journal records suspend at2026-10-06T22:32:12Z
and resume2026-10-07T08:04:15Z; failure followed at08:04:16Z.
Batch wall time34526.5s versus Go elapsed210.1s confirms the interruption.
This is separate from the selected assertion and not evidence of a beta69 change.
The untouched baseline package20 repeated after resume passed completely194.6s.
The interrupted receipt and journal remain preserved; no assertion was relaxed.

## Narrow correction and acceptance

Only `carrier/tcpforward/mux_test.go` changes (20 insertions,1 deletion): the
first/slow target uses the existing `pipeSocket` helper wrapping unbuffered
`net.Pipe`, with an echo goroutine, explicit close/join cleanup and atomic dial
selection. The interactive sibling still uses the real loopback TCP target.
Without arbitrary kernel buffering, the bounded forward/reverse windows cannot
absorb4MiB while the consumer is stopped. The writer remains blocked until Reset.
All original assertions, payload size, deadlines and timeouts remain unchanged.
No production mux, transport, Reliable callback or RTP identity changes.

Tests use explicit Go overlays against pristine source checkouts, not the unrelated
dirty root tree. The final working-tree test is byte-identical to the tested overlay:
SHA256 `1eae8164d4e59523b311ef82c4ca2ef354f8db8f80153ebddff5d4e7e0a04480`.

- Corrected beta69 at EACH CPU1/2/default12: isolated50/50, package20/20,
  mux suite10/10; isolated race50/50 and full-package race PASS.
- Same correction over beta68 at EACH CPU1/2/default12: isolated50/50,
  isolated race50/50, full-package race PASS.
- Corrected beta69 full default `go test -count=1 -p=1 ./...`: PASS atCPU1
  anddefault12, including default/public sessiontrace tests.
- gofmt and `git diff --check`: PASS.

## Resource checks and preservation

During576 samples, minimum free storage: root9398456320bytes, tmp6118387712bytes;
minimum available memory6461584KiB; maximum tcpforward test FDs70 against soft
limit1024. Process limit125098; no exhaustion errors. Initial inode use11%/19%.
Load1 ranged1.24–6.78 on12 CPUs. Initial swap usage was high but memory remained
available; there is no evidence connecting the selected assertion to disk/tmp,
FD/process limits or memory exhaustion. The host suspend is separately documented.

Beta67 and beta68 sealed files and manifests rehashed unchanged. Existing reports,
failed receipts, rollback artifacts and unrelated dirty work remain preserved.
No commits, versions, tags, pushes, release artifacts, signing, installs, deployments,
arming, physical experiments or transport tuning occurred. Runtime rollback is
unnecessary because runtime did not change.

## Freeze disposition and receipts

`RTP-IDENTITY-FREEZE-1` remains PARTIAL. Existing validation SHA is unchanged but
does NOT contain this test fix. Do not promote that SHA using overlay acceptance.
Prior1809-pass Python receipt remains valid only for its original SHA.

Next: prepare a new scoped validation SHA containing the accepted beta69 delta
plus this test-only correction, then repeat exact-SHA acceptance before freeze.

Local receipts: `state-client-build/field65-export16/tcp-mux-scheduling-1/`:
`matrix.json`, `followup.json`, per-runJSONL, observation and deterministic overlays,
`test-only.patch`, `host-suspend.txt`, `beta68-default-package-post-suspend.json`,
`resources.jsonl`, `closeout.json`, `evidence-sha256.json`.
