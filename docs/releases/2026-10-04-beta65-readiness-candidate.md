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
