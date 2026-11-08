# ANDROID-APP-VPN · 8 ноября 2026

## Объём и исходная точка

Отдельная ветка от main `09f1aae5e11f0b766bf3fba20010bc0d08c3ed6d`.
Владелец разрешил продолжить продуктовый план независимо от физического cold/whitelist;
это не новое измерение и не изменение сохранённых PASS/FAIL/NOT_RUN.
Remote branches и локальные артефакты проверены: максимальный занятый code121;
для нового source/package-кандидата выделен122. Принятые121 и прежние байты неизменны.
Release-кандидат проходит штатный hosted package gate; не установлен и не опубликован,
updater и download links прежние. Изолированный debug/x86_64 APK используется только
на собственных последовательных AVD, с NVIDIA/KVM на локальном исполнителе.

## Реализация и источники

Существующие точки: AWG `TunnelEngine`/GoBackend, TCP `TcpTunnelEngine`,
`RestrictedTunnelEngine`, Auto `AutomaticVpnOwner.replace`, включая blocking guard.
Одна локальная immutable `AppVpnPolicy`, Android validator/адаптер и отдельное private
SharedPreferences-хранилище. Списки INCLUDE/EXCLUDE раздельные; миграция — ALL без
исключения Family Connect. В persisted connection-request сохраняется active snapshot;
sticky resume читает его, не новую pending-настройку. Исходные server profiles не меняются.

QUERY_ALL_PACKAGES нужен для основной VPN-функции: выбор установленных приложений,
включая нелончерные/system/shared-UID компоненты текущего Android user. Более узкий
launcher-query не перечисляет такой набор. Список и выбор не уходят в HTTP, телеметрию
или обычные логи; рабочий профиль не обещается доступным из личного профиля. Shared UID
имеет одну OS-политику; UI отмечает группу. Системный lockdown не переключается.
Manifest содержит адресную lint-аннотацию только для этого разрешения: проверено,
что launcher-only queries не покрывают требуемую основную VPN-функцию. Остальной
lint и обязательные gates сохранены; это не разрешение на публикацию в Google Play
без отдельной декларации использования package visibility.

## Gate и текущие доказательства

- Локальный debug JVM:472 tests PASS, включая7 policy tests; lintDebug PASS.
- API35 NVIDIA/KVM: реальные независимые Alpha/Beta UID, ALL/INCLUDE/EXCLUDE,
  AWG/TCP DNS/verified HTTPS и IPv6 внутри VPN — PASS на промежуточном исходнике.
  Guard блокирует выбранный UID, не захватывая намеренно исключённый; pending не
  меняет активную политику. MESH использует реальную production owned-TUN точку,
  но REALITY carrier в этом тесте подменяет MESH wire; это не carrier-приёмка.
- API35 Auto AWG→TCP recovery с неизменным snapshot — PASS после воспроизведения
  EPERM у Android Network.bindSocket для исключённого VPN-owner UID. Исправление:
  ограниченный DNS probe внутри действующего authenticated carrier; приложение
  не добавляется скрыто в allowlist. Серверные профили и socket protect сохранены.
- UI→сохранение→реальный TCP TUN→два UID и pending — PASS на API35. Реальные
  view-renderings осмотрены (EN, длинное имя); FLAG_SECURE остаётся включённым.
- Новый AWG health demultiplexer: адресные Go race tests PASS; native x86_64
  пересобран из закреплённых зависимостей. Это ещё не окончательный ARM artifact.
- ConnectionService explicit Connect, invalid pending, сохранённый resume snapshot
  и следующий Connect с новой политикой — PASS в полных7-test запусках API35 и API27.
  Удаление последнего выбранного package/переустановка и старый binding также проверены.
  Resume selector в этом тесте не выдаётся за OS sticky restart процесса.
  Прежние прерванные запуски из-за GL-контекста NVIDIA сохранены как infrastructure
  failures, не заменяют последующие самостоятельные завершённые receipts.
- API27:7 runtime tests и RU/font1.5 UI→TCP test PASS; длинные названия, поиск,
  selected/pending, Save/Back осмотрены на реальных View renderings с FLAG_SECURE.
  Исправлено вытеснение списка/кнопок крупным текстом: header прокручивается,
  пояснение Android открывается отдельно. API35 ранний крупношрифтовый отказ сохранён.
  DNS probe стенда теперь ждёт ограниченный8s resolver budget (фактический успешный
  API27 ответ после переключения4.240s превышал прежние3s); timeout не считается PASS.
  Synthetic AWG DNS responder больше не копирует счётчики отсутствующих EDNS sections.
- Усилена повторная проверка package binding после establish; исторический health89
  сохранён отдельным byte-exact fixture с прежним SHA. Его10 сценариев и те же
  сценарии текущего health проходят; JNI dispatcher проверяет новый DNS export.
  Адресный release/source gate:72 PASS; исторический/current health:2 PASS.
- После UI/fixture corrections адресные source/release/orchestrator/health tests:60 PASS,
  включая8 дополнительных carrier/cancel/budget случаев. Исторические
  health89 и baseline hashes сохранены; новый Restricted contract проверяет порядок
  через валидирующий adapter, а не прежнюю буквальную строку `.establish()`.
- API28, process restart/update format fixtures и окончательный ARM package проходят
  отдельные gates. Финальные результаты, source/native/APK hashes и CI/review/merge
  закрепляются в [PR12](https://github.com/Joker20380/family_connect/pull/12), без
  косметического post-CI head. Пока этих receipts нет, эти gates не приняты.
- UI и unit tests сами по себе не подтверждают завершение функции.

## Границы интерпретации

Два probe APK имеют разные UID и сами выполняют default-network DNS и HTTPS с
проверкой сертификата/hostname одноразового тестового CA. IPv6 внутри реальных AWG/TCP
проверяется; direct IPv6 в эмуляторной сети отсутствует и не выдаётся за public IPv6 PASS.
MESH per-app проверяет production TUN/guard adapter с REALITY substitute carrier,
не новую Telemost/field/cold-приёмку. API35/27 прямой и VPN пути различаются ответами
серверов, а не значком подключения. Общий policy не меняет подписанные профили.
Legacy managed-preview ControlTrafficHealth сохраняет обязательный kernel-VPN HTTPS;
эту отдельную preview-схему не ослабляют до DNS-only. Friends сохраняет собственный
identity/readiness путь. [Порядок использования](../android-app-vpn.ru.md).

Production, телефон владельца, подписки, cohort, identity, периоды, G4, cold-entry,
renewal и updater не изменяются. Локальные стенды используют synthetic identities.
