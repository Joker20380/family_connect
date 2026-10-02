# Owner proof handoff — local acceptance contract

This contract supersedes the operator-generated real-owner F/G requirement from
the candidate-preflight gate. It does not authorize deployment, authority refresh,
service startup or a physical-device operation. Attempt12 remains rolled back.

## Separate states

`SERVER_CANDIDATE_READY` is not `OWNER_PRODUCT_READY`. Synthetic server fixtures
are **CONTROLLED SERVER CONTRACT FIXTURE**, never real-owner evidence. The operator
does not load an owner identity, construct its proof, call an Android signing API,
extract keys, or export a credential bundle. Only the normal Friends application
authenticates the real owner. USB connectivity is not an authentication mechanism.

| Stage | Checks and ownership |
| --- | --- |
| Pre-switch live candidate | B ordinary malformed400; C established safe400; D restricted malformed400; E non-canary challenge403; current authority loads via pinned isolated sync `--check` |
| Pre-switch controlled F/G | Fresh disposable loopback instance of the **same exact HTTP artifact**; independently generated fixture DB/authority/identities; challenge semantics; signed fetch; delegation/certificate/CRL/BOOT-1 validation with the accepted native consumer |
| Post-switch external server | A nginx static200; B400; C400; D400; E identifiable non-canary403; correlated generation/origin/upstream status |
| Post-switch actual product | Real F/G through Friends app prewarm, then native validation and atomic encrypted cache import; safe app/server correlation required before commit |

F/G fixtures must never be inserted into the real candidate's DB, admission list,
issuer files or directory. They do not test the production owner's enrollment.
The real candidate uses only its existing authority/admission. No synthetic
admission, fake production grant, extra canary or secret copied from production is
permitted. A fixture PASS without current production authority load is insufficient.

## Harness API and artifact binding

`scripts/friends_http_transition.py` remains an injected operator library, not a
service installer or credential-discovery CLI. Scoped action callbacks are trusted
operator implementations; boolean callbacks are not cryptographic attestations.

1. In a fresh **disposable state directory**, run the pinned HTTP zipapp with
   `python -I` on an ephemeral127.0.0.1 port, not18084/18085/18086/other reserved
   service ports. Generate fixture identities/authority locally; no static real
   owner proof. No external provider is contacted.
2. `Session(..., layer='server_contract_fixture').fixture_matrix(artifact,
   identities, prove, validate_readiness)` exercises B–G. `prove` signs **only the
   synthetic fixture identity**; `validate_readiness` must use the accepted
   `wholedevice.ValidateDelivery` consumer (the public-identity delivery-check
   executable is sufficient), not status-only or shape-only validation.
   `tests/test_owner_proof_handoff.py` supplies the executable local recipe using
   the actual isolated archive and native consumer. Stop the disposable runtime.
3. The returned `ContractFixture` is an in-process, at-most300s result bound to the
   SHA256 of the fixture artifact. It is not an owner receipt or a portable signed
   attestation. Do not fabricate it or import an old pytest PASS as current evidence.
4. Candidate18086 retains existing ownership/ss/bind/argv/artifact checks.
   `direct.server_matrix(non_canaries, fixture=..., current_authority=...)` requires
   that fresh exact-artifact fixture and a successful current material check, then
   probes live B–E only. Use `current_authority_check` with pinned accepted sync
   archive, local DB/material paths and existing SSH configuration; it adds
   `--check`, runs isolated with10s bound, does not publish, SSH, refresh or write.
5. After switching ingress, `external.server_matrix(non_canaries)` runs A–E only.
   The operator cannot send real F/G through direct/external `Session.probe`.

Use actual known non-canary public challenge inputs, or a synthetic unregistered
identity which is safely known to be ineligible. Challenge rejection needs no
private key; never activate/register/grant a fixture on production. Require a
nonempty non-canary set; an absent E is not a successful server matrix.

Each operator Session paces probes at≥1s and persists a redacted receipt before
verdict; run one serialized external stream and no parallel observer. Stop those
probes while the product prewarms. Product HTTP uses its existing bounded protocol
and unchanged limits, not an operator proof loop. No429 retry or limit relaxation.

## Real product F/G and observation

Existing foreground/activation/configuration prewarm remains the trigger. There
is no exported signing component, special deep link, debug credential, forced
refresh bypass, or new Android manifest entry. Do not clear app data, reenroll,
inject material or bypass the persistent300s cooldown/valid-cache policy.

`FriendsRestricted` loads the existing vault identity and calls
`FriendsAccessAndroid.restrictedReadiness`. `FriendsReadinessProtocol` contains the
same challenge→`ControlIdentity.proveTransportKey`→fetch protocol, extracted only
for local JVM testing. Paths, audience, binding and challenge TTL checks remain.
The existing native validator and `RestrictedCache.accept` still precede successful
import and encrypted AtomicFile persistence. No algorithm or admission changes.

Minimal added observability:

- Two fresh random32-hex correlation IDs, one per normal challenge/fetch request,
  carried as `X-FC-Probe-ID`; IDs are not authentication, capabilities or device IDs.
- Existing readiness diagnostics display `owner_acceptance` JSON with
  `receipt_class=real_owner_product`, `challenge_id`, `fetch_id`, fixed
  `challenge_result`, `fetch_result`, `import_result`, integer `revision`,
  `expires_at`, `observed_at`. Successful import is emitted **after** cache.accept.
- Accepted nginx trace configuration records only a fixed `product_step` enum
  (`challenge`, `readiness`, `other`), request ID, generation, timestamps, HTTP/
  upstream statuses and timing/limiter categories. No arbitrary URI/query logging.
- Operator reads the safe diagnostics from the known real Friends app and scoped
  server trace, not arbitrary unauthenticated JSON. `OwnerProduct.observe(app,
  server)` checks exact app schema, fixed categories, distinct request IDs, matching
  generation/routes, both200/upstream200, ordered timestamps from this post-switch
  window and unexpired metadata. App `accepted` means its normal native validator
  and atomic import succeeded; nginx200 alone is never import evidence.

The successful G200 plus normal app binding/native validation is evidence of
authorized proof and delivered provisioning/directory. No separate assertion that
an unproven F challenge alone authenticates the owner. An invalid/revoked/non-canary
proof remains rejected by unchanged backend checks. Receipts are support evidence,
not an alternative auth mechanism or cryptographically signed device attestations.

Collection callbacks only observe product behavior/diagnostics; they do not receive
challenge bytes or return a proof. `OwnerProduct` is created only after external
server PASS, consumed once, and has a300s observation budget; its callback must
enforce that deadline while waiting. Missing/stale/mismatched/failed observations
are failure, not permission to obtain keys. If cache is already valid and no fresh
normal refresh occurs in the window, do not invent fresh F/G evidence or bypass
cooldown: report physical blocked/rollback per policy. The new receipt is volatile;
restart persistence is still verified using encrypted cache readiness, not by
replaying this receipt.

No raw proof, identity key/public bytes, certificate, credential bundle, room URL,
provider token, arbitrary exception message or app response body enters receipts.
`server_contract_fixture` and `real_owner_product` are separate classes; ordinary
server probes are `server_probe`. Local product tests simulate observations and
must never be reported as physical owner acceptance.

## Transaction and rollback

`transaction` order:

old18084 healthy → candidate18086 start → controlled F/G plus live B–E/current
authority PASS → validate nginx → atomic switch → external A–E PASS → verify old
still healthy → `owner_prewarm(product)` → correlated actual app F/G/import PASS
→ verify candidate and old again → commit → confirmed old-worker drain → retire old.

A true callback without completed matrices/product observation is rejected. There
is no server-PASS shortcut to commit. Keep old18084 alive through the entire
prewarm, receipt writes and commit. Never touch18085. No boot enablement/retirement
before owner acceptance; preserve rollback generation after any uncertain result.

On failure: persist safe failure first → restore/validate/reload old ingress → prove
old ordinary routes → confirm candidate no longer referenced by old workers → stop
only verified candidate → rollback restricted runtime as scoped by runbook. If
restoration/drain cannot be proven, retain candidate rather than stop a possibly
routed generation. Never reset CRL/revision history or restore an old full DB.

Current policy is rollback on owner failure: report `SERVER ACCEPTANCE = PASS`,
`OWNER PREWARM = FAIL`, then `5N-PROV-1 = DEPLOYMENT FAILED / ROLLED BACK` only after
verified rollback. A separately authorized hold can report `DEPLOYED / PHYSICAL
BLOCKED` with old generation retained and no commit/retirement; the automatic
transaction does not implement that hold or assume successful restoration.

## Local verification and rollout boundary

Run the handoff/candidate/transition/runtime/restricted/native/receipt suites with
`FC_TEST_GO`, `FC_TEST_NGINX`, `FC_TEST_HTTP_ARTIFACT` and `FC_TEST_SYNC_ARTIFACT`
pointing at accepted local tools/bundles. Run Android `control-tests` for protocol,
receipt, cryptographic identity and persistent cache tests. Local nginx/subprocesses
are disposable fixtures, not system services or production operations.

No APK version/build/install/publication is part of this gate. Android source now
has additional safe observability; a later authorized deployment must build/check
the same-signature canary APK containing it and install in place at the product
phase. Previously built canary53 does not gain this hook retroactively. An old APK
without correlated diagnostics cannot satisfy the new observation contract.
Unchanged HTTP/sync archives remain pinned; the separate operator and nginx trace
template must be staged from the newly accepted source at a future authorized run.
No attempt13, authority refresh, device operation, beta or FIELD-1 is authorized here.
