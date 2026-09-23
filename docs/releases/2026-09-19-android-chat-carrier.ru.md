# Android chat carrier и общая стадия — 19.09.2026

Продукт находится на стадии интеграции перед закрытым пилотом. Пользователь
одобрил терминальный интерфейс и следующий этап мессенджера. Действующий порядок:
мессенджер → публичное оформление GitHub → оставшиеся VPN release gates →
подписанный выпуск и50 инвайтов. Подготовлено10, дополнительные40 не создавались.

## Что сделано

- fc_chat_transport.CarrierMailbox: единый RNS runtime и общий session lock с
  control channel; на каждый exchange создаётся привязанный Java к underlying
  network socket. Literal IP, port и node public key проверяются до соединения.
- Connected-socket RNS interface не инициирует собственный reconnect. Общий
  deadline включает connect (до5с), path/link discovery и обмен. Cancellation
  во время connect наблюдается после его возврата/таймаута. После exchange
  закрываются link, socket и interface; reader получает shutdown и join до1с.
- Mailbox-only IN destination использует identity из encrypted Store; direct
  inbound links отключены, router job loop и автоматические announce не создаются.
  Существующий закрытый mailbox wire/encryption не менялись. Это не новый
  ratchet-based protocol и не заявление о forward secrecy.
- LocalChat.attach_carrier создаёт worker с platform mailbox. Session удерживает
  carrier до закрытия LocalChat; close_pending сохраняет владение прежнего этапа.
- ChatLocalAndroid.configureDelivery/deliveryUpdate доступны внутреннему owner
  вне main thread. ChatNetworkAndroid предоставляет bindSocket callback.
  Ни host, ни trust anchor, ни lifecycle не принимаются через UI JSON invoke.
- Busy при занятом control session считается временным отказом и имеет те же
  ограниченные повторы, что link failure. Control implementation не менялась.
- Isolated harness включает новый callback и дополнительный instrumentation
  сценарий configure/offline/close/reopen, пока без запуска.

## Проверки

Python3.14, RNS1.5.1, LXMF1.1.1, cryptography46.0.7, существующие lockfiles.
Focused carrier/bridge/delivery:32 passed до расширения двух allowlist cases
и busy parameter. Полный `python -m pytest -q messenger/tests`:104 passed за81.13с.
`git diff --check` и ссылки нового checkpoint: passed.
Стандартный `python -m pytest -q`:497 passed,2 dependency deprecation warnings.

Реальный loopback: Android Python Session → закрытый RNS node → второй клиент;
сообщение и ответ сохранены, приём очищает spool, повторный exchange открывает
новый socket, каждый socket проходит callback, интерфейсы возвращаются к baseline.
Отдельно проверены занятый control lock, отказ binding, неверный bootstrap,
доступность локальной истории после отказа и удаление destination при close/reopen.
Всё на синтетических identity, никаких production credentials/узлов.

ChatNetworkAndroid скомпилирован javac17 против Android35; предупреждение о
устаревшем getAllNetworks. Это проверка отдельного callback, не компиляция всего APK
и не Android network/JNI runtime acceptance. Новый instrumentation тест не запущен.

## Что ещё не готово

Activity lifecycle callbacks и native экраны чатов пока не подключены. Нужно
получение доверенного mailbox bootstrap и регистрация реальных chat identities;
Amsterdam pilot пока допускает только две диагностические identity. Конфигурацию
для реальных пользователей не добавляли. QR/контакты, UI переписки, сон/Doze,
уведомления и приёмка двух телефонов с VPN остаются отдельными этапами.

## Версии, выпуск и возврат

Исходник3f6f662 с локальными изменениями; Android0.1.7-beta08/code8 без повышения.
Последняя ранее сверенная CI запись: Client builds34857790251/f4f320f success,
phase034859397457/3f6f662 success. Она не относится к новым dirty changes.
Последние зафиксированные опубликованные версии: desktopv0.2.9 и tcp-v0.1.0
от11.09.2026. Установленное приложение/серверы здесь не проверялись и не менялись.

APK по просьбе пользователя не собирался; push, signing, release и deployment
не выполнялись. Продолжение: UI/enrollment, затем после снятия паузы native runtime,
два телефона, platform CI, проверка artifacts и неизменяемый подписанный выпуск.

Rollback только исходников этого этапа: убрать вызовы configureDelivery/update
и carrier binding, успешно закрыв owner; вернуть bridge к local-only режиму,
убрать ChatNetworkAndroid из harness и busy retry при необходимости. Не удалять
Store/identity/Keystore и не сбрасывать соседние dirty изменения. Формат Store1,
серверные endpoints, VPN protocols и release pipeline не менялись.
