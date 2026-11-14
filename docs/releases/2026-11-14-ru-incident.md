# RU service recurrence — 14 November 2026

## Outcome and scope

Owner requests investigation and repair of stopped RU services. Native AWG/TCP
availability is restored at **10:36:19.175UTC**; final readback at10:52:23.969UTC
passes. **RECOVERED_CAUSE_OPEN**, not permanent prevention of storage stalls.
A separate legacy peer-worker name collision is repaired at10:46UTC. Only Family
Connect on185.251.89.19 is changed; no NL, neighbouring service, phone, payment,
release, firewall, filesystem mount, disk scheduler or timeout policy is changed.

The dirty, divergent main checkout and parallel subscription work are preserved.
Documentation uses the clean existing `fix/ru-watch-lifecycle-20261109` worktree,
fast-forwarded to current origin/main before this change. This is an operational
receipt, not a new application-source release or installation of current main.

## First failure and timeline

Original first-failure SHA256:
`3c341059f2805818a022f4d8c29db71cc4996b9f556a1636c38202d8a72e1912`.

At **03:03:41.800280UTC /06:03:41.800280MSK**, the watcher records
`TRANSPORT_OPERATION_DEADLINE`, mode `watch`, phase `persist_file`, boundary
`after`, `TimeoutError`. Total operation9.314666s exceeds the8s budget. Three
completed engine queries take0.002384/0.022143/0.002561s. The next call, decision
state **file fsync**, takes **9.278200s**, with only0.000360s self CPU, zero major
faults and `replace_completed=false`. This is not a slow TCP query, completed
state replacement, or the previous day's multi-call persistence sequence.

The active journal file independently records AWG stopping03:03:41.827778UTC,
TCP stopping41.844014 and stopped41.856875, watcher exiting1 at41.906314, and AWG
stopped41.959934. The watcher retries at03:03:47.079277, but does not restart the
stopped dependent engines. Thus this incident is explicit fail-closed shutdown
after the operation deadline, not a12s watchdog termination first. The initial
protected snapshot finds763 watcher restarts with both engines inactive.

Broad bounded original-invocation/kernel journal queries reach their5s limits.
Reading only the active journal later succeeds:97 incident-window records;
the invocation-filter query returns zero. Missing invocation output is not proof
that no failure occurred. The persistent first-failure record and systemd stop
timeline are separate evidence, retained without rewriting history.

## Storage evidence and causal limits

The06:00–06:10MSK sysstat interval containing the failure records:

- virtual disk `vda`: await62.59ms, queue1.35, write219.56KiB/s,20.84 operations/s;
- CPU iowait7.31%, steal0.48%, idle77.70%; I/O full pressure8.91%;
- memory full/some pressure0%, available memory about1.21GiB;
- swap in0.02 pages/s, swap out0, major faults0.03/s.

Unlike13 November, these measurements do **not** corroborate substantial memory
pressure or swapping. Root storage has7.3GiB free/74% used. Low throughput does
not exclude a long-tail flush stall. Current mount is ext4 with `discard,commit=30`;
virtual-disk scheduler is `none`, write cache `write back`. These are observations,
not proof that mount options, a specific writer or the provider caused the stall.
They are not changed speculatively.

A bounded15s per-process sample after recovery finds journald471040 bytes written,
watcher344064 and filesystem journal118784, with no heavy competing writer in that
sample. It does not reconstruct the initiating event or prove absence of earlier
contention. The kernel ring tail is dominated by UFW records; it is not a complete
historical kernel/OOM audit. No disk benchmark, cache drop or broad tuning is done.

## Native transport recovery and validation

The accepted recovery procedure captures fresh private evidence, fences only the
central `gateway-ru` command, drains its cycle, stops watcher/AWG/TCP together and
checks PID0/no jobs/no remaining handlers. Retained state is validated without
resetting decisions or extending authorization. Original first-failure bytes are
archived without replacement; the unchanged runtime is started sequentially.
The exact three-node command map is restored10:36:20.839UTC; NL reconciliation
continues and the central timer remains active.

Six samples over196.492700s pass: stable invocations/PIDs, NRestarts0, fresh ordinary
`applied` readback,64 records/20 allowed, unchanged bindings and exact persisted TCP
id/email/flow set. Actual cohort admission advances1794652663→1794652871, crossing
the initial expiry and finishing before the renewed expiry. Final10:52 readback
still has the same PIDs, no new first failure and attempt age1.969s. Panel RU
snapshot is `ok`, observed10:39:06/imported10:39:07.666UTC; panel HTTP200.

Original versus post-both-repairs fingerprints match for64 devices,118 invites,
1 subscription,4 paid events,52 chat bindings and1 service sender. Support
configuration, keys, root authorized_keys, actual code, effective transport units,
operator pointer and exact command map remain unchanged. HTTP PID3916809 is not
restarted. Policy stays `android-paid-108-119-123-125-v1`;8/12/120s is unchanged.

| Installed component, unchanged | SHA256 |
| --- | --- |
| Native node | `125c796a30c3fba1772c47b96963517350087ad04aad675b6f33a31a5383276c` |
| AWG gateway | `9023d2c3f7c3a5127d67c509a16eb2d974810ff54d5b76cc225cd9b93e0b4234` |
| Paid125 HTTP overlay | `617c7d752a20631d624b301c59142af34f3624483a5d2d5adc2a7c7722dd74b1` |
| Paid125 operator | `a7c801dba6a09e35c9ca7a6e6d816bbb57bc4f483404d44b5ee7f641e70cac15` |
| Paid125 reconciler | `40e1d7212b158fa01e4e4a92c0b635a910ae05b8b350840c07629629108b7aeb` |

**USER_TRAFFIC NOT_RUN**: no physical-client DNS/HTTPS/egress acceptance is inferred.
Android public/installed125/catalog8 and other client distribution remain unchanged.

## Separate legacy peer-worker repair

The host supervisor has over21200 restarts, exit125. Its active journal proves a
Docker name collision with the old29 September container. Docker reports that
container as running, but its recorded PID does not exist and `docker top` returns
`NotFound: task ... not found`. This is not a second live worker. Its exact image,
command, read-only root, bind-only mounts and sole local RU pilot gateway are checked;
no external/NL target is introduced. It is not established why the old task vanished.

Private inspection, original effective unit and consistent legacy product DB backup
are retained. A temporary runtime-only override prevents retries and clears ExecStop
while stopping the failed supervisor. After PID0/no jobs and a second orphan check,
only that exact taskless container record is removed. No image, bind mount, DB, key,
profile or unrelated container is deleted. The temporary override is removed;
the byte-identical effective unit is reloaded and started normally.

New worker starts10:46:12.099UTC on the same image/command/mounts. Two readbacks
20.186s apart find the same live PID, NRestarts0, and eight recent successful cycle
records each; these overlapping windows are **not**16 distinct cycles. Native
watcher/AWG/TCP and HTTP PIDs are unchanged during this repair. Effective worker
unit SHA256 is `d9166b6fc676d5154e9c639256f110d0ba9283c374b40540143297c543ca0850`.

The first repair driver finishes mutation but queries before Docker creates the
new container and exits on that startup race. A separate readback proves successful
startup; repair is not repeated. The first verification then rejects list-order
differences in mounts; normalized exact mount-set comparison passes separately.
Both initial failures are retained, not relabelled PASS. Docker still reports its
existing `unhealthy` flag despite successful worker cycles: the inherited API-image
probe calls `http://127.0.0.1:8080/healthz`, while this process is a reconciliation
worker with network mode `none`; the last five probe exits are1. No API server is
started merely to satisfy that probe. Full container health acceptance is not
claimed. No claim links removal of this restart loop causally
to eliminating the native transport fsync stall.

## Recovery paths and remaining gates

Private evidence: ignored `state-client-build/ru-incident-20261114/`; remote retained
state `/opt/apps/family_connect/private-ru-incident-20261114/`. Modes restrict raw
records, command maps, backups and inspection data; none are committed. The initial
sandbox SSH failure is preserved separately before the approved outside-sandbox retry.

No new native application code is deployed, so no code rollback is required. On a
repeat failure, preserve its first record and current state, then use the same guarded
RU-only recovery; never restore an old business DB or silently bypass a failed gate.
For the legacy worker, stop only its unit if needed and inspect current state; do not
run a second worker/timer or recreate the stale container metadata. The private backup
is recovery evidence, not permission to roll back live product records.

The availability repair is verified, but permanent prevention of the storage stall
is **OPEN**. Next needs storage/provider attribution, a qualified persistence/recovery
change preserving durability/fail-closed behavior, or an authorized replacement RU
host (still WAITING_FOR_HOST). Disabling fsync, increasing enforcement deadlines,
unqualified automatic restarts or reinstalling failed PR16/17 candidates is not a fix.
Physical traffic, long-duration stability and the legacy Docker healthcheck remain
distinct checks. No unrelated queued implementation is started.

Documentation validation: `scripts/check_public_docs.py --all` checks797 files and
5038 local links with zero errors; external URLs are enumerated, not fetched.
`git diff --check` passes. No source/package changes or client builds are made;
live gates are recorded separately from unit-test or platform-CI acceptance.
