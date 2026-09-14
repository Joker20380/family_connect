# Закрытый узел: приём и ограниченный том

`messenger.relay.ClosedRelay` — прикладной прототип на RNS1.5.1. Он принимает
ciphertext через `/family_connect/chat/v1/put` только после RNS-identify разрешённой
identity. Получатель также должен входить в закрытый список. Native LXMF uploads,
peer offers и автоматическое peering не регистрируются. Для отправки нужен
`Mailbox.publish(id)`, а не обычный PROPAGATED-клиент LXMF/Sideband. GET API совместим
с нашим Mailbox на основе LXMF1.1.1. Новый wire-протокол Reticulum здесь не вводится.

Параметры Spool по умолчанию:

- Ciphertext всего262144 байта/128 сообщений; одному отправителю65536 байт/32.
- Не более4864 байт на envelope, до10 сообщений/48KB в ответе.
- Срок хранения86400 секунд, удаление при get/put/явном expire. Фоновый вызов
  expire выполняется daemon loop каждые60с; secure erase не заявляется.
- Жёсткий размер SQLite-файла:192 страницы по4096 байт =786432 байта. Индексы и
  свободные страницы входят в лимит. DELETE journal и RNS runtime требуют отдельного
  ограниченного файлового тома; max_page_count не выдаётся за квоту всей службы.
- Приём: burst4, восстановление1 запроса/s на разрешённую identity. Квоты и
  запись атомарны, один владелец процесса, конкурирующие callback сериализованы.
- База хранит ciphertext и открытые sender/recipient hashes, время и размеры.
  Ключа получателя на relay нет. Успешный put возвращается после FULL commit.

При повторе после потери ACK клиент использует один и тот же encrypted envelope,
сохранённый в своём encrypted Store. Копия не занимает квоту повторно, в том числе
после перезапуска отправителя. При full/rate_limited/unavailable сообщение снова queued.

## Изолированный тест настоящего ENOSPC

`volume_check.py` запускается только в одноразовом контейнере без сети. Ему нужен
приватный каталог `/lab` с новым, заранее форматированным ext4 regular file
`relay.ext4` ровно16MiB. Не передавать рабочие диски/каталоги. Тест монтирует файл
в собственном mount namespace контейнера, заполняет том, проверяет отказ без ACK,
сохранность старого сообщения и запись после освобождения места. В finally — umount.
Результат13.09: ENOSPC=true, false_ack=false, previous_message_preserved=true,
recovery_and_reopen=true. Production volume/service этим тестом не создавались.

## Развёрнутый Amsterdam-пилот

Отдельная служба на TCP4243, том64MiB и две диагностические identity приняты вживую.
`install_amsterdam.py` создаёт новую установку из проверенного публичного bundle,
`family-connect-mailbox.service` ограничивает права/ресурсы, `messenger.server --check`
отказывает без отдельного тома. `amsterdam_peer.py` — диагностический клиент,
выводящий размеры LXMF/ciphertext и счётчики RNS без раскрытия ключей.

Инструкции, bootstrap, лимиты, тесты и откат:
[отчёт](../../docs/releases/2026-09-13-amsterdam-mailbox.ru.md).
RNS может принять часть request resource до callback: прикладные квоты не заменяют
ограничения памяти/тома и не доказывают устойчивость к произвольной нагрузке.
