# 24 November 2026 — installed native canonical recovery

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
The actual retained610-row in-memory preflight also passes; actual PG execution is the next
action, not yet a PASS. Installed/public/invitation versions remain unchanged.

## Acceptance boundary

Even after this bounded canonical import passes, HA-02 needs joint native receiver/worker/
OWNER integration, coherent all-writer/dispatcher capture, complete machine-loss source/
image dependencies and independent forward-checkpoint trust. Distinct local custody points
do not become a coherent fleet snapshot merely by importing their canonical DB into PG.
