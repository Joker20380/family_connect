# UI60 layout / current style — safe implementation evidence

[UI report](../../docs/releases/2026-10-16-ui60-layout-current-style-1.md) ·
[Field continuation, not started](../../docs/releases/2026-10-16-field-1-ui60-warm-start.md)

## Review the actual UI

Every comparison uses real UI classes/resources from the named APK; **all data are
fixtures**, with no production account or private conversation. Left: beta60;
middle: accepted modern diagnostic UI; right: new UI. RU392×780, density1, fontScale1.

| Screen | Comparison |
|---|---|
| Main OFF | [Three versions](comparisons/home-off.png) |
| Empty chat | [Three versions](comparisons/chat-empty.png) |
| Conversations list | [Three versions](comparisons/chat-list.png) |
| Conversation | [Three versions](comparisons/chat-conversation.png) |
| Route / servers | [Three versions](comparisons/route.png) |
| Settings | [Three versions](comparisons/settings.png) |

Full-resolution [screenshots](screenshots/) include RU/EN main OFF, CONNECTING,
CONNECTED, DISCONNECTING, FAILED, RESTORING, cleanup-required; route/settings and
three chat states. The candidate additionally has320×640/fontScale1.5 RU and780×392
EN fixtures. Constrained main workspace scrolls; bottom navigation stays fixed.
Country names wrap instead of reproducing beta60's tiny text. Blank metrics remain
unknown; fixture/emulator telemetry is never described as owner TUN proof.

Revision2 follows the owner's requested beta60 telemetry grouping and square corners.
Revision3 changes only the compact map width and private versionName. The actual
map rendering fills available width without making surrounding panels taller.
[Map-only pixel check](map-revision-check.json) confirms normal RU/EN OFF pixels
outside the map are identical to revision2; eight actual width/height/density cases
per configuration cover the narrowed-map regression. [Execution receipt](map-revision-execution.json)
records bounded build/KVM checks and final emulator OFF. Owner accepts the rest;
the final map image awaits confirmation before signing or tester transfer.
Network/signal, battery percentage/bar, traffic grid and connection selectors retain
modern data sources. Message-route information remains in the existing panel's
detail dialog/accessibility description, not in the graph. Four extra scenes use
explicit synthetic telemetry; they are not observations of a phone connection.

Final checks:54 candidate scenes across four configurations, eight navigation
cycles, zero service requests, secure flag retained, and15 targeted JVM cases pass.
Each configuration checks telemetry grouping and real rectangular-frame pixels.
The79 PNGs comprise24 reference frames and55 candidate/component frames.
[Real keyboard component viewport](screenshots/candidate-real-ime-chat-component.png)
is an additional measured IME check, not a picture of the keyboard itself:
IME visible, bottom inset366px, system bars27/54px, draft/selection preserved.

## Source and artifact boundary

- [`ui-only.patch`](ui-only.patch): apply **only** to the retained modern inventory
  `b36c4a21ee6cf04acb192a0e6d140fa565b3e5ae75f6fc8d028d029c3152781d`, never root main
  or beta60. Full reference commit is in the report. No whole old activity replacement.
- [`boundary.json`](boundary.json) / [`verify_boundary.py`](verify_boundary.py):
  only eleven UI/resource/version-name/test paths differ; non-UI product files and
  connection handlers/lifecycle/navigation/telemetry sampling remain exact.
- [`build-cumulative-source.json`](build-cumulative-source.json): cumulative file
  inventory against baselinef524099, not a publication commit or native rebuild.
- [`build-receipt.json`](build-receipt.json) / [`artifact-check.json`](artifact-check.json):
  full UI assemble,15 targeted JVM tests, identical native payloads and restricted
  provenance, identical permissions/SDK/ABI/features. Code84 is unchanged; versionName
  identifies the new UI candidate. No production signing/install or public APK.
- [`render-inputs.json`](render-inputs.json), [`screenshots.json`](screenshots.json),
  [`ui-tests.json`](ui-tests.json): exact input APK identities, image hashes and bounded
  fixture results. Renderer-debug APK hashes are **not** product artifact identities.

## Reproduce locally

The scripts retain the private build workspace's relative retained-input layout.
Copy these tools into `state-client-build/ui60-layout-current-style-1/` and the
`renderer/` subtree beneath it. Retained accepted artifacts and SDK/Gradle caches
are prerequisites, not included in Git. `prepare.py` verifies accepted inputs,
creates an isolated derivative and extracts beta60 reference sources. Do not run
prepare over an existing derivative. Apply `ui-only.patch` there, then run:

```
python3 verify_boundary.py
python3 build_ui.py
python3 check_artifact.py
python3 renderer/build_fixture.py candidate build/android/app/outputs/apk/researchProvisioning/app-researchProvisioning-unsigned.apk
python3 renderer/run.py candidate --full
```

The Gradle build is offline; `verifyProvisioningResearchInputs` and native producer
guards remain enabled. Native binary **and native manifest** are copied unchanged;
the new UI inventory is recorded in the separate research asset/build receipt.
No native/JNI transport build is requested or implied.

Rendering uses a new credential-free Android31 x86_64 emulator, explicit ADB server
port5040 and serial`emulator-5580`, never a phone. The runner repackages retained
DEX/resources with an isolated instrumentation/host manifest and standard existing
Android debug key. It removes native libraries, all production services/providers,
and Internet permission. These test-only APKs are neither published nor transferred.
Product onCreate/onResume is not invoked. Reflection calls actual view builders and
chat projection callbacks with synthetic contacts/messages and connection states.
Canvas reads the view tree with FLAG_SECURE still enabled. No product security flag
or manifest changes are used to obtain screenshots.

Do not repeat the original software-CPU emulator launch. It was stopped after the
owner's host-temperature warning. KVM is usable on this host outside the filesystem
sandbox; sandbox absence of `/dev/kvm` must not trigger `-accel off` fallback. Future
local runs require an approved `-accel on -gpu host` launch, verified hardware
acceleration, a cgroup CPU quota, temperature cutoff and finite lifetime. The final
outstanding IME check used50% of one core/nice10,85°C cutoff and10-minute cap, then
stopped after103.422seconds. No whole scene matrix or product build was repeated for
that mode change. [Execution receipt](emulator-execution.json) records the78°C peak
and shutdown limitation; the emulator is not left running between tasks.

Navigation exercises two route→settings→home cycles per configuration, retaining
the same main controls and session ID/status. A context guard rejects service start/
bind requests; none are permitted. All candidate Button targets remain≥48 logical
pixels at density1. This checks the UI construction boundary, not lifecycle behavior
under real backend callbacks; unchanged source plus existing JVM checks cover the
retained handler/export boundary without running another CONNECT.

The real IME check is separate: the actual `ChatThreadView` is hosted in a disposable
activity, with no send callback, retained secure flag, draft and selection. It is not
a product onCreate or native runtime test. Earlier harness attempts were obstructed
by an emulator **System UI ANR** dialog; this was identified by the focused window
and dismissed using its observed `android:id/aerr_wait` button. No product code was
changed to address that emulator condition. See the final receipt for IME outcome.

## Limits and next action

- The image suite is isolated UI-code rendering, not screenshots of a live connected
  owner/tester session. Modern background chat is not stopped or manufactured on a
  real phone. No credentials, grants, identities or provider rooms are accessed.
- API31 renderer coverage does not claim API35 edge-to-edge/OEM keyboard validation.
  Existing inset/IME handling is not reverted. Insets/keyboard receipt has its own
  scope; view-tree fixtures are not evidence of full Android lifecycle acceptance.
- Activation/deep-link/export/transport-selection handlers are retained, not exercised
  against accounts. Export serialization checks remain targeted JVM tests. No export
  is generated from a real device. Shared frame geometry applies to those dialogs.
- Same code84 enables potential same-signer owner replacement/return without `-d`;
  a tester's lower version is not promised as an ordinary rollback target.
- Await **owner visual approval** before applicability/grant/readiness checks and
  product signing/private owner transfer. The authorized field continuation remains
  one CONNECT,240s/18min, no reconnect or server repair. It has not started.

Historical A/B causes, chat handoff, supervisor, broad field acceptance and release
are unchanged. Accepted old-APK no-restart PASS is not reassigned to the new UI APK.
