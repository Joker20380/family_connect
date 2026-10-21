# Android consolidated speed candidate — 21 October 2026

## Decision and scope

**Compatible97 is signed and installed; the approved shared gateway transition
is complete. Original96 and new-pair P0 each delivered15/15 responses.**
No speed/product admission. Fresh READY97 and independent Android/gateway applied
P0 receipts match session `ca8d5613…`; actual RS8/16/effective8, LEGACY64. New-pair
P0 is slower beyond the frozen review threshold; cause unresolved, not clean
original/new equivalence. Gateway next-session owner P1 is prepared13:02UTC,
P1 was then manually applied and measured; both ends32/32+CREDIT128/Q0.
First P1 bulk is faster but not repeated or clean package admission; its later
gateway terminal has3 whole-session protocol errors and RS exhaustion. P2a was
applied with both-end32/32/Mux128/Q1 receipts and15/15 bodies delivered. Its Android
1 protocol error predates load; the post-export reports10 over a mixed664.356s
load/background interval, with no known exact onset or branch. This is not clean
acceptance; it is also not nine failed downloads or proven Q1 causality. The
post-export is reconciled. P2a later gateway terminal1/RS exhaustion is retained.
Fresh P2b then delivered15/15 at1.245062/2.545860Mbit/s; initial Android/server
errors0, Android post-export0→0 then later2; gateway terminal1/RS exhaustion,
so no clean acceptance. P1b was actually applied with32/32/Mux128/Q0;
15/15 delivered at1.324169/2.583097Mbit/s. Post-export14:00:03UTC has Android errors
0→1 over831.678s including background, unknown onset/branch; not clean acceptance
or a failed download; later gateway terminal3/exhaustion is also retained.
Owner manually returned to verified P0. Its final single completed0.654210Mbit/s,
but both parallel responses were truncated during proven scheduled renewal.
All planned phases have been attempted; no automatic repeat. Q1 single effects
−3.736%/−5.974%, aggregate+0.068%/−1.442% in the two orders: no added speed gain
or clean package admission. P1/P0 raw single gain is2.116×/2.024×, reverse aggregate
unavailable. Final `(14)` matches the new gateway P0 session after renewal;
Android CONNECTED/READY, actualeffective8/LEGACY64, but17 protocol errors in the
new session. Cause unknown; no clean admission. **Cycle closed with limitations,
keep P0, no more owner actions or diagnostic exports.** The new Android
binary retains the same identity, UID and signer.
No tester distribution, public release or push.

Only the current authorized P0 → RS32/Mux128 → Q1 integration is pursued. The
[QUIC evidence](2026-10-21-quic-carrier.evidence.json) is closed for this iteration:
DATAGRAM_ADAPTER_LOCAL_VALIDATION completed; BULK_SPEED_GAIN not established;
SMALL_RESPONSE_OBSERVATION positive once; CLEAN_REPEATED_CONTRAST absent;
PRODUCT_ADMISSION not given. QN1 delivered all bodies/receipts before its later
controller/log completion failure; this is not download loss. QN2 lost publisher
before bulk, not a full speed measurement. No QUIC/FEC/fragment/host/tuning rerun.

## EXACT_BASELINE

Inputs are exact local accepted source capsules, not an old GitHub main. Their
inventories, changed-file pins and all attempts are in the
[machine evidence](2026-10-21-android-speed-candidate.evidence.json). Private workdir:
`state-client-build/speed-candidate-20261021`.

| Item | Observed or pinned value | Qualification |
|---|---|---|
| Android | `com.familyconnect.app.friends`,96, `0.1.18-beta96-bootstrap`, UID10283 | Fresh ADB12:16:58 and12:23:10UTC before update; now superseded by installed97 |
| Accepted APK | `07a90f03269e1df683289bc1fbe7fa7e88647c5629f71db1f784d6566aa9228d` | Local accepted signed artifact |
| Accepted native | `66a9d18d04ff71100df0144228db05decb970aea71b6d277ec321b1c6c240c63` | Pinned96 native, not candidate hash |
| Existing signer | `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a` | Required for in-place update |
| Original gateway executable | `734b6ca6eb42be0367b703b657be87c624f3500ae408bbd771309ffaeb86128e` | Fresh `/proc/PID/exe` before approved12:30 transition |
| Android input | `state-client-build/mobile-bootstrap-20261020/android-source` | Exact96 inventory |
| Gateway input | `state-client-build/rtp-pacing-20261020/candidate` | Exact accepted734 inventory, bootstrap1011 preserved |
| Source-derived P0 RS | local send8/receive16 at each end; effective8 if peer announces16 | Not retrospectively inferred from TLS ALPN |
| Runtime flags | pacingOFF, LEGACY64, Mux countersOFF, no speed-profile | Pre-install readbacks only |

### External process/profile event — no task mutation

Entry **10:47:31.540680UTC**: PID555883, invocation
`31ee59ae99c84bafa3be5402d784efce`, profile SHA
`55b508c213ab279e95b4f30c9d165eed4c9281adc6c3ff9f2cbaee111eb7d2c6`.
Pre-install **12:04:43.976585UTC**: PID671088, invocation
`e33e6d1b9a90496d811903d55b1589cf`, reported process start **11:41:02UTC**,
profile SHA `24c040c087ca68100af363cc3285be836ae05f0bbaa77984cc7c8ec0c02b274d`.
Binary/observed transport flags stayed equal. The profile-file change is bounded
by these readbacks, not proven to occur exactly at process start. Cause and changed
fields are **unknown**; do not infer renewal. No profile contents/secrets printed,
no restoration of the historical hash, no forced renewal or timer action.
Only local preparation overlapped that external event. The **later explicitly
approved12:30:28UTC executable transition** is separate and task-owned; it must
not be described as production unchanged.

### Owner continuation and approved transition

Fresh accepted96/734 baseline over actual TUN completed15/15 HTTP bodies by
12:24:35.591UTC. After the owner manually disconnected, protected vault signing
and in-place install completed at12:28:22UTC. No uninstall, data clear, identity
rotation or security rollback. An initial signed97 had the selector in
`MainActivity`, not the actual `FriendsActivity` launcher; fixed **before any
installation**. That unused signed build/logs are retained under `superseded-ui/`.
The final Friends selector is idle-guarded;190 JVM tests pass, native unchanged.

Approved shared gateway restart at12:30:28UTC installed `ae527cbd…`, PID703785,
invocation `052c9a94fa39418990337bccbb8accd0`. This interrupted shared MESH
sessions as explicitly disclosed in the approval. Global limits remain P0;
owner-only profile initially P0, prepared P1 for the next session13:02UTC. Profile SHA remains `24c040c0…`,
carrierL/A0/pacingOFF/Mux counter exportOFF. Existing credentials/renewal retained.
The first readiness check1.15s after restart saw the previous publication and
failed its timestamp gate; a fresh read at12:33:53UTC passed the **same** strict
checks after ordinary startup publication. No second restart or gate relaxation.
Catalog SHA `e0389d06636747a611546eea518495a2018703b1ae52f62b7f64fa9e4d1f7afe`.

Operator helper failures are retained: embedded newline syntax error before any
write; then a33B target with newline, corrected to the existing32B reader contract
while P0 was still selected; terminal-reader placeholder syntax error before any
journal query. Three local helper tests pass. None required production code,
authentication or test-failure semantics changes.

Owner manually connected. READY97 ACK12:44:24UTC, new gateway applied P0 receipt
12:44:52UTC. Fresh12:51:29UTC readback confirms APK97 and cellular TUN; the owner's
JSON export independently confirms the same session tag, RS limits and Mux64,
protocol_errors0 at its observation. Its historical96 `incident` is retained but
**not** treated as a new97 incident. Export age is recorded (maximum300s guard),
and a fresh same-tag gateway trace/TUN readback prevents use after reconnection;
this is not clock-derived one-way latency. New P0 measurement followed that gate;
all15 bodies completed and post-load Android export remains connected in the same
session, protocol_errors0→0.13:02UTC server owner-only next P1 was prepared without
restart, while the last independently verified applied session was still P0.

## INTEGRATED_COMPONENTS and EFFECTIVE_RS_AND_MUX

| Profile | Local RS send / OPEN receive | Required peer receive / effective send on new pair | Mux | Retry basis |
|---|---|---|---|---|
| P0 |8 /16|16 /8|LEGACY64,65536B per stream|Q0|
| P1 |32 /32|32 /32|CREDIT128,131072B per stream|Q0|
| P2 |32 /32|32 /32|CREDIT128,131072B per stream|Q1 local completion|

`sessionprofile` snapshots a new-session configuration. `OpenMuxReliable` passes
RS configuration **before** RS OPEN and Family TLS. TLS negotiates only existing
authorized LEGACY64/CREDIT128; it cannot retroactively negotiate RS receive memory.
RS diagnostics expose local send/receive, peer receive and actual effective send.
No announced OPEN changes, peer-window assumption or flow-control removal.

Android exposes a local next-profile choice only when disconnected. It reaches the
dedicated whole-device session through a bounded JNI enum/context; generic
bootstrap/exchange paths stay P0. Gateway uses existing protected operator files
`speed-profile`/`speed-target`; target is the existing hash-tag convention for the
authorized peer public key. A target mismatch stays P0. This is not authorization,
onboarding, directory policy, a canary system or a public debug API.

Actual applied metadata is separate from intent: safe Android `SpeedReceipt`
projection and gateway `session_profile` startup / `session_terminal` final
events. Unknown fields and invalid limits are rejected; no keys/payloads exported.
Same bounded instrumentation applies to all profiles. The startup receipt does
not masquerade as successful terminal delivery.

Carrier L/A0, original2ms/frame and inherited33ms timestamp behavior are unchanged.
Packing/FEC/new pacing/timebase-fix/SACK-hole/read-alignment OFF. Payload16KiB,
RTO1s, MaxRetries8, MaxAge20s, WebRTC/NACK and routing unchanged. Bootstrap96
Python/native inputs and gateway1011 seed recovery are hash-protected. Package,
signer requirement, identity/security history, authority/claims/CRL/revocations/
floors and ordinary renewal remain unchanged. No production dependencies updated.

### Sealed deltas and builds

| Artifact | SHA256 | State |
|---|---|---|
| Android Q1 core diff,10 files | `d02ea5c123134ad0338ed09255fa7638f9de1316dde370777e59cd19d881ef27` | Separate dormant correctness delta |
| Android96→97 combined diff,30 files | `6e28a68d72d1cb7defc57412ec763856cb94b6aed2a169013a42efc581141ad1` | Includes gated Q1 and product profiles |
| Gateway734→candidate diff,12 files | `ee21f2d43b8b30bc99900f555d057223e20150e8e03815559452b4349d65710c` | Existing dormant Q1 enabled only for targetP2 |
| Unsigned97 APK | `f380e0c74a2acdfabb87d59ac1193a12882fc92776f8d5952f2a685f151a07ec` | Final unsigned build; signed derivative installed owner-only |
| Candidate arm64 native | `1fa75ee968ae75ad6446000e1907c35ae39a3993625220c51c76bf607f71ee82` | Ordinary Android tags, bootstrap96 retained |
| Candidate gateway | `ae527cbd0b93a5d34d10af1a5424cdf8254d79e253c9994a57520408614ce1dd` | Existing `fc_perf_diagnostic` tag; approved owner-test deployment12:30UTC |

Go1.26.1, NDK28.2, SDK35 and pinned Gradle8.11.1 offline toolchain reused. All three
source replays match **all** files. Source inventory for Android build:
`06c80554634e3226c622fea13df65ae1d3c9f194d339c4d4f20e340c60aaa2e1`.
Only `libfc_restricted.so` changes among12 native libraries. Check-only signing
verification passes package/version, native manifest, unsigned state,16KiB
alignment and accepted signer pin. Code97 was checked against freshly installed96 before the in-place update.
No published release was replaced. Superseded unsigned/signing artifacts are retained.

## OLD_NEW_COMPATIBILITY and local gates

Actual old/new sources execute in separate processes, four384KiB echo streams
per case, deterministic byte/SHA/EOF and both-end limits. This is not a simulated
“old” configuration of only new code. Seven cases pass:

| Client / server | Actual Mux | RS effective send client / server |
|---|---|---|
|96 /734|LEGACY64|8 /8|
|96 /new P1|CREDIT128 (96 already offers it)|8 /16 (old peer receive16)|
|new P1 /734|LEGACY64|16 (old peer receive16) /8|
|new P0 /new P0|LEGACY64|8 /8|
|new P1 /new P1|CREDIT128|32 /32|
|new P2 /new P2|CREDIT128|32 /32|
|return new P0, new session|LEGACY64|8 /8|

Local integration on both exact candidate trees also passes:

- Three simultaneous P0/P1/P2 sessions,32 streams each, byte-exact/EOF, slow
  consumer, small and bulk traffic, isolated stream reset, cancel/close, bounded
  retained bytes, duplicate/reorder/ACK-loss and a three-message loss burst.
  The fault boundary is RS messages in this fixture, not equal RTP loss modelling.
- Bound-Pion missing-head tests at full32 for P1/P2 on both implementations:
  logical/frame/fragment loss, duplicate, late whole message and late RTP,52 cases
  including parent cases. Queue/receive/reassembly remain bounded.
- Six security/lease runs, P0/P1/P2 each side:309 case passes including parents;
  full-window persistent sockets, renewal/expiry, lost lease response, revocation,
  floors, claims and ALPN denial. Fresh disposable certificates prevent fixture
  wall-clock expiry; no authority change or fallback exemption.
-190 JVM tests (first189-test UI build retained), including bootstrap96 and profile/receipt bounds, pass. Gateway
  final race selection611 cases passes,8 skipped. Exact Android final selection
 539 cases passes,6 skipped, **exit1**, as explained below. These are case counts,
  including parents, not independent samples or a claim that all suites passed.

### All exceptions retained; not a blanket green suite

The machine evidence indexes **every root JSONL attempt**, including earlier
failures, not just overwritten final receipts. Initial sandbox build/test socket
restrictions were rerun normally. Build provenance initially lacked `.git` in the
capsule; the pinned95 Git metadata plus97 worktree supplied the original verifier,
without weakening it. Final build succeeds; all earlier Gradle/native logs remain.

The first32-head fixture retained its old255 full-window bitmap expectation;
corrected to4294967295 for32 **in the fixture only**, retaining failed runs.
Early lease runs crossed disposable certificate expiry and exposed immediate
test-only lease-control stream overlap (`stream_limit`). Regenerated certificates
and a bounded prior-stream-quiescence check fix test setup; production exchange
semantics, failure handling and retry limits are not modified.

The exact accepted96 baseline reproduces six negative-case assertions in
`TestProductIdentityOverBootstrapCarrier`: bootstrap96 intentionally emits a
diagnostic rejection where the older assertion expected no exchange-failure
event. Auth rejection still occurs; these assertions were not silently “fixed”.
`TestAuthenticatedBusyExchangeReportsChallengeReason` is also non-green:
20 repeats on accepted96 and candidate97 each produce **12 pass /8 fail**.
Final candidate broad Android selection fails that assertion. This paired result
does not prove every new behavior is risk-free, but it is evidence against
attributing this existing assertion failure to the profile delta. No broad-suite
PASS claim, no deletion of failures, no change to rejection logic for a green log.

## Q1_CORRECTNESS_AND_COST

The saved queue-retry delta is transferred minimally, gated by P2, not included
only in a faster measurement. Android requires10 core files; gateway734 already
contains the dormant prerequisite. RS stores session/attempt generations and
observes completed local media write separately from enqueue. ACK processing stays
independent of writer; freed DATA cannot be resurrected by stale completion.
Queue/write deadlines are finite (bounded by MaxAge and the existing2s local
deadline); session cancellation and post-local-write loss recovery remain intact.
SendContext is not remote-ACK completion. Payload of an assigned sequence never
changes; MaxRetries is not reduced.

The existing bound-Pion reproducer is run at32 with test-only RTO30ms and340ms
writer hold, not product defaults:

| Source | Q0 attempts / premature retries | Q1 attempts / premature retries | Completion |
|---|---|---|---|
|Android|9 /8|1 /0|Q0 `recovery_exhausted` even if delayed bytes later arrive; Q1 exact body, empty terminal error|
|Gateway|9 /8|1 /0|Q0 `recovery_exhausted`, incomplete body; Q1 exact body, empty terminal error|

A passing Q0 **reproducer assertion** is not successful transport acceptance.
True loss after completed write is still retransmitted in separate tests. Q1
removes demonstrated early local attempts; it does not eliminate necessary
network repair or establish Android speed gain. Retry bytes/useful bytes,
post-write losses, delayed ACK/SACK and unknown cases must be separated live.
No new claim about packet loss from a retry-byte counter alone. LabDrain/reset
semantics are unchanged; terminal reset never becomes success.

## LATENCY_FAILURES_RESOURCE_LIMITS

Static payload/ring accounting per endpoint (not total process RSS):

| Component | P0 | P1/P2 | Additional maximum |
|---|---|---|---|
|RS payload buffers|8×16KiB send +16×16KiB receive =384KiB|32+32 slots =1MiB|640KiB|
|Mux rings,16 streams|1MiB|2MiB|1MiB|
|Mux rings,32 streams|2MiB|4MiB|2MiB|
|Mux rings,existing cap64|4MiB|8MiB|4MiB|

RS+rings extra: **1.625MiB at16**, **2.625MiB at32**, **4.625MiB at64** per
endpoint; double for both ends. Three concurrent32-stream gateway sessions add
at most7.875MiB by this component model. Max streams64/pending opens32/DNS16 are
not raised. Local concurrent tests do not justify increasing user/session caps.

Carrier caps unchanged:256 queued frames,8192B fragment payload plus24B carrier
header and17B VP8 prefix (≈2.01MiB queued frame data);64 receive messages with64KiB
message bound (≤4MiB);16 pending reassemblies with64KiB bound (≤1MiB),10s TTL,
8 parts,32KiB assembled-frame bound. TLS/staging/bridge buffers remain existing
64KiB-scale bounds. These may alias or exist at different stages: do not add all
figures as measured RSS. Pion, TLS, maps, metadata, allocator/GC and socket memory
are additional. Q1 adds bounded O(32) tracking/completions, not a new bulk-copy
queue. Whole-gateway CPU/RSS are now sampled for both P0 controls, not owner-only.
Android phase CPU/peak RSS, exact queue age and full media cost remain
**UNKNOWN/NOT_MEASURED**. Later bounded OS point readbacks are not phase peaks or
owner-isolated CPU; they do not retrospectively fill missing earlier measurements.

## Predeclared owner comparison contract — frozen before live data

The following limited-owner criteria are frozen before measurements, not fitted to
future results. They are not a global release policy:

1. Fresh original installed receipt, READY, DNS/HTTPS through actual Android
   TUN/MESH, then the same checks on new P0. If comparable original/new P0 controls
   differ by >15% in single or aggregate, investigate integration/background first;
   no silent substitution of historical Linux or beta87–94 data.
2. Same phone/underlay/gateway/meter, P0→P1→P2→P2→P1→P0; without suitable P2,
   P0→P1→P1→P0. Each phase4MiB single plus2×2MiB aggregate; six1024B idle and
   six1024B loaded probes. **64MiB** total ledger includes smoke/control/errors;
   six main phases reserve48.0703125MiB, leaving15.9296875MiB. No automatic rerun.
   Bulk150s current meter cap (stricter than180s); HTTP retries disabled.
3. Clean speed acceptance requires all expected body bytes, HTTP/TLS validation,
   delivery result and final two-end diagnostics with actual limits, no newly
   attributable protocol error/terminal reset or unexpected fallback/reconnect.
   Historical counter values are subtracted only within a documented same-counter
   scope. Any reset/missing trace makes the delta unknown, not zero. Failed attempts
   remain in reliability statistics and cannot enter clean-speed averaging.
4. Material windows gain: single goodput ≥20% in **both order-matched P1/P0
   contrasts**, aggregate not more than10% lower in either. Report absolute Mbit/s,
   durations and paired differences, not multiplied historical percentages.
   Small median and observed max >20% worse in either comparable phase is a review
   trigger, not something to hide with n6 or a claimed p99. No severe new timeout,
   recovery, memory or protocol regression is acceptable for owner recommendation.
5. Q1 correctness admission is separate: known premature attempts eliminated,
   real-loss recovery retained, no >10% single/aggregate regression versus P1 in
   either order and no severe latency/error/resource regression. Speed increase
   is not required of Q1. Show P1−P0, P2−P1 and P2−P0 separately. If controls are
   unstable, the result is inconclusive, not a reason to tune thresholds or RTO.
6. Record SFU/ICE/session IDs, setup separately, background, CPU/RSS, actual
   limits, RS/Mux stalls, queue age, retries/bytes and available wire counters with
   coverage. Missing media attribution is an evidence limitation, not zero cost.
   No full per-packet trace in only one profile, no unsynchronized one-way latency.
7. End by preparing P0 on both ends, one explicit owner reconnect, confirm actual
   P0, then stop collectors. If a phase fails, preserve first cause and restore
   P0 for a new session; do not downgrade Android or security history.

The prepared meter reuses the existing Android HTTP meter rather than a benchmark
framework. It checks current TUN topology, installed candidate hash, gateway epoch,
<90s applied receipts and a bounded reservation. Observed body SHA256 is recorded;
the external meter has no pre-known origin SHA contract, unlike deterministic
local byte-exact tests. Final export/terminal review remains required, so raw
`measure.py` output intentionally cannot declare clean acceptance by itself.

## P0_P1_P2_ANDROID_RESULTS and RECOVERY_SCOPE

| Phase | Single / aggregate | Small median/max/n | Errors, retry bytes, CPU/RSS | Status |
|---|---|---|---|---|
|Original96/734 P0 control|0.811277 /1.591011Mbit/s;41.36 /21.09s|idle2.283741/2.984310s,n6; loaded3.399056/5.410096s,n6|whole gateway8.743% one-core;RSS62084→64804KiB; retry bytes unknown|15/15 delivered; not clean acceptance|
|New P0a|0.661693 /1.192411Mbit/s;50.71 /28.14s|idle2.684606/3.887328s,n6; loaded3.039472/3.803253s,n6|Android post0→0 then later4; server terminal3; whole gateway5.931% one-core;RSS48420→50524KiB|15/15 delivered; consistency review triggered, not clean acceptance|
|P1a|1.400435 /2.290405Mbit/s;23.96 /14.65s|idle2.492160/2.856800s,n6; loaded2.218355/3.208626s,n6|Android post0→0; later server terminal3/exhaustion; gateway6.757% one-core;RSS44696→54244KiB|15/15 delivered; first positive windows contrast, not clean acceptance|
|P2a|1.348109 /2.291969Mbit/s;24.89 /14.64s|idle2.654272/3.361555s,n6; loaded2.460405/3.483448s,n6|Android errors1→10, later gateway1/exhaustion; gateway6.685% one-core;RSS47540→53212KiB|15/15 delivered; not clean acceptance|
|P2b|1.245062 /2.545860Mbit/s;26.95 /13.18s|idle2.298595/2.909742s,n6; loaded2.685517/3.663040s,n6|Android post0 then later2; gateway terminal1/exhaustion; gateway6.973% one-core;RSS47308→53916KiB|15/15 delivered; not clean acceptance|
|P1b|1.324169 /2.583097Mbit/s;25.34 /12.99s|idle2.257751/3.067726s,n6; loaded2.725028/3.657239s,n6|Android post errors0→1 over831.678s, later server terminal3/exhaustion; gateway7.232% one-core;RSS49976→54680KiB|15/15 delivered; not clean acceptance|
|New P0b|0.654210Mbit/s /aggregate unavailable; single51.29s|idle2.242176/4.291554s,n6; loaded3.434376/4.865721s,n6|server terminal0/cancelled during scheduled renewal; old PID5.858% one-core,RSS47624→51868KiB; Android post pending|13/15 complete; both parallel partial/curl18; phase failed, not clean acceptance|

**CUMULATIVE_GAIN_VS_P0: descriptive completed-body observations, not clean admission.**

|Contrast|Forward single /aggregate|Reverse single /aggregate|
|---|---|---|
|P1/P0, windows|2.116× /1.921×|2.024× /unavailable|
|P2/P1, Q1 addition|0.963× /1.001×|0.940× /0.986×|
|P2/P0, cumulative|2.037× /1.922×|1.903× /unavailable|

P0a later has protocol errors; P0b single completed before the observed renewal
interruption but its parallel did not. Neither phase is a clean-acceptance
denominator; do not turn partial aggregate bytes into a speed comparison. Windows
single observations exceed the frozen20% threshold in both orders, but the complete
two-order aggregate/reliability/closure contract is not met. Q1 has no added speed
gain and remains a separate local correctness result. Original controls do not establish failure-rate,
overnight stability or automatic network-loss recovery. Local clock-driven
renewal/expiry/revocation and existing recovery tests pass at the integrated
profiles; manual reconnect compatibility is not proof of automatic physical
recovery. NOT_RUN is neither PASS nor an automatic prohibition of a coordinated,
limited owner test. No shared gateway fault was provoked.

### Original/new P0 review — threshold retained

New P0a versus original: single **−18.438%**, aggregate **−25.053%**. Frozen15%
consistency review triggers; it has not been loosened after seeing results.
Idle small-response observed max also rises2.984310→3.887328s (about30.26%),
crossing the20% latency review trigger; idle median rises about17.55%. Loaded
median/max improve in this one pair. Neither mixed result with n6 establishes p99
or repeatability, and the adverse idle tail is not discarded.
Same cellular underlay343/TUN/meter, different media sessions and gateway epochs.
The original active trace tag is not independently owner-attributed. A static
integration audit verifies39 equal files/function bodies: protocol/default RTO,
wire/engine behavior, Mux implementation, dependency locks and framing. P0 returns
unchanged default RS config/context; Q1 completion behavior is off. Android retains
minor unconditional timestamp/struct/nil-check costs plus bounded diagnostics;
these are not claimed benchmark-proven free. Existing actual old-old/new-P0/return
P0 loopback tests are exact-body/EOF/empty-terminal checks, not speed causality.

New owner's sampled unconfirmed-head retry appears in29/49 gateway observations,
versus2/40 in the old active (not independently attributed) tag. These2s samples
are not exact stall duration or a loss-rate estimate. New reverse receive RTP gaps
show0 increment while the old active tag shows2; that is **not** download-direction
loss evidence. No changed P0 window/cadence/recovery policy was found, but the live
cause is **UNRESOLVED**. Bounded new-pair P0/P1/P2 contrasts may continue; no claim
of original/new equivalence or package admission is made. A reverse P0 is still
required; no new sweep or repeated cherry-picked baseline is authorized.

Post-load owner Android export12:55:02UTC: same P0/session, no terminal error,
protocol_errors0→0. Counter interval12:49:20.324→12:55:02.319UTC includes idle and
background as well as measurement: +33 retry attempts/+219,163 retryB, +28 recovery
timeouts, +871,040 sentB/+9,029,668 receivedB. These are Android-direction counters,
not whole outgoing media overhead or all download retries. Necessary/early/late
causes cannot be separated from these totals; **UNKNOWN**, not claimed packet loss
or a Q1 speed result. During P0a ordinary lease offer/request/accept/apply succeeds;
this does not demonstrate automatic recovery from physical network loss.

Both P0 collectors ended below their cap with no partial tail/error, and stopped.
The original late terminal qualifications follow; new P0 final closure remains
pending until ordinary profile reconnect. Total synthetic delivered/reserved now
**16,801,792B =16.0234375MiB**. Remaining five primary phases plan40.05859375MiB,
leaving7.91796875MiB within64MiB; none of that planned traffic has been sent yet.

### P1a and late P0a completion update

P1a actual Android/gateway32/32, peer32, effective32, CREDIT128/131072, Q1false;
session `c9601fae…`, same binary/profile-file hash and cellular underlay, a new media
session.15/15 responses; single23.96s, aggregate14.65s. Idle n6 median/max
2.492160/2.856800s; loaded n6 2.218355/3.208626s. No p99 or repeated-gain claim.
Post-load Android snapshot13:10:08.349UTC is connected, no terminal error,
protocol_errors0→0. Its191.702s pre/post interval (includes background/idle)
adds23 retries/134,501 retryB and20 timeout events; sent/received Mux bytes
+664,695/+8,514,278. Not a same-duration comparison with P0's longer export window,
not whole-media accounting, and no early/local/network classification from totals.

The P1 startup export also preserves P0a history: Android protocol_errors **4**
at13:06:10.091UTC, versus0 at the post-bulk12:55:02.319 snapshot. This is a proven
**later** increase outside the measured P0 body interval, not four download losses.
Gateway's P0 terminal13:06:20.246UTC records `recovery_exhausted`, protocol_errors3,
243 RS retries/1,495,627 retryB for the **whole session**; first protocol-error time
is unknown. Exhaustion is after body delivery near the ordinary manual disconnect,
but causation by that action is not proven. Do not erase/rename this as clean
shutdown or a failed completed download. P0a **excluded from clean acceptance**.
Thus the positive P1/P0 speed ratio is descriptive only, not product admission.

At13:11:58UTC existing gateway epoch/hash unchanged; operator owner-only NEXT P2
prepared without restart. Owner applied P1 remains last verified; actual P2 waits
for manual switch/export. Android point readback outside load: PSS128304KiB,
RSS237604KiB, swap PSS149KiB; dumpsys CPU21% covers15:04:59→15:09:59 phone-local
wall time (mixed P0/setup/P1), **not** pure P1 CPU. Such bounded point readbacks are
now retained before/after remaining phases; measurement-loop instrumentation is
unchanged. No reconstructed Android CPU/peak for prior phases. Gateway bulk samples
are the same collector throughout. Full media cost and exact queue/ready waits
remain unknown; no zero substitution.

Total delivered/reserved **25,202,688B =24.03515625MiB**; remaining four primary
phases plan32.046875MiB, leaving7.91796875MiB. P1 collector closed below cap, no
partial tail. Final terminal review and reverse contrasts remain mandatory.

### Original control qualifications

Exactly8,400,896B delivered/reserved (8.01171875MiB). Main six phases plan
48.0703125MiB including small probes; **planned is not sent**. Total ceiling64MiB,
150s/request. All six loaded probes overlap single bulk. Gateway CPU/RSS above
covers the whole process (73 samples), not owner-only. Android CPU/RSS and full
media/retry bytes were not sampled in this original control; unknown, not zero.
Observed SHA256 is not a pre-known-origin digest.

Existing bounded journald continuation parser recovered two terminal records
missed by the original line-by-line reader (both versions retained):
- `bcd5957e…`,12:27:10UTC: `recovery_exhausted`, head retries8, protocol_errors11
  over the **whole existing session**,510 retransmissions. Owner attribution and
  pre-load error count are unproven; this is not11 new download failures.
- `b1dc0aab…`,12:29:37UTC: broker `lifetime_expired`, RS cancelled,
  protocol_errors0 over that session; not proof the other session was clean.
Both closures are logged later than all measured bodies; no incomplete download
is inferred. Histories dropped446/314 old trace entries, respectively. Original
control is retained for delivery/speed context but **not clean acceptance**;
missing pre-load counters/attribution are not filled with zeros.

### P2a delivery and late P1a terminal update —13:22UTC

Owner export `(7).json` binds new session `4b6668ba…`; Android and gateway each
report local send32/receive32, peer32/effective32, CREDIT128/131072 and local-write
completion Q1=true. This is actual application, not just operator/UI intent.
Android already reports **1 protocol error before load**; its cause is unknown.
Gateway startup counter is0 in its separate scope. Do not subtract one endpoint's
counter from the other's or blame the preload error on the later measurements.

P2a requests span13:16:53.541→13:17:52.394UTC:15/15 valid HTTP/TLS/body receipts,
8,400,896B, observed SHA256 with the same external-origin limitation as other
phases. Single4MiB24.89s=1.348109Mbit/s; parallel2×2MiB14.64s=2.291969Mbit/s.
All six loaded probes overlap the single transfer. Idle n6 median/max
2.654272/3.361555s; loaded n6 2.460405/3.483448s; no p99 estimate.
Versus P1a: single−3.74%, aggregate+0.068%; no added Q1 speed gain established.
Versus P0a: approximately2.037× single/1.922× aggregate, but neither denominator
nor candidate is a clean-session acceptance sample. Reverse observations remain
necessary; no multiplied historical speed claims or product admission.

Whole gateway CPU6.685% one logical core, RSS47540→53212KiB (observed maximum
53212), shared-process scope. Collector ended normally: no cap hit, partial tail
or parse error; all four completed phase collectors stopped.13:22:48 readback
confirms unchanged gateway PID703785/invocation052c9a94…, binaryae527cbd…,
profile24c040c0…, same installed97 and one TUN. Android point PSS165328/RSS274900KiB,
swap110KiB; CPU33% is a historical OS window15:14:59→15:19:59 phone local time,
not an isolated phase CPU measurement or one-way time correlation. Different
point samples/GC/background are not proof of a Q1 leak. Full media bytes, queue age
and necessary/early/late retry classification remain unknown.

The same preflight export preserves P1a Android history still at0 errors at
13:15:03.127UTC. Gateway terminal13:15:12.598UTC independently reports3 whole-
session Mux protocol errors,370 retries/1,896,868 retryB, RS `recovery_exhausted`
with head retries8. This is after all measured P1a bodies near the ordinary manual
disconnect; the first protocol-error time and causal branch are not known.
Retain `post-P1a-p2a-preflight.json`: **P1a is not clean acceptance**, but these
terminal observations do not negate already complete downloads. Android history
is not a terminal success receipt. No error is relabelled benign or discarded.

Total now60/60 delivered responses,33,603,584B=32.046875MiB, including original96
control. Remaining P2b/P1b/P0b plan24.03515625MiB;7.91796875MiB remains unspent
reserve under64MiB after the planned series. No new traffic is started while
awaiting the same-session Android post-P2a export. The next P2b requires an ordinary
manual reconnect retaining P2 and a **new session tag**; `scope.py` rejects tag
reuse before a phase can begin. No gateway restart or policy rewrite is needed
between P2a/P2b. Final P0 return is still mandatory.

### P2a post-export and reverse gate —13:27UTC

Export `(8).json`, saved privately as `android-p2a-post.json`, matches current
session `4b6668ba…`, connected97/READY/MESH and actual32/32/peer32/effective32,
Mux128/Q1. `post-P2a-p2a-post.json` records Android protocol_errors **1→10 (+9)**
between13:15:43.692 and13:26:48.048UTC (664.356s). This interval includes measured
load and about nine minutes after its last body; no snapshot pins which part saw
the increase. It is wrong to call all nine either load failures or harmless late
shutdown errors. Terminal reason NONE, reliable terminal empty, publisher/subscriber
connected; no fallback or same-session reconnect demonstrated.

Same-scope Android deltas:89 retransmissions,555,804 retryB,88 recovery timeouts,
1,099,616 sent MuxB,8,798,308 received MuxB; DNS errors0 and TCP-open errors0.
These are not equal-duration comparisons with P1a's191.702s or P0a's341.995s
export intervals, not full outgoing media cost, and not proof of89 network losses
or89 premature local attempts. Necessary/early/late classification remains unknown.

Bounded source review of the sealed Mux counter sites distinguishes unknown/removed
stream, invalid state/credit/FIN/CLOSE and missing/completed DNS-call responses.
The aggregate counter does **not** identify its branch. DNS success/error totals
cannot rule out late unmatched DNS replies, nor prove that explanation. No Q1 or
Mux patch is made without a reproducer. The current192-entry Android trace begins
13:22:49.878UTC, after measured bodies, and retains only reason NONE;365 older
trace entries and326 delivery entries were dropped. Missing earlier trace is not
evidence of no earlier error. The export's old DNS/READY events predate this P2
session and are not reclassified as its failures.

13:27:53–57UTC read-only checks confirm same gateway binary/profile/process,
current P2 policy, installed97/native, owner identity and READY/security binding.
No P2 terminal receipt is present in the bounded server journal; this is not a
zero server-error count or completed-close receipt. Point phone PSS133077/RSS242804KiB,
swap108KiB; CPU30% is a later OS window, not phase CPU or memory maximum. No load,
profile write, restart, security operation or additional collector was started.

**Gate decision:** P2a excluded from clean acceptance. All15 bodies completed and
there is no observed terminal/authentication/route failure or established Q1-specific
defect; permit only the already declared fresh-session **P2b observation**, without
changing parameters or treating a better repeat as erasure of P2a. Ordinary manual
Disconnect → retain P2 → Connect → new diagnostic export; actual both-end/new-tag
preflight must pass before traffic. New terminal/fallback/incomplete-delivery evidence
stops that phase. No additional sweep or attempt beyond the frozen sequence.
Then P1b/P0b and verified owner return P0. Budget remains32.046875MiB used.

### P2b reverse observation —13:34UTC

Export `(9).json` confirms a genuinely new session `538e91ad…`, not reuse of
P2a. Both endpoints report32/32/peer32/effective32, CREDIT128/131072 and Q1=true;
Android preflight and gateway startup counters0. Same gateway epoch/profile/binary,
Android97/native, cellular underlay343, meter and bounded instrumentation. No policy
rewrite/restart between P2a/P2b. Scope and traffic ledger checks passed before load.

15/15 bodies completed13:33:19.553→13:34:16.128UTC;8,400,896B, single4MiB26.95s
=1.245062Mbit/s, parallel2×2MiB13.18s=2.545860Mbit/s. Small idle median/max
2.298595/2.909742s,n6; loaded2.685517/3.663040s,n6, all overlapping single bulk.
No p99 or repeated Q1 speed-gain claim: the order-matched P1b contrast is still
pending. All request records, TTFB, observed hashes and external-origin digest
limitation retained. Gateway whole-process CPU6.973% one core; RSS47308→53916KiB,
max53916. Collector stopped normally, no cap hit/partial tail/parse errors.

The new export also archives old P2a Android at10 errors13:31:35.785UTC, not a
terminal success receipt. Gateway P2a terminal13:31:46.155 reports1 whole-session
Mux protocol error,395 retries/2,121,772 retryB, RS `recovery_exhausted`, head8,
5 pending DATA. These are after delivered bodies near ordinary manual disconnect;
first protocol-error time and causal relation to close remain unknown. Saved in
`post-P2a-p2b-preflight.json`, separate from the earlier post-export. Do not sum
overlapping snapshots or erase P2a failure because P2b delivered all bodies.

13:34:39–42UTC readback confirms same gateway epoch/hash and owner identity/READY;
one TUN remains. Android memory projection is empty (unavailable, not zero), and
OS CPU window predates P2b; neither is a P2b resource measurement. Current P2b
Android post-export and final terminal review remain required. No final server
error count is inferred from its startup0. All five completed collectors stopped.
75/75 responses delivered across original control and four main phases;
42,004,480B=40.05859375MiB. Remaining P1b/P0b plan16.0234375MiB; reserve7.91796875MiB.
Next: post-P2b export **before disconnect**, then prepare owner next P1 for the
ordinary manual switch; finally P0b/verified return. No extra P2 attempt or tuning.

### P2b post-export and owner-only next P1 —13:40UTC

Export `(10).json` is the same current P2b session `538e91ad…`, connected97/READY,
actual32/32/peer32/effective32/CREDIT128/Q1. Android protocol errors remain **0→0**
from13:32:20.288 to13:37:33.911UTC,313.623s including load and background.
Terminal reason NONE, reliable terminal empty. Pre-existing TCP-open error1 stays1
(delta0); DNS error delta0. Neither is a new measured HTTP failure. The15/15 body
results stand; whole-session two-end closure still pending, not clean admission.

`post-P2b-p2b-post.json` retains +48 RS retransmissions/+403,405 retryB,+46 recovery
timeouts, +1,066,099 sent/+8,518,661 received MuxB in that Android interval. Duration
differs from P1a/P2a; counters include background and are not full media cost or
classified necessary/early/late attempts. Do not infer a Q1 retry-rate improvement
from these totals. No final P2b server error count is yet available.

Read-only13:38:44–48UTC checks preserve owner identity/READY, gateway process,
binary/profile hash and Android97/native/TUN. Phone point PSS135238/RSS244360KiB,
swap108KiB and OS CPU24% over15:29:59→15:34:59 phone-local are outside-load
readback/mixed-window observations, not phase peak or isolated P2b CPU.

At13:40:04UTC the existing protected owner-targeted operator policy is prepared
from P2 to **next-session P1** (`policy-p1b-prepared.json`).13:40:05–10 readback
confirms P1 intent, same PID703785/invocation052c9a94…, gatewayae527cbd… and
profile JSON24c040c0…, global OFF/LEGACY64/countersOFF. No restart, other-user
profile change, new payload traffic or identity/security mutation. The active
P2b session remains Q1; prepared intent is not an applied P1 receipt.

Next single manual workflow: **Disconnect → Settings P1 → Connect → fresh JSON**.
Both-end new-tag32/32/Mux128/**Q0** preflight is required before P1b load. Remaining
P1b/P0b and final verified P0 are unchanged;40.05859375MiB used, all collectors off.

### P1b reverse observation and late P2b closure —13:48UTC

Export `(11).json` confirms new session `1bd3bd0f…`, actual both-end32/32/peer32/
effective32, CREDIT128/131072, Q1=false. Android preflight and server startup errors0;
same phone97/native, cellular underlay343/TUN, gateway epoch/hash/profile, carrier
and meter. Applied P1 is now proven, not inferred from the prepared operator file.

P1b15/15 bodies completed13:47:13.522→13:48:07.473UTC;8,400,896B. Single4MiB25.34s
=1.324169Mbit/s; parallel2×2MiB12.99s=2.583097Mbit/s. Idle n6 median/max
2.257751/3.067726s; loaded n6 2.725028/3.657239s, all fully overlapping single bulk.
No p99. Same observed SHA256/external-origin qualification, HTTP/TLS checks and
raw request records. Whole gateway CPU7.232% one logical core, RSS49976→54680KiB,
observed max54680. Collector stopped normally with no cap hit/partial tail/parse
error. All six completed collectors are off; post Android/terminal review pending.

Old P2b Android history now reports2 errors at13:45:20.168UTC, versus0 at the
post-bulk13:37:33.911 snapshot: a proven **later increase**, not two failed measured
downloads. Gateway terminal13:45:30.233UTC reports1 whole-session protocol error,
364 retries/2,150,392 retryB, RS `recovery_exhausted`, head8,4 pending DATA. Timing
is after bodies near manual disconnect; exact first server error time/close cause
unknown. `post-P2b-p1b-preflight.json` preserves both; P2b excluded from clean
acceptance. Android history is not proof of successful terminal closure. Overlapping
counter snapshots are not added; no Q1-specific cause is established by these totals.

Q1 comparisons are now available in both orders (not clean acceptance):

| Contrast, P2 relative to P1 | Single | Aggregate | Idle median/max | Loaded median/max |
|---|---:|---:|---:|---:|
|P2a / P1a, forward|−3.736%|+0.068%|+6.505% /+17.669%|+10.911% /+8.565%|
|P2b / P1b, reverse|−5.974%|−1.442%|+1.809% /−5.150%|−1.450% /+0.159%|

No repeatable added Q1 speed gain is established. The local9→1/8→0 correctness
result remains separate. Observed speed changes do not cross the frozen10%
regression trigger, but that does **not** waive protocol/closure/resource gates;
n6 latency is not a proof of no tail regression. Sessions/background differ and
wire/early-local-retry classification remains unknown. Final P0b is still needed
for the order-matched windows contrast; no substitution with original96 or Linux.

13:48:26UTC readback confirms unchanged gateway process/binary/profile and installed
Android97/native/TUN. Phone point PSS134302/RSS243352KiB, swap108KiB; OS CPU window
predates this phase, not phase CPU. The subsequent supplementary read-only journal
SSH step timed out after30s; preserve `p1b-delivered-observation-attempt1.json`.
One read-only retry uses the same timeout/bound; this is not a body failure, a
transport retry or permission to restart the gateway. That retry reached the
32MiB raw-journal assertion; its failure is retained as attempt2, not discarded.
The minimal helper correction adds an optional UTC `--since` selection, without
raising any byte/entry/time bound or weakening exact-epoch/parser/startup gates.
Read since13:45Z succeeded13:54:59UTC with5,061,871B, parser errors0, same epoch,
P2b terminal and P1b startup included. It is a supplementary receipt, not a new
measurement or zero final P1b error count. Both failed reads remain indexed.
Six local helper tests pass, including generated observer scripts with/without the
UTC filter and retained entry/byte/timeout/epoch bounds (`observer-filter-tests.log`).
90/90 responses delivered;50,405,376B=48.0703125MiB. Remaining P0b8.01171875MiB
leaves7.91796875MiB reserve. Next post-P1b export without disconnect, then prepare
owner next P0 and finish P0b/verified return; no more P1/P2 runs or tuning.

### P1b post-export and owner-only next P0 —14:05UTC

Owner export `(12).json`, copied privately as `android-p1b-post.json`, SHA256
`ba52db1aa0ae92d6235f1463479d2a52e00219fab1d3d8633d073de62f5ba5da`, matches
the supplied file byte-for-byte. It remains current session1bd3bd0f… CONNECTED,
actual32/32/peer32/effective32, CREDIT128/131072, Q1=false. Android snapshot
14:00:03.206UTC has protocol_errors1 versus preflight0 at13:46:11.528UTC:
**+1 over831.678s**. The interval includes measured load and subsequent background;
exact first-error time and Mux branch are unknown. Do not classify it as necessarily
during load, harmless after load, a lost download or a Q1 defect (this is Q0).
The15 completed HTTP bodies remain completed; clean acceptance is excluded.

`post-P1b-p1b-post.json` retains deltas:95 retransmissions,534387 retry bytes,
94 recovery timeouts,1175115 sent/8736233 received Mux bytes, DNS/open errors0.
Do not normalize these mixed831.678s session deltas by the short8MiB bulk phase
or compare them directly with shorter export intervals; early/local/necessary
retry classification remains unknown. Android terminal reason NONE, reliable
terminal empty. No matching gateway terminal receipt yet in the bounded journal;
that is not a successful final-close receipt. Whole-wire cost remains unknown.

Readbacks14:04:27/14:04:56UTC preserve installed97 APK/native/UID, identity hashes,
READY97, gateway ae527cbd…/PID703785/invocation052c9a94… and profile JSON24c040c0….
Owner-only next-session policy changed P1→P0 at14:04:55UTC, with atomic existing
operator workflow (`policy-p0b-prepared.json`), **no restart**. Global defaults,
pacingOFF, LEGACY64/countersOFF and other users are unchanged. Existing P1b OPEN
limits are not mutated. Fresh gateway activity still belongs to1bd3bd0f…;
`observation-p0b-prepared.json` uses the same bounded13:45Z filter,10216898B,
parser0. Old failed supplementary reads remain retained separately.

No additional payload, build, installation, deployment or collector in this step.
Budget remains48.0703125/64MiB. Next manual action is Disconnect → Settings P0 →
Connect → fresh diagnostic export. Verify a new tag and actual both-end8/16/
peer16/effective8/LEGACY64/Q0 before the final P0b8.01171875MiB load. Reconcile
P1b closure from the next receipts; do not call P0 already applied or the final
return verified. No further P1/P2 runs or parameter tuning.

### Final P0b attempt, scheduled renewal and stopped matrix —14:20UTC

Export `(13).json` identifies new session
`a6a3855ad423efc5e29ea68983277a051d327117fb8c36d2a644bc7ed5d9a812`.
Android and gateway agree P0, RS8/16/peer16/effective8, LEGACY64/65536, Q1=false,
initial protocol errors0. Installed97, underlying cellular343/TUN and the exact
meter/instrumentation remain the same. `scope-P0b.json` passes all unchanged gates;
no OPEN parameter was changed in the previous session.

Measured14:10:02.556→14:11:34.163UTC (controller clock):12 small bodies and single
4MiB complete; single51.29s,0.654210Mbit/s, request TTFB0.954136s. Idle n6
median2.2421755/max4.291554s, loaded n6 median3.4343755/max4.865721s; all six
loaded probes overlap single. No p99 claim. Both2MiB parallel requests return
HTTP200 but **curl18 / incomplete bodies**:855726B and790208B, not2097152B each.
Their intervals22.743026/22.739138s and observed SHA values remain in the raw
requests, not in completed-goodput acceptance. The cell's raw partial byte-rate
is retained for audit only; normalized `completed_goodput_mbit_s=null`.
The subsequent `ip route get`/TUN topology guard fails and the phase exits1;
no timeout/retry suppression or failure-handler change.13/15 complete, no rerun.

**External cause is established for this event, not assumed from a profile hash.**
Existing RU service journal and coordinator transaction agree operation
`scheduled-1792591872-28bb9be0fa02eed7`, result COMMITTED, gate RENEWAL_READY,
`zero_downtime=false`, pre-stop session inventory UNKNOWN. Same-host journals show:

- RU renewal starts14:11:11.796UTC; COMMITTED receipt14:11:40.781UTC.
- NL systemd starts stopping bootstrap14:11:24.021UTC, stopped14:11:24.142UTC;
  sessiona6a3855a… terminal14:11:24.035UTC has protocol_errors0, RS `cancelled`,
  IO_CLOSED, first close UPPER_CLOSE, no first failure. This is cancellation during
  incomplete delivery, **not successful drain**.138 retries/961693retryB are
  whole-session gateway totals, not local-premature/network-loss classifications.
- NL bootstrap starts14:11:33.957UTC, PID775194/invocationa5b5909d… versus
 703785/052c9a94…. Same binary ae527cbd…. Config flags still P0/OFF/LEGACY64/
  countersOFF. Correlation uses operation/session IDs; host clocks are not used
  to infer one-way latency or an exact Android TUN outage duration.

The archived **exact** old gateway JSON hashes24c040c0… and current738e5f52….
Read-only per-field comparison finds only `certificate` and `revocations` changed;
`private_key`, `authority`, `family`, `gateway`, `minimum_crl`, `minimum_revision`
are identical. These eight fields are the full profile key set, not transport
settings. No private values are exported by the comparison. Other runtime directory
publication is not covered by that field equality. Existing renewal/grant/floor
policy was neither changed nor disabled. No forced renewal, task restart, rollback,
APK change or load was performed after the abort. The earlier11:41 unexplained
event is **not retroactively attributed** to this proven operation.

Receipts: private `NL-p0b-state-change.json`, `RU-p0b-state-change.json`, safe
`p0b-profile-delta-archive.json`. The first read-only profile probe found no active
owner file because the operation was already archived; its stderr is retained.
The next read uses that exact completed operation's existing archive, with old/new
file hash assertions. No recovery controller was executed. Initial line-at-a-time
capture parsing missed a split terminal JSON: both errors remain in
`phase-P0b/line-parser-attempt.json`; the existing bounded, stream-bound continuation
parser recovers terminal0/cancelled, no remaining parser errors. Nine helper tests
pass, including partial-body qualification and incomplete-continuation rejection.
This only changes offline reporting; the HTTP meter and installed code are untouched.

P1b closure is separately reconciled from `(13)`: Android history stillerrors1
at14:08:21.507UTC; gateway terminal14:08:30.053UTC reports3 whole-session errors,
408 retries/1915499retryB, RS exhaustion/head8/pending2. It occurs after its measured
bodies; exact error branch unknown, not a lost P1b download. Keep it excluded from
clean acceptance. Do not mix these old-session totals with P0b's counters.

P0b CPU5.858% of one core and RSS47624→51868KiB/max51868 describe old gateway
PID703785 only,78 samples14:10:02.840→14:11:23.413UTC; not a new-process or full-
failure-interval estimate. Android CPU/PSS remain point readbacks with OS-defined
windows, not phase attribution. Full media/queue-age costs and early retry
classification remain unavailable. The collector ends normally, no byte cap or
partial record; all seven phase collectors are stopped.

All105 attempts remain:103 complete,2 incomplete. Complete responses total
54611968B=52.08203125MiB; partial bodies1645934B=1.569685MiB, total received
56257902B=53.651716MiB. **Reserved/requested58806272B=56.08203125MiB** remains
debited against64MiB; do not refund failed requests or assume the remote source
generated only the received portion.7.91796875MiB unreserved is not an authorization
to repeat/sweep. No successful reverse aggregate exists. P0b single is−19.36%
versus original96, consistent with the unresolved earlier P0 drift, not proof of
its code/path cause. P1/P0 idle median changes−7.169%/+0.695%, idle max−26.510%/
−28.517%; loaded median−27.015%/−20.654%, max−15.635%/−24.837%. These n6
observations do not erase phase failures or establish a reliable latency tail.

14:19 readback: installed97/native unchanged, gateway active in new epoch above;
identity hashes preserved, ordinary READY97 refreshed with minimumCRL27150 and
new expiry. Gateway reports new **P0** sessiond0ca9226… at14:12:41.307UTC, startup
errors0. No assistant-driven reconnect took place. This is a server-side recovery
observation, not yet proof of Android automatic recovery/full TUN usability.
Next: current Android diagnostics, including interrupted session history, **without
profile switching or another load**. Final current Android P0 confirmation remains
pending; no clean/product admission, tester rollout or new architecture work.

### Final owner receipt and closure —14:30UTC

Export `(14).json` is privately preserved as `android-owner-p0-final.json`.
`owner-p0-final-receipt.json` matches current sessiond0ca9226… between Android and
the gateway startup receipt: P0,8/16/peer16/effective8,LEGACY64/65536,Q1=false.
Android14:28:49.848UTC reports CONNECTED/READY/capture open, no terminal error,
**17 protocol errors in this new session**. Gateway0 is its startup counter, not
a final opposite-end zero or an Android baseline; do not subtract them. The exact
error onset/branch is not established, nor are17 failed downloads inferred.
This confirms the selected/applied return to P0, not clean transport health.

Interrupted P0b history is independently reconciled in
`post-P0b-owner-p0-final.json`: Android snapshot14:11:34.112UTC, errors0→0,
IO_CLOSED/`recovery_exhausted`; interval deltas46 retries/334507retryB/45timeouts,
1100040 sent/5985389 received Mux bytes, DNS/open errors0. Server's old-epoch
terminal0/`cancelled` remains in the captured phase analysis, not the new-epoch
journal. Different endpoint shutdown outcomes do not contradict the proven
renewal interruption and neither is success. Do not merge history with current17.

14:30 readback retains same installed97/native/signer/UID, gateway ae527cbd…,
PID775194/invocationa5b5909d…/profile738e5f52…, identity preserved, READY97 and
normal CRL27150. The current VPN object is present; **no additional active route,
DNS/HTTPS or load check was run after renewal**. Automatic network-loss recovery
and overnight stability remain NOT_RUN; a new session alone proves neither.
No restart, profile write, deployment, identity change or payload in this closure.

**Decision:** close the measured cycle with all qualifications. P1 has a promising
roughly2× raw single observation in both orders, but original/new P0 consistency,
protocol/closure errors and missing reverse aggregate block clean/product admission.
Q1 retains local correctness value without added observed speed. Keep owner P0.
No more exports, load, tuning or implicit follow-up branch; investigation of the
remaining error path requires a separate decision. All105 attempts, failed parallel,
helper failures and nine passing helper tests remain indexed; all collectors off.

## SIGNED_APK_PATH_AND_SHA256; CURRENT_OWNER_AND_GATEWAY_STATE

- Installed owner-only97: `com.familyconnect.app.friends`, UID10283,
  `0.1.18-beta97-speed`. Signed APK:
  `state-client-build/speed-candidate-20261021/delivery/FamilyConnect-0.1.18-beta97-speed.apk`.
  SHA256 **`d7c02ef5e947733702490c2bf5b6afc0d17dbcb5f19b44eca478d621dfcf928f`**.
  Existing signer `67a90d1b…`; identity/SupportID hashes unchanged. READY97 verified.
- Running gateway `ae527cbd…`, PID775194/invocationa5b5909d…, profile738e5f52…;
  global/owner policy P0, OFF/LEGACY64/countersOFF. Proven scheduled renewal, not
  a task-triggered second restart. P0b was verified both ends before interruption;
  new P0 sessiond0ca9226… is confirmed both ends by final `(14)`, Android
  CONNECTED/READY with17 protocol errors, no terminal at snapshot. No elevated-
  profile enablement or binary rollback; not a clean-health claim.
- Exact734 binary rollback is staged in the existing protected workflow. No
  rollback has been executed. Returning profiles to P0 needs no APK downgrade,
  credential restoration, identity reset or security-history rollback.
- Original P0, new P0a/P1a/P2a/P2b/P1b complete; P0b13/15 with two partial responses.
  Total52.08203125MiB complete plus1.569685MiB partial;56.08203125MiB reserved.
  Local loopback/Pion traffic remains separate. No tester/public distribution,
  authority changes, push, purchase, migration or additional research.
- Five prep-only disposable identity directories and old/new private process
  profiles were cleaned. All seven phase collectors stopped in the meter's finally
  block; interrupted P0b history and current applied P0 are now reconciled.

Cycle closed: keep P0, no more owner actions or exports and no automatic repeat.
Preserve unresolved original/new P0 consistency, all errors and final verified
profile (not clean transport health). No product admission or distribution.

[Executable preparation and replay guide](../../tests/fixtures/speed_candidate/README.md).
