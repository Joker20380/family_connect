# Try Family Connect

Windows0.2.16 targets Windows10 1809+ /11 x64 and bundles .NET.
After a failed0.2.13 installation, run the new installer over the remaining files.
No manual service setup is needed. Affected Windows10 device acceptance is pending.

[Русский](getting-started.ru.md) · [Home](../README.md)

## First activation

Android12+, ARM64; access is invitation-only. Installing the APK does not grant access.
The invitation page and in-app updater both provide beta110. Updating does not enable restricted FIELD access.

Beta110 includes MESH and quiet ongoing VPN-notification updates. Android below12 is unsupported.
Exact Android CI41449895463, existing signer and full verified-HTTPS hash checks PASS.
Beta110 adds explicit Amsterdam1 and Amsterdam2 choices for AWG/TCP; owner110 installation is not yet confirmed.
Paid baseline remains108 and existing entitlement is preserved. No Mi account or ADB is needed.
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

[Download beta110 — 56.2 MB](https://185.251.89.19:8443/downloads/FamilyConnect-Test-0.1.18-beta110.apk).
Version `0.1.18-beta110`, code110, ARM64,56221032 bytes; SHA256:

```text
159034142f0430445caf6420c7d491866f7802a7a3eb615a4d4bfb7908641861
```

The app also checks for updates. Open the APK and select **Update** in Android’s system
prompt. Do not uninstall or clear data: activation, keys and history must be kept.
A CI debug APK may use a different signature. Each other device needs its own activation;
do not copy another device’s profiles or keys.

The [older universal beta13](https://185.251.89.19:8443/downloads/FamilyConnect-Test-0.1.12-beta13.apk)
remains available for other architectures,240.5 MB. It lacks current features and is not
an equivalent alternative to110.

[Exact audio corresponding source and licenses](https://185.251.89.19:8443/downloads/FamilyConnect-Android-0.1.18-beta110-audio-source.tar.gz)
are available with the release. Installation requires Android confirmation; it is not forced.

Owner checkpoint: update over109 via **Settings → Check for updates → Install beta110**.
Do not uninstall, clear data or reenroll. After launch do not connect; report **110 УСТАНОВЛЕНА**.
Android sequence5 is optional. [Public108 rollback evidence](https://185.251.89.19:8443/downloads/FamilyConnect-Test-0.1.18-beta108.apk)
remains immutable; no paid event or canary replay accompanies this update.

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
and messages. [Beta110 validation/publication](releases/2026-11-02-gateway-selection.md).

## Desktop clients

[Linux0.2.11 / Windows0.2.16 previews](clients.en.md) also accept invitation links. Linux needs
operator-assisted dependency and VPN-helper setup. Desktop messenger parity with Android
is not claimed. Direct invitations and referral claims use separate pools; limits are not
current availability counts.

## Server load display

Beta110 shows **Server CPU** on the dashboard and **CPU N%** in the server list when
channel capacity is unknown. CPU is not channel utilization or the monthly traffic quota.
Known-capacity servers retain their aggregate indicator; stale/missing samples show No data.
[Release status](releases.md).

Explicit Amsterdam1/2 choices support AWG/TCP, not a second MESH gateway.
Netherlands keeps the assigned server; no existing device moves automatically.
Explicit nodes without measurements show No data, never an inferred country CPU reading.
