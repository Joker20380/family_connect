# QUIC over legacy media — isolated architecture comparison

This fixture transforms the sealed `carrier-fec-20261021/source` copy, never the
production carrier module. Parent binary: cdb583b6076016d95d2de0640f13ec25ea5abdf8a35a1c78ebe5a35a43c42cce.
The exact laboratory runtime, manifests, logs and patch are retained under
`state-client-build/quic-carrier-20261021/`. No push is required.

## Layers and pins

- A: original L → RS32/32 → Family TLS → Mux128, packing OFF, Q0.
- QS: L → QUIC → one QUIC stream with bounded length framing → existing Mux128.
- QN: L → QUIC → separate reliable streams of **one** connection, no Mux or RS.
- quic-go v0.54.1, MIT, Go requirement1.23; inherited lab module directive1.24,
  tested with Go1.26.1.
- Exact `module/go.mod` and `module/go.sum` are the isolated module's pins.
  Dormant FEC/packing/Q1/timebase candidates inherited from the parent are not
  enabled. Production go.mod/go.sum are unchanged.
- Default library **Reno** and pacing remain enabled. No library patches,
  artificial UDP offload/ECN, QUIC DATAGRAM extension, direct UDP fallback or
  reliable/ordered adapter below QUIC. Pion's existing WebRTC/NACK remains.

Datagram size is capped at1200B, including Initial/Handshake; path MTU discovery
is disabled on the virtual path. This is not FCF2/1024. One1200B QUIC datagram
becomes one legacy message/part/VP8 frame and **two** RTP packets at MTU1200;
smaller datagrams may need one. The old carrier alone reassembles whole messages.
ReadFrom rejects a short receive buffer instead of returning partial success.

The adapter serializes one write and awaits `localwrite` actual media completion;
it has no retransmission/ordering logic and no additional receive queue. Ownership,
changing deadlines, concurrent close and finite5s writes are tested. The library
has its own8-entry send queue; carrier queues remain finite. Synthetic198.18.0.1/2
addresses are routing labels within a phase, not identity or network destinations.

Fixed stream receive window128KiB, connection512KiB,24 incoming streams, no
unidirectional streams. QN ignores the inherited capacityConfig RS/Mux fields;
its emitted reliability_config is null and no such objects are constructed.

## Cadence, security and completion

Original controls retain2ms/frame without the later byte ceiling. The one common
normalized policy uses1MiB/s conservative media service with at most2ms earned
burst credit and no frame sleep. This avoids a new timer-rounding ceiling on
every tiny RTP packet. RTP33ms nominal progression and keepalive remain unchanged.
Do not enable the earlier FIXED4M controller or compare different cadence policies
as a protocol-only speed gain.

Fresh standard-library Ed25519 CA and one-hour role certificates per phase;
root validation, expected DNS role and lab ALPN, no InsecureSkipVerify/key logging.
Allow0RTT=false, ordinary Dial (not DialEarly), nil client session cache. The first
local test exposed a SessionTicketsDisabled compatibility panic; the logs remain.
Ordinary unused tickets avoid that unsupported setting without enabling resumption.

The existing source/sink verifies complete bodies and SHA256. QN additionally
sends a40B receiver receipt over the request stream; the server checks its size
and digest, and the controller matches both ends before allowing connection close.
QS conserves both-end Mux bytes/closed streams. A retains strict LabDrain: terminal
reset is never success. A clean stop cannot substitute for a receiver receipt.

## Reproduction and safety

Preparation sequence on a new isolated copy: `lab.py`, pinned
`go get github.com/quic-go/quic-go@v0.54.1`, `overlay.py`, `operator_prepare.py`,
`finish_prepare.py`, `go mod tidy`, `go mod verify`, then `build.py`.
The pinned toolchain/cache paths are explicit in `lab.py`. Network dependency
fetches and local QS loopback tests may need executor approval. Local tests are
separate from live traffic accounting. Preserve failed logs; do not call build.py
again against already named admission/build receipts.

`run_series.py original|normalized|product-gated` is a fixed finite plan. It requires
approved external execution, a fresh read-only `production-live-entry.json`, and
the exact build/operator hashes. It creates only disposable lab rooms, processes
and credentials. It refuses a changed production epoch and never restores one.
The initial AO preflight sent0B because the production process/profile changed
before live; that receipt and the subsequent fresh epoch are retained separately.

Two failed main-baseline attempts remain separate from clean comparisons. A1
read an unfinished JSONL line; `records.py` accepts only complete LF-terminated
records and still rejects a malformed complete record. A1R's server exhausted
its20s RS startup while the client was still establishing media (21.153s setup).
`revision.py` preserves the v1 source/binary/manifests and creates v2 with a
common45s maximum both-media-ready gate before protocol startup. It changes no
transport timer or data-path parameter. All four primary phases use this v2;
the failed historical A1/A1R are not substituted for its baseline. Start-gate
wait, media setup and application steady-state time are recorded separately.
QN1 subsequently completed all17 bodies and verified both-end receipts, but the
controller's full14MiB remote log fetch delayed finish beyond QUIC idle/phase
deadlines. This is a retained post-delivery completion error, not a download
failure or clean acceptance. `proof_snapshot.py` now selects only the bounded
complete proof remotely (locally tested against A/QS/QN logs); full evidence is
retrieved after shutdown. It changes neither binary nor transport parameters.
Only the originally remaining QN2/A2 are run after this operator repair.

Main A/QN/QN/A reserves32MiB bulk. Overall live limits64MiB source/128MiB outgoing
media and180s transfer, with stricter inherited request/session/process limits.
Each phase uses one new connection and the same deterministic workload. Short
cadence/QS controls are not substitutes for the full-size primary comparison.
No automatic retries, size/window/controller sweeps or expansion after a failure.

`analyze.py` is an offline extension of existing capacity summaries. Counters have
separate meanings: RS retries, QUIC lost packets/repeated STREAM bytes, RTP repeats
and missing lower carrier parts are not interchangeable packet-loss rates.
Incomplete rings produce unknown gaps, not zero. No inter-host one-way subtraction
or sparse p99. No payload or TLS secrets in QUIC counters.
Adapter WriteNS covers serialized I/O to actual completion after the slot is
acquired, not contention before it or quic-go's earlier eight-entry send queue.
Those bounds are finite but exact pre-send/ACK causal timing is not fully measured.

See the mesh-capacity report and `docs/adr/2026-10-21-quic-media-lab.md` for results,
limitations and the unimplemented Family admission/product compatibility work.
