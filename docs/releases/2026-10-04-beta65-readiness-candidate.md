# Android beta65 — retained-cache refresh candidate, 2026-10-04

## Release state

User authorized a separate commit/push for CI and the next APK. Candidate version
`0.1.18-beta65`, code65, carries the [early-refresh correction](2026-10-04-readiness-early-refresh.md):
retain the persistent300s attempt cooldown but do not suppress refresh merely because
old credentials remain valid. No cache reset, identity change, schema migration,
authority bypass or transport timeout/retry changes. Source baseline7088fb5.

Final source `86fa1bae8b97ff34d3e8cbd5b3cfe923cb7d71a6` is CI-accepted, offline signed
and installed on owner Redmi65. **Not publicly distributed: recovery gate failed.**
Tester/targeted public64, default/catalog/invitation60 remain unchanged. Existing
signed64 APK b1a9f621 must never be overwritten. Live gateway remains f71b7e7b;
`carrier` and `pilot/android-restricted` have no source changes since accepted64.
Historical/policy documents already dirty at entry are preserved outside the scoped
source commit where not required for the new release/current-state documentation.

## Evidence and gates

Initial source `2fd6b4a5114b1db9cbd5f8c65e458947c6458c1f` was pushed.
Readiness37229125304 and phase037229125311 passed. Clients37229125318 failed
before APK construction: `TestAuthenticatedImmediateResetPreservesOpen` reported
`TCP OPEN: connect_failed` in the carrier race step. Diagnostic artifact11313272643
SHA256 `917d881a11e7f1d56299eb33306d036daa3e7b7de357a8ada5e7c347f3db057d`
retains the failure; it is not a refresh regression or a successful release gate.
Linux control was not triggered by the initial path set. No artifact was signed.

Follow-up regression checks the complete four-hour persisted300s cadence and server
replacement of still-valid one-/four-hour directories using the same registration,
unchanged grants and security floors; revoked devices remain denied. Python119 PASS
and the focused JVM cache class PASS. Initial new server assertions incorrectly
looked for family at the top level (two KeyErrors); corrected the test to the actual
`directory.family` schema, without changing production code or weakening denial.
The follow-up source must pass all four workflows before any signing/delivery.

Before version preparation, Android254 unit/lint, standalone JVM171 and Python117
passed, including Java HTTP and four native Go compatibility cases. Five new red
regressions reproduced the old behavior first. Native validation in the scheduled
Java fixture is a callback, not a physical/JNI proof. New test starts with serialized
valid four-hour cache, passes the ordinary attempt gate, signs/fetches/imports/readbacks
and ACKs a new directory without clearing old state. Timeout, validation failure,
denial, persistent cooldown and anti-rollback cases remain covered.

## Final exact-source acceptance

All four final-source workflows passed attempt1:
- Clients37230196863, including carrier race, Android emulator VPN/runtime checks,
  exact ARM64 release build/unit/lint, Linux GUI and Windows native/compatibility.
- Readiness wire37230196819; Linux control37230196828; phase037230196827.
- Initial-source TCP immediate-reset failure is retained above. Local30 repeats PASS
  and final CI PASS do not establish its root cause or a transport fix.
- Final local Python119 PASS; version65 Android254/lint0 errors37 warnings, JVM171,
  focused long-cadence test PASS. Documentation475 files/2891 links PASS.

Accepted artifact11313732252:58404731bytes, ZIP SHA256
`c644f397670bbb0893acc8329ed7eb4b48b8a9c31417dd318873de40dfe4adde`.
Unsigned APK SHA256 `51e20f1ff2882fe7abc1b017ea2935933cc2204ba1270c8416ee8d99d0003022`.
Signed APK SHA256 `dfbdb5352b8c707fb77ff3d7392d8217f898aa8e999b6a0f52fad8172185778e`,
49671035bytes, package `com.familyconnect.app.friends`, version0.1.18-beta65/code65.
Original signer `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
No rebuild during signing; APK v2 signature/16KiB alignment, ARM64-only, non-debuggable,
native/source provenance and privacy scan1074 entries/no findings PASS. Accepted
stdlib Basic-scheme false positive remains documented, not a credential.
Built native SHA `4fdc14f751e9ada09a0306970caca6d5bc134e2728dc5c073842ea7f20499fb2`;
built gateway SHA `8ab8400ffee66b3c880ef9944042146c78b8d0e9210a7eae500adabd1e231719`
is **not deployed**. Live gateway SHA remains
`f71b7e7bb92d7f312d210d41ebf200cf4416ed73ca7fe3a33ae2e13d4d3f2ebf`.

## Physical owner acceptance and release hold

Owner Redmi31ce63ba upgraded64→65 without uninstall/reset. UID10283, data inode,
first-install timestamp, encrypted identity/config/readiness at installation,
enrollment/activation and Support FC-4D8Q-REEG preserved. Final installed APK pulled
and SHA/signer verified; private instrumentation APK removed, synthetic export/test
state cleaned. No real server revocation/admission change, product data kept.

Ordinary `FriendsActivity.onResume` was the first Activity launch after upgrade:
old native-valid cache still had **9576seconds** remaining. Existing persisted cooldown
was already elapsed, not edited. No forced prewarm/fetch or cache clear. Ordinary
fetch→native import/readback→new signed READY/ACK passed. Server confirms fetch
20:19:56UTC and ACK20:20:35UTC for65; same registration/revision3, newer CRL4802.
This proves the retained-cache refresh correction on hardware, not field DATA recovery.

PASS: enrollment, AWG/TCP HTTPS200, local denied startup with no session, connected
AUTH cleanup with no recovery, cancellation, diagnostic sharing/privacy, runtime
provider/update checks, restart/Support and final preservation/cleanup.

**FAIL: policy-loss recovery20:21UTC.** First real restricted session connected and
HTTPS200 passed. The fixture then injected a NETWORK policy cause (not actual native
retry exhaustion). Production orchestration cleaned the old candidate and attempted
a new one, but ended BOOTSTRAP_UNAVAILABLE after8.5s. Client shows BOOT_CACHE_READY,
BOOT_CARRIER_READY and FAMILY_AUTH_READY, then STARTUP_FAILED; no new descriptor/tag.
Server20:21:24.725UTC confirms `bootstrap_family_auth`, followed at24.726UTC by
`bootstrap_exchange_failed`, with no new CREATING/CLIENT_ISSUED event in the observed
window. This is no longer the original INTERNAL/no-retry classification failure.
The precise broker rejection is not currently logged. Existing `device_busy` admission
guard is a hypothesis only; no proof of expiry, revocation, RKN, or refresh causation.
No blind recovery rerun or timeout/security relaxation was used to make acceptance green.

Initial bounded journal read failed; retry with an explicit1000-line limit
and longer read-only command allowance retrieved the same-minute safe event projection.
Transport timeouts were unchanged. Failure snapshots/client events and server projection
are retained privately under `state-client-build/field65-owner/`; no keys/profiles in Git.
Subsequent separate connected-AUTH case did establish a session, but does not replace
the failed immediate-recovery gate.

Readback20:20:44UTC: gateway active/PID4077612/NRestarts0, loaded leaf matches profile
and expires **04.10 22:57:31UTC**; directory expires22:59:29UTC and cannot extend it.
Tester still64 with old-cache ACK, no new tester mobile attempt or delivery performed.
Final readback20:30:22UTC confirms the same gateway PID/binary/leaf bound, owner65 new
ordinary fetch20:27:45UTC/ACK20:27:52UTC with revision3/CRL4816, tester64 unchanged.
There is no new public65 link or changed catalog/invitation. Original DATA stall remains
unlocalized. NEXT bounded bootstrap exchange/admission reason diagnosis, then a valid
owner recovery/security gate and fresh material headroom before publication/tester trial.

## Original release gates (historical preparation)
1. DONE version65 Android254 unit/lint and working-tree documentation475 files/2891
   links, zero errors. Next scoped source commit/push with clean-index export checks
   and required current-state docs, excluding unrelated dirty work.
2. All four exact-source workflows: phase0, Linux control, clients and readiness wire
   contract. Download the accepted ARM64 artifact; verify digest, provenance, ABI,
   privacy and original signer after local offline signing. Do not sign a failed build.
3. Revalidate complete live material validity. Last verified gateway leaf bound was
  04.10 22:57:31UTC; directory/client receipt may expire later and cannot extend it.
4. Owner in-place64→65, original UID/identity/enrollment/Support preserved. Verify
   **ordinary foreground prewarm with retained valid old cache**, a new authenticated
   fetch/native import/readback/ACK and successful access. No test-forced refresh or
   cache deletion may stand in for the production scheduler gate.
5. AUTH/denial, retry bounds, export/privacy and ordinary VPN checks; remove private
   instrumentation. Then immutable targeted65 publication and downloaded hash/signer
   verification, leaving default/catalog/invitation60 unchanged.
6. Tester update/fresh current-directory READY/ACK before the authorized single
   Krasnodar mobile attempt/export. No mobile repeat is requested at this checkpoint.

## Rollback

Owner65 is installed; gateway and public distribution were not changed. Preserve current
64 artifacts/route and device data. Withdraw only a future65 route if needed, retaining
immutable bytes and unrelated nginx edits. Installed rollback requires a higher-code
forward fix, never uninstall/data clear, version downgrade or replacement of published
64/65 bytes. Gateway renewal must preserve authority floors and valid credentials.
