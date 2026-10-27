# ANDROID-CONTROLLED-BETA / BETA-0-CANARY-1

## Result and scope

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

**STOP. NEXT — continue BETA-0-CANARY-1 after receiving the remaining live procedure.**
Only OWNER_CANARY_1 is eligible; no customer payment/enrollment, alternate identity,
CP2 redeployment, Linux/Windows work or new top-level PLAN ID.
