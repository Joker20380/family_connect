# План / bounded desktop parity106 queue

## Current engineering priority / Текущий critical path

Цель — тот же Family Connect на Linux/Windows, что принятая Android beta106-recovery,
а не отдельные реализации продукта. [Текущий срез](STATUS.md) — источник текущего состояния.
Продуктовый checkpoint: phase22, source baseline `664342a6566792a4ea621274a369bcd6b6012143`.
D00 — организация документации; следующие строки являются очередью, не разрешением на автозапуск.
**Разрешён только D02.2. Review D02.1-R и fleet-документации `1725656` принят;
D02.1-R остаётся PARTIAL/NOT_RUN, D05 QUEUED и не начинается.**

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
| D02 | Сбор и импорты исследовательских fixtures | dependency-части D01.1/D01.2 приняты | IN_PROGRESS | D02.1 и D02.2 завершены; не ждёт полного зелёного CI, который сам должен разблокировать. Общая CI-приёмка D01 остаётся отдельным обязательным gate. |
| D02.1 | Девять collection errors, историческая overlay-suite, изоляция импортов | окружения D01.1/D01.2 готовы | DONE (collection/import isolation) | Review подтвердил границы; `6a0a982`: clean collection 2996/0 errors, helpers/import/runner 75 PASS; три CI full suites с 56 residual failures. Историческая воспроизводимость отдельно в D02.1-R. |
| D02.1-R | Комплектность исторического runner | review D02.1 | PARTIAL | Коррекция принята review. Vector/original API, явные retained inputs, preflight до pytest; 110 адресных PASS. Historical suite NOT_RUN: нет anchored pins delivery-check, Java runtime/classes и 3 JARs; полный replay не обеспечен и в D02.2 не выполняется. |
| D02.2 | RNS/reference checks без локальной capsule в обычном CI | review коррекции D02.1-R принят | IN_PROGRESS | [Evidence](releases/2026-10-24-rns-reference-d02-2.md): явные public mappings, прежние accepted hashes, readiness APK/inventory linkage и строгий --capsule. Clean export: 49 passed/1 прежний skip, collection 3051/0 errors; real capsule 2073 PASS. Остаётся зафиксировать CI pushed SHA, затем отдельный review D02.2. |
| D03 | Окончательные ошибки ChatHTTP | D02 | QUEUED | HTTP400/401/403/409, TLS и установленный invalid_response сохраняются при ошибке teardown; разрешённый transient fallback продолжает работать. |
| D04 | Auto stop/start lifecycle | D02 | QUEUED | Детерминированное воспроизведение и исправление с одним владельцем, завершённой cleanup и generation fencing; до дальнейшей Linux-интеграции. |
| D05 | Минимальная внутренняя модель выбора/назначения/активной сессии и граница существующего provider | D03, D04 | QUEUED | [Адресные критерии](desktop-architecture.md#desktop-fleet-acceptance): разные сущности, устойчивый ID на fixture 2×NL+DE, refresh без apply/reconnect, stale callback отклонён, строгий legacy RU/NL и реальные capabilities. Не production fleet/F-01 live. |

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
Сообщённое синтетическое воспроизведение фактического метода:
`direct400/401/403/409 + TransportError при закрытии → fallback_calls=1`.
Это проверка логики с synthetic transport, не установленного клиента; D00 её не перезапускает.
Не переписывать прошлые phase22 PASS как доказательство отсутствия этого дефекта.
Проверить сохранение первой окончательной причины (HTTP/TLS/invalid_response) при teardown,
отсутствие слабого fallback после отказа авторизации и разрешённый transient fallback.

### D04: наблюдение, не доказанная причина CI

`clients/linux/auto_service.py`: DISCONNECTED может публиковаться до завершения cleanup,
а `start` отклоняется при несброшенном `self.thread`. Связь с конкретным CI assertion
из D01.1 пока не доказана. В D01.2 только фиксируем; D04 не выполняется.

<a id="d05"></a>
### D05: локальная подготовка к расширяемому парку, не fleet-приёмка

[Основной контракт](desktop-architecture.md#desktop-fleet-boundary) — **планируемая граница;
реализация ещё не выполнена**. После D03/D04, без зависимости от production fleet,
новых VPS или F-01 live. D05 задаёт общую модель/provider boundary; W01/W02 используют
её при продуктовой Windows-интеграции, обратной зависимости D05 → W01/W02 нет.
Модельные/отрицательные проверки выполняются адресно в D05; миграция — L08/W12,
полная установленная приёмка — L04/W11/R01. UI/model fixture не доверенный assignment.
L01/L02/W04 не расширяются за пределы fixed chat DIRECT/service-only.
Документационный checkpoint не закрывает D01/D02/D05 или fleet; проверки D05/F-01 NOT_RUN.

## Linux: интеграция, полный кандидат, затем установленная приёмка

| ID | Результат | Зависимость | Статус | Критерий завершения |
|---|---|---|---|---|
| L01 | Защищённый DIRECT для чатов | D03, D04 | QUEUED | Фиксированные chat API/mailbox используют корректный underlying-маршрут с действующей авторизацией; отсутствует общий пользовательский bypass. |
| L02 | MESH service-only и передача владения | L01 | QUEUED | Чаты работают при VPN OFF; OFF→ON→OFF сохраняет одно активное владение; проверены drain, expiry, отмена и поздние результаты. |
| L03 | Полный внутренний Linux-кандидат | L02, D05 | QUEUED | Согласованы GUI, пользовательские службы, root-helper, native/RNS, зависимости и установка; capabilities соответствуют точному составу реально интегрированного пакета. |
| L04 | Установленный Linux VPN | L03 | QUEUED | На установленном кандидате подтверждены реальные AWG/TCP/MESH/Auto, P0/P1, DNS/HTTPS и передачи, применённый target/profile и заявленные capabilities; не CLI/echo/SOCKS или model fixture. |
| L05 | Установленный Linux-мессенджер | L03, L04 | QUEUED | DIRECT/MESH-доставка без VPN и с VPN, контакты/текст/голос, история и фоновые события подтверждены на реальных компонентах. |
| L06 | Linux recovery | L04, L05 | QUEUED | Ограниченные loss/return, sleep/resume, рестарт службы и отмена проходят с корректной очисткой, backoff и одним reconnect owner. |
| L07 | Linux visual parity | L03, L06 | QUEUED | Реальные окна: согласованные экраны/состояния, список вариантов и отдельные selected-next/active state по D05, RU/EN, DPI100/125/150/200%, resize/focus/Tab/Enter/Escape; сопоставление с точным Android-эталоном без изменения Android106. |
| L08 | Linux updater и сохранение данных | L03, L07 | QUEUED | Переход со старого поддерживаемого клиента на полный bundle и совместимая миграция настроек выбора D05; identity/WG keys, активация, Support ID, история, настройки, ссылки и signed floors/счётчики сохранены. |

Phase22 уже подключила Linux ChatOwner к EXISTING_EXIT. SYSTEM пока не protected DIRECT.
Общий Go service-only есть, но host lifecycle ещё не завершён. Одно активное владение
не означает вечный PID: текущий worker имеет собственный жизненный цикл.
Полный внутренний пакет L03 обязателен перед закрытием L04–L08; system-only component-r18 недостаточен.
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
**После отчёта D02.2 остановиться. NEXT — review D02.2;
без автоматического перехода к D03/D04/D05/Linux/Windows/iOS или live-операциям.**
