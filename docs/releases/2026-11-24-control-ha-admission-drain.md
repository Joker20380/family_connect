# CONTROL-HA — opt-in local admission and drain, 24 November 2026

Selected task: **CONTROL-HA-20261123 / HA-02**, not HA-03. This is a source-only
implementation checkpoint on `feature/device-technical-metadata-20261115`, based on
`0e282c34f16b08d55c8d3bda1a64103d6ff91cea`. No host connection, service deployment,
version bump, catalog/signing change, live capture or recovery acceptance occurs here.
The current [writer-boundary contract](2026-11-24-control-ha-writer-boundary.md#minimum-boundary-contract)
and four existing HA-02 acceptance gates remain authoritative.

## Implemented boundary

`control/capture_gate.py` provides an opt-in, Linux, **single-host/single-UID cooperative**
gate. It is disabled without a configured path. The exclusive initialization creates a
new private0700 directory, two empty0600 lock files and private `pending/`. It refuses
existing state rather than resetting it. Participants pin device/inode identities and
refuse missing/replaced files, unsafe ownership/modes, symlinks, hardlinked/nonempty locks.
The directory and its ancestry must be operator-controlled on a local filesystem; this
is not protection against another root/same-UID administrator changing state underneath it.

An admitted operation takes shared admission and operation locks, creates and fsyncs a
randomly named pending marker, then releases the admission lock while keeping the operation
lock for its entire lifetime. Clean, settled completion removes/fsyncs only its own marker
before releasing the operation lock. Nested operations reuse that scope. An exception,
killed writer, caught external RPC timeout or failed external readback retains uncertainty.
Markers contain no device/customer payload or exception details. Existing uncertainty
does **not** block ordinary traffic, but always refuses capture, including after restart.
An empty process/lock sample cannot erase it. There is no automatic marker-clear command.

The drainer exclusively closes new admission, waits at most5s for admitted operations,
then requires the pending directory to be empty. Unknown entries also refuse. Busy or
unsettled state releases its own locks without terminating the writer. Concurrent
coordinators cannot release each other's boundary.

`python -m scripts.control_ha_capture_guard` owns the locks in a separate pipe-driven
process. `--gate PATH --initialize` only initializes new local state. Normal operation
uses `--drain-seconds` (maximum5) and `--hold-seconds` (maximum2). A default-action kernel
alarm bounds the entire attempt to drain+hold, at most7s, including setup; an inherited
blocked/ignored/replaced alarm or existing alarm timer refuses before acquiring locks. The remaining
hold interval never extends the total deadline. There is no shell/capture-command dispatch
or persistent maintenance flag. The `LOCAL_DRAINED` receipt reports pinned identities,
remaining hold time and a fresh token; exact `RELEASE <token>` or input EOF releases it.
SIGKILL/alarm expiry releases the OS-owned locks. Every receipt deliberately says
**`capture_permitted: false`**: a local gate is not fleet coverage or capture permission.

The low-level `Gate.drain()` context bounds only the wait, not caller hold time; the
standalone guardian is required for bounded ownership. Kernel-uninterruptible I/O,
stopped/suspended processes and host scheduler failure can delay signal handling; do not
claim this repairs the RU storage-stall cause or proves the fleet watchdog budget.

## Participating source paths

| Surface | Opt-in behavior | Remaining boundary |
| --- | --- | --- |
| Friends HTTP zipapp | `--capture-gate PATH`, route validation/four-request capacity check before admission;503 on closed/unsafe gate before proof/DB mutation; whole admitted handler holds the operation scope | effective deployed argv/source/UID not changed or attested |
| HTTP diagnostics and metadata retention | both background threads share the configured gate; skip a blocked prune and continue the existing schedule | standalone collectors/other retention writers not automatically included |
| HTTP routing administration | gate wraps `administer`, not just HTTP requests | other admin/SSH entrypoints need explicit integration |
| HTTP gateway registration and chat sync | external call plus reply validation retains ambiguity even if handler catches the error | standalone chat-sync scheduler still needs admission; a timeout is not remote cancellation |
| Product admin | optional global `--capture-gate PATH` before subcommand; admission precedes `ProductStore` construction; busy exits75 without DB creation | direct model imports do not acquire the gate implicitly |
| Legacy peer worker | forwards the option to the admin child; scope covers cycle/queue/file/Docker work; external timeout or failed verification retains uncertainty | installed worker argv/mount/user and independent Docker completion proof still absent |

The HTTP runtime manifest includes the new module. No installed systemd unit, Docker
configuration or writer account is modified. The gate has no dependency on product keys,
retained recovery secrets or network availability. This change does not claim request
idempotency improvements or automatically retry rejected mutating requests.

## Historic recovery compatibility

`control_ha_worker_custody.PINS` remains unchanged: all11 retained source files still
require their exact historical digests during capture/validation/restore. Tests preserve
the three changed public wrapper sources in `tests/fixtures/control_ha_worker_v1_sources.json`
with the original source commit; these are source fixtures, not a private state capsule.
Offline qualification executes model/schema code and in-memory adapters, never the
admin/worker entrypoints or Docker adapter. Its local source check now explicitly selects
the8 unchanged pinned model/schema files used by that path. Tampering with any of the8
still refuses. Tampering with any of the3 retained wrapper sources still refuses custody.
This does not relabel the new gate-enabled source as installed or recapture old ciphertext.

## Validation

**170 focused tests PASS,0 skips**, using `/tmp/fc-control-ha-20261123/venv/bin/python`:

```text
python -m pytest -q tests/test_capture_gate.py tests/test_capture_gate_integration.py
  tests/test_control_ha_worker_custody.py tests/test_peer_worker.py
  tests/test_gateway_adapter.py tests/test_gateway_reconciliation.py
  tests/test_product_registration.py tests/test_product_provisioning.py
```

These are one invocation (the displayed lines wrap). Checks exercise real subprocess death/deadlines, simultaneous writers/coordinators,
packaged HTTP startup/admission, retention, CLI, worker propagation, caught RPC ambiguity,
and historic custody/native recovery. Gateway/Docker/SSH effects use fakes, not live commands.

Broader regression includes those files plus `test_friends_http_runtime.py`,
`test_technical_metadata.py`, `test_technical_metadata_overlay.py`,
`test_diagnostics_repository.py`, `test_chat_repository.py`, `test_friends_chat.py` and
`test_nl_replacement_routes.py`: **307 passed,93 skipped,3 failed**. The93 are explicit
optional real-PostgreSQL contracts; no new PG capture/acceptance is claimed. The3 failures
are reproduced on an isolated archive of unchanged baseline0e282c34: two historical
technical-metadata overlay reverse-patch fixtures and the old NL chat-sync fake missing
`access.enrollment_repository`. They are not hidden or repaired in this task. The final
focused run additionally includes the two inherited-alarm refusal cases. Both runs report
the existing Starlette/httpx/anyio deprecation warnings. Documentation links and whitespace
are checked separately before commit.

## Rollout, rollback and remaining gate

Nothing is deployed, so no live rollback is needed. Existing no-flag behavior remains the
default. Before any deployment, bind every participant's effective source, argv, gate
path/inodes, UID and namespace/mounts; one unconfigured writer invalidates the boundary.
Each successful operation adds three synchronous flushes (marker, pending creation and
pending removal); workload/storage-latency qualification is required before enabling it
on RU. A source-level deadline is not evidence that the extra I/O is safe on that host.
Do not delete/reinitialize/replace gate state while participants run. Preserve uncertain
markers and reconcile external work independently; never clear them to manufacture PASS.
Any future removal of the opt-in flag must first cancel capture and release its guardian,
preserving uncertainty evidence; it restores legacy operation, not a valid capture boundary.
Do not disable paid-watch, extend grants, or restart previously failed services as rollback.

Next selected work remains the same boundary: integrate schedulers/CLI/forced-SSH and
OWNER PG/synthetic publishers, bind gateway/membership participants, prove external
completion, and qualify an overlapping fleet interval under existing local safety limits.
Current NL authorization covers checks/isolated recovery, **not working-service deployment**.
After coverage is complete: one coherent capture, independent approval of that exact current
checkpoint, independent off-laptop key/access custody, then final combined post-ACK and
stale-copy recovery. Replication stays PASS; the other three HA-02 gates stay partial.
