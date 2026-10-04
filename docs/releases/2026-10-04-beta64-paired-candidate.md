# Android beta64 — paired delivery diagnostics candidate, 2026-10-04

## Current gate

**Local candidate prepared; scoped commit/push authorized, exact-source CI pending.**
User requested the next release/owner-validation stage after the
[source diagnostics checks](2026-10-04-paired-delivery-diagnostics.md).
Local version `0.1.18-beta64`, code64, based on
`de7cacde133d96423939dfcde5da048f97d87d46`. No commit, push, tag or GitHub Release created.
Pre-existing dirty work is preserved; it must not be blindly included in a release commit.

## Read-only preflight

- GitHub main readback remains de7cacd. Latest Client builds run37214189165, attempt2,
  completed SUCCESS for beta63; it is not candidate64 acceptance.
- `git ls-remote --tags origin '*beta64*'` returns no matches. Sandbox SSH configuration
  access failed first; approved normal execution completed successfully.
- `2026-10-04T18:08:23Z`: beta64 HTTPS download HEAD returns404; no release bytes claimed.
  Existing default route/catalogs were not modified or reverified in this preflight.
- Same authorized owner Redmi31ce63ba connected over ADB. This checks connectivity,
  not current installed APK bytes, authenticated readiness or identity preservation.
- Previous material bound `2026-10-04T17:30:19Z` has elapsed. No renewal attempted here;
  renew/revalidate the complete chain immediately before physical acceptance.

## Version and artifact separation

Local source64 is not a built/signed/installed/published APK. No64 APK size, SHA256,
native hash or matching gateway artifact hash is available yet; do not invent them.
Last verified owner63 APK SHA256 remains
`ce81216a84005880eef834dd5f576d0c43082b1c501767c7cf83522a765aebb8`,
signer `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
Tester last receipt62; default/updater/invitation60. Last verified gateway binary:
`6773423c960c303c4a1b3b6dea35941d3011873d7ee7a3cf31818f3672372f09`.
No installed-version or gateway-live readback is implied by this source preparation.

## Checks and next actions

Diagnostics source previously passed full Go, six-package race, Android246/lint and
Python52 focused checks. These are local tests, not exact-source hosted release CI.
Candidate64 rerun: `:app:testFriendsUnitTest :app:lintFriends` PASS, **246 tests**,
zero failures/errors/skips; Python focused suite **52 passed**. Documentation checker
**473 files/2869 links**, zero errors; `git diff --check` PASS. Existing Gradle
deprecation/cache-watcher warnings remain. No full release artifact was assembled.

1. Explicit commit/push authorization received. Isolate diagnostics, tests, version and
   required release/baseline docs from unrelated dirty work. Push exact candidate source for CI.
2. Require all applicable platform/native/runtime jobs and release payload checks on
   that exact source. Download and verify artifacts/provenance before offline signing.
3. Record64 APK/native/gateway hashes and signer; retain old gateway binary/settings.
   Refresh owner installed baseline and identity/enrollment/Support evidence before update.
4. Renew/revalidate full materials and owner authenticated native READY/ACK. Deploy the
   matching gateway and install64 in place without clear/uninstall/new enrollment.
5. Verify paired delivery fields, bounded/private export and matching journal; normal
   access, cleanup/new session, bounded recovery and AUTH/revoke/cancel protection.
6. Keep tester/default/catalog/invitation unchanged. Decide further delivery only after
   owner acceptance. No repeat mobile attempt now; no field-loss/RKN conclusion.

## Rollback

No new runtime is deployed, so no runtime rollback is needed at this checkpoint.
For future gateway replacement retain exact prior binary/service settings and use
current valid materials, never expired cached credentials or lowered security floors.
Android rollback must use an accepted forward-fix/revert release with a higher code,
not data clear or assumption that version downgrade is allowed. Keep all prior APK
bytes and routes immutable; do not alter default60 distribution for owner testing.
See [beta63 accepted baseline](2026-10-04-beta63-recovery-candidate.md) and
[material renewal runbook](../../deploy/friends/restricted/GATEWAY_RENEWAL.md).
