# UI60-LAYOUT-CURRENT-STYLE-1 — implemented UI candidate

Part one of UI60-RESTORE-AND-FIELD-1. **Revision4 unsigned candidate ready for visual
review; revision3 remains the owner-approved installed version.**
This is an isolated derivative of the retained accepted diagnostic product, not a
checkout of beta60 or the dirty root main. Existing snapshots, accepted artifacts and
historical acceptance reports are retained. The field stage has **not started**.

Subsequent ordinary owner use produced a slow-loading complaint and export9.
[Separate read-only analysis](2026-10-16-ui60-owner-slowness-export9.md) records exact
server correlation and delivery-pressure evidence, without proving the primary
bottleneck or a UI regression. No code/configuration change or new acceptance follows.

Later [export10/call interruption](2026-10-16-ui60-owner-call-drop-export10.md) preserves
the same session's maintenance-driven closure and failed automatic seed admission
using the pre-cutover directory. This is a separate read-only diagnosis, not a UI fix,
new device acceptance or completed field trial. The final provided phone state is OFF.

## Revision4 — proportional map and more compact neighboring blocks

Owner explicitly requests full map width **without stretching continents**, allowing
more map height at the expense of the other two blocks, and prefers the compact
central composition of beta60. This is a UI-only continuation, not a transport fix.

- Compact map uses the same scale on both axes in the existing geographic projection.
  Its preferred height derives from actual map bounds and available content width;
  a separately undersized container fits it uniformly rather than flattening it.
  Initial location-bound changes request layout; no transport operation is added.
- At392×780/density1, RU and EN OFF fixtures: map **368×114→368×156px**;
  connection/dial panel **300→265px** high; middle network panel **204→197px**.
  Widths, block order, square corners, palette and thin strokes are preserved.
- Space comes from the dial and spare network-panel spacing, not smaller text or
  overlapping/shrunken selectors. The middle panel remains taller than beta60's
  compact reference because the modern controls retain their readable labels and
  minimum touch areas. On constrained/large-font viewports the body scrolls instead
  of hiding or distorting the map; bottom navigation stays fixed.
- [beta60 → installed revision3 → revision4 comparison](../../research/ui60-layout-20261016/comparisons/home-map-revision4.png)
  and [revision4 main image](../../research/ui60-layout-20261016/screenshots/candidate-ru-392-780-1.0-home-off.png)
  are real UI-code renders with synthetic data, not live CONNECTs.

| Revision4 identity | Value |
|---|---|
| Version | `0.1.18-research84-ui60-4`, code84, minSdk31, arm64-v8a |
| UI source inventory, not Git SHA | `e90893aee5fdc04aae1cacd296d5291ca8a743350de42334b290f08504c48fce` |
| Unsigned APK | `64b4c71f8fc91ce91a457e1c99c1b171adeaad58d226a7c05e71e32c0b655ba1` |
| Unsigned size |55,990,836bytes|
| Native, unchanged | `be70a66ccc2bcbf0478915fd414c32de3bedb2a0ae0c3222a53e65eebd0a92b2` |
| Native source inventory, unchanged | `b36c4a21ee6cf04acb192a0e6d140fa565b3e5ae75f6fc8d028d029c3152781d` |
| Product signing / install / transfer |0 /0 /0; revision4 remains private and unsigned|

Full offline Gradle assemble plus15 targeted JVM/export/presentation cases PASS.
All native payloads and restricted native manifest are byte-identical; permissions,
SDK/ABI/features unchanged; unsigned signature state/alignment verified. Six paths
change from revision3: four presentation classes, presentation test and private
versionName. No lifecycle/connection handler, native/security/transport logic change.
Accepted artifacts and revision3 source/build/render snapshots remain retained.

Four isolated Android31 configurations render54 scenes (RU/EN, normal/narrow,
fontScale1/1.5, landscape),8 navigation cycles and32 map dimension/density cases;
no service/session side effects, clipped network labels or reduced button targets
were detected by the existing checks. Actual dot-cloud bounds also check proportional
rendering in deliberately short fixture containers. Normal RU/EN measured block
heights are asserted by [map geometry checks](../../research/ui60-layout-20261016/map-revision-check.json).

**Fresh real-IME check was NOT_VERIFIED**: the disposable host had text focus but
not window focus, so IME was not visible. No production chat change is made to hide
that harness limitation; revision3's prior IME PASS is retained separately, not
relabelled as a revision4 PASS. Chat fixture/navigation renders pass; Android35 live
runtime remains NOT_RUN. No retry/restart loop was used to turn the IME check green.

One bounded KVM/host-GPU render run,50%-of-one-core quota,85°C cutoff; measured maxima
**build73°C, emulator66°C**. Emulator was explicitly stopped after the IME attempt;
the wrapper reports the requested interruption, not a successful natural exit.
[Execution receipt](../../research/ui60-layout-20261016/map-revision4-execution.json).
No phone/server action accompanies this UI revision. Current installed UI60-3 and
its existing signed backup are untouched. Revision4 visual approval/signing/install
are pending; code84 is retained, not increased. FIELD-1 remains NOT_STARTED.

## Owner approval and requested installation —16Oct17:11UTC

After approving the full-width map, the owner explicitly requested installation on
their own phone. This extends the earlier no-phone-actions implementation checkpoint;
it does not authorize a VPN CONNECT, tester delivery or gateway action. Safe selected
evidence: [owner-install.json](../../research/ui60-layout-20261016/owner-install.json).

- Preflight confirmed one authorized physical phone, API31/ARM64, expected installed
  diagnostic APK8e5579f0…4a8845, code84, sole previous signer and actual UID10283.
  No active VPN transport or app VPN service was observed. The actual installed APK
  was pulled into private storage and verified as the immediate backup.
- Existing local vault/memfd workflow signed the exact already-tested unsigned
  APKef3c7e06…2a1ec95b once; no rebuild, new key, secret output or plaintext key export.
  Signed SHA256: **`e6c9dce07520abb40ce29e7bfc7e39e2483db0572d22c31ab27931478da4b00f`**;
  size56,011,667bytes. Signature and16K alignment pass. Every original non-META-INF
  entry, including DEX/native payloads and native provenance, is unchanged by signing.
- Sole signer SHA256 remains
  `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
  Native SHA256 remains
  `be70a66ccc2bcbf0478915fd414c32de3bedb2a0ae0c3222a53e65eebd0a92b2`.
- One ordinary `adb install -r` began17:11:02.152UTC and returned success17:11:07.696UTC.
  Installed APK readback equals the signed hash; package, signer, UID10283 and code84
  are preserved. VersionName is0.1.18-research84-ui60-3. No `-d`, uninstall, data/cache
  clear, re-enrollment, private database/identity read or force-stop was used.
- Ordinary launcher start17:11:21.106UTC succeeded. At17:11:25.772UTC PID19934 was alive,
  VPN OFF, no active app VPN service, and the bounded UID-filtered startup log sample
  contained no new errors. This short observation is not exhaustive crash/ANR coverage,
  a traffic check, a full on-device visual review or device transport acceptance.
- Same code84/package/signer and unchanged storage sources preserve ordinary replace
  compatibility with the verified immediate backup8e5579f0…4a8845. No rollback was
  performed. Data preservation means replace-install without clearing data and retained
  UID, not a byte-exact audit of private contents. The owner can now inspect the UI.

This continuation adds signing1, owner replace-install1 and normal launch1;
CONNECT/export/server operations/tester transfer0. Emulator, builds and tests were not
restarted. Signed APK and backup stay private; no catalog, landing or public release
changes. Tester compatibility/grant/readiness remain unverified. Reuse this exact signed
candidate after those checks; do not rebuild/re-sign merely because field work waits.

## Owner-requested revision 3 — map width

The owner approved the remaining composition and requested only a wider main map.
The compact preview no longer derives its drawing width from the short block's
height. It uses the full existing content width minus the same6dp inset on each side;
height, surrounding panels, navigation, country/transport controls and the full
Route screen are unchanged. This is map rendering only, not a session/state change.
Revision2 unsigned APK1a11f98f…2e2ea92a and its receipts/renderer images remain archived;
its published checkpoint is42196f866ef501918ada272884b6aaef8dbcd8e8.
Revision3 unsigned build,15 targeted JVM checks and bounded visual verification
pass. At that build checkpoint product signing/transfer had not occurred. Only `RouteMapView.java` and the private
candidate versionName differ from revision2 product sources.

At the392px fixture viewport, the unchanged368px-wide/114px-high map frame now
draws across356px inside its6px insets instead of shrinking to about253px. Both
normal RU/EN OFF fixtures are pixel-identical to revision2 outside that map frame.
The actual map class passes eight width/height/density cases per configuration
(296/368dp widths,88/114dp heights,1x/2x density), including measured land-dot extent.
All54 scenes/eight navigation cycles and the real-IME component check use the new
APK; no previous candidate's render is relabeled as revision3.

The single UI assemble used a50%-of-one-core cgroup quota and85°C guard:338.464s,
peak78°C. Test-renderer preparation first failed under the service's ASCII locale;
explicit javac UTF-8 encoding fixed the harness only, with no repeated product build.
The successful renderer preparation took32.092s/peak70°C. KVM/Intel-GPU UI checks
used the same quota/cutoff and10-minute cap:132.080s,65 temperature samples,
peak84°C/last75°C. The service stopped after evidence was saved; the emulator is OFF.
As in revision2, emulator shutdown returned-6; graceful internal exit is not asserted.
These bounds/measurements are not a general temperature guarantee for other workloads.
See [map-only pixel check](../../research/ui60-layout-20261016/map-revision-check.json)
and [execution receipt](../../research/ui60-layout-20261016/map-revision-execution.json).

## Owner-requested revision 2

The owner accepted the general direction and requested the beta60 network/battery
block plus straight corners instead of chamfers. Revision2 restores the network
value and signal on the left, amber battery percentage/bar on the right, traffic
grid below left, and connection heading/selectors/state below right. Values still
come from the unchanged modern telemetry pipeline; an empty graph has grid lines,
not fabricated traffic. Shared frames now have square90-degree corners, retaining
thin strokes. Circular controls and icon geometry are not replaced with rectangles.
The message-route summary is retained in the existing telemetry detail dialog and
accessibility description, rather than occupying beta60's graph area.

Previous unsigned UI candidate52e903bb…617fcf6f and its changed sources are archived
locally; the original comparisons remain in publication8aa905994e42c5d41a9aa7d1231d1538f2873e87.
At that revision2 checkpoint the revised images still required owner confirmation;
the later revision3 approval and owner installation are recorded separately above.

Revision2 emulator preparation initially failed before UI tests: the Android system
process reported `IllegalStateException: Lost network stack`, and PackageManager
returned `Broken pipe`. After system-service recovery, readback still identified the
previous debug-only renderer; one subsequent renderer installation succeeded. This
is an isolated emulator-system failure, not a product startup/transport observation.
There was no repeated product build or phone operation to address it.

Large-font review then caught a genuine presentation issue: absolute text spans
ignored system font scaling. Relative spans now preserve beta60's size hierarchy
while scaling with the user's font setting; the renderer asserts this boundary.
This required one corrective UI-only assemble. A separate first IME run was blocked
by an observed `com.android.systemui` ANR dialog, not a product ANR. Its exact Wait
control was read from the emulator hierarchy before dismissal and final verification.

The owner subsequently reported96–99°C host CPU temperature/throttling during
software emulation. That emulator was stopped; the four final scene/navigation
receipts and images had already been saved, but the separate IME check was interrupted.
On explicit authorization to use a different mode, only the outstanding IME check
resumed with verified KVM descriptors and Intel host GPU, not `-accel off`/SwiftShader.
A systemd cgroup enforced50% of one CPU core (`cpu.max=50000 100000`), nice10,
10-minute maximum and a2-second temperature guard stopping at85°C. Over103.422seconds,
52 samples measured55–78°C, last58°C. These are observed temperatures, not a guarantee
against heat from other workloads. The IME check passed using the exact final renderer
APK, without reinstall/rebuild. The service was then stopped and no emulator process
remained. Shutdown reported emulator returncode-6; this is retained as a host-emulator
shutdown observation, not a product crash or an assertion of graceful internal exit.
See [bounded execution receipt](../../research/ui60-layout-20261016/emulator-execution.json).

## Revision3 identities — installed owner checkpoint

| Identity | Value |
|---|---|
| Starting review publication | `da2b13eeb66d1335296f4dbd4619ee7692431799` |
| Beta60 visual reference, resolved `5c740f2d` | `5c740f2d05f725ee1bcbe63a41f886605d4c7ac4` |
| Retained beta60 render-input APK | `8ee59352e5f490aea74c3c8c8aeefd0d65bec0c261a044899d512ca376cf6104` |
| Accepted modern cumulative source inventory | `b36c4a21ee6cf04acb192a0e6d140fa565b3e5ae75f6fc8d028d029c3152781d` |
| Retained accepted signed APK, not the UI candidate | `8e5579f04de91e4ec00e3e79271dbb0f380b1ed91945ff89016aa50d274a8845` |
| Modern before-render input, unsigned APK | `b2a4b76b3218ec06f3409154a1a14f71bf4feff3206be3282c25852eabdd35ca` |
| New UI cumulative source inventory, not a Git commit | `7f8fd0dd8498c61c4f182b1f3322d9c2d38d17dc4f30ff9e06cef0b733d9c39d` |
| **New unsigned UI APK** | `ef3c7e06f5666c87b8e31bf1eddc318d1a7cd97a0c720187f05e342a2a1ec95b` |
| **Signed and owner-installed UI APK** | `e6c9dce07520abb40ce29e7bfc7e39e2483db0572d22c31ab27931478da4b00f` |
| Embedded restricted native, reused unchanged | `be70a66ccc2bcbf0478915fd414c32de3bedb2a0ae0c3222a53e65eebd0a92b2` |
| Gateway retained identity, no live query in this task | `a537257162348afc35b1ebc08755d8c5dc1cd90e74c49e3987fb3eb81885e61f` |

Package `com.familyconnect.app.friends`; versionName **0.1.18-research84-ui60-3**;
versionCode **84**, minSdk31, arm64-v8a, unsigned size55,990,388bytes.
Existing-key signing and owner installation completed as recorded above. Code84
retains same-code replacement compatibility with the accepted owner APK; signer and
package were verified against the actual installed backup before replacement. This
does **not** promise ordinary rollback to an unknown tester's lower-code APK. Tester
version/signer/ABI/API and authorization remain prerequisites after visual approval.

Native metadata remains byte-for-byte the accepted native manifest, including its
original source inventory. The separate UI/provisioning build manifest binds the new
UI inventory and identifies native reuse. Neither provenance guard was disabled;
the library is not represented as rebuilt from UI sources.

## What changed

- Main screen returns to beta60 ordering: full header; large centered circular
  switch/status/server load; two-column telemetry and country/transport controls;
  compact full-width map; fixed four-item bottom navigation. No old transport list is copied.
- Square frame geometry follows the owner's revision2 request through the shared drawable, including
  buttons, navigation, chat bubbles, route/settings panels and common dialogs.
  Current background, palette, text styling, health colors and animation logic remain.
- Thin shared stroke parameters replace scattered widths in the touched frame,
  toggle, telemetry and map paths. Modern anti-aliasing and density scaling remain.
- Current configured-message-route information remains in existing telemetry details.
  Modern connection terminals, actual observed transport, diagnostics,
  activation, export, voice preview and settings remain available.
- Chat empty/list/conversation, route and settings already retained beta60's primary
  hierarchy. Their shared geometry is restored rather than replacing these screens
  with historical activity implementations. All newer behavior is retained.
- DISCONNECTING and cleanup-required get distinct localized presentation labels.
  These labels consume existing service state; no TUN-based readiness shortcut or
  new runtime state is introduced.

Accessibility deviations from beta60 are deliberate and bounded: selectors retain
48dp targets, text is not shrunk to beta60's tiny sizes, two-line navigation remains
readable, and a constrained main workspace scrolls independently of navigation.
Country/transport labels wrap naturally (up to three lines); telemetry measures
actual text/selector heights, rather than clipping large-font descriptions.
The main dial keeps the beta60 0.60-width cap in portrait; short landscape uses120dp
so the complete dial remains reachable. The map receives remaining space and
is omitted from the main preview when less than88dp remains; the full Route tab
remains accessible. At normal size the taller accessible controls leave a shorter
map preview than beta60. No decorative panels or additional spaces are introduced.

## Real-code comparisons

All images are **synthetic fixtures**, not CONNECT evidence. Columns are beta60 →
accepted modern UI → new UI, same392×780 logical viewport, density1, RU, fontScale1.
Actual retained APK UI DEX/resources are used, not hand-drawn mockups. The isolated
renderer has no Internet permission, provider/service declarations, native libraries
or production credentials. It invokes real view builders/projection callbacks while
avoiding product onCreate/onResume enrollment and service startup. FLAG_SECURE stays
set; the view tree is rendered to a Canvas, not captured by disabling security.

![Main comparison](../../research/ui60-layout-20261016/comparisons/home-off.png)
![Chat list comparison](../../research/ui60-layout-20261016/comparisons/chat-list.png)
![Conversation comparison](../../research/ui60-layout-20261016/comparisons/chat-conversation.png)
![Route comparison](../../research/ui60-layout-20261016/comparisons/route.png)
![Settings comparison](../../research/ui60-layout-20261016/comparisons/settings.png)

Additional empty-chat, main-state, narrow/large-font and keyboard evidence is linked
from the [reproduction/evidence index](../../research/ui60-layout-20261016/README.md).
Reference artifacts were frozen before editing; the conversation fixture callback
was corrected during QA and reference images regenerated from the same retained APKs.
This does not substitute current product code into the historical reference.

## Functional and build boundary

- Full offline `assembleResearchProvisioning` with accepted native bytes succeeds.
- 15 targeted JVM cases: UI presentation3, bootstrap correlation2, diagnostic ring5,
  restricted startup3, startup fidelity2. No transport/race/PKI suites rerun.
- Source boundary checks compare the derivative against the retained accepted tree:
  only the listed UI/resources/version-name/test files differ. Connection handlers,
  navigation/lifecycle methods, settings/route actions and telemetry sampling logic
  are unchanged. All other product sources, including async writer/queue64, ownership,
  handoff, generation guards, early correlation, security and storage, are identical.
- All embedded native payloads, not only `libfc_restricted.so`, are byte-identical.
  Permissions, SDK/ABI/features and restricted manifest are unchanged.
- Renderer checks and limits are recorded separately in the evidence index. Fixtures
  are not an ARM64 native runtime test, device acceptance, live export or field trial.
  No claim of API35/OEM keyboard runtime coverage follows from an API31 emulator.
- Final candidate:54 real-code scenes across four configurations, eight navigation
  cycles, retained controls/session state, zero service requests, secure flag retained.
  Button targets remain at least48 logical pixels; selectors have no measured ellipsis.
  Each configuration checks beta60 telemetry grouping, retained message-route details
  and actual rectangular frame pixels; revision3 adds eight map dimension/density
  cases per configuration. A separate real-IME ChatThreadView check preserves draft and
  selection; system-bar insets27/54px and IME bottom366px are recorded, not inferred.
  The79 safe screenshots include24 reference frames and55 candidate/component frames.

Eight UI-only assembles preceded the first checkpoint; revision2 uses two additional
UI-only assembles and revision3 uses one. The final unique test count is15, not an aggregate count. An initial
sandbox Gradle socket denial was resolved by the normal approved external execution.
No transport/race/PKI suite, native rebuild or live acceptance was substituted.

The existing Android dashboard test source now distinguishes fixed navigation from
scrollable workspace controls instead of banning every ScrollView. That legacy
device test suite was not executed; the isolated renderer checks below have their
own explicit scope and do not imply full product lifecycle coverage.

The normal research provisioning mechanism is retained. No gate is enabled, no
credential cache copied, and no identity is embedded for a tester. Its actual device
applicability is still a separate post-approval check, not inferred from owner UID.

## Revision3 result / installation checkpoint (preserved)

| Criterion | Result at this checkpoint |
|---|---|
| UI_LAYOUT_RESTORED | Main/beta60 telemetry; square frames; revision3 full-width compact map; other layout retained; accessibility deviations listed above |
| CURRENT_STYLE_AND_THIN_STROKES_PRESERVED | Current palette/background/type and state sources retained; common density-scaled strokes |
| UI_STATE_AND_NAVIGATION_TESTS | 15 targeted JVM cases;54 fixture scenes;8 navigation cycles;real IME component check pass |
| TRANSPORT_NATIVE_SECURITY_UNCHANGED | Exact source boundary and all embedded native payload checks pass; no native rebuild |
| NEW_UI_SIGNED_APK | e6c9dce0…8da4b00f; installed hash matches, full identity above |
| TESTER_COMPATIBILITY_AND_AUTHORIZATION | NOT_CHECKED; owner compatibility does not establish tester applicability |
| FIELD_STAGE_AND_RESULT | NOT_STARTED / owner on-phone inspection, then tester preparation |
| FIRST_FAILURE_OR_REMAINING_BLOCKER | No installation/startup error observed; owner inspection and tester checks remain |
| FINAL_DEVICE_STATE | Owner UI60-3/PID19934/VPN OFF at17:11:25UTC; tester untouched; gateway not queried or changed |
| ACTION_COUNTS | UI assemble11 cumulative,1 in revision3; native rebuild0; product signing1/owner install1/normal launch1; CONNECT/export0; server operations0 |

**UI_VISUAL_APPROVAL=APPROVED.** Owner inspection installation is complete; it is not
a tester field episode. Both unsigned and signed APKs remain private. Tester selection/
contact/delivery/install, CONNECT/export and server SSH/actions: **0**. Only a disposable
credential-free emulator was used for fixtures; its debug-only renderer packages are
not product or distribution artifacts. The emulator remains off.

Previous NEW_PAIR_FAST_RECONNECT=PASS_BOUNDED remains bound to the **previous exact
APK** and gateway. The new UI APK is not automatically device-accepted. Historical
causality, chat handoff, supervisor, field coverage and public release remain open.
Continue with the [field-stage record](2026-10-16-field-1-ui60-warm-start.md) after
owner inspection and tester prerequisites; do not repeat UI development or owner reconnect.
