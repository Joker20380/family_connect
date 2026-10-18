# CRL-WRITER-SAFETY-1 — PARTIAL / source-only, not accepted

## Decision

`CRL-WRITER-SAFETY-1=PARTIAL`. The key-mismatch defect is reproduced on the exact
deployed writer and corrected in an isolated source derivative. The full requested
transaction/publication acceptance is **not** satisfied; no accepted validation
commit or deployment-ready candidate is created.

**First unclosed boundary:** `RU_COMMITTED → NL_COMMITTED` has no common
reader-visible commit barrier. Injected NL promote failure leaves a valid RU CRL
N+1 and a valid NL CRL N. Retry rolls forward the same operation/sequence, but
recoverability is not distributed atomic visibility. Existing readers independently
load the two files. No claim that every failure leaves the previous RU sequence
unchanged after a new CRL has already become active.

Exactly next operation: **source-only RU/NL committed-state publication and reader
barrier design, followed by fault acceptance**, on this exact baseline and retained
counterexample. Do not resume canary-policy implementation, deploy, issue an identity,
renew credentials or run a live canary automatically.

## Exact baseline and artifacts

Capsule: `state-client-build/field65-export16/crl-writer-safety-1/manifest.json`.
The prior provenance capsule and all65 sealed files were rechecked; twelve archive
source members were copied unchanged to isolated `baseline/` and modified only in
isolated `source/`. Main checkout's pre-existing product changes were preserved.
No fresh production read was made; deployed identity is inherited from the verified
provenance report, not inferred from current HEAD or directory name.

| Identity | Value |
|---|---|
| Exact deployed RU/NL zipapp | `9faaa1c27f534e71774f5b4f34872e87747f391409c4958562694f07f86d64d1` |
| Prior manifest | `caf9b0540dd767ab02de854aec5ced3296ecc4082c40c77b17536a9c3ff37800` |
| Experimental source-tree SHA256 | `74951952999062d973a3168d07dc1334eb01208656d60b3b90afd873576f84fb` |
| Experimental zipapp SHA256 | `54c9715cdf6501ed87155f82e7e5ac9d593d446fee17310f7fe43be84e54b61b` |
| Frozen gateway unchanged | `53beb661cab014c32494fa8d7384f9565300311ef467e62ae9f8c20201e5138f` |
| Frozen gateway source, not rebuilt | `134083d87773dacc038c9593afdaff0c57ea951d` |
| This manifest | `f1c959ba5e842f41a2574df42741d944bfc2aa9926f795a4eb7f9d6964860b02` |

Source identity is SHA256 of the sorted member-hash map, **not a Git commit**.
Two deterministic local zipapp builds match byte-for-byte. Archive is labelled
`unaccepted`; it must not be installed. Validation commit is deferred because the
user required it after PASS. Rollback zipapp is an exact copy of the sealed baseline.

## Before / after

Baseline fixture: issuer A, key B, valid CRL1 and committed SQLite sequence1.
Actual baseline writer replaces RU with invalid-signature CRL2 and commits sequence2;
actual NL receiver rejects. No files were manually changed to simulate the result.
This remains a disposable-PKI fixture defect, not a production incident.

Patched mismatch fixture returns `ISSUER_SIGNING_KEY_MISMATCH`:

- RU current hash before=after; issuer signature valid.
- SQLite bytes and committed sequence before=after.
- NL requests=0; NL current hash before=after.
- No active publication mutation. Only safe failure receipt metadata is permitted.

Normal matching-key fixture validates and stages candidate bytes, independently
validates them on NL, commits N+1, and reconciles equal RU/NL hashes. Initial normal
CRL bytes match baseline with identical PKI/clock. Existing entries are retained as
a union, including dates/extensions. Duplicate periodic publication still advances
sequence, as in the baseline; unknown/untracked serials are not magically revocable.

## Implementation and acceptance inventory

| Requested result | Result / evidence |
|---|---|
| EXACT_BASELINE | PASS, exact sealed archive/import closure |
| BASELINE_DEFECT_REPRODUCTION | PASS, `receipts/before.json` |
| ISSUER_KEY_PREFLIGHT | PASS, Ed25519 type + canonical SPKI comparison + sign/verify capability |
| CANDIDATE_INDEPENDENT_VALIDATION | PASS locally, reparse/signature/issuer/number/time/AKI if present/exact intended entries |
| SEQUENCE_TRANSACTION | PARTIAL: current signed CRL authoritative; DB mirror recoverable via marker, not indivisible to all existing readers |
| STAGING_AND_ATOMIC_COMMIT | PASS local fixture fsync/rename; private0700/0600 staging; no unverified current |
| RU_NL_PUBLICATION_CONTRACT | PARTIAL: authenticated stage/promote/finish + CAS; observable cross-replica skew remains |
| CRASH_RECOVERY | PASS modeled boundaries; same-op rollforward; expired pending transaction requires explicit operator handling |
| CONCURRENCY_AND_LOCKING | PASS tested thread/fork/local-filesystem cases; no network wait under flock; NFS/arbitrary authority edits unproven |
| EXISTING_REVOCATION_PRESERVATION | PASS, no lost existing entries or altered dates/reasons |
| TYPED_ERRORS_AND_RECEIPTS | Implemented; private atomic bounded receipts; first failure retained; receipt I/O cannot undo protocol result |
| FAILURE_MATRIX | 30 focused tests ×3 PASS; global atomicity counterexample retained, not counted as safety PASS |
| KEY_MISMATCH_REGRESSION | PASS all critical unchanged-state/NLrequests0 assertions |
| NORMAL_SUCCESS_PATH | PASS local RU/NL equality, N+1, byte-compatible CRL; actual packaged receiver stdin protocol PASS |
| FROZEN_GATEWAY_REVOCATION | PASS exact executable Family TLS/RequestAuthorizer; unrelated valid profile still accepted |
| NON_ACTIVATED_DEVICE_REVOCATION | SUPPORTED_AFTER_SAFETY_FIX in local tracked-device TLS fixture, not issuance-policy acceptance |
| CHAT/PUBLISHER_NEGATIVE | Local exact API negatives unchanged; external Store/mailbox/notification runtime NOT_RUN |
| SECURITY_AND_PRIVACY | PASS checked source/permissions/receipt/PEM-scan scope; universal TOCTOU/privileged-attacker proof not claimed |
| BASELINE_DIFFERENTIAL | NO_NEW_FAILURES in tested three-module subset; both71 passed/15 skipped/1 identical harness failure |
| LOCAL_CANDIDATE | Preserved unaccepted source/archive/diffs; no accepted validation commit |
| DEPLOYMENT_PLAN | Prepared, explicitly BLOCKED; no execution |
| PRODUCTION_UNCHANGED | All task-induced production actions0; no owner/live actions |

### Important limits

The frozen executable test uses a loopback proxy sink and disposable credentials.
Before revoke and for an unrelated valid profile after revoke, authenticated HTTP503
is evidence of successful Family TLS/RequestAuthorizer, **not** seed/bootstrap/media/
Mux/lease success. The revoked profile is rejected by that same gateway process.
No production keys or room URLs enter the fixture; no live Telemost calls occur.

Local exact API checks cover eligibility, chat challenge/registration, routed member
snapshot, publisher configuration and service notices with no ordinary device/grant
rows. They do not execute external mailbox/Store/notification services. No writer code
creates or cleans ordinary user/chat state. Unchanged reconciliation immediately
revokes tracked nonactivated leaves; a usable canary lifecycle still needs later policy.

Final differential's common failure is `test_http_routes_bounds_and_disabled_feature`:
the repository HTTP module imports `control.friends.chat`, absent from the exact
writer archive. This is a harness/import-closure coverage limitation, not a new
deployed product failure. Earlier candidate helper/legacy compatibility failures
were corrected; their logs remain retained. Full historical diagnostic assertions,
busy-wire/source-guard suites were not run or claimed fixed/green.

Python thread/fork concurrency matrix repeated three times is not a Go race-detector
run. Fork/_exit and fault injection do not prove real power-loss or NFS durability.
No test claims hostile root/ancestor-directory TOCTOU immunity or automatic recovery
from a permanently failed/expired unresolved distributed transaction.

## Patch stack and runbooks

Capsule contains `key-preflight.diff`, `transactional-write.diff`,
`publication-commit.diff`, `recovery.diff`, `tests.diff`, `docs.diff` under patches/,
plus full/source-only diffs, `scope.txt`, `FEATURE-INVENTORY.md`,
`TRANSACTION-CONTRACT.md`, `RECOVERY-CONTRACT.md`, `FAILURE-MATRIX.md`,
`DEPLOYMENT-PLAN.md`, build/source identities, exact baseline rollback and SHA256SUMS.
Diff categories have disjoint source-file ownership; recovery.diff contains the
coordinator/recovery logic. These are evidence, not an instruction to apply them to HEAD.

Public API, profile/Family/directory formats unchanged. Internal operator SSH exchange
adds schema1 stage/promote/finish; legacy envelope still validates before local
promotion and cannot bypass a pending transaction. This is not backward-compatible
distributed coordination with an old RU writer; matched upgrade and reader behaviour
must be accepted separately. No new network endpoint or trust root.

Future rollback must distinguish code rollback before exposure from forward CRL
reconciliation after exposure. Never lower an already exposed CRLNumber to restore
an old file. Preserve first cause and markers; no timer/restart loop is authorized.

## Mandatory final counters

`PRODUCTION_CRL_WRITES=0`; `PRODUCTION_CRL_SEQUENCE_CHANGES=0`;
`PRODUCTION_GRANTS_CREATED=0`; `PRODUCTION_IDENTITIES_CREATED=0`;
`PRODUCTION_DATABASE_MUTATIONS=0`; `PRODUCTION_DEPLOYMENT=0`;
`PRODUCTION_RESTART=0`; `PRODUCTION_RENEWAL=0`; `OWNER_CONNECT=0`;
`LIVE_TELEMOST_ROOM=0`.

`PRODUCTION_IDENTITY_CREATED=NO`; `DEPLOYMENT=NOT_RUN`;
`OWNER_CONNECT=NOT_RUN`; `ATTEMPT_CONSUMED=NO`;
`PUBLIC_RELEASE=NOT_RUN`; `REAL_RESTRICTED_NETWORK_FIELD=NOT_RUN`.
These are task-induced counters; no inference about autonomous production changes
is made without a fresh runtime observation.
