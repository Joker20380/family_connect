# 25 November 2026 — HA-02 support stabilization, not handoff acceptance

## Scope and starting point

Remote feature `595acebe72bc486ec9661bb68bc493a09e9863f8` and main
`17d3b32ab7384bdeb680f3a389408f25b2e78559` matched the owner checkpoint; both worktrees
were clean. Work remains on `feature/device-technical-metadata-20261115`. No working
support replacement, mailbox opening, capture permission, HA-03 cutover or release is claimed.
The selected result is the **combined OWNER ↔ NL1 handoff/reclosure/recovery**, not a helper PASS.

## WORKERS_REMAIN: evidence and limits

The original failed fixture and JUnit remain untouched. A private second copy of its13 JSON
receipts and failed JUnit is retained under `/tmp/fc-ha02-stabilize-20261125/retained-failure`.
The original failed JUnit SHA256 remains
`40fe8c267b11496ea2d85a4d66745015888a5f95b19b24c3b7afbf28d6d77c78`.
It proves irreversible WORKERS_REMAIN, not the identity of the extra task. **The historical
specific cause cannot be recovered from these artifacts.** A subsequent PASS is not an explanation.

The three `only_main()` boundaries now retain bounded, private census files: phase, last completed
step, fixed owner roles, Python identifiers, native TIDs and set differences. Thread names, messages,
keys, frames and arbitrary locals are excluded. Partial/read-failed/changing/over-limit snapshots
are explicitly incomplete and refuse progress. Samples are not described as atomic.

A controlled native-tail counterexample removes an owned thread from Python's active registry,
then holds its native lifetime with a pipe. Python enumeration is already main-only while the native
TID remains. No sleep, timeout extension or repeated attempt is used to make the check pass.
CPython3.14 joins the OS thread, but Linux distinguishes pthread completion from task detachment:
pidfd readable exit and pidfd HUP/reaping are different boundaries. The legacy bridge now retains
PIDFD_THREAD handles **before irreversible commit**, joins owned Python workers, and waits for their
kernel HUP before its unchanged native-task exclusion check. Unsupported pidfd setup refuses before
commit. Final-persistence starts and their descendants retain explicit ownership even after Python
enumeration loses them; they too are joined/reaped before persistence completion.

This establishes and fixes a concrete completion gap; it does **not** establish that this was the
original20:35UTC failure. Unknown native tasks still refuse; none are ignored or killed by the bridge.

## Terminal reconciliation

An irreversible error is durably latched as `MANUAL_RECONCILIATION_REQUIRED`, with its original
reason and receipt/diagnostic hashes. The CLI exits78, matching the existing supervisor
`RestartPreventExitStatus=78`; only genuine pending work returns WAITING/75. Re-entry, recovery
and direct rollback cannot install a candidate or restart the old writer after this latch.
Witness sampling refuses, and the receipt explicitly denies witness/open/capture permission.
Reservation guards remain in force, including dangling markers. No reservation removal is added.

A real user-systemd synthetic service injects `SYNTHETIC_FINAL_FAILURE` after READY. Its supervisor
exits78 with zero restarts, while the original process remains parked, no candidate/witness/rollback
intent is produced, and uncertainty remains. Fixture teardown is scoped to its synthetic unit only.

## Qualification through21:14UTC

| Check | Result | JUnit SHA256 |
| --- | --- | --- |
| Exit/terminal/replacement/witness, CPython3.14 GIL | 65 passed,0 skipped;462.45s | `5055ffef222fe99cbf3fc4cd411ace1ab1c6ecfc576c52d414dab687e063cbe5` |
| Native systemd terminal behavior | 1 passed,0 skipped;18.99s | `766b5e38d4ae874c8feb18f64dbfb8773c42b86f7cb42a1c4942067a2ef11ff6` |
| Actual fc-support UID/systemd replacement/witness | 3 passed,0 skipped;53.59s | `2b7e03445accf4af2754b684321119bd224dd983f5b7d9342dce24152c662303` |
| CI context/native-diagnostic regressions | 21 passed;1.50s | `041284a2b88d36dc3a4e4df7f5ea5cf49f3ef50307a4112a139ae5434b550bbd` |

An earlier preparation run stopped after51 passes and one newly introduced reservation-order
regression; its JUnit is retained as `initial-diagnostics.xml`. Reservation precedence was restored
before the complete final run. Preliminary and overlapping runs are not added to the final count.
The actual-root run21:13:45–21:14:40UTC independently verifies the working OWNER before and after:
same PID2022541,0 restarts,19 source pins, unit files and interpreter digest. These are isolated tests,
not working installation. Private evidence remains outside Git.

## CI integration: still open

The original CI artifacts are retained locally, not inferred from workflow names:

- a39c74b9: phase0 run45693050426, Linux control45693051031, messenger45693050885,
  notifications45693050692, panel45693051038 and voice45693050487 fail. Golden and Linux internal
  candidate pass; conditional Android/support workflows are skipped, not accepted.
- Exact595acebe: phase0 run45697240725 and Linux control45697240234 fail; golden45697240931 passes.
  Other path-filtered workflows did not run at this SHA and are not claimed successful.
- phase0 standard context at595acebe:72 failed,8957 passed,1009 skipped,521 errors. Root258 and
  snapshot31498 pass. All593 failed/error lines match the preceding artifact after normalizing
  temporary diagnostic paths; the earlier artifact additionally has the queue-descendant lifecycle
  failure. Docker failover also fails its full-suite build gate, not a working failover exercise.

Concrete corrections in this checkpoint: route native mailbox/remote-exec tests to a distinct
CPython3.14 **GIL-enabled**, unprivileged context while retaining Python3.13 desktop coverage;
install the existing HA PostgreSQL lockfile in test environments; provision messenger dependencies
for314; run messenger/notification/support-contract jobs on314; restore the actual migration graph
leaves after the payment migration test instead of leaving later console tables removed; preserve
bounded native-fixture stderr, including timeouts, in uploaded always-run diagnostic artifacts.
Fixture stdout/input containing synthetic custody material is not included in these logs.

No contract hashes or assertions are relaxed. Full CI is **not reconciled yet**: native-image/daemon
availability and internal errors, launcher executable permissions, historical overlay inputs,
runtime-package closure and the announcement-source contract still need exact-source resolution.
The migration change also requires panel CI, not just the context unit tests. New-source CI must be
observed after publication; a workflow that did not run is NOT_RUN.

## Installation, recovery and one next result

Installed support remains the original19-source OWNER runtime; candidate archive
`9d7bf840f3455d0ef2e7653dc9289aac2f0d77c9f2a0a8e305c786f7ddb80489` is **NOT installed**.
No working NL1 unit, mailbox, notification queue, product database or client version changes occur.
The seven historical UNKNOWN outcomes are neither cleared nor replayed. No code rollback may restore
old data. Existing reservation markers remain mandatory and may not be removed or bypassed.

**One next result:** reconcile applicable CI and qualify the single resumable, authenticated
OWNER ↔ NL1 handoff/reclosure/recovery, including live closed/drained mailbox verification,
old exit/candidate verification, reservation-bound witness consumption, confirmed opening,
identity-specific notice-queue pause, reclosure/drain/permit invalidation before code-only recovery,
and interrupted/lost-response/controller-death/mailbox-restart/candidate-restart boundaries; then
perform authorized working installation and independent readback. This combined executor and
working gate are not delivered by the shutdown correction. No renewed operational authorization
is requested, but unqualified working activation is not performed.

The same three HA-02 criteria remain partial: current approved inputs/trust and journals; coherent
installed schemas/all-writer capture; complete independent custody/final recovery. Replication
remains PASS in isolation. FLEET-PRODUCTION-ONBOARDING-1 remains mandatory and unimplemented:
VPS → IP/access/roles → ordinary enrollment → verified active node. Support migration alone cannot
close that requirement or all of HA-02.
