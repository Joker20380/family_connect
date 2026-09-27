# 5N-REL-1 — ReliableStream перед Family TLS

## Checkpoint

**5N-REL-1 = PASS.** Reliable ordered delivery доказана deterministic faults,
реальными RTP gaps, отдельной controlled injection и physical300s run.
Starting commit `498818e`, worktree был чистым. Core + deterministic/TLS tests:
`ecc884c`. Live gap harness: `8896bcc`; bounded producer/Android observer fix:
`d14a92f`; bounded stale-replay observer `6759f7c`; clean TLS exhaustion regression
`bbcea5e`. Actual CLI/APK build d14a92f
(последующий6759f7c меняет только Python observer). Push не выполняется.
Production Android beta51/code51, Linux0.2.11,
Windows0.2.15, публичные assets/catalogs/invitation pages не меняются.

## Architecture / protocol

До: `application / Family Session → TLS1.3 → lossy VP8/RTP → Telemost`.
После: `application / Family Session → TLS1.3 → ReliableStream → VP8/RTP → Telemost`.
Одинаковый Go core используется Android PIE и Linux EU endpoint. TUN, native
DataChannel substitution, TCP/DNS/mux/orchestrator/FEC/multipath не добавлялись.
TLS/crypto, сертификаты, admission/revocation/revision/gateway pin не изменены.

Полный [wire format, ACK model, security boundary и bounds](../../carrier/reliablestream/README.md).
64-byte big-endian header: FRS1/version, type, reserved0, exact payload length,
128-bit source/destination epochs, uint64 DATA seq/cumulative ACK, uint32 SACK,
OPEN receive-window/max-payload. DATA/ACK/RESET + минимальный OPEN для обмена
свежими epochs. Никакого криптографического дублирования TLS; существующий
carrier CRC32 остаётся только diagnostic/framing protection.

Cumulative ACK означает следующий **не переданный вверх** seq. SACK bitmap
помечает buffered blocks, но не освобождает sender slots до cumulative progress.
При gap последующие blocks удерживаются; только contiguous bytes идут в TLS.
ACK refresh раз в RTO восстанавливает потерянный final ACK. Повторяются только
unacknowledged/non-SACKed blocks по собственному timeout, не всё окно.

Defaults: DATA16KiB, sender8, receiver16, RTO1s,8 retries, MaxAge20s. Конфигурация
в Go API (`OpenReliable`/`reliablestream.New`), не глубоко hardcoded. Hard limits:
DATA≤32KiB, windows≤32, frame≤32KiB+64B, retries≤32, MaxAge≤60s. Retained DATA
default≤393216B, hard≤2MiB. Header validated before clone; huge jumps/overflow
fail closed. Carrier send timeout≤2s, reset budget100ms,128 numeric events.
Carrier outgoing256 fragments/incoming16 messages и64KiB TLS bridge — отдельные
фиксированные bounds, не включаются в `BufferedBytes`.

Fresh epochs отвергают delayed addressed DATA/ACK/RESET предыдущей сессии.
OPEN не является authentication: hostile SFU может вызвать DoS/spoof ACK/reset,
но не authenticated plaintext. TLS остаётся security boundary. Close — abort,
не reliable FIN/drain. Lost RESET завершается peer work deadline/exhaustion.
No reconnect/replay. Все adapter workers/waiters закрываются и buffers очищаются.

## Unit / fault / security regression

Virtual-time tests: ordered, single/multiple missing, every-Nth, burst, reorder,
duplicate, delay, ACK loss, retransmit duplicate, prolonged gap, combined;
byte-for-byte каждый delivered prefix и полный1,638,717-byte stream. Sender8,
receiver16, memory bounds, selective-only retry, slow receiver/ACK refresh,
huge seq, malformed frame/config, stale epoch, RESET, retry exhaustion.
Adapter tests: sender backpressure/resume, cancellation during retry/stall,
remote reset, no leaked waiters, negotiated payload sizes. TLS fault matrix:
207 exact encrypted echoes (7 sizes,100×1KiB/16KiB), bidirectional drop/reorder/
duplicates. Replay tests сохраняют injection выше reliability для проверки TLS,
а не только transport duplicate suppression.

Final bbcea5e Go race×3 all packages, vet, modules PASS. Fuzz5s each: FRS frame533996,
engine538051, IPC576453, carrier reassembler2108 executions, PASS. Final harness
backpressure test passes race, including unchanged strict PERF-1 failure semantics.
Python153 selected auth/identity/control/fixture/harness tests PASS (90+63),
2 existing dependency warnings; control+identity lockfile version mismatches0.
Final Android build/6 JVM/lint PASS,0 lint errors/6 existing warnings.
Optional Go `TestProductStoreFixtures` SKIP without `FC_FAMILY_TEST_FIXTURES`,
as in the prior baseline. Python issuer tests and all authenticated live runs
separately exercise freshly issued ProductStore profiles end-to-end.
Physical ARM ReliableStream11 top-level groups, carrier7, CLI9 groups PASS;
final seven Family groups PASS
(canonical/cancellation, admission negatives, expiry/bounds, two raw TLS replay
tests, bidirectional fault matrix, clean exhaustion). Native live controlled gap/WS-close/PC-close
PASS. Full handshake-transcript replay on fresh real VP8 session PASS with6759f7c
observer: fresh B `family_auth accepted=false` observed **before cleanup**.
Full canonical APK regression **PASS**:500 exact echoes, TX=RX6,628,641B;
7 sizes/100×1KiB/100×16KiB/30s/5min. Last264×16KiB over300.438865250s:
goodput0.115174873Mbit/s, avg/p50/p95/p99 RTT
1137.950306/1073.779792/1560.206718/1667.842030ms. No accepted corruption,
timeout or unexpected close; naturally time-bounded phases explain the echo count.
Activity recreation and20s background/foreground preserve the same parent/child.
APK live wrong-family/revoked/unknown rejected, no exact application echo.
Explicit cancel observed2.140s, activity close2.160s, force-stop0.119s,
remote exit11.696s (polling includes unchanged10s application deadline): PASS.
Native WS/PC closure and context cancellation PASS. Independent ADB-observed
cellular loss terminal0.622589s, exit1/carrier closure, radios restored; explicitly
started fresh authenticated session subsequently echoed exactly and cancelled
in2.114s. No automatic reconnect. Wi-Fi handoff/deep Doze remain NOT TESTED.
Additional `TestReliableTLSExhaustion` drops all outgoing DATA after authentication,
requires retry-exhausted terminal cause, nil plaintext/no bad MAC at the peer,
and completion before the external test deadline. Local Family race×3 PASS.

## Failed attempt retained

`rate1` on8896bcc: warm-up, NOT an accepted60s measurement. Existing PERF-1
producer treated application-window8 saturation as `offered_load_outstanding_bound`:
7 sent/2 received,5 unconfirmed when harness aborted. Then Android rejected the
new `reliability_final` event (`OUTPUT_REJECTED`). No TLS bad-MAC/accepted corruption.
This is not hidden/retried-to-green runtime tuning: d14a92f changes only harness,
adds explicit `backpressure:true` (default false preserves PERF-1), and allowlists
the numeric final event. Configured offered rate becomes an upper bound;
actual TX/goodput are reported separately. Core/RTO/windows/carrier unchanged.

First live replay observer also **FAIL/incomplete proof**, not accepted security
evidence: native sender finished its old8s observation while fresh B correctly
ignored stale epochs below TLS. The old observer immediately entered cleanup;
its later SIGTERM-induced auth rejection cannot prove replay rejection.6759f7c
waits at most35s for the existing bounded refusal, without changing adapter/TLS
timeouts. `replay-observed` then PASS on unchanged binaries; both attempts retained.
Sandbox socket restrictions initially blocked local Pion/HTTP tests; normal
outside-sandbox race×3 passed without runtime changes.

First network-loss **observer FAIL** retained: SSH collection timed out while
mobile data was disabled, preventing the runner from refreshing its local A log.
After restoring radios, direct ADB evidence showed Android had already exited1
with `SESSION_CLOSED`/`carrier_closed`; that delayed read cannot establish the
requested20s observation bound. A second explicit fault uses independent ADB
polling rather than SSH progress, confirms0.622589s terminal, and restores radios
in finally. Both owned remote cleanups succeeded without forced kill. No transport
timeout/retry/security changes were made for this observer repair.

## Live path / long run / gap recovery

Physical Redmi Note9 Pro, Android12/arm64, ordinary cellular → Family TLS1.3 →
ReliableStream → real Telemost signaling/SFU VP8/RTP → Amsterdam
`186.246.45.246`, temporary nobody process → authenticated echo → Android.
Operator room supplied through private stdin, no URL in report/argv. Disposable
authority uses existing ProductStore flow in a new local DB, never production DB.

Both real running `/proc/<owned-pid>/exe` hashes matched local final artifacts
during the300s run, metadata `d14a92f`, dirty=false. Diagnostic code2/name
`5N.3-test-only` built/installed only, not public. Immutable public versions untouched.

| Final artifact | SHA256 |
| --- | --- |
| Linux CLI | `1879364c126a81260e080625594370df4ce53d270599d99cacb1c9f2794662a2` |
| Android PIE | `11f5b4a47d77fa5942b9dc9a3c95a577c739dd62927d94850fd2ffee459a0eeb` |
| Debug APK | `916ebfc6fc384af4830554229d021203b7ec486cf72ddaf492d1903283bc6582` |

Each point uses a fresh session,5s warm-up/drain before measurement, application
payload16KiB/window8, ReliableStream16KiB/sender8/receiver16. Offered means pacing
**upper bound**, not an assurance that2Mbit/s reaches the carrier. No pacing debt,
unbounded queue or retransmission tuning. Exact input config retained in evidence.

| Offered cap Mbit/s | Measured s | Echoes after drain | RX interval Mbit/s | Drain-normalized Mbit/s | avg/p50/p95/p99 RTT ms | Backpressure episodes |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 60 | 416/416 | 0.895659 | 0.890933 | 635.261/376.699/1498.016/2417.211 | 43 |
| 2 | 60 | 519/519 | 1.116297 | 1.114313 | 918.818/654.767/2096.569/3094.715 | 354 |
| 2 | **300** | **4315/4315** | **1.883505** | **1.883011** | **422.949/411.751/647.240/1180.171** | 413 |

All3 measurement points PASS reliability: corruption, missing confirmed application
bytes, application duplicates/reorder, timeout/disconnect counters0. TLS bad MAC0.
Long run requested300s completed; rate2 cap is the highest tested offered setting,
**not a proven sustainable2.000Mbit/s rate/ceiling**. Goodput is1.883505, not2.
No lower-rate tuning loop or PERF-2: loss recovery is the acceptance objective.
Maximum application outstanding8 throughout. Long actual TX1.885252267Mbit/s,
elapsed with drain300.357060198s, max RTT1393.130312ms. Long4315 echoes =70,696,960B in
each direction including drain; ciphertext counters additionally include warm-up,
TLS/framing/handshake. Expected close/reset only after successful drain.
Counts/monotonic sequences, interval bytes and mean/p50/p95/p99 of all3 performance
points independently recomputed from raw block rows; all match the reported metrics.

### Natural loss proof

During accepted60s points, real return RTP `SequenceGaps`:10 at cap1,15 at cap2.
Android ReliableStream gaps recovered12/12 and17/17 respectively; these are block
holes, not a1:1 count of lost RTP packets. Across these3 complete live sessions:
29/29 detected block gaps recovered,37 retransmissions (A5/B32), maximum observed
gap recovery1578.496093ms. Counters include warm-up; measurement errors are separate.
The300s session had no observed RTP/stream gap and0 retransmissions; it is **not**
used as evidence of recovery by itself.

Concrete natural example from cap2: return DATA seq24 absent; Android records
`gap_sack` at local adapter t=7080.832445ms/depth1, retains later DATA. Amsterdam
records retransmit seq24 at its local t=14902.071546ms (age1006.007703ms) and
16002.070104ms (age2106.006261ms). Android `recovered` t=8281.959789ms/depth7,
gap latency1201.127344ms. Monotonic origins differ between endpoints; do not
subtract those clocks to invent a one-way delay. SACK describes the missing hole;
RTO, not an immediate NACK fast-resend, schedules the retransmission.519 exact
echoes complete on that same authenticated TLS session, no TLS restart/bad MAC.

### Controlled fault

Test-only native `TestLiveReliableGap` drops one DATA after TLS admission; eight
16KiB encrypted echoes plus matching receiver gap/recovery seq and sender retry
are required by the harness. No production loss injector exists.
Controlled **PASS**: after successful Family admission Android intentionally drops
outgoing DATA seq2 once. Amsterdam detects `gap_sack` at t=7090.557398ms/depth1;
Android retransmits seq2 at its t=2700.135833ms/age1003.947708ms. Amsterdam recovers
at t=7965.536294ms/depth8, latency**874.978896ms**.8/8 exact16KiB encrypted echoes
complete on the same TLS session. Receiver1/1 detected gap recovered; total8
retransmissions (4 each direction),3 duplicate frames suppressed on each side.
The other retries reflect conservative fixed RTO/ACK timing, not additional
injected losses. Source/receiver proof is machine-checked by the Python harness.
This is an injected reliable-block omission, **not** a claimed natural RTP gap.

## Resource usage / correctness / limitations

| Resource / session-lifetime counters | Long Android | Long Amsterdam |
| --- | --- | --- |
| send-window high-water | 8 | 8 |
| receive-buffer high-water | 3 | 2 |
| max retained DATA bytes | 74050 | 82110 |
| sampled carrier outgoing fragments | 5 | 11 |
| retransmissions / retry bytes | 0 / 0 | 0 / 0 |
| Go sampled heap peak B | 11104240 | 12371600 |
| Go sampled heap-system peak B | 23625728 | 19759104 |
| RSS high-water KiB | 114380 | 30468 |
| Java used heap peak B | 5763112 | n/a |
| app PSS peak KiB | 199296 | n/a |

Across3 completed performance sessions maximum retained bytes98550, send8,
receive8, sampled carrier queue11. No observed unbounded growth, OOM/ANR.
The393216B default retained-DATA limit is deterministic, not inferred from sampled
heap. Long retransmission payload overhead0%; natural-loss short sessions resend
83003B (cap1) and180524B (cap2), excluding64B headers/carrier fragmentation.
Reset counters include expected final aborts; transport duplicates/reorder are
not application duplicate/reorder. DeliveredBytes counts ciphertext to TLS bridge,
not application goodput. Counters/samples are bounded, not an allocation profiler.

Это не TCP и не TCP replacement. Congestion control остаётся WebRTC, fixed RTO
не adaptive RTT, FEC/multipath отсутствуют. Throughput ceiling всё ещё может
потребовать отдельно разрешённый PERF-2. TUN/full VPN/restricted-mobile/production
readiness не доказаны. Один физический телефон/оператор/room, не fleet load test.

## Cleanup / rollback / remaining

**Cleanup PASS**: test APK uninstalled; all15 recorded Android native PIDs absent,
all22 recorded Amsterdam native PIDs no longer execute from owned directories.
Android native test directories0, Amsterdam temporary directories0. Every harness
cleanup completed without forced kill; process-death test intentionally force-stops
only the test APK. Radios mobile_data1/wifi_on1 restored to the initial state.
Local diagnostic APK/native/build outputs, disposable DB/keys/certificates/profiles,
pytest private fixtures, raw private logs and helpers under `/tmp/fc-rel1` removed.
Preexisting SDK/NDK/Gradle/Go caches preserved. No production service/DB/route,
public release/catalog/invitation version or signing material changed; no push.

Sanitized20-run evidence (including all3 incomplete/failed observer/harness attempts):
[`2026-09-27-webrtc-5n-rel1.sanitized.json`](2026-09-27-webrtc-5n-rel1.sanitized.json),
SHA256 `75648d8258cc0056ba77d20f2538a823e334784556c2be97e284a839114a50fc`.
Contains exact block rows, counters/events, admitted/rejected results, native test
summaries, running/artifact hashes and cleanup proof; excludes room URL, private
keys/certificates/profiles/DBs, payloads and arbitrary stderr. Original raw file
hashes retained before deletion. Documentation is committed separately from code.

Remaining limitations are not unfinished REL-1 work: exact sustainable capacity,
adaptive RTO/ACK optimization, restricted-network coverage, Wi-Fi handoff and
production integration require separate scope. No missing acceptance checks.

Rollback: завершить diagnostic participants, удалить test APK; deployment rollback
не нужен. Source rollback при отдельном запросе — revert `bbcea5e`, `6759f7c`,
`d14a92f`, `8896bcc`, `ecc884c`
в этом порядке; не force/reset исторических releases. После результата STOP:
5N-PERF-2 и5N.4 не начинать автоматически.
