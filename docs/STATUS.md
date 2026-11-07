# Текущее состояние / Current state

**7 November — bounded ARM64 field-delivery preparation, not deployment.**
Accepted F/application9bf02724/native6eb61a9 remains immutable. Production-tag ARM64
JNI is now built through the accepted builder; beta120 is reserved for the unpublished
candidate (118 is not reused). Packaging accepts a separately pinned native commit only
after checking its complete runtime-source closure against application HEAD. No native
runtime changes, new AVD, provider rooms or phone operations. Server entry packaging and
final APK gates remain in progress; fresh real locator and vault signature are deliberately
deferred until authorized server start/user handoff. Public113/catalog7 unchanged.
Local119 draft was never signed/distributed;119 is already reserved by a separate paid
branch, which remains untouched. This cold candidate uses120 to avoid that collision.
[Delivery preparation and remaining gates](releases/2026-11-07-cold-field-delivery.md).

**7 November — API28/emulated CELLULAR-only cold DROP PASS (F).**
Unchanged application9bf0272/native6eb61a9/JNI17119f00…60c59 with harness252c87e:
real API28/x86_64 Android, sole foreground/unrestricted CELLULAR, no WiFi/VPN/readiness,
fresh verified locator407s, registered synthetic identity. Exact guest DROP records4/3
packets on former HTTPS/RNS destinations. HTTPS consumes5.002s, RNS6.201s including
initialization; provisioning starts with18.790s readiness budget and validates fetch with
7.279s remaining. Native27 protected/0 denied; both request IDs correlate server200.
Ordinary MESH READY57.565s; DNS, default verified HTTPS and gateway egress pass. Every
traffic-boundary snapshot retains zero DNS timeouts/errors and zero Mux protocol reasons.
Original example.com still returns NXDOMAIN without counter errors. No product/native
change or timeout increase; all A–E artifacts/original FAILs verified unchanged. Own
AVD/workers/authority stopped, lock free, monitor joined; room deletion NOT_VERIFIED.
This is emulator cellular, not the original user's physical operator, G4 or field rollout.
Field gate: compatible signed ARM64 candidate, real trust/authorized provisioning entry,
and a valid pre-Connect locator; assets-only expiration remains an operational constraint.
[F runtime, budgets, exact artifacts and field gate](releases/2026-11-07-cold-api28-cellular.json).

**E counter analysis — timing localized, exact per-request cause still unknown.**
E remains accepted in its exact API27/x86_64 synthetic scope. Its saved counters place
timeouts in(45.894,51.100]s and(51.100,56.252]s after Connect; protocol errors rise
in(56.252,57.268]s, after READY43.982s but before DNS_OK58.018s, HTTPS60.616s and
cleanup62.267s. The later example.com NXDOMAIN cannot explain these earlier increments.
No per-request IDs or protocol-reason breakdown were saved, so late unmatched DNS frames
are a code-supported hypothesis, not an established E cause. Existing JNI exposes reason
counters: the targeted test now retains them and per-traffic-stage snapshots. Existing
runner adds API28, actual sole eligible CELLULAR checks and exact guest DROP; no product,
JNI, budgets or security changes. Seven selected harness checks and the network-only
27/28/35 probe pass. F's zero counters do not retrospectively identify or fix E's cause;
E lacks per-DNS IDs, reason breakdown and gateway resolver exchange timing. No unchanged
repeat is justified. No public/production/G4 action.
[Bounded follow-up evidence](releases/2026-11-07-cold-api28-cellular.json).

**7 November — real cold positive path PASS; bounded incident goal achieved.**
E/14c2b81 (application9bf0272, native6eb61a9/JNI17119f00…60c59 unchanged) reaches
ordinary MESH READY43.982s from a registered synthetic identity with no readiness/VPN,
fresh verified locator and both exact former direct paths rejected. Real Telemost/TLS,
challenge/fetch, authorized verified encrypted bundle, DNS, default verified HTTPS and
matching gateway egress pass. Native28 protected/0 denied; request IDs correlate server
issuance. D also reached READY, so the bind fix is not inferred from one lucky success:
B's background-network EACCES, targeted before/after regression and D/E bind success agree.
E confirms original example.com NXDOMAIN through TUN, matching the host resolver; no DNS
settings changed. Observed2 DNS timeouts/2 Mux protocol errors remain unclassified: this
is positive-path acceptance, not zero-loss or sustained-stability acceptance. Old FAILs/
all19 original artifacts and A–D remain. Own processes/authority/AVD stopped, lock free,
monitor joined; provider room deletion NOT_VERIFIED. Only disposable beta118 qualification
APKs installed; public/production/G4/phones unchanged. No further task starts automatically.
[Final runtime, provenance, limitations and cleanup](releases/2026-11-07-cold-connect-e.json).

**7 November — cold provisioning and ordinary MESH READY confirmed; traffic gate next.**
D on9bf0272 confirms the bind repair:29 protected/0 denied, real Telemost/TLS, challenge
and fetch responses validated, registered identity authorized, encrypted bundle accepted,
ordinary MESH READY in42.762s. Server request IDs correlate both operations. The subsequent
example.com DNS check fails; the unchanged gateway host resolver independently returns
NXDOMAIN for A/AAAA and host HTTPS fails too. api.ipify.org DNS/verified HTTPS pass on
the host, not yet Android. Keep all DNS/routes/security/native unchanged; qualify that
working public traffic target and capture original-target RCODE plus numeric Mux counters.
Own D resources stopped, all failures retained. No public rollout; room deletion unverified.
[D READY and traffic evidence](releases/2026-11-07-cold-connect-d.json).

**7 November — C exposes API27 compatibility error in the selection correction.**
Modern FOREGROUND=19 does not match API27's then-hidden bit18. C fails before JNI,
not a confirmation of the bind fix. Use bit18 only on supported SDK27 and public19
on28+; actual-bit regression fails before, passes after on27/28/35. Also reject hex-text
egress fixtures before packaging (the traffic verifier expects32 raw bytes);4 packager
tests pass. Neither issue changes JNI, trust, deadlines or CPU observation-only. Own C
resources stopped, no READY/traffic, room deletion unverified; corrected runtime pending.
[C evidence and correction](releases/2026-11-07-cold-connect-c.json).

**7 November — bind cause localized; minimal selection repair, confirmation pending.**
Diagnostic Connect B preserves NETWORK_BIND/SOCKET/EACCES(13), after successful FD_DUP,
before TLS. Selected CELLULAR lacks FOREGROUND; WIFI has it. API27 netd denies this
background network to the ordinary app. Provisioning now filters unrestricted foreground
physical networks before pinning, and fails closed on demotion. No added permission,
forced WiFi, resolver override or security/budget change. The targeted replay fails on
old Java and passes on the correction, including eligible cellular and no fallback.
Managed APK confirmation next; accepted JNI/Android JNI PASS unchanged. B resources
are stopped; room deletion unverified. No bundle/READY/traffic yet; no public rollout.
[Cause and exact B artifacts](releases/2026-11-07-cold-connect-b.json).

**7 November — real cold Connect now reaches Go; socket bind cause under investigation.**
Owner permits evidence-driven corrective runs without new consent; CPU observe-only
continues. Fixed packaging passes in the stand. The cold AutomaticConnection fails in
2.206s: native last success TELEMOST_CREATE, first failure SOCKET_PROTECT_BIND /
SOCKET_DENIED,0 protected/4 denied,4ms elapsed/27993ms native remaining. CELLULAR was
available at bind; Java reports IO. TLS/challenge bytes were not reached; server challenge
and certificate counts are0. Both exact guest blocks register2 rejected packets each.
No route-race or trust diagnosis is inferred. Add only Java FD_DUP/NETWORK_BIND and safe
nested errno/type fields to distinguish this failure. Network-probe regression and39
harness tests pass. Next diagnostic APK reuses unchanged JNI; runtime is still pending.
[First concrete cold result and immutable artifacts](releases/2026-11-07-cold-connect-a.json).

**7 November11:14UTC — CPU stop overridden; packaging defect found and fixed offline.**
One19877fd API27 NVIDIA/KVM run retains CPU readings without CPU termination; no guard
stop occurs. It reaches fresh registered identity/two own rooms/verified locator but
stops before Connect: apksigner exits2 because one one-line password file is supplied
twice (`--ks-pass` and `--key-pass`), exhausting the stream. Exact offline replay proves
the cause. The versioned asset packager now omits redundant key-pass and is called by
the existing runner.39 targeted harness tests pass; real signing/verification/alignment
of both APKs succeeds offline with unchanged manifest/dex/JNI. Those offline inputs are
expired, not installed and not a new runtime. Own processes/container/AVD are stopped,
lock released, room deletion NOT_VERIFIED. Source6eb61a9/JNI/Android PASS unchanged.
Connect/native snapshot/READY/DNS/HTTPS/egress remain unexecuted. No automatic extra AVD;
an additional preparation launch needs owner approval under the one-launch constraint.
[Cause, regression and offline artifact identities](releases/2026-11-07-cold-cpu-observed-runtime.json).

**7 November — owner supersedes CPU thermal stop for one new attempt; runtime pending.**
Explicit `--observe-cpu-temperature-only` retains CPU raw frames/85°C observations but
does not abort on that CPU reading for the selected run. Default CPU stopping remains;
GPU80°C, sensor/monitor errors, memory/lock and all finite budgets still enforce stops.
38 targeted harness tests pass; no product/JNI change or old suite repetition. No claim
of sensor correctness, thermal safety or provisioning repair. One fresh cold runtime
is authorized by the owner, not an automatic retry series; prior receipts stay immutable.

**7 November11:06UTC — authorized single guarded run STOPPED_BEFORE_CONNECT.**
Versioned4854f96 runner/guard actually imported; source6eb61a9/JNI17119f00…60c59
and accepted Android JNI PASS unchanged, no rebuild or suite repeat. One preflight and
one API27 NVIDIA/KVM AVD reach Android-ready/no-VPN/no-readiness. Protected local OAuth
access starts the isolated authority/workers, creates two test rooms and a fresh verified
locator (415s remaining). During assets-only packaging, the exact saved WATCH frame
reports Core4 raw91000/max91°C, Package90°C, GPU56°C: CPU_TEMPERATURE_LIMIT at58.199s,
with121.801s preparation remaining. Secondary ASSET_PACKAGING_FAILED is not the primary
cause. No final signed APK/install, guest blocks, Connect, Android native snapshot or
READY/DNS/HTTPS/egress. Own processes/groups/container are gone; monitor joined and lock
released. Room deletion NOT_VERIFIED. Both prior FAILs/all19 artifact hashes preserved.
This local attempt is finished: no automatic repeat; a separate owner decision on the
test environment is required. No heat-source attribution, physical94°C conclusion,
provisioning fix, product/public/production/G4 change or rollout/rollback is claimed.
[Exact stop, load, provenance and artifact hashes](releases/2026-11-07-cold-guarded-runtime.json).

**7 November — source-only harness repair; runtime remains stopped.**
Watcher and stage audit now decide from the exact saved temperature frame, including
raw inputs/labels, per-read times, capture interval and computed maxima. Typed stop
evidence separates CPU/GPU limits, unavailable sensors, monitor failures and lifetime
expiry. Missing/unreadable sensors remain fail-closed;85°C/80°C are unchanged. The
captured as-run scripts remain immutable; their runner is versioned with the corrected
helper under tests. Preparation180s, instrumentation attempt390s (including the unchanged
200s product candidate), cleanup120s and overall705s replace the conflicting global180s
cap. A separate clock watchdog remains responsive to a blocked sampler; forced teardown
has at most5s authority-stop allowance. Monitor join is bounded6s and preserves the last
completed frame, without another read.34 targeted mocked/controlled-clock tests pass;
no sensor observation, AVD/OAuth/rooms/APK/native build/Connect or old suites run.
Product6eb61a9/JNI17119f00…60c59 and Android JNI PASS are hash-verified unchanged.
This fixes runner contradictions, neither disproves old94°C nor repairs provisioning.
[Harness change, budgets and scope](releases/2026-11-07-cold-harness-guards.md).

**6 November22:01UTC — thermal-reader audit; cold runtime explicitly stopped.**
The exact6096535 as-run reader hashes are verified. Both paths select coretemp/k10temp
`temp*_input` and divide the raw integer by1000; no max/crit/highest source explains94.
The watcher stores only its own earlier samples, sleeps3s after work, and stage audits
independently reread without updating that peak. Identical-input replays agree;66 then94
is reproducible with separate samples, not proof of the historical timing or physical peak.
Old raw integers/per-sensor times/watch history/fan RPM are missing. Neither overheating
nor a faulty sensor is established; the physical94°C event remains INSUFFICIENT_DATA.
One passive60s observation on verified Dell XPS15 9500/i7-10750H records coretemp53–76°C
package, Dell CPU55–61°C and reported fans2763–2774/3076–3088RPM. These newer readings
do not refute old94 or establish old fan behavior. A subsequent paired sensors/sysfs
check matches all7 coretemp inputs; the minute's sensors JSON parse fails, so a full
per-second sensors comparison is unavailable. Raw sysfs readings/timestamps are saved.
A separate reproduced bug is fixed in a versioned test helper: missing CPU sensors
must stop, not fabricate0°C. It does not explain the populated94°C frames.16 targeted
mocked tests plus exact/fixed input replays pass; no emulator/provider/build or cold gate
runs. Original artifacts/native/Android PASS remain untouched;85°C is unchanged.
[Reader sources, limitations and bounded observations](releases/2026-11-06-beta113-field16-bootstrap.md#thermal-reader-audit).

**6 November21:47UTC — reduced-load attempt stopped after Android ready, before rooms.**
Fromf7073e6, unchanged source6eb61a9/JNI17119f00…60c59 and existing binaries/APK bases
are verified and reused; accepted Android JNI PASS is retained, no gate/suite/rebuild.
One initial preflight passes at CPU58°C/GPU52°C; one own API27 NVIDIA/KVM AVD boots
with the existing data-filesystem userdata. Own test packages/readiness and VPN are
absent; the guest clock converges without adjustment. At the next existing resource
gate, `ANDROID_READY_NO_VPN_BEFORE_ROOMS`, coretemp Package id0/Core2 reach94°C
against85°C,41.740s after the initial preflight. GPU53°C and available16279992KiB RAM
pass. The paired1.069s CPU sample shows QEMU PID3079674 at2.81%, other processes58.01%
(100%=one core), chiefly firefox-bin PID19485 at21.51% and ptyxis PID16284 at12.16%.
No own compiler/authority/Telemost-worker is running. This is a measured sensor-limit
violation despite reduced sampled load, not proof of a particular process causing heat.
The background watch's66°C maximum misses this stage-audit94°C sample and is not the
whole-run peak. OAuth, rooms, fresh inputs, APK packaging/install, guest blocks and
Connect are NOT_RUN; zero authorized Connects consumed, live native cause still unknown.
Own runner/QEMU are gone, lock free, authority absent; zero new rooms. Both FAILs/19
artifacts, accepted Android PASS andf7073e6 evidence remain unchanged. No restart:
the owner's next decision is environment migration, not another identical local cycle.
No production/G4/public APK/catalog/version or system/foreign-process change.
[Measured reduced-load stop and cleanup](releases/2026-11-06-beta113-field16-bootstrap.md#reduced-load-runtime-stop).

**6 November — ordered single-AVD attempt: measured thermal conflict before workers.**
The accepted Android JNI PASS is retained, not repeated. Product6eb61a9 and JNI
17119f00…60c59 are unchanged; no native build or host/JVM/race suites. Immutable
components are prepared first; one own API27/NVIDIA/KVM AVD reuses data-filesystem
userdata. No reboot between stages. After Android boots and own test packages are
reset/no VPN observed, the existing guard stops it at34.035s during pre-worker clock
observation: coretemp Package id0/Core5 reach87°C against85°C. Over the paired3.072s
CPU sample, own QEMU PID3031862 uses82.35% and other processes total226.62% (100%=one
core), led by Isolated Web Co PID2937122 at79.09% and firefox-bin PID19485 at68.35%.
No own compiler, authority, Telemost-worker or secret-input process is running.
GPU60°C and available memory13860068KiB do not trip their guards. This identifies the
observed AVD-plus-desktop thermal conflict, not an exclusive thermal cause per process;
the previous pre-AVD86°C event still lacks retrospective PID attribution.
No OAuth, new rooms/identity/locator, final APK packaging or Connect is started. The
one authorized Connect remains unused; live provisioning cause/READY/traffic remain
unknown. Own runner/QEMU are gone, lock free, no authority present; no foreign processes
or cooling/power settings changed. No restart or automatic host/phone move. Both old
FAIL_RUNTIMEs/19 artifacts and accepted Android evidence remain hash-identical.
[Measured stages and process evidence](releases/2026-11-06-beta113-field16-bootstrap.md#ordered-runtime-resource-attribution).

**6 November21:12UTC — actual Android JNI PASS; single Connect NOT_RUN, thermal preflight.**
Continuation from6eb61a9 has no product-source delta. That exact source, including the
final underlay/cancellation fixes, is rebuilt as real Telemost x86_64/API27 JNI
17119f00…60c59; seven defined exports, manifest and packaged bytes are verified.
The short provider-free test passes on actual API27/NVIDIA/KVM: pre-Go arguments,
Go locator rejection/security and closed-handle diagnostic retained across Close.
This is Android JNI evidence, not carrier/TLS/provisioning readiness. Existing host-JNI,
100 JVM and targeted race results are retained, not rerun without a source change.
After that PASS, protected local input accesses the same authorized OAuth entry; a new
synthetic identity/authority and two test rooms produce a freshly verified signed
locator. Final disposable118 APK79c4ea7b…2cbbfc contains real inputs and the latest JNI,
not placeholders or previous readiness. Native/APK builds and emulation are sequential.
Before the fresh cold AVD starts, CPU samples68/80/86°C fail the unchanged85°C guard;
GPU56/56/57°C, memory and data-filesystem space pass. No second guest boot, Connect,
client provisioning Network/bind, TLS or challenge occurs. No restart is attempted.
Own first AVD, authority, workers and secret-input processes are stopped; lock is free.
Authority challenge/certificate counts are0/0. Two provider room objects were created;
their deletion is NOT_VERIFIED. Both previous FAIL_RUNTIME receipts and19 artifacts
remain hash-identical. The single authorized Connect remains unused; the live root
cause and bundle/READY/DNS/verified HTTPS/egress remain unknown. A future continuation
needs a stable resource window with the stand running and a new verified locator/APK;
do not reuse this expiring locator or infer live success from the offline PASS.
No product timeout/retry/admission, production/G4, public APK/catalog/version change.
[Current evidence](releases/2026-11-06-beta113-field16-bootstrap.md#actual-android-jni-pass-live-preflight-stopped).

**6 November19:40UTC — single corrected diagnostic attempt FAIL_RUNTIME; no more retries.**
The actual AutomaticConnection MESH candidate receives absolute guest deadline339645ms
(200000ms budget), not the old harness30s. It fails after1.792s with preserved enum
BOOTSTRAP_UNAVAILABLE,198230ms candidate budget remaining. HTTPS and RNS fail as
deliberately blocked; provisioning creates a JNI lease but returns no challenge reply
with about28.27s of the real readiness budget remaining. No deadline expired in this
attempt. Fresh authority challenge/certificate counts both remain0. No received bundle,
validator/vault acceptance or NativeRestricted.beginReady/READY/DNS/HTTPS/egress PASS.
The original issued-bundle attempt remains FAIL with its unknown delivery boundary.
The native provisioning null-reply boundary is localized, but its underlying transport/
TLS/lease error was collapsed by JNI and is still unknown. Do not label it AUTH, slow
Telemost or a protocol rejection. Post-run source diagnostics now preserve original IO
before challenge wrapping (37 JVM tests PASS); that diagnostic change was not rerun live.
Owned connection/AVD/authority/workers and credential processes exited; shared emulator
lock is free. Two owned room objects are recorded privately; deletion remains NOT_VERIFIED.
No token file, deployment, public APK, production/G4 or other-branch change.
[Exact follow-up sequence and remaining limits](releases/2026-11-06-beta113-field16-bootstrap.md#single-corrected-diagnostic-attempt-6-november).

**Earlier source checkpoint — harness deadline defect established; follow-up was pending.**
Hash-verified original instrumentation `952790bb…fc590` directly constructed the engine
with `elapsedRealtime()+30000`; it did not use ConnectionService/AutomaticConnection.
This is not the product MESH budget (200000ms candidate/300000ms Connect).
The separate real readiness fetch remains 30000ms. Original FAIL and all artifacts
remain intact; issued certificate does not establish delivery or acceptance.
The corrected harness uses the existing AutomaticConnection MESH path, snapshots
typed failure/trace/native state before cleanup, and never polls restoration/retries.
36 focused JVM tests and coldprovision Go tests pass; disposable APK prebuild passes.
Exactly one new API27/Telemost diagnostic run is authorized, not yet performed.
No timeout, trust, TTL, admission, production or public artifact change.

**6 November — actual Android/Telemost cold provisioning attempt FAIL, not auth-blocked.**
Protected local input now reads only the authorized vault entry and pipes its value
to the disposable test process; no credential is printed, persisted or sent to the
client. After G4 resource release, sequential API27 NVIDIA/KVM AVDs pass renderer
checks. The first server fixture incorrectly pins ICE to a loopback resolver and
fails before locator publication; its evidence is retained. The corrected fixture
uses the existing server Telemost connector and publishes a signed finite locator.
Real Android/framework/Keystore/JNI Connect then fails with `Rejected` at30.119s,
without NATIVE_READY. Its isolated authority records one restricted challenge and
one newly issued certificate, but delivery/validation/cache completion is unproved.
No budget extension or unchanged retry. DNS/verified HTTPS/egress and runtime
negatives/ACK checks remain NOT_RUN. Both own AVDs, authority and carrier workers
are stopped; no temporary secret file was made. Test-only118/x86_64 APK is built,
installed only in the disposable AVD, never distributed; product source unchanged.
**Superseded next (see corrected deadline finding above):** localize the issued-bundle→READY boundary with better stage evidence,
not a rollout, locator import, new discovery or another identical Connect attempt.
[Actual attempt, failures and cleanup limits](releases/2026-11-06-beta113-field16-bootstrap.md#actual-androidtelemost-attempt-6-november).

**6 November18:23UTC onward — cold provisioning: G4 resources released, vault access pending.**
One authorized read-only snapshot finds the existing G4 main container exited0 at
18:14:35UTC/Pid0 and both route helpers stopped (gateway1, origin0). Its waiter exit
file contains0; the terminal receipt is absent at the inspected local path, so this
branch does not declare G4 PASS or take over its cleanup. No second poll is performed.
The owner now authorizes one specific local OAuth vault entry for this isolated test
and newly created test rooms only. However, KeePassXC is not running and has no DBus
owner; no unlocked KeePassXC session is available. The documented CLI route requires
normal owner authentication in the protected local dialog, not credentials in chat.
No vault entry/password/token was read, and no alternative secret source was queried.
Android/Telemost remains **NOT_RUN**: no AVD, build, room, locator or temporary secret
copy was created. Source remains cf419a1; no release/deployment or product change.
**Next:** normal local vault authentication, then the already authorized bounded test;
no repeated entry-use authorization, locator import or discovery implementation.
[Access boundary and retained readback](releases/2026-11-06-beta113-field16-bootstrap.md#authorized-vault-access-follow-up-6-november).

**6 November17:55UTC — Android/Telemost cold provisioning runtime NOT_RUN.**
Read-only preflight of unchanged cf419a1 finds the three existing G4 containers still
running and using resources. Under the explicit no-competing-AVD/build constraint,
no emulator, qualification APK or Telemost room is started. KVM/NVIDIA are available,
but that does not override the resource gate; no physical phone is authorized here.
The current environment has no Telemost OAuth token; no separately authorized test
credential source was supplied, and production/private credentials were not read.
Connect latency, node, real DNS/HTTPS/egress, Android negatives and ACK runtime results
are NOT_RUN, not inherited from core PASS. The finite APK-asset locator (at most4h)
still has no independent refresh after missed rotation. **Next:** after G4 releases
its resources and an authorized test OAuth source is identified, execute the single
Android/real-Telemost vertical with a fresh independently prepositioned locator.
[Resource receipt, exact scope and proposed locator import](releases/2026-11-06-beta113-field16-bootstrap.md#androidtelemost-runtime-eligibility-6-november1755utc).

**6 November — bounded cold provisioning source candidate, not delivered.**
Separate `feature/android-cold-provisioning-20261106`, based on41b4e6e: a registered
uncached client uses a prepositioned root-delegated, issuer-signed finite locator,
existing packet carrier and device proof, then unchanged readiness validation,
encrypted vault, AutomaticVpnOwner/RestrictedTunnelEngine and native MESH.
The isolated dual-block full path passes TCP/DNS/verified HTTPS and closed-owner
late-response checks; real authority denies revoked/unactivated/expired-subscription
fixtures. Android OS/JNI boundaries are fixtures, not Android/Telemost field acceptance.
Locator expiry is at most4h and may be shorter; missing a locator rotation requires
independent delivery, not a fetch from the blocked API. No locator ships by default.
Trigger/cleanup diagnostic causes are separate; terminal policy remains unchanged.
Final scoped checks:95 JVM,97 Python (4 native-artifact cases skipped), four native
packages under race;38.52s integration includes real20s of modeled direct-path stalls,
late identity replacement and in-flight link loss. These are not additive/full-CI totals.
The unchanged30s Connect budget now excludes a synchronous unavailable-path ACK:
the existing receipt store retains ACK_PENDING, never a fabricated ACK_RECEIVED.
Arm64 JNI candidate builds from6840193; no APK/install. **Next:** qualify this
candidate on real Android with actual Telemost provisioning before controlled delivery;
the phone's whitelist/provider reachability remains unknown. No AVD, production, APK,
main-worktree or G4 changes. [Contract/evidence](releases/2026-11-06-beta113-field16-bootstrap.md#bounded-provisioning-candidate).

**6 November — beta113 cold bootstrap gap reproduced; not a field-network diagnosis.**
With HTTPS8443 and direct RNS4242 both unavailable, an activated device without usable
readiness or an already healthy VPN has no cold path to verified pre-Telemost materials.
Service-only chat also requires that cache; it is not an independent provisioning route.
A valid cache can feed a fresh Connect, not first activation or unavailable-refresh recovery.
Seven short exact113 JVM entrypoint cases PASS with blocked synthetic I/O; three existing
native crypto/binding cases PASS separately. This is not Android/Telemost traffic acceptance.
The first fixture failure is retained. No product code, APK, AVD, production or G4 change.
Export16/source conclusions at148e212 stand: fetch failure, owner interruption and cleanup
are distinct; neither operator blocking nor the exact owner callback is established.
**Next proposed implementation:** bounded service-only provisioning for an activated,
uncached device over the existing carrier/trust, without the current cache dependency.
It is not implemented or assumed reachable on this phone. Activation remains separate.
[Missing transition, reproduction and diagnostic metadata proposal](releases/2026-11-06-beta113-field16-bootstrap.md#dual-direct-path-failure).
The live-renewal watch and frozen G4 below retain their separate scope/status.

**6 November14:22UTC: authorized live MESH repair verified on both NL.**
Common ordinary renewal COMMITTED; fresh leaf/CRL expire17:58:13UTC, CRL floor27274.
Both original recovery-start PIDs remain active/NRestarts0. Existing service identity
FLEET_MESH_PROBE_1 fetched node-bound HTTPS readiness, passed native validation and
real Telemost bootstrap/Family TLS/mux, four verified HTTPS and three DNS checks per
NL, including each correct egress. NL2's first probe FAIL is preserved: that old probe
hardcodes NL1's egress; the retained NL2-specific binary passes separately, not a
relabelled result. Temporary publisher configurations and own SSH forwards are retired.
Scheduled-service interlock ea1bfc9 is installed;14:06/14:21 jobs return NOOP with
both existing timers restored and their definitions unchanged. AWG/TCP PIDs on all
three nodes are unchanged. Next operational check: the next due automatic common
renewal, before17:58:13UTC; a NOOP does not prove that renewal has already happened.
[Final evidence and rollback](releases/2026-11-06-vpn-health.md#verified-recovery-and-live-traffic).
This is a narrow live repair, not online-package/G4 acceptance, Android rollout or B.
Earlier preparation/checkpoint entries below retain their original historical state.

**6 November14:00UTC: live fleet renewal COMMITTED; both NL MESH and HTTP active.**
The first repair renewal safely aborted on expired seed directories (DIRECTORY_INVALID,
readers stopped). Existing bounded publisher recovery staged real Telemost rooms and
published fresh directories on both nodes; the next ordinary pinned-controller operation
committed, after strict signatures/three-node readback and authorized normal starts.
No online runtime package was installed. Final stability/readiness checks remain pending.
A thin scheduled-service interlock is qualified: pause only the existing directory timer,
wait for its active writer to finish, invoke the unchanged controller, restore prior timer
state even on failure. This prevents its demonstrated shared-lock race; no new writer/timer,
schedule interval or authorization policy. Installation/readback of the interlock is next.

**6 November: authorized live MESH recovery, source guard qualified; not restored yet.**
Both NL leaf/CRL expired5 November11:44:40UTC. RU's first acquisition failed with
OPERATION_BUSY at10:15:12UTC; its durable RECOVERY_REQUIRED record has no acquired/
quiesced roles or COMMIT. All three node owners/staging are absent; canonical material
matches the recorded predecessor, but the live RU database digest has since changed.
Explicit unacquired-abort protection passes128 scoped tests, including expiry then
ordinary fleet renewal, lost-response/owner refusal and metadata crash replay. It does
not restore DB/profiles, start readers or deploy online renewal. Next: guarded dry-run,
abort of only this empty operation and existing fleet-controller renewal/readback.
[Diagnosis/recovery](releases/2026-11-06-vpn-health.md). Frozen G4 remains untouched.

**6 November13:27UTC — live health warning:** AWG/TCP active on all nodes, but BOTH
NL MESH bootstrap services FAILED (exit1/NRestarts6; last exits5 November11:47UTC).
Cause unknown; no repair/restart. RU CPU initially70–72%, follow-up4–31%; disk71%/8.4GiB.
AWG recent peers0/4/0; TCP443 sockets0/91/5, not unique clients.
[Read-only evidence](releases/2026-11-06-vpn-health.md). Isolated G4 untouched.

**5 November11:29UTC — read-only VPN check:** all AWG/TCP and both NL bootstrap
active; CPU RU9–25%, AMS1 19–21%, AMS2 16–18%. RU disk70%/8.5GiB free.
Recent AWG peers1/5/1, TCP443/8446 sockets0; not unique users. RU steal briefly11%.
[Measurements and limits](releases/2026-11-05-vpn-health.md). No runtime changes.

**4 November22:54UTC — read-only VPN snapshot:** all AWG/TCP and both NL bootstrap
services active. CPU RU13–23%, AMS1 8–34%, AMS2 8–17%; RU disk70%/8.5GiB free.
Recent AWG peers0/2/0, AMS1 TCP443 sockets145, not unique clients. No runtime changes.
[Measurements and limits](releases/2026-11-04-vpn-health.md#2254utc-refresh).

<!-- Android113 MESH incident 20261104 -->
**6 November12:43UTC: existing corrected G4 still RUNNING; G1/G2/G3 PASS retained.**
Read-only inspection confirms the same container started10:42:51UTC, frozen c8eb8b9,
archive5721a5c1 and serving driver0fead52a/PIDs67/74. Both original sockets are open
with fresh TCP/DNS/verified-HTTPS samples, generation0; renewal1 is still due13:13:02UTC.
The exit file is empty and there is no final receipt or final exit code. The unchanged
progress is a waiting phase, not acceptance. Local readback/logs are preserved separately;
no runtime resources, frozen source or artifacts changed. No AVD or competing test started.

**Retained6 November12:16UTC: G3 remaining cases PASS on API27/API35.**
Legacy HTTP/cache/owner/native and late completion after closed owner are now proven
on both APIs, with separate new Connect, real clocks and NVIDIA/KVM. Late final:
API27/af39bc7 333.565s; API35/212b811 350.367s. Original failures remain unchanged;
the older API35 VPN-control timeout is not declared fixed. All own Android AVDs and
stands are stopped. G1/G2 scoped PASS retained; frozen c8eb8b9 G4 is still before
renewal1, due13:13:02UTC, on unchanged bfff97d archive5721a5c1/driver0fead52a.
**A NOT_ACCEPTED, B NOT_STARTED.** One next: collect the existing full G4 final
receipt/exit, without duplicate/rebuild. [Gate matrix](releases/2026-11-05-mesh-online-renewal.md).
No production, phone, release/catalog/timer or paid changes. Older deltas are history.

**6 November12:05UTC: corrected late API27 PASS333.565s; API35 runtime NOT_RUN.**
The repaired HTTPS adapters stay at≤6 sampled descriptors. API35 instead fails
before APK installation: system phone service unavailable within the unchanged60s
preflight. Its QEMU log and deterministic namespace check expose unavailable IPv6
modem-loopback resolution; this warning also existed in older successful boots.
An owned-endpoint link-local-only correction and fail-closed preflight pass33 scoped
guards; actual API35 still pending. No new package, changed G4, accepted A or B.

**Late-fixture root cause localized:** corrected-underlay API27 fails at300.139s
before delivery because both synthetic HTTPS adapters exhaust1024 file descriptors.
The frozen adapter reproduces two retained sockets/thread after origin EOF without
client FIN. A test-only cleanup repair passes both EOF and half-close guards; paired
Android qualification on it is still pending. API35 was not started on this adapter;
both prepared stands are stopped. Original API35 VPN timeout remains separately open.
G4's copied adapter/source/processes remain unchanged. A open; B not started.

**6 November11:41UTC: legacy Android API27/API35 PASS, A still open.** Both actual
HTTP/cache/owner/native cases retain the old bound, refuse an unauthenticated
successor commit, close normally and allow only a separate explicit new Connect.
The synthetic negative peer has its own overlay/digest, not the production gateway.
Both legacy NVIDIA/KVM AVDs and owned stands are stopped. Corrected late API27 is
running alone on GPU; API35 follows. Original API35 VPN-control timeout remains FAIL.
G4 c8eb8b9 is still waiting within its real-time budget; no restart, A or B acceptance.
[Exact receipts](releases/2026-11-06-mesh-android-remaining-evidence.json).
Older dated entries below are historical, not additional active next steps.

**Late-test coordination correction:** only its fixture-state HTTPS moves to the
existing underlay helper; actual readiness and owner/native checks stay unchanged.
The original API35 data-path timeout stays FAIL/unexplained, not silently retried
or declared fixed. Corrected paired late receipts are pending; legacy runtime is
running sequentially on NVIDIA/KVM. G4's frozen c8eb8b9 run remains independent.

**6 November11:13UTC: G3 late API27 PASS, API35 FAIL; A remains open.** API27 proves
HTTP/cache completion after owner close cannot resurrect the native lease; explicit
new Connect succeeds separately. API35 stops before late delivery on a10s HTTPS
fixture-control connect timeout, with still-valid materials; product/harness cause
not yet localized. Both GPU AVDs/Android stands are stopped, failure retained.
Legacy compatibility peer preflight passes on both NL with unchanged old native
bounds and no commit; actual Android legacy NOT_RUN. [Exact evidence](releases/2026-11-06-mesh-android-remaining-evidence.json).
G1/G2 scoped PASS; c8eb8b9 G4 still RUNNING on unchanged bfff97d package. No B.

**6 November10:43UTC: corrected G4 RUNNING, not accepted.** Frozen c8eb8b9 uses the
unchanged bfff97d package/driver; first renewal due13:13:02UTC. Expiry PASS is retained,
not repeated. Existing Android runner gains a closed-owner late-completion scenario;
its API27 APK compiles, actual paired runtime still pending. No legacy PASS, A or B.

**6 November: finished-run readback, not A acceptance.** Frozen expiry52c91f5
finished03:51:34UTC, exit0: two actual post-expiry resumes return precisely
`FAIL_CLOSED/ONLINE_RUNTIME_RECEIPT/automatic_retry=false`, unchanged COMMIT,
canonical profiles and processes. Original first-run FAIL remains unchanged.
Full path37ffc2c finished07:13:57UTC, exit1 after27092.71s: both NL completed two
renewals and23395 checked samples each across real leaf/CRL/lease bounds on the
original sessions/sockets. Emergency recovery completed, but the next CRL assertion
read the stale fixture instead of the canonical profile. Read-only postmortem finds
the revoked serial in both canonical CRLs, floor6>4; final fresh traffic/replay was
not reached. [Exact results](releases/2026-11-06-mesh-frozen-run-results.json).
Repair only the test's profile lookup, validate it, then qualify the unfinished
combined path on unchanged bfff97d package5721a5c1. G3 legacy/late still NOT_RUN;
A not accepted, B not started. Both old runs/helpers stopped; no AVD running.
Older NEXT entries below are historical; one active next is to complete remaining A.

**6 November00:06UTC checkpoint: current isolated G1 regression PASS; A open.**
The bfff97d root/package/process selection finishes68 PASS/5 SKIP; the five omitted
snapshot cases then pass separately5/0 using its reproducible frozen capsule. The
missing-RNS/missing-artifact setup failure remains in the log, not an accepted run.
No overlapping-suite sum or full-CI claim. [Current artifacts/results](releases/2026-11-05-mesh-seed-continuous-evidence.json).
G4 bfff97d/37ffc2c is waiting for its first renewal02:12:33UTC; the guarded current
G2 expiry repeat bfff97d/52c91f5 waits until03:51:29UTC. Neither is PASS yet. G3
legacy/too-late remains; no accepted A checkpoint or B. All AVDs are off, heavy
foreground regressions finished; only isolated low-load wall-clock stands remain.

**23:46UTC real successor-expiry test FAIL, safely blocked; G2 not closed.** After
four real hours and controller death after COMMIT, the frozen d968ddd package returns
`FAIL_CLOSED/ONLINE_RUNTIME_RECEIPT` before resuming the journal. Expired loaded
credentials cause the serving reader to close without a valid receipt. The saved
COMMIT/plan/fence1 remain unchanged, with no publication. The old assertion stopped
before the second attempt; cleanup completed. [Exact evidence](releases/2026-11-05-mesh-expiry-evidence.json).
The harness now permits only this precisely guarded stable-block outcome and verifies
unchanged canonical profiles/processes/journal plus actual expiry on both attempts.
Its fresh four-hour run is still required, not PASS. Corrected G4 continues separately
on bfff97d/37ffc2c; G3 legacy/late and A acceptance remain open, B not started.

**bfff97d candidate preflight and affected native race PASS; A still open.** Its
separate frozen archive/driver proves both NL Family TLS/mux/TCP/DNS/verified HTTPS
and actual-reader cleanup; production rejects qualification flags. Bootstrap,
wholedevice, qualification and release-command `-race -count=3` pass with0 SKIP,
including the source-pinned Python publication artifact. [Exact candidate receipt](releases/2026-11-05-mesh-seed-continuous-evidence.json).
The8h harness also waits for sampled native generation, not only its earlier COMMIT
callback;9 guards pass. The short initial long-run attempt is stopped before renewal
to freeze this observation fix; its log is retained. Resume the same runtime package
with the fixed frozen harness. No G4/A acceptance or B; no emulator is running.

**23:36UTC seed-lifecycle source candidate; not G4 acceptance.** The existing overlap
loop now supports explicit bounded repeated rotation, default off. The separate driver
opts in to4h seeds/2h cadence; production command/defaults/TTL remain unchanged and no
test provider is added to the release. Bootstrap `-race -count=3` with disposable
ProductStore profiles and the isolated Python publication artifact passes without
skips; eight budget guards pass. A new frozen package/preflight/full wall-clock path
is still required. The previous failed stand receipt is preserved; A/B remain gated.

**23:28UTC G4 stand budget FAIL; no accepted A checkpoint.** The frozen fd7562c
full-core run completes its first normal renewal on both NL with original TLS/mux/TCP
and checked traffic, but its next eligibility is61s after the actual client security
deadline. SeedManager currently rotates only once:4h lifetime +1h rotation supports5h,
not the requested8h. Both invalid long stands were interrupted normally; processes
were waited and reader sockets removed. No actual second renewal or expiry is claimed.
[Exact reproduction](releases/2026-11-05-mesh-seed-budget-evidence.json). Seven targeted
budget guards pass; these prevent another invalid run, not fix the lifetime contract.
The independent5h successor-expiry G2 run remains active; all Android emulators are off.
G3 legacy/too-late cases remain; B is not started. Next: genuine long-lived seed and
normal directory publication lifecycle, then requalify the complete G4 combination.

**23:00UTC partial-publication new Connect PASS on API27/API35; A remains open.**
The explicit new owners connect using unchanged predecessor security material while NL2
publication is missing; native mux/verified HTTPS work, then the same COMMIT resumes.
[Exact receipt](releases/2026-11-05-mesh-android-partial-connect-evidence.json):61s/71s,
wrapper exit0, unchanged native bytes, real aligned clocks and normal cleanup. The
earlier clock/test-comparison failures are retained, not relabelled. All Android AVDs
and stands are stopped. Final targeted runner/receipt selection29 PASS/0 SKIP; no full-CI
claim. Remaining G3: legacy peer and too-late delivery. G2 expiry/G4 real-time stands
continue; there is still no accepted A checkpoint and no split-tunneling implementation.

**22:43UTC owner-race runtime PASS on both APIs.** API35 also completes363s through
the actual HTTP/cache/closed-owner/new-explicit-owner/native path; its fixed runner
exits0 and cleanup completes. [Exact paired receipt](releases/2026-11-05-mesh-android-owner-evidence.json).
Source038b66a is pushed/remote-verified. New-Connect-during-partial qualification is
in progress: one API27 AVD was7s behind host UTC and correctly rejected a not-yet-valid
certificate; API35 connected but the test incorrectly compared fresh challenge bytes.
Both failures remain evidence, not PASS. No clock changes or validation bypass; A/B
remain unaccepted/not started, and the independent G2/G4 real-time jobs continue.

**22:25UTC API27 real late-completion/owner race exercised; A remains open.** The normal
owner fetch reaches the real encrypted-cache import monitor after verified HTTP. While
that import is delayed, explicit Disconnect completes and a new explicit Connect takes
a different owner; the validated successor then reaches that new native session and
verified mux traffic succeeds. This is delayed application completion, not an HTTP
socket surviving Disconnect. Instrumentation PASS339s; the runner exited1 only because
its final assertion omitted the new narrow PASS enum. That assertion is fixed with
targeted21 PASS; the original exit/log remain unmodified. API35 runs sequentially on
NVIDIA/KVM. No A acceptance, split tunneling, production or publication change.

**22:00UTC API27 and API35 positive delivery PASS, full A still open.** Sequential
NVIDIA/KVM runs650s and669s now both prove HTTP/cache → normal service owner → renewed
native credentials after real partial publication/cooldown, without reconnect. Both
AVDs and their server stands are stopped with normal cleanup. Exact identities/bounds:
[sanitized receipt](releases/2026-11-05-mesh-android-gpu-evidence.json). Scenario checkpoint
2e3d180 is pushed/remote-verified, not accepted A. Remaining G3 late/closed-owner/legacy/
new-connect cases and genuine G2 expiry/full G4 stay open; B NOT_STARTED. Follow-up
snapshot-route guard5 PASS and GPU/receipt unit selection16 PASS are separate scopes,
not full CI or additive totals with older suites. No production/phone/publication.

**21:40UTC new API27 positive delivery evidence, not full G3/A acceptance.** A single
NVIDIA/KVM AVD completed650s of actual HTTP readiness, encrypted cache, ConnectionService,
partial NL2 publication, duplicate refresh, real310s cooldown, normal same-COMMIT resume
and successor commit in the original native/VPN owner, then normal cleanup. The earlier
activation failure was correct rejection of an already-consumed invitation on a fresh AVD.
New stands use fresh synthetic invitations and the existing scheduled directory publisher
over SSH/read-only snapshots, rather than the stale RU fixture directory. Two targeted
root/package tests PASS/zero skips, including this publisher and pre-publication RPC loss.
API35 now runs the same path sequentially on GPU. Old-peer/late-delivery/stale-owner and
remaining G2/G4 gates are still open; B NOT_STARTED. No production/phone/release changes.

**21:14UTC thermal interruption and GPU correction — G3 remains open.** Four remaining
software-rendered AVDs were explicitly stopped after the owner's overheating report;
the two partial-scenario AVDs had already failed and exited, not passed or been interrupted.
Their earlier service preflights do not prove successor delivery. The runner now requires
one API per invocation, a shared exclusive emulator lock, `-gpu host`, NVIDIA PRIME and
`-accel on`; actual guest GLES must identify NVIDIA or qualification stops. A fresh API27
boot verified GTX1650Ti rendering and exact APK/native bytes, then failed synthetic
activation (`FriendsAccessAndroid.Denied`) and cleaned up. No emulator remains running.
Targeted guard tests:11 PASS; this is neither G3 nor A acceptance. Existing non-Android
long-runtime evidence remains separate; B is not started. Production/phone unchanged.

**21:00UTC actual Android service preflight on both APIs, still not G3 PASS.** API27
and API35 complete HTTP/cache, normal ConnectionService, borrowed native session and
verified HTTPS through VPN. API35 now runs inside a no-egress network namespace with
an actual synthetic public-IP origin; emulator Wi-Fi must not rely on an HTTP proxy.
Test-only domain CA resources cannot enter release tasks. Both await the real22:55:56UTC
successor. Frozenfd7562c full-core run uses test checkpoint e144e81, first due23:11:57UTC.
Affected native race count3 and artifact-enabled bootstrap PASS/zero skips; full A/B
gates remain open. No production or owner-phone changes.

**20:43UTC routed preflight PASS, not A acceptance.** Frozenfd7562c package846818ad…
and separate driver180f386f… pass real public-IP TCP/verified HTTPS, DNS and original
mux traffic on both NL (21 samples each), with serving-process reader custody intact.
The new eight-hour harness additionally retains actual lease receipts, two renewals,
crypto-bound crossing and linked emergency on the same sessions. Its full run is pending.
API27/API35 service qualification remains incomplete; exact native/load and underlay
failures are retained separately. Older d968ddd long/expiry jobs continue. B stays gated.

**20:24UTC actual G3 service-path blocker reproduced, A not accepted.** API35 reaches
ConnectionService/MESH, but HTTPS through its active VPN fails; a fresh API27 reproduces
the reset with exact installed native bytes. The local driver unintentionally enabled
ServicesOnly when adding test chat origins. A same-namespace API alias is also correctly
forbidden as a local destination. The qualification-only fix retains normal internet
forwarding policy and adds an external-to-gateway origin on an internal, no-egress test
network. It does not weaken destination/trust checks or change the production entrypoint.
The d968ddd long/expiry runs remain evidence of that older driver, not acceptance of this
pending full path. B remains NOT_STARTED; no production/phone/publication changes.

**G2 successor-expiry run active:** packaged d968ddd controller was killed after the
durable COMMIT. `expiry-d968ddd-long/successor-expiry/progress.json` records the unchanged
decision/plan and real successor bounds; expiry is due23:46:04UTC. No result yet.

**19:39UTC Android runtime checkpoint, not G3 PASS:** both fresh disposable API27/API35
AVDs have completed verified HTTP readiness, actual encrypted-cache writes and native
VPN owner connection/borrowed mux echo. They are waiting for the server's real due time
(21:57:20UTC), not using a changed clock. The d968ddd long core run remains active.
Frozen d968ddd package/core/process/release-payload selection:67 PASS/0 SKIP,969.70s.
No accepted A checkpoint or split tunneling implementation yet; production unchanged.

**Long core run started, not accepted:** frozen d968ddd/archive849232db… and separate
drivercaeccf70… run in the network-none disposable stand. At19:06UTC both original
TLS/mux streams had431 successful TCP/DNS/verified-HTTPS samples; no restart or renewal
had occurred yet. First due21:28:53UTC, expected crypto-bound crossing on6 November.
Mandatory artifact-enabled bootstrap plus wholedevice/qualification/command `-race`
count3 PASS, zero skips. G3 HTTP/cache/owner remains unexecuted; B remains gated.

**Frozen G2 fix5043d72 qualified for the exercised process/RPC scope.** Selected
root/package/core/API regression347 PASS/1 optional skip,1059.78s; the omitted native
compatibility gate was separately1 PASS on the same frozen source. No full-CI claim.
G1 actual revoke/recovery repeats PASS; the dead-receipt defect now reaches approved
recovery instead of false COMMITTED. Additional wall-clock predecessor expiry refuses
journal/owner writes (61.15s). Successor-expiry/full G2, G3 and complete G4 remain open.
The bounded long harness will retain two new renewals and cross actual old leaf/CRL
bounds without clock changes; its short preflight is not long-runtime acceptance.

**G3 transport preparation, not Android acceptance.** The existing whole-device runtime
now accepts explicit packet connectors while retaining bootstrap admission, Family TLS,
mux, owner cleanup and credential maintenance. Normal Android builds still select Telemost;
only a separately labelled `fc_local_core` x86_64 qualification build uses the loopback
relay through the existing protected underlay. Real shared-runtime traffic and denied
protection checks pass; release payload checks reject this provider/tag/artifact.
Actual Android HTTP/encrypted-cache/owner delivery and G4 are still NOT_RUN; B not started.

**G2 stale-process receipt defect found and fixed in source; qualification continuing.**
Frozen9369e65 incorrectly completed online renewal when a gateway was killed/replaced
after publication but its old valid RPC receipt was returned. New pre-delivery confirmation
reads the actual serving process again; replacement now requires emergency approval.
Parallel cleanup keeps eight RPC rounds/SSH120/1395s+lateness; budget is rechecked before
journal writes. Real handoff controller deaths, unavailable NL, publisher contention and
paused stale RPC requester checks pass on the earlier artifact. Full matrix/expiry,
Android G3 and long G4 remain open. B stays NOT_STARTED; no accepted A checkpoint.

**G1 revoke continuation (isolated core; A still incomplete).** Both NL now pass actual
Family admission before revoke and deny the same unexpired credentials after packaged
approval-gated recovery. Revoke after COMMIT and another after approval preserve the
original decision, invalidate stale approval, require fresh approval, retain revocations/
floors and reconcile lost start response without another start. The surviving identity
obtains normal HTTP readiness and new TLS/TCP/DNS/verified HTTPS. Local operator revoke
uses the existing Access DB transaction, not test SQL or a second authorization service.
Frozen9369e65 G1 PASS (isolated core); selected138 PASS/0 SKIP,494.24s, not full CI.
Archive7065f8bf…/separate driverdc104ed6…; source pushed and remote verified.
G2 remainder/G3/G4 remain open,
and B is NOT_STARTED. No production or handset change. [Evidence and limits](releases/2026-11-05-mesh-online-renewal.md#g1-revoke-continuation).

**Isolated core runtime continuation (same incident; A not accepted).**
The positive packet-provider stand now creates real seeds and carries Family TLS/mux
traffic on both NL beyond the old15s boundary: original/new TCP, DNS and verified HTTPS.
It uses frozen packaged controller/node/API/HTTP plus a separately identified driver
sharing the production runtime; no Telemost/live-production or systemd acceptance claim.
Real gateway replacement after COMMIT reaches approval-gated emergency recovery and
new sessions. This exposed a lost-start-response bug: emergency fencing stopped the
already-started reader despite its durable intent. The fix preserves uncertain-start
reconciliation; an inactive attempted start still blocks, with no second start.
Full revoke G1, remaining process/race G2, Android HTTP/cache/native G3 and two-renewal
wall-clock G4 are still incomplete. Phase B remains NOT_STARTED; this is not accepted A.
Next: finish those remaining packaged G1–G4 scenarios, then independently checkpoint A.
Frozen source8eeb9f0/package90b020034527…: selected root/renewal/package/core263 PASS,
zero skips,486.54s; separate packet drivera49c4412efec… is not the production gateway.
Source pushed/remote SHA verified. No Android artifact or accepted A/B checkpoint yet.
[Scope, commands and provenance](releases/2026-11-05-mesh-online-renewal.md#isolated-core-runtime-continuation-froma30966c).

**Earlier online package/process checkpoint (retained evidence; A not accepted).**
Separate default-off controller/node/current API/HTTP/native package is implemented;
accepted maintenance archive unchanged. Real packaged CLI→SSH→three handlers now exercises
COMMIT/replay, six controller SIGKILL boundaries and six lost/corrupt response cases.
Frozen source/package8c876e3 scoped selection114 PASS/0 SKIP; root regression373 PASS/1 optional SKIP, with that
native compatibility check separately1 PASS. These selections overlap; do not sum them.
Artifact-enabled bootstrap/command race/count3 PASS, zero skips; Family/broker race PASS
with7 optional skip events. No full-CI claim. Reader errors and later retry causes are explicit.
The real gateway observer exits at the unchanged15s provider timeout on this isolated proxy;
this fixture has no READY/traffic acceptance. Full G1/G2/G3/G4 remain NOT_RUN/incomplete.
At that checkpoint the next step was the isolated native path and packaged G1–G4. Only after a
separate accepted A checkpoint, execute bounded ANDROID-APP-VPN. Phase B is not started.
Archive SHA256a27502d752eefe05306a189dce6a8630107d5980eca1477ffa9401a9283ffaea;
this is an incomplete-A implementation checkpoint, not the required accepted A checkpoint.
No production/phone/publication changes; APK118/updater113 remain unchanged.
[Contract](../deploy/friends/restricted/maintenance/ONLINE_RUNTIME.md) ·
[Same incident evidence](releases/2026-11-05-mesh-online-renewal.md#online-runtime-package-continuation).

Earlier emergency-only source checkpoint (superseded by package continuation above):
**5 November — G1 emergency implementation checkpoint; G1–G4 qualification IN PROGRESS.**
Product milestone: operational reliability of Android MESH for a small opted-in group,
without routine developer reconnection. Existing roadmap stage5 remains open; subscription
accounting exists, but controlled paid beta/commercial acceptance is not implied.
The same controller can now preserve an online COMMIT, durably archive its staged state,
fence the old owner and request explicit outage approval before a linked quiesced recovery.
Current revoke state wins; the emergency CRL advances beyond the committed floor, never
restores the old DB, and ordinary rollback is forbidden for this continuation.
Scoped Python192 PASS/1 optional SKIP on5ef0193; root/package292 PASS on that exact capsule.
Follow-up handoff/window/start-intent selection25 PASS (overlaps, not an additional total).
Sourceb1d17d3 final targeted root/package118 PASS, zero skips. G1 full runtime, G2 independent
processes and G3 Android HTTP/cache are NOT_RUN. G4 online entrypoint FAIL: the separate
source capsule still has no `--mode online`, and the constructor's qualification guard is
intact. This is an unfinished implementation/qualification gate, not an external approval
blocker or a completed stage. No release preparation/activation is started.
Fresh artifact-enabled bootstrap/command race/count3 PASS with zero skips; Family/native
broker race PASS with27 optional/root/DNS/long-stand skip events. No full-CI claim.
This is not yet independent-process, Android HTTP/cache or final-package runtime acceptance.
Next: finish the SAME incident's G1–G4 qualification. Production constructors remain closed;
no deployment/access, APK118/updater113, timers, cohort, admission or paid baseline changes.
After G1–G4: exact immutable release qualification/delivery preparation, separately authorized
delivery/live/field acceptance, then ANDROID-CONTROLLED-BETA. Paired-DNS/WebSocket remain OPEN.

Previous isolated positive checkpoint (preserved evidence, not a current NEXT):
**5 November12:55UTC — online positive stand PASS; whole requested stage NOT accepted.**
Checkpointa8e1db9 survives999.12s on isolated logical RU/NL/NL2 roles: real Family TLS/mux,
existing gateway/broker handlers and authenticated readiness → DeliveryMaterial → existing
SessionMaintenance. Both original TCP streams transfer883 verified messages through two
leaf/CRL boundaries and lease deadlines; generations0→1→2, no gateway stop/start. Fresh
TCP, isolated DNS and verified HTTPS PASS. This is not three production hosts or mobile RF.
Delta2cbd304 adds strict malformed-marker checks and accurate preserved-error assertions.
Scoped Python229 PASS/5 optional skips; online negatives55 PASS; isolated root/package219
PASS. Mandatory artifact-enabled bootstrap+command race/count3 PASS with zero skips;
all six inherited assertions and the additional receive-cause regression are covered.
The stage remains INCOMPLETE: post-commit revoke safely fences, but machine handoff to
quiesced emergency recovery, full distributed fault/receipt/cache matrix and online API
packaging are still gates. The production constructor rejects the qualification RPC.
No deployment, APK/catalog/timer/admission change;118/default113 unchanged. Paired-DNS
and WebSocket remain independent OPEN incidents. No full-CI or release PASS.
[Current contract, evidence and explicit gaps](releases/2026-11-05-mesh-online-renewal.md).

Previous completed integration stage:
**5 November — bounded renewal integration stage finished; candidate NOT released.**
Fromd4de324, sourcef7d0920 +6dcd727 +b46bff4 connects selected-node Android delivery to the
existing native owner, consistent gateway lease authorization and active broker monitoring.
Real TLS/mux/persistent TCP survives two authenticated generations across old leaf/CRL and
real lease bounds; new TCP, isolated DNS and verified HTTPS PASS. Revoke/cancel/Disconnect/
expiry/partial-commit/dedup/legacy/control-drain and joined-cleanup race checks PASS.
Scoped JVM66 PASS; fresh API27/API35 five JNI/ownership/Keystore checks each PASS; official
local ARM64 build/packet gate PASS. Five affected native packages pass the broad race run;
bootstrap still FAILS the same six baseline diagnostic assertions. No full-CI/release PASS.
No server/phone installation or public artifact/catalog/maintenance/admission change.
118/default113/catalog7 unchanged; paired-DNS/WebSocket and physical gates OPEN.
STOP here. Online single-writer/durable/crash-reconciled two-node publication is described
but NOT executed or automatically authorized. Concurrent documentationd976e51 preserved.
[Dependency map, exact bounds/evidence, failure and next-stage boundary](releases/2026-11-05-mesh-renewal-integration.md).

Previous native primitive checkpoint:
**5 November10:10UTC — authenticated native credential exchange implemented/locally qualified; NOT activated.**
Opt-in Family TLS-bound successor proof preserves one TCP socket across the old leaf/CRL
deadline, including concurrent traffic; isolated DNS checks pass across both boundaries
three times each. Invalid/replayed/late/cancelled exchanges fail closed. Two successive
generations pass20 race repetitions. Five native packages pass under race; six bootstrap
assertions fail identically on baselinebea0421, not a green whole-suite claim.
No gateway/client integration, online publication or deployment yet: current lease and
broker monitors still use their original authorization/bounds. Next connect trusted fresh
credential delivery and generation-consistent authorization/lease monitoring, then qualify
coordinated online publication and identical both-node delivery. Maintenance guards remain.
Owner/opt-in118, default113/catalog7, desktops and last-verified NL70e6c0fc are unchanged;
no live readback this checkpoint. Restricted-network and physical stability acceptance OPEN.
[Protocol, checks, limitations and rollback](releases/2026-11-05-mesh-credential-exchange.md).

Previous field-delivery checkpoint:
**5 November09:07UTC — Android118 opt-in field download HTTPS-verified; default113/catalog7 retained.**
Owner requests testing by users actually on mobile allowlists, not another owner-local
substitute. Existing qualified13e0b37/CI41933207129 APK is published unchanged with its
matching audio source; no rebuild/resign, forced update or stability-fix claim.
Normal-trust HTTPS full bytes of118/source/retained113 and both catalog routes PASS.
Guarded exact-route publication retains invitation, catalogs, prior downloads and protected
product rows; nginx HUP only, no backend/MESH restart. Field installation/allowlist acceptance
remain PENDING. Both gateways retain70e6c0fc. Next engineering gate is authenticated
credential renewal without the measured coordinated outage; preserve hard security deadlines.
[Download, user procedure, hashes and rollback](releases/2026-11-05-android118-field.md).

Earlier09:16UTC renewal boundary checkpoint: real signed leaf/CRL replacement preserves the old
TCP stream but cannot extend its original Family security deadline. A new handshake uses
the authenticated successor; held-request revocation/foreign authority/Family/CRL-floor
negatives preserve lease bounds.120 repeated leaf cases pass under race, no skips;
288 broader native leaf cases pass,20 root and3 optional harness cases skipped explicitly.
Only test scaffolding/tests/docs change, not production or deployment. Next implementation
is authenticated in-session successor transition, then coordinated online publication and
both-node acceptance. No timer/expiry workaround; field acceptance remains open.
[Exact checks and remaining completion gate](releases/2026-11-05-mesh-renewal-continuity.md).

Previous overnight checkpoint:
**5 November00:55UTC — bounded overnight checks complete; maintenance outage confirmed, full acceptance OPEN.**
New30-minute observation initially passes8 DNS/2 HTTPS/2 NL2-egress checks, then phone
reliable exhaustion follows exact-session gateway parent cancellation. Independent
systemd records show RU credential renewal stopping both MESH nodes00:12:56/58UTC,
restarting00:13:25/27 and COMMITTED00:13:37; common70e6c0fc unchanged. New PIDs
1436865/1252999 have NRestarts0: this counter does not exclude intentional stop/start.
Phone automatically reconnects00:14:40 with capture retained, no operator reconnect.
This is not uninterrupted stability and does not explain the earlier117 WebSocket or
118 paired-DNS failure. No policy/expiry bypass, timer pause, APK/public/server change.
Original30-minute gate remains FAIL after session replacement. Subsequent sampled
post-recovery continuity lasts38m37.883s on NL2; across10 rounds80 DNS/20 HTTPS/20 exact-egress
checks pass. Final118/native2/NONE, retained Support ID/capture and probe cleanup verified.
Both active gateways retain the same70e6c0fc binary; no physical NL1/weak-link acceptance.
[Current overnight checks and remaining gates](releases/2026-11-05-mesh-overnight-checks.md).

00:34UTC isolated checkpoint: packet DNS stress, native/media race, explicit paced
256/512/1000kbit loss/retransmission matrix and40ms offline matrix PASS. New paired-DNS
authenticated-loss/concurrent-bulk regression passes20 race repetitions, without changing
production behavior or claiming the handset timeout fixed. Correctly isolated root renewal/
publication suite397 PASS/5 optional skips; earlier harness prerequisite failures retained.
The150ms model and two accepted118 native credential cases also pass:399 executed Python
cases, three historical exact-snapshot skips retained. Final protocol counters include66
unknown_stream, zero dns_unmatched/DNS errors; earlier paired-DNS/WebSocket causes OPEN.
Source/test ff9c602 is pushed/remote-verified. CI Client builds41942402171 fails one Android
invitation UI assertion; Linux/Windows/Windows compatibility pass. phase0 41942402154 fails
fixture/stack setup. No full-CI green or release claim. Public113/catalog7 signature and full
APK hash independently verified; owner118/public/desktops unchanged. Next: authenticated
renewal without this outage, retained DNS/WebSocket diagnosis and both-node physical gates.

Previous118 delivery checkpoint:
**5 November00:06UTC — Android118 owner delivery PASS; traffic gate FAIL, DNS7/8 pass.**
This checkpoint packages234af08's finite signaling-read classes as a new immutable
version118, without changing retries, timeouts, authorization, media wire or server code.
First sourcea03bdec/run41931735646 fails at release contracts, before an ARM64 APK.
Local reproduction identifies stale117/version and diagnostic-file hash expectations;
strict118 pins and Android-only CI selection for that contract are corrected, not bypassed.
Source13e0b37 is pushed/remote-verified. Client builds41933207129 attempt1 and readiness
wire contract pass; phase0/Linux-control fail separately, so no whole-CI green claim.
Downloaded ARM64/source/native/ABI/16K,839 JVM cases, API27/API35 and8 UI samples pass;
the fixed-height CPU-row capture retains its identical117 crop, not a new UI regression.
Synthetic API27 Java-storage117→118 retention passes with disposable keys. Production
Android/carrier/messenger/vector sources are identical between fixturea03bdec and13e0b37.
Existing-key signed118 SHA256b7b0be92 is installed in place with exact byte readback,
same UID/first-install and consented Support ID verification; no uninstall/data reset.
Current USB support is authorized; one normal Connect reaches NL2/native2. Exact-session
server attribution and current118 readiness pass. The20-minute gate stops after26.081s:
7/8 wire DNS pass, one UDP_PAIRED case times out at8011ms; both Android HTTPS cases pass.
No egress round or long-duration PASS. The local harness reports KeyError on that error
record's absent result field, not an app exception; failure is retained, not retried away.
00:06:49 readback retains the same connected session, Support ID and no probe; no
signaling/ICE failure is observed.13 protocol errors remain visible (unknown_stream9,
dns_unmatched4), not attributed as root cause. Public113/catalog7/desktops are unchanged.
Both NL gateways retain common70e6c0fc; no server mutation.117's failed sustained
observation is not retroactively fixed, and118 remains diagnosis rather than a proven fix.
[118 qualification, delivery and remaining gates](releases/2026-11-05-android118-signaling-diagnostics.md).

Previous source-only diagnostic checkpoint:
**4 November23:00UTC — Android117 sustained observation FAIL; typed signaling diagnostics SOURCE ONLY.**
The selected20-minute NL2 observation stops after91.621s, with one successful ordinary-
UID DNS/HTTPS/egress round. First phone failure22:50:46.330UTC is WEBSOCKET READ_ERROR /
SIGNAL_READ, not a preceding ICE failure; gateway reliable expiry and cleanup follow.
Automatic recovery reaches CONNECTED after35.694s without an operator reconnect.
No packet loss, radio change or server mutation was injected. Nearby system network
transitions are correlation only;117 cannot distinguish reset, JSON type/read-limit or
other read errors, and does not identify the failed WebSocket's underlay. Root cause OPEN.
Additive finite error classes now pass native/default-production race and Android JVM
projection/recovery checks; legacy reasons, retry/auth/deadlines and fail-closed behavior
are unchanged. This is diagnostic source, not a stability fix or a new installed build.
Optional owner-diagnostic-tag compilation still fails on pre-existing missing FirstClose;
baseline reproduces it. Friends provenance guard rejects the dirty tree as designed;
no release gate is bypassed. Full qualification/publication remains OPEN.
Read-only23:00UTC checks confirm recovered117/native2/NONE on NL2, retained Support ID,
probe absent, both existing gateway PIDs/NRestarts0 and identical70e6c0fc unchanged.
Owner117/public113/catalog7/desktops unchanged. Next is exact-source qualification of
the additional diagnosis and a controlled repeat, not public rollout or another PLAN task.
[Failed soak, source checks and remaining gates](releases/2026-11-04-mesh-protected-ice-route.md#failed-sustained-observation-and-additive-signaling-diagnosis).

Earlier ordinary-traffic checkpoint (not sustained acceptance):
**4 November22:43UTC — Android117 both-NL traffic/cleanup/reconnect PASS, sustained stability OPEN.**
Read-only Android system history places cellular NETWORK_DISCONNECTED at21:05:48.860UTC,
coincident with116's ACK loss; VPN/Wi-Fi remains present. The old selected candidate's
interface was not recorded, so this is correlated evidence, not complete attribution.
Reproduced code defect: Pion gathers all IPv4 interfaces, including non-default paths,
although socket protection does not select one interface. New protected UDP route lookup
sends no data and restricts host/STUN candidates to that source address; denied/closed/
cancelled protection fails closed. No timeout, retries, auth, wire or server change.
Source5a0f6e0 pushed/remote-verified; exact Client builds41917441995 attempt1 passes.
Downloaded ARM64/source/ABI/16K/licenses, API27/API35,833 JVM cases and8 UI images pass.
Unsigned117 APK07d88bef is50,262,297 bytes. Separate phase0/Linux-control fixture jobs
fail; no whole-CI PASS. Both live nodes still have equal70e6c0fc/NRestarts0 at readback;
current PIDs1293513/1184264 differ from the earlier delivery, not an uptime proof.
Disposable API27 Java-storage116→117 retention passes without product key/phone mutation
by that fixture.
Existing-key signed117 APK a2f63787 is installed over116 with exact byte readback,
same UID/first-install and Support ID, no uninstall/data clear/reenrollment. Renewed
app consent works. Exact117 readiness binds each of two sessions to NL1. Both pass
ordinary-UID64/64 UDP,8 wire DNS cases,2 Android hostname HTTPS and2 exact-egress checks
without session changes. First session retains sampled continuity for5m56s; normal
Disconnect yields gateway cleanup in1.024s, followed by one successful normal reconnect.
NL1 PID1293513/NRestarts0 unchanged; its temporary probes removed.
Nonzero retry/expected late-stream counters are retained, not hidden as zero errors.
Owner-selected NL2 now also passes two ordinary-UID64/64 UDP/DNS/HTTPS/exact-egress
runs,10m14s sampled first-session continuity and normal cleanup1.050s/reconnect.
Exact authenticated session appears on NL2 only; PID1184264/NRestarts0 unchanged.
Last-global-readiness attribution was a local test-helper error: NL2 prewarms both nodes.
Two pre-probe guard failures retained; corrected validation uses exact session/egress
and separately verified current owner/node READY receipts, not the last global fetch.
No application/source/policy change for this harness correction. Probes removed;
owner left CONNECTED on NL2 with the same reconnected session, Support ID retained.
Owner117, public113/catalog7, identical NL70e6c0fc; desktop versions unchanged.
Next stays within this incident: authorized/restorable unrelated-network-loss,
controlled slow/lossy-link and longer stability checks. Both-node ordinary physical
traffic/cleanup/reconnect is complete; no consent/input or network-control bypass.
No public117 rollout or blanket low-speed/long-duration stability PASS.
[Evidence, tests and remaining gates](releases/2026-11-04-mesh-protected-ice-route.md).

Earlier delivery checkpoint:
**4 November21:07UTC — identical MESH/owner116 delivered; physical traffic FAIL.**
Guarded NL2→NL1 delivery completes with the same70e6c0fc executable, independently
verified through running processes: NL1 PID1219052, NL2 PID1150135, zero restarts.
Fresh seeds/canonical contracts pass; node identity/profile bytes and ordinary AWG/TCP/RU
HTTP processes unchanged. Common writer evaluates NOOP and both timers resume; boot
state remains disabled. Node-specific rollback binaries/custody retained.
Sourcea597d2a and qualification880fcb3 pushed/verified. Reproducible builds, production-tag
race,113/115/116 mixed native peers, six paced links and isolated root gates pass;
inherited fixture failures retained. Android116 CI41905046530 attempt1/API27/API35,
downloaded artifact digests, source/ABI/16K/licenses,833 JVM cases and8 reviewed UI
images pass. Existing-key signed APK3ee68c62 is installed115→116 with exact byte
readback, same UID/first-install and no data clear/reenrollment; separate synthetic
API27 storage upgrade passes. Fresh app consent works. First116/NL1 connection is
observed21:05UTC, but64-flow burst returns46 replies and crosses a native session.
Both ends hit pending-DATA RELIABLE_FRAME_TIMEOUT after~20s without ACK progress;
client ICE/peer disconnection precedes it. Normal automatic recovery succeeds in26.292s
after cleanup, same outer connection/gateway PID; this does not make traffic PASS.
Normal disconnect confirmed21:07:51UTC, capture closed, temporary probe absent.
HTTPS readback confirms public113/catalog7 unchanged; desktops unchanged.
Next within this task: isolate/reproduce the ICE/underlay ACK loss before changing
transport behavior, then paired traffic/cleanup/egress on both nodes. Detailed DNS/HTTPS
and NL2 physical checks NOT_RUN. Original media loss remains open; new-session three
unknown_stream counters are retained, not attributed as its cause. No public rollout
or full stability PASS, no retry/deadline/auth weakening.
[Exact delivery, checks and rollback](releases/2026-11-04-unified-mesh-stability.md).

Earlier source checkpoint:
**4 November — idle ACK cleanup source PASS; physical MESH stability still OPEN.**
Local blackhole tests reproduce a dead-idle session retaining Family/broker ownership
on main and both qualified gateway predecessors. Source now expires missing ACKs in an
empty send window using existing20s MaxAge; live quiet ACKs preserve the session.
Replacement waits for real cleanup; no owner eviction, retry increase or wire change.
Six red regressions each become green on main; full five-package race272 PASS/22 optional
skips, repeated targeted180/39/63 PASS, Python45 and JVM419+414/lint PASS. Original
physical media loss and later device_busy attribution are not solved by this result.
No phone/server/signing/version/publication changes. Last owner115 state is OFF at19:39;
public113/catalog7 unchanged. Next only when selected: distinct gateway/exact Android
qualification, then consented paired quiet/loss/reconnect/traffic evidence. No unrelated task.
[Source correction, retained failures and delivery gates](releases/2026-11-04-mesh-idle-ack-cleanup.md).

Earlier physical checkpoint:
**4 November19:39UTC — owner115 manual cleanup PASS; post-reconnect traffic FAIL.**
First NL1 session passes64 distinct UDP flows, DNS/HTTPS and verified egress. Manual
disconnect releases the exact server session in about0.99s before reconnect, with the
same gateway process; new authenticated connection is observed after29.43s. Subsequent
burst returns47/64 across a native-session change, so traffic/stability acceptance fails.
Paired first failures: gateway RELIABLE_RETRY_EXHAUSTED after9.514s ACK/progress stall;
client RELIABLE_FRAME_TIMEOUT after~20s, preceded by subscriber disconnection. Further
automatic recovery ends HELLO_RECEIVE/CLOSED_PIPE; a device_busy bootstrap is retained
without complete ownership attribution. Normal disconnect confirms capture closed;
temporary probe removed. Owner115 is DISCONNECTED. Public113/catalog7 unchanged.
No retry/deadline weakening, new APK or server mutation in this check. Next, only when
selected: reproduce the media/ACK stall and recovery ownership before another correction.
[Paired evidence and exact acceptance boundary](releases/2026-11-04-android115-mesh-cleanup.md#physical115-paired-acceptance--manual-cleanup-pass-traffic-fail).

Earlier installation checkpoint:
**4 November19:21UTC — Android115 signed and installed in place; physical checks OPEN.**
Existing product signer and unchanged payload verified; installed APK bytes match
`ee97f88e5d4d98c00cbee9283b334dbecb8ac1efc1431b795868596114ade061`.
114→115 preserves UID/first-install without uninstall, data clear or reenrollment.
App USB consent renewed and verified19:22UTC; initial state DISCONNECTED/capture closed.
Paired MESH cleanup/reconnect/DNS/HTTPS is now in progress, not accepted. Public113/catalog7
and desktop releases unchanged. [Signed delivery and remaining gates](releases/2026-11-04-android115-mesh-cleanup.md#owner115-offline-signing-and-in-place-delivery--1921utc).

Earlier qualification checkpoint:
**4 November — Android115 qualified; existing-key signing awaits local vault unlock.**
Exact-source CI41880315713 attempt2/API27/API35, downloaded artifact hashes, provenance,
ABI/16K/licenses,831 JVM cases and reviewed RU/EN picker screens pass. Separate disposable
API27 Java-storage114→115 recovery passes; it is not product-signed ARM64 traffic acceptance.
Both gateway runtimes remain unchanged/active at18:37UTC; common writer timers active.
Owner still114, public/invitation/updater113/catalog7 unchanged. No115 APK is signed or
installed at this checkpoint. App USB support is disabled; do not bypass it. Remaining:
local protected signing, in-place install/readback, renewed consent and paired reconnect/
DNS/HTTPS. [Exact qualification and caveats](releases/2026-11-04-android115-mesh-cleanup.md#android115-hosted-and-local-artifact-qualification).

Earlier runtime checkpoint:
**4 November18:07UTC — both gateway cleanup runtimes delivered; Android115 pending CI.**
NL1/NL2 run their independently qualified8769eadf/5bcb32ea binaries with new seeds,
NRestarts0 and unchanged boot-disabled state. Profile bytes, ordinary AWG/TCP PIDs,
RU HTTP and RU config are unchanged. Common writer evaluation NOOP; both timers resumed.
Rollback not used. Normal-TLS public113/catalog7 readback is byte-identical. Owner114
remains installed;115 is not qualified/signed/installed. Next selected gate: successful
Android115 attempt2/artifact/signing/install, then consented physical cleanup/reconnect.
[Exact runtime receipts and rollback](releases/2026-11-04-android115-mesh-cleanup.md#gateway-delivery-and-independent-readback--1807utc).

Earlier source/qualification checkpoints:
**4 November — owner selects Android115 + gateway cleanup qualification/delivery.**
Candidate115 source includes f66b533; exact CI/artifact/signing, canonical gateway
projection/runtime and physical gates are pending, not PASS. Owner114 and public/
invitation/updater113/catalog7 unchanged; no server or phone mutation at this checkpoint.
[Current delivery and rollback gates](releases/2026-11-04-android115-mesh-cleanup.md).
Read-only fleet inventory preserves distinct primary/secondary binary baselines;
the narrow three-file canonical projection passes34 source checks. Builds, runtime
delivery and physical acceptance remain pending; no generic-main gateway replacement.
Test-fixture compatibility correction passes35 checks; retain the earlier compile
failure and qualify fresh committed outputs before delivery.
Both gateway baselines reproduce exactly; each cleanup candidate reproduces twice and
passes5 lifecycle/auth race repetitions. An unchanged secondary broker timing failure
is reproduced on its predecessor and retained. Android115 CI attempt1 fails before
instrumentation; one same-source retry is pending. Nothing installed/signed yet.

**4 November — selected MESH startup/cleanup source correction DONE; delivery OPEN.**
One controlled114 reconnect fails at SEED_ADMISSION/DEADLINE. Exact old-session NL1
readback shows cleanup about10.1s after Disconnect, after reliable exhaustion rather
than prompt RESET; a separate unidentified bootstrap holds challenge until120s.
No service restart or policy mutation is issued. Last phone readback after the failed
bounded check is DISCONNECTED/capture closed, superseding the17:00 connected state.
Local regressions reproduce three lifecycle defects: parent cancellation kills the
client carrier before bounded RESET; a disconnected authenticated waiter retains its
exchange; bootstrap reader teardown independently closes the RESET route too early.
Source fixes preserve active ownership, wire format, admission/security deadlines and
retry limits. The physical logs do not prove every earlier failure has these causes.
New regressions pass10 race repetitions; relevant race results, retained red cases and
two baseline test failures are in the receipt. Full suite is not PASS. No new version,
APK installation, gateway deployment or public publication:
owner114, public/invitation/updater113/catalog7, desktops unchanged. Next delivery gate,
only when selected: exact-source native/gateway qualification, immutable client update
and guarded server delivery, then paired cleanup/reconnect and DNS/HTTPS acceptance.
[Current source correction, checks and rollback](releases/2026-11-04-mesh-startup-cleanup.md).

Earlier bounded acceptance (not current phone state):
**4 November17:00UTC — Android114 owner DNS/HTTPS acceptance PASS; MESH stability OPEN.**
Renewed app USB consent works. Ordinary-UID64 distinct UDP flows return64 valid replies;
all8 A/AAAA/TCP/paired cases and both Android hostname HTTPS checks pass. Hostname and
IPv4-literal HTTPS200 confirm the exact readiness-verified Netherlands/NL1 egress, not NL2.
One native session throughout;17:00:53 CONNECTED/native2/NONE, temporary probe removed.
First burst test is retained as invalid for the64-flow gate: Android reused one closed
port, so only63 queries were sent; corrected test-only socket retention passes64/64.
Two earlier starts fail at HELLO_RECEIVE (~120s). Time-correlated NL1 challenge failures
and a service stop/start are evidence, not a proven per-device root cause. A third start
after the observed generation change succeeds; no server mutation is issued by this check.
Next only when selected: paired bootstrap ownership/cleanup and stable reconnect diagnosis;
do not equate this DNS gate with sustained or low-speed stability. Exact source3d3bf26/CI,
offline signing, installed APK readback and retained-state gates remain accepted. Owner114,
public/invitation/updater113/catalog7 unchanged; no public publication or full phase0 PASS.
[Exact114 gates and rollback](releases/2026-11-04-android114-dns.md).

Retained source-only checkpoint, superseded by114 delivery above:
**4 November — Android113 MESH DNS source fix; live incident still OPEN.** Renewed app
consent works; unchanged113 is CONNECTED on Wi-Fi. Ordinary-UID wire tests isolate intermittent
UDP DNS loss: A times out while AAAA/TCP A work; Android hostname results remain inconsistent.
The pinned packet engine deterministically drops query17 after16 completed requests because
idle UDP flows retain all16 slots for10s. New Android datagram dispatch releases capacity
per completed query, keeping16 in-flight operations, DNS wire semantics and IPv6 containment.
Source cf9d576 pushed/remote-verified. Pinned packet/race regression including64 sequential
flows and paired requests, focused carrier/44 Python checks and local ARM64/16K build PASS.
Predecessor Client builds41857785568 was cancelled by114; not release acceptance.
This is source-only, not a phone fix or stability PASS: NL2 frame exhaustion and earlier
mixed-network startup failure are separate open problems. Public/invitation/owner113/catalog7
unchanged; no APK signing/install, server restart or policy change. Temporary probe removed.
15:28UTC phone remains CONNECTED on the same native session as the wire probe; no post-fix
phone acceptance is possible from this still-old binary.
[Evidence, limitations and next gate](releases/2026-11-04-android113-mesh-reconnect.md).
<!-- /Android113 MESH incident 20261104 -->

<!-- Android113 unified picker 20261104 -->
**4 November — Android113 hybrid picker published; owner112→113 installed in place.**
One Russia/Netherlands/Netherlands2 list in Auto/AWG/TCP/MESH; correct per-node load,
green squares below85%, orange from85%, selected-row tint/checkmark and responsive layout.
Russia/MESH remains visible but explicitly unavailable; no hidden country fallback.
Exact source d2882cd/CI41833086774 attempt2 PASS; attempt1 failed before instrumentation
and remains evidence. JVM418+413, local Python22 and release metadata54 PASS/0 skips;
API27/API35 required runtime cases execute; existing optional skips are recorded separately.
Downloaded native/source/licenses/16K checks and offline existing-key signing PASS.
Public APK/invitation113/catalog7 (optional/minimum1), ARM64/minSDK27; owner signed112→113
retains UID/first-install/selected node and mode, dashboard/live load visible. Installed APK
matches50,273,696 bytes/SHA2566078d061…4edc094. Synthetic upgrade retains identity/journal/outbox;
physical key readback NOT_RUN. Full HTTPS APK/source/catalog/CSP readback PASS; old111 retained.
One nginx reload, no backend restart; protected rows, gateway catalog and desktop releases
unchanged. Owner VPN is OFF after update: manual reconnect required, Android input denied;
no permission bypass. Sustained MESH stability, renewal race and Huawei113 checks remain open.
[Exact hashes, evidence and rollback](releases/2026-11-04-android113-server-picker.md).
<!-- /Android113 unified picker 20261104 -->

**4 November12:21UTC — requested RU disk cleanup complete:** archived host journals
older than14 days removed; ~2.10GiB freed, disk77%→70%, available6.5→8.6GiB.
AWG/TCP/HTTP/host worker active with unchanged PIDs; no restart or version change.
[Scope and irreversible deletion receipt](releases/2026-11-04-ru-disk-cleanup.md).

**4 November12:15UTC — VPN load refresh:** AWG/TCP active on all three nodes;
CPU RU12–31%, AMS1 10–16%, AMS2 7–11% in short samples. Recent AWG peers1/5/1;
AMS1 xray TCP sockets11 then9, not unique users. No changes or end-to-end acceptance.
[Read-only measurements](releases/2026-11-04-vpn-health.md#1215utc-refresh).

**4 November09:10UTC — read-only VPN check:** all three AWG/TCP nodes active;
eight recent peer handshakes, not unique users. RU TLS renewal timed out, but external
TLS currently validates; legacy Docker worker unhealthy, host worker active.
No repair/deployment or end-to-end acceptance. [Snapshot](releases/2026-11-04-vpn-health.md).

**Export26 primary journal correlation — stale bootstrap cache hypothesis strengthened.**
AMS1 stopped20:00:41UTC, started20:01:30, seed ready20:01:32. Client20:07 uses a
pre-restart valid cache and times out at SEED_ADMISSION; no Family-open/auth record
in that window. Packet receipt/old-room identity not proven. No changes by this check.
[Evidence](releases/2026-11-03-krasnodar-diagnostics.md#export26-primary-journal).

<!-- MESH2 canonical installation 20261103 -->
**4 November11:49UTC — owner112 MESH2 traffic proven; sustained stability gate NOT PASSED.**
MESH2 node-scoped HTTPe2ed4ca6/additive migration remain installed; existing accounts,
keys/grants/assignments are preserved. Historical service readback08:56 verifies both MESH
nodes active/boot-disabled, accepted AMS2 binary566cbc96, common writer COMMITTED with
active timers. Later guarded recovery is recorded below; no admission-policy change.
Android source2b7d672 is pushed/remote-verified: selected MESH2 now refreshes its own
readiness scope while retaining primary Auto/chat prewarm.62 Python and414+409 JVM
PASS/0 skips; lint0 errors/56 existing warnings; exact API27/API35 UI4/4 each PASS.
Exact synthetic API27 CI-signed111→112 upgrade retains UID/identity/journal/outbox;
per-node storage/restart/refusal checks PASS. Not handset/ARM64/product READY evidence.
CI41806139859 failed before APK construction in the framing healed-gap test; older
41802908693 is cancelled/superseded. Local5/12 reproduction identifies the test endpoint's
missing idle RTP expiry (production already has it). Test-only correction keeps all
loss/negative checks and retry/time bounds:12 full framing repetitions PASS, exact
14-package race selection686 PASS/48 existing optional skips, one package without tests.
Correctionbe75101 is pushed/remote-verified. Exact CI41808770801 succeeds on Android,
Linux, Windows and Windows compatibility; failed/cancelled runs remain evidence.
Four downloaded artifact ZIPs match GitHub SHA256 and source/run. Unsigned ARM64
beta112/code112 (minSDK27/target35), all12 native libraries/source manifests/licenses,
ELF/ZIP16K alignment and no diagnostic provisioning entrypoint PASS. APK50,251,561bytes,
SHA2562fe1fd25…1bd95e; not a signed/public installer. Exact JVM414+409 PASS/0 skips;
API35 debug/Friends28/19 PASS (25/4 skips), API27 debug/Friends27/18 PASS (26/5 skips).
Picker/language/legacy audio execute; existing opt-in/variant/API skips are retained,
not counted as acceptance. CI screenshots reviewed for both APIs; synthetic CPU data
and distinct Amsterdam rows render, Android8.1 offers Codec2 rather than unsupported Opus.
Operator ACK reader now accepts an explicit node, private device-reference file and
exact reported version code under the existing all-activated policy. Legacy sole-owner
behavior and revocation/expiry/node-binding checks remain; no identity inference or
ACK generation.125 selected Python PASS/0 skips/one separate historical pipeline
deselected, including isolated packaged entrypoint and byte-unchanged DB checks.
At10:24 read-only inventory confirms all-activated: primary14 challenges/fetches/ACKs,
6 READY/8 native rejection; versions111×5/60×8/109×1 are separate aggregates, not a
failure attribution. Secondary had0 requests/ACKs at that historical readback.
At10:45 the exact accepted ARM64 artifact is signed offline with the existing production
key:50,273,640bytes, SHA2564791d811…74776; signature/payload/16K checks PASS. At10:50
ADB installs112 over111 on the authorized Android12/API31 ARM64 phone without uninstall
or data clear. UID, first-install time and subsequently observed support identity match.
This is a controlled owner installation, not public rollout or full stored-data acceptance.
After the user re-enables app USB consent and selects MESH2, normal connection fails at
readiness CHALLENGE/HTTPS_UNDERLAY with HTTP502, before native readiness/Family traffic.
Independent normal-TLS HTTPS probes reproduced502. This failed attempt is not product
PASS. That failed attempt's cleanup readback is DISCONNECTED/VPN capture closed.
Temporary read-only UI helper is removed; MIUI's denied ADB taps were not bypassed.
RU inspection identifies a failed pre-preparation renewal: STALE_NODE_STATE, all three
roles acquired, no commit or candidate artifacts; only the database observation changed.
HTTP is stopped by that transaction, not an APK/native MESH failure. A bounded explicit
unprepared-reconciliation tool passes193 focused checks (one unchanged optional native
toolchain check skipped), then17 reconciliation/entrypoint checks PASS/0 skips.
Corrected exact tool passes live dry run. Guarded metadata reconciliation and the pinned
controller recover the failed operation to ABORTED with the product DB unchanged;
ordinary RU AWG/TCP state/PIDs unchanged. Normal three-node renewal reaches COMMITTED
at11:29:40, no first cause; both timers active. Fresh readback: HTTP active, both MESH
nodes active/boot-disabled. Public catalog111/6 hash and TLS rechecked unchanged11:34.
The first wrapper's import error and recovery CLI's expected75/ABORTED are retained;
neither reconciliation nor recovery was blindly repeated. No database/profile rollback.
Normal scheduled acquisition/quiesce race still needs a root fix, not repeated manual
rebasing. The user's subsequent normal MESH/Amsterdam2 connection succeeds. Read-only
known-device receipts independently confirm node2 ACK_RECEIVED/READY/usable/version112;
primary prewarm also has its own READY and must not be mistaken for the selected exit.
An ordinary-UID probe confirms active VPN, DNS, normal-TLS HTTPS200 and Amsterdam2 egress.
The first probe's UnknownHostException remains a failed sample; its cause is not established.
Controlled disconnect closes VPN capture; reconnect reaches CONNECTED/READY in35.7s and
repeats the full DNS/HTTPS/egress PASS. Temporary probe removed. A subsequent snapshot is
RESTORING/IO_CLOSED/read_error; the same-session gateway trace has RELIABLE_FRAME_TIMEOUT
and cleanup, without a process restart. Automatic recovery establishes Family TLS again
and returns CONNECTED/READY, but a follow-up DNS succeeds while HTTPS fails with IOException.
Final UI state is CONNECTED, not proof of healthy traffic. Root cause is not yet established.
Paired diagnosis, full negative/server-cleanup/low-speed acceptance, acquisition-race correction and qualified
boot activation remain OPEN; this is not a blanket stability or public-rollout PASS.
Public111/catalog6, invitation and Windows/Linux
distribution are unchanged by this task; no112 public APK/catalog/tag publication.
[Evidence, exact CI/artifact acceptance and rollback](releases/2026-11-04-mesh2-android112.md).
<!-- /MESH2 canonical installation 20261103 -->

**3 November export24 server correlation — PARTIAL, cause still OPEN.** Second API36
device matched privately on RU; device/invitation not revoked, no stored online snapshot.
Client18:29–18:34UTC fails before MESH; HTTP unit current activation18:35:46UTC is
later, not proof of outage overlap. SSH follow-up timeouts block historical journal/
request correlation. No production changes. [Readback](releases/2026-11-03-krasnodar-diagnostics.md#export24-server-correlation).

**Earlier preparation checkpoint —3 November18:47UTC (superseded by live state above).**
The live gateway is the accepted canonical/P1 four-member source capsule, not generic main.
The narrow slow-link projection preserves its admission, chat, identity and canonical-profile
code, and retains performance instrumentation with the actual adaptive send window.
Baseline rebuild matches the installed binary; two candidate builds match.20 Python checks
and production-tag native race677 test/subtest PASS/49 optional skips. Broader runs exposed
pre-existing slot-release timing failures and untagged diagnostic-test assumptions, reproduced
on the unchanged baseline; these are not silently waived or reported as all-green.
A fresh, distinct AMS2 identity/delegation is retained privately and signed offline using the
existing control root. AMS2 Python3.12.3/pinned dependencies are staged separately, not active;
AWG/TCP PIDs/restart counts unchanged,0 units created/started. No gateway binary/service,
controller, selector, Android version or catalog switched. Next: exact committed projection
readback, permanent canonical AMS2 provisioning and coordinated writer/live acceptance;
then the immutable Android update. [Evidence](releases/2026-11-03-second-nl-mesh.md#production-gateway-projection-and-ams2-prerequisites).

**19:02UTC follow-up:** exacteb0b5e6 source pushed/remote-verified and reproduced twice;
gateway/renewal artifacts staged on AMS2 with successful native/Python CLI checks, not active.
All four Family TLS pairings with public111 and all four real Pion VP8 pairings PASS;
six paced/asymmetric256/64,512/128,1000/250kbit cases PASS under race detection.
The pinned snapshot launcher now supports explicit Python3.12 for AMS2; default3.14 and
its existing pins remain unchanged.123 selected Python checks PASS;265 isolated-root
Python3.12 profile/snapshot/fleet-recovery cases PASS, plus5 package checks (2 repeated).
Actual AMS2 non-root runtime/pin probes PASS; implicit downgrade rejected. Canonical
profile/forced-route installation, writer cutover and live provider acceptance remain;
no MESH2 service, selector or Android release activated.
Sourceae2737f pushed/remote-verified. Its two exact snapshot packages are identical;
AMS2 verifies their hash, CLI and argument-override rejection. The bootstrap unit is
still absent/inactive; ordinary AWG/TCP remain active with0 restarts.

**3 November Krasnodar supplied trace — two beta111 retry-exhaustion closures confirmed.**
Current Wi-Fi history shows successful MESH sessions followed by RELIABLE_RETRY_EXHAUSTED
at17:16:44/17:19:34UTC, eight retries around9.4s with fresh ACKs; TLS failures follow.
Recovery then hits readiness/bootstrap failures. This supports the selected slow-link
retry defect, not provider attribution or a deployed fix. [Analysis](releases/2026-11-03-krasnodar-diagnostics.md).

**3 November MESH2 production → Android update — current owner-selected order.**
Owner now explicitly requests enabling the second server, then delivering the update.
This supersedes the slow-link-first pause below; include the already checked slow-link
and Android picker changes in that delivery. Read-only RU/AMS2 audit confirms the
canonical renewal writer still targets only AMS1 and AMS2 has no permanent MESH runtime.
The earlier source slice added two pinned, independently validated gateway snapshots and node-scoped
directory synchronization under the existing RU maintenance lock. A failed secondary
cannot overwrite or stop primary directory distribution. Shared CA/CRL, distinct signed
identities, certificate identity/role/revocation, directory freshness/conflict and
source/package boundaries are checked; that earlier slice was read-only/directory-only.
Final maintenance/package/snapshot selection168 PASS,0 skips, including the accepted-source
native compatibility check and gateway certificate revision-floor regressions.
Source checkpointc902e79 and revision-floor correction0775711 pushed/remote-verified;
no deployment. Exact142ee46 Android job126044369850 in CI41672473840 is now PASS,
including API35/API27 and unsigned ARM64 packaging. Downloaded candidate APK/native
source/tree/hash, minSDK27/target35, production tags and all12 library16K alignments PASS.
This is an unsigned111-metadata candidate, not a new release or permission to replace111.
Overall workflow fails on the separate Linux GTK job; release job skipped.
That CI/read-only checkpoint made no production writes/restarts, token transmission,
version/catalog or invitation changes.
Follow-up source now implements one coordinated RU–AMS1–AMS2 leaf/shared-CRL transaction:
explicit pinned membership, separate gateway leaves/keys, three matching commit receipts,
per-node fresh directories before RU resume, rollback/roll-forward and durable fencing.
Pair-only controllers reject opted-in fleet nodes; the old pair mode remains supported.
Checkpoint7d3fac7 pushed/remote-verified. Follow-up also implements offline planned
authority renewal for both signed gateway delegations in that same transaction, with
unchanged issuer/gateway keys, independent sequences, explicit outage approval and shared
CA readback. Explicit append-only registry-overlay recovery now checks both gateways.
Current validation:358 user-space/native/package checks plus one independent-sequence/
approval test PASS;326 isolated root checks PASS, including90 repeated fleet cases.
Sourcee96334d pushed/remote-verified; two exact committed-source renewal packages are
byte-identical and12 canonical root/profile-source checks PASS against that package.
Follow-up implements whole-fleet recovery after authority expiry: one offline-signed
schema4 request binds both historical snapshots, three current node states, shared
checkpoint and distinct gateway successors. Explicit outage approval and explicit
roll-forward remain mandatory; expired approval cannot resume a partial publication.
Final recovery selection60 PASS; the other359 user-space/native/package checks PASS.
Isolated root selection387 PASS, including151 repeated fleet cases:655 distinct cases,
0 skips across the final selections; no production keys/data enter the root container.
Revoked clients/CRL entries, independent delegation sequences, keys and admissions remain
unchanged. Runtime CLI/offline FD signer, nineteen interruption points, secondary RPC
failure/reconnection and malformed/stale approval rejection are covered.
Sourcefcb3116 pushed/remote-verified. Exact-source archives are byte-identical;12 canonical
root/package checks PASS. The package is staged separately on RU/AMS1, not active;
new source validates both canonical installations. RU read-only evaluation returns NOOP
with0 operational writes/restarts; active node/controller configs unchanged, timers/API active.
Remaining: coordinated writer activation with fresh secondary configuration,
permanent AMS2 runtime and live acceptance, then selector and immutable Android>111/catalog>6.
[Current integration and rollout boundary](releases/2026-11-03-second-nl-mesh.md).

**3 November15:59UTC — refreshed read-only health.** Registry60/56 non-revoked/4 revoked;
recent180s AWG peers RU0/AMS1 6/AMS2 1. RU sampled CPU37–71%, follow-up13–54%,
disk78%; legacy Docker worker still unhealthy, host worker active. No deployment,
repair or client acceptance. [Updated snapshot](releases/2026-11-03-vpn-health.md#1559utc-refresh).

**3 November MESH-SLOW-LINK-1 — SOURCE CHECKED, pending combined MESH2 rollout.**
Owner reported repeated MESH disconnects at low speed and initially selected connection
quality before MESH2; the latest order above supersedes that pause. Reproduced premature closure on transient ICE and fixed1s retries
exhausting at9s. Candidate preserves established media through recoverable ICE loss,
uses bounded RTT/backoff and gradual send-window admission; Android recovers correlated
DATA-age/terminal peer failures. Auth/revocation, protocol rejection,20s DATA-age and
fail-closed routing remain enforced. Same serialized256/512/1000kbit/s,600ms RTT model:
baseline fails12/12; candidate completes12/12 byte-exactly, including loss and8/32 windows.
Real local Pion VP8 survives two temporary packet outages and terminates persistent loss
(accelerated ICE timers); not a Telemost/handset claim. Dependency-selected native race
gate669 test/subtest PASS,45 explicit optional skips; Android411+406 JVM PASS,
lint0 errors/56 warnings;66 focused Python PASS. Pinned ARM64 and Linux gateway builds
from55e872c PASS, including16K Android alignment; neither is installed. CI exposed
the prior node-scope integration's omitted standalone JVM sources and stale ACK source
assertion; corrected without removing checks. Standalone JVM187 and wire Python119 PASS.
Exact55e872c Android CI stopped at JVM compilation (API27/API35 NOT_REACHED); unrelated
Linux interaction and phase0 fixture/stack failures remain recorded, not waived.
Follow-uped54f33 is pushed/remote-verified; Readiness wire41668105208 PASS. Android
CI41668105524 then reached the source-reference guard, which still pinned pre-change
gateway/readiness/recovery handlers. Reviewed exact new handler hashes are now pinned;
260 diagnostic/readiness/release contract tests PASS (2 unrelated Windows deselections).
Wall-clock bidirectional qualification exposed a remaining256/64kbit/s failure with
the first eight-block startup allowance. Reducing initial admission to four blocks
passes all six256/512/1000kbit/s cases with quarter-rate return path,600ms RTT and
initial DATA loss, retaining20s age/eight-retry limits.256KiB in each direction is
byte-exact. Beta111-source/current combinations pass both Family TLS and actual local
Pion VP8; these are local separate-layer checks, not handset/provider acceptance.
Final dependency-selected native race672 test/subtest PASS/48 explicit optional skips.
Final source142ee46 is pushed/remote-verified. Fresh ARM64 and Linux gateway builds
PASS; manifest source/tree/hash and16K Android alignment verified. They are not installed.
Exact Client builds41672473840 Android job is now PASS with downloaded artifact checks
recorded above; live gateway qualification remains pending. phase0 still fails before tests in
release-fixture provisioning/failover-stack construction; no gate is waived.
No server/APK deployment or version change. Remaining: exact new-version release CI,
deployed-peer/live shaped-link
acceptance, coordinated client/gateway rollout and immutable Android delivery.
Android111/catalog6, Windows0.2.16/catalog12, Linux public0.2.11/owner0.2.12~l03.2.13
remain unchanged. [Tests, limits and rollout](releases/2026-11-03-mesh-slow-link.md).

**3 November FLEET-BOOTSTRAP-2 — second-node MESH RESUMED; production gates remain open.**
Owner confirms the separately supplied token and asks to finish the integration.
Correction: AMS2 already passed real MESH/reboot rehearsal; its temporary runtime was
retired, not rejected as incapable. Separate publisher input remains in private custody.
Read-only AMS2 check: ordinary AWG/TCP active,0 restarts; permanent MESH service absent.
First integration slice now passes265 backend/HTTP/relay/native checks,2 optional
environment skips: bounded node-targeted readiness, signed distinct gateway binding,
shared identity/entitlement/CRL and node-bound challenge/import acknowledgements. Legacy
requests and primary storage remain compatible. This is SOURCE ONLY, not a working
production second MESH. Fresh permanent runtime, coordinated renewal/revocation/fencing,
and exact new Android delivery remain mandatory gates. Android source now isolates
encrypted readiness/receipt stores, in-flight refresh, denial and replay state per node;
the selected target reaches readiness and native connection setup without changing
the primary wire/storage contract.410 debug+405 Friends JVM and88 packaged/contract
Python tests PASS, lint0 errors/56 warnings; API27/API35 storage prepare/recover PASS.
UI27 passes4/4; UI35 first3/4 (chat-open timeout), then4/4 after force-stop; cause not
established and first failure retained. Only disposable CI APKs installed. The MESH
picker remains country-only until live acceptance; this is not production qualification.
No production writes/restarts, token transmission, new invitations or public artifacts.
Android111/catalog6, Windows0.2.16/catalog12 and Linux public0.2.11 are unchanged;
owner Linux stays0.2.12~l03.2.13. Do not expose an unqualified MESH2 choice.
[Current scope, tests and remaining gates](releases/2026-11-03-second-nl-mesh.md).

**3 November Android node picker — source/runtime checks PASS, NOT DISTRIBUTED.**
Owner defers the isolated Telegram symptom, then reports Android still shows the legacy
assigned-NL choice alongside Amsterdam1/2. The Linux-only correction had not reached
Android. Friends now shows Amsterdam1/Russia/Amsterdam2 for AWG/TCP and Netherlands/
Russia for Auto/MESH; the remembered manual node survives mode changes and recreation.
Initialization does not persist route changes or connect, and active-session routing is
retained.403 debug/398 Friends JVM tests,38 focused Python tests and API27/API35 UI4+4
PASS; lint0 errors/56 warnings. Only disposable CI-signed emulator APKs installed.
Public beta111/catalog6, other platform versions and server policy remain unchanged;
the installed111 is not repaired by this source push. New immutable Android delivery
and physical confirmation remain pending. Per-node telemetry is not changed here.
Telegram is DEFERRED_BY_OWNER, not fixed. Fleet production-canary preparation remains
the main queue's next candidate, not started during this UI correction.
Node2 MESH is an unfinished production integration, not a diagnosed hardware inability:
only AWG/TCP was admitted there; MESH readiness/directory/renewal still use first NL.
[Scope, tests and delivery boundary](releases/2026-11-03-android-node-picker.md).

**3 November13:15UTC — read-only service snapshot.** Registry60 devices/56 non-revoked/4
revoked; recent AWG handshakes3min RU0/AMS1 5/AMS2 1 (peers, not unique people).
AMS1 sampled TX16.008Mbps; no sampled CPU saturation. RU disk78%, legacy Docker
peer-worker unhealthy while host worker active. No changes/restarts/publication;
Android111/catalog6 and desktop versions unchanged. [Snapshot](releases/2026-11-03-vpn-health.md).

**3 November Telegram follow-up — apparently isolated handset issue, cause OPEN.**
Owner reports Telegram works for them and other users in the MESH discussion; only the
affected Huawei is reported failing. This weakens a general MESH incompatibility
hypothesis, but does not establish matched versions/nodes/networks or a device root cause.
Do not start a UDP extension or transport rewrite for this report. First establish the
failed operation and foreground/background behavior, then compare Telegram proxy/version,
active VPN path and Wi-Fi/mobile conditions. Huawei battery restrictions are only a
hypothesis for background-related failure, not a confirmed diagnosis. Preserve app data
and full-tunnel/fail-closed policy. Documentation-only clarification; no handset test,
runtime or server change. Public beta111/catalog6 and rollback paths remain unchanged.

**3 November field follow-up — update/operation reported recovered; Telegram issue OPEN.**
Owner reports «все заработало» after111, but relays that Telegram does not work with
the VPN. This is user-reported recovery, not independently verified handset/version,
identity/voice/MESH acceptance. Whether chats, media or calls fail, selected node/transport,
Telegram proxy and direct-without-VPN behavior are unknown. Read-only source review:
no Telegram-specific application exclusion; ordinary VPN captures both default routes.
MESH explicitly denies non-DNS UDP and IPv6, which is a conditional explanation only;
the reported transport is not established.111 did not alter normal VPN/native transport
source versus110. Next: identify failure scope and mode before any transport/server fix.
No new build, publication, production mutation or diagnostic user-data collection.

**3 November — Android111 PUBLISHED; affected Huawei recovery still OPEN.**
Exact source40e6c6c / Client builds41618639307 attempt2, API27/API35 runtime and
downloaded ARM64/native/UI gates PASS. Existing product signer retained. Signed111
APK50,265,448 bytes, SHA256 `32d5f4f1d050be83dc192ae632cc0603cb4150b3c00df3b594bc22cef9105607`;
minimum Android8.1/API27. The actual signed archive is accepted by the API27 package
parser. Public APK, optional signed Android catalog6 (`min_sdk:27`), both invitation
routes/CSP and corresponding audio source verified over HTTPS. Previous110 bytes
remain unchanged; Windows0.2.16/catalog12, Linux public0.2.11/owner internal.13 unchanged.
One nginx reload, zero backend restarts, invitations/paid mutations/phone actions0;
protected product rows and gateway catalog4 unchanged. Source/API compatibility and
delivery are complete, not real Huawei/ARM64/MESH or product-signed handset-upgrade
acceptance. Next evidence: install111 over the existing app without clearing data,
confirm retained identity and ordinary VPN/voice on the affected Huawei. No automatic
fleet successor or admission expansion. Earlier candidate checkpoints below are history.
[Release/readback/rollback](releases/2026-11-03-android-update-incident.md#beta111-publication-and-readback).

**3 November — beta111 platform/artifact qualification PASS; NOT RELEASED.**
Source40e6c6c is pushed and remote-verified. Client builds41618639307 attempt2 passed
both API35 and27 transport/control/Friends gates and final ARM64 packaging. Downloaded
artifact13225731676 SHA256/provenance/package111/minimum27/target35/ARM64,12 native
libraries,16K alignment and corresponding source/licenses PASS. Runtime matrix:
API35 46 PASS/27 explicit skips; API27 44 PASS/29 skips; zero failures. JVM400 debug/
395 Friends PASS; protected-storage process restart and visual review PASS on both.
Attempt1's API35 automatic-TCP IPv6 timeout is retained, not erased or bypassed;
unchanged-source attempt2 passes the complete gate. Root cause of that intermittent
failure is not established. This is emulator acceptance, not physical Huawei/MESH
or a product-signed old-to-new handset upgrade. Next: existing-key offline APK signing,
increasing signed Android catalog and immutable delivery/public readback. Public110/
sequence5 and desktop versions remain unchanged; no production mutation yet.
[Qualified candidate evidence](releases/2026-11-03-android-update-incident.md#beta111-exact-source-platform-and-artifact-acceptance).

**3 November continuation — beta111 source selected, NOT RELEASED.** Owner authorizes
continuing ANDROID-UPDATE-FIELD-1 through qualification. Reserve new immutable code111/
`0.1.18-beta111`, minimum27/ARM64; public/invitation110 and signed sequence5 stay unchanged.
The earlier code110 compatibility candidate is never publishable. Its Client builds
41610914956 passed API35 runtime/control and reached API27, then was superseded/cancelled
by the111 source push; it is not a complete PASS. Source99c155d is pushed/remote-verified;
exact111 Client builds41613303779 FAILED at two API27 debug test assumptions (unknown
LinkProperties MTU and unavailable InputStream.readAllBytes); API35 passed, API27
Friends/final ARM64 packaging were not reached. The bounded test repair checks the
actual kernel tunnel MTU and streams the unchanged manifest-pinned asset. Both repaired
tests PASS on API27 and35 (four runtime executions);88 focused Python checks PASS.
The repaired exact-source platform run now passes as recorded above; no failure is waived. Local disposable111 build/lint and
395 JVM/88 focused Python checks PASS. API27 UI/update/audio17 PASS/5 explicit skips.
Synthetic CI-signed110→111 in-place upgrade preserves UID/protected identity/journal/
outbox and recovers the interrupted write in a new process; fixture cleanup PASS.
This is not a product-signed ARM64/Huawei upgrade proof.
Read-only strong-import audit of all12 retained110 ARM64 libraries against API27 NDK
exports finds no unresolved symbols; this is reference static evidence, not candidate
runtime acceptance. Broader existing CI failures remain explicit: historical HTTP
fixture packaging expects a newer ingress file;22 Messenger tests omit the runtime
platform/version introduced in107. No unrelated production changes or test bypasses.
Next: exact111 platform CI, candidate artifact/SDK/signer and release gates.
Actual Huawei/ARM64 field recovery stays OPEN.
[Continuation evidence](releases/2026-11-03-android-update-incident.md#beta111-release-continuation).

**3 November — Android update incident OPEN; compatibility source candidate.**
Owner authorizes restoring support for the reported Huawei nova3/likely Android8.1;
actual handset OS/ABI/installed beta remain unverified. Repository history and retained
signed beta65 confirm minimum26, same package and product certificate. Public107
introduced the Friends minimum31. On an actual API27 emulator, the package parser
accepts65 and rejects110: browser installation cannot solve that SDK mismatch.
Existing client restored to a candidate minimum27, not a separate app or downgrade.
Updater checks signed APK-derived `min_sdk` before download, preserves all signature/
hash/version guards and separates verified transfer from APK checking. Android8–9
voice uses existing Codec2 with peer confirmation; Opus recording remains10+.
Local395 JVM/60 Python PASS; lint0 errors,57 warnings. API27 final UI/update/audio
selection17 PASS/5 explicit skips, storage roundtrip and separate-process synthetic
in-place reinstall/recovery PASS. Same candidate API35 selection19 PASS/4 skips.
API27 native transport lifecycle is added to CI alongside35. Source446260e is pushed
and remote SHA verified; Client builds41610914956 was superseded/cancelled, not acceptance.
ARM64/MESH acceptance and a real product-signed old-to-new upgrade are still pending.
Only disposable x86_64 CI-signed candidate APKs built/installed; that initial source
used code110 and was NOT publishable. Current candidate is111 as recorded above.
No production/signing/catalog writes.
Public110/catalog5 signatures, full HTTPS bytes and server hash match; regional
network health and affected-phone recovery are not proven. Android110/sequence5,
Windows0.2.16/sequence12, public Linux0.2.11 and owner Linux0.2.12~l03.2.13 unchanged.
[Incident evidence, safe workaround and remaining checks](releases/2026-11-03-android-update-incident.md).

<!-- FLEET-BOOTSTRAP-2 current -->
**3 November — isolated native data-plane canary qualification PASS.**
The next authorized substep exercises real AWG3.1/REALITY packets in disposable
client/gateway/origin containers with new synthetic keys. Existing production users,
profiles, credentials, assignments and services remain untouched. This is qualification
of a canary harness, not Amsterdam1/2 live acceptance.37 unit guards PASS; genuine
AWG fresh handshake/DNS/TLS HTTPS/NAT and REALITY auth/remote DNS/HTTPS PASS twice
with fresh keys on the same exact source/image.
Wrong identity/server key and direct-bypass controls reject; controlled origin sees
exactly2 application requests,2 DNS queries. Client and all run resources cleaned up.
Initial capability spelling, Xray config-extension and fixture nft syntax failures
are retained, cleanup PASS; no production parser or guard weakened. No user keys,
production mutations, client release, MESH or failover. Qualified image and repeat gates in
[the current report](releases/2026-11-03-fleet-data-plane-canary.md).

**3 November — independent network evidence and advisory recovery, LOCAL ROLLOUT PASS.**
Owner authorizes the next bounded step. Credential-free TCP observations now bind RU8443,
AMS1/AMS2:443 independently of SSH/inventory failures; legacy NL is never probed.
Append-only local records and a conservative three-sample/90-second advisory policy
distinguish missing/stale/conflicting data, path failure, service failure and stabilization.
No state grants VPN readiness or calls fleet admission, repair, restart or reassignment.
Direct read-only TCP reachability observed on all three endpoints; no authenticated
AWG/REALITY/MESH or end-to-end traffic acceptance. Source tests73 PASS, PostgreSQL
targeted69/full186 PASS, check/drift PASS. Source9870e12 is pushed and installed in
the local loopback console;184 packaged hashes match. Additive migration0007,
private PG backup, unchanged secrets and payment/operation hashes/counts verified.
Separate network timer active; three real timed observations per source at07:21–07:23UTC
all reachable, advisory=observe with fresh services; prior insufficient samples correctly
stabilizing. Permission-guarded view rendering and both local timers PASS. This bounded
step is complete; VPN data-plane canary remains a separately scoped next candidate,
not started. No automatic action or client version changes.
[Current evidence and rollback](releases/2026-11-03-fleet-network-probes.md).

**3 November — autonomous fleet observability continuation.** Owner removes the
interactive owner-test gate and requests continued automated development; .13 physical
AWG/TCP/Disconnect acceptance is DEFERRED_TO_FIELD, not PASS. No forced user testing,
assignment migration, invitations or automatic VPN switching follows from this decision.
Current bounded step: distinguish RU/Amsterdam1/Amsterdam2 in operator inventory;
old gateway-nl remains archive-only. Source/locked PostgreSQL tests PASS:30 operator/
packaging tests,45 targeted Django tests and162 full console tests; check/drift PASS.
Both NL nodes return real read-only service/host observations; no registry or HMAC key
is collected/sent to NL. Stale/missing/future/unknown/failed observations never imply
VPN readiness. Local console rollout now PASS fromc95cc86:177 packaged source/lock
hashes match, loopback-only health PASS, all three fresh sources imported with exact
bindings, legacy NL archive-only. Local secrets/volumes retained, PG backup private;
local payment/operation/device counts unchanged across import. Timer active with
reused approved SSH pins and380s budget. Initial stopped-console import errors and
verification-wrapper/mount-context failures retained, not acceptance PASS.
This bounded observability step is complete. Recovery policy/independent probes are
the next candidate, not implemented or activated here. No production VPN/backend
restart, public release, second-node MESH or automatic failover is claimed.
[Current report](releases/2026-11-03-fleet-observability.md).

**2 November — owner-requested two-node load follow-up, LIVE_METRICS / .13 INSTALLED.**
Owner requests exactly two Amsterdam choices and provisional5000Mbps capacity on
each node. Linux AWG/TCP picker removes the duplicate assigned-NL choice; Auto/MESH
retain country routing and do not imply second-node MESH. Independent fresh,
gateway-bound metrics never substitute country/other-node data. Source tests1251
PASS/183 environment skips; real-display GTK RU/EN2 PASS. Initial full test attempts
retained: missing GI in the venv, then8 fixture-mode failures under inherited umask002;
locked venv plus system GI and umask022 pass without weakening guards. Both NL nodes
now publish independent bound samples with operator-assumed5000Mbps duplex capacity;
RU aggregation and verified HTTPS PASS. Only monitor services changed; non-monitor
service PIDs/restart states unchanged. NL2's initial dedicated monitor directory was
0700 under private umask; failed readiness/automatic monitor retries retained.
Stopped that monitor, corrected only its directory to0755, kept private state0700,
and resumed only pending RU activation. Installer regression2 plus monitor11 PASS.
Exact .13 full DEB/AppImage/system/integrity/pre-start AWG/TCP gates PASS; packaged
GTK RU/EN scale1/2 four cases PASS and screenshots inspected. Initial frame-readiness
and too-small scale2 display attempts retained; bounded capture wait and correctly
sized virtual display repair the harness only. Fresh guarded full-package upgrade
from .12 to0.2.12~l03.2.13 PASS: candidate0d23476c/system1428321b, imports/READY,
installed GTK startup and installed-parser HTTPS samples PASS. All3171 protected
entries unchanged through install and smoke; no automatic connection. At final
readback AMS1/AMS2 load16.3%/4.7%, both5000Mbps operator-assumed, not a speed test.
Retain exact .12 full pair for guarded rollback. Public Linux0.2.11 and all signed
catalogs/downloads unchanged. Physical AWG/TCP/Disconnect checks are deferred to
field feedback by the3 November owner decision above, not a development stop or PASS.
[Load follow-up and gates](releases/2026-11-02-linux-node-load.md).

**Earlier2 November — explicit two-Amsterdam delivery; Linux superseded by .13 above.** Owner requests
visible choices on Android/Linux/Windows, not only new-device backend assignment.
Source schema3/target-bound proof, isolated durable floors, operator import and all
three selectors implemented; existing assignments remain unchanged. Local Python361
PASS/25 existing environment skips; GTK52 PASS, JVM/C# protocol PASS. Native Windows
control/DPAPI and ordinary-access CI PASS. Package-gate repairs: full desktop1229
PASS/185 environment skips, native configuration/Auto71 PASS, release contracts53
PASS. Backend fce23400 + signed schema3 selection sequence1 and exact Nginx routes
are LIVE/HTTPS-verified; legacy catalog4/policy2/all57 assignments remain unchanged.
Cold-listener readiness race caused1 rollback; journal reconciled, bounded helper
and2 regressions accepted, final switch PASS.3 manual restarts,1 Nginx reload,
0 DB restores. Production writes authorized/nonzero; protected rows unchanged,
invitations0/paid mutations0/phone actions0; native gateway services untouched.
Full Linux internal.12 from efc13f1: exact DEB/AppImage/system/pre-start smoke PASS,
packaged RU/EN GTK4 PASS; hosted candidate41438372471 PASS. Corrected Windows0.2.16
installer/hash/native compatibility41439156032 PASS; immutable Windows0.2.16
publication41442681710 and public HTTPS/hash PASS, signed Windows catalog12.
Android110 exact-source05d8919 CI41449895463 PASS: transport lifecycle, Friends
language/rows, native ARM64 packaging,43 executed instrumentation cases/24 variant
skips/0 failures. Exact downloaded APK/source/licenses/12 native libraries/16K
alignment and both Amsterdam row captures PASS. Existing-certificate offline signing
and immutable Android110/optional catalog5/invitation publication PASS; complete
public HTTPS APK/hash and both CSP routes PASS. Owner110 installation not claimed.
Android109 remains immutable.1 Nginx reload/0 backend restarts, protected rows unchanged.
Retained failed attempts are not erased.
Linux.12 owner full-package installation now PASS after the14:48CET workstation
reboot and a fresh authorized operation. Exact efc13f1 DEB and paired system
d5fc9df5 installed; candidate a4959628 imports PASS, system READY. All3169 protected
user/config entries unchanged, including symlink targets; root/user owners stopped
normally, no active FC interfaces, no automatic reconnect or server changes.
Installed GTK startup PASS on the owner display with isolated D-Bus and no renderer
overrides; first Xvfb attempt NOT_STARTED because xvfb-run is absent, retained.
Earlier sticky-owner refusal and exact .9 rollback/2562 unchanged entries remain
historical evidence, not the current installation. No marker deletion or L08 bypass.
Public Linux stays0.2.11; owner physical Amsterdam1/2 AWG/TCP/cleanup checks remain
pending. NL CPU is available, but unknown capacity suppresses legacy combined load;
per-node telemetry is not supplied or repaired by this installation.
Windows invitation/mirror16 and both actual CSP routes verified over HTTPS;6 browser
scenarios and12 signing/publication regressions PASS. Publication needed3 Nginx
reloads/0 backend restarts; protected rows unchanged. Real Nginx/HTTP55 PASS/1 skip.
Read-only public verifier now also binds Android signed/legacy discovery and full
APK bytes: current110/sequence5 and Windows16/sequence12 HTTPS PASS;49 focused
publication/signing/source tests PASS. No automatic phone installation/connection.
[Selection source and delivery gates](releases/2026-11-02-gateway-selection.md).

**2 November — SECOND_NL_ORDINARY_LIVE (AWG3.1/TCP REALITY).**
The owner-authorized second Amsterdam node185.10.158.196 is admitted for new device
assignments on Android109, Linux0.2.11 and Windows0.2.15 with unchanged schema2 clients.
All57 existing devices remain assigned to first NL185.10.158.212; no existing device moved.
MESH/readiness/renewal still use the first NL. Second-node MESH/renewal and a manual
client two-NL selector are not implemented or claimed. Existing FLEET-BOOTSTRAP-2 only.

Both new ordinary services are enabled/active, NRestarts0. Real external AWG handshake/
DNS/HTTPS/egress, REALITY auth/DNS/HTTPS/egress, pinned RU registration and probe cleanup PASS.
Original catalog4 is byte-identical; offline-signed per-device sequence5 is enabled for new
assignments, sequence6 is reserved for forward rollback. No public installer/update catalog
or client version changed. HTTP f33dee20… is serving; only dispatcher/routing module differ
from the actual paid108 predecessor. Protected registry/paid rows remain unchanged:
devices57, invites111, restricted grants2, ledger1/4; entitlement/cohort1/10/revenue0 retained.
RU backend/registration and new-node writes are authorized and nonzero for this admission;
first-NL services unchanged, invitations0, paid-event mutations0, phone actions0.

Owner accepted the existing TOFU SSH pin without another VNC comparison. Strict host checking
remains; no independent-provider verification claim or relaxation of rehearsal permits.
First preparation's directory-mode failure and the initial lower-priority HTTP override were
reconciled;3 controlled HTTP restarts include1 verified rollback, with no database restore.
A wildcard-listener check/order defect is recorded in the report, not erased: corrected
process-bound health and final registry readback PASS, with an in-process admission guard.
New source52 PASS; final focused regression339 PASS/25 existing environment skips; exact-native
Ubuntu24.04 config/unit/service-user-DAC simulation PASS. Retained Android JVM174 and native
Windows/visual/client-build checks PASS. Broader current full-CI PASS is not claimed.
[Live scope, failures and rollback](releases/2026-11-02-second-nl-ordinary-live.md) ·
[Sanitized receipt](releases/2026-11-02-second-nl-ordinary-live.receipt.json) ·
[Compatible routing source](releases/2026-11-02-fleet-multinode-source.md).

**Retained completed rehearsal evidence, not an active NEXT:** source readiness,
A→B→A, physical role reboot and retirement PASS; trials01–07 RETIRED. Frozen rehearsal
source d3416ea4abacfafc843411f765fb8037722b55d0 and its deterministic signed A/B artifacts
are unchanged. Retained fleet/console480 and paid170 PASS, Django check/migration drift PASS.
The disposable runtime/permit/remote/material/acceptance guards were not repurposed for
permanent use. No new production-layout reboot or second production MESH acceptance claim.
[Reboot evidence](releases/2026-11-02-fleet-bootstrap-2-reboot.md) ·
[Qualified rehearsal hashes](releases/2026-11-01-fleet-bootstrap-2-ready.receipt.json) ·
[Runbook](fleet-bootstrap.md). Older NEXTs below are historical, not concurrent active work.
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

## NL availability restoration — 31 October

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

[Same-operation report and remaining gates](releases/2026-10-30-nl-gateway-replacement.md).

## Current critical path — ANDROID-CONTROLLED-BETA

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

**Historical read-only input for BETA-0-CANARY-1 — OWNER_CANARY_BOUND_READONLY /
BLOCKED_CRL_PROFILE_COMPATIBILITY / LIVE_WRITES_NOT_RUN.**
Read-only provenance review fromf499bdf: **NL_VALIDATOR_ONLY_DRIFT** proven. The old
auxiliary validator allows3600s; actual SSH forced-command parser allows14400s and
its directory/timestamp function hashes match current accepted source. Exact directory
lifetime13401.739755428s passes the actual parser; no timestamp precision mismatch.
No parser correction/package/deployment is required by this finding.
Separate blocker: actual forced command accepts READ_ONLY_SECURITY_SNAPSHOT only;
CRL payloads fail MAINTENANCE_TRANSACTION_REQUIRED. Embedded/observed/RU CRL27211
match, minimum_crl27088; max(embedded,minimum) is enforced, but this route cannot
accept the next payload or update the floor. CRL_FLOOR_UNRESOLVED for that required
forward-update guarantee; do not claim CRL_FLOOR_LAG_NONBLOCKING or numeric corruption.
OWNER_CANARY_1=`dev_fa4f7e03ca04`; prior exact106/binding/status artifacts unchanged.
No lookup/status repeat. Ledger0/0, cohort0/10, owner certificates0/horizon CLEAR.
96 affected tests +48 synthetic parser +18 synthetic gateway/floor checks PASS.
Materials remain valid beyond720s at readback; monitor read-only/fresh, NL registry
UNAVAILABLE, not0; console synthetic-only. Protected identity/policy/ledger, owner
certificate/readiness scope, services and material/profile hashes unchanged. One
unrelated certificate was added by concurrent traffic; no global table equality claim.
Historical review proposed bounded maintenance/delivery and floor-contract
reconciliation. Its source gate is complete; production continuation is blocked by
the fresh preflight above. Preserve the read-only snapshot, no generic writes.
No refresh, activation, phone instruction or request for ГОТОВ while blocked.
[Provenance review](releases/2026-10-27-android106-beta-0-canary-1.md#nl-parser-provenance-and-read-only-material-review--28-october-local).

Historical exact-payload CRL source gate:
Exact-payload CRL source gate from11b99a6: pure paid-aware builder, no live sequence/
file mutation during preparation; one persisted payload/request per operation.
Private journal, one proven-NOT_SENT retry only, trusted exact remote readback,
post-acceptance local commit and crash reconciliation A–E implemented. Existing
publisher behavior and accepted recovery/lookup semantics preserved.98 new CRL/
packaging +79 canary +76 paid-backend +2 preparation tests PASS;206 restricted/sync/
directory tests PASS (29 existing optional native skips,4 native deselections).
118 PostgreSQL console tests and Django system/drift checks PASS. Unbound packaging
only; no production configuration/credential/permit/transport installed.
Its historical NEXT was read-only owner lookup/binding, now performed above.
That source gate performed no production registry, CRL, subscription/event, phone,
restart or deployment action.

Historical bounded-dispatch source gate:
Bounded dispatch correction from3a5e91d over accepted emergency source49bdd794:
recover only from versions1/2 after natural expiry, no valid bound certificate,
exact2592000s permit period and at most300s execution window. First apply allows
period_start<=server_now with dispatch delay0..299s, never rebases the period;
future/closed dispatch fails RECOVERY_DISPATCH_WINDOW_CLOSED. Existing authority
unchanged. Terminal reference_hash marker blocks all further normal/new recovery
events; only the identical backend-payload replay remains allowed. No new schema,
CRL mutation, identity/invite change or Django production adapter.
79 canary +118 PostgreSQL console +76 affected backend +2 preparation tests PASS;
Django system/drift checks PASS. Normal four-stage path retained. Packaging must
remain lookup_only, from exact committed source; artifact receipt is in the report.
Production lookup/registry access/binding/enrollment/CRL/Android/live operations
NOT_RUN. No Friends restart/deployment, CP2 change or desktop work.
Its historical NEXT was the CRL helper contract/source gate, now completed above.
Read-only owner lookup/binding are now recorded above; live phone operations remain blocked.

Historical local preparation at28657bf/68b99ac:
Continuation from55c6a24: private PG+synthetic-volume backups and disposable restore
checks PASS. Running loopback console rebuilt; migration0006 installed, system/drift
checks PASS. Existing50 synthetic bindings,3 customer-payment records, operations,
559 prior audit records and private configuration preserved; concurrent read-only
inventory imports append audit normally.118 console +76 paid-backend tests PASS.
Source-only preparation now handles restrictive umask without changing original
source/private-file permissions (2 regression tests). Bounded single-HMAC-token
canary operator/committed-source packager:30 synthetic tests PASS; no second
entitlement state machine, Django production adapter or real owner projection.
Only fixed activate/expire permits; no revoke/grace/migration/delete/CRL/restart API.
Production lookup/binding/package execution/enrollment/CRL/Android actions NOT_RUN.
The continuation ends at the suggested component paths. Short expiry/observation
windows, reviewed CRL delivery procedure and physical-phone coordination remain
unspecified; the final30-day recovery target is accepted, not executed.
Historical NEXT was to obtain the live procedure and coordinate OWNER_CANARY_1;
the current emergency source gate and next authorized boundary are recorded above.

Historical source checkpoint55c6a24 (before the local console upgrade):
Dependency: owner accepted CP2 as DONE / PAID-AWARE EMPTY-COHORT BACKEND SERVING /
PUBLISHER CAPABILITY PRESERVED / REAL PAYMENT AND ENROLLMENT NOT_RUN.
Only OWNER_CANARY_1 may become the permanent internal production canary; planned
allocation1 owner +9 customer devices, not an enrollment or an occupied slot yet.
Control-plane-only PaymentRecord purpose: customer_payment (default, existing rows
preserved) /internal_canary (zero amount, not customer payment/revenue). Purpose
immutable from creation; separate analytics/UI/audit/admin receipt metadata.
118 console PostgreSQL tests PASS, including23 new purpose/migration/workflow tests.
No entitlement-authority/client changes, CP2 source/package gates, migration or
restart repeated. Test migrations use a separate disposable local PG test database;
running console/schema not upgraded, production never connected by the new workflow.
Owner administrative lookup/HMAC binding, activation, live Connect/expiry/CRL/session/
recovery/reactivation and Android state readback NOT_RUN. No private selector copied
into code, docs, operator files, audit, events or receipts.
The original request ended at purpose choices; its historical NEXT was to obtain
the continuation. Current progress and the remaining live gate are recorded above.
[Canary source checkpoint and remaining gates](releases/2026-10-27-android106-beta-0-canary-1.md).

**Accepted input CONTROL-PLANE-2 — DONE / PAID-AWARE EMPTY-COHORT BACKEND SERVING.**
Owner-authorized continuation from90ad148 completed. Exact source8b4177d/bundle6ea4ef3a…/
HTTPdcd76998… preserved, not rebuilt. Committed typed D-Bus observer a2bf728 handles
empty/nonempty jobs, strict signatures, full argv and PID/config stability;
53 observer +8 existing guard tests PASS,9 private mocked operator-flow tests PASS.
Fresh20:09:45UTC preflight PASS, paid schema PRESENT_EMPTY/8 objects; consistent
backupff9d0c50…/446464 bytes, isolated restore/integrity/FK PASS, six original unit
files and old archive retained privately. No repeat migration or live DB restore.
Only own highest-priority ExecStart drop-in installed; typed + existing argv guards
PASS. One rollout restart at20:10:09UTC: PID120606→486622, NRestarts0. Three post-start
observations and independent20:11:13UTC readback PASS, sole HTTP listener belongs to
new MainPID. Paid subscriptions0/events0; device/invite/grant/revocation/admission/
publisher fingerprints unchanged. HTTP404 proves liveness, not paid-user acceptance.
Restart budget consumed1 rollout/0 emergency; no second rollout allowed. Earlier
pre-start pending-job stop consumed0/0 and was independently cleaned up; bounded
read-only quiescence wait then passed. All terminal runners/receipts remain historical.
Monitor active/waiting, post-start cycle SUCCESS; NL registry unavailable, not0.
No real payment/enrollment, CRL/gateway/client/desktop change; Android106 unchanged.
CP2 review accepted by the owner. Historical NEXT was CP2 rollout review, then
actual Android Beta-0 blockers. No further CP2 restart/deployment/migration/gates;
the new limited canary authorization does not authorize customer payments/enrollment.

Previous guarded attempt (historical, not a second active NEXT):
Stale active-looking Linux blocks removed by242f428; only Android CP2 is active.
Exact source8b4177d/bundle6ea4ef3a…/HTTPdcd76998… unchanged, baseline/publisher
preservation gate PASS. Fresh19:28 preflight: old healthy PID120606, paid schema
PRESENT_EMPTY/8 objects,54 devices/108 invites/2 grants; NTP/integrity/FK PASS.
Fresh consistent backup643fe650…/446464 bytes + isolated restore PASS; six exact
unit/drop-in files and old archive saved privately. No migration repeated.
New highest-priority drop-in selected candidate; committed effective ExecStart
guard PASS **before any restart**. The following private observation helper raised
JSONDecodeError; no restart was requested. Own drop-in removed, old effective
ExecStart guard PASS. Initial cleanup observation also failed parsing; independent
19:37 readback confirms original unit hash/argv/PID restored, old21d64558… healthy,
paid rows/events0, device/invite/grant/revocation/admission/publisher fingerprints
unchanged. Rollout restarts0/emergency restarts0; no second rollout attempt.
8 guard tests rerun PASS; prior192 focused acceptance retained, not rerun/full CI.
Historical artifacts/backups and Android106 unchanged; no real payments/enrollment,
CRL/gateway changes or Linux/Windows work. Local read-only timer active/success;
NL registry remains unavailable, not0. Live paid CRL/session acceptance still open.
[Current and immutable historical evidence](releases/2026-10-27-android106-control-plane-2.md).
The previous pre-start stop is superseded by the explicit continuation above.
No real enrollment, paid events or client/gateway changes are authorized.

**Принятый вход CONTROL-PLANE-1 — DONE / LOCAL SYNTHETIC + PRODUCTION-READONLY SNAPSHOTS.**
Русский Django Admin/UI, 50 demo identities (paid cap10 неизменён), отдельные
read-only inventory/server observations и synthetic technical samples, фильтры/
charts/drill-down, timestamp/freshness, emergency stop новых demo dispatch.
Friends paid_beta остаётся единственной authority; production snapshots не могут
попасть в payment workflow. Read-only SSH collection двух разрешённых шлюзов:
RU54 devices, NL registry UNAVAILABLE (не пустой); server metrics наблюдались.
95 PostgreSQL console +76 unchanged-backend tests PASS; Chromium desktop/mobile,
русский payment→preview→confirm и stop/resume PASS. Реальная client telemetry/
continuous monitoring/alerts не подключены: отсутствующие показатели = null,
не0/100%. Production writes/deployment/payment/enrollment0; Android106/backend/
public catalog неизменны. [Отчёт и границы](releases/2026-10-27-android106-control-plane-1.md),
[runbook](../control_plane/README.md). STOP; NEXT — review и только фактические
Android controlled-beta launch blockers, не автоматический rollout.

**Принятый вход CONTROL-PLANE-0 — DONE / LOCAL SYNTHETIC ONLY.** Django/PostgreSQL
management console over accepted PAID-ENTITLEMENT-MVP; no second subscription state
machine. Friends registry/paid_beta remain authority; PG stores workflow, payment/
cohort/incident/audit/release metadata and timestamped read-only projections.
Custom Admin/dashboard/charts, POST lookup, pure real-backend preview, signed
confirmation and uncertain-result reconciliation implemented.57 PostgreSQL tests
+76 focused unchanged-backend checks PASS; Chromium desktop/mobile PASS,5 synthetic
events/2 synthetic payment records, no JS errors. Local loopback UI healthy;
production deployment/registry lookup/real payments/enrollment NOT_RUN.
Android106/APK/source/catalog unchanged. [Report and limits](releases/2026-10-27-android106-control-plane-0.md),
[local console runbook](../control_plane/README.md). No new top-level project/PLAN ID.

**Owner decision27.10: Linux L04.2 PAUSED / NON-BLOCKING DESKTOP ENGINEERING.**
L04.2-R3 SOURCE GATE **DONE / review accepted**; .11 CONSTRUCTION **DONE /
frozen internal candidate**. L04.2 не DONE. Exact0.2.12~l03.2.11,
candidate570a5515…/system34b27cb9…: четыре размера/SHA256 сверены, artifacts
read-only/internal. Source/native/system/reference и46 tests PASS; embedded
DEB/AppImage equality PASS/inner exit0; outer exit1 только на root-owned
`embedded.json` overwrite. Product defect не установлен. Installed package и
live P0/P1/Auto NOT_RUN; Linux MESH installed acceptance и overall CI PASS нет.
`PACKAGE_HARNESS_EMBEDDED_RECEIPT_FILENAME_COLLISION` перенесён в существующий
D02/CI debt; не Android blocker. Никакого Linux retry/checkpoint/harness repair,
rebuild/install/rollback, retained test identity, AppImage lifecycle, L05/L06 или
публикации. Дальнейшая installed acceptance — отдельный поток после controlled beta.

**ANDROID106-MESH-FIELD-1 = PASS / owner accepted:** реальный внешний пользователь,
реальная whitelist-сеть, обычное приложение, MESH подтверждён. Desktop parity не
блокирует Android beta; field PASS не переносится на Linux/Windows.
Exact signed106: `0.1.18-beta106-recovery`/106, `com.familyconnect.app.friends`,
56093664 bytes, SHA256`242855c43e889e708234ce2f687fa02d37bccb1eee408904f09216b6abd8f020`.
Manifest/signature/reference/2073 source files проверены; другие code106 inputs
разделены на byte-identical installed copy и unsigned builds. No source change.
Read-only administrative lookup: одна canonical identity/invite, activation active,
revoked=false, MESH eligible; более новый authenticated ACK26.10 21:00:50UTC
сообщает106/READY (старый support snapshot84 не текущий). APK bytes/signer на
устройстве и точное время field use не аттестованы; новых invite/записей0.

**ANDROID-CONTROLLED-BETA / PAID-ENTITLEMENT-MVP — source checkpoint DONE,
originally NOT_DEPLOYED; CP2 now DEPLOYED_EMPTY_COHORT, paid launch BLOCKED.**
The following source-acceptance record is historical, not the current deployment state.
Owner Beta-0: максимум10 existing
activated Friends identities, только exact106 (new106 install/already106), private
verified handoff, manual confirmed payment/operator event. Older-version upgrade и
external acquiring исключены из Beta-0, не новые PASS/launch blockers. APK неизменён.
Отдельные paid subscription/event tables, atomic opt-in/cap10/idempotent audit,
trial/active/grace/expired/revoked effective state и private CLI реализованы.
Без paid row прежняя admission/all_activated семантика сохранена; paid challenge и
fetch повторно проверяют entitlement, certificate/response ограничены paid/crypto
expiry. No automatic trial/grace, identity/invite/activation/client changes.
243 targeted PASS,10 nginx skips,8 external-integration deselections; не overall CI.
Ранее49 backend/20 JVM остаются историческими, не full installed upgrade PASS.
Production DB/deployment/payment/cohort mutations0; live paid enforcement NOT_RUN.
Старый certificate/session не отзывается мгновенно: действуют signed expiry/CRL
propagation; paid-aware deployment/empty-cohort + synthetic106 expiry/revoke/recovery
rehearsal остаются gate. Нельзя rollback на pre-paid backend при nonempty cohort.
Saved signed105 verified, downgrade не safe rollback. Public updater60/sequence1
не менялся. Delivery/opt-in roster, legal text, monitoring/stop ownership открыты.
[Readiness/artifacts](releases/2026-10-27-android106-controlled-beta-readiness.md),
[MVP result and finite blockers](releases/2026-10-27-android106-paid-entitlement-mvp.md),
[private operator runbook](paid-beta.md).
**Historical source-checkpoint NEXT — закрыть только фактические Android controlled-beta launch blockers.**
Следующий bounded этап — review CONTROL-PLANE-0 и только фактические Beta-0 gates;
paid-aware server/synthetic acceptance/recovery требует отдельного разрешения.
Local console не разрешает production connection/deploy/enrollment/сбор оплаты.

## Предыдущие записи — evidence, не активные NEXT

Записи ниже сохранены, включая прежние Linux NEXT и ops observations; текущие
priority/status определены owner decision выше. Они не разрешают продолжение Linux.

**L04.2 — R3 PARTIAL / PACKAGE_GATE_FAILED (environment harness finalization).**
R2 FINAL PARTIAL / READINESS_CAUSE_UNRESOLVED accepted: diagnostic collapse
hid the original fetch cause. No further live Connect on .10. R3 is a bounded
subtask of L04.2, not a new top-level PLAN ID. Input70b919b; R1/R2 runtime169aa68
cleanup/containment/drain semantics preserved. Deterministic old-red reproduces
availability→expired/missing cache masking; source now retains typed fetch error,
keeps FETCH_FAILED as import result, preserves validated-cache fallback and makes
cooldown-only MISSING/EXPIRED terminal. Existing FETCH_INCOMPATIBLE_RESPONSE is
added to strict desktop diagnostics. Exact Go race, native15, combined3, MESH157,
cleanup32 and desktop1317/82skip PASS retained. Source2d125137 is review accepted
in affected scope; runtime/tests/locks/pins unchanged. Reviewed Gson and missing
Go-cache blockers are environment-only. Retained Gradle171/classpath/JAR integrity
and read-only javap PASS, no Gradle replay. Offline Go module verify/dependency
list/validator compile close the cache prerequisite; one authorized Android/Python
selection now143 PASS/0 FAIL/0 ERROR/0 SKIP. Bounded readiness workflow path
coverage commite93bf7d; canonical GitHub run40491350035 SUCCESS. Raw full suite remains FAIL:55 FAIL/3373 PASS/105 SKIP/0 ERROR; no overall CI PASS.
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
NOT_RUN. Containers removed; .10/.11/READY/protected seven byte-identical. Sealed internal/unpublished .10 remains
4264406722f6dd3efb83e9d9666e67180ce4f950333bb3e711bcbb4f5068b55a;
incorrect historical task suffix is not an artifact identity. Phase B/setup/GUI
authorization evidence retained, not replayed. No server/material/policy changes.
READINESS_RELAY_PROBE_CORRELATION_GAP belongs to L06; direct correlation rows
cannot count relay requests. No RNS/wire expansion. Owner workstation NOT_USED.
L04 IN_PROGRESS; L04.1 DONE; L05/messages/voice/signing/publication NOT_RUN.
[Current R3 report](releases/2026-10-27-linux-readiness-cause-preservation-l04-2-r3.md).
**STOP. NEXT — review L04.2-R3 package-harness finalization.**

**OWNER-CHAT-UX-2-INSTALL — PARTIAL / owner-use accepted (owner review).**
Exact **0.2.12~l03.2.9** установлен; candidate/package/system checks PASS,
одно main window/embedded chat, один ChatClient и один D-Bus owner подтверждены
владельцем. Две queue-операции неизвестного происхождения исключены из acceptance
evidence; product defect не установлен. Установка принята для дальнейшего owner-use,
не как full L05 или публикация. OWNER-CHAT-UX-2-INSTALL не продолжался;
дополнительных сообщений, smiley/composer/visual проверок владельцу не выполнялось.

### CHAT-UX-2 — source/package DONE; прежние ограничения сохранены

Owner decisions: мессенджер внутри единственного главного окна; exact Android106
ICQ-classic49 GIF вместо системного picker. CHAT-UX-1 technically completed в
reviewed source/UI/package scope, но product design superseded; исходное evidence
и residual failures сохранены, не превращены в PASS нового дизайна.
По текущему owner review установлен internal **0.2.12~l03.2.9**, candidate
`6f312d1e7c783ea42a39ca164d93d74b0ec4faf5bac53e24c12551cedd052a5b`;
system `43266d97c6a9f8d4e7026727cbb4b5cb6aeea49db799f93bd798b67a8135198c` READY.
Исторический OWNER-CHAT-UX-INSTALL относился к .8; текущий review .9 указан выше.
CHAT-UX-2 source: embedded Stack, прежние RPC/drafts/bubbles/voice,49-face manifest,
Android aliases/boundaries, literal copy, один visibility-bound GIF clock.
Full desktop1272 PASS/84 SKIP; messenger222 PASS; parser/picker/UX72 PASS;
exact DEB/AppImage/integrity/AWG/TCP gates и14 synthetic GTK captures PASS.
Full local3353 PASS/36 прежних FAIL/101 SKIP/1 отдельная новая FD teardown ERROR
(22 vs24 descriptors, повторилась на final source); общий full-suite PASS не заявлен.
CI full suites54/54/53 FAIL без suppression. Failure IDs/ограничения сохранены в отчёте.
Собран exact Ubuntu26.04/Python3.14 **0.2.12~l03.2.9**, source `cb81cd5`,
candidate `6f312d1e7c783ea42a39ca164d93d74b0ec4faf5bac53e24c12551cedd052a5b`;
прежний system build byte-identical, .7/.8 immutable.
[CHAT-UX-2 report, hashes/screenshots/gates](releases/2026-10-26-chat-ux-2.md).
Full L05 / TCP HTTPS diagnosis / signing / publication **NOT_RUN**.
Текущий NEXT — только review L04.2; исторический report CHAT-UX-2 не активный NEXT.

### Предыдущий compatibility checkpoint — историческая граница

**U2604-COMPAT — CHECKPOINT PASS, только Ubuntu26.04/CPython3.14 compatibility.**
LOCAL-OWNER-UPGRADE **BLOCKED на ABI**: workstation Ubuntu26.04/system Python3.14.4,
frozen .5 требует3.12. До установки/backup/launcher migration не дошли; workstation unchanged.
Новая disposable Ubuntu26.04.1/systemd259/Python3.14.4: exact provisioning/messenger
locks,630 RECORD/hash-verified runtime members, strict imports всех17 distributions,
GTK/Adw/cairo/Secret Service/GStreamer/codec2 и129 адресных tests **PASS** без source edits.
Начальная test-runner ошибка3 imports из-за отсутствия explicit public source path
сохранена; исправлен только invocation, все129 PASS. Pins/hashes не менялись.
Собран отдельный **0.2.12~l03.2.7 / Ubuntu26.04 / Python3.14**, internal/unpublished:
candidate `c79b4feb…` / source `3df82b4` / system `43266d97…`.
Exact DEB/AppImage, strict user/system imports, real pkexec/READY, rollback,
tamper/mixed-build/locks, synthetic state и URI/user-service gates **PASS**.
Full desktop1199 PASS/83 SKIP; native144, Auto18 checks, DIRECT, lifetime15,
combined3 и AWG/TCP prestart PASS. Full suite3257 PASS/**55 FAIL**/104 SKIP без suppression;
extra root lock/umask observation воспроизводится на3.12 и3.14, isolated runtime6 PASS.
Общего CI/release PASS нет; residual failures — отдельный technical debt.
Frozen .5/3.12 hashes/IDs повторно сверены, immutable; L04.1 не переоткрывается.
Production VPN/GUI/helper/protocol/identity/cache logic не меняется. Private identity,
activation/cache/gateway не использованы. Publication/L04.2/L05/teardown/live VPN **NOT_RUN**.
[U2604-COMPAT report](releases/2026-10-26-linux-ubuntu2604-python314-compat.md).
Прежний STOP U2604-COMPAT сохранён в отчёте; установленная .7 подтверждена выше.

### Frozen Linux AWG/TCP Beta baseline — сохранён, не активный NEXT

**L04.1-LIVE-2 DONE / review accepted; L04.1 DONE — installed Linux AWG/TCP,25.10.**
Владелец принял E, F1 и F2. P1/P2 и A–D на .4 не повторялись; E/F1/F2 на .5
приняты без нового live-run. **Linux AWG/TCP Beta candidate frozen:
exact 0.2.12~l03.2.5**, candidate f0ee1760…/source1c2beb6/system8d7d78ec….
AppImage/DEB bytes неизменны; hashes/размеры повторно сверены локально, без запуска.
Candidate **internal/unpublished**, ранее установлен только в disposable guest;
не установлен на workstation, public/invitation versions и каталоги не менялись.
Поддерживаемый beta scope: activation, AWG/TCP, Connect/Disconnect, DNS/HTTPS,
state preservation и diagnostics. MESH/Auto и messenger в него не входят.
Registry restart F2 остаётся отдельным **operational observation**: первый readback
FAIL сохранён, **uninterrupted continuity NOT_PROVEN**, причина неизвестна;
assignment/configuration не изменились, registry service identity изменился.
Клиентский F2 не повторять; R3 не создавать. Это не блокер принятого client scope.
Parent **L04 IN_PROGRESS только из-за L04.2**; L04.2/L05/test-device teardown **NOT_RUN**.
Full-suite residual54/54/54 failures (historical Docker53) — отдельный technical debt,
общего CI PASS нет. Original protected state/teardown receipt сохранены.
Signing/upload/catalog update/publication **NOT_RUN**; никаких новых live/source/server
операций. [Итоговый отчёт](releases/2026-10-25-linux-installed-awg-tcp-l04-1-final.md),
[единый beta-freeze manifest](releases/2026-10-25-linux-awg-tcp-beta-freeze.json).
**STOP. NEXT — решение владельца о signing и ограниченной публикации Linux AWG/TCP Beta.**

### Исторические checkpoints — не текущие статусы или NEXT

**L04.1-LIVE-2-R2 DONE / review accepted — source/package scope.**
На exact .4 review принимает P1/P2, B1/B2/C1/C2/D PASS; E FAIL/review accepted,
F1/F2 NOT_RUN. E доказывает queued Future/busy/open/CONNECTING, не late VPN start:
helper/TUN0, generation0/pending null; fixture отменил Future до освобождения worker.
R2 явно отслеживает только normal Connect/Disconnect; успешный cancel снимает busy
и fencing запрещает старый callback. Running/done-undelivered mutation блокирует Close.
Deterministic prior-source overlay4 FAIL → targeted197 PASS, full desktop1191/84.
Новый internal .5/source1c2beb6/candidate f0ee1760…: exact integrity и оба offline
systemd255/pkexec package gate PASS. System8d7d78ec… byte/contract verified unchanged;
.4 immutable. Linux/AWG/TCP/package CI PASS; isolated root→UID/native179,
Auto18/DIRECT/lifetime15/combined3 PASS. Full CI54/54/54 failures (Docker раньше53;
дополнительный readiness-receipt assertion, причина не установлена), без fixes/retries.
Общего CI PASS нет. В самом R2 private identity/gateway/live E/F не использовались.
Source/package checkpoint принят; последующий live checkpoint указан выше.
L04.1 IN_PROGRESS; L04.2/L05/test-device teardown NOT_RUN.
[R2 report](releases/2026-10-25-linux-queued-connect-close-l04-1-live-2-r2.md).

Исторические этапы25.10.2026 (текущий итог и NEXT выше):
**L04.1-LIVE-1-RETEST DONE / review accepted**.
Review принимает fresh DNS matching request/reply на actual AWG/TCP TUN после flush,
включая валидный terminal **NODATA**; positive installed gate завершён без повтора.
Exact **0.2.12~l03.2.2**, source `57f8eff`, candidate `d9c0d07f…`, system build-9
не меняются. [Исторический RETEST и решение review](releases/2026-10-25-linux-installed-awg-tcp-l04-1-retest.md).
**L04.1-LIVE-2 PARTIAL / review accepted**: actual installed tamper/reinstall A PASS;
B1 первый отказ — root lock блокирует transport, но AWG helper up1 и pending/APPLYING
сохраняется после освобождения lock (generation0→1). Сеть/identity/cache/floors
сохранены, guest уничтожен; journal не объявлен восстановленным. B2–F NOT_RUN.
Product source/artifact bytes immutable; никаких повторов/исправлений.
FC-3YSQ-BE2D/nl сохраняются, новый issuance/provisioning/manual fetch запрещён.
L04/L04.1 IN_PROGRESS до LIVE-2 review; L04.2/L05/teardown NOT_RUN.
[LIVE-2 checkpoint](releases/2026-10-25-linux-installed-awg-tcp-l04-1-live-2.md).
D01/full suites54/54/53 failures и voice/Windows observations сохраняются.
**L04.1-LIVE-2-RESUME PARTIAL / review accepted, STOP на E** (тот же ID). Exact .4 A/B1 review
accepted; без повтора. P1/P2 continuity, B2, C1/C2 и D recovery PASS.
E: один queued Connect + Close — GUI остаётся busy/open, Future не отменён;
helper/TUN0, generation0/pending null. Только fixture cleanup, без повторного action.
F1/F2 NOT_RUN. Сеть/state/server readback сохранены; KVM/secret copies уничтожены,
original FC-3YSQ-BE2D/nl сохранён. Source/candidate immutable. L04.1 IN_PROGRESS;
L04.2/L05/teardown NOT_RUN. Review E принят; correction только R2 выше.
[Продолжение того же checkpoint](releases/2026-10-25-linux-installed-awg-tcp-l04-1-live-2-continuation.md).
**L04.1-LIVE-2-R1 DONE / review accepted (source/system/package).**
Final internal **0.2.12~l03.2.4**, source053c4e5, candidate42ea0699…,
новый system8d7d78ec…/authorization2 (не build-9). .3 — intermediate immutable.
Actual AWG/TCP red→green: up1/start0, IDLE/generation2/pending null, poll PASS;
unknown outcome сохраняет pending до same-owner recovery и первую причину ошибки.
Exact integrity/systemd255/pkexec/rollback/DEB/AppImage/coherence/old-build refusal
PASS; desktop1195 PASS/96 SKIP. Linux/AWG/TCP/package CI PASS; native/DIRECT
первый отказ сохранён, один unchanged rerun PASS. Full CI54/54/53 failures;
общего CI PASS нет.
В самом R1 live B1/B2–F NOT_RUN; private state/gateway не использовались.
Последующий installed результат — RESUME выше, не перенос evidence между scopes.
[R1](releases/2026-10-25-linux-prestart-journal-l04-1-live-2-r1.md).
**Граница завершения — STOP; NEXT review PARTIAL L04.1-LIVE-2 (E).**

Предыдущий **L04.1-LIVE-1 PARTIAL принят review**; final-2 больше не candidate
для завершения L04.1. Его положительное live evidence ниже сохраняется исторически.
L03.1/L03.2 **DONE (review accepted)**; parent L03 **DONE** в scope внутреннего
Linux-кандидата. AUTH/PROVISION **DONE, review accepted**. L04/L04.1 **IN_PROGRESS**;
LIVE-2 теперь PARTIAL (см. текущий checkpoint); L04.2 **QUEUED / NOT_RUN**.
Exact final-2 не изменён.
Реальная KVM Ubuntu24.04/systemd255: DEB/GUI/pkexec/READY PASS; AWG×3 и TCP×1,
DNS/HTTPS/64KiB download+upload, reconnect/handoff и network cleanup PASS.
Original AppImage AWG/traffic и single-owner/confirmed GUI close PASS; после reopen
Disconnect отказал: «Connection settings are being updated», actual tunnel остался.
STOP: без новых connect/исправлений. Cleanup-only GUI Disconnect после освобождения
lock восстановил baseline; guest/временные secret copies уничтожены. FC-3YSQ-BE2D,
nl bindings, исходный protected state/cache/floors и teardown receipt сохранены.
Device-scoped gateway cleanup → readback → registry revoke остаётся NOT_RUN.
D01 открыт:54 residual failures; D02.1-R PARTIAL/NOT_RUN; Windows/voice сохранены.
[Отчёт LIVE-1 и точная граница отказа](releases/2026-10-25-linux-installed-awg-tcp-l04-1-live-1.md).
LIVE-1 — исторический checkpoint, не активный NEXT. L04.1-LIVE-2/L04.2/L05/teardown NOT_RUN.

### Принятый checkpoint L03.1

Срез **L03.1**, 25.10.2026: внутренний system/runtime build-9; review accepted.
D01.3/D01.3-R приняты в public completion/admission scope; L01/L01-R,
локальные L02/L02.2, D03/D04/D05 и native границы сохранены. D01 открыт,
D02.1-R PARTIAL/NOT_RUN. [Отчёт L03.1](releases/2026-10-25-linux-system-runtime-l03-1.md).
758 payload files: manual/Auto/chat, native/RNS/Python3.12, anchor, AWG3.1/TCP.
94 финальных адресных PASS (umask077); desktop1120 PASS/24 SKIP. Systemd255 PASS:
imports, реальный polkit/UID IPC, idle units, install exclusion, rollback/capabilities.
Rollback повторно маскирует службы до восстановления old source; actual start refusal PASS.
Source `f826dbd`: Client Linux и isolated native/root→UID/Auto/DIRECT CI PASS.
После обрыва25.10: неизменный build-9 повторно проверен в disposable systemd255;
package/system smoke и94 адресных PASS; исходники/публичная поставка не менялись.
Control/phase0/Docker: по54 failures, errors0; voice observation сохранён. Не общий CI PASS.
Review L03.2 теперь принят; родительский L03 DONE только в scope внутреннего кандидата.
Ни public versions/catalogs, ни установка на рабочую машину не разрешены.
Review L03.1 принят; это предыдущий, не активный NEXT.

### Предыдущий checkpoint D01.3-R (review принят 25.10)

Срез **D01.3-R**, 24.10.2026: DIRECT completion/admission contract исправлен;
**source gate PASS, review pending**.
Review D01.3 принял ChatBridge и Host/ServiceHost; D01.3 **PARTIAL по review**
из-за оставшегося close→active.pop окна DirectHost. Только эта коррекция;
**NEXT — review D01.3-R**, без автоматического L03.
Вход: чистая актуальная `main` = remote `68e4029f58d54384471576c623b08e89752f2c94`.
[Отчёт D01.3-R](releases/2026-10-24-desktop-chat-direct-completion-d01-3-r.md):
actual DirectHost/DirectBridge/Authority, Unix IPC и барьер после фактического close/EOF.
До: **1 failed**, active4/native opens3/API sends2, dependent open ConnectionResetError.
После: close и active.pop под одним admission lock после прежнего cleanup;
четвёртый mailbox проходит, пятый отклонён, закрытие возвращает capacity.
**30 PASS**: пять новых DIRECT + прежние24 completion + исходный bounded-mailbox.
Cancel/deadline/shutdown bounded; descriptors/handlers/DIRECT monitors учтены;
synthetic socketpair backing не заменяет native/installed acceptance.
Зависимые DIRECT/public IPC/error/lifecycle **326 PASS**, root→UID/process **13 PASS**.
Production source `050f06baef8b94e81d1bd4becb7f4fc38d1a6744`; final test source
`b910edbd108fc5e146792b6db966d6f8daf53b1a` pushed/remote-verified. Follow-up только
согласует post-close Event с EOF observer: **5 PASS**, old-host overlay red1 без rollback.
На финальном source Client Linux **40134155274/120992056110 PASS**, включая
mandatory desktop pytest. Isolated-linux **40134155291/120991993095 PASS**:
прежние15 authenticated, combined3, root→UID/process, Auto/DIRECT kernel и race.
Full suites отдельно: control **3061/54/138**, phase0/tests **3061/54/138**,
Docker **3059/54/140**, errors0 (passed/failed/skipped). Voice/AWG/TCP PASS;
Windows protocol job того же Auto workflow FAIL, вне scope/без разбора и перезапуска.
Это не общий CI PASS. Точные SHA/jobs в отчёте; прежние54 failures/voice не исправлялись.
Принятые L01/L01-R, локальные L02/L02.2, D03/D04/D05/native semantics сохранены.
D01 открыт, D02.1-R PARTIAL/NOT_RUN. Версии/identity/keys/history/settings/floors/
reference pins неизменны. L03/install/live/publication/Windows/fleet/iOS NOT_RUN.
**STOP. NEXT — review D01.3-R.**

### Предыдущий checkpoint D01.3 (evidence до DIRECT review correction)

Срез **D01.3**, 24.10.2026: public chat IPC completion/admission race исправлена;
**source gate PASS, review pending. NEXT — review D01.3.**
Вход: чистая актуальная `main` = remote `d448e99b55e594522c02234ac2a87575603a6bbb`.
Review L02.2 принят в local source/native scope; исходный локальный критерий
L02 (authenticated OFF→ON/publication→EXISTING_EXIT→OFF через Manual и Auto) выполнен.
Это не installed/live/F-01 и не общий CI PASS. D01 открыт, D02.1-R PARTIAL/NOT_RUN.
[Отчёт D01.3](releases/2026-10-24-desktop-chat-admission-d01-3.md): actual Host/
ServiceHost/ChatBridge, Unix IPC и event barriers; synthetic native lane только
для адресного public admission evidence. До: probe и prepare допускают следующий
open до cleanup, **2 failed**, ConnectionResetError. Это та же выявленная гонка,
но точная причинность исторического CI BrokenPipeError не установлена.
После: EOF управляющего обмена ждёт завершения cleanup в пределах исходного
deadline, максимум4s; EOF/removal сериализованы с admission. Caps4/native caps,
handler/monitor accounting, typed errors/cancellation и no-replay сохранены.
Локально **266 passed** (24 новых + зависимые Python/IPC/error/lifecycle).
Source `23e3c5513ab9c37e919f228066c0e23f733a997e` pushed/remote-verified:
Client Linux (включая mandatory desktop pytest) и isolated-linux PASS; локально
прежние15 authenticated, combined3 и13 root→UID/process PASS. Follow-up
`f258c17007102634fead9894bcfe9a82f6db44cf` публикует тестовый handler до ответа
(24 PASS); mandatory desktop pytest **40132223364/120986275264 PASS** на этом SHA.
Весь Client Linux job PASS. Завершившиеся full suites на `f258c17`: control
**3056/54/138**, phase0/tests **3056/54/138**, Docker **3054/54/140**, errors0
(passed/failed/skipped); точные jobs в отчёте, не общий CI PASS. Voice PASS без
изменений voice-кода; прежний holding-state failure сохранён отдельным результатом.
Production-код после `23e3c55` не менялся. Общий D01 остаётся открыт;
54 residual failures и voice failure не исправлялись в этом scope. Прежние15 authenticated,
combined3, root→UID/process, Auto/DIRECT и full suites не отключены.
Identity/history/settings/keys/floors/reference pins и установленный baseline
не менялись. L03/установка/live/publication/Windows/fleet/iOS NOT_RUN.
**STOP. NEXT — review D01.3.**

### Предыдущий checkpoint L02.2 (evidence до принятия review)

Срез **L02.2**, 24.10.2026: локальная authenticated цепочка
**SERVICE_ONLY → VPN CONNECTED/publication → EXISTING_EXIT → новый SERVICE_ONLY**
прошла отдельно через настоящий manual Supervisor и Auto/MESH.
**Review pending; родительский L02 PARTIAL. NEXT — review L02.2.**
Вход: чистая актуальная `main` = remote `9d472e96b6854f26053ca8d797d2c73aad18b0ef`.
Review L02.1-R2 принят. [Текущий отчёт](releases/2026-10-24-linux-chat-mesh-l02-2.md):
UID1000 IPC, настоящие native owners/FamilyTLS/Mux, TUN, private D-Bus/resolved,
kernel route/DNS readback, native health/publication, broker bind/renewal и cleanup.
На каждом участке challenge/register/duplex fixed-mailbox; три последовательных
transport opens, generation/operation lease accounting, held cleanup/late acquire,
profile mismatch, active-mailbox cancellation, signed expiry/revocation, DENIED/no replay.
Исправлены потеря release при CONTROL4 и выявленная race-инициализация packet RX;
caps/reference pins и порядок drain→worker exit→admission сохранены.
Локально 242 адресных Python, 13 root→UID/process, прежние15 authenticated,
combined gate, native/race, оба Auto/DIRECT kernel gates и 175 pins PASS.
Source **`dac0f6b45be6ed8703d3de93ff5fdbc67462eabe`** pushed/remote-verified.
CI20:29UTC: isolated-linux **40129362252/120977564710 PASS**, включая прежние15,
новый combined **3 passed / 79.04s**, оба kernel gates и native race. AWG/TCP PASS.
Control **3032/54/138**, phase0/tests **3032/54/138**, Docker **3030/54/140**,
errors0. Client Linux **1003/1/94**: bounded-mailbox BrokenPipeError;
voice: pointer/holding-state failure. Причины этих двух failures не установлены,
тесты не отключались/не исправлялись; не общий CI PASS. Точные jobs в отчёте.
Завершившийся R2 source `89e20a3437b2ba1b02f7d1649487579678158373`:
control **3030/54/135**, phase0/tests **3030/54/135**, Docker **3028/54/137**
(passed/failed/skipped), errors0; phase0/tests перепроверен по собственному логу.
Isolated-linux с15 authenticated, Client Linux, AWG/TCP/voice PASS; не общий CI PASS.
Внешние rendezvous/media и room provider заменены fixture; mailbox — byte relay,
не LXMF/node (L05), не live Telemost/installed/F-01. Сеть/DNS рабочего хоста не менялись.
D01 открыт; D02.1-R PARTIAL/NOT_RUN; L01/L01-R/D03/D04/D05 сохранены.
Identity/history/settings/keys/floors, версии и установленный baseline не менялись.
L03/установка/live/publication/Windows/fleet/iOS NOT_RUN. **STOP перед review L02.2.**

### Предыдущий checkpoint L02.1-R2 (историческое evidence)

Срез **L02.1-R2**, 24.10.2026: native status classification исправлена;
**review pending; родительский L02 PARTIAL. NEXT — review L02.1-R2.**
Вход: чистая актуальная `main` = remote
`323d49b09af57a809ba467f27e9c4650a97d7844`; checkout не откатывался.
[Текущий отчёт](releases/2026-10-24-linux-chat-mesh-l02-1-r2.md): настоящий
CONTROL4 limiter воспроизвёл отмену исправного поколения; malformed native route
терял DENIED до ChatBridge/ChatHTTP. Теперь BUSY — ограниченный отказ/перенос
проверки watcher, не healthy и не terminal; после освобождения очереди тот же
authenticated transport/lease. DENIED сохраняется до `access_rejected`, без HTTP
send/replay; terminal/protocol failure закрывает допуск и запускает прежний cleanup.
Review L02.1-R atomic RetainChat и обоих terminal-generation исправлений принят;
generation pin/refcount/drain→worker exit→flock ordering и IPC caps не менялись.
Локально 117 адресных Python/IPC, 66 dependent error/lifecycle, 13 root→UID/process
и 15 authenticated (включая прежние 13) PASS; native Go/race и 175 reference pins
PASS. R2 source **`89e20a3437b2ba1b02f7d1649487579678158373`** committed/pushed,
remote SHA проверен равным. CI19:17UTC: Auto/isolated-linux, Client Linux,
control/phase0/Docker, AWG/TCP/voice IN_PROGRESS, не общий PASS;
точные новые jobs — отдельно в текущем отчёте.
Завершившийся CI **предыдущего** source `6556a902c723a3ef73486733f090cea6f388d099`:
control **3015 passed / 54 failed / 133 skipped**, phase0/tests **3015 / 54 / 133**,
Docker **3014 / 53 / 135**, errors0; isolated-linux с13 authenticated,
Client Linux, AWG/TCP и voice PASS. Это не общее CI acceptance.
Mandatory suites и Auto/DIRECT kernel gates сохранены; full suites/неизменённые
kernel scripts локально NOT_RERUN. Посторонние failures не исправлялись.
Combined VPN publication→EXISTING_EXIT→OFF **NOT_RUN**, отдельный этап, не расширен.
D01 открыт; D02.1-R PARTIAL/NOT_RUN; L01/L01-R/D03/D04/D05 сохранены.
Identity/history/settings/keys/floors/reference pins и версии не менялись;
установка/live/publication/L03/Windows/fleet/iOS NOT_RUN. **STOP перед review L02.1-R2.**

### Предыдущий checkpoint L02.1-R (историческое evidence)

Срез **L02.1-R**, 24.10.2026: terminal native generation fencing/recovery исправлен;
**review pending; родительский L02 PARTIAL. NEXT — review L02.1-R.**
Вход: чистая актуальная `main` = remote
`878d2918ce4ba014bd7fe73a1f223753ce18748b`; checkout не откатывался.
[Текущий отчёт](releases/2026-10-24-linux-chat-mesh-l02-1-r.md): оба actual-native
отказа воспроизведены до исправления; после peer/Mux failure и asynchronous
bootstrap failure новый demand восстанавливает authenticated challenge/register/
duplex fixed-mailbox на одном новом транспорте, без idle45s/readiness expiry.
Проверяется native route; operation acquire атомарно удерживает только указанное
поколение через `RetainChat`, а не создаёт новое владение за старой lease.
Accepted Coordinator/refcount и все 175 Android106/reference pins не изменены.
Локально 580 Python/native/owner/mailbox, 13 root→UID/process и 13 authenticated
проверок PASS; Go/race и Auto/DIRECT isolated-kernel PASS. Точные source SHA,
повторные проверки и CI receipt фиксируются в текущем отчёте отдельно от L02.1.
Source **`6556a902c723a3ef73486733f090cea6f388d099`** committed/pushed,
remote SHA проверен равным. CI **18:42 UTC**: Client Linux, Auto protocol matrix,
TCP и readiness golden PASS; isolated-linux/authenticated gate, control,
phase0/tests/Docker, AWG и voice ещё IN_PROGRESS, не общее CI acceptance.
Законченный CI L02.1 `a2b105de49391928d4bb9c15c4d5ee2305085918`: control
**3015 passed / 54 failed / 127 skipped**, phase0/tests **3014 / 55 / 127**,
Docker **3013 / 54 / 129**, errors0. Дополнительный phase0 failure:
`test_ui_unavailable_server_ack_is_authoritative`, причина не установлена.
Mandatory suites сохранены; эти failures не исправлялись в L02.1-R.
Combined VPN publication→EXISTING_EXIT→OFF **NOT_RUN**, отдельный следующий этап,
не начат. D01 открыт; D02.1-R PARTIAL/NOT_RUN. L01/L01-R, D03/D04/D05 сохранены.
Identity/history/settings/keys/floors и версии не менялись; installation/live/
publication/L03/Windows/fleet/iOS не выполнялись. **STOP перед review L02.1-R.**

### Предыдущий checkpoint L02.1 (историческое evidence)

Срез **L02.1**, 24.10.2026: lifetime исправлен; **комбинированная приёмка PARTIAL**.
Вход: чистая актуальная `main`, remote проверен
`9b7418e2675d1e30787f491f8c924467835e7b05`; checkout не откатывался.
**Родительский L02 остаётся PARTIAL. NEXT — review L02.1.**
[Отчёт L02.1](releases/2026-10-24-linux-chat-mesh-l02-1.md): отдельная native lease
поколения плюс operation leases; idle45s/expiry/preemption/cancel/shutdown сохраняют
drain→worker exit→flock release. Исправлена typed-nil ошибка native IPC при отказе
Acquire. Старый host: authenticated challenge200 → leases0 → удержанный cleanup →
register UNAVAILABLE; новый: challenge/register/duplex fixed-mailbox, один transport.
Локально 556 Python/native + 24 owner/mailbox, 13 root→UID/process; native/race и 7
authenticated fixture checks; точные результаты и ограничения — в отчёте.
Fixture изолирован Go overlay: реальные native owner/IPC/FamilyTLS/Mux и Linux
lifecycle, но внешние rendezvous/carrier/broker и readiness-fetch заменены;
mailbox peer — байтовый relay, не установленный LXMF/node.
Полный VPN ON/publication/EXISTING_EXIT/OFF gate **NOT_RUN**: peer ещё не обслуживает
generic packet/DNS/owned-TUN health и broker lease lifecycle. Это не требование
live/private capsule. D01 открыт; D02.1-R PARTIAL/NOT_RUN; L01/L01-R/D03/D04/D05
сохранены. Версии/установка/публикация не менялись; L03 не начат.
Source `a2b105de49391928d4bb9c15c4d5ee2305085918` committed/pushed, remote SHA
проверен равным. CI срез **18:07 UTC**: новый authenticated gate, Auto/protocol,
root→UID/оба kernel gates, Client Linux, AWG/TCP, voice PASS. Mandatory control,
phase0/tests и phase0/Docker ещё **IN_PROGRESS**, не PASS; прежние failures не
объявляются исправленными. Точные source jobs — в отчёте L02.1.

### Предыдущий checkpoint L02 (историческое evidence)

Срез L02, 24.10.2026. Вход: чистая актуальная `main`, HEAD = проверенный `origin/main`
`b3301d07cb6e06f3c032b31a99f39e9535d3b21d`; checkout не откатывался.
**Review L01/L01-R принят пользователем в Linux source/native/root→UID/isolated-kernel scope.**
**L02 PARTIAL; NEXT — review L02.** [Отчёт](releases/2026-10-24-linux-chat-mesh-l02.md):
demand SERVICE_ONLY host, межпроцессный flock admission, manual/Auto drain→cleanup
и происхождение регистрации подключены в source. Полный authenticated native
API/mailbox OFF→ON→OFF через реальные Linux services ещё не доказан: положительные
host fixtures используют synthetic lane; отдельный process gate — реальные idle workers.
Это не L02 DONE, не установленная функция и не разрешение начать L03.
Source `383ef3606aaa4dbd29f0c7c0f755e6faec6e309f` pushed/remote-verified.
Локально 354 + 82 адресных Python/native и 13 root/process/UID PASS; Go/race и
DIRECT/Auto isolated kernel PASS. CI Auto/new gates/Client Linux/AWG/TCP/voice PASS;
полные control и phase0/tests FAIL (каждый 3015 passed / 54 failed / 120 skipped),
Docker FAIL (3013 passed / 54 failed / 122 skipped). Точные CI jobs/статусы —
в [L02](releases/2026-10-24-linux-chat-mesh-l02.md), не перенос с прежнего SHA.

Принятое evidence L01-R (точные SHA не заменяются новым checkpoint):
[L01-R](releases/2026-10-24-linux-chat-direct-l01-r.md): runtime0711 при unit umask0077,
проверенный registration route без импорта EXIT response в root authority, настоящий
TCP/TLS fatal alert остаётся DENIED до ChatHTTP, без fallback. Before/after записаны.
Локально: 145 Python/native + 49 mailbox/owner, 6 root→UID checks, шесть Go/race
packages и isolated DIRECT kernel PASS. Root→UID не является installed acceptance.
Source `4fab7b66d27d8a0a5306a6a923c120f023389218` pushed/remote-verified:
Client Linux, Auto/protocol/root→UID/оба kernel gates, AWG/TCP PASS. Текущий voice job
PASS, но прежние GTK failures не исследовались и не объявлены исправленными/flaky.
Control/phase0 full pytest FAIL; Docker: 2980 passed / 53 failed / 115 skipped, exit1.
Обязательные suites/negative gates сохранены; точные jobs и SHA — в отчёте L01-R.
D01 открыт, D02.1-R PARTIAL; full-suite/GTK voice failures вне scope.

Историческое положительное evidence L01 ниже сохранено только для своих SHA:
[L01](releases/2026-10-24-linux-chat-direct-l01.md): ChatOwner/daemon используют отдельный
root DIRECT endpoint, fixed chat API и mailbox только из root-проверенной регистрации.
Native underlay bind/mark до connect; SYSTEM fallback отсутствует в этом пути.
UID/device/chat-key/sequence/expiry и AF_UNIX relay ограничены; VPN owner не создаётся.
Локально: 141 chat/admission/D03/package + 49 mailbox/owner PASS; Go/race и isolated
kernel с synthetic TLS peer PASS. Installed/live, L02 и полные установщики NOT_RUN.
`bff34eb` CI: Client Linux/Auto protocol/AWG/TCP PASS; full control/phase0/Docker и voice FAIL.
Первый новый kernel gate FAIL; harness-only `edc79c2` переносит test-worker из writable
`/opt` под trusted `/root`, не ослабляя admission: Auto bridge/isolated DIRECT kernel CI **PASS**.
На `edc79c2` phase0/tests FAIL; Docker: 2976 passed / 53 failed / 109 skipped,
exit1; другие filtered jobs NOT_RUN.
Evidence и разные SHA — в отчёте; старые counts не переносятся.
[D03](releases/2026-10-24-chat-http-terminal-d03.md) и [D04](releases/2026-10-24-auto-lifecycle-d04.md) review accepted; D02.1 collection/import
isolation и D02.2 public-reference приняты. Dependency-части D01.1/D01.2 приняты;
их PARTIAL и общая CI-приёмка D01 не закрыты.
[D05 review accepted](releases/2026-10-24-desktop-provider-d05.md): target/selected-next, проверенное
assignment и applied metadata используются Linux NormalOwner/Platform/GuardedHost.
Legacy gateway_id неизвестен; assignment только после fresh fetch/floor/readback/inspect,
applied только после guard.ready. Refresh не вызывает configure/apply/close; IPC не расширен.
Clean export: provider/model/platform/native/catalog 162 PASS, ownership/service/chat 213 PASS,
0 failures/errors/skips. Native normal-stdio проверен с синтетическими материалами;
installed/live/F-01 и dynamic fleet не приняты. Code `c53265d` pushed/remote-verified:
Auto bridge Linux/AWG/TCP PASS, Client Linux job завершён PASS (перепроверен в L01).
Control/phase0: каждый 2930 passed / 54 failed / 0 errors / 107 skipped, exit1;
Docker: 2929 passed / 53 failed / 0 errors / 109 skipped. Voice GTK Return gate FAIL, причина неизвестна; не исправлялся и не объявляется flaky.
D04 evidence уточнён: на `b41e1ad` одинаковый набор 54 failures в control/phase0/Docker;
docs-only phase0 `3f9854a` завершился FAILURE отдельно от code SHA. D01 остаётся открыт.
Review коррекции D02.1-R и [fleet-документации `1725656`](releases/2026-10-24-desktop-fleet-boundary.md)
завершён. [Граница desktop/fleet](desktop-architecture.md#desktop-fleet-boundary) сохраняется:
D05 реализует только внутреннюю Linux-границу; W01/W02, UI/миграция и fleet gates остаются отдельными.
[D02.2 DONE, review принят](releases/2026-10-24-rns-reference-d02-2.md): public mappings
с прежними accepted pins; clean export 49 passed / 1 прежний skip, collection 3051/0 errors;
public verifier и настоящий `--capsule` (2073 files + APK/native hashes) PASS.
Исторические CI counts `da8670e` сохранены в отчёте, не переносятся на D05.
[D02.1-R PARTIAL, коррекция принята review](releases/2026-10-24-historical-runner-d02-1-r.md): bootstrap vector и original API
добавлены; retained inputs явно перечислены, preflight/snapshot fail-closed. Чистая collection
3031/0 errors, адресные 110 passed. Полный исторический запуск **NOT_RUN**: у delivery-check,
Java runtime/classes и трёх JARs нет подтверждённых artifact pins; существование файлов не PASS.
Collection/import isolation D02.1 подтверждено review. Комплектность исторического replay ещё
не закрыта. Полные suites локально не запускались; старые CI counts ниже — только `6a0a982`.
Code `85b29da` pushed/remote-verified; по отчёту D02.1-R control/phase0/tests/Docker build
были IN_PROGRESS без full pytest counts; в документационном checkpoint CI не перепроверялся.
[D02.1 DONE](releases/2026-10-24-fixture-boundaries-d02-1.md), code `6a0a982`: чистый export —
collection 2977 + 9 errors → 2996 / 0 errors; helpers/import/runner — 75 passed.
В трёх CI окружениях collection errors = 0; полный pytest остаётся FAIL (56 failures):
control/phase0 2834 passed, 106 skipped; Docker 2832 passed, 108 skipped. Остались capsule/
reference, nginx contract, expiry, privacy и socket failures; не исправлялись.
Шесть исторических overlay-файлов сохранены и отделены; исторический runner в D02.2 не менялся.
[D01.2 PARTIAL](releases/2026-10-24-control-ci-d01-2.md): на pushed `07b52e3` Python3.13
strict imports и адресные gates PASS в control/phase0/tests/Docker tests-stage;
Docker root 22 passed, адресные 59 passed. Каждый полный suite прерван: 9 collection
errors owner_handoff/prepare, exit 2 (D02). Общий CI FAIL; последующие GUI/package/cargo/
failover проверки не выполнены. Runtime/fixtures/collection policy не менялись.
[D01.1](releases/2026-10-24-desktop-ci-d01-1.md): локальные реальные импорты PASS,
адресные 59 passed; локальный desktop 877 passed / 64 skips / 0 failures/errors.
На pushed `26f71d6` imports/адресные CI PASS; полный suite FAIL: отсутствующая RNS capsule,
в AWG также Auto lifecycle assertion. Подробности и точные counts — в отчёте; продукт/fixtures не исправлялись.

## Цель и порядок работы

Довести существующие Linux GTK4/libadwaita и Windows WinForms до функционального
и визуального соответствия принятой Android beta106-recovery, включая мессенджер,
голос, уведомления, объявления, настройки, приглашения, диагностику и обновление.
Сохранить полезные desktop-функции, модель привилегий и пользовательские данные.
Общий PARITY PASS не достигнут; процент по объёму исходников не является приёмкой.
Работа идёт отдельными ограниченными задачами из [PLAN](PLAN.md), без автоперехода.

## Android reference / exact pins

- APK: `FamilyConnect-0.1.18-beta106-recovery.apk`, принятый native105.
- APK SHA256: `242855c43e889e708234ce2f687fa02d37bccb1eee408904f09216b6abd8f020`.
- Signer SHA256: `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
- native105 SHA256: `37ba4fac656811dd979688a274f45aed85a3aa567f1fafb3987a81c020fa91f1`.
- Точные APK/source/native inventories и 175 общих pins: [reference manifest](../clients/shared/android106-reference.json).
- Source capsule: `state-client-build/owner-diagnostic106-20261022/android-source`;
  delivery: `state-client-build/owner-diagnostic106-20261022/delivery/`.
  Inventory 2073 файлов: `8574228fc809fdbd67b3d92680e09c979fe930599a47e4ed1b47fd30f872ed0c`.
- [Chat pins](../clients/shared/android106-chat.json), [UI contract](../clients/shared/android106-ui.json),
  [feature matrix и исходные наблюдения](releases/2026-10-23-desktop-parity106.md#desktop_feature_parity).
  Android-код в корне и лабораторные fixtures не заменяют принятую source capsule.
- Принятая база: P1 effective RS32/32 + согласованный CREDIT128, P0/LEGACY64,
  health102, cancel/timeout103, reorder104, pressure105, bounded JSON-export106.
  RS согласуется до Family TLS, Mux ALPN не подменяет RS; профиль зависит от обоих концов.

## Состояния поставки — не смешивать

| Уровень | Подтверждённое состояние |
|---|---|
| SOURCE | Frozen Linux candidate source `1c2beb6`, system source `053c4e5`; R2 принят. Freeze не меняет product source. |
| LOCAL TESTS | R2 targeted197 PASS, desktop1191 PASS/84 SKIP; isolated root→UID/native179, Auto18/DIRECT/lifetime15/combined3 PASS. Это прежние receipts, не новый запуск. |
| CI | R2 Linux/AWG/TCP/package PASS; control/phase0/Docker54/54/54 failures — отдельный долг, не общий CI PASS. [Точные jobs](releases/2026-10-25-linux-queued-connect-close-l04-1-live-2-r2.md). |
| BUILT | Exact internal Linux `0.2.12~l03.2.5` AppImage/DEB frozen без rebuild/repack; IDs/hashes в [manifest](releases/2026-10-25-linux-awg-tcp-beta-freeze.json). Не полный parity release. |
| INSTALLED | L04.1 DONE/review accepted в installed Linux AWG/TCP scope; disposable guest удалён, workstation rollout NOT_RUN. L04 IN_PROGRESS только из-за L04.2; MESH/Auto/messenger NOT_RUN. Windows runtime не принят. |
| PUBLISHED | Candidate internal/unpublished; signing/publication NOT_RUN. Последние документированные public Linux0.2.11 / Windows0.2.15 и invitation/download/catalog links не менялись; в freeze не перепроверялись по сети. |

## Продуктовый baseline: phase22

[Phase22, 24.10 08:53 CEST и остановка 08:55](releases/2026-10-23-desktop-parity106.md#linux-user-chat-admission-and-existing-exit-handoff-2410-phase22).
Linux ChatOwner подключён к **EXISTING_EXIT** через отдельный UID/device-bound root
chat endpoint; fixed API/mailbox используют существующего MESH owner, не второй VPN worker.
**SYSTEM — обычная маршрутизация ОС, НЕ protected-underlying DIRECT.**
Общий Go service-only adapter существует; **Linux host lifecycle ещё NOT_INTEGRATED**.
Требуется **одно активное владение транспортом**, не вечный PID: worker имеет свой lifecycle.
**Windows public/native chat endpoint на baseline — NOT_INTEGRATED.**

Границы доказательств phase22:
- Реальные Unix framing/SO_PEERCRED/SCM_RIGHTS, 64KiB duplex/half-close, cancel,
  deadlines, capacity и FD cleanup проверены в изолированном same-user fixture.
  Ожидаемый root UID заменён UID fixture; установленная root/user граница NOT_RUN.
- Native lane/session в host fixture синтетические: это не media/TUN/gateway egress PASS.
- Реальные ChatOwner/encrypted store, disposable identity proofs и локальные ChatAccess
  handlers: register/revoke/reopen. Pending node не выдавался за доставку сообщений.
- 175 общих / 2073 capsule checks и шесть chat pins — исторический PASS phase22;
  в D00 они не запускались. Наборы PASS перекрываются, их числа не суммируются.
- Phase22 не снимала новые UI screenshots. Имеющиеся Android GPU/GTK captures —
  частичные доказательства, не полный visual parity и не Windows runtime acceptance.
- [Source checkpoint](releases/2026-10-24-source-checkpoint.md) отдельно описывает
  последующую EOF/whitespace подготовку; старые hashes не выданы за тест нового исходника.

## Артефакты и ограничения обновления

Текущий Linux AWG/TCP Beta — exact .5 в [freeze manifest](releases/2026-10-25-linux-awg-tcp-beta-freeze.json).
Ни установки, ни rollback в freeze нет; matching full pair/root reinstall допустим
только отдельным решением при idle/confirmed cleanup, с сохранением state/floors.
L08 upgrade не принят; legacy updater не объявляется full-bundle updater.

Исторический phase22 component-r18 (не текущий beta candidate): все три файла в
`state-client-build/desktop-parity106-20261024/`:
`bridge-linux-r18/fc-mesh`, `bridge-windows-r14/fc-mesh.exe`,
`mesh-system-r18/FamilyConnect-MESH-system-amd64.tar.gz`.
[Точные SHA256, inventory и требования](releases/2026-10-23-desktop-parity106.md#internal-artifacts-and-upgrade-boundary).
Component-r18: 98 members, 22 root / 4 common modules; Linux x86_64 systemd254+,
resolved/iproute2/polkit/TUN/Python3 и согласованный GUI. Это НЕ полный AppImage/DEB.
Новых update-manifest/Authenticode/driver signatures нет; подписи не взаимозаменяемы.
Linux updater принимает **legacy six-file archive**; переход на полный bundle ещё
требует реализации (L08). Полный внутренний пакет (L03/W10) предшествует установленной приёмке.
Identity/history/settings сохранены в локальных fixtures, но installed upgrade ещё не принят.
D00 ничего не устанавливает: runtime rollback не нужен; прежние установки/state сохраняются.

## Блокеры / оставшаяся реализация

- D01.1/D01.2 PARTIAL, dependency gates приняты; review D02.1 collection/import isolation и D02.2 public-reference принят. D02.1-R historical replay PARTIAL/NOT_RUN. Остальные CI failures требуют отдельной оценки, не расширяют L01 автоматически. Общий D01/CI acceptance открыт до полного PASS.
- D03/D04/D05, L01/L01-R, local L02/L02.2 и L03 review accepted. W01/W02, L07/W09, L08/W12 не закрыты; очередь не запускается автоматически.
- D03: [исправление и детерминированные регрессии](releases/2026-10-24-chat-http-terminal-d03.md)
  сохраняют HTTP/TLS/invalid_response/timeout/cancellation при ошибке teardown.
  Это локальная логика с synthetic transport, НЕ installed/live delivery PASS;
  review D03/D04 принят; D05 не расширяет fixed chat DIRECT/service-only scope.
- L04.1 DONE только в installed AWG/TCP scope. Parent L04 и L04.2 PAUSED /
  NON-BLOCKING DESKTOP ENGINEERING по owner decision27.10; L04.2 не DONE.
  Installed MESH/Auto, L05 messenger и test-device teardown остаются незакрытыми,
  но не блокируют ANDROID-CONTROLLED-BETA и не запускаются автоматически.
- W01–W12: Windows native↔broker, Auto/recovery и продуктовые функции, затем полный installer,
  installed runtime и upgrade. Cross-build/Wine/headless не заменяют Windows TUN/driver acceptance.
- R01: конечные точные пакеты и проверки их установки/обновления; публикация отдельно.

## Неизменные ограничения

- Не пересобирать/публиковать Android106, не трогать активные MESH-сессии и общий gateway ради desktop.
- P1 разрешён только трём согласованным Android-устройствам; desktop identities не считаются
  разрешёнными автоматически. Точечная политика требует отдельного операторского решения, не global/FIELD grants.
- Не копировать Android identity/Support ID на ПК; сохранять старые ключи, историю, настройки,
  активацию и `familyconnect://`. Не ослаблять TLS/Family/roles/revocation/expiry/floors/directory.
- Не включать Q1/TLS packing/FEC/QUIC/FIXED4M или исследовательские SACK/timebase patches.
  Не выпускать неподдерживаемый пользовательский трафик напрямую ради smoke.
- Live-бюджет при отдельной приёмке: до32MiB прикладных данных на ОС, нормальный Wi-Fi/Ethernet;
  media overhead/фон учитывать отдельно. Android field check не блокирует локальную desktop-разработку.
- Будущие emulator checks: KVM + подтверждённый host NVIDIA GPU, 2 cores, CPUQuota150%,
  максимум180s, stop85°C CPU/80°C GPU; без SwiftShader fallback/idle emulator.
  [Тепловой инцидент и ограниченный GPU capture](releases/2026-10-23-laptop-thermal-diagnostic.md).
- Проверки выбирать по изменённому риску и обязательному gate; не повторять весь исторический набор
  без причины. Source push ≠ CI PASS ≠ installation ≠ publication. [Правила](../AGENTS.md).
- Capsules, приватные доказательства, бинарники, ключи и state остаются локально, вне Git.

## Другие незакрытые обязательства — не текущие задания

- Закрытая Android-группа: физические tester updates106/P1 и cold-bootstrap ещё не подтверждены;
  Volgograd96 положителен, но не равен106/P1/Краснодар. [Cohort report](releases/2026-10-23-tester-p1-cohort.md).
- RU SSH banner timeout / legacy Docker peer-worker unhealthy и неизвестные RU live counters:
  [операционный follow-up](releases/2026-10-23-vpn-health.md), без диагностических рестартов.
- Local storage: сохранить symlinks; оставшаяся миграция live project/Codex и reboot automount —
  отдельное maintenance после остановки writers. [Receipt](releases/2026-10-07-local-storage-migration.md).
- Fleet/control5.2–5.6, длинная AWG/TCP/Android приёмка, vault signing/consumer audit/external backup/full DR,
  gateway recovery6, Home Gateway, multi-carrier после FIELD-1, Django7.1/payments,
  licensing/private reporting/Windows publisher signing/iOS/macOS — [отложенные обязательства](PLAN.md#other-obligations).
  Они не закрыты D00 и не добавлены в desktop scope.

## История и один следующий шаг

[STATUS до D00](STATUS.history-2026-10-24.md) и [PLAN до D00](PLAN.history-2026-10-24.md)
сохранены целиком; старые NEXT/ACTIVE/checkpoints — история, не параллельные задания.
[Отчёт D00](releases/2026-10-24-desktop-parity106-d00.md) фиксирует сохранность и границы.
**STOP после CHAT-UX-1. NEXT — review CHAT-UX-1 перед установкой нового UI-кандидата владельцу.
L04.2/full L05/TCP HTTPS diagnosis/teardown/signing/publication не начинать.**

Этот прежний STOP сохранён как история. **Текущий STOP27.10: readiness checkpoint
завершён. NEXT — только фактические ANDROID-CONTROLLED-BETA launch blockers;
Linux L04.2 PAUSED / NON-BLOCKING DESKTOP ENGINEERING.**
