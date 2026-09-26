# Family Connect

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

The canonical English introduction is [README.md](README.md).

[Русская версия](README.ru.md) · [Documentation](docs/README.md)

This compatibility page keeps existing links working. Product information is maintained
in README.md and README.ru.md only; update both together as described in
[CONTRIBUTING.md](CONTRIBUTING.md#documentation-and-languages).

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
