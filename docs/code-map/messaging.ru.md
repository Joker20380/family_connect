# Мессенджер, объявления и диагностика

[Общая карта](README.ru.md).

## Ядро мессенджера

Корень: [messenger](../../messenger/). Чтение начать с `chat.py` и `server.py`, затем
выбрать слой ниже. Старые этапы в README этого каталога не являются текущим статусом UI.

| Файлы | Назначение | Граница |
| --- | --- | --- |
| chat.py, codec.py | Состояние чата и wire-представление | Лимиты/типы/подписи; не произвольные команды из сообщения |
| store.py, local.py | Локальные данные и операции | Сохранение/identity, не «транспорт доставил — значит записано» |
| delivery.py, sync.py | Доставка, повторы и синхронизация | Отдельные прикладные подтверждения/идемпотентность |
| mailbox.py | Почтовый ящик служебного обмена сообщениями | Отличать от managed configuration journal |
| relay.py, server.py | Закрытый relay и daemon entry point | Operator config/volume/identity, ограничения ресурсов |
| membership.py, admission.py | Участники и допуск | Закрытый relay не означает открытый доступ любому peer |
| service_events.py | Сервисные события | Не содержимое пользовательского трафика в диагностике |

Friends допуск расположен отдельно: `control/friends/chat.py`, `chat_sync.py` и
`deploy/friends/chat-sync.py`. Его изменение требует проверки membership/revoke,
а не только UI отправки. Runbooks: [Reticulum messenger](../reticulum-messenger.ru.md),
[ядро](../../messenger/README.ru.md), [приёмка уведомлений](../testing/messenger-notices.ru.md).

## Android integration

`ChatActivity` отвечает за экран, `ChatThreadView`/`ChatVoiceView`/`ChatAudio` — представление
и голос, `ChatDeliveryService`/`ChatRestartReceiver` — фон и restart,
`ChatNotifications` — уведомления. `ChatKeyVault`, `ChatStoreCipher`, `ChatLocalAndroid`,
`ChatNetworkAndroid`, `ChatRuntime` связывают ключи/локальное состояние с Python.
Bridge-файлы: `fc_chat_store.py`, `fc_chat_transport.py`, `fc_rns_transport.py` в
`clients/android/app/src/main/python/`. Не переносить тяжёлую сеть в UI thread.

Тесты: `messenger/tests`, Android `Chat*Test`, instrumented UI/voice/notification tests.
Пилот подтверждал текст/правки/голос и уведомления с выключенным экраном. Долгий Doze,
OEM/restart и точные задержки требуют отдельных проверок; desktop parity не подтверждён.

## Сервисные объявления и измерения

- `control/friends/notices.py`, `scripts/service_notices.py`, `publish_service_notice.py`:
  операторские/авторизованные объявления. Публикация является внешним действием,
  запускать только в рамках конкретного задания.
- `deploy/server-load/monitor.py`, `publish.py`, `install.py`: сбор/публикация метрик
  нагрузки. Это не доказательство числа уникальных людей: устройства, peers и люди
  различаются. Проверки — `tests/test_server_load_monitor.py` и клиентские load tests.
- `telemetry/events.py`: контракт ограниченных кодов ошибок, не готовый централизованный
  сборщик событий. Не приписывать ему существующую аналитическую платформу.

Сообщения/вложения, invitation tokens, личные конфигурации и private keys не включать
в отчёты об ошибках. Для диагностики различать отказ авторизации, потерю carrier,
задержку записи и отсутствие ACK; один status «не работает» скрывает разные слои.

Внешняя зависимость membership — синхронное время RU/NL.
`deploy/time/family-connect.sources` содержит дополнительный NTS-источник;
[приёмка новых серверов и диагностика](../server-time-and-chat-sync.ru.md).
Приёмник сохраняет fail-closed TTL, runtime код не изменён.

Восстановление mailbox identity/spool проверяет `scripts/vault_restore_probe.py`:
реальные preflight/start/stop в network-none контейнере, без публичного announce.
[Runbook](../vault-restore-rehearsal.ru.md); client-to-client recovery ещё не принят.
