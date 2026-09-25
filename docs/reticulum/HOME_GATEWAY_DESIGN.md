# Personal/Home Gateway — Reticulum control, selectable data transport

Engineering decision and implementation requirements, 2026-09-25.
**Stage 5 / Reticulum — active development; design recorded, RNS-1–RNS-5 open.**
This document specifies work to implement; it is not evidence of a working tunnel.
Current execution order lives in [PLAN](../PLAN.md), measured results in
[STATUS](../STATUS.md). The project has working pilot clients and VPN transports;
it is no longer only an isolated research laboratory, nor production-ready.

## Whitelisted WebRTC Carrier — extension, 2026-09-25

**Current scope: documentation and implementation preparation only**, as clarified
by the owner after requesting the carrier extension. No carrier implementation,
platform build or live-provider acceptance is claimed by this checkpoint.

Delta: previous Home Gateway with Reticulum control and selectable data transport
**+** interchangeable WebRTC underlays **=** Reticulum overlay over a separately
managed network path. Reticulum remains independent of provider/IP transport.
The earlier freedom to use another IP data transport remains; the new WebRTC
workstream specifically proves RNS frames, announces and Links over the carrier,
with IP-over-RNS-over-WebRTC as a later explicit test branch. The historical
strategy below is retained, not a second competing architecture.

```text
Android / Family Device Identity
                 │
        Reticulum Overlay
                 │
        UnderlayPathManager
                 │
     ┌───────────┼───────────────┐
 DirectIPv6  DirectIPv4     WebRTC Carrier
             /future NAT        │
                         ┌──────┼──────┐
                      Telemost  VK     WB
                         └──── SFU/RTC ┘
                                │
                       Windows Reticulum Overlay
                                │
                       Windows Home Gateway
                                │
                     existing Family Connect VPN
                                │
                             Internet
```

**Reticulum = overlay / identity / encryption / routing. WebRTC = carrier /
underlay.** Family entitlement remains authoritative for admission. Provider
accounts, room membership and ICE/DTLS success do not authenticate Family devices.
RNS Link payloads remain end-to-end encrypted across untrusted SFUs. RNS announces
and some routing metadata are public/signed, not secret: do not claim every byte
of RNS signaling is encrypted or place credentials in announce application data.

### Existing code and intended integration

Inspected checkpoint `3bddff0` and existing dirty working tree. Home Gateway work
to date consists of design/legal documents; no `UnderlayPathManager` or WebRTC
provider implementation was found. `provisioning/reticulum.py` already contains
`ReticulumAdapter` / `ReticulumControlProvider` for finite control exchanges;
Android `fc_rns_transport.py` owns an RNS runtime and TCP interface. Preserve these
callers and their verification/lifecycle behavior. Attach a packet-oriented custom
RNS Interface below the existing runtime; do not reproduce destination, announce,
Link, encryption or packet parsing in a provider. Validate the Interface hooks
against pinned `rns==1.5.1` when implementing.

Proposed `UnderlayPathManager` owns enabled path factories, cancellation, generation
tokens, bounded setup deadlines, health and reconnect. Initial preference: direct
IPv6/IPv4 → existing cheap reachable path → WebRTC. Use bounded sequential attempts
first; future racing must cancel losing paths. `NatTraversalPath`, `OwnRelayPath`
and `MeshtasticBootstrap` are future extension points, not implemented paths.
Meshtastic is a possible bootstrap/control channel, not an assumed broadband path.
Replacing an interface must not replace Device Identity. Seamless live migration
is out of scope; reconnect/reauthentication may be needed when the path changes.

`WhitelistedWebRtcPathProvider` exposes connect/disconnect/send/receive/health/
reconnect/capabilities. Opaque binary frames are the only payload contract. It
contains no TUN, SOCKS, HTTP proxy, VPN routes, Family accounts or Internet
forwarding. Provider adapters encapsulate create_session/join_session, signaling,
credentials, SFU negotiation, ICE and cleanup. Reticulum code must not branch on
Telemost/VK/WB. Avoid importing either reference project's complete VPN stack.

### Reference inspection and first provider decision

Sources inspected as code (not a live-service test):

- `kulikov0/whitelist-bypass` at `7c19a7ec40900940fe0c43ea1db7768ee632393d`:
  MIT; `relay/wbstream/{api,session}.go`, `relay/livekit/*.go`,
  `relay/telemost/api.go`, headless creator entrypoints, Android headless joiners
  and `relay/tunnel/rtc/vp8tunnel.go`. It uses a Pion-derived headless-client
  dependency, publisher/subscriber peer connections, signaling, server-provided
  ICE parameters, DC and paced VP8 media paths. Reconnect/session loops need
  adaptation to our bounded lifecycle, not copying wholesale.
- `openlibrecommunity/olcrtc` at `92b2332769c3dd5000584366201572efc448065f`:
  WTFPL v2, Copyright (C) 2026 zarazaex; `internal/auth/{wbstream,telemost}`,
  engine/transport separation, reconnect contracts and provider example configs.
  Its module graph includes forked RTC engines and other dependencies whose
  licenses must be checked individually before use. Root license is not a
  license for every transitive component.

**First provider selected for implementation preparation: WB Stream, VP8 mode.**
Its guest-register → join existing room → room-token/server-URL flow is visible
in both references, and the LiveKit-style signaling boundary is separable from
the VPN bridge. This is lower integration risk than copying Telemost's custom
signaling/slot management for this first PoC; it is not a claim that WB is reachable
or stable on the target SIM. Telemost remains the next candidate; VK comes later.

Guest joining is not guest room creation. The inspected whitelist WB creator
requires a bearer from cookies; its API helper also has a guest/create code path,
whose current service acceptance has not been tested. olcrtc WB auth joins an
existing room. The inspected Telemost creator requires Yandex `Session_id`, and
olcrtc Telemost auth does not implement room creation. Start with an explicitly
provided disposable room through the session API; manual exchange is permitted
only in this PoC. Do not promise fully anonymous creation/no-login final UX until
tested. No credentials have been requested, exported or committed.

### Carrier process and protocol proposal

Use an isolated `family-webrtc-carrier` process, with Go/Pion as the preferred
implementation candidate pending version/license review. Parent-owned stdio pipes
are preferred over localhost listeners. One process owns one carrier session;
only inherited handles connect it to its parent. No unauthenticated TCP listener.
Windows broker controls executable verification/process lifetime; Android requires
an ABI-matched packaged executable and lifecycle tests. Do not assume gomobile
reference builds prove our separate-process packaging works on Android.

Proposed IPC v1, to freeze with conformance vectors before coding:
`u32be body_length | u8 version | u8 opcode | u32be request_id | payload`.
Body bound 64 KiB, control JSON bound 16 KiB; reject unsupported versions/types,
truncation, invalid lengths/JSON and unsolicited state transitions before allocation.
Payload opcodes preserve exact bytes, including zero bytes; max RNS frame size is
negotiated with the pinned adapter, not inferred from this IPC envelope bound.
Commands: OPEN, SEND, PING, STATUS, CLOSE. Responses/events: OPENED, RECV, PONG,
STATUS, ERROR, CLOSED. Frame counters and sanitized errors only in diagnostics;
stdout is exclusively framed IPC. Bounded queues, backpressure, serialization of
writes, deadlines and cancellation are required. EOF tears down the child; parent
terminates/reaps a stuck process after a bounded grace interval.

OPEN supplies provider, mode preference, ephemeral session descriptor and expiry
through the private pipe; no token/cookie in argv, environment or log. STATUS
must not echo the descriptor. Host owns secure storage, policy and provider-enable
config. Provider/API exceptions become sanitized unavailable states. CLOSE must
be idempotent and clean up room participation, sockets and timers where supported.

Capabilities explicitly name `supports_datachannel`, `supports_vp8_carrier`,
`supports_tcp_fallback`, `supports_turn`, limits and observed mode. Model unknown
separately from false. References show DC and VP8 paths, but actual provider/session
support must be probed: do not hardcode Telemost DC=false or WB DC=true as proven
facts. Start WB in VP8, retain DataChannel as a separate mode contract. TCP signaling
does not prove TCP media fallback; TURN availability/credentials are session-specific.
Never disable TLS/certificate checks. Bound and validate signaling responses and
server URLs; prevent unsafe schemes, credential forwarding and arbitrary local
network access from untrusted signaling. Media loss/fragmentation/reordering and
queue saturation need explicit tests before trusting binary integrity.

### Rendezvous, security, enable flags and recovery

Session descriptor is short-lived provider room/role/join material, never device
identity. The host binds it to existing Family identities/authorization. Rendezvous
eventually uses existing provisioning or another reachable control path; avoid the
circular assumption that RNS-over-this-carrier can bootstrap itself before both
ends have its session descriptor. PoC manual exchange stays behind session API;
cached expiring provisioning, another RNS path or Meshtastic remain future options.

Provider and overlay connection states stay separate. A provider may be connected
while RNS peer authentication fails: no gateway admission in that case. Provider
failure cannot disable other transports or silently downgrade authentication.
Use exponential backoff/jitter, finite attempts/deadlines and explicit retry state;
replace expired session material, reject stale callbacks, release failed sessions.

Proposed signed provisioned config: `webRtcProviders.wb.enabled=false`, with
independent Telemost/VK flags also false by default; experimental opt-in required.
A supported provider can be disabled by verified configuration without a new build.
Config expiry must be defined: an offline client cannot receive an immediate kill
switch; cached authorization must not remain valid forever. No arbitrary executable
or code download through these flags. Future API breakage may still need a build.

Android must protect/bind **all** carrier network sockets, including HTTP signaling,
DNS, ICE/STUN/TURN, RTP/DTLS, DataChannel and reconnect sockets. Parent-side protection
needs an explicit cross-process FD mechanism or equivalent platform-approved
binding; stdio alone does not solve it. Prove the socket factory before full VPN
integration. Pure binary WEBRTC-2 may run without VpnService first, but cannot
therefore claim tunnel-loop/leak protection. Existing secret storage and firewall
constraints remain; no cookies/tokens, RNS/user payloads or production DNS queries
in logs. An SFU can observe timing/size/public announce metadata or drop/replay
frames; RNS and Family authorization remain the security boundary.

### Added stages and acceptance (existing 5A–5G preserved)

| Stage | Work / gate | Current status |
| --- | --- | --- |
| 5H | UnderlayPathManager and RNS Interface / private IPC contracts | Designed, not implemented |
| 5I | Single-provider isolated carrier: WEBRTC-1, then WEBRTC-2 | WB/VP8 selected for first investigation; not run |
| 5J | Reticulum-over-WebRTC: WEBRTC-3 | Not run |
| 5K | Home Gateway over WebRTC: WEBRTC-4/5, linked to existing5C–5E | Later; not run |
| 5L | Multi-provider WebRTC; independent flags and recovery | Later; not implemented |
| 5M | Restricted-mobile acceptance, extension of existing5F | Краснодар; not run |

Execution priority is 5A reachability →5H→5I→5J; adding later letters does not mean
existing5B–5G are complete. Continue into5K only after reviewing these gate results.

WEBRTC-1: two desktop processes through real WB infrastructure, random binary
round trips with exact equality at 1, 64, 512, 1500, 4096 bytes and negotiated
maximum; reject maximum+1. Exercise partial IPC reads, concurrent send/receive,
duplicates, disconnect/rejoin, token expiry, provider unavailable and clean shutdown.
WEBRTC-2: Android↔Windows repeats those tests over the provider, recording exact
OS/ABI/builds. Desktop loopback/cross-compilation does not satisfy this gate.
WEBRTC-3: actual reference RNS interfaces carry announces both directions and
establish an authenticated RNS Link without manual packet reconstruction; demonstrate
identity/signature rejection and no provider logic in the Reticulum layer.
WEBRTC-4: Android TUN→RNS→WebRTC→Windows deterministic IP/reply, ping-equivalent,
TCP and UDP. WEBRTC-5: browser/DNS, FC exit public IP, no mobile/DNS/IPv6 leak,
upstream failure and reconnect on the restricted mobile network.

Measure DataChannel and VP8 separately: setup/reconnect time, RTT, throughput,
CPU/memory, loss and 30–60 minute stability. >5 Mbit/s stable is a useful PoC
target, 20+ Mbit/s a strong result, neither a current measurement nor guaranteed.
Slower first results prompt analysis, not automatic rejection of the architecture.
Path telemetry: provider, carrier_mode, RTT or unavailable, connected_since,
rx_bytes/tx_bytes, reconnects, sanitized failure_reason and path generation.

Краснодар matrix: ordinary FC transport = user-reported cellular failure (reproduce
and record timestamp/active restrictions); direct Home Gateway = unknown; WB =
unknown; Telemost = unknown; RNS-over-WebRTC = unknown; full Home Gateway = unknown.
Success requires ordinary direct VPN failing while the complete new path works
in the same restricted-network conditions. No whitelist reachability is inferred
from a service name, reference README, office Internet or loopback result.

### Implementation preparation and open blockers

Next authorized implementation step, when resumed: license-pin the minimal Go/Pion
graph, specify executable packaging/protected sockets, implement and test bounded
IPC plus path manager, then WB session/media adapter and opt-in live WEBRTC-1.
Reuse only justified small modules; preserve notices and exact provenance before
copying. No SOCKS/tun2socks/mux or full VPN import. Check dependencies of forks
individually; no unreviewed GPL/AGPL inclusion.

Open: live guest/create/media capabilities, reachable carrier on the target SIM,
provider/API stability, final Go/Pion or fork versions/licenses, Android process
packaging/socket protection, actual Windows+Android test endpoints. No Go/adb/dotnet
commands were found in the current shell PATH during inspection; toolchain setup
is deferred with implementation. Source clones stay outside the repository in /tmp;
no implementation, dependency pins, app release or provider session was created.
The user has deferred device testing and requested preparation only at this time.

## Previous strategy revision — owner decision, 2026-09-25

The primary objective is establishing a secure phone↔home-PC connection while
mobile allowlist restrictions are active. Reticulum is the control/discovery,
authentication and negotiation/recovery channel; carrying all IP traffic over RNS
is no longer required. This supersedes the original mandatory IP-over-Reticulum
strategy. Milestone names RNS-1–RNS-5 are retained for continuity, with updated
acceptance below. No milestone has passed. Current position: global stage5,
start of5A (design and reachability validation); no Home Gateway runtime yet.

First validate reachable authorized infrastructure on the target mobile network:
control/bootstrap AND data ingress. A successful RNS exchange is not evidence of
a reachable data endpoint; a known destination is not a firewall bypass. If the
RNS carrier is blocked, it also needs a reachable bootstrap/carrier. Shared
operator infrastructure is allowed; per-user home DDNS/static IP is not required.

Relay-first PoC: both endpoints establish outbound connections to a reachable
relay; user traffic remains encrypted end-to-end to the home PC. The relay is not
an Internet exit. Direct IPv6/IPv4 and NAT traversal come later as optimisation.
AWG/WG with reachable UDP and existing TCP/XHTTP/TLS are candidates, not validated
solutions for this mobile network. Existing runtimes do not automatically provide
a reverse/relay tunnel. Choose the data adapter after measurement and license audit;
no new implementation or dependency is selected by this strategy change.

## Goal and scope

Android on a mobile network establishes an authenticated connection to its owner's
Windows Home PC using Reticulum control and a selected encrypted data channel.
Windows provides diagnostic direct Internet (A) or existing Family Connect VPN / EU
exit (B). No per-user static IPv4, domain/DDNS, manually entered home endpoint,
key transfer or reconfiguration after home-IP changes. Device Identity → RNS
Destination → signed negotiation → currently reachable data path. IP addresses
belong to the mutable underlay, never permanent identity.

```text
Family Control / Device Identity / FAMILY authorization
                         │
        Reticulum: discovery + signed negotiation
                         │
           Android Phone ↔ Windows Home PC
                         │
Data: Android TUN ══ encrypted selected transport ══ Windows Gateway
                        direct OR relay                    │
                                               diagnostic Internet
                                                OR existing FC VPN
                                                           │
                                                        Internet
```

Direct Internet is an explicit diagnostic mode, never a fallback from mode B.
Home Gateway serves only explicitly authorized devices of the same FAMILY.
This is a personal gateway, not a public relay or arbitrary public proxy.

## Inspection and minimal integration points

| Existing component | Integration decision |
| --- | --- |
| `device_identity/device.py`, Android `ControlIdentity.java`, Windows `Core/ControlIdentity.cs` | Existing Device Identity already has RNS-compatible X25519/Ed25519 keys and stable public reference; reuse secure storage and enrollment, no second identity/account system. Messenger identity is not device authorization. |
| `control/product/store.py` | Existing `devices`, `device_entitlements`, `entitlements.family_id`, expiry/revision/revoke are authoritative. Issue Home Gateway authorization from this store, not from peer self-assertion. Friends integration remains an explicit mapping task, not a second membership database. |
| `provisioning/models.py`, `envelope.py`, `cache.py` | `NetworkProvisioningState` currently accepts only WG gateway candidates. Add a separately versioned, capability-gated Home Gateway grant using existing signing/verification/revision rules; do not silently broaden old schema-1 acceptance. |
| `provisioning/configuration.py`, Android `ControlSelection.java`, `ConnectionService.java`, Windows `Core/TransportSequence.cs` | Add explicit experimental selection after platform integration. Preserve existing default WG/AWG/TCP selection and reconnect; no automatic Home Gateway promotion. |
| Android `TcpVpnService.java`, `ControlRnsAndroid.java`, `fc_rns_transport.py` | Reuse VpnService ownership, existing Python runtime and underlay binding pattern. Current RNS carrier is bounded control exchange, not an IP tunnel; add a separate adapter/lifecycle without changing its protocol. |
| Windows `Broker.cs`, `BrokerIdentity.cs`, `TcpEngine.cs`, `TcpNetwork.cs`, `TcpSession.cs`, `TcpHealth.cs` | Broker owns privileges, identity and route lifecycle. Reuse existing networking facilities; current outbound VPN engine does not yet implement LAN/tunnel forwarding or NAT. Add gateway adapter explicitly. |
| Android `VpnHealth.java` / service generation tokens; Windows health/session; control journals | Extend bounded health/reconnect and cancellation contracts. Retain stale-callback protection and transaction recovery; keep payloads out of telemetry. |

No broad refactor, replacement of WG/AWG/TCP/WebRTC, or automatic resumption of
unrelated migration/test debt. Changes must preserve existing security tests.

## Implementation choice and boundary

Use the **official Python reference implementation, `rns==1.5.1`**, already pinned
in Device Identity and bundled by Android's Chaquopy configuration. Android can
reuse the existing embedded runtime. Windows initially needs an isolated broker-owned
worker with bounded private IPC and runtime packaging; that worker is not yet present.
No public localhost SOCKS/HTTP interface, command-line secrets, or extra VPN stack.
The IPC must authenticate its owner and reject unrelated local processes; named-pipe
ACLs/parent-owned handles, bounded messages and child cleanup are acceptance gates.

`HomeGatewaySession` is the proposed orchestration boundary: existing identity/FAMILY
policy, a `ReticulumControlAdapter`, replaceable `DataTransportAdapter`, Android TUN
and Windows gateway adapters, health/reconnect and diagnostics. These are design
names, not implemented classes. The former `ReticulumHomeGatewayTransport` name
must not require RNS packet carriage. Control handles destination/discovery and
signed negotiation; data handles peer handshake, bounded packet I/O and close.
Business logic depends on these contracts, not RNS objects. Both peers use the
reference RNS stack for control; IP-over-RNS remains an optional future data adapter.

[rns-vpn-rs](https://github.com/BeechatNetworkSystemsLtd/rns-vpn-rs) is a reference
for TUN packets over links, destination-based peer lookup and nonce/signature peer
authentication. Its source uses a TUN interface, MTU 1500, announce-driven links,
and peer authorization before forwarding. Its Rust dependency is Reticulum-rs;
these choices do not establish Android/Windows support or reference wire compatibility.
No code is copied, bundled or added as a dependency in this documentation change.
Do not adopt its permissive `allow_all` option. An alternative implementation must
pass bidirectional interoperability tests against the pinned Python reference before
adoption; do not implement the Reticulum protocol from scratch.

The reference implementation's Reticulum License differs from MIT and from the
authors' public-domain protocol statement. See [dependency audit](../legal/DEPENDENCY_LICENSE_AUDIT.md).

## Identity, signed binding and threat model

Reuse the device's existing RNS-compatible identity; derive a distinct application
destination using a versioned Home Gateway aspect, separate from control and chat.
Do not generate or manually copy another permanent credential. Where a worker
requires access to private material, use existing native vault ownership and a
private process boundary; never persist it in a public config or log it.

Specify a canonical, domain-separated device-signed binding of device reference,
RNS public identity, derived destination, protocol version and role. Verify the
reference from the public key, signature and destination derivation. Even when
the keys coincide, include these fields in the signed authorization transcript to
prevent cross-protocol or role confusion. Control countersigns a bounded grant
binding both device identities, FAMILY/entitlement and revision, roles, virtual
addresses, allowed mode, gateway consent, issue/expiry and audience. Signed negotiation
also binds data transport keys, both identities, roles, selected protocol/version,
path parameters, session nonce and expiry. The data handshake must independently
prove possession of the bound keys; reject relay substitution, replay and downgrade. A device
signature proves possession, **not entitlement**. Both peers validate the existing
Control trust anchor and revision floor; no TOFU and no shared family password.

Use RNS's destination proof and client identification plus fresh challenge/response
bound to the link/session, both peers, roles, grant digest and protocol domain.
No IP frame is admitted before mutual authentication and authorization. Retire
old-session replay state on reconnect; reject late callbacks and duplicate frames.
Re-check expiry/revocation while connected; authority unavailability must not renew
an expired grant. Pin the chosen gateway identity, not merely a matching family name.
Final wire format, maximum grant TTL and revocation convergence bound require tests
and review before RNS-1; they are not existing provisioning guarantees.

Threats: hostile bootstrap/transport node, Internet scanner, wrong-family member,
revoked device, replayed grant/frame, local unprivileged process, spoofed virtual IP,
resource exhaustion, network change and compromised authorized endpoint. Encrypt
end-to-end, authenticate and bound allocations/queues, enforce assigned source IPs,
expire stale sessions and deny arbitrary routing. A transport node can still observe
timing/volume and disrupt service; compromised endpoints can see their own traffic.
Reticulum alone does not guarantee reachability through CGNAT or allowlist filtering.

## Data plane and routing safety

Android: applications → VpnService → TUN → selected encrypted data transport → Windows.
Start with IPv4; preserve future IPv6 support. Reuse existing packet/framing/MTU
handling when suitable, with strict bounds, source validation and backpressure.
Specify extra framing only where the selected adapter requires it. Do not build
RNS IP fragmentation as a prerequisite; if that optional adapter is later selected,
validate its packet limits and bounded fragment reassembly separately.

Before any underlay connect or reconnect, Android must `VpnService.protect(fd)`
and bind the socket to a validated non-VPN `Network` as needed. Fail closed if
protection/binding fails. Bootstrap DNS must use that explicit network or pinned
numeric bootstrap addresses; application DNS stays in the tunnel. Library-created
reconnect sockets must use the same factory/guard, never bypass it. Guard against
selecting the VPN network itself and test Wi-Fi/LTE replacement.

Full-traffic Home Gateway captures `0.0.0.0/0`; route IPv6 into a blocked/captured
path until supported, so IPv6 cannot escape. DNS points to a resolver reachable
through the gateway. Keep the TUN and capture routes alive during tunnel loss;
drop/limit queued traffic and reconnect without silent direct fallback. Android
always-on/lockdown is required for protection across service death/reboot; ordinary
VpnService alone cannot guarantee OS-wide blocking after its process disappears.
Document that distinction and test both cases before advertising fail-closed.

Windows: broker-owned private gateway adapter injects/receives packets with source
validation, bounded forwarding and return-path state. Mode A explicitly selects
normal Windows egress. Mode B pins the existing Family Connect VPN interface and
blocks forwarding if upstream VPN fails. No second VPN stack or mandatory manual
Internet Connection Sharing. Select and validate application-managed forwarding/NAT
and narrow firewall rules before RNS-3; do not claim existing Wintun alone supplies NAT.
Use idempotent route/rule ownership and crash journal; remove only application-owned
state. Prevent routing control or data underlay recursively through this tunnel. No automatic
WAN port exposure, global firewall disable, or public SOCKS/HTTP listeners.

## Discovery and lifecycle

First PoC may use an explicit shared bootstrap RNS node for control and a
reachable data relay (possibly colocated, but separate roles). Both devices
make outbound connections; home address changes never edit device identity or user
configuration. Announce/path rediscovery follows underlay reconnection. Adapter
configuration supports a list of bootstrap paths and future direct IPv6, direct IPv4,
NAT traversal and RNS transport nodes; full NAT traversal is out of initial scope.

```text
DISABLED → DISCOVERING → CONNECTING → AUTHENTICATING → CONNECTED
                             ↑                          ↓
                             └── RECONNECTING ← DEGRADED
```

Use bounded connection/auth deadlines, health probes and exponential backoff with
jitter and a maximum delay; reset retries only after stable success. No busy loops.
Track control and data health separately. Loss of control need not interrupt a
healthy data session while its bounded authorization remains valid. Reconnect uses
reachable control or preauthorized unexpired paths; grant expiry fails closed.
On Android/Windows network change close stale sockets, cancel old generation work,
rediscover and reauthenticate; preserve capture policy. Persist only approved
configuration/identity, not ephemeral endpoints as identity. PC restart restores
explicit opt-in from protected state, obtains a valid grant and re-announces.
Mobile reconnect and home DHCP/router/ISP-prefix changes follow the same flow.
Shutdown cancels timers, closes links/IPC/TUN in policy order, joins workers and
removes owned routes; deliberate user disable must be distinguishable from failure.

## Feature gate and diagnostics

Proposed configuration: `home_gateway.enabled=false`, `experimental=true`, label
**Home Gateway Experimental**, explicit `direct_diagnostic` or `family_connect`
egress. One config switch disables the feature. These are planned names, not
currently accepted client options. Existing transport defaults stay unchanged until
real-world acceptance. Avoid UI polish until the data path is proven.

Record `mode=home_gateway`, `control_transport=reticulum`, actual `data_transport`,
`path_kind=direct|relay`, separate control/data states and ingress reachability, local Device Identity,
`gateway_device_id`, `rns_destination`, `path_state`, `connection_state`,
`session_age`, `rx_bytes`, `tx_bytes`, `rx_packets`, `tx_packets`,
`reconnect_count`, sanitized `last_error`, RTT/loss only when actually measured
(otherwise unavailable). Never log private keys, complete authentication tokens,
user packets or production DNS queries. Diagnostic exports need the same filtering.

## Milestones, test gates and delivery

| Gate | Required evidence | Current status |
| --- | --- | --- |
| RNS-1 / 5A–5B | Reachable control and data ingress under active target mobile restrictions; RNS negotiation and authenticated selected data session Android ↔ Windows; both identities; reconnect | Not run |
| RNS-2 / 5C | Real IP packets from Android TUN over the selected encrypted transport to Windows; virtual-IP ping or deterministic packet test, with return path | Not run; minimum implementation success gate |
| RNS-3 / 5D | Explicit direct-Internet gateway: HTTP/HTTPS, DNS, UDP and TCP | Not run |
| RNS-4 / 5E | Existing Windows VPN upstream; phone public IP equals VPN exit, not home ISP/mobile carrier | Not run |
| RNS-5 / 5F | Краснодар with active allowlist restrictions: mobile→home Windows→Family Connect; measurements below | Not run |
| 5G | Direct paths/NAT traversal and zero-config optimisation, informed by measurements | Planned |

Required unit/integration coverage: control reachable/data blocked and control blocked;
relay end-to-end identity/key binding, negotiation replay/downgrade; framing and malformed/oversized packets;
authentication/wrong-family/revoked/expired-grant rejection; replay/duplicates;
state-machine backoff and cancellation; route install/remove/rollback; tunnel/DNS
leaks including unsupported IPv6; loop prevention and unprotected reconnect sockets;
shutdown, gateway disappearance, endpoint change and upstream failure in mode B.
Existing tests must continue passing without weakening security assertions.
Mock tests, Linux loopback and cross-compilation are not Android/Windows acceptance.

Start reachability measurements at5A; repeat full acceptance at RNS-5. Record
evidence that allowlist restrictions are active, and test control and data separately.
For RNS-5 record device/OS/build/commit, operator and network type (no subscriber
number), bootstrap path, connection establishment time, throughput, latency, packet
loss, 30–60 minute stability, mobile-data off/on, Wi-Fi↔LTE and home-IP change where
practically possible. Explicitly mark untested scenarios. Optimise after measurements.

Implementation delivery must include changed-file list, design and library/license
decision, exact third-party portions if any, Windows gateway and Android PoC launch
instructions, automated tests with exact local commands/results, device evidence,
limitations, next steps and commit hashes. Launch commands do not yet exist; do
not invent runnable configuration for an unimplemented gateway. Real-device access
is a prerequisite for acceptance, not for writing implementation/tests.

Keep reviewable commits: (1) docs/legal licensing, (2) docs/rns design,
(3) core/rns abstraction, (4) windows/rns endpoint, (5) android/rns TUN,
(6) core/rns IP routing, (7) tests/rns security/reconnect, (8) docs/rns validation.
RNS-3 and RNS-4 should remain independently bisectable/revertible. Do not declare
the implementation task complete before at least RNS-2 passes on real devices.
