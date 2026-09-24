# Потребители секретов и права серверов —24.09.2026

Позднее в тот же день: [отложенный TCP restart выполнен](2026-09-24-tcp-private-umask-restart.ru.md).
Ниже сохранены результаты первоначального аудита до перезапуска.

Проверены только разрешённые RU/NL FC hosts и выбранные каталоги проекта. Содержимое
секретов, systemd Environment/ExecStart и строки БД не выводились. Read-only metadata
не является полным аудитом всех резервных копий, ACL или всех секретов машин.

## Результат аудита

На обоих узлах Friends AWG root0700; server.conf/settings.json/peers.db root0600.
Friends TCP каталог root:fc-friends0750, server.json root:fc-friends0640; служба
работает от fc-friends. На RU Friends access root0700, access.db/referral.key root0600,
служба root с UMask0077. Product state на RU root0700 и выбранные файлы0600.
На NL нет локального Friends access/Product state. Каталог build signing state
не обнаружен в проверенном месте на обоих узлах; это не полный поиск ключа по диску.

Файлы0644/0755 внутри закрытых каталогов в основном код/библиотеки; одни только
mode bits файла не означают доступ извне при родительском каталоге0700/0750.
Нарушения прав известных основных файлов секретов не обнаружены. Root для AWG/API
сохранён: изменение account/capabilities без анализа helper-операций могло нарушить VPN.

## Применено без прерывания служб

В новые install-awg.py/install-tcp.py добавлен UMask0077. На RU и NL установлен
одинаковый systemd drop-in `70-private-files.conf` для двух Friends VPN units;
перед записью исключены symlinks/неожиданное существующее содержимое. Выполнен
только daemon-reload. После него configured UMask0077; MainPID и active-state
сохранились. Runtime /proc mask: AWG0077, TCP0022 на обоих узлах.

Следовательно, TCP creation policy ещё ожидает следующего запуска. Существующий
server.json уже0640 и доступен только владельцу/группе. Перезапуск и interruption
не выполнялись. Откат: убрать только этот drop-in, reload; для изменения runtime
mask потребуется отдельный restart. Права/содержимое самих секретов не менялись.

## Инструменты подписи

Общий KeePassXC loader подключён к sign_tcp.py и tcp_setup_signature.py sign — теперь
пять issuers имеют vault path. Старые API/sign(...key_path...) и `--key` сохранены;
последний также использует строгий common loader. Standalone setup verify не импортирует
operator-only module и не требует KeePassXC: это проверено отдельным subprocess.

40 targeted tests passed: common loader/update/TCP delivery/setup. Реальный временный
KDBX с synthetic key подписал update/TCP/setup envelopes, их подписи проверены;
неверный пароль не создаёт output. Ключи пользователей и production signing не использованы.
Предыдущий15e074b: GitHub phase0 и Linux control preview завершились success.

## Остаток

Рабочие оригиналы на ноутбуке сохранены, внешнего backup нет. Серверные секреты и
актуальные серверные БД не скопированы в vault. Требуются приватный реестр всех
потребителей, согласованное резервирование, план ротации и проверка восстановления;
отдельно — плановый TCP restart, проверка runtime0077 и подключений после него.
.env не заменяет эти проверки и сам не обеспечивает шифрование.
Приложения/публичные версии прежние, каталоги обновлений не менялись.
