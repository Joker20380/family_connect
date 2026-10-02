# 5N-REAL-OWNER-CHALLENGE-503 — local investigation, 2026-10-02

**BLOCKED: the production cause is not established. Do not retry PROV-1.**

Starting HEAD: `014e6f945cce2d9956423d285492c8e315840d29`. This task is local only:
no SSH/ADB, authority refresh, service start, ingress operation, deployment, publication,
push, FIELD-1, DIAG-1, OPS-1 or beta. Existing dirty/untracked documents are preserved.
Attempt15 remains rolled back; its recorded installed private Android55 and public51
are not reverified here. Accepted artifact pins remain the attempt15 pins, not these
new diagnostic builds. No production rollout or rollback was executed.

## Evidence boundary and proven reproduction

The actual Android request on a synthetic activated owner with current authority and
the current migrated schema returns200. Removing only `restricted_readiness_results`
reproduces503 through the actual packaged HTTP parser/handler. Classified locally:
`stage=correlation_store reason=CORRELATION_SCHEMA_UNAVAILABLE`.
The transaction rolls back: no orphan nonce, grant or correlation is accepted.
Running the existing explicit `restricted.migrate(access)` on that **synthetic DB**
restores200 without changing request bytes or authorization. This is a proven local
upgrade-state failure, **not proof that attempt15 had this schema**.

`readiness_fixture.create()` always initializes and migrates a new synthetic DB;
`configured()` in historical server tests does likewise. The retained attempt15
operator/operation scripts and their attempt12/13 dependencies do not execute the
new receipts migration. Sync's authority check does not check that receipt table.
No retained attempt15 schema snapshot, backend exception or classified reason was
found in the inspected local evidence. Authority failure, DB failure and capacity
exhaustion can also yield503. The recorded nginx upstream503 alone cannot distinguish
these. Missing-table production attribution would be a guess.

No speculative automatic migration, owner exception, new entitlement behavior or
authorization workaround is added. The changes classify failures and establish the
contract regression. A production-cause fix remains blocked pending **already retained,
sanitized evidence** of the failed backend stage or DB schema at the failure time.
Current scope does not authorize contacting production to obtain it.

## Every challenge503 path

The HTTP handler's final catch returns the unchanged503 `{"error":"unavailable"}`.
Its parser/assertion/key/type failures remain400; authorization `Rejected` remains403;
the four-slot concurrency guard remains429. Content type, size and duplicate-key checks
are unchanged. Response-write/network failure may prevent delivery of any response;
it is not proof of an application503. No raw exception, identifier, body or secret is logged.

| Internal stage | Failure examples | Safe local reason |
| --- | --- | --- |
| http_parse | socket read/I/O failure not in the400 classes | INTERNAL_ERROR |
| handler_import | restricted module/dependency import | INTERNAL_DEPENDENCY_FAILURE |
| dispatch | unexpected handler infrastructure failure | INTERNAL_ERROR |
| authority (construction) | missing env/path/file, permissions, malformed anchor/admission/issuer/private key | AUTHORITY_UNAVAILABLE |
| binding / clock | unexpected identity derivation or clock failure (ordinary invalid input still400/403) | INTERNAL_ERROR |
| authority (validation) | delegation signature/time/schema, issuer-key mismatch, CRL signature/time/number/canonicalization | AUTHORITY_UNAVAILABLE |
| device_lookup | DB open/BEGIN/read/auto-enrollment failure, missing schema | DEVICE_MAPPING_UNAVAILABLE |
| challenge_store | cleanup/count/nonce-row/revision-row writes | CHALLENGE_STORE_FAILURE |
| challenge_store | eight outstanding unused challenges | CHALLENGE_CAPACITY_EXHAUSTED |
| nonce | random generation/encoding/expiry construction | INTERNAL_ERROR |
| correlation_store | missing receipts table specifically | CORRELATION_SCHEMA_UNAVAILABLE |
| correlation_store | invalid/duplicate correlation, SQLite writes/retention/schema mismatch | CORRELATION_STORE_FAILURE |
| commit | transaction commit/connection cleanup failure | CHALLENGE_STORE_FAILURE |

Classification is private server stderr/logging, not a new HTTP field or new status.
Malformed body validation occurs before authority loading. Existing correlation reuse
returns503 and rolls back; it is not made idempotent or silently overwritten.

## Real canary55 wire trace and comparison

Activated Friends activity/resume timer and normal control prewarm call
`FriendsRestricted.prewarm`: single-flight, encrypted identity load, restart revalidation,
cache cooldown, then `FriendsAccessAndroid.restrictedReadiness` →
`FriendsReadinessProtocol.fetch` → `post` → HTTPS direct control connection →
`Handler.do_POST` → `restricted.request` → `RestrictedReadiness.challenge`.
An existing local valid cache is separate from the success of this attempt.

- POST `/friends/restricted-readiness/challenge`, UTF-8 Gson compact JSON.
- `Content-Type: application/json`; fixed Content-Length in bytes; no Authorization
  header, bearer token, invitation or cookie supplied by this builder. TLS authenticates
  the server; the subsequent fetch proves possession. Platform-generated HTTP headers
  are not assumed to be fixed or reproduced by JVM transport.
- `X-FC-Probe-ID`:32 lowercase hex, UUID without hyphens; fetch has another distinct ID.
- Exactly two required string fields: `public_identity` (standard padded Base64 of
  64 raw bytes, X25519 public32 + Ed25519 public32), `wireguard_public_key` (standard
  padded Base64 of independent X25519 public32). Neither is a private key or a reference
  string; the server derives the32-hex device reference from the public identity.
- No optional fields, explicit nulls, purpose, Family, revision, timestamp, proof,
  transport name, request ID or device reference in the challenge JSON body.
  Purpose `restricted`, active Family/revision and100-second TTL are server-side.
- Response: `challenge` (Base64 nonce32), integer epoch-seconds `expires_at`, audience
  `family-connect/enrollment/v1`. Android checks expiry/audience and nonce encoding;
  only then marks challenge issued and builds the signed transport-key fetch proof.
- Controlled fixture uses the same two keys/types/encodings and random32-hex header.
  Its Python JSON includes insignificant whitespace; Android emits compact JSON.
  Both fit8KiB and the parser does not canonicalize/reject whitespace. Challenge body
  is not signed; canonical signing is on the later transport-key proof.
- **No meaningful wire-shape contract difference found.** The meaningful verified
  fixture difference is fresh migrated synthetic state, not wire format or lookup bypass.
  Both routes use binding, admission, existing registration, grant, Family/revision,
  revocation and authority checks. Synthetic state cannot verify the real owner's mapping.

## Correlation / ACK audit

No circular dependency found. Challenge inserts the nonce and an empty attempt row;
fetch fills its fetch/revision/expiry fields after proof authorization; validated import
produces a receipt; ACK challenge checks that attempt and signs/binds the exact receipt;
ACK consumes its own one-use nonce. A challenge never requires a completed fetch/result,
import or ACK. It **does** require the receipts schema when the request ID is present.
Controlled fixture F/G already sends request IDs, but only against its fresh migrated DB.

## Permanent cross-language contract

`FriendsReadinessGoldenTest` calls the actual protocol builder with a disposable all-zero
test identity and fixed safe IDs. Gson and shared production `wireBytes`/`wireHeaders`
produce `tests/vectors/friends-readiness-challenge.json`; no Python JSON re-creation is
used to produce the golden. No real identity/proof/credentials are captured. JVM tests
compare structure **and the exact serialized body string** with the committed golden.

`tests/test_android_challenge_contract.py` feeds those UTF-8 bytes and headers through
the packaged HTTP parser, not a mock parser. Its optional JVM leg is mandatory in the
new `readiness-contract.yml` CI job: actual Java builder → Python challenge/fetch →
actual Java response parser and signing →200. It does not claim native import/READY.
CI needs no production secrets or device. Local JVM classpath is supplied explicitly.

## Stable Android classification

401/403 → `CHALLENGE_UNAUTHORIZED`;429/5xx and transport I/O →
`CHALLENGE_TEMPORARY_SERVER_FAILURE`; other non200, malformed JSON/schema/audience/
nonce/expiry → `CHALLENGE_INCOMPATIBLE_RESPONSE`; socket/deadline timeout →
`CHALLENGE_TIMEOUT`; unexpected exceptions → `CHALLENGE_INTERNAL_ERROR`.
No server text becomes a reason. `FriendsRestricted.refresh` carries the stable code;
existing receipt v1 keeps FETCH_FAILED/AUTHORIZATION_REJECTED rather than changing
the ACK schema. Unauthorized still invalidates the cache; temporary failures do not
invent revocation or new READY. Native validation/import remains required for READY.

## Validation, artifacts and next boundary

Server implementation/build source: `ad17db7faf7407296dd48748045a202664860ed7`.
Android build source: `a10a9c4e4f237d2b7a6df1a9ac4ed4fc8aee26b0` (only subsequent
change is a test-only Files.writeString→Files.write compatibility correction).
Every tracked file in each export matches its committed bytes; per-source and per-bundle
inventories were verified. No source-pin exception. All three server bundles contain
the changed restricted module, so all three were rebuilt with the existing builders.
Android native AWG/restricted JNI were freshly built and verified against packaged bytes.

| New local artifact | SHA256 |
| --- | --- |
| friends-http.pyz | `ad71cadba79a8fbbe4e60d8d2a1c581304e263a30fdf71fd69b002001d01dd63` |
| candidate-readiness.pyz | `9f914a07dd925c892ea489e0f38b3db488a462544a574d7df7a7c4e54671c64b` |
| restricted-sync.pyz | `f6aa8859ab716383bf207b2ff7b302687692832b2ccb410f1aef0ada0793a9c9` |
| Android unsigned canary56 | `5ca1d29101df529cce197e5eeb82f231b50e3f4fc76c8835ba12fdad0c2122b0` |

[Machine pins, exact paths, input/export hashes and inventories](2026-10-02-5n-real-owner-challenge-503-pins.json).
Server artifacts: `state-client-build/real-owner-challenge-503/{http,readiness,sync}`.
APK: `state-client-build/real-owner-challenge-503-android/source/clients/android/app/build/outputs/apk/friends/app-friends-unsigned.apk`.
Local build-only override `0.1.18-canary56-challenge`/56, `.friends`, arm64,
non-debuggable,49,575,960 bytes. **Unsigned, not update/install-ready, not installed,
not distributed.** No signing secret was read. Immutable signed55 is not replaced;
last installed55 and public/invitation51 remain unchanged, not reverified.

- Python environment matches both control/identity lockfiles exactly.
- Focused parser/security/receipt/source/secret suites:151 passed,12 skipped (optional
  nginx/native/artifact prerequisites); exact new HTTP run65 passed,8 skipped.
- Final exact three-artifact/native/owner/Android-source regression: **171 passed**, in
  `state-client-build/real-owner-challenge-503/evidence/artifact-regression-final.log`.
  Earlier historical negative used the new pin accidentally:170 passed,1 configuration
  failure. Correct retained `460e752...` pin independently restored1/1 PASS; no historical
  pin check or test was weakened.
- Separate control JVM:163 passed; full app Gradle `assembleFriends`,
  `testFriendsUnitTest`218 passed, `lintFriends`0 errors/37 warnings. Suites overlap.
  First app test compilation caught unsupported Files.writeString in Android's test
  API surface; committed correction and fresh clean-source rebuild passed.
- Exact accepted HTTP `7ef821...` also reproduced missing-schema503→explicit synthetic
  migration200. No new serializer/diagnostic code is needed to trigger that failure.
- Compiled the accepted canary55 `FriendsReadinessProtocol` from starting HEAD separately:
  its Gson wire body is byte-identical to the golden,180 bytes, SHA256
  `31e9ae09989f4d3db46f9624072939c9f2814963d33641236855828fb830f794`.
- Non-canary, revoked device/invite/grant, expired grant, wrong Family/revision/key403;
  stale/used/wrong-purpose fetch proof403; duplicate correlation503 with rollback;
  capacity8 preserved; malformed400; unavailable authority safe503. No security weakening.
- APK package/manifest/alignment, fresh JNI equality and bounded nested archive scan:
  1071 entries,0 findings; one existing hash-pinned stdlib false positive reviewed.
  This is not an exhaustive secret scan or physical/native runtime acceptance.
- New server archive source/secret guard:48 entries,0 findings. All four retained
  artifact SHA256 pins match; export inventories match committed source exactly.
- `git diff --check` passes. Whole-index `check_public_sources.py` reports **one existing
  finding** in unchanged `tests/test_readiness_adapter_packaging.py` (`private-key-pem`),
  reproduced at starting HEAD; task-owned staged files pass. No allowlist/guard change
  was made. Therefore the whole-repository source guard is not reported as green.

Local sockets required approved outside-sandbox test execution. No production socket,
SSH/ADB session, CI dispatch, push or remote service operation occurred. CI workflow is
committed but not run remotely. New private builds are diagnostic candidates, not accepted
deployment replacements. No authoritative real owner READY/import/ACK is claimed.

No production rollback is needed: production is untouched. Local code can be reverted
by its task-owned commits without touching unrelated edits. Artifact rollback means
retain the accepted immutable attempt15 bytes, not republish or overwrite them.
Gate remains BLOCKED until production503 attribution and a proven minimal production
cause fix exist. Local200 and synthetic migration reproduction are not sufficient for PASS.
