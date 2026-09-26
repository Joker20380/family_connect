# Проверка актуальности локальных SQLite

Модуль [scripts/sqlite_backup_compare.py](../scripts/sqlite_backup_compare.py)
предназначен для закрытого операторского процесса, не публичного API. Он возвращает
байты snapshot/внутренний digest/boolean, не печатает schema, records или hashes.
Содержимое БД и подробный inventory остаются в KeePassXC.

## Алгоритм

Источник — owned regular file0600, без symlink/hardlink на самом файле. Оператор
выбирает доверенный source root. Проверяется размер16MiB; online backup через SQLite
API учитывает committed WAL pages. Снимок выполняется в памяти с15s deadline;
quick_check и inode/dev guard отказывают при повреждении или замене файла.
После завершённого backup образ переводится из WAL-header mode в standalone mode;
так нельзя обрабатывать необработанный файл работающей WAL-базы без backup API.

Для сравнения две завершённые копии открываются в отдельных in-memory connections.
trusted_schema выключен, query_only включён. Сравниваются SQL schema без физических
root pages, user_version/application_id/encoding, типизированные значения всех строк,
повторы и доступный implicit rowid. WITHOUT ROWID поддерживается. Virtual tables и
полностью перекрытые user-columns псевдонимы rowid/_rowid_/oid отклоняются.
Нормализация не учитывает freelist/page layout и journal headers. Текст SQL schema
сравнивается точно: эквивалентные, но иначе записанные определения могут дать отличие.
Лимиты100000 rows/64MiB serialized row data и10s SQLite progress deadline; это не
универсальный diff больших баз или гарантия общего транзакционного момента нескольких БД.

Тесты: typed values/BLOB/NULL, duplicates/rowid, version/schema changes,
WITHOUT ROWID/quoted identifiers, live WAL, повреждённый image и unsafe source.
Hash остаётся внутренним механизмом сравнения и не публикуется.

## Проверка24.09

Три выбранные локальные базы относятся к пилоту управления и двум тестовым
участникам мессенджера. Все3 логически совпали с ранее сохранёнными vault copies.
Новые online snapshots помещены в отдельный encrypted attachment с закрытым
manifest; binary export SHA256 и повторное logical comparison прошли.
Старая encrypted KDBX сохранена локально. Источники не удалялись, серверы не менялись.

Во время поиска потребителей:0 наблюдаемых открытых DB files,0 совпадающих mount
работающих FC containers. Просмотрено121 process fd directory,310 недоступны.
Это точечное наблюдение с неполной видимостью: не доказательство отсутствия
потребителей, коротких обращений, других mount namespaces или копий по другим путям.
Поэтому классификация — «локальное пилотное состояние, сохранять», не «можно удалить».
state-v2 остаётся документированной зависимостью старых tools; массовое удаление
или автоматическое перемещение identities не выполнялось.

Первый импорт отказал с ValueError до замены основной KDBX. После добавления
диагностики этапов повтор прошёл без изменения логики сравнения/сохранения.
Точная причина первого отказа не установлена; он не считается потерей/повреждением
данных и не скрывается за успешным повтором. Plaintext snapshots на диск не писались.

Далее — явная проверка потребителей перед выведением pilot state из эксплуатации,
независимая внешняя копия и full clean-machine DR. Наличие свежей копии само по себе
не разрешает удалять данные или сбрасывать replay/sequence/revocation state.
