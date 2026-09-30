[Русская версия →](README.ru.md)

# Family Connect

**Resilient connectivity for families and personal devices.**

Family Connect helps people stay connected without having to understand which
transport or server works today. It is not a protocol picker or just another VPN:
connection continuity and automatic recovery are the product direction. Fast,
inexpensive VPN transports remain the normal path; a restricted service carrier
is a fallback, not the default.

The initial target is a technically capable family member helping relatives and
devices stay connected without repeatedly explaining configurations. Families
split across countries, including people with relatives in Russia, are a common
starting context—not a limit to the product's geography.

**[Try the Android beta](docs/getting-started.en.md)** · [Desktop installation](docs/clients.en.md) · [How it works](#how-it-works) · [Security](SECURITY.md)

## Current usable beta — implemented

Device Identity, Family admission, invitations and provisioning exist. Beta users
already use normal AWG/TCP connectivity; Android already has a VpnService/VPN
lifecycle. Automatic orchestration across normal and restricted transports is
**not product-complete**. Current clients still expose region/transport choices.

| Platform | Latest documented distribution and limits |
| --- | --- |
| Android 8+ / ARM64 | **0.1.18-beta51 / code51**; invitation activation, normal VPN, text/voice messaging and background notifications tested on phones. |
| Linux | **0.2.11**, GTK 4/libadwaita; AppImage and DEB, legacy archive retained for advanced/manual use and updater compatibility. System dependencies and VPN helpers still require setup. |
| Windows 10 1809+ / 11 x64 | **0.2.15**; invitation activation, independent signed update catalog; installer has no trusted publisher signature. 0.2.14 remains a compatibility fallback; affected Windows 10 device acceptance is pending. |
| macOS / iOS | No client release; iOS is later work, after real beta evidence. |

These are the last documented public/invitation versions, not a new artifact or
installed-device audit. See [versions and checksums](docs/releases.md),
[cross-platform release evidence](docs/releases/2026-09-26-server-list-crossplatform.ru.md)
and [Linux packaging](docs/linux-appimage-deb.ru.md). Windows 0.2.12 and earlier
need one manual transition before using the independent update catalog.

Desktop feature parity with Android messaging is not claimed. Android screen-off
notifications were confirmed; deep Doze latency and broader offline/restart
acceptance remain open. This remains a pilot, not a production-ready service.

## Restricted-network R&D — proven experimental

Isolated engineering acceptance passed on a **physical Redmi Android → real
Telemost VP8/RTP carrier → Amsterdam EU gateway → TCP/DNS Internet** path:

- Family TLS 1.3 authentication over a selective-repeat ReliableStream, real RTP
  gap recovery and long-duration reliable goodput.
- Multiple simultaneous public HTTPS streams with verified end-site TLS, mixed
  TCP + Family DNS workload, exact byte delivery, fair scheduling and bounded buffers.
- Destination DNS containment/hardening in the tested core path.
- Automatic Room Broker using the official Telemost API with server-side OAuth
  only: Amsterdam joins first and reports READY; Android receives the dedicated
  descriptor and joins without an operator-supplied room URL.

[5N.5 acceptance](docs/releases/2026-09-28-webrtc-eu5-mux-dns.ru.md) ·
[Room Broker PASS](docs/releases/2026-09-28-webrtc-5n-room-broker.ru.md) ·
[Reliability and sustained goodput](docs/releases/2026-09-27-webrtc-5n-perf2-reliable-envelope.ru.md)

**This is not yet the released whole-device restricted Android VPN.** The accepted
Room Broker run used temporary control ingress (SSH forwarding + adb reverse),
not production restricted-network bootstrap. If the ordinary Family API is
unreachable, the device cannot yet independently obtain its first dedicated room.
5N.6 full-device integration and Krasnodar FIELD-1 have not run; restricted mode
has not been rolled out to existing beta users. There is no generic UDP support
in this path; global ReliableStream head-of-line blocking remains, and no
production capacity or universal allowlist availability is claimed.

In one user-reported Krasnodar cellular restricted/allowlist condition, Family
AWG 3.1 and TCP were unavailable while Telemost communication remained available.
This is one field observation—not a claim about every network, operator, region
or time, and not a Family restricted-VPN field acceptance.

## How it works

**Target experience (planned across transports):**

```text
INSTALL → accept family invitation → CONNECT
        → Family Connect selects/recovers an available path → CONNECTED
```

The normal user-facing states should be **CONNECTING**, **CONNECTED** and
**RESTORING CONNECTION**; protocol details belong in advanced diagnostics.
The mental model is **Family → people/devices → connectivity**, not account →
server → configuration file. A shared family dashboard is not implemented by
this diagram or claimed here.

**Today:** obtain an invitation, install the client, return to the original link
and open the application to activate it. Accept Android VPN permissions and use
the current region/connection controls. Fresh sideload installation still needs
the return to the invitation; end-to-end automatic activation is not claimed.
Messaging is a separate feature, not a consequence of connecting the VPN.

**Next:** restricted bootstrap (`5N-BOOT-1`) → Android full-device integration
(`5N.6`) → minimum viable Connectivity Orchestrator → Krasnodar FIELD-1 →
50–100-user product beta. [Authoritative roadmap](docs/PLAN.md).

## Security & privacy

Third-party carriers are untrusted. The restricted path's security boundary is
**Device Identity / Family admission / Family TLS**, not Telemost room secrecy.
Telemost is the first proven restricted carrier, not the product or a permanent
architectural dependency; carriers remain replaceable adapters.

The gateway is trusted and can observe destination metadata. No anonymity,
zero-logging, guaranteed bypass or guaranteed availability is promised. Future
connection-success metrics must not collect traffic content or browsing history;
they are planned, not presented as an existing telemetry system.

[Security boundaries](SECURITY.md) · [Privacy](docs/privacy.md) ·
[Update verification](docs/updates.en.md)

## Architecture

The architecture distinguishes the **control/product plane**, the missing
**restricted bootstrap/recovery plane**, and the proven experimental **data
plane**. A planned Connectivity Orchestrator selects among available capabilities;
normal AWG/TCP paths do not run through the experimental 5N mux.

[Architecture and product decisions](docs/architecture.md) ·
[Device Identity](docs/adr/001-identity-provisioning.en.md) ·
[Provisioning](docs/provisioning-provider.en.md) · [Current state](docs/STATUS.md)

## Development

Start with [CONTRIBUTING.md](CONTRIBUTING.md) and the [documentation map](docs/README.md).
Source, CI builds, installed clients and public artifacts are separate states;
CI test signing does not reproduce the distributed friends APK. The current main
CI has open failures documented in STATUS; repository synchronization is not a
release or a deployment.

| Area | Source |
| --- | --- |
| Android / Linux / Windows | [Android](clients/android/) / [Linux](clients/desktop/) / [Windows](clients/windows/) |
| Identity and provisioning | [control](control/) / [device_identity](device_identity/) / [provisioning](provisioning/) |
| Experimental restricted core / Room Broker | [carrier](carrier/) / [roombroker](carrier/roombroker/) |
| Messaging / separate QUIC relay lab | [messenger](messenger/) / [core](core/) |

## Contributing

Bug reports, documentation and scoped patches are welcome. Include platform and
exact version, and remove private data. Follow [contribution guidance](CONTRIBUTING.md)
and [security reporting](SECURITY.md).

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
