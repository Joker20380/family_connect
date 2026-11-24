# CONTROL-HA — opt-in local admission and drain, 24 November 2026

Selected task: **CONTROL-HA-20261123 / HA-02**, not HA-03. This is a source-only
implementation checkpoint on `feature/device-technical-metadata-20261115`, based on
`0e282c34f16b08d55c8d3bda1a64103d6ff91cea`. No host connection, service deployment,
version bump, catalog/signing change, live capture or recovery acceptance occurs here.
The current [writer-boundary contract](2026-11-24-control-ha-writer-boundary.md#minimum-boundary-contract)
and four existing HA-02 acceptance gates remain authoritative.

## Pinned renewal dispatch continuation

This source-only continuation is based onfd378475. It adds an explicit admission wrapper
for the existing offline renewal coordinator, online coordinator, node CLI and scheduled
credential/directory evaluator. Native entrypoints remain unchanged and **ungated unless
invoked through this wrapper**. No installed service, SSH route, watchdog or policy changes.

`deploy/friends/restricted/maintenance/capture_entry.py` runs only with isolated Python,
a caller-supplied SHA-256 of the exact capsule manifest, an existing gate and a fixed
entry name. The new capsule includes this launcher in `source_files` and the shared
`control/capture_gate.py` in its pinned API library. Both credential and online packagers
inherit these additions; the accepted historical `API_MEMBERS` hashes remain unchanged.
New packages require a source commit containing the new files. Existing immutable capsules
are not rewritten; rebuilding an old source uses its own historical packager.

Before importing a native entrypoint or reading its config/stdin, the launcher verifies
the manifest pin, unbound/no-permit metadata, exact flat source inventory and every source
hash, and the API archive hash. Symlinks, unsafe ownership/write modes, hardlinks, oversized
files and unexpected files/bytecode caches are refused. The verified API descriptor stays
open throughout execution; the gate must actually import from that descriptor, not a
host checkout. This assumes a trusted interpreter/dependency environment and no concurrent
replacement of the approved source directory; it is not an immutable-source attestation
or a replacement for independently approved deployment hashes.

Source-only invocation shape, **not an installation instruction**:

```sh
python -I -B "$CAPSULE/renewal/capture_entry.py" \
  --manifest-sha256 "$APPROVED_MANIFEST_SHA256" --capture-gate "$GATE" \
  --entry scheduled -- --config "$CONFIG" --ssh-key "$SSH_KEY" \
  --known-hosts "$KNOWN_HOSTS" --gateway-routes "$ROUTES" --directory-only
```

Other fixed entries are `renewal`, `online` and `node`; arguments after `--` go unchanged
to the existing parser. `online` requires the actual online capsule; it is refused in
the classic capsule. No arbitrary module/shell entry, network discovery, gate initialization,
source fallback or automatic retry is added. Native root requirements, authorization,
maintenance approvals and existing transaction/recovery rules still apply.

Admission encloses native imports, config/DB/file access, the whole coordinator sequence
and native return. Closed admission returns redacted `CAPTURE_BUSY`/75 before native work.
Successful `None`/0/`SystemExit(0)` settles only its own marker. Nonzero returns/exits,
exceptions or process death retain uncertainty. This intentionally also retains a marker
for a native read-only evaluation returning75: the wrapper does not guess from a status
whether all external effects are settled. Removing such a marker requires independent
reconciliation; a later successful run cannot erase it.

`SshNode.call` now encloses RPC execution **and all response validation** in the current
operation's external-uncertainty scope when the shared gate is loaded. Timeout, invalid
reply/binding, remote rejection, failing exit or readback error remains uncertain even if
the coordinator catches it and subsequently retries successfully. Legacy transport does
not import, initialize or require the gate. SSH routes,120s timeout and native rollback
semantics are unchanged; no timeout is treated as remote cancellation.

### Renewal validation

All runs use `/tmp/fc-control-ha-20261123/venv/bin/python -m pytest -q`.

- **319 passed,1 skipped,22 deselected**: `test_capture_renewal.py`,
  `test_package_credential_renewal.py`, `test_renewal_profile_routes.py`, `test_capture_gate.py`,
  `test_activated_maintenance.py`, `test_multi_gateway_renewal.py`, `test_online_renewal.py`,
  `test_serialized_renewal.py`, `test_abort_unacquired_renewal.py`,
  `test_reconcile_unprepared_renewal.py`, `test_online_runtime_package.py` under `tests/`.
  `FC_ONLINE_GO=/tmp/fc-ios-tools/go/bin/go` (Go1.26.1) builds the actual deterministic
  online capsule and exercises its launcher. The one skip requires a separately pinned
  accepted historical carrier source/native validator, not this current package.
  The22 disposable-root/SSH-stand cases were explicitly deselected: packaged node/process,
  controller entrypoint, online commit, NL failures, SIGKILL resume, seed-timeout and RPC-loss
  scenarios. They are not claimed as passed; root/remote receiver qualification remains.
- **305 passed,8 skipped**: final `test_capture_renewal.py` (including the added fresh-process
  legacy/no-gate check), `test_control_ha_renewal_v1.py`, `test_control_ha_renewal_history.py`,
  `test_control_ha_maintenance_v1.py`. The8 skips require the separate real PostgreSQL
  import/recovery rehearsal. Retained-state schema/history adapters still pass their local
  checks. Counts overlap; do not add them into a distinct-case acceptance total.

New fixtures cover classic and online package execution with `-I -B`, hash/inventory/
permissions/source-cache refusal, busy before native config/stdin, no implicit gate creation,
normal/exception/nonzero completion, a real admitted process surviving drain timeout then
retaining its marker on SIGKILL, caught malformed/lost/rejected SSH replies, successful
retry and success-only cleanup. All network responses are synthetic; no live SSH occurred.
Native renewal rollback/replay tests run unchanged. No OWNER/PG/Windows/live fleet acceptance
is inferred. Documentation links and whitespace are checked before commit.

### Renewal boundary limits and rollback

This provides opt-in **entrypoint** coverage, not a fleet transaction fence. Direct calls
to `node.dispatch`, other forced-command handlers, AWG registration, legacy restricted-sync
and manual operator dispatch are not automatically covered. Current seven-argument SSH
routes are deliberately not rewritten to the wrapper. Node RPCs span a multi-step remote
transaction: gating one RPC does not prove the interval between RPCs is safe, or that a
successfully started external service has finished its own work. Actual controller/receiver
bindings and independent external completion remain mandatory. OWNER PostgreSQL/synthetic
publishers remain outside this continuation. Paid-watch/deny enforcement stays running.

No host access, production capture, package installation, version bump, public artifact,
grant or signing change occurred. No installed rollback is needed. A later approved
enablement must first qualify source/argv/UID/mount/gate-inode bindings, busy75 behavior,
flush latency and existing watchdog budgets. To withdraw it, cancel capture and release
its guardian before restoring original dispatch; retain all pending evidence/current
transaction state. Do not delete markers, restore stale credentials or start previously
failed/inactive services as rollback. Same four HA-02 gates: replication PASS; current
independent approval, coherent capture and complete independent recovery still partial.

## Scheduler and payment dispatch continuation

The next source checkpoint is based on1015ac5e. The same opt-in boundary now covers the
standalone chat-sync timer, paid-node reconciliation timer and paid operator CLI, not just
HTTP and the legacy product worker. No server is contacted and no service/unit/forced-SSH
configuration, live grant, payment record, installed version or catalog is changed.

- `deploy/friends/chat-sync.py --capture-gate PATH` acquires admission before constructing
  Access and holds it through mailbox acknowledgement **and** support-file publication.
  Busy returns75 before registry/network work; other errors return1 and retain uncertainty.
- `control.friends.transport_reconcile --capture-gate PATH` encloses the complete node
  cycle, including command-file reads and snapshot generation. Busy returns75 before I/O;
  unavailable configured state fails closed. Remote call **and ACK validation** run inside
  the uncertainty scope even though the existing cycle catches errors and continues to
  other nodes. Duplicate ACK fields, boolean schema, wrong node, oversize or invalid JSON
  cannot count as success. Existing12s per-node timeout and partial-cycle return code remain.
- `control.friends.paid_beta_admin --capture-gate PATH` encloses registry connection,
  transaction and commit for mutations/status; busy returns75 before opening the DB.
  Existing errors keep the original redacted responses. The `policy` action intentionally
  remains read-only and ungated, without opening a registry or gate directory.
- `transport_membership.prepare_nodes` retains uncertainty for each external prepare/ACK.
  A failed/lost ACK can leave a prepared node even when the canonical payment transaction
  rolls back and the caller catches the error. Such an error now refuses capture. A later
  successful ordinary retry does not erase that old marker or substitute for independent
  external reconciliation. Membership token/idempotency, eligibility, ledger and expiry
  semantics are unchanged.

The optional flag must be configured by the operator on each actual dispatcher; direct
library calls do not silently acquire a global gate. Old no-flag invocations remain legacy
behavior. Watchdogs, gateway run/preflight paths and denial enforcement are **not gated or
stopped**. The8s gateway operation/12s watchdog budgets and120s transport lease are unchanged.
This does not yet integrate credential-renewal/restricted-sync, arbitrary operator/SSH
entrypoints, receiver-side mutations or OWNER PG/synthetic/publisher containers.

### Closed scheduler packaging

`python -m scripts.package_capture_dispatchers --dispatcher chat-sync --output NEW.pyz`
and `--dispatcher paid-reconcile` create deterministic new source-only archives from the
current closed HTTP runtime manifest, adding only the selected entrypoint and no runtime
state. They refuse replacement of an existing output. They are **not overlays** over an
installed archive and do not weaken historical exact-source package pins. Tests execute
them with `python -I -B` from a temporary directory; the bundled chat module does not insert
the installed `/opt/.../app` into `sys.path`. Existing operator/restricted source manifests
include `control/capture_gate.py`, so the paid operator does not depend on a host checkout.
External Python dependencies still use the existing control/identity locks; this is not an
OS/dependency deployment kit. Archive bytes stay in temporary test directories, not Git.

The disabled gate and external uncertainty context no longer eagerly import POSIX `fcntl`.
This preserves pure-module/no-flag import behavior when that optional platform module is
unavailable; enabled locks remain Linux-only. It is not Windows runtime acceptance.

### Continuation validation and rollback

Using `/tmp/fc-control-ha-20261123/venv/bin/python -m pytest -q`:

- **200 passed,0 skips**: `test_capture_dispatchers.py`, `test_capture_gate.py`,
  `test_capture_gate_integration.py`, `test_transport_membership.py`,
  `test_transport_enforcement.py`, `test_transport_http.py`, `test_paid_beta.py`,
  `test_paid_beta_cli.py`, `test_paid_beta_http.py`, `test_support_package.py`,
  `test_restricted_runtime.py` (all under `tests/`).
- Additional historical/package/budget run: **22 passed,4 failed,0 skips** across
  `test_paid_policy_package.py`, `test_transport_package.py`, `test_transport_budget.py`
  and `test_transport_command_budget.py`. All4 failures reproduce on an isolated unchanged
  archive of1015ac5e with read-only access to existing Git objects: the closed transport
  overlay fixture and historical RU diagnostics/lifecycle/v2 recovery package fixtures.
  Existing `UNRELATED_PAID_DELTA` / `POLICY_CHANGE_FORBIDDEN` source-pin rejections remain;
  historical pins are not weakened and these old packages are not qualified or deployed.
- Final focused/package/budget run after review: **39 passed,0 skips** across
  `test_capture_dispatchers.py`, `test_paid_policy_package.py`, `test_transport_budget.py`
  and `test_transport_command_budget.py`. This overlaps the other runs; do not sum them
  into a distinct-case acceptance count.

Fixtures exercise DB rollback with retained external uncertainty, success/retry, real
dispatcher death and guardian timeout without killing active work, isolated packaging and
policy readback for the accepted release descriptors. Gateway/SSH/payment interactions
use synthetic local fixtures, not live hosts. No PostgreSQL/OWNER or Windows gate is claimed.
Documentation links/whitespace are checked before commit.

No installed rollback is needed. Before any later enablement, qualify all effective
argv/source/gate-inode/UID/mount bindings, load/flush latency and timer handling of busy75.
Do not automatically add a systemd success override or suppress genuine failures. Removing
the flag is allowed only after cancelling capture and releasing its guardian, while
preserving uncertainty evidence. Never delete markers or restore an older ledger as rollback.
Current NL permission still excludes changes to working services.

Next within the same HA-02 gate: remaining credential/restricted renewal and operator/SSH
dispatchers, receiver-side bindings and independent external completion, plus OWNER
PG/synthetic publishers, before an overlapping fleet capture. Independent current approval,
off-laptop key/access custody and final combined recovery remain. Replication PASS; the
other three acceptance gates remain partial, with no new lettered stage or HA-03 cutover.

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
