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
