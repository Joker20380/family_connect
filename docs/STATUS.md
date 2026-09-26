# Текущее состояние / Current state

- production и current released versions этой задачей не менялись
  (Android beta51/code51, Linux0.2.11, Windows0.2.15).
- active engineering critical path — **5N: Restricted WebRTC Android→EU**
  (Telemost VP8 → Linux EU gateway → TCP+DNS → Internet).
- ближайший runtime milestone — **WEBRTC-EU-1 / 5N.1**.
- все WEBRTC-EU gates пока **NOT RUN**.

26.09 активация (WIP): начато упрощение invitation/activation. Сервер Friends:
read-only authenticated recovery `POST /friends/device/status` и purpose `status`
(не расходует приглашение), canonical URL `/i/` (redirect совместимость с
`/invite/`), smart landing page с одним primary CTA и без checkbox/инструкций,
QR = canonical URL; клиенты: `FriendsAccessAndroid.deviceStatus()` + recovery при
старте, Python `FriendsClient.device_status()`; тесты server/client (65+5 passed).
Fresh-install sideload активация **не** заявляется fully automatic: Flow A
(приложение установлено, 1 действие) и Flow B (sideload: возврат на landing +
«Открыть», 3–4 действия). Real-device Android E2E acceptance ещё НЕ пройден;
версии/production/WEBRTC gates не менялись.
[design](design/activation-simplification-design.ru.md),
[android note](design/android-sideload-deferred-bootstrap.ru.md).

26.09: [аудит использования и сбоев VPN](releases/2026-09-26-vpn-health.ru.md).
22 устройства/18 действующих (+4 с24.09); NL12 с handshake<24ч,4 свежих,
3–4 передают трафик; RU0. Найдена история sysstat: AWG около26.7ГиБ с24.09
до26.09 08:40UTC, в основном NL; средний CPU25.09 RU20.3%/NL5.2%.
25.09 AWG restart NL7с/RU20с; RU снова stop-sigterm timeout, оба после
unattended-upgrade libexpat1. Во время чтения журналов высокий iowait и
тайм-ауты chat-sync; затем sync success, к08:50UTC iowait снизился на обоих: RU6.1%/NL5.8%.
Открыты: дисковые задержки (отдельная диагностика), alerts sync/HTTP, история
устройств/TCP, сквозная клиентская проверка. 26.09 исправлено завершение RU AWG
по SIGTERM: TimeoutStopSec=20→90 (шаблон install-awg.py + drop-in на RU),
чистая остановка1с вместо timeout20с/SIGKILL; rollback — удалить drop-in.
Production/версии не менялись.
26.09 Android: в исходники главного экрана Friends добавлен выбор сервера
с флагом и нагрузкой на момент выбора (RU/NL, `server-load.json`, кэш15с).
Android beta51/code51, Linux0.2.11 и Windows0.2.15 собраны и опубликованы
(APK/discovery/invite, desktop GitHub/HTTPS, Windows catalog sequence11) —
см. [отчёт](releases/2026-09-26-server-list-crossplatform.ru.md).
26.09 Linux: подписанный updater-канал поднят до 0.2.11 (`updates/pilot.json`
sequence9, release `v0.2.11`); ранее клиент показывал «последняя версия», потому
что каталог указывал на 0.2.9. Сборка Linux-архива сделана воспроизводимой.
26.09 Linux UI: в исходниках вкладка «Маршрут» заменена на «Статистика»
(трафик сессии, суммарные байты/длительность, нагрузка NL/RU), профиль и
«Проверить IP» перенесены на «Статус»; версия0.2.11 и каталоги не менялись —
см. [отчёт](releases/2026-09-26-linux-stats-tab.ru.md).

25.09: лицензирование опубликовано в GitHub main, commit
`aa3ed9f801a83a4808df3352abc300d235a7c42c`: LICENSE, notices, audit и README RU/EN.
Публичный LICENSE скачан по immutable commit и побайтно совпал с проверенным
локальным текстом. Push выполнен из отдельного checkout поверх139f7da; текущая
локальная ветка разработки не перебазирована, незавершённые изменения сохранены.
[Отчёт](releases/2026-09-25-license-publication.ru.md). Версии/production не менялись.

## 25.09.2026 — критический путь теперь Android → Telemost → Linux EU

Пользователь изменил приоритет на прямой restricted transport в EU Gateway без
Windows Home PC и без обязательного IP-over-Reticulum. Основание — успешный
штатный Telemost видеозвонок Краснодар→Бельгия при недоступном прямом Family VPN;
headless Family carrier этим не проверен. **Этап5, подготовка нового track5N.**
[План и WEBRTC-EU-1–6](PLAN.md) · [Архитектурное решение](reticulum/HOME_GATEWAY_DESIGN.md)
· [Отчёт](releases/2026-09-25-webrtc-eu-priority.ru.md).

Reticulum control/recovery/identity/provisioning/messaging сохранён. Home Gateway
остаётся вторичной функцией для LAN/NAS/RDP/residential exit. Нумерация5A–5M и
старые gates сохранены; новые5N.1–6 пока NOT RUN. Приоритет Telemost/VP8 → EU
Family auth → single TCP → mux → Android TCP+DNS; UDP позже, без direct leaks.
Все existing transports остаются, код и dependencies не менялись. Текущий scope
по прежнему уточнению — документация/preparation. APK/builds/production/версии
прежние по release checkpoint (Android beta50/code50, Linux0.2.10, Windows0.2.14),
нового rollout/rollback нет. Предыдущие записи ниже описывают историю приоритетов.

## 25.09.2026 — Telemost: полевое подтверждение пользователя

Android в ограниченной сотовой сети Краснодара успешно завершил видеозвонок
Yandex Telemost с Бельгией, при этом прямое подключение Family Connect VPN
недоступно. **Источник — сообщение пользователя; это не инструментальный тест
нашего carrier.** [Запись и границы](releases/2026-09-25-telemost-cellular-evidence.ru.md).

Приоритет первого carrier PoC изменён: **Telemost первым, WB резервным**.
Подтверждён один штатный видеозвонок, а не headless API, произвольные binary frames,
RNS Link или Home Gateway. Все WEBRTC-1–5 остаются открытыми. Данные об операторе,
версиях клиентов, длительности/скорости, ICE/TURN/SFU path и ОС в Бельгии не получены.
Этап5/подготовка5A–5H продолжается; по прежнему уточнению пользователя пока только
документация и подготовка. Код/версии/production не менялись.

## 25.09.2026 — Whitelisted WebRTC Carrier: подготовка

**Глобально этап5; сейчас подготовка5A/5H, реализации Home Gateway/carrier ещё нет.**
По уточнению пользователя эта итерация ограничена документацией и подготовкой.
ReticulumOverlay → UnderlayPathManager → direct IPv6/IPv4 либо WebRTC underlay;
Reticulum отвечает за identity/Link encryption, провайдер переносит opaque frames.
[План](PLAN.md) · [Delta/design](reticulum/HOME_GATEWAY_DESIGN.md)
· [Отчёт](releases/2026-09-25-webrtc-carrier-preparation.ru.md).

Исследованы pinned whitelist-bypass (MIT) и olcrtc (WTFPL v2), без копирования кода.
Первый кандидат — WB/VP8; guest joining найден, создание room без login и реальные
media capabilities не проверены. Подготовлены contracts IPC/path/provider/rendezvous,
тестовые gates WEBRTC-1–5 и стадии5H–5M без перенумерации5A–5G.
Все WEBRTC gates открыты; ни desktop service round trip, ни Android↔Windows/RNS,
ни Краснодар не проверялись. Code/dependencies/runtime/production не менялись;
Android beta50/code50, Linux0.2.10, Windows0.2.14 по предыдущему checkpoint прежние.
Новых artifacts/rollout нет. Предыдущие решения ниже сохраняют историю уточнений.

## 25.09.2026 — стратегия Home Gateway уточнена

**Мы на глобальном этапе5, в начале5A Home Gateway: дизайн и проверка достижимости.**
Цель — соединить телефон с домашним Windows при активных белых списках мобильной
сети. Reticulum — control/discovery/auth/negotiation/recovery; IP-трафик — через
выбранный защищённый data transport, напрямую либо через достижимый relay.
Обязательный IP-over-Reticulum отменён пользователем. Relay не подменяет домашний exit.

[Текущий план5A–5G](PLAN.md) · [Обновлённый дизайн](reticulum/HOME_GATEWAY_DESIGN.md)
· [Отчёт](releases/2026-09-25-home-gateway-strategy.ru.md).
Home Gateway ещё не реализован; RNS-1–RNS-5 не пройдены. Сначала подтвердить
доступность control/bootstrap **и** data ingress на целевой SIM при ограничениях;
наличие RNS identity/сессии само по себе не доказывает обход белых списков.
Имеющийся XHTTP/TLS проверялся локально, не на таком мобильном пути.
Документация/лицензирование есть, transport/runtime код и production не менялись.
Android beta50/code50, Linux0.2.10, Windows0.2.14 остаются прежними по предыдущему
release checkpoint; новых сборок/публикаций и rollout/rollback нет.
Прежние5.2/5.3а и независимые test/migration задачи остаются открытыми.

Предыдущий checkpoint25.09: добавлены LICENSE, third-party inventory и
[аудит](legal/DEPENDENCY_LICENSE_AUDIT.md). Его первоначальное требование вести
все пакеты через RNS заменено текущей стратегией; legal-решения сохранены.

24.09: [Windows0.2.14 опубликован](releases/2026-09-24-windows0214-installer.ru.md), source6eed30c.
GitHub/HTTPS installer и страница обновлены; отдельный подписанный Windows-каталог
schema2/sequence10. CET отключён только для процессов приложения для совместимости
со старыми патчами Win10; системные настройки защиты не меняются. Повторная установка
не запускает старый EXE, данные сохраняются. Native CI: Server2025/2022, recovery/upgrade,
UI/user/AWG/TCP passed. Физический проблемный Win10 ПК ещё требует приёмки.
Windows10 1809+ /11 x64 — целевые версии, не гарантия всех сборок Windows.


24.09: [разбор сбоя первой установки Windows0.2.13 на Windows10](releases/2026-09-24-windows10-install-audit.ru.md).
На ПК Windows10 Pro22H2/19045.2364 служба не создана; причина ещё не установлена.
Хеш локального release EXE совпал, Windows CI success повторно подтверждён;
отдельного Win10 job нет. Полученные setup/host журналы: admin/x64, повтор
останавливается на remove-service; trace обрывается после загрузки coreclr.dll.
Crash TXT подтвердил CLR0x80131506 на i5-11300H; основная гипотеза — CET
на старых патчах Win10 (аналог dotnet/runtime108589). Следом обновление Win10,
перезагрузка и повторная установка; CET на этом ПК ещё не доказан.
Версии/публикация не менялись.

24.09: [XHTTP/TLS реализован в исходниках и проверен локально](releases/2026-09-24-xhttp-local.ru.md).
Этап5.3в теперь в работе по прямому запросу пользователя: Python/Linux, Android
Java/Go и Windows activation v2; двусторонний loopback, TLS/credential refusals.
Публичный режим белых списков пока не готов: DNS/CDN ingress, Friends/capability,
fleet и реальные сети открыты. Домен предоставлен, DNS не менялся. Краснодар —
первый регион приёмки; номер абонента не сохраняется.5.3а остаётся открытым.

24.09: в план добавлен **5.3в — реализация режима для сетей с белыми списками**
по ориентиру Shuka: обследование→ingress/транспорт→клиенты→восстановление→операторская
приёмка и Django7.1. [Требования](allowlist-connectivity.ru.md). Пока это план;
текущий5.3а и отложенная проверка Android на телефоне сохраняются.

24.09: [подготовлены проверки admission Android-службы](releases/2026-09-24-android-service-admission.ru.md).
Три instrumented сценария для пустого debug pilot: неверный gateway, выбор без
managed enrollment с повтором, отмена callback разрешения VPN. Сборка прошла;
первый запуск на телефоне завершился тайм-аутом, runtime acceptance не засчитана.
По просьбе пользователя дальнейшая работа пока без телефона. Следующий шаг5.3а:
повторить эти проверки, затем реальный enrollment/permission/restart/rollback/трафик.

Обновлено 24.09.2026. Это актуальный статус; датированные отчёты сохраняют историю.

24.09: [сравнение восстановления у Proton, Mullvad, Amnezia, Psiphon и Tor](releases/2026-09-24-competitor-recovery.ru.md).
Анализ публичных источников, не проверка доступности в России. Код/production не
менялись; следующий шаг5.3а и открытые критерии5.2/6 сохраняются.

## Положение в общем плане

24.09: [уточнение AWG на Wi-Fi](releases/2026-09-24-awg-wifi-followup.ru.md):
пользователь пробовал AWG до исправления выдачи конфигурации; повтор ещё ожидается.
NL AWG работает и имеет свежие handshake. Отдельная проблема UDP не подтверждена;
код и серверные настройки не менялись, план5.3а сохраняется.

24.09: [актуальность3 локальных SQLite подтверждена](releases/2026-09-24-local-sqlite-review.ru.md).
Все3 совпали логически с backup; свежие encrypted snapshots сохранены и извлечены.
14 targeted tests passed. Классификация: локальное pilot state, сохранять;
наблюдение потребителей неполное. Следующая разработка5.3а — Android device acceptance.
Внешняя копия, full DR и production signing acceptance остаются открытыми.

24.09: [Android signing consumer из KeePassXC реализован](releases/2026-09-24-android-vault-signing.ru.md).
65 targeted tests passed, включая реальный synthetic KDBX→apksigner→verify.
Настоящий keystore проверен по сертификату beta50 без подписи; новых релизов нет.
Следом свежесть3 локальных SQLite/active-legacy state; внешний носитель и production
signing acceptance остаются открытыми. Рабочие оригиналы сохранены.

24.09: [закрытый реестр локальных потребителей сохранён в KeePassXC](releases/2026-09-24-local-secret-consumer-audit.ru.md).
204 файла:200 совпадают с прежними backups,3 SQLite требуют проверки актуальности,
ещё1 административный credential добавлен и проверен.7 modes сужены до0600.
Следом Android signing consumer из vault; внешний носитель и full clean-machine DR
остаются открытыми. Рабочие оригиналы сохранены, production не менялся.

24.09: [исправлен нулевой запас challenge на расхождение часов](releases/2026-09-24-friends-challenge-clock.ru.md).
RU API выдаёт challenge100с вместо120с; клиентская граница120с сохранена.
45 tests passed, HTTPS200/TTL100, службы active. APK friends beta50 проверен по
хешу/package; пользователь подтвердил: новый клиент подключился.
Следом возврат к аудиту оставшихся plaintext секретов и их потребителей.

24.09: [изолированное восстановление из KeePassXC прошло](releases/2026-09-24-vault-restore-rehearsal.ru.md).
89 файлов/7 SQLite, Access/referral identity и реальный mailbox startup/shutdown
проверены в контейнере без сети;12 tests passed. Live state и vault не изменялись.
Следом аудит plaintext/потребителей; полный clean-machine DR, VPN/HTTPS acceptance
и внешний носитель остаются открытыми.

24.09: [синхронизация участников чата восстановлена](releases/2026-09-24-chat-clock-recovery.ru.md).
Причина — часы NL отставали примерно24с; добавлен рабочий NTS-источник chrony.
RU/NL synchronized, timer успешен, membership актуален и совпадает с RU;21 tests passed.
Далее clean-machine restore/внешний носитель/аудит plaintext; alerts времени ещё открыты.

24.09: [TLS/SSH/mailbox: ещё42 файла в KeePassXC](releases/2026-09-24-infrastructure-secret-backup.ru.md).
Binary export/SHA256 и1 SQLite restore прошли;10 targeted tests passed.
Обнаружены failed RU chat-sync и просроченный NL membership lease: диагностика и
исправление — следующий шаг. Затем clean-machine restore/внешний носитель;
рабочие plaintext originals пока сохранены. Версии клиентов не менялись.

24.09: [47 серверных файлов/6 SQLite сохранены в KeePassXC](releases/2026-09-24-server-secret-backup.ru.md).
Извлечение/hashes/in-memory SQLite restore прошли, VPN службы active.7 targeted tests passed.
Следом — TLS/system SSH/messenger-node, clean-machine restore и внешний носитель.
Это не единый образ всех серверов; работающие plaintext originals пока сохранены.


24.09: [TCP-службы NL и RU перезапущены по разрешению пользователя](releases/2026-09-24-tcp-private-umask-restart.ru.md).
Runtime Umask0077 подтверждён на обоих узлах; службы active/NRestarts0, TCP-порты
доступны локально и с ноутбука. AWG PID сохранены. Отложенный TCP restart закрыт;
полный клиентский VPN-трафик этим запуском не проверен. Следом — server backup/recovery.


24.09: [аудит серверных прав и5 vault issuers](releases/2026-09-24-secret-consumers.ru.md).
40 targeted tests passed; основные секреты RU/NL имеют ожидаемые600/640 и закрытые
каталоги. Drop-in UMask0077 установлен без restart; AWG runtime0077, TCP runtime0022
до планового restart. Далее — server backup/реестр потребителей; plaintext оригиналы пока сохранены.


24.09: [подпись из KeePassXC](releases/2026-09-24-vault-signing.ru.md) подключена к3 issuers.
896 Python tests passed; рабочий ключ прочитан из vault и проверен по public anchor
без подписи/экспорта. Далее — проверка остальных потребителей/серверных credentials,
внешний backup и устранение ненужных plaintext копий. Старые файлы пока сохранены.


24.09: [203 локальных файла скопированы в KeePassXC](releases/2026-09-24-vault-import.ru.md),
2 encrypted attachments проверены бинарным извлечением/SHA256. Исходники сохранены,
внешней копии ещё нет. Далее — [перевод потребителей секретов](secrets-and-recovery.ru.md),
серверные credentials и устранение лишних plaintext копий после проверки восстановления.


24.09: [локальное KeePassXC-хранилище создано](releases/2026-09-24-local-vault.ru.md),
проверено открытие повторно введённым паролем.5 разделов пока пустые; рабочие секреты
не переносились. Внешняя копия отложена пользователем. KDBX/keyx блокируются в Git.


24.09: добавлен [guard публикуемых исходников](releases/2026-09-24-public-source-guard.ru.md)
и CI-проверка индекса.2 новых теста passed. Хранилище/офлайн-копия пока не созданы:
носитель не подключён. Предыдущие Linux control/Windows conformance/phase0/messenger/
desktop visual/user access CI прошли; Android/Windows builds и native AWG/TCP ещё выполнялись.


24.09: [source checkpoint и правила секретов](releases/2026-09-24-source-checkpoint.ru.md)
опубликованы в GitHub main: `86eb24e`.890 Python/124 Java tests и C# runner passed.
GitHub Actions для этого коммита поставлен в очередь; результат ещё не подтверждён.
Публикация Git не означает rollout. Исторические пометки «локально» ниже описывают
состояние на момент соответствующей проверки.


Текущий checkpoint5.3а: [проверки на Redmi Note 9 Pro](releases/2026-09-24-android-selection-device.ru.md).
В отдельном debug pilot прошли4 instrumented tests: protocol/JSON, selection с настоящим
Keystore/journal и запуск Python/RNS. Friends beta50 сохранён. VPN Host в selection
имитируется: service/UI/handshake, process restart и Friends integration ещё открыты.
Документация локальная, APK не опубликованы.

Предыдущий checkpoint5.3а: [подготовка instrumented selection](releases/2026-09-24-android-selection-runtime-preparation.ru.md).
Собраны ARM64 debug pilot APK и test APK с Python3.10; новый тест реального encrypted
journal с имитацией VPN скомпилирован. ADB не видит устройств: исполнение теста,
service/UI/native acceptance ещё не выполнены. APK не установлены/не опубликованы.
Документация и изменения локальные; capability/Friends integration остаются открытыми.

Предыдущий checkpoint5.3а: [Android selection service/UI](releases/2026-09-24-android-selection-service.ru.md).
MainActivity→ConnectionService worker→ControlSelection→journal подключены в исходниках.
124 Java tests и Android debug Java compile passed; APK не устанавливалась/не публиковалась.
Capability AWG3.1/Friends integration и device acceptance ещё открыты. Карта кода обновлена.

24.09: составлена [общая карта кода по модулям](code-map/README.ru.md): серверные
контуры, платформы, messaging, эксплуатация/CI и лаборатория. Это документация,
runtime/версии не менялись. Карта дополняет подробную managed-карту и остаётся локальной.

Последний checkpoint5.3а: [локальная транзакционная смена Android gateway](releases/2026-09-24-android-gateway-transaction.ru.md).
120 Java tests passed. Journal schema2 появляется только при явном selectGateway;
сохранение выбора/rollback/restart проверены с имитацией Host/storage. Service/UI
ещё не подключены, APK/production прежние. Документация пока локальная.

24.09: [исправлен выбор Android gateway при нескольких профилях одного транспорта](releases/2026-09-24-android-gateway-selection.ru.md).
111 Java tests passed; Host имитируется, native rollout отсутствует. Добавлена
[карта managed-кода](managed-control-code-map.ru.md) с границами authority/recovery.
Следом — транзакционная смена gateway/действующая identity и device acceptance.

Последний checkpoint: [Android AWG3.1 identity/journal](releases/2026-09-24-awg31-android-journal.ru.md),
110 Java tests passed; application Host/storage имитируются, production caller выключен.
GitHub main проверен: b5f4864, STATUS23.09. Последние документы24.09 пока локальные,
commit/push не выполнены; не путать их с опубликованной документацией.

Последнее продолжение5.3а: [Java/C#/Python conformance AWG3.1](releases/2026-09-24-managed-awg31-native-verifiers.ru.md).
Java109 tests, Python86 tests и .NET runner прошли локально; общий corpus8×2 и
дополнительные проверки защиты. Рабочие capability callers ещё не включены;
Windows OS/Android device acceptance впереди. Production/версии не менялись.

24.09, последний кодовый checkpoint: [5.3а managed AWG3.1](releases/2026-09-24-managed-awg31.ru.md)
в schema/issuer/Python verifier с явным capability. Добавлен отдельный общий corpus;
360 уникальных локальных сценариев прошли по совокупности запусков (детали в отчёте).
Native managed клиенты/runner ещё не включены,5.3а не закрыт. Production и версии прежние.
Поручение усилить защиту принято в [требованиях устойчивости](blocking-resilience.ru.md).

Этап4 закрыт как выпуск пилотных приложений 23.09.2026. После перечисления критериев
Windows0.2.13 (интерфейс, приглашение, подключение, обновления) и базового сценария Linux
пользователь сообщил: «считай подтвердили». Это основание пользовательской приёмки;
новых инструментальных прогонов и подробных замеров эта запись не добавляет.
Начат этап5: независимый служебный канал и расширяемый парк серверов. Коммерческая готовность,
длительная сетевая устойчивость и новые функции остаются отдельными открытыми задачами.

## Версии и распространение

| Платформа | Собрано | Установлено / опубликовано |
| --- | --- | --- |
| Android ARM64 | 0.1.18-beta51 / code51 | Redmi Note 9 Pro обновлён поверх50; HTTPS APK, updater и страница —51 |
| Linux | 0.2.11 / preview5b02e8cb9fde119f | GitHub/HTTPS paired archive; CI GTK/map/link/friends/recovery/install passed |
| Windows x64 | 0.2.15 / source2ffba77 | GitHub/HTTPS installer + catalog sequence11; native/compat CI passed; affected Win10 device acceptance pending |

[Интерактивная страница](https://185.251.89.19:8443/invite/) принимает исходную ссылку
приглашения: установка → возврат к ссылке → открытие приложения. Вкладки, выбор платформы
и переключатели работают в браузере; VPN подключается самим приложением. Во всех клиентах
и на странице OFF оранжевый, ON бирюзовый. Старые файлы и автоматические desktop-каталоги
сохранены; Linux0.2.10 остаётся manual preview. Windows0.2.14 опубликован и включён
в отдельный подписанный updates/windows.json (schema2, sequence10). С0.2.12 и старше нужна
одна ручная установка переходной версии; затем работает встроенная проверка Windows.

[Версии и хеши](releases.md) · [Windows: приёмка и откат](releases/2026-09-23-windows0213-updater.ru.md) · [Android/Linux](releases/2026-09-23-switch-colors-beta50.ru.md).

## Подтверждено

Android: VPN пилот, обмен текстом и голосовыми между двумя телефонами, редактирование,
запись удержанием/фиксация вверх, прокрутка к новым сообщениям и уведомление с выключенным
экраном подтверждены ранее. Beta50 сохраняет эти функции и меняет оформление переключателей.
153 unit tests, lint, ARM64 build и проверка payload/подписи. CI и точные проверки текущего
выпуска приведены в отчёте. Публичные загрузки проверены по полному SHA256.
Linux GTK rendering, взаимодействия, запуск распакованного архива и URI checks passed в CI.
Windows native installer/broker/UI/URI, ordinary-user и AWG/TCP проверки passed.

## Следующая приёмка

- Долгий фон, перезапуск/OEM, Android13+ и Doze с точным временем доставки.
- Российская сеть, смена сети и длительная устойчивость (отдельная полевая приёмка).
- Полная недоступность gateway и восстановление через независимый служебный канал.
- Desktop messenger не имеет подтверждённого равенства возможностей с Android.
- Подписки/оплата, publisher signing Windows, лицензия и независимый аудит не завершены.

Доступ только по приглашению; личные ключи и данные при обновлении сохранены. Лимиты
20 referral claims за24ч и500 мест — параметры, а не текущий остаток. Прямые приглашения
имеют отдельный запас. CI использует тестовую подпись, ключ выпуска остаётся offline.
[Рабочий план](PLAN.md) · [Карта документации](README.md).

Windows0.2.11 исправил разметку, логотип и активацию;0.2.12 — причины лишней перерисовки.
В0.2.13 добавлен отдельный Windows updater после обнаружения устаревшего общего каталога0.2.9.
Пользователь выбрал одну ручную установку переходной версии. Native CI пройден;
пилотные проверки приняты пользователем 23.09.2026, см. запись выше. [Артефакт, канал и откат](releases/2026-09-23-windows0213-updater.ru.md).

Этап5 начат24.09: аудит5.1 завершён, подготовлены контракт приёмки и локальная
основа реестра серверов/планировщика5.2. По просьбе пользователя добавлены новые
серверы, распределение новых подключений и управление IP. Production-балансировщик
ещё не включён. Локально добавлены durable leases/IPAM: резервирование, revoke,
expiry и подтверждённое освобождение;112 checks passed. Следом — интеграция доступа
и удалённый reconciler с fencing. [Отчёт хранения](releases/2026-09-24-fleet-leases.ru.md).
[Аудит, тесты и границы готовности](releases/2026-09-24-stage5-audit.ru.md) ·
[Контракт](stage5-fleet-contract.ru.md).

## Снимок нагрузки24.09.2026

Read-only аудит: Friends18 устройств,14 не отозваны;5 устройств передавали
трафик через NL в20-секундном замере. CPU RU≈19%, NL6%; на RU iowait5–10%.
Число людей и суточные пики не установлены; текущий этап и версии не менялись.
[Метрики, границы измерения и оставшиеся проверки](releases/2026-09-24-server-usage.ru.md).

## Продолжение5.2 и согласование7.1

24.09 добавлены локальный шлюзовой журнал fencing и worker:139 tests passed
включая реальное падение процесса с дочерним эффектом. Это предыдущий checkpoint локального прототипа; live rollout не выполнялся.
Последующее добавление WG/AWG и SSH описано ниже.
[Подробный отчёт](releases/2026-09-24-fleet-fencing-admin-plan.ru.md).
Согласован [7.1 — единая Django-админка серверов, доступа и платежей](PLAN.md#django-admin).
UI запланирован после5/6; общие операции5.2 готовятся сейчас. Клиентские версии прежние.

## Текущий шаг5.2: WG/AWG и SSH

24.09 реализованы точечный WG/AWG backend, SSH adapter с закреплённым host key
и агент с фиксированной командой; общий локальный прогон163 passed. Проверены
subprocess fixture и SSH argv/receipt, native VPN/SSH приёмка ещё впереди.
[Отчёт](releases/2026-09-24-fleet-wg-ssh.ru.md) · [Runbook](fleet-wg-ssh.ru.md).
Нет установки на RU/NL и изменений клиентских версий.5.2 остаётся открыт:
native приёмка → общая авторизация/scheduler/signed publish; также нужны
автономный TTL, TCP и миграция существующих IP.7.1 Django остаётся после5/6.

## Последний checkpoint5.2: native-приёмка завершена

24.09,10:39–10:40 UTC:12 сценариев WG/AWG2/AWG3.1 с настоящим SSH и VPN-трафиком
passed; отдельно163 regression tests passed. Проверены crash после peer effect,
повтор SSH, restart/recover, revoke, повторное использование IP и fencing старой команды.
[Отчёт/границы](releases/2026-09-24-fleet-native.ru.md) ·
[Запуск стенда](../pilot/fleet-native/README.ru.md). Тестовые контейнеры/сети удалены.
После server restart клиентский handshake инициировался явно; автоматический
client recovery и межсерверная SSH-сеть здесь не приняты. Production rollout отсутствует.
Следом в5.2 — единая авторизация и bounded scheduler, затем signed publish;
TTL, TCP, миграция действующих IP и установка/recovery services ещё открыты.
Клиентские версии и согласованный пункт7.1 не изменились.

## Последний checkpoint5.2: proof авторизация и scheduler

24.09: FleetAccess проверяет подпись/актуальные права и резервирует одной транзакцией;
FleetScheduler сохраняет claims/backoff, ограничивает проход и приоритетно удаляет
отозванные подключения.201 tests passed. Схема fleet DB2, явный upgrade1→2;
production DB не менялись. [Отчёт](releases/2026-09-24-fleet-services.ru.md) ·
[Контракт/миграция](fleet-access-scheduler.ru.md).
Следом — signed publish после ready. Подключение к действующим Friends правам/API,
TTL/TCP, supervisor и импорт старых выдач ещё открыты. Это локальный service backend,
не опубликованный endpoint. Клиентские версии и пункт7.1 прежние.

## Последний checkpoint5.2: offline signed publication

24.09: локальный issuer подписывает/шифрует существующий control-config/schema2
для ready WG/AWG2 lease; повтор возвращает те же bytes. Отдельный published()
проверяет текущие права и выдаёт ciphertext без signing key.269 tests passed,
fleet schema3, явная миграция1/2→3. [Отчёт](releases/2026-09-24-fleet-publication.ru.md) ·
[Контракт](fleet-publication.ru.md). Offline production key не читался.
Далее verified ACK и безопасный перенос offline→online/relay; действующий Friends
доступ, импорт старых floors/IP, TTL/TCP и production deployment ещё не подключены.
Managed AWG3.1 остаётся5.3. Клиентские версии и план7.1 не менялись.

## Последнее решение: приоритет managed AWG3.1

24.09 пользователь согласовал: ближайшим шагом становится5.3а managed AWG3.1;
5.2 не закрыт, оставшиеся relay/ACK/миграции сохраняются. WG/AWG2 — только
совместимость/регрессия. VLESS/REALITY остаётся альтернативным TCP-путём.
В5.3б записано исследование третьего транспорта: NaïveProxy HTTPS/HTTP2 первым,
Hysteria2 как сравнительный кандидат. Выбор для production ещё не сделан.
[План](PLAN.md) · [Обоснование](releases/2026-09-24-transport-priorities.ru.md).
Код/серверы/клиентские версии не менялись; новых runtime и сетевых тестов нет.

24.09 подготовлен [анализ рынка и устойчивости](releases/2026-09-24-vpn-market-assessment.ru.md).
Автопереключение и несколько протоколов уже есть у конкурентов; преимущество
Family Connect ещё требует российских сравнительных испытаний и платного пилота.
Код/версии/серверы не менялись, порядок работ сохраняется.

24.09 описана [архитектура восстановления Reticulum](reticulum-recovery-design.ru.md).
Криптографический destination сохраняется при переносе службы; независимая связность
входов, discovery и восстановление состояния ещё требуют реализации/приёмки.
Текущий single-bootstrap не заменён; код/версии/серверы прежние.

24.09 дополнена [модель обнаружения Reticulum/endpoints](releases/2026-09-24-reticulum-threat-model.ru.md).
Защита подписью/шифрованием не равна невидимости IP для подписчика или сетевого наблюдателя.
Только документация, поведение сервиса не менялось.
