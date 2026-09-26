# Мессенджер: очередь доставки — 19.09.2026

Продолжение после одобрения терминального макета. APK остаётся на паузе.
Источник: 3f6f662 с сохранёнными локальными изменениями. Android
0.1.7-beta08/code8, RNS1.5.1, LXMF1.1.1, cryptography46.0.7; версии не повышались.
Нового CI/release/deployment нет. Последний сверенный Client builds34857790251
(f4f320f) успешен, phase034859397457 (3f6f662) успешен; эти результаты не проверяют
текущие незакоммиченные изменения. Последний опубликованный desktop v0.2.9,
TCP v0.1.0 от11.09. Серверы и установленное приложение не менялись.

## Изменения

- Store.pending_outbox выбирает queued и sending предыдущего владельца; сохраняет
  исходные ID/байты и не выбирает relayed/delivered или текущую попытку.
- Mailbox.exchange получает до10 сообщений/48KB и отправляет до4 на одном link
  с общим deadline12с (максимум30). Подписи, commit-before-purge, квоты и протокол
  сохранены. Частичный успех не откатывается при последующей ошибке.
- DeliveryController: один foreground/online worker, объединение событий,
  cooldown4с, до3 автоматических повторов временной ошибки, backoff до300с.
  После пустого успеха нет idle polling. Потеря сети/уход в фон отменяет обмен;
  поздний результат не меняет состояние нового lifecycle generation.
- LocalChat будит worker после сохранения очереди/контакта. Close сначала ждёт
  worker; close_pending сохраняет Store/ключ у владельца и запрещает новые операции.
- Python Android bridge получил delivery_state/request_sync. Allowlist упаковки
  содержит7 клиентских модулей; PUT_PATH перенесён в codec без изменения значения,
  чтобы не импортировать серверный spool в Android.

## Проверки

Python3.14 в /tmp/fc-messenger-venv, согласованные lockfiles.

- Focused delivery/bridge/local/chat:64 passed.
- Новый реальный loopback RNS test:1 passed. Два клиента и закрытый узел с
  синтетическими identity:5 сообщений уходят двумя порциями; получатель пока
  не запрашивает почту; затем сохраняет5 и удаляет их с узла. Повторное обновление
  отправителя не пересылает relayed. Это не приёмка телефона/Doze/интернета.
- Стандартный `python -m pytest -q`:497 passed,2 dependency deprecation warnings.
- Полный `python -m pytest -q messenger/tests`:95 passed за83.63с.
- `git diff --check`: passed.

Проверены ограниченные повторы/backoff, отмена и подавление позднего результата,
ожидание нового события после постоянной ошибки, close timeout с сохранением
владения Store, пробуждение после commit, повтор stale sending с теми же байтами.

## Что остаётся

Подключить реального Android carrier owner, LXMF destination/router и lifecycle
к LocalChat. Использовать общий RNS runtime с control channel, проверить совместную
работу с VPN. Amsterdam pilot разрешает только две диагностические identity;
регистрация реальных пользователей чата ещё нужна. Diagnostic keys не используются
как пользовательские. Непрерывный приём/уведомления/Doze и native chat screens
не реализованы этим этапом. Relayed не означает delivered.

Native Keystore/Chaquopy/process-death и UI требуют runtime acceptance после
снятия паузы APK. Публичный GitHub и увеличение инвайтов до50 остаются после
мессенджера. Группы/звонки/вложения не входят в текущий этап.

## Rollout / rollback

Изменения только локальные исходники и документы. APK, теги, публикации, push,
установка и серверный rollout не выполнялись. После снятия паузы: native carrier
и enrollment, изолированная Android runtime/interaction приёмка, затем platform CI
и отдельный неизменяемый подписанный выпуск по существующему runbook.

Для отката этапа отключить attach_delivery, удалить delivery_state/request_sync
из bridge и убрать mailbox/delivery из allowlist, согласованно вернуть exchange
и перенос PUT_PATH. Сначала успешно закрыть worker, затем Store/router/carrier.
Формат Store1 не менялся; миграция или удаление истории/ключей не нужны.
Не сбрасывать соседние незакоммиченные изменения bridge/UI и документации.
