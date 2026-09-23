[Русская версия →](README.ru.md)

# Family Connect

**Private connectivity for families and devices across borders.**

Family Connect is a private networking project for families and personal devices, with an Android app for an encrypted connection and messaging. It started with a simple need: its developer lives in Europe, while people close to him live in Russia. The goal is to make staying connected easier, without asking family members to learn VPN configurations, servers or protocols.

**[Try the Android beta](docs/getting-started.en.md)** · [Getting started](docs/getting-started.en.md) · [How it works](#how-it-works) · [Security](SECURITY.md) · [Architecture](docs/architecture.md)

## Next client update

Android beta38 and desktop 0.2.10 are being tested on Android, Windows and Linux. Access remains invitation-only: install from the invitation page, then tap **Open app** on that page. The app exchanges the invitation for its own device credentials, without typing or copying an activation key. Device keys remain available for access management and revocation.

Country and protocol selection move into the connection information panel beside the battery display. Navigation stays within the main window, using the Android interface as the shared design reference. These changes are not yet available in the public downloads; see the [verification and release status](docs/releases/2026-09-23-public-client-status.ru.md).

## Platforms

| Platform | Current availability |
| --- | --- |
| Android 8+ | Invite-based beta35; ARM64 APK, 36.4 MB. VPN and text messaging tested on phones. |
| Linux | GTK 4 / libadwaita desktop pilot; 0.2.9 preview146d221d0ad23c07. Operator-assisted setup. |
| Windows x64 | Native desktop pilot; 0.2.9 previewa6c68fe installer. Operator activation; no trusted publisher signature yet. |
| macOS / iOS | No application release. Apple-platform work remains on the longer-term roadmap. |

Features and onboarding differ between platforms. The current friends invitation flow and messenger are available in the Android beta, not the desktop releases.

## A look inside

<img src="docs/assets/android-beta38-home.png" width="300" alt="Family Connect Android beta38 test build home screen, with connection switch, network status and persistent navigation">

Android beta38 test build, Russian interface, captured on 23 September 2026. Actual native UI rendered during device testing; VPN is off in this capture. Public downloads still provide beta35. [Image provenance](docs/assets/README.md).

```mermaid
flowchart LR
    F["Your family"] --- A["Your phone"]
    F --- B["Your laptop"]
    F --- C["A relative's phone"]
```

The idea: make connections manageable for people and their devices. This illustration is not a claim of a shared family dashboard or a direct mesh between devices.

## Why Family Connect?

- **Simple for family members.** On Android, an invitation leads to the APK and an activation code. Activate once, choose a connection and connect. Removing setup friction is the goal; the pilot still needs an invitation and Android permissions.
- **Inspectable development.** Client and server code, test evidence and architecture can be inspected publicly. The project is intended to become an open-source private network; the repository-wide license decision is still pending.
- **Personal device identities.** Device credentials and activation belong to a device. Family members do not need to share a single configuration file.
- **More than one connection option.** The Android friends beta offers AWG and TCP transports and a choice of gateway region. Automatic selection and recovery have separate experimental implementations and are not a cross-platform reliability guarantee.

## Why I built it

I live in Europe, while people close to me live in Russia.

I built Family Connect because I wanted a connection my family could use without learning VPN clients, configuration files, servers or networking. I wanted to configure it once and know that the next connection would be straightforward.

That personal need grew into a project for families and personal devices spread across different countries. Making secure networking approachable remains the reason for building it.

## How it works

1. **Get an invitation** from a participant or the pilot operator.
2. **Install and activate** the Android app with your own invitation code.
3. **Choose a region and connect.** The app connects your device to the selected gateway, which provides Internet access.
4. **Use the messenger** with contacts whose keys you have checked. Messaging is a separate feature; a VPN connection is not itself a chat session.

Participants can share a QR code or invitation link from Settings. The recipient can download the APK and obtain their own activation code on that page; the code is currently pasted into the app manually.

## Project status

Family Connect is under active development. Some platforms and features are experimental. **This is a pilot, not a production-ready service.**

Android VPN connection and two-phone text exchange have been confirmed in the pilot. Incoming messages refresh while the messenger is open; background push, broader device coverage and offline/restart acceptance remain incomplete. Animated smileys are present; their rough edges are a known visual issue.

Desktop releases and Android beta releases have separate versions and capabilities. No app-store release or independent security audit is claimed. [Current state](docs/STATUS.md) takes precedence over dated engineering reports. [Next work](docs/PLAN.md).

## Getting started

**Android:** follow the [installation and invitation guide](docs/getting-started.en.md). Existing users install the new APK over the old version; keep the app and its data. No new invitation is needed for an ordinary update.

**Linux and Windows:** use the [desktop pilot instructions](docs/clients.en.md) and [current preview downloads](docs/releases.md). Desktop onboarding currently requires operator assistance.

**Building from source:** see [development](#development). CI artifacts are test builds, not interchangeable with the signed Android friends APK.

## Security & privacy

Public source helps inspection; it does not establish security on its own. Device key storage, signed configuration verification and release checks are documented with their limits.

- [Security boundaries and reporting status](SECURITY.md)
- [Privacy: local data, gateways and metadata](docs/privacy.md)
- [Desktop update verification and signing](docs/updates.en.md)
- [Android beta artifact and checksum](docs/releases/2026-09-23-public-client-status.ru.md)

A VPN gateway is a trusted part of the connection and can observe destination metadata. Family Connect makes no anonymity or zero-logging guarantee.

## Architecture

```mermaid
flowchart TD
    A["Invitation and entitlement"] --> B["Device registration and identity"]
    B --> C["Provisioning and signed configuration"]
    C --> D["Client verification and protected state"]
    D --> E["Platform VPN adapter"]
    E --> F["Transport and gateway"]
```

This is the implemented provisioning path at a high level; integration maturity differs by platform. The networking code includes WireGuard, AmneziaWG and VLESS REALITY adapters. Reticulum carries control messages in the newer control path. The Rust QUIC relay lab is a separate experiment, not the Android VPN data path.

[Architecture map](docs/architecture.md) · [Device identity](docs/adr/001-identity-provisioning.en.md) · [Provisioning](docs/provisioning-provider.en.md) · [Messenger core](messenger/README.ru.md)

## Development

**Source snapshot:** the public main branch currently predates the distributed Android beta35. The beta features above describe the tested APK; building main does not reproduce that version. Publishing the corresponding source checkpoint is tracked in [PLAN](docs/PLAN.md).

Start with [CONTRIBUTING.md](CONTRIBUTING.md) for setup and scoped checks.

| Area | Source |
| --- | --- |
| Android client | [clients/android](clients/android/) |
| Linux client | [clients/desktop](clients/desktop/) |
| Windows client | [clients/windows](clients/windows/) |
| Registration and provisioning | [control](control/), [device_identity](device_identity/), [provisioning](provisioning/) |
| Messaging | [messenger](messenger/) |
| Experimental relay core | [core](core/) |

## Documentation

The [documentation map](docs/README.md) separates user guides, operator runbooks, development references and project history. Detailed engineering reports remain available.

## Contributing

Bug reports, clearer documentation and scoped patches are welcome. Include the platform and exact version, and remove private data from reports. See [contribution guidance](CONTRIBUTING.md); security-sensitive reports follow [SECURITY.md](SECURITY.md).

## License

A repository-wide license has not yet been selected. Public source availability alone does not grant reuse rights. Third-party components retain their own terms; the classic smiley asset provenance records unresolved redistribution terms. See the [licensing audit](docs/licensing.md) before reuse or redistribution.
