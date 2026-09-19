# Release distribution

Audited 2026-09-19 against the GitHub Releases API and the deployed Android invitation page.

| Channel | Latest relevant distribution | Limits |
| --- | --- | --- |
| Android friends | 0.1.18-beta19/code19, HTTPS APK through invitation page | ARM64; manual update; same beta signing certificate; not a Play/GitHub release |
| Desktop | GitHub prerelease v0.2.9 | Linux GTK archive and Windows x64 pilot installer; not Android feature parity |
| TCP helpers | tcp-v0.1.0 / tcp-setup-v0.1.0 | Separate operator/setup components, not the consumer app |

[Android installation](getting-started.en.md) · [Desktop installation](clients.en.md) ·
[Published desktop releases](https://github.com/Joker20380/family_connect/releases).

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
claim of app-store approval. [Beta19 verification](releases/2026-09-19-beta19-download.ru.md).

## Recommendations, not pipeline changes

1. Keep separate desktop and Android version channels; do not label desktop v0.2.9 as
   newer than Android beta19 by comparing their numbers.
2. For a future Android GitHub prerelease, attach the exact locally signed, verified APK,
   checksum and source/build receipt after platform checks. Never upload signing keys
   or silently replace the existing beta file with a CI debug build.
3. Resolve dependency/artwork licensing, private vulnerability reporting, Windows publisher
   signing and remaining mobile acceptance before presenting a broad public launch.
4. Retain controlled catalog signing as a separate approval boundary. Automation may stage
   artifacts, but must not bypass verification or expose offline keys.

No workflow semantics, release versions or signed catalogs changed during this documentation audit.
