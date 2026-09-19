# Native экраны локального чата — 19.09.2026

Продолжение мессенджера по поручению пользователя. APK остаётся на паузе.

## Изменения

ChatActivity доступна из MainActivity и FriendsActivity; Activity не экспортируется.
Использует существующий TerminalUi: зелёная палитра, рамки, моноширинные подписи.
Английские и русские строки добавлены одновременно.

Пользовательский путь:

1. На пустом устройстве — явное «Создать локальный чат». При существующем state —
   только resume; остатки vault/Keystore/Store или ошибка открытия не вызывают reset.
2. «Моя карточка» показывает публичный ключ, полный fingerprint и адрес. Копируется
   только public key по нажатию пользователя, без private identity/Store key.
3. «Добавить контакт» принимает public key, показывает вычисленный fingerprint;
   сохранить можно после отметки о независимой проверке всего отпечатка. Собственный
   ключ и некорректные данные отклоняет существующий LocalChat API.
4. Контакты отображаются короткими адресами; полная карточка доступна для сверки.
   Имена контактов пока не добавлены. Переписка открывается на последней странице,
   по50 сообщений; можно листать предыдущие/следующие страницы и обновлять историю.
5. «Сохранить в очередь» вызывает реальный encrypted Store commit. После успеха
   input очищается; ошибка оставляет текст. Нет имитации отправки, фиктивных сообщений
   или сетевой кнопки без bootstrap. Баннер объясняет локальный режим.

Queued/sending/relayed/delivered/received имеют разные подписи; relayed подписан
«Сохранено на узле». Текущее локальное создание/сохранение не включает доставку.

## Владение и lifecycle

Один process FIFO executor выполняет Store/Keystore/Python вне main thread.
OnStop ставит close после уже принятых операций, новое открытие ждёт предыдущий
close. Поздние UI callbacks отбрасываются по generation; на время операции элементы
отключены, повторное сохранение по двойному нажатию не запускается.

Draft сохраняется при ошибке commit. Маркер успешного commit учитывается и при
возврате/rotation, чтобы уже сохранённый текст не появлялся снова как несохранённый.
Rotation сохраняет UI данные в RAM через retained state; process death не сохраняет
draft. История и identity остаются в прежнем зашифрованном Store. FLAG_SECURE,
отключённые autofill/view saved-state для ввода; никаких черновиков в Bundle.

ChatKeyVault.hasState и ChatLocalAndroid.hasState проверяют также orphan key/backup
и существующий каталог. Instrumentation orphan/corruption сценарии дополнены
утверждениями hasState; пока не запускались. Новых миграций Store или ключей нет.

## Проверки

- javac17: ChatActivity, ChatLocalAndroid, ChatKeyVault, ChatKeyEnvelope,
  ChatStoreCipher, ChatNetworkAndroid, PythonRuntimeAndroid, TerminalUi — passed.
  Classpath: Android35, реальный Chaquopy Java16.1.0 из Maven Central, cached Gson2.10
  (app pinned2.13.2). R.java временно сгенерирован из strings.xml только для javac.
  Предупреждения о deprecated Android APIs; AAPT/Gradle/lint/runtime не выполнялись.
- `python -m pytest -q messenger/tests/test_android_bridge.py messenger/tests/test_local.py`:
  28 passed. Python API не менялся в этом шаге.
- XML parsing, полный набор chat strings EN/RU, ссылки нового checkpoint и
  `git diff --check`: passed.
- Последняя полная проверка прошлого шага:104 messenger и497 общих/2 warnings;
  заново полные наборы здесь не запускались.

## Оставшиеся шаги

Реальное разрешение пользовательских chat identities на закрытом узле и доверенный
bootstrap, затем configureDelivery/сетевые lifecycle callbacks из UI. Диагностические
identity Amsterdam не используются как пользовательские. QR,49 смайлов и имена
контактов ещё не подключены. Прямой/постоянный фоновый приём и уведомления не заявлены.

После снятия паузы APK: Android resources/lint, rendering на320/360/430dp, крупный
шрифт, клавиатура/прокрутка50 сообщений, TalkBack, hardware back, rotation во время
commit, повторное открытие/ошибки Keystore, две реальные identity на двух телефонах,
Wi-Fi/mobile/сон/VPN. Сейчас native rendering/interaction не проверены; HTML-макет
предыдущего шага не является скриншотом этой Activity.

## Версии / rollout / rollback

Исходник3f6f662 + сохранённые локальные изменения. Android0.1.7-beta08/code8,
RNS1.5.1/LXMF1.1.1, Store1 — без изменений версий/формата.
Последний ранее сверенный CI: Client builds34857790251/f4f320f success,
phase034859397457/3f6f662 success; не проверяет новые dirty sources.
Последние зафиксированные releases: desktopv0.2.9/tcp-v0.1.0 от11.09.
Нового APK, CI, push, signing, установки, release или серверных изменений нет.

Rollout: завершить enrollment/network UI, снять паузу, пройти Android/device gates,
затем существующий immutable release/offline signing процесс. Публичное оформление
GitHub обязательно после мессенджера; цель50 инвайтов сохраняется (подготовлено10).

Rollback этого шага: убрать навигацию «Чаты», manifest registration и ChatActivity;
вернуть изменения hasState/strings при необходимости. Успешно закрыть chat owner
до отката. Не удалять Store/vault/историю и не сбрасывать остальные dirty изменения
carrier/bridge/TerminalUi. Production release pipeline и VPN networking не менялись.
