# WARM-START-FORMAL-ACCEPTANCE-2

## Result — PARTIAL / PRELIVE_SERVER_CHANGED

**COLLECTOR_DEPLOYMENT = NOT_RUN. READY_FOR_LIVE = NO. ATTEMPT_CONSUMED = NO.**

The accepted candidate passed immutable input verification. Entry gateway/API
invocations matched the accepted baseline. After one permitted same-key credential
renewal, but **before any collector deployment**, the existing gateway naturally
exited. The mandatory server-change stop was applied: no deployment, manual restart,
owner access, gate arm, ACK prompt or CONNECT followed.

This is not a new functional warm-start failure. No new warm-start episode took
place. Historical **FUNCTIONAL_WARM_START = PASS_IN_TESTED_SCENARIO**,
FULL_TUNNEL_EGRESS=PASS, TRAFFIC_AFTER_LEASE_DEADLINE=PASS and client provisioning
block PASS stand. Historical formal acceptance remains PARTIAL; its two evidence
gaps have not been closed by this aborted task.

## Exact inputs and scope

Protected capsule (not public/Git):
`state-client-build/field65-export16/warm-start-formal-acceptance-2/`.
Source candidate, schemas, scope, feature inventory, differential results and
rollback come unchanged from sibling `warm-start-collector-rebase-1/`.

| Identity | Exact value |
|---|---|
| Accepted validation source | `473ebe5768f3c78c8e36b4a79f26189f560cbadc` |
| Accepted gateway candidate, **not deployed** | `406a5ca4bdf8ff6b3a4d2edf4e392e572fcb5e3ff622fe74ce7121346aaadfe2` |
| Accepted API candidate, **not deployed** | `78bfc20f67e1b72c7907aad6fd3c0c4c7814a2915118288cec6e851ae7145fc6` |
| Gateway actual loaded/next | `21f0a0fdc27b50c00ea922f0b716516e2422aedf1b3797369718f7d00070509a` |
| API actual loaded archive/next | `12ca0c72a89ff20c1b3c70a1182a2d5d98d4d78d25e7a079bb4d75bdf34060ed` |
| Accepted candidate manifest | `22cb357b3c80cbec02bac83388cc724790d9cf70ca36c9c1625f74865161ed25` |

8144 rebase,4133 attribution and1616 functional-episode sealed inputs checked at
entry and closeout. No rebuild, product-source patch, commit, push, public release
or replacement of stale modules. AKI/skew/ACK/publisher and signaling classifier
baseline remain deployed. Local scripts only perform bounded preflight, authorized
renewal, immutable fatal preservation and abort evaluation.

Previously accepted test results remain **historical local acceptance**, not tests
rerun against a new deployment: contracts36×2, HTTP16×3, publisher19, evaluator9,
lease/observer race×3 and privacy/retention gates. Full suite remains NOT_GREEN with
the documented identical baseline assertions; no claim they were fixed here.

## UTC chronology and correlation

Times below are UTC or explicitly converted systemd MSK wall clock. No monotonic
clocks from different hosts were compared. Application/systemd evidence is joined
by exact InvocationID, not temporal proximity.

| UTC | Event / source | Correlation / confidence |
|---|---|---|
| 16:52:44 | Existing gateway invocation start; entry/runtime and systemd receipt | `1613fa1ce16d4ea5a649255ddf76829f`, PID1415977; direct |
| 19:52:50.852 | Pre-entry directory issued in the same invocation | directory `2287c6c5…9ec5e`; exact hash below; direct directory metadata |
| 20:04–20:06 | Fresh observer/API/NL/RU entry snapshots | Expected invocations active; NRestarts0, no receipt for running gateway; bounded snapshots |
| 20:09:41 | New same-key leaf issuance | `receipts/issuance.json`, lifetime14400s; direct |
| 20:09:45.446 | Strict/native validated credential publication | `receipts/renewal-publication.json`; no service restart |
| 20:12:48.289481941 | Natural application fatal | application receipt, original invocation, first SEED_READ/SIGNAL_READ/WS_CLOSE1011; direct |
| 20:12:48.374817 | systemd exit receipt | same invocation, `exit-code / exited / 1`; direct |
| 20:13:18 | Automatic replacement starts after configured30s | `4fafa22abf6c4bcbbc137375472855c7`, PID1540161, NRestarts1; direct |
| 20:13:21.417947895 | Replacement directory created | `4d722bad…15424`; direct directory metadata |
| 20:14:06 onward | Pre-deployment read detects changed invocation; strict chain read-only | Mandatory abort, no mutation/deployment attempted |
| 20:15:25 | Final observer snapshot | New invocation still active/observer armed; bounded, not10-minute stability |

The pre-fatal directory full hash is
`2287c6c5af470c7546fbb81dfca961950df8733031c7c80d4bb9a992a1c9ec5e`.
Its issued time and seed_generation2 support a rotated seed snapshot, not a
low-level cause or proof of provider lifetime policy.

## Fatal evidence — safe category PROVEN, underlying server reason UNKNOWN

23 existing application/systemd receipts copied **byte-exact** into private
`preserved-receipts/`; source SHA256/mode/ownership retained in
`receipts/preserved-receipts.json`. Original receipts were not regenerated, deleted
or edited. No journal query was made, including no retry of historical TIMEOUTs.

- Application: `application-1613fa1ce16d4ea5a649255ddf76829f.json`, SHA256
  `9fae6d22695208f451fc3370466ae0d5264562372e24b2fe43a5de0025106ecc`.
- systemd: `systemd-1613fa1ce16d4ea5a649255ddf76829f.json`, SHA256
  `2531d94a71a7faf28794ceb4e393baa8455756c555128cd90ac6a9d0ef41c9ef`.
- First immutable stage/cause: **SEED_READ / SIGNAL_READ**;
  safe class `sessiontrace.FirstClose`; `signaling_read.error_kind=WS_CLOSE`,
  `close_code=1011`, `context_state=ACTIVE`, `carrier_closed_at_observation=false`.
- Seed generation2, last confirmed stageSEED_RUN, brokerSEED_PUBLISHED,
  `exit_path=returned_error`, `fatal=true`, cleanup started/completed.
- Elapsed12004115ms, not the configured four-hour controlled completion.
- The receipt retains startup leaf expiry20:48:29 and2140s headroom with explicit
  `credential_snapshot=STARTUP_NOT_AUTHORIZATION`. This is **not** a statement that
  the newly published profile was rejected or that expiry caused this fatal.
- Standard WebSocket close code1011 is preserved; provider internals/close reason
  are not retained. No DPI, owner identity, credential, renewal or collector blame
  is assigned. Renewal preceded the failure, but causality is NOT_ESTABLISHED.
- This task issued no owner CONNECT or phone command. Unobserved independent
  background activity is not declared absent. Earlier historical UNKNOWN causes
  are not retroactively reassigned to1011.

## Credential operation and rollback

One renewal was authorized and performed before the server change was detected.
Pre-renewal leaf headroom2540s was below the3720s planned envelope: deployment300,
stability600, cache preparation600, operator120, startup180, lease720,
evidence/cleanup/rollback600 and local preparation reserve600 seconds.

Same root/issuer/gateway keys, authority, grants, admission/revocation and revision
floors preserved; existing14400s leaf lifetime unchanged. Issuance CRL23592 advances
normally; sync timer restored. Local strict Python/OpenSSL server/client, AKI/SKI,
native authority positive/negative validation and atomic service-readable publication
PASS. No owner refresh or new identity.

Post-automatic-restart strict served DER equals renewed profile leaf
`78f2b6bcdba298ab0c2633b976d7d755bb7a64e1bc6ebf639591fac5afe01fb3`.
Expiry **2026-10-13T00:09:41Z**, limiting leaf headroom14134s at20:14:06 snapshot;
authority and existing owner grant expire13Oct09:33:59Z. This is not future live
readiness. The current profile changes normally with CRL synchronization.

Protected baseline binaries/unit/drop-ins/configuration saved under each authorized
host's `restricted-materials-stage-20261001/warm-start-formal-acceptance2-20261012`.
Rollback **NOT_EXECUTED**: no candidate was deployed and existing service automatically
recovered. Renewed credentials and rollback backups retained; no cosmetic restart.
No AWG/TCP/mailbox restart. No private renewal material copied into Git/reports.

## Last observed server state

- Gateway active: PID**1540161**, InvocationID
  **4fafa22abf6c4bcbbc137375472855c7**, NRestarts**1**. Existing classifier
  loaded/next21f0a0fd…509a, argv/unit/drop-ins unchanged; listen127.0.0.1:18444,
  duration4h, chat-services, seed-rotate-after3h unchanged.
- Fatal observer armed in replacement; application directory0700/serviceUID979,
  systemd directory0700/root, files0600, counts11/12, retention32 each.
- API active PID**414703**, InvocationID**e9618550d9624ce887a2c392c4eb3e3f**,
  NRestarts0; same Python-I archive12ca0c72…060ed/port18086; no collector flag.
- New RU/NL directory full SHA256
  `4d722bad82ec131eefec4e74dc16ba4a8cfa7b4bc95b215fe30c984a09415424`,
  issued20:13:21.417947895Z, expires13Oct00:13:18.546119381Z. Existing sole-live-seed
  contract has no surviving old-invocation overlap. Owner cache was not reread and
  compatibility with this new seed is NOT_CHECKED.
- Sequential CRL23600/23601 snapshots differ while the existing sync timer runs;
  directory and authority equality proven, simultaneous whole-state equality not
  claimed. Strict chain is PASS; client mTLS/application READY NOT_ATTEMPTED.

## Required acceptance results

| Result | This task |
|---|---|
| COLLECTOR_DEPLOYMENT | NOT_RUN, mandatory prelive abort |
| DEPLOYED_FEATURE_PRESERVATION | Existing baseline retained; candidate seal PASS |
| GATEWAY_PRELIVE_STABILITY | ABORTED_BEFORE_DEPLOYMENT; no600s acceptance window |
| OWNER_ARTIFACT_AND_CACHE / EXACT_SELECTION | NOT_ACCESSED / NOT_RUN |
| TWO_PHASE_OPERATOR_PROTOCOL | NOT_ENTERED; no READY prompt or ACK requested |
| CLIENT_PROVISIONING_BLOCK / SERVER_OWNER_ATTRIBUTION / HTTP403_ATTRIBUTION | NOT_RUN; previous formal gap remains |
| CACHED_NATIVE_INPUT / TELEMOST_BOOTSTRAP / SEED_ADMISSION | NOT_RUN |
| FAMILY_AUTH / DEDICATED_READY / FULL_TUNNEL_EGRESS / DNS_EGRESS | NOT_RUN this task; historical functional PASS retained |
| CLIENT_LEASE_RENEWAL / SERVER_LEASE_RECEIPT / TRAFFIC_AFTER_OLD_DEADLINE | NOT_RUN |
| UNEXPECTED_CLOSES | One prelive shared-seed WS_CLOSE1011 fatal |
| GATE_CLEANUP | NOT_APPLICABLE; gate never armed by this task |
| OWNER_PRESERVATION | No phone actions; not a new byte/lifecycle verification |
| FORMAL_EVALUATOR_RESULT | NOT_RUN, no live evaluator inputs; aggregate remains PARTIAL |

## Counters and final limits

| Counter | Value |
|---|---:|
| operator ACK / physical CONNECT / manual reconnect | 0 / 0 / 0 |
| blocked provisioning operations initiated by task | 0 — no gate |
| owner server provisioning receipts / unrelated403 | NOT_MEASURED — collectors not deployed |
| native attempts / Telemost sessions created by task / full-phase requests | 0 / 0 / 0 |
| lease requests / accepted renewals / post-deadline requests in a task session | 0 / 0 / 0 |
| controlled gateway restarts / controlled API restarts | 0 / 0 |
| natural gateway fatal exits / automatic restarts observed | 1 / 1 |
| same-key credential renewals | 1 |
| owner install / instrumentation / refresh / gate arm | 0 / 0 / 0 / 0 |

No assertions about unrelated background request/session counts. Normal service
startup creates the replacement seed; this is not an agent-created synthetic
test room. Owner final lifecycle **NOT_OBSERVED**; previous VPN OFF/app ON/chat ON
is historical. Do not launch anything to cosmetically re-establish that state.

`RESULT.json`, `manifest.json`, `receipts/verification.json` and `SHA256SUMS` seal
local scripts, input verification, renewal/preflight and exact fatal receipts.
Original evidence retained; temporary local bytecode removed. No new production
artifact, source change or release was created.

**ATTEMPT_CONSUMED=NO. WHITELIST_WARM_START_READY=NO.**
**WHITELIST_COLD_START_READY=NO. REAL_RESTRICTED_NETWORK_FIELD=NOT_RUN.**
**PUBLIC_RELEASE=NOT_RUN.**

Функциональный warm-start ранее доказан. Новый formal-прогон **не начат**:
gateway естественно завершился до deployment; обязательный prelive gate остановил
задачу. Это не функциональный FAIL и не повторное доказательство PASS.

**Ровно следующая операция:** отдельный offline-разбор сохранённого natural
`WS_CLOSE/1011` и shared-seed lifecycle до возобновления live acceptance.
Ничего автоматически не развёртывать, не перезапускать и не выполнять CONNECT.
