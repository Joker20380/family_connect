# P-stack × packing interaction — lab only, 21 October 2026

This extends the existing TLS→RS harness, not the production writer or a new
profiler. `packing.go` is unchanged. Parent: the full strict-drain v3 inventory
and binary `4e1ff73f20b03c3576944b2ca7cdffbe14bea6b7f6c77376e822f852e0dc4a87`.
Private results: `state-client-build/p-stack-interaction-20261021/`.

## Reproduction and boundaries

From the repository root, the one-shot preparation order is:

1. `interaction_prepare.py`: verify the entire parent inventory, copy it once.
2. `interaction_overlay.py`: bounded Mux lifecycle observations and a lab-only
   entry point to the **existing** authenticated LEGACY64/CREDIT128 negotiation.
3. `interaction_local.py <unique-label>`: real TLS + Mux + TCP fixture, RS32/32;
   A=OFF/64, B=B2/64, C=OFF/128, D=B2/128. Local loopback requires permission.
4. `interaction_prior.py`, `interaction_retry.py`: preserve old P32 evidence and
   test Q0/Q1 independently with the existing queue-retry reproducer/correctness
   tests. The pinned tree already contains dormant Q1; it is **not enabled** in
   the interaction matrix or live binary. No completion patch is reapplied.
5. `interaction_live_prepare.py`, `interaction_build.py`: derive the existing
   isolated operator/worker with finite limits and a two-end completion barrier.
6. `interaction_audit.py`: read-only production hashes/schema/journal metadata;
   no reset, renewal/timer change or rollback. Missing history is not a local gate.
7. `interaction_live.py`: the explicitly budgeted A/B/C/D/D/C plan only. It stops
   on an error; it is not an automatic retry or tuning loop. The recorded
   `--resume-proof-repair` is specific to the preserved A1 controller error and
   cannot be reused to bypass arbitrary failures.
8. `interaction_analyze.py`: offline, retain failed attempts and overlapping waits.

Scripts live in the parent fixture directory. New Go fixtures live here so the
original packing replay's `*.go` discovery does not accidentally include them.
All builds, raw events, identities and buffers stay in the ignored private capsule;
no Git push, APK, release signing, production binary/config or routing changes.
The lab source is a copy, not the older committed carrier tree. Never apply its
observation patch to product sources or an immutable prior capsule.

## Measurement contract

The P producer is the real `Mux.forward` TCP reader and `MuxStream.Write`; its
plaintext batch scheduler and Family batch implementation match the pinned
product-lineage functions byte-for-byte. Data is prebuilt, not generated on the
network critical path. Common RTO=1s/retries=8/MaxAge=20s/payload=16384, original
media A/phase0, Q0, receiver and source policy. A is **lab RS32**, not production RS8.

Local tests reuse `meshPerfEndpoint`: measured 156345875ns symmetric delay proxy,
8KiB/2ms serialization, not a reconstruction of the SFU. Faults act on first-send
ciphertext byte intervals `[64KiB+128KiB*k,80KiB+128KiB*k)`, dropping overlapping
DATA, plus adjacent reorder at 32KiB. Actual affected ranges are exported; changing
segmentation changes collateral bytes. The old observed retry-density proxy does
not identify real forward packet loss. Slow consumers sleep 80ms/16KiB. One and
two streams, exact SHA256/EOF, idle and concurrent-start controls are checked.
Local "concurrent-start" probes are not all assumed to remain inside a short bulk.

Live: each phase single4MiB, parallel2×2MiB, 64KiB echo/reverse, six32B idle echoes
and six32B echoes starting1s into single bulk, sequential with100ms gaps. Report
actual interval overlap, sample size, median, maximum and every error; never p99.
Maximum180s transfer, finite10s final drain,250s worker,280s owned systemd unit.
Every reservation, including failed A1, counts toward64MiB source/128MiB outgoing
media. No extra window/pacing/RTO variants and no more than the planned contrasts.

`observe.go` retains at most32768 metadata-only Mux events. IDs are stream IDs;
`Bytes` on `writer_selected`, `writer_returned`, `reader_frame` is the frame kind
(DATA4, FIN5, RESET6, CLOSE7, WINDOW_UPDATE8), not a byte count. Other events report
bytes. Existing per-stream retired counters remain bounded to64 entries. Samples
are100ms live/10ms local and use one host's common intervals. Writer send time
contains Family/TLS/adapter blocking; it must not be added to RS/queue/credit waits.
`SchedulerWaitMaxMS` has broader/stale enqueue semantics for controls; it is not
used as a writer-lock or WINDOW_UPDATE delay. No ciphertext reordering/inspection.

The controller validates17 application SHA256/FIN/close results, corresponding
both-end Mux byte counts and17 completed streams, empty tails/queues, terminal-free
RS drain, all DATA ACKed, and cross-end accepted=submitted=ordered ciphertext.
Only then does it signal both owned peers to close. Protocol counters are checked
again after closure. Terminal-reset zero depth never counts as successful drain.
A1's obsolete callback-count gate failed *after* delivery/drain; it remains an
excluded controller-completion attempt, not a fabricated download failure.

The original fixture intentionally suppresses its callback. `interaction_proof.py`
therefore validates the actual end-to-end byte/stream/ACK ledgers, not nonexistent
server callback rows. `test_interaction_proof.py` checks good receipt and rejects
terminal reset, missing ACK, wrong SHA256, pending tail and asymmetric credit.
