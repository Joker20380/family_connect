# Online MESH renewal qualification / 5 November 2026

## Late-fixture EOF defect and bounded correction

Corrected-underlay API27 on6befd10 **FAIL**,300.139s, before READINESS_HELD:
`SSLHandshakeException / Connection reset by peer`. Both synthetic HTTPS adapters
log `EMFILE` at1024 descriptors. The original adapter forwards upstream EOF as a
half-close but waits indefinitely for client FIN, retaining two descriptors and a
handler. A deterministic socket-pair reproduction against the actual frozen Handler
confirms this; normal client close releases it. This explains the new underlay-run
failure, not the earlier API35 VPN timeout (its route logs have no EMFILE evidence).

Repair is restricted to `tests/android_core_route.py`: origin HTTP EOF terminates
the forwarding pair, while client half-close still permits the complete response.
Two targeted tests pass; no descriptor-limit/TTL/trust/security-timeout increase.
The original failed logs/receipts and unused API35 preparation are retained; owned
AVD/stands/routes stopped. New paired late receipts are required on the corrected
adapter. The running G4 uses its separate frozen copy and is not modified or restarted.
No new gateway package or production changes; A still open, B not started.
[Reproduction and exact failures](2026-11-06-mesh-android-remaining-evidence.json).

## Legacy Android completed:6 November11:41UTC

API27/API35 **PASS_LEGACY_PEER_ONLY** on teste5c20eb, packagebfff97d/archive5721a5c1,
explicit legacy overlay drivere641e2cd and diagnostic native39c69de/d1025a1d.
[Receipts, APK hashes, phases and clocks](2026-11-06-mesh-android-remaining-evidence.json)
record real HTTP readiness, validated encrypted-cache successor after cooldown,
existing owner/native traffic and refusal to commit a successor without peer exchange.
Duplicate refresh does not change the owner; Disconnect leaves the old lease closed;
a separate explicit new Connect succeeds. The two-NL native preflight additionally
records exactly one offer and unchanged security deadlines; neither result claims
that a legacy session was extended or that cryptographic expiry was crossed here.
Both owned NVIDIA/KVM AVDs and supervisors/routes are stopped, with final receipts.

Corrected late-owner API27 is running; API35 follows on the same existing runner.
The initial API35 fresh-TCP timeout remains a retained FAIL, not an explained/fixed
product defect. G4's unchanged-package c8eb8b9 run is independent and still RUNNING.
No new package, release, accepted A checkpoint or phase B. Older checkpoints below
retain the states observed then; this is the current continuation pointer.

## Remaining Android cases:6 November11:13UTC checkpoint

**Follow-up test correction:** late-case coordination used the VPN data path to poll
its fixture state every500ms. It now explicitly uses the existing `ChatNetworkAndroid`
underlay HTTPS helper for `/qualification/*` only, independent of the owner it must
close. Ordinary product readiness, validation/cache/owner/native delivery, native
echo and the initial verified VPN HTTPS check are unchanged; no timeout/trust/clock
or acceptance assertion is relaxed. Other scenarios keep their existing control
path. This isolates test orchestration; it does **not** fix or explain the retained
API35 fresh-TCP timeout, which remains an open Android data-path observation.
Both late cases require new receipts on this corrected test source before a paired
PASS claim. Legacy Android is running separately against the explicit negative peer.

[Exact APK/native/server identities and receipts](2026-11-06-mesh-android-remaining-evidence.json).
API27 late-closed-owner **PASS**,319.028s: actual HTTP completion reaches the locked
cache import, normal Disconnect closes the owner, then validated encrypted-cache
completion leaves the old native lease closed. A later explicit Connect works; it
is not renewal or resurrection. This is the requested closed-owner alternative,
not a claimed wall-clock certificate-expiry crossing.

API35 same scenario **FAIL**,257.498s, before READINESS_HELD: a new HTTPS TCP to the
isolated fixture-control endpoint times out after10s while polling state. The earlier
Family service/HTTPS and echoes succeeded; host/AVD initial clocks passed, leaf/CRL
were still valid,310 native TCP flows, peak2, limit_denied0. The test finally requests
Disconnect; later gateway close is cleanup, not proof that it died first. Cause
inside the VPN/control route is **not localized sufficiently to label product versus
harness**. No retry or relaxed timeout, trust, clock or expectation. Its failed log,
diagnostics, gateway trace and route receipts are retained. Both NVIDIA/KVM AVDs and
their own Android supervisors/routes are stopped; G4's independent run is untouched.

Legacy peer preparation is separate and **not Android PASS**. A compiler overlay on
frozen bfff97d omits only registration of the optional credential-exchange handler;
the actual TLS, broker, lease, reader and all validation remain the shared code.
This synthetic old-feature peer is **not** the production gateway, normal isolated
driver, or a G1/G4 online-runtime acceptance artifact. Its explicit delta manifest
records base inventory, original/overlay hashes and distinct binarye641e2cd. The
normal bfff97d archive and driver remain byte-identical. No test feature enters a
release. This is a negative compatibility fixture, not another authorization writer.

`legacy-preflight3-bfff97d.log`:5 PASS,89.56s (four fixture guards and real two-NL
preflight). Each original native session offers the valid delivered successor once,
does not commit it, retains generation0 and exactly the original security deadline
through61 checked TCP/DNS/verified HTTPS samples; separate fresh sessions succeed.
No security-clock substitution. This does not replace either Android HTTP/cache case.
The first overlay used a symlink path and produced the normal digest: NOT_QUALIFIED;
a new unchanged-binary guard rejects that. Two initial preflight FAILs are retained:
missing normal seed-directory publication, then non-root-owned driver custody. The
accepted fixture uses the existing publisher and root-owned copied executable, not
manual profile writes or disabled reader checks. API27/API35 legacy are still NOT_RUN.

**A not accepted; B not started.** G1/G2 scoped PASS retained; G3 is incomplete with
a real API35 FAIL; corrected G4 c8eb8b9 is RUNNING, not PASS. One next is remaining A:
localize that control-route failure, run the legacy Android cases, then reconcile the
already-running G4 result. No unrelated suites, release/production/phone/paid changes.

## Finished frozen runs read back6 November

**10:43UTC continuation:** corrected full harness c8eb8b9 is running on the identical
bfff97d archive/driver, first renewal due13:13:02UTC. Owned containers
`fc-mesh-full-core-bfff97d-c8eb8b9` and its two `c8eb8b9` route helpers have independent
output `full-core-bfff97d-c8eb8b9/full-core/progress.json`; a waiter records exit/log
and stops only these helpers. This is RUNNING, not PASS or a rerun of expiry.

The existing Android runner now has `late-closed-owner`: hold a real HTTP completion
at the cache-import monitor, close the normal owner, then allow validation/encrypted
cache completion and assert the old native lease stays closed. Only afterwards make
a separate explicit Connect. This targets the specified closed-owner alternative,
not wall-clock certificate-expiry proof. Source/test checkpoint only until actual
API27/API35 runs finish. Runner/metadata selection30 PASS; disposable APK compile
42s PASS. Two setup failures (missing `fcTestBuildType=friends`, first also incorrect
local tool paths) are retained as `android-late-gpu27-apk1/build.log` and `build2.log`;
corrected `build3.log` is not runtime acceptance. Legacy remains NOT_RUN.

[Sanitized final receipts, identities and exact unexecuted boundary](2026-11-06-mesh-frozen-run-results.json).
No candidate was rebuilt or stand restarted to obtain these results. Source remains
bfff97d, archive5721a5c1, separate driver0fead52a; production gateway6032b926 is not
this driver. Original failed runs and all foreign work are retained.

* Expiry52c91f5: **PASS**, exit0,14423.91s, finished03:51:34UTC. At03:51:31 and
  03:51:33UTC both packaged resumes return exit1 and the exact stable-block response
  `FAIL_CLOSED / ONLINE_RUNTIME_RECEIPT / automatic_retry=false`, after candidate
  leaf/CRL expiry03:51:27UTC. The frozen test asserts byte-identical journal and
  canonical profiles, unchanged serving processes, expired loaded leaf/CRL, original
  COMMIT/plan/fence and no publication/start/rollback. Safety, not availability recovery.
  The initial d968ddd assertion FAIL remains a separate failed run, never relabelled.
* Full37ffc2c: **FAIL**, exit1,27092.71s, finished07:13:57UTC. Both NL complete two
  online renewals, native confirmations and23395 useful traffic samples each,
  generation0→2 on original TLS/mux/TCP with real crypto/lease crossing. Preserved
  socket byte counters increase; no normal-renewal process replacement. The combined
  emergency closes those sockets intentionally, reconciles lost start and recovers.
  Line173 then reads `node.live/gateway.json`, the old setup fixture, instead of the
  `profile_locator` canonical file. Read-only retained-state inspection confirms the
  revoked serial in both real CRLs and floor6>4, COMMITTED with original COMMIT parent.
  This is a **harness evidence-path defect**, not grounds to mark the run PASS.
  NL2's final rejection check, fresh allowed TCP/DNS/HTTPS and idempotent replay were
  not reached. Both test containers and owned route helpers have stopped; cleanup
  receipts confirm waited processes and absent reader sockets.

Repair scope: reuse the canonical lookup already used by `bounds`, plus decoy/missing
profile regression and the existing packaged emergency test. No runtime security,
TTL, clock, eligibility,1395s+lateness or package change. A corrected full run is
justified by this exact fixed assertion, not a blind retry. The successful long
prefix is retained as scoped evidence, not renamed complete G4.

Targeted correction check: `canonical-profile-check.log`,12 PASS/0 SKIP,84.26s
(two canonical-path guards, nine existing budget/sampling guards and real packaged
revoke-after-COMMIT/approval recovery). The latter uses the same canonical reader
as corrected G4 and proves both revoked denial and new allowed traffic. This short
regression does not retroactively execute the missing tail of37ffc2c or accept G4.

| Gate | Current result | Evidence / limitation |
| --- | --- | --- |
| G1 | PASS isolated core | Existing bfff97d approval/revoke/start-intent regression retained |
| G2 | PASS isolated process/RPC matrix | Existing bfff97d root/package fault cases plus52c91f5 actual expiry repeat; stable-block is not auto-recovery |
| G3 | INCOMPLETE | Positive/owner/partial-connect GPU cases retained; legacy/too-late NOT_RUN on both APIs |
| G4 | FAIL |37ffc2c finished at stale-fixture assertion; real two-renewal prefix retained, final traffic/replay missing |

No independent accepted A checkpoint yet; B UI/storage/routing/recovery for all
transports NOT_STARTED. One active next: finish remaining A. Release/live/field
constraints remain unchanged, not new isolated gates. Nothing installed or published.
All earlier waiting-state snapshots below are historical, not current results.

## Continuation checkpoint6 November00:06UTC

**Newly demonstrated compared with a30966c:** a frozen package now supports actual
both-NL Family TLS/mux/TCP/DNS/verified HTTPS through the real serving reader and
supervisor; retained API27/API35 GPU evidence additionally proves real HTTP validation,
encrypted cache, normal owner/native successor delivery, owner replacement and a new
Connect during partial publication. This continuation requalifies the new bounded
seed-lifecycle candidate; it does **not** yet prove two long renewals or all G3 cases.

[Current exact identities and result paths](2026-11-05-mesh-seed-continuous-evidence.json).
Runtime/package **bfff97d**, separate driver `0fead52a…`, archive `5721a5c1…`.
The production gateway digest `6032b926…` is not the driver digest and its Telemost
path is not qualified by local packet transport. The old online8c876e3 archive is
rehashed unchanged; original999s evidence retains its original source/scope.

| Gate | Result at checkpoint | Exact scope / remaining boundary |
| --- | --- | --- |
| G1 | PASS, isolated core | bfff97d packaged revoke/approval/restart/lost-start/repeat/new TLS traffic regression; full combined G4 still pending |
| G2 | FAIL, original expiry test | d968ddd first expired resume safely blocked; required repeat was not reached. Current bfff97d/52c91f5 repeat waits until03:51:29UTC |
| G3 | NOT_RUN, complete gate | Retained paired GPU HTTP/cache/owner/partial cases PASS; actual legacy-peer/too-late cases not complete |
| G4 | NOT_RUN, complete current path | bfff97d/37ffc2c running, first renewal due02:12:33UTC; previous fd7562c budget FAIL is retained, not relabelled |

`regression-bfff97d.log`:68 PASS/5 SKIP,1404.49s. The missing configuration was
`FC_TEST_SNAPSHOT`, not disabled code. Host snapshot construction lacked RNS; its
resulting five failed checks are preserved in `snapshot-bfff97d-checks.log`. Building
inside the locked Python image produces byte-identical bfff97d snapshot capsules.
With that artifact, `snapshot-bfff97d-locked-checks.log` runs all five missing cases:
5 PASS/0 SKIP,13.78s. Report these selections separately; the earlier3-case preflight
overlaps the larger run and is not added. Affected native `-race -count=3` remains
PASS/0 SKIP with artifact-enabled bootstrap. This is **not full CI PASS**.

The full-path harness and expiry harness have independent frozen source IDs and
normal cleanup; full-path route adapters stop after its test exits. No emulator is
running. No new Android runtime is claimed in this continuation: the existing GPU
receipts and unchanged native `d1025a1d…` remain scoped evidence, not full G3.

**Checkpoint status:** A has no independently accepted source/integration checkpoint
yet. Split tunneling UI/storage/routing/recovery for AWG/TCP/MESH/Auto is NOT_STARTED;
there is no B artifact/checkpoint. These source pushes install nothing. One active
next is to finish A's real-time/remaining G3 qualification on the recorded combination.
Then the original release-qualification → separately authorized delivery → both-NL
live renewal/field gates → controlled paid-beta queue remains unchanged. Exact release
binary/Telemost/systemd, paired-DNS/WebSocket, weak network, screen-off and mobile
allowlist gates remain open; no phone/production/catalog/timer/paid changes occurred.

## Actual successor expiry23:46UTC: safe block, incomplete repeat

[Exact source/package/result/journal receipt](2026-11-05-mesh-expiry-evidence.json).
The d968ddd stand waited14408.39s under real wall clock after controller SIGKILL at
durable COMMIT. Candidate leaf/CRL expire23:46:02UTC. At23:46:05UTC normal packaged
`resume` returns `FAIL_CLOSED/ONLINE_RUNTIME_RECEIPT`, not the harness's expected
emergency/recovery result. The already-expired loaded predecessor makes the real
reader reject its profile and close the socket without a valid receipt; capability
preflight stops **before** controller recovery. The retained journal remains the
same COMMIT, plan and fence1, with no publication. No expired rollback or restart
was used. Cleanup waited processes and removed reader sockets.

The original assertion terminated before the second resume: **test FAIL, G2 not
accepted**, not evidence of repeatability or a completed emergency handoff. A stable
precisely explained block is an allowed G2 outcome. The test now explicitly admits
only this exact fail-closed response, asserts unchanged journal bytes, canonical
profiles and serving process identities, and verifies their leaf/CRL have actually
expired. It records both raw responses before assertions. Unrelated/unknown failures
are still rejected. This is a test-only correction, not a reader-custody or approval
bypass, and needs a fresh4h qualification on bfff97d before any PASS claim.

Separately the fixed G4 harness37ffc2c runs on unchanged bfff97d package/driver;
its first renewal is due02:12:33UTC6 November. Source/tag/hash/runtime roles remain
distinct. G3 legacy/too-late delivery is still missing; A/B are not accepted/started.
No production, phone, publication, paid or emulator action accompanies this result.

## Frozen repeating-seed candidate and observation guard

[Candidate identities and evidence](2026-11-05-mesh-seed-continuous-evidence.json).
Runtime/package source **bfff97d** is pushed and remote-verified. Its own archive and
separate driver pass the early both-NL Family TLS/mux/TCP/DNS/verified-HTTPS preflight,
real reader binding/cleanup and release-command rejection of local/continuous flags:
3 PASS/0 SKIP,103.15s. These tests do not run for8h or prove repeated renewal.
Affected bootstrap/wholedevice/qualification/bootstrap-broker native `-race -count=3`
passes with0 SKIP, fresh ProductStore fixtures and the bfff97d Python publication
artifact. Root/package/process regressions are separately running, not yet PASS.

Review found a harness observation race: the native COMMIT callback can precede its
next traffic sample. The deadline check now waits for **both** sampled generations as
well as callbacks. Nine focused guards pass; controlled observations do not establish
wall-clock continuity. The initial bfff97d long run is intentionally stopped **before
any renewal** to freeze that test-only fix. Its log is
`full-core-bfff97d-sampling-restart.log`; this is not a runtime-expiry failure. The
new harness retains the same immutable runtime package/driver and its own source ID.

The older fd7562c5h/8h budget failure remains unchanged evidence. Current complete
G4 is still NOT_RUN on the corrected combination; G2 real expiry and G3 actual
legacy/late cases remain. A is NOT_ACCEPTED, B NOT_STARTED. No emulators/owner phone,
production, publication or paid operations. One next is completion of this corrected
full path, not another architecture or a split-tunneling distraction.

## Bounded repeated-seed source candidate23:36UTC

`SeedManager.ContinueRotation` defaults off and reuses the existing overlap loop,
publisher and timer. It requires at least half-lifetime spacing, preserves each
seed's expiry, publishes only after normal provider/readiness, retires old endpoints
and waits all workers on shutdown. Creation failure preserves only the current finite
seed; publication failure stops the runtime, without retry/authorization bypass.
The separate driver can explicitly request4h seeds/2h rotation for8h; production
`bootstrap-broker` retains Telemost-only options and its existing4h duration cap.

Five-generation endpoint/traffic/cleanup, failed third-generation creation/publication,
invalid overlap and previous finite behavior run under the native bootstrap suite:
`seed-continuous-bootstrap-race-configured.log`, `-race -test.count=3`, PASS/0 SKIP,
fresh disposable ProductStore fixtures plus the frozen fd7562c Python publication
artifact. `seed-continuous-budget-guards.log`:8 PASS/0 SKIP,0.04s. Scheduling tests use
a controlled clock and are **not** cryptographic-continuity evidence. No Android
emulator was started for these checks. The earlier unconfigured targeted log is
retained but does not replace this artifact-enabled run.

This is a source checkpoint, not a replacement of the failed full-run receipt or an
accepted A/package. Next: a new immutable source/package/driver combination, early
two-NL traffic preflight and the actual8h G4/remaining G2/G3 path. No production,
phone, publication or paid operation; release/live/field gates stay unchanged.

## G4 concrete stand-budget failure23:28UTC

[Sanitized exact receipt](2026-11-05-mesh-seed-budget-evidence.json): the current
fd7562c archive/driver with e144e81 full-core harness completes the first COMMIT on
both NL at23:12:08UTC. Generation0→1 preserves original session/socket and TCP/DNS/
verified HTTPS. Its actual client deadline is01:40:59UTC, whereas the next online
eligibility is01:42:00UTC: **61s short even before SSH120's1395s + lateness budget**.
No security clock, profile, database or marker was modified to finish the test.

The common `carrier/bootstrap/seed_overlap.go` schedules generation2 only after
generation1; `gatewayruntime.Run` exits when the active seed ends. With4h lifetime
and1h rotation this provides5h, not the requested8h. The earlier7h d968ddd soak has
the same incompatibility. Both were intentionally interrupted and normal finally
cleanup waited processes and removed reader sockets. Their original logs remain;
neither actual expiry nor a second renewal is claimed. The independent5h d968ddd
successor-expiry scenario remains running and is not invalidated by this horizon.

| Gate | Current result | Proven scope / remaining runtime |
| --- | --- | --- |
| G1 | PASS, isolated core | Existing package approval/revoke/restart/new traffic receipts retained; final combined repetition pending |
| G2 | NOT_RUN, complete matrix | Existing process/RPC subsets retained; actual candidate-expiry run pending |
| G3 | NOT_RUN, complete gate | Both APIs positive HTTP/cache/owner delivery, owner replacement and partial Connect pass; actual legacy/late cases missing |
| G4 | FAIL, stand budget | First current-package renewal only; no second renewal/boundary-crossing/emergency acceptance |

`full-core-seed-budget-final-guards.log`:7 PASS/0 SKIP,0.04s. These are arithmetic
preflight/regression guards, not lifetime implementation or wall-clock acceptance.
No common production runtime changes in this checkpoint. Next is a real long-lived
SeedManager/publication lifecycle retaining its trust boundaries, then a new frozen
combination and full G4. A is **NOT_ACCEPTED**, B **NOT_STARTED**. Release/live/field
gates and all existing immutable artifacts remain unchanged; no delivery occurred.

## Paired partial-publication new Connect result23:00UTC

**Additional proven user scenario:** after explicit Disconnect, API27 and API35 create
a new real ConnectionService/native owner while NL2 has not published the successor.
Fresh authenticated HTTP readiness retains the predecessor's security material, native
validation passes, and the new owner carries checked mux bytes and verified HTTPS.
The controller subsequently resumes the **same COMMIT** and finishes publication. The
previous connection is deliberately closed; this is not seamless TCP continuity.

[Exact artifact, clock, decision and cleanup receipt](2026-11-05-mesh-android-partial-connect-evidence.json).
API27 completes61s and API35 completes71s, both `PASS_PARTIAL_CONNECT_ONLY`, wrapper exit0.
The accepted API27 run uses a fresh synthetic invitation and aligned clocks on its first
measurement, with no clock writes. The runner may observe for a60s retry budget (10s per
ADB read), but cannot set time or relax validation. Both accepted AVDs use NVIDIA/KVM;
only one AVD runs at a time. All Android stands/AVDs now stopped normally.

The failed API27 clock samples (approximately7s and9s behind) and API35's erroneous
whole-response comparison remain in their original directories. They are not replaced
or included as passes. The final assertion intentionally excludes only the changing
challenge/issued-at envelope fields; it requires the same device, revision, issuer,
certificate, CRL/floor, directory and expiry, plus actual native validation and traffic.
The paired owner-race evidence above remains a separate scenario and separate artifacts.

Final affected runner/receipt selection: `android-partial-connect-final-guards.log`,
29 PASS/0 SKIP/0.35s. It includes the earlier overlapping GPU/network/metadata checks and
new strict clock observations; do not add these selections together. Final APK builds
pass83 tasks each. No production/native/package implementation changes in this delta;
the earlier fd7562c67-test frozen selection, native race count3, artifact-enabled bootstrap
and421-test Android JVM results remain their original evidence, not new/full-CI runs.

| Gate | Status | Current evidence and unfinished scope |
|---|---|---|
|G1|PASS, isolated core|Retained frozen revoke/approval/restart/new-TLS/DNS/HTTPS evidence; final integrated repetition is in the running G4 test.|
|G2|NOT_RUN, complete gate|Process/RPC subsets PASS; real successor-expiry continuation still running to23:46:04UTC.|
|G3|NOT_RUN, complete gate|Both APIs pass positive delivery, closed/replaced owner and partial-publication new Connect. Actual legacy peer and too-late delivery are still missing.|
|G4|NOT_RUN, complete gate|fd7562c two-renewal/crypto/lease/emergency run active; first renewal due23:11:57UTC. Older d968ddd soak remains separate evidence.|

The online archive stays fd7562c /846818adefa292939034b9c427d658cfd3c427f48d1fb522dbda104f31aeb94f;
local driver180f386f… and Android native39c69de /d1025a1d… are unchanged. Original
online8c876e3 /a27502d7… and the accepted maintenance archive are untouched. There is
**no independently accepted A checkpoint yet; B UI/storage/routing/recovery are NOT_STARTED**.
No product APK version/catalog change, installation on the owner's phone, production
rollout, release publication or paid operation occurred. No installed rollback is needed.
Physical Telemost, exact production-binary/systemd and remaining field gates are not
closed by this isolated packet/supervisor setup. The one active next remains finishing
G1–G4, then preserving accepted A before the separately scoped Android feature.

## Paired owner-race result22:43UTC

[Sanitized artifact/runtime receipt](2026-11-05-mesh-android-owner-evidence.json) now
records both actual runs: API27 runtime339s with the preserved final-wrapper exit1;
API35 runtime363s, narrow `PASS_OWNER_RACE_ONLY`, wrapper exit0 and normal cleanup.
Source038b66a1af7a30ed79e3a8697c8ce6c72ffa6548 is pushed and remote-verified. Native
d1025a1d… is unchanged before/after both runs. Both server stands and GPU AVDs stopped.
This closes the application-completion/owner-race subscenario only, not full G3/A.

The subsequent partial-publication **new Connect** test remains in progress. Its first
API27 attempt failed initial native validation before Connect: host start1793918040.946,
guest1793918034; actual issued leaf NotBefore1793918036. The AVD clock was about7s behind,
beyond the unchanged5s certificate backdating. No clock was set or validation relaxed.
A new runner guard records host-before/guest/host-after and refuses excessive skew
before instrumentation. API35 had aligned clocks and did connect during partial
publication, but the test compared the entire readiness response: a new authenticated
challenge legitimately changes wire bytes. The corrected assertion compares device,
revision, issuer, certificate, CRL/floor, directory and expiry, and still runs native
validation. Earlier failed logs/artifacts are retained; no PASS is inferred from reaching
Connect alone. G2 actual expiry and G4 full-core remain running; B NOT_STARTED.

## Actual Android owner-race continuation22:25UTC

New relative to a30966c and the positive-only cases: API27 completes a real normal-owner
readiness fetch after real300s cooldown, then exercises delayed **application completion**
across explicit Disconnect and a new explicit Connect. The test holds the existing cache
import monitor only after the frozen API generated a valid successor. Verified TLS bytes
are released unchanged; the actual readiness thread reaches `RestrictedBootstrap.refresh`
and blocks on that monitor. No mocked future, native credential injection, modified
profile, security-clock change or production scheduling hook is used.

With import still pending, the normal service closes its old owner; the next explicit
Connect obtains a different owner. After the monitor is released, native validation and
encrypted persistence complete normally, the new service connects with the successor,
and borrowed native mux streams transfer checked bytes. This is not an assertion that
the old TCP or HTTP socket survived Disconnect, nor delivery into a closed native owner.
The separate late-security-deadline case remains unqualified.

API27 `android-owner-gpu27-emulators2/api27-runtime.log`: `OK (1 test)`,339.069s;
`HTTP_COMPLETED_IMPORT_PENDING`, `OLD_OWNER_CLOSED_BEFORE_IMPORT`,
`NEW_EXPLICIT_OWNER_WAITING_FOR_IMPORT`, `OWNER_RACE_VALID_SUCCESSOR_NEW_EXPLICIT_OWNER`,
then normal cleanup. Its wrapper exit1 is retained: the final runner assertion still
required `PASS_POSITIVE_PATH_ONLY` after recording the new `PASS_OWNER_RACE_ONLY` scope.
The correction explicitly allows only these two narrow outcomes; five new guard cases
reject FAIL/RUNNING/invented full-G3 PASS. Targeted GPU/receipt selection21 PASS/0 SKIP,
not an additive total or full CI. API35 runs the identical Android test sequentially;
both test APK builds pass83 tasks. The initial API27 build invocation used a relative
Gradle init path and failed before compilation; its separate log is retained. Its first
route-helper invocation lacked the read-only busybox mount; the no-egress preflight
refused before an emulator was started or invitation consumed. Neither is a PASS.

Commands remain the existing `tests/android_core_partial.py --scenario owner-race`
with frozen fd7562c archive/driver/snapshot inputs and
`tests/android_core_emulators.py --api 27|35 --service --isolated-network`.
Only androidTest/fixture/runner source changes; production owner, trust, credential
delivery and TTL/timeouts are unchanged. G1 isolated evidence is retained; G2 actual
expiry and G4 full-core remain running; full G3 and A are NOT_ACCEPTED, B NOT_STARTED.

## Both GPU Android positive paths complete22:00UTC

**New full user scenario relative to a30966c:** on both API27 and API35 an active MESH
VPN receives usable successor credentials through verified HTTP, validates and stores
them in the encrypted cache, and renews the existing native session through the normal
ConnectionService owner after a real partial two-NL publication and cooldown. It does
not reconnect, bypass TLS, inject a profile into SessionMaintenance or change clocks.
This closes the positive delivery subscenario, not every G3 case or phase A.

[Sanitized machine-readable provenance, timestamps and bounds](2026-11-05-mesh-android-gpu-evidence.json).
Scenario source checkpoint2e3d1801ed98a3a2a7f327408d0325fcceda59c3 is pushed and
remote-verified. API27 runs650s; API35 runs669s. Both finish `OK (1 test)` /
`PASS_POSITIVE_PATH_ONLY`, `SERVICE_SUCCESSOR_COMMITTED_SAME_OWNER` and normal cleanup.
Both original and successor leaf/CRL bounds are real; SSH120 and the1395s+lateness window
are unchanged. Initial synthetic age selects valid overlapping material, not a frozen
security clock or extended production TTL. Both original native artifact checks match.

The first GPU API35 attempt failed before APK installation when `svc data disable`
returned20 after Android reported boot completion. The runner now uses a60s retry budget
(10s per command) for both ordinary network commands to succeed, retains failed output and still
fails closed; it never treats an unavailable command as success. A fresh AVD reused
only the still-unconsumed synthetic invite (no readiness requests or activation had
occurred), then completed the test. This is disposable boot readiness, not a changed
product timeout. API35 runner hash is recorded separately in the receipt.

Correction to the21:40 capsule wording: the canonical snapshot capsule also contains
the existing bounded maintenance dispatcher. The dedicated fixture SSH route now
explicitly rejects write/extra-field/duplicate-field/boolean-schema requests **before**
loading its disposable configuration; it passes only the canonical read-only request
to the frozen entrypoint. Old positive traces contained read-only calls but did not
qualify that negative route guard. Capsule bytes stay b6e15add…; the hardened adapter
hash is4089c58c386634aabc21dacfdba8c0a7e219235fe39bc5029de42c9e408ed929.

Follow-up validation: `directory-readonly-guard.log`5 PASS/0 SKIP/13.76s (four rejects
and normal real publisher/traffic), plus GPU runner/receipt projection selection16
PASS/1.26s. The latter includes13 existing/new boot guards and three sanitized readiness
metadata projections. Secondary gateway envelopes are now unwrapped for future receipt
metadata; completed runtime receipts retain their original format. Do not add these
overlapping selections to the earlier totals or call them full CI.

| Gate | Status | Exact current scope |
|---|---|---|
|G1|PASS|Retained frozen isolated-core revoke/approval/restart evidence; final full-path repetition pending.|
|G2|NOT_RUN, full gate|Process/RPC subsets PASS; actual successor expiry remains running, not accepted.|
|G3|NOT_RUN, full gate|API27/API35 positive partial-publication paths PASS. Closed/replaced owner, new Connect during partial publication, legacy peer and too-late delivery remain unqualified.|
|G4|NOT_RUN, full gate|fd7562c full-core wall-clock run remains active; first renewal due23:11:57UTC. Older d968ddd first renewal is separate evidence.|

All Android AVDs and the corresponding disposable Android server/route helpers have
stopped. Only the previously bounded non-Android long core/expiry checks remain active.
Next: actual late HTTP completion across Disconnect/owner replacement in G3, retaining
the real G2/G4 runs. No independently accepted A checkpoint exists; split tunneling UI,
storage, routing and recovery are NOT_STARTED. No release package is approved from this
combination. Production/phone/APK118/updater113, rollout/rollback, catalogs, payments and
cohort are unchanged. Later exact-release, approved delivery, Telemost/systemd, both-NL
live renewal, paired-DNS/WebSocket and weak-network/screen-off/mobile-field gates remain.

## API27 real successor after partial publication21:40UTC

Newly proven relative to a30966c: a normal Android ConnectionService VPN obtains its
successor through verified HTTP and encrypted cache, survives an actual partially
published durable COMMIT and real cooldown, and commits renewed credentials in its
existing native session/owner. This is API27 isolated-core evidence, not complete G3.

Private evidence: `android-partial-gpu27-1/server.json`,
`android-partial-gpu27-emulators/{inputs.json,api27-receipt.json,api27-runtime.log}`.
The650s instrumentation run finishes `OK (1 test)` and `PASS_POSITIVE_PATH_ONLY`;
`SERVICE_SUCCESSOR_COMMITTED_SAME_OWNER` follows `REAL_COOLDOWN_PARTIAL_RELEASED`,
then `SERVICE_OWNER_CLEANED`. Both installed native checks match d1025a1d….
The successor borrow checks the native owner's profile fingerprint: `AcquireChat`
refuses a different fingerprint until the actual renewal commit callback updates it.
The original borrowed session continues carrying verified echo bytes throughout.

| Component | Exact identity |
|---|---|
|Online source/archive|fd7562cc466606002aa2af064b2b67ee165056c2 / 846818adefa292939034b9c427d658cfd3c427f48d1fb522dbda104f31aeb94f|
|Separate local-provider driver|180f386f8afba4d9a604e3f3b812370dcc7f5e0c9d855775f9d3c379daf91376|
|Read-only snapshot capsule, same fd source|b6e15addc5eb2ab864208957cf2b5908c8075f37b96c62b37dfa46798479b78b|
|API27 test-only APK|8270ef5811dd5e3fae30d059629b319df69531e17eed464bd5f5e9d8b0aed8be|
|API27 instrumentation APK|0199e70dc4967cda417b3c72467d3a8e4199baf9ef684cbfb52e91e3e3a2f3f3|
|Android native39c69de|d1025a1ddbebc4169872fdbc194317d86a21164b8b19767b0a62aa65c08129af|

The partial stand originally lacked RU publication of the actual SeedManager directory;
its initial fixtures were not live endpoints. `scheduled_evaluate.py --directory-only`
now publishes both real directories through forced-command SSH snapshots, preserving
gateway PIDs/profiles and authority. The additional snapshot capsule is reproducible
(second build byte-identical), unbound and read-only. Its separate fixture route binds
`profile_snapshot.main` to each disposable configuration path; custody checks remain
enabled, no signer/writer/timer is added, and this test adapter is not shipped. Packaged
controller/node/API/HTTP still execute only frozen archive code through normal entrypoints.
No manual directory/profile/journal repair is performed.

`directory-drop-before-trusted.log`:2 PASS/0 SKIP/46.59s for the new publisher/traffic
test and NL2 pre-publication RPC loss followed by the same COMMIT. The first fault test
incorrectly expected a partially populated controller receipt map; parallel publication
records that map only after both replies. Correct evidence is the actual changed NL
profile, unchanged NL2 profile and unchanged durable decision on resume. Two preliminary
test invocations failed Git clone trust setup before tests; they are not PASS.
No totals are added to overlapping earlier suites. Retain earlier fd67 root/package,
native race count3/artifact-bootstrap and421 JVM results with their original scope.

| Gate | Full-gate status | Current evidence / missing runtime |
|---|---|---|
|G1|PASS, isolated core scope only|Earlier frozen revoke/approval/restart receipts retained; final integrated repetition still running in G4.|
|G2|NOT_RUN, complete gate|Existing process/RPC cases plus new pre-publication loss PASS; genuine successor expiry still running on d968ddd.|
|G3|NOT_RUN, complete gate|API27 positive partial-publication path PASS; API35 running sequentially. Actual late delivery, stale/closed owner, legacy peer and remaining negatives stay open.|
|G4|NOT_RUN, complete gate|fd7562c eight-hour path still awaiting first renewal23:11:57UTC; d968ddd older soak has its first renewal and remains separate evidence.|

NVIDIA rendering is verified inside the guest; only one AVD runs, additionally capped
to one host CPU in its no-egress container. Finished/interrupted Android stands are
cleaned up, not left as idle duplicate jobs. The selected next step remains completion
of these gates. No accepted A checkpoint, B implementation, production installation,
Telemost-media/systemd/physical-field acceptance or release publication is claimed.

## Thermal interruption and hardware-GPU correction21:14UTC

The owner's overheating report interrupts the remaining engine-only API27/API35,
service API27 and isolated service API35 AVDs. They are stopped and cannot demonstrate
successor delivery. Preserve their earlier service/preflight evidence, not G3 PASS.
The two partial-working1 AVDs exited with failures before that explicit stop
(container exit1 at21:10:10UTC): API27 native-session assertion and API35
BOOTSTRAP_UNAVAILABLE. These are failures, not successful or operator-interrupted tests.

`tests/android_core_emulators.py` now requires an explicit single API, a shared
`android-emulator.lock` under the common evidence directory, NVIDIA PRIME offload,
`-gpu host` and `-accel on`. Actual guest SurfaceFlinger GLES must identify NVIDIA
without SwiftShader/llvmpipe/lavapipe/software rendering before installing/running
qualification. Missing hardware rendering fails closed and cleans up. Container runs
must share this lock and have real GPU access; isolation must not be weakened for GPU.
Guest OS/native CPU work still exists. This is not a promise of CPU-free emulation.
The owner-laptop constraint is also retained in AGENTS.md.

Actual API27 hardware probe: private `android-service-gpu-api27-1/api27-renderer.txt`
and `api27-receipt.json` record
`Google (NVIDIA Corporation), Android Emulator OpenGL ES Translator (NVIDIA GeForce GTX 1650 Ti/PCIe/SSE2)`.
APK38e3522f… and native d1025a1d… match before/after. The subsequent service test fails
at `FriendsAccessAndroid.proof/activate` with `Denied`, before native connection;
do not turn renderer success into G3 PASS. The emulator exited through normal cleanup.
API35 container hardware rendering remains NOT_RUN. No AVD is left running.

`python3 -m pytest -q tests/test_android_core_emulators.py`:11 PASS (hardware renderer,
software/missing renderer rejection, exclusive lock and release after failure).
The initial `python` alias was unavailable; the explicit python3 invocation ran tests.
No full-CI, release/package change or accepted A/B checkpoint. Non-Android wall-clock
stands retain their original source/artifact identity and remain independent evidence.
No production, owner phone, public APK/catalog or paid operation occurred.

## Actual Android service preflight21:00UTC — qualification continues

Two API-specific preflights now pass: HTTP readiness, validation, encrypted vault,
normal ConnectionService/MESH owner, borrowed authenticated native session and verified
HTTPS through its VPN. API27 evidence: `android-service-fd7562c-try2-emulators/api27-runtime.log`;
API35: `android-service-fd7562c-isolated35-2-emulators/api35-runtime.log`. Both show
SERVICE_OWNER_CONNECTED and SERVICE_VERIFIED_HTTPS and wait for the real22:55:56UTC
server successor. Neither currently proves successor delivery or complete G3.

API27 main APK SHA256`38e3522f1c9fbbb1114629db4d697714c3ce49b9bfbeb0d520b6aa5a2325ec49`;
API35 main APK SHA256`5a12878b7206d6cadf672c5c8490eb10626f4cbf195c781a7b3d1e0c0d479f98`;
instrumentation APK SHA256`3744880dcf01165fe0783791a19cdb7c8ea08de55faed22f06fa044ce9e253c6`.
Both use exact native39c69de SHA256d1025a1d…; installed APK and extracted ELF digests
are checked before and after execution. The earlier API27 cold-boot probe reproduces
bad ELF magic; reinstall/sync then real HTTP probe validates both gateways. Those failed
attempts are retained, not counted as successful application validation.

Host API35 Wi-Fi attempts returned a different TLS trust path, despite the emulator
HTTP-proxy argument; they do not prove isolated routing and are excluded. The successful
API35 runtime instead shares only the disposable server's no-egress network namespace:
no default route, synthetic185.251.89.19 routed exclusively to the private origin peer,
verified host-side synthetic TLS preflight before boot, and namespace-local adb/reverse.
This makes accidental external routing impossible, without changing host routing.
The early container mount-path typo failed before AVD creation and is retained separately.

`android_core.init.gradle` generates a domain-scoped synthetic CA/manifest only beneath
the explicitly selected private qualification build directory. Release tasks reject
this init script. Production sources/trust/Telemost, hostname verification, keys and
normal output APKs are untouched; no trust-all or security-clock replacement is used.
The owner/native positive path is real runtime, not a300s scheduling model.

Full-core harness source checkpoint`e144e8184155f86519259fd9403a0ec675c959e5` was pushed
and remote-verified. It now runs against immutablefd7562c archive/driver in a separate
internal network; first due23:11:57UTC. Actual lease traces correlate with original
session IDs and already show applied renewals of short leases; credential renewal and
crypto crossing are still pending. `full-core-fd7562c-e144e81/full-core/progress.json`
is running evidence, not G4 PASS. Older d968ddd long/expiry jobs remain separate.

Frozenfd7562c native bootstrap/wholedevice/qualification/bootstrap-broker `-race`, count3,
PASS with zero skips (`fd7562c-*-race-configured.log`), including real ProductStore
fixtures and frozen-source sync artifact publication. A wrong artifact path failed the
first bootstrap invocation; it was not waived. The configured full package/core/RPC
selection is running; its earlier missing opt-in invocation was aborted and is not PASS.
No full-CI, release, production, systemd, Telemost-media or physical-device claim.

## Routed preflight and full-core harness20:43UTC

Frozen sourcefd7562cc466606002aa2af064b2b67ee165056c2:
archive`online-fd7562c.tar.gz` SHA256
`846818adefa292939034b9c427d658cfd3c427f48d1fb522dbda104f31aeb94f`;
separate local-provider driver SHA256
`180f386f8afba4d9a604e3f3b812370dcc7f5e0c9d855775f9d3c379daf91376`.
Normal driver client entrypoints now pass21 samples on each NL with original mux stream,
462 echo bytes, DNS and verified HTTPS to the public-IP fixture address. Evidence under
`state-client-build/mesh-core-runtime-20261105/`: `public-fd7562c-{1,2}.log`,
`public-fd7562c-inspect.json` (ONLINE_CAPABILITIES_READY, mutations0), and
`android-routed-{gateway,origin}.json`. The origin is in a separate namespace on a labelled
internal network with no egress; no host/production public-IP route is changed.

`tests/test_mesh_core_acceptance.py` extends the existing harness, not runtime business
logic: bounded eight-hour two-renewal run, actual old leaf/CRL and original lease crossing,
same process/session/socket/bytes, then real revoke/linked emergency/lost-start/replay
and fresh public-IP HTTPS. Run explicitly with FC_CORE_ACCEPTANCE=1 and an immutable
FC_TEST_ONLINE_PACKAGE; its skip/default does not count as acceptance. The test-source
checkpoint and frozen runtime source are recorded separately. This full run is NOT_RUN
at this checkpoint. API27/API35 actual service qualification is still incomplete.

|Gate|Current result and remaining scope|
|---|---|
|G1|PASS earlier frozen isolated revoke/approval/restart scope; repeat in final full path pending|
|G2|Partial process/RPC PASS retained; real successor-expiry run and final reconciliation pending|
|G3|NOT COMPLETE: actual service HTTP/cache/native successor path and negatives remain|
|G4|NOT_RUN full fd7562c path; short routed preflight PASS is not long-runtime acceptance|

Older d968ddd long/expiry jobs continue without relabelling. Local-provider/core evidence
does not prove Telemost media/signaling, exact production binary or systemd. No release,
production, owner-phone or B changes; source checkpoint only.

## Actual service-path diagnostics20:24UTC

The earlier direct-engine runtime is not sufficient evidence of normal active-VPN HTTP
routing. `OnlineReadinessRuntimeTest` now has an explicit `fc_core_service=true` branch:
actual ConnectionService connect/disconnect, its existing AutomaticConnection owner,
borrowed native mux echo, verified HTTPS through the VPN, and real successor delivery.
API35 reaches SERVICE_OWNER_CONNECTED; active HTTPS readiness fails. API27 trial4
reproduces a TLS connection reset after actual service connection, before the long wait.
Evidence: `android-service-emulators-1/api35-running-diagnostic.json` (HTTPS_VPN failure),
`android-service-emulators-4/api27-runtime.log` (SSLHandshakeException/reset), with installed
native SHA256d1025a1d… verified. This is a newly exposed fixture boundary, not G3 PASS.

The separate qualification driver supplies test Services but omitted AllowInternet;
the normal PacketGateway therefore correctly selected ServicesOnly. The real production
entrypoint has no such service map and is not affected by that fixture error. A same-netns
public-address loopback alias also cannot pass the existing local-address deny policy.
Do not change those policy checks or test the VPN path solely through reserved chat services.
The driver now explicitly retains ordinary forwarding and emits the existing sanitized
sessiontrace/lease events. Production entrypoint, shared gateway runtime, signer, writer,
timers, security clocks and TTLs are unchanged. Its new bytes require a new immutable
package/driver qualification; the running d968ddd soak is not renamed as that acceptance.

`tests/android_core_route.py` provides only TCP plumbing for an internal Docker network:
gateway and origin have separate namespaces; the origin owns the synthetic API IP, while
only the gateway namespace gets a specific route via the private peer. No public-address
route is installed on the host. Both roles refuse a default route; the host bridge
adapter accepts only network-none or a labelled Internal Docker network. The real frozen
API/HTTP process still generates all replies, TLS remains verified against its synthetic
CA, and gateway destination policy stays intact. This topology is pending preflight.

Two earlier API27 attempts were not application validation failures: the exact installed
APK contained the expected ELF, but PackageManager's extracted30788048-byte native file
was entirely zero. Expectedd1025a1d… versus installed
`229e15c2844bb20487e335c11bc93b0dc62a6a67acf7b4f4314f19554481587e`;
`android-service-emulators-2/api27-probe.log` records bad ELF magic. Raw local APK/native
copies and sanitized diagnostics are retained there, not in Git. The runner now uses
non-streaming installs and verifies both installed APK and extracted native digests before
the runtime, and rechecks native bytes at cleanup. Trial3 verified native bytes but had
no available Wi-Fi underlay; trial4 uses stable emulated cellular only, not a physical
mobile/allowlist gate. No production trust or application validation bypass was added.

The incomplete source checkpoint includes this diagnostic harness, not accepted A.
Existing G1 isolated-core receipts and original8c/d968ddd evidence remain retained with
their own artifact identities. Next: early public-address HTTPS/service preflight, then
complete G3 scenarios and the changed full G4 combination before considering B.

## Android HTTP runtime checkpoint19:39UTC

Additional G2 runtime started19:46UTC: `FC_CORE_EXPIRY=1` enables
`tests/test_mesh_core_expiry.py` against immutable `online-d968ddd.tar.gz` and its driver.
The real controller is killed after ONLINE_COMMIT_DECIDED; the retained plan is hashed,
not modified. The test waits until the actual candidate leaf/CRL bounds pass
(23:46:04UTC), then runs two ordinary `resume` attempts and requires stable explicit
blocking/emergency with the same COMMIT/plan, no expired rollback. Progress is retained
at `expiry-d968ddd-long/successor-expiry/progress.json`; not a PASS until completion.
This harness's source is later than the d968ddd runtime and is labelled separately.

Not an acceptance result. New `tests/android_core_stand.py` starts frozen d968ddd
controller/node/API/HTTP and the matching separate gateway driver in a network-none
container. Actual custody rejected the first fixture attempts: directory0700 rather
than0750 under umask077, then an executable beneath a user-owned mount. The fixture
now explicitly creates the existing required directory mode and copies the identical
driver bytes into a root-owned runtime directory. Reader custody was not relaxed.
Both failures remain in `android-server-working{,-2}.log`.

`tests/android_core_bridge.py` exposes only loopback bridges to that container. The
emulator HTTPS proxy permits only the application's existing API CONNECT destination
and routes it to the local synthetic TLS origin, never the public destination. An
instrumentation-only P256 test CA and offline public-anchor asset overlay are used;
stock hostname verification is retained. Production trust, URLs, APK118/updater113,
build variants and native Telemost defaults are unchanged. No test provider is releasable.

The separately directed Gradle build uses `tests/android_core.init.gradle`,
`fcFriendsCi=true`, `fcTargetAbi=x86_64`, `fcTestBuildType=friends`, absolute `fcCoreWork`
and `fcCoreNative` paths, and tasks `:app:assembleFriends :app:assembleFriendsAndroidTest`.
It does not overwrite normal build outputs. The initial private-method compile error
is retained in `android-working-apk/build-private-call-failure.log`; corrected build2
passes using ordinary `FriendsRestricted.ready`/`renewal`. APK digests:

- local friends APK: `801ad1f63a1b62a54f675abaf360a3ec090877d198ba8d5a5da43d8907dab4ca`;
- instrumentation APK: `c6710ab5c1774b6471744ffe57286cf76b29ca67f455aba4acd21584256182fa`;
- native input: committed39c69de, SHA256 `d1025a1ddbebc4169872fdbc194317d86a21164b8b19767b0a62aa65c08129af`.

`tests/android_core_emulators.py` launches owned fresh API27/API35 AVDs, checks their
identity, installs only these APKs, binds the protected loopback relay with serial-scoped
ADB and executes `OnlineReadinessRuntimeTest`. It waits for the actual server renewal
and always stops only its owned emulator. At19:39UTC both receipts report RUNNING and
OWNER_CONNECTED after real HTTP validation, AndroidKeyStore encrypted cache, existing
AutomaticVpnOwner/RestrictedTunnelEngine and borrowed native mux echo. Successor delivery
is not yet observed. Logs/receipts are in `android-working-emulators-1/`; private synthetic
invitations and APK test inputs remain ignored local state. This test does not replace
partial-NL, stale-owner, late delivery, old-peer or full G4 acceptance.

Additional frozen d968ddd regression completed: `test_online_runtime_package.py`,
`test_mesh_core_runtime.py`, `test_mesh_core_faults.py`, `test_restricted_release_payload.py`:
67 PASS/0 SKIP,969.70s. `frozen-d968ddd-integration.log` SHA256
`1a7ec9fd308f63a83c84a33f404847682d3cef7a73295182f7e8e97b7bb8fea6`.
This repeats G1 and12 process cases on the exact current package; do not sum it with
the overlapping5043d72 selection or call it full CI. Long core evidence is still running.

| Gate | Current result | Still required runtime |
|---|---|---|
| G1 | PASS, isolated core only | Retain exact frozen receipts; no Telemost/systemd claim. |
| G2 | NOT_RUN, complete gate | Actual successor-expiry continuation and remaining matrix reconciliation;12 process cases pass. |
| G3 | NOT_RUN, complete gate | Running API27/API35 actual successor plus HTTP/owner negative scenarios. |
| G4 | NOT_RUN | Running two-renewal wall-clock path, lease-bound evidence and integrated emergency/Android scope. |

No accepted A checkpoint exists yet. No B/UI/storage/routing/recovery acceptance exists.
The only next task remains completion of these same G1–G4 gates before independent A
checkpoint and bounded Android app-VPN work. No delivery, rollback or production operation
has occurred; rollback of this test setup is owned-AVD/container cleanup only.

## Frozen5043d72 process qualification

The full selected run imports test sources from a detached5043d72 clone and starts
controller/node/API/HTTP from its immutable archive. Real gateway ownership, SSH RPC,
supervisor stop/start/wait, revoked Family admission and survivor TCP/DNS/verified HTTPS
are exercised again. `frozen-5043d72.log`:347 PASS/1 optional SKIP,1059.78s. Selection:
`test_online_emergency`, `test_online_renewal`, `test_online_diagnostics`,
`test_activated_maintenance`, `test_multi_gateway_renewal`, `test_package_credential_renewal`,
`test_online_runtime_package`, `test_mesh_core_runtime`, `test_mesh_core_faults`,
`test_friends_access`, `test_friends_restricted` (all under `tests/`). The missing optional
native compatibility environment was supplied in a separate detached5043d72 run:
`test_operational_authority_two_existing_identities_native_compatibility`1 PASS1.57s.
Do not add overlapping historical suites or call this full CI.

| Gate | Status | Exact exercised scope / remaining boundary |
|---|---|---|
| G1 | PASS | Isolated core revoke after COMMIT and approval, real restart, denied revoked credentials and new survivor HTTP/TLS/DNS/HTTPS; `frozen-5043d72/revoke/recovery.json`. Not Telemost/systemd/production acceptance. |
| G2 | NOT_RUN (complete gate) | Eleven real process/race cases PASS, including four emergency durable boundaries, dead/stale receipts, actual gateway death, unreachable NL, publisher contention, old-fence requester and corrupt confirmation. Real successor-expiry continuation and any unexercised full matrix boundaries remain open. |
| G3 | NOT_RUN | The new shared Android connector/build prerequisite is tested, not the Android HTTP/cache/owner/native path. |
| G4 | NOT_RUN | No completed current-combination two-renewal wall-clock plus emergency/Android acceptance. The new long harness is not a result. |

Artifacts, all local under `state-client-build/mesh-core-runtime-20261105/`:

| Identity | Exact value |
|---|---|
| Source | `5043d72c5b1db260d3200b9fab70a3f3bf1fa00c` |
| online-5043d72.tar.gz | `bd9a35b8a065f07dbfa725d986a46031e339ea92a246f536f2cff1bdc5b73129` |
| Manifest | `e0cd39aedab5ed9f12361ff18189446dd6b5e3c4c23f841b4a6595f85a9289c5` |
| Renewal source inventory | `dba5a18f6409cd1ab10e9a373caccb9cec10cad1dc0647e2e433794bc9af4071` |
| API / HTTP | `b2111a104412c5aad206b7acaca7854f51f9c99d9ad6608a63fd07644d24859f` / `6a4a8b36a68066204e41b86379c7f79f52e4765752304b51213bc627629a21bc` |
| Production gateway | `382dcf26298bad8ccbfc2ca5664e297215b2ab1d7a1338f594536285651f1e7d` |
| Separate packet driver | `dc104ed6c40c154f8b152ea673be0d7409eb5970af9a8eebd17f0c4a5a09518a` |
| Main test log | `f77982442bac47e7c82b2daad8cad26ecea1a0411b8f4a355ac4efcf0b0a6aa9` |
| Native compatibility log | `43557565734a08c43e5a3973973179f5bf3692ffb6987e822d48d508730995f8` |
| G1 recovery receipt | `c84d15916e175a7501584f6279fcd1cf94ee4250045f0e7ee061dc2a144048ba` |

Additional new test on that frozen runtime: actual wall clock crosses synthetic predecessor
leaf/CRL bounds. First ONLINE_WINDOW_INSUFFICIENT, then two ONLINE_RUNTIME_RECEIPT refusals;
no journal, owner or profile write. `expiry-5043d72.log`:1 PASS/11 deselected,61.15s;
receipt `expiry-5043d72/wall-clock-predecessor-expiry/receipt.json`, SHA256
`563c47832cba7c18a0b3d6333d9c9c53ef3ebb6d6abeeb73c9b35a0cbf47d06b`.
The test was added after5043d72; do not describe its test source as part of that archive.
Two retained failed assertion logs document correction of the expected CLI exit code and
the actual earlier capability-receipt expiry boundary, not runtime bypasses.

### Current long-runtime harness

`FC_CORE_SOAK=1` explicitly enables `tests/test_mesh_core_soak.py` with a frozen archive.
The gateway lifetime is7h, existing seed lifetime4h/overlap rotation1h, ordinary leaf/CRL
validity4h and renewal due window90min. No production TTL, timer or security clock changes.
After setup, original clients run24000s; two further normal CLI operations run only when
actually due (approximately2.5h and5h). The test retains original process/instance,
TLS/mux stream IDs, bytes and generations, then crosses the first successor's old leaf/CRL
bound (approximately6.5h). Early provider/traffic failure is checked while waiting.
This is the core continuity part of G4, not its complete emergency/Android/live scope;
no PASS is implied before its result exists. Source changes after it require explicit
artifact reconciliation, not renaming old evidence.

The frozen run is now started from `d968ddd55935ef7b37340262e3ea2729afdf7cd2`:
archive `online-d968ddd.tar.gz` SHA256
`849232db0d36252afceab0feabc7550700079569b333602d2c535dbc8d376350`, manifest
`d1540f8878197dcc7717b8c5964474e59a6ab0679c9860624599ed5518651f86`, separate driver
`caeccf70210221cf371ff54a0e775d2ad05e9cab2d4dfa8ed0f176af675684d1`.
Production gateway bytes remain382dcf26298bad8ccbfc2ca5664e297215b2ab1d7a1338f594536285651f1e7d;
the driver digest is not that gateway digest. Container `fc-mesh-soak-d968ddd` is isolated
with `--network none`; its frozen test source lives in `/run/frozen-source`.
`frozen-d968ddd-long/soak/progress.json` and `frozen-d968ddd-long.log` retain progress.
At19:06UTC: WAITING_FOR_RENEWAL_1, zero renewals, first due2026-11-05T21:28:53Z;
each original stream had431 successful samples and9482 echo bytes received. This is
only a running observation, not either renewal, crossing or G4 PASS. Expected duration
is about6h40m, extending into6 November; emergency, explicit lease-bound evidence and
Android full-path results must still be joined for complete G4.

Affected frozen-source native `-race -count=3`: bootstrap, wholedevice,
internal/qualification and cmd/bootstrap-broker PASS with zero skips. The bootstrap
run has actual ProductStore fixtures and the frozen `restricted-sync.pyz` Python
publication gate enabled (`FC_TEST_PYTHON`, `FC_TEST_SYNC_ARTIFACT`). Logs:
`d968ddd-{bootstrap,wholedevice,qualification,bootstrap-broker}-race.log`.
An earlier invocation used the wrong working directory for the timestamp-vector test;
its failure is retained in `d968ddd-bootstrap-wrong-cwd.log`, then the complete bootstrap
selection was repeated from `carrier/bootstrap`. No test assertion/gate was removed.
The two short duration/rotation preflights passed (`soak-preflight-working.log`,2 PASS,
88.28s), but do not qualify the long run. A separate frozen d968ddd package/core/release-
rejection regression is running in `fc-mesh-integration-d968ddd`; its result is not yet
claimed by this checkpoint.

## Android shared-runtime transport preparation

Continuation from5043d72; no Android version/production trust change. `wholedevice`
keeps one bootstrap admission/Family TLS/broker bind/mux/SessionMaintenance implementation.
Its explicit `PacketTransport` seam changes only seed/dedicated packet connection.
`OpenProvisioned` and ordinary Android builds retain the existing Telemost route.
The separate `fc_local_core` build connects to127.0.0.1:19091 through the supplied
`underlay.Network.DialContext`; it does not bypass Android protect/bind. There is no
production runtime flag, directory setter, synthetic READY or alternative writer.
Only the build-tagged `qualificationtransport` bridge imports the local provider.

`build.py --local-core-qualification` emits x86_64/provider=isolated-local-core,
diagnostic_only=true and the exact tag; it is mutually exclusive with owner diagnostics.
Normal builds clear inherited GOFLAGS and keep arm64/Telemost. Existing release payload
verification rejects each local-core marker independently:13 PASS, `android-core-release-rejection.log`.
No release gate was disabled and no existing generated Android payload was replaced.

Working-source checks under `state-client-build/mesh-core-runtime-20261105/`:
- `android-transport-race-1.log`: wholedevice and qualification `go test -race` PASS;
  fixture-dependent test was subsequently executed explicitly, not counted as accepted here.
- `wholedevice-transport-runtime-2.log`: all3 tests PASS with disposable ProductStore
  profiles and real SeedManager/Family/broker/mux/echo/cleanup, plus rejected protect.
  The first log retains a qualification-adapter typed-nil interface panic on denied dial;
  Seed/Gateway adapters now return a genuinely nil interface on connection failure.
- `android-packet-working.log`: existing native packet `-race -count=3` PASS.
- Both default Telemost and `fc_local_core` Android27 x86_64 JNI shared objects compile;
  `android-default-deps.txt` contains neither qualificationtransport nor internal/qualification.
  These are working-source build probes, not frozen Android acceptance artifacts.

Committed build39c69de21f87ea4ca83a3e7eac1d0b7d42a62fdb was subsequently built with the
documented builder into `android-core-39c69de/`, without replacing generated release files:
x86_64 JNI SHA256 `d1025a1ddbebc4169872fdbc194317d86a21164b8b19767b0a62aa65c08129af`;
metadata SHA256 `a557ea564334f705d0ceff57856b4e5cfafb166be7c6ccb51a6f9b901f7e2760`.
It is explicitly isolated-local-core/diagnostic, not a production gateway digest or APK.

**G3 remains NOT_RUN:** no emulator HTTP→validation→encrypted cache→connection owner→
active native renewal has been executed by these tests. The local connector seam is only
the missing client-side transport prerequisite. G4/current-package two-renewal wall-clock
acceptance and remaining G2 cases remain open. B remains NOT_STARTED. Nothing installed,
published, changed in production, or tested on the owner's phone.

## G2 process handoff and stale receipt continuation

Entry79421ec1cbd3fd9c457a65ddde7e8fbbde74eb8a; G1 frozen9369e65 evidence below remains
valid for its scope. Added actual controller SIGKILL at EMERGENCY_HANDOFF,
EMERGENCY_AUTHORIZED, EMERGENCY_COMMIT_DECIDED and CLEANING; replay preserves the same
COMMIT and does not start gateways again. An unreachable NL before journal/after COMMIT
blocks without changing the decision, then resumes when the SSH route is restored.
The real packaged directory publisher refuses the active maintenance owner without
mutations. A separate paused old-fence RPC requester resumes after a higher-fence owner
and receives ONLINE_STALE_WRITER. These are actual processes, not exception-only faults.
Earlier artifact9369e65: `g2-working-1.log`6 PASS231.04s, `g2-races-1.log`2 PASS40.72s;
different selections, not a full matrix or full-CI count.

**New failure reproduced, not hidden by those passes:** the fault adapter executes the
normal NL publish RPC, then SIGKILLs/restarts its actual gateway and returns the original
receipt. Frozen9369e65 reports COMMITTED/zero_stop despite receipt ownership belonging
to the dead process. `g2-stale-receipt-1.log`:1 FAIL17.44s, with replacement PID/instance
and original response retained in `g2-stale-receipt-9369e65/dead-process-receipt/receipt.json`.
The old TCP cannot survive this kill; this result blocks accepting the whole A package.

Source fix: a read-only `online/confirm` round checks fresh actual reader identity/profile
against the stored publication before RU delivery-ready. Capability/version matching
requires it. Changed process → ONLINE_EMERGENCY_REQUIRED; stopped gateway after COMMIT
also enters the existing approved continuation, without a manual preliminary start.
Current recovery reuses the original COMMIT, emergency machinery and custody boundaries.
Completion is now parallel across participants, with existing durable per-node cleanup
ledgers; lost replies replay without a second decision. Eight bounded rounds remain:
acquire, prepare, stage, decide, NL publish, NL confirm, RU publish, parallel complete.
Headroom is rechecked after read-only inspection before any journal/owner write.
SSH120,1395s+lateness, certificate/CRL/lease limits and wall clocks are unchanged.

`confirm-working-1.log`:93 PASS,8 deselected,136.50s (online/emergency unit selection and
real dead-process-receipt recovery); this overlaps earlier suites and is not frozen/full
acceptance. New tests also cover the confirmation crash/lost-reply boundaries, concurrent
completion and insufficient headroom consumed during read-only inspection. Final frozen
candidate results/provenance will be appended; no production/phone/publication operations.
`confirm-working-2.log` retains a harness failure: crash was incorrectly labelled ordinary
inactive by the disposable supervisor, so the intentionally unchanged quiesced resume
preserved that inactive service and returned NEW_DIRECTORY_NOT_READY. The supervisor now
derives failed state from an actual nonzero child exit absent an explicit stop request.
`confirm-working-3.log`: dead-gateway approval-only restart PASS48.95s, with exit-9, no
preliminary manual restart, new PID/instance, and both new DNS/HTTPS sessions. The earlier
corrupt-confirmation case passed separately. No systemd acceptance is inferred.

Still open: remaining expiry/full G2 matrix, actual API27/API35 HTTP/cache/owner/native G3,
and final two-renewal wall-clock G4. B remains NOT_STARTED. This is the same incident,
not a new roadmap stage and not an accepted A checkpoint.

## G1 revoke continuation

Continuation HEAD1e2823ec042bf4fe35b083c94cf58c8aa42bc8d3; source8eeb9f0 and its
90b02003… archive remain immutable. Foreign working changes are preserved separately.
New user scenario beyonda30966c: after a durable online COMMIT, explicit identity revoke
causes a safe emergency handoff. A second revoke invalidates the existing outage approval.
With newly bound synthetic approval, both real gateway processes restart; both revoked
identities fail Family TLS while the survivor obtains a new readiness-backed session
with TCP/DNS/verified HTTPS. Lost start response reconciles the saved intent, without a
second start or changed original COMMIT. This is local core, not Telemost or systemd.

The missing operator action is added to existing `restricted_admin`/Access and packaged
in the new API inventory. It only performs monotonic explicit device revocation in the
existing transaction; no new DB/HTTP authorization route, signer, timer, policy or
automatic CRL publication. The existing controller remains the publication writer.
Tests never edit DB/profile/marker to complete recovery. Predecessor probe credentials
are synthetic fixture material issued by the frozen API against real SeedManager output
with wall-clock validation. That setup is not Android HTTP/cache acceptance. Post-recovery
survivor delivery does use packaged HTTP readiness; revoked credentials are still unexpired.

Working command: `python -m pytest -q tests/test_friends_access.py
tests/test_mesh_core_runtime.py -k 'operator_revocation or signature_purpose or
revocation_after_commit' --basetemp=/run/revoke-tests` in root/network-none
`fc-online-runtime-tests:20261105`, explicit Go1.26.1 and isolated SSH. The fixture builds
the entire candidate from one temporary committed export; controller/node/API/HTTP
execute only its archive. `revoke-working-3.log`:3 PASS,14 deselected,85.48s.
Independent Access selection9 PASS/0 SKIP,0.44s (overlaps, do not add counts).
Logs/receipts remain ignored under `state-client-build/mesh-core-runtime-20261105/`.
`revoke-working-1/2.log` retain harness diagnostic failures: a generic client bootstrap
error is not a TLS rejection receipt, and the asynchronous server rejection must be
awaited. Assertions now check the actual serving process's `family_open` rejection,
absence of authenticated/broker admission, plus the preserved certificate's CRL serial.

| Gate | Current status | Exact scope / remaining boundary |
|---|---|---|
| G1 | PASS isolated core on frozen9369e65 | Both NL, real revoke/late revoke, absent/denied/expired/stale/fresh approval, original COMMIT/fence/floors, lost start, TLS denial and new survivor DNS/HTTPS. Not systemd/Telemost/production. |
| G2 | NOT_RUN full matrix; earlier partial PASS retained | Remaining handoff/owner/publisher races, expiry and unavailable/partially updated participant scenarios. |
| G3 | NOT_RUN | API27/API35 HTTP→encrypted cache→existing owner→active native session and required scenario matrix. No new Android artifact. |
| G4 | NOT_RUN | Two successive renewals through real old leaf/CRL/lease bounds on final combined artifacts; earlier999s and20s results are not replacements. |

This is an incomplete-A source checkpoint. B remains NOT_STARTED, with no B artifact or
routing acceptance. Continue the remaining A gates; no production, phone, publication
or paid action occurs. G1 acceptance does not imply acceptance of the complete A package.

### Frozen9369e65 G1 result

Source9369e65c916650d016b3b15acb534467163b9af1 pushed; remote main readback matched.
Separate artifact identities (local/ignored, no publication):

| Artifact | SHA256 |
|---|---|
| online-9369e65.tar.gz | 7065f8bfb64128bb7ff796f5f087605cfbf60c51d50458ae4a1cffab3ae07ee8 |
| source-manifest.json | a0fa60e947461ffc8a5ed5e58f2bc84cb8ff675ed5401540c5ddc5bfce53561a |
| renewal source inventory | 54c4671e778a161278e2ab8dc87c0aa0daa75807658256808b365b9d0d0a3330 |
| api.pyz | f46484d755658dc7c7cf3f853bfe227af4c58225a7d85e7b205522fb6975a5c4 |
| http.pyz | bbefdb3d93b716d14d514224395439664559ba478d36bf08aab75cea7c66f8e8 |
| packaged production gateway (unchanged) | 382dcf26298bad8ccbfc2ca5664e297215b2ab1d7a1338f594536285651f1e7d |
| separate non-production mesh-runtime-9369e65 | dc104ed6c40c154f8b152ea673be0d7409eb5970af9a8eebd17f0c4a5a09518a |

Same network-none image/toolchain as8eeb9f0. Build from committed export; checkout exact
9369e65 in `/run/frozen-source`, set `FC_TEST_ONLINE_PACKAGE=/out/online-9369e65.tar.gz`,
`FC_ONLINE_GO=/go/bin/go`, `FC_TEST_GO=/go/bin/go`, `FC_ONLINE_ISOLATED=1`,
`FC_ONLINE_SSH=1`, then `python -m pytest -q -p no:cacheprovider
tests/test_friends_access.py tests/test_friends_restricted.py tests/test_online_emergency.py
tests/test_online_runtime_package.py tests/test_mesh_core_runtime.py --basetemp=/run/frozen-tests`:
**138 PASS/0 SKIP,494.24s**, one selection, not full CI and not added to earlier overlapping
counts. Deterministic archive rebuild, packaged SSH negative/fault cases and both core
traffic/recovery scenarios run again. Go1.26.1 `go -C carrier test -race
./internal/qualification`:PASS; shared production native/runtime is unchanged from8eeb9f0.

Under `state-client-build/mesh-core-runtime-20261105/`:
- `frozen-9369e65.log`:70a1ef5e49af28bc3ffbca77eec2aa7cd499dc76823848355fa4cad15566be51.
- `frozen-9369e65/revoke/recovery.json`:96ea11420ded74cdf2e60618cc21431fbd83a0638b600310e9e1cb86f9cef7a1.
- `revoke-native-race.log`:8f227f00f7dcb3085a380001659acfde0d0c2db48c33b777ce141dfd3166c96f.
- Same receipt directory contains both gateway logs and survivor HTTP/TLS/mux/TCP/DNS/HTTPS
  logs; synthetic-only, not committed. Before:NL PID9648/NL2 PID9657. After:10490/10554,
  different process instances and exactly one emergency start each. CRL floor3 on both;
  both revoked identities had successful bootstrap admission on both before COMMIT and
  server-side Family rejection on both after recovery. Original COMMIT plan hash retained,
  fence1→2, archived start-intent hash preserved and replay leaves actual service state unchanged.

## Isolated core runtime continuation froma30966c

Entry HEAD exactlya30966c16980e73074215a4570066c8fd31361ed; no subsequent committed
delta. Existing dirty documents/historical patch/reports were preserved. The immutable
online8c876e3 archive/digest and previous999s/a8e1db9 evidence remain unchanged.
No production, owner-phone, release/publication, paid/cohort/admission/boot operations.

New demonstrated user path: both isolated NL create actual seeds and admit a synthetic
identity through Family TLS, dedicated broker/mux, original/new TCP, DNS and verified
HTTPS beyond15s. After a real gateway replacement following COMMIT, the packaged
controller detects the new runtime instance, quiesces actual processes, requires outage
approval, reconciles a lost start response using the saved intent, and permits new
Family sessions/traffic. Emergency deliberately closes old connections. This is not
the earlier observer-only15s fixture, and not a claim that an old TCP survived a kill.

The production command and isolated driver share `gatewayruntime`, `PacketGateway`
and the bootstrap connector boundary. Actual SeedManager creates/publishes endpoints;
no READY setter, hand-written usable directory, direct qualification constructor,
manual DB/profile/journal repair or second signer/controller is used. An initial
ordinary online COMMIT publishes the real NL directories to RU. The driver is built
from the package's frozen native inventory, separately hashed, and bound by exact
PID/UID/executable; the reader belongs to the traffic-serving gateway process.
Only external room/packet transport is substituted. Test provider/configuration are
not release payloads. Production rejects the test mode.

The new process stand found a real bug absent from the earlier modeled lost-RPC test:
`SystemdBarrier` reports an unsuccessful command response as `SERVICE_ACTION_FAILED`
(or timeout as `SERVICE_OUTCOME_UNKNOWN`), whereas emergency recovery treated that
as deterministic and fenced the already-started gateway. Its durable intent then
prevented another start (`START_ALREADY_ATTEMPTED`). Post-emergency-COMMIT service
outcome/readback uncertainty now preserves state for reconciliation. If the original
start did not take effect, recovery remains blocked and does not start twice.

| Gate | Full gate status | New isolated scope | Still missing |
|---|---|---|---|
| G1 | NOT_RUN (partial runtime evidence) | Real approved emergency stop/start/new TLS+DNS+HTTPS; absent/denied/expired approval, lost start reply and replay | Real revoke after COMMIT and after approval; revoked identity TLS denial |
| G2 | NOT_RUN (partial PASS) | Controller SIGKILL distinguished from gateway SIGKILL; replacement receipt, preserved COMMIT/fence, real start-intent reconciliation | Remaining handoff/owner/publisher races, expiry/unavailable-participant full matrix |
| G3 | NOT_RUN | Verified synthetic HTTP readiness supplies the core client | API27/API35 HTTP→encrypted cache→connection owner→active native delivery and full scenarios |
| G4 | NOT_RUN | Two-node traffic/preflight and emergency path on frozen package/shared driver | Two successive online renewals retaining original sessions through actual old leaf/CRL/lease bounds; final combination qualification |

The preflight is diagnostic, not the endpoint of this task: work continued into
gateway-kill/approval/start-response recovery and the resulting source fix. The
supervisor actually starts, stops and waits for children; it is not systemd acceptance.
Telemost signaling/media and exact production-gateway live traffic remain separate
unexecuted gates, not silently redefined as local-core PASS.

Time budgets are distinct: provider creation15s, default lease600s, seed≤4h,
SSH120 eligibility1395s+lateness. The isolated driver permits process≤8h using the
existing4h seed/3h overlap rotation, not longer certificate TTLs or frozen clocks.
Current issuer lifetimes mean the full two-renewal/boundary run is genuinely long;
the20s traffic sample is not substituted for it.

Working evidence is local/ignored under `state-client-build/mesh-core-runtime-20261105/`.
`preflight-4.log` first passed the positive traffic check; initial failures retained:
repository ownership setup, then unsupported test echo service alias (fixed to the
existing chat-mailbox mapping, with no destination-policy relaxation). `emergency-1.log`
reproduces the real start-response bug; later harness assertions were corrected to
account for normal intent archival and monotonically increased recovery fencing.
`native-race.log` records a fixture-location failure (no timestamp fixture mount);
`native-race-fixtures.log` uses correct source-relative fixtures and mandatory packaged
Python publication validation. Final frozen identities/results are recorded below when
available; these working runs are not full-CI or accepted-A claims.

Working validation: core entrypoint/traffic/recovery/binding selection8 PASS/0 SKIP
(`core-checks-2.log`,103.55s). Root/renewal/package selection254 PASS/1 FAIL
(`python-regression.log`,365.66s): COMMIT succeeded but its replay hit the old negative
proxy's intentional15s exit. Positive COMMIT/process/RPC tests now use `CoreStand`;
the original negative timeout test is preserved separately. This is a fixture boundary,
not permission to extend a production timeout or suppress the replay assertion.
The updated complete package module passes30/0 SKIP in253.00s
(`package-positive-matrix.log`), including six controller kills and six lost/corrupt
RPC replies on the real seeded runtime. This rechecks the failed replay, not a sum
of the previous overlapping selections.
Native bootstrap, production command, packet adapter and Family session `-race` pass.
Broker `-race` with fresh disposable Family fixtures passes; four DNS subcases also
pass in their explicit port53 selection (`broker-race-partitioned.log`). Counts overlap
and are not summed. The historical opt-in long-stand test is not charged as executed.
Earlier broker attempts retain two setup failures: missing Family fixture and a
port53 collision when a cross-session test creates two fixtures concurrently. The
final partition runs the full broker suite and then the mandatory DNS selection,
without changing assertions, security clocks or product DNS behavior.

Phase B: UI/storage/routing/recovery across AWG/TCP/MESH/Auto **NOT_STARTED**. No B
checkpoint or APK exists. A is not accepted, so there is no unqualified A+B release
combination. Current source rollback is selection of the previous source/package,
not installation or production rollback. Next: complete the remaining G1–G4 scenarios;
then independent accepted A, bounded B, exact release qualification, separately allowed
delivery, real two-NL renewal and field gates. Paired-DNS/WebSocket, weak network,
screen-off/mobile allowlists remain OPEN; the paid canary is not repeated.

### Frozen8eeb9f0 checkpoint (incomplete A)

Source8eeb9f0d4e92e439d0519a24317be8a8b4ac0078 was committed and pushed normally;
remote `refs/heads/main` matched exactly. The source/package checkpoint is independently
recoverable, **not the accepted A checkpoint required before B**. A fresh shared clone
checked out that exact source, with no checkout imports in the package. Deterministic
rebuild (including after dirtying the clone) and the combined selected root/renewal/
package/core module run pass **263/0 SKIP in486.54s**. This is one actual selection,
not addition of overlapping earlier runs, and not full CI.

| Artifact | SHA256 / identity |
|---|---|
| Source commit | 8eeb9f0d4e92e439d0519a24317be8a8b4ac0078 |
| `online-8eeb9f0.tar.gz` | 90b02003452724eee604e4372d581597f9dc40dde3670cebb43970d62ce53ffb |
| Manifest | 438d49ed114bcfab259e3a856f859ebcbaaaef3b2732c73920ef2193c4aa60f5 |
| Renewal inventory | 54c4671e778a161278e2ab8dc87c0aa0daa75807658256808b365b9d0d0a3330 |
| Native inventory (310 source files; canonical JSON hash) | eb9f2b36b7b50349925187dc584820329d008474be406b194bf570ac5a124792 |
| Packaged production gateway, Telemost path | 382dcf26298bad8ccbfc2ca5664e297215b2ab1d7a1338f594536285651f1e7d |
| Separate isolated packet driver, **not production gateway** | a49c4412efecd6215767390fc9f78cbda8347187823b9b4b11875efbd40af4b5 |
| Packaged API | b6c1fcfe62780bc874029617446a5e30dfc7d703fa30aca21a2a92c1829b6a13 |
| Packaged HTTP | 59f170af4ac8e781e58f1d952af1a8d40aa3752234d000d05950bf6ebba162c8 |

Toolchain: Go1.26.1/linux-amd64; existing locked Python3.13.15 image
`fc-online-runtime-tests:20261105` / `89598610ee266cf1efa164092d1193479069784f1c94493c46fcff82f5a6736f`.
Archive and driver remain local and uninstalled/unpublished. Previous online8c876e3
archive was rehashed and still equalsa27502d752eefe05306a189dce6a8630107d5980eca1477ffa9401a9283ffaea.
No accepted maintenance archive, APK118 or updater113 replacement.

Evidence root: `state-client-build/mesh-core-runtime-20261105/`:
- `frozen-8eeb9f0.log`:263 PASS; SHA25666c4a412fc4d9a09174fde040cc7902196a0a0a358eac3b6f7524cc85bcb893f.
- `frozen-8eeb9f0/preflight.json`: SHA25612004f70577258568b0571c190d2b4d13bb3e1c9b95d81bc0ff6075e737d2e9c.
  Both NL have21 traffic samples over20 real seconds, original stream/session retained,
  verified echo bytes22→462, plus new TCP/DNS/verified HTTPS. Seed and gateway existed
  before these samples and survive beyond15s. Cleanup waits for actual children and
  verifies both reader sockets absent.
- `frozen-8eeb9f0/gateway-restart-emergency.json`: SHA256f6e7987a4a5dc0d0664e9d15e083e30db4c8015e7450806d9b8f0102c72a0d22.
  Controller/gateway death, new process/reader, approval refusal, real lost start
  response, archived original intent, same-decision continuation and replay.
- `frozen-8eeb9f0/emergency-{NL,NL2}-{client,gateway}.log`: actual restarted gateway
  PIDs and four post-recovery traffic samples per NL, including verified HTTPS and
  normal client completion. These are new sessions, not surviving old TCP.

Reproduction uses the committed tests, `FC_TEST_ONLINE_PACKAGE=<that archive>`,
`FC_ONLINE_GO=/go/bin/go`, `FC_ONLINE_ISOLATED=1`, `FC_ONLINE_SSH=1`,
`FC_TEST_GO=/go/bin/go`, `FC_ACCEPTED_CARRIER_SOURCE=<frozen clone>/carrier`,
`FC_CORE_EVIDENCE=<private directory>`, network-none root container and
`--basetemp=/run/frozen-tests`. Selection: `test_online_emergency`, `test_online_renewal`,
`test_online_diagnostics`, `test_activated_maintenance`, `test_multi_gateway_renewal`,
`test_package_credential_renewal`, `test_online_runtime_package`, `test_mesh_core_runtime`.
No Android artifact/runtime check was executed in this checkpoint. The remaining G3
transition is specifically the real app HTTP/cache/connection-owner path into its
native session; the driver client is not that path. The remaining G4 transition is
two due renewals and actual old material-bound crossing, not merely a longer sleep
after the already demonstrated COMMIT. Full gate statuses above remain NOT_RUN.

## Online runtime package continuation

Entry HEAD409644142114d34f50e0543c4472274d72153d20 matches the requested verified
baseline. Source against emergency checkpointb1d17d3 is unchanged (only four documentation
files differ). The four pre-existing dirty documents and five untracked historical reports
plus restricted patch are preserved. No server/phone access, deployment, signing or publication.

Implemented a separate `MESH_ONLINE_RUNTIME_V1` builder and explicit online CLI, rather than
setting the qualification flag. The package closes over committed current API/HTTP sources,
renewal modules and a source-built native gateway; all have an inventory/digest. The accepted
maintenance archive/accepted API inputs are unchanged. Online requires exact opt-in, package
source/API, RU/NL/NL2 membership/capabilities and actual reader custody. Reader checks Unix
peer UID/PID against service MainPID and the executable digest as well as gateway/profile
receipt binding. Existing controller, RPC, signer, locks, fences, durable decisions, emergency
authorization and continuation are reused. SSH budget remains1395s+lateness.

New isolated package checks:6 PASS in10.78s (`reader-tests-second.log`), Go1.26.1 and existing
Python3.13.15 locked test image. Build determinism is checked twice after dirtying the test
checkout; isolated imports/HTTP/node/controller entrypoints, opt-out/membership negatives
and actual packaged gateway reader/PID checks run. This is A1 boundary evidence only:
the gateway's seed creation is held by a local nonresponding proxy with a synthetic unused
token in a network-none container, not Telemost/provider readiness or useful traffic.
Service status in this narrow test uses a disposable systemctl adapter reporting the actual
owned PID; no real systemd stop/start acceptance is claimed.

Initial failures retained: three test configs were not canonical JSON; the first native
reader launch lacked a provider token and stopped before observation. Corrections affect
only fixture setup. Initial containing Python selection82 PASS/3 FAIL is not all-green;
its80 online/emergency tests overlap prior evidence. The new6-check repeat is not full CI.
Raw evidence: ignored `state-client-build/mesh-online-package-20261105/`.

Initial six-check scope: G1 full emergency runtime NOT_RUN; G2 independent SSH/process faults
NOT_RUN (subsequently exercised in part below). G3 actual
Android HTTP/cache/native owner: NOT_RUN. G4 final two-renewal/cross-bound package traffic:
NOT_RUN. The original known parser blocker is implemented, not substituted for these gates.
The999s stand remains evidence for a8e1db9 only. APK118/updater113 and production unchanged;
rollback is source-only and old quiesced behavior remains available, not a live action.

One next step: complete packaged independent-process G1–G4 on frozen source. Then retain an
independent accepted A checkpoint before the separately scoped ANDROID-APP-VPN implementation.
No Phase B source or acceptance claim yet. Exact release artifacts, separately authorized
delivery, real both-NL renewal and remaining field gates still precede controlled paid beta.

See [online configuration/entrypoint contract](../../deploy/friends/restricted/maintenance/ONLINE_RUNTIME.md).

### Independent-process checkpoint — incomplete A, no B

Sourcec54e7b3d96a930ca713a2a9fa4353ea93e60e4d5 was pushed and remote/main verified.
Its separate immutable online archive (not an accepted release or maintenance replacement):

| Identity | SHA256 |
| --- | --- |
| `online-c54e7b3.tar.gz` | c7f26418348bf326a7589beb7c8dde64adb9a749fec8a38f25c5e97fab32416c |
| Manifest | e486157dead44e197d300e544480786ff06926d73d4b9a2991af84fb6d9cfd4b |
| Renewal source inventory | a9984a302e6b08608c8bc955732cd76c7778afa1228fe39772eb1a07cfb45eac |
| API | 817218bc19b308f1dc4f066291f3afcf795c91cf8527573a07ef3a066e1b118e |
| HTTP | 2067e591be267045e39d911c489c818afbc2274a0294079e072d88cfd953f64a |
| Gateway | 0e8d914cceba6712aba1e68b1dda53f98340ffe32215f02e7c142f9cb6ddf882 |

New source tests use separate controller, three handlers, actual HTTP and two gateway
observer processes, independent state, root-private canonical ProfileStore and ordinary
SSH RPC/host-key checking. No production configuration, internal qualification constructor,
manual DB/profile/marker repair, reduced SSH budget or security-clock substitution.
Fixture setup creates synthetic initial profiles with the native-required gateway DNS SAN.
The systemctl adapter reports owned PIDs only; it does not implement restart/stop acceptance.

| Gate | Full gate result | New evidence and exact remaining boundary |
| --- | --- | --- |
| G1 | NOT_RUN | Existing approval/handoff tests retained; actual restarted gateway/new valid Family TLS, revoked denial and post-recovery DNS/HTTPS not exercised by this package stand. |
| G2 | NOT_RUN (partial checks PASS) | Real controller SIGKILL at ONLINE_FENCING, ONLINE_PREPARED, ONLINE_COMMIT_DECIDED, ONLINE_NL2_DECIDED, ONLINE_NL2_PUBLISHED, ONLINE_CLEANING. RPC loss after RU prepare, NL stage, NL2 decide, NL publish, RU publish; wrong NL2 stage participant aborts predecision. Handoff/process-owner/publisher races, expired material and full distributed matrix remain. |
| G3 | NOT_RUN | No new Android artifact or disposable API27/API35 HTTP→encrypted-cache→owner→native session qualification. Previous JNI/storage evidence is not substituted. |
| G4 | NOT_RUN | COMMIT/replay/delivery-ready marker verified, but no two-renewal retained TLS/mux/TCP/bytes/lease/crypto-crossing run on the final package. The999s sourcea8e1db9 stand remains unchanged historical evidence. |

Containing scoped selection:110 PASS/0 SKIP (`scoped-serial.log`,264.46s). Earlier six
RPC cases passed alone (`rpc-faults.log`), but a containing concurrent-build run had108 PASS/
1 FAIL (`scoped-final.log`): retry returned ONLINE_RECOVERY_REQUIRED after a lost stage
reply. Its first-cause-only result concealed the current blocker; attribution to load or
the15s fixture lifetime is unproven. New `last_cause` retains the original incident cause
and independently reports a later retry failure. Missing/timed-out/malformed runtime-reader
responses now have bounded explicit causes rather than UNKNOWN. No assert/gate is disabled.
Additional package/document/participant tests5 PASS (`participant-configured.log`,31.08s):
reproducibility, missing opt-in, incompatible contract, real gateway SIGKILL and natural15s
seed timeout. Incompatible construction returns an unbound node rejection; SSH correctly
rejects its response schema, and direct packaged-node diagnostic confirms
ONLINE_OPT_IN_REQUIRED. The initial expectation of a bound rejection failed1/4 tests
(`participant-final.log`); the RPC trust/binding requirement was preserved, not weakened.

Broader root/profile/rollback/multi-gateway regression:373 PASS/1 optional SKIP
(`root-regression-configured.log`,132.52s), using the exactc54e7b3 archive for construction.
The skipped existing-identity native compatibility test separately1 PASS
(`authority-native-configured.log`); its source is frozen c54e7b3, byte-identical native to
the earlier accepted source. These counts overlap the110-test selection, not additive.
Initial root run356 PASS/17 FAIL/1 SKIP retained (`root-regression.log`): missing explicit
package environment and absent `/usr/bin/python3` for service DAC checks. Only the disposable
image/test invocation was repaired. No production code workaround for those fixture errors.

Fresh c54e7b3 native `-race` binaries and sync artifact
`2f54d9df3b4178b110ac0cfd734bef722740d4c6ba4f95fb7c77c53dd943367e`:
bootstrap + bootstrap command count3 PASS with zero skips (`bootstrap-c54e7b3-cwd.log`);
Family session + broker count1 PASS with7 optional process/DNS/long-stand skip events
(`native-c54e7b3.log`). Initial native invocation from the wrong working directory failed
the shared timestamp fixture (`bootstrap-c54e7b3.log`); corrected package cwd rerun passes.
These are exact-source checks, not full CI or G4. Final disposable Python/SSH image:
`sha256:89598610ee266cf1efa164092d1193479069784f1c94493c46fcff82f5a6736f`.

The unfinished boundary is concrete: the packaged production gateway creates its Telemost
seed at startup; the network-none synthetic proxy never supplies a seed. The observer is
real but exits at the unchanged production15s timeout. Current process tests fit that narrow
window. This is not a long-lived isolated packet path and cannot qualify G1/G3/G4 traffic.
No production token, extra provider dependency, altered timeout or security clock is used to
hide this limit. Complete the reusable long-lived native stand before accepting A; phase B
must not mask the gap. All raw archives/keys/state/logs remain ignored under
`state-client-build/mesh-online-package-20261105/`. No release or deployment action occurred.

### Frozen8c876e3 result — source/package checkpoint, not acceptance

Source`8c876e3f7865e71e3d40b9b1e80ce5be1e4cdcb3` committed/pushed; remote/main matched.
The final source archive includes its own entrypoint/configuration contract documentation.
`FC_TEST_ONLINE_PACKAGE` selected these exact immutable archive bytes for the containing
suite, not a rebuilt fixture capsule: **114 PASS, zero fail/skip,281.93s**
(`frozen-8c876e3-final.log`). The suite also rebuilds from that same committed revision
after dirtying a disposable clone and requires byte-for-byte identical archives.
Runtime binaries/sources never import the working checkout. This supersedes the earlier
110-check source-fixture result for this scope; do not add overlapping counts.

| Final candidate identity | SHA256 |
| --- | --- |
| `online-8c876e3.tar.gz` | a27502d752eefe05306a189dce6a8630107d5980eca1477ffa9401a9283ffaea |
| Manifest | f205636dd8215a6323acf8aa1b0bed589675682ba92f9b4314db704f8873d0b5 |
| Renewal source inventory | 391b5d06d120c1e547e5dae4d69bfccbaac2d9535bb8c4dcc9e039860a09b7de |
| API | cdbc1c3878b96b4eff37a02d03184fed85f32912f7ed109936fa8828aed87ef7 |
| HTTP | ba4601699f2410dbdca272f567c08ae2c0ee3e9fe556e91038462f595ee072b4 |
| Gateway | 0e8d914cceba6712aba1e68b1dda53f98340ffe32215f02e7c142f9cb6ddf882 |

Native, Android, control and identity source trees are unchanged fromc54e7b3; the fresh
native race/sync evidence above retains that exact provenance. No Android delivery tests
were rerun here and no new Android artifact exists. Frozen package setup first failed
twice with91 PASS/23 fixture setup ERROR (`frozen-8c876e3.log` and
`frozen-8c876e3-configured.log`): Git clone's upload-pack rejects the differently owned
readonly `/src/.git` and does not inherit the command-scoped safe-directory setting.
The corrected disposable-container invocation explicitly trusts only `/src/.git` in its
temporary global Git config, retaining the exact `/src` command-scoped allowance. No host
Git configuration, source guard or test assertion was relaxed. All failed logs are retained.

The final source/package is **not** an accepted A checkpoint: full G1/G2/G3/G4 statuses
and missing traffic/Android boundaries in the table remain unchanged. Phase B has no
source/package/artifact checkpoint: UI, storage, routing and recovery for AWG/TCP/MESH/Auto
are NOT_RUN/NOT_STARTED under this task, intentionally gated by A. No unqualified combination
is release-ready. APK118/updater113, accepted maintenance archive and previous999s evidence
are unchanged. Rollback remains source/candidate selection only, not a production action.
One next step is the long-lived isolated gateway/packet stand through packaged G1–G4;
then independent accepted A, bounded B, exact release artifacts and separately authorized
delivery/live/field gates. Paired-DNS/WebSocket, weak network, screen-off and mobile
allowlists stay OPEN; paid canary, limits, roster and enrollment are not changed.

## Continuation from354513d — G1 implementation checkpoint

HEAD matched354513dd9f8a9558b800963664eb9ea053e457ab; no subsequent source delta. All
pre-existing dirty documents and historical untracked files are preserved. No production
access or changes. This checkpoint does not accept G1–G4 or enable the production constructor.

`recover_online_emergency` reuses the existing controller lock and node owner/lock,
quiescence barrier, issuer custody, validator, ProfileStore CAS, grant planning/apply,
directory publication, reconciliation, service resume intents and archive/cleanup ledger.
There is no second signer, writer, timer or authorization database. A durable continuation
ID binds the original COMMIT/plan/prepared receipts/fence; the original decision is never
changed to ABORT. Node handoff archives the original bytes before replacing staged work,
preserves services-before, and moves the owner to a higher fenced emergency epoch.
Stale online publish/fence/abort and ordinary rollback cannot mutate that owner.

States: ONLINE_EMERGENCY_REQUIRED → EMERGENCY_HANDOFF → EMERGENCY_APPROVAL_REQUIRED →
EMERGENCY_AUTHORIZED → EMERGENCY_PREPARED/PUBLISHING → EMERGENCY_COMMIT_DECIDED → existing
resume/cleanup → EMERGENCY_RECOVERED. Missing approval yields a durable state-bound request;
invalid/denied/expired approval leaves all readers stopped. Leaf/CRL emergency uses the
existing operator outage authorization, not a fabricated root signature. Changed pinned
policy/authority is not automatically authorized; offline authority approval remains separate.

The emergency successor is signed from the committed authenticated material with the
current registry. It includes current revocations and advances to committed CRL floor+1,
even if one participant never published the earlier floor. Skipping that unpublished floor
requires the locally retained exact parent plan/prepared receipt proof; ordinary sequence
rules are unchanged. No intermediate forbidden profile is published and no DB is restored.
After both gateways reconcile and publish current directories, RU publishes a matching
delivery marker before resuming HTTP. Intentional quiescence closes old sessions: this is
availability recovery, not TCP continuity. New runtime/TLS acceptance is still a gate.

Checks: `test_online_emergency.py`20 PASS; a containing selection with online renewal,
multi-gateway and activated maintenance192 PASS/1 optional SKIP. Do not add these totals.
The selection covers both pre-node-decision and post-NL-publication revoke, missing/invalid/
expired/denied outage approval, six controller boundaries, nine node handoff response-loss
boundaries, stale owners, immutable parent COMMIT/floor advance, revoked readiness rejection
and surviving identity readiness. These are in-process Python handlers, NOT G2 process death.
Logs: ignored `state-client-build/mesh-online-gates-20261105/python-g1-second.log`.
An initial invocation used a nonexistent test filename (collection NOT_RUN); it is retained
as `python-g1-first.log`, not counted as a passing execution.

G1 runtime handoff, G2 real RPC/process faults, G3 disposable Android HTTP/cache and
G4 final online API/runtime package remain qualification work. Existing accepted maintenance
API archive, old stand provenance and bootstrap success below are not silently replaced.

### Follow-up: current registry and start-intent reconciliation

The stopped, not-yet-prepared continuation can refresh its expected registry snapshot;
the old outage approval then fails binding and the same continuation emits a fresh request.
This permits a second revoke while awaiting approval without manual DB/marker edits.
Archive directory links are fsynced before publishing the handoff owner. An unknown start
response does not manufacture another stop/start: the explicit repeat rechecks reconciliation
and the existing start-intent against service state. Deterministic authorization/policy
failures still fence readers; unavailable/corrupt transport receipts never count as commit
success. There is no background recovery loop. The existing ambiguous-start guard remains.

25 focused tests PASS: the original20 plus stale-approval-after-revoke, two real-contract
SSH budget boundaries, lost start response using the existing SystemdBarrier intent logic
(service adapter simulated), and expired online successor followed by a fresh emergency
signature. Window evidence is a model test:120s ×8 +435s =1395s plus supplied scheduling
lateness; equality/insufficient headroom rejects before journal/owner writes. It is NOT an
Android HTTP/cache cooldown experiment or independent-process fault acceptance.

Exact5ef0193252f00000e87da65a5deebadc3688eb19 evidence:
- Separate unbound maintenance source capsule: SHA256
  `2c04d2815edafe69aa8adb33fad0d097e29d01150e007448814541dfb88b8b91`;
  source inventory`bac40c99de0e6d9fca73a99c189e5d085661a5cb90681464f8ebfacf4f0f1d33`.
  This is NOT the G4 online runtime package. Accepted API source/digest remain unchanged.
- Root/network-none container:292 PASS, zero skips, scoped online/handoff/canonical-profile/
  route/package/expired-recovery/fenced-rollback tests (`root-5ef0193.log`).
- Fresh frozen-source sync artifact and synthetic ProductStore fixtures: mandatory
  bootstrap + bootstrap command `-race -count=3` PASS, zero skips/failures
  (`bootstrap-5ef0193.jsonl`).350 parent/subtest/package PASS events are not350 independent tests.
- Family session + broker `-race -count=1` PASS (`native-5ef0193.jsonl`),27 nested skip events:
  canonical root/reader boundaries, four opt-in DNS checks, process-paced helper and long
  online stand.211 PASS events are not an additive suite total. The old999s stand is retained,
  not rerun or relabelled as this candidate's full-path acceptance.
- Android JVM/API27/API35 delivery checks: NOT_RUN in this continuation; no Android changes.
  Previous accepted ownership checks do not cover G3 actual HTTP/cache delivery.

Raw evidence remains ignored under`state-client-build/mesh-online-gates-20261105`.
One sync packaging CLI invocation supplied an unsupported `--source` flag (FAIL invocation);
the corrected frozen-source builder API and smoke completed before bootstrap. No gate was
disabled. No production access, deployment, APK/catalog change or private state is committed.

### Final source checkpoint for this continuation — not G1–G4 acceptance

Source`b1d17d3be8f347c1d991528ecebbe72c962ef21c` is committed/pushed after5ef0193;
origin/main was checked against the pushed SHA. The final targeted root/network-none
selection is118 PASS/0 SKIP:25 handoff/window/start-intent tests, canonical profile/package
construction, deterministic packaging and entrypoint smoke. It overlaps the earlier292;
do not sum them. `root-b1d17d3.log` is the exact receipt. Native/HTTP sync sources are
byte-identical to5ef0193 (`git diff` of carrier and runtime inventory is empty), so the
fresh artifact-enabled bootstrap/native results above retain that exact provenance rather
than being renamed as a new execution. No full-path999s rerun, Android JVM or API27/API35
HTTP/cache acceptance was performed for this source checkpoint.

Final separate **maintenance source capsule, not online runtime candidate**:
- Source SHA`b1d17d3be8f347c1d991528ecebbe72c962ef21c`.
- Archive SHA256`04da90a06e141685573e983f8affe98cbb24141b11fe184cf66ef4b4cc155548`.
- Source inventory SHA256`d11ae8d634fcb7659bb8d923e22442eb5aaad857a5a3df8f162563e3c17937ae`.
- API wrapper SHA256`94ecc55e7282fa8d1a49bb8291065b9b3acf8b8985179a1579313c78616eb718`.
- Manifest SHA256`8d67351fd966043edc11351b3f562bc0244491559001fa1a9eb0e452e69e2fc3`.
The old accepted archive is not overwritten; these are distinct ignored local files.

| Requested gate | Outcome | Exact scope and remaining transition |
| --- | --- | --- |
| G1 full emergency runtime acceptance | NOT_RUN | Implementation and25 focused tests PASS, including protected SystemdBarrier start-intent reconciliation with simulated service commands. No claim of actual gateway restart/TLS admission acceptance on the final package. |
| G2 independent-process distributed failures | NOT_RUN | Existing in-process fault matrix remains evidence only. No claim that multiple Python objects or fault exceptions are remote process death. |
| G3 Android HTTP/cache delivery | NOT_RUN | SSH120 budget1395s+lateness and pre-write rejection tested; Android300s cooldown/HTTP/Keystore/owner integration on API27/API35 still needs the isolated endpoint. |
| G4 qualified online package | FAIL | Current separate source capsule's ordinary CLI rejects `--mode online` with exit2; `node.construct` still has no online reader/capability configuration and dispatch remains `ONLINE_QUALIFICATION_ONLY`. |

G4 reproduction (no configuration read or mutation): unpack the separate source capsule;
run its `renewal/runtime_controller.py` using the documented Python `-E -s -B` invocation,
`--config <disposable-path> --mode online`. The parser accepts only evaluate/scheduled/
operator/recover/expired-request/expired-apply/expired-resume. Evidence:
`online-entrypoint-contract.log`. An earlier `-I` invocation wrongly excluded the script
module directory and failed import; retained separately, not used as the gate diagnosis.

Required remaining implementation: a distinct pinned current readiness/API/runtime package
and explicit opt-in controller/node entrypoints with capability and actual-reader checks;
then its own real RPC/process, disposable Android HTTP/cache and both-node full-path
qualification. Do not simply enable the in-process qualification flag or replace the old
API archive. The lack of production authorization is NOT the reason these isolated gates
remain unfinished. There is no assertion that the requested stage is complete.

Automatically recoverable within the qualified Python scope: stopped handoff/archive and
lost replies, repeated authorization request, stale approval after another revoke, same
emergency plan/floor publication and already-executed service start. Explicit outage
approval remains required; pinned policy/authority changes require their separate trusted
authorization, not continuity priority. Normal compatible online renewal retains earlier
TLS/mux/TCP evidence; emergency quiescence deliberately closes those sessions and requires
new permitted connections. No live user connection was touched by this work.

Release/live/field gates stay queued, not started: exact immutable client+both-gateway+
publisher artifacts, separately authorized controlled delivery, actual scheduled renewal
on both NL, paired-DNS/WebSocket, weak-link/loss/screen-off/mobile allowlists; only then
controlled paid beta on an accepted baseline with roster/opt-in/terms/access-revocation/
monitoring/stop ownership. No canary replay, payments, enrollment or arbitrary expansion.

## Prior accepted evidence (not current instructions)

**Latest outcome,12:55UTC: positive isolated online stand PASS; requested stage INCOMPLETE.**
Source checkpointa8e1db9 plus narrow negative-test/strict-JSON delta2cbd304 is pushed.
The mandatory bootstrap gate now passes including its isolated Python artifact contract.
Emergency reconciliation/handoff, complete distributed failure/cache acceptance and
online runtime packaging remain source gates. The qualification RPC is disabled by the
production constructor. Earlier checkpoint paragraphs below are historical progress,
not additional active NEXTs or permission to activate anything.

## Entry and boundary

Entry HEAD is exactly `15ef592bf92c143839130da7884328e4a7d9918f`. The four pre-existing
dirty documents and six untracked historical files are preserved. This is the existing
Android MESH incident, source/isolated qualification only: no production access, installed
APK change, catalog, timer, paid/cohort/admission/boot change or activation permission.
Installed/opt-in118 and updater113 remain unchanged. Paired-DNS/WebSocket remain OPEN.

## Dependency map and selected contract (implementation in progress)

- RU's existing issuer signs leaf/CRL materials using the existing local custody key.
  ProductionController owns the operation under DurableOperation.lock; ProductionNode
  uses the existing owner, staging/archive ledger, membership and canonical ProfileStore.
- The controller transaction.json/plan.json carries the durable decision. Online prepare
  must not promote files before this decision; normal quiesced/emergency paths remain.
- NL gateway profiles feed Family TLS, credential exchange, lease and broker monitors.
  Runtime receipts must come from the actual reader, bound to its process instance and
  exact profile digest, not merely a successful rename. Unknown runtime contract rejects.
- RU CRL/issuers and per-node directory feed authenticated readiness. A delivery gate
  must hide the committed successor until both corresponding runtime readers acknowledge.
  Directories retain the running rooms; no restart/new seed is evidence of continuity.
- Readiness's existing certificate retention (expires > now+300) must be reconciled with
  the Android300s persisted cooldown,30s owner polling,30s request and bounded exchange.
  Otherwise an early CRL-only delivery may produce a refused, non-retried candidate.
- Recovery follows the same durable decision/fenced owner, not the newest local file.
  Pre-decision abort requires unchanged live state; post-decision may only roll forward.

Online controller/node/publication/native qualification is NOT yet complete at this
checkpoint. No production route is enabled by committing this source.

## Bootstrap diagnostic contract

The inherited six assertions are a phase-classification regression: OpenServer sent
profile/TLS-open failures to the callback for an authenticated broker exchange, although
no authenticated exchange or provider admission occurred. The preserved contract requires
that callback only after Family authentication. Admission failures are not successful
exchanges, but their errors must still be observable.

OpenServerObserved separates the admission observer from the authenticated exchange
observer. The command records structured bootstrap_admission_rejected with stage/reason;
the existing exchange event remains reserved for authenticated protocol failures. The
legacy OpenServer contract and all six negative assertions are unchanged. Added negative
checks require exactly one family_open admission report and zero exchange reports, no
descriptor/provider call/authentication; valid control has no rejection report.

Raw local evidence: `state-client-build/mesh-online-renewal-20261105/`.
Baseline15ef592 is rerun from an isolated source archive; updated bootstrap `-race -count=3`
passes. An initial broader run retains a transient existing authenticated-busy wire-reason
failure; it is not erased or attributed to this fix without evidence. No tests are disabled.

## Remaining gates

Finish online transaction, runtime/readiness integration, both-node continuity and fault
matrix before claiming this stage complete. Then stop. Full release CI, new immutable
artifacts, equal gateway builds, scheduled live renewal and physical/mobile allowlist
acceptance remain separate, unexecuted gates. No independent timer or writer is authorized.

## Implementation checkpoint (not stage acceptance)

The explicit `MESH_SAME_HOLDER_ONLINE_V1` path reuses the controller/node locks,
owner journal, issuer, membership, staged file CAS, ProfileStore, SQLite sequence and
existing archive ledger. It does not change the ordinary quiesced transaction. Node RPC
requires an explicit in-process qualification flag; packaged production construction
does not set it. There is no new timer, production online CLI activation or second signer.

Window calculation after initial read: eight bounded RPC rounds plus explicit scheduling
lateness, Android cooldown300s, owner polling30s, readiness request30s, maximum ordinary
lease control attempts55s, credential exchange15s and skew5s. Thus local1s-RPC/0s-schedule
qualification requires443s; configured SSH120s plus schedule requires1395s+schedule.
Neither production validity nor timeouts are increased. Unknown timing rejects.
Both gateway bindings, authority, keys, grants, policy revisions, CRL floors and current
material validity are checked. Existing client certificate records also need headroom.

States: ONLINE_ACQUIRING/FENCING → PREPARED/STAGED → durable COMMIT_DECIDED →
per-node DECIDED/PUBLISHED → RU delivery-ready → CLEANING → COMMITTED. Before the
decision, explicit ABORT requires unchanged credential files and does not restore DB rows.
After COMMIT, retry uses the same plan/digests and higher fencing epoch, never a new CRL
or rollback. Lost RPC results reconcile against node state; completed cleanup is archived.

During NL-only publication, existing peers retain their authenticated generations and RU
still gives predecessor readiness. Runtime receipts use the same native credential loader,
cryptographic successor validation and process-instance nonce. RU only exposes the new
CRL/readiness generation after both exact profile hashes acknowledge. It copies validated
current directories without creating seed rooms; no distributed instantaneous atomicity is
claimed. Readiness uses a fixed committed issuance target, not a moving target per refresh.
Local publication is not a native session commit; only authenticated exchange advances it.

45 focused tests cover17 controller crash boundaries,17 node crash/lost-response points,
four durable abort positions, stale epochs, maintenance contention, client headroom,
duplicate delivery/commands and two revoke positions. Positive/unit readers are doubles;
those tests alone are NOT native continuity proof. Existing affected Python/package scope
is214 PASS/5 optional skips. A real two-node stand has reached two authenticated native
generations on both nodes; its complete cross-bound outcome/provenance is pending.

Known blocking gaps at this checkpoint: post-decision emergency detection safely stops
readers and preserves the COMMIT decision, but machine handoff/reconciliation from that
fenced state is unfinished; no manual marker deletion is prescribed. Complete malformed
receipt, expiry, old-peer/new-connection and cache-delay acceptance is also outstanding.
The accepted maintenance API archive is intentionally unchanged; it must not be silently
substituted with the newer readiness implementation. Final online runtime packaging and
root qualification remain separate required gates. This checkpoint is NOT release-ready.

## Additional negative and bootstrap evidence

Source checkpoint `a8e1db900105219b22abae21accd2c2b6e2f5b30` is pushed and remote SHA
verified. The real native stand is repeated from an immutable export of this commit.
The earlier development stand passes999.28s but is not substituted for that frozen-source
acceptance. Isolated root/package scope on the checkpoint passes219 tests. The first root
attempt incorrectly put root-owned fixtures below a user-owned bind mount (UNSAFE_PARENT)
and omitted Git's explicit read-only repository trust; both harness errors are retained.
The repeat uses root-owned tmpfs, without relaxing ProfileStore ownership checks.

Focused online negatives now pass55 tests: add unavailable participant/precommit abort,
rollforward after predecessor expiry versus successor-expiry fencing, corrupt durable
decision, and six readiness-marker failures with an unconsumed proof challenge. Strict
existing JSON parsing rejects duplicate marker fields; no new runtime package dependency.

The six inherited cases (unknown issuer, wrong Family, revoked device, wrong gateway,
stale CRL floor, stale revision) all failed the same baseline `auth_test.go:87` assertion:
expected zero authenticated-exchange reports before TLS admission, actual nonzero reports.
Baseline15ef592 reproduces each case five times. The new observer preserves separate
admission diagnostics and all denial assertions.

The expanded bootstrap artifact gate also reproduces an independent busy-reason assertion:
an ERROR frame gives a direct public Code, while a peer closing before HELLO gives the same
public Code wrapped by the existing startupdiag.Preserve with its receive cause. Comparing
Go error object identity incorrectly calls the latter a changed wire reason. The check now
requires both errors.Is and exact startupdiag.Legacy category; a new deterministic test
also requires the original receive cause and unchanged public Error text, and contrasts
the actual ERROR-frame branch. No production error is suppressed or authorization changed.
Ten race repetitions of busy, both HELLO outcomes and negative admission boundary PASS.
The complete artifact-enabled bootstrap repeat is still required after this assertion fix.

## Frozen-source stand result

`a8e1db900105219b22abae21accd2c2b6e2f5b30` exported with `git archive`, mounted read-only;
one network-isolated Docker container contains three logical node roots, actual
ProductionController/ProductionNode handlers, real authenticated RestrictedReadiness
proofs, and two separate Family TLS/mux/broker runtimes. This is not a physical three-host
or SSH-failure qualification. A local packet carrier and local echo/DNS/HTTPS origins
replace Telemost/Internet. Synthetic signing/device keys never leave private test state.
Server material is written by the real transaction; client material comes from readiness
and wholedevice.DeliveryMaterial, not a manually supplied SessionMaintenance profile.

The fixture shortens synthetic leaf/CRL validity only: initial500s, successors1000s;
production4h validity is untouched. The real300s Android cooldown is included in the443s
window, not waited by an actual Android process. The native driver validates readiness
and offers each distinct profile through the existing maintenance owner. This does not
claim Android HTTP/cache timing or APK118 continuity acceptance.

All times below are UTC on5 November2026:

| Observation | NL/AMS1 fixture | NL2/AMS2 fixture |
|---|---|---|
| Original security/leaf/CRL bound |12:47:25|12:47:25|
| Original lease bound |12:39:17.030930941|12:39:17.031156091|
| Generation1 native confirmation |12:39:09.588154962|12:39:09.726322421|
| Generation1 security/leaf/CRL bound |12:55:42|12:55:42|
| Generation2 native confirmation |12:47:29.328411896|12:47:29.390912114|
| Generation2 security/leaf/CRL bound |13:04:02|13:04:02|
| Final crossing observation |12:55:43.125387420|12:55:43.127724158|
| Final lease bound |12:55:48.057772975|12:55:48.057092799|

CRL floors1→2→3 and exact common CRL bytes agree on both gateways. Native authorization
generation is checked on both endpoints for each exchange. Original client/server mux
objects and exactly one accepted original TCP are asserted during every traffic iteration;
the same stream survives both crossings with883 verified payloads /18,433 useful bytes
in EACH direction per node. The final explicit fresh TCP makes the final accept count2;
this is a deliberate new-flow check, not replacement of the original connection.
DNS and certificate-verified HTTPS succeed after both old bounds. No mock deadline setter,
service restart or new seed is counted as continuity. Entire stand:999.12s PASS.

Receipt persistence timestamps provide upper bounds on the actual runtime-read observation,
not a claim of distributed instantaneous commit:

| Generation | NL receipt | NL2 receipt | RU delivery-ready receipt | Both native confirmations by |
|---|---|---|---|---|
|1|12:39:07.869196|12:39:07.870507|12:39:08.084377|12:39:09.726323|
|2|12:47:27.635243|12:47:27.637729|12:47:27.785584|12:47:29.390912|

Thus observed RU-ready→both validated native confirmations is under1.643s each round.
The readiness-read and exchange are not separately timestamped; no invented split latency
is reported. Receipt times are retained filesystem timestamps, while native times are
explicit harness observations. At the second issuance the predecessor has495s remaining,
above the443s local budget. A transport with the real120s SSH timeout requires a different,
larger eligibility window; the local result does not qualify deployed scheduling.

Runtime process-instance receipts remain unchanged across both generations:
- NL: `c931f9a6929dc8c82dd277c623f4cf8b40d91771d115c1ef72abaf46e03f0d96`.
- NL2: `fa4f8154f4a37bddbc29f0baa0ab94e9da6136ae16742ace28a7a67ac1260918`.

| Gateway | Generation1 profile SHA256 | Generation2 profile SHA256 |
|---|---|---|
|NL|`cd9983e627d431e1b1c03d9bce53aceb81e5276058a5316b3748780515c2ccde`|`4c48d25db1f0a94a1f4b3d3218c244ad71dfe6c4f75644d0451bef0fdeab4bf6`|
|NL2|`2415d0fbb5cd131b445c2bb9ac26daa49aced789c9db6df7c68205a2803e2557`|`3a2cf95e91930838e79216e4500f185b48f9811f53947b60a41e10f935996427`|

## Final check scope and provenance

- Python scoped controller/node/readiness/multi-gateway/package selection on2cbd304:
  **229 PASS,5 optional harness skips**. Focused online subset: **55 PASS**.
- Isolated root canonical custody, profile routes, archive/recovery, packaging and online
  selection ona8e1db9: **219 PASS**, including existing immutable accepted API checks.
- Go1.26.1 `-race -count=1` on four affected packages (familysession, roombroker, bootstrap,
  cmd/bootstrap-broker) ona8e1db9 with fresh ProductStore fixtures: all packages PASS;
  28 nested optional/root/DNS/stand skip events are not concealed.
- Root roombroker race binary:163 parent/nested PASS events,5 skips (four explicit DNS
  subtests and separate long stand). The long stand separately runs actual isolated DNS.
  An earlier broad run with DNS enabled for every test hits an existing fixture collision:
  cross-session proof test creates two independent port53 listeners. That failure is
  retained, not erased or reported as production DNS failure; the proof test passes in
  the normal root suite. No unrelated test is removed or desktop failure repaired.
- Final mandatory bootstrap and command `-race -count=3` on2cbd304 with real disposable
  identity fixtures AND source-built isolated sync Python artifact: **PASS, zero skips**,
  350 parent/nested/package PASS events. Earlier failure logs remain in local evidence.
- Android/JVM/API27/API35 are not rerun: this delta does not change Android/native owner
  integration; those accepted previous-stage checks are not relabelled as new acceptance.

Source and artefact distinctions:

| Item | Provenance/SHA256 |
|---|---|
|Online stand/source checkpoint|`a8e1db900105219b22abae21accd2c2b6e2f5b30`|
|Strict marker parsing/negative bootstrap assertion delta|`2cbd304684e23e855df75a8d9e5666e53a64805a`|
|Isolated root image|`sha256:ca61f885607656ea89f5726853761c4c533d050faf26b71853575c24ca1ed123`|
|Unbound maintenance capsule|`beb68dd770285d7e2a2315111c8ab6075af0834e0be1dfd692941acdeab7a23c`|
|Capsule source-files inventory|`d6bbe45081e7652e76314f97589708028d9129d9ca795a22258e8f679baa3a82`|
|Capsule manifest|`6bb965853b5e75dd49ac7d61891435d31cde4cb66910dcda8da98357b7303e5e`|
|Race native stand test binary|`325d9263acbdf7e787114089be71fae520f786cf762eb0e11d8ef3d906c8fb23`|
|Readiness validation helper|`2ef72dfe1c5ae57eba69cbc013c72a2f75a4fb963284159f39695e26bbca323a`|
|Source-built sync Python artifact|`0227d22ccb5be6b1808e560c35a4dabd3da923dc9ed8aaa830374792968f11ff`|

Capsule keeps accepted API sourceedca544 unchanged; it is NOT an online runtime package.
No archive, native test binary, synthetic identity or raw fixture state is committed or
distributed. Private evidence stays under `state-client-build/mesh-online-renewal-20261105/`;
the sanitized `stand-a8e1db9-public-summary.json` contains no private material or traffic.

## Unfinished source gates and later release gates

The requested stage is deliberately **not marked complete**:
1. Post-COMMIT revoke/emergency safely reaches ONLINE_EMERGENCY_REQUIRED with readers
   fenced and original decision retained, but it lacks the machine handoff to the existing
   quiesced emergency transaction. Do not delete its marker or edit profiles/DB to resume.
2. Complete receipt-corruption/unknown-participant/process-death reconciliation, including
   actual independent controller/node processes and concurrent directory publisher custody.
   Logical crash/lost-response tests do not prove every remote process failure boundary.
3. Qualify late/cached Android delivery and new-session admission throughout partial
   publication, plus unsupported peers within this coordinated stand. Previous native
   legacy/revoke/late-ACK/partial-commit/cancel/control-drain negatives remain in the race
   scope, but are not a substitute for all coordinated end-to-end scenarios.
4. Explicitly package and validate the current readiness/runtime-reader contract; retain
   the old accepted maintenance API and production-disabled qualification guard meanwhile.

Only after these source gates may a separate release decision consider immutable artifacts,
full platform CI, exact matching gateway binaries, approved production scheduling/window,
online live acceptance on both nodes and physical weak-link/screen-off/mobile allowlists.
APK118 is not upgraded by this source work and receives no continuity promise. Production
activation, paid/cohort/boot/catalog changes and fixes for paired-DNS/WebSocket are NOT done.
No rollback of live systems is needed: none were changed. Source fallback is the unchanged
quiesced path; this is not permission to reset Git or alter a live transaction.
