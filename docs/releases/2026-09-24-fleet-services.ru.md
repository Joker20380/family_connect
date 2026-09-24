# 24.09.2026 —5.2: proof авторизация и durable scheduler

Добавлен локальный путь FleetAccess: подпись устройства, проверка актуального grant
и резервирование в одной транзакции. FleetScheduler выполняет ограниченные проходы,
сохраняет claims и backoff, приоритетно обрабатывает удаления.201 tests passed in5.17s.
[Подробный контракт и миграция](../fleet-access-scheduler.ru.md).

## Изменения

- `control/fleet_access.py`: Reservation и одноразовый proof-gated reserve.
- `control/fleet_scheduler.py`: limit/budget, durable claim, повтор после сбоя.
- `control/fleet_store.py`: схема2, явная транзакционная миграция1→2, challenges/jobs,
  общий транзакционный reserve, ограничение batch expiry и completion token.
- `control/fleet_worker.py`: выделен process одной lease; прежние проверки receipt,
  generation/прав и публичные коды результата сохранены.
- `device_identity/device.py`: добавлен разрешённый audience fleet-reservation/v1;
  прежний enrollment domain по умолчанию сохранён. Остальные незакоммиченные
  изменения этого файла из предыдущих работ не относятся к этому checkpoint.
- `tests/test_fleet_services.py`:18 новых сценариев.

Проверены конкурентный consume proof, потеря ответа и новый proof с прежним request ID,
revoke/revision/expiry после challenge, чужая подпись/ключ/audience, лимит challenges,
rollback при отсутствии capacity, строгая валидация, end-to-end proof→reserve→ready→
revoke→release, claim collision/expiry, restart backoff, приоритет удаления,
старый completion token, revoke во время эффекта, batch/deadline и миграция с lease.
Первый прогон новых тестов выявил ошибку вызова тестового helper (два device аргумента);
исправлен сам тест, затем выполнен полный успешный прогон.

## Воспроизведение

```sh
/tmp/fc-desktop-current-venv/bin/python -m pytest -q \
  tests/test_fleet_services.py tests/test_fleet_adapters.py \
  tests/test_fleet_gateway.py tests/test_fleet_store.py tests/test_fleet.py \
  tests/test_friends_identity_store.py tests/test_friends_store.py \
  tests/test_friends_owner.py tests/test_device_identity.py tests/test_friends_access.py
```

201 passed: прежняя fleet/Friends выборка163 +18 новых service tests +20 дополнительных
identity/Friends-access проверок. Pytest9.1.1, pydantic2.13.5, rns1.5.1,
cryptography46.0.7. [SHA256 и команда](2026-09-24-fleet-services.json).
Native12 сценариев WG/AWG+SSH из [предыдущего шага](2026-09-24-fleet-native.ru.md)
не повторялись: gateway/SSH/CLI код не менялся. Новый proof/scheduler проверен локально
с test gateway adapter; это не новый сквозной native-прогон сервиса.

## Где мы и что не завершено

Этап5.2: локальные авторизация выдачи и scheduler готовы. Следующий результат —
атомарная signed выдача после ready и дальнейшая интеграция с действующим входным
протоколом/источником прав. FleetAccess использует fleet.access; рабочая Friends DB
не подключена и её миграция ещё не выполнена. Внешний API/rate limiting, supervisor,
TTL на gateway без контроллера, TCP backend и migration/import рабочих IP впереди.
Схема2 обновляется только явным upgrade_services при остановленных writers;
автоматического downgrade нет. До production нужны согласованный backup/recovery
и контроль единственного источника прав/allocator.

Изменения только в рабочем дереве. Без commit/push/CI, удалённых действий и production
rollout. Клиенты не пересобирались: Android0.1.18-beta50/code50, Linux0.2.10,
Windows0.2.13; установленные/публичные версии, каталоги и страница прежние.
Production DB не мигрировались, серверный откат не нужен. После будущей миграции
нельзя возвращать старую DB/схему без сверки с gateway journal и живыми peers.
7.1 Django-админка серверов, доступа и платежей остаётся после5/6.
