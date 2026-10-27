# Android controlled beta — manual paid entitlement (Beta-0)

Subscope of **ANDROID-CONTROLLED-BETA / PAID-ENTITLEMENT-MVP**, not a new PLAN ID.
[Checkpoint and evidence](releases/2026-10-27-android106-paid-entitlement-mvp.md).
Original source checkpoint was **NOT_DEPLOYED**; CP2 now serves the exact paid-aware
backend with **empty cohort/events**, not paid launch approval. Commands below
describe a future authorized operator action,
not permission to deploy, collect payment or enroll the existing field user.

## Owner canary operator — source-ready, live not run

The BETA-0-CANARY-1 exception authorizes only OWNER_CANARY_1, not customer enrollment.
Use `control.friends.paid_beta_canary`, not the generic selector-in-argv CLI below.
No owner token is embedded in source. Read-only lookup accepts an exact JSON object
with `support_id` and a64-hex `hmac_key` through private stdin only, never argv,
shell history, session, URL or logs. No selector is echoed. Operators must provide
it via a non-recording input channel; do not paste private values into command
examples, here-documents, recorded tool calls or receipts.

Lookup returns a safe binding: schema1, alias OWNER_CANARY_1, full HMAC device_token,
`safe_ref=dev_<first12 token hex>`, permit null. The HMAC domain matches inventory.
Review this binding against the authorized owner before building a bound archive;
a label alone is not proof that a device belongs to the owner. Subsequent status/
apply stdin contains only hmac_key. The wrapper resolves the bound device server-side,
keeps canonical identifiers in memory and returns only allowlisted safe receipt fields.
It neither changes Django's synthetic adapter nor enables a production web action.

Build with `python -m scripts.package_paid_canary_operator --ref <reviewed-commit>
--output <new-private.pyz> --envelope <reviewed-safe-envelope.json>` using the accepted
control/identity runtime. Omit envelope for a lookup-only archive. Explicit committed
source inventory, fixed ZIP metadata and exclusive output creation preserve artifact
identity. Verify exact archive SHA/source inventory before use; the envelope is an
operator-reviewed operational guard, not a signature or sandbox against a host admin.
No private key/selector/DB enters the archive. Packaging does not upload or execute it.

A bound envelope has exactly schema, alias, device_token, safe_ref, permit. A non-null
permit has exactly action, event_id (`canary_` +32 random hex), expected_version,
period_start, paid_until, not_before, not_after. All timestamps are integer UTC.
No arbitrary external reference: backend reference is derived from the fixed event ID.
The normal four-stage workflow permits activate at versions0,1,3 and expire at version2;
event count/version must agree. Version1 requires expired effective state; version2
requires active entitlement and an unexpired target certificate; version3 requires
expired effective state and no unexpired retained target certificate. No revoke,
grace, unenrollment or fifth new event is exposed. This is workflow sequencing, not
an alternative subscription state machine.

Normal-path execution windows are explicit and at most900 seconds; paid periods have no default
and a31-day ceiling. The short natural-expiry/CRL stages must be coordinated with
phone observations, clock health and reviewed CRL delivery before issuing permits.
Final recovery is intended for approximately server_now+30 days after revoked
certificates have expired, without a new identity/invite. The wrapper does not
publish CRLs, prove gateway delivery, kill a session or verify APK signer remotely.

Emergency permit action `recover` is separate and allowed only at versions1/2,
with matching current version/event count and only prior payment events. The stored
subscription must still be active but its effective state expired/paid_allow false:
natural expiry only, not explicit expire or terminal revoke. Existing Android106,
device/invite and one-cohort guards remain in force. A known certificate inventory
must contain no bound-device row with expires>server_now; no row/expiry/revision is
deleted or modified. Future live procedure must wait NotAfter+30s if any certificate
was issued; this source wrapper neither sleeps nor performs a live CRL operation.

Recovery period_start must equal server_now on first apply and paid_until must equal
server_now+2592000 (exact30 days); the permit is never silently rebased. Its period
start must be within the explicit execution bounds and window length is1..300 seconds.
Other periods fail INVALID_RECOVERY_PERIOD. A delayed execution that misses its exact
start also rejects; a fresh event is not a way to reconcile an uncertain prior commit.

Recovery delegates to unchanged paid_beta.apply_event as payment, with transient
reference `internal-canary-recovery:<event_id>`; only its SHA256 is stored. The wrapper
first finds the incoming event and then scans existing reference_hash values for
that marker. Once present, every different event ID fails RECOVERY_TERMINAL, including
old normal-event replays, normal expire/final activation and another recovery. Same
recovery ID and canonical backend payload is an idempotent readback, even after the
window/entitlement expires; changed payload fails EVENT_ID_CONFLICT. Duplicate
readback never restores expired/revoked access or extends its original paid period.
No extra field/table/authority is introduced. Safe output adds emergency_recovery
branch and NATURAL_PHASE_ABORTED_OWNER_RECOVERED or CRL_PHASE_ABORTED_OWNER_RECOVERED;
purpose remains internal_canary, amount0, never revenue. Backend receipt is unchanged.

After emergency recovery the normal path for this checkpoint is permanently closed.
No CRL generation/publication/number update/entry removal/rollback occurs. Old expired
serials may remain in the CRL; observing a new unlisted serial after future live
recovery is a separate live acceptance gate. This source checkpoint produces only
lookup-only packages: no production lookup, bound archive or live operation.

Each apply holds the existing BEGIN IMMEDIATE transaction, delegates to paid_beta,
rejects other cohort members and checks non-paid tables remain unchanged. The raw
backend event retains event_type payment; safe receipt purpose internal_canary and
amount_minor0 are operational metadata, not revenue. Duplicate execution uses the
same immutable event and exact payload, with a fresh effective-state observation;
conflicts reject. On lost output preserve the exact archive/permit: status is read-only,
replaying the same permit is idempotent, and a new event ID is not reconciliation.
No production receipt has been imported into PostgreSQL in this checkpoint.
[Local upgrade, tests and remaining live gate](releases/2026-10-27-android106-beta-0-canary-1.md).

## Scope and prerequisites

- At most10 distinct, already activated Friends devices; retained expired/revoked
  rows still occupy slots. No automatic enrollment, trial, grace or new identity.
- Only exact signed `0.1.18-beta106-recovery`, versionCode106,
  `com.familyconnect.app.friends`, APK SHA256
  `242855c43e889e708234ce2f687fa02d37bccb1eee408904f09216b6abd8f020`,
  56093664 bytes; signing certificate SHA256
  `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
  [Exact retained APK, reference and saved105](releases/2026-10-27-android106-controlled-beta-readiness.md).
- New106 installations must already have their existing Friends identity activated
  through the normal flow before paid enrollment; this CLI never installs,
  activates a device, issues an invite or changes keys. Devices on older versions
  are excluded, not remotely upgraded. Public updater/catalog remains unchanged.
- Operator checks private handoff bytes/signature and device version, opt-in,
  approved terms and a confirmed manual payment. No acquiring/provider API.
  `--apk-sha256` is an explicit operator attestation, NOT remote signer attestation.
  Latest authenticated support/readiness version observation must also say exact106;
  a newer106 ACK can supersede stale84 support data. Missing/ambiguous/non106 evidence
  denies enrollment. Same-timestamp conflicting observations deny enrollment.
- Use the existing canonical Friends registry, not a copied or new identity DB.
  Keep registry/backup/audit receipts private; restrict filesystem/operator access.
  Do not put raw payer/bank/address/transaction secrets into any CLI argument,
  reference, event ID, ticket or Git. Use opaque reconciliation IDs only.

## Storage and effective state

`paid_beta_subscriptions` is separate from devices/invites/grants: device FK/PK,
state, period_start, paid_until, nullable grace_until, created_at, updated_at,
monotonic version, last_event_id, nullable revoked_at. `paid_beta_events` is
append-only: global opaque event_id, device FK, event_type, occurred_at,
previous_state, new_state, period_start, paid_until, grace_until, reference_hash,
payload_hash, applied_at, result. No raw payment details or Support ID columns.
Dates in storage/JSON are integer Unix UTC seconds from server/operator host time;
occurred_at/applied_at mean server application time, not unverified payer time.

One effective-state function: revoked (including revoked_at) always DENY;
active/trial with `now < paid_until` ALLOW; grace with `now < grace_until` ALLOW;
otherwise effective expired/DENY. Equality at the boundary denies. No client clock.
Time expiry requires no cron or write; a stored active row may be effectively
expired. Status reports both stored and effective state. No automatic trial/grace.

No subscription row means the previous admission/all_activated decision is
preserved. A paid row is an additional restriction, never an activation/admission
bypass. `paid_allow` in operator status is not a full MESH health/admission claim.
Payment enrollment and audit insertion commit atomically under SQLite
`BEGIN IMMEDIATE`, with foreign keys and the10-row cap. Missing migration rejects
operator writes; read-only status and runtime with no paid tables retain legacy
semantics. Partial paid schema fails closed rather than bypassing enforcement.

## Operator commands

Use the locked control/identity Python environment. Source invocation is
`python -m control.friends.paid_beta_admin`; the program name in help is `paid-beta`.
An isolated source-only archive can be built with
`python scripts/package_support_operator.py --operator paid-beta --output /private/new-paid-beta.pyz`;
the existing default support operator is unchanged. Never publish the archive with
registry, keys, profiles or private receipts. Use `python -I /private/new-paid-beta.pyz`
in place of the module invocation below. Output path must be new.

Obtain DB path and Support ID through the existing private administrative process;
do not write a real alias in this runbook, command transcripts or public receipts.
Support ID is resolved to exactly one existing canonical device. Disable shell
tracing/session capture; protect shell history and process visibility. Variables
below are operator inputs, not client/protocol settings. UTC arguments require
exact `YYYY-MM-DDTHH:MM:SSZ` (no offsets, local time or fractional seconds).

```sh
python -m control.friends.paid_beta_admin --db "$REGISTRY_DB" migrate
python -m control.friends.paid_beta_admin --db "$REGISTRY_DB" status --support-id "$SUPPORT_ID"
python -m control.friends.paid_beta_admin --db "$REGISTRY_DB" activate \
  --support-id "$SUPPORT_ID" --event-id "$PAYMENT_EVENT_ID" \
  --period-start "$PERIOD_START_UTC" --paid-until "$PAID_UNTIL_UTC" \
  --reference "$OPAQUE_REFERENCE" \
  --apk-sha256 242855c43e889e708234ce2f687fa02d37bccb1eee408904f09216b6abd8f020
python -m control.friends.paid_beta_admin --db "$REGISTRY_DB" grace \
  --support-id "$SUPPORT_ID" --event-id "$GRACE_EVENT_ID" \
  --grace-until "$GRACE_UNTIL_UTC" --reference "$OPAQUE_REFERENCE"
python -m control.friends.paid_beta_admin --db "$REGISTRY_DB" expire \
  --support-id "$SUPPORT_ID" --event-id "$EXPIRY_EVENT_ID" --reference "$OPAQUE_REFERENCE"
python -m control.friends.paid_beta_admin --db "$REGISTRY_DB" revoke \
  --support-id "$SUPPORT_ID" --event-id "$REVOCATION_EVENT_ID" --reference "$OPAQUE_REFERENCE"
```

- Migration is idempotent and does not enroll devices or change existing rows.
  Status is read-only and never migrates. The existing registry file must exist;
  symlink DB paths are rejected. Take a consistent private backup before a future
  authorized production migration; never restore an old DB over live identities.
- Activate is the only enrollment operation. It requires a confirmed payment,
  `period_start <= server_now < paid_until`, matching106 evidence, active device
  and invite, no existing MESH grant revocation, and an available cohort slot.
- A renewal/grace cannot shorten a previous paid/grace boundary. Grace is only an
  explicit operator event on an enrolled device. Expire denies new readiness now
  without altering activation; a later authorized payment may reactivate it.
  Revoke is terminal for this MVP: neither payment nor grace can undo it.
- `event_id`: 8–128 ASCII letters/digits/underscore/hyphen, globally unique across
  devices and actions; no embedded Support ID. Same ID and identical canonical
  payload returns the original receipt with `duplicate:true`, without mutation,
  even after expiry/revoke. Conflicting reuse rejects atomically. An old successful
  duplicate receipt does not mean current access is active: use status.
- Reference is stored only as SHA256; payload_hash binds device, event type/ID,
  periods, reference hash and APK attestation. Audit timestamps/states/periods and
  canonical device reference are private metadata, not public release receipts.
  Exit0 is committed/read success; exit2 is rejection with a fixed safe reason.
  If output is lost after commit, retry the same event/arguments, never mint a
  second payment ID just to recover a receipt. Rejected events do not append audit
  rows; no partial paid state is committed.

## Readiness, caches and revocation boundary

Both restricted challenge and fetch check paid state under the existing registry
transaction. Fetch checks again after challenge; stale/replayed proof, existing
activation and previous cache cannot renew expired/revoked paid entitlement.
Wire fields, transport, MESH certificate format, device/WG keys and invites remain
unchanged. New response and certificate expiry are bounded by the minimum of
existing crypto/material/CRL limits, directory expiry and paid_until/grace_until.
A retained longer certificate is not reissued as a way around the paid boundary.

Previously issued certificates/cache cannot be retroactively shortened. Revoking
or enrolling a previously non-cohort device does NOT instantly terminate an
existing session. Its old signed expiry remains the offline upper bound unless
the existing CRL publication/propagation path invalidates it sooner. The existing
CRL publisher now observes paid DENY; these CLI commands do not publish CRLs,
restart gateways, revoke identity or claim a live kill. Accept/rehearse that
propagation/session bound before billing; do not advertise instant revocation.

## Deployment, rollback and stop boundary

CONTROL-PLANE-2 operational update27.10: **DEPLOYED_EMPTY_COHORT / REVIEW_PENDING**.
Exact paid-aware HTTPdcd76998… now serving after one guarded restart; subscriptions0/
events0, critical non-cohort/admission/publisher fingerprints unchanged. Typed D-Bus
observer, fresh backup/isolated restore, complete effective argv and three post-start
plus independent listener/health/inventory readbacks PASS. No repeat migration or
live DB restore. Consumed1 rollout/0 emergency; second actual rollout restart forbidden.
Earlier pre-start stops spent no restart and their evidence is retained. No real-user operation.
[Exact outcome and next gate](releases/2026-10-27-android106-control-plane-2.md).
No real payment/enrollment is authorized; live paid CRL propagation remains unaccepted.

The original PAID-ENTITLEMENT-MVP source checkpoint had no deployment/paid activation.
CP2 now verifies exact packaged server modules, retained empty schema, backup and
empty-cohort operational invariants. Remaining acceptance requires review of that
evidence and authorized paid expiry/revocation/CRL/session/recovery evidence before
any real enrollment. A production identity is not a test fixture. Clock health and
consistent UTC are prerequisites. Owner must approve cohort/terms/monitoring and
private delivery; cap10 is not consent from any existing tester.

Do not roll back to a pre-paid backend with a nonempty cohort: it ignores paid rows
and reopens all_activated access. Never delete paid rows to regain legacy admission,
clear data, reissue identity or silently extend paid periods. Preserve audit and
working non-cohort users; stop new enrollment/payment/distribution, use an
authorized paid-aware corrective server build and rehearse rollback first. APK106
is not changed by this server checkpoint; saved105 is not permission for Android
downgrade/uninstall. Server/client recovery remains a separate launch gate.

Stop on wrong/duplicate charge application, unexpected non-cohort denial, identity
mutation, entitlement beyond the accepted crypto/CRL bound, signer/hash mismatch,
unsafe rollback, missing receipts or clock anomalies. No Linux/Windows/full-suite
task is a prerequisite. **STOP; next only actual Beta-0 launch blockers.**
