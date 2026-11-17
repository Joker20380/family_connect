# 17 November2026 — IOS-DEVELOPMENT-HANDOFF-1

Source checkpoint, not acceptance. Owner selected startup coordination, provider
lifecycle, VPN manager, secure synthetic-material handoff and development build.
Base remote main bda954fb27ad7115b8c373929cf3e80e84992175 unchanged since PR41.
All5 post-merge workflows SUCCESS (43999095437/95720/95477/95425/95469).
[PR41 exact d02fce99 final acceptance](https://github.com/Joker20380/family_connect/pull/41#issuecomment-6935466490)
remains accepted; new work needs its own checks. Dirty original checkout preserved.

## Requested RU readback first — no recovery

At05:20:30UTC, AWG/TCP inactive/PID0 since01:03:56UTC. Watcher auto-restart/PID0,
432 restarts; later snapshots can temporarily show active while its restart fails.
Bounded single-current-journal read01:02:30–01:05:15 returns24 manager events:
AWG stop01:03:56.231823, TCP stop.250286; both exit successfully; watcher exits1
at.466839, result exit-code. Restart attempts fail after about30s. No watchdog event
appears in this selected window; this is not a whole-history exclusion.

First-failure file1979 bytes, SHA256
e5d769ec262cbbf15defb2d779741d5140ec048a11dd1a343df0d0f64c3263a2:
mode watch, phase persist_file, boundary after, reason TRANSPORT_OPERATION_DEADLINE,
budget8s, elapsed9.593906831s. decision_state file_fsync takes9.538853733s,
self CPU0.00031s,0 major faults,3 voluntary switches; replace_completed=false.
The preceding engine queries take0.005055/0.032449/0.004255s. This identifies the
operation crossing the deadline, not why the block/filesystem sync took so long.
Do not substitute the older watchdog-only attribution for this captured failure.

Current IO PSI full avg10/60/300=2.94/3.51/3.50%; memory full averages0;
memory available1210MiB of1962MiB, swap used478MiB, disk6.8GiB free. These later
snapshots do not attribute the01:03 delay to provider, OOM, another service or our
diagnostics. No broad journal scan, DB/profile/key read, observer, backup, restore,
restart, server policy or neighbouring service operation. RU remains down; a
separately selected guarded recovery/latency investigation is needed, not a longer
deadline or a durability bypass disguised as a fix.

## Startup baseline

Added the requested deterministic real NativeSession(mode1) regression: hold network
configuration completion, cancel native only, bounded wait for terminal, release
configure(nil), require one startup error/no pump/zero handles. Old implementation
is intentionally retained for baseline CI; a failed assertion is expected and must
be retained before the fix. No old test assertion or budget is weakened.

## Gates

New device/simulator builds, native coordination, provider/manager/material tests:
PENDING. Real VPN preference installation, extension launch, interprocess Keychain
sharing/provisioning, physical routes/memory/background, Telemost/whitelist: NOT_RUN.
Public beta126/catalog9 and production unchanged. No release signing or installation.
Rollback is source revert; development stage is not a rollout.
