# Warm-start: двухфазный manual operator gate

## Current override: TELEMOST-WORKABILITY-PROOF-1

Latest authorized task requires **ACK before arm**, not the historical order below:
PREPARED → READY_FOR_OPERATOR → OPERATOR_ACK → GATE_ARMED → GATE_RECHECK →
CONNECT_WINDOW_ACTIVE → CONNECT_OBSERVED → TEST_RUNNING → CLEANUP.
No arm while waiting for the explicit fresh «ГОТОВ» after PREPARATION COMPLETE.
An early ACK during preparation does not activate this sequence.

Keep900s/32 unchanged. For the required12min post-READY observation, budget30s
post-arm setup reserve +45s CONNECT +45s startup acceptance +720s observation
+60s cleanup. This is a host acceptance cutoff, not a product timeout change.
If insufficient, abort/partial without rearm, renewal or a second CONNECT.
Current local protocol and fixtures are under
`state-client-build/field65-export16/telemost-workability-proof-1/`;
live adapter readiness must be proven separately before displaying CONNECT.
Historical22 fixtures and budgets below do not prove the new live wiring.

## Historical protocol (superseded order/budget for current task)

**Подготовлено offline12.10.2026, НЕ исполнено.** Это не разрешение на новый
CONNECT. Предыдущая физическая попытка израсходована; blocked warm-start остался
NOT_TESTED. Следующая попытка требует отдельной задачи и fresh preflight.
[Исходный разбор](releases/2026-10-12-gateway-seed-read-cause-1.md).

## Артефакты и неизменные границы

- Принятый research84/code84, тот же package/signer/native; проверять фактические
  SHA/UID/embedded metadata по manifest, не брать historical snapshot за current.
- Research provisioning-only gate остаётся **900s /32 operations**. APK, safe-cache
  policy, native, TUN, Telemost, admission, server response не изменять.
- Локальный протокол/fixture:
  `state-client-build/field65-export16/gateway-seed-read-cause-1/harness/operator_gate.py`
  и `test_operator_gate.py`. Это pure event-driven host adapter, не новая Android
  управляющая API. Никаких ADB input, Accessibility, автоматического CONNECT.
- Старый `whitelist-warm-start-1/live.py` сохранён как evidence. Его самостоятельный
 90s wait НЕ использовать как новый operator gate: в нём отсутствует явный ACK.
  Следующий driver должен вызывать `wait_for_manual_connect` вместо этого wait,
  передавая существующие read-only capture/control adapters; fixtures не являются
  доказательством выполненного live wiring. Lifecycle context manager держать
  до окончания startup/egress/evidence, а не только до получения CONNECT.

## Бюджет

900s gate TTL начинается при фактическом signed-helper arm и **не обновляется**.
После подтверждения ARMED: ACK wait≤120s; только после ACK короткое CONNECT
window≤90s; после наблюдения CONNECT startup≤300s; после READY observation≤120s;
cleanup margin120s. Сумма750s, внутри принятого900s контракта. Это прежние
90/300/120s startup/test budgets плюс отдельное ожидание ACK и cleanup, не новое
transport timeout/credential TTL. Не обещать5min observation поверх этого бюджета.

Перед arm/pre-ACK заранее подтвердить готовность оператора к скорому этапу;
не arm во время сборок/установки/длительного исследования. Gate checkpoint возрастом
не более5s должен покрывать оставшийся бюджет, binding и blocked_calls<32.
Недостаток TTL/credential headroom — ABORT, не rearm/renewal внутри эпизода.

## Последовательность A–L

1. **A — Fresh gateway preflight.** PID/InvocationID/start/NRestarts, loaded=next,
   config, observer/receipt schema, no new fatal, strict served chain/profile,
   expiry/headroom, current publication RU/NL, accepted directory set. При новой
   fatal receipt сохранить её и остановиться. Никакого restart «для чистоты».
2. **B — Exact cache.** Принятый offline reader/production selector с реальной
   identity: committed bytes/hash, binding/time/floors/revocation, exact selected
   snapshot, native offline validation. Selected snapshot принят invocation из A.
   Любой preparation refresh/update только если отдельно разрешён будущей задачей,
   только ДО arm и с новым exact proof; иначе ABORT.
3. **C — Installed84.** Фактически сверить research84, signer/UID/native,
   cache/enrollment preservation. Не запускать launcher для косметики. Никакого
   hidden AWG/TCP fallback, service-only carrier вместо full VPN.
4. **D — Collectors.** Проверить fixtures и подключить существующие read-only
   incident/selected-directory/admission/HELLO/dedicated/fatal/first-close captures,
   server provisioning counter baseline и deterministic ordinary-app egress.
   Listener должен быть готов до operator сообщения, без истечения основного
   CONNECT window в фоне. Сохранить previous connection ID и device clock anchor.
5. **E — Arm.** Один штатный signed-helper arm; exact package/UID/version/source/
   APK/signer/nonce,900s/32, cache unchanged. Сохранить ARMED receipt и счётчики.
   Проверить Telemost/ordinary/chat scope, не выполнять лишний provisioning probe.
6. **F — Explicit ACK.** Показать пользователю:

   ```text
   READY_FOR_MANUAL_CONNECT
   Телефон открыт на EX_IT / Family Connect, выбран Telemost?
   Ответьте ACK <generation>: «готов нажать сейчас».
   CONNECT пока НЕ нажимайте. Ожидание ACK не более120 секунд.
   ```

   Отсутствие ACK → bounded timeout → cleanup. Duplicate/stale ACK не продлевает
   TTL и не открывает вторую попытку. Сообщение должно идти из того же driver,
   который действительно обслуживает события, а не из уже завершившегося wait.
7. **G — Re-check после ACK.** Fresh gate binding/state/TTL/counters, тот же gateway
   invocation, credential headroom, collectors alive, device wall-clock sample.
   ACK сам по себе не означает CONNECT. Record host receipt time и device sample
   отдельно; monotonic разных устройств не сравнивать. При скачке/неопределённости
   часов ABORT, а не принимать старый CONNECT за новый.
8. **H — Active window.** Только после G показать:

   ```text
   CONNECT_WINDOW_ACTIVE
   Gate перепроверен. Один раз физически нажмите CONNECT сейчас.
   Окно90 секунд. После нажатия ничего не нажимайте.
   ```

   Не inject input. Единственный finite host deadline стартует после ACK/recheck,
   внутри неизменного абсолютного arm TTL.
9. **I — CONNECT observed.** Требовать новый connection ID и реальный orchestrator
   DISCONNECTED→CONNECTING event, из capture текущей generation, свежее device
   event time после ACK device sample. Generation — host capture binding, не
   выдуманное поле product event. Исключить previous ID/дубли/старый capture.
   Проверить APK/source-specific диагностику: неизвестный event schema — ABORT.
   Framework VPN icon или слова «включил» без event не подменяют startup evidence.
   Поздно доставленный pre-ACK event не принимается. После фактического CONNECT
   attempt consumed независимо от результата, даже если stage evidence потеряно.
10. **J — Startup.** Blocked-before-dial/zero owner provisioning/import/ACK,
    exact cached native input, Telemost seed/admission/Family auth/descriptor/
    dedicated READY + full VPN established. Gate не снимать после одного CONNECT
    event. Первый terminal failure сохранить, не выполнять второй CONNECT.
11. **K — Egress.** Только после J existing ordinary Android test app: IPv4/normal
    HTTPS nonce, controlled DNS, TUN→Mux→Telemost→NL→endpoint→complete response
    correlation.≤120s/2MiB, до4 streams; no browser/speedtest/lease-boundary extension.
    Endpoint IP, а не текстовый ISP label; IPv6 unavailable не PASS. Warm model не
    доказывает cold start/DPI/реальный FIELD.
12. **L — Evidence затем cleanup.** Preserve first cause/receipts; штатный disarm,
    verify CLEANED/EXPIRED, cache unchanged, удалить временные helpers/resources.
    Штатный VPN OFF; app/chat lifecycle по отдельному разрешённому контракту,
    без второго CONNECT/косметического refresh. No gateway restart.

## Abort, late events, crash

- Любая смена invocation A–I до физического CONNECT: ABORT/ATTEMPT_NOT_CONSUMED.
  После CONNECT: consumed; никаких manual retries. Не полагаться на тот же PID.
- Таймаут/explicit cancel/expired gate/headroom/collector failure/fatal gateway:
  сначала немедленно объявить окно закрытым, затем cleanup и receipt:

  ```text
  TEST_WINDOW_CLOSED
  НЕ нажимайте CONNECT. Проверка завершена; позднее подключение вне теста.
  ```

- CONNECT до ACK или после cleanup: **OUTSIDE_TEST_WINDOW**, не product PASS/FAIL.
  Если это реальное новое физическое нажатие, отдельно учесть consumed budget.
  Старые connection/generation события бюджет новой попытки не расходуют.
- Host не может запретить физическую кнопку без запрещённого изменения product
  UI/permissions. Протокол предотвращает неверное засчитывание и явно закрывает
  окно, но не обещает физическую блокировку кнопки.
- `try/finally`/context manager вызывает idempotent cleanup на обычном exception/
  cancel. SIGKILL/потеря host или связи не гарантируют немедленный cleanup: отметить
  UNCONFIRMED, не PASS; принятый app gate сам прекращается по исходному900s TTL,
  max32/reboot invalidation. После возвращения — проверить expiration/cleanup,
  не rearm автоматически. Валидный cache не удалять.
- Все READY/CLOSED сообщения и ACK/CONNECT/cancel сохранить с generation,
  host timestamp и отдельным device timestamp, не с содержимым пользовательских
  сообщений. Старое краткое collector window после его завершения не «расширять».

## Локальная проверка протокола

```sh
cd state-client-build/field65-export16/gateway-seed-read-cause-1/harness
python3 -m unittest -v test_operator_gate.py
```

22 fixture: ACK+CONNECT; ACK/noCONNECT; noACK; early/lateCONNECT; expirybeforeACK;
invocation/headroom changes; helper exception; lostcleanup/SIGKILL via boundedTTL;
duplicateACK; stalegeneration/connection/timestamp; cancel/maxcalls/stalecheckpoint;
fatalafterCONNECT; collector loss; event-driven driver. Fixture не управляет owner или gateway.
