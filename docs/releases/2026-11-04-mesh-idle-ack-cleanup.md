# 4 November — MESH idle ACK cleanup source correction

## Scope and result

Selected continuation of the Android115 MESH incident within FLEET-BOOTSTRAP-2:
local media/ACK-starvation and recovery-ownership reproduction before another
correction. Source parent `81b5c8f8324b2a0c9bd50ea6b395e479ba48bff5`.

**SOURCE REGRESSION/CORRECTION PASS; PHYSICAL STABILITY STILL FAILED/OPEN.**
This work uses saved paired evidence and local test endpoints only. No phone,
server, signing, release-tag, installer, invitation or catalog mutation occurs.
No new Android version is assigned. The original media interruption is not
explained by this correction, and the later physical `device_busy` still lacks
complete holder attribution.

## Evidence and reproduced defect

The [physical115 receipt](2026-11-04-android115-mesh-cleanup.md#physical115-paired-acceptance--manual-cleanup-pass-traffic-fail)
remains authoritative: first-session DNS/HTTPS and manual cleanup pass; the next
burst returns47/64 across a native generation. NL1 first exhausts an outstanding
frame after9.514s without ACK/progress; Android first exhausts a frame after~20s,
with subscriber disconnection preceding its terminal event. These are **pending
DATA** failures, not observed idle-timeout failures. The later recovery's precise
server ownership has not been proven. Do not relabel either as solved.

Local fault injection exposes a separate recovery gap: after the final DATA is
acknowledged, both directions can lose all media, including RESET, while their
outer carrier contexts remain alive. ReliableStream previously checked age only
for negotiation or outstanding DATA. With an empty send window, it sent ACK
refreshes forever without expiring a missing peer. Family `Done` stayed open;
the broker retained its active owner and a subsequent authenticated waiter could
not acquire it before outer cancellation. This is not fixed by raising retries.

Six regression cases fail on each of:

- Unchanged main engine at the source parent, with new tests supplied separately.
- Independently qualified NL1 `primary-source-r2` capsule corresponding to
  deployed binary `8769eadfa88850c41fc0d90a9dcc4749f2e949de36dfd95bb606c32c404b3c30`.
- Independently qualified NL2 `secondary-source-r2` capsule corresponding to
  deployed binary `5bcb32ea138325fbe3c788e2500d5054073ffc8df589e1cd1e83ed31c0946638`.

Go overlays add the same tests without changing those private source capsules;
gateway baseline runs use `-race -tags=fc_perf_diagnostic`. These are local source
reproductions, not new runtime observations or qualified gateway replacements.

## Correction and invariants

When the established sender has no pending DATA, missing valid ACK refreshes now
expire after existing `MaxAge` (20s in the examined defaults). Before its first
ACK, the timer starts at negotiation completion. Subsequent OPENs, foreign epochs
and obsolete cumulative ACKs do not refresh it. Valid duplicate cumulative ACKs
are expected during quiet operation and keep a healthy idle peer alive.

`RELIABLE_IDLE_TIMEOUT` is recorded before bounded teardown, without inventing an
outstanding frame or retry count. Native, Android ring/projection/recovery and
operator correlation allowlists agree. Android classifies only a correlated,
proven reliable exhaustion as a network failure; auth denial, cancellation and
invalid evidence retain their existing fail-closed behavior.

This **adds idle liveness termination**; it is not a diagnostics-only change.
No new wire frame, retransmission increase, frame/handshake deadline extension,
owner eviction, setup cancellation shortcut or application replay is added.
Existing RESET limits and worker joins remain intact. The ownership integration
test deliberately holds `Gateway.Close`: a replacement stays blocked until it
finishes, and stale cancellation cannot release the new owner. Separate real
Family TLS coverage proves idle expiration closes `Session.Done` and buffers.

## Local qualification

| Gate | Result |
| --- | --- |
| Unchanged main and both canonical predecessors | Six expected regression failures each; quiet valid-ACK positive passes. |
| Final full `-race` on reliablestream/familysession/roombroker/sessiontrace/localwrite |272 PASS test events,22 optional skips,0 failures; all five packages pass. |
| New idle cases, ownership and fresh-ACK/non-progress negatives, `-race -count=10` |180 PASS events,0 failures/skips. |
| Real local ICE outage/recovery, transient disconnect and owned-carrier lifetime, `-race -count=3` |39 PASS events,0 failures/skips. |
| Selected bootstrap cleanup/admission/revocation/overlap, `-race -count=3` |63 PASS events,0 failures/skips. |
| Python correlation/Android contract/orchestrator acceptance |45 passed. |
| Android debug/Friends JVM, final source |419 +414 passed,0 failures/errors/skips; new idle classification case executes in both. |
| Android debug/Friends lint |Both pass; existing Gradle9 deprecation notice retained. |

Fresh disposable ProductStore fixtures stay in ignored local state. The22 Go
skips are20 root/canonical-access cases and2 opt-in Family process-runner cases;
none is a new idle regression. Counts above include Go parent/subtest events.
The bounded bootstrap selection does not include the two previously recorded
inherited assertions; no full historical/bootstrap/platform CI PASS is claimed.

The first broad candidate run failed all four variants of
`TestHeadLossAndDuplicateVirtualClock`: its old post-drain assertion advanced a
whole `MaxAge` with no peer ACKs but expected indefinite survival. The fixture now
models the real periodic ACK refresh for its healthy quiet peer; all head-loss,
duplicate and retry assertions remain. New negative tests independently require
expiry with absent ACKs. This initial failure is retained, not called a flake.

Private evidence: `state-client-build/mesh-idle-ack-20261104/` (red overlays/logs,
fresh fixtures, race JSONL and JVM/lint receipts). No raw user export or private
source capsule is committed. No external media/provider traffic is generated.

## Versions, delivery and remaining gates

- Owner remains product-signed Android115, last observed DISCONNECTED/capture
  closed at19:39:10UTC. It is not re-read or changed in this source-only step.
- Public/invitation/updater113/catalog7, Linux0.2.11 and Windows0.2.16/catalog12
  remain the last verified versions; no new public readback is claimed here.
- NL1/NL2 retain the earlier cleanup runtime delivery. This correction is **not
  projected, built or deployed** to either canonical profile. No service restart,
  common-writer action or rollback was performed.

Next only when selected: qualify the narrow change independently against both
canonical sources, preserving their distinct framing/performance/admission
policies; qualify an exact new Android candidate through its normal CI/artifact
and protected-signing gates before any installation. Do not publish another APK
under115 or deploy generic main as a gateway.

Then renew normal app support consent as needed and pair physical quiet/loss/
reconnect and DNS/normal-TLS egress evidence on the selected node, including
confirmed old-owner cleanup and no overlap. The original media/ICE interruption
and incomplete physical holder attribution remain investigative work, not an
acceptance PASS. Short transient loss must recover without unnecessary teardown;
persistent loss must close within the documented bound without leaks or replay.

No runtime rollback is needed for an undelivered source change. Future guarded
delivery must use the [existing runtime rollback and state-preservation paths](2026-11-04-android115-mesh-cleanup.md#gateway-delivery-and-independent-readback--1807utc),
fresh immutable artifacts and retained product identity. A source push alone is
not permission for publication or server policy changes.
