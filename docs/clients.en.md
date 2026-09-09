# Family Connect applications 0.1

[Русский](clients.ru.md) · [Home](../README.en.md)

## Included

- Android: a native app embedding the official WireGuard GoBackend; no separate WireGuard
  app is required. Android 8.0/API 26 or newer.
- Linux: a Python/Tk desktop UI controlling WireGuard through NetworkManager.
- Windows: the same UI controlling an installed official WireGuard service. Administrator
  rights are required; Windows packages are built on Windows through GitHub Actions.
- Full IPv4/IPv6 profile import, connect/disconnect, actual OS tunnel state, manual public-IP
  checks, and Russian/English UI.

This first client uses direct WireGuard. Adaptive relays, family invitations, link enrollment,
gateway selection and a persistent application kill switch are not integrated. The experimental
Rust core remains separate. The retired website server is not used.

## Android

Local build: `artifacts/clients/FamilyConnect-Android-debug.apk`.
GitHub Actions: **Client builds**, artifact **FamilyConnect-Android-debug**.

1. Transfer the APK and personal `fc-ru-android.conf` file by USB.
2. Install the APK; Android may ask you to allow installation from that source.
3. Open Family Connect → Add device profile → select the `.conf` file.
4. Tap Connect and grant VPN permission; notification permission is optional.
5. Tap Check public IP. The current Russian gateway should show `185.251.89.19`.

Disconnect the old VPN before using this app. The imported configuration remains this device's
personal profile; do not share one key between simultaneously connected devices. The APK does
not contain your private keys or a preconfigured VPN profile.

The profile is stored privately using AES-GCM with an Android Keystore key. The file is excluded
from backup/device transfer and FLAG_SECURE protects the screen. The original imported file is
not deleted by the app; you may remove it after import. Remove saved profile deletes the stored
profile and its storage key.

A foreground service provides a disconnect notification. Closing the Activity keeps the VPN
running. There is no boot auto-connect, and Always-on is explicitly disabled pending lifecycle
and recovery validation. A debug APK is for private testing. Persistent updates need a release
signing key: debug builds from different machines/CI can have different signatures. This is not
a Google Play release. Physical-device operation, Wi-Fi/LTE and leak behavior remain to be tested.

## Linux

Requires Python 3, Tk and NetworkManager with WireGuard support. These components were checked
on your laptop, and the existing `fc-ru-linux` profile is detected automatically.

```sh
./clients/desktop/install-linux.sh
```

Open **Family Connect** from the applications menu, or run directly:

```sh
python3 clients/desktop/app.py
```

Only application profiles `fc-app-*` and the existing `fc-ru-linux` are listed. Import creates a
NetworkManager profile, disables automatic connection and prioritizes full-tunnel DNS. Temporary
configuration files have mode 0600 and are removed; permanent key storage and authorization are
handled by NetworkManager/Polkit. Run the UI as a normal user, not through sudo. The OS can request
authorization. Closing the window keeps the system tunnel running and prompts when its active
state is known.

## Windows

1. Install [official WireGuard](https://www.wireguard.com/install/).
2. In GitHub **Actions → Client builds**, download **FamilyConnect-Windows**.
3. Extract the **whole** folder, including `_internal`, run `FamilyConnect.exe` and allow UAC.
4. Import a separate Windows profile and connect. Do not reuse a currently active Linux/Android
   key; an additional device needs its own peer on the gateway.

The app checks the installed WireGuard Authenticode signature. Its official manager service
applies ACLs and converts imported profiles into DPAPI storage. Family Connect does not maintain
its own persistent plaintext profile store. Profile names are limited to `fc-app-*`; unrelated
VPN services are not deleted. The app's tunnel service is configured for manual startup;
disconnecting uninstalls only the selected tunnel service. IP checks are user-triggered.

The Windows executable is packaged with PyInstaller on Windows and is not Authenticode-signed.
Unknown-publisher warnings do not constitute an operator signature. Actual VPN/DPAPI behavior
has not yet been validated on a user's Windows machine.

## Tests and builds

Parsers reject executable hooks such as PostUp/PreUp, unknown or repeated fields, multiple peers,
invalid keys, incomplete IPv4/IPv6 routes and oversized profiles. Android also uses the official
library parser. This MVP accepts numeric endpoint/DNS addresses. The app does not log private
keys, configurations or traffic contents.

```sh
python3 -m pytest clients/desktop/tests -q
python3 clients/desktop/app.py --smoke

# Android: JDK 17, Gradle 8.11.1, SDK 35 / Build Tools 35.0.0
cd clients/android
gradle --no-daemon :app:assembleDebug :app:testDebugUnitTest :app:lintDebug

# Windows PowerShell, Python 3.12+
./clients/desktop/build-windows.ps1
```

An active interface alone is not evidence of working Internet access. The UI therefore reports
“Tunnel is on” and provides a separate IP check through Cloudflare.

Integration references: [WireGuard embedding](https://www.wireguard.com/embedding/),
[Windows services and secure storage](https://git.zx2c4.com/wireguard-windows/about/docs/enterprise.md).

The local debug signing key is retained only on the laptop under `state-client-build/android-signing/`, outside Git. Keep it to support updates over the locally installed build.

### Windows troubleshooting

If the profile list is empty and setup fails, install official WireGuard using Install WireGuard, then select Retry setup. Run Family Connect as administrator. WireGuard signature verification remains mandatory. After setup succeeds, import a separate Windows device profile using Add profile. The client displays specific setup failures without exposing profile contents or system command output.
