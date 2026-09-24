# Изолированная проверка серверных копий KeePassXC

Код: [vault_restore_probe.py](../scripts/vault_restore_probe.py),
[тесты восстановления](../tests/test_vault_restore_probe.py),
[Dockerfile](../pilot/recovery/Dockerfile).
Это проверка восстановления состояния в контейнере, не полный clean-machine DR.

## Подготовка и границы изоляции

Операторский helper читает четыре attachments из группы Backup inventory:
application RU/NL и infrastructure RU/NL. Мастер-пароль вводится локально в Zenity,
передаётся KeePassXC через stdin. Binary export — только memfd, не stdout CLI.
Текущая процедура выбора последних записей каждой роли не доказывает общий момент
backup: даты и доступы нужно сверять отдельно перед настоящим переносом.
Хранилище читается, не изменяется. Helper остаётся локальным операторским инструментом;
публичный модуль выполняет только проверку внутри подготовленного контейнера.

Контейнер запускается с network none, read-only root, cap-drop ALL,
no-new-privileges, memory/memory-swap512MiB, pids-limit64, core limit0 и log-driver none.
В него монтируется только публичный код readonly. Приватные attachments передаются
в памяти через stdin, не аргументы/переменные окружения/файлы на диске.
`/restore` — tmpfs128MiB; mailbox state — отдельный tmpfs64MiB, `/tmp` — tmpfs16MiB.
Все tmpfs nosuid/nodev/noexec. После завершения контейнер удаляется через --rm.
Хостовая память/swap и привилегированный администратор остаются границей защиты;
это не обещание гарантированного уничтожения следов из RAM.

Probe проверяет отсутствие сетевых интерфейсов кроме lo и наличие mount `/restore`.
Остальные ограничения обеспечивает runner, они не проверяются самим модулем.
Нельзя запускать модуль с production root или направлять private stdin в CI/чат/лог.

## Что проверяется

- Все четыре архива проходят inventory/hash/SQLite проверки перед восстановлением.
- Файлы создаются исключительно с новым именем и mode0600, каталоги0700;
  перезапись и пути через symlinks отклоняются. TLS ссылки создаются относительно
  staging root; числовые UID/GID production не переносятся.
- Реальный код Access/ChatAccess открывает RU DB; referral secret сверяется с
  сохранёнными referral_links через HMAC, без вывода токенов/участников.
- Ключ mailbox соответствует public identity в settings. Просроченный membership
  не продлевается; runtime продолжает отклонять его.
- Настоящий mailbox preflight принимает отдельный mounted state volume;
  Spool открывает SQLite, затем сервер стартует и открывает TCP4243 внутри
  изолированного namespace, после SIGTERM завершается успешно.

Результат наружу — только booleans/counts. Ошибки — класс и function/line stack без
exception message, содержимого конфигов или traceback source lines.
Spool при открытии может удалить просроченные сообщения только в восстановленной
копии. Контейнер работает от root без capabilities: это не приёмка UID/GID реальных
service accounts, systemd hardening или persistent ext4 volume.

## Что ещё требуется перед настоящим переносом

Восстановить ОС, зависимости и службы на чистом хосте; сопоставить service accounts,
вернуть рабочие600/640/755 из проверенного инвентаря, подключить ограниченный volume.
Проверить TLS private-key/cert matching и HTTPS, sshd host identity, WG/AWG/TCP
handshake и пользовательский трафик, mailbox обмен между двумя клиентами.
Отдельно сверить актуальные revocations, floors/sequence и изменения после backup.
Исключить работу двух владельцев одной identity/state. Не делать production cutover
по одному успешному контейнерному probe. Исходники секретов до этого сохраняются.
