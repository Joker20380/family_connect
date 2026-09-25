# Third-party notices

Family Connect's [proprietary source-available LICENSE](LICENSE) covers only
original material owned by the project rights holder. It does not relicense any
component below. Preserve upstream license texts, copyright notices and applicable
source/redistribution obligations in packaged artifacts. This inventory is not a
claim that every historical artifact has passed a complete license audit.

## Reticulum and Home Gateway

| Component | Actual use | License / notice | Integration |
| --- | --- | --- | --- |
| [Reticulum reference implementation](https://github.com/markqvist/Reticulum), Python `rns==1.5.1` | Existing Device Identity/control and Android dependency; selected for future Home Gateway adapter | Reticulum License; packaged notice: Copyright (c) 2016-2025 Mark Qvist. [Full retained text](clients/android/app/src/main/assets/control-licenses/Reticulum.txt) | Dependency; bundled with Android; proposed private Windows worker, not yet implemented. No upstream source modification introduced here. |
| [rns-vpn-rs](https://github.com/BeechatNetworkSystemsLtd/rns-vpn-rs), upstream package 0.1.0 | Research/PoC reference only | [MIT](https://github.com/BeechatNetworkSystemsLtd/rns-vpn-rs/blob/master/LICENSE), Copyright (c) 2025 Beechat Network Systems Ltd. | Not a dependency, bundled or modified; no portions/files copied. Record exact revision/files and preserve full MIT notice if this changes. |

Reticulum Protocol's public-domain designation does not license the Python
implementation as public domain. The Reticulum License is not Family Connect's
license and is not MIT: it includes use restrictions. See the
[audit and integration decision](docs/legal/DEPENDENCY_LICENSE_AUDIT.md).

## Existing packaged components and retained notices

| Component | License / provenance | Existing notice or packaging record |
| --- | --- | --- |
| LXMF 1.1.1, Mark Qvist | Reticulum License | [LXMF.txt](clients/android/app/src/main/assets/control-licenses/LXMF.txt), Android `chat-python.gradle` |
| Chaquopy, Chaquo Ltd and contributors | MIT; runtime dependencies retain separate terms | [Chaquopy.txt](clients/android/app/src/main/assets/control-licenses/Chaquopy.txt) |
| pyserial 3.5, Chris Liechti | BSD-3-Clause | [PySerial.txt](clients/android/app/src/main/assets/control-licenses/PySerial.txt) |
| Bouncy Castle: Android 1.85.2 / Windows 2.7.0 | MIT, respective Bouncy Castle copyright holders | [Android text](clients/android/app/src/main/assets/control-licenses/BouncyCastle.txt), [Windows record](clients/windows/THIRD-PARTY.md) |
| Gson 2.13.2, ZXing core 3.5.3 | Apache-2.0 | [Gson](clients/android/app/src/main/assets/control-licenses/Gson.txt), [ZXing](clients/android/app/src/main/assets/control-licenses/ZXing.txt) |
| WireGuard Windows v1.0.1; WireGuardNT 1.1 SDK | Preserve exact `COPYING`/SDK license; distribution audit remains open, do not infer identical terms for all WireGuard projects | [Windows inventory](clients/windows/THIRD-PARTY.md), `clients/windows/build.ps1` copies original texts |
| Wintun 0.14.1 | Official prebuilt SDK's distribution terms, distinct from source licensing; verify exact artifact notice before new bundling | `pilot/windows-tcp/build.ps1` and `pilot/windows-awg/build.ps1` copy SDK `LICENSE.txt` |
| Xray-core, d2758a023cd7f4174a5a5fa4ff66e487d4342ba0 in Windows record | MPL-2.0; file-level obligations remain applicable | [Retained Xray license](pilot/tcp/LICENSE-Xray), [Windows record](clients/windows/THIRD-PARTY.md) |
| amneziawg-go 3.1, b5928efb6ca19f0153958460c3d141f04abc5c2e in Windows record | MIT, upstream contributors; existing local TUN startup patch | [Windows record](clients/windows/THIRD-PARTY.md); `awg/licenses` in package |
| .NET runtime | MIT, Microsoft and contributors | [Windows record](clients/windows/THIRD-PARTY.md); bundled runtime notices |
| Natural Earth land data | Public domain; derived polygon data | [Land notice](clients/assets/land-NOTICE.txt), [Android maps notice](clients/android/app/src/main/assets/maps/NOTICE.txt) |
| Classic ICQ smiley assets | Redistribution rights unresolved; excluded from claims of project ownership | [Provenance](clients/android/app/src/main/assets/chat/icq-classic/provenance.json); existing beta contains assets, replacement previously deferred |

Server/Python, AndroidX, Go transitive libraries, Python runtime/cryptography,
platform SDKs and complete shipped-artifact inventories still require their full
version-specific transitive audit. The list above is an entry-point inventory,
not a blanket compatibility certification. No new dependency is introduced by
the 2026-09-25 documentation/licensing change.

## Application access

Required future navigation: **Settings → Legal → Third-Party Notices**. Package
this index together with complete version-specific notices, accessible offline,
and verify presence in APK/installer acceptance. This change documents that path;
it does not add the UI or assert it is already available. Do not replace full
license texts with links alone in redistributed packages.

## WebRTC carrier references — 2026-09-25

No WebRTC source or dependency is included in this preparation-only checkpoint.

| Reference | License / revision | Integration / portions used |
| --- | --- | --- |
| [kulikov0/whitelist-bypass](https://github.com/kulikov0/whitelist-bypass/tree/7c19a7ec40900940fe0c43ea1db7768ee632393d) | MIT; `Copyright (c) 2026`; revision `7c19a7ec40900940fe0c43ea1db7768ee632393d` | Research only: WB/Telemost auth, LiveKit signaling, headless Pion, DC/VP8. No copied, modified, linked or bundled files. |
| [openlibrecommunity/olcrtc](https://github.com/openlibrecommunity/olcrtc/tree/92b2332769c3dd5000584366201572efc448065f) | WTFPL v2; Copyright (C) 2026 zarazaex; revision `92b2332769c3dd5000584366201572efc448065f` | Research only: provider/auth/transport split and reconnect. No copied, modified, linked or bundled files. |

Exact inspected paths, license sources and candidate-dependency blockers are in
[the audit](docs/legal/DEPENDENCY_LICENSE_AUDIT.md#webrtc-carrier-reference-audit--preparation-only-2026-09-25).
Any later MIT source reuse must retain the full original notice and identify
source/destination files. No implied license for forks/transitive dependencies.
