# Редактирование и голосовые — Android beta45, 2026-09-23

Пользователь расширил задачу: список/правка объявлений, правка своих личных сообщений,
голосовые со сжатием как в Sideband. Реализованы native Android UI и общий Python core.

Объявления: серверный список с пагинацией50, архивом и предпросмотром редактирования.
Свежий signed device proof для list/edit, проверка роли, optimistic revision conflict409,
идемпотентный request_id, приватная история before/after/actor в edit_operations.
V2 feed передаёт revision/updated/editor; v1 сохраняет исходные неизменяемые сообщения,
чтобы старые клиенты не отвергали ленту. Для получения исправлений нужна beta45.
Получатели/срок/исходный автор объявления не меняются. Тесты не изменяли реальные записи.

Личные сообщения: долгий тап на своём текстовом сообщении открывает редактор внутри
того же окна. Подписанная LXMF-правка с target ID/revision передаётся зашифрованно;
получатель применяет её только к сообщению того же автора/диалога/направления.
Контрольные записи скрыты из видимой истории; порядок получения не важен, replay не
сбрасывает прочитанность. Исходные подписанные байты сохраняются для повторов доставки.

Голосовые: Opus/Ogg через стандартный LXMF FIELD_AUDIO/AM_OPUS_OGG (формат также
используется Sideband). Моно12кбит/с, до60секунд/128КиБ; запись Android10+.
Запись → прослушивание → отправка; запрос микрофона только по нажатию пользователя.
Временные файлы приватные, удаляются при завершении/выходе; история и outbox зашифрованы.
Воспроизведение доступно в пузыре чата. Синтетическое аудио проверялось без микрофона.
Реальную микрофонную запись и второй Android должен ещё проверить пользователь.

Версия0.1.18-beta45/code45, ARM64,36444236 байт.
SHA256 `239d6008d899722980c9c869be3df4ec2ae9c87aa2f1b234a0858f843aa020c4`.
Прежний signing certificate сохранён. Данные приложения не очищались.

Проверки: Python150 passed вне песочницы (локальные сокеты запрещены внутри);
дополнительно11 targeted passed, включая полную минутную Opus-запись через настоящий
локальный Reticulum ingress/шифрование/доставку и старый размер transfer budget.
Android147 unit/build/lint passed. Native Opus encoder/silent playback, v2 import,
role proof,notification/service/dashboard/language passed. Первый UI список timeout;
повторная отдельная проверка list API и списка прошла. Preview-проверка просмотра/редактора и прямого list API прошла (2 native tests), без сохранения правок.

Серверы:
- RU `/opt/apps/family_connect/friends-access/backup-notices45/manifest.json`:
  исходники API/validator, nginx и новый v2 feed. Никакие объявления не редактировались.
- NL `/opt/apps/family_connect/mailbox-pilot/backup-voice45/`: codec.py/relay.py;
  mailbox active, identity и SQLite spool сохранены. Предел ciphertext131840,
  spool1МиБ/sender256КиБ, batchдо192КБ; запросы старых клиентов48КБ сохраняются.
- Откат сервера: восстановить исходники по manifest, restart только соответствующего
  Friends API/mailbox; nginx -t и HUP product HTTPS. VPN не перезапускался.
  После появления больших voice envelopes старые лимиты relay могут задержать их
  до повторного обновления — не очищать spool при откате.

Beta45 опубликована в Android discovery; public APK size/SHA256 проверены.
Backup discovery/nginx: `/opt/apps/family_connect/state-product-https/config/backup-android45-v2/`.
Для отката discovery восстановить manifest-before.json; APK immutable, старые версии сохранены.
Beta45 установлена на подключённом телефоне с прежней подписью. Финальные3 updater/VPN native tests passed. После instrumentation VPN восстановлен
обычным запуском; Current Networks VPN CONNECTED, ConnectionService/AWG/ChatDeliveryService
живы. SHA256 установленного APK совпал; временный UI-test пакет удалён.
Далее: реальные микрофон/второй Android, Doze/OEM/Android13+ и общая desktop-публикация.

Источники формата: https://github.com/markqvist/Sideband,
https://developer.android.com/reference/android/media/MediaRecorder.AudioEncoder,
https://developer.android.com/reference/android/media/MediaRecorder.OutputFormat.
