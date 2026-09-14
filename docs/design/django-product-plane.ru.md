# Django, оплата, мониторинг и Reticulum identity

Направление от 14.09.2026: пользователь предложил Django для оплаты/мониторинга
и явно запросил привязку клиента к криптографическому ключу Reticulum.
Это проект интеграции: Django и платежи ещё не реализованы/не развёрнуты.
Приоритет VPN Linux/Windows/Android сохранён.

## Identity как основание доступа

Устройство идентифицируется постоянной Reticulum identity: публичный набор X25519
для шифрования и Ed25519 для подписей. Закрытый набор создаётся на устройстве и
не передаётся серверу. Identity hash служит для поиска; авторизация требует
доказательства владения ключом. Не путать identity hash и destination hash,
зависящий также от aspects. [RNS Identity API](https://reticulum.network/manual/reference.html).

Android ControlIdentity.publicIdentity/reference/proveTransportKey уже соответствует
этой схеме. Серверные device_identity/device.py и control/product/store.py проверяют
подписанный одноразовый challenge, audience и привязку отдельного WG public key,
срок challenge, приглашение, entitlement и лимит устройств. Закрытые RNS/WG ключи
независимы. Полный Android enrollment flow ещё нужно подключить.

Предлагаемая модель: Account/Family → Subscription/Entitlement → DeviceIdentity
→ TransportKeyBinding. Аккаунт объединяет оплату и устройства; VPN разрешён
подтверждённой identity. Email/телефон не обязательны для этого протокола.
Вход плательщика в кабинет требует отдельной реализации (возможен challenge-response);
знание identity hash само по себе не авторизует запрос.

По умолчанию каждому устройству отдельная identity для независимого отзыва.
Оплата продлевает entitlement и не заменяет ключ. Потеря закрытого ключа требует
явного восстановления доступа владельцем подписки и отзыва старого устройства;
ошибка Keystore не приводит к неявной смене identity. Перенос/восстановление ключей
и root rotation — отдельные задачи. Server signing root независим от device keys.

## Django и существующий product API

Предлагаются Django + PostgreSQL для кабинета, тарифов, подписок, платёжных событий,
admin, ролей и аудита. ORM/auth/admin входят в Django:
[официальный обзор](https://www.djangoproject.com/start/overview/).

Существующий API регистрации — FastAPI/SQLite. Проверенные challenge/enroll/
provisioning контракты сохраняются. Django не пишет напрямую в его SQLite и
не запускает VPN-команды из HTTP handler. Нужен внутренний аутентифицированный
entitlement adapter с idempotent operation_id и проверкой revision: этот контракт
пока не реализован. ProductStore остаётся источником действующих VPN entitlement;
Django хранит коммерческое состояние и статус применения. Будущая миграция на
PostgreSQL должна сохранить IDs/revoke/audit и исключить двойную запись.

## Оплата

Order → provider checkout → проверенный webhook → PaymentEvent → Subscription
→ transactional outbox → entitlement adapter → подтверждение применения.
Сумма/валюта/заказ сверяются с серверными данными; browser return не активирует VPN.
Provider + event_id уникальны. Повторы и доставка не по порядку не продлевают
подписку повторно. Событие, изменение подписки и outbox записываются одной
DB-транзакцией; worker retries идемпотентны. Refund/cancel/chargeback требуют
явной политики переходов и аудита. Данные карт в Django не хранятся.
Провайдер, валюта, юрисдикция и тарифы пока не выбраны.

## Мониторинг

Django показывает подписки, устройства, последний ACK/доставку и доступность шлюзов
с timestamp и unknown/stale. Offline не означает revoke. Prometheus предлагается
для метрик/алертов, Grafana — для графиков. Проверять health/handshake age,
transport errors, lease expiry, ACK backlog, latency provisioning, reconciliation,
серверные ресурсы. Биллинг опирается на события транзакционной БД, не на метрики:
[ограничения Prometheus](https://prometheus.io/docs/introduction/overview/).

Не собирать трафик/посещаемые сайты, private keys или профили. Identity в кабинете
видна по ролям; public metrics labels не содержат ключи и не создают ряд на каждое
устройство. Нужны backup/restore и проверка доступа операторов.

## Очерёдность

Сначала закончить enrollment/resume и VPN acceptance на трёх платформах. Затем
Django models/admin и entitlement adapter; тесты idempotency/concurrency/revoke/
downstream outage. Далее provider sandbox с проверкой webhook signatures/replay/
порядка событий/возвратов/worker crash, read-only мониторинг и алерты. Приёмка:
«оплата → право identity → подписанная config → device ACK → revoke».
