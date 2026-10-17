# FIELD-1-VOLGOGRAD — grant authorized, operator compatibility blocked

**RESULT=OPERATOR_COMPATIBILITY_BLOCKED; GRANT_NOT_APPLIED; FIELD_NOT_STARTED.**
The owner explicitly authorized restricted access for the already selected T1.
Do not request that same entitlement approval again. This supersedes the approval
gate in the [preparation report](2026-10-17-field-1-volgograd-batch1-preparation.md),
not the missing server grant or device compatibility evidence. Input review:
`12d178dc165863d7ecdf7e9818392d709ec55247`. Date:17 October2026 UTC.

## Fresh read-only preflight

Two bounded SSH readbacks on RU,10:14:11–10:15:24, inspect the installed admission
operator and relevant current4h code/state. Existing `--mode evaluate` completes
with exit0/NOOP, files_changed0, remote_writes0, restarts0, due[] and alerts[]. This
is a readiness decision, **not renewal performed** and not a new phone/TLS test.

- Current policy has two explicit admitted devices, no wildcard; the historical
  cap of three is not the blocker. No existing recipient is removed or modified.
- Renewal service inactive; timer active/waiting. No owner/request markers found;
  transaction COMMITTED, first_cause null. No scheduling change or parallel writer.
- Current CRL27112: issued17Oct08:58:21UTC, expires17Oct12:58:21UTC, duration14,400s.
  Material is not expired at this check. Gateway process/readiness is not newly polled.

## Exact incompatibility, before a modifying command

The previously accepted installed FIELD operator remains SHA256
`b6fe9220590524905cd98580c083bfd985d80cd5d01391ae7c2b5c4152c995b7`.
Its bundled `RestrictedReadiness._trust` requires CRL lifetime **at most3,600s**.
The existing14,400s CRL necessarily fails that predicate. In `support_admin.change`,
this validation precedes the PENDING audit/grant mutation. No enable-field command
was executed merely to reproduce the predictable failure.

The same installed operator's `publish_crl` also hardcodes `now +900s` as its upper
expiry bound; it has no lifetime argument. Bypassing validation would therefore
introduce another unsafe mismatch with current4h. Do not shrink shared CRL validity,
replace current materials or monkey-patch the old operator to make admission pass.

Configured HTTP archive SHA256
`12ca0c72a89ff20c1b3c70a1182a2d5d98d4d78d25e7a079bb4d75bdf34060ed`
has the modern four-hour validation path; that does not update the separately bundled
FIELD CLI. The installed maintenance controller exposes renewal/recovery operations,
not a new-recipient admission operation. Existing grant cutover preserves identity
sets; renewal/recovery must not be misused to invent the new entitlement.

Local source inspection checks the exact installed predicate, call order and
hardcoded CRL duration. An initial inspection assertion expected a configurable
lifetime; it failed locally, and examination confirmed the older hardcoded900s
implementation. This was not a production command failure, local transport test or
failed issuance. No validation rule, module or accepted test result was rewritten.

## Remaining boundary

Owner permission is retained, but **server entitlement remains unissued by this
task**. A narrowly scoped, locally checked current4h-compatible admission workflow
is required before attempting issuance. That would be a management-code change;
do not perform it under the prior no-product/no-new-management-change field scope.
No raw SQL/profile edit, new identity, old credential restore or trust-anchor change.

The existing batch1 private kit remains unchanged and untransferred. “Modern phone”
is the owner's only new device description; Android12+/ARM64/package/signer are not
confirmed. No repeated APK build/signing/installation is needed merely to resume
this preparation. One bounded field episode remains pending all gates; no automatic
CONNECT, capture, gateway restart or security maintenance.

Actions this continuation: read-only SSH2, existing read-only evaluate1, local source
compatibility inspection. Grant commands0/writes0, CRL/policy writes0, admission changes0,
service transitions0, APK/device actions0, CONNECT/export0. Existing user data, keys,
revocations and exact product artifacts are untouched by this task. Historical field,
causality, handoff, supervisor and release conclusions remain unchanged.
