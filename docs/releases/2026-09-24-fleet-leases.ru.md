# Этап 5.2: постоянные leases и атомарный IPAM — 24.09.2026

Пользователь поручил продолжить этап5 и подробно документировать всю работу.
Результат этого шага — локальный слой хранения выдач поверх ранее подготовленного
реестра/планировщика. Этап5.2 целиком ещё не закрыт, production rollout не выполнялся.

## Проблема и изменение поведения

Ранее планировщик только возвращал список узлов. Два одновременных запроса могли
увидеть одинаковую свободную ёмкость; постоянной записи адреса и результата запроса
не было. Новый FleetStore выбирает gateway, резервирует место и IPv4 `/32`, сохраняет
request mapping и событие в одной write transaction. После потери ответа тот же
request ID возвращает прежнюю выдачу, включая состояние после удаления.

Истечение lease не освобождает IP: сначала retiring, затем подтверждение очистки
правильной generation, затем released. Это предотвращает повторное использование
адреса, пока прежний peer может оставаться на недоступном шлюзе. Устаревшее ready
подтверждение не отменяет retire/revoke. При смене endpoint с неочищенными выдачами
реестр отвергается; тихий переезд существующих leases не выполняется.

## Изменённые компоненты

- `control/fleet_store.py`: SQLite schema1, registry history, public access bindings,
  access revisions, IPAM/limits, request idempotency, lifecycle/generations, durable
  pending work и исходные gateway snapshots.
- `tests/test_fleet_store.py`: конкурентные запросы, реальные отдельные процессы,
  реальные crash до/после commit, файл/permissions, expiry, revoke, replay, pool
  bounds, drain, endpoint migration gate, rollback при ошибке записи.
- `control/fleet_store.py` явно фиксирует предпосылку sole allocator; observations
  и DB counts относятся к одной популяции. Старые неучтённые peers требуют импорта.
- [Подробная документация API, SQL-инвариантов и recovery](../fleet-leases.ru.md),
  обновлены STATUS, PLAN, карта документации и контракт этапа5.

Новая DB находится только в явно инициализированном приватном каталоге. Существующие
Friends/product DB, identities, ключи, peers и gateway services не изменялись.

## Решения и их последствия

| Решение | Причина / предел |
| --- | --- |
| Отдельный store, без автоматической миграции product/Friends | Не объявлять старые адреса свободными и не менять работающий доступ |
| flock + BEGIN IMMEDIATE + synchronous FULL | Один управляющий хост; решение о месте и IP сериализовано между процессами |
| Считать reserved/ready/retiring занятыми | Не освобождать ёмкость при потере ответа или недоступном gateway |
| Запрет тихого изменения binding и endpoint | Не выдавать старый lease другой identity и не терять место очистки |
| Не делать сеть/подпись в SQLite-модуле | Сетевой adapter и issuer требуют отдельных fencing/publication контрактов |
| Public grant sync — доверенный API библиотеки | Proof устройства и действующий Friends revoke пока не интегрированы |
| Порог max(local, observed) при sole allocator | Защита от низкого устаревшего счётчика; не оценка объединения независимых выдач |

Локальная generation защищает состояния DB от старых receipts, но **не останавливает
старую удалённую команду**. Live adapter не может вызывать confirm_removed, пока не
гарантирует удалённый fencing/quiescence. Publishable — point-in-time проверка,
а не атомарная публикация; issuer должен заново проверить access/generation.

## Проверки

Среда: `/tmp/fc-desktop-current-venv/bin/python`, pytest9.1.1,
pydantic2.13.5, rns1.5.1, cryptography46.0.7 — версии совпадают с lockfiles проекта.

Команда:

```sh
python -m pytest -q tests/test_fleet_store.py tests/test_fleet.py \
  tests/test_friends_identity_store.py tests/test_friends_store.py tests/test_friends_owner.py
```

**112 passed**: 37 новых storage tests,49 fleet tests,26 существующих Friends checks.
[Машиночитаемая запись результата и SHA256 четырёх fleet source/test файлов](2026-09-24-fleet-leases.json).
Локальные ссылки обновлённых документов проверены; отсутствующих целей не обнаружено.

Наблюдаемые результаты:

- Десять отдельных процессов одновременно запрашивают три места: ровно3 leases,
  три разных IP `.2/.3/.4`, остальные7 получают `no-capacity`.
- Двадцать четыре одинаковых запроса в8 потоках: ровно один lease ID.
- Процесс принудительно завершён `os._exit(23)` до commit и отдельно после commit:
  повтор оставляет ровно1 lease,1 request mapping и1 reserved event.
- `/29` с ёмкостью5 выдаёт только `.2–.6`; адрес сети, `.1` шлюза и broadcast исключены.
- Retiring занимает место до корректного removal receipt; адрес затем может получить
  другой lease. Повтор старого receipt не меняет нового владельца.
- Ошибка записи во время резервирования и во время revoke откатывает всю транзакцию.
- Draining сохраняет ready; disabled/provisioning создают retiring intents;
  смена endpoint запрещена до окончательной очистки.
- Restart, clock rollback, missing/corrupt DB, небезопасные permissions/symlink/hardlink,
  stale telemetry и ограничения доступа проверены локально.

Рабочие серверы, native Android/Windows/Linux VPN и новая подписанная выдача в этом
шаге не тестировались. Их готовность не выводится из unit/concurrency tests.

## Осталось до завершения 5.2

1. Сверить/импортировать прежние leases и определить единственного allocator;
   интегрировать source-of-truth авторизацию/revoke с Friends.
2. Реализовать bounded gateway adapter и durable remote generation fence, включая
   задержанный apply после удаления и crash/restart worker.
3. Очередь provision → ready → signed publication с повторной проверкой доступа,
   без помещения offline signing key на relay.
4. Доставка через независимый ingress, затем AWG3.1/dynamic clients и общие live gates.

## Версии, rollout и rollback

Android0.1.18-beta50/code50, Linux0.2.10 preview, Windows0.2.13 остаются текущими;
новых сборок, публикаций, перезапусков или серверных миграций не было. Исходники
локальны, Git commit/push этой работой не выполнялись; прежние незакоммиченные
изменения сохранены. Rollback рабочего сервиса не нужен, так как новый store не
подключён. При будущем rollout останавливать новые выдачи и сохранять leases/history;
не удалять DB и не возвращать старую копию как способ освободить адреса.
