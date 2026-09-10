> Current deployment: 0.2.1 is deployed; API and Docker worker verified. See [STATUS](STATUS.md).

# Gateway peer reconciliation and revocation

2026-09-10. Implemented for a single product host; not deployed to production.

Migration v3 preserves v1/v2 data and adds deployments, unique address reservations,
and a durable peer outbox. Stage checks registration/key/entitlement and queues every
candidate. Publication requires all peers confirmed; `--peers-ready` has been removed.

```sh
python -m control.product.admin --database state-product/product.db migrate
python -m control.product.admin --database state-product/product.db stage-peers DEVICE_IDENTITY --network network.json --lease-seconds 3600
python -m control.product.admin --database state-product/product.db reconcile-peers --gateways gateways.json
python -m control.product.admin --database state-product/product.db peer-status
python -m control.product.admin --database state-product/product.db publish-provisioning DEVICE_IDENTITY --network network.json --key-directory state-product/signing --lease-seconds 3600
```

Use the [provider network format](provisioning-provider.en.md). The operator gateway
file maps candidate IDs to local Docker containers and their real host `/keys` source:

```json
{"be-1":{"container":"family-connect-pilot-gateway-1","keys":"/opt/family-connect/state-v2/wireguard"}}
```

This mapping never comes from a public API. The adapter verifies the mount, WG public
key, port, and startup/helper support. Build the current `pilot/Dockerfile`, including
`family-connect-peer-sync`; old images fail before mutations. Peer installation does
not prove public endpoint reachability or a client handshake.

The pilot adapter supports `10.77.0.4–254/32` and optional corresponding
`fd77:92::<number>/128`. Static Android/Linux peers and unmanaged dynamic peers are
preserved. Key/address conflicts and unsafe files fail closed. Device topology is
immutable after staging; address/gateway changes require a separate migration.
Reservations are not automatically reused after revoke. Restaging the same network
renews its lease and requires fresh reconciliation before publication.

Device/entitlement revocation atomically queues desired removal. The worker also
checks entitlement/deployment expiry and key revocation. It rechecks actual state on
each pass, repairing drift and retrying removals. Failures store only
`GATEWAY_UNAVAILABLE`, attempts and retry time, with 2–300 second backoff.
`desired=absent` is pending intent; `applied=absent` is confirmed removal. An unreachable
gateway cannot yet be considered physically revoked.

The host atomically persists/removes `peers/product-IDENTITY.conf` before syncing WG.
The in-container helper takes the same filesystem lock and rereads current intent.
A Docker command finishing after timeout cannot replay an old install after that file
has been removed. Crashes between persistence, WG and database acknowledgement can be
retried. Gateway `/keys` may be read-only; the host writes its source directory.
Restart loads only remaining peer files, so completed removals stay removed.

A product write transaction serializes each external operation with revoke. Each
Docker call has a three-second timeout; host file locking is nonblocking. API requests
may receive SQLite 503 while reconciliation holds the writer lock. Use bounded client
backoff. Multiple control hosts/distributed worker leases are not supported.

The signed client cache may remain valid through its lease, but a removed peer no
longer carries gateway traffic. Stopped workers or unavailable Docker delay removal.
Stopping a worker does not revoke existing peers. After recovery, reconcile and inspect
the queue before opening the product API. Old database/peer backups can resurrect
revoked grants; restore only while stopped and reconcile authorization first.

Systemd templates in `deploy/systemd/` run after boot and every 15 seconds after the
previous pass, with a 60-second service timeout. Adapt `/opt/family-connect` and `.venv`.
`/etc/family-connect/product.env` defines absolute `FC_PRODUCT_DB` and `FC_GATEWAYS` paths.
The default service UID is root; whichever UID is selected must own private 0700
storage/0600 files and have Docker access. Do not expose Docker to the public HTTP
process. Templates have not been installed or started.

Rollback means stopping the timer and product API while preserving v3 data and deciding
how to handle existing peers. Do not downgrade the schema. Migrated v2 envelopes without
managed deployments are no longer delivered. Manually installed v2 peers are not silently
adopted; they require reviewed operator migration during controlled maintenance.

Tests cover staging/publication gates, all candidates, restart, revoke/install races,
crashes, drift, independent revocation, expiry, retries and unmanaged/file protections.
`python -m scripts.test_product_gateway` explicitly runs real WG install/remove/restart
and delayed-command checks in a disposable Docker NET_ADMIN namespace without networking,
published ports or host routes. Default image:
`family-connect-wireguard:reconciliation-test`, override with `FC_GATEWAY_TEST_IMAGE`.
It does not test production traffic or native VPN applications.

The reconcile-peers CLI returns exit code 1 while jobs remain unconfirmed or failed, including backoff; peer-status provides details.
