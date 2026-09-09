# Two server sites

[Русский](distributed.ru.md) · [Home](../README.en.md)

**Status: the cross-server deployment was decommissioned at the owner’s request.** Family Connect code, keys, containers, networks, images and installation archives were removed from `186.246.51.201`. The server is reserved for websites; do not redeploy VPN services there without a new explicit instruction from the owner. The primary site tunnel was removed and catalog epoch 3 contains gateway-lab, relay-a and relay-b. The material below is historical test documentation, not the current deployment.

## Deployed topology

- `185.251.89.19`: control plane, controlled Russian gateway and backup relay-a.
- `186.246.51.201`: relay-remote in `/opt/apps/family_connect-relay`.
- Both public IPs were reported as RU. Geographic redundancy is not established.

```text
Linux test client on the primary VPS
  → operator WireGuard site link → relay-remote on the second VPS
  → operator WireGuard site link back → Russian gateway → Internet

remote relay and site-router failure:
  client → local relay-a → the same gateway → Internet
```

This is actual cross-server traffic, but not yet a phone/laptop client in Europe.
The existing direct user WireGuard VPN on UDP/51820 continues separately.

## Identity, routes and Reticulum

The remote relay's private identity key was generated on the second VPS and stays there.
The primary received a public CSR, issued a certificate and added its identity/fingerprint to
the signed catalog. The relay catalog endpoint is `172.29.94.11:4444`; the gateway endpoint is
`172.29.93.10:4433`. The remote relay refreshes the signed catalog over the site link and caches it.

Reticulum itself is not installed. Identity is independent of addresses, while the transport
still uses IP. Public WireGuard site endpoints are operator-configured in this increment.
Automatic public IP rediscovery, gateway loss and distributed bootstrap independent of the
primary server remain unfinished. During a complete control-plane outage, cached authorization
lasts only until the signed lease expires, normally 15 minutes.

## Isolation

- Remote Compose project: `family-connect-remote`; existing applications were not changed.
- Primary router project: `family-connect-site` in `/opt/apps/family_connect-site`.
- UDP/51830 exposes only the operator WireGuard link. Relay/gateway UDP is not exposed directly.
- Relay has no capabilities and lives on an internal Docker network. The site router forwards
  only client UDP to the relay, UDP to the gateway, and TCP to the control API. Firewall rules
  prohibit arbitrary public egress through it.
- Internet egress remains exclusively on the primary controlled gateway; the remote VPS is not an exit.
- Site keys are generated independently on each VPS and only public keys are exchanged.
  `state-site/`, `state-remote/`, `state-enroll/` are excluded from Git and build context.
- `routes` prepares the network namespace before relay startup. Readiness checks the route,
  rather than requiring a continuously available API. Recreating `routes` requires recreating
  `relay` too because they share a network namespace.

Site WireGuard uses MTU 1440 for the tested IPv4 path to accommodate outer QUIC UDP payloads
up to 1400 bytes. Arbitrary mobile path MTUs are not verified.

## Operations

The primary already has `family-connect-data` and its `172.29.93.0/24` network. The site router
joins as `172.29.93.254`; the remote network is `172.29.94.0/24`. The catalog prefers relay-remote
with relay-a as backup. The previous relay-b is stopped.

```sh
# Primary VPS, /opt/apps/family_connect-site
docker compose -f compose.site-primary.yaml up -d

# Remote VPS, /opt/apps/family_connect-relay
docker compose -f compose.site-remote.yaml up -d

# When recreating the remote network namespace
docker compose -f compose.site-remote.yaml up -d --force-recreate routes relay
```

Router keys are mounted for UID 0; relay identity/cache belong to UID 65532. Key directories
use mode 0700 and private files 0600. Public trust files are readable. `site_key.py` generates a
local key; `identity.py` generates a local identity and CSR; `register_relay.py` performs operator
certificate issuance and atomic catalog updates with increasing epochs under the shared lock.
This is not a public enrollment API. Never transfer CA private keys or relay private keys between VPSs.

To repeat the test **from the operator laptop** with SSH access to both VPSs:

```sh
python3 scripts/test_distributed.py
```

The test creates a temporary client on the primary, measures byte growth on the remote site
link, starts one HTTPS download without retry/resume, and stops only the two Family Connect
containers on the remote VPS. Other applications and the server itself continue running.
It then restores the remote services and removes the test client. Operator SSH keys stay on the laptop.

The old `test_data.py` is for a single-host catalog. It refuses to dismantle this topology when
relay-remote is active. Never roll back the signed catalog to an older epoch.

## Results and limitations

The [test report](distributed-validation-result.json) records 8 MiB, one HTTPS connection,
one inner QUIC session and one switch after remote-service shutdown. Curl is limited to
256 KiB/s; this is a functional test rather than a throughput benchmark. The SHA-256 is observed;
TLS protects the public HTTPS transfer's integrity.

The tested fault is remote-service loss, not power failure or loss of the primary VPS.
Gateway/control and the test client remain on the primary. Gateway session migration,
independent geographic paths, public IP mobility and Android access through the adaptive core
remain future work.

Relay certificates are issued for 30 days; automatic renewal is not implemented yet.
