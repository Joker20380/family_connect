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
8/12/120s or lifecycle based on correlation.

## Bounded observer qualification

Added a PID-scoped BPF syscall/child-lifetime observer plus a finite counter ring;
[limits, signals, collection and extraction](../operators/ru-pressure-observation.md).
Only numeric phase/counter data and aggregate access observations, no argv, keys or
message contents. No transport/paid/support source, archive or unit was changed.
The prerequisite node/gateway hashes and hostname are enforced, including refusal
to start over an existing first failure. No diagnostic persistence is authoritative.

Qualification is staged in RAM with CPU10%/Memory256MiB/no swap, not an application
installation. Initial small probes and guard tests are not route acceptance: one
invocation lost its SSH wait result; the detached20-second tracer hit its unit
runtime limit after collecting36 fsyncs. Three candidate collector runs stopped on
their own cost guard before tracing, exposing that sampling235+ PIDs/45 cgroups
costs about0.12–0.13 CPU seconds and quota wait inflates wall time. The accepted
budget must therefore use separate CPU/wall measurements and a five-second counter
interval, not a tight two-second loop. A subsequent candidate failed BPF compilation
on signed fd keys/conditional integer types; explicit uint64 map keys/roles correct
that diagnostic compatibility issue. None of these probes restarted or changed RU.

Own scheduling inspected: paid reconcile and restricted directory sync30s after
completion; chat sync20s; credential health10min/renewal15min; cert renewal00/12 host
time plus≤30min jitter. No Family Connect entry found in inspected cron.d/root-user
crontabs, and no Family Connect backup timer appeared in the unit inventory. This
does not exclude manual/provider tasks. Installed server-load monitorf9ec91fb matches
source and writes two small atomic snapshots roughly every15s, without fsync. These
are candidate contributors to measure, not established historical causes.

Local collection6191 PASS; observer regressions27 PASS (numeric schema, privacy,
PID identity, first-failure priority, immutable bounded outputs, five stop paths).
General CI remains separate below. No product persistence/lifecycle alteration is
proposed: crash/reboot/partial-write fault injection would be mandatory for such a
fix, but is not falsely claimed from observer tests or repeated on production.

Final qualification14:09:04–14:12:03UTC (181.50s process duration) PASS:75 complete
cycles,300 fsync/150 rename/225 child-exit phase records, no phase0, no lost indication,
no first failure and no tracer errors. Source script004114fe317b223fd78f898444f0990147b3634b25ba0c64330360279b8104f5;
exact companion hash is recorded in the source/installation receipt.28 counter
samples; mean/max sample CPU152/175ms, aggregate unit CPU6.584s (3.63% of one core),
MemoryPeak74,014,720 bytes. Counter polling waits5s after sampling; actual mean
spacing6.63s, not an asserted exact5s. Zero omitted PIDs/cgroups; up to13 procfs races
per sample are visible. Short-lived tasks between samples may escape per-PID deltas;
host/cgroup totals must not be mistaken for complete per-process accounting.

State-file fsync median23.08/p95 53.07/max374.13ms; attempt-file median18.91/max44.47ms;
directory maxima44.85/34.70ms; rename maxima3.05/2.72ms. AWG child max24.27ms/TCP
child max91.59ms (not whole engine-query timings). Logical watched writes3,220,647
bytes over75 cycles; watcher `/proc/io` delta4,128,768 bytes over178.91s (~22.54KiB/s),
not an I/O reduction: no product write-path change was made. Host writes52,980KiB,
swap-in0/swap-out12 pages; memory-full PSI delta0.0226s versus IO-full6.301s.
Largest long-lived process write deltas include journald5.83MB, watcher4.13MB and
Family Connect HTTP2.03MB. These healthy-window counters do not attribute the old
multi-second stalls to any of them or prove a provider fault.

All28 observations:64 applied records/20 allowed, fresh readback, no prepared entry
at independent engine inspection. Initial lease14:10:38UTC crossed with later
deadline14:14:02UTC, no extension of the120s policy. Independent AWG/TCP queries at
14:10:59UTC:64 canonical identities checked, zero presence/identity/flow mismatches,
no decision race, state age1.09s, same four runtime PIDs/invocations/NRestarts0.
The measured interval is not proof against future recurrence. At that source
checkpoint finite production capture was not yet enabled; activation follows below.

## Actual activation and preservation

Observer source43eb84eb76871ae907a64f2fef4934f04cf8385f pushed/remote SHA verified;
PR29 ordinary merge59cd72ed0e3af4a2f68c399a6fc8b6f27fedd461 verified on remote main.
Author scoped review and27 tests/exact RU smoke/public-source/docs gates completed.
No independent third-party approval is claimed. The repository has no required
check contexts; hosted general CI was still running, not represented as PASS or
as qualification for a product persistence change.

Enabled **only** the RAM-staged observer/trace/manifest, not a gateway correction:
`/run/family-connect-ru-pressure/source-43eb84eb`. Script SHA004114fe317b223fd78f898444f0990147b3634b25ba0c64330360279b8104f5;
trace SHA49f96235b61eee6b3b9e03033880b6391f6cf48e984ce7ac0aede8571fa2de90.
Transient unit`family-connect-ru-pressure-20261114-43eb84eb.service`, PID464781,
invocation2384a0930d87408c9490297b023febe7. Start14Nov14:19:15.976UTC; one-day
deadline15Nov14:19:15.976UTC, unit ceiling+30s, Restart=no, no reboot enablement.
Effective CPU100ms/s, memory268435456/no swap, Tasks24, Nice19, IOWeight1, LimitFSIZE9MiB
read back. At14:24:42UTC still running: unit CPU10.567s over326s, peak89.59MB;
observer process read_bytes/write_bytes/cancelled_write_bytes all0, empty trace errors.
Unit CPU excludes some in-kernel probe work; no total-host overhead claim.

At14:25:05UTC the diagnostic process stopped by its own cost guard, NOT a RU
failure: sample CPU306ms exceeded200ms. Completed349.88s/151 cycles/604 fsync with
zero lost indications, preserved first-slow and final receipts; unit CPU11.716s,
peak94.96MB. The24-hour maximum was NOT reached and that collector is no longer
running. Final extraction`first-window-final` succeeded. A small observer-only
refinement skips redundant user-memory/cgroup reads for143 kernel threads while
retaining their stat/CPU/fault and jbd2 I/O, full userspace I/O/memory/cgroups and
host disk/PSI. No resource guard or product guarantee is relaxed. This revised
observer requires its own exact qualification before a new finite window.

Refinement qualified14:32:23–14:35:18UTC,181.99s process duration: script
ebd64d14346385cb1e98b754dab3b34ed7dfde1ba0e9790f72250c8451d5c0ff, unchanged trace49f96235.
75 cycles/300 fsync/150 rename/225 child records, zero lost indications/errors or
gateway failure.29 samples, mean/max sample CPU121.68/151.82ms (previous smoke
152.01/174.69ms); unit CPU5.960s/3.28% one core, peak76.69MB. The code deterministically
avoids redundant kernel-thread procfs reads; healthy-window latency differences do
not establish a product I/O improvement. New local tests29/collection6193 PASS.
Initial lease14:34:21 crossed to14:37:11,64 applied/20 allowed throughout. Same
200ms CPU/10s sample wall guards and unit limits; no repeated automatic retry.

First slow trigger14:20:46UTC: successful state-file fsync747.740401ms/42,862 bytes,
not an8-second deadline failure. Immutable`slow.json` SHA8513f09ce715af5adf15a0f14bf35d7f0b91d20c2d728e6ffb80ad77c34b20a2
was extracted and hash-verified with14 preceding counter snapshots/292 phase records.
Last counter sample precedes syscall completion by2.48s; it must not be advertised
as an after-event measurement. Preceding6.41s interval: journald225,280/watcher147,456/
HTTP65,536 write bytes, no sampled long-lived PID major-fault increment while host
pgmajfault rose35. Short-lived/unobserved tasks and shared writeback remain attribution
gaps; no process is blamed from this snapshot. First-failure detection/finite expiry
will preserve the then-current ring in final.json. No current transport failure.
The subsequently extracted full first-window final receipt also brackets this slow
fsync with14:20:43.568–14:20:50.356UTC counters (6.788s): journald cgroup writes
1,765,376 bytes, watcher147,456, HTTP53,248; host swap-in/out0, major faults4. This
narrows contemporaneous I/O accounting but still does not prove journald caused
the747ms wait, identify its log producer or explain the old8s deadline failures.

Before/after read-only canonical snapshots:64 devices/118 invites/1 subscription/
4 paid events retained; subscriptions, terms, pilot membership, credentials and17
protected groups byte-identical. Initial blanket19-group comparison correctly failed
for two live changes and was **not** silently waived: matching12:35 backup anchors
prove all52 device→chat-public mappings unchanged, with one support_sender NULL→the
already-existing official sender; all64 support-ID mappings unchanged, with one
observation_source change already present before observer activation. The initiator
is not established from these rows. No old DB was restored to erase live changes.
All paid archive members/configs/effective existing units, four runtime PIDs and
both notification-reader helper hashes unchanged. Local actual panel IPC still
shows baseline_excluded4/cursor4, zero automatic jobs,2 conversations/5 messages,
1 panel user/socket0660 gid980. No payment, message or subscription operation created.

Safe rollback is stopping the diagnostic unit, retaining captures and all product
state. No old archive, DB, worker or configuration is installed. The exact tested
extraction command/deadline is in the operator runbook. Cause remains **OPEN**;
this bounded data acquisition satisfies the diagnostic fallback, not causal closure
or a promise of future stability. Next action is finite-result analysis, not another
unspecified monitoring request or an unrelated CI/payment/client-card task.

## Refined finite activation

PR30 ordinary mergeedd10793f43f866c7add806d0a1609b0b43e42e8 and source38e9f403913ee7a73e6eb309bbe0d445d11f0494
verified remotely. Enabled only the exact ebd64d14/49f96235 diagnostic pair in a new
RAM directory; previous source43eb84eb/start/slow/final are preserved. New unit
`family-connect-ru-pressure-20261114-38e9f403.service`, invocation428ee09ca2744951b2b4249f08c823f5,
PID535313, started14:40:35.898UTC. Normal deadline15Nov14:18:46.898UTC; runtime
ceiling remains14:19:16UTC from the original window, not an unlimited retry extension.
At14:42:27UTC: active/running, unit CPU4.251s, peak73.19MB, process disk read/write0,
no final/error receipt. Both installed source hashes verified. Repeated actual
engine readback at14:40:35UTC:64 applied/20 allowed, zero identity/presence/flow
mismatches, no prepared state/failure, same archive bytes and four runtime PIDs.
No application restart, new lease policy or persistence fix. Exact extraction and
safe disable commands are in the runbook's active-refined-window section.
Final acceptance14:47:24UTC: same observer PID535313 running408.48s, past the first
window's349.88s cutoff; CPU10.785s (2.64% one core), peak87,474,176 bytes, process
read/write/cancelled-write0, empty errors, no final receipt yet. Refined extraction
helper tested under`acceptance-20261114`, downloaded start/errors with SHA verification.
At14:47:26UTC independent RU readback:64 applied/20 allowed, no prepared/mismatched
identity/presence/flow, no failure, age2.12s; same four PIDs/invocations/NRestarts0.
Initial renewed lease14:42:12 crossed to14:48:56. Final read-only registry check
found no further protected-table changes after the audited live deltas, same4 paid
events/1 subscription/64 devices/118 invites and identical paid archives. Local
support worker still2651059/NRestarts0, RuntimeDirectoryPreserve=yes/inode333786.
The original dirty checkout/untracked work was preserved. Continuous qualification
windows and this408s live check are limited observations, not a24-hour PASS or
evidence that future stalls cannot recur. No unrelated task is resumed.

## Separate CI disposition

Phase043591863104 tests132438099847 is completed FAILED by external timeout; cargo
was skipped, not passed. Artifact14115497288 digest38f336c896770969e03ba09d3fec44feeef063ad62eeaa8b294ac67332cacafa
records standard5808/root258/snapshot31498 contexts all return0, coverage PASS,
no failure/error IDs. It uses PR test-merge906b4653, tree-identical toac3479bf.
Linux control43591863123 has the analogous outer timeout; actual failover/auth/
offline/revocation132438099607 PASS. CI-RUNNER-COMPLETION-1 stays separate; no general
CI success or runner-cause claim. No gate is removed for a prospective RU change.

New observer PR29 hosted runs are distinct: readiness43603921659/job132474346844
completed PASS. At14:22UTC phase043603921594/tests132474346280 and Linux control
43603921607/job132474346773 were still running; failover132474346460 was still
building, with actual failover/auth/offline/revocation pending. Neither Docker build
nor the prior source's result is substituted for that new run's completed steps.
Later14:42UTC, PR29 actual failover/auth/offline/revocation132474346460 completed
PASS (all execution steps, not just build). PR30 exact source38e9f403 readiness
43606003839 PASS; its phase043606003930 and Linux control43606003884 remain
IN_PROGRESS at that observation. These are separate from old sourceac3479bf's
completed timeout debt and from the observer's completed local/RU qualification.

Private read-only snapshots/source capsule stay in `/mnt/data/fc-ru-persistence-pressure-20261114`;
no keys, raw registry, user contents or private snapshots are committed.
