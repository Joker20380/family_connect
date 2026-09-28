# Architecture map / Карта архитектуры

28.09 **5N.5 PASS**: opt-in bounded/fair TCP mux + wire DNS above the existing single
Family TLS/ReliableStream/Telemost path; default16/max32,64KiB credit,16KiB DATA.
Physical4 public HTTPS and304.138s mixed TCP+DNS, native destination resolver denied;
[exact evidence/limits](releases/2026-09-28-webrtc-eu5-mux-dns.ru.md). No TUN/rollout.
Hostname OPEN already resolved at the gateway in5N.4, not at the Android client.
[DNS dependency audit, containment proof and manual verification](testing/webrtc-dns-containment.ru.md)
separates carrier bootstrap from user destinations; no whole-device DNS claim.

## Current decision — Restricted WebRTC to EU Gateway first

Earlier28.09: isolated [5N.4 single TCP forwarding](../carrier/tcpforward/README.md)
adds `Application TCP → Family TCP framing → Family TLS → ReliableStream → VP8`
above the unchanged proven carrier. One admitted session/stream, explicit FIN and
structured connect errors; gateway DNS with public-destination validation, no mux
or TUN. **5N.4 PASS**: physical public HTTPS200/10MiB and controlled exact duplex
300.821s; security/lifecycle/regressions/cleanup accepted. No production rollout
or5N.5; [proof and limits](releases/2026-09-28-webrtc-eu4-single-tcp.ru.md).

2026-09-27 implementation checkpoint: [carrier/](../carrier/README.md) recovers
the interrupted isolated Go/Pion prototype initially for **5N.1**. Bounded binary
framing, Telemost join/signaling, VP8 and a separate diagnostic DC mode exist;
local two-process Pion tests pass. Real Linux↔Telemost VP8↔Amsterdam **5N.1 PASS**
on27.09, clean runtime `a13068e`: 291 exact echoes including30s/5min and live
failure teardown. Observed RTT≈4s and useful roundtrip≈0.0655Mbit/s are limitations,
not production performance acceptance. [5N.1 evidence](releases/2026-09-27-webrtc-eu1-telemost-binary.ru.md).

5N.2 now has a separate [Android diagnostic APK](../clients/android/telemost-runtime/README.md):
shared Go core → unchanged Linux CLI or Android PIE CLI child → bounded foreground
test Service/Activity. No second source copy, Java WebRTC, JNI or product Go runtime.
Physical **5N.2 PASS**, clean `3f65346`: Redmi Note9 Pro/Android12 ordinary cellular
↔Telemost VP8↔Amsterdam,372 exact echoes including30s/5min and lifecycle/fault checks.
Final RTT≈2s/aggregate0.131069Mbit/s; earlier full run≈4s/0.065536Mbit/s are baseline
measurements, not a throughput ceiling or production acceptance.
Wi-Fi handoff/deep Doze/restricted-mobile not claimed.
Isolated5N.3 now adds `familysession`: standard TLS1.3 above unchanged VP8,
existing DeviceIdentity/ProductStore-derived disposable authorization, gateway pin,
signed revocation snapshot and bounded lease. No production authority/identity
store integration. **5N.3 PASS**: physical Android374 exact echoes/302.001s sustained,
live admission/replay rejection and lifecycle/recovery. Two earlier SSH-lifetime
failures are retained; accepted run isolates its observer without carrier changes.
[Report/limits](releases/2026-09-27-webrtc-eu3-family-session.ru.md).
5N-REL-1 now inserts `ReliableStream` **below TLS and above VP8/RTP** in Family
mode. Cumulative ACK + bounded selective-repeat/SACK restores ordered bytes before
TLS; sender8/receiver16,16KiB defaults, no crypto/auth changes or unreliable fallback.
Fresh bidirectional epochs scope each attempt, not an additional authentication
layer. Plaintext carrier mode is unchanged. [Protocol/threat boundary](../carrier/reliablestream/README.md)
and [physical/local acceptance record](releases/2026-09-27-webrtc-5n-rel1-reliable-stream.ru.md).
At that earlier REL-1 boundary there was no egress gateway; current5N.4/5N.5 TCP
egress is described above. Still no TUN or production transport integration. All sockets remain
unprotected; future HTTP/WS/Pion transport.Net/DNS protection requires an explicit
cross-process SCM_RIGHTS+protect ACK bridge or in-process JNI, not child fd integers.
[5N.2 report](releases/2026-09-27-webrtc-eu2-android-binary.ru.md).

Priority correction25.09, preparation-only: remove the Windows home-PC detour from
restricted mobile Internet access. Reticulum is retained for identity binding,
control/recovery, provisioning, messages/discovery and future Meshtastic bootstrap.
Home Gateway remains a secondary LAN/NAS/RDP/residential-egress feature. Existing
Home/RNS-underlay diagrams below still apply to that feature, not the current critical path.

```text
CONTROL: Device Identity / FAMILY ↔ Reticulum control/recovery/provisioning

Android apps → VpnService/TUN → existing stream conversion
                                     │
                         existing transport selection
                         ├── AWG
                         ├── TCP / XHTTP
                         └── WebRtcRestrictedTransport
                              Family mux + authenticated E2E encryption
                                     │
                              opaque Telemost VP8 carrier
                                     │
                                  SFU / RTC
                                     │
                         headless Linux EU Family Gateway
                         Family admission / mux / DNS / egress
                                     │
                                  Internet
```

Telemost first, WB fallback after real-network validation; no second transport
manager/TUN converter unless reuse is shown unsuitable. Phase1 TCP+DNS, phase2
UDP with reserved framing; unsupported UDP/IPv6 must not escape directly. Provider
is untrusted; encryption of payloads, destinations and DNS is above carrier and
Family admission precedes any egress. Production integration of secure sessions,
reliability and mux remains open; isolated TLS/reliability is covered by5N.3/REL-1,
not a deployed production multiplexer. One conference supports many connections.
Reticulum encapsulation is optional and benchmark-driven, not mandatory for5N.
[Existing design/decision](reticulum/HOME_GATEWAY_DESIGN.md) · [Gates](PLAN.md).

## Whitelisted WebRTC Carrier — architecture extension

Preparation-only checkpoint; no carrier implementation or runtime acceptance yet.
Previous Home Gateway + interchangeable WebRTC underlay = the path below.
Existing direct paths and the selectable IP data transport strategy remain valid;
this workstream proves opaque RNS frame carriage before IP-over-RNS-over-WebRTC.

```text
Android / Device Identity
          │
Reticulum Overlay (identity / Link encryption / routing)
          │
UnderlayPathManager
          ├── DirectIPv6
          ├── DirectIPv4 / future NAT traversal
          └── WebRTC Carrier (isolated process; framed private IPC)
                      ├── WB (reserve candidate)
                      ├── Telemost (first PoC candidate)
                      └── VK (later)
                            │
                         SFU / RTC
                            │
                  Windows Reticulum Overlay
                            │
                    Windows Home Gateway
                            │
                  existing Family Connect VPN
```

Reticulum = overlay; WebRTC = underlay. SFU/signaling is untrusted and cannot
replace Family authentication. Only RNS Link payload encryption is claimed;
announces/public metadata are not secret. Session room IDs are ephemeral and
rendezvous must avoid a circular bootstrap dependency. No TUN/SOCKS/HTTP proxy
belongs in the carrier. WB guest join is a reference-code finding, not proof of
anonymous room creation or mobile whitelist availability. The full contracts,
reference SHAs, lifecycle/security and WEBRTC-1–5 gates extend the
[existing design](reticulum/HOME_GATEWAY_DESIGN.md). [Plan](PLAN.md).

## Personal Gateway / Reticulum Transport

Strategy revised by the owner on 2026-09-25: the objective is a secure Android↔home
Windows connection on a mobile network with active allowlist restrictions.
Reticulum carries discovery/authentication/transport negotiation and recovery;
user IP packets may use any approved encrypted data transport. IP-over-RNS is
optional. [Full design and acceptance](reticulum/HOME_GATEWAY_DESIGN.md).

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

Existing Device Identity/FAMILY authorizes both peers and binds negotiated data keys
and paths. End-to-end encryption terminates at the home PC even when using a relay.
First prove reachable control/bootstrap and data ingress on the target network;
then relay-assisted sessions, real TUN packets and gateway egress. Direct paths/NAT
traversal are later optimisation. No static home IP/DDNS or manual key transfer.
RNS control success alone is not data reachability or NAT traversal.

Reference `rns==1.5.1` stays behind the control adapter. Reuse existing VPN engines
where suitable; a reverse/relay data path still needs implementation. No transport
has been selected or validated for the restricted mobile path yet. Preserve mutual
FAMILY authorization, fail-closed including DNS/IPv6, Android socket protection,
Windows route ownership and no ISP fallback from VPN-upstream mode. Experimental
flag defaults OFF. Home Gateway remains unimplemented; RNS-2 now means real IP
packets over the selected transport, not necessarily over RNS.

Family Connect contains a product client path and separate networking experiments.
Use [STATUS](STATUS.md) for platform integration and deployment facts; older design
records describe their named stage, not the entire current application.

For source entry points, module responsibilities, data stores and tests, use the
[module code map](code-map/README.ru.md).

## Product and device path

Invitation/entitlement → device identity → provisioning → client verification and
protected state → platform VPN adapter → transport/gateway.

- [Registration: EN](registration.en.md) / [RU](registration.ru.md): product admission,
  single-use challenges and entitlement. Dated module boundaries are historical.
- [Device identity ADR: EN](adr/001-identity-provisioning.en.md) / [RU](adr/001-identity-provisioning.ru.md).
- [Provisioning/cache: EN](provisioning-provider.en.md) / [RU](provisioning-provider.ru.md).
- [Stage 5 control design](stage5-architecture.ru.md) and [native binding](stage5-native-binding.ru.md):
  signed configuration delivery, verification and recovery. Initial AWG/platform limits
  in these dated documents are superseded where STATUS has newer runtime evidence.
- [Android source](../clients/android/), [Linux source](../clients/desktop/),
  [Windows source](../clients/windows/).

Android friends currently exposes AWG 3.1 and TCP REALITY options. Desktop releases
have their own capabilities and activation; see STATUS for current versions. Do not infer identical feature support
from shared architecture. Device provisioning/configuration is distinct from the
[offline-signed application update catalog](updates.en.md).

## Messenger

[Design](reticulum-messenger.ru.md) · [Core](../messenger/README.ru.md) ·
[Android voice/UI checkpoint](releases/2026-09-23-voice-scroll-beta49.ru.md) ·
[Foreground delivery/animation evidence](releases/2026-09-19-android-beta16.ru.md).

The core uses separate chat identities, encrypted storage and existing RNS/LXMF
components. Android integrates native screens and a carrier. Early core notes saying
there is no Android UI are historical, not the current pilot state. Android now has a foreground delivery service, notifications, text edits and voice.
Screen-off notification delivery was confirmed; deep Doze latency and broader
restart/offline acceptance remain open. There is no FCM integration.

## Experimental relay network

[Original QUIC architecture and threat model: EN](architecture.en.md) /
[RU](architecture.ru.md) · [Data plane: EN](data-plane.en.md) / [RU](data-plane.ru.md).

The inner/outer QUIC laboratory is separate from the current Android VPN data path.
Its mTLS, revocation timing and failover claims must not be generalized to every client.

## Trust and operations

[Security](../SECURITY.md) · [Privacy](privacy.md) ·
[Documentation map](README.md) · [Current plan](PLAN.md).
