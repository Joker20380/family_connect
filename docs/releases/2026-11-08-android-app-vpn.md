# ANDROID-APP-VPN · 8 ноября 2026

## Объём и исходная точка

Отдельная ветка от main `09f1aae5e11f0b766bf3fba20010bc0d08c3ed6d`.
Владелец разрешил продолжить продуктовый план независимо от физического cold/whitelist;
это не новое измерение и не изменение сохранённых PASS/FAIL/NOT_RUN.
Remote branches и локальные артефакты проверены: максимальный занятый code121;
для нового source/package-кандидата выделен122. Принятые121 и прежние байты неизменны.
Release-кандидат пока не собран/не установлен/не опубликован; updater и download links прежние.
Изолированный debug/x86_64 APK используется только на собственном API35 AVD.

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

## Gate и текущие доказательства

- Адресная Java compilation и7 policy JVM tests PASS до резервирования версии.
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
  и следующий Connect с новой политикой — адресный API35 PASS. Удаление последнего
  выбранного package и повторная установка — адресный PASS в совместном запуске;
  полный запуск прерван сбоем GL-контекста локального NVIDIA эмулятора, не выдан за PASS.
- Усилена повторная проверка package binding после establish; исторический health89
  сохранён отдельным byte-exact fixture с прежним SHA. Его10 сценариев и те же
  сценарии текущего health проходят; JNI dispatcher проверяет новый DNS export.
  Адресный release/source gate:72 PASS; исторический/current health:2 PASS.
- Process restart/update, API27/28, RU/крупный шрифт,
  окончательный native/MESH adapter, обязательный CI/review/merge — **NOT_RUN**.
- UI и unit tests сами по себе не подтверждают завершение функции.

Production, телефон владельца, подписки, cohort, identity, периоды, G4, cold-entry,
renewal и updater не изменяются. Локальные стенды используют synthetic identities.
