# 23 November 2026 — CONTROL-HA implementation checkpoint

Owner requests implementation and documentation of distributed management.
Source: existing metadata branch33b9cbdc; dirty divergent main preserved.
[Architecture, ordered gates and rollback](../control-ha.md).

Latest known installation remains console5ce82415 and two NL GeoIP collectors
on22 November; public Android126/catalog9 unchanged. This is not control HA or
RU recovery. The22 November RU outage recorded in the main checkout remains open;
source inspection is not a fresh server-health check.

## Progress

- HA-01 isolated scope implemented and verified; details below.
- HA-02A enrollment, HA-02B paid/subscription and HA-02C membership slices qualified below; remaining
  HA-02 and HA-03..05 pending:
  no full canonical PostgreSQL migration, fenced authority,
  alternate API, client fallback or live cutover installed.
- No server service/policy, product database, consent or client artifact changed.
- Design checkpoint `e5eaef838863e2ce43110dd1821eef9df9b67df3` is committed/pushed;
  remote branch SHA independently matched. Implementation checkpoint
  `bbc0a9fb925165716052e3e574f8fa9da7c77a57` is also ordinarily pushed and verified
  against the remote feature-branch SHA; the worktree is clean after that commit.
- Old-main handoff `cf645e71` is retained locally. Its ordinary push was rejected
  `non-fast-forward`; no force, rebase, merge or change to pre-existing work.
  The feature branch, not that unpushed handoff, is the available source checkpoint.

## HA-02C — first-payment node preparation and failure consistency

Continuation from `eeb11ba7fb8e95c2d0cad300b71359417f97f77b` on the same metadata
branch. The selected scope is synthetic transport-membership transaction parity,
not live migration, service recovery, client release or provider move. Latest
known installed console5ce82415 and Android126/catalog9 remain unchanged; no fresh
RU/NL health assertion. Production still uses the accepted SQLite/runtime bytes.

### Implementation and safety boundary

- `transport_membership.prepare_nodes` shares the first-payment protocol between
  SQLite's existing private command-map wrapper and explicit lab PostgreSQL exchange.
  All command entries validate before contact. The complete three-node set, payload
  token, single-device binding, pre-commit preparation and12s subprocess bound remain.
- ACK validation now rejects duplicate JSON keys, non-UTF8/non-bytes, oversized
  replies, bool/float schema and unexpected/mismatched fields. It does not retry a
  failed node or assume commit from a missing response. Existing node8s operation,
  watchdog12s and paid lease120s are unchanged; noncohort retains its separate policy.
- Native disposable schema version2 has purpose `membership-required`. First payment
  refuses a missing exchange; version1/no-transports refuses a configured exchange
  instead of claiming that preparation ran. There is no production DSN, environment/
  HTTP/CLI switch, automatic migration or alternate writer. Constructor injection
  carries the same exchange through the existing enrollment/paid transaction.
- Rollback never removes already-durable target fences. On partial prepare/ACK loss
  or transaction failure, canonical ledger/subscription remain unchanged; prepared
  target nodes deny across restart, timeout and newer noncohort snapshots. Other
  noncohort/foreign entries remain. Exact retry completes preparation and one commit;
  a committed replay skips all node calls. Terminal revoke is not undone.
- All three nodes, including RU, are still required for first cohort admission.
  Excluding an unavailable node needs a separately qualified serving-set quarantine/
  fencing protocol, not a smaller quorum silently introduced here. No HA-03 epoch
  receiver fencing, compensation/unprepare or production reverse import is supplied.

### Verification

- Final real PostgreSQL17.11/psycopg3.3.9 runner: **131 contracts PASS /0 skipped**
  in56.32s (40 enrollment +49 paid/subscription +42 membership). Membership uses real
  `Gateway` state files, locks, atomic writes/fsync and algorithms with simulated
  kernel/service/network executors; it is not three live servers or WAN acceptance.
- Lost ACK after durable prepare on each node, malformed ACKs, readback failure,
  last-step DB rollback, concurrent duplicate payment, pre-commit invisibility,
  stale snapshots, expired leases and terminal revoke/restart pass. A real owned
  PostgreSQL backend is terminated after every node ACK and uncommitted ledger/
  subscription writes: no payment survives, node denies do, exact retry succeeds.
- The unchanged PostgreSQL5s idle-in-transaction timeout terminates a delayed
  preparation after the first node; no subsequent node contact or payment occurs.
  Target deny survives and exact retry works. This explicitly exposes a lab versus
  WAN deadline limitation; the5s timeout is **not** increased to hide it.
- Inherited SIGKILL/restart, stale-backup refusal and exact current nine-table/
  twelve-row restore pass; restored proof/ledger/revoke/triggers/audit sequence hold.
  Additionally, a real pg_dump/pg_restore of a fresh membership-required schema
  refuses first payment without its exchange and preserves every row. This only
  qualifies the marker/no-fallback guard, not production node+DB backup consistency.
- Receipt `/tmp/fc-control-ha-20261123/membership-3/receipt.json` records
  `ISOLATED_PAID_POSTGRES_PASS`, `SYNTHETIC_CONTRACTS_ONLY`,
  `REFUSES_MISSING_EXCHANGE`, zero production writes and owned-container cleanup.
  Logs, source capsule, credentials, dumps and raw synthetic state stay outside Git.
- Broader changed-risk suite: **389 PASS /16 skipped /4 FAIL** in48.07s, including
  payment CLI/HTTP/readiness/release policy, registry backup, policy packaging,
  transport enforcement/membership/budgets/lifecycle/application/HTTP, subscription,
  packaged HTTP, HA shadow and runner safety. The16 skips are15 configured real-nginx
  gates and1 pinned sync-archive interoperability gate. This is not a green full suite.

### Historical package blocker and retained attempts

All four failures are `tests/test_transport_package.py`: closed overlay/tamper,
exact RU diagnostic overlay, PR15 lifecycle and v2 node-forward package. They fail
with `UNRELATED_PAID_DELTA` or `POLICY_CHANGE_FORBIDDEN`: strict historical packagers
do not accept HA-02B's current paid/policy source as an old exact overlay. No guard,
historical hash, installer, archive or public release was changed to hide the failure.

Verified baseline reproduction from a separate source capsule at exact
`eeb11ba7fb8e95c2d0cad300b71359417f97f77b` produces the **same4 failures /2 passes**.
The working directory/import roots and paid/policy/membership bytes were checked
against that commit; the initial invocation from the current worktree is not used
as baseline proof. Evidence: `membership-baseline-packages-verified.log`. This is
not a new HA-02C regression, but it remains a deployment/package gate; a separately
reviewed closed HA runtime is required rather than weakening old overlay pins.

First SQLite-focused run:55 PASS /22 PostgreSQL skips (not PostgreSQL acceptance).
First real runner:130 PASS and recovery PASS. The extended run:130 PASS /1 failure
because the timeout fixture expected generic `OperationalError`, while psycopg
correctly raises `IdleInTransactionSessionTimeout` (different exception family).
The test now expects that exact server error, retaining the5s timeout and all deny/
rollback assertions; final131 cases and restores pass. Failed attempts remain in
`membership-{1,2,3}/`, `membership-sqlite-1.log`, `membership-regressions.log` and
the baseline logs under `/tmp/fc-control-ha-20261123/`.

### Next and rollback

Next HA-02 slice: remaining canonical support/admin/referral writers, followed by
metadata/tombstones/files, full import/backup and PostgreSQL/Patroni replication.
Production membership scheduling/wiring and new runtime package qualification stay
open. HA-03 receiver fencing, HA-04 API/client failover and HA-05 guarded cutover
remain mandatory. No copied SQLite becomes a second writer.

Current rollback stops only disposable tests; production needs no restore. After
future acknowledged writes, fence writers and preserve the current state before
forward recovery or qualified reverse import. Do not restore old SQL/node caches,
clear `prepared` or automatically extend a payment to make recovery appear green.

## HA-02B — paid ledger, subscription and recovery checkpoint

Owner continuation explicitly prioritizes rollback on failure. This is a source
checkpoint on the existing metadata branch, **not** production deployment or
completion of HA-02. No release/version/catalog change. Rollout remains blocked
on remaining writers, full import/recovery, strict replication and HA-03..05 gates.

Source/tests/docs `a62b5b2e3ef58598a062e19289c2c06642c3af78` ordinarily pushed to
`feature/device-technical-metadata-20261115`; independent remote SHA matched.
Final staged scope/private-key marker scan, local documentation targets and
whitespace checks PASS; locked environment `pip check` PASS. Final runner-only
rerun13 PASS. No marked rehearsal containers remain after the final readback.
Root navigation checkpoint `e95ddcdb5a2da556557403b781076218d97af0d1` remains local:
ordinary main push rejected `non-fast-forward`; remote main is still
`cb47bf230c6795cf21f4e6948253f49aa5377ed0`. No force/rebase/merge. Root's existing
40/66/11/6-line documentation edits and untracked work are preserved exactly;
the verified metadata branch is the published source, not that old main.

- `paid_beta.py` adds semantic paid operations without duplicating admission,
  payment/release validation or event state transitions. SQLite stays the default;
  its first-payment transport preparation remains mandatory when configured.
  Native `paid_postgres.py` is an explicit synthetic-only/no-transports schema,
  with immutable ledger, cohort10, binding and terminal-revoke triggers.
- Personal subscription proof consumption and paid projection now share the
  enrollment transaction. A projection savepoint preserves consumed-proof behavior
  on missing/corrupt schema or SQL failure without committing a PostgreSQL aborted
  transaction. No noncohort/allow response replaces a failed read. A failed/unknown
  outer commit is not asserted successful; no alternate SQLite write is attempted.
- All three transport projections share semantic reads; wire shape, entitlement
  boundaries, paid/noncohort separation and8/12/120s remain unchanged. No transport
  receiver, legacy archive pin or production/client dependency lock is changed.
- **89 contracts PASS /0 skipped** on real PostgreSQL17.11/psycopg3.3.9 and SQLite:
  40 enrollment +49 paid/subscription/parity cases. Concurrent duplicate/event-ID
  conflict/last-cohort-slot/proof races, rollback after ledger append, exact ledger
  and all-node decision parity, latest Android observation/mesh revoke, identity
  revoke, natural grace expiry, coherent concurrent reads, marker guards, native
  update/delete/truncate refusal and direct-writer trigger concurrency pass.
- **366 regression/runner checks PASS /20 optional skips** in47.97s, covering
  Access/support, paid policy/membership/enforcement, HA shadow/backup, packaged
  HTTP, restricted/chat/referral/subscription, technical metadata/GeoIP and runners.
  The skipped15 real-nginx,1 pinned sync archive and4 locked-Go compatibility gates
  are unchanged and not represented as release acceptance. Runner checks include
  six inherited isolation/ownership/driver tests and seven restore-comparison tests.
- Final rehearsal: `python -m scripts.paid_postgres_rehearsal --workdir
  /tmp/fc-control-ha-20261123/paid-3` using the existing dedicated locked venv and
  pinned official image from HA-02A. Source, stale-restore and current-restore
  containers use disposable private state and ownership-checked cleanup; no SSH,
  live export, server restart or product write.
- Real SIGKILL/restart retains committed payment/grace/revoke and consumed proof,
  drops an uncommitted ledger/invitation write and returns the original payment
  for same-ID/payload retry. An older backup taken **before those payments** is
  restored only into another disposable container and explicitly REFUSED against
  current state; accepting it would lose acknowledged events/revocation.
- Latest dump restores every row in all nine lab tables:2 challenges,1 device,
  1 invite,1 Support ID,1 audit row,3 events,1 subscription,2 schema-marker rows
  (12 total). Payment replay adds nothing, proof replay is refused, revoked state
  persists, restored immutability triggers reject updates and audit sequence
  advances. This is not the full product schema, metadata/file/CRL restore,
  reverse migration, host-loss durability or replicated RPO0.
- Before cutover, rollback means stopping only the lab/shadow; unchanged production
  needs no restore. After new-store writes, fence writers, preserve acknowledged
  current state and use verified forward recovery or a separately qualified reverse
  import. Old SQLite restoration is not a safe shortcut. No production reverse
  importer exists yet; do not switch writers assuming this lab provides one.

Failed attempts retained outside Git: the first SQLite regression caught malformed
empty event schema returning200 instead of503 after a generic `SELECT *`; explicit
column reads restore fail-closed behavior (162 passed /1 failed before correction).
The first real run passed78 cases and failed one fixture expecting a binding error
on an already terminal-revoked row, where SQLite correctly rejected revocation
first. The binding fixture now uses an active row; the terminal test remains
separate. The corrected run passed89; the final run additionally verified restored
triggers and audit sequence. No production failure/restore occurred.

Private evidence: `/tmp/fc-control-ha-20261123/paid-{1,2,3}/`,
`paid-sqlite-first.log`, `paid-regressions.log` and each run's log. Dumps, credentials,
JUnit, SQL rows and raw test evidence remain local; only safe sources/tests/docs
are published. Read [remaining writer gates and recovery rules](../control-ha-storage.md).

## HA-02A — enrollment repository checkpoint, not complete HA-02

- Source/tests/docs checkpoint `9d1219d89b462e3ba87daa6e1e560dc1f238ce8b`
  ordinarily pushed to `feature/device-technical-metadata-20261115`; exact remote
  branch SHA independently matched. Staged scope/private-key markers, local
  documentation links and whitespace checks pass; no build output/private state.
- Old-main navigation checkpoint `a22efc6e3f1be5a813ac6469b9f80ce6c5543463`
  remains local. First push failed transient DNS; one ordinary retry was rejected
  `non-fast-forward`. Remote main remains `cb47bf230c6795cf21f4e6948253f49aa5377ed0`.
  No force/rebase/merge; the pre-existing40/66/11/6-line documentation changes and
  untracked root work remain untouched. Use the published feature-branch source.
- Shared `Access` domain logic now uses semantic transaction operations for invite,
  challenge, activation, status and device revocation. SQLite remains the default;
  existing API signatures, proof/binding validation,TTL100s and challenge limit8
  remain. The boundary stays in `access.py` to preserve closed artifact inventories;
  historical archive pins/overlays are not rewritten.
- `enrollment_postgres.py` is explicit synthetic-only injection, loopback/fixed
  disposable DB+role, versioned schema marker, native SQL and transactional locking.
  Legacy `db()` paths refuse instead of becoming mixed PostgreSQL/SQLite writers.
  No production DSN/HTTP switch or server configuration is added.
- Real PostgreSQL17.11 official image
  `postgres@sha256:18cfe3ef5e6815560c98237d6216d1e5119702fb0f3894c8785dd58b8bbe5d73`;
  psycopg/psycopg-binary3.3.9 pinned in an optional HA lockfile. Existing production
  and client dependency locks remain unchanged. Dependency notices updated.
- **40 SQLite/PostgreSQL contracts PASS /0 skipped** in the real runner. Includes
  eight competing independent connections spending one proof, two identities
  spending one invitation,16 simultaneous challenge requests respecting limit8,
  status replay, revoked/expired/wrong-device rejection, rollback after the last
  activation step, Support ID collision, lost-response status recovery, bounded
  lock refusal, schema mismatch and no silent SQLite fallback.
- Actual source-container SIGKILL/restart preserves committed identity/TCP ID,
  revocation and unused invitation, refuses consumed proof, drops an uncommitted
  insert and accepts a fresh reconnect with the same identity. fsync,
  full_page_writes and synchronous_commit are checked on; this is single-instance
  crash evidence, **not** host-loss RPO0, replication or hardware power-loss proof.
- Binary pg_dump restores into a second fresh owned container in one transaction.
  All five enrollment tables are nonempty and compare exactly:3 invites,2 devices,
  3 challenges,2 Support IDs,1 audit row. Restored identity sequence advances.
  This does not qualify paid/metadata/CRL backup or a production SQLite import.
- **353 consumer tests PASS /20 skipped**: Access/support, paid ledger/policy,
  old HA shadow/backup, packaged HTTP, restricted/chat/referral/subscription,
  technical metadata and GeoIP. Skips:15 explicitly configured real-nginx gates,
  1 pinned sync-archive interoperability gate,4 locked-Go compatibility cases.
  No claim of a complete release gate. A separate HTTP/runner rerun passes25
  tests /16 optional skips;5 of these are new runner safety tests. Final runner-only
  suite passes6 tests, adding refusal of a mismatched driver before container start.
- Initial unit run:165 PASS,19 PostgreSQL skips,1 fixture failure because the
  identity is already base64 text; corrected the fixture. First real PostgreSQL
  run:42 PASS,1 test used the deliberately refused legacy `db()` interface;
  replaced that assertion with the semantic transaction check, not a fallback.
  First broader collection lacked LXMF; installed the existing provisioning and
  messenger lockfiles in the same isolated `/tmp` venv. `pip check` passes.
- Private evidence under `/tmp/fc-control-ha-20261123/enrollment-1..5` retained;
  final `enrollment-5` passes contracts/crash/restore and removes both owned
  containers/anonymous volumes. Dumps, credentials, synthetic keys and raw logs
  are not committed. The runner is pinned to the local Docker socket and checks
  ownership before destructive cleanup; no existing panel container is touched.
- SIGTERM during a real pytest child: parent exits143, test child is gone and
  the owned container is absent. An earlier cleanup assertion expected capitalized
  Docker wording; independent readback confirmed removal, then the corrected
  case-insensitive exact-error check passed. No runtime cleanup change was needed.

[Exact writer inventory/remaining work](../control-ha-storage.md) ·
[Reproducible runner](../../deploy/control-ha/README.md#ha-02a-isolated-postgresql-enrollment).

## HA-01 implementation and validation

- `control/friends/control_shadow.py`: one read-only SQLite snapshot, schema/all
  table HMACs and existing paid-policy projections for RU/NL1/NL2. Dedicated
  synthetic HMAC key; no raw rows or identities in the manifest, no write/migration.
- `control/friends/control_quorum.py`: loopback-only verified mTLS, linearizable
  reads, revision CAS, replay/conflict/expiry rejection and lost-ACK readback.
  It is not a product leader lease or a replication adapter for application data.
- `scripts/control_ha_rehearsal.py`: three real etcd children, disposable CA,
  synthetic SQLite and owned-process cleanup. No production config or credential.
- etcd3.7.4 official archive SHA256
  `a0d47d07d081c12611fe69dc81a16ae8dd758401c0fe3a83d508823a1dac558e`;
  binary SHA256 `6fcf4a133e477a2340c59a287461b4988f0ed5c7559ff4750a8695ac41ae5a2a`.
  Source/version pins are committed, downloaded binaries are not.
- **61 focused tests PASS**: shadow, paid-registry backup, transport enforcement,
  membership. Dependencies installed from control/identity lockfiles in an isolated
  venv; `pip check` PASS. No full historical/platform release suite claimed.
- First unit pass exposed an incorrect synthetic key length; fixed without
  relaxing32-byte validation. First live rehearsal failed strict X.509 verification
  (missing Authority Key Identifier). Added AKI/SKI and KeyUsage to disposable
  certificates; did not disable verification, mTLS or downgrade TLS.
- Two subsequent real rehearsals PASS. Final run adds direct per-member readback
  after recovery, disallowing fallback to a healthy neighbour as acceptance proof.
  Leader SIGKILL → next confirmed shadow publication **1.766s** on this laptop;
  earlier less-strict rehearsal1.611s. Neither is a production availability promise.
- Minority linearizable read refuses; publication refuses before attempting a
  write. Confirmed manifest survives two crashed members and their return. Stale
  CAS is refused, unauthenticated TLS clients rejected. Only own children stopped.
- Separate real SIGTERM check stops the runner during startup: exit143, all three
  owned child PIDs gone; final61-test rerun PASS. This does not promise SIGKILL cleanup.
- Private local evidence: `/tmp/fc-control-ha-20261123/rehearsal-1`,
  `tls-diagnostic`, `rehearsal-2`, `rehearsal-3`. These contain only synthetic state
  and ephemeral test credentials; retain locally, never commit raw directories.

[Reproducible commands and limits](../../deploy/control-ha/README.md).

## Remaining work — not a production HA acceptance

HA-02 must finish **all** canonical writers beyond the enrollment slice, including
subscription's own challenge transaction, immutable paid events, separate metadata
tombstones and filesystem coordination. Full import, PostgreSQL replication and
Patroni/RPO0 gates are not implemented by this checkpoint.
Then HA-03 receiver-enforced fencing, HA-04 multi-endpoint clients and HA-05 live
shadow/cutover and real failure acceptance. No alternate API is serving users;
RU remains a shared dependency. No provider replacement or live outage test done.

## Rollback

Only source and disposable local rehearsal state exist at this checkpoint.
Stop rehearsal children; keep private logs outside Git. Do not restore a product
DB or replace deployed archives to undo this work.
