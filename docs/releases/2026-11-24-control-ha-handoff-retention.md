# 24 November 2026 — closed handoff retention in canonical import and recovery

## Scope and outcome

Continuation of all selected HA-02 gates, after census7c8a5747 identified five additional
installed registry tables. This removes a concrete data-loss/import gap without making
the old adapter permissive or activating a new runtime. **Isolated retention/recovery/
replication PASS; HA-02 overall remains IN_PROGRESS.** No new stage or production cutover.

Additional bounded read-only RU observation found1 legacy row,2 successor operations,
1 current pointer,1 per-device security row and1 schema row; legacy/successors are all
CLEANED. The installed accepted HTTP archive contains no `handoff`-named Python module.
This is not proof of no external writer or permission to discard old floors. Only
aggregate counts/known phase names were returned; no identity/profile/key or row payload
was exported. Private shape receipt stays with the preceding census evidence.

## Explicit data-preserving adapter

[Handoff retention](../../scripts/control_ha_handoff_import.py) and the separate
`preflight_installed_sqlite` entry point require the exact29-table application schema
plus the22 pinned handoff definitions (five tables,17 indexes/triggers). Unknown DDL,
missing objects or v1-only schemas are not accepted by this new entry point. The old
`preflight_sqlite` still refuses the installed overlay. No live SQLite file is modified
or stripped: deserialized inputs are read-only; the five additional row sets are retained
alongside the ordinary canonical rows, not dropped from the recovery result.

Validation checks scalar types/bounds; CLOSED/CLEANED state only; canonical legacy digest
and exact migrated legacy values; contiguous unique generations/predecessors and current
pointer; prepare-input identity; existing-device references; security operation/generation/
scope; required historical floors and monotonic retained floor/directory order. Expired
historical floor documents remain evidence, not fresh grants. Duplicate JSON fields and
malformed data refuse. The verifier checks internal consistency and preservation, **not
missing historical consent, live publication authorization or issuer rotation**.

Canonical snapshot fingerprint includes exact handoff rows and profile provenance;
its private repr omits rows. All35 application/retained tables and14 marker/receipt/CRL
anchor tables import in one PG transaction. Handwritten PG DDL is fixed, not generated
from untrusted observed SQLite SQL. Handoff rows have no enabled runtime mutator:
INSERT/UPDATE/DELETE/TRUNCATE (including CASCADE) refuse after import. Closed history
cannot be reopened and security floors cannot be reset through this retained domain.
Schema/function/trigger fingerprints and exact readback participate in retry verification.

This is **retention**, not a PG port of operational owner-handoff administration. Any
future resumed writer needs separate semantics/fencing and activation qualification.
Existing product-family nonpublication guards remain in place; import still returns
`activation=FORBIDDEN`. Do not plug this adapter into a live endpoint or treat the old
forward capsule's v1-only loader as having acquired new acceptance implicitly.

## Native-format synthetic qualification

[Fixture](../../scripts/control_ha_handoff_fixture.py) checks the retained migration
source hash, uses temporary product identities/issuers and creates a native-shaped
closed legacy plus successor chain. No actual state/keys are used or committed.
[Runner](../../scripts/control_ha_handoff_rehearsal.py) uses the existing ownership-pinned
PG17.11 container lifecycle and private temporary evidence.

- **199 tests PASS,0failed,0skipped**:46 new handoff tests plus existing import,
  application-schema and census tests. Includes all-five-table immutability, TRUNCATE
  CASCADE, source mismatches/open operations/floor regression, exact retry/provenance and
  interruption after each retained table/before commit/after committed response loss.
- **28 existing commit/runner guards PASS,0failed,0skipped**.
- Full49-table import; SIGKILL with an uncommitted update; exact crash recovery; native
  dump/restore to separate PG instances; product transactions after restore; exact new
  acknowledged state; stale restore and old import refused; consumed proof replay refused.
- Full extended strict PostgreSQL17.11/Patroni4.1.5/etcd3.7.4 run **PASS** with49 tables:
  primary loss/return, DCS minority/majority and lease expiry, loss of both synchronous
  standbys, ambiguous disconnect and canceled sync COMMIT, no false successful ACK.
  Handoff rows remain exact on all copies. Local image/pins are unchanged from the
  [replication report](2026-11-24-control-ha-replication.md).

The first contract attempt had193 passes and one assertion mismatch: PostgreSQL's FK
guard rejected bare TRUNCATE before the retained-domain trigger. The test now explicitly
uses CASCADE and verifies the immutable trigger, without weakening production guards.
Final199-test/native run and extended replication run both clean up all owned resources.
The one-host lab does not establish independent WAN/production failure domains.

```sh
python -m scripts.control_ha_handoff_rehearsal --workdir /tmp/fc-ha-handoff-new
python -m pytest -q tests/test_postgres_durability.py tests/test_control_ha_replication_rehearsal.py tests/test_enrollment_rehearsal.py
```

Private evidence: `/tmp/fc-control-ha-20261124/handoff/`; `run-2/contracts.xml`,
`run-2/receipt.json`, `guards.log`, `replication-49/receipt.json`. Earlier failed evidence
is retained, not overwritten. The preceding live aggregate receipt is
`/tmp/fc-control-ha-20261124/installed-census/handoff-shape.json`.

## Remaining gates, authorization and rollback

Real production capture was not run. Schema recognition and a successful synthetic
import do not fence HTTP, operator queues, cron/forced commands, timers, gateway
publishers or offline writers. The existing eight refused pressure-unit observations
and unclassified writers remain explicit, not converted into PASS by table coverage.

The [previous forward-checkpoint approval](2026-11-24-control-ha-forward-checkpoint.md#authorization-and-scope)
was development without service stops/server changes. Original schedule approval was
not found in the bounded provenance investigation. A real owner-trusted approval key,
independent request pins/floors and bounded live capture authorization are still required;
generating a test signing key does not create owner approval. Do not infer historical
consent from the general request to complete HA-02 or replay old operation records.

Actual-current journal custody, complete writer/barrier coverage and full off-node
recovery of real stores/files/keys/checkpoints remain open. The new runner retains its
synthetic keys; independent PG restore is not a claim of complete fleet DR. No measured
ETA is available and no “one last substep” completion claim is made.

No live service/configuration/DB mutation, installer/catalog/publication/version change.
Console5ce82415, HTTP4e2df679, NL GeoIP22November, Android126/catalog9 and8/12/120s/
all-three-node ACK remain unchanged. Rollback is removal of owned lab resources and an
ordinary source revert if needed. Never restore old live SQLite, erase retained handoff
floors/history or overwrite a published version. Existing clients still depend on RU.
