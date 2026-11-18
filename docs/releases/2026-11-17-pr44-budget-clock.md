# 17 November — PR44 slow-open budget and panel clock

Source-only iteration; PR44 stays **DRAFT / NOT_DEPLOYED**, no merge. Remote entry
head `cff3e4664bce2adbbbc9303593c2d7c2abcef881`, main
`380da279588761c83e5433bec33a0511e4781133`. Other worktrees remain untouched.
The [prior receipt](https://github.com/Joker20380/family_connect/pull/44#issuecomment-6962872364)
retains cff3 results, including its panel failure and downstream skipped steps.
No earlier PASS qualifies this iteration. Final heads/runs/artifact identities go
in the PR receipt, not additional documentation-only CI-triggering commits.

## Budget reproduction and repair

Three deterministic cases invoke the actual register entrypoint for reconcile,
prepare and ordinary registration, real Gateway contexts and real file/flock.
After the actual Path.open(application.lock) returns, a controlled monotonic clock
advances9s. No sleeps or mocked serialization/fail-closed. On cff3 all three fail:
no timeout, body executes, three engine queries, ACK, operation elapsed0s. On exact
c086d131 all three pass: timeout, zero body calls/queries, no observation or ACK,
elapsed9s, protective stop, closed owned handle and reusable lock.

The minimal repair enters the same operation before open; an outer ExitStack owns
the file context until after operation-exit checks and error handling. It does not
reset time on acquire/body or acquire its own flock again. Error/context retained,
observation invalidated, stop requested, error attempt persisted, diagnostic receipt
persisted, resource released. Secondary cleanup errors do not replace the first
error; idempotent error handling does not repeat the protective stop.8/12/120s and
durable-before-ACK are unchanged, as are legacy/default and opt-in observations-v1.

101 focused cases pass after repair:27 serialization cases,66 observation-mode
cases and8 diagnostics cases. The prior nine real-thread/flock barriers still show
no competing queries, fresh observation, collector ok, WATCHDOG datagram or ACK
while registration diagnostic fsync is held; stop is already requested. Existing
open/acquire/context-exit/cleanup and successful-path cases remain enabled.
Legacy's two durable writes and six-cycle18-query/12→0-sync tests remain unchanged.
All182 transport/public-source tests pass; public-source guard4045 entries/0 blocked.
The transport repair was separately committed/pushed and remote-verified as
`98c692abae63f2ca5ae17718e16b477159713f80` before the panel change.

## Panel and final qualification

Separate logical test-only change: fixed aware UTC t0=2026-11-17T12:00:00Z for
test_wrong_clock_and_independent_age. Test-scoped monkeypatch of Django timezone.now
aligns observation and ingest; explicit presentation at t0 and t0+1s asserts exact
ages3600 and3601, with clock-skew label checked at both times. Production age formula,
TTL and transport monotonic time are untouched; no sleeps, tolerance or retries.
Locked panel environment passes36 targeted and320 full tests on a new loopback-only
task-owned PostgreSQL17 container, removed after completion. Browser request identity/
network-loss checks2 and external deployment-boundary check1 also pass locally.
Final-head CI must actually run
panel browser/deployment-boundary/build and all other applicable gates. Native
artifact must name the literal or synthetic source SHA, with tree comparison.

## Separate open delivery question

The main-era watch path releases application.lock after apply failure and calls
fail_closed externally. If asynchronous stop has not finished, a concurrent
registration can complete. This is not introduced by this repair and is not
silently redesigned here. The proven exclusion is scoped to **guarded registration
error handling**, not successful ACK exclusion during any fail-closed operation.
Resolve/qualify that concrete scenario before real systemd/package/deployment
acceptance, alongside cold-start/order/watchdog, coordinated core/entrypoint/
collector provenance, installed-unit verification and authority-preserving rollback.
No actual systemd termination, production routing or availability is claimed.
Historical storage latency cause remains UNKNOWN; RU is not FIXED. Physical iOS
remains deferred/NOT_RUN. Stop at repeat review; no next stage automatically.
