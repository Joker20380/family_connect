# Администратор на Android — 2026-09-23

Роль администратора объявлений привязана к существующей signing identity подключённого
телефона, не к ADB serial/IP и не к общему токену. Назначение проверяет активность
устройства в Friends access. Новые role/publish endpoints требуют одноразовый proof;
member/revoked device/revoked role не могут публиковать. Назначение других администраторов
остаётся операторской командой; приложение не получает серверных полномочий.

Android 0.1.18-beta43/code43, ARM64, 36 423 756 байт, установлен поверх beta42.
SHA256: `13387b97d64bfc715edc95c0dbdd5658a21859c663b03e0998f1fc12f578f3bf`.
Сертификат прежний: `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
Мессенджер → Family Connect → ⋮ открывает проверку прав и форму объявления.
Предпросмотр и отдельная публикация; ошибки связи допускают повтор с тем же ID.
Публичная лента не содержит тестовых объявлений.

Проверки: Python77 passed; Android assembleFriends/AndroidTest,147 unit,lint passed.
С телефона подтверждён server role=administrator (existing identity preserved).
5 прежних native notification/service/dashboard/language тестов passed.
Новая native UI-проверка passed после замены фонового старта на обычный вход через
FriendsActivity: итого7 native tests (роль/экран +5 прежних). Дополнительно3 passed:
публичная загрузка APK/подпись/запрет повторной установки, live check в настройках,
восстановление VPN. Тестовые ошибки запуска Activity не выдаются за приёмку.


Сервер: RU Friends API; резервная копия исходников и nginx
`/opt/apps/family_connect/friends-access/backup-device-admin-20260923-v2/manifest.json`.
Первая установка системным Python не нашла RNS и автоматически откатилась;
повтор в venv сервиса прошёл, роль назначена. VPN gateway не перезапускался.
Откат API: восстановить файлы по manifest, nginx -t, restart только Friends API,
HUP family-connect-product-https. Отзыв роли: service_notices revoke-device.
Роль и остальные данные сохраняются отдельно в notices.sqlite.
Не удалять приложение: исправление клиента выпускать новой версией.

## Публичное обновление

В Android discovery опубликована **beta43**. С внешнего компьютера и телефона
скачаны метаданные/APK; SHA256, размер, package и подпись проверены. Телефоны с beta35
увидят обновление через Настройки → Проверить обновления. Публичная лента объявлений
остаётся пустой. Страница приглашения и GitHub README пока ведут на прежнюю beta35;
их синхронизация с общей публикацией клиентов остаётся отдельным пунктом.

Серверная резервная копия:
`/opt/apps/family_connect/state-product-https/config/backup-android43-v2/`.
Первый public fetch получил404 до завершения nginx HUP, metadata не переключились;
после ожидания применения конфигурации полный public fetch прошёл.
Откат обнаружения: восстановить `manifest-before.json` в `android-friends-update.json`.
Старые APK не удалены; установленную beta43 не понижать с очисткой данных,
исправления выпускать следующей версией. Nginx-файлы для отката перечислены в files.json.

Остаются длительный Doze/два фоновых телефона/Android13+ consent/OEM/boot и согласованный
выпуск остальных клиентов. Обычное VPN-соединение восстановлено после instrumentation: Current Networks VPN CONNECTED, ConnectionService/AWG/ChatDeliveryService живы. Установленный APK SHA256 совпал; временный отдельный UI-test пакет удалён.
