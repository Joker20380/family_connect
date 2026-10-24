# MESH-PERF-3B fixtures and task-scoped operator evidence

## D02.1: explicit local historical suite

Ordinary pytest excludes **only** the six files below, not this directory. They
require the historical overlay API, absent from current `control/friends`.
`test_canary_environment.py`, `test_canary_prestart.py`, `test_timing_preflight.py`
remain ordinary tests. Explicit direct pytest of an overlay file fails BLOCKED;
use `run_history.py`, never seal/stage/deploy/readback helpers.

`historical-suite.json` pins the public source files to commit
`76df691961aa88a46b73e7a355687fa6f9a3c457`. The required sealed owner API is SHA256
`78a69db8f4e48ee89cf132ea279287dbfc71bdf8d9ae69c205bcaa0e19932a46`, already containing
`api-overlay.patch` over original API `12ca0c72a89ff20c1b3c70a1182a2d5d98d4d78d25e7a079bb4d75bdf34060ed`.
Provenance: existing `docs/releases/2026-10-18-mesh-perf-3b-evidence.json` and
`build_successor_api.py`; neither is executed or modified. The runner checks the
archive, owner/restricted members, historical fixture helper, tests, overlays and
`tests/vectors/bootstrap-timestamps.json` (SHA256
`a542d50e3b3645b9cd1813619ffb075fd3777d2a2473bd079d05ef83a8b2aca2`)
before starting Python. No reconstruction from main. The vector is read at helper
import, not just by the helper's own tests.

| File | Exact inputs beyond sealed owner API | Per-file command suffix |
|---|---|---|
| `test_owner_handoff.py` | historical `tests/test_friends_restricted.py` + bootstrap vector | `--test test_owner_handoff.py` |
| `test_cleaned_allocation.py` | same helper and `test_owner_handoff.py` | `--test test_cleaned_allocation.py` |
| `test_live_operator.py` | historical `live_operator.py` | `--test test_live_operator.py` |
| `test_successor_lifecycle.py` | owner tests/helper/vector + successor overlay; original API, delivery-check, Java runtime/classes/three JARs | `--test test_successor_lifecycle.py` |
| `test_successor_migration.py` | lifecycle Python sources + `successor_migrate.py`; original API for database default | `--test test_successor_migration.py` |
| `test_successor_operator.py` | lifecycle Python sources + `successor_live_operator.py`; runtime files supplied by disposable fixtures | `--test test_successor_operator.py` |

All thirteen public files are checked/copied for every selection. Retained inputs
are required only by the files in `retained_inputs.*.required_by`; importing a
lifecycle fixture does not execute its native/Java test. The baseline helper's Go
test is not collected by this runner, so it does not require a Go source checkout.
Operator tests replace systemctl/process/root access with their existing disposable
fixtures; no live command or real material/database/receipt is an input.

Preparation and **attempt** of the full six-file set (explicit local paths, never
auto-discovered in state):

```sh
mkdir -p /tmp/fc-mesh-history-inputs
git archive 76df691961aa88a46b73e7a355687fa6f9a3c457 tests/test_friends_restricted.py tests/vectors/bootstrap-timestamps.json tests/fixtures/mesh_perf3b | tar -x -C /tmp/fc-mesh-history-inputs
python tests/fixtures/mesh_perf3b/run_history.py \
  --source-root /tmp/fc-mesh-history-inputs \
  --api-archive /explicit/preserved/friends-http-owner-candidate.pyz \
  --original-api /explicit/preserved/deployed-api.pyz \
  --delivery-check /explicit/preserved/delivery-check \
  --java-runtime /explicit/preserved/jdk \
  --java-classes /explicit/preserved/java-floors-final-classes \
  --gson-jar /explicit/preserved/gson-2.13.2.jar \
  --junit-jar /explicit/preserved/junit-4.13.2.jar \
  --hamcrest-jar /explicit/preserved/hamcrest-core-1.3.jar
```

Append one table suffix for a single file; no suffix means the exact six-file set.
Use the prepared CI/test Python. Missing, mismatched, unpinned or unusable inputs
yield BLOCKED/NOT_RUN, exit 2, before pytest, never a skip/PASS or partial run.
Verified bytes and execute modes are copied into a disposable tree at the exact
test paths. Java classes retain package directories, runtime retains bin/lib, and
each JAR is the sole match of the unchanged versioned cache glob. Tree inventories
must cover exactly all files (symlinks are rejected). API/helper imports are checked
in isolated Python; native invalid-input and Java `--dry-run` probes check usability
without executing the test main. Only after preflight does a separate Python run
pytest, retaining its exit code. No inherited FC/SSH/PYTHONPATH or live commands.

### D02.1-R: unresolved retained provenance — historical suite NOT_RUN

Original API `12ca0c72…` is pinned and now included. **Six retained input pins remain
unresolved**, explicitly `null` in the manifest; supplying an arbitrary existing
file cannot bless it. The existing pinned `native-validator.json` records a build
command and exit/log, not the delivery-check output hash. Pinned
`java-floors-final.json` records source/log hashes, not compiled classes, runtime or
JARs. The local JDK download metadata is not an anchored retained-tree inventory;
Gson2.13.2/JUnit4.13.2/Hamcrest1.3 versions alone do not pin bytes. Both receipts
match the existing public evidence hashes; neither is rewritten. Before a full
run, recover independently anchored artifact pins/inventories for those six
inputs and review them. Do not rebuild from main, recompile classes, or hash local
files into new acceptance pins. Full historical replay is **not yet ensured**.

Regression coverage uses real pinned public sources/vector in an actual snapshot
and separate Python reader, plus explicitly synthetic executable/runtime/class/JAR
inputs. It checks fail-closed behavior, paths, modes and byte snapshots, not the
historical artifacts' behavior. Six historical tests/assertions remain byte-identical.

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
