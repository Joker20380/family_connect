# Аутентифицированная выдача provisioning и кеш

Обновление: текущая migration v3 требует [staging и подтверждения gateway](gateway-reconciliation.ru.md). Описание ручного --peers-ready ниже относится к завершённому этапу v2; этот флаг удалён. Используйте команды из нового документа.

10.09.2026. Локальный продуктовый этап, без развёртывания и изменения VPN peers.

## Выдача и версии

Отдельный product API предоставляет `POST /v2/provisioning/challenge`: JSON только с
`public_identity` и `wireguard_public_key` в каноническом base64. Устройство должно
быть зарегистрировано, его ключ и entitlement — действовать. Ответ содержит
`challenge`, `expires_at`, `audience=family-connect/provisioning-fetch/v1`.
Challenge живёт до 120 секунд (не дольше entitlement), хранится только как SHA-256,
привязан к identity и WG key. На устройство максимум 16 непогашенных challenge.

`provisioning.auth.prove(device, challenge)` подписывает отдельный domain и audience,
схему 1, оба публичных ключа и challenge. Полный proof передаётся JSON в
`POST /v2/provisioning/fetch`. Registration proof здесь не принимается.
В одной транзакции проверяются challenge, ключ, device revoke, entitlement и
последняя опубликованная версия; challenge гасится вместе с успешной выдачей.
Один proof обслуживается ровно один раз, включая конкурентные запросы.

Ответ 200 — сохранённый JSON envelope с ciphertext/signature; никакие приватные
ключи не передаются. Для повторной загрузки после потери ответа нужен новый challenge:
он вернёт **те же байты** последней версии, пока она разрешена. Отдельного ACK нет;
выдача не означает применение туннеля. Нет fallback к более старой серверной версии.
400 `INVALID_REQUEST`, 403 `PROVISIONING_REJECTED`, 503 `PROVISIONING_UNAVAILABLE`.
Ошибки фиксированные, body ограничен, ответы `no-store`. TLS, ingress timeouts,
rate limiting и исключение секретных body из логов нужны как для регистрации.

Migration v2 расширяет отдельную SQLite БД таблицами challenge и неизменяемых
версий. Миграция v1→v2 сохраняет регистрации и выполняется транзакционно. Версии
монотонны отдельно для каждого устройства; fetch их не увеличивает. История хранит
зашифрованные envelopes и публичные метаданные lease/entitlement/key. Она не является
логом VPN-трафика. Очистка истории пока отсутствует; нельзя удалять максимальный
revision или восстанавливать старую БД как способ обновления. Требования backup и
прав доступа из [регистрации](registration.ru.md) сохраняются. После restore старой
БД клиент может отвергнуть версии до превышения сохранённого floor; автоматического
сброса floor нет.

## Оператор

```sh
python -m control.product.admin --database state-product/product.db migrate
python -m control.product.admin --database state-product/product.db init-provisioning-signer --key-directory state-product/signing
```

Команда создаёт отдельную серверную RNS signing identity в `signer.key` (0600,
каталог 0700); повторный запуск не заменяет ключ. В stdout только публичный anchor.
Его надо доставить клиенту по заранее доверенному каналу; TOFU и ротация не добавлены.
HTTP-процесс не загружает signing private key: он обслуживает готовые envelopes.

Файл `network.json` содержит **только** `addresses`, `dns`, `gateways`, например:

```json
{
  "addresses": ["10.77.0.4/32"],
  "dns": ["1.1.1.1"],
  "gateways": [{
    "gateway_id": "be-1", "provider_id": "provider-1", "region": "BE",
    "transport": "wireguard", "endpoint": "198.51.100.1", "port": 51820,
    "public_key": "REPLACE_WITH_CANONICAL_BASE64_WG_PUBLIC_KEY"
  }]
}
```

Адрес gateway выше — пример. Оператор предварительно устанавливает peer и проверяет
уникальность адреса и работоспособность **каждого** кандидата. Затем:

```sh
python -m control.product.admin --database state-product/product.db publish-provisioning DEVICE_IDENTITY --network network.json --key-directory state-product/signing --lease-seconds 3600 --peers-ready
python -m control.product.admin --database state-product/product.db provisioning-versions DEVICE_IDENTITY
python -m control.product.admin --database state-product/product.db prune-challenges
```

`--peers-ready` — явное утверждение оператора, не автоматическая проверка gateway.
Revision, recipient, WG key, entitlement и lease определяет сервер из БД; клиент
их не выбирает. Lease максимум 24 часа, не дольше entitlement. Продление требует
новой публикации. Подпись и сохранение выполняются в транзакции; ошибка не расходует
revision. Автоматическое распределение адресов, reconciliation/outbox и снятие peer
при revoke остаются следующим этапом. Не публиковать рабочие конфигурации без peers.

## Linux reference client

`ProvisioningClient(http_client, device, cache)` использует настроенный `httpx.Client`
с HTTPS base URL и конечными timeout. `refresh(now=...)` получает challenge,
подписывает proof, скачивает ограниченный по размеру envelope и передаёт его кешу.
Redirects отключены; retries автоматом не выполняются. При timeout следующая попытка
начинается с нового challenge. Ошибки авторизации не маскируются кешем.
`cached(now=...)` — отдельное явное чтение офлайн.

`ProvisioningCache(path, verifier).initialize()` вызывается **один раз** для нового
каталога в доверенном локальном хранилище приложения. Verifier получает заранее
доверенный anchor, локальную identity и WG public key. `accept` и `load` возвращают
только `VerifiedProvisioningState`, не применяют VPN. Кеш хранит ciphertext, floors
revision/entitlement и время; права 0700/0600, flock, атомарный replace и fsync.
Повторно принимаются только точные байты уже сохранённой версии. Новый envelope
должен строго повысить revision и не понижать entitlement revision. `load` заново
проверяет подпись, адресата, ключ и lease. Истечение не стирает floors; обнаруженный
откат часов отклоняется, в том числе после проверки истёкшего lease.

Повреждённый/потерянный файл, symlink/hardlink и неверные права приводят к отказу.
Существующий каталог нельзя повторно инициализировать для обхода floors. Файловые
права не защищают от root/владельца, откатывающего целиком backup, и не заменяют
аппаратный monotonic counter. Источник `now` должен быть доверенным UTC временем;
reference API получает его от вызывающего кода. Нативные DPAPI/Keystore и UI пока
не подключены. Отзыв немедленно блокирует серверный fetch, но офлайн-кеш действует
до конца подписанного lease; работающий туннель этот модуль не отключает.
