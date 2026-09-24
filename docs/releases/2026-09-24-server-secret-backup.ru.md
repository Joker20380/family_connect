# Зашифрованная серверная копия —24.09.2026

В локальный KeePassXC сохранены два проверенных recovery attachments:
NL7 файлов/1 SQLite, RU40 файлов/5 SQLite. Всего47 файлов/6 баз. Полный приватный
manifest с путями, правами и digest хранится только внутри вложений. Сами архивы,
ключи, DB rows, пароли и реальные vault entry paths в Git не включены.

[Состав, механизм и restore runbook](../server-secret-backup.ru.md).
Данные переданы SSH stdout прямо в память локального процесса, а не в вывод tool.
На диск записаны только зашифрованные KDBX. Импорт выполнен в отдельной encrypted
копии; оба сохранённых вложения выгружены в memfd, hashes совпали, inventory и все6
SQLite quick_check после in-memory restore прошли. Основная база заменена атомарно;
предыдущая encrypted KDBX сохранена локально. Внешней/офлайн-копии пока нет.

## Проверки и изменения

Новый snapshot/verify module и5 тестов. Сначала WAL test выявил ограничение SQLite
in-memory deserialize; по официальной SQLite-инструкции нормализован заголовок только
образа копии. Затем5 snapshot tests и2 publication guard tests прошли:7 passed.
Проверены committed WAL, отсутствие sidecars, неизменность содержимого источников
в synthetic test, занятая registration lock, отсутствующий ключ, symlink,
unfinished registration и подмена содержимого вложения.

Сервисы на production не останавливались/не перезапускались. После копирования
AWG/TCP active на RU и NL. Рабочие ключи, DB state и конфигурации не заменялись.
Применён короткий gateway lock; SQL backup выполняет чтение через SQLite API.
Версии приложений и публичные каталоги прежние.

## Что не закрыто

Нет TLS/system SSH/messenger-node/legacy state-v2 и зависимостей/binaries в этих
вложениях. Нет единого cross-host transaction snapshot. Нет full clean-machine
restore или проверки VPN-трафика из восстановленного сервиса. Нет внешнего носителя.
Следующие шаги: включить неохваченные критические компоненты отдельными копиями,
проверить восстановление сервисов на изолированном стенде и сделать внешнюю копию.
Удаление действующих plaintext originals пока не выполняется.

Откат импорта — предыдущая зашифрованная KDBX; live state менять не требуется.
Документация, план и карта обновлены; публичный код не содержит private inventory.
