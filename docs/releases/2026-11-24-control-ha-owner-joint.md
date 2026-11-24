# 24 November 2026 — canonical / OWNER / legacy integration

## Preparation and acceptance boundary

Selected: CONTROL-HA-20261123 / HA-02. Dependencies are the completed native canonical,
node, OWNER database/runtime and legacy-worker custody checks. No HA-03..05, deployment,
new version, production restore or operator-intent replay is selected.

The read-only census establishes three DISTINCT namespaces:69 canonical devices,
50 OWNER synthetic devices and4 legacy transport-key identities. Neither identities nor
WG public keys intersect. The three distinct legacy outbox keys also do not target canonical
or synthetic devices. OWNER HMAC and aliases exactly match the retained canonical inputs.
This is important: merging the demo/legacy stores into the live registry would be wrong.

`scripts/control_ha_owner_joint.py` validates the cross-store boundaries, builds an offline
native subscription projection from SQLite or PostgreSQL, and authenticates the existing
encrypted OWNER PG archive. It rejects namespace collisions, alias/key drift, changed
checkpoints, unexpected archive members, observation-bearing floors and wrong source images.
The capsule contains37 retained-data tables,39 schemas and consent floors only; no GeoIP
or technical observations are reintroduced.

`scripts/control_ha_owner_joint_lab.py` starts only a uniquely labelled, pinned PostgreSQL
container and disposable volume. Its network is NONE, with no published ports; the native
console probe shares only this network namespace and reaches the owned PG over loopback.
Both containers are nonroot/read-only with dropped capabilities. Credentials are freshly
generated LAB values, not original deployment credentials. No original volume, Docker
socket, publisher, migration command, service restart or SSH is used.

`scripts/control_ha_owner_joint_probe.py` runs the installed pinned console image's real
alias decoder and subscription importer against the restored owner DB. The planned actual
gate checks all retained table hashes, restores only consent floors, ingests the canonical
projection, verifies duplicate/conflicting-history/wrong-generation refusal, preserves all
unrelated tables, then repeats after a new dump/restore. A pre-ACK copy must be distinguished
and refused against the independently retained LAB readback. This is not production trust.

The existing native legacy-worker replay/retry/expiry qualification runs only on a separate
private restored copy with in-memory adapters; no original or lab gateway command is issued.
Namespaces remain separate, not migrated. Actual joint execution is pending at preparation.

Preparation checks:98 focused real-PG tests PASS,0 failures/errors/skips (new archive,
projection parity, namespace collision and lab-boundary tests plus existing OWNER runtime,
legacy-worker custody and native canonical tests). The owned network-none PostgreSQL smoke
test passes empty-dump restore and removes its own container/volume. This is not the actual
OWNER database/native-import result.

The first actual attempt refuses before restoring data: `pg_isready` on the Unix socket
can report the entrypoint's temporary init server before the requested database exists.
Readiness now uses loopback TCP, which that temporary server does not listen on. A regression
test pins this distinction; the original OWNER containers remain untouched and the owned
failed-attempt resources are removed. This refusal is not a failed production restore.

## Fixed remainder of stage 2

The four acceptance blocks have NOT increased. Replication is PASS; three remain partial:

1. **Inputs/trust:** independently approve and bind the final CURRENT checkpoint/signing
   authority. Existing historical capsules and a self-generated lab signature cannot do this.
2. **Coherent capture:** close all-writer/in-flight dispatcher coverage, including the
   canonical/OWNER PG/synthetic pair. Separate successful snapshots are not one barrier.
3. **Complete recovery:** finish machine-loss source/image dependencies, then restore the
   complete final checkpoint and verify new acknowledged state/stale-copy refusal together.

Native component tests reduce risk inside these existing blocks; their count is not a
percentage or an ETA. There is no evidence-backed calendar completion estimate yet, and
HA-02 alone will not switch production management away from RU. Later cutover stays separate.

## Rollback

Installed/public/invitation versions and all live services stay unchanged. Stop only owned
lab resources after a failure; ownership/image/network labels must match before removal.
Keep private encrypted source capsules, separate keys/checkpoints and sanitized receipts.
Never restore a lab dump over production or treat a stale-copy test as an authorized rollback.
Source rollback is a normal revert; preserve other work and do not rewrite published history.
