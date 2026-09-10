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


## 2026-09-10 — authenticated provisioning provider and Linux cache

* Migration v2 preserves enrollment and adds single-use fetch challenges and immutable envelope history.
* Separate domain/audience proof, transactional device/key/entitlement checks, replay prevention and no fallback to old server versions. Lost responses recover through a fresh challenge without issuing another version.
* Operator signer initialization, publication with --peers-ready, and version listing. HTTP delivery needs no signing private key. Operators prepare peers manually; automatic reconciliation remains pending.
* HTTPS reference client and atomic Linux cache with durable floors, lease verification, exact redelivery and fail-closed corruption/observed clock rollback handling. No tunnel ACK, native integration or hardware backup rollback protection.
* Full suite: **130 passed**, two existing upstream warnings. HTTP tests ran outside the sandbox because of its known TestClient event-loop restriction.
* [Protocol, commands and limitations](provisioning-provider.en.md). Next: gateway reconciliation/outbox, peer application/revocation, then client VPN lifecycle integration.

Docker: **118 Python 3.13 tests passed**; build succeeded. Legacy health and scripts/admin.py --help smoke checks passed in a container with networking disabled.


## 2026-09-10 — gateway reconciliation and desktop layout fixes

* Migration v3 adds deployments, address reservations and a durable peer outbox. Publish/fetch require confirmed deployments; manual --peers-ready is removed.
* Revoke atomically queues removal. Worker checks expiry/key/revoke, repairs drift and retries with backoff. The Docker helper rereads current persisted intent under a lock, including delayed operations after timeout.
* Pilot adapter verifies gateway key/port/mount, persists public peer records atomically and protects unmanaged/static peers. Systemd templates are prepared, not installed.
* Linux gets responsive actions/wrapping, scrolling/focus access, fixed footer, consistent dark styling, HiDPI-aware minimum width and timer cleanup. Windows gets explicit auto-size rows, constrained labels, scrolling/footer, PerMonitorV2 and a responsive code dialog.
* Linux: 18 RU/EN layout cases at three sizes and 100/150/200% scale; screenshot reviewed. Windows cross-build: zero warnings/errors. WinForms /layout-test is added to CI but was not run on this Linux host; manual Windows DPI validation remains required before release.
* Real WG in an isolated Docker namespace without networking: install/remove/restart, delayed command after removal, unmanaged peer preservation and read-only /keys passed.
* [Gateway protocol/operations/rollback](gateway-reconciliation.en.md), [UI details/screenshot](desktop-layout.en.md). Not deployed; installed applications have not been replaced.

Current next steps: client runtime application/ACK/known-good recovery, Linux flow integration, native secure storage and real Windows DPI validation, Reticulum delivery, then distributed gateway agents/topology migration. Fetch/cache and local gateway reconciliation are implemented; tunnel-application ACK remains pending.

Final validation: **155 Python tests passed**, control Docker build succeeded with **143 Python 3.13 tests**, two existing upstream warnings.


## 2026-09-10 — 0.2.1 rollout

Published immutable Linux/Windows release from 8cd0f2d; all client CI passed.
Linux replaced with backup; server gateway/API/worker deployed, 3 peers preserved.
Signed catalog sequence 1 added. Reticulum notifications and personal Windows install
remain pending. Current facts and next steps: [STATUS](STATUS.md), [PLAN](PLAN.md).


## 2026-09-10 — Desktop 0.2.2

Refreshed desktop appearance and temporary dodecahedron icon. CI passed, release
published, catalog sequence 2 signed. Linux upgraded using 0.2.1 updater with rollback
preserved. Windows update available; personal installation pending. See STATUS.


## 2026-09-10 — 0.2.3 quiet polling

Rounded buttons and rotated dodecahedron; polling separated from user-action busy state.
Unchanged polls do not repaint; stale replies discarded. Windows/Linux regression checks
passed; signed catalog sequence 3 published; Linux upgraded with rollback preserved.
See STATUS and release report for exact evidence.


## 2026-09-10 — Linux 0.2.5

User-reported clipping reproduced with actual font metrics (effective scale 2.06).
Font-aware window sizing, themed selector/dialogs, hidden unused scrollbar, cached
layout, separate polling queue and 3s polling timeout. Platform checks passed; signed
catalog sequence 4 published; Linux installed with 0.2.3 retained. Real warm runtime
probe max callback interval 17.9 ms; initial probe gap 850 ms remains documented.
See STATUS and release report for evidence and remaining confirmation.


## 2026-09-10 — 0.2.6 narrow Linux layout

At user request: narrower window, one action per row even at wide sizes, height exactly
content + footer. Real laptop 658×1078 (993 + 85), all actions visible. Platform checks
passed; signed catalog sequence 5 published; Linux upgraded with 0.2.5 rollback retained.
See STATUS, PLAN and release report for current state and evidence.


## 2026-09-10 — 0.2.7 native Linux frontend

Replaced Tk with GTK 4/libadwaita after real-display redraw stalls. Compact one-column
UI, native dialogs/dropdown, coherent state updates and content-sized window. 27 Python
tests, 24 GTK layouts, native Wayland probe and platform CI passed. Published immutable
release and signed catalog sequence 6; installed through 0.2.6 updater with rollback.
No server changes. User visual confirmation pending. See STATUS and release report.


## 2026-09-10 — Windows 0.2.8

User approved Linux 0.2.7. Windows visually aligned; platform CI passed, immutable
release published and catalog sequence 7 signed. Personal Windows update pending.
Linux 0.2.7 and server 0.2.1 retained. See STATUS and release report. Source `5f0303d`.

Android APK link supplied; existing separate Android profile checked against live and
persistent gateway records. Windows reinstall request matched its old public key;
fresh signed import grant issued for existing 10.77.0.4 (24h import validity). No private
keys printed or committed, no peer changes. User imports and phone/Windows connectivity
checks pending.
