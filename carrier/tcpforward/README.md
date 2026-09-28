# Single TCP stream, experimental 5N.4

Application TCP → **TCP forwarding → Family TLS 1.3 → ReliableStream → VP8/RTP**
→ Telemost → authenticated Amsterdam gateway → target TCP socket. End-site HTTPS
TLS stays at the application, with normal CA/hostname verification; no gateway MITM.

`OpenTCP(ctx, *familysession.Session, OpenRequest)` returns `Read`, `Write`,
`CloseWrite`, `Close`, `Reset`, `Stats`. `Serve` accepts only the concrete admitted
server Session. A role-checked, one-shot claim prevents second/concurrent streams.
No standalone proxy listener, new authentication, TUN, DNS transport or mux.
Hostname lookup is gateway-local, under the same connect deadline as dialing.

## Wire v1

One Family application message contains one frame: version u8=1, opcode u8,
stream ID u32 big-endian=1, length u32 big-endian, payload. The ID is explicit for
future mux, but only 1 is accepted now. There is no stream reuse in this version.

| Opcode | Meaning |
| --- | --- |
| 1 OPEN | ≤512-byte JSON: host, port, optional timeout_ms |
| 2 OPEN_OK | Empty, only after an actual outbound connect |
| 3 OPEN_ERROR | JSON code: malformed_request, policy_rejected, dns_failure, connection_refused, timeout, unreachable, cancelled, connect_failed |
| 4 DATA | 1–16384 arbitrary bytes; no relationship to application or TCP segmentation |
| 5 FIN | Empty; sender has no more DATA, reverse direction remains open |
| 6 RESET | Empty; abort this stream |
| 7 CLOSE | Empty; client confirms both FINs, gateway acknowledges after closing its socket |

Transport EOF is **not** stream EOF: only FIN produces `io.EOF` in the client.
`CloseWrite` is idempotent; writes after it fail. `Close` before both FINs cancels
the owned Family transport, unblocking active IO. After both FINs, CLOSE/ack is
bounded by 10s. The gateway keeps its Family endpoint alive for up to 10s after
the response to avoid dropping an enqueued reliable response during teardown;
the TCP socket is already closed. No migration after Family session loss.
An immediate target RST closes its socket but retains the Family endpoint for
peer observation (up to10s); otherwise a queued OPEN_OK/RESET could be lost during
carrier teardown. The client cancels its endpoint after observing terminal RESET.
Callers must supply a bounded lifetime context and close the returned stream.

## Policy

Port 1–65535; host 1–253 ASCII bytes; labels 1–63; no URL/userinfo, whitespace,
zone ID or malformed IP syntax. Connect default 10s, maximum requested 30s;
client OPEN exchange capped at 40s. All resolved addresses are checked before any
dial (max32); mixed public/private answers fail closed. Dial uses the checked
literal, not a second hostname lookup. No arbitrary client-chosen resolver.

Only public global-unicast destinations by default: reject loopback, RFC1918,
ULA, link-local, CGNAT, multicast/reserved, documentation/benchmark, IPv6
translation/tunnel/special blocks and well-known metadata addresses. This is a
minimal defense, not a production ACL (public services can still have side effects).
`TestOnlyLoopbackPort` permits **only 127.0.0.1 at exactly one operator-specified
port**, including mapped IPv4; it never enables all private/internal destinations.
Public live HTTPS uses policy defaults, never this override.

## Bounds and lifetime

Two gateway IO directions, no data queues: TCP Read waits on Family Send; Family
Recv waits on completed TCP writes (including partial writes). Existing reliable
window/backpressure remains unchanged. Gateway forwarding DATA storage is bounded
by 49172 bytes: 16KiB socket read buffer + two DATA frames, including headers.
Metrics track this staging separately from TLS/ReliableStream/OS buffers, Go heap,
and caller-owned buffers. Family can allocate a bounded 64KiB application frame
before rejecting oversized TCP frames. There are no unlimited producers or queues.
One outbound socket maximum, lifetime context cancellation closes socket and
Family endpoint, and Serve joins its reverse worker before returning.

Automated tests include real loopback sockets, large arbitrary segmentation,
duplex and half-close, partial/zero writes, policy/DNS pinning, connect failures,
cancellation, bounded send, TLS+ReliableStream loss/duplication with exact bytes,
authentication boundary and rejected second stream. These are not live SFU proof.
