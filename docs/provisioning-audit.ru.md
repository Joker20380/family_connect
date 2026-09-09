# Аудит перехода к платформе без ручных конфигураций

База: `80a8f67`, 09.09.2026. Проверен исходный код; это не проверка текущего состояния серверов или реального подключения физических Android/Windows. Английская версия: [provisioning-audit.en.md](provisioning-audit.en.md).

## CURRENT — что уже существует

| Слой | Код | Реализовано |
|---|---|---|
| Продукт | `scripts/activate_windows.py`, `scripts/register_pilot_peer.py` | Ручная активация Windows и регистрация публичного ключа на gateway; аккаунтов, семей и подписок нет |
| Управление | `control/app.py`, `scripts/admin.py`, `core/src/discovery.rs` | Подписанный общий каталог, несколько HTTPS bootstrap, сроки действия, атомарный кеш и защита от отката |
| Данные | `clients/desktop/backend.py`, Android `ConnectionService.java`, Windows `Broker.cs`, `Native.cs`, `Core/Activation.cs` | Существующие платформенные подключения WireGuard |
| Экспериментальная сеть | `core/src/main.rs`, `tls.rs`, `packet.rs`, `data/*.sh` | mTLS/QUIC, переключение relay, управляемый exit; отдельно от пользовательских приложений |
| Телеметрия | `scripts/test_*.sh`, `scripts/test_*.py`, локальные статусы и журналы | Синтетические проверки; нет сбора событий беты, HealthEngine и PolicyEngine |

**Reticulum и WebRTC в коде отсутствуют.** В лаборатории используется P-256 identity с сертификатом, Windows идентифицируется публичным ключом WireGuard. Это не Reticulum Device Identity. Независимость identity от IP доказана в лабораторной модели, но ещё не внедрена единообразно в приложения.

## Ответы на обязательные вопросы

1. **Можно ли без физического .conf?** Windows уже не требует пользовательский .conf, но требует вручную полученный `.fcactivation`; внутри есть защищённые `.conf.dpapi`. Android принимает конфигурацию в памяти, однако пользователь импортирует профиль. Linux импортирует временный .conf в NetworkManager; после импорта исходный файл не нужен. Полностью автоматического подключения нового устройства пока нет.
2. **Где формируется runtime?** Windows — `Core/Activation.cs`, хранение DPAPI в `Store.cs`. Android — разбор строки из `ProfileStore.java` в `ConnectionService.java`. Linux — проверка и импорт через nmcli в `backend.py`. Лабораторные shell-скрипты используют команды wg.
3. **Где Reticulum identity?** Нигде. Лабораторный ключ — `IDENTITY_DIR/key.der`. Windows создаёт собственный WG-ключ локально в защищённом ProgramData. Android шифрует импортированный профиль через Android Keystore, но пока не генерирует WG-ключ непосредственно на телефоне.
4. **Аутентификация?** Лаборатория: mTLS и членство в подписанном каталоге. Windows: SID для локального broker, подписанная активация конкретного WG-ключа, затем WG handshake. Код FC1 публичен и сам по себе не доказывает владение identity. Регистрационного challenge нет.
5. **Доставка provisioning?** Пользовательские приложения — ручная доставка активации/профиля; лаборатория — HTTPS/кеш каталога. Единого ProvisioningTransport нет.
6. **Кто выбирает сервер?** Оператор/профиль, в лаборатории фиксированные имена gateway и список relay. Контроллера по качеству сети нет.
7. **Кто знает здоровье?** Проверки процесса/API и синтетические тесты. Агрегатора результатов реальных подключений нет.
8. **Телеметрия?** Локальные статусы, технические сообщения, JSON-результаты тестов. Нет базы событий, стабильной таксономии ошибок, retention, dashboard и измерения crash-free sessions.

## TARGET / GAPS — что нужно реализовать

Сохранить четыре независимых слоя. Product разрешает устройству пользоваться услугой; Control выпускает неизменяемое желаемое состояние; Data подключает; Telemetry измеряет. Health рассчитывает качество, Policy выбирает, Provisioning публикует. ConnectivityCore получает проверенную модель без HTTP/RNS-зависимостей.

Отсутствуют: отдельная локальная Reticulum identity, proof of possession, семьи/entitlement, подписанная привязка transport keys, подписанное и зашифрованное адресное provisioning, общий verifier, HTTPS/RNS/cache адаптеры, версии known/verified/applied/good, ACK, восстановление, автоматическая смена gateway, ограниченные retry/failover, сбор событий, health, policy и метрики беты.

## REUSABLE COMPONENTS

Сохраняем WireGuard engines, Windows broker/ACL/DPAPI, Android GoBackend/Keystore, Linux NetworkManager, проверку подписи/адресата/срока активации Windows, лабораторные проверки каталога и атомарного кеша. Это полезные компоненты, но не готовая автоматическая платформа. Старые trust domains и v1 API сохраняются; новый протокол получает отдельную версию и область подписи.

## RISKS — совместимость

* Linux: сохранять UUID, маршруты и DNS существующих NM-подключений. Автоматический путь должен использовать типизированный адаптер; импорт остаётся временным fallback.
* Android: сохранить сервис и GoBackend, учесть уничтожение процесса и ограничения хранилища ключей. Новая identity не должна ломать старый зашифрованный профиль.
* Windows: сохранить SID/ACL/проверки владельца, bundled drivers и старую активацию. Требуемый upstream DLL файл остаётся внутренней деталью адаптера; бизнес-логика постепенно перестаёт зависеть от его пути.
* Настоящий Reticulum на трёх платформах требует отдельной проверки упаковки и совместимости с reference implementation. Назвать заглушку ReticulumTransport недостаточно. Не выводить identity из WG-ключа, не создавать собственную криптографию.
* Лаборатория закрывает активные соединения после истечения каталога. Короткий offline-тест не доказывает переживание длительного отказа. До изменения нужно определить offline lease, отзыв и разрешённое восстановление.
* Переключение relay не равно смене gateway: другой публичный IP/NAT может разорвать TCP. Непрерывность видеозвонков при смене exit не гарантирована.
* Подпись Windows-активации сейчас выполняется на операторском ноутбуке. Производственные ключи подписи provisioning должны находиться на серверной инфраструктуре с процедурами ротации и восстановления.
* Предполагаемый рабочий exit сейчас один, российский. Схема нескольких провайдеров не создаёт физическую резервность. На снятый с VPN второй сервер с сайтами ничего не разворачивать; старые документы о двух серверах описывают историю.
* CI не заменяет испытания новых клиентов на физических устройствах. Отсутствие издательского сертификата Windows — отдельная задача, не решаемая подписью provisioning.

## MIGRATIONS — база данных

Существующей реляционной БД Family Connect нет. Создать отдельную; не использовать БД другого приложения.

1. Accounts, families/memberships, subscriptions, entitlements, devices/public identity, независимые public transport keys, одноразовые challenge и хеши invitation с TTL. Уникальность identity, независимый отзыв устройств.
2. Providers, gateways/ASN/region/capabilities/capacity, адресные allocations, неизменяемые provisioning revisions/digests, entitlement revision, ссылки на signing key, ACK, транзакционный outbox для установки gateway peers. Сериализовать выдачу версий; не публиковать рабочее состояние до установки необходимых peers.
3. Ограниченные технические события, deduplication, сменяемые псевдонимы, сроки хранения, агрегированные health snapshots. Не делать device ID и raw IP метками Prometheus.

Старый WG-ключ не превращать в Reticulum identity. Создать отдельную identity локально, доказать владение и привязать существующий либо новый WG public key. Старый путь сохраняется до проверки миграции. Приватные ключи не входят в миграции БД.

## FILES/MODULES TO MODIFY

* `control/app.py`, `control/requirements.txt`, `control/requirements.lock`: отдельные v2 API и зависимости, сохранить v1.
* `clients/desktop/app.py`, `clients/desktop/backend.py`: автоматическое получение состояния и типизированный NM-адаптер.
* `clients/android/app/src/main/java/com/familyconnect/app/MainActivity.java`, `ConnectionService.java`, `ProfileStore.java`: onboarding, проверенное состояние, локальное хранение.
* `clients/windows/MainForm.cs`, `Broker.cs`, `Store.cs`, `Core/Activation.cs`: автоматический путь рядом с legacy; изоляция runtime-файлов.
* `.github/workflows/test.yml`, `.github/workflows/clients.yml`: новые проверки протокола и регрессии.
* `compose.yaml`, `README.ru.md`, `README.en.md`: отдельные сервисы и инструкции после готовности реализации.

## FILES/MODULES TO ADD

Это план, а не перечень уже работающих функций.

* `provisioning/models.py`, `envelope.py`, `verifier.py`, `provider.py`, `transports/base.py`, `transports/https.py`, `transports/cache.py`, `transports/reticulum.py`.
* `control/product/models.py`, `control/product/api.py`, `control/provisioning/service.py`, `control/provisioning/api.py`, `control/gateways/reconciler.py`.
* `control/migrations/001_product.sql`, `002_provisioning.sql`, `003_telemetry.sql`.
* `telemetry/events.py`, `control/telemetry/api.py`, `control/health/engine.py`, `control/policy/engine.py`.
* `clients/desktop/device_core.py`, `clients/desktop/provisioning_provider.py`.
* В существующем Android Java package: `DeviceIdentityStore.java`, `ProvisioningProvider.java`, `ConnectivityCore.java`.
* Windows: `Core/DeviceIdentity.cs`, `Core/ProvisioningProvider.cs`, `Core/ConnectivityCore.cs`.
* `tests/test_provisioning_security.py`, `test_provisioning_transports.py`, `test_provisioning_recovery.py`, `test_telemetry_privacy.py`, `test_health_policy.py`; нативные тесты рядом с имеющимися.

Python-модели не становятся автоматически общей библиотекой Android/Windows: нужны protocol fixtures/schema и эквивалентная нативная валидация. Формат envelope и упаковку RNS определить через ADR и interoperability tests до реализации security-critical кода.

## STAGED COMMIT PLAN / TEST PLAN

1. Этот двуязычный аудит без runtime-изменений.
2. Стабильная таксономия ошибок и ограниченный контракт технических событий с тестами отклонения; это ещё не сбор событий.
3. ADR, проверка настоящей RNS identity/упаковки и стандартного криптографического envelope. Описать публичные bootstrap anchors, ротацию destinations/keys, отказ bootstrap, offline leases и разрешённый rollback.
4. Product DB/API; тесты challenge/invitation/key binding: replay, чужое устройство, гонки, expiry, независимый revoke.
5. Provisioning/verifier/HTTPS/cache: подпись, расшифровка, адресат, схема, entitlement, монотонность, crash-safe сохранение. Непроверенный hint latest_version не поднимает доверенный rollback floor.
6. Автоматический Linux, затем Android и Windows с сохранением engines/manual flow. Fresh-install без импорта, приватные ключи локальны; нативные сборки и физические сетевые проверки.
7. Настоящая RNS-доставка тех же envelopes, общая проверка и независимый ConnectivityCore. Отказ управления не закрывает действующий разрешённый туннель; валидный кеш позволяет reconnect.
8. v20 → v21, durable ACK, failed apply, known-good recovery, primary failure/fallback success, исчерпание retry/backoff, peer reconciliation перед публикацией.
9. Ingestion/export/health: фиксированные данные для success rate, median/p95, disconnect с определённым знаменателем, reconnect, недостаток выборки. Раздельно учитывать клиентские события, probes и gateway metrics, исключать дубли. Проверять privacy/размер/rate/retention/сегментацию.
10. Осторожная policy: исключать явно нездоровые gateway, учитывать регион, стабильные оценки и альтернативы. Не перенаправлять всех по малой выборке. Сначала контролируемая бета, потом deprecation manual flow.

На соответствующих этапах запускать существующие pytest, locked Rust tests, лабораторные auth/offline/failover/revocation и сборки трёх платформ. Телеметрия отклоняет лишние поля, URLs, DNS, payloads и ключи; свободные строки в разрешённых измерениях тоже требуют ограничений. Определить lifecycle crash-free sessions и знаменатели метрик заранее.

## Статус acceptance A–O на момент аудита

A — частично Windows UX. B — частично лабораторная identity. C/D/E — отсутствуют в целевых клиентах. F — Windows генерирует локально, Android пока импортирует операторский профиль. G — Windows имеет часть проверок подписи/адресата, но нет нового immutable encrypted provisioning. H/J — отсутствуют в продуктах. I — WG работает независимо от backend, лаборатория ограничена сроком каталога. K/L/M — beta plane отсутствует. N — нужна модель провайдеров. O — сохранять исходный функционал и проверять каждую платформу до rollout.

## Первый шаг реализации

Добавлен `telemetry/events.py`: ограниченный контракт ошибки со стабильными кодами, платформой и числовой версией приложения. Лишние поля, произвольные сообщения и неправильные типы отклоняются без включения исходных значений в текст ошибки. Проверки — `tests/test_telemetry_privacy.py`. Сбор/отправка событий, клиентская инструментация и изменение provisioning пока не включены. Целевые тесты телеметрии, Windows-активации и desktop: 31 passed. Полная нативная и сетевая приёмка ещё предстоит.
