# Try Family Connect

Windows0.2.15 targets Windows10 1809+ /11 x64 and bundles .NET.
After a failed0.2.13 installation, run the new installer over the remaining files.
No manual service setup is needed. Affected Windows10 device acceptance is pending.

[Русский](getting-started.ru.md) · [Home](../README.md)

## First activation

Android12+, ARM64; access is invitation-only. Installing the APK does not grant access.
The invitation page and in-app updater both provide beta107. Updating does not enable restricted FIELD access.

Beta107 includes MESH and quiet ongoing VPN-notification updates. Android below12 is unsupported.
CI/signature/public-download checks PASS; physical107 runtime remains unverified. The owner
authorized general rollout without USB debugging. No Mi account or ADB is required to install.
MESH still requires accepted admission and current readiness material, not an old cached READY.

1. Ask a participant for their link/QR from **Settings → Invite a friend**. Keep it private.
2. Download the APK and install **Family Connect Test**, allowing installation from your
   browser when Android asks. Update an existing installation in place.
3. Return to the original full invitation link, mark **Application installed** and choose **Open application**.
   Allow Family Connect to open. Activation happens inside the app; no manual code is needed.
   If Telegram's embedded browser does not open the app, use an external browser.
4. Select a country and transport beside the battery panel, enable VPN and accept Android's
   VPN prompt. Check the external IP on the Route screen, then open a normal website.

## Update an existing app

[Download beta107 — 56.2 MB](https://185.251.89.19:8443/downloads/FamilyConnect-Test-0.1.18-beta107.apk).
Version `0.1.18-beta107`, code107, ARM64,56212840 bytes; SHA256:

```text
5e219e77d1a030b59c08a4e994213bc2fd4dc0689cd7fb3fb8365e81de737099
```

The app also checks for updates. Open the APK and select **Update** in Android’s system
prompt. Do not uninstall or clear data: activation, keys and history must be kept.
A CI debug APK may use a different signature. Each other device needs its own activation;
do not copy another device’s profiles or keys.

The [older universal beta13](https://185.251.89.19:8443/downloads/FamilyConnect-Test-0.1.12-beta13.apk)
remains available for other architectures,240.5 MB. It lacks current features and is not
an equivalent alternative to107.

[Exact audio corresponding source and licenses](https://185.251.89.19:8443/downloads/FamilyConnect-Android-0.1.18-beta107-audio-source.tar.gz)
are available with the release. Installation requires Android confirmation; it is not forced.

## Text and voice

Add a contact and verify the full key/fingerprint through a trusted channel. The arrow
sends text; long-press your own text message to edit. Hold the microphone to record,
release to send. Swipe up to lock recording, then use the arrow to send or cross to
cancel. Swipe left while holding to cancel. Recording requires Android10+ and is limited
to60s/128KiB. After granting microphone access, hold again to start. At the limit,
recording stops and waits for sending. Leaving the app cancels an unsent recording.
Use the current version on both phones for the same interface.

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
and messages. [Beta107 validation/publication](releases/2026-10-30-nl-gateway-replacement.md#android107-general-publication--31-october).

## Desktop clients

[Linux0.2.11 / Windows0.2.15 previews](clients.en.md) also accept invitation links. Linux needs
operator-assisted dependency and VPN-helper setup. Desktop messenger parity with Android
is not claimed. Direct invitations and referral claims use separate pools; limits are not
current availability counts.
