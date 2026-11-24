# 24 November 2026 — canonical / OWNER / legacy integration

## Actual execution — 11:10:32UTC

Result `ACTUAL_OWNER_CANONICAL_LEGACY_JOINT_PASS`; execution source
`8b4198033a3062160d5e0263517bbc68f076a50b` was pushed and remote-SHA verified before the run.
The native canonical PG projection was prepared on pushed source
`16daed94e147959a0f0afec812ae89776902c6b8`; its generating module is byte-identical at execution.
This uses the retained07:22 canonical,07:38 OWNER PG,08:43 worker and09:17 OWNER runtime
points, not a new live or coherent fleet snapshot.

- All37 retained-data fingerprints match the authenticated OWNER capsule:1,907,455 rows.
  The native39-table schema restores with only3 metadata consent floors; no observations,
  GeoIP or source-projection rows are restored. The baseline readback is independently
  retained as private LAB evidence, not an actual forward authorization.
- The pinned native panel image decodes the canonical aliases and accepts69 devices/4 paid
  history events. Exactly two tables change: `console_subscriptionsnapshot` gains one
  snapshot and `console_auditrecord` records it. Existing event observations and all other
  tables remain unchanged.50 synthetic and4 legacy key identities remain separate, as do
  the3 distinct legacy outbox target keys. No demo/legacy device is merged into canonical.
- Duplicate ingestion preserves the same snapshot and all39 fingerprints. A wrong alias
  generation and conflicting paid history are rejected without changing any table.
- A new private post-ACK dump is restored into a fresh database on the owned network-none
  PG instance. Native readback matches every post-ACK table fingerprint and repeats the
  duplicate/refusal checks. Restoring the pre-ACK dump is distinguished and refused against
  that retained LAB readback. This does not authorize a production rollback or import.
- Native legacy-worker qualification on its separate copy preserves retry/restart/duplicate
  behavior and refuses all3 expired deployments, with0 real gateway commands. It is not an
  external in-flight Docker-command fence and does not qualify every OWNER write path.
- 103 focused real-PG tests PASS,0 failures/errors/skips. The two earlier refusal attempts
  below are not counted as passes. Their owned resources and the final probe/PG/volume are
  removed; original OWNER container identities/images/start times/configuration and source
  capsules remain unchanged. No SSH, production write, default startup/migration, publisher,
  service restart, installed/public/invitation version or policy change occurs.

Sanitized hashes; raw receipts, dump rows, identifiers, aliases, HMAC and credentials stay
in private local custody, not Git or CI:

| Evidence | SHA256 |
| --- | --- |
| Retained encrypted OWNER PG capsule | `28bbb64de3907a1cf1949f1d20a04c63c3dcee94c0aef68cebf58611d5e240d1` |
| Verified pre-ACK dump | `6fc6035e6e271215c8af718ee9fdf372bece0f02e945b6ffc6fb33d8c46b0961` |
| Post-ACK dump | `3a400721b90b7339e91e1ea62e99173072b6025a1f69cad08beb4d0aeeb6e7ec` |
| Canonical native projection | `f619d6be431bd54de791cdb197579439706a7ac8d0fc733fa8dad6928f69e46a` |
| Actual execution receipt | `0834c16bde2dffb751434d2feebf855dee17651fa8d92216bac95b07f531561f` |

HA-02 remains IN_PROGRESS. This closes the selected panel-projection/namespace integration
gap, not current independent trust, coherent all-writer capture or full machine-loss recovery.

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
Namespaces remain separate, not migrated. Actual joint execution was pending at preparation;
the completed result is recorded above.

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

The next actual attempt restores the full PG archive and verifies all39 table fingerprints
after restoring only three consent floors. Its native ingestion probe then reaches the300s
lab deadline: two complete scans of1,907,455 rows already take220.4s at the explicit1-CPU
lab limit; the ingestion/readback probes each require four scans. No ingestion/recovery
PASS is claimed from this attempt. The owned probe/PG/volume are removed automatically.
The bounded probe deadline is now900s, with all table checks,1-CPU/memory limits and
production isolation unchanged. Regression tests require owned-probe cleanup on timeout
in every mode. The already verified pre-ACK dump is private restart evidence, not a new
production checkpoint; a continuation must verify its39 fingerprints before ingestion.

## Fixed remainder of stage 2

The four acceptance blocks have NOT increased. Replication is PASS; three remain partial:

1. **Inputs/trust:** define/review the actual approval-authority registration and offline
   owner-signing workflow, then independently approve/bind the final CURRENT checkpoint,
   retained pins and monotonic floors. Existing historical capsules, backdated approval
   and a self-generated lab signature cannot do this; it is not just one missing signature.
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
