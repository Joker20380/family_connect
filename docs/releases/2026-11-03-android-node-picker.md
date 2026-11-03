# Android node-picker parity — 3 November 2026

## Scope and cause

Continuation of FLEET-BOOTSTRAP-2, selected by the owner's report that Android still
offers three Netherlands-related choices after the Linux correction. Telegram triage
is separately DEFERRED_BY_OWNER, not resolved. The next fleet canary task is not started.

Android beta111 retains the fixed four-entry array: Russia, assigned Netherlands,
Amsterdam1 and Amsterdam2 for every transport. Linux had already split manual nodes
from country-based automatic/MESH routing. This is UI parity, not three live Amsterdam
servers or a gateway catalog defect. No server/catalog change is needed for this fix.

`GatewayPicker` now supplies Amsterdam1/Russia/Amsterdam2 for AWG/TCP and Netherlands/
Russia for Auto/MESH. Friends retains the last manual gateway across mode changes and
activity recreation, including selecting Russia with a remembered Netherlands node.
Legacy country-only manual preferences show Amsterdam1, matching Linux's UI default;
initialization does not rewrite preferences, change backend assignments or connect.
An existing active session keeps its recorded target. Explicit node connections still
use the existing checked configuration/profile path; second-node MESH is not enabled.

Per-node load parsing is unchanged. Missing exact-node metrics still display No data,
never a country aggregate mislabelled as a physical node's measurement. This task does
not claim the separate Linux load/5000Mbps presentation has shipped on Android.

## Checks

- JVM:403 debug and398 Friends tests PASS, including three new picker model tests in
  each variant. Both exact manual choices, country modes and invalid-node defaults covered.
- Focused Python public-release/orchestrator contracts:38 PASS.
- Friends build and instrumentation build PASS; lint0 errors/56 warnings.
- API27 andAPI35: DashboardLayoutRuntimeTest and AppLanguageRuntimeTest,4 PASS each.
  Real spinner callbacks exercise TCP→Auto→MESH→AWG→TCP, remembered Amsterdam2,
  Russia across recreation/mode changes, return to the remembered node, selection of
  Amsterdam1 and recreation. VPN stays off and session ID is unchanged.
- Existing dashboard/navigation/layout and shared-language checks retained; rendered
  Amsterdam1/API27 and Amsterdam2/API35 rows visually inspected without truncation.
- Initial new API27 test failed because its setup wrote the short Activity preference
  name, not the actual Friends-variant fully qualified name. Corrected the fixture and
  assert the preferences object matches the Activity's. Focused retry and full4-test
  runs pass; no product guard or assertion was removed to hide that setup failure.

Private logs/renderings remain under ignored `state-client-build/android-node-picker-20261103/`.
Emulators use read-only disposable overlays; no physical handset action, account
activation, profile replacement, invitation or production mutation. These tests prove
UI behavior, not a new transport/native release or physical-device acceptance.

## Delivery and rollback boundary

Source/runtime checkpoint only. Local CI-signed x86_64 Friends test builds retain the
development version metadata111 and must never be distributed over the immutable public
product-signed111. No version increment, signing, publication or public catalog write.
Public Android0.1.18-beta111/catalog6, Windows0.2.16/catalog12, Linux public0.2.11 and
owner Linux0.2.12~l03.2.13 remain unchanged. Existing installed111 still has the old list.

User-visible delivery requires a new immutable version greater than111, exact platform/
native/artifact gates, existing-certificate offline signing, increasing signed Android
catalog and full public HTTPS readback. No production rollback is needed for this source
checkpoint; the current APK/catalog and existing identities remain untouched. Affected
phone installation and actual server selection remain unverified until that delivery.
