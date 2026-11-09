# RU operation budget: diagnostic candidate,9 November2026

## Boundaries and exact historical execution

Main at task entry: `7daf41418f0e8730f9636700bfb02556a8c56ce7`.
Accepted [recovery receipt](https://github.com/Joker20380/family_connect/pull/14#issuecomment-6740402014)
remains RECOVERED_CAUSE_OPEN. This work does not restart/recover RU again or retry
paid123. Central policy remains108/119. Owner phone permission is limited to existing
beta123/existing identity and two explicit RU transports; it is not another Android
qualification or permission to modify production services/admission.

Historical source: `b811547fcfd15d112c66d5db77a708daaee1b0a7`.
Installed node SHA256:
`f747759cfcf5b2881a18f984c81c95647db90cd30e93eea78e60066826c73131`;
gateway `9023d2c3f7c3a5127d67c509a16eb2d974810ff54d5b76cc225cd9b93e0b4234`.
The saved archive was verified and loaded directly in an isolated subprocess for
the historical reproductions; source/module equality was checked, not inferred
from a similar current implementation. Old bytes/evidence remain immutable.

## What the old persist_file record actually proves

At11:37:07.979763UTC the original invocation reports `watch/persist_file`,
`TRANSPORT_OPERATION_DEADLINE`, elapsed8.150496s against the total8s budget.
The error pass aggregates engine_query4.488401s and persist_file2.589603s;
the preceding complete pass was6.964687s. The8.150496s is **not an individual
fsync duration**. `Operation.stage` checks remaining time before and after its
body. The record therefore does not distinguish rejection before syscall entry
from successful syscall return after the overall deadline.

Recorded stages overlap: readback contains engine queries and persistence; repeated
calls accumulate under the same name. At least one replace and directory-sync
stage was entered in the failed operation, but old telemetry does not identify
its file or count completed syscalls. We cannot attribute the failing fsync to
state versus attempt, or prove the exact number of readback passes, from these
aggregates. One normal converged readback uses two AWG snapshots, one full TCP
snapshot, and writes state then attempt. Convergence may repeat, bounded by the
same operation deadline.63 records do not imply63 separate native queries here.

No retained per-process storage/scheduler trace establishes why the production
operation slowed. HTTP restart/backup/collector timing is not causal evidence.
Synthetic scenarios below demonstrate ambiguity and diagnostic usefulness, not
the historical root cause.

## Narrow diagnostic delta

- Per-call safe kind, file role (`decision_state`, `attempt_result`, `engine_config`,
  `failure_record`, otherwise `unknown`), relative start/finish, wall duration,
  remaining budget on entry, before/body/after boundary, completion and replace
  completion. No path, argv, profile, raw output, key or device identity.
- Counts of stage entries distinguish multiple queries/persistence/readback passes.
  Calls retain at most24 entries with an explicit dropped counter; aggregate timing
  remains available. Progress/failure records carry completed-call histories.
- Bounded process rusage deltas: self CPU time, major faults and voluntary/involuntary
  context switches. They are clues, **not proof of I/O versus scheduler attribution**;
  subprocess CPU and kernel wait reasons are not silently inferred. Missing optional
  resource data cannot replace an application failure.
- Exclusive first-failure persistence remains non-overwriting and precedes cleanup.
  Its fsync start/end are separately marked; cleanup never overwrites the primary
  record. For ordinary calls, a process killed before it can emit progress/failure
  may still leave no completed-call record; this candidate does not claim full tracing.

No optimization is asserted. `accept` commits lease/revision/prepared membership;
readback commits applied decisions/observation and the attempt receipt. Unchanged
peers alone do not prove these writes redundant. Both writes, file fsync, atomic
replace, directory fsync, and commit-before-ACK remain. No new daemon, restarter,
policy, schema or permanent tracing facility is introduced.

## Isolated evidence

Five controlled-clock cases around real temporary-file operations exercise both
the exact historical archive and the candidate:

| Case | Candidate observation | Atomic target |
|---|---|---|
| Budget exhausted before file fsync | before; no syscall start/duration; negative remaining | not replaced |
| TCP query uses7.95s; ordinary0.1s fsync crosses deadline | after; query7.95s, fsync0.1s, remaining0.05s | not replaced |
| File fsync itself delayed8.1s | after; fsync8.1s, remaining8s | not replaced |
| Replace delayed8.1s | after replace; replace_completed true | replaced; directory durability not yet confirmed |
| Directory fsync delayed8.1s | after directory fsync; replace_completed true | replaced; operation still fails closed |

These are synthetic timings, not measured production syscall durations. The old
archive yields the same phase/elapsed for the pre-entry and slow-file cases despite
different actual fixture syscall counts. The new fields distinguish them.

Addressed Python regressions cover first-failure retention/redaction, bounded command
cleanup, writes/roles/counts, partial replacement, expiry/revoke/replay/membership,
readback mismatch and exact package tamper rejection. The existing real-systemd
fixture runs the assembled node archive, production-style fc-friends sandbox and
root-only preflight with real AWG/Xray,63 synthetic records and19/48/5 registration
layouts. Positive HTTPS, terminal revoke, injected TCP-query rc73, stop and controlled
recovery pass; denied traffic stays denied and noncohort traffic returns. Diagnostic
call family/timing/completion are checked from the actual watcher failure record.
Measured protective stop in this run:0.772315s; fixture cleanup PASS. This is not
production user-traffic acceptance and not a new long soak.

## Package, review and field result

`scripts/package_transport_diagnostics.py` accepts only the exact PR9 node/gateway
pins and replaces only `control/friends/transport_gateway.py`. Policy and gateway
must remain byte-identical. It outputs a separate node archive and full before/after
module inventory; no HTTP/operator/reconciler, service/drop-in or installer change.
Fresh subprocess package tests verify the loaded archive and real durable-write
diagnostics, not source grep. Final committed-source rebuild, hashes, hosted checks,
review and merge are recorded in the PR receipt. Production installation is **NOT_RUN**
and needs a separate addressed decision; do not install this candidate automatically.

Redmi API31 is connected; initial UI shows Netherlands/MESH/VPN off. Temporary app
USB-support was closed at entry and one owner action was requested. Owner traffic
is not inferred from host requests, native sets, old beta123 split-routing results or
these synthetic tests. Final RU AWG/TCP DNS/verified HTTPS/egress, route correlation,
app-policy/settings restoration and helper cleanup belong in the private receipt and
sanitized PR follow-up. No phone APK/identity/cache/time changes are authorized.
