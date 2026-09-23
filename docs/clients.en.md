# Client installation

[Русский](clients.ru.md) · [Home](../README.md)

Status checked 2026-09-23. Client features and release versions differ by platform.

## Android

Use the [friends beta guide](getting-started.en.md): Android 8+, ARM64 beta35,
invitation activation, VPN and pilot text messenger. The APK is distributed through
an invitation page and HTTPS download; it is not yet a GitHub or app-store release.
The [client workflow](../.github/workflows/clients.yml) documents source-build requirements.
CI debug APKs are not update packages for an installed friends beta.

## Current invitation-page downloads

[Linux 0.2.9 / 146d221d0ad23c07](https://185.251.89.19:8443/downloads/FamilyConnect-Control-Linux-preview-146d221d0ad23c07.tar.gz) · [Windows 0.2.9 / a6c68fe](https://185.251.89.19:8443/downloads/FamilyConnect-Setup-0.2.9-preview-a6c68fe.exe)

These immutable previews are newer than the original GitHub v0.2.9 assets described below. Linux requires operator-assisted setup; [current Linux instructions](https://185.251.89.19:8443/downloads/FamilyConnect-Linux-brand-20260920.txt). Desktop 0.2.10 with invitation-link activation is still under test.

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
[updates](updates.en.md). Android friends updates are manual, using the same beta key.
A successful build or installer check does not establish live VPN reliability on every
network. [Current platform evidence](STATUS.md) and dated release reports separate
installation, UI, networking and recovery tests.

[Historical initial-client guide](clients-legacy.en.md) is retained for the early direct
WireGuard experiment; its old Tk/Windows-wrapper instructions are not current installation advice.
