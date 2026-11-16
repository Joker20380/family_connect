# RU recurrence — 16 November 2026

## New outage — 16 November15:34UTC

**Current outcome at15:48UTC: NOT_RECOVERED / CAUSE_OPEN.** The owner reports another
outage during the metadata-release continuation. This section supersedes current-health
inferences from the earlier successful recovery; it does not erase its acceptance.
Only bounded read-only checks are performed. No fence, stop/start, reset-failed,
configuration/timeout change, database restoration or new observer is authorized or
performed by this diagnostic checkpoint.

| Observed at15:43:45UTC | Result |
| --- | --- |
| AWG | failed / timeout / PID0, inactive since15:34:43UTC |
| TCP | inactive / success / PID0, inactive since15:34:36UTC |
| Watcher | transiently active, NRestarts16; restarting is not healthy VPN |
| Paid reconcile | failed / exit1; timer active/waiting |
| HTTP | active/success; accepted archive, separate14:25:14UTC start |
| Public HTTPS |200; beta125 remains advertised |
| Monitor | inventory/metadata IMPORTED15:44:04UTC; not VPN/reconcile acceptance |

A single current journal file yields43 selected records in the bounded15:32–15:36UTC
window. The private original records and failure bytes are retained locally, without
printing request identities, IPs, keys, configuration or message content.

| UTC | Recorded ordering |
| --- | --- |
| 15:34:36.622163–.622307 | Paid reconcile exits; systemd result timeout. |
| 15:34:36.968379 | Watcher watchdog timeout. |
| 15:34:36.969224–.970888 | AWG/TCP stopping; TCP stops. |
| 15:34:43.020721–.031913 | AWG stop-sigterm timeout, failed/timeout, stopped. |
| 15:34:43.050430–.050879 | Watcher exits, failed/watchdog. |
| 15:34:48.080202 onward | Watcher restarts, followed by further exit-code failures. |
| 15:35:08.189397 | Retained failure: register/engine_query/body, COMMAND_FAILED. |

The2,105-byte retained failure has SHA256
`950ed783f48bdfc289343abffe5c98b3750901d223233e48caeee8f2334fa2f5`.
It records CalledProcessError,0.065945s elapsed/8s budget, four calls, no dropped calls.
Its timestamp follows the initial watchdog and engine stops; it is not proof that
registration or persistence initiated the outage. Effective watcher unit SHA256
`659b954beb67d1e23c0cea45ffda62704f48dc2fb0b1f5bd30d0ae733760bd4e`
and gateway SHA256
`9023d2c3f7c3a5127d67c509a16eb2d974810ff54d5b76cc225cd9b93e0b4234`
match the accepted foundation. The later resource sample has7,519,301,632 free bytes
and1,289,424KiB MemAvailable; this does not reconstruct resource conditions at failure.

Metadata work's last short health sample15:33:19UTC still showed the old watcher/AWG/TCP
PIDs active with zero restarts. Candidate nginx syntax checking completes15:38:07UTC,
after the recorded transport failure, without HUP/container restart or live-file
replacement. No new release asset, catalog, paid policy or server runtime is activated
in this interval. The evidence does not establish the cause of the initiating delay.

Public metadata delivery is held. Installed126's completed offline/online revocation
and original-card cleanup remain valid earlier observations; no fresh broad protected-
data equality or restored VPN is claimed. Resume recovery only as the separately
coordinated [guarded procedure](../operators/subscriptions.ru.md), preserving accepted
paid-v2/metadata/HMAC2 and current user data. Do not simply restart the watcher.

## Earlier outcome at12:06UTC: RECOVERED_CAUSE_OPEN

After the read-only diagnosis, the owner explicitly confirmed a separate controlled
RU recovery on the existing runbook, without new runtime code, HMAC2 changes or
subscription/user-data changes. Recovery runs from source documentation checkpoint
26b267625a52781fe1589b15703500b81e5b3786; the dirty primary checkout is untouched.
This is service restoration on accepted bytes, not a permanent watchdog/latency fix.

### Fresh guards, backup and recovery

At11:51:57UTC accepted runtime hashes listed below, effective units, ownership and
private-parent permissions match. Root free space is7.02GiB; MemAvailable1,211,020KiB.
RU/operator generation2 key agreement is checked in-process without exporting keys.
HTTP remains active from11:40:07 and its process/invocation stays unchanged throughout
recovery; no further concurrent HTTP action is observed. Peer service also remains.

A fresh consistent canonical SQLite backup is restored in isolation: integrity,
foreign keys, all27 table fingerprints and exact-runtime paid projections for all
three nodes at the same clock pass. Backup SHA256:
`f3e9240de5939d0c81e3b376f4bd1dbf9e62fae143504f92492a3f4d369e7bd4`.
The pre-start native state/config/peer backup is copied offline with AES-256-GCM;
203,650 encrypted bytes, SHA256:
`8f8da951cb6d208b65ecddcf789a03782051e1110778d5dc0ff82f39b97ced0f`.
Decryption/digest roundtrip passes; key and raw evidence stay in the protected local
contour. No backup is restored over live data.

At11:52:56UTC the RU-only command fence is in place, NL entries are unchanged and
central reconciliation continues. Current work is drained; grouped watcher/AWG/TCP
stop reaches PID0, no jobs and zero gateway handlers. Retained-state validation
passes with66 records/20 peers before startup. The first-failure bytes are preserved
without overwrite. At11:54:45UTC the unchanged watcher, AWG and TCP are started
sequentially; original three-node command-map bytes are restored. No HTTP, peer,
paid-reconciler timer, local support worker or panel restart is issued by recovery.

### Initial continuity failure and separate convergence anchor

The first continuity check **fails**: TCP changes PID after the startup receipt.
That failure and the original receipt remain retained, not relabelled PASS.
The paused cohort deadline was11:54:26UTC, before the11:54:45 start. The ordinary
11:55:12–18 reconciliation renews admission; TCP restarts at11:55:14. Accepted
`Gateway.plan()` excludes expired admission at startup and `apply_serialized()`
restarts TCP when configuration changes. The paused and post-renewal20-client
id/email/flow dictionaries match exactly. The intermediate configuration was not
sampled: no claim of an observed19-client intermediate set is made.

Watcher/AWG/HTTP/peer process and invocation remain unchanged, no new failure record
appears, and subsequent reconciliation applies all three nodes. Only after those
checks a separate post-convergence anchor is recorded. All original continuity,
actual/persisted, identity, protected-data and lease assertions are rerun against
that anchor; none is removed. This is not an unbroken startup or a restart retry.

### Six strict observations and preservation

| UTC | Records / AWG / TCP | Attempt age, seconds | Cohort deadline UTC |
| --- | --- | --- | --- |
| 12:00:31.247 | 66 / 20 / 20 | 1.247 | 12:02:17 |
| 12:01:35.178 | 66 / 20 / 20 | 1.179 | 12:03:25 |
| 12:02:11.968 | 66 / 20 / 20 | 0.968 | 12:03:59 |
| 12:02:48.562 | 66 / 20 / 20 | 1.562 | 12:04:33 |
| 12:03:25.041 | 66 / 20 / 20 | 1.041 | 12:05:07 |
| 12:04:01.731 | 66 / 20 / 20 | 1.731 | 12:05:40 |

The210.483s window crosses the first observed deadline and exceeds120s. All revisions
are applied; actual AWG/TCP sets and TCP bindings match persisted decisions. Watcher,
AWG and TCP remain active with stable processes/invocations and NRestarts0 throughout
this window. Original command map and generation2 files remain unchanged.

Fresh12:06:35UTC preservation readback compares full table fingerprints, not only
historical counts:

| Protected canonical domain | Before | After | Fingerprint |
| --- | --- | --- | --- |
| devices | 66 | 66 | unchanged |
| invites | 121 | 121 | unchanged |
| paid_beta_subscriptions | 1 | 1 | unchanged |
| paid_beta_events | 4 | 4 | unchanged |
| chat_bindings | 53 | 53 | unchanged |
| chat_service_senders | 1 | 1 | unchanged |
| referral_links | 19 | 19 | unchanged |
| referral_claims | 59 | 59 | unchanged |

All66 retained transport identities, membership, terms and prepared state match;
normal renewal/observation timestamps are compared separately, not mistaken for
data loss. Six effective unit definitions are unchanged. Original command-map SHA:
`d07803df7c82d4dfabd6eb1131d8c9132a1df8f1a84f2103ca33fe13a5d48b11`.
Generation2 manifest digest:
`8602e6526ca1ec0e408c99a7ca37aedc4413b417f392e32096d5167517fcdcb8`.
RU/operator active keys agree inside the protected process. Archived first-failure
hash remains83daf777; no replacement failure appears. No old key, database, timeout
or policy is installed. Public125/catalog8 and paid108/119/123/125 are unchanged.

### Support, panel and a separate existing projection gap

Local support worker stays active without restart. Read-only support IPC confirms
cursor4, baseline position4, excluded-events4, original baseline time14November
12:48:20UTC and baseline-position hash equal to cursor anchor; source_error is null.
The selected existing device has no notification jobs. This is not a full encrypted
message-history comparison or global-job-count proof. No test payment, term change,
support message or notification is created; new notification delivery is NOT_OBSERVED.

Panel stays on image5ae92f8c with generation2/manifest8602e652. Normal RU transport
observation12:02:08/import12:02:09 reports ok/66 records on node125c796a; inventory
and metadata imports are fresh. Both NL transport sources report ok/66 records.

However, subscriptions snapshots are **unavailable**, last success15November
13:47:21UTC/66 devices. Structured read of the existing source configuration finds
its expected archive SHA still
`617c7d752a20631d624b301c59142af34f3624483a5d2d5adc2a7c7722dd74b1`,
while installed metadata HTTP is70a924db. The collector rejects that mismatch before
canonical import. This is a pre-existing stale producer pin, not erased subscriptions
or a recovery-induced change. The earlier broad metadata receipt claim of fresh
subscription imports is corrected by this readback. Canonical data/enforcement and
notification cursor remain preserved. No source pin is changed in this RU-only task.
Metadata follow-up must validate provenance, atomically update this exact pin while
preserving other fields/permissions, then verify normal import and fail-closed pins.

### Limits and recovery posture

Root cause remains open: the incident evidence below shows watchdog ordering and
concurrent I/O delay, not causal attribution. No observer, pressure workload, runtime
fix or restart loop is introduced. Physical client traffic and RU/AWG geography are
NOT_RUN here. No phone/network/consent setting changes; no APK or paid126 publication.
There is no active fence left to undo. On a new incident use fresh guarded recovery,
not a stale DB restore or automatic old-key rollback. Metadata release does not
resume automatically from this incident closeout.

Closeout qualification: documentation checker passes6 files/851 links with zero
errors; whitespace and staged secret/raw-identifier checks pass. Review is the
author's own. No new runtime source or full CI qualification is claimed by this
documentation-only change; operational checks are the separate receipts above.

## Historical diagnosis: NOT_RECOVERED / CAUSE_OPEN at11:42UTC

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

## Historical recovery boundary before owner confirmation

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

Initial diagnosis documentation checks:6 changed files/849 links, zero errors; whitespace and staged
secret/raw-device-ID pattern checks pass. Review is the author's own; no runtime
or independent review PASS is claimed by this documentation checkpoint.
