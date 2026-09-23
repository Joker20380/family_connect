# Запись удержанием и фиксация — beta48, 2026-09-23

Реализованы inline запись и жесты из STATUS/PLAN. VoiceGesture отдельно проверяет
порог/диагональное направление, отмену, фиксацию и отсутствие повторной отправки.
VoiceHoldButton сохраняется в дереве и на месте во время захвата, composer/emoji
временно уступают место таймеру и подсказке. Отмена/фиксация не отправляет сообщение.
В locked mode доступна отправка/отмена в той же строке. Отказ сохранения оставляет
черновик в RAM для повторной отправки, сетевой retry работает через прежнюю очередь.
Запрос mic permission не начинает запись автоматически после возврата.
Уход в другой экран/фон/Back удаляет неотправленную запись и снимает KEEP_SCREEN_ON.
Сетевые обновления истории не заменяют composer/gesture view.

153 Android unit passed, включая6 новых VoiceGesture tests; lint/build passed.
Native VoiceHoldRuntimeTest passed на Redmi API31: касание, отпускание, lock,
отмена слева/системная, accessibility click, render. Fake recorder: микрофон и
переписка не затронуты тестом. Synthetic screenshot просмотрен:
state-client-build/android-pilots/beta48/voice-hold.png.
Реальная запись удержанием/фиксацией запрошена у пользователя и пока не подтверждена.

APK0.1.18-beta48/code48, ARM64,36448332 байт.
SHA256 e840f393bbf52f0e4ec207fb7949064673c879ad8a77673398aaa86e3527f22e
Certificate SHA25667a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a.
APK verify/signature/alignment/version passed. Установлена adb -r поверх beta47
без очистки. Временный test package удалён, запущен обычный FriendsActivity.
Публикации пока нет, публичная beta47 сохранена. Серверы/каталоги/БД не менялись.
Откат подготовки — не публиковать beta48; данные телефона не очищать и версию
не понижать с удалением истории. Следующее исправление публиковать новым номером.

Следующий пункт по указанию пользователя — фоновая доставка. Начат read-only аудит:
foreground service существует; приложение не запрашивает battery exemption и не
использует FCM. Doze может приостановить сетевой polling независимо от наличия FGS.
Источник Android: https://developer.android.com/training/monitoring-device-state/doze-standby
Текущая платформа API31 не проверяет Android13+ runtime notification consent.
Нужны bounded screen-off/Doze/recovery проверки и отдельная длительная/OEM/boot приёмка.

Пользователь подтвердил оба жеста: запись и доставка работают. Screen-off test также
подтверждён: уведомление пришло на второй/подключённый телефон до включения экрана.
Это короткая ручная проверка, не Doze/OEM/boot. До неё read-only snapshot: API31,
RECORD_AUDIO granted, battery exemption=false, deep/light ACTIVE, ChatDeliveryService
и постоянное уведомление живы, installed SHA256 beta48 совпал.

Пользователь заметил исчезающую кнопку отправки (появлялась после ввода) и отсутствие
прокрутки к голосовому. В beta49 кнопка постоянно видима (пустой текст не отправляет),
после новых сообщений выбирается последняя страница и прокрутка выполняется после
layout. Только обновление статуса сохраняет позицию чтения. Beta48 не публиковалась.

Итоговое исправление установлено и опубликовано как [beta49](2026-09-23-voice-scroll-beta49.ru.md).
