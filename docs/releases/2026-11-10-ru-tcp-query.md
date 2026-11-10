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

The same watcher invocation retained87 successful passes from00:48:32.911 to
00:51:35.756UTC (maximum complete operation0.362575s). A00:52:10 snapshot still
shows the original Xray invocation started00:47:40, without a restart. First failure
was recorded00:52:27.541; TCP exited00:52:29, AWG00:52:31, watcher watchdog00:52:32,
NRestarts0. Source order is timeout → first-failure record → protective stop request;
individual diagnostic-fsync/stop-job completion times are not available. The later
watchdog is not the initiating error. There is no retained API-listener/RPC-arrival
observation at the failure instant and no retained child output/exit status.

Host PSI17s before failure: CPU some avg10=9.34, I/O some4.22/full2.38, memory0.
These are interval host metrics, not proof of starvation of this child or an I/O
cause. Historical per-child/cgroup throttling and wait-channel evidence is missing.
Fresh engine restrictions are256MiB/128tasks, `fc-friends`, strict filesystem sandbox;
watcher/query are root with no CPU quota and no service memory cap. Current cgroup
OOM/throttle counters are zero; they do not reconstruct the failed invocation.

Exact-version source uses a shared **3s context for blocking gRPC dial and RPC**.
It starts after CLI initialization and does not cover JSON output/process termination.
This is not evidence that the historical failure was a gRPC deadline, server deadlock,
resource shortage or filesystem delay. The engine's stdout/stderr are null; present-day
resource counters cannot reconstruct historical pressure.

In this exact source, the handler gets the inbound under the manager read lock,
then enumerates VLESS users via `sync.Map.Range` and converts them to protobuf.
There is no evidence of a concurrent inbound removal/replacement holding that lock
in this incident. No hypothetical handler-lock repair or Xray upgrade is proposed.
Dial reconnect/backoff remains inside the same3s context; no extra CLI retry loop
or supported flag is assumed or added.

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

Local transport/package/security selection:87 PASS. Baseline: two late-action
regressions FAIL, descendant cleanup PASS; corrected wrapper selection:13 PASS.
Real-systemd/native fixture uses the exact Xray hash, real AWG, synthetic63-record
registry and19/48/5 registration sets. Xray remains `fc-friends` with the production
base unit, sandbox and root-only preflight. CLI probe runs in a root systemd unit
with watcher-equivalent network/access/limits, not a privileged engine or root-shell
substitute. Disposable nodes are bounded to0.6CPU/448MiB; engine256MiB/128tasks.
Fixture Python is3.12; source tests run on3.14. This is not a claim that host load or
production scheduling was reproduced.

| Isolated case | Measured seconds | Result / observed boundary |
| --- | ---: | --- |
| Exact CLI baseline | 0.011512 | Full live id/email/flow set matches direct RPC |
| Same exact-proto direct RPC | 0.001205 | Same set, not count/config substitution |
| Synthetic slow Popen,0.2s test budget | 0.303067 | No new wait allowance; child killed/reaped |
| Synthetic0.4s before CLI exec | 0.433121 | Successful real CLI/RPC after the artificial delay |
| API port unavailable | 3.010854 | CLI dial error, not outer8s timeout |
| TCP accepted, no HTTP/2 settings | 3.020705 | CLI dial error despite a TCP listener |
| Proxy received real RPC response, delayed reply | 3.018732 | CLI DeadlineExceeded; direct RPC also expires |
| CLI response/output received, inherited pipe held | 1.001308 | Scaled1s outer timeout; leader exit0; own group terminated |

The relay forwards the exact `GetInboundUsers` protobuf RPC to the real Xray and
delays only the isolated return path; it does not invent the set. Delays and inherited
pipe holder are synthetic stage discriminators, not reproduction of the historical
trigger. No handler deadlock, CLI initialization defect or resource cause is established.
Packaged preflight, first-failure-before-cleanup, controlled manual recovery, positive
HTTPS, terminal-denied traffic and noncohort preservation pass. No live own descendant
remains after the held-pipe case. Disposable containers/networks are removed.

One specific missing historical boundary remains: **did the failed CLI complete
`GetInboundUsers` and receive its response before the outer timeout?** That boundary
would distinguish an unfinished API exchange from a post-response process/output
delay. Neither the saved aggregate command timing nor current healthy samples provide
it. New spawn/wait/cleanup metadata narrows the wrapper boundaries but does not pretend
to instrument the remote handler or prove that historical response arrived.

Live read-only observations09:33:47–09:57:47UTC: same RU PIDs, all three services
active/success, NRestarts0, fresh applied attempts, protected fingerprints unchanged.
No extra production API queries, service changes, fence, recovery or deployment.
One bounded5s current-invocation journal request timed out; no repeated scan. The
ordinary service/readback evidence remains distinct from user traffic (not rerun).

Hosted checks and ordinary review/merge are recorded in the task PR receipt. Exact
candidate module archive is `b0d4e5096e3b40529a99de6841a80301c5c9b2845c6e7e3903c366a534211a45`;
it includes already accepted PR16 manual lifecycle/output behavior plus this wrapper
delta. Its unchanged PR16 `Restart=no` unit is
`1887854790a4dcc2d6aee06e575c7f5311468304b3ff7e73d72e4bfb98f72e21`.
It is **not installed** and is not represented as a cure for the historical TCP delay.
Final source/bundle/inventory identities belong to the PR receipt; installed125c796a
and historical PR16 artifacts retain their original provenance.
