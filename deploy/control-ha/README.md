# Isolated control HA rehearsal — not a production deployment

This first stage tests a real etcd quorum and a read-only evidence format. It does
not replicate the Friends database, elect a product writer, issue permissions,
restart gateways, change endpoints or remove the RU dependency. The candidate
PostgreSQL/Patroni migration is a separate, unfinished stage.

## Run

Use a dedicated environment with `control/requirements.lock` and
`device_identity/requirements.lock`. Download the official archive named in
`rehearsal-etcd.json`, verify its archive SHA256, and extract only the `etcd`
executable outside the repository. The runner independently verifies its binary
SHA256 before executing anything. No automatic download or production install is
performed by the runner. The pinned dependency is etcd3.7.4, Apache-2.0; its source
repository is https://github.com/etcd-io/etcd. No third-party source is vendored.

```sh
python -m pytest -q tests/test_control_ha_shadow.py tests/test_paid_registry_backup.py tests/test_transport_enforcement.py tests/test_transport_membership.py
python -m scripts.control_ha_rehearsal --etcd /tmp/etcd-v3.7.4-linux-amd64/etcd --workdir /tmp/fc-ha-new-rehearsal
```

`--workdir` must be a new non-symlink directory under the system temporary
directory. The runner binds six ephemeral loopback ports, creates a private0700
directory and disposable CA, and starts only its own three etcd children. Client
and peer links require mTLS; CA/private files are0600. No existing credentials,
production configuration, SSH connection or database is consulted. CA signing
material and the dedicated HMAC key are ephemeral, not product keys. The test CA
expires after one hour. New runs require new state directories.

The runner SIGKILLs the elected test leader, publishes through the remaining
majority, kills another member, checks refusal of linearizable reads and publication
before any write attempt, then restarts both members with retained test data.
Each recovered member is checked directly, without client endpoint fallback.
Stale compare-and-swap revisions are refused. Confirmed bytes must survive.
Missing client certificates must be rejected; certificate verification is never
disabled. Normal exit, failures, Ctrl-C and SIGTERM clean up owned children; a
forced SIGKILL of the runner cannot guarantee cleanup. Never kill unrelated etcd.

## Evidence and limitations

- `receipt.json` is a bounded summary. Logs, data directories and private keys stay
  outside Git; retain failed-run evidence. A PASS is only `ISOLATED_SHADOW_QUORUM_PASS`.
- `control_shadow.capture` uses one read-only SQLite transaction for schema, all
  table fingerprints and all three paid decision projections at one timestamp.
  Row values, device IDs, transport keys and payment IDs are replaced by keyed
  HMACs. Row/table/value/time bounds fail closed. No DB migration is invoked.
- Compare only snapshots at the same observation time with the same dedicated
  test HMAC key. Freshness is120s, not a renewable offline grant. Neither a valid
  MAC nor an etcd revision is a product authorization. The existing transport
  envelope parser rejects the shadow format.
- The adapter is intentionally loopback HTTPS only. It uses linearizable reads,
  CAS writes, rejects redirects/invalid responses and reconciles a lost ACK by
  readback. An ambiguous write is not proof of non-commit; never mint a new
  operation/timestamp just to retry it. It is not production fencing.
- One-laptop crash tests do not prove WAN partition handling, independent failure
  domains, PostgreSQL RPO0, CRL/metadata recovery or client failover. Measured local
  failover is not production RTO/SLA. No live SQLite snapshot was exported.

See [migration gates and rollback](../../docs/control-ha.md) and
[dated evidence](../../docs/releases/2026-11-23-control-ha.md).

## HA-02A: isolated PostgreSQL enrollment

Requires local Docker and Python dependencies in a **dedicated** environment:

```sh
python -m pip install -r control/requirements.lock -r device_identity/requirements.lock -r deploy/control-ha/requirements.lock
docker pull postgres@sha256:18cfe3ef5e6815560c98237d6216d1e5119702fb0f3894c8785dd58b8bbe5d73
python -m pytest -q tests/test_enrollment_rehearsal.py
python -m scripts.enrollment_postgres_rehearsal --workdir /tmp/fc-ha-enrollment-new
```

The runner requires the pinned image already present (`--pull=never`), verifies
PostgreSQL17.11 and durability settings, and uses the explicit local Unix Docker
socket, never an inherited remote Docker context. Two owned containers (source and
isolated restore) use their own anonymous volumes,512MiB/one CPU each and ephemeral
ports published only on127.0.0.1. No host product-directory mount, production
environment, database or SSH access. Plain PostgreSQL/SCRAM over this disposable
loopback binding is **not** a production TLS design; do not expose the port.

The forty contract cases include both SQLite and real PostgreSQL; standalone
pytest without `FC_HA_PG_PORT` reports PostgreSQL cases as skipped, **not PASS**.
The runner supplies private test credentials, requires zero skipped contracts,
SIGKILLs only its marked source container, restarts retained test data and verifies
committed identity/revocation/invitation, consumed proof, uncommitted rollback and
reconnection. It then dumps five nonempty enrollment tables, restores them into
a fresh container, compares every row and checks identity-sequence continuation.

`receipt.json` records bounded results/counts. Password/env files, binary dump,
JUnit and logs remain in the private0700 workdir (secret/dump/log files0600).
Cleanup verifies exact container ID and random ownership label before removing
only those containers and anonymous volumes. Failure, Ctrl-C and SIGTERM also
clean up; SIGKILL of the runner/daemon failure needs ownership-checked recovery.
Never use a global Docker prune or remove an unrelated PostgreSQL container.

No alternate serving API, production DSN, SQLite import, production paid/metadata migration,
replica, Patroni failover or receiver fencing exists here. See the
[writer inventory and remaining HA-02 gates](../../docs/control-ha-storage.md).

## HA-02B: isolated paid/subscription recovery

Use the same pinned local Docker image and dedicated dependencies as HA-02A:

```sh
python -m pytest -q tests/test_paid_rehearsal.py tests/test_enrollment_rehearsal.py
python -m scripts.paid_postgres_rehearsal --workdir /tmp/fc-ha-paid-new
```

The runner requires a new private temporary directory. It now runs131 enrollment/paid/membership
contracts with zero skips, then SIGKILL/restarts its source container. Confirmed
payment/grace/revoke and a consumed subscription proof survive; an uncommitted
event does not. Retries with the same event ID/payload never grant a new period.

Two backups are deliberately exercised in two sequential fresh restore containers:
the earlier **pre-payment** backup must be refused as stale, and the latest backup
must match every row of all nine lab tables. Restored payment replay, proof refusal,
revocation, immutable triggers and audit sequence are checked. No live database is
read or restored. Existing ownership guards, loopback binding, resource limits and
cleanup apply. Keep receipts/logs/dumps/password files private and out of Git.

The only success receipt is `ISOLATED_PAID_POSTGRES_PASS`, emitted after cleanup.
This proves neither replication/host-loss RPO0 nor SQLite reverse migration. The
`no-transports` lab marker explicitly excludes node-membership preparation; the
SQLite production path retains that prerequisite. Remaining writers, metadata,
files/CRL and full canonical backup remain gates. An old snapshot is **not** a safe
production rollback after acknowledged writes: fence writers, retain current
state and use a separately verified recovery path before any cutover.

## HA-02C: required membership and rollback consistency

The same `scripts.paid_postgres_rehearsal` command now includes42 membership cases.
They use the real `Gateway` cache/locking/fsync and readback algorithms on three
separate temporary node roots, with **simulated AWG/TCP/systemctl commands and
network exchange**. No real host service or firewall is touched. SQLite's existing
command-map wrapper and the native PostgreSQL transaction invoke the same protocol.

First payment requires exact durable-preparation ACKs for all three nodes. Missing,
ambiguous, duplicated, incorrectly typed or mismatched ACKs cannot commit payment.
Partial prepare, failed commit, killed PostgreSQL backend and the unchanged5s
idle-in-transaction timeout preserve prepared target denies. Cache reload/restart
and noncohort snapshots never clear them. Retry only the original event ID/payload;
after commit it returns the original event without re-preparing or extending time.
This is not automatic compensation or a permission to erase node cache.

An additional fresh-store rehearsal creates `membership-required` schema version2,
dumps/restores it into a separate disposable container and verifies that a first
payment still fails without an explicitly supplied exchange, leaving every row
unchanged. Receipt field `required_mode_restore=REFUSES_MISSING_EXCHANGE` records
this gate. Version1/no-transports remains the explicitly separate HA-02B lab mode.
The source plus three sequential restore containers retain all ownership/cleanup
guards; credentials, dumps and raw receipts remain private.

Do not infer WAN-ready behavior: PG's5s idle timeout may interrupt a slow prepare
before the existing12s network timeout. No timeout is increased; node8s/watchdog12s/
paid120s remain. Production CLI/wiring, serving-set fencing/quarantine, remaining
writers, replicas and full recovery remain gates. RU is still in the required
three-node set and cannot silently be dropped to make a payment succeed.

Broader qualification currently includes four historical exact-overlay failures
also reproduced on the unchanged source baseline; see the dated report. Do not
update old hashes/guards or use those packagers to deploy HA source. Qualify a new
closed runtime separately before any production switch.

## HA-02D: isolated referral transactions and recovery

Use the same locked environment, psycopg3.3.9 and preloaded pinned PostgreSQL17.11
image as HA-02A/B/C. No new dependency, network download or production selector:

```sh
python -m scripts.referral_postgres_rehearsal --workdir /tmp/fc-ha-new-referral-rehearsal
```

The runner executes181 SQLite/PostgreSQL contracts with zero skips:50 referrals
plus the131 enrollment/paid/membership contracts. The referral tests exercise the
actual shared500-slot pool,20-per-day boundary, independent concurrent connections,
atomic proof/link and invitation/claim, sponsor-bound replay, ACK loss, revoked
sponsor versus independent child invitation, and killed backend rollback.

The source container's actual SIGKILL/restart must preserve every committed row
and roll back both unfinished invitation and claim. Two sequential owned restore
containers compare an old pre-claim dump (refused) and a current dump (exact9-table,
18-row synthetic store). Consumed proofs, sponsor/child revocation, activated and
still-pending invitations survive; the pending invitation activates after restore.
`restored_rows` refers to this referral fixture, not the distinct paid fixture or
the whole product. This runner re-executes prior DB contracts, not prior paid
backup/restore scenarios. All file/privacy, loopback, pinned image, ownership and
cleanup protections are inherited unchanged. No volume from production is mounted.

SQLite remains the production backend. No support/admin migration, secret rotation,
replication, alternate endpoint, serving-set change or server deployment is implied.
Rollback stops only the disposable owned containers. After a lost claim response,
retain the same secret/token/request ID; after committed issue, use a fresh one-use
proof for the same link. Never restore stale state to recover an ambiguous result.

## HA-02E: isolated Support ID observations and recovery

Use the same pinned PostgreSQL17.11 image and locked psycopg3.3.9 environment:

```sh
python -m scripts.support_postgres_rehearsal --workdir /tmp/fc-ha-new-support-rehearsal
```

This risk-selected runner executes155 real DB contracts with zero skips:66 support,
40 enrollment and49 paid. It does not rerun unchanged referral/membership contracts.
Cases cover atomic support proof/observation, missing aliases without allocation,
whole-batch backfill rollback, collision exhaustion/retry, independent concurrent
API connections, revoke races, ACK loss, actual killed backend and strict PG marker.
Readiness null ordering/ties, invalid optional ACKs, version freshness and safe
lookup/admission semantics are checked against both backends. FIELD mutation on PG
must refuse before any file open; the live operator CLI remains SQLite-only.

The recovery fixture combines enrollment/support/paid with two explicitly synthetic
restricted read-side tables; it is not a restricted writer migration. The source
container is SIGKILLed with uncommitted observation/proof changes. Restart must
preserve all committed rows and drop both unfinished writes. Separate old/current
restore containers reject a stale pre-observation dump and require exact current
12-table/19-row state. Aliases, version freshness, consumed/pending proofs, revoke,
payment replay and audit sequence continuity are exercised after restore.

The comparison uses the known lab committed snapshot; no production high-watermark
or disaster-recovery service is implemented. Existing ownership/loopback/private-file
guards and cleanup apply unchanged. No live configuration, product secret or server
data is read. Stop only the owned disposable lab for rollback. This does not complete
FIELD grant/audit/file writers, sender bindings, canonical import, replicas or HA.

## HA-02F: isolated restricted grant/audit DB recovery

Use the same dedicated locks, psycopg3.3.9 and pinned PostgreSQL17.11 image. No
production selector, credentials or existing database is used:

```sh
python -m scripts.restricted_admin_postgres_rehearsal --workdir /tmp/fc-ha-admin-new
```

The runner exercises176 SQLite/real-PG contracts (70 admin,40 enrollment,66 support)
without skips. Admin scope is explicit grant/revoke/audit transactions, not restricted
certificate/readiness/CRL or FIELD file publication. PG FIELD/CRL operations must
still refuse before file access. SQLite operator ordering and compensating revoke
remain; a separate consumer test covers loss of APPLIED commit acknowledgement.

Grant renewal increments revision and is **not idempotent**: unknown commit needs
readback, not blind retry. Revoke and audit completion are idempotent. A pending
audit is not success. APPLIED can become INCOMPLETE during fail-closed compensation;
INCOMPLETE cannot be promoted back to APPLIED by replaying the completion.

Recovery combines enrollment/support/admin with paid state. SIGKILL with unfinished
grant/audit/proof changes must preserve committed data and discard those changes.
Restore runs in distinct owned containers: stale pre-revoke dump is refused; current
12-table/20-row lab snapshot must match exactly. Check grant/device revokes/revisions,
paid replay, consumed/pending proof, pending audit and continuation of audit IDs.
Known-snapshot comparison is not a production high-watermark or RPO0 service.

All ownership/loopback/private-file rules apply; only the runner's containers and
volumes are cleaned. Preserve failed evidence. Rollback is stopping this lab, never
restoring an old SQLite/product backup. Fencing, file reconciliation, full canonical
import, replicas and production cutover remain blocked on their separate gates.

## HA-02G: isolated restricted issuance/readiness recovery

Use the same dedicated control/identity/HA locks, psycopg3.3.9 and pinned PostgreSQL17.11:

```sh
python -m scripts.restricted_postgres_rehearsal --workdir /tmp/fc-ha-restricted-new
```

This runs163 SQLite/real-PG contracts (123 restricted +40 enrollment), then an actual
SIGKILL/restart and distinct stale/current restore. Fresh workdir, loopback-only DB,
private evidence and owned-container guards are inherited unchanged. No SSH, existing
product database, production credentials or authority keys are used. Synthetic issuer
keys are generated in memory and retained across restore, **not backed up/restored**.

Required checks: one-use concurrent fetch/ACK, rollback and lost-ACK semantics,
node/owner/grant/CRL binding, auto-enroll eligibility, paid expiry, receipt retention
and read-only snapshot. Current16-table/36-row lab restore must match exactly before
testing consumed-proof refusal, pending fetch/ACK once, certificate reuse and paid
bound. Stale pre-issuance restore must fail known-snapshot comparison. Private logs,
dumps and credentials remain outside Git; retain failed attempts as well as PASS.

No production selector, replicated issuer, CRL/file publisher, secret recovery,
reverse migration or RPO0 is provided. Rollback now means stopping the owned lab,
not restoring a product DB. After future production writes, fence writers and use
current-state recovery; old SQLite is not an unconditional rollback. All-three-node
first-cohort ACKs and8/12/120s remain unchanged. Full HA gates still block cutover.

## HA-02H: isolated chat/support sender recovery

Use the same dedicated control/identity/HA locks, psycopg3.3.9 and pinned PostgreSQL17.11:

```sh
python -m scripts.chat_postgres_rehearsal --workdir /tmp/fc-ha-chat-new
```

Runs114 SQLite/real-PG contracts (74 chat/support +40 enrollment), then actual
SIGKILL/restart and separate stale/current restores. Reuse no existing workdir or
credentials: loopback-only, temporary/private evidence, image/ownership/cleanup
guards are unchanged. No SSH, production DB, product identity or policy is read.

Check both device signatures, immutable bindings, one-use proofs/cap8, service vs
device identity exclusion, terminal service revoke, support sender validation/write
in one transaction, membership550, monotonic sequence and100s lease. Failure and
commit-ACK-loss tests must not turn old proof/sequence into a fresh authorization.
Read-only configuration/inventory cannot enroll; fresh time is checked after waits.
PG mailbox/support-file publication must refuse before lock/key/file/network I/O.

Recovery must match all15 lab tables/29 rows before new writes, including paid/
aliases/audit coexistence. Stale pre-chat snapshot must fail with the exact restore
refusal reason. Consumed proof and revoked service registration remain refused;
pending chat proof consumes once, support binding persists, sequence continues.
Test keys and local policy are retained, not recovered: secret/file recovery, remote
mailbox ACK, replica/RPO0 and reverse migration are unqualified. No production selector.

Retain failed evidence outside Git. Rollback is owned-lab cleanup; after future live
writes require fencing/current-state recovery, never an unconditional old SQLite
restore. Gateway assignment and remaining canonical writers/import/recovery/replicas
and HA-03..05 gates still block production cutover.
