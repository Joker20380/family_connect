# 24 November 2026 — both forward-checkpoint publications

Historical source checkpointb105033d. The subsequent
[source-custody checkpoint](2026-11-24-control-ha-forward-sources.md) also requires saved
renewal source/config bytes. Results below describe this earlier publication-only change.

## Scope and result

Continuation of the selected CONTROL-HA-20261123 journal/current-state task from
source38a3ac27, under the owner's development-only authorization. No SSH, server
changes, writer stops, production signing, capture/import/resume or queued next block.

The [forward-checkpoint API](../../scripts/control_ha_forward_checkpoint.py) no longer
accepts a secondary publication on its hash alone. The fresh signed request now pins
two distinct gateway identities and both signed-delegation byte hashes. Verification
requires the corresponding authority bytes and independently retained minimum
delegation sequences for **each** gateway. Those floors cannot be inferred from the
supplied snapshot when independent custody is missing.

This is a tightening of the unpublished v1 development format, not a released protocol
migration. Prior requests without `gateways` fail closed; there is no default, silent
upgrade, re-signing or import compatibility switch. No real approvals were issued by
either implementation. All signing in tests uses temporary test keys.

## Validation and limits

- Primary delegation must equal the current capsule's signed envelope, and the primary
  publication must equal its issuer directory. Both captured delegation byte strings
  are pinned by the new authorization; neither is read from old journals by the API.
- Existing native `restricted.delegation` verifies the offline-root signature, CA,
  gateway/family/revision fields and validity at both capture and verification time.
  The secondary must share the primary's exact CA, family and minimum revision.
- Existing native `restricted.directory` checks each directory's own gateway/family,
  supported transport/URL, seed uniqueness, shape and freshness at both instants.
  Native directory maximum lifetime is14400seconds, not the120second paid receiver
  lease. This change modifies neither limit. New authorization does not extend a
  publication's validity or legitimize a wrong node, different family or stale delegate.
- Each authority sequence must meet its independently supplied floor, regardless of
  the newly authorized checkpoint sequence. Existing checkpoint/CRL floors, signatures,
  current-state capsule, receiver/maintenance and opaque history checks remain in place.
- Public material maps are copied before hash/semantic checks and on result creation.
  Caller map mutation during validation cannot substitute bytes after their pin check.
  `QualifiedCheckpoint` retains both exact delegation/publication byte strings without
  printing them; `publication_semantics=BOTH_GATEWAYS_CHECKED_OFFLINE`.

This closes **offline publication-content validation**, not proof of what a live host
is serving, installed source/configuration attestation, coherent writer capture or full
gateway leaf/private-key recovery. Returned limits still include activation FORBIDDEN,
import/resume NOT_AUTHORIZED, live publication NOT_ATTESTED and full recovery
NOT_QUALIFIED. Existing historical auditors/importers and production code are unchanged.
The authority/publication sidecars must accompany their pinned request; hashes alone
do not reconstruct missing bytes. They do not replace the missing full-store/key backup.

## Qualification

Focused tests cover native two-node material, independent authority floors, wrong root
signatures, correctly root-signed but wrong gateway/family/CA/revision, missing/aliased
nodes, expired/future/overlong/malformed directories, duplicate seeds and documents,
capture-time consistency, request substitution and mutable input maps. Integration
tests confirm even a fresh valid checkpoint signature cannot make invalid secondary
publication content acceptable. Old request shapes fail closed.

The existing native post-renewal/source-removed fixture now reads **both current issuer
envelopes** through the allowed native material names. After deleting the source,
both public delegations/directories, all captured DB/artifact bytes and consumed-proof
refusal/fresh-proof issuance survive. This is still a local isolated fixture, not
production/off-host acceptance. No raw private evidence, keys, DBs or capsules in Git.

Final local qualification: **219passed,0failed,0skipped** in34.28seconds:
forward checkpoint86, publication semantics77, unchanged current-audit regression56.

```sh
/tmp/fc-control-ha-20261123/venv/bin/python -m pytest -q \
  tests/test_control_ha_forward_checkpoint.py \
  tests/test_control_ha_forward_publications.py \
  tests/test_control_ha_current_audit.py
```

The existing environment uses the control/identity lockfiles; no dependency change.
These focused gates do not claim PostgreSQL, full-store restore or live acceptance.
Documentation checker:6files,970links,0errors; external URLs inventoried, not fetched.
`git diff --check` passes. Safe sources/tests/docs only; no runtime artifacts in commit.
Private logs/JUnit: `/tmp/fc-control-ha-20261124/forward-publications/`.
Earlier251 tests/3 PostgreSQL skips belong to38a3ac27, not a new result for this turn.

## Stage2 remainder and rollback

The fixed [four-block acceptance checklist](../control-ha.md#когда-заканчивается-этап-2)
remains the definition of completion:

1. Finish the selected journal/current-state block: actual independently authorized
   current inputs, source/publication/capture binding, not another attempt to reconstruct
   missing historical consent. Offline content/signature checks are implemented.
2. Qualify installed schemas and all real writers/CLI/timers, and a coherent cross-store
   capture barrier. No production capture/writer stop authorized by this continuation.
3. Preserve every mandatory store/file/key/checkpoint independently off-host and perform
   full current-state recovery after acknowledged writes, with stale-restore refusal.
4. Qualify strict PostgreSQL/Patroni primary loss/return, quorum refusal and RPO0.

Thus three large integration blocks plus the remainder of the first remain—not one or
two minor patches. There is no evidence-backed calendar ETA before schema/writer and
recovery qualification plus a separately reviewed capture window. Do not count commits,
test cases or new letters as percentage completion. No automatic switch to the next
queued block. HA-03 fencing, HA-04 failover and HA-05 cutover still follow HA-02.

No installed/deployed/public/invitation version change. Known console image
`sha256:5ce824159e9f206c27ba92185097857382aa5fec71678ce5e728423509d1446a`, RU HTTP archive
`4e2df679761ba9e7af74128984ef2e19e8e7b228f1cc85b36d50be2b0bc24ce8`, NL GeoIP22 November,
Android126/catalog9 and8/12/120s/all-three-node ACK remain previous accepted state,
not fresh health measurements. RU independence is not achieved by these source changes.

Rollback: stop using this offline API or revert the source checkpoint in a new ordinary
commit. There is no server change to undo. Do not restore obsolete SQLite/renewal state
over later writes, weaken signature/floor checks, replay old archives or force-push.
Future failed capture must abort before cutover, preserving the existing authority;
recovery after new writes requires current data and fencing, not stale-baseline rollback.
