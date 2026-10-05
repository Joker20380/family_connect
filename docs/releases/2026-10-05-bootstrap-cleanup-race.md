# Bootstrap cleanup race — source correction, 2026-10-05

## Scope and delivery state

Continuation of the [beta65 failed recovery gate](2026-10-04-beta65-readiness-candidate.md).
Source prepared on HEAD `5263410`; user authorized scoped commit/push05.10.
CI receipt pending; no version change, APK build/signing, installation, gateway
mutation or public rollout in this step. Unrelated dirty
documentation is preserved. This is a locally verified server-side correction,
not evidence that installed beta65 recovery now works against production.

Last verified04.10: owner Redmi `0.1.18-beta65`/65; tester and targeted public64;
default/catalog/invitation60. Accepted APK65 source
`86fa1bae8b97ff34d3e8cbd5b3cfe923cb7d71a6`, four exact-source workflows PASS;
signed APK SHA256 `dfbdb5352b8c707fb77ff3d7392d8217f898aa8e999b6a0f52fad8172185778e`,
49671035bytes. Do not replace these bytes with a same-version rebuild.
Last gateway binary SHA256
`f71b7e7bb92d7f312d210d41ebf200cf4416ed73ca7fe3a33ae2e13d4d3f2ebf`;
PID4077612 at04.10 20:30UTC. This report does not assert a new live state readback.

## Evidence and limits

Original owner test injected a NETWORK policy cause after real restricted HTTPS200;
it was not a genuine native retry-exhaustion injection. Client cleanup occurred at
04.10 **20:21:16.631UTC**. New bootstrap family authentication succeeded at
**20:21:24.725749UTC**, followed by generic exchange failure at
**20:21:24.726987UTC**, before descriptor delivery. The old server session remained
alive until `RELIABLE_RETRY_EXHAUSTED` at **20:21:35.103UTC** (8 retries, one pending
block, ACK/progress age18460ms); final cleanup at **20:21:35.113UTC**.

The server slot therefore remained occupied18.482s after client cleanup, and was
released approximately10.386s after the new exchange failed. The original session
has67 gap-free server trace events. Strict projection reports zero changed/invalid
trace records. Private evidence is retained in
`state-client-build/bootstrap-exchange-diagnosis/original-session-server-inventory.json`,
alongside the earlier `state-client-build/field65-owner/` snapshots. No profiles,
keys, room URLs or product database are committed.

The old journal does **not** expose the rejection code. Code inspection and a red
deterministic regression reproduce immediate `device_busy` rejection during this
active-slot overlap; that demonstrates a cleanup race, not retrospective proof of
the exact historical error. Original field DATA/ACK loss location and RKN involvement
remain unproven. Earlier empty journal selections were a diagnostic selector error;
the corrected retrieval supplies the67-event record, not evidence of absent logs.

## Correction and security

- BOOT-1 waits for the exact previous active/closing setup's `done`, then requests
  a fresh challenge through the original admission path. Gateway close precedes
  `done`. It neither cancels the old session nor creates a parallel dedicated room.
- The existing120s total exchange deadline and any earlier parent deadline bound
  waiting. No transport timer, retransmission count or retry budget was increased.
- Family/device/public key are pinned and rechecked at the broker's existing
  authorization interval and after cleanup. Revocation, identity changes,
  cancellation and expiry stop admission. Deadline/cancel errors take precedence
  over a concurrent authorization-poll error caused by that cancelled context.
- Non-active unfinished duplicate setups and global limit violations still reject
  immediately. HTTP `Challenge`, replay checks and one-device slot limits remain.
- Server event `bootstrap_exchange_rejected` contains UTC and fixed stage/reason
  enums only. Unknown/raw errors map to `unknown`; generic on-wire ERROR and the
  existing `bootstrap_exchange_failed` event remain. No client protocol change.

## Validation and retained failures

1. RED before wait correction: active old gateway caused immediate ERROR instead
   of bounded waiting (`/tmp/fc-bootstrap-cleanup-red.log`).
2. Initial full Go race suite and94 Python tests PASS04.10. Python selection:
   `test_bootstrap_acceptance`, `test_nl_bootstrap_acceptance`,
   `test_telemost_family_fixture`, `test_restricted_correlation`;
   `/tmp/fc-bootstrap-python-checks.log` records94 passed in6.84s.
3. A20-repeat stress run exposed three deadline/auth polling races. The fix preserves
   exact `context.DeadlineExceeded`/`context.Canceled` assertions; it does not accept
   either error interchangeably. Initial failure log retained.
4. Overnight50-repeat run failed only the real-TLS busy test: disposable leaf/CRL
   expired04.10 21:44:44UTC, CA22:44:44UTC. At05.10 08:22UTC these were expired.
   No expiry checks or assertions were disabled. New isolated ProductStore-backed
   fixtures were generated under a separate ignored private directory.
5. Final05.10 fresh-fixture **50 repeats PASS** in10.640s: active cleanup wait,
   deadline, cancellation, authorization loss/identity change, immediate admission
   refusal, malformed request and real-TLS busy-reason observation.
   Receipt `/tmp/fc-bootstrap-repeat-race-20261005.log`.
6. Final05.10 **`go -C carrier test -race -count=1 ./...` PASS** with fresh fixtures,
   no cached test results. Receipt `/tmp/fc-bootstrap-full-race-20261005.log`.
   Full suite retains wrong-Family, revoked/unknown identity, provider/gateway failure,
   successful handoff, room broker, TCP, ReliableStream and privacy regressions.
7. Documentation checker:476 files/2896 links, zero errors; `git diff --check`
   and `gofmt -l` on all changed Go files are clean. This checks repository links,
   not public rollout or availability of download URLs.

No physical owner acceptance or Krasnodar mobile trial was repeated in this step.

## Next gates and rollback

1. Scoped commit/push authorized05.10; run exact-source CI and verify matching
   gateway artifact provenance. Existing accepted APK65 can be used for this
   wire-compatible server correction; do not rebuild/re-sign it under the same version.
2. Before hardware testing, renew/revalidate material: last actually loaded gateway
   leaf bound **04.10 22:57:31UTC has expired**. Later directory bound22:59:29UTC did
   not extend it. Verify loaded TLS chain/hostname/leaf and RU/NL directory generation
   consistency, issuer/security floors and device admission preservation.
3. Deploy only the verified gateway correction through the restricted runbook,
   preserving old binary and service configuration. Pass owner65 immediate recovery,
   auth/denial/cancellation and ordinary VPN/privacy gates with saved paired evidence.
4. Only then publish immutable targeted65, download/verify hash/signer, obtain tester
   fresh authenticated fetch/native READY/ACK and run one authorized Krasnodar trial.
   Default/catalog/invitation60 remain unchanged; no readiness from cached READY alone.

There is no production rollback to perform now. A later gateway rollback restores
the saved f71b7e7b binary/configuration with **fresh valid credentials**, not the
expired04.10 profile, and then revalidates service/loaded chain. Keep issuer floors,
admission, private state and unrelated services intact. A client fix requires a
higher-code successor, never uninstall/data clear/downgrade or immutable-byte replacement.
