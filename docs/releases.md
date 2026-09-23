# Release distribution / Выпуски

Verified 2026-09-23 against public HTTPS discovery and the invitation page.

| Channel | Distributed version | Notes |
| --- | --- | --- |
| Android updater / direct APK | 0.1.18-beta49, code49, ARM64 | Existing activation preserved; user confirms installation |
| Android first-activation page | beta35 | Code activation, then update in place to49 |
| Linux invitation download | 0.2.9 preview146d221d0ad23c07 | Paired GTK archive, operator-assisted setup |
| Windows invitation download | 0.2.9 previewa6c68fe | x64 preview, publisher signing/physical acceptance open |
| Original desktop GitHub release | v0.2.9 | Separate older assets; not Android feature parity |

[Android guide EN](getting-started.en.md) / [RU](getting-started.ru.md) ·
[Desktop EN](clients.en.md) / [RU](clients.ru.md).

[APK49](https://185.251.89.19:8443/downloads/FamilyConnect-Test-0.1.18-beta49.apk),
36448332 bytes. SHA256 `3a37613a63c130af97c853d1c39836c026822dca717a748fa005a3211f8f549d`.
[Discovery](https://185.251.89.19:8443/updates/android-friends.json) ·
[Checks, certificate and rollback](releases/2026-09-23-voice-scroll-beta49.ru.md).
Beta48 was tested locally and never published. Historical reports retain their original
versions; use this page and STATUS for current downloads.

## Release procedure

The [client workflow](../.github/workflows/clients.yml) defines platform builds and
release conditions. CI artifacts do not by themselves establish a release. Validate native
UI/runtime and downloaded artifacts before signing/publishing. Windows cross-build alone
is insufficient. The current source checkpoint includes Android beta49 and
the desktop0.2.10 candidate; see the [source report](releases/2026-09-23-source-checkpoint.ru.md). Desktop0.2.10 and the new invitation page are not distributed.

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
