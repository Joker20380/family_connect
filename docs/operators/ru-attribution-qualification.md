# RU first-failure candidate: isolated qualification only

**Outcome: NO_GO**, both original695ff6c3 and the separately qualified v2 candidate.
See the [measured qualification report](../releases/2026-11-14-ru-first-failure-qualification.md).
The original allocation/attach assumptions are rejected, not normative instructions.
V2 uses verified attach/CPU fences and bounded request generations, but still loses
the original healthy burst between producer attempts and consumer input under the
unchanged limits. A paced control is NOT admission. Advanced real mechanisms remain
NOT_RUN after the failed original burst gate; do not start a production capture.

This is not an installation or capture runbook. No production probes are authorized.
V2 baseline is PR34/41ada7cf; PR33 FINAL_ANALYSIS_COMPLETE / CAUSE_OPEN remains unchanged.
The candidate uses existing bpftrace0.25 and numeric ring-buffer output, not a new loader.
Despite its historical name, `perf_rb_pages=8` configures ONE shared BPF ring buffer
of8×4096=32768 bytes here, not8 pages per CPU. Keep8; doubling it is not an allowed
repair. `printf` exposes attempts, not successful transfer, to the bpftrace program.
Taskstats is not used: RU `kernel.task_delayacct=0` for the live watcher. Enabling it
or restarting the watcher is outside scope. Read-only capability receipt14November
identifies7.0.0-30-generic, ext4/vda1, cgroupv2 and the required tracepoint formats.

## Frozen matrix before kernel tests

All real loads must run inside a disposable KVM guest on the exact7.0.0-30 kernel,
no network, no host filesystem mount, dedicated small RAM-backed virtual test disk,
at most2vCPU/1536MiB guest RAM. No host/production stress, shared application volumes,
or VM memory overcommit. Stop the guest after the finite matrix; retain numeric
receipts only. The diagnostic cgroup must set cpu.max10000/100000, memory.max256MiB,
memory.swap.max0 and pids.max24, matching the accepted unit limits. Each processing
batch reads at most64KiB per pipe; aggregation and final serialization are timed
separately with the same200ms CPU/10s wall guard, not excluded from qualification.

| Scenario | Independent control | Required evidence |
| --- | --- | --- |
| Healthy synthetic persistence | workload counters, fsync return values, strace-free timestamps | state write/file fsync/rename/dir fsync then attempt write/file fsync/rename/dir fsync; no invented cause |
| Runnable CPU wait | pinned competing task plus /proc/TID/schedstat delta | runnable interval grows, not classified blocked |
| Direct reclaim | private guest cgroup memory.high and memory.events/pgscan_direct deltas | observed task reclaim events overlap its waits; no host memory pressure |
| Device queue delay | guest scheduler/queue settings and independent block trace | insert→issue distinguished from service, or explicit NOT_RUN if injection cannot be verified |
| Device service delay | dedicated guest dm-delay/controlled virtual backend and independent completion timing | issue→completion at named guest boundary, not physical-provider blame |
| Two writer cgroups | separate private group io.stat and workload byte counters | executor and bio blkcg distinguished, merged/shared provenance UNKNOWN |
| Mixed/incomplete | combination of verified controls plus deliberately dropped/reordered synthetic records | overlapping intervals, lost/unpaired data and residual, no unique invented cause |

Compare identical healthy and bounded-burst workloads without/with probes; measure
guest workload latency, recorder/tracer CPU and RSS, guest total CPU as a noisy
kernel-inclusive bound, event counts and loss. Unit accounting alone is insufficient.
Any measured limit violation or inability to distinguish a required clean case is
NO_GO. An unavailable experiment is BLOCKED/NOT_RUN, not a successful qualification
and not a measured defect. Do not raise limits or start an alternative architecture.

## Numeric protocol and limits

Each line is `E mono_ns cpu sequence kind subject birth a b c d result`. Kind1/2/3
is switch-out/wake/switch-in,4/5 direct reclaim,6/7 fsync,8/9 rename,10 successful
write bytes,11/12/13 request insert/issue/requeue,14 completion,15 merged-away
request,16 free,17/18 cgroup creation/removal,19 task exit,20/21 stream begin/end,
23 explicit loss. PID/TID plus start_boottime is scoped by saved boot ID. Watcher
selection checks leader start ticks (this target has CLK_TCK100). No names, paths,
argv, environment or file contents are emitted. Request addresses are private
ephemeral correlation tokens, never public evidence. `alloc_time_ns` is conditional
and is NOT a lifetime ID. V2 uses bounded per-CPU generation counters at the exact
kernel's `blk_mq_rq_ctx_init.isra.0`, plus `blk_rq_init` generations for reused internal
flush requests. It checks `__blk_mq_free_request` and the32-tag batch release through
`blk_mq_put_tags`; a hook's presence is not proof its path was exercised. Reset may
retire a previous internal flush generation only after its observed completion.
Unknown initial requests, reuse without a terminal, map overflow and open terminal
requests stay explicit. No universal free-path qualification is claimed.

Kinds24/25 are per-CPU start/end fences;26 allocation/reset generation;27 lifecycle
conflict;28 `blk_insert_flush` (length/flags). Completion carries pre-update rq_flags;
exact7.0.0-30 headers define RQF_FLUSH_SEQ as bit1. A completed data transfer with that
bit remains `flush_wait`; the later zero-byte logical completion after bit clearing
is not another device service interval or a duplicate. Ordinary partial completion
is an observation, not stream loss. Real partial/batch/requeue/merge controls remain
unqualified until exercised independently; deterministic replay is separate.

BEGIN runs before ordinary attachment in0.25 and must NEVER release workload.
Require the pinned tracer's `__BPFTRACE_NOTIFY_PROBES_ATTACHED` marker with
`missing_probes="error"`, then a separate pinned controller's start fence on every
participating CPU, consumed by the recorder. This proves consumer readiness without
restarting the already-running target. End fences use the same controller before
SIGINT. CPU hotplug/changed affinity is unsupported, not silently covered.
The independent ledger records each successful syscall's TID,fd and monotonic
begin/end; require64 enter AND64 exit AND64 unique matching pairs, not just totals.
Per-CPU/kind terminal C counts reconcile hits/attempts with parsed/retained records;
sequences and fences expose missing prefix/tail and duplicates. No internal gap
alone can prove completeness. Successful transfer count is UNKNOWN when attempted
and received disagree; the exact missing site within ring/formatter is not guessed.

Regular block tracepoint formatted fields lack request identity. Raw tracepoints
expose the actual request; exact matching kernel headers define complete(rq,error,
nr_bytes). Completion is partial when nr_bytes<the pre-update __data_len. Requeue
ends the current service segment, and merge discards unresolved destination rather
than inventing linkage. This semantic assumption must be verified on the guest.
Bio blkcg is recorded only for a single-bio request; merged/multiple-bio provenance
is UNKNOWN. Executor cgroup is NOT the original data producer. A guest request wait
does not establish storage-provider fault. Cgroup creation/removal supplies observed
generations; pre-existing groups explicitly retain unknown initial generation.

Retain at most4096 events/60 batch receipts,256 pending identities/groups,8MiB final,
1MiB stderr counted/hashed but not copied, total≤18MiB RAM, stop≤8s, duration≤24h.
Stream sequences detect retained gaps; eviction is counted, never hidden. Intervals
are unioned, with overlap and unclassified phase time; no addition of overlapping
blocked/reclaim/device waits. EOF, child exit, END marker and loss are separate.
SIGINT stops only the child tracer, both pipes are drained, then final is serialized;
six seconds without terminal completion forces kill and incomplete=true semantics
(`complete=false`). Active intervals remain unpaired. SIGKILL/OOM cannot guarantee
a final receipt. The first authoritative failure is read/hash-filtered once, never
written or replaced; later failures cannot replace it. Production launcher absent.

## Reproduction

Run deterministic/pipe checks with the project's locked environment:

```sh
python -m pytest -q tests/test_ru_attribution_recorder.py tests/test_ru_attribution_contract.py
```

The executable harness reports negative admission, not a full matrix implementation.
On a genuine initial PASS, the selected task requires continuing the frozen matrix,
not accepting GO. No such original-burst PASS occurred. Existing pressure observer
remains stopped and unchanged. Kernel compatibility is not attribution GO.

Recorder CLI exit0 means pipes drained and measured resource checks passed, NOT
kernel completeness. V2 separates `window_complete`, `phase_complete`, lifecycle
validity, and causal UNKNOWN. The legacy `complete` field is not the v2 gate.
Lab exit1/NO_GO_INITIAL_GATE rejects burst admission; exit2 requires the full matrix;
exit0 in paced/readiness modes means that auxiliary experiment ended, not GO.
The exact30-byte `WARNING: Addrspace is not set` is retained/hash-counted and only
explicitly allowed in this pinned fixture (legacy probe_read fallback). Other stderr,
including loss warnings, rejects admission. Do not suppress all tracer warnings.
CPU/wall guards cover batches, reducer, v2 audit and serialization. Violations latch
outside the60-receipt ring. Failure-file hash remains unchanged;1ns fixture budget
tests publication only, not the production8s failure. EOF/END/exit0/drain≤8s remain
separate from producer reconciliation and retained endpoints. SIGKILL/OOM promises
no final JSON. Unit accounting excludes some kernel/host overhead.

Use explicit extracted packages, never install them on RU or the host. Required
guest kernel/image/modules package7.0.0-30.30, QEMU10.2.1, bpftrace0.25 and local
Python3.14 runtime. Builder copies local binary dependencies/UAPI headers and makes
module dependencies; it also provides /dev/fd needed by this bpftrace compiler.

```sh
python3 scripts/ru_attribution_vm.py --kernel "$PRIVATE/kernel" --output /dev/shm/fc-attribution-replay
truncate -s 128M /dev/shm/fc-attribution-replay/test.raw
systemd-run --user --unit=fc-attribution-replay --collect --wait \
  -p CPUQuota=100% -p MemoryMax=2G -p MemorySwapMax=0 -p TasksMax=32 \
  -p RuntimeMaxSec=240 -p Nice=19 \
  env LD_LIBRARY_PATH="$PRIVATE/qemu/usr/lib/x86_64-linux-gnu" \
  "$PRIVATE/qemu/usr/bin/qemu-system-x86_64" \
  -L "$PRIVATE/qemu/usr/share/qemu" -bios "$PRIVATE/qemu/usr/share/seabios/bios-256k.bin" \
  -enable-kvm -cpu host -smp 2 -m 1536 -nodefaults -no-reboot \
  -nographic -serial stdio -monitor none -nic none \
  -kernel /dev/shm/fc-attribution-replay/vmlinuz \
  -initrd /dev/shm/fc-attribution-replay/initramfs.cpio.gz \
  -append 'console=ttyS0 panic=-1 rdinit=/init quiet' \
  -drive file=/dev/shm/fc-attribution-replay/test.raw,format=raw,if=virtio,cache=none
```

Set PRIVATE to the private qualification directory; require an unused output/unit
name and adequate RAM. Capture the unit journal privately. FC_CONTROL receipts,
FC_RESULT, FC_DECISION and FC_LAB_EXIT determine outcome; QEMU shutdown exit0 alone
does not mean qualification PASS. FC_CAPTURE contains private numeric raw events:
decode base64 and verify capture_sha256 before analysis; never commit that payload.
The exact measured run used an equivalent redirected private serial log. Stop only
this disposable VM unit if its240s outer limit is reached; never pkill host workloads.
Rebuilding reproduces the environment, not an identical cpio digest (file times and
local runtime packages matter). The exact tested image and its hash are retained
privately in final-vm; recorder/trace/harness hashes also match the committed receipt.

For the separately retained v2 image/source receipts use the
[v2 report](../releases/2026-11-14-ru-attribution-v2-qualification.md), not final-vm
from the original695ff6c3 candidate. Default builder selects v2; `--legacy` selects
the old harness. The ordinary command above is the original burst. Appending
`FC_LAB_MODE=readiness` runs only the minimal old/new barrier reproduction. Appending
`FC_LAB_PACE=0.2` deliberately lowers rate for a lifecycle diagnostic and NEVER passes
the original burst gate. Kernel passes these assignment arguments to init's environment.
All runs require separate unit/log names and sequential exclusive use of test.raw.
