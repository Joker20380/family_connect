# HA-02 — каноническое хранилище и очередь writers

23 November 2026. **IN_PROGRESS; только HA-02A enrollment slice квалифицирован
на синтетическом стенде.** Это не PostgreSQL production, не репликация и не cutover.
[Общие gates](control-ha.md) · [Результаты](releases/2026-11-23-control-ha.md).

## Реализованная граница HA-02A

`control/friends/access.py` сохраняет один алгоритм проверки подписи, purpose,
identity/WG binding, TTL100s, лимита8 незавершённых challenge, активации и отзыва.
SQL перенесён в семантические операции `EnrollmentTransaction`; SQLite по умолчанию
сохраняет прежний `BEGIN IMMEDIATE` / synchronous FULL и интерфейс `Access(path)`.
Граница оставлена в том же модуле, чтобы замкнутые inventories архивов,
исторические pins и overlay не получили скрытую зависимость от нового файла.

`control/friends/enrollment_postgres.py` реализует **только лабораторный** repository.
Включение явное: `Access(None, enrollment_repository=...)`; environment/HTTP/service
selector не добавлен. Legacy `Access.db()` и `initialize()` в этом режиме отказывают,
а не создают запасной SQLite. Ошибка PostgreSQL не включает локальную запись.

- Только127.0.0.1, отдельные БД/роль `fc_ha_synthetic`, уникальная новая схема с
  version/purpose marker. Не подключать к panel Postgres или продуктовой БД.
- Native PostgreSQL SQL/параметры; нет SQLite proxy или произвольного SQL translator.
- Одна транзакция охватывает проверку/расход invitation, привязку устройства,
  расход challenge и назначение Support ID. Ошибка последнего шага откатывает всё.
- PostgreSQL READ COMMITTED + transaction advisory lock сохраняет текущую
  сериализацию SQLite между независимыми соединениями, включая ещё отсутствующие
  строки. Коллизия Support ID не оставляет транзакцию aborted.
- Этот lock **не distributed fencing** и не защищает writers, ещё не переведённые
  на repository. Глобальная сериализация не обещает масштабирование throughput.
- Local synchronous_commit=on, fsync/full_page_writes=on. Это durable commit
  **одного** экземпляра, не RPO0 при потере хоста; remote ACK пока отсутствует.
- Lock timeout3s / statement timeout5s / connect timeout3s только для стенда.
  Это не сквозной production deadline и не замена действующих8/12/120s.
- Потеря ответа после commit не разрешает повторно использовать proof: получить
  новый status proof, проверить регистрацию, затем новый proof для конфигурации.

## Карта оставшихся canonical writers

Это source-level карта семейств, не утверждение о завершённой live-инвентаризации.
Перед cutover необходимо закрыть каждый прямой SQL/file writer, включая операторские
CLI и периодические задания; число таблиц production не выводится из тестовой схемы.

| Семейство / источник | Инварианты переноса | Статус |
| --- | --- | --- |
| `access.py`: invites/devices/challenges, регистрационный Support ID | One-use, binding uniqueness, limit8, TTL, monotonic revoke, rollback | HA-02A synthetic PASS; production SQLite |
| `paid_beta.py`, `transport_membership.py`, paid CLI | Immutable ledger, payload-bound event ID, cohort/binding triggers, terminal revoke, exact paid/noncohort projection | NEXT; native transaction/trigger parity ещё нет |
| `subscription.py` | Собственное атомарное потребление challenge вместе с paid projection, не только `Access.complete` | Pending |
| `support_ids.py`, `support_admin.py`, `support.py` | Backfill/observation/audit; admission-file + grant + audit consistency; support sender bindings | Pending; новая DDL audit не означает перенос writer |
| `referrals.py` | Request idempotency, pool/daily limits, referral claim + invitation в одной транзакции | Pending; тоже пишет invites вне Access |
| `chat.py`, `chat_service.py`, `chat_sync.py` | Chat identity/proof, directory sequence, service sender revoke; filesystem exports | Pending |
| `restricted.py`, `restricted_admin.py`, `readiness_receipts.py` | Grants, отдельные restricted challenges, certificates, readiness, CRL sequence | Pending |
| `restricted_maintenance.py`, `restricted_sync.py`, `paid_canary_crl.py` | HMAC journal, local flock, signed directory/CRL, publication/receipt ordering | Pending; требует также HA-03 fencing |
| `gateway_routing.py`, `gateway_selection.py` | Assignment versions, operation IDs, append-only events, atomic projections | Pending |
| `technical_metadata.py`, `geoip.py` | Отдельная SQLite, consent epoch/sequence/digest, revoke tombstone, retention, no resurrection | Pending; не входит в access registry |
| `diagnostics.py` | Отдельное хранилище snapshots, ограничения данных/retention | Pending |
| `notices.py` → `scripts/service_notices.py` | Отдельная notices БД, publisher roles/revisions и exports | Pending |
| `profile_store.py`, `pseudonyms.py`, generated membership/catalog files | Atomic file replace/fsync, local locks, authority versus derived copies | Pending; не копировать локальные locks как global fencing |

`transport_gateway.py` содержит node-local cache/receipt state: это не новый master
канонической БД. Panel Django/Postgres — read-side projection, не authority. Root/release
signing keys не входят в migration и остаются офлайн.

## Следующие gates

1. Перевести paid ledger и subscription challenge с теми же событиями/решениями и
   триггерами, затем остальные строки карты. Не допускать mixed backend writers.
2. Создать явную versioned all-table migration: snapshot consistency, nullable и
   INTEGER/TEXT/BLOB типы, sequence reseed, FK/unique/check/trigger parity. Сравнить
   все строки/три paid projections без вывода персональных данных. Не считать
   произвольный перенос SQLite DDL полноценной миграцией PostgreSQL.
3. Отдельный PostgreSQL/Patroni + etcd стенд: synchronous replication, strict
   no-quorum refusal, primary loss, повторное включение старого primary, RPO0 на
   подтверждённых payment/revoke/challenge/tombstone, bounded ACK-loss recovery.
4. Непустой полный backup/isolated restore. Нынешний restore пяти **enrollment**
   таблиц — только regression primitive, не backup всей системы.
5. После HA-03/04 — production preflight/shadow/sole-writer cutover по HA-05.

Откат текущего checkpoint: остановить только disposable стенд. Рабочие RU/NL,
registry, metadata, ключи и клиентские версии не менялись; восстанавливать их из
старого backup нельзя и не требуется.
