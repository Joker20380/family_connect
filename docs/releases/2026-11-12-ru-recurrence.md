# RU recurrence — 12 November 2026

## Status and authorized scope

Owner reports stopped RU services again. Controlled recovery and the post-recovery
observation/protected-state comparison PASS: **RECOVERED_CAUSE_OPEN**.
This is an availability incident, not a release or a completed root-cause fix.
Only the authorized RU gateway was operated. No NL/excluded host, neighbouring
application, phone, client release, support message or public announcement changed.

Source documentation baseline is main/PR22 `c58ab7c8`. Runtime is deliberately not
equated to main: the accepted node and gateway remain unchanged, including the
existing watcher `Restart=on-failure` and optional-stderr-null drop-in. The failed,
rolled-back PR16/17 candidates were not retried. The support-compatible HTTP overlay
must remain installed; replacing it with the old archive would break the additive
support schema.

| Component | Unchanged SHA256 |
| --- | --- |
| Node `friends-awg/paid-transport.pyz` | `125c796a30c3fba1772c47b96963517350087ad04aad675b6f33a31a5383276c` |
| Gateway `friends-awg/awg-gateway.py` | `9023d2c3f7c3a5127d67c509a16eb2d974810ff54d5b76cc225cd9b93e0b4234` |
| Watcher unit, excluding its unchanged drop-in | `e9a9d82841d0d5aa257780660107d9588af80a24b32d604dccf9c81c2730523a` |
| Support-only `private-paid-transport-v2/friends-http.pyz` | `16d96eb767602188e1999052e11cfead8dc1a4b38ae8c15394a61dc9ce7f3503` |

## First failure, not a restarted invocation

The preserved first failure is11 November21:12:13.800732UTC
(12 November00:12:13.800732MSK), original invocation
`14dbcb81395147169ffff8374f12641f`, PID2634771. Its byte SHA256 is
`cda882502520b9b245c296bf3b2e45b3d93977c623a9c96564a0edf98dd1d32d`.
Reason `TRANSPORT_OPERATION_DEADLINE`, exception `TimeoutError`, mode `watch`,
boundary `after`, phase `persist_directory`: elapsed8.651672s against8s.
No recorded calls were dropped.

| Recorded operation | Duration, seconds |
| --- | ---: |
| First AWG query | 0.003382 |
| TCP query | 0.027918 |
| Second AWG query | 0.002836 |
| Decision-state file fsync | 2.710012 |
| Decision-state replace | 0.000160 |
| Decision-state directory fsync | 1.439591 |
| Attempt-result file fsync | 1.378701 |
| Attempt-result replace | 0.546717 |
| Attempt-result directory fsync | 1.897639 |

The four fsync calls consume7.425943s; all three engine queries total0.034137s.
The final directory fsync completes after the deadline with replacement already
completed. This establishes the immediate failure boundary for **this occurrence**;
it is not evidence of a TCP RPC timeout, failed fsync syscall, corrupt data, or a
proven provider/disk hardware fault. Preserve commit-before-ACK and fsync semantics.

TCP subsequently stops21:12:16UTC; AWG reaches failed/timeout21:12:20UTC with status9.
At12Nov10:32UTC both engines are still down, while the restarted watcher looks active
with1347 restarts; by10:37UTC that is1354. An active watcher alone is not VPN health.
The historical watcher-only restart/dependency problem remains, not fixed by another
watcher restart. The separate HTTP and chat-sync timer remain available.

Sysstat interval00:10:02–00:20:00MSK, containing the failure, records vda await135.95ms,
I/O wait9.29%, swap-in/out16.11/36.86pages/s, major faults16.21/s, I/O full pressure
9.72% and memory full pressure4.84%. This supports host storage/memory contention,
but ten-minute aggregates cannot identify the competing writer or exact stall cause.
Current pre-recovery I/O full pressure avg10 reaches56.98%, memory39.81%; root disk
has7.6GiB free, so a full RU filesystem is not the observed cause. A bounded original
invocation journal lookup returns no records; the5s kernel lookup times out. Neither
establishes absence of OOM/kernel errors. No repeated broad journal scan was run.

## Controlled recovery and retained evidence

Private local evidence lives under ignored
`state-client-build/ru-incident-20261112/`; mode0700 directory/0600 files. Raw registry,
identity, profile, command-map and key material are not committed. Original failure
bytes, units, code/member hashes, protected table fingerprints and pressure are
captured before mutation. Prior private recovery tooling is adapted with fresh paths
and current failure/configuration guards, never blindly rerun against old evidence.

1. Atomically fence only `gateway-ru` in the central command map. Preserve exact NL
   command entries and keep the existing central reconcile timer active; allow any
   active central cycle to finish.
2. Stop watcher/AWG/TCP; verify zero MainPID/ControlPID, no unit jobs or gateway
   register/preflight/watch/run handlers. Retain state, attempt, enforcement,
   settings, peer database backup and native engine configuration privately.
3. Validate63 retained records with the installed engine's ordinary operation/lock.
   No ledger, state, deny, prepared record, expiry or registry reset/restore.
4. Archive the exact first-failure bytes using no-replace rename and directory sync;
   reset failed units and sequentially start unchanged watcher/AWG/TCP. Startup
   failures would retain the RU fence and stop, not trigger a blind retry loop.
5. Restore the byte-exact original command map and retain the enabled central timer.

RU fence:12Nov10:37:42.248UTC. Controlled stop10:37:43.443UTC; all three units active
10:37:44.749UTC. Fence removed10:37:46.539UTC. New PIDs are2723464/2723487/2723503,
initial restart counters0. Remote evidence/retained snapshots are at
`/opt/apps/family_connect/private-ru-incident-20261112/`; archived failure remains
alongside the original state under a timestamped `transport-failure.retained-incident-`
name. These are preservation/diagnostic assets, **not permission to roll back live
decisions or restore the product database**. No code rollback was required.

## Acceptance and remaining work

Six ordinary readback samples over196.376549s PASS. Watcher/AWG/TCP remain active,
successful and on the same new PIDs/invocations with restart counters0. Every sample
has a fresh `applied` attempt, age below10s,63 retained records/20 allowed, unchanged
peer bindings and exact equality of persisted TCP clients to allowed decisions
(id, email and flow). The ordinary watcher performs the engine set checks; no extra
manual live query loop or synthetic transport state substitutes for its readback.
No new `transport-failure.json` appears. Cohort admission advances
1794480005→1794480176: the observation crosses the original expiry and verifies the
renewed120s lease, not just a fresh startup allowance.

Final before/after comparisons PASS:63 devices,117 invites,1 paid subscription,
4 paid events,51 chat bindings and1 chat-only service sender are byte-fingerprint
identical at row level. Code, effective units, policy, exact central command-map
bytes, current/paused release pointer, preserved support configuration/key hashes
and root authorized_keys are unchanged. HTTP process2372888 is unchanged. Central
reconcile last run succeeds; its timer remains active. Protected data was compared,
not restored. This does not claim dynamic operational records must stop changing.

Local panel has a fresh `ok` RU snapshot observed10:42:35UTC/imported10:42:37UTC,
runtime125c796a; its HTTP response is200. These checks are distinct from owner-phone
AWG/TCP DNS, verified HTTPS and egress: **USER_TRAFFIC NOT_RUN**. No physical phone
was involved, and root-cause FIXED is not claimed. Continued storage latency can
trigger the same protective stop again; the current watcher loop does not restore
the dependent engines automatically.

Local system disk starts/ends1.7GiB free; data partition starts/ends2.7GiB. This incident
needs only small bounded diagnostics, no build. No caches, logs, release artifacts, backups,
rollback material or user data were removed. Capacity remains a separate warning.

Next correction must address the evidenced persistence/host-latency boundary with
appropriate isolated durability, expiry, fail-closed and package/CI gates; silently
increasing8s/12s/120s or removing fsync is not an accepted remedy. The older query
incidents remain separate unresolved evidence. RU replacement remains
WAITING_FOR_HOST; this recovery does not qualify a replacement.

Keep [SUPPORT-CHAT-1](2026-11-11-support-chat-125.md) at its actual status: backend
enabled, signed private125 not physically accepted/installed, last verified phone123
historical, no production chat send. Public Android announcement delivery and cold
no-cache restricted bootstrap/recovery remain separate NOT_RUN production/field
gates. Subscription-change notifications, payment partner and later Windows/Linux
acceptance remain separate queued tracks, not automatically resumed here.
