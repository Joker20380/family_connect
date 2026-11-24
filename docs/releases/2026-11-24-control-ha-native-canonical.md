# 24 November 2026 — installed native canonical recovery

## Actual execution — 09:37:05UTC

Capture/import source `723e90eff7ab9bec27e08caed58cb23e7f55049a` was committed, pushed and
remote-SHA verified before execution. The previously retained07:22:17UTC encrypted inputs
authenticate using their separately held checkpoints/keys.16 exact external files bind to
the canonical610 rows. Native checks preserve66 mapped plus3 explicit new devices and4
mapped paid-event identities;20 referral links and63 claims verify with the retained secret.
No alias/key/grant is regenerated and metadata observations remain absent.

Actual PostgreSQL17.11 execution completes2026-11-24T09:37:05.192441Z:

- All610 source rows import exactly:34 original SQLite tables become35 import data tables
  including the new empty CRL outbox;49 target tables contain624 rows including schema/import
  markers. All five retained handoff tables survive unchanged and remain read-only.
- Killing only the owned lab PG with an uncommitted revocation transaction, then restarting
  it, preserves the original committed snapshot. Exact retry and fresh-target restore pass.
- The single paid subscription in this canonical point denies access after expiry. This is
  not the separate OWNER synthetic store's three subscriptions.
- One new laboratory identity is activated through the native enrollment API on the restored
  copy. Fresh post-ACK restore matches every table and refuses reuse of the consumed proof.
  The older dump is rejected against the newer acknowledged state; replaying the old import
  into the newer recovered DB is also rejected. No real device receives an invitation/profile.
- All owned lab containers/volumes are removed. Existing OWNER console/PG/publisher IDs,
  images/configuration/mounts/start observations remain unchanged; no SSH/server operation,
  production write, dispatch, migration, public release or installed version change occurs.

Input fingerprint: `a9dbb613b076acf07903abdf9d39ab6561431efffe15fe963e063931055725d1`.
Private before-ACK dump SHA256:
`3cc4f53d4e092da042c6f37c9b87d29d8f4aee2ee3d052610be8133a540271f6`;
private after-ACK dump SHA256:
`1daca4bc6e080f1a339267f008b59fceecade6e93e7813a3cce707bf41938e8e`.
Execution receipt SHA256:
`ef0ffe3ab8222668143b49b2b90688b0eaae8afd6a722e4cebc6fdfba6518331`.
Private evidence locator: `/tmp/fc-control-ha-20261124/canonical-native/actual-location.json`;
the original durable encrypted capsules stay under owner-private `control-ha/20261124-external-01`.
The lab dumps are qualification evidence, not a jointly fenced production rollback image.

249 focused real-PG contracts pass,0 failures/errors/skips. No historical whole-suite rerun
or optional-test skip substitutes for this gate. This closes the old native canonical format
blocker and qualifies actual-data PG recovery after a laboratory ACK, not full fleet DR or
independent current-checkpoint authorization. HA-02 remains IN_PROGRESS; see the boundary below.

## Scope and preparation

Selected work remains CONTROL-HA-20261123 / HA-02, not a deployment or HA-03..05.
The next native integration gap is concrete: the old external-v1 alias adapter requires
every canonical entity to have a migration mapping. The installed native protocol also
accepts explicit new entities. The retained actual point contains66 mapped devices plus
3 new devices and4 mapped paid-event identities. Inventing old handles, replacing aliases
or silently relaxing the old adapter would be incorrect.

`scripts/control_ha_installed_composite.py` introduces a separate offline installed profile.
It binds every input byte to the caller's authenticated custody pins, uses the existing
strict installed34-table SQLite/handoff schema adapter, and preserves all610 source rows
(35 import data tables including the new empty CRL-outbox table). Minimal native subscription
envelopes exercise `seal`/`unseal`: migrated identities resolve to their original handles,
new identities stay explicitly declared, and the stored alias document never changes.
The legacy external-v1 adapter and its full-coverage rejection remain unchanged.

The profile also validates native v2 `all_activated` admission WITHOUT enrolling anyone,
the original PEM Ed25519 issuer key against its delegated certificate, CRL/certificate
bindings at capture time, referral links/claims against the preserved secret, support sender
and signed routing/history. Metadata retains consent floors with empty observations only.
The exact selected file digests and adapter identity enter the canonical import fingerprint.
Derived external reference documents are bookkeeping, NOT independent authorization or
proof that receiver/worker/OWNER state shares the canonical capture point.

## Isolated execution and rollback

The actual input is the already authenticated07:22:17UTC custody point under owner-private
`control-ha/20261124-external-01`, with separate key/checkpoints in `control-ha-keys`.
No new SSH/live DB capture, service stop/start, migration, gateway command, publisher call,
or production write is part of this task. Validation uses that point's capture timestamp;
it does not extend old certificates or establish that the retained credentials are current now.

`scripts/control_ha_installed_rehearsal.py` accepts only the prepared snapshot and creates
owned disposable pinned PostgreSQL17.11 containers through the existing rehearsal helper.
The target is a new randomly named synthetic schema on an ephemeral localhost-only port,
with a fresh private test password and no original volume/production credential mount.
All source keys and decrypted records stay outside Git/CI/output; PG dump/log evidence is
private. No maintenance or handoff operation is resumed; handoff rows stay read-only.

Checks: exact import/retry, kill/restart with an UNCOMMITTED revocation transaction, exact
fresh-target dump restore, native paid expiry denial, then ONE newly generated laboratory
device activation/ACK. A later fresh restore must preserve the ACK and refuse proof replay;
the older dump must fail comparison against the acknowledged state, and importing the old
snapshot into the newer restored database must fail. The new identity is laboratory-only,
never a product registration or a gateway publication.

Abort on any pin/schema/key/reference/table mismatch, unexpected exception or ownership
failure. Cleanup removes only helper-owned labelled lab containers/volumes. Rollback requires
no production operation: the retained original capsules and separate checkpoints are unchanged.
Keep private evidence on failure; do not overwrite live authority with a lab dump.

## Preparation checks

249 focused native/installed/handoff/legacy SQLite/import/external-role tests pass against
owned PostgreSQL,0 failures/skips. A separate76-row fixture passes49-table import, crash
rollback, fresh restore, new laboratory ACK, stale-copy rejection, consumed-proof rejection
and old-import refusal after ACK. All owned fixture containers/volumes are removed.
The actual retained610-row in-memory preflight also passes. Actual PG execution subsequently
passes09:37:05UTC above; it is no longer pending. Installed/public/invitation versions remain unchanged.

## Acceptance boundary

Even after this bounded canonical import passes, HA-02 needs joint native receiver/worker/
OWNER integration, coherent all-writer/dispatcher capture, complete machine-loss source/
image dependencies and independent forward-checkpoint trust. Distinct local custody points
do not become a coherent fleet snapshot merely by importing their canonical DB into PG.
