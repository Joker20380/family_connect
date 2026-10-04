# Paired DATA/ACK/fragment diagnostics — 2026-10-04

## Result and release boundary

**Local source implementation and tests PASS; runtime acceptance pending.** Uncommitted
patch based on `de7cacde133d96423939dfcde5da048f97d87d46`. No version bump, release APK
build/sign/install/publication, gateway deploy, material renewal or live mutation.
Existing dirty documentation and native-framing regression are preserved.

Last verified distribution remains owner `0.1.18-beta63`/code63, tester authenticated
receipt beta62/code62, default/updater/invitation beta60/code60. Owner APK SHA256:
`ce81216a84005880eef834dd5f576d0c43082b1c501767c7cf83522a765aebb8`.
Gateway binary remains the last verified
`6773423c960c303c4a1b3b6dea35941d3011873d7ee7a3cf31818f3672372f09`.
This task inspected existing release evidence, not a new live deployment readback.
The previous material bound `2026-10-04T17:30:19Z` is **not** renewed or fresh readiness.

The accepted beta63 recovery fix is unchanged: correlated retry exhaustion maps to
NETWORK; AUTH/revocation/cancellation protection and one-restoration guard remain.
This new patch observes transport boundaries; it does not claim the field stall is fixed.

## Implementation map

- `carrier/sessiontrace/delivery.go`: fixed numeric/boolean schema and deep copies.
  Recorder retains last8 detail events plus a separate pinned first failure, without
  evicting lifecycle events merely to trim detail. Input, sink and snapshots do not alias.
- `carrier/reliablestream/engine.go`, `stream.go`: cumulative/SACK state, receive window,
  outstanding head and retry state; freeze before terminal buffer cleanup.
  `diagnostic.go` recognizes only the fixed FRS1 DATA header prefix/declared length.
- `carrier/telemost/msg.go`, `session.go`, `signaling.go`: same sender/message/fragment
  IDs at enqueue, successful local write and receive assembly. Missing first fragment
  leaves DATA sequence unknown; zero is a valid sequence. Count rejects without changing
  rejection, duplicate/recent policy, pruning, retransmission or delivery decisions.
- `carrier/sessiondiag/endpoint.go`, `wholedevice/session.go`, `roombroker/gateway.go`:
  both endpoints sample at existing2s cadence, with one final sample on sampler stop.
  The failure event pins reliable flow. No packet-by-packet journal expansion.
- Android `RestrictedDelivery`/`RestrictedTrace`: strict bounded allowlist, no raw strings,
  last8 details plus first failure; existing history/export limits unchanged.
- `scripts/correlate_restricted.py`: optional-detail merge across ring/incident exports;
  reject contradictory component evidence. Add two-direction comparisons only for the
  latest sampled outstanding flow, join fragment IDs when present. A later drained flow
  cannot revive an older pending-head sample. Old exports remain accepted.

See the [operator contract](../testing/restricted-session-diagnostics.ru.md) for field
semantics. No payload, keys, addresses, destinations, room identifiers or CRC values are
logged. Header recognition is diagnostic, never authentication/admission evidence.
Android/Python omit malformed or out-of-safe-integer-range components, not coerce them.

## Verification

- Full native `go test ./...`: PASS, including broker, family session, forwarder and tools.
- `go test -race ./sessiontrace ./reliablestream ./telemost ./sessiondiag ./wholedevice
  ./roombroker`: PASS. Initial sandbox run denied local test TCP/UDP sockets; normal
  approved outside-sandbox execution passed. Workspace GOTMPDIR/GOCACHE avoid `/tmp` quota.
- Actual ReliableStream→fragment→VP8/RTP regression: no loss, healed loss and persistent
  missing-head DATA with fresh ACK. Frozen terminal Flow/base0/next8/pending8/retries8,
  SACK254 and receiver partial assembly asserted; default transport timers unchanged.
- Android `:app:testFriendsUnitTest :app:lintFriends`: PASS, **246 tests**, zero failures,
  errors or skips. Maximum allowed detail values plus full history/ring/incident fit the
  existing export budget. Initial new fixture visibility compile error fixed before pass.
  Existing Gradle deprecation/cache watcher and initial Chaquopy Python-version warnings
  remain; no APK runtime acceptance is inferred from unit/lint.
- Python focused correlation/Android contract/acceptance-hook suite: **52 passed**;
  includes malformed numeric/boolean rejection, optional-detail merge/conflict,
  partial message join, mismatched identity, drained head and non-simultaneity cases.
- Public documentation link checker, `git diff --check` and modified Go-file gofmt
  check: PASS. No formatter configuration or unrelated source changes added.

## Interpretation and remaining gates

Samples across endpoints and layers are **not simultaneous**. Enqueue success is not
wire delivery; WriteSample/DC.Send success is local handoff; CRC completion is before
ReliableStream acceptance/consumption. receive_next is not end-site application success.
Only last DATA markers and oldest pending assembly are retained. Missing matching IDs
may simply mean sampling/retention missed them. Counters alone do not identify a lost
packet or RKN involvement. A head present in the receiver buffer but not consumed differs
from a head not buffered at that observation; neither is a causal verdict by itself.

Next: assign a fresh immutable successor, exact-source platform CI/artifact verification
and offline signing; matching gateway build/owner-private controlled deployment; verify
real paired fields, bounded export, AUTH/revoke/cancel, cleanup/new-session behavior and
identity/enrollment preservation. Revalidate/renew the actual material validity window
before any physical gate. Then decide whether another tester attempt is justified.
No tester repeat is requested now and no retry/timeout increase is proposed.

## Rollout and rollback

Nothing new is deployed, so no runtime rollback is needed. Existing
[beta63 delivery/rollback](2026-10-04-beta63-recovery-candidate.md) and
[gateway renewal safeguards](../../deploy/friends/restricted/GATEWAY_RENEWAL.md) apply.
Keep beta63 and gateway6773423c as the recorded pre-change baseline, preserve immutable
artifacts, admission/identity and default60 catalogs. A future deployment must retain its
verified old gateway binary/service settings and record actual rollback results; Android
fallback must use the signed release procedure, never data clear or overwritten beta63.
Do not remove unrelated pre-existing work when isolating this source patch.
