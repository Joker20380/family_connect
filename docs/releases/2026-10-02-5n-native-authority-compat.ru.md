# 5N-NATIVE-AUTHORITY-COMPAT — offline compatibility, 02.10.2026

## Verdict and scope

**5N-NATIVE-AUTHORITY-COMPAT = PASS**

Starting accepted HEAD: `4f482027d739b52bfab11ff0a796e9dd0dec692f`.
Implementation commit: `8b829971f4e75a1a584cebf9867eb0ae5d256129`
(`fix(authority-check): derive negative floors from validated claims`).
Following documentation-only checkpoint does not change artifact inputs.

No deployment, authority renewal/signing, NL/RU runtime/service start, remote native
checker execution, HTTP activation, Redmi, Android full build, APK, push, DIAG-1,
distributed beta or FIELD-1. Attempt #11 remains historically failed/rolled back.
This gate explains its previously unknown prerequisite failure; it does not turn
that deployment or its unreached gates into PASS.

Protected ignored evidence: `state-client-build/native-authority-compat/`.
Pre-existing work is snapshotted before edits, including all10 dirty/untracked entry
files and the empty index. Only task-owned source/tests/new guide/report and additive
STATUS/PLAN entries are committed. Other report/runbook bytes remain unchanged.

## Exact checker and provenance

Attempt #11 invoked on NL:

- Binary: `/opt/apps/family_connect/restricted-materials-stage-20261001/bin/native-authority-check`.
- Gateway input: `/opt/apps/family_connect/restricted-materials-stage-20261001/gateway.json`.
- Owner validation certificate: `/opt/apps/family_connect/restricted-materials-stage-20261001/canary-validation.pem`.
- Original source: retained `/tmp/fc-authority-native-check.go`,60 lines, untracked
  operator helper, importing `carrier/familysession` and its `reliablestream` dependency.
- Original binary SHA256:
  `8f59485fb8976f079b081e0dd355177102053fb2546bf33566e582cbbb9c3c15`.
- Toolchain: Go1.26.0/linux-amd64, CGO_ENABLED=0, GOAMD64=v1, `-trimpath`.
  Embedded build info says `command-line-arguments` and has **no VCS revision**.
- Historical authority preparation associates the source context with
  `584d252552ebd61e819032ec9453a52805c9bb5b`; that is retained operational provenance,
  not an embedded stamp. `familysession`/`reliablestream` have no diff from that
  checkpoint to accepted4f48202. The original helper was not in either Git tree.

Read-only retrieval confirms deployed bytes equal the retained local binary.
Rebuilding the unchanged original main with the **current accepted libraries** and
the same toolchain/flags produces the **identical full SHA256** above. This is
stronger than a timestamp/version assertion: stale native library behavior does
not explain the failure. The defect is present in the retained checker source.
The regression-only original source is now preserved as
`carrier/cmd/native-authority-check/testdata/legacy.go.txt`; never deploy that fixture.

## Private material and exact reproduction

With explicit tool approval, read-only SFTP retrieved the existing checker and
preserved #11 gateway profile/owner certificate to an ignored owner-only local
directory. The gateway profile contains a private key and stays private, outside
Git, CI and output. No issuer private key or owner-device private key was exported.
No production file was edited and no remote checker or application service was started.
Public delegation2 from the retained #11 offline signing output is reused unchanged.
No authority is regenerated or resigned for this investigation.

Material verification confirms delegation2, owner certificate revision2, gateway
certificate revision1, global revision floor1, CRL19/floor19, same Family/gateway/
issuer and exact issue/expiry classes from #11. Grant revision2/expiry and sole-owner
membership are corroborated by the retained #11 renewal receipt, not a new live DB
query. Python directly rechecks the actual public delegation signature, canonical
issuer, certificate chains/claims/key binding and signed CRL/validity at attempt time.
Issuer-private-key continuity remains evidence from #11; it is not revalidated by
exporting the online CA key.

CRL19 expired02.10 12:12:08UTC. Replaying at today's clock alone would stop on expiry
and would **not** attribute the original failure. Local GDB therefore substitutes
`time.Now` returns inside the offline process with **02.10 11:57:10UTC**. It does
not change the executable, input bytes, host clock or validation predicates. This
debugger-only replay is never shipped as an operator flag or production bypass.
Initial sandbox ptrace denial and debugger-expression setup failure were local
tooling issues, not successful executions or production attempts.

Before any validator/checker fix:

| Local execution, same #11 material/attempt time | Result |
| --- | --- |
| Exact original binary | exit1, original suppressed output |
| Byte-identical current-library rebuild | exit1 |
| Original helper with **observability-only** error labeling | exit1, `negative_revision_unexpected_acceptance` |

The diagnostic change only labels which existing negative returned an error; it
does not change inputs, loops, callback behavior or acceptance. Reaching that branch
also proves preceding actual owner/gateway chain and binding positives and the
wrong-Family negative completed. The original CRL negative was not yet reached.
Durable replay receipts retain binary hashes, process-clock scope, exit and safe
classification without certificates, IDs, proofs or key contents.

## Exact failed predicate / root cause

**Classification D: operator-checker negative-fixture assumption bug.** Not stale
binary only, not a production native authorization bug, not producer/Python/native
contract disagreement.

The old negative constructs `changed.MinimumRevision = profile.MinimumRevision + 1`.
For #11: original floor1 → test floor2; the signed owner revision is2. Native policy
correctly rejects only `signed_revision < required_floor`, so **2 >= 2 is accepted**.
The helper then treats successful native admission as failure of its purportedly
invalid fixture and exits1. The real renewed authority was not rejected by positive
native admission. There is no legitimate revision1-only rule to relax.

The source audit finds no production special case requiring revision==1/revision<=1.
`wholedevice/testdata/delivery-check.go`'s minimum-revision1 assertion describes its
fixture profile floor, not an owner-revision ceiling. Existing native/Python
delivery tests already issue owner revision2. Global floor and grant revision need
not be equal; they remain independent accepted contract values.

## Minimal runtime impact and safe observability

The fix adds the tracked operator under `carrier/cmd/native-authority-check`:

- Derive the rejecting revision floor from **validated signed owner revision+1**,
  not the profile minimum; do not special-case1/2 or alter the native comparator.
- The same independently reproduced negative-fixture problem exists for a signed
  CRL newer than its configured floor and for the all-zero valid Family matching
  the old wrong-Family constant. Derive CRL negative from signed number+1 and choose
  a genuinely different Family. Legacy/new synthetic tests reproduce/fix both.
- Keep all positive chain/binding/revocation checks and all three negatives.
  Integer successor overflow fails closed, never wraps or silently skips a check.
- Emit only fixed safe JSON fields: `version,status,stage,reason,object,comparison`.
  No raw X.509/OS errors, identifiers, paths, certificate bodies or private material.

**No changes** to `carrier/familysession`, `carrier/wholedevice`, Python producer,
Android cache runtime, cryptographic format, TTL/security policy or admission.
Only an Android unit test is added. Existing HTTP/sync artifacts remain unchanged.

The standalone `scripts/native_authority_acceptance.py` pins the binary, bounds
execution, validates an allowlisted bounded native result and exit consistency,
and persists/fsyncs it before returning any verdict to future orchestration.
Raw stderr/unknown response content is discarded. Timeout, malformed/oversized
output, changed/wrong artifact, conflicting result and persistence errors forbid
PASS. Existing receipts cannot be overwritten or replayed automatically. Future
deployment must use this adapter before rollback; it is **not installed now**.
[Build/execution contract](../../deploy/friends/restricted/NATIVE_AUTHORITY.md).

## Semantic comparison and tests

| Contract / case | Existing enforcement and observed result |
| --- | --- |
| Delegation1/grant1/CRL1 | Full synthetic producer→native→delivery PASS; legacy PASS |
| Delegation2/grant2/CRL2 | Normal monotonic renewal PASS; legacy helper FAIL |
| Delegation2/grant2/CRL19 | #11-equivalent fixture: Python PASS; legacy FAIL; fixed native and both delivery parsing paths PASS |
| Actual unchanged #11 snapshot at attempt time | Old exit1; clean fixed checker exit0, complete positive+negative PASS |
| Actual #11 snapshot at actual current time | Fixed checker still exit1/configuration rejected due expired material |
| Future valid revision37/sequence37/CRL43 | PASS, no initial-revision hard coding |
| Delegation2/grant1 with floor1/current membership | PASS by contract; sequence is not a grant floor |
| Grant1 with required minimum revision2 | Producer/native rejection |
| Revision rollback2→1 | Rejected below required floor, signed revocation of old leaf, and persistent cache rollback guards |
| Signed CRL below required floor | Native rejection; delivery/cache retained-floor checks unchanged |
| Signed CRL19 with lower floor18 | Valid lower-bound relationship; fixed helper PASS, legacy false failure reproduced |
| Same revision, conflicting content | Cache rejects conflicting same-issued content; delivery rejects revision/certificate mismatch; legitimate later refresh remains allowed |
| Current-revision revoked owner | Producer denied, new signed CRL revokes leaf, native and delivery reject |
| Expired delegation/grant/certificate/issuer/CRL | Respective producer/native rejection; no grace added |
| Stale challenge after grant revision increases | Producer rejection |
| Wrong Family/gateway/issuer bindings | Existing checks retained; negative tests reject |

Delegation signatures/sequence are checked by Python and shared delivery parser;
DB membership/admission/expiry by producer; native Family TLS receives signed X.509
claims and required floors, not the grant DB or delegation envelope. It is stateless
and cannot invent retained revision history. `RestrictedCache` preserves delegation,
revision, CRL and issuance floors across restart. This layering is unchanged.

Verification:

- **82 Python tests PASS,0 skips**, including the exact clean-built checker in the
  cross-language matrix; final packaged run2.01s. Native tools run outside checkout.
- Go checker matrix uses deterministic virtual time/synthetic key seeds; shared
  `familysession`/`wholedevice` tests also run. Initial broad run skipped the opt-in
  ProductStore fixture; final run supplies freshly generated disposable fixtures
  and repeats all three packages: **56 tests/subtests PASS,0 failures/skips**.
  No production fixture is used in this test suite.
- **7 JVM RestrictedCache tests PASS**, including1→2/CRL19, future revisions,
  rollback, conflicting content and persistence; JDK17.0.20.1, no Android full build.
- Safe receipts, malformed/duplicate/conflicting output, timeout, artifact pin,
  file+directory fsync order, persistence failure and no-replay tests PASS.
- Source/docs guards and `git diff --check` PASS. Historical actual-time expiry is
  intentionally a failing prerequisite test, durably classified, not a test failure.

## Clean artifact provenance

Two separate clean `git archive` exports of implementation commit
`8b829971f4e75a1a584cebf9867eb0ae5d256129`, no dirty overlay, no production material:

- Go1.26.0/linux-amd64/v1; CGO disabled, `-trimpath -buildvcs=false`, module network
  access disabled. Builds execute in separate temporary source directories.
-14 inventoried source files, exact Git archive hash, Go/compiler/assembler/linker
  hashes and build metadata recorded in each `provenance.json`.
- Both complete manifests and artifact hashes are identical.
- Checker SHA256:
  `a1df5f88a103340a6ba9d67ae8842147afd99d430fba6b30b8ba7b212373ce90`.
- Standalone acceptance adapter SHA256:
  `a4408bf29c3c268c469c065e1b9315d04b8a69560dc8ba8caac052c11a82652d`.
- Local paths: `state-client-build/native-authority-compat/build-one/` and
  `state-client-build/native-authority-compat/build-two/`. Built/tested only, not
  installed on either server, distributed or signed as a release.

## Final boundary

No production configuration, authority, floor, DB, runtime or service was changed.
Only approved read-only SFTP retrieval occurred; all executions/builds/replays were
local. The last production state remains #11 rollback with authority history2/2/19;
its expired short-lived material is not made valid by this offline gate. No new
production health or port-availability claim is made. Phone untouched.

No app version/install/public/invitation change; those versions were not reverified.
Unrelated work preserved, task-only local commits, no push. STOP: a separate
authorization/acceptance is needed before any deployment attempt #12.
