# Multi-node operator observability — 3 November 2026

## Scope and current gate

FLEET-BOOTSTRAP-2 continues autonomously at the owner's request. Interactive owner
AWG/TCP/Disconnect checks on Linux .13 are DEFERRED_TO_FIELD, not PASS and not a
development prerequisite. Future user feedback does not imply forced updates,
enrollment, paid events or automatic switching of existing sessions.

Selected step: source-bound observation of the three current operational endpoints
before recovery policy. This is not automatic failover, independent recovery,
second-node MESH, production-console exposure or client release work.

**LOCAL_THREE_SOURCE_OBSERVABILITY_PASS.**
The old collector knew only RU and obsolete gateway-nl186.246.45.246. It now has
one shared source catalog for RU185.251.89.19, AMS1 185.10.158.212 and AMS2
185.10.158.196. Legacy gateway-nl remains importable/readable history with no live
poll target; it is never renamed or used to fill either new node's missing data.

## Changes and safeguards

- Every current node gets a distinct card, source filter and history. Missing,
  stale (>5min), future (>15s), unknown and non-active required services stay
  distinct from an observed active service set. Active systemd is explicitly not
  end-to-end VPN acceptance; no automated action consumes these observations.
- The two NL collectors do not open the user registry or create/transmit an HMAC
  key. Their registry_status is not_collected, with no device rows. The importer
  rejects NL device/registry payloads. RU pseudonymization and access boundaries
  remain unchanged; no raw IDs, keys, profiles or paid tables are exported.
- A failed collection/import never borrows another node's sample or aborts the
  next source. Strict SSH host checking remains mandatory. An optional existing
  known-hosts file supports already-approved pins; trust is not learned on failure.
- Local timer budget is380s for three bounded collection/import pairs. The build
  context now includes the allowlisted fleet runtime/resources already required
  by the Dockerfile; state, binaries and credentials remain excluded.
- No schema migration, client version, signed catalog, invitation, assignment or
  server VPN/backend configuration changes. Installed Linux stays0.2.12~l03.2.13;
  public Linux0.2.11, Android110/catalog5 and Windows0.2.16/catalog12 unchanged.

## Automated checks

- 30 operator/collector/state/packaging tests PASS, including wrong-source binding,
  one-node timeout isolation, no registry/key use on NL, missing/stale/future/failed
  state handling, preserved archive identity and safe source context.
- 45 targeted Django observability tests PASS, a subset of162 full console tests
  PASS. Separate real PostgreSQL17 database, internal Docker network, temporary
  credentials and source-only read-only mount; no workstation/product state mounted.
  Exact control-plane dependency-lock digest matches the reused image. Django check
  and makemigrations --check --dry-run PASS, no migration.
- Both real NL endpoints returned independently bound read-only snapshots with
  AWG, TCP and monitoring services active; no registry/device collection. These
  observations do not prove a user tunnel, automatic recovery or long-duration health.
- First disposable-test attempt did not start: missing mountpoint for tmpfs under
  a read-only source mount. Added the empty mountpoint to the test harness; retained
  initial log, rerun PASS. No product/test guard weakened.

## Local rollout and retained outcomes

The existing workstation monitor timer executes the checked-out source. An early
cycle therefore attempted the new targets before local rollout: RU/AMS1 collection
succeeded but local import failed; AMS2 initially lacked its pin in the default
known-hosts file. This result is retained, not reported as no production interaction.
Only the local read-only timer was paused for controlled checks; no remote service
was stopped/restarted. Existing approved standard RU/AMS1 pins and the retained
AMS2 RSA pin were copied into a private local observer known-hosts file. No network
key discovery or new trust approval was used.

A local user-service drop-in selects those pins and380s timeout; prior unit retained
privately, timer restored. All three collections now succeed, but their imports
initially reported IMPORT_FAILED because the local console stack was stopped.
That failure is retained and resolved by the local rollout below. Private snapshots,
receipts, pinned-host file and diagnostic logs stay outside Git.

The loopback console was rebuilt from source
`c95cc86aa5d507b17aac5ae70325420e68153f83` with the corrected allowlisted fleet
build context. Previous context and a private local PostgreSQL dump retained;
existing .env is byte-identical and named data volumes retained, no volume reset.
Local payment/operation/device counts are unchanged across the import cycle.
Image `sha256:0862dbdbb9a0f9d545cb4c71d2990f83cfe1126b1967078509e9f8f06b81c2fe`:
all177 packaged source/lock hashes match the build manifest; changed runtime files
also match in the running container. Health returns synthetic/ok; the only published
binding is127.0.0.1:8765. No admin credential, role override or public exposure added.

Final readback: RU, AMS1 and AMS2 have independent fresh imported snapshots and
observed-active required services. NL registry collection remains disabled. Retained
gateway-nl is archive-only. The existing one-minute local timer is active, with
three-source imports successful; no production write/VPN/backend restart occurred.
This is operator observability, not a connection/throughput/automatic-recovery PASS.

Verification failures are retained: the first readback wrapper had a syntax error;
while the timer was paused, later snapshots correctly became stale and the gate
refused them. Restored normal fresh collection, without relaxing the5-minute bound.
The runtime's /tmp tmpfs hid the image's dependency lock during a full-file audit;
the read-only/network-none image audit verified that lock and all source hashes
without changing package bytes. These were verification-context repairs, not new
product releases. New docs links/whitespace PASS; the broader docs check retains the
pre-existing STATUS historical anchor error for27 October, unchanged by this task.

[Sanitized receipt](2026-11-03-fleet-observability.receipt.json).

## Remaining work and rollback

The local observability gate is complete. Independent readiness probes and a bounded
recovery policy are the next candidate; these source observations alone must never
authorize automatic endpoint reassignment. Field acceptance remains deferred.

For observer rollback: stop only the local read-only timer, preserve receipts,
remove only this task's user-service drop-in and review current approved targets
before resuming. Do not silently restart polling of the retired source. No client,
production database, VPN service or signed-catalog rollback is needed for this step.
For local-console rollback, stop only its console service and keep PostgreSQL/data
volumes/.env and backups; do not use down -v or automatically restore a database.
The prior source context and private local PG dump remain available for a separately
bounded restore if required. No such rollback was needed for the successful rollout.
Field acceptance and independent recovery remain unproven; no second task starts
automatically from this checkpoint.
