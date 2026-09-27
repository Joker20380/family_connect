# WEBRTC-EU-3 / 5N.3 — authenticated Family session

## Working checkpoint / scope discrepancy

27.09.2026, исходный clean HEAD `29ba7986cf70a7eba961ae051ac396f902920920`,
runtime checkpoint `3f65346a02d621c0843975cbe84173d23ebba91f`.
Чужих tracked/untracked изменений при входе нет. 5N.1/5N.2 PASS принимаются
как установленные факты; повторять их с нуля не требуется.

**5N.3 не является ещё одним plaintext binary echo.** PLAN и
HOME_GATEWAY_DESIGN задают authenticated E2E Family session с existing
Device Identity/FAMILY, gateway pinning и отказом unknown/wrong-family/
revoked/expired/replayed proofs. В существующем carrier/CLI и diagnostic APK
нет Family admission или E2E encryption; WebRTC DTLS завершается у SFU.
Поэтому запуск прежнего harness сам по себе не может закрыть этот gate.
Устаревший вводный addendum HOME_GATEWAY_DESIGN ещё называет 5N.1 blocked;
актуальные gate-таблица, STATUS и отчёты 27.09 имеют приоритет.

Минимальный рассматриваемый путь: стандартная reviewed secure session над
opaque carrier; неизменные Telemost signaling, VP8 envelope, pacing/framing,
canonical matrix, 10s echo deadline и отсутствие retry. Нельзя считать
самодельный membership allowlist эквивалентом existing Family authority.
До реализации необходимы secure-session selection/reuse audit и проверяемая
binding/revocation boundary. Production provisioning/DB/config не изменяются.

Последний внешний CI: phase0 run `36268143806`, SHA `8e368585`, completed/failure
26.09; это предыдущий unrelated run, не проверка 5N.3. Production по STATUS:
Android beta51/code51, Linux0.2.11, Windows0.2.15; наличие сборки не означает
installation/distribution. Эта задача не выпускает production версию.

## Result

**PASS — isolated WEBRTC-EU-3 / 5N.3 gate закрыт на исправленном test stand.**
Physical Android Family E2E через настоящий Telemost VP8/Amsterdam: **374 exact
echoes**, sustained **302.000772958s**, corruption/timeout/unexpected disconnect/
reconnect **0** в принятом полном run. Valid admission, live unknown/wrong-family/
revoked/old-handshake rejection, native record replay, lifecycle и cellular
loss/explicit recovery проверены. Production не изменён.

[Sanitized raw evidence](2026-09-27-webrtc-eu3-live.sanitized.json) сохраняет RTT
samples, состояния endpoints, resources, negatives/faults **и два предыдущих FAIL**.
Transport не менялся между этими run; исправлена lifetime-зависимость test endpoint
от SSH observer. Точный источник завершения прежних parent sessions не установлен.

### Initial failed checkpoint (superseded, evidence retained)

Первый полный run clean runtime `5dd8b49` — **FAIL**:
150 exact checks (7 sizes +100×1KiB +43×16KiB), затем `ECHO_TIMEOUT` на следующем
16KiB echo. App/native interval325.198s; отдельные30s/5min phases не достигнуты.
Ноль обнаруженных byte-equality mismatches; это не успешная sustained acceptance.
На A normal deadline teardown: обе PC closed, Go goroutines3. B final summary
отсутствует: последний resource event13:34:15 UTC, A timeout13:34:44 UTC.
SSH observer не завершился в15s cleanup deadline. На этом checkpoint причина
не установлена; позднее найдено завершение B parent session **до** data timeout
(таблица ниже). Нельзя приписывать точный сигнал TLS/carrier или мобильной сети.
Amsterdam test PID и каталог затем отдельно проверены: отсутствуют;
kernel events для этого PID/comm не найдены. Общий host load в момент проверки
0.31/0.41/0.36 не устанавливает причину более раннего события.

Physical negative admission: wrong-family, revoked, unknown — REJECTED на B,
zero exact echoes на A, terminal code1; cleanup без forced kill. Первый FAIL
не стирается последующими проверками. Явный повтор той же canonical suite
сохранил runtime, credentials и deadlines; его FAIL также сохранён ниже.

Cleanup-only fix `b029cf1` принудительно reap-ит именно SSH observer при timeout
после remote cleanup и **всё равно выбрасывает ошибку**. 3 regression tests PASS.
Это не исправление data timeout и не изменение transport behavior.

### Observer isolation / additional evidence

Явный повтор тоже FAIL:153 exact checks (7+100+46), затем16KiB timeout,
app interval326.022s; тот же бинарник/credentials, без reconnect/retry.
Потеря B stdout повторилась у5min, final summary снова отсутствовала.

Read-only journal **только точных parent PID тестов**, не соседних сервисов:

| Attempt | runuser session lifetime | Parent session closed (UTC) | A ECHO_TIMEOUT (UTC) |
| --- | ---: | --- | --- |
| initial | 320.048125s | 13:34:35.638019 | 13:34:44.176435 |
| repeatability | 320.047695s | 13:51:29.484601 | 13:51:37.980794 |

Таким образом B parent session завершалась **до** timeout A, примерно за9s;
это не только отсутствие последних log lines. Точный OS signal/источник320s
termination из имеющегося journal не установлен. Go echo был привязан к SSH
stdio/session; закрытие stdout pipe может завершить Go через SIGPIPE, но конкретно
SIGPIPE в этих двух запусках не утверждается. Local SSH multiplexing выключен,
ServerAliveInterval0, ChannelTimeout none; config не менялся.

Минимальный test-only эксперимент `d2f7686` + atomic-exit fix `fc4bf29`:
`--independent-observer` запускает **тот же** nobody binary под owned temporary
supervisor; stdout/stderr идут в private bounded files. Короткий SSH только читает
evidence, не является lifetime/data dependency. Child/supervisor имеют25min cap /
явный PID-checked cleanup, private files удаляются. No service/install/config/route
change. Root process control, а не carrier reconnect; никакой ошибочный payload
не переотправляется. B exit code сохраняется атомарно; failures не превращаются в0.
Третий controlled run изолирует observer dependency; его результат ниже не должен
стирать два предыдущих FAIL или превращать предположение об OS signal в факт.

На этом stand **тот же clean5dd8b49** прошёл всю матрицу: Android app interval
760.526s/exit0; B final summary и controlled SIGTERM exit0 получены, forced kill
не понадобился. Runtime/VP8/профили/10s echo deadline/25min cap не менялись.
Именно этот run, а не старые timeout runs, является accepted measurement.
Это не автоматический retry-to-green и не игнорирование failed transactions.

Ещё две lifecycle-попытки остановились **до media**, на45s SSH upload17MiB
artifact.tar. B directories удалены, transport не стартовал. Test-only `e4b67f8`
сжимает staging tar и удаляет его даже при ошибке; upload deadline45s сохранён.
Последующие lifecycle завершены; это не изменение transport или measurement.

## Environment / exact path

Physical Redmi Note9 Pro, Android12/API31/arm64, ordinary cellular → shared Go
PIE diagnostic child → TLS1.3 Family test session → existing Telemost HTTP/WSS
signaling + real SFU VP8 media → Amsterdam186.246.45.246 Ubuntu26.04/amd64 `nobody`
temporary endpoint → TLS decrypt/authorize + synthetic binary echo → TLS/VP8/SFU
→ Android exact comparison. No DataChannel substitution, TUN или Internet egress.
ADB/SSH используются для orchestration/input/evidence, не вместо media data path.

Runtime `5dd8b49ab51547d463e7a9fc2dd1f7c66f629ae6`, clean detached build;
running executable SHA256 на обоих endpoints совпал с locally built:

- Android native `9aeab062c33158cbd919a3c69136dff068c11f067fbf16d08c0f4d56951e92fc`.
- Linux `1621769da6c86798c85a13a965fd75037a9d89d8f22720590f239c3029531da4`.
- Diagnostic APK `9fad2e4d528a4fc46ca0023341f2ce89bfbdf939dedaec4b884cc43b5bac0498`,
  versionName`5N.3-test-only`/code2, package`com.familyconnect.telemosttest`.
- Go1.27.1/Pion4.2.15, NDK28.2.13676358/API26, SDK35/AGP8.9.2,
  Gradle8.11.1/JDK17; Python control/identity pins include rns1.5.1/cryptography46.0.7.

Built and temporarily installed diagnostic artifact; never published/signed for
release, no update catalog/download/invitation changes. Production versions unchanged.
The extra live replay/closure harness is test-only commit `b69ea73`; it does not
change the running carrier/session binary.
Final test/harness commit `e4b67f8`; runtime всё ещё `5dd8b49`, не HEAD harness.

## Auth boundary

[Selection/reuse profile](../testing/webrtc-eu3-session-profile.md): standard Go
TLS1.3 mutual certificates, normal certificate verification plus Family admission,
versioned ALPN, fresh handshake, no resumption/0-RTT or plaintext fallback.
Identity remains existing RNS X25519+Ed25519/public reference; TLS signs with that
identity's Ed25519 seed, not the independent WG key. Signed certificate covers
full public identity (URI SAN), family/role/revision (named OU), expiry; client pins
authorized gateway reference. Signed current CRL and trusted local floors reject
revoked/stale grants; session operations are bounded by both peer leases/CRL expiry.

Disposable identities use **existing** DeviceIdentity and ProductStore
challenge/enroll/authorization/revoke in a new private temporary DB. No standalone
membership/password database, production DB or private identity/signing material
was accessed. Test certificate issuer/profile is experimental and not production
provisioning, secure-store migration, authority rollout or immediate offline revoke.
Existing enrollment proof replay is rejected; local TLS transcript/ciphertext replay,
wrong role/pin/issuer/family, revision floor, expired cert/lease, bounds/cancel pass.
This is not an independent security audit or a Telemost security/privacy guarantee.

## Measurement / initial failed run

Canonical sizes unchanged:1/32/256/1024/4096/16384/65536B; then100×1KiB,
100×16KiB,30s,5min. Original per-echo10s and overall25min deadlines unchanged.
TLS/test record headers are above opaque VP8, whose envelope/fragmentation/pacing/
signaling are unchanged. One application echo outstanding; no mux/concurrent streams
required until5N.5. Queue-depth/encode/decode timings are not instrumented.

Completed exact application payloads: TX/RX **894,241B each**. This is the confirmed
completed lower bound for TX, not an assertion that the timed-out request sent0B.
With one outstanding request, total application TX lies between894,241 and910,625B;
the legacy failure event does not record how much of that last write completed.
Carrier TLS bytes A TX919,272/RX919,137 are **not** useful plaintext throughput.
No successful 5min16KiB phase metric may be inferred from these totals.

For the complete100×1KiB phase (202.003436381s): avg2020.009098ms,
p50=1999.710989, p95=2009.017083, p99=2096.180937, min1910.810207,
max4007.264529ms;100 samples. Aggregate0.008110753Mbit/s; one-way0.004055377.
Raw successful-phase RTT samples are recorded, nearest-rank quantiles. RTTs of43
successful echoes in the interrupted phase were not emitted by the existing
failure path; do not fabricate full-run percentiles or extrapolate from100 samples.

Rate formula: **one-way=completed TX payload bytes×8/elapsed seconds/1e6**;
**aggregate=(completed TX+completed RX)×8/elapsed seconds/1e6**. Both exclude
TLS/test headers, RTP, signaling, keepalive and retransmission overhead. Stop-and-wait
useful rate depends on payload size/RTT; a1KiB phase is not a16KiB benchmark.

Normalization existing measurements only (not a new benchmark):5N.1 extended
76×16384B each way /303.989867439s → aggregate0.065538184/one-way0.032769092Mbit/s;
5N.2 extended150×16384B each way /300.006638271s →0.131069100/0.065534550Mbit/s.
Historical raw events contain mean/max, not individual samples: old p50/p95/p99
cannot be recovered. Throughput ceiling remains undetermined.

## Accepted correctness / sustained / RTT

Accepted Android start14:00:24.685959 UTC → suite complete14:13:05.146317 UTC;
B start14:00:20.601855 UTC → final summary14:13:08.186706 UTC.

| Phase | Payload | Completed exact echoes | Elapsed | Avg RTT ms | Aggregate Mbit/s |
| --- | ---: | ---: | ---: | ---: | ---: |
| Canonical sizes | 1/32/256/1024/4096/16384/65536B | 7 | per-size in JSON | per-size | per-size |
| Batch | 1KiB | 100 | 200.005764819s | 2000.032144 | 0.008191764 |
| Batch | 16KiB | 100 | 199.998612789s | 1999.881487 | 0.131072909 |
| Sustained30s | 16KiB | 16 | 31.982834415s | 1998.842131 | 0.131142348 |
| Sustained5min | 16KiB | 151 | **302.000772958s** | **1999.913819** | **0.131071665** |

Всего **374** completed echo transactions, useful plaintext **TX=RX4,564,257B**.
Все длины и bytes равны; sequence monotonic; observed duplication/reordering/
unexpected application record/corruption0. TLS integrity и application u64 sequence
отклоняют повторы/неожиданный порядок; ошибку не пропускает retry-loop. Негативные
тесты отдельно проверяют corrupt/replayed record, bad length/oversize/sequence.
Это не доказательство отсутствия редчайших ошибок за пределами измеренного окна.

5min raw metrics: **151 RTT samples**, useful TX2,473,984B/RX2,473,984B;
avg1999.913819ms; **p50 2000.067656 / p95 2013.326301 / p99 2044.018489ms**;
min1844.876510/max2148.041250ms. Samples сохранены, quantiles nearest-rank
`sorted[ceil(q*N)-1]`, без интерполяции; bytes/rates/quantiles независимо пересчитаны.
Продолжительность превышает300s, поскольку заканчивается текущий echo transaction.
Useful **one-way0.065535832Mbit/s**, **aggregate echo0.131071665Mbit/s** по формуле
выше. Это не wire bitrate; overhead не добавляется к полезным bytes.

Accepted run: echo timeout0, corruption0, unexpected disconnect0,
automatic reconnect/recovery0, RTP sequence gaps0 на A и B. Шифрованные carrier
bytes A TX4,585,392/RX4,585,291, B inverse; это **не** plaintext throughput.
A650 sent/649 received carrier messages и B inverse не обязаны равняться374:
TLS handshake/records и fragmentation разделяют application transactions.
Media A1569 sent samples/4839 received RTP; B1572/4838.

По76 native resource samples/endpoints сохранено. Final summary A goroutines7,
B4 (не утверждаем0); обе PC closed, процессы реально завершились. A heap7,709,768B,
maxRSS110,988KiB; B heap11,563,752B/maxRSS29,444KiB. MaxRSS — raw process high-water
metric, не текущий resident heap и не показатель очереди. One outstanding echo
задан harness; queue depth и encode/send/receive/decode timings **не снимались**.
Runtime не переделывался ради telemetry. Concurrent streams/mux относятся к5N.5.

## Auth / lifecycle / network matrix

| Check | Result | Evidence / boundary |
| --- | --- | --- |
| Clean start + valid existing FAMILY grant | PASS | Mutual TLS/admission A/B, полная canonical suite |
| Unknown identity / wrong family / revoked | PASS (rejected) | Physical APK→real SFU→B: accepted=false, zero application checks, exit1 each |
| Replayed old handshake/proof | PASS (rejected) | Physical native ELF captures successful TLS flights in memory; old session closed; fresh B rejects old flights over new real VP8 carrier, no accepted=true on B2 |
| Existing enrollment challenge replay | PASS (rejected) | Existing ProductStore; replay/unknown/revoked issuance tests |
| Expiry/revision/role/pin/issuer/record replay | PASS | Local race + physical native tests; не live CA distribution |
| Clean shutdown | PASS | A complete exit0; B controlled SIGTERM exit0; summaries, no forced kill |
| Context cancel / Disconnect + SIGTERM | PASS | Local ctx tests; APK cancelled=true/code1, operator observes exit2.130s after action |
| Activity finish | PASS | cancelled=true/code1, observed2.131s |
| Diagnostic app force-stop | PASS | After exact echo; action0.104s, owned PIDs later absent; не graceful signaling leave |
| Remote B exit | PASS | SIGTERM B, A bounded ECHO_TIMEOUT/code1, observed11.794s including polling/SSH; no reconnect |
| Signaling WebSocket close | PASS | Physical native after authenticated1KiB echo; terminal session/PCs in9ms |
| PeerConnection close | PASS | Physical native publisher.Close after authenticated echo; terminal in10ms |
| Real cellular loss | PASS | `svc data disable` after valid echo; SESSION_CLOSED/code1, observed2.003s, PCs closed |
| Cellular recovery | PASS | Original mobile_data=1 restored; **explicit fresh** authenticated session/exact echo, then controlled cancel |
| Wi-Fi↔mobile / address handoff | **NOT TESTED** | Wi-Fi enabled but not connected; no second network available |

Forced PC close is not a naturally observed ICE `failed` transition; failed-state
callback regression covered locally. App force-stop is not independent proof of
PDEATHSIG. Network-loss runner returns1 intentionally: interrupted suite **не** PASS.
Эти ожидаемые fault outcomes отделены от accepted-run counters. Transport никогда
не retries/reuses dead TLS state; explicit recovery count1, automatic reconnect0.
Device radios restored в finally и rechecked. Нет invented handoff PASS.

Native units: physical Android shell-launched PIE ELF,5 top-level tests/14 subcases,
включая canonical207+cancel; это не APK JVM tests. WS/PC/replay — physical native
injections на том же phone/carrier/session; full matrix, negatives и lifecycle —
isolated APK. Repeated independent starts/auth/echo/teardowns дополняют один полный
accepted13min run; это finite reproducibility evidence, не multi-hour SLA.

## Static / runtime validation

- Go `go test -race -count=3 -timeout=120s ./...`: PASS, включая local Pion
  canonical207 per repetition, Family admission/bounds/cancel/replay и metrics.
- `go vet ./...`, `go mod verify`: PASS; no module/version change.
- Existing `FuzzDecode`5s977,637 executions; `FuzzReassembler`5s147,653: PASS.
- Python с existing control + identity lockfiles: **91 passed**,2 dependency
  deprecation warnings. Known sandbox TestClient stall/socket restriction rerun
  outside sandbox; fixture interoperability checked.
- Clean detached Android assembleDebug, **6 JVM tests**, lint: PASS;0 errors,
  6 existing warnings. Runtime hashes matched actual running A/B executables.
- Windows UI/CI и full product rollout не запускались. Последний внешний phase0
  CI — прежний failed run выше; local validation не выдаётся за новый CI result.

## Normalized comparison

Все values — **aggregate echo useful TX+RX**, decimal Mbit/s, только5min phase.
Предыдущие values — normalization existing measurements, не новый benchmark.

| Gate | Platform | Sustained | Avg RTT | Useful throughput | Corruption | Disconnect |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 5N.1 | Linux | 303.989867s | 3999.806776ms | 0.065538184 Mbit/s | 0 | 0 |
| 5N.2 | Android physical | 300.006638s | 1999.844240ms | 0.131069100 Mbit/s | 0 | 0 |
| 5N.3 | Android physical + Family TLS | 302.000773s | 1999.913819ms | 0.131071665 Mbit/s | 0 | 0 |

One-way соответственно0.032769092/0.065534550/0.065535832Mbit/s. При stop-and-wait
16KiB и≈2s RTT useful aggregate≈0.131Mbit/s;1KiB даёт≈0.00819Mbit/s. Это связь
payload/RTT данного harness, **не архитектурный throughput ceiling**. Данных для
causal attribution2s latency недостаточно. Batching/pacing/framing не менялись;
performance investigation — отдельное последующее решение.

## Cleanup / rollback / distribution

Diagnostic APK code2 был built/temporarily installed, затем **uninstalled** вместе
с private room/profile/evidence; not published, not signed for production, no update
catalog/invitation/download changes. Production Android beta51/code51, Linux0.2.11,
Windows0.2.15 не менялись. Проверены24 known Android PIDs и32 remote child/parent
PIDs — отсутствуют; Android native test dirs и Amsterdam temporary test dirs0.
Radios mobile_data=1/wifi_on=1 сохранены, Wi-Fi not connected. Remote cleanup без
forced kill. Existing operator-owned room не создавалась заново и не удалялась/
перенастраивалась; собственные peers закрыты. Sensitive URLs не сохранены.

Local private fixture DB/keys/certs, staging archives, APK/native/test artifacts,
disposable build worktree и own temporary helpers удалены после сохранения
sanitized evidence, включая private fixtures в own pytest scratch directories.
Preexisting SDK/toolchains/caches5N.1/2 не удалены.
Rollback изолированного теста — stop/uninstall diagnostic APK + PID-checked cleanup
temporary B/profile, **не** production redeploy. Для нового воспроизведения собрать
runtime5dd8b49 и использовать final harness/новые disposable fixtures/independent
observer согласно Android runbook. Source и documentation commits разделены; no push.

## Limitations / decision

Feasibility VP8 carrier уже доказана5N.1/2; теперь подтверждён **Family authenticated
E2E synthetic binary exchange**, byte correctness, scoped admission и отказ replay/
unknown/wrong/revoked, sustained stability и bounded teardown/recovery на physical
Android→Amsterdam. PASS относится к isolated test profile, не production issuance,
device secure-store или automatic policy refresh.

Не доказаны: **TUN, full VPN routing**, TCP/DNS/Internet egress, multiplexing,
protected sockets/leak prevention, Device Core integration, production readiness,
restricted Krasnodar mobile5M, multi-hour reliability, deep Doze, Wi-Fi handoff,
other OEM/OS/ABI, **throughput ceiling**. TLS over lossy VP8 не создаёт reliability
или production mux; revocation — signed snapshot/lease, не instant offline revoke.
**Security/privacy guarantees Telemost как carrier этим тестом не доказаны**;
нет независимого crypto audit. Все application payload synthetic.

Два failed runs не приравниваются к accepted zero-error окну. Наблюдаемое320s
завершение прежних parent sessions остаётся harness caveat: sustained запускать с
independent observer, не persistent SSH stdio lifetime. Не менять production SSH
config. Performance остаётся baseline/unknown ceiling, не предмет этого gate.
**NEXT = отдельное решение о WEBRTC-EU-4 / 5N.4 (один TCP→HTTPS через EU).**
Он не начат; full VPN production-ready не объявляется.

## Stop boundary

Не начинать5N.4/TCP/DNS/TUN/Device Core, optimization или production rollout.
Room/tokens/identity private material не сохранять в отчёте, Git или stdout.
