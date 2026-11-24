# 24 November 2026 — authorized bounded live capture

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
