# План / bounded desktop parity106 queue

## Current engineering priority / Текущий critical path

Цель — тот же Family Connect на Linux/Windows, что принятая Android beta106-recovery,
а не отдельные реализации продукта. [Текущий срез](STATUS.md) — источник текущего состояния.
Продуктовый checkpoint: phase22, source baseline `664342a6566792a4ea621274a369bcd6b6012143`.
D00 — организация документации; следующие строки являются очередью, не разрешением на автозапуск.
**L01/L01-R review принят в Linux source/native/root→UID/isolated-kernel scope. Review L02.2 принят: локальный критерий L02 authenticated OFF→ON→OFF через Manual и Auto/MESH выполнен. L02.1-R atomic RetainChat/terminal recovery и L02.1-R2 status classification приняты. D01.3 ChatBridge/Host/ServiceHost приняты; D01.3 PARTIAL до DIRECT correction. Только D01.3-R DIRECT completion/admission; NEXT — review D01.3-R. Review D03/D04/D05, D02.1 collection/import isolation и D02.2 public-reference принят.
Review D02.1-R и fleet-документации `1725656` принят;
D02.1-R остаётся PARTIAL/NOT_RUN; L03 и дальнейшие Linux/Windows задачи не начинаются.**

Порядок по умолчанию: D01.1 → D01.2 → D02.1 / принятый review D02.1-R → D02.2 / review → D03 → D04 → D05 → Linux → Windows → R01.
Зависимости в таблицах — необходимые результаты, а не требование заново выполнять завершённые фазы.
Каждый ID — отдельный ограниченный пользовательский результат, отдельные проверки и commit/push.
`DONE` = выполнен указанный критерий, `NEXT` = ещё не начат, `QUEUED` = не начат как отдельная задача.
Это не означает отсутствия всего кода в QUEUED: существующие части переиспользуются и проверяются.
Отсутствие физической ОС не закрывает её gate и не блокирует доступную другую ОС;
фиксировать точный NOT_RUN и короткую инструкцию, согласовывая следующий ограниченный шаг.

## Подготовка и известный дефект

| ID | Результат | Зависимость | Статус | Критерий завершения |
|---|---|---|---|---|
| D00 | Компактное состояние и последовательный план | phase22 / baseline | DONE | Новый сеанс читает STATUS + выбранный ID; история сохранена побайтно, ссылки и diff проверены; commit/push с remote SHA отражён в итоговом ответе. |
| D01 | Зависимости Linux/desktop CI | D00 | IN_PROGRESS | Dependency gates D01.1/D01.2 отдельно от общей CI-приёмки; закрытие требует полного PASS обязательных suites после устранения остаточных blockers, без скрытия тестов. |
| D01.1 | Client builds/linux, AmneziaWG pilot, TCP pilot | D00 | PARTIAL | Dependency gates `26f71d6` приняты review; реальные Python3.12 imports/адресные CI PASS. Полный desktop FAIL: RNS capsule, AWG Auto lifecycle assertion; PARTIAL сохранён. |
| D01.2 | Linux control, phase0, Dockerfile.control test-stage | принята dependency-часть D01.1 | PARTIAL | На pushed `07b52e3` Python3.13 imports/адресные gates PASS ×3; Docker root 22 passed. Каждый full suite: 9 owner_handoff/prepare collection errors, exit 2 (D02); обязательные gates сохранены. |
| D01.3 | Public chat probe/prepare completion и следующий admission | L02.2/local L02 review принят; D03/D04/D05, L01/L01-R сохранены | PARTIAL (Host/ServiceHost/ChatBridge accepted; DIRECT correction D01.3-R) | [Отчёт](releases/2026-10-24-desktop-chat-admission-d01-3.md): actual Host/ServiceHost/ChatBridge и Unix IPC, event-barrier red2/green; EOF после cleanup сериализован с admission, bounded client wait без open/HTTP retry. Public4/native caps и drain/accounting сохранены. 266 адресных + финальные24, прежние15/combined3/root→UID PASS. Production `23e3c5513ab9c37e919f228066c0e23f733a997e`: Client Linux и isolated gates PASS. Финальный test source `f258c17007102634fead9894bcfe9a82f6db44cf`: mandatory desktop pytest 40132223364/120986275264 PASS; общий D01 открыт. |
| D01.3-R | DIRECT close/active removal под admission lock | D01.3 accepted subset; без переработки native | CHECKPOINT (local PASS; CI pending) | [Отчёт](releases/2026-10-24-desktop-chat-direct-completion-d01-3-r.md): actual DirectHost/DirectBridge/Authority и Unix IPC, барьер после close/EOF; red1/green30, зависимые326/root→UID13 PASS. Четвёртый open ждёт lock, пятый отклонён; cancel/deadline/shutdown/accounting/no replay. Mandatory Client Linux desktop pytest на новом source обязателен; до CI не PASS. STOP перед review D01.3-R. |
| D02 | Сбор и импорты исследовательских fixtures | dependency-части D01.1/D01.2 приняты | IN_PROGRESS | Review D02.1 collection/import isolation и D02.2 принят; зависимости D03 готовы. D02.1-R PARTIAL/NOT_RUN. Не ждёт полного зелёного CI, который сам должен разблокировать; общая CI-приёмка D01 остаётся отдельным gate. |
| D02.1 | Девять collection errors, историческая overlay-suite, изоляция импортов | окружения D01.1/D01.2 готовы | DONE (collection/import isolation) | Review подтвердил границы; `6a0a982`: clean collection 2996/0 errors, helpers/import/runner 75 PASS; три CI full suites с 56 residual failures. Историческая воспроизводимость отдельно в D02.1-R. |
| D02.1-R | Комплектность исторического runner | review D02.1 | PARTIAL | Коррекция принята review. Vector/original API, явные retained inputs, preflight до pytest; 110 адресных PASS. Historical suite NOT_RUN: нет anchored pins delivery-check, Java runtime/classes и 3 JARs; полный replay не обеспечен и в D02.2 не выполняется. |
| D02.2 | RNS/reference checks без локальной capsule в обычном CI | review коррекции D02.1-R принят | DONE (review accepted) | [Evidence `da8670e`](releases/2026-10-24-rns-reference-d02-2.md): public mappings, прежние pins, APK/inventory linkage, строгий --capsule. Clean export: 49 passed/1 прежний skip, collection 3051/0 errors; real capsule 2073 PASS. CI control/phase0/Docker: 55/54/54 residual failures, 0 errors; полные команды сохранены. |
| D03 | Окончательные ошибки ChatHTTP | приняты D02.1 collection/import isolation и D02.2 | DONE (review accepted) | [Evidence `290d430`](releases/2026-10-24-chat-http-terminal-d03.md): до 15 failed/18 passed, после 33 passed; зависимые 63+24 passed. Terminal-причина сохранена при cleanup, полный 200/consumer error без повторов, transient fallback сохранён. CI control/phase0/Docker: 54/54/53 residual failures, 0 errors; общий D01 открыт. |
| D04 | Auto stop/start lifecycle | приняты D03, D02.1 collection/import isolation и D02.2 | DONE (review accepted) | [Evidence `b41e1ad`](releases/2026-10-24-auto-lifecycle-d04.md): прежний Controller 8 failed/1 passed; service 55 PASS, зависимые 180 PASS/6 прежних skips. Публикация завершения owner и admission согласованы, fatal не сбрасывается; callback/process close до передачи владения. Linux desktop/Auto bridge CI PASS; одинаковые 54 residual failures в control/phase0/Docker. Docs-only `3f9854a` phase0 FAILURE отдельно. |
| D05 | Минимальная внутренняя модель выбора/назначения/активной сессии и граница существующего provider | review D03/D04 принят | DONE (local Linux boundary; review accepted) | [Evidence `c53265d`](releases/2026-10-24-desktop-provider-d05.md): модель используется NormalOwner/Platform/GuardedHost; 162 provider/model/native + 213 ownership/service/chat PASS. [Критерии](desktop-architecture.md#desktop-fleet-acceptance): stable ID 2×NL+DE, refresh без apply, fencing, signed legacy rejection, безопасные metadata. Linux Auto CI PASS; общий CI остаётся красным. Не Windows-интеграция/production fleet/F-01. |

<a id="ci-evidence"></a>
### D01/D02: наблюдавшиеся ошибки после baseline push

Эти ссылки — исходные наблюдения, не CI-проверки D00 и не автоматическое заключение
о причине каждого job. Разделить dependency/collection и fixture-import failures по фактическим logs.
1218 PASS phase22 относятся только к описанному локальному набору, не ко всему CI.

- [Client builds / Linux](https://github.com/Joker20380/family_connect/actions/runs/40073089239/job/120810560761).
- [AWG](https://github.com/Joker20380/family_connect/actions/runs/40073089248/job/120810560564).
- [TCP](https://github.com/Joker20380/family_connect/actions/runs/40073089297/job/120810560697).
- [Linux control](https://github.com/Joker20380/family_connect/actions/runs/40073089380/job/120810561183).
- [phase0](https://github.com/Joker20380/family_connect/actions/runs/40073089270).

D01.1: [итог PARTIAL, точные failures и CI](releases/2026-10-24-desktop-ci-d01-1.md).
D01.2: [окружение и evidence](releases/2026-10-24-control-ci-d01-2.md).
D02.1: [границы collection/imports и evidence](releases/2026-10-24-fixture-boundaries-d02-1.md).
D02.1-R: [комплектность runner и незакрытые pins](releases/2026-10-24-historical-runner-d02-1-r.md).
D02.2: [public RNS/reference и полный capsule gate](releases/2026-10-24-rns-reference-d02-2.md).
D01 сначала читает соответствующие workflows/lockfiles и эти ошибки; не переносит
лабораторный каталог целиком и не отключает обязательные suites ради зелёного CI.
D02 явно отделяет поддерживаемые проверки от архивных опытов; их source push не делает их release core.

<a id="d03"></a>
### D03: точка воспроизведения и требуемое сохранение ошибки

[provisioning/chat_bridge.py](../provisioning/chat_bridge.py), `ChatHTTP.stream`;
[tests/test_chat_bridge_http.py](../tests/test_chat_bridge_http.py).
[Детерминированное воспроизведение и исправление](releases/2026-10-24-chat-http-terminal-d03.md):
фактические ChatHTTP/FriendsClient, независимо управляемые read/close и clock без sleeps.
До исправления 15 failures, включая HTTP400/401/403/409 → ошибочный fallback;
после — первая terminal-причина сохранена независимо от cause cleanup, close выполняется.
Полный 200 и исключение потребителя после единственного yield не повторяют запрос.
Transient ConnectError/ReadTimeout/503, partial-read fallback и BridgeError mapping сохранены.
Это synthetic transport, не installed/live/protected DIRECT/service-only acceptance.
Review D03 принят; открытый historical replay D02.1-R не выдаётся за завершённый.

### D04: детерминированное завершение владельца

`clients/linux/auto_service.py`: Events на настоящем Controller воспроизвели ранний
DISCONNECTED, отказ start после завершённого потока и гонку повторного stop.
Теперь reap завершённого owner, публикация состояния и start/status/stop согласованы
одним lock; живой owner не обнуляется, FAILED/fatal не разрешает start.
Revocation до cleanup, retry записи journal без повторного cleanup, shutdown retain intent,
старые generation и поздний CONNECTED покрыты адресно. Реальный Coordinator завершает
terminal callback и process close до Runtime.dispose/передачи владения; native process
в этом тесте синтетический. [До/после и ограничения](releases/2026-10-24-auto-lifecycle-d04.md).
Связь с конкретным прошлым CI assertion из D01.1 не доказана; review D04 принят.

<a id="d05"></a>
### D05: локальная подготовка к расширяемому парку, не fleet-приёмка

[Основной контракт](desktop-architecture.md#desktop-fleet-boundary) — **минимальная Linux-граница реализована;
review D05 принят**. После принятых D03/D04, без зависимости от production fleet,
новых VPS или F-01 live. D05 задаёт общую модель/provider boundary; W01/W02 используют
её при продуктовой Windows-интеграции, обратной зависимости D05 → W01/W02 нет.
Модельные/отрицательные проверки выполняются адресно в D05; миграция — L08/W12,
полная установленная приёмка — L04/W11/R01. UI/model fixture не доверенный assignment.
L01/L02/W04 не расширяются за пределы fixed chat DIRECT/service-only.
Адресные model/provider/native проверки D05 выполнены; F-01/installed/live NOT_RUN.
Это не закрывает D01/D02 и не разрешает автоматически начинать Linux/Windows-интеграцию.

## Linux: интеграция, полный кандидат, затем установленная приёмка

| ID | Результат | Зависимость | Статус | Критерий завершения |
|---|---|---|---|---|
| L01 | Защищённый DIRECT для чатов | D03, D04; D05 review принят | DONE (review L01-R accepted) | Linux source/native/root→UID/isolated-kernel, не installed/live. [Исходное evidence](releases/2026-10-24-linux-chat-direct-l01.md) и [коррекция](releases/2026-10-24-linux-chat-direct-l01-r.md) сохранены с точными SHA; runtime umask, provenance и real TLS fatal исправлены и приняты. |
| L01-R | Исправления review protected Linux chat DIRECT | L01 review; принятые D03/D04/D05 | DONE (review accepted) | [Before/after и точные CI jobs](releases/2026-10-24-linux-chat-direct-l01-r.md): unit umask0077 + настоящий UID, DIRECT→EXIT registration→ProtectedMailbox→DIRECT с expiry/metadata, real TCP/TLS fatal без fallback. 145 + 49 Python/native, 6 root/UID, Go/race и оба isolated kernel gates PASS. Source `4fab7b6`: Client Linux/Auto/root→UID/kernel/AWG/TCP/voice CI PASS, control/phase0/Docker FAIL. Ни установка, ни live, ни закрытие D01/D02.1-R. |
| L02 | MESH service-only и передача владения | L01 (принят) | DONE (local source/native, review accepted) | [Начальный checkpoint](releases/2026-10-24-linux-chat-mesh-l02.md), source `383ef3606aaa4dbd29f0c7c0f755e6faec6e309f`, был PARTIAL. [L02.2](releases/2026-10-24-linux-chat-mesh-l02-2.md), source `dac0f6b45be6ed8703d3de93ff5fdbc67462eabe`, выполнил исходный authenticated API/mailbox OFF→ON/publication→EXISTING_EXIT→OFF через реальные Manual/Auto owners, drain/expiry/cancel/late results. Не installed/live/F-01; full-suite D01 остаётся открыт. |
| L02.1 | Lifetime поколения и комбинированная native/process приёмка | L02 partial; L01/L01-R, D03/D04/D05 приняты | HISTORICAL PARTIAL (completed by R/R2/L02.2) | [Отчёт](releases/2026-10-24-linux-chat-mesh-l02-1.md): bounded generation lease и typed-nil IPC исправлены; red/green на actual native owner, authenticated service-only/API/duplex-byte-mailbox/cleanup. На том checkpoint полный VPN publication→EXISTING_EXIT→OFF был NOT_RUN: отсутствовали generic packet/DNS/TUN health и broker lease lifecycle. Этот оставшийся gate выполнен отдельно в L02.2, не приписывается старому evidence. |
| L02.1-R | Terminal native generation: fencing и recovery | L02.1; L01/L01-R, D03/D04/D05 сохранены | REVIEW ACCEPTED (bounded scope) | [Отчёт](releases/2026-10-24-linux-chat-mesh-l02-1-r.md): peer/Mux failure и async bootstrap failure red/green на actual native owner; atomic generation pin закрывает acquire/use race; late HTTP/acquire, held/sticky cleanup, concurrent demand/VPN reservation проверены. Review RetainChat и terminal fixes принят; status-result correction выделена в L02.1-R2. На том checkpoint combined gate ещё был открыт; его завершение — отдельное evidence L02.2. |
| L02.1-R2 | Классификация native status и сохранение typed errors | L02.1-R review принят | REVIEW ACCEPTED (bounded scope) | [Отчёт](releases/2026-10-24-linux-chat-mesh-l02-1-r2.md): actual CONTROL4 contention и malformed IPC red/green. BUSY не отменяет healthy generation; DENIED до ChatBridge/ChatHTTP без replay. Atomic pin/refcount/cleanup/caps сохранены; прежние15 authenticated остаются обязательными. |
| L02.2 | Комбинированная local authenticated MESH OFF→ON→OFF приёмка | L02 partial; L02.1-R2 принят | DONE (review accepted, local source/native) | [Отчёт](releases/2026-10-24-linux-chat-mesh-l02-2.md): manual Supervisor и Auto/MESH отдельно; реальные UID IPC/native owner, TUN/private DNS/readback/health/publication, EXISTING_EXIT и новый SERVICE_ONLY; API/duplex byte-mailbox на каждом участке. Broker bind/renewal, lease/open/resource accounting, held cleanup/late result/profile mismatch/expiry/revocation/DENIED-no-replay; release CONTROL4 и packet RX fence приняты. Bounded CI gate сохраняет прежние15 и обязательные suites. Не live/installed/LXMF/F-01; исходный локальный L02 выполнен. |
| L03 | Полный внутренний Linux-кандидат | L02, D05 | QUEUED | Согласованы GUI, пользовательские службы, root-helper, native/RNS, зависимости и установка; capabilities соответствуют точному составу реально интегрированного пакета. |
| L04 | Установленный Linux VPN | L03 | QUEUED | На установленном кандидате подтверждены реальные AWG/TCP/MESH/Auto, P0/P1, DNS/HTTPS и передачи, применённый target/profile и заявленные capabilities; не CLI/echo/SOCKS или model fixture. |
| L05 | Установленный Linux-мессенджер | L03, L04 | QUEUED | DIRECT/MESH-доставка без VPN и с VPN, контакты/текст/голос, история и фоновые события подтверждены на реальных компонентах. |
| L06 | Linux recovery | L04, L05 | QUEUED | Ограниченные loss/return, sleep/resume, рестарт службы и отмена проходят с корректной очисткой, backoff и одним reconnect owner. |
| L07 | Linux visual parity | L03, L06 | QUEUED | Реальные окна: согласованные экраны/состояния, список вариантов и отдельные selected-next/active state по D05, RU/EN, DPI100/125/150/200%, resize/focus/Tab/Enter/Escape; сопоставление с точным Android-эталоном без изменения Android106. |
| L08 | Linux updater и сохранение данных | L03, L07 | QUEUED | Переход со старого поддерживаемого клиента на полный bundle и совместимая миграция настроек выбора D05; identity/WG keys, активация, Support ID, история, настройки, ссылки и signed floors/счётчики сохранены. |

Phase22 подключила Linux ChatOwner к EXISTING_EXIT. L01 добавляет protected DIRECT;
старый SYSTEM не переименован в DIRECT и не используется fallback этого нового пути.
Локальный host lifecycle принят по L02.2; DIRECT public admission завершается в D01.3-R. Одно активное владение
не означает вечный PID: текущий worker имеет собственный жизненный цикл.
Полный внутренний пакет L03 обязателен перед закрытием L04–L08; system-only component-r18 недостаточен.

L02.1 source `a2b105de49391928d4bb9c15c4d5ee2305085918` pushed/remote-verified:
600 адресных Python/native/process checks, Go/race и isolated kernel PASS.
Завершившийся CI: authenticated service-only и прежние Auto/root→UID/DIRECT,
Client Linux/AWG/TCP/voice PASS; control 3015 passed/54 failed/127 skipped,
phase0/tests 3014/55/127, Docker 3013/54/129, errors0. Дополнительный phase0 failure
`test_ui_unavailable_server_ack_is_authoritative` — причина не установлена.
Это не общее CI acceptance. Новые L02.1-R результаты и SHA отдельно в
[текущем отчёте](releases/2026-10-24-linux-chat-mesh-l02-1-r.md); mandatory suites
не отключены, посторонние failures не исправлялись.
L02.1-R source **`6556a902c723a3ef73486733f090cea6f388d099`** pushed/remote-verified:
606 distinct local checks, native/race/reference и isolated kernel PASS. Завершившийся
CI: control 3015 passed/54 failed/133 skipped; phase0/tests 3015/54/133;
Docker 3014/53/135, errors0; isolated-linux с13 authenticated, Client Linux,
AWG/TCP и voice PASS. Эти результаты не переносятся на R2.
L02.1-R2 source **`89e20a3437b2ba1b02f7d1649487579678158373`** pushed/remote-verified:
211 distinct local Python/native/process checks, native/race/reference PASS;
завершившийся CI: control **3030/54/135**, phase0/tests **3030/54/135**,
Docker **3028/54/137** (passed/failed/skipped), errors0; phase0/tests перепроверен
по собственному логу. Isolated-linux с15 authenticated, Client Linux, AWG/TCP/voice
PASS. Точные R2 jobs и новые L02.2 source/jobs разделены в
[отчёте L02.2](releases/2026-10-24-linux-chat-mesh-l02-2.md).
L02.2 source **`dac0f6b45be6ed8703d3de93ff5fdbc67462eabe`** pushed/remote-verified:
isolated-linux **40129362252/120977564710 PASS**, включая original15, combined3,
root→UID, оба kernel gates и race. Новый CI: control **3032/54/138**,
phase0/tests **3032/54/138**, Docker **3030/54/140**, errors0; AWG/TCP PASS.
Client Linux **1003/1/94** (bounded-mailbox BrokenPipeError) и voice pointer/holding
FAIL, причины не установлены; не общий CI PASS. Никаких unrelated fixes или bypass.
Mandatory full suites и Auto/DIRECT/root→UID gates сохранены; локальный L02 принят review.
Новый D01.3 source/CI учитывается отдельно в [отчёте](releases/2026-10-24-desktop-chat-admission-d01-3.md).
Linux updater пока принимает legacy six-file archive; не объявлять полный bundle обновляемым до L08.

## Windows: платформенная и продуктовая интеграция

| ID | Результат | Зависимость | Статус | Критерий завершения |
|---|---|---|---|---|
| W01 | Windows native ↔ broker | D03, D05 / общий core | QUEUED | Модель/provider boundary D05 и MESH/P0/P1 подключены через защищённый broker/FriendsOwner IPC; собственные Windows runtime/readback проверки, не перенос Linux evidence; GUI без постоянного admin. |
| W02 | Windows Auto и recovery | W01 | QUEUED | Общий Go Auto интегрирован с платформенными службами и моделью D05; проверены выбор транспорта, отмена, cleanup/generation fencing и восстановление. Эта интеграция ещё не завершена. |
| W03 | Windows контакты, текст и история | W01, W02 | QUEUED | Пользовательская служба и WinForms выполняют базовый чатовый цикл с существующей identity. |
| W04 | Windows DIRECT/service-only | W03, L01/L02 contract | QUEUED | Чаты при VPN OFF и переходы владения работают на Windows с необходимыми проверками доступа и underlying routing. |
| W05 | Windows голосовые сообщения | W04 | QUEUED | Реализованы принятые запись, отправка, воспроизведение и существующие voice/radio режимы. |
| W06 | Windows фон и уведомления | W05 | QUEUED | Закрытие GUI, уведомления и восстановление пользовательской службы сохраняют принятую семантику. |
| W07 | Windows диагностика и online support | W06 | QUEUED | Экспорт, opt-in согласие, срок действия, отзыв и фоновая отправка соответствуют принятой модели; без автоматического opt-in. |
| W08 | Windows объявления | W07 | QUEUED | Реализованы существующие операции и проверки ролей без изменения прав пользователей. |
| W09 | Windows UI и остальные пользовательские сценарии | W03–W08 | QUEUED | Реальные visual comparisons, список вариантов с отдельными selected-next/active state D05, настройки, активация, приглашения/QR/deep links и согласованные элементы интерфейса. |
| W10 | Полный внутренний Windows installer | W01–W09 | QUEUED | Согласованные GUI, broker/native/RNS и зависимости с достоверными capabilities; сохранены SCM/driver paths и privilege boundary. |
| W11 | Установленная Windows-приёмка | W10 | QUEUED | На установленном кандидате проверены VPN, чаты, фон, recovery, переходы сети и применённый target/profile с заявленными capabilities; cross-build/Wine/headless/model fixture не засчитываются. |
| W12 | Windows обновление | W10, W11 | QUEUED | Совместимая миграция настроек выбора D05 при обновлении; identity/WG keys, активация, Support ID, история, настройки, ссылки и signed floors/счётчики сохранены. |

Windows chat endpoint на проверенном SHA — NOT_INTEGRATED. W10 предшествует завершению
установленной приёмки, даже если отдельные W01–W09 уже проверены в dev environment.
Нет разрешённой Windows-машины/VM/runner — runtime NOT_RUN с точной инструкцией,
а не PASS по Linux cross-build; доступные исходники/пакеты доводятся отдельно.

<a id="release-gates-three-platforms"></a>
## Финальные артефакты и границы выпуска

| ID | Результат | Зависимость | Статус | Критерий завершения |
|---|---|---|---|---|
| R01 | Финальная проверка поставки | L04–L08, W11/W12 | QUEUED | Точные AppImage/DEB/Windows installer, обновления и заявленные возможности согласованы; проверки относятся к финальным артефактам; SHA256/manifests/RU/EN инструкции готовы. Dynamic fleet не заявляется по D05 без отдельной интеграции/приёмки. |

AppImage — основной Linux artifact, DEB дополнительный; legacy archive сохраняется для совместимости.
Windows сохраняет действующий installer/broker/service/driver workflow, не новый формат ради parity.
Обновления сохраняют signed catalogs, digest, anti-rollback, permitted upgrade paths и identity.
Подписи update manifest, installer/Authenticode и driver перечислять отдельно; отсутствующие не выдумывать.
Версии выбирать по desktop-линейке; Android106 соответствие фиксировать feature/core manifest, не номером.
Полный parity installer сейчас0/2, завершённая установленная приёмка0/2.
Source/local tests/CI/build/install/private-test readiness/publication — отдельные состояния.
R01 готовит release/catalog/landing изменения, но НЕ разрешает публичную публикацию.
Исторические [three-platform gates](PLAN.history-2026-10-24.md#release-gates-three-platforms)
сохранены как прошлые обязательства, не как альтернативный текущий NEXT.

## Общие обязательные ограничения и выбор проверок

- Читаем STATUS, выбранный ID и только релевантные исходники/доказательства через [docs map](README.md).
  Исторические NEXT/ACTIVE в архивах и release reports не запускают другую задачу.
- Проверки выбирать по изменённому риску и обязательному gate; сначала адресные проверки,
  шире — при общей зависимости/регрессии/перед приёмкой. Не гонять весь исторический набор после мелкой правки.
- Сохранять точную связь source/artifact/evidence; старые PASS и hashes не переписывать для нового исходника.
- Для D00 только documentary consistency, byte-exact history, новые ссылки и `git diff --check`;
  никаких сборок, pytest, эмулятора, capsule sweep или live-трафика.
- Не менять Android106, действующие пользовательские MESH-сессии, gateway или чужую policy.
  Desktop P1 identities проверять отдельно; точечное операторское решение не блокирует создание installer.
- Native общий, не отдельные Python/C# RS/crypto реализации. Сохранять AWG/TCP, identity/roles/
  certs/revocation/expiry/floors/signed directory, accepted cache semantics и fail-closed traffic policy.
- На целевой ОС проверять TUN/DNS/IPv6/underlying service routes, cleanup при error/cancel/crash,
  negotiated P0/P1, HTTPS, single4MiB + parallel2×2MiB, idle/recovery и export.
  Первичный live-бюджет до32MiB прикладных данных на ОС; не тратить его на ограниченном мобильном тарифе.
- GUI обычного пользователя, ограниченные helper/broker IPC; не ослаблять key storage или защиту ОС.
- Реальные screenshots, а не наличие CSS/строк, закрывают visual gate. Для emulator retain KVM/host GPU,
  2 cores, CPUQuota150%, max180s, stop85°C CPU/80°C GPU; никаких idle/SwiftShader fallback.
- Commit/push каждого завершённого шага по [AGENTS](../AGENTS.md), без force/reset/clean.
  Проверять remote SHA; push не равен CI success, установке или публикации. Секреты/state/capsules/binaries вне Git.

<a id="other-obligations"></a>
## Другие обязательства — HOLD, вне текущей desktop-очереди

Ниже сохранены незакрытые направления, не разрешение начать их или расширить parity106.
Перед возобновлением сверить релевантную дельту, а не принимать старый NEXT за действующий.

| Направление | Что остаётся / источник |
|---|---|
| Android field / P1 cohort | Физические updates106/P1 и cold-bootstrap; Volgograd96 не закрывает Краснодар FIELD-1. [Cohort](releases/2026-10-23-tester-p1-cohort.md). |
| Fleet/control5.2–5.6, gateway recovery6 | Native/Friends/device integration, долговременная AWG/TCP/Android приёмка, independent ingress/recovery. [Исходные обязательства](PLAN.history-2026-10-24.md#глобальные-этапы), [recovery design](reticulum-recovery-design.ru.md). |
| Secrets / disaster recovery | Consumer audit перед удалением originals, production signing acceptance, внешний носитель и восстановление чистого хоста; не считать закрытым по локальным backup. [Архив](PLAN.history-2026-10-24.md#глобальные-этапы). |
| Операции RU/NL | RU SSH timeout, legacy Docker peer-worker unhealthy, RU counters неизвестны. [Snapshot](releases/2026-10-23-vpn-health.md); без рестартов ради диагностики. |
| Local storage / thermal | Сохранить symlinks; live project/Codex migration и reboot automount отдельно. [Migration](releases/2026-10-07-local-storage-migration.md), [GPU/thermal limits](releases/2026-10-23-laptop-thermal-diagnostic.md). |
| Остальной продукт | Doze/OEM/boot/Android13+, iOS/macOS, лицензирование, private security reporting, Windows publisher signing, коммерческий запуск. [Deferred backlog](PLAN.history-2026-10-24.md#отложенные-задачи). Новые VPS/покупки не разрешены. |

<a id="mesh-roadmap"></a>
Home Gateway (phone↔home PC, LAN/NAS/RDP/residential egress) остаётся отдельным design/backlog;
[5A–5G/RNS gates](reticulum/HOME_GATEWAY_DESIGN.md) не закрыты desktop MESH exit.
<a id="multi-carrier-roadmap"></a>
Multi-carrier: после авторизованного Краснодар FIELD-1 и разбора Telemost path;
[Carrier API → WB → VK → failover](PLAN.history-2026-10-24.md#multi-carrier-roadmap).
Ни новые carriers, ни MESH2/MESH3 не входят в parity106.
<a id="django-admin"></a>
Django7.1 (servers/access/payments) зависит от backend/fencing и recovery; нет второй writable
копии leases, платежи идемпотентны, migration/provider/secret store — отдельные решения.
[Сохранённый контракт7.1](PLAN.history-2026-10-24.md#django-admin), [design](design/django-product-plane.ru.md).

## История и завершение шага

[Полный прежний PLAN](PLAN.history-2026-10-24.md), [STATUS](STATUS.history-2026-10-24.md),
[phase22](releases/2026-10-23-desktop-parity106.md#linux-user-chat-admission-and-existing-exit-handoff-2410-phase22),
[отчёт D00](releases/2026-10-24-desktop-parity106-d00.md).
**После отчёта D01.3-R остановиться. NEXT — review D01.3-R;
без автоматического перехода к Linux/Windows/iOS или live-операциям.**
