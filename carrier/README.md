# Telemost binary carrier — experimental 5N.1–5N.5

**5N.5 PASS28.09**, clean tested native/APK `c26c2b7`:
[bounded TCP mux + wire DNS](tcpforward/MUX.md),4 public HTTPS streams and304.138s
mixed physical TCP/DNS with native destination DNS denied. No full-device claim.
CLI `--mux-gateway`/`--mux-config` requires admitted VP8; one existing Family
TLS/reliable session, not one carrier per stream. [Current acceptance report](../docs/releases/2026-09-28-webrtc-eu5-mux-dns.ru.md).
Legacy single-stream mode remains unchanged; no production rollout or TUN.

5N.4 adds [one authenticated TCP stream](tcpforward/README.md) above existing
Family TLS/ReliableStream, without changing the carrier. CLI `--tcp-gateway` and
`--tcp-config` are explicit test-only modes requiring authenticated VP8. Default
echo behavior is unchanged. [Android/operator surface](../clients/android/telemost-runtime/README.md)
and [live evidence/status](../docs/releases/2026-09-28-webrtc-eu4-single-tcp.ru.md).
The legacy single-stream mode has no mux/DNS; neither mode is a production proxy,
TUN implementation or seamless TCP migration.

Recovered from the interrupted DeepSeek worktree, not a second carrier.
`WEBRTC-EU-1 / 5N.1` **PASS on 2026-09-27**: independent developer Linux and
Amsterdam Linux exchanged 291 exact synthetic echoes through **real Telemost VP8**,
including the 30-second and five-minute phases. See the linked result record for
the exact clean revision, artifact hash, low throughput/high RTT and fault checks.
This result is not Android, restricted-mobile or production acceptance. The separate
[5N.2 Android diagnostic APK](../clients/android/telemost-runtime/README.md) now
reuses this exact CLI/core; its physical-device acceptance is recorded separately.
**5N.2 PASS27.09**, clean3f65346: physical Redmi/Android12→Telemost VP8→Amsterdam,
372 exact echoes including30s/5min; see the Android report for lifecycle/performance limits.
Local Pion and DataChannel results alone do not close the gate.
The original plaintext carrier has no VPN/proxy/routing/DNS product integration. The opt-in5N.3
`--family-config` adds an isolated TLS1.3 Family session above the opaque carrier;
the default5N.1/5N.2 mode remains plaintext. Use synthetic random data only:
the SFU is untrusted and DTLS is not Family E2E.

**5N.3 PASS27.09**, runtime5dd8b49: physical Android374 exact echoes/302.001s,
Family admission/replay rejection and lifecycle/recovery. Two early failed runs
remain in evidence; independent SSH observer isolates the accepted test endpoint.
[Result and limits](../docs/releases/2026-09-27-webrtc-eu3-family-session.ru.md).
[Profile/reuse boundary](../docs/testing/webrtc-eu3-session-profile.md) and
[disposable authority/operator runbook](../clients/android/telemost-runtime/README.md).
No crypto/SFU/pacing replacement, automatic reconnect or production credential
issuer is included. 5N-REL-1 now inserts a bounded selective-repeat adapter before
TLS receives bytes: [protocol/bounds/threat boundary](reliablestream/README.md).
`familysession.Open` always uses it; plaintext carrier mode is unchanged.
This is experimental, not a production rollout or TCP/VPN readiness claim.
**5N-REL-1 PASS27.09**: physical300s/4315 exact echoes,1.883505Mbit/s useful RX
at pacing cap2;29 natural block gaps recovered in accepted60s sessions and one
separately injected gap recovered below TLS. Auth/lifecycle/regression/cleanup PASS.
[Exact scope, failed harness attempts and report](../docs/releases/2026-09-27-webrtc-5n-rel1-reliable-stream.ru.md).

`pilot/android-telemost/family_checks.py` runs physical native unit, live WS/PC
closure, old-transcript replay and controlled reliability-gap cases. It takes
`--case unit|ws-close|peer-close|replay|reliable-gap`,
`--adb`, `--binary` (Linux CLI), `--native-test` (Android PIE Go test executable),
`--family-dir` and a new private `--out`. Unit mode uses `familysession`'s test
executable; other modes use `telemost`'s. Build with the same Android toolchain as
the APK, `go test -c -buildmode=pie -ldflags=-checklinkname=0`.
The replay test captures only in memory, proves an initial exact authenticated
echo, closes it, waits for an explicitly restarted B, and sends the old transcript
through a fresh real VP8 carrier. PASS additionally requires B's new
`family_auth accepted=false`, not just the client test exit code.
The replay observer waits up to35s for that refusal before cleanup; stale epochs
are discarded below TLS rather than immediately causing a TLS parse failure.
`reliable-gap` drops one DATA only in the native test binary, after admission,
and checks eight exact encrypted echoes plus matching receiver gap/recovery and
sender retransmission evidence. The CLI/APK cannot enable that injector.

## Build and preliminary checks

From this directory, with Go 1.24+ (validated with Go 1.27.1 on Linux/amd64):

```sh
go mod verify
go test -race -timeout 90s ./...
go vet ./...
go build -trimpath -o /tmp/fc-telemost-binary ./cmd/telemost-binary
```

`TestLocalTwoProcessVP8` spawns two test processes, exchanges SDP only through
parent-owned pipes, then exercises real local Pion VP8 RTP/DTLS. Seven sizes and
100 × 1 KiB + 100 × 16 KiB are byte-compared. It has **no Telemost/SFU** and is
only a regression test. Socket-restricted sandboxes need normal host execution.
The test-only WebSocket fixture binds loopback; the carrier opens no application
listener. Pion uses UDP sockets for ICE/media, not a public proxy.

## Boundary and limits

`telemost.New(ctx, Config)` → `Connect(ctx)` → `SendContext(ctx, bytes)` /
`Recv(ctx)` → `Close()`. A session is single-use, with one publisher and one
subscriber PeerConnection. Connect is bounded (60 s default), HTTP/WS handshake
15 s, WS write 15 s/read 60 s, send 10 s; the harness has an overall deadline.
Cancellation closes sockets and joins owned workers. Failure is terminal, no
automatic retries, replay or reconnect (reconnect count is always zero).

Queue limits: 256 outgoing fragments, 16 incoming messages; overflow on receive
fails closed. Application maximum is **65,536 bytes**, fragment payload 8 KiB.
Wire fragment: six big-endian u32 values: sender ID, message ID, zero-based
sequence, fragment count, total message length, CRC32 of the entire message.
CRC32 detects corruption only; it is not authentication. Max 8 fragments/message,
16 partial messages, 4,096 recent IDs; duplicate fragments reject that message,
completed/expired IDs are rejected within a bounded 10 s retention window.
Partial assemblies expire after 10 s and are pruned even when no data arrives.
No TCP reliability layer; loss can fail a probe, which is reported, not retried.

VP8 interframe prefix + fragment is packetized as VP8/RTP; periodic keyframes
keep the track active. The prefix is not encryption, steganography or a proof of
arbitrary-video decoder conformance. RTP reorder window 256, gap expiry 100 ms
on next arrival; frame assembly is bounded and rejects packet gaps/timestamp
mixing. SFU forwarding passed in the recorded disposable room; this does not
promise arbitrary decoder conformance or compatibility with every future SFU.

`frame/` preserves DeepSeek's private IPC codec. It now permits 64 KiB **payload**
(body maximum 65,542 bytes), rather than incorrectly limiting body to 64 KiB.
The unshipped proposal had no deployed consumers. Control maximum is 16 KiB;
unknown opcodes/versions and short writes fail. There is no general-purpose IPC
command server yet; the current executable is the bounded synthetic harness.

## Real two-endpoint runbook

1. Create a disposable Telemost room manually in the official UI. Do not export
   cookies/tokens. Keep its owner present if admission is required. Exchange its
   URL privately, never in Git, a report or a command transcript.
2. Build from a clean committed checkpoint. Copy the binary **and `licenses/`**
   to a private temporary directory on the authorized EU host
   `186.246.45.246`. Do not install services or change routing/firewall/VPN.
3. On both endpoints, enter the room without putting it in shell history:

```sh
read -r -s FC_TELEMOST_ROOM
export FC_TELEMOST_ROOM
```

4. Start B first. Then run A after B reports `connected`:

```sh
# Linux B — EU endpoint
/tmp/fc-telemost-binary --role echo --mode vp8 --duration 25m > /tmp/fc-eu1-B.jsonl
# Linux A — independent Linux developer machine
/tmp/fc-telemost-binary --role probe --mode vp8 --sustained 30s --extended \
  --duration 25m > /tmp/fc-eu1-A.jsonl
```

The suite checks 1 B, 32 B, 256 B, 1/4/16/64 KiB, then 100 × 1 KiB,
100 × 16 KiB, 30 seconds and (only after success) another 5 minutes.
The explicit 25-minute overall budget accommodates the observed 2–4-second
live RTT; each individual echo still has a 10-second deadline, not a retry.
B checks bounded reassembly and CRC before echo; A byte-compares random payloads.
An idle peer departure may leave the SFU connection alive: A fails at its 10 s
receive deadline, B at its operator-set overall deadline. SIGTERM closes cleanly.
No room-membership event is misrepresented as reliable remote liveness.

For diagnostic comparison only, set `--mode datachannel`; native SFU DC sharing
or TO_RTP mapping is not proven by merely advertising capabilities. A DC success
never substitutes for VP8. The recorded room admitted both guests immediately;
waiting-room polling remains unimplemented and unverified for rooms requiring it.
Errors never print API bodies, credentials or SDP.

JSONL contains build revision/dirty flag, OS/arch, Go/Pion versions, setup time,
per-size/batch RTT mean/max and exact-byte result, aggregate CPU seconds, heap and
peak RSS, disconnect/reconnect counts. Useful throughput counts both payload
directions (`2 × size × count / elapsed`), not RTP/network wire bitrate. Session
TX counts admitted application bytes; RX counts fully reassembled validated
messages, not packet capture. No payloads, hashes, URLs, tokens or ICE credentials
are logged. Write metrics to a local regular file; stdout is not a network service.

Stats also retain at most 128 sanitized signaling/ICE/media events (with an
overflow counter), selected candidate **types** and protocol, connection-state
changes and media counters. No candidate address, SDP or credential is retained.
`VP8_MEDIA_ACTIVE` means a VP8 RTP track arrived, not successful binary decoding;
only exact echo comparisons prove the latter. Selected host/host and
`turn_used=false` describe Pion's pair, not every underlying network hop.
WebSocket failures preserve only the numeric close code, timeout/JSON category,
and fixed reason keywords, never the server's arbitrary close reason.

The signaling heartbeat uses both WebSocket control pings and a bounded-lifetime
5-second application `ping` loop; incoming application `pong` is acknowledged.
Counters distinguish sent application pings, received pongs and generic ACKs.
Do not infer a successful application pong exchange just from an open socket.

With a separate live echo endpoint still running, an explicitly opted-in test
checks an exact 1 KiB VP8 echo, closes **only its own** signaling socket, and
requires terminal receive/send behavior and bounded teardown:

```sh
FC_TEST_LIVE_SIGNALING_CLOSE=1 go test -v -count=1 -timeout 90s \
  -run '^TestLiveSignalingClosure$' ./telemost
```

Normal tests skip this test; the room is read only from `FC_TELEMOST_ROOM`.

Record endpoint distro/kernel separately (`uname -srm`, `/etc/os-release`), room
creation method (not URL), placement, UTC window and matching source revision.
Before claiming PASS also exercise remote exit, signaling closure and SIGTERM
during live traffic. Local malformed/oversized/closure tests are not live proof.
Do not start Android automatically.

Rollback: stop the temporary process, unset `FC_TELEMOST_ROOM`, close the
disposable room, remove only the operator-created temporary deployment if desired.
No production defaults, released artifacts or catalog versions change.

See [result/recovery record](../docs/releases/2026-09-27-webrtc-eu1-telemost-binary.ru.md)
and [dependency audit](../docs/legal/DEPENDENCY_LICENSE_AUDIT.md).
