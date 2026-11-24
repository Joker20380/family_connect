# 24 November 2026 — original schedule provenance: decision boundary

This continues the selected HA-02 journal/current-operation task after
[certificate-content qualification](2026-11-24-control-ha-certificate-delta.md).
**Investigation conclusion, not implementation/recovery acceptance:** the original
approval cannot be reconstructed from the examined native record and retained sources.
A newly identified independent source could change that conclusion; no exhaustive
search of every backup/account is claimed. Do not repeat the same diagnostic loop.

## What was actually checked

No SSH, service operation, production read/write, private-key/profile/DB export or
execution of a retained staging script occurred in this turn. Local evidence was read
through the existing bounded no-follow reader with metadata rechecks. Python staging
source was parsed as AST, not imported. Six selected JSON trees were traversed with
depth/node limits without emitting their payloads or dynamic identifiers.

The installed source was not guessed from the current development branch. The14-module
manifest was reconstructed from Git commit `fcb311641457165405dc85fa070aaa4b1464e185`
using that commit's packager module list. SHA256
`e9fd31754bdf50c95842a1644f86ddb328b839ec1e0c9454daf08d3e9d17f0cc`
matches the prior three-host observations at24 November00:34:17–00:34:20UTC.
Those are previous observations, **not a new health or deployment check**.

| Exact installed source | SHA256 | Relevant behavior |
| --- | --- | --- |
| production_controller.py |1116e1949fd07b82ae91bba8b2e525490a53dc511fc61218a8145934f9162f8b |Scheduled branch consumes approved_leaf_crl_schedule boolean and stores the derived gate, not original controller config/approval |
| runtime_controller.py |59604820123def4c6b705fdddcc3075613b7360134f7cc1c4714e68f61f28fb6 |Reads the flag from controller config and passes it to the controller; this is not retained independent owner authorization |

The native initial record carries schema, operation_id, state, first_cause, before and
its digest, previous, acquired, quiesced, commit_decided and gate. Later transition
receipts do not reconstruct who approved the original flag/configuration. Present
configuration equality and the string OPERATOR_APPROVED_LEAF_CRL_SCHEDULE are not a
replacement for that evidence. The
[historical activation report](2026-11-03-second-nl-mesh.md#permanent-fleet-activation-and-live-data-plane)
documents the owner's requested rollout, but is not a per-operation bound approval artifact.

Seven selected retained artifacts were examined: the fleet staging source, RU/NL
staging receipts, initial/close-idle/reset-repeat source manifests, and the committed
recovery-package receipt. The six JSON trees contain no approval/controller-config
artifact. All three source manifests explicitly have production_configuration=absent
and operation_permit=null. Package provenance/installation receipts do not substitute
for historical owner consent. This list defines the search boundary; other private
backups were not recursively searched or declared absent.

Private sanitized audit receipts are retained under
`/tmp/fc-control-ha-20261124/provenance-decision/`: `retained-artifacts.json`,
`nested-receipt-fields.json`, `exact-installed-source.json`. Directories0700/files0600;
raw private sources remain in their existing ignored custody. These local temporary
receipts are not independent off-host disaster-recovery storage.

## Decision requested, not yet accepted

Two defensible routes remain within the selected journal task:

1. Identify independently retained original approval/configuration evidence and bind
   it to the installed operation. Do not manufacture it from the current flag, an
   old start intent or this investigation. A concrete new source is needed before
   repeating the search.
2. **Recommended:** explicitly approve development of a forward-only current-state
   checkpoint contract. The owner authorizes a new recovery starting point, not the
   old operation retroactively. Old native journals remain immutable historical
   evidence with no replay/resume authority. Their original approval remains recorded
   as NOT_ESTABLISHED; no old gate changes to PASS.

The requested decision is to develop/qualify route2 and replace the unattainable
historical-approval prerequisite for that **new** contract, not to weaken the old
auditor or deploy anything. This report itself and the preceding generic continuation
are not that new authorization. Existing exact-equality import gates remain unchanged.

## Proposed route2 acceptance conditions

- A new explicit current authorization binds scope, source/config/anchor identities,
  operation/checkpoint identity, expiry and intended action; it cannot authorize old
  operations, a new issuer/key, lost revocation floors or automatic host resume.
- Preserve complete unequal legacy ledgers/archives, including unknown/pending evidence,
  as opaque history. Do not execute them, equalize cohorts, delete receipts or re-sign
  old records. Pending/uncertain active writers still prevent capture acceptance.
- Capture current DB/files/publications separately from the immutable renewal baseline
  using a qualified cross-store writer barrier. File stability and certificate-content
  compatibility alone are not that barrier. Discover actual writers/schemas before
  choosing a production maintenance procedure; no guessed outage duration is approved.
- Preserve current consumed challenges, membership/paid/revocation state, sequences and
  all mandatory stores/keys/checkpoints. Do not require reconstructing an already
  consumed proof from certificate bytes, and do not use missing history to invent
  membership or payment entitlement. Current-state recovery must preserve the real state.
- Perform isolated, source-removed full restore and stale-state/floor/replay refusals
  before any activation. Independent off-host custody, replication/quorum/RPO0 and the
  remaining HA gates still apply. A signed document alone does not close stage2.

These are proposed requirements, not a new implemented adapter, passed test suite,
production snapshot or approval to start the next queued block. Before real capture,
the exact maintenance scope and failure/rollback path must be reviewed separately.

## Qualification, stage and rollback

This turn changes documentation only. Evidence checks: exact14-module hash
reconstruction, comparison to all three existing host receipts, bounded seven-artifact
inspection and no-observed-change metadata checks. Source175-test PASS belongs to
`cc4be524c6ece6e9852409fa79800978a8a44e55`; it was **not rerun or counted as a new gate**.
Documentation links/content/whitespace are checked separately for this checkpoint.
Final documentation check:5 changed files/958 local links, zero errors; whitespace
passes. External URLs were not freshly fetched. No runtime tests were required for
this documentation-only decision checkpoint.

Selected task remains IN_PROGRESS / OWNER DECISION REQUIRED, not journal COMPLETE.
The four [stage2 exit blocks](../control-ha.md#когда-заканчивается-этап-2) are unchanged:
journals partial, installed schemas/writer barrier, full off-host/current-state recovery,
strict PostgreSQL/Patroni quorum/RPO0 unqualified. HA-03..05 follow and RU dependence
persists. No credible calendar ETA follows from this investigation.

No runtime/source implementation, deployment, host/service/timer/configuration/policy,
release/catalog/publication or version change. Known installed console image
`sha256:5ce824159e9f206c27ba92185097857382aa5fec71678ce5e728423509d1446a`, RU HTTP archive
`4e2df679761ba9e7af74128984ef2e19e8e7b228f1cc85b36d50be2b0bc24ce8`, NL GeoIP22 November,
Android126/catalog9,8/12/120s and all-three-node ACK remain previous accepted versions/
policy, not newly measured results. Public/invitation versions remain unchanged.

Rollback now: stop/revert this documentation proposal in a new ordinary source commit;
there is no installed change to reverse. During a future qualified capture, abort
before cutover must leave the existing system authoritative. After subsequent writes,
never restore the old renewal/SQLite baseline as a rollback; require fenced recovery
of current state. No reset/force push or journal repair is part of either route.
