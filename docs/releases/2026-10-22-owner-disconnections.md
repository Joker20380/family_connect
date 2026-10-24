# Owner disconnections → private candidate, 22 October 2026

## Decision and scope

###23 October final closed-group handoff — supersedes owner-only gates below

PRIVATE_FIELD_READY for the owner-confirmed three existing devices. Same signed106;
bounded server P1 group deployed as a515 with one locked normal restart and verified
TLS/materials/publication. Post-deploy owner106 Wi-Fi/TUN/RS32/CREDIT128 and full1KiB
HTTPS PASS3.422s; consent renewed normally after its hour expired. No new APK/Connect.
Continuation budget8,408,064 bytes; collectors ended. Export21 adds a positive
Volgograd96 cellular MESH result with owner-relayed whitelist testimony; keep its
older94 incident and nonzero96 counters, no106/P1/cold-bootstrap inference.
[Final group, field evidence, file and rollback](2026-10-23-tester-p1-cohort.md).

###23 October reboot continuation — current gate

Fresh readback verifies105/UID/APK/native, Wi-Fi398 and VPN off. USB is authorized
but full snapshot still unavailable, so do not toggle active consent. Recovered
unfinished106; final219 JVM tests and recorded-budget replay PASS, all native bytes
unchanged.106 signed via existing vault, installed04:38:17UTC with same UID/native;
fresh normal JSON/Support ID confirmed. Ordinary Connect preserves both-end P1/TUN;
body/recovery are separate gates. Gateway3a08/single-owner P1
unchanged by this task; exact renewal PASS, cert/CRL valid until07:48:57UTC.
Fresh106 bounded Wi-Fi acceptance now19/19 complete (single1.189/parallel2.276Mbit/s).
Expected crossed RESET0→1 retained, actual/unclassified0. Ordinary Disconnect/Connect
and one full1KiB response pass. Subsequent controlled Wi-Fi-loss auto recovery PASS:
new session without Connect, matched gateway P1/RS32/CREDIT128, full1KiB HTTPS200
in3.733s. Wi-Fi creation→CONNECTED106.578s; this is bounded recovery, not instant
or overnight stability. New-session raw expected crossings8→8, actual/unclassified0.
Same continuation budget8,407,040/33,554,432 bytes; all temporary collectors ended.
[23 October report/evidence/remaining gates](2026-10-23-wifi-resume.md).
Historical failures and owner-attributed tariff clarification below remain intact;
The fresh recovery result is instrumental evidence, not inferred from the tariff
explanation. Whitelist validation remains NOT_RUN; tester P1 policy is still owner-only.
Old consent-denied next action is superseded.

### Supplied normal export15: stale ring and reproduced record-budget failure

Owner supplied `FamilyConnect-diagnostics (2) (15).json`; original bytes retained in
`state-client-build/owner-wifi-resume-20261022/export15-readback/owner-export.json`.
SHA256 `758586f2ccba84c00e8b12d6d0e54e0e60d7fb64ed03a2edbad659a7cfc9ddb5`,496,940 bytes.
Filesystem arrival/mtime is not treated as the diagnostic sampling/export time.
Both records confirm beta105/code105 and Support ID FC-4D8Q-REEG:

- `ring`: latest native sample19:43:11.901UTC, latest retained event19:43:11.845UTC;
  WIFI/CONNECTED/READY/TUN, RS32/32/effective32 and CREDIT128/131072, session
  `0d65d8c26973dac5f5e86460f5ec0a5f6950df480831d0f8b030e85309ef47d3`, already correlated
  to gateway.245886 sent/5003559 received payload bytes and5 protocol errors are
  retained as reported, not a benchmark/body-completion proof or rewritten counters.
- `incident`: retained FAILED/AUTH event19:33:17.334UTC and earlier history; not a
  new failure at export arrival. This does not explain the later20:05→20:27 VPN stop.
- Four historical sessions/128 events per record remain intact. Fresh live settings,
  network phase and security cache validity cannot be inferred from these records.

The saved ring serializes to261,081 bytes,1063 below the256KiB record limit. Local
`DiagnosticRecordBudgetReplay.java` executes retained105 `DiagnosticRing` and
`MuxLifecycle` classes with the build's pinned Gson2.13.2: the actual baseline
passes record and bundle export checks; adding **two synthetic duplicates** of a
retained valid incident context yields7 incidents (below32, no component-overflow
flag) and262,837 bytes. The unchanged record guard rejects this with `Diagnostic
bound`. Compile/replay PASS; raw owner file unchanged. This is an aggregate-budget
defect reproduced with recorded structure, **not** a claim that exactly those two
events occurred on the phone or a direct measurement of its inaccessible live heap.

Source path: `DiagnosticRing.snapshot()` combines independently bounded current/
history/event data without a total serialization budget. `Diagnostics.save()`
rejects oversized records before replacing the persisted ring; callers catch the
failure. `OwnerSupportProvider.openFile()` also rejects it and masks the specific
IO cause as `Snapshot unavailable`. `Diagnostics.share()` can successfully export
the old persisted ring/incident instead. This mechanism explains how a valid normal
JSON can be stale and is consistent with observed failures; other IO causes of the
earlier live-provider error have not been directly excluded. No claim of a new
MESH regression, no buffer increase, history clearing or transport patch.

Current read-only device check21:10:59UTC:105/UID10283, no owner VPN network, shell
route wlan0. Protected `status` now returns `SecurityException: Owner USB support
disabled`; unlike20:27, a new normal consent is required. Check stdout **and stderr**:
ADB exit0 is not successful authorization. Raw evidence is in `export15-device-readback/`;
its initial stdout-only summary misclassified this denial, superseded by
`summary-corrected.json` derived from both retained streams. No command was acted
on using that incorrect flag. No Connect/Disconnect, installation, signing, server
mutation or intentional application request was performed; budget remains0/32MiB.

**Next manual action:** enable **USB: разрешить поддержку на 1 час** in the app and
confirm its normal dialog. No MIUI/lockscreen bypass or hidden wait. A fresh readback
must precede any authorized normal Connect/current Wi-Fi control. The local record-
budget defect is reproduced but not fixed/shipped; resolve minimally if needed for
fresh normal diagnostics without suppressing errors, increasing buffer budgets or
reopening transport research. SIGNED_APK_READY remains YES for existing105 bytes;
PRIVATE_FIELD_READY remains NO. Delivery and whitelist gates are unchanged.

### Owner connected USB: actual105 verified; full JSON unavailable

After the owner's “подключил”, ADB identifies Redmi Note9 Pro31ce63ba, Android12/API31.
Read-only capture20:04:59UTC preserves package, APK, available app/system logcat,
network/VPN/services/power and process exit history without clearing anything.
The actual installed APK SHA256 is
`91ba2d6e4cb6d3c789e4921df96b79ea196d42bc602bc72ea727fa1489aef2a3`,
version `0.1.18-beta105-recovery`, code105, UID10283, same pinned signer; all12
native-library hashes match the already verified source/signing receipt. No
installation, build/signing, profile or server change was made.

The normal `/owner.support/snapshot` read and one separately preserved read both
return `java.io.FileNotFoundException: Snapshot unavailable` (ADB exit0 is not JSON
success). Protected `status` succeeds: consent is active, **not a request to renew
USB permission**. Source `OwnerSupportProvider.openFile` maps IO failures, including
the record-size guard, to this message; the underlying cause is not established.
Available `/data` space is27,283,324KiB; do not call it disk-full or a proven size
overflow. No bound bypass, new API, private-key/profile extraction or restart.

Separate observed phases: the20:05 capture contains full-UID MESH-address owner
`tun1`, Wi-Fi underlying network398; later20:27 and20:28 status is `off`, no owner
VPN network or ConnectionService, route via `wlan0`. No intentional application
request was sent over that direct route. Transition time/intent/root cause UNKNOWN;
neither manual Disconnect, automatic recovery nor APK/throttle causation is inferred.
Do not merge these into a connected Wi-Fi control or silently reconnect to pass.

Evidence: `state-client-build/owner-disconnections-20261022/raw-entry-20261022T200459Z/`
manifest SHA256 `721484b36650a48dc450ed930748ef5c04867a429f78c97a6877ff5d94f0d3cf`;
`state-client-build/owner-wifi-resume-20261022/usb-readback-2004/` and
`usb-current-state/`, latter manifest
`26e9b0c4dab25025b2f53721a10cdf3a718ea624b0c85dec4762dd898adbb597`.
No new continuous collectors; all acquisitions terminate. The32MiB ledger remains0.

**Next exact action:** in the app's Settings choose **Отправить диагностику**,
confirm normal export and provide the JSON. If export reports failure, retain that
message rather than clearing data/history. This supplies the normal saved ring/
incident bundle, which must be checked for freshness; it is not assumed equivalent
to a live snapshot. Current Support ID/settings and full-body/recovery remain open.
SIGNED_APK_READY stays YES; OWNER_WIFI_ACCEPTANCE is BLOCKED_FULL_JSON_VPN_OFF;
TESTER_P1_POLICY_READY stays NO; FIELD_WHITELIST_VALIDATION stays NOT_RUN.

### Wi-Fi continuation: corrected context and actual readback

**Source: owner's message,22 October2026:** «22 октября 2026 года владелец сообщил:
пакет мобильного трафика закончился, оператор ограничил скорость; на Wi-Fi
приложение работает нормально». This is not a new instrumental phone test. The
throttle rate, onset and installed version at that successful manual Wi-Fi check
are UNKNOWN; reconstructing them is not a prerequisite for fresh Wi-Fi acceptance.
The Wi-Fi upstream (including possible hotspot on the same SIM) is also UNKNOWN.

All mobile failures below remain real failures, not retroactive PASS. The external
factor prevents treating the latest mobile attempts as clean APK/P1 regression
evidence; absent time correlation it does not explain every historical failure,
Volgograd/Krasnodar incidents or all speed measurements. It proves neither a
whitelist nor MESH detection nor Telemost blocking. Locally reproduced software
mechanisms remain valid independently of the network trigger.

**Readback supersedes the paused summary:**

- `state-client-build/owner-pressure105-20261022/install-receipt.json` records
  successful `adb install -r`,104→105,12:13:13–12:13:29UTC, unchanged UID10283,
  matching installed APK/native hashes. Post-install VPN was false; app profile
  awaited a snapshot. A later command's exit1 is not evidence installation failed.
  The receipt's identity-not-rotated assertion is not fresh Support ID/key readback.
- Existing opt-in support storage, read19:51:15UTC via the normal read-only support
  mechanism for FC-4D8Q-REEG, contains a report stored19:42:25UTC: code105, WIFI,
  CONNECTED/READY, TUN open, RS send/receive/peer/effective32, CREDIT128/131072,
  terminal NONE,70088 sent/562101 received payload bytes,55 retransmissions and53
  cumulative recovery timeouts. These are not newly generated test bytes, zeroed
  counters or complete-body/controlled-recovery proof. No attribution of every
  timeout to throttling. Online export is a reduced snapshot, not full saved JSON.
- Both outside-sandbox ADB enumerations have **no attached device**. Current
  installed-file hashes, UID/identity/settings, full JSON/history, underlying-network
  continuity, no-fallback checks and actual Wi-Fi bulk/recovery are blocked. Do not
  reinstall105 or switch working P1 to P0 based on old documentation.
- Fresh Amsterdam readback: loaded binary SHA256
  `3a0804cd3da63135dce387d1dff9afdc4588562186abea2e5d00da1d9f5c31ae`,
  PID1794339, invocation `78db9a0d39584f169c88fa0ae3b879d3`, active, NRestarts0,
  start17:47:05UTC; profile SHA256
  `fa9d8344189241a1f55bcc00ebde078cd6d5e740f37eeb7df09e030718a013e0`.
  This differs from the midday PID/config; no restart/change was performed by this
  continuation and its cause is not inferred from the hash alone. P1 target remains
  configured; base mux LEGACY64, pacing/counters OFF. Exact gateway source overrides
  credit to128 for the matched P1 identity; the base flag alone is not a mixed-pair
  diagnosis. Real effective values still require session correlation.

**Independent fix review, no new functional patch:**

| Change | Evidence and retained boundary |
|---|---|
|102 health|Fresh bidirectional Mux DATA progress prevents DNS-only teardown; DNS failures remain logged. `sessiondiag` bytes come from accepted DATA/enqueued payload, not RTP keepalive, RS ACK or Mux credit updates. Sent bytes are not delivery proof; unrelated payload does not prove every application succeeds. Three failures without payload progress still recover.|
|103 deadline|Timeout remains distinct from explicit cancel; valid cache fallback retains validation, expiry/revocation/floors and runtime-generation guard. No stale-cache exemption.|
|104 reorder|Observed358–540ms late complete frames and red replay establish premature discard.750ms is a bounded engineering choice, not a universal optimum. Permanent gap advancement, small/complete frames, wrap, duplicates and finite memory have existing regressions; no timer sweep.|
|105 pressure|104 reproducibly clears complete queued frames at256-packet pressure.105 drains queued frames before skipping gaps, with unchanged capacity/time/retry/windows. Two normal/wrap red cases and green regressions support retaining this minimal correction. Good Wi-Fi would not disprove the old code defect.|

Existing105, **not a new build**, is the selected candidate pending owner acceptance:
`state-client-build/owner-pressure105-20261022/delivery/FamilyConnect-0.1.18-beta105-recovery.apk`.
SHA256 `91ba2d6e4cb6d3c789e4921df96b79ea196d42bc602bc72ea727fa1489aef2a3`;
native `37ba4fac656811dd979688a274f45aed85a3aa567f1fafb3987a81c020fa91f1`;
signer `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`;
package `com.familyconnect.app.friends`, versionCode105, Android12+/API31,
arm64-v8a,16KiB alignment. Fresh apksigner/aapt/zipalign checks, signed/unsigned
payload equality, all2071 source files,12 native libraries, exact three-file104→105
delta and213 retained zero-failure JVM results verify. Eleven native libraries are
unchanged. Initial verifier used a raw-file hash instead of the existing canonical
JSON source digest; corrected verifier passes, no artifact/source change.
Static package/signer/version/API/ABI update checks pass for retained88/94/104 APKs;
only104→105 has a physical receipt. Do not claim tester88/94→105 migration or actual
tester installed versions verified. No downgrade/uninstall/clear-data path.

Artifacts/receipts under `state-client-build/owner-wifi-resume-20261022/` are private:
`artifact-verification-3/artifact-readback.json`, `support-renewal-readback/`,
`renewal-session/`, `local-checks/` and `local-checks-host/`. The sandbox network
failure is retained separately; local loopback tests require normal host execution.
The public fixture `tests/fixtures/owner_disconnect/resume_verify.py` reads only
artifacts and cannot sign/install/measure. It does not certify live acceptance.

Fresh host regressions PASS: seven105 Go race packages (telemost/reliablestream/
tcpforward/wholedevice/familysession/sessiondiag/sessiontrace),12 actual Python
deadline-bridge tests, and gateway roombroker speed/Mux/lifecycle/seed-recovery
selection under race. These include byte-exact loss/reorder/pressure, cancellation,
late callbacks, cache/security and old-client compatibility according to their
existing test contracts; no fresh shaped-bandwidth benchmark or physical overnight
acceptance is claimed.213 JVM results are verified retained build results, not a
new run. Sandbox socket denial is not a transport regression. Embedded native
provenance pins `pressure.py` (`actual_runner_sha256`), not the generated runner;
the verifier reconstructs its source substitutions and exactly matches the saved
`executed-build-runner.py`. Both full hashes are retained in the receipt.

Later19:53–19:56UTC readback records PID1862598/invocation
`6dd00e9a5c00452496cb71ec66d00e85`, NRestarts1, start19:38:47UTC, **same loaded
binary and profile hashes** as the first read. The bounded restart window retains
systemd's scheduled restart, not a proven root trigger; do not attribute this to
the operator throttle, renewal or this read-only continuation. Crucially the
owner online session matches a19:41:57.596756UTC gateway `session_profile` in that
invocation: P1/RS32 local-send/local-receive/peer/effective, CREDIT128/131072,
local-write-completion false. This establishes paired profile evidence for the
saved online sample, not continuous connectivity or body completion.

Gateway certificate/CRL validity at read:17:46:54–21:46:54UTC on22 October.
RU credential-renewal timer active; latest service19:47:20–19:47:24UTC success/exit0;
directory-sync timer active, latest19:53:26–19:53:28 success/exit0. Legacy restricted-
sync timer inactive. No renewal, timer, floor, profile or security-material mutation;
phone cache expiry still needs phone readback. An on-disk gateway profile expiry
is not proof of successful future renewal or all tester materials being current.

**Acceptance boundaries:** OWNER_WIFI_ACCEPTANCE = BLOCKED_USB (positive reduced
online evidence, not a full-body acceptance); RECOVERY_ACCEPTANCE = controlled
network-return NOT_RUN; SIGNED_APK_READY = YES (existing verified bytes);
TESTER_P1_POLICY_READY = NO (single owner target);
FIELD_WHITELIST_VALIDATION = NOT_RUN; **PRIVATE_FIELD_READY = NO**.
Android's ordinary persistent profile selector needs no USB grant; gateway
`speedPolicy` still matches just one16-byte identity hash. No normal closed-group
allowlist is implemented by that deployed selector. Prepare the existing agreed
tester group through normal authenticated negotiation before calling this an
accelerated tester delivery; do not silently enable everyone or create enrollment.

New authorized Wi-Fi ledger: limit32MiB, intentionally requested/reserved0 bytes.
The old five reservations total25,204,736 bytes and remain unchanged, including
unsent reservations/failures. Carrier/media/automatic traffic is separate and not
zero merely because this new application-test ledger is zero. No mobile bulk,
continuous transfer, shared firewall shaping, public release, catalog/invitation
change, push, sending or new signing. No known local temporary collector process
was found; existing server monitoring was not stopped as an unrelated service.
Phone detail-capture OFF and full JSON availability must be read back before handoff.

**Next physical step:** connect the owner phone by USB; save current normal JSON
and available history before changes. If support access expired, use only its normal
in-app consent. Then bounded current-version Wi-Fi controls with the old endpoint/
meter (DNS/full small HTTPS,4MiB,2×2MiB, small-before/during/after, finite idle), not
a speed matrix. Explain the manual short Wi-Fi outage before starting observation,
exclude mobile fallback, and verify automatic transfer without a new Connect.
No new build is needed unless a specific fresh regression is demonstrated.
Rollback remains normal supported profile control only for a proven critical
defect; functional APK rollback requires a higher-code same-key candidate from
retained source, not replacing immutable bytes or resetting identity/security.

The following sections preserve the original chronology and failures.

###104 physical result and105 pressure follow-up

104's both-end P1 gate passes: effective32/32 and CREDIT128/131072, real Android
TUN. Six1KiB HTTPS bodies complete (TLS verified/HTTP200):5.782493/2.226213/
1.612069/2.555805/2.571110/3.811722s. Headers identify actual egress
186.246.45.246; this is not AWG/TCP fallback. The subsequent single4MiB response
closes after56553 bytes/16.485839s, curl18. HTTP200 is **not** a complete body.
Parallel control is not started; speed preservation is not accepted.

Session eba83f8f: first retained gateway RS exhaustion11:56:08.803,
DATA222/8 retries/pending32; phone11:56:15.174 and subsequent RESTORING. During
the preceding receive interval,56 retained `window` packet drops span31 VP8
timestamps at11:56:05.130. Source104 clears the entire queued reorder map when
an incoming sequence reaches its256-packet range limit. Local reproduction shows
this discards even a complete queued frame. A105 derivative drains queued ranges
in order before advancing over missing gaps, rather than discarding the queue.
The256-packet cap,750ms bound, RS retries/RTO/windows and security are unchanged.
No new packet logger or suppressed protocol counters. Two deterministic normal/
wrap pressure cases fail104 and pass105; the initial fixture syntax failure is
retained separately and is not counted as the behavioral red test. All seven
Go race packages and12 bridge cases pass.105 build/owner acceptance is pending.

Exact DATA222→discarded-frame identity is not retained; do not claim this proves
every loss in the failed bulk attempt. New failure remains in the acceptance
table. `beta104-pressure-analysis.json`, raw USB115800 manifest
`890a760bbb415a0608776a433ae334f825dbf288c9891ce4d019e10765cc08d1`, and
gateway11:55:45–11:56:45 manifest
`8936f9c2c8ba934d21958665d48fe6120f6b9f670dc399605e157c63deaed585`
preserve the evidence. Subsequently `accept-beta104-auto` confirms another
P1 session and a full1KiB HTTPS body in2.418794s without any new Connect.
This is genuine post-natural-failure transfer, not yet the controlled network
return scenario or acceptance of105.

### Current candidate104 — built, signed and installed11:52UTC

Owner104 retains103's verified Support ID after renewed USB permission; install
receipts confirm unchanged package/signer/UID and no uninstall/data reset. Actual
P1/transfer acceptance is running, not yet PASS. APK:
`state-client-build/owner-reorder104-20261022/delivery/FamilyConnect-0.1.18-beta104-recovery.apk`.
SHA256 `828ffe3534e22a61cecacd261f0875d5333682522d9533cb854cb11309436c1a`.
Unsigned SHA256 `344a3d4f64d713f2f8910b1565c1d9e2dee4c5202b7205de6029bfe253d77af7`.
Signer `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
Package `com.familyconnect.app.friends`, code104, minAPI31/Android12, arm64-v8a,
16KiB alignment. Only `libfc_restricted.so` changes among12 native libraries:
`f6628021200408a317770cd189dd10afb7bd53b4da802b67b4b4f55f0c88e28d`.

213 JVM/12 actual Python bridge tests pass. Go race telemost/reliablestream/
tcpforward/wholedevice/familysession/sessiondiag/sessiontrace pass, including
byte-exact complete late frames, wrap, duplicate, permanent loss, memory bounds,
ACK-loss, cancel and independent streams. Original ten-case failure and first
expiry-fixture failure remain saved. `source-delta-final.json` contains exactly
the version, receiver constant, adjusted expiry injection and new replay test.
`executed-build-runner.py` is preserved with SHA256 matching embedded provenance;
build/sign/install receipts are separate. Full platform CI NOT_RUN.

Gateway remains3a0804cd/PID1510765/invocation7117d925, profile hash0409b841 across
the five matched103 windows; no task server mutation. Rollback is a new higher-code
same-key APK from retained103 source/native, not uninstall or overwriting a release.
**NOT PRIVATE_FIELD_READY** pending actual104 recovery/transfer and ordinary tester
P1 delivery. Whitelist field validation remains NOT_RUN.

### 11:45UTC follow-up: complete late RTP frames localized

The earlier incomplete-receiver conclusion is superseded **for DATA85 attempts6/7**
by joining *all* hop-local events, not only events already carrying message IDs.
`reorder-complete-frame-analysis.json` joins same track/timestamp and contiguous
receiver sequence numbers. Attempt6: tail340 arrives first; prefix338/339 arrives
483ms later and both are explicitly dropped as `old_rtp`. Attempt7: tail345,
prefix343/344,358ms. The later `incomplete` observer records are flushes of these
prefixes, not proof that the third packet never arrived. All three packets are
observed. Other retained late groups show381/474/540ms. No endpoint clocks are
subtracted. Why the prefix is delayed before `track.Read` remains unknown.

The100ms reorder gap budget advances past these complete but late frames.
This is a concrete local contributor to the persistent RS head hole, not proof
that every unretained attempt/session has the same origin. Exact103 code fails
ten deterministic complete-frame cases (five observed delays, ordinary/wrapped
sequence IDs). Candidate104 changes only the Android reorder budget to750ms:
210ms above the largest observed540ms, below unchanged RS RTO1000ms. No retries,
RS/Mux windows, RTP encoding/pacing, Q1, gateway or security change. The256-packet
bound remains; a permanently missing packet is skipped on the next arrival after
the budget, not by a new timer. No infinite busy loop/timer is added.

The first broad regression run correctly exposed two existing fault-fixture
assumptions: they forced expiry by backdating101ms. Their injection now uses the
actual budget+1ms; byte-exact/order/one-retry assertions are unchanged. Failure
logs are retained. The subsequent corrected broad run passes; owner acceptance
is separate from these local tests.

After renewed USB grant,103 identity/readiness is confirmed by original
`raw-entry-20261022T113621Z`, manifest
`ed59b20b2c58720cb6c1e06f443fdb3bb023f713cab514857603e34c4966ae27`.
One ordinary Connect11:37:16.691 is not an automatic recovery test. Both-end
P1/TUN gate passes, but first1KiB HTTPS fails DNS in5.978830s; bulk is not started.
The natural RS failure and subsequent automatic CONNECTED/DNS recovery are retained
in `raw-entry-20261022T113928Z`, manifest
`0b7ed4685934f245eb6758726c7d3bba9d7491813281c2c0d977167d8430830a`,
and bounded gateway11:37:40–11:39:05, manifest
`c9ec96ce94bc5bc75ef02ae2535ed33b0f9a67717dc86415c26ba9f3ce01e40a`.
Shared task ledger now reserves16.0244140625/64MiB;3072B intentionally requested,
zero complete HTTP bodies so far. This is not a clean103 acceptance.

Earlier103 checkpoint: the initiating RS DATA-hole failures were reproduced
but the receiver boundary was not yet localized. A separate DNS-health teardown
mechanism has a narrow app-only correction and local regression coverage.
Beta103 was the **diagnostic/recovery candidate**, including102's health
correction and the deadline bridge repair described below, not a claim that RS
failures are fixed. No public release, catalog, invitation, push, tester message or shared
gateway modification is part of this checkpoint.

### Complete103 observed episode list,11:37:16–11:51:13UTC

Five active failures retained over13m57s, before the deliberate104 update. This
does not assert complete event coverage outside sampled/ring history. First
confirmed gateway RS exhaustion, then Android native failure/cleanup/recovery:

|Session|Last retained DNS|Gateway first RS/head|Android first native failure; cleanup|Automatic attempt → CONNECTED → DNS|
|---|---|---|---|---|
|55b46d83|11:38:20.968|11:38:31.050/DATA118|11:38:40.002;11:38:41.312|11:38:41.159→11:39:04.638→11:39:10.469|
|89cf34f5|11:39:10.469|11:40:26.361/DATA83|11:40:40.511; recovery wait11:40:41.215|11:41:16.224→11:41:44.919→11:41:51.977|
|312bff35|11:42:22.527|11:42:43.007/DATA183|11:43:01.899; recovery wait11:43:03.054|11:44:08.071→11:44:32.177→11:44:38.226|
|cb8eb4f5|11:44:38.226|11:44:59.239/DATA80|11:45:10.103; recovery wait11:45:13.738|11:47:18.760→11:47:44.424→11:47:50.152|
|1cc5c1fc|11:47:50.152|11:48:17.705/DATA190|11:48:27.555; cleanup11:48:30.883|11:50:35.990→11:51:08.428→not retained before capture|

These are whole RS/MESH session closures, not evidence of app/gateway crashes or
one Mux stream closing the tunnel. No explicit Disconnect was issued during this
103 window. Later `IO_CLOSED`/TLS/ICE cleanup does not replace the first RS cause.
Underlying-network unavailability duration is unknown; measured35/65/125s waits
are recovery backoff, not inferred network downtime. Five automatic installations,
four retained post-recovery DNS responses, zero completed intentional HTTPS bodies.
Discovery of the102 receiver contributor does not retroactively prove the same
per-attempt packet mechanism in these103 episodes.

Pre-update original `raw-entry-20261022T115113Z` manifest:
`9713a769edf6ce4017e85373687d2955b9c0e3080752bdef195bb7b0db50ffce`.
Matched gateway labels beta103-first/89cf/312b/cb8e/1cc5 contain104/39/40/41/46
reassembled records respectively, no continuation errors. Native first-failure
snapshots and19 passive samples over120s are retained in `post103-build-observation`.
Post104 original `raw-entry-20261022T115351Z` manifest:
`ab74f17a3f53fcf3240edd6a3fdec743cc52bf52d680042991228892dc043f56`.

This supersedes the stale entry summaries of the
[21 October report](2026-10-21-p1-owner-acceptance.md), not its recorded measurements.
The late private `completion-results.json` and final readback recorded101/P1;
the fresh USB readback, not the earlier100/P0 summary, is the current baseline.

## Evidence preserved before transport changes

ADB identifies the attached owner Redmi Note9 Pro, Android12/API31, UID10283.
Support ID is obtained from that device's authorized provider; no tester device
or tester diagnostics are used. Full identifiers and raw evidence remain private.

Private root: `state-client-build/owner-disconnections-20261022/`.

- `raw-entry-20261022T095322Z/`: first read, existing app/system lifecycle logcat,
  package/APK, process/service/exit history, network/TUN, UTC/uptime/boot ID.
  USB JSON initially returns `Owner USB support disabled`; this error is retained.
  Manifest SHA256 `c5e402b9ca88847350642009a2c248602ffd11502938c7633dc44852bfeac5cf`.
- `raw-entry-20261022T095450Z/`: authorized JSON obtained after owner interaction,
  without Disconnect/Connect, force-stop, cache/data/logcat clearing or reboot.
  Manifest SHA256 `bb09e91da29fe64ae64035d7df711c85899b55ae670e29dbeec3712d37583c55`.
- Each acquisition stores original stdout/stderr, acquisition UTC/host monotonic
  interval, result and SHA256, with read-only raw files. Analysis is separate.
  USB `/snapshot` exposes the in-memory ring, session incidents and four archived
  sessions, **not** the separately persisted `diag-incident.json` or entire native
  JSONL file. Those inaccessible private files have not been silently read through
  another permission path. The retained ring begins21:25:27.900UTC on21 October;
  archived traces/boundaries report eviction. This is not a complete night history.
- Initial state is DISCONNECTED, no owner VpnService/TUN. PID8738 remains alive;
  the latest recorded process exit is the previous installation, not a new crash.
  Current logcat is preserved without clearing; it cannot reconstruct missing
  previous-night events. No OOM/panic or Android process death is established.

Installed baseline: `com.familyconnect.app.friends`, code101,
`0.1.18-beta101-lifecycle`, APK SHA256
`3c023e39d95e29fe0561dc462e28f1e643b9e14558cf49700d58df528b2963d9`.
Restricted native SHA256
`97d0bf793f8c4bb9975f32579f19369df0e7201786609ab9f46decdea3fec263`.
The pulled APK's12 native libraries are inventoried and its signer verified.

Gateway on authorized `186.246.45.246` reads loaded SHA256
`3a0804cd3da63135dce387d1dff9afdc4588562186abea2e5d00da1d9f5c31ae`.
22 October readback PID1421746, start07:45:26UTC, NRestarts0, profile hash
`d6455812f2514297beb2d5c1c2587bc8f647b7c7bb0a82283bc66b697f9b572d`.
Renewed profile bytes differ from21 October; no old profile is restored.
Both-end session profiles are P1: RS32/32/peer32/effective32, CREDIT128/131072,
Q0/local-write-completion false. The operator's legacy flag alone does not describe
the negotiated Mux. P1 remains owner-targeted, not an existing-tester rollout.

## Matched chronology

First journal query covers only21:26:20–21:27:00UTC. The five retained owner session
tags justify expanding to21:25:00–21:34:10UTC, still only the Family Connect unit.
565 reassembled records, no continuation errors, one invocation/PID976867.
There is no process restart or generation/renewal transition in this interval.
Lease deadlines are still in the future at the observed session terminations.
No seed1011, preceding signaling/ICE failure or Mux session violation explains
these first stops. Later TLS_ERROR and ICE/PeerConnection closed are cleanup.
Timestamps below are endpoint-local UTC observations, not one-way network latency.

| Session prefix | Last confirmed Android DNS | First established initiating mechanism | Android recovery and result |
|---|---|---|---|
|1a5826dc|21:26:17.266|Gateway21:26:37.190 RS retry exhaustion: DATA186 hole,8 retries; recent ACK969ms, pending32. Android agrees receive_next186 with later DATA buffered. Android first failure21:26:42.096.|Detection0.559s; automatic attempt21:26:42.655, CONNECTED21:27:10.568, DNS21:27:16.515. Attempt→CONNECTED27.913s; attempt→DNS33.860s.|
|2d918cdc|21:27:16.515|Gateway21:27:28.030: DATA65 hole,8 retries, ACK age880ms. Android first failure21:27:32.970.|Cleanup21:27:37.173; recovery_wait21:27:37.234. CANCELLED21:27:50.145 before next attempt; origin not retained, not automatically attributed to a user.|
|87d56884|21:28:27.230|Gateway21:29:17.138: DATA128 hole,8 retries, ACK/progress age442ms. Android first failure21:29:25.705.|Detection2.386s; attempt21:29:28.091; CONNECTED21:29:54.448; DNS21:30:00.523. New installation26.357s; first DNS32.432s after attempt.|
|f8e002c3|21:30:00.523|Gateway21:30:15.535: DATA9 hole,8 retries, ACK age275ms, only3 pending. Android first failure21:30:37.824.|Detection3.621s; recovery_wait21:30:41.477; next attempt21:31:16.503; CONNECTED21:31:42.649; DNS21:31:48.291. Backoff35.026s, installation26.146s, first DNS31.788s after attempt.|
|095b068e|21:31:48.291; continuing authenticated data thereafter|Android DNS probes fail21:32:23.675/21:32:59.141/21:33:34.629. Still native2/NONE, active Mux data and increasing carrier RX through21:33:34.211; no native terminal. Health policy initiates blocking/cleanup by21:33:34.721; cleanup21:33:34.932, recovery_wait21:33:35.001.|CANCELLED21:33:41.627; origin unknown. Gateway RS exhaustion21:33:43.836 is **after** Android cleanup, not the initiating active failure.|

The first four establish RS's termination decision and a missing DATA sequence
despite later DATA/ACK progress. They do **not** establish whether that DATA failed
before local RTP write, in the media path, or at receiver processing. Per-attempt
enqueue/write/receive history for the missing server head is not retained fully.
No blind retry/timeout increase or automatic Q1 transplant is justified. Three of
these four have zero Mux protocol errors; stream-local late terminal errors are
not the session cause. Fifth-session raw counters24 Android/27 gateway remain.
Carrier byte progression is not an independently verified full HTTPS body.
Underlying-network availability/history is incomplete: the recorded backoff is
not relabelled time spent waiting for an unavailable network.

## Fresh bounded baseline recurrence,22 October

After preserving the initial evidence, one authorized ordinary Connect is issued
at10:03:57UTC. No profile change and no intentional HTTP/speed traffic.
16 snapshots span10:04:22.184–10:07:15.685UTC (173.502s); matched gateway interval
10:04:00–10:07:40UTC is207 records with no continuation error.

- `0148875f`: gateway10:04:39.701 RS/DATA97/8 retries, recent ACK901ms;
  Android first failure10:04:48.818, automatic RESTORING10:04:51.615,
  CONNECTED10:05:19.701, successful VPN-bound DNS10:05:25.378.
  Same-clock detection2.797s, new setup28.086s, attempt→DNS33.763s.
- `b2a147f2`: successful DNS10:05:25.378/10:05:57.804/10:06:28.158;
  gateway10:06:44.376 RS/DATA107/8 retries, ACK age702ms; Android enters
  recovery_wait10:06:58.508. The bounded collector ends before its next result.

The subsequent pre-install acquisition `raw-entry-20261022T102320Z` preserves four
more active failures; do not count only the first collector's two. Manifest SHA256
`0a87848ead96c106a24725dced6f121e44507613a44804e47e4ca61e94d6183d`.

| Session | Gateway first RS exhaustion | Android terminal / recovery wait | Next CONNECTED |
|---|---|---|---|
|441c9c7e|10:08:45.324, DATA50,8 retries, pending3|10:09:00.451 /10:09:00.711|10:10:28.991|
|5378c31c|10:11:02.721, DATA49,8 retries, pending7|10:11:15.045 /10:11:15.298|10:13:44.345|
|d426f0f6|10:15:40.093, DATA225,8 retries, pending3|10:15:54.911 /10:15:55.159|10:18:24.516|
|65eb5b41|10:18:50.974, DATA28,8 retries, pending4|10:19:10.351 /10:19:10.580|10:21:40.121|

Six active RS closures in the observed10:03:57–10:23:17 window, about19m20s,
with app/background traffic, not a benchmark. Coverage is sampled, not a complete
packet log. The first has genuine automatic recovery and post-recovery DNS.
At10:15:40.580 the gateway service starts a separate stop/start sequence,
returning10:15:50.837 with PID1510765/invocation7117d925… and the same binary.
This is **after** d426's first RS exhaustion, not its initiating cause. No task
command restarted it. NRestarts0 alone does not exclude this controlled restart.
Three45–55s windows plus the441c interval are retained; the first5378 query timed
out and its later successful, same-interval readback is separately named.

## Minimal candidate and local verification

Exact101 source capsule is copied, not replaced by repository main. New102 Java
policy retains the30s DNS cadence,5s probe bound and three-failure recovery rule
when application progress is absent. A failed DNS probe alone no longer closes
a currently authorized native-ready session if **both authenticated Mux RX and TX
increase in the same session with fresh samples**. Heartbeat/frame counts do not
qualify. Native/auth failure is checked again after the blocking probe; denied,
terminal, malformed, stale, reset or old-session samples cannot suppress recovery.
The45s sample freshness bound accommodates the existing30s cadence,5s poll and
5s probe with one poll allowance; it is not a larger retry budget or timeout.
Every DNS_PROBE_FAILED remains; DNS_TRAFFIC_PROGRESS is separately recorded.
New engine generation gets a new policy. This fixes the DNS-only teardown rule,
**not the earlier RS DATA loss** or proof of the external DNS failure's origin.

-210 JVM checks PASS:203 inherited plus7 policy/schema/diagnostic tests.
- Red/green: exact101 three-failure decision rule extracted into a deterministic
  policy harness fails the third-probe/progress regression; corrected policy7/7.
  This is a policy regression, **not** a full native/Android loss reproduction.
- Go `-race -count=1`: reliablestream, tcpforward, wholedevice, familysession,
  sessiondiag PASS. Existing byte-exact/loss/reorder/ACK-loss, crossed-terminal,
  cancellation/neighbor, bounds and legacy/P1 integration tests are reused.
- Bootstrap96 cache/auth tests are in the JVM gate. Native/wire/RS/Mux/P1 and all12
  native libraries stay byte-identical. No server behavior/security delta.
- Exact gateway `TestSeedRecovery*` under Go race PASS: seed1011 classification,
  budget/cancellation, parent/runtime-generation isolation remain covered.
- Initial sandbox socket failures and a missing pinned Git build context are
  retained; host rerun uses the original pinned base plus exact source inventory,
  not a weakened verifier. Full platform CI is NOT_RUN for this private candidate.

## Artifact, rollout and remaining gates

Retained102 artifact: `state-client-build/owner-disconnections-20261022/delivery/FamilyConnect-0.1.18-beta102-recovery.apk`.
SHA256 `bd7eab4920c7358c1343c0a4a6f425df7483301044e051fad3ee365b6a948427`.
Signer SHA256 `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
Package unchanged; code102 selected after actual101 readback; Android12+/API31,
arm64-v8a;16KiB alignment verified. Protected existing-vault signing, no secrets
exported or placed in CI/server. Installation receipt is authoritative; signing
alone does not imply installation, owner acceptance or tester distribution.

102 is installed in place. `raw-entry-20261022T103034Z` verifies code102, unchanged
Support ID, READY, same signer/UID/native. Manifest SHA256
`bfba8dd2976194e746926523a98db924afabf3e1f8246c8e04978070462419a5`.
Package replacement ended the previous VPN and process-local USB grant, which the
owner renewed; it is not a claimed automatic reconnect across installation.

## Physical102 acceptance: failed, all new failures retained

One Connect10:35:18.945; CONNECTED10:35:45.709, DNS10:35:51.425. Both-end P1,
RS32/32/peer32/effective32, CREDIT128/Q0, actual owner TUN routing are read back.
The following active failures are not erased by later DNS success:

| Session | Last successful phone DNS | First gateway RS / first Android RS | Automatic next CONNECTED / first DNS |
|---|---|---|---|
|2aca1f37|10:35:51.425|10:36:13.316 DATA85,8 retries,pending3,ACK age19ms /10:36:31.080|10:37:00.921 /10:37:06.697|
|c38441b1|10:38:09.754|10:38:50.627 DATA130,8 retries,pending6,ACK165ms /10:39:00.146|10:40:10.771 /10:40:16.492|
|77cc6e3b|10:41:18.570|10:41:30.048 DATA111,8 retries,pending2,ACK1168ms /10:41:42.962|10:43:10.412 /10:43:17.771|
|2314658e|10:43:49.468|10:44:14.549 DATA68,8 retries,pending2,ACK411ms /10:44:27.877|10:47:00.545 /10:47:07.604|

Four failures in10:35:18.945–10:46:03, approximately10m44s; the last recovery's
result comes from the later explicit-intent pre-snapshot. App recovery transitions
follow native failure; TLS/ICE cleanup is not its first cause. Raw Mux error counts
are0/1/2/0, not suppressed. Underlying-network wait duration is not established by
these snapshots. No manual Connect between these automatic recoveries.

Same-phone timing, seconds; detection means first native failure → orchestrator
NETWORK decision, not time from an inferred network drop:

| Failed session | Detection | Scheduled backoff (not network wait) | New attempt → CONNECTED | New attempt → first DNS |
|---|---|---|---|---|
|2aca1f37|0.620|no delayed series; attempt10:36:32.879|28.042|33.818|
|c38441b1|5.037|35.011; attempt10:39:41.400|29.371|35.092|
|77cc6e3b|0.815|65.029; attempt10:42:50.018|20.394|27.753|
|2314658e|1.915|125.022; attempt10:46:36.046|24.499|31.558|

Time waiting for a truly unavailable underlying network is UNKNOWN in these
natural episodes. First full HTTPS after recovery is NOT_CONFIRMED, not equated
with the successful DNS. This is bounded recovery evidence, not a passed gate.

`head85-analysis.json` joins **sender/message IDs**, not cross-machine clocks:
gateway attempts6/7/8 each show successful actual local RTP writes,3 packets/frame.
Phone's retained matching attempts6/7 each show an incomplete frame with2 packets;
nearby old_rtp drops are visible. Attempt8 receive boundary is not retained.
This narrows the observation to local write → complete receiver VP8 delivery, but
does not distinguish missing/delayed media from receiver discard for every attempt.
No proof of retry-before-local-write; Q1 and all retry/timeouts stay unchanged.
Ring gaps and differing SFU RTP identifiers prevent a complete packet reconstruction.

`DNS_TRAFFIC_PROGRESS` appears without suppressing the failed DNS event. The two
metered1KiB HTTPS requests nevertheless fail (DNS resolution, then15s connect
timeout), with zero complete bodies. Controls stop before any bulk request.
Reserved8.0126953125/64MiB, actually requested2048B; failed attempts are included and
reservations are nonrefundable. **Single4MiB/parallel2×2MiB NOT_RUN; current speed
preservation is not accepted.** The21 October2.3× result is historical, not replaced
with an inferred102 speed. Background user traffic is separate.

Explicit USB Disconnect10:47:39.655–10:47:40.091 releases TUN; seven observations
over45s remain DISCONNECTED, no reconnect. Its CANCELLED has a known command source.
Explicit Connect10:48:27.418 then fails readiness at10:48:59.414; the90s acceptance
fails and is retained. This is neither another active RS disconnection nor a
successful automatic-recovery test.

## New readiness failure and narrow103 derivative

The fresh102 trace has cache validation READY, age146s, expiry1792678537, but
`selected_source=NONE`: direct HTTPS CHALLENGE TIMEOUT, then RNS RELAY_REQUEST
INTERNAL/PROTOCOL, refresh duration30270ms. The saved source's shared30s deadline
is included in `Callbacks.cancelled()`. Its Python `_wait` checks that callback
before its own deadline, raising generic OSError; the bridge converts this to an
internal challenge failure, which cannot select valid cache or classify availability.
This mechanism reproduces on exact102; the original exception type/string is not
retained on the phone, so this is not asserted as the cause of the earlier RS loss.

103 separates explicit cancellation from shared-deadline expiry at the existing
Java/Python bridge. Only the known timeout becomes typed transport unavailability;
cancel wins when both apply. Unknown, malformed, trust and authorization errors
are not converted. No proof/request replay or new route. The original valid-cache
warm-start rules and restoration generation-refresh guard remain intact. An initial
experiment allowing cached runtime during every restoration fails five existing
cutover tests; it is **reverted**, not shipped or hidden by rewriting those tests.

Exact Python bridge red/green:102 fails the shared-deadline regression;103 passes
12 bridge tests, including old bootstrap96 cases, cancel priority, no request on
expired deadline, malformed/denied failures and release of the RNS session lock.
The first sandbox test attempt is retained; the final test uses a socket stub and
no production traffic. Immutable102 artifacts remain unchanged;103 has a separate
source/build/delivery directory `state-client-build/owner-deadline103-20261022/`.

Final103 build:213 JVM tests PASS, all five unchanged cutover regressions PASS;
native libraries byte-identical, same P1/Q0 parameters. The earlier five-failure
build and sandbox Gradle socket failure remain recorded, not a release candidate.
API query only10:48:20–10:49:10UTC first times out; explicit current-journal-file
readback returns zero records. Coverage/completeness is unknown, so this is not
proof that a network blocked the request. Both acquisition manifests are retained.

Latest signed APK, **installed owner-only over102**, no data reset:
`state-client-build/owner-deadline103-20261022/delivery/FamilyConnect-0.1.18-beta103-recovery.apk`.
SHA256 `0d274fe5e0250301242d0307ae69c345bb27e935d79248d859afde817693fb04`.
VersionCode103, `0.1.18-beta103-recovery`, package/signer/API31/arm64-v8a unchanged;
UID10283 and native hash verified by installer. Build/signing/install receipts are
separate. The signer receipt says `SIGNED_DIAGNOSTIC_CANDIDATE_NOT_FIELD_READY`;
installation is not owner acceptance. Process-local USB grant requires renewal.
103 Support ID and running profile readback await that grant;102 preservation was
verified. No public artifact, update catalog, invitation version or tester changed.

Remaining physical gates:103 identity, current P1/TUN DNS/full HTTPS, same-profile
small/bulk control if small responses pass, background/screen-off, controlled owner
network loss/return without a new Connect. No shared-gateway outage. USB observation
is not overnight/Doze acceptance. FIELD_WHITELIST_VALIDATION remains NOT_RUN.

Primary missing evidence remains a complete initiating RS attempt's receiver
arrival/discard/assembly boundary; retained attempts now include actual local writes.
No claim that deadline/health fixes resolve those failures. P1 selection/distribution to existing testers also remains
unaccepted: current gateway higher profile is owner-targeted. Do not forward102
as an accelerated whitelist field build. FIELD_WHITELIST_VALIDATION=NOT_RUN.

Rollback: no shared server change to undo. Do not uninstall/downgrade or clear
identity/floors. If103 requires reversal, produce a higher-code same-signer build
from the desired exact101/102 parent; next-session P0 is a temporary safety fallback, not a P1 fix.
Public artifacts/catalog/invitation versions are unchanged and not revalidated
as part of this private task. [Candidate instructions](../clients/OWNER_RECOVERY_CANDIDATE.md)
and [reproduction](../../tests/fixtures/owner_disconnect/README.md).
