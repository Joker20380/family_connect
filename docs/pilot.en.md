# Russian VPN: Android and Linux pilot

[Русский](pilot.ru.md) · [Guide](../README.en.md)

The current test direction is you in Europe → controlled gateway in Russia → Internet.
Server: `185.251.89.19`, UDP port `51820`. This is a separate direct WireGuard pilot, not the
finished Family Connect application or proof of an adaptive multipath VPN.

## Keys and configurations

Client private keys are generated on your Linux computer, not on the gateway. Android and Linux
have different keys and addresses so both can connect simultaneously. Only their public keys
are uploaded to the server. The prepared Android key must be transferred with its configuration
to the phone; this is manual pilot provisioning, not the future Android Keystore flow.

Local files are in the separate project's `state-v2/pilot-clients/`:

- `fc-ru-android.conf` — Android;
- `fc-ru-linux.conf` — Linux laptop.

They contain private keys, have mode 0600, and are excluded from Git. Transfer the Android file
through a trusted method such as USB; never publish it or upload it to an online QR generator.
Neither these configurations nor the client private keys are present on the server.

## Android

1. Install the official [WireGuard app](https://www.wireguard.com/install/).
2. Transfer `fc-ru-android.conf` to the phone.
3. Tap “+”, import the configuration from a file, and enable the tunnel.
4. Allow the VPN connection. Verify your external IPv4: expected `185.251.89.19`.

For no-bypass mode, use Android's system “Always-on VPN” and “Block connections without VPN”
settings where supported by your OS version. Enable these on the phone; the server cannot
turn them on for you.

## Linux

Install WireGuard tools from your distribution's packages:
[official installation instructions](https://www.wireguard.com/install/).

With NetworkManager, import through network settings or the CLI:

```sh
sudo nmcli connection import type wireguard file /path/to/fc-ru-linux.conf
sudo nmcli connection up fc-ru-linux
```

Alternatively use `wg-quick` (the DNS field requires compatible resolvconf support):

```sh
sudo wg-quick up /path/to/fc-ru-linux.conf
sudo wg-quick down /path/to/fc-ru-linux.conf
```

Disconnect NetworkManager with `sudo nmcli connection down fc-ru-linux`.
Preparing these files does not automatically change your laptop's routes or DNS.

## Traffic behavior

- All IPv4 is routed through the tunnel; default DNS is `1.1.1.1`, reached through the VPN.
- IPv6 is also routed into the tunnel, but IPv6 egress is currently blocked at the gateway.
  This prevents direct IPv6 egress while the full tunnel is active; IPv6-only sites are unsupported.
- Access from the VPN to the gateway's private networks and TCP/25 is blocked. Arbitrary public
  IPv4 connections are allowed only at the controlled gateway; home relays are not involved.
- Manually disabling the VPN restores ordinary Internet access. These files do not install a
  permanent OS kill switch. Android/NetworkManager behavior still needs testing on your devices,
  including DNS/IPv6 handling and Wi-Fi/LTE transitions.
- A Russian IP does not guarantee access to every Russian service: sites use their own geography
  databases, may block datacenter addresses, or impose additional requirements.
- Direct WireGuard may be unavailable on some networks. These profiles do not yet fall back
  automatically to relays.

## Operator notes

The separate Compose project `family-connect-pilot` uses `compose.pilot.yaml`.
It does not replace the mTLS laboratory or its catalog. Revocation through `scripts/admin.py`
applies to mTLS; a WireGuard peer must be removed from gateway peer configuration separately.

```sh
docker compose -f compose.pilot.yaml up -d --build
docker compose -f compose.pilot.yaml exec gateway wg show wg0
```

The server key is `state-v2/wireguard/server.key`; client public keys are `android.pub` and
`linux.pub`. Run `scripts/create_pilot_clients.py` locally, not on the gateway for real users.
NAT and packet filtering operate inside the gateway container. This is a two-device pilot,
without billing, automatic key rotation, dynamic enrollment or complete anti-abuse operations.
