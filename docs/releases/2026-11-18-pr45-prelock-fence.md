# 18 November — PR45 pre-lock emergency-latch repair, NOT_DEPLOYED

## Scope and immutable failing baseline

Independent review blocks exact head `3f5698e432871e55cd2f1dee33673f266cb3136d`.
Continue its existing feature worktree without resetting other worktrees/main.
Remote main remains `bc8f7b5b42800269aeb43bcf54059205e7a7cbf7`; accepted PR44
is unchanged. Old manifests and qualification results remain evidence only for
their old bytes. PR45 returns to draft pending this repair and repeat review.
No production access/restart/rollout, payment/message fixtures or new product work.

Real-process source reproduction uses the real entrypoint with synthetic engine
adapters, real flock, and barriers: B enters application.lock open;8.15s elapse;
later A owns the lock/active intent and waits; B resumes open, hits its already
expired8s budget before acquiring flock, requests async stop, records error attempt
and first failure; A continues. Exact old source executes three queries, emits
result=applied, deletes the shared marker and collector returns ok. Immediate open
EIO after the same ownership barrier has the same failure. Two regression assertions
FAIL on unchanged runtime; source log SHA256
`f22a9921b7d04d6ad80f47c816b5f1b763e5ae461cc39a23cb9d318de7e31c65`.

Separately, exact old installed bundle/nodef454af6a under real isolated systemd
reproduces both unsafe ACKs with nonzero actual engine MainPID/ControlPID and pending
stop Jobs. Receipt deadline SHA256
`99fc9911ee0b3b5956bbfdfa33c1b497c9f71bc069688d97921b27c2e99f4812`;
open-error SHA256 `7ce1973000f950316b4762e0df1d589af5adc0ea40b02f1b51b07fb6f4c64e7a`.
Both are REPRODUCED_UNSAFE_ACK, not acceptance; cleanup PASS. Exact event timestamps,
ACKs, query counts, collector and stop properties are retained. The first fixture
attempt correctly rejected an inherited /kit module import: fixed by running this
phase in a fresh interpreter that asserts the installed archive loader; retained
failed receipt is not presented as a runtime result. Original package was unchanged.

## Corrected concurrency contract

`application-incomplete` means an active/interrupted operation. The separate
`application-failed` emergency latch is sticky; no ordinary success removes it.
An independent `application-outcome.lock` orders emergency publication/error cleanup,
successful completion and explicit recovery. Lock order is application then outcome;
pre-lock fail-closed needs outcome only, never application. Collector takes shared
application/registration/outcome locks, rejecting both markers and any active writer.

An ordinary operation acquires the outcome flock after its body while still holding
the application descriptor. It checks the emergency latch, removes only its active
intent, then validates the original operation deadline and checks the emergency
latch again **before** progress=complete/context success, then checks the original
deadline once more to include time spent checking the latch. That final latch check is the
success linearization point. It is not an uncoordinated exists()/rmdir fix: a failure
published earlier under outcome excludes success; a failure contending with final
completion publishes after it and excludes subsequent operations. Such a later
failure cannot retroactively retract an already committed result/ACK. A conservative
emergency fallback on outcome-lock I/O failure is also caught by the final check
if published before that success point. Neither successful path deletes its latch.
Failure cleanup retains the first saved diagnostic and the original raised error.

Recovery is not ordinary success. External fence/drain must exclude concurrent
handlers and service starts; actual watcher/AWG/TCP must be loaded, inactive/failed,
MainPID=ControlPID0 and Job empty. With application/outcome descriptors held, recovery
maintains active intent, validates retained state, discards disposable observation
and clears the two markers. Final deadline/emergency checks still apply; error
rearms the ban. No authority/preparation/first-failure data is restored or removed.
Lock inodes stay in place. Process exit releases flock, not the sticky emergency.
This is same-boot safety, not physical power-loss or uninterruptible-storage proof.

PR44 budget starts before application-lock open; descriptor spans final validation
and error cleanup; durable commit precedes ACK.8/12/120, default legacy, lease/
revision/terminal revoke, preparation, identity binding and anti-replay unchanged.
No unconditional restart, timeout increase, heartbeat or historical latency claim.

## Repair gates and evidence routing

Checkpoint `fdcdf961cd399728c199ab9c42281c1d6599e5cc` passes213 transport tests
and produces two identical24-file bundles (nodef3eca939, manifest7db3aef4). Its panel
CI fails because the old synthetic observation fixture creates only two lock files;
local exact-case FAIL confirms missing outcome-lock, not a reason to weaken collector
checks. The corrected fixture creates all three and tests both markers/exclusive
outcome writer as unavailable; full320 panel tests pass on a disposable synthetic DB.
Keep the failed CI runs44411941321/44411933262 and skipped downstream steps historical;
new final-head panel CI must execute the complete gate, not rerun unchanged failure.

First installedfdcdf961 run fails during controlled AWG recovery: native actuation
exits1, then watcher readback fails closed; cleanup PASS. Receipt SHA256
`18e333d40a27ab4003e1f0710917b2a086e3a6ee76e4472bef18d89a0854b0d5`.
The short original journal cannot establish the native cause; it remains unassigned,
not declared fixed by later availability. A separate diagnostic-only AWG wrapper
calls unchanged installed code and classifies native stderr without exposing values;
that run passes full matrix including both P1 overlaps/rollback, but does not reproduce
or explain the native failure (receipt `b53793bd25839466cfbfb7f36e09187726ebc6dbca6cc7f1ed3fcfe457665f62`).
It is not final uninstrumented-AWG acceptance. Its patch stays local with the receipt.
Final source removes that wrapper, records more unit-scoped failure evidence and
requires NRestarts=0 after every controlled start, so automatic restart cannot mask
a native startup failure. Runtime/gateway bytes and service limits are not altered.
Repeat full installed qualification of the final manifest under that stricter gate;
retain the first FAIL and this limitation even if the final bounded run passes.

213 transport/source/package tests cover the repair with locked control/identity dependencies.
New tests distinguish failure-before-completion from later failure publication for
registration/watch/recovery; cover final deadline, outcome-lock I/O fallback and
emergency persistence after process exit. Prior interrupted-write, owner-error,
first-receipt barrier and ACK tests remain; final-exit injection now targets removal
of active intent, after the new outcome acquisition, rather than an earlier boundary.
Systemd fixture adds both real pre-lock overlaps, pending-unit recovery rejection,
subsequent registration rejection, and explicit stopped recovery restoring service.

Accepted packager and historical PR15 guards/legacy bytes remain unchanged. Repair
changes node/collector together; rebuild twice from exact committed source, verify
the complete new manifest and installed paths/owners/effective units. Full installed
matrix still includes owner-error, durable delay/error, actual watchdog termination,
generation/freshness, native permitted/denied traffic, retained post-install authority
through legacy rollback/return and comparable six-cycle18-query/12-to0-sync results.
Do not carry any old artifact PASS onto these new bytes.

Before repeat review require final bundle/systemd/rollback PASS, all applicable
exact-head CI, self-review of this two-process ordering and verified ordinary push.
Final source/tree/component/manifest hashes, run IDs, terminal results and limitations
belong in the PR45 receipt, with no cosmetic commit after acceptance. Non-PASS runs
and raw synthetic/private fixture diagnostics stay locally outside Git; publish only
sanitized summaries. Evidence root: `/tmp/fc-pr45-repair-20261118`.

Production **NOT_DEPLOYED**. RU/NL recovered services and paid-v2/HMAC2/tombstones/
support/notification state untouched. Repeat review precedes any merge or separately
authorized RU-only delivery. Android subscription-card auto-refresh stays queued;
physical iOS deferred and desktop L04.2 paused. Storage latency remains UNKNOWN.
