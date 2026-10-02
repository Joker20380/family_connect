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

Build/test results and exact inventories will be recorded after clean-source builds.
All three server bundles include `restricted.py` and therefore require rebuilding;
HTTP also includes the classified catch. Android source changed, requiring a new local
APK, never replacement of immutable canary55. No source-pin exception is permitted.

No production rollback is needed: production is untouched. Local code can be reverted
by its task-owned commits without touching unrelated edits. Artifact rollback means
retain the accepted immutable attempt15 bytes, not republish or overwrite them.
Gate remains BLOCKED until production503 attribution and a proven minimal production
cause fix exist. Local200 and synthetic migration reproduction are not sufficient for PASS.
