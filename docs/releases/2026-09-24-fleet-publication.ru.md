# 24.09.2026 —5.2: offline signed publication

Готовы локальные атомарная offline-выдача и получение ciphertext без signing key:
только ready/live lease с актуальным доступом. Используется прежний control-config
schema2/offline Ed25519 anchor; нового wire protocol/root нет.269 tests passed in5.04s.
[Контракт, ограничения и миграция](../fleet-publication.ru.md).

## Изменения и проверки

- `control/fleet_publish.py`: доверенный offline issuer, сериализация с revoke,
  pin authority/profile, idempotent ciphertext, per-device revisions и time recheck.
- `provisioning/fleet.py`: проверенные операторские pins DNS/MTU/server public key/AWG.
- `control/fleet_store.py`: schema3, явный upgrade1/2→3, public authority, counters,
  публикации и отдельное чтение без signing key с проверкой текущего доступа.
- `tests/test_fleet_publish.py`:18 новых проверок; migration fixture предыдущего
  service test обновлена под полный состав старой схемы1.

Проверены отказ до ready, exact bytes после reopen, совместимость WG/AWG2 с текущим
ConfigVerifier, concurrent issuance, revoke/expiry/retire/чужой device, смена access
revision без продления lease, подмена signer/policy/previous hash/min client version,
rollback при signer error/expiry, конкурирующий revoke, keyless read, schema2 migration.
Managed AWG3.1 по-прежнему отвергается существующим протоколом, остаётся5.3.
Во время разработки тест отказа AWG3.1 был исправлен: Pydantic оборачивает
ConfigError в ValidationError; итоговый тест проверяет ValueError и точную категорию.

```sh
/tmp/fc-desktop-current-venv/bin/python -m pytest -q \
  tests/test_fleet_publish.py tests/test_fleet_services.py tests/test_fleet_adapters.py \
  tests/test_fleet_gateway.py tests/test_fleet_store.py tests/test_fleet.py \
  tests/test_friends_identity_store.py tests/test_friends_store.py tests/test_friends_owner.py \
  tests/test_device_identity.py tests/test_friends_access.py tests/test_control_vectors.py
```

269 passed =201 предыдущих +18 publication +50 существующего control corpus.
Pytest9.1.1, pydantic2.13.5, rns1.5.1, cryptography46.0.7.
[Команда, результаты и SHA256](2026-09-24-fleet-publication.json).
Native WG/AWG+SSH в этом шаге не повторялись: gateway/SSH backend не менялся.
Новая цепочка не проверялась на установленном клиенте или действующем relay.

## Граница готовности

5.2 остаётся открыт: следующий результат — verified ACK/previous-hash и перенос
подписанного результата offline→online с повторной сверкой lease/access, затем
привязка действующего Friends доступа и доставка через relay. Автоматический online
signer не добавлен, offline key на сервер не переносился. Runtime published() уже
не требует ключа, но внешний proof-gated endpoint ещё не подключён.

До production нужны импорт прежних sequence/floors и IP, единственный источник
доступа/выдач, сопоставление profile pins с gateway, TTL, TCP, supervisor/recovery.
Нельзя считать атомарность одной локальной DB гарантией переноса между двумя DB.
Уже доставленный конверт остаётся криптографически действительным до expiry;
revoke требует очистки peer, а не только блокировки повторной выдачи.

Рабочие RU/NL и их DB не изменялись. Signing выполнялся исключительно тестовыми
ключами, offline release key не читался. Без commit/push/CI/production rollout.
Android0.1.18-beta50/code50, Linux0.2.10, Windows0.2.13, публичные/установленные
артефакты, каталоги и страница приглашения прежние. Серверный откат не требуется;
схема3 обратно не мигрируется, старую DB нельзя возвращать поверх изменённых peers.
Этап6 и единая Django-админка7.1 остаются в прежнем порядке после5.
