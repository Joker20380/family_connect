# Client installation

## CHAT-UX-1 — internal UI checkpoint,26 October

Ubuntu26.04/Python3.14 candidate **0.2.12~l03.2.8** is built for review only:
[report, screenshots and exact hashes](releases/2026-10-26-chat-ux-1.md).
Chats opens a separate adaptive window; Enter sends, Shift+Enter adds a newline,
and the emoji button opens the system chooser. Back returns to dialogs on narrow windows.
Onboarding keeps activation, system setup and messaging preparation explicit and separate.
DEB recommends distro `fonts-noto-color-emoji`; no hidden font download is added.
The owner workstation stays on **0.2.12~l03.2.7**; no new UI installation/publication.
Full suites still fail without suppression. STOP for review before any installation.
Public downloads and signed catalogs are unchanged. Development sections below are historical.

## Desktop parity106 — development only

Native worker binaries now exist for both amd64 platforms; they are internal
service components, **not user installers**. Do not replace an installed app with
these files. Linux isolated TUN/routing checks do not prove live MESH connectivity.

Development code now also persists bounded readiness receipts and performs the
independent authenticated ACK. This has local tests, not installed/live acceptance;
it does not enroll this computer or grant P1 access. Existing identities stay unchanged.

The development RNS bootstrap adapter now uses the accepted channel with a bundled,
isolated RNS1.5.1 runtime. Local actual-link tests cover its request/response and
cancellation paths; they do not prove a live desktop VPN or authorize P1. Windows
still needs its embedded Python runtime and broker integration; users should not
install Python or move these components manually to work around that unfinished work.

An unsigned offline Linux system-component installer now exists for development,
but has not been installed/accepted and is not an end-user app installer. Its exact
archive/hash and RU/EN instructions are in the report; do not use it as a public update.
No new application installer is available yet. Keep existing installations and their own
Device Identity; do not copy phone keys, delete data or reenroll for this work.
Current download links are unchanged. A future private candidate must pass actual
OS/TUN, UI and in-place-upgrade checks before handoff; public publication requires
a separate decision. [Feature matrix and exact gates](releases/2026-10-23-desktop-parity106.md).

The development GTK tree now connects manual MESH through its privileged service,
only when the verified system component is installed. Settings show selected and
actually negotiated profiles separately; Disconnect cancels service recovery.
Closing the window explains that MESH continues in that service. This is code and
synthetic-state UI-test coverage, not installed/live-VPN acceptance or an invitation
to replace the stable app. Android reference captures use only a fresh offline emulator.

### Support controls in the development build

Development GTK settings now includes **About / Diagnostics**. **Refresh Support
ID** asks the existing authenticated service for this computer's ID; **Copy Support
ID** copies only that ID, never a key. A failed refresh keeps the valid saved ID.
**Send diagnostics** first explains privacy, then **Save JSON** opens the OS save
dialog. Share that file with your chosen recipient yourself; nothing is uploaded
automatically. Export does not require shell/root access or disconnect the VPN.
It includes bounded public connection/session/startup information and omission
counts, not browsing history, messages, destinations or credentials. These controls
are source-tested/rendered development functionality, not a published0.2.11 update.
Windows counterparts, installed collection and full diagnostic parity remain open.

### Messaging in the development tree

The GTK **Messenger** page now uses the shared encrypted store rather than a
placeholder. Activate this computer first, then choose **Start messaging**. Its
separate chat identity is not copied from Android. The32-byte history key is saved
in the user's Secret Service; unlocking that keyring may be required. Missing or
damaged history/key material produces an error, never an automatic account reset.
Do not delete the keyring entry or the application chat directory to update.

Use **Add contact**, paste the entire public key and independently compare the
full fingerprint before saving. Contacts can be renamed; text can be queued and
edited, and encrypted history survives reopening. **Accepted by relay** does not
mean the recipient has stored the message; that has a separate verified receipt.
The Linux mailbox first follows normal OS routing (SYSTEM), including an existing
VPN, and never opens privileged bypass routes. The matching new root component also
allows bounded chat-only use of an existing authenticated MESH exit (EXISTING_EXIT),
bound to this computer and user. Authentication/conflict rejection is terminal.
This is locally tested source, not installed/live acceptance. Protected-underlying
DIRECT, service-only delivery without VPN, installed background-service acceptance
and complete UI parity are still unfinished.
These are development sources, not a published installer or a live-server PASS.

**EXIT messenger** in Chats opens background/notification preferences, stored in
the encrypted history. With background delivery enabled, an unprivileged user-session
service continues after the GUI quits; it is not the root VPN helper. Disable
background delivery here to stop delivery without an open, focused chat. After
closing the GUI with background disabled, the idle service exits within about36s.
The service does not start a new chat or bypass a locked/missing keyring. It starts
on application use, not as a new system-wide boot service. An existing chat resumes on app launch,
without replacing its keys or creating another identity on failure. System
notifications contain no message text/audio/contact name. Clicking opens the
verified conversation; viewing it in a focused window marks displayed messages
read. Failed/unavailable notification service leaves the pending flag unchanged.
The notification daemon's acknowledgement does not prove a popup was visible
(for example, Do Not Disturb can hide it). OS notification settings still apply.
**EXIT · service notices** shows Linux-targeted public announcements and retained
cached notices when refresh fails, including kind, revision, validity and author.
An announcement cannot execute a command or install an update. In the local Linux
candidate, the **⋮** menu opens announcement administration. The server must
authorize this computer's existing identity for every list, publish or edit;
ordinary users cannot grant themselves access. Compose a title and body, choose
**Preview announcement**, then explicitly publish. New announcements target all
three platforms for30 days. Editing retains the author, audience and expiry.
A revision conflict requires reopening the latest version. If a reply is lost,
retrying the same preview uses the same operation identity, not another announcement.
No real role was granted or public announcement sent during development.
Physical desktop notification-daemon/installed-package checks and exact Android
administration-screen comparison remain separate from local API/D-Bus/GTK tests.
If a send loses its service reply, check the conversation history before sending
again: the message may already be saved. The client does not silently retry an
ambiguous mutation. Normal updates must retain both the chat directory and vault.

Voice: hold the microphone control to record, slide left to cancel or up to lock;
keyboard activation starts locked recording. Stop/release opens a preview, not an
automatic send. Listen, pause/seek, then choose **Send**. Escape or leaving the
conversation cancels unsent audio. Limit60 seconds; no temporary audio file is
written. **Voice profile** defaults to Opus; Codec2 modes require explicit
per-contact support confirmation, independent of identity trust or VPN/P1 access.
The choice is stored in encrypted history. Linux requires system GStreamer audio
plugins and Codec2; an unavailable audio runtime reports an error, not a fake send.
Tests use a synthetic microphone and silent sink. Physical microphone/headphone
behavior and interoperability with a real Android installation remain NOT_RUN.

## Media transport name: MESH

The local candidate on the approved Android UI84 shows Auto / AWG 3.1 / TCP
REALITY / **MESH**. It names the existing media transport, not a new protocol or
a guaranteed bypass. Stored `telemost` selection, Device Identity and activation
do not migrate. The candidate is unsigned, not installed or published; download
links below are unchanged. That18-Oct report predates the current GTK/service work;
installed desktop releases still lack accepted product MESH. The development GTK
option is capability-gated, not an inert public button. [Historical status](releases/2026-10-18-mesh-product-integration.md).

**Private owner build, not a public release (12 Oct):** research84/code84 was
installed in place at11:47:34UTC, retaining package/signer/UID and data. SHA256
`fd3106170ceeb1e24dad6c8eacda4107b1ab09a6ee120ccf495d92d96841aa48`.
Native bytes are unchanged; no uninstall/data clear/re-enrollment. Not distributed
to testers or published; public APKs, invitation/download links/checksums unchanged.
No warm-start PASS: CONNECT occurred after gate cleanup; a later natural gateway
SEED_READ/UNKNOWN fatal was captured. Do not automatically repeat CONNECT.
[Private build and limits](releases/research84.en.md) /
[Exact outcome](releases/2026-10-12-whitelist-warm-start-1.md).

**Beta65/code65: [verified targeted APK](https://185.251.89.19:8443/downloads/FamilyConnect-Test-0.1.18-beta65.apk).**
Published05.10 10:25UTC; full HTTPS download, SHA256 and original signer verified10:27UTC.
ARM64,49671035bytes; SHA256
`dfbdb5352b8c707fb77ff3d7392d8217f898aa8e999b6a0f52fad8172185778e`.
Earlier gateway cleanup fixa813dc5 acceptance passed unchanged owner65 real-session recovery
with an injected policy-loss cause, AUTH/cancel, AWG/TCP and privacy checks. This does
not locate the original field DATA/ACK loss. Owner data/Support and signed bytes preserved.
Exports12/13 confirm tester65; no reinstall needed. The
[05.10 server readiness fix](releases/2026-10-05-readiness-clock-skew.md) is active;
unchanged owner65 obtains fresh native READY/ACK13:56:08UTC without installing an APK.
Export14 proves Telemost traffic and automatic restoration, but both sessions fail
after roughly20s. RTP gateway correction deployed05.10 **15:22UTC**, source8d04632/
SHA7c6e1e11, after CI/artifact acceptance. Unchanged owner65 fresh native READY/ACK
15:23:05 validates the new directory; no phone package of any kind installed.
Keep the working VPN and open Family Connect to refresh its directory. **Fresh
tester native READY/ACK for the post19:53UTC05.10 directory** must precede mobile Auto.
The previous evening certificate expired before work resumed after the interruption.
Credential-only renewal19:53UTC restores the window without changing the
APK or gateway binary. Fresh tester ACK for this directory confirmed20:00UTC05.10;
export15 contains an earlier pre-renewal attempt without a Telemost session.
That trial is now captured in export16: two real Telemost sessions transfer data,
but both fail after about20s despite successful first restoration. Do not repeat
the same trial; keep the working VPN. RTP correction is insufficient; investigate
VP8/RTP delivery instead of reinstalling or changing clocks.
Actual gateway bound **05.10 23:53:04UTC (06.10 02:53:04 Krasnodar)**; revalidate/renew
for later tests. After the short trial restore the working VPN and send diagnostic
JSON. No manual clock changes. Default download/catalog/invitation60 and older APKs
remain unchanged; access is not expanded.
[Current gateway, tests and rollback](releases/2026-10-05-field-export14-beta65.md#gateway-ci-artifact-and-deployment-pass).

**Historical beta64/code64: [immutable previous APK](https://185.251.89.19:8443/downloads/FamilyConnect-Test-0.1.18-beta64.apk).**
Installed on owner Redmi; published19:13UTC, downloaded SHA/signer/HTTPS200 verified19:14UTC.
APK SHA256 `b1a9f62116265b13a8482292175d3a685dca23ad3a5be0e4af5ef995a4d32d69`,49671035bytes;
installed bytes/original signer67a90d1b and identity preservation are verified. Matching
gateway/native exhaustion→recovery, saved paired diagnostics, AUTH/cancel and privacy PASS.
Effective material bound04.10 22:57:31UTC requires revalidation before later checks.
Earlier APKs/checksums and default60 are unchanged. Update in place over Wi-Fi, never
uninstall, clear data or reenroll. Verify64 and unchanged Support ID; open with VPN off.
Before one mobile Auto attempt, the operator confirms **fresh current-directory
fetch/native READY/ACK**, not an old cache re-ACK. Export JSON after failure before
manual reconnection. Tester64 is confirmed by server ACK19:21:49UTC, but that ACK
reuses old cache; fresh fetch is not confirmed and the mobile attempt remains gated.
[Release preparation](releases/2026-10-04-beta64-paired-candidate.md).

**Previous targeted public version: beta63/code63.** Its earlier CI/offline signing and
in-place identity preservation PASS. [Separate beta63 APK](https://185.251.89.19:8443/downloads/FamilyConnect-Test-0.1.18-beta63.apk)
verified04.10 16:57UTC: HTTP200,49654651bytes, downloaded/installed SHA256
`ce81216a84005880eef834dd5f576d0c43082b1c501767c7cf83522a765aebb8`;
signer SHA256 `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
Owner is now on64; do not downgrade to63. Any later authorized update must be in place,
never uninstall, clear data or reenroll. Verify the expected version and unchanged Support ID.
Initial reconnect acceptance used an injected policy cause. Subsequent
[genuine native exhaustion→poll→reconnect](releases/2026-10-04-beta63-native-exhaustion.md)
also passed on unchanged63 under controlled RTP loss. The original mobile stall is not claimed fixed.
The no-repeat instruction belongs to the earlier63 checkpoint; use the targeted64 procedure above.
Default/updater/invitation remain60. [Release gates](releases/2026-10-04-beta63-recovery-candidate.md).

**Beta62/code62 is a verified targeted upgrade only for FC-YHQB-9VJN.**
[Android beta62 diagnostic](https://185.251.89.19:8443/downloads/FamilyConnect-Test-0.1.18-beta62.apk)
passed in-place owner Redmi acceptance over61 r2; data/UID/Identity/Support, AWG and export pass.
HTTP200, downloaded SHA256 `f60b8d3a74b85a5934b942d7e273831e7c1d88d35e4d8a87db7332fb7d7703d4`;
signer SHA256 `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
Choose **Update** over the existing installation on working Wi-Fi. Do not uninstall
or clear app data; no new invitation is required. Verify62 and unchanged Support ID.
**Mobile export(11) has been received and correlated; no repeat is needed now.**
[First failure and recovery-policy blocker](releases/2026-10-04-field-export11-beta62.md).
Do not clear cache/data or reinstall the app.
Current server bound04.10 17:30:19UTC (20:30:19 Moscow), not four new hours on every
app open; about2h35m remained at14:55UTC. After expiry, refresh materials on working
Wi-Fi and verify readiness first. [Window verification](releases/2026-10-04-beta62-four-hour-rollout.md).
Real owner-session correlation is proven; the original disconnect is not claimed fixed.
[Checks and limitations](releases/2026-10-04-beta62-recovery-candidate.md).
Default download/updater remain60; the published61 r2 asset is not replaced.

**Previous beta61 r2 targeted release — historical acceptance; newer releases above.**
Data continuity/AWG/export and real client/server correlation pass; the original
disconnect is not claimed fixed. Separate verified download04.10:
[Android beta61 r2 diagnostic](https://185.251.89.19:8443/downloads/FamilyConnect-Test-0.1.18-beta61-r2.apk).
SHA256 `4297ea1a7124f048bdfca4889e89114e84465fab3100a3caea7cbe23cd5e35fb`;
versionName/code `0.1.18-beta61`/61, unchanged production signer. Do not supply
old61/c98852b3. [Acceptance/signature/rollback](releases/2026-10-03-beta61-targeted-acceptance.md).
HTTP200 and downloaded SHA256/signer verified; [delivery report](releases/2026-10-04-beta61-r2-direct-delivery.md).
This is not the default Android release: landing/updater and links below remain60. Supply only
the signed APK and choose **Update** over60, without uninstall, data clear or new
invitation; verify unchanged Support ID FC-YHQB-9VJN. Before one mobile attempt,
the operator must revalidate leases and fresh READY/ACK; export immediately after
disconnect. FIELD admission and the public updater remain unchanged.

**Current03.10: beta60/code60 is public**, with the same accepted APK SHA8ee59352
and signer67a90d1. Use the [installation/update guide](getting-started.en.md).
Settings → About / Diagnostics shows the registration-bound Support ID; copy it,
not keys, for support. Install over the app, never clear/uninstall. Existing FIELD
cohort owner+FC-YHQB-9VJN (2/cap3) is not expanded by updates. Historical preparation notes below are
superseded by the [publication report](releases/2026-10-03-field1-release-final.md#beta60-publication--2026-10-03).

## Historical preparation checkpoints

Final FIELD preparation adds a registration-bound Support ID in Settings → About /
Diagnostics (Copy Support ID). Candidate59 is still unpublished; old8229a36 is the
previous local build, not the revised candidate. [Current status and tester steps](releases/2026-10-03-field1-release-final.md).
Update over the existing app; never uninstall or clear data. Send the Support ID,
not cryptographic keys, and wait for explicit operator admission before FIELD tests.

Revised local candidate: source `5abc2da`, APK SHA256
`6d13720bc8cff25d51d95ff7453127577890bee881685a4a66c86fae163f2148`.
Installed in place on the owner Redmi03.10; not published. Identity/data retained,
Auto/AWG/TCP pass. Authenticated server delivery now returns the original backfilled
Support ID; visible/Copy/restart and diagnostics export pass. No replacement identity
or enrollment. Hosted release checks/publication remain pending; no wider FIELD yet.
The earlier `b952c3b` / `8229a36` build below is historical. Public download remains51.

FIELD candidate03.10: beta59/code59 source in local validation, **not installed or
published**. Download remains51 until in-place owner acceptance. Never uninstall
to update; retain identity/data/enrollment. [Release status](releases/2026-10-03-field1-release-diag1a.md).

Local candidate now built/signed from `b952c3b`, APK SHA256
`8229a36e8b176aa49346f3bf106f4f1229cb492a47c1c50e86593ddcb4c85a3b`.
This is not a public download or completed rollout; public links below stay51.

Latest private checkpoint03.10.2026: **`0.1.18-canary58-physical`/58 installed over57**,
same Friends package/signer/UID/data, encrypted restart READY/ACK_RECEIVED preserved.
APK SHA256 `91e8910896ff84b31a7cebf40f840256dca283d684b075577290d1282f227194`;
signer `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
Private launcher hook fixed and live ON/OFF tested. Physical rehearsal BLOCKED on
MIUI-denied ADB input/no manual CONNECT. Override OFF after restart; app disconnected.
Not a public release; public/invitation/catalog links unchanged and not reverified.
[Current installed state/provenance](releases/2026-10-03-5n-physical-hook-fix-and-rehearsal.ru.md).

Current private-device checkpoint03.10.2026: exact `0.1.18-canary57-physical`/57 is
**installed in place over55**, with the same package/signer and encrypted readiness
preserved (restart READY/ACK_RECEIVED). SHA256
`dd3c1b1bd9031f189ef7fc606969eb7da05e44f470478c8457f9097119b9c975`.
Private hook navigation crashed before restricted CONNECT; diagnostic override is OFF,
Auto retained, app disconnected. Physical acceptance FAIL, Stage5N not closed.
Not publicly distributed; public/invitation/catalog links unchanged and not reverified.
[Current installed state and exact failure](releases/2026-10-03-5n-physical-restricted-rehearsal-final.ru.md).
Earlier build-only statements below are historical.

Private acceptance build03.10.2026: `0.1.18-canary57-physical`/57 arm64 is signed,
**not installed or published**; the Redmi remains canary55. Same Friends package/signer;
debuggable packaging exposes existing diagnostic Activities for private acceptance only.
APK SHA256 `dd3c1b1bd9031f189ef7fc606969eb7da05e44f470478c8457f9097119b9c975`.
No public/invitation/update-catalog change; do not distribute this diagnostic build.
[Exact signer, local tests and credential-reload blocker](releases/2026-10-03-5n-physical-restricted-rehearsal.ru.md).

Windows0.2.15 targets Windows10 1809+ /11 x64 and bundles .NET.
After a failed0.2.13 installation, run the new installer over the remaining files.
No manual service setup is needed. Affected Windows10 device acceptance is pending.

[Русский](clients.ru.md) · [Home](../README.md)

Status checked 2026-09-23. Client features and release versions differ by platform.

## Android

Local compatibility investigation,2026-10-02: `0.1.18-canary56-challenge`/56 arm64
**built unsigned only**, not install/update-ready, installed or distributed. SHA256
`5ca1d29101df529cce197e5eeb82f231b50e3f4fc76c8835ba12fdad0c2122b0`.
Installed private55 and public/invitation51 remain last documented, unchanged and
not reverified. No new download/update link or catalog. Production503 cause remains
unproven; [local tests, pins and BLOCKED gate](releases/2026-10-02-5n-real-owner-challenge-503.md).

Attempt15,02.10.2026: private `0.1.18-canary55-receipt`/55 **installed over54** on the
owner Redmi, exact APK/signature verified; no uninstall/data reset. SHA256
`680a21f60e69cb62d2c7a70be07234b34196e178f0207ed69cb4b422b7bc6247`.
Real app challenge503 blocked READY; server restricted rollout rolled back. Phone
remains55, not a public/FIELD release. Public beta51/invitation downloads unchanged
and not reverified. Build-only statements below are historical checkpoints.
[Attempt15 evidence and limits](releases/2026-10-02-5n-prov1-attempt15.ru.md).

Local build checkpoint,2026-10-02: private `0.1.18-canary55-receipt`/55 arm64 adds
post-import structured readiness receipt and authenticated ACK. Same package/beta
signer, update-compatible with54; **built/signed, NOT installed or publicly distributed**.
SHA256 `680a21f60e69cb62d2c7a70be07234b34196e178f0207ed69cb4b422b7bc6247`.
[Local APK path, checks and contract](releases/2026-10-02-5n-device-readiness-receipt.ru.md). Installed54 and public
beta51/invitation links below remain last documented; no download link was replaced
or public artifact reverified. No production/authority change or rollout in this gate.

Checkpoint, 2026-10-02: private `0.1.18-canary54-prov1`/54 is built, beta-signed and
**installed in place on the owner Redmi** during attempt14; final APK/hash/signature
verified16:47UTC. No uninstall/data clear. Server deployment rolled back after owner
UI observation failed; restricted cache readiness is unverified. The app remains54,
not publicly distributed and not a FIELD release. Public beta51/invitation links
remain unchanged and were not reverified. [Attempt14](releases/2026-10-02-5n-prov1-attempt14.ru.md)
· [Canary provenance and SHA256](releases/2026-10-02-5n-android-canary-build.ru.md).

Use the [friends beta guide](getting-started.en.md): Android 8+, ARM64 beta60,
invitation-based access, VPN, text and voice messages. The APK is distributed through
an invitation page and HTTPS download; it is not yet a GitHub or app-store release.
The [client workflow](../.github/workflows/clients.yml) documents source-build requirements.
CI debug APKs are not update packages for an installed friends beta.

## Current invitation-page downloads

[Linux 0.2.11 AppImage](https://185.251.89.19:8443/downloads/FamilyConnect-0.2.11-x86_64.AppImage) · [Linux 0.2.11 .deb](https://185.251.89.19:8443/downloads/FamilyConnect_0.2.11_amd64.deb) · [Windows 0.2.15 / 2ffba77](https://185.251.89.19:8443/downloads/FamilyConnect-Setup-0.2.15-pilot-unsigned.exe)

Install the client, then open it from the invitation link or the **Open Family Connect**
button on the invitation page. Windows installs the URI handler with its service and
preserves existing activation.

Windows 0.2.15 is the primary version. Windows 0.2.14 is available as a compatibility
fallback for some older Windows 10 installs: the invitation page shows it as a secondary
**Download compatible version 0.2.14** action
([immutable EXE](https://185.251.89.19:8443/downloads/FamilyConnect-Setup-0.2.14-pilot-unsigned.exe)).

Linux is now distributed as regular user-facing artifacts:

- `FamilyConnect-0.2.11-x86_64.AppImage` — primary option; `chmod +x` and run; no pip,
  venv or source checkout. Host GTK/GI prerequisites are documented in the [report](linux-appimage-deb.ru.md).
- `FamilyConnect_0.2.11_amd64.deb` — Ubuntu / Debian / Mint: `sudo apt install ./FamilyConnect_0.2.11_amd64.deb`,
  appears in the menu and registers `x-scheme-handler/familyconnect`.
- `FamilyConnect-Control-Linux-preview-5b02e8cb9fde119f.tar.gz` — advanced/manual only.

VPN helpers are installed separately. SHA256 and checks are in [releases.md](releases.md)
and the [Linux report](linux-appimage-deb.ru.md).

[Windows GitHub preview](https://github.com/Joker20380/family_connect/releases/tag/windows-v0.2.15) · [Linux GitHub preview](https://github.com/Joker20380/family_connect/releases/tag/desktop-preview-20260926-5b02e8cb) · [Hashes and checks](releases/2026-09-26-server-list-crossplatform.ru.md).
Preserve identity and application data when updating. Windows0.2.15 uses its own signed update catalog; install it manually once from0.2.12 or earlier. Linux and the older shared catalog are unchanged. Desktop messenger parity is not claimed.
The separate historical GitHub v0.2.9 flow below is retained; use the current downloads above for new invitations.

Windows0.2.15 automatically creates the local device key on first launch. Access still needs an invitation: on the phone choose **Settings → Invite a friend**, send the full link to the PC and open it. Alternatively choose **Activate with invitation** on the PC, paste the full link and select **Activate access**. Launching only the desktop shortcut cannot supply the invitation. Existing access survives an update.

## Original GitHub v0.2.9: Linux

The original desktop release is the [v0.2.9 pilot](https://github.com/Joker20380/family_connect/releases/tag/v0.2.9).
The UI uses **GTK 4/libadwaita**, not Tk. Requirements: system Python with GI,
GTK 4.8+, libadwaita 1.2+, cryptography and NetworkManager with WireGuard support.
On Debian/Ubuntu, install the prerequisites:

```sh
sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 python3-cryptography network-manager
```

Download and extract `FamilyConnect-Linux-0.2.9.tar.gz` from that release. Inside the
extracted directory, run `sh install-linux.sh`, then open Family Connect from the
applications menu. Run the UI as your normal user; privileged operations use the
platform's authorization flow. The operator supplies device-specific activation/profile
setup. The release does not include the Android friends invitation flow or messenger.

For source installation, run `sh clients/desktop/install-linux.sh` after installing
prerequisites. Experimental paired control builds are separate from the six-file
release archive: [operator runbook](linux-control-preview-rollout.ru.md).

## Original GitHub v0.2.9: Windows x64

Download `FamilyConnect-Setup-0.2.9-pilot-unsigned.exe` from the
[v0.2.9 release](https://github.com/Joker20380/family_connect/releases/tag/v0.2.9).
The installer includes the native app, .NET runtime, broker and VPN components.
Administrator approval is needed for installation; a separate WireGuard app is not required.
A trusted Family Connect Authenticode publisher signature is still missing; do not
turn off security software to install it. No Windows ARM64 release is validated.

Use **Get device code**, give the public code to the operator, then import the
operator-issued `.fcactivation` file and connect. See the
[native Windows guide](windows-native.en.md) for key custody, activation and build steps.
Published desktop onboarding is not the newer Android friends activation flow.

## Updates and limits

Desktop update checks verify an offline-signed catalog and artifact hashes; see
[updates](updates.en.md). Android friends checks for updates in the app; Android asks the user to install the APK signed with the same beta key.
A successful build or installer check does not establish live VPN reliability on every
network. [Current platform evidence](STATUS.md) and dated release reports separate
installation, UI, networking and recovery tests.

[Historical initial-client guide](clients-legacy.en.md) is retained for the early direct
WireGuard experiment; its old Tk/Windows-wrapper instructions are not current installation advice.
# FIELD-1 publication notice — 2026-10-03

Android `0.1.18-beta60` / code60 is signed and accepted on the owner Redmi and by
the required hosted gates, and **publicly distributed unchanged**. Public SHA256:
`8ee59352e5f490aea74c3c8c8aeefd0d65bec0c261a044899d512ca376cf6104`.
Historical beta59 remains unpublished. Public invitation/downloads and both Android
catalogs now reference beta60; updates are optional, minimum1, FIELD owner-only/cap3.
