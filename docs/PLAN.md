# План / Android controlled beta and paused desktop queue

## Current engineering priority / Текущий critical path

<!-- FLEET-BOOTSTRAP-2 current -->
**2 November owner authorization:** implement and admit the second Amsterdam node for Android,
Linux and Windows. Compatible AWG/TCP assignment source now retains schema2 and pins existing
devices to their previous signed catalog; new assignments can use the second physical NL.
Rollback is forward-only with a newer catalog sequence. No client runtime/anchor/schema change,
no new PLAN ID, no live deployment or catalog publication in this source transition.
Routing regression287 PASS (25 environment-dependent skips), new routing tests46 PASS,
Android JVM174 PASS; native Windows conformance/DPAPI, ordinary-user and visual checks PASS.
Public Linux0.2.11 tagged parser accepts all3 new vectors; Windows0.2.15 parsers are unchanged.
MESH routing and production renewal remain unchanged; second-node admission is not complete.
Owner now explicitly accepts the existing TOFU pin without another provider-console comparison;
strict single-host SSH checking remains. Read-only new-node preflight PASS; first-install
ordinary AWG/TCP source29 new tests PASS, combined contour316 PASS/25 existing skips.
[Second-node preparation and trust decision](releases/2026-11-02-second-nl-ordinary.md).
[Multi-node source and qualification](releases/2026-11-02-fleet-multinode-source.md) ·
[Original constraint and measured timing](releases/2026-11-02-fleet-bootstrap-2-activation-check.md).

**READY_FOR_FLEET_BOOTSTRAP_2_HOST — source PASS; A→B→A, role reboot and retirement PASS.**
Existing FLEET-BOOTSTRAP-2 only; no new PLAN ID or production activation. Owner wants two
Amsterdam servers; first production NL remains excluded. Reserved disposable VPS remains
Ubuntu24.04/x86_64; no reinstall/deletion or production/catalog admission is implied.
Frozen deployable source `d3416ea4abacfafc843411f765fb8037722b55d0` remains unchanged and pushed.
A/B each reproduce archive/manifest/signature/SHA inventory twice byte-identically. Their only
member difference is reviewed monitoring revision metadata; native binaries, roles, ports,
material slots/schema and protocol contracts match. Exact four natives and282-file MESH source
provenance/licenses remain bound. Private signer, packages and material remain outside Git.
Offline Ubuntu24.04 native/config/unit/nft/material/A-B/rollback/boot/retirement qualification PASS.
Exact-native synthetic loopback REALITY/HTTPS and offline MESH mTLS-directory/guard checks PASS.
Retained unchanged-source qualification: fleet324 + console156 =480 PASS; paid170 PASS;
Django check PASS; migration drift NONE. This continuation changes evidence/docs, not runtime.
Signed permit, exact SSH/target/agent/bundle/key bindings, production exclusions, immutable
releases, encrypted material, two-phase external acceptance and append-only evidence remain.
Trials01–07 RETIRED; signed retirement precedes disposal of their operator client files.
Original FLEET_MESH_PROBE_1 custody retained; separate publisher token remains private.
Trial06 completed real A→B upgrade→A explicit rollback with signed AWG/TCP/MESH acceptance.
Trial07 completed one guarded physical reboot of A, preserving node identity and bundle.
All six services recovered automatically with zero restarts; no manual role restart was used.
Fresh, distinct external acceptance before/after reboot passed AWG/TCP/MESH, DNS/HTTPS/egress
and operator cleanup. Each receipt was accepted while fresh, then the node was activated locally.
Final drain/retirement PASS; disposable node secrets and three operator clients removed.
Reserved VPS is retained; no temporary rehearsal role is left active or published to users.
Owner confirmed VNC access and authorized the reboot; no manual recovery was requested.
SSH trust remains owner-accepted TOFU with unchanged strict pin, NOT independent verification.
That trust limitation is retained for future admission; no production-ready trust claim is made.
The physical reboot test is finished. No queued activation starts automatically.
Admitted: awg/tcp/mesh/profile-reader/publisher/snapshot/monitoring/load-monitor. Disabled:
mailbox/chat-services, production renewal/restricted-sync, registry/control-plane database.
Production RU/NL writes, catalog publications, user invitations, paid events, phone actions0.
Public Android109/sequence4/catalog4/paid108/entitlement/ledger1/4/cohort1/10/revenue0 unchanged.
[Reboot checkpoint](releases/2026-11-02-fleet-bootstrap-2-reboot.md) ·
[Reboot evidence](releases/2026-11-02-fleet-bootstrap-2-reboot.receipt.json) ·
[Qualified hashes](releases/2026-11-01-fleet-bootstrap-2-ready.receipt.json) ·
[Physical A/B receipts](releases/2026-11-01-fleet-bootstrap-2-host-ab.receipt.json) · [Runbook](fleet-bootstrap.md).
Older checkpoint NEXTs below are historical, not simultaneous active work.
<!-- /FLEET-BOOTSTRAP-2 current -->

<!-- FLEET-BOOTSTRAP-1 current -->
**FLEET_BOOTSTRAP_1_SOURCE_READY — SOURCE/SYNTHETIC FOUNDATION ONLY.**
Frozen artifact source: `a3fc3bf1c11a686ea444ad36d576c05ac5e24810` (remote-verified).
Strict physical-instance contracts, deterministic signed bundle, atomic sandbox installer,
one-use enrollment, role-health gates and Russian Django inventory/operator audit implemented.
Two identical builds and end-to-end CLI simulation PASS; fleet79, Django fleet10 and existing
focused paid/backend/canary/package170 PASS; Django check/migration drift PASS. The broader
console/fleet run is206 PASS/1 pre-existing synthetic-seeder UUID-prefix failure, retained.
Not live provisioning/data-plane acceptance: remote writes and catalog publication remain
closed; real-role binary provenance/adapters/physical health are live-rehearsal entry gates.
Production writes/user invitations/paid events/phone actions0. Public109/sequence4, catalog4,
paid baseline108, entitlement, ledger1/4/cohort1/10/revenue0 and NL fencing/routes preserved.
Owner109 result is closed; no server-TX investigation or external cohort expansion.
NEXT: **FLEET-BOOTSTRAP-2, separately authorized disposable VM/VPS rehearsal — NOT_STARTED.**
[Runbook](fleet-bootstrap.md) · [Checkpoint](releases/2026-11-01-fleet-bootstrap-1.md) ·
[Receipt](releases/2026-11-01-fleet-bootstrap-1.receipt.json).
Earlier Android/NL checkpoints below are retained evidence, not simultaneous active NEXTs.
<!-- /FLEET-BOOTSTRAP-1 current -->

**1 November — owner beta109 targeted Auto→AWG checks PASS; server TX retained.**
`DESKTOP_SMILEY_BASELINE_STALE_AFTER_REVIEWED_ANDROID107_CHANGE`: exactly one stale
Android106 pin, ChatThreadView.java; current file is byte-identical to accepted public108.
Reviewed voice-preview/recording visibility and message styling only; all49 faces, aliases,
GIFs, provenance, picker/insertion/foreground behavior and the other four source pins retained.
Catalog advances to Android108 with only that source digest changed. Full-file SHA fencing
remains; mismatch diagnostics name the safe relative path. Android production source unchanged.
Follow-up diagnostic validation uses host-independent Windows path parsing, rejecting POSIX
roots, Windows roots/drives and either traversal separator; no source pin or asset changes.
Existing CI41285992226/source4a7bf20 is terminal FAILURE: Android, Windows and compatibility
PASS; Linux failed only the stale baseline. Android includes JVM/control, carrier race,
readiness, native/audio, Gradle/tests/lint, APK verification, emulator AWG/TCP/Auto/system
consent, permission handover/revoke/cleanup, language/dashboard, ARM64 and unsigned packaging.
Its APK is not the final exact-source109 candidate. TCPFORWARD product fix remains accepted.
Local Ubuntu24.04/Python3.12 acceptance: smileys49 PASS, mandatory desktop1230 PASS/182 existing
skips/0 failures/0 errors, dependency60 PASS, JVM contour2 PASS; GTK, Disconnect poll50,
messenger27, smiley9, layout24, map/invitation/recovery/TCP and DEB/AppImage/package smokes PASS.
Minimal-container libXtst/TUN differences were corrected; initial logs retained, no test waiver.
**Full-matrix qualification and offline signing PASS.**
Retained CI-only marker `carrier/ci/beta109-full-matrix-qualification.txt` was pushed as
`600ae52bfac673ca0323bd7c96d6cdd369593624` and remote-verified. Sole candidate Client builds
run41289980872 completed SUCCESS; hosted scope android/windows/linux=true. Android, Linux,
Windows and Windows compatibility all PASS. General desktop release is correctly SKIPPED
(no v-tag/Release prefix); the Android job supplies the exact-source release artifact.
No rerun, second marker, new PLAN ID or production-source change was used to force scope.
Android gates PASS: JVM/control, carrier race, readiness/contracts, unified VPN/audio native,
debug/friends Gradle/tests/lint, APK checks, emulator AWG/TCP/Auto, interactive system VPN
consent with exact com.android.vpndialogs/enabled button/actual click, ownership transfer,
revoke/cleanup, language/dashboard and ARM64 packaging. Downloaded runtime XML has67 cases:
43 executed PASS,24 existing variant skips,0 failures/errors; no gate waiver was added.
Three downloaded UI captures were inspected: CPU display and country/transport selectors
remain visible in off/failure states. This is emulator evidence, not owner109 acceptance.
Linux mandatory pytest, smiley parity, dependency/GTK/Disconnect/messenger/layout/map/
invitation/recovery/TCP and AppImage/DEB/archive/launcher gates PASS. Windows build, Defender
step when available, install/driver/broker/TCP/upgrade/data/UI/invitation/layout/uninstall and
the separate identical-artifact compatibility job PASS. No desktop publication is claimed.
Downloaded ARM64 artifact13076449037 ZIP SHA256
`3c816fbf0b4ef603a712d0337af87b0220739ea15611351208c6685a43c96dcc` PASS.
Manifest: com.familyconnect.app.friends,0.1.18-beta109/code109,ARM64,min31,target35.
All12 native libraries and APK ZIP pass16K alignment. Exact source includes the TCP slot
release fix, system-consent harness and reviewed Android108 smiley baseline; catalog4 routing
and paid backend source are unchanged. Marker bytes/names are absent from every APK member.
Corresponding source/licenses and unsigned signing input verified. Offline signed APK:
SHA256 `2d602aa74e134fd0104fa0900ef28e6086a6eace8f0255f521e09ec48f9edca3`,56216936 bytes;
unsigned SHA256 `8b06f595f4b5eac733d528479768e8088b7f92ae60e2062b6f3606e4e5ec9991`.
Existing signer `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`
unchanged; APK signature, signed alignment and unchanged unsigned payload PASS.
**READY_FOR_BETA109_OWNER_UPDATE — immutable109 published and HTTPS-verified.**
Public and invitation versions are0.1.18-beta109/code109; Android update sequence4 is optional
(minimum supported code1, mandatory_after0). Signed APK matches the qualified source600ae52
and CI41289980872 byte-for-byte over verified HTTPS. Public108 remains immutable/downloadable.
Gateway catalog4/signature/routes, paid baseline108, entitlement through2026-12-01T07:09:19Z,
ledger1/4, cohort1/10, revenue0, registry identities/invites/grants and renewal/sync remain
unchanged. Read-only before/after fingerprints match; no backend restart or database write.
Only Android downloads, discovery catalogs and invitation were published; no forced update.
Canary remains COMPLETED_WITH_DEVIATIONS, final108 internet/84s READY PASS; never replay it.
**Owner109 installation confirmed.** Fresh owner
confirmation: «109 УСТАНОВЛЕНА». Read-only09:31UTC observation confirms exact0.1.18-beta109/
code109 from the latest authenticated readiness ACK, with no conflicting latest version.
Existing private owner binding matches the same non-revoked identity; entitlement remains
active through2026-12-01T07:09:19Z, ledger1/4 and cohort1/10. No database or canary write.
**Owner-reported data/UI PASS:** existing data remains present, server CPU is visible and
transport selection is available both before and after the requested single Force stop/reopen.
These data/CPU/selector/reopen checks are owner-reported; transport/cleanup evidence follows.
Read-only pre-Connect snapshot09:39UTC matches the existing owner binding/exact109 and ledger1/4;
the09:37:30UTC challenge/fetch/import ACK is READY with current material. It predates the
requested Connect and must not be presented as Connect latency or Internet/VPN-owner proof.
**Auto109 selected AWG — runtime PASS.** Owner reports one Auto Connect,
AWG selected,3 seconds to connected, Internet working and system VPN indicator present.
Read-only new-NL185.10.158.212 observation matches the existing bound peer: recent handshake,
bidirectional traffic over12s, service active/NRestarts0. No test session or server mutation.
New authenticated109 challenge/fetch/READY import ACK09:42:29UTC follows the pre-Connect
snapshot; provisioning/bootstrap are PRESENT_VALID. Server timestamps share one integer second,
not a measurement of tap-to-READY. The3s value is owner-reported tap-to-connected latency.
Auto's normal-profile priority before restricted fallback permits AWG; this is not MESH
data-path acceptance. No MESH109, whitelist109, independent HTTPS/egress or client OS-owner
inspection PASS is inferred. Earlier canary deviations are not erased by this AWG result.
**Owner109 targeted Disconnect cleanup — owner-confirmed PASS.** The fresh reply
«все нормально» answers the explicit Disconnect checklist: application off, VPN indicator gone,
notification gone and transport selector available. This is owner field evidence, not an
independent Android OS/ADB owner inspection. No extra Connect or forced MESH attempt requested.
Read-only cleanup: the initial12s sample has RX0/TX1400 bytes and no new handshake;
that residual server TX is retained, not labelled immediate complete silence. One fixed60s
follow-up ending09:55:03UTC has RX0/TX8865 and no new handshake. No client return
traffic is observed, but server-originated TX persists; full server quiescence/resource release
is NOT_PROVEN. No retry-until-zero or client reconnect. The registered AWG peer/old handshake
are expected persistent state, not proof of a retained client tunnel. No peer/certificate deletion.
Fresh authenticated exact109 observation, existing binding and active entitlement are preserved;
ledger1/4, cohort1/10, paid baseline108 and gateway catalog4 remain unchanged. Readiness ACKs
are control-plane material evidence and do not prove a live VPN while the application is off.
Result: **OWNER109_TARGETED_AUTO_AWG_OWNER_PASS_SERVER_TX_RETAINED**; install/data/CPU/selector/reopen,
one Auto→AWG Connect/Internet and one Disconnect/owner-reported cleanup are accepted in scope.
MESH109 field traffic and exact tap-to-READY remain unmeasured; earlier canary deviations retained.
No further phone action for this smoke. Paid-baseline109 promotion and controlled cohort
expansion are separate gates, NOT_RUN here; no READY_FOR_COHORT_3 claim or automatic enrollment.
No paid event, CRL operation or cohort expansion is authorized by this publication.

**Current beta109 qualification — TCPFORWARD_PRODUCT_SLOT_RELEASE_DEFECT (1 November).**
Accepted production state remains NL_REPLACEMENT_LIVE/catalog4, public108/Android sequence3,
paid baseline108, owner entitlement through2026-12-01T07:09:19Z, ledger1/4, cohort1/10,
customer revenue0. Canary COMPLETED_WITH_DEVIATIONS; final108 Connect/internet and84s READY
PASS. Earlier stage0/stage1 deadlines and selector defect remain recorded. No canary operation
is pending or replayed; no paid event, CRL, certificate deletion, backend restart or phone action.
Client CI41284629022/source9603e87 failed first at Restricted carrier race regression:
tcpforward TestBatchMixedPeerBulkAndSlotRelease/both, batch_test.go:163, TCP OPEN: stream_limit.
JVM/control and the other reported carrier race packages passed. Android instrumentation,
native build/release packaging did not run; the system-consent change is NOT_REACHED, neither
PASS nor FAIL. No qualified109 APK exists. Public108 remains authoritative.
Accepted108 source3b10199 and9603e87 have identical complete carrier trees, all34 tcpforward
source/test files, go.mod/go.sum and Client builds workflow. Both workflows pin Go1.26.1 and
the same dependency-selected go test -race invocation. Local reproduction uses Go1.26.1.
The exact failing command passed once; that alone is not accepted as proof. A deterministic
endpoint gate delivers the server CLOSE ACK but holds SendContext return: client Close succeeds,
then a valid next OPEN is rejected while the server still counts the completed stream. The
new test is RED on the unchanged implementation, proving a production lifetime/order defect,
not an Android-harness regression or a premature OPEN in the original test.
The correction waits only for already-terminal stream retirement or a removed stream's closing
worker before server admission; worker release now signals the same mutex-protected condition.
Live-stream quota exhaustion still returns stream_limit. No limit, wire protocol, retry policy,
sleep-only barrier, test skip or race removal. Source correction is not a deployed gateway change.
Focused acceptance PASS: exact failing subtest, all mixed-peer cases, full tcpforward -race,
reliablestream/familysession -race, and20 bounded repeated runs of the mixed-peer, forced ACK
ordering and closing-worker tests. Nine forced-order cases cover batching on either/both peers,
concurrent peer/bulk streams and shutdown; owned workers join, active/socket/pending counters and
retained bytes drain to0. Existing stream-limit/lease/FIFO tests pass with unchanged limits.
An initial supplemental worker stress fixture lacked the client Reset-completion boundary;
it was corrected with a condition-driven ActiveStreams=0 barrier, not a sleep or blind rerun.
**STOP_NEW_FULL_CI_FAILURE:** narrow correction4a7bf20b648e335fbdd9a8099916080f71741552
is pushed and remote-verified. Exactly one new Client builds run41285992226 was triggered;
41284629022 was not rerun. In the new run, scope/JVM control/carrier race/restricted readiness
PASS. Existing scope selection enables all platforms for shared carrier changes; no workflow
filter or mandatory gate was weakened. Linux job124787317664 completed FAILURE at Mandatory
desktop pytest: ValueError: Android smiley implementation changed, in desktop smiley/catalog
and packaging-entrypoint tests (4 failed,1208 passed,182 skipped,5 fixture errors).
Snapshot2026-11-01T07:48:31Z: overall workflow still in_progress, Android and Windows still
running; this is an observed failed mandatory job, not a claim that the workflow has completed.
Android native build was running; system consent, language/dashboard, emulator lifecycle and
ARM64 release packaging were NOT_REACHED at this snapshot, not PASS or FAIL. Diagnostics are
retained with exact run/source/job identity. No blind retry, additional CI trigger, unrelated
desktop repair, artifact acceptance, signing, publication or phone workflow after this stop.
Public108/Android sequence3, gateway catalog4, paid baseline108 and owner entitlement/ledger1/4/
cohort1/10 remain unchanged. Canary is not repeated. No qualified109 release or READY_FOR_COHORT_3.
No desktop release tag/publication is authorized; its publishing job is not Android qualification.

**1 November — beta109 UI repair authorized; source candidate, not distributed.**
Owner explicitly authorizes a new Android APK and update sequence4 after the current canary.
Candidate version is **0.1.18-beta109 / code109**; public, invitation and installed owner
version remain exact beta108, Android sequence3. Gateway catalog4 and paid baseline108 stay
unchanged. Do not install109 before final recovery and the owner's final108 Connect.
Additional source review reproduced a second UI cause: the terminal pane hid the entire
country/transport panel after failure, even with enabled controls. Stable failed/off states
now show route controls; cleanup-required shows disabled selectors and Disconnect. Active
connection/cleanup transitions retain the terminal. Error history remains available by tapping
the status label. Fail-closed ownership, authentication and cleanup-before-reconnect are retained.
Two JVM assertions reproduced the hidden-panel defect before the fix. Focused checks now PASS:
56 selected JVM tests and50 Python release/contract tests; one unrelated Windows check excluded.
Disposable-emulator acceptance now checks actual selector visibility/enabling, dial actions,
busy/cleanup states and a failed-state screenshot. Hosted build/lint/native/emulator acceptance,
offline signing, public readback and physical109 acceptance are PENDING, not PASS.
Rollout: accept exact CI artifact, verify source/manifest/native provenance, sign offline with
the existing signer, then publish immutable109 and optional Android sequence4 only after final108
canary recovery. Until publication, rollback is simply retaining public108; never overwrite an
APK or lower a signed sequence. Any later rollback retains device data and uses a higher sequence.
Final canary recovery and owner108 Connect/internet are verified below; earlier deviations remain.
Candidate109 remains unpublished; no backend restart, identity/invite/grant change, certificate
deletion or gateway publication.

### Authorized operational exception — NL-REPLACEMENT-20261030

**Beta109 CI follow-up:** candidatebe37c93 was pushed and remote-verified. Readiness
CI41280655230 failed an outdated source-location assertion: the accepted bootstrap helper,
not FriendsRestricted itself, now calls product.imported. Local reproduction found the same
single failure; the fixture now verifies delegation, synchronized product import, READY gating,
restart and authenticated ACK without weakening any production check.115 focused readiness/
HTTP tests PASS,4 optional cases skipped; no product/wire/auth change. Emulator coverage also
requires the visible status label to retain its history action. A new exact-source Android CI
candidate is required; the earlier pending run/artifact is not accepted for publication.

**Beta109 emulator qualification follow-up:** sourcee6817b5 is pushed/remote-verified;
readiness CI41281001187 PASS. Client CI41281001188 passed compilation/JVM/lint/native setup
and the new Friends dashboard visibility/history-action assertions, but overall acceptance
FAIL: the language recreation test expected Russian and observed the previous English text.
The downloaded diagnostics ZIP matches its GitHub digest. Test review finds that matching
English text could finish the first iteration before a new Activity resumed; the next language
change could overlap that pending recreation. The harness now requires a distinct, resumed,
non-finishing/non-destroyed Activity with the requested locale within15s. Production language,
VPN, authentication and release gates are unchanged; no retry-until-green or skipped assertion.
51 focused Python checks PASS; exact-source hosted emulator/native packaging is pending again.
No qualified release APK, signature, publication, installation or Android sequence4 yet.

**Beta109 system-consent harness checkpoint:** source1d9fb0c readiness CI41282459790 PASS;
client CI41282459786 FAIL at the debug Auto system-VPN consent test (no confirmation button
found), followed by retained-VPN/ownership failures. Friends language/dashboard and ARM64
release packaging did not run in this attempt. Both downloaded diagnostics and debug ZIPs
match GitHub SHA256. The available logcat capture contains boot output rather than the failure;
it does not establish why the dialog was absent. Do not label this a confirmed product fix.
The disposable test now wakes/unlocks the emulator and asserts that precondition before opening
the same system dialog; its test-only Activity keeps the display awake. Exact system package,
button, injected touch, revoke and cleanup assertions remain mandatory, with bounded monotonic
timeouts and screen/keyguard/window counters on failure. Logcat collection now tails main/system/
crash buffers rather than consuming the kernel boot prefix. No production permission, transport,
VPN lifecycle, paid baseline108 or gateway catalog4 change.52 focused Python tests PASS;
new exact-source hosted runtime/native/artifact acceptance is required, not waived or retried
blindly. Public/invitation remains108, sequence3;109 signing/publication/installation NOT_RUN.
Final108 owner recovery is verified; no canary operation is replayed for this CI checkpoint.

**1 November — current owner acceptance continuation (supersedes older pending-phone notes).**
`ANDROID107_WHITELIST_FIELD_ARCHANGELSK_PASS`: owner/tester reports real mobile-whitelist
operation on public107 in Arkhangelsk region. `ANDROID108_OWNER_INSTALL_RUNTIME_UI_PASS`:
owner reports an in-place108 installation, successful launch/runtime and visible server CPU
on the dashboard and country list. These are field reports, not notification-lifecycle or
separate108 AWG/TCP/Auto-MESH acceptance, universal installation or a physical108 whitelist test.
`ANDROID108_WHITELIST_TRANSPORT_EVIDENCE_INHERITED_FROM_107_UI_ONLY_DELTA`: reviewed
accepted107 source16c91fcc → public108 source3b10199; production changes are CPU presentation
and version metadata only; supporting changes are tests, CI diagnostics and publication/docs.
Carrier/Telemost/AWG/TCP/readiness/VPN lifecycle/JNI/trust/routing implementation is unchanged.
Verified-HTTPS APK manifest reads **0.1.18-beta108 / versionCode108**; exact SHA256, size,
signer and CI41243393838/source provenance PASS. Android update sequence3 retained.
Fresh03:44–03:47UTC read-only preflight PASS: RU API/SSH, catalog4 signature/new NL
185.10.158.212/unchanged RU entry, old NL FENCED, new AWG/TCP/Restricted active, current
profile/certificate/CRL/directory, CRL=floor27233, healthy renewal/read-only sync.
Existing OWNER_CANARY_1 binding retained; latest authenticated readiness ACK is exact108.
Paid subscriptions/events **0/0**, cohort **0/10**; canary **PAUSED / NOT_RUN**.
Current order under existing IDs: **ANDROID108 physical transport/cleanup acceptance →
NL_REPLACEMENT_LIVE → BETA0 baseline106→108 source/package/deployment → BETA-0-CANARY-1**.
**Owner timing correction / NL_REPLACEMENT_LIVE:** owner confirms all requested checks
were already completed successfully and explicitly asks to continue coding. Accept the
owner-reported beta108 NL AWG/TCP/Auto-MESH runtime and disconnect/cleanup smoke; do not
require another Connect to reproduce a session after the test has ended. Earlier passive
snapshots were later than the physical tests: absence of traffic is not a failed test.
No retrospective claim of an independently captured handshake, phone trace, per-stage
readiness trace or all notification lifecycle cases. Prior raw observations remain below.
New NL185.10.158.212/catalog4, old NL FENCED and FLEET_MESH_PROBE_1 retained; accepted
infrastructure is not rebuilt or replayed. Last readback paid0/0, cohort0/10, canary PAUSED.
**BETA-0-CANARY-1 live — explicit expiry and exact CRL COMMITTED on baseline108.**
Owner first reports failed connection/locked transport selector, then «подключился».
Record delayed connection recovery and a separate Android UX defect; internet verification is
not separately reported. Fresh authenticated108 import READY ACK at05:38:31UTC and two stage1
certificates expire exactly05:51:00UTC. First fresh ACK is151s after stage1 activation:
the90s server-proof gate is NOT_MET, not retrospectively marked PASS. No phone TLS trace claimed.
Explicit expire APPLIED at 2026-11-01T05:45:39+00:00: subscriptions/events1/3,
cohort1/10, version3, paid_allow=false; purpose internal_canary, amount0/revenue0.
Exact CRL27234 committed at 2026-11-01T05:48:36+00:00, floor27234, directory validation PASS.
One generation, one delivery; exact NL accepted payload matches the RU committed payload.
Three still-valid owner certificates are revoked, including the retained baseline certificate;
no certificate rows are manually deleted. No other device identity/invite/grant is edited.
Temporary forced-command credential removed on NL and private credential removed on RU;
maintenance configuration restored byte-exactly. Existing canonical locator/publisher retained.
Post-CRL180s backend observation PASS (202s): paid denied, latest exact108,
CRL=floor27234 and matching exact payload on RU/NL; registry57/111/2 retained. All three
revocations belong to this owner. Owner reports «не подключается» after the requested single
Disconnect/Connect: post-CRL reconnect denial confirmed as field evidence, not a phone trace.
Renewal/read-only-sync timers resumed at05:52UTC; active timers and successful worker status
confirmed. Temporary credentials removed; original maintenance configuration restored.
**Final30-day recovery APPLIED — owner beta108 Connect/internet and READY proof PASS.**
The existing time/certificate guard passed naturally; no certificate rows were deleted or
expiry values changed. Same OWNER_CANARY_1 binding, accepted baseline108 and sourceaccc4ff.
Activation at 2026-11-01T07:09:19+00:00; exact2592000s paid period ends 2026-12-01T07:09:19+00:00.
Subscriptions/events1/4, cohort1/10, version4, active/paid_allow=true; internal_canary,
amount0/revenue0. Exact private final capsule SHA256 `78ba99793d8779b83702e5478b38501ad17c61e6061fe274fb6e247caa5dc7e2`,
built twice byte-identically; unchanged HTTP candidate/trust/directory and latest108 prechecks PASS.
Only the final payment event was applied. No new CRL, gateway deployment, HTTP restart or
identity/invite/grant mutation. Earlier temporary credentials remain removed and normal schedules
were already resumed; the final activation does not pause them again.
**Final owner recovery verified:** owner reports «подключился работает» on beta108.
Fresh bound read-only evidence: challenge/fetch at07:10:42UTC, authenticated exact108 import
READY ACK at07:10:43UTC,84s after final activation (final90s gate PASS). Current material is
PRESENT_VALID, orchestrator usable, failure NONE, minimum CRL27235 after normal maintenance.
One new valid certificate expires09:52:11UTC, within the paid period ending1 December07:09:19UTC.
Readback at07:14:44UTC: active/paid_allow=true, ledger1/4, cohort1/10, registry57/111/2;
both normal timers active with successful workers, exact HTTP8e74997c… active/NRestarts0.
Temporary credential cleanup/configuration restoration remains the previously verified result;
no credential or schedule was reintroduced. No extra activation, CRL, restart or identity edit.
Canary sequence COMPLETED_WITH_DEVIATIONS, owner recovery PASS: earlier stage0/stage1
90s server-proof misses and the Android selector defect remain recorded, not a blanket PASS.
No additional phone TLS/DNS trace is claimed. The final108 prerequisite for authorized109
publication is met; exact-source CI/artifact/signing/public-readback gates still apply.
**Owner UI follow-up / unreleased source fix:** owner confirms transport selection returned
after Android Force stop/reopen, without clearing data/cache. This is workaround field evidence,
not a repaired installed108 or an AWG/TCP internet acceptance claim.
Refined source diagnosis: FAILED intentionally retains the fail-closed VPN guard until explicit
Disconnect; that retention is not itself a service bug. The UI incorrectly disabled route
selection and labelled the actual Disconnect action as Connect, with a pending animation.
Unreleased source now allows country/transport selection in FAILED through the existing
Disconnect → confirmed off → queued reconnect path. No replacement starts before service-owner
cleanup/release; busy/transitional/cleanup-required states still block route selection.
Primary and accessible dial actions now agree: failed/cleanup-required show Disconnect;
terminal failure stops the pending animation. Auth rejection and fail-closed policy are unchanged.
Regression evidence:2 contract tests reproduced the old defect;17 focused Python checks and55
fresh selected JVM tests PASS, including failed-cleanup/one-owner guards. JVM resource IDs come
from a test-only fixture generated from current XML; no APK, native build or device UI run.
Source-only push skips automatic build CI to honor the no-Android-rebuild instruction; release
CI and installed/UI acceptance remain NOT_RUN, not waived. Public/installed beta108, update3,
catalog4, paid ledger1/3/cohort1/10 and final-recovery time guard remain unchanged.

**Baseline108 production deployment PASS — READY_FOR_BETA0_CANARY_1.**
Latest readback 2026-11-01T04:59:14.654212+00:00; supersedes the two rolled-back attempts below.
Owner explicitly authorized one further candidate restart. Fresh separate private SQLite/
config/artifact backup and isolated restore/integrity/FK PASS; consumed reservations not reused.
Exact candidate HTTP8e74997c… from sourceaccc4ff is now serving; private bound canaryfa43f88d…
retained from the same source. Only paid_beta.py differs from pre-deploy44a6b50f…: current
route members, registration/chat-sync/publisher bytes and admission/config fingerprints preserved.
Effective/running ExecStart, candidate hash, service-user help and existing bound108 lookup PASS.
One controlled restart in this attempt; exact candidate process owns the listener, health PASS,
NRestarts0, rollback NOT_USED. Tested full process/listener/HTTP startup gate825f47b applied.
Real non-cohort verified-HTTPS challenge/fetch/native material validation PASS on baseline108;
CRL=floor27233, directory current, catalog4 signature and RU/new-NL endpoints PASS.
Registry/schema/identities/invites/grants preserved; no migration or non-cohort106/107 revocation.
Paid subscriptions/events0/0, cohort0/10; latest authenticated owner exact0.1.18-beta108/code108
and private bound read-only canary lookup PASS. Renewal/read-only sync active, last success.
No Android build/sign/release, update sequence3/catalog4 change, enrollment or MESH server probe.
Source483 + exact-package5 + startup111 focused tests retained PASS;21 optional cases skipped.
Exact pre-deploy rollback artifact retained; no database restore or paid schema deletion.
Prior two rollbacks remain historical evidence, not the current serving state. Total issued:
3 candidate restarts and2 rollback restarts across separately authorized attempts.
At deployment acceptance canary writes were NOT_RUN. Fresh owner ГОТОВ has now been
received; stage0 is APPLIED as recorded in the current live checkpoint above.

**Android108 public release evidence — 31 October (physical follow-up above).**
The dashboard and country list show explicitly labelled **Server CPU / CPU сервера**
when fresh CPU metrics exist but channel capacity is unknown. No link speed is invented;
CPU is not total/channel utilization. Known-capacity aggregate behavior stays unchanged,
and stale/missing measurements show No data rather than zero. RX/TX remain in the tooltip.
Hosted CI41243393838 at source3b10199 PASS, including actual emulator VPN/UI checks,
381 JVM tests/64 suites, lint and exact-source ARM64 packaging. Both synthetic CPU renders
were downloaded and visually checked.51 focused local tests PASS. Existing offline signer,
16K alignment and verified-HTTPS exact APK/source/catalog/invitation readbacks PASS.
Public updater and invitation now offer108; Android catalog sequence3, minimum1,
mandatory_after0. Updating needs Android consent: install in place without clearing data.
At publication physical108 runtime was NOT_RUN; the1 November owner report above supersedes it.
No phone debugging or reenrollment.
Gateway catalog4, server identities/admission and paid ledger are unchanged; canary PAUSED.

**NL-REPLACEMENT-20261030 / READY_FOR_OWNER_NL_SMOKE.**
Owner-executed Sprintbox console checks at11:52UTC confirm the RU host, synchronized clock,
database integrity, unchanged API/SSH processes and real local backend/proxy challenges PASS.
The diagnostic timeout is localized to journalctl, not the challenge endpoint. A bounded
kernel-ring follow-up at11:54UTC covers the last hour: no OOM, storage, conntrack-full or
lockup match. No service restart/reload, host reboot or product configuration change.
Three consecutive samples from each of operator and new NL at11:54–11:55UTC pass SSH,
verified TLS, real challenge and signed device-status; no504. Current control-plane gates
PASS. The earlier intermittent stall's root cause remains NOT_PROVEN, not declared repaired.
Catalog4/signature/new NL endpoint and unchanged RU entry are reconciled read-only at
11:55:13UTC. No republication or sequence5. Owner subsequently reports AWG/internet working;
owner now confirms the HTTPS egress address matches185.10.158.212 and reports Disconnect.
This is owner-reported AWG egress PASS; resource cleanup is not yet verified. TCP/Auto-MESH not run.
Earlier load diagnosis: fresh NL metrics were hidden by107 when channel capacity was
unknown. The108 publication now shows explicitly labelled CPU instead; channel capacity
remains unverified, with no invented speed or server-monitoring contract change.
Historical107 publication (superseded by108): Android107 was publicly distributed for Android12+/ARM64, following the owner's
explicit instruction to switch all users without phone debugging. Hosted CI41213595334
at source16c91fcc PASS:376 JVM tests/63 suites, lint, carrier race checks,43 executed
instrumentation cases (24 variant skips), real emulator VPN traffic/revoke/cleanup and
quiet foreground notification flags, plus final native/source-provenance packaging.
The downloaded CI APK was qualified, signed offline with the existing certificate,
and read back byte-for-byte over verified HTTPS. The earlier private unsigned107
candidate is not this release; public JNI was rebuilt by CI, not reused from that candidate.
At that publication the updater and invitation offered beta107; signed Android catalog sequence2,
minimum_supported_version1 and mandatory_after0. Installation still needs Android consent.
Exact Codec2 corresponding source/licenses are published alongside the APK.
Physical owner installation/runtime is NOT_RUN: owner explicitly authorized expedited
rollout after CI without ADB. No claim that every device has installed or that the phone's
repeated notification is resolved in the field. Update in place; do not clear data or reenroll.
Gateway catalog4, RU/NL identities, admission policy and paid ledger are not modified.
Canary stays PAUSED. Provider panel1000GB is a traffic quota, not Mbps; capacity remains unverified.

New NL **185.10.158.212** has accepted AWG/TCP and now real production-bound MESH
DNS/HTTPS/egress acceptance. Reused **FLEET_MESH_PROBE_1**; no second identity/invitation,
owner identity or paid event in that server probe. Probe retained non-revoked in encrypted custody.

Join cause: **PRE_CONNECT_OPERATOR_CONTROL_MISSING**. The relative operator-control
boundary was absent in the replacement service working directory. Restoring the exact
retained seven-file boundary fixed pre-Connect configuration rejection; gateway source,
binary, trust, signaling and service environment are unchanged. Direct Telemost join PASS,
then the sole full MESH retry PASS: registration, Family TLS, three DNS queries, four
verified HTTPS streams, new NL egress and bounded cleanup. Three stable samples, zero restarts.

Signed catalog **4** was published; initial authenticated NL readback returned the new endpoint,
RU entry and probe assignment remain unchanged. Actual Android catalog parser PASS without
APK update; Android106 owner AWG smoke is **IN_PROGRESS**, not completed by parser
acceptance. Owner-reported HTTPS egress now matches the new NL; cleanup is still unverified.
Prepared routing artifact and mailbox/monitoring target updates are deployed.
Fresh11:55:13UTC readback validates canonical profile/certificate/CRL, floor **27226**,
RU/NL directory equality and actual SSH snapshot. Renewal evaluates NOOP; no material refresh
is needed at that observation. Normal renewal/read-only sync timers are active/waiting,
last workers succeeded, controller COMMITTED and neither node has an active operation owner.
New NL remains active with integrated publisher rotation; no separate publisher timer.
Old NL remains **FENCED**. No rollback/catalog rewrite or RU reboot was attempted.
Paid ledger **0/0**, payments/revenue0, cohort0/10. **BETA-0-CANARY-1 PAUSED**;
paid-canary, subscription events and Android stage0 stay off. Complete the1 November108
AWG Connect/Disconnect and notification check, then TCP and Auto/MESH once each with cleanup.
A retained notification is a separate UX defect, not an automatic TCP/MESH smoke blocker.
No further gateway-catalog publication. Not NL_REPLACEMENT_LIVE until all owner gates PASS.

NEXT within this same operation: owner installs public108 in place without USB debugging,
checks visible server CPU and notification behavior, completes AWG cleanup, then tests TCP
and Auto/MESH with current readiness import/ACK. Public108 is not proof of installation.
No further Android or gateway-catalog publication is required for those checks.
Canary PAUSED; no new identity, PLAN ID, paid action or automatic queue advance.
Only complete server and owner gates permit NL_REPLACEMENT_LIVE.
[Current evidence and rollback](releases/2026-10-30-nl-gateway-replacement.md).
Earlier provider/network observations below are retained context, not the restoration path.

**ANDROID-CONTROLLED-BETA — единственный текущий critical path (owner decision27.10).**
**Historical canary pause/availability diagnosis — superseded by1 November gates above.**
At this earlier checkpoint the owner authorized availability restoration, not canary resumption.
Fresh09:11–09:16UTC comparison finds accepted snapshot/maintenance/gateway hashes,
renewal helper, launcher and base gateway unit unchanged. Paired header-only capture:
19 matching RU outbound SYNs, zero matching packets at NL; no capture drops. Reverse
NL→RU HTTPS connects, while new RU→NL SSH/HTTPS still time out. NL has no attached XDP
or tc ingress/egress filters in this readback. Blocking network hop remains unknown;
no evidence supports an application-code rollback. Recovery is blocked on RU→NL
connection establishment. No production changes/restarts; expired material retained,
not accepted or substituted. Provider network investigation is required; canary paused.
Post-provider boot readback30.10 08:55–09:04UTC: NL administrative SSH restored;
ordinary AWG/TCP, mailbox, Reticulum and monitoring units active. Memory29.19–31.12%,
load0.14–0.25, no swap; this short observation does not resolve the earlier memory rise.
Service recovery is PARTIAL: restricted gateway inactive/disabled, its listener absent;
canonical gateway certificate and CRL expired29.10 11:42:38UTC, directory expired13:04:25UTC.
Floor remains aligned27224; canonical boundary/configuration and accepted snapshot/gateway
artifact hashes retained. Actual RU-origin SSH snapshot times out; direct RU→NL TCP22/443
also time out while local→NL succeeds. Renewal timer waiting, last worker failed.
RU Friends HTTP dispatch responds as expected; paid ledger freshly0/0. No operator
restart, refresh, route/source change or canary action. No full VPN/client acceptance;
46 AWG peers loaded but no recent handshake/traffic in the bounded sample. Canary paused.
This fresh observation supersedes the earlier total-inaccessibility observations below.
Memory retrospective:1282 stored NL samples. Observed post-cutover28.10 median60.10%;
29.10 08:23–08:30UTC58.81–60.90%, rising to87.52% at08:42 and89.92% at09:03.
Metric uses MemAvailable, not merely free memory. Overnight and pre-failure gaps exist.
Per-process RSS/OOM evidence is absent; our application/background workload is not ruled
out. No process attribution or proven causal link to the separate boot panic yet.
Provider screenshot supplied29.10 now identifies a boot-time kernel panic:
VFS unable to mount root filesystem on unknown-block(0,0). This is provider evidence,
not a successful remote readback. Underlying cause and original pre-reboot stall remain
unknown; it does not prove lost data or implicate the application migration. No OS repair
performed. Need full boot log, attached-disk/initramfs/root-target checks and safe recovery.
Owner paused the canary29.10 and requested read-only NL diagnosis. No automatic resume.
NL IP responds, but SSH banner exchange times out from both local and RU vantage points.
Last successful monitor09:03:55UTC: RAM89.92%, disk50.42%; earlier load peak15.55.
Resource/IO stall is a hypothesis, not confirmed OOM or storage failure; console needed.
Owner subsequently requested availability recovery and reported pressing the provider
reboot control. Completion is unconfirmed:09:35–09:37UTC SSH still gives no banner;
ICMP3/3 and TCP22/443 were then reachable. Owner subsequently reported boot completion;
at09:40UTC TCP22/443 time out and ICMP0/3; RU also cannot reach SSH. OS/service startup
is unverified. Owner subsequently reported Running with an empty connected console,
and announced another reboot at10:06UTC. Seven bounded checks through10:09UTC show
no ICMP reply and TCP22/443 timeouts; RU independently confirms both port timeouts.
Reboot mode/completion and OS startup remain unverified. No further power action sent.
No canary resume or application/config change.
Prior live-entry preflight failure follows.
Owner decision29.10: former zero-certificate gate is
**SUPERSEDED_BY_PRODUCT_CONTRACT_REVIEW**. No wait for zero certificates before stage0.
Fresh09:14:18UTC binding/exact Android106/device-invite PASS, ledger0/0, cohort0/10;
baseline safe certificate token dc6b3aa3b462 retained unchanged as evidence.
Actual09:17:07UTC failure: existing forced-command SSH snapshot exits255 with banner
exchange timeout. Renewal timer active, worker not running, last result exit-code/1.
Direct administrative SSH also times out; cause not established. This is failure of
the already-required live route, not a new certificate/infrastructure/source gate.
Canonical migration acceptance retained; no redesign, reconciliation or restart.
Fresh backup/permit/activation NOT_RUN; no paid/readiness/Android/CRL writes.
Parameters fixed: natural600s, Connect90s, post-expiry120s, CRL phase900s,
post-CRL180s, final recovery2592000s; internal_canary/amount0/revenue0.
Future canary continuation requires owner resume first, then the listed minimal
preflight/backup and fresh ГОТОВ before stage0. No automatic repair or resume.
[Current canary evidence](releases/2026-10-27-android106-beta-0-canary-1.md).

**Accepted migration milestone at3996fa0 — READY_FOR_OWNER_LIVE / LIVE_CANARY_WRITES_NOT_RUN.**
PINNED_VENV_RUNTIME_PASS / SNAPSHOT_LAUNCHER_ACCOUNT_REHEARSAL_PASS /
CANONICAL_PROFILE_MIGRATED / RENEWAL_GATEWAY_SNAPSHOT_ALIGNED / CRL_FLOOR_ALIGNED.
Same checkpoint; previous rollback is historical and remains accepted.
Source fix5cc52f6bf967174bdfa34ba89436c4ad3b13ca60 pushed, remote SHA verified.
262 focused launcher/runtime/snapshot/canonical/package/authorization/parser/directory
checks PASS; retained coherent artifacts remain exact and unchanged fromc9c0a4d.
Real temporary-key SSH rehearsal PASS on a fresh secure non-authoritative copy;
cleanup PASS, original authorization bytes restored, removed key rejected.
Fresh private coordinated backups and a separate fresh canonical copy from current
live bytes verified. Only its floor changed27088→27219; CRL bytes/number unchanged.
Actual canonical snapshot PASS **before** the sole gateway restart, again afterward,
and after old-profile retirement. TLS/listener/publisher PASS; accepted renewal evaluate
NOOP with zero writes/promotions, including after retirement. Renewal timer active.
One authoritative canonical profile; all five profile routes and shared root-controlled
lock aligned. Publisher directory route/configuration unchanged, valid rotation accepted.
Old profile and rehearsal copy private/inactive; temporary credentials0.
New continuation budgets: rehearsal credential1/1, timer cycle1/1, offline floor1/1,
gateway cutover restart1/1, emergency rollback0/1. No automatic second cutover.
Final20:20:38UTC28.10: embedded CRL/floor27219, material headroom10170s;
ledger0/0, cohort0/10, owner certificates0, binding/exact Android106 unchanged.
No paid/readiness/Android/stage0 action, RU CRL/sequence mutation or Friends HTTP restart.
Historical NEXT at3996fa0 was owner ГОТОВ; that reply is now received.
The current live-entry certificate-horizon gate above supersedes that pending handoff.
[Canonical-profile receipt](releases/2026-10-28-android106-beta-0-canary-canonical-profile.json).

**Historical entry BETA-0-CANARY-1 — OWNER_CANARY_BOUND_READONLY /
BLOCKED_PROFILE_WRITER_CONFLICT / LIVE_WRITES_NOT_RUN.**
Read-only continuation from9205588 stopped at the required pre-source writer gate.
The active approved credential-renewal schedule reaches the existing root RPC;
its exact pinned NL node stages and atomically replaces the same live profile.
All13 deployed source-member hashes match controller/node pins. This is a legitimate
non-maintenance profile writer, not merely unused code. The running gateway also
references that profile. Moving only snapshot/maintenance would leave them detached
from the renewal-updated profile. Layout separability is not qualified; no source
redesign or package build. Shared publisher parent/group-write, directory, profile,
lock, snapshot route and services remain unchanged. No layout migration, backup,
permit, credential, maintenance operation, restart or canary action; budget0/1.
Fresh signed RU/NL CRL/sequence27216 already observed at entry; floor27088 remains.
No CRL generated by this checkpoint. Final material headroom13266s at readback;
ledger0/0, cohort0/10, owner certificates0, binding/exact106 retained. No-write PASS.
STOP. NEXT — separately authorize a coordinated profile-path/ownership design that
includes the existing renewal writer and gateway reader. Do not migrate only the
snapshot route, change renewal/publisher permissions or begin live canary automatically.
[Split-boundary receipt](releases/2026-10-28-android106-beta-0-canary-split-boundary.json).

**Historical read-only input — BETA-0-CANARY-1 / OWNER_CANARY_BOUND_READONLY /
BLOCKED_CRL_PROFILE_COMPATIBILITY / LIVE_WRITES_NOT_RUN.**
Dependency: CP2 accepted DONE / PAID-AWARE EMPTY-COHORT BACKEND SERVING, publisher
capability preserved, real payment/enrollment NOT_RUN. No CP2 redeployment/restart/
migration/source-package gates. Same ANDROID-CONTROLLED-BETA root, no CP3.
Scope: only OWNER_CANARY_1; planned permanent1/10 internal slot and9 customer slots.
No slot occupied/reserved in the backend yet. No substitute production identity.
Progress: purpose customer_payment/internal_canary in control-plane operational
metadata only; existing payments default customer, zero-value canary, immutable
purpose, separate counters and explicit UI/audit/admin receipt classification.
Local PG+synthetic-volume backup/disposable restore PASS; running console rebuilt,
migration0006 installed,50 bindings/3 old customer records/operations/prior audit and
credentials preserved.118 PostgreSQL console +76 affected backend tests PASS.
Source-only context permissions corrected for restrictive umask (2 tests).
Bounded HMAC-token-only canary wrapper and committed-source packaging implemented:
Normal four-stage path unchanged; emergency recover added only for versions1/2
after natural expiry with no valid certificate, exact30 days from permit.period_start
and execution window<=300s. Bounded dispatch permits server delay0..299s without
rebasing the payload; future/closed dispatch fails RECOVERY_DISPATCH_WINDOW_CLOSED.
Terminal reference_hash marker prohibits new operations
after recovery; identical backend-payload replay alone remains allowed.79 canary
tests PASS; existing backend remains sole authority. No new schema/CRL action or
generic Django production write. Source packaging is lookup_only; see report receipt.
Exact-payload CRL source gate complete: pure builder reused by publish_crl, immutable
private payload/request, one-generation journal, proven-NOT_SENT-only retry (max2
attempts), exact trusted gateway readback, post-acceptance commit/recovery A–E.
98 new tests PASS;206 existing restricted/sync/directory PASS with29 optional native
skips/4 native deselections.118 console/79 canary/76 backend/2 preparation PASS;
Django system/drift PASS. Unbound source package only, no transport/config/permit.
Those source gates performed no production lookup/registry access/mutation, Android
interaction, CRL or CP2 restart.
Read-only continuation from6dff337: exact lookup artifact verified; one owner lookup
and one bound status PASS. OWNER_CANARY_1=`dev_fa4f7e03ca04`, authenticated Android106
observation PASS; ledger0/0, cohort0/10. Private status-only artifact fromad086c0:
two byte-identical builds, permit=null,4 synthetic status/negative-guard checks PASS.
No valid owner certificates; CERTIFICATE_HORIZON_CLEAR. RU material validation PASS.
That initial parser observation is superseded by the read-only f499bdf provenance
review: NL_VALIDATOR_ONLY_DRIFT. Old auxiliary parser maximum3600s; actual forced
command maximum14400s, matching current directory/timestamp function hashes. Same
exact bytes/lifetime13401.739755428s PASS on actual gateway; no precision mismatch.
96 affected tests,48 synthetic parser and18 gateway/floor checks PASS; no correction
package built because runtime parser drift was not proven.
Separate live-entry blocker: the actual forced command is a read-only security snapshot
endpoint; incoming CRL payloads fail MAINTENANCE_TRANSACTION_REQUIRED. Embedded and RU
CRL27211 match, minimum_crl27088, guard=max(embedded,minimum). No next-payload/floor
update path is established on this command: CRL_FLOOR_UNRESOLVED, not accepted as
CRL_FLOOR_LAG_NONBLOCKING. This is a delivery-contract gap, not proven numeric corruption.
No lookup/status repeat or binding change. Owner certificates remain0, ledger0/0.
Local read-only monitoring active/fresh, NL registry UNAVAILABLE, production writes
disabled. Protected ledger/identity/policy, owner certificate/readiness scope and
service/material/profile state unchanged; concurrent unrelated certificate/readiness/
chat activity disclosed, no whole-DB equality claim. Materials exceed720s at readback.
Completion gate: exact authorized-device binding; live activation/paid certificate
boundary/MESH Connect; natural expiry and new challenge/fetch/reconnect denial;
active-session behavior; CRL generation/propagation; recovery/reconciliation and
reactivation on the same identity; Android state preservation. All live stages NOT_RUN.
Emergency recovery source gate complete; binding is read-only, paid/live acceptance
remains NOT_RUN. Historical review proposed bounded maintenance/delivery and
floor-contract reconciliation. Source is ready; production continuation is blocked by
the fresh preflight above. Preserve the snapshot. Do not
enable generic writes or substitute the old mutating archive. No repair, refresh,
phone opening/Connect or request for ГОТОВ while live entry is blocked. No bound
write permit, canary write credential or CRL transport is installed.
Final same-identity30-day active
recovery is a future live gate, not synthetic acceptance transferred to the phone.
[Bounded checkpoint](releases/2026-10-27-android106-beta-0-canary-1.md).

**Accepted input CONTROL-PLANE-2 — DONE / PAID-AWARE EMPTY-COHORT BACKEND SERVING.**
Dependency: accepted CONTROL-PLANE-1 at21dd8d72ad5505cd82631856083694729d292c8b.
Gate: exact paid-aware bundle; read-only preflight; consistent private backup/recovery;
existing paid schema PRESENT_EMPTY, no repeat migration; guarded Friends restart;
unchanged non-cohort access;
read-only local bridge/continuous collection; synthetic production-identical expiry/
revoke/CRL/recovery. No real subscriptions/events, client/gateway changes or public console.
Current continuation from90ad148: typed D-Bus observer53 +existing ExecStart8 tests
PASS,9 private runner-flow tests PASS. Live empty/nonempty jobs readback confirmed.
Fresh20:09 preflight/PRESENT_EMPTY backupff9d0c50…/isolated restore PASS. Own drop-in,
effective full argv guard and one actual rollout restart PASS at20:10:09UTC.
New PID486622/NRestarts0 serves exact HTTPdcd76998…; three post-start observations
plus independent listener/health/inventory/empty-cohort readback PASS. Critical
registry/admission/publisher fingerprints unchanged. Consumed1 rollout/0 emergency;
no second candidate restart. Pre-start harness stop spent no restart; historical
receipts preserved. No migration, rebuild, real paid/client/gateway mutation.
Historical NEXT was CP2 rollout review; the owner has accepted it. Live paid
CRL/session/recovery acceptance remains open under the canary gate, not a CP2 retry.
Previous attempt evidence: exact publisher-preserving bundle6ea4ef3a…/source8b4177d unchanged;
fresh baseline/empty-schema/NTP gate and backup643fe650…/isolated restore PASS.
New ordered drop-in selected exact candidate; effective ExecStart guard PASS.
Subsequent pre-start observation raised JSONDecodeError; no restart requested.
Only own drop-in removed; independent final readback confirms original unit/PID,
healthy old runtime21d64558…, paid rows/events0 and unchanged non-cohort/publisher
fingerprints. That attempt consumed0/0; the owner now permits the continuation above.
8 guard tests rerun PASS,192 prior acceptance retained. Historical evidence
preserved, no migration/rebuild/client/gateway/real paid mutation. Live CRL/session
acceptance remains open. Stale Linux active blocks removed, no desktop task resumed.
[Exact evidence and finite next gate](releases/2026-10-27-android106-control-plane-2.md).

**Принятый вход CONTROL-PLANE-1 — DONE / LOCAL SYNTHETIC + PRODUCTION-READONLY.**
Dependency: accepted CONTROL-PLANE-0 at `a948d2328b5bd419b7d88be04b719c1dc6e16646`.
Gate: русский Admin/UI; 50 synthetic identities без изменения paid cap10/authority;
раздельный production-readonly inventory/fleet snapshots; technical telemetry models,
charts/filters/drill-down с явными unknown/stale boundaries; no production writes.
Gate met:95 PostgreSQL console +76 existing backend tests PASS, Chromium desktop/mobile
PASS. RU54 устройств наблюдались; NL registry недоступен; server stats read-only.
Client production telemetry/continuous alerts не собираются; production deployment,
real payments/enrollment NOT_RUN. Android106/backend/catalog unchanged.
[Checkpoint](releases/2026-10-27-android106-control-plane-1.md),
[runbook](../control_plane/README.md). Не новый PLAN root и не paid launch acceptance.

**Принятый вход CONTROL-PLANE-0: DONE / LOCAL SYNTHETIC ONLY.** Dependency —
accepted PAID-ENTITLEMENT-MVP at `ac90a2ac2f9e053b367bc3f7dde1711e94fd24a6`.
Django/PostgreSQL console, not a new product/PLAN root. Source of truth remains
Friends registry/paid_beta; no subscription ORM/state-machine duplication.
Completion gate: local Compose/PostgreSQL + customized Admin/dashboard/charts,
device lookup/readbacks, immutable intent/preview/confirm/reconcile, payment/cohort/
incident/audit/release metadata; actual synthetic backend integration, permission/
CSRF/concurrency/uncertainty tests and visual QA. Gate met:57 console+76 backend
PASS, desktop/mobile browser5 synthetic operations PASS. Production registry,
deployment, real payment/enrollment NOT_RUN; Android106/client/catalog unchanged.
[Checkpoint](releases/2026-10-27-android106-control-plane-0.md),
[local runbook](../control_plane/README.md). This is local implementation acceptance,
not approval of live billing or production console security.

Preparation и **PAID-ENTITLEMENT-MVP source checkpoint DONE** (originally NOT_DEPLOYED;
now CP2 DEPLOYED_EMPTY_COHORT);
controlled paid launch **BLOCKED** только на фактических Beta-0 gates в
[MVP report](releases/2026-10-27-android106-paid-entitlement-mvp.md).
Dependencies: exact accepted signed106/reference, owner-accepted
**ANDROID106-MESH-FIELD-1 PASS**, read-only canonical activation/admission lookup.
Положительный field result: real external user/whitelist network/ordinary app/MESH;
не Windows/Linux PASS. Desktop parity не prerequisite Android beta.

Exact106 APK manifest/signature/source inventory verified; one accepted hash,
unsigned106 builds не кандидаты.49 locked backend +20 JVM tests PASS; synthetic
vault/identity reload×3 не заменяет full installed APK upgrade и три запуска.
Новый authenticated106 READY ACK отделён от stale support84; production device
не менялся. Никаких Android source changes/rebuild/signing/publication автоматически.

Owner Beta-0 scope: максимум10 existing activated Friends devices, new106 installs
или already106, exact accepted APK без rebuild; older-version users исключены.
Private verified handoff, manual payments/operator events; external acquiring API
и older-version upgrade не Beta-0 prerequisites (не PASS). Новый top-level ID нет.

Bounded PAID-ENTITLEMENT-MVP: отдельные мигрируемые subscription/event tables,
atomic paid opt-in/cap10/idempotency, server effective state и private operator CLI
DONE. Non-cohort admission unchanged; paid state rechecked challenge/fetch,
certificate/readiness capped by entitlement/material expiry.243 targeted PASS,
10 nginx skips/8 external-integration deselections; no general CI claim. No live
migration/deployment/payment/cohort mutation, no Android source/APK/wire changes.
[Runbook](paid-beta.md) separates private receipts/operator attestation from remote
signer proof and documents existing-cache/CRL revocation bounds.

Completion gate: applicable14 launch rows under Beta-0 scope need exact evidence.
Remaining: review CP2 deployed-empty-cohort evidence and live paid CRL/session/
recovery acceptance (retained synthetic tests are not live acceptance); approved
private handoff/opt-in roster/operator, legal/subscription text, monitoring/stop
ownership. Source tests do not prove live paid enforcement. No pre-paid backend
rollback with nonempty cohort; saved105 does not authorize downgrade/uninstall/
reset. Public updater60/catalog unchanged; no launch or payment collection yet.

**Linux L04.2 PAUSED / NON-BLOCKING DESKTOP ENGINEERING, не DONE.**
R3 SOURCE GATE DONE/review accepted; .11 CONSTRUCTION DONE/frozen internal candidate,
exact0.2.12~l03.2.11/candidate570a5515…/system34b27cb9… read-only. Source/native/
system/reference/46 tests/embedded equality PASS; inner exit0, outer exit1 только
root-owned `embedded.json` collision. Installed package/live P0/P1/Auto NOT_RUN;
product defect не установлен, overall CI PASS нет. Collision — existing D02/CI
debt, не Android launch blocker. Linux installed acceptance только отдельным
потоком после controlled beta; не повторять harness, не переименовывать receipt,
не чинить launcher, не rebuild/install/rollback, не использовать retained identity,
не запускать P0/P1/Auto/AppImage lifecycle/L05/L06 и не публиковать Linux artifacts.

**STOP. NEXT — закрыть только фактические Android controlled-beta launch blockers.**
Следующий конечный этап — production read-only owner lookup/binding в BETA-0-CANARY-1,
не автоматически. CRL helper source gate завершён, пакет только unbound.
Live procedure не начинать до owner ГОТОВ.
Только OWNER_CANARY_1; customer payments/
enrollment не разрешены. Ни одного live canary stage пока не выполнено. CP2 принят,
бюджет consumed1 rollout/0 emergency; его deployment/migration/restart/gates не повторять.
Terminal scripts не запускать, paid schema не удалять. Read-only monitoring продолжается.
Новый top-level PLAN ID и CONTROL-PLANE-3 не создаются.

### Предыдущие priority/ops records — исторические, не активные NEXT

Ни один сохранённый ниже Linux NEXT не переопределяет owner decision27.10.

**Текущий bounded task — L04.2; R3 PARTIAL / PACKAGE_GATE_FAILED (environment harness finalization).**
R2 FINAL PARTIAL / READINESS_CAUSE_UNRESOLVED accepted; original typed fetch
cause was masked by expired cache. Live .10 Connect is prohibited. R3 adds no
new top-level ID. Required sequence: deterministic old-red → exact-error and
bounded-cooldown source correction → complete source gate → new matching system
and internal .11/package gates → one corrected P0; P1/Auto/lifecycle/AppImage only
after preceding PASS. First new affected/package/live failure stops progression.
Exact Go race/native15/combined3/MESH157/cleanup32/desktop1317+82skip PASS.
Source2d125137 review accepted in affected scope; runtime/tests/locks unchanged.
Gson and missing Go-cache failures reviewed as environment-only. Retained
Gradle171/classpath/JAR/javap PASS, no Gradle replay. Offline cache closure PASS;
one authorized Android/Python selection143 PASS. Bounded readiness workflow paths
committed e93bf7d; canonical run40491350035 SUCCESS. Raw full suite remains FAIL:55 FAIL/3373 PASS/105 SKIP/0 ERROR; no overall CI PASS.
Review normalization: common35 + local-only1 + fixture-absent19 = exact union55,
new/missing IDs relative to union0. ENVIRONMENT_FIXTURE_INPUT_ABSENT19 is existing
D02.1-R/CI debt, not a product regression. After separating it, exact accepted
local36 remains. Union55 is NOT a newly adopted permanent baseline. Full suite
will not be rerun; no historical capsules fabricated, tests suppressed or changed.
Source gate DONE/review accepted; continue new native/system, bounded reference
advancement and internal .11 package gates, then one corrected P0 only after PASS.
New native/system34b27cb9 construction/readback and reference gates PASS;
reference/candidate tests46 PASS. .11 candidate570a5515/system34b27cb9 built and sealed, source_dirty=false;
embedded candidate/system equality PASS/container exit0; launcher exit1 on
root-owned receipt overwrite (ENVIRONMENT_HARNESS_FINALIZATION). No product defect
established; no replay/harness patch. Remaining installed package/live gates
NOT_RUN. Containers removed; .10/.11/READY/protected seven byte-identical. R1/R2 primary/
cleanup/containment/drain semantics unchanged. Exact sealed .10 candidate remains
4264406722f6dd3efb83e9d9666e67180ce4f950333bb3e711bcbb4f5068b55a,
sourceb8e9196/system8ab7f298; Phase B/setup/GUI authorization retained.
No server/material/policy changes, manual fetch/cache deletion, owner-workstation
use, messages, voice acceptance, signing or publication. Relay probe correlation
gap is L06 observability debt, not a reason to expand RNS/public protocols here.
[Current R3 report](releases/2026-10-27-linux-readiness-cause-preservation-l04-2-r3.md).
L04 IN_PROGRESS; L05 NOT_RUN/delivery_unavailable backlog; L06/L07/L08 queued.
**STOP. NEXT — review L04.2-R3 package-harness finalization.**

**OWNER-CHAT-UX-2-INSTALL — PARTIAL / owner-use accepted.** По owner review exact
0.2.12~l03.2.9 установлен, candidate/package/system PASS, одно main window/embedded
chat, один ChatClient/D-Bus owner. Две unknown queue events исключены из acceptance
evidence, product defect не установлен. Не продолжать этот task; owner workstation
не использовался для L04.2, дополнительных messages/smiley/composer/visual checks нет.
Это не full L05 и не publication PASS.

[CHAT-UX-2](releases/2026-10-26-chat-ux-2.md) source/package DONE; .9/sourcecb81cd5/
candidate6f312d1e…/system43266d97… immutable. Прежние local3353 PASS/36 FAIL/101 SKIP/
1 FD teardown ERROR и CI full54/54/53 FAIL не скрыты; overall full-suite PASS нет.
CHAT-UX-1 product design superseded; historical evidence .7/.8 сохранено.

### Предыдущий compatibility checkpoint — не активный NEXT

**U2604-COMPAT — CHECKPOINT PASS в compatibility scope.**
LOCAL-OWNER-UPGRADE **BLOCKED на ABI**: Ubuntu26.04/Python3.14.4 не поддерживается
frozen .5/Python3.12. Workstation/launchers/private state unchanged.
Read-only source probe в disposable Ubuntu26.04.1/systemd259/Python3.14.4 **PASS**:
exact locks, RECORD630/strict imports17 distributions, platform libraries и129 tests.
Отдельный exact internal .7: candidate c79b4feb…/source3df82b4/system43266d97…;
packaging/runtime metadata/tests only. DEB/AppImage/imports/pkexec/READY, rollback,
tamper/locks/state, native/Auto/DIRECT и AWG/TCP prestart gates PASS.
Full desktop1199/83/0; full suite3257 PASS/55 FAIL/104 SKIP, без suppression;
отдельный technical debt, не общий CI PASS. Старые .5 hashes/IDs immutable.
[Report](releases/2026-10-26-linux-ubuntu2604-python314-compat.md).
L04.1 DONE сохраняется; L04 только L04.2. Publication/L04.2/L05/teardown/live VPN NOT_RUN.
Исторический STOP сохранён в U2604-COMPAT report; установленная .7 подтверждена выше.

### Frozen baseline — не текущая задача

**L04.1-LIVE-2 DONE / review accepted; L04.1 DONE в installed Linux AWG/TCP scope.**
Review принимает E/F1/F2; принятые P1/P2/A–D и клиентский F2 не повторять.
Exact **0.2.12~l03.2.5** frozen как **Linux AWG/TCP Beta candidate**, internal/unpublished;
candidate/source/system и artifact bytes неизменны. Signing/publication NOT_RUN.
Registry restart во время F2 — отдельное operational observation: первый readback
FAIL сохранён, uninterrupted continuity **NOT_PROVEN**, причина неизвестна,
assignment/configuration не изменились. Это не новый client defect или задача R3.
Parent **L04 IN_PROGRESS только из-за L04.2**. L04.2/L05/device teardown **NOT_RUN**.
Full-suite residual54/54/54 failures остаются отдельным техническим долгом; не общий CI PASS.
[Final installed report](releases/2026-10-25-linux-installed-awg-tcp-l04-1-final.md),
[единственный beta-freeze manifest](releases/2026-10-25-linux-awg-tcp-beta-freeze.json).
**STOP. NEXT — решение владельца о signing и ограниченной публикации Linux AWG/TCP Beta.**
Никакого автоматического L04.2/L05/teardown, F2 replay, R3, rebuild или публикации.

### Исторические checkpoints — не текущие статусы или NEXT

**L04.1-LIVE-2-R2 DONE / review accepted (source/package).**
Review exact .4: P1/P2/B1/B2/C1/C2/D PASS, E FAIL/review accepted, F1/F2 NOT_RUN.
Normal queued Connect/Close: deterministic overlay4 FAIL → targeted197 PASS.
Новый .5/source1c2beb6/candidate f0ee1760…: exact offline systemd255 DEB/AppImage
package/integrity PASS; system8d7d78ec… byte/contract verified unchanged, .4 immutable.
Full desktop1191/84; Linux/AWG/TCP/package CI PASS, isolated root→UID/Auto/DIRECT
и combined/lifetime PASS. Full CI54/54/54 failures: Docker readiness-receipt assertion
дополнительно к historical53, без исправления/повтора; общего CI PASS нет.
В самом R2 private identity/gateway/live E/F не использовались; последующий live
checkpoint указан выше. L04.1 IN_PROGRESS; L04.2/L05/teardown NOT_RUN.
[Source/package report](releases/2026-10-25-linux-queued-connect-close-l04-1-live-2-r2.md).

Цель — тот же Family Connect на Linux/Windows, что принятая Android beta106-recovery,
а не отдельные реализации продукта. [Текущий срез](STATUS.md) — источник текущего состояния.
Продуктовый checkpoint: phase22, source baseline `664342a6566792a4ea621274a369bcd6b6012143`.
D00 — организация документации; следующие строки являются очередью, не разрешением на автозапуск.
L03.1/L03.2 **DONE (review accepted)**; parent **L03 DONE** в scope полного
внутреннего Linux-кандидата. Исторически **L04.1-LIVE-2: PARTIAL / review accepted**, STOP на B1.
**L04.1-LIVE-2-RESUME PARTIAL / review accepted**, тот же ID; STOP на первом новом дефекте E.
P1/P2 continuity, B2, C1/C2 unavailable и D channel-loss/recovery PASS.
Queued Connect не отменяется при Close: busy/open, Future queued; helper/TUN0,
generation0/null. Только безопасный fixture cleanup; F1/F2 NOT_RUN.
Exact .4 A/B1 review accepted, не повторялись. Три stable pre-action reads,
структурный firewall/readback/state PASS; KVM/secret copies уничтожены.
Product/candidate и original FC-3YSQ-BE2D/nl сохранены. Review E принят;
R2 correction принят; текущий installed итог и единственный NEXT указаны выше.
L04.1 IN_PROGRESS, L04.2/L05/teardown NOT_RUN.
**L04.1-LIVE-2-R1 DONE / review accepted (source/system/package).**
Final internal0.2.12~l03.2.4/source053c4e5/candidate42ea0699…/system8d7d78ec…,
authorization2; .3 — immutable intermediate. Actual AWG/TCP up1/start0,
IDLE/generation2/pending null/poll PASS; unknown outcome fail-closed, первая
diagnostic category сохраняется через recovery. Exact system/package/rollback/
coherence/actual old-build refusal PASS; desktop1195/96. Linux/AWG/TCP/package CI
PASS; native/DIRECT initial FAIL, один unchanged rerun PASS (оба receipt сохранены).
Full CI54/54/53 failures, общего CI PASS нет. В самом R1 live B1/B2–F NOT_RUN;
private state/gateway не тронуты; последующий installed RESUME указан выше.
LIVE-1 PARTIAL принят review; final-2 retired для завершения L04.1, прежние PASS
сохраняются только за этим exact build. Red actual backend/GTK race подтверждён;
generation-fenced unlocked poll и queued Disconnect cancellation: адресные229 PASS.
Source57f8eff, internal0.2.12~l03.2.2/candidate d9c0d07f…; unchanged build-9.
Desktop1121 PASS/85 SKIP, integrity и оба systemd255/pkexec package gates PASS;
Client Linux/AWG/TCP/native/root→UID/Auto/DIRECT/package CI PASS;
control/phase0/Docker54/54/53 failures и voice FAILURE сохранены.
L04.1-LIVE-1-R **DONE / review accepted** в source/package scope.
[Correction report](releases/2026-10-25-linux-poll-disconnect-l04-1-live-1-r.md).
Новый exact candidate установлен в новой KVM Ubuntu24.04/systemd255:
DEB/setup/AWG/TCP/HTTPS/64KiB↓/↑/single Disconnect PASS. Original AppImage
close/reopen → один Disconnect PASS; поздние polls25s не возвращают CONNECTED.
Review принимает fresh nonce DNS на actual TUN с matching request/reply после flush:
валидный terminal positive/NXDOMAIN/NODATA contract, не только exit0.
RETEST **DONE / review accepted**, positive installed AWG/TCP gate завершён.
Network/DNS/IP cleanup и state preservation PASS; предыдущий guest уничтожен.
[RETEST evidence](releases/2026-10-25-linux-installed-awg-tcp-l04-1-retest.md).
AUTH/PROVISION **DONE, review accepted**; существующая FC-3YSQ-BE2D/nl, без новых
identity/invite/assignment. Parents **L04/L04.1 IN_PROGRESS**; LIVE-2 PARTIAL, L04.2 NOT_RUN.
Exact final-2 source `cf66532`, candidate `9d4b13cc…`, AppImage/DEB0.2.12~l03.2.1
не пересобраны: real KVM Ubuntu24.04/systemd255, DEB/pkexec/READY, AWG×3/TCP×1,
DNS/HTTPS/transfers, handoff/cleanup PASS. AppImage AWG/traffic/single-owner PASS;
после confirmed GUI close/reopen Disconnect отказал на connection-operation lock.
Это first-failure STOP, не полный LIVE-1 PASS. Cleanup-only после освобождения lock
восстановил baseline; guest уничтожен, исходный state/cache/floors/receipt сохранены.
[Отчёт LIVE-1](releases/2026-10-25-linux-installed-awg-tcp-l04-1-live-1.md).
LIVE-2: A actual installed tamper/reinstall PASS; B1 root lock не допускает transport,
но helper up1 и pending/APPLYING остаются после освобождения lock (generation0→1).
Network/state сохранены; pending не очищен вручную, guest уничтожен. B2–F NOT_RUN
по first-failure STOP. Никакого rebuild/source fix; [отчёт](releases/2026-10-25-linux-installed-awg-tcp-l04-1-live-2.md).
Исторический first-failure STOP; continuation exact .4 принимает P1/P2/B1/B2/C1/C2/D.
E FAIL/review accepted; F1/F2 и device teardown NOT_RUN. NEXT только review R2.
**L01/L01-R review принят в Linux source/native/root→UID/isolated-kernel scope. Review L02.2 принят: локальный критерий L02 authenticated OFF→ON→OFF через Manual и Auto/MESH выполнен. L02.1-R atomic RetainChat/terminal recovery и L02.1-R2 status classification приняты. D01.3/D01.3-R приняты в public completion/admission scope. L03.1/L03.2 и parent L03 приняты; correction L04.1-LIVE-1-R и RETEST приняты, NEXT только review LIVE-2-R2. Review D03/D04/D05, D02.1 collection/import isolation и D02.2 public-reference принят.
Review D02.1-R и fleet-документации `1725656` принят;
D02.1-R остаётся PARTIAL/NOT_RUN; D01 открыт. Дальнейшие L04.2/L05 и Windows задачи не начинаются.**

Порядок по умолчанию: D01.1 → D01.2 → D02.1 / принятый review D02.1-R → D02.2 / review → D03 → D04 → D05 → Linux → Windows → R01.
Зависимости в таблицах — необходимые результаты, а не требование заново выполнять завершённые фазы.
Каждый ID — отдельный ограниченный пользовательский результат, отдельные проверки и commit/push.
`DONE` = выполнен указанный критерий, `NEXT` = ещё не начат, `QUEUED` = не начат как отдельная задача.
Это не означает отсутствия всего кода в QUEUED: существующие части переиспользуются и проверяются.
Отсутствие физической ОС не закрывает её gate и не блокирует доступную другую ОС;
фиксировать точный NOT_RUN и короткую инструкцию, согласовывая следующий ограниченный шаг.

## Подготовка и известный дефект

| ID | Результат | Зависимость | Статус | Критерий завершения |
|---|---|---|---|---|
| ANDROID-CONTROLLED-BETA | Controlled paid Android beta readiness | exact signed109/source600ae52; full CI41289980872 PASS; existing bound owner | BETA109 TARGETED OWNER CHECKS PASS / SERVER TX RETAINED / COHORT HELD | [Current receipt](releases/2026-10-30-nl-gateway-replacement.md#android109-general-publication--1-november): install/data/CPU/selector/reopen, Auto→AWG Internet and owner Disconnect cleanup PASS; bounded RX0/no new handshake, server TX persists. Full server cleanup/MESH109/exact tap-to-READY not proven; paid canary remains COMPLETED_WITH_DEVIATIONS. Paid baseline108/cohort1/10 unchanged; baseline promotion and [launch gates](releases/2026-10-27-android106-controlled-beta-readiness.md#minimal-controlled-launch-gate), including legal/explicit opt-in/monitoring/stop ownership, remain separate; no automatic enrollment/deployment. |
| CHAT-UX-1 | Первый продуктовый desktop messenger UX checkpoint | explicit owner request; installed Ubuntu26.04 .7; штатный prepare-chat | IMPLEMENTED / REVIEW; validation PARTIAL | [Report](releases/2026-10-26-chat-ux-1.md). Одно GTK окно/ChatClient, adaptive dialogs/bubbles, fixed4096-byte composer/native emoji, bounded onboarding; backend unchanged. GTK27, desktop1226, exact package/AWG/TCP/integrity/12 screenshots PASS; mandatory full57 FAIL unsuppressed, no overall acceptance PASS. Built .8 sourceb094595/candidate0bf09cee…, system43266d97… unchanged; owner install/publication/L04.2/full L05 NOT_RUN. STOP for review. |
| U2604-COMPAT | Отдельный Ubuntu26.04/CPython3.14 source/system/package candidate | exact lock compatibility probe; explicit owner request; frozen .5 immutable | CHECKPOINT PASS (compatibility scope; review pending) | [Report](releases/2026-10-26-linux-ubuntu2604-python314-compat.md). Exact .7 candidate c79b4feb…/system43266d97…, manifests [3,14], imports/DEB/AppImage/pkexec/READY/rollback/tamper/barriers/state PASS. Full suites executed unsuppressed: local3257/55/104; general CI not PASS, residual debt retained. No workstation/private identity/gateway/live VPN. STOP for review. |
| LOCAL-OWNER-UPGRADE | Установка совместимого candidate на workstation владельца | отдельный review U2604-COMPAT и разрешение владельца | Исторический ABI blocker .5; установленная .7 теперь read-only verified | CHAT-UX-1 подтверждает только installed .7 manifest/dpkg и owner context prepare-chat, не воспроизводит acceptance/upgrade. Новая .8 владельцу NOT_RUN; сначала review CHAT-UX-1. Остальные installed checks не объявлены выполненными и не запускаются автоматически. |
| D00 | Компактное состояние и последовательный план | phase22 / baseline | DONE | Новый сеанс читает STATUS + выбранный ID; история сохранена побайтно, ссылки и diff проверены; commit/push с remote SHA отражён в итоговом ответе. |
| D01 | Зависимости Linux/desktop CI | D00 | IN_PROGRESS | Dependency gates D01.1/D01.2 отдельно от общей CI-приёмки; закрытие требует полного PASS обязательных suites после устранения остаточных blockers, без скрытия тестов. |
| D01.1 | Client builds/linux, AmneziaWG pilot, TCP pilot | D00 | PARTIAL | Dependency gates `26f71d6` приняты review; реальные Python3.12 imports/адресные CI PASS. Полный desktop FAIL: RNS capsule, AWG Auto lifecycle assertion; PARTIAL сохранён. |
| D01.2 | Linux control, phase0, Dockerfile.control test-stage | принята dependency-часть D01.1 | PARTIAL | На pushed `07b52e3` Python3.13 imports/адресные gates PASS ×3; Docker root 22 passed. Каждый full suite: 9 owner_handoff/prepare collection errors, exit 2 (D02); обязательные gates сохранены. |
| D01.3 | Public chat probe/prepare completion и следующий admission | L02.2/local L02 review принят; D03/D04/D05, L01/L01-R сохранены | DONE (review D01.3-R accepted; public completion/admission) | [Отчёт](releases/2026-10-24-desktop-chat-admission-d01-3.md): actual Host/ServiceHost/ChatBridge и Unix IPC, event-barrier red2/green; EOF после cleanup сериализован с admission, bounded client wait без open/HTTP retry. Public4/native caps и drain/accounting сохранены. 266 адресных + финальные24, прежние15/combined3/root→UID PASS. Production `23e3c5513ab9c37e919f228066c0e23f733a997e`: Client Linux и isolated gates PASS. Финальный test source `f258c17007102634fead9894bcfe9a82f6db44cf`: mandatory desktop pytest 40132223364/120986275264 PASS; общий D01 открыт. |
| D01.3-R | DIRECT close/active removal под admission lock | D01.3 accepted subset; без переработки native | DONE (review accepted; bounded scope) | [Отчёт](releases/2026-10-24-desktop-chat-direct-completion-d01-3-r.md): actual DirectHost/DirectBridge/Authority и Unix IPC, post-close/EOF barrier; red1/green30, зависимые326/root→UID13 PASS. Production `050f06baef8b94e81d1bd4becb7f4fc38d1a6744`; final barrier5 PASS/red1 на old-host overlay. Final source `b910edbd108fc5e146792b6db966d6f8daf53b1a`: mandatory Client Linux desktop pytest и весь linux job40134155274/120992056110 PASS; isolated-linux15/combined3/root→UID/Auto/DIRECT/race PASS. Full suites54 failures отдельно, не общий CI PASS. Review принят; разрешён только L03.1. |
| D02 | Сбор и импорты исследовательских fixtures | dependency-части D01.1/D01.2 приняты | IN_PROGRESS | Review D02.1 collection/import isolation и D02.2 принят; зависимости D03 готовы. D02.1-R PARTIAL/NOT_RUN. Не ждёт полного зелёного CI, который сам должен разблокировать; общая CI-приёмка D01 остаётся отдельным gate. |
| D02.1 | Девять collection errors, историческая overlay-suite, изоляция импортов | окружения D01.1/D01.2 готовы | DONE (collection/import isolation) | Review подтвердил границы; `6a0a982`: clean collection 2996/0 errors, helpers/import/runner 75 PASS; три CI full suites с 56 residual failures. Историческая воспроизводимость отдельно в D02.1-R. |
| D02.1-R | Комплектность исторического runner | review D02.1 | PARTIAL | Коррекция принята review. Vector/original API, явные retained inputs, preflight до pytest; 110 адресных PASS. Historical suite NOT_RUN: нет anchored pins delivery-check, Java runtime/classes и 3 JARs; полный replay не обеспечен и в D02.2 не выполняется. R3 review:19 historical capsule-input FileNotFoundError IDs classified ENVIRONMENT_FIXTURE_INPUT_ABSENT before product assertions; existing CI debt, not a new permanent union55 baseline. |
| D02.2 | RNS/reference checks без локальной capsule в обычном CI | review коррекции D02.1-R принят | DONE (review accepted) | [Evidence `da8670e`](releases/2026-10-24-rns-reference-d02-2.md): public mappings, прежние pins, APK/inventory linkage, строгий --capsule. Clean export: 49 passed/1 прежний skip, collection 3051/0 errors; real capsule 2073 PASS. CI control/phase0/Docker: 55/54/54 residual failures, 0 errors; полные команды сохранены. |
| D03 | Окончательные ошибки ChatHTTP | приняты D02.1 collection/import isolation и D02.2 | DONE (review accepted) | [Evidence `290d430`](releases/2026-10-24-chat-http-terminal-d03.md): до 15 failed/18 passed, после 33 passed; зависимые 63+24 passed. Terminal-причина сохранена при cleanup, полный 200/consumer error без повторов, transient fallback сохранён. CI control/phase0/Docker: 54/54/53 residual failures, 0 errors; общий D01 открыт. |
| D04 | Auto stop/start lifecycle | приняты D03, D02.1 collection/import isolation и D02.2 | DONE (review accepted) | [Evidence `b41e1ad`](releases/2026-10-24-auto-lifecycle-d04.md): прежний Controller 8 failed/1 passed; service 55 PASS, зависимые 180 PASS/6 прежних skips. Публикация завершения owner и admission согласованы, fatal не сбрасывается; callback/process close до передачи владения. Linux desktop/Auto bridge CI PASS; одинаковые 54 residual failures в control/phase0/Docker. Docs-only `3f9854a` phase0 FAILURE отдельно. |
| D05 | Минимальная внутренняя модель выбора/назначения/активной сессии и граница существующего provider | review D03/D04 принят | DONE (local Linux boundary; review accepted) | [Evidence `c53265d`](releases/2026-10-24-desktop-provider-d05.md): модель используется NormalOwner/Platform/GuardedHost; 162 provider/model/native + 213 ownership/service/chat PASS. [Критерии](desktop-architecture.md#desktop-fleet-acceptance): stable ID 2×NL+DE, refresh без apply, fencing, signed legacy rejection, безопасные metadata. Linux Auto CI PASS; общий CI остаётся красным. Не Windows-интеграция/production fleet/F-01. |

<a id="ci-evidence"></a>
### D01/D02: наблюдавшиеся ошибки после baseline push

**PACKAGE_HARNESS_EMBEDDED_RECEIPT_FILENAME_COLLISION — OPEN technical debt.**
R3 inner `embedded.json` root-owned receipt уже содержит PASS/container exit0;
outer summary пытается перезаписать тот же path и получает PermissionError/exit1.
Product defect не установлен. Future correction: разные filenames для inner и
outer либо outer summary в отдельном user-owned evidence directory. В этом
checkpoint нет rename/repair/replay; не launch blocker Android. L04.2 PAUSED.

Эти ссылки — исходные наблюдения, не CI-проверки D00 и не автоматическое заключение
о причине каждого job. Разделить dependency/collection и fixture-import failures по фактическим logs.
1218 PASS phase22 относятся только к описанному локальному набору, не ко всему CI.

- [Client builds / Linux](https://github.com/Joker20380/family_connect/actions/runs/40073089239/job/120810560761).
- [AWG](https://github.com/Joker20380/family_connect/actions/runs/40073089248/job/120810560564).
- [TCP](https://github.com/Joker20380/family_connect/actions/runs/40073089297/job/120810560697).
- [Linux control](https://github.com/Joker20380/family_connect/actions/runs/40073089380/job/120810561183).
- [phase0](https://github.com/Joker20380/family_connect/actions/runs/40073089270).

D01.1: [итог PARTIAL, точные failures и CI](releases/2026-10-24-desktop-ci-d01-1.md).
D01.2: [окружение и evidence](releases/2026-10-24-control-ci-d01-2.md).
D02.1: [границы collection/imports и evidence](releases/2026-10-24-fixture-boundaries-d02-1.md).
D02.1-R: [комплектность runner и незакрытые pins](releases/2026-10-24-historical-runner-d02-1-r.md).
D02.2: [public RNS/reference и полный capsule gate](releases/2026-10-24-rns-reference-d02-2.md).
D01 сначала читает соответствующие workflows/lockfiles и эти ошибки; не переносит
лабораторный каталог целиком и не отключает обязательные suites ради зелёного CI.
D02 явно отделяет поддерживаемые проверки от архивных опытов; их source push не делает их release core.

<a id="d03"></a>
### D03: точка воспроизведения и требуемое сохранение ошибки

[provisioning/chat_bridge.py](../provisioning/chat_bridge.py), `ChatHTTP.stream`;
[tests/test_chat_bridge_http.py](../tests/test_chat_bridge_http.py).
[Детерминированное воспроизведение и исправление](releases/2026-10-24-chat-http-terminal-d03.md):
фактические ChatHTTP/FriendsClient, независимо управляемые read/close и clock без sleeps.
До исправления 15 failures, включая HTTP400/401/403/409 → ошибочный fallback;
после — первая terminal-причина сохранена независимо от cause cleanup, close выполняется.
Полный 200 и исключение потребителя после единственного yield не повторяют запрос.
Transient ConnectError/ReadTimeout/503, partial-read fallback и BridgeError mapping сохранены.
Это synthetic transport, не installed/live/protected DIRECT/service-only acceptance.
Review D03 принят; открытый historical replay D02.1-R не выдаётся за завершённый.

### D04: детерминированное завершение владельца

`clients/linux/auto_service.py`: Events на настоящем Controller воспроизвели ранний
DISCONNECTED, отказ start после завершённого потока и гонку повторного stop.
Теперь reap завершённого owner, публикация состояния и start/status/stop согласованы
одним lock; живой owner не обнуляется, FAILED/fatal не разрешает start.
Revocation до cleanup, retry записи journal без повторного cleanup, shutdown retain intent,
старые generation и поздний CONNECTED покрыты адресно. Реальный Coordinator завершает
terminal callback и process close до Runtime.dispose/передачи владения; native process
в этом тесте синтетический. [До/после и ограничения](releases/2026-10-24-auto-lifecycle-d04.md).
Связь с конкретным прошлым CI assertion из D01.1 не доказана; review D04 принят.

<a id="d05"></a>
### D05: локальная подготовка к расширяемому парку, не fleet-приёмка

[Основной контракт](desktop-architecture.md#desktop-fleet-boundary) — **минимальная Linux-граница реализована;
review D05 принят**. После принятых D03/D04, без зависимости от production fleet,
новых VPS или F-01 live. D05 задаёт общую модель/provider boundary; W01/W02 используют
её при продуктовой Windows-интеграции, обратной зависимости D05 → W01/W02 нет.
Модельные/отрицательные проверки выполняются адресно в D05; миграция — L08/W12,
полная установленная приёмка — L04/W11/R01. UI/model fixture не доверенный assignment.
L01/L02/W04 не расширяются за пределы fixed chat DIRECT/service-only.
Адресные model/provider/native проверки D05 выполнены; F-01/installed/live NOT_RUN.
Это не закрывает D01/D02 и не разрешает автоматически начинать Linux/Windows-интеграцию.

## Linux: интеграция, полный кандидат, затем установленная приёмка

| ID | Результат | Зависимость | Статус | Критерий завершения |
|---|---|---|---|---|
| L01 | Защищённый DIRECT для чатов | D03, D04; D05 review принят | DONE (review L01-R accepted) | Linux source/native/root→UID/isolated-kernel, не installed/live. [Исходное evidence](releases/2026-10-24-linux-chat-direct-l01.md) и [коррекция](releases/2026-10-24-linux-chat-direct-l01-r.md) сохранены с точными SHA; runtime umask, provenance и real TLS fatal исправлены и приняты. |
| L01-R | Исправления review protected Linux chat DIRECT | L01 review; принятые D03/D04/D05 | DONE (review accepted) | [Before/after и точные CI jobs](releases/2026-10-24-linux-chat-direct-l01-r.md): unit umask0077 + настоящий UID, DIRECT→EXIT registration→ProtectedMailbox→DIRECT с expiry/metadata, real TCP/TLS fatal без fallback. 145 + 49 Python/native, 6 root/UID, Go/race и оба isolated kernel gates PASS. Source `4fab7b6`: Client Linux/Auto/root→UID/kernel/AWG/TCP/voice CI PASS, control/phase0/Docker FAIL. Ни установка, ни live, ни закрытие D01/D02.1-R. |
| L02 | MESH service-only и передача владения | L01 (принят) | DONE (local source/native, review accepted) | [Начальный checkpoint](releases/2026-10-24-linux-chat-mesh-l02.md), source `383ef3606aaa4dbd29f0c7c0f755e6faec6e309f`, был PARTIAL. [L02.2](releases/2026-10-24-linux-chat-mesh-l02-2.md), source `dac0f6b45be6ed8703d3de93ff5fdbc67462eabe`, выполнил исходный authenticated API/mailbox OFF→ON/publication→EXISTING_EXIT→OFF через реальные Manual/Auto owners, drain/expiry/cancel/late results. Не installed/live/F-01; full-suite D01 остаётся открыт. |
| L02.1 | Lifetime поколения и комбинированная native/process приёмка | L02 partial; L01/L01-R, D03/D04/D05 приняты | HISTORICAL PARTIAL (completed by R/R2/L02.2) | [Отчёт](releases/2026-10-24-linux-chat-mesh-l02-1.md): bounded generation lease и typed-nil IPC исправлены; red/green на actual native owner, authenticated service-only/API/duplex-byte-mailbox/cleanup. На том checkpoint полный VPN publication→EXISTING_EXIT→OFF был NOT_RUN: отсутствовали generic packet/DNS/TUN health и broker lease lifecycle. Этот оставшийся gate выполнен отдельно в L02.2, не приписывается старому evidence. |
| L02.1-R | Terminal native generation: fencing и recovery | L02.1; L01/L01-R, D03/D04/D05 сохранены | REVIEW ACCEPTED (bounded scope) | [Отчёт](releases/2026-10-24-linux-chat-mesh-l02-1-r.md): peer/Mux failure и async bootstrap failure red/green на actual native owner; atomic generation pin закрывает acquire/use race; late HTTP/acquire, held/sticky cleanup, concurrent demand/VPN reservation проверены. Review RetainChat и terminal fixes принят; status-result correction выделена в L02.1-R2. На том checkpoint combined gate ещё был открыт; его завершение — отдельное evidence L02.2. |
| L02.1-R2 | Классификация native status и сохранение typed errors | L02.1-R review принят | REVIEW ACCEPTED (bounded scope) | [Отчёт](releases/2026-10-24-linux-chat-mesh-l02-1-r2.md): actual CONTROL4 contention и malformed IPC red/green. BUSY не отменяет healthy generation; DENIED до ChatBridge/ChatHTTP без replay. Atomic pin/refcount/cleanup/caps сохранены; прежние15 authenticated остаются обязательными. |
| L02.2 | Комбинированная local authenticated MESH OFF→ON→OFF приёмка | L02 partial; L02.1-R2 принят | DONE (review accepted, local source/native) | [Отчёт](releases/2026-10-24-linux-chat-mesh-l02-2.md): manual Supervisor и Auto/MESH отдельно; реальные UID IPC/native owner, TUN/private DNS/readback/health/publication, EXISTING_EXIT и новый SERVICE_ONLY; API/duplex byte-mailbox на каждом участке. Broker bind/renewal, lease/open/resource accounting, held cleanup/late result/profile mismatch/expiry/revocation/DENIED-no-replay; release CONTROL4 и packet RX fence приняты. Bounded CI gate сохраняет прежние15 и обязательные suites. Не live/installed/LXMF/F-01; исходный локальный L02 выполнен. |
| L03 | Полный внутренний Linux-кандидат | L02, D05, D01.3; L03.1 + L03.2 | DONE (review accepted; internal candidate scope) | Согласованы GUI, пользовательские службы, root-helper, native/RNS, зависимости и установка; capabilities соответствуют точному составу реально интегрированного пакета. Exact final-2 AppImage/DEB L03.2 проверены, review принят. Это не installed live acceptance L04/L05 и не public release. |
| L03.1 | Согласованный system/runtime payload, безопасная установка и ограниченный chat setup | принятые L01/L01-R, local L02/L02.2, D03/D04/D05, D01.3/D01.3-R | DONE (review accepted; exact build-9) | [Отчёт](releases/2026-10-25-linux-system-runtime-l03-1.md): полный hash/member/import closure, native/RNS/anchor; install exclusion/rollback и точные capabilities; fixed UID setup без VPN. Build-9,758 files;94 финальных адресных (umask077), desktop1120/24; actual disposable systemd255 install/polkit/UID/rollback/capability smoke PASS, private network/D-Bus/resolver. Source f826dbd: Client Linux и isolated native/root→UID/Auto/DIRECT CI PASS; rollback re-mask/start refusal PASS. Control/phase0/Docker по54 failures/errors0; voice observation сохранён, не общий CI PASS. Собственный system-only gate не равен L04/L05 PASS; review принят, включение в полный кандидат завершено в L03.2. |
| L03.2 | Включение принятого состава в AppImage/DEB | review L03.1 принят | DONE (review accepted; exact final-2) | Sourcecf66532, candidate9d4b13cc…, внутренние0.2.12~l03.2.1 AppImage/DEB с exact build-9; inventory/import/реальные polkit/setup/background/removal и rollback/barrier PASS в disposable Ubuntu24.04/systemd255. Desktop1146/24, адресные62 PASS; Client Linux/isolated native и final package CI40184803906 PASS. CI rebuildf7f6e765… не заменяет final-2. Full suites по54 failures отдельно. [Evidence](releases/2026-10-25-linux-candidate-l03-2.md). Legacy six-file/updater сохранён; не L04/L05 PASS. |
| L04 | Установленный Linux VPN | L03; L04.1 + L04.2 | PAUSED / NON-BLOCKING DESKTOP ENGINEERING | L04.1 DONE; L04.2 paused by owner27.10, not DONE. R3 source gate accepted, .11 construction frozen; installed MESH/Auto gates remain open in a separate stream after controlled beta. Not an Android launch prerequisite; no automatic retry, install or publication. |
| L04.1 | Установленная приёмка exact Linux candidate: AWG/TCP | review L03/AUTH/PROVISION/LIVE-1-R/RETEST/R2 и final LIVE-2 принят | DONE (review accepted; installed Linux AWG/TCP) | [RETEST](releases/2026-10-25-linux-installed-awg-tcp-l04-1-retest.md) и [final E/F1/F2](releases/2026-10-25-linux-installed-awg-tcp-l04-1-final.md) accepted. Exact .5 frozen/internal/unpublished. Registry restart — отдельное ops observation, continuity NOT_PROVEN/cause unknown; assignment/configuration unchanged. F2 не повторять; R3 не создавать. |
| L04.1-AUTH | Одна отдельная test identity/activation | explicit owner authorization25.10; fbb1732 accepted; L04.1-AUTH-PROVISION | DONE (review accepted) | [Activation](releases/2026-10-25-linux-test-activation-l04-1-auth.md) и [provisioning](releases/2026-10-25-linux-test-provisioning-l04-1-auth.md): одна FC-3YSQ-BE2D; registry/replay/resume и verified nl AWG/TCP assignment PASS. Outside-checkout state UID1000/0700/0600, private teardown receipt. Issuance не повторять; последующий guest-only handoff проверен в LIVE-1, original state сохранён. |
| L04.1-AUTH-PROVISION | Один штатный per-device nl assignment | accepted AUTH identity/activation subset; explicit owner authorization25.10 | DONE (review accepted) | Один FriendsOwner.configuration("nl") из exact final-2 Python3.12/vendor, без driver/retry: один AWG row/live peer и один persisted/runtime Xray user; чужие bindings и global settings сохранены. Signature/device/cache/floor/readback PASS, apply в этом checkpoint NOT_RUN. [Evidence и ограничения](releases/2026-10-25-linux-test-provisioning-l04-1-auth.md). Не повторять provisioning отдельно от разрешённого product connect. |
| L04.1-LIVE-1 | Положительная installed AWG/TCP приёмка exact final-2 | accepted AUTH/PROVISION; isolated Ubuntu24.04/systemd255 | PARTIAL (review accepted; historical final-2) | [Evidence](releases/2026-10-25-linux-installed-awg-tcp-l04-1-live-1.md): DEB/setup/READY, AWG×3/TCP×1 и transfers/cleanup PASS. Original AppImage AWG/traffic, second launch/confirmed GUI close сохраняют single owner; после reopen Disconnect отказал «Connection settings are being updated». Cleanup-only GUI Disconnect после освобождения lock PASS. Final-2 не изменён, больше не кандидат для завершения L04.1; PASS не переносится на новый build. |
| L04.1-LIVE-1-R | Poll/Disconnect race correction и новый internal candidate | LIVE-1 PARTIAL accepted; source/package only | DONE (review accepted; source/package scope) | [Report](releases/2026-10-25-linux-poll-disconnect-l04-1-live-1-r.md): deterministic red/green, generation fencing, pending/foreign fail-closed, stale callback/queued close. Source57f8eff, internal0.2.12~l03.2.2/d9c0d07f…; build-9 unchanged, exact pair integrity/real package gates PASS. Linux/AWG/TCP/native/package CI PASS; full suites54/54/53 failures, voice FAILURE. Live приёмка не входит в принятие source/package correction. |
| L04.1-LIVE-1-RETEST | Короткая installed приёмка exact corrected candidate | accepted LIVE-1-R; существующая FC-3YSQ-BE2D/nl; новая KVM | DONE (review accepted) | [Report](releases/2026-10-25-linux-installed-awg-tcp-l04-1-retest.md): exact DEB/setup/READY, AWG/TCP/HTTPS/64KiB↓/↑, single Disconnect и AppImage close/reopen PASS. Review принимает matching fresh-DNS request/reply с valid terminal NODATA. Cleanup/state PASS; positive gate не повторять. |
| L04.1-LIVE-2 | Bounded negative installed AWG/TCP gates | accepted RETEST/R1/R2; final owner review | DONE (review accepted; installed Linux AWG/TCP) | [Final receipt](releases/2026-10-25-linux-installed-awg-tcp-l04-1-final.md): .4 P1/P2/A–D accepted, not repeated; exact .5 E/F1/F2 accepted. F2 original AppImage local PASS; first registry readback failure retained as separate operational observation, uninterrupted continuity NOT_PROVEN, cause unknown, assignment/configuration unchanged. No replay/R3/source change. STOP → owner signing/limited-publication decision. |
| L04.1-LIVE-2-R1 | Terminal pre-start refusal / unknown outcome; новый system/user candidate | review LIVE-2 PARTIAL accepted; source/package only | DONE (review accepted; source/system/package) | [Report](releases/2026-10-25-linux-prestart-journal-l04-1-live-2-r1.md): actual AWG/TCP red→green, same-owner terminalization/recovery, generation fencing; final .4/source053c4e5/candidate42ea0699…/system8d7d78ec…. Exact systemd/polkit/import/rollback, DEB/AppImage/coherence и actual old-build refusal PASS. Full CI не зелёный; live B1 retest/B2–F отдельно. |
| L04.1-LIVE-2-RESUME | Installed negative acceptance exact .4, continuation | A/B1 review PASS; existing test identity/nl; fresh KVM | PARTIAL (STOP E; review accepted) | [Continuation](releases/2026-10-25-linux-installed-awg-tcp-l04-1-live-2-continuation.md). P1/P2/B1/B2/C1/C2/D PASS on exact .4. E FAIL: queued Future/busy/open/CONNECTING; no late VPN start proven, helper/TUN0/generation0/null. Fixture cancels before worker release; F1/F2 NOT_RUN. Source/candidate unchanged; L04.2/L05/teardown NOT_RUN. |
| L04.1-LIVE-2-R2 | Normal queued Connect/Close ownership; new internal .5 | LIVE-2 PARTIAL/review accepted, E defect; source/package only | DONE (review accepted; source/package) | [Report](releases/2026-10-25-linux-queued-connect-close-l04-1-live-2-r2.md): source1c2beb6/candidate f0ee1760…, unchanged verified system8d7d78ec…. Red4/targeted197/full1191 PASS; normal mutation Future/revision fence, running/done-undelivered blocks Close. Exact .5 package/integrity and Linux/AWG/TCP/package CI PASS; local isolated gates PASS. Full CI54/54/54 failures retained, no overall PASS. R2 used no private state/gateway/live E/F; later LIVE-2 result above. |
| L04.1-AUTH-TEARDOWN | Обязательная очистка отдельного test device | после L04/L05 или завершения test campaign; отдельное разрешение/review | QUEUED / NOT_RUN | Device-scoped gateway cleanup → readback отсутствия только test peer/user при сохранении чужих ресурсов → registry revoke. Private receipt содержит exact binding hashes/row/address/read-only checks и дополнен L04.2 test chat/store/keyring, certificate issuance/expiry и registration. Revoke/teardown не выполнялись. Штатного unregister сейчас нет; не восстанавливать целиком старые DB/server.json и не начинать cleanup автоматически. |
| L04.2 | Installed Linux MESH/Auto | L04.1; accepted R3 source gate; separate future owner authorization | PAUSED / NON-BLOCKING DESKTOP ENGINEERING | SOURCE GATE DONE/review accepted; .11 CONSTRUCTION DONE/frozen internal candidate570a5515/system34b27cb9.46 tests/embedded equality PASS, inner exit0; outer exit1 only receipt collision, existing D02/CI debt. No established product defect; installed package/live P0/P1/Auto NOT_RUN, not L04.2 DONE or overall CI PASS. No harness/launcher/rebuild/install/rollback/identity/lifecycle/L05/L06/publication. [Owner decision](releases/2026-10-27-android106-controlled-beta-readiness.md), [historical R3 evidence](releases/2026-10-27-linux-readiness-cause-preservation-l04-2-r3.md). |
| L05 | Установленный Linux-мессенджер | L03, L04 | QUEUED / NOT_RUN | DIRECT/MESH-доставка без VPN и с VPN, контакты/текст/голос, история и фоновые события — completion gate на реальных компонентах. Backlog: L04.2 observation registration_error=delivery_unavailable; причина не локализована, client defect/gateway outage не заявлены. Исключён из L04.2 core prerequisites final review-решением; диагностика/repair здесь NOT_RUN. Вне Linux AWG/TCP Beta scope; автоматически не начинать. |
| L06 | Linux recovery | L04, L05 | QUEUED | Loss/return, sleep/resume, restart/cancel, bounded recovery and one reconnect owner. READINESS_RELAY_PROBE_CORRELATION_GAP: validated Post probe is not forwarded through relayProcess/RNS/Channel/provider; zero direct rows cannot count relay calls. No wire expansion in R3. R2 cooldown-only retry mechanism reproduced deterministically in R3; original live exact network counts remain unknown. Automatically do not start. |
| L07 | Linux visual parity | L03, L06 | QUEUED | Реальные окна: согласованные экраны/состояния, список вариантов и отдельные selected-next/active state по D05, RU/EN, DPI100/125/150/200%, resize/focus/Tab/Enter/Escape; сопоставление с точным Android-эталоном без изменения Android106. |
| L08 | Linux updater и сохранение данных | L03, L07 | QUEUED | Переход со старого поддерживаемого клиента на полный bundle и совместимая миграция настроек выбора D05; identity/WG keys, активация, Support ID, история, настройки, ссылки и signed floors/счётчики сохранены. |

Продолжение после обрыва25.10: неизменный L03.1/build-9 повторно прошёл hash/member/source
verification, actual disposable systemd255 smoke и94 адресных проверки (umask077).
Новый runtime/build не создавался; затем review L03.1 принят и отдельно разрешён L03.2.

Phase22 подключила Linux ChatOwner к EXISTING_EXIT. L01 добавляет protected DIRECT;
старый SYSTEM не переименован в DIRECT и не используется fallback этого нового пути.
Локальный host lifecycle принят по L02.2; DIRECT public admission завершается в D01.3-R. Одно активное владение
не означает вечный PID: текущий worker имеет собственный жизненный цикл.
Полный внутренний пакет L03 обязателен перед закрытием L04–L08; system-only component-r18 недостаточен.

L02.1 source `a2b105de49391928d4bb9c15c4d5ee2305085918` pushed/remote-verified:
600 адресных Python/native/process checks, Go/race и isolated kernel PASS.
Завершившийся CI: authenticated service-only и прежние Auto/root→UID/DIRECT,
Client Linux/AWG/TCP/voice PASS; control 3015 passed/54 failed/127 skipped,
phase0/tests 3014/55/127, Docker 3013/54/129, errors0. Дополнительный phase0 failure
`test_ui_unavailable_server_ack_is_authoritative` — причина не установлена.
Это не общее CI acceptance. Новые L02.1-R результаты и SHA отдельно в
[текущем отчёте](releases/2026-10-24-linux-chat-mesh-l02-1-r.md); mandatory suites
не отключены, посторонние failures не исправлялись.
L02.1-R source **`6556a902c723a3ef73486733f090cea6f388d099`** pushed/remote-verified:
606 distinct local checks, native/race/reference и isolated kernel PASS. Завершившийся
CI: control 3015 passed/54 failed/133 skipped; phase0/tests 3015/54/133;
Docker 3014/53/135, errors0; isolated-linux с13 authenticated, Client Linux,
AWG/TCP и voice PASS. Эти результаты не переносятся на R2.
L02.1-R2 source **`89e20a3437b2ba1b02f7d1649487579678158373`** pushed/remote-verified:
211 distinct local Python/native/process checks, native/race/reference PASS;
завершившийся CI: control **3030/54/135**, phase0/tests **3030/54/135**,
Docker **3028/54/137** (passed/failed/skipped), errors0; phase0/tests перепроверен
по собственному логу. Isolated-linux с15 authenticated, Client Linux, AWG/TCP/voice
PASS. Точные R2 jobs и новые L02.2 source/jobs разделены в
[отчёте L02.2](releases/2026-10-24-linux-chat-mesh-l02-2.md).
L02.2 source **`dac0f6b45be6ed8703d3de93ff5fdbc67462eabe`** pushed/remote-verified:
isolated-linux **40129362252/120977564710 PASS**, включая original15, combined3,
root→UID, оба kernel gates и race. Новый CI: control **3032/54/138**,
phase0/tests **3032/54/138**, Docker **3030/54/140**, errors0; AWG/TCP PASS.
Client Linux **1003/1/94** (bounded-mailbox BrokenPipeError) и voice pointer/holding
FAIL, причины не установлены; не общий CI PASS. Никаких unrelated fixes или bypass.
Mandatory full suites и Auto/DIRECT/root→UID gates сохранены; локальный L02 принят review.
Новый D01.3 source/CI учитывается отдельно в [отчёте](releases/2026-10-24-desktop-chat-admission-d01-3.md).
Linux updater пока принимает legacy six-file archive; не объявлять полный bundle обновляемым до L08.

## Windows: платформенная и продуктовая интеграция

| ID | Результат | Зависимость | Статус | Критерий завершения |
|---|---|---|---|---|
| W01 | Windows native ↔ broker | D03, D05 / общий core | QUEUED | Модель/provider boundary D05 и MESH/P0/P1 подключены через защищённый broker/FriendsOwner IPC; собственные Windows runtime/readback проверки, не перенос Linux evidence; GUI без постоянного admin. |
| W02 | Windows Auto и recovery | W01 | QUEUED | Общий Go Auto интегрирован с платформенными службами и моделью D05; проверены выбор транспорта, отмена, cleanup/generation fencing и восстановление. Эта интеграция ещё не завершена. |
| W03 | Windows контакты, текст и история | W01, W02 | QUEUED | Пользовательская служба и WinForms выполняют базовый чатовый цикл с существующей identity. |
| W04 | Windows DIRECT/service-only | W03, L01/L02 contract | QUEUED | Чаты при VPN OFF и переходы владения работают на Windows с необходимыми проверками доступа и underlying routing. |
| W05 | Windows голосовые сообщения | W04 | QUEUED | Реализованы принятые запись, отправка, воспроизведение и существующие voice/radio режимы. |
| W06 | Windows фон и уведомления | W05 | QUEUED | Закрытие GUI, уведомления и восстановление пользовательской службы сохраняют принятую семантику. |
| W07 | Windows диагностика и online support | W06 | QUEUED | Экспорт, opt-in согласие, срок действия, отзыв и фоновая отправка соответствуют принятой модели; без автоматического opt-in. |
| W08 | Windows объявления | W07 | QUEUED | Реализованы существующие операции и проверки ролей без изменения прав пользователей. |
| W09 | Windows UI и остальные пользовательские сценарии | W03–W08 | QUEUED | Реальные visual comparisons, список вариантов с отдельными selected-next/active state D05, настройки, активация, приглашения/QR/deep links и согласованные элементы интерфейса. |
| W10 | Полный внутренний Windows installer | W01–W09 | QUEUED | Согласованные GUI, broker/native/RNS и зависимости с достоверными capabilities; сохранены SCM/driver paths и privilege boundary. |
| W11 | Установленная Windows-приёмка | W10 | QUEUED | На установленном кандидате проверены VPN, чаты, фон, recovery, переходы сети и применённый target/profile с заявленными capabilities; cross-build/Wine/headless/model fixture не засчитываются. |
| W12 | Windows обновление | W10, W11 | QUEUED | Совместимая миграция настроек выбора D05 при обновлении; identity/WG keys, активация, Support ID, история, настройки, ссылки и signed floors/счётчики сохранены. |

Windows chat endpoint на проверенном SHA — NOT_INTEGRATED. W10 предшествует завершению
установленной приёмки, даже если отдельные W01–W09 уже проверены в dev environment.
Нет разрешённой Windows-машины/VM/runner — runtime NOT_RUN с точной инструкцией,
а не PASS по Linux cross-build; доступные исходники/пакеты доводятся отдельно.

<a id="release-gates-three-platforms"></a>
## Финальные артефакты и границы выпуска

| ID | Результат | Зависимость | Статус | Критерий завершения |
|---|---|---|---|---|
| R01 | Финальная проверка поставки | L04–L08, W11/W12 | QUEUED | Точные AppImage/DEB/Windows installer, обновления и заявленные возможности согласованы; проверки относятся к финальным артефактам; SHA256/manifests/RU/EN инструкции готовы. Dynamic fleet не заявляется по D05 без отдельной интеграции/приёмки. |

AppImage — основной Linux artifact, DEB дополнительный; legacy archive сохраняется для совместимости.
Windows сохраняет действующий installer/broker/service/driver workflow, не новый формат ради parity.
Обновления сохраняют signed catalogs, digest, anti-rollback, permitted upgrade paths и identity.
Подписи update manifest, installer/Authenticode и driver перечислять отдельно; отсутствующие не выдумывать.
Версии выбирать по desktop-линейке; Android106 соответствие фиксировать feature/core manifest, не номером.
Полный parity installer сейчас0/2, завершённая установленная приёмка0/2.
Source/local tests/CI/build/install/private-test readiness/publication — отдельные состояния.
R01 готовит release/catalog/landing изменения, но НЕ разрешает публичную публикацию.
Исторические [three-platform gates](PLAN.history-2026-10-24.md#release-gates-three-platforms)
сохранены как прошлые обязательства, не как альтернативный текущий NEXT.

## Общие обязательные ограничения и выбор проверок

- Читаем STATUS, выбранный ID и только релевантные исходники/доказательства через [docs map](README.md).
  Исторические NEXT/ACTIVE в архивах и release reports не запускают другую задачу.
- Проверки выбирать по изменённому риску и обязательному gate; сначала адресные проверки,
  шире — при общей зависимости/регрессии/перед приёмкой. Не гонять весь исторический набор после мелкой правки.
- Сохранять точную связь source/artifact/evidence; старые PASS и hashes не переписывать для нового исходника.
- Для D00 только documentary consistency, byte-exact history, новые ссылки и `git diff --check`;
  никаких сборок, pytest, эмулятора, capsule sweep или live-трафика.
- Не менять Android106, действующие пользовательские MESH-сессии, gateway или чужую policy.
  Desktop P1 identities проверять отдельно; точечное операторское решение не блокирует создание installer.
- Native общий, не отдельные Python/C# RS/crypto реализации. Сохранять AWG/TCP, identity/roles/
  certs/revocation/expiry/floors/signed directory, accepted cache semantics и fail-closed traffic policy.
- На целевой ОС проверять TUN/DNS/IPv6/underlying service routes, cleanup при error/cancel/crash,
  negotiated P0/P1, HTTPS, single4MiB + parallel2×2MiB, idle/recovery и export.
  Первичный live-бюджет до32MiB прикладных данных на ОС; не тратить его на ограниченном мобильном тарифе.
- GUI обычного пользователя, ограниченные helper/broker IPC; не ослаблять key storage или защиту ОС.
- Реальные screenshots, а не наличие CSS/строк, закрывают visual gate. Для emulator retain KVM/host GPU,
  2 cores, CPUQuota150%, max180s, stop85°C CPU/80°C GPU; никаких idle/SwiftShader fallback.
- Commit/push каждого завершённого шага по [AGENTS](../AGENTS.md), без force/reset/clean.
  Проверять remote SHA; push не равен CI success, установке или публикации. Секреты/state/capsules/binaries вне Git.

<a id="other-obligations"></a>
## Другие обязательства — HOLD, вне текущей desktop-очереди

Ниже сохранены незакрытые направления, не разрешение начать их или расширить parity106.
Перед возобновлением сверить релевантную дельту, а не принимать старый NEXT за действующий.

| Направление | Что остаётся / источник |
|---|---|
| Android field / P1 cohort | Физические updates106/P1 и cold-bootstrap; Volgograd96 не закрывает Краснодар FIELD-1. [Cohort](releases/2026-10-23-tester-p1-cohort.md). |
| Fleet/control5.2–5.6, gateway recovery6 | Native/Friends/device integration, долговременная AWG/TCP/Android приёмка, independent ingress/recovery. [Исходные обязательства](PLAN.history-2026-10-24.md#глобальные-этапы), [recovery design](reticulum-recovery-design.ru.md). |
| Secrets / disaster recovery | Consumer audit перед удалением originals, production signing acceptance, внешний носитель и восстановление чистого хоста; не считать закрытым по локальным backup. [Архив](PLAN.history-2026-10-24.md#глобальные-этапы). |
| Операции RU/NL | RU SSH timeout, legacy Docker peer-worker unhealthy, RU counters неизвестны. [Snapshot](releases/2026-10-23-vpn-health.md); без рестартов ради диагностики. |
| Local storage / thermal | Сохранить symlinks; live project/Codex migration и reboot automount отдельно. [Migration](releases/2026-10-07-local-storage-migration.md), [GPU/thermal limits](releases/2026-10-23-laptop-thermal-diagnostic.md). |
| Остальной продукт | Doze/OEM/boot/Android13+, iOS/macOS, лицензирование, private security reporting, Windows publisher signing, коммерческий запуск. [Deferred backlog](PLAN.history-2026-10-24.md#отложенные-задачи). Новые VPS/покупки не разрешены. |

<a id="mesh-roadmap"></a>
Home Gateway (phone↔home PC, LAN/NAS/RDP/residential egress) остаётся отдельным design/backlog;
[5A–5G/RNS gates](reticulum/HOME_GATEWAY_DESIGN.md) не закрыты desktop MESH exit.
<a id="multi-carrier-roadmap"></a>
Multi-carrier: после авторизованного Краснодар FIELD-1 и разбора Telemost path;
[Carrier API → WB → VK → failover](PLAN.history-2026-10-24.md#multi-carrier-roadmap).
Ни новые carriers, ни MESH2/MESH3 не входят в parity106.
<a id="django-admin"></a>
Django7.1 (servers/access/payments) зависит от backend/fencing и recovery; нет второй writable
копии leases, платежи идемпотентны, migration/provider/secret store — отдельные решения.
[Сохранённый контракт7.1](PLAN.history-2026-10-24.md#django-admin), [design](design/django-product-plane.ru.md).

## История и завершение шага

[Полный прежний PLAN](PLAN.history-2026-10-24.md), [STATUS](STATUS.history-2026-10-24.md),
[phase22](releases/2026-10-23-desktop-parity106.md#linux-user-chat-admission-and-existing-exit-handoff-2410-phase22),
[отчёт D00](releases/2026-10-24-desktop-parity106-d00.md).
**STOP после CHAT-UX-1. NEXT — review CHAT-UX-1 перед установкой нового UI-кандидата владельцу;
L04.2/full L05/TCP HTTPS diagnosis/teardown/signing/publication NOT_RUN.**

Этот прежний STOP сохранён как история. **Текущий STOP27.10: readiness checkpoint
завершён; NEXT — закрыть только фактические ANDROID-CONTROLLED-BETA launch blockers.
Linux L04.2 PAUSED / NON-BLOCKING DESKTOP ENGINEERING, не DONE.**
