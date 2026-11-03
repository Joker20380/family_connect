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

## Beta111 release continuation

The owner requests proceeding. Source reserves code111/`0.1.18-beta111`, minimum27,
target35 and unchanged ARM64/package/signing identity. **Candidate only: not yet built
from accepted hosted CI, product-signed, installed on a handset or distributed.**
Public/invitation110, Android sequence5 and all desktop versions remain unchanged.
Public download links intentionally continue to point at110 until an accepted111 exists.

At the continuation readback,446260e's Client builds41610914956 had passed source,
restricted race/contracts, native build and Gradle/JVM/lint gates and was running the
API35 emulator. It was not a complete PASS; version111 needs a new exact-source run.
Readiness wire contract41610914917 passed. Other triggered workflows expose pre-existing
failures: Messenger41610914915 has22 failures because tests omit mandatory Session
platform/version arguments introduced in107; phase0/Linux-control historical fixture
packaging applies the current HTTP builder to older source without the newer ingress
file. These are not disguised as green, repaired by weakening checks, or proof of an
Android8.1 regression. No unrelated production behavior is changed in this task.

The retained110 unsigned ARM64 APK's12 native libraries were read-only inspected against
Android NDK API27 system exports: no unresolved strong imported symbol in the combined
packaged/system export set. This is a reference static compatibility audit, not proof
of dynamic loading, dependency-namespace order, VPN traffic or exact111 native behavior.
Private receipt: `state-client-build/android81-release-20261103/arm64-api27-reference.json`.
The unchanged source/native pins and eventual111 bytes still require normal qualification.

Planned next checks are the exact111 platform run (API35 and27), downloaded unsigned
package/provenance/SDK/native/alignment verification, and a synthetic versioned in-place
upgrade with identity/journal/outbox preservation. Existing signing/catalog/immutable
publication guards remain; actual Huawei recovery and product-signed field upgrade are
not declared PASS from an emulator. Rollback before publication is source-only; after
publication use a higher version/sequence, preserve old artifacts and never clear data.

### Versioned local upgrade PASS; hosted qualification pending

Source `99c155dd7ab64e38be607b01d8d7b73384da8448` is pushed with matching remote SHA.
Its [Client builds41613303779](https://github.com/Joker20380/family_connect/actions/runs/41613303779)
is IN_PROGRESS. The earlier446260e run passed API35 runtime/control and reached API27,
then normal branch concurrency cancelled it for111; it is superseded, not a full PASS.

Local exact111 source assembles with the existing disposable CI signer and reused
accepted audio natives;395 JVM and88 focused Python tests PASS, lint/assemble PASS.
On the isolated API27 emulator, a110 CI-signed predecessor creates the synthetic
protected identity/journal/outbox and an interrupted write. After force-stop,
`adb install -r` upgrades to111, retaining the package UID. The recovery test runs
in a distinct process, verifies the same protected state and cleans all its fixture
material. A further22 UI/update/audio cases yield17 PASS/5 documented opt-in or
unsupported-feature skips. No new enrollment, live service or user identity is used.

This is a real versionCode increase in a **synthetic x86_64 CI-signed test**, not an
immutable product beta65→111 ARM64/Huawei acceptance. The local APK is not for users:
SHA256 `582ba34b083a78e505a06cc53d8a9c054f2f1925699cf869e9c27ebf2b598686`.
Receipt/screenshots/logs remain ignored under `state-client-build/android81-release-20261103/`.
No product signing or public distribution has occurred; public110/sequence5 unchanged.

### Hosted API27 failures and bounded test repair

[Client builds41613303779](https://github.com/Joker20380/family_connect/actions/runs/41613303779)
on99c155d FAILED, not accepted. API35 debug51 cases yielded28 PASS/23 explicit skips;
API35 Friends22 yielded18 PASS/4 skips. API27 debug51 yielded25 PASS/24 skips/2 failures.
API27 Friends and final ARM64 packaging were NOT_REACHED. The retained API35 Friends
XML must not be counted as API27 evidence. Artifact13222275099 runtime diagnostics
SHA256 is `ca0498375acd70754410711e61e951c161355eff87a82b1a17f6606ba0537f0f`.

Both failures are test API assumptions, repaired without changing product behavior:
`AutoTcpAddressRuntimeTest` now always checks the real tunnel interface kernel MTU1280,
and also checks LinkProperties MTU when nonzero (Android8.1 reports unknown0).
`ControlSelectionRuntimeTest` reads its asset through a buffered stream instead of
the unavailable InputStream.readAllBytes; manifest SHA, encrypted selection, restart
and rollback assertions remain intact. No test is skipped to hide these failures.

Both repaired tests PASS on isolated API27 and35 (four runtime executions), with88
focused Python regression checks PASS. Initial local retries exposed a missing
disposable-build flag and a stale generated Python environment symlink; correct CI
flags and regeneration of that disposable build output resolved setup, not by weakening
checks. Logs are retained privately under `state-client-build/android81-release-20261103/`.
Both emulators are stopped; no handset, production account or service was used.

Next gate is a fresh complete platform CI run on this repaired source, followed by
verification of its exact ARM64 artifact and existing offline-signing/publication gates.
Version111 remains reserved, not released. Public/invitation110 and catalog5 remain
unchanged; no rollout or runtime rollback. Actual product-signed Huawei recovery is OPEN.

## Beta111 exact-source platform and artifact acceptance

Source `40e6c6c88c1d51c96736ded125a1b8060bdd4d26` is committed, pushed and remote-verified.
[Client builds41618639307 attempt2](https://github.com/Joker20380/family_connect/actions/runs/41618639307/attempts/2)
PASS includes API35 and27 real WG/AWG/TCP/Auto lifecycle, encrypted control selection,
process-restart storage recovery, Friends UI/audio and final unsigned ARM64 packaging.
The400 debug and395 Friends JVM tests pass. UI review confirms synthetic load rendering,
Amsterdam1/2 labels, and Codec2 on8.1 versus normal Opus on15; these screenshots do not
assert current production node load.

| Runtime | Cases | PASS | Explicit skips | Failures |
| --- | ---: | ---: | ---: | ---: |
| API35 debug | 51 | 28 | 23 | 0 |
| API35 Friends | 22 | 18 | 4 | 0 |
| API27 debug | 51 | 27 | 24 | 0 |
| API27 Friends | 22 | 17 | 5 | 0 |

Variant/opt-in skips are retained, including live/product-signed update checks and
unsupported Opus recording below29. Attempt1 failed before27 on an API35 automatic-TCP
IPv6 connect timeout; its diagnostics ZIP13222209779 has SHA256
`247acdae8f32d81769aa76eb75388bb1df4cb228fcb34a9aa9bfa98697dd338b`.
The two repaired test cases passed and ran after that failure. A single full failed-job
rerun on the unchanged source passes; the intermittent timeout's cause is not proven.
No timeout increase, test omission, forced success or product change was used.

Downloaded artifacts from the accepted second attempt are checked against GitHub digests:

| Artifact | ID | ZIP SHA256 |
| --- | --- | --- |
| ARM64 release | 13225731676 | `a0fc47c4d4bd20ce3d892f74dd2ccff07bedf4d860b4e0ede0894c8035fbf667` |
| Runtime matrix | 13225641948 | `1fcbea1dca705fd3c2ca16c42b97a48a0a66b9edd805cc7c2c06028640cca654` |
| UI | 13225666835 | `392ea719d3c2d196d8ebbaca6602e35af1fa7637552281643c8e5d002dd11d68` |
| Debug/JVM/storage evidence | 13225468995 | `1a9eca1ba3c24e427be5a141554b7572e27d1c1357af81b0be94926ec5149f64` |

Unsigned APK: `FamilyConnect-Test-0.1.18-beta111-unsigned.apk`,50,246,229 bytes,
SHA256 `16876be250d69c8632de0c24c0ebbb6e497ac9ca584ad94d61ad770a94019b94`.
Package `com.familyconnect.app.friends`, code111/minSDK27/target35/ARM64-only,
non-debuggable, deliberately unsigned. APK/native source commit/tree, AWG/Xray/Codec2
pins, all12 native libraries, ZIP/ELF16K alignment and corresponding source/license
payloads verified. These are the accepted signing inputs, not distributable binaries.

Next: sign that exact input with the existing product certificate using the local
protected vault, then sign an increasing Android catalog and publish immutable111.
No signing secret is in CI/server/Git. At this checkpoint no product signing or rollout
has happened; public/invitation110/catalog5 and desktop versions remain unchanged.
Do not uninstall/clear data or replace110 bytes. Physical Huawei/ARM64/MESH and actual
product-signed preserved-data upgrade remain NOT_RUN; unrelated broader CI failures
listed earlier are not represented as fixed by this platform PASS.

## Beta111 publication and readback

**PUBLISHED,3 November2026; affected-phone recovery remains OPEN.** The accepted
40e6c6c/CI41618639307 attempt2 input is signed offline through the protected local
vault with the existing product certificate. No key/password is exported to disk,
server, CI or Git. All unsigned APK entries are byte-identical after signing;
package/version/minimum SDK/ABI/signature/16K alignment PASS. The exact signed ARM64
archive is also accepted by Android8.1/API27's package parser with code111/minSDK27
and one signer. This is archive acceptance, not ARM64 execution on the x86_64 emulator.

- [APK111](https://185.251.89.19:8443/downloads/FamilyConnect-Test-0.1.18-beta111.apk):
  **50,265,448 bytes**, SHA256 `32d5f4f1d050be83dc192ae632cc0603cb4150b3c00df3b594bc22cef9105607`.
- Product certificate SHA256: `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
- [Signed Android catalog6](https://185.251.89.19:8443/updates/android-friends-v2.json):
  SHA256 `ca3e6c630d086379ab79055e1b83ac7217165ee9461033b19ce0ca3f817a41df`,
  `min_sdk:27`, minimum supported code1, mandatory-after0; optional, no forced install.
- [Corresponding audio source/licenses](https://185.251.89.19:8443/downloads/FamilyConnect-Android-0.1.18-beta111-audio-source.tar.gz):
  7,601,671 bytes, SHA256 `249b86d49612b716d69e25d554579213a32cbb74d7167d652f6808f60f618a89`.
  Archive reused only after every member matched the exact accepted111 CI source.

The server publication uses a fresh guarded baseline and an exclusive recovery journal,
adds immutable APK/source routes, updates invitation111 and its exact script/style CSP,
then publishes matching legacy/signed catalogs. One nginx reload; zero backend restarts,
new invitations, paid mutations or phone actions. Protected product rows and gateway
catalog4 remain unchanged. Readback confirms all five published files and nginx config.
`scripts/verify_public_invitation.py` PASS checks both `/i/` and `/invite/`, exact HTML/CSP,
Android signature/sequence/full APK bytes, and unchanged Windows0.2.16/catalog12/full
installer bytes. Additional full HTTPS reads verify111 audio source and retained110 APK.
No regional-network or affected-phone recovery claim follows from operator HTTPS access.

Publication metadata regression selection88 PASS. A local preparation retry corrected
the apksigner Java PATH before catalog creation; no server mutation occurred on that
failed preparation. Earlier failed CI attempts and broader unrelated CI failures remain
documented above. The current source release, public download, updater and invitation
all identify111; actual handset installation is NOT_RUN. Linux public0.2.11/owner
0.2.12~l03.2.13 and Windows0.2.16/catalog12 remain unchanged.

Recovery journal: `185.251.89.19:/root/fc-android111-publication-20261103`, including
pre-publication HTML/nginx/catalog backups and immutable completion receipt. Before
catalog publication, guarded failure restores invitation/routes without altering the
catalog; no rollback was needed. After catalog6 exposure, never reissue5 or substitute
different111 bytes: use a newly signed higher sequence and, for an APK repair, code112+.
Retain110 for historical/manual recovery only; it does not run on8.1. Never uninstall,
clear data, replace identities or use another signing certificate to recover an update.

Remaining incident gate: confirm the Huawei's actual Android/ABI/old beta; install111
over the existing app (browser APK if the old updater fails); verify retained activation,
keys/history and ordinary VPN behavior. On Android8.1–9 voice uses existing Codec2 with
peer confirmation; normal Opus recording still needs10+. Actual Huawei/ARM64/MESH and
product-signed old-to-new preserved-data operation remain unverified. No unrelated fleet
successor, automatic live canary or admission expansion starts from this release.

Changed public-guide/report links and whitespace checks PASS. The required whole-docs
scan covers729 files/4511 links and still reports two pre-existing historical anchor
errors: STATUS's October27 `evening-readback--1736utc` and the October24 source
checkpoint's October23 `linux-user-chat-admission-and-existing-exit-handoff-24-10-phase22`.
These unrelated historical entries are preserved, not silently repaired or reported PASS.
