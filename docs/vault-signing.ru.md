# Подпись с ключом из KeePassXC

Локальный Linux operator workflow. Код: `scripts/signing_key.py`; потребители:
`sign_update.py`, `sign_control_config.py`, `sign_friends_catalog.py`.
Не серверный secrets manager и не физически офлайн signing station.

## Проверка без подписи

Запускать из корня проекта в Python environment с cryptography. Установлены
KeePassXC CLI и, для графического ввода, Zenity. Значения ниже — placeholders,
не реальные пути/названия приватного хранилища.

```sh
python -m scripts.signing_key --vault /private/operator.kdbx --vault-entry 'GROUP/ENTRY' --vault-member 'path/inside/archive.key' --vault-public-key clients/desktop/update.pub --vault-password-dialog
```

Требуется существующее вложение `recovery.tar.gz` с `PRIVATE-INVENTORY.json` по схеме
локального импорта. Ключ — ровно32 байта Ed25519. Список имён записей и member paths
хранить в закрытом runbook; не копировать приватный inventory в Git.

Без `--vault-password-dialog` используется локальный TTY и скрытый ввод. Если TTY
недоступен, операция не переходит к открытому stdin prompt. Нет параметров передачи
мастер-пароля через argv/environment. Не подставлять пароль в команды или чат.

## Подпись после необходимых release-проверок

У существующей команды заменить `--key PATH` на четыре vault options выше;
остальные параметры платформы, sequence, input/output и проверки релиза прежние.
Пример формы команды, не поручение выпускать реальный релиз:

```sh
python -m scripts.sign_update --vault /private/operator.kdbx --vault-entry 'GROUP/ENTRY' --vault-member 'path/inside/archive.key' --vault-public-key clients/desktop/update.pub --vault-password-dialog --platform windows --version X.Y.Z --sequence N --artifacts /private/verified-artifacts --output /private/new-catalog.json
```

Аналогичные options доступны для control config и Friends catalog. Нельзя обходить
приёмку артефактов, monotonic sequence и неизменяемость опубликованных релизов.
`--initialize` допускается только с файловым `--key`; vault workflow не создаёт/не
меняет корневые ключи. Режим `--key` сохранён для совместимости, проверки regular file,
owner, nlink1, mode0600 и запрет symlink теперь общие.

## Механизм и ограничения

KDBX открывается через проверенный file descriptor; CLI получает пароль через pipe,
не argv. Бинарное вложение экспортируется в Linux memfd, не CLI --stdout (он менял
binary bytes при проверке2.7.10). Tar читается в памяти без extract на файловую систему.
Проверяются canonical member path, regular entry, отсутствие повторов,32-byte length,
размеры/число entries, SHA256 из private manifest и соответствие public anchor.
Неверный пароль, повреждённый архив, другой key/anchor останавливают операцию.

Общие CLI diagnostics подавлены: наружу идёт только категория/этап отказа. Core dump
для vault operation отключён. Ограничения размера: KDBX/export16MiB, распакованный
архив16MiB и1024 entries, inventory1MiB. Экспорт может временно занять больше памяти
до проверки его размера. Содержимое может оставаться в памяти Python/CLI и swap:
это не гарантия против root, дампа памяти или компрометации ноутбука.

## Приёмка24.09

896 Python tests passed, включая реальный временный KDBX с синтетическим ключом:
создание Windows catalog и проверка подписи, неверный пароль без output.9 targeted
checks passed после добавления безопасного обозначения этапа отказа. В phase0 CI
добавлена установка KeePassXC для исполнения этого теста; в окружении без CLI
интеграционный test skipped, это не native acceptance.

Рабочая база проверена только командой проверки источника: public anchor matched,
без подписи и plaintext export. Первый запуск не завершился, повторный succeeded;
успешная проверка не означает выполненный выпуск на рабочем ключе. Control/Friends
signer получили общий loader, их реальная подпись из рабочего vault не выполнялась.
Рабочие оригиналы и live services не изменялись. Внешнего backup пока нет.
