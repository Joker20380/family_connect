# HA-02 — receiving notice-export completion

Date:25 November2026. Selected task:CONTROL-HA-20261123 / HA-02. Source/package checkpoint,
not a product release, installed receiving-side barrier, coherent capture or HA-03 cutover.
Queue: [PLAN](../PLAN.md); current state: [STATUS](../STATUS.md).

## Concrete defect and repair

The [working OWNER publication database boundary](2026-11-25-control-ha-publication-boundary.md)
does not prove the receiving HTTP handler finished publishing its files. Inspection found a
specific receiver-side bug in legacy `Notices.export_all()` / `export()`:

- Each output used a separate SQLite transaction/time. A concurrent edit or expiry could separate
  the v1/v2 snapshots, and exceptions before the old export's `try/finally` left its transaction open.
- File data was fsynced, but rename's parent directory was not; a successful return did not
  include directory-entry durability confirmation.
- The HTTP handler catches export exceptions and returns503. Without an `external_operation()`
  boundary, the enclosing capture operation then appeared successful and removed its pending
  marker despite a partial external file publication.

The last defect is reproduced against the retained pre-change source from Git with a nonempty
synthetic notice: fail the second rename, catch the exception as HTTP does, then observe v1
present/v2 absent, pending0, and **incorrectly successful drain**. No working files or DBs used.

`scripts/service_notices.py` now exports both versions inside one `BEGIN IMMEDIATE` transaction
with a shared timestamp. Each temporary file gets its final0644 mode before file fsync, then
atomic rename and parent-directory fsync. Serialization/tempfile failures roll back the export
transaction instead of leaking its lock. Commit and all export cleanup remain inside the
uncertainty boundary; caught exceptions cannot erase the gate's persistent pending marker.
Single-version `export()` follows the same completion rules. HTTP APIs, notice IDs and public
feed schemas do not change; legacy v1 immutability and v2 revisions remain covered by tests.

**The two renames are not an atomic pair.** A crash may leave one new output and one old/missing
output. The safety property is refusal to declare such an operation settled, not undoing files
or falsely claiming atomic publication. Publication rows already committed before export are
preserved. A later successful idempotent retry repairs files but does not clear earlier uncertainty.
No marker-clearing or forced reconciliation tool is introduced.

## Validation and evidence

Final run **13:12:51.296022–13:14:10.003449UTC**, including disposable PostgreSQL startup/removal:
**146 PASS,0 skipped;18 new tests**, pytest reports73.84s. Python3.14.4, pytest9.1.1,
psycopg3.3.9; all26 control/identity lockfile pins match. Existing repository contracts exercise
both SQLite and real PostgreSQL17.11 using the pinned image
`sha256:18cfe3ef5e6815560c98237d6216d1e5119702fb0f3894c8785dd58b8bbe5d73`.
The owned synthetic PostgreSQL container is independently confirmed absent after cleanup.

```sh
python -m pytest -q tests/test_notice_publication_boundary.py tests/test_device_notices.py tests/test_capture_gate.py tests/test_capture_gate_integration.py tests/test_notices_repository.py
```

Use `scripts.enrollment_postgres_rehearsal.Rehearsal` and its private synthetic port/password-file
environment for the real-PG selection, not a product database. New cases verify:

- File fsync → rename → directory fsync ordering for each version while the gate is held.
- Failure at either file's fsync/rename/directory sync preserves pending even after a successful
  retry; serialization, tempfile and native SQLite COMMIT denial release the export transaction.
- Both versions hold one SQLite writer lock and share a timestamp; public file modes and
  temporary-file cleanup remain correct. Canonical DB-only publication still refuses file export.
- Actual separate receiver process pauses after the first durable file: drain refuses. Resume
  completes both outputs; real SIGKILL preserves pending and partial output, even after retry.
- A real local TCP server runs the existing HTTP Handler and notice publication code. It sends
  no ACK while the first export is paused; successful completion returns200; a caught export
  error returns503 without losing pending. A real client TCP reset loses the ACK, allows server
  file completion and retains uncertainty. The reset case also passes three extra repetitions.
- A freshly built closed Friends HTTP archive runs the same export/gate in an isolated `-I`
  process outside the repository, without falling back to checkout imports.

HTTP fixtures redirect only the hardcoded output destination to private synthetic storage and
inject pauses/failures at explicit export boundaries; they do not substitute successful publish
results, database transactions or filesystem operations. Handler completion is explicitly awaited,
not inferred from stopping the listener. Process-death tests kill only their own synthetic child.

An earlier broader exploratory selection returned87 PASS/16 skipped:15 existing nginx/TLS
activation cases require `FC_TEST_NGINX`, and one existing sync-archive interoperability case
requires `FC_TEST_SYNC_ARTIFACT`. Those are **not** claimed passed or a release gate. The final
146-test changed-risk selection above has no skips; no HTTP ingress/TLS configuration is changed.
An initial16-case source test also passed before adding TCP-reset/package cases. Counts are not
summed as separate acceptance results.

Private evidence locator: `/tmp/fc-ha-notice-boundary-current`. Authoritative `final.xml`,
`final.log`, `run.json`; baseline reproduction, candidate manifest, health and earlier exploratory
logs retained alongside. Raw token files, synthetic DBs, TLS fixtures, runtime artifacts and
execution state stay beneath private directories outside Git/CI. Safe digests:

| Artifact | SHA256 |
| --- | --- |
| Export source | `06a82c948cf8a6e37e90ff96a46e08f697784c1060ea9fb1dec7ceeedd5c1f5a` |
| New tests | `30c97dcfe91390206c790b65cc70d58f9b365280078d5def52ff1696c9623d2d` |
| Final JUnit | `3469b953e838142a00881971a518680c831010ce3be667a8190945bbd9855563` |
| Baseline failure reproduction | `3e6e0e64672b5b0c5140be2fe11ca63f83524b5855aed577fc8bbaf2cfc435f9` |
| Candidate manifest | `ee22e4b938e191add1a6f566ac8b8b441b5ab9d779e45e72febc0084eafa91b2` |
| OWNER health/timers | `4a3d259230c10b1e7c320717178d2742fc266b64a47895dac2d7ce00d6bbb520` |

## Rollout, rollback and remaining boundary

Closed Friends HTTP candidate SHA256:
`cd33328c1159cbf5c3ebb3f0028ec4a91c969f08750458c1cf7189dadbb898c5`.
Built and isolated import/export tested, **not installed or publicly distributed**. Historical
served-source pins are not rewritten to pretend this candidate is deployed. No application
version, public installer/catalog/download link or invitation-page version changes.

Read-only OWNER observation confirms the same console/publisher/PostgreSQL image pins as the
preceding checkpoint, healthy with0 restarts; console health200 and both collector timers active.
No remote hosts contacted, live notice files edited, containers replaced or policy changed.
There is no working deployment to roll back in this checkpoint. Retain the existing installed
runtime; source rollback means reverting the source change normally, not resetting published
Git history. A future installation must preserve its exact runtime/config prestate, current DBs,
feeds and uncertainty evidence. Never restore a stale product DB, delete pending markers, kill
an old publisher or restore the unsafe implementation as a way to obtain capture permission.

This repair qualifies receiving-export **source completion**, not the old installed handlers.
Without an already installed outer gate, `external_operation()` cannot create a retroactive
marker or prevent arbitrary manual writers. Successful file checks alone are not admission
closure. Filesystem stalls can still outlive a drain timeout; timeout means refusal, not permission
to kill the receiver. Native process-death/fsync tests are not a host-power-loss storage guarantee.

Next: qualify/adopt receiving source with independent old-work settlement and remaining support/
manual coverage, then actual gate/runtime attestation and guarded startup/abort. Existing OWNER
ingress/dispatcher/PG boundary/stopped-replacement components remain qualified; do not repeat
them as new gates. Fleet participation, coherent capture, independent custody/trust/approval and
final combined current recovery remain. Replication PASS in isolation; the same three HA-02
acceptance gates are partial. No HA-03 cutover, automatic RU-independent failover or new ETA.
