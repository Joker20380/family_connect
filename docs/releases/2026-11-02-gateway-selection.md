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
- Native Windows control/DPAPI CI41431840282, ordinary user access41431840217,
  AWG41431840299 and TCP41431840245 PASS on source22069b2. Desktop visual CI41431840205
  PASS. These do not assert acceptance of a new distributed installer.
- Synthetic vectors use an explicitly public deterministic test signing seed and
  documentation-network endpoints. No production key/profile is in the fixtures.

## Package-gate repair

The first source CI was not green: Android's accepted-source guard did not yet
record the reviewed selection handlers/resources; the desktop three-gateway
negative test wrapped the former three-argument validator and failed before
inspecting its catalog. Exact reviewed hashes are now explicit, and the wrapper
passes/asserts legacy schema2. Neither production validation nor a test is skipped.
Focused release contracts53 PASS/40 native-environment skips/1 unrelated Windows
deselection; full desktop1229 PASS/185 environment-gated skips. With the rebuilt
native worker, configuration/Auto compatibility71 PASS, zero skips.

The full-runtime builder also found four stale shared-reference hashes. Their
bytes are already accepted commits a11eb8f (recovery lock), c309bff (canonical
profile DAC), and4a7bf20 (beta109 stream retirement), not changes introduced here.
Bounded desktop adaptations and companion source/test hashes advance explicitly;
the historical Android106 inventory is retained unchanged. Go1.26.1 native race
tests/build PASS, source inventory f0e48d7cd3bd68a02759a5ff29967492ab170e171942d502864f0e03a07c23fe.
The system reference advances only that inventory and two reviewed provisioning
files; other111 pinned system sources and RNS digest remain unchanged.
Local preparation failures (missing builder git/gcc, old Python tar API and host
umask002) are isolated packaging-environment failures, not accepted artifacts.
No failed output is reused or published. Full package/service smoke is still pending.

## Rollout boundary

Source versions reserved for this change: Android0.1.18-beta110/code110 and
Windows0.2.16. They are not yet signed/published/installed. Linux complete internal
Ubuntu26.04/Python3.14 candidate0.2.12~l03.2.12 is built from efc13f1 (not installed),
with DEB/AppImage byte/member audit PASS and system-component isolated systemd259
install/rollback/identity-preservation smoke PASS. DEB/AppImage smoke is pending.
System build d5fc9df50a66292b7cd1b10c81a2521352d7648c0bd2b5037af2c457b1617eb7;
DEB cde8416c07ef87ec2ef5441e17a33b93f72be8aad2e1675c7203d542ea975972;
AppImage1fb37e03b01e8aaf7d598f9907e27e6bee8500fa37d272018abcc49287fb2d2c.
The bundled legacy six-file tar is NOT a supported update for internal candidates.

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
