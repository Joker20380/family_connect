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

## Current result

Permission recorded; execution preflight in progress. No live capture, barrier success,
actual independent restore or HA-02 completion is claimed by this checkpoint. Product
versions/public downloads/catalogs remain unchanged. Source-only rollback is to stop this
preflight; there is no server change to undo at this point.
