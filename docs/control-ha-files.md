# HA-02N — file authority and writer inventory

## Scope and gate

23 November2026, source review from `f4c21afb`, after HA-02A–M synthetic DB
contracts. This is the selected remaining **source-level** file/CLI inventory,
not a production process census, migration, backup or authorization to switch.
No private files, server databases, keys, effective units or live host state were
read. Repository entrypoints do not prove which version a host executes.

Completion gate: distinguish authority from projections; trace the remaining
profile/alias/membership/catalog writers and callers; specify recovery inputs,
freeze boundaries and unresolved integration gates; test the two non-rebuildable
file families using synthetic inputs. The all-store importer and fenced
publication are separate next tasks, not implemented by this inventory.

[Storage contracts](control-ha-storage.md) · [Stages and rollback](control-ha.md) ·
[Evidence](releases/2026-11-23-control-ha.md#ha-02n--file-authority-inventory).

## Classification

“Not canonical control DB” does **not** mean “safe to delete and regenerate”.
Keep separate:

- **DB authority:** canonical identity, payment, revoke, proof, grant, observation,
  sequence and operation records covered by A–M; live stores are still separate.
- **Private file authority:** stable alias identities, admission/policy choices,
  credential/floor state and transaction journals not derivable from a DB dump.
- **Node-local durable state:** allocation and receiver safety state; not a second
  management master, but still required for safe recovery.
- **Derived expiring publication:** recomputable content only after authority,
  sequence/floors, receiver identity, current time and fenced writer are restored.
  Never make a stale file valid by extending its expiry or resetting its sequence.
- **Trust/configuration and secrets:** explicit external recovery inputs; do not
  import private keys into the canonical DB or put them in Git, CI or receipts.

## File and caller map

[HA-02U](control-ha-storage.md#ha-02u--online-renewal-evidence) checks a separate
single-operation online-renewal evidence format. It does not replace this caller
census, qualify installed histories/offline modes, or authorize host relocation.
[HA-02V](control-ha-storage.md#ha-02v--combined-online-renewal-capsule) binds this
completed-operation evidence to the canonical capsule/issuer/DB checkpoint.
The combined format explicitly declares renewal evidence on every bounded node;
it does not reinterpret T's empty-ledger declaration or change native HMAC journals.
The explicit history extension retains coordinator predecessors before replacement,
checks the matching full three-node archive/ledger set and preserves all original
bytes. It does not reconstruct missing legacy coordinator records or attest live
inventory completeness. The explicit [stopped variant adapter](control-ha-storage.md#completed-stopped-variants)
also binds one completed operator-approved stopped renewal, planned offline authority
handoff or completed online-emergency rollforward to the current capsule. Both NL
publication payloads and native parent archives are retained. Missing original approval
or signed handoff-envelope bytes are not reconstructed; these records cannot authorize
another outage. Mixed histories, expired-recovery/fenced rollback, service-bearing
installed archives and actual host reconciliation remain unqualified. No automatic
pruning, rebinding or host resume is authorized.

All paths below are source paths or relative logical artifacts, not an instruction
to read/copy a live directory. Scope includes callers outside `control/friends`.

| Family and entrypoints | Authority / side effect | Migration and recovery boundary |
| --- | --- | --- |
| [profile_store](../control/friends/profile_store.py): `Locator`, `ProfileStore.replace/transact`; [maintenance](../control/friends/restricted_maintenance.py): `CanonicalConfiguration`, `Operation`; [production_node](../deploy/friends/restricted/maintenance/production_node.py): `replace_profile` | Root-controlled profile, bindings, credentials and CRL floors; local lock/CAS; same-directory file+directory fsync. Locator and reader/publisher metadata bind the exact path. | Preserve accepted profile bytes, metadata, locator, current floors and operation evidence privately. Do not reconstruct a profile from grants or install an older profile after new writes. Shared `flock` is local, not distributed fencing. |
| [credential_renewal](../deploy/friends/restricted/maintenance/credential_renewal.py): `Controller`; [production_controller](../deploy/friends/restricted/maintenance/production_controller.py), [runtime_controller](../deploy/friends/restricted/maintenance/runtime_controller.py), [online_cli](../deploy/friends/restricted/maintenance/online_cli.py), [online_node](../deploy/friends/restricted/maintenance/online_node.py) | Private coordinator transaction/previous/candidate state, bounded permits and node recovery evidence. Bounded maintenance separately persists authenticated journal and before/target files. | Preserve incomplete operation state and matching configuration/keys; do not mark a pending or unknown operation APPLIED from DB rows alone. Quiesce all accepted renewal/maintenance entrypoints, not only HTTP. Recovery keys remain separate protected inputs; HA-03 replaces sole-host authority, not the existing journal with an empty one. |
| [pseudonyms](../control/friends/pseudonyms.py): `prepare/save`; [prepare_pseudonym_migration](../scripts/prepare_pseudonym_migration.py): `build/main` | `pseudonym-aliases.json` is **private authority**, not a disposable HMAC cache. Random entity IDs, historical handles, generations and aliases are persisted. The CLI reads consistent DB copies and writes a candidate, never activates consumers. | Retain the exact accepted manifest/digest and consumer generation; add deltas to it. Identical canonical rows plus even both HMAC keys do not recreate the same entity IDs/digest. Steady state uses the current key; do not resurrect or distribute the old key. Coordinate producer/importer manifests using the [HMAC runbook](operators/hmac-generation.md). |
| [awg-gateway](../deploy/friends/awg-gateway.py): `register/database/address`; [access-api](../deploy/friends/access-api.py) | `peers.db` is a **node-local allocation ledger**: `public → id → address`, with `AUTOINCREMENT` state and network settings. Enrollment rows contain a public key, not the complete allocator history. | Leave local allocation in place during control migration; include consistent per-node DB/settings in full recovery. Preserve row IDs and `sqlite_sequence`; replaying registrations in a different order changes IPs. A stale or empty peers DB is not an acceptable rollback. No central allocator migration is implemented. |
| [transport_gateway](../control/friends/transport_gateway.py): `prepare/accept/apply_serialized`; [transport_membership](../control/friends/transport_membership.py), [transport_reconcile](../control/friends/transport_reconcile.py) | `transport-state.json` contains decisions **and** durable prepared/cohort/terminal-denial state, boot/deadline bindings and receipts; `transport-attempt.json` is diagnostic evidence. | Do not discard receiver safety state as cache. Partial first-payment preparation can survive canonical DB rollback; all three serving nodes still ACK. Reboot must not renew a paid lease. Current clocks, identities, receiver floors and accepted snapshot must reconcile; no automatic unprepare, RU exclusion or copying another node's cache. |
| [awg-gateway](../deploy/friends/awg-gateway.py): `tcp_user`; [transport_gateway](../control/friends/transport_gateway.py): `plan/apply_serialized` | TCP `server.json` mixes server-owned configuration with managed clients; AWG live peers and TCP live users are derived application state. Runtime applies files and live commands in separate steps. | Preserve unrelated/noncohort bindings and server secrets. Reconcile only owned membership against current authority plus local allocation; verify persistent **and** live state. Atomic JSON replace is not a multi-service transaction or evidence of HA fencing. |
| [chat_sync](../control/friends/chat_sync.py), [chat-sync timer entry](../deploy/friends/chat-sync.py); [mailbox receiver](../pilot/messenger/accept_membership.py): `main`; [Membership](../messenger/membership.py) | DB chat sequence is authority. `members.json` is an expiring projection **and the receiver's persisted last-sequence check**. Receiver accepts only a greater sequence; reader rejects missing/corrupt/expired membership. | Preserve receiver high-water state, node identity and settings separately from the lease content; expired files grant nothing. Removing the file also removes that receiver's current anti-replay comparison. A replacement receiver needs a qualified floor/bootstrap, not an empty file. PG publication is already refused; distributed publication awaits HA-03. |
| [support](../control/friends/support.py): `publish/bindings`; same chat-sync entry | `support-bindings.json` derives DB sender/binding state, private `chat-support.json`, HMAC/aliases and an acknowledged mailbox lease. | Preserve sender policy/keys/aliases separately; a derived file is not proof that a sender is authorized or that mailbox ACK occurred. Rebuild only with matching current sequence/lease. PG publication remains refused before I/O. |
| [support_admin](../control/friends/support_admin.py): `change/write_admission`; [restricted_admin](../control/friends/restricted_admin.py): `main/publish_crl` | FIELD admission file is explicit operator policy; grants/audit and signed CRL outbox are DB authority. Existing SQLite CLI coordinates separate file/DB effects and compensation. | Snapshot admission plus grants/audit/CRL together; a file-only rollback must not resurrect a revoked grant. Existing canonical file-publication guards stay closed. HA-02J local CRL reconciliation is not distributed publication. |
| [restricted_sync](../control/friends/restricted_sync.py): `sync/gateway`; [bootstrap-broker](../carrier/cmd/bootstrap-broker/main.go), [SeedManager](../carrier/bootstrap/seed.go), [gateway runtime](../carrier/gatewayruntime/runtime.go) | Gateway profile/CRL and a separately running READY directory publisher have different ownership. RU `directory.json` is a validated mirror of a short-lived gateway publication, not the source of credentials. | Do not freeze/restore the publisher by merely rolling back a profile. Preserve publisher identity/configuration and current profile floors; prove fresh READY/expiry and owner isolation. Legacy sync is an alternate profile writer to account for, not permission to activate it alongside the canonical route. No Go publisher runtime acceptance is claimed here. |
| [gateway_routing](../control/friends/gateway_routing.py): `Policy.load/install`; [sign_friends_catalog](../scripts/sign_friends_catalog.py), [catalog verifier](../provisioning/friends_catalog.py), [initial installer](../deploy/friends/install-access.py) | Signed `catalog.json` / content-addressed catalogs are trusted inputs, not SQL exports. Policy generation/admit/legacy choices are explicit configuration; their hashes/assignments/sequences are DB authority. Installer copies the initial catalog; runtime loads exact hash-bound inputs. | Retain all catalog/policy bytes referenced by imported rows, anchors and client floors. Validate digest/signature/schema/sequence; never re-sign or silently use the newest catalog for all existing assignments. Schema3 explicit selection is separate from the schema2 signing helper. Forward rollback needs a newer accepted signed sequence. |
| [service_notices](../scripts/service_notices.py): `Notices.export/export_all/main`; [notice API](../control/friends/notices.py) | Notice roles/tokens/events/revisions/edit receipts are DB authority; public v1/v2 files are separate derived exports. | Import authority, not files as the source of notice history. Retain audience/expiry/order and exact publication status. Canonical returns `stored`, not delivered, and refuses export. Two file replacements are not atomic distributed delivery. |
| [sign_control_config](../scripts/sign_control_config.py), [sign_restricted_issuer](../scripts/sign_restricted_issuer.py), [sign_update](../scripts/sign_update.py), [credential publication](../scripts/gateway_credential_publication.py) | Offline signing creates trust artifacts; credential publisher atomically installs supplied bytes under an externally serialized contract. Release catalogs/installer versions are independent of the control DB. | No signing-key relocation, reissue, rotation, public update or artifact overwrite in HA-02. Retain offline keys outside HA servers/CI and protect delegated runtime credentials separately. A publication receipt does not establish a global writer epoch. |

Panel Django state, operator pending queues/cursors, client stores and mailbox
spool remain separate recovery domains. They are not sources of VPN grants;
“read-side” does not permit deleting operator intent, chat history or cursors.
The inventory does not claim full application/disaster recovery from a control DB.

## Writer freeze and activation checklist

Before a future live consistency barrier, collect a **private** per-node manifest
of effective unit/forced-command/cron entrypoints, executable and configuration
hashes, store paths, UID/GID/modes, ownership, current operation/floor and backup
coverage. Public evidence may contain aggregate counts/status and sanitized source
hashes, never raw paths/contents that expose private configuration or identity.
Map accepted installed bytes, including overlays; repository HEAD is not installed.

The barrier must cover these classes, or stop with an explicit missing writer:

1. Friends HTTP: invite/enroll/proof, paid projections, referrals, restricted issue/
   readiness, support/chat, routing/selection, metadata, diagnostics and notices.
2. Operator commands: `paid_beta_admin`, `restricted_admin`, `support_admin`,
   `service_notices`, support sender/routing setup, alias preparation/activation.
   Stop their dispatchers/queues too; preserve pending requests and idempotency IDs.
3. Timers/workers: paid reconciliation/watchers, chat/support publication,
   restricted sync/CRL, renewal and bounded maintenance, metadata/diagnostics
   retention/collectors and node registration forced commands.
4. Independent gateway/READY publishers and offline configuration deployment:
   record their ownership and fences; do not infer a stopped writer from a stopped
   API. A local lock only serializes callers using that lock on that filesystem.
5. Import activation: exactly one DB writer backend for each family and **no**
   still-active old SQLite CLI/timer path. Until HA-03, the new backend must not
   publish profiles, CRLs, membership, support bindings or notice feeds.

This is a freeze specification, **not an executable stop-services recipe**.
Node watchdogs/deny enforcement must continue; stopping the only authority while
short leases expire can interrupt traffic. Qualify the bounded barrier and recovery
before production, keeping8s operation /12s watchdog /paid lease≤120s unchanged.

## Import and recovery input contract

The [24 November installed census](releases/2026-11-24-control-ha-installed-census.md)
recognizes the deployed four-store schema but finds five additional owner-handoff
tables in the registry. The observation-only
[pinned definitions](../deploy/control-ha/sqlite-handoff-v2.json) match the existing
successor migration; they are not a new accepted importer schema. Retain legacy/current
operation history, security floors and generation bindings. Do not strip these tables,
infer they are disposable from their original fixture location, or treat CLEANED as
permission to discard anti-replay state. The old strict importer remains closed.
The subsequent [closed-handoff retention adapter](releases/2026-11-24-control-ha-handoff-retention.md)
preserves these rows and bindings in the canonical import transaction and makes the
five retained PG tables immutable. It refuses unsettled histories and regressing floors;
it is not a port/enablement of the handoff writer or a new certificate authority.
Its synthetic49-table restore/replication PASS does not replace actual capture,
external-secret recovery or separately established owner approval.

The next all-store synthetic importer must explicitly inventory versioned tables,
types/constraints/triggers/IDs/sequences and each external reference. Unknown tables,
missing authority inputs, mismatched hashes/generations, newer receiver floors,
unsettled operations or any unclassified writer are **NO_GO**, not warnings.

Compare at one logical checkpoint:

- Every canonical source store, including separate notices, metadata/consent and
  diagnostics; preserve tombstones, one-use proofs, immutable history and all
  three paid projections. Separate online SQLite backups are not a common barrier.
- Exact current alias manifest, FIELD admission, sender policy, catalog/policy/
  anchor bytes, profile/issuer/delegation/floors and maintenance state. Restore
  privileged keys via their own protected path; a passing DB dump cannot restore them.
- Per-node peers allocator/settings, receiver prepared/denied/high-water state and
  managed-vs-unmanaged transport ownership. Keep these node-scoped; never merge
  independent local ledgers by public key alone or overwrite them from control rows.
- Fresh publications only after their authorities and receiver fences are ready;
  no expiry extension, old catalog fallback or whole-directory copying to hide drift.

Existing [server snapshot tooling](server-secret-backup.ru.md) already includes
Friends peers/TCP and selected stores, but explicitly lacks a global transaction
and full disaster recovery scope. It is **not** the HA all-store importer. Do not
run its private stdout stream through chat/CI or treat its historical receipt as
current recovery evidence. Full external-input/key recovery remains unqualified.

## Checks and rollback

[Synthetic boundary tests](../tests/test_control_ha_file_boundaries.py) exercise
real alias prepare/save/load/seal logic and real node registration/SQLite backup,
with gateway commands, live TCP/AWG and paid-engine activation disabled. They prove:

1. Regenerating aliases with identical keys/rows changes random entity IDs/digest;
   an accepted old envelope rejects the recreated manifest.
2. Restoring the manifest retains historical IDs/handles and supports deltas with
   only the current key; a stale manifest rejects a newer envelope.
3. Rebuilding a peers DB in another registration order assigns different IPs.
4. A consistent SQLite backup retains row IDs, reverse-order idempotent registrations
   and allocator high-water state, including a synthetic deleted-highest-row case.

These are five local test cases, not SIGKILL, concurrent live snapshot, encrypted
off-host restore, network/fencing or cross-store atomicity acceptance. Existing
membership/catalog checks complement them; root profile and native publisher
gates are not rerun or waived. [Reproducer](../deploy/control-ha/README.md#ha-02n-file-authority-boundaries).

Rollback of this checkpoint is source/tests/docs only; no service, database,
profile, key, catalog or client changed. Before cutover discard only isolated
candidate state. After acknowledged new writes never restore an old DB, alias
manifest, allocator, profile or receiver cache to “undo” them: fence writers and
reconcile current state under a separately qualified recovery procedure.
