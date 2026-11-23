# HA-02 — каноническое хранилище и очередь writers

23 November 2026. **IN_PROGRESS; HA-02A enrollment и HA-02B paid/subscription slices
квалифицированы на синтетическом стенде.** Это не production, не репликация и не cutover.
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

## Реализованная граница HA-02B

- `PaidTransaction` в существующем `paid_beta.py` сохраняет один алгоритм проверки
  платежей, release/APK policy, payload-bound event ID, exclusive expiry/grace и
  terminal revoke. SQLite по умолчанию и существующие закрытые архивы сохранены.
- Native PostgreSQL adapter `paid_postgres.py` работает только в disposable
  HA-02A store с дополнительным purpose marker `no-transports` и native CHECK/FK.
  Immutable event/update/delete/truncate guards, cohort10 и binding/revoke triggers
  проверены, включая конкурентные вставки без repository lock.
- Это **не перенос transport-membership**: SQLite по-прежнему вызывает подготовку
  всех nodes перед первым payment. Стенд явно не имеет транспортов/конфигурации и
  проверяет только БД; его marker/метод нельзя использовать как production ACK.
  CLI, service/HTTP selector, production DSN и автоматический импорт не добавлены.
- `subscription.request` проверяет и расходует challenge в той же транзакции, что
  и paid projection. Savepoint сохраняет прежнее правило: ошибка чтения/схемы
  даёт отказ, но расходует валидный proof. Ошибка commit/connection не доказывает
  расход proof; ACK-loss требует нового proof/идемпотентного event ID, не fail-open.
- Три транспортные проекции используют ту же семантическую границу; wire shape,
  noncohort и пределы8/12/120s не изменены. Lease не продлевается ради HA.
- 89 контрактов enrollment+paid/subscription проходят с реальным PostgreSQL, без
  skips. Ledger и все три node projections совпадают с SQLite.366 regression/
  runner checks PASS,20 optional nginx/sync/Go gates не запускались.

### Проверенный recovery, не обещание безусловного отката

В disposable стенде сделан backup **до** платежей; после него подтверждены payment,
grace, revoke и расход subscription proof. SIGKILL/restart сохраняет все эти записи
и удаляет незавершённую вставку ledger. Старая копия восстанавливается только во
второй disposable БД и **отвергается** сравнением с текущим состоянием: она потеряла
бы подтверждённые события/отзыв. Это не команда восстановления production.

Актуальная копия восстанавливается в ещё одном свежем контейнере. Проверены все
девять таблиц именно лабораторной схемы, повтор payment без новой записи, запрет
повторного proof, terminal revoke, защитные триггеры и audit sequence. Credentials,
dump и строки остаются вне Git; receipt содержит только результаты/числа.

**До cutover:** остановить только стенд/shadow; рабочая БД не менялась и не требует
restore. **После новых записей:** fence всех writers, сохранить текущее состояние,
подтвердить полноту acknowledged ledger/revokes/challenges/tombstones и использовать
forward recovery либо отдельно квалифицированный reverse import. Простая замена
старым SQLite запрещена. Ни production reverse import, ни потеря хоста/RPO0, ни
полный backup metadata/files/CRL этим checkpoint не квалифицированы; это блокеры
cutover, а не необязательная доработка после переключения.

## Карта оставшихся canonical writers

Это source-level карта семейств, не утверждение о завершённой live-инвентаризации.
Перед cutover необходимо закрыть каждый прямой SQL/file writer, включая операторские
CLI и периодические задания; число таблиц production не выводится из тестовой схемы.

| Семейство / источник | Инварианты переноса | Статус |
| --- | --- | --- |
| `access.py`: invites/devices/challenges, регистрационный Support ID | One-use, binding uniqueness, limit8, TTL, monotonic revoke, rollback | HA-02A synthetic PASS; production SQLite |
| `paid_beta.py`, `transport_membership.py`, paid CLI | Immutable ledger, payload-bound event ID, cohort/binding triggers, terminal revoke, exact paid/noncohort projection | HA-02B DB contracts synthetic PASS; transport preparation и CLI/wiring pending |
| `subscription.py` | Собственное атомарное потребление challenge вместе с paid projection, не только `Access.complete` | HA-02B synthetic PASS; production остаётся SQLite |
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

1. Перевести transport-membership preparation с теми же fail-closed гарантиями,
   остальные writers/CLI и строки карты. Не допускать mixed backend writers;
   лабораторные paid/subscription contracts не заменяют этот gate.
2. Создать явную versioned all-table migration: snapshot consistency, nullable и
   INTEGER/TEXT/BLOB типы, sequence reseed, FK/unique/check/trigger parity. Сравнить
   все строки/три paid projections без вывода персональных данных. Не считать
   произвольный перенос SQLite DDL полноценной миграцией PostgreSQL.
3. Отдельный PostgreSQL/Patroni + etcd стенд: synchronous replication, strict
   no-quorum refusal, primary loss, повторное включение старого primary, RPO0 на
   подтверждённых payment/revoke/challenge/tombstone, bounded ACK-loss recovery.
4. Непустой полный backup/isolated restore и current-state recovery. Нынешний
   restore девяти **лабораторных** таблиц — не backup всей системы; reverse import
   после новых записей не реализован. Старая pre-cutover копия не подходит.
5. После HA-03/04 — production preflight/shadow/sole-writer cutover по HA-05.

Откат текущего checkpoint: остановить только disposable стенд. Рабочие RU/NL,
registry, metadata, ключи и клиентские версии не менялись; восстанавливать их из
старого backup нельзя и не требуется.
