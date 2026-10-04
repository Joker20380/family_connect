# Android beta63 — bounded recovery release candidate, 2026-10-04

Follow-up: [genuine native exhaustion→production poll→fresh session acceptance](2026-10-04-beta63-native-exhaustion.md)
now passes on the same installed63, without product/server replacement. The initial
injected-policy acceptance below remains a separate, honestly scoped checkpoint.

## Current gate

**CI / SIGNING / OWNER POLICY ACCEPTANCE / TARGETED DELIVERY PASS.** User authorized the new
immutable release and owner acceptance after the locally validated recovery fix.
Version `0.1.18-beta63`, code63; base main
`cb76f115bb45101dc0528cf0d343f12cd10cb24f`. Exact candidate commit
`de7cacde133d96423939dfcde5da048f97d87d46` pushed to main.
No GitHub Release/tag created. Baseline phase0 run37203525069 was not candidate acceptance.

Owner Redmi31ce63ba updated62→63 in place; UID10283, inode601521, first install
2026-09-19 17:30:26 preserved. Encrypted identity/config/readiness, enrollment, activation
and Support preserved at install; final16:43:39UTC identity/enrollment/Support and pulled
installed APK hash/signer PASS. Only private instrumentation removed. Readiness was
subsequently refreshed normally. No product uninstall/data clear/reenrollment.
Last accepted beta62 APK SHA256
`f60b8d3a74b85a5934b942d7e273831e7c1d88d35e4d8a87db7332fb7d7703d4`;
signer pin `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
Default/catalog/invitation remain60; no gateway change required by this Java-only fix.

Exact-source CI: phase0 `37214189109`, readiness contract `37214189135`, Linux control
preview `37214189145` PASS. Client builds `37214189165` attempt1 failed in Android
job `111471250197`: unchanged `InvitationRuntimeTest` line53 observed the preceding
synthetic invitation instead of the second one. Unit/lint, recovery tests, full Go race,
normal transport runtime, Linux/Windows/Windows compatibility passed. Required restricted
native/release packaging was skipped; the failed-run artifact was not signed as a release.
Debug ZIP11307942089 SHA256 `484400a35dc3c08248d8f665c9e5c74b68a92174e1eef4f645421edfeb44f33c`
downloaded/verified; XML retained (Debug248/Friends243, zero failures/errors).
Requested Android retry reran the client workflow on the same source. Attempt2 **PASS**,
including Android job111475140142, runtime, native/restricted packaging and payload checks.
All four workflows now PASS. No assertion/source changes; invitation flake not claimed fixed.

Redmi briefly disconnected/reconnected; read-only ADB confirms the same31ce63ba is
authorized again. This is independent of the hosted emulator failure. Owner baseline
was refreshed after reconnect, before update. Product now63; tester last receipt still62.

Read-only RU/NL preflight15:58UTC: both existing devices admitted/non-revoked, no admission
change, issuer sequence4, matching CRL4322. NL gateway PID3908811/restarts0, accepted
binary6773423c loaded and certificate/profile match. Earliest bound remains **17:30:19UTC**;
approximately92 minutes remained at that read, not a renewed four-hour window.
Owner native import/ACK16:33:34UTC PASS, receipt remaining3479s, no cache clear; effective
bound is the earlier gateway certificate17:30:19UTC, not receipt17:31:33UTC.
Read-only16:42UTC: owner63 READY/ACK, tester62 last READY/ACK, two devices admitted/non-revoked,
revisions3/1, issuer4, CRL4401; gateway samePID/restarts0/binary and certificate/profile match.
Default catalog/invitation hashes match baseline. No gateway/API/material mutation/restart.
Local docs check470 files/2836 links PASS; local private instrumentation compiles.

## Verified artifacts

Accepted artifact11308732220, `FamilyConnect-Android-restricted-arm64`,58370385bytes;
ZIP SHA256 `41e0bca84edf81caf7191b24ba9edf086194078dbc379dff3462bf352f2ae70a`.
Unsigned APK SHA256 `aee13bbd209b0685b64fd50a690001d075af3c28a31462b0abc3ce86921d62c3`.
Exact source/native pins, ARM64-only,16KiB alignment, non-debuggable and privacy scan PASS.
Offline signing used the existing protected local key, never CI/server.

- Signed `FamilyConnect-Test-0.1.18-beta63.apk`,49654651bytes.
- APK SHA256 `ce81216a84005880eef834dd5f576d0c43082b1c501767c7cf83522a765aebb8`.
- Signer SHA256 `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
- Native SHA256 `31be1b023e6c550b294d03ddbbda6eba73ad2e1b952d359beb65a417b6d36373`.
- CI gateway SHA256 `8ca752fe6ba71276bf053a7c66af34137e30f90d8ff2ea4476106c9c17499e18`, **not deployed**.
- Live gateway remains `6773423c960c303c4a1b3b6dea35941d3011873d7ee7a3cf31818f3672372f09`.

## Owner acceptance and honest scope

PASS AWG1513ms/TCP1508ms, VPN present and HTTPS200; existing signed enrollment;
Support visible/copy/restart; compiled diagnostic/provider/update checks; bounded
synthetic diagnostic export/privacy and cleanup of only its test artifacts.

Restricted test uses the signed production APK/native stack and real BOOT-1. A private
instrumentation Host adapter filters the candidate list to restricted after normal
configuration; it does not remove stored profiles or change product code. A typed
correlated retry-failure snapshot enters the production classifier, followed by the
production orchestrator loss path. **Native retry exhaustion was not physically induced;
the exhaustion→native poll segment was not exercised on this phone.**

PASS initial real session/HTTPS200, old handle invalidated, fresh descriptor/different
native handle and tag, healthy restored session/HTTPS200. Second injected loss reaches
FAILED without a third candidate and retains guard TUN; explicit disconnect releases it.
Server readback matches both real tags with56/132 events, no sequence gaps and complete
descriptor/join/carrier/TLS/session/cleanup stages:

- Initial `6ff6386de8dfdd69cab9517466e4418a73e2014acb2ad052d5e8477448ecfc00`.
- Restored `b7303eff8c69c274d000cb7ede9fce853ff09e39231a412882b049b29a63a994`.

Server retry exhaustion also appears in these controlled sessions. Forced client teardown
is a confounder, not proof of the original field stall. Server projection privacy PASS;
no full four-ID export claim here. Local denial injected before startup/while connected
PASS: AUTH, cleanup, no new descriptor, guard retained. Cancellation before startup PASS.
No real server grant/CRL revocation performed; no field/RKN/long-duration acceptance claim.

Retained failures: first recovery harness refused existing profiles before opening any
session; corrected only private candidate selection. First connected-denial attempt
failed to establish its initial session, before denial injection; cause not established.
One unchanged retry passed. These failures remain in private evidence, not hidden.

## Source and checks

Only correlated retry-exhaustion enters the existing one-pass recovery policy;
cleanup, guard, fresh bootstrap/authentication, revocation/cancellation and unknown-error
fail-closed rules remain. Retry/RTO/window/wire semantics unchanged. Local prior-source
checks: Android243/lint, Python100, four Go race packages and export(11) replay PASS.
Exact-source CI and scoped physical owner acceptance are recorded above.
[Detailed fix and limitations](2026-10-04-restricted-recovery-classification.md).

## Targeted delivery

Initial `scp` upload timed out after180s with24545280/49654651bytes in a private staging
directory. Readback confirmed no publication receipt, no public APK/route activation.
Resume uses `rsync --append-verify` on that same staged file, full hash before publication;
it must not replace an existing public asset or rerun the initial create-stage command.

Resume completed; immutable route activated16:56:40UTC. Only `family-connect-product-https`
nginx syntax check/reload; no API/AWG/TCP/gateway restart. **16:57:45UTC verified**:
[beta63 download](https://185.251.89.19:8443/downloads/FamilyConnect-Test-0.1.18-beta63.apk),
TLS verification/HTTP200,49654651bytes; downloaded SHA and signer equal the accepted
installed artifact above. No rebuild/resign, no GitHub Release/tag.
Readback confirms all older downloads unchanged (including62/60), catalogs/landing,
admission/Support/enrollment/grants and ordinary service processes unchanged. Default
catalog still60, mandatory_after0; signed catalog SHA256
`f042becae969474ed7ebc28890a635ae5812769a3203fa6d75cf18fd22060006`;
discovery SHA256 `6e5817dc109b579384985b7f966bcf56c22ec59b4759eb477ef031cdc59a6a3b`.
Tester last authenticated receipt remains62; this separate URL is not an instruction
to repeat a mobile test. Local final docs/link and whitespace checks PASS.

## Remaining checks

1. No default/catalog/invitation promotion or tester repeat now; retain the targeted
   scope and immutable artifacts. Installed owner63 is distinct from tester62/default60.
2. Subsequent genuine native exhaustion→poll→restoration passed in the follow-up above;
   initial injected policy acceptance alone did not prove it. Original DATA/ACK stall remains open.
3. Before later mobile checks, renew/revalidate the complete material chain and fresh
   native READY/ACK. Do not rely on this recorded window, bypass expiry or clear data.
4. Investigate targeted framing/loss evidence; do not tune retry/RTO/timeouts blindly.

## Rollback

Keep immutable62/60 public artifacts. After an in-place update, do not assume Android permits downgrading
versionCode; keep guard/manual normal access and use an accepted forward-revert if needed,
without deleting identity/data. Old62 public artifact must remain byte-identical.
Targeted publication rollback removes only63's nginx route after config backup/check,
not APK bytes or device data. Gateway rollback is unnecessary: it was not changed.
Private evidence remains in ignored `state-client-build/field63*`, including failed attempts.
