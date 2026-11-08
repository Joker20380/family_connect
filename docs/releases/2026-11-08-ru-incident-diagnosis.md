# RU incident diagnosis — 8 November 2026

Owner request: investigate what happened to RU. Read-only inspection of authorized
RU185.251.89.19, approximately22:49–22:55UTC. No recovery was attempted. Result:
**NOT_RECOVERED; initiating failure identified, underlying delay cause open.**

## Entry and provenance

The working checkout is main a531916e with pre-existing tracked/untracked changes,
four local commits and112 upstream-only commits. A non-merging fetch confirms
origin/main967f38f4. Upstream STATUS/PLAN and the RU-TRANSPORT-RECOVERY-2 report were
read because local7 November masking observations are no longer the current state.
The morning8 November recovery and accepted diagnostic delivery supersede those
older observations; they do not establish evening availability.

Installed RU bytes match the morning diagnostic payload, both mtime05:50:15UTC:

- paid-transport.pyz: `f747759cfcf5b2881a18f984c81c95647db90cd30e93eea78e60066826c73131`.
- awg-gateway.py: `9023d2c3f7c3a5127d67c509a16eb2d974810ff54d5b76cc225cd9b93e0b4234`.

No source, binary, client version, installer, catalog or policy was changed. Public
artifacts and installed client versions were not reverified. Previous recovery:
[upstream incident report](https://github.com/Joker20380/family_connect/blob/967f38f4/docs/releases/2026-11-08-ru-transport-recovery-2.md).

## Failure chronology

Times are UTC; systemctl's MSK timestamps were converted rather than treated as UTC.
Journal query bounds explicitly include UTC. Unit JSON ingestion timestamps can lag
source events, so adjacent telemetry arrival times are not used as precise durations.

| Time | Observed evidence |
| --- | --- |
| 05:50:17 | Both ordinary RU engines started after the morning diagnostic delivery. |
| Before21:02:26 | Successful watcher work grows from about0.11–0.22s to0.70–0.77s, then5.659s. The last slow successful pass records5.027s in engine queries. |
| 21:02:26.166 | First diagnostic: watch/plan, TimeoutError, TRANSPORT_OPERATION_DEADLINE, elapsed9.368102s, budget8s. Lock acquisition0.000100s; plan9.367482s; no engine-query/persistence stage in this failed pass. |
| 21:02:26 | Systemd records the12s watcher watchdog and stopping both ordinary engines. The explicit application failure was already recorded. |
| 21:02:27 | TCP exits successfully after stop. |
| 21:02:33 | AWG exceeds its stop timeout and is killed; this is downstream cleanup, not evidence that AWG initiated the incident. |
| 21:02:39 onward | Watcher restarts, but engines remain stopped; startup checks repeat. |
| Final readback | AWG failed/PID0, TCP inactive/PID0; watcher activating with NRestarts188. Earlier active/running watcher snapshots are transient and do not mean VPN is restored. |

The retained first diagnostic is `/opt/apps/family_connect/friends-awg/transport-failure.json`,
SHA256 `6b26e765fb9989cab5fc1f8092f9ab0b11fe0550d2b70ee5642ee762bdbd72c4`.
Only allowlisted diagnostic fields were printed; no private keys, profiles or device
rows were extracted. The first-failure file was not removed or rewritten.

Accepted source explains the persistent outage: a watcher failure requests both
engine stops; BindsTo also stops engines when the watcher dies. The watcher restarts
itself but only checks that engines become active; it does not start them. Therefore
automatic watcher retries cannot replace the accepted operator recovery sequence.
The subsequent paid-reconcile failures are consistent with RU unavailability; their
independent full root cause was not analyzed.

## Host observations and limits

- SSH works, uptime68 days; no host reboot is indicated. Root disk71%,8.2GiB free;
  available RAM approximately800–840MiB of1962MiB; occupied swap893–916MiB.
- One live window shows63–68% IO wait,10–13 blocked tasks and504–940KiB/s swap-in.
  A later window largely recovers to0–6% IO wait. This is intermittent, not proof of
  continuously saturated CPU, exhausted RAM or a full filesystem.
- IO PSI at22:52:50: some avg60=22.23%, full avg60=16.99%; memory some avg60=7.49%.
- Historical sysstat21:00–21:10 averages: disk await85.98ms, queue7.75, IO wait9.58%,
  CPU steal1.37%, read1247.64KiB/s, write306.28KiB/s. Ten-minute averages cannot
  attribute the exact9.37s plan stall to a syscall, workload or provider fault.
- The large discard volume in that interval is explained by fstrim21:03:08–13,
  **after** the first failure. It is not identified as the initiating cause.
- Bounded kernel journal20:55–21:10 has no matching OOM, killed-process, I/O-error,
  segfault or blocked-task messages. This does not rule out transient storage stalls.
- RU HTTP candidate is running, most recently started21:45:59, not by this inspection.
  TLS-verified local8443 request returns404 in0.087s; the guessed `/friends/status`
  route is not an API health endpoint, so no application-health PASS is claimed.
- Port443 and UDP51820/51821 belong to older Docker gateways, not the stopped
  ordinary Friends units. Their listeners do not prove current-client availability.
  The long-standing legacy Docker peer-worker unhealthy status is separate evidence,
  not attributed as the cause of this new incident. No neighboring services touched.

The established mechanism is a bounded plan failure followed by protective shutdown
and a non-restoring watcher restart loop. Storage/paging/scheduling delay is plausible;
the exact initiating workload or blocking operation remains **UNKNOWN**. This is not
evidence of a paid denial, revoked subscription, external attack or provider outage.

## Checks, recovery and remaining work

Checks: pinned SSH, systemd properties and bounded journals, installed SHA256s,
allowlisted first failure, vmstat/free/df, PSI, historical sar and live iostat. Initial
sandbox SSH restriction was handled through approved outside-sandbox execution.
No service restart, unmask, deployment, DB restoration, phone action or NL mutation.
Documentation checks only; no code test or end-to-end VPN acceptance is claimed.

Rollback is not applicable to this read-only session. If recovery is separately
selected, use the accepted RU-only application fence and stop watcher/engines, verify
all PID0/no jobs, then controlled start with existing accepted bytes and retained
restrictions. Preserve the first failure and all cache/deny/bindings; do not rerun
initial preparation or extend deadlines. Verify multiple central cycles, the120s
lease boundary, stable PIDs, engine readback and actual RU AWG/TCP HTTPS separately.
Do not weaken the8s operation budget,12s watchdog or paid enforcement to conceal the
outage. Investigate/qualify any deeper slow-plan correction as a separate change.
