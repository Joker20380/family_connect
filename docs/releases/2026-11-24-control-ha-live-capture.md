# 24 November 2026 — authorized bounded live capture

## Actual node readback — 08:10UTC

Actual collector source916894b5771a6d2a8aa6fd34107c93ef5058d9b0 was pushed before use.
Each source has the reviewed installed pins and no allocator WAL/SHM/journal sidecars.
Local application/registration locks and the allocator transaction cover the fixed capture
scope together; three different timestamps are **not** an all-fleet/canonical barrier.

| Node | Capture UTC | Barrier ms | Peers | Sequence floor | Next offline ID | Ciphertext SHA256 |
| --- | --- | --- | --- | --- | --- | --- |
| RU | 08:09:57.894312 | 40.119 | 20 | 20 | 21 | `923f31cecabb50da208b4004515dc6f945c3cf9baaac917b3f0ec86bf8ebc261` |
| NL1 | 08:10:00.830636 | 36.184 | 55 | 55 | 56 | `29d6f8d8e71a7778249fe1a16a1b0d7d0bba00ab37e8cf2564ad3bcadd71e57c` |
| NL2 | 08:10:02.719195 | 5.020 | 7 | 8 | 9 | `203683d0947970568416dc80d4946147a93c15700f67a2e7c2fba1d54d2ca24e` |

Fresh-process authenticated restoration preserves8 files and69 cached decisions per node,
including the real NL2 sequence gap. A second qualification uses private scratch only:
installed Gateway.load/allowed/accept, policy.validate/successor and allocator.address ASTs
match the repository functions before using those native consumers. Installed source itself
is never imported/executed from the capsule. All207 duplicate accepts leave cached records
and lease deadlines unchanged;12 actual terminal denials refuse resurrection. All3 actual
paid-cohort records deny a changed boot, exhausted monotonic deadline and wall-clock expiry.
No pending noncohort preparation occurs in this actual snapshot; do not claim actual coverage
of that absent case. SQLite next-ID/address probes use memory and roll back. No engine
command, source mutation, service start/stop, network dispatcher or production restore.

Qualification source `scripts/control_ha_node_qualify.py`;94 focused checks PASS,49 new
node tests plus45 reused inventory/four-store safety checks. Synthetic tests additionally
exercise stale envelopes and changed native safety code. TCP/AWG configuration is exact-byte
custody, not a live engine/traffic qualification; terminal and lease checks do not turn
cached grants into fresh authority. Original service states/PIDs/invocations/restarts match
before/after each capture: RU AWG failed/TCP inactive pre-existed; both NL pairs remain active;
paid-watch remains active on all nodes. No attempt is made to disguise that RU failure.

Private capsules, capture/restore/native receipts and offline/scratch files are retained in
owner-only `control-ha/20261124-nodes-01`; wrapping keys/checkpoints remain separately in
`control-ha-keys`. No keys, user IDs, IP bindings or raw records enter Git. Rollback is still
release of locks/transaction, not deployment of the offline material. Installed/public
versions stay unchanged. Mailbox, legacy worker, OWNER runtime, native composite integration,
all-writer/dispatcher coherence and independently approved forward authority remain open.

## Installed node custody

Preparation source: `scripts/control_ha_node_capture.py` and
`scripts/control_ha_node_restore.py`;91 focused checks PASS, including46 new cases.
These cover immediate lock/SQLite contention refusal, source changes, symlinks/hardlinks,
same-byte rewrites, kernel deadline release after a hung read, sequence-floor corruption,
unknown schema/peer, stale/changed/wrong-key capsules, unsafe tar members and private restore.
No version, installer/catalog, deployment or production PostgreSQL change is authorized here.

Read-only preflight finds a16,384-byte rollback-journal allocator and69 cached records on
each node. RU installed gateway source matches the repository, NL1/NL2 retain the older
failure-reporting variant. Both use application.lock then registration.lock for registration
and paid-watch; exact gateway/archive hashes are pinned before locking. The installed
policy differs from repository only in the storage implementation of read_snapshot, not
the decision validation/successor contract. Original AWG/TCP state is failed/inactive on
RU, active/active on NL1/NL2; paid-watch is active on all three. These are pre-existing
states, not a traffic-health proof or a request to start failed services during rollback.

Execution/abort plan: acquire the existing application and registration lock files with
LOCK_NB, then BEGIN IMMEDIATE with SQLite timeout0; never create missing locks/databases.
The kernel250ms SIGALRM is armed before the first lock and kills a stalled collector,
closing descriptors/transaction without committing. Any contention, unexpected source,
non-DELETE journal, sidecar, link, replaced/changed file or oversized input refuses the
attempt. No retry loop, service stop, paid-watch freeze or gateway command is used.
Tar construction, transmission and encryption happen after releasing the barrier.

The fixed capture scope is peers.db including sqlite_sequence, settings.json,
transport-state/enforcement, AWG server.conf, TCP server.json and the two installed
source files. No client profile or metadata observations are selected. Settings.external
is the native interface name (ens3/eth0), **not** the node public host assumed by the
older synthetic adapter; that adapter is not weakened. Dynamic receiver clocks/boot,
prepared tokens, terminal denials and configuration bytes are retained without refresh.
No restart/activation or live engine state is reconstructed. The locks cover the reviewed
local application paths, not all administrative writers, the canonical registry, mailbox,
legacy worker or OWNER dispatcher. A per-node capture is not a cross-node fleet fence.

Custody uses AES-256-GCM with a distinct purpose and separately held key/checkpoint.
Only a new0700 offline directory with0600 files is permitted; exact byte readback,
installed source pins, allocator schema/sequence/IP range and receiver binding checks
must pass. The checkpoint is operator-held custody, not independently approved forward
authority. Rollback means automatic release on refusal; no live source is changed.
This preparation was followed by the actual08:10UTC readback above; those local slices are
no longer pending. It is not full HA-02 acceptance.

## OWNER database capture — 07:38:49UTC

The three existing OWNER containers are pinned by exact ID, Compose project
`fc-control-plane-0` and image; no other Docker application is selected. The source
PostgreSQL image remains `sha256:18cfe3ef5e6815560c98237d6216d1e5119702fb0f3894c8785dd58b8bbe5d73`.
Read-only size preflight finds1,389,696,691 bytes,39 public tables and25 sequences.
The initial128MiB small-database bound refuses before backup. The reviewed larger operation
uses a2GiB source/512MiB compressed archive bound,12.3GiB available disk, per-statement120s,
1s lock wait,180s idle-transaction expiry and120s dump timeout. It never stops panel writers.

A repeatable-read, read-only transaction exports one PostgreSQL snapshot. The native
`pg_dump --format=custom --compress=6 --no-owner --no-acl --snapshot=...` and logical-row
fingerprints use that same snapshot. Each retained row is hashed as canonical PostgreSQL
JSONB with SHA256, and each table hashes its sorted multiset of row hashes plus a separate
row count. The source transaction closes after86.920s. It is a coherent **panel database**
point, not simultaneous with the earlier fleet capture or a fence on external dispatchers.

Both `public.console_technicalmetadata` and `public.console_technicalmetadatasource` row
data are excluded from the dump. A separate projection selects only pseudonym, consent
epoch, sequence, consent status and received timestamp from the same snapshot:3 floors.
No observations or GeoIP enter the capsule. Retained ordinary data:37 tables/1,907,455 rows;
native schema for all39 tables and sequence definitions/state remain in the dump.

The owner-held AES-256-GCM capsule is51,312,677 bytes. Ciphertext SHA256:
`28bbb64de3907a1cf1949f1d20a04c63c3dcee94c0aef68cebf58611d5e240d1`;
authenticated archive SHA256:
`d957f6a34742963e0f8f9152f29b250036dd76747984e0454da95136c386037d`.
Private custody is `control-ha/20261124-owner-03`; key and checkpoint are separate owner
files in `control-ha-keys`. No plaintext dump is retained. Capsule layout is nine-byte
`FCOWNER1\0`,12-byte nonce and AES-GCM ciphertext/tag; AAD is
`family-connect/owner-postgres-custody/v1/floors-only/no-dispatch`. Decrypted tar contains
exactly `database.dump`, `floors.json`, `manifest.json`; never extract uncontrolled paths.

Two earlier read-only attempts close without a capsule: one fingerprint SQL parenthesis
error and one line-oriented parser refusal of multiline `json_agg`. The corrected query
uses compact `jsonb_agg`; failed-attempt receipts remain. Neither failure changes source
rows or disables any service. This is not a new product release or installed backend.

Fresh-process restoration authenticates the independent checkpoint and exact three-member
archive before using the dump. A unique labelled PostgreSQL container uses the same image,
`--network none`, no published ports, read-only root filesystem, UID/GID70, dropped
capabilities/no-new-privileges,1 CPU/512MiB and a new uniquely labelled disposable volume.
There is no Docker socket, source database volume, panel application or dispatcher mount.
The archive TOC confirms both technical-metadata TABLE DATA sections are absent.

Native `pg_restore --exit-on-error --single-transaction --no-owner --no-acl` succeeds.
Only the3 consent floors are inserted into the otherwise empty metadata table, with empty
`observations` and `geoip`; the source-status projection stays empty. Result:39 tables,
25 sequences, all37 retained table counts and SHA256 row multisets match, all3 floor
records match, zero nonempty observation/GeoIP rows and zero stale source-status rows.
The test does not replay operator intent or start a production panel. Sequence count is
verified; no new dispatch/sequence activation is inferred from that count.

The exact owned container/image/name/label and volume label are checked before removal.
Both are removed; subsequent label queries find zero remaining containers/volumes.
Original console/PostgreSQL/publisher IDs/images/status/start times match their preflight.
Rollback requires no production action. Never replace the running panel DB with this
offline point or restore metadata observations from an older backup.

This qualifies actual **OWNER database** custody/readback, not complete panel deployment
recovery: runtime environment/configuration/HMAC/collector custody and consistency with
external dispatchers/fleet remain open. The point is separate from07:22 fleet evidence.
HA-02 is not complete and production remains on its existing backends.

## Actual three-node file readback — 07:22:17UTC

Executed source `16c94824d49a3140f3a151729d78dc4db54fd7ed`, all108 focused tests pass.
Per-host explicit plans select36/19/19 files and3/2/2 bounded trees. These cover current
node/controller configuration,14 declared renewal source modules and API archive per node,
issuer/anchor/referral/HMAC/admission/sender inputs, both gateway private profiles/locators,
retained routing files, original renewal/coordinator and profile-operation history.
Derived short-lived directory publications, receivers, allocators, worker product database
and OWNER panel are not included or silently declared rebuildable.

| Host | Files | Directories | Exact bytes | Encrypted capsule SHA256 |
| --- | --- | --- | --- | --- |
| RU | 3,870 | 377 | 33,469,038 | `88d1175c81d7805eff5a0df91b7aa44dea2f6de9756341d0af48ec8891bbf5e0` |
| NL1 | 3,286 | 374 | 18,452,995 | `3a9cbeb7941e8483d68eb1d893f67e27cec5d705f961d480b3e6c7319b0c6789` |
| NL2 | 1,575 | 178 | 10,271,508 | `031d83f94b974106ab0a2d5bb980c75081064d55ffab79729f3744cbcf6c7990` |

After all file captures, a new simultaneous four-store SQLite barrier lasts52.099ms at
07:22:17.358283UTC; later witnesses match4,247/3,660/1,753 captured file/directory stamps.
The9,660 observations bracket the SQLite point without paid-watch/VPN/service stops.
AWG/TCP/paid-watch unit states/PIDs/invocations/restart counters and RU HTTP candidate
observations match before/after this point. This is not an end-to-end VPN traffic test.

Fresh processes, using only local encrypted capsules and separately held keys/checkpoints,
restore every file into new0700/0600 offline destinations and the four SQLite images into
a separate directory:34 tables/610 rows; closed handoff1/2/1/1/1. Metadata contains only
consent/replay floors. The earlier04:58 actual capsule refuses against the newer checkpoint
before decryption. Latest SQLite ciphertext SHA256:
`5ba8a5d2b720d07e91beba35ae887309538f1d44448e858edf8158b93ef77c35`.

Offline checks at the capture time pass: all three installed source/config/API bindings;
both signed delegations and issuer private-key/public-certificate equality; CRL27423;
both gateway leaf signatures/current validity/private-key match and locator/CRL/floor
bindings; signed routing/registry references; current terminal coordinator and all three
archive manifests. Original ledgers contain369/369/175 entries, not the older366/366/172
sample. Legacy bytes are preserved without executing code or inventing old approvals.

Native alias HMAC binding passes. Of69 devices,66 have retained alias history and3 are
explicit new entities, as supported by `pseudonyms.seal/unseal`; all4 paid events are mapped.
Native roundtrip preserves old handles and the3 current identities without changing the
manifest. The older `external_v1.alias_check` deliberately requires every mapping and still
refuses this shape. Do not repair that refusal by inventing old identities or changing
production aliases: an installed-format recovery path remains required. Initial exploratory
anchor verification supplied encoded file bytes instead of decoded32-byte public material;
correct decoding passes the unchanged source verifier. Initial probe receipts remain.

Private receipts/capsules/readback are under the owner-only `control-ha/20261124-external-01`
custody directory; wrapping keys and checkpoints remain separately in `control-ha-keys`.
No raw records, profiles, keys or journals are committed. Source publication does not deploy
the collector. Installed console5ce82415, RU HTTP4e2df679 and public Android126/catalog9
are unchanged. Rollback of this read-only operation requires no live action: never restore
these old credential profiles into a running host or start pre-existing failed units.

HA-02 remains IN_PROGRESS. File-stability observations do not prove an all-writer fence or
absence of an already incomplete cross-store operation. Full receiver/allocator/mailbox,
legacy worker and OWNER panel custody/recovery, exact installed-format integration and
independently approved current forward trust remain required. No production PG switch.

## External-file custody

The prepared bounded operation uses `scripts/control_ha_file_custody.py`: an explicit private
per-host plan, restricted Family Connect roots, exact selected files and only renewal history,
profile-operation or routing trees. No broad project/home/key-directory backup. Database and
technical-metadata paths are rejected. Runtime issuer/profile keys belong in encrypted owner
custody, never Git, CI, terminal output or the PostgreSQL canonical DB; offline release keys
are outside this operation. Legacy journal bytes remain opaque, not fabricated approvals.

Collection is read-only/no service stops. The collector rejects links, special files, path
overlap, oversized/deep/changed trees and keeps original byte digests and metadata. A later
file witness checks inode/ctime/mtime/size/mode plus directory membership observations, so
changes including same-byte rewrites are refused. Bracketing the SQLite point with these
observations is useful evidence, **not** proof that every external writer is fenced or that
an already incomplete multi-file transaction is valid. Pending operations and semantic
key/profile/DB bindings still need separate checks.

AES-256-GCM and an external owner-held ciphertext/document checkpoint reject changed/stale
capsules; fresh-process offline readback restores exact bytes with0700 directories/0600 files
only in a new destination. It never replaces live paths, executes saved source, adopts original
root ownership, enables credentials or resets replay floors. Abort leaves the live system
untouched; a partial offline directory is not acceptance and cannot be overwritten on retry.
This work belongs to the existing capture/history/full-recovery gates, not a new stage.
108 focused tests PASS/0 skips (42 new file-custody guards,
26 installed-inventory and40 SQLite capture/restore checks). No production/version change.

## Authorization and scope

Owner response: “подтверждаю давай делай”, explicitly answering the request for a limited
live snapshot with temporary management-write blocking, after checking the concrete
stop/abort/rollback plan, without switching production servers to PostgreSQL.
This removes the prior development-only permission blocker for that bounded operation.
It is not retroactive approval of old journals, a production migration, issuer rotation,
new release, HA-03 fencing rollout or general permission to stop VPN/data-plane services.

HA-02 remains IN_PROGRESS until all existing four gates pass. The last source checkpoint
is `afe4812e7c12dfd83b22cc50659c35152208d700`:555 offline contracts/zero skips and49-table
synthetic recovery, not actual-state acceptance. Existing source, public artifacts and
installed production versions are not assumed equal.

## Execution preconditions

Refresh RU185.251.89.19, NL1 185.10.158.212, NL2 185.10.158.196 and OWNER observations.
Use existing strict SSH pins and scoped Family Connect resources only. Do not access
retired/excluded gateways or neighbouring MicroTrader services. Read actual unit/command/
account/configuration bindings privately before deciding which writers to inhibit.

Before inhibiting any writer, preserve its exact prestate, identify timers and external
dispatchers, check pending operations/locks, define a bounded interruption budget and
independent recovery of the barrier if the SSH/coordinator connection disappears.
Existing failed or inactive services must not be started under the guise of rollback.
Do not stop VPN transports or broadly freeze the machine. Unknown writer scope, active
unsettled operation, unsafe path or unavailable recovery guard aborts before disruption.

Actual DBs, keys/profiles, journal trees, panel data and raw evidence remain private,
outside Git/CI/terminal output. Capture must preserve installed schemas and source bytes,
legacy history and floors; neither current nor historical rows are edited to satisfy a
verifier. Any capsule must be authenticated, independently pinned and restored to isolated
targets before being counted as a recovery gate. Never restore the backup over production
as a test. After the bounded capture restore only the pre-existing intended service states,
verify management availability and record remaining checks honestly.

## Reviewed first capture operation

Installed preflight finds Python3.14.4/SQLite3.46.1 and the required
`SQLITE_DBCONFIG_NO_CKPT_ON_CLOSE` on RU. The four application databases total598016
bytes before capture. The active paid-watch has a12-second watchdog and an8-second
application operation budget; its failure path stops transport services. Therefore
neither stopping/freezing paid-watch nor a long registration-lock hold is an acceptable
generic management barrier. No such action is performed. The legacy peer-worker runs
inside Docker and has a70-second graceful stop budget; it is not a short-pause substitute.

The reviewed first operation is restricted to the four RU application SQLite stores.
`scripts/control_ha_live_sqlite.py --capture` opens only their existing fixed paths,
refuses unsafe files/sidecars/possible hot rollback journals, disables checkpoint-on-close,
and obtains all four `BEGIN IMMEDIATE` locks with zero busy wait. All locks remain held
until every image is serialized. There is no application SQL write, COMMIT, service stop,
timer disable, forced-command change or profile/issuer write. An already busy store aborts
immediately and rolls back acquired transactions. A one-second default-action kernel alarm
covers acquisition, serialization and connection closure; if the process stalls or its
coordinator disappears, termination releases SQLite's OS locks without a remote restart.
The alarm is not a hard real-time guarantee against uninterruptible kernel/storage failure.
No externally controlled signal handler is installed. Core dumps are disabled by the CLI.

Only after all locks are released does the tool verify exported images, hash them and emit
a binary archive to a private SSH consumer. Terminal output is refused. Private material
must be encrypted off-node with separately retained key/checkpoint; only aggregate sizes,
hashes and success/refusal may enter documentation. WAL header normalization affects only
exported images, never source bytes. Rollback is transaction close/process exit, not a
database restore. Before/after units and application reachability must be checked separately.

This is a consistent four-store point, **not a fleet/file/OWNER barrier**. It does not prove
that an application operation spanning DB and external files is settled. The manifest
explicitly refuses full-recovery/fleet-barrier claims. It advances actual schema/row
preservation and isolated validation; external authority/history/custody remain required.

Qualification:56 focused capture/census tests PASS, zero skips. These include all-stores
locked before the first image, each busy-store abort, a killed/stalled capture releasing
locks, uncheckpointed WAL commits, unchanged source DB/WAL bytes, unsafe/hot-journal refusal,
no output before success and alarm ownership. No production capture result is inferred.

## Initial ephemeral capture and off-node four-store restore

At **24 November04:45:16UTC**, the pinned SSH capture executes source
`084530ce30862a5353c99ada36e3b22704dcddec`. Acquisition/serialization/rollback/close take
**0.041791344 seconds**, below the one-second abort deadline. The common fully locked
interval containing all four image reads is approximately7.816ms. All transactions are
rolled back and connections closed before transmission. Four images total598016 bytes
and retain34 installed tables. No timer, service, forced command, profile or issuer changes.

The604197-byte encrypted capsule was temporarily retained on OWNER, outside Git, not on RU.
Its SHA256 is `b2e867323b73c53a6450f0ebe11a7b6955b82e4de103819ba90be891dc2527f2`;
the archive SHA256 is `d1b4f0274ed6dc0896abd9bdda5776be4cf69028c8f54a7044152b4b5d1454db`.
AES256-GCM key and expected checkpoint were in a separate owner-only local custody
directory; the key was never logged or committed. This was off-RU retention, **not an
independent external custodian or a signed whole-fleet forward checkpoint**.

`scripts/control_ha_live_sqlite_restore.py` checks the external checkpoint, ciphertext
hash, AEAD tag, archive/image hashes, exact installed schema/PRAGMAs, integrity/FKs and
closed handoff history/security floors before creating a new0700 offline target. It refuses
existing targets, unsafe archives, wrong keys, stale pins, unknown schemas and public
output parents; it never connects to production or executes captured code. Actual
fresh-process restoration on OWNER passes: **four stores /34 tables /607 rows**,
exact byte readback and retained handoff counts1/2/1/1/1. All private values stay private.
This restores SQLite, not an accepted PG import or application restart.76 focused
capture/restore/census tests PASS /0 skips.

Before/after RU/NL1/NL2 AWG/TCP/paid-watch observations, and the RU management unit, have
identical states/PIDs/invocations/restart counters. RU loopback HEAD on the actual management
port returns501 before/after: listener reachability, not authenticated product health or
a VPN traffic test. Pre-existing RU failed/inactive services are **not** restarted or
disguised as healthy. NL service state stays unchanged; no data-plane stop is performed.

An earlier read-only probe fails because it shadows an HTTP module name. It aborts
**before capture or any DB lock**; its failure receipt is retained. The corrected probe
precedes the single successful live capture. All capsule/key/evidence/restored files
stayed outside Git/CI. The raw observation-bearing copies are subsequently removed below.

Rollback is already complete: transactions closed, locks released; no live DB restore,
version rollback or service restart is necessary. Source tools may be left unused.
Do not copy offline restored files over production. Installed/public versions, downloads,
catalogs and backend choices remain unchanged.

## Metadata privacy correction before durable custody

The applicable [panel/metadata retention runbook](../../control_plane/README.md) forbids
long-lived observation backups and restoring old panel projections. The initial raw image
contains3 nonempty metadata payloads. It is therefore **not retained as a durable backup**:
after its offline byte/schema qualification, the exact original encrypted capsule, its key,
all four offline restored images and the unused key from the aborted probe are removed
with hash/ownership/no-link checks on24 November04:57:26UTC (7 files). Receipts/checkpoints
remain; live files, consent state and source tombstones are untouched. File deletion is not
claimed as physical secure erasure. No raw observation copy is committed or distributed.

The corrected capture uses purpose/ciphertext v2 and a freshly built metadata database.
It selects only device, consent epoch, sequence, request digest, enabled and received;
`payload` is always `{}`. It never serializes the original metadata database, so deleted
payload fragments/free pages cannot leak into the retained image. Other store images remain
exact; metadata schema, row coverage and consent/replay floors are retained, not rewritten
on production. Existing replay cannot repopulate observations; a revoked epoch cannot become
enabled by a later sequence in that same epoch. Fresh consent-fenced data must populate
observations after recovery. The restorer refuses v1 and any v2 image carrying nonempty
payloads, even when the archive/hash/tag authenticate successfully. This is an explicit
privacy projection, **not an exact original metadata byte copy**.

79 capture/restore/census tests PASS /0 skips, including privacy removal, unchanged source,
enabled/revoked floor preservation, replay/re-enable refusal and observation-bearing archive
rejection. The next actual durable capture must use this v2 source and a fresh key/checkpoint;
the previous successful ephemeral receipt is not a current retained-backup claim.

## Retained v2 capture and restore — 04:58:58UTC

Source `eba7a5ce87cb9b6d45ac649d31ba63793371b8a8` is remotely verified on the agreed
branch before capture. The actual v2 barrier takes **61.694ms**, below its one-second
deadline; the fully locked image-read interval is15.921ms. The four exported images
total589824 bytes, including the freshly built12288-byte consent-floor-only metadata store.
The encrypted capsule is604197 bytes, SHA256
`ec2e84182a07acd739262113dfa63b4d17c4a9480b1a838046d4c392b01c028e`;
archive SHA256 `f01682b5a794fc5cc61d11c0dd51ca54faea0439f5ad841d0332f8c222689da4`.
New key and checkpoint remain separate owner-only files outside Git/CI.

Independent fresh-process local restore passes **4 stores /34 tables /609 rows**, exact
export-image readback, all five handoff tables1/2/1/1/1 and zero metadata observation
payloads. The registry changes legitimately between the two captures; no row is rolled
back or edited to match the earlier607-row image. Metadata byte equality refers only to
the privacy-projected export, never to the original live file. Sources remain untouched.
RU/NL1/NL2 unit state/PID/invocation/restart-counter comparisons are unchanged again;
RU management HEAD remains501 before/after. No stop/start/freeze occurs.

The retained private custody directory is
`~/.local/share/family-connect/control-ha/20261124-live-capture-03/`;
its separate key/checkpoint are under `~/.local/share/family-connect/control-ha-keys/`.
Only the owner should access them. Use the authenticated offline-restore tool against a
new private directory; never copy these files into production. This v2 checkpoint
supersedes the removed ephemeral v1 material, but not the remaining whole-fleet gates.

## Remaining HA-02 gates

The actual four-store capture/restore slice passes, but HA-02 is **IN_PROGRESS**. It does
not cover external files/issuer keys/renewal histories, NL receiver/mailbox state, legacy
peer-worker state or the OWNER panel. Their coherent writer/dispatcher boundary and complete
independently trusted recovery remain required. New acknowledged writes/current restore/
stale-copy refusal remain qualified in the laboratory, not across the complete actual fleet.
The previously accepted strict PG/Patroni replication gate remains PASS. No HA-03..05 starts.
