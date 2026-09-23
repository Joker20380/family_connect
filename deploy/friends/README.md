# Invited tester distribution

Final user requirements,2026-09-14: one APK, one-use invite for one device, no account
or payment, no expiry after activation. Independent country (RU/NL) and transport
(AWG3.1/TCP REALITY) selection. This supersedes the earlier anonymous/common-access
prototype. It is separate from managed Reticulum acceptance and billing/product DB.

Android `friends` build type: `com.familyconnect.app.friends`, non-debuggable,
`FriendsActivity`. Each installation creates and preserves independent signing and
WG keys inside encrypted Android Keystore-backed private storage. Invite redemption
and every configuration refresh require a nonce-bound device signature. APK copying
alone does not activate a device. Updates retain identity; uninstall removes it.

The offline root signs credential-free gateway templates under the separate
`family-connect/invited-test/v1\0` domain (`scripts/sign_friends_catalog.py`). Templates
contain DEVICE_CREDENTIAL, LOCAL_DEVICE_KEY and ASSIGNED_ADDRESS placeholders.
Individual TCP UUID and AWG peer address are issued over authenticated HTTPS only.
The signed templates and returned credentials are cached in protected device storage.
Cached access has no lease, and never falls back after an explicit API denial.

Dedicated authorized-host services:

- `family-connect-friends-tcp`: RU185.251.89.19:8446, NL186.246.45.246:443;
  `/opt/apps/family_connect/friends-tcp/`, individual users, loopback Xray API18085.
- `family-connect-friends-awg`: UDP51823 on both hosts, interfacefcopen31;
  RU10.84.0.1/16, NL10.83.0.1/16, `/opt/apps/family_connect/friends-awg/`.
- `family-connect-friends-access`: RU loopback18084, private SQLite DB under
  `/opt/apps/family_connect/friends-access/`. HTTPS paths under `/friends/` on8443.
- Xray26.3.27/d2758a0 SHA256
  `4f7a4436f86798bbb5c875014e352021a1673710a45e170ccc507c5f59341940`.
- AWG3.1 experiment2 engine/tools SHA256
  `e7f00e47d6df853ade5dcd2fe79240f01ff897d75088c768316a444c27c87e0f` /
  `906d6795af1dd4adee7b11bf1e7fa133d4795c8a8d6e2099b34a026f810a3278`.

Nginx supplies TLS, method/body/rate limits; the root helper accepts only canonical
keys/UUID/device identifiers. The separate inter-server SSH key is restricted to
this registration command and pins the existing known host. Operator keys are never
copied. Existing product DB, API and VPN services are retained. The formerly shared
TCP credentials were revoked and the public credential catalog was withdrawn.

`control/friends/access.py` atomically binds a one-use invitation to one device and
WG key, rejects concurrent second claims/replays, and has no entitlement expiry.
`access-api.py` proves authorization before provisioning the selected country's
AWG peer/TCP user. `awg-gateway.py` maintains only its own interface, private peer DB,
iptables chain/rules and test TCP users. It never prints private configs or keys.
Generated profiles, invite codes and receipts stay under private state directories,
not Git/CI/command output. Only intended APK/manual files become public downloads.

Distribution gates: platform CI, final signed APK version/ABI/payload checks, real
Android activation and four country/transport combinations, repeat connection and
process restart, second-device invite refusal. Sign accepted assets using the
persistent local beta key, preserve immutable version/code and offline update root.

Rollback: stop only the affected friends service; preserve DB/keys/configs. This
intentionally disables those testers and must not be routine test cleanup. Review
later edits before restoring nginx `.before-invites` config; do not restore the old
public credential endpoint. Keep existing registration/TLS renewal and Pilot working.
Update clients with a higher version/code, without uninstalling their data.

## Participant referrals (2026-09-19)

The direct batch is now 50; a separate server-side campaign permits 500 referral
claims. Activated devices sign the `refer` challenge to obtain a stable URL.
The Android source displays it as QR; the public landing page explicitly claims
one invitation, with a browser-persisted idempotency ID. A sponsor may issue 20
new grants per rolling 24 hours. Revocation blocks new claims; prior child grants
remain independent. This is not unique-person verification.

Keep `referral.key`, `access.db` and `direct-50.json` backed up privately together;
never rotate the key or reset the counters during an upgrade. Fresh installation
requires `app/control/friends/referrals.py` and `invite/index.html` in the service
root before `install-access.py`. That installer is first-install-only.

See the [rollout, rollback, tests and remaining Android checks](../../docs/releases/2026-09-19-referrals.ru.md).
The source QR screen has not been packaged/installed: the user's APK pause remains.

## Compact Android download (2026-09-19)

The invite page offers beta14 ARM64 (36.4 MB) and the immutable universal beta13
fallback. Build compact explicitly with `-PfcTargetAbi=arm64-v8a`; default builds
keep four ABIs. Verify with `pilot/android-awg/verify-apk.py --abis arm64-v8a`.
Compact packaging compresses the unchanged native libraries; Android extracts them
on install. [Artifact, checks and rollback](../../docs/releases/2026-09-19-android-beta14.ru.md).
