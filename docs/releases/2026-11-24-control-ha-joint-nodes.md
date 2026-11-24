# 24 November 2026 — joint canonical and receiver recovery

## Preparation

Selected task: CONTROL-HA-20261123 / HA-02. Dependencies are the authenticated installed
canonical point, all three authenticated node capsules and their native-format checks.
This is an offline integration qualification, not HA-03 fencing or production activation.
The canonical-only recovery already passes; it is not being counted as a new completion.

`scripts/control_ha_joint_nodes.py` binds the canonical fingerprint and all three exact
capsule checkpoints into a joint fingerprint. Authentication, installed source pins and
native receiver/allocator validation run before comparison. Missing/extra/swapped nodes,
changed keys/source/pins or incomplete device coverage refuse qualification. Keys, rows,
device identifiers and cached envelopes never enter the aggregate receipt or Git.

The native policy reader must reproduce every field of every retained decision from the
imported PostgreSQL database at that decision's ORIGINAL timestamp, including WG/TCP
bindings, paid revision/state/deadlines, invitation/revocation and lease boundaries.
This does not refresh a lease or claim the earlier canonical point and later receiver
points were captured under one barrier. Allocated peers must resolve through these exact
decisions; allocator sequence gaps stay intact. Installed `external` settings remain
interface names, not the legacy adapter's public-host assumption.

The owned PostgreSQL17.11 lab imports the canonical state, checks all three receivers,
dumps/restores into a fresh target and repeats parity. Native receiver checks preserve
duplicates, terminal denials, paid expiry/reboot denial and allocator next-ID behavior.
One existing identity is revoked through the native enrollment API **only in the lab**.
All three scratch receivers ingest its PostgreSQL-derived denial; duplicate delivery,
receiver reconstruction and an old allow envelope with a refreshed timestamp cannot
remove it. A fresh post-ACK PostgreSQL restore repeats those denial checks; the old
dump and old canonical import are refused against the acknowledged revocation.

The receiver uses reviewed, installed-safety-AST-matched code and forbids all gateway
commands. No SSH, Docker exec into production, transport reconciliation or network
dispatcher is called. Scratch caches are independent copies; original capsule bytes,
allocator stores and server/runtime volumes stay untouched.

## Checks

109 focused real-PG contracts pass with zero failures/errors/skips:

- `tests/test_control_ha_joint_nodes.py`: authenticated coverage, SQLite/PG native parity,
  individually valid binding/revision/expiry/identity/lease drift, provenance changes,
  new revocation delivery, restart and terminal replay refusal.
- Existing installed-composite and node-custody contracts remain passing.
- Native transport-enforcement and membership regression contracts remain passing.

The initial unconnected run exposed a fixture selecting an unpaid row for the paid-deadline
mutation; the fixture now selects an active paid identity explicitly. One subsequent test
invocation named nonexistent files and executed no tests; it is not acceptance evidence.
The corrected real-PG run above is the accepted result.

The full fixture qualification also passes:12 decisions across three receivers, sequence
gaps preserved, fresh PG parity, one acknowledged laboratory revocation, six receiver
denial readbacks before/after PG restore, and refusal of stale restore/old import. All
owned fixture containers/volumes are removed. This is synthetic evidence, not actual input.

Actual retained-input qualification is pending at this preparation checkpoint. The
preliminary read-only SQLite comparison finds69 canonical identities on every node,
207 exact cached decisions and82 allocated peers, but is not the PG recovery result.

## Recovery and rollback boundary

This changes safe source/tests/docs only; installed, built, distributed and invitation-page
versions do not change. No deployment, catalog/signature change or live service restart.
Owned lab containers use new loopback-only PG ports, independent random schemas/passwords
and ownership-checked cleanup; native scratch receivers have no command dispatcher.
On failure, retain private logs/dumps, remove only owned containers/volumes, and do not
activate any output. Source rollback is an ordinary revert; no production rollback is needed.
The lab dumps are private qualification evidence, not a jointly fenced production backup.

Passing this slice closes the canonical-to-three-receiver comparison/revocation gap only.
Worker/OWNER integration, a coherent all-writer/in-flight-dispatcher snapshot, complete
machine-loss source/image custody and independently approved forward trust remain open.
The separate replication gate already passes. HA-02 is not COMPLETE, and RU independence
still requires the later authorized deployment stages; no cutover is selected here.
