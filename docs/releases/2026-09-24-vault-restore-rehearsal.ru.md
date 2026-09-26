# Восстановление серверных копий на изолированном контейнерном стенде

24.09.2026: из существующего KeePassXC извлечены четыре application/infrastructure
attachments RU/NL. Проверены и восстановлены89 файлов/7 SQLite. Vault не изменялся,
production hosts не затрагивались; контейнер без внешней сети удалён после проверки.
Plaintext архивы не сохранялись на диск; restored files находились в tmpfs.

Фактический результат: Access/ChatAccess открываются, referral HMAC совпадает с
сохранёнными связями, mailbox identity совпадает с public anchor в settings,
preflight проходит на отдельном mounted state, spool открывается. Реальный
messenger.server стартовал, слушал4243 в изолированном namespace и завершился по
SIGTERM с кодом0. В восстановленной базе6 разрешённых chat identities.
12 tests passed: snapshot/restore, TLS links, отсутствие перезаписи, отказ при
symlink staging path; отдельный реальный probe использовал содержимое KDBX.

Образ проверки family-connect-vault-restore:20260924, image ID prefix3ddff9c300c0,
на основе локального family-connect-source49-tests с LXMF1.1.1 из hashed lockfile.
В Git сохранён Dockerfile такого расширения; исходный control image нужно подготовить
отдельно. Это не воспроизведение новой ОС с нуля. Операторский CLI runner локальный,
в Git — probe, синтетические tests и подробный [runbook](../vault-restore-rehearsal.ru.md).

Не приняты: systemd/service-user ownership на чистом хосте, TLS/HTTPS и sshd startup,
VPN handshake/трафик, обмен сообщениями двух клиентов, свежесть прав после backup,
внешний носитель. Production configs/code не менялись; клиентские версии прежние:
Android beta50/code50, Linux0.2.10, Windows0.2.13. Рабочие plaintext originals сохранены.
Откат production не требуется: стенд удалён, исходные backups и live state неизменны.

Следом — инвентаризация оставшихся plaintext секретов и потребителей, затем точечная
миграция с проверкой запуска. Удалять старые ключи/копии можно только после проверки
каждого потребителя и внешнего recovery backup. Полный clean-machine restore остаётся
отдельным открытым критерием; этапы5.2/5.3 и Django7.1 не закрыты.
