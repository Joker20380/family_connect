# 5N-PROD-READINESS-SCHEMA — PASS

Date: 2026-10-02 UTC. Explicit user authorization: **migration only**.
Starting/final local HEAD: `9b3ec45e83ccb226ec4373087329cfdc218b0fac`.
No commit, push, runtime deployment, ingress change, restricted activation, authority
refresh, Android signing/install or Redmi access. Existing dirty/untracked work preserved.

## Scope and final state

RU production DB: `185.251.89.19:/opt/apps/family_connect/friends-access/access.db`.
The running ordinary handler's command line and its `ROOT`/`Access(ROOT/'access.db')`
binding identify this DB; no ambient checkout or guessed database was used.

Exactly one call to `control.friends.readiness_receipts.migrate` committed successfully.
The receipts table is now present and empty. SQLite schema cookie **13 → 14**;
`user_version=0`, `application_id=0`, journal mode `delete`, DB size184320 bytes unchanged.
No migration ledger exists; the cookie is not a numbered application migration.
Final independent readback: **20:50:06.492833 UTC**.

Safe structured evidence: [migration, schema, health and service receipts](2026-10-02-5n-prod-readiness-schema-evidence.json).
Private database contents remain on RU; only safe metadata/counts/booleans are retained locally.

## Baseline and ordinary API regression

External HTTPS uses the existing verified-TLS acceptance helper, one serialized request
stream with1.1s pauses, no real identity/proof or fake owner receipt.

| Check | Before20:42:09–20:42:14 | After20:49:05–20:49:10 |
| --- | --- | --- |
| GET `/status/server-load.json` | 200 | 200 |
| POST `/friends/challenge`, `{}` malformed | 400 | 400 |
| POST `/friends/chat/challenge`, `{}` safe ordinary probe | 400 | 400 |
| POST `/friends/restricted-readiness/challenge`, `{}` | 404 | 404 |

The safe ordinary probe preserves the established attempt15 baseline behavior; it is
not an authenticated owner challenge and does not create a new challenge/registration.
Three additional around-operation samples returned200/400/200. All11 samples meet their
expected status; no transport error,429 or502 was observed.

Before any production write, read-only inspection established table absence, healthy
ordinary services, absent restricted ingress/drop-ins, inactive RU sync/static service
and disabled inactive timer, absent candidate service, and inactive disabled NL bootstrap.
The first local preflight assertion initially rejected systemd's legitimate `static`
sync service; a read-only unit check established the disabled timer and inactive state.
The assertion was corrected before any backup/migration; no service state was changed.

## Protected backup / recovery point

Accepted SQLite online backup API (`source.backup(target)`), not a raw live-file copy.
Source opened `mode=ro`; ordinary services stayed running.

- Path: `/opt/apps/family_connect/readiness-schema-migration-20261002-9b3ec45/access-before-readiness-schema.db`.
- Started20:48:50.222236UTC; finished20:48:50.266342UTC; elapsed44.160ms.
- Size184320 bytes; file0600 in directory0700; file and receipt/directory fsynced.
- SHA256: `e47be43919250196807d12da9040b6014ab282c32be04289162fb6d94c88b76a`.
- `quick_check=ok`; expected old schema/table absence confirmed before migration.
- Live rollback journal mode `delete`; no WAL/SHM/journal sidecars at baseline/final read.
- Backup `user_version=0`, `application_id=0`, destination schema cookie1. The backup's
  destination cookie is not a historical migration sequence or comparable live cookie.
- Durable production `intent.json`, `backup.json`, `committed.json`, `result.json`
  reside alongside the protected backup. No database downloaded into Git/task reports.

## Final source review and execution

Used the already-retained closed sync artifact, **not its CLI/main**:

`/opt/apps/family_connect/restricted-materials-stage-20261001/canary-rollout-attempt15-014e6f9/sync-candidate/restricted-sync.pyz`

Archive SHA256: `0237527cc0fbe6ea5498b0f1d2025894ae3f347c4bb26b4da9f702bfc25f4f1c`.
`control/friends/readiness_receipts.py` SHA256:
`4e45675f2d3a9a08fbaa43e9ff048c509902902a8ab26d5f5ca5f3799fb13237`.
Exact source hash equals the current reviewed file; imported module origin checked
inside this archive. No source pin exception, upload, new artifact or runtime replacement.

The reviewed function contains only one `CREATE TABLE IF NOT EXISTS` statement. No
DROP, rename, ALTER, backfill, existing-row rewrite, pruning, challenge/fetch/ACK invocation,
grant/CRL mutation or other migration. The full restricted migration wrapper was **not** run.

Existing DB opened `mode=rw`, timeout15s, synchronous FULL, explicit `BEGIN IMMEDIATE`.
Schema drift/table presence and original versions were rechecked under the writer lock.
All existing table rows were compared privately in memory before/after the call in that
same transaction; only equality/counts were emitted. Schema and integrity assertions ran
before COMMIT, with rollback on exception. No second production invocation.

| Measurement | Result |
| --- | --- |
| Transaction start | 20:48:50.283870 UTC |
| Transaction end | 20:48:50.319772 UTC |
| Total transaction elapsed | **35.893ms** |
| BEGIN IMMEDIATE acquisition | 0.131ms |
| Exact migration function call | 0.440ms |
| COMMIT call | 32.590ms |
| SQLITE_BUSY / SQLITE_LOCKED / retries | none observed / none / none |
| Transaction result | **COMMITTED** |

SQLite's reserved writer lock lasts through the transaction; the exclusive commit phase
is not separately instrumented. Ordinary writers could wait. There is no claimed zero
downtime: bounded probes had no observed failures, but **no probe overlaps the35.893ms
transaction**, and these samples are not continuous end-user traffic evidence.

## Exact schema / data / application validation

Expected columns, order/types/defaults/nullability and PK flags match the previously
validated synthetic schema exactly; all defaults are NULL:

| Column | Type | NOT NULL | PK |
| --- | --- | --- | --- |
| correlation | TEXT | no | 1 |
| nonce | TEXT | yes | 0 |
| device | TEXT | yes | 0 |
| challenge_at | INTEGER | yes | 0 |
| fetch_id | TEXT | no | 0 |
| fetch_at | INTEGER | no | 0 |
| revision | INTEGER | no | 0 |
| minimum_crl | INTEGER | no | 0 |
| expires | INTEGER | no | 0 |
| ack | TEXT | no | 0 |
| ack_at | INTEGER | no | 0 |

Two unique BINARY autoindexes only:
`sqlite_autoindex_restricted_readiness_results_1` (origin `pk`, correlation),
`sqlite_autoindex_restricted_readiness_results_2` (origin `u`, nonce).
No FK/CHECK/additional index. SQLite's TEXT PK is not inherently NOT NULL here; existing
application correlation validation remains unchanged. All index details are in evidence.

`quick_check=ok`; `foreign_key_check` empty. Only the new table plus its two indexes
were added; every pre-existing schema entry and row was unchanged inside the transaction.
Final counts match baseline, plus the new table count0: devices28, invites82,
restricted_grants1, restricted_certificates2, restricted_challenges1,
restricted_crl_sequence1, challenges1, chat_bindings17, chat_challenges1, chat_sequence1,
referral_claims24, referral_links8. No identifiers or row values persisted in reports.

Read-only production `readiness_receipts.readback` using an intentionally nonexistent
synthetic correlation returns `UNKNOWN`/no receipt from the migrated table. This verifies
the packaged application query can open/use the schema without enabling routes, calling
authority or inserting a fake receipt. It does **not** claim owner provisioning acceptance.

## Ordinary services and restricted shutdown retained

Before/final RU service metadata, start timestamps and restart counters are identical:
ordinary API PID1566654, AWG PID1515959, TCP PID1908885, all active/running, NRestarts0.
Normal handler and nginx config SHA256 values unchanged. No stop/restart/config change.
AWG/TCP process continuity is verified, not a new tunnel/end-user traffic acceptance test.

RU sync remains inactive/dead/static with inactive/disabled timer. HTTP candidate remains
not-found/inactive. NL bootstrap read-only before/after metadata is byte-identical,
inactive/dead/disabled, PID0. Restricted route remains404. No authority/Redmi action.

## Local tests and preservation

- Exact guarded runner rehearsed against synthetic schema: COMMITTED with row preservation;
  injected schema-validator failure: ROLLED_BACK with new table absent and old row intact.
- Exact archive receipt migration repeated only locally: idempotent, no schema/row change.
- Existing Android challenge, restricted authorization, receipt and artifact regressions:
  **125 passed,6 skipped** (optional JVM/Go/native-artifact integrations in this invocation).
- Configured actual JVM serializer/response parser ↔ local Python handler suite:
  **23 passed,0 skipped**, including the prior JVM-skipped roundtrip.
- Existing schema compatibility metadata used to assert all production columns/indexes/FKs.
  Prior old-schema Android503/CORRELATION_SCHEMA_UNAVAILABLE→migration→200 proof remains
  referenced in the [forensics report](2026-10-02-5n-prod-schema-forensics.md).
- No Android/server source or artifact changed; no Gradle/build/sign/install needed.
  Canary55 wire protocol remains compatible;56 is not required for functionality.
- Task documentation secret/source guard and `git diff --check` PASS. Whole-index guard
  retains the unchanged pre-existing `tests/test_readiness_adapter_packaging.py`
  private-key-PEM fixture finding; it was not fixed or bypassed.
- No files staged, no commit, no push. Prior dirty/untracked files preserved; only new
  task report/evidence and additive STATUS/PLAN entries are task-owned documentation changes.

## Rollback and next boundary

On migration transaction failure SQLite rollback is authoritative; local failure rehearsal
verified this behavior. Production succeeded: **leave the additive table in place**.
Do not restore the old full database merely to remove it or roll back grants/CRL/security state.

Current schema prerequisite is satisfied. Historical table state at the exact attempt15
failure remains UNKNOWN; this migration does not prove that historical root cause.
No real-owner restricted request was attempted on production; routes deliberately stay404.
PROV-1 remains stopped/open. Any subsequent runtime/authority/retry/device action needs
its own explicit scope. FIELD-1/DIAG-1/OPS-1/beta not started. STOP.
