# Stage 5: следующий блок native binding

Статус13.09.2026: общий corpus и Python runner реализованы; native verifier следующий.
[Первый implementation checkpoint](releases/2026-09-13-control-vectors.ru.md).
Native Stage5 ещё не реализован; успешные native WG/AWG/TCP/Auto тесты относятся
к data plane. Linux протокол и живой paired pilot приняты отдельно.

## Обнаруженные точки интеграции

| Область | Windows | Android |
|---|---|---|
| Владелец операций | Broker.Handle, pipe caller SID; AutoSession/TcpSession имеют собственный lifecycle | ConnectionService single-thread worker, generation/cancellation; VpnService lifecycle |
| Защищённые профили | Store, ACL root и DPAPI под LocalSystem; разделение по SID | ProfileStore, AndroidKeyStore AES-GCM, AtomicFile в noBackupFilesDir |
| Ручные изменения | Broker activate/connect/disconnect actions | MainActivity import/save/clear и ConnectionService |
| Текущая identity | Store.Key/Public создаёт WG X25519 key; activation grant иной purpose | Импортированный профиль; encrypted profile store не является Stage5 device identity |
| Недостающий контракт | RNS identity, schema2 verification, durable journal/outbox, общая operation ownership | Те же элементы плюс координация Activity/service и восстановление после process death |

Исходники: `clients/windows/Broker.cs`, `Store.cs`, `Wire.cs`, `AutoSession.cs`,
`Core/Activation.cs`; Android `ConnectionService.java`, `ProfileStore.java`,
`MainActivity.java`, `TcpVpnService.java` в app/src/main/java/com/familyconnect/app.

## Порядок реализации и критерии

1. Сначала совместимость протокола без VPN/сервера: общие проверочные векторы из
   Python reference для signed encrypted schema2 и device-signed ACK. Только
   одноразовые fixture identities/keys, явно не production. Набор включает подпись,
   адресата/WG binding, purpose domain, duplicate JSON keys, canonical encoding,
   size bounds, lease/version/AWG3.1 refusal, revision/previous-hash и ACK idempotency.
   Native verifier должен подтвердить одинаковый результат для тех же bytes;
   существующие activation envelopes не переименовывать в Stage5 configurations.
2. Windows: защищённая постоянная RNS identity и journal по SID в broker storage,
   восстановление до принятия новых mutation requests. Общий durable owner должен
   охватывать ручные actions и Auto/TcpSession callbacks, а не только pipe handler.
   Проверки чужого SID, corrupted/pending journal, SCM restart, commit/rollback/ACK.
3. Android: отдельные identity/journal/outbox под OS-protected storage, AtomicFile
   и явный recovery до новых операций. MainActivity import/clear обязаны использовать
   ту же ownership, что service. Учитывать existing stop/destroy barrier, revoke,
   cancellation и process death; не создавать второй параллельный VPN lifecycle.
4. После verifier/storage/arbiter — native application adapters поверх существующих
   транспортов. Commit требует traffic health, а не живого процесса/active интерфейса.
   Проверить snapshot→apply→health→commit и crash→rollback, неизменность floor,
   outbox retry, отсутствие повторного apply и cleanup. Linux bound HTTPS проверка
   не переносится механически: использовать native network-bound API платформы.
5. Только после этого подключать RNS carrier и background lifecycle, собирать
   согласованные GUI/core artifacts и проходить scoped native runtime CI.
   Carrier не получает signing secret и не принимает decisions вместо verifier.

## Решения, которые нельзя пропустить при реализации

- Windows Wire сейчас ограничен16384 bytes/35s; schema2 envelope до65536 bytes.
  Нужен отдельный bounded contract или broker-owned ingestion, с точным лимитом
  целого запроса, защитой SID и отменой. Не увеличивать все legacy pipe limits
  молча и не передавать произвольный privileged filesystem path от GUI.
- Android ProfileValidator.LIMIT16384 — лимит отдельного профиля, не encrypted
  envelope. Хранение journal/outbox не должно ломать этот legacy profile bound.
- RNS identity и WG key — разные сущности. Нужны explicit registration/binding и
  persistence; существующий WG public key не доказывает наличие RNS identity.
- Same signed revision/hash нельзя принимать после частичного apply как новый
  конфиг. Pending marker/journal очищается только после завершённого recovery.
- Сеть и отправка ACK не должны удерживать application mutation lock. Ошибка
  carrier не должна отключать рабочий VPN. Отдельно тестировать восстановление
  без carrier и сохранение неподтверждённых ACK.

Это план реализации, не новая готовая API/schema и не обещание поддержки native
RNS библиотек. Выбор совместимой реализации carrier/crypto требует отдельной
проверки после interop vectors. Independent relay/gateway Stage6, AWG3.1 runtime,
root rotation и отложенные реальные device/load проверки остаются отдельными.

## Первый implementation commit: interop vectors

Проверочные bytes должны быть независимы от native runtime и от текущего времени.
Предлагаемый manifest: vector_id, purpose, input_file/SHA256, fixture identity/anchor,
now, client_version, initial_floor/previous_hash, expected_category/status и
expected_effects. Это формат тестовых ресурсов, не изменение wire protocol.
Для encrypted fixtures использовать только явно тестовые ключи, сгенерированные
специально для набора; запретить generator доступ к рабочему signing path.
Случайная ciphertext при генерации нормальна: зафиксированные input bytes и digest
должны оставаться неизменными при проверке Python/.NET/Java.

| Набор | Обязательный результат | Python reference |
|---|---|---|
| Valid WG/AWG2/TCP config | те же decoded fields, envelope SHA256 и gateway binding | test_offline_issue_and_full_lifecycle, test_existing_awg2_tcp_profile_parsers_reused |
| Tamper/unknown signer | SIGNATURE до применения | test_verification_fail_closed |
| Wrong target/WG key/audience | TARGET, без mutation | test_verification_fail_closed |
| Bool schema, malformed/oversize, expiry/future/client version | точная category reference; границы включения времени | test_verification_fail_closed |
| AWG3.1 | UNSUPPORTED_TRANSPORT_VERSION, не интерпретация как2.0 | test_verification_fail_closed |
| Same bytes / same revision different bytes / previous hash mismatch | idempotent result / REPLAY / PREVIOUS_HASH, correct floor | test_replay_duplicates_previous_hash_and_bad_high_sequence |
| ACK body/hash/signature | тот же ack_id и canonical signed bytes; reject forged/duplicate JSON | provisioning/ack.py, test_relay_replay_revoke_and_forged_ack |
| Pending/outbox restart | состояние и эффекты совпадают, повтор без apply | test_crash_restart_is_deterministic, test_ack_retry_duplicate_and_carrier_failure_preserve_vpn |

ACK имеет собственный domain family-connect/control-ack/v1 с NUL, limit4096,
строго заданные поля, статусы и категории. ack_id — SHA256 canonical body до
добавления ack_id; device signature покрывает domain + canonical body уже с ack_id.
Это порядок из provisioning/ack.py, его нужно сохранить в обоих native портах.
Envelope hash считается от исходных wire bytes, не повторной JSON сериализации.

Критерий завершения первого commit: генератор/manifest и Python reference verifier
проверены; каждый новый native verifier использует те же fixtures. Генератор сам
по себе ещё не означает native acceptance. На этом этапе не подключать VPN,
не выдавать production identity, не менять схемы установленного profile store.
