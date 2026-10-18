# MESH product integration — 2026-10-18

**RESULT: PARTIAL. Local source/build/test only. No release or deployment.**

Official name: **MESH — Media Encapsulated Secure Hop**, not translated.
Family Connect owns the secure media transport; VP8/RTP is its current carrier;
Telemost is its current media-session provider. This is not a claim of decentralized
networking, peer routing, multi-hop or guaranteed bypass.

Android presentation integration is built and unit-tested on the approved UI84
source. Windows and GTK Linux product clients have no integrated media backend;
adding an inert menu item would not meet acceptance. All-platform acceptance is
therefore **not achieved**. The separate earlier all-activated admission problem
also remains **NOT_DEPLOYED / unresolved in production**; renaming does not fix it.

## Follow-up: owner-authorized GitHub source checkpoint

After the naming task the owner explicitly requested committing everything to
GitHub. All accumulated nonignored source/doc changes were committed and the push
to `origin/main` succeeded:

- Before: `8d046321039d0bd1e18ecc1af979ff90f591e029`.
- Source checkpoint: `edca5447418141cb44c0706e26d1973d7defd397`,
  [GitHub commit](https://github.com/Joker20380/family_connect/commit/edca5447418141cb44c0706e26d1973d7defd397).
- 240 changed files,33183 insertions,163 deletions. This includes earlier carrier,
  Android diagnostics, activation-v2/management experiments and historical reports;
  it is deliberately a broad source checkpoint, **not** a claim that all this work
  is production-ready or that it contains only naming changes.
- The worktree was clean immediately after the source commit. This subsequent
  documentation-only receipt records the successful push without altering runtime.
- `python3 scripts/check_public_sources.py`:1942 index entries,0 blocked files.
  This is the repository's bounded guard, not a proof that every possible secret
  format is detectable. No state directories, private keys, databases or binaries
  were staged. `.gitignore` now excludes the local `artifacts` symlink as well as
  the already-ignored artifact directory. `.gitattributes` gives the MESH patch
  the same narrow whitespace rule as the existing Xray patch, preserving valid
  blank unified-diff context. `git diff --cached --check` passed.
- Repeated local command, using the retained control/identity venv:
  `python -m pytest -q tests/test_mesh_product.py tests/test_restricted_activation_policy.py tests/test_restricted_activation_http.py tests/test_activated_maintenance.py --tb=short`:
  **59 passed in6.28s**, no skips. Authorized outside-sandbox loopback execution;
  no live gateway/device interaction. These selected tests do not replace full CI.
- GitHub readback for that exact SHA reports four push-triggered workflows.
  [phase0 run39110077526](https://github.com/Joker20380/family_connect/actions/runs/39110077526)
  was IN_PROGRESS at initial readback around08:05UTC; completion/PASS is not claimed.
  Native/platform and full-suite outcomes remain to be reviewed.
- No tag, release, APK installation/distribution, signing, gateway restart or
  deployment occurred. Product versions and unresolved acceptance gates are unchanged.
  A later rollback of source must be a reviewed revert, not a force-push or device
  identity reset. The earlier baseline section below describes the naming phase
  **before** this separately authorized publication.

## Baseline and provenance

- Initial and final root HEAD:
  `8d046321039d0bd1e18ecc1af979ff90f591e029`. No commit, branch or push in this task.
- The root already had214 dirty/untracked status entries at MESH task entry.
  Existing transport, API, access experiments and release work were preserved.
  Snapshot: `state-client-build/mesh-product-20261018/baseline-status.txt`,
  SHA256 `21a5d8cc3ab406b2c66ecad4b4df19bdc1645d7ba56d51c03445c9732c674872`.
  Tracked worktree delta: sibling `baseline-working.patch`,
  SHA256 `6524eab3843f4716e4e2d0f37eb829e06e57171d3a051602d7d2a623938c7bd5`.
  This patch is not a backup of untracked files; none were removed or overwritten.
- Root Android source is the older beta65 baseline. Rebuilding it as the new
  tester UI would regress the accepted design. The actual source selected here is
  `state-client-build/transport-write-batching-1/source`, version
  `0.1.18-research84-ui60-4-batch1`, code84, package `com.familyconnect.app.friends`.
  Its base commit is `f5240994869826c6a28f59e58e38256c688cf6eb` plus the sealed
  cumulative source inventory
  `cdd089478624ff5113d14590a340092684127a674565c3acfe6750aa76a17790`.
- Retained Oct17 acceptance/review records report private code84 already installed
  and delivered to the tester, but NOT_PROVISIONED. Original signed artifact SHA256:
  `697f9c244b67f75e7e3e612dbcd91a48891d32ee77e23fd9bce173a5f049233f`.
  This task did not re-read the physical device or redistribute that artifact.
- Windows source remains0.2.15; GTK Linux source remains0.2.11. No desktop version
  change, installation or release. Public Android beta65 and invitation/updater
  beta60 are retained documentation observations, not a new public-artifact audit.
  Public binaries, catalogs, checksums and download links were not changed.
- Latest read-only GitHub result at audit time: phase0
  [run39032869009](https://github.com/Joker20380/family_connect/actions/runs/39032869009),
  completed SUCCESS2026-10-17T12:39:14Z, commit
  `947d816c2061cea8d47dde2b803fac4ea44ba74b`, branch
  `review/supervisor-state-20261015`. It validates that earlier baseline, **not**
  these uncommitted MESH changes. No new deployment result is asserted.

## Audit map and platform boundaries

| Area | Actual implementation and decision |
|---|---|
| Android selector/persistence | UI84 `FriendsActivity.java`: Auto/AWG3.1/TCP REALITY/legacy `telemost`; private activity preferences key `transport`. Only display strings change. Selection handlers, stored values and restore mapping stay unchanged. |
| Android Auto/fallback | `ConnectionService`, `ConnectivityOrchestrator` and restricted bootstrap/cache/recovery code remain sealed baseline inputs. No selection ordering, fallback or timeout rewrite. |
| Windows | `clients/windows/MainForm.cs` exposes TCP REALITY/AWG3.1; `AutoSelected` is false. Registry `Software\family_connect` stores tcp/awg. `Broker.cs` has connect-tcp/connect-awg, no media command. No fake Auto or MESH item added; source unchanged. |
| Linux desktop | `clients/desktop/app.py` has AWG3.1/TCP REALITY and persisted route JSON. `backend.py` has Linux AWG helper and LinuxTCP. No product media backend or Auto selector; source unchanged. Gateway/lab CLI is not GTK integration. |
| Provider/carrier | `carrier/telemost/` contains current session/signaling/VP8/RTP implementation; `carrier/reliablestream/`, `tcpforward/`, `wholedevice/` and Android restricted native bridge remain unchanged by MESH work. Existing dirty changes predate this task. |
| Provisioning | `control/product/provisioning.py` / `ProvisioningService`, `provisioning/models.py` / `NetworkProvisioningState`, gateway bindings and capabilities retain existing values and serialization. No new MESH wire capability is advertised. |
| Identity/entitlement | Android `FriendsIdentityVault`, control identity/proof/revocation handling and signed restricted directory remain unchanged by naming. Earlier unshipped activation-v2 edits are a separate candidate, not part of this result. |
| Diagnostics/support | `DiagnosticRing` gains static optional metadata; existing event identifiers, restricted transport class, Support ID, lifecycle, disconnect/recovery/fallback fields remain. `scripts/correlate_restricted.py` consumes old/new exports identically in the added test. |
| CI/releases | `.github/workflows/clients.yml` and `test.yml` retain platform checks and release boundaries. The existing Android contract pytest command now includes `test_mesh_product.py`. No CI dispatch/push, offline signing or release workflow run. |

The remaining occurrences of Telemost in the prepared Android main Java/resources
describe the technical diagnostic provider. Internal enum `TELEMOST`, package names,
signed IDs and machine event identifiers intentionally remain legacy-compatible.

## Implementation and compatibility strategy

```text
Product architecture today: Family Connect → MESH → VP8/RTP → Telemost → Gateway
Compatibility mapping: MESH (UI) → telemost (saved selection)
                      → restricted (implementation/events)
                      → telemost-webrtc (signed directory seed)
```

The architecture chain describes today's implementation, not a permanent provider
constraint. The compatibility chain is a mapping of existing identifiers, not a
new wire format. Target ID `mesh` is deliberately not accepted as a replacement:
no migration exists or is needed for display renaming. No `mesh/1` is introduced.

The retained `pilot/android-restricted/mesh-product.patch` applies only seven files
to the approved UI84 source:

1. `FriendsActivity.java`: selector, active route and status labels become MESH.
2. `DiagnosticRing.java`: optional `transport_metadata` catalog, inner schema1.
3. `TransportPresentation.java`: fixed display mapping and static diagnostic labels.
4. `res/values/connection_terminal.xml`: English MESH label.
5. `res/values-ru/connection_terminal.xml`: Russian MESH label, name untranslated.
6. `TransportPresentationTest.java`: legacy mapping, locales, static metadata.
7. `DiagnosticRingTest.java`: additive metadata and unchanged legacy event fields.

Outer diagnostic schema stays1. Catalog entry `restricted` records name MESH,
implementation restricted, selection_id telemost, carrier VP8/RTP, provider
Telemost. This is descriptive metadata, not a capability or successful connection
claim. No runtime credentials, tokens, room data, private keys or device identifiers
are added. Older exports without this optional field remain supported.

Root Android receives the same helper/tests, additive DiagnosticRing field and
existing restricted-status label. It does **not** replace the newer UI84 Activity
with the older root Activity or fabricate a new root media selector. Source
convergence onto the accepted UI84 baseline remains a gate before any future
integration commit/release.

No geometry, margins, fonts, animation, assets or layout code is changed. No new
engine, abstraction factory, carrier framing, ReliableStream/TLS/OpenTCP/DNS,
reconnect, transport timeout, identity reset or provisioning regeneration is added.
All native libraries in the local test APK match the accepted unsigned84 baseline
byte-for-byte. This is evidence of unchanged implementation, not a live network test.

## Changed files belonging to MESH

- `.github/workflows/clients.yml` (only adds the new contract test to its command).
- `clients/android/app/src/main/java/com/familyconnect/app/`:
  `FriendsActivity.java`, `DiagnosticRing.java`, new `TransportPresentation.java`.
- `clients/android/app/src/test/java/com/familyconnect/app/`:
  `DiagnosticRingTest.java`, new `TransportPresentationTest.java`.
- New `pilot/android-restricted/mesh-product.patch`, `check_mesh_ui.py` and
  `tests/test_mesh_product.py`.
- `README.md`, `README.ru.md`, `README.en.md`, `carrier/README.md`.
- `docs/architecture.md`, `docs/clients.ru.md`, `docs/clients.en.md`,
  `docs/reticulum/HOME_GATEWAY_DESIGN.md`.
- `docs/STATUS.md`, `docs/PLAN.md`, `docs/README.md`, new
  `docs/adr/002-mesh-product-name.md`, this report, and the superseding-scope note in
  `docs/releases/2026-10-18-telemost-all-activated-preflight.md`.

The full worktree diff contains much more pre-existing work; it must not be treated
as the MESH patch. No Windows/Linux runtime files were changed by this task.
Canonical transport documentation now covers purpose, composition, security,
lifecycle, reconnect, diagnostics, limitations and compatibility. ADR002 follows
the existing ADR practice. PLAN distinguishes MESH1 existing media transport with
incomplete acceptance; MESH2 multi-provider/multi-route PLANNED; MESH3 distributed
mesh/Reticulum RESEARCH/FUTURE. Neither future stage is a current-release commitment.

## Executed verification

| Check | Result and boundary |
|---|---|
| Approved UI84 assembly and selected JVM suites | PASS:112 tests across15 suites,0 failures/errors/skips; unsigned research APK built. |
| Python compatibility/regression selection below | PASS:190 tests,0 skips, outside sandbox. Covers identity, provisioning/security, support IDs, correlation and existing desktop transports. |
| APK native preservation | PASS: all12 native `.so` libraries byte-identical to unsigned baseline84. |
| APK alignment/package metadata | PASS: `zipalign -c -P 16 4`; aapt2 confirms friends package, code84, minSdk31/target35. |
| New selector/localization/diagnostics contracts | PASS: legacy IDs remain, presentation-only overlay, RU/EN MESH, old correlator result unchanged by optional metadata. |
| Worktree delta/whitespace | PASS: `git diff --check`; tracked diff sections compared with the MESH-entry snapshot change only the listed UI/tests/workflow/docs files. Pre-existing tracked network/identity/API changes are unchanged. |
| Desktop MESH runtime | NOT IMPLEMENTED; tests establish existing AWG/TCP scope, not working desktop MESH. |
| Physical selector/relaunch/upgrade/UI render | NOT RUN; no device mutation or emulator interaction. Source restore/save code is unchanged; unit checks do not prove a physical upgrade. |
| Live network/reconnect/fallback | NOT RUN; no disconnect, gateway restart or production test. Existing Auto/recovery unit suites pass. |
| Current-patch remote/native Windows CI | NOT RUN; no authorized push of this source. Earlier phase0 success is not current-patch evidence. |

JVM suites: AdmissionDiagnostics3, DiagnosticRing6, RestrictedStartup3,
TransportPresentation3, StartupFidelity2, Ui60Presentation3, CutoverRecovery14,
RestrictedCache14, RestrictedRecovery5, RestrictedBootstrap6, ReadinessProduct10,
ConnectivityOrchestrator29, ConnectionTerminal8, FriendsReadinessProtocol4,
BootstrapCorrelation2. No disabled or skipped test is counted as PASS.

Executed Android command:

```sh
python3 pilot/android-restricted/check_mesh_ui.py --resume-after-sandbox
```

The initial Gradle attempt failed because sandbox socket creation was denied;
the authorized outside-sandbox retry completed successfully. The runner verifies
the sealed baseline inventory and unchanged non-presentation inputs, builds into
an isolated directory and neither signs nor installs anything. It requires the
retained approved source/toolchain and a prepared copy with `mesh-product.patch`
applied; it is not a general clean-checkout build. `--resume-after-sandbox` is a
guarded retry of the recorded denial, not a way to overwrite a completed receipt.
For a new reproduction preserve existing evidence, copy the sealed baseline to a
fresh work directory and apply the seven-file overlay before invoking the runner
with appropriately selected work/output paths. Do not rebuild the older root UI
or overwrite the accepted source capsule.

Python command (the retained venv matches control/identity dependency locks):

```sh
state-client-build/field65-export16/telemost-admission-ownership-1/build/venv/bin/python -m pytest -q -rs \
  tests/test_mesh_product.py tests/test_device_identity.py tests/test_android_control_identity.py \
  tests/test_friends_identity_store.py tests/test_provisioning_security.py \
  tests/test_restricted_correlation.py tests/test_support_ids.py \
  clients/desktop/tests/test_profile.py clients/desktop/tests/test_recovery.py \
  clients/desktop/tests/test_awg.py clients/desktop/tests/test_tcp.py \
  clients/desktop/tests/test_operations.py --tb=short
```

Initial sandbox attempt:187 passed,2 skipped,1 failed on denied loopback socket.
Authorized outside-sandbox repeat: **190 passed in1.89s**, no skips. This was local
loopback/fixture testing, not gateway access or a production disconnect test.

Evidence directory: `state-client-build/mesh-product-20261018/build/`:
`receipt.json`, `artifact-qa.json`, `gradle-outside-sandbox.log`, and JUnit XML under
`android/app/test-results/testResearchProvisioningUnitTest/`.

- Candidate source inventory:
  `0aa343101cbb0f65ffc20ea8b6e65104fd280d61e35416af9e99d9e070cc7a93`.
- Reused `libfc_restricted.so`:
  `dd722eada0da7c890a8d71a72099cba5d0bbac1ce73377bbdbc8e7b85d820c23`.
- Unsigned local APK SHA256:
  `2af685e5a60667af4cfedc1b997714cc2fa038d9976d5385fb0abe044f2e4a35`.
  Path: `android/app/outputs/apk/researchProvisioning/app-researchProvisioning-unsigned.apk`
  beneath that evidence directory. It retains version84 solely for compile/test.
  **Do not distribute it or replace the immutable signed84 artifact.**

Device Identity, private keys, entitlements, signed provisioning, capabilities and
active configurations were not written by this task. Identity/provisioning unit
regressions pass; an actual installed-app upgrade preserving them is **unverified**.
Wire protocol, cryptography and network implementation were not changed by MESH.

## Remaining work, proposed integration and release gates

1. Reconcile the newer accepted Android UI84 source with the version-controlled
   baseline without overwriting unrelated dirty work. Keep the presentation patch
   separate from unfinished access and network experiments.
2. Separately scope desktop integration: package the existing core for each
   platform; adapt existing identity/readiness stores; integrate platform broker,
   TUN protection, permissions and cleanup; only then add a working MESH selector
   and persistence. Preserve existing transport ordering and actual Auto behavior.
   No new desktop Auto algorithm is implied by this naming patch. Any required
   wire/crypto/infrastructure change requires a separate migration plan/approval.
3. Execute native Windows CI, GTK rendering/interaction and Android approved-UI
   screenshots/interaction, saved-selection relaunch, old-preference and in-place
   upgrade checks. Test explicit MESH and Auto fallback with the existing harness
   under separately authorized non-disruptive network conditions.
4. Resume the all-activated authorization/credential lifecycle work separately;
   the earlier proposed authority-lifetime experiment is not accepted here. A
   four-hour credential/CRL lifetime is not an APK usage entitlement. The current
   naming task does not repair that operational failure or authorize its rollout.
5. Only with later release/push authorization: assign a new immutable version,
   run platform CI on the exact source, verify artifacts, sign offline and perform
   approved installation/distribution. Update STATUS/PLAN/report/guides/catalogs
   and public checksums at that point; never overwrite the published84 artifact.

Current rollout is **none**: built unsigned locally; installed0, distributed0,
published0, gateway mutations0. Existing installed/public/invitation builds remain
unchanged. No signing key, profile, room credentials or product database is included
in these changes or receipts.

Rollback for this local presentation work is selective removal/reversal of the
owned MESH hunks or a fresh copy of the sealed baseline, retaining evidence. Do not
reset/clean the dirty worktree, revert other transport experiments, erase app data,
regenerate identity or roll back security floors. No server rollback is necessary
because nothing was deployed. A future released-version rollback must follow the
existing immutable release and increasing signed-catalog sequence rules.
