# Delivery plan

## Product

Buyer: European family member. Primary user: a relative in Russia.
First commercial offer: one Family Plan, initially five devices, invitation link/QR,
Automatic Route, optional exit region, no server configuration exposed to the family.
Promise to validate: one button finds a working protected route and adapts to failure.
Do not advertise universal reachability, perfect anonymity or seamless gateway failover.

## Architecture invariants

1. Device identity is independent of IP; private keys remain on the owning device.
2. Relays, routes, transports and gateways are replaceable components.
3. Volunteer participation is explicit opt-in with revocable limits.
4. A volunteer relay is never a public Internet exit.
5. Only controlled gateways can create arbitrary Internet connections.
6. Relay protocol accepts authorized network-node identities, never arbitrary CONNECT/NAT.
7. No browsing, DNS history, payload or message logging.
8. Existing sessions tolerate control-plane outages within defined authorization leases.
9. Multiple independent transports/bootstrap paths are required before resilience claims.
10. BitTorrent is not a required feature; AUP and gateway restrictions are separate from
    browsing-history collection and cannot guarantee detection of every encrypted P2P flow.
11. Operator gateway operations handle abuse/rate limits/SMTP restrictions/isolation.
12. Home relay IPs must not be used for Internet egress; this is not a legal immunity promise.

## Phase 0 acceptance matrix

| Capability | Current implementation | Remaining proof |
|---|---|---|
| Encrypted client-to-gateway data | Rust QUIC lab stream with certificate validation | TUN traffic and device authentication |
| Relay loss | Two fixed relays and response-gap switching | Multi-host/mobile networks and jitter |
| Non-exit relay | Fixed upstream, no destination operation, internal network | OS-specific egress policy and adversarial audit |
| Signed state | Python Ed25519 signer/verifier, expiration and epoch checks | Rust consumption, cached epoch persistence, key rotation |
| Stable device/node identity | Local lab node-key provisioning | Device enrollment and authenticated use in data plane |
| IP mobility | Not validated | Fault-injection source-address and Wi-Fi/LTE tests |
| Gateway replacement | Not implemented | Explicit session/egress-anchor design |
| Transport diversity | One UDP/QUIC lab transport | Modular API and independent transport implementation |
| Distributed bootstrap | Single loopback lab API | Multiple delivery paths and offline cache |

Phase 0 is intentionally not marked complete just because relay failover works.

## Subsequent increments

Phase 1: Android prototype + Rust core, authenticated relay/gateway, control registration,
revocation and signed discovery. No billing or app store release.

Phase 2: multiple EU hosts and a small consenting connectivity test group. Record coarse
network cohort, success, TTC, loss and throughput; define short retention and aggregation.
Do not collect browsing activity or granular telemetry identifying a family member.

Phase 3: 20–50-family closed pilot only after leak/failover/security gates. Measure onboarding,
invitation completion, support/user and reconnection in actual target networks.

Phase 4+: Android MVP, commercial accounts/families/billing/admin/abuse operations; opt-in
Linux/Windows/macOS relays; iOS NetworkExtension; more transports and adaptive policy.
