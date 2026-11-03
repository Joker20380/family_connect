# Android update incident — 3 November 2026

## Scope and status

**OPEN; local compatibility source candidate, not a public fix or rollout.** The owner reports that
Android users in St Petersburg reach100% and then see “Не удалось скачать или
проверить обновление”. Their Android OS, installed beta and exact failing exception
were initially unavailable; the follow-up identifies Huawei nova3, probably Android8.1.
Exact installed OS/ABI/beta still require readback. This incident takes priority over
the queued fleet continuation. The owner subsequently authorized compatibility work
and requested checking earlier compatible builds; see the implementation section below.

Initial investigation made no source/runtime changes. The subsequent source candidate
is built and installed only on disposable emulators, without product signing, user-data
access, public catalog changes, production writes or service restarts.
Android public/invitation110, signed catalog sequence5;
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

## Initial source findings and unresolved cause

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

## Initial safe workaround and next checks

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

## Follow-up: legacy Android effort assessment

The owner confirms “old Android” and asks how much work supporting it would take;
exact OS, model/ABI and installed beta remain unknown. No implementation/release
is started by this assessment. Initial source evidence is encouraging but is not
compatibility acceptance:

- `clients/android/app/build.gradle` retains shared minimum26/Android8; only the
  public Friends variant overrides it to31/Android12.
- Current AWG, restricted ARM64 and audio native build scripts target Android26.
  That does not prove their linked dependencies/imports run on every older OS.
- Java already guards several newer APIs; voice capture explicitly requires29/
  Android10. Public restricted packaging is ARM64, so a32-bit OS is a separate
  native/packaging scope even on a64-bit-capable processor.

Prefer assessing one backward-compatible application rather than maintaining a
separate fork. For Android10/11 ARM64, a preliminary planning allowance is1–2
working days including focused automated/runtime/release checks, assuming no native
dependency blocker; this is not a measured duration or delivery commitment.
Android8/9,32-bit systems and older phones need a separate estimate after exact
OS/model information. Merely reducing `minSdk` and publishing is not sufficient:
VPN start/stop/reconnect, native loading, app startup, notifications, available voice
features and in-place signed update/data preservation must be checked. Versions and
rollout/rollback state remain unchanged; this is still an open incident.

## Device model follow-up

The reported model is Huawei nova3, with Android8.1 stated tentatively. No contact
name or private message is retained here. [Huawei's model specifications](https://consumer.huawei.com/hk/phones/nova3/specs/)
list EMUI8.2 based on Android8.1 and Kirin970 with Cortex-A73/A53 cores. This supports
an API27 compatibility investigation; it does not read back the actual installed
OS, supported process ABIs or app version from the affected handset.

If Android8.1 is installed,110's minimum31 prevents installation even from a browser.
Do not recommend uninstalling or clearing data to work around this requirement.
The earlier1–2-day estimate was conditional on Android10/11 ARM64 and does not apply
unchanged. For API27, allow several working days provisionally, subject to the first
native/API/runtime checks; no delivery date is committed. Initial priority is app
startup, VPN/native compatibility, reconnect/background lifecycle and preserved-data
updates. Standard Opus recording separately requires API29 in the current source;
full voice parity must be adapted/qualified or explicitly limited, not assumed.
Prefer one compatible APK if dependency gates permit. No client code/version,
catalog, production state or rollback state changes in this assessment.

## Authorized compatibility implementation and historical proof

This section supersedes the assessment-only status above, not its retained evidence.
The owner authorized implementation, then correctly recalled the older compatible
build. We restore the existing application; no separate package, downgrade or new
identity is required.

- Retained beta65: `com.familyconnect.app.friends`, code65, minimum26/Android8.0,
  target35, SHA256 `dfbdb5352b8c707fb77ff3d7392d8217f898aa8e999b6a0f52fad8172185778e`.
  `apksigner` verifies the same product certificate as110. Historical source includes
  minimum26; commit `37d16edf522bd485788c2bb507b6b86e92ff9465` introduces public107's
  Friends minimum31. Private owner106 was already31; this is not a claim that every
  intervening private build supported8.0.
- A disposable Android8.1/API27 emulator runs Android's actual archive parser against
  both immutable signed APKs:65 returns the expected package/code/minimum and one
  signer;110 returns null. This reproduces the compatibility failure without claiming
  to have inspected the affected Huawei or installed ARM64 APKs on x86_64.
- Candidate Friends minimum is27, scoped to the reported8.1 device, not a new promise
  of8.0 or32-bit support. No transport, identity, enrollment or server policy changes.
- New signed catalog payloads carry `min_sdk` derived from the verified APK's actual
  `aapt dump badging` `sdkVersion` value. Missing legacy metadata conservatively means31.
  Discovery/download/verification refuse unsupported SDKs without weakening package,
  Ed25519/APK signer, checksum, size, anti-rollback or downgrade checks. Transfer stays
  below100% until length/SHA verification; archive checking has a separate UI state.
  Read-only metadata extraction against the real signed65 also passes; no key is loaded.
- Android8–9 recording uses the existing native Codec2 path (default3200bit/s), not an
  unsupported Opus encoder. Existing explicit radio choices and peer-support consent
  remain. Opus recording requires10+; modern defaults are unchanged. RU/EN explain this.

### Local qualification, failures and limitations

All APKs here are disposable **CI/debug-signed x86_64 source candidates**, still
code110/`0.1.18-beta110`, never product releases. Native audio libraries are reused
from the retained accepted110 debug artifact, with local hash evidence. No private
signing key, user profiles or handset are used.

- Friends JVM:395 tests PASS. Focused release/catalog/source Python:60 tests PASS.
  Friends assemble and lint PASS; lint reports0 errors and57 warnings.
- API27 final UI/update/audio selection:22 cases,17 PASS/5 explicit skips. Includes
  startup/navigation/settings/routes, notification channels/privacy, voice UI,
  native Codec2 encode/decode/playback/capture and APK-verification rejection paths.
  Skips: existing active-device background delivery, unsupported Opus recording and
  three opt-in live/product-signed updater checks. None is counted as acceptance.
- API27 storage roundtrip PASS. Separate-process prepare → force-stop → same-version
  `adb install -r` → recover PASS, preserving synthetic protected identity/journal/
  outbox and recovering an interrupted AtomicFile write. Recovery uses a different
  process and cleans the fixture. This is not beta65→new product-signed upgrade proof.
- API35 same candidate UI/update/audio/storage selection:23 cases,19 PASS/4 explicit
  skips (active-device delivery and the three opt-in updater checks). Modern Opus
  capture/playback passes. Both emulators are stopped; synthetic evidence remains local.
- Initial API27 runs exposed two test-only assumptions: AtomicFile uses `.bak` rather
  than modern `.new`, and WindowInspector is API29+. Tests now assert recovery on both
  implementations and inspect resumed Activity windows. No assertion is removed to
  mask product failure; repeated storage/UI checks pass. Early failure logs retained.
- Reviewed source hash pins are updated only for these updater/voice/resource changes;
  accepted UI/MESH reference guards remain. CI adds API27 native transport lifecycle,
  storage/control conformance and Friends tests **in addition to**, not instead of35,
  preserving separate logs/screenshots. This new exact-source CI has not yet passed.

### Remaining release gate and rollback

Pending: exact-source Android platform CI including API27 native transport/control,
ARM64 restricted/MESH runtime qualification, and a product-signed old-to-new in-place
upgrade preserving identity/data. Actual Huawei/region field recovery remains unknown;
local emulator UI/audio checks are not VPN/production acceptance. An eventual release
must use a new version greater than110, exact downloaded/verified CI artifacts, offline
signing and catalog sequence greater than5, plus corresponding guides/public readback.
Never distribute these CI-signed APKs or replace110's immutable bytes.

No rollout or runtime rollback is performed: installed/public/invitation versions and
catalogs stay as listed above. Source rollback can revert this bounded patch without
modifying stored identities or production; a future public rollback must be a higher
version, never uninstall/clear data or downgrade the catalog. Private logs, screenshots,
APKs and native hashes stay ignored under `state-client-build/android81-20261103/`.

Source checkpoint `446260eebce3bc7b006f993dfa42444cdc1c85c7` is committed and pushed
to `origin/main`; remote branch SHA matches. Exact-source
[Client builds41610914956](https://github.com/Joker20380/family_connect/actions/runs/41610914956)
is IN_PROGRESS at this readback, not CI acceptance or publication. Five other
source workflows are also in progress. Existing unrelated dirty documentation and
private evidence are preserved outside this commit. Documentation links and whitespace
checks pass for the changed report/code map; no physical device remains connected.
