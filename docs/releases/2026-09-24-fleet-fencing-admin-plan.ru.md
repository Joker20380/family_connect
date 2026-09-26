# Этап5.2: fencing-прототип; согласование Django-админки7.1

24.09.2026 пользователь одобрил единую Django-админку для новых серверов и платежей
и поручил закрепить её в плане, продолжая текущий этап. Добавлен **7.1 «Единая
Django-админка: серверы, доступ и платежи»**, с зависимостью от общих операций5.2.
Сам Django UI не реализован; порядок5 →6 →7 сохранён, контракты7.1 определены сейчас.

## Реализация следующего шага

Добавлены `control/fleet_gateway.py`, `control/fleet_worker.py` и проверки
`tests/test_fleet_gateway.py`. Шлюзовой журнал фиксирует intent/generation до эффекта,
сохраняет tombstones после удаления, резервирует IP и WG key, возвращает точные
receipts и восстанавливает незавершённые операции. WG/AWG команда не становится
готовой в центральном store без успешного receipt и повторной проверки доступа.

Повтор старого удаления не исполняется заново и не затрагивает переиспользованный
IP/key. Отложенный present после absent блокируется локально на gateway.
Унаследованный FD `.effects.lock` не даёт новому удалению обогнать ещё работающий
дочерний эффект после смерти родителя. Удаления в recovery приоритетнее установок.

Worker выполняет конечный проход и сохраняет pending при ошибках/потере ответов.
Сетевой adapter и настоящий WG/AWG backend отсутствуют; TCP не поддержан этим
командным прототипом. Настоящий backend обязан соблюдать FD/quiescence contract
и проверять фактическое состояние; чистый callback сам по себе его не доказывает.

[Подробный контракт, сценарии сбоев и ограничения](../fleet-gateway-fencing.ru.md).

## Проверки

Команда:

```sh
python -m pytest -q tests/test_fleet_gateway.py tests/test_fleet_store.py \
  tests/test_fleet.py tests/test_friends_identity_store.py \
  tests/test_friends_store.py tests/test_friends_owner.py
```

Результат: **139 passed** —27 gateway/worker,37 storage,49 registry и26 Friends tests.
[Запись команды/результата и SHA256 новых исходников](2026-09-24-fleet-fencing.json).
В том числе проверены:

- restart gateway journal и отказ запоздалой установки;
- absent-before-present без удаления постороннего peer;
- повтор старого удаления после повторной выдачи IP/key;
- pending removal удерживает ownership; конфликт IP или key не меняет peer;
- реальная смерть родителя с остающимся дочерним эффектом и ожидание удаления;
- runtime recovery, expiry, clock rollback, потеря DB и неправильный gateway pin;
- полный локальный reserve → ready → retire → released цикл;
- потеря ответов после успешных эффектов, гонка retire с apply, неправильные receipts;
- отказ malformed bool-generation и неподдержанного транспорта до эффекта.

Первый прогон выявил нормализацию malformed bool-generation при typed JSON
serialization; execute теперь перепроверяет реальные field types до сериализации.
Регрессионный тест сохранён. Последний прогон выполнен после исправления.

Новых native/client/live проверок нет. Реальный дочерний fixture доказывает механизм
наследования FD, но не заменяет будущую приёмку системного peer backend.

## План и оставшиеся работы

7.1 закрепляет карточки серверов, onboarding/checks/active/draining/disabled,
устройства/доступ, тарифы/платёжные события, очередь/аудит и роли. Подготовка узла
выполняется фоновым обработчиком. Webhook платежа меняет entitlement идемпотентно;
он не выполняет SSH. Перед будущим Django/PostgreSQL rollout нужна явная миграция
authoritative store, а не вторая изменяемая копия leases/access.

Текущий следующий шаг5.2: bounded peer backend и аутентифицированный adapter,
gateway TTL/restart policy, scheduler/backoff/fairness и интеграция Friends revoke.
Затем transactional signed publication и независимый ingress acceptance.
Этап5.2 остаётся открытым. Обновлены PLAN, STATUS, ROADMAP, карта документации.

## Версии и откат

Android0.1.18-beta50/code50, Linux0.2.10 preview, Windows0.2.13 не менялись.
Новых сборок, публикации, Git commit/push или server rollout не было.
Прежние незакоммиченные изменения сохранены. Production rollback не требуется.
Будущий rollout нельзя откатывать удалением gateway journal/tombstones или старой
копией DB: это разрешило бы старые команды. При проблемах останавливаются новые
операции, журнал сохраняется, узел исключается из новых назначений до recovery.
