# Android106 controlled paid beta — readiness, 2026-10-27

## Subsequent Beta-0 scope decision

Owner subsequently limited Beta-0 to10 existing activated identities on exact106
or new106 installs, private verified handoff and manually confirmed payments.
Older-version upgrades and external acquiring are excluded from this first scope,
not newly accepted. The historical gate table below is retained; current Beta-0
scope, implemented paid server model/operator, tests and remaining launch blockers
are in the [PAID-ENTITLEMENT-MVP checkpoint](2026-10-27-android106-paid-entitlement-mvp.md).
No APK change/deployment/real paid enrollment. Linux remains PAUSED/non-blocking.

## Owner decision and result

**Current critical path: ANDROID-CONTROLLED-BETA. Preparation checkpoint DONE;
controlled paid launch BLOCKED on the finite gates below, not on desktop parity.**
Input main: `c3200edda39c64e7a2764bacbb78d568fd68a031`.
Existing unrelated uncommitted ops/client-guide work is preserved and excluded
from this source checkpoint. No Android source/version change, rebuild, signing,
publication, payment collection, server-policy mutation or production-device action.

**ANDROID106-MESH-FIELD-1 = PASS, owner accepted27.10.** Real external user,
real whitelist-restricted network, ordinary application use, MESH confirmed.
This is the owner's field acceptance, not a newly instrumented traffic test.
Exact successful-use time/traffic counters are not supplied. Do not transfer this
PASS to Linux/Windows, complete upgrade preservation, paid expiry or general CI.
Linux installed acceptance resumes only as a separately authorized stream after
controlled beta; historical evidence/NEXT records remain historical, not active work.

## Linux .11 frozen — no retry

- L04.2-R3 SOURCE GATE = **DONE / review accepted**.
- L04.2-R3 .11 CONSTRUCTION = **DONE / frozen internal candidate**.
- L04.2 = **PAUSED / NON-BLOCKING DESKTOP ENGINEERING**, not DONE.
- Version: `0.2.12~l03.2.11`.
- Candidate: `570a5515173d66b9a25cd9f01f76e72f492a41acb1f341ee95368aac62e78252`.
- System: `34b27cb97abb149b9a59f7ea4ad2ea2e9b79aab5e4e9345c064b6a98d20e5db8`.

| Artifact | Bytes | SHA256 |
|---|---:|---|
| DEB | 56148076 | `1976d2bfe13cc0efc421e7cfcdf52bd301ed725168e743c0b32d372422ab062f` |
| AppImage | 58116600 | `92ff5a79f61d8d29e32596d8333d0880f1fe60803d831de418cad63952517a5d` |
| Legacy six-file archive | 114647 | `8adeda8e6af059100d1254c40db186fd4d8abd7812090c33af38271c575c3a70` |
| System archive | 49251389 | `4794ae4d8bb0b794aced081b4c330595e18aeaf334ba6b787c248daaa5725ae4` |

Source/native/system/reference gates PASS;46 candidate/reference tests PASS.
DEB/AppImage embedded candidate/system equality PASS; inner product container
exit0. Outer launcher exit1 only on overwriting root-owned `embedded.json`;
product defect not established. Installed package acceptance and live P0/P1/Auto
remain NOT_RUN. Linux MESH is not installed-accepted; overall CI is not green.

All four sizes/hashes rechecked without extraction/execution. DEB/legacy already
0444, AppImage0555; standalone system archive was root-owned0644, now0444 with
unchanged bytes (single-file chmod only). Files remain local/internal/read-only.
No harness replay, receipt rename, launcher repair, rebuild, pkexec, installation,
rollback, retained Linux identity use, P0/P1/Auto, AppImage lifecycle, L05/L06 or
Linux publication. No new Linux retry/checkpoint.

Existing **D02/CI technical debt** now records
`PACKAGE_HARNESS_EMBEDDED_RECEIPT_FILENAME_COLLISION`: future inner receipt and
outer summary must use different filenames, or the outer summary must use a
separate user-owned evidence directory. Not an Android launch blocker.
[Historical R3 evidence](2026-10-27-linux-readiness-cause-preservation-l04-2-r3.md)
and [exact delivery manifest](2026-10-27-linux-readiness-cause-preservation-l04-2-r3/candidate-delivery.json)
remain authoritative for construction, not installed acceptance.

## Exact accepted Android artifact

Selected by the [accepted delivery receipt](2026-10-22-private-field-delivery-receipt.json),
[106 acceptance report](2026-10-23-wifi-resume.md) and
[pinned reference](../../clients/shared/android106-reference.json), not timestamp
or filename. APK manifest read with aapt2; signature freshly verified with apksigner.

| Property | Verified value |
|---|---|
| Local/internal path | `state-client-build/owner-diagnostic106-20261022/delivery/FamilyConnect-0.1.18-beta106-recovery.apk` |
| Filename | `FamilyConnect-0.1.18-beta106-recovery.apk` |
| Bytes | 56093664 |
| SHA256 | `242855c43e889e708234ce2f687fa02d37bccb1eee408904f09216b6abd8f020` |
| Package ID | `com.familyconnect.app.friends` |
| versionName / versionCode | `0.1.18-beta106-recovery` /106 |
| Signing certificate SHA256 | `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a` |
| Build type | `privateBeta`, non-debuggable; `PROVISIONING_TEST_SEAM=false` |
| Platform | arm64-v8a, min API31 / Android12+, target API35 |
| Native restricted library SHA256 | `37ba4fac656811dd979688a274f45aed85a3aa567f1fafb3987a81c020fa91f1` |
| Source base commit | `f5240994869826c6a28f59e58e38256c688cf6eb` plus retained derivative; NOT an exact clean single-commit106 build |
| Exact source inventory SHA256 | `8574228fc809fdbd67b3d92680e09c979fe930599a47e4ed1b47fd30f872ed0c` —2073 files freshly matched |
| Source delta identity | `6ceec4025ccdfb08538c69de0c85d343ced444a378a1cb0caef52a5a396350a0` |
| Native source inventory identity | `1a6f52a91dc2482f67992f28a2b46dcdf2c3c0bc56f8f0665a0dd469943584af` (accepted reference pin) |
| Native build metadata SHA256 | `f50ee0ee2b8a4ad464de65ad159de366fcb9e31d445b0c7c28f2fc8cb3ecbeb2` — freshly matched |
| Reference JSON SHA256 | `bbf115bd257abea956f6b41ab1617a5b2b371a8a7073c2daba8255a81143cbbb` |

All12 packaged native libraries equal the accepted105 predecessor. Embedded
research/derivative metadata is retained, not reinterpreted as a clean main build.
An exact standalone106 Git source commit is **not available**; provenance is the
base commit + pinned complete snapshot/delta, not current main. No source capsule
or binary is added to Git. Historical219 JVM build checks remain historical;
no new platform-CI/full-repository PASS is asserted.

### Multiple code106 artifacts reconciled

Discovery inspected APK metadata across readable local APKs, not just filenames.
Two unrelated Linux Go-cache files were unreadable; they are not APK candidates.

| Local artifact | Bytes | SHA256 | Disposition |
|---|---:|---|---|
| Selected delivery APK above | 56093664 | `242855c43e889e708234ce2f687fa02d37bccb1eee408904f09216b6abd8f020` | Valid accepted signer/reference |
| `owner-disconnections-20261022/raw-entry-20261023T051103Z/installed-0.apk` under `state-client-build/` | 56093664 | `242855c43e889e708234ce2f687fa02d37bccb1eee408904f09216b6abd8f020` | Byte-identical retained installed copy; not a second release |
| `build/android/app/outputs/apk/privateBeta/app-privateBeta-unsigned.apk` under the106 directory | 56072561 | `551c4e02d19aa04901e73200a344f35becc3cee412f85a580f1165ed7c8db272` | Final unsigned input, not installable accepted delivery |
| `build-initial-regression/android/app/outputs/apk/privateBeta/app-privateBeta-unsigned.apk` under the106 directory | 56072453 | `2e6c0aa131e3e55a4100d064bf7bb4760f35d7aa039697e622d521337b249d2e` | Earlier unsigned regression build, rejected as candidate |

All four manifests say106; only the accepted signed hash qualifies. No unresolved
candidate ambiguity. Older build evidence is not deleted or relabelled.

## Administrative field readback — sanitized

Private lookup uses only the owner-specified Support ID as an administrative
selector. Public report deliberately omits that ID, canonical device/key hashes,
invite values and person-level data. Private mapping and receipts remain in ignored
`state-client-build/android-controlled-beta-20261027/`, mode-restricted locally.

Authoritative RU registry opened SQLite `mode=ro`, `query_only=ON`; current running
HTTP process admission configuration read without dumping environment/secrets.
Fresh readback **2026-10-27T11:42:41Z**:

- One canonical identity/public-key row and one invite association; no duplicate
  for that canonical key/device in the queried registry. No claim about every
  identity a person might own or uninspected client-local state.
- Activation active; device/invite revoked=false. Admission v2 `all_activated`;
  MESH eligible, no explicit grant row required. No new invite necessary.
- Last support-request observation remains code84,17.10 12:42:49UTC, but **newer
  authenticated readiness ACK26.10 21:00:50UTC reports106,
  `0.1.18-beta106-recovery`, READY, orchestrator_usable=true**.
- That readiness receipt's expiry was26.10 23:32:15UTC. It proves a historical
  successful readiness/import observation, not current live-session health or
  subscription expiry. Current APK bytes/signer on the device are not attested.
- Last successful ordinary MESH use is owner-confirmed FIELD-1; precise time
  remains unknown. ACK is not silently substituted for a successful VPN session.

Writes0; no entitlement change, identity creation, revoke/reissue, new invite,
remote client upgrade or production-data export. Existing working access preserved.

## In-place update readiness

Target user action remains **«Установить обновление и открыть приложение»**.
No uninstall, clear-data, new invite or re-enrollment is proposed.

| Required property | Evidence / boundary |
|---|---|
| Same package/signer, increasing code | Fresh APK comparison105→106 PASS; retained84 artifact is not target-installed signer attestation |
| No uninstall/clear-data | Historical authorized owner105→106 `adb install -r` PASS; no such command in this checkpoint |
| Identity/readiness persistence | Synthetic actual106 Java classes: restored105-style vault and synthetic ControlIdentity survive three new readiness owners; persisted vault bytes/context unchanged |
| Activation/entitlement | Production read-only activation/eligibility still active;49 synthetic backend tests PASS, not a full Android package-update test |
| Settings/history/Keystore | Full old-state→new-APK preservation NOT_RUN; not proved by in-memory vault fixture |
| No repeated invite; MESH after update | Historical owner105→106 + owner-accepted external106 field result positive; exact controlled upgrade chain still needs fixture evidence |
| Three application launches, migration runs once | Three synthetic readiness-owner reconstructions PASS; three installed Android launches NOT_RUN, no full migration PASS |
| Authorized upgrade device | `adb devices -l` empty; no authorized physical/emulator upgrade target available in this session |
| Overall in-place gate | **PARTIAL / BLOCKED for launch**, not proof of incompatibility or product defect |

The target's newer106 ACK means stale84 cannot be used to prescribe84→106 now.
If106 is already installed, handing over the same106 is not an increasing-code
update. Confirm the actual starting installation in the authorized fixture;
any future106 successor requires a separately authorized higher versionCode.

Synthetic fixture uses no production identity/keys and no external network.20 JVM
tests PASS: new three-cold-owner check + retained ReadinessRefreshTest,
ReadinessProductTest, DiagnosticRecordBudgetTest. No APK or Android source rebuilt.
Full fixture gate must seed representative identity/activation/entitlement,
settings/history with synthetic data, install exact APK in place, compare state,
open normally three times and verify MESH/no repeated migration or invite. Use
authorized test infrastructure; never remotely modify the external user's phone.

## Subscription and entitlement gaps

49 targeted tests PASS under exact control + identity lockfiles (27 pins checked):
`test_restricted_activation_policy.py`, `test_restricted_activation_http.py`,
`test_support_ids.py`. Disposable offline container, loopback HTTP and synthetic
identities only. Initial minimal mount missed `clients`:3 collection errors;
only mount scope corrected, then49 PASS/0 FAIL/0 SKIP. Failure log retained.

This proves existing activation→MESH admission automation and revocation checks
at challenge/fetch boundaries, **not paid subscription automation**. The passing
`test_legacy_expiry_is_not_new_policy_entitlement_expiry` explicitly confirms that
v2 all_activated ignores legacy grant expiry. `control/friends/access.py` states
there is no payment/entitlement-expiry condition. Separate product entitlements
are not evidence of a live Friends billing integration.

Required paid-state contract, proposed here for the next bounded gate (not deployed):

| State | Required access decision |
|---|---|
| trial | Allow only until recorded trial end; no renewal into unbounded free access |
| active | Allow during paid period tied to audited activation/payment event |
| grace | Explicit bounded grace_until and approved policy; not indefinite |
| expired | Deny renewal/new admission and remove effective entitlement within an agreed, tested bound |
| revoked | Deny irrespective of trial/payment/grace; reconnect/cache/renewal must not resurrect access |

Missing: authoritative subscription state machine, idempotent payment→existing
identity activation audit receipt, authenticated payment/refund/cancel handling,
bounded expiry/revocation enforcement for cached credentials/ongoing sessions,
and failure/replay/reconciliation tests. Receipt should bind a non-secret event
reference to previous/new subscription state, period, entitlement decision,
timestamp and outcome; raw payment/customer secrets stay out of Git/diagnostics.
Short-lived crypto expiry and existing deny tests are not subscription enforcement.

## Download and rollback

Accepted106 is an **internal signed handoff**, at the exact local path above.
No verified public106 URL or controlled-cohort delivery receipt exists here.
Client's signed update channel is `android-field`, index
`https://185.251.89.19:8443/updates/android-friends-v2.json`.
Fresh HTTPS GET + offline public-anchor signature/expiry verification PASS:
index still offers **0.1.18-beta60/code60, sequence1**, not106. Targeted public
downloads and invitation-page versions are separate; neither is changed or
claimed rolled out. Legacy parser requires `-beta<number>` names, so do not
silently insert `-beta106-recovery` into that catalog or rename immutable bytes.
Private manual delivery can be chosen for beta; it still needs an approved,
verified download/handoff path and two-action user-flow test.

Saved rollback predecessor:
`state-client-build/owner-pressure105-20261022/delivery/FamilyConnect-0.1.18-beta105-recovery.apk`.
Package `com.familyconnect.app.friends`, version `0.1.18-beta105-recovery`, code105,
56093664 bytes, SHA256
`91ba2d6e4cb6d3c789e4921df96b79ea196d42bc602bc72ea727fa1489aef2a3`;
same certificate SHA256 as106, signature freshly verified. Both APKs retained.
**Saved105 is not a proven safe in-place106 downgrade.** Normal Android version
checks prohibit that downgrade; uninstall/reset/forced downgrade is not a remedy.

Manual incident procedure: stop new paid activations/distribution; preserve
redacted evidence and working identity/state; keep unaffected installs unchanged;
operator prepares a separately authorized higher-code same-signer correction from
the known-good snapshot, validates synthetic restore/update, then performs bounded
handoff and verifies launches/MESH. No such successor is built now. Tested
non-destructive rollback/recovery remains a launch blocker, not an automatic
instruction to roll back current users or server policy.

## Minimal controlled launch gate

| # | Gate | Readiness |
|---|---|---|
| 1 | Exact signed Android APK | PASS, exact106 above; composite source provenance disclosed |
| 2 | In-place update | PARTIAL; full APK/state/three-launch fixture outstanding |
| 3 | MESH entitlement automation | PASS existing activation/admission; paid mapping BLOCKED with4–6 |
| 4 | trial/active/grace/expired/revoked | BLOCKED; model not implemented/accepted in live Friends path |
| 5 | Payment activation audit receipt | BLOCKED; no payment integration/accepted event receipt |
| 6 | Expiry/revocation actually disables entitlement | PARTIAL existing revocation; paid expiry/session-bound enforcement BLOCKED |
| 7 | Support ID and diagnostic export | PASS bounded existing source/owner evidence and tests; no public identifiers |
| 8 | Rollback APK | PASS saved/verified105; operational safety gated by13 |
| 9 | Download/update path | BLOCKED for launch; private file exists, approved cohort handoff and user-flow verification missing |
| 10 | Terms/privacy/subscription text | BLOCKED; [privacy notes](../privacy.md) explicitly are not complete commercial policy; price, periods, cancellation/refunds, operator contact/retention require owner approval |
| 11 | First limited group | BLOCKED pending explicit opt-in roster/cap and rollout owner; old P1 engineering cohort is not paid consent |
| 12 | Monitoring | BLOCKED pending bounded cohort dashboard/receipts and responsible operator; existing Support ID alone is insufficient |
| 13 | Manual rollback procedure | Proposed above; non-destructive rehearsal/correction readiness outstanding |
| 14 | Stop criteria | Proposed below; accept together with cohort/monitoring before collecting payment |

Monitoring minimum: activation attempts/failures, MESH Connect attempts/failures,
crashes per launches/sessions, version distribution, support-request count/severity.
Record denominators and observation window; stale support rows are not current
version distribution, absence of crash reports is not zero crash rate. Bound
retention and access; no raw keys/profiles/messages in telemetry. Before each next
cohort increment require reviewed receipts, a named operator and agreed thresholds.

Proposed immediate STOP: any identity/history loss, forced reset/re-invite,
wrong/duplicate payment activation, expired/revoked access beyond approved bound,
signer/hash mismatch, unsafe routing/security failure, crash loop, missing upgrade
or recovery receipt. Stop expansion also on repeated same-cause activation/MESH
failures, unowned critical support incident or missing monitoring denominator;
triage rather than automatic reinstall/reissue. Numeric service thresholds and
cohort size must be set before launch, not invented from this single field result.

**Explicitly not launch gates:** Linux P0/P1/Auto, Linux AppImage, Windows parity,
Linux messenger lifecycle, or a completely green historical repository suite.
No Linux task starts to close any Android blocker.

## Validation, scope and finite next stage

Local private evidence: `state-client-build/android-controlled-beta-20261027/`:
artifact/signature/source inventory checks, sanitized-output administrative lookup
(full mapping private),49 backend/20 JVM logs, read-only Linux hashes, signed public
catalog observation. Retained source/artifact files untouched except system-archive
write-bit removal. No public release/tag/catalog change, installation or deployment.

Target Support ID absent from the selected APK's decompressed entries (UTF-8 and
UTF-16), checked public catalog/release notes, and this committed documentation;
unrelated pre-existing local administrative drafts are not published by this commit.
Strict JSON, local links, staged scope/secrets and `git diff --check` are checked
before commit; commit/push and remote SHA outcome are recorded in the checkpoint
handoff, not invented as a self-referential SHA inside this report.

**STOP. NEXT — close only factual ANDROID-CONTROLLED-BETA launch blockers:**
one bounded authorized upgrade fixture, paid-state/payment/expiry acceptance,
approved delivery + non-destructive recovery, legal/cohort/monitoring/stop review.
Completion gate: all14 rows satisfied in their stated scope with exact receipts;
otherwise retain BLOCKED and list only remaining gaps. No automatic client patch,
Linux retry, new build, payment activation or rollout is authorized by this queue.
