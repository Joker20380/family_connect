# Рабочий план / Working plan

## Current engineering priority / Текущий critical path

- current: **5N — Restricted WebRTC Android→EU** (Telemost VP8 carrier → authenticated
  Family session → headless Linux EU gateway → TCP+DNS → Internet).
- immediate engineering gate: **WEBRTC-EU-1 / 5N.1**.
- затем: **5N.2 → 5N.3 → 5N.4 → 5N.5 → 5N.6**.
- после этого: restricted-mobile acceptance **5M**.
- **WB fallback** — только после подтверждения Telemost на реальной сети.
- **5.3a / 5.3в** и **Home Gateway (5A–5M secondary track)** — backlog, не запускаются автоматически.
- Параллельно (WIP, не блокирует 5N): упрощение invitation/activation — server-side
  authenticated recovery `POST /friends/device/status`, canonical URL `/i/`, smart landing
  page, QR=canonical URL; real-device Android E2E ещё не пройден.

Gate-таблица и порядок — ниже в секции `DECISION25.09 — Restricted WebRTC → Linux EU`.

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

25.09: лицензирование опубликовано в GitHub main, commit
`aa3ed9f801a83a4808df3352abc300d235a7c42c`: LICENSE, notices, audit и README RU/EN.
Публичный LICENSE скачан по immutable commit и побайтно совпал с проверенным
локальным текстом. Push выполнен из отдельного checkout поверх139f7da; текущая
локальная ветка разработки не перебазирована, незавершённые изменения сохранены.
[Отчёт](releases/2026-09-25-license-publication.ru.md). Версии/production не менялись.

## DECISION25.09 — Restricted WebRTC → Linux EU: новый критический путь

**Для ограниченной мобильной сети приоритет — Android → Telemost VP8 → Linux EU
Gateway → Internet. Windows Home PC и IP-over-Reticulum не prerequisites.**
Основание: пользовательский видеозвонок Telemost Краснодар→Бельгия прошёл при
недоступном прямом Family VPN. Community-код показывает binary/media реализации,
но наши headless/binary/Family tests пока не выполнены. Убираем зависимость от
home IP/NAT, Windows routing, включённого ПК и лишнего домашнего hop.

[Решение в существующем дизайне](reticulum/HOME_GATEWAY_DESIGN.md#decision-restricted-webrtc-to-eu-gateway-first--2026-09-25)
· [Checkpoint](releases/2026-09-25-webrtc-eu-priority.ru.md).
**Мы на глобальном этапе5: подготовка restricted Android→EU track.** Ранее
согласованный scope документации/preparation сохранён; runtime пока не реализуется.
Старые немедленные планы через Windows/RNS ниже — история прежнего приоритета,
а не условия начала нового track. Существующие номера5A–5M не переиспользовать.

Добавлен **5N — Restricted WebRTC Android→EU**, со стадиями:

| Gate / подэтап | Результат | Статус |
| --- | --- | --- |
| WEBRTC-EU-1 / 5N.1 | Linux/desktop↔Linux через настоящий Telemost: binary round trip нескольких размеров | Не запускался |
| WEBRTC-EU-2 / 5N.2 | Android↔EU Linux binary round trip без TUN | Не запускался |
| WEBRTC-EU-3 / 5N.3 | E2E Family session с existing Device Identity/FAMILY; wrong/revoked/replay rejected | Не запускался |
| WEBRTC-EU-4 / 5N.4 | Один TCP stream: реальный HTTPS response через EU | Не запускался |
| WEBRTC-EU-5 / 5N.5 | Много TCP/API/browser/DNS streams в одной carrier session | Не запускался |
| WEBRTC-EU-6 / 5N.6 | Full-device Android TCP+DNS, EU exit, no direct/DNS/IPv6 leak | Не запускался |

Порядок: reuse generic5H/5I contracts →5N.1–3 на целевой мобильной сети →5N.4–6 →
5M реальная30–60min приёмка (связана с5F) →5L WB fallback. Telemost первый,
WB только после Telemost validation, VK/future позже.5J/5K RNS-over-WebRTC/Home
Gateway и Home5B–5E сохраняются вторичными; NAT traversal/direct home paths и
Meshtastic emergency bootstrap не блокируют5N. Старые numeric5.1–5.6 control/fleet
задачи также не объявлены завершёнными и не возобновляются автоматически.

Data-plane: existing VpnService/TUN conversion → Family stream mux → authenticated
E2E session → opaque VP8 carrier → headless family-restricted-gateway → egress.
Проверить reuse Xray TUN inbound из pilot/android-tcp/tcp-android.go до введения
второго tun2socks. Existing Transport/ConnectionService/selection/provisioning
расширять новым WebRtcRestrictedTransport, не создавать второй TransportManager.
Изолированный carrier ничего не знает о Family auth, DNS/destinations и routing.
Linux gateway интегрируется с existing entitlement/revoke/provisioning и server
infrastructure. Выбор audited session/mux/reliability libraries — до реализации.

Phase1 TCP+DNS; phase2 UDP. Mux: OPEN/DATA/CLOSE/RESET с bounded flow control,
half-close, quotas и reserved datagram framing; одна conference на session, не
на запрос браузера. DNS внутри E2E session; неподдерживаемые UDP/IPv6 блокировать
без direct fallback. Сохранить socket protection, kill switch, auth/replay/expiry,
provider isolation/TLS verification. Повторное создание carrier не должно повторять
старые application writes. Service SFU не является доверенной Family стороной.

Reticulum сохраняется для identity binding, provisioning/control/recovery,
emergency messaging/discovery и future Personal Gateway/Meshtastic. Весь high-bandwidth
VPN не помещать в RNS без результатов сравнительных benchmarks. AWG/TCP/XHTTP
остаются first-class; будущий auto-select идёт от доступных existing transports к
Telemost при ограничениях. Пока новые flags OFF, production/defaults неизменны,
UI CONNECT без настройки протоколов. Providers remotely disableable через verified
config с TTL/revision/offline ограничениями. Telemost API failure не ломает другие paths.

Краснодар — решающая среда: Android cellular only, Wi-Fi OFF. В одном тестовом окне
сравнить ordinary FC FAIL / Telemost video PASS / Family Telemost PASS. Замеры:
setup,5/30/60min,RTT,throughput,CPU,memory,battery,reconnect count/time. Сценарии:
screen off/on,data off/on,airplane on/off,cellular reconnect,room recreation,EU
restart; browsing,large file,video,many HTTP streams. >5Mbit/s stable PoC,
>10–20 good,>30 strong — цели без текущих измерений. Stability важнее peak.
Ближайший engineering milestone после возобновления — **authenticated Family data
Android Краснодар → Telemost VP8 → EU Linux**, потом full-device Internet. UI polish
и Windows gateway до этого не требуются. All WEBRTC-EU gates open.

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

Следующий шаг после возобновления реализации: Telemost headless join → desktop
binary round trip → Android↔Windows → RNS announces/Link. Проверять именно тот
carrier/media путь, который использует PoC; работа штатного видеоклиента не
доказывает достижимость всех API/серверов. Не запрашивать/хранить cookies в документации.

## WebRTC extension25.09 — superseded immediate ordering (backlog: RNS-over-WebRTC / Windows path)

> Superseded immediate ordering. Эта секция описывает прежний путь WebRTC underlay →
> Windows Home Gateway / RNS-over-WebRTC. Текущий critical path — 5N (см. Current
> engineering priority выше). Сохранена как backlog / secondary track.

**По последнему уточнению пользователя сейчас только документация и подготовка
к реализации.** Carrier-код, сборки, провайдерские сессии и device tests отложены.
[Delta и контракт в существующем дизайне](reticulum/HOME_GATEWAY_DESIGN.md#whitelisted-webrtc-carrier--extension-2026-09-25)
· [Аудит источников](legal/DEPENDENCY_LICENSE_AUDIT.md)
· [Checkpoint](releases/2026-09-25-webrtc-carrier-preparation.ru.md).

Прежняя схема Home Gateway + WebRTC underlay = ReticulumOverlay →
UnderlayPathManager → direct IPv6 / direct IPv4 / WebRtcPathProvider → Windows.
Внутри carrier — сменные WB/Telemost/VK adapters. Reticulum сохраняет overlay
identity/Link encryption/routing; WebRTC переносит непрозрачные RNS frames.
Свобода отдельного data transport сохраняется; IP-over-RNS-over-WebRTC становится
явной тестовой веткой, а не требованием переписать все существующие VPN-транспорты.

Существующие5A–5G не перенумерованы. Добавлено:

| Подэтап | Результат | Статус |
| --- | --- | --- |
| 5H UnderlayPathManager | Path API, bounded lifecycle, custom RNS Interface, isolated carrier IPC | Контракт спроектирован, кода нет |
| 5I WebRTC carrier PoC | WEBRTC-1 desktop binary round trip → WEBRTC-2 Android↔Windows | Telemost первым после полевого видеозвонка; carrier-тестов нет |
| 5J Reticulum-over-WebRTC | WEBRTC-3: announces в обе стороны и authenticated RNS Link | Не реализовано |
| 5K Home Gateway over WebRTC | WEBRTC-4 IP/TCP/UDP → WEBRTC-5 browser/DNS/FC exit/no leaks; связано с5C–5E | Следующий этап |
| 5L multi-provider WebRTC | Telemost/VK после WB; независимое отключение verified config | Запланировано |
| 5M restricted-mobile validation | Дополнение5F: обычный VPN не работает, новый путь работает на той же SIM при ограничениях | Краснодар; не проверено |

Порядок после возобновления реализации:5A reachability →5H →5I →5J; перед5K
зафиксировать blockers/results. Сейчас глобальный этап5, подготовка5A/5H, а не
завершённые5B–5G. Без реальных Android/Windows и целевой сети gates не засчитывать.

Первоначально WB выбирался по guest-join/LiveKit reference; теперь Telemost первым
по полевому видеозвонку25.09, WB резервный.
Гостевой join не доказывает создание комнаты без входа: whitelist creator требует
cookie bearer; olcrtc использует готовую room. PoC допускает manual disposable room
через session API. Финальный UX — ephemeral rendezvous через provisioning/другой
достижимый control; room не Device Identity. Нельзя предположить, что ещё не поднятый
RNS-over-WebRTC сам доставит свои начальные credentials.

Для подготовки следующей реализации зафиксированы: stdio framed IPC, mode
capabilities DC/VP8/TCP fallback/TURN с unknown, bounded queues/cancel/backoff,
проверка всех Android signaling/ICE/media sockets, independent provider flags OFF,
no secrets/logging/TLS downgrade и provider-unavailable без падения приложения.
Производительность DC/VP8 измерять отдельно: >5Mbit/s полезная цель,20+ сильный
результат, не текущие замеры. Достижимость видеосервиса в белых списках не доказана.

## Home Gateway (secondary track / backlog) — Reticulum control, selectable data transport

> Superseded immediate ordering. Home Gateway — secondary LAN/NAS/RDP/residential-egress
> track, не немедленный следующий шаг. Текущий critical path — 5N (см. Current
> engineering priority выше).

**Уточнение пользователя: главная задача — установить защищённое соединение
телефон ↔ домашний компьютер в мобильной сети с белыми списками.** Reticulum
используется для discovery, аутентификации и согласования/восстановления пути;
гнать пользовательские IP-пакеты через RNS необязательно. Это заменяет прежнее
требование обязательного IP-over-Reticulum, не отменяя Device Identity/FAMILY,
fail-closed и минимальную приёмку реальных IP-пакетов Android↔Windows.

[Дизайн](reticulum/HOME_GATEWAY_DESIGN.md) · [Белые списки](allowlist-connectivity.ru.md)
· [Статус](STATUS.md) · [Отчёт об изменении](releases/2026-09-25-home-gateway-strategy.ru.md).

**Текущее положение: глобальный этап5, начало5A — дизайн и проверка достижимости.**
Документация/обследование есть; Home Gateway не реализован, RNS-1–RNS-5 не пройдены.
Старая нумерация5.1–5.6 относится к control/fleet; новая5A–5G — к Home Gateway.
Это две связанные части этапа5, а не заявление о завершении прежних задач.

| Подэтап | Результат и критерий | Статус |
| --- | --- | --- |
| 5A Control/discovery и достижимость входа | Existing Device Identity/FAMILY, RNS adapter и signed transport negotiation; измерить достижимость control/bootstrap и data ingress в целевой мобильной сети | Дизайн; полевые проверки впереди |
| 5B Android ↔ Windows encrypted session | RNS-1: согласование через RNS, взаимная аутентификация выбранного data channel, обе Device Identity, reconnect; сначала через достижимый relay | Не реализовано |
| 5C IP tunnel over selected transport | RNS-2: реальные Android TUN → выбранный защищённый transport → Windows packets и reply; IPv4 ping/deterministic test | Не реализовано |
| 5D Windows Personal Gateway | RNS-3: app-managed direct diagnostic egress; HTTP/HTTPS, DNS, UDP/TCP; без ручного ICS | Не реализовано |
| 5E existing VPN upstream integration | RNS-4: existing Windows engine, IP телефона = VPN exit; нет fallback на ISP | Не реализовано |
| 5F real mobile-network validation | RNS-5 Краснодар: работа при активных белых списках, establishment/throughput/RTT/loss, 30–60 min, смена сетей/IP | Не проверено |
| 5G direct paths / zero-config optimisation | Direct IPv6/IPv4, NAT traversal, multiple paths; relay остаётся резервным | После измерений |

Ближайший проверяемый результат: определить достижимый разрешённый ingress на
тестовой SIM при активных ограничениях, отдельно проверить control и data path,
затем установить authenticated телефон↔ПК session через него. Проверка через Wi-Fi
или мобильную сеть без активных ограничений не доказывает решение основной задачи.
Reticulum identity и обмен endpoint не создают доступ к заблокированному адресу.
Если control/bootstrap недоступен, требуется доступный carrier/bootstrap; если
control работает, а data path заблокирован, session не считать установленной.

Первый PoC: оба устройства подключаются исходящими соединениями к доступному
relay, который переносит end-to-end encrypted data и не является Internet exit.
Статический IP/DDNS/проброс портов на домашнем ПК не требуются. Прямой путь —
следующая оптимизация, не prerequisite. AWG/WG — кандидаты при доступном UDP;
существующий TCP/XHTTP/TLS и другие варианты оцениваются по reachability, наличию
authenticated reverse/relay path и скорости. Наличие runtime не означает готовый
reverse tunnel. Конкретный data transport ещё не выбран, новые зависимости не добавлены.

Согласование подписывает обе identity, transport public keys, роли, session nonce,
параметры/срок пути и FAMILY grant. Data handshake отдельно доказывает владение
ключами; контрольный успех не заменяет handshake. Потеря RNS не обязана рвать
здоровый data tunnel до истечения grant; для восстановления нужны доступный control
или заранее разрешённые актуальные пути. При expiry — fail closed.

Обязательные gates: DNS/IPv6 fail-closed, Android socket protection каждого
underlay/reconnect, anti-replay/downgrade, bounded buffers, route ownership,
Windows upstream failure, clean shutdown и recovery. Existing tests не ослаблять.
Feature OFF по умолчанию, default transports неизменны; no public proxy/cleartext/
shared credentials. RNS-2 сохраняет имя для continuity, но больше не требует IP-over-RNS.

Делить commits по legal/design/core/control/platform/data/tests/docs; RNS-3/RNS-4
отдельно. Лицензионные ограничения и audit сохраняются. Предыдущие5.2/5.3а и прочий
migration/test debt не возобновлять автоматически. Из5.3в переиспользовать только
нужное для текущей проверки ingress; остальные критерии не считать закрытыми.
Старые датированные «ближайшие шаги» ниже не перекрывают этот приоритет.

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

Обновлён 24.09.2026. Факты и версии: [STATUS](STATUS.md).
История сохранена в [прежнем журнале](PLAN.before-beta49-2026-09-23.md).

## Текущий приоритет (исторический журнал 24.09, superseded ordering)

> Исторический журнал24.09; immediate ordering superseded. Текущий critical path — 5N
> (см. Current engineering priority выше). Содержимое ниже сохранено как backlog/история.

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


24.09: принята [схема хранения секретов](secrets-and-recovery.ru.md). Выбраны компьютер
и отдельный офлайн-носитель. Настройка шифрования и проверка восстановления ещё открыты; секреты не перемещались.

На подключённом Redmi Note 9 Pro выполнены [4 instrumented tests](releases/2026-09-24-android-selection-device.ru.md)
в отдельном debug pilot: encrypted journal selection/reopen/rollback, protocol/JSON и
Python/RNS. Следующий шаг — service/UI acceptance с тестовым enrollment и настоящим
VPN gateway: permission/cancel, stop во время health, process restart и трафик.
Пустой pilot пока не имеет enrollment/managed configuration; TEST ONLY corpus не
предоставляет рабочие серверы. Friends identity integration остаётся отдельной задачей.
Изменения и карты пока локальные.

Android selectGateway service/UI wiring готов в исходниках;124 JVM tests и debug Java
compile passed. [Отчёт](releases/2026-09-24-android-selection-service.ru.md).
Следом — instrumented/device acceptance (permission/cancel/restart/rollback/UI selection),
оставшаяся native/Friends identity интеграция. buildPython для локальной APK исправлен выше.
Рабочая capability3.1 пока выключена. Обе карты кода актуализированы.

По просьбе пользователя24.09 подготовлена [карта всего проекта по модулям](code-map/README.ru.md)
для подключения новых разработчиков. При изменении ответственности/границ модуля
обновлять соответствующую страницу вместе с кодом (правило добавлено в CONTRIBUTING).
Порядок разработки5.3а→оставшиеся5.2/6 сохраняется.

Следующий шаг5.3а: подключить selectGateway к единому Android service worker/UI,
согласовать selection из journal и провести device acceptance. Локальная операция
с schema2/SWITCHING и recovery готова:120 Java tests passed.
[Контракт и границы](releases/2026-09-24-android-gateway-transaction.ru.md).
Это не завершение native/Friends интеграции и не закрытие5.2/6.

24.09: ControlApplication materialize учитывает явно выбранный gateway;111 Java tests
passed. [Отчёт](releases/2026-09-24-android-gateway-selection.ru.md) и
[карта кода](managed-control-code-map.ru.md). Переход между gateway одного транспорта
в уже committed envelope пока требует отдельной операции: resume не переписывает
слоты, replay не вызывает apply. Это входит в remaining5.3а/Android application gates.

Android identity/journal opt-in для managed AWG3.1 готов локально;110 Java tests passed
с apply/reopen/rollback на имитации службы. [Отчёт](releases/2026-09-24-awg31-android-journal.ru.md).
Далее native service/device integration и remaining Linux/Windows application gates.
Документация24.09 пока не отправлена на GitHub: remote main b5f4864 содержит статус23.09.
Отдельный docs checkpoint требует согласования с актуальным remote tree без потери
существующей незакоммиченной работы; force push/reset не применять.

Последний checkpoint5.3а: Java/C# verifier и parser согласованы с Python на общем
AWG3.1 corpus, defaults сохраняют отказ. [Результаты](releases/2026-09-24-managed-awg31-native-verifiers.ru.md).
Следом — capability через identity/journal/application boundary и native apply,
health/rollback/restart на устройствах; Windows C# тесты на Linux не закрывают OS gates.
Аренда сервера для текущих проверок не требуется; независимый ingress понадобится
на сетевом этапе5.2/6 согласно проекту recovery.

24.09: начат5.3а — schema/issuer/Python verifier AWG3.1 и отдельный shared corpus
готовы локально; следующий шаг — native conformance/capability/apply на трёх платформах.
[Checkpoint и тесты](releases/2026-09-24-managed-awg31.ru.md).
Пользователь поручил усилить защиту всеми доступными способами:
[матрица мер/приёмки](blocking-resilience.ru.md) обязательна для5/6. Independent ingress,
сегментация, внешнее восстановление и дополнительные транспорты ещё не реализованы.

По просьбе пользователя24.09: начать этап5 и включить расширяемый парк серверов,
распределение нагрузки и управление IP. Предыдущая сверка документации сохранена ниже.
**После каждого изменения версии обновлять документацию в той же работе.** Отдельно
указывать локальную сборку, установленную, публичную и версию на странице приглашения.
[Процедура](releases.md#documentation-with-every-version).

1. Выполнено: RU/EN инструкции, загрузки и статус сверены, история сохранена;
   274 Markdown-файла/1586 ссылок проверены. Документация опубликована в GitHub
   коммитом b8d51bf;9 основных файлов скачаны и совпали побайтно.
2. Выполнено: актуальный source checkpoint Android49 / Linux/Windows0.2.10 опубликован
   в main, версии согласованы. Код8627d55: Client builds35899784973, Linux control,
   phase0 и TCP — success; native Windows AWG/TCP и ordinary-user acceptance также passed.
   На момент этого checkpoint приёмка этапа4 ещё не была завершена; итог ниже.
3. Выполнено: интерактивная страница, Android beta50 и desktop0.2.10 manual preview
   опубликованы согласованно. URI/UI проверки и SHA256 публичных файлов подтверждены.
   Переключатели всех клиентов: оранжевые OFF, бирюзовые ON. Документация обновлена.
4. Выполнено: 23.09.2026 пользователь принял перечисленные проверки словами
   «считай подтвердили». Этап4 закрыт в объёме пилотного выпуска: Windows0.2.13
   (интерфейс, приглашение, подключение, проверка обновлений), базовый сценарий Linux,
   ранее подтверждённые сценарии Android. Это пользовательская приёмка, не новый тестовый прогон.
5. Начат этап5: независимый служебный канал и, по уточнению пользователя24.09,
   расширяемый парк серверов, распределение новых подключений и IP-адреса. Аудит5.1
   завершён; реестр/планировщик и durable leases/IPAM5.2 реализованы локально.
   Резервирование, конкуренция, crash/recovery и Friends regression:112 passed.
   Добавлены локальный шлюзовой fencing-прототип и worker: общий прогон139 passed.
   Добавлены WG/AWG backend и SSH adapter в исходниках:163 passed.
   Изолированная native/SSH приёмка пройдена:12 сценариев на WG/AWG2/AWG3.1.
   Добавлены локальные proof авторизация и durable scheduler:201 passed.
   Добавлена локальная offline signed выдача WG/AWG2:269 passed, fleet schema3.
   Следом — verified ACK и перенос offline→online, привязка действующего доступа/API.
   HTTPS Friends сам по себе независимость не обеспечивает.
6. Длительные сетевые испытания, российская сеть, смена сети и точная задержка Doze
   остаются отдельными задачами устойчивости; они не переоткрывают пилотный этап4.

## Глобальные этапы

| Этап | Состояние / следующий результат |
| --- | --- |
| 1. Продукт, WG, идентичности | Работает в пилоте; сохранить выдачу/отзыв и ключи |
| 2. AWG и восстановление | AWG3.1 реализован; длительная и российская приёмка открыты |
| 3. TCP REALITY | Реализован; общая сетевая приёмка открыта |
| 4. Три клиента и выпуск | Закрыт как пилотный выпуск по приёмке пользователя 23.09.2026 |
| 5. Служебный канал и парк серверов | В работе:5.1 завершён;5.2 backend/SSH/scheduler/offline publish подготовлены;5.3а managed AWG3.1 требует native/Friends integration и device acceptance. Сейчас —5.3а, Android service/UI acceptance |
| 6. Недоступный gateway | Нужна сквозная смена endpoint через независимый канал |
| 7. Сервис и коммерческая версия | Согласована7.1 — единая Django-админка; оплата/подписки не реализованы |

**Текущая точка (superseded immediate ordering / backlog):** этап5.3в, локальная реализация XHTTP/TLS по новому прямому запросу;
5.3а Android service/UI acceptance остаётся открытым, телефон отложен пользователем.
Обеспечивающие задачи секретов/recovery для5/6 продолжаются отдельно.
Хранилище, пять vault issuers, server backups и контейнерное восстановление готовы;
реестр потребителей начат. Android vault entry point готов; не закрыты production signing acceptance, внешний носитель
и восстановление на чистом хосте. Безопасность — не отдельный завершённый этап.

**Очередь:** выбранные3 SQLite сверены, fresh snapshots проверены. Ближайшая
разработка возвращается к5.3а: Android service/UI acceptance с реальным
enrollment, разрешением VPN, restart/rollback и трафиком. Далее remaining5.2/5.4–5.6,
сквозной этап6 и только затем Django7.1. Проверка всех потребителей перед удалением
originals, внешний носитель и full DR остаются отдельными обязательными пунктами. Исследование третьего транспорта5.3б остаётся
согласованным, но отдельный production transport ещё не выбран. Новый сервер для
текущей локальной работы не нужен; независимый ingress нужен для сетевой приёмки6.

<a id="release-gates-three-platforms"></a>
## Условия выпуска трёх платформ

- Android: совпадение версии/ABI/сертификата/хеша, unit/lint/build, native UI и VPN,
  обновление без потери идентичности, приглашение по ссылке и фон на доступных устройствах.
- Linux: извлечённый пакет, зависимости/helpers, обычный пользователь, GTK rendering
  и взаимодействия, установка/обновление, приглашение и реальные транспорты.
- Windows: native CI UI/broker/installer/AWG/TCP, обычный пользователь, URI handler;
  физическую проверку отмечать отдельно, не заменять Linux cross-build.
- Публиковать неизменяемые файлы; каталог подписывать offline только после проверки
  скачанных platform CI artifacts. Не заменять прежний APK другой сборкой.
- Согласовать загрузки/страницу/документацию; проверить внешнее скачивание и предусмотреть
  откат метаданных. Не удалять данные устройств при обновлении или откате.

## Отложенные задачи

Долгий Doze/OEM/boot/Android13+, desktop messenger, iOS/macOS, полный gateway failover,
лицензирование, private security reporting, Windows publisher signing и коммерческий
запуск не закрываются успешной сборкой. Новые VPS не заказаны.

[Текущая приёмка, артефакты и откат](releases/2026-09-23-switch-colors-beta50.ru.md).
Этап4 закрыт по решению пользователя; это не утверждение о коммерческой готовности.
Новые функции и desktop messenger ведутся отдельно от завершённого пилотного выпуска.

Windows0.2.13 и отдельный подписанный канал опубликованы; пользователь принял проверки
переходной установки, интерфейса, приглашения, подключения и кнопки обновления.
Schema2/sequence9 отделён от прежнего общего schema1/sequence8. Подробные новые замеры
на ПК не предоставлялись. [Выпуск и запись приёмки](releases/2026-09-23-windows0213-updater.ru.md).

## Разбиение этапа5

[Подэтапы5.1–5.6, сроки и критерии завершения](releases/2026-09-23-stage5-plan.ru.md).
5.1 завершён24.09. [Аудит и результаты тестов](releases/2026-09-24-stage5-audit.ru.md).
[Дополненный контракт](stage5-fleet-contract.ru.md): несколько узлов одной страны,
реестр endpoints, IPAM, capacity admission, drain и добавление сервера без новой сборки.
В5.2 готовы локальный реестр/валидатор и постоянное атомарное резервирование
IP/мест. [Отчёт:112 tests passed](releases/2026-09-24-fleet-leases.ru.md) ·
[Схема хранения и recovery](fleet-leases.ru.md). Следующий конечный результат —
единая авторизация и remote adapter с fencing, затем идемпотентный
provision → ready → signed publish. До включения обязателен импорт старых адресов;
локальная generation не подменяет защиту от задержанных команд на gateway.
Шлюзовой журнал и worker теперь реализованы как локальный прототип:139 checks passed.
[Контракт fencing](fleet-gateway-fencing.ru.md) ·
[Отчёт и согласование Django7.1](releases/2026-09-24-fleet-fencing-admin-plan.ru.md).
Добавлены WG/AWG peer backend, bounded subprocess и SSH forced-command adapter:
163 tests passed. [Отчёт](releases/2026-09-24-fleet-wg-ssh.ru.md) ·
[Контракт/установка](fleet-wg-ssh.ru.md). Изолированная native WG/AWG
и SSH приёмка пройдена:12 сценариев,163 regression tests.
[Native-отчёт](releases/2026-09-24-fleet-native.ru.md) ·
[Повторяемый стенд](../pilot/fleet-native/README.ru.md).
Добавлены FleetAccess и FleetScheduler:201 tests passed; схема2 с явной миграцией.
[Контракт](fleet-access-scheduler.ru.md) · [Отчёт](releases/2026-09-24-fleet-services.ru.md).
Добавлен локальный offline publish после ready, WG/AWG2/schema2:269 passed.
[Контракт](fleet-publication.ru.md) · [Отчёт](releases/2026-09-24-fleet-publication.ru.md).
Далее verified ACK/previous hash и перенос offline→online с повторной авторизацией;
интеграция с рабочими Friends правами/API ещё впереди. По решению пользователя
приоритет изменён: ближайший шаг5.3а — managed AWG3.1, затем продолжение5.2 relay.
Код ещё не установлен на рабочие шлюзы; автономный TTL и TCP backend не реализованы.
5.3а — AWG3.1/dynamic IDs теперь выполняется первым;5.4/5.5 — Android/Linux/Windows;
5.6 — live failure gates. WG/AWG2 остаются для совместимости/регрессии без отдельного развития.
С расширением fleet предварительно14–22 рабочих дня; уточнить после leases/reconciliation.
Полный gateway failover остаётся этапом6; покупка VPS не запланирована.

## Снимок нагрузки24.09.2026

Read-only аудит: Friends18 устройств,14 не отозваны;5 устройств передавали
трафик через NL в20-секундном замере. CPU RU≈19%, NL6%; на RU iowait5–10%.
Число людей и суточные пики не установлены; текущий этап и версии не менялись.
[Метрики, границы измерения и оставшиеся проверки](releases/2026-09-24-server-usage.ru.md).

<a id="django-admin"></a>
## 7.1 Единая Django-админка: серверы, доступ и платежи

Согласовано пользователем24.09.2026. Одна панель для Family Connect:

- Серверы: карточка ID/страна/provider/IP, порты/транспорты, VPN-пул и capacity;
  provisioning → проверки → active → draining → disabled.
- Устройства и доступ: public bindings, leases, отзыв/срок доступа; без смены ключей.
- Подписки и платежи: тарифы, платёжные события и сроки доступа; повторные webhook
  не продлевают доступ повторно. Платёж меняет entitlement, не вызывает SSH напрямую.
- Операции: durable очередь, прогресс/ошибки/повторы, журнал действий и роли операторов.

Добавление сервера: карточка → проверка IP/пула → подготовка служб/firewall/monitoring
→ тестовый peer и проверка трафика → явное включение новых назначений. Удаление
карточки не освобождает IP: сначала draining, подтверждённая очистка, затем disabled.
Секреты подключения хранятся отдельно; private keys не попадают в обычные формы/логи.

Зависимость от5.2: админка вызывает общие сервисные операции и фоновые workers.
HTTP-запрос Django не держит SSH/настройку узла и не изменяет SQLite-таблицы в обход
инвариантов. Повторное нажатие и restart worker должны быть идемпотентны.
Разделение ролей платежей/инфраструктуры и история действий входят в приёмку7.1.

Порядок работ сохраняется:5.2 backend/fencing → оставшиеся5.3–5.6 → этап6 →7.1 UI.
Проектирование контрактов7.1 ведётся сейчас; сама Django-панель ещё не реализована.
Перенос authoritative fleet/access store в Django/PostgreSQL потребует явной миграции;
вторую независимо изменяемую копию leases или access создавать нельзя.
Критерий7.1: оператор через панель добавляет тестовый узел и выводит его в draining,
видит результат фоновых операций и платежи/доступ, а повторы и ошибки не теряют
leases, не дублируют оплату и не раскрывают секреты. Выбор платёжного провайдера
и конкретного хранилища секретов остаётся отдельным решением перед реализацией.

## Уточнение приоритетов24.09: Россия и третий транспорт

Пользователь согласовал перенос managed AWG3.1 в ближайшую работу.
Текущая позиция —5.2 ещё открыт; начинаем необходимую часть5.3 раньше остальных
задач5.2. Это смена порядка, не закрытие предыдущих критериев.

- **5.3а, ближайший шаг:** AWG3.1 в control schema/issuer/verifier, общие vectors,
  dynamic gateway IDs, проверка совместимости и отказа старых клиентов; далее
  native применение и российская сетевая приёмка. Совместимость нельзя включить
  одним удалением UNSUPPORTED_TRANSPORT_VERSION.
- AWG3.1 — приоритетный кандидат для основного UDP-подключения; VLESS/REALITY —
  альтернативный TCP-путь. Работоспособность проверять по конкретным сетям.
- WG/AWG2 — только совместимость, диагностика и регрессия; новые отдельные функции
  под них не развивать, действующие назначения автоматически не удалять.
- **5.3б, исследование дополнительного транспорта:** первый кандидат NaïveProxy
  HTTPS/HTTP2; сравнительный кандидат Hysteria2/QUIC. Это исследование, не решение
  включить оба runtime и не гарантия обхода российских блокировок.
- Для5.3б: стоимость сборок/обновлений Android/Linux/Windows, DNS/UDP/full-device
  routing, размер/CPU/RAM, revoke/секреты и совместимость с нашим lifecycle;
  российские домашняя и мобильная сети, UDP blocked, loss, смена сети и блок IP.
  Внедрять кандидат только при измеримом выигрыше относительно AWG3.1+REALITY.

## 5.3в — режим подключения в сетях с белыми списками (backlog)

> Backlog / secondary. Задача сохранена, но не является немедленным engineering step;
> текущий critical path — 5N (см. Current engineering priority выше).

Добавлен24.09 по прямому запросу пользователя; ориентир — продуктовый режим
«Белые списки» у Shuka. Задача включает исследование, реализацию и сетевую приёмку,
а не только изучение конкурента. [Требования и границы](allowlist-connectivity.ru.md).

- **5.3в.1 — обследование и выбор схемы:** определить доступные входные узлы на
  тестовых SIM/операторах; разделить фильтрацию IP/маршрутов, DNS, TLS и UDP.
  Выбрать транспорт и инфраструктуру по измерениям; не считать смену SNI или
  протокола доказательством доступности IP. Описать стоимость и пределы ёмкости.
- **5.3в.2 — стенд и реализация:** отдельный пул ingress и путь ingress→egress,
  интеграция с fleet/IPAM/доступом, signed profiles, ограниченная выдача адресов,
  клиентский режим и ограниченные повторы/переключение. Сохранять identity,
  проверку подписи, revision floor и rollback. Секреты — через действующее хранилище.
- **5.3в.3 — обновление и восстановление:** доставка свежих назначений при
  недоступном основном API, заранее сохранённые резервные точки, TTL/revoke;
  проверить достижимость самого канала Reticulum в ограниченной сети.
- **5.3в.4 — приёмка:** реальные мобильные сети минимум двух операторов с
  наблюдаемым режимом белых списков; первый вход, полезный трафик, DNS,
  длительное соединение, смена сети, блокировка ingress и получение замены.
  Фиксировать оператор/регион/время и ограничения. При отсутствии достижимого
  входа показывать понятный отказ, не бесконечное «подключение».
- **5.3в.5 — эксплуатация:** ёмкость/стоимость и health отдельно по ingress/egress,
  вывод узла из работы и замена адресов через fleet; отображение и управление
  режимом в будущей Django-админке7.1, без отдельного реестра назначений.

По следующему прямому запросу пользователя5.3в переведён в реализацию: выбран
XHTTP/TLS для первого стенда, код/локальные проверки готовы (см. checkpoint выше).
5.3а не закрыт и сохраняется в очереди; его проверка на телефоне отложена. Реализация5.3в.2 зависит от выбора проверенного входа,
5.2 и клиентского lifecycle;5.3в.3–4 связаны с этапом6. Выбор NaïveProxy/Hysteria2
в5.3б сам по себе не закрывает5.3в. Закупка нового узла — после выбора стенда.
Работоспособность Shuka у наших операторов не проверена; их протокол не установлен.

После5.3а продолжить5.2: verified ACK, offline→online/relay, доступ/migration.
5.3б не задерживает основную цепочку; не покупать серверы/домены до выбора стенда.
[Обоснование и первичные источники](releases/2026-09-24-transport-priorities.ru.md).

## Проверка продуктовой гипотезы

[Сравнение других проектов](releases/2026-09-24-competitor-recovery.ru.md)
уточняет5.2/6: независимая доставка, ограниченная выдача адресов и измеримое восстановление.
Это исследование, не реализованные функции и не изменение приоритета5.3а.

[Анализ конкурентного преимущества](releases/2026-09-24-vpn-market-assessment.ru.md):
проверять время восстановления и ручные действия, а не число транспортов.
Критический открытый вопрос — автоматический failover при offline signing и
недоступном основном API. Предложенные метрики/платный пилот — рекомендации,
не принятые SLA или новая смена очередности5.3а→продолжение5.2.

## Reticulum recovery: уточнение требований5.2/6

[Проект переноса службы по постоянному destination](reticulum-recovery-design.ru.md):
разделить service identity и transport ingress; multi-ingress/discovery, согласованный
backup/fencing, pull/ACK и тест миграции при блокировке прежних IP. Полная потеря
всех carrier paths требует внешнего bootstrap. Это дизайн, не выполненная приёмка;
ближайший согласованный кодовый шаг5.3а сохраняется.

В приёмку Reticulum включить [модель обнаружения](releases/2026-09-24-reticulum-threat-model.ru.md):
публичный peer, обычный подписчик и наблюдатель на сетевом пути клиента.
Приватный discovery/сегментация пока проектные меры; секретность выданных IP не гарантируется.
