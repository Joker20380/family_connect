# ANDROID-CONTROLLED-BETA / PAID-ENTITLEMENT-MVP — 2026-10-27

## Decision and bounded result

Input main `9cb1a4c4948f7003d01f71ec5a3a3663002bc5ad`.
**Server source/model/operator checkpoint DONE; NOT_DEPLOYED. Paid launch remains
BLOCKED on the finite Beta-0 gates below.** This is a subscope of the existing
ANDROID-CONTROLLED-BETA, not a new top-level PLAN ID or release acceptance.
No real payment, paid cohort enrollment, production DB migration/mutation,
service restart, client change, APK rebuild/signing or catalog/publication occurred.
Pre-existing unrelated ops/client-guide edits remain outside this commit.

Owner Beta-0 scope: at most10 existing activated Friends identities; new106
installations or devices already on exact106 only. Older versions are excluded,
so the previous older-version in-place-upgrade gate is **out of Beta-0 scope**,
not newly PASS. Private verified APK handoff, manual confirmed payment and operator
event; external acquiring/provider integration is **not a Beta-0 blocker**.
Linux L04.2 stays PAUSED/non-blocking; Windows, desktop messenger and a completely
green repository suite are not prerequisites and were not started.

## Fixed Android artifact and field evidence

| Property | Accepted value (unchanged) |
|---|---|
| Local private APK | `state-client-build/owner-diagnostic106-20261022/delivery/FamilyConnect-0.1.18-beta106-recovery.apk` |
| Version / code | `0.1.18-beta106-recovery` /106 |
| Package | `com.familyconnect.app.friends` |
| Bytes | 56093664 |
| SHA256 | `242855c43e889e708234ce2f687fa02d37bccb1eee408904f09216b6abd8f020` |
| Signing certificate SHA256 | `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a` |

Size/hash rechecked without modifying APK. Manifest/signer/native/reference/source
provenance remains the [accepted readiness evidence](2026-10-27-android106-controlled-beta-readiness.md),
not inferred from filename or a new clean source commit. No Android source or
wire contract change. Private delivery only; public updater60/sequence1 unchanged.
Saved signed105 rollback APK remains as recorded there; no downgrade acceptance
or destructive recovery is claimed.

**ANDROID106-MESH-FIELD-1 = PASS / owner accepted**, same external user/whitelist
network/ordinary app/MESH scope. Previous private administrative lookup showed
one canonical identity/invite, activation active, revoked=false and admission
eligible; newer authenticated106 READY observation superseded stale84. No repeat
production lookup or change in this checkpoint. Real Support ID/device mapping
is not included here, in source constants, wire fields, APK or public receipts.
Field PASS does not establish paid expiry, Linux/Windows or general CI acceptance.

## Implementation and safety properties

- Separate idempotent `paid_beta_subscriptions` / append-only `paid_beta_events`,
  existing-device FK binding; server UTC periods, version/last_event, hashed
  opaque reference/payload and committed APPLIED audit. No payer/bank/transaction
  secrets, raw payment details or Support ID in these tables.
- Atomic operator payment enrollment/renewal (`BEGIN IMMEDIATE`), global event-ID
  idempotency/conflict rejection and max10 retained devices including expired/
  revoked. Concurrent duplicate applies once; concurrent tenth-slot race admits
  exactly one. No device/invite/key/activation mutation; no unenrollment escape.
- One effective-state function: revoked absolute DENY; unexpired active/trial/
  explicit grace ALLOW; all other states/time boundaries expired/DENY. No client
  clock or automatic trial/grace. Expiry is computed without a manual action.
- Non-cohort admission/all_activated path remains unchanged. Missing/empty paid
  tables do not alter access; tests compare complete challenge and serialized
  readiness bytes with no paid rows, empty cohort and an unrelated paid member.
- Paid state is rechecked at challenge and fetch, including changes between them;
  proof replay/cached readiness cannot mint a new entitlement. New certificate and
  response expiry cannot exceed paid/grace or existing crypto/material/directory
  expiry. Longer pre-cohort certificates are not reused in paid responses.
- Private CLI `migrate/status/activate/grace/expire/revoke`, safe JSON failures,
  no raw-input echo; isolated deterministic operator archive. Runtime manifests
  and historical pinned bridge overlay include the new runtime dependency.
  [Operator runbook, exact commands and recovery restrictions](../paid-beta.md).

`--apk-sha256` explicitly attests the operator's exact private handoff. Latest
authenticated version evidence must additionally match106; a stale/non106/missing
or conflicting latest observation rejects enrollment. This is **not remote
installed APK/signer attestation**, which is unavailable without changing the
client/wire. New106 users must finish ordinary existing-identity activation first.

**Cache/revocation limit:** a previously issued certificate/session cannot be
retroactively shortened by a subscription row or CLI event. New issuance stops;
old signed expiry and existing CRL propagation govern old cache/session denial.
The existing CRL publisher includes paid expired/revoked certificates when invoked;
the payment CLI never publishes a CRL or claims instant live disconnection. A
paid-aware server/CRL/session/recovery rehearsal remains mandatory before billing.
Rolling back to a pre-paid backend with a nonempty cohort would bypass enforcement
and is prohibited; no subscription-table deletion or identity reset as rollback.

## Validation and evidence boundary

Final targeted Python selection: **243 passed,10 skipped,8 deselected**, no failures,
23.50s. Paid storage/operator/readiness/HTTP plus activation and Support ID selection
contributes132 PASS without skips; the expanded existing backend/package regression
contributes111 PASS. This is not a repository-wide or platform acceptance run.

Coverage: state equality boundaries/revocation precedence; idempotent migration;
FK binding; immutable audit and retained cohort; full-cohort renewal; atomic fault
rollback; concurrent event/cap race; invalid/shortening events; existing active106
only/newer ACK ordering; unchanged no-row bytes; challenge→fetch expiry/revoke;
replay; certificate crypto/paid/material bounds; existing CRL inclusion; actual
packaged HTTP challenge/fetch denial and unaffected non-cohort route; isolated
operator/runtime closure and deterministic packaging.

10 skips are existing nginx-dependent HTTP matrix cases (`FC_TEST_NGINX` absent).
8 explicit deselections:4 external Go/native compatibility cases,1 pinned sync
artifact interoperability case,3 external nginx cases. No fresh native/real-ingress
or live Android/session acceptance is inferred. These remain explicit deployment
validation boundaries, not a reason to run Linux parity or the full historical suite.

The existing local Python image was used only as a locked, read-only generic test
environment: control+identity27 package pins match; network disabled, tmpfs synthetic
DBs/keys, no production credentials/devices. Its historical Linux-oriented image
name is not a Linux gate invocation. Initial new-fixture run64 PASS/1 FAIL used an
incorrect ACK table column; corrected the fixture to actual nonce/correlation/
challenge_at schema. Subsequent118 PASS and the final result above supersede it;
the failed log is retained, not called product/CI success.

Private ignored evidence: `state-client-build/paid-entitlement-mvp-20261027/`,
including baseline doc snapshots, `targeted-first.log`, `targeted-second.log`,
`backend-packaging.log`, `final-targeted.log` and precommit verification. No raw DB,
keys, source capsule, build output or private user mapping is staged. Strict JSON,
local links, unchanged exact APK, staged secrets/scope and whitespace are checked
before ordinary commit/push; remote SHA is reported in handoff, not invented here.

## Remaining launch gates and finite NEXT

| Beta-0 gate | Result / remaining evidence |
|---|---|
| Exact signed106 / no older-version cohort | Accepted artifact unchanged; enforce private handoff and enrollment observation |
| Older-version in-place update / external acquiring | Out of Beta-0 scope; not PASS and not a blocker for this scope |
| Subscription/payment audit/expiry source | PASS bounded synthetic tests; production deployment and acceptance NOT_RUN |
| Server/CRL/session and rollback | BLOCKED: paid-aware deployment/empty-cohort non-regression and synthetic106 expiry/revoke/recovery rehearsal; no downgrade to legacy admission |
| Private download/first group | BLOCKED: named operator, verified handoff/opt-in roster; cap10 approved, existing engineering testers not automatically paid members |
| Terms/privacy/subscription | BLOCKED: approved price/periods/manual confirmation, cancellation/refunds, revocation-bound disclosure, retention/contact |
| Monitoring/stop ownership | BLOCKED: activation/MESH failures, crash denominator, current version distribution, support counts, event reconciliation and agreed thresholds |
| Android rollback | Saved105 unchanged; safe non-destructive recovery remains required, no forced downgrade/reset |

**STOP. NEXT — close only factual ANDROID-CONTROLLED-BETA Beta-0 launch blockers:**
review this MVP, then separately authorize a bounded paid-aware server deployment/
synthetic acceptance and recovery checkpoint; approve private cohort, terms,
monitoring and stop criteria before any real payment/enrollment. No automatic
implementation/deployment of NEXT; no new PLAN ID, Linux retry or client patch.
