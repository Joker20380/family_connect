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
