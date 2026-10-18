# CRL-COMMIT-READ-BARRIER-1 — PARTIAL

## Decision

Two independent gates are established:

1. `COMMON_BARRIER_INFRASTRUCTURE_REQUIRED`: the exact baseline has independent
   RU/NL files and no authoritative activation/reader-fencing service.
2. `FROZEN_GATEWAY_BARRIER_INCOMPATIBLE`: the exact frozen executable rereads its
   local profile but neither consults a commit barrier nor persists a highest-seen
   epoch. An actual same-process TLS experiment accepts restored old profile N
   after rejecting revoked profile N+1.

**No deployable writer/receiver/barrier candidate is accepted.** The new code is
an isolated executable design model and a frozen-binary characterization probe,
not a hidden partial production reader. Frozen gateway bytes/source and all input
capsules remain unchanged. No production read or mutation was performed this task.

```
CRL-COMMIT-READ-BARRIER-1 = PARTIAL
TRUE_ATOMIC_VISIBILITY = REQUIRES_NEW_INFRASTRUCTURE
FROZEN_GATEWAY_COMPATIBILITY = FAIL
CRL_WRITER_DEPLOYMENT_READY = NO
CANARY_POLICY_CAN_CONTINUE = NO
```

Exactly next operation: **separate coordination/commit-ledger design acceptance**,
including fresh authoritative reads, durable antirollback and remote decision/session
fencing. This is the prerequisite selected under the new-infrastructure branch.
The independently required gateway semantic rebase is documented as a dependency,
not launched against an unspecified coordinator. No automatic deployment or canary.

## Exact baseline and evidence

Capsule: `state-client-build/field65-export16/crl-commit-read-barrier-1/manifest.json`.
All **941 sealed input entries** were verified across provenance, safety, policy,
trigger and observation-source capsules. Source-inventory hashes cover161 Python/Go
production source files in the retained closures;21 contain CRL-related references.
This does not attest every installed client/external Store binary in the fleet.

| Artifact | Exact identity |
|---|---|
| Deployed writer/receiver archive from provenance | `9faaa1c27f534e71774f5b4f34872e87747f391409c4958562694f07f86d64d1` |
| Safety source-only, unaccepted archive | `54c9715cdf6501ed87155f82e7e5ac9d593d446fee17310f7fe43be84e54b61b` |
| Safety source-tree hash | `74951952999062d973a3168d07dc1334eb01208656d60b3b90afd873576f84fb` |
| Exact API archive | `12ca0c72a89ff20c1b3c70a1182a2d5d98d4d78d25e7a079bb4d75bdf34060ed` |
| Frozen gateway source | `134083d87773dacc038c9593afdaff0c57ea951d` |
| Frozen gateway binary, used unchanged | `53beb661cab014c32494fa8d7384f9565300311ef467e62ae9f8c20201e5138f` |
| Historical observation gateway source | `a4087e000fdbe674b72ede3a6c8822445c87c654` |
| Historical observation gateway binary | `21f0a0fdc27b50c00ea922f0b716516e2422aedf1b3797369718f7d00070509a` |

The five critical control/Family/bootstrap/gateway/lease files have byte-identical
hashes in observation and frozen source. No approximate repository HEAD was used.
`receipts/inputs.json` includes prior manifest/seal hashes and this comparison.
No current PID, invocation or CRL number is inferred from historical receipts.

## Actual readers and split path

Full per-component source/input/reload/cache/validation/failure inventory:
`READER-INVENTORY.md` and `receipts/source-inventory.json` in the capsule.

- RU API `restricted.py._trust` reads local `revocations.pem` per operation and
  verifies signature/validity/number; no shared epoch or durable global floor.
- NL receiver writes CRL inside gateway profile JSON. Gateway `LoadCredentials`
  requires a private regular file. `ServerTLS.GetConfigForClient` and request/session
  authorizers reload it, but each authorization result precedes later effects.
- `familysession.Configuration` captures a parsed CRL in the TLS configuration;
  `Open/OpenReliable` retain a session security deadline. Send/Recv check expiry,
  not a newly committed revocation generation.
- Broker monitor periodically reauthorizes; bootstrap and lease renewal use local
  SessionAuthorizer. Polling and per-request reload are not an activation fence.
- Provisioning/native validation checks CRL supplied with the profile. The offline
  authority checker can validate old-but-unexpired N without knowing global commit.
- Exact API chat/publisher/notices/admission modules use separate product state;
  no same X.509 CRL decision path was found in those modules. External Store/mailbox
  and installed older/research clients lack a complete attested mapping here.

`READER_INVENTORY=COMPLETE_FOR_SEALED_CLOSURES`, not full-fleet completeness.
`FULL_DEPLOYED_FLEET_READER_INVENTORY=NOT_ESTABLISHED` remains a rollout gate.

The safety derivative's `publish → local_commit → peer.promote` exposes RU N+1
before NL switches. Both objects can be correctly signed while their revocation
decisions diverge. The existing private transaction marker does not bind readers.

## Frozen executable result

Disposable PKI, no activation/grant rows, actual unchanged executable, loopback
Family TLS/request authorizer. Local provider sink prevents any live Telemost
connection. One isolated gateway process, no rebuild, no service deployment.

| Experiment in the same process | Actual authenticated result |
|---|---|
| Local profile N | accepted |
| Signed fixture epoch2 sidecar + staged CRL N+1, local profile still N | accepted |
| Actual profile updated to revoked N+1 | rejected |
| Exact old N profile and local minimum restored | accepted |
| Profile removed | rejected |
| Old N restored after removal | accepted |

The signed sidecar is explicitly **fixture-only**, not a deployed/accepted coordinator.
Source inspection establishes the missing input; the executable proves local reload
and rollback acceptance. No claim of full seed/media/Mux/lease coverage from a TLS
probe. `receipts/frozen-barrier.json` records binary/helper hashes and cleanup.

A transparent file resolver cannot fix this: there is no mandatory online check,
captured session snapshots survive, and authorization/effect races remain. A missing
file rejects a new call but does not prove synchronous revocation of existing streams.

## Consistency model and selected design

`TRANSACTION-AND-READ-CONTRACT.md` defines byte, commit and visibility atomicity,
the four options, schema, state machine, clocks, activation, replay, recovery and GC.

**Conditional selection: Option A, a single authoritative signed ledger with online
fenced security decisions.** Not just a signed JSON pointer copied asynchronously.
There is no such accepted component in the current baseline. All affected gateway,
API and other security readers must participate; partitions sacrifice availability.

- N+1 is independently verified and fsynced on both nodes. Matching authenticated
  prepare receipts precede a signed immutable commit certificate.
- Certificate creation does not activate. Both sites stage/verify the exact certificate
  and return matching ACKs; old decision permits/security effects must drain or be fenced.
- Durable authoritative head CAS is the activation point. After it, only N+1 may
  authorize; missing/corrupt N+1 or uncertain authority means fail closed, never N.
- Old authenticated responses cannot be reused after activation. Merely querying
  latest epoch and then authorizing outside a fence is insufficient.
- Durable reader maximum epoch rejects rollback. Clean first start still requires
  a fresh authority query; the authority itself must not roll back on backup restore.
- After commit, recover N+1 or publish N+2 preserving revocations. No rollback to N.
- nextUpdate and certificate/process lifetimes remain independent validity limits,
  not a substitute for a commit protocol. No future activation time is selected.
- GC retains current+previous and all recovery references; authenticated registered
  reader acknowledgements, explicit retention and reference pinning are prerequisites.
  Production offline/retention policy is not invented here.

Option B needs clocks and previously enforced offline-reader fencing; two time-staged
certificates alone cannot stop a reader that missed them. Option C adds consensus but
still needs reader/effect fencing. Option D explicitly permits stale acceptance and
is rejected for this task. No simultaneous filesystem commit is promised.

## Executable model and limits

`model/reference.py` uses synthetic real Ed25519 signatures, exact safety-candidate
CRL parsing/semantic verification and protected local storage. RU/NL are independent
logical node stores; a single coordinator lock abstracts serialized decisions and
activation. Each reader verifies signed head, durable floor, exact hash/sequence,
issuer signature/CRL validity, leaf signature/validity and serial revocation.
No expected reader outcome is supplied by the test harness.

**38 tests ×3 PASS** with `/tmp/fc-lease-venv/bin/python` (Python3.14.4,
cryptography46.0.7). Includes30 requested abstract fault cases plus concurrent
decisions, permit drain, disk/mode/corruption, receipts/retention, node authentication,
path bounds, expiry/recovery and unknown-policy/symlink checks. System Python lacks
RNS; that import failure is retained separately, not counted as a product regression.

Success: candidate N+1 remains invisible before activation; after activation both
readers reject B, accept unrelated A, and report equal epoch/hash/sequence. There
are no ordinary activation/grant rows. `receipts/model-success.json` records results.

Critical partial publication regression:

- Before activation with one stage/ACK missing: both still read committed N.
- After activation with NL generation lost: RU rejects B using N+1; NL denies all
  decisions. NL does not fall back to N. Same result for missing RU generation.
- Authority unavailable: readers deny; offline reader returns through latest head,
  not its last locally valid file. New reader with no local floor and only N denies.

`FAILURE-MATRIX.md` includes actual reader outcomes/epoch/hash and recovery action
for each model observation. Detailed receipts/logs are sealed.

**Not established by these tests:** distributed RPC/network partitions, remote
permit drains/fences, active Family/Mux stream fencing, coordinator disaster recovery
antirollback, OS crash at every fsync point, real disk-full filesystem, complete
TOCTOU/ownership hardening, authenticated production GC or a full installed-reader
inventory. Clock offset/uncertainty is controlled in the model, not measured in
production. The synthetic issuer signing a new domain-separated record does not
authorize that signing purpose in production.

Concurrency tests are repeated Python thread tests, not Go `-race` or a distributed
linearizability proof. Full historical suite NOT_RUN; previous baseline failures
are not relabeled green. No product source changed, so there is no new product
candidate for which a differential acceptance PASS could be issued.

## Requested result inventory

| Result | Status |
|---|---|
| EXACT_BASELINE | PASS,941 sealed entries; historical provenance, not fresh runtime |
| WRITER_INVENTORY | Exact deployed writer + unaccepted safety derivative separated |
| READER_INVENTORY | Exact retained closures mapped; full installed fleet not established |
| CURRENT_SPLIT_BRAIN_PATH | PROVEN in prior safety receipt and exact source ordering |
| CONSISTENCY_MODEL | Defined; decisions/effects fence required, not just rename |
| DISTRIBUTED_ATOMICITY_LIMIT | Independent files cannot ensure strict visibility |
| COORDINATION_OPTIONS | A/B/C/D evaluated; D rejected |
| SELECTED_BARRIER | A, conditional single authority + online fencing |
| AUTHORITATIVE_COMMIT_SOURCE | NEW COMPONENT REQUIRED; not deployed/accepted |
| COMMIT_RECORD_SCHEMA | Strict signed model schema; production signing authorization pending |
| PREPARE_RECEIPTS | Independent authenticated synthetic node signatures in model |
| TRANSACTION_STATE_MACHINE | Defined; precommit invisible, postcommit rollforward only |
| ACTIVATION_CONTRACT | Authoritative CAS after both ACKs and old-effect fencing |
| CLOCK_SKEW_CONTRACT | No scheduled activation; fixture bound1s only, production bound unproven |
| READER_BARRIER | Model PASS; existing product readers lack it |
| ROLLBACK_PROTECTION | Model durable floor PASS; authority antirollback infrastructure required |
| CRASH_RECOVERY | Abstract signed-state reload tested; real coordinator crash acceptance pending |
| PARTITION_BEHAVIOUR | Simulated fail-closed PASS; no deployed transport/fencing proof |
| SEQUENCE_AND_EPOCH | Exact head/CAS monotonic in model; old staged state never current |
| IMMUTABLE_GENERATIONS | Exact-hash private model stores; corruption fails closed |
| GC_CONTRACT | Predicate/reference rules defined; production membership/retention pending |
| FROZEN_GATEWAY_BARRIER_COMPATIBILITY | FAIL, exact source + executable counterexample |
| LOCAL_MULTI_NODE_FIXTURE | PASS abstract38×3; NOT a deployed multi-node coordinator |
| FAILURE_MATRIX |30 modeled cases +8 focused tests; implementation limits explicit |
| CANARY_REVOCATION_CONTRACT | Both model readers reject; NOT accepted with frozen stack |
| SECURITY_AND_PRIVACY | Local crypto/negative tests + bounded retained-artifact scan; not production service security acceptance |
| SOURCE_ONLY_CANDIDATE | DESIGN_MODEL_ONLY; no product patch/accepted validation commit |
| PRODUCTION_UNCHANGED | All task-induced actions0; no fresh runtime equality assertion |

## Artifacts, patch boundary and counters

Capsule contains source inventory and input seals, exact-binary probe/log, model and
tests, failure outcomes, signed-generation hash receipts, privacy/scope report,
formal design, exact future gateway/API/writer delta plan, manifest and SHA256SUMS.
No synthetic private key/profile/CRL payload or production secret is archived here.
`patches/design-model-and-tests.diff` is local experiment code only; `patches/docs.diff`
is documentation. Requested production commit/prepare/activation/reader/recovery
patches are explicitly NOT_CREATED. No public control endpoint or ledger is installed.

```
PRODUCTION_CRL_WRITES = 0
PRODUCTION_SEQUENCE_CHANGES = 0
PRODUCTION_DEPLOYMENT = 0
PRODUCTION_RESTART = 0
PRODUCTION_RENEWAL = 0
PRODUCTION_IDENTITIES_CREATED = 0
PRODUCTION_DATABASE_MUTATIONS = 0
PRODUCTION_GRANTS_CREATED = 0
OWNER_CONNECT = 0
LIVE_TELEMOST_ROOM = 0
DEPLOYMENT = NOT_RUN
ATTEMPT_CONSUMED = NO
PUBLIC_RELEASE = NOT_RUN
REAL_RESTRICTED_NETWORK_FIELD = NOT_RUN
```

The new guard cannot be supplied by another asynchronous copy script. Preserve the
locally accepted supervisor/trigger feature stack, but do not treat its frozen binary
as compatible with strict atomic revocation. No next operation is run automatically.
