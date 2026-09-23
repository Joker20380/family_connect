# Release distribution / Выпуски

Verified 2026-09-23 by downloading every new public artifact and checking its SHA256.

| Channel | Distributed version | Notes |
| --- | --- | --- |
| Android updater / invitation | 0.1.18-beta50, code50, ARM64 | Persistent beta certificate; in-place update |
| Linux invitation | 0.2.10 preview8e9fabe3cbef2989 | Paired manual preview; operator-assisted setup |
| Windows invitation | 0.2.11 preview8906d62 | Native tested installer; no publisher signature |

Invitation activation now opens the app from the original link. OFF switches are orange,
ON switches turquoise on the page and all clients. Historical artifacts remain immutable.

[FamilyConnect-Control-Linux-preview-8e9fabe3cbef2989.tar.gz](https://185.251.89.19:8443/downloads/FamilyConnect-Control-Linux-preview-8e9fabe3cbef2989.tar.gz), 120093 bytes.
SHA256 `67b569cb2423692f088baa7ef0d83761394bec4fadb38249ac0788a046605795`.

[FamilyConnect-Linux-0.2.10-invitation.txt](https://185.251.89.19:8443/downloads/FamilyConnect-Linux-0.2.10-invitation.txt), 3371 bytes.
SHA256 `2d1e0578767c3e0258f9214c080363cbc54c04944cea91e6b5f704393ba8c5bd`.

[FamilyConnect-Setup-0.2.11-preview-8906d62.exe](https://185.251.89.19:8443/downloads/FamilyConnect-Setup-0.2.11-preview-8906d62.exe), 49934207 bytes.
SHA256 `9cc04ba7446ff31d87e2a3d96dfb7faf24e61cf81a7eac8eccea0adb29c3ed3c`.

[FamilyConnect-Test-0.1.18-beta50.apk](https://185.251.89.19:8443/downloads/FamilyConnect-Test-0.1.18-beta50.apk), 36448332 bytes.
SHA256 `8a1d44eac8cdd45bb9225e930c71377ea5b38428238300803fecc42a60761369`.

[Discovery](https://185.251.89.19:8443/updates/android-friends.json) · [Windows checks and rollback](releases/2026-09-23-windows0211-dpi.ru.md) · [Android/Linux checks](releases/2026-09-23-switch-colors-beta50.ru.md).

## Release procedure

The [client workflow](../.github/workflows/clients.yml) defines platform builds and
release conditions. CI artifacts do not by themselves establish a release. Validate native
UI/runtime and downloaded artifacts before signing/publishing. Windows cross-build alone
is insufficient. The current release includes Android beta50 and Linux0.2.10 and Windows0.2.11 manual previews; see the [Windows report](releases/2026-09-23-windows0211-dpi.ru.md) and [Android/Linux report](releases/2026-09-23-switch-colors-beta50.ru.md).

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
