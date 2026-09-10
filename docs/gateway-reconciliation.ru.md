# Согласование peers и отзыв на gateway

10.09.2026. Реализован односерверный продуктовый механизм; на рабочий сервер не развёрнут.

## Порядок работы

Migration v3 сохраняет v1/v2 данные и добавляет `peer_deployments`, уникальные адресные
резервации `peer_allocations` и устойчивую очередь `peer_outbox`. При staging сервер
проверяет регистрацию, ключ и entitlement и резервирует адреса. Каждый кандидат получает
задачу установки. Выдача provisioning разрешена только после подтверждения всех задач;
старый `--peers-ready` удалён. Stage не выдаёт envelope и не означает подключения клиента.

```sh
python -m control.product.admin --database state-product/product.db migrate
python -m control.product.admin --database state-product/product.db stage-peers DEVICE_IDENTITY --network network.json --lease-seconds 3600
python -m control.product.admin --database state-product/product.db reconcile-peers --gateways gateways.json
python -m control.product.admin --database state-product/product.db peer-status
python -m control.product.admin --database state-product/product.db publish-provisioning DEVICE_IDENTITY --network network.json --key-directory state-product/signing --lease-seconds 3600
```

Формат `network.json` описан в [provisioning provider](provisioning-provider.ru.md).
`gateways.json` — доверенная операторская привязка ID к локальному контейнеру и его
реальному host-каталогу `/keys`, например:

```json
{"be-1":{"container":"family-connect-pilot-gateway-1","keys":"/opt/family-connect/state-v2/wireguard"}}
```

Это не поле публичного API. Docker adapter сверяет mount, публичный ключ WG gateway,
порт и поддержку сохранения peers. Нужен актуальный образ из `pilot/Dockerfile` с
`family-connect-peer-sync`; старый образ отклоняется до изменения peers. Автоматическая
проверка доступности публичного endpoint и успешного клиентского handshake не заменяется
этим подтверждением установки.

Для пилота adapter принимает IPv4 `10.77.0.4–254/32` и необязательный соответствующий
IPv6 `fd77:92::<номер>/128`. Исходные Android/Linux peers и чужие динамические записи
сохраняются. Пересечение адресов, повторное присвоение ключа, небезопасные файлы и
неверная привязка контейнера приводят к отказу. Топология устройства после staging
не меняется: смена адресов/gateways потребует отдельной миграции. Адреса после отзыва
не освобождаются автоматически. Повторный stage того же network продлевает lease,
сбрасывает подтверждения установки и требует нового reconcile перед publish.

## Отзыв, ошибки и восстановление

`revoke-device` и `revoke-entitlement` меняют разрешение и записывают желаемое удаление
в одной транзакции. Worker также обнаруживает истечение deployment/entitlement и отзыв
transport key. Он сверяет желаемое состояние с реальным при каждом проходе, поэтому
может восстановить потерянный peer либо повторить его удаление. Ошибка сохраняет только
`GATEWAY_UNAVAILABLE`, attempts и retry_at; backoff от 2 до 300 секунд. Статус `absent`
означает проверенное отсутствие после успешного прохода, а `desired=absent` само по себе
ещё не подтверждает удаление. При недоступном gateway отзыв пока не завершён физически.

Сначала атомарно сохраняется/удаляется публичный файл `peers/product-IDENTITY.conf`,
затем синхронизируется WG. Helper внутри контейнера получает ту же файловую блокировку
и **заново читает актуальный файл**. Запоздалая после timeout Docker-команда не применяет
старое действие: если файл уже удалён, peer удаляется. Сбой между сохранением, WG и
подтверждением в БД безопасно повторяется. `/keys` можно монтировать read-only в gateway;
host worker пишет в исходный каталог. После перезапуска startup загружает только
сохранившиеся записи; подтверждённо удалённый peer не восстанавливается.

В пределах одного хоста продуктовый write lock сериализует внешнюю операцию с revoke.
Каждая Docker-команда имеет timeout 3 секунды, файловая блокировка host неблокирующая.
Во время прохода API может получить SQLite 503: клиенту нужен ограниченный backoff.
Это не распределённые worker leases; несколько control hosts не поддерживаются.

Офлайн-кеш клиента может оставаться валидным до конца подписанного lease, но удалённый
WG peer больше не разрешает трафик на gateway. При остановленном worker или недоступном
Docker гарантии мгновенного удаления нет. Остановка worker не останавливает gateway и
не отменяет grants. После восстановления сначала выполнить reconcile, проверить очередь,
затем открывать product API. Старые backups БД/peer-файлов могут вернуть отозванные grants;
не восстанавливать их под работающими сервисами без сверки отзыва.

## Периодический worker

Шаблоны находятся в `deploy/systemd/family-connect-peers.service` и `.timer`: проход
через 15 секунд после старта и после завершения предыдущего, timeout 60 секунд.
Пути `/opt/family-connect` и `.venv` адаптировать к установке. EnvironmentFile
`/etc/family-connect/product.env` содержит `FC_PRODUCT_DB` и `FC_GATEWAYS` — абсолютные
пути к БД и операторскому JSON. Unit по умолчанию запускается от root; выбранный service
UID должен владеть БД/каталогами 0700 и файлами 0600 и иметь доступ к Docker. Публичный
HTTP-процесс не получает Docker socket. В этом этапе unit не установлен и не запущен.

Для остановки/отката остановить timer и product API, сохранить БД v3 и записи peers.
Не понижать схему. Отдельно решить судьбу уже разрешённых peers; отключение timer их
не удаляет. Старые v2 envelopes без управляемого deployment после миграции не выдаются.
Вручную зарегистрированные v2 peers автоматически не присваиваются новой системе:
их перенос требует отдельной операторской сверки и контролируемого обслуживания.

## Проверки

Python-тесты: staging/публикация, все кандидаты, сохранение очереди, гонка установки
и revoke, прерывание после внешней операции, drift, независимый отзыв, expiry,
повтор после ошибок, защита чужих peers и файлов. `python -m scripts.test_product_gateway`
— явный интеграционный тест с Docker/NET_ADMIN: отдельный контейнер без сети, портов и
маршрутов хоста, реальный WG install/remove, сохранение при пересоздании интерфейса,
запоздалая команда и сохранение постороннего peer. По умолчанию использует тестовый образ
`family-connect-wireguard:reconciliation-test`; можно задать `FC_GATEWAY_TEST_IMAGE`.
Рабочий сервер, клиентский интернет-трафик и физические VPN-приложения тест не затрагивает.

CLI reconcile-peers возвращает exit code 1 при неподтверждённых задачах/ошибках, включая ожидание backoff; peer-status показывает подробное состояние.
