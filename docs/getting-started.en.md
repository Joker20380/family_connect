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
[Download beta35 — 36.4 MB](https://185.251.89.19:8443/downloads/FamilyConnect-Test-0.1.18-beta35.apk).
Version `0.1.18-beta35`, code `35`; SHA256:

```text
fd7cc8ca00ca95acd4cc2cf5cc265d6afd46d39a4a21d22374e14f1f915a3a4e
```

For other CPU architectures, the older build remains available separately:
[universal beta13 — 240.5 MB](https://185.251.89.19:8443/downloads/FamilyConnect-Test-0.1.12-beta13.apk).
It does not include later messenger improvements. This is not an equivalent current build.

## Update an existing installation

Download the new APK, open it, and choose **Update**. Do not uninstall or clear data.
An ordinary update uses the same signing certificate and keeps activation and history.
The app can check for updates and request Android installation; system confirmation is still required. A CI debug build may have a different
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
[Beta35 verification](releases/2026-09-23-public-client-status.ru.md).

## Desktop

[Linux and Windows pilot installation](clients.en.md). These releases have different
onboarding and features from the Android friends beta.

Direct pilot codes and participant referrals use separate budgets: 50 direct codes and 500 shared referral slots. Using a direct code does not reduce the referral pool. The fixed pool limit is not the remaining count.
