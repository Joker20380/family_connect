# HMAC generation cutover / Смена поколения псевдонимов

**Preparation only. No production key switch is authorized by this document.**
Scope: the pseudonymization key, NOT device identity, chat/store encryption,
payment credentials, VPN keys or Android signing. PR38 metadata delivery remains
separately gated. [Rehearsal receipt](../releases/2026-11-15-hmac-migration-rehearsal.md).

## Mechanism / Механизм

Generation2 derives full device HMACs and separate `event:` panel-event HMACs.
The protected alias manifest binds these to opaque internal entities and existing
storage handles. Historical handles are NOT represented as fresh generation2 HMACs.
They intentionally remain in existing URLs/rows; rotation cannot erase links already
visible in historical evidence. No snapshot, audit JSON or digest is rewritten.
No immutability trigger is disabled. Canonical notification event IDs are untouched.

Only authenticated operator/forced-command streams carry the generation envelope.
`FC_PSEUDONYM_ALIASES` is an absolute private, read-only manifest path on operator
collectors, panel importers and the support owner. The RU publisher/helper use
`friends-access/pseudonym-aliases.json`. The manifest must match across consumers.
Generation, channel, manifest digest and producer key check must agree. Bare legacy
streams are rejected by activated collectors/importers. An interrupted distribution
therefore stops import, not duplicate contacts or resets of stored history/cursors.

Existing pseudonyms resolve only by exact manifest entries. A genuinely new entity
has its current full HMAC as its stable handle; the trusted producer explicitly
declares such self-mappings in `new_entities`. That declaration cannot alias an
unknown value to an existing handle. Support additionally rejects any new handle
for an already pinned canonical device/public identity. Missing historical inputs
remain `legacy_unresolved`, never inferred by names, prefixes, IP or phone models.
Missing active/pending references block switching. Ordinary operation after cutover
uses only the new HMAC key and saved aliases; the old key is not mounted in either
isolated steady-state rehearsal.

## Preparation / Подготовка

1. Verify current installed hashes against `deploy/support-chat/pseudonym-baseline.json`.
   The observed publisher is the filesystem module loaded by RU **chat-sync**,
   not just the HTTP archive. Operator `inventory-hmac.key` and RU
   `support-inventory-hmac.key` were compared inside a process: equal.
2. Take online SQLite backups and a transaction-consistent PostgreSQL dump; retain
   encrypted off-host backups and verify restore with no external network. These
   individual snapshots are not a global write freeze. At cutover repeat the delta
   under the bounded pause below. Never use old counts as today's expected state.
3. Generate a private32-byte replacement once, mode0600, using OS randomness. Do
   not print it, put it in argv, CI or Git. Keep original backups and the candidate
   manifest in the protected operator area; publish only aggregate coverage.
4. Run `python -m scripts.prepare_pseudonym_migration` with explicit private paths:
   `--registry`, `--old-key`, `--new-key`, `--references`, `--output`, `--report`.
   Inputs are consistent **copies**, not live writable databases. The canonical
   event query has no1000-row limit. Reference groups carry counts and criticality.
   Reruns preserve entities/handles and incorporate exact canonical deltas. This
   command never installs keys, switches a process or authorizes cutover.
5. Build `scripts.package_pseudonym_migration` from the audited eight-file baseline.
   It checks every source SHA, applies the bounded delta, adds the alias module,
   and compiles the result. No HTTP/paid/reconciler/VPN archive is replaced.
   For the panel, overlay ONLY two importer commands and the alias module on the
   accepted image. Existing volumes/users/passwords/commands remain unchanged.
6. Run `scripts.rehearse_pseudonym_support` and `scripts.rehearse_pseudonym_panel`
   on isolated restored copies. Both refuse a namespace with a non-loopback network
   interface. Mount no old HMAC key. Retain receipts for replay, restart, card/event
   deduplication and partial activation rejection, plus synthetic pending/ACK tests.

## Proposed production switch / Предлагаемый порядок

**Requires a separate owner confirmation referencing the qualified receipt/source.**

1. Refresh installed-source/image/key-copy equality checks and free-space checks.
   Confirm scope still matches the receipt. Obtain fresh encrypted backups and
   preflight restorations. Do not continue after unexpected runtime drift.
2. Enter a short support maintenance window: stop scheduling the local user
   `family-connect-readonly-monitor.timer`; wait for its active collection and
   import/monitor lock to finish. Stop scheduling local system
   `family-connect-support-bindings.timer` and
   `family-connect-subscription-notifications.timer`; wait for active oneshots.
   Block new support-send IPC while draining `family-connect-support.service`
   with its normal SIGTERM/40-second stop budget. Abort on incomplete drain;
   never kill a sender to force the switch. Existing outbox/requests remain saved.
3. Pause RU `family-connect-chat-sync.timer` and wait for its current oneshot to
   finish. Do NOT stop VPN, AWG, TCP, MESH, HTTP admission or paid reconciliation.
   Do not reset subscription baseline/cursor. Chat binding leases may temporarily
   expire; do not extend an old lease to hide the maintenance window.
4. Capture the final canonical/support/panel delta and full reference coverage.
   Include latest active inventory, labels/audit references, every stored snapshot,
   event domain, pinned contacts, requests and jobs. Rebuild with the SAME candidate
   key, retaining mappings. Check stored/mapped/missing/conflicts; unknown active
   or pending correspondence aborts the switch. New canonical operations arriving
   after this frontier remain new operations, not a baseline rebuild.
5. Stage the same manifest in each protected consumer location with appropriate
   owner and0600 permissions. Install the minimal source overlay and private
   manifest-path configuration. Stage the new key on the operator and RU, without
   printing/transmitting it in argv. Swap the two key files atomically while their
   consumers remain stopped. Verify generation/key checks in-process at both ends.
   Replace only the console image with the qualified overlay and read-only alias
   mount/env; preserve its volumes and publisher container. No schema migration is
   required for HMAC rotation. Metadata migrations are a separate PR38 delivery.
6. Refresh RU chat-sync once to create a new acknowledged generation-bound lease;
   read it through the existing pinned forced-command SSH path. Validate/normalize
   it into the existing support projection path. Start the support owner, verify
   pins/block flags/requests/outbox/baseline/cursor unchanged, and read its cursor.
   Fetch the next notification page with that original cursor/anchor. Do not send
   a probe message, create a payment, alter an expiry or generate a new baseline.
7. Run one read-only inventory/import cycle. Check one existing card, all event
   counts/digests, and absence of duplicate identity/contact/notification jobs.
   Re-enable the existing timers only after all checks agree. New genuine events
   can then resume normal processing; old excluded history stays excluded.

## Recovery / Восстановление без потери новых данных

If distribution stops between consumers, leave automatic collection/publication
paused, retain both databases, the new key and the same candidate manifest, and
finish the missing consumer installation. A wrong/missing manifest must fail closed.
Re-run the same normalization/import: stable handles and event IDs deduplicate.
After new-generation work has begun, roll back only to a compatible alias-aware
code/image build or fix forward. Retain all newly created requests/messages/jobs,
generation2 key and aliases. Never restore an old database over current events,
never automatically reactivate the disclosed key, and never remove the replay or
identity block checks. The isolated rehearsal tests restart and repeated replay.

English operational summary: drain the collectors/sender, pause only the HMAC
publisher, reconcile the final full delta, install matching aliases and new keys,
refresh verified projections, resume with the original cursor, then re-enable
timers. Preserve the new key/data on recovery. No VPN restart or historical send.
