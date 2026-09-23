# Release distribution

Updated 2026-09-23; published APK and invitation-page links checked. Beta38 is a device-tested candidate, not a public download.

| Channel | Latest relevant distribution | Limits |
| --- | --- | --- |
| Android friends | 0.1.18-beta35/code35, HTTPS APK through invitation page | ARM64; manual update; same beta signing certificate; not a Play/GitHub release |
| Linux preview | 0.2.9 / 146d221d0ad23c07 | Paired bundle; operator-assisted installation |
| Windows preview | 0.2.9 / a6c68fe | x64 installer; physical Windows acceptance pending |
| Test candidates | Android beta38; desktop0.2.10 | Not yet public downloads |
| TCP helpers | tcp-v0.1.0 / tcp-setup-v0.1.0 | Separate operator/setup components, not the consumer app |

[Android installation](getting-started.en.md) · [Desktop installation](clients.en.md) ·
[Published desktop releases](https://github.com/Joker20380/family_connect/releases).

Current preview downloads: [Linux 0.2.9 / 146d221d0ad23c07](https://185.251.89.19:8443/downloads/FamilyConnect-Control-Linux-preview-146d221d0ad23c07.tar.gz) · [Windows 0.2.9 / a6c68fe](https://185.251.89.19:8443/downloads/FamilyConnect-Setup-0.2.9-preview-a6c68fe.exe)

## Existing pipeline

[Client builds](../.github/workflows/clients.yml) builds/tests Android, Linux and Windows.
Its release job needs all three jobs and runs for `v*` tags or main commits beginning
with `Release `. It publishes versioned desktop assets, checksums and a Windows preview.
It does not currently publish the friends APK to GitHub Releases.

Platform CI artifacts alone do not authorize a signed update. The desktop catalog is
signed locally after downloaded assets are verified; the release key stays off CI and
servers. Catalog sequence numbers increase, and existing versions/tags/assets remain
immutable. [Full signing and rollback procedure](updates.en.md).

The Android friends APK is separately signed with a persistent beta key and manually
published to an exact HTTPS path. The signature permits in-place updates; it is not a
claim of app-store approval. [Beta35 verification](releases/2026-09-23-public-client-status.ru.md).

## Recommendations, not pipeline changes

1. Keep separate desktop and Android version channels; do not label desktop v0.2.9 as
   newer than Android beta35 by comparing their numbers.
2. For a future Android GitHub prerelease, attach the exact locally signed, verified APK,
   checksum and source/build receipt after platform checks. Never upload signing keys
   or silently replace the existing beta file with a CI debug build.
3. Resolve dependency/artwork licensing, private vulnerability reporting, Windows publisher
   signing and remaining mobile acceptance before presenting a broad public launch.
4. Retain controlled catalog signing as a separate approval boundary. Automation may stage
   artifacts, but must not bypass verification or expose offline keys.

No workflow semantics, release versions or signed catalogs changed during this documentation audit.
