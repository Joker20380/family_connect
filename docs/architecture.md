# Phase 0 decisions

Identity is permanent; routes are replaceable. Identity keys must remain on their owning
device. The network operator authenticates membership; peers may distribute signed state
without becoming trusted state authors. Production signing should use a rotatable online
intermediate under an offline root, with versioned revocation and bounded offline leases.
Current key files and node identities are laboratory provisioning only.

## Non-exit invariant

Volunteer relays forward only to authenticated, operator-authorized network nodes. Clients
must never supply a next-hop arbitrary address. Production requires BOTH a constrained
protocol and operating-system egress controls to defend against implementation mistakes.
In this lab the destination is a literal fixed gateway address. The internal-only Docker
network has no Internet egress. This does not demonstrate volunteer deployment hardening
on arbitrary home operating systems yet.

Public service destinations belong inside client-to-gateway encryption. The gateway may
observe destination IPs and potentially plaintext DNS/HTTP unless protected end to end.
Do not claim that a gateway cannot observe metadata, or that this design eliminates legal
exposure for participants; egress concentration is an architectural property, not a legal
immunity guarantee.

## Threats to test before public access

- Malicious clients requesting arbitrary relay destinations, unregistered next-hop identities,
  oversized packets, token replay, connection churn and spoofed-source amplification.
- Malicious relays altering or replaying inner ciphertext, stripping catalogs, observing
  timing, silently dropping traffic or redirecting to an unauthorized gateway.
- Expired, rolled-back, future-dated or wrong-root network state; compromise and rotation
  of online signing keys; device revocation while the backend is unreachable.
- Endpoint/certificate pinning mismatch, DNS rebinding, bootstrap enumeration and privacy
  leakage through persistent device IDs, granular ISP/region telemetry or raw source IP logs.
- IPv6/DNS bypass during reconnect; Availability First must explicitly communicate loss of
  protection and must not display Protected when falling back to unprotected connectivity.

## Deliberately deferred

No universal censorship-resistance claim from a single UDP/QUIC transport. No promise of
perfect P2P detection without visibility into encrypted applications. No billing, public
registration, volunteer recruitment or public Internet exit in this commit. No mobile UI
that reports Connected based only on a tunnel handshake: later UI must verify working
protected Internet reachability.

KPI definitions: successful connection requires a protected end-to-end probe, TTC starts at
user intent and ends at that probe; survival is tracked separately for relay loss, address
change, network change and gateway failure. Report median/p90/p95 with sample sizes and
network cohorts, not just success examples.
