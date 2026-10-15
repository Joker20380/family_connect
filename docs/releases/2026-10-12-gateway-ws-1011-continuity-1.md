# GATEWAY-WS-1011-CONTINUITY-1 — PARTIAL

**FIRST_BLOCKER = SAME_ROOM_POST_1011_MEDIA_AND_CACHED_BOOTSTRAP_UNPROVEN.**
**DEPLOYMENT = NOT_RUN. OWNER_CONNECT = NOT_RUN.**

Реальный WS1011 локально воспроизведён до shared seed manager и fatal observer.
Потеря dedicated sessions локализована: не наследование seed context, а закрытие
broker при завершении service/process. Однако безопасное восстановление media
в той же room и реальная обслуживаемость старого cache после него не доказаны.
Спекулятивный retry не добавлен. Это не принятый continuity fix.

## Три независимых уровня причины

| Уровень | Результат |
|---|---|
| REMOTE_CLOSE_BOUNDARY | PROVEN: natural receipt WS_CLOSE/1011, context ACTIVE; локально настоящий Gorilla CloseError1011 |
| PROVIDER_INTERNAL_REASON | UNKNOWN: внутренняя причина signaling server не сохранена |
| LOCAL_RESILIENCE_BEHAVIOUR | CURRENT/PROVEN: current shared seed failure → service return → broker teardown → exit1 → new invocation/route |

1011 — кандидат для исследования bounded recovery, **не доказательство** того,
что room/credentials/media сохранились или что следующий join будет успешен.
Действующий README явно задаёт fail-closed при потере единственного seed; новый
continuity requirement им не выполняется. Это воспроизводимый availability gap,
но не основание автоматически retry любую неизвестную ошибку.

## Точная база и evidence

Защищённый локальный capsule:
`state-client-build/field65-export16/gateway-ws-1011-continuity-1/`.
Содержит `RESULT.json`, `manifest.json`, `DESIGN.md`, `DEPLOYMENT_PLAN.md`,
`REPRODUCE.md`, `scope.txt`, `fixtures.diff`, пустые `observability.diff` и
`behaviour.diff`, source/baseline, test receipts и `SHA256SUMS`.

- Проверены1920 sealed inputs из formal-acceptance2, signal-read-cause,
  seed-read-observability, seed-read-cause и functional-workability capsules.
  Исходные receipts/отчёты не переписаны. Dirty main worktree сохранён.
- Exact deployed source: `a4087e000fdbe674b72ede3a6c8822445c87c654` + classifier diff
  `7e7d408670a6ac6afa18e856beb8dcc0ca26a3b6f074e205d4dd25e62d78967b`.
- Observation binary:
  `21f0a0fdc27b50c00ea922f0b716516e2422aedf1b3797369718f7d00070509a`.
  Предыдущий observation baseline:
  `fa4cf8672c3606c1b6d4d665a6944b4ebe8661076a19a6d2187909263f733eea`.
- Natural application receipt SHA256:
  `9fae6d22695208f451fc3370466ae0d5264562372e24b2fe43a5de0025106ecc`;
  systemd receipt:
  `2531d94a71a7faf28794ceb4e393baa8455756c555128cd90ac6a9d0ef41c9ef`.
- Fatal20:12:48UTC, invocation`1613fa1ce16d4ea5a649255ddf76829f`, PID1415977,
  seed_generation2, firstSEED_READ/SIGNAL_READ, cleanup completed, exit1.
  Directory before`2287c6c5…9ec5e`, replacement`4d722bad…15424`; full hashes and
  chronology remain in immutable previous capsule.
- OWNER_CONNECTS_AT_FATAL=0; OWNER_TELEMOST_SESSIONS_AT_FATAL=0;
  RELATION_TO_OWNER_CONNECT=EXCLUDED for this fatal. Independent background
  server/client processes are not declared absent. Earlier UNKNOWN exits remain UNKNOWN.

Единственная remote-операция: bounded read-only snapshot20:29:42UTC.
Gateway active PID1540161, InvocationID`4fafa22abf6c4bcbbc137375472855c7`, NRestarts1,
loaded=next21f0a0fd…509a, existing observer armed. Receipt counts11/12, directories
0700, files0600, retention32. Invocation matches the prior post-restart snapshot.
Это не длительное наблюдение и не fresh credential/cache readiness. Journal не запрашивался.

## SHARED_SEED_CALL_GRAPH / CURRENT_PROCESS_FATAL_CAUSE

Ссылки здесь относятся к **exact capsule source/carrier**, не dirty root source.

1. `cmd/bootstrap-broker/main.go:57` — `runObserved`: загружает credentials,
   создаёт один `roombroker.Broker`, откладывает `broker.Close()`. Service context:
   `signal.NotifyContext` + finite `--duration`; HTTP directory listener и seed
   manager работают sibling goroutines.
2. `bootstrap/seed_overlap.go:37` — `runOverlap`: дочерний context, workers,
   current generation; planned rotation ограничена двумя generations. Failure
   **current** generation возвращается наружу. Retired old generation изолирована.
3. `bootstrap/seed.go:77` — `Run`: provider `CreateRoom` с15s budget,
   конечный lifetime, `TelemostSeed` с45s READY, publication после готовности.
4. `roombroker/provider.go:64` — OAuth conference creation. `RoomProvider`
   содержит только `CreateRoom`, не Resume/Rejoin и не гарантию room survival.
5. `telemost/session.go:181` / `Connect:268` — новый session/child context,
   single-use CAS; `Auth.FetchConnection` делает GET существующей room, получает
   peer/credentials/WSS endpoint. Создаются **новые** subscriber/publisher Pion PCs,
   transport/ICE; `dialWebSocket`, hello и workers; затем реальный media READY.
6. `telemost/signaling.go:110` — Gorilla WebSocket1.5.3 `ReadJSON`. Первая safe
   классификация сохраняется до generic error; `signalClosedAt` фиксирует first
   source, закрывает session/cancel. `Session.Recv` возвращает сохранённую failure.
7. `bootstrap/carrier.go:162` — shared endpoint read **до** FCB1 decode. Ошибка
   наблюдается как SEED_READ и возвращается `roombroker.Code("seed_closed")`.
   Ошибки отдельных bootstrap exchanges не эквивалентны этому shared read failure.
8. `main.go` seedDone branch возвращает error после service cancellation/HTTP close;
   deferred `broker.Close()` отменяет все holders и ждёт cleanup. `main` пишет
   fatal receipt и вызывает `os.Exit(1)`. systemd`Restart=always`/30s создаёт другой
   process/seed; старый cached locator не становится принимаемым от одной подписи.

Production deadlines неизменны: signaling read60s, refresh на message/pong,
write15s, handshake15s, WS ping20s/control-write1s, application heartbeat5s.
Fixture timeout80ms применяется только к loopback connection. Он не доказывает,
что исторический1011 вызван heartbeat/read timeout.

## WS_CLOSE_MATRIX / LOCAL_BEFORE_AFTER

Новая composed fixture использует реальные WS/WSS close frames и реальные
`ReadJSON → Session.signalingLoop/Recv → SeedManager.Run/runOverlap → fatalObserver`.
Нет `errors.New("1011")`. Direct read отдельно проверяет `errors.As(*CloseError)`,
тип, code и `errors.Is` EOF. Wrapper/receipt цепочка запускается на втором реальном
соединении. First cause не меняется после cleanup/cancellation.

**Ограничение:** seed connector READY в этой fixture подставлен на signaling boundary;
реальный provider/media не запускается. Проверяется manager/service error result,
а не выполнение целиком production main. Exit1 подтверждён кодом main и отдельным
историческим systemd receipt — не выдан за локальный полный service integration.

| Реальный input | Safe class | Текущий shared-seed result / policy conclusion |
|---|---|---|
| Close1000 /1001 | WS_NORMAL_CLOSE с code | seed_closed/fatal; remote normal closure не равна local stop |
| Close1002 /1003 /1007 /1008 /1009 | WS_CLOSE с exact code | fail closed; protocol/data/policy не retry |
| Close1011 | WS_CLOSE1011 | seed_closed/fatal; bounded recovery candidate только после полного proof |
| Close1012 /1013 | WS_CLOSE с exact code | библиотека принимает; provider rotation/retry policy не доказана |
| TCP EOF без close frame | WS_ABNORMAL_CLOSE1006 | причина закрытия не уточняется; no blanket retry |
| Partial WS frame + EOF | WS_ABNORMAL_CLOSE1006 | framing ambiguity, fail closed до новой доказанной policy |
| TCP reset | CONNECTION_RESET | потенциальная network loss; recovery пока отсутствует |
| TLS close_notify без WS close | WS_ABNORMAL_CLOSE1006 | TLS transport closed, не доказательство reusable room |
| Malformed JSON | JSON_SYNTAX | fail closed |
| Invalid WS frame | UNKNOWN | fail closed, не классификация по raw text |
| Empty JSON payload | UNEXPECTED_EOF | fail closed |
| Oversized message | WS_READ_LIMIT | fail closed |
| Read deadline / no pong fixture | IO_TIMEOUT | ускоренный fixture deadline; не доказанный provider timeout |

20 composed cases×3 проходят. Existing real normal JSON/ACK и local close/context
cancel/deadline fixtures также race×3 PASS; local stop не заменён на SIGNAL_READ.
TLS alert покрыт существующим **type-only** classifier test (`UNKNOWN`), не выдан
за настоящий post-handshake TLS alert или восстановление после него.

**До/после здесь — exact baseline против test-only source, не working recovery patch.**
All2004 existing files побайтово неизменны. Обычный GoFiles set совпадает; test bridge
под `ws1011fixture` отсутствует в normal build. Никаких новых production methods,
endpoints, wire/schema или lifecycle changes в обычной сборке.

## DEDICATED_SESSION_ISOLATION / ACTIVE_SESSION_CONTINUITY

Ключевая находка: `Broker.Challenge` создаёт отдельный bounded leaseLifetime.
`Broker.Create` привязывает отмену request только на setup через `context.AfterFunc`,
затем снимает связь. Dedicated gateway использует свой Telemost session/room/PCs,
Family TLS, Mux и lease handler. После READY shared seed не является data path.

Fixture поднимает реальную Family TLS/Reliable + Mux + persistent loopback TCP и
authenticated lease handler. Dedicated packet carrier синтетический, **не Telemost
media**. После независимого настоящего seed WS1011 и отмены seed subtree:

- TCP stream продолжает передавать полные payloads;
- тот же holder/session принимает authenticated renewal sequence1;
- после старого deadline проходит ещё один payload по тому же stream;
- actual `broker.Close()` затем отменяет holder и освобождает socket.

Lease clock ускорен8+2 минуты; это deterministic local test, не12-минутный live run.
Доказана возможность lifecycle-изоляции до service teardown. **Не доказаны** seed
recovery, real provider media continuity или дальнейший bootstrap старого cache.

## SAME_SEED_RECOVERY_CAPABILITY / REMEDIATION_OPTIONS

Production `Auth.FetchConnection` дважды запрашивает тот же room URL у local stub;
получает новую peer metadata, не вызывает OAuth CreateRoom.403 reject сохраняется.
Повторный `Session.Connect` на том же объекте отвергается single-use guard.

Но metadata GET ≠ signaling rejoin ≠ fresh Pion PCs ≠ media READY ≠ seed packets
≠ authenticated bootstrap по старому cache. Source/interface не гарантируют, что
room остаётся доступной после1011. Восстановление одного WSS не воскрешает закрытые
PCs, closeOnce, connectedOnce, queues и media state.

| Вариант | Continuity | Security / resources / compatibility | Решение |
|---|---|---|---|
| A Fresh carrier в прежней room | Может сохранить v1 directory и dedicated holders | Fresh auth/PCs; finite budget/backoff; старый cleanup не касается нового; исходные expiry/floors | Предпочтителен для следующего proof, NOT_ACCEPTED |
| B Successor + overlap | Existing planned overlap сохраняет только **живой** старый endpoint | ≤2 generations, old expiry; две публикации не оживляют dead room | Сам по себе не решает старый cache |
| C Restart + stable locator | Locator потенциально сохраняется, active dedicated всё равно гибнут | Нужны provider reuse/persistence/replay/ownership guarantees | Не закрывает оба требования |
| D Current restart/no overlap | Cache и dedicated continuity отсутствуют | Текущий bounded fail-closed contract | Оставлен без изменений |

**SELECTED_REMEDIATION = NONE_ACCEPTED.** Конкретная недоказанная граница:
fresh same-room join → новые publisher/subscriber Pion PCs → media/PacketEndpoint
READY → реальный authenticated bootstrap с неизменными cached directory bytes.

`DESIGN.md` фиксирует требования к будущей A: ограниченный lifetime recovery budget,
finite cancelable backoff, retire-before-replace, no parallel seed owners, свежая
security validation, no auth/protocol/UNKNOWN retry, unchanged security deadlines,
не отравлять fatal receipt успешно восстановленной nonfatal первой ошибкой.
Новые retry timers/budgets не приняты и не внедрены.

## Tests / baseline / security

| Check | Результат |
|---|---|
| Final continuity fixtures race×3 | 132PASS events,0FAIL,0SKIP |
| Baseline / test-source targeted race×3 | 414PASS/3SKIP каждый; immutable cause, negative auth, overlap, lease, retention/write failure |
| Baseline full race suite | 344PASS/7SKIP;6 known diagnostic subfailures + aggregate parent failure |
| Test-source full race suite | 345PASS/7SKIP; те же6 subfailures + parent |
| Busy-wire | В этом сравнении не воспроизведён, не исправлен |
| Repeated signaling cleanup | 20 cycles×3, FD/goroutine bounds PASS; media PCs не создавались |
| Privacy | Новые receipts allowlisted; нет close reason, URL, payload, token или raw error |
| Source scope | Product bytes unchanged; fixture bridge excluded from normal GoFiles |

**NO_NEW_FAILURES_RELATIVE_TO_EXACT_BASELINE** в выполненном scope. Full suite
**NOT_GREEN**. Старые diagnostic failures: unknown identity, wrong-family, revoked,
wrong-gateway, stale-crl, stale-revision. Independent actual security rejection
fixture проходит; assertions не переписаны ради зелёного результата.

Первый sandbox probe остановлен запретом loopback socket (`operation not permitted`);
после approval тот же local test PASS. Это отдельный environment failure, не продукт.

Обязательные recovery-сценарии repeated failures/budget exhaustion/backoff cancel,
stale reconnect callbacks, old cleanup после new generation, expiry **during
recovery**, media PC/room bounds и old-cache bootstrap после recovery — **NOT_RUN**:
recovery implementation отсутствует. Existing holder replay/expiry/cleanup/overlap
tests не выдаются за эти новые сценарии. Retention/receipt write failure проверены
для существующего observer, не для несуществующего recovery collector.

Family auth/admission/revocation/floors/lease policy не менялись. API/AKI/publisher
не портировались и не развёртывались; их runtime untouched, новые API tests здесь
не заявляются. Old-client schemas unchanged; recovery compatibility NOT_PROVEN.

## Artifacts, deployment plan and final state

`OBSERVABILITY_PATCH = NONE`; existing classifier уже сохраняет1011.
`BEHAVIOURAL_PATCH = NOT_CREATED`; пустые diffs явно отделены от test-only diff.
`LOCAL_CANDIDATE = NOT_CREATED`; validation commit и production binary не создавались,
поскольку recovery acceptance не закрыта. Source tree manifest hash, exact fixture
diff, toolchain, command/input hashes и logs сохранены в capsule.

`DEPLOYMENT_PLAN.md` — **blocked, non-executable checklist**, не команда к rollout:
сначала complete local recovery/security/generation acceptance, затем отдельная
fresh-baseline/credential проверка, rollback, один controlled restart, real continuity
acceptance и30-minute stability. Owner formal warm-start не совмещается с первым
continuity deployment. Нельзя откатывать API/collector updates более поздней baseline.

Существующие gateway classifier/observer/rollback, API, client research84/cache/
identity/enrollment/settings не менялись. Телефон не опрашивался. Temporary synthetic
credential fixtures удалены после тестов; evidence/source сохранены. Ничего не push.

| Counter | Value |
|---|---:|
| GATEWAY_DEPLOYMENT / GATEWAY_RESTART / RENEWAL | 0 / 0 / 0 |
| OWNER_INSTALL / OWNER_INSTRUMENTATION / OWNER_REFRESH / OWNER_CONNECT | 0 / 0 / 0 / 0 |
| TELEMOST_LIVE_SESSIONS / GATE_ARM | 0 / 0 |

Historical functional warm-start PASS сохранён. **ATTEMPT_CONSUMED=NO** для этой
задачи; warm-start readiness не повышена. **PUBLIC_RELEASE=NOT_RUN**.
**REAL_RESTRICTED_NETWORK_FIELD=NOT_RUN.**

**Ровно следующая операция:** закончить локальное доказательство полного same-room
rejoin с реальным Pion/media и authenticated bootstrap по неизменному cache,
включая old/new generation cleanup, до выбора и реализации recovery patch.
Deployment, restart, provider room и owner CONNECT автоматически не выполнять.
