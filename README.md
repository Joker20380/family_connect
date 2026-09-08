# Family Connect

Adaptive private connectivity for families across borders.

**Status: isolated Phase 0 laboratory, not a VPN service or an Android application.**
No public Internet egress is implemented. Do not enable volunteer participation yet.

## Implemented

- Rust gateway serving a bounded test stream over certificate-verified QUIC/TLS 1.3.
- Rust UDP relays forwarding opaque inner QUIC datagrams to one operator-configured gateway.
  Packet contents cannot select an IP, port, DNS name, CONNECT destination or Internet exit.
- Local client path adapter switches relay after a 1.5-second response gap while retaining
  the existing QUIC connection. This is a laboratory detector for an active download,
  not production idle-session health checking or an adaptive path scoring algorithm.
- Fixed 16 MiB integrity-checked transfer and a script killing relay A during the transfer.
- Python read-only control API with Ed25519 signed network state, expiry, epoch rollback
  rejection and an explicit relay/non-exit policy check.
- Isolated Compose network, unprivileged core processes, dropped capabilities,
  credential mounts separated by role, no externally published data-plane ports.

## Run the laboratory

Requirements: Linux, Docker Compose, OpenSSL, Python 3.

```sh
docker compose build
sudo ./scripts/provision.sh
docker compose up -d control gateway relay-a relay-b
./scripts/test_failover.sh
```

The API is available only on `127.0.0.1:18080` on the host:

```sh
curl http://127.0.0.1:18080/healthz
curl http://127.0.0.1:18080/v1/network-state
```

Remote inspection uses SSH port forwarding, not an unauthenticated public API:

```sh
ssh -L 18080:127.0.0.1:18080 root@185.251.89.19
```

The root public key must be pinned through trusted provisioning. Fetching a new key
from `/v1/trust-root` on an untrusted network does not establish trust. The verifier
is currently tested in Python; the Rust client uses a provisioned gateway certificate
and static routes, and does **not yet consume the signed catalog**.

## Security boundary

The relay API has no arbitrary-destination operation. Relays mount neither the gateway
private key nor the control-plane signing key. Inner payloads are QUIC-encrypted between
client and gateway. Relays still observe peers, timing, volume and gateway endpoint.
This provides no anonymity guarantee against traffic correlation or colluding nodes.

The outer admission token is a **shared laboratory token sent in the outer UDP header**.
It prevents accidental unauthenticated use, but is observable/replayable by an on-path
party. It is not production authentication. The private Docker network is essential.
Before public testing, replace this with authenticated encrypted hop transport,
device-bound short-lived capabilities, replay protection and bounded resource allocation.

A relay has one configured gateway; the prototype does not yet authenticate that next-hop
identity at the outer layer. End-to-end server certificate validation protects the inner
channel. Signed catalog/node identity integration remains a Phase 0 acceptance item.

Prototype limits are coarse per-second ingress/per-session return limits, not monthly
volunteer quotas, production congestion control, or a complete anti-abuse mechanism.
No access logs, browsing history, DNS queries or payload contents are stored by the API.
Test artifacts contain only counts, duration and a checksum of generated test bytes.

## Session migration is not gateway replacement

A relay failure changes the path to the **same live gateway**, which retains QUIC state.
QUIC connection migration does not transfer that state to a different gateway process.
Changing the public egress IP also changes Internet-facing TCP/NAT flows. Phase 0 therefore
reports relay failover separately from gateway failover. A gateway failure currently
terminates the transfer. Preserving external flows requires an egress anchor/state design;
it must not be advertised before a fault-injection test proves it.

## Next acceptance milestones

1. Device-held keys and authenticated hop admission; signed catalog verification in Rust,
   pinning, revocation and bounded cached-operation semantics.
2. Relay IP mobility tests, multiple independent bootstrap delivery paths, transport API,
   health probing and path-selection hysteresis.
3. Android VpnService/TUN integration and controlled gateway egress with IPv4/IPv6/DNS
   leak tests, kill switch, Wi-Fi/LTE migration and measured throughput/CPU/battery.
4. Gateway failure: specify reconnect semantics first; then validate an egress-anchor design
   if continuity of existing Internet flows is a product requirement.
5. Private multi-host network. Only then family onboarding, invitations, subscriptions,
   voluntary relay enrollment, billing and operational abuse procedures.

Architectural reference: [QUIC RFC 9000, migration](https://www.rfc-editor.org/rfc/rfc9000.html#section-9).
The Reticulum-inspired control model does not imply using Reticulum as the data plane.
