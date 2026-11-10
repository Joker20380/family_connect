# RU TCP query boundary — 10 November 2026

Scope: continue incident [PR16/comment6755872599](https://github.com/Joker20380/family_connect/pull/16#issuecomment-6755872599).
Deployment remains **DEPLOYMENT_FAILED_ROLLED_BACK_VERIFIED**. No PR16 or paid123
retry, phone operation, policy change or production fault injection is authorized here.
Fresh read-only entry observation finds RU engines/watcher running, without a restart
loop. Installed node remains125c796a, gateway9023d2c3, policy108/119.

## Evidence boundary

The exact engine and CLI binary is Xray26.3.27, SHA256
`4f7a4436f86798bbb5c875014e352021a1673710a45e170ccc507c5f59341940`, upstream
`d2758a023cd7f4174a5a5fa4ff66e487d4342ba0`. The running executable matches the
CLI path. The engine runs as `fc-friends`; the query child inherits the root watcher
context. These are different processes and different service restrictions.

The saved00:52:27UTC operation records TCP command timeout:7.841651s remaining on
entry,8.163121s within the command and8.321587s total operation. AWG query took
0.146105s. There are no persistence calls in this failed pass. Earlier persistence
incidents are separate evidence. Python-parent CPU/scheduling counters do not measure
the Xray child. Historical Popen/communicate boundaries, child output sizes and API
request arrival were not retained; the stage within TCP query remains UNKNOWN.

Exact-version source uses a shared **3s context for blocking gRPC dial and RPC**.
It starts after CLI initialization and does not cover JSON output/process termination.
This is not evidence that the historical failure was a gRPC deadline, server deadlock,
resource shortage or filesystem delay. The engine's stdout/stderr are null; present-day
resource counters cannot reconstruct historical pressure.

## Reproduced wrapper defect, separate from historical cause

The previous executor computes remaining time before Popen, then reuses it for
communicate. Two deterministic real-child regressions show that slow creation grants
the child extra time, allowing a late synthetic action after the shared deadline.
The candidate recalculates remaining time after creation; on failure it kills its
own process group, bounds reaping to250ms and closes its pipes instead of performing
an unbounded second drain. Cleanup metadata does not replace the primary exception.
Unreaped/uninterruptible children are reported, not treated as successful termination.
The250ms termination allowance is cleanup after failure, never extra actuation time;
8s operation,12s watchdog and120s lease constants are unchanged. Kernel process
creation/scheduling cannot be made hard-real-time by a Python timeout.

Safe per-command metadata separates spawn, communicate and cleanup durations,
remaining time, completion, return code and output byte counts. It contains no raw
argv/output, identity, key or profile. It cannot by itself split dial from handler time.
Durable security state, fsync/replace/directory sync and commit-before-ACK are unchanged.

## Acceptance status

Local wrapper/budget regressions:13 PASS; baseline: two late-action regressions FAIL,
descendant cleanup PASS. Exact-Xray systemd/native stage discrimination, packaged
security regressions, hosted checks and review remain pending at this source checkpoint.
No candidate installed. Final immutable candidate identities and receipts will be
attached to the task PR, not reassigned to the historical installed archive.
