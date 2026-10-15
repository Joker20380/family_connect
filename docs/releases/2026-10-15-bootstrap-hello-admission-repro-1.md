# BOOTSTRAP-HELLO-ADMISSION-REPRO-1 — 2026-10-15

## RESULT

**SOURCE_CHARACTERIZATION: PASS. SOURCE_MECHANISM: REPRODUCED.**
**APP_PATH_COMPATIBILITY: COMPATIBLE, conditional chat-first ownership conflict.**
**HISTORICAL_CAUSAL_BINDING: NOT_PROVEN; ROOT_CAUSE_PROVEN=NO.**
**PRODUCTION_UNCHANGED=YES. Not FROZEN_BINARY_ACCEPTED.**

Настоящий Broker удерживает новую bootstrap-попытку перед HELLO, пока ACTIVE
holder той же identity не завершит cleanup. Истечение контекста новой попытки
не вытесняет holder. Реальный Family/TLS receive воспроизводит
`FAILED / HELLO_RECEIVE / UNKNOWN / complete=true` при deadline и закрытии pipe.
Baseline и frozen candidate дают одинаковый механизм; это **не** доказательство
supervisor regression. Android caller source допускает конфликт, но не доказывает,
что фоновый чат действительно имел сессию в C1/I1.

Исходная точка review: `2843b88252728902b23ca62d8df8c25914cdc5c8`.
[Предыдущий owner report](2026-10-15-owner-support-export-and-triage-1.md) остаётся
источником исторических фактов: C1/I1 установлен; startup HELLO_RECEIVE/UNKNOWN;
descriptor, dedicated/native packet startup не достигнуты; S1 не привязана к owner
VPN. Новый export, поиск исторических файлов, seal audit и live episode не проводились.

## Исходники и границы компиляции

| Input | Фактически использовано |
| --- | --- |
| Server baseline | Опубликованный `research/supervisor-20261015/baseline/carrier`, preserved snapshot `471d1d62e1385a9ffc5ff6a16a5a7e9fe043fae2`; provenance base `a4087e000fdbe674b72ede3a6c8822445c87c654` + сохранённый delta |
| Server candidate | Опубликованный `research/supervisor-20261015/frozen-candidate/carrier`, source `134083d87773dacc038c9593afdaff0c57ea951d` |
| Client interpretation | Retained `whitelist-provisioning-block-seam-1/source`, research84 base `f5240994869826c6a28f59e58e38256c688cf6eb`, delta SHA256 `d7907697d71f119c21bced533f08abae06ae33ef9159c5fd9bd54cf031a481e7` |
| Installed-client binding reused | Recorded native SHA256 `cb3af31f62fdc1339df5f03374652ef6c62c4382ed10ef2d314bd6b610c989e2`; ранее установленное соответствие research84 не переаудировалось |
| Actual executables | Четыре новые локальные `bootstrap.test`: baseline/candidate × normal/race, Go 1.26.1 linux/amd64, CGO_ENABLED=1, одинаковый `seedacceptance` build tag; только изолированные копии + два test files |

[Source bindings](../../research/bootstrap-hello-admission-20261015/source-bindings.json)
содержит 32 узких сравнения с exact retained research84. Недостающие 11 небольших
файлов опубликованы byte-identical в новом `research84-source/`; старые snapshots
не редактировались. Сверены непосредственные Android/native callers, bootstrap
protocol, broker ownership/wait, Family receive/bridge, startupdiag и lease path.

**Client не объявлен exact по названию candidate.** Хеши исполняемого client slice
`bootstrap/protocol.go`, всего выбранного `familysession`, `reliablestream`,
`startupdiag` совпали с retained research84; выбранный `roombroker` тоже совпал.
Полный client tree не подменяется server tree: `bootstrap/carrier.go`, `seed.go`,
`seed_overlap.go` различаются; candidate имеет дополнительные supervisor/acceptance
files. Первые два exact research84 файла дополнительно опубликованы. Эти server
seed/observation/overlap paths скомпилированы, но не исполняются данным harness:
вход начинается на локальном packet endpoint и Family/TLS, до реального Exchange.
Это **не** запуск Android client или seed supervisor.

[Compiled source manifest](../../research/bootstrap-hello-admission-20261015/results/compiled-source-manifest.json)
фиксирует 132 выбранных source/test entries пяти пакетов, включая несовпадения и
добавленные тесты. Это не полный seal/dependency audit. Research84 native build
metadata содержит `build_tags=[]`; read-only `go version -m` retained native
показывает Go 1.26.1, android/arm64, c-shared, без `-tags`. Поэтому
`fc_messenger_lab`/`fc_messenger_owner` overrides не являются установленным caller
path; применяется `chat.go` с `openChatSession = wholedevice.OpenProvisioned`.

## SOURCE_MECHANISM и BASELINE / CANDIDATE MATRIX

На каждом server input: 1 normal + 3 race suite executions; каждый сценарий A–D
выполнен 4 раза. **32 admission cases + 304 classification cases = 336 PASS.**
Race detector не сообщил гонок. B — ожидаемый отрицательный исход, не ошибка suite.

| Case | Baseline | Candidate | Наблюдаемая граница |
| --- | --- | --- | --- |
| A: holder отсутствует | 4/4 PASS | 4/4 PASS | grant, HELLO send=1/receive=1, полный REQUEST_TRANSPORT/descriptor/BYE exchange; wait отсутствует |
| B: ACTIVE same identity, cleanup не разрешён | 4/4 expected-negative PASS | 4/4 expected-negative PASS | busy → wait ACTIVE → wait_end context_deadline; HELLO send=0/receive=0; server context.DeadlineExceeded; client FAILED/HELLO_RECEIVE/UNKNOWN/complete=true |
| C: тот же holder штатно освобождён вовремя | 4/4 PASS | 4/4 PASS | wait ACTIVE → Cancel → gateway.Close entered, всё ещё нет HELLO/release → разрешён cleanup → slot removal/release → новый grant → HELLO send=1/receive=1 |
| D: ACTIVE другой identity, capacity свободна | 4/4 PASS | 4/4 PASS | новый grant/HELLO без wait; чужой holder не блокирует новую identity |

ACTIVE создан только через настоящий Challenge → Create → Claim → gateway Run
`active()` callback; состояние подтверждено ownership event/channel, не sleep и
не подстановкой map. Existing packet `pair()` переносит реальный reliable stream
и TLS 1.3 с одноразовыми certs; A/B/C используют настоящий SessionAuthorizer.
D использует вторую синтетическую identity для старого holder; новая авторизуется
тем же реальным Family/TLS путём. Provider и dedicated gateway заменены fixtures
на штатных интерфейсах, не изменённой логикой Broker/Exchange.

В B старый holder продолжает Run; очередь cleanup заблокирована тестовым gate и
вообще не запускается до teardown. После истечения новой попытки проверены
`device_busy`, сохранение ACTIVE/present и отсутствие старого gateway.Close.
В C отдельно доказано, что одного Cancel/входа в Close недостаточно: до возврата
Close нет release и HELLO. Проверяется строгий порядок release < grant < hello.
Это различает ожидаемое владение ACTIVE от незавершённого terminal cleanup.

Новый parent context B ограничен 200ms; остальные admission parents — 8s.
Production `ExchangeTimeout=120s`, retry budget, DefaultLimits (10min lifetime,
32 outstanding), single-holder policy и cleanup semantics **не изменены**.
200ms проверяет причинный механизм ожидания, а не реальное распределение latency
или 120-секундный Android acceptance.

### Непосредственные source references

- [protocol.go:58](../../research/supervisor-20261015/baseline/carrier/bootstrap/protocol.go#L58):
  Exchange ставит deadline, вызывает ChallengeAfterCleanup до отправки HELLO.
- [broker.go:171](../../research/supervisor-20261015/baseline/carrier/roombroker/broker.go#L171):
  device_busy той же identity и ACTIVE/started terminal holder ведут в ожидание
  `pending.done` с reauthorization; waiter не отменяет holder.
- [broker.go:482](../../research/supervisor-20261015/baseline/carrier/roombroker/broker.go#L482):
  finish удаляет slot и закрывает done после возврата gateway cleanup.
- [control.go:79](../../research/supervisor-20261015/baseline/carrier/roombroker/control.go#L79):
  Identity = gateway credentials Family + peer certificate SerialNumber Device +
  Ed25519 PublicKey, не имя caller и не отдельная messenger identity.
- [protocol.go:137](../../research/supervisor-20261015/baseline/carrier/bootstrap/protocol.go#L137):
  requestTransport фиксирует первую Recv-ошибку именно на HELLO_RECEIVE.

## APP_PATH_COMPATIBILITY — exact research84

**Два независимых владельца потенциального restricted transport:** VPN native
`current`/`ownerMu` и chat native `chatCurrent`/`chatMu` с chat consumers/refcount.
UI/background chat разделяют ChatRuntime/ChatCarrier, а не открывают сессию на
каждое UI/service действие. Это локальная координация чата, не общий VPN/chat owner.

1. [RestrictedTunnelEngine.java:67](../../research/supervisor-20261015/research84/clients/android/app/src/main/java/com/familyconnect/app/RestrictedTunnelEngine.java#L67)
   загружает FriendsIdentityVault, использует restricted delivery и первые 64 bytes
   identity material, затем NativeRestricted.beginReady. Legacy begin/open/cache
   также проходит через единственный VPN `current`, не создаёт отдельного chat owner.
2. [ChatCarrier.java:21](../../research/bootstrap-hello-admission-20261015/research84-source/clients/android/app/src/main/java/com/familyconnect/app/ChatCarrier.java#L21)
   использует тот же FriendsIdentityVault, RestrictedVault/RestrictedCache,
   NativeRestricted.validateDelivery и первые 64 bytes, затем chatAcquire.
   [DeliveryMaterial:205](../../research/supervisor-20261015/baseline/carrier/wholedevice/provisioning.go#L205)
   проверяет delivery/certificate identity и строит credentials из того же ключа.
   При той же family/device/key и том же обслуживающем Broker это **одна broker
   Identity**. Отдельного namespace/broker «для чата» в этих callers нет. Смена
   family/key/gateway либо другой Broker не удовлетворяет этой предпосылке.
3. [chat.go:82](../../research/bootstrap-hello-admission-20261015/research84-source/pilot/android-restricted/native/chat.go#L82)
   переиспользует живой chatCurrent. Если его нет, смотрит VPN current: готовая
   неfailed session с совпадающим profileHash заимствуется (`borrowed=true`).
   **VPN-first ready — конкретный контраргумент против неизбежного конфликта:**
   второй независимый restricted session здесь не нужен. In-progress VPN без
   готовой session не удовлетворяет этому условию.
4. **Обратного handoff нет:** [main.go:108](../../research/supervisor-20261015/research84/pilot/android-restricted/native/main.go#L108)
   при CONNECT проверяет лишь VPN current и начинает wholedevice.OpenProvisioned;
   chatCurrent не проверяется, не заимствуется и не освобождается. В проверенном
   Java/native CONNECT path нет ChatRuntime.stop/chatRelease. Поэтому chat-first
   established session + CONNECT допускают два caller attempts одной identity.
5. Старый чат должен освобождаться его владельцем: ChatCarrier.close → chatRelease
   → refs=0 → отмена owned chat context → session.Close. При borrowed-сессии чат
   не владеет закрытием VPN. На сервере Run должен закончиться, Close завершиться,
   затем finish удаляет slot; только тогда waiter получает новый challenge.
   CONNECT сам эту последовательность для независимого чата не инициирует.
6. [chat.go:89](../../research/bootstrap-hello-admission-20261015/research84-source/pilot/android-restricted/native/chat.go#L89)
   ограничивает lifetime delivery.ExpiresAt, а 30s timer ограничивает **открытие**
   и останавливается после него. Успешный chat с refs>0 может жить дольше новой
   120s попытки, если security/delivery budget достаточен. Default broker lifetime
   10min уже больше 120s; [wholedevice/session.go:414](../../research/supervisor-20261015/research84/carrier/wholedevice/session.go#L414)
   запускает MaintainLease. Продление ограничено authorization/security deadline,
   не является бессрочным. Renewal source прочитан, live renewal не запускался.

**ChatDeliveryService сам по себе ничего не доказывает.** Его onCreate запускает
ChatRuntime, но [FriendsAccessAndroid.java:46](../../research/bootstrap-hello-admission-20261015/research84-source/clients/android/app/src/main/java/com/familyconnect/app/FriendsAccessAndroid.java#L46)
сначала пробует direct HTTPS, только IOException без SSL trust failure ведёт в
chatCarrier.request. Другой вход — ChatCarrier.openMailbox, который также acquire.
Наличие сервиса/конфигурации не доказывает факт acquire, ACTIVE или identity binding.
Java lifecycle/JNI не исполнялись в этих тестах; caller compatibility — source
finding, не подтверждённое состояние owner Android. S1 не назначается ни чату,
ни VPN.

## ACTUAL_ERROR_CLASSIFICATION

Отдельный тест проходит **реальный familysession.Recv → requestTransport →
startupdiag.Failure/Complete**. Это не передача выбранной ошибки classifier.
До cancel/close наблюдается фактический blocked Family/TLS read. Observer после
Recv записывает безопасные type/Is/Timeout/context facts до классификации.

| Scenario / actual Recv variant | Baseline count | Candidate count | startup result |
| --- | ---: | ---: | --- |
| HELLO wait deadline: `*net.OpError`, Is(os.ErrDeadlineExceeded)=true, Timeout()=true | 36 | 42 | FAILED / HELLO_RECEIVE / UNKNOWN / complete=true |
| Тот же deadline: `*errors.errorString`, Is(io.ErrClosedPipe)=true | 12 | 6 | FAILED / HELLO_RECEIVE / UNKNOWN / complete=true |
| Обычный cancel уже заблокированного read: `*errors.errorString`, closed pipe | 48 | 48 | FAILED / HELLO_RECEIVE / UNKNOWN / complete=true |
| Peer Session.Close при живом local ctx: `*errors.errorString`, closed pipe | 48 | 48 | FAILED / HELLO_RECEIVE / UNKNOWN / complete=true |
| Неверный HELLO; Recv успешно получает frame | 4 | 4 | FAILED / HELLO_RECEIVE / PROTOCOL_REJECTED / complete=true |
| Успешный HELLO и оставшийся exchange | 4 | 4 | SUCCEEDED / cause NONE / complete=true |

Для всех фактических deadline/cancel/peer-close Recv errors:
`errors.Is(err, context.DeadlineExceeded)=false`,
`errors.Is(err, context.Canceled)=false`, `Is(io.EOF)=false`,
`Is(io.ErrUnexpectedEOF)=false`. У net.OpError closed_pipe=false; у closed pipe
os_deadline=false и Timeout interface отсутствует (не «timeout returned false»).

В точке наблюдения deadline: ctx.Err и context.Cause имеют тип
`context.deadlineExceededError`, соответствующие Is(deadline)=true; cancel:
оба `*errors.errorString`, Is(canceled)=true; peer-close: оба nil. В данном конечном
наборе не встретился вариант os deadline с ещё nil ctx.Err; это не гарантия
невозможности такого interleaving. Все реально встретившиеся варианты сохранены,
соотношение 36/12 против 42/6 не трактуется как regression или probability estimate.

Возвращаемая requestTransport ошибка в трёх error scenarios —
`*startupdiag.primaryError`: raw cause сохранён рядом с legacy
`bootstrap_protocol_rejected`, однако первая startup failure уже записана UNKNOWN.
Для invalid HELLO возвращается `roombroker.Code`, для success nil.
Полные безопасные boolean/type/context facts обоих наблюдений и snapshot каждого
из 304 случаев: [observations.jsonl](../../research/bootstrap-hello-admission-20261015/results/observations.jsonl).
Плюс все 8 B admission outcomes получили тот же HELLO_RECEIVE/UNKNOWN результат
(7 os-deadline errors, 1 closed pipe); их counts не включены в таблицу отдельного теста.

Почему это возможно: [Session.Recv:321](../../research/supervisor-20261015/baseline/carrier/familysession/session.go#L321)
назначает read deadline, регистрирует context cleanup и возвращает io.ReadFull
error без нормализации. [bridge:180](../../research/supervisor-20261015/baseline/carrier/familysession/session.go#L180)
закрывает обе стороны net.Pipe при остановке. [causeCode:47](../../research/supervisor-20261015/baseline/carrier/startupdiag/enabled.go#L47)
знает context deadline/cancel и EOF, но не os.ErrDeadlineExceeded/ErrClosedPipe;
context в этот classifier не передаётся. Неизвестная raw error фиксируется первой
и не заменяется поздним Complete. Peer close в этом fixture не эквивалентен
прямому io.EOF, несмотря на существующий EOF case classifier.

## Команды, результаты и cleanup

```sh
python3 research/bootstrap-hello-admission-20261015/run.py \
  --go /mnt/data/PycharmProjects/family_connect/state-client-build/field65-export16/diag-source-freeze-1/resume-tools/go/bin/go \
  --work /tmp/fc-bootstrap-hello-admission-repro-1/matrix-final --race-count 3
```

[Runner и test sources](../../research/bootstrap-hello-admission-20261015/README.md),
[build metadata](../../research/bootstrap-hello-admission-20261015/results/build-metadata.json),
[all classification counts](../../research/bootstrap-hello-admission-20261015/results/classification-counts.json).
Runner использует offline module cache, отдельные копии и свежий GOCACHE; без
скачивания зависимостей, внешних listeners или внешнего provider. Test flags:
`-test.run=^TestRepro -test.v -test.failfast -test.timeout=90s -test.count=1/3`.
Build timeout 240s, subprocess test timeout 100s. Все четыре build/run exit=0.
Предварительные baseline admission/classification прогоны тоже PASS; после них
усилены C ordering и A/D no-wait assertions, затем выполнена вся final matrix один
раз. Нет скрытого retry-until-pass или неожиданного test failure.

После тестов metadata-only `go list` сначала отверг VCS discovery в non-Git copy;
запрос повторён с `-buildvcs=false` (build/test команды не менялись). Collector
также явно исключил generated testmain вне source tree после path check error.
Эти metadata corrections не являются повтором упавших тестов; отметки сохранены
в compiled manifest. Raw test/build logs сохранены локально с опубликованными
SHA256; 736 структурированных записей опубликованы полностью, а не cherry-pick.

40 broker cleanup receipts подтверждают возврат Close после join workers.
Все Family sessions/packet endpoints закрываются cleanup; stream Close ожидает
bridge workers. Synthetic profile только в test.TempDir, удалён test runner;
credential material/PEM/payload/identity/session tags не публикуются.
Новых реальных credentials, CRL writers или provisioning artifacts нет.

## HISTORICAL_CAUSAL_BINDING

**NOT_PROVEN.** Положительные SOURCE_MECHANISM и APP_PATH_COMPATIBILITY не создают
binding к C1/I1. Не установлено наличие chat ACTIVE holder, его identity/broker,
overlap по времени и причина конкретной исторической UNKNOWN. Историческая S1 с
unbound challenge/context_deadline совместима с гипотезой, но не назначается owner
episode. Историческое UNKNOWN не переименовано в DEADLINE/CANCELLED/CLOSED_PIPE.

Локальный packet fixture заменяет signaling bridge/Telemost/Pion/RTP/VP8. Android,
JNI, native packet startup, TUN/DNS/Mux data path, реальная dedicated readiness и
live provider не покрыты; их исправность/непричастность из теста не следует.
Тест не закрывает прежний production FAIL и не принимает frozen candidate.

## MINIMAL_NEXT_CORRECTION_OR_EXPERIMENT

1. **Отдельный ownership шаг, не выполнен здесь:** общий per-identity owner/lease
   coordinator для VPN и chat. При совместимом security/profile scope — явное
   заимствование уже готового транспорта; если это неприемлемо для VPN capability,
   согласованный handoff: release старого owner → завершённый server cleanup →
   новый acquire. Сохранить single-holder, authorization/recheck, security deadlines
   и capacity. Не обходить ограничения, не убивать background chat и не увеличивать
   120s timeout. Следующий локальный caller regression должен проверить обе
   последовательности chat-first/VPN-first и cancellation во время handoff.
2. **Отдельный diagnostic шаг, не выполнен здесь:** классифицировать
   `errors.Is(err, os.ErrDeadlineExceeded)` как deadline; сохранить raw error и
   локальный ctx.Err/context.Cause в месте receive failure. Для closed pipe/EOF
   использовать контекст только с явным происхождением local cancellation, иначе
   отдельный transport-close факт, не предполагать deadline. Regression — текущий
   real Family/TLS harness с deadline/cleanup race, cancel, peer close с nil ctx,
   invalid/success HELLO, без завязывания на долю race-вариантов.
3. Если требуется именно historical proof, нужен отдельный разрешённый binding
   holder identity/broker/time и owner attempt. Здесь он не запрашивался и новый
   production episode автоматически не запускается.

## Публикация и неизменность production

Review branch: `review/supervisor-state-20261015`; commit/push только docs и новый
research evidence/test directory. Canonical report URL после публикации:
https://github.com/Joker20380/family_connect/blob/review/supervisor-state-20261015/docs/releases/2026-10-15-bootstrap-hello-admission-repro-1.md

REMOTE_HEAD_SHA и immutable report URL возвращаются в итоговом сообщении после
проверенного push/readback; SHA собственного commit не записывается внутрь него.
Build/installed/public/invitation-page versions **не менялись**. Rollout отсутствует;
rollback этих материалов — обычный revert review commit, не runtime rollback.
Product correction и diagnostic patch остаются отдельными незапущенными задачами.

Original dirty main сохранён; frozen sources/binaries не изменены. SSH/ADB/runtime
interventions, owner CONNECT/reconnect, native polls, APK install, gateway restart,
deployment/release, live room/provider, credential mutations и WS1011/recovery
triggers — **0**. Git publication не является gateway SSH intervention.
