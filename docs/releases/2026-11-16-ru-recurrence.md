# RU recurrence — 16 November 2026

## Outcome: NOT_RECOVERED / CAUSE_OPEN

The owner's new report is confirmed by read-only checks at11:32–11:42UTC.
AWG is failed/PID0/result timeout; TCP is inactive/PID0. Watcher is intermittently
active but its restart counter rises335→349; this is not working VPN. Reconciler
fails with exit1 while its timer remains active. No recovery or production mutation
is performed. The preceding release scope expressly excluded repeating RU recovery;
this diagnostic receipt does not silently override that operational boundary.

Primary dirty checkout is untouched. Evidence and bounded original journal/first-
failure bytes are retained privately, not committed. Worktree source at entry is
ba3e93703d407c945350c1187e3738d25a3c9eab; remote feature matches. Remote main remains
53a780d9ccfcdb2c3ec6141a197917190f9be7a5. This is documentation, not a runtime fix.

## Ordering matters

| UTC | Observed event |
| --- | --- |
| 08:12:36.327610 | Systemd records watcher watchdog timeout. |
| 08:12:36.330884–.341113 | AWG/TCP stopping; TCP deactivates and stops. |
| 08:12:41.578648–.585350 | Watcher and AWG stop timeouts; kill actions recorded. |
| 08:12:57.078839–.080652 | Watcher and AWG fail; AWG stop completes. |
| 08:13:02.335036 | Watcher restarts. |
| 08:13:10.462999 | Retained failure: watch/lock/body, TRANSPORT_OPERATION_DEADLINE,8.000265s against8s; one lock stage, no recorded calls. |
| 08:14:45.194377–.543380 | TCP briefly starts and stops again. |
| 11:32:25 | AWG/TCP unavailable; watcher NRestarts335. |
| 11:40 readback | AWG/TCP still unavailable; watcher NRestarts349. |

The retained first-failure file SHA256 is
`83daf7773ed5e6687c11252a3ec71753afbdb4c67de05deb2ddfcc4aeb716fbc`.
Its error occurs **after** the initiating watchdog and transport stops. It does not
identify what delayed the original watcher, the holder of its lock, a persistence
call, or a particular engine query. No weakening of8/12/120s or BindsTo is proposed.

The initial bounded multi-file journal read timed out; a narrower read also timed
out. Reading the single relevant archived journal instead returns61 records for
08:11–08:15:30. The current journal alone has no records for that window. A separate
54-record kernel window08:10–08:16 has no matched OOM/blocked-task/I/O-error markers;
this limited search does not establish that no kernel/resource problem occurred.

## Resource observations, not root-cause proof

The599s sysstat interval ending08:20UTC contains vda await406.32ms, average queue7.78,
CPU iowait18.01%, steal1.75%, I/O full pressure18.51% and memory full pressure6.93%.
The preceding600s interval ending08:10 had await20.40ms, queue0.58 and iowait4.61%.
This supports substantial concurrent I/O delay, not attribution to a process,
storage provider, metadata collection, HMAC rotation or the Android native defect.

At11:32 root has7.02GiB free and uptime exceeds75 days. At11:34 four Python tasks
are in D/folio_wait_bit_common; the subsequent11:36 snapshot has no D-state tasks
or holders on registration.lock/application.lock. These later samples do not
reconstruct the original lock holder or prove a permanent resource recovery.

## Accepted bytes and separate HTTP activity

| Component | SHA256 |
| --- | --- |
| Transport node | `125c796a30c3fba1772c47b96963517350087ad04aad675b6f33a31a5383276c` |
| Gateway | `9023d2c3f7c3a5127d67c509a16eb2d974810ff54d5b76cc225cd9b93e0b4234` |
| Effective watcher unit | `659b954beb67d1e23c0cea45ffda62704f48dc2fb0b1f5bd30d0ae733760bd4e` |
| Serving metadata HTTP | `70a924dbc02c4ebdb15fe2b935f29070bda0a5fa37f140ac2d35765b34500614` |
| Operator archive | `a7c801dba6a09e35c9ca7a6e6d816bbb57bc4f483404d44b5ee7f641e70cac15` |
| Reconciler archive | `40e1d7212b158fa01e4e4a92c0b635a910ae05b8b350840c07629629108b7aeb` |
| Running panel image | `5ae92f8c7775d2ff0ad26627f6cdfcda53a3d4193a08b9fe1de1e89f32c432da` |

HTTP candidate stops/starts at08:54:17–08:54:57, then again at11:39:28–11:40:07
while this read-only check is running. Its configured Restart=no, PartOf/TriggeredBy
empty and current NRestarts0 do not identify who initiated these actions. Hash stays
70a924db; final PID775862 is active. These restarts were not issued by this diagnostic
run. Reconcile concurrent operational activity before any subsequent mutation.

The local panel remains running. Normal monitor receipt11:41:17.954223UTC reports
metadata IMPORTED and production_writes0. This is not proof of VPN, successful
subscription reconciliation or actual notification delivery. No keys, aliases,
identities, messages, canonical data, paid terms, baseline/cursor or phone settings
are changed by this diagnosis. No new full preservation comparison is claimed.

## Recovery boundary

Metadata release/physical acceptance is interrupted. The signed candidate stays
immutable and unpublished; exact paid126 remains unloaded. The independent native
race gate remains open. No observer, pressure workload or automatic recovery loop
is introduced, and no old database or disclosed key is restored.

A separately coordinated RU recovery must use the existing
[guarded procedure](../operators/subscriptions.ru.md): fresh accepted-pin/ownership/
resource readback and consistent backup/isolated restore; RU-only central fence
while NL refresh continues; drain, grouped stop and PID0/no-jobs/zero handlers;
retained-state validation; preserve this failure without overwrite; sequential
unchanged-runtime start; restore the exact command map; several ordinary actual/
persisted readbacks and lease renewal across120s. Do not simply restart the watcher.
If drain/preflight fails, keep the safe fence and diagnose rather than retry-loop.
Recovery preserves generation2 and all current user data; it would not close the
cause of recurring latency or substitute for physical client acceptance.

Documentation checks:6 changed files/849 links, zero errors; whitespace and staged
secret/raw-device-ID pattern checks pass. Review is the author's own; no runtime
or independent review PASS is claimed by this documentation checkpoint.
