# Android beta63 — bounded recovery release candidate, 2026-10-04

## Current gate

**PREPARATION; NOT BUILT/SIGNED/INSTALLED/DISTRIBUTED.** User authorized the new
immutable release and owner acceptance after the locally validated recovery fix.
Version `0.1.18-beta63`, code63; base main
`cb76f115bb45101dc0528cf0d343f12cd10cb24f`. Exact candidate commit/CI pending.
Remote main equals this baseline and no beta63 tag exists at preflight.
Latest baseline phase0 run37203525069 PASS; not a candidate acceptance.

Owner Redmi31ce63ba connected; installed62/code62, UID10283, first install
2026-09-19 17:30:26. No device changes yet. Last accepted beta62 APK SHA256
`f60b8d3a74b85a5934b942d7e273831e7c1d88d35e4d8a87db7332fb7d7703d4`;
signer pin `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
Default/catalog/invitation remain60; no gateway change required by this Java-only fix.

## Source and checks

Only correlated retry-exhaustion enters the existing one-pass recovery policy;
cleanup, guard, fresh bootstrap/authentication, revocation/cancellation and unknown-error
fail-closed rules remain. Retry/RTO/window/wire semantics unchanged. Local prior-source
checks: Android243/lint, Python100, four Go race packages and export(11) replay PASS.
These do not replace exact-source CI or physical owner acceptance for63.
[Detailed fix and limitations](2026-10-04-restricted-recovery-classification.md).

## Required next gates

1. Exact-source platform CI; download and verify native/APK payload, provenance,
   package/version/ABI/alignment and privacy before offline signing.
2. Same signing identity; install in place only after owner baseline is saved. Preserve
   UID, device identity, enrollment, activation, Support and app data. No uninstall/clear.
3. Native/service owner acceptance: normal AWG/TCP; restricted establishment, controlled
   loss, old cleanup and fresh descriptor/session; one-pass limit, denial/cancellation.
   Distinguish injected evidence from genuine native exhaustion; no false field-fix claim.
4. Renew/verify actual authorization-chain validity before restricted tests; the previous
   17:30:19UTC bound is not a current usable window. Keep admission/identity unchanged.
5. Publish only if accepted; never replace62. Verify actual downloaded bytes/signer and
   document URL/checksum. No default/catalog/invitation promotion or tester repeat now.

## Rollback

Before install: retain installed62, do not sign/publish failed candidates. No runtime
rollback needed yet. After an in-place update, do not assume Android permits downgrading
versionCode; keep guard/manual normal access and use an accepted forward-revert if needed,
without deleting identity/data. Old62 public artifact must remain byte-identical.
