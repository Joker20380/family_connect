# Experimental Family TCP + DNS mux (5N.5)

Opt-in `NewMux(context, admittedFamilySession, server, MuxConfig)` claims the
existing exclusive application owner once. `mux.OpenTCP` provides concurrent
Read/Write/CloseWrite/Close/Reset. `mux.QueryDNS` carries standard DNS wire bytes.
No public constructor accepts an unauthenticated packet endpoint. The internal
packet adapter exists only for deterministic tests. Legacy version-1 single TCP
APIs/tests remain intact; no automatic version downgrade/negotiation exists.

```
N TCP connections + DNS → version-2 mux → one Family TLS 1.3 session
→ one unchanged ReliableStream → one VP8/RTP/Telemost path → Amsterdam
→ independently validated TCP sockets / gateway-configured DNS resolver
```

## Wire and IDs

Same ten-byte big-endian header as single TCP: version byte **2**, type byte,
uint32 stream ID, uint32 exact payload length. OPEN(1), OPEN_OK(2), OPEN_ERROR(3),
DATA(4), FIN(5), RESET(6), CLOSE(7) retain their meanings. WINDOW_UPDATE(8)
contains one uint32 credit increment. OPEN/error strict JSON ≤512B; DATA 1–16384B;
empty lifecycle payloads. Invalid wire length/type/ID fails the session closed.

Client stream IDs are monotonically increasing odd integers 1..2147483647.
Even IDs are reserved (rejected), zero is DNS/control only. OPENs are serialized
in allocation order. IDs never wrap or reuse; exhaustion requires a new session.
The gateway retains only a high-water ID, not an unbounded tombstone map. Stale
or unknown IDs allocate nothing and are counted/ignored. Duplicate active OPEN,
DATA before OPEN_OK/after FIN, duplicate FIN, premature CLOSE and invalid credit
accounting reset only the affected stream. Frames after terminal reset/close do
not resurrect the stream. Default live-stream cap **16**, configurable **1–32**;
gateway worker slots have the same cap and remain held through socket cleanup.
N+1 returns OPEN_ERROR `stream_limit`; local saturation returns ErrStreamLimit.

States: opening → open → local-half-closed/remote-half-closed → both-half-closed
→ closed. Opening failure → failed; RESET/cancellation → reset. Local CloseWrite
is idempotent; duplicate received FIN is a protocol violation. Clean Close waits
up to10s for CLOSE acknowledgement; other Close is abort/reset. Gateway drains
pending data and applies both TCP half-closes before acknowledging clean CLOSE.
One failed stream never closes the Family endpoint. Whole-session failure cancels
all workers, closes sockets, fails DNS callers and releases all retained buffers.

## Flow control and scheduler

Fixed initial credit **65536 bytes per direction per stream**. DATA consumes byte
credit; application Read returns credit, coalesced into WINDOW_UPDATE. A receiver
owns one fixed 64KiB ring. A writer queues at most one 16KiB DATA frame plus FIN;
it cannot allocate based on input byte count. Credit overflow above64KiB resets
the stream. TCP gateway staging is additionally at most two16KiB copy buffers.

One session writer: round-robin ready stream heads, skipping blocked/no-credit
streams. Lifecycle/credit/DNS control has priority, but at most8 consecutive
priority frames precede a ready DATA turn. FIN cannot overtake its stream's DATA.
One in-flight transport send is outside scheduling; it cannot be preempted.
Control FIFO ≤96 frames, stream queues ≤3 frames, DNS outstanding ≤16. Flooding
the control FIFO fails closed rather than allocating unlimited memory. Reader
dispatch never waits for a TCP destination or a stream consumer.

Conservative retained payload bound at hard cap32: stream rings+queued DATA
32×(64+16)KiB; gateway copy buffers32×32KiB; control96×(4096+4)B;
DNS query/response16×2×4096B; session encode/receive scratch≤3×(16384+10)B,
plus small fixed metadata/headers and each DNS worker's bounded message buffers.
`RetainedBytes` measures owned mux rings/queued payloads/DNS callers only, not
socket kernel buffers, goroutine stacks, TLS, ReliableStream or carrier queues.
Those are reported separately. Heap is not synonymous with retained payload.
Default ReliableStream payload retained bound393216B remains unchanged.

**Underlying ordered ReliableStream still creates global transport HOL during
loss recovery.** Scheduler fairness does not remove that and is not a latency SLA.

## DNS

DNS_QUERY(9), DNS_RESPONSE(10), DNS_ERROR(11), DNS_CANCEL(12) use stream0, with a
uint32 Family request ID before DNS bytes. Family IDs are monotonic1..2147483647,
never reused, independent of the 16-bit DNS transaction ID. Duplicate Family
queries are ignored, not assigned to another caller. Responses require matching
Family ID, DNS ID and question. A/AAAA/CNAME/TTL/NXDOMAIN remain wire-format data.
One IN question, standard opcode, ≤128 resource records, 12..4096B per message,
16 outstanding requests/worker slots, timeout5s; malformed queries rejected.

Upstream is **gateway configuration only**: literal IP:53 or first nameserver in
bounded `/etc/resolv.conf`. DNS-over-TCP upstream (two-byte length framing), with
no arbitrary UDP relay and no client-specified resolver address. No retries or
local Android resolver fallback. DNSSEC validation is not added. Cancellation
closes the upstream socket and releases the outstanding slot.

## Security and limits

Family admission/TLS remains the security boundary; Telemost is untrusted.
Existing destination policy/validated literal dialing, connect timeout, host/port
validation and exact-port **test-only** loopback override are reused unchanged.
No TUN/VpnService/UDP/QUIC/Room Broker/reverse streams/seamless migration.
No multi-user capacity or production-readiness claim. Physical gate status belongs
to the dated release report, not this protocol description.
