# WARM-START-COLLECTOR-REBASE-1 — PASS (local candidate only)

`REBASED_COLLECTOR_ACCEPTED=YES`. Collector-only delta transferred onto the exact
deployed API source; the previous baseline mismatch is resolved locally. **Nothing
deployed.** Historical functional warm-start remains `PASS_IN_TESTED_SCENARIO`;
historical formal acceptance remains PARTIAL. Warm-start readiness is still NO.

## Evidence and identities

Private local capsule:
`state-client-build/field65-export16/warm-start-collector-rebase-1/`.
It contains baseline/source/isolated validation Git, exact diffs, schemas/evaluator,
feature inventory, commands/logs, response comparisons, artifacts and rollback.
No remote Git, push, tag, APK or public release was created.

| Identity | Exact value |
|---|---|
| Deployed API bundle / rollback | `12ca0c72a89ff20c1b3c70a1182a2d5d98d4d78d25e7a079bb4d75bdf34060ed` |
| Deployed gateway / rollback | `21f0a0fdc27b50c00ea922f0b716516e2422aedf1b3797369718f7d00070509a` |
| Gateway baseline source | `a4087e000fdbe674b72ede3a6c8822445c87c654` + signal diff `7e7d408670a6ac6afa18e856beb8dcc0ca26a3b6f074e205d4dd25e62d78967b` |
| Donor collector diff | `0cb0e59da551a2291be0225a8ef885fea6d3a3e1441e9dc09952071387fec22a` |
| New assembled baseline validation commit | `433a0fc74006e6e9fd8e85eaf13e3d3fb7240a63` |
| New collector validation commit | `473ebe5768f3c78c8e36b4a79f26189f560cbadc` |
| Collector-only source diff | `df949a80d928ba0735b8f9ca6500659cc36ced633c9a5ce3db01ef9ffee78dbc` |
| Candidate gateway | `406a5ca4bdf8ff6b3a4d2edf4e392e572fcb5e3ff622fe74ce7121346aaadfe2` |
| Candidate API pyz | `78bfc20f67e1b72c7907aad6fd3c0c4c7814a2915118288cec6e851ae7145fc6` |
| Manifest | `22cb357b3c80cbec02bac83388cc724790d9cf70ca36c9c1625f74865161ed25` |
| SHA256SUMS (8144 files, excludes Git internals) | `10b2044643d40f1abdcdde6420939b64e9ad932da94e2399d09f2c7f46c7ee3a` |

Prior formal/attribution capsules verified before and after work; original receipts,
manifests and source were not rewritten. The main dirty worktree was preserved.
Only isolated server source changed; repository changes for this task are docs.

## DEPLOYED_BASELINE_IDENTITY — RESOLVED

Fresh bounded read-only snapshots at approximately19:25UTC:

- RU API active PID414703, InvocationID`e9618550d9624ce887a2c392c4eb3e3f`;
  actual argv uses Python `-I http-publisher-research74-20261010.pyz --port18086`.
  Current archive SHA/member hashes match the accepted publisher packaging and
  deployment receipts. Those receipts link the AKI-corrected input archive to this
  publisher output, with unchanged remaining members.
- Python `/proc/PID/exe` and next interpreter agree (`52e0a13e…cb41`); this is **not**
  the application binary identity. The API is a closed plaintext-source archive.
  Its23 file members provide exact deployed source, even though no original Git SHA
  was embedded. No process-memory source dump was attempted. The new validation
  baseline commit is a local source seal, not a fabricated historical Git identity.
- NL gateway active PID1415977, InvocationID`1613fa1ce16d4ea5a649255ddf76829f`,
  NRestarts0, loaded=next21f0a0fd…509a; argv/unit hash saved. Existing signal observer
  left unchanged. These are historical snapshots at closeout, not fresh live grants.
- Unit/drop-in identities, API configuration hashes and query-only SQLite schema
  digest/object names retained. No DB rows, private profiles, owner identities,
  secrets, journal follow or previously timed-out journal queries were read.

Chain: deployed archive hash → original accepted build/deployment receipts → exact
member source hashes → assembled local baseline. Current HEAD or directory naming
was not used to select a production baseline.

## DEPLOYED_FEATURE_INVENTORY / preservation — PASS

Detailed inventory: capsule `FEATURE_INVENTORY.md`,
`receipts/feature-inventory.json`, `receipts/baseline-identity.json`.

| Feature | A deployed | B stale donor | C rebased |
|---|---|---|---|
| AKI issuance | PASS | absent | PASS |
| Leaf not-before skew | −5s | 0s | −5s |
| ACK observed now−5s | accepted | rejected | accepted |
| Publisher registration/config modules | present | absent | byte/semantic preserved |
| Legacy/client response compatibility | baseline | not a deployment baseline | PASS vs A |
| Provisioning receipts | absent | present | present |
| Lease receipts | absent | present | present |

- **AKI_PRESERVATION:** `_issue` byte-identical. Issuer SKI including custom SKI,
  standard public-key fallback, noncritical extension, device/client and gateway/
  server EKU, SAN/hostname and claims preserved. Real signatures/OpenSSL boundary
  fixtures PASS. Missing issuer SKI still fails strict OpenSSL's CA policy; fallback
  signature verification is not falsely described as strict-CA acceptance.
- **CLOCK_SKEW_PRESERVATION:** existing five-second leaf/response backdating and
  authority lower bounds preserved. Directory validation remains strict at
  nanosecond boundaries; no blanket five-second allowance or new TTL introduced.
- **ACK_VALIDATION_PRESERVATION:** unchanged challenge age, observed-time bounds,
  current fetch/grant/revision/CRL/deadline and prior-ACK checks. Real deterministic
  tests include boundaries, stale/future, wrong/previous attempt and replay.
- **PUBLISHER_PRESERVATION:** optional authenticated owner response branch retained;
  `control/friends/chat_publishers.py` and `provisioning/chat_publishers.py` exactly
  match deployed bytes. Encrypted Store/reopen/version-context tests use the pinned
  accepted publisher consumer fixture, not an owner APK/lifecycle test.
- **API_RESPONSE_COMPATIBILITY:**10 representative canonical rows equal for A/C,
  both with normal writer and ENOSPC. Includes versions55/83/84, accepted/rejected
  provisioning, ACK, publisher owner, client without field and rejected chat proof.
  Fixture canonicalization lists dynamic nonce/certificate/identity/time fields;
  it does not claim random certificate bytes match. Additionally, original dispatch
  and response-serialization AST are **exactly equal** after removing only observer
  statements/wrapper. DB fixture counts agree; no required client field was added.

## DONOR_DELTA_EXTRACTION / SEMANTIC_REBASE / PATCH_SCOPE — PASS

The donor was not deployed or blindly applied as a source tree. API hooks were
inserted into the actual deployed dispatch/fetch/ACK boundaries. Removing the two
observation statements makes each restricted/readiness file equal to deployed bytes.
Publisher modules, issuer, validity helpers, SQL, configuration defaults and runtime
dependencies were not replaced. Gateway baseline already matched the donor's
signal-observation source; only its collector hooks/new files were transferred.

`scope.txt` describes16 changed files/functions. No change to auth results, HTTP
status, response schema, challenge/fetch/ACK, lease policy/ownership, timers,
admission, process exit decisions, Telemost, Family TLS or Reliable/Mux. Added hooks
capture actual decisions; disk I/O occurs on bounded workers outside auth/broker
locks. Optional flags do not create an endpoint or new listener.

Retention was narrowed from broad globs to regular collector-owned filenames,
protecting unrelated operator files/symlinks. This is an evidence-storage correction,
not a protocol change. Bounded shutdown flush and writer resource use are observer
overhead; zero performance effect is not claimed.

## PROVISIONING_COLLECTOR / LEASE_COLLECTOR — PASS locally

Provisioning: schema1, request/collector IDs, role, actual status/decision, safe
rejection enum, HMAC requester, proof-auth stage and exchange/import correlation.
Probe header remains **untrusted**; no owner test-generation is invented. Two users
behind one IP are not attributed by NAT or time. A blocked-before-dial fixture makes
zero server requests/receipts. Unknown/pre-HTTP attribution remains unknown.

Lease: actual policy/auth result, same session/holder tag, request/sequence, old/new
deadline, context/cleanup outcome, separate confirmation-write/peer-done event.
Acceptance is captured before later cleanup; failed ACK cannot become ACK-sent.
Replay is explicitly idempotent, not a new extension; append-only records do not
overwrite earlier successful renewal. Client confirmation remains independently
required; a local write alone is not proof of client receipt.

Schemas/evaluator retained in capsule. No raw URL, payload, identity/key, certificate,
profile, token/header/cookie or arbitrary error text is recorded. Service-owned0700
directory,0600 atomic files,4096-byte cap, queue64, default256 retained records.
HTTP1800s and gateway3600s capture lifetimes unchanged. Loss/drop/write failure
causes evaluator PARTIAL, never a fabricated zero. Malformed old JSON is not parsed
by writers; retention excludes foreign names. No network export.

## LOCAL_TESTS / BASELINE_DIFFERENTIAL

| Check | Result |
|---|---|
| New deployed-feature + response fixtures | A36 PASS / C36 PASS |
| Provisioning collector/storage |16 PASS; thread/concurrent suite repeated×3 |
| Pinned publisher Store/registration/package |19 PASS |
| Existing evaluator |9 PASS |
| Lease Go race×3 | baseline96 / candidate147 passing test events |
| Existing fatal/signal observer race×3 |69 passing test events |
| Independent real auth/unauthorized-creation fixture |7 cases×3 on A and C PASS |
| Expanded API regression, standard umask022 | A/C each329 PASS,70 SKIP,5 identical FAIL |
| Full affected bootstrap/roombroker suites | same six diagnostic subtest failures and parent; no new failure |
| Privacy / permissions / retention / write failure | PASS |
| Repeated Go + closed API builds | both byte-identical |

**Full suite is NOT_GREEN.** Unmodified Python failures are the old source guard
and four old assertions expecting non-backdated refresh/CRL durations. Exact names
and A/C logs are in `receipts/final-differential.json`. Initially two additional
permission-fixture failures appeared because private capsule umask077 masked their
intended0755 directories; rerunning unchanged tests under022 resolved both. Initial
logs retained. Sandbox loopback refusals were separately retried outside sandbox.

Six Go auth-diagnostic assertions remain failing. Their early counter assertion
prevents subsequent security assertion execution, so an **additional independent**
fixture checks actual successful auth/failed unauthorized carrier creation on A/C.
It passes; the original assertions were not removed or weakened. Known busy-wire
flake did not recur in this differential and is not declared fixed. Skipped external/
platform tests are not claimed PASS. No new failure relative to the tested deployed
baseline was found.

## BINARY_AND_PROVENANCE / ROLLBACK / DEPLOYMENT_PLAN

Go1.26.1, Python3.14.4, OpenSSL3.5.5; inputs/locks/toolchain/commands in build receipt.
Go `-trimpath -buildvcs=false`; no false embedded deployed SHA. The validation commit,
tree/diff hashes and build manifest bind binary to source. Both artifacts rebuilt
identically. API has24 file members versus deployed23: exactly one collector added,
only the three hook-bearing existing modules differ. No dependency/import rollback.

Local artifacts:

- `build/bootstrap-broker-REBASED-OBSERVATION-ONLY`
- `build/http-observation-only/friends-http.pyz`
- `rollback/bootstrap-broker-signal-observation`, `rollback/deployed-api.pyz`
- `source.diff`, `commit.diff`, `manifest.json`, `SHA256SUMS`

`DEPLOYMENT_PLAN.md` and a fixture-validated argv plan specify fresh drift/credential
checks, original unit/config preservation, private receipt paths, one controlled
gateway restart, the distinct API process update, rollback and600s prelive stability.
Capture lifetime/headroom must cover owner preparation through renewal/cleanup;
API observer should not expire while waiting for the operator. No speculative TTL
change, automatic deployment or service start was performed here. Future rollback
uses verified original artifacts and removes only the future task-specific override;
fresh private unit snapshots remain a mandatory future preflight step.

Temporary synthetic private credentials and fixture scratch/build resources removed;
accepted local build/source/rollback/test evidence retained. Main worktree/prior
capsules unchanged apart from this task's documentation. Research84 and all owner
data untouched; phone lifecycle intentionally not re-observed.

## Final state and next operation

```text
WARM-START-COLLECTOR-REBASE-1 = PASS
REBASED_COLLECTOR_ACCEPTED = YES
DEPLOYMENT = NOT_RUN
OWNER_INSTALL = 0
OWNER_INSTRUMENTATION = 0
OWNER_REFRESH = 0
OWNER_CONNECT = 0
GATE_ARM = 0
TELEMOST_SESSION = 0
GATEWAY_RESTART = 0
RENEWAL = 0
ATTEMPT_CONSUMED = NO
FUNCTIONAL_WARM_START = PASS_IN_TESTED_SCENARIO
WHITELIST_WARM_START_READY = NO
WHITELIST_COLD_START_READY = NO
PUBLIC_RELEASE = NOT_RUN
REAL_RESTRICTED_NETWORK_FIELD = NOT_RUN
```

Earlier physical attempt history is unchanged, not reset. **Exactly one next
operation:** separately authorized controlled collector deployment, fresh preflight
and one final formal warm-start run using research84/two-phase operator gate/existing
egress harness. Not executed automatically.
