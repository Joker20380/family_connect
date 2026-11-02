# Multi-node operator observability — 3 November 2026

## Scope and current gate

FLEET-BOOTSTRAP-2 continues autonomously at the owner's request. Interactive owner
AWG/TCP/Disconnect checks on Linux .13 are DEFERRED_TO_FIELD, not PASS and not a
development prerequisite. Future user feedback does not imply forced updates,
enrollment, paid events or automatic switching of existing sessions.

Selected step: source-bound observation of the three current operational endpoints
before recovery policy. This is not automatic failover, independent recovery,
second-node MESH, production-console exposure or client release work.

**SOURCE_AND_READ_ONLY_COLLECTION_PASS; local console rollout pending.**
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
report IMPORT_FAILED because the local console stack is stopped. This is the next
bounded rollout step, not a request for owner VPN testing. Private snapshots,
receipts, pinned-host file and diagnostic logs stay outside Git.

## Remaining work and rollback

Finish the local loopback-only console rebuild/start with retained local state,
then verify exact source identity in all three imported snapshots and archive-only
legacy history. No public hosting, remote backend restart or user connection test.

For observer rollback: stop only the local read-only timer, preserve receipts,
remove only this task's user-service drop-in and review current approved targets
before resuming. Do not silently restart polling of the retired source. No client,
production database, VPN service or signed-catalog rollback is needed for this step.
Field acceptance and independent recovery remain unproven; no second task starts
automatically from this checkpoint.
