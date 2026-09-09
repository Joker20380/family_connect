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
