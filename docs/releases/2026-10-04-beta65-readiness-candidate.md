# Android beta65 — retained-cache refresh candidate, 2026-10-04

## Release state

User authorized a separate commit/push for CI and the next APK. Candidate version
`0.1.18-beta65`, code65, carries the [early-refresh correction](2026-10-04-readiness-early-refresh.md):
retain the persistent300s attempt cooldown but do not suppress refresh merely because
old credentials remain valid. No cache reset, identity change, schema migration,
authority bypass or transport timeout/retry changes. Source baseline7088fb5.

This preparation is not CI acceptance, signing, installation or publication. Last
verified owner64/tester64 and targeted public64, default/catalog/invitation60 remain
unchanged. Existing signed64 APK b1a9f621 must never be overwritten. Matching live
gateway remains f71b7e7b; no gateway code change is needed for the Java-only correction.
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

Required next gates:
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

No new installed/deployed runtime yet, so no live rollback is needed. Preserve current
64 artifacts/route and device data. Withdraw only a future65 route if needed, retaining
immutable bytes and unrelated nginx edits. Installed rollback requires a higher-code
forward fix, never uninstall/data clear, version downgrade or replacement of published
64/65 bytes. Gateway renewal must preserve authority floors and valid credentials.
