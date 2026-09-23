# Client installation

[Русский](clients.ru.md) · [Home](../README.md)

Status checked 2026-09-23. Client features and release versions differ by platform.

## Android

Use the [friends beta guide](getting-started.en.md): Android 8+, ARM64 beta50,
invitation-based access, VPN, text and voice messages. The APK is distributed through
an invitation page and HTTPS download; it is not yet a GitHub or app-store release.
The [client workflow](../.github/workflows/clients.yml) documents source-build requirements.
CI debug APKs are not update packages for an installed friends beta.

## Current invitation-page downloads

[Linux 0.2.10 / 8e9fabe3cbef2989](https://185.251.89.19:8443/downloads/FamilyConnect-Control-Linux-preview-8e9fabe3cbef2989.tar.gz) · [Windows 0.2.12 / a584e54](https://185.251.89.19:8443/downloads/FamilyConnect-Setup-0.2.12-preview-a584e54.exe)

Install the client, return to the original invitation link, mark **Application installed** and choose **Open application**.
Windows installs the URI handler with its service and preserves existing activation.
Linux needs operator-assisted setup: [current archive instructions](https://185.251.89.19:8443/downloads/FamilyConnect-Linux-0.2.10-invitation.txt).
They cover a persistent Python environment and desktop URI handler; VPN helpers are installed separately.

[Windows GitHub preview](https://github.com/Joker20380/family_connect/releases/tag/windows-preview-20260923-a584e54) · [Linux GitHub preview](https://github.com/Joker20380/family_connect/releases/tag/desktop-preview-20260923-840181d) · [Hashes and checks](releases/2026-09-23-windows0212-repaint.ru.md).
Preserve identity and application data when updating. This is a manual preview; the older
six-file release's automatic catalogs are unchanged. Desktop messenger parity is not claimed.
The separate historical GitHub v0.2.9 flow below is retained; use the current downloads above for new invitations.

Windows0.2.12 automatically creates the local device key on first launch. Access still needs an invitation: on the phone choose **Settings → Invite a friend**, send the full link to the PC and open it. Alternatively choose **Activate with invitation** on the PC, paste the full link and select **Activate access**. Launching only the desktop shortcut cannot supply the invitation. Existing access survives an update.

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
