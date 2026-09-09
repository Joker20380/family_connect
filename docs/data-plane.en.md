# Real IP traffic through the adaptive path

[Русский](data-plane.ru.md) · [Guide](../README.en.md)

## Implementation

The separate `family-connect-data` Linux testbed connects a real kernel WireGuard interface
to the authenticated relay core. Applications use ordinary TCP/UDP and system DNS.

```text
curl / DNS / Linux IP stack
    ↓ fcwg0 (kernel WireGuard)
local UDP bridge
    ↓ one inner mTLS QUIC stream
    ↓ replaceable outer mTLS QUIC relay A / relay B
controlled gateway: QUIC → local WireGuard
    ↓ fcwg0 → firewall → NAT
public IPv4 Internet
```

The inner QUIC connection and the gateway UDP socket survive relay replacement. The WireGuard
peer, tunnel address and outbound TCP NAT state consequently remain unchanged. This addresses
relay loss with the same gateway; gateway failure remains unsolved.

Reticulum is not installed. The testbed uses the existing identities, signed catalog,
membership/lease verification, certificate pinning and automatic path switching.

## Protocol and security boundaries

- `packet-client` requires both inner and outer mutual TLS authentication.
- The gateway enables packet forwarding only with `ENABLE_PACKET_GATEWAY=1` and a signed
  `internet_exit` permission. The original authentication lab does not enable this operation.
- The gateway forwards packets only to local WireGuard at `127.0.0.1:51820`.
  Clients cannot supply a destination address to the bridge operation.
- Relay code still forwards encrypted packets only to the announced gateway. There is no
  relay CONNECT/SOCKS/NAT API, and the relay Docker network has no public egress.
- Stream framing is a two-byte big-endian length followed by one encrypted WireGuard packet.
  Lengths 1–2048 are accepted; empty, oversized and truncated frames are rejected. UDP arrivals
  never cancel a partial frame read, preserving message boundaries.
- Only the controlled gateway decrypts IP packets, filters traffic and performs NAT.
  TCP/25 and private/reserved IPv4 destinations are blocked.
- IPv6 is routed into the VPN with egress disabled. The client container has no ordinary public
  route; losing both relays closes connectivity. This does not configure a laptop kill switch.
- Browsing history, DNS history and packet contents are not logged. Test artifacts describe
  the explicitly requested test download rather than user traffic.

WireGuard packets currently use a reliable ordered stream. This validates real routing without
inventing a fragmentation algorithm. It adds overhead and delays later packets when an earlier
packet is lost; it is not claimed to be an optimal calling transport. The next engineering step
is measuring loss/latency and selecting a packet transport with a tested MTU. Cryptographic
algorithms are unchanged.

## Deployment

Requires Linux with WireGuard support, Docker Compose and Python 3. From the repository root:

```sh
docker compose -f compose.data.yaml build
sudo ./scripts/provision_data.sh
python3 scripts/test_data.py
```

The testbed uses `state-v3/`, subnet `172.29.93.0/24` and API `127.0.0.1:18081`.
No public UDP ports are published. Test identities and WireGuard keys are generated in separate
directories on one operator host. These are laboratory keys, not the user's phone/laptop keys.
`state-v3/` is excluded from Git and the Docker build context.

WireGuard helper containers receive NET_ADMIN only in the client and gateway network namespaces.
Rust processes have no capabilities; relays never receive NET_ADMIN. Recreating a core container
requires recreating its WireGuard helper because they share a network namespace. The test script
handles this automatically.

## Acceptance

`test_data.py` performs one 8 MiB HTTPS download from Cloudflare's public test service,
without retry/resume. After receiving a partial file it kills relay A and verifies:

1. HTTP 200, the expected size and one HTTPS connection.
2. One inner QUIC session and an observed relay switch.
3. External IPv4 `185.251.89.19`, with DNS functioning through the VPN.
4. No public IPv6 connectivity.
5. No new public connection after both relays have been stopped.

The observed download SHA-256 is recorded; it is not compared against a pre-published file hash.
HTTPS authenticates the server and protects transfer integrity. The test depends on the public
service's availability and targets this Russian server.

Artifacts are written to `artifacts/data3/`. Afterwards the client is stopped and test infrastructure
restored. The direct `family-connect-pilot` VPN and original `family-connect` lab are unchanged.

This remains one Docker host plus an external HTTPS service. Wi-Fi/LTE transitions, Android TUN,
international relays, recovery of lost paths, gateway migration and real-network performance
are not proven. The user's Android/Linux profiles still connect directly.

## References

[WireGuard network namespaces](https://www.wireguard.com/netns/)
and [Quinn connections and streams](https://docs.rs/quinn/latest/quinn/struct.Connection.html).

## Verified result

On September 9, 2026, the final implementation transferred 8 MiB over HTTPS in 28.99 s with
a configured 256 KiB/s download limit. Relay A was killed after 708,608 bytes. One HTTPS
connection and one inner QUIC session survived, with one relay switch. Egress was
`185.251.89.19`, RU. With both relays stopped, hostname and direct-IP checks failed.
The unlisted certificate was rejected; 4 Rust and 6 Python tests passed. This is a functional
test result, not a maximum-throughput benchmark. [Machine-readable report](data3-validation-result.json).

## Next deployed increment

The current network extends to a second VPS: [cross-server relay and failure test](distributed.en.md).
The results above remain the historical single-host validation.
