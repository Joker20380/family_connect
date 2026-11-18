# 17 November — PR44 fail-closed serialization P1

Source-only repair; **NOT_DEPLOYED, RU NOT_FIXED**. Stop at repeat review PR44;
merge, production access/deployment and physical iOS are not authorized here.
Entry remote main `380da279588761c83e5433bec33a0511e4781133`, PR44 head
`c086d131e7d4f7c3d60aa536cab5a841906f0e92`; existing isolated candidate worktree
reused, other dirty worktrees preserved.

The [previous final receipt](https://github.com/Joker20380/family_connect/pull/44#issuecomment-6960939690)
and its13 successful workflows remain historical evidence for c086, not acceptance
of the repair. No old success is inherited, gate removed or unchanged failure rerun.
Final new head, push/PR runs, artifact identity and author self-review go in a new
PR receipt rather than documentation-only commits to trigger additional CI.

## Reproduction before repair

`tests/test_transport_failure_serialization.py` uses the real entrypoint, synthetic
SQLite and signed decisions, separate Gateway instances, real flock and threads,
actual collector, actual watch loop and notify datagrams to an owned Unix socket.
Engine responses and storage faults are injected; this is not a production or
systemd test. A barrier holds the registration thread inside the first failure
receipt's actual fsync boundary. A competing watcher is held at its first real
lock contention or after its actual WATCHDOG datagram, permitting observation of
the intermediate state before either participant cleans up. No sleep-based race.

The unchanged c086 source in a detached worktree fails all nine cases: mandatory
attempt-file fsync EIO, elapsed-budget failure, and final operation-exit deadline,
each for reconcile/prepare/ordinary register. While the receipt is blocked:
application.lock is available, the watcher executes three queries and publishes
fresh applied, collector returns ok and WATCHDOG is actually emitted. For the
ordinary register context-exit case an ACK can also precede the failing exit.
Elapsed time is injected by advancing the operation's age nine seconds, keeping
the configured eight-second budget; this does not simulate cancellable kernel I/O.

## Repair and checks

Only opt-in registration requests guarded serialization. The application handle
remains owned through the final operation deadline check and fail-closed reaction.
Original error/context is captured; observation is invalidated; stop is requested;
error attempt is written; the first diagnostic receipt is persisted; then the lock
is released. Stop/error-receipt/descriptor-close errors do not replace the primary
failure; outer handling does not repeat stops for the same exception. No recursive
flock acquisition. Open/acquisition errors fail without entering the operation
body, and a contending participant's descriptor is never closed.

24 focused regressions and179 transport/public-source tests pass after repair,
using the existing control/device-identity locked environment. During the same nine held barriers:
lock busy, zero competing queries, no new observation, collector unavailable,
no WATCHDOG datagram, no ACK; protective stop already requested once. Threads join,
operation context resets and the application lock can be acquired after cleanup.
Additional cases cover real lock contention/deadline, open/flock failure, original
error retained across stop/error-write/context-close faults and all three successful
ACK paths after final exit validation with no spurious stop.

The legacy two-durable-write assertion and six-cycle baseline/candidate comparison
remain required unchanged:18 engine queries each,12→0 authoritative writes/file
fsync/directory fsync,0→6 observations and6/6 correct collector readbacks after
warm-up. Targeted/full transport and native CI provide the new source's evidence;
new exact-head CI is pending at this source checkpoint. Local reproduction log
SHA256 `3d8238098f8a9b62be9de604b562eae7d6fb5df3713ebd34b676b82d8e2e3f90`;
179-test log SHA256 `11b3287eb4678c8c51faa929b7ca6c914de273afe803ffa36cc23788141a912a`.
Raw synthetic fault logs remain outside Git.

## Separate remaining gate

No claim that stop requests have actually terminated engines on a real systemd
node, or that Python can cancel an uninterruptible fsync. The existing8/12/120s,
leases, denial, expiry, revoke, preparation, bindings and durable-before-ACK stay
unchanged. Real systemd cold-start/order/watchdog, coordinated pinned archive +
entrypoint + collector packaging, installed/source-unit verification and
authority-preserving deployment/readback/rollback require a separately authorized
stage. Historical storage latency cause remains UNKNOWN. Old pressure observer is
not a candidate freshness monitor; no new production observer is started.
