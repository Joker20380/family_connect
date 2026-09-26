# Fleet5.2: атомарная offline-подпись и выдача ciphertext

Checkpoint24.09.2026:269 тестов passed, production rollout отсутствует.
[Отчёт](releases/2026-09-24-fleet-publication.ru.md).

## Формат и граница ключа

`FleetPublisher` использует существующие `ControlConfiguration/schema2`,
`TransportProfile`, `issue_config` и domain `family-connect/control-config/v1`.
Новый формат конверта, signing root или TOFU не вводятся. Подписание — только
локальный offline-процесс с доверенным Ed25519 signing_key; online worker/relay
не импортируют publisher и не получают ключ. В тестах используются новые
случайные тестовые ключи, рабочий offline key не читался.

Это библиотечный контракт для контролируемой offline-выдачи. Безопасный перенос
запроса на offline-машину и подписанного результата назад с повторной сверкой
authoritative online state ещё не реализован. Нельзя просто скопировать DB,
подписать её и считать обновление рабочей DB атомарным: гарантии ниже относятся
к одной базе и процессам, использующим её транзакции.

## Подготовка и подписание

Доверенный оператор задаёт `ProfileBinding` для gateway_id/transport/version:
серверный публичный ключ, DNS, MTU и строго проверенные AWG параметры.
Endpoint/порт и адрес устройства берутся из сохранённых registry/lease, а не из
запроса клиента. Pins должны совпасть с установленным gateway agent/engine;
автоматического сопоставления server key и AWG параметров с receipt пока нет.
При несовпадении настроек подпись сама по себе не гарантирует рабочий VPN.

`pin_publication_authority(base64_ed25519_public)` явно закрепляет public anchor
в DB. Первый вызов — доверенная операция администратора; повтор с тем же ключом
идемпотентен, смена ключа запрещена без отдельной миграции. Доставка anchor клиентам
остаётся существующей доверенной процедурой, запись в DB не меняет клиентский anchor.

`publish(lease_id, device=..., previous_config_hash=..., min_client_version=...)`:

1. Под одной SQLite/POSIX-блокировкой проверяет текущий grant, владельца lease,
   состояние ready, срок и закреплённый signing anchor.
2. Проверяет policy: immutable server/profile pins и minimum client version.
   Повтор пары lease/access revision возвращает те же сохранённые bytes;
   попытка изменить previous hash или policy такого результата отклоняется.
3. Для новой access revision выделяет следующий per-device revision. Адрес и
   срок lease не продлеваются: expires=min(lease expiry, access expiry).
4. Создаёт профиль с `PrivateKey = LOCAL_DEVICE_KEY`, full IPv4/IPv6 routes,
   выбранными DNS/MTU/endpoint. Private device key на сервер не передаётся.
5. Адресно шифрует существующей RNS identity устройства и подписывает существующим
   offline Ed25519 anchor через `issue_config`.
6. Повторно проверяет время после подписания. Истёкший результат, откат часов или
   длительность более5с откатывают транзакцию. Проверка времени не прерывает
   зависший signer: поддержан только локальный доверенный signer, не remote HSM.
7. В одной транзакции сохраняет ciphertext, revision/counter, access revision,
   signer, policy digest, previous hash и event. Возвращает bytes после commit.

Сбой шифрования/подписания/commit не публикует результат и не расходует revision.
Параллельные издатели получают один ciphertext, хотя шифрование рандомизировано.
Изменение access revision требует новой подписи; повтор не продлевает lease.

`previous_config_hash` должен происходить из подтверждённого клиентского committed
состояния. Publisher принимает его как доверенный вход, сам ACK не проверяет.
None допустим только для подтверждённого первого применения. Подключение к
проверенным ACK/relay и импорт прежних sequence/floors ещё обязательны перед rollout.
Новый счётчик начинается с1: нельзя включать его поверх прежнего issuer без импорта
его истории. Подмена этого условия произвольным клиентским параметром недопустима.

## Выдача без ключа и revoke

`FleetStore.published(lease_id, device=...)` не принимает signer и возвращает
сохранённый ciphertext только при текущем grant, ready/live lease, совпадении
владельца, access revision и закреплённого signer. Отзыв/expiry/retiring запрещают
даже выдачу ранее сохранённого конверта. Это внутренний API: перед передачей device
внешний обработчик должен аутентифицировать устройство. HTTP/RNS endpoint в этом
checkpoint не добавлен.

Revoke и подписание сериализованы одной DB-блокировкой. Если revoke пришёл первым,
подписи не будет. Если подпись закоммичена раньше revoke, bytes уже могут оказаться
у клиента: криптографически отозвать их задним числом нельзя. Revoke запрещает
последующую выдачу и создаёт retiring, удаление peer выполняет scheduler.
Autonomous gateway TTL при потере контроллера остаётся отдельной незакрытой задачей.

Клиент использует существующий ConfigVerifier и transaction journal: проверка
подписи/identity/WG binding/lease/min-version, затем revision/previous hash/floor
и применение с rollback/ACK. Один ConfigVerifier не защищает от повторного apply;
постоянный journal обязателен. Весь существующий corpus продолжает проходить.

## Поддержанные транспорты

WG1 и AWG2.0 выдаются и проверены текущим клиентским verifier. С checkpoint5.3а
schema/issuer также поддерживают AWG3.1 со всеми обязательными параметрами защиты.
Python verifier принимает его только при явном `supports_awg31=True`; по умолчанию
сохраняет UNSUPPORTED_TRANSPORT_VERSION. Native managed клиенты ещё не включены.

Java/C# verifier теперь также имеют явный opt-in и проходят общий corpus с Python;
рабочие callers оставлены выключенными до application acceptance.
[Checkpoint совместимости](releases/2026-09-24-managed-awg31-native-verifiers.ru.md).
[Проверки/границы](releases/2026-09-24-managed-awg31.ru.md). Успешная native-проверка
VPN engine не заменяет managed application acceptance. TCP fleet issuance пока отсутствует.

## Схема3 и переход

Новый initialize создаёт fleet schema3. `upgrade_services()` явно обновляет1 или2
до3, транзакционно и идемпотентно, при остановленных writers. Для1 создаются также
challenges/jobs. Сохраняются все leases/requests/events; gateway journal прежний.
Добавлены:

| Таблица | Данные |
| --- | --- |
| publication_authority | Явно установленный публичный Ed25519 anchor |
| publication_counters | Последний выданный configuration revision устройства |
| publications | lease/access revision, revision, signer, policy digest, previous hash, encrypted envelope |

Обычное открытие старой схемы отвергается; автоматического downgrade нет.
Перед будущей миграцией нужна приватная согласованная резервная копия, остановка
writers и проверка версии/leases после upgrade. Public anchor устанавливается явно.
Не снижать номер схемы вручную и не возвращать старую DB поверх живых peers.
В production эта миграция не выполнялась; серверный откат не требуется.
