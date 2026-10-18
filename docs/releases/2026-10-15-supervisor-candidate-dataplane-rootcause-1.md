# SUPERVISOR-CANDIDATE-DATAPLANE-ROOTCAUSE-1 = PARTIAL

**HARD_STOP = EVIDENCE_INSUFFICIENT_AT_EXACT_BOUNDARY. ROOT_CAUSE_PROVEN = NO.**

**FIRST_MISSING_BOUNDARY = EVIDENCE_INSUFFICIENT_AT_OWNER_DEDICATED_SESSION_READY.**

Это terminal bounded offline-разбор, не продолжение live acceptance.
SEED-SUPERVISOR-OWNER-ACCEPTANCE-3-FINAL остаётся **FAIL**: обычный браузерный
DNS/HTTPS не прошёл до WS1011; восстановление supervisor не проверялось.
Приписать отказ коду candidate, acceptance flag или DNS сейчас нельзя.

## Evidence authority и проверки

Первичный episode, неизменённый:
`/tmp/family-connect-isolated-_k54bo6a/artifacts/seed-supervisor-owner-acceptance-3-final/episode-90m/`.
Использованы REPORT.md и sealed файлы, а не восстановленная по памяти хронология.

| Проверка | Результат |
|---|---|
| Episode SHA256SUMS | 49/49 PASS |
| gateway-seed-supervisor-trigger-1 SHA256SUMS | 611/611 PASS |
| gateway-seed-supervisor-1 SHA256SUMS | 1,239/1,239 PASS |
| Baseline source inventory → сохранённый Git tree471d1d6 | 226/226 совпадают |
| Candidate → inherited baseline inventory | 221 unchanged; 5 existing files changed |
| Research84 APK и embedded ARM64 native | exact hashes PASS |
| Шесть рассматриваемых Android/native source files | равны base f5240994, не затронуты research84 delta |

Digest episode SHA256SUMS:
`b28f2851f1066b624cc389365b12b5a77b27530e03173f78b4750f58b61cc327`.
Digest исходного REPORT.md:
`279da0be4e71f99ef0e9112d33131f76fdce1dfc028d0fc43607350e8d696ba2`.
Digest first-connect-gateway.log:
`9a1b06562e2aa5de51ff632ca14201c9e49b2e9743dfc3da6129b4e3aa93c084`.
Digest trigger capsule SHA256SUMS:
`458f8bd02ca5eb8d05db799684794b167cec5aa4ec1371c83cfe8bc2238d3df4`.

Новые sanitized analysis receipts:
`/tmp/supervisor-candidate-dataplane-rootcause-1/`:
`input-verification.json`, `exact-differential.json`, `server-correlation.json`,
`baseline-buildinfo.txt`, `candidate-buildinfo.txt`, `existing-runtime-diff.patch`,
`result.json`, `REPORT.md`, `SHA256SUMS`.
Это анализ сохранённых данных, не helper, диагностический протокол или новый collector.
Private keys/profiles, raw cache, history, contacts, message contents не читались.

## PRODUCTION_EPISODE_TIMELINE

Все времена UTC,15.10.2026. Время snapshot не подменяет время пользовательского действия.

| Время | Сохранённое событие и предел утверждения |
|---|---|
| 06:51:23.600400 | deployed.json: exact candidate loaded/next; PID3516748, invocation3e6421a73c3e40b09addffa44a4f4dc0, NRestarts0 |
| 06:51:27.863431776 | control TARGET_AVAILABLE, generation1/ACTIVE; trigger не применён |
| 06:51:27.867155891 | postdeploy-NL.json: bootstrap_seed_ready |
| 06:53:38 / 06:53:39 | Owner provisioning challenge / ACK READY; это readiness material, не dedicated READY |
| 06:55:29.496346486 | ACTIVE; trace23 GATEWAY_SESSION ESTABLISHED для a0ae95da…95b47; owner VPN binding отсутствует |
| 06:55:30.326 / 06:55:30.886 | Тот же tag: lease offer/applied; не доказательство owner HTTPS |
| 06:55:43.785 | Android NetworkAgentInfo: создание full VPN network271/tun1; не exact timestamp нажатия CONNECT |
| 06:55:44 / 06:55:45 | Ещё один owner provisioning challenge / ACK READY |
| 06:55:50.481663024 | bootstrap_family_open без session tag / Support ID |
| 06:55:52.828867356 | bootstrap_family_auth без owner-VPN binding |
| 06:56:42 | owner-first-observation.txt: службы VPN/Connection/Chat присутствуют; broadcast result0 не содержит startup diagnostics |
| 06:57:49.498 | Последняя sampled CARRIER_ACTIVITY, sequence137, тот же неподтверждённый owner tag |
| 06:57:50.482608395 | bootstrap_exchange_rejected, challenge/context_deadline; затем exchange_failed |
| 07:01:00 / 07:01:02 | Owner provisioning challenge / ACK READY; не доказательство data-plane recovery |
| До 07:05:33 | https-before.xml: Chrome DNS_PROBE_FINISHED_NO_INTERNET; exact DNS invocation/error timestamp не записан |
| 07:05:33.232486 | failure-before-rollback.json: тот же candidate PID/invocation; D unchanged; trigger0; fatal/recovery receipts пусты |
| 07:05:36.325759 | rollback-result.json: exact baseline restored/active, PID3525336, invocation9860ce9589064656859d5a2f6bb32deb |
| 07:09:07 | owner-final.txt: VPN OFF observation; app PID26585/ChatDeliveryService ON; не timestamp перехода OFF |

Exact physical CONNECT timestamp **NOT_RECORDED**. Есть только факт одного CONNECT
в sealed report и точное время создания Android network. Exact VPN OFF transition
**NOT_RECORDED**, известен финальный OFF snapshot. Нельзя выдавать эти snapshots за
полную последовательность orchestrator/native events.

## CLIENT_STATE / DEDICATED_READY / TUN_STATE

Research84: `0.1.18-research84-provisioning-seam`, versionCode84, UID10283.
APK `fd3106170ceeb1e24dad6c8eacda4107b1ab09a6ee120ccf495d92d96841aa48`;
ARM64 native `cb3af31f62fdc1339df5f03374652ef6c62c4382ed10ef2d314bd6b610c989e2`.
Проверены сохранённые APK/native и source provenance, не owner device.

**Важное уточнение прежнего отчёта:** его фраза, что этот TUN появляется только
после native ready, не доказывается для automatic mode. В exact research84 source:

1. `AutomaticConnection.java:46` configure вызывает `owner.open` **до** open transport.
2. `AutomaticVpnOwner.java:21` open вызывает `replace(builder())`;
   `builder` на строке52 уже задаёт полный TUN:10.79.0.2/fd79:fc::2,
   default IPv4/IPv6 routes, DNS10.79.0.1, MTU1280. Это начальный блокирующий TUN.
3. `RestrictedTunnelEngine.java:85` ждёт native phase1. Только затем на строках90–95
   заменяет TUN и вызывает native attach. Увидеть такой же system VPN можно и раньше.
4. Native `main.go:177` выставляет phase1 после wholedevice.Open*; в
   `wholedevice/session.go:394` Mux создаётся до dedicated_data_ready.
   `main.go:192` повторно проверяет readiness, затем запускает packet.Start;
   phase2/vpn_packet_ready появляются лишь после успешного attach на строке215.
5. Orchestrator CONNECTED выставляется после успешного host.open,
   не при первом Android Builder.establish.

Все относительные пути здесь внутри
`state-client-build/field65-export16/whitelist-provisioning-block-seam-1/source/`;
Java-классы в `clients/android/app/src/main/java/com/familyconnect/app/`,
native main.go в `pilot/android-restricted/native/`, wholedevice в `carrier/`.

`owner-first-ui.txt` сохраняет resumed Activity и **NetworkAgentInfo VPN CONNECTED**,
а не текстовый app CONNECTED и не state-machine transition. `VALIDATED` тоже не
заменяет проверку dedicated data plane. TUN/network creation — **PROVEN**;
native attachment, phase1/phase2 и работа dedicated session — **NOT_PROVEN**.
Нельзя утверждать ни «dedicated READY достигнута», ни «она никогда не достигалась».

Readiness ACK READY revision5/minimum_crl27095 сохранены. Per-owner Family auth,
descriptor, dedicated READY event, client session tag, protect_ok/protect_denied,
native startup stages, lifecycle trace, terminal/first-failure и native cleanup
в episode не сохранены. Неуспешный diagnostic broadcast не восполняет эти данные.
System services/TUN OFF подтверждают внешнюю уборку, но не native cleanup receipt.

## PACKET_COUNTERS / DNS_PATH / TCP_PATH

| Поле/граница | Episode evidence |
|---|---|
| dns / tcp / tcp_active / tcp_peak | NOT_RECORDED, не0 |
| udp_denied / ipv6_denied | NOT_RECORDED, не0 |
| protect_ok / protect_denied | NOT_RECORDED, не0 |
| TUN packet capture / converter accepted or rejected | NOT_RECORDED |
| Native DNS probe event | NOT_RECORDED; есть только Chrome error snapshot |
| Owner Mux streams / DNS request IDs / OpenTCP IDs | NOT_RECORDED |
| Owner-correlated gateway DNS/OpenTCP | NOT_RECORDED |
| External resolver / NL dial result / socket bytes | NOT_RECORDED |
| DNS response / HTTPS response / write back to TUN | NOT_RECORDED |

Chrome error доказывает провал пользовательского traffic gate, но не локализует
DNS defect. Отсутствие per-request telemetry не доказывает отсутствие запросов.
В сохранённом gateway source DNS forwarding использует TCP к первому nameserver
из /etc/resolv.conf, если DNSUpstream не задан (`tcpforward/mux_dns.go:175`).
Состояние resolver/socket в NL для этого episode не записано; production файл
не читался. OpenTCP policy использует net.DefaultResolver для имён; ни её успех,
ни отказ в owner episode не установлен.

## SERVER_SESSION_CORRELATION

Полный сохранённый first-connect-gateway.log:120 JSON records,115 traces,
sequence23–137, ровно один tag:
`a0ae95da8b8db1a0be2cc659d6dd4bff96e0b78c1f87ed621ae702bae4395b47`.
Trace stages: GATEWAY_SESSION3, HEARTBEAT42, CARRIER_ACTIVITY70.
Нет начала sequence1–22, descriptor/room-creation records или terminal report.
Это ограниченный фрагмент, не непрерывный journal всей попытки до rollback.

Для **этого server tag**, не доказанно owner VPN, имеются ACTIVE, lease offer/applied,
Family Reliable flow и двусторонние carrier bytes. Sample появляется после
успешного `tcpforward.NewMux` в `roombroker/gateway.go:118`, поэтому для этой сессии
Mux и защищённая transport session действительно были созданы. Transport counters
не являются HTTP response counters: ACK/heartbeat/control тоже дают трафик.
Они намеренно не используются как owner E2E evidence.

Tag ACTIVE предшествует TUN creation на14.289s. Нет client tag, Support ID,
connection/incident ID либо descriptor digest, связывающего его с owner VPN.
Не присваивать его ни owner VPN, ни ChatDeliveryService по одному времени.
Последующие bootstrap_family_open/auth/rejected не содержат этого tag;
их нельзя склеивать с ACTIVE в единую доказанную owner session.

Process binding подтверждается deployed/postdeploy/failure snapshots:
candidate PID3516748, startticks275480135, invocation3e6421a73c3e40b09addffa44a4f4dc0,
NRestarts0. Seed generation1, room hash
`843252af4c80bfd3b52aa72f05660978265eeed98a02702f3f982679e4fe8970`;
D `3b38925badd9dfeca9d5c9f466dc048040677393683aa3e0d39db4c5058cbe74`.
Это gateway/seed correlation, не отсутствующий owner/dedicated binding.

## FIRST_MISSING_BOUNDARY

**EVIDENCE_INSUFFICIENT_AT_OWNER_DEDICATED_SESSION_READY** — единственная выбранная
граница. После доказанного создания системного TUN нет owner-bound подтверждения
успешного завершения dedicated startup, от которого зависит native packet attach.
Последующие capture/converter/Mux/request/dial/response границы тоже не доказаны,
но выбрать одну из них как установленное место поломки означало бы пропустить
неподтверждённый readiness prerequisite. Это не DEDICATED_SESSION_NOT_READY:
неполная запись не доказывает, что READY не была достигнута.

## BASELINE_CANDIDATE_DIFF

Exact working baseline binary:
`21f0a0fdc27b50c00ea922f0b716516e2422aedf1b3797369718f7d00070509a`.
Source provenance: a4087e000fdbe674b72ede3a6c8822445c87c654 + classifier delta
`7e7d408670a6ac6afa18e856beb8dcc0ca26a3b6f074e205d4dd25e62d78967b`;
preserved exact snapshot commit471d1d6. Это не текущий dirty main checkout.

Failed frozen candidate source134083d87773dacc038c9593afdaff0c57ea951d,
binary `53beb661cab014c32494fa8d7384f9565300311ef467e62ae9f8c20201e5138f`.
Source checkout чистый; executable buildinfo vcs.modified=false.

| Категория | Exact differential / вывод по source, не runtime acceptance |
|---|---|
| Seed supervisor | generation-local WithCancel; supervise оборачивает serveCarrier; только recoverable WS1011 включает recoverSeed; backoff/budget не изменены этой задачей |
| Acceptance trigger | root-local policy/controller + seed-only WS bridge; generation/process binding и one-shot security сохранены |
| Observability | bounded recovery/acceptance receipt queues, отдельные writers; не DNS/TCP telemetry |
| Startup/config | новый явный research flag; main присваивает acceptanceContext; обычные listen/duration/chat/rotate options сохранены |
| Carrier lifecycle | Session получает bridge pointer; после оригинального WS dial optional research boundary; без opt-in возвращается исходный socket |
| Dedicated ownership | roombroker файлы неизменны; lease context создаётся от context.Background(), не от seed generation |
| Packet/Mux lifecycle | wholedevice, tcpforward, familysession, reliablestream и roombroker inventory unchanged; newMux по-прежнему запускает run/writeLoop |
| Shutdown/context | StartSeedAcceptance возвращает WithValue(parent), не deadline-context controller; generation.close отменяет generation, не dedicated lease; глобальный Broker.Close остаётся service teardown |
| Resources | добавлены controller listener/writers и generation-owned bridge pumps; статический анализ не доказывает отсутствие всех runtime side effects |

Всего в cumulative diff22 files:5 изменённых существующих,17 добавленных
implementation/test files. Среди226 inherited carrier files221 byte-identical.
Нет source evidence, что patch не запускает packet pump, меняет Mux consumer,
прикрепляет dedicated plane к seed generation или отменяет общий service context
из controller expiry. Это **не** доказательство отсутствия regression.

Отдельный **build differential**, не скрытый под «только supervisor patch»:
оба Go1.26.1/linux-amd64; baseline CGO_ENABLED=1, candidate CGO_ENABLED=0,
candidate добавляет seedacceptance tag. Возможные resolver/build-environment effects
не проверены. DNS forwarding к literal resolver address сам использует TCP;
обнаруженный CGO delta не доказывает, что это причина browser DNS error.

## ACCEPTANCE_FLAG_EFFECT

Без flag StartSeedAcceptance возвращает исходный ctx/no-op.
С принятой policy возвращается WithValue(parent); отдельный controller deadline
не подменяет lifetime service. Только TelemostSeed добавляет seed boundary marker.
Dedicated connector не наследует этот marker через независимый lease context.

**Flag меняет no-fault seed signaling ещё до trigger:** создаётся in-memory WS bridge
с двумя forwarding pumps и обработчиками ping/pong. Поэтому trigger0 не означает
«flag ничего не менял». Причинное влияние этого изменения на owner data plane
**NOT_PROVEN**; candidate без flag в данном episode не запускался.
Policy истекала07:14:10, после07:05:36 rollback; expiry не совпадает с ранним отказом.
Сохранены TARGET_AVAILABLE/NOT_TRIGGERED и CLEANED/REMOVED, reader_observed_1011=false.

## ISOLATED_A_B_C_MATRIX

| Вариант / требуемый result | Exact bytes | Seed READY | Dedicated READY | DNS | HTTPS/OpenTCP + exact response | Cleanup |
|---|---|---|---|---|---|---|
| A BASELINE_DATA_PLANE | verified21f0a0fd…70509a | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | N/A, process not started |
| B CANDIDATE_NORMAL_CONFIG_DATA_PLANE | verified53beb661…5138f | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | N/A, process not started |
| C CANDIDATE_ACCEPTANCE_CONFIG_DATA_PLANE, trigger0 | те же verified bytes | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | N/A, process not started |

**Обязательная матрица не выполнена; это существенное ограничение PARTIAL.**
Существующий accepted local real-Pion stack (`trigger-1/REPRODUCE.md`, validate.py)
работает через пересобранный `sameroomfixture` overlay: меняет metadata routing,
WS TLS/dial hooks, добавляет fixture provider/clock. В exact frozen executable этих
hooks нет. Main создаёт NewTelemostRoomProvider с фиксированным production endpoint;
Telemost Auth также использует production default. Сохранённая fixture не является
готовым адаптером для запуска этих двух exact executables.

Запуск старого fixture test binary не является A/B/C exact binaries. Пересборка
candidate с hooks нарушает требуемую идентичность; создание нового adapter/helper
и live provider run выходят за bounded offline scope. Ни одна такая подмена не сделана.
Synthetic identities не создавались, так как соответствующий executable smoke не
запускался. Исторические source-overlay PASS не повышены до текущих DNS/HTTPS PASS.
WS1011 не выполнялся, включая isolated fault path: ordinary pre-trigger gate не PASS.

## ROOT_CAUSE / MINIMAL_CORRECTION / NEW_CANDIDATE

ROOT_CAUSE_PROVEN=NO. Ни CANDIDATE_CODE_REGRESSION, ни
ACCEPTANCE_STARTUP_CONFIG_REGRESSION, ни OWNER_OR_PRODUCTION_ENVIRONMENT_SPECIFIC
не установлены: нет необходимой A/B/C и owner-correlated native evidence.
Точная правка отчётности — отделить system TUN CONNECTED от dedicated READY;
это не product patch и не объявление новой root cause.

MINIMAL_CORRECTION=NOT_CREATED; patch gate CLOSED. Product source, Reliable
timeouts/retries, credentials, Android, Mux protocol не менялись. Нет новой версии,
build/install/publication/catalog/invitation changes, freeze или validation commit.
NEW_CANDIDATE=NOT_CREATED. Sequential DNS/HTTPS и recovery matrix NOT_RUN.
Нельзя объявить новый candidate принятым или продолжить owner acceptance.

Для пересмотра нужны уже сохранённые owner-bound native startup/descriptor/tag/READY
и packet receipts этого episode, а также accepted isolated exact-executable route.
Их отсутствие не даёт разрешения на новый owner export/instrumentation/CONNECT,
production deployment, helper framework или PKI task. Текущая задача завершена.

## PRODUCTION_UNCHANGED / rollout и rollback

В этой задаче PRODUCTION_DEPLOYMENT=0; PRODUCTION_RESTART=0; OWNER_CONNECT=0;
OWNER_INSTRUMENTATION=0; TRIGGER=0; CREDENTIAL_MUTATIONS=0; APK_INSTALL=0;
LIVE_PROVIDER_ACTIONS=0. SSH/ADB не запускались; baseline gateway и owner device
не затрагивались. Dirty main source и frozen capsules сохранены.

Исторические episode counters остаются deployments1/rollbacks1/manual CONNECTs1,
triggers0/credential mutations0/data clears0. Не смешивать их со счётчиками анализа.
Последний sealed rollback receipt07:05:36.325759 показывает restored baseline
21f0a0fd…70509a, active/running, original argv, без research flag/policy/control path.
Это не свежая live health-проверка. Никакой второй rollback не выполнялся и не нужен
для анализа. Новый rollout path закрыт; существующие frozen/rollback binaries
остались в trigger capsule build/ и rollback/, не заменены.

**Сохранённого evidence недостаточно на точной границе owner dedicated session READY;
production повтор не выполнялся.**
