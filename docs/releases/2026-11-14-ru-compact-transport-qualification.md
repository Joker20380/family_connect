# RU compact transport — feasibility NO_GO

14 November2026, over PR35/main `0d689d32fa1c9d164c8d123e4800518ecab611f6`.
Decision: **NO_GO_PREFLIGHT** for the selected unbatched direct-output format.
This is the expressly permitted capacity/short transport experiment BEFORE a full
probe rewrite, not a claim that Gates A/B/C ran. No alternative architecture, limit
increase, workload pacing, production access, RU collection or persistence change.
Historical695ff6c3/417edbe2 remain NO_GO; PR33 analysis complete / RU CAUSE_OPEN.
Android125/catalog8/tablet/paid125/support/notifications/CI32 remain accepted.

Executable file hashes, compiled layout and all numeric per-CPU/kind receipts are
in the [sanitized manifest](2026-11-14-ru-compact-transport-qualification.json).
Raw LLVM, logs, build products and final image remain private in
`/mnt/data/fc-ru-attribution-compact-20261114`. Original checkout edits are untouched.

## Measured layout, not text-format guessing

The old bpftrace0.25 producer ALREADY sends binary printf arguments through its
shared ring. Shortening the format string does not shrink those records. Actual
7.0.0-30/BTF codegen produced LLVM SHA256
`fa485109825fb675d1af53ae851de92311af2920da7dc2c52aa04cf3aee44917`.
`ru_compact_layout.py` reads constant byte lengths passed to helper130, associating
the compiled kind field with each call; it rejects missing or inconsistent kinds.
Lengths include the printf ID, narrowed argument types and compiler padding.
The exact kernel BTF defines `bpf_ringbuf_hdr` as8 bytes (len/pg_off, two32-bit fields).
Occupied size is round_up(payload+8,8); it is NOT a uniform96-byte old record.

| Kinds | Old helper payload / occupied B | Compact payload / occupied B |
| --- | --- | --- |
|1–5,8,17–19,23|56 /64|24 /32|
|6,16,27|64 /72|32 /40|
|7,28|72 /80|32 /40|
|9|64 /72|24 /32|
|10|72 /80|40 /48|
|11–13,15|88 /96|48 /56|
|14|88 /96|40 /48|
|24,25 fences|56 /64|16 /24|
|26 allocation|64 /72|40 /48|
|29 proposed task binding|not in v2|32 /40|

Old BEGIN/END metadata has24-byte payload; map-print control12, map entry40 and
runtime-error20 also exist outside normal window events. They are not silently
counted as watcher events. Compact terminal maps do not use the transport ring.

The frozen v2 burst histogram has1871 records, including four CPU fences. Its
old occupied volume is150232B; selected compact volume82896B, a44.82% reduction.
That is still2.53× the32768B TOTAL ring, shared by both CPUs. Even1871 header-only
records would occupy44904B with this16-byte header. No hidden event queue: one
ring,32×2 fixed counter entries, one config,4096 retained records (196608B), and
bounded shared driver counters only. Map counters contain no queued event payloads.

## Chosen prototype and boundaries

One minimal approach: existing clang21/libbpf1.6.3, a small C producer using
`bpf_ringbuf_output`, and a C `ring_buffer__consume_n` consumer. Extracted compiler
headers/packages were used without installation on the owner host. No new dependency
or lockfile change in the product. Exact kernel/BTF match is asserted in the guest.
The protocol's C static assertions and real consumer verify header16/max48/alignment8.

Header v3: monotonic u64, per-CPU sequence u32, version/kind/CPU/length u8 each.
The supported CPU set is exactly0,1; sequence overflow is latched, never wrapped.
Proposed semantic payloads retain task-ref/result, fd, cgroup, generation, byte counts
and flags. An immutable task binding would carry PID/TID plus birth identity;
allocation carries generation and pointer, subsequent request records generation.
The existing generation/flush algorithms would remain necessary. **This preflight
emits synthetic payload tokens, not a completed implementation of those bindings.**
No claim of full watcher/probe identity qualification follows from compact framing.

Input is the PUBLIC v2 per-CPU/kind histogram. A synthetic guest getpgid driver
emits that histogram without pacing, in CPU/kind order; successful syscall invocation
counts are independent shared counters. They are NOT an fsync-operation ledger.
The producer filters the already-created target PID; successful link attachment and
consumed start fences on both CPUs precede release. It does not use BEGIN or sleep
as readiness. The driver is the observed workload in writer1, not diagnostic runtime.
Loader, consumer, audit and serialization stay in diagnostic. Python re-execs after
cgroup entry so startup allocations are accounted; the earlier exploratory VM2's
migration-only memory observation is not the final memory result.

This short test deliberately stresses peak delivery; it does NOT reproduce the old
event ordering or timings. Old ledger duration63.174680ms and fenced window102.834623ms
must not be substituted for the missing per-event timestamps of1398 lost v2 records.
It is not proved that all1871 old events arrived in one90ms pause. The measured
rejection is of this format's bounded peak feasibility, not a theorem that every
possible compact encoding or the unported original workload must fail.

## Direct accounting and measured peak

Each supported CPU/kind records hits, attempted, submitted, failed, discarded and
overflow. Output API has no discard path: discarded=0. Normal conservation requires
`ledger=hits=attempted=submitted=received=decoded=retained`,
`attempted=submitted+failed`, and failed/discarded/overflow=0, PER KEY as well as in
total. Sequences and one start/end per CPU reject equal-count loss/duplication.
Counter/range faults remain rejection even when ordinary event totals agree.

Final exact-source VM3, seven finite cases, no pacing or quota-phase alignment:

| Case | Ledger / hits / attempts | Submitted / received / decoded / retained | Failed | Result |
| --- | ---: | ---: | ---: | --- |
|Normal peak0|1871 /1871 /1871|1790 each|81|reject|
|Normal peak1|1871 /1871 /1871|1519 each|352|reject|
|Normal peak2|1871 /1871 /1871|1871 each|0|transport-only pass|
|Quota pause|1871 /1871 /1871|652 each|1219|reject|
|Sequence-overflow injection|1871 /1871 /2|2 each|0|reject,1869 refused events plus2 global overflow latches|
|Invalid-kind injection|1871 /1871 /1871|1850 each|21|reject,2 explicit invalid-kind latches|
|Stop during stream|323 /323 /323|323 each|0|reject,missing end fences|

Quota-pause control waits for independent cpu.stat `nr_throttled`12→13 before the
driver emits. The consumer uses its SAME quota to reach throttling, not a sleep or
an unaccounted auxiliary consumer. Emission0.492981ms, maximum processing-batch
wall98.365374ms; maximum callback gap157.592054ms includes terminal detach/drain and
is NOT a pure CPU wait measurement. Its first two fences were consumed before the
pause. The remaining650 successful records occupied32760B; with48B already consumed
fences totalreceived=32808B. The smallest next record needs24B: the measured ring
boundary is exhausted. 1219 helper failures reconcile exactly with missing input;
no parser/retention loss, discard or unexplained upstream gap is concealed.

Normal peak2 consumes1871 records in0.587496ms of measured consumer+drain CPU
(about3.18M records/CPU-second); driver2.291101ms (~0.817M records/wall-second).
This is a microbenchmark, not sustained end-to-end throughput. The normal three
emission durations are0.774134/0.583094/2.291101ms; losses in two of them demonstrate
why average speed or one favorable quota phase cannot admit the format. Compiler
setup and prototype iteration VM1/2 are preserved privately, not substituted for
these final-source numbers. VM1 also provided the unchanged v2 compiled layout.

## Terminal, first failure, resources and matrix

The sole synthetic producer joins, config is disabled, the link detached, terminal
maps read independently of the ring, retained transport drained to empty, then maps
reread byte-equal. All seven cases meet that completion contract (drain43–60ms).
Lost END fences do not prevent terminal accounting. A valid terminal snapshot does
NOT turn failed output into complete delivery. C exit0 means experiment terminated;
harness exit1 rejects feasibility, exit2 would require Gates A/B/C, never mean GO.
No code path returns full GO. Missing terminal/error/timeout is fail-closed.

| Requirement | Result for this candidate |
| --- | --- |
|Gate A: original16 cycles/64 enter/64 exit/64 unique fsync pairs|NOT_RUN after preflight rejection. Histogram kind6/7 counts are not real fsync pairs.|
|Gate B: allocation/reuse/partial/requeue/merge/batch release|NOT_RUN; v2 unchanged, replay is not kernel qualification.|
|Gate C: runnable CPU, direct reclaim, guest queue, guest service, two writers|each NOT_RUN after rejection|
|Gate C: mixed/incomplete causal intervals|NOT_RUN; framing-negative tests are not this mechanism scenario.|
|Matched full probes-off/on overhead|NOT_RUN; microbenchmark CPU is not full kernel/host overhead.|
|New first-authoritative-failure integration|NOT_RUN; prototype does not touch a failure file. Old immutable-first-failure and1ns-fixture tests still PASS, not8s production reproduction.|
|Overflow, sequence overflow, invalid map/kind, active stop|real guest controls reject; exact successful/failed-output accounting retained.|
|Equal-total loss+duplicate, damaged/partial frame, absent/live terminal, boundaries, capacity|deterministic tests reject; separately labelled, not real kernel injection.|

Limits unchanged: shared32768B ring; guest diagnostic cpu.max10000/100000,
memory.max268435456, swap0, pids.max24; retained4096, counter slots64 (<256),
runtime10s/case, stop8s, final<8MiB/stderr<1MiB, total diagnostic output<18MiB.
Consumer batch≤256 records (≤12288 payload bytes), independent terminal read≤64
entries; setup/reduction/audit/serialization measured separately. Guard latch never
clears; any CPU>200ms/wall>10s rejects, including final save. Host VM remains capped
at one core/2GiB/no swap/32tasks/240s, two guest vCPUs/1536MiB,128MiB RAM disk,
no network or host mount; this is not permission to move runtime out of diagnostic.

Final diagnostic memory.peak14495744B, pids.peak3, zero OOM/max/swap events.
Maximum C bounded-operation CPU7.955993ms, wall98.365374ms, no guard violations;
Python audit max1.431551ms CPU/1.438730ms wall, final save1.892684/1.906451ms.
C saves≤0.183957ms CPU. Per-case diagnostic CPU3.443–18.443ms includes setup but
not all probe execution charged to the synthetic target; not total host overhead.
No calibrated probes-off/on comparison is claimed. SIGKILL/OOM cannot promise a
terminal JSON. Unknown shared-writeback origin, partial lifetimes and actual RU
deadline cause remain UNKNOWN; the prototype does not classify them.

## Decision and next boundary

**NO_GO before full implementation**, as allowed by the selected task's capacity
gate. One unbatched format was built/tested; it cannot absorb the demonstrated peak
during a legitimate quota pause with32KiB. Keeping a second payload queue, raising
quota/ring, pacing, sampling or omitting event kinds was not used to manufacture GO.
Gates A/B/C were never passed, so their conditional continuation was not triggered.
This is a completed negative feasibility decision, not INITIAL_GATE_PASS or BLOCKED.

Single next action: retain the deployment prohibition and obtain a separately scoped
architecture decision, with an explicit worst-pause capacity proof before another
implementation. Required evidence for reconsideration: bound queued bytes during
the measured quota pause to the existing32768B INCLUDING headers, with no excluded
events/unaccounted queue, then real original burst and ALL lifecycle/matrix gates.
No alternative is selected or started here. No further RU monitoring is proposed.

## Checks and integration

90 scoped deterministic/pipe/analysis tests PASS; complete collection6264 PASS.
Both C targets compile with the pinned clang/libbpf headers and GCC `-Wall -Wextra
-Werror`. LLVM size parser tests cover all kinds, missing kinds and contradictory
helper sizes. Existing73 tests, historical pins/lockfiles and all original probes
are unchanged. Local source/doc/whitespace checks and staged public-source guard
precede commit. Hosted CI is separate; no claim of whole-workflow success from
local tests, VM poweroff or inner terminal success. Integration details follow in
the documentation-only receipt after source push and ordinary PR review.

Executable source **ea19c1d751cfb330ad1f9f503e650cdee27151c3** is committed/pushed;
remote branch SHA verified. [PR36](https://github.com/Joker20380/family_connect/pull/36)
preserves it separately from this documentation-only integration receipt. Scoped
review5907383301 is explicitly SELF-review, not independent approval. At22:05UTC
main remained0d689d32, protected=false, required contexts/checks empty, rulesets=[];
no mandatory check disabled or bypassed. Source PR phase043646233529, Linux
control43646233437 and readiness43646233533 were IN_PROGRESS at22:07UTC, not green.
The applicable isolated diagnostic gate is a completed negative result; no product
release/requalification is authorized. Final merge/remote SHA is verified separately
from hosted completion and retained in the PR receipt. All VM units are inactive;
no collector, schedule or runtime deployment was left behind.
