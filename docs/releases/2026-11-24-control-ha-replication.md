# 24 November 2026 — strict replicated storage rehearsal and truthful commit ACK

## Scope and stage2 result

Owner request: “дальше. работай до завершения 2 этапа”. This selects completion of
all four existing HA-02 gates, not another journal-only variant, HA-03..05 or a silent
production cutover. Authoritative worktree/branch remains
`/home/joker/.codex/worktrees/dad9/family_connect`,
`feature/device-technical-metadata-20261115`, starting at75ad8011.

**Isolated replication gate PASS. HA-02 as a whole remains IN_PROGRESS.** Journal/
actual-current authorization and custody, installed schemas/all writers/coherent
capture, and independent full current-state recovery remain open. No real service
was stopped, no SSH or production data read, and no server/backend policy changed.

## Implementation and failure discovered

[Runner](../../scripts/control_ha_replication_rehearsal.py) owns three disposable
PostgreSQL/Patroni containers and three pinned mTLS etcd children. Fresh private
temporary directory, loopback-only ports, exact Docker ownership labels before each
kill/start/remove, bounded waits and cleanup on success/failure/SIGTERM. Unknown
container ownership refuses mutation. Failed runs and raw logs remain private.

Pinned PostgreSQL17.11, Patroni4.1.5, psycopg3.3.9 and etcd3.7.4. Derived local image:
`sha256:43943c65d0c68dbda76eaac635a7f5b708cc659e0996c61853330fdaeb49d419`.
The pinned PostgreSQL base is
`sha256:18cfe3ef5e6815560c98237d6216d1e5119702fb0f3894c8785dd58b8bbe5d73`.
Container Python is Alpine3.24.1's python3-3.14.10-r2. Full Python dependency lock and
upstream notices retained; installed APK/Python package inventory is private evidence.
The locally built image is not a published reproducible server release.

Effective settings must match: synchronous_mode=quorum, synchronous_mode_strict=true,
synchronous_node_count=1 (primary plus at least one durable standby), fsync/full-page
writes/synchronous_commit=on, failsafe=false, maximum_lag_on_failover=0, timeline check.
Patroni enforces minimum TTL20seconds. Streaming alone was insufficient: application
writes now wait for both DCS quorum voter roles as well as PostgreSQL ANY1 readiness.
Bootstrap's transient upstream `ANY None (*)` warning is not accepted as readiness.
No application authority is imported before that guard passes.

A native failure was reproduced before the fix: while both replicas were stopped,
COMMIT waited in SyncRep. `pg_cancel_backend` produced SQL WARNING01000 and the detail
that the transaction had committed locally but might not have replicated. Unguarded
psycopg returned success and the synthetic client printed COMMIT_ACK. A canceled wait
is therefore **not** a successful durable acknowledgement or proof of rollback.

[DurableConnection](../../control/friends/postgres_durability.py), used by the existing
[PostgresEnrollment](../../control/friends/enrollment_postgres.py), treats **any warning
during Connection.commit** conservatively as `ReplicationAcknowledgementUncertain`,
closes the connection and prevents the application's success return. It uses PostgreSQL's
nonlocalized severity, not localized text. Normal non-warning notices and warnings
outside commit do not poison unrelated commits. Original DB errors stay errors.
All current canonical repository context-manager commits use this path. This is not
a general guard around arbitrary raw SQL COMMIT/autocommit or third-party connections.
Reconcile the original idempotency operation after recovery; do not automatically
mint a new ID/replay a consumed proof. No permissive fallback is introduced.

## Acceptance evidence

- **905 SQLite/PostgreSQL repository contracts,0failed,0skipped** in262.791seconds,
  covering all13 `tests/test_*repository.py` modules on a separate owned PG17.11.
  Includes paid, revoke, enrollment/proofs, membership, referrals, support, restricted,
  CRL, chat, routing, consent/metadata, diagnostics and notices.
- **28 focused connection/runner guards,0failed,0skipped**. New pytest modules make
  their optional psycopg dependency explicit; mandatory qualification used the dedicated
  locked environment, so none of these checks was skipped.
- **Two complete fault runs, both `ISOLATED_PATRONI_RPO0_PASS`** on fresh clusters.
  Both elected node0 initially and node2 after primary loss; all owned resources cleaned.

Each full run imports the existing44-table synthetic native-format fixture and exercises
product contracts; then new payment, revoke and consumed-proof writes are acknowledged.
The current checkpoint contains44tables/91rows after further failover/minority writes.
Assertions compare exact full row sets, not just those counts:

1. Kill primary with an uncommitted device update: successor retains all acknowledged
   state and does not expose the unfinished transaction. Consumed proof/stale import refuse.
2. Return old primary: all three copies match. Fresh product writes work on the successor.
3. Lose one etcd voter: product writes continue. Lose two: no writable primary after
   TTL plus5seconds, and direct write attempts on reachable replicas refuse. Restore
   voters and verify every table on all three nodes again.
4. Lose both PostgreSQL standbys: a real product proof completion remains in SyncRep
   for TTL plus2seconds with no application COMMIT_ACK. Disconnect leaves an ambiguous
   operation, reconciled as committed after replicas rejoin; proof retry refuses.
5. Repeat, explicitly cancel the sync wait: the warning is observed and the guarded
   client reports uncertainty, never COMMIT_ACK. Rejoin/readback preserves exact state
   on all three copies and still refuses the consumed proof.

DCS loss detection is lease-bounded, not instantaneous; existing lease validity is not
proof of permanent majority. Independent WAN failure domains, old process/receiver
fencing, production routing and RTO/SLA are not qualified by one laptop. HA-03 remains
necessary before distributed publication. No actual product data/keys are in the lab.

[Reproduction commands and guard details](../../deploy/control-ha/README.md#strict-postgresqlpatroni-replication-rehearsal).
Private receipts: `/tmp/fc-control-ha-20261124/replication/` (run-6/run-7, guard log,
all-repositories JUnit/log, image/package inventory; failed-run evidence retained).
No raw evidence, data directories, image, test keys or capsules enter Git.

Documentation gate:7changed files/1010links/0errors; external URLs inventoried, not
fetched. `git diff --check` passes. This is not a platform CI/release qualification.

## Rollout, rollback and remaining gates

Source-only checkpoint. No built/installed/public/invitation application version change.
Known console image `sha256:5ce824159e9f206c27ba92185097857382aa5fec71678ce5e728423509d1446a`,
RU HTTP archive `4e2df679761ba9e7af74128984ef2e19e8e7b228f1cc85b36d50be2b0bc24ce8`,
NL GeoIP22 November, Android126/catalog9 and8/12/120s/all-three-node ACK unchanged.
These are retained version observations, not fresh fleet-health checks. RU dependency persists.

Stop only the owned lab to abort; source rollback is an ordinary revert. Never remove
the COMMIT-warning guard while claiming RPO0 on a replicated backend. After an uncertain
commit, reconcile current state; never restore old SQLite, replay a new event ID, reset
floors or force-push. No production rollback is needed because nothing was deployed.
Continue the three remaining HA-02 gates with exact installed evidence, scoped barrier
and abort/recovery paths. No automatic HA-03/04/05 selection or guessed completion date.
