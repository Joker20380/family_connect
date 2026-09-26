# Release distribution / Выпуски

Android0.1.18-beta51, Windows0.2.15 and Linux0.2.11 verified 2026-09-26 by CI, real-device Android acceptance and full GitHub/HTTPS SHA256 downloads.

| Channel | Distributed version | Notes |
| --- | --- | --- |
| Android updater / invitation | 0.1.18-beta51, code51, ARM64 | Persistent beta certificate; in-place update |
| Linux invitation | 0.2.11 AppImage + .deb (+ preview5b02e8cb9fde119f) | User installables; tar.gz stays advanced/manual |
| Windows invitation / updater | 0.2.15 source2ffba77 (+ 0.2.14 compatibility fallback) | Independent signed catalog schema2/sequence11; no publisher signature; 0.2.14 kept for old Windows 10 |

Invitation activation now opens the app from the original link. OFF switches are orange,
ON switches turquoise on the page and all clients. Historical artifacts remain immutable.
Linux user packaging (AppImage + .deb) is built by CI and accepted on clean Ubuntu 24.04;
the invitation page now serves the AppImage as primary Linux download, with `.deb` and the
legacy preview tar.gz as secondary. [Acceptance and publication](linux-appimage-deb.ru.md).

[FamilyConnect-0.2.11-x86_64.AppImage](https://185.251.89.19:8443/downloads/FamilyConnect-0.2.11-x86_64.AppImage), 8559096 bytes.
SHA256 `7dfaca6022a275e62eeac5b8c402477d493d5833181d238f2080aa62014ba83b`.

[FamilyConnect_0.2.11_amd64.deb](https://185.251.89.19:8443/downloads/FamilyConnect_0.2.11_amd64.deb), 6685688 bytes.
SHA256 `a336624808b96de4455963307c609be1d3bddbbadf29976a9a0176207f415697`.

[FamilyConnect-Control-Linux-preview-5b02e8cb9fde119f.tar.gz](https://185.251.89.19:8443/downloads/FamilyConnect-Control-Linux-preview-5b02e8cb9fde119f.tar.gz), 121503 bytes.
SHA256 `6d4c6186fa69d36f4835b380582ba046e1a3a70abf359ee1a0332dd741f97a56`.

[FamilyConnect-Linux-0.2.11-invitation.txt](https://185.251.89.19:8443/downloads/FamilyConnect-Linux-0.2.11-invitation.txt), 3371 bytes.
SHA256 `59fb42f034b86a2fc451f6cb3914ed2e4f19c93805e9348a5bd1676f1b75c279`.

[FamilyConnect-Setup-0.2.15-pilot-unsigned.exe](https://185.251.89.19:8443/downloads/FamilyConnect-Setup-0.2.15-pilot-unsigned.exe), 49941739 bytes.
SHA256 `3e610962da40510e0dce7a9d794f4352ba113e090e462f6d1c75d7712f965e6b`.

[FamilyConnect-Setup-0.2.14-pilot-unsigned.exe](https://185.251.89.19:8443/downloads/FamilyConnect-Setup-0.2.14-pilot-unsigned.exe), 49942347 bytes.
SHA256 `7b1af167a55a977c357c47b94407916fe27d1b343d33ecb69c42b2d11b85e886`.

[FamilyConnect-Test-0.1.18-beta51.apk](https://185.251.89.19:8443/downloads/FamilyConnect-Test-0.1.18-beta51.apk), 36456636 bytes.
SHA256 `79a2d28667332ea442eae1b895b4fc632b52734cbed1e75bd95f32b7175ad366`.

[Discovery](https://185.251.89.19:8443/updates/android-friends.json) · [Android/Windows/Linux checks](releases/2026-09-26-server-list-crossplatform.ru.md) · [Windows0.2.14 checks](releases/2026-09-24-windows0214-installer.ru.md).

## Release procedure

The [client workflow](../.github/workflows/clients.yml) defines platform builds and
release conditions. CI artifacts do not by themselves establish a release. Validate native
UI/runtime and downloaded artifacts before signing/publishing. Windows cross-build alone
is insufficient. The current release includes Android0.1.18-beta51, Linux0.2.11 and Windows0.2.15 Windows-channel release; see the [cross-platform report](releases/2026-09-26-server-list-crossplatform.ru.md) and the prior [Windows0.2.14 report](releases/2026-09-24-windows0214-installer.ru.md).

Desktop catalogs use offline signing with increasing sequence numbers. Keep keys out of
CI and servers; never replace an existing version/tag with different binaries.
[Signing and rollback](updates.en.md). Android uses its persistent beta signing key,
immutable HTTPS APKs and discovery metadata. It is not a Play or GitHub APK release.
For rollback, restore previous metadata/routes from the release backup, retain immutable
artifacts and device data. Publish fixes using a new versionCode.

<a id="documentation-with-every-version"></a>
## Documentation with every version

Required by the project owner,23 September2026. Every version change includes documentation
in the same task, even when a build is only a candidate or installed on one device.

1. Update STATUS and PLAN with built, installed, public and invitation-page versions.
2. Add/update the dated report: source/build identity, package/ABI/version, artifact size,
   SHA256/signing identity, checks performed, known gaps, rollout and rollback.
3. For public distribution changes, update both READMEs, RU/EN getting-started/client
   guides, this page and applicable screenshots/captions. Check invitation-page links
   and record discrepancies explicitly; never claim rollout from a local build alone.
4. Check local links/anchors and images with `python3 scripts/check_public_docs.py --all`,
   run `git diff --check`, verify live URLs and APK hashes, then publish the documentation
   and verify the resulting GitHub revision. Preserve dated evidence as history.

[Documentation map](README.md) · [Working plan](PLAN.md).

Windows0.2.13+ uses [updates/windows.json](../updates/windows.json), signed offline with `scripts/sign_update.py --platform windows`. Each Windows version must include this catalog with an increasing sequence. The legacy shared catalog remains0.2.9/sequence8 for older desktop clients.
