# Independent network evidence and bounded advisory recovery — 3 November 2026

## Task and boundary

Owner explicitly authorizes the next bounded FLEET-BOOTSTRAP-2 substep after the
[three-source observability rollout](2026-11-03-fleet-observability.md). No interactive
owner test is required. Linux .13 physical acceptance stays DEFERRED_TO_FIELD, not PASS.
No unrelated task, enrollment, paid/cohort change, user connection switch, production
service restart, public release or catalog publication is included.

Dependencies: admitted ordinary AMS1/AMS2, exact-source local inventory, existing
operator RBAC and loopback-only PostgreSQL console. This does not repurpose the
fenced bootstrap-rehearsal agent or claim second-node MESH. Stage5 admission still
requires authenticated peer API and real data-plane proof; stage6 session failover
is not implemented by this observation layer.

## Independent evidence

`control_plane/apps/console/network_probe.py` uses an operator-controlled fixed map:
RU `185.251.89.19:8443`, AMS1 `185.10.158.212:443`, AMS2 `185.10.158.196:443`.
The local runner makes one TCP connect then closes, without application data, SSH,
identity/profile keys, DNS, redirects, arbitrary target arguments or UDP assertions.
It records exact source/address/port, probe type, operator-workstation vantage, UTC
completion time, duration and a bounded outcome (reachable/refused/timeout/network_error).
Raw socket exceptions never enter the record. Each connect has5s; each local import20s.

This is independent of SSH collection and systemd, **not an independent failure domain**:
the operator workstation, its routes and possibly its VPN remain a shared vantage.
An open port neither authenticates the remote identity nor proves AWG, REALITY, MESH,
API semantics, traffic forwarding or internet. AWG UDP/data-plane is NOT_CHECKED;
UDP connect success must never be promoted into readiness. Endpoint changes require
a reviewed map update; older binding evidence is rejected by the policy.

`probe_network.py` has its own lock and local systemd service/timer, with95s total budget
and60s after completion. No overlap or unbounded retry. Missing SSH credentials,
failed inventory imports and an absent registry do not disable these network probes.
If one local import fails, remaining endpoints are still sampled; error output is
sanitized and the service fails instead of falsely reporting all imports successful.

`NetworkProbe` is a separate append-only local PostgreSQL table (migration0007).
Import is an operator CLI only, not a public ingestion endpoint or remote attestation.
Strict schema/type/endpoint binding, immutable rows, unique(source,time), digest
idempotency and conflicting replay rejection preserve evidence. Production and
synthetic data remain separate; no user identities or payment/assignment FK is added.
Existing inventory/server view permissions protect readbacks; no recovery button,
editable Admin model, fleet-ready field or integration into `rank_gateways` exists.

## Advisory recovery policy

The latest three records must all match source, endpoint, probe and vantage; times
must descend strictly, be non-future and no older than5min. Latest must be≤150s old,
each gap≤150s, total span≥90s. Existing independent service evidence must also be
fresh (≤5min) and either observed_active or degraded. No missing/unknown state is green.

| Evidence | Advisory only |
| --- | --- |
| Missing probes | no_data |
| Wrong binding, stale/future, missing/unknown services, replay/non-descending time or long gap | hold |
| Fewer than3, too short a span, or mixed success/failure | stabilizing |
| Three successes + active services | observe; VPN remains not_checked |
| Three successes + degraded services | investigate_service |
| Three failures + active services | investigate_path; not proof of node failure |
| Three failures + degraded services | investigate_node; no automated repair |

Failure and recovery both need three consistent samples. One transient failure or
one successful retry cannot declare failure/recovery. A policy result is a pure
read-time advisory, not a queued action: automatic_action=false in every branch.
There is no automatic restart, rollback, policy/catalog change, failover or existing
assignment migration, and no retry loop capable of disrupting users.

Before any future actuator: separately qualify authenticated per-transport canary
and traffic proof, independent failure-domain corroboration, exact incident/target
binding, durable at-most-once action journal, cooldown and retry budget, post-action
proof, rollback and stop conditions. Current evidence cannot authorize such actions.
This future gate is a design boundary, not a scheduled or automatically started task.

## Checks and rollout checkpoint

- Operator/probe/policy/collector/packaging tests:73 PASS.
- PostgreSQL targeted new-probe plus existing observability tests:69 PASS.
- Full PostgreSQL console:186 PASS; Django check PASS; migration drift NONE.
- Documentation links/whitespace: new links PASS; the broader5-file/524-link scan
  retains the existing STATUS historical27 October anchor error, not a full docs PASS.
- Initial direct TCP observation: all3 reachable; no VPN/authenticated handshake PASS.
- Local runtime was NOT_YET_RUN at the source checkpoint; subsequently verified
  below. Credentials/private evidence/build outputs remain outside Git.

Versions unchanged: installed Linux `0.2.12~l03.2.13`, public Linux `0.2.11`, public
Android110/catalog5 and Windows `0.2.16`/catalog12. No client build/install/publication.

## Verified local rollout

Source `9870e129ba7e24f16560a5d47e0da187b259da9b` pushed and remote SHA verified.
Local image `sha256:55119faec980ca2ce58bf3f1846c01f649a2e8a31ca6fccdfb84ffd1b0474285`:
184 packaged source/lock hashes match, checked in a read-only network-none container;
the running console uses that exact image. Local health PASS and binding remains
only `127.0.0.1:8765`. Migration0007 applied to the local PG database only. Existing
`.env` bytes/volumes retained; private pre-migration PG dump retained. Payment and
operation row hashes unchanged; synthetic model counts remain3 payments/7 operations/
50 devices/3 cohort records. These are not real-user/payment success statistics.

The existing inventory timer was paused during the local build/start and restored;
only the local console was restarted. Independent user service/timer installed from
the source templates and active,95s budget,60s after completion. Initial direct
observations and the recurring service send no credentials or transport payloads.
No production VPN/backend service restart or configuration/assignment write occurred.

Readback at `2026-11-03T07:23:36.734921+00:00`:

| Source | Actual completion times (UTC, oldest → newest) | Outcome / advisory |
| --- | --- | --- |
| gateway-ru | 07:21:03,07:22:11,07:23:21 | reachable ×3 / observe |
| nl-amsterdam-1 | 07:21:05,07:22:13,07:23:23 | reachable ×3 / observe |
| nl-amsterdam-2 | 07:21:07,07:22:15,07:23:25 | reachable ×3 / observe |

All three sources also have fresh observed_active service evidence. The spans exceed
90s without invented/backdated samples; early readbacks correctly showed stabilizing.
Read-only RequestFactory rendering through the existing permission-guarded views
verified three independent cards, explicit no-switching notices and the node detail
page. This render is not a new browser login/authentication acceptance; RBAC is covered
by the PostgreSQL tests. `automatic_action=false`, `vpn_readiness=not_checked` throughout.
No second-node MESH, authenticated traffic, field acceptance or continuous uptime PASS.
The workstation must remain awake; losing this vantage yields missing/stale evidence,
not a remote failure diagnosis. No full production endpoint monitoring service is deployed.

Locked PostgreSQL final suite suffix `9a94533d`:69 targeted/186 full PASS; initial
suite `6a1d19ca` also PASS before the additional source-filter regression assertion.
Operator73 PASS. The documentation checker has no help switch: an initial `--help`
invocation failed before checking files; the subsequent explicit-path scan retains
only the previously recorded historical anchor error. No failing tests were hidden.

Local evidence/backup/logs: ignored `state-client-build/fleet-network-probe-20261103/`.
[Sanitized receipt](2026-11-03-fleet-network-probes.receipt.json).

## Local rollout and rollback

After tests, back up only the local PG database privately and preserve `.env`, volumes
and the prior local image. Build the allowlisted source context, start only the
loopback console (additive migration0007), verify hashes/health and protected model
counts. Install the two templates as user units named
`family-connect-network-probe.service` and `family-connect-network-probe.timer`,
substituting the exact repository root and Python. No production credentials required.
Verify imports on all3 exact endpoints, multiple timed observations, UI advisories,
separate inventory timer and unchanged public versions. Do not manufacture timestamps.

Rollback: stop/disable only this task's local network-probe timer and wait for any
in-flight read-only cycle. Preserve history and receipts. Keep the existing inventory
timer, private secrets and data volumes. If needed, restart the prior local console
image, leaving additive migration0007/table/history intact; no `down -v`, automatic
DB restore or destructive schema reversal. No production/client rollback is needed.
The retained previous image is
`sha256:0862dbdbb9a0f9d545cb4c71d2990f83cfe1126b1967078509e9f8f06b81c2fe`,
also tagged locally `fc-control-plane-0-console:before-network-probes-20261103`.
No rollback was needed. This bounded step is complete; the isolated authenticated
per-transport/data-plane canary is the next candidate, not automatically started.
