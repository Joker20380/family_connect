# TARGETED-DATA-FAULT-1 — PASS (local source contract only)

Base986323ecef112fcc421a22263e6fbfc9d6cf1922. Isolated clone
`/tmp/fc-targeted-data-fault-1`; main dirty worktree source/docs not edited.
Evidence/diff/provenance: `state-client-build/field65-export16/targeted-data-fault-1/`.
No validation commit was needed by these tests; no commit/tag/push created.

## Explicit criterion

Target is **logical Reliable DATA N**, not an HTTP request or particular writer.
Any ordinary writer, including Mux control, may allocate N after successful arm.
No application request identity is claimed. Receiver prearm, actual attempt1 identity,
hop-local correlation, Reliable acceptance/consumption, actual token-matched ACK write,
sender progression, buffered-successor/gap and traffic continuity remain mandatory.
Historical selected-retry FAIL and UNKNOWN causes remain historical; no physical retry.

## Atomicity and routing

Existing protected correlation control gains `operation=targeted_arm`, `key` and
`prearm` (the confirmed receiver CorrelationReceipt). The operator first prearms
receiver, then sender correlation for exactly its returned key, then requests targeted
arm once. Client/gateway role routing rejects the opposite local direction. Existing
Unix UID/mode checks, Android DUMP/owner controls,16KiB strict JSON parser are reused.
No public endpoint, descriptor schema or wire field is added.

Reliable.New binds the active allocation owner to the recorder in diagnostic builds.
The arm callback acquires **stream.mu**, the same lock covering engine.send/state.next++.
It checks active owner/context, then acquires recorder.mu and checks current session,
correlation key/local tx watch/generation/attempt1, bounded unexpired receiver receipt,
local correlation window and existing evidence watch if present. Under both locks it
requires **pending0 and base==next==N** and installs the one-shot target/watch. Allocation
therefore either precedes arm (explicit HEAD_NOT_FREE rejection) or follows installation.
No sampled Flow can authorize arm, no retarget to N+1, no generic fallback.
Owner replacement invalidates stale allocation callbacks. No transport lock is held
while waiting for receiver prearm/operator command; randomness for the separate fault
nonce is generated before acquiring the allocation lock.

Lock order for this path: allocation stream.mu → recorder.mu. Drop/status/cancel only
use recorder.mu; its liveness callback checks context without acquiring stream.mu.
Normal allocation/receive/transmit retains its existing locking. No writer pause/lease,
TLS handoff marking, Mux change, packet format change, RTO or pacing change.

## Drop, time and cancellation

At the existing actual attempt0 fault boundary, recorder.mu serializes the decision.
The recorder scopes the session; targetValid checks live owner/session, exact tx
correlation key and watch, local deadline, and closure state. Only exact N with known
DATA/attempt0 and tx direction consumes. Wrong lower sequence, ACK or retry does not
consume; a later new sequence makes target explicitly TARGET_MISSED, not a latent trap.
Consumption atomically disarms, records count1/N/timestamp and preserves the N/attempt1
evidence watch. Descriptor/actual carrier-write/ACK callbacks remain the accepted path.

Correlation `key.generation` is the receiver prearm nonce. `fault.generation` remains
an independently generated fault nonce; response exposes `key` separately. They are
not compared or substituted for each other.

Receiver absolute expiry is interpreted under the existing validated UTC clock
assumption; expired or >30s-future receipts are rejected. Remaining duration is converted
once to a local monotonic deadline and capped by local correlation/evidence deadlines.
No TTL extension or revived expired watch. Existing clock validity remains a prerequisite
for a future run; this does not solve arbitrary cross-host clock skew.

Expiry is checked **in drop path**, not merely by the background correlation timer.
Cancel/cleanup/owner change/close that becomes effective first prevents drop. Drop that
linearizes first retains CONSUMED/count1 through later disarm/close. Session context
cancellation is checked at the decision; no context wait or remote operation occurs
under locks. Repeated targeted commands cannot create a second target after success.
Generic arm remains available to unchanged legacy tests, but returns TARGETED_ONLY
(not armed) after entering targeted mode; new controller/helper has no generic branch.

Terminal reasons include EXPIRED, CANCELLED, CLOSED, BINDING_LOST, OWNER_CHANGED and
TARGET_MISSED. Ordinary transmission continues when a target cannot be applied. These
are diagnostic outcomes, not fabricated retry PASS or transport failures.

## Controller/helper

An exact-source adaptation of the historical controller/helper is preserved separately
under `scripts/owner_targeted_retry`; historical originals/receipts are untouched.
One status candidate supplies N with session/type/event-order checks, but not ownership.
Stable sampled send_next/pending loops no longer authorize selection. Actual head
conditions are exclusively the atomic targeted operation's responsibility.

One receiver prearm → sender correlation prearm → targeted arm. Rejection raises
PREPARATION_ABORTED/drops0, persists response and enters the existing finally cleanup
for both watches. No loop searching a different N and no generic arm fallback. Java
helper permits traffic only after the targeted result says ARMED; old arm command is
removed from this helper, not silently translated. Runtime controls are unchanged except
the explicit diagnostic operation. This helper is source only, not built/installed.

Failure-only candidate metadata is bounded to one whitelisted sample, written once;
export failure preserves the primary exception. Endpoint/transport/evidence failures
are classified separately. Existing first-failure receipts, TTL/export timing, transport
checks and cleanup remain. Existing exporter fields now explicitly check gap/buffered
successor readiness; no new ACK token/export field is demanded.

Controller fixture retains base69 identity scaffolding because no successor version was
selected. It is **not** deployment-ready against sealed beta69: that runtime lacks this
operation. Successor artifact identity/provenance must be bound in a separate task before
any authorized installation/run. Missing targeted support rejects preparation, never
falls back to the old fault hook.

## Local tests and limitations

- Diagnostic `go test -race -tags=fc_owner_diagnostic` on sessiontrace, reliablestream,
  telemost, familysession, wholedevice, tcpforward: PASS (Go1.26.1).
- Default/public tests and race on the same six packages: PASS. Public beta66 JSON
  schema golden and no-default-endpoint/no-forensic-export regressions pass unchanged.
- Deterministic ordering tests cover writer-before/after atomic arm, queued-allocation
  before/after the command, cancel while allocation command waits, wrong scope/key/N/
  generation/attempt/expiry, terminal-before-drop, consumed-before-disarm, repeated
  commands and concurrent boundary count1. Queue fixtures model the common allocation
  seam; they do not claim a new physical Mux/bridge experiment.
- Real two-endpoint Reliable test confirms pre-arm reverse receive progress and either
  stale-head rejection/drop0 or N-only drop/retry recovery. ACK/retry is not blocked by
  an outstanding receiver prearm or operator preparation.
- Existing local bound-Pion test retained for generic path, plus targeted variants
  for1byte and16384byte payloads: actual packetization/RTP write → remote reconstruction
  → selected Reliable acceptance/consumption → token-matched actual ACK write → sender
  base27, ordered8 deliveries, buffered successor and2000-event ring flood: PASS.
  This uses local Pion track/write callbacks, not a Telemost physical session.
- Python existing control/correlation/privacy checks:49 PASS. Controller5 tests PASS,
  including execution of actual preparation AST block with mocked receiver/sender for
  success/rejection and no traffic after rejection.
- git diff --check PASS; no release emulator workflow or hosted CI run.

Initial Unix socket test inside sandbox was rejected by sandbox; authorized local
outside-sandbox tests passed. One Python invocation from the evidence directory failed
module collection; rerun from the isolated source root passed. These tool/environment
receipts are retained, not hidden runtime/physical retries.

## Full source scope

| File | Purpose |
|---|---|
| carrier/reliablestream/stream.go | Bind diagnostic allocation owner at creation |
| carrier/reliablestream/target_default.go | Compile-time no-op; no public state |
| carrier/reliablestream/target_diagnostic.go | Current head under allocation mutex, context liveness |
| carrier/reliablestream/targeted_test.go | Actual endpoint/allocation order and reverse progress |
| carrier/sessiontrace/targeted.go | Diagnostic atomic callback/control receipt/deadline binding |
| carrier/sessiontrace/fault_enabled.go | Exact drop predicate, terminal/count preservation, targeted-only mode |
| carrier/sessiontrace/correlation_command.go | Existing protected route, strict targeted request |
| carrier/sessiontrace/targeted_test.go | Ordering/cancel/expiry/key/control/bounds/count regressions |
| carrier/sessiontrace/watch_disabled_test.go | Explicit targeted command disabled in public build |
| carrier/telemost/watch_test.go | Retain generic and add targeted full pinned-chain/gap regression |
| scripts/owner_targeted_retry/controller.py | Source-only single targeted preparation and failure classification |
| scripts/owner_targeted_retry/OwnerSelectedRetryTest.java | Source-only helper targeted acknowledgement; no generic arm |
| scripts/owner_targeted_retry/preparation.py | Bounded candidate validation/diagnostics, no reservation claim |
| scripts/owner_targeted_retry/test_preparation.py | Controller mocks and no-fallback contracts |
| docs/STATUS.md, docs/PLAN.md, this report | Isolated candidate status/scope/next action |

No production package resources/permissions, native payload, gateway artifact, version,
tag, TLS/Mux/TUN/codec/RTP/Reliable retry semantics or wire bytes changed. Sealed beta67/
68/69, manifests, original FAIL/UNKNOWN receipts and prepared gateway observer preserved.
The observer was not run. No install, deploy, credential renewal, restart, external
prearm/arm/drop, Krasnodar, soak, signing or publication.

PASS is **local source acceptance only**. Next is separately authorized successor
packaging/provenance; no physical run is authorized by this result.
