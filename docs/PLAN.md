# План / bounded desktop parity106 queue

## Current engineering priority / Текущий critical path

Цель — тот же Family Connect на Linux/Windows, что принятая Android beta106-recovery,
а не отдельные реализации продукта. [Текущий срез](STATUS.md) — источник текущего состояния.
Продуктовый checkpoint: phase22, source baseline `664342a6566792a4ea621274a369bcd6b6012143`.
D00 — организация документации; следующие строки являются очередью, не разрешением на автозапуск.
**Текущая разрешённая задача: только D01.1. После отчёта остановиться.**

Порядок по умолчанию: D01.1 → D01.2 → D02 → D03 → Linux → Windows → R01.
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
| D01 | Зависимости Linux/desktop CI | D00 | IN_PROGRESS | DONE только после D01.1 и D01.2; необходимые httpx/LXMF/GI доступны без скрытия обязательных тестов. |
| D01.1 | Client builds/linux, AmneziaWG pilot, TCP pilot | D00 | IN_PROGRESS | Python3.12: реальные httpx/LXMF/RNS/GI и ChatOwner/ChatBridge/chat_daemon; адресные и полный desktop pytest PASS в трёх jobs на pushed SHA. Остальные этапы отдельно. |
| D01.2 | Linux control, phase0, Dockerfile.control test-stage | D01.1 | QUEUED | Исправлены зависимости соответствующих Python3.13/test-stage окружений; обязательные suites сохранены, результаты на pushed SHA; fixture scope остаётся D02. |
| D02 | Сбор и импорты исследовательских fixtures | D01 | QUEUED | Устранены owner_handoff/prepare import errors; обязательные проверки имеют явный воспроизводимый запуск; границы архивных экспериментов задокументированы. |
| D03 | Окончательные ошибки ChatHTTP | D02 | QUEUED | HTTP400/401/403/409, TLS и установленный invalid_response сохраняются при ошибке teardown; разрешённый transient fallback продолжает работать. |

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

D01.1: [отчёт и текущая проверка](releases/2026-10-24-desktop-ci-d01-1.md).
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

## Linux: интеграция, полный кандидат, затем установленная приёмка

| ID | Результат | Зависимость | Статус | Критерий завершения |
|---|---|---|---|---|
| L01 | Защищённый DIRECT для чатов | D03 | QUEUED | Фиксированные chat API/mailbox используют корректный underlying-маршрут с действующей авторизацией; отсутствует общий пользовательский bypass. |
| L02 | MESH service-only и передача владения | L01 | QUEUED | Чаты работают при VPN OFF; OFF→ON→OFF сохраняет одно активное владение; проверены drain, expiry, отмена и поздние результаты. |
| L03 | Полный внутренний Linux-кандидат | L02 | QUEUED | Согласованы GUI, пользовательские службы, root-helper, native/RNS, зависимости и установка; зафиксирован точный состав полного пакета. |
| L04 | Установленный Linux VPN | L03 | QUEUED | На установленном кандидате подтверждены реальные AWG/TCP/MESH/Auto, P0/P1, DNS/HTTPS и передачи; не CLI/echo/SOCKS smoke. |
| L05 | Установленный Linux-мессенджер | L03, L04 | QUEUED | DIRECT/MESH-доставка без VPN и с VPN, контакты/текст/голос, история и фоновые события подтверждены на реальных компонентах. |
| L06 | Linux recovery | L04, L05 | QUEUED | Ограниченные loss/return, sleep/resume, рестарт службы и отмена проходят с корректной очисткой, backoff и одним reconnect owner. |
| L07 | Linux visual parity | L03, L06 | QUEUED | Реальные окна: согласованные экраны/состояния, RU/EN, DPI100/125/150/200%, resize/focus/Tab/Enter/Escape сопоставлены с точным Android-эталоном. |
| L08 | Linux updater и сохранение данных | L03, L07 | QUEUED | Реализован и проверен переход со старого поддерживаемого установленного клиента на полный bundle; identity, история, настройки и ссылки сохранены. |

Phase22 уже подключила Linux ChatOwner к EXISTING_EXIT. SYSTEM пока не protected DIRECT.
Общий Go service-only есть, но host lifecycle ещё не завершён. Одно активное владение
не означает вечный PID: текущий worker имеет собственный жизненный цикл.
Полный внутренний пакет L03 обязателен перед закрытием L04–L08; system-only component-r18 недостаточен.
Linux updater пока принимает legacy six-file archive; не объявлять полный bundle обновляемым до L08.

## Windows: платформенная и продуктовая интеграция

| ID | Результат | Зависимость | Статус | Критерий завершения |
|---|---|---|---|---|
| W01 | Windows native ↔ broker | D03 / общий core | QUEUED | MESH/P0/P1 подключены через защищённый платформенный IPC и проверены на Windows; GUI не требует постоянного admin. |
| W02 | Windows Auto и recovery | W01 | QUEUED | Общая политика интегрирована с платформенными службами; проверены выбор транспорта, отмена и восстановление. |
| W03 | Windows контакты, текст и история | W01, W02 | QUEUED | Пользовательская служба и WinForms выполняют базовый чатовый цикл с существующей identity. |
| W04 | Windows DIRECT/service-only | W03, L01/L02 contract | QUEUED | Чаты при VPN OFF и переходы владения работают на Windows с необходимыми проверками доступа и underlying routing. |
| W05 | Windows голосовые сообщения | W04 | QUEUED | Реализованы принятые запись, отправка, воспроизведение и существующие voice/radio режимы. |
| W06 | Windows фон и уведомления | W05 | QUEUED | Закрытие GUI, уведомления и восстановление пользовательской службы сохраняют принятую семантику. |
| W07 | Windows диагностика и online support | W06 | QUEUED | Экспорт, opt-in согласие, срок действия, отзыв и фоновая отправка соответствуют принятой модели; без автоматического opt-in. |
| W08 | Windows объявления | W07 | QUEUED | Реализованы существующие операции и проверки ролей без изменения прав пользователей. |
| W09 | Windows UI и остальные пользовательские сценарии | W03–W08 | QUEUED | Завершены реальные visual comparisons, настройки, активация, приглашения/QR/deep links и согласованные элементы интерфейса. |
| W10 | Полный внутренний Windows installer | W01–W09 | QUEUED | Установщик содержит согласованные GUI, broker/native/RNS и зависимости; сохранены SCM/driver paths и privilege boundary. |
| W11 | Установленная Windows-приёмка | W10 | QUEUED | На установленном кандидате проверены VPN, чаты, фон, recovery и переходы сети; cross-build/Wine/headless не засчитываются. |
| W12 | Windows обновление | W10, W11 | QUEUED | Обновление предыдущей поддерживаемой версии сохраняет identity, ключи, историю, настройки и пользовательские ссылки. |

Windows chat endpoint на проверенном SHA — NOT_INTEGRATED. W10 предшествует завершению
установленной приёмки, даже если отдельные W01–W09 уже проверены в dev environment.
Нет разрешённой Windows-машины/VM/runner — runtime NOT_RUN с точной инструкцией,
а не PASS по Linux cross-build; доступные исходники/пакеты доводятся отдельно.

<a id="release-gates-three-platforms"></a>
## Финальные артефакты и границы выпуска

| ID | Результат | Зависимость | Статус | Критерий завершения |
|---|---|---|---|---|
| R01 | Финальная проверка поставки | L04–L08, W11/W12 | QUEUED | Точные AppImage/DEB/Windows installer и механизмы обновления согласованы; необходимые проверки относятся к финальным артефактам; SHA256/manifests/RU/EN инструкции готовы. |

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
**После D01.1 остановиться. NEXT: D01.2 только после принятия D01.1 и отдельного запроса.**
