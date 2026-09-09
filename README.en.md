[Windows 0.2 — standalone installer and activation](docs/windows-native.en.md)

# Family Connect — English

[Русский](README.ru.md) · [Documentation index](README.md)

Reliable private connectivity for families across borders. The buyer is a European family
member; the first intended users are relatives in Russia. The eventual product offers a
Family Plan, invitations and one Connect button with automatic route selection.

## Client applications

Android and Windows/Linux: [installation, capabilities and limitations](docs/clients.en.md).

## Two server sites

Server `186.246.51.201` has been removed from the VPN; its code, keys and containers were deleted. The current network remains on `185.251.89.19`. [Historical two-VPS test](docs/distributed.en.md).

## Practical pilot: Europe → Russia

A separate direct WireGuard pilot targets the Russian server `185.251.89.19` for Android
and Linux, with distinct device keys. It provides real IPv4 Internet egress but is not yet
integrated with Rust discovery, family accounts or automatic relay selection.
[Connection instructions and limits](docs/pilot.en.md).

## Real traffic through relays

A separate Linux testbed connects a real WireGuard interface through the inner QUIC session
to controlled IPv4 egress. [Design and tests](docs/data-plane.en.md).
Existing user profiles remain direct; the Android application is not implemented yet.

## Current increment: authenticated discovery laboratory

- TLS 1.3 mutual authentication on outer client-to-relay QUIC connections and on the
  independent inner client-to-gateway QUIC connection. The shared plaintext token is removed.
- Operator-issued device certificates plus explicit membership in signed network state.
  A CA-issued but unlisted device is not authorized. Relays and gateways have separate
  server credentials; clients additionally match certificate pins from the signed catalog.
- Rust verifies Ed25519 signed state, pinned trust root, expiry, schema, node roles,
  unique identities and persistent monotonic epoch/issuance high-water marks.
- Endpoints are obtained from the verified catalog. Bootstrap URL order is configurable.
  A valid on-disk signed cache supports startup and continuing operation without backend.
- Operator-local revoke/enroll commands increment the epoch. Nodes refresh every five
  seconds; active connections are checked once per second. No private device keys are sent
  to the control API. Enrollment still uses operator provisioning, not a public onboarding API.
- Inner QUIC remains intact when switching between authenticated relay connections.
  Relay forwarding takes an operator-selected gateway name, not a client-supplied IP/port.
- Isolated Docker network without public data-plane ports or Internet egress. The API is
  published on host loopback only. Runtime mounts separate node/device keys and signing keys.

## Quick start

Linux, Docker Compose and Python 3 are required. Run provisioning as an administrator.

```sh
docker compose build
sudo ./scripts/provision.sh
docker compose up -d control gateway relay-a relay-b
./scripts/test_failover.sh
./scripts/test_auth.sh
./scripts/test_offline.sh
python3 scripts/test_revocation.py
```

See [operations](docs/operations.en.md) for restart, key protection and local inspection;
[testing](docs/testing.en.md) for exactly what each acceptance test proves.

## Boundaries

The authentication lab above still transfers generated test bytes. The separate data testbed
now carries real IP traffic, but neither is an Android app, public volunteer network or
censorship-resistance claim. Gateway replacement,
mobile network migration, general transport diversity and public enrollment remain pending.

The lab uses one CA and an online Ed25519 state signer. A production design still needs
an offline root/intermediate lifecycle, secure enrollment, certificate rotation, hardware
key storage, stronger per-device abuse limits and an independent security review.

A valid cache authorizes operation only until its signed lease expires (normally 15 minutes).
Revocation cannot propagate instantly through a total backend outage. At expiry the prototype
closes sessions rather than extending authorization indefinitely. No fresh state means no
unbounded offline access.

The QUIC-inside-QUIC lab fixes outer UDP MTU at 1400 and inner MTU at 1200. This is suitable
for this Docker test, not proven across arbitrary mobile paths. The path detector is based on
responses during an active download and is not a complete production idle-health algorithm.

[Architecture and security](docs/architecture.en.md) · [Roadmap](docs/roadmap.en.md)
