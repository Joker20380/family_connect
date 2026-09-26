> Historical design/plan. Current delivery status: [STATUS](STATUS.md); active work: [PLAN](PLAN.md). Goals below are not guarantees of the current pilot.

## Current priority25.09 — Restricted Android→EU (5N)

**Stage5 now prioritizes Android → Telemost VP8 → headless Linux EU Gateway →
Internet.** Windows Home Gateway and IP-over-Reticulum are not prerequisites.
Reticulum control/recovery/provisioning/identity/discovery remains first-class.
The user-reported Krasnodar cellular→Belgium video call supports provider selection,
not a claim of working Family binary transport. Current scope: preparation only.

Preserve5A–5M; add **5N.1–6 = WEBRTC-EU-1–6**: desktop/Linux binary → Android/EU
binary → authenticated Family session → single HTTPS stream → multiplexed TCP/DNS
→ full-device Android. Reuse generic5H/5I work; validate in Krasnodar (5M/5F), then
WB fallback (5L). RNS/Home Gateway5J/5K and home-specific5B–5E remain secondary.
No earlier gate is closed by this reprioritization. Meshtastic stays future control
bootstrap. [Plan/gates](PLAN.md) · [Existing design](reticulum/HOME_GATEWAY_DESIGN.md).
Earlier immediate-next-step orders below are superseded by this section.

## Whitelisted WebRTC Carrier extension — 2026-09-25

Current scope is **documentation/preparation only**, per the owner's latest request.
We are at global stage5, preparing5A/5H. Existing5A–5G retain their numbering and
open gates. Added work: **5H** UnderlayPathManager → **5I** single-provider carrier
(WEBRTC-1/2) → **5J** RNS-over-WebRTC (WEBRTC-3) → **5K** Home Gateway-over-WebRTC
(WEBRTC-4/5) → **5L** multi-provider support → **5M** restricted-mobile acceptance
(linked to5F). Execution starts with5A reachability,5H/5I/5J; earlier letters are
not thereby complete. [Current plan](PLAN.md) · [Design](reticulum/HOME_GATEWAY_DESIGN.md).

Telemost is the first candidate after the user-reported Krasnodar→Belgium video
call (25 Sep); WB is the reserve. Binary/headless carrier availability is untested.
Reticulum overlay consumes interchangeable direct/WebRTC underlays; provider logic
stays below it. All WEBRTC gates are untested. Device tests and code are deferred.

## Stage 5 / Home Gateway — active development (strategy revised 2026-09-25)

**Current position: start of 5A — design and ingress reachability validation.**
Primary goal: a secure phone↔home-PC connection while mobile allowlist restrictions
are active. Reticulum supplies control/discovery/authentication/negotiation/recovery;
IP packets use a selected encrypted data transport. IP-over-RNS is optional.
[Current plan](PLAN.md) · [Design and gates](reticulum/HOME_GATEWAY_DESIGN.md).

- **5A Control/discovery and ingress reachability** — verify both control and data paths on the target restricted mobile network; existing Device Identity/FAMILY.
- **5B Android ↔ Windows encrypted session** — RNS-1: negotiated data handshake and reconnect; reachable relay first.
- **5C IP tunnel over selected transport** — RNS-2: real IPv4 packets/return path; RNS packet carriage not required.
- **5D Windows Personal Gateway** — explicit diagnostic Internet, RNS-3.
- **5E existing VPN upstream integration** — same VPN exit IP, RNS-4.
- **5F real mobile-network validation** — Краснодар with active restrictions, measurements and 30–60 minute stability, RNS-5.
- **5G direct paths / zero-config optimisation** — direct IPv6/IPv4, NAT traversal and multiple paths after measurements.

Home Gateway implementation and all RNS gates remain open. Stage4 pilot delivery
was accepted; stage5 is not complete. Numeric5.1–5.6 control/fleet tasks remain
separate from lettered5A–5G. Stage6 recovery and stage7 commercial/service work are
still ahead. Reuse relevant5.3в ingress work without restarting unrelated debt.
An encrypted relay carries data to the home PC; it is not the selected Internet exit.
A reachable RNS destination alone does not make a blocked data endpoint reachable.
Existing VPN defaults and releases stay unchanged.


# Roadmap

[Русский](roadmap.ru.md) · [Guide](../README.en.md)

## Product and permanent invariants

European family buyer, relatives in Russia, one Family Plan initially for five devices,
invitation link/QR, Automatic Route and optional exit region. Never expose protocol/server
configuration as part of normal family onboarding.

Identity is independent of IP. Device private keys stay on their owning device. Volunteer
participation is explicit opt-in. Volunteers never provide public Internet egress. Only operator
controlled gateways may do so; relay protocol cannot accept arbitrary CONNECT/NAT destinations.
Browsing/DNS history and payloads are not logged. Active sessions use bounded offline leases.
Multiple independent transports/bootstrap paths are required before resilience claims.
P2P is not a required feature; gateway AUP/abuse controls must not become browsing-history
collection. Egress concentration is not a legal immunity guarantee for volunteers.

## Current acceptance state

| Capability | Implemented | Remaining |
|---|---|---|
| Authenticated data | Outer and inner QUIC mTLS; membership and server pins | Public enrollment, secure mobile key storage, rotation |
| Relay loss | Active-download switch preserving inner QUIC | Multi-host, address changes, Wi-Fi/LTE, idle health |
| Non-exit | Gateway selected by signed role/name; no destination API; isolated network | Host egress hardening and adversarial review |
| Signed discovery | Python signer, Rust verification, expiry, atomic cache/high-water | Offline root/intermediate lifecycle and large public-directory privacy |
| Revocation | Epoch-incrementing operator CLI and active-session checks | Commercial identity/subscription integration |
| Offline bootstrap | Valid cached startup, configurable source list | Actual independently hosted delivery sources |
| Gateway replacement | Not implemented | Explicit egress-anchor/state design and failure semantics |
| Transport diversity | Only UDP/QUIC | Transport API and independent fallback implementation |

## Next increments

1. Mobile/Android VpnService + Rust TUN prototype; IPv4/IPv6/DNS leak tests, kill switch,
   Wi-Fi/LTE, throughput/CPU/battery measurements. Keep it private.
2. Multiple EU hosts and a small consenting connectivity test group. Define SCR, TTC,
   survival per failure type and coarse cohort telemetry with bounded retention.
3. A 20–50-family pilot after security/connectivity gates: invitations, onboarding, support/user.
4. Android MVP, accounts/families/subscriptions/billing/admin and gateway abuse procedures.
5. Explicitly opt-in Linux/Windows/macOS relay enrollment and quotas; iOS NetworkExtension;
   more independent transports, path intelligence and geographic expansion.

Phase 0 is not declared complete merely because the current laboratory tests pass.

## Separate real-traffic testbed

The next step is implemented separately from the authentication lab described above:
[WireGuard interface over QUIC and relays](data-plane.en.md). It enables controlled IPv4
egress while retaining the relay non-exit invariant.

## Next deployed increment

The current network extends to a second VPS: [cross-server relay and failure test](distributed.en.md).
The results above remain the historical single-host validation.
