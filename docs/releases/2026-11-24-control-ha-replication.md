# 24 November 2026 — replicated storage handoff

Source `9034163db7370803e1d008ed9678e3107d27cec0` pushed and independently remote-SHA
verified on `feature/device-technical-metadata-20261115`. Full implementation/report:
`/home/joker/.codex/worktrees/dad9/family_connect`. Old main is navigation only.
Original four dirty files and six untracked files are preserved. Its previous push
was non-fast-forward against `cb47bf230c6795cf21f4e6948253f49aa5377ed0`; no force/reset.

Owner selects completion of all HA-02. **Isolated replication gate PASS**, overall
HA-02 IN_PROGRESS. Two fresh three-PG/three-etcd runs qualify strict synchronous
Patroni quorum, primary loss/return, minority/majority DCS loss, refusal after lease
expiry and exact recovery. Both-standby loss withholds client ACK. Explicitly canceled
SyncRep waits previously yielded WARNING01000 but a false successful commit; the
canonical PG connection now closes and raises ReplicationAcknowledgementUncertain.
It conservatively treats every warning during Connection.commit as uncertain, using
nonlocalized severity. Reconcile the original operation, do not replay under a new ID.
Native proof reuse/stale import remain refused after replicas return. All44table row
sets match, including91acknowledged rows after later writes, not merely row counts.

PostgreSQL17.11, Patroni4.1.5, psycopg3.3.9, etcd3.7.4. DCS TTL20seconds, strict ANY1
of two synchronous standbys, fsync/full-page writes on, failsafe off. DCS voter roles
must converge before application import. One-host loopback rehearsal is not WAN/failure-
domain/receiver-fencing or production RTO acceptance. No new backend is installed.
905 SQLite/PostgreSQL contracts PASS /0 skips in262.791seconds;28 focused guards PASS
/0 skips; two full native fault receipts PASS. Seven source docs/1010links/0errors
and whitespace PASS; external URLs inventoried, not fetched. Private evidence:
`/tmp/fc-control-ha-20261124/replication/`, not Git. Owned resources cleaned.

Staged navigation check:3files/381links/0errors and whitespace PASS. Original unstaged
changes and six untracked files match the retained baseline exactly.

Three remaining criteria: actual-current authorization and history custody; installed
schemas/all writers/coherent capture; independent complete current-state recovery.
Next is read-only census, then the scoped barrier/abort plan. No real service stop,
SSH, production-data read, server policy change, release or deployment in this checkpoint.
HA-03 fencing/HA-04 failover/HA-05 cutover are not selected; RU dependency persists.

No built/installed/public/invitation version change or fresh health claim. Known console
image `sha256:5ce824159e9f206c27ba92185097857382aa5fec71678ce5e728423509d1446a`, RU HTTP
archive `4e2df679761ba9e7af74128984ef2e19e8e7b228f1cc85b36d50be2b0bc24ce8`,
NL GeoIP22 November, Android126/catalog9,8/12/120s/all-three-node ACK unchanged.

Rollback stops only owned lab resources; source revert is an ordinary new commit.
Do not remove the COMMIT-warning guard while claiming replicated RPO0, restore old
SQLite over newer writes, reset floors or force-push. Uncertain commits require
current-state reconciliation, not an assumption that rollback occurred.
