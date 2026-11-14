# RU-PERSISTENCE-PRESSURE-1 — 14 November 2026

## Final analysis — COMPLETE, cause remains OPEN

Selected on main817266aa after closed PR32; integration [PR33](https://github.com/Joker20380/family_connect/pull/33).
The finite data have been analyzed;15November is **not** a prerequisite for analysis
or an active collection deadline. No third run, limit change, product correction,
deployment, preventive restart, payment or message. Original dirty checkout retained.
The following dated activation/recovery observations are history, not simultaneous NEXTs.

**Decision:** do not change persistence or blame a process/provider from these data.
The two real historical deadline overruns are established, but neither occurred in
these windows. Finish this analytical stage with **CAUSE_OPEN / FINAL_ANALYSIS_COMPLETE**.
The single proposed follow-up is isolated qualification of first-failure attribution
instrumentation, specified below; it is not automatically started or deployed.

### Provenance and uniqueness

Both manifests were checked against `git show <source>:scripts/<file>`: first
43eb84eb has observer004114fe/trace49f96235; refined38e9f403 has observerebd64d14
and the same trace. Full source hashes remain in the activation sections below.
Local file hashes match the original extraction receipts' hashes, not just another
copy. Initial acceptance slow/start match first-window-final. Refined entry and exit
exports are byte-identical: **one run, not two independent observations**.

| Capture | SHA256 |
| --- | --- |
| first start | e6005e5e0cba0ea6dcdb24e71a49e0566b184cbd2ba7840631b004e45bcc8b59 |
| first slow | 8513f09ce715af5adf15a0f14bf35d7f0b91d20c2d728e6ffb80ad77c34b20a2 |
| first final | ada3a755c21d185b6f2cf6ee9a3a9858801ad3c705465d404956754827c4d2d4 |
| refined start | 2680c3a4bbd32d59ee39df08d58b83f416e63c92cdc58af7d5374f1006f36ff5 |
| refined final, both exports | 911a8f16e9a5ac2cdd7cc1d19cf9e1f0b366b53dc56941dc39505e2ab4e7e660 |
| all empty tracer-error files | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |

Same boot411dc329-437f-418d-bb71-37a8d1e4d4bf, watcher PID3952264/start_ticks638777204,
watcher invocation1a0fc5c8af3f40eca2bc2cc8b224a481 in every retained sample.
This watcher invocation is distinct from the observer unit invocation. Saved units:
clock_ticks100/s, page_size4096; diskstats sectors are independently512 bytes.
Actual node125c796a/gateway9023d2c3 matches both captures, not current main.

Original failure bytes were found in the existing ignored checkout directories
`state-client-build/ru-incident-20261112/first-failure.original.private.json` and
`state-client-build/ru-incident-20261113/first-failure.original.private.json`.
Their cda88250/79f980b9 full hashes below revalidate exactly. Incident before/after
snapshots have the same boot ID; the original failure records identify their own
PID/invocation, not this watcher's PID/start. They do not contain original proc start
ticks. No current process counters are joined to those dead historical processes.
No expected saved capture is missing. Refined slow.json is absent as expected: no processed
phase reached its500ms trigger. Source captures and extraction receipts are unchanged.

### Actual coverage, not a complete final log

Times below are UTC14November. Phase timestamps are monotonic completion timestamps;
approximate wall rendering uses a saved sample's wall/mono pair, never wall ordering.
Start+elapsed estimates final serialization time, not the final traced syscall.

| Coverage | First window | Refined window |
| --- | --- | --- |
| Start → approximate final; elapsed | 14:19:15.976 →14:25:05.855;349.878274s | 14:40:35.898 →15:00:07.346;1171.447650s |
| Stop | sample_cost_limit, CPU | sample_cost_limit, CPU |
| Retained phase completions | 1359,14:19:36.565–14:24:59.799 | 4096,14:43:54.766–15:00:03.067 |
| Monotonic phase range ns | 6401169831754757–6401493065780244 | 6402628033091859–6403596333900487 |
| Retained counter samples | 53,14:19:16.358–14:25:01.468 starts; last finishes14:25:04.464 | 60,14:54:00.515–15:00:04.298 starts; last finishes15:00:06.297 |
| Monotonic counter starts ns | 6401149624874980–6401494735517933 | 6403233782115685–6403597564600239 |
| Processed phase count in summary | 1359, all retained | 4842;746 older records evicted |
| Real sample spacing min/mean/max | 6.202/6.637/7.400s | 5.993/6.166/6.796s, retained tail only |
| Procfs races sum/max per sample | 396/13 | 419/11, retained tail only |
| Omitted process/cgroup records | 0/0 in retained samples | 0/0 in retained samples |

The first slow capture's292 phases/14 samples are a subset of its final1359/53,
not additional events. Refined's total sample count is **not recorded**; do not infer
it from elapsed/5. Its60-sample ring covers only the last363.782s between starts,
whereas phases cover968.301s. No counter attribution is available for the earlier
retained phases or for the evicted phase records. First startup has about20.59s before
the first processed event; it is not measured phase time. No coverage is claimed
between the two runs, before tracing attached, or after the last drained event.

The terminating sample is appended **before** the cost check. On stop the collector
closes the selector, signals/waits for tracer and closes stdout **without a final
drain**. Last phase precedes last sample start by1.670s/1.231s, and final metadata by
about6.056s/4.279s. Events buffered during sampling/tracer shutdown can be absent
from both ring and summary. `lost_indications=0` and tracer rc0/empty stderr mean no
reported perf loss, not proof of a fully drained end boundary. All retained F/R results
are0; Q result0 is the trace format's constant, not independent child exit validation.

### Why the collectors stopped

Refined's last five samples (start UTC; CPU ms / wall seconds):

| Start | CPU ms | Wall s |
| --- | ---: | ---: |
| 14:59:39.699 | 113.770 | 1.099339 |
| 14:59:45.802 | 113.100 | 1.097265 |
| 14:59:51.901 | 126.685 | 1.201880 |
| 14:59:58.195 | 110.497 | 1.100131 |
| 15:00:04.298 | **202.841517** | **1.999824** |

Thus CPU exceeded200ms by2.841517ms; wall did **not** exceed10s. First window's
different terminating sample was306.477418ms CPU/2.995883s wall. Do not transfer306ms
to refined. Refined last sample has235 processes/45 cgroups/8 races, comparable with
the preceding counts; no per-reader profile exists to attribute its CPU excursion.
Retained refined sample CPU mean/max121.869/202.842ms; wall1.169358/1.999824s.
First53-sample CPU mean/max164.903/306.477ms; wall1.651628/2.995883s.

Refined collector self CPU24.509s/1171.448s=2.092% of one core, unit CPU28.158s
and peak92,377,088 bytes from retained unit receipt. First self CPU9.325s/349.878s
=2.665%; unit11.716s/peak94.96MB. Unit totals include tracer work but not all in-kernel
probe cost. Zero observed collector disk read/write counters do not mean zero host
CPU/cache/scheduling/BPF overhead. No overall refined sample-average or total host
instrumentation cost is inferred from its last60 samples or unit accounting.

### Accumulated phase statistics versus retained distributions

The next table is **summary over processed events**, not per-window sample percentiles.
Each cell is `count / total seconds / mean ms / maximum ms`; means divide accumulated
duration_ns by counts. Q is child fork→leader-exit, not complete engine-query duration.

| Phase | First | Refined |
| --- | --- | --- |
| F1 state file fsync | 151 /5.335679 /35.336 /747.740 | 538 /12.931791 /24.037 /472.707 |
| F2 attempt file fsync | 151 /2.976574 /19.712 /142.941 | 538 /9.285793 /17.260 /85.529 |
| F3 state directory fsync | 151 /2.212453 /14.652 /164.133 | 538 /7.070325 /13.142 /210.606 |
| F4 attempt directory fsync | 151 /2.073812 /13.734 /157.723 | 538 /6.596395 /12.261 /61.624 |
| R1 state rename | 151 /.030151 /.200 /3.638 | 538 /.099147 /.184 /4.541 |
| R2 attempt rename | 151 /.029305 /.194 /4.522 | 538 /.094236 /.175 /3.640 |
| Q1 AWG child | 302 /1.049249 /3.474 /16.696 | 1076 /3.457227 /3.213 /62.349 |
| Q2 TCP child | 151 /4.620389 /30.599 /102.823 | 538 /15.245360 /28.337 /100.331 |

Summary fsync total12.598518s/35.884303s. Logical F1/F2 bytes6,472,150/12,533 and
23,059,307/44,654 respectively; other phases report0 bytes. These are logical file
writes, not physical disk or cgroup traffic. Equal per-phase counts correspond to
151/538 processed cycles; not proof all activity through final serialization was read.

**Retained-only** F1 first151 samples: median22.483ms, nearest-rank p9548.890ms,
max747.740ms. Refined455 F1 samples: median20.149ms, p9539.252ms, max278.883ms,
mean22.971ms, not summary mean24.037ms. Refined ring contains455 each F1/F2/F3/R1/R2/Q2,
456 F4 and910 Q1, so its first cycle is partial. Summary max472.707ms was evicted;
it has no retained timestamp/counter bracket. Retained max278.883ms at14:48:30.948
and F3 max210.606ms at14:50:48.246 precede the saved counters. The largest fully
counter-bracketed refined F1 is198.239ms at14:59:37.423. No cross-window improvement
or regression is inferred from differing workloads/coverage; persistence is unchanged.

### Slow-fsync interval and host/process accounting

First F1 completed14:20:46.043784, monotonic6401239310899633, duration747.740401ms,
42,862 logical bytes, result0. Its entry is14:20:45.296044. The before sample in
slow.json starts14:20:43.567982 and finishes14:20:45.264890: entirely before this
fsync, **not** an after-event measurement. First final supplies the actual next sample
14:20:50.356134–14:20:51.965327. Start-to-start spacing6.788153s; because counters
are read sequentially, any individual counter's interval lies approximately within
5.091244–8.397346s, not one synchronized instant for all fields.

Over that bracket: vda reads2,834,432/write3,313,664 bytes,108/365 operations,
read_ms7935/write_ms30211, busy1.527s/weighted38.639s. IO PSI full/some increases
.378747/.838926s, CPU some2.281260s; memory PSI0, swap-in/out0, host major faults4.
These disk times include overlapping requests and cannot be added to fsync wall time.
Matched process deltas: journald675,840 write bytes; watcher143,360; HTTP0;
jbd2 167,936. Matching cgroup deltas on253:0: journald1,765,376; watcher147,456;
HTTP53,248. These levels differ due to sampling/ownership/writeback semantics; they
are **not independent volumes to sum**. No matched long-lived process gains a major
fault, two earlier process identities disappear. Missing short-lived work/shared
writeback prevents attributing all host I/O or those four faults to one process.

Journald is a contemporaneous writer, not a demonstrated culprit: another first-window
bracket14:24:41.864 has1,294,336 journald cgroup bytes with max bracketed F1 only21.060ms.
Refined's largest retained journald bracket14:54:37.907 has1,216,512 bytes with max F1
34.327ms. These counterexamples reject a simplistic “journald bytes imply the stall”
rule; they do not prove journald innocent under the historical load or identify its
upstream log producer. No journald/neighbor configuration was changed.

Endpoint counter deltas (only saved counter periods, not the whole refined run):

| Metric | First345.111s | Refined363.782s tail |
| --- | ---: | ---: |
| vda read / write bytes | 26,234,880 /105,099,264 | 90,112 /111,149,056 |
| IO PSI full | 13.757859s (~3.987%) | 12.925405s (~3.553%) |
| Memory PSI full | .014044s | .000001s |
| Swap in / out pages | 1 /5 | 1 /0 |
| Host major faults / matched endpoint PID faults | 100 /6 | 4 /2 |
| Watcher process write bytes | 7,864,320 | 8,404,992 |
| Journald process write bytes | 11,284,480 | 11,882,496 |

Rates use actual monotonic spacing, not configured5s. Retained available RAM ranges
1,024,768–1,149,076KiB and1,009,980–1,089,148KiB, above the256MiB guard. No matching
cgroup memory.events counter increases or matched process counter resets were found.
This does not cover evicted samples or unsampled/recreated cgroups: cgroup inode/start
identity was not collected, unlike PID/start ticks. Omitted=0 means no budget pruning
of retained records, not no races. Refined unsampled kernel-thread I/O remains unknown,
not zero. No double counting across PID/cgroup/device; no interpolation across gaps.

### Historical failures and one engineering decision

The preserved8.651672s operation spent7.425943s in four fsync calls; queries .034137s.
The9.259661s operation spent6.511998s in state persistence and2.194040s in full engine
queries; it failed before attempt persistence. Neither is reproduced by747.740ms or
by refined's processed maxima. Historical10-minute vda wait135.95/147.99ms, swap and
memory/IO PSI support shared resource pressure but do not name a writer, distinguish
guest scheduling/reclaim from block-service delay, or prove a provider fault.
Fsync elapsed time itself includes task scheduling; Q child lifetime omits parts of
the gateway's query. No per-request block latency/off-CPU/reclaim trace exists at the
actual8s failures. Four durable fsyncs per cycle prove policy, not excess removable I/O.

**Missing fact:** a time-aligned decomposition of a genuine deadline-exceeding
operation into guest off-CPU/reclaim, guest block queue and virtual-device completion
wait, with contemporaneous writer-cgroup attribution. Healthy intervals do not supply
that counterfactual. Do not remove fsync, batch durability, lengthen8/12/120s or change
paid expiry/revoke from these observations. No minimal product fix is justified yet.

**Single recommended next task: RU-FIRST-FAILURE-ATTRIBUTION-QUALIFICATION-1**, an
isolated design/qualification of a bounded event-driven first-failure recorder, not
a third RU run. Avoid full periodic procfs enumeration; retain only numeric watcher
off-CPU/reclaim and vda issue/completion/queue counters with boot/PID-start/cgroup IDs,
bounded pre-failure ring and one immutable first-failure receipt. No argv/keys/content.
This can distinguish guest scheduling/reclaim from a long virtual-device wait and
concurrent write pressure; it still cannot prove physical/provider fault without
provider-side evidence. Qualification ends with reproducible isolated cases for each
wait class, correct first-failure/tail-drain accounting and measured overhead within
the existing CPU200ms/sample, wall10s/sample, CPU10%, memory256MiB/no-swap/time/file
limits. Report probe overhead separately from unit accounting. A failed budget or
ambiguous attribution is a completed NO_GO result, not permission to raise limits.
Only a later explicit decision could authorize any RU capture. No indefinite wait
for another incident is part of this analysis. No host replacement decision is made.

### Fresh read-only health, separately dated

One check18:27:25.469UTC14November: watcher/AWG/TCP active, PIDs3952264/3952267/3952276,
same invocations/start ticks and restart counters0. Actual engine keys/accounts/flow
match64 applied/20 allowed, zero prepared/mismatches, no decision race; state age2.469s,
lease deadline18:29:07UTC. No current first-failure file. Node/gateway hashes unchanged.
This is engine/readback health, not a physical client throughput test or proof of
continuous availability since15:00. Observer active/exited/PID0/Resultsuccess.
HTTP is active but PID1265623 differs from the old178722 observation; its reason is
not established, and it is not attributed to a VPN crash or this read-only analysis.
No canonical DB, bindings, notification baseline/cursor/jobs/dedupe or guard was changed.
Closed beta125/catalog8/tablet/paid125/support/notifications and CI PR32 stay closed.

### Reproduction and validation

Use the exact command in the [offline analysis runbook](../operators/ru-pressure-observation.md#offline-final-analysis).
Private output `final-analysis-v3.private.json` SHA256
c198fd981d3e20483bea1a20fa284bd6172d76228944bda88b58c5ac5d68add5; no raw data/output
is committed. The output includes input hashes, source provenance, explicit spans,
summary/retained statistics, real sample durations, interval uncertainty bounds,
identity-matched deltas and unique slow bracket. All input hashes checked unchanged.
38 analysis/observer tests and full collection6212 PASS, including exclusive output/input preservation,
duplicate exports, ring truncation, source/metadata conflicts, PID reuse, reset/gauge
handling, saved units, CPU-vs-wall stop and conservative serial-sample brackets.
Documentation links/whitespace and source privacy reviewed; no independent approval
is implied by self-review. No product persistence/lifecycle change: crash/reboot,
durability, fail-closed, expiry/revoke and8/12/120 tests are not newly qualified or
waived for a future patch. They remain mandatory if such a patch is later proposed.
The applicable gate here is offline arithmetic/provenance/CLI tests plus documentation
checks, not a new transport release qualification. Branch main is unprotected and
repository rulesets empty at the integration check; no mandatory check was bypassed.
Automatic hosted runs are not represented as completed merely from local PASS.

## Historical final-analysis tooling checkpoint

Selected on main817266aa after PR32. `scripts/ru_pressure_analysis.py` reads only
existing local captures and writes a new exclusive0600 private analysis file. It
verifies source/trace pairs, deduplicates identical exports and overlapping samples,
keeps summary means separate from retained nearest-rank percentiles, uses saved
clock_ticks/page_size and actual monotonic spacing, and brackets a phase only with
a completed before-sample and an after-sample. Counter decreases are unknown/reset,
not negative traffic; changing PID start identity is not joined. No host access.
38 analysis/observer tests PASS, including real CLI non-overwrite/input-preservation.
Historical first-failure bytes and source manifests verified. Refined stop is CPU
202.841517ms>200ms, not wall1.999824s>10s. Full attribution decision is recorded above;
no new collection, runtime fix, resource increase or deployment is authorized here.

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

## CI-task entry readback15:07UTC

Refined observer38e9f403 had already stopped on sample_cost_limit after1171.45s;
unit active/exited/MainPID0/Resultsuccess, no gateway failure, tracer rc0/empty errors.
Start/final/errors extracted under NEW label`ci-entry-20261114-1506` with hashes,
without restarting/extending/changing RU. At this checkpoint final analysis was pending;
see [CI handoff receipt](2026-11-14-ci-runner-completion.md#ru-read-only-handoff).
The earlier408s running check is historical, not the current observer state.

CI-task exit readback: NEW label`ci-exit-20261114-1713`, separate local directory;
same active/exited/MainPID0/Resultsuccess and sample_cost_limit final receipt.
Start/final/empty-error SHA256 match entry; no slow receipt, no gateway failure,
no lost indications, tracer rc0. No restart, extension or production change.
This was the CI handoff; the final analysis above now completes that separate stage.
No scheduled automatic collection/analysis exists. RU remains CAUSE_OPEN, not resolved
by the separately completed CI fix. Original command/checkpoint/hashes remain history.
