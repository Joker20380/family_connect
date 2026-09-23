# Отправка голосовых — кандидат Android beta46, 2026-09-23

Симптом пользователя: после голосовой записи отправка возвращает «Проверьте
публичный ключ или введённые данные». Это invalid_input, общий для формы ключей
и проверки аудио. Реальный файл/телефон пока недоступен, причина конкретной
пользовательской записи остаётся гипотезой до проверки на устройстве.

Подтверждён дефект совместимости: Android OggWriter может завершать запись без
EOS. Наш opus_duration отклоняет такой поток. Регрессия воспроизведена на
синтетическом полном Ogg с пересчитанной CRC и снятым EOS. Исходник Android:
https://android.googlesource.com/platform/frameworks/av/+/refs/heads/main/media/libstagefright/OggWriter.cpp

Исправление: finalize_recorded_opus на стороне отправителя проверяет границы
страниц, CRC и завершённость последнего пакета, выставляет EOS и пересчитывает
CRC, затем применяет прежний валидатор. Никакого восстановления потерянных байтов.
Подписываются уже нормализованные байты; принимающая beta45 понимает их без
обновления сервера. Поддельная/обрезанная запись отклоняется. Ошибка invalid_input
при queue_audio отображается как ошибка записи, без упоминания публичного ключа.

Проверки: 65 Python passed (codec/local/bridge/carrier/chat), дополнительно новый
android_voice через настоящий локальный закрытый Reticulum ingress passed.
Android147 unit: 0 failures/errors/skips; lint/build passed. Сокетные тесты и Gradle
потребовали обычного запуска вне песочницы. Первичная сборка использовала Python3.14:
APK verification остановилась на отсутствующем pyc. После явного Python3.10
пересборка и все проверки упаковки прошли; дефектный APK не подписан/не опубликован.
Generated Python sources совпали с рабочими codec.py/local.py. git diff --check passed.

Артефакт: state-client-build/android-pilots/beta46/FamilyConnect-Test-0.1.18-beta46.apk
Версия0.1.18-beta46/code46, ARM64,36444236 байт.
SHA256: 2a0e2b33cae289d09ad23b0bf1d017bfad640c8d7b3b5a85c7541e6fbbe2ea3f
Certificate SHA256: 67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a
APK verifier, apksigner verify, zipalign16KiB, package/version/launcher checks passed.
Подпись прежняя; локальный артефакт immutable. Не установлен и не опубликован.

ADB дважды вернул пустой список устройств. Пользователь подтвердил наличие двух
телефонов. Следующий шаг — USB с отладкой, установка поверх beta45 без очистки,
реальная запись с микрофона и отправка второму Android beta45+, воспроизведение и
проверка сохранения после повторного открытия. Затем проверка VPN и обычных служб
после instrumentation, и только после приёмки публикация нового immutable APK/discovery.
Doze/OEM и общий desktop выпуск остаются отдельными незакрытыми проверками.

Rollout отсутствует: серверы/discovery/установленные клиенты не изменялись.
Откат локального кандидата — не устанавливать/не публиковать beta46, оставить beta45.
Опубликованные APK не заменять; установку не понижать с удалением пользовательских данных.

## Продолжение: native ошибка очереди и beta47

Beta46 установлена adb -r на Redmi31ce63ba; installed SHA256 совпал. Обычный запуск
успешен, chat service жив; VPN service отсутствовал до/после установки. Пользователь
сообщил: аудио сохраняется, но не покидает очередь. Поэтому доставка не принята.
Native диагностический тест показал online/attached=true и exchange_failed. Второй
тест вывел только тип/строки стека: GeneralSecurityException → relay_blob → _put →
Java ChatStoreCipher.encrypt. Старый лимит65552 нарушается после добавления relay_blob.
Beta47 повышает bounded JSON row до1МиБ, decrypt допускает ещё16байт GCM. Java fixture,
700000/1048576 roundtrip и отказ на oversize passed. Для гарантированной поддержки
длинных голосовых обновление понадобится отправителю и получателю.

Пользователь дополнительно попросил вид голосового как в Telegram: реализуется
компактная кнопка play/pause, декоративная волна, реальный playback progress, duration
и touch seek. Native render и доставка пока впереди. Публичная beta45 не заменена.

На серверах только read-only: mailbox active, sync timer active/Result success,
membership5, lease111с при замере, spool count0/bytes0. Серверы не менялись.

Beta47/code47 собрана с Python3.10, Android147 unit/lint/build passed.
APK ARM64,36444236байт, SHA256
be6d7cd01366a7dd69b4997a205151e07a6536397f21e9ffc0968ab7d4209264.
Сертификат прежний67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a.
APK verifier/signature/alignment/version checks passed; установлена поверх beta46
без очистки. Native diagnostic: attached/online=true, failures0/error=null,
outbox_pending0 в четырёх снимках. Новые сообщения тест не создавал; повторялась
сохранённая пользовательская очередь. Подтверждение получения/звука второго телефона
запрошено. Native визуальная проверка ещё выполняется; публикации нет.

## Приёмка beta47

Пользователь подтвердил: ранее застрявшее голосовое пришло на второй телефон и
воспроизводится. Native обмен error=null/failures0/outbox_pending0. Native
VoiceBubbleRuntimeTest прошёл: play/pause/seek, layout и синтетический render
state-client-build/android-pilots/beta47/voice-bubbles.png визуально просмотрен.
Первый вариант теста не смог запустить Activity через startActivitySync; следующий
упёрся в FLAG_SECURE, затем в external storage тестового context. Итоговый тест
использует shell launch и Canvas только синтетического дерева, передаёт PNG в
результате instrumentation; защита реальной переписки от скриншотов сохранена.
Проблемы были в тестовом harness, опубликованный APK не заменялся.

Временный test package удалён. Обычный FriendsActivity запущен, ChatDeliveryService
жив, установленный SHA256 beta47 совпал. VPN был выключен до обновления и не включался.
Публикация beta47 ещё выполняется; пока публичная discovery остаётся beta45.

## Публикация beta47

Опубликована в Android discovery; immutable APK доступен по
https://185.251.89.19:8443/downloads/FamilyConnect-Test-0.1.18-beta47.apk .
Серверный installer проверил публичный APK size/SHA256 и discovery после nginx -t/HUP.
Предыдущие APK сохранены. Backup:
/opt/apps/family_connect/state-product-https/config/backup-android47-v2/
manifest-before.json содержит beta45; files.json сопоставляет nginx с backup0/1.
Откат discovery: атомарно восстановить manifest-before.json; при откате routes вернуть
nginx по files.json, nginx -t и HUP только family-connect-product-https.
Не понижать установленную beta47 с удалением данных. Не откатывать mailbox/БД:
они в этой задаче не менялись.
Второй Android следует обновить для отправки голосовых и приёма длинных записей.

Внешняя проверка завершена: discovery47, APK36444236 байт и SHA256 совпали.
Receipt: state-client-build/android-pilots/beta47/public-verification.json.
STATUS/PLAN/index обновлены, git diff --check passed. Реальная двухтелефонная
отправка/воспроизведение приняты пользователем; длительная фоновая приёмка остаётся.
