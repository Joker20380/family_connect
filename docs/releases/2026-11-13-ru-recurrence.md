# RU recurrence — 13 November 2026

## Scope and current gate

Owner reports another RU problem. Investigation confirms stopped native transports,
not merely a stale panel or an unavailable support chat. This incident is RU-only;
Amsterdam, neighbouring services, phone, subscriptions and public distribution are
not changed. The dirty main checkout is preserved; safe documentation uses the
existing `feature/support-chat-1-20261110` worktree/branch.

**RECOVERED_CAUSE_OPEN.** Controlled recovery of the unchanged accepted runtime
completes at13 November 11:58:12.054 UTC. Six-sample observation, actual admission
renewal and protected-state comparison PASS; final snapshot is12:01:46.063 UTC.
This closes the operational recovery gate, not the underlying storage/host-latency
cause or client VPN traffic acceptance.

## Preserved first failure

At **13 November 01:36:28.115299 UTC / 04:36:28 MSK**, the watcher records
`TRANSPORT_OPERATION_DEADLINE`, mode `watch`, phase `persist_directory`, boundary
`after`, `TimeoutError`: **9.259661 seconds against an 8-second budget**. PID2723464
is the watcher started in the previous day's recovery, not a newly deployed binary.
Original failure SHA256:
`79f980b9946ced7316556ebc794c34015730d4ea3c6945e75c3350cfd6ed3016`.

The recorded calls are:

| Boundary | Duration, seconds | Result |
| --- | ---: | --- |
| AWG query | 0.129067 | completed |
| TCP query | 0.127143 | completed |
| AWG readback query | 1.937831 | completed |
| Decision-state file fsync | 3.280578 | completed |
| Decision-state replace | 1.831176 | completed, replacement occurred |
| Decision-state directory fsync | 1.400244 | completed, deadline exceeded |

Persistence calls total **6.511998 seconds**; engine queries total **2.194040
seconds**. Unlike the previous incident, the overrun already occurs while persisting
the decision state, before an attempt-persistence call is recorded. Do not describe
it as the identical four-fsync sequence from 12 November. Completed rename/fsync is
not evidence that the entire operation passed its deadline.

TCP stops at01:36:29 UTC; AWG stops with `Result=timeout` at01:36:34 UTC. The first
read-only probe at11:54 UTC observes watcher active/restarts1040 but AWG failed and
TCP inactive; the guarded pre-recovery snapshot observes1046 watcher restarts.
Restarting only the watcher does not restore the stopped dependent engines. Central
reconcile is failing, although its timer remains active. HTTP is separately running;
its health does not establish that either VPN transport works.

## Host evidence and limits

A single low-priority, bounded sysstat read covers04:16:28–04:56:28 MSK. The
04:30–04:40 interval containing the failure shows:

- virtual disk `vda` average wait147.99ms, average queue17.64;
- CPU iowait18.57%, steal0.66%;
- swap in/out36.41/49.63 pages per second; major faults37.32/s;
- interval I/O full pressure18.96%, memory full pressure12.78%.

This corroborates concurrent storage/memory pressure, not a proven competing writer,
OOM, faulty physical disk or provider fault. The watcher reports no major faults in
the measured calls themselves. The10-minute aggregate is not per-process attribution
at the precise failure timestamp. Remote root has7.5GiB available/74% used at the
initial probe, so local laptop disk pressure is a separate issue.

The narrow original-invocation journal query returns zero records. The kernel query
hits its5-second bound; its partial outcome is retained privately. Neither result
proves absence of kernel/OOM errors. No repeated broad journal scan, disk benchmark,
cache drop or neighbouring-service operation is performed.

## Recovery and preserved runtime

Fresh private evidence is retained under ignored
`state-client-build/ru-incident-20261113/` with restrictive directory/file modes.
The remote retained snapshot is
`/opt/apps/family_connect/private-ru-incident-20261113/`.
Original failure, configuration, unit/member hashes, registry fingerprints and
pressure are captured before mutation. Reused recovery tooling has fresh paths,
current failure/configuration guards and no-replace archival; it is not a blind
replay of yesterday's commands.

1. At11:58:09.101 UTC, atomically fence only `gateway-ru` in the central command map;
   preserve NL entries and keep the central timer active. Drain its active cycle.
2. At11:58:11.161 UTC, stop watcher/AWG/TCP together; verify zero MainPID/ControlPID,
   no pending unit jobs and no remaining gateway handlers. Preserve native/state
   files and a consistent peer-database backup privately.
3. Validate retained decisions with the installed engine under its ordinary
   operation/lock. Preserve state bytes; no database restore, expiry extension,
   decision reset or new authorization is introduced by this procedure.
4. Archive the exact first-failure bytes without overwrite; reset failed units and
   sequentially start the same runtime. All three start by11:58:12.054 UTC.
   PIDs: watcher2244159, AWG2244162, TCP2244185; restart counters0.
5. At11:58:13.390 UTC, restore the exact original command-map bytes. A start failure
   would retain the RU fence and stop the procedure rather than retry blindly.

Installed versions/hashes, also unchanged from the12 November evidence:

| Component | SHA256 |
| --- | --- |
| RU paid-transport node | `125c796a30c3fba1772c47b96963517350087ad04aad675b6f33a31a5383276c` |
| RU gateway | `9023d2c3f7c3a5127d67c509a16eb2d974810ff54d5b76cc225cd9b93e0b4234` |
| Watcher unit | `e9a9d82841d0d5aa257780660107d9588af80a24b32d604dccf9c81c2730523a` |
| Support-only HTTP overlay | `16d96eb767602188e1999052e11cfead8dc1a4b38ae8c15394a61dc9ce7f3503` |

Policy remains `android-paid-108-119-v1`; watchdog/deadline/lease remain12/8/120s.
No fsync removal, commit-before-ACK relaxation, new binary or previously rolled-back
PR16/17 candidate deployment. Existing support schema, official chat-only sender,
keys and collector configuration are preserved. Retained backups are diagnostic
assets, not permission to roll back live decisions or restore the product database.
No code rollback is needed because no code is deployed.

## Verification and remaining work

Six ordinary readback samples over **197.794926s PASS**: watcher/AWG/TCP remain
active/successful on the same PIDs/invocations, restart counters0, no new first
failure. Each sample has fresh `applied` readback younger than10s,64 retained
records/20 allowed, unchanged bindings, and persisted TCP id/email/flow exactly
matching the allowed decisions. The ordinary watcher supplies engine readback;
there is no substitute synthetic state or extra manual live-query loop.

The actual cohort admission advances **1794571181→1794571389**, a208s increase;
observation crosses the initial expiry and finishes before the renewed expiry.
This tests real renewal, not only the first startup allowance.

Before/after protected table fingerprints match:64 devices,118 invites,1 paid
subscription,4 paid events,52 chat bindings and1 official service sender. These
are current records, not yesterday's smaller snapshot restored over new devices.
Code, effective units, policy, exact command map, release/paused pointer, support
configuration/key hashes and root authorized_keys are unchanged. HTTP PID2074210
is unchanged during this intervention; no HTTP restart or chat resend is performed.
Central reconcile succeeds and its timer stays active. The panel's RU snapshot is
`ok`, observed12:01:42 UTC/imported12:01:44 UTC with node125c796a; panel HTTP200.
Final narrow readback at12:03:27.519 UTC also PASS: same watcher/AWG/TCP/HTTP PIDs,
restart counters0, no new first failure, latest `applied` attempt age1.519s.

**USER_TRAFFIC NOT_RUN**: no owner-phone DNS, verified HTTPS or egress test is part
of this recovery. HTTP200 or a healthy unit is not a substitute. The recurring
latency and watcher-only restart/dependency behavior remain unresolved; recovery
cannot honestly be called a permanent fix. Next correction must isolate the
storage/resource-pressure cause or qualify a persistence/recovery change through
the durability, expiry, fail-closed and deployment gates. RU replacement remains
`WAITING_FOR_HOST`, not an authorized target that can be invented or provisioned.

Local capacity starts/ends at1.9GiB free on system root and2.6GiB on the data partition.
Only small bounded diagnostics are needed; no build or cleanup is performed. User
data, logs, accepted APKs, keys, backups and rollback material are preserved.

The owner remains on installed private Android0.1.18-beta125, unchanged here.
[Panel↔owner support exchange with user tunnel OFF is already confirmed](2026-11-12-android125-owner-install.md);
do not reopen or repeat that accepted basic scenario because RU VPN stopped.
Production public Android announcement delivery remains NOT_RUN. Cold no-cache
restricted bootstrap/recovery, subscription-change notifications, payment partner
and later Windows/Linux acceptance remain separate tracks, not automatically begun.

Documentation-only validation: `scripts/check_public_docs.py --all` checks793 files
and5014 local links with zero errors; external URLs are enumerated, not fetched.
`git diff --check` passes. No application source/package changes require a rebuild
or repetition of historical platform suites. Safe documentation follows the existing
PR23 branch; private incident evidence and retained recovery artifacts stay out of Git.
