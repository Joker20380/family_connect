# DIAG-AUTH-REJECTION-1 — OPEN

11.10.2026; isolated diagnostic-test issue, not an access-control bypass.

The preserved `local-authenticated.log` and `baseline-authenticated.log` from
`telemost-admission-ownership-1` fail six negative subcases at
`carrier/bootstrap/auth_test.go:86`: an exchange failure callback is unexpected.
That fatal assertion precedes the mandatory `err != nil / provider calls == 0`
assertion, so those receipts alone classified the rejection boundary as **C**.

Minimal local verification on the same preserved source plus one new test:
`telemost-stability-1-continuation/source/carrier/bootstrap/negative_boundary_test.go`,
`TestNegativeAuthMandatoryRejectionBoundary`, using disposable ProductStore-issued
fixtures. All six negative cases reject, return no descriptor, emit no authenticated
admission and invoke no room provider. The positive control authenticates and creates
one descriptor/provider call. Each negative callback is `family_open / unknown`.
Classification after this verification: **A — actual security rejection succeeds;
the diagnostic callback contract differs from the test expectation**.

Exact result: `state-client-build/field65-export16/telemost-stability-1-continuation/receipts/auth-boundary.log`.
`bootstrap/protocol.go:205` checks `familysession.Open`; its error path emits
`family_open` and returns before authenticated exchange. No original assertion was
weakened, moved or skipped; no application/security code was patched.

Remaining: reconcile the expected diagnostic callback semantics and useful bounded
reason codes separately. The complete bootstrap suite remains **FAIL**, not PASS.
This issue does not block the single stability observation after the explicit
mandatory-rejection check; it is not a reason to repair the entire suite first.
