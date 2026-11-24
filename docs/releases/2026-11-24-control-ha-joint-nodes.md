# 24 November 2026 — joint canonical and receiver recovery

## Actual execution — 09:57:21UTC

Execution source `0cddf92d676f3f24ef2543224368aa44b63d2b63` was committed, pushed and
remote-SHA verified before qualification. Actual execution completes
2026-11-24T09:57:21.170135Z using the unchanged07:22 canonical610-row point and the
separate08:10 three-node capsules, not a fresh live or coherently fenced checkpoint.

- All69 canonical identities match each receiver:207 PostgreSQL-derived decisions are
  field-for-field equal at their original timestamps. All82 allocated peers resolve to
  those bindings. RU/NL1/NL2 retain20/55/7 peers and sequence floors20/55/8 respectively;
  the next private NL2 allocation is9, not8.
- Fresh PostgreSQL17.11 restore matches every table and repeats the same207 decisions.
  The native safety checks preserve207 duplicates,12 terminal denials and3 paid
  expiry/reboot checks. No cached deadline is refreshed by the parity comparison.
- One existing identity is revoked **only on the isolated PG copy** through the native
  API. Each scratch receiver accepts its denial, preserves duplicate state, remains
  denied after reconstruction and rejects the older allow even with a refreshed timestamp.
  These three checks repeat after a fresh post-ACK PG restore: six denial readbacks total.
  The pre-revocation dump and old canonical import are refused against the new ACK.
- Original encrypted node capsules and all three OWNER container observations remain
  unchanged. All four owned actual-run PG containers/volumes are removed. No SSH, live
  service changes, real gateway command, public release or installed version change occurs.

Joint fingerprint: `05c971d5fb0c77e6c6549316159cd11bf1952f1a9b0b9974a5e6ea15e90bbfd3`.
Private before-ACK dump SHA256:
`e14d053abda04c0c24146bb76218f970d1afde5d64b0be48ee1ef0f2d5bb3a0b`;
after-ACK dump SHA256:
`a29fc71c75c6e0c7ba0531fccfd5bae7fa7486d0bd66cf9b6fc99324b70eb49a`.
Execution receipt SHA256:
`bba31769e3fbfaa7079f30c2941ecb12540a6ca852b4ff1c23e50d132caed3de`.
Private locator: `/tmp/fc-control-ha-20261124/joint-nodes/actual-location.json`.
The original durable capsules/keys remain in owner-private custody; lab dumps are not
production rollback images.109 focused real-PG tests pass without skips.

This closes the retained canonical/three-node native integration gap, not the remaining
worker/OWNER joint recovery, coherent all-writer/dispatcher capture, machine-loss source/
image dependencies or independent forward trust. HA-02 remains IN_PROGRESS.

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

Actual retained-input qualification was pending at the preparation checkpoint and now
passes09:57:21UTC above. The
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
