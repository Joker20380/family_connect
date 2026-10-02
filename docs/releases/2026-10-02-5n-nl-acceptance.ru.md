# 5N-NL-ACCEPTANCE — local bootstrap acceptance correction, 02.10.2026

## Scope and history

**5N-NL-ACCEPTANCE = PASS — local-only acceptance/receipt correction.**

Starting HEAD: `f4c06df5f16593273b4c8bffa75646f1df17c2fb`.
This task changes only the local operator, synthetic tests and related documentation.
No production access/deployment, authority refresh, service start, live Telemost,
Redmi/Android build, public artifact/version change or push. No attempt #9.

[Attempt #8](2026-10-02-5n-prov1-attempt8.ru.md) stays **DEPLOYMENT FAILED / ROLLED
BACK**: its producer exported a READY-path seed, live directory validation passed
with canonical UTC-Z/no issued_in_future, and NRestarts0. It was aborted by an
operator's mandatory diagnostic journal wait, **not a proven bootstrap/provider
failure**. Attempt #3 cause remains UNKNOWN; #6/#7 remain pre-production stops.

## Exact reconstruction

The retained `state-client-build/prov1-attempt8/deploy.py:nl` extracts NL_START from
attempt5, changes generation to attempt8, bounds journal output to100 entries and
adds timeout5s to its journal command. The exact resulting flow is preserved as
an inert string in `tests/fixtures/restricted_bootstrap_attempt8.py`; its SHA256:
`640972d5fd9a5919a4e5ca0c4a35e3d9bb6c7f30d0c674040f6726191caa0649`.
The test compares the full retained source when available, without requiring ignored
historical files in CI. No private runtime inputs are in the fixture.

Old order:

1. Read profile/CRL; require inactive service; blocking start with30s timeout.
2. Up to60 iterations: active service/NRestarts0, look for directory, sleep2s.
3. Pinned `directory-check` writes its own durable PASS; canonical Z/one seed checked.
4. Set `ready=True` but **do not persist the authoritative NL verdict**.
5. Mandatory `journalctl -n100 ...`, timeout5s; require a journal READY event/leak scan.
6. Shared `except BaseException` catches diagnostic timeout and sets `ready=False`.
7. Persist combined NL failure receipt; external operator rolls back.

Thus post-READY diagnostic failure overwrote verdict eligibility. Live timestamps
08:36:53.695Z validation →08:36:58 failure match that executed path; the original
primary receipt lacked the failing argv. Offline replay, not another live attempt,
now deterministically reproduces the exact behavior.

## Authoritative completion

New standalone `scripts/restricted_bootstrap_acceptance.py` does not change producer,
protocol, packaged artifacts, trust/TTL/admission, or RU acceptance implementation.

Actual producer semantics: `SeedManager.Run` creates the provider room, waits for
connector READY, then constructs the directory and invokes `Publish`; only afterward
does it emit the informational `bootstrap_seed_ready` log event. The broker configures
`Publish` as validated atomic `Cache.Store` with file/directory fsync. Systemd unit
has no sd_notify READY protocol. Therefore a **fresh validated post-start export**
plus healthy same-process readback is stronger than optional journal evidence.
Disk export may survive exit; file existence by itself is not liveness.

Required preflight remains pinned native/unit/runtime, expected production gateway
identity, native authority validation/JIT, inactive RU sync/HTTP and protected rollback
inputs. Operator checks inactive unit and **absent** old export; it never deletes a
stale file automatically. Profile CRL/leaf need >600s remaining before start.
Successful blocking start must yield active/running, Result=success, exit status0,
NRestarts0, nonzero PID and a new start identity. It then requires exactly one seed,
valid canonical UTC-Z issuance/expiry and Family/gateway binding through the pinned
runtime validator, issuance≥this start, unchanged preflight public-profile binding,
and final same PID/start plus unchanged still-valid material. Invalid published
material fails immediately; it is not hidden by polling until a later good export.
Native credential validation remains a prerequisite, not replaced by metadata.

Bounds: state2s, snapshot5s, start30s; wait≤120s including commands,≤60 observations
with≤2s sleep. Overall authoritative monotonic budget165s accommodates prechecks/
start/wait/final readback, with reserved final7s. Each command/sleep is clamped to
remaining time. Authoritative timeout/nonzero exit, restart, unhealthy service,
missing READY, changed binding, stale/invalid/expired directory all fail closed.

## Diagnostic policy and receipts

Authoritative command/state/material/READY records and final verdict are fsynced
before diagnostics can execute. Fresh owner-only evidence directory required; reruns
cannot overwrite prior evidence. File fsync→atomic rename→directory fsync precedes
return. Authoritative and diagnostic filenames/kinds are distinct and append-only.
Only bounded safe metadata is recorded; no raw argv/output, identities, profile
content, room URL, OAuth or proofs. Internal snapshot public-binding digest is used
transiently for comparison, excluded from durable evidence.

Optional `--journal` performs one bounded5s read. Timeout → `diagnostic_timeout`;
nonzero/spawn failure → `diagnostic_unavailable`; omitted → `diagnostic_not_requested`.
Neither availability nor journal content participates in runtime acceptance. CLI
separates `authoritative: PASS|FAIL` from diagnostic classification. A true service
failure remains FAIL with either available or unavailable journal. Receipt-storage
errors return nonzero and do not rewrite the already durable runtime verdict.
Hard process exit during optional diagnostics preserves the authoritative decision
for an external rollback/controller; acceptance is point-in-time, not future liveness.

The committed RU operator already does not invoke journal retrieval in its success
path: synchronous unit completion, fresh signed CRL/DB/directory and both negatives
are authoritative. NL follows the same principle without modifying or merging RU.

## Deterministic proof

| Case | Expected/proved result |
| --- | --- |
| A READY + valid directory + journal available | PASS |
| B READY + valid directory + journal timeout | PASS + diagnostic_timeout |
| C READY + valid directory + journal command failure | PASS + diagnostic_unavailable |
| D service failed + journal available | FAIL |
| E service failed + journal unavailable | FAIL |
| F no READY before bounded deadline | FAIL |
| G READY export but invalid directory | FAIL |
| H restart/unhealthy state/PID change | FAIL |
| I hard exit during diagnostics + shell rollback trap | Authoritative PASS/FAIL receipts survive |
| J diagnostic writes/content/storage failure | Authoritative bytes/verdict remain unchanged |
| Exact attempt #8 retained flow + simulated journal elapsed5.01s | Old FAIL/TimeoutExpired; corrected PASS/diagnostic_timeout |

Additional coverage: failed start/real subprocess timeout, total/cap overruns, stale
preexisting export, wrong profile binding, old issuance, noncanonical timestamp,
wrong seed count, final service/material regression, missing fsync, no default
execution, explicit CLI authoritative/diagnostic results and isolated archive-backed
snapshot with valid/invalid/future/expired/wrong-binding directories. Tests use
synthetic material only; no production credentials, service calls or provider calls.

Focused results and final Git/preservation receipts are retained under ignored
`state-client-build/nl-acceptance/`. Existing bootstrap/precise-directory/native
contract and RU sync tests are included, not replaced by mocks of their validators.
The final focused Python run includes the NL matrix/fixture/receipts, unchanged RU
operator, existing Android bootstrap evidence-validator tests (no device/build),
directory/native contract and closed runtime packaging. Go bootstrap producer tests
also run offline with cached dependencies (`GOPROXY=off`); broker command compiles.
An intermediate run exposed two test-child import-path errors after adding fixture
imports; only the synthetic child setup was corrected, then the full suite rerun.

Final verification: **191 Python tests PASS,0 skipped,19.37s**. Offline Go
`./bootstrap` PASS (2.411s), `./cmd/bootstrap-broker` compiles (no test files).
The venv matches all24 control-lock and3 identity-lock entries. Documentation
guard:419 files/2558 links/0 errors; targeted source/secret guard8 files PASS;
`git diff --check` PASS. No full-repository test result is claimed.

## Git finalization and remaining boundary

Task commit includes only new NL operator/tests/fixture, this report, directly
related new runbook/STATUS/PLAN sections and the unchanged retained attempt-#8 report.
Mixed documents are staged from HEAD plus only the new sections, not their retained
VPN-health/artifact-refresh/earlier-attempt edits. All entry worktree bytes outside
these additions remain intact; the existing Android bootstrap tests are unchanged.
No workflow/source-runtime/manifest/version/catalog edits, no broad add/reset/stash.
Final HEAD is recorded after commit in local evidence and the completion response.

Production state and historical authority timestamps were not queried or refreshed.
This local PASS does not retrospectively accept attempt #8 or satisfy any live RU,
HTTP or physical gate. A newly authorized rollout must re-pin all inputs and repeat
the complete ordered acceptance using the new NL operator. **STOP: push:no,
production changed:no; no automatic attempt #9, distributed beta or FIELD-1.**
