# MESH capacity phases 1–2 — isolated Linux laboratory

This fixture extends the existing `host_compare` CLI capsule, not the product.
`prepare.py` checks every source hash in the previous build manifest and stages
`state-client-build/mesh-capacity-20261020/source`. No checkout/reset to main.
All edits are CLI workload, test code, read-only histograms and a lab-only hard
outgoing-media budget interceptor. No production files or identities are changed.

## Reproduction and boundaries

- `prepare.py`, then `prepare.py --build`: pinned offline Go1.26.1 and dependencies;
  race tests include actual four window pairs, fault simulation, slow consumer,
  cancel/close, real RTP/VP8/reassembly head-loss recovery and capacity overlap.
- `run.py PHASE --mode C|R|T|P ...` executes **one** fresh NL-only media session.
  Run sequentially; never reuse a phase name, room, stale identity or output path.
  The path and namespace intentionally refer to this experiment. A future rerun
  needs a new directory/namespace and its own authorized budget, not deletion here.
- The issuer and room creation are reused verbatim from `host_compare`, including
  the isolated temporary ProductStore/CA and existing NL provider OAuth handling.
  The OAuth token remains on NL. Test identities/room descriptors are private files,
  removed after each phase. No production private key is copied.
- Server stays a separate `nobody` process: CPU50% of one core, MemoryMax220MiB,
  no swap, TasksMax96, Nice10, RuntimeMax510s. Same previous Linux client/network.
  Transfer timeout180s, P requests150s, media/worker lifetimes bounded.
- Source reservations include complete planned messages plus64KiB control allowance,
  even for failures. P reserves the original8585273bytes. Total <=128MiB.
- Every outgoing RTP/RTCP **attempt**, including NACK retransmits, traverses the
  first Pion interceptor. Budget adds actual unencrypted header/payload length +64
  conservative IPv4/UDP/SRTP/SRTCP overhead per packet/compound. Per-endpoint atomic
  reservation rejects writes before its limit; no sender-TX/receiver-RX duplication.
  Sum of previous charges plus both new hard limits must fit256MiB. Failed/unclosed
  endpoints retain their full reservation. Closed endpoints charge final counter
  plus64KiB tail margin. Signaling/admin SSH excluded from the media boundary.

## Workload

C sends independently verified messages directly through unchanged VP8 carrier;
R adds current ReliableStream; T uses `familysession.OpenReliable`; P uses the
existing `Mux64` and original bounded loopback fixture, not a new proxy framework.
TLS verification/ALPN are unchanged. RS configuration is supplied before OPEN on
both ends. No new ALPN, runtime switching protocol, encryption fallback or pacer.

All data is reproducible xorshift synthetic bytes seeded by run ID, with32-byte
magic/kind/run/message-ID/length envelope. Generation copies a precomputed buffer;
verification compares every byte. Unique IDs, missing IDs and duplicates are
separate. Payload template generation precedes the measured interval. No per-block
disk logging, hashing or random generation in the send loop. P retains its existing
precomputed SHA256(counter) fixture and full independent byte/hash checks.

Raw offered rate is carrier-input bytes/sec (including32-byte envelope), using an
absolute monotonic schedule, not production FIXED4M pacing. Raw151×16448 bytes and
R DATA16384+FRS1 header64 do equal carrier work per DATA message:3 fragments /15 RTP
packets at Pion's actual1200-byte MTU, not the2/14 of RAW16384. The older synthetic
framing helper uses1100-byte payloader input and produces17/16 instead; the separate
`packetization_actual_test.go` uses the actual Pion packetizer. Their useful
payloads differ by64 bytes; report actual useful bytes, never count headers as goodput.

Receiver measures elapsed time from its own start request and every unique arrival
monotonically. Raw observation is offered duration +12s drain, unless every known
message has already arrived. Timely raw goodput counts only arrivals within offered
duration; last-arrival and whole observation rates remain separate. R/T require all
known messages and receiver confirmation; failure is not relabeled a partial speed.
Three32-byte round trips precede load; bounded32-byte probes during load measure
the same stack's full round trip, not one-way/network-only delay. Separate sessions,
SFU selection and ordinary system load remain confounders.

Sampled queues/histograms/RS state are in JSONL once per second. Thread scheduler,
per-core/host CPU, cgroup throttling and memory are in an independent owned worker.
Existing RTP/VP8/reassembly telemetry is retained; an unexported discard category
cannot be inferred from absence. Histograms distinguish initial TLS records from
all RS DATA attempts and carrier messages. No per-packet profiler on production.

`summarize.py` calculates offline tables. Preserve failed preparations and sessions.
Do not increase offered rate after persistent overload/loss, growing queues, missing
feedback or wire stop. Do not rerun a severely regressing window merely for symmetry.
Normal context/session close stops both PeerConnections; provider room metadata
deletion is not supported by the existing abstraction and must not be claimed.

Postflight found P816's client ProtocolErrors transition0→1 after echo and before
bulk. All five bodies match, but this is not a clean protocol pass and is excluded
from clean P comparisons. The new operator initially omitted the previous fixture's
stop gate; discovery occurred after later independent sessions, not at that phase.
`operator-used/run.py` preserves the actual original runner. The repaired runner
rejects any nonzero P before/after counter and refuses further runs in this closed
experiment after the postflight warning. P3232/P816b remain the single clean pair.
No transport patch, counter reset or extra media rerun conceals the warning.
