# Exact94/b9 Mux credit capsule

Completed20 October2026. No functional production patch. See
`docs/releases/2026-10-20-mesh-mux-credit.md` and its evidence JSON.
Private working artifacts: `state-client-build/mux-credit-20261020/`.

## Reproducible source

`prepare.py` pins exact accepted b9 binary/source inventory, then applies only
the hash-pinned existing `mesh_perf3/accepted-overlay.patch` and
`counter-only.patch`. The latter adds bounded credit increment/interarrival,
freed-ring-to-scheduler, protocol-error and memory counters to the existing
export. It excludes full media/RS packet rings. No credit/RTO/RTP/window policy
changes; bootstrap1011 files must remain exact. `check.py` copies two delta tests,
runs affected race suites or builds the observer. Existing workdir must not be
overwritten; preparation fails if it exists. Current observer is **not deployed**.

`model.py prepare` uses retained matrix counters for a symmetric effective delay
proxy and retry-density fault sensitivity. It copies three private matched-pair
fixtures; only `MuxWindow` changes to128/256KiB in those local fixtures. Never use
these trees to build a production gateway. `model.py run` enables the opt-in
`TestCreditMeasuredModel`; `model.py regressions` runs ordinary tcpforward race
checks with the model skipped. Logs are numbered, previous failures retained.
Offline Go toolchain/module cache paths come from `prepare.py`; race/integration
tests need permitted loopback sockets (sandbox EPERM is not a product failure).

Model workload:512KiB total,1/4 streams, delay-only/drop-reorder, fast/slow reader;
actual Family TLS + Mux + RS. Fixed45s case deadline,40s fixture socket deadline,
single bounded held reorder packet, byte equality and zero retained accounting
after close. One sample per cell; no statistical/physical speed acceptance.
The drop density is derived from retries, not a claim of actual forward loss.

## Measurement and interpretation

`measure.py` reuses the hash-pinned existing Android-TUN request function and
bounded collector. Counter/schema/session gate precedes traffic. It measures
24MiB exactly (1×4,2×2,4×1, reverse),150s/request, no retry. Device topology,
exact94 hash and observer PID/hash are preconditions. It refuses existing target
or traffic reservation. Do not rerun an historical matrix to regenerate evidence.
`rollout.py` wraps the pinned guarded transition implementation and permits only
counter variant a; every transition uses fresh current-state guards/intents.
No old intent/security history may be replayed. `final_control.py` verifies exact
94/b9 and uses one64KiB phone control, not a second bulk run.

Physical corpus:117 compact snapshots,221 process/socket samples,14 requests.
`summarize.py` is offline: reassembles existing journal, checks consistency,
derives real new bulk Mux IDs by lifetime/byte totals and socket maxima, parses
split Go JSON output, strips unused model rings and writes the sanitized evidence.
Run `python3 tests/fixtures/mux_credit/summarize.py` to regenerate from retained
private files; it does not create traffic, install anything or alter live state.

Size buckets: <=512/1024/2048/4096/8192/16384 bytes, then larger.
Duration buckets: <=1/5/20/80/200/500/1000/5000ms, then larger.
CreditIntervals are NL WINDOW_UPDATE **interarrivals**, not end-to-end return
latency. ReturnQueueDelay is that endpoint's freed-ring→scheduler selection,
not Android timing when collected on NL. Ready-zero and queued-ready waits can
overlap; never sum them or multiply point-sample counts into exact durations.
Whole-session RS deltas use bracketing samples including background/edges.
Body-only curl intervals start with the first response byte, an approximation.

Memory includes fixed allocated Mux rings, not only unread DATA. Per-stream
bounds do not bound sessions/users/process overhead. Source/test/capture hashes,
local failures and exact rollback/readiness receipts are retained in the report
and private capsule. The ordinary94 handoff is not a new version or public release.
