# ANDROID-CONTROLLED-BETA / CONTROL-PLANE-0 — 2026-10-27

## Result and accepted input

Input main `ac90a2ac2f9e053b367bc3f7dde1711e94fd24a6`.
**Bounded implementation checkpoint DONE / LOCAL SYNTHETIC ONLY. Production
deployment, real payment and real enrollment NOT_RUN.** This is a substep of the
existing ANDROID-CONTROLLED-BETA, not a new product project, PLAN root ID or Linux task.
The accepted PAID-ENTITLEMENT-MVP source checkpoint remains authoritative:243 PASS,
10 existing skips/8 explicit deselections are historical accepted input, not rerun
or reclassified as a full-suite/production PASS here.

New subtree [control_plane](../../control_plane/README.md) implements a local
Django5.2.18/PostgreSQL17 console: customized Admin, responsive dashboard and two
accessible SVG charts, administrative device lookup, timestamped read-only backend
projections, operation preview/confirmation/reconciliation, payment records,
cohort metadata, incidents, append-only audit, analytics and release metadata.
Local UI: `http://127.0.0.1:8765/`; loopback only, authenticated staff access.

## Authority — no second subscription state machine

`control/friends/paid_beta.py`, `paid_beta_admin.py`, their SQLite tables and existing
readiness integration are **unchanged**. Friends registry + `control.friends.paid_beta`
remain the only source of subscription/effective-state truth. No subscription ORM
table is introduced in PostgreSQL. PG owns workflow/operational metadata and
explicitly marked read-only JSON projections with `observed_at` only. Charts never
recompute expiry or decide MESH ALLOW/DENY from those projections.

The synthetic adapter imports/calls the actual accepted backend. Preview applies
the real operation to an in-memory SQLite copy and reads back through the same
backend; execute applies it to the isolated synthetic registry. No duplicate
active/trial/grace/expired/revoked logic, limit10 logic, payment event deduplication,
challenge/fetch check, certificate logic, RNS transport or client protocol is built.
Trial remains modeled by the backend but is not issued automatically or via UI.

The adapter has a fixed subtree-local synthetic registry path, no configurable
production registry connection, no remote lookup or registry path form. It rejects
symlinks, wrong/missing fixture markers and unexpected device sets. Compose mounts
only dedicated local volumes, not production/state/keys/APKs from the checkout.
No production registry, gateway or field-user lookup was performed. Twelve generated
synthetic identities include11 exact106 observations and one84 negative fixture;
they are not real enrolled users. Normal synthetic activation uses existing Access
and DeviceIdentity; synthetic private identity keys are not retained or exposed.

## Safe requests, payments and audit

- Immutable operation intent with stable event ID `cp0-<UUID hex>`, action/device/
  UTC periods; a confirmed payment can back at most one intent. Django Admin cannot
  directly edit projections, requests, receipts, payment/release/audit rows.
- Payment records contain synthetic positive minor units/currency, opaque reference
  SHA256, operator/timestamps. Unique reference hashes reject duplicate records;
  confirmation is explicit/immutable. No payer, bank, crypto address, transaction
  secret, raw payment blob or provider integration. Metadata alone grants nothing.
- Preview is pure with respect to the registry and bound to intent, operator,
  backend fingerprint and5-minute TTL. Signed confirmation, CSRF, staff/RBAC and
  POST-only mutations. Execution rechecks backend state under its write lock;
  a changed/expired preview becomes STALE, not silently recalculated/applied.
- PostgreSQL row locks serialize dispatch; backend event/subscription atomicity
  and idempotency are reused. RUNNING is recorded before backend execution. A lost
  receipt/uncertain cross-store result stays RUNNING/UNKNOWN. Read-only reconciliation
  accepts only the matching event ID/payload hash; absence/conflict is not failure
  proof and never authorizes minting another event. No automatic retry of uncertainty.
- PG triggers protect immutable request inputs, retained payment rows, confirmed
  payment metadata, release metadata and append-only audit. Audit details are
  allowlisted; lookup aliases and raw errors are not stored. Metadata edits also
  append audit; Django's own Admin log covers account/group administration.
- Support IDs are private POST lookup inputs only. No real alias is included in
  source, URLs, PG projections, receipts, release metadata or this report. Canonical
  device references/actor IDs remain private administrative data, not public output.

PostgreSQL and Friends SQLite are deliberately **not claimed to be one distributed
transaction**. A missing uncertain receipt requires operator investigation; there
is no automatic reset/delete/new-event escape. This is tested, documented and not
hidden behind an APPLIED label. Existing certificate/cache/CRL/session boundaries
remain those of the MVP; the console neither publishes CRLs nor promises instant
revocation of a previously issued session.

## Verification

| Check | Result |
|---|---|
| New console tests on real PostgreSQL | **57 PASS**, no skips,5.34s |
| Focused unchanged paid backend storage/readiness tests | **76 PASS**, no skips,1.16s |
| Django system checks / migration drift / applied migrations | PASS; no issues, no model drift, no pending migrations |
| Compose boot / internal health / host loopback HTTP | Both containers healthy; host health200, synthetic scope |
| Chromium end-to-end, actual HTTP/auth/CSRF | PASS: two synthetic payment records; activate→grace→expire→revoke, then second-device activate;5 durable backend events |
| Desktop1440×1100 / mobile390×844 | Rendered and visually inspected; no horizontal overflow, no JS/console errors; both charts and responsive navigation visible |
| Existing MVP / client / APK / catalogs | Source untouched; exact APK size/SHA rechecked before commit |

Tests cover actual PostgreSQL triggers, permissions, authentication/CSRF, strict UTC,
read-only projection non-authority, preview byte-level registry immutability, state
change/TTL/token/actor rejection, real backend limit10/version/revocation rules,
duplicate payment references, concurrent execution, commit-before-lost-receipt
reconciliation, absent/conflicting readback, immutable audit and fixture guards.
The test database and per-test fixture copies are separate from the local demo.
No full repository suite, Linux L04.2, Windows, desktop messenger or Android build.

Browser QA left only synthetic demo data:2 cohort rows (one revoked, one active at
readback),5 events,2 confirmed **synthetic** payments. Activation state of actual
users and all production databases/services remain unchanged. Dashboard crash/MESH
rates are `null`/NOT OBSERVED without live denominators, not fabricated zeros.
Demo projections can age/expire normally after this observation.

Corrections retained in private evidence: the first Compose build tried to traverse
an unrelated unreadable parent-context cache; build staging now uses a strict
source-only allowlist and never includes private state. An internal-only Docker
network did not expose host HTTP; a separate loopback UI bridge fixes local
publication while PG remains unexposed. The first browser login exposed Chrome's
`Origin:null` behavior under `no-referrer`; `same-origin` fixes the root cause with
CSRF still enforced, plus a login regression test. An initial mounted-source
backend test run could not read owner-only source files as the container UID;
the same read-only tests passed under the checkout owner's UID, without chmod or
changes to accepted sources. These failed attempts are retained, not called PASS.

Private evidence: `state-client-build/control-plane-0-20261027/`, including test/
build/boot logs, browser QA JSON and screenshots. Local application/database/login
secrets are ignored and not committed. Build context contains only allowlisted
source files; local dependency lock includes hashes, image bases are digest-pinned.
No claim of production security approval or public-distribution license clearance.
Precommit verification:56 scoped files,28 Python syntax checks,10 local links,
strict JSON/TOML/Compose validation and whitespace PASS. Actual local credentials
and target private selector absent from staged content; accepted MVP sources and
APK bytes unchanged. Existing unrelated111-line local edits remain unstaged.

## Android and remaining boundary

Exact unchanged APK: `0.1.18-beta106-recovery`, versionCode106,
`com.familyconnect.app.friends`,56093664 bytes, SHA256
`242855c43e889e708234ce2f687fa02d37bccb1eee408904f09216b6abd8f020`;
signer SHA256 `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
[Prior accepted artifact/reference/field/rollback evidence](2026-10-27-android106-controlled-beta-readiness.md)
and [MVP result](2026-10-27-android106-paid-entitlement-mvp.md) remain intact.
No APK rebuild, installed-signer attestation, public updater/catalog change,
distribution, real payment or enrollment is implied by console release metadata.

Remaining launch gates: paid-aware server/empty-cohort/synthetic106 expiry/revoke/
CRL/session/recovery acceptance, approved private handoff/opt-in roster, commercial
terms, real monitoring and stop ownership. This console does not close those live
gates. Before any nonlocal console use, separately review HTTPS/secure cookies,
MFA/SSO/throttling, least-privilege DB/network access, backups, reconciliation and
operator security. Local HTTP and bootstrap PG role are intentional local limits.

**STOP. NEXT — review CONTROL-PLANE-0 and close only actual Android controlled-beta
launch blockers in a separately authorized bounded checkpoint.** No automatic
production connection/deployment/payment/enrollment. Linux L04.2 remains PAUSED /
NON-BLOCKING DESKTOP ENGINEERING; no new top-level project/PLAN ID or Linux retry.
