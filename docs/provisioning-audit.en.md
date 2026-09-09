# Configurationless platform: implementation audit

Baseline: `80a8f67`. Date: 2026-09-09. Source inspection, not certification of deployed services or physical Windows/Android connectivity. Proposed files below do not imply completed implementation.

## CURRENT / reusable components

| Plane | Existing code | What it actually provides |
|---|---|---|
| Product | `scripts/activate_windows.py`, `scripts/register_pilot_peer.py` | Operator-issued Windows activation and gateway peer registration; no account, subscription, family or entitlement service |
| Control | `control/app.py`, `scripts/admin.py`, `core/src/discovery.rs` | Signed global node/device catalog, multiple HTTPS bootstrap URLs, expiry, atomic cache, rollback floor; not recipient-bound device provisioning |
| Data | `clients/desktop/backend.py`, Android `ConnectionService.java`, Windows `Broker.cs`, `Native.cs`, `Core/Activation.cs` | Working platform-specific WireGuard integrations |
| Experimental data/control | `core/src/main.rs`, `tls.rs`, `packet.rs`, `data/*.sh` | mTLS QUIC overlay, relay switching and controlled exit; separate from consumer apps |
| Telemetry | `scripts/test_*.sh`, `scripts/test_*.py`, client status and process logs | Synthetic diagnostics and local status; no beta event ingestion, health engine or policy engine |

Reticulum and WebRTC are not implemented. Existing identities are P-256 certificate identities in the Rust laboratory and WireGuard public-key device codes in Windows. Neither is a Reticulum Device Identity. The lab already demonstrates IP-independent identity, but consumer clients do not share that identity architecture.

## Explicit answers

* **No physical .conf today?** Windows needs no user-facing .conf, but requires a manually delivered `.fcactivation`. Its adapter uses protected `.conf.dpapi` files. Android parses configuration from memory, but onboarding imports a profile. Linux imports a temporary .conf into NetworkManager; an existing NM connection subsequently works without the original file. A fresh, automatically entitled client is not implemented.
* **Runtime generation:** Windows `Core/Activation.cs` builds WireGuard text; `Store.cs` persists it using DPAPI. Android `ConnectionService.java` parses a string loaded from `ProfileStore.java`. Linux `backend.py` validates/imports through nmcli. Lab shell scripts use wg commands.
* **Reticulum identity storage:** nowhere. Lab private identities live in `IDENTITY_DIR/key.der`; Windows stores its independent WireGuard private key under protected ProgramData. Android stores an imported profile encrypted using Android Keystore; it does not yet generate its own transport key on the phone.
* **Authentication:** lab mTLS and signed catalog membership; Windows SID-based local broker authorization, recipient-bound signed activation, and WireGuard handshake. An FC1 public device code is not identity proof of possession. No registration challenge protocol exists.
* **Provisioning delivery:** operator activation/profile delivery for consumer apps; HTTPS signed catalog/cache for the lab. No shared ProvisioningTransport boundary.
* **Server selection:** imported profile or operator activation for apps; fixed gateway names and relay paths in the lab. No health-driven controller.
* **Health:** process/API checks and synthetic connectivity tests; no outcome-based gateway health component.
* **Telemetry:** local status, fixed diagnostics and synthetic result artifacts. No structured beta event database, dimensions, retention policy, dashboard or crash-free-session measurement.

## TARGET / gaps

Keep four separate planes: product authorizes devices; control produces immutable desired state; data adapters establish connectivity; telemetry measures technical outcomes. Health measures, policy decides, provisioning publishes. ConnectivityCore receives verified typed state and has no HTTPS/Reticulum dependencies.

Missing: independent on-device Reticulum identity, ownership challenges, accounts/families/entitlements, signed transport-key binding, immutable recipient-bound signed/encrypted provisioning, transport-neutral verification, HTTPS/RNS/cache delivery, version cursors, acknowledgements, secure known-good recovery, automatic updates, bounded candidate failover, telemetry ingestion, deterministic health, policy and observability.

The existing Windows activation signature/expiry/recipient validation and lab cache/rollback tests are reusable precedents, not substitutes for these components. Keep both old trust domains unchanged; introduce a distinct versioned API and provisioning trust domain.

## RISKS / compatibility

* Linux: preserve existing NM UUIDs, routes and DNS; use a typed NM adapter for automatic operation. File import remains a legacy path.
* Android: retain the current service and GoBackend; add local keys and typed state without breaking existing encrypted profiles. Account for process death, foreground service and OS key-storage limitations.
* Windows: preserve broker SID/ACL/owner protections, bundled drivers and activation fallback. Keep upstream-required runtime files inside the adapter; remove file-path dependencies from application business logic gradually.
* Reticulum integration on all three platforms requires an interoperability and packaging spike against the actual reference implementation. An interface named Reticulum is not a functioning RNS transport. Do not implement custom cryptography or derive identity keys from WG keys.
* Lab catalog expiry currently closes active sessions. The short offline test does not prove indefinite outage survival. Specify bounded authorization leases, explicit revocation and offline recovery before changing this behavior.
* Relay switching is not gateway migration. Changing public exit/NAT state can reset TCP connections; do not promise seamless gateway survival without additional infrastructure.
* Windows activation signing currently runs on the operator machine. Production provisioning signing must move to controlled server key custody with rotation and recovery procedures.
* Only one intended Russian exit currently exists. Multi-provider metadata does not create redundancy. The retired second website server must remain free of VPN deployment; historical multi-site documentation is not current topology.
* Existing CI is useful regression coverage, not proof of fresh-user onboarding or real platform networking after these changes. Unsigned Windows publisher status remains separate from protocol security.

## MIGRATIONS

There is no existing Family Connect relational database to alter. Introduce a dedicated database; do not reuse an unrelated application's database.

1. Product migration: accounts, families/memberships, subscriptions, entitlements, devices/public identity, independent public transport keys, expiring single-use ownership challenges and invitation token hashes. Unique device identity and key binding; revoke one device independently.
2. Control migration: providers, gateways/ASN/region/capabilities/capacity, address allocations, immutable per-device provisioning revisions and digests, entitlement revision, signing-key references, acknowledgements and transactional gateway reconciliation outbox. Publish usable provisioning only after required peers are installed. Serialize revision allocation.
3. Telemetry migration: bounded allowlisted events, deduplication IDs, rotating pseudonymous references, retention and dimensional aggregate snapshots. Avoid device IDs and raw IPs as Prometheus labels.

Do not silently convert old WG public keys into Reticulum identities. Enroll an independent local identity and cryptographically bind an existing or rotated local WG key. Keep legacy activation/profile data until automatic migration is validated. Private keys never enter database migration inputs.

## Exact planned files

Existing files to modify, in stages:

* `control/app.py`, `control/requirements.txt`, `control/requirements.lock`: mount separate v2 APIs and dependencies; preserve v1 catalog.
* `clients/desktop/app.py`, `clients/desktop/backend.py`: onboarding/provider orchestration and typed NM adapter.
* `clients/android/app/src/main/java/com/familyconnect/app/MainActivity.java`, `ConnectionService.java`, `ProfileStore.java`: automatic onboarding, verified state consumption, secure local persistence.
* `clients/windows/MainForm.cs`, `Broker.cs`, `Store.cs`, `Core/Activation.cs`: automatic path beside legacy activation; isolate runtime-file handling.
* `.github/workflows/test.yml`, `.github/workflows/clients.yml`: protocol/security/platform checks.
* `compose.yaml`, `README.ru.md`, `README.en.md`: isolated services and deployment documentation only when implementation is ready.

Planned new modules (names are implementation plan, not present features):

* `provisioning/models.py`, `envelope.py`, `verifier.py`, `provider.py`, `transports/base.py`, `transports/https.py`, `transports/cache.py`, `transports/reticulum.py`.
* `control/product/models.py`, `control/product/api.py`, `control/provisioning/service.py`, `control/provisioning/api.py`, `control/gateways/reconciler.py`.
* `control/migrations/001_product.sql`, `002_provisioning.sql`, `003_telemetry.sql`.
* `telemetry/events.py`, `control/telemetry/api.py`, `control/health/engine.py`, `control/policy/engine.py`.
* `clients/desktop/device_core.py`, `clients/desktop/provisioning_provider.py`.
* Android package above: `DeviceIdentityStore.java`, `ProvisioningProvider.java`, `ConnectivityCore.java`.
* Windows: `Core/DeviceIdentity.cs`, `Core/ProvisioningProvider.cs`, `Core/ConnectivityCore.cs`.
* `tests/test_provisioning_security.py`, `test_provisioning_transports.py`, `test_provisioning_recovery.py`, `test_telemetry_privacy.py`, `test_health_policy.py`; platform-specific fixtures/tests alongside existing suites.

Python models are not automatically shared native client code: publish protocol fixtures/schema and implement equivalent native validation. Final envelope format and RNS packaging must be settled by ADR and interoperability tests before security implementation.

## STAGED COMMIT PLAN / TEST PLAN

1. This bilingual source audit; no runtime changes.
2. Add stable failure taxonomy and privacy-bounded event contract with rejection tests; not ingestion or instrumentation yet.
3. ADR plus real RNS identity/packaging and standard envelope interoperability spike. Specify public bootstrap anchors, signed destination/key rotation, unavailable bootstrap behavior, offline leases and rollback authorization.
4. Product DB/API and challenge/invitation/key-binding tests: replay, wrong device, races, expiry, independent revocation.
5. Provisioning contracts/verifier/HTTPS/cache: signature, decrypt, recipient, schema, entitlement, monotonic revision, atomic crash-safe persistence. Untrusted latest-version hints cannot poison verified rollback floors.
6. Linux automatic path first, preserving existing engine and manual flow; then Android and Windows. Fresh-install tests without config import and assertions that private keys remain local. Native build/unit checks plus physical network smoke tests.
7. Real RNS delivery of identical envelopes; shared validation and transport-independent connectivity tests. Control outage must not stop a valid tunnel; valid cache reconnect must work.
8. Revision updates and bounded failover: v20 to v21, durable ACK, failed apply, known-good recovery, primary failure/fallback success, retry exhaustion and backoff. Gateway peer reconciliation before publication.
9. Ingestion/export and deterministic health: known fixtures for success rate, median/p95, disconnect/session denominator, reconnect success and insufficient-data health. Separate client observations, probes and gateway metrics; no duplicate counting. Privacy/size/rate/retention tests and segmented metrics.
10. Conservative policy integration: exclude explicitly unhealthy gateways, honor region, stable scoring, retain alternatives; no aggressive rerouting on sparse data. Controlled beta before manual-flow deprecation.

Run existing pytest, locked Rust tests, lab auth/offline/failover/revocation checks and Android/Windows/Linux build regressions at relevant stages. Telemetry must reject unknown fields, URLs, domains, payloads and keys, including covert data placed in nominally allowed free-text dimensions. Latency/disconnect denominators and crash-free-session lifecycle need explicit definitions.

## Acceptance status at audit baseline

A: partial Windows UX only. B: partial lab identity only. C/D/E: missing in target clients. F: Windows local key generation exists; Android currently imports an operator-generated profile. G: signatures/recipient binding partly exist in Windows, but immutable provisioning/encryption absent. H/J: missing for production clients. I: consumer WG operates independently, lab bounded by catalog expiry. K/L/M: missing beta plane. N: schema/design work needed. O: preserve baseline; verify on each platform before rollout.

## First implementation increment

Added `telemetry/events.py`: a bounded failure report contract with the specified stable failure codes, platform and numeric application version. It rejects unknown fields, free-text error strings and wrong value types without echoing rejected values in exceptions. `tests/test_telemetry_privacy.py` checks these boundaries. No ingestion, network delivery, client instrumentation or provisioning behavior is enabled. Targeted telemetry, Windows activation and desktop regression tests: 31 passed. Full native/network acceptance remains outstanding.
