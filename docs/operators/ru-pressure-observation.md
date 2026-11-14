# Finite RU persistence-pressure observation

This is diagnostic collection, **not a persistence fix or recovery**. It changes no
gateway code, state, lease, engine, paid policy, support or notification data. Use
only authorized RU185.251.89.19 (`box-932982`), via the existing administrative path,
never the read-only collector key. Do not restart healthy transport for observation.

## Pinned prerequisites and information collected

`scripts/ru_pressure_observer.py` checks root, hostname, RAM-only `/run`, root0700
output parent, fresh run directory, live watcher PID and the actual accepted node
125c796a30c3fba1772c47b96963517350087ad04aad675b6f33a31a5383276c plus gateway
9023d2c3f7c3a5127d67c509a16eb2d974810ff54d5b76cc225cd9b93e0b4234. An existing first
failure prevents a new run. Stop and preserve it before controlled RU-only recovery.
This is deliberately not compatible with an arbitrary main/candidate runtime.

The companion BPF program observes only that watcher PID: file fsync, directory
fsync and rename durations/return values, logical bytes written to the two known
pending files, and AWG/Xray child lifetimes. Child lifetime is fork→leader exit,
**not** the complete gateway query/parse duration. The original gateway failure's
`calls` remain the authority for complete engine queries and operation budget.
An initial unclassified syscall is retained as phase0, not attributed speculatively.

Every5 seconds, collect cumulative host CPU/vda counters, PSI, selected memory/swap/
VM counters; per-PID start identity, comm, CPU/RSS/swap, major faults and read/write
bytes; cgroup memory/events/io/PSI. Rates must use actual monotonic sample intervals,
PID+start_ticks and boot ID, not wall-clock ordering. At most512 PIDs/64 cgroups;
sampling races and omissions are explicit. No argv, environment, buffer contents,
keys or user messages. Applied-state observation retains only times/counts/lease
bounds, no identities. Timer names/times are metadata, not command arguments.
PF_KTHREAD kernel threads retain stat/CPU/fault counters; only jbd2 additionally
reads per-thread I/O. Kernel threads do not have user RSS/swap, so reading their
status/cgroup files is unnecessary. `kernel_io_sampled=false` explicitly marks
other kernel-thread I/O as unsampled, not zero. All user processes retain I/O,
RSS/swap and cgroup sampling; host disk and cgroup totals cover shared writeback.
Tasks that start and exit between counter samples can be missing from per-PID
deltas; do not equate the sampled process sum with host/cgroup total I/O or use
absence in a sample as proof a process did not run.

## Limits and triggers

- Duration180..86400s, chosen before launch; no automatic repeat/restart or reboot
  enablement. Production collection is one24-hour maximum window.
- Five-second polling after each sample; last60 samples and4096 phase records in RAM.
- Compact sample≤96KiB plus timing fields. Each immutable JSON capture≤8MiB; only
  start/first-slow/final files. The tracer's stderr is hard-limited to1MiB, the unit
  to9MiB/file; bounded receipts plus tracer errors total≤18MiB, exclusively tmpfs.
  No per-cycle disk writes. Budget trimming avoids repeated serialization of a whole
  sample for every omitted PID.
- First phase≥500ms saves `slow.json` once. First gateway failure saves a sanitized
  copy/hash in `final.json` and stops; the original persistent first failure is never
  replaced. Normal expiry also saves the last window and aggregate phase totals/maxima.
- Stop on watcher PID/start identity change, available RAM<256MiB, sample CPU>200ms
  or sample wall duration>10s, missing phase events after45s, tracer exit/error, operator
  SIGTERM, or deadline. Visible stop reason is not a root-cause diagnosis.
- Unit hard limits: CPUQuota10% of one core, MemoryMax256M, MemorySwapMax0, TasksMax24,
  Nice19, IOWeight1, IOSchedulingClass=idle, KillMode=control-group, TimeoutStopSec8.
  RuntimeMaxSec is chosen duration+30s. BPF maps≤256 keys/map, perf ring8 pages/CPU.
  A hard OOM/kill may prevent a final receipt; unit result and original failure remain
  evidence. RAM captures do not survive reboot: retrieve before reboot/recovery.
  Unit CPU accounting/quota does not measure all in-kernel BPF probe overhead;
  do not describe the measured unit CPU as total host instrumentation cost.

## Qualification, launch and extraction

Run `python -m pytest -q tests/test_ru_pressure_observer.py`. Copy the exact qualified
two files into a new root-owned directory, verify SHA256 against the accepted source,
and first run180s with the same quotas. Do not install a full archive or edit any
existing unit. Compare loaded hashes, PID/invocation, original failure, protected
canonical fingerprints, applied/engine state and lease renewal across its initial
deadline. Inspect phase completeness, dropped events, sample CPU, memory and actual
read/write byte deltas before authorizing the longer window. A quota-limited wall
delay is not itself collection CPU cost or proof of gateway I/O pressure.

Use a unique transient `family-connect-ru-pressure-*` unit and fresh
`/run/family-connect-ru-pressure/<run-id>` directory. Exact qualified source hashes,
unit, start/deadline and output path belong in the dated task report. Check MainPID,
Result and final receipt, not just ActiveState (an exited retained unit is not running).

Read `start.json`, optional `slow.json`, `final.json` and bounded errors using the
existing administrative SSH into a private local0700 directory. Preserve all files
and SHA256; do not commit raw process/cgroup counters or identity-bearing snapshots.
Never output SSH credentials. Retrieve once after the deadline or immediately after
the first-failure stop. Correlate phases with adjacent counter deltas; high iowait or
one correlation alone does not identify a competing writer or provider fault.

Safe disable: `systemctl stop <exact-observer-unit>` only. It stops the diagnostic
process group and leaves captures, gateway, original failure, queues, baseline and
all databases untouched. No database restore or old worker rollback is involved.
Do not change neighbour applications, run disk stress, induce swap, remove fsync,
increase8/12s budgets or extend120s access leases to make the graph look better.

## First window — 14 November 2026 (stopped by cost guard)

PR29 merged59cd72ed, exact source43eb84eb76871ae907a64f2fef4934f04cf8385f.
Only two verified diagnostic files and a manifest are staged in
`/run/family-connect-ru-pressure/source-43eb84eb` (root0700/0600). No persistent
application file or existing systemd unit is replaced; no application backup/DB
restore is needed for this additive, volatile diagnostic switch.

- Unit: `family-connect-ru-pressure-20261114-43eb84eb.service`, Restart=no.
- Output: `/run/family-connect-ru-pressure/20261114-43eb84eb`.
- Start14November14:19:15.976UTC; deadline15November14:19:15.976UTC.
- Actual stop14November14:25:05UTC after349.88s: one sample used306ms CPU>200ms.
  No gateway failure,151 complete cycles,604 fsync, zero lost indications. Full
  final receipt extracted under label`first-window-final`; the original maximum
  deadline is no longer an active collection. A lower-cost kernel-counter path
  passed a separate181.99s qualification with the same limits before reactivation.
- Safe disable on RU: `systemctl stop family-connect-ru-pressure-20261114-43eb84eb.service`.
- Prepared extraction on the owner's laptop, using the existing administrative
  SSH path without printing its credentials:

```sh
python3 /mnt/data/fc-ru-persistence-pressure-20261114/collect_result.py final-20261115
```

It preserves exclusive private receipts and verifies SHA256 of downloaded files in
`/mnt/data/fc-ru-persistence-pressure-20261114/extracted-final-20261115`. Use a fresh
label for another observation, never overwrite a prior result. Extraction was
tested with label`acceptance-20261114`: start/first-slow/errors downloaded and hashes
verified. A running unit without final receipt is reported as such, not completed.
Do not reboot before retrieval. No background task promises automatic analysis;
the next task turn must inspect the saved finite result.

## Active refined window — source38e9f403

PR30 mergededd10793f43f866c7add806d0a1609b0b43e42e8. Reviewed/qualified source
38e9f403913ee7a73e6eb309bbe0d445d11f0494 is staged separately at
`/run/family-connect-ru-pressure/source-38e9f403`; old captures/source remain intact.
Script SHAebd64d14346385cb1e98b754dab3b34ed7dfde1ba0e9790f72250c8451d5c0ff;
unchanged trace SHA49f96235b61eee6b3b9e03033880b6391f6cf48e984ce7ac0aede8571fa2de90.

- Active unit: `family-connect-ru-pressure-20261114-38e9f403.service`.
- Output: `/run/family-connect-ru-pressure/20261114-38e9f403`.
- Start14Nov14:40:35.898UTC; normal deadline15Nov14:18:46.898UTC.
- Same limits; remaining duration is calculated from the first window's deadline,
  less30s headroom. Hard ceiling remains15Nov14:19:16UTC, not a reset24-hour budget.
- Disable only this diagnostic unit:
  `systemctl stop family-connect-ru-pressure-20261114-38e9f403.service`.

Extract this window (not the former43eb84eb one) on the owner's laptop:

```sh
python3 /mnt/data/fc-ru-persistence-pressure-20261114/collect_refined_result.py final-20261115
```

The exclusive destination is
`/mnt/data/fc-ru-persistence-pressure-20261114/extracted-refined-final-20261115`.
Use a new label on a second extraction. Check stop reason/complete JSON, not just
systemd's success status: a cost-guard stop is successful data preservation, not a
completed24-hour window or proof the RU cause is solved.
This exact refined extraction path was tested with label`acceptance-20261114`:
start/errors downloaded with digest verification; unit still running/no final
receipt was reported honestly. At14:47:24UTC it had run408s with unchanged limits,
empty errors,87.47MB peak and no process disk I/O. Do not infer tomorrow's outcome.
