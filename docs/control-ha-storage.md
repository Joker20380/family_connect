# HA-02 — каноническое хранилище и очередь writers

23 November 2026. **IN_PROGRESS; HA-02A enrollment, HA-02B paid/subscription и
HA-02C membership, HA-02D referral, HA-02E Support ID и HA-02F grant/audit contracts
квалифицированы на синтетическом стенде.**
Это не production, не репликация и не cutover.
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
- Режим HA-02B **не переносит transport-membership**: SQLite по-прежнему вызывает подготовку
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

## HA-02C — подготовка transport membership

`transport_membership.prepare_nodes` — общий протокол для прежнего SQLite wrapper
и явного PostgreSQL test exchange: подготовить конкретный device/binding/token на
**всех трёх** serving nodes до первого canonical payment. SQLite сохраняет private
command map, прежний subprocess timeout12s и проверяет все команды до первого
контакта. ACK ограничен1024 bytes, строгим UTF-8/JSON, целочисленным schema1,
точными node/token/result/полями; duplicate keys и bool/float schema отвергаются.

Новая disposable схема `version2 / membership-required` требует явный injected
exchange. Нет environment/HTTP/CLI selector, production DSN или SSH-конфигурации
для PostgreSQL. Старая v1 `no-transports` остаётся отдельным HA-02B режимом;
попытка настроить exchange для первого платежа в v1 отклоняется. В v2 отсутствующий
exchange не превращается в успешную no-op подготовку, в том числе после pg_restore.

131 контракт с реальным PostgreSQL и SQLite PASS /0 skips.42 membership cases
включают стенд из трёх настоящих `Gateway` instance с отдельными файлами cache, locks,
atomic writes/fsync и повторным чтением с диска; **AWG/TCP/systemctl и сеть заменены
тестовыми исполнителями**. Это не три хоста, WAN, реальный kernel readback или SLA.
Проверены потеря ACK на каждом узле, неверный ACK, отсутствие видимого платежа до
всех ACK, конкурентный повтор, DB backend termination после all-ACK/uncommitted
ledger, старый noncohort snapshot, expiry/revoke/restart и PostgreSQL idle timeout.

**Откат БД не является откатом запрета на узле.** При частичной подготовке ledger
остаётся без платежа, уже подготовленный target остаётся denied; остальные
noncohort не закрываются. Нельзя стирать `prepared`/cache, возвращать старый cache
или автоматически продлевать период. Точный повтор event ID/payload завершает
подготовку и commit; только свежая canonical cohort projection открывает доступ.
После commit повтор не обращается к узлам и не добавляет событие. Если период
истёк, требуется новое явно проверенное основание, не автоматический retry renewal.

PG connect3s/lock3s/statement5s/idle-in-transaction5s не расширены. Медленный node ACK
может закрыть лабораторную транзакцию раньше прежних12s сетевого ожидания; проверено,
что это сохраняет запрет и не создаёт payment. WAN scheduling/deadline redesign
не квалифицирован и требует отдельного решения перед production wiring.
8s node operation /12s watchdog /до120s paid lease и offline noncohort не изменены.
Unavailable RU всё ещё блокирует первый cohort переход; исключать его из serving
set ради доступности без HA-03 fencing/quarantine запрещено.

Broader suite:389 PASS /16 optional skips /4 FAIL. Все четыре точных исторических
overlay-packager теста также падают на исходномeeb11ba7 (`UNRELATED_PAID_DELTA`,
`POLICY_CHANGE_FORBIDDEN`): HA-02B уже изменил canonical paid/policy bytes. Pins и
guards оставлены строгими. Это не новый membership regression, но и не release
PASS: новый closed runtime/overlay должен пройти отдельный gate до deployment.

## HA-02D — referral transactions

`referrals.py` теперь выполняет issue/claim через существующую enrollment transaction,
а не через отдельный SQLite-only writer. SQLite остаётся production default;
`referrals_postgres.py` доступен только явно созданному synthetic loopback store
с точным purpose `family-connect/ha-referrals-synthetic/v1`. Инициализация PG не
выбирается автоматически; прежний SQLite initializer на PG по-прежнему запрещён.
Native PG DDL имеет FK на sponsor/device и invitation, unique request/invite/sponsor,
BIGINT timestamp и индекс daily. SQLite on-disk schema не меняется.

- Общий `Access.complete(..., transaction=...)` не открывает/коммитит вложенную БД:
  caller владеет транзакцией. Обычный вызов сохраняет проверку подписи перед открытием
  своей транзакции. Referral issue атомарно потребляет proof, назначает отсутствующий
  Support ID и сохраняет link; ошибка откатывает всё, пока proof ещё действителен.
- Claim атомарно создаёт invitation и request row. Все API используют тот же
  `BEGIN IMMEDIATE`/PG advisory transaction lock, что enrollment/revoke; pool500 и
  daily20 проверяются внутри блокировки, включая точную границу86400s.
- Идемпотентность привязана к исходному sponsor и восстановленному invitation hash.
  Попытка повторить request ID с чужим referral token или несогласованной записью
  отклоняется, а не возвращает чужой код. URL/формат кода и HMAC derivation не меняются.
- Сохраняется существующая политика: отзыв sponsor запрещает новые claims/issue,
  но не отзывает уже выданные независимые child invitations. Отозванная child invite
  не возвращается при replay. Конкурентные claim/revoke имеют последовательный исход.
- При потере ответа после commit повторять тот же token/request ID с тем же
  существующим referral secret. Issue proof после commit одноразовый: нужен новый
  proof, который вернёт прежний link. Не ротировать secret и не создавать новый
  request ID, чтобы «исправить» неопределённый результат.

Реальный стенд:181 contracts (50 referral +131 A/B/C),0 skipped; SIGKILL/restart
PostgreSQL17.11 сохраняет committed state и удаляет обе uncommitted записи.
Current dump восстанавливается в другом контейнере row-for-row (9 таблиц/18 строк);
stale pre-claim dump отклонён. Проверены consumed activation/issue proof,
revocation и активация ещё не использованного приглашения после restore.
Это один synthetic store, не RPO0 replica, не production secret migration,
не all-table product recovery. Support/admin/audit writers и файлы остаются pending.
SQLite semantics выше изменены только в исходниках; accepted production bytes не
заменены. Rollback текущего шага — остановка owned стенда, без восстановления RU/NL.

## HA-02E — Support ID transactions

`support_ids.py` использует общий `SupportTransaction` для request, backfill,
inventory и lookup. PostgreSQL доступен только в явно созданном synthetic store
с marker `family-connect/ha-support-synthetic/v1`; отсутствующий/неверный marker
запрещает все четыре операции без fallback/DDL. SQLite остаётся production default,
его schema и CLI не переключены. Общая реализация включена в существующий операторский
архив без добавления PG driver в runtime или ослабления exact-package pins.

- Request атомарно потребляет support proof и сохраняет platform/app-version/last_seen.
  Ошибка после UPDATE или потеря backend откатывает оба изменения. Отсутствующий
  Support ID не создаётся при выдаче: отдельный backfill, затем retry ещё действительного
  proof. После commit тот же proof отклоняется; свежий proof возвращает тот же alias.
- Backfill выполняется одной транзакцией вместе с возвращаемым inventory. Повторные
  и конкурентные вызовы сохраняют существующие aliases/bindings, включая revoked
  devices. Коллизии retry32 сохранены; исчерпание/сбой посередине откатывает весь batch.
- Receipt не определяет platform и не перезаписывает более новое наблюдение запроса.
  Для одинаковых backend outcomes введены `ack_at DESC NULLS LAST, correlation ASC`;
  JSON не-объект, неверная версия и отсутствующий/отрицательный timestamp не являются
  наблюдением. Невалидный последний ACK не разрешает fallback на старый READY.
- Read-only lookup сохраняет safe response без device identity/ключей, явную FIELD
  list и отдельную существующую all-activated политику. В all-activated expired grant
  остаётся ELIGIBLE по прежнему контракту; revoked — нет. Это не изменение допусков.
- Таблицы restricted grants/readiness в стенде — **read-side fixtures**, не перенос
  их writers. `support_admin.change` на PG отказывает до открытия lock/admission/CRL
  файлов. SQLite FIELD поведение сохранено и проверено прежними операторскими тестами.
  Grant/audit transaction ordering, file publication/reconciliation и sender bindings
  остаются отдельными задачами. Чтение support ID не даёт разрешения на FIELD mutation.

155 real DB contracts /0 skips (66 support +40 enrollment +49 paid);443 consumer/
runner checks /21 optional skips. Дополнительно выполнены backfill/inventory/lookup
из настоящего воспроизводимого `.pyz` через `python -I` на synthetic SQLite.
Реальный PostgreSQL SIGKILL/restart и отдельный restore сравнивают все12 lab tables/
19 rows с заранее сохранённым committed state: ID/version/proof/revoke/paid и audit
sequence. Stale backup отклоняется именно этой сверкой, не новым production recovery
service. Pending proof после restore работает один раз. Это не RPO0/replication,
полный product backup или обратная миграция. Число155 не сумма всех прошлых этапов:
неизменённые membership/referral PG suites в этом шаге заново не запускались.

Никакого нового сбора OS/GeoIP/consent: здесь только прежний Support ID/app-version
контракт. Production данные, ключи, архивы и клиентские версии не менялись. Откат
checkpoint — остановка owned disposable стенда; live DB из старого backup не нужна.

## HA-02F — grant and audit transactions

`RestrictedAdminTransaction` переносит только DB-операции явного grant/renewal,
revoke и audit. SQLite использует эту же реализацию через `Access.enrollment`;
`support_admin.change` сохраняет порядок pending/revoke → CRL/file → audit completion
и компенсирующий revoke при ошибке. Это не атомарность между БД и файлами.

- PostgreSQL требует отдельный marker `family-connect/ha-restricted-admin-synthetic/v1/db-only`.
  Инициализатор создаёт native grant FK/CHECK и marker только в disposable store;
  не импортирует существующие таблицы, не выбирает production DSN/backend/CLI.
- Grant разрешён только активному device с активным invite и ещё будущим expires,
  проверенным внутри сериализованной транзакции. Revision растёт с учётом minimum;
  параллельные renewal не теряются. Неявных retry/новых operation IDs нет.
  **Grant не идемпотентен:** после неизвестного commit прочитать текущую revision,
  а не повторять renewal и лишний раз инвалидировать сертификаты.
- Revoke меняет revision только при переходе active→revoked. Повтор — no-op;
  явный grant может восстановить grant, но не revoked registration. Неверные
  типы/диапазоны expires/minimum revision, пустая family и переполнение BIGINT
  отклоняются одинаково на SQLite/PG, без float/wrap. Device revoke остаётся доступен.
- Audit получает ID от БД и известный Support ID, без device identity/ключей.
  Pending audit и revoke могут быть одной транзакцией. Completion идемпотентен;
  APPLIED→INCOMPLETE разрешён для fail-closed компенсации при потере commit ACK,
  но INCOMPLETE→APPLIED запрещён. Компенсация не откатывается из-за уже записанного
  APPLIED. Неизвестные IDs/outcomes отклоняются.
- Полный PG FIELD operator и `publish_crl` по-прежнему отказывают до файловых I/O.
  PostgreSQL restricted challenges/certificates/readiness и CRL sequence ещё не
  перенесены. Отдельно остаются fencing, file reconciliation, support sender.
  Ни успешный DB audit, ни marker не являются подтверждением выдачи сетевого допуска.

176 real DB contracts /0 skips (70 admin +40 enrollment +66 support),264 focused
regressions /4 optional Go skips. Проверены concurrent renew/revoke, device revoke
race, commit ACK loss, атомарный rollback и реальное отключение PG backend. SQLite
FIELD проверен с реальной CRL/file записью и потерей APPLIED commit ACK.
Отдельный SIGKILL/restart и restore точных12 synthetic таблиц/20 строк сохраняет
grant/device revoke, revision, Support ID/proofs, paid ledger и pending audit;
sequence продолжается, pending audit закрывается только явно. Stale pre-revoke
dump отвергнут сравнением с известным lab snapshot. Это не production watermark,
полный product backup, reverse migration или replicated RPO0.

## Карта оставшихся canonical writers

Это source-level карта семейств, не утверждение о завершённой live-инвентаризации.
Перед cutover необходимо закрыть каждый прямой SQL/file writer, включая операторские
CLI и периодические задания; число таблиц production не выводится из тестовой схемы.

| Семейство / источник | Инварианты переноса | Статус |
| --- | --- | --- |
| `access.py`: invites/devices/challenges, регистрационный Support ID | One-use, binding uniqueness, limit8, TTL, monotonic revoke, rollback | HA-02A synthetic PASS; production SQLite |
| `paid_beta.py`, `transport_membership.py`, paid CLI | Immutable ledger, payload-bound event ID, cohort/binding triggers, terminal revoke, exact paid/noncohort projection | HA-02B/C DB + membership contracts synthetic PASS; production CLI/wiring pending |
| `subscription.py` | Собственное атомарное потребление challenge вместе с paid projection, не только `Access.complete` | HA-02B synthetic PASS; production остаётся SQLite |
| `support_ids.py` | Stable aliases, atomic backfill и proof/observation; safe inventory/lookup | HA-02E synthetic PASS; full import/production wiring pending |
| `support_admin.py`, `support.py` | Admission-file + grant + audit consistency; support sender bindings | HA-02F DB grant/revoke/audit synthetic PASS; FIELD file consistency/fencing and sender pending, PG FIELD refused before file I/O |
| `referrals.py` | Sponsor-bound request idempotency, pool/daily limits, proof/link и claim/invitation в одной транзакции | HA-02D synthetic PASS; full import/production wiring pending |
| `chat.py`, `chat_service.py`, `chat_sync.py` | Chat identity/proof, directory sequence, service sender revoke; filesystem exports | Pending |
| `restricted.py`, `restricted_admin.py`, `readiness_receipts.py` | Grants, отдельные restricted challenges, certificates, readiness, CRL sequence | HA-02F explicit admin grant/revoke DB PASS; auto-enroll, challenges/certificates/readiness/CRL writers pending |
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

1. Перевести остальные writers/CLI (далее restricted challenges/certificates/readiness и support sender), затем metadata,
   tombstones/files и остальные строки карты. Не допускать mixed backend writers;
   synthetic membership не заменяет production wiring, deadline и package gates.
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
