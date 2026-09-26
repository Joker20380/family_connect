[Русская версия →](README.ru.md)

**Stage5 priority update:** Android → Telemost VP8 → Linux EU Gateway → Internet.
Reticulum control/recovery remains; Windows Home Gateway is a secondary feature.
Preparation only: Family encrypted binary/TCP/DNS/full-device transport is not yet
implemented or validated. [Current plan and WEBRTC-EU gates](docs/PLAN.md).
Earlier Home Gateway notes below describe retained future functionality.

WebRTC underlay preparation: Reticulum frames may travel through an isolated
WB/Telemost/VK carrier as an alternative to direct paths. Telemost is now the first
candidate after a reported cellular video call from Krasnodar to Belgium; WB is
the reserve. Headless/binary/RNS carrier and Android↔Windows acceptance remain open. [Updated Stage5 plan](docs/PLAN.md).

## Personal/Home Gateway — active development

Stage 5 targets a secure Android↔Windows Home PC connection under mobile
allowlist restrictions. Reticulum handles discovery and connection negotiation;
IP traffic uses a selected encrypted transport, direct or through a relay, then
diagnostic Internet or the existing Family Connect VPN. Stable Device Identity, no per-user DDNS or manual key transfer. Experimental,
not yet implemented; real Android↔Windows RNS-2 acceptance is still required.
[Design and milestones](docs/reticulum/HOME_GATEWAY_DESIGN.md) · [Plan](docs/PLAN.md).

# Family Connect

**Private connectivity for families and devices across borders.**

Family Connect is a private networking project for families and personal devices, with an Android app for an encrypted connection and messaging. It started with a simple need: its developer lives in Europe, while people close to him live in Russia. The goal is to make staying connected easier, without asking family members to learn VPN configurations, servers or protocols.

**[Try the Android beta](docs/getting-started.en.md)** · [Getting started](docs/getting-started.en.md) · [How it works](#how-it-works) · [Security](SECURITY.md) · [Architecture](docs/architecture.md)

## Current release

Android **0.1.18-beta51** is available for existing users: voice messages, hold-to-record,
swipe-up locking, text edits and background notifications. New messages scroll into view. Switches are orange when off and turquoise when on.
[Install or update](docs/getting-started.en.md) · [Versions and checksums](docs/releases.md).

The invitation page provides Android beta51 and Linux0.2.10 / Windows0.2.14 previews. Install
the client, return to the original invitation mark **Application installed** and choose **Open application**.
[Desktop installation](docs/clients.en.md) · [Rollout checks](docs/releases/2026-09-24-windows0214-installer.ru.md).

Windows0.2.14 fixes installer recovery and adjusts app-local CET compatibility for older Windows 10 updates. Windows 10 1809+ / 11 x64 are the target platforms; affected-device acceptance remains pending. Version0.2.13 can update through Check for updates;0.2.12 or earlier needs one manual installation.

## Platforms

| Platform | Current availability |
| --- | --- |
| Android 8+ | Beta51; ARM64 APK, 36.4 MB. VPN, text and voice tested on phones; invitation-link activation. |
| Linux | GTK 4 / libadwaita desktop pilot; 0.2.10 preview8e9fabe3cbef2989. Operator-assisted setup. |
| Windows x64 | Native desktop pilot; 0.2.14 source6eed30c installer. Invitation-link activation; no trusted publisher signature yet. |
| macOS / iOS | No application release. Apple-platform work remains on the longer-term roadmap. |

Invitation-link activation is available on all three clients. Messenger functionality is verified on Android; desktop feature parity is not claimed.

## A look inside

<img src="docs/assets/android-beta38-home.png" width="300" alt="Family Connect Android beta38 test build home screen, with connection switch, network status and persistent navigation">

Android beta38 test build, Russian interface, captured on 23 September 2026. Actual native UI rendered during device testing; VPN is off in this capture. Historical screenshot; the current update is beta51. [Image provenance](docs/assets/README.md).

```mermaid
flowchart LR
    F["Your family"] --- A["Your phone"]
    F --- B["Your laptop"]
    F --- C["A relative's phone"]
```

The idea: make connections manageable for people and their devices. This illustration is not a claim of a shared family dashboard or a direct mesh between devices.

## Why Family Connect?

- **Simple for family members.** An invitation leads to the download and an Open application button. Activate once, choose a connection and connect. Removing setup friction is the goal; the pilot still needs an invitation and Android permissions.
- **Inspectable development.** Client and server code, test evidence and architecture can be inspected publicly. Family Connect is source-available proprietary software; public inspection does not grant reuse rights.
- **Personal device identities.** Device credentials and activation belong to a device. Family members do not need to share a single configuration file.
- **More than one connection option.** The Android friends beta offers AWG and TCP transports and a choice of gateway region. Automatic selection and recovery have separate experimental implementations and are not a cross-platform reliability guarantee.

## Why I built it

I live in Europe, while people close to me live in Russia.

I built Family Connect because I wanted a connection my family could use without learning VPN clients, configuration files, servers or networking. I wanted to configure it once and know that the next connection would be straightforward.

That personal need grew into a project for families and personal devices spread across different countries. Making secure networking approachable remains the reason for building it.

## How it works

1. **Get an invitation** from a participant or the pilot operator.
2. **Install and activate** the app by returning to your original invitation link.
3. **Choose a region and connect.** The app connects your device to the selected gateway, which provides Internet access.
4. **Use the messenger** with contacts whose keys you have checked. Messaging is a separate feature; a VPN connection is not itself a chat session.

Participants can share a QR code or invitation link from Settings. The recipient downloads the app, returns to that same link and opens the app to activate access.

## Project status

Family Connect is under active development. Some platforms and features are experimental. **This is a pilot, not a production-ready service.**

Android VPN, two-phone text/voice exchange and screen-off notifications have been confirmed in the pilot. Background delivery uses the app’s own service, not FCM. Delivery latency during deep Doze, broader device coverage and offline/restart acceptance remain open. Animated smileys are present; their rough edges are a known visual issue.

Desktop releases and Android beta releases have separate versions and capabilities. No app-store release or independent security audit is claimed. [Current state](docs/STATUS.md) takes precedence over dated engineering reports. [Next work](docs/PLAN.md).

## Getting started

**Android:** follow the [installation and invitation guide](docs/getting-started.en.md). Existing users install the new APK over the old version; keep the app and its data. No new invitation is needed for an ordinary update.

**Linux and Windows:** use the [desktop pilot instructions](docs/clients.en.md) and [current preview downloads](docs/releases.md). Linux dependency and VPN-helper setup requires operator assistance.

**Building from source:** see [development](#development). CI artifacts are test builds, not interchangeable with the signed Android friends APK.

## Security & privacy

Public source helps inspection; it does not establish security on its own. Device key storage, signed configuration verification and release checks are documented with their limits.

- [Security boundaries and reporting status](SECURITY.md)
- [Privacy: local data, gateways and metadata](docs/privacy.md)
- [Desktop update verification and signing](docs/updates.en.md)
- [Android beta artifact and checksum](docs/releases/2026-09-26-server-list-crossplatform.ru.md)

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

**Source snapshot:** this checkpoint includes Android0.1.18-beta51 and Linux0.2.11 / Windows0.2.15 candidates; the published desktop versions remain Linux0.2.10 / Windows0.2.14. See [source acceptance](docs/releases/2026-09-23-switch-colors-beta50.ru.md) for checks and limits. CI uses test signing; byte-for-byte reproduction of the published APK is not claimed. Linux remains a manual preview. Windows0.2.14 uses an independent signed catalog after one manual transition.

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

Family Connect is source-available proprietary software. The source repository
being public does not make Family Connect open source. All rights are reserved
except where explicitly stated for third-party components. See [LICENSE](LICENSE),
[Third-Party Notices](THIRD_PARTY_NOTICES.md) and the [license audit](docs/legal/DEPENDENCY_LICENSE_AUDIT.md).
Public visibility grants no general reuse, derivative distribution, resale,
substantial republication or branding permission. Existing third-party rights and
prior valid grants are preserved. Classic smiley redistribution rights remain unresolved.

Family Connect — проприетарное ПО с публично доступными исходниками (source-available).
Публичный репозиторий не делает Family Connect open source. Все права сохранены,
кроме явно установленных условий сторонних компонентов. См. [LICENSE](LICENSE),
[Third-Party Notices](THIRD_PARTY_NOTICES.md) и [аудит](docs/legal/DEPENDENCY_LICENSE_AUDIT.md).
Публичность не разрешает использование кода в другом продукте, распространение
производных, продажу копий, перепубликацию существенных частей или использование
бренда. Права третьих лиц и ранее выданные разрешения сохраняются. Права на
распространение классических смайликов остаются неустановленными.
