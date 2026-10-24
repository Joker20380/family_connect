# Текущее состояние / Current state

Срез D00, 24.10.2026. Проверены `main`, чистая исходная рабочая копия и `origin/main`:
`664342a6566792a4ea621274a369bcd6b6012143` — исходный source checkpoint.
D00 меняет только навигацию и документы, не продукт или его версии.
**Следующая отдельная задача: D01. Не начинать её автоматически после D00.**

## Цель и порядок работы

Довести существующие Linux GTK4/libadwaita и Windows WinForms до функционального
и визуального соответствия принятой Android beta106-recovery, включая мессенджер,
голос, уведомления, объявления, настройки, приглашения, диагностику и обновление.
Сохранить полезные desktop-функции, модель привилегий и пользовательские данные.
Общий PARITY PASS не достигнут; процент по объёму исходников не является приёмкой.
Работа идёт отдельными ограниченными задачами из [PLAN](PLAN.md), без автоперехода.

## Android reference / exact pins

- APK: `FamilyConnect-0.1.18-beta106-recovery.apk`, принятый native105.
- APK SHA256: `242855c43e889e708234ce2f687fa02d37bccb1eee408904f09216b6abd8f020`.
- Signer SHA256: `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
- native105 SHA256: `37ba4fac656811dd979688a274f45aed85a3aa567f1fafb3987a81c020fa91f1`.
- Точные APK/source/native inventories и 175 общих pins: [reference manifest](../clients/shared/android106-reference.json).
- Source capsule: `state-client-build/owner-diagnostic106-20261022/android-source`;
  delivery: `state-client-build/owner-diagnostic106-20261022/delivery/`.
  Inventory 2073 файлов: `8574228fc809fdbd67b3d92680e09c979fe930599a47e4ed1b47fd30f872ed0c`.
- [Chat pins](../clients/shared/android106-chat.json), [UI contract](../clients/shared/android106-ui.json),
  [feature matrix и исходные наблюдения](releases/2026-10-23-desktop-parity106.md#desktop_feature_parity).
  Android-код в корне и лабораторные fixtures не заменяют принятую source capsule.
- Принятая база: P1 effective RS32/32 + согласованный CREDIT128, P0/LEGACY64,
  health102, cancel/timeout103, reorder104, pressure105, bounded JSON-export106.
  RS согласуется до Family TLS, Mux ALPN не подменяет RS; профиль зависит от обоих концов.

## Состояния поставки — не смешивать

| Уровень | Подтверждённое состояние |
|---|---|
| SOURCE | Последний завершённый продуктовый checkpoint — phase22; сохранён в baseline выше. D00 — документация. |
| LOCAL TESTS | Phase22: 1218 PASS в описанном локальном наборе, без failures/errors/skips; существующий GI warning. Шесть Linux native packages: race PASS. Не полный pytest и не CI. |
| CI | После baseline push наблюдались отдельные dependency/collection failures; [точные runs/jobs](PLAN.md#ci-evidence). CI PASS не заявлен; новый push может запустить CI, но не подтверждает результат. |
| BUILT | Linux native-r18, Windows native-r14 cross-build, unsigned Linux system/native/RNS component-r18. **Полный parity installer: 0/2.** |
| INSTALLED | **Завершённая установленная приёмка: 0/2.** Полный кандидат не принят на Linux/Windows; Windows runtime NOT_RUN. |
| PUBLISHED | Parity-кандидаты не опубликованы. Linux0.2.11 / Windows0.2.15 не менялись; существующие публичные каталоги/ссылки в D00 не изменялись и заново не проверялись. |

## Последний завершённый checkpoint: phase22

[Phase22, 24.10 08:53 CEST и остановка 08:55](releases/2026-10-23-desktop-parity106.md#linux-user-chat-admission-and-existing-exit-handoff-2410-phase22).
Linux ChatOwner подключён к **EXISTING_EXIT** через отдельный UID/device-bound root
chat endpoint; fixed API/mailbox используют существующего MESH owner, не второй VPN worker.
**SYSTEM — обычная маршрутизация ОС, НЕ protected-underlying DIRECT.**
Общий Go service-only adapter существует; **Linux host lifecycle ещё NOT_INTEGRATED**.
Требуется **одно активное владение транспортом**, не вечный PID: worker имеет свой lifecycle.
**Windows public/native chat endpoint на baseline — NOT_INTEGRATED.**

Границы доказательств phase22:
- Реальные Unix framing/SO_PEERCRED/SCM_RIGHTS, 64KiB duplex/half-close, cancel,
  deadlines, capacity и FD cleanup проверены в изолированном same-user fixture.
  Ожидаемый root UID заменён UID fixture; установленная root/user граница NOT_RUN.
- Native lane/session в host fixture синтетические: это не media/TUN/gateway egress PASS.
- Реальные ChatOwner/encrypted store, disposable identity proofs и локальные ChatAccess
  handlers: register/revoke/reopen. Pending node не выдавался за доставку сообщений.
- 175 общих / 2073 capsule checks и шесть chat pins — исторический PASS phase22;
  в D00 они не запускались. Наборы PASS перекрываются, их числа не суммируются.
- Phase22 не снимала новые UI screenshots. Имеющиеся Android GPU/GTK captures —
  частичные доказательства, не полный visual parity и не Windows runtime acceptance.
- [Source checkpoint](releases/2026-10-24-source-checkpoint.md) отдельно описывает
  последующую EOF/whitespace подготовку; старые hashes не выданы за тест нового исходника.

## Артефакты и ограничения обновления

Все три файла находятся только в `state-client-build/desktop-parity106-20261024/`:
`bridge-linux-r18/fc-mesh`, `bridge-windows-r14/fc-mesh.exe`,
`mesh-system-r18/FamilyConnect-MESH-system-amd64.tar.gz`.
[Точные SHA256, inventory и требования](releases/2026-10-23-desktop-parity106.md#internal-artifacts-and-upgrade-boundary).
Component-r18: 98 members, 22 root / 4 common modules; Linux x86_64 systemd254+,
resolved/iproute2/polkit/TUN/Python3 и согласованный GUI. Это НЕ полный AppImage/DEB.
Новых update-manifest/Authenticode/driver signatures нет; подписи не взаимозаменяемы.
Linux updater принимает **legacy six-file archive**; переход на полный bundle ещё
требует реализации (L08). Полный внутренний пакет (L03/W10) предшествует установленной приёмке.
Identity/history/settings сохранены в локальных fixtures, но installed upgrade ещё не принят.
D00 ничего не устанавливает: runtime rollback не нужен; прежние установки/state сохраняются.

## Блокеры / оставшаяся реализация

- D01/D02: httpx/LXMF/GI и imports owner_handoff/prepare; локальные 1218 PASS не отменяют CI failures.
- D03: `provisioning/chat_bridge.py`, `ChatHTTP.stream`: синтетический вызов фактического
  метода direct400/401/403/409 + TransportError при закрытии даёт `fallback_calls=1`.
  Это сообщённое воспроизведение логики, НЕ проверка установленного клиента и не новый запуск D00.
  Историческое общее утверждение phase22 о terminal errors недостаточно для этого случая;
  исправление/адресные тесты: [D03](PLAN.md#d03), [tests](../tests/test_chat_bridge_http.py).
- L01/L02: protected DIRECT и host service-only/handoff; L03–L08: полный Linux bundle,
  installed VPN/messenger/recovery/visual/upgrade. Текущий existing-exit не закрывает эти задачи.
- W01–W12: Windows native↔broker, Auto/recovery и продуктовые функции, затем полный installer,
  installed runtime и upgrade. Cross-build/Wine/headless не заменяют Windows TUN/driver acceptance.
- R01: конечные точные пакеты и проверки их установки/обновления; публикация отдельно.

## Неизменные ограничения

- Не пересобирать/публиковать Android106, не трогать активные MESH-сессии и общий gateway ради desktop.
- P1 разрешён только трём согласованным Android-устройствам; desktop identities не считаются
  разрешёнными автоматически. Точечная политика требует отдельного операторского решения, не global/FIELD grants.
- Не копировать Android identity/Support ID на ПК; сохранять старые ключи, историю, настройки,
  активацию и `familyconnect://`. Не ослаблять TLS/Family/roles/revocation/expiry/floors/directory.
- Не включать Q1/TLS packing/FEC/QUIC/FIXED4M или исследовательские SACK/timebase patches.
  Не выпускать неподдерживаемый пользовательский трафик напрямую ради smoke.
- Live-бюджет при отдельной приёмке: до32MiB прикладных данных на ОС, нормальный Wi-Fi/Ethernet;
  media overhead/фон учитывать отдельно. Android field check не блокирует локальную desktop-разработку.
- Будущие emulator checks: KVM + подтверждённый host NVIDIA GPU, 2 cores, CPUQuota150%,
  максимум180s, stop85°C CPU/80°C GPU; без SwiftShader fallback/idle emulator.
  [Тепловой инцидент и ограниченный GPU capture](releases/2026-10-23-laptop-thermal-diagnostic.md).
- Проверки выбирать по изменённому риску и обязательному gate; не повторять весь исторический набор
  без причины. Source push ≠ CI PASS ≠ installation ≠ publication. [Правила](../AGENTS.md).
- Capsules, приватные доказательства, бинарники, ключи и state остаются локально, вне Git.

## Другие незакрытые обязательства — не текущие задания

- Закрытая Android-группа: физические tester updates106/P1 и cold-bootstrap ещё не подтверждены;
  Volgograd96 положителен, но не равен106/P1/Краснодар. [Cohort report](releases/2026-10-23-tester-p1-cohort.md).
- RU SSH banner timeout / legacy Docker peer-worker unhealthy и неизвестные RU live counters:
  [операционный follow-up](releases/2026-10-23-vpn-health.md), без диагностических рестартов.
- Local storage: сохранить symlinks; оставшаяся миграция live project/Codex и reboot automount —
  отдельное maintenance после остановки writers. [Receipt](releases/2026-10-07-local-storage-migration.md).
- Fleet/control5.2–5.6, длинная AWG/TCP/Android приёмка, vault signing/consumer audit/external backup/full DR,
  gateway recovery6, Home Gateway, multi-carrier после FIELD-1, Django7.1/payments,
  licensing/private reporting/Windows publisher signing/iOS/macOS — [отложенные обязательства](PLAN.md#other-obligations).
  Они не закрыты D00 и не добавлены в desktop scope.

## История и один следующий шаг

[STATUS до D00](STATUS.history-2026-10-24.md) и [PLAN до D00](PLAN.history-2026-10-24.md)
сохранены целиком; старые NEXT/ACTIVE/checkpoints — история, не параллельные задания.
[Отчёт D00](releases/2026-10-24-desktop-parity106-d00.md) фиксирует сохранность и границы.
**NEXT: D01 — зависимости Linux/desktop CI, только отдельной задачей.**
