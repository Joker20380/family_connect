# Release distribution / Выпуски

Android0.1.18-beta62/code62 is a [local source-only diagnostic candidate](releases/2026-10-04-beta62-recovery-candidate.md),
not built/signed/installed/published. Installed owner baseline and targeted download
remain61 r2; default Android distribution remains60. No62 download/hash claimed.

Android0.1.18-beta60 published 2026-10-03 after hosted CI, owner in-place acceptance and public HTTPS SHA256/signer verification. Windows0.2.15 and Linux0.2.11 distribution remains unchanged.

| Channel | Distributed version | Notes |
| --- | --- | --- |
| Android updater / invitation | 0.1.18-beta60, code60, ARM64 | Same beta certificate; optional update; minimum1; FIELD admission separate |
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

[FamilyConnect-Test-0.1.18-beta60.apk](https://185.251.89.19:8443/downloads/FamilyConnect-Test-0.1.18-beta60.apk), 49412987 bytes.
SHA256 `8ee59352e5f490aea74c3c8c8aeefd0d65bec0c261a044899d512ca376cf6104`.
Signer SHA256 `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
Build source `5c740f2d05f725ee1bcbe63a41f886605d4c7ac4`; no publication rebuild or APK resigning.
[Signed Android catalog](https://185.251.89.19:8443/updates/android-friends-v2.json)
uses android-field/schema1/sequence1, minimum1, mandatory_after0; expires2027-01-01 13:34:01UTC.
Renew before expiry with a higher sequence and the existing offline root. beta59 remains unpublished.
[FIELD publication evidence](releases/2026-10-03-field1-release-final.md#beta60-publication--2026-10-03).

[Discovery](https://185.251.89.19:8443/updates/android-friends.json) · [Android/Windows/Linux checks](releases/2026-09-26-server-list-crossplatform.ru.md) · [Windows0.2.14 checks](releases/2026-09-24-windows0214-installer.ru.md).

## Targeted diagnostic download — not production

[Android beta61 r2 diagnostic](https://185.251.89.19:8443/downloads/FamilyConnect-Test-0.1.18-beta61-r2.apk),
published separately04.10.2026 for existing tester FC-YHQB-9VJN. Version/code
`0.1.18-beta61`/61,49654651bytes; same already accepted APK, no rebuild/resign.
Downloaded SHA256 `4297ea1a7124f048bdfca4889e89114e84465fab3100a3caea7cbe23cd5e35fb`;
signer SHA256 `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
HTTP200/readback PASS. Beta60 remains default/production and both update catalogs
remain60; landing, desktop downloads and FIELD admission unchanged. No GitHub Release.
Install over60 without uninstall/data clear/new invitation; the original disconnect
is not claimed fixed. [Evidence and rollback](releases/2026-10-04-beta61-r2-direct-delivery.md).

## Release procedure

### Release-test fixture prerequisite

Full Python release tests require closed HTTP, sync and readiness artifacts, their
SHA256 pins, the immutable historical HTTP fixture, Go1.26.0 and nginx. Use the same
provisioner in hosted phase0/Linux-control and Docker; do not substitute production
state or skip tests when fixtures are absent. From a committed checkout with full
history, install the two Python lockfiles, Go1.26.0, nginx, iproute2 and keepassxc:

```sh
(cd carrier && go mod download)
python scripts/ci_release_fixtures.py prepare --output /tmp/fc-release-fixtures --go "$(command -v go)"
python scripts/ci_release_fixtures.py run --fixtures /tmp/fc-release-fixtures --go "$(command -v go)" --nginx /usr/sbin/nginx -- python -m pytest -q
```

Use a fresh output directory for each source commit. Inventory hashes and HEAD are
checked before test execution. The historical regression retains its independent
immutable pin; current readiness tests receive the current source artifact explicitly.
Before `docker compose build`, run
`python scripts/ci_release_fixtures.py export --output .ci-release-source`.
This exports only committed public source and the pinned historical source, never
host Git configuration, ignored state, device credentials or signing keys. Docker's
test stage restores and checks the exact source tree/commit for clean-export tests,
then provisions artifacts before collection. The runtime stage does not inherit
test artifacts, Go, Git metadata or synthetic device state. Remove/regenerate this
ignored export directory after changing the committed source.

Docker first runs the real root-DAC publication tests with `setpriv` and
`/usr/bin/python3`, then runs full pytest as an unprivileged runner like hosted CI.
This keeps nginx's synthetic static files readable by the same test identity without
relaxing private fixture permissions. `curl` is also required by the desktop tests.
The operator ZIP includes explicit namespace-directory entries for Python3.13;
Python3.14's implicit-directory imports must not hide a broken isolated archive.

The [client workflow](../.github/workflows/clients.yml) defines platform builds and
release conditions. CI artifacts do not by themselves establish a release. Validate native
UI/runtime and downloaded artifacts before signing/publishing. Windows cross-build alone
is insufficient. The current release includes Android0.1.18-beta60, Linux0.2.11 and Windows0.2.15 Windows-channel release; see the [FIELD report](releases/2026-10-03-field1-release-final.md), [desktop cross-platform report](releases/2026-09-26-server-list-crossplatform.ru.md) and prior [Windows0.2.14 report](releases/2026-09-24-windows0214-installer.ru.md).

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
