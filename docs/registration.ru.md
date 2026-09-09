# Регистрация устройств: односерверный продуктовый контур

Дата: 09.09.2026. Реализовано в исходном коде и проверено локально; на публичном gateway не развёрнуто. Приложения Linux/Android/Windows пока используют прежнюю активацию. [ADR identity/provisioning](adr/001-identity-provisioning.ru.md).

## Что работает

Отдельный сервис разрешает новой независимой Reticulum identity присоединиться через семейное приглашение. Оператор локально создаёт entitlement семьи. Устройство генерирует собственные identity и WireGuard key, получает challenge с помощью приглашения, подписывает привязку ключа и завершает регистрацию. База сохраняет только публичные ключи. API не принимает конфигурационные файлы или приватные ключи клиента.

Приглашение — секретное разрешение на регистрацию, а не VPN credential и не общая identity. Случайные invitation token и challenge имеют по 256 бит; в БД хранятся только SHA-256 хеши. Challenge действует максимум 120 секунд, но не дольше приглашения/entitlement. Он привязан к одному приглашению и обоим публичным ключам. При завершении одной транзакцией выполняются повторная проверка разрешения, создание устройства, запись ключа, расходование приглашения, погашение challenge и запись технического аудита.

Параллельные запросы не могут дважды потратить challenge/использование приглашения или превысить лимит устройств семьи. Существующая identity не переносится незаметно в другую семью, не регистрируется повторно после отзыва и не делит WG public key с другим устройством. Неверная подпись или ошибка транзакции не оставляют частично зарегистрированное устройство. Отзыв одного устройства сохраняет разрешения других членов семьи. Отзыв entitlement блокирует разрешение всей семьи и увеличивает его revision.

**На этом этапе отзыв меняет только продуктовую БД. Он ещё не удаляет WireGuard peers и не останавливает существующие VPN-туннели.** Согласование gateway и выпуск provisioning — следующие этапы. Также ещё нет входа в аккаунт, billing/subscription webhooks, самостоятельного управления семьёй владельцем и аутентифицированного восстановления после потери успешного ответа регистрации. Повтор proof возвращает 403; сетевой timeout не доказывает, что регистрация не состоялась.

## Хранилище и миграция

`control/migrations/001_product.sql` создаёт families, entitlements, invitations, challenges, devices, членство device-entitlement, независимые публичные transport keys и ограниченные типы audit events. Аккаунтов с паролями и платёжных записей пока нет. Семья, созданная оператором для пилота, не считается доказательством оплаченной подписки.

Для этого односерверного этапа используется **отдельная локальная SQLite-база**. Нельзя использовать базу другого приложения или подписанный лабораторный каталог. Транзакции используют `BEGIN IMMEDIATE`, foreign keys и unique constraints. Одновременно работает один writer; ожидание блокировки ограничено пятью секундами. До нескольких control replicas нужны миграции PostgreSQL, соответствующие блокировки строк и повторные concurrency tests. Этот SQLite SQL нельзя применять к PostgreSQL. [Транзакции SQLite](https://www.sqlite.org/lang_transaction.html).

Каталог должен принадлежать пользователю сервиса и иметь права 0700; БД — обычный принадлежащий ему файл 0600, без symlink/hardlink. Использовать локальный диск и доверенные родительские каталоги. Защита обеспечивается файловыми правами, а не шифрованием БД. Миграция запускается явно при установке; HTTP-сервис не создаёт разрешения и схему автоматически. Версия миграции хранится в `PRAGMA user_version`. Повтор v1 безопасен, более новая версия отклоняется мигратором.

Резервировать эту отдельную БД через SQLite online backup либо остановить продуктовый процесс и согласованно скопировать БД с журналом. Права резервных копий должны быть такими же строгими. Не восстанавливать при активной записи. Старый backup может восстановить отменённые приглашения/разрешения: перед открытием регистрации инвалидировать outstanding invitations и проверить авторизацию. Файлы старого v1 не мигрируются. Откат этапа — остановить новый сервис, сохранив БД; не понижать схему и не стирать identity зарегистрированных устройств.

## Инструкция локального оператора

Запускать из репозитория в отдельном Python virtual environment. Команды создают только продуктовые данные, не включают VPN и не изменяют peers.

```sh
pip install -r control/requirements.lock -r device_identity/requirements.lock
mkdir -m 700 state-product
python -m control.product.admin --database state-product/product.db migrate
python -m control.product.admin --database state-product/product.db create-entitlement --days 7 --devices 5
```

Последняя команда выводит публичные идентификаторы family/entitlement. Использовать полученный entitlement ID:

```sh
python -m control.product.admin --database state-product/product.db create-invitation --entitlement ENTITLEMENT_ID --hours 24 --uses 1 --output state-product/invitation.json
```

Новый файл 0600 содержит секрет приглашения; он не выводится в терминал. Передавать его только через предполагаемый приватный invitation flow. Не вставлять содержимое в логи, задачи, аргументы командной строки или Git. Файл назначения не должен существовать. Если запись файла после выпуска приглашения завершилась ошибкой, считать его не переданным пользователю и отозвать при операторской проверке перед повтором.

Локальный listener для разработки:

```sh
FC_PRODUCT_DB="$PWD/state-product/product.db" python -m uvicorn control.product.api:app_from_env --factory --host 127.0.0.1 --port 18081 --no-access-log
```

Не публиковать этот HTTP listener напрямую. Для публичной интеграции нужны TLS termination, request/header/body timeouts, лимиты частоты и одновременных соединений, отключение либо редактирование body logs на proxy/APM. Token передаётся в JSON POST body, не в URL. Публичных admin routes и CORS-разрешений нет. Приложение ограничивает body до 8192 байт, отклоняет дубли полей, возвращает фиксированные ошибки и `Cache-Control: no-store`. На приглашение допускается 16 активных challenge; это не заменяет глобальные ingress limits.

Обслуживание и отзыв доверенным оператором:

```sh
python -m control.product.admin --database state-product/product.db prune-challenges
python -m control.product.admin --database state-product/product.db revoke-invitation INVITATION_ID
python -m control.product.admin --database state-product/product.db revoke-device DEVICE_IDENTITY
python -m control.product.admin --database state-product/product.db revoke-entitlement ENTITLEMENT_ID
```

До развёртывания запланировать очистку challenge. Удаление истёкших строк не разрешает replay. Аудит содержит только фиксированный тип события, subject reference и серверное время; без IP, token, proof, исключений и трафика. Ссылки позволяют связывать продуктовые записи — это не анонимная аналитика беты. Перед реальными пользователями определить retention аудита/backup; автоматическое удаление аудита пока не реализовано.

## Контракт API

`POST /v2/registration/challenge`, `Content-Type: application/json`:

```json
{
  "invitation_token": "<64 lowercase hex characters>",
  "public_identity": "<canonical base64 of 64-byte RNS public identity>",
  "wireguard_public_key": "<canonical base64 of 32-byte WG public key>"
}
```

Успех: `challenge` в base64, `expires_at` в Unix seconds, `audience` = `family-connect/enrollment/v1`. Локально вызвать `DeviceIdentity.prove_transport_key(challenge)` и передать полученный подписанный proof целиком в `POST /v2/registration/complete`.

Успех: `device_identity`, `entitlement_id`, `entitlement_revision`, `status: enrolled`. Ответ не является bearer access token и сам по себе не разрешает следующие запросы provisioning. Для fetch потребуется отдельное доказательство владения identity.

Ошибки: 400 `INVALID_REQUEST` для некорректного body; 403 `REGISTRATION_REJECTED` для неверных/истёкших/использованных разрешений или proof; 503 `REGISTRATION_UNAVAILABLE` при ошибке SQLite. Ответ не раскрывает, какое приглашение/устройство существует. Не повторять 403 бесконечно; для 503/timeout нужны ограниченный backoff и последующее аутентифицированное recovery.

## Проверки и совместимость

Новые тесты покрывают persistence после restart, повторную миграцию, чужую identity/key/signature, истечение/отзыв разрешений, гонки replay и лимитов приглашения/семьи, отсутствие частичных записей, независимый revoke, запрет переноса семьи/повторного ключа, отсутствие секретов в БД, pruning, HTTP-flow, безопасные ошибки и некорректные body.

Сборка старого Docker control теперь запускает тесты в отдельной стадии с необходимыми модулями/зависимостями, сохраняя прежний runtime и операторские scripts. На v1 новый API не монтируется, рабочие Compose services не меняются. Движки клиентов сохранены. Фактические результаты тестов и оставшиеся этапы указаны в журнале реализации.
