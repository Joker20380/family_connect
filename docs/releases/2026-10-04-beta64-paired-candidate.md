# Android beta64 — paired delivery diagnostics candidate, 2026-10-04

## Current gate

**Exact-source CI, downloaded artifact verification and offline signing PASS.**
User requested the next release/owner-validation stage after the
[source diagnostics checks](2026-10-04-paired-delivery-diagnostics.md).
Version `0.1.18-beta64`, code64, source
`ce73ddf3e0dfc25546850b083b7dae4680720397`, pushed to main from de7cacd with user approval.
No tag or GitHub Release created. Diagnostics/tests/version/release and required baseline
docs committed. The existing02.10 health report was included solely because HEAD
STATUS/PLAN already linked to the then-untracked file; clean-export checking found it.
Five other dirty historical/renewal documents remain outside the commit, unchanged.
**Not installed, deployed or publicly distributed.** No live mutation or material renewal.

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

All four exact-source workflows completed SUCCESS by18:32:38UTC:

| Workflow | Run | Accepted attempt |
|---|---|---|
| phase0 |37223645511|1|
| Linux control preview |37223645532|1|
| Client builds |37223645645|1|
| Android Friends readiness wire contract |37223645492|2|

Readiness attempt1/job111498774820 failed in the Python HTTP/Android contract step
after Java success. Local golden-classpath rerun passed113 tests;4 optional locked-Go
compatibility cases skipped (FC_TEST_GO absent, matching that workflow's optional path).
One unchanged-source failed-job rerun passed; no tests/assertions/source relaxed.
The initial failure is retained and its cause is not established as fixed. Public log
download403 and coarse annotations did not provide a narrower reliable diagnosis.
Client Android race/contracts, unit/lint, emulator runtime, restricted native/gateway
packaging and exact release payload passed; Linux/Windows/Windows compatibility passed.

Artifact11311153048, `FamilyConnect-Android-restricted-arm64`,58404609bytes:
ZIP SHA256 `48edede84048c8816eb4df35f897e0292ee637cfe7004dc42dc663d1b263ba7a`.
Initial transfer403 was followed by a fresh-link CDN1010 response; a standard HTTP
User-Agent resolved the transfer. No artifact bytes were accepted before digest match.

- Unsigned APK SHA256 `4dde08a241e992c3225f4cd380751ae98571fcfdbcb26efb11b8264047c84878`.
- Signed `FamilyConnect-Test-0.1.18-beta64.apk`,49671035bytes, SHA256
  `b1a9f62116265b13a8482292175d3a685dca23ad3a5be0e4af5ef995a4d32d69`.
- Signer `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`,
  existing local protected beta key; no rebuild, key upload or key output.
- Restricted native SHA256 `d9c709917279a5e721a74f0e7a26d9c9346d3b162393021779e1fa19800ecf8c`.
- Matching CI gateway SHA256 `f71b7e7bb92d7f312d210d41ebf200cf4416ed73ca7fe3a33ae2e13d4d3f2ebf`,
  **built only, not deployed**.

Source/provenance pins, ARM64-only,16KiB alignment, non-debuggable, allowBackup=false,
cleartext=false, no private diagnostic components and privacy scan PASS before/after
signing.1074 signed entries scanned; known immutable stdlib Basic-scheme false positive
remains explicitly reviewed, no credential findings. Local receipts/artifacts are under
ignored `state-client-build/field64-ci/`; the signed APK is under its `signed/` directory.

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

1. DONE scoped source commit/push, clean-export docs473/2862 links checked without
   unrelated working-tree changes; existing broken dependency resolved explicitly.
2. DONE all four exact-source workflows, download/digest/provenance checks and offline
   signing; failed readiness attempt retained separately from accepted retry.
3. NEXT retain old gateway binary/settings and refresh owner installed baseline and
   identity/enrollment/Support evidence before update. APK64 hashes/signer recorded above.
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
