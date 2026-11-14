# RU-PERSISTENCE-PRESSURE-1 — 14 November 2026

## Entry and scope

Entry main732dabae710b7db03e95e9a2f62d3a4414f3958e; existing clean worktree/branch
fast-forwarded to it. Original dirty checkout and untracked work preserved. Target
is only authorized RU185.251.89.19. Closed beta125/catalog8, tablet update, paid125,
support and sourceac3479bf notification automation remain accepted. No client test,
payment, user message, subscription change or neighbouring application operation.

Read-only entry13:38UTC: actual node archive125c796a30c3fba1772c47b96963517350087ad04aad675b6f33a31a5383276c,
gateway9023d2c3f7c3a5127d67c509a16eb2d974810ff54d5b76cc225cd9b93e0b4234.
Watcher/AWG/TCP active with PIDs3952264/3952267/3952276 and NRestarts0, no new
transport-failure.json, applied state age2.10s. Effective watcher unit hash659b954b;
watchdog12s retained. Main is NOT the installed source: installed gateway module
1800894a differs from main416fa4b1; transport policy160ed03c is identical.
No restart was required or performed. HTTP PID178722/start12:52:41UTC is a separate
observation, not proof of a VPN failure or notification-installer action.

Canonical snapshot retains64 devices/118 invites/1 subscription/4 paid events and
actual policyandroid-paid-108-119-123-125-v1 in serving paid archives. RU disk free
7,804,588,032 bytes; RAM total2,009,584KiB/available1,144,892KiB; swap used400,656KiB.
Entry IO full PSI avg10=6.36%, memory full avg10=0.00%. Laptop capacity is irrelevant.
These instantaneous values do not establish the historical pressure source.

## Established failures and missing attribution

Saved original12 November incident (11Nov21:12:13.800732UTC), invocation
14dbcb81395147169ffff8374f12641f/PID2634771:8.651672s against8s; four fsync calls
7.425943s, engine queries0.034137s. Original failure SHA256cda882502520b9b245c296bf3b2e45b3d93977c623a9c96564a0edf98dd1d32d.
Saved13Nov01:36:28.115299UTC invocation16efd379144848e385a5987c048ab0cf/PID2723464:
9.259661s/8s; decision-state persistence6.511998s, queries2.194040s, before attempt
persistence. Original SHA25679f980b9946ced7316556ebc794c34015730d4ea3c6945e75c3350cfd6ed3016.
Both exact saved files were reread; neither is replaced by a recovery error.

Installed TICK_SECONDS=2. Each successful Gateway.readback validates AWG/TCP sets,
updates applied observations, then writes decision state and transport-attempt:
each uses pending-file flush/fsync, replace and directory fsync. Thus unchanged
authorization still executes four fsyncs/two renames per successful watch cycle,
in addition to canonical renewal operations. This proves the path/frequency policy,
not that its load causes the multi-second stalls or that writes are safely removable.

Missing: time-aligned syscall phase latency, per-process/cgroup writes/major faults/
swap/memory and host PSI/disk deltas at a slow cycle/first failure. Historical sysstat
10-minute aggregates do not supply that attribution. Do not change persistence,
8/12/120s or lifecycle based on correlation. Bounded observation preparation is next.

## Separate CI disposition

Phase043591863104 tests132438099847 is completed FAILED by external timeout; cargo
was skipped, not passed. Artifact14115497288 digest38f336c896770969e03ba09d3fec44feeef063ad62eeaa8b294ac67332cacafa
records standard5808/root258/snapshot31498 contexts all return0, coverage PASS,
no failure/error IDs. It uses PR test-merge906b4653, tree-identical toac3479bf.
Linux control43591863123 has the analogous outer timeout; actual failover/auth/
offline/revocation132438099607 PASS. CI-RUNNER-COMPLETION-1 stays separate; no general
CI success or runner-cause claim. No gate is removed for a prospective RU change.

Private read-only snapshots/source capsule stay in `/mnt/data/fc-ru-persistence-pressure-20261114`;
no keys, raw registry, user contents or private snapshots are committed.
