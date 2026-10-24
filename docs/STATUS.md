# Текущее состояние / Current state

Срез L01, 24.10.2026. Вход: чистая `main`, HEAD = проверенный `origin/main`
`a1d79001be2a20dd72cb5f75607843218bbaa428`; phase22 baseline — `664342a`.
**L01 выполнен в локальном Linux source/native/kernel scope; NEXT — review L01.**
[L01](releases/2026-10-24-linux-chat-direct-l01.md): ChatOwner/daemon используют отдельный
root DIRECT endpoint, fixed chat API и mailbox только из root-проверенной регистрации.
Native underlay bind/mark до connect; SYSTEM fallback отсутствует в этом пути.
UID/device/chat-key/sequence/expiry и AF_UNIX relay ограничены; VPN owner не создаётся.
Локально: 141 chat/admission/D03/package + 49 mailbox/owner PASS; Go/race и isolated
kernel с synthetic TLS peer PASS. Installed/live, L02 и полные установщики NOT_RUN.
`bff34eb` CI: Client Linux/Auto protocol/AWG/TCP PASS; full control/phase0/Docker и voice FAIL.
Первый новый kernel gate FAIL; harness-only `edc79c2` переносит test-worker из writable
`/opt` под trusted `/root`, не ослабляя admission: Auto bridge/isolated DIRECT kernel CI **PASS**.
На `edc79c2` phase0/tests FAIL; Docker: 2976 passed / 53 failed / 109 skipped,
exit1; другие filtered jobs NOT_RUN.
Evidence и разные SHA — в отчёте; старые counts не переносятся.
[D03](releases/2026-10-24-chat-http-terminal-d03.md) и [D04](releases/2026-10-24-auto-lifecycle-d04.md) review accepted; D02.1 collection/import
isolation и D02.2 public-reference приняты. Dependency-части D01.1/D01.2 приняты;
их PARTIAL и общая CI-приёмка D01 не закрыты.
[D05 review accepted](releases/2026-10-24-desktop-provider-d05.md): target/selected-next, проверенное
assignment и applied metadata используются Linux NormalOwner/Platform/GuardedHost.
Legacy gateway_id неизвестен; assignment только после fresh fetch/floor/readback/inspect,
applied только после guard.ready. Refresh не вызывает configure/apply/close; IPC не расширен.
Clean export: provider/model/platform/native/catalog 162 PASS, ownership/service/chat 213 PASS,
0 failures/errors/skips. Native normal-stdio проверен с синтетическими материалами;
installed/live/F-01 и dynamic fleet не приняты. Code `c53265d` pushed/remote-verified:
Auto bridge Linux/AWG/TCP PASS, Client Linux job завершён PASS (перепроверен в L01).
Control/phase0: каждый 2930 passed / 54 failed / 0 errors / 107 skipped, exit1;
Docker: 2929 passed / 53 failed / 0 errors / 109 skipped. Voice GTK Return gate FAIL, причина неизвестна; не исправлялся и не объявляется flaky.
D04 evidence уточнён: на `b41e1ad` одинаковый набор 54 failures в control/phase0/Docker;
docs-only phase0 `3f9854a` завершился FAILURE отдельно от code SHA. D01 остаётся открыт.
Review коррекции D02.1-R и [fleet-документации `1725656`](releases/2026-10-24-desktop-fleet-boundary.md)
завершён. [Граница desktop/fleet](desktop-architecture.md#desktop-fleet-boundary) сохраняется:
D05 реализует только внутреннюю Linux-границу; W01/W02, UI/миграция и fleet gates остаются отдельными.
[D02.2 DONE, review принят](releases/2026-10-24-rns-reference-d02-2.md): public mappings
с прежними accepted pins; clean export 49 passed / 1 прежний skip, collection 3051/0 errors;
public verifier и настоящий `--capsule` (2073 files + APK/native hashes) PASS.
Исторические CI counts `da8670e` сохранены в отчёте, не переносятся на D05.
[D02.1-R PARTIAL, коррекция принята review](releases/2026-10-24-historical-runner-d02-1-r.md): bootstrap vector и original API
добавлены; retained inputs явно перечислены, preflight/snapshot fail-closed. Чистая collection
3031/0 errors, адресные 110 passed. Полный исторический запуск **NOT_RUN**: у delivery-check,
Java runtime/classes и трёх JARs нет подтверждённых artifact pins; существование файлов не PASS.
Collection/import isolation D02.1 подтверждено review. Комплектность исторического replay ещё
не закрыта. Полные suites локально не запускались; старые CI counts ниже — только `6a0a982`.
Code `85b29da` pushed/remote-verified; по отчёту D02.1-R control/phase0/tests/Docker build
были IN_PROGRESS без full pytest counts; в документационном checkpoint CI не перепроверялся.
[D02.1 DONE](releases/2026-10-24-fixture-boundaries-d02-1.md), code `6a0a982`: чистый export —
collection 2977 + 9 errors → 2996 / 0 errors; helpers/import/runner — 75 passed.
В трёх CI окружениях collection errors = 0; полный pytest остаётся FAIL (56 failures):
control/phase0 2834 passed, 106 skipped; Docker 2832 passed, 108 skipped. Остались capsule/
reference, nginx contract, expiry, privacy и socket failures; не исправлялись.
Шесть исторических overlay-файлов сохранены и отделены; исторический runner в D02.2 не менялся.
[D01.2 PARTIAL](releases/2026-10-24-control-ci-d01-2.md): на pushed `07b52e3` Python3.13
strict imports и адресные gates PASS в control/phase0/tests/Docker tests-stage;
Docker root 22 passed, адресные 59 passed. Каждый полный suite прерван: 9 collection
errors owner_handoff/prepare, exit 2 (D02). Общий CI FAIL; последующие GUI/package/cargo/
failover проверки не выполнены. Runtime/fixtures/collection policy не менялись.
[D01.1](releases/2026-10-24-desktop-ci-d01-1.md): локальные реальные импорты PASS,
адресные 59 passed; локальный desktop 877 passed / 64 skips / 0 failures/errors.
На pushed `26f71d6` imports/адресные CI PASS; полный suite FAIL: отсутствующая RNS capsule,
в AWG также Auto lifecycle assertion. Подробности и точные counts — в отчёте; продукт/fixtures не исправлялись.

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
| SOURCE | L01 — protected DIRECT для fixed chat API/mailbox поверх принятых D03/D04/D05; не новая поставка. |
| LOCAL TESTS | L01: 141 chat/admission/D03/package + 49 mailbox/owner PASS; Go/race и synthetic-peer kernel PASS. Полный pytest и installed/live локально NOT_RUN. |
| CI | Новые L01 results — в [отчёте](releases/2026-10-24-linux-chat-direct-l01.md). D05 `c53265d`: Client/Linux/Auto/AWG/TCP PASS; control/phase0 по 54, Docker 53 failures; GTK Return FAIL. D01 открыт. |
| BUILT | Linux native-r18, Windows native-r14 cross-build, unsigned Linux system/native/RNS component-r18. **Полный parity installer: 0/2.** |
| INSTALLED | **Завершённая установленная приёмка: 0/2.** Полный кандидат не принят на Linux/Windows; Windows runtime NOT_RUN. |
| PUBLISHED | Parity-кандидаты не опубликованы. Linux0.2.11 / Windows0.2.15 не менялись; существующие публичные каталоги/ссылки в D00 не изменялись и заново не проверялись. |

## Продуктовый baseline: phase22

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

- D01.1/D01.2 PARTIAL, dependency gates приняты; review D02.1 collection/import isolation и D02.2 public-reference принят. D02.1-R historical replay PARTIAL/NOT_RUN. Остальные CI failures требуют отдельной оценки, не расширяют L01 автоматически. Общий D01/CI acceptance открыт до полного PASS.
- D03/D04/D05 review accepted; NEXT review L01. W01/W02, L07/W09, L08/W12 и installed/live gates не закрыты.
- D03: [исправление и детерминированные регрессии](releases/2026-10-24-chat-http-terminal-d03.md)
  сохраняют HTTP/TLS/invalid_response/timeout/cancellation при ошибке teardown.
  Это локальная логика с synthetic transport, НЕ installed/live delivery PASS;
  review D03/D04 принят; D05 не расширяет fixed chat DIRECT/service-only scope.
- L01 — local protected DIRECT source/native/kernel; L02 service-only/handoff не начат.
  L03–L08: полный Linux bundle, installed VPN/messenger/recovery/visual/upgrade остаются gates.
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
**После отчёта L01 остановиться. NEXT — review L01; L02 и прочие задачи автоматически не начинать.**
