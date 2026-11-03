# Android update incident — 3 November 2026

## Scope and status

**OPEN; read-only initial diagnosis, not a fix or rollout.** The owner reports that
Android users in St Petersburg reach100% and then see “Не удалось скачать или
проверить обновление”. Their Android OS, installed beta and exact failing exception
are not available. This incident takes priority over the queued fleet continuation.

No source/runtime/catalog changes, signing, installation, user-data access, production
writes or service restarts. Android public/invitation110, signed catalog sequence5;
Windows0.2.16/sequence12; public Linux0.2.11, owner-installed0.2.12~l03.2.13 unchanged.

## Verified observations

- Public signed Android catalog matches the repository, verifies against the existing
  Ed25519 anchor and agrees with legacy discovery: optional110, sequence5.
- Full public HTTPS download repeated successfully before08:34UTC: HTTP200,
  56,221,032bytes, SHA256
  `159034142f0430445caf6420c7d491866f7802a7a3eb615a4d4bfb7908641861`.
  Read-only server file hash and retained signed release copy match.
- `apksigner verify` passes on the downloaded bytes; certificate SHA256
  `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
  `aapt2` confirms `com.familyconnect.app.friends`, code110,
  `0.1.18-beta110`, minimum API31/Android12, target35.
- Disposable Android15/API35 emulator: `getPackageArchiveInfo` with certificate
  collection successfully parses these release bytes with both `.apk` and `.part`
  suffixes, identical package/version and one signer. A filename-only diagnosis is
  not supported on this runtime. This shell parser probe is not an installed-client
  upgrade test or evidence for every Android/OEM version.
- The same emulator rejects a separately generated synthetic API36-minimum signed
  fixture with a null archive result. No product signing key or user profile was
  used. The disposable emulator was stopped after the probes; no physical device
  was connected or modified.
- Initial Python HTTPS catalog fetch ended with remote disconnect; first full curl
  APK transfer timed out after180s at1,572,441bytes. A2MiB range and then a full curl
  repeat succeeded, the latter in21.95s. Do not erase those failures or infer that
  the St Petersburg route is healthy from this workstation's successful repeat.

## Source findings and unresolved cause

`AppUpdateUi.download` catches transfer, disk/sync/rename and APK verification errors
under one generic message. `AppUpdate.receive` reports100% when the expected byte
count arrives, before final checksum and APK identity/signer verification. Therefore
100% does not establish a verified, installable update.

Discovery checks ARM64 and the Friends package but not the Android OS. Since107,
public Friends builds require API31; older installed clients can still offer110 on
Android8–11, then fail archive verification. This is a confirmed compatibility gap,
but **not the established cause on the reported phones** without their OS/version.
Other possibilities, including installed signer mismatch, local storage failure and
transfer failure, have not been excluded on those phones. Do not remove checksum,
certificate or version checks, lower SDK requirements, or republish110 speculatively.

## Safe workaround and next checks

For Android12+ ARM64, download the already-published
[signed110 APK](https://185.251.89.19:8443/downloads/FamilyConnect-Test-0.1.18-beta110.apk)
in a browser and open it as an in-place update. Keep Android's normal confirmation
and signature checks. **Do not uninstall or clear app data**: that risks losing the
existing identity/profiles. A browser install bypasses only the app's updater UI,
not Android package verification. It is a workaround to try, not confirmed recovery.
Android8–11 cannot install110; direct download does not make it compatible.

Remaining: obtain the affected Android OS and installed beta, localize/reproduce the
matching failure, add focused regression/runtime coverage and validate any necessary
new-version delivery through normal CI/offline-signing gates. No new APK is built or
distributed by this investigation. Rollback is unnecessary because production and
client state were not changed; all immutable artifacts/catalogs remain intact.

Private local probes and downloaded bytes remain ignored under
`state-client-build/android-update-20261103/`. Only this sanitized report enters Git.
