# Telemost carrier — implementation plan (WEBRTC-EU-1 / 5N.1)

Technical preflight. This document is the implementation contract for the next
task (Astra). It defines the minimal Telemost binary carrier for
`Linux process A ↔ real Telemost ↔ Linux process B`.

Not in this task: runtime carrier code, WEBRTC-EU-2, Android, EU gateway
integration, Family auth/session, TCP destination, DNS, production, version
bumps, dependency manifests. WEBRTC-EU-1 remains **NOT RUN**.

Reference-only (do not copy code here), pinned revisions:

- `kulikov0/whitelist-bypass` `7c19a7ec40900940fe0c43ea1db7768ee632393d`
- `openlibrecommunity/olcrtc` `92b2332769c3dd5000584366201572efc448065f`

## 1. Фактический protocol path

### 1.1 Полная цепочка

```
room URL (join only; creation not exposed)
  → connection metadata (HTTP JSON)
  → signaling (WebSocket JSON)
  → two PeerConnections: subscriber + publisher (ICE/DTLS/SRTP)
  → binary carrier (VP8 video frames, or DataChannel bridged to VP8 by the SFU)
  → binary encode / decode (framing + optional AEAD)
```

### 1.2 Room/session: join only, no creation

Both references agree Telemost does **not** expose room creation. Rooms originate
in the Yandex UI. The headless client performs a guest join from a room URL/hash.

- `GET https://cloud-api.yandex.ru/telemost_front/v2/telemost/conferences/{url.QueryEscape(roomURL)}/connection`
  with query `next_gen_media_platform_allowed=true&display_name=<name>&waiting_room_supported=true`.
- Headers: browser-like `User-Agent`, `Accept`, `Content-Type: application/json`,
  `Client-Instance-Id` (uuid), `X-Telemost-Client-Version`, `Idempotency-Key` (uuid),
  `Origin: https://telemost.yandex.ru`, `Referer: https://telemost.yandex.ru/`.
- Response fields used by the carrier:
  `peer_id`, `room_id`, `credentials`,
  `client_configuration.media_server_url`, `client_configuration.service_name`,
  `client_configuration.ice_servers`, `client_configuration.state_check_interval_seconds`.
- Waiting room: when `connection_type == WAITING_ROOM`, poll
  `GET /conferences/{roomURL}/waiting-rooms/check-access` until `admitted == true`,
  then re-fetch the connection metadata.
- State keepalive: `POST /conferences/{roomURL}/request-states` with `peers`,
  `permissions`, `conference` (version -1).

No anonymous creation / no-login UX is promised. Start with a manually exchanged
disposable room via the session API. Guest join ≠ guest creation.

### 1.3 Signaling (WebSocket, JSON)

Connect WebSocket to `client_configuration.media_server_url` with
`Origin: https://telemost.yandex.ru`.

- Client → server `hello`: `participantMeta`/`participantAttributes` (name,
  role `SPEAKER`, `sendAudio: false`, `sendVideo: true`), `participantId`,
  `roomId`, `serviceName`, `credentials`, `capabilitiesOffer`, `sdkInfo`.
- Server → client `serverHello`: `rtcConfiguration.iceServers`.
- SDP: server `subscriberSdpOffer` → client `subscriberSdpAnswer`;
  client `publisherSdpOffer` → server `publisherSdpAnswer`.
- ICE: `webrtcIceCandidate` trickle in both directions
  (`target` = `SUBSCRIBER` or `PUBLISHER`).
- Housekeeping: `ack`, `ping`/`pong`, `request-states`,
  `updateDescription`/`upsertDescription`/`removeDescription`, `slotsConfig`.

### 1.4 Generic WebRTC

- Two `pion/webrtc` PeerConnections: `subscriber` receives SFU video,
  `publisher` sends local media/data.
- Each PC gets its own API + MediaEngine (VP8 + Opus default codecs) and
  default interceptors.
- ICE servers come from the connection response; bootstrap
  `stun:stun.rtc.yandex.net:3478`; TURN is advertised in `serverHello`.

### 1.5 Binary carrier (two observed variants)

Variant A — VP8 video-frame carrier (whitelist `relay/tunnel/rtc/vp8tunnel.go`):

- Publisher adds `TrackLocalStaticSample(VP8)` (+ Opus audio track); binary
  payload is written as VP8 samples.
- Subscriber reads the remote VP8 track: RTP → VP8 depacketization
  (`S == 1` frame start, `M == 1` frame end) → reassembled frame → decode.

Variant B — DataChannel bridged to VP8 by the SFU
(olcrtc `internal/engine/goolom`):

- Publisher creates `DataChannel("olcrtc")`; capabilities advertise
  `dataChannelSharing: TO_RTP` and `dataChannelVideoCodec: VP8`.
- The SFU bridges DataChannel → VP8 RTP for peers without a native
  DataChannel. Observed data-channel message limit is 12 KiB.

VP8 is a **candidate** carrier, not a proven observed codec of the field call.
Do not hardcode `supports_vp8_carrier` or `supports_datachannel` as proven facts;
probe both at session start. Investigate VP8 first per the 5N decision, keep
DataChannel as a separate mode contract.

### 1.6 Binary encode/decode

- Framing (whitelist tunnel layer): `u32be length | connID u32 | msgType u8 | payload`
  (`WireHeaderLen == 5`).
- Obfuscator (whitelist-specific VPN hardening): ChaCha20-Poly1305 AEAD,
  key = `SHA256(join token)`, random nonce, 4-byte epoch, VP8 keepalive/interframe
  magic headers. Not required for WEBRTC-EU-1 byte-fidelity PASS.

### 1.7 Separation of concerns

- API/signaling — Telemost-specific; small reimplemented adapter.
- Generic WebRTC — library (`pion/webrtc/v4`).
- VP8 binary carrier — concept reuse; small self-written framing + VP8
  sample write/read.
- Project-only VPN — do **not** reuse: SOCKS, tun2socks, full VPN, routing,
  Android, RNS, Family auth, AEAD obfuscator, KCP reliability layer,
  headless-client TLS fingerprinting.

## 2. Минимальный dependency graph

Goal: `Linux process A ↔ real Telemost ↔ Linux process B`, binary payload.

| Module | Candidate version | Why | Direct/transitive | License | Avoidable |
| --- | --- | --- | --- | --- | --- |
| `github.com/pion/webrtc/v4` | v4.2.15 (olcrtc pin; FC pin TBD) | PeerConnection, ICE, DTLS, SRTP, tracks, DataChannel | direct | MIT | no |
| `github.com/gorilla/websocket` | v1.5.x (stable; olcrtc uses pseudo v1.5.4-…) | signaling WS client (stdlib has none) | direct | BSD-3-Clause | no |
| `github.com/google/uuid` | v1.6.0 | instance/message IDs | direct | BSD-3-Clause | yes (crypto/rand) |
| `golang.org/x/crypto` | — | ChaCha20-Poly1305 only if AEAD obfuscation added later | direct (optional) | BSD-3-Clause | yes for 5N.1 |

Pion transitive modules (generic WebRTC, pulled by `webrtc/v4`): `pion/ice/v4`,
`pion/dtls/v3`, `pion/sctp`, `pion/sdp/v3`, `pion/srtp/v3`, `pion/stun/v3`,
`pion/turn/v5`, `pion/mdns/v2`, `pion/interceptor`, `pion/rtp`, `pion/rtcp`,
`pion/datachannel`, `pion/logging`, `pion/randutil`, `pion/transport/v4` —
all MIT, unavoidable transitives. Plus `golang.org/x/net`, `golang.org/x/sys`
(BSD-3-Clause) as unavoidable transitives.

Exact pinned versions must be re-audited in the FC `go.mod`/`go.sum` at
implementation time; the versions above are candidates, not FC pins.

### Explicitly excluded (do not import)

- `github.com/kulikov0/headless-client` v0.1.0 — **BLOCKED** (not audited; own
  license and forks unchecked). It is whitelist's headless browser/fingerprint
  runtime and is not needed: olcrtc proves a plain HTTP/WS client with standard
  headers joins Telemost.
- LiveKit/forked engines (`github.com/owenewans/owenlivekit/v2`, `github.com/livekit/*`)
  — **BLOCKED** for this carrier; olcrtc's Telemost `goolom` engine does not import
  them. Avoid the whole graph.
- whitelist VPN stack: `xjasonlyu/tun2socks/v2`, `xtaci/kcp-go/v5`,
  `gvisor.dev/gvisor`, `golang.zx2c4.com/wireguard`, `wintun`,
  `refraction-networking/utls`, `andybalholm/brotli`, `go-gost/relay`,
  `tjfoc/gmsm` — do not use.

## 3. Лицензии / provenance

- `pion/webrtc/v4` + all transitive Pion modules: **MIT** (upstream standard).
  Root-project license must not be treated as the license of these transitives.
- `gorilla/websocket`: **BSD-3-Clause** (upstream standard).
- `google/uuid`: **BSD-3-Clause**; avoidable.
- `golang.org/x/crypto`, `x/net`, `x/sys`, `x/mobile`: **BSD-3-Clause**.
- `kulikov0/headless-client` v0.1.0: provenance/license **unclear → BLOCKED**;
  stop inclusion until its own license and forks are checked.
- LiveKit/forked RTC engines: provenance/license **unclear → BLOCKED**.
- Reference roots only: whitelist = MIT (`Copyright (c) 2026`, no named holder);
  olcrtc = WTFPL v2 (`Copyright (C) 2026 zarazaex`). Do not label olcrtc MIT or
  attribute all transitive files to a root license.

## 4. Source reuse decision

| Component | Decision |
| --- | --- |
| Telemost auth provider (olcrtc `internal/auth/telemost`) | small source reuse candidate — reimplement own ~80-line adapter from the verified endpoint/params/headers/JSON facts |
| Goolom signaling/session (olcrtc `internal/engine/goolom`) | reuse concept only — reimplement own signaling over pion + gorilla/websocket |
| VP8 tunnel + obfuscator (whitelist `vp8tunnel.go`, `obfuscator.go`) | reuse concept only — do not copy AEAD/epoch/keepalive for 5N.1 |
| DataChannel mode (olcrtc `goolom`) | reuse concept — candidate primary carrier, probe first |
| `kulikov0/headless-client` ChromeWindows/TLS fingerprinting | do not use |
| SOCKS / tun2socks / full VPN / routing / Android / RNS / Family auth | do not use |

## 5. Proposed files/modules

New isolated Go module (no second general transport framework):

```
carrier/
  go.mod                              # module github.com/Joker20380/family_connect/carrier
  telemost/auth.go                    # room URL → connection metadata (peer_id/room_id/credentials/media_server_url/ice_servers)
  telemost/signaling.go               # WS hello/SDP/ICE/ack/ping flow
  telemost/session.go                 # subscriber + publisher PeerConnection lifecycle
  telemost/datachannel.go             # DataChannel carrier (probe first)
  telemost/vp8.go                     # VP8 video-frame carrier (VP8 sample write/read)
  frame/frame.go                      # binary framing + IPC frame codec
  frame/frame_test.go
  telemost/auth_test.go
  telemost/signaling_test.go
  telemost/integration_test.go        # mock/loopback only — NOT a WEBRTC-EU-1 PASS
cmd/
  carrier-smoke/main.go               # Linux A/B PoC harness for the live gate
tests/
  webrtc_eu1_live/                    # live Telemost fixtures/scripts — never run in CI
```

The same `carrier/telemost` package is later reusable by the Android and EU
gateway processes, but only the Linux↔Linux 5N.1 slice is designed now.

## 6. IPC contract (private framed IPC)

Carry forward verbatim from `HOME_GATEWAY_DESIGN.md` (already frozen as v1):

- Isolated `family-webrtc-carrier` process, Go/Pion preferred; parent-owned stdio
  pipes, not a localhost listener. One process owns one carrier session.
- Frame: `u32be body_length | u8 version | u8 opcode | u32be request_id | payload`.
- Body bound 64 KiB; control JSON bound 16 KiB; reject unsupported versions/types,
  truncation, invalid lengths/JSON and unsolicited state transitions before
  allocation.
- Payload opcodes preserve exact bytes including zero bytes.
- Commands: `OPEN, SEND, PING, STATUS, CLOSE`.
- Responses/events: `OPENED, RECV, PONG, STATUS, ERROR, CLOSED`.
- stdout is exclusively framed IPC. Bounded queues, backpressure, serialized
  writes, deadlines, cancellation. EOF tears down the child; bounded grace reaping.
- `OPEN` supplies provider, mode preference, ephemeral session descriptor and
  expiry through the private pipe only; no token/cookie in argv/env/log.
  `STATUS` must not echo the descriptor. `CLOSE` must be idempotent.
- Capabilities: `supports_datachannel`, `supports_vp8_carrier`,
  `supports_tcp_fallback`, `supports_turn`, limits, observed mode; unknown ≠ false.

No Family semantics, no TCP destination, no DNS in this IPC.

## 7. WEBRTC-EU-1 test gate

PASS = A sends deterministic binary payload → real Telemost carrier → B receives
exact bytes; B sends deterministic response → A receives exact bytes.

Payload sizes (deterministic pattern, byte-exact, include zero bytes):
empty (0 B), 1 B, 7 B, 994 B (Telemost DC chunk), 12 KiB, 16 KiB, 60 KiB, 64 KiB.

Layers:

- Unit tests: frame codec round-trip, VP8 sample encode/decode, signaling JSON
  (golden vectors), capabilities parse.
- Integration tests: mock/loopback WebRTC + fake signaling. These are for
  regression only and do **not** count as WEBRTC-EU-1 PASS.
- Live Telemost test (only true PASS): two Linux processes, one real disposable
  Telemost room, real SFU. Must assert exact bytes in both directions for all
  sizes, plus clean `CLOSE`.

Mock/local WebRTC must not be treated as WEBRTC-EU-1 PASS.

## 8. Live credentials/session requirements

Required real inputs (disposable only):

- Telemost room URL/hash (created manually in Yandex UI; creation is not exposed).
- Display name for the guest join.
- No persistent user login; guest join from room URL.
- Runtime inputs (peer_id/room_id/credentials/media_server_url/ice_servers) are
  fetched at join time and passed to the carrier only through the private pipe.

Do not obtain or store real user credentials. Do not log tokens/cookies or echo
the session descriptor in `STATUS`. The PoC uses a disposable session.

## 9. Blockers

- `kulikov0/headless-client` — provenance/license unclear → BLOCKED, exclude.
- LiveKit/forked RTC engines — provenance/license unclear → BLOCKED, exclude.
- Telemost room creation — not available via API; PoC must use a manually
  created disposable room. Guest join ≠ guest creation.
- VP8 carrier — candidate, not proven. If live probing shows VP8 is not a
  viable carrier without a large unaudited tree or proprietary component, the
  fallback is the native DataChannel mode (already implemented by olcrtc
  `goolom`); do not work around a blocker with unaudited code.

## 10. Scope следующего implementation task (Astra)

- WEBRTC-EU-1 / 5N.1 only: two Linux processes exchanging exact binary payloads
  over one real Telemost room.
- Implement the `carrier/` module above: auth adapter, signaling, session,
  DataChannel carrier (probe first), VP8 carrier, frame codec, smoke harness.
- Freeze the IPC frame codec with conformance vectors.
- Run unit + integration tests, then the single live Telemost gate.
- Update only the WebRTC section of `docs/legal/DEPENDENCY_LICENSE_AUDIT.md`
  when new verified facts emerge.
- Do **not** implement WEBRTC-EU-2, Android, EU gateway, Family auth, TCP/DNS,
  or any production/runtime path.
