# Architecture and trust boundaries

[Русский](architecture.ru.md) · [Guide](../README.en.md)

## Session structure

```text
Generated data client
  → inner QUIC + mTLS, gateway certificate pinned from signed state
  → local UDP adapter
  → outer QUIC + mTLS to relay A or relay B
  → relay UDP uplink to operator-selected gateway
  → controlled gateway test service
```

The relay decrypts only its outer hop. The inner client-to-gateway payload remains encrypted.
The relay sees peer addresses, timing, volume and gateway endpoint, but receives no browsing
URL, DNS history or application destination. The test gateway has no arbitrary egress operation.
The production gateway will necessarily observe some destination metadata; do not claim anonymity
against a colluding gateway/relay or traffic correlation.

## Keys and admission

Each role has a separate P-256 private key and a CA-issued certificate. Stable identity is
SHA-256 of DER SubjectPublicKeyInfo, independent of endpoint IP. The signed catalog binds
identity, current certificate fingerprint and endpoint. Certificate rotation can preserve the
identity if the key is retained, but automatic rotation is not implemented.

`scripts/identity.py` creates the private key and public CSR locally. The issuer checks CSR
signature and signs its public key. In the single-host test, separate role directories simulate
separate devices; the host administrator can access them. This is not hardware-backed mobile
key custody. No device private key is sent over the enrollment/control protocol.

TLS requires device client-auth certificates. After the handshake, the relay/gateway checks
certificate membership before allocating a relay UDP uplink or serving application data. A
server certificate cannot substitute for a device credential because of its EKU and membership.
Client checks CA chain, server name and signed certificate fingerprint. No 0-RTT application
traffic is enabled. Standard QUIC/TLS handles encryption, packet authentication and replay;
there is no custom cryptographic algorithm or reusable plaintext admission token.

## Signed discovery

The control API signs the exact JSON payload bytes with Ed25519 under the domain separator
`family-connect/network-state/v1\0`. Envelope fields are base64 payload and signature; payload
schema version is 2. The domain remains version 1 intentionally for envelope compatibility.
Rust rejects invalid signatures, expired/future leases, unsupported schema, duplicate identities,
invalid node roles, multicast/unspecified endpoints and relay Internet-exit declarations.

The trust root is provisioned outside discovery. `/v1/trust-root` is a provisioning aid, not a
trust-on-first-use mechanism. A valid signature authorizes operator-declared network endpoints;
a compromised signer remains a critical threat. Production should constrain egress at the OS
layer too, and introduce offline roots/intermediates and signer rotation.

Rust tries configured bootstrap URLs, then uses valid cache when sources fail. A signed cache
file also stores the epoch/issuance high-water mark across restart. Updates use atomic rename
and fsync. Membership changes require a higher epoch; an older issuance at the same epoch is
rejected. An expired but correctly signed cache retains the rollback floor, not permission to
connect. Deleting trusted local state resets that floor: protecting the device filesystem is
part of the threat model.

The lab exposes membership fingerprints in its private catalog. This is not the final
privacy-preserving public directory design. Before a public network, separate public topology
from device-specific authorization and define minimal telemetry retention.

## Revocation and offline operation

The operator-local CLI edits membership under a file lock, increments epoch, and replaces the
file atomically. There is no public administrative HTTP endpoint. Nodes poll every five seconds,
with three-second timeout per bootstrap URL, and check session authorization once per second.
Timing is an observed target, not a hard real-time guarantee. Invalid/unreachable updates never
replace an already trusted valid cache.

A node/device removal closes active sessions after the new state is received. Total control
outage delays revocation until the last signed lease expires. At expiry both new and existing
sessions fail closed. Indefinite offline service and immediate global revocation are incompatible;
this increment chooses a bounded lease, normally 900 seconds.

## Non-exit and operational limits

Relay accepts opaque inner datagrams, not destination commands. Its configured gateway name
must resolve to a gateway role in signed state; address or identity changes terminate the
existing relay session. Only the connected UDP socket receives replies from that gateway.
The client additionally authenticates the actual inner gateway, so a relay cannot impersonate it.

Core containers run unprivileged, read-only, with dropped capabilities and role-specific mounts.
The data network is Docker-internal. The control API has a separate management network and a
loopback host port. A relay cannot mount the gateway private key or the control signer.

Admission is capped at 64 simultaneous handshakes/sessions per node, with a five-second handshake
timeout. Relay byte budgets are coarse per-session limits. These do not constitute production
DDoS protection, per-device fairness, monthly quotas or an independent security audit.

Gateway migration still destroys the existing inner session. Public TCP/NAT flow survival needs
an egress-anchor/state design and separate fault tests. Relay path migration alone cannot prove it.

References: [QUIC migration](https://www.rfc-editor.org/rfc/rfc9000.html#section-9),
[rustls client verifier](https://docs.rs/rustls/latest/rustls/server/struct.WebPkiClientVerifier.html),
[Quinn connections/datagrams](https://docs.rs/quinn/latest/quinn/struct.Connection.html).

## Separate real-traffic testbed

The next step is implemented separately from the authentication lab described above:
[WireGuard interface over QUIC and relays](data-plane.en.md). It enables controlled IPv4
egress while retaining the relay non-exit invariant.

## Next deployed increment

The current network extends to a second VPS: [cross-server relay and failure test](distributed.en.md).
The results above remain the historical single-host validation.
