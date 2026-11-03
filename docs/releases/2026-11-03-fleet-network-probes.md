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
- Local runtime rollout NOT_YET_RUN at this source checkpoint; source bytes are not
  assumed deployed. Credentials/private evidence/build outputs remain outside Git.

Versions unchanged: installed Linux `0.2.12~l03.2.13`, public Linux `0.2.11`, public
Android110/catalog5 and Windows `0.2.16`/catalog12. No client build/install/publication.

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
