# 5N-PROD-SCHEMA-FORENSICS — 2026-10-02

**5N-PROD-SCHEMA-FORENSICS = HISTORICAL CAUSE UNRESOLVED**

Classification **C: historical state at the exact failure time is unresolved**.
Current production is conclusively missing the required receipts table. The retained
pre-attempt15 backup is also missing it. These observations and the deployment omission
strongly support the missing-schema explanation, but are not an uninterrupted database
write history or a snapshot at the actual challenge time. Do not promote this to proof.

Starting/final HEAD remains `9b3ec45e83ccb226ec4373087329cfdc218b0fac`.
Read-only production access was confined to authorized RU `185.251.89.19`:
schema metadata, existing attempt15 backup metadata/schema, retained source/archive
hashes, and selected deployment-receipt timestamps. No production DDL/DML, migration,
runtime deployment, authority refresh, restricted-service start, ingress change,
Redmi access, signing, installation, Git commit or push. No NL/excluded host access.
Ordinary service traffic was not stopped. Existing user edits/untracked work remain.

## Current production schema and historical snapshot

Current DB: `/opt/apps/family_connect/friends-access/access.db`.
Observed **2026-10-02 20:13:28.316364 UTC** using a read-only SQLite connection,
connection-local `query_only=ON`, `trusted_schema=OFF`, and an authorizer permitting
only schema SELECTs, schema PRAGMAs and read transactions. No application rows read.
Both files used rollback-journal header mode1/1; no WAL/SHM/journal sidecars were
present. The inspection refused WAL/sidecar cases rather than ignoring their contents.
Recorded size/mtime/ctime/mode were unchanged across each inspection.

| Observation | Live DB | Existing pre-attempt15 backup |
| --- | --- | --- |
| SQLite `user_version` | 0 | 0 |
| SQLite `application_id` | 0 | 0 |
| SQLite `schema_version` | 13 | 1 |
| Table count | 12 | 12 |
| Migration/version ledger table | absent | absent |
| `restricted_readiness_results` | **absent** | **absent** |
| Size | 184320 bytes | 184320 bytes |

`schema_version` is SQLite's schema cookie, **not an application migration version**.
There is no numbered Friends migration history or timestamp ledger to query. The
backup cookie must not be compared as a migration sequence: it is a separate SQLite
backup destination. `user_version=0` is not evidence of a numbered migration being
applied or omitted.

The twelve tables are `challenges`, `chat_bindings`, `chat_challenges`, `chat_sequence`,
`devices`, `invites`, `referral_claims`, `referral_links`, `restricted_certificates`,
`restricted_challenges`, `restricted_crl_sequence`, `restricted_grants`.
All seven tables relevant to restricted issuance, correlation dependencies and CRL
floor exist. Their SQL, columns, indexes and foreign-key definitions are identical
between current DB and retained backup; canonical inspected-schema SHA256:
`b1d833fa573957f4379052c0b4e92289225167466609a9cd26f59b424cc8e2e3`.
This digest covers the inspected table definitions/presence, **not database rows**.

Existing backup:
`/opt/apps/family_connect/restricted-materials-stage-20261001/canary-rollout-attempt15-014e6f9/access-before-rollout.db`.
Its mtime is **18:40:27.593256 UTC**. Retained local prepare receipt records successful
backup preparation at18:40:29 UTC. The inherited PREPARE implementation uses SQLite's
online `source.backup(target)` and does not copy a live DB blindly. No backup was made
or exported by this forensic task; only its schema and filesystem metadata were read.

## Historical attribution limits

- New migration source was committed at **17:34:38 UTC** in `e81738083457912da5b1032c45cfbe92bad112cc`.
- Existing pre-attempt backup has no receipts table at its recorded18:40:27 snapshot.
- Authority refresh receipt is18:40:35 UTC; it contains no migration record.
- Real Android challenge failure: **18:45:03.869 UTC** (attempt15 report).
- Failure intent18:47:51 UTC; candidate rollback/drain18:47:56; restricted rollback
  receipt18:48:19. Selected retained receipts contain no top-level schema/migration field.
- Current schema still lacks the table at20:13:28 UTC. This alone cannot prove
  what existed at18:45:03.869, and a pre-attempt snapshot does not cover the interval.
- No failure-time snapshot or complete DDL/write audit was found in the inspected
  evidence. No migration application timestamps exist in the database.
- A bounded candidate-unit journal query for18:40:20–18:48:40 timed out after20s.
  It was stopped and **not retried with a larger scan**. No journal contents were
  used or treated as evidence of absence; subsequent SSH read omitted journal access.

The evidence proves absence **before** the attempt and **now**, not exact-time
absence or presence. Unknown intervening actions cannot be excluded by schema cookies,
mtime, an absent ledger, or an activation script's omission. Historical classification
is C, not A or B. Production503 is neither conclusively confirmed nor disproven.

## Exact required migration and activation gap

There is **no numbered migration ID**. Exact source identity:

- `control.friends.readiness_receipts.migrate(database)`, introduced in
  `e81738083457912da5b1032c45cfbe92bad112cc`.
- Called by `control.friends.restricted.migrate(access)`.
- Explicit operator entrypoint:
  `control.friends.restricted_admin --db <existing Friends DB> migrate`.
- `readiness_receipts.py` SHA256:
  `4e45675f2d3a9a08fbaa43e9ff048c509902902a8ab26d5f5ca5f3799fb13237`.
- The retained, accepted attempt15 sync archive SHA256
  `0237527cc0fbe6ea5498b0f1d2025894ae3f347c4bb26b4da9f702bfc25f4f1c`
  includes that migration. Retained HTTP SHA256
  `7ef821a824914b35490d3d371ae4b1722a8900d99cf7b16dbacdd3c5c0af105a`
  includes the call path that requires its table. Remote hashes match accepted pins.

General deployment instructions at accepted HEAD already contain an explicit migrate
command. Therefore **the migration was not entirely omitted from documentation**.
However, that runbook's table list still names only grants/challenges/certificates;
the separate receipt document describes the new additive table and leaves production
migration for later authorization. No new versioned upgrade checkpoint was added.

The actual retained attempt15 runner reuses attempt12→attempt8 orchestration:
PREPARE from attempt4 creates the online backup; RU_INSTALL from attempt3 stages
the sync runtime and runs `sync --check`; later sync refresh and the HTTP candidate
transaction execute. Inspection of these source fragments finds **no call to the
restricted migration**. `sync --check` validates authority, CRL floor and quick_check,
not the receipt-table schema. HTTP startup/request handlers also do not migrate.
Controlled F/G instead always initializes/migrates its own new fixture database.

Thus the concrete integration gap is **a required additive schema upgrade absent
from the reused attempt15 activation sequence and not asserted by its preflight**.
The new runtime assumes schema provisioning has already occurred. This is not a
circular ACK dependency or a discovered ordering defect inside the migration.
It does not prove that nobody ever executed some migration outside that sequence.

The three checked legacy checkout paths under `friends-access/app/control/friends/`
(`restricted.py`, `readiness_receipts.py`, `restricted_admin.py`) are currently absent.
The migration is available in the pinned closed archive, not verified through an
ambient checkout import. Any future authorized runner must explicitly load that exact
archive and verify the imported module origins; do not execute an unpinned ambient module.

## Production-schema-equivalent synthetic proof

Only safe schema metadata was used. A disposable local DB reconstructs the **seven
restricted-endpoint prerequisite tables**, with exact SQL/columns/indexes/FKs compared
against the observation. Unrelated chat/referral tables and all production rows are
excluded. All registrations, keys, authority, grants and CRLs are synthetic.

The existing Android-produced golden bytes and headers pass through the actual
packaged Friends HTTP parser/handler. There is no Python re-creation of Android JSON.

| Local step | Result |
| --- | --- |
| Observed old prerequisite schema, no receipts table | HTTP503 |
| Instrumented local handler classification | correlation_store / CORRELATION_SCHEMA_UNAVAILABLE |
| Run exact explicit migration from accepted sync archive against this temporary DB | succeeds |
| Run the same migration again | idempotent |
| Compare pre-existing schemas and synthetic rows | unchanged |
| Repeat identical Android challenge bytes/ID | HTTP200 |
| Signed fetch / repeated fetch proof | 200 / 403 |

The same before/after test also passes using the exact accepted attempt15 HTTP archive:
503→200. That older artifact does not emit the new diagnostic classification; the
classification comes from the separately instrumented local artifact under identical
schema conditions, never from a production error log. Migration function ASTs in the
pinned archive equal the current repository implementations.

Focused Android/Python authorization, malformed input, revocation, stale/replay and
receipt tests: **99 passed,4 skipped** (optional native-toolchain cases). No security
tests changed or weakened. Synthetic local CLI timings are not production downtime
estimates. No Android build, signing or installation was performed.

## Migration safety review — not executed on production

The wrapper opens the existing DB and calls the receipt migration plus three existing
`CREATE TABLE IF NOT EXISTS` statements. It verifies core `devices`, `invites`,
`challenges` exist. On the observed schema the only addition is:

```sql
CREATE TABLE IF NOT EXISTS restricted_readiness_results (
    correlation TEXT PRIMARY KEY,
    nonce TEXT UNIQUE NOT NULL,
    device TEXT NOT NULL,
    challenge_at INTEGER NOT NULL,
    fetch_id TEXT,
    fetch_at INTEGER,
    revision INTEGER,
    minimum_crl INTEGER,
    expires INTEGER,
    ack TEXT,
    ack_at INTEGER
)
```

- Additive: yes. No DROP, rename, ALTER, data-copy loop, grant reset or existing-row
  rewrite. The migration does not invoke challenge retention pruning or CRL publication.
- Two implicit unique BINARY indexes: primary key on `correlation`, unique on `nonce`.
  No explicit device/time index, CHECK constraint or FK in the new table.
  SQLite's ordinary TEXT PRIMARY KEY does not itself imply NOT NULL here; the existing
  application validator enforces the non-null32-hex correlation contract.
- `IF NOT EXISTS` is idempotent but **does not repair an incompatible existing table**.
  Exact post-schema verification remains mandatory.
- Ordinary Friends API remains schema-compatible and ignores the added table. Restricted
  routes can stay disabled. No runtime restart, ingress switch, authority refresh or
  Android update is necessary to perform this isolated schema addition.
- Locking: `Access.db()` uses SQLite timeout15s, synchronous FULL and `BEGIN IMMEDIATE`.
  In observed rollback-journal mode, it reserves the writer lock, excludes other writers,
  and needs a short exclusive commit phase. Readers can delay commit. The empty table
  and two indexes require no production-row backfill, but disk/fsync latency and
  concurrent requests determine duration. **Zero downtime is not guaranteed**; ordinary
  writers may wait or time out. No lock-duration benchmark was run on production.
- Failure before commit rolls back the transaction. There is no down migration. After
  successful commit, rollback to the older runtime should **leave the additive table**.
  Never restore the old complete DB or lower CRL/grant/security floors. Existing runbook
  rollback protects monotonic state; no schema deletion is authorized here.

## Decision and bounded next authorization

Current missing schema is a confirmed prerequisite gap for any future correlated
challenge/ACK retry, regardless of unresolved historical attribution. A migration-only
change may be proposed separately to fix this **current** gap, not labelled a proven
historical root-cause repair. No command below has been executed on production.

If separately authorized: recheck current schema and ordinary health; retain a protected
server-side online backup and baseline; verify the exact already-retained archive pin,
migration source and imported module origins; invoke only `restricted_admin ... migrate`
against the existing DB in a bounded change window; verify the new columns/indexes,
unchanged existing ledger/security state and ordinary health; preserve a safe dated
migration receipt with source hash and before/after schema metadata. On lock timeout,
stop without automatic retry. On rollback, retain the additive table and monotonic DB.
No artifact deployment, sync/publish-crl, authority refresh, service start, ingress
change, canary action or PROV-1 retry is part of such migration-only authorization.

Canary55's wire protocol remains compatible with the migrated server. Canary56 is
**not required for functionality**; its challenge reason codes improve diagnostics
and its parser hardening does not introduce a required new wire format.
Installed55/public51 remain last documented, not rechecked. All artifact pins unchanged.

Safe evidence is retained in `state-client-build/prod-schema-forensics/`:
`schema.json`, `history.json`, `synthetic.json`, `synthetic-accepted.json`, `tests.log`,
and the read-only inspection/local-proof scripts. No private DB, device identifier,
raw proof, key, credential, receipt body or journal MESSAGE was exported.
[Safe evidence summary and hashes](2026-10-02-5n-prod-schema-forensics-evidence.json).

**STOP. No production migration or automatic retry.**
