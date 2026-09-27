# Experimental 5N-REL-1 ReliableStream

`application → Family TLS 1.3 → ReliableStream → unchanged VP8/RTP → Telemost`.
The plaintext 5N.1/5N.2 path is unchanged. `familysession.Open` now always uses
this adapter; there is no silent unreliable fallback. No DataChannel substitution,
TLS tolerance change, TCP compatibility, congestion controller, FEC or mux.
Both disposable endpoints must use FRS1; old raw-TLS diagnostic peers are not
wire-compatible. The TLS ALPN/identity profile itself is unchanged.

## Framing and session scope

One carrier message contains one frame. All integers are big endian. Header:

| Offset | Bytes | Meaning |
| --- | --- | --- |
| 0 | 4 | `FRS1` protocol/version |
| 4 | 1 | OPEN=1, DATA=2, ACK=3, RESET=4 |
| 5 | 1 | Reserved, must be zero |
| 6 | 2 | Exact payload length |
| 8 | 16 | Source random epoch |
| 24 | 16 | Destination random epoch |
| 40 | 8 | DATA sequence, starting at zero |
| 48 | 8 | ACK cumulative next-to-consume sequence |
| 56 | 4 | ACK selective bitmap, bit0 = cumulative sequence |
| 60 | 2 | OPEN receive window |
| 62 | 2 | OPEN maximum block payload |
| 64 | length | DATA bytes only |

Unused type-specific fields must be zero. Invalid types, lengths, source zero,
oversized frames and impossible ACKs fail closed. No extra checksum: the existing
carrier already has diagnostic CRC32; **only TLS authenticates bytes**.

Each endpoint generates a fresh 128-bit epoch with crypto/rand. Initial OPEN has
zero destination; the peer replies with its epoch and the requester's destination.
Only an OPEN addressed to our freshly generated epoch pins the peer; a peer then
confirms its OPEN. Lost negotiation is retried within MaxAge. Once pinned, the
peer/parameters cannot change. Every DATA/ACK/RESET requires both matching epochs.
Old addressed frames are ignored/count as stale. Old untargeted OPEN can provoke
a bounded challenge, not delivery. Each Family session gets its own adapter,
including the pre-authentication TLS handshake. Reconnect creates new epochs.

Epochs are not authentication or secret capabilities: an active SFU can observe
them, forge ACK/reset/OPEN and cause denial of service. It cannot make forged
application plaintext pass mutual TLS. TLS admission, gateway pin, expiry, CRL,
identity/revision checks and application replay sequencing remain unchanged.
The adapter is not an authorization layer; malicious loss/alteration can still
terminate TLS. The invariant concerns recovery of lossy/reordered carrier data,
not availability against an active Byzantine peer.

## Selective repeat and backpressure

DATA uses independent monotonic sequence spaces in each direction. Receiver
buffers only `[next, next + receiveWindow)`, never delivers across a gap, and
suppresses duplicates. ACK cumulative progress advances **on upper-layer
consumption**, not arrival. Selective bits mark buffered blocks without releasing
their sender-window slots. Therefore a slow TLS reader cannot cause unlimited
receive buffering even if SACKs keep arriving.

The sender permits `next - cumulativeACK < min(sendWindow, peerReceiveWindow)`.
Full window blocks SendContext; there is no internal producer queue. Configurable
defaults: payload16KiB, sender8, receiver16, RTO1s, maximum8 retransmissions/block,
maximum20s from first send. MaxAge also bounds a SACKed but unconsumed block.
Negotiation chooses the smaller maximum payload. Larger TLS writes are split;
only contiguous reassembled bytes reach the TLS bridge. This is not stop-and-wait.

SACK is also gap notification: missing bits below a later received block identify
holes. Only unsatisfied, non-SACKed blocks retry after their own RTO; no go-back-N
or resend-all. ACK loss may necessarily cause harmless duplicate DATA. A current
cumulative/SACK refresh once per RTO repairs lost final ACKs even when all DATA was
SACKed and no additional DATA exists. No PING/PONG or NACK protocol is needed.
The first implementation uses configurable fixed RTO, not a claim of adaptive RTT
estimation. It is independent of the old2s application benchmark RTT.

No catch-up retransmission flood: one retry per outstanding block per RTO, bounded
by the sender window. MaxRetries/MaxAge exhaustion is observable and terminal.
Carrier writes have a2s maximum deadline (or smaller MaxAge); a stalled queue
aborts rather than accumulating unlimited pending calls. WebRTC retains media
congestion control; this adapter adds reliability/flow control only.

## Bounds and shutdown

- Payload hard maximum32KiB, each window1–32, maximum framed size32KiB+64B.
- Default retained DATA bytes ≤(8+16)×16KiB =393,216; hard config bound2MiB.
- At most128 numeric gap/retry events, then an explicit dropped-event counter.
- Header decoding allocates no payload; validation precedes cloning/buffering.
- Huge sequence jumps, receive-window overflow and conflicting buffered duplicates
  reset the session. No sequence wrap or resizing to a peer-provided distance.
- Existing carrier queues remain bounded:256 outgoing fragments and16 messages;
  they are not hidden in ReliableStream's byte accounting. Encoding, the64KiB
  TLS bridge and one delivered block are additional fixed/temporary allocations.
- Two owned goroutines: one state/IO loop, one carrier reader with a1-slot channel.
  All public waiters select cancellation/terminal state. Close joins both workers.
- Context cancellation, carrier/WS/PC termination, TLS termination, local Close,
  remote RESET and retry exhaustion abort the stream and clear retained buffers.
  RESET is best-effort with100ms send budget. It is an abort, not a reliable FIN or
  a graceful drain promise. If RESET is lost, outstanding peer work exhausts or
  its parent context expires. There is no automatic reconnect/replay.

Stats include DATA/ACK/SACK, retransmitted bytes, duplicates/stale frames, gaps,
per-gap detect/recover timing and sequence, queue high-water, retained bytes,
timeouts and fixed terminal categories. `Reordered`/`WithheldBytes` mean arrival
ahead of the delivery frontier (including a slow reader), not proof of wire
reordering. `DeliveredBytes` counts ciphertext handed to the TLS bridge, not
decrypted application goodput. Reset counts include normal final local aborts.

## Validation

`engine_test.go` runs virtual-time loss/reorder/duplicate/delay/ACK-loss/burst cases;
every delivered prefix and final stream must match. `stream_test.go` tests real
adapter cancellation, full-window blocking, stalls, reset/exhaustion and payload
negotiation. `familysession.TestReliableTLSFaultMatrix` exercises207 exact encrypted
echoes (canonical sizes and100×1/16KiB) with bidirectional faults. Raw TLS replay
tests still inject **above** reliability so duplicate suppression cannot mask a
TLS-security regression. Live fault injection exists only in `_test.go`.

Results, failed attempts, physical evidence and limits:
[5N-REL-1 report](../../docs/releases/2026-09-27-webrtc-5n-rel1-reliable-stream.ru.md).
