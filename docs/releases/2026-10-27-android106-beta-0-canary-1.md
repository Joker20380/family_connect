# ANDROID-CONTROLLED-BETA / BETA-0-CANARY-1

## Exact-payload CRL delivery — source-only gate

**LIVE_ENTRY_SOURCE_READY / CRL_HELPER_UNBOUND_READY / PRODUCTION_LOOKUP_NOT_RUN /
LIVE_WRITES_NOT_RUN.** Input main `11b99a6cae1c9c8722b266bd773caa821d3e3a61`;
accepted bounded-dispatch source `ad086c030cc77c680d924fb9c8e37faa286adc4c` unchanged.
Same BETA-0-CANARY-1; no new top-level task. No production access or operational action.

### Source and authority boundary

- New helper/packager and their tests only; minimal existing restricted_admin refactor
  extracts pure build_crl_payload. It reads a query-only snapshot, computes the existing
  paid-aware deny set, signs once and returns PEM, number/timestamps/serial metadata.
  It does not change any DB row or file. Existing publish_crl delegates to it and keeps
  its public/operator behavior, including valid lifetime choices and monotonic floor.
- Canary lifetime900s; generated number=max(previous CRL number, stored sequence)+1.
  Expected certificate must be newly revoked; other newly added serials require
  independently proven current deny/revision/family reasons. Allowed unrelated
  certificates are excluded. Serial output uses HMAC(decimal serial) short tokens
  privately; sanitized receipts never expose raw serials or CRL contents.
- Immutable bound-envelope contract is tested only with synthetic values: alias,
  operation_id, HMAC device/safe_ref, version3/count3/expired, exact certificate token
  and <=300s generation window. Two payment events followed by explicit expire,
  current Android106 eligibility, non-revoked device/invite, paid denial and valid
  authority/revision/family/identity-bound certificate are required. No other cohort
  member is allowed. No helper operation can change paid/identity/invite/grant state.
- No default/live configuration, host, key, credential, readback transport or bound
  package is installed. Public CLI is help/manifest only; it cannot run prepare,
  deliver, commit or accept operational input. Future configuration/transport injection
  must be fixed and operator-reviewed, never supplied via public input. Existing
  sync lock identity must be verified by that future configuration, not guessed here.
- Existing gateway returns directory only. Acceptance additionally requires trusted
  authenticated readback of exact payload SHA256, installed CRL number and minimum_crl.
  Plain directory output is not treated as that proof. Existing strict directory
  parser checks time/family/gateway/seeds; no new signature or wire schema is invented.

### Immutable operation and delivery

Preparation holds the configured existing restricted-sync lock and opens authoritative
DB read-only. Exclusive0700 operation directories and0600 regular/non-symlink/single-link
files retain PEM, exact canonical compact JSON request (only revocations), hashes,
generation metadata, prior local hashes/sequence, safe revoke tokens and private
fingerprints. Journal updates are authenticated, atomic and parent-fsynced. Key and
canonical device/selector/certificate body are never persisted in the journal.

Generation_count=1 for every prepared operation. Existing directory prevents any
second generation, including after a partial preparation crash. Payload/request bytes
are hash-checked on every resume, never recomputed for retry. Request<=20000 bytes,
PEM<=16384, returned directory<=8192; duplicate/nonfinite JSON is rejected.

| State/outcome | Continuation |
|---|---|
| PREPARED |One delivery of saved request bytes |
| DELIVERY_IN_PROGRESS after crash |DELIVERY_UNRESOLVED; no resend |
| NOT_SENT with proven pre-execution failure |TRANSPORT_NOT_SENT; one exact-byte retry, at most2 attempts |
| Generic exit/timeout/lost/partial output |UNKNOWN / DELIVERY_UNRESOLVED; readback only |
| Definitive pre-apply rejection |REMOTE_REJECTED; no retry |
| Valid exact gateway acceptance |REMOTE_ACCEPTED; local commit only |
| Local commit begun |LOCAL_COMMIT_IN_PROGRESS; reconcile files/DB |
| Remote accepted, local I/O failure |LOCAL_COMMIT_FAILED / REMOTE_ACCEPTED_LOCAL_COMMIT_FAILED; retain all evidence |
| Readback/hash/sequence complete |COMMITTED; idempotent local readback |

The adapter contract does not equate an arbitrary SSH exit with NOT_SENT or REJECTED.
Actual gateway tests prove same number/same bytes idempotency and reject same number/
different bytes (typed adapter outcome CRL_PAYLOAD_CONFLICT), bad signature/issuer,
rollback number and invalid time/lifetime. Gateway mutation followed by lost/invalid
directory output is uncertainty, not proof of pre-apply rejection.

### Local commit and crash reconciliation

After remote acceptance: recheck prior CRL/hash/sequence and relevant paid/event/device/
invite/certificate/authority fingerprint; fsync local temp files, persist in-progress
journal, set exact sequence, atomically replace CRL/directory, fsync parents, commit
SQL, read back exact bytes/sequence and mark COMMITTED. Newer/conflicting local state
is not overwritten. No payload regeneration or second delivery repairs local failure.

| Restart case | Action |
|---|---|
| A: DB old, CRL old, directory old |Commit exact saved payload/response |
| B: DB new, CRL new, directory new |Validate and mark COMMITTED |
| C: DB old, CRL exact new |Finish sequence/directory from saved evidence |
| D: DB new, CRL exact old baseline |Install saved CRL/directory without incrementing again |
| E: Unknown/conflicting number or hash |LOCAL_COMMIT_CONFLICT; no generation/delivery |

Current directory hash must match exact old or validated new bytes in every case.
UNKNOWN trusted readback proving exact installed payload transitions REMOTE_ACCEPTED;
old payload remains unresolved, with no automatic resend; conflicts fail READBACK_MISMATCH.

Typed results: PASS, LOCK_BUSY, INVALID_PERMIT, PRECONDITION_FAILED,
CRL_GENERATION_FAILED, CRL_GENERATION_ALREADY_COMPLETED, CRL_EXPECTED_SET_MISMATCH,
CRL_UNEXPECTED_REVOCATION, TRANSPORT_NOT_SENT, TRANSPORT_FAILED,
CRL_DELIVERY_UNRESOLVED, CRL_PAYLOAD_CONFLICT, REMOTE_REJECTED,
GATEWAY_VALIDATION_FAILED, DIRECTORY_VALIDATION_FAILED, LOCAL_PRECONDITION_CHANGED,
REMOTE_ACCEPTED_LOCAL_COMMIT_FAILED, LOCAL_COMMIT_FAILED, LOCAL_COMMIT_CONFLICT,
READBACK_MISMATCH. Receipts use only the prescribed sanitized allowlist; no stderr,
raw exception, profile, directory, URL, host, private path or key is returned.

### Source validation

| Gate | Result |
|---|---|
| New CRL helper / package tests |95 /3 PASS |
| Existing canary / paid backend / preparation |79 /76 /2 PASS |
| Existing restricted/admin/sync/directory/window tests |206 PASS,29 existing optional Go/native skips,4 explicit native deselections |
| PostgreSQL console / Django check / migration drift |118 PASS / PASS / no changes detected |
| Syntax / strict JSON / private-content scan / scoped links / staged scope / diff checks |PASS |
| Production registry/lookup/binding/CRL/delivery/paid writes |NOT_RUN |

Tests exercise the actual existing gateway against synthetic local files, not live
transport. A first run's3 isolated-sync tests rejected a venv site path inside checkout;
unchanged tests passed using the same accepted dependencies copied to an external
disposable venv. No production/path workaround or test assertion weakening. No native
build, Android action, full historical suite, Linux/Windows task or Friends restart.
Console tests used a separate disposable local PostgreSQL test DB.

Accepted lookup-only artifact remains unchanged:15 members/56017 bytes/SHA256
`63ffe0f1ac4dad0c15a94558423de4eab2a5aff754167e8108d75064bb95d308`.
Its source inventory excludes the changed restricted_admin and new helper; no rebuild
is needed. New unbound CRL package receipt follows after exact source commit/build.
No bound envelope/activation/expire/recovery permit is built.

The first post-commit package audit found IP constants in unused catalog-validation
functions. It was rejected by the capsule's no-IP gate and retained privately, not
delivered. A packaging-only follow-up extracts exact committed source segments for
the five required strict-parser functions and their two stdlib imports; no function
is rewritten, no authority/parser policy is relaxed. The full source blob hash,
selected names and exact segment hashes are recorded in source_projections, alongside
ordinary member hashes. Unused catalog/profile code and all IP constants are excluded.
AST equality, isolated import/help and deterministic package tests PASS. No accepted
lookup artifact or backend source is changed by this packaging correction.

**STOP. NEXT — production read-only owner lookup and binding, not automatically.**
No production key/configuration installed, no CRL publication or local live files
changed, no CP2 redeployment or gateway/Android change. Historical evidence retained.

## Historical bounded recovery dispatch — source-only continuation

**SOURCE_READY_WITH_EMERGENCY_RECOVERY / LIVE_NOT_RUN.** Input main
`3a5e91d06977eb86fa78dec386477518fb5a0bfc`; accepted emergency source
`49bdd794cce32075d93691daa0b9f9cc7f7dffcf`. Same checkpoint, no new PLAN ID.
Only the practical dispatch guard, focused tests/docs and local lookup-only package
change. This is not completion of the broader live-entry preparation.

- New recovery first apply accepts `period_start<=server_now` and
  `server_now-period_start<300`: execution at start or1..299 seconds later can pass.
- Preserve exact `paid_until-period_start==2592000`, inclusive static period-start
  bounds `not_before<=period_start<=not_after`, half-open execution window
  `not_before<=server_now<not_after`, and `0<not_after-not_before<=300`.
- Never rebase or extend the signed-off payload: expiry is30 days from permit start,
  not30 days from delayed execution. Backend receives original period fields.
- Future dispatch, delay>=300s or a closed execution window fails typed
  `RECOVERY_DISPATCH_WINDOW_CLOSED` without inserting an event. Invalid duration or
  static period bounds still fail `INVALID_RECOVERY_PERIOD`; invalid window length
  still fails `INVALID_EXECUTION_WINDOW`.
- Normal four-stage path, version/state/certificate/eligibility guards, backend
  authority and terminal marker remain unchanged. Identical terminal recovery replay
  bypasses new-event dispatch checks; changed payload remains `EVENT_ID_CONFLICT`.
- Certificate/CRL state is not modified. Internal purpose/zero amount, sanitized
  receipts and non-paid fingerprints remain unchanged.

### Dispatch validation

| Gate | Result |
|---|---|
| Canary operator tests |79 PASS |
| PostgreSQL console tests / affected paid backend / preparation |118 /76 /2 PASS |
| Django system check / migration drift |PASS / no changes detected |
| Staged syntax / strict JSON / private-content scan |PASS |
| Staged Markdown local links / anchors |444 /23 PASS |
| Scoped staged diff / git diff --check |PASS |
| Production lookup/registry/binding/write permits/live operations |NOT_RUN |

Both recovery versions cover dispatch0/1/150/299s, unchanged payload/expiry and
actual server applied_at. Negative tests cover future start,300/301s delay, shortened
execution window, out-of-bounds period start and invalid duration/window length;
rejections preserve registry snapshots. CLI tests use the server clock at0/1/299s,
reject300s and prove no rebase. Existing idempotency/terminal/normal-path tests PASS.
Console tests use a separate disposable local PostgreSQL test DB; no running-console
upgrade, backend deployment or production connection is performed.
Unrelated unstaged operational notes remain untouched, including one pre-existing
missing Markdown anchor found by the working-tree check; the staged link gate passes.

### Dispatch lookup-only artifact

Source/tests/docs committed and pushed as
`ad086c030cc77c680d924fb9c8e37faa286adc4c`; remote main SHA independently verified.
Two independent builds from that exact committed source are byte-identical.

| Field | Verified value |
|---|---|
| Source commit |`ad086c030cc77c680d924fb9c8e37faa286adc4c` |
| Binding / envelope |`lookup_only` / null |
| Members / size |15 /56017 bytes |
| SHA256 |`63ffe0f1ac4dad0c15a94558423de4eab2a5aff754167e8108d75064bb95d308` |
| Strict manifest / exact member hashes / committed-source equality |PASS |
| Non-wrapper source members unchanged from accepted49bdd794 |PASS |
| Python syntax / strict JSON / private-selector scan |PASS |
| Import and --help smoke outside repository import path |PASS |
| Historical c5f2346c artifact unchanged |PASS |
| Bound/write-permit archive / production registry opened |NOT_BUILT / NOT_OPENED |

Both new artifacts are read-only inside private ignored evidence. Historical
artifacts/evidence remain untouched. Smoke executes only --help; no lookup, status,
apply or registry connection. No binding, credential or permit is included.

**STOP. NEXT — obtain the exact-payload CRL delivery helper contract, complete its
source gate, then read-only owner lookup/binding and coordinated phone preparation.**
The helper contract was not supplied in this continuation and is not invented.
No production lookup, binding, CRL generation/publication, Android action, payment,
enrollment, Friends restart or CP2 change. Live phone operations wait for owner ГОТОВ.

## Historical emergency recovery source gate —49bdd794

**SOURCE_READY_WITH_EMERGENCY_RECOVERY / LIVE_NOT_RUN.** Input main
`68b99ac667c78fa6f20f95ffa443cdbd7d1a5ef7`, accepted previous product source
`28657bf9e53411a4cdaff44d8ad5ebfb252046e0`. Same BETA-0-CANARY-1 under the existing
Android critical path. Only source/tests/docs and local lookup-only packaging;
no production registry/lookup, binding, enrollment, real payment, CRL publication,
Android action, Friends restart/deployment, CP2 backend change or desktop work.

### Exact recovery contract

- Normal activate0/activate1/expire2/activate3 sequence retained. Separate permit
  action recover is allowed only at expected_version1 or2, matching current
  subscription version and paid-event count. Versions0/3, explicit expiry and
  terminal revoke cannot start emergency recovery.
- First/second activation must already exist; all prior events are payments.
  Subscription stored state active, effective_state expired and paid_allow false
  prove natural expiry. Existing backend rechecks exact Android106 eligibility,
  non-revoked device/invite and existing admission restrictions. Full bound HMAC
  token/safe_ref/alias and no-other-cohort-member guards remain unchanged.
- Exact30 days: period_start=server_now, paid_until=server_now+2592000. First apply
  rejects a past/future start rather than rebasing the permit. Static bounds require
  period_start within not_before..not_after, execution within the half-open window,
  and window length1..300 seconds. Other durations fail INVALID_RECOVERY_PERIOD.
- Certificate inventory must exist and have no bound row with expires>server_now.
  Certificates, expiry/revision and non-paid tables remain unchanged. Future live
  procedure must wait any issued certificate's NotAfter+30 seconds; that wait and
  phone/serial observation are not performed or claimed by this source gate.
- Delegate to existing paid_beta.apply_event(event_type=payment), unchanged schema,
  APK attestation and authority. The transient reference is
  internal-canary-recovery:<event_id>; backend stores its SHA256, not raw text.
  No new event type, field, table, identity, invite or entitlement machine.
- Terminal detection reads reference_hash against SHA256 of that prefix plus each
  existing event ID. Find the incoming event first, then check the terminal marker,
  then run guards for a new event. A different ID after recovery fails
  RECOVERY_TERMINAL, including old normal-event replays. Same ID/backend payload
  returns the existing event; changed payload fails EVENT_ID_CONFLICT. Replay is
  permitted after window/entitlement expiry and does not extend the original period.
- After version1 recovery: active/version2/count2 and
  NATURAL_PHASE_ABORTED_OWNER_RECOVERED. After version2 recovery:
  active/version3/count3 and CRL_PHASE_ABORTED_OWNER_RECOVERED. The checkpoint's
  normal path is permanently closed after either branch. Classification is derived
  from immutable event order, not a replay caller's changed expected_version.
- Safe wrapper output adds branch emergency_recovery; purpose internal_canary and
  amount0 stay non-revenue. Raw authoritative backend event/receipt is unchanged.
  No selector, canonical device, HMAC key, raw reference, invite or certificate body
  enters the sanitized output. Transactional non-paid fingerprints are checked;
  unexpected trigger side effects roll back the whole new event.
- CRL number/entries are not generated, published, removed or rolled back. An old
  expired serial may stay in CRL; proving a future new certificate has a different
  unlisted serial is live acceptance, not a source-checkpoint side effect.

### Required validation

| Gate | Result |
|---|---|
| All canary operator tests, including normal path |68 PASS (30 existing +38 emergency cases) |
| Existing PostgreSQL console tests |118 PASS in separate disposable test DB |
| Existing affected paid backend tests |76 PASS |
| Existing preparation tests |2 PASS |
| Django system check / migration drift |PASS / no changes detected |
| Staged source syntax / strict JSON / secret-private scan |PASS |
| Markdown local links / anchors |446 /23 PASS |
| Staged scope / working and staged diff --check |7 files / PASS |
| Production lookup/registry access/binding/live procedure |NOT_RUN |

Emergency tests cover both versions, active/valid-certificate/revoked/explicit-expire
denial, exact period/start/window, token/alias/safe_ref/device/eligibility guards,
sanitized zero-amount classification, unchanged identity/invite/support/certificates/
CRL sequence, transactional rollback, concurrent replay, payload conflict, terminal
normal-path/recovery rejection and exact server-clock CLI behavior. Existing normal
expire/final certificate guards still PASS. Tests use generated synthetic identities
only. Packaging tests now build only lookup_only archives and smoke --help; no bound
permit archive is created even by those packaging fixtures.

The console image/schema/configuration was not rebuilt/restarted/migrated in this
source checkpoint. No historical full suite, CP2 source/package gate, Linux or Windows
gate repeated. Prior production counts0/0 remain accepted input, not a fresh live read.
Source commit `49bdd794cce32075d93691daa0b9f9cc7f7dffcf`
(`feat: add terminal emergency recovery for owner canary`) pushed to main; remote
SHA verified before packaging. Prior lookup artifact c25447d9… stays immutable
historical evidence and was independently verified unchanged.
Pre-existing123 added lines in unrelated working-tree edits and untracked work are
preserved outside this source commit; private validation evidence remains ignored.

### Deterministic emergency-capable lookup artifact

| Field | Exact result |
|---|---|
| Source commit | `49bdd794cce32075d93691daa0b9f9cc7f7dffcf` |
| Binding | `lookup_only` (envelope null) |
| Members |15 |
| Size |56021 bytes |
| SHA256 | `c5f2346cd4d46a6bf3875e2181e81027c7db43f62b886161756230b6499adc31` |
| Independent builds |2; byte-identical PASS |
| Strict manifest / exact inventory / member hashes |PASS |
| Members match exact committed source |PASS |
| Existing backend/identity modules match accepted28657bf source |PASS |
| Python syntax / private-selector scan / local import-help smoke |PASS |
| Production registry opened / bound permit archive / live operation |NOT_RUN / NOT_BUILT / NOT_RUN |

Both newly named local artifacts are retained read-only in private ignored evidence;
no historical archive was replaced. Only sanitized package metadata is committed.
This artifact includes the recovery source but cannot perform a bound operation:
lookup_only does not carry a device binding or operation permit. Smoke used --help,
not lookup/status/apply, and did not open any registry. No automatic next-stage run.

**STOP. NEXT — production lookup, binding and coordinated owner-phone live procedure.**
Do not start that next stage automatically; this checkpoint grants no live execution.

## Historical continuation from55c6a24 — local upgrade and bounded operator

**CHECKPOINT / LOCAL_CONSOLE_UPGRADED / CANARY_OPERATOR SOURCE_READY / LIVE NOT_RUN.**
Same task and same sole OWNER_CANARY_1 authorization; no new top-level PLAN ID.
The owner has supplied the four live goals and the final same-identity recovery
target of server_now+30 days. The continuation stops at the suggested component
paths; short live windows, reviewed CRL delivery and physical-phone coordination
have not been supplied. They were not guessed.

### Local console upgrade

- Private backups: PostgreSQL custom dump and the complete synthetic volume, taken
  while the local console was stopped. Online PG dump remains consistent while the
  separate read-only inventory monitor runs. PG disposable restore/open and SQLite
  disposable restore/integrity/FK checks PASS. Files0600/directory0700; no backup,
  DB, credentials or private receipt committed.
- `.env`, inventory HMAC key and operator credentials backed up privately and
  verified byte-identical after upgrade. No credentials printed or regenerated.
- Source-only preparation and local image rebuild completed; running migration
  now0006. Django system check and migration drift PASS. Console health PASS;
  HTTP remains127.0.0.1:8765, PostgreSQL has no published port.
- First local start stopped before Django because a restrictive umask produced
  root-owned source files unreadable by the non-root console user. Preparation now
  sets only copied allowlisted generic source files0644/directories0755 beneath
  private `.local`0700. Original source/private permissions unchanged. Rebuild and
  local start PASS. This was not a production restart or a paid-service failure.
- Running image ID: `sha256:1e28103e380a4acd5143f7055feb49ad6019ebe2fd01b142fd37f06d336752d9`.
  Application payload is the accepted55c6a24 console source; the preparation fix
  changes context permissions, not the entitlement authority or Android artifact.
-50 synthetic device bindings and synthetic registry devices/invites/support/paid
  tables preserved; all prior workflow rows preserved. Existing3 payment records
  now have default customer_payment.559 prior audit rows compared to the restored
  backup and retained unchanged;8 concurrent inventory.import records were appended
  at the comparison readback. Projection observation timestamps refresh normally.
- No real-owner DeviceProjection or synthetic substitute created. Production
  write actions remain absent: Django still opens only the guarded synthetic
  registry. No production DB is mounted or copied into Django.

### Canary-only source boundary

`control/friends/paid_beta_canary.py` delegates status/activation/expiry, idempotency
and conflict detection to the unchanged `control.friends.paid_beta`. It provides
read-only transient-stdin lookup, then full HMAC-token-bound status and a fixed
single-operation permit. No runtime write selector/reference/event/time override;
no revoke/grace/delete/migrate/restart/CRL operation. Exceptions/receipts do not echo
the selector, key, raw device or registry path.

The bounded workflow has at most four new events: initial activation, activation
after natural expiry, explicit expire with a still-valid certificate, and recovery
after all retained target certificates expire. Each operation needs a separately
reviewed exact envelope (server execution window at most15 minutes; no default
paid duration; ceiling31 days). Existing paid backend remains the only state machine.
Guards reject a second cohort member, stale versions/counts, bad bindings, invalid
Android eligibility and non-paid table changes. Duplicate permits return the
original event plus fresh status, never an implicit renewal.

`scripts/package_paid_canary_operator.py` exports only allowlisted committed
sources with source hashes/license/dependency metadata and an optional immutable
safe envelope. Repeated builds are byte-identical; dirty source, DBs, `.env`, keys,
private selector and other operator modules are excluded. No production-bound
envelope/package or owner token has been created. No package was uploaded/executed
on a gateway. There is no new Django production adapter or receipt importer; any
future import must validate a strict sanitized safe_ref-keyed receipt, not create
a fake DeviceProjection or authoritative subscription copy.

Committed lookup-only artifact (not bound to an owner and not deployed): source
`28657bf9e53411a4cdaff44d8ad5ebfb252046e0`,15 members,52921 bytes, SHA256
`c25447d92bcc3edd0b26889734465e759cbb5a682697f055a3d64a847a894e8e`.
Independent repeat build byte-identical; internal source-manifest hashes and local
CLI import/help PASS, no registry opened. Both private artifacts retained read-only.

### Validation and remaining boundary

-118 PostgreSQL console tests PASS on the rebuilt image in a separate disposable
  test database: purpose defaults, zero canary acceptance/customer rejection and
  analytics separation included. System/drift checks PASS.
-76 existing affected paid backend tests PASS using the retained control/identity
  environment. No CP2 source/package gate or repository full suite repeated.
-30 new canary wrapper/packaging tests +2 restrictive-umask tests PASS, including
  real synthetic backend transitions, denial/recovery/idempotency/conflict, guarded
  stage/window/certificate/binding/eligibility rejection, unrelated-trigger rollback,
  strict input/no echo and packaged subprocess readback.
- Source closeout:11 staged source/test/doc files; Python syntax,448 local link
  targets, added-content privacy scan, strict private JSON and both staged/working
  `git diff --check` PASS. Unrelated pre-existing123 added lines and untracked work
  remain outside the commits. Private backups, credentials and historical evidence
  retained, never staged. Source commit pushed and remote SHA verified before this
  artifact-receipt closeout.
- Production lookup, binding, activation, expiry, live Connect/session, CRL delivery,
  recovery/reactivation and Android state readback remain **NOT_RUN**. No customer
  payment/enrollment, CP2 deployment/restart/migration, gateway/publisher/admission
  mutation or Android/Linux/Windows change. No canary slot occupied yet.

**Historical NEXT at28657bf/68b99ac — obtain the remainder of the live procedure and
coordinate the owner phone.** The final30-day active
and connect-capable owner state is a required future gate, not a claimed result.

## Historical result and scope at55c6a24

**CHECKPOINT / PAYMENT_PURPOSE SOURCE_READY / LIVE NOT_RUN.** Input main:
`6d5202128ebfda6b60446d4f85cd7d9e5f2323fc`. This is a substep of the existing Android
critical path, not a new top-level project or CP3. CP2 is owner-accepted **DONE /
PAID-AWARE EMPTY-COHORT BACKEND SERVING / PUBLISHER CAPABILITY PRESERVED /
REAL PAYMENT AND ENROLLMENT NOT_RUN**. Its deployment/migration/restarts and
source/package gates were not repeated.

The sole authorized production target is designated **OWNER_CANARY_1**. Planned
allocation is one permanent internal slot out of ten, leaving nine customer slots
after enrollment. No row or reservation was created: this allocation is not yet
an observed backend state. No alternate production identity was used. The private
administrative selector was not passed to tools, copied into operator files or
persisted in Git/docs/PG/audit/URLs/sessions/logs/screenshots/receipts/event IDs/
external references. No device-token mapping is invented: administrative lookup
and HMAC binding are NOT_RUN.

## Implemented operational metadata

- `PaymentRecord.purpose`: `customer_payment` / `internal_canary`; default and
  existing rows remain customer payments. Existing confirmation metadata is preserved.
- Customer amounts remain positive. Internal canary must have zero amount, is not
  a customer payment/revenue, and retains the existing currency field as zero-value
  metadata only. Model/form validation and PostgreSQL constraints fail closed.
- Purpose is immutable from creation, including before confirmation. Existing
  confirmed-record/intent/audit immutability, reference uniqueness and permissions
  remain in force. No payer/bank/secret/selector fields were added.
- Customer-payment analytics exclude canaries; a separate confirmed-canary-record
  counter is explicit, not a count of devices/cohort slots. Operational activity
  still counts operations, not revenue.
- Russian form/detail/preview screens, admin filter, new metadata audit rows and
  administrative receipt wrapper expose the purpose. Raw authoritative backend
  receipt is not modified; synthetic integration still produces `event_type=payment`
  with existing idempotency and one request/event behavior.

Friends `paid_beta` remains the only entitlement authority. No changes to its
schema/state machine/cap10/idempotency/challenge/fetch/certificate boundary, client,
protocol, keys, invitation or activation semantics. The console remains synthetic
for write workflows; production inventory remains read-only. No production device
was copied into a synthetic projection to bypass that separation.

## Validation and installation boundary

- 23 new PostgreSQL tests PASS: purpose defaults/constraints, pre/post-confirmation
  immutability, analytics separation, metadata-only no-enrollment, form/admin/receipt
  rendering, unchanged synthetic backend activation/idempotency, migration of an
  existing confirmed payment and repeated migrate with a fresh migration loader.
- 118 console tests PASS in a separate disposable PostgreSQL test database with
  per-test synthetic registry copies. The first repeated-migration test reused a
  stale MigrationExecutor cache; the test was corrected and rerun successfully.
  No live schema was affected by that test failure.
- Migration drift check PASS; Django system check PASS. These are console checks,
  not a CP2 package/source gate, full repository suite or Android live acceptance.
- No running-console upgrade, production registry lookup/write, device interaction,
  CP2 restart, CRL publication or gateway change. Android106 was not rebuilt or changed.
  Installed APK/state and actual live session behavior were not reverified here.

Migration0006 is source-ready and tested, **not installed into the running console**.
No real payment/customer enrollment or owner-canary activation was performed.
Do not roll a nonempty paid cohort back to a pre-paid backend or delete paid/audit
rows. Neither test migrations nor SQLite fixtures constitute live recovery evidence.

## Live completion gates still open

| Gate | Result |
|---|---|
| Exact authorized-device lookup/HMAC binding and Android106 observation | NOT_RUN |
| Internal owner enrollment and production activation | NOT_RUN |
| Readiness/certificate paid boundary and successful MESH Connect | NOT_RUN |
| Natural expiry; new challenge/fetch/reconnect denied | NOT_RUN |
| Already-active session behavior after expiry | NOT_RUN |
| Paid-aware CRL generation and gateway propagation | NOT_RUN |
| Recovery/reconciliation and repeat activation on the same identity/invite | NOT_RUN |
| Android identity/activation/settings/history preservation | NOT_RUN |

The submitted procedure ends at the `purpose` choices. A live expiry period,
observation/CRL propagation/session stop bounds and safe recovery sequence were
not supplied. They must be agreed before mutating the owner's production access;
this checkpoint does not invent a period, assume a CRL deployment path or substitute
synthetic results for the authorized physical-device canary.

## Source closeout

The staged scope contains19 source/test/documentation files only. Staged Python
syntax,455 local Markdown links/anchors, added-content secret/private-data scan,
strict JSON validation of the local sanitized validation summary, and
`git diff --check` / `git diff --cached --check` PASS. Pre-existing unrelated
working-tree changes and private/historical evidence remain untouched and unstaged.

**Historical NEXT at55c6a24 — obtain the remaining live procedure.**
Only OWNER_CANARY_1 is eligible; no customer payment/enrollment, alternate identity,
CP2 redeployment, Linux/Windows work or new top-level PLAN ID.
