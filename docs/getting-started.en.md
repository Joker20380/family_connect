# Try Family Connect

[Русский](getting-started.ru.md) · [Home](../README.md)

## Android friends beta

Android 8 or newer; the compact build requires ARM64. This is an invitation-based
pilot, not a public subscription launch. Downloading the app does not grant server access.

1. Ask a participant for an invitation link or QR code. In their app it is under
   **Settings → Invite a friend**. Open that page, obtain your own invitation code
   and download the APK. Do not post invitation links publicly.
2. Install **Family Connect Test**. Android may request permission to install from
   that browser or file manager.
3. Open **Settings → Activate with code**, and paste your code. Each activation is
   bound to a device; do not copy another device's profile or keys.
4. In **Route**, select a gateway region and transport; tap **Connect** and allow
   Android's VPN request. Check the public IP in Route, then try a website.
5. Open **Messenger** to add a contact, verify their full key/fingerprint through
   a trusted channel, and exchange text. Incoming refresh currently requires the
   messenger to be open; background push is not implemented.

**Already have an invitation or an activated app?**
[Download beta19 — 36.4 MB](https://185.251.89.19:8443/downloads/FamilyConnect-Test-0.1.18-beta19.apk).
Version `0.1.18-beta19`, code `19`; SHA256:

```text
5ebe38168f084d3e19bb740722ec7c3a7ceb5e9ed63508efc3e3ff3f5e0bf3a4
```

For other CPU architectures, the invitation page offers the older
[universal beta13 — 240.5 MB](https://185.251.89.19:8443/downloads/FamilyConnect-Test-0.1.12-beta13.apk).
It does not include later messenger improvements. This is not an equivalent current build.

## Update an existing installation

Download the new APK, open it, and choose **Update**. Do not uninstall or clear data.
An ordinary update uses the same signing certificate and keeps activation and history.
There is no automatic Android updater yet. A CI debug build may have a different
signature and cannot serve as an update to the friends beta.

## Troubleshooting

- **No invitation:** the APK alone cannot activate service. Ask the participant or operator.
- **VPN connects but Internet does not work:** use Check public IP, then try the other
  available region or transport. Report the app version, Android version and network type.
- **No incoming message:** keep the messenger open and allow roughly 10–15 seconds;
  confirm both devices have registered messaging and checked contact keys.
- **Location unavailable:** Android approximate location is optional. Route placement
  depends on permission and device location availability; VPN does not require it.
- **An update fails:** keep the installed app. Record the Android error and APK version;
  do not delete your data to work around a signature mismatch.

Keep invitation codes, profiles, private keys and personal chat history out of reports.
[Detailed Russian walkthrough](testing/friends-quickstart.ru.md) ·
[Beta19 verification](releases/2026-09-19-beta19-download.ru.md).

## Desktop

[Linux and Windows pilot installation](clients.en.md). These releases have different
onboarding and features from the Android friends beta.

Direct pilot codes and participant referrals use separate budgets: 50 direct codes and 500 shared referral slots. Using a direct code does not reduce the referral pool. The fixed pool limit is not the remaining count.
