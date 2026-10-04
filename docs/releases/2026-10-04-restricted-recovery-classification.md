# Export(11): bounded recovery classification fix — 2026-10-04

## Scope and delivery boundary

**LOCAL SOURCE FIX / REGRESSIONS PASS; NOT A RELEASE OR FIELD FIX.**
Working-tree patch on `cb76f115bb45101dc0528cf0d343f12cd10cb24f`.
Pre-existing uncommitted documentation preserved; no commit, tag or push in this task.
No APK assembled/signed/installed/published, native runtime rebuilt or server changed.
Java compilation for unit/lint is not an installable release acceptance.

Last accepted targeted artifact remains Android `0.1.18-beta62`, code62, source
`42a5e59b4bc2c43e56e018ce7287cd7b6e901db2`, APK SHA256
`f60b8d3a74b85a5934b942d7e273831e7c1d88d35e4d8a87db7332fb7d7703d4`.
The last accepted installed Amsterdam gateway is SHA256
`6773423c960c303c4a1b3b6dea35941d3011873d7ee7a3cf31818f3672372f09`.
Default/catalog/invitation remain beta60 per the prior accepted record. These are
baseline rollout facts, not a fresh public-download/server verification in this task.
No download/checksum/signing/catalog update is warranted for an undelivered source patch.

## Change

- `AutomaticConnection.poll` no longer maps every unhealthy restricted session to
  INTERNAL. `RestrictedTunnelEngine.connectionFailure` samples native state/stats once,
  feeds that snapshot to diagnostics and classifies it before cleanup. This avoids
  a second stats read draining native event evidence.
- Pure `RestrictedRecovery` permits NETWORK only for failed native phase3, valid
  matching diagnostic/lifecycle/session tags, first failure CARRIER/FAILED/
  RELIABLE_RETRY_EXHAUSTED, `reliable_terminal=recovery_exhausted` and terminal reason
  IO_CLOSED, EOF or RELIABLE_EXHAUSTED. No heuristic based on error text or counters.
- Native AUTH/denial, cancellation and terminal FAMILY_REJECTED/CANCELLED override
  network classification. Missing/malformed/mismatched evidence, TLS errors, protocol
  errors, setup loss, handshake/frame timeouts and unknown causes remain terminal.
- The existing orchestrator still permits only one restoration pass per user CONNECT:
  guard before stopping the old engine, no new engine after cleanup failure, bounded
  backoff/deadline, then the ordinary fresh BOOT-1 descriptor/session path. Normal
  transports may be tried first under the unchanged candidate ordering. Existing
  application sockets are not migrated; this is not seamless session resumption.
- Explicit access checks run before startup and immediately before native begin;
  denial also stops the startup wait. Current cache/native expiry, identity, CRL,
  TLS and authorization checks are unchanged; no bypass or expired material reuse.
  `ConnectivityOrchestrator.lost` honors an already recorded owner interruption so
  an AUTH signal observed during snapshot collection cannot be downgraded to generic
  cancellation and release the guard. A regression covers that race boundary.
- No retry/RTO/window/timeout/wire-format changes; no native production code changes.

## Verification

All final checks use the patched working tree:

- Android `:app:testFriendsUnitTest :app:lintFriends`, offline Gradle8.11.1/JDK17,
  `-PfcTargetAbi=arm64-v8a`: **243 tests / 38 suites, zero failures/errors/skips; lint PASS**.
  Log `/tmp/fc-export11-recovery-full.log`. Initial Gradle sandbox socket denial was
  resolved by normal approved outside-sandbox execution, not by changing the app.
- Python: **100 PASS**, no skips, in `/tmp/fc-boot1-venv`; installed versions checked
  against `control/requirements.lock` and `device_identity/requirements.lock` (MATCH).
  `FC_TEST_GO=/tmp/fc-boot1-tools/go/bin/go` enables the four cross-language cases.
  Suites: `test_orchestrator_android_contract`, `test_restricted_android_contract`,
  `test_friends_restricted`, `test_orchestrator_restricted_acceptance`,
  `test_restricted_correlation`, `test_telemost_reliable_gap`.
  The preliminary minimal environment run had96 PASS/4 skips; superseded by this run.
- Go `go test -race -count=1 ./reliablestream ./telemost ./sessiondiag ./sessiontrace`:
  **all four packages PASS**. Telemost's local socket tests required approved execution
  outside sandbox. This is local testing, not a live provider/field acceptance.
- Private local replay of actual export(11) against compiled `RestrictedRecovery`:
  all three retained retry-exhaustion sessions classify NETWORK, the separate setup
  failure stays INTERNAL. Export duplicates yield6 NETWORK/2 INTERNAL projections,
  not eight distinct sessions. No export or private material added to Git/output.
- New regressions cover strict reason allowlist, malformed/missing/cross-session
  evidence, security precedence, later TLS errors not replacing first failure,
  one fresh bootstrap/broker/dedicated lifecycle, cleanup failure, interruption before
  and during recovery backoff, fresh-attempt rejection, exhausted restoration budget
  and AUTH-versus-cancellation ordering. Existing cache expiry/denial tests also pass.
- `git diff --check`: PASS.

## DATA/ACK investigation boundary

Added deterministic `TestFreshACKWithoutProgressDoesNotResetRetryBudget` using
unchanged production defaults: lose the head DATA block, deliver the following seven,
continue receiving valid ACK/SACK200ms before each sender tick. The sender retransmits
only the missing block, not SACKed blocks, and terminates after8 retransmissions with
8 pending, ACK age200ms and cumulative-progress age9000ms. Fresh ACK traffic is not
proof of successful DATA delivery. A control delivering the missing block on retry4
drains the window and restores progress without any timeout/retry change.

This reproduces a *possible mechanism* for the observed signature, not the actual
field-loss cause. Local VP8/RTP loss/reorder/framing tests pass. Packet/fragment loss,
reassembly expiry, provider behavior and path-specific loss remain to be distinguished;
neither a carrier/framing bug nor RKN involvement is established. No tester repeat now.

## Rollout, rollback and remaining checks

1. Review the patch, then use a new immutable version/code/tag (never replace beta62).
   Run exact-source platform CI and verify downloaded native/APK assets before offline
   signing. Preserve beta60 default/catalog/invitation and current FIELD admission unless
   separately authorized to change them.
2. Owner in-place acceptance must preserve UID/identity/enrollment/activation/Support;
   verify normal AWG/TCP, controlled restricted loss, old-session cleanup, new descriptor
   and authenticated session, guard and bounded second-loss behavior. Test denial and
   cancellation through the actual native/service path. JVM fixtures are not this gate.
3. Before a future owner/field restricted test, renew and verify the complete current
   authorization/material chain and actual remaining validity. The previously recorded
   04.10 17:30:19UTC bound is historical, not a renewed test window.
4. Public artifact/signature/catalog/invitation checks remain required for any future
   rollout; only then update release/user guides and announce delivery. Do not ask the
   tester to repeat with unchanged beta62 now.
5. No runtime rollback is needed: nothing installed/deployed. Source rollback removes
   only this task's classification/adapter/orchestrator/test changes, preserving earlier
   uncommitted work. A future installed successor needs an explicitly verified in-place
   rollback/forward-revert plan; do not assume Android accepts a lower versionCode.

[Original field evidence](2026-10-04-field-export11-beta62.md) ·
[Last accepted APK](2026-10-04-beta62-recovery-candidate.md) ·
[Prior server window](2026-10-04-beta62-four-hour-rollout.md).
