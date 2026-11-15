# RU recurrence — 15 November 2026

## Result and scope

**NOT_RECOVERED / CAUSE_OPEN.** The owner's new report is confirmed by read-only
RU observations at12:46:47–12:49:31UTC. This is not merely a stale panel.
No remote service, configuration, key, policy or database was changed in this
diagnostic continuation. No transport restart, pressure workload, new recorder,
timeout relaxation or collection-window extension was performed.

The preceding permission covered only the HMAC generation2 cutover and expressly
excluded transport/paid restarts. A separate bounded recovery is proposed below;
it has not been executed. The dirty primary checkout is preserved. Safe evidence
documentation uses the existing PR38 worktree, not a new production deployment.

## Preserved first failure and timeline

Original first-failure bytes are retained privately with restricted access, without
overwriting the server record. SHA256:
`97afb4fab46b1edcc003c6d8093c34751129eb228bc61b9e68cf90f6b8143ce3`.

| UTC on15 November | Observation |
| --- | --- |
| 12:06:48.857091 | Watcher PID3952264 records COMMAND_TIMEOUT / TimeoutExpired, engine_query, tcp-query, boundary body. |
| 12:06:49 | Both transport units leave active state. |
| 12:06:49.954855 | Systemd journal records watcher watchdog timeout. |
| 12:06:51 | TCP completes stop with exit0. |
| 12:06:54 | AWG completes failed stop: timeout, status9/KILL. |
| 12:46:47 | AWG failed/PID0, TCP inactive/PID0, watcher active but NRestarts67, reconciler failed/exit1. |
| 12:49:31 | Latest transport attempt remains error; HTTP and peer worker active. |

The first-failure operation consumed9.284026s against8s. Its two recorded calls:

| Call | Remaining before call | Duration | Outcome |
| --- | ---: | ---: | --- |
| AWG query | 2.328873s | 0.002528s | Completed |
| TCP query | 2.326040s | 3.609965s | Timed out, not completed;8 recorded major faults |

No recorded calls were dropped. The operation reports lock3, plan1, readback1 and
engine_query2 stage entries, but this first-failure record does not provide their
individual durations. Do not assign the preceding roughly5.67s to a specific lock
or writer. No persistence call appears in this failure's call list: unlike the
12/13November incidents, it is not evidence of an fsync timeout.

The installed engine's fail-closed path requests transport stops; both transport
units also BindsTo the watcher. Watcher-only restart does not start the stopped
engines, so `active` on one restarting watcher does not establish VPN availability.
The next watchdog timeout is separately observed; it is not substituted for the
earlier recorded command failure. A permanent fix is not demonstrated.

## Runtime and surrounding evidence

| Component | Observed SHA256 |
| --- | --- |
| Paid transport node | `125c796a30c3fba1772c47b96963517350087ad04aad675b6f33a31a5383276c` |
| Gateway | `9023d2c3f7c3a5127d67c509a16eb2d974810ff54d5b76cc225cd9b93e0b4234` |
| Effective watcher unit | `659b954beb67d1e23c0cea45ffda62704f48dc2fb0b1f5bd30d0ae733760bd4e` |
| Paid reconciler | `40e1d7212b158fa01e4e4a92c0b635a910ae05b8b350840c07629629108b7aeb` |

These match accepted runtime evidence, not an unqualified PR38 installation.
At12:49HTTP candidate PID325012 and peer worker PID3967036 remain active with
NRestarts0. The old `friends-access` unit is inactive; it is not the serving HTTP
candidate and is not restarted. No current end-user VPN/HTTPS test was run.

Remote root has7.28GiB available. The599-second sysstat interval ending12:10UTC
contains disk vda await205.26ms, average queue9.59, CPU iowait7.89%, steal0.82%,
I/O full pressure8.53%, memory full pressure1.17%, swap-in1.40 and swap-out6.26
pages/s. This supports concurrent I/O pressure, not a proven process, physical
disk/provider fault, OOM, or causal link to HMAC rotation. The failed operation's
major-fault counter is likewise not sufficient attribution.

The retained pressure/qualification units that show active are actually
active/exited with MainPID0; failed probe/qualification units also have PID0.
They are not currently running observer processes. No such unit was stopped or
deleted. Bounded journal queries covered only the failure window; they are not a
complete system-log audit. No raw journal text, identifiers, keys or mapping is
published. Protected local evidence is kept outside Git.

## Proposed controlled recovery — not executed

One owner confirmation should cover restoring only the existing RU AWG/TCP/watcher
runtime by the [established procedure](../operators/subscriptions.ru.md), without
changing binaries, policy, persistence or HMAC generation:

1. Refresh accepted pins, effective units, live commands and protected registry/
   transport state; preserve a fresh consistent private backup and first failure.
2. Fence only gateway-ru in the central command map, preserving NL entries and
   their reconciliation. Drain the current cycle before stopping RU handlers.
3. Stop watcher/AWG/TCP together; require PID0, no pending jobs and no remaining
   handlers. Validate retained decisions under the normal operation/lock.
4. Archive the exact first failure without overwrite; sequentially start the same
   accepted runtime. On failure retain the RU fence and investigate, not retry-loop.
5. Restore the exact original command map, observe several ordinary cycles beyond
   the120s lease, and verify actual/persisted engine sets, renewed admission,
   stable PIDs/restart counters, unchanged protected data and fresh panel import.

Retain generation2 keys/aliases and all new user data. Never restore an old DB over
current events, reactivate the disclosed key, weaken8/12/120s or change paid terms.
Recovery would restore service availability, not resolve the recurrent latency.
Physical-client traffic and a lasting root-cause correction remain separate gates.

## Documentation and release boundary

This checkpoint changes documentation only. Public beta125/catalog8, exact
paid108/119/123/125 and metadata NOT_DEPLOYED remain. No APK is built or published,
and no product or RU root-cause acceptance is claimed. PR38 stays draft.
Remote main at entry is53a780d9ccfcdb2c3ec6141a197917190f9be7a5;
the preceding documentation head is7edf0e8e10d3e08b9b3c636def9e4ee1db8d9f73.
Documentation checks:4 changed files/813 local links, zero errors; whitespace check
passes. Staged private-key scan reports zero matches. Review is the author's own.
