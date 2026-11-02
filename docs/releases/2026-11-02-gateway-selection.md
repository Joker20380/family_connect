# Explicit Amsterdam selection — 2 November 2026

Continuation of **FLEET-BOOTSTRAP-2**, explicitly requested by the owner. This is
source integration, not an installed or publicly distributed client release.
The existing ordinary admission remains the deployed baseline until separately
verified package/backend rollout receipts are recorded here.

## Contract

- Android, Linux GTK and Windows selectors include **Amsterdam 1** and **Amsterdam 2**.
  The previous Netherlands choice remains **Netherlands · assigned**; existing
  preferences and sticky assignments are not silently migrated.
- Explicit choices use stable signed `gateway_id` values `nl-amsterdam-1` and
  `nl-amsterdam-2`, distinct from country `nl`. A schema3 catalog contains exactly
  those two ordinary AWG/TCP templates. It does not advertise a second MESH service.
- Existing schema2 endpoints, global legacy floor and country semantics are unchanged.
  Explicit selection has a separate durable catalog/floor namespace, shared between
  both explicit choices. Alternating nodes therefore requires neither a downgrade nor
  rewriting a previously signed catalog. Same-sequence substitution is rejected.
- Fresh one-use proof purposes bind the exact target. Only the two fixed
  `/friends/gateway-configuration/nl-amsterdam-{1,2}` endpoints are accepted.
  A failed request never falls back to the assigned node or an old explicit profile.
  Registration uses the existing pinned SSH/forced-command boundary; credentials
  remain in stdin/private stores, not argv or UI results.
- Offline operator import binds each signed template to its already-admitted
  native-node policy template. The root-only `install-selection` operation uses
  expected predecessor, increasing sequence, idempotent operation ID and append-only
  database triggers. HTTP cannot import catalogs. Policy replacement fences selection
  until a newly bound selection catalog is installed.
- Explicit selection does not mutate `gateway_assignments`, transfer an existing
  session, create invitations or change paid state. Revocation is checked before
  registration. Existing schema2 clients continue to reject schema3.
- Explicit choices are available for AWG/TCP. Android/Linux refuse Auto/MESH with
  an explicit node and explain the limitation instead of silently using another
  MESH gateway. No node-specific load is invented from the country-level monitor.

## Local qualification

- Python protocol/backend/identity/store/application contour:190 PASS.
- Additional HTTP/package/floor/ordinary/restricted contour:171 PASS,25 existing
  environment-gated skips; no suppressed failures.
- GTK display-backed selection and disconnect tests:52 PASS. RU/EN selected-node
  renders captured with isolated HOME/network disabled; no workstation install.
- Android JVM control suite PASS, including shared schema3 positive/negative vectors.
- C# protocol/conformance PASS on Linux; native Windows DPAPI and Windows GUI
  acceptance still require Windows CI. Linux compilation is not Windows acceptance.
- Synthetic vectors use an explicitly public deterministic test signing seed and
  documentation-network endpoints. No production key/profile is in the fixtures.

## Rollout boundary

Not yet delivered: new signed live selection catalog, matching backend archive,
Android APK, Windows installer/update catalog, or reviewed full Linux DEB/AppImage.
Public Android109/Linux0.2.11/Windows0.2.15 and installed owner Linux
0.2.12~l03.2.9 remain unchanged. L08 migration is not bypassed; the existing internal
Linux updater cannot install a legacy six-file archive as a full runtime update.

Before claiming the new choices appear for users: qualify exact client artifacts,
publish only immutable increasing versions/catalog sequences, verify delivered
bytes and install the reviewed Linux package without losing identity/state. Import
the signed selection catalog and matching HTTP runtime with protected-state
readback and a scoped rollback. Keep existing sticky routing intact. Until then,
the current clients continue to show the old country selector.

References: [current state](../STATUS.md), [existing task](../PLAN.md),
[ordinary live baseline](2026-11-02-second-nl-ordinary-live.md),
[desktop identity boundary](../desktop-architecture.md#desktop-fleet-boundary),
[Linux full-package boundary](../linux-appimage-deb.ru.md).
