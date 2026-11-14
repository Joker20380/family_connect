# RU attribution v2 — bounded transport admission / NO_GO

14 November2026. This is a separate candidate over PR34/main41ada7cf, not a
replacement of the historical695ff6c3 NO_GO. PR33 analysis remains complete and
RU **CAUSE_OPEN**. No production access, probes, restart, installation, third RU
capture or product persistence change occurred in this continuation. The original
dirty checkout is untouched. Closed Android125/catalog8/tablet/paid125/support/
notifications/CI acceptances remain closed; no state, key, baseline or guard changes.

## Contract repairs and scope

- `ru_attribution_program.py` replaces the old BEGIN readiness assumption with the
  pinned0.25 attach notification, strict missing-probe errors, then CPU-specific
  controller fences observed by the consumer before releasing a waiting synthetic
  target. The target already exists before attach; no target restart is needed.
- Allocation generations no longer use conditional `alloc_time_ns`. The exact
  kernel's `blk_mq_rq_ctx_init.isra.0` covers normal/batched initialization. Per-CPU
  bounded counters generate distinct tokens; allocation over a live generation,
  counter/map failure and unknown initial requests are explicit. Internal persistent
  flush requests use `blk_rq_init` generations. Single final free and32-tag release
  hooks cover the selected paths; unexercised batch paths are NOT qualified by symbol
  presence alone. Linux v7.0 source inspection is corroborated by the exact Ubuntu
  image's BTF, System.map and disassembly, not claimed to be downloaded Ubuntu C source.
- A normal flush sequence completes data first, then its logical request after
  postflush. The data-completion RQF_FLUSH_SEQ bit, cleared at logical completion,
  distinguishes this from a duplicate or another device service interval. Internal
  flush requests instead retire on reset after their completed service. This was
  measured and corrected during preparation, not hidden as transport loss. Partial
  completion remains a normal observation; unexplained second completion is rejected.
- `ru_attribution_contract.py` independently matches every ledger syscall (TID,fd,
  monotonic interval,return0) to one enter/exit pair with a consistent task birth.
  Equal-count loss+duplicate is rejected. Per-CPU fences/sequences plus per-kind
  hit/attempt/parse/retention reconciliation expose prefix, tail and internal losses.
  Generations and cgroup/task lifecycles remain boot-scoped. CPU hotplug is unsupported.
- Pipe EOF/END/exit status, kernel-window completeness, phase coverage, lifetime
  validity, normal observations and causal UNKNOWN are separate. `printf` attempts
  are NOT successful-transfer acknowledgements. Old reducer `complete` is not the v2
  admission verdict. An exit0 process is not GO; the runbook specifies all exit codes.
- Batch CPU/wall violations latch independently of receipt eviction or a later stop
  reason. Reduction, audit and serialization are measured separately under the same
  limits. Terminal fences precede tracer SIGINT; both pipes are drained, not closed
  prematurely. The first failure is read/hash-filtered once and never written.

## Exact environment and interpretation of limits

Same prepared KVM guest: Ubuntu7.0.0-30.30, BTF matching retained RU capability
evidence,2vCPU/1536MiB, network disabled, no shared host filesystems. A dedicated
128MiB RAM-backed virtio disk is freshly formatted ext4 per run; no application data.
Host VM unit100%core/2GiB/swap0/tasks32/240s is separate from diagnostic guest cgroup
**10%core/256MiB/swap0/tasks24**. No limits were increased. Recorder4096 events,
60 batch receipts,256-key maps,8MiB final/18MiB total RAM files,200ms CPU/10s wall
per bounded operation,8s stop remain unchanged.

bpftrace0.25 uses ONE shared BPF_MAP_TYPE_RINGBUF. Historical configuration name
`perf_rb_pages=8` means32768 bytes total on this4096-byte-page guest, **not per CPU**.
Upstream0.25 `IRBuilderBPF::CreateOutput` calls `bpf_ringbuf_output`, counts negative
returns, and does not expose success to script printf. Thus terminal attempts are
an independent upper-stage counter, not proof of delivery. The pinned binary hash,
kernel/BTF/image/source/log/capture digests are in the sanitized v2 receipt. Exact
30-byte Addrspace warning is retained and explicitly recognized as legacy probe_read
fallback; no blanket suppression. All other stderr, including loss, rejects admission.

## Attach versus transport: measured distinction

The minimal BEGIN/attached reproduction is retained in `readiness_repro()` and
private vm20. Kernel BEGIN16133652467 preceded attach notification consumption
16134377022; consumer BEGIN16134507828 followed it. The alternate attached run had
23035723259/23036843665/23037224073 respectively (monotonic ns in that guest).
Both minimal runs obtained64 ledger/64 enter/64 exit, stderr0 and complete drain.
Therefore the old barrier is invalid by implementation order, but **zero missing
fsyncs were explained by startup alone in this minimal experiment**. It does not
retroactively assign all52 old missing pairs to attach. New full-program burst
loss persists after verified attach/fences and all128 producer fsync hits.

Preliminary paced vm19 printed INITIAL_GATE_PASS in an intermediate harness. It
had0.2s spacing and is expressly NOT the required burst admission. The corrected
harness labels paced controls PACED_DIAGNOSTIC_ONLY_NOT_ADMISSION. Preparation
vm22/24 identified flush completion modeling errors; their original captures remain
unchanged. Final results use the corrected source, not those intermediate verdicts.

## Frozen matrix and decision

Final source-file digests and exact image56b6a2825d0d1361ad2db43a89442c8d28917a6328ec2e560aa3149671e7c882
are preserved in the [sanitized v2 receipt](2026-11-14-ru-attribution-v2-qualification.json).
Final vm25 is original burst; vm26 is the separately labelled paced control, both
on identical candidate files/image. The original request above remains the admission
workload; pacing is not a fix or an independent CPU/queue-delay injection.

| Accounting | Original burst vm25 | Paced control vm26 |
| --- | ---: | ---: |
| Independent successful fsync ledger |64|64|
| Producer enter / exit |64 /64|64 /64|
| Parsed enter / exit / unique pairs |17 /16 /16|64 /64 /64|
| Window hits = attempted records |1871|1914|
| Parsed = retained window records |473|1914|
| Metadata BEGIN+END, additional |2|2|
| Total wire = parsed = retained |475|1916|
| Invalid / eviction / accounting overflow |0 /0 /0|0 /0 /0|
| Missing attempts CPU0 / CPU1 |916 /482|0 /0|
| Known new generations / completed |72 /72 (incomplete stream)|288 /288|
| Reused addresses / ordinary allocated reuse |2 /0|34 /32|
| Requests open at end fence |2 internal flush handles|2 internal flush handles|

Both CPUs have first sequence1/start fence and last sequence equal to their terminal
counter/end fence. Burst holes lie INSIDE this window, not an unknown attach prefix
or truncated pipe tail. Terminal attempts=hits1147/724, received231/242; no malformed
line or ring eviction hides the1398 missing records. Fsync producer proves all64+64
hits but95 fsync records never reach parser. bpftrace reports916 lost, matchingCPU0
only; own counters also expose482 onCPU1. At least the reported loss is explicitly
ringbuf output failure; additional missing events are localized to producer-output/
tracer transport, consistent with the pinned upstream last-CPU sum defect. No
successful emission counter is available per event: the finer sub-boundary remains
unmeasured, not inferred from EOF. Burst workload ledger spans63.174680ms; paced
ledger spans3.087656199s. Rate-sensitive transport overflow remains after attach fixes.

Paced full-stream lifecycle audit has no errors:160 ordinary frees,126 completed
internal resets,64 data-completion→logical-completion flush sequences and32 ordinary
pointer addresses reused with distinct generations. Two persistent internal flush
handles remain open at the end fence after completed service; explicitly censored,
not missing target fsyncs. No valid partial completion occurred in these real runs.
Replay partial checks pass, but the required real partial control remains NOT_RUN.

| Resource/completion metric | Burst vm25 | Paced vm26 |
| --- | ---: | ---: |
| Recorder elapsed including tracer compile/attach |30.710844s|29.851102s|
| Stop/drain |1.299167s|1.701143s|
| Maximum batch CPU / wall |5.142198ms /148.436041ms|1.704171ms /143.347374ms|
| Reduction CPU / wall |2.677978ms /182.900107ms|29.790875ms /308.075679ms|
| Ledger audit CPU / wall |1.235916ms /1.239802ms|13.304828ms /102.636268ms|
| Save CPU / wall |1.123873ms /1.127833ms|6.281607ms /96.654654ms|
| Diagnostic peak memory / tasks |70,619,136B /3|70,565,888B /3|
| Diagnostic CPU usage including compilation |3.042297s|2.742155s|
| Final capture bytes |66,757|216,788|

Both retain immutable first failure, no forced kill, child exit0, EOF, END, no partial
line, no CPU/wall guard violation, no OOM/swap. Final failure budget is deliberately
1ns: publication/drain fixture only, NOT a reproduction of production8s. Failure
immutability under replacement, active terminal pipe tails, SIGTERM request, tracer
error, forced incomplete drain, overflow and resource stop also pass deterministic/
real-Python-pipe regressions; those are not additional kernel-injection results.
Limits include audit/reduction/save; batch receipts cannot erase a latched violation.
The cgroup numbers are not full kernel/host overhead. Whole-guest/probe CPU overhead
and matched impact on operation latency are NOT qualified on this failed stream.

| Real scenario | Status and interpretation |
| --- | --- |
| Original16-cycle burst, four fsync/cycle | FAIL: producer executes128 phases; consumer loses records before parsing; NO_GO admission |
| Same16 cycles with0.2s spacing | Diagnostic only: tests complete stream/identity at a lower event rate, never substitutes for burst |
| Runnable CPU wait | NOT_RUN after failed original admission; incidental scheduler events are not the independent injection |
| Direct reclaim | NOT_RUN; probe loading does not prove controlled reclaim |
| Guest queue delay | NOT_RUN; no queue-latency acceptance |
| Guest issue→completion delay | NOT_RUN; no service-delay/provider attribution |
| Two writer-cgroups/background | NOT_RUN; one writer plus journal activity is not this scenario |
| Controlled mixed/incomplete kernel case | NOT_RUN; replay gaps/duplicates/UNKNOWN tested separately |
| Matched probes-off/on overhead | NOT_QUALIFIED; serial warm-cache baseline and incomplete burst cannot establish overhead |

The initial gate never passed for the original burst, so the conditional instruction
to continue the full matrix did not activate. Missing later rows are NOT_RUN, not
measured failures or PASS. Real controlled partial/requeue/merge/batch-free coverage
also remains NOT_RUN. Replay partial/reuse/duplicate/flush tests do not replace it.
An individual request address without a generation is never accepted as identity.

**NO_GO for this printf/ring-buffer candidate under the existing limits.** Fixing
attach, draining stdout and generations does not make an overflowing transport
complete. No capacity/quota increase, pacing of admission, event exclusion or
second architecture was used to manufacture PASS. No inference about historical
RU deadline cause or physical/provider storage follows from these VM results.

Single proposed next, requiring separate selection: replace the current verbose
printf event transport with a bounded compact record transport that reports actual
emission success and reconciles per-CPU terminal counts, within the SAME buffer,
CPU/memory/time limits. Completion criterion: original64+64 unique phases and64
ledger pairs without prefix/tail/gaps, real lifecycle controls and then every frozen
matrix/overhead row. This is a specific transport qualification, not indefinite RU
observation, a third production capture, a new server or a persistence rewrite.

## Reproduction and evidence boundaries

See the [updated runbook](../operators/ru-attribution-qualification.md). Builder
defaults to v2; `--legacy` preserves the old experiment. Append `FC_LAB_MODE=readiness`
only for the minimal barrier reproduction; `FC_LAB_PACE=0.2` only for the separately
labelled paced diagnostic. Plain command line is the original burst admission.
Use fresh output/unit/log names and only the dedicated disposable test disk.

Captures and synthetic pointer/boot/task identities remain private under
`/mnt/data/fc-ru-attribution-qualification-20261114`; no raw data or images are in Git.
To reproduce audit, decode FC_CAPTURE, verify its SHA against FC_RESULT, then call:

```python
import json, sys
from pathlib import Path
sys.path.insert(0, 'scripts')
from ru_attribution_contract import audit
capture = json.loads(Path('PRIVATE_CAPTURE.json').read_text())
print(json.dumps(audit(capture, capture['workload']['ledger'], [0, 1]), indent=2))
```

Per-CPU missing records are terminal attempted minus parsed counts (exclude metadata
BEGIN/END in both). Verify wire_records=events_seen and evicted=invalid=0 before
locating a gap upstream of parser/retention. Successful-transfer count within the
ring/formatter is unavailable; do not invent it from attempts. Upstream0.25's loss
sum loops CPU indices below max_cpu_id, consistent with its warning omitting the
last CPU's loss in these two-CPU runs. Own per-CPU counters, not that warning alone,
determine total gaps. This does not require changing the installed tracing tool.

Safe source/tests/docs only. No tests, historical pins or lockfiles removed or
relaxed. Transport durability/crash/reboot/expiry/revoke and8/12/120s product behavior
are unchanged, not requalified by synthetic1ns failure publication. Shared writeback
producer attribution stays UNKNOWN. SIGKILL/OOM cannot guarantee final output.

## Checks and integration

73 scoped tests PASS (35 recorder/contract plus38 prior observer/analysis), including
equal-total loss+duplicate rejection, JSON replay parity, pointer reuse, partial and
both flush completion semantics, terminal counters and guard latching. Complete
collection6247 PASS. No tests excluded. Whitespace, linked local documents and source
digests checked; staged public-source guard required before commit. Hosted CI is
reported separately, not inferred from local tests or the VM's exit0 poweroff.
All isolated VM units have terminated; no scheduled recorder or production hook exists.

Executable source **417edbe2251e1762db2122735a144e5d7380910b** committed/pushed;
remote branch SHA verified. Subsequent integration notes are documentation-only.
[PR35](https://github.com/Joker20380/family_connect/pull/35) retains the original
source commit; scoped review5907244092 is self-review, NOT independent approval.
At21:31UTC source PR runs phase043643172522 and Linux control43643172588 were
IN_PROGRESS; Android wire43643172642 was also IN_PROGRESS. No full-hosted-CI success
is claimed from these pending runs. Main protection=false, required contexts empty,
rulesets empty at21:30UTC; nothing disabled, cancelled or bypassed. The applicable
diagnostic gate is the reproducible NO_GO plus local source/test/privacy checks,
not a transport release gate. Ordinary merge and exact remote-main SHA are recorded
in the PR integration receipt after merge; production remains untouched.
