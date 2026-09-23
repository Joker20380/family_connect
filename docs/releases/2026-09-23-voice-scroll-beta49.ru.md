# Голосовые, прокрутка и фон — beta49, 2026-09-23

Продолжение [жестов beta48](2026-09-23-voice-hold-beta48.ru.md).
Пользователь подтвердил запись и доставку обоими жестами, а также уведомление при
выключенном экране. По замечанию о видимости отправки beta49 сохраняет текстовую
кнопку постоянно видимой, отключая её для пустого текста. Новое сообщение выбирает
последнюю страницу истории и прокручивает после layout. Обновление статуса без новых
сообщений сохраняет позицию чтения. Отдельных окон записи нет.

## Сборка и приёмка

Android0.1.18-beta49/code49, ARM64,36448332 байт.
SHA256 `3a37613a63c130af97c853d1c39836c026822dca717a748fa005a3211f8f549d`.
Сертификат SHA256 `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
153 unit tests, lint и сборка passed. Native VoiceHoldRuntimeTest и
ChatScrollRuntimeTest passed на Redmi Note9Pro/API31; synthetic hold/scroll renders
просмотрены. Проверены пустая/непустая строка, новые сообщения после прокрутки вверх,
обновление статуса без скачка позиции, явная прокрутка при неизменённой истории.
Тесты используют синтетическую историю и fake recorder, не отправляют переписку.
Установлена adb -r без очистки данных; test package удалён, обычный FriendsActivity
запущен. VPN был выключен до работы и не включался.

## Публикация и откат

Discovery `https://185.251.89.19:8443/updates/android-friends.json` указывает на49.
APK `/downloads/FamilyConnect-Test-0.1.18-beta49.apk` неизменяемый;48 не публиковалась.
Installer проверил nginx -t, публичный APK hash/size и discovery. Независимое внешнее
скачивание также прошло; local evidence: beta49/public-verification.json.
Изменены только Android download routes/discovery в family-connect-product-https.
Backup: `/opt/apps/family_connect/state-product-https/config/backup-android49-v2`:
manifest-before.json содержит47, files.json сопоставляет nginx configs с backup0/1.
Для отката вернуть прежний discovery и nginx configs по files.json, проверить nginx -t,
перечитать только family-connect-product-https. APK49 не заменять. На телефоне не
удалять приложение/данные ради downgrade; исправление ставить новым versionCode.

## Фоновый режим

Пользователь подтвердил обычную доставку с выключенным экраном на beta48.
На beta49 после ручного выключения экрана выполнен ограниченный Doze-тест:
IDLE около122с, затем unforce и battery reset, восстановлен ACTIVE;
ChatDeliveryService присутствовала во всех наблюдениях. Настройки battery exemption
не менялись. Первая попытка получила INACTIVE предположительно из-за гонки с battery unplug; после
паузы обработки unplug вход в IDLE подтверждён. MIUI не разрешила ADB INJECT_EVENTS,
поэтому экран выключал пользователь. Все попытки завершены восстановлением режима.

Пользователь сообщил: «прожужжало но экран не включился». Уведомление сработало,
но время относительно выхода из IDLE пользователь не заметил. Проверка доставки
именно в IDLE остаётся открытой; подтверждено получение уведомления с выключенным экраном.
Количество/ревизия notification records не изменились; это не доказывает ни успешную
доставку, ни потерю. Нужна привязка фактической отправки к окну IDLE и проверка получения
после выхода. Длительный сон, OEM, Android13+ notification consent и boot не закрыты.
Приложение использует собственный polling без FCM; Android может блокировать сеть в
Doze даже с foreground service: [Android documentation](https://developer.android.com/training/monitoring-device-state/doze-standby).
Следом по плану остаётся согласованный выпуск клиентов; эта проверка его не заменяет.

Финальная проверка: установленный SHA256 совпал с публичной49; forced idle=false,
battery simulation=false, ChatDeliveryService=true, VPN ConnectionService=false.
