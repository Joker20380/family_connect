# MESH-PERF-3B fixtures and task-scoped operator evidence

**Do not replay the closed live operation.** Current result and remaining gate:
`docs/releases/2026-10-18-mesh-perf-3b.md`.

Timing continuation adds only local/read-only checks:
`timing_preflight.py` takes explicit test clocks and calculates a conditional window;
it never starts or schedules anything. `timing_readback.py` and
`timing_guard_readback.py` use read-only SSH and exclusive protected output names.
`test_timing_preflight.py`/`test_cleaned_allocation.py`:23 PASS, including rejection
of a fresh operation by the exact sealed API after never-armed CLEANED cleanup.
Existing `live_operator.py` cannot allocate that next operation: do not remove the
retired row, reuse an old ID or launch a canary merely because arithmetic passes.
No new operation exists; `timing03-*` labels investigation evidence, not a start.

Authorized retry operation `mesh-perf-3b-20261018-02` is also **closed**. It reached
READY once, but no later production R existed inside its valid arm window. No
API/owner handoff/bulk; graceful canary cleanup is recorded under protected retry02.
`retry_canary.py` reuses the sealed candidate/fixed launcher; `canary_prestart.py`
checks real systemd environment-only and ExecStartPre configurations without provider
calls or values. `retry_readback.py`, `retry_policy.py`, `retry_cleanup.py` retain
bounded observations/cleanup; do not replay the exclusive fixed operation.
`retry_gate.py`/`ActualDirectoryGate.java` exercise real directory objects against
retained validators/cache ordering, with a stub native callback/disposable outer
metadata, not a device import.20 focused launcher tests pass. Initial read-only
failures/journal timeouts and no-TUN control preflight are retained, not hidden.
Previous15:30 receipts below remain historical, not overwritten by retry02.

- `api-overlay.patch`: applies only to extraction of deployed API ZIP SHA256
  `12ca0c72a89ff20c1b3c70a1182a2d5d98d4d78d25e7a079bb4d75bdf34060ed`.
- `gateway-owner-overlay.patch`: applies after the retained PERF-3 overlay, not
  directly to main or the accepted baseline. Adds an opt-in diagnostic build's
  fail-closed authenticated owner guard and local tests. Do not deploy the original
  PERF-3 binary as though it contained this guard.
- `test_owner_handoff.py`: exact extracted API plus overlay; disposable identities,
  SQLite serialization, nonce/revocation/Family/key checks, phases and floors.
- `make_fixtures.py [new-name]`: creates private disposable issuer/client profiles
  under the protected local task root. Exclusive directories; no production input.
- `check_floors.py [new-label]`: compiles unchanged retained Java cache sources and
  runs local JUnit/roundtrip checks; never builds or installs an APK. Its Java
  validity callback is deliberately a stub for floor testing; native validation
  is an independently recorded check, not implied by that callback.
- `run_checks.py`: locked local Go toolchain, offline modules, bounded local test
  commands and receipts. Loopback TLS tests need normal outside-sandbox execution.
- `seal.py`: one-time exclusive artifact/patch construction and source inventory;
  fails rather than overwrite accepted outputs. Current outputs already exist.

Continuation helpers are a fixed, explicitly authorized operation capsule, not a
general-purpose deployment workflow:
- `continue_preflight.py`: rechecks pinned artifacts/receipts, verified admitted
  identity/ACK and renewal pin. Private identity output stays outside Git.
- `live_operator.py`: serialized durable API preparation, explicit readback-based
  reconciliation and never-armed abort. It refuses blind replay and refuses code
  rollback if canary could have escaped. Forward transition gates are not live accepted.
- `stage_api.py`: one exclusive operation, exact argv and immutable archive; used
  once, then safely aborted. Its fixed manifest/deadline must not be reused.
- `stage_canary.py`: one isolated process with protected private state. The attempt
  failed before READY because its original launcher omitted provider.env. The current
  source includes a tested EnvironmentFile fix; that fix was **not** retried live.
  It passes the path to systemd, never the token in argv/output. Protected failed
  remote source is retained separately; do not confuse its hash with the local fix.
- `cleanup_probe.py`: one bounded post-abort Android-TUN HTTPS control with production
  PID socket attribution; no bulk test or physical throughput acceptance.
- `test_live_operator.py`, `test_canary_environment.py`, and three additional cases
  in `test_owner_handoff.py`:22 new final passing cases; failures retained in receipts.

Protected `state-client-build/mesh-perf-3b/` holds receipts and candidates. RU retains
a CLEANED audit tombstone and NL retains a failed, process-free unit descriptor;
no owner canary/return view or live override exists. An actual newer runtime-issued
production return directory still must exist before any future arming. Do not adapt
credential/global-directory commands, fabricate timestamps or reset floors to bypass it.

Do not commit private fixtures, identity material, rooms, candidate archives or
runtime receipts. Public fixture code and overlays contain no live credentials.
