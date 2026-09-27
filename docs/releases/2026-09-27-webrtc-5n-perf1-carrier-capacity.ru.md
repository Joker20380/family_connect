# 5N-PERF-1 — physical Telemost VP8 carrier capacity

**5N-PERF-1 = FAIL: устойчивый throughput ceiling не установлен.**
Это не отсутствие измерений: все7 обязательных окон,6 offered rates и5 payload
sizes проверены.22 performance attempts:17 completed zero-error,5 FAIL.
Failed points полностью сохранены, не превращены в PASS повторными попытками.
Наиболее быстрые60s результаты не выдержали отдельную300s validation.

**Главный ответ:** highest error-free60s = **1.9922944Mbit/s one-way** при
paced offered2Mbit/s; highest completed300s = **0.130635093Mbit/s** при
16KiB/window2. Ни одно из этих чисел не объявляется физическим/production ceiling.
Hypothesis о прежних0.0655Mbit/s one-way /0.131Mbit/s aggregate **подтверждена**:
window2 дал примерно×2, paced2Mbit/s дал примерно×30.4 в60s окне.
2s RTT не является неизменным свойством carrier: paced2 →avg317.584ms.

[Sanitized raw evidence и полные normalized metrics](2026-09-27-webrtc-5n-perf1.sanitized.json).
В JSON сохранены min/max/p50/p95/p99, counts/bytes, TX/RX/aggregate/drain rates,
achieved outstanding, queues, timings, resource samples и numeric Pion reports.

## Scope / provenance

Measurement-only investigation, started from clean
`477bbfafd5290ca51df8b756dc85680a2bee649d`. No production rollout, no push,
no5N.4/TCP/TUN/DNS, no native DataChannel substitution. Physical Redmi Note9 Pro,
Android12/arm64 → Family TLS1.3 → real Telemost signaling/SFU → unchanged VP8 →
temporary nobody endpoint on Amsterdam `186.246.45.246` → authenticated echo.
Production Android beta51/code51, Linux0.2.11, Windows0.2.15 remain unchanged.
Diagnostic APK retains code2/5N.3-test-only; rebuilt locally, not distributed.

Last external CI checked at entry: phase0 `36268143806`, remote
`8e3685854f3beea07aea573fa775e97a6220a70d`, completed/failure26.09. It is not a
validation of this unpushed work. Existing runtime baseline is5dd8b49, prior
harness e4b67f8. Source changes in this task:

- `7d60c59`: opt-in read-only queue lengths and numeric/boolean Pion GetStats.
  No addresses, credentials, SDP or arbitrary Pion strings are emitted.
- `3540cd2f77ddb52b1d4bdbb42f7619ee2e843ebb`: bounded asynchronous CLI harness,
  optional private performance.input in the diagnostic wrapper, physical runner.
  Carrier pacing, framing, Telemost signaling, TLS and Family authorization unchanged.

## Phase A — canonical reproduction

Clean starting source, original acceptance code, original stop-and-wait probe.
Seven sizes,100×1KiB,100×16KiB,30s and5min, without modified instrumentation.
The accepted5min point:151×16384B in301.991478843s; avg1999.843353974ms,
p50/p95/p99=1999.691823/2008.942187/2016.646978ms. Useful one-way
0.065537849200Mbit/s, aggregate0.131075698399Mbit/s. Android exit0, B exit0,
remote cleanup without forced kill. **Baseline reproduced.**

Baseline Linux SHA256 `a2bf237f2db22d3c5b5371bff63fec0bfd6e47dc2897589fbcbb3b84e979bb36`;
Android native `d5fd45fa55e13c5eb0faba81263d9423c16e2947df15ba9127a6b082b1c6095d`;
APK `9d98b99325af0f2c30e482edc5a38326994dbe88468a7ccf7e5ea759f0a88e86`.

## Method / definitions

Each point opens a fresh authenticated session.5s warm-up, then drain before
starting the measurement clock. Measurement producer runs60s (or300s for selected
validation), then drains already submitted blocks; raw interval and drain-normalized
rates are both retained. Warm-up results are excluded; a warm-up failure still fails
the point. Discovery<60s is explicitly not an accepted-duration measurement.

One sender goroutine and one independent receiver; up to requested window blocks
can be created/enqueued before any echo. Rate mode schedules creation from a
monotonic offered-rate clock independently of ACKs. Reaching128 outstanding stops
the point instead of throttling the producer to disguise overload. No retries.
Payload is exactly the stated size, with an8-byte sequence embedded in the synthetic
payload, not an additional wire header. The full byte array must match, including
sequence; Family's existing authenticated frame sequence also remains enabled.
Useful bytes mean complete synthetic application payload, excluding existing
Family/TLS/carrier/RTP headers, padding/keepalives and retransmissions.

Bounds:128 outstanding,65536B per payload,10s block deadline,300s measurement,
16384 RTT samples; app evidence remains bounded2MiB/1024 events. Timeout,
corruption, wrong sequence, unexpected frame or exhausted resource bound ends
the point as FAIL. Pending successfully-sent blocks without a validated echo are
reported as missing/unconfirmed, not proven permanent media loss. Recovery is
not automatic and its count is zero within every point.

A records sequence, created/enqueued, SendContext begin/return and exact echo time
using one monotonic clock. B records application receive, echo enqueue and send
return on its own monotonic clock. Send return means accepted by the existing TLS
bridge/queues, **not proven RTP transmission**. Clocks are not synchronized enough
to infer one-way media latency; forward and reverse delays must not be invented.
Every5s A samples application/carrier queues, Pion numeric counters and existing
sanitized carrier evidence. B retains per-block echo stages and Pion snapshots.
Missing/zero Pion values are not evidence of an available end-to-end SFU estimate.

Interval RX rate counts exact validated echoes arriving within the measurement
interval; each proves a delivered forward payload and return payload. B's independent
receive timestamps/counters are retained too. Drain-normalized rate counts all
validated measurement payloads divided by measurement+drain; it avoids claiming
undelivered tail data as throughput. RTT includes local enqueue time, not just ICE RTT.
Reference `window_bytes*8/observed_RTT` is a window-bound diagnostic, not a carrier
capacity prediction.

## Final source / artifacts

- `7d60c5939011b70428a190d3d7f5dfb0d07bb575`: отдельный read-only instrumentation commit.
- `3540cd2f77ddb52b1d4bdbb42f7619ee2e843ebb`: первоначальный asynchronous harness;
  physical window1/2/4 measurements именно на нём.
- `589096c58292f945c2e80d31c89df5867fb67fb2`: только исключение невыбранных ICE pairs
  из evidence, чтобы длинный run не достигал2MiB log bound. Собран, отдельно не установлен.
- `f1a211a4fde7eebfa00f78b9d0b27d78b5e8ccd7`: static sanitized error classification;
  **final running binary/harness** для остальных measurements и regression.
  No retry/deadline/pacing/auth/framing changes. Clean builds, vcs.modified=false.

Final Linux SHA256 `e9d8ed859f12868813290cf335bb1ea0385ce57b5c0c713278da9447e95e56d5`;
Android native `740ab45d6c049156f258e47653731588aec9440e27c27f6d66834cc9c960d092`;
APK `6650b7e9aba4b294926ab93458ad7d8279fb90df21f081d283cb5699b6b559a7`.
Built/temporarily installed only; no public assets/catalog/invitation changes.
Documentation/evidence are a subsequent separate commit; its hash is supplied
in the final session response (a document cannot contain its own commit hash).

## Phase B — window sweep,16KiB

All requested windows were attempted once; window4 failed in warm-up, so it has
no accepted60s result. No128 expansion: saturation-like behavior, bufferbloat and
integrity failures already appeared. Requested data excludes protocol overhead.

| Window | In-flight KiB | RX Mbit/s | Drain Mbit/s | avg ms | p95 ms | p99 ms | sent/echoed | errors |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 16 | 0.065536 | 0.065656 | 1996.236 | 2010.460 | 2015.886 | 31/31 | 0 |
| 2 | 32 | 0.089566 | 0.090891 | 2837.316 | 4004.827 | 4012.508 | 43/43 | 0 |
| 4 | 64 | 0.000000 | 0.000000 | — | — | — | 4/0 | FAIL:4 unconfirmed/closure |
| 8 | 128 | 1.815347 | 1.773748 | 575.946 | 908.676 | 1276.105 | 839/839 | 0 |
| 16 | 256 | 1.389363 | 1.378481 | 1486.821 | 2196.841 | 2844.155 | 652/652 | 0 |
| 32 | 512 | 1.778210 | 1.732682 | 2326.449 | 3725.695 | 4336.560 | 846/846 | 0 |
| 64 | 1024 | 1.481114 | 1.519829 | 5314.308 | 9186.239 | 9589.090 | 742/742 | 0 |

Window1 reproduced the original behavior with independent workers. Window2 has
session variability:60s gave0.089566Mbit/s/2837ms, whereas its300s run gave
0.130635Mbit/s/2000ms. Do not infer a deterministic capacity curve from one
fresh session per point, or attribute this difference to the statistics-only patch.

Window4:0.402987865s of warm-up,4 sent,0 confirmed echoes. B application received
and submitted all4 echoes. A has one post-reorder RTP gap, then stream closure.
The original harness did not yet classify the native TLS error; do not retroactively
label it as proven bad-record-MAC. Subsequent higher windows passed60s: this first
failed point is **not proof of a universal overload threshold at window4**.

## Longer validation — complete outcomes, not cherry-picked prefixes

| Point | Requested s | Measured s | RX Mbit/s | avg RTT ms | sent/echoed | Result | Terminal |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 16KiB/window2 | 300 | 300.000 | 0.130635 | 1999.765 | 301/301 | PASS | none |
| 16KiB/window8 | 300 | 82.990 | 1.255606 | 830.328 | 803/795 | FAIL | tls_bad_record_mac |
| paced2Mbit/s | 300 | 6.481 | 1.860621 | 280.959 | 99/92 | FAIL | tls_bad_record_mac |
| 64KiB/window2 | 300 | 252.274 | 0.259781 | 3983.877 | 127/125 | FAIL | tls_bad_record_mac |

300s window2 completed with301 exact echoes,4,931,584B each direction including
drain; interval RX4,898,816B. Elapsed including drain301.999884312s.
Avg/p50/p95/p99=1999.764619/1999.778073/2046.538384/2128.153593ms,
min/max820.514531/3407.846770ms. Achieved outstanding avg1.999993/max2.
Drain-normalized RX0.130638037Mbit/s; interval aggregate0.262144Mbit/s.

Long window8, paced2 and64KiB/window2 all terminated on TLS bad-record-MAC,
each with one A return RTP gap and no B forward gap. Even the252s completed prefix
of64KiB is **not** accepted as a sustainable result: the full requested run failed.
Long16/64-window validation was cancelled after long8 failed; no retries-to-green.
The64KiB long run also had≈4s RTT versus≈2s in its short run, demonstrating
session/media-phase variability rather than a reproducible constant RTT.

## Phase C — independent offered load,16KiB

Producer follows a monotonic rate schedule, not the echo completion.128 is only
the outstanding safety bound. Actual observed concurrency is much smaller below
overload; max10/average4.81 at offered2Mbit/s. Raw rows include individual B receive
timestamps for successfully submitted echoes. The table RX is stricter confirmed
delivery at A, not a claim that unconfirmed blocks never reached B.

| Offered Mbit/s | TX Mbit/s | RX Mbit/s | TX+RX Mbit/s | avg ms | p95 ms | p99 ms | max/avg outstanding | Result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.1 | 0.100489 | 0.098304 | 0.198793 | 1721.799 | 2128.189 | 2819.567 | 2/1.29 | PASS60s |
| 0.25 | 0.251221 | 0.246852 | 0.498074 | 1098.972 | 1208.570 | 1266.395 | 3/2.07 | PASS60s |
| 0.5 | 0.500258 | 0.495889 | 0.996147 | 675.873 | 753.051 | 896.312 | 4/2.55 | PASS60s |
| 1 | 1.000516 | 0.993963 | 1.994479 | 444.484 | 594.580 | 705.197 | 6/3.36 | PASS60s |
| 2 | 2.001033 | 1.992294 | 3.993327 | 317.584 | 556.082 | 593.285 | 10/4.81 | PASS60s |
| 4 | 4.010803 | 3.329229 | 7.340032 | 841.704 | 875.005 | 885.964 | 27/23.53 | FAIL warm-up |

Offered4 failed in warm-up:5s production plus0.567614372s drain,153 sent/139 echoed,
14 unconfirmed, bad-record-MAC after an A RTP gap.3.329229Mbit/s is a **failed
warm-up interval**, not accepted throughput. Higher rates were not attempted.
Paced2 reached1.9922944Mbit/s without errors for60s (916 total validated blocks;
drain-normalized1.936370Mbit/s), but its separately planned300s validation failed
after6.480968748s. No stable upper ceiling can be inferred from the short PASS.

## Payload-size sweep

Window2 was selected instead of the apparent short-run knee8 because2 was the
only window with successful300s validation. This is an explicit safety deviation
from testing at the unvalidated knee, not an operational-default recommendation.
Each size has5s warm-up plus60s measurement; existing64KiB packet/TLS bridging
and8KiB carrier fragmentation were reused, with no new fragmentation layer.

| KiB/block | Window | RX Mbit/s | Drain Mbit/s | avg ms | p95 ms | p99 ms | Result |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 2 | 0.008192 | 0.008192 | 1979.459 | 2028.010 | 2054.252 | PASS |
| 4 | 2 | 0.032768 | 0.032770 | 1973.609 | 2022.034 | 2026.542 | PASS |
| 16 | 2 | 0.124518 | 0.125481 | 2065.041 | 2443.107 | 3689.364 | PASS |
| 32 | 2 | 0.257775 | 0.257943 | 1999.538 | 2037.239 | 3318.637 | PASS |
| 64 | 2 | 0.515550 | 0.515598 | 2002.076 | 2078.509 | 2475.919 | PASS |

At low window the similar≈2s RTT and roughly proportional byte rate indicate
window/block-release limitation, not a measured bytes/sec ceiling.64KiB reached
0.515550Mbit/s for60s, but its separate300s run failed; it is not a durable capacity.

## Knee / saturation / overload — scope of inference

- **Linear region:** window1→2 in the300s comparison approximately doubles useful
  throughput at unchanged≈2s mean RTT. The separate60s window2 run is slower.
- **Short-run knee:** window8. Highest window-sweep60s throughput1.815347Mbit/s,
  avg/p95/p99 RTT575.946/908.676/1276.105ms. It is also the lowest tested window
  reaching≥90% of the highest error-free60s rate across methods (1.992294Mbit/s).
  This point failed its long check and is **not** a recommended sustainable default.
- **Saturation-like window region:**16–64; useful RX1.39–1.78Mbit/s does not exceed8,
  while latency increases. First latency penalty without useful gain is16.
  This is a closed-loop/burst behavior, **not global physical saturation**:
  independent paced2 exceeds it with much smaller RTT.
- **Bufferbloat:** sampled carrier queue max3/2/50/186 frames for8/16/32/64;
  Android pub/sub ICE RTT avg321/1109/1399/1651ms, max703/2143/2788/3113ms.
  Window64 p95/p99 application RTT9186/9589ms approaches the unchanged10s bound.
  Application producer queue and SendContext timing do not explain seconds of RTT.
  Buffering exists in the carrier/network path; precise distribution is unmeasured.
- **First failed point:** window4/64KiB outstanding, but later higher short runs
  passed, so a universal first overload window is **not established**. First paced
  failure is4Mbit/s during warm-up. Long failures also occur at lower load without
  runaway local queues; integrity/reliability, not just congestion, limits conclusions.
- **Highest completed300s / lowest qualifying window:**0.130635Mbit/s,16KiB/window2;
  lowest tested window reaching≥90% of this300s rate is2. Its avg/p95/p99 are
  1999.765/2046.538/2128.154ms. This is a finite observed result, not a capacity bound
  or a claim that all loads up to it always work.

## Window reference / BDP

`window_bytes*8/observed_RTT` is only a reference, not a capacity prediction.
Important qualification: in a full closed-loop pipeline, Little's law
`outstanding≈throughput×RTT` also holds **after saturation**, because queue delay
increases RTT. Thus equality with this reference alone cannot prove that capacity
has not been reached. Throughput plateau + rising RTT and the independent paced
sweep are needed to distinguish the regimes.

| Window | Window/RTT reference Mbit/s | Measured RX Mbit/s |
| --- | --- | --- |
| 1 | 0.065660 | 0.065536 |
| 2 | 0.092392 | 0.089566 |
| 4 | — | 0.000000 |
| 8 | 1.820615 | 1.815347 |
| 16 | 1.410494 | 1.389363 |
| 32 | 1.802878 | 1.778210 |
| 64 | 1.578495 | 1.481114 |

For300s window2 the reference is0.131087Mbit/s versus measured0.130635Mbit/s.
Initial filling, measurement-end cutoff and drain explain finite-interval differences.

## Where does≈2s RTT come from?

At window1, A enqueue→SendContext begin averages0.016ms; SendContext itself0.282ms.
B application receive→echo enqueue is<0.001ms; echo SendContext averages0.296ms.
Android pub/sub selected-pair ICE RTT averages85ms, not2s. At paced2, application
RTT is318ms with ICE RTT97ms and A SendContext0.334ms. No2s sleep exists in the
application echo path. The original stop-and-wait producer waited for the delayed
echo; continuous production substantially changes media delivery and latency.

Most accepted points retain≈2s final drain even when mean active RTT is far lower;
32/64 windows retain≈4s drain. This is consistent with sparse/media-buffer release
and the existing2s keyframe keepalive cadence, but **not a causal proof** of which
component imposes delay. No pacing/codec parameter was changed to force a result.
Monotonic B/A clocks are independent; forward media time, reverse media time,
TLS decode→application delivery and actual carrier enqueue→RTP-write latency were
not individually measured. SendContext return is not a wire-send timestamp.

## Correctness, WebRTC evidence and resources

The17 successful performance points have zero unequal plaintext, missing confirmed
echoes, duplicate/reordered application blocks, timeouts and unexpected session exits.
Five failed points are separate: **35 sent-but-unconfirmed echoes,5 session closures,
4 explicitly classified TLS bad-record-MAC errors**, one earlier unclassified closure.
All five correlate with one A post-reorder RTP gap each; B has0 gaps in these runs.
Application duplicate/reorder/unequal-byte counters are0, but this **does not mean
zero wire corruption/loss**: authenticated-record rejection occurs before plaintext
is delivered. Bad MAC may follow loss/reordering of encrypted stream bytes; the
trace does not distinguish those from bit corruption. No invalid plaintext is accepted.

B records prove many unconfirmed echoes had already arrived there (all4 for window4,
all803 measurement blocks for long8). B records are appended after successful
echo submission, so a receive followed by failed SendContext may be absent. Do not
convert35 unconfirmed echoes or5 gap events into a forward packet-loss percentage.
No retransmission/recovery loop was added; within-point recovery counters remain0.
Fresh-session successes after failures are explicit recovery evidence, not retries.

Existing media counters retain SamplesWritten/RTPReceived/FramesReceived/BinaryFrames/
SequenceGaps. Selected Pion ICE pairs remain host/host UDP with no selected TURN.
Numeric Pion candidate-pair/transport/peer-connection reports are retained; this API
did not provide RTP encoder/decoder/jitter/packetsLost/NACK/PLI/FIR reports here.
availableOutgoingBitrate=0 is unavailable information, not zero capacity. ICE
retransmission counters must not be mistaken for RTP retransmission counts.
Non-nominated candidate reports and repeated signaling evidence in snapshots are
omitted from the sanitized file; original file hashes and full final evidence remain.

Performance Go heap samples peak13,619,656B; Java used heap observed≤5,306,128B,
app PSS observed≤277,034KiB across the test campaign. No OOM/ANR or unbounded growth
was observed in these finite windows;5s/10s polling is not an allocation profiler.
Higher-load long checks ended on integrity rejection, not a memory or log-size bound.

## Regression / lifecycle

- Final `f1a211a`: Go race×3 all packages PASS, including canonical Pion/Family
  byte matrices, cancellation, admission, bounds and replay; vet/modules PASS.
- FuzzDecode5s990350 executions; FuzzReassembler5s3275; PASS. No module changes.
- Python95 passed,2 existing dependency warnings. Container dependencies were
  checked against both control and identity lockfiles: zero version mismatches.
- Android clean build/6 JVM tests/lint PASS (0 errors,6 existing warnings).
- Physical ARM tests:8 CLI groups and5 Family groups PASS; ProductStore file-fixture
  test SKIP because its optional fixture variable was absent. Real authenticated
  runs separately exercise the Python-issued ProductStore profiles end-to-end.
- Physical explicit cancel, activity close, force-stop and remote exit PASS after
  exact echo; native process termination bounded. Recreation and20s background/
  foreground retained the same native child during final canonical regression.

One extra canonical observer attempt was **HARNESS ABORTED**, not a carrier result:
the temporary observer parsed a non-JSON ADB diagnostic before evidence existed,
then force-stopped the APK. Its own wait timed out; the remaining owned remote
directory was explicitly PID-checked/reaped/removed without forced kill. The final
canonical run uses the existing runner directly, without that observer dependency.
This is separate from all performance FAILs; none of those were retried to green.

Final canonical regression on clean `f1a211a`: **PASS**,370 exact checks,
TX=RX4,498,721B. Its5min phase has148 echoes/300.000377750s, one-way
0.064662105Mbit/s, aggregate0.129324210Mbit/s; avg/p50/p95/p99 RTT
2026.944350/2000.286041/2018.331405/3950.124947ms. No corruption, timeout or
unexpected disconnect. Android exit0/B exit0; remote teardown without forced kill.
This reproduces window1 behavior within normal phase variability, including a≈4s
tail. Sustained phases are time-based:370 rather than the earlier374 is not loss.
SHA256 of both running `/proc/<pid>/exe` matched the final local binaries above,
and both runtime metadata records identify `f1a211a`.
The normalized metrics were independently recomputed from raw block rows:
all22 point counts, sequences, interval bytes, RTT quantiles and outstanding bounds match.

## Cleanup / rollback / limits

Diagnostic APK uninstalled. All28 recorded Android native PIDs are absent; all29
recorded Amsterdam native PIDs are no longer running from owned test directories.
Amsterdam temporary directories0; Android native test directories0. Radios unchanged:
mobile_data=1/wifi_on=1; no radio changes were required. Existing operator room was
not deleted/reconfigured; own participants were closed. All own local diagnostic
APK/native/build outputs, disposable keys/certificates/DBs/profiles, pytest private
fixtures, raw private logs and temporary helpers under `/tmp/fc-perf1` were removed
after the sanitized export was verified. Preexisting SDK/NDK/Gradle/Go caches were
preserved. No own host runner remains. Sanitized evidence contains no room URL,
private key, certificate input or arbitrary stderr.

No production configuration, DB, keys, service, routes, public builds, signed
catalogs or invitation versions changed. Android beta51/code51, Linux0.2.11,
Windows0.2.15 remain the released versions. Debug APK code2 was built/installed
only for this test. No source push.

Rollback is diagnostic uninstall + owned-PID cleanup, not a production redeploy.
Source-only removal, if subsequently requested: revert `f1a211a`, `589096c`,
`3540cd2`, `7d60c59` newest-first. Existing canonical runtime at5dd8b49/starting477bbfa
remains the reference; the current default canonical path is unchanged.

Limitations: one physical device/network/room, fresh session per point, no confidence
interval or sustained plateau accepted, no synchronized one-way stage timing,
no protected sockets/TUN, no true unidirectional no-echo capacity claim. Payload
sweep used safety window2 rather than unvalidated knee8. Long16/64-window and
additional lower paced300s points are NOT RUN after repeated integrity rejection.
Unknown media-loss/reordering recovery prevents a durable capacity conclusion;
do not treat failed high rates as an acceptable price for throughput.

**STOP after this report.** 5N.4/TCP/DNS/TUN, codec redesign, FEC, congestion-control
replacement, bonding, production multiplexer/orchestrator and rollout were not started.
