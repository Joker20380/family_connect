# Резервирование закрытого серверного состояния

Реализация: `scripts/server_secret_snapshot.py`. Потребитель private stream обязан
шифровать результат до любой записи на постоянный диск. Не запускать этот stream
через инструмент, печатающий stdout в чат/CI/logs. Не использовать shell `tee` или
перенаправление в незашифрованный файл. Инвентарь находится внутри encrypted attachment.

## Состав и границы

Роли фиксированы: RU и NL Family Connect. Friends AWG/TCP top-level рабочие файлы,
без бинарников, lock/WAL/shm, вложенных старых backups и venv. На RU дополнительно
Friends access top-level (API DB/уведомления, ключи, настройки, deployed scripts)
и state-product. Обязательные файлы проверяются до создания архива. Symlinks,
незавершённая gateway registration и превышение лимитов приводят к отказу.

Исключены TLS/certbot, системный SSH/authorized_keys, отдельный messenger node,
legacy state-v2, бинарники, вложенные backups, dependency environments. Это выбранный
набор state/credentials, а не образ машины и не полный disaster recovery комплект.
Git-код, pinned binaries/dependencies и конфигурацию запуска восстанавливать отдельно.

## Получение и проверка

На узле берётся неблокирующий registration.lock Friends gateway. Если занят — отказ,
а не длительное ожидание. Реестр peers и TCP config собираются под этой блокировкой.
SQLite копируется read-only connection → backup API → memory database; quick_check
проверяет копию. Online backup включает committed WAL pages; sidecars не архивируются.
Для standalone deserialize bytes18/19 SQLite image нормализуются в rollback mode по
[официальной инструкции SQLite](https://www.sqlite.org/c3ref/deserialize.html).
Это меняет только образ копии, не источник.

В manifest входят относительный путь, SHA256, размер, uid/gid/mode, метод копирования,
роль и время. Перед/после чтения обычных файлов проверяются inode/size/mtime; замена
отклоняется. Лимиты16MiB и1024 entries. Основная база и notices/Product снимаются
отдельно: это не одна транзакция между базами и двумя серверами. Регистрации могут
кратко ждать gateway lock; служба VPN не останавливается.

Локальный операторский процесс принимает stdout SSH только в память, проверяет tar
без распаковки на диск, exact file inventory/hashes и восстанавливает SQLite в памяти
с quick_check. Затем импортирует attachment в отдельную зашифрованную копию KeePassXC,
выгружает его бинарно в memfd и повторяет проверки. К основной KDBX применяется
atomic replace только после двух успешных snapshots и проверки отсутствия параллельной
правки vault. Старая encrypted KDBX сохраняется локально для отката.

Мастер-пароль вводится локально, не argv/environment/log. Plaintext archives не
пишутся на диск; память/swap/компрометированная ОС остаются отдельной границей защиты.
Текущий операторский orchestration выполнен локальным helper, не установлен как cron
или production backup service. Публичный script предоставляет snapshot/verify, не
автоматическое расписание и не пользовательский интерфейс восстановления.

## Безопасное восстановление

1. Сначала открыть копию на изолированном стенде и проверить inventory/hash/SQLite.
2. Подготовить требуемые версии кода/бинарников и новый isolated state root с0700;
   восстановить только перечисленные regular files с проверкой путей. Не распаковывать
   архив целиком от root в `/` и не перезаписывать работающие БД.
3. UID/GID в manifest — сведения источника: сопоставить service accounts нового хоста,
   не переносить числовые идентификаторы вслепую. Проверить600/640 и родительские каталоги.
4. До выдачи доступа сверить revocations, sequence/replay floors, peers/TCP users и
   изменения после snapshot. Старый snapshot не должен повторно разрешать отозванный
   доступ. Для неохваченных компонентов получить отдельные проверенные копии.
5. Исключить параллельную работу старого владельца state, проверить service startup,
   VPN handshake/трафик и служебные операции на стенде. Лишь затем планировать перенос.

24.09 выполнены только encrypted save, byte/inventory checks и SQLite restore-in-memory.
Полный запуск сервиса на чистой машине и client acceptance из backup ещё не выполнены.

## Дополнительный scope infrastructure

`--infrastructure` использует корень файловой системы и отдельный allowlist:
SSH host keys RSA/ECDSA/Ed25519 (присутствующие пары) и root authorized_keys на обоих
FC hosts; на RU дерево certificates Certbot, на NL node.identity/settings/members,
volume marker, RNS config/transport identity и SQLite spool. Старый application scope
не изменён. Это два отдельных attachments, их нужно восстанавливать совместно с
предыдущими application snapshots и конфигурацией развёртывания.

TLS symlinks не разыменовываются в tar: архив содержит regular targets, а закрытый
manifest — отображение link path → target path. Цель обязана быть обычным файлом
внутри TLS дерева и присутствовать в архиве. При восстановлении сначала проверять
manifest, затем создать файлы и относительные ссылки внутри нового staging root;
не создавать ссылки в работающем `/etc/letsencrypt` вслепую. UID/GID сверять по
служебным пользователям на новом хосте, не переносить числовые ID автоматически.
Host private keys восстанавливать только для замены прежнего узла, не клонировать
одну SSH identity на одновременно работающие разные машины.

Mailbox state.ext4 и RNS caches исключены. Для восстановления нужен новый bounded
смонтированный volume с сохранённым marker, правильными владельцами/правами и
preflight `messenger.server --check`. SQLite spool включает ciphertext сообщений;
он остаётся чувствительными данными. Online backup не гарантирует общий момент
снимка с membership/settings; lease участников после восстановления обновляется
с authoritative RU, а не продлевается вручную. Старые сообщения ограничены retention.
Проверка tar/SQLite в памяти ещё не означает успешный запуск восстановленного узла.
