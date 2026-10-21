# Current1011 send-queue / retry control (19–20 October 2026)

This is an **exact-source experiment**, not a patch to arbitrary `main` and not
an instruction to deploy its HEAD. The live baseline is beta90 plus gateway
`b9ae880731517753e456637e52dcc421b9f7d7b881b400c856989ae93193e9ba`.
The old4b binary is NOT this experiment's fallback. Keep bootstrap1011 recovery,
current credentials, publication/floors, identity and ordinary Android recovery.
No owner guard, canary routing, enrollment, fault injection or IPv6 experiment.

## Pinned inputs and artifacts

`source-pins.json` records every changed input/output hash and each patch digest:

- `observation.patch`: current1011 accepted source → temporary server-only
  performance counters/transport trace, including first-fragment WRITING.
  Reuses accepted performance instrumentation and its checksummed chunk export.
- `completion.patch`: current1011 accepted source → functional local-completion
  candidate, without performance build tag.
- `completion-observed.patch`: observation source → the same functional
  candidate with matched instrumentation. Do not apply both completion patches.

Verify the entire accepted inventory and all touched input hashes before applying.
A missing input hash means the path must not exist. Run `git apply --check` in a
fresh copy of the intended **carrier source capsule**, never this repository root.
Verify all output hashes afterward. `seal.py` creates the patches and proves all
three fresh-copy applications reproduce their full target trees. It intentionally
refuses to overwrite artifacts or reuse existing reproduction directories.

Private sources, raw diagnostics, build/test logs, binaries and operator receipts:
`state-client-build/queue-retry-20261019/` (ignored by Git). Published fixtures do
not contain phone exports, credentials, keys, payloads or personal Support IDs.

## Functional boundary

`localwrite.Observe/Register` carries an optional, per-attempt completion through
the existing `Endpoint.SendContext` context. Wrappers still receive their original
`SendContext` calls; an embedded optional method must not bypass loss/admission
wrappers. Endpoints without registration retain their legacy semantics.

QUEUED is not WRITING, LOCAL_WRITE_COMPLETED is not REMOTE_ACKED. Completion waits
in the existing transmit worker, **not** the incoming-ACK event loop. The RTO's
`last` point advances only after local completion of the still-matching pending
block/attempt. Queue + write remains bounded by the existing min(MaxAge,2s) limit,
now measured from submission to the local queue. Protocol RTO, MaxRetries, windows,
credit, pacing and SACKed retention are unchanged.

A received ACK can obsolete an unstarted queued attempt. Once writing has started,
all fragments complete or the bounded session/write deadline fails; an ACK does
not truncate a partial message. Completion objects contain no engine pointer and
cannot alter a new session. An unbound VP8 write does not count as local completion.
No local completion is treated as delivery to the SFU/phone or remote consumption.

## Reproduction and regression

`prepare.py` preserves the sealed current1011 inputs and prior receipts.
`local_test.py baseline <unique-label>` and `local_test.py candidate <unique-label>`
run `queue_retry_test.go` on isolated copies using a real bound Pion VP8 writer.
Local test RTO30ms and340ms writer hold are fixture-only; never production faults.
The strict expectation is nine pending attempts/eight retries/exhaustion before
the first local RTP write on A, one attempt/zero retries/byte-exact delivery on B.

`suite.py` runs affected race suites with pinned offline tools. The accepted seed
source requires `FC_EXPECT_SEED_OBSERVABILITY=1` in tests. Keep failed initial logs;
do not change production classification to satisfy a misconfigured test runner.
Tests include original loss/reorder/slow-consumer/bounds/cancel checks plus queued
ACK cancellation, partial completion, old completion, legacy endpoint and1011.

`build_gateway.py` builds only; it verifies all three bootstrap1011 files unchanged.
`rollout.py` uses a fresh ordinary hash-guarded transition for each variant with
current credentials and exclusive lock/intent receipts. It is **not** a general
replayable deployment tool: read current receipts/runtime before any new use.
A controlled restart interrupts existing sessions. A live binary change needs
the owner's authorization; permission in this task is not perpetual permission.

## Bounded physical measurement and interpretation

`measure.py <unique-label> <loaded-gateway-sha> [1|2]` verifies the owner beta90 APK,
VPN UID route/underlay and actual gateway executable before phone-side curl. Each
round is single2MiB then parallel2×2MiB, HTTP1.1/fresh connections/identity encoding.
The small64KiB exchange must provide actual performance snapshots and gateway TCP
attribution before bulk. A server TLS/publication readback alone does not mean
Android has completed recovery. Retain pre-READY DNS failures, do not erase them.
No payload streams over ADB; observed body hashes are not independent origin hashes.

Collector: one invocation, max600s/64MiB journal bytes, bounded local samples,
compact journal fields; no global journald settings. `journal.py` reassembles
line-max continuations by invocation + stream + PID, with1MiB/16-stream bounds.
The existing correlator validates performance chunk hashes and reports ring gaps.
Raw/errors remain private. Earlier collector syntax/substitution/cap failures
remain evidence, not zero-delay/zero-loss measurements.

`analyze.py` reports goodput, failed bodies, TCP connections, counter deltas,
local queue intervals, overlapping attempts, ACK/release timing and coverage.
CPU ticks require the actual server CLK_TCK to convert. Mux/background traffic
can overlap probes; retained bytes and send depth are not physical bytes in flight.
Never add overlapping waits or subtract phone/server clocks as one-way latency.

See `docs/releases/2026-10-20-mesh-queue-retry.md` for the measured decision. A
successful local reproducer or lower retry counter alone is not speed acceptance.
