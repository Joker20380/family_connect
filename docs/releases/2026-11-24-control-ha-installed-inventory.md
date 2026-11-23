# 24 November 2026 — CONTROL-HA installed journal inventory

## Scope and result

Selected NEXT from HA-02V: read-only installed-shape census and host reconciliation,
not another hypothetical renewal variant. This slice is COMPLETE; the journal block
and stage2 of5 remain open. Production still depends on RU. No deployment, service
start/stop, timer suspension, journal execution, profile/DB mutation or new trust pin.
No subsequent queued implementation is started by this checkpoint.

Final observation:23 November23:16:08.980927–23:16:13.214058UTC,
24 November00:16 Brussels. All three SSH calls succeeded. These are serial observations,
not an atomic cross-host snapshot or a general availability/transport health check.

| Observation | RU | NL1 | NL2 |
| --- | ---: | ---: | ---: |
| Completed-ledger entries / archive directories | 366 /366 | 366 /366 | 172 /172 |
| CLEANED / CLEANED_FENCED_ROLLBACK | 363 /3 | 363 /3 | 170 /2 |
| Archive filename shapes | 15 | 6 | 5 |
| Archives with services-before.json | 366 | 366 | 172 |
| Missing archives / unledgered archives | 0 /0 | 0 /0 | 0 /0 |
| Entries outside the three-node intersection | 194 | 194 | 0 |
| Active owner.json marker observed | no | no | no |
| Metadata entries checked | 4169 | 3609 | 1718 |

The172 common operation identifiers have no ledger-result disagreements. The current
RU coordinator operation is COMMITTED, with recorded gate
OPERATOR_APPROVED_LEAF_CRL_SCHEDULE, and is present on all three nodes. This is not
the operator-approved stopped fixture from the preceding capsule qualification.
Presence/result comparison is not validation of archived payload hashes or signatures.
Unequal cohorts are not by themselves corruption: NL2 was admitted later. Do not
delete RU/NL1 history or backfill NL2 to satisfy the synthetic equal-cohort gate.

## Actual installed paths and source

Targets are canonical RU185.251.89.19, NL1 185.10.158.212 and NL2 185.10.158.196,
not retired186.246.45.246 or excluded186.246.51.201. Current mapping follows the
[collector](../../control_plane/apps/console/collector.py), previous
[NL1 read-only acceptance](2026-11-13-amsterdam1-health.md) and owner-authorized
[NL2 trust/admission](2026-11-02-second-nl-ordinary.md#authorization-and-trust).
Existing strict SSH pins were used; NL2 uses the previously accepted dedicated
known_hosts_fleet_rehearsal_185_10_158_196 file, not a new scan or weakened SSH check.

- All node state roots: `/opt/apps/family_connect/friends-restricted/renewal-state`.
- RU coordinator: `/opt/apps/family_connect/friends-restricted/renewal-coordinator`.
- Effective RU credential-renewal unit references the existing serialization wrapper
  under `/var/lib/fc-profile-control/mesh-serialization-ea1bfc9/` and the fleet
  controller/runtime under `/var/lib/fc-profile-control/mesh2-fcb3116414571654/`.
- Selected RU/NL1 node-fleet.json and renewal sources are under that latter path;
  NL2 uses `/var/lib/fc-profile-control/mesh2-eb0b5e68e49d/`.
- All14 declared source-file hashes and their canonical aggregate match
  `e9fd31754bdf50c95842a1644f86ddb328b839ec1e0c9454daf08d3e9d17f0cc`.
  All configs bind the inspected state root. online_history.py is neither declared
  nor present. Source retention qualified on23 November is NOT installed.

Discovery also found older pair-only controller/node configs at the original
friends-restricted/renewal location. They are not the effective scheduled RU controller;
do not deploy or execute whichever configuration a broad filesystem search finds first.
RU fleet routes point to family-restricted on the two current NL addresses. Existing
forced-launcher metadata was observed, but no NL node RPC or end-to-end launcher
execution is claimed by this inventory. Installed manifest equality is not that test.

## Custody gaps and concrete next gate

All archives contain native service-barrier evidence; many also contain start-intent
files. Shapes include authority-request.json on RU and fenced rollback evidence,
including one rollback-registry-overlay.json. These are real installed differences,
not permission to expand the completed-stopped adapter by ignoring extra files.

The canonical coordinator history directory is absent.365 RU ledger entries have no
current/history-name counterpart. Five adjunct JSON files are also read in memory:
four expose an operation_id field; none is accepted as a full retained history record.
Recovery-prep/request/result subdirectories are only counted at this boundary, not
recursively interpreted. This is a scoped custody gap, not proof that every older
coordinator/approval byte is absent from every backup or operator store.

The current transaction has no top-level original approval/handoff envelope. Original
authorization custody remains NOT_ESTABLISHED; recorded gate strings are not replayable
approvals. Missing data must not be reconstructed, re-signed or silently waived.

NEXT bounded task, not started here: define and qualify lossless legacy-prefix custody
for these exact mixed cohorts, service-bearing archives and adjunct/fenced evidence.
Preserve every ledger/archive member and opaque legacy byte; distinguish preserved
from validated evidence and retain hard refusal of executable recovery/host resume.
Do not require invented historical coordinator records or empty journals. Later
current-state import, installed schema/live writer barrier, full-system recovery/off-host
custody and strict PostgreSQL/Patroni RPO0 gates still need independent qualification.

## Collector, tests and private evidence

[Standalone collector](../../scripts/control_ha_installed_inventory.py) and
[tests](../../tests/test_control_ha_installed_inventory.py):26 PASS /0 skips.
Checks cover no archive-payload reads, no content/mtime writes, arbitrary name/value
redaction, source mismatch, symlink ancestors/leaves, hardlinks/FIFOs/nested archives,
duplicate/malformed JSON, bounded reads/entries/metadata, file replacement/concurrent
changes, unequal cohorts, missing nodes and conflicting results. Existing recovery
adapters and production executors were not changed; historical PG suites were not rerun.
Six changed documentation files/1014 local links and whitespace checks PASS.

```sh
python -m pytest -q tests/test_control_ha_installed_inventory.py
python -m scripts.control_ha_installed_inventory --root /absolute/private/node-state \
  --coordinator /absolute/private/coordinator --config /absolute/private/node-fleet.json \
  --runtime /absolute/private/renewal > /private/evidence/host.json
```

Use the existing control/identity-lockfile environment. For hosts, stream this exact
stdlib source to `python3 -I -B -` through approved pinned SSH; do not install it or
invoke runtime_controller.py, online_cli.py, node.py or run_serialized_renewal.py.
Use umask077/private0700 evidence, a90s outer SSH deadline and the already reconciled
paths. There is no automatic SSH target discovery or remote write in the collector.
Reconcile the three private JSON documents with `reconcile({'RU': ..., 'NL1': ..., 'NL2': ...})`.
Operation-name hashes stay in private evidence; publish only aggregate counts.

Reader limits are4096 ledger/archive entries,128 entries per archive,1MiB per read
document,16MiB total read and32768 observed metadata entries. It rejects unsafe/racing
objects instead of following links or truncating. Before/after and final metadata
readback yielded NO_OBSERVED_CHANGE on all three nodes. Ordinary reads can update
filesystem access times and SSH audit logs; this is not a claim of bitwise unchanged
hosts. No lock, fsfreeze, writer pause, cryptographic archive audit or DB snapshot.

Final collector SHA256:
`323035f48bc156215085a0dcc28eb5b5fc1b85747b6ae7d0d51f3d5208ef40fe`.
Sanitized summary SHA256:
`5d46563f9bb296ec739ed81ab294bf11a9857f577dde4a41b93631afe989841f`.
Private receipts/times remain under
`/tmp/fc-control-ha-20261124/installed-inventory-qualified/`, outside Git.
Earlier inventory attempts remain retained: one unfamiliar filename was initially
counted/redacted, then identified as rollback-registry-overlay.json; the scheduled
gate enum was corrected to the exact native value before final collection. Neither
earlier projection is substituted for final evidence. No raw archive/profile/key/DB
payloads were exported, and no source capsule or private state is committed.

## Rollout, rollback and unrelated observation

No installed code changed. Latest known console remains
`sha256:5ce824159e9f206c27ba92185097857382aa5fec71678ce5e728423509d1446a`,
NL GeoIP collectors22 November20:53:48UTC; RU HTTP archive remains
`4e2df679761ba9e7af74128984ef2e19e8e7b228f1cc85b36d50be2b0bc24ce8`.
Android126/catalog9, signed/public artifacts and invitation versions were not changed
or requalified.8s/12s/paid120s and all-three-node ACK remain unchanged.

Rollback of this source-only collector is to stop using/revert it; no server restore,
service restart or old database replay is needed or authorized. Preserve private
receipts and every native journal. No HA rollout or full-system recovery PASS.

During scoped unit discovery the credential-renewal timer was active and its oneshot
inactive/success with exit0; inactive is normal for a completed oneshot. The separate
product-cert-renew.service was observed failed while its timer was active. This is
an uninvestigated, unrelated health observation, not evidence that the management
service is stopped or a reason to restart it. No corrective server action was taken.
