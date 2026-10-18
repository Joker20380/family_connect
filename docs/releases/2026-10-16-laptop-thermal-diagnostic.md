# Local laptop thermal diagnosis — 2026-10-16

## Scope and result

User requested diagnosis of excessive laptop heat. Read-only measurements on
`joker-XPS`, 18:16–18:18 Europe/Brussels (16:16–16:18UTC). This is a workstation
diagnostic receipt, not a release or production health assertion.

The dominant observed CPU consumer was an Android emulator with hardware CPU
acceleration explicitly disabled. Thermal throttling was active during measurement.
This identifies the current workload contributing to heat; it does not establish
that the cooling system is healthy or prove the post-stop temperature response.

## Measurements

- CPU: Intel Core i7-10750H, 12 logical CPUs; kernel `7.0.0-38-generic`.
- Emulator: `qemu-system-x86_64-headless`, AVD `ui60`, PID `1005098`, parent Codex
  PID `20448`; started 18:02:16 local time. Separate from this diagnostic session.
- Observed options: `-port 5580 -no-window -no-audio -no-snapshot -accel off
  -gpu swiftshader -memory 2048`. No KVM device descriptor observed.
- Two six-second `pidstat` samples each averaged 101.66% emulator CPU, approximately
  one logical CPU rather than the entire 12-thread processor. Hot thread `1005177`
  averaged 99.83% in the thread sample. Software graphics was selected, but these
  measurements do not attribute the hot thread specifically to graphics rendering.
- Final package readings at five-second intervals: 99, 96, 99, 86°C; maximum sampled
  CPU frequency 4.208GHz. Reported critical CPU temperature is 100°C.
- Package throttle counter increased by 215 over that 15-second window; core4/10
  counters also increased. Package counters are shared: do not sum per-CPU copies.
- Fans approximately 4,600 and 4,900RPM, near their reported maximum speeds.
- NVIDIA GTX1650Ti: 60°C, 0% utilization, 2.43W, P8, no compute consumers listed.
- Memory: 30GiB total, 20GiB available; only 952KiB swap occupied. Two interval
  `vmstat` readings: no swap traffic, no I/O wait, approximately 90% aggregate idle.
- Power/platform profiles both `balanced`; CPU governor `powersave`, energy
  preference `balance_performance`, turbo enabled. Governor name does not mean
  turbo is disabled.

## Changes, versions and validation

Host commands only read process metadata, counters and device status. Initial
sandbox process isolation hid host workloads; host inspection used approved
outside-sandbox execution. No SSH, ADB, process signal, power/fan configuration,
service restart or MicroTrader operation. Existing repository changes preserved;
only this receipt and STATUS/PLAN notes added by this diagnostic task.

No application version change, build, install, public distribution, catalog signing,
invitation-page change or deployment. Public artifacts were not reverified because
there was no rollout. Product tests were not run: no application code changed.
Rollback is not applicable to runtime state because no runtime setting was changed.

## Remaining checks

1. Ask the owner whether the separate session still needs AVD `ui60`; do not stop
   another session's workload without confirmation. Revalidate process identity
   before any signal because a recorded PID can later be reused.
2. If stopping is authorized, stop that emulator gracefully and remeasure CPU,
   temperature, fan speed and throttle-counter deltas after several minutes.
3. Before a later emulator launch, verify host KVM support and permissions instead
   of silently choosing `-accel off`. No relaunch or host reconfiguration authorized
   by this diagnostic alone.
4. If high temperatures persist at actual idle, investigate ventilation, dust and
   cooling condition. No physical cooling diagnosis has been established here.
