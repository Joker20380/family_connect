# Opt-in transport readback candidate — NOT_DEPLOYED

Selected task: RU-PERSISTENCE-READBACK-1. This is an isolated source candidate, not
a change to RU or evidence of current availability. The historical 9.538854s
decision-file fsync exceeded the unchanged 8s budget; the underlying storage cause
is UNKNOWN. Reducing repeated commits cannot protect against every VPS/storage stall.

## Contract before qualification

18 November continuation: PR44 is merged; its historical open delivery question
is now under package/systemd qualification, not yet accepted. The new same-boot
`application-incomplete` intent fence prevents automatic reuse after failed/killed
application. `paid-recover` requires explicitly stopped units and preserves authority
and first failure. [Current evidence and exact remaining gates](../releases/2026-11-18-readback-delivery.md).
The older source-only limits below describe PR44, not an instruction to repeat it.

The default configuration retains the exact legacy two-durable-write readback.
The existing `test_converged_readback_keeps_both_durable_writes` remains mandatory.
Only a node configuration explicitly containing `readback_mode: observations-v1`
selects the candidate; unknown values fail. There is no automatic rollout/enabling
command. Do not edit a running node's mode as part of this source task.

Authority remains on the existing durable filesystem in `transport-state.json`:
decisions, revisions, leases/monotonic deadlines/boot binding, terminal denies,
membership preparation and confirmed applied changes. `accept` and `prepare` keep
their file-sync → replace → directory-sync sequence. Reconciliation, registration
and membership-preparation ACKs remain after application and all required syncs.
No lease, anti-replay, identity/binding or 8/12/120s limit is relaxed.

Every application cycle still loads authority, evaluates expiry/preparation,
reconciles configuration, queries real AWG twice and Xray users once, repairs
incorrect AWG bindings and verifies the complete expected result. A state change
between planning and readback retries rather than overwriting newer authority.
An actual repair/configuration change requires a durable applied confirmation
even when the final allowed set matches the previous one.

The candidate adds the full decision digest to each durable applied receipt. A
renewal with the same revision but a changed lease therefore cannot reuse the old
confirmation. Its schema-2 durable attempt binds the canonical state digest, boot
and producer `(PID, /proc start ticks, random instance generation)`. A new producer
or changed authority/application requires the state and attempt commits before
success. Forked producers refresh their identity. Missing/broken attempts cannot
produce a successful cached confirmation; they require real readback and commits.

For an unchanged, already confirmed state in the same producer generation, only
`transport-observation.json` is atomically replaced. This is disposable observation,
not authority: no fsync, no lease extension and no admission from this file. It
binds the exact durable state and attempt, producer/boot, complete per-device result,
completed readback wall time and monotonic time. There is no writer thread/queue.
The file is invalidated before enforcement or acceptance and on failed operations.
Its loss never loses a decision; it loses panel freshness until another readback.

## Freshness and consumers

The external collector acquires both application and registration locks shared,
nonblocking: an in-flight writer is `unavailable`, never a fresh applied result.
It validates file type/permissions/size, duplicate fields, state hash, exact receipt
and record bindings, living producer PID/start ticks, boot, decision proof, revision,
wall/monotonic age (at most12s), clock disagreement (at most5s), and current lease
expiry. Missing, corrupt, foreign-generation, dead-producer or stale observations
produce the existing explicit `unavailable`/panel source-error state with no devices.
There is no fallback to old durable applied timestamps in candidate mode.

On success both snapshot `observed_at` and row `applied_at` come from the completed
readback, **not collection time**. Output remains schema2, so existing immutable
console ingestion/UI retains its compatibility and error/previous-snapshot rules.
Legacy collector semantics are unchanged. Metrics use durable identity mappings
and their own real AWG counter queries, not applied receipt freshness.

Reconciliation and membership clients still require their unchanged bounded ACKs.
Candidate registration uses `serialized(failure_mode='register')`: the owned
application descriptor outlives both the operation's final deadline check and
fail-closed handling. The shared operation starts before opening the descriptor;
open latency consumes the same8s budget used by acquisition and the body, with
no fresh budget at either boundary. This covers acceptance/preparation, apply, and context-exit
errors; ordinary registration also prints its ACK only after context exit.
The first error/context is retained in memory, observation invalidated, protective
stop requested, error attempt written, and only then the first diagnostic receipt
persisted; application lock is released last. Cleanup errors are recorded safely
without replacing the original failure, and an already handled exception is not
handled twice by the outer context. Legacy's order/default remain unchanged.
Failure to open/acquire the lock never enters the registration body; it requests
stop without re-acquiring the same lock or closing another participant's descriptor.
This is a stop **request**, not proof of actual systemd termination. Diagnostic
fsync can still block, but a held application lock prevents competing application
and successful watch heartbeat; the real collector reports unavailable. See the
[P1 reproduction and new acceptance gate](../releases/2026-11-17-pr44-failure-serialization.md).
This exclusion proof concerns guarded **registration errors**, not every fail-closed.
The separate `watch → apply → unlock → external fail_closed` path already existed
on main380da279. If its asynchronous protective stop has not completed, a competing
registration can acquire the lock and succeed. This remains an open systemd/package/
deployment qualification question; the budget repair does not redesign watch or
prove the absence of ACKs during that interval.
Synchronous writes may still block; enforcement
does not send background heartbeat. Candidate startup wait sends no WATCHDOG before
the first completed application; READY remains dependency readiness, not applied
health. The existing systemd watchdog remains the external bound during startup.

## Isolated reproduction

Use the control/device-identity lockfiles and the panel hash-locked environment.
Run `python -m pytest -q tests/test_transport*.py`; separately run
`python -m pytest -q tests/test_transport_observations.py tests/test_metrics_collector.py`
from `control_plane` against a new synthetic PostgreSQL database. Existing data is
not a fixture. The new CI workflow also runs the selected legacy/risk groups and
builds the existing pinned AWG3.1/Xray inputs; it does not replace other gates.

Real-engine comparison, after building the existing native Dockerfiles and
`pilot/readback/Dockerfile`:

```sh
docker run --rm --network none --cap-add NET_ADMIN --device /dev/net/tun \
  -e FC_SOURCE_SHA="$(git rev-parse HEAD)" -e PYTHONDONTWRITEBYTECODE=1 \
  -v "$PWD:/source:ro" fc-readback:isolated
```

All keys/identities are generated solely for the disposable namespace. Authority
uses its ordinary container filesystem, not tmpfs. The test warms each mode once,
then compares six unchanged cycles with one real registered AWG/Xray user. Native
commands, filesystem syncs and collector output are real; there is no production
traffic, remote endpoint, Telemost or VPN-client claim. Processes are joined and the
container/network namespace removed. Receipts expose counts/source/native hashes,
not key/configuration values. Fault-injection tests separately model crash outcomes,
clock/deadline crossings and controlled concurrency; they are not a physical disk
power-loss or kernel-I/O cancellation experiment.

## Future rollout prerequisites — not authorized here

Review the candidate and exact-head CI/receipts first. A future delivery design must
pin the node archive, gateway entrypoint and collector together, verify installed
unit/source differences, and qualify cold-start/systemd ordering and enforced
watchdog termination on a disposable real systemd node. No `Restart=no` rewrite is
needed: it already exists in source. The old pressure observer reads durable
timestamps; it is **not** a candidate liveness monitor and must not be started or
used to certify this mode. Operator scripts requiring legacy attempt schema/fresh
state timestamps need a separately qualified delivery/readback procedure.

Only a separately authorized guarded rollout may alter production. Preserve current
decisions/leases/deny/preparation state; never restore older authority. A future
rollback must stop/fence, retain authority and restore the default configuration
with compatible verified bytes, then requalify ordinary durable readback. No
production migration/rollback has been performed by this task.
