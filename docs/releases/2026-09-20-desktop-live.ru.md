# Живой desktop Friends pilot — 2026-09-20

Источник preview3e5943c, bundle52d42ebe92d774a0, SHA256
ceed62bde654005d981206a7fd0aa09c97a82c628192db3fd3702be528fb8229.
Windows CI artifact10599641893/run35492618663 — подготовлен источник скачивания,
локально не скачан и не установлен на Windows пользователя.

RU/NL Friends службы active. Создан отдельный Linux pilot invite, не из тиража50
и не из referral pool. Identity сохраняется в штатном friends-identity; коды/ключи
и служебные результаты остаются в закрытом state-client-build/desktop-live-20260920,
не в Git. Подписанный catalog sequence3 проверен для обеих стран.

На Linux установлен AWG3.1 helper; старый комплект сохранён в
/var/backups/family-connect/desktop-awg31-20260920. GUI current0.2.8 не переключён.
Первый импорт при umask077 создал root metadata0600. Туннель не поднялся;
read metadata заблокировал rollback. Исправлены AWG/TCP writers (fchmod644 metadata,
600 private profile), восстановлены права только нового pilot metadata, затем
штатный Friends recovery завершён. Source fix локальный, CI/commit ещё впереди.
Локальные регрессии76 passed/2 skipped, включая6 новых umask checks.

| Подключение | Время apply | Internet health | Cleanup routes/rules/DNS |
|---|---:|---|---|
| NL AWG3.1 |14.25s|passed|baseline restored|
| RU AWG3.1 |21.4s|passed|baseline restored|
| NL TCP |22.63s|passed|baseline restored|
| RU TCP |14.76s|passed|baseline restored|

Это подключение из текущей сети пользователя, не проверка из российского провайдера.
После жалобы на примерно20 запросов пароля: процесс уже завершён, fcawg/fctcp
интерфейсов нет. Повторные pkexec на import/up/down и повторный прогон дали лишние
диалоги; сценарий авторизации нужно исправить перед следующим пользовательским тестом.
Новых сетевых проверок не запускать до исправления потока авторизации.

Rollback: сначала штатно отключить VPN/recover journal; вернуть файлы helper из
root backup только после очистки и проверки несовместимости старых tools с31.
before-metadata-awg.py/before-metadata-tcp.py сохраняют состояние до fchmod fix.
Не удалять identity/journal и не возвращать private profiles в Git. Серверные службы
не изменялись; добавлено только отдельное pilot устройство через штатный Friends API.
Открыто: auth UX fix, commit/CI metadata fix, Windows live, российская сеть,
новая immutable подписанная поставка. Androidbeta19/public desktopv0.2.9 прежние.

Продолжение: [auth session реализован и изолированно проверен](2026-09-20-linux-authorization.ru.md); установка ещё впереди.
