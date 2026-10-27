# ANDROID-CONTROLLED-BETA / BETA-0-CANARY-1

## Continuation from55c6a24 — local upgrade and bounded operator

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

**STOP. NEXT — obtain the remainder of the live procedure and coordinate the owner
phone; then execute only the agreed OWNER_CANARY_1 stages.** The final30-day active
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
