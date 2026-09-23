# Try Family Connect

[Русский](getting-started.ru.md) · [Home](../README.md)

## First activation

Android8+, ARM64; invitation-only access. Downloading an APK does not grant access.
The invitation page still provides beta35, while the updater provides beta49.

1. Ask a participant for a link/QR from **Settings → Invite a friend**. Obtain your own
   code on that page and download its beta35 APK. Keep invitation links private.
2. Install **Family Connect Test**, allowing installation from your browser if Android asks.
3. In beta35, use **Settings → Activate with code** and enter your code.
4. Once activated, install beta49 below over the existing app, keeping its data.
   No new invitation is required. Beta49 no longer has manual code entry; the new
   invitation page with an app-opening button has not been published yet.
5. In beta49, choose country/transport in the home connection panel near the battery,
   enable VPN and allow Android’s VPN request. Check the public IP in Route, then try a website.

## Update an existing app

[Download beta49 — 36.4 MB](https://185.251.89.19:8443/downloads/FamilyConnect-Test-0.1.18-beta49.apk).
Version `0.1.18-beta49`, code49, ARM64,36448332 bytes; SHA256:

```text
3a37613a63c130af97c853d1c39836c026822dca717a748fa005a3211f8f549d
```

The app also checks for updates. Open the APK and select **Update** in Android’s system
prompt. Do not uninstall or clear data: activation, keys and history must be kept.
A CI debug APK may use a different signature. Each other device needs its own activation;
do not copy another device’s profiles or keys.

The [older universal beta13](https://185.251.89.19:8443/downloads/FamilyConnect-Test-0.1.12-beta13.apk)
remains available for other architectures,240.5 MB. It lacks current features and is not
an equivalent alternative to49.

## Text and voice

Add a contact and verify the full key/fingerprint through a trusted channel. The arrow
sends text; long-press your own text message to edit. Hold the microphone to record,
release to send. Swipe up to lock recording, then use the arrow to send or cross to
cancel. Swipe left while holding to cancel. Recording requires Android10+ and is limited
to60s/128KiB. After granting microphone access, hold again to start. At the limit,
recording stops and waits for sending. Leaving the app cancels an unsent recording.
Update both phones to49 for the same interface.

The background service receives messages and posts notifications without an active VPN
when the message server is reachable. Check the service and notification settings in the
messenger menu. Screen-off delivery was tested; immediate delivery during deep Doze is
not established. [Notification and announcement guide (RU)](testing/messenger-notices.ru.md).

## Troubleshooting

- No invitation: ask a participant/operator; the APK alone is insufficient.
- VPN without Internet: check the public IP and try another region/transport.
- Missing messages: check connectivity, both registrations, contact keys, background
  service and notification permission. Open the app again after a system force-stop.
- Missing map location: allow approximate location; VPN does not require it.
- Update failure: record the error and versions; do not erase data to bypass a signature mismatch.

Report model, Android/app version and network type. Exclude invitations, keys, profiles
and messages. [Beta49 validation (RU)](releases/2026-09-23-voice-scroll-beta49.ru.md).

## Desktop

[Linux/Windows](clients.en.md) have separate versions and operator-assisted activation.
Direct invitations and referrals use separate pools; configured limits50/500 are not
live remaining counts. Coordinated invitation-link rollout remains in [PLAN](PLAN.md).
