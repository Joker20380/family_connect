# Recurrent tunnel closures / beta90 — 19 October 2026 UTC

## Result and acceptance boundary

**A demonstrated server failure-amplification mechanism is fixed and deployed.**
Bootstrap signaling WebSocket close1011 made the original gateway cancel its root
context, destroying otherwise independent dedicated sessions and exiting. The
replacement recovers only this exact seed failure, serially, with a three-retry
budget and30-second delay. It does not claim to repair the upstream signaling
service, media/ACK loss, or every user-visible reconnect.

Normal same-key beta90 removes beta89's extended performance trace, preserving
beta88 recovery and all12 normal native libraries. Trace removal is **not evidence
that instrumentation caused the closures**. No speculative health, ICE, window,
SACK, RTO, credit or batching change is included. Both rejected throughput
experiments remain rejected.

Source checkpoint: pushed `dddc3347db5b02896c123488f2e5e0292ff2b7a7`, branch main,
origin `Joker20380/family_connect`; this task's scoped fixture/docs delta is local,
not pushed. Build inputs are sealed accepted capsules, **not a main checkout**.
See [evidence](2026-10-19-tunnel-restart-fix.evidence.json) and
[hash-pinned fixtures](../../tests/fixtures/tunnel_restart/README.md).

| Requested result | Outcome |
|---|---|
|FIRST_CLOSE_CAUSE|Multiple: dedicated retry exhaustion, Android signaling read close, seed WS1011.|
|RESTART_INITIATOR|Native/client recovery for dedicated loss; bootstrap main cancels root on seed failure, then systemd restarts process.|
|FALSE_HEALTH_RESTART|NOT_DEMONSTRATED in retained events;43 successful probes, no failed series.|
|MEDIA_OR_SERVER_LOSS|Head gap and signaling closures confirmed; upstream source/location unknown.|
|TRACE_OVERHEAD_EFFECT|UNKNOWN; removed extended instrumentation without attributing the failures to it.|
|TARGETED_FIX|Bounded exact seed1011 containment, built/tested/deployed.|
|REPEATED_RECOVERY_REGRESSION|Local PASS; repeated natural failures of final pair not observed.|
|PHYSICAL_OBSERVATION|Stable bounded PID/TUN samples, DNS/full HTTPS and same-identity READY PASS; no natural1011 during passive window.|
|SIGNED_APK_OR_SERVER_FIX|Normal signed90 installed over89; server candidate hash verified loaded.|
|NEXT_HOST_COMPARISON_INPUTS|Unchanged IPv4 pair pinned; comparison NOT_RUN.|
|FINAL_RESULT|PARTIAL: proven cascade fixed; eliminating all recurrent disconnects is not physically accepted.|

## Evidence preserved before any new connection

The already saved phone export was copied without Connect, bulk, UI-dump or
unlock bypass. SHA256
`a316aa7e24f44ca69b3af874806f39329605992334ac31c1a609d6253021f9d2`,406017bytes.
Its current ring is89; the embedded older incident is88 and is not a new89 failure.
The ring ends at a successful16:14:54 READY. At first current readback16:36:53,
the phone VPN/ConnectionService was already off; PID25908 still existed. Android
exit history has the14:40 installation exit, not a later app-process restart.
Historic TUN IDs and complete service-instance history are not exported: logical
native/session changes must not be reported as verified process or TUN restarts.

NL executable readback16:50:11: accepted `4b722d…8fab7`, PID3172670,
invocation `01a4b88584ef4cc99e2cac52232095d8`, start16:16:31,NRestarts3.
No rejected SACK-hole/read-alignment candidate was loaded.

Bounded server evidence:600-row capture requested15:28–16:17, actually covering
16:02–16:16 because of the cap; two targeted120-row intervals around15:54 and16:00;
three protected fatal receipts plus bounded renewal-operation records. Three
legacy fragmented JSON records were not parseable. Raw evidence and parser errors
remain protected in `state-client-build/tunnel-restart-20261019/`; no payload,
identity database, private keys or raw diagnostic export is published here.
Absence from these bounded records does not establish absence of an event.

## First causal boundary, not cleanup

All times UTC. Android recovery success means READY; application success is
reported separately. Cross-host timestamps order coarse events, not one-way delay.

| First event | Initiator and closure | Recovery and application evidence |
|---|---|---|
|15:29:11 phone history|Prior task's gateway rollback at15:28:56|Operator A/B/A event; excluded from current recurrent-failure diagnosis.|
|15:54:38.806 NL|Dedicated ReliableStream retry exhaustion, head3984,next3992,mask254,headretry8; gateway PID3142658 survives|Phone same-session exhaustion15:54:47.754; retry15:54:51.598→READY15:55:15.906 (24.308s); VPN DNS OK15:55:21.610. No matched full HTTPS receipt in this export.|
|16:00:24.191 phone|Signaling read error / SIGNAL_WS_CLOSE, not health or a prior PC Disconnected|Retry16:00:25.738→READY16:00:53.131 (27.393s), subsequent DNS OK. NL dedicated exhaustion16:00:33.401 is later; gateway process survives. Exact Android WS close code unknown.|
|16:11:15.817 NL fatal receipt|Seed SEED_READ/SIGNAL_READ, typed WS_CLOSE1011, context ACTIVE, transport not already closed; main cancels broker root and exits1|Independent session cancelled16:11:15.811; phone exhausts16:11:26.998. Attempts16:11:30,16:12:40, then READY16:14:54.640 (204.259s from first attempt). Export ends there: no post-READY DNS/HTTPS proof.|
|16:12:02.092 NL|Same seed1011 in replacement PID3169757, invocation3d5e86…; lifetime16.118s|Systemd30s restart. No renewal/operator mutation accounts for it.|
|16:16:01.370 NL|Same seed1011 in PID3170265, invocation85f5b2…; dedicated session cancelled while lease valid|Systemd restart to3172670. Phone aftermath outside preserved export.|

The seed fatal receipts retain credential headroom8425/8378/8139seconds: expiry
was not the initiating cause. Normal renewals15:31,15:46,16:01,16:16 were NOOP,
files changed0/restarts0. NRestarts is corroborative, not the sole restart proof.
The millisecond ordering of broker cancellation and final fatal receipt reflects
concurrent teardown; typed first seed failure, not the final receipt timestamp,
identifies the trigger.

The15:54 gap is real: NL ACKbase3984/mask254 and phone receive-head3984 with seven
buffered blocks agree. Missing head/return-path behavior is not localized to a
particular host, network segment or provider. This task does not tune retries to
hide it.16:00 Android signaling failure is also not repaired by the seed-only fix.

## Client health / PeerConnection / instrumentation audit

Retained events contain **43 DNS_PROBE_OK and no failed health series**. The native
failure branch runs before the periodic DNS probe. Thus these closures are not
demonstrated false three-probe health restarts.

The actual probe binds a newly selected VPN Network and source10.79.0.2, with a
fresh-Network equality check and cancellation check at completion. A serial
ScheduledExecutor prevents concurrent scheduled probes. Cleanup cancels and
discards the checker; replacement creates a new checker. Valid DNS rcode0/3 is
accepted; timeout/malformed/no Network/cancellation collapse to false, so that
boolean alone cannot diagnose future incidents. No unobserved semantic rewrite
is justified by this ring.

The apparent destinations1.1.1.1/9.9.9.9:53 are **not independent resolver paths**:
wholedevice intercepts DNS and sends FamilyMux QueryDNS; gateway Mux uses its
configured DNSUpstream or the first valid nameserver in its `/etc/resolv.conf`,
over TCP. These probes cannot bypass the VPN. Media bytes/keepalives are not
counted as successful DNS/HTTPS. No VALIDATED requirement is introduced.

Accepted native `onSubscriberState`/`onPublisherState` treats Disconnected,
Failed and Closed as terminal. There is no preceding transient PC event in the
retained first-failure chains. A local six-case callback reproducer documents
the existing terminal behavior even after a later Connected callback, closed
Send rejection and generation-local callbacks. **No transient-state tolerance
is shipped**; it would require separate causal evidence and bounded semantics,
not blindly restarting ICE or resurrecting Closed.

Beta89's bounded performance sampler/export is absent from90. The available
phone was already disconnected before fresh observation; there is no matched
live89/90 CPU/GC/scheduling/closure-rate comparison. TRACE_OVERHEAD_EFFECT remains
UNKNOWN, not “fixed because trace was removed.” Ordinary bounded diagnostics and
minimal gateway first-cause events remain. No full profiler was added.

## Targeted server delta and tests

`gateway.patch` changes only bootstrap-broker main and adds seed_recovery.go plus
tests on accepted inventory
`aeeb6755bd235160127cfed67da4a870ae340cfebe89fc6d0f937908607d9483`.
Classification requires seed_closed + SEED_READ + SIGNAL_READ + WS_CLOSE1011 +
ACTIVE context + not previously closed + no parent cancellation. Non1011, auth,
publication, initial readiness and cancellation failures retain fail-closed behavior.

Each old SeedManager.Run returns, closes and joins its resources before a fresh
seed attempt; the independent broker parent remains alive. Dead publication is
withdrawn and a replacement is published only after READY. Budget is **three
replacements per process lifetime**, delay30s; exhaustion returns to the existing
fatal supervisor. Original four-hour process context, credentials, directory,
lease and floor bounds remain. No auth lifetime is extended to make retry work.

- 401 distinct Go test cases including subtests PASS,25 opt-in SKIP across affected
 bootstrap/broker/session/carrier and reliable packages under race. Initial
 TestSharedTimestampContract failure was a missing unchanged vector in the
 source capsule; retained, supplied and affected packages rerun successfully.
- 169 Android JVM checks/22 suites PASS, covering existing repeat recovery,
 cooldown, requested-connect ownership, manual Disconnect/revocation and floors.
  Public platform CI was not run for this private owner update; it is not a
  public-release/CI acceptance claim.
- Actual VpnHealth with local Android Network stubs:10 scenarios PASS (one pytest),
 including delayed probe with synthetic useful progress, blackhole, malformed,
 missing/stale/fresh Network, cancellation/reuse and worker cleanup. This does
 not substitute for Android routing/field acceptance.
- Six extra unchanged PeerConnection cases PASS in a separate test-only source
 copy; no extra test code or behavior was added to the deployed source inventory.
- Hash-pinned patches reproduce the exact built inputs in a fresh directory.
 No live fault injection, gateway outage test, fallback or security bypass.

## Separate scheduled-renewal interruption during this task

Normal renewal started17:01:57 and stopped the old NL service17:02:07, **before
this task's deploy**. Operation `scheduled-1792429318-4cbbcf5dda81698b` committed
new security materials, then failed IO_OR_TRANSPORT_FAILURE17:04:55 (exit75 at
17:05:26). Coordinator RECOVERY_REQUIRED; equal committed RU/NL snapshots were
confirmed read-only. NL retained a consumed start-intent but was inactive, so
blind replay of the ordinary resume would not repair that boundary.

One guarded forward completion of **that exact committed operation**, under the
coordinator/node locks, started the unchanged original binary with current
committed credentials, then completed normal controller recovery. No deletion
of start-intents, floor rollback, authority migration or old recovery bundle.
COMMITTED; NL restarted17:15:22; strict TLS/runtime/publication PASS17:16:50.
Current limiting material expiry21:02:05UTC at readback. Scheduled renewal stays
enabled. Underlying transient management I/O cause is not uniquely established;
this was an operational repair, **not a permanent renewal transport fix**.

## Build, application and rollback

| Artifact | Exact value |
|---|---|
|Previous installed89 APK|`b6ab744740726676dca8f51a73460db82b435c719828af14e6564c764ed11856`|
|Previous89 native|`3ca3119ac12c9a3a61b5ebb1ee0244650db39dc36743e355d35bf523b53ef992`|
|Original accepted gateway / rollback|`4b722d2d7f2159b96953e27777494bf596768f860ee8da7e634fb1100b08fab7`|
|New gateway binary|`b9ae880731517753e456637e52dcc421b9f7d7b881b400c856989ae93193e9ba`|
|New gateway source inventory|`4722b7353ba93209657f66b45c47874915362f1fbe732845ec61745abdb673e6`|
|Beta90 APK / code90|`68cbcccfb5adf8656e8203436126330e780de099670ee2031d71019baadc3e9a`|
|Restricted native90, identical88|`dd722eada0da7c890a8d71a72099cba5d0bbac1ce73377bbdbc8e7b85d820c23`|
|Unchanged signer certificate|`67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`|

Existing private APK:
`state-client-build/tunnel-restart-20261019/delivery/FamilyConnect-0.1.18-beta90-stability.apk`.
Package `com.familyconnect.app.friends`, Android12+/arm64,16KiB alignment checked.
Built from sealed88 recovery ancestry (Java unchanged except version), normal
89→90 `adb install -r` at17:06:57.261UTC; same UID10283 and installed APK/native
hashes verified. No uninstall, clear data, activation or new keys. The phone was
disconnected before and after installation. Old signed APKs are untouched.
After the owner's normal Connect, canonical identity/key/Support ID comparison
and a new beta90 READY pass; no new registration is inferred merely from UID.

The first staged gateway switch was **aborted before mutation** on
RUNTIME_CHANGED_RECHECK: invocation changed during approval wait. Its response
and unchanged binary were inspected before refreshing the preflight; no blind
live retry. Guarded ordinary restart finally applied candidate17:50:13.449UTC,
PID3230136, invocation `43a426928faa4675aa975e8b06d71251`, same unit/argv/profile.
Strict TLS/runtime/material/publication readbacks PASS17:55:30 and18:11:21, same
PID/invocation, loaded hash and NRestarts0. Phone90 VPN/service active at18:11:21.
No API, admission,
directory format, owner handoff or canary routing change. A real service restart
can interrupt existing sessions; zero downtime was not promised.

Server rollback uses the retained original4b executable through the same guarded
ordinary operation with **current** credentials/floors, not a historical profile.
Android removal/rollback needs a normal same-key code>=91 build if required;
never install88/89 over90 or clear data. Public release, invitation page, catalogs,
mass distribution and tester beta88 delivery are unchanged. No push in this task.

## Physical scope and next comparison

At17:55:31 installed90 was verified but VPN/ConnectionService was off. Owner was
asked once to enable MESH normally after evidence preservation. Passive capture
17:56:20–18:01:22 contains31 samples of the same phone PID19388 and TUN interface
tun1/ifindex563; gateway PID3230136/invocation43a426… also unchanged. Journal cap
4MiB was not reached; no natural seed1011 event during this window. This is
sampled continuity, not proof against arbitrarily short unobserved transitions.

One small existing HTTPS control at18:07:34 passes through full-UID Android TUN,
VPN DNS and the current MESH gateway: HTTP/1.1, identity, TLS verify0, HTTP200,
215bytes in2.803211s full request.17 current-PID TCP socket samples match the
destination443; observed exit is NL. Body SHA256
`32c629fbd7f9f66e21db1b3a5c4d6c7cb8bcc33c33cc7de1e1b1f245d0231681`
is this response's evidence, not an independent origin hash or pure RTT. No
direct fallback, retry, bulk or intentional fault; temporary phone files removed.
Identity/key/Support ID and new90 READY comparison PASS. No seed1011 occurred
under the observed transfer, so physical containment/repeated-loss and overnight
acceptance remain outstanding, not implied by this successful first control.

Reproducible next-host inputs: exact90 APK/native + exact deployed gateway above,
same signer, accepted-source inventories, same default IPv4 MESH settings, no
read-alignment/SACK-hole/performance overlay; verify loaded executable and real
TUN/Mux route before a small control. Compare unchanged pairs and natural
signaling/retry conditions, not the best single speedtest. Existing agreed
Cloudflare HTTP/1.1 fresh-connection/identity-encoding endpoints and bounded
32MiB-per-variant/180s-per-request limits remain; no endpoint refusal bypass.
Another hosting run is **NOT_RUN**, no server bought or production exit moved.
Amsterdam IPv6 remains DEFERRED_BY_OWNER; SPb/IPv6 NOT_RUN and outside this task.

The remaining missing facts are a matched natural1011 while an active dedicated
connection transfers through the repaired process, repeated real recovery/data
checks after it, and the cause/location of the independent media/ACK and Android
signaling failures. A short quiet interval cannot supply those facts.
