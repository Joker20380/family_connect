# CURRENT4H-EXPIRED-PREDECESSOR-RECOVERY-1

**RESULT: RECOVERY_PATH_IMPLEMENTED_AND_LOCALLY_VERIFIED**

Implementation and local acceptance only. **PRODUCTION_ACTIONS=0**.
No SSH/ADB, production key access/signing/publication, gateway starts, owner actions,
gateway executable/APK/supervisor changes, trust/TTL/policy changes or main merge.
This does **not** mean ENVIRONMENT_RESTORED. Historical production acceptance remains
FAIL; HISTORICAL_CAUSAL_BINDING=NOT_PROVEN; DEVICE_ACCEPTANCE=NOT_RUN.

## Exact base and derivative

| Identity | Value |
|---|---|
| Review starting point | `36705eaaae165d64d9d1ce756867ed3fc37f84ce` |
| Actual controller source | `9423d45ee013b349f342a81be502757b17b3fbf2` |
| Accepted current-policy archive SHA256 | `5fa24f5383e3f64c6ce7368e807972a6a4e4e9d832268feabefb9fea396c0e00` |
| Accepted management source-map SHA256 | `107d1c4219e13fdb91283b9e34f01951f95436a30c9b155f57ea427041221a5b` |
| Cumulative 299-file source inventory digest | `338faa75b96ff7ad3eb0d961e1cfa47d79eb75e60d285165cacec9ddf7df3e8b` |
| Prepared 13-module management source-map SHA256 | `5109a7c92ddd1937fe75ed7199866855a8cc20279bc226c35475d4cc81330145` |
| Signed cumulative client, rehashed unchanged | `3c733d2fc3a0ec377143b668244a4c7d6619ff24abe024da4ee9bfe31d140513` |
| Preserved baseline gateway identity | `21f0a0fdc27b50c00ea922f0b716516e2422aedf1b3797369718f7d00070509a` |

Used the retained current-policy capsule's MAINTENANCE-CONTRACT,
OFFLINE-SIGNING-HANDOFF and VALIDITY-POLICY, not root main, legacy issuer5→6 or the
experimental CRL writer. Verified the supplied archive, not all sealed entries.
Original dirty root status is byte-identical to the entry snapshot. Frozen source
and binary artifacts were not edited. No loaded-server hash was read in this task.
Publication commit identity is not an APK or gateway source/build identity.

Public review materials: [README / reproduction](../../research/current4h-expired-recovery-20261015/README.md),
[source manifest](../../research/current4h-expired-recovery-20261015/source-manifest.json),
[actual delta](../../research/current4h-expired-recovery-20261015/recovery.patch),
[complete next-operation runbook](../../research/current4h-expired-recovery-20261015/RUNBOOK.md),
[bounded result receipts](../../research/current4h-expired-recovery-20261015/results/summary.json).

## Before failure / after recovery

The unmodified accepted controller/node/API modules created a synthetic committed
checkpoint through the actual normal workflow. A controlled **fixture** clock then
advanced two days: authority, all nonrevoked grants, leaf and CRL were expired.
The old `authority_request` rejected with its original UNKNOWN result; normal operator
and scheduled reads rejected with SNAPSHOT_VALIDATION_FAILED. Credential snapshot
hashes did not change. [Reproduction receipt](../../research/current4h-expired-recovery-20261015/results/before.json).
These are local observations; earlier production receipts are not renamed.

On the same scenario, the implemented path executes:

`expired-request → explicit offline root signature → expired-apply → existing node
quiescence/stage/promote/commit → normal strict validation → new runtime directory
publication → controlled resume/cleanup`.

Local systemd actions are subprocess fixtures, not calls to real system services.
Actual SQLite/filesystem/controller/node/offline-verifier implementations are used.
Normal Python validation and real Family/TLS configuration/handshakes accept the
new synthetic material; the expired predecessor remains rejected by normal paths.

## Implemented entrypoints and authorization

`runtime_controller.py` adds **only explicit operator modes** `expired-request`,
`expired-apply`, `expired-resume`. The offline signer requires both
`--expired-recovery` and its existing `--confirm-authority-renewal` confirmation.
No scheduled fallback to recovery exists. The fixed privileged node RPC gains only
bounded `recovery-evidence`, `recovery-authority-request`, `prepare-expired` actions.
The existing forced receiver already forwards this RPC and refuses legacy writes;
no receiver/protocol replacement is introduced.

The dedicated `HistoricalPredecessor` dataclass stores independently verified
historical provenance; it is not interchangeable with a normal validated active
snapshot. It verifies exact schemas, root/delegation/issuer/CRL/leaf signatures,
issuer key, Family/gateway identity/public key, original intervals, floors and grant
bindings. The current committed coordinator plan, node archive manifests/completion
records and current files must match. Grant revisions/revoked state cannot fall below
the retained committed checkpoint. An old signed snapshot alone is not freshness.

Recovery request schema3 binds operation ID, explicit recovery purpose, predecessor
digest/scope, authority/revision/CRL/grant floors, committed checkpoint, both observed
node state/policy hashes, approved grant set, update classes, exact successor authority
payload, creation and expiry. A separate domain-separated offline-root signature
binds the entire request and new normal wire delegation. The old issuer's signature
does not renew its own authority. Same issuer/gateway/device keys and pinned anchor
are retained. Root-key custody remains offline; no production key was used locally.

Normal validators are **unchanged**. No global allow-expired/skip-validation, fake
historical now or `expires_at-1` workaround exists in the management reader. The new
successor is checked by normal validators at actual application/resume time. The
fixture clocks are confined to tests. Request validity is at most the existing day;
authority/grants remain one day and leaf/CRL four hours under the accepted policy.
Offline delay consumes this window; it is not reset by apply.

## Grants, revocations and floors

Expired grants are not renewed merely because an old record says unrevoked. The
current protected DB snapshot includes devices, invites, grants, certificates and
CRL state; the current admission policy hash is also bound. Recovery requires an
explicit exact list of currently unrevoked grants. It verifies their current
entitlement with the actual API `_grant` method on an in-memory successor projection
at current time. Live expired grants are not temporarily made valid to run this check.

Revoked/deleted grants are never reinstated; missing/revoked devices/invites and lost
admission eligibility reject. An ineligible unrevoked grant causes a rejection, not
an automatic entitlement change. Device keys, roles, Family bindings, revoked flags,
existing CRL entries and namespaces persist. Authority/CRL increment within their
existing namespaces, authorized grant revisions increment, no floor resets occur.
The complete-expiry path rejects an unexpected still-valid tracked certificate.

## Lock / CAS / admission / resume contract

Request capture uses existing coordinator/node locks and then **releases them for
human signing**. After handoff, the controller rechecks request/checkpoint/current
state and explicit operation-bound outage approval before acquiring durable node
ownership or publishing credentials. A security-relevant state change produces a
stale result; it is not silently incorporated into the approval. A further pre-promote
check rejects stale DB/policy/files before first publication. Actual SQL CAS remains.

The accepted outage gate stops the actual RU restricted API plus sync and directory
sync timers/services, as well as the NL gateway. PID0 alone is never treated as proof
that all readers or sessions are absent. Known current4h/recovery callers share the
same coordinator lock and node owners. After all readers stop, both sides stage and
validate, promote, reconcile and persist/replicate a commit decision before restoration.
Identical hashes are readback evidence, **not distributed atomic visibility**.

After a partial recovery, the original failure and durable cursor survive. This
mode cannot call the normal expired-predecessor rollback path. Explicit
`expired-resume` with the identical bundle performs idempotent rollforward and current
strict validation; ordinary scheduled/recover/operator paths cannot auto-resume it.
Fencing preserves closed admission during mixed/incomplete publication. Once valid
publication is committed, lost cleanup responses resume cleanup without another issuance.
Same completed operation/bundle gives idempotent readback; different bundle under
the same ID rejects. Existing start-intent semantics prohibit retry-until-green after
a failed gateway start. A failed start/expired successor remains an operator blocker.

Bounded codes include RECOVERY_PREDECESSOR_UNTRUSTED,
RECOVERY_CHECKPOINT_UNCONFIRMED, RECOVERY_STALE_APPROVAL,
RECOVERY_SIGNATURE_INVALID, RECOVERY_APPROVAL_EXPIRED,
RECOVERY_STRICT_SUCCESSOR_INVALID and PUBLICATION_INCOMPLETE. No arbitrary exception
text, payload or secret is exposed as a recovery cause. Normal historical UNKNOWN is
unchanged, not reclassified retroactively.

## Local acceptance matrix

| Case | Actual exercised boundary | Result |
|---|---|---|
| A | Entirely expired signed/checkpoint-bound predecessor; offline authorization; controller/node publication; strict successor | PASS |
| B | Same expired set through ordinary authority request/operator/scheduled; no implicit recovery | PASS, fail-closed |
| C | Bad signature/root/key/scope/schema/interval/digest; missing committed evidence | PASS, reject without credential mutation |
| D | Revoked/deleted grants; revoked device/invite; lost entitlement; lowered floors/changed device key | PASS, no restored permissions |
| E | State change before signing/after signing/after acquire/after staging; same lock and different owner | PASS, stale/busy result |
| F | Wrong offline signature/op/successor/expiry; wrong update scope | PASS, before publication |
| G | Expired or tampered successor on partial transaction resume | PASS, admission remains closed |
| H | 16 controller crash boundaries, 7 lost RPC-response boundaries, 7 partial file/SQLite mutation boundaries | PASS, verified rollforward/no floor rollback |
| I | Same completed ID/bundle; changed content under same ID | PASS, no additional issuance |
| J | Normal scheduled evaluation then due leaf/CRL renewal after recovery | PASS, authority/grants unchanged |
| K | Existing live-authority operator/offline handoff and all prior security regressions | PASS |

- **221 Python tests PASS**: 154 existing + 67 new recovery tests, one final full run.
- Seven partial-node-write tests repeated in **three fixed batches**, all 21 PASS.
- Three management-config projection tests PASS, including idempotent source-only
  projection and wrong-base/scope rejection.
- Real Family/TLS source: **one normal + three race runs PASS**, three synthetic
  clients per run; expired gateway configuration rejected by the ordinary validator.
  This uses existing Family/Reliable in-memory endpoint fixtures, no provider/rooms.
- Reconstructed source inventory and prepared package match the tested derivative;
  script syntax and zero-context patch checks PASS. Python3.14.4 / Go1.26.1;
  [test-only build identities](../../research/current4h-expired-recovery-20261015/results/build-identities.json).
  No frozen gateway executable was run/rebuilt. Its CLI
  provides no observed provider-free synthetic Family/TLS mode; the source path,
  not **FROZEN_BINARY_ACCEPTED**, is the stated validation scope.

### Unexpected failures retained

Initial smoke exposed missing private bookkeeping-directory creation and an incorrect
assumption that archived owner.json existed. Fixed with mode0700 checked directories
and protected committed plan/file metadata, retaining unchanged-file hashes. A CLI
test initially mixed frozen node time with real CLI time and correctly failed its
time binding; the fixture now uses real time for that boundary, without relaxing code.

Go linking/compilation hit `disk quota exceeded` in the temporary build filesystem;
one initial race command emitted only FAIL. A separate compile diagnostic confirmed
quota. Moving **build temporary/cache** files to a disk-backed task directory and
serial compilation fixed the build without product changes. By then the original
one-hour synthetic client certificate had expired; all three first executable race
attempts were rejected. The harness now compiles first, then creates fresh fixtures
with the **same durations**, and executes the fixed 1-normal/3-race batch. No TTL
extension, clock trick, hidden retry-until-pass or production retry occurred.
Bounded failure/correction summaries are published; full local development receipts
remain separately retained, not overwritten by final success.

## Deployment delta and remaining limits

Changed management modules: `expired_recovery.py` (new), `grant_cutover.py`,
`production_node.py`, `production_controller.py`, `production_transport.py`, `node.py`,
`runtime_controller.py`; separately offline-only `sign_authority_offline.py`.
Four additional source files are local tests/characterization/vector generation;
the Go addition is test-only. No gateway production source or API validator changes.
The package contains the full compatible 13-module online management inventory;
the offline signer entrypoint, root key, API/receiver archives and production configs
are not included. Reproducible config-copy tooling changes only management source
hashes and the controller's expected peer identity.

The [runbook](../../research/current4h-expired-recovery-20261015/RUNBOOK.md) covers the
management version switch, explicit grant review/request, offline key-owner action,
CAS/apply/resume, strict validation, unchanged baseline startup/directory distribution
and return to the existing schedule. There is no deferred “invent apply later” step.

Limits: intact protected last-COMMITTED evidence is required; unknown external writers
or extra readers are outside the verified declared unit topology and require a stop,
not an assumption. Today's actual production checkpoint/topology/security state was
not inspected. Local systemd fixtures prove ordering, not live systemd/network success
or cross-host atomicity. Expired successor during an incomplete operation, lost state
or a failed one-shot service start are fail-closed limits, not automatic reissue/restart.
Generated keys/profiles/vectors, binaries, accepted full archive and raw operational
materials remain private. Local `/tmp` paths are not presented as public evidence.
The exact base source commit is not included as a Git ancestor by this publication;
the verified retained archive is required for full reproduction.

**Next step is separate controlled management deployment/recovery authorization.**
Only after real environment restoration can owner acceptance resume from the already
signed APK and fresh short checks. No automatic install, CONNECT or further signing.
