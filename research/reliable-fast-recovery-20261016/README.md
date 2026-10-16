# Bounded local fast-recovery candidate

Apply `candidate.patch` **only** to the retained UI60-4 cumulative source inventory
`e90893aee5fdc04aae1cacd296d5291ca8a743350de42334b290f08504c48fce`.
Root main, beta60 and publication commits are not replacement product baselines.
One product file changes: `carrier/reliablestream/engine.go`; two test files are added.
The patch is not installed on a phone or deployed to a gateway.

The candidate retries only the oldest unacknowledged/unsacked block, after at least
three distinct later blocks have been SACKed, at least RTO/4 after its first send.
This can happen once per block before ordinary retry recovery. Duplicate ACKs are
not counted as independent confirmations. Existing tick/writer dispatch is retained;
there is no new goroutine, timer, reader or queue. Existing retransmit events/counters
include fast retries, while Timeout counts still mean actual RTO expiration.

FRS1 bytes, sequence/epoch checks, cumulative ordering, payload/window limits, RTO,
MaxAge and MaxRetries configuration values are unchanged. The early retry **uses**
the existing retry budget; persistent loss can therefore reach retry exhaustion
earlier than baseline (up to3/4 RTO in this policy), not gain extra retries. MaxAge,
error identity and failure-before-cleanup behavior remain checked. This is a source
candidate requiring further validation, not permission to replace accepted binaries.

## Reproduce without live services

Prepare `state-client-build/reliable-fast-recovery-1/` with immutable `baseline/`
and separate `candidate/` copies of the retained UI60-4 source. Apply the patch only
to candidate; copy its `carrier/reliablestream/throughput_comparison_test.go` to
baseline at the same path. Do not copy the fast-recovery-only unit tests to baseline.
Copy `seal.py`, `run_checks.py` and `summarize.py` here. The existing local Go1.26.1
SDK/module/build caches under the retained resume-tools path are prerequisites;
there are no downloads, provider APIs, production credentials or server dependencies.

Run `python3 seal.py`, then the fixed test batch with a fresh output label:

```sh
systemd-run --user --scope -p CPUQuota=50% -p MemoryMax=2G -p TasksMax=128 \
  python3 /absolute/path/state-client-build/reliable-fast-recovery-1/run_checks.py run-1
python3 summarize.py run-1
```

The runner refuses an existing output directory. It uses GOMAXPROCS1/-p1, offline
modules, a75°C pre-start limit,85°C cutoff and bounded process-group termination.
Fixed normal/race repeat counts are3/2 for both variants; targeted inherited
regressions run once normally and once under race. No retry-until-pass. Thermal
interruption is an incomplete run, never PASS; do not remove the guard to complete it.

## What the comparisons mean

The same13-case fixture uses the real engine plus FRS1 encode/decode, a virtual clock,
1MiB synthetic exact bytes,60ms one-way delays,6ms serialization per data block,
10ms steps and100ms ticks. It separately exercises data loss, reordering, reverse
ACK delay/outage, duplicates and consumption delay. Model throughput is **not** a
phone, TLS/mux, VP8/SFU or mobile-network bandwidth measurement.

A separate real `Stream` test uses the existing in-memory endpoint adapter and
async writer/receive queue, drops one head block, transfers129600 exact bytes and
checks the actual retransmit/timeout path. Wall time is local only; no controlled
mobile comparison or new JNI/APK/gateway executable is built.

Long reordering is an intentional negative tradeoff: when originals arrive after
the grace period, early retries may be redundant. They are not proof of network loss
and are not hidden by the completion-time improvement. A successful model does not
prove the primary bottleneck in export9 or repair the separate cutover failure.
