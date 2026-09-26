# 24.09.2026 — native WG/AWG + SSH приёмка5.2

Изолированная native-проверка завершена:12 сценариев на WireGuard, AWG2.0 и AWG3.1
прошли с реальным VPN-трафиком и OpenSSH. Регрессионный прогон163 passed in7.05s.
Этап5.2 остаётся открыт; ближайшая работа — общая авторизация и ограниченный
scheduler, затем signed publish. Полный отказ gateway остаётся этапом6,
единая Django-админка серверов/доступа/платежей —7.1.

## Что добавлено

- `pilot/fleet-native/Dockerfile`: отдельный тестовый образ с CLI/engine,
  OpenSSH и текущими control/provisioning/agent исходниками.
- `pilot/fleet-native/accept.py`: реальная настройка интерфейса, restricted SSH key,
  принудительное падение агента после эффекта, проверки journal/retry/recovery.
- `scripts/test_fleet_native.py`: жизненный цикл двух изолированных контейнеров
  для каждого транспорта, проверка handshake/ICMP, очистка, JSON evidence.
- [Инструкция стенда](../../pilot/fleet-native/README.ru.md): запуск, изоляция,
  секреты, точные сценарии и границы. Production-код в этом шаге не менялся.

## Результаты

Финальный native-прогон24.09.2026,10:39:25–10:40:18 UTC:

| Сценарий | WG | AWG2.0 | AWG3.1 |
| --- | --- | --- | --- |
| Admit + падение после эффекта + повтор SSH | passed | passed | passed |
| Потеря интерфейса + восстановление журнала | passed | passed | passed |
| Удаление, повтор, отказ запоздавшему present | passed | passed | passed |
| Новая lease с тем же IP/ключом, старое удаление | passed | passed | passed |

При admit неверный server host key, неавторизованный client key, посторонняя
команда и попытка удалённого initialize отклонены. Для аварии применяется только
тестовый wrapper: настоящий backend меняет peer, процесс завершается с73 до
фиксации done/отправки receipt. На gateway остаются peer и done=0; повтор через
обычный агент по SSH возвращает receipt и фиксирует done=1.

Во всех сценариях соседний unmanaged peer сохраняется. В положительных случаях
проверены свежий handshake и два ICMP-пакета; после удаления трафик не проходит.
Контейнеры/сети всех трёх прогонов удалены; тестовый Docker-образ сохранён локально.

Первый exploratory-прогон показал отсутствие трафика сразу после потери серверного
интерфейса при старой клиентской сессии. Для изоляции проверки серверного recovery
стенд явно пересоздаёт клиентский peer после restart/reuse и получает новый handshake.
Это не доказательство автоматического восстановления клиента; его тайминги остаются
в приёмке этапа6. Изменения рабочего клиента не делались.

## Среда и воспроизведение

Kernel7.0.0-31-generic; wireguard-tools1.0.20210914;
OpenSSH10.0p2 Debian-7+deb13u4 / OpenSSL3.5.7.
AWG2 CLI1.0.20260618-2; AWG3.1 CLI3.1.20260812.
Оба engine выводят одинаковую строку0.0.20250522: она недостаточна для различения
сборок, поэтому точный итоговый image digest сохранён в
[машинном отчёте](2026-09-24-fleet-native.json), вместе с SHA256 исходников.

```sh
docker build -f pilot/fleet-native/Dockerfile -t family-connect-fleet-native:accept .
python3 scripts/test_fleet_native.py --report /tmp/fc-fleet-native-report.json
/tmp/fc-desktop-current-venv/bin/python -m pytest -q \
  tests/test_fleet_adapters.py tests/test_fleet_gateway.py \
  tests/test_fleet_store.py tests/test_fleet.py \
  tests/test_friends_identity_store.py tests/test_friends_store.py \
  tests/test_friends_owner.py
```

Pytest9.1.1, pydantic2.13.5, rns1.5.1, cryptography46.0.7.
Native-прогон требует Docker/TUN/NET_ADMIN; разрешение sandbox запрошено и получено.
Использован существующий локальный Docker, новые серверы не заказывались.

## Ограничения, rollout и откат

SSH реально выполняется по loopback внутри gateway container; VPN — между двумя
контейнерами в private Docker network. Отдельный контроллер/удалённая сеть,
HTTP/DNS/Internet-egress, MTU, production firewall и нагрузка не проверялись.
Установочный root wrapper/systemd/recovery service не подготовлен; в стенде
использован ограниченный root key. Root test image не предназначен для production.

Авторизация доступа, bounded scheduler/signed publish, автономный TTL при потере
контроллера, TCP backend и миграция действующих адресов остаются открытыми.
Native-приёмка не включает production rollout и не закрывает целиком5.2.

Рабочие RU/NL не изменялись. Android0.1.18-beta50/code50, Linux0.2.10,
Windows0.2.13, установленные/публичные артефакты, подписанные каталоги и страница
приглашения остались прежними. Commit/push/CI не выполнялись.
Откат серверов не требуется. Новые файлы — opt-in тестовый стенд; при будущей
установке сохранять центральные leases и gateway journal, не освобождать IP
без подтверждённого удаления. Исторический [предыдущий checkpoint](2026-09-24-fleet-wg-ssh.ru.md)
остаётся записью проверок до этой native-приёмки.
