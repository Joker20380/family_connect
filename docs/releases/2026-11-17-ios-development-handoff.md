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
is retained in checkpoint `2ea1f6f2e9c995e9611c7648cac87630951a1dc7`.
macOS run44023861642 builds both unsigned targets successfully, then **fails**
`isolated.cancelled-native-must-not-start-successfully` with handles0, exactly as
predicted. Downloaded artifact14302731166 ZIP SHA256
`a01da92536bc1da02a35fb0d731bd4d5962894375501b5c510b9534e5bb1a47e`.
No unchanged retry. This is baseline failure evidence, not acceptance.

Implementation candidate0.0.1/build2 adds native serialized CommitStart after
settings completion; fresh control-queue status; stop returns retained first error.
Provider generation cleanup joins native resources, isolates old callbacks, and
blocks overlap while a system settings callback remains outstanding. Manager uses
load/find/save/reload/session APIs; status is observed NEVPNStatus, not start return.
Keychain immutable bundle/reference handoff, strict offline existing trust checks,
AfterFirstUnlockThisDeviceOnly policy and parameterized manual development signing
are implemented. No common Android/desktop transport runtime change. New Swift
checks cover deterministic stale handoff, settings error, provider cleanup/recreate,
fake preferences save/reload/permission errors and fake Keychain denial/corruption.
These models do not prove system VPN preferences or interprocess Keychain sharing.
Go tests generate fresh synthetic certs/CRLs in memory, never stored as artifacts.
No old assertion or test budget weakened; a new10s initial path eligibility deadline
is distinct from unchanged180s native startup.

Self-review follow-up: preserve BridgeFailure numeric code across NSError/process
boundary, read actual last disconnect error with generation guards, expose file
import failure safely, test cancellation during reload as well as save, and verify
development provisioning grants with synthetic Python models (including a valid
App ID prefix different from Team ID).9 project/provisioning tests pass locally.
This is not real signing or cross-process Keychain acceptance.

## Gates

New device/simulator builds, native coordination, provider/manager/material tests:
PENDING. Real VPN preference installation, extension launch, interprocess Keychain
sharing/provisioning, physical routes/memory/background, Telemost/whitelist: NOT_RUN.
Public beta126/catalog9 and production unchanged. No release signing or installation.
Rollback is source revert; development stage is not a rollout.
