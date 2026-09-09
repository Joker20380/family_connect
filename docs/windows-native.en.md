# Windows 0.2: standalone client

## Status

The new client replaces the Python/Tk Windows wrapper. A single installer includes the application, .NET runtime, Family Connect service, embedded WireGuard tunnel library and official signed WireGuardNT driver. Users need no separate installations. This build targets Windows x64; a separate ARM64 build has not been validated.

This is a direct Russian-gateway pilot. Adaptive routing, family subscriptions and online invitations are not integrated. A trusted Family Connect publisher certificate is not available yet: `pilot-unsigned` is not a signed commercial release. Do not disable antivirus or add exclusions to install the pilot. If Windows blocks a file, retain its detection name, path and SHA256 for investigation.

## First connection

1. Install Family Connect. The installer needs administrator permission; the regular interface does not.
2. Select “1. Get device code”. The app generates a unique key on this computer. Send the code to the operator: it contains only the public key.
3. The operator registers this device on the gateway and issues `device.fcactivation`.
4. Select “2. Open activation file”. Activation is bound to this device key and valid for import for 24 hours.
5. Select Connect. Verify access to the sites you need: a running tunnel service does not prove Internet connectivity.

No manual IP, DNS or key entry is required. Linux used a previously configured profile; Windows receives its own key and address. Do not copy the Linux profile. Activation contains no private key and cannot activate another device. An accepted activation works offline; the import deadline is not a subscription expiry. Revocation currently requires removing the gateway peer; commercial revocation is not implemented.

## Isolation and storage

The LocalSystem broker creates a separate key per Windows account. Keys are protected with the service account's current-user DPAPI (SYSTEM) under `%ProgramData%\FamilyConnect`, restricted to SYSTEM/Administrators. The private key never reaches the UI, operator or server. A named pipe allows local authenticated clients, denies network clients, and binds each request to the caller's Windows SID. Its privileged API accepts only status/request/activate/connect/disconnect, never commands, arbitrary paths or raw configurations.

Only one tunnel runs at a time. Another Windows account cannot replace an active tunnel belonging to someone else. System administrators remain trusted. Tunnel configurations are also DPAPI encrypted; plaintext configuration is not saved on disk. The application does not log browsing history or traffic contents. WireGuard diagnostics may contain technical tunnel information in system logs; this is not a promise of zero technical logging.

Closing the UI keeps the VPN running; stopping the broker or uninstalling disconnects it. Tunnel autoconnect after reboot is disabled. Uninstall preserves protected device data for reinstall; an administrator may delete `%ProgramData%\FamilyConnect` to erase keys, which requires a new activation. This version does not guarantee a kill switch when the service stops.

## Operator enrollment

The activation signing key stays outside Git in `state-client-build/activation/signing.key`; only `clients/windows/activation.pub` is bundled. This is distinct from the Windows Authenticode publisher certificate.

On the trusted operator machine:

```sh
python3 scripts/activate_windows.py \
  --key state-client-build/activation/signing.key \
  --request FC1_PUBLIC_DEVICE_CODE \
  --number 4 --gateway-public BASE64_GATEWAY_PUBLIC_KEY \
  --output state-enroll/windows-device-4
```

Choose a free address from 4–254. Before delivering activation, register `peer.json` on the controlled gateway:

```sh
python3 scripts/register_pilot_peer.py \
  --peer /secure/path/peer.json \
  --keys /actual/project/state-v2/wireguard \
  --container ACTUAL_GATEWAY_CONTAINER
```

Registration checks address/key conflicts, persists the public peer and adds it without restarting existing tunnels. It requires the updated `pilot/gateway.sh` that loads `peers/*.conf` at startup. Upgrade an older gateway image separately in an agreed maintenance window: replacing its container interrupts sessions. The application and build do not deploy anything to servers. Server `186.246.51.201` is excluded from the VPN infrastructure.

## Building and trusted signing

Build-machine requirements: .NET SDK 10, Git and Inno Setup 6. VPN dependencies come from official sources with pinned version and SHA256 checks. These are developer requirements, not user dependencies.

```powershell
./clients/windows/build.ps1
# Only after obtaining a publisher certificate in the Windows certificate store:
./clients/windows/build.ps1 -SignedRelease -SigningThumbprint CERTIFICATE_THUMBPRINT
```

The certificate key must be available to SignTool through the supported hardware/cloud provider. Do not put private keys or passwords in chat or Git. The script signs the application EXE/DLL, tunnel.dll, installer and uninstaller, verifying Authenticode trust and the expected certificate. The official driver retains WireGuard's signature. `-SignedRelease` fails without a certificate; it never substitutes a self-signed certificate.

Obtaining a certificate requires publisher registration and verification with a signing provider. A trusted signature still does not guarantee absence of SmartScreen/antivirus warnings: clean-Windows testing, Defender scans, investigation of specific detections and reputation are necessary. Do not alter builds to evade detection or disable protection.
