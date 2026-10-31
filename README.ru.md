[English →](README.md)

# Family Connect

Принятый API/mailbox-адаптер restricted-чата выделен в общий Go-код; native VPN
использует тот же координатор. В Linux добавлен отдельный ограниченный IPC-канал
между родительской службой и native-worker. Пользовательская служба подключена
к уже действующему MESH для API/mailbox с проверкой UID и identity; локально
проверены сокеты, proof и отмена. Защищённый underlying DIRECT, service-only без VPN
и Windows broker **ещё не реализованы**. Приёмка установленного restricted-чата
NOT_RUN; это не завершённая поставка паритета.

В Linux реализованы полный ограниченный native106 JSON-export и отдельное согласие
на онлайн-диагностику на7 дней, проверенные локально без отправки в рабочий сервис.
Фоновой отправкой после закрытия GUI теперь владеет пользовательская служба;
изолированные D-Bus/systemd-проверки перезапуска и отзыва согласия проходят.
Приёмка установленной службы/обновления и Windows ещё не завершены.
[Инструкция RU/EN и точные ограничения](docs/clients/DESKTOP_DIAGNOSTICS106.md).

**Desktop parity106 разрабатывается, не выпущен.** Зафиксирован точный Android
source capsule; native workers Linux/Windows собраны, Linux helper/routing
прошёл локальные проверки, включая изолированный kernel TUN. Перенесён общий
readiness, health102 и GTK-путь MESH/отмена/профили; собран неподписанный offline-пакет
системного Linux-компонента. Есть снимки точного APK в эмуляторе и настоящих GTK-окон.
MESH, мессенджер, визуальная и установочная приёмка Linux/Windows ещё не завершены.
В GTK добавлены настоящие контакты/текст/история с зашифрованным хранилищем и
ключом в Secret Service; RNS mailbox проверен локально. Добавлены ограниченная
запись Opus/Codec2, предпрослушивание и явная отправка, проверенные на синтетическом
звуке. Уведомления с подтверждением системной службы, переходом в чат и сервисные
сообщения проверяются локально через GTK/D-Bus. Доставка работает на других вкладках
и после выхода из GUI через отдельную непривилегированную пользовательскую службу;
изолированные systemd/Secret Service/RNS проверки подтверждают восстановление без замены identity.
Управление объявлениями использует proof этого компьютера, явный предпросмотр и
серверные проверки роли/редакции; API/GTK проверены локально. Рабочие права не
выдавались, объявления в рабочем сервисе не публиковались.
Общая политика Auto сверена с17 сценариями принятого Java-контроллера и работает
в native-worker через ограниченный IPC. Linux-защита и отмена проверены на настоящем
изолированном ядре/TUN. Адаптер одной MESH-попытки использует тот же пакетный путь,
что и ручной MESH. Защищённое получение обычной конфигурации и AWG/TCP-попытки
переиспользуют native signer и существующие helper’ы. Реализованы root-координатор
Auto, capability-проверки, UID-привязанный IPC и восстановление intent через память
systemd. Локально проверены отмена и перезапуск/отзыв intent, не установленный VPN.
В GTK реализованы штатный клиент Auto и синхронизация подписанного root/user
catalog floor. Выбранный Auto отображается отдельно от фактического AWG/TCP/MESH;
пункт доступен только с проверенным установленным Auto-компонентом, не как
переименованный TCP. Установленная приёмка переключений и Windows broker ещё
не завершены; полного parity-установщика и публичного обновления пока нет.
AWG теперь сохраняет журнал владения ресурсами после исчезновения TUN. Настоящий
изолированный AWG3.1 проверен при падении процесса и очистке DNS/routes/firewall
без удаления чужих правил; это не приёмка установленного MESH/P1 или автовосстановления.
Приёмка реального аудиоустройства/обмена с Android, установленной службы/обновления, restricted service-only
доставка и Windows-мессенджер ещё впереди.
RNS bootstrap теперь имеет ограниченный native-адаптер и упакованный runtime,
проверенный настоящим локальным обменом; установленная/live-приёмка и Windows runtime ещё впереди.
[Полная матрица функций и статусов](docs/releases/2026-10-23-desktop-parity106.md).

**MESH (Media Encapsulated Secure Hop)** — собственный защищённый медиатранспорт
Family Connect. Текущий carrier — VP8/RTP, текущий медиапровайдер — Telemost;
название продукта от провайдера не зависит. Это пока не децентрализованная
multi-hop mesh-сеть. Android107 включает этот медиатранспорт;
медиатранспорт в desktop-клиенты ещё не интегрирован. См.
[модель и ограничения](carrier/README.md#mesh-product-contract) и
[текущий статус](docs/STATUS.md) и сведения о выпуске ниже.

Общий выпуск **beta107 / Android12+ / ARM64**: [скачать и обновить поверх](docs/getting-started.ru.md).
Приглашения и updater предлагают107 с MESH и тихими обновлениями VPN-уведомления.
CI/подпись/HTTPS проверены; проверка107 на телефоне владельца ещё не выполнена. Допуск не расширяется.

**Устойчивая связь для семей и личных устройств.**

Family Connect помогает оставаться на связи без необходимости понимать, какой
транспорт или сервер работает сегодня. Это не переключатель протоколов и не
«ещё один VPN»: направление продукта — непрерывность связи и автоматическое
восстановление. Быстрые недорогие VPN-транспорты остаются обычным путём;
restricted service carrier — резерв, а не основной режим.

Первый целевой пользователь — технически подготовленный член семьи, который
помогает близким и их устройствам оставаться на связи без постоянного объяснения
конфигураций. Семьи в разных странах, в том числе с родственниками в России, —
частый начальный контекст, но не географическое ограничение продукта.

**[Попробовать Android beta](docs/getting-started.ru.md)** · [Установка desktop](docs/clients.ru.md) · [Как это работает](#как-это-работает) · [Безопасность](SECURITY.md)

## Доступная beta — реализовано

Device Identity, Family admission, приглашения и provisioning существуют.
Beta-пользователи уже используют обычные AWG/TCP-подключения; Android уже имеет
VpnService/VPN lifecycle. Автоматическое управление обычными и restricted
транспортами **ещё не завершено как продукт**. Сейчас клиенты показывают выбор
региона/транспорта.

| Платформа | Последнее документированное распространение и ограничения |
| --- | --- |
| Android12+ / ARM64 | **0.1.18-beta107 / code107**; общий выпуск с MESH и тихим обновлением VPN-статуса; CI PASS, проверка107 на телефоне ожидается. |
| Linux | **0.2.11**, GTK 4/libadwaita; AppImage и DEB, прежний архив сохранён для advanced/manual и совместимости updater. Системные зависимости и VPN helpers ещё требуют настройки. |
| Windows 10 1809+ / 11 x64 | **0.2.15**; активация приглашением, отдельный подписанный каталог обновлений; у установщика нет доверенной подписи издателя. 0.2.14 сохранён как compatibility fallback; проверка проблемного Windows 10 устройства ожидается. |
| macOS / iOS | Выпуска клиента нет; iOS — поздняя работа после реальных beta-данных. |

Это последние документированные public/invitation версии, не новая проверка
артефактов или установленных устройств. См. [версии и контрольные суммы](docs/releases.md),
[проверки трёх платформ](docs/releases/2026-09-26-server-list-crossplatform.ru.md)
и [Linux packaging](docs/linux-appimage-deb.ru.md). Windows 0.2.12 и старше нужна
одна ручная переходная установка перед использованием отдельного каталога.

Паритет desktop с Android-мессенджером не заявляется. Android-уведомления при
погашенном экране проверены; задержки deep Doze и более широкая offline/restart
приёмка остаются открытыми. Это пилот, не production-ready сервис.

## Restricted-network R&D — экспериментально доказано

Изолированная инженерная приёмка прошла на пути **физический Redmi Android →
настоящий Telemost VP8/RTP carrier → Amsterdam EU gateway → TCP/DNS Internet**:

- Family TLS 1.3 authentication поверх selective-repeat ReliableStream,
  восстановление реальных RTP gaps и длительная надёжная передача данных.
- Несколько одновременных публичных HTTPS streams с проверкой TLS конечных сайтов,
  смешанный TCP + Family DNS workload, точная доставка байтов, fairness и bounded buffers.
- DNS containment/hardening назначений в проверенном core path.
- Automatic Room Broker через официальный Telemost API, OAuth только на сервере:
  Amsterdam подключается первым и сообщает READY; Android получает dedicated
  descriptor и входит без переданной оператором ссылки на комнату.

[Приёмка 5N.5](docs/releases/2026-09-28-webrtc-eu5-mux-dns.ru.md) ·
[Room Broker PASS](docs/releases/2026-09-28-webrtc-5n-room-broker.ru.md) ·
[Надёжность и длительный goodput](docs/releases/2026-09-27-webrtc-5n-perf2-reliable-envelope.ru.md)

**Это ещё не выпущенный whole-device restricted VPN для Android.** Принятый
Room Broker run использовал временный control ingress (SSH forwarding + adb reverse),
а не production restricted bootstrap. Если обычный Family API недоступен,
устройство пока не может самостоятельно получить первую dedicated room.
5N.6 full-device integration и Краснодар FIELD-1 не проводились; restricted mode
не развёрнут для текущих beta-пользователей. В этом пути нет generic UDP;
сохраняется global ReliableStream head-of-line blocking. Production capacity
и универсальная работа в белых списках не заявляются.

В одном сообщённом пользователем случае ограниченной сотовой сети/белых списков
Краснодара Family AWG 3.1 и TCP не работали, а связь Telemost оставалась доступной.
Это единичное полевое наблюдение, не утверждение обо всех сетях, операторах,
регионах или временах и не полевая приёмка restricted VPN Family.

## Как это работает

**Целевой сценарий (план для всех транспортов):**

```text
УСТАНОВИТЬ → принять семейное приглашение → ПОДКЛЮЧИТЬ
           → Family Connect выбирает/восстанавливает доступный путь → ПОДКЛЮЧЕНО
```

Обычные пользовательские состояния: **ПОДКЛЮЧЕНИЕ**, **ПОДКЛЮЧЕНО** и
**ВОССТАНОВЛЕНИЕ СОЕДИНЕНИЯ**; протоколы остаются в расширенной диагностике.
Модель — **семья → люди/устройства → связь**, а не аккаунт → сервер → файл
конфигурации. Общая family dashboard этой схемой не реализована и не заявляется.

**Сейчас:** получите приглашение, установите клиент, вернитесь к исходной ссылке
и откройте приложение для активации. Разрешите Android VPN и используйте текущие
элементы выбора региона/подключения. Новая sideload-установка ещё требует возврата
к приглашению; полностью автоматическая активация не заявляется.
Мессенджер — отдельная функция, а не следствие подключения VPN.

**Далее:** restricted bootstrap (`5N-BOOT-1`) → Android full-device integration
(`5N.6`) → минимальный Connectivity Orchestrator → Краснодар FIELD-1 →
продуктовая beta на 50–100 пользователей. [Авторитетный roadmap](docs/PLAN.md).

## Безопасность и приватность

Сторонние carriers недоверенные. Граница защиты restricted path —
**Device Identity / Family admission / Family TLS**, не секретность Telemost room.
Telemost — первый доказанный restricted carrier, не сам продукт и не вечная
архитектурная зависимость; carriers остаются заменяемыми адаптерами.

Gateway доверенный и видит метаданные назначений. Не обещаются анонимность,
zero logging, гарантированный обход или гарантированная доступность. Будущие
метрики успешности соединений не должны собирать содержимое трафика и историю
просмотров; это план, не описание уже работающей системы телеметрии.

[Границы защиты](SECURITY.md) · [Приватность](docs/privacy.md) ·
[Проверка обновлений](docs/updates.ru.md)

## Архитектура

Архитектура разделяет **control/product plane**, недостающий
**restricted bootstrap/recovery plane** и экспериментально доказанный **data
plane**. Планируемый Connectivity Orchestrator выбирает доступные возможности
сети; обычные AWG/TCP пути не проходят через экспериментальный 5N mux.

[Архитектура и продуктовые решения](docs/architecture.md) ·
[Device Identity](docs/adr/001-identity-provisioning.ru.md) ·
[Provisioning](docs/provisioning-provider.ru.md) · [Текущее состояние](docs/STATUS.md)

## Разработка

Начните с [CONTRIBUTING.md](CONTRIBUTING.md) и [карты документации](docs/README.md).
Исходники, CI builds, установленные клиенты и public artifacts — разные состояния;
тестовая CI-подпись не воспроизводит распространяемую friends APK. У текущего main
есть открытые CI failures, записанные в STATUS; синхронизация репозитория не
является релизом или deployment.

| Компонент | Исходники |
| --- | --- |
| Android / Linux / Windows | [Android](clients/android/) / [Linux](clients/desktop/) / [Windows](clients/windows/) |
| Identity и provisioning | [control](control/) / [device_identity](device_identity/) / [provisioning](provisioning/) |
| Experimental restricted core / Room Broker | [carrier](carrier/) / [roombroker](carrier/roombroker/) |
| Мессенджер / отдельный QUIC relay lab | [messenger](messenger/) / [core](core/) |

## Участие в проекте

Полезны сообщения об ошибках, документация и предметные изменения. Указывайте
платформу и точную версию, удаляйте личные данные. См. [инструкцию участника](CONTRIBUTING.md)
и [сообщение об уязвимостях](SECURITY.md).

## License / Лицензия

Family Connect — проприетарное ПО с публично доступными исходниками (source-available).
Публичный репозиторий не делает Family Connect open source. Все права сохранены,
кроме явно установленных условий сторонних компонентов. См. [LICENSE](LICENSE),
[Third-Party Notices](THIRD_PARTY_NOTICES.md) и [аудит](docs/legal/DEPENDENCY_LICENSE_AUDIT.md).
Публичность не разрешает использование кода в другом продукте, распространение
производных, продажу копий, перепубликацию существенных частей или использование
бренда. Права третьих лиц и ранее выданные разрешения сохраняются. Права на
распространение классических смайликов остаются неустановленными.

Family Connect is source-available proprietary software. The source repository
being public does not make Family Connect open source. All rights are reserved
except where explicitly stated for third-party components. See [LICENSE](LICENSE),
[Third-Party Notices](THIRD_PARTY_NOTICES.md) and the [license audit](docs/legal/DEPENDENCY_LICENSE_AUDIT.md).
Public visibility grants no general reuse, derivative distribution, resale,
substantial republication or branding permission. Existing third-party rights and
prior valid grants are preserved. Classic smiley redistribution rights remain unresolved.
