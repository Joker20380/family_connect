# CONTROL-HA — receiver admission, 24 November 2026

Selected task: **CONTROL-HA-20261123 / HA-02**, continuing sourcee225db60. This is an
opt-in source checkpoint, not installation, a live capture, HA-03 or a new stage.
The [minimum boundary contract](2026-11-24-control-ha-writer-boundary.md#minimum-boundary-contract)
and the same four acceptance gates remain unchanged.

## Implemented boundary

`control.capture_receiver` provides a stdlib-only parent launcher for four fixed one-shot
native entries. It does not rewrite the existing receiver source, accepted archive,
forced-command route, service unit, lease or watchdog policy.

| Kind | Exact SSH original command | Fixed native arguments | Form |
| --- | --- | --- | --- |
| `awg-register` | `register`; local invocation also allowed only without SSH connection/original-command environment | `register` | Python script |
| `mailbox-membership` | `chat-sync` | none | Python script |
| `profile-snapshot` | `restricted-sync` | none | Existing Python archive |
| `fleet-agent` | `fleet-v1` | none | Python script |

No shell interpretation, forwarded caller arguments, arbitrary action switch, `run`,
`paid-watch`, fleet initialization/recovery, automatic retry or gate initialization is
provided. A native runtime's own authorization remains in force. The fleet-agent adapter
does not install or activate the separate fleet backend.

The required private binding is a0600 regular file owned by the launching UID. Its
SHA-256 must match the explicit `--binding-sha256` argument. Exact keys are `schema` (1),
`kind`, `capture_gate`, `entry_path`, `entry_sha256`, `libraries`; the last is a list of
at most8 `{path, sha256}` Python archives. Duplicate JSON keys, extra fields, mismatching
command/hash, unsafe mode/owner, hardlinks, symlinks, relative/noncanonical paths, missing
gate and invalid archives fail closed without native execution. Source and library files
must belong to root or the launching UID, never be group/other-writable or special files.

The binding is limited to64KiB, each native artifact/library to32MiB. Reads verify inode,
size, ownership/mode, mtime/ctime and the expected hash. Access time is not a content
identity. Verified bytes are copied into sealed Linux memfds: later modification of the
original pathname cannot change the entry or explicitly supplied archive bytes executed
by this invocation. Script syntax is checked without executing it. Archive duplicates
and traversal names are refused. No private runtime material is packaged or committed.

Only after acquiring the existing gate does the parent spawn isolated Python (`-I -B`).
The child gets fixed arguments, pinned read-only descriptors and the original entry path
as script identity; it cannot discover the developer checkout via cwd/PYTHONPATH. Standard
input/output remain the native protocol streams. The parent holds admission through child
exit, not just the first printed ACK; normal Python exit includes flushing its reply.
Wrapper diagnostics are redacted; native protocol/error output is not rewritten or logged
by the launcher. Busy returns75 before spawn or stdin consumption. Other refusal or native
failure returns1; a failure after admission retains durable pending.

If the parent dies, its OS lock may release while the child continues. **Pending remains**
and prevents capture even after that child later finishes successfully. A new successful
invocation cannot erase the older marker. Native death/nonzero exit and broken reply pipe
are also uncertain. The launcher does not claim that killing a client cancels its child,
sudo helper, Docker exec or remote effect; it does not terminate those processes as an
automatic rollback. Existing native timeouts and the separate bounded capture guardian
are unchanged.

`node.dispatch` additionally accepts an explicit enabled `capture_gate` for direct callers,
before schema/state/native dispatch. With an already loaded gate it marks dispatch
exceptions uncertain even when an outer caller catches them. It rejects an explicitly
disabled gate rather than pretending to protect a call. Legacy calls without a gate still
run as before; no gate import is forced into old capsules. New node source requires a new
source-bound capsule/configuration, not replacement of files under old accepted hashes.
The existing pinned renewal launcher remains the CLI boundary before node construction.

## Artifact and invocation

Build only; this does not install a forced command or change a service:

```sh
python -m scripts.package_capture_receivers --output /private/new-receiver-launcher.pyz
```

The deterministic archive contains only `control/capture_gate.py`,
`control/capture_receiver.py`, its namespace directory and `__main__.py`. Rebuilding at an
existing output path is refused. The tested archive SHA-256 is
`41558e807dd7d0cf4333ae9f64ff0d329e2dc7d1a45f484ec6537cbd9146760a`.
This is a locally built artifact, not a public/installed/client or invitation-page version.

Future invocation shape, **not permission to enable it on a working host**:

```sh
python -I -B /approved/receiver-launcher.pyz \
  --binding /private/receiver-binding.json --binding-sha256 "$APPROVED_BINDING_SHA256"
```

The binding hash must come from the independently approved record; recomputing it from
an unexpectedly changed file is not approval. The launcher artifact/interpreter itself
also needs an approved deployment pin. A verified entry/library does **not** automatically
pin every configuration, import directory prepended by native code, installed Python
dependency, external executable, helper or service. Those effective bindings and the
whole external-effect completion condition remain required before any coherent capture.

## Validation

- Final regression: **300 passed,1 skipped,1 deselected**,85.01s, using
  `/tmp/fc-control-ha-20261123/venv/bin/python -m pytest -q` with
  `tests/test_capture_receivers.py`, `test_capture_renewal.py`, `test_capture_gate.py`,
  `test_package_credential_renewal.py`, `test_renewal_profile_routes.py`,
  `test_activated_maintenance.py`, `test_multi_gateway_renewal.py`, `test_online_renewal.py`,
  `test_package_profile_snapshot.py`, `test_nl_replacement_routes.py` (all under `tests/`).
  The new receiver suite contains27 passing cases. Coverage includes all four command
  shapes, closed admission before native import/input, sealed entry/library execution,
  unsafe binding refusal, native/parent death, late child completion, ACK-before-exit,
  broken stdout and older pending surviving a later success. Renewal direct-dispatch
  failure and the existing capsule/gate tests are included; counts overlap prior runs.
- The one skip is `test_operational_authority_two_existing_identities_native_compatibility`,
  requiring separately accepted native source/toolchain. The explicitly deselected
  `test_chat_sync_uses_configured_host_and_keeps_pinning` uses an obsolete fake registry
  without `.access`; its identical AttributeError is reproduced from unchanged source
  `e225db603e595e8e86a15579f622f4a2d75c7ec7` in a fresh temporary checkout. It is not fixed
  as part of this receiver task and is not counted as PASS.
- An earlier broader attempt also selected `tests/test_profile_snapshot.py`: its22 cases
  refuse setup at non-root UID1000 and require their separate isolated root fixture. They
  are not claimed as passing. That attempt had299 PASS,1 skipped, the same unrelated
  failure and22 setup errors. The final selection above excludes that root-only file;
  the following native probe is not a substitute claim for all22 cases.
- **ISOLATED_NATIVE_RECEIVER_PASS** on pinned Python3.13.17 in an owned disposable root
  container (`tests/fixtures/capture_receivers/native.py`). Network is disabled, rootfs
  read-only; only private tmpfs fixtures are writable; all capabilities except CHOWN are
  dropped. The fixture refuses a non-container/unmarked/nonempty target. Actual unchanged
  AWG and mailbox receiver sources execute through the packaged launcher. AWG/Xray and
  systemctl commands are simulated, not real transport or service operations. Busy creates
  neither peers DB nor membership; registration succeeds and is idempotent; membership
  persists, replay fails and later success preserves pending. A failed TCP readback leaves
  a changed TCP file but rolled-back SQLite insert; pending correctly refuses capture.
  The container is removed after each run. The initial fixture address expectation was
  corrected from `.3` to the native allocator's existing `.2`; allocator code is unchanged.

Private logs/bindings/artifacts stay local, outside Git. Documentation links/whitespace
are checked before source publication. No profile-snapshot/fleet-agent live runtime,
actual AWG engine, production latency or fleet recovery acceptance is asserted here.

## Rollback and fixed remainder

No live deployment occurred, so no installed rollback is needed. Native serving artifacts,
fixed SSH routes, transport/watchdog deadlines, databases, versions and catalogs are
unchanged. Before any future opt-in enablement, bind every participant to the intended
gate/UID/mount and independently approved source/configuration. A source push does not
permit changing working NL services. Single-UID permissions must not be loosened to make
incompatible participants work.

For a future withdrawal, first cancel capture and let its guardian release admission;
restore the prior approved invocation and preserve all pending/current state for independent
reconciliation. Do not clear markers, restore a stale DB, assume orphan cancellation or
stop paid-watch/deny enforcement. Default native paths still bypass this opt-in wrapper.

Next: qualify effective installed participation (including manual entrypoints and any
remaining bypass), source/config/UID/mount binding, external completion and flush latency;
then perform a provably overlapping, independently approved capture and combined current/
post-ACK/stale-copy recovery with independent key/access custody. Do not redo the completed
OWNER/renewal/receiver source slices or NL2 recovery. Replication PASS; the same other
three HA-02 gates remain partial. No HA-03/cutover or new acceptance gate.
