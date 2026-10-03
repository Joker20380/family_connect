# Client installation

Final FIELD preparation adds a registration-bound Support ID in Settings → About /
Diagnostics (Copy Support ID). Candidate59 is still unpublished; old8229a36 is the
previous local build, not the revised candidate. [Current status and tester steps](releases/2026-10-03-field1-release-final.md).
Update over the existing app; never uninstall or clear data. Send the Support ID,
not cryptographic keys, and wait for explicit operator admission before FIELD tests.

Revised local candidate: source `5abc2da`, APK SHA256
`6d13720bc8cff25d51d95ff7453127577890bee881685a4a66c86fae163f2148`.
Installed in place on the owner Redmi03.10; not published. Identity/data retained,
Auto/AWG/TCP pass. Authenticated server delivery now returns the original backfilled
Support ID; visible/Copy/restart and diagnostics export pass. No replacement identity
or enrollment. Hosted release checks/publication remain pending; no wider FIELD yet.
The earlier `b952c3b` / `8229a36` build below is historical. Public download remains51.

FIELD candidate03.10: beta59/code59 source in local validation, **not installed or
published**. Download remains51 until in-place owner acceptance. Never uninstall
to update; retain identity/data/enrollment. [Release status](releases/2026-10-03-field1-release-diag1a.md).

Local candidate now built/signed from `b952c3b`, APK SHA256
`8229a36e8b176aa49346f3bf106f4f1229cb492a47c1c50e86593ddcb4c85a3b`.
This is not a public download or completed rollout; public links below stay51.

Latest private checkpoint03.10.2026: **`0.1.18-canary58-physical`/58 installed over57**,
same Friends package/signer/UID/data, encrypted restart READY/ACK_RECEIVED preserved.
APK SHA256 `91e8910896ff84b31a7cebf40f840256dca283d684b075577290d1282f227194`;
signer `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
Private launcher hook fixed and live ON/OFF tested. Physical rehearsal BLOCKED on
MIUI-denied ADB input/no manual CONNECT. Override OFF after restart; app disconnected.
Not a public release; public/invitation/catalog links unchanged and not reverified.
[Current installed state/provenance](releases/2026-10-03-5n-physical-hook-fix-and-rehearsal.ru.md).

Current private-device checkpoint03.10.2026: exact `0.1.18-canary57-physical`/57 is
**installed in place over55**, with the same package/signer and encrypted readiness
preserved (restart READY/ACK_RECEIVED). SHA256
`dd3c1b1bd9031f189ef7fc606969eb7da05e44f470478c8457f9097119b9c975`.
Private hook navigation crashed before restricted CONNECT; diagnostic override is OFF,
Auto retained, app disconnected. Physical acceptance FAIL, Stage5N not closed.
Not publicly distributed; public/invitation/catalog links unchanged and not reverified.
[Current installed state and exact failure](releases/2026-10-03-5n-physical-restricted-rehearsal-final.ru.md).
Earlier build-only statements below are historical.

Private acceptance build03.10.2026: `0.1.18-canary57-physical`/57 arm64 is signed,
**not installed or published**; the Redmi remains canary55. Same Friends package/signer;
debuggable packaging exposes existing diagnostic Activities for private acceptance only.
APK SHA256 `dd3c1b1bd9031f189ef7fc606969eb7da05e44f470478c8457f9097119b9c975`.
No public/invitation/update-catalog change; do not distribute this diagnostic build.
[Exact signer, local tests and credential-reload blocker](releases/2026-10-03-5n-physical-restricted-rehearsal.ru.md).

Windows0.2.15 targets Windows10 1809+ /11 x64 and bundles .NET.
After a failed0.2.13 installation, run the new installer over the remaining files.
No manual service setup is needed. Affected Windows10 device acceptance is pending.

[Русский](clients.ru.md) · [Home](../README.md)

Status checked 2026-09-23. Client features and release versions differ by platform.

## Android

Local compatibility investigation,2026-10-02: `0.1.18-canary56-challenge`/56 arm64
**built unsigned only**, not install/update-ready, installed or distributed. SHA256
`5ca1d29101df529cce197e5eeb82f231b50e3f4fc76c8835ba12fdad0c2122b0`.
Installed private55 and public/invitation51 remain last documented, unchanged and
not reverified. No new download/update link or catalog. Production503 cause remains
unproven; [local tests, pins and BLOCKED gate](releases/2026-10-02-5n-real-owner-challenge-503.md).

Attempt15,02.10.2026: private `0.1.18-canary55-receipt`/55 **installed over54** on the
owner Redmi, exact APK/signature verified; no uninstall/data reset. SHA256
`680a21f60e69cb62d2c7a70be07234b34196e178f0207ed69cb4b422b7bc6247`.
Real app challenge503 blocked READY; server restricted rollout rolled back. Phone
remains55, not a public/FIELD release. Public beta51/invitation downloads unchanged
and not reverified. Build-only statements below are historical checkpoints.
[Attempt15 evidence and limits](releases/2026-10-02-5n-prov1-attempt15.ru.md).

Local build checkpoint,2026-10-02: private `0.1.18-canary55-receipt`/55 arm64 adds
post-import structured readiness receipt and authenticated ACK. Same package/beta
signer, update-compatible with54; **built/signed, NOT installed or publicly distributed**.
SHA256 `680a21f60e69cb62d2c7a70be07234b34196e178f0207ed69cb4b422b7bc6247`.
[Local APK path, checks and contract](releases/2026-10-02-5n-device-readiness-receipt.ru.md). Installed54 and public
beta51/invitation links below remain last documented; no download link was replaced
or public artifact reverified. No production/authority change or rollout in this gate.

Checkpoint, 2026-10-02: private `0.1.18-canary54-prov1`/54 is built, beta-signed and
**installed in place on the owner Redmi** during attempt14; final APK/hash/signature
verified16:47UTC. No uninstall/data clear. Server deployment rolled back after owner
UI observation failed; restricted cache readiness is unverified. The app remains54,
not publicly distributed and not a FIELD release. Public beta51/invitation links
remain unchanged and were not reverified. [Attempt14](releases/2026-10-02-5n-prov1-attempt14.ru.md)
· [Canary provenance and SHA256](releases/2026-10-02-5n-android-canary-build.ru.md).

Use the [friends beta guide](getting-started.en.md): Android 8+, ARM64 beta51,
invitation-based access, VPN, text and voice messages. The APK is distributed through
an invitation page and HTTPS download; it is not yet a GitHub or app-store release.
The [client workflow](../.github/workflows/clients.yml) documents source-build requirements.
CI debug APKs are not update packages for an installed friends beta.

## Current invitation-page downloads

[Linux 0.2.11 AppImage](https://185.251.89.19:8443/downloads/FamilyConnect-0.2.11-x86_64.AppImage) · [Linux 0.2.11 .deb](https://185.251.89.19:8443/downloads/FamilyConnect_0.2.11_amd64.deb) · [Windows 0.2.15 / 2ffba77](https://185.251.89.19:8443/downloads/FamilyConnect-Setup-0.2.15-pilot-unsigned.exe)

Install the client, then open it from the invitation link or the **Open Family Connect**
button on the invitation page. Windows installs the URI handler with its service and
preserves existing activation.

Windows 0.2.15 is the primary version. Windows 0.2.14 is available as a compatibility
fallback for some older Windows 10 installs: the invitation page shows it as a secondary
**Download compatible version 0.2.14** action
([immutable EXE](https://185.251.89.19:8443/downloads/FamilyConnect-Setup-0.2.14-pilot-unsigned.exe)).

Linux is now distributed as regular user-facing artifacts:

- `FamilyConnect-0.2.11-x86_64.AppImage` — primary option; `chmod +x` and run; no pip,
  venv or source checkout. Host GTK/GI prerequisites are documented in the [report](linux-appimage-deb.ru.md).
- `FamilyConnect_0.2.11_amd64.deb` — Ubuntu / Debian / Mint: `sudo apt install ./FamilyConnect_0.2.11_amd64.deb`,
  appears in the menu and registers `x-scheme-handler/familyconnect`.
- `FamilyConnect-Control-Linux-preview-5b02e8cb9fde119f.tar.gz` — advanced/manual only.

VPN helpers are installed separately. SHA256 and checks are in [releases.md](releases.md)
and the [Linux report](linux-appimage-deb.ru.md).

[Windows GitHub preview](https://github.com/Joker20380/family_connect/releases/tag/windows-v0.2.15) · [Linux GitHub preview](https://github.com/Joker20380/family_connect/releases/tag/desktop-preview-20260926-5b02e8cb) · [Hashes and checks](releases/2026-09-26-server-list-crossplatform.ru.md).
Preserve identity and application data when updating. Windows0.2.15 uses its own signed update catalog; install it manually once from0.2.12 or earlier. Linux and the older shared catalog are unchanged. Desktop messenger parity is not claimed.
The separate historical GitHub v0.2.9 flow below is retained; use the current downloads above for new invitations.

Windows0.2.15 automatically creates the local device key on first launch. Access still needs an invitation: on the phone choose **Settings → Invite a friend**, send the full link to the PC and open it. Alternatively choose **Activate with invitation** on the PC, paste the full link and select **Activate access**. Launching only the desktop shortcut cannot supply the invitation. Existing access survives an update.

## Original GitHub v0.2.9: Linux

The original desktop release is the [v0.2.9 pilot](https://github.com/Joker20380/family_connect/releases/tag/v0.2.9).
The UI uses **GTK 4/libadwaita**, not Tk. Requirements: system Python with GI,
GTK 4.8+, libadwaita 1.2+, cryptography and NetworkManager with WireGuard support.
On Debian/Ubuntu, install the prerequisites:

```sh
sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 python3-cryptography network-manager
```

Download and extract `FamilyConnect-Linux-0.2.9.tar.gz` from that release. Inside the
extracted directory, run `sh install-linux.sh`, then open Family Connect from the
applications menu. Run the UI as your normal user; privileged operations use the
platform's authorization flow. The operator supplies device-specific activation/profile
setup. The release does not include the Android friends invitation flow or messenger.

For source installation, run `sh clients/desktop/install-linux.sh` after installing
prerequisites. Experimental paired control builds are separate from the six-file
release archive: [operator runbook](linux-control-preview-rollout.ru.md).

## Original GitHub v0.2.9: Windows x64

Download `FamilyConnect-Setup-0.2.9-pilot-unsigned.exe` from the
[v0.2.9 release](https://github.com/Joker20380/family_connect/releases/tag/v0.2.9).
The installer includes the native app, .NET runtime, broker and VPN components.
Administrator approval is needed for installation; a separate WireGuard app is not required.
A trusted Family Connect Authenticode publisher signature is still missing; do not
turn off security software to install it. No Windows ARM64 release is validated.

Use **Get device code**, give the public code to the operator, then import the
operator-issued `.fcactivation` file and connect. See the
[native Windows guide](windows-native.en.md) for key custody, activation and build steps.
Published desktop onboarding is not the newer Android friends activation flow.

## Updates and limits

Desktop update checks verify an offline-signed catalog and artifact hashes; see
[updates](updates.en.md). Android friends checks for updates in the app; Android asks the user to install the APK signed with the same beta key.
A successful build or installer check does not establish live VPN reliability on every
network. [Current platform evidence](STATUS.md) and dated release reports separate
installation, UI, networking and recovery tests.

[Historical initial-client guide](clients-legacy.en.md) is retained for the early direct
WireGuard experiment; its old Tk/Windows-wrapper instructions are not current installation advice.
# FIELD-1 candidate notice — 2026-10-03

Android `0.1.18-beta60` / code60 is signed and accepted on the owner Redmi and by
the required hosted gates, but **not publicly distributed**. Candidate SHA256:
`8ee59352e5f490aea74c3c8c8aeefd0d65bec0c261a044899d512ca376cf6104`.
Historical beta59 is not eligible for publication. Public invitation/downloads
remain beta51; no public download link or update catalog has changed.
