# RU recurrence — 15 November 2026

## Final recovery — RECOVERED_CAUSE_OPEN

The owner explicitly confirmed the separate recovery after the read-only diagnosis.
RU watcher/AWG/TCP are restored on the same accepted bytes by13:03:16.077UTC.
No metadata deployment, version change or HMAC rollback is part of this recovery.

Fresh preflight at13:02:06UTC verifies runtime pins, effective watcher unit and
original command-map digest. All27 canonical registry tables restore identically
into a separate SQLite, with integrity/FK checks and the three exact-runtime paid
projections evaluated at the same time. The restored database never replaces live
data. Private evidence stays on RU and an encrypted offline copy is retained;
AES-GCM decryption/digest round trip passes. Encrypted archive187933bytes SHA256:
`8fb269a836de0c95f65200ed499aa2142ce548239334e78ab07f00a2c9064d22`.
Registry backup SHA256:
`056aa06790f4b978f2c9ebf13051144d3eec831f176a86741328686c5af8b0a0`.
Backup key is kept separately in the protected local backup-key directory.

The initial preparatory ownership guard rejected the reconciler's existing
uid1000/gid1000/mode0664. Inspection confirms the accepted40e1d721 archive hash,
its unchanged14November timestamp and root-owned0700 immediate parent. The
recovery pins that exact existing ownership instead of assuming every artifact
is root-owned. Node/gateway remain root-owned0600. No ownership or permissions
were changed; this is not a new archive installation or a security-hardening claim.

Only gateway-ru is fenced in the command map; both NL commands and the central
timer remain. After the current cycle drains, watcher/AWG/TCP are stopped together.
At13:02:46UTC all have MainPID0/ControlPID0, no pending jobs and zero gateway
handlers. Native files, current decisions and a consistent peers database are
backed up. Installed engine load/lock validation and retained TCP identity checks
pass for66 decisions/20 registered peers without modifying decision-state bytes.

The original first-failure bytes are archived without replacement as
`friends-awg/transport-failure.20261115-120648.preserved.json`; their digest remains
the97afb4fa value recorded below. After reset-failed and sequential unchanged-runtime
starts, the exact original command-map bytes are restored. No old database is
restored, denied decisions are not cleared and no lease/expiry is manually extended.

| Unit | Restored PID | Observation |
| --- | ---: | --- |
| paid-watch | 733875 | active/running, NRestarts0 |
| friends-awg | 733879 | active/running, NRestarts0 |
| friends-tcp | 733898 | active/running, NRestarts0 |
| HTTP candidate | 325012 | Original PID/invocation unchanged |
| peer worker | 3967036 | Original PID/invocation unchanged |

Six server observations from13:03:56.768 to13:07:17.822UTC span **201.054s**.
Every observation verifies exact live20 AWG/20 TCP sets, TCP id/email/flow, all66
persisted applied revisions and fresh ordinary watcher readback (final age0.822s).
All restored PIDs/invocations remain, restart counters stay0 and no new first
failure appears. Ordinary reconciliation succeeds with its original timer active.
The cohort deadline advances **1794747946→1794748148**; the final observation
crosses the initial deadline while remaining before the renewed deadline.

Full row fingerprints remain equal for these current protected canonical tables:

| Table/domain | Before | After | Result |
| --- | ---: | ---: | --- |
| Devices | 66 | 66 | Unchanged |
| Invites | 121 | 121 | Unchanged |
| Paid subscriptions | 1 | 1 | Unchanged, including terms/expiry |
| Paid events | 4 | 4 | Unchanged |
| Chat bindings | 53 | 53 | Unchanged |
| Official chat senders | 1 | 1 | Unchanged |
| Referral links | 19 | 19 | Unchanged |
| Referral claims | 59 | 59 | Unchanged |

Retained device/public/TCP identities, membership/revisions/paid terms and prepared
decisions also compare equal across all66 transport records. Expected observation
and lease timestamps advance normally, not by restoring stale state. All six
checked effective service definitions remain identical. HMAC generation2 manifest
validates; RU/operator keys both equal the prepared generation2 key in-process.
Manifest digest remains8602e6526ca1ec0e408c99a7ca37aedc4413b417f392e32096d5167517fcdcb8.
No key, mapping or raw identifier is published. Local support owner remains active,
NRestarts0; support histories, queues and notification baselines are not rewritten.

Panel read at13:07:32UTC confirms all three transport snapshots `ok`,66 records each.
RU observed13:07:20/imported13:07:22.926, registry status `ok`, accepted node125c796a.
NL1/NL2 also have fresh transport imports; their `not_collected` inventory registry
status is expected because canonical registry collection belongs to RU.
The actual `/inventory/` route follows its login redirect to HTTP200. An initial
guess `/accounts/login/` returned404; it was not treated as a panel outage or PASS.
Open the panel at http://127.0.0.1:8765/inventory/ with the existing login.

**Remaining limit:** client VPN DNS/verified HTTPS/egress is NOT_RUN. Server
restoration and renewed admission are verified, not permanent removal of the
latency cause. No new observer, pressure run or unqualified lifecycle/failure-writer
candidate is enabled. If failure recurs, preserve the new first failure and use
the guarded procedure; do not create an automatic restart loop, relax8/12/120s,
restore an old database or reactivate the disclosed HMAC key.

## Historical diagnosis and scope before authorization

**Initial NOT_RECOVERED / CAUSE_OPEN.** The owner's new report is confirmed by read-only
RU observations at12:46:47–12:49:31UTC. This is not merely a stale panel.
No remote service, configuration, key, policy or database was changed in this
diagnostic phase. No transport restart, pressure workload, new recorder,
timeout relaxation or collection-window extension was performed.

The preceding permission covered only the HMAC generation2 cutover and expressly
excluded transport/paid restarts. A separate bounded recovery is proposed below;
it was not yet executed at that point. The dirty primary checkout is preserved. Safe evidence
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

## Recovery plan confirmed and executed

The owner's subsequent confirmation covered restoring only the existing RU AWG/TCP/watcher
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

The Git checkpoint changes documentation only; operational recovery is described
separately above. Public beta125/catalog8, exact
paid108/119/123/125 and metadata NOT_DEPLOYED remain. No APK is built or published,
and no product or RU root-cause acceptance is claimed. PR38 stays draft.
Remote main at entry is53a780d9ccfcdb2c3ec6141a197917190f9be7a5;
the diagnosis documentation head is46543f33296d048698fc0ae3818a21f677c54f75.
Recovery documentation checks:5 changed files/829 local links, zero errors;
whitespace check passes. Review is the author's own, not an independent review.
The initial diagnosis checkpoint separately passed4 files/813 links and its
staged private-key scan. No source/runtime test results are invented for this
documentation change; operational checks and their limitations are listed above.
