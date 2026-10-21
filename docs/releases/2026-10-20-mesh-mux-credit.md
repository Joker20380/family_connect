# Single-flow MESH / Mux credit —20 October2026

## Final return confirmed —20.10 13:39:52UTC: LEGACY64, experiment CLOSED

Owner's ordinary manual reconnect created VPN336 at13:34:19.180UTC, same cellular327/
tun1. New owner session tag
`b502c9dda1ab4368704aa7bebe24669a6cb42bae29285f4915a3cc868a4728e2`:
AUTHORIZED13:34:28.421345UTC, Family TLS ESTABLISHED13:34:43.058325UTC,
gateway session ESTABLISHED13:34:44.877402UTC. Former B3 tag`791977aa…` closed during
the manual reconnect; it was not reinterpreted as64.

Actual Mux snapshots confirm **LEGACY64/65536** for this new authenticated session.
Common TLS ALPN`family-connect-5n3-test-v1`, exact installed native/server source
mapping and actual server Mux bind **65536 bytes per stream/direction on Android
and NL**, including ring and initial credits. This is not CONNECTED or configured
preference alone; no independent Android live Mux counter export was read.
Return-session protocol_errors **1→1** across the short readback; exact establishment
counter is unknown. Preserve that error without attributing its cause to CREDIT128,
resetting it or combining it with B3's0→0 load interval. No HTTP request was issued.

Unchanged pair, verified again at13:39:52.287282UTC:
- Owner beta95/A0, same package/UID10283/PID9374. APK SHA256
  `e36a24601d459ea13553d9236486befe514dca496d8b2933290e6867d97c4159`;
  native`66a9d18d04ff71100df0144228db05decb970aea71b6d277ec321b1c6c240c63`.
- Compatible gateway SHA256
  `272bbc3fed90bbcf740a58f812e93511c976c114e2190f2c8711b55fa0dfb0c4`,1011 preserved;
  same PID3937546/invocation`17ec5abfcbc84a9d913e844193e0d931`, NRestarts0.
  Current credential-profile hash unchanged from A3/B3; no identity, credentials,
  floors, admission, registration, signer or package changes made here.
- Active profile **LEGACY64**; protected operator policy **LEGACY64**,128 disabled
  for new sessions. Counter-off receipt and final readback both confirm **OFF**.
  Known temporary remote collector/journal-follower and local collector/meter audits
  return empty PID lists. No background wait remains.

Only bounded existing readback was used. A locally invalid readback label and a
remote projection quoting error were repaired; the failed projection's finally
path disabled counters before retry. These are helper failures, not transfer failures;
`return_attempt_repairs` retains them. No product/fixture implementation change,
bulk/control request, speedtest, build/install, gateway restart or rollback occurred.
Additional measurement bytes **0**; experiment total remains50921472B =48.5625/64MiB.

Final private receipt:
`state-client-build/mux-profile-20261020/manual-return64-result.json`;
latest pointer`manual-continuation-result.json`. Supporting files in the same capsule:
`return-legacy-session-readback.json`, `return-legacy-profile-proof.json`,
`return-legacy-owner-scope.json`, `return-legacy-closed-readback.json`,
`return-legacy-local-collector-audit.json`, `policy-Return64retryoff.json`.
Prior phase receipts and tests remain unchanged; sanitized negotiated JSON updated.
Offline closure/source-pin checks and `git diff --check` PASS; receipt
`return-legacy-validation.json` retains the repaired validation-root mistake
(actual Android sources are `android-source/carrier`, not the functional-only root).

**Compatibility PASS** from completed actual old/new checks; **speed INCONCLUSIVE**
from the three pairs below; **working profile LEGACY64**. Return is confirmed and
the experiment is closed. No further owner action, load, rollout or tuning is pending.

## Final three-pair result —20.10 13:24UTC: INCONCLUSIVE

**Measurement experiment CLOSED.** No fourth/fifth pair, new implementation, build,
APK, deployment, gateway restart, new tuning branch, push or public release in this
continuation.24/24 phase HTTP requests completed; all full bodies consumed through
Android TUN using the same HTTP/1.1 endpoint, pinned meter and bounded counters.
Including preceding three64KiB controls, actual/reserved traffic is50921472bytes =
**48.5625MiB of64MiB**,15.4375MiB unused.150s/request, HTTP retry0, no failed request
removed from results. Earlier zero-traffic preflight failures remain in evidence.

### Separate decisions

- **NEGOTIATION_AND_LEGACY_COMPATIBILITY: PASS.** Actual old/new cross-process
  matrix5/5 and unchanged local security/race tests reused, not rerun/recounted.
  LEGACY64 and CREDIT128 physically observed on the same95/compatible-gateway pair.
  Certificate claim/authorization and bootstrap1011 unchanged. Testers stay94.
- **CREDIT128_CORRECTNESS: LOCAL PASS; bounded physical delivery PASS.**24/24 phase
  HTTP requests finish with no load protocol-error increments, measured streams
  close empty. This is not independent physical origin-byte-exact, all-network,
  continuous-TUN-gap, or whole-process/multi-user memory-cap acceptance.
- **PHYSICAL_SINGLE_FLOW_GAIN: positive direction3/3, uncertain magnitude/attribution.**
  +24.93%, +89.32%, +3.65%. Credit relief repeats, but background DATA and media/ACK/
  retry conditions differ. Do not assign the full A2/B2 difference to window. In
  final pair, single phone-wall improvement is1.68s (47.70→46.02), HTTP body interval
  only44.912984→44.090789s; setup/TTFB also differs.
- **AGGREGATE_LATENCY_MEMORY_AND_FAILURES: mixed.** Final pair aggregate−13.61%,
  control full latency+23.28%; earlier pairs disagree. No new measured failures,
  but expected ring memory increases and shared RS stalls remain. Control is
  application latency, not RTT; a single control per phase is limited evidence.
- **Owner-use decision: INCONCLUSIVE, not ACCEPTED_BOUNDED_ON_OWNER.** Mechanism
  change is real; useful balanced speed/latency improvement is not established
  sufficiently to make128 the owner default. This is not proof128 has no benefit
  or a demand for universal-network proof. Leave128 disabled for new sessions,
  preserve implementation/results and stop this experiment, not another tuning round.

### Three paired comparisons (new pair throughout, never old b9 as A)

A=beta95/A0 +compatible gateway/LEGACY64; B=same binaries/CREDIT128. B1 is recorded
as directory`B1m`; the earlier`B1` preflight sent no HTTP. Gain columns are B relative
to its paired A regardless of order. Goodput uses actual common phone BEGIN→END;
control latency uses unrounded curl full time.

| Order | Single A→B Mbit/s | Gain | Aggregate A→B Mbit/s | Gain | Control A→B full s | Latency change | Completion A/B | Load protocol_errors A; B |
|---|---|---:|---|---:|---|---:|---|---|
| A1/B1 |0.647020→0.808346|+24.93%|1.195810→1.299552|+8.68%|4.943254→6.625675|+34.03%|4/4;4/4|1→1; 1→1|
| B2/A2 |0.424417→0.803507|+89.32%|0.998644→1.211351|+21.30%|5.042774→4.298021|-14.77%|4/4;4/4|2→2; 0→0|
| A3/B3 |0.703447→0.729127|+3.65%|1.224168→1.057499|-13.61%|4.454774→5.491793|+23.28%|4/4;4/4|1→1; 0→0|

### B3 session, errors and recovery scope

Owner manual VPN335 created13:17:14.891UTC, same cellular327/tun1, UID10283/PID9374.
New tag`791977aa5b4ffcf25d56644eee24b95f1af35fff3ca5a1a650065989285f21fc` established
Family TLS13:17:34.745479UTC. Actual gateway Mux CREDIT128/131072 observed; common
TLS ALPN`family-connect-mux-credit128-v1` plus exact installed native/server mapping
binds both endpoint windows131072. Not merely CONNECTED/preference and not an
independent Android live counter export. `b-three-profile-proof.json` retains pins.

Same gateway PID3937546/invocation`17ec5abfcbc84a9d913e844193e0d931`, binary and renewed
credential-profile hash as measured A3. Old A3 CLOSED/FAILED events during owner's
manual disconnect are outside B3, not a new128 fault. The earlier **pre-A3 external
process/credential refresh** and interrupted initial A3 media session remain in
comparison context; this task did not initiate them. No exact external-network
culprit or uninterrupted session across that refresh is claimed.

Protocol_errors at exact B3 establishment: **UNKNOWN_NOT_SAMPLED_AT_ESTABLISHMENT**;
no sampler was left waiting for the manual action. First cumulative observed value
13:19:23.902596UTC=0; pre-control13:20:21.902669=0; pre-bulk13:20:27.902289=0;
post-load13:21:51.902172=0; final active readback13:24:45.943723=0. No resets.
Previous sessions' initial1/2 errors are retained, not subtracted across epochs or
attributed to128. No B3 owner FAILED/CLOSED/reconnect in capture; VPN335 unchanged
at checked boundaries. Continuous subsecond TUN gaps were not instrumented.
All B3 measured Mux IDs37/41/47/49 close empty by capture end; control/single were
still closing at their first after-request snapshot, not indefinitely retained.
Existing collector ends normally, cap_reached=false, partial_bytes0, reconstruction
errors0. No new profiler/full media trace was enabled.

### Every measured HTTP request (saved original timestamps)

Full/TTFB/body times use curl timestamps, not rounded goodput inversion. Request
Mbit/s below uses body/full; paired single/aggregate table uses common phone wall
and therefore differs slightly. Parallel actual Mux set is shown without assigning
an HTTP row to an ID merely because response sizes match. Each HTTP request reports
one connection; observed gateway Mux DATA validates the path and actual stream set.

| Phase | Request / actual Mux ID set | Body bytes | Full s | TTFB s | Body s | Phone wall s | Body/full Mbit/s | Completion |
|---|---|---:|---:|---:|---:|---:|---:|---|
| A1 |control / {25}|65536|4.943254|2.775929|2.167325|4.970|0.106061|complete HTTP200|
| A1 |single / {27}|4194304|51.841938|2.649338|49.192600|51.860|0.647245|complete HTTP200|
| A1 |parallel/0 / {39,41}|2097152|28.030760|1.086425|26.944335|28.050|0.598529|complete HTTP200|
| A1 |parallel/1 / {39,41}|2097152|27.820742|0.690164|27.130578|27.850|0.603047|complete HTTP200|
| B1 |control / {71}|65536|6.625675|4.661478|1.964197|6.650|0.079130|complete HTTP200|
| B1 |single / {73}|4194304|41.478868|1.594841|39.884027|41.510|0.808952|complete HTTP200|
| B1 |parallel/0 / {81,83}|2097152|25.793190|1.144128|24.649062|25.810|0.650451|complete HTTP200|
| B1 |parallel/1 / {81,83}|2097152|25.377780|0.681424|24.696356|25.400|0.661099|complete HTTP200|
| B2 |control / {25}|65536|4.298021|2.387177|1.910844|4.320|0.121984|complete HTTP200|
| B2 |single / {27}|4194304|41.739897|2.205978|39.533919|41.760|0.803894|complete HTTP200|
| B2 |parallel/0 / {37,39}|2097152|27.407213|0.739781|26.667432|27.430|0.612146|complete HTTP200|
| B2 |parallel/1 / {37,39}|2097152|27.672009|1.086397|26.585612|27.690|0.606288|complete HTTP200|
| A2 |control / {109}|65536|5.042774|3.881590|1.161184|5.070|0.103968|complete HTTP200|
| A2 |single / {111}|4194304|79.041733|3.034492|76.007241|79.060|0.424515|complete HTTP200|
| A2 |parallel/0 / {145,147}|2097152|31.987272|1.727158|30.260114|32.010|0.524497|complete HTTP200|
| A2 |parallel/1 / {145,147}|2097152|33.563924|3.437013|30.126911|33.590|0.499859|complete HTTP200|
| A3 |control / {49}|65536|4.454774|3.474330|0.980444|4.490|0.117691|complete HTTP200|
| A3 |single / {51}|4194304|47.675350|2.762366|44.912984|47.700|0.703811|complete HTTP200|
| A3 |parallel/0 / {59,61}|2097152|27.382714|0.897959|26.484755|27.410|0.612694|complete HTTP200|
| A3 |parallel/1 / {59,61}|2097152|27.130556|0.753513|26.377043|27.150|0.618388|complete HTTP200|
| B3 |control / {37}|65536|5.491793|4.108530|1.383263|5.510|0.095468|complete HTTP200|
| B3 |single / {41}|4194304|45.999420|1.908631|44.090789|46.020|0.729453|complete HTTP200|
| B3 |parallel/0 / {47,49}|2097152|30.692122|0.993168|29.698954|30.720|0.546629|complete HTTP200|
| B3 |parallel/1 / {47,49}|2097152|31.696371|1.118651|30.577720|31.720|0.529310|complete HTTP200|

### Exact wait brackets, background activity and shared RS

Each row records the **counter-delta snapshot interval**, not request duration or a
lifetime counter. Process-local monotonic denominator is retained to nanoseconds;
UTC endpoints identify the snapshots. Cross-clock host/journal offset was not
independently measured. Neighboring brackets can overlap. Mux/RS/head waits overlap:
**do not add them**, and do not sum bracket bytes as disjoint request-local totals.
Shared RS includes background, controls and measurement edges. Background DATA is
owner-Mux total HandedDATA delta minus identified measurement-stream deltas in the
same bracket, not all traffic at every layer. Open-stream count alone is not load.

| Phase/cell | UTC start→end (20.10) | Monotonic interval s | Mux ID: credit stall s / % | Shared RS ready-full s / % | Head unconfirmed/later-SACKed s | RS new/retry bytes | Background streams; handed DATA bytes |
|---|---|---:|---|---|---:|---:|---|
| A1/control |11:42:38.050969→11:42:46.050532|7.999712949|25:0.000000/0.00%|0.466720/5.83%|0.000000|72494/28785|7–7; 24|
| A1/single |11:42:44.050699→11:43:38.050781|54.000027490|27:45.551868/84.36%|16.238159/30.07%|7.479823|4446848/677106|6–8; 229036|
| A1/parallel |11:43:36.050473→11:44:06.050899|30.000649794|39:17.423608/58.08%; 41:17.974398/59.91%|25.346623/84.49%|10.186016|4260413/405438|6–7; 25272|
| B1/control |12:19:24.919853→12:19:32.920157|8.000072777|71:0.000000/0.00%|0.499937/6.25%|0.000000|72173/25550|6–6; 0|
| B1/single |12:19:30.931145→12:20:14.919186|43.988332864|73:0.055200/0.13%|38.546957/87.63%|17.936200|4248437/730502|6–7; 13665|
| B1/parallel |12:20:12.919796→12:20:40.920267|27.999998888|81:0.000000/0.00%; 83:0.044034/0.16%|25.226234/90.09%|11.494405|4299841/493456|5–6; 48155|
| B2/control |12:26:58.635878→12:27:04.634744|5.999420330|25:0.000000/0.00%|1.402559/23.38%|0.853999|73762/7175|5–6; 1115|
| B2/single |12:27:02.634798→12:27:46.635077|44.000208974|27:0.486611/1.11%|39.494137/89.76%|17.434159|4307268/662246|6–7; 91745|
| B2/parallel |12:27:44.634837→12:28:14.634913|30.000038937|37:0.000000/0.00%; 39:0.000000/0.00%|27.238742/90.80%|12.499994|4335911/669383|6–6; 101270|
| A2/control |12:42:08.767034→12:42:14.767510|6.000327442|109:0.000000/0.00%|0.501387/8.36%|0.000000|72140/0|12–12; 0|
| A2/single |12:42:12.767765→12:43:34.767437|81.999818083|111:70.728292/86.25%|39.682467/48.39%|20.713202|4567746/1045442|13–18; 325249|
| A2/parallel |12:43:32.767699→12:44:08.767679|36.000041220|145:20.307436/56.41%; 147:17.880387/49.67%|27.941977/77.62%|10.121337|4246781/543037|15–15; 11468|
| A3/control |13:10:26.944031→13:10:34.943867|7.999826774|49:0.074033/0.93%|0.365562/4.57%|0.000000|72279/0|9–9; 24|
| A3/single |13:10:33.013785→13:11:22.943689|49.929902477|51:38.065180/76.24%|17.929618/35.91%|7.403870|4409263/576762|8–10; 190987|
| A3/parallel |13:11:20.944025→13:11:50.943922|29.999986263|59:15.697081/52.32%; 61:13.862905/46.21%|26.434783/88.12%|12.247308|4250456/588273|7–8; 15312|
| B3/control |13:20:21.902669→13:20:29.902660|7.999095136|37:0.000000/0.00%|0.633684/7.92%|0.168739|76201/2940|6–6; 3731|
| B3/single |13:20:27.902289→13:21:15.902443|48.000143043|41:1.409007/2.94%|44.167292/92.01%|21.803470|4302607/746974|6–7; 67004|
| B3/parallel |13:21:15.902443→13:21:49.902266|34.000016877|47:0.000000/0.00%; 49:0.000000/0.00%|29.554101/86.92%|15.829098|4244680/576689|5–6; 9923|

A2 single background13–18/325249B versus B2 6–7/91745B; A3 8–10/190987B versus B3
6–7/67004B. These unequal activity levels remain limitations despite the same quiet
phone instruction. Same underlay ID327 does not establish equal radio/media/ACK
conditions. Per-stream before/after values, exact node_ns endpoints, window-only and
both head-wait categories are preserved in`final-three-pair-comparison.json`.
B3 single credit1.409s/48.000143043s (2.94%) but RS ready-full44.167s (92.01%),
head-unconfirmed21.803s and746974 retry bytes. This is the **remaining observed
limiter: shared RS occupancy/head/retry**, not proof of a particular external link's
fault or a new RTO/SACK/pacing work item. No additional investigation starts here.

### Memory and failures

| Phase | Whole-gateway RSS max KiB | CPU % one core | Owner Mux retained high-water bytes | Measured requests |
|---|---:|---:|---:|---|
| A1 |44028|6.554|658198|4/4|
| B1 |59484|6.608|1081434|4/4|
| B2 |63636|8.410|1179736|4/4|
| A2 |67936|8.570|1376300|4/4|
| A3 |45100|6.660|737280|4/4|
| B3 |50072|6.716|1179648|4/4|

A3/B3 use the same new gateway process; prior pairs used its predecessor. Other
sessions/stream counts coexist, so RSS is not a window-only causal comparison. B3
ends6 background streams/786432 retained bytes, all measured streams closed empty;
A3 ends7/458752. No benchmark queue accumulation is presented as stability. The
[ADR](../adr/2026-10-20-negotiated-mux-credit.md) retains ring/queue/staging accounting:
16/32 streams require2/4MiB CREDIT128 rings per endpoint versus1/2MiB legacy, with
separate TLS/RS/carrier/kernel/staging/metadata. Live MemoryMax/MemoryHigh=infinity;
no global process or multi-user memory bound/acceptance is claimed.

### Current artifacts and safe end state

- Owner remains beta95/A0; no APK created or installed in these final phases.
  Existing APK:`state-client-build/mux-profile-20261020/delivery/FamilyConnect-0.1.18-beta95-mux-profile.apk`.
  SHA256`e36a24601d459ea13553d9236486befe514dca496d8b2933290e6867d97c4159`;
  native`66a9d18d04ff71100df0144228db05decb970aea71b6d277ec321b1c6c240c63`.
- Exact compatible gateway remains
  `272bbc3fed90bbcf740a58f812e93511c976c114e2190f2c8711b55fa0dfb0c4`, bootstrap1011 kept.
  Current PID3937546/invocation`17ec5abfcbc84a9d913e844193e0d931`, unchanged during A3/B3.
  Current credential-profile`daf1f087d9041152b9c8e2208f7a5aee3457ce761a8160e69f8f48736a6657d4`,
  leaf expiry17:05:36UTC; never restore older credentials/floors/transition intents.
- Historical13:24:45.943723UTC counter read confirmed active owner B3 **CREDIT128/131072**,
  errors0. Existing operator preference is now **LEGACY64 for new sessions**;
  `policy-Final64prepared.json`. Current128 was not reinterpreted or forcibly closed.
  Return64 was prepared but not yet confirmed at that checkpoint. The subsequent
  owner manual reconnect and13:39:52UTC readback above confirm new LEGACY64/65536;
  **no more bulk** was run.
- Final13:24:49UTC receipt`policy-FinalProfileoff.json` confirms counters **OFF**.
  No background collector, manual-wait task or automatic next phase remains.
  This task made no identity, credentials, enrollment, authority/floors or admission
  change. Same signer/package/UID/settings; testers94 remain legacy, no95 rollout.
- All rejected transport/cleanup patches stay separate. Implementation source seals
  and unchanged test results are retained; no source/test rebuild was needed here.
  functional patch`tests/fixtures/mux_profile/complete-functional.patch` SHA256`fce936ae1d6db5007aa4b3634d77b5dca61b9ad00668f0fcf7ddf52d25f63d01`.
  gateway patch`tests/fixtures/mux_profile/complete-gateway.patch` SHA256`6f8695ffefc22372ccdba1ee050b13518339ff8de6c95f9c9de8f97b11a56dc3`.
  android patch`tests/fixtures/mux_profile/complete-android.patch` SHA256`ab8ff13d6c996002b913d157ad54e0158726e495e82e81bc0ad7dc0768721b55`.

Exact capsule sources:`carrier`, `gateway-source/carrier`, `android-source`;
Android source inventory`f31cf6267fdafa772ed3b5c6e08ee21f3e70b25c74fa9a8164a97d67194844fe`,
gateway manifest`324c6af155168099bd5a8183f4774e793d178350c7d85bcb7a5313ed036e308e`.
Unchanged meter/parser pins verified. The existing large six-phase evidence patch
hit OS argv-size limit; same generated patch passed via apply_patch stdin and saved
successfully. `final-analysis-repair.json` retains this offline failure/repair;
no instrumentation or physical traffic repeated.

Private capsule receipts:`manual-b3-result.json`, latest`manual-continuation-result.json`,
`final-three-pair-comparison.json`, `B3/analysis.json`, `B3/normalized.json`,
`b-three-profile-proof.json`, `b-three-final-readback.json`,
`final-active-session-readback.json`, `final-return64-preparation.json`.
Sanitized negotiated JSON, STATUS/PLAN, ADR and private beta guide updated.
**The comparison and subsequent manual return64/readback are complete.**

## Historical A3 physical checkpoint —20.10 13:12UTC (B3 pending then)

Only A3 measured; no previous phase repeated. Owner manual reconnect created VPN334
at13:03:57.855UTC, cellular327/tun1. Same95/A0 package/APK/native and compatible
gateway binary; no code/build/install/deployment or task-initiated restart.

### Pre-bulk interruption and actual profile

Initial13:04:30UTC readback still showed PID3878280/invocation`e4d547a4…`. During scope
preflight the process changed externally to **PID3937546**, invocation
`17ec5abfcbc84a9d913e844193e0d931`, start13:05:48UTC, NRestarts0. NRestarts0 does not
erase the observed invocation change. Exact binary stayed
`272bbc3fed90bbcf740a58f812e93511c976c114e2190f2c8711b55fa0dfb0c4` (1011 preserved).
Credential-profile SHA changed from`fdbcc561…` to
`daf1f087d9041152b9c8e2208f7a5aee3457ce761a8160e69f8f48736a6657d4`, leaf expiry now
17:05:36UTC. No credential update/restart was initiated by this task; initiator and
trigger were not audited. Do not restore the old credential snapshot to match A1/A2.

First post-manual owner media tag`c5899d6b…` established TLS13:04:19.953641UTC and
closed13:05:40.046466UTC; no load had started. Recovered owner tag
`5f0136db0c1a4af481c9517596e1822beebe284e319b50d27c768b3b1553b39a` established
authenticated Family TLS13:06:29.786453UTC. New invocation has one observed
established session, current Mux snapshots **LEGACY64/65536**. Meter gates the new
tag/PID/invocation/VPN334 and finds the actual measured Mux streams. Both endpoint
windows are65536 via shared authenticated ALPN and unchanged pinned native/server
mapping; not merely CONNECTED/operator preference and not an independent Android
live Mux counter export. Exact source/hash proof in`a-three-profile-proof.json`.

Preflight initially failed without HTTP traffic: process changed during the readback
and the ad-hoc startup projection initially looked for top-level stage rather than
`restricted_trace.trace`. Raw evidence was retained and parsed correctly. A full
all-fields journal read then exceeded25s; bounded remote projection succeeded.
Counters were turned OFF in each finally block. No meter/transport code changed.
Offline AST reuse also initially missed `import re`; corrected locally and analysis
rerun successfully, without rerunning traffic. These analysis/preflight failures are
not Mux protocol errors. `a-three-prebulk-events.json` retains the interruption and
unknown counter scope, rather than presenting a clean uninterrupted connection.

### A3 HTTP results (full bodies through Android TUN)

Unchanged pinned HTTP/1.1 endpoint and meter, same order/instrumentation as B2/A2;
150s/request, retry0. Actual Mux IDs corroborate MESH, no AWG/TCP fallback observed.
Full lengths and local body hashes verified; independent origin byte-exact is not
claimed. Each HTTP request reports one new TCP connection. All4/4 finish HTTP200.

| Request | Body bytes | HTTP full s | TTFB s | Body interval s | Phone BEGIN→END s | Goodput Mbit/s | Result |
|---|---:|---:|---:|---:|---:|---:|---|
| Control, Mux49 |65536|4.454774|3.474330|0.980444|4.490|0.116768|complete|
| Single, Mux51 |4194304|47.675350|2.762366|44.912984|47.700|0.703447|complete|
| Parallel flow0 |2097152|27.382714|0.897959|26.484755|27.410|0.612084|complete|
| Parallel flow1 |2097152|27.130556|0.753513|26.377043|27.150|0.617945|complete|

Parallel actual Mux set **{59,61}**; equal-sized bodies do not establish which HTTP
row corresponds to each ID. Aggregate is4194304bytes over common27.410s =
**1.224168Mbit/s**, not the sum of independently timed per-request speeds. Full,
TTFB and body intervals retained separately; control full time is not RTT.

### Counters and exact accumulation intervals

No counter resets. Exact-at-TLS-establishment value unavailable; label unknown, not
measured zero. First observed cumulative errors at13:09:16.943927UTC = **1**;
pre-control13:10:26.944031 = **1**; pre-bulk13:10:33.013785 = **1**;
post-load13:11:52.943869 = **1**. The one pre-load error is included. Counter of the
interrupted`c5899d6b…` session is unknown; do not subtract or merge counters across
epochs. No owner FAILED/CLOSED/reconnect during measurement capture; **one pre-bulk
process/media interruption is explicitly retained**. No continuous TUN-gap telemetry;
VPN334/underlay327 unchanged at checked boundaries, not proof of zero subsecond gaps.

All intervals below are server snapshots enclosing the relevant request, from exact
process-local `node_ns`; percentages use that same interval, not HTTP duration.
Journal/host clock alignment selected brackets; independent cross-clock offset is
not measured. Waits overlap, including across adjacent snapshot brackets; do not add
Mux and RS waits or sum bracket bytes as if they were disjoint request-local traffic.

| Cell | UTC snapshot start → end | Exact monotonic interval s | Mux ID: ready-zero-credit s (% interval) | Shared RS ready-full s (% interval) | Shared RS head-unconfirmed/later-SACKed s | RS new / retry bytes |
|---|---|---:|---|---|---:|---:|
| Control |13:10:26.944031 →13:10:34.943867|7.999826774|49:0.074033 (0.93%)|0.365562 (4.57%)|0|72279 /0|
| Single |13:10:33.013785 →13:11:22.943689|49.929902477|51:38.065180 (76.24%)|17.929618 (35.91%)|7.403870|4409263 /576762|
| Parallel |13:11:20.944025 →13:11:50.943922|29.999986263|59:15.697081 (52.32%);61:13.862905 (46.21%)|26.434783 (88.12%)|12.247308|4250456 /588273|

`A3/normalized.json` keeps before/after values, exact node_ns endpoints, both head
wait categories and window-only waits. No lifetime counter is compared directly to
a request-local counter. Whole capture has29 ready-zero samples,5 RS-free/idle and
24 RS-full,46 snapshots total: sampled joint state, not additive wait durations.

Background owner-Mux activity, excluding the measured ID set:
- Control9 streams,24 other handed DATA bytes in its bracket.
- Single8–10 streams,190987 other handed DATA bytes in its bracket.
- Parallel7–8 streams,15312 other handed DATA bytes in its bracket.

These are DATA handed into owner Mux/RS, not proof of the entire background load at
every layer. Counts alone are not load. Prior A2 single13–18/325249bytes versus B2
6–7/91745bytes remains a material comparability limitation. The quiet-phone instruction
was given; absence of all user/background activity is not independently established.

All measured streams49/51/59/61 close with zero queued/ready/receive-buffered/pending
credit. Owner Mux retained high-water737280B, start589824/end458752B, end7 background
streams/max11. Whole-gateway sampled RSS max45100KiB/CPU6.660% one core. A new gateway
process and other traffic mean these are not a window-only memory comparison with
A1/B1/B2/A2 or a whole-process resource bound. Capture end normal, cap_reached=false,
partial_bytes0, reconstruction errors0.

### Pair status and safe continuation

| Phase | Profile | Single Mbit/s | Aggregate Mbit/s | Control full s | Completed | Load errors before→after |
|---|---|---:|---:|---:|---|---|
| A1 |64|0.647020|1.195810|4.943254|4/4|1→1|
| B1 |128|0.808346|1.299552|6.625675|4/4|1→1|
| B2 |128|0.803507|1.211351|4.298021|4/4|0→0|
| A2 |64|0.424417|0.998644|5.042774|4/4|2→2|
| A3 |64|0.703447|1.224168|4.454774|4/4|1→1|
| B3 |128|not run|not run|not run|not run|unknown|

No final speed acceptance: B3 is still required. The full prior gain is not assigned
to window alone; sessions, background bytes, shared RS and now gateway process age
vary. Compatibility/local correctness result retained, no unchanged tests rerun.

After saving A3, existing operator preference switched to **CREDIT128 for new
sessions only**, counters OFF (`policy-B3prepared.json`). Last active owner session
remains the immutable64 contract; no128 success inferred from preparation. Final
13:12:45UTC readback: same95/A0, exact gateway binary/PID3937546/invocation and renewed
credential-profile hash, VPN334. No new APK, tester rollout, identity/floors/admission
mutation or push. Existing collectors ended; no background/manual-wait task remains.
Budget **40.5/64MiB**,23.5MiB remaining; B3/control8.0625MiB would reach48.5625MiB.
Receipts: `manual-a3-result.json`, latest`manual-continuation-result.json`,
`A3/analysis.json`, `A3/normalized.json`, `b-three-preparation.json`,
`a-three-post-readback.json`; sanitized negotiated evidence updated. Owner preserves
quiet conditions, manually Disconnect→Connect and replies connected. Only then
verify fresh131072 on both sides and run **B3 only**, no fourth pair or tuning branch.

## Historical A3 preparation checkpoint —20.10 12:57UTC (no load then)

User authorized remaining A3/B3 in separate manual steps. This turn only prepares
A3; no previous phase repeated, no HTTP/control/bulk request, no new implementation,
APK, build, deployment or gateway restart. Same95/A0 and compatible gateway with1011.
Fresh readback12:57:42UTC verifies exact APK/native/gateway hashes listed below and
same gateway PID3878280/invocation`e4d547a4c0fb41c3adae78c341329331`/NRestarts0.
Credential-profile hash unchanged; current leaf expiry14:35:11UTC (recheck when
continuing, never restore expired snapshots or old transition intents).

Active owner remains A2 VPN333/created12:34:54.829UTC, cellular327/tun1, same tag
`adb95897842128552c7ef30d97d6c2cd59e9a838dd8bb6c4ddc3917667b9cc95`.
Two fresh Mux snapshots report **LEGACY64/65536, protocol_errors2→2**; final snapshot
epoch1792501060.767269/node_ns4831626894267. Shared authenticated ALPN plus unchanged
exact native/server mapping retains65536 on both endpoints; no independent Android
live counter export claimed. These are current **A2** counters, not A3 establishment.

The existing protected operator setting is already **LEGACY64 for next sessions**;
no profile-file write was needed (inode273094/mtime_ns1792499330554152576 unchanged).
Only existing bounded counter export briefly ON for readback, then **OFF** in finally;
final readback confirms OFF. No collector/manual-wait task remains. A3 is not created
or negotiated yet. Existing meter/parser hashes match pinned B2/A2 tools; unused A3
output/reservation and continuation inputs checked. No instrument/code changes.

Owner leaves phone without explicitly running video/browser downloads or other
manual transfers, then presses Disconnect→Connect and replies connected. Keep the
same conditions for B3. Do not force-stop apps/services or change network/DNS/routes.
After that reply verify a **new owner session** and actual65536 contract, then only
A3: control64KiB →single4MiB →parallel2×2MiB, same endpoint/meter150s/retry0. Preserve
background byte activity over matched intervals; open-stream count is not load.
After A3 save results, turn counters/collectors OFF, prepare128 only for a separately
requested manual B3 reconnect. No fourth pair or automatic background continuation.

**Protocol-error sampling contract:** retain establishment snapshot if existing logs
provide one, first observed cumulative counter, immediate pre-load and post-load
values separately. Include errors between connect and bulk; never reset. Counters
accumulate even when export is OFF. Because no sampler is left running while waiting
for the owner, an exact establishment snapshot may be unavailable: label
`UNKNOWN_NOT_SAMPLED_AT_ESTABLISHMENT`, not a measured zero. First observed cumulative
counter still includes earlier errors from that session. Source-defined initialization
at zero is not substituted for a physical snapshot.

### Existing-pair wait normalization (offline, no new traffic)

`prior-pairs-normalized.json` retains original HTTP timestamps/full/TTFB/body bytes
and each server bracket's exact process-local monotonic endpoints, counter before/
after/delta and matching denominator for all12 cells. No duration is reconstructed
from rounded goodput. Single-request brackets summarized here (rounded display only):

| Phase | Snapshot interval s | Single ready-zero-credit / interval | Shared RS ready-full / interval |
|---|---:|---:|---:|
| A1 |54.000027490|84.36%|30.07%|
| B1 |43.988332864|0.13%|87.63%|
| B2 |44.000208974|1.11%|89.76%|
| A2 |81.999818083|86.25%|48.39%|

Fractions describe **their server snapshot brackets**, not exact HTTP-local shares.
Existing journal/host wall-clock alignment selects brackets; independent cross-clock
offset is not measured. Shared RS includes other traffic; overlapping waits are not
added. Parallel HTTP request rows and actual Mux-ID sets are preserved, but equal
response sizes do not prove one-to-one request↔Mux-ID assignment. A2 single background
13–18 streams/325249 handed DATA bytes versus B2 6–7/91745 within their respective
brackets, plus different retries/conditions, prevent attributing the full gain to128.

Private checkpoint `state-client-build/mux-profile-20261020/a-three-preparation.json`;
readbacks `a-three-prep-readback.json`, `a-three-prepared-readback.json`, snapshots
`a-three-prep-sessions.json`, counter receipts `policy-A3prepRead.json` and
`policy-A3prepared.json`. Prior phase receipts unchanged; `manual-continuation-result.json`
and negotiated measurement summary still describe completed A2, not a new measured phase.
Budget remains **32.4375/64MiB**, no extra measurement bytes this turn. A3+B3 each
8.0625MiB including control would reach48.5625MiB. **Stop for manual reconnect now.**

## Historical A2 physical checkpoint —20.10 12:44UTC (stop after A2)

User authorized **A2 only**, explicitly no code/APK/gateway/transport-setting change
or next-profile transition. Those limits were preserved. Owner manually created
VPN333 at12:34:54.829UTC; cellular327/tun1, UID10283/PID9374 unchanged. Old B2 session
closed during that manual transition, not during A2 measurement. Among two active64
peers, recorded AUTHORIZED→FAMILY_TLS ESTABLISHED12:35:16.039UTC identifies new owner
tag `adb95897842128552c7ef30d97d6c2cd59e9a838dd8bb6c4ddc3917667b9cc95`.
Other tag `0f6b0ccd…` excluded from owner counters. Startup attribution was read from
existing logs, not a new trace/profiler or a manual wait.

### Actual profile / unchanged pair

Before bulk, actual owner Mux reports **LEGACY64/65536**, not merely configured
preference or Android CONNECTED. Established authenticated Family TLS uses the
common legacy ALPN `family-connect-5n3-test-v1`. Exact installed95 native and gateway
source pins show both endpoints derive65536 from that shared negotiated protocol;
`NewMux`/stream creation use it for receive-ring capacity and both initial credits.
Therefore Android/NL contracts are **65536/65536 per stream in each direction**.
This is a TLS/common-contract proof plus live server counter, **not an independent
Android live Mux counter export**. `a-two-profile-proof.json` records this distinction
and the exact manifest/file hashes. A wrong observed profile would stop before bulk.

Unchanged APK `e36a24601d459ea13553d9236486befe514dca496d8b2933290e6867d97c4159`,
native `66a9d18d04ff71100df0144228db05decb970aea71b6d277ec321b1c6c240c63`, gateway
`272bbc3fed90bbcf740a58f812e93511c976c114e2190f2c8711b55fa0dfb0c4`, PID3878280,
invocation `e4d547a4c0fb41c3adae78c341329331`, NRestarts0. Credential profile SHA
`fdbcc561f6f08757a1253a6e430d5b5709ecdcffba3c6b9d0cfca01ad916586c` unchanged;
A0, bootstrap1011, identities, floors, registration and tester94 preserved.

### Requested pair comparison (full wall interval goodput)

| Pair/order | LEGACY64 single / aggregate Mbit/s | CREDIT128 single / aggregate Mbit/s | Observed B over A | Completion |
|---|---|---|---|---|
|A1/B1|0.647 /1.196|0.808 /1.300|+24.9% /+8.7%|both4/4, no HTTP failures|
|B2/A2|0.424 /0.999|0.804 /1.211|+89.3% /+21.3%|both4/4, no HTTP failures|
|A3/B3|not run|not run|not evaluated|no next phase started|

Percentages describe these observations, **not a profile-only causal speedup**.
Second pair ran in reverse order B2→A2; neither A2's slower result nor background
variation is excluded. Only two of three planned pairs exist; no final acceptance.

| Metric | A1 | B1 | B2 | A2 |
|---|---:|---:|---:|---:|
|Single full / body seconds|51.842 /49.193|41.479 /39.884|41.740 /39.534|79.042 /76.007|
|Single TTFB seconds|2.649|1.595|2.206|3.034|
|Parallel common wall seconds|28.060|25.820|27.700|33.600|
|Control64KiB full seconds|4.943|6.626|4.298|5.043|
|ProtocolErrors during phase|1→1|1→1|0→0|2→2|
|Single ready-zero-credit seconds|45.552|0.055|0.487|70.728|
|Single sharedRS ready-full seconds|16.238|38.547|39.494|39.682|
|Single sharedRS head-unconfirmed/later-SACKed seconds|7.480|17.936|17.434|20.713|

A2 control stream109: full5.042774s, TTFB3.881590s, body1.161184s. Single stream111:
full79.041733s/wall79.060s, TTFB3.034492s/body76.007241s; one endpoint socket.
Parallel streams145/147: full31.987272/33.563924s, TTFB1.727158/3.437013s,
body30.260114/30.126911s, common wall33.600s, two simultaneous endpoint sockets.
Same HTTP/1.1 endpoint and phone continuous body reader as B2, MESH/tun1, no observed
AWG/TCP fallback. All bodies complete with recorded lengths/hashes; not independent
origin-byte-exact proof. Control/setup/full times are application timings, not RTT.

### Errors / stalls / background / memory

- A2 ProtocolErrors **2 before/2 after**; these two pre-load errors remain of unknown
  branch/time/impact and are not assigned to CREDIT128. Other64 peer0→0. No failed
  HTTP request, retry of a request, observed owner reconnect, lifecycle failure/close
  or recovery event during the bounded capture. VPN333/PID/invocation remain fixed
  at checks. This does not prove absence of sub-sampling TUN gaps.
- A2 single ready-zero-credit70.728292s; parallel20.307436/17.880387s.47/65 snapshots
  have ready-zero,11 with free/idle RS and36 overlapping full RS. B2 corresponding
  short single stall0.486611s and parallel0/0s. Do not sum overlapping Mux/RS waits.
- A2 shared RS single ready-full39.682467s/head-unconfirmed-later-SACKed20.713202s;
  parallel27.941977/10.121337s. RS new/retry bytes single4567746/1045442,
  parallel4246781/543037; B2 single4307268/662246, parallel4335911/669383.
  These are session brackets including background/edges, not isolated request bytes.
- A2 single has13–18 non-measurement active streams vs B2 6–7. Other handed Mux DATA
  in the single brackets325249 vs91745bytes; parallel15 vs6 background streams but
  other handed DATA11468 vs101270bytes. Stream count alone is **not** background
  throughput or proof of the slowdown's cause. Sessions/radio/ACK/retries also differ.
- A2 session max active19, retained high-water1376300bytes; end15 background streams
  retain983040bytes, versus12/786432 at start. All four measurement streams close
  with zero queued/ready/receive-buffered/pending-credit bytes. Retained background
  streams are not unconsumed benchmark bodies. B2 ends6/786432bytes, max active8.
- A2 whole-gateway RSS max67936KiB/CPU8.570% one core; B2 63636KiB/8.410%. Other
  peers/background coexist: not a window-only cost or a global resource bound.
  Capture ended normally, cap_reached=false, partial_bytes0, reconstruction errors0.

### Completion / state preserved

Temporary counters are **OFF**, collector ended, no background/manual waiting.
Only the existing `mux-counters` file was toggled; `mux-profile` was not rewritten:
inode273094/mtime_ns1792499330554152576 identical before and after. Saved receipts
`policy-A2counterson.json`/`policy-A2countersoff.json` confirm that. No source code,
APK, gateway binary, transport policy or security setting changed; no next profile
was prepared. Exact meter/parser pins match B2; existing tests reused unchanged.

Final12:44:14UTC readback confirms active owner and next-session **LEGACY64**, same
95/A0 and compatible gateway/1011, no gateway restart or credential-profile change.
This phase8.0625MiB, experiment **32.4375MiB/64MiB**,31.5625MiB remaining;
150s/request, no HTTP retries. Artifacts in `state-client-build/mux-profile-20261020`:
`session-scope-A2.json`, `a-two-profile-proof.json`, `A2/analysis.json`,
`manual-a2-result.json`, `a-two-post-readback.json`; latest pointer data in
`manual-continuation-result.json`, prior B1/B2 receipts preserved. Sanitized negotiated
evidence, STATUS and PLAN updated. **Stop here.** A3/B3 require a separately agreed
manual step; no automatic profile change, reconnect or continuation.

## Historical B2 physical checkpoint —20.10 12:28UTC

Second manual owner reconnect confirmed: VPN332 created12:24:49.757UTC, cellular327,
tun1, same UID10283/PID9374. Independent owner media tag
`bd2fcaffb74066bf6b8dfde06d8f5de451a4050b88c4ff6a5db19140cd630e1c`
selects **CREDIT128/131072**, protocol_errors0 before load. Old B1 tag absent; other
active LEGACY64 peer kept separately in raw capture and excluded from owner analysis.
Actual measured stream IDs support attribution. Meter/parser hashes match the B1
pins; no implementation, observation level, build, install or test-matrix change.

Exact95/A0 APK `e36a24601d459ea13553d9236486befe514dca496d8b2933290e6867d97c4159`,
native `66a9d18d04ff71100df0144228db05decb970aea71b6d277ec321b1c6c240c63`, gateway
`272bbc3fed90bbcf740a58f812e93511c976c114e2190f2c8711b55fa0dfb0c4` unchanged.
NL PID3878280/invocation `e4d547a4c0fb41c3adae78c341329331`, NRestarts0; retained
b9/1011 and credential profile SHA
`fdbcc561f6f08757a1253a6e430d5b5709ecdcffba3c6b9d0cfca01ad916586c` unchanged.

### Current three-pair table (full wall interval goodput)

| Pair/order | A LEGACY64 single / aggregate Mbit/s | B CREDIT128 single / aggregate Mbit/s | Completion |
|---|---|---|---|
|1 A1/B1|0.647 /1.196|0.808 /1.300|both3/3 bulk +1/1 control;0 HTTP failures|
|2 B2/A2|not run; next manual step|0.804 /1.211|B2 3/3 bulk +1/1 control;0 HTTP failures|
|3 A3/B3|not run|not run|pending manual steps|

Only **B2** ran this turn. Single4MiB full41.739897s, wall41.760s, TTFB2.205978s,
body39.533919s; Mux stream27/one endpoint socket. Parallel2×2MiB wall27.700s,
full27.407213/27.672009s, TTFB0.739781/1.086397s, body26.667432/26.585612s;
Mux37/39 and two simultaneous endpoint sockets. HTTP/1.1 full bodies read continuously
through Android MESH TUN; no AWG/TCP fallback observed. Length/hash recorded, not
independent origin-byte-exact proof. No retries or excluded failed requests.

Control64KiB stream25 full4.298021s, TTFB2.387177s (B1 full6.625675s; A1 4.943254s).
Full request latency is not RTT. B2 single is close to B1, but aggregate is lower;
the A2 half of this pair has **not** run. Same underlying network ID is not proof
of identical radio, media or reverse-ACK conditions. **Speed not accepted yet.**

- Owner ProtocolErrors **0→0** throughout B2. Other observed peer also0→0. B1 initial1
  and the old LEGACY64 session's5 remain separate historical unresolved observations.
- Single zero-credit-ready0.486611s, parallel0/0s. Coarse snapshots0/43 ready-zero
  do not erase the short accumulated single stall. Shared RS single ready-full
  39.494137s, head-unconfirmed/later-SACKed17.434159s; parallel27.238742/12.499994s.
  Overlapping waits are not additive. Shared RS remains a concrete limiter.
- RS new/retry bytes single4307268/662246, parallel4335911/669383, whole-owner-session
  brackets including background/edges. These are not isolated per-request counters.
- End: all four measured streams closed with queued/ready/receive-buffered/pending
  credit0. Six background streams retain786432bytes, same as start. Session retained
  high-water1179736bytes/max active8. No accumulation of the completed bulk bodies.
- Whole-gateway RSS max63636KiB, CPU8.410% of one core (B1 59484KiB/6.608%); another
  peer is present, so these are not owner-only/window-only costs. No global memory
  cap claim; MemoryMax/High remain unlimited. Capture ended normally, cap_reached=false,
  partial_bytes0, journal parser errors0. VPN332 and gateway incarnation stayed fixed
  at checked boundaries; no continuous TUN-gap instrumentation claim.

After B2, counters disabled. At12:28:50UTC existing protected operator setting
prepares **LEGACY64 only for NEW sessions**, for A2 on the same95/compatible-gateway
pair. Active B2 remains128; it is not reinterpreted and was not disconnected.
Readback12:28:51UTC confirms policy64/countersOFF, unchanged binaries/PID/invocation,
credential profile, phone and VPN332. No security/identity/floors/registration write,
new API/APK, input injection or automatic reconnect. Tester94 remains unchanged.

Phase8.0625MiB; experiment total **24.375MiB/64MiB**,39.625MiB remaining,
150s/request. No background collector or manual wait. Latest state:
`state-client-build/mux-profile-20261020/manual-continuation-result.json`;
immutable phase receipts `manual-b1-result.json`/`manual-b2-result.json`,
`B2/analysis.json`, `session-scope-B2.json`, `policy-A2prepared.json` and
`a-two-prepared-readback.json`. Public sanitized evidence JSON updated. Existing
scope tests reused with exact pins; no functional code delta requiring a new race run.

Next manual action: Family Connect **Disconnect→Connect**, reply “подключил”.
Verify a fresh owner LEGACY64/65536 session before **A2 only**. A2 load has not run;
preparing64 is not evidence of successful64 negotiation. Then A3/B3 remain.

## Historical B1 physical checkpoint —20.10 12:20UTC

User reported manual reconnect. Fresh readback12:16:39UTC confirms the exact
installed95/A0 APK `e36a24601d459ea13553d9236486befe514dca496d8b2933290e6867d97c4159`,
native `66a9d18d04ff71100df0144228db05decb970aea71b6d277ec321b1c6c240c63`, and gateway
`272bbc3fed90bbcf740a58f812e93511c976c114e2190f2c8711b55fa0dfb0c4`. No rebuild,
install, gateway restart or compatibility rerun. Same PID3878280/invocation
`e4d547a4c0fb41c3adae78c341329331`; b9/bootstrap1011 preserved. Credentials profile
hash remains `fdbcc561f6f08757a1253a6e430d5b5709ecdcffba3c6b9d0cfca01ad916586c`.

Owner VPN330 replaced by331, created12:13:30.642UTC, cellular underlying network327,
tun1, UID10283/PID9374 unchanged. New owner session
`071df71c98ae270148b014fd5e4e534ddc23a1c26fb1308a1874e8018919b1e8` reports
**CREDIT128/131072**, confirmed by fresh bounded snapshots and later measured Mux
streams. Old owner tag is absent; known other peer remains LEGACY64 in preflight.
The new128 session already has **protocol_errors1 before measurement**; its branch,
time and impact are not established. This is distinct from the old64 session's5.
During B1 load errors remain **1→1**; neither error is hidden or labeled credit overflow.

Only B1 ran, output `state-client-build/mux-profile-20261020/B1m`. Existing HTTP/1.1
phone TUN meter and bounded counters reused. Local analysis now pins the validated
owner tag via `session-scope-B1m.json`, retains raw other-peer records and fails on
missing/stale target, profile/window mismatch, gateway invocation or owner VPN change.
No transport/HTTP payload/observation level change. Five local attribution tests
PASS; historical A1 reparse preserves its measurements. These local analysis changes
supersede only the old collector-wrapper hash in the preparation receipt, not binaries.
Pins: `manual-b1-analysis-tools.json`; tests: `manual-b1-scope-tests.log`.

### Current paired physical results (full wall interval goodput)

| Pair/order | A LEGACY64 single / aggregate Mbit/s | B CREDIT128 single / aggregate Mbit/s | Complete / failed |
|---|---|---|---|
|1 A1/B1|0.647 /1.196|0.808 /1.300|both3/3 bulk +1/1 control;0 HTTP failures|
|2 B2/A2|not run|not run|pending manual independent sessions|
|3 A3/B3|not run|not run|pending manual sessions|

B1 single4MiB: full41.478868s, wall41.510s, TTFB1.594841s, body39.884027s;
actual Mux stream73 and one endpoint TCP socket. A1 full51.841938s/wall51.860s,
TTFB2.649338s/body49.192600s. Full-wall gain **+24.93%** in this pair only.
B1 parallel2×2MiB: wall25.820s, individual full25.377780/25.793190s,
TTFB0.681424/1.144128s, body24.696356/24.649062s; actual Mux streams81/83,
two simultaneous endpoint sockets. A1 wall28.060s; aggregate gain **+8.68%**.
All4 request bodies continuously read on phone, length/hash recorded; not independent
origin-byte-exact proof. IPv4 HTTP/1.1 through MESH/tun1, no AWG/TCP fallback observed.

Control64KiB stream71 full latency **6.625675s versus A1 4.943254s** (worse),
TTFB4.661478s versus2.775929s. This is application request time, not RTT. No request
retried or excluded. Same physical pair/underlay ID does not imply identical radio,
media or reverse-ACK conditions: A1/B1 use different sessions separated in time.

### Credit / RS / resources / failures

- Single ready-but-zero-credit: A1 **45.551868s**, B1 **0.055200s**. Parallel per-stream:
  A1 17.423608/17.974398s, B1 0/0.044034s. Coarse snapshots see0/44 ready-zero in B1
  versus37/49 in A1; cumulative counters still retain the short B1 stalls.
- Single shared-RS ready-full:16.238→38.547s; head-unconfirmed/later-SACKed:
  7.480→17.936s. Single RS new/retry bytes4446848/677106→4248437/730502;
  parallel4260413/405438→4299841/493456. Brackets include session background and
  edges. These overlapping waits must not be added; RS is still a material limiter.
- B1 end: all four measured streams closed, queued/ready/receive-buffered/pending
  credit0. Six background streams remain, Mux retained786432bytes (A1 six:393216).
  Session retained high-water1081434 versus658198bytes; max active streams8 versus9.
  This is increased per-stream reservation, not an indefinitely growing bulk queue.
- Gateway whole-process RSS max59484 versus44028KiB, CPU6.608% versus6.554% of one
  core; not attributable solely to window size or owner session. Whole-process
  MemoryMax/High remain unlimited; no claim of a global memory cap.
- ProtocolErrors1→1, no failed HTTP or observed gateway/owner VPN replacement during
  the phase. Final VPN331 stable at measurement boundaries; no continuous TUN-gap
  instrumentation, so sub-sampling gaps are not ruled out. Journald reconstruction
  clean, bounded capture ended normally (`cap_reached=false`, partial_bytes0).

**Decision:** negotiation confirmed physically; local correctness remains PASS and
B1 completed without an error increment. **Speed acceptance NOT YET GRANTED**:
only one pair, increased control latency/memory, unresolved pre-load protocol error.
The reduction in zero-credit wait supports this mechanism, not a proven speedup
across independent sessions or a precise external-network diagnosis.

Final12:20:47UTC readback:95/A0, active owner CREDIT128, next-session preference128,
**counters OFF**, same gateway PID/invocation/NRestarts0 and credential hash. No
identity/credentials/floors/registration mutations, no APK/install, no background
collector/manual wait, no ADB input. Tester94 and public/invitation versions unchanged.
Safe eventual return: set existing operator profile LEGACY64 for new sessions,
ordinary owner Disconnect→Connect; do not reinterpret active128 or downgrade.

This phase8.0625MiB; experiment total **16.3125MiB** of64MiB (47.6875MiB remaining),
150s/request. Private latest state `manual-continuation-result.json`, detailed
`B1m/analysis.json`, fresh `b-one-post-readback.json`; public sanitized summary
`2026-10-20-mesh-mux-credit.negotiated.json`. Next step: manual owner reconnect for
independent **B2**, same prepared128; no B2 traffic or wait started this turn.

## Historical B1 preparation checkpoint —20.10 12:10UTC

User explicitly requested **preparation only**, followed by a separate manual step.
Readback12:08:29UTC confirms installed95/A0 APK/native and compatible gateway hashes
below, same NL PID3878280/invocation, owner PID9374/UID10283/VPN330/underlay327.
Credential profile hash unchanged; no security/floors/registration write.
Fresh bounded snapshot12:10:22UTC: active owner A1 session
`d0a19cfb7d0ffb14f2117cb1dfe232604d91c6170de51cd41b61000205f6c4f0`,
**LEGACY64,65536,protocol_errors5**. Attribution uses the previously isolated A1
tag still active and stable owner/gateway runtime identifiers, not the presence
of only one server session. Two other current tags are preserved separately.
These errors occurred on LEGACY64; CREDIT128 has not been physically measured.

12:10:23UTC: existing protected operator control sets **CREDIT128 for the next
session only**, counters **OFF** after the readback. Active64 session is unchanged.
No oldb9 rollback: A and B both use95 and compatible `272bbc3f…` gateway/1011.
No new APK/API/canary/switching mechanism, no ADB input or MIUI bypass.

Prepared continuation receipt:
`state-client-build/mux-profile-20261020/b-one-preparation.json`.
It pins the existing collector/meter/parser inputs, unused B1m output destination,
old owner/other peer tags, expected128 contract and mandatory post-reconnect
readback gate. `b-one-prep-session-readback.json` and `policy-B1prepared.json` retain
exact observations. Collector is **not started**; no background process or120s
manual wait remains.0 HTTP requests/measurement bytes this turn; cumulative8.25MiB.
Initial equality of full VPN text rejected volatile fields; stable network ID,
creation timestamp/interface/underlay independently matched. No runtime change
was performed by that readback guard.

Required action at that checkpoint: normal Family Connect **Disconnect→Connect**, then reply
“подключил”. That next message resumes readback of the new negotiated profile and
owner scope before any B1 load. Preparation alone is not agreement on128 and not
acceptance. Earlier “128 OFF” below describes the completed previous checkpoint;
the latest new-session policy is now CREDIT128, while active owner remains64.

## Historical implementation/first-A1 checkpoint — owner-only,20 October2026

Compatibility implementation and local checks complete; physical paired acceptance
**incomplete because MIUI denies input injection and the required manual restart
was not observed**. Dedicated ALPN separates Mux resource profile from the unchanged
certificate authorization contract. See [ADR/contract](../adr/2026-10-20-negotiated-mux-credit.md).

Server-first rollout11:37:09UTC: compatible gateway
`272bbc3fed90bbcf740a58f812e93511c976c114e2190f2c8711b55fa0dfb0c4`,
PID3878280, invocation `e4d547a4c0fb41c3adae78c341329331`, LEGACY64.
Fresh guards preserved credentials; initial publication propagation check failed,
then fresh readiness passed without repeating deploy or restoring security state.
Actual old94/new-server64KiB phone smoke PASS5.877s. Bootstrap1011 files unchanged.

Owner95 installed11:40:25UTC, same package/signer/UID10283; fresh READY and hashed
identity/Support ID bindings verified. APK:
`state-client-build/mux-profile-20261020/delivery/FamilyConnect-0.1.18-beta95-mux-profile.apk`,
SHA256 `e36a24601d459ea13553d9236486befe514dca496d8b2933290e6867d97c4159`;
native `66a9d18d04ff71100df0144228db05decb970aea71b6d277ec321b1c6c240c63`.
No uninstall, downgrade, clear data, enrollment, FIELD grant or all_activated change.
New pair LEGACY64 phone smoke PASS4.305s (full request time; not RTT).
**Tester/public/invitation versions are not updated: tester remains94.**

Capsule `state-client-build/mux-profile-20261020`, fixture `tests/fixtures/mux_profile`.
Actual old/new matrix5/5 PASS;471 affected race PASS/16 opt-in skips,483 observed
integration PASS/17 skips,169 Android JVM PASS. Extra128 loss/slow/overflow/streams
and actual lease renewal/fresh-floor rejection tests retained. First signing
attempt stopped without secret output; retry using the existing protected vault
workflow succeeded. No secret material is included in patches or receipts.

### NEGOTIATION_AND_LEGACY_COMPATIBILITY — PASS

Actual94/b9/new cross-process matrix: old/old64, old/new64, new/old64,
new/new128, forced-legacy new/new64: **5/5 PASS**, four concurrent384KiB
synthetic echo streams per case. ALPN no-common/unknown/empty and family/expiry/CRL
fail closed. Generic/bootstrap ALPN stays old; certificate claim Protocol stays old.
The deployed new gateway served actual94 LEGACY64 before owner update; the new
pair's64 profile is confirmed by bounded counters and successful authenticated
traffic. CREDIT128 was **not selected on the owner** in this task.

### CREDIT128_CORRECTNESS — local PASS; production128 not tested

28 delta race PASS include128 ring fill/wrap, overflow/invalid update, slow
consumer, cancellation, loss/duplicate/reorder, multiple streams through32 and
revoked certificate denial. Additional disposable ProductStore lease suite:
**34 PASS**, including actual128 persistent TCP through renewal and rejection after
fresh floor invalidation; no switch to legacy on authorization error. The earlier
two lease opt-in skips are not counted as passes. Complete patches apply cleanly
to exact accepted bases. Existing recovery/1011 checks reused/affected integration
rerun; no claim of new overnight or real whitelist acceptance.

Retained repaired failures: sandbox socket/Gradle restrictions, missing test-only
atomic import, disposable-fixture missing dependency, null empty-Streams parser.
All relevant reruns passed. UI read-only automation works; UIAutomator click failed
and ordinary `adb shell input tap` then explicitly returned
`SecurityException: Injecting to another application requires INJECT_EVENTS permission`.
No subsequent alternate injection, root, security-settings change, lockscreen bypass
or hidden transport API was attempted. No transport UI APK was installed.

### PHYSICAL_SINGLE_FLOW_GAIN — NOT EVALUATED (external blocker)

| Pair/order | A: LEGACY64 single / aggregate Mbit/s | B: CREDIT128 single / aggregate | Completion |
|---|---|---|---|
|1 A/B|0.647 /1.196|not run|A bulk3/3; B stopped before requests|
|2 B/A|not run|not run|not started|
|3 A/B|not run|not run|not started|

A1: single4MiB51.842s, TTFB2.649s, body interval49.193s; actual Mux stream27,
one external TCP socket. Parallel2×2MiB wall28.060s, individual full times
27.821/28.031s, TTFB0.690/1.086s, body intervals27.131/26.944s; actual streams39/41,
two concurrent sockets. Each request created one HTTP/1.1 connection; full phone
body reads verified length and recorded hash, not independent origin-byte-exact.
A1 control64KiB full4.943s is application latency, not RTT. Same owner cellular
underlay327/tun1; gateway PID3878280, media tag
`d0a19cfb7d0ffb14f2117cb1dfe232604d91c6170de51cd41b61000205f6c4f0`.
MESH/TUN and current gateway sockets verified, no fallback observed at checks;
there is no continuous Android TUN-gap recorder in this comparison.

The B1 profile preflight correctly rejected an unchanged64 session; **zero B
application bytes**. A passive120s wait saw no owner VPN-network restart. It is
not a timeout-based downgrade or a physical failure of128. Before stopping, set
new-session profile back to LEGACY64. A counter-attributed return preflight saw
two media tags and stopped **before** any request rather than attribute another
session to owner. Both tags reported64; the second peer is not identified here.
No extra investigation matrix, direct-NL run or repeated bulk was used.

### AGGREGATE_LATENCY_MEMORY_AND_FAILURES

A1 single ready-zero-credit45.552s; parallel streams17.424/17.974s each. These overlap
shared RS waits; **do not sum them into end-to-end latency**.49 bounded snapshots:
37 ready-zero,8 senderRS-free/idle,29 sharedRS-full. Single RS new/retry bytes
4,446,848/677,106; parallel4,260,413/405,438. Whole-session brackets include
background/edges; they are not exact per-stream retransmission attribution.
Single ready-full RS16.238s/head-unconfirmed-later-SACKed7.480s; parallel25.347/10.186s.
Raw increments/return-delay histograms and complete stream receipts are in
[negotiated evidence](2026-10-20-mesh-mux-credit.negotiated.json).

A1 maximum observed gateway RSS44,028KiB, Mux retained high-water658,198 bytes;
CPU6.55% of one core. This is64 only, not a measured128 memory comparison. Ring
accounting and32-session component sums are in the ADR; unit MemoryMax is infinity,
so neither per-stream bounds nor this owner run proves global fleet capacity.

**New95 LEGACY64 protocol error count**:0→1 during smoke; A1 stays1→1; later
background-session readback is3. This is not the old beta90 incident or inherited
beta94 cumulative error. The bounded counter does not identify offending frame/
stream/branch; no measured request failed, but causation and application impact
outside measured requests remain unknown. It is not labeled a credit overflow or
hidden as zero. No observed gateway restart: same PID/invocation/NRestarts0.

Final counters-off phone64KiB control PASS3.522s, same cellular327/tun1; no claim
of server-media attribution for that last control. Total **8.25MiB** application
traffic (3/3 bulk +4/4 controls), no failed HTTP requests excluded. B/return
preflight failures are explicitly retained. Per-request limit150s, task cap64MiB.

### Decision, current pair and remaining action

Keep negotiated implementation, **CREDIT128 OFF; speed acceptance not evaluated**.
Do not infer physical rejection from this incomplete comparison. Owner stays95/A0
and LEGACY64 without downgrade; bounded counters OFF at11:57:02UTC. Fresh11:57:56
readback: same compatible gateway/PID,95 APK/native, UID10283, one VPN; fresh95 READY
and same identity/key/Support-ID bindings already verified. Current credential
profile hash equals entry `fdbcc561f6f08757a1253a6e430d5b5709ecdcffba3c6b9d0cfca01ad916586c`,
leaf expiry14:35:11UTC. No authority/floors/security-state restore. Gateway retains
b9/1011 source fixes but its executable is the new hash above, **not exactb9**.

Required external action: owner performs ordinary **Disconnect→Connect at each
profile boundary** when the operator has selected that phase. Shell touch is
currently denied; no remote tester or hosting change is needed. Do not enable128
blindly after this task: reread current materials/session and retain the unused
budget/preceding evidence. The second media tag also requires unambiguous owner
session attribution before any resumed bulk; do not treat all gateway tags as owner.

Exact reusable patches:
- `tests/fixtures/mux_profile/complete-functional.patch` SHA256
  `fce936ae1d6db5007aa4b3634d77b5dca61b9ad00668f0fcf7ddf52d25f63d01`.
- `tests/fixtures/mux_profile/complete-gateway.patch` SHA256
  `6f8695ffefc22372ccdba1ee050b13518339ff8de6c95f9c9de8f97b11a56dc3`.
- `tests/fixtures/mux_profile/complete-android.patch` SHA256
  `ab8ff13d6c996002b913d157ad54e0158726e495e82e81bc0ad7dc0768721b55`.
- Private `final-source-seals.json` SHA256
  `25bf7bc4570f26046e11c4b0ea967e90d9f2cf06e966d9d2b47516f793d43137`;
  gateway build/source manifest `324c6af155168099bd5a8183f4774e793d178350c7d85bcb7a5313ed036e308e`;
  Android source-inventory file `f31cf6267fdafa772ed3b5c6e08ee21f3e70b25c74fa9a8164a97d67194844fe`.

Source directories are capsule `carrier`, `gateway-source/carrier`, `android-source`;
patches preserve accepted ancestry. All rejected RTP/read-alignment/SACK/queue/
cleanup patches remain separate. Tester remains94; no95 distribution, public
catalog/invitation update, push, purchase, IPv6 or hosting change.

## Historical completed investigation (before negotiation implementation)

**Completed measurement and matched laboratory comparison. No functional speed
patch deployed or accepted. Current pair: beta94/A0 + exact b9/1011.** The task's
compatibility exception applies:128KiB helps the model, but current protocol has
no safe window negotiation. No unilateral increase or hidden new wire contract.

[Machine-readable evidence](2026-10-20-mesh-mux-credit.evidence.json).
Reproducer: `tests/fixtures/mux_credit/`. Private manifests, raw logs and receipts:
`state-client-build/mux-credit-20261020/` (not for Git/distribution).

## CURRENT_APK_AND_GATEWAY

- Android code94, A0 original arrival-driven100ms, `com.familyconnect.app.friends`,
  UID10283. No Android build/install in this task.
- APK SHA256 `fe32f36d0705d83705e549f598512305d63fd942a415f71afaebfd91534f8e13`.
  File: `state-client-build/rtp-deadline-20261020/normal94/delivery/FamilyConnect-0.1.18-beta94-stability.apk`.
  Identical private copy: `/home/joker/Downloads/FamilyConnect-0.1.18-beta94-stability.apk`.
- Native SHA256 `dd722eada0da7c890a8d71a72099cba5d0bbac1ce73377bbdbc8e7b85d820c23`.
  Signer SHA256 `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
- Android source/receipt: `state-client-build/rtp-deadline-20261020/normal94/android-source`
  and `android-build/receipt.json`; source-inventory file SHA256
  `f2ea940ec1fe18bbbcd8907890aa5b07ac0a305fc4d55fbd2e65e9aca41c7810`.
 94 preserves the sealed native libraries; it does not rebuild a native policy.
- Exact b9 SHA256 `b9ae880731517753e456637e52dcc421b9f7d7b881b400c856989ae93193e9ba`.
  Source: `state-client-build/tunnel-restart-20261019/gateway-source/carrier`;
  `gateway-build.json` inventory
  `4722b7353ba93209657f66b45c47874915362f1fbe732845ec61745abdb673e6`.

Entry10:08UTC: exact pair, NL PID3747077. Fresh guarded **counter-only** deployment
10:16:09.701UTC: PID3826820, invocation `804c0a5c4f0841abad5414687c768699`,
readiness PASS10:17:05UTC. Observer binary SHA256
`a575abed97fad68fe1cce8cf4876bad9f31563e10bcd83640e48357d4a633970`.
This is not a functional candidate. Bootstrap1011 files,64KiB, RS and RTP settings
unchanged; no full packet/media event export or receiver-trace overlay.

Exact b9 restored10:24:47.713UTC using a **fresh** guarded rollback intent, not
security-state restoration. PID3832764, invocation
`2647bbd3becf4217ae83ab1734ab2fb8`; TLS/runtime/binding/material/publication PASS
10:29:08UTC. Final10:30:44UTC: same b9/PID, active/NRestarts0,94 APK/native,
UID10283, app PID18202, one VPN. Profile hash unchanged across transition:
`de9045210af5e4c9e339fbecef7284077fd50722d034f2785712040077359892`.
Extended counters end by returning b9; no trace-removal APK needed.

Identity, Support ID, key bindings, all_activated, revocations, floors and credential
lifecycle were not changed/restored. Prior94 same-identity READY proof is reused,
not presented as a fresh identity audit. Renewal locks/current-material guards
used for both transitions. No push/public release/catalog/invitation/registration.

Tester: user reports already sending a version; its exact file/hash is unknown.
If its name/hash is94 above, it is
the correct ordinary build, **not93 B125**. No need to resend the identical copy.
Tester installation/version and whitelist operation are not yet observed. The
old beta90 incident in the supplied export is not a new beta94 failure.

## ACTUAL_MUX_CREDIT_CONTRACT

Exact Android94 capsule and b9 have identical `tcpforward/mux.go`, `mux_stream.go`,
`mux_protocol.go`, `protocol.go`. Android's existing Family receive observer stays;
gateway source is not substituted for accepted Android native source.

1. Gateway `io.CopyBuffer` reads the external socket with16KiB buffer. Mux `Write`
   marks available payload ready; reserves sendCredit only for bytes it can queue.
   One queued DATA frame per stream; chunk <=16KiB, further bounded by Family batch
   capacity (~16340). Actual socket reads are not always full16KiB.
2. Initial send/receiveCredit65536 **per stream/direction**, fixed65536 receive ring.
   Distinct from shared RS8 slots and external TCP windows. Production dedicated
   gateway max64streams; generic MuxConfig default16. Other limits unchanged.
3. Android `Read` copies out bytes, reduces used capacity, then adds the exact
   count to receiveCredit/creditPending and signals immediately. No return timer,
   threshold or deliberate coalescing wait. Ring capacity is freed, not necessarily
   final TUN/application consumption completed.
4. WINDOW_UPDATE is selected ahead of ordinary stream DATA, subject to existing
   controls/fairness (DATA opportunity after8 priority frames). It uses the single
   serialized Family TLS/RS writer: an already blocked SendContext cannot be
   overtaken. NL dispatch validates increment, restores credit and wakes Write.
5. Positive four-byte increment <=65536; cumulative credit overflow or excessive
   incoming DATA resets the stream. No validation removed or credit returned early.

See accepted Read/Write in `tcpforward/mux_stream.go`, pickLocked/nextLocked/
writeLoop/dispatchLocked in `mux.go`, decodeMux in `mux_protocol.go`, and
DedicatedMaxStreams in `roombroker/gateway.go`.

## SINGLE_VS_PARALLEL_EQUAL_VOLUME

Same media session, Android-TUN HTTP/1.1 meter/Cloudflare endpoint, full continuous
phone reads. Forward1/2/4 then reverse4/2/1:24MiB, **14/14 HTTP200/curl0/TLS-verified**,
no omitted failure or retry. One new TCP connection per request; no Range splitting.
PID3826820 throughout; media tag
`eb3e8f79e2c998dbc7472deadd1e85d1325a257c2e151c8bdcb1dc0786050297`.
117 compact snapshots/221 process-socket samples; zero journal reconstruction
errors. Underlay327 CELLULAR, tun1, full UID routing through10.79.0.1. NL response
exit metadata and actual PID sockets corroborate MESH, not AWG/TCP fallback.

| Order | Equal4MiB load | Common interval s | Aggregate Mbit/s | TTFB s | Per-request body-only s | Actual Mux IDs |
|---|---|---:|---:|---:|---:|---|
| 1 | 1×4MiB | 57.19 | 0.587 | 3.625 | 53.533 | 65 |
| 2 | 2×2MiB | 31.68 | 1.059 | 1.297–1.684 | 29.970–30.191 | 81,83 |
| 3 | 4×1MiB | 25.38 | 1.322 | 0.616–1.106 | 23.213–24.240 | 89,91,93,95 |
| 4 | 4×1MiB | 29.63 | 1.132 | 0.646–0.806 | 27.517–28.798 | 99,101,103,105 |
| 5 | 2×2MiB | 34.27 | 0.979 | 0.651–0.799 | 33.197–33.451 | 111,113 |
| 6 | 1×4MiB | 39.44 | 0.851 | 2.260 | 37.152 | 119 |

Aggregate = total body bytes / first phone BEGIN→last END, not summed individual
speeds. Body-only = curl total-starttransfer, approximating from first response
byte, not a separate body-byte clock. DNS/TCP/TLS cumulative setup values retained
per request in evidence. TTFB is application latency, not RTT. Different response
sizes retain different startup/tail fractions despite equal total volume.

Mux attribution uses new-stream lifetime + handed DATA totals in bracketing
snapshots. Matching endpoint socket maxima1/2/4/4/2/1 corroborate real connections,
not just HTTP counts. Parallel IDs are a matched set, not an invented per-curl
mapping.14–22 total Mux streams include background; this is not an idle session.

Reverse single improves45% **without a policy change**,0.587→0.851: a fixed0.57
ceiling is not established. Parallelism helps, but is not a single-flow fix.
Direct-NL4MiB control: HTTP200,0.781432s, TTFB0.080252s,42.94Mbit/s. It weakens a
persistent endpoint0.57Mbit/s cap explanation at that time, not every external TCP
explanation. It does not measure Android/MESH or whitelist connectivity.

## CREDIT_LIMIT_INDEPENDENT_OF_RS

**Insufficient data for causal independence from end-to-end RS recovery.** An
independent **local sender admission gate** is directly observed:

- Ready payload + zero credit in62/117 simultaneous snapshots.
-11 ofthose: shared sender RS has free slots (<8), local writer idle, local queue
  empty. Thus local RS fullness cannot explain every credit stop. All11 points
  occur in single-flow cells.
- Other51: shared RS full. ZeroCreditReadyNS and QueueReadyNS overlap; do not
  add those durations or intersecting RS wait categories.
- Free NL sender slots do not prove an absent Android receive head-gap or reverse
  delay. No paired Android Mux timing: consumer/scheduler/reverse recovery costs
  cannot be separated completely or all speed loss attributed to credit.

| IDs | Ready + zero credit s per stream | Ready + queued DATA s per stream | RS new/retry bytes, bracketing session samples |
|---|---|---|---|
| 65 | 46.475 | 11.347 | 4266641 / 783949 |
| 81,83 | 17.301 / 16.313 | 23.214 / 24.238 | 4282893 / 679700 |
| 89,91,93,95 | 0–0.230 | 23.048–23.366 | 4332007 / 525929 |
| 99,101,103,105 | 0.315–0.638 | 26.931–27.538 | 4286638 / 584427 |
| 111,113 | 14.606 / 18.096 | 27.929 / 28.587 | 4244978 / 700326 |
| 119 | 35.837 | 3.319 | 4383234 / 509996 |

RS includes background and sample edges, not exact HTTP allocation; its bracket
durations may exceed request intervals. Full/head-unconfirmed-with-later-SACK/
head-SACKed counters retained in evidence. Point counts are not exact durations.

## CREDIT_RETURN_TIMING

65:539 DATA chunks/4206222bytes including endpoint TLS overhead;422 updates,
mean increment9967bytes, mean update interarrival129.53ms/max1.413s.
119:543chunks/4206156bytes;438updates, mean9603bytes,86.14ms/max0.993s.
Small chunks coexist with near16KiB; full histograms/ready-byte gauges retained.

These are **NL update interarrival times**, not Android Read→update processing
latency or RTT. New ReturnQueueDelay measures gateway freed-ring→scheduler
selection, the opposite direction in a download; it cannot replace missing
Android timestamps. Source shows no needless timer/coalescing delay. Shared
ordered Family/RS can delay controls. Fast RS consume from prior evidence does
not measure downstream Mux/TUN consumption. No new profiler/Android build.

## LOCAL_MODEL_RESULT

Existing real Family TLS+Mux+ReliableStream fixture, matched64/128/256KiB ends,
512KiB total/cell,1 or4 streams, fast/slow consumers, delay and drop/reorder modes.
Synthetic byte-exact/race tests, not physical byte-exact acceptance.

Calibration: no-retry RS ACK mean312.691749ms →156.345875ms symmetric per-direction
**effective delay proxy**, not measured one-way SFU RTT.3007new/377retry blocks →
one-in8 first-attempt drops plus adjacent reorder. Retry density does not identify
forward loss probability, direction or actual arrivals; observed-shaped
sensitivity only. Existing2ms fragment serialization unchanged. Slow consumer
pauses the calibrated delay after each<=16KiB Read: independent negative scenario,
not a claim that Android actually consumes this slowly.

| Model | Flows | Consumer | 64KiB Mbit/s | 128KiB Mbit/s | 256KiB Mbit/s |
|---|---:|---|---:|---:|---:|
| Delay only | 1 | fast | 1.096 | 1.456 | 1.457 |
| Delay only | 1 | slow | 0.760 | 0.760 | 0.759 |
| Delay only | 4 | fast | 1.632 | 1.625 | 2.139 |
| Delay only | 4 | slow | 1.767 | 1.745 | 1.455 |
| Drop/reorder | 1 | fast | 0.497 | 0.597 | 0.596 |
| Drop/reorder | 1 | slow | 0.474 | 0.609 | 0.571 |
| Drop/reorder | 4 | fast | 1.000 | 1.000 | 1.002 |
| Drop/reorder | 4 | slow | 0.933 | 0.935 | 0.713 |

One sample/model cell, not a production benchmark. Fast single/no-loss64→128
removes1.057s ready-zero wait, improves33%; queued wait remains~1.96s. With faults,
zero-ready5.619→0.007s, queue wait1.355→4.215s, throughput+20%, not2×.128→256 has
no single gain. Four-flow loss case stays~1Mbit/s; shared RS remains limiting.
Slow cases can add memory or regress. Lower credit stalls alone are not acceptance.

## ONE_TARGETED_CHANGE / LEGACY_COMPATIBILITY

Implemented bounded counter delta + calibrated matched-pair model only. Smallest
model-supported future budget:128KiB, **not deployed**. No demonstrated needless
return delay justified option A. Option B is unsafe as a one-ended constant edit:

- OpenRequest has host/port/timeout_ms, rejects unknown JSON fields.
- openOK must be empty; unknown new control kinds fail decoding.
- Family ALPN exactly `family-connect-5n3-test-v1`; authenticated binding has no
  window capability. Existing batch support does not negotiate a window.

Required compatibility delta, **not implemented here**: explicitly authenticated,
version-selected session capability exchange confirmed by both peers **before**
stream/ring/initial-credit changes.128KiB only in agreed sessions; legacy clients
keep64KiB and never get elevated credit. Auth/protocol failures stay fail-closed,
not a downgrade trigger. This is coordinated protocol work, not a hidden overlay;
the task explicitly permits finishing at this laboratory boundary.

Counter patch `tests/fixtures/mux_credit/counter-only.patch`, SHA256
`5cbbaee5751eb2a7bc233a98d232524c625b0b80305b519b02474382a548c802`, applies after
pinned `mesh_perf3/accepted-overlay.patch` to exact b9. Five counter/export files;
clean reapply matches all247 observed source/test files (inventory SHA256
`27e8783c0afbcb684a25843851ba25a077371c9e73e61bada51576ce3b1e04b3`).
Tests separate. Model-only window edits in
private `lab-128/256` are not release artifacts. Read-alignment/SACK-hole/queue-
retry/finite-deadline patches remain separate and were not included.

## PHYSICAL_SINGLE_AND_AGGREGATE_GAIN

**NOT ESTABLISHED for a functional candidate.** Physical table is baseline64KiB
with identical server observability, not baseline-versus128KiB. No candidate run
or independent candidate media session claimed. Unused budget does not justify
incompatible deployment or repeated tuning. No RTP/RTO/pacing/hosting branch.

## FAILURES_LATENCY_MEMORY

-14/14 bulk complete; same media/PID throughout, no observed reconnect. TUN/underlay
  checked at cell boundaries/end, not continuous submillisecond gap monitoring.
  Controlled deployment/rollback replace sessions outside the measured matrix.
- ProtocolErrors1→1: **delta0 in matrix**. Initial1 belongs to this observer
  session before matrix, unknown cause; neither hidden nor blamed on credit.
  Historical A2/beta90 counts are not added to current increments.
- Gateway mean CPU5.65% of one core, peak RSS45224KiB; Mux retained high-water
 1706856bytes across background+bulk, RS sampled max114974bytes, local RS queue
  sampled empty. Mux retained includes allocated ring capacity, not only unread
  data. No precise Android CPU profile added.
- Model single server maxima81876/147412/278484bytes for64/128/256KiB; receiver
 65569/131105/262177. Four-flow server maxima327504/589648/1113936. Post-close
  retained accounting zero; synthetic bytes equal. Not all process/socket memory.
- Per-endpoint max64stream ring budgets4/8/16MiB (generic16stream1/2/4MiB);
  both ends double that. N users at64streams need N×4/8/16MiB gateway rings alone,
  e.g.10users40/80/160MiB. Add up to16KiB queued DATA/stream, current writer
  buffers, controls, FamilyTLS/RS, TCP buffers/runtime. Not a global process bound.
- Affected eight-package outside-sandbox race suite465 PASS/17 opt-in skips;
  counter delta4PASS. Matched-window regressions125PASS/2skips perwindow
  (375PASS total);24 model cells +3 parent tests PASS. Existing tests cover
  byte-exact, slow consumer, bounds/credit overflow, fairness, FIN/RESET/CLOSE,
  cancel/late callbacks/sibling isolation; bootstrap1011/recovery integrated.
  Counts include parents; prior unchanged tests reused, not recounted as new.
- First sandbox run socket-permission failures339PASS/57FAIL/17skip preserved in
  `checks-1.jsonl`; outside-sandbox repeat passes. Matrix preflight missing `re`
  import preserved in `matrix-preflight-failed-1`, fixed before bulk. No arbitrary
  sleep increase; failures did not end the task or consume a retry traffic series.

Final restored-b9 phone64KiB HTTPS control:200/TLS verified,
TTFB3.326959s/full4.348751s, same327/tun1. Not RTT or bulk-speed acceptance.
Task body total **29425664bytes =28.0625MiB**:24matrix +4directNL +0.0625control,
below64MiB;150s request cap. No candidate/retry series.

Remaining: exact Android credit-return versus reverse recovery timing unmeasured;
safe window capability absent. The specific compatibility delta above is required
before a future matched128KiB test; none is started here. Physical speedup and
tester whitelist acceptance remain unproven, not dependent on tester availability.
