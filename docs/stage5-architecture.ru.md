# Stage 5 — Reticulum control channel

Inspection baseline: `4cb1423`, 2026-09-12. Реализация — reference Python/Linux
protocol/application layer; native Windows/Android packaging не заявляется.

## Что переиспользовано

- `provisioning/envelope.py`: размер envelope, отказ duplicate JSON keys, адресное
  шифрование существующей device identity. Формат не содержит RNS Link/destination.
- `clients/desktop/updates.py`, `scripts/sign_update.py`: существующий offline
  Ed25519 anchor и правила version. Новый purpose-separated domain использует тот
  же signing root; каталог приложений и его sequence 8 не меняются.
- `clients/desktop/profile_config.py`: строгие WG/AWG 2.0/TCP парсеры без hooks.
- `clients/desktop/backend.py`: LinuxTCP import/connect/disconnect/healthy, включая
  существующие транспортные реализации. В control core нет engine/routes/DNS кода.
- `provisioning/cache.py`: приватный каталог, flock, проверка файлов, атомарный
  replace/fsync. Новый journal использует отдельный каталог и запись `cache.json`;
  существующий provisioning cache/schema 1/product DB остаются совместимыми.

## Контракт

`configuration.py`: schema 2, `config_id`, `revision` (configuration sequence),
issued/expires, recipient, audience, привязка WG public key, min client version,
previous committed envelope SHA256, signer key id, gateways и transport profiles.
WG private key задаётся исключительно `LOCAL_DEVICE_KEY`; реальное значение
подставляет локальный application adapter. TCP credentials находятся только внутри
адресно зашифрованного ciphertext. Signature покрывает domain и ciphertext;
signer key id проверяется после расшифровки относительно доверенного anchor.

Root остаётся существующим Ed25519 offline key. RNS transport identity — адрес
носителя, не новый signing root. Relay получает public device binding и готовые
ciphertexts; не имеет private signing key и не может выпустить конфигурацию.
Relay metadata sequence не является authority: клиент проверяет подписанный revision.

Envelope и ACK независимы от carrier. `ReticulumAdapter.receive/send_ack` и
`TestAdapter` реализуют один узкий интерфейс. Смена carrier не меняет signature,
configuration format, verifier, journal или application logic. Legacy HTTP provider
сохраняется без изменения; schema 2 доставляется новым control endpoint.

## AWG 3.1

Пользователь подтвердил: продолжать Stage 5 с учётом AWG 3.1; миграция отдельная.
У профиля обязательны `transport` и `transport_version`. Текущая capability:
WG 1, AWG 2.0, VLESS REALITY 1. AWG 3.1 распознаётся и **отклоняется до stage**
с `UNSUPPORTED_TRANSPORT_VERSION`: его параметры не выкидываются и не трактуются
как 2.0. Это не поддержка runtime 3.1. Добавление pinned runtime/parser и scoped
native/Auto acceptance остаётся TD-2. Основной envelope/carrier при этом не меняется.
См. [официальное описание 3.1](https://docs.amnezia.org/documentation/amnezia-wg/).

## State machine

```text
IDLE → verify/revision/previous hash → STAGED → APPLYING → APPLIED_PENDING
                                                         │           │
                                                       health OK    failure
                                                         │           │
                                                commit + ACK      ROLLING_BACK
                                                atomic write         │
                                                         │       restore + ACK
                                                        IDLE ←───────┘
```

`committed` и `staged` хранят ciphertext/hash/time. Commit дополнительно хранит
`applied_at` и runtime inventory. `baseline` фиксируется до системных изменений.
`floor` сохраняет максимальный принятый revision, в том числе после failed apply;
`result` хранит подписанный последний результат, `outbox` — подписанные ACK.
Last-known-good не заменяется до health success. Previous hash ссылается на
committed, а не на последний неуспешный staged envelope.

Восстановление любого staged/applying/pending состояния идёт через rollback.
Никогда не выводим успешный health из наличия живого процесса после crash.
Commit и COMMITTED ACK сохраняются одной записью. Повтор точных уже committed
байтов не вызывает apply, повтор failed envelope возвращает сохранённый результат;
другие байты с тем же/меньшим revision отвергаются. Expiry проверяется и на повторе.
Истёкший last-known-good сохраняется как evidence/floor, но не переподключается.

Rollback failure сохраняет ROLLING_BACK и требует повторной очистки до следующего
apply. Повторяющиеся failure ACK не заполняют outbox; backpressure проверяется до
stage. Relay делает INSERT OR IGNORE по подписанному ack_id. Потеря ответа после
server receipt безопасна: durable outbox отправляет те же байты повторно.

## Application boundary и ограничения

`BackendApplication` использует действующий LinuxTCP backend. Перед импортом
сохраняется inventory известных и активных профилей. Импорт не активирует профиль;
поэтому crash до получения нового ID восстанавливается через inventory delta.
После crash кандидат отключается и восстанавливается previous active profile.
Неактивные импортированные профили пока сохраняются; garbage collection не добавлена.

**Linux GUI и reference runner одной новой версии используют общий arbiter** в
`~/.local/state/family-connect-operations`. Nonblocking flock + reentrant thread
exclusion защищают всю транзакцию snapshot/apply/health/commit/rollback; pending owner
записывается атомарно до stage/system changes. После crash обычные GUI mutations
запрещены до recovery тем же journal owner. Повреждение/потеря state fail closed.
Generation меняется при control stage/finish и ручных GUI mutations. GUI обновляет
inventory/selection и отвергает stale recovery; собственное automatic recovery не
сбрасывает generation/finite retry budget. Сеть/ACK не держат connection lock.

Это не блокировка сторонних NetworkManager/root команд. Старый установленный GUI
0.2.8 (проверено13.09) и прежние binaries не участвуют: до согласованного обновления старый GUI должен
быть закрыт. Новые GUI/core могут работать одновременно. Native Windows/Android
и autonomous background scheduling остаются отдельно.

RNS запускается независимо от data plane с явным operator config. Нет требования
работающего HTTP API/VPN для fetch. Сбой carrier не трогает VPN; runtime сначала
восстанавливает локальный pending apply, даже если RNS недоступен. Один запуск
`once` выполняет конечный обмен; постоянный polling/scheduler не добавлен.

Доверяются UTC clock, локальному owner/root и offline bootstrap anchor. Atomic
storage защищает от interrupted writes, но не от восстановления всего каталога из
старого backup владельцем/root; hardware monotonic counter отсутствует. Relay не
может подделать конфигурацию, но может отказать в доставке/ACK. Нет TOFU, recovery
root rotation или emergency sequence downgrade. Endpoint RNS ограничен на уровне
application message; deployment также должен ограничить ресурсы RNS/частоту links.

Windows DPAPI/broker и Android Keystore/VpnService не изменены. Портирование journal
и application boundary, совместная упаковка новых GUI/core, background lifecycle, безопасная очистка временных
профилей и production relay retention/quotas остаются до широкого выпуска.
Stage 6: независимый control entry/alternate gateway, не проверенные здесь.


Следующий native блок: [карта исходников, контракты и критерии](stage5-native-binding.ru.md).
Native binding ещё не реализован; начинать с interop vectors, затем protected storage/ownership.
