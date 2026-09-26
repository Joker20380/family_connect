# Architecture map / Карта архитектуры

## Current decision — Restricted WebRTC to EU Gateway first

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
Family admission precedes any egress. Secure-session/reliability/mux selection is
an open implementation prerequisite. One conference supports many connections.
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
