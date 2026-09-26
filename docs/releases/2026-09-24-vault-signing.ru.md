# Ключи подписи из KeePassXC —24.09.2026

Три issuer scripts получили общий loader с opt-in `--vault`, вводом пароля локально,
бинарным memfd export, проверкой private inventory и pinned public key. Само значение
ключа не передаётся через argv/logs и не экспортируется открытым файлом. Старый
`--key` сохранён с унифицированными owner/mode/nlink/no-symlink проверками.
[Runbook и ограничения](../vault-signing.ru.md).

Полный Python regression:896 passed,2 deprecation warnings. После уточнения безопасной
диагностики9 targeted tests passed. Synthetic real KeePassXC test подтвердил подпись
Windows update и отказ при неверном пароле; добавлена установка CLI в phase0 CI.
Проверено чтение рабочего key из vault и совпадение с публичным anchor: success,
без создания подписи. Первый рабочий запуск не завершился; повторная проверка прошла.

Ни production, ни каталоги обновлений, ни исходные ключи не менялись. Versions:
Android beta50/code50, Linux0.2.10, Windows0.2.13. Открытые оригиналы пока сохранены;
полное закрытие секретов/серверная миграция/внешний backup не завершены.
Откат — прежний `--key` путь; формат vault и wire signatures не изменён.
Карта, политика, STATUS/PLAN обновлены вместе с кодом. Публикуются только исходники
и инструкции; KeePassXC и приватный инвентарь в Git не попадают.
