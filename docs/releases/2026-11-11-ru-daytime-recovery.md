# RU daytime recurrence and optional-output mitigation — 11 November 2026

Status: **SERVER_RECOVERED_WITH_OUTPUT_MITIGATION; ROOT_CAUSE_OPEN; USER_TRAFFIC_NOT_RUN**.
The owner requests RU repair and, separately, support-chat production. This report
does not authorize new-host provisioning or claim chat rollout. The original dirty,
divergent checkout is preserved; this uses the existing RU incident branch.

## Overnight failure retained

At10:10UTC, AWG is failed/PID0 and TCP inactive/PID0, stopped since03:11UTC.
The watcher is active but has704 restarts; that is not availability. The original
03:11:05.008UTC first-failure record reports `TRANSPORT_OPERATION_DEADLINE`,
phase `persist_file`, boundary `after`:9.480803s for the unchanged8s budget.

| Recorded call | Seconds | Remaining at entry |
| --- | ---: | ---: |
| TCP live query | 3.201763 | 7.406916 |
| Decision-state file fsync | 1.356407 | 4.195994 |
| Decision-state directory fsync | 1.283848 | 2.646429 |
| Attempt-result file fsync | 1.922825 | 0.442145 |

The final fsync completes late, before replace of that attempt result. Required
durability is not disabled to hide this failure. The parent's recorded calls have
zero major faults; host-wide swap metrics do not prove this process was paging.

Historical sysstat, host MSK converted to UTC: the interval ending03:20UTC has
51.67% CPU I/O wait,50.18 major faults/s, swap37.81/88.66 pages/s in/out,
vda await136.13ms and85.10% utilization. `apt-daily-upgrade.service` ran
03:09:43–03:23:58UTC. This is temporal overlap and direct evidence of slow durable
operations, not proof that a particular package or provider caused the failure.
No system upgrade/timer policy or unrelated service is modified.

## First recovery was not durable availability

At10:13:17.719UTC the accepted RU-only fence, stopped/PID0/no-jobs gate, retained
state validation and sequential start restore the same binaries. The exact original
three-node command map is restored10:13:19.481UTC. Six read-only samples over196.684s
pass:63 records,20 allowed, stable processes, strict normal readback and renewed lease.

The later check fails: AWG stops10:22:20UTC; a secondary record at10:24:10.422UTC
reports an AWG query failure in0.506s after engine shutdown. That secondary failure
is not substituted for the missing initiating boundary. The last saved invocation
logs have a completed3.9656s operation at10:22:00.361UTC and a progress-gap message
received10:22:14.068UTC. The old source uses blocking stderr for both messages.
This supports investigating output delay, but journal receipt timestamps alone do
not prove the exact blocked syscall. A broad system-manager journal read overlapped
this interval and took minutes; it was not repeated. Observer load is not excluded
as a contributor. A final SSH snapshot first timed out during banner exchange; its
later successful retry exposed the outage rather than concealing it.

The original and second records, private snapshots and all unsuccessful checks are
retained under ignored `state-client-build/ru-recovery-20261111b` and `...20261111c`.
Root-only remote recovery directories use the same suffixes under
`/opt/apps/family_connect/private-ru-recovery-*`. Neither database nor cached deny
state is rolled back or cleared.

## Limited operational mitigation

The accepted PR16 analysis already demonstrates that this installed old logger can
block useful progress on a full sink. This operation does not retry the rolled-back
PR16/17 binary or change security timing. It adds exactly:

```ini
[Service]
StandardError=null
```

Installed path:
`/etc/systemd/system/family-connect-paid-watch.service.d/90-optional-stderr-null.conf`.
Safe source copy: `deploy/friends/restricted/ru-watch-optional-stderr-null.conf`.
Only optional watcher stderr is discarded, including progress JSON and tracebacks;
systemd state/results and mandatory durable first-failure/state/attempt records remain.
This is a deliberate observability tradeoff and removes one blocking sink, not a
claim to fix slow fsync, CPU scheduling or the shared host. No other service logging
or global journald setting changes. Replacement/bounded logging still needs its
separate acceptance; future incidents must use small bounded reads, not broad scans.

Second recovery10:44:11.362–10:44:14.671UTC again uses the RU-only fence, full stop,
PID0/no-jobs/drained handlers, retained-state validation, atomic failure archival and
ordinary sequential start. The drop-in is written only while stopped; daemon-reload
and effective StandardError=null/Watchdog12s/Restart=on-failure are checked. The
original command map is restored10:44:16.081UTC. No automatic recovery loop is added.

Unchanged node archive:
`125c796a30c3fba1772c47b96963517350087ad04aad675b6f33a31a5383276c`.
Unchanged gateway:
`9023d2c3f7c3a5127d67c509a16eb2d974810ff54d5b76cc225cd9b93e0b4234`.
The original watcher base unit remains e9a9d828; its effective configuration changes
only through the new stderr drop-in. Operator policy remains android-paid-108-119-v1.
8s operation,12s watchdog,120s lease, fsync/replace/directory sync and ordinary engine
preflights are preserved. NL services, registry identities, device bindings and paid
events are not changed. First-recovery before/after protected fingerprints match.

## Validation and remaining work

Fifteen low-overhead normal-readback observations10:44:37.034–10:54:53.668UTC span
616.634s. Each retains the same watcher/AWG/TCP PIDs/InvocationIDs, NRestarts0,
63 records/20 allowed, a fresh strict applied receipt and full persisted TCP set
matching the decisions. The managed lease renews across its initial expiry.
Protected device/invite/subscription/event fingerprints, original command map,
operator policy and both binaries match before/after. At11:05 the same PIDs remain;
at11:17:04UTC the process fd2 is actually /dev/null, the durable applied receipt is
1.063s old and no new first-failure record exists. Drop-in SHA256:
`94e55b4fb640b7dd6c689b260fbcdc3f14ad9d933ce5451568a94656cd97d42a`.
Panel remains running/healthy/HTTP200 on the unchanged image.
[Sanitized verification](2026-11-11-ru-daytime-recovery.receipt.json).

Neither the finite window nor a null sink establishes long-term stability. Physical
owner AWG/TCP DNS/HTTPS is NOT_RUN. No Android release, signed/public artifact or
update catalog is changed; last-recorded owner beta123 is not operated here.
Runtime/configuration readbacks,
strict two-line drop-in validation, documentation links and whitespace are the scoped
checks; no unrelated historical transport/Android/G4 suite was repeated.

Support work remains separate: source26727eb7, PR18, all three scoped jobs PASS in
[CI43008983724](https://github.com/Joker20380/family_connect/actions/runs/43008983724).
The first43007041835 contract guard failure is retained and fixed through reviewed
support-only UI pins, not an excluded assertion. ARM64 output is still unsigned.
The existing panel imagec179d1ae/database0011 remains installed. Its consistent
backup restores36 tables/929830 rows to a separate RAM-backed networkless PostgreSQL;
that does not commission support or resolve the distinct sender identity. Low local
disk headroom is retained as a rollout blocker, not silently cleared.

## Rollback

Use the same RU-only fence and stopped/PID0/no-jobs/retained-preflight sequence.
Remove only the new90-optional-stderr-null.conf, daemon-reload and verify the prior
effective stderr setting, then sequentially start the same accepted units and restore
the exact original command map. Preserve archived failures, state, denies, leases,
peer databases and protected tables; no old database/state restore. Rolling back
reintroduces the blocking optional output path and is not an availability guarantee.

The permanent fix remains separate from operational recovery: resolve shared-host
resource latency and qualify bounded logging/new runtime on an explicitly authorized
independent host. Do not buy a host, weaken fail-closed behavior, or repeat a failed
runtime rollout automatically to turn this receipt into PASS.
