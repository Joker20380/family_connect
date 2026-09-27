# 5N-PERF-2 — reliable operating envelope

## Verdict / scope

**5N-PERF-2 = PASS.** Starting clean commit `ca4f9e7`.
Highest accepted long-duration reliable application goodput **1.742311Mbit/s**
at cap3 over1800s. Conservative validated point **1.480531Mbit/s** at cap1.5
over900s. Sustained overload threshold and hard carrier ceiling **not established**.
Physical Redmi Note9 Pro / Android12 / arm64 / cellular → Family TLS1.3 →
ReliableStream → real Telemost VP8/RTP SFU → Amsterdam `186.246.45.246`.
No native DataChannel substitution, TUN, TCP/DNS/mux, FEC, multipath, redesign,
multi-user load or production deployment. No push.

Defaults unchanged: DATA16KiB, sender8, receiver16, cumulative ACK+32-bit SACK,
fresh bidirectional epochs, RTO1s, retries8, max recovery20s, bounded backpressure.
Application measurement window also8; offered rate is only a pacing cap.

Runtime **instrumentation only** `df6149e`: first128 events retained as before,
plus bounded latest128 later events with monotonic indices. Necessary because the
old first128-only snapshot cannot expose late recovery latency during a long run.
No wire/protocol/timing/queue/default behavior changes. Harness `04f39f2` adds
1800s bounded measurements, streaming128-row exact evidence, complete bounded
RTT sample storage, GC counters and incremental file observation. Observer-only
repairs `c06839c`/`4f4e8e9`; active/teardown and exact-sequence audit `e0b1334`;
final harness `4475560` adds sampled CPU reporting and fresh admission evidence.
Tested native binaries remain clean `04f39f2`; later changes are Python-only.

Diagnostic built/installed code2/name`5N.3-test-only`, never public/distributed.
Public Android beta51/code51, Linux0.2.11, Windows0.2.15, catalogs/invitation pages
unchanged. Latest observed GitHub phase0 run36268143806 on8e368585 was failure;
it is not validation or deployment of these local commits and was not rerun.

| Built artifact | SHA256 |
| --- | --- |
| Linux CLI | `64c7c0b265ddde1957992c8aeeb63ae2dee6b0a5940122b7b6810ff73543e7d9` |
| Android PIE | `28aa61afac864447e4d53cdfc73cc2a37bdca72f02fb6347c902e8b0f9f773bb` |
| Diagnostic APK | `010a3d25e289e87fca50ce7793713afea41e109bd7687ea41cd7e2c20e1c1a00` |

## Baseline reproduction

300s measured,300.962170s with drain,3935/3935 exact16KiB echoes.
Cap2Mbit/s; actual TX1.717480, reliable delivered1.716169, aggregate3.433649,
drain-normalized1.713731Mbit/s. Complete sequence/random-byte validation,
zero corruption/duplicate/delivered-reorder/missing/timeout/disconnect/bad-MAC.
RTT avg/p50/p95/p99/max595.852/554.731/819.938/1375.918/1899.162ms.
REL-1 comparison: delivered1.883505→1.716169 (−8.9%); avg422.949→595.852ms.
New baseline has2 RTP gap events,6/6 recovered reliable gaps,7 retransmissions,
50,101 retry payload bytes across both endpoints; carrierQ sampled maxima6/7.
No queue runaway or active-session TLS failure. Discovery cap2 and minute
distributions provide the additional environment comparison below.

| Cap2 comparison | REL-1 accepted300s | PERF-2 baseline300s | PERF-2 discovery120s |
| --- | ---: | ---: | ---: |
| Useful TX Mbit/s | 1.885252 | 1.717480 | 1.773841 |
| Reliable goodput Mbit/s | 1.883505 | 1.716169 | 1.769472 |
| RTT avg/p95/p99 ms | 422.949/647.240/1180.171 | 595.852/819.938/1375.918 | 485.831/868.299/1316.243 |
| Sampled carrierQ max, A/B | 5/11 | 6/7 | 4/7 |
| RTP gap events / recovered block gaps | 0/0 | 2/6 | 0/0 |
| Retransmissions, session lifetime | 0 | 7 | 1 |
| Go heap peak B, A/B | 11104240/12371600 | 11979568/12055304 | 11456832/11514256 |
| Android PSS peak KiB | 199296 | 194067 | 172629 |

The120s resource sample has a shorter warming period and is not a like-duration
memory comparison. New baseline sampled native CPU is14.311% A/7.012% B of one
core, battery100→100 on USB. Natural gaps and session RTT differ, but resource
peaks/queue bounds do not show a new accumulating backlog. REL-1's separate60s
gap-proof sessions are deliberately not substituted for its gap-free300s run.

### Observer evidence and excluded attempt

Initial `baseline` aborted before measurement: `adb exec-out` merged missing-file
stderr into stdout, which corrupted an incremental JSON offset. Preserved as
observer FAIL, not a reliable transport run. Operator reported a concurrent phone
call; this is an environmental note, not the cause of the proven parser defect.

`baseline-observed` native transport completed300s without restart. The first
observer repair incorrectly quoted the script for `exec-out` (unlike `adb shell`),
so independent direct ADB reading recovered the complete original private log.
Only after Android's successful exit was the stuck observer interrupted, triggering
its normal remote cleanup. Original observer exit is not promoted to PASS.
Amsterdam stayed alive after normal Android completion and ended19.6s later with
`recovery_exhausted` during post-exit teardown; last active snapshot had no terminal
error and all3935 accepted application messages were already exactly echoed.
This is recorded separately from in-run retry exhaustion/overload; final cleanup
must not be confused with an unexpected measurement closure. Baseline running
process hashes were not captured before Android exit; embedded clean revision
and built/installed artifact provenance are retained. Subsequent runs require
live `/proc/<owned-pid>/exe` hash matches on both endpoints.

## Rate sweep

Each discovery point120s after5s warm-up/drain, fresh sessions. No artificial
faults, window changes or retries-to-green. Rates are Mbit/s; RTT is ms. Gap/retry
rates below use complete session counters / measurement minutes (warm-up/drain
included in counters); they are not independently measured stationary loss rates.
`CORRECT` means complete byte/sequence validation, not long-duration acceptance.

| Offered | Actual TX | Reliable goodput | RTT avg | p95 | p99 | gaps/min | retrans/min | carrierQ max | result |
| ------: | --------: | ---------------: | ------: | --: | --: | -------: | ----------: | -----------: | ------ |
| 0.5 | 0.499166 | 0.496981 | 491.056 | 552.696 | 592.281 | 0 | 1.5 | 10 | CORRECT, discovery |
| 1.0 | 0.983040 | 0.979763 | 410.970 | 958.234 | 1379.453 | 0 | 0.5 | 10 | CORRECT, discovery |
| 1.5 | 1.430869 | 1.427593 | 375.750 | 829.956 | 1313.845 | 0 | 0 | 8 | CORRECT, discovery |
| 2.0 | 1.773841 | 1.769472 | 485.831 | 868.299 | 1316.243 | 0 | 0.5 | 7 | CORRECT, discovery |
| 2.5 | 1.600171 | 1.593617 | 672.978 | 1295.595 | 4803.857 | 11 | 22.5 | 7 | CORRECT, severe transient tail; not stable proof |
| 3.0 | 1.800055 | 1.795686 | 579.499 | 868.880 | 1377.692 | 0 | 0.5 | 8 | CORRECT, long-run candidate |

Cap2.5 had22 return RTP gap events,18/18 recovered blocks,45 retries. RTT max
9824.765ms almost reached the unchanged10s application deadline; drain took6.483s.
Drain-normalized goodput1.520227Mbit/s. Carrier queues did not grow without bound;
there is no post-burst sustained under-load recovery observation beyond the end
of this short point. It is **not** labelled a stable operating point.
The next cap3 point and its30min validation are substantially better; therefore
this burst does not establish a monotonic rate-dependent overload threshold.

Cap2→3 raises actual goodput only1.48%, while application average outstanding
rises6.574→7.955 (limit8). RTT avg rises485.831→579.499ms. Carrier queue does not
grow, delivery efficiency remains1, and loss/retry rates do not rise systematically.
This is a **window/RTT-limited region**, not proof of hard carrier saturation.
No cap4 run: with nearly full application window8 and no pacing debt, merely
raising the cap would not establish a greater offered data load or carrier ceiling.
No diagnostic window tuning was used.

The new cap2 discovery1.769472 and300s baseline1.716169 are6.1%/8.9% below REL-1's
1.883505. Both retain exact delivery, bounded queues and unchanged transport
behavior. This is observed session/environment variance, not evidence for a fixed
carrier RTT or a core regression; its precise network/SFU cause is not established.
The operator's call in the excluded initial attempt is not used as a causal claim
about later sessions. Measurements use cellular, not an active VPN/Wi-Fi path.

## Long-duration runs

### Cap3 — 1800s accepted application run

UTC measured start19:31:27.741, result20:01:29.282 with1.535s drain.
**23,935/23,935 exact echoes**,392,151,040B each direction including drain.
Interval TX392,085,504B →1.742602Mbit/s; exact RX392,019,968B →
**1.742310969Mbit/s one-way useful goodput**. Aggregate3.484913Mbit/s;
drain-normalized1.741408Mbit/s. No missing accepted application data.

RTT avg/p50/p95/p99/max:
**599.271/570.229/756.025/1010.886/2598.424ms**. All23,935 samples retained;
this run passes the previous16,384-sample limit without truncating correctness.
Application outstanding avg7.968/max8, queued unsent jobs avg3.100/max4.
19,243 bounded producer-backpressure episodes, no accumulated pacing debt.

5 natural RTP gap events,5/5 recovered reliable gaps,0 unrecovered. Recovery
avg/p95/max1466.778/1946.356/1946.356ms. Seven data-work retransmissions from
Amsterdam; final session total8 includes one34B tail/teardown retransmission
outside the1800s interval. Total retry payload98,360B; defined overhead0.012541%.
Android suppresses2 duplicate carrier DATA frames; application duplicates/reorder0.
No active retry exhaustion, RESET, TLS bad-MAC, corruption or unexpected close.
Expected final close yields one RESET/endpoint and `cancelled` after completion.

### Cap1.5 — 900s conservative point

**10,169/10,169 exact echoes**,166,608,896B each direction including drain.
900s measured,900.998s with drain. Actual TX1.480968Mbit/s; reliable goodput
**1.480531058Mbit/s**, aggregate2.961499, drain-normalized1.479327Mbit/s.
RTT avg/p50/p95/p99/max275.649/254.324/380.603/793.063/1347.565ms.
No RTP/block gaps, retries, carrier duplicates, TLS/application errors or active
exhaustion/RESET/closure. A gap-free accepted run is not fault-injected to manufacture loss.

Application outstanding avg3.115/max8; unsent jobs avg0.056/max3;125 backpressure
episodes. Compared with cap3, the average application window is39% rather than
99.6% occupied; RTT and retry exposure are lower. This provides meaningful
headroom even though event-sampled gateway queue maxima are not lower.

### Queue / memory evolution

Quarter means below use only active samples, not zero queues after teardown.
A is Android, B is Amsterdam. B samples follow every128 echoes and are **not
time-weighted**; averages from different pacing phases cannot alone rank load.

| Run | Endpoint | carrierQ quarter means | sampled max | send/reorder high-water | max retained DATA B |
| --- | --- | --- | ---: | --- | ---: |
| 1800s cap3 | A | 0.600 / 0.522 / 0.733 / 0.544 | 8 | 8 / 8 | 82222 |
| 1800s cap3 | B | 2.457 / 2.267 / 1.979 / 2.122 | 9 | 8 / 8 | 82234 |
| 900s cap1.5 | A | 0.689 / 0.467 / 0.778 / 0.556 | 5 | 8 / 3 | 74050 |
| 900s cap1.5 | B | 6.158 / 8.000 / 6.850 / 6.850 | 10 | 8 / 3 | 82110 |

No sustained queue-baseline drift. Cap3 RTT/minute averages674ms initially,
626/659/611ms in gap-heavy minutes9–11 (zero-based),611ms in minute17, then
588/563ms in18–19 and572ms in the final minute. Minute p99 returns from2484ms
in minute9 to860/728ms in18–19 and857ms at the end: no RTT runaway.

| Resource | cap3 A | cap3 B | cap1.5 A | cap1.5 B |
| --- | ---: | ---: | ---: | ---: |
| Go heap sampled peak B | 13284528 | 13080296 | 12884488 | 12629008 |
| Go HeapSys peak B | 23724032 | 19759104 | 19464192 | 19759104 |
| getrusage RSS high-water KiB | 111948 | 31460 | 113544 | 30772 |
| native CPU, % of one core, sampled | 13.819 | 7.106 | 13.308 | 6.225 |
| Java process CPU, % of one core | 10.153 | n/a | 10.177 | n/a |
| Java process PSS peak KiB | 197919 | n/a | 200158 | n/a |
| goroutines peak | 172 | 224 | 178 | 223 |
| GC cycles, final sampled | 1118 | 1028 | 500 | 467 |
| total GC pause ms, final sampled | 509.984 | 102.573 | 254.325 | 43.349 |

Cap3 Go heap quarter means A9.32/10.00/10.10/10.30MB, B8.96/9.61/9.60/10.07MB:
there is modest warm-up/allocation variation, **not a claim of zero memory growth**.
HeapSys remains bounded and slightly decreases after the initial quarter; steady
goroutines stay170/222. No runaway allocation, OOM or ANR observed. Native RSS
and Java PSS have different scopes and are not simply summed. Both runs show
battery100→100 while USB charging; energy efficiency is not established.
Cap3 sampled nominated-pair ICE RTT means A101.960ms/B51.888ms; these SFU legs
are not Family application RTT. Reliable ACK RTT is not exposed.

## Natural gaps / reliability

Across nine completed performance sessions: **45,452 exact measured echoes**,
29 RTP gap events,29/29 recovered reliable block gaps,0 unrecovered;66 lifetime
retransmissions in7/9 sessions (including control/warm-up/tail retries). No
accepted plaintext corruption, duplicate delivery, delivered reorder or missing
accepted data. Native RESET/closure counters include expected teardown; the
baseline observer's delayed post-exit exhaustion remains explicitly separate.

For the30min run: gap counts in measurement minutes9/10/11/17 are2/1/1/1;
remaining minutes0. Corresponding active retry counts2/3/1/1, plus one tail retry
after the interval. Natural gaps0.1667/min; active retries0.2333/min, lifetime
normalized retries0.2667/min. All indexed recovery events are captured. One of
two long sessions actually needs ARQ recovery; the other has no natural loss.
Counters alone do not imply every retry was caused by RTP loss: ACK timing/loss
and normal final abort can cause retries without a detected block gap.

Cap3 ACKSent A145472/B145473, SACKSent72996/74020; cap1.5 ACKSent62022/62029,
SACKSent34849/36680. ACK headers total18,620,480B /7,939,264B respectively;
DATA headers9,200,832B /3,914,176B. SACK/reorder activity also reflects buffered
contiguous blocks waiting for consumption, not only gaps. Exact ACK/SACK RX,
all resource distributions and per-minute cumulative counters are in the evidence.
Full media/WebRTC/IP byte overhead is not measured; RTP/frame counters and ICE
RTT are available, but no packet-capture-derived wire bitrate is claimed.

### Per-point byte accounting

TX/RX columns here include completed drain; interval byte totals are retained
separately in evidence. Delivery efficiency is1.000000 for every row.

| Point | Exact TX B = exact RX B | Retry payload B, both endpoints | Defined retry overhead % |
| --- | ---: | ---: | ---: |
| baseline2 /300s | 64471040 | 50101 | 0.038855 |
| discovery0.5 | 7487488 | 5812 | 0.038811 |
| discovery1 | 14761984 | 859 | 0.002910 |
| discovery1.5 | 21463040 | 0 | 0 |
| discovery2 | 26640384 | 2290 | 0.004298 |
| discovery2.5 | 24035328 | 393810 | 0.819232 |
| discovery3 | 27066368 | 859 | 0.001587 |
| long3 /1800s | 392151040 | 98360 | 0.012541 |
| long1.5 /900s | 166608896 | 0 | 0 |

## Operating envelope

- **Highest observed stable long-duration goodput:1.742310969Mbit/s**, proven
  for1800s at offered pacing cap3.0, not sustained3Mbit/s of application data.
- **Conservative demonstrated point:1.480531058Mbit/s**, cap1.5,900s; substantially
  lower RTT/window occupancy and no observed loss/retries. Approximately1.4–1.5
  useful Mbit/s is the evidence-based planning region for a future TCP experiment,
  not a hardcoded production default or a guarantee on another network.
- Highest PERF-2 short-run goodput:1.7956864Mbit/s at cap3,120s.
- **First sustained overload/instability threshold: not established.** Cap2.5's
  severe transient is a warning, not a proven rate-dependent threshold; no third
  long overload point is selected because none is unambiguously identified.
- **Hard carrier ceiling: not found.** The fixed application window8 is almost
  full near cap2–3; plateau alone cannot identify SFU bandwidth saturation.
  RTO is not demonstrated to be the primary steady-state limiter. The near-deadline
  burst merits future investigation, not RTO tuning or FEC in this task. Future TCP
  framing/workload may change effective window usage and needs its own gate.

## Metric definitions

- Primary goodput: exact useful echoed application bytes received within the
  measurement interval ×8/duration/1e6, counted once, not bidirectional aggregate.
  Echo proves the forward and return path; this is not synchronized one-way delay.
- Actual TX: successful application-send bytes within the same interval. Final
  TX/RX totals include drain, with equality required for every accepted message.
- Delivery efficiency: final exact RX useful bytes / successful TX useful bytes.
- Retry overhead: session-lifetime retransmitted DATA payload bytes (both
  directions, including warm-up/auth) / measured final TX+RX useful bytes ×100.
  This explicitly mixed scope is conservative, not exact network wire overhead.
- ACK/control headers: ACKSent×64B; DATA headers: (DataSent+retransmissions)×64B.
  OPEN/RESET, TLS, VP8/RTP/DTLS/IP overhead are not included in those formulas.
- RTP gap events are sequence-discontinuity counters, not proven lost-packet count.
  Reliable block gaps/retries are separate. SACK/reorder activity need not mean loss.
- Queue samples are sampled maxima, not exact carrier queue high-water. Reliable
  send/reorder/retained-DATA high-water comes from runtime counters.
- RTT uses all measured creation-to-exact-echo samples, nearest-rank quantiles.
  Recovery quantiles require all indexed events; missing telemetry is explicit.
- Minute bins use endpoint UTC for sample association, not cross-endpoint latency;
  exact RTT uses Android monotonic times. B samples are per128 completed echoes.
- Java process PSS and native child RSS/Go heap are separate. USB charging means
  battery percent delta is not a power-efficiency measurement.

## Final canonical regression — PASS

Preflight and final deterministic ReliableStream regression cover one dropped
block, reorder, duplicate, ACK loss, burst loss, TLS recovery and exhaustion.
Fault injection is separate from all accepted performance measurements.

| Check | Final evidence |
| --- | --- |
| Physical canonical exact bytes | 516/516 echoes,6,890,785B TX=RX,exit0;7 sizes,100×1KiB,100×16KiB,30s and300s stages |
| Canonical sustained stage | 281×16KiB,300.388092s; stop-and-wait0.122612Mbit/s, not an envelope measurement |
| Auth/admission | Fresh allowed session; wrong-family,revoked,unknown all rejected before echo and before cleanup |
| Replay | Native physical replay rejection PASS |
| Activity recreation/background | Same parent5474/child5504 across recreation;20s background/foreground survives |
| Cancellation / Activity close / force-stop | Expected exit in2.138s /2.150s /0.091s |
| Remote exit | Expected exit in11.741s, including unchanged10s application deadline and observation delay |
| WebSocket / PeerConnection close | Both native physical cases PASS |
| Cellular loss / fresh recovery | Terminal in0.482s,code1,not user-cancelled; explicit fresh session PASS; no auto-reconnect |
| Controlled dropped seq2 | 8/8 exact echoes,TLS survives,1/1 recovered,max1350.358ms; client2/server1 retries |
| Go | All5 packages race×3,vet and module verification PASS; disposable ProductStore fixture integration exercised |
| Fuzz | 5s each: FRS frame155508,engine161960,IPC154461,carrier33376 executions; all PASS |
| Python | 982 passed,1 optional skip,2 existing warnings,29.14s; control+identity lockfiles |
| Android | Final forced rebuild/JVM6/lint PASS;0 lint errors,6 existing warnings; APK hash identical to installed binary |
| ARM native | 10 ReliableStream,7 Family,8 carrier,10 CLI test groups PASS; plus2 FRS/1 carrier fuzz-seed groups |

The Python skip is `test_real_kdbx_to_apksigner`, which requires an explicit
Android SDK/public APK signing fixture. Existing warnings are httpx/Starlette
deprecations. The optional ProductStore fixture case is skipped in the ARM
binary but exercised in the local Go run. These are not unperformed live
admission/reliability checks. Canonical sustained RTT avg/p50/p95/p99/max is
1068.919/1046.970/1188.831/1578.017/1632.800ms; stop-and-wait scheduling differs
from the performance workload and must not be mixed into its table.

Build preparation initially hit SDK/cache permission failures; owned copied
caches resolved them. No protocol changes, platform releases or CI reruns.

## Sanitized evidence / cleanup / rollback

- [Metrics, counters, per-minute observations, regressions and cleanup](2026-09-27-webrtc-5n-perf2.sanitized.json).
  SHA256 `86f5130e9ca06f203f07d450d75112e4c098d71cbf807384ecf8c1661cba3f4d`.
- [Complete numeric application timing/sequence rows](2026-09-27-webrtc-5n-perf2-timing.sanitized.jsonl).
  SHA256 `6956597c786efd5cce2dd7a1881f4cbcdca1a3aabf1fdeddc202fed91fa88f08`.

Post-export audit independently verifies all9 performance sessions,45,452 exact
measured sequence rows without holes/duplicates, TX=RX byte totals, throughput
formulas and all RTT mean/quantiles. Warm-up rows are marked separately. Raw
evidence hashes and the excluded observer failures remain in sanitized evidence;
private payloads, room URLs, credentials and raw logs are not committed.
Documentation link check `python3 scripts/check_public_docs.py --all` and
`git diff --check` PASS; the link check is not public artifact verification or rollout.

Cleanup **PASS**: diagnostic APK uninstalled;20 Android and25 Amsterdam known
process IDs checked, no owned processes remain. Android PID16264 has been reused
as a thread of another process (Tgid29490), not a surviving test process; it was
not killed. Owned native/remote test directories0. Initial mobile_data1/wifi_on1
restored. Disposable fixtures/credentials, raw private logs, local diagnostic
APK/PIE/CLI/test binaries, generated builds and owned tool/cache copies removed.
Pre-existing SDK/NDK/Go/Gradle caches preserved. No production service/routing/DB,
public artifact, catalog or invitation change. No push.

No unfinished PERF-2 checks. A concurrent, unrelated VPN audit appeared after
the clean start; its files and STATUS/PLAN edits are preserved and excluded from
the PERF-2 commit. A globally clean worktree cannot be claimed while those foreign
changes remain; this is not permission to discard or commit them.

Runtime commit `df6149e` is telemetry-only; harness commits end at `4475560`,
tested native revision `04f39f2`. Rollback needs no production action: owned
diagnostics are already stopped/uninstalled. If source rollback is requested,
revert PERF-2 commits in reverse order; never reset foreign work. **STOP: no5N.4.**

## Limitations

One physical device/network environment; no TUN, TCP workload or multi-user load.
No production readiness claim. Telemost/SFU/network conditions affect results.
No automatic operating default, RTO tuning or FEC. Hard physical carrier ceiling
need not be found for this gate. Stop after PERF-2; **do not start5N.4**.
