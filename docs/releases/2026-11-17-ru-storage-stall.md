# RU storage stall and availability — 17 November 2026

**Availability restored at07:42UTC; durable stability fix NOT_ACCEPTED.**
The owner explicitly requests that RU stop suffering recurring service outages.
This selects RU diagnosis/recovery ahead of the separate iOS work. Entry remote main is
`bda954fb27ad7115b8c373929cf3e80e84992175`; the dirty primary checkout and iOS draft
PR42 are preserved. This work does not deploy source, change NL, release126/catalog9,
rotate identity/HMAC or alter paid terms. A successful restart is not a durable fix.

## What caused this particular stop

At07:33:53UTC, AWG/TCP remain inactive/PID0 since01:03:56UTC. The watcher has657
restarts; an intermittent `active/running` during its engine-start wait is not VPN
health. At07:40:34 its restart count is668. The first failure remains byte-identical:
SHA256 `e5d769ec262cbbf15defb2d779741d5140ec048a11dd1a343df0d0f64c3263a2`.

| Original01:03:56 event | Observation |
| --- | --- |
| Mode/phase/boundary | watch / persist_file / after |
| Error | TRANSPORT_OPERATION_DEADLINE |
| Operation budget / elapsed | 8s / 9.593906831s |
| Dominating syscall | decision_state file_fsync:9.538853733s |
| Work before sync | AWG0.005055s, TCP0.032449s, AWG0.004255s |
| Sync self CPU / major faults | 0.000310s / 0 |
| Atomic replacement | not completed |

This record **does** identify the immediate triggering call, unlike older records
which only identified a persistence phase. The deadline is checked after the
syscall returns; Python cannot interrupt an uninterruptible kernel disk wait.
`Gateway.fail_closed` requests both engines stop. The previously retained bounded
manager journal places AWG/TCP stops before watcher exit1 in this event; do not
rename it the16 November22:07 watchdog-first incident. The production watch unit
then retries startup, but does not start its stopped dependent engines. Thus the
outage persists after the original disk delay has ended.

Source `Gateway.readback` also explains the exposure: each successful watch cycle
(2s pause between cycles) commits applied observations and the attempt receipt, using two file fsyncs,
two atomic replacements and two directory fsyncs, even without an authorization
change. Those files also carry durable decisions/receipts consumed elsewhere.
Removing their durability or treating an uncommitted revision as acknowledged is
not an acceptable quick fix. Production still uses accepted node125c796a, not a
new source candidate silently substituted for its installed runtime.

AST comparison of installed and main-source `write`, `readback` and `fail_closed`
matches exactly. `watch` differs only in progress-output handling; its enforcement,
watchdog-after-apply and startup engine-wait sequence agree. The explanation is
checked against the installed archive, not inferred solely from a newer checkout.

## Storage evidence and its limits

Historical sysstat intervals ending01:00/01:10UTC show vda await37.11/80.08ms and
average queue1.08/1.95. Available RAM is1,145,764/1,262,264KiB; swap-in0.01/0.04
pages/s, swap-out0 and direct-reclaim scans0. These10-minute aggregates do not
prove an absence of short pressure spikes, nor identify a responsible process.

A single finite synthetic test on the **same RU filesystem**, before recovery,
creates its own temporary directory, writes only generated zero bytes, and removes
it afterwards. It does not read or modify product state, run a disk stress workload,
install an observer, or scan journals.90 iterations/270 file-sync, replace and
directory-sync calls finish in96.839s, with a1s pause per iteration:

| Call | Median | Maximum |
| --- | --- | --- |
| 64KiB write + flush + file fsync | 0.028560s | 0.774132s |
| Atomic replace | 0.000150s | 0.003223s |
| Directory fsync | 0.013379s | 0.901068s |

Three bounded slow-call samples show the test process waiting in
`jbd2_log_wait_commit` → `ext4_sync_file`, while `jbd2/vda1-8` waits in
`__wait_on_buffer` during transaction commit. This is real kernel-wait evidence for
**this test**, not a reconstruction of the original9.54s wait. It confirms that
otherwise small synchronous writes can wait on the shared filesystem journal.
No sample in this test exceeds8s; it is not a reproduction of the full outage.

Root is ext4 on virtual disk vda, with `discard,commit=30`; ext4 errors_count is0.
About6.8GiB is free. No filesystem corruption or full disk is established. Neither
the mount options nor the presence of a virtual disk establishes a faulty setting,
provider throttling, a noisy neighbour, hardware failure or a particular writer.
No mount/sysctl/IO-priority changes, fsync/barrier disabling, service time-budget
increase or unrelated service shutdown is made on that speculation.

## Guarded recovery

Fresh07:40:36UTC canonical backup passes integrity/FK/all27-table fingerprints and
isolated paid-projection restore for all three nodes. Backup SHA256:
`7be99e190768d54717704036feaec79e5dcf2d076888260a07be38aa234d1293`.
RU-only fence/drain/grouped stop at07:41:31 proves zero PIDs/control PIDs, no jobs
and zero gateway handlers. NL command entries remain unchanged. Retained66 records
and20 registered peers pass validation; no old database or profile is restored.
The paused backup is encrypted off-host with a separately stored local key:
192,136 bytes, SHA256
`8e40ed97d2e0e93e792120cba0b2fb6a1fc902ec156d20ed94ea15508f836ed7`.

At07:42:14 the unchanged watcher/AWG/TCP start sequentially and the original command
map is restored. The original failure is archived without overwriting it. PIDs are
477344/477402/477461 respectively, all NRestarts0. HTTP331790 and peer-worker3967036
remain unchanged from this recovery's entry baseline; support/panel, HTTP, NL and
the reconciler timer are not restarted. First strict07:42:40 readback confirms66
applied records, exact20 AWG/20 TCP actual bindings, current receipts and protected
canonical fingerprints/HMAC2. Thirteen strict observations through07:50:35 span
474.358s with identical process anchors and zero restarts. The initial cohort
deadline1794901459 is crossed and advances to1794901937 through ordinary renewal.
Final07:50:53 readback additionally verifies unchanged effective units, archived
failure, protected fingerprints, identity/membership/terms/prepared-state and HMAC2.
This establishes bounded recovery, not future uptime or client traffic.

## Validation and publication boundary

The13 existing diagnostics/failure tests pass using an environment verified against
both control and device-identity lockfiles. They cover simulated call timing around
real temporary-file operations and first-failure preservation, not a production
storage fix. An initial system-Python collection fails because RNS is absent; this
is retained as an environment failure, then corrected by selecting the locked
environment without modifying any assertion. Source itself is unchanged.
Local documentation links, whitespace and the public-source guard are checked.
The incident/recovery documentation is a separate source change; its CI and author
self-review are recorded on its PR. No source publication deploys a runtime fix.

## Integration and newly selected source boundary

PR42 is accepted at source `af1b37b6`, merge `b3fefac1`; physical iOS and Apple
enrollment/TestFlight are deferred by the owner. PR43 preserves this historical
incident/recovery evidence while merging current main without rewriting history.
Its exact-head checks, self-review and final merge/tree readback are recorded on
[PR43](https://github.com/Joker20380/family_connect/pull/43), not as a runtime fix.
The newly selected RU-PERSISTENCE-READBACK-1 task is isolated source qualification
of an opt-in durability/observation split. It does not authorize production SSH,
deployment, restart or infrastructure work. The next section retains the original
incident decision; it is not a simultaneous instruction to contact hosting.

## Durable-fix decision and next action

The immediate failure mechanism is established: **synchronous durable state write
exceeds the application deadline → protective transport stop → watcher-only retry
cannot restore availability**. The underlying cause of the long storage waits is
still open. Restoring the processes does not meet the owner's durable-stability goal.

The next infrastructure action is to obtain the hosting operator's per-vdisk
latency/throttling/error evidence for17 November approximately01:03:46–01:03:56UTC
and the16 November22:07 incident, and qualify a lower-latency RU storage/host path
if the existing one cannot meet the contract. This report is suitable as sanitized
incident context; no ticket, purchase, new host or migration has been initiated.
Guest averages cannot answer host-backend attribution by themselves.

A software alternative requires an explicit persistence/lifecycle design and
isolated crash/revoke/expiry/ACK/collector compatibility acceptance: separate
security-critical durable decisions from disposable liveness observations, without
allowing storage/lock stalls to postpone expiry or reopen a denied member. It is
not equivalent to deleting fsync calls, putting authority in tmpfs, granting a
longer lease, sending heartbeat independently of enforcement, or installing a
blind restart loop. Even that redesign would not prove immunity to a stalled VPS.

No sustained availability guarantee, client traffic, physical-phone or MESH test
is claimed. Private state, backups, local recovery drivers and raw evidence remain
outside Git. Recovery rollback is the existing RU-only guarded stop/fence procedure,
preserving current state; never restore old keys/data or start an unfenced old node.

Related: [guarded operator procedure](../operators/subscriptions.ru.md),
[previous recovery](2026-11-17-ru-recovery.md),
[persistence contract and earlier uncertainty](2026-11-14-ru-persistence-pressure.md).
