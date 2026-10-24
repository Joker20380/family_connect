# Linux + Windows parity with accepted Android106

## Current entry point — D00, 24 October2026

Read [current STATUS](../STATUS.md) and [the selected PLAN task](../PLAN.md) first.
The last finalized product checkpoint is [phase22, 24.10 08:53 CEST](#linux-user-chat-admission-and-existing-exit-handoff-2410-phase22),
followed by the owner's stop at08:55. D00 is documentation only; NEXT is D01 as a
separately authorized task, not automatic continuation. [D00 preservation report](2026-10-24-desktop-parity106-d00.md).
Everything below is historical evidence: intermediate NEXTs/checkpoints are not
concurrent assignments, and results/hashes retain their original source and scope.
The1218 PASS are a local phase22 suite, not later CI success; see [CI observations](../PLAN.md#ci-evidence).
The subsequently reported ChatHTTP teardown/fallback defect is tracked as [D03](../PLAN.md#d03),
not silently covered by older terminal-error claims. No new runtime/visual acceptance is claimed here.

## Owner progress readback —24.10,07:07 CEST

Readback only: stage3/6, Linux integration; no measured overall percentage.
Full parity installers0/2 and completed installed target-OS acceptances0/2.
Latest broad suite `support106-full-r2.log` records1130 PASS, one warning;
`support-owner-unit-r2.log` records133 PASS, one warning. These scopes overlap.
Both are under `state-client-build/desktop-parity106-20261023/`.

New `state-client-build/desktop-parity106-20261024/support-service-runtime-r1/result.json`
records PASS with actual GTK, private D-Bus and user-systemd: collection after GUI
exit,63.444s cadence, synthetic identity/consent preserved across service restart,
stale mutation rejection, revoke without chat keyring and idle exit. Its real
local API handlers use MockTransport and VPN state is synthetic. The supervisor
is Type=exec on a private bus, not accepted production Type=dbus installation.
Receipt:136.07s, CPU quota50%, peak77°C, no guard stop; fixture unit is inactive.
The collector-history source change at07:04 is newer than this passing run and
requires regression before reporting current-source completion.

Remaining: support-owner regression and package closure, restricted chat,
installed Linux MESH/P1/network-loss/sleep/recovery/identity-safe upgrade,
Windows broker/WinForms integration, complete visual comparison and full private
AppImage/DEB/Windows installers. Component-r14 remains a historical unsigned
internal component, not a full installer or this newest source snapshot.
Linux0.2.11/Windows0.2.15, existing installations, Android106, identities,
server grants and public catalogs are unchanged. No deployment occurred and no
rollback is required. This checkpoint launches no tests, builds or emulator.

## Owner progress readback —24.10,02:56 CEST

Documentation-only checkpoint: stage3/6, Linux integration, not50% completion.
There are0/2 complete parity installers and0/2 installed target-OS acceptances.
New source since phase13 implements protected native normal configuration,
authenticated signed catalog/floor checks and shared Linux profile validation;
the Friends existing-identity handoff is not connected to a product Auto backend.
`auto-normal-go-r2.log` records carrier/desktopmesh race tests repeated three times
and native normal/automatic tests five times, exit0; thermal receipt26.01s/57°C.
`auto-normal-python-r1.log` records134 PASS,4.00s/66°C, before the newest owner
handoff changes. Both receipts are under
`state-client-build/desktop-parity106-20261023/`. The new owner tests and36 native
compatibility vectors are not yet run. No Linux r14/Windows r10 worker or Linux
component-r7 exists; phase13 builds below do not contain these new sources.
Real AWG/TCP Auto handoffs, root coordinator and authorized GUI IPC remain open.
Windows broker/WinForms integration, complete diagnostics/consent, exact visual
and installed MESH/P1/recovery/upgrade acceptance, AppImage/DEB/Windows installers
remain unfinished. Linux0.2.11/Windows0.2.15, Android106, existing installations,
server grants and public catalogs are unchanged; no new rollout/rollback action.
No emulator was running during this check. No measured whole-task percentage is
established; overlapping test counts and stage numbers are not completion shares.

## Owner progress readback —24.10,02:13 CEST

Documentation-only status check: stage3, Linux integration. No new installation,
publication, server policy change or runtime acceptance occurred during this check.
The latest completed native build is
`state-client-build/desktop-parity106-20261024/bridge-linux-r12/fc-mesh`, Linux amd64,
SHA256 `8b6d42b5f442cd98a99c4d0627213a79e0c77da8f66ce6c2df5ffeaf6e991480`.
Its build manifest records source digest
`aa71de8221935bc0adad869c83e4f4c8d2fafcbbd01480f0f97d36d4459c02b8`, local packet/IPC
tests PASS, installed=false, runtime_acceptance=NOT_RUN, publicly_distributed=false.
Automatic/materials/platform/worker package tests passed. Recorded earlier IPC
checks are11 Go tests repeated5 times with race detection and91 targeted Python
checks; they do not cover all subsequent source edits or the unrun kernel IPC fixture.
The r12 thermal receipt records309.15s, CPUQuota50%, peak72°C, exit0, no thermal stop.
The policy IPC and Linux guarded-host adapter are implemented in source, but real
root coordinator/configuration/capability/readiness integration is incomplete.
Exact IPC validation and native+kernel integration checks remain next. Full Linux
installed MESH/P1/recovery/upgrade, complete diagnostics and visual acceptance,
Windows frontend/broker parity and AppImage/DEB/Windows installers remain open.
Existing published versions are unchanged; there is no new rollout to roll back.
No defensible overall completion percentage is established by these receipts.

**IN_PROGRESS — NOT PARITY PASS. No desktop candidate installer yet.**
This is the single continuing parity report, not a release announcement.
Product versions remain Linux0.2.11 and Windows0.2.15 as last documented; native
development workers are now built separately. Linux's current install symlink is
read back as0.2.11; no installed-package/public-artifact acceptance is inferred.
No version bump, signing, push, publication,
Android rebuild or owner/tester install, gateway restart or policy mutation.
The unchanged reference APK was installed only in a newly created offline emulator.

## Owner progress readback —24.10,06:20 CEST

Status-only checkpoint, not a release or completed phase18. Latest local suite:
`state-client-build/desktop-parity106-20261024/diagnostics106-full-r1.xml`,
980 passed, zero failures/errors/skips,47.498s. Thermal wrapper51.02s,50% CPU quota,
peak83°C, no guard stop. New native diagnostic fields and cached lifecycle/incident
projection now have41 matching vectors against five hash-verified accepted106 Java
sources (`diagnostics106-java-r2/result.json`), zero differences. No APK rebuild.
Fresh GTK export verification did not run: `diagnostics106-acceptance-r1.log`
reports `dbus-run-session: failed to exec 'xvfb-run': No such file or directory`
after the Java comparison passed. Its wrapper exited1 after10s, peak71°C.
Do not promote this failed launch or previous synthetic-state screenshots to new
visual acceptance. Repair the test environment and rerun bounded GUI checks next.

Stage3/6 remains Linux integration, not50% completion. Common worker binaries exist
for Linux/Windows; Linux Auto/MESH/helper, contacts/text/voice/background delivery
have implementation and scoped local checks, not complete installed acceptance.
Windows broker/WinForms integration, remaining consent/restricted carrier work,
installed MESH/P1/recovery/identity-preserving upgrade, final visual comparisons and
complete AppImage/DEB/Windows installers remain open. Latest internal component-r13
predates the new diagnostics changes. Full parity installers0/2; completed installed-OS
acceptance0/2. No defensible aggregate percentage is established by test counts.
Linux0.2.11/Windows0.2.15 and existing installations/public catalogs remain unchanged;
no new deployment or rollback action. No emulator/parity test service running at readback.

## ANDROID_REFERENCE

- APK: `state-client-build/owner-diagnostic106-20261022/delivery/FamilyConnect-0.1.18-beta106-recovery.apk`.
- SHA256: `242855c43e889e708234ce2f687fa02d37bccb1eee408904f09216b6abd8f020`.
- Signer SHA256: `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`, locally verified with apksigner.
- Source: sibling `android-source/`; complete inventory SHA256
  `8574228fc809fdbd67b3d92680e09c979fe930599a47e4ed1b47fd30f872ed0c`;
  all2073 files independently rehashed and matched.
- Restricted native105, unchanged in106:
  `37ba4fac656811dd979688a274f45aed85a3aa567f1fafb3987a81c020fa91f1`.
  All12 APK native entries are retained; no desktop/ARM64 binary equivalence claim.
- `clients/shared/android106-reference.json` pins175 shared files and exact Android
  resource/handler hashes.96 changed/new shared files were initially extracted.
  The default dependency closure excludes experimental build tags/commands; only
  explicit platform/test adaptations follow. No whole fixture/capsule import.
- Sources: owner-disconnections, p1-owner-acceptance, wifi-resume,
  OWNER_RECOVERY_CANDIDATE and EXISTING_USERS_PRIVATE_BETA; original evidence and
  the user's uncommitted documentation/fixtures are preserved.

## DESKTOP_FEATURE_PARITY

Android column is source-backed against the verified APK capsule, with fresh
offline emulator rendering, not a new physical Android test. Desktop columns describe current integration, not planned
buttons. `MISSING` remains a completion gate; it is not removed from the matrix.

| Function/screen | Actual106 | Linux working tree, not installed | Windows working tree, not installed | Required implementation | Acceptance |
|---|---|---|---|---|---|
| Home/navigation | FriendsActivity→TerminalUi.DashboardLayout; thin-line terminal; status/chat/route/settings | reference palette/EXIT/rectangular frames/nav/state strings, real captures; incomplete details | older terminal | complete reference composition and strings | partial GTK comparisons; Windows NOT_RUN |
| No access/activation | Friends identity + invitation | existing Friends flow | broker Friends flow | preserve, align UI | new computer + in-place upgrade |
| Connect/disconnect/states | orchestrator, terminal, CONNECTING/RESTORING | AWG/TCP plus GTK→MESH/Auto services, explicit cancel/stale-poll/generation guards | AWG/TCP | real installed integration + Windows counterpart | system TUN + HTTPS + cancel |
| Server/route choice | RU/NL, map, server load | existing route/load, different layout | existing route/load | capabilities + accepted layout | actual selected/active server |
| Auto/manual AWG/TCP | real orchestrator + manual choices | shared native policy, root guard/coordinator/service and single-attempt MESH/AWG/TCP adapters; signed root/user floors and authorized GTK client implemented; actual transport shown separately | existing broker AWG/TCP Auto; new shared policy not wired | installed handoff/capability/cleanup/upgrade acceptance; Windows counterpart, no rename | Java traces/race/native catalog/isolated guard checks;879 selected regression tests and four-scale GTK Auto tests; helper operations synthetic, installed Auto NOT_RUN |
| Manual MESH | readiness→authenticated media→TUN | native/service/backend/GTK source wired; receipt/ACK and packaged RNS locally tested; installed/live acceptance MISSING | worker cross-build only, broker/UI and embedded runtime MISSING | installed RNS/product runtime; Windows protected owner | actual MESH at both ends |
| P0/P1 | pre-TLS RS; effective Mux profile | settings select next session; current request/effective RS/Mux shown separately | GUI MISSING | Windows counterpart + live proof | RS32/32 + CREDIT128/P0 compatibility |
| P2 operator selector | present in APK; P1/Q0 accepted baseline | absent | absent | explicitly outside accepted desktop profile boundary; do not enable Q1 | boundary rejects P2, no hidden mode |
| Recovery | user intent, bounded retry, explicit stop | AWG/TCP recovery; MESH desired/backoff/stop plus systemd memory-only restart intent in source; isolated manager crash/revoke check PASS | existing broker Auto | finish helper regression and installed restart/network recovery; Windows MESH counterpart | network loss/return, sleep, UI/backend restart |
| Settings | RU/EN, motion, sound/voice and support options | subset | subset | port actual options/semantics | restart persistence + focus |
| Identity/Support ID | own Device Identity + server Support ID | own Friends identity; authenticated refresh, identity-bound cache and GTK copy implemented/tested locally | own protected identity; support gap | installed identity-preserving upgrade; Windows counterpart | local authenticated API/unchanged-key and clipboard checks PASS; installed upgrade NOT_RUN |
| Invitations/QR/deep links | access/referral and contact workflows | access/referral implemented | access/referral implemented | retain handlers; add chat workflows | before/after first launch, single instance |
| Contacts | add/rename, full-key/fingerprint verification | real shared store + GTK card/copy/verify/rename, local checks PASS | placeholder | Windows counterpart; complete accepted contact menu/layout | actual GTK checks and restart PASS; installed upgrade NOT_RUN |
| Text/history/outbox | chat runtime, local history, durable delivery | encrypted Secret Service owner + GTK queue/edit/history; local RNS ACK/background lifecycle PASS; shared restricted Go core, native ownership and private Linux parent/worker IPC implemented; user-service admission/routing NOT_INTEGRATED | placeholder; shared native ownership cross-build only | authenticated user-service/host admission and route orchestration; installed background lifecycle, exact thread composition; Windows | local two-endpoint wire/GTK/reopen, shared-core and duplex IPC checks PASS; live restricted service/installed NOT_RUN |
| Voice messages | hold-to-record, playback, voice/radio modes | actual GStreamer/Codec2 pipeline, GTK preview/pause/seek/explicit send, encrypted preferences; local codec/wire/UI checks | MISSING | exact composer/profile placement; physical audio/Android pair; Windows counterpart | synthetic capture/silent playback and actual local RNS ACK; hardware/installed pair NOT_RUN |
| Notifications/events | grouped private notifications, service history, background delivery | independent user-session owner; bounded D-Bus RPC/ACK/actions; encrypted flags/history/replay fence; local closed-GUI RNS delivery and crash recovery | MISSING | production Type=dbus/package activation and upgrade, real host notification daemon, Windows counterpart | isolated real systemd/Secret Service/RNS + GTK checks; installed OS acceptance NOT_RUN |
| Announcement management | role-checked list/publish/edit/preview in accepted ChatActivity | authenticated API + GTK list/compose/preview/publish/edit; final local tests and four rendered scales PASS | MISSING | exact Android comparison, installed acceptance and Windows counterpart; do not grant roles | synthetic role/revocation/conflict/idempotency/bounds; final-r5 and missed regressions-r3 PASS; no live publication |
| Diagnostic export | bounded106 JSON, current/incident/history | native106 typed projection, RS/flow/Mux/startup, cached incident/history, private atomic store and GTK privacy/save | no equivalent | installed live collection acceptance; Windows counterpart |41 accepted-Java vectors and real GTK save PASS locally; installed/live NOT_RUN |
| Online support | opt-in support automation/diagnostics controls | explicit7-day GTK consent; independent non-root session owner; identity-bound metadata,4096B projection, authenticated upload, completion cadence/cancel | MISSING | installed Type=dbus/upgrade/logout/cold-login acceptance; Windows counterpart |54 accepted-Java vectors; real private GTK/D-Bus/systemd GUI-close/restart/revoke, local API proof/retention/rate tests; no production uploads |
| Updates | signed catalogs/in-place update | existing shared Linux channel | independent Windows channel | preserve floors/digests/upgrade format | actual artifacts + old state |
| Desktop lifecycle | Android foreground/VpnService semantics | window/helper policies | tray + broker/SCM | preserve desktop conveniences | no hidden dead TUN on close/crash |
| Platform permissions | VpnService/USB not desktop APIs | polkit/helper | authenticated pipe/UAC/service | OS equivalents, ordinary-user GUI | least privilege + denied client commands |

No new calls, group networks, distributed mesh, MESH2/MESH3, QUIC/FEC or speed
research is included. Voice/radio controls refer to already present messages,
not a new calling feature. Android's owner P2 control is recorded rather than
misrepresented as absent; accepted desktop profile behavior is deliberately P0/P1.

## VISUAL_PARITY

`clients/shared/android106-ui.json` is extracted reproducibly from exact resources
and handlers: palette, stroke widths, navigation/block order, RU/EN source text.
Background `#071211`, surface `#102321`, frame `#416861`, text `#e2eee8`,
muted `#a4bab2`, mint `#a8dfce`, amber `#dbb674`; strokes0.5/0.65/1dp.
This data is not a replacement for real rendered comparisons.

Earlier apparent owner captures were empty and are not used as evidence. A new
AVD `fc-parity106`, dedicated adb5040/serial emulator-5582, ran the exact APK
via libndk_translation. Installed base.apk SHA256 matches242855c4…; versionCode106,
Wi-Fi/data off, **Active default network: none**. No phone command/session change.
FLAG_SECURE makes adb screencap black; emulator-console framebuffer capture obtains
the actual rendered window without changing APK code or security flags.

Evidence under `state-client-build/desktop-parity106-20261023/reference-emulator/`:
- `Screenshot_1792770180.png`: EN home/off; `Screenshot_1792770321.png`: EN route.
- `Screenshot_1792770322.png`: EN settings; `Screenshot_1792771564.png`: lower settings/support.
- `Screenshot_1792771723.png`: RU settings; `Screenshot_1792771725.png`: RU home/off.
- `Screenshot_1792772253.png`: RU empty messenger, notifications declined in emulator;
  `Screenshot_1792772254.png`: RU route.
- `installed-reference.txt` and `network-isolation.txt`: installed reference/isolation readback.
- `host-gpu-check-2/Screenshot_1792773766.png`: subsequent RU home capture on the
  actual NVIDIA GTX1650Ti host GPU; guest SurfaceFlinger and Vulkan/GLES log confirm
  hardware rendering. Offline; same installed APK. The bounded check booted30.3s,
  ended around51s, and stopped the emulator. Earlier unattended SwiftShader run
  caused unacceptable laptop load; [incident/remediation](2026-10-23-laptop-thermal-diagnostic.md)
  records measurements and mandatory CPU/time/thermal limits for future runs.

Important correction from real rendering/call-site inspection: `CompactHome.java`
is present in the capsule but **not the installed FriendsActivity home layout**.
The active chain is `compactDashboardDial→DashboardLayout.compact/onMeasure`;
the dial remains above selectors/telemetry, not beside them. GTK now follows that
composition, with a bounded-width content area and retained native window controls.
Navigation uses exact RU **СТАТУС / ЧАТЫ / ПУТЬ / ОПЦИИ**, not invented long labels;
existing desktop statistics are retained under settings.

GTK captures are actual realized windows with a synthetic service **only in the test
harness**. Production code calls the installed private backend. Comparison confirms
the palette/rectangular thin frames/EXIT header/navigation and state text changes;
it does **not** establish overall visual parity. Remaining differences: telemetry
metrics/layout, map interaction/location, settings/support/voice controls and the
missing messenger. Exact Android CONNECTING/CONNECTED/RESTORING/error references
are still absent; those GTK states are not matched against a live Android session.
Wayland trials ignored the requested DPI and are **not DPI evidence**. Subsequent
X11 tests measure96/120/144 font DPI and device scale2; fractional-font tests are
not proof of GNOME compositor fractional scaling. Latest runs are
`gtk-mesh-r5-{1,1.25,1.5,2}.log` and adjacent screenshot directories:40 synthetic
state cases and60 real GTK captures. Later map-selection source correction (do not
show a stale AWG/TCP country for MESH) was not in those captures and has not been
rerun yet. No Windows screenshots or installed GTK MESH acceptance are claimed.

### Health/GTK continuation build checkpoint

This supersedes older phase counts below without replacing their evidence.
`desktop-gtk-mesh-r3.log`:363 Python desktop tests PASS;
`gtk-reference-tests-r2.log`:19 pinned-reference/Friends tests PASS. These are local
tests, not installed-product acceptance. Latest native source digest:
`4deb54f6009fe079a8dd620d065648a7b6c31c0c3793de9c7cd33e4840a4193d`.

| Internal artifact under `state-client-build/desktop-parity106-20261023/` | SHA256 | State |
|---|---|---|
| `bridge-linux-r7/fc-mesh` | `15001e9f5094f3a46f6709b3e4c2807c4ea1e583d3a73aaef901cf33b9786f8d` | Linux amd64 built; not installed |
| `bridge-windows-r5/fc-mesh.exe` | `27742e7219aeb96af350902ac1a72b738d4db90e24222dcf91e371c2287839b5` | Windows amd64 cross-built; runtime NOT_RUN |
| `mesh-system-r2/FamilyConnect-MESH-system-amd64.tar.gz` | `ca62d790e952830ef449084d1aea6bfcff913b00ddd23f62deb4e0c4c3588b83` | Unsigned internal component; not a complete desktop installer; not installed/published |

Versions remain Linux0.2.11/Windows0.2.15. No release/catalog/publication or identity
migration performed. Common RNS/receipt integration, full product/visual parity,
installed-system MESH and end-user packages remain open.

## SHARED_CORE / TESTS

Supported Go core preserves default P1/RS32, CREDIT128 negotiation, P0, certificate/
role/revocation/expiry/floors, bounded750ms reorder104, pressure drain105 and
diagnostic/lifecycle evidence. No tuning or server code deployment.

`carrier/desktopmesh`: real provisioned transport adapter, explicit platform-path
activation, cancel/close isolation, health102, readiness103 distinction and106
bounded JSON projection. These are library implementations, **not desktop VPN
integration**. Session tests use an explicit test plane; production has no fake
connection fallback. JSON projection is not a privacy filter or a full collector.

Evidence directory: `state-client-build/desktop-parity106-20261023/`.

- Reference verifier:175 shared files +2073 capsule files PASS; APK/native match.
- Python reference/contract/path-security tests:9 PASS.
- Existing desktop AWG/TCP/helper/updater suite:225 PASS outside sandbox. Initial
  sandbox result222 PASS/2 SKIP/1 socket-permission failure is retained separately;
  it is not a product regression or a successful physical-network test.
- Targeted Go race tests: health, profiles, cancellation, platform attachment,
  export, reorder and pressure PASS. Source test results retained separately.
- First full Go run: sandbox denied loopback; rerun outside sandbox. That run
  found a root-only stale150ms gap test. Updated it to accepted750ms+50ms, not
  transport tuning; original failed logs retained. Final full `go test -race
  -count=1 ./...` PASS:18 tested packages,3 packages without tests. Subsequent
  platform-cache split rechecked with `-race ./bootstrap ./desktopmesh`, PASS.
- Windows shared-adapter cross-build initially failed on Unix cache locking;
  moved the original Unix lock unchanged and made Windows plaintext cache
  fail closed. Second `GOOS=windows GOARCH=amd64 CGO_ENABLED=0 go build ./desktopmesh`
  PASS. This is **not** Windows UI/driver/installer/runtime acceptance.

## LINUX_RUNTIME / WINDOWS_RUNTIME

Both **product MESH runtime acceptances NOT_RUN**. Linux now has a real kernel
TUN/routing test, confined to a fresh network namespace. `fcmesh0` is created via
TUNSETIFF, assigned address/MTU, then closed to simulate loss of the packet device.
Kernel readback proves user IPv4 uses TUN, mark64640 uses underlying main, IPv6
is unreachable, and unmarked IPv4 stays unreachable after TUN removal. Exact
cleanup restores the namespace's original route. No systemd-resolved/native media
session was tested by this harness. Dummy eth0 is test-only; it is not a VPN PASS.

Runner: `scripts/check_desktop_mesh_routing.py`, requires root **inside** an empty
network namespace and rejects the host/initial namespace. Initial rootless attempts
were denied by user-namespace policy; sudo -n required authentication. Explicit
pkexec→unshare run passed, including a rerun of the checked-in hardened runner.
Evidence: `mesh-kernel-namespace-r3.log`. No host routes/resolver/firewall, installed
helper, SCM or existing client data changed. Live application budget remains
0/32MiB per OS. An available Windows machine has not yet been established.

## NATIVE_WORKER_AND_LINUX_SERVICE — continuation phase

`clients/mesh` contains the actual native service child, Linux TUN/fdbased and
Windows Wintun/channel packet adapters, strict96KiB/512KiB length-prefixed IPC,
one session per child, P0/P1 validation, private in-memory material, and staged
TRANSPORT_READY/PACKET_READY/routing acknowledgment. No fake production backend.
Linux SO_BINDTODEVICE+SO_MARK and Windows IP_UNICAST_IF protect native underlay
sockets; Windows driver installation is still not exercised.

Builds use accepted Xray commit `d2758a023cd7f4174a5a5fa4ff66e487d4342ba0`, exact
patch `eaeb30fd1e2aa52272d7f3a2a06bcad7b983ca9866a87fbd0a614eede6048872`, gVisor
`v0.0.0-20260122175437-89a5d21be8f0`, Go1.26.1, CGO0/default tags. Source digest for
both builds: `486459cd0e6646a2431c8c2946e5f8733e528ff133758601357deb82ca4d5024`.
`scripts/build_desktop_mesh.py` verifies the source inventory before/after build,
uses an isolated pinned/patch-checked Xray checkout, preserves logs and licenses.

Linux service source (`clients/linux/mesh_*.py`, `mesh-helper.py`, systemd unit)
adds a UID-authenticated private control socket, existing explicit pkexec setup,
one native worker, bounded recovery/history and strict route/DNS readback. A
root-owned journal contains only resource ownership. TUN crash leaves unreachable
defaults until explicit stop/owned cleanup. An authorization failure never tries
AWG/TCP; pending/fatal MESH keeps its guard until Stop. Existing AWG/TCP helper
startup is serialized against MESH. These copies must be installed together;
the existing machine's root helpers have **not** been overwritten.

Verification of this phase:
- Linux native `go test -race -count=1 ./...`: packet and worker packages PASS,
  one command package without tests. Real gVisor TCP/DNS tests use a synthetic
  authorized test plane/loopback, not an external MESH gateway.
- Actual Linux executable:6 bounded process/protocol checks PASS, including EOF,
  duplicate/oversized messages and invalid material rejection before networking.
- Desktop regression suite274 PASS outside sandbox; targeted IPC/route/recovery/
  authorization62 PASS, including late-positive-callback and unexpected-failure
  guards. Updated desktop adapter Go race tests PASS separately.
  Earlier225-test receipt remains historical phase evidence.
- Isolated real kernel TUN/rules/crash-containment PASS as described above.
- Windows full native worker cross-build PASS. First compile found missing named
  x/sys IP_UNICAST_IF constant; use the documented WinSock value31, no API bypass.
  Linux's first archive attempt needed network permission for a lazy pinned Git
  object. Failed/superseded build directories and logs remain preserved.

At that earlier phase, setup source, GTK MESH, readiness persistence and health
scheduling were absent; the continuations below supersede those source gaps.
Installed helper acceptance, service-restart intent, full diagnostics and user
functionality remain absent. Linux service mock tests
do not prove actual polkit/socket/systemd lifecycle or resolved cleanup.

## MESH_P1_AND_RECOVERY / SERVER_POLICY

### Readiness/materials + Linux backend/component continuation

The accepted Java readiness sources are now mapped in
`clients/shared/desktop-readiness106.json`; their hashes already belong to the
verified106 handler inventory. New supported Go code implements exact proof
goldens, bounded challenge/fetch, strict JSON, signed-material validation, cooldown,
transient-only usable-cache fallback, denial persistence, issuer/directory floors
and equivocation rejection. Real signed CA/certificate/CRL fixtures check expired,
revoked, wrong-device and wrong-anchor rejection. Local real HTTPS tests exercise
protected sockets, trusted TLS, untrusted TLS, redirects and cancellation during a
partial body; these are loopback tests, not gateway or live MESH acceptance.
The17-field receipt and authenticated ACK wire exist; durable ACK ownership and
the RNS relay adapter remain unwired, explicitly not a complete readiness parity PASS.

Native `--materials-stdio` is a one-operation, bounded private protocol. It returns
a byte-exact cache proposal+digest, **always durable:false**. Linux root storage
fsyncs/atomically replaces/reads back that proposal, including authorization denial,
then runs a second native cryptographic inspection of the actual disk bytes.
Only that transaction can supply a session. No identity seed is stored in the
cache. Strict file ownership/modes, symlink/hardlink/FIFO rejection, torn writes,
cancel and readback failure have targeted tests. No Windows plaintext-cache port.

`FriendsOwner.connect_mesh` uses the computer's existing identity without creation,
and sends it only to the private backend; tests compare old key/marker bytes after
the operation. `LinuxMesh` uses exact root-owned components and root SO_PEERCRED,
never starts a second GUI reconnect loop or silently disconnects another VPN.
Its connection request returns CONNECTING, not an invented CONNECTED result.
At that phase GTK/health were not connected. They are now wired as described below;
the full product UI and installed runtime remain unfinished.

The offline Linux system-component installer is implemented and packaged. It locks
the existing AWG/TCP/MESH owners, refuses active resources, updates existing helper
copies/modules together, backs up old own files, verifies the native source ID,
reloads units and publishes the capability marker last. Fault-injection tests
restore previous files and retain unrelated data. It does not start a service,
install new AWG/TCP engines, or change any identity/profile/history. **No real host
installation/upgrade has been run**; this is not the requested end-user AppImage/DEB.

New evidence under `state-client-build/desktop-parity106-20261023/`:

- `carrier-readiness-r1.log`: full carrier race18 tested packages +3 no-test PASS,
  including new real TLS/readiness/receipt checks and existing wire regressions.
- `bridge-linux-r6/test.log`: materials/platform/worker race PASS; command has no tests.
  The earlier r4 attempt hit sandbox-denied loopback and is retained, not hidden.
- `native-materials-process-r1.log`:7 checks of the exact built executable PASS,
  offline missing/denied/invalid/corrupt material, strict framing and metadata.
- `desktop-readiness-backend-r2.log`:331 desktop tests PASS outside sandbox, including
  those7 process checks. `linux-mesh-installer-r1.log`:10 installer checks are a subset;
  `linux-materials-r1.log`:66 IPC/material/service tests are an earlier subset.
- `friends-mesh-owner-r1.log`:3 existing/new Friends owner tests PASS using an existing
  environment whose control/identity/provisioning lockfiles all match installed versions.
  `parity-targeted-python-r3.log`:19 related reference/Friends/static contract tests PASS.
- Broad `python -m pytest -q` is **not green**: initial collection imports historical
  lab modules into the application namespace (42 errors). With `--ignore=tests/fixtures`,
  result1944 PASS/115 SKIP/10 FAIL/25 ERROR is retained. Most require explicit historical
  HTTP artifacts/toolchain environment; three isolated sync tests also failed. One
  directly related old literal MuxConfig assertion was adapted to the accepted bounded
  configuration's additional Policy/WaitForSlot/Lifecycle fields and now passes.
  This is not permission to alter historical fixtures or call the broad suite PASS.

Latest internal native workers share frozen source digest
`1165fddcd0d20c930cc5e1054b4b717a4e983faf68735a91315378c8ced08354`:

| Artifact relative to evidence directory | Bytes | SHA256 |
|---|---:|---|
| `bridge-linux-r6/fc-mesh` |28364606|`c2c108eec7e40bdc1a84d6a7dd09f5e44b1fe040e67718cd2ba42bc6ee000fb2`|
| `bridge-windows-r4/fc-mesh.exe` |28236288|`b21f7ac364687aac8e2d58b0e77eb9a70077d06e0c44b293dfecea7f897d9843`|
| `mesh-system-r1/FamilyConnect-MESH-system-amd64.tar.gz` |14125899|`e39c888226782a75d1ea662d098955e5d3299eb10f2bc4bbe59fcc05f41e924d`|

The system-component archive has a complete member digest manifest, dependency
licenses, bilingual instructions, installer source and `delivery.json`. It is
**unsigned**, not update-catalog signed, not an application release, not installed,
not physical-runtime accepted, and not published. It needs x86_64 Linux/systemd,
systemd-resolved/iproute2/polkit/Python3/TUN; it is not a new supported distro claim.
Windows remains an unsigned amd64 cross-build without bundled/accepted Wintun driver.
All earlier build directories remain immutable phase evidence, not replacements.

Installation when the later installed-product gate is ready: verify the above
archive and member manifest, extract locally, disconnect Family Connect, then
explicitly authorize `pkexec /usr/bin/python3 -I ./install.py` from its directory.
Do not run the GUI as root. Installation failure rolls back its own files; after a
successful upgrade, rollback is reinstalling the previous verified component while
disconnected. Preserve the printed root-owned backup for operator recovery.
No host/server/public rollback is currently needed because none was changed.
Linux0.2.11/Windows0.2.15, Android106, live sessions, P1 policy and public catalogs
remain unchanged; new live application traffic0 bytes on both OS budgets.

Android106's reported recovery106.578s is historical observation, not a desktop
timer or promise. Desktop both-end P1, TUN data path, recovery and cleanup are
NOT_RUN. Read-only local identity derivation + RU registration lookup found the
existing Linux owner **FC-3Y3W-EBZE**, device
`beafe2cd0e81140abb5f9e3d7c672551`; registration/invitation non-revoked, no explicit
restricted_grant row. Public identity binding verified without outputting keys.
Current Linux symlink: `releases/0.2.11-3aaf6e0661b5-67bcfb1a25b1`.

Fresh NL policy readback: active PID2374898, P1, exactly three Android targets,
group SHA256 `1cb942471c3d1349a4551b7acb922adc75e788549201a0cbabb764b72b858103`.
Linux's family-signing-key target `42f55d54ef48797b3e8428e3d22abce8` is absent.
This task did not restart the service; the current PID differs from the older
tester report and no cause is inferred. Initial read-only lookup used a relative
policy path as absolute; retry resolved it through the process working directory.

Operator action for later live P1: explicitly approve the exact existing Linux
identity and independently discover/verify the Windows computer's own identity.
The current gateway parser has a hard maximum of three targets/99 bytes, so
adding desktops requires a reviewed bounded policy-capacity change, **not** merely
appending an invalid fourth line or replacing an Android member. Preserve all
three existing members, auth checks and no-global-grant semantics. No such change
was made. This separate decision does not block client implementation/builds.

## IDENTITY_AND_UPGRADE / DELIVERY

Existing identity/storage/installer paths are untouched. This is non-mutation,
not a completed upgrade-preservation test. The existing Linux identity was only
read, not recreated/migrated. No new user package, installer signature, driver
signature verification or signed update manifest exists yet.
Existing download links/catalogs remain unchanged. New AppImage/DEB/compatible
archive and Windows installer require integration and artifact-level acceptance.
Never conflate offline update signatures with Authenticode or driver signatures.

Earlier development component delivery, retained immutable phase evidence,
**not current installers or private-test-ready clients**. Latest workers/system
component are listed in the continuation above:

| Internal artifact under `state-client-build/desktop-parity106-20261023/` | Bytes | SHA256 |
|---|---:|---|
| `bridge-linux-r3/fc-mesh` |28258837|`78a3e2966736fc701855c680944ee8af9261aa0c6bef21ec1dcf4da70a763675`|
| `bridge-windows-r2/fc-mesh.exe` |28130816|`6d01e49a66016e07a5672e2d27dd8b28dafd6958746fb5df794131c4a56aabdf`|

Each directory has `build.json`, `source-inventory.json`, dependency/license
inventory and logs. Targets Linux amd64/Windows amd64; no end-user supported-OS
range is newly claimed. Neither is update-catalog signed or Authenticode signed.
Windows Wintun DLL/driver must come from the existing pinned official packaging
flow; it is not included/accepted by the EXE cross-build alone.

Rollback: no installed/server/public state changed, so no operational rollback.
Source rollback must be path-selective using the reference's before hashes and
retained initial status; never reset/clean the user's uncommitted work/capsules.

## REMAINING_GAPS / next ordered work

1. Verify installed/pinned-provider RNS and finish full bounded UI export. Linux durable receipt/ACK
   owner is now connected and locally tested; installed/live ACK remains NOT_RUN.
   Linux refresh/cache/floors/readback and native health102 are connected.
   Preserve user intent across UI and backend
   restart; current Linux recovery retains it only while the service lives.
2. Run the built Linux component's install/upgrade and UID/socket/resolved crash acceptance; GTK
   integration acceptance, real Auto, remaining accepted UI, contacts/text/voice/
   notifications/support; ordinary-user launch and bounded physical tests.
3. Windows protected broker integration and same functionality; cross-build then
   native runner UI/SCM/DPAPI and physical Windows TUN acceptance when available.
4. Complete exact106 state references and GTK comparisons; WinForms captures are NOT_RUN.
5. Immutable private packages, upgrade-preservation evidence and hashes. Prepare
   catalogs/landing only; **publication requires a separate owner decision**.

## Readiness receipt continuation — local code/test/build, not rollout

Accepted106 `ReadinessProduct`/`ReadinessImportResult` semantics are now connected
through the shared native bridge to the Linux owner. Native offline receipt
generation validates exact17 typed fields; `ack` uses a separate signed challenge
exchange on the existing protected fixed HTTPS route, bounded to15s within startup.
No caller-selected executable, URL or shell operation was added to privileged IPC.

The owner atomically writes/readbacks `<uid>.receipt.json`0600 under its existing
root0700 directory, maximum4096B. It records UNKNOWN locally without prior cache
context, otherwise re-evaluates cache on service restart and sends a fresh restart
observation. An import first persists ACK_PENDING, then writes ACK_RECEIVED only
after the exact matching acknowledgment. Server acknowledgment and disk durability
are independent fields: a lost/failing final write leaves the disk pending and
reports `durable:false`. Failed refresh with usable old cache reports FETCH_FAILED,
not a fresh READY. Receipt/ACK failure does not revoke valid cache or create rights.
Cancel during ACK prevents returning materials to start a packet session.

Tests: `desktop-receipts-r2.log` **386 PASS**, including11 actual native offline
process checks; `reference-receipts-r1.log`19 PASS; `receipt-core-r1.log` desktopmesh
race PASS; `bridge-linux-r8/test.log` materials/platform/worker race PASS.
`reference-receipts-r1.json` rechecks175 shared and2073 capsule files. Local ACK
tests use injected bounded transports; no server/live ACK claim is made.
No GUI, physical TUN, installed upgrade or Windows runtime gate is newly satisfied.

Native source digest:
`9c298f38d4883dc63dafa62c67384accc90622333186b0d0e60b53b79cc66920`.
New artifacts under `state-client-build/desktop-parity106-20261023/`:

| Artifact | SHA256 | State |
|---|---|---|
| `bridge-linux-r8/fc-mesh` | `3be2bf1805f80337d896a5f4b939c226bed27acc7140b1bc52eaedfc182fccc0` | Linux amd64, built/race-tested, not installed |
| `bridge-windows-r6/fc-mesh.exe` | `3b482da7ac6341ec3b4417303db469a8b30f1e11ce65bd87c04e00004125fee8` | Windows amd64 cross-build, runtime NOT_RUN |
| `mesh-system-r3/FamilyConnect-MESH-system-amd64.tar.gz` | `7011310e5df67ebe64da81a0495fcf2cb97a4e5410572d7c7db5bc85bf979833` | Unsigned internal component, not installed/published, not an end-user installer |

Prior artifacts remain unchanged. No app version/catalog/identity changes; the
development receipt identifies Linux0.2.11 as `linux-0.2.11`/2011, not Android106.
Windows protected storage/integration is still open. Installed0.2.11 is untouched;
rollback is therefore not required. Later component installation must follow the
existing guarded own-file backup/rollback workflow, never delete identity/cache.
No live test data spent, new grant, Android operation, gateway restart or publication.
The continuing evidence JSON retains this as a new phase without rewriting old hashes.

## Intermediate owner checkpoint —23.10,19:28 CEST

Stage: Linux integration, after the shared-core baseline; full Windows broker/UI
integration, final visual/runtime acceptance and end-user packages remain ahead.
This is not PARITY PASS or a release candidate.

The next RNS materials adapter exists as unfinished source: the exact accepted
`fc_rns_transport.py`, a restricted Python worker, shared envelope validation and
the native Go child-process adapter. `rns-worker-python-r1.log` records67 passing
focused Python/materials/receipt tests, including fake-channel/socket checks;
these are not67 additional full-product tests and not a real RNS exchange.
The new Go relay has not yet been compiled/tested; its runtime packaging and
installer integration are unfinished. The receipt-phase386 tests and Linux r8 /
Windows r6 / component r3 artifacts remain evidence only for that earlier source
checkpoint, not the current RNS delta.

Both installed-product MESH acceptances, identity-preserving installed upgrade,
full messenger/support/export parity and Windows runtime remain unverified or
missing as listed in the matrix. No new AppImage, DEB or Windows end-user installer
is available. Versions stay Linux0.2.11 / Windows0.2.15; installed applications,
identity, public catalogs, Android and server policy are unchanged by this checkpoint.
No rollout occurred, so no rollback is required. Process inspection confirms no
emulator is currently running; this checkpoint starts no emulator, build or test.

## RNS native integration and packaged runtime —23.10 continuation

Supersedes the unfinished19:28 RNS checkpoint, not the outstanding product gates.
The accepted106 Python channel is copied byte-exact (SHA256
`70593713d1d915904d10cf0cac0eb21ca41b11b4dedcdb7973d0da236579ada0`), not the
older root Android module. The native materials transport now lazily starts its
fixed-provider worker on the accepted HTTPS challenge-network-failure branch.
TLS/auth denial cannot start it; an authenticated fetch is not replayed. Product
identity/proofs/cache validation remain in shared Go, not in a second Python/C# core.

Private IPC limits: four messages/process,8192B request body,90000B relay envelope,
131072B reply frame, shared deadline capped at200s. Linux binds/checks interface
and mark64640; Windows implements IP_UNICAST_IF readback but remains runtime NOT_RUN.
Cancel closes pipes and stops/reaps the child. Native scratch and Linux per-operation
scratch isolate temporary runtime/ephemeral RNS state and remove it on termination.
No product private keys are stored there or printed.

`scripts/build_desktop_rns.py` packages official unmodified RNS1.5.1/pyserial3.5
sources with RECORD checks, pinned channel, complete notices and source inventory.
Linux invokes fixed `/usr/bin/python3 -I -S`; no site-package or caller path is used.
The library's existing internal crypto provider is used for RNS only. Direct
zipimport in `rns-linux-r1` failed the actual-link test because upstream interface
discovery uses filesystem globbing; that attempt is retained and **rejected**.
The selected loader extracts validated/bounded members privately0700, without
modifying upstream source. `rns-linux-r2` and an independent `rns-linux-r3` rebuild
are byte-identical. Windows still requires its bundled embedded Python runtime;
the `.exe` below alone does not satisfy that requirement.

### Checks and limits

- `desktop-rns-r2.log`: **415 PASS**, including11 real native offline checks,
  installer rollback/runtime mismatch, strict worker/loader checks and an actual
  packaged RNS link. That link exercises all four readiness paths,8192B request,
  65536B byte-exact response, a second session and cancellation while awaiting
  another command with no private runtime/ephemeral files left behind.
- The local RNS peer uses test-only loopback bootstrap/socket callbacks. This
  proves actual library/wire/framing behavior, **not** the production pinned relay,
  protected physical interface, live ACK, Family TLS/MESH or system VPN.
- `bridge-linux-r10/test.log`: materials/platform/worker race PASS, including child
  deadline/reap and proof that TLS/auth/non-network failures do not launch RNS.
  `rns-core-r1.log`: shared desktopmesh race PASS.
- `reference-rns-r1.log`:19 PASS. `reference-rns-capsule-r1.json`:175 shared files,
  2073 capsule files and APK/native digest correspondence PASS. Signer unchanged;
  this phase does not claim a new APK signature verification or Android install.
- `mesh-system-r4/archive-check.json`: exact tar archive unpacked and all listed
  payload hashes plus native/RNS version metadata verified without installation.
- New `check_desktop_rns_underlay.py` is **NOT_RUN**: rootless namespace uid-map
  creation was denied; sudo/polkit require local admin authentication. This does
  not invalidate prior Go/service namespace checks or turn them into Python socket
  acceptance. When locally authorized, run only inside a new empty namespace:
  `pkexec /usr/bin/unshare --net /usr/bin/python3 "$PWD/scripts/check_desktop_rns_underlay.py" "$PWD/state-client-build/desktop-parity106-20261023/rns-linux-r2/fc-rns.pyz" "$(stat -Lc %i /proc/self/ns/net)"`.
  The script rejects the host namespace and touches no host route/resolver.
- All recorded build/test/package units use50% of one CPU, bounded lifetimes and
  an85°C stop guard, starting below70°C. Maximum sampled CPU in these units79°C.
  No emulator, live gateway request or bulk Internet test was started.

### Exact artifacts, not an end-user release

Directory: `state-client-build/desktop-parity106-20261023/`.
Native source digest:
`d1a40ff51a1a2a69dbf3b17f8e629b969ca7003be49a2aa1ddb99bfc27aaebe4`.
RNS runtime source digest:
`66128235484f01b82bfd2e4ad604a486428706fc48020abbf84211554edef26e`.

| Artifact | SHA256 | Evidence scope |
|---|---|---|
| `bridge-linux-r10/fc-mesh` | `013afb092c1087f2eff67056d34dd47466d2c734ca2d9f1666faaf61f0674abe` | Linux amd64 built/race/offline-process tested |
| `bridge-windows-r8/fc-mesh.exe` | `858cced8d8984f5b5dda96722643d25eda9b5b14d4f3861f304c0da075638068` | Windows amd64 cross-build only |
| `rns-linux-r2/fc-rns.pyz` | `61e7264459accc6a9a84ac18d11d19b5702cd537c718748d915e202540b0eeb2` | Actual local RNS exchange; reproduced byte-identically |
| `mesh-system-r4/FamilyConnect-MESH-system-amd64.tar.gz` | `08ea631bb6d947d7b06f0f370b18db18440851c0bf0305a0b8484374213805be` | Unsigned internal Linux component,14994947B; verified unpacked, not installed |

Local Python execution: Linux7.0.0-38 x86_64 / Python3.14.4; this is not a new
supported-OS release matrix or Ubuntu24.04 installed acceptance. No AppImage/DEB/
Windows application installer, update-manifest signature, Authenticode signature
or driver artifact was created. App versions remain Linux0.2.11/Windows0.2.15.
Existing installation/identity/catalogs, Android APK/devices, gateway and server
rights are unchanged; live application budget stays0/32MiB per OS. There is no
operational rollout to roll back. A later installed component update must use its
guarded own-file backup/rollback and preserve all existing user stores.

Next: installed Linux helper/RNS/UID/socket/resolved and upgrade checks, persisted
recovery intent, actual Auto and complete UI/messenger/support/export; then Windows
embedded runtime/broker/UI, native acceptance and full private installers. Full
visual/runtime/identity-upgrade gates remain open: **NOT PARITY PASS**.

## Interim control — Linux backend-restart implementation,23 October

Current stage is Linux integration, before Windows broker/UI integration and full
visual/runtime/package acceptance. No finished parity installer exists for either OS.

New working-tree code retains connection intent/materials in anonymous memfd memory
owned by the existing systemd service manager across backend restart. The root-owned
runtime record contains only schema, UID, generation, desired and recovery count,
not private keys. Explicit Disconnect revokes the memory record before cancellation;
network-guard retention/reconciliation and lost-socket stop handling are implemented
but their latest combined regression is not yet recorded. This requires systemd254+;
it does not claim cold-reboot autoconnect or create an identity migration.

`state-client-build/desktop-parity106-20261023/intent-systemd-r1.log` records
**1 PASS in3.39s** against a real isolated user-systemd unit: SIGKILL/restart restores
synthetic materials; revocation followed by another SIGKILL/restart does not restore
them. This is a manager/memory lifecycle check, not root-service/TUN/live VPN recovery.
Its thermal receipt records exit0,50% CPU quota, peak sampled CPU68°C and no guard
stop. No emulator or new test/build was started during this interim status audit.

The prior **415 PASS** regression, Linux r10/Windows r8 native workers and unsigned
`mesh-system-r4` component remain evidence for their recorded earlier source state;
they do not validate/package the latest helper/intent changes. Next: finish those
regressions and rebuild the internal component, then installed helper/RNS/routing/
resolved/upgrade acceptance and the missing actual Auto, messenger, support/export
and UI functions. Windows broker/WinForms/embedded runtime, physical OS acceptance
and complete private AppImage/DEB/Windows installers remain outstanding.

Versions stay Linux0.2.11/Windows0.2.15. No new install, signing, publication, server
grant, Android change or gateway restart; existing stores and public artifacts are
unchanged. There is no new deployed version requiring rollback. Installed upgrade
and identity preservation remain unverified, not inferred from unchanged files.

## Linux recovery and user-visible support/export —23 October

This phase supersedes the unfinished recovery checkpoint above. It adds a working
GTK product operation, not just another transport test; overall parity remains
**IN_PROGRESS**, with no finished end-user installer on either OS.

### Implemented source and bounded behavior

- Finalized memory-only service restart intent, revocation-before-cancel, owned
  guard retention/reconciliation and lost-socket Disconnect handling. Requires
  systemd254+. No key copy to a new disk file; no cold-reboot autoconnect claim.
- `FriendsClient.support_id` uses the existing authenticated `support` purpose and
  `/friends/device/support`, with this computer's identity and Linux version2011.
  `FriendsOwner` caches only public alias/registration metadata atomically0600,
  rejects mismatched/unsafe/corrupt caches and never creates keys while reading or
  refreshing support. Failed refresh preserves a valid cached ID. No live support
  request or server mutation was made during development; API tests use local fixtures.
- GTK settings now exposes **About / Diagnostics**, refresh/copy Support ID and
  **Send diagnostics → privacy confirmation → Save JSON**. This is a native GTK
  save operation with user-selected destination, not silent online upload. Failure
  or cancellation does not affect the connection. The six-file archive layout is
  retained: collector code is in the existing `backend.py`.
- The collector exports a complete parseable `ring`/optional `incident` envelope,
  preserving common Android field names, selected versus negotiated values, native
  startup/session data, health/readiness summaries, first failure, bounded lifecycle
  and four-session history. Public code/counter projection excludes arbitrary text,
  URLs, private material and messages. Rejected fields/events and native/service
  losses are counted. First/latest detail and first failure survive size trimming;
  an unrepresentable record fails export instead of byte-truncating JSON.
- Limits match106:262144B per record and525312B per bundle. UI-restart history/
  incident storage is atomic0600 inside a0700 user-state directory. Export includes
  OS/architecture, actual installed core metadata when available, and reports missing
  metadata rather than substituting an uninstalled development binary's version.
  Online support opt-in/TTL/upload, exhaustive native-field projection parity and
  installed/live collection remain open; this is not full diagnostic PARITY PASS.

### Verification and actual windows

Evidence directory: `state-client-build/desktop-parity106-20261023/`.

- `diagnostics-final-r1.log`: **452 desktop tests PASS**, including actual isolated
  systemd crash/revoke, native offline process and packaged RNS checks; **46 identity/
  Support ID/reference tests PASS**. The identity checks preserve both original
  private-key byte sequences and initialized marker, reject a copied other-device
  support cache, reject duplicate JSON and preserve the cached ID on HTTP failure.
- Export tests cover real negotiated values, first failure, health, secret injection,
  nonfinite/boolean counters, event/history bounds, restart, valid bounded JSON,
  omission accounting, atomic-write failure and symlink rejection. Accepted106
  startup/trace enum values remain projectable. Full raw native DTO coverage still
  needs review; dropped projection fields are disclosed, not silently treated as full
  native evidence.
- `diagnostics-render-final-r2-{1,1.25,1.5,2}/`: actual GTK/Xvfb windows, RU/EN,
  clipboard readback, keyboard focus, Escape/privacy cancellation, actual GTK save
  chooser callback and resulting private JSON.100/200% use device scaling;125/150%
  use font DPI, **not compositor fractional-scaling acceptance**. Service/network
  state is synthetic; these screenshots do not prove VPN connectivity or a live
  Support ID response. No application/traffic destination is included in the JSON.
- `mesh-ui-diagnostics-final-r1/`: previous connect/cancel/stale-callback interaction
  checks pass after integration; actual RU/EN windows for five states, route/settings
  and wide/long-error layout are retained. No real VPN is started by this test.
- Compared support section to unchanged106
  `reference-emulator/Screenshot_1792771564.png`: same section/control names, amber16
  title,14px body and thin-line controls. Full settings composition/order, other
  product screens and physical Windows rendering still differ or are missing.
  A mixed-language transient copy notice found in rendered QA was corrected and
  checked again; it is not hidden by editing screenshots.
- Initial UI check failed because Xvfb was absent; a subsequent portal-driven test
  could not programmatically select its file. Final tests use an isolated D-Bus
  config with the real GTK fallback chooser, not a mocked chooser. GNOME portal
  integration remains outside this test. A200% fixture state race was also fixed
  by making the synthetic polled service consistent; earlier failed logs are kept.
  Xvfb2:21.1.22-1ubuntu1 was downloaded from the configured Ubuntu repository and
  extracted locally, not installed system-wide. Package SHA256:
  `d430679ffd9864f0c29c7b1edd434b42aa37ad3f622a7f58a76f62cef7e86ba4`.

All heavy jobs use50% of one CPU, hard lifetimes and85°C stop guards. Final tests/
packaging sampled peak68°C; the recorded display regression sampled67°C. No Android
emulator was launched. The approved GPU-backed emulator workflow remains available.

### Exact internal delivery and remaining acceptance

`mesh-system-r5/FamilyConnect-MESH-system-amd64.tar.gz`,15005984B:
SHA256 `3d8ecb58a5ab79095f0de31e789b831a554510b3b7871101e44ed8a6540e65d3`.
The exact tar is unpacked and all payload bytes/manifests are verified before the
delivery receipt. It includes the current helper/intent/guard changes, but is **not
the GTK application installer**. Linux amd64 component; systemd254+, Python3,
resolved/iproute2/polkit/TUN prerequisites remain. Not installed, not published,
no update-manifest signature, no installer signature and no new driver artifact.
Native Linux r10/Windows r8 and RNS r2 bytes are unchanged; the current native-source
digest independently still matches `d1a40ff51a1a2a69dbf3b17f8e629b969ca7003be49a2aa1ddb99bfc27aaebe4`.

Versions remain Linux0.2.11/Windows0.2.15; no public catalog, installed identity,
Android device/APK, gateway or P1 policy was changed. Live application budget remains
0/32MiB per OS. No new deployment exists to roll back. Future component installation
must occur disconnected through its explicit privileged installer; failure rolls
back only its own files, retaining the previous installation and user stores.

Next: installed Linux helper/RNS/UID/socket/resolved and exact upgrade/runtime tests,
complete native diagnostic projection, actual Auto and contacts/text/voice/
notifications/online-support; then Windows broker/embedded runtime/WinForms, native
OS acceptance and complete private installers. Unavailable admin/Windows checks do
not block continued source/product work and are not replaced by unit-test counts.

## Owner progress audit —23 October,21:14 CEST

This is a read-only implementation/evidence audit apart from these documentation
updates; no new build, test, emulator, installation, network or server action ran.
The previous25–30% estimate has no defined weighting/acceptance denominator and
is not repeated as a measured completion figure. Current stage: Linux integration,
after the shared transport baseline, before Windows product integration and final
visual/runtime/package acceptance.

Since the19:28 checkpoint, RNS integration/runtime packaging was locally tested,
restart intent and cancellation were regression-tested, GTK Support ID refresh/copy
and private JSON saving were implemented and rendered, and component r5 was built
and unpack-verified. The20:57 `diagnostics-final-r1.log` records452 desktop tests
and46 identity/support/reference tests. Exact component digest and limitations
remain as recorded above; this is not an end-user installer or live MESH PASS.

The latest21:11 source-only delta consolidates7 production messenger modules and
one regression-test file from the accepted capsule; all8 hashes match
`clients/shared/android106-messenger.json`. Its test run is still pending. GTK
messaging remains a placeholder; no working contacts/text/voice UI is claimed.
The earlier498 passing tests must not be attributed to this later source change.

Outstanding product gates: actual Linux Auto, complete messaging/voice/notifications,
online diagnostic consent/upload and full native export projection; installed
Linux TUN/MESH/P1/recovery and identity-preserving upgrade; Windows protected
runtime/broker/WinForms integration and native-OS acceptance; full visual parity
and private AppImage/DEB/Windows installers. Windows remains cross-build only.
Versions remain Linux0.2.11/Windows0.2.15; no new rollout or rollback operation,
signing/publication, Android change, gateway restart or policy mutation. No emulator
process was found during this audit. Overall PARITY remains NOT COMPLETE.

## Linux messenger: real contacts/text owner and GTK —23 October,21:56 CEST

The21:14 source-only messenger checkpoint is superseded. This phase changes
working product code, not only the matrix. It does not complete Linux/Windows
messenger parity, installed MESH acceptance or an installer release.

Read-only owner recheck22:03 CEST: existing logs directly confirm611 PASS/13 skips,
478 PASS/no skips and17 focused PASS; the isolated actual Secret Service restart
result is PASS. These overlap and are not new test executions. Windows frontend
worktree remains unchanged, emulator process count is0, and the15MiB r5 internal
component remains the20:57 artifact, not an end-user installer. No new version,
rollout, rollback action or completion percentage is established by this audit.

### Source and behavior

- `clients/shared/android106-messenger.json` pins12 accepted source/test files
  against the106 inventory. The one shared adaptation in `messenger/routed.py`
  lets a trusted platform subclass name normal OS routing SYSTEM. Default
  Android route order is unchanged; the exact patch is retained. No Android file
  or installed APK was modified and no laboratory implementation was imported.
- `provisioning/chat_owner.py` opens the existing Friends identity read-only and
  owns a separate encrypted chat identity/history, explicit creation versus resume,
  an exclusive process lock and strict identity-bound metadata. Corrupt, oversized,
  duplicate, boolean-schema or other-device metadata never triggers recreation.
  The key lives in Secret Service; unavailable/locked/nontext existing entries
  cannot be overwritten, including during creation. Keyring calls are bounded15s.
- `chat_transport.py` uses accepted RNS/LXMF, the authenticated existing chat
  registration and≤120s node lease. Authorization/invalid replies disable an old
  lease; transient refresh failures may retain a still-valid one. Refresh of an
  unchanged node keeps the carrier instead of unnecessarily replacing it. No
  caller-provided endpoint, privilege change, shell command or route exemption.
  SYSTEM follows the OS route, including an existing VPN; it is **not** protected
  underlay or restricted SERVICE_ONLY parity.
- GTK now has explicit start, own card/public-key clipboard, full-key preview,
  independent fingerprint confirmation, contacts, rename, text queue/edit,
  encrypted history and unread counts. Twenty-five labels are verified verbatim
  against accepted RU/EN resources. The card order is address→grouped fingerprint→
  public key. Relay acceptance and signed recipient-storage receipt are distinct.
  Local operations and registration use separate single-flight workers, so slow
  registration does not disable the composer or prevent offline queueing. Closing
  joins registration and delivery before releasing the encrypted store; stale
  completed callbacks cannot redraw a closing window.
- Corrected the initial matrix's unsupported word “block”: the accepted
  ChatActivity, bridge operation signatures and LocalChat expose add/rename/trust,
  not a contact-block handler. No implemented Android function was removed from
  the scope. Voice/radio, notifications/service events and other remaining screens
  still have explicit unfinished entries.

### Checks, rendered windows and limits

All paths below are under `state-client-build/desktop-parity106-20261023/`.

| Evidence | Result and scope |
|---|---|
| `messenger-core-r1.log` |148 accepted-core regressions PASS before Linux owner integration; not full product acceptance |
| `chat-wire-r1.log` |Actual loopback closed RNS mailbox, two shared-core participants, byte-exact Unicode text, signed recipient-storage ACK, cancel and interface cleanup PASS; not a physical Android/desktop pair |
| `chat-regression-r1.log` |611 PASS,13 explicitly gated native/systemd skips; targeted suite, not the whole repository |
| `chat-desktop-final-r2.log` |478 PASS with explicit native worker/RNS artifacts and user-systemd gate enabled; no skips; overlaps the previous suite |
| `chat-safety-ui-r1.log` |15 then-current safety/reference/assembly tests plus existing actual GTK MESH/cancel and diagnostics/save regression PASS; synthetic service, no VPN |
| `chat-final-r5.log` |17 latest safety/wire/reference/assembly tests PASS; then four actual GTK runs PASS |
| `chat-final-r5-{1,1.25,1.5,2}/` |44 actual PNGs, RU/EN, verified GdkX11Display/Xvfb, trust/copy/send/edit/rename/draft navigation, encrypted identity/history reopen and queueing while registration is deliberately pending |
| `keyring-final-r11/result.json` |Actual isolated libsecret/GNOME Secret Service, background caller, durable same-key read after service restart with distinct verified D-Bus owner PIDs; missing key not created; raw/base64 key absent from files |

Numbers overlap and must not be added into a completion percentage.100/200% use
device scaling;125/150% use font DPI, **not compositor fractional scaling**.
GTK scenarios use disposable synthetic identities and a memory-vault fixture;
the real Secret Service boundary is independently checked on its own private
D-Bus/HOME/XDG directories. No real user keyring, identity or live server was used.

Visually inspected the unchanged106 empty-chat screenshot
`reference-emulator/Screenshot_1792772253.png` against the new real GTK welcome
screen: same EXIT header, title, notice, welcome text, primary action and navigation
order. Card/verification/conversation windows are also captured, not inferred from
CSS. Full chat menu/thread/composer placement, contact previews, service notices,
voice controls and Windows visuals remain different/missing; **VISUAL PARITY is
not passed**. No emulator was started. Earlier exploratory captures inherited
Wayland; final runs explicitly require X11 and record actual device scale.

Retained failed attempts: an incorrect expected string-count assertion, GTK frame
timing/focus-fixture issues, and isolated keyring restart checks. The keyring test
initially exceeded AF_UNIX control-path limits; short owned runtime paths fixed
that fixture. A subsequent check proved the old libsecret convenience proxy could
remain stale after service restart while a fresh service read the same key.
Production now opens its own bounded service session per request; final restart
test passes without generating a replacement key. No failing run is erased or
relabelled. Heavy jobs use50% of one CPU, finite runtime and85°C stop guard; broad
regression peak73°C, final GTK67°C, final keyring63°C. All are terminal.

### Packaging, identity and remaining work

Full Linux bundle assembly now includes an explicit messenger/owner/UI module
allowlist, pinned LXMF1.1.1 and the existing complete Reticulum/LXMF/PySerial notices;
DEB declares `gir1.2-secret-1`. An extracted first-party source bundle imports with
the existing pinned test dependencies. This is **not** a fully vendored installer
or installed-package test. The six-file legacy archive remains six files and does
not by itself deliver the new runtime; its full-bundle upgrade transition remains
a gate. No old installed chat/Device Identity was migrated or deleted.

Versions remain Linux0.2.11/Windows0.2.15. No new end-user AppImage, DEB or Windows
installer, signature, catalog change or public link. The prior unsigned internal
MESH component r5 and native r10/r8 artifacts are unchanged. No Android change,
gateway restart, P1 grant, live transfer or rollout; budget remains0/32MiB per OS.
There is no new deployed version to roll back; installed upgrade remains NOT_RUN.

Next: finish Linux voice/radio, notification/service-event/background lifecycle,
restricted message delivery and exact chat composition, alongside actual Auto/full
diagnostic collection and installed helper/TUN/upgrade gates. Then Windows
broker/runtime/WinForms and native OS acceptance, followed by complete private
installers. Windows physical runtime remains NOT_RUN; the original two-client
objective and all explicit acceptance gates remain open.

## Linux voice and Radio —23 October continuation

This continues the same two-client task, not a separate audio product or a new
calling feature. `clients/shared/android106-voice.json` pins nine actual accepted
Java/native/reference files, verified against the2073-file capsule inventory.
The supported shared messenger wire/crypto files remain unchanged by this phase.

### Implemented source

- `provisioning/chat_audio.py`: fixed application-owned GStreamer pipelines,
  mono Opus/Ogg16kHz/12kbit/s and Codec2 1.2 public shared-library API at8kHz.
  Codec2 mode mapping, frame padding and peak8191 normalization match the accepted
  JNI implementation. There is no codec rewrite, ARM library copy, external
  pipeline/command input, real microphone test or new cryptography.
- Capture≤60s, encoded≤131072B; short recordings<400ms rejected. PCM/drafts stay
  in bounded memory; conversion runs off GTK. Decode has its own output/deadline
  bound. No temporary audio file. Buffers are cleared best-effort, not a promise
  that Python/GStreamer memory copies are securely erased.
- `chat_voice.py`: hold/release→preview, slide-left cancel, slide-up lock,
  keyboard recording, pause/seek, explicit Send, stored-message playback and
  navigation/Escape/close cleanup. Generation guards suppress stale completions;
  close joins audio before closing history. Output-device removal/change stops
  playback; actual PulseAudio/PipeWire/headphone acceptance is still NOT_RUN.
- Existing ChatOwner now exposes the accepted validated audio operations.
  An additive encrypted `desktop-voice-v1` record retains the selected mode and
  separately confirmed Codec2 peers. Default Opus; confirmation never grants
  VPN/P1 permission or replaces contact fingerprint verification. Existing keys,
  history schema, account binding and metadata are not replaced.
- Source packaging includes the audio/UI modules and runtime-boundary notice;
  DEB declares GStreamer/Codec2 dependencies. The new Linux CI workflow uses an
  isolated system-GI venv, audiotestsrc/fakesink and Xvfb. It is source only and
  has not been remotely run/pushed. No new end-user package, signature, catalog,
  Android build, server restart, policy change or live-data budget consumption.

### Visual and remaining scope

Actual GTK recording/preview windows are captured in RU/EN at100/125/150/200%.
100/200% use device scale;125/150% remain font-DPI checks, not compositor scaling.
Thin rectangular controls and reference labels are used. A recording preview was
visually inspected, not inferred from CSS. Full Android conversation/voice reference
screens are not yet captured; exact composer/menu/profile placement differs, so
this is **not VISUAL PARITY PASS**. Hardware capture/playback/unplug, physical
Android exchange and installed upgrade remain NOT_RUN. Notification/service-event
and background delivery, restricted service-only delivery, Auto/full diagnostics,
Windows counterpart and complete packages remain in the original objective.

Retained failed runs include EOS handling in the initial player bus reader,
an incorrect owner argument/contact shape, exceeding the relay's unchanged
four-token burst in a test, snapshot-frame timing, and real pointer interaction
failures. Tests now use independent bounded wire scenarios rather than weakening
the relay limiter. Actual X11 input found that child button activation could treat
a short click as keyboard recording; parent-capture gestures distinguish pointer
and keyboard activation. All unsuccessful evidence is retained, not relabelled.

The extended input test also found that a periodic history refresh could disable
and rebuild the held control, cancelling recording, and that disabling the record
button at finalization lost keyboard focus. Background snapshots now avoid making
the conversation insensitive; rebuilding waits while an unsent recording is active.
The ready preview receives focus, and Escape cancels audio even if a separate owner
operation is pending. A delayed-start callback is explicitly tested after navigation
to ensure it cannot revive recording or overwrite the new screen.

`voice-final-r5` exited0 but printed an uncaught GTK callback error during the
text regression; it is **not accepted as a clean run**. A history response from
the previous conversation reached the contacts screen. Snapshot requests now
capture address/offset/view revision; stale/hidden-screen results are discarded
and current visible state is refreshed. Read marking occurs only after accepted
rendering, not a stale fetch. Both GTK runners now fail on uncaught callback
exceptions, and the text check deliberately delays history across navigation.
The pending180ms hold is protected from a background rebuild as well as recording
itself. These are lifecycle fixes, not weakened assertions or skipped input checks.

### Final local evidence and unchanged delivery

All paths are under `state-client-build/desktop-parity106-20261023/`:

| Evidence | Result and exact scope |
|---|---|
| `voice-final-r4.log`, pytest step |497 PASS/no skips, explicit native/RNS/user-systemd gates enabled; its later GTK failure is retained and is not a full-run PASS |
| `voice-final-r4.log`, reference step |175 supported shared files and2073 capsule files PASS, including pinned voice source mapping; no APK rebuild |
| `voice-final-r6.log` |34 final codec/owner/wire/reference/source-package tests PASS, followed by a clean text GTK regression and four clean voice GTK runs; no uncaught callback traceback |
| `voice-final-r6-{1,1.25,1.5,2}/` |36 real PNGs plus result/actual input event records; all four codecs, preview/pause/seek, explicit send, encrypted reopen, persisted Radio confirmation, stale-start suppression, hold/release/cancel/lock and Enter/Escape |
| `voice-text-regression-r4/` |11 PNGs and PASS result; contact/card/clipboard/text/edit/rename/drafts and deliberately delayed history across navigation |
| `voice-final-r6.thermal.json` |101.04s, CPUQuota50%, peak61°C,180s hard limit, no thermal stop; no emulator or physical audio device opened |

Counts overlap; do not add them or infer product completion. New CI workflow is
prepared only, NOT_RUN remotely. Actual local codec runtime versions and licensing
boundaries are recorded in the dependency audit. Source/test/screenshot hashes are
in the appended `LINUX_VOICE_RADIO_AND_INPUT_LIFECYCLE` evidence phase.

Linux remains0.2.11, Windows0.2.15. No new AppImage/DEB/Windows installer was built,
signed, installed or published. Existing internal component r5/native r10/r8 bytes
are unchanged; no installed identity migration or rollback was attempted. No
Android, active MESH, gateway, user grants, catalogs or public links were changed.
Live application budget remains0/32MiB per OS. Next required Linux work is background
delivery/notifications/service events and exact accepted chat/settings composition,
then the remaining transport/diagnostic and installed gates, Windows integration
and complete private packages. The full objective remains active.

## Owner progress control and visible GPU rerun —23 October,22:45 CEST

Readback confirms `voice-final-r6.log`34 focused checks PASS and all four final
GTK voice results PASS. These are existing results, not new test executions or a
completion percentage. Work remains in Linux integration; Windows frontend,
installed system TUN/P1/recovery/upgrade acceptance and full installers are open.
Versions remain Linux0.2.11/Windows0.2.15; no build, signing, installation,
publication, rollback, policy or identity operation in this control turn.

At the owner's request, the unchanged offline106 AVD ran in a visible window with
NVIDIA GTX1650Ti rendering verified inside Android. Prior KVM/2-core/150% CPU,
180s lifetime and85°C CPU/80°C GPU guards retained. Boot30.2s, final sample122.1s;
sampled CPU peak81°C/GPU61°C, CPU82°C immediately after stop. Home screenshot
visually inspected; this is reference capture, not desktop visual parity.
The whole emulator unit stopped with MainPID0. Evidence:
`state-client-build/desktop-parity106-20261023/reference-emulator/host-gpu-check-3/`;
launcher `reference-emulator/launch-host-gpu-check-3.py`. No software GPU fallback,
APK rebuild/reinstall, phone interaction or live application traffic.

## Linux notifications, service history and hidden-UI delivery —23 October,23:10 CEST

### Accepted source and implementation

`clients/shared/android106-notifications.json` pins8 accepted files against the
same2073-file106 inventory: ChatRuntime/ChatNotifications/ChatDeliveryService/
ChatActivity/TerminalToggle and shared feed/notices/store code. Accepted shared
sources are unchanged. The Python owner performs the platform adaptation; no
parallel crypto, new entitlement or public event publisher is introduced.

- `ChatOwner.tick` now distinguishes visible UI from enabled background work.
  Other tabs/minimization no longer suspend the authenticated lease/mailbox.
  Expiry, denial and transient-valid-cache rules remain; mailbox polling15s on
  success/60s after error, enrollment retry60s. Actual local closed RNS delivery
  while `visible=False` and encrypted notification receipt/reopen are tested.
- Existing chat state resumes on GUI launch without implicit creation. The
  additive encrypted `desktop-delivery-v1` preferences retain identity/history;
  failure never substitutes a key. Complete Quit still joins/stops this owner:
  **independent closed-app/crash-resilient delivery is not implemented yet**.
- Notification IPC is only the user's session D-Bus, never a privileged helper.
  Eight in-flight posts,64 tracked notifications,3s calls, no arbitrary command/
  URI action. Daemon replies acknowledge API acceptance, not visual presentation.
  Error/unavailable/disabled notification paths retain pending flags. Replaced
  daemons, navigation/cancel and late-close replies cannot acknowledge the wrong
  notification. Personal edits and public-event revisions fence both notified
  and read updates. Reading requires a displayed conversation in a focused window.
- There is no portable desktop private lock-screen view equivalent to Android;
  OS notifications omit contact names, message text/audio and service titles/bodies.
  They use accepted generic RU/EN labels and grouped unread counts. Clicking an
  opaque known notification ID opens its verified conversation/service history.
- The fixed HTTPS public feed is Linux-filtered by the unchanged validator;
  no credentials/redirects, identity encoding only,1,000,000-byte bound,8s network
  timeouts/16s chunk-loop deadline,30s cadence. Failed refresh keeps cached valid
  events. Signed LXMF notices still require separate pinned publisher authority;
  downloading a public feed never grants this authority or operator rights.
- Service history is newest-first and paged50 entries at a time, with actual
  accepted kind/title/body/expiry/platform/build/revision/author metadata. Update
  notices navigate to existing Settings, never execute content. The accepted
  role-checked announcement list/publish/edit UI was identified and explicitly
  added as a separate remaining row in the feature matrix; it is not silently
  treated as implemented by this read-only history screen.

### Real windows and regression evidence

Native GTK switches use the accepted TerminalToggle mint/amber, capsule and thin
frame values rather than the desktop theme's orange checkboxes. Native switch
accessibility/focus remains; real XTest Space/Return/Tab changes persist. Actual
render inspection also found asynchronous chat content left the window at its
previous small height: the completed owner callback now requests the existing
coalesced window fit. Long notices render/readably scroll instead of being confined
to a tiny pre-load viewport. This is not a claim of complete visual parity:
navigation/composer/operator screens still have documented gaps, and matching
Android notification/settings screenshots have not yet been captured for this set.

| Evidence under `state-client-build/desktop-parity106-20261023/` | Scope/result |
| --- | --- |
| `notices-final-r1.log` |167 related tests PASS/no skips, actual codecs/closed RNS/recovery flags/shared messenger checks; source integrity175/2073 PASS; first full GTK/text/voice batch PASS |
| `notices-final-r2.log` |50 focused tests PASS/no skips and175/2073 source checks PASS; four updated native-switch/D-Bus GTK runs PASS |
| `notices-final-ui-r3.log` |Final post-layout-fix GTK/D-Bus runs at1/1.25/1.5/2 plus text/voice regressions PASS, no uncaught callbacks |
| `notices-final-ui-r3-{1,1.25,1.5,2}/` |24 PNGs/result JSON; signed LXMF receive→encrypted inbox→real session-D-Bus fixture ACK→GTK action, privacy/disable/visible-peer/replacement/late-reply checks, empty and long RU/EN service views, keyboard |
| `notices-final-text-r3/`, `notices-final-voice-r3/` |11 text and9 voice PNGs; existing contact/text/edit/draft/stale-navigation and actual codec/input regressions PASS |
| `notices-final-ui-r3.thermal.json` |exit0,62.02s,CPUQuota50%, peak65°C; no thermal stop or emulator |

Counts overlap:167 and50 are not additive or a product completion percentage.
100/200% use actual device scale1/2;125/150% vary font DPI, not compositor
fractional scale. The notification daemon is an isolated D-Bus fixture, not the
user's GNOME/KDE popup service. Screenshot inspection includes the final100% long
service view and200% RU switch/focus view. Synthetic audio only, no real microphone.
Remote CI workflow is updated but NOT_RUN; only public PNG/result files are uploaded
by that workflow, not synthetic identities/stores. Full package source assembly
closure is tested; it is not an installer or installed-upgrade test.

Earlier failures are preserved, not reclassified PASS: `notices-unit-r2` had an
already-consumed mock HTTP stream and incorrect test relay-role name; corrected
fixtures preserve transport quotas. `notices-unit-r3` caught original message
revision0 being compared as1, allowing stale acknowledgement after the first edit;
the production receipt/read fence now distinguishes personal0 from service1.
`notices-final-r1/r2` screenshots predate the final switch/layout adjustments.

### Unchanged delivery and remaining work

Linux0.2.11/Windows0.2.15 and native r10/r8/component r5 remain unchanged. No new
AppImage/DEB/Windows installer, signature, installed migration, catalog, public link
or rollout/rollback operation. Do not roll back by deleting user state/keyring;
existing installation is untouched. Android APK/capsule, active MESH/gateways,
other-user policies and P1 permissions are unchanged; live application budget
still0/32MiB per OS. Own desktop P1 approval remains a separate operator action,
not implied by this local messaging work.

Next: independent closed-app delivery and accepted announcement management,
restricted service-only delivery and exact chat/settings layout; actual Auto/full
native diagnostics and online-support consent; installed Linux TUN/P1/recovery/
identity-preserving upgrade; Windows broker/runtime/WinForms and available OS
acceptance; full private packages. Host notification-popup/installed acceptance,
physical audio/Android pair and physical Windows remain NOT_RUN. Full parity
remains INCOMPLETE, not blocked on these checks for further local implementation.

## Independent Linux chat owner —23 October continuation

### Implemented, not installed

`chat_daemon.py` now owns the existing `ChatOwner`, encrypted store, Secret Service
key, mailbox, feed and OS notification adapter in an ordinary user-session process.
GTK uses `chat_client.py`; Quit detaches rather than stopping enabled background
delivery. No additional identity, root daemon, privileged networking or replacement
messenger implementation. Disabled background and no GUI exits after30s idle;
absent/locked store with no GUI also has a60s idle bound. Session bus loss stops
the owner. Production systemd failure restart is5s, limited to3 starts per120s.

`chat_rpc.py` exposes a fixed same-UID session API, with strict command/argument
validation,262144-byte requests,1048576-byte responses,8 pending operations,
4 independent clients and15s visibility leases. Public summaries omit inbox bodies;
service history is paged50 at a time. Mutation replay uses up to64 encrypted,
120s request tickets, committed pending before the change. Completed requests can
replay their result; an interrupted commit/result boundary returns an explicit
unknown outcome, never repeats the send. GUI errors explain checking history before
manual retry. Existing identity binding/key/history remain intact on restart.

The full-bundle launcher supports `--chat-service`. AppImage startup reopens the
original image to avoid depending on a closed GUI's mount. Notification actions
open only an opaque verified peer/service route in a separate GUI user unit;
the existing invitation handler and single-instance mechanism remain. Source
assembly includes all new modules; DEB adds systemd/session-D-Bus dependencies.
No full installer was built by this phase. See [ADR004](../adr/004-linux-chat-session-owner.md).

### Runtime evidence

- Final `chat-service-runtime-r5.log`:75 targeted tests PASS/no skips,175 supported
  shared files and2073 capsule files verified, then a clean repeat of the independent
  service scenario after the window-fit change. Actual GTK MESH state/profile/cancel
  and diagnostics/privacy/save regressions also PASS, with synthetic VPN state.
  This final batch took89.04s, peak74°C, parent50%/child25% quotas; unit-after-stop
  is inactive/MainPID0 and subsequent manager listing has no remaining fixture units.
  Current-source service/MESH/support screens add21 PNGs to the44 UI-regression PNGs:
  65 total, not65 accepted Android-equivalent states. There is no new live VPN test.
- `chat-service-runtime-r4.log`:74 targeted tests passed, followed by an actual
  isolated user-systemd/Secret Service/session-D-Bus/loopback RNS scenario. GTK closed;
  the separate owner received a new message and posted a content-free notification.
  SIGKILL caused a new service PID with the same profile/history. A fixture crash
  after queue commit but before RPC result did not duplicate the message on replay.
  Reopened real GTK showed both messages. Background disabled + detached GUI stopped
  the owner; final unit readback inactive/MainPID0.71.03s, parent CPU quota50%,
  child quota25% bound to the parent unit, peak71°C, no thermal stop.
- The production worker code has no crash-injection commands. The synthetic crash
  hook exists only in the explicitly excluded test worker. The isolated bus uses
  Type=exec because the real user manager cannot watch its private D-Bus name.
  Production Type=dbus and fresh installed-window activation remain NOT_RUN.
- `chat-service-ui-r2.log`: four GTK/D-Bus runs at100/125/150/200%, text and voice
  regressions passed,44 PNGs.100/200% are actual device scales;125/150% are font DPI.
  These legacy UI fixtures inject a local owner; the two separate service-check
  screenshots exercise the actual remote owner. Neither fixture proves installed
  host notification-popup acceptance or full reference composition parity.
- Earlier `chat-service-runtime-r1` failed because Type=dbus watched the wrong bus;
  r2 failed from an overlong Unix keyring socket path. The corrected fixture uses
  a short private temporary socket directory, verifies the keyring's actual PID,
  and stops all children. Original failure logs are preserved.
- `chat-service-ui-r1` and layout-r1/r3 exposed a real window-size race: a late GTK
  configure replaced the requested default size with the old small size while the
  cached target still said746. The final fit waits until after the frame paints,
  measures the whole window and retains outer width, including client decorations.
  It does not compensate by removing the height assertion or enlarging screenshots.
  Failure PNGs/geometry receipts are retained; a focused coalescing/geometry test
  now covers this scheduling boundary. Final UI run66.03s, peak76°C at50% quota.

### Unchanged deployment and remaining gates

Linux0.2.11, Windows0.2.15, native r10/r8 and component r5 are unchanged. No new
end-user AppImage/DEB/Windows installer, signature, catalog, public link, installation,
Android rebuild, gateway restart, policy grant or real-user-state modification.
External application test budget is still0/32MiB per OS; all new mailbox exchanges
used loopback and synthetic identities. Installed upgrade/rollback is NOT_RUN;
never delete user history or keyring entries to switch versions.

Next required Linux work remains announcement-admin UI/API, restricted service-only
delivery, exact composer/settings layout, actual Auto/full native diagnostics and
online-support consent, production user-service activation/upgrade handoff and
installed system TUN/P1/recovery/identity-preserving update. Windows broker/runtime/
WinForms integration and full private packages are still required. Physical Windows
runtime remains NOT_RUN. This phase advances the original two-client objective;
it does not redefine it as Linux chat completion or claim overall PARITY PASS.

## Owner progress control —24.10

Readback only; no additional product implementation, version, package, signature,
deployment, policy change or live application traffic in this control. Current
stage remains Linux integration. Windows has a cross-built shared worker, not the
required new broker/WinForms product integration. Full AppImage/DEB and Windows
installer acceptance are still open; Linux0.2.11/Windows0.2.15 remain unchanged.

The subsequent announcement implementation is present in the working tree:
authenticated role-checked administration, explicit preview, publish/edit, stable
retry identities and revision-conflict handling. Evidence read back from
`state-client-build/desktop-parity106-20261023/announcements-final-r2.log`:
156 tests PASS and175 shared/2073 capsule source checks PASS. Four result files in
`state-client-build/desktop-parity106-20261024/announcements-final-r2-{1,1.25,1.5,2}/`
report PASS. These are real GTK windows using a private D-Bus owner and synthetic
server/identity fixtures; Android announcement visual comparison is explicitly
NOT_RUN. Fractional runs use font DPI, not compositor fractional scaling.

The overall batch exited2: the regression loop invoked the nonexistent
`clients/desktop/chat__check.py`. Notification/text/voice/MESH/support checks after
that point did not execute. Correct that command and run those steps; retain the
failed receipt. Do not call the complete batch PASS or count prior overlapping
tests as new coverage. Thermal receipt:52.02s,CPUQuota50%,peak74°C,no guard stop.
No emulator process was present at this readback.

Remaining delivery gates include actual Auto, complete diagnostics/online consent,
restricted service-only chat, exact remaining screen composition, installed Linux
MESH/P1/recovery and identity-preserving upgrade, Windows integration/runtime and
full private packages. No measured whole-task percentage is available: stage
counts, test totals and elapsed time do not establish one.

## Linux announcement administration —24.10 final local checkpoint

### Implemented product path

The accepted `ChatActivity.java` and `FriendsAccessAndroid.java` handlers, strings,
server authorization/notice code and shared feed format are pinned in
`clients/shared/android106-announcements.json`. This is a minimal desktop adapter,
not a copy of experimental Android sources. `chat_admin.py` uses this computer's
existing challenge/proof. `chat_owner.py` and the bounded same-UID D-Bus interface
expose list/publish/edit; GTK's service-notices toolbar opens the same list → compose
→ explicit preview → submit sequence. No local role grants or cached-role bypass.

New notices preserve information/all-three-platforms/30-day defaults. Edits retain
author, timestamps, expiry, kind and audience; revision/request ID enforce conflict
and replay behavior. Stable IDs survive preview/back/language changes and explicit
retry after a lost reply. No automatic write retry. Role revocation after preview
is enforced by the actual server code. Stale list callbacks cannot replace another
screen. Archived administrative entries remain visible, unlike expired public-feed
items. Both normal permission denial and unavailable service have explicit UI.

Bounds match the accepted contract: title160/body4000 UTF-16 units,50 events/page,
1MiB list response,16KiB challenge/write responses,32KiB write request. The new
adapter requests identity encoding and rejects encoded responses before reading
or decompressing them. Existing non-announcement Friends calls retain their
behavior. Tests prove challenge as well as final API rejection without consuming
the encoded body. No proof/private keys/tokens or server error bodies appear in UI.

GTK uses the accepted back/menu toolbar, exact RU/EN labels, input placeholders,
thin borders and preview hierarchy. Body entry has3–6-line height; UTF-16 clipping
happens before oversized insertion. Full-bundle packaging includes the new modules;
legacy six-file compatibility is unchanged. This does not complete the pending
full-bundle updater transition or produce an installer. CI workflow adds API and
four-scale announcement checks; no remote CI run/push was performed.

### Final evidence and visual scope

- `announcements-final-r5.log`:166 targeted tests PASS/no skips,175 shared/2073 capsule
  source checks PASS, then four actual GTK/private-D-Bus announcement runs PASS.
  Only the existing PyGI deprecation warning remains in the test step.
- `announcements-final-r5-{1,1.25,1.5,2}/`:44 PNGs; separate owner process and actual
  server proof/role code through in-process MockTransport. Synthetic identities and
  memory vault only; no sockets, real roles or publication. Checks cover denied/
  allowed list, explicit preview without write, lost reply/no duplicate, revision
  conflict, unchanged expiry/audience, later revocation, UTF-16, Enter/Escape and
  stale callbacks.100/200% are device scales;125/150% are font DPI only.
- `announcements-regressions-r3.log`: successful notification/text/voice, MESH
  cancel/profile and support/native-save regression after correcting the command
  that expanded to `chat__check.py` in r2. These45 PNGs have their own fixture scopes;
  synthetic VPN results are not real TUN/P1 evidence.
- Visually inspected actual RU compose at100% and EN edit preview at200%. Controls,
  wrapped text and navigation fit those windows. Android announcement-screen
  screenshot comparison remains NOT_RUN: source/layout review is not that comparison.
- Final phase89 PNGs; r5 took49.02s,peak75°C and r3 took52.02s,peak63°C, both quota50%
  and no guard stop. No emulator. Failed r1 startup and r2 command receipts remain
  in place. Intermediate165-test security run is not added to final166 as new coverage.

Paths: logs/thermal receipts remain under
`state-client-build/desktop-parity106-20261023/`; final UI directories are under
`state-client-build/desktop-parity106-20261024/`. The continuing evidence JSON
appends a tenth phase with final source, result, log and screenshot SHA256 values.

### Delivery boundary

Linux0.2.11/Windows0.2.15 and native r10/r8/component r5 are unchanged. No new full
AppImage/DEB/Windows installer, signature, catalog, installation, production
publication, Android rebuild, gateway restart, identity migration or policy grant.
Live application test budget remains0/32MiB per OS. Installed upgrade/rollback,
exact Android announcement visuals and Windows runtime remain NOT_RUN.

Next work is actual Linux Auto/capabilities, full diagnostic projection/online
consent, restricted service-only chat, installed service/upgrade/TUN/P1/recovery;
then Windows integration and full private packages. The original two-client goal
remains INCOMPLETE. Announcement completion does not imply overall PARITY PASS.

## Shared Auto policy —24.10 final local checkpoint

### Implementation, not a new UI selector

`carrier/desktopauto` implements the accepted orchestration policy once in Go for
both desktop hosts. `clients/shared/android106-auto.json` pins six exact accepted
Java sources and the policy parameters. The host interface preserves the Android
division: install blocking ownership/configure authorized capabilities; open an
actually ready path; block before candidate teardown; release only on explicit
Disconnect. No packet transport, RS, RTP, crypto or P1 grant was reimplemented.

Order is last successful configured normal, preferred configured normal, remaining
configured normals, then restricted/MESH. Restricted-only has no normal fallback;
MESH never replaces the normal hint. Deadlines remain30s configuration,20s normal,
200s restricted,300s series. One immediate restoration pass,30/60/120s backoff with
bounded0–5s jitter, third temporary-bootstrap failure cooldown300s, reset after120s
stable traffic. Permanent bootstrap failure and authorization/configuration/internal
failures retain a failed state/guard rather than silently falling back or cycling.

Desktop adaptations: serialized operations, service-owned monotonic generations,
cooperative context cancellation/deadlines, bounded detached snapshots,128 events
with first reason and drop counter. Explicit Disconnect cancels then drains the
old operation before cleanup; stale generations cannot stop a newer session.
Ready publication is fenced against late cancel, including during hint storage.
Go certificate/TLS validation errors remain terminal even when a URL/network
wrapper would otherwise classify them as retryable. Only stable categories enter
events, never raw errors, addresses, credentials or payloads. Platform cleanup
watchdog is supplied separately and capped60s; it is not a network-timer retune.

This library is not wired into a service or GUI yet. Existing Linux helper chaining
is insufficient because MESH owns an exclusive routing namespace and AWG/TCP
cleanup is independent. A cross-transport guard and narrow service-only underlay
socket path must survive configuration, handoff, cancellation and crash. Do not
enable Auto by removing the guard, allowing general endpoint/DNS bypass or renaming
TCP. Service-restart ownership/generation persistence is also a host requirement,
not something the in-process race tests establish. These are the next required
implementation steps, not external blockers.

### Exact reference and tests

`scripts/check_desktop_auto_reference.py` compiles the unchanged accepted pure-Java
`ConnectivityOrchestrator.java` and `Transport.java` with a synthetic Host. It does
not build an APK or contact a phone. Against the Go host fixture,17 scenarios and
160 event/final-state records match exactly: order, normal/MESH fallback, terminal
failures, offline waiting, temporary/permanent bootstrap, deadlines, cancel,
restoration, stable reset and cleanup failure. The resulting trace fixture is
pinned by SHA256 and checked by ordinary Go tests without needing the capsule/JDK.

- Final `auto-core-r5`:21 top-level Go tests repeated5 times with `-race`;130 pass
  events include repetitions/subtests and are not130 unique tests. No failure/skip.
  Additional tests cover concurrent snapshots/cancel, stale generations, bounded
  events, no late READY and nine wrapped TLS-validation variants.
- The same final run passes16 Python reference tests,175 shared/2073 capsule
  checks, the Windows amd64 policy-test cross-build and a fresh17/160 Java comparison
  in `auto-traces-r5`. Related `desktopmesh`/`restrictedowner` race checks passed in
  the earlier r2 run; no code in those packages changed here.
- `.github/workflows/desktop-auto.yml` prepares Linux/Windows policy tests and
  Linux race coverage. Remote CI was not run. Physical Windows remains NOT_RUN.
- r2 hit its180s cgroup lifetime during the cold Windows test build after its race
  steps passed. It is retained as timeout, not full PASS. Later bounded builds
  completed. Trace r1/r2 javac failures were locale/US-ASCII; explicit UTF-8 fixed
  invocation without modifying any accepted source. Stderr and failed logs remain.
- Final48.02s,CPUQuota50%,peak77°C,no thermal stop or emulator. No new GUI/screenshots;
  synthetic guard flags and policy traces are not system TUN or leakage evidence.

Internal cross-build only:
`state-client-build/desktop-parity106-20261024/auto-core-r5/desktopauto.test.exe`,
SHA256`325633f93a8e075da2788bdf56b94e8852a72469a66bd2f56c780a412b8427bf`.
This is an unsigned Windows amd64 Go TEST executable, not a native VPN worker,
installer, driver, supported-OS declaration or runtime acceptance artifact.
Logs/thermal receipts are in the23.10 evidence directory; traces/test output are
in the24.10 directory. The continuing evidence JSON appends phase11 with exact hashes.

### Unchanged delivery boundary

Linux0.2.11/Windows0.2.15, worker r10/r8 and component r5 are unchanged. No full
AppImage/DEB/Windows installer, signature, installation/upgrade, public catalog,
Android rebuild, gateway restart or user-policy change. Application live budget
remains0/32MiB per OS. Overall parity remains INCOMPLETE. Next: actual Linux Auto
host/IPC/guard/capabilities, remaining diagnostics/consent/service-only chat and
installed acceptance; Windows integration and complete private packages remain
mandatory, not replaced by shared-core tests.

## Linux Auto cross-transport traffic guard —24.10 final local checkpoint

This continuation changes real root-internal Linux firewall code, not a new GUI
button or synthetic policy host. `clients/linux/auto_guard.py` implements the
owned `inet family_connect_auto` table without changing other tables, the system
resolver or any route. It is **not yet wired into a product Auto coordinator**.
The original two-client task remains INCOMPLETE.

### Implementation and boundary

- Output and forward default-drop persist through configuration, attempts and
  recovery. Root-only, exact-mark/endpoint transport exceptions do not let an
  ordinary application bypass via the gateway or external DNS. DHCP and narrow
  IPv6 discovery are separate control-plane allowances, not general IPv6 access.
- Planned-interface probe is root-only. Ready pins interface name **and index**,
  removes that probe allowance and rejects MESH IPv6. The host still owes actual
  authentication, route/DNS/health checks; a firewall state is not CONNECTED.
- Block precedes cleanup. Prepare/release refuse an existing candidate TUN;
  release deletes only the complete verified owned table. No global flush or
  general established-connection exemption. VPN forwarding and tracked replies
  are supported only while ready; blocked/probe closes forwarding too.
- Root0700 directory,0600 single-link/no-follow journal, exclusive process lock,
  persistent generation/table comment and exact rule/chain readback protect
  ownership. Unknown table/rule changes are not adopted or deleted. State intent
  precedes one atomic nftables batch; both possible outcomes are recognized after
  a lost reply/commit. Restart always reconciles to blocked, not old ready.
- Command input/output are bounded64KiB with5s subprocess limits. Existing
  AWG/TCP/MESH helpers and Go policy are not changed. No external caller can send
  shell commands/nft expressions through this component; product IPC is still
  required. The root coordinator must serialize its calls and preserve intent.
- Kernel readback correctly handles nft's numeric protocols/conntrack state,
  implicit protocol dependencies and interface-name/numeric-string rendering.
  Interface-index resolution uses stable before/after kernel inventory, rather
  than dropping the pin during comparison.

[Detailed contract and remaining integration](../clients/DESKTOP_AUTO_GUARD.md).
The implementation currently covers the existing helper-backed AWG/TCP/MESH
interface families. It does not add a NetworkManager/WG host or prove non-root
network-manager DHCP compatibility. Existing manual capabilities are unchanged;
future Auto must filter and then implement actual supported capabilities, not
silently relabel one transport or claim omitted paths are complete.

### Exact local checks

`auto-guard-final-r1` PASS:214 Python cases,0 failures/errors/skips, including45
guard cases and169 reference/existing MESH/AWG/TCP/authorization/profile/installer
checks. Source verifier PASS175 shared/2073 capsule; Go `./desktopauto` PASS.
The JUnit receipt is
`state-client-build/desktop-parity106-20261024/auto-guard-final-r1/pytest.xml`.
This is targeted regression coverage, not the complete repository test suite.

`auto-guard-kernel-r9` and `r10` each PASS the same44 checks on the real local
Linux7.0.0-38-generic kernel with nftables1.1.6, isolated from the host network.
The Docker engine was verified local (`unix:///var/run/docker.sock`, matching
hostname). Existing image digest:
`sha256:0eb939a49d18b66c080a3de35e9fa6403d5d8947779590a8dac857a0e026f820`.
The image has no nft binary: the exact host nft executable/libs are mounted
read-only and run only inside that empty network namespace. It has no Internet
interface. Public-format test addresses terminate in its TUN descriptors, not
at a public DNS/server. No APK, identity, profile, SFU, gateway or real session is
used. Host network inode4026531833 differs from test inode4026532690.

Packets demonstrate ordinary IPv4/IPv6 DNS blocking, root-only service access,
exact TCP mark/endpoint and AWG UDP endpoint, no user gateway bypass, blocked
handoff, privileged probe versus unprivileged pre-ready denial, actual ready TUN
delivery, forwarded data and replies, MESH IPv6 denial, interface-name reuse
denial, no stale root probe, owner exit/restart retention, established forwarding
closure, explicit cleanup/restoration and retention of an unrelated nft table.
Root filesystem checks reject symlinks, hardlinks, permissive journal/directory,
oversized journal and unsafe lock. They are not installed product/driver tests.

The kernel runner has0.5 CPU,256MiB,32 PIDs,45s inner deadline and removes only
its own nonce-labelled container on cancellation/exit. No host network or
privileged-container mode. The outer laptop thermal watchdog remains active.
R9 elapsed7s/peak62°C; r10 elapsed6s/peak62°C. Final unit/reference/Go elapsed7s,
CPUQuota50%,peak71°C. No thermal stop; no emulator or surviving test container.
The repeated runs are44 unique checks, not88 distinct tests. The new CI workflow
is prepared only; remote CI and wider distribution/kernel coverage are NOT_RUN.

Earlier r1/r2/r4/r5 exposed exact nft JSON representation mismatches and were
fixed in code without weakening ownership comparison. R3 exposed a test
assumption: a filtered nonblocking TCP connect can return EINPROGRESS. The check
requires absence of its SYN at the TUN, not an immediate socket error. R7 exposed
numeric strings after interface deletion; r8 counted permitted background IPv6
neighbor discovery as a test packet. The final harness matches protocol,
destination, ports and payload/SYN. These failure receipts remain retained;
r6 is an earlier narrower PASS, not the final source acceptance.

### Delivery and next step

Linux0.2.11/Windows0.2.15 and existing workers r10/r8/component r5 are unchanged.
No new native build, installable package, installation/update, signature, catalog,
public link, screenshot, Android rebuild, real identity or server policy change.
Live application budget remains0/32MiB per OS. This guard is not added to an
installer prematurely and there is no instruction to run the GUI as root.

Next: connect the Linux root Auto coordinator and Go policy through authenticated
bounded IPC; protect underlying bootstrap/media/DNS sockets through each routing
mode; enforce capabilities and full readiness; then GTK and installed acceptance.
Complete diagnostics/online consent/restricted chat and all Windows/product/
visual/identity-upgrade/private-package gates remain in the original scope.

## Native Auto IPC and shared MESH attempt —24.10 continuation

### Implementation and actual boundary

`clients/mesh/automatic` connects `carrier/desktopauto` to the native worker's
`--auto-stdio` entry point. This is32KiB length-prefixed UTF-8 JSON, exact lowercase
keys, duplicate/case-alias/null/unknown-field rejection, monotonic safe-integer IDs,
one active callback and no arbitrary commands, paths, credentials or raw errors.
The shared Go controller retains its accepted timers/order/recovery. An immediate
Disconnect cannot race ahead of Connect generation initialization. Cancellation
waits for host ACK/drain; a missing ACK closes the channel after20s rather than
overlapping cleanup or a new attempt. Status remains responsive during callbacks.

`clients/linux/auto_policy.py` supplies the root-only private-pipe parent and
`GuardedHost`: acquire before configure, planned transport check before opening,
ready after platform readiness, block before close, explicit verified release.
Child exit/EOF/protocol failure cancels the current operation, blocks and closes
the platform but does not silently release the firewall. These private pipes
authenticate the parent/child relationship, not a future GUI/service client.
The product coordinator must still own persistent generations, authorize the
external socket and contain an uncooperative host process; a Python thread cannot
be killed safely. No product Auto listener or fake active selector was added.

The real MESH candidate adapter is `clients/linux/auto_mesh.py`. The packet
lifecycle extracted into `mesh_service.PacketSession` is also used by the existing
manual supervisor, not a separate transport/crypto implementation. It resolves
materials through the real native/cache/floor owner, starts the real packet worker,
attaches/verifies routes and DNS, sends routed ACK and waits for native health.
Auto's adapter uses the remaining caller deadline, has no retry thread and returns
the verified interface index with IPv6 unsupported. Health loss is reported to its
owner. Cleanup failure prevents another attempt/release; cancellation prevents a
late READY. Diagnostic reads do not wait behind a connecting operation. Manual
supervisor timers/recovery remain unchanged. The adapter is not yet called by a
complete product Auto coordinator. Protected normal configuration, AWG/TCP real
capabilities/handoffs and installed lifecycle remain open.

### Verification, including retained failures

- `auto-ipc-go-r3`:11 top-level Go protocol tests,5 repetitions with race detection,
  PASS. Includes early cancellation, late host reply, cleanup failure, stale IDs,
  no-ACK termination, strict JSON and bounded diagnostics.10.01s, peak62°C.
- `auto-ipc-final-r1`:560 desktop/reference tests PASS, no skips, with explicit
  native worker, packaged RNS and isolated user-systemd flags. Includes22 Auto MESH,
  24 policy-parent,45 guard and41 manual-service cases. One existing PyGI
  `GLib.unix_signal_add_full` deprecation warning, not a failure. Source integrity
  PASS175 supported shared/2073 capsule files.25.01s, peak77°C.
- `auto-policy-kernel-r2`:18 checks PASS against the exact Linux r13 worker,
  Python root parent and actual isolated nftables/TUN. Non-root packets, recovery
  to a replacement interface, cancellation waiting for ACK, late readiness,
  offline restore/Disconnect and native death/retained guard are exercised.
  The transport is a synthetic platform, not live AWG/MESH or a product service.
  No host network change or external traffic.11.01s, peak61°C. Earlier r1 passed
  the same18 checks using pre-hardening r12; it is not final-source acceptance.
- Build Linux r13: package/race checks PASS,36.02s, peak63°C. Windows r9:
  cross-build only,381.18s, peak78°C; physical Windows/driver acceptance NOT_RUN.
- Retained: Linux r11 timed out at its240s process limit after package tests had
  passed; no binary was accepted. R12 subsequently built, then was superseded by
  exact-key protocol hardening/r13. `auto-mesh-unit-r1` had1 failed/172 passed:
  the deadline test mutated a copied context field instead of advancing time.
  Corrected to advance the test clock; r2 passed174 cases and final full run560.
  Its measured peak79°C and the r11 peak82°C are not hidden by final-run numbers.

Tests/builds retain50% CPU quota and85°C thermal-stop guards. No emulator was
started for this work. These counts overlap earlier phases; do not add them into
a completion percentage. Workflow `.github/workflows/desktop-auto-bridge.yml` is
prepared locally; it has not been pushed or executed as hosted Windows CI.

### Exact component delivery, not complete installers

Both native builds have source digest
`82bd57bad2a0ef10e1e56f3faa99f64d4a6f5f7c05c0854f3a769b77f368bcef`, accepted
Android106/native105 reference, pinned Xray revision and no experimental build tags.
All paths below are under `state-client-build/desktop-parity106-20261024/`:

| Artifact | SHA256 | Scope |
|---|---|---|
| `bridge-linux-r13/fc-mesh` | `77a8d5f96825eb1588db9073cc86237f3a53322e10002e1a4376ebc56a73941b` | Linux amd64 worker; local checks, not installed |
| `bridge-windows-r9/fc-mesh.exe` | `3ea4ba679fc703482cb618651e610cbab74d3dda0acd0cd0350b62b9c314c45a` | Windows amd64 worker; cross-built, runtime NOT_RUN |
| `mesh-system-r6/FamilyConnect-MESH-system-amd64.tar.gz` | `2753a4920021d0baca16c2bbc57a961db7843bd2f82b39c7f2a9520fceb11d7c` |15064519-byte unsigned Linux internal component, archive/member readback verified, not a full desktop installer |

The component includes the unchanged verified RNS r2 runtime and the current
Python service/guard/policy/MESH adapter source. `build.json`, dependency/source
inventories, licenses, member `manifest.json` and `delivery.json` accompany these
artifacts. No update-manifest signature, installer/Authenticode signature or new
driver signature is claimed. No AppImage/DEB/Windows full installer was produced.
Component installation and root-service runtime acceptance remain NOT_RUN.
No installation occurred, so no installed rollout/rollback action is needed;
existing component installer own-file rollback logic remains covered by tests.

Versions remain Linux0.2.11/Windows0.2.15; Android106, active sessions, identities,
public downloads/catalogs and server grants are unchanged. Live application bytes
remain0/32MiB per OS. No UI screenshot or visual/physical acceptance is claimed.
Next: product root Auto coordinator/configuration/normal transports/durable intent,
then GTK activation and installed acceptance; full diagnostics/consent/restricted
chat, Windows broker/UI, visual/state-upgrade checks and complete private packages
are still required. This phase is not PARITY PASS.

## Protected normal configuration and existing-helper attempts —24.10 phase14

### Implemented source, not full Auto activation

`carrier/desktopmesh/normal_configuration.go` and `normal_http.go` reuse the accepted
signer/challenge and shared protected underlay. Fixed normal origin/paths, canonical
identity and WireGuard binding, bounded HTTP, signed catalog domain/floors, strict
response binding and cancellation are enforced. No unprotected network fallback,
cached normal authorization or additional desktop grant is introduced. Native
`clients/mesh/normal` exposes one-operation `--normal-stdio`; AUTHENTICATED_RESPONSE
does not mean a ready VPN. P0/P1 negotiation and restricted cache semantics are
unchanged. The175 accepted shared files remain exact.

`auto_configuration.NormalOwner` reuses the existing full Friends profile validator
before an atomic common-catalog floor commit/readback and native revalidation.
Root floor files exclude assigned TCP credentials and WireGuard private keys.
`FriendsOwner.connect_auto` validates this computer's existing key/marker/country
floors and hands them over in memory without an unprotected GUI HTTP call or
identity recreation. The future product `backend.start_auto` is not yet present;
the UI does not call/enable this incomplete workflow. Root→user high-water-floor
synchronization before later manual updates also remains unfinished.

`auto_normal.NormalCandidate` plus `auto_normal_worker` supply real helper-invoking
AWG/TCP attempt source, not a new crypto/transport implementation. A generated
interface/endpoint/generation is journaled before private profile creation. The
worker requires the inherited root guard's actual locked open-file description;
independent same-path fds, foreign profile ownership and arbitrary commands fail.
Fixed existing helpers retain their parser, engine, route/DNS/health and teardown
paths. Only original helper health plus TUN/index/type checks can return ready.
User IPv6 stays blocked unless separately proven, rather than bypassing the VPN.
The parent enforces the common attempt deadline and reaps its subprocess group;
cleanup retains containment on error. Generation-owned deterministic temporaries
allow partial-write cleanup without touching other profiles. Root profile files
keep the existing Linux0600 model, not a new plaintext Windows identity store.
Existing manual starts now refuse Auto guard or residual normal journals; component
setup likewise refuses either journal, including broken symlinks, without requiring
a TUN to be present. The internal MESH
owner can receive the same checked guard. No actual helper/service was installed.

The product coordinator, real capability filtering, underlying discovery, complete
handoff/recovery ownership and authenticated GUI socket are still required.
See [native configuration protocol](../../clients/mesh/normal/README.md) and
[Linux adapter contract](../clients/DESKTOP_AUTO_NORMAL.md). CI is prepared, not
remotely executed; no push was performed.

### Exact verification and retained failures

Receipts are under `state-client-build/desktop-parity106-20261023/`:

- `auto-normal-go-r2`: carrier desktopmesh race tests×3 and normal/automatic native
  tests×5 PASS,26.01s, peak57°C. Protected-socket refusal tests do not connect to
  an external gateway. All requests use synthetic identities/catalogs.
- `auto-normal-owner-r1`:64 targeted owner/catalog/configuration checks PASS,
 3.00s, peak61°C; existing key/marker/cache bytes remain unchanged in fixtures.
- `auto-normal-vectors-r1`:36 existing catalog vectors passed through the actual
  r14 native inspect process plus the shared Python full profile validator.
  This is signature/schema compatibility, not fresh live device authorization.
- `auto-normal-final-r1`:737 Python desktop/reference/Friends checks PASS, no skips,
  one existing PyGI deprecation warning;175 shared/2073 capsule source integrity
  PASS.29.01s, peak62°C. JUnit is under the24Oct `auto-normal-final-r1/` directory.
  Includes43 candidate/lease/cleanup tests,36 native vectors,16 normal-owner tests
  and6 existing-identity handoff tests. These overlap earlier runs; do not add
  counts or interpret them as whole-product completion percentages.
- Final `auto-normal-final-r2`:744 PASS/no skips, same single existing warning and
 175/2073 integrity PASS;27.01s, peak60°C. Includes46 normal-candidate tests and
  four new installer pending-Auto checks. This final run covers the final component
  source; JUnit is under the24Oct `auto-normal-final-r2/` directory.
- Candidate/helper OS operations are synthetic. A real child process is reaped on
  deadline and actual file locks are tested, but no installed AWG/TCP/MESH runtime,
  gateway egress, physical recovery or identity-preserving upgrade is proven here.
- Final `auto-normal-package-readback-r2`: r8 archive/digest,87 member readback and
  root-module imports using Python `-I -S` PASS. No cryptography/httpx/RNS/GI module
  is imported by this isolated root normal path.2.00s, peak62°C. Earlier r7/readback-r1
  remain verified historical outputs, superseded after installer/manual-start
  handling of residual Auto journals was hardened; neither was installed.

Failed attempts remain: candidate-r1 had13 failures/22 errors/74 passes because
test profiles used documentation-only addresses, correctly refused by the public
gateway guard. Tests now substitute a synthetic public endpoint without opening
network connections. Candidate-r2 had12 failures/97 passes because tests expected
Failure instead of the existing strict ProtocolError/ValueError. Tests were fixed,
not validation weakened. Candidate-r3 passed113 checks; final-r1 includes additional
interrupted-write cases. Peaks stayed≤79°C; CPU quota50%, no thermal stop or emulator.

### Component delivery and unchanged rollout

All artifacts below are under `state-client-build/desktop-parity106-20261024/`.
Both native workers have284 matching current source hashes and digest
`b2b39619ff4db035583a0a79c2d30fd210f33e61fc2ba9315710e892c1399637`.
Pinned Xray patch/revision and accepted Android106/native105 remain unchanged.

| Artifact | SHA256 | Actual scope |
|---|---|---|
| `bridge-linux-r14/fc-mesh` | `9ffcdcae2d40bc1b30dc9c981984de600e07e42c21496240e86535219da2f5f6` | Linux amd64 native worker; local packet/IPC tests PASS;44.02s, peak70°C |
| `bridge-windows-r10/fc-mesh.exe` | `4fac7c9171260875668ae662204edb9f97576adaeaa3c03e7010df3c2066ad87` | Windows amd64 cross-build only;10.00s, peak63°C; Windows runtime NOT_RUN |
| `mesh-system-r8/FamilyConnect-MESH-system-amd64.tar.gz` | `126cc67ed790976ad719233b85625d4f42b41acd54530957f50d139daba52226` |15101298-byte unsigned Linux internal component;15.01s, peak62°C; verified, not installed or a full desktop installer |

No update-manifest, installer/Authenticode or new driver signature is claimed.
No full AppImage, DEB or Windows installer is produced in this phase. Linux0.2.11/
Windows0.2.15, installed state, identity/history, Android106, active MESH sessions,
server policy and public downloads/catalogs remain unchanged. No rollout occurred;
there is no new installed rollback action. Live application budget used stays0/32MiB
per OS. No UI layout changed or new screenshot/physical-OS acceptance is claimed.

Remaining: product Auto ownership/capabilities/handoffs and root/user floor sync;
full diagnostics/consent/restricted chat; installed Linux MESH/P1/recovery/upgrade;
Windows broker/WinForms/embedded runtime and driver acceptance; actual visual
comparisons and complete private packages. Phase14 is progress, not PARITY PASS.

## Owner progress readback —24.10,03:47 CEST

Read-only code/test/artifact inspection confirms further Linux integration work:
`auto_platform.Platform` joins protected normal configuration and existing
normal/MESH candidates, validates material offline before lookup, filters installed
capabilities and detects underlying interface/address changes. `auto_runtime.Coordinator`
uses the actual native Auto policy and serializes attempts, health and explicit
Disconnect. Late CONNECTED replies cannot restore cancelled user intent. This is
source integration, not an enabled GUI Auto path or an installed VPN acceptance.

Final `auto-coordinator-final-r1/pytest.xml` under the24Oct evidence directory
records776 tests,0 failures/errors/skips (32 more than phase14); the wrapper log
records one existing warning and175/2073 source-integrity PASS. Native-controller
tests use synthetic platform/guard/helper operations, not authenticated gateway
traffic. The23Oct wrapper thermal receipt records42.02s,50% CPU quota, peak71°C,
exit0 and no guard stop. No emulator was running at this checkpoint.

Both new amd64 worker manifests share source digest
`37038fef67acf7d7ea500ea3e6dcef584daaa25547f45807e6145e71fde417f2`.
Actual binary SHA256 and size match their build manifests:

| Artifact under `state-client-build/desktop-parity106-20261024/` | SHA256 | Boundary |
|---|---|---|
| `bridge-linux-r15/fc-mesh` | `9a4b111e0306aebeba3a9ec01b3a77ab20240ecd553d44a51e155e2fd39c7c76` | Native component, local packet/IPC checks PASS, not installed |
| `bridge-windows-r11/fc-mesh.exe` | `9070adb0df67f7bd76344d61c52c079993898a1c7ad04a7475f534639f563b2a` | Cross-build only, Windows runtime NOT_RUN |

Component-r9 is not assembled. Neither worker is a complete desktop installer.
Stage3/6 remains Linux integration, not50% overall completion;0/2 complete parity
installers and0/2 installed OS acceptance. Next: durable Auto service/intent,
authenticated GUI IPC and root/user floor synchronization; then installed Linux
MESH/P1/recovery/upgrade, remaining diagnostics/consent/chat, Windows broker/WinForms,
actual visual comparisons and full private packages. No aggregate percentage is
derived from test counts or elapsed time.

Linux0.2.11/Windows0.2.15, installed identities/history, Android106, active MESH
sessions, server policy and public catalogs remain unchanged. No new installation,
rollout or rollback operation; no new signature claim. Live application budget
used remains0/32MiB per OS. This checkpoint is not PARITY PASS.

## Linux root Auto host, service and memory intent —24.10 phase15

### Implemented path and limits

The native configuration adapter now supports offline identity/WG key/floor
validation before network lookup; this cannot authorize a session. Linux's real
capability/physical-underlay host calls the existing normal and MESH attempt
adapters under the same guard. The coordinator uses the shared native policy,
not a second retry algorithm; address changes on an unchanged interface also
invalidate the current path. Only transient normal configuration failure permits
restricted fallback; AUTH/configuration/internal/cancel are not hidden by MESH.

`auto_service.py` supplies the root lifecycle and packaged
`family-connect-auto@.service`. A root-only global runtime lock excludes duplicate
owners. Reservation uses the existing transport lock and rejects active manual
VPNs. The root guard is prepared before the native configure call, reused with
readback rather than acquired twice, and reconciled before restart attempts.
The unit does not start on component installation and is not yet launched by GUI.

The separate0711 root IPC directory contains a0600 UID-owned socket. Each accepted
connection checks actual SO_PEERCRED and permits only one bounded typed start,
status or generation-fenced stop request. No caller-supplied path, executable or
arbitrary bypass endpoint is accepted. Start acknowledges saved intent/queued work,
not CONNECTED. Late connection status cannot overwrite explicit disconnect.

`AutoIntent` reuses the manual-MESH manager-held memfd implementation with a
separate name and32KiB maximum for validated key material plus two public signed
floors. The root intent journal contains no private material; manual-MESH's4KiB
wire/memory contract remains unchanged and cannot consume the Auto descriptor.
Explicit stop revokes memory before asynchronous cleanup, even when disk journal
revocation fails. Daemon shutdown instead closes the candidate while retaining
the guard and desired intent for manager restart. Missing credentials fail closed.
Terminal authorization failure revokes the service intent; no new grants exist.

The unit keeps NoNewPrivileges, strict filesystem/home protection, no core dumps,
limited capabilities and bounded cgroup shutdown. Only existing AWG/TCP profile
directories are additionally writable. Installer/manual-start exclusions now also
cover residual Auto MESH journals; setup locks/refuses a running Auto service.
Installed drivers, helpers, route/DNS rollback and userspace AWG crash behavior are
not established by these unit tests. See [service contract](../clients/DESKTOP_AUTO_NORMAL.md).

### Exact checks

Receipts are in `state-client-build/desktop-parity106-20261023/`; JUnit files and
binaries below are in `state-client-build/desktop-parity106-20261024/`.

- `auto-coordinator-go-r1`: desktopmesh race×3 and normal/automatic race×5 PASS;
 25.01s, peak66°C. The preceding native host/preflight continuation is included here.
- `auto-coordinator-final-r1`:776 Python checks PASS/no skips,175/2073 source
 integrity PASS;42.02s, peak71°C. This predates the root service, not its validation.
- `auto-service-r1`:91 PASS,1 failed test because the wrong-UID peer correctly
 closed before the test could write, raising BrokenPipeError. The test now accepts
 that valid rejection outcome; no service authorization was weakened.17.01s,60°C.
- `auto-service-r2`:158 targeted checks PASS,27.01s,62°C. Includes real user-systemd
 FD-store restoration/revocation for both contracts and actual Unix socket frames.
- `auto-service-final-r1`:817 PASS,0 errors/failures/skips, one existing
 PyGI GLib.unix_signal_add_full deprecation;175/2073 source integrity PASS.
 Wrapper47.02s, peak77°C. This precedes the final uncertain-intent commit case.
 Native coordinator abort tests confirm that restart closes the attempt without
 releasing containment. Service adapter/network/helper operations are synthetic;
 no real gateway or installed TUN/P1/recovery/upgrade PASS is claimed.
- Final `auto-service-final-r2`:818 PASS/no skips, same existing warning and
 175/2073 integrity PASS;48.02s, peak65°C. Includes40 service tests,30 host/coordinator
 tests and two actual manager restart/revocation cases. An uncertain intent write
 after rename now fails the daemon instead of leaving an apparently disconnected
 owner without a usable stop generation. The restarted service reports missing
 credentials with the recorded generation; it never starts a replacement session.
 All final component source changes are covered by this run.
- `auto-service-package-readback-r1`: archive/digest and94 member readback PASS;
 both284-file native inventories match current source. Extracted root modules
 import under Python `-I -S` without cryptography/httpx/RNS/GI. The actual
 systemd-analyze verifier accepts the new unit. This is not unit execution.
- Final `auto-service-package-readback-r2` verifies component-r10 after that last
 persistence correction:94 members, every packaged root module byte-equal to
 current source, isolated imports and unit validation PASS. The earlier r9/readback
 remain historical evidence, not the final component.

The user-systemd tests use synthetic credentials, isolated temporary journals and
their own bounded units. They kill/restart only those test units, not the actual
Family Connect daemon, Android, existing VPNs or a gateway. Same-UID socketpair
credentials and a mismatching expected UID are tested; installed root socket ACL
acceptance remains a separate gate. No fake runtime replaces a shipped adapter.

### Delivery, not installation

Linux r15 and Windows r11 native source digest:
`37038fef67acf7d7ea500ea3e6dcef584daaa25547f45807e6145e71fde417f2`.
Builds share284 hashes; accepted175 shared files and2073 capsule entries match.
Native build time/peak: Linux46.02s/60°C; Windows11.01s/63°C. Windows is cross-built,
not runtime/driver accepted. Binary hashes remain those recorded at03:47 above.

New internal package:
`state-client-build/desktop-parity106-20261024/mesh-system-r10/FamilyConnect-MESH-system-amd64.tar.gz`

SHA256: `88644b02518f908c270056fcf8b19ba38039ca479e2bb8c2d4e7dc0b2d1dc7a9`.
15110718 bytes;94 verified members. Assembly16.01s/62°C; final readback2.00s/59°C.
Includes root Auto
service/IPC and existing native/RNS components; not a complete AppImage, DEB or
desktop installer. Linux amd64 development prerequisites remain systemd254+,
systemd-resolved, system Python3, iproute2/nftables, polkit and TUN. Packaging does
not bundle the missing full desktop environment or change those prerequisites.
Unsigned private component: no new update-manifest signature, Authenticode or
driver-signature claim. No artifact is published or linked from public downloads.

No setup/update was performed on this computer. Existing Linux0.2.11 and
Windows0.2.15 state is untouched; Android106, identities/history, existing active
sessions and server policy are unchanged. No installed rollback is needed. For a
future authorized component install, the installer preserves its root-owned file
backup; rollback uses the prior verified component while disconnected, not a
reset of user data. The prior r8 remains an immutable historical component. The
first r9 in this phase (15110692 bytes,
SHA256 `606262519845804d34de3982fca080920c7a5859222946026f66eee4a8e51ee8`,
15.01s/64°C assembly) was superseded by r10 after the uncertain-intent correction;
neither package was installed. No existing version/archive was overwritten.

Remaining immediate work: root→user signed-floor synchronization and ordinary
authorized GUI/service client launch, before GTK Auto activation. Then installed
Linux handoffs/MESH/P1/crash/sleep/network-return/route-DNS-IPv6/upgrade checks,
complete diagnostics/consent and restricted chat, Windows broker/WinForms/runtime,
actual visual comparisons and full private installers. Live application traffic
used remains0/32MiB per OS. No emulator ran; all builds/tests used50% CPU quota and
thermal guards. Stage3/6,0/2 complete parity installers/installed OS acceptance;
this phase is concrete progress, not PARITY PASS or an overall completion percent.

## Linux authorized GTK Auto and signed floor continuity —24.10 phase16

### Implemented source

`LinuxAuto` now uses the existing serialized authorization session and fixed
polkit helper verbs. It checks root-owned component files, a separate versioned
Auto marker, UID-owned0600 socket and root peer credentials; request/reply frames
are bounded. Root startup and emergency stop share a command lock; stop validates
the exact32-hex intent generation before revocation and fixed-unit shutdown.
No arbitrary executable, path, UID or shell command is added to privileged IPC.
The IPC directory explicitly becomes0711 despite the unit's0077 umask. A legacy
root-only directory is migrated only if its entries are recognized private sockets.

Before sending a start, the client atomically records a public pending receipt.
Lost replies are reconciled, not replayed or reported as DISCONNECTED. Normal
Disconnect uses UID IPC without another elevation; generation-checked helper
cleanup is the bounded fallback. An unknown generation is read before privileged
recovery. Cancellation after declined authorization does not prompt again merely
to stop a session that never existed. The root service, not the GTK TCP recovery
loop, owns Auto retry intent. Window-close warns about continuing service operation;
reopening reads its state.

The root exposes only its signed public catalog envelope. Manual configuration
merges it under the existing user identity lock before HTTP. The shared full
catalog grammar/signature checks reject rollback, equal-sequence conflict, invalid
templates/signatures and initialized missing/corrupt files. The additive0600
`friends.catalog-floor.json` and initialized marker are atomic/retry-safe; they do
not duplicate private identity or replace the old country profiles. Root Python
remains stdlib-only; native code still performs root-side cryptographic validation.

GTK keeps the existing screen/navigation structure. Auto is available only with
the verified component and identity module. Selected `Auto` differs from actual
AWG/TCP/MESH; P1 and RS/CREDIT are not attributed to AWG/TCP. A MESH fallback shows
the directory gateway, not a guessed country/map endpoint. The IP check binds curl
to the actual TUN and fences generation/interface/attempt changes. Stale IP results
are cleared on disconnect/generation change. Diagnostic export distinguishes
selected Auto from actual transport; full106 native projection remains a separate
unfinished requirement. See [RU/EN user notes](../clients/DESKTOP_AUTO_USER.md).

### Evidence and retained failures

- `auto-floor-final-r2.xml`:879 PASS,0 failures/errors/skips,44.639s pytest;
  wrapper49.02s, peak69°C. Includes actual isolated user-systemd memory contracts,
  native catalog vectors, floor migrations, client/generation/IP fences and prior
  AWG/TCP/MESH/messaging tests. The root/helper network operations are synthetic.
  One pre-existing PyGI deprecation remains. Earlier final-r1 also879 PASS.
- Accepted integrity175 shared files/2073 capsule entries PASS. Existing Linux r15
  and Windows r11 native inventories284 entries are reused, not Android ARM binaries.
- `auto-gtk-final-r3-{1,1.25,1.5,2}/`:68 actual GTK/X11 PNGs, RU/EN, six connection
  states, settings/route and wide long-error case. Tests exercise main-button
  keyboard activation, focus/Tab, Escape, cancelled/lost start replies, denied
  authorization, stale polls, service reattachment, close warning and actual
  transport/profile labels.125/150% are font-DPI tests, not compositor fractional
  scaling. `mesh-gtk-regression-r3/`:15 manual-MESH PNGs and interactions PASS.
  Final UI wrapper85.04s, peak80°C; no thermal stop.
- `auto-gtk-final-r2`: four scales plus24 existing generic layout cases PASS,
  137.06s, peak66°C. It predates final route/IP refinements. GTK/Xvfb emitted
  locale/DRI and isolated portal/Secret Service activation warnings; application
  owners were synthetic and smoke mode did not activate real chat identity.
- Visually inspected final English connected and200% Russian settings, plus the
  preceding200% disconnected capture against the retained exact106 GPU reference.
  Palette/EXIT/navigation hierarchy is retained; desktop gauge density, extra
  explanatory text/settings and complete live-state Android comparisons remain
  gaps. This is not overall VISUAL_PARITY PASS; network states are injected.
- Retained r1 backend failures:98 passed,2 AF_UNIX test paths exceeded the kernel
  length limit; fixture now uses a short private temporary path. Retained r2:
  153 passed,5 synthetic IP-test failures lacked the socket-presence fixture.
  Both are corrected in the final879 run, without weakening production checks.
- Initial Auto screenshot runs did not fence synthetic state injection against
  an older queued poll; one file named disconnected showed ON. Final harness
  advances revision, waits for layout and asserts displayed state/gauge before
  capture. Earlier screenshots are retained but superseded, not acceptance proof.

### Private component, not a complete installer

`state-client-build/desktop-parity106-20261024/mesh-system-r12/FamilyConnect-MESH-system-amd64.tar.gz`

SHA256: `43c0dd59e2ee9012dc7cfbea35e393c73e57850bdebdcc80f241f10b3ea7a261`.
15114492 bytes;94 members. Assembly14.01s, peak62°C. It packages root/native/RNS
components, not the GTK application or bundled desktop dependencies. Linux amd64
prerequisites remain systemd254+, systemd-resolved, Python3, nftables/iproute2,
polkit and TUN. No signature: archive hash is not an update-manifest signature,
Authenticode signature or driver signature. No signing key/catalog/public URL changed.

The preceding r11 (15114454 bytes,
SHA256`5b36a8389b3846e8ece6a4fba91fe3bfe9f7f8d077dc08350ebf887049791e43`)
is retained but superseded solely to correct its stale packaged README claiming
GUI/floor work was still absent. It was not installed or distributed. No immutable
artifact was overwritten. Archive readback verifies source bytes and isolated
stdlib imports. Auto unit syntax is checked. The first readback also tried the
manual unit's installed executable check and failed because
`/usr/local/lib/family-connect-mesh/helper` is not installed; this is not silently
counted as runtime acceptance. Manual helper installation remains NOT_RUN.

### Remaining delivery gates

Versions remain Linux0.2.11/Windows0.2.15; no installed setup/upgrade/rollback took
place. Future setup retains prior root files for rollback while disconnected;
never reset identity or delete catalog floors. No production identities, gateway,
Android APK, live sessions, grants or public artifacts were modified. Linux owner
P1 authorization is not inferred from the three-device Android cohort; Windows
owner identity still needs verified discovery. Live application test traffic0/32MiB
per OS. No emulator ran; each heavy job used50% CPU quota and hard/thermal bounds.

Next: installed Linux root ACL, AWG/TCP↔MESH handoffs, TUN/DNS/IPv6 cleanup,
network/sleep/crash recovery, actual P1 and identity-preserving upgrade. Finish
full diagnostics/opt-in support, restricted chat and remaining settings. Then
Windows broker/WinForms/runtime, complete visual acceptance and private
AppImage/DEB/Windows installers. Physical Windows NOT_RUN. Stage3/6,0/2 complete
parity installers and0/2 completed installed-OS acceptance; goal remains active.

## Linux AWG ownership and isolated crash cleanup —24.10 phase17

Owner checkpoint05:47 CEST. This phase completes a concrete normal-transport
integration defect, not the whole parity task. Previous status-only readback did
not constitute implementation progress. No new privilege grant, host installation,
production traffic, Android change, gateway restart, commit, push or publication.

### Root cause and product change

The inherited AWG helper called teardown only while the TUN existed. A userspace
engine death could therefore leave resolver/firewall/policy resources behind.
Upstream quick teardown also loops over main-table suppression rules without
proving ownership. `awg_lifecycle.py` retains the pinned engine/tools but replaces
those platform operations using exact source anchors and a root0700 directory/
0600 atomic journal. No private key or transport payload is added to that journal.

Table64620, priorities10619/10620 and both unreachable backup defaults are reserved
only when unused. A generation alias plus interface index and nft generation
marker prove ownership; the resolver entry is recorded before setup. Cleanup
works after TUN disappearance, removes only exact own selectors and is repeatable.
Unexpected ownership or changed unrelated rules prevent destructive cleanup or
unsafe sysctl reset. A missing journal cannot claim success over residual resources.
The userspace-creation→alias crash window is deliberately not adopted automatically:
an unproven interface remains a reconciliation error, not a claimed recovery PASS.

The checked iproute2 emits string table IDs, null `not` and `suppress_prefixlen`;
these exact representations are accepted without relaxing selector validation.
nft1.0.6 omits table comments in JSON; generation-named chains are mandatory proof,
and a returned comment must also match. Manual Disconnect no longer skips an absent
AWG TUN. Auto cannot forget a still-journaled AWG profile or start over foreign
manual ownership. Both setup paths refuse pending cleanup and install the new module
beside the existing helper. No GUI privilege change or alternate crypto/engine.

### Checks and retained failures

- `awg-lifecycle-full-r2`:925 PASS,0 failures/errors/skips,45.040s pytest;
  wrapper49.02s,71°C. Includes new lifecycle, cancellation/transition, capability,
  installer and normal-service regressions, existing actual user-systemd/memfd and
  compiled native configuration checks. One existing PyGI deprecation warning.
- Accepted source integrity175 shared files/2073 capsule files PASS; no Android
  build or APK replacement. Native inventories284/284 still match both prior builds.
- `awg-lifecycle-kernel-r9`: installed reviewed helper plus pinned AWG3.1 in a
  disposable internal Docker network; real TUN, authenticated handshake and bound
  internal HTTP. Explicit down, exact daemon SIGKILL, IPv4/IPv6 unreachable route
  lookup, cleanup and fresh-generation connection all PASS. Routes, rules, resolver
  bytes and nft state equal baseline; injected foreign suppression rules/nft table
  survive. Wrong protected-header key rejects; authorization-session cross-UID and
  forbidden-command checks PASS. Wrapper41.02s,71°C. r8 also PASS before the final
  missing-journal rejection check,41.02s,61°C.
- `awg-lifecycle-legacy-r1`: real isolated AWG2 handshake/internal HTTP PASS,
  5.00s,64°C. This does not certify an old installed AWG2 helper upgrade.
- `awg-lifecycle-unit-r1`:157 PASS,6 opt-in systemd skips,3.00s,63°C; superseded
  by the final full run with those checks enabled and no skips.
- Retained kernel r1–r3: the tightened server container lacked permission to read
  its user-owned0600 test key. Only that disposable server receives DAC_OVERRIDE;
  private file permissions remain unchanged. r4–r5 exposed actual iproute/nft JSON
  differences and failed closed. r6 exposed openresolv's empty-list exit status1;
  the harness now also verifies exact resolver bytes and empty interface inventory.
  r7 required the kernel's equivalent `No route to host` rejection wording. r8/r9
  complete the real checks. No failed attempt is counted as acceptance.
- Retained full-r1:923 PASS,2 obsolete fixture expectations; manual cleanup now
  precedes TCP selection even if AWG's link disappeared. Final expectations retain
  the no-extra-TCP-cleanup checks and verify the additional necessary AWG teardown.

Containers have CPU25% each,256MiB,64-PID and150s independent lifetime bounds;
the test controller has CPU50%,150s/85°C guards. Only the reviewed source clients
and checker are mounted read-only; no host network, published ports, production
identity or host system directories are writable. Fresh exact named containers/
network are removed; final discovery found none remaining. Final jobs all stopped
normally, no thermal guard stop, no emulator. External/live application bytes0/32MiB
per OS; the successful internal check transfers only small fixed HTTP bodies.
Docker itself creates/removes the temporary test bridge and its routing resources;
the harness's “no host routes” shorthand means no manipulation of host VPN routes,
not an assertion that Docker performs no host networking operations at all.

### Artifact and verification boundary

`state-client-build/desktop-parity106-20261024/mesh-system-r13/FamilyConnect-MESH-system-amd64.tar.gz`

SHA256 `6316255674d7aa2607a45c470c84686b494ae334558f7adbb6dfcba6adea6545`;
15117620 bytes,95 members. Build15.01s,63°C. Unsigned Linux amd64 system component,
not a GUI/AppImage/DEB or Windows installer. Requirements remain Python3,
systemd254+, systemd-resolved, nftables/iproute2, polkit and TUN. r12 is retained;
no immutable artifact overwritten. Native Linuxr15/Windowsr11 and RNSr2 are reused.
No update-manifest signature, Authenticode or driver signature is inferred.

`awg-lifecycle-readback-r1`: archive digest/inventory,20 packaged module bytes,
3 common modules, helper/installer bytes and isolated `python -I -S` imports PASS;
auto unit syntax PASS. Both284-source native inventories and binary digests PASS.
3.00s,65°C. Manual unit executable/host component remain NOT_INSTALLED/NOT_RUN;
no exact full-package installation/upgrade/rollback has been exercised.

Linux0.2.11/Windows0.2.15 unchanged. The existing synthetic state-preservation tests
do not substitute for upgrading the owner's installed client. Visual evidence is
unchanged from phase16, not a new overall visual PASS. No authorized desktop P1
cohort membership is assumed; Windows identity discovery and physical runtime
remain open. Still stage3/6,0/2 full parity installers,0/2 completed installed-OS
acceptance. Next: full Linux diagnostic/consent/restricted-chat integration and
authorized installed MESH/P1/handoff/automatic network/sleep recovery/upgrade,
then Windows broker/WinForms, actual visual acceptance and full private packages.

## Native106 JSON and Linux online support —24.10 phase18

### Reference and implementation

Android APK/source/native105 remain unchanged. The diagnostic contract pins five
pure-Java projectors from the accepted capsule, not root Android code.41 vectors
match exactly. `NativeDiagnostics106` preserves receipt constraints, local write
completion, bounded delivery/assembly/boundary fields, numeric Mux kinds/arrays,
correlation and startup/cache observations previously lost by generic projection.
Terminal samples and first failures cannot be overwritten by stale/empty callbacks;
service-attempt fences distinguish restarted native counters. Cached incidents and
history are exportable before the first fresh poll. Limits and dropped counters
remain explicit; neither raw logs nor private strings are admitted.

Online support is a separate4096-byte allowlist, not an upload of the full export.
`provisioning/support.py` implements identity-bound atomic0600 consent metadata,
seven-day expiry, completion-based60s success/300s failure cooldown, one in-flight
worker, explicit cancellation and stale-completion fences. `FriendsClient` uses the
existing diagnostics proof purpose bound to SHA256 of the exact report string,
HTTPS/no redirects, bounded response, shared15s deadline and distinct rate/auth/
timeout results. It never creates identity or routes, replaces keys, grants rights
or falls back after authentication rejection. OS resolver/transport cancellation
is cooperative rather than a force-killed process; no overlapping worker is spawned.

GTK offers a separate confirmation and expiry/status display, disabled by default.
Cancellation/expiry stops future uploads; an already received snapshot follows the
existing server retention, not a fictional delete request. Failed consent withdrawal
stops the current process and visibly asks for a restart-state check. Full local JSON
saving remains a separate privacy-confirmed action. The accepted mint switch style
is reused, not the host's orange accent. The full GUI bundler includes the support
module; the root component deliberately does not gain HTTP/crypto/GI dependencies.

**Still incomplete:** this uploader lives for the GTK process lifetime. GUI-closed
background collection must move into the independent user service with a single
owner before claiming full parity. Windows support/WinForms is not implemented.
No actual production snapshot was sent, no existing user's consent enabled, no
server policy or Android artifact changed. See the RU/EN guide
`docs/clients/DESKTOP_DIAGNOSTICS106.md` for limits and user-visible behavior.

### Checks and retained failures

- `diagnostics106-full-r1`:980 PASS, zero skips;41 native Java vectors PASS in
  `diagnostics106-java-r2`. These precede the online workflow.
- `support106-full-r2`:1130 PASS,0 failures/errors/skips,49.006s pytest;175/2073
  integrity PASS. Includes real local API identity/proof/report-digest/retention,
  malformed/unsafe fields, cancellation/deadline, default-OFF/expiry/clock rollback,
  private metadata, cadence/inflight/late completion and existing VPN/native/package
  regressions. This is a selected local suite, not installed networking acceptance.
- `support106-java-r2`:54 online snapshot vectors equal the accepted projector after
  the explicit Android→Linux platform-label adaptation. Random report IDs are fixed
  only in fixtures. Source and Gson hashes are in the shared contract.
- Final `support106-gtk-r4`:four real X11/Xvfb runs, RU/EN,32 PNGs, four full JSON
  exports, actual GTK save chooser, clipboard/focus/Escape, consent cancel/grant/
  persistence/revoke and visible focused switch in a compact390×600 requested window.
  Backend and upload sender are synthetic; the HTTP proof path is tested separately.
  125/150% are font-DPI checks, not compositor fractional scaling. Native GTK portal
  fallback is controlled only inside the fixture; installed portal acceptance is open.
- Visual inspection of final200% compact focus and150% RU consent confirms readable
  controls/scrolling and no new dashboard/navigation. Existing accepted Android
  `Screenshot_1792771564.png` confirms the settings/Support ID hierarchy; it does not
  show the online switch and is not full pixel/state equivalence. Full visual parity
  remains incomplete.
- Retain `diagnostics106-acceptance-r1` failure: missing Xvfb PATH after Java PASS.
  r2/r3 attempted host portal selection; r4 needed an explicit SAVE filename;
  r5 local save passed. Early support GTK r1/r2 actually used inherited host Wayland
  (geometry/scale evidence), not Xvfb. They are not isolated/DPI acceptance. r3 forced
  X11; final r4 also isolates XDG metadata and records the actual display backend.
- Retain `support106-unit-r1`:60 PASS/1 fixture failure. The local HTTP fixture caught
  `Rejected` before its `RateLimited` subtype, incorrectly returning403 instead of429.
  Correct exception ordering gives61 PASS in r2; no server authorization was weakened.
- Final thermal receipts: Python53.02s/81°C, GTK41.02s/69°C, CPUQuota50%, no guard stop.
  Earlier native-projection full run peaked83°C. No emulator was started this phase.

### Delivery, identity and remaining gates

`state-client-build/desktop-parity106-20261024/mesh-system-r14/FamilyConnect-MESH-system-amd64.tar.gz`
contains95 verified members,15,122,913 bytes, SHA256
`002b79488461aaebaf08aa0743eefa28e0d3cb4d9fb0d3f40cf60fd72be161d0`.
It is an **unsigned Linux amd64 root/native/RNS development component**, not the
complete GUI, AppImage,DEB or Windows installer. It contains the updated backend
projector, not the separate GTK/support uploader. No installation or publication.
Prerequisites remain Python3, systemd254+, resolved/iproute2/nft/polkit and TUN.
The readback checks exact source bytes, isolated stdlib-only root imports, Auto
unit syntax and both unchanged284-file native inventories/binary hashes. The manual
unit executable remains NOT_INSTALLED. Source GUI/support closure is checked by
`test_linux_chat_package.py`; no standalone installed-GUI acceptance is implied.

Native Linux-r15/Windows-r11 and RNS-r2 are reused, not rebuilt. Linux0.2.11 and
Windows0.2.15 product versions, existing identity/keys/history and public catalogs
are unchanged. There is no signed update manifest, Authenticode or new driver
signature for this internal component; these distinct signatures are not conflated.
A later authorized component install requires disconnected Family Connect and the
existing explicit pkexec installer. Rollback is reinstalling the previous verified
component while disconnected; no current installation has been changed to roll back.

Stage3/6 remains Linux integration, not a completion percentage.0/2 complete parity
installers and0/2 complete installed-OS acceptance. Actual MESH/P1 RS32/32+CREDIT128,
real gateway/DNS/HTTPS, network/sleep/automatic recovery, installed identity-preserving
upgrade, restricted chat, independent support ownership, Windows broker/WinForms
and full visual/package gates remain open. Windows physical acceptance NOT_RUN;
no new desktop P1 grant is assumed or created. Source/evidence/artifact hashes are
appended as phase18 in the companion evidence JSON; earlier phase hashes are retained.

## Linux independent support owner —24.10 phase19

### Implemented product path

GTK now uses `provisioning/support_client.py` for status/control only. The existing
unprivileged `ChatService` owns `SupportSession` and the single uploader, without
moving keys to a privileged process, creating identity or requiring chat-keyring
access. Same-UID commands admit only empty status reads or an explicit consent
boolean with the observed revision. One separate bounded control worker prevents
a busy/locked chat owner from blocking withdrawal. Revisions rotate on accepted
changes and restart; lost replies require readback, never automatic mutation replay.
Repeated enable does not extend existing consent. Expiry/withdrawal restore ordinary
idle exit. A GUI close detaches rather than revoking or stopping valid background
collection. No UI-side fallback uploader runs when the service is unavailable.

`SupportCollector` reads existing Auto/MESH status and the own AWG/TCP interfaces/
metadata without invoking a mutating helper or creating an underlying-network bypass.
Read failures report UNKNOWN, not MESH success. Validated terminal native metrics
remain historical on disconnect, and are cleared for a new attempt/generation;
the VPN-active flag still follows current observation. The normal legacy observation
is not a new HTTPS/egress proof. The accepted seven-day consent,4096-byte allowlist,
proof digest,15s HTTP budget and60/300s completion cadence are unchanged.

Full GUI packaging includes the new service/client modules and VERSION. The bundle
test actually imports ChatService/SupportSession/SupportClient from the assembled
directory and checks its version/default-off behavior, not just filenames. The
six-file legacy archive contract remains unchanged. ADR004 and the RU/EN guide
describe user-session lifetime, storage errors and unconfirmed withdrawal honestly.

### Checks, screenshots and boundaries

All logs/thermal receipts are in `state-client-build/desktop-parity106-20261023/`;
XML/runtime outputs are in `state-client-build/desktop-parity106-20261024/`.

- `support-owner-unit-r1`:132 PASS/1 fixture failure; the fixture incorrectly used
  a generic NetworkManager name rather than the existing `fc-app-` prefix. Corrected
  fixture retained; no production ownership weakening. r2:133 PASS. After collector
  terminal-history correction, `support-owner-unit-r3`:134 PASS,3.10s pytest,
 5.00s wrapper/61°C. Scope counts overlap and are not additive.
- `support-owner-full-r1`:1157 PASS, no failures/errors/skips, one existing GI
  deprecation warning;49.83s pytest,54.03s wrapper/64°C.175 shared and2073 capsule
  files match. No Android build, install or field session.
- `support-service-runtime-r2/result.json`: PASS with actual GTK, private D-Bus and
  user-systemd. Two snapshots reached real local API handlers; second snapshot
  followed GUI close and a changed synthetic VPN state at63.727s completion cadence.
  Exact service SIGKILL/restart preserves synthetic identity/consent, rejects old
  revision, permits revoke without chat keyring and then exits idle.140.07s/79°C.
  The earlier passing r1 (136.07s/77°C) predates the collector-history correction;
  r2 verifies the current product source. Three RU screenshots are retained in r2.
- `chat-service-support-r1/result.json`: PASS with actual private Secret Service,
  D-Bus/user-systemd and loopback RNS: GUI detach→delivery/notification, SIGKILL→same
  identity/history, crash-after-commit replay rejection and background-off idle
  exit. Reopened GTK and settings screenshots retained.56.02s/69°C.
- `support-owner-delivery-r1`:28 targeted support/package tests PASS after strengthening
  actual bundled-import assertions;2.31s pytest. Source-byte/component/import/unit
  checks and175/2073 integrity checks PASS;9.00s wrapper/63°C.
- `support-owner-evidence-r1` failed before any evidence edit because the isolated
  service PATH lacked `apply_patch`. r2 passes with the explicit tool PATH:
 16 source hashes,25 evidence-file hashes and component digest read back;1.00s/60°C.
  Earlier phase records and the failed writer log are preserved.

Runtime fixtures use Type=exec on an isolated bus; production Type=dbus, exact
installed paths, AppImage mount retention, cold login/logout and installed upgrade
remain NOT_RUN. Support HTTP uses local real handlers via MockTransport and VPN is
synthetic; no real MESH/P1/egress or production upload is inferred. The new screenshots
verify service-backed controls and retained history, not complete visual parity.
Earlier phase18 RU/EN/four-scale screenshots retain their narrower recorded scope.
All fixture units stopped; no emulator, live test data or user state changed.

### Internal delivery and next gate

`state-client-build/desktop-parity106-20261024/mesh-system-r15/FamilyConnect-MESH-system-amd64.tar.gz`
is15,123,187 bytes,95 members; SHA256
`ec1dd1cad861884e94815c38be98ba658ff65077862b058d84b603ec5df6e4d8`.
This is the unsigned Linux amd64 system/native/RNS component, not the GTK bundle,
AppImage, DEB or complete installer. Source bytes,20 root Python modules,3 common
modules, stdlib-only isolated imports, Auto unit syntax and both284-file native
inventories/binary hashes pass readback. Manual unit executable is NOT_INSTALLED.
Existing native Linux-r15/Windows-r11 and RNS-r2 are reused without rebuilding.
Package creation:16.01s/66°C. No signing/catalog/publishing action occurred.

Linux0.2.11/Windows0.2.15, installed identities/history, Android106 and server grants
remain unchanged. There is no current rollout to roll back. A later authorized
component installation still requires disconnected Family Connect and explicit
pkexec setup; rollback uses the prior verified component while disconnected.

Next: accepted restricted chat API/mailbox and existing-exit/service-only ownership,
then installed Linux MESH/P1/DNS/HTTPS/underlying-interface/sleep/recovery and
identity-preserving update. Windows broker/WinForms/runtime integration, physical
Windows NOT_RUN and full private installer/visual gates remain open. Stage3/6;
full parity installers0/2, completed installed-OS acceptances0/2. No PARITY PASS.

## Shared restricted-chat transport and native ownership —24.10 phase20

### Actual implementation, not completed desktop messaging

`carrier/restrictedchat` adapts the accepted native105 chat bridge and106 Java
caller into portable Go. `clients/shared/android106-chat.json` pins six exact
accepted files; the capsule verifier now checks these hashes against its2073-file
inventory. Existing Family material/certificates/revocation/floors/directory,
ReliableStream, Mux and `restrictedowner` are reused, not reimplemented in Python
or C#. No Android source/APK, experimental transport/tag or third-party dependency
was changed. The licensing note records that narrow source reuse.

The adapter validates delivery with the computer's existing identity and public
anchor before any network open. Eight leases maximum; existing exit requires the
same validated profile hash. Fresh service-only follows accepted default P0 and
30s protected-underlay startup; it does not grant desktop P1 access. VPN reservation
cancels/drains previous service-only work before publishing a replacement. Releasing
chat leaves borrowed VPN alive; stale Close cannot release a newer reservation.
The shared session retains its existing four-service-stream quota.

Only `chat-api` and `chat-mailbox` are available. API uses fixed accepted origin,
POST challenge/register only,8192-byte request,16384-byte response/header limits,
30s maximum duration, no redirect or proxy-environment route. HTTP400/401/403,
certificate rejection and409 remain terminal denial/conflict without reading an
unbounded/stalled error body. API operation cancellation is separate from socket
teardown. Portable stream adapters preserve raw bytes, cancellation, half-close
and explicit deadlines; replaced-timer callbacks are fenced. Ordinary formatting
redacts configuration and API response contents. No arbitrary host/path/command
or user-traffic bypass is introduced.

`desktopmesh.DialWithOwner` and the real native VPN worker now share this coordinator:
material validation precedes reservation, authenticated transport publishes its
profile, and teardown drains/releases only its own reservation. This is actual
native startup/cleanup integration, not just a fixture. **Desktop chat API/mailbox
IPC is still NOT_INTEGRATED on Linux and Windows.** Direct-first route eligibility,
privileged host forwarding and GTK chat-owner binding remain next. Existing Linux
SYSTEM-route mailbox continues unchanged; no new active UI capability is advertised.
Publishing transport ownership does not change CONNECTED/TUN/health readiness rules.

### Verification and retained failures

Logs/thermal receipts: `state-client-build/desktop-parity106-20261023/`.
Native builds, Go JSON test events and Python XML: `.../desktop-parity106-20261024/`.

- `restricted-chat-core-r1`: a real defect was caught—HTTP socket teardown cancelled
  the operation context and hid TLS certificate denial as unavailable. The adapter
  now separates these lifetimes; r2 passed five race-test repetitions. No weak
  fallback was shipped. The failed log remains retained (11s/73°C).
- `restricted-chat-owner-r1`: its only failure was the test comparing a JSON
  MarshalerError wrapper by equality instead of `errors.Is`; serialization was
  correctly rejected. Corrected fixture, no authorization weakening; r2 passes
  five repetitions. Failed receipt19.01s/79°C retained.
- `restricted-chat-go-final-r2.jsonl`: four packages PASS with `-race -count=3`;
 110 unique test/subtest names,330 pass events, zero failure events. Includes
  signed valid/mismatched/expired/revoked material, limits, loopback HTTPS,
  authorization/redirect/error-body behavior, byte-exact mailbox, cancellation,
  deadlines/concurrent close and service-only→VPN drain.22.01s/61°C. These use
  synthetic sessions/local network, not real provider/media or installed VPN.
- `restricted-chat-build-linux-r16c`: five native packages pass race tests; the
  CLI package compiles without tests. Build49.02s/70°C. Earlier r16/r16b attempts
  stopped before creating an output directory: missing PYTHONPATH, then an archive
  supplied instead of the required pinned Xray Git checkout. Corrected command
  uses `PYTHONPATH=$PWD` and `state-client-build/desktop-parity106-20261023/xray-pristine`;
  no checkout mutation or network fetch. Both failed invocation logs remain.
- `restricted-chat-build-windows-r12`: cross-build PASS,12.01s/62°C. This is not
  Windows execution, driver/TUN acceptance, WinForms integration or an installer.
- `restricted-chat-python-final-r1`:1158 PASS, zero failures/errors/skips, one
  existing GI warning;50.78s pytest,55.03s wrapper/66°C. Uses the new Linux worker.
 175 shared files/2073 capsule files and the six chat reference pins match.
- `restricted-chat-delivery-r1`: exact component source bytes, isolated stdlib-only
  imports, Auto unit syntax, both290-file native inventories/hashes, reference
  integrity and Linux `--version` manifest readback PASS. Host installation and
  manual service executable remain NOT_INSTALLED/NOT_RUN.

No new GUI screenshots were needed for this native-only change; prior GTK/Android
comparisons retain their recorded limits. All work remains local; no emulator,
production API upload, live application data, gateway restart or policy change.

### Private components and remaining work

All three artifacts below are under `state-client-build/desktop-parity106-20261024/`:

| Component | Relative path | SHA256 |
|---|---|---|
| Linux amd64 native | `bridge-linux-r16/fc-mesh` | `41d78b3b2d094981d1cf08b353fc30646d32b8f0aa4f30741785b5eb885a8991` |
| Windows amd64 native, cross-built | `bridge-windows-r12/fc-mesh.exe` | `df8fb1bf33b677efc4ee589f177fa2033fb3edde3633ea836d3a12eda316cd59` |
| Linux system/native/RNS archive | `mesh-system-r16/FamilyConnect-MESH-system-amd64.tar.gz` | `5604cff6a78e1e661423e24dcd5f9ccc92e25ebacf4f2c31b6789eed3c871539` |

Both native builds seal the same290-file source inventory:
`b71006e619a803b3f27e58318aa0e1907473c9ad1fd624143f2bd04c89628fc9`.
Build manifests explicitly record VPN ownership integrated and desktop chat IPC
NOT_INTEGRATED. The archive is15,144,379 bytes/95 members;20 root Python and3 common
modules are unchanged in role. Packaging14.01s/65°C. RNS-r2 is reused.
These are unsigned development components, not a full AppImage/DEB/Windows installer.
No update-manifest signature, Authenticode or new driver signature is supplied.
No artifact was installed, signed, published or substituted at a public URL.

Versions stay Linux0.2.11/Windows0.2.15; existing identities, stores/history, Android106,
P1 policy and update catalogs are untouched. No rollout needs rollback; a future
authorized component install still requires explicit setup with Family Connect
disconnected, retaining the previous verified component for rollback.

Next exact gate: authenticated/bounded Linux host IPC and route orchestration for
chat API/mailbox, with one native owner and no authorization fallback. Then installed
MESH/P1/DNS/HTTPS, interface/sleep/recovery and identity-safe upgrade; Windows product
integration and full private installers/visual acceptance remain mandatory.
Stage3/6, full parity installers0/2 and completed installed-OS acceptances0/2.
Windows physical acceptance NOT_RUN. Common-core tests do not establish PARITY PASS.

Final `restricted-chat-evidence-r1` readback verifies12 changed-source hashes,
39 evidence-file hashes, both290-file native inventories and all3 artifact digests;
1.00s/63°C, no guard stop. Prior phase records are retained in the companion JSON.
Final whitespace check passes, fixture units/emulator are absent; CPU61°C at readback.

## Private duplex chat IPC and Linux native parent —24.10 phase21

Checkpoint08:21 CEST. This closes the private native IPC gap from phase20, not the
remaining unprivileged-user authorization or end-user route integration. Linux0.2.11
and Windows0.2.15 remain unchanged; full parity installers0/2, completed installed
OS acceptances0/2, stage3/6. No Android build/install, gateway operation, policy
change, user identity access/migration, external application traffic or publication.

### Implementation and security boundary

- `clients/mesh/chatipc` exposes acquire/route/release, fixed API request and mailbox
  open/read/write/finish/close plus cancellation. It reuses `restrictedchat`, not a
  second implementation of crypto, RTP, ReliableStream or Family TLS/Mux.
- One owner is passed to VPN control and the chat server in the same process. Linux
  inherits an anonymous Unix stream from the root parent; the child validates its
  stream type and peer EUID. There is no filesystem listener, arbitrary URL, shell,
  command execution or persistent credential file. Windows fails closed for this
  inherited-descriptor mode and advertises NOT_INTEGRATED.
- Strict4-byte framing,96KiB frames, monotonic/channel-local request IDs; at most
 12 asynchronous jobs,8 leases,4 mailbox handles and16KiB chunks. Each mailbox can
  read and write concurrently but not have two readers/writers. Operation budgets
  are at most30s. Cancel/release/close/route bypass the job queue. Blocked replies
  retain their bounded job slot and have a4s write deadline.
- Cancelled/late opens and acquisitions are disposed, borrowed VPN ownership is
  retained, authorization/conflict categories cannot become transient fallback.
  Secrets/payloads have redacted formatting and no error-detail logging. Python has
  one reader, serialized writes and reserved control capacity; malformed/unknown
  replies close only the chat lane. Ambiguous mutations are never retried.
- `NativeWorker` now owns the separate chat descriptor; VPN stdin/stdout remains
  independent. Package/setup require the new native capability before accepting
  the parent sources; installer carries21 root modules, including `mesh_chat.py`.

This is a root-parent/native boundary, **not** sufficient authorization for a GUI
or user-session caller. The next implementation must bind public admission to the
authenticated computer/user/generation and validated readiness ownership, connect
the existing non-root ChatOwner, and preserve single-process transport ownership.
Existing SYSTEM-route messaging remains unchanged. No restricted-route GUI success
or production delivery is claimed.

### Checks and scope

Logs/thermal receipts: `state-client-build/desktop-parity106-20261023/chat-ipc-*`.
Build/test/delivery files: `state-client-build/desktop-parity106-20261024/`.

- `chat-ipc-go-r1` retained: test-local variable shadowed the test interface type,
  producing a compile failure, not a failed transport check. Corrected alias;
  r2 passes three race repetitions, final r3 passes five in chatipc/worker.
  Final9.00s/68°C; no guard stop. Tests cover duplex byte-exact16KiB chunks across
  repeated operations, bounded jobs/handles, reserved cancel/status, duplicate
  readers, deadlines, late cancellation, authorization/conflict and owner isolation.
- Linux-r17 builder tests six native packages with race, CLI compiles;47.02s/75°C.
  Windows-r13 cross-build11.00s/66°C. Windows runtime/driver acceptance NOT_RUN.
- `chat-ipc-python-r1.xml`:1176 PASS, zero failures/errors/skips, one existing GI
  warning;52.09s pytest,54.02s wrapper/65°C. Includes actual new native process
  status and operation replies, closing/malforming the chat lane without killing
  VPN control, duplex response demultiplexing, bounded jobs and cancel cleanup.
  Native control is DISCONNECTED in these fixtures, not a live TUN/MESH acceptance.
- Package14.01s/64°C; exact96-member archive,21 root modules/3 common modules,
  source bytes, stdlib-only imports, Auto unit syntax, both295-file native
  inventories and binary digests pass readback. Reference175/2073 and six accepted
  chat source pins match. No new GUI screenshots: this phase changes backend IPC.

### Private artifacts

All paths below are relative to `state-client-build/desktop-parity106-20261024/`.

| Artifact | Path | SHA256 |
|---|---|---|
| Linux amd64 native | `bridge-linux-r17/fc-mesh` | `56196fad7f39bb9cadac0b804e7e03967e2a68fd697bf345246fbe41927b96ec` |
| Windows amd64 native, cross-build only | `bridge-windows-r13/fc-mesh.exe` | `e9fa9756178ceda424e126759df916c5d771a00977807b62d5117f9345ae0f25` |
| Linux system/native/RNS component | `mesh-system-r17/FamilyConnect-MESH-system-amd64.tar.gz` | `04454556c2c3153b3bd0477ccad4284d3e64bcd4b49c5ba91933673d6ef874ae` |

Both native builds seal295 source files with digest
`2845e7befe77342bd1750df00cc26911fb115e9d6119d50d97287730ea95adc9`.
The component is15,194,724 bytes, internal and unsigned; no update-manifest signature,
Authenticode or new driver signature is supplied. It is not an AppImage/DEB/full
Windows installer. Nothing was installed/published, so no rollback was performed.
An eventual install must use explicit privileged setup while Family Connect is
disconnected and retain the preceding verified component for rollback.

Still required: authenticated public chat handoff and actual route orchestration;
installed Linux MESH/P1/DNS/HTTPS, recovery/sleep/interface changes and identity-safe
upgrade; Windows product integration/target-OS acceptance; final visual parity and
full private packages. Do not infer PARITY PASS from these component checks.

Final evidence readback (`chat-ipc-evidence-r2`,1.00s/57°C) verifies15 changed-source
hashes,31 evidence hashes, both295-file native inventories and all3 artifacts. Its
first invocation lacked `apply_patch` in the systemd service PATH and performed no
report write; the retained failure was corrected by explicitly passing PATH. Delivery
readback took5.00s/62°C. Final whitespace check passes; no parity fixture unit or
reference emulator remains running, and CPU measured52°C. No runtime acceptance or
rollout status was promoted by these evidence checks.

## Linux user chat admission and existing-exit handoff —24.10 phase22

Checkpoint08:53 CEST. This advances the Linux-integration stage, not full parity.
Linux0.2.11/Windows0.2.15 and the accepted106 APK/native105/source pins are unchanged.
No owner identity, production grant, gateway, Android build, public catalog or link
changed. No live application traffic or emulator was used. Full parity installers
remain0/2, installed-OS acceptances0/2; Windows runtime remains NOT_RUN.

### Implemented path

`provisioning/chat_bridge.py` now connects the actual user-session ChatOwner to a
separate chat-only endpoint in the existing Auto/manual-MESH root runtime. Both
sides check Unix peer credentials; the endpoint is0600 and its directory root-owned.
The active packet-session binding is published only after CONNECTED and network
guard checks, and binds the computer reference/API public-identity hash to validated
readiness. Caller-supplied private material, resolver/interface/executable/path and
arbitrary destinations are not accepted. Root material is never sent back to GUI.

At most4 public operations use32KiB frames,2 fixed API paths and30s budgets. Real
CLOEXEC AF_UNIX mailbox descriptors pass via SCM_RIGHTS;16KiB duplex pumps reuse the
existing private native lane. Half-close drains the opposite direction. Caller
cancellation interrupts a pending public open; native stream closure precedes writer
join, with bounded cleanup. Session retirement cancels only that binding; a late
old result cannot close its replacement. Ambiguous simultaneous owners fail closed;
only read-only probes can visit multiple endpoints, never automatic mutation replay.

ChatOwner uses the existing computer and encrypted chat store. API registration
keeps the OS-routed attempt first and uses the active exit only after transient
failure; TLS/auth/conflict and malformed successful responses stay terminal. The
existing mailbox route remains SYSTEM, then EXISTING_EXIT. SYSTEM is not advertised
as protected-underlying DIRECT. Existing AWG/TCP and independent support/notification
ownership are preserved. The GUI does not gain root privilege or a fake MESH item.

The shared Go adapter already supports service-only sessions, but Linux host
service-only orchestration and protected-underlying DIRECT are still NOT_INTEGRATED.
This phase does not turn an existing-exit-only adapter into full Android chat parity.
Windows public/native chat endpoint remains NOT_INTEGRATED. Next work must retain
one native coordinator through service-only→VPN handoff and validated-cache expiry,
without duplicate reconnect owners or a general user-application bypass.

### Verification and boundaries

Logs/thermal receipts: `state-client-build/desktop-parity106-20261023/chat-host-*`.
Artifacts, XML and readback scripts: `state-client-build/desktop-parity106-20261024/`.

- Initial unit-r1:30 PASS. Baseline regression-r1:1206 PASS before cancellation/
  cleanup refinements. Expanded unit-r2:41 PASS. Final regression-r2:1218 PASS,
  zero failures/errors/skips, one existing GI deprecation warning;54.18s pytest,
  56.03s wrapper/68°C. Counts overlap, not additive.
- Actual Unix peer credentials and SCM_RIGHTS transfer are exercised under an
  isolated ordinary-user fixture, with expected root UID substituted by fixture UID.
  A genuine installed root/user boundary is NOT_RUN. Tests cover wrong UID/device,
  forbidden fields, retired binding/replacement,30s open interrupted within2s,
  bounded4 live mailboxes, deadline/cleanup, and rejected duplicate/INET/file FDs.
- Duplex fixture sends64KiB in each direction byte-exact, including request half-close.
  Native lane/session in this host fixture is synthetic, not real media/TUN traffic.
  Shared/native race checks remain separate; no MESH/P1 or gateway egress PASS.
- Real ChatOwner, encrypted LocalChat store, disposable DeviceIdentity proofs and
  local ChatAccess challenge/register handlers cross the public host endpoint.
  Reopen preserves identity; revocation rejects the next challenge. Node remains
  pending rather than manufacturing delivery success. No production grants used.
- Linux-r18: six native packages race PASS, CLI builds;41.02s/68°C.
  Windows-r14: cross-build only,7.00s/63°C. Both seal the same295 source files.
- Component-r18: built14.00s/76°C; archive readback verifies98 members,22 root
  modules,4 common modules, exact source bytes, stdlib-only privileged imports,
  unit syntax and both native digests/inventories. Accepted175 common/2073 capsule
  checks and six chat-source pins match. No new screenshots: this is a backend phase.

### Internal artifacts and upgrade boundary

Paths below are relative to `state-client-build/desktop-parity106-20261024/`.

| Artifact | Path | SHA256 |
|---|---|---|
| Linux amd64 native | `bridge-linux-r18/fc-mesh` | `a0bd9072695a64c8859e7e9aef45b232ab28ed3d922df907ebb8072aaf65df78` |
| Windows amd64 native, cross-build only | `bridge-windows-r14/fc-mesh.exe` | `72b6e5e1de1c2db3624d828741c73f19f6f23e3523c4e5cda9ec89e79841ff1c` |
| Linux system/native/RNS component | `mesh-system-r18/FamilyConnect-MESH-system-amd64.tar.gz` | `25ad843628b808e7f20561e41495064f2bb580e34ec58c3fa06871c9bb46f998` |

Native inventory digest:
`3441bf1fc3d3fb7b3f370ad5edb007cd27a1a2a9dc25a2d3299c643b98732284`.
The archive is15,198,985 bytes. It requires the existing Linux x86_64 systemd254+/
resolved/iproute2/polkit/TUN/Python3 model and matching GUI sources. It is internal,
unsigned and not a complete AppImage/DEB/Windows installer. No signed update manifest,
Authenticode signature or new signed driver is supplied by these artifacts.

Nothing was installed or published, so no rollback occurred. A future explicit
privileged component setup must run with Family Connect disconnected, preserve its
verified predecessor for rollback, and leave identity/history/keyring untouched.
The new ordinary-user modules are included in full GUI bundle assembly/import tests;
legacy six-file updater shape is preserved. Full-bundle updater handoff and actual
installed upgrade still require implementation/acceptance, not an identity-reset
workaround. Remaining end-to-end gates: Linux installed MESH/P1/DNS/HTTPS, transfers,
sleep/interface/recovery and upgrade; Windows product integration/target OS; complete
visual parity and full private installers. No PARITY PASS is claimed.

### Owner-requested stop at this checkpoint —24.10,08:55 CEST

The owner requested finishing the current task, reporting the results and continuing
only in separately agreed steps. Phase22 is the last finalized task: source/tests,
native/component builds and evidence; not installed/live acceptance. Final delivery
readback passed in5.00s/65°C; evidence readback passed in1.00s/65°C and verifies20
source hashes,29 evidence files, both295-file inventories and3 artifact digests.
Whitespace check passes. No parity fixture unit or emulator remains running.
Work is paused by request, not complete or blocked. Protected DIRECT/service-only,
Windows integration and package/OS/visual acceptance have not been silently dropped
or started as another step. No install, rollout, rollback, identity or policy change.
