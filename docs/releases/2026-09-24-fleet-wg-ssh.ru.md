# 24.09.2026 — этап5.2: WG/AWG backend и SSH adapter

Глобально: этап4 принят; в этапе5 завершён5.1, продолжается5.2. Следом5.3–5.6,
затем полный gateway failover6 и согласованная Django-админка7.1. Новый checkpoint
добавляет код реального CLI backend и ограниченного SSH-вызова;5.2 ещё не закрыт.

## Изменения

- `control/fleet_wg.py`: pin интерфейса, точечное добавление/удаление peer,
  отказ при конфликте IP/ключа и проверка результата без чтения private keys.
- `control/fleet_gateway.py`: preflight первого присвоения до durable intent;
  восстановление существующего intent сохраняет прежнюю идемпотентность.
- `control/fleet_process.py`: ограниченный subprocess I/O, timeout, наследование lock.
- `control/fleet_ssh.py`: strict host pin, фиксированная команда, JSON через stdin,
  точное сопоставление receipt, отказ от неоднозначных JSON и bool generation.
- `scripts/fleet_agent.py`: root-only forced-command entry, фиксированный защищённый
  конфиг, отдельные локальные initialize/recover. Автоматической установки ещё нет.

Подробные контракты, последовательность установки и ограничения:
[WG/SSH runbook](../fleet-wg-ssh.ru.md). План7.1 остаётся прежним: Django вызывает
общие фоновые операции, настройка сервера не выполняется внутри HTTP-запроса.

## Проверки

Локальная среда `/tmp/fc-desktop-current-venv/bin/python`; pytest9.1.1,
pydantic2.13.5, rns1.5.1, cryptography46.0.7. Итог: **163 passed in4.45s**.

```sh
/tmp/fc-desktop-current-venv/bin/python -m pytest -q \
  tests/test_fleet_adapters.py tests/test_fleet_gateway.py \
  tests/test_fleet_store.py tests/test_fleet.py \
  tests/test_friends_identity_store.py tests/test_friends_store.py \
  tests/test_friends_owner.py
```

Новые24 проверки включают конфликт маршрута/ключа, неправильный серверный pin,
ложный успешный exit-code, recovery при изменённой привязке, ограничения stdin/stdout,
timeout, подавление stderr, unsafe key files, SSH options, неверный/повторный JSON
и receipt. Fixture запускается реальным дочерним процессом и проверяет наследование
`.effects.lock`; WG/AWG CLI, kernel/userspace engine и настоящий SSH не запускались.
Предыдущие139 проверок журналов/выдач/планировщика и Friends тоже прошли.
Первый тестовый запуск выявил недостающий импорт зависимостей pytest fixture;
импорты исправлены перед итоговым полным прогоном.

## Выпуск и границы

Изменения только в рабочем дереве; без commit/push, CI и production rollout.
Android0.1.18-beta50/code50, Linux0.2.10, Windows0.2.13 не пересобирались;
установленные и публичные версии, каталоги и страница приглашения не менялись.
Рабочие RU/NL серверы в этом шаге не изменялись. Новые VPS не приобретались.

Не приняты: native WG/AWG и SSH smoke, root wrapper/службы, миграция старых IP,
единая авторизация/signed publish, автономный TTL при потере контроллера, TCP backend.
Ближайший шаг — изолированная native-приёмка WG/AWG+SSH перед server integration.
Откат текущего checkpoint — исключить новый неустановленный код; после будущего
включения нельзя удалять gateway journal или освобождать IP без подтверждения удаления.
[Хеши исходников и итог тестов](2026-09-24-fleet-wg-ssh.json).
