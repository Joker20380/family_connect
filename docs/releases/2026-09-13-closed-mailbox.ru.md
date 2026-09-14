# Закрытый приём мессенджера и квоты — 13.09.2026

База1e24fb97f1af4141aaddf9e3f47200e6cd646340. Pins: RNS1.5.1, LXMF1.1.1,
cryptography46.0.7. Никаких новых APK/версий или изменений рабочего сервера.

## Доставка conf через Reticulum: ответ по текущему состоянию

Да, защищённая доставка VPN-конфигураций уже реализована и проверена на Linux:
внешний relay в Amsterdam → проверка подписи/адресата/ревизии → применение VPN →
health-check → commit/ACK; rollback также проверен. [Живая приёмка](2026-09-13-external-reticulum.ru.md)
и [исправленный Linux-пилот](2026-09-13-linux-control-pilot-pass.ru.md).
Исторические lease имеют срок действия: для нового живого прогона нужна актуальная
подписанная ревизия, journal/anti-replay floor нельзя переинициализировать.

В установленном Android сейчас ручной импорт AWG3.1 `.conf`. Native RNS carrier
ещё не интегрирован; signed control schema пока отвергает поля3.1, хотя manual
parser их поддерживает. [Ограничение схемы](2026-09-13-android-awg31.ru.md).
Нужны версионированная схема/векторы AWG3.1 и Android carrier/lifecycle; не ослаблять
старые подписи/векторы. Это отдельный путь от текста мессенджера: chat не применяет VPN.

## Реализация закрытого узла

`ClosedRelay` принимает ciphertext через новый версионированный RNS request path
`/family_connect/chat/v1/put`, после криптографического identify отправителя.
Список до100 публичных identities задаётся оператором при запуске, проверяются
отправитель и destination получателя. Анонимный native LXMF packet/resource upload
и peer offer не имеют обработчиков. Скачивание использует известный LXMF GET API,
привязанный к identity получателя. Это расширение прикладного ingress Family Connect,
не fork wire-протокола RNS. Стандартный Sideband/PROPAGATED sender автоматически
с таким ingress не совместим; нужен наш `Mailbox.publish()`.

`Spool`: ciphertext в private SQLite, лимиты до insert и в той же транзакции;
общий/per-sender count+bytes, FULL commit перед stored response, постоянные message
IDs по hash ciphertext. Клиент сохраняет ciphertext в encrypted Store и повторяет
те же bytes после потерянного ACK/перезапуска. Full/rate_limited/unavailable не
выдают relayed и возвращают сообщение в queued. Персональный token bucket:
burst4,1 запрос/s. Просроченные записи исключаются при работе с очередью.

При default262144 bytes/128 messages и per-sender65536 bytes/32 messages SQLite
получает hard ceiling786432 bytes (192×4096). Это предел **файла базы**, не всего
каталога. Реальный отдельный файловый том должен покрывать журнал и RNS cache.
Данные sender/recipient/time/size видны на узле; текста и recipient private key нет.
[Параметры и эксплуатационные ограничения](../../pilot/messenger/README.ru.md).

## Проверки

- Конкурирующие12 insert из8 потоков при лимите4 сообщения/2048 bytes: приняты
  ровно4, duplicate не занимает места, повторное открытие сохраняет квоты/данные.
- Per-sender quota оставляет место другому участнику; expiry освобождает записи.
- Посторонняя identity/неизвестный получатель отклонены до записи; recipient не
  может читать или удалять чужие записи; flood известной identity ограничивается.
- Искусственный SQLITE_FULL не выдаёт успешный put и не сохраняет неполную запись.
- Реальный закрытый RNS стенд: неизвестный отправитель и native packet/resource
  не попали в spool; разрешённый отправитель принят, повтор не увеличил очередь;
  превышение квоты возвращает full/queued. После перезапуска узла и отправителя
  повтор того же сообщения остаётся duplicate, offline-получатель забирает его,
  очистка возвращает квоту и следующая queued отправка проходит.
- Отдельный контейнер без сети, disposable ext4-файл16MiB: настоящий ENOSPC,
  отсутствие ложного ACK, старое сообщение сохранилось; после удаления filler
  запись снова проходит, повторное открытие видит2 сообщения. Mount снят в finally,
  контейнер --rm. Это тест квоты, не развёртывание сервера.

Фокусно:26 unit/core passed0.36s; закрытый wire test1 passed5.08s.
Финальный общий прогон `tests clients/desktop/tests messenger/tests`: **521 passed**,
2 прежних deprecation warnings,58.46s. Из них31 проверка мессенджера.
`git diff --check` чистый. Дисковый тест — отдельная container acceptance, не pytest.

## Открытые шаги и сохранение

Перед Amsterdam: постоянный ограниченный том под все RNS/spool файлы, отдельная
OS identity/service, fail-closed mount dependency, защита памяти/числа задач,
постоянная node identity и bootstrap, малый живой resource test. Прикладные пределы
не предотвращают всю стоимость обработки RNS request до callback. Node ещё не
развёрнут. Android Keystore/UI, автоматический sync и прикладной ACK получателя
отправителю остаются отдельными задачами; TCP adverse-network эксперимент сохранён.

Код сохраняется в рабочей ветке с `[skip ci]`, чтобы не упаковывать новые клиенты;
remote CI этого commit не заявляется пройденным. Публичные файлы синхронизируются
с проверкой конфликтов. Runtime rollback не нужен; исходники — отдельным revert,
не reset каталога с существующими правками. Ключи/сообщения тестов только синтетические.
