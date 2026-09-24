# Три локальные SQLite: сверка и обновление backup

24.09.2026: все3 выбранные локальные базы логически совпадают с предыдущими копиями.
В KeePassXC сохранены3 свежих online snapshots; binary export/SHA256 и восстановление
для повторного logical comparison прошли. Точные имена/пути/данные в закрытом inventory.
Оригиналы сохранены, production RU/NL не менялись.14 targeted tests passed.

Добавлены sqlite_backup_compare.py и4 теста: схема/typed rows/rowid, WAL, unsafe
sources и WITHOUT ROWID. Дополнительно прошли10 существующих snapshot/restore tests.
[Методика и ограничения](../local-sqlite-backup-review.ru.md).

Открытых DB files у доступных процессов и mount у работающих FC containers не
обнаружено;310 process directories недоступны. Классификация «локальное пилотное
состояние, сохранять»; это не разрешение удалить identities/базы. Первый импорт
отказал до commit; повтор с уточнённой диагностикой прошёл, точная причина первого
отказа не установлена. Предыдущая encrypted KDBX доступна для отката.

Версии не менялись: Android beta50/code50, Linux0.2.10, Windows0.2.13.
Свежесть выбранных3 local DB backups подтверждена на момент операции, а не навсегда.
Внешний носитель отложен, full clean-machine restore и production Android vault-signing
acceptance остаются открытыми. Следующая разработка по5.3а — managed Android
service/UI/device acceptance; блок секретов целиком не объявляется завершённым.
