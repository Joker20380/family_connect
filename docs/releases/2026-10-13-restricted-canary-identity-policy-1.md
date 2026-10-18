# RESTRICTED-CANARY-IDENTITY-POLICY-1 — PARTIAL

**POLICY_ACCEPTANCE = NO. POLICY_CANDIDATE_NOT_CREATED.**
First mandatory gate remains open:
`DEPLOYED_REVOCATION_WRITER_SOURCE_IDENTITY_UNRESOLVED`.

The exact retained deployed HTTP API source is resolved. The same is **not** established
for the deployed authority/CRL writer: `restricted_admin.py` and `restricted_sync.py`
are not members of that archive, and the supplied latest runtime archive receipts do
not attest their deployed source/import closure. Old source-tree copies, a buildable
checkout and fixture sync archives do not establish deployed identity. No speculative
port, issuer CLI, migration, API candidate or validation commit is created across this gate.
This is an evidence/provenance limitation, not proof that a restricted-only policy is
impossible, nor a downgrade of the previously accepted supervisor/warm-start results.

## Exact inputs and preservation

Capsule: `state-client-build/field65-export16/restricted-canary-identity-policy-1/`.
`audit.py` verifies **10056 files** across the retained op-readiness, trigger, supervisor
and collector-rebase seals. All pass. Original evidence remains unchanged.

- Frozen source: `134083d87773dacc038c9593afdaff0c57ea951d`.
- Frozen executable: `53beb661cab014c32494fa8d7384f9565300311ef467e62ae9f8c20201e5138f`.
- Exact retained deployed HTTP archive:
  `12ca0c72a89ff20c1b3c70a1182a2d5d98d4d78d25e7a079bb4d75bdf34060ed`.
- Build manifest → deployment receipt → latest supplied RU archive observation all
  identify those API bytes.23 Python members are extracted byte-exact into `baseline-api/`.
- API deployed Git commit is not embedded; source identity is its verified archive,
  not current repository HEAD. The copied API source is unmodified.
- This task makes **no fresh production connection**. Previous PID/expiry/session values
  remain historical. It does not declare current credentials, active-session safety,
  full collectors or rollout readiness healthy.

AKI issuer logic, skew/validity, ACK freshness, publisher modules and public API schemas
in that archive retain their exact member hashes. Frozen classifier/supervisor/lease/
admission behavior and binary retain their original hashes. This does not imply local
collector candidates were deployed, or establish the separately deployed CRL writer.

## Actual activation and eligibility graph

Paths below are relative to `baseline-api/`; member SHA256 values are in
`receipts/baseline-coverage.json`. No ordinary user's record was read.

| File/function | Input/authentication | Mutation/capability/side effect | Role in product |
|---|---|---|---|
| `access.py` binding/challenge | Canonical public identity/WG key; invitation for first activation; purpose-bound nonce | Bounded challenge row,100s TTL | Ordinary enrollment/config access; proof is not entitlement |
| `access.py` complete | Signed transport-key proof, nonce, purpose, invite, key binding | New ordinary `devices` row, invite consumption, TCP ID, support metadata | Activates ordinary product; not a canary path |
| `restricted.py` `_enroll` | Admission list + active ordinary device/invite + trust | `restricted_grants` row linked to device | Restricted network entitlement; no chat registration itself |
| `restricted.py` `_grant`, challenge/fetch | Active grant/admission/revision/expiry + fresh proof + authority/directory/CRL validation | Restricted nonce, tracked certificate/profile response | Family network credential issuance |
| `restricted.py` `_issue` | Existing authority/signing key, validated caller inputs | AKI + leaf role=device/gateway, four OUs, bounded validity | Cryptographic issuance primitive, **not** an operator policy entrypoint |
| `chat.py` active/challenge/register | Independently checks same active device/invite, device proof and signed chat key | `chat_challenges`, `chat_bindings`; pending-node | Chat eligibility and registration are distinct |
| `chat.py` desired_members/snapshot; `chat_sync.py` synchronize | Active registered chat bindings; operator node sync | Membership snapshot/sequence; downstream node operation | Routed chat admission; not tested against live node |
| `friends_http.py` chat/register → `chat_publishers.py` configured | Successful chat registration, synchronized node, operator-configured exact device pins | Optional publisher configuration in authenticated response | No publisher config solely from a restricted certificate |
| `notices.py` device_request | Fresh purpose-specific ordinary device proof; independent Notices publisher registry | Notice role/publish/list/edit operations | No canary exemption; registry is not touched by rejected fixture requests |
| `referrals.py` issue | Ordinary proof and active sponsor | Referral state/invites | Not part of canary scope |
| External mailbox/LXMF/Store/dashboard | Separate deployed components | Not in this recovered API bundle | Full negative acceptance remains NOT_RUN |

**Coupling:** ordinary activation makes both restricted enrollment and chat eligibility
possible through the same device/invite predicates. It is not a single
`restricted == chat` flag, and a restricted grant does not itself create a mailbox.
No subscription/payment expiry is part of this exact Friends activation path.

## Local evidence actually executed

### API baseline:23 checks PASS

`policy_probe.py` imports the verified deployed `.pyz`, not the dirty repository.
Disposable DB and in-memory fixture identities only. The real HTTP handler is exercised
in-process, with no network listener, node sync or registration subprocess.

Checks include unactivated status, proof replay, admission-list-alone rejection,
chat eligibility/challenge/registration rejection with valid fixture signatures,
absent publisher pin config, empty chat membership, no canary route, client-selected
purpose/extra-role/test flag rejection, notices role/publish/list/edit rejection,
ordinary configuration rejection, unchanged ordinary activation response schema and
replay rejection, and ordinary activation enabling both network and chat predicates.

The last check demonstrates an important required future protection: **baseline has
no reserved synthetic-key namespace**. That unused fixture key can later ordinarily
activate with a valid invite. A future policy must prevent this, including challenges
created before reservation; a label or omitted initial activation alone is insufficient.
Two ordinary disposable fixture activations are controls, NOT production canaries and
NOT substitutes for a restricted-only issuance path.

### Exact frozen executable:10 TLS checks PASS

The existing frozen executable runs unchanged as a local child. `/proc/<pid>/exe` hash
is checked. Its production `ServerTLS`/Family verification/`RequestAuthorizer` path accepts
an existing four-claim device certificate without an activation DB and rejects:

- invented `RESTRICTED_CANARY_TEST_ONLY` wire role;
- extra canary OU, wrong family or below-floor revision;
- expired, future, wrong-EKU or revoked certificate;
- wrong subject/device binding.

Strict TLS1.3 with CA/hostname validation; no verification bypass. A separately built
minimal standard-library Go **test client**, not a rebuilt gateway, sends one leaf.
The positive response is authenticated **HTTP503 because no seed exists**. This is
NOT seed/dedicated/media/lease PASS, not an issued test-only grant, and not evidence
that the full proposed policy is gateway-compatible.

The provider CreateRoom request is intercepted at a loopback CONNECT sink that never
connects/forwards upstream and never responds with provider metadata. No Telemost room
or real OAuth is used. Disposable authority represents the existing Family format in
a local fixture only: no production root/issuer/trust store is created or changed.
Client keys remain in memory/stdin; the gateway execution profile exists briefly in
private0600 tmpfs under0700. It is destroyed, not archived or treated as a sealed
production credential store.

Initial sandbox sockets were denied; an approved outside-sandbox loopback run was used.
Two initial Python-TLS harness attempts received BAD_CERTIFICATE and were cleaned up;
they are not policy/gateway regression evidence. The final single-leaf Go client passes.
Six conservative evaluator tests pass; missing provenance or TLS-only evidence cannot
produce policy acceptance. Full suite/race, new issuer, external Store/mailbox negatives
and baseline-vs-policy-candidate differential are **NOT_RUN**, not green.

## Proposed scope — not executable/accepted

`POLICY_DESIGN.md` describes `RESTRICTED_CANARY_TEST_ONLY` as operator policy, while keeping
the frozen wire role `device`; fixed issuer path, no public HTTP test switch, transactional
key reservation, separate inventory, existing PKI and authoritative CRL integration,
sealed custody, bounded use, audit and revoke/publication/rejection/private-key destruction.
`schema-draft.json` is a strict safe-envelope **proposal**, not a signed grant, migration
or authorization. Operator command/security/storage implementation is NOT_CREATED.

Important frozen constraints are explicit rather than silently relaxed:

- One outstanding holder per exact identity. Simultaneous persistent session plus second
  bootstrap cannot be assumed possible with that same identity (`device_busy`).
- An API inventory counter/run ID is not read by the frozen broker; do not assert it
  enforces a new max-bootstrap quota or per-canary destination ACL.
- Inherited future deployment arithmetic2710s+180s is a planning input, not permission
  to extend cert/profile/CRL/directory validity or bridge canary and deployment indefinitely.

## Result matrix

| Required item | Result |
|---|---|
| DEPLOYED_BASELINE | PARTIAL: exact HTTP archive resolved; authority/CRL writer provenance unresolved |
| CURRENT_ACTIVATION_CALL_GRAPH | RECOVERED for exact API; external consumers explicitly unverified |
| CURRENT_RESTRICTED_CHAT_COUPLING | PROVEN at independent shared ordinary-device/invite predicates |
| CANARY_ROLE_AND_SCOPE / DATA_MODEL / BOUNDS_AND_VALIDITY | DRAFT_ONLY; no new gateway claim or decorative enforced quota |
| ISSUANCE_PATH | NOT_CREATED — mandatory baseline gate |
| PUBLIC_API_ISOLATION | Existing strict handler negatives PASS; no new endpoint |
| TRUST_AND_PKI_PRESERVATION | Production untouched; disposable local fixture only |
| FROZEN_GATEWAY_COMPATIBILITY | PARTIAL: exact-binary TLS PASS; full issuance/bootstrap/Mux/lease NOT_PROVEN |
| KEY_STORAGE / AUDIT_RECEIPTS | Runtime fixture cleanup PASS; production custody/audit implementation NOT_CREATED |
| ORDINARY_ACTIVATION_DIFFERENTIAL | Baseline control PASS; candidate differential NOT_RUN |
| CANARY_NETWORK_POSITIVE_TESTS | TLS control boundary only; seed/dedicated/TCP/DNS/lease NOT_RUN |
| CHAT_NEGATIVE_TESTS / PUBLISHER_NEGATIVE_TESTS | API predicates/handler tests PASS; full mailbox/Store paths NOT_RUN |
| SECURITY_TESTS |23 API checks +10 frozen TLS checks PASS; new issuer security NOT_RUN |
| OLD_CLIENT_COMPATIBILITY | No existing bytes/schemas changed; new policy not accepted |
| REVOCATION_AND_CLEANUP | Design only for future issuance; exact deployed writer required |
| PATCH_SCOPE | Tests, evidence copies, design/docs only; product diff NONE |
| LOCAL_CANDIDATE | NOT_CREATED; no validation commit or replacement frozen binary |
| PRODUCTION_DEPLOYMENT / PRODUCTION_IDENTITY_CREATED | NOT_RUN / NO |

Production synthetic identities/grants/DB mutations/deployment/restart/renewal =0.
Owner CONNECT=0. Live Telemost rooms=0. ATTEMPT_CONSUMED=NO.
PUBLIC_RELEASE=NOT_RUN. REAL_RESTRICTED_NETWORK_FIELD=NOT_RUN.

**Exactly next operation:** recover and verify the deployed revocation-writer source/
provenance capsule (entrypoint, import closure and certificate→grant→CRL decision),
then resume this source-only policy task. Do not proceed to operational identity
issuance, credential staging, real-Telemost canary or deployment from this PARTIAL.
