# Implementation log

This log records completed changes and verification, not a claim that every target platform feature is deployed.

## 2026-09-09 — audit and identity/provisioning foundation

* `fc847c9`: bilingual source audit and bounded technical failure contract.
* `a77475b`: real reference RNS identity, separate local WireGuard key, signed ownership/key binding, strict desired state and encrypted/signed envelope verification. 75 Python tests passed.
* Native apps, public enrollment and real RNS network delivery remained unchanged. See [ADR 001](adr/001-identity-provisioning.en.md).

## 2026-09-09 — transactional product registration

* Added explicit SQLite migration v1 for families, entitlement, invitation hashes, single-use challenge hashes, devices, independent public transport keys, membership and fixed audit events.
* Added private-database permission checks and startup schema validation. Chose local SQLite for a single host; PostgreSQL is still required before distributed control replicas. No unrelated database is touched.
* Added invitation-based challenge/complete HTTP routes in a separate app factory. Registration verifies identity proof and key binding, checks current grants and limits, and atomically consumes challenge/invitation usage with device insertion.
* Added operator-only CLI for migration, pilot grants/invitations, independent device/grant/invitation revocation and challenge pruning. Invitation secrets go to new 0600 files, not stdout. Public API cannot create grants.
* Added race, replay, expiry, revocation, capacity, privacy, malformed-request, migration, restart and CLI-output tests. Full Python 3.14 suite: **102 passed**, including desktop tests. Two upstream TestClient deprecation warnings remain; no dependency churn in this stage.
* Local sandbox prevents the TestClient thread event loop from progressing; the same suite passes outside sandbox. This is recorded as an execution-environment limitation, not a skipped API test.
* Corrected legacy control Docker test-stage dependency/copy omissions introduced by new tests. Kept old runtime, v1 API and operator scripts. The Docker stage excludes desktop files, so its count differs from the full repository suite.
* Added [registration API and operator runbook](registration.en.md), with backup/restore, rollback, privacy and current limitations. Ignored `state-product/` in Git and Docker contexts.

Not deployed. No VPN was connected, no gateway peers were changed, no mobile/Windows client builds were altered, and the retired website server was not contacted. Database revocation currently affects future product authorization only; active WireGuard revocation awaits reconciliation.

## Next stages

1. Authenticated recovery/fetch challenges and durable immutable provisioning persistence: signed state, atomic version allocation and ACKs, protected client cache/version floors.
2. Gateway peer reconciliation/outbox before publishing usable provisioning; device revocation propagation.
3. HTTPS provider and configurationless Linux onboarding/connection beside the existing flow; then native secure-storage integration for Android and Windows.
4. Actual Reticulum delivery of identical envelopes, bounded recovery/failover, beta telemetry ingestion, health and conservative policy.

Account authentication, paid-subscription integration, family-owner UI, distributed PostgreSQL deployment and production public exposure are not completed by the pilot operator grant mechanism.

Final validation for the registration stage: Docker build passed with **90 Python 3.13 tests** in its test stage. A network-disabled runtime smoke test passed for legacy `control.app.health()` and `scripts/admin.py --help`. These checks do not activate a VPN or replace physical platform regression tests.
