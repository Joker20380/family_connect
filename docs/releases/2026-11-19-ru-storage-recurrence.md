# OPS-RU-20261119 — recovery and storage evidence

All incident times below are UTC. Status: **RU availability recovered; underlying
storage-latency cause UNKNOWN / investigation OPEN**. The owner explicitly asked
to repair RU and investigate recurrence. This does not authorize PR45 delivery.
No NL operation, real-payment/message fixture, database rollback or release change.

## First failure and actual shutdown

- First diagnostic at **02:08:06.214296**: watch / persist_file / after,
  `TRANSPORT_OPERATION_DEADLINE`, budget8s, elapsed9.684459s. Required decision-state
  file fsync took **9.637045s**, completed=true, replace_completed=false.
- Three engine queries took approximately3.35/27.87/3.10ms. The observed long stage
  is durable file persistence, not the engine queries.
- Journal records an actual12s watchdog timeout at02:08:06.578867 and SIGABRT.
  TCP stops at02:08:06.599147; watcher/AWG stop timeouts lead to SIGKILL at02:08:11.83.
  Watcher restart1 starts at02:08:17.079934; at least962 restarts are observed
  before the guarded operator stop. No reboot or full filesystem is observed.
- Unlike the18November incident, **an actual initiating watchdog is recorded**.
  The order is long persistence/deadline failure, watchdog, dependent shutdown;
  do not relabel this as a random engine crash or infer a new software fix.
- First receipt SHA256:
  `3df72173917ff5f57e2371a20d88a047f45f3b8e13937ffd7bde27a3a47b71d4`.
  Original inode1064424 is retained under
  `friends-awg/transport-failure.20261119-020806.preserved.json`.

## Guarded recovery on unchanged installed bytes

Readback mode remains **legacy** (`readback_mode` absent). Installed SHA256 pins:

| Component | SHA256 |
| --- | --- |
| Node archive | `125c796a30c3fba1772c47b96963517350087ad04aad675b6f33a31a5383276c` |
| Gateway | `9023d2c3f7c3a5127d67c509a16eb2d974810ff54d5b76cc225cd9b93e0b4234` |
| Paid reconciler | `ff4601aa3bb0990b4f8566aadde1fd6b12120bffbd912b4b901e2d77a114d6aa` |
| HTTP | `4e2df679761ba9e7af74128984ef2e19e8e7b228f1cc85b36d50be2b0bc24ce8` |

1. 11:38 preflight: runtime pins verified;27-table SQLite snapshot and isolated
   restore integrity/foreign-key/paid-projection checks pass. No restore to live DB.
   Snapshot SHA256 `6721e15c8d45cea7f41bc765a27629f284c088c5ab1020a49d6be5a8b27124dc`.
   Off-host AES-GCM encryption/decryption roundtrip passes; ciphertext196886bytes,
   SHA256 `25e77a8282e56cc1d5ba6660fc77785c3aedf63c42d6de361dbc6af9d481e0a7`.
   Keys, backups and raw state remain private, not Git artifacts.
2. 11:40 RU-only command-map fence, reconciler drain, watcher/AWG/TCP stop;
   zero MainPID/ControlPID/Jobs/handlers confirmed. Retained68 records/20peers
   validate. State/config/peer backups retained. NL command entries untouched.
3. 11:42:16–17 sequential watcher/AWG/TCP start; original command map restored.
   HTTP and peer worker are not restarted. No code, unit, timeout, restart-policy,
   collector pin or authority rollback is introduced.
4. **11:43 strict initial invocation-continuity check FAIL**, retained verbatim.
   TCP changed invocation twice: stop/start11:42:27.735/28.029 and
   11:42:43.107/43.509. Journal shows explicit stops/starts, NRestarts=0, not a new
   crash or watchdog. They align with paused-state lease expiry11:42:27 and the
   canonical reconcile11:42:42.460–47.936 renewing eligibility. Installed gateway
   restarts TCP on changed client configuration. Requesting PID was not audited;
   temporal/state agreement is not a complete attribution trace. The strict gate
   remains FAIL, not overwritten by a new starting baseline or a retry.
5. Separate11:47 and **12:24** audits pass actual transport correctness:
   **20AWG/20TCP**,68 applied revisions, latest attempt age0.834s at12:24,
   no active failure, all service NRestarts=0. All settled invocations match across
   those two audits; watcher/AWG/HTTP/worker also match their initial invocations.
   Generation2 files, effective units and command map unchanged; stable transport
   identity/membership/terms/prepared state preserved. Devices, invites, paid
   subscriptions/events, chat bindings/senders and referral links/claims unchanged.
   Lease timestamps can advance through normal authority operations.
6. 11:58 public TLS test with an existing enrolled technical identity: challenge
   and RU configuration HTTP200, pinned-anchor signature verified, identity
   unchanged. No new registration/key/grant. This is **not** a physical-client
   tunnel/traffic matrix; affected-device confirmation is still open.

## What storage measurements establish — and do not

Guest: KVM,2vCPU, about2GiB RAM; root `/dev/vda1`, ext4 with `discard,commit=30`,
virtio device scheduler `none`, WBT75ms. These are observations, not a tuning
recommendation. No mount/scheduler/cache/durability option was changed.

- Sysstat10-minute interval containing18Nov01:49: await75.42ms, queue2.24,
  util13.97%, write288.75KiB/s, CPUidle64.94%, available memory about1226MiB.
  Interval containing19Nov02:08: await69.83ms, queue2.25, util16.3%,
  write293.90KiB/s, CPUidle64.31%, available memory about1158MiB.
  These aggregates support substantial latency at modest guest throughput; they
  **cannot locate the exact9.637s request or prove provider contention**.
- Current watcher/system-slice cgroups show no configured I/O maximum or CPU/memory
  ceiling and zero recorded OOM kills. This does not exclude host/provider limits.
  A selected01:50–02:15 kernel-log filter found no I/O-error/EXT4/virtio/OOM/hung-task
  matches; this is not proof that every layer or all logs were healthy.
- Passive180s eBPF capture11:52–11:55:336 watcher fsyncs, maximum712621us;
  journal-commit maximum644454us correlated with a slow fsync. Blocked stacks
  include `jbd2_log_wait_commit`, `folio_wait_writeback` and `wbt_wait` beneath
  `ext4_sync_file`. The sector-based request matcher had1987 collisions:
  **its block latency estimates are not accepted as exact request measurements**.
- Corrected180s capture11:59–12:02 keys requests by actual kernel request pointer.
  VDA counts:13reads/4734writes/2040flushes/558discards; maximum last-dispatch-to-end
  times12.534/371.885/58.070/14.836ms respectively. Two reissues mean these timings
  are not total residence times for requeued requests.332 fsyncs, maximum85.143ms.
  Both eBPF captures completed and detached; target watcher identity stayed fixed.
- The bounded sampler subsequently caught **12:14:49**, about1.11s sampled fsync
  residence, with `folio_wait_writeback → ext4_sync_file → do_fsync`. Services
  remain healthy. Sampling is not exact syscall timing and did not capture the
  overnight9.637s stall. No successful daytime trace explains that earlier tail.

**Established:** the observed recurrence trigger is required durable persistence
exceeding its existing security budget; live waits occur in the filesystem/storage
path. **Unresolved:** why the underlying persistence occasionally takes8–10s.
Shared journal/writeback pressure, guest throttling and provider backend scheduling
remain hypotheses, not attributed root causes. No evidence justifies weakening
fail-closed,8/12/120 budgets, adding heartbeat or restarting indiscriminately.

## Bounded next-occurrence capture and handoff

Explicitly installed diagnostic only: `fc-ru-fsync-evidence-20261119.service`,
transient, Restart=no, RuntimeMaxSec86400, CPUQuota5%, MemoryMax64MiB, Nice19,
idle I/O class, ProtectSystem=strict. It started19Nov12:06UTC and stops no later
than **20Nov12:06UTC**; it also exits on target replacement/exit, a new transport
failure,5000 records or8MiB. No restart/rearm, heartbeat, runtime-state writes,
network traffic or application imports. Fixed PID plus start ticks prevents PID
reuse. Read-only `/proc` sampling100ms; kernel stack on sampled fsync residence≥1s,
with60s preceding disk/CPU/PSI samples. Output only in root-private tmpfs:
`/run/fc-ru-fsync-evidence-20261119/events.jsonl` (0600; directory0700).
Reboot loses tmpfs evidence. Source SHA256:
`8b6f703e04698f246cd31d6fffc18d519ca8019826f67fffd5e7327cf88b2c8f`.

Next operator action: copy this evidence privately before reboot/loss, compare
any new first-failure receipt with the sampled wait stacks and I/O deltas. Inspect
unit result as well as capture completion; expiry or MemoryMax termination is not
a transport failure. Early stop, if needed, is only
`systemctl stop fc-ru-fsync-evidence-20261119.service`; do not stop/restart the
transport to collect it. No automatic rearm or future assistant run was scheduled.
If another multi-second wait remains unattributable from the guest, request
provider-side volume/flush latency, queue/QoS and host-contention evidence for the
exact UTC window. No provider ticket is claimed sent. Do not modify unrelated
workloads or disk settings on correlation alone.

Private local evidence roots: `state-client-build/ops-incident-20261119` and
`state-client-build/ops-recovery-20261119`; protected remote recovery snapshots:
`/opt/apps/family_connect/private-ru-recovery-20261119-r1`. Retain raw evidence,
including initial diagnostic timeout and strict recovery FAIL. Public anchors:

| Receipt | SHA256 |
| --- | --- |
| First passive trace (matcher limitation retained) | `381591524833f27135bb5682461ed2b6409fd95c2fb536937128f629381fe4f8` |
| Corrected request-pointer trace | `904b169df7728e508095bd604e6251556d991be140f2e4f67620be8aff206017` |
| Diagnostic installation | `e46aa07760c3d6b470a0750ba4d1417fa79e38c43eb7e485ca6c83306af5c5af` |
| 12:24 retained-authority audit | `1892e36fc9762ae1d16971952c4c4615666df1bf728540e31fbc738e461125d0` |

## Accepted source/package boundary remains separate

PR45 accepted `081879602244a782b24c7bf39c6d399d85947255` is merged normally into
`cb47bf230c6795cf21f4e6948253f49aa5377ed0`; parents are
`bc8f7b5b42800269aeb43bcf54059205e7a7cbf7` and accepted08187960; tree
`acada98130090b2fb705c1d0ca54f973a7bb4c0e` matches the reviewed synthetic merge.
Nine head and six automatic main workflows SUCCESS, attempt1, retained in the
[final integration receipt](https://github.com/Joker20380/family_connect/pull/45#issuecomment-6997163178).
Those results are not new CI results for this documentation checkpoint.

Package provenance remains **literal08187960**; node SHA256
`f3eca939b50016eb9844f199adc309513e547e55686a0b029227d1abfe6ef7d0`, manifest
`04fe0ec12aae8af819878d97cfb6ced642928b1fe725d5d1fc001db5d4f40f6a`.
**SOURCE/PACKAGE INTEGRATED; production NOT_DEPLOYED.** The independently retained
first native AWG qualification recovery FAIL remains UNKNOWN; subsequent unwrapped
PASS/NRestarts=0 is not an explanation of that failure or of this storage incident.
Reduced repeated fsync does not guarantee bounded mandatory security writes.

Future delivery is a separate explicitly authorized RU-only operation using the
[accepted runbook](../operators/transport-readback-delivery.md): fresh runtime and
effective/native pins, external fence/drain, stopped units/PIDs/Jobs, coherent
installation, sequential launch and real acceptance. Rollback retains current
authority; never restore an old DB/transport state over newer events. Android
subscription-card auto-refresh stays queued after the server stage.
