# TELEMOST-STABILITY-1 — lease and actual continuation

11.10.2026 Brussels; live episode10.10.2026 22:24:55–22:37:22UTC.
**EXPECTED_EXPIRY / AUTOMATIC_SERVICE_CONTINUATION_OBSERVED.** Не общий PASS
стабильности: один эпизод, одна ожидаемая потеря при security lease, один новый
полный ответ после реального automatic open. Диагностическое покрытие частичное.

Bundle **B**: `state-client-build/field65-export16/telemost-stability-1-continuation/`.
Машинный итог `B/RESULT.json`, нормализованный trace/traffic `B/observation.json`.
Source `B/source`: сохранённый6f3772942f3f3e45aba9a309233ebe8b8a31bf14 плюс
прежний server observability patch; новый только локальный auth-boundary test.
Main APK research81-refresh/code81 **не изменён**:
`06513be88ac924e6412cf65865361b6c4369da7f7e4c80e90c3d91eab1fe543f`.
Gateway binary **не изменён**:
`c101065a92e3a10e5c018b09c982e56c0a0d954965bd914b15a00fa091cc54c7`.

Исторический failed exchange20:03 окончательно отделён:
**ROOT_CAUSE_UNKNOWN / CORRELATION_NOT_RETAINED; SEARCH_CLOSED**. Его holder
не восстанавливается новым успехом. Предыдущий admission-эпизод длился только120s
после READY, не содержал поведенческого исправления. Старые DATA exhaustion и
carrier closure не объявляются объяснёнными текущим lease-эпизодом.
Источники: прежний `telemost-admission-ownership-1/RESULT.json`, сохранённый source
report10.10, hashes `B/preservation/inputs.sha256`.

## AUTH_NEGATIVE_ASSERTIONS_CLASSIFICATION

**A после минимальной локальной проверки.** Сами старые receipts давали **C**:
`auth_test.go:86` вызывал Fatal по неожиданному diagnostic callback **раньше**
обязательного assertion о rejection. Совпадение с baseline этого не доказывало.

`TestNegativeAuthMandatoryRejectionBoundary`: unknown, wrong-family, revoked,
wrong-gateway, stale-crl, stale-revision — все возвращают error, no descriptor,
authenticated count0, provider calls0. Valid control: один authenticated handoff,
descriptor/provider call1. У всех отрицательных случаев callback `family_open/unknown`.
`OpenServer` возвращает ошибку Family open до authenticated exchange. Исходные
assertions не ослаблены/не пропущены. **Полный bootstrap suite остаётся FAIL.**

Отдельная открытая задача: [DIAG-AUTH-REJECTION-1](../testing/negative-auth-diagnostics-open.md).
Источники: `B/receipts/auth-boundary.log`, `auth-classification.json`,
`B/source/carrier/bootstrap/negative_boundary_test.go`, `bootstrap/auth_test.go:86`,
`bootstrap/protocol.go:205`; прежние local-authenticated/baseline-authenticated logs.

## STARTUP_AND_ADMISSION

Fresh installed APK/UID/signer проверены, loaded/next binary c101…cc54c7 совпал;
исходный invocation d1e195e9…c4c5 действительно продолжал работать. Credentials,
served Family chain, expected leaf, grants/revocation/floors и directory прошли
preflight. Renewal **не нужен и не выполнялся**. Настройки clocks не менялись.

Ownership collector был завершённым одноразовым512/15min; peer capture не включён.
Код не предоставляет hot re-arm. После подготовки выполнен **один явно разрешённый
restart того же restricted binary исключительно для включения существующего сбора**,
не для «чистого» admission. Старые unit/profile/directory/evidence сохранены; прежнее
in-memory состояние не используется для атрибуции. Новый invocation
`8577d558a3b943feb16f21cb27e344e8`, PID80782. AWG/TCP/API/mailbox не перезапущены.
После нового seed выполнен ordinary sync; приложение получает новую directory
через штатный authenticated refresh, без helper injection/cache clear:
`118130b9ac6774fec72ef6eb56ef30b27699fddc56ced6942d6327d29a318678`.
Этот fingerprint совпал с native startup обоих attempts.

Первоначальная цепочка:
- UI CONNECT22:24:55.135UTC, строго Telemost/NL;
- native attempt1 started22:24:56.960, duration24724ms;
- exchange `aba839a0f78abb97ca19bf3d2d19cfe61511911cca10c83a3bd3bf2a05ff8bc0`;
- holder/session tag `277206babab86637cca8b564756f948dd1039ae7677abb67f32a8e5762b8f256`;
- authenticated22:25:05.153 → grant05.155, same_identity=true → HELLO05.156;
- dedicated/client READY22:25:22.007. Блокирующего holder/wait не было.

Источники: `B/receipts/owner-entry.json`, `owner-immediate.json`, `runtime-entry.json`,
`preflight-entry-*.json`, `observation-loaded.json`, `preflight-armed-*.json`,
`directory-current.json`, `runtime-final.json` ownership seq1–13,
`B/private/diagnostic/connected-ring.json` (private; в отчёт не выгружен целиком).

## TIME_TO_FIRST_FULL_RESPONSE

CONNECT→READY **26.872s**, CONNECT→первый полный ответ **31.070s**.
Первый ответ22:25:26.205UTC, последний22:36:25.392UTC. Все17 успешных ответов:
HTTPS206 Range, Content-Length65536, hostname/TLS и полный body SHA256 проверены.
Это полные тела запрошенного Range, **не** полная загрузка APK/HTTP200.
Проверено **1,114,112 bytes = 1.0625MiB**. Всего18 запросов, один SocketException.

Сценарий: DNS/initial → пауза45s → два последовательных ответа → четыре
parallel streams → все streams закрыты в22:26:36.255 → новый after-series ответ
22:26:38.586 → редкие новые запросы по минутам. Нет HTTP retries/speedtest/drop.
Parallel responses завершились за5.160/5.916/8.285/8.284s. Helper ограничен32
запросами/2MiB и900s от CONNECT,720s после READY; main APK не собирался.
Изменён только workload существующего helper, не capture/recovery logic:
`B/helper-workload.patch`, `scenario.json`, `receipts/helper-signed.json`.

Полная таблица времени каждого ответа — `B/observation.json:response_records`.
Объединение интервалов успешных запросов без двойного счёта parallel = **56.261s**;
оно включает TCP/TLS/headers. Payload-only airtime отдельно не измерялось. Интервал
между первым/последним полными ответами659.187s не означает непрерывный трафик.
Источник: `B/receipts/diagnostic-result.json` request_complete events.

## UNEXPECTED_SESSION_LOSS

Наблюдение **720.095s после первоначального READY**. Неожиданного завершения
**до обязательного deadline не зарегистрировано**:
**NOT_REPRODUCED_IN_THIS_EPISODE** для непредвиденного обрыва.
Один client loss event и один неуспешный minute-10 запрос относятся к ожидаемому
lease termination ниже, не к доказанному новому DATA/провайдерному дефекту.
Helper outcome `LOSS_OBSERVED` не подменяется общим PASS.
Источники: `B/observation.json`, `receipts/diagnostic-result.json`.

## LEASE_EXPIRY_AND_CONTINUATION

`Broker.Challenge` создаёт600s context **при acquisition**, не при CONNECTED.
Unused descriptor deadline — отдельное ограничение, не active lifetime.
Фактический lease:22:25:05.155 → **22:35:05.155UTC**, около583.148s после UI READY.
`monitor` при deadline отмечает EXPIRED; worker завершает Run, Close и освобождает
свой setup. Family certificate/CRL expiry — отдельные security ceilings; текущие
материалы покрывали эпизод, срок не увеличивался ради испытания.

Server ownership: seq14 EXPIRED/lifetime_expired22:35:05.157; seq15 Run end;
seq16–18 Close begin/end/release22:35:05.167, present=false. Точный holder совпадает
с client tag. **EXPECTED_EXPIRY / AUTOMATIC_SERVICE_CONTINUATION_OBSERVED**:
продолжение через существующий реактивный recovery, не proactive lease renewal.
Источники: `B/receipts/ownership-first-failure.json`, `runtime-final.json`,
`B/source/carrier/roombroker/broker.go:144`, `broker.go:240`,
`carrier/familysession/session.go` Configuration/expiry.

## ACTUAL_AUTOMATIC_RECOVERY

Ручных CONNECT **1**, ручных reconnect **0**, automatic opens **1**, native attempts
**2**. Не только restoration_attempted:
-22:35:29.264 — orchestrator RESTORING/NETWORK;
-22:35:32.193 — новый native attempt2, duration20223ms;
-22:35:39.788 — новый authenticated exchange;
-22:35:39.790 — новый grant и HELLO;22:35:52.060 server ACTIVE;
-22:35:52.635 — restoration_succeeded, dedicated READY подтверждена.

Новый exchange `e7b96c19bb2ec2f67eded1a30d5dceeaea378478c72545bbce16e7072563b431`,
generation `1eac55810414a92fb8da62746762f5d88e97a3ce6d04451c355e64e22cf6b714`.
Его grant происходит после release первого holder; чужой cleanup/new holder conflict
не наблюдался. `RestrictedRecovery` разрешил NETWORK только по существующему
allowlisted exhaustion evidence; policy не расширялась на любой INTERNAL/AUTH.
Источники: `B/private/diagnostic/recovery-1.json`, `recovery-2.json`, `sample-65.json`,
`B/receipts/runtime-final.json` seq19–31; `RestrictedRecovery.java`,
`ConnectivityOrchestrator.java:80`, `AutomaticConnection.java:93` в saved source.

## NEW_TRAFFIC_AFTER_RECOVERY

**PROVEN:** minute-11 — новый socket/TLS request, начат22:36:22.084,
полный65536-byte ответ **22:36:25.392UTC**, duration3308ms. Это после нового native
open, нового server holder и восстановленного restricted/VPN state, которые
helper проверяет перед request. Старые TCP streams не заявляются сохранёнными.
Около80.237s от server deadline до нового полного ответа включают плановую паузу
до minute-11; это не измерение непрерывной недоступности или чистой recovery latency.
Источники: diagnostic-result request_complete:minute-11, native attempt2,
`B/testsrc/com/familyconnect/app/LateOwnerEpisode.java` request/probe.

## FIRST_CLOSE_ATTRIBUTION

**PROVEN в этом эпизоде: broker lifetime/context deadline.** Server immutable first
close — sequence492,22:35:05.156, CARRIER/CLOSED/**PARENT_DEADLINE**; first failure
sequence495,05.157, **BROKER_LIFETIME/lifetime_expired**, exact deadline05.155.
Это тот же tag, что acquisition/expired/release. Причинная связь подтверждается
context/lifecycle и последовательностью одного сервера, не соседством UTC.

Android first close только в22:35:24.376: RELIABLE_EXHAUSTION, DATA send_base1087,
send_next1091, receive_next1150, pending4, head_retries8, ACK base1087/mask0,
ACK age19347ms. Сервер к тому времени уже закрыл общий carrier и освободил setup.
**Android exhaustion не первопричина.** Последний server flow перед deadline:
send_base/send_next1150, receive_next1087, pending0/buffered0. Точная receiver-stage
последующих DATA1087–1090 не сохранена; не выводится из SACK/RTP соседства.
Cross-leg RTP sequence/timestamp не использованы как packet identity.

Собственные test streams на момент expiry уже закрыты (последний ответ22:34:24.770);
minute-10 начался только22:35:22.105 и завершился SocketException22:35:24.400.
Нельзя из этого утверждать отсутствие фоновых health/OS операций.
RU/NL NTPSynchronized=yes; независимой subsecond калибровки Android нет.
Elapsed/sequence внутри одного endpoint надёжнее межхостовых UTC дельт.

Источники: `B/receipts/peer-direct-observation.json` first.json seq492/495,
`ownership-first-failure.json`; `B/private/diagnostic/first-failure-ring.json`.
First ring сохранён до замены session, но persisted incident file **не совпал**
за существующие2s (`matched_file=false`); не заявляем его успешную копию.

**Ограничения сбора:** ownership36/512, contiguous, limited=false, stopped=true.
Streaming peer bridge остановился с STOP_TIMEOUT/exit255; последняя полученная
status устарела, второй requested tag не был выбран на сервере. Однократным bounded
чтением сохранён уже существовавший immutable first-close первого tag; второй
detailed peer trace отсутствует. Это не исправлялось новым collector/replay.
Peer first file collector_dropped0, но history_evicted456. У client generation1
trace_dropped328, delivery_dropped296, archive_dropped160: rolling metadata eviction,
не доказательство сетевого packet loss. First-close отдельные записи сохранены.
Bridge STOP_TIMEOUT/incident-file mismatch остаются открытыми diagnostic limitations.

## PROVEN_CORRECTION

**NONE.** Поведенческое нарушение этого пути не доказано. Существующий security
deadline соблюдён, existing recovery реально возобновил передачу. Main APK/gateway
binary, UI/Codec2/framing/RTO/retries/buffers/admission/TTL/trust не изменены.
Два подготовленных helper signing результата сохранены: первоначальный короткий
общий limit обнаружен до установки, исправлен только test budget; запущен единственный
окончательный helper. Пароль signer вводился только в локальном защищённом диалоге.

## CONTROL_RESULT

**NOT_RUN_NO_CORRECTION.** Диагностических эпизодов1, контрольных0. Нет повторов
неизменённого кода «до успеха». Наблюдение не закрывает глобальную TELEMOST-STABILITY-1,
не реатрибутирует исторические carrier/DATA incidents и не доказывает все сети.

## CLEANUP

TEST_STOP22:37:22.102 после720.095s от READY; test VPN выключен, helper удалён,
обычное приложение восстановлено одним launcher start, без CONNECT. Generation2
Run end/generic FAILED/Close/release в22:37:32.266 (seq32–36) **после TEST_STOP**,
не посчитаны неожиданным обрывом. Оба созданных holders освобождены.

Peer bridge STOP_TIMEOUT согласован через существующий stop-request; server status
stopped=true подтверждён. Точного оставшегося helper process не найдено. Ownership
дождался своего исходного15min deadline,36 events/limited=false. Spent capture и
stop marker защищены и сохранены: новый скрытый сбор не включается. Loaded/next
arguments/binary одинаковы, **cleanup restarts0**. Отдельный peer self-limit20min
не увеличен и не использован целиком: collector явно остановлен в22:38:58.506.

Финально22:41:50.165UTC: **VPN OFF; приложение ON; ChatDeliveryService ON**,
code81/APK/UID сохранены. Chat route DIRECT на READY и cleanup, service running;
фактические message/sync counters **UNKNOWN**, переписка не выгружалась.
AWG не переключался, code path его settings не записывал; server AWG/TCP/API,
mailbox listener, identity/admission/revocation bindings, issuer10 и publisher file
проверены сохранными. CRL floor растёт штатно. Побайтовая проверка всех Android
private settings/AWG ciphertext не выполнялась, E2E AWG не тестировался.
Локальные synthetic auth fixtures удалены, production identities/history не удалялись.

Источники: `B/receipts/test-stop.json`, `runtime-final.json`, `security-entry.json`,
`security-final.json`, `peer-stop-reconciliation.json`, `owner-closeout.json`,
`helper-removed.json`, `background-final.json`, `local-cleanup.json`.

Runtime paths: `friends-restricted/stability-continuation-20261011/`, override
`99-zz-stability-continuation.conf`; прежний unit/profile/evidence сохранены там
защищённо. При отдельно необходимом rollback убрать только этот override и вернуть
сохранённые arguments при согласованной активации; **не** откатывать profiles/CRL/floors.
Сейчас extra restart/rollback не выполняется. Prior UI rollback draft не применён,
его hash и прежние input artifacts проверены. Публичный релиз/download links,
отправка APK тестеру, Краснодарский FIELD, UI и аудио не изменялись.
