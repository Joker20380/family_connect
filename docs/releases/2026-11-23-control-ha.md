# 23 November 2026 — distributed control implementation handoff

## Source, authorization and scope

The owner requested implementation of distributed management and documentation.
Work continues in the existing current worktree:
`/home/joker/.codex/worktrees/dad9/family_connect`, branch
`feature/device-technical-metadata-20261115`. This main checkout is older and
divergent; pre-existing modifications are preserved. Do not deploy its runtime.

- Design/gates commit: `e5eaef838863e2ce43110dd1821eef9df9b67df3`.
- HA-01 implementation: `bbc0a9fb925165716052e3e574f8fa9da7c77a57`.
- Both ordinarily pushed; remote branch SHA matched after each push.
- HA-02A implementation: `9d1219d89b462e3ba87daa6e1e560dc1f238ce8b`, ordinary
  push to the same metadata branch; no source merge/deployment to this old main.
- HA-02B implementation: `a62b5b2e3ef58598a062e19289c2c06642c3af78`, ordinary
  push to that branch succeeded; remote SHA independently matched.
- HA-02C implementation: `0ed728f06acdb131ba17869e6d57a1122451e58e`, ordinary
  push to the same branch succeeded and remote SHA independently matched.
- HA-02D implementation: `22caaf6c4d9fa0167f8e8b93d1cad64971c9a019`, ordinary
  push to the same branch succeeded and remote SHA independently matched.
- HA-02E implementation: `ed6a664ffe6f377caf37af173b68a0cecca3e418`, ordinary
  push to the same branch succeeded and remote SHA independently matched.
- HA-02F implementation: `20129a67e2b6febd9eadd98e2c3425a070ab82a4`, ordinary
  push to the same branch succeeded and remote SHA independently matched.
- HA-02G implementation: `e8240e81ea63d280324acb20193da6d22d0e137b`, ordinary
  push to the same branch succeeded and remote SHA independently matched.
- HA-02H implementation: `9a1f7f44dc8089fa6b41a8fa6e7bb754617dfac4`, ordinary
  push to the same branch succeeded and remote SHA independently matched.
- HA-02I implementation: `b5cb676bd905580e2519a55bdea1d70a7b3d7153`, ordinary
  push to the same branch succeeded and remote SHA independently matched.
- HA-02J implementation: `019aa578788d58a044798a0604fcab5be61c7ec8`, ordinary
  push to the same branch succeeded and remote SHA independently matched.
- HA-02K implementation: `a72941d0840a28e0fa5292fdbf97ab9eb5f6b6d1`, ordinary
  push to the same branch succeeded and remote SHA independently matched.
- HA-02L implementation: `6cd46c938405d2a6294f6339ee1fdb58dcfe39f9`, ordinary
  push to the same branch succeeded and remote SHA independently matched.
- Full architecture: [CONTROL-HA plan](https://github.com/Joker20380/family_connect/blob/feature/device-technical-metadata-20261115/docs/control-ha.md).
- Full evidence: [source-worktree release record](https://github.com/Joker20380/family_connect/blob/feature/device-technical-metadata-20261115/docs/releases/2026-11-23-control-ha.md).
- Commands/limits: [isolated rehearsal runbook](https://github.com/Joker20380/family_connect/blob/feature/device-technical-metadata-20261115/deploy/control-ha/README.md).
- Storage/writer map: [HA-02 scope and queue](https://github.com/Joker20380/family_connect/blob/feature/device-technical-metadata-20261115/docs/control-ha-storage.md).

## Implemented and verified

HA-01 supplies read-only single-transaction SQLite fingerprints, HMAC-only row/
schema/paid-policy evidence, a loopback-only mTLS etcd adapter and a real pinned
three-process rehearsal. No row export, product write or automatic admission.
etcd3.7.4 archive and binary SHA256 are pinned in source; binaries, logs, test keys
and synthetic databases remain outside Git under `/tmp/fc-control-ha-20261123/`.

61 focused tests pass using control/identity lockfiles; `pip check` and whitespace/
documentation links pass. Real rehearsals verify leader crash, remaining majority,
no-quorum read/publication refusal, stale-CAS refusal, unauthenticated TLS rejection
and direct readback from every recovered member. Final local failover is1.766s,
not a WAN/product RTO or SLA. A separate SIGTERM check confirms all three owned
children are stopped. Initial strict X.509 failure was repaired with AKI/SKI and
KeyUsage extensions, not by weakening certificate checks.

## HA-02L — diagnostics recovery

Source checkpoint `6cd46c938405d2a6294f6339ee1fdb58dcfe39f9`, fromc484d6d4, is
published in the authoritative metadata branch. This old main is navigation only;
no runtime merge/deployment or removal of original dirty/untracked work.

Synthetic canonical proof consumption, Support ID binding and latest report now
share one SQLite/PG transaction. Validation/conflict/rate/capacity/save/prune failures
roll back proof too; ambiguous committed ACK needs a fresh proof with the same report.
Duplicates of the retained report preserve receipt/TTL. Schema1 per-report opt-in
is NOT metadata consent epochs/tombstones: fresh signed resubmission after expiry
remains allowed.4096 bytes/5000 devices/60s/7 days and no raw log/IP/history remain.
Legacy separate SQLite commits remain separate; canonical state refuses the split
entrypoint. Production HTTP/CLI/retention worker and backend are not changed.

Final113 real DB contracts PASS /0 skips (73 diagnostics +40 enrollment),217 focused
regressions PASS /16 explicit optional skips (15 nginx,1 pinned sync archive).
Closed HTTP/support packages, legacy diagnostics/desktop senders, metadata and
proof/support behavior pass; prior overlay/readiness gates remain open. Final
`diagnostics-3/receipt.json` under the private `/tmp/fc-control-ha-20261123/` records
actual SIGKILL/restart/current restore PASS and owned-container cleanup. An earlier
unregistered-device test expected proof issuance, but policy already refuses the
challenge: fixed the test, not the policy. Final runner has no failures/skips.

Exact12 lab tables/19 rows survive: current report, acknowledged expiry deletion,
Support IDs, paid state, device revoke and still-valid used/pending challenges.
Stale pre-prune/revoke backup refuses against retained current lab state; not an
automatic live freshness oracle. Keys/clock retained in memory, NOT restored.
No full cross-store product backup/import, PG/WAL/backup physical-erasure policy,
replication/RPO0 or reverse migration is qualified. Abort before cutover only stops
the owned lab; after new writes fence writers and recover current state, never
old SQLite. No live service/database needs restoration in this checkpoint.

Console5ce82415, NL GeoIP22 November, Android126/catalog9,8/12/120s and all-three-node
ACKs unchanged. RU remains a dependency; no fresh live-health check. Next bounded
writer is notices, then remaining writers/full import/recovery/replication and
HA-03..05. Full sanitized evidence/runbook remain in the linked source worktree.

## HA-02K — metadata and consent recovery

Source checkpoint `a72941d0840a28e0fa5292fdbf97ab9eb5f6b6d1`, from36c23756, is
published on the authoritative metadata branch. No source merge/deployment from
this older main. Its independent navigation push may remain non-fast-forward;
preserve existing dirty/untracked work and never force/rewrite history.

Canonical synthetic SQLite/PG now commits signed proof consumption with latest-only
metadata or revoke tombstone. Failure/rejection rolls back both. Exact report retry
after commit ACK loss needs a fresh proof, not a new consent epoch, and does not
refresh received/TTL. Sample/revoke races retain newer consent; old/same-epoch samples
cannot undo revoke, but a new explicit epoch can opt in. Per-group expiry/prune
retains epoch/sequence/digest/capacity slot; read-only view takes no writer lock.

Legacy production API still commits proof before its separate metadata file; this
two-store boundary is not falsely described as atomic. PG/synthetic canonical state
refuses that legacy entrypoint. No HTTP/CLI selector, actual cross-store import,
collector/retention cutover or default-consent change. Schema1 and6144-byte/5000-device/
60s/7day limits remain. GeoIP source/lookup unchanged; no real metadata/IP read.

Final120 real DB contracts PASS /0 skips (80 metadata +40 enrollment).152 focused
regressions PASS /16 optional skips /2 failures;15 skips need real nginx and1 needs
a pinned sync archive. Both failures are historical metadata-overlay fixture reverse
patching, reproduced on unchanged36c23756. Pins/tests were not weakened. Actual
current HTTP metadata route, legacy consent/retention, GeoIP/fleet and closed support/
HTTP packaging checks pass, not a full release gate. Earlier package gates stay open.
First recovery setup lacked the required signed Android baseline for synthetic
payment; corrected with ordinary proof-bearing Android126 support observation,
without changing policy. Failed evidence retained; final entire runner passes.

Actual owned PostgreSQL17.11 SIGKILL/restart/current restore preserves12 lab tables/
26 rows; stale pre-revoke snapshot refused. Restored triggers/tombstones/proof use/
paid retry retained; expired replay does not resurrect observations, pending proof
works once and explicit new-epoch consent works. Private receipt:
`/tmp/fc-control-ha-20261123/metadata-2/receipt.json`; owned cleanup PASS. Synthetic
keys retained, NOT restored. Logical TTL does not qualify physical erasure from PG
pages/WAL/backups; no full product backup/replication/RPO0/reverse-import/fencing claim.
Locked pip, whitespace,891 local source-doc links and staged15-file scope/key/token
scan PASS. Production console5ce82415, Android126/catalog9 and8/12/120s unchanged.

Before cutover abort only owned lab; no product restore needed. After live writes
fence old writers and recover current acknowledged consent/proof/payment state,
never old SQLite/CRL or pre-revoke panel rows. Source rollback is a new revert commit
if requested. Next: diagnostics/notices/remaining writers, cross-store import,
privacy-aware backup and full recovery/replication, then HA-03..05. All-three-node
first-cohort ACKs remain mandatory; RU dependency and its separate availability
problem are not resolved by this source checkpoint.

## HA-02J — durable CRL recovery

Source checkpoint `019aa578788d58a044798a0604fcab5be61c7ec8`, from86660b86, is
published on the authoritative metadata branch. No source merge/deployment from
this old main; existing dirty/untracked work preserved. Its separate navigation
push may remain non-fast-forward; do not force or rewrite history to resolve it.

CRL sequence, immutable signed candidate, request/payload hashes and validity now
share a SQLite/PG transaction with grant/device/invite/revision/paid checks. Replay
returns exact bytes without signing or prolonging validity. Pending/local-receipt
checks refuse stale, expired or inconsistent candidates. Local file helper is
script-only, temporary and single-publisher; DB receipt is NOT a remote ACK/fence.
Legacy SQLite file-before-commit behavior stays separate: file-ahead retry advances
max(file floor,DB floor)+1. PG/synthetic outbox cannot use legacy sync/canary writers.
Production distributed publication still requires HA-03, node ACK/readback and
bounded recovery; old processes/CLI/file journals need explicit migration fencing.

Final128 real DB contracts PASS /0 skips (88 CRL +40 enrollment),285 focused consumer/
package/runner regressions PASS /20 optional skips. These are4 locked-Go,15 nginx
and1 pinned-sync archive checks, not qualified. One preliminary SQLite test-only
directory assertion failed because the fixture already contained its DB; corrected
to compare before/after entries and rerun on both databases without weakening guards.
Prior exact-overlay and HA-02G artifact-dependent package gates remain open.

Actual PostgreSQL17.11 owned-container SIGKILL/restart and separate current restore
preserve19 lab tables/22 rows. Stale restore refused; immutable triggers retained,
consumed/revoked proofs refused, payment retry unchanged. Pending receipt0 survives
despite already replaced local file; exact stored bytes reconcile and next candidate
advances. Private receipt `/tmp/fc-control-ha-20261123/crl-2/receipt.json`; owned
cleanup PASS. Keys retained, NOT restored; no full product/key recovery, RPO0,
replication, reverse import or distributed authority claim. Locked pip/whitespace/
879 local source-doc link targets and staged16-file scope/key/token scan PASS.

Before cutover abort only owned lab; no production restore needed. After future
canonical writes fence writers and recover current acknowledged state, never old
SQLite/CRL. Source rollback is a new revert commit if requested. Next: metadata/
consent tombstones and remaining writers/CLI/files, full import/recovery/replication,
then HA-03..05. Console5ce82415, Android126/catalog9,8/12/120s and all-three-node
first-cohort ACKs unchanged. RU remains a dependency; no fresh live-health claim.

## HA-02I — gateway routing recovery

Source checkpoint `b5cb676bd905580e2519a55bdea1d70a7b3d7153`, fromccef2c08, is
published on the authoritative metadata branch; source worktree is named above.
No source merge/deployment from this older main. Its unrelated dirty/untracked
work is preserved; independent root navigation push may remain non-fast-forward.

Common SQLite/PostgreSQL transactions now cover policy generation/install/seed,
sticky assignments, explicit moves and operation journals; selection import is
separate from sticky state. Status/selection use read-only snapshots. Operation
IDs bind exact payloads, ACK-loss retries do not duplicate evidence or undo later
work, and conflicting concurrent moves have one winner. Device/invite revoke is
checked before assignment/catalog read. Selection also rejects generation corruption.
Offline catalog verification and all existing public protocol formats are preserved.

111 real DB contracts PASS /0 skips (71 routing +40 enrollment),327 focused existing
HTTP/client/catalog/package/runner checks PASS /26 optional skips. These are16 nginx,
2 locked-Go native delivery,1 pinned-sync and7 exact served-archive cases; not accepted.
Prior exact-overlay and artifact-dependent readiness packaging gates remain open.

PostgreSQL17.11 actual owned SIGKILL/restart and separate current restore preserve
all15 synthetic tables/28 rows, including assignments, operation history, proofs,
revokes and payment state. Stale pre-routing backup refused; restored append-only
triggers still reject writes. Consumed proof refused, pending proof usable once;
committed operations/payment retries unchanged. Return to the earlier physical host
works with a newer signed catalog, never an old sequence/DB rewind. Final private
receipt: `/tmp/fc-control-ha-20261123/routing-2/receipt.json`; cleanup PASS.

Signed files/anchors and synthetic identity keys are retained, NOT recovered.
HTTP proof use, routing, paid decision and remote registration remain separate
boundaries; use a fresh proof after a lost response. No distributed atomicity,
full product recovery, replication/RPO0, fencing or production selector claim.
Rollback now is owned-lab cleanup; after live writes require fenced current-state
recovery, not old SQLite. CRL/files/remaining writers, metadata/tombstones, full
import/recovery/strict replication and HA-03..05 still block production HA.
Console5ce82415, Android126/catalog9,8/12/120s and all-three-node first-cohort ACKs
unchanged; RU remains a dependency, no fresh server-health claim.

## HA-02H — chat and support sender recovery

Common SQLite/PostgreSQL transactions now cover chat identity/proof, service sender
registration/revoke, membership sequence and support binding. Both signatures,
immutable identity, terminal sender revoke, capacity8/550 and100s lease remain.
Support sender validation and enrollment share one transaction; time is checked
after transaction waits. Safe read-only configuration/inventory does not enroll.
No production selector; PG mailbox/support-file publication refuses before any I/O.

114 real DB contracts PASS /0 skips (74 chat/support +40 enrollment),238 consumer/
package regressions PASS /23 explicit optional skips,18 final runner guards PASS
(overlapping runner selection, not18 extra unique cases). Closed support kit import/
reproducibility passes; nginx/pinned archives and prior packaging gates remain open.
Two initial recovery attempts failed in fixture setup/error classification; both
retained, repaired without weakening paid or stale-restore guards. Full commands
and evidence are in the authoritative feature-branch report.

Actual PostgreSQL17.11 SIGKILL and separate exact15-table/29-row current restore
preserve proof use, identities, service revokes, support binding, sequence and
coexisting aliases/paid/audit. Stale dump refused; pending proof consumes once and
sequence continues. Keys/local policy are retained, NOT restored: not full product/
secret recovery, remote mailbox ACK, RPO0, replication or reverse migration.

No SSH/live-health check or production/server/client/consent change. Console5ce82415,
Android126/catalog9 and RU dependency unchanged. Rollback now is owned-lab cleanup;
after future writes, fence and use current-state recovery, never stale SQLite.
Next: gateway assignment/routing, remaining DB writers/CLI, CRL/files/metadata,
full import/recovery/replicas and HA-03..05 gates before live cutover.

## HA-02G — restricted issuance and readiness recovery

Restricted challenge/certificate/auto-enrollment and readiness ACK/readback now
share a SQLite/native-PostgreSQL transaction boundary. Proof use and writes commit
together; readback is a read-only snapshot without a PG writer lock. Preserve
owner/node/revision/family/CRL binding, paid expiry, capacity8, receipt24h/cap16 and
offline noncohort policy. Lost commit ACK requires readback/new proof, never replay.
Strict PG markers include paid schema; no fallback to unpaid or production selector.

163 real DB contracts PASS /0 skips (123 restricted +40 enrollment),521 focused
regressions PASS /36 explicit optional skips,121 isolated-root maintenance checks
PASS /3 retained-snapshot skips. Earlier unprivileged ownership attempt failed;
proper no-network/read-only-source Docker rerun passes.28 artifact-dependent adapter
cases remain unqualified without accepted Go/HTTP fixtures, not masked as PASS.
Four prior baseline overlay failures remain open. See authoritative report for all
attempts/commands; raw logs/dumps/credentials remain private outside Git.

Actual PostgreSQL17.11 SIGKILL/restart discards unfinished writes. Exact current
restore of16 lab tables/36 rows preserves consumed/pending proofs, ACKs, certificates,
revokes, support/paid/audit; stale pre-issuance dump is rejected. Pending fetch/ACK
works once after restore, certificate reuse/paid bounds hold. Ephemeral issuer keys
are retained in memory, **not restored**: no secret recovery, full product backup,
replication/RPO0 or fenced authority is qualified.

No server/backend/client change, SSH/live-health readback or release publication;
console5ce82415 and Android126/catalog9 unchanged, RU dependency remains. Rollback
now is owned-lab cleanup only. After future writes, fence and recover current state,
not old SQLite. Next: support sender, remaining writers/CLI, CRL/files/metadata/
tombstones, full import/recovery/replicas and HA-03..05 gates before cutover.

## HA-02F — restricted grants and audit recovery

Shared SQLite/PostgreSQL explicit grant/renewal, idempotent grant revoke and audit
transactions are qualified. Native PG grant FK/CHECK and explicit DB-only marker;
no production backend/CLI selector. Concurrent renewals preserve revision, device
revoke cannot be overridden. Grant ACK loss needs readback, not a blind renewal.
Audit/revoke rollback together; APPLIED→INCOMPLETE compensation is permitted after
lost commit ACK, but INCOMPLETE→APPLIED replay is refused. Actual SQLite FIELD
CRL/file path and this compensation are tested. This is not DB/file atomicity.

176 real DB contracts PASS /0 skips in40.68s (70 admin,40 enrollment,66 support).
264 focused consumer/operator/runner checks PASS /4 optional locked-Go skips in10.23s.
Pinned PostgreSQL17.11 SIGKILL/current restore preserves12 lab tables/20 rows,
including grant/device revoke, revisions, consumed/pending proof, Support IDs, paid
ledger and pending audit. Audit ID sequence continues; pending audit closes only by
an explicit operation. A stale pre-revoke backup is refused against known lab state.
This is not a full product backup, production watermark, reverse migration or RPO0.

First `admin-1` run passed contracts but recovery setup correctly hit
ANDROID_BASELINE_REQUIRED; fixture now records the supported Android observation
before its synthetic payment. No guard weakened; failed evidence retained outside
Git. Successful evidence is `/tmp/fc-control-ha-20261123/admin-2/`; focused regression
log is `admin-regressions-1.log` in its parent. Owned container cleanup, locked pip
check, staged16-file secret-marker/scope scan and870 local Markdown targets PASS.

PG FIELD/CRL publication stays blocked before file I/O. Auto-enroll, restricted
challenges/certificates/readiness, CRL sequence, fenced file reconciliation, sender
and remaining writers/import/replication remain pending. No SSH/deployment or new
RU/NL health claim. Console5ce82415 and Android126/catalog9 unchanged; RU remains a
dependency. Four prior exact-package failures stay open. Rollback now stops only
the disposable lab; after future cutover writes use fenced current-state recovery,
never an older SQLite backup. Authoritative implementation is in the metadata branch,
not this divergent main; preserve unrelated local edits and do not force its push.

## HA-02E — Support ID observation and recovery

Support ID backfill/request/inventory/lookup now share SQLite/PostgreSQL transaction
semantics. Request proof and app-version observation commit together; a failed
UPDATE/backend loss rolls both back. Missing aliases are not allocated during
delivery. Batch backfill preserves existing aliases/bindings/revoked rows, retries
collisions within32 attempts, and rolls back the whole batch on failure.

Readiness does not infer platform or replace newer request data. Null timestamps
sort last with a deterministic correlation tie-break; malformed optional receipt
objects/timestamps are not observations. Safe lookup and existing explicit-list/
all-activated rules remain. This is app-version support metadata, not OS/GeoIP or
new consent/telemetry collection.

155 real DB contracts PASS /0 skips in54.05s:66 support +40 enrollment +49 paid.
443 consumer/runner tests PASS /21 optional skips in44.21s (16 real nginx,1 pinned
sync artifact,4 locked Go checks). Expanded deterministic operator.pyz test1 PASS
in2.33s runs backfill/inventory/lookup under `python -I` on synthetic SQLite; this
overlaps the443 selection rather than adding another distinct test.

Actual PostgreSQL17.11 SIGKILL/restart and fresh-container restore preserve12 lab
tables/19 rows, including paid state, support observations and read-side restricted
fixtures. Consumed/pending proofs, stable aliases, revocation and audit sequence
survive. Uncommitted observation/proof changes roll back; older readiness does not
downgrade the app version. A stale pre-observation backup is refused by comparison
with the known committed lab snapshot. Not full product recovery, replication or
production reverse import. Raw evidence stays outside Git at
`/tmp/fc-control-ha-20261123/support-1/`; owned test-container cleanup verified.

FIELD grant/audit/CRL/admission-file writers and support sender are still pending.
PostgreSQL FIELD mutation explicitly refuses before opening any files; SQLite
operator behavior remains. No server services, production DBs, clients/catalogs,
keys or consent changed. Console5ce82415 and Android126/catalog9 unchanged. Prior
four historical packaging failures remain open; no new production HA/RU independence.
Rollback of this checkpoint stops only the owned disposable lab, never restores
old production state. Next: restricted/admin DB and support sender writers, then
other canonical writers/metadata/files/import/recovery, replication and HA-03..05.

## HA-02D — referral transactions and recovery

Shared SQLite/PostgreSQL referral transactions now commit proof/link and
invitation/claim atomically. Pool500/daily20 and same-proof/request races use the
existing enrollment/revoke transaction locks. Replay must match the original
sponsor and reconstructed invitation hash; another sponsor token is rejected.
Existing child invitations remain independent of later sponsor revocation;
revoked child invitations are not returned. SQLite remains the production default.

Final qualification:181 DB contracts PASS /0 skips in99.07s (50 referral +131 prior),
379 consumer/runner checks PASS /21 optional skips in37.01s (16 real nginx,
1 pinned sync archive,4 locked Go checks). Actual PostgreSQL17.11 SIGKILL/restart
preserves committed records and rolls back unfinished invite/claim. Current dump
restores row-for-row into another owned container:9 nonempty lab tables/18 rows.
Consumed proofs and revocation survive; a pending invitation activates after
restore. A pre-claim backup is refused. This is not all-table product recovery,
replication or production reverse migration. Prior four packaging failures remain
an open deployment gate; old pins were neither weakened nor requalified here.

After lost claim ACK, retry the same token/request ID with the existing secret.
After committed issue, use a fresh proof to obtain the same link; do not reuse a
consumed proof, rotate the secret or restore stale DB state. Before commit failure,
all associated writes roll back. Raw evidence/credentials/dumps stay outside Git
under `/tmp/fc-control-ha-20261123/referrals-2/`; owned-container cleanup verified.

No live servers, product databases, consent, transport policies, client builds or
catalogs changed. Console5ce82415 and Android126/catalog9 unchanged; RU remains a
shared dependency. Rollback of this checkpoint stops only the disposable lab.
Next: support/admin and other writers/CLI, metadata/tombstones/files, full import
and recovery, replication, then mandatory fencing/API/cutover gates.

## HA-02C — node preparation and failure consistency

SQLite and the explicitly enabled synthetic PostgreSQL mode now share first-payment
preparation of all three serving nodes. ACK validation is strict (size, UTF-8,
JSON duplicates, exact node/token/fields, integer schema); commands validate before
contact. PostgreSQL's membership-required mode cannot silently fall back to the
separate no-transports mode, including after real pg_dump/pg_restore.

131 real SQLite/PostgreSQL contracts PASS /0 skipped, including42 new membership
cases. The three node fixtures use actual Gateway cache/locks/fsync/readback logic
with simulated AWG/TCP/systemctl/network, not live servers. ACK loss on each node,
readback failure, DB rollback, real backend termination after all ACKs, unchanged
5s idle timeout, concurrent retry, cache reload, stale noncohort snapshots and
terminal revoke pass. Inherited crash/current restore/stale-backup refusal also pass.

**A DB rollback must not undo a prepared node deny.** No partial payment commits;
already-prepared target nodes stay denied, other noncohort/foreign entries remain.
Retry the same event ID/payload to finish the transition; do not delete `prepared`,
restore old node cache or automatically extend time. First cohort transition still
requires all three nodes including RU; a smaller serving set needs HA-03 fencing.
Node8s/watchdog12s/paid120s and network12s remain unchanged. The lab's5s PostgreSQL
idle timeout is fail-closed, not a qualified WAN scheduling/deadline design.

Broader suite:389 PASS /16 optional skips /4 failures. All four historical exact
overlay tests also fail on unchanged baselineeeb11ba7 after checking capsule imports
and bytes (`UNRELATED_PAID_DELTA`, `POLICY_CHANGE_FORBIDDEN`). These are not introduced
by HA-02C; they remain an explicit package/deployment gate. No old pin/guard or public
artifact was changed. Full release acceptance is not claimed. Failed attempts and
exact test commands/evidence are retained in the authoritative source report.

Final private evidence: `/tmp/fc-control-ha-20261123/membership-3/`; no owned test
containers remain. No live export, server restart, production DB switch or client
release. Next are remaining support/admin/referral writers, metadata/tombstones/files,
full migration/recovery and replication, followed by mandatory fencing/API/cutover gates.

## HA-02B — paid/subscription and exercised recovery

Owner explicitly requires rollback safety. Payment state transitions and personal
subscription proofs now have a shared semantic transaction boundary; SQLite is
still the default. Native PostgreSQL paid tables/triggers exist only in the
explicit synthetic `no-transports` store. SQLite retains first-payment node
preparation; production transport membership/wiring is not migrated.

89 real SQLite/PostgreSQL contracts PASS /0 skips, including duplicate ACK-loss,
event-ID conflict, cohort/proof races, atomic rollback, terminal revocation and
exact all-node projection parity.366 consumer/runner checks PASS /20 optional
nginx/sync/Go skips; separate final runner checks13 PASS. No release gate claim.

Actual SIGKILL/restart preserves acknowledged payment/grace/revoke and consumed
proof while dropping uncommitted writes. An older pre-payment dump is restored in
an isolated container and explicitly REFUSED because it loses acknowledged state.
The latest dump restores all12 rows across nine lab tables exactly in another
fresh container. Replay, restored immutable triggers and audit sequence pass.
Final private evidence is `/tmp/fc-control-ha-20261123/paid-3/`; owned containers
and anonymous volumes are removed, dumps/credentials/raw rows stay outside Git.
Earlier failures and their corrections are documented in the source-worktree
dated report, not erased or relabelled as successful first attempts.

This proves single-instance synthetic recovery, not full product backup,
replication/RPO0, reverse SQLite import or production failover. Before cutover,
abort only the lab/shadow; production needs no restore. After new writes, fence
writers and recover the current acknowledged state; never restore old SQLite
and lose payments/revokes. A production rollback/recovery procedure must pass
its full gates before switching management.

## HA-02A — enrollment checkpoint

Shared Access domain logic now runs through explicit transaction operations,
preserving default SQLite and existing proof/identity/TTL/limit checks. PostgreSQL
is only an injected synthetic repository: no production DSN, fallback writer,
alternate HTTP endpoint or automatic migration. Legacy SQL paths refuse there.

Forty contracts pass on SQLite/real PostgreSQL with no skips: concurrent one-use
proof/invite/limit races, status/replay/revocation, rollback, lost-response recovery,
Support ID collision, schema guard and bounded lock refusal.353 consumer tests
pass;20 optional nginx/sync/Go gates remain skipped, not accepted. Six runner
safety tests pass; locked environments pass pip check. Existing closed HTTP archive
checks pass without changing historical manifests/pins or client dependencies.

PostgreSQL17.11 is pinned by official-image digest; psycopg/binary3.3.9 is optional
lab-only. Real owned-container SIGKILL/restart preserves committed identity,
invitation/revocation and consumed challenge, drops uncommitted insertion and
permits a fresh reconnect. Binary backup restores all11 rows across five nonempty
enrollment tables into a separate fresh container; identity sequence advances.
This is not replication/RPO0 or a full product backup. SIGTERM during pytest leaves
no owned test child/container. Source/restored containers and anonymous volumes
are removed; credentials/dumps/logs remain private under `/tmp`, not Git.

## Not yet implemented

These are isolated checkpoints, **not completed migration**. HA-02 must finish all
production transport-membership wiring/deadlines, other canonical writers/CLI, metadata revoke
tombstones and file coordination to an explicitly qualified replicated store.
Paid/subscription/membership synthetic parity does not qualify production import,
new runtime packaging or full recovery.
HA-03 adds receiver-enforced fencing, HA-04 multi-endpoint API/clients, HA-05 live
shadow and cutover with real failure tests. No HA controller is installed on NL and
no alternative API serves users. RU remains a shared dependency.

Latest known console5ce82415, public Android0.1.18-beta126/catalog9 are unchanged.
No server restart, provider move, policy/consent change or fresh health claim.
The22 November RU outage remains a separate open operational issue.

## Rollback and publication

Current rollback is only stopping the isolated rehearsal and reverting unused
source through a new commit if requested. Do not restore a product DB or replace
deployed archives. After future cutover, old SQLite rollback must not discard
confirmed events; fencing and verified forward/reverse migration are mandatory.

This handoff is separately committed on the old main. Ordinary push remains
subject to its existing non-fast-forward divergence; no force/rebase/merge is
authorized merely to publish these notes. Source availability is established by
the verified feature-branch pushes, not by this main checkout.
