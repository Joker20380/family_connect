# Привязка чата к приглашению — 19.09.2026

## Итог этапа

Подготовлен регистрационный путь в исходниках сервера и Android. Это регистрация
заявки, не применённое разрешение рабочего mailbox. Никаких новых инвайтов, APK,
серверных изменений, CI, push, signing или release в этом шаге не выполнялось.

ChatAccess принимает только ранее активированное устройство. Challenge на120с
связан с device и точным chat public key, ограничен8 незавершёнными запросами.
При регистрации нужны существующий device transport-key proof и отдельная подпись
chat identity. Последняя подписывает domain + device16 + chat_public64 + nonce32;
чужой key, challenge другого назначения/устройства, replay и expiry отвергаются.

На устройство допускается одна неизменяемая chat identity; один chat public key
нельзя присвоить двум устройствам. Повтор с новой challenge и тем же ключом допустим
при потерянном ответе. Проверяются и device revocation, и invite revocation, включая
отзыв между выдачей challenge и commit. Список желаемых участников исключает
отозванные записи, но сам по себе ещё не отзывает доступ на удалённом узле.

## Файлы и пользовательский путь

- messenger/admission.py: ограниченный domain-separated payload.
- LocalChat/Session/ChatLocalAndroid: нативный метод enrollment proof; private key
  не возвращается, универсального signing endpoint и JSON invoke операции нет.
- control/friends/chat.py: additive registry/challenges, атомарное одноразовое
  потребление, операторский desired_members без публичной выдачи списка.
- access-api.py: /friends/chat/challenge и /friends/chat/register через существующий
  bounded HTTPS request handler. register возвращает status=pending-node, не active.
- FriendsAccessAndroid использует сохранённую invited identity без повторного
  расходования кода, проверяет device/chat/expiry/audience ответов и два proof.
- ChatActivity получила «Зарегистрировать доступ к чату». Ошибки доступа/сети имеют
  отдельные подписи; успех сообщает об ожидании узла, локальная очередь сохраняется.
- Android source allowlist теперь8 модулей; admission не импортирует server code.

## Проверки

11 friends access/chat tests passed: два ключа, replay, idempotent retry, отозванные
device/invite, expiry/cap, подмена ключа, неподтверждённое устройство, параллельное
присвоение одного ключа разным устройствам. Полный общий suite:505 passed/2 warnings.

Позднее дополнены bridge проверки: proof из сохранённой identity, domain/device
binding и отсутствие enrollment_proof в JSON invoke; focused bridge/friends:
25 passed. Полный messenger suite до добавления этих двух tests:104 passed за90.73с.
Новые два сценария входят в последующие25 focused passed. Серверные tests также
проверены с запрещённым импортом LXMF:11 passed; test image получил только
messenger/__init__.py/admission.py, без новой зависимости или смены CI semantics.

Java ChatActivity/FriendsAccessAndroid и автоматически найденные source dependencies
скомпилированы javac17 против Android35, Chaquopy16.1.0, Gson2.13.2 и cached
BouncyCastle1.78.1 (app pin1.85.2). Временный R из strings.xml, без AAPT/Gradle/APK.
Предупреждения deprecated Android APIs. Это не JNI/Keystore/network/device приёмка.

## Следующий шаг до инвайтов

1. Согласованно установить registry/API/ingress migration, связать desired_members
   с работающим закрытым узлом и проверяемым bootstrap/подтверждением применения.
   После этого настроить carrier и lifecycle UI. Пока endpoint на production не
   объявляется доступным. Диагностические identity не использовать для друзей.
2. После снятия APK-паузы — собрать и проверить двух реальных участников:
   регистрация, сообщение/ответ, offline/restart/network change и совместная работа
   с VPN. Закрыть оставшиеся release gates; не выдавать непроверенный бинарник.
3. Обязательное продуктовое оформление GitHub по сохранённому заданию, неизменяемый
   подписанный выпуск и50 инвайтов. Сейчас подготовлено10, дополнительные40 не созданы.

## Rollout / rollback

Исходник3f6f662 + dirty changes; Android0.1.7-beta08/code8, Store1,
RNS1.5.1/LXMF1.1.1 без смены версий. Последние ранее сверенные CI:
Client builds34857790251/f4f320f success, phase034859397457/3f6f662 success.
Последние зафиксированные releases desktopv0.2.9/tcp-v0.1.0 от11.09.
Новая работа этими CI не проверена. Установка на телефоне здесь не подтверждалась.

Для существующей установки не запускать install-access.py: это fresh install.
Сначала приватный SQLite backup access.db, затем additive ChatAccess.initialize()
на этой БД (CREATE IF NOT EXISTS, без изменений invites/devices), доставка
control/friends/chat.py + messenger/__init__.py/admission.py вместе с API,
расширение существующего /friends/ nginx location двумя chat routes и проверка
nginx -t. Перезапуск только friends-access после проверки зависимостей и миграции.
Fresh installer обновлён в исходниках; повторная установка поверх existing запрещена.

Реальный rollout ещё не выполнялся: нужно сначала подготовить и проверить применение
membership/отзыва на узле, bootstrap и end-to-end сценарий. desired_members содержит
публичные ключи, но это private operator membership: не писать в Git/логи/публичный API.

Rollback: отключить chat routes/регистрационную кнопку и вернуть прежний API bundle;
две новые таблицы оставить до отдельного решения, не восстанавливать старую DB
поверх новых активаций. VPN identities/invites/историю не удалять. Если membership
уже применён в будущем, rollback должен отдельно отозвать соответствующий доступ
на узле. На текущем шаге удалённый mailbox не менялся.
