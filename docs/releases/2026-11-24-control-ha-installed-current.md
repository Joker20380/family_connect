# 24 November 2026 — actual installed-current evidence, recovery still blocked

## Selected scope and outcome

Continuation of the same [current-operation task](../PLAN.md), not a new lettered
variant or permission to start another HA-02 block. The preceding
[content auditor](2026-11-24-control-ha-current-audit.md) was qualified on synthetic
inputs. This checkpoint adds actual read-only RU/NL1/NL2 observations and identifies
a concrete installed-state mismatch. The selected acceptance gate remains IN_PROGRESS.

Final observation: **24 November00:13:07–00:13:10UTC** (01:13 Brussels), sequential
pinned SSH to RU185.251.89.19, NL1 185.10.158.212 and NL2 185.10.158.196. Existing
NL2 authorization/pin is recorded in the [host runbook](2026-11-02-second-nl-ordinary.md#authorization-and-trust).
No retired/excluded host or MicroTrader service was accessed. The collector was streamed
to an existing interpreter with `-I -B`; it was not installed and no production executor
was imported. Only fixed Family Connect `systemctl show` calls and read-only file/SQL
observations ran. No service/timer/configuration/DB update or state restoration occurred.

## Actual evidence

| Check | Observed result |
| --- | --- |
| Current operation | Same COMMITTED operation and canonical plan on all three nodes; native current archives and CLEANED ledger hashes agree locally |
| Historical ledgers |366/366/172 entries retained; current archives contain10/9/9 files; history was not pruned, equalized or reinterpreted |
| Installed renewal source |All three14-file manifests match `e9fd31754bdf50c95842a1644f86ddb328b839ec1e0c9454daf08d3e9d17f0cc` |
| Node configuration/order |Each current config SHA matches that node's `transaction.before[slot].policy.node_config`; the configured service order and archived start-intent unit bindings match |
| RU issuer state |Primary/secondary issuer documents and CRL equal the current plan |
| NL material |Both installed gateway certificates/CRLs equal their corresponding plan candidates |
| Publications |Both current RU directories equal their committed publication hashes and the corresponding NL copies |
| DB projection |Devices69, invites125, grants2 and CRL sequence1 match the plan; certificates do **not** |
| File stability |No observed metadata replacement/change during each host probe; not an atomic cross-host/store snapshot |

The certificate baseline has **three rows**, all expired by observation time. Current
DB has **one different row**, whose parsed certificate not-before is after the renewal
plan issue time. Row comparison:0 unchanged,3 removed,1 added. No row, device/invitation
identifier, serial, certificate/profile payload or private key leaves the host.

This is consistent with normal [certificate pruning and issuance](../../control/friends/restricted.py),
not proof of a failed service or corrupt DB. Timing alone does not authenticate the
writer or authorize those changes. Crucially, the previous exact five-table binding
compares against the renewal baseline, which is not a general current-state snapshot
after later application writes. It must refuse this input; no production recovery
capsule was assembled or passed to the auditor, and no acceptance bypass was added.
**Never restore the three expired rows, delete the new certificate, or edit/re-sign
old journals to make an equality check pass.**

## Service observation, not end-to-end health acceptance

- RU `family-connect-friends-http-candidate.service`: active/running, Result=success,
  NRestarts=0 at observation.
- Both NL `family-connect-restricted-bootstrap.service`: active/running, Result=success,
  NRestarts=0. This is not a VPN/WebRTC traffic, HTTP endpoint or client failover test.
- RU credential-renewal and directory-sync timers: active/waiting. Their one-shot
  services are inactive/dead with Result=success, which is not a crash by itself.
- Legacy restricted-sync timer/service: inactive/dead with Result=success. The
  [3 November fleet activation](2026-11-03-second-nl-mesh.md#permanent-fleet-activation-and-live-data-plane)
  explicitly retained the disabled legacy timer. It was not enabled or restarted here.

## Provenance: what is established and what is not

The node config hashes retained by the current transaction bind its service-unit order
to the observed installed configuration. This closes the narrower **caller-supplied
unit-order evidence gap for this observation**, not independent historical authorization.
Present RU controller schema2 points at the observed node/coordinator paths and has
`approved_leaf_crl_schedule=true`; its SHA256 is
`a3fae10e013b770bf4edf1e18ceec3046c4670feee784f3f567ea0a256c30801`.

The current native transaction retains the schedule decision, **not the original
controller config or owner approval**. Targeted inspection of the retained source
manifest found `binding=unbound`, `production_configuration=absent`, `operation_permit=null`.
The deployment report provides historical activation context, not those missing bound
bytes. Inspected stage/first-renewal receipts do not establish original schedule approval.
This is a bounded search, not a claim that no older protected backup could contain it.
Do not infer past approval from the present flag or the owner's general HA request.

## Implementation and qualification

[Collector](../../scripts/control_ha_installed_current.py) reuses the no-follow,
bounded [inventory reader](../../scripts/control_ha_installed_inventory.py). It reads
only the selected archive's payloads on-host, rejects pending/unknown node roots,
checks current manifest/ledger/plan/reconciliation bindings and exposes only fixed
field names, counts, digests and booleans. Other archives remain untouched/opaque.

SQL uses URI `mode=ro`, `query_only=ON`, one read transaction, data-version/metadata
rechecks, a5s VM deadline,1MiB SQLite value limit,4096 rows/table and16MiB aggregate.
It includes existing WAL state; it never uses `immutable=1`. WAL without pre-existing
sidecars refuses before connecting, rather than initializing them. SQLite read locks,
SSH audit logs and filesystem access times are observational side effects, not a
writer fence. No shared snapshot/barrier or signature/authorization validation is
claimed. Every result remains `recovery=BLOCKED`, `activation=FORBIDDEN`.

```sh
python -m pytest -q tests/test_control_ha_installed_current.py \
  tests/test_control_ha_installed_inventory.py tests/test_control_ha_current_audit.py
python -m scripts.control_ha_installed_current --config /absolute/node-fleet.json \
  --runtime /absolute/renewal --controller /absolute/controller-fleet.json
```

Use the existing control/identity-lockfile environment. For an NL observation omit
`--controller` and supply `--operation-sha256` from the private RU result. Retain the
existing approved SSH pins, private0700 destination/umask077,85s remote/95s local
deadlines. Stream the exact two source modules in memory; RU uses its existing
friends-access venv (CRL parser), NL uses system Python. Never run node/controller
entrypoints or paste private connection/configuration material into command output.

Final qualification: **112 PASS /0 skips in22.23s**:30 new collector tests,26 inventory
regressions,56 current-audit regressions. Tests cover unchanged bytes/mtimes/no payload
export, subsequent changes in each table, duplicate row accounting, pending/fenced/
tampered journals, replaced files, source/config/order/locator mismatch, private error
redaction, future/noninteger receipt times, row bounds and real uncheckpointed WAL
visibility/missing-sidecar refusal. No new PostgreSQL, full-system recovery or platform
release qualification is claimed.

Final qualified source hashes, matched against all three final host receipts:

| Source | SHA256 |
| --- | --- |
| control_ha_installed_current.py | c9b48a35ffd96f57ed376f75b7fc889d9c3ac64e09b45dca139a2bcd4a65656c |
| control_ha_installed_inventory.py (unchanged) |323035f48bc156215085a0dcc28eb5b5fc1b85747b6ae7d0d51f3d5208ef40fe |

Six documentation files/962 local link targets checked without errors; whitespace passes.

Private final evidence: `/tmp/fc-control-ha-20261124/current-installed-final/`, three
host JSON/meta receipts and `reconciled.json`; JUnit:
`/tmp/fc-control-ha-20261124/current-installed-regressions.xml`. Earlier discovery and
the first observation are retained separately under `current-installed/`. The initial
explicit-key RU attempt failed authentication; the existing authorized pinned connection
then succeeded. No SSH trust/authentication policy was weakened. Private evidence is
not committed and `/tmp` retention is not off-host disaster-recovery custody.

## Remaining gate and rollback

Continue this same task with a narrowly defined **post-renewal current-state contract**:
keep the immutable renewal baseline as evidence, independently qualify subsequent
certificate expiry/issuance and bind the actual current DB/issuer/publications to one
consistent capture. Do not relax equality solely because this observation looks normal.
Original schedule/configuration provenance still needs a trusted retained source; if
unavailable, a separately authorized forward-only provenance design is needed, never
retroactive approval. This checkpoint does not authorize deploying that design.

The four fixed [stage2 exit blocks](../control-ha.md#когда-заканчивается-этап-2) remain:
journals partial; installed schemas/writer barrier, full off-host/current-state recovery,
and strict PostgreSQL/Patroni quorum/RPO0 unqualified. No new letter or credible ETA.
HA-03..05 follow; current production still depends on RU.

Rollback: stop using the collector; there is no installed change to reverse. Preserve
private observations and current production data; a source revert must be a new normal
commit, not history rewriting. No deployment, publication, version, catalog, policy,
timer or host-resume change. Installed console5ce82415, RU HTTP4e2df679, NL GeoIP
22 November, Android126/catalog9,8/12/120s and all-three-node ACK remain unchanged.
