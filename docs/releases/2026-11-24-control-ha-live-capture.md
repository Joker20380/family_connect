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

## Current result

Permission recorded; bounded four-store capture implementation qualified locally. No live capture, barrier success,
actual independent restore or HA-02 completion is claimed by this checkpoint. Product
versions/public downloads/catalogs remain unchanged. Source-only rollback is to stop this
preflight; there is no server change to undo at this point.
