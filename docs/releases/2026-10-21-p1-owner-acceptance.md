# P1 owner acceptance after15166ff — speed preserved; lifecycle continuation

## Superseding readback22 October

The private101 completion receipt and fresh USB readback establish101/P1 as the
starting state; the in-progress/P0 text below is an earlier checkpoint. New owner
disconnections are handled in the [22 October incident](2026-10-22-owner-disconnections.md),
not as a new speed audit.103 deadline candidate signed and installed owner-only;
active RS failures remain unresolved, no field/public rollout. Historical speed
and incomplete lifecycle observations are retained, not retroactively marked PASS.

## Authorized lifecycle continuation101 — in progress

Prior speed result remains **SPEED_GAIN_CONFIRMED_BOUNDED**, not reset by missing
lifecycle history. Current decision is **LIFECYCLE_ACCEPTANCE_PENDING**.

Exact100/f631 parents verified17:46UTC.101 is installed owner-only, same
package/signer/UID10283 and data; bootstrap96/1011, profiles and recovery unchanged.
Source:`state-client-build/p1-lifecycle-101-20261021/android-source`.
APK:`state-client-build/p1-lifecycle-101-20261021/delivery/FamilyConnect-0.1.18-beta101-lifecycle.apk`.
SHA256:`3c023e39d95e29fe0561dc462e28f1e643b9e14558cf49700d58df528b2963d9`.
Native:`97d0bf793f8c4bb9975f32579f19369df0e7201786609ab9f46decdea3fec263`.
Source inventory:`bffc42e8c5f15a96add422e8c7ec9f2352fef0a472608dea8f6c4df92c729143`.
203 JVM tests pass; Go race tcpforward/sessiondiag/wholedevice/reliablestream/
familysession pass. Both-window live-worker cancel/neighbor/cleanup test repeated5
times passes. Full platform CI remains NOT_RUN. Preparation/build failures were
local (different gateway counter layout/incomplete Java projection); corrected
before signing/installing, failed artifacts retained, no traffic from them.

The existing unknown-ID return already prevents resurrection and RESET loops.
No functional fix was justified:101 keeps **all raw counters and dispatch behavior**.
It adds32 independently retained incidents; normal bulk cannot evict them.
Each contains session-scoped stream state and last per-kind enqueue/write/receive
times, frame size/credit but no payload.64 retired records,60s classification TTL,
fixed bounds, explicit dropped/projection-overflow counters. Missing history fails
classification, not silently accepted. Positive/negative tests distinguish known
in-flight abort crossings from post-FIN DATA, duplicate terminal, overflow,
never-known/old-generation IDs, expiry and malformed frames. Existing decoder,
live state validation, auth, TLS order and credit accounting are unchanged.
[Contract table and replay code](../../tests/fixtures/p1_owner/lifecycle101/README.md).

327 saved JSON artifacts recover additional stream293 WINDOW_UPDATE773ms after
local reset/removal and stream305 DATA+FIN128ms after reset/removal;305 includes
creation/open and an uninterrupted local event sequence. There is still no retained
credit snapshot or original request mapping for those events. This narrows history;
it does **not** turn the historical eight incomplete cases into PASS. Stream51
Android CLOSE / gateway RESET belong to the same session/stream sequence, not two
independent failures. Histories are endpoint-local; no cross-host one-way latency.

Gateway source:`state-client-build/p1-lifecycle-101-20261021/gateway-source`;
loaded:`3a0804cd3da63135dce387d1dff9afdc4588562186abea2e5d00da1d9f5c31ae`.
An unrelated active non-owner session prevented an initial restart. Existingf631
then independently exited status1 at18:00:28UTC and systemd restarted18:00:59;
same binary/profile, not proven renewal, not101/P1 traffic. No new test request
had started. After an empty current invocation was verified, the existing guarded
transition ran18:06:36, preserving profile362e5c08…, argv, identity and timers;
locks released. Immediate directory propagation failures are retained; full
TLS/material/runtime/publication readiness passed18:07:49, expiry20:41:36UTC.
Rollback is exactf631, never beta96 or ae527. Other users' profile remains P0.

Continuation budget frozen before traffic: existing36.080078125/64MiB used;
≤24MiB additional,16.0234375MiB for short P0/P1 controls, ≤2MiB periodic activity,
≤2MiB short/smoke, remainder reserve. No refunds for failures. Original full
matrix stays below; fresh controls assess observer cost and lifecycle, not a new
architecture. Fresh complete both-end evidence, bodies, bounded teardown and
ordinary persistent P1 reconnect are required before leaving owner on P1.

### Fresh101 short controls (completed; not a repeated full matrix)

Same101/3a08 code, cellular TUN/MESH, Q0, original carrier/policy and bounded
instrumentation. Both-end gates verify P0 effective8/LEGACY64 and P1
32/32/peer32/effective32/CREDIT128. Each phase has a new media session.

| Phase | Single4MiB Mbit/s / seconds | Parallel2×2MiB aggregate Mbit/s / seconds | Requests | Raw Mux errors Android / gateway |
|---|---:|---:|---:|---:|
| l101-p0 |0.608752 /55.12|1.021444 /32.85|15/15|1 /1|
| l101-p1 |1.408666 /23.82|2.361325 /14.21|15/15|0 /0|

Fresh single2.314×, aggregate2.312× preserve the earlier two-order speed result.
Small full-time median/max, six samples per cell: P0 idle2.925/4.258s,
P1 idle3.031/3.404s; P0 loaded2.713/3.240s, P1 loaded2.043/2.473s.
Only idle median increases (+3.64%), below the frozen20% review threshold;
no p99 claim. All bodies HTTP200/full length/TLS verification/observed SHA256;
the random-body endpoint still supplies no independent origin digest.

P0's two endpoint counters describe one crossed RESET sequence on stream1,
session0233776f…: both had opened, locally aborted and removed the stream before
receiving the peer's RESET. Android sent260/received370B, gateway the reverse;
neither direction had FIN. Local receive follows removal by704ms/335ms respectively.
No preceding RS failure or session cancellation. Complete independent incident
contexts classify both as expected; raw counters remain1/1. No active-stream
mutation, delivery, resurrection or extra credit occurs in the existing return
branch. Exact request association is unavailable; it is not assumed to be a meter
request. P1 has no incidents. Actual violations/unclassified/dropped are0 on both
ends in both controls; no observed session/route change.

All meter requests finished before Disconnect. Android cleanup completes0.790s
(P0)/0.810s (P1) after the command. Gateway records actual `recovery_exhausted`
11.148s/10.346s after it, never before Disconnect; whole close observation takes
21.124s/20.505s. This is retained as post-Disconnect exhaustion, not renamed clean
remote RESET receipt or download failure. The existing unscoped
`dedicated_resources_closed` follows each terminal by3.350ms/1.181ms; it is emitted
only after Mux.Close verifies zero sockets/streams/retained bytes. The bounded
journal contains no overlapping other profiled session in these intervals, but
the resource event itself has no session ID: this is temporal corroboration,
not an invented cross-session identifier. Local race/worker cleanup tests provide
the independent bounded-close check. No Q1/retry/timeout change was introduced.

Gateway CPU averaged6.16%/6.62% of one core; sampled RSS maxima42932/45460KiB.
Android pre-close PSS153839/162669KiB, native heap PSS26500/28330KiB are point
observations including normal app/background work, not isolated window costs.
Retry bytes Android4537/3169, gateway1183311/1544733 cover whole sessions including
background and gateway teardown; they are not per-download packet-loss rates.
Collectors ended without cap or partial-record loss.15min activity and final
ordinary persistent P1 reconnect remain pending at this checkpoint.

## Historical result of the first acceptance attempt (unchanged)

Final17:20UTC: installed100, gatewayf631bd99…, **owner P0 restored**, CONNECTED/READY,
real TUN MESH and DNS/HTTPS smoke PASS. The goal “leave accepted accelerated P1 on
the phone” is **not achieved**. Speed passes both orders; active-session event
provenance is incomplete. This is neither clean acceptance nor proof of failed
downloads. [Structured results](2026-10-21-p1-owner-acceptance.evidence.json).

New authorized owner-only P0/P1/P1/P0 series; leave persistent P1 only after full
limited acceptance. No other-user delivery/profile change or general release.
Historical96/newP0−18.438% single/−25.053% aggregate remains unresolved.

## Exact entry and new evidence

Entry16:11UTC: installed99/native matched the checkpoint; gateway ae527cbd…,
profile738e5f52…, operatorP0/LEGACY64/pacingOFF. Phone was already RESTORING.
Old gateway exited status1 at16:09:37UTC, systemd restarted16:10:07, new invocation
a46c8fd4…/PID851828. This is not proven renewal. Two earlier session terminals
have exhaustion before gateway cleanup, but old evidence does not exclude an
earlier client/owner close. A third has gateway parent cancellation followed by
Android exhaustion. Do not classify all three as active-session protocol failure.

Before update, session4160f870… is a **mixed pair**: Android selectedP1,
send32/receive32/peer16/effective16; gatewayP0 send8/receive16/peer32/effective8;
LEGACY64 at both ends. Setting-change origin unknown, not full P1, no measurement
from it admitted. Old unknown-stream events lack ID/kind/removal provenance.

## Installed observation100

Exact parent:`state-client-build/support-cadence99-20261021/android-source`, never
old root main. Installed100 `0.1.18-beta100-lifecycle` owner-only, same package,
signer and UID10283, no data clearing. Existing vault and guarded installer used.

- APK:`state-client-build/p1-owner-acceptance-20261021/delivery/FamilyConnect-0.1.18-beta100-lifecycle.apk`.
- APK SHA256:`1eb04cc6082f6a03380b99e8a47053d51efd8e6098c0c135075ac030228061e0`.
- Native SHA256:`da6be2bbee9d65dff074aef09c4dd795b7d6c3f4270545853968486ee134c35e`.
- Signer:`67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
- Source inventory:`a311dbc85544345ad6b2ee69f764fe362e19ae0b8da2d5d552b079eddf0dbdda`.

Observation only:32 payload-free lifecycle events,64 retired-stream records and
detached first unknown-ID provenance; fixed memory/export bounds. No frame handling,
counter suppression, retry/flow change or HTTP schema extension. Missing retired
history means unknown. Only the restricted native library changes among12 bundled
libraries. Bootstrap/recovery/security sources preserved. Go race tcpforward and
sessiondiag PASS;202 selected JVM tests PASS; full CI NOT_RUN.

USB consent renewed through the app; automatic ordinary P0 connect succeeds.
Sessionde28c75c… verified both ends8/16/peer16/effective8/LEGACY64.1024B actual TUN
HTTPS probe completes HTTP200/TLS verification/full body in3.071686s; post counter0.
Not P1 acceptance. All unsuccessful preparation/read/gate attempts are retained.
An APK-path gate rejected Android's`~` prefix before traffic; corrected shell
quoting. Filtered journal reads timed out; bounded unfiltered tail plus existing
continuation parser succeeds. No service/journal reset to hide missing data.

## Frozen contract

New64MiB requested-byte ledger, no refund for failed requests. Reserve32.046875MiB
four phases,8.01171875MiB one proven service-interrupted-phase repeat,8MiB diagnosis,
12MiB periodic activity,3.94140625MiB smoke/closure. Each phase: single4MiB,
parallel2×2MiB,6×1024B idle and6×1024B loaded controls. Same existing HTTP meter,
150s curl/170s subprocess bounds. Observed body SHA is not independent origin-hash
acceptance for the existing random-body endpoint.

Both-order single≥20% gain; each aggregate≥−10%; small median/max deterioration>20%
requires explanation. All bodies, actual TUN, both-end limits and explained session
completion; no unexplained active failure/fallback/reconnect. P1 must also pass15min
periodic load, drained ordinary Disconnect, bounded close, ordinary Connect and
DNS/HTTPS/TUN smoke. No invented p99 or continuous-saturation claim. At most two
causally supported corrections, no new Q1/packing/FEC/QUIC/window tuning.

## Causal observation and current server

Android session`de28c75c…`, stream91: created1792600543892ms,
opened1792600545056ms, finished RESET1792600546570ms, removed1792600546571ms;
incoming RESET(kind6)1792600547153ms,582ms after removal. No preceding RS failure,
session cancellation or Disconnect.428B sent/569B received; not a measured download
(the1KiB smoke ended earlier). Its exact application/request identity is not known.
This is a proven retired-reset-stream event, not a live-stream state mutation.
The existing decoder validates zero-length RESET before dispatch. A deterministic
crossed-RESET test preserves the raw error increment, proves retired buffers empty
and neighboring DATA intact; never-known IDs and invalid live state still fail.
Full tcpforward/sessiondiag Go race checks pass again. No transport fix or Q1
was justified by this event. Classification is evidence-only and narrow; late DATA,
missing history, unrelated IDs and other historical errors remain unclassified.

Normal owner Disconnect after completed requests precedes gateway exhaustion by
about10–11s in the observed sessions. This remains an actual`recovery_exhausted`
terminal, not a renamed successful close or failed download. Q0 close has a
best-effort queued RESET and bounded lower-layer cleanup; proof of remote RESET
receipt is absent. Active-session failure and post-Disconnect cleanup are reported
separately; no general exhaustion exemption is introduced.

Owner-scoped gateway observer`f631bd997ffc3a58a3216f8657062bef3edb1dcf38ec340c94dd26d3c625763e`
replaces exact`ae527cbd…` at16:40:59UTC only after the owner disconnected and the
bounded current-invocation journal showed no other profiled active sessions.
Existing guarded transition/renewal locks were used and released. Ordinary scheduled
renewal subsequently COMMITTED (`scheduled-1792600892-66dde93d2dce9af0`) at16:41:55;
new invocation`b27302d7…`, PID873237, same binary, profile`362e5c08…`.
Readiness verifies certificate/CRL headroom until20:41:36UTC before the new series.
No timer/renewal disable, authority/permission change or other-user profile change.
This task changes owner APK and shared gateway binary: not “production unchanged”.

## New same-code P0/P1/P1/P0 contrast

Same installed100/f631 pair, CELLULAR phone network, HTTPS endpoint/meter, carrier L,
A0, Q0, OFF packing/FEC/pacing/timebase candidates. Each phase starts a new media
session; one gateway invocation remains unchanged throughout. Setup is excluded
from body goodput. RS limits are applied on both ends, not inferred from selection:
P0 send8/receive16/peer16/effective8 +LEGACY64/65536;
P1 send32/receive32/peer32/effective32 +CREDIT128/131072.

| Phase | Single4MiB Mbit/s / seconds | Parallel2×2MiB aggregate Mbit/s / seconds | Complete requests | Android / gateway raw Mux errors |
|---|---:|---:|---:|---:|
| P0a |0.606661 /55.31|1.023001 /32.80|15/15|0 /0|
| P1a |1.396937 /24.02|2.346464 /14.30|15/15|0 /0|
| P1b |1.443201 /23.25|2.239949 /14.98|15/15|0 /0|
| P0b |0.631791 /53.11|0.966151 /34.73|15/15|0 /0|

Single gain +130.266% /+128.430%; aggregate +129.371% /+131.842% in the two
orders. Frozen speed criteria pass without historical multiplication or selective
best-run comparison.60/60 HTTP200/full bodies/TLS verification/observed SHA256;
no route/session/fallback change during measured load. No failed HTTP attempt or
phase retry. Random-body endpoint still has no independent origin checksum.
Historical96 regression is **not** resolved by this contrast.

| Phase | Idle small median / max, seconds (n=6) | Loaded small median / max, seconds (n=6) |
|---|---:|---:|
| P0a |3.177507 /4.159206|2.887313 /4.253728|
| P1a |2.438770 /4.785608|2.080711 /3.459410|
| P1b |2.505176 /3.131048|2.112316 /3.588815|
| P0b |2.705708 /3.319537|3.001595 /4.096787|

No paired median/max deterioration exceeds20%; P1a idle observed max is15.06%
higher, retained rather than hidden. These are six probes per condition, not p99.
Native cleanup_completed is confirmed for each exact session; gateway reaches
actual IO_CLOSED/recovery_exhausted after ordinary Disconnect, not during body
transfer. Client final counters are the last pre-stop snapshot, with native-stop
success recorded separately; gateway counters are terminal. There is no invented
post-stop Android terminal snapshot. The observed close interval is bounded by
host command/readback timing; cross-host timestamps are not one-way latency.

Gateway process CPU sampled within each phase:8.18/8.94/6.42/6.30% of one core;
RSS peak55,636/60,060/52,144/50,140KiB. Phone post-phase PSS169,077/169,753/168,051/
169,383KiB. Android dumpsys CPU windows overlap prior phases and are stale in some
reads: not valid per-phase CPU comparison. No claim of long-duration boundedness
from these short RSS observations. Existing fixed stream/queue limits are unchanged.
Gateway whole-session retry bytes1,612,692/1,904,150/1,553,310/1,374,910B; Android
2,601/3,513/1,089/5,702B. They include background traffic and server close cleanup,
not exclusively the8MiB workload or a packet-loss estimate. Q0 remains; no Q1 gain
or elimination of all premature attempts is claimed. All collectors ended below cap.

## Active session and ordinary reconnect

P1 session`18929834…`:917.803s instrumented duration,910.579s actual request span.
31×1KiB controls at nominal30s intervals plus4×1MiB at nominal0/300/600/900s:
**35/35 complete**, no observed active reconnect/fallback/RS failure. Periodic load,
not15min continuous saturation. Small median2.909240s/max5.155503s(n=31), no p99;
1MiB bodies took9.118/10.605/10.243/10.158s.

Android raw unknown_stream reaches9; gateway raw protocol errors3. The32-event
ring loses the intervening burst; only the first incident retains complete stream
provenance. Do not replace missing events with zero or presumed benign labels:

- Android47: created1792602179876/opened1792602180033ms; RESET finish/removal
  1792602181008ms; WINDOW_UPDATE1792602181043ms (+35ms). Used0, local FIN true,
  remote FIN false; no primary RS failure, cancellation or Disconnect. Valid late
  control after stream cancellation, no live credit mutation. Original application
  request identity is not retained; successful meter bodies cannot identify it.
- Stream51, same session on both ends: Android sends CLOSE and RESET, removes the
  stream, then receives CLOSE. Gateway retains both FINs, used0, EOF finish/removal
  1792602182527ms, then RESET1792602182561ms (+34ms). Crossed terminal frames are
  established for that ID, not an active-stream failure. Endpoint IDs establish
  correspondence; cross-host clock subtraction is not used for one-way latency.
- Android115: RESET finish/removal precedes incoming FIN by9ms; its earlier open
  history is outside the saved ring. Six other Android and two other gateway events
  lack individual event history. Their origin remains unknown.

Deterministic tests cover late RESET after RESET/removal, WINDOW_UPDATE/CLOSE after
RESET, and RESET after closed EOF. Neighboring state/data and raw counters remain
intact; malformed controls, never-known IDs and invalid live state remain visible.
Tests **do not classify the eight missing real sequences**. No proven live-stream
transition defect justified a transport patch. Q1/retries/windows/wire behavior
remain unchanged. No matched15min P0 control: these events are not causally
attributed to P1, and the nil-stream branch predates P1.

All35 requests finish before ordinary Disconnect. Gateway pre-close observation
has no terminal; Android reports native`cleanup_completed`. Actual gateway
`recovery_exhausted` is retained, terminal confirmed within21.254s of the host
Disconnect command. This is not relabeled as graceful close; remote RESET receipt
is unproven. Ordinary Connect takes31.678s **without rewriting either profile**;
both ends again RS32/32/CREDIT128 and DNS/TLS/1KiB TUN smoke pass. Persistent P1
selection works, but does not waive the incomplete-event acceptance gate.

## Decision, budget and final state

**Limited owner admission: NOT_ACCEPTED / evidence incomplete.** Main speed and
latency criteria pass; active phase is not used as clean acceptance. All98 metered
requests in eight load/smoke stages complete; no failed body is invented from a
counter.36.080078125MiB requested/reserved of64MiB, no refunds/hidden retries.
Remaining27.919921875MiB cannot fit another complete32.046875MiB four-phase series.
No automatic budget increase, favorable retry or parameter sweep. Complete bounded
per-event provenance and a new same-code acceptance remain unfinished. No claim
that two transport correction cycles ran; conditional olcRTC follow-up not started.

Owner returned by ordinary Disconnect/profile/Connect to **P0**. Both ends
8/16/peer16/effective8, LEGACY64/65536, Q0; session`a647ff0b…`, CONNECTED/READY,
capture open, Telemost VP8/RTP MESH. Final1KiB DNS/HTTPS body completes in3.794883s.
17:20:49UTC readback verifies installed100 APK/native hashes above and loaded
gatewayf631bd99…/PID873237/invocationb27302d7…; runtime profile SHA256
`362e5c0895c5e1cb308edf054855f782a5a9734fc1860b04f5913892cbce8765`.
16:41 renewal archive comparison proves certificate/revocations changed only;
authority, private key, family/gateway binding and floors unchanged. This explains
that renewal, not the earlier16:09 status1 exit.

202 JVM;13 focused Python; Go race tcpforward/sessiondiag and
wholedevice/reliablestream/familysession plus targeted late-frame regressions PASS.
No full platform CI, forced network-loss recovery, overnight reliability, Russian
whitelist or general release claim. Old96/newP0 regression stays open. Failed
preparations/reads, partial journal capture, exact capsules/patches/receipts retained;
partial capture is not treated as valid evidence. Payloads/keys/raw diagnostics
stay out of Git. Native final counters remain pre-stop, with successful cleanup
separately confirmed; no invented post-stop snapshot.

No downgrade/uninstall/data clearing/re-activation; signer/package/identity retained.
Return path is existing next-session P0, not APK/security-history rollback. Guarded
binary rollback target ae527cbd… exists if separately needed, not executed. Other
users unchanged. Temporary HTTP processes/directories and journal collectors are
absent; normal owner VPN and opt-in support remain. No push/public release/tester
distribution. Do not silently reuse this failed-active ledger for a clean retry.

Late additional USB snapshot is unavailable; the support guard is not bypassed
and no new manual consent is requested just to repeat the completed handoff.
17:26:51 OS/binary readback still shows one owner VPN, the same100 APK/native,
same gateway invocation/binary and operator P0. Last complete both-end profile
snapshot and successful TUN smoke remain the17:20 receipts, not a fabricated
later private app snapshot.

Private evidence and replay:
[fixture](../../tests/fixtures/p1_owner/README.md).
