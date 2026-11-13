# Android125 — public promotion, 13 November 2026

## Published — verified live

At **13 November2026 14:26:54.985103UTC**, the qualified immutable Android125 became
the default public/invitation/updater release, with optional signed catalog8.
This is a production publication, not a rebuilt candidate or a claim that every
user has installed the update. The owner already runs the identical125 APK; this
operation performs no phone installation, uninstall, data clear or identity change.

- [Download Android125 APK](https://185.251.89.19:8443/downloads/FamilyConnect-Test-0.1.18-beta125.apk).
- [Corresponding audio source](https://185.251.89.19:8443/downloads/FamilyConnect-Android-0.1.18-beta125-audio-source.tar.gz).
- Existing users: Settings → Check for updates → Install125, or the invitation link;
  install over the existing app without deleting data. Reconnect VPN if necessary.
- Signed catalog8 expires **11 February2027 14:20:11UTC**; optional policy remains
  minimum_supported_version1, mandatory_after0. This does not grant VPN access.

`scripts/verify_public_invitation.py` PASS using verified HTTPS: full125 APK bytes,
signed v2/legacy125 discovery, both `/i/` and `/invite/` byte equality and exact CSP.
The unchanged Windows0.2.16 installer/catalog12 is also checked by full download:
49,955,605 bytes, SHA256
`491a731edbf80887122844bebcccb8741e701b03816202f9a9b77c77855e8a65`.
Additional independent full downloads at14:29:18.623146UTC confirm the125 audio
archive and retained113 APK (50,273,696 bytes, SHA256
`6078d0610272c5eb1b8008d330f9e646163b90b89df180b4bd56fd8ae4edc094`).
Fresh read-only journal/current-file reconciliation at14:34:21UTC confirms the
completion marker and all four live metadata hashes match the published receipt.

Only one nginx HUP is issued after old/new configuration validation. No backend or
transport process is restarted. Protected records/fingerprints remain unchanged:
64 devices,118 invites,52 chat bindings,2 restricted grants,1 paid subscription,
4 paid events and1 service sender. Support configuration and gateway catalog are
unchanged. Publication pre/post RU watcher/AWG/TCP/HTTP PIDs are identical, all
active/success with NRestarts0. The HTTP PID had changed before this release preflight;
this is not a claim of continuity since the earlier RU recovery or a cause fix.

| Published metadata | SHA256 |
| --- | --- |
| Signed v2 catalog8 | `28a9df08d2b10d48457aac67a52a197a7f7caa168ad77feb000781d154c369ea` |
| Legacy discovery125 | `f3db0d127f3460dabd30f8fea801aace8c0c04a079549eefca2ad28d3d0bad87` |
| Invitation HTML | `ba8f10152fa8520282f1844e08a4f22ba86a7e93f31928281b3f10fea37994a5` |
| nginx configuration | `22e21e0255c7c216c2a20ef7b4e79d82e92d7df1fd16b136fd60fceadd0c5dbe` |

## Preparation evidence — prior to activation

Owner requests promotion from the default public113 to125. The initial verified
HTTPS/server baseline was113/sequence7, with no conflicting125 asset or publication
journal. Prepared source metadata alone did not establish rollout; the live receipt
above supersedes that initial state.

The existing qualified125 is reused without rebuilding or re-signing the APK:

| Item | Exact identity |
| --- | --- |
| Android source | `b293f9ac5f2cc6fe2d11777dae97f4423e2d073a` |
| Hosted run/artifact | `43048235831`, attempt1 SUCCESS / `13868911920` |
| Downloaded CI ZIP SHA256 | `4a6bcbfabbafa37d3be5d4793d4693f1f03997f7f68f9b06b0d517e5c41ded62` |
| Package | `com.familyconnect.app.friends`,0.1.18-beta125/code125 |
| Platform | ARM64 / Android8.1+, minSDK27 |
| Product APK |50,470,304 bytes; `f1c5bf578a5ca1e8e864a60fa9ab33249807e22c4552b5da984d126720e5740c` |
| APK certificate SHA256 | `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a` |
| Audio corresponding source |7,601,671 bytes; `249b86d49612b716d69e25d554579213a32cbb74d7167d652f6808f60f618a89` |
| Published signed catalog |sequence8; `28a9df08d2b10d48457aac67a52a197a7f7caa168ad77feb000781d154c369ea` |

CI run/source/artifact identity is freshly checked. The retained ZIP matches its
GitHub digest, and every unsigned APK payload member matches the already signed
artifact; added entries are signing metadata only. Fresh package/ABI/non-debuggable,
original signer and16KiB ZIP alignment checks PASS. Audio source matches every
corresponding-source member of the exact CI ZIP, with duplicate/path/member-set
checks; only then are the identical older source-archive bytes reused at a new125 URL.

Retain the accepted API27/API35 preservation, admission-renewal and isolated messaging
checks; no new Android code requires rerunning them. The owner phone already has
these exact125 bytes installed over123 and confirmed support exchange with the user
tunnel OFF. This does not claim that every public113 device has installed125 or that
the113→125 transition has been physically observed on every model.

Catalog8 is signed locally by `scripts/sign_update.py`, with the existing offline
root and optional policy: minimum_supported_version1, mandatory_after0. No key goes
to Git, CI or server. No entitlement, admission, gateway policy or client identity
change accompanies APK availability. Desktop versions remain unchanged.

## Publication and recovery gate

Targeted metadata/signature/invitation regressions:56 PASS, no skips. Guarded
immutable APK/audio publication, invitation/CSP and legacy/v2 promotion, independent
verified-HTTPS full artifact/source/hash readback and protected-state comparison all
PASS. No new Android code is introduced, so the qualified hosted run and physical
owner acceptance are reused rather than rebuilding or reinstalling.
Final metadata regression rerun:56 PASS in0.20s. Public documentation check:
795 files/5029 local links, zero errors; whitespace check PASS. These local link
counts do not substitute for the independent public HTTPS checks recorded above.

Private evidence/staging: ignored `state-client-build/android125-publication-20261113/`.
Completed RU journal: `/root/fc-android125-publication-20261113`. Preserve prior113
metadata/configuration, all immutable downloads and current support/paid state.
After an uncertain write, inspect that same journal/current hashes instead of
replaying publication. Withdraw routes/advertisements with guarded nginx validation;
do not restore the product DB, uninstall clients, clear data or force a downgrade.
Clients that saw sequence8 reject7: a corrective catalog needs a higher sequence,
and changed APK bytes require a new versionCode with the same original signer.

The journal retains `html-before`, `config-before`, `legacy-before`, `signed-before`,
intent and fsynced completion receipts. Private local evidence includes the driver,
preparation/publish receipts, original artifact checks, `public-readback.json` and
`public-source-and-113.json`; none is committed as raw private evidence.

Local system/data space is1.8/2.6GiB free before and after. Existing artifacts are
reused; no build, cache cleanup or data deletion is needed. Accepted APKs, keys,
logs, backups and rollback material are preserved. RU/EN installation, update and
support guides plus STATUS/PLAN and release routing now identify public125 separately
from the already installed owner125 and historical candidates.

Separate open gates remain: public Android announcement receipt, cold no-cache
restricted bootstrap/recovery in field networks, sustained VPN acceptance, RU
resource-pressure cause/replacement, subscription notifications/payment partner and
later desktop acceptance. Public promotion does not close them.
