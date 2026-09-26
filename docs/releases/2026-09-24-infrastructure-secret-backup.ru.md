# TLS, SSH и mailbox: дополнительная зашифрованная копия

24.09.2026: в локальный KeePassXC добавлены отдельные infrastructure snapshots:
NL14 файлов/1 SQLite, RU28 файлов/0 SQLite. Всего42 файла дополнительно к ранее
сохранённым47 application files. Binary attachment export совпал по SHA256;
SQLite восстановлена в памяти и прошла quick_check. Предыдущая encrypted KDBX
сохранена для отката; plaintext архивы на диск не записывались. Секреты и закрытый
инвентарь не публикуются. Рабочие оригиналы сохранены, services не перезапускались.

Реализация: [snapshot/verify](../../scripts/server_secret_snapshot.py),
[10 targeted tests](../../tests/test_server_secret_snapshot.py) вместе с source guard.
Добавлены проверки TLS link metadata/выхода за границы дерева, отсутствующей identity
и mailbox SQLite. [Состав и восстановление](../server-secret-backup.ru.md).

NL mailbox/AWG/TCP active после копирования. Отдельно обнаружены RU chat-sync
Result=exit-code/ExecMainStatus=1 и истёкший membership lease на NL. Причина ещё не
установлена; исправление синхронизации — ближайший шаг. Это не ошибка резервирования.
Пользовательский обмен сообщениями и восстановление на чистой машине не проверены.

Клиенты прежние: Android beta50/code50, Linux0.2.10, Windows0.2.13. Production code
и configs не менялись: snapshot выполнялся как одноразовая read-only процедура.
Для отката vault доступна предыдущая зашифрованная копия; восстановление сервисов
требует отдельного стенда. Внешний носитель, legacy state и устранение лишних
plaintext originals остаются открытыми. Этапы5.2/5.3 и Django7.1 не закрываются.
