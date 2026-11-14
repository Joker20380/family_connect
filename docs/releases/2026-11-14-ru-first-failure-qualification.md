# RU-FIRST-FAILURE-ATTRIBUTION-QUALIFICATION-1 — NO_GO

14 November 2026. Diagnostic candidate only; **NO_GO for RU use**. This is a
completed negative admission decision, not a successful full scenario matrix.
FINAL_ANALYSIS_COMPLETE / CAUSE_OPEN from PR33 remains unchanged. No third RU
capture, production probe, installation, sysctl change, restart or persistence fix.
No change to beta125/catalog8/tablet, paid125, support, notification guard/state or
closed CI-RUNNER-COMPLETION-1. Appimagetool403/readiness150ms remain separate.

## Source, feasibility and isolated environment

Entry main verified e1defaab7448859780dc9e890ca970946768c2b2. The existing clean
worktree/agreed branch was reused; the original dirty checkout was left untouched.
New files: numeric recorder/reducer, bpftrace program, disposable initramfs builder,
guest qualification harness and tests. No installed observer/product file changes.
Exact source/image hashes and numeric results are in the
[sanitized receipt](2026-11-14-ru-first-failure-qualification.json).

One read-only RU capability query (1.717s,14Nov19:13:55UTC) confirmed:
7.0.0-30-generic/x86_64, bpftrace0.25.0, cgroupv2, ext4/vda1; scheduler, direct-reclaim,
request insert/issue/requeue/complete/merge and cgroup lifecycle tracepoints present.
The ordinary formatted block records lack request identity: the candidate uses raw
tracepoint arguments/BTF. Live watcher PID/start identity matched the previous
receipt; this was **not** a new engine/access/availability acceptance check.
TASKSTATS/TASK_DELAY_ACCT are compiled in but kernel.task_delayacct=0. Zero live
delayacct ticks are not a measurement of zero wait. No enabling/restart was attempted.

An actually booted disposable KVM guest, not a host-container stress test:

- Exact Ubuntu kernel package7.0.0-30.30; image SHA256
  04d6998810b8e0a9b8b3676524bfca2e895f44c5da2626c963368d7204c6e0da.
- Guest BTF SHA256 **d7fca84d2c3f476afbeb2e37ddba3093eaac0af39b07b0cd1b61c11fdc1c89fb**
  equals the actual RU BTF, not just a similar kernel version. bpftrace0.25.0,
  libclang21.1.8, QEMU10.2.1/KVM; guest2vCPU/1536MiB, no network or host mounts.
- Dedicated128MiB RAM-backed virtio disk, freshly formatted ext4. Only synthetic
  files; VM root is an initramfs. Host VM unit: CPUQuota100%,MemoryMax2GiB,no swap,
  TasksMax32,RuntimeMax240s. These bound the whole test VM, **not** the recorder.
- Guest diagnostic cgroup: CPU10%,MemoryMax256MiB,swap0,pids24. Map256/perf8pages,
 4096 events/60 batch receipts,200ms CPU/10s wall/8s stop and file ceilings retained.
  No KVM fallback, host memory pressure or host disk stress was used.

Preparation failures are not workload qualification: missing BIOS path, /dev/fd,
module dependency metadata and initial bpftrace syntax/type warnings were corrected
inside the disposable image/source. The /dev/fd omission made even minimal BEGIN
fail; it was an environment failure, not evidence against the candidate. Four
final controls (BEGIN, fsync tracepoint, task BTF and request BTF) all actually
attached/exited0 with empty stderr on the exact kernel. No probes ran on RU.

## Frozen matrix and admission result

The [matrix and independent controls](../operators/ru-attribution-qualification.md#frozen-matrix-before-kernel-tests)
were written before real kernel testing. The initial mandatory clean gate fails;
the remaining pressure mechanisms were deliberately not injected after rejection.

| Real scenario | Result / evidence |
| --- | --- |
| Healthy write/rename/fsync and bounded16-cycle burst | **FAIL**. Workload completed16 identical cycles, each state write/file fsync/rename/dir fsync then attempt write/file fsync/rename/dir fsync. Independently expected64 fsync enters/exits; only12/12 retained in final run. Not an idle-only PASS. |
| Controlled runnable CPU wait | **NOT_RUN** after clean-gate failure. Some scheduler intervals exist, but no independent controlled-CPU attribution PASS. |
| Direct reclaim of observed task | **NOT_RUN**; tracepoint availability is not mechanism qualification. |
| Guest device queue delay | **NOT_RUN**; basic request identity already fails. |
| Guest issue→completion delay | **NOT_RUN**; cannot make a service-wait attribution with this candidate. |
| Two writer cgroups plus background | **NOT_RUN**; single writer bytes observed, not a two-writer attribution acceptance. |
| Mixed/partial data | Deterministic processing PASS only; real controlled mixed case **NOT_RUN**. |

The decisive final run (`vm12`) captured268 numeric events, including54 issue,
66 completion,30 free and12 insert records. **All162 request records had
alloc_time_ns=0**. The reducer explicitly refuses to pair a reused pointer with no
allocation generation: unknown_request_generation162, no device-service interval.
Thus the selected identity mechanism is unusable for this clean guest case. The
prior admission run (`vm11`) independently showed30 zero-generation request events.
Neither zero-generation identity nor absent service attribution is a passing UNKNOWN
for a deliberately ambiguous writeback case: it fails the basic controlled case.

Also, the available phase stream is incomplete (12/64 fsync enter/exit; one sequence
gap/reorder indication), despite successful workload syscalls and EOF/END. BEGIN is
not a verified all-probes-ready barrier in this harness. Missing events have **not**
been located uniquely to attachment, perf consumption or shutdown; do not claim
all missing records are terminal loss, or that draining Python stdout fixes the
whole BPF transport. This second limitation independently forbids GO.

No second architecture or request-generation workaround was started after this
decision. Lack of later scenario results is NOT_RUN, not a claimed measured failure
of CPU/reclaim/writer controls and not a hidden PASS.

## First failure, stream drain and semantics

The fixture publishes a synthetic authoritative failure atomically after measuring
the16 cycles against a disclosed test budget1ns. This is a test-process deadline,
not a production8s failure or an artificial production payment/access operation.
The pre-failure ring already exists; the first failure is read/hash-filtered once.
The original file remained byte-identical in the final guest run. The recorder
does not write it and does not stop the observed process; only the tracer stops.

Final run: first_failure stop, stdout+stderr EOF, child exit0 and END received,
stop/drain/reduction0.605699s. Full private receipt exported and its SHA verified:
c794cf66a0cef098a14b12d3197c90b25ffb09ffc3a9b87185147e4cfd1391eb.
The JSON correctly says **drain_complete=true, complete=false**. Python no longer
closes its tracer stdout without draining; whole-kernel-stream completeness remains
unqualified as described above. Failure/EOF/END/loss/open intervals are distinct.

22 new tests exercise ordering/union/intersections, PID reuse, cgroup recreation,
partial completions/requeue/merge/free, zero request generation, lost/duplicate/
unpaired records, map/ring/line bounds, first/second failures, exclusive output,
SIGTERM, resource stop, nonzero child exit and missing END. Real local pipe tests
drain102 records including a SIGINT-produced terminal tail, and reject an inherited
pipe without EOF within the deadline. These are real pipe tests, **not kernel
attribution tests**. SIGKILL/OOM of the recorder itself cannot promise final JSON.

Completion uses pre-update __data_len versus nr_bytes; upstream7.0 blk_update_request
calls the tracepoint before consuming bios. Merged-away request destination is
UNKNOWN, not guessed. Even if identity were repaired, partial/merge/requeue semantics
are replay-tested only, not qualified under induced real block lifecycle cases.
Executor syscall bytes, bio blkcg and original producer are separate. Multi-bio,
shared writeback, jbd2/worker origin and initial cgroup generations remain UNKNOWN.
Guest completion latency alone cannot prove provider/physical-storage fault.

## Resources and bounds of comparison

Final run recorder duration12.196s includes tracer startup. Userspace loop CPU
25.769ms total; maximum measured batch CPU0.399243ms/wall100.153220ms. Reduction
and save stayed below200ms CPU/10s wall (exact values in receipt; save0.621750ms CPU).
Diagnostic cgroup peak72,433,664 bytes, pids3, OOM0; quota throttling is visible.
The8s stop limit and original budgets were not increased. This is a narrow measured
PASS for those operations, **not** full burst/long-run overhead acceptance.

Same synthetic16-cycle workload: baseline median0.866893ms/max23.395210ms;
instrumented median1.202057ms/max2.667046ms. These small, serial, cache/startup-sensitive
samples cannot quantify steady-state instrumentation overhead, especially with
incomplete probe coverage. Unit CPU includes tracer/control/export work; its two
snapshots do not bracket exactly the same interval as the recorder elapsed time.
Do not divide mismatched spans or call unit accounting total kernel/host overhead.
Guest CPU counters exist, but no controlled, complete-probe kernel-inclusive
overhead comparison passed. That required gate remains **NOT_RUN / NOT_QUALIFIED**.

Raw captures, package/image artifacts, logs and source copies remain private under
`/mnt/data/fc-ru-attribution-qualification-20261114`; only safe sources and sanitized
numbers/hashes are committed. Final private log SHA256
61aea65e25305daefa00f56c0ef38e368399ef7d3712511a3fadd50d3b9ab109.
All test VMs have powered down; no recurring observer or task was installed.

## Decision and single next step

**NO_GO: do not apply this candidate to RU.** Real matching-kernel evidence rejects
request generation and complete phase coverage before advanced attribution tests.
The RU cause remains OPEN; current availability, diagnosis and candidate admission
must not be conflated.

The single proposed next step requires separate selection: redesign the bounded
producer's request-lifetime identity and verified attach/terminal coverage contract
on this same disposable fixture. Its first completion criterion is exact64/64
fsync coverage, a verifiable allocation/free generation under pointer reuse and
partial completion, no unexplained event gap, and preserved first-failure/8s drain
under original limits. Only then run the already frozen full matrix. No new RU
observation, limit increase, provider attribution or replacement decision follows
automatically from this proposal.

## Checks and integration

60 scoped tests (22 new recorder/pipe +38 existing observer/analysis) PASS;
full collection6234 PASS, source-digest/link/whitespace checks PASS. Staged public
source guard is checked before commit. No historical pins, lockfiles, tests or assertions removed. Transport
durability/access/crash/reboot/expiry/revoke/8/12/120 behavior is unchanged, not newly
qualified by these tests. This NO_GO diagnostic-only source is not packaged/deployed.
Hosted CI is separate; local checks are not a claim that every hosted workflow passed.
Ordinary PR integration preserves commits; no protected checks are bypassed.

Source695ff6c3fe7e976f38e1837ad073449a093f2702 was committed/pushed and remote SHA
verified. Subsequent integration-note changes are documentation-only. PR34:
https://github.com/Joker20380/family_connect/pull/34 . Scoped self-review5906794022
is explicitly not independent approval. At the integration checkpoint hosted
phase0 run43634152801 and Linux control43634152730 were IN_PROGRESS; Android wire
contract43634152763 completed SUCCESS. This is not whole-hosted-CI PASS. The scoped
diagnostic gate is the tested negative admission result, not a transport release.
Main was unprotected with no required contexts/rulesets; no mandatory gate was
disabled, cancelled or bypassed. Exact ordinary-merge/remote SHA receipt is retained
in PR34 after integration; source/code hashes remain in the committed JSON receipt.
