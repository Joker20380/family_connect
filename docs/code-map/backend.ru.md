# Серверные модули и контракты

[Общая карта](README.ru.md). Пути в таблицах относительно корня репозитория.

## Идентичность и доступ

| Модуль | Ответственность и вход | Состояние/данные | Проверки |
| --- | --- | --- | --- |
| device_identity/device.py | DeviceIdentity, ключи RNS/WG и transport-key proof | Локальное приватное состояние; identity не сбрасывать при ошибке | tests/test_device_identity.py |
| device_identity/friends.py | Явное создание/возобновление POSIX Friends identity | Private files и enrollment marker, flock; это не desktop keyring | tests/test_friends_identity_store.py |
| control/friends/access.py | Access: invite → challenge → activation/config access | SQLite invites/devices/challenges, явный revoke; не готовая система подписок | tests/test_friends_access.py |
| control/friends/referrals.py | Выдача/использование реферальных приглашений | Лимиты и записи на сервере | tests/test_referrals.py |
| control/friends/chat.py, chat_sync.py | Допуск chat identity и синхронизация membership | Связь доступа Friends с закрытым relay | tests/test_friends_chat.py |
| control/friends/notices.py | Сервисные объявления и права публикации | Отдельное хранилище notices/роли | tests/test_device_notices.py |
| deploy/friends/access-api.py | Реальный HTTP handler Friends, ограничение тела/конкуренции | Loopback API за TLS ingress, вызывает сервисные модули | deploy/friends/README.md и профильные tests |

Типовой Friends сценарий: клиент сохраняет identity → получает challenge → подписывает
proof → сервер потребляет challenge и проверяет доступ → клиент проверяет полученную
конфигурацию → платформенный owner применяет профиль. Внешняя HTTP-граница не заменяет
проверку криптографического proof. Адрес устройства из запроса не является правом доступа.

## Product: отдельный серверный контур

В [control/product](../../control/product/) читать `api.py` (HTTP boundary), `store.py`
(ProductStore), `provisioning.py` (ProvisioningService), `gateways.py` и
`gateway_adapter.py` (согласование gateway), `admin.py` (операторские операции).
SQL-миграции лежат в [control/migrations](../../control/migrations/), запуск описан
в [compose.product.yaml](../../compose.product.yaml) и Dockerfile.product.

Не переносить автоматически утверждения об entitlement/ProductStore на Friends Access.
`admin.py` — не Django-панель. Общая Django-админка серверов/доступа/платежей запланирована
в [7.1](../PLAN.md#django-admin); готового платежного провайдера здесь нет.

## Provisioning: получение и применение

| Группа | Файлы | Контракт |
| --- | --- | --- |
| Базовая выдача | models.py, envelope.py, auth.py, client.py, cache.py | Модели, envelope, авторизация, получение и локальный cache |
| Friends-клиент | friends.py, friends_owner.py, friends_store.py | Сеть отдельно от сохранения identity/владения операциями |
| Friends-профили | friends_catalog.py, friends_application.py | Проверка каталога, локальная подстановка ключа, применение |
| Managed wire | configuration.py, ack.py | Подписанная конфигурация и подписанные receipts с отдельными domains |
| Managed lifecycle | transaction.py, application.py | Durable journal, apply/health/rollback, backend boundary |
| Managed carrier | relay.py, reticulum.py, runtime.py, control_route.py | Хранение/доставка, reference runner, независимость служебного маршрута |
| Fleet binding | fleet.py | Строгие operator pins для issuer; не сетевое право клиента менять сервер |

Все эти файлы находятся в [provisioning](../../provisioning/). Тесты распределены по
`tests/test_friends_*`, `test_control_channel.py`, `test_control_vectors.py`,
`test_reticulum_provisioning.py`, `test_control_route.py` и platform suites.
Подробный порядок проверок/журнала — в [managed map](../managed-control-code-map.ru.md).

## Fleet: расширяемый парк серверов

| Файлы в control/ | Ответственность | Что запрещено обходить |
| --- | --- | --- |
| fleet.py | Registry, lifecycle, endpoints, capacity/ranking | Не назначать disabled/draining/unhealthy узлы новым устройствам |
| fleet_store.py | Leases/IPAM, access, очереди/publications | Authoritative DB; IP не свободен до подтверждённой очистки |
| fleet_access.py | Device proof и резервирование | Актуальный grant и одноразовый challenge |
| fleet_scheduler.py | Ограниченные проходы, claims/backoff | Не держать бесконечный цикл/сетевой вызов под видом одной операции |
| fleet_worker.py | Согласование желаемого состояния/receipt | Не объявлять ready по одному факту отправки SSH |
| fleet_gateway.py | Durable fencing на gateway | Старое generation не может воскресить удалённого peer |
| fleet_wg.py | Точечная WG/AWG настройка | Не менять чужие peers; проверять operator pins |
| fleet_ssh.py, fleet_process.py | Закреплённый SSH host key, subprocess bounds | Не превращать запрос клиента в shell-команду |
| fleet_publish.py | Offline подписанная адресная выдача ready lease | Signing key не переносится в online worker/relay |

CLI/agent: `scripts/check_fleet.py`, `scripts/fleet_agent.py`. Проверки:
`tests/test_fleet*.py`, isolated native `pilot/fleet-native` и
`scripts/test_fleet_native.py`. Runbooks: [leases](../fleet-leases.ru.md),
[fencing](../fleet-gateway-fencing.ru.md), [SSH](../fleet-wg-ssh.ru.md),
[access/scheduler](../fleet-access-scheduler.ru.md), [publication](../fleet-publication.ru.md).

Fleet пока локальный backend этапа5: native engine acceptance отдельных сценариев
не означает production deployment, рабочую платежную авторизацию или независимый failover.
Открыты ACK/offline→online, migration действующих выдач, автономный TTL и остальные
пункты STATUS. Не создавать вторую независимо изменяемую копию leases в будущей Django DB.

Friends Access/ChatAccess используют общий `CHALLENGE_TTL=100` в
`control/friends/access.py`: запас20с до клиентской границы120с, DB expiry100с.
[Инцидент и проверка](../releases/2026-09-24-friends-challenge-clock.ru.md).
