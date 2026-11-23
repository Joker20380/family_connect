# HA-02 — каноническое хранилище и очередь writers

23 November 2026. **IN_PROGRESS; HA-02A–M DB contracts квалифицированы по отдельности
на синтетическом стенде; HA-02N source file/writer inventory и HA-02O общий
лабораторный storage-shape import проверены отдельно. HA-02P добавляет pinned
application SQLite adapters и joint semantic fixture; live schemas не обследованы.**
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

## HA-02G — issuance and readiness transactions

`RestrictedTransaction` в существующем `restricted.py` выносит challenge/certificate,
auto-enrollment и readiness receipt SQL в семантическую границу. SQLite использует
тот же алгоритм; PostgreSQL — native placeholders и отдельные DDL/marker, не перевод
SQLite SQL строк. `Access.enrollment` объединяет запись и расход proof; readback
использует `Access.read_enrollment`: SQLite URI `mode=ro` + explicit snapshot и
PostgreSQL `REPEATABLE READ, READ ONLY`, без advisory writer lock.

- Новый PG marker `family-connect/ha-restricted-synthetic/v1` требует валидные
  enrollment/admin/paid schemas. Отсутствие paid schema не допускает noncohort fallback.
  Серийные номера X509 хранятся как TEXT, без потери159-bit значений. Инициализация
  явная и только в disposable store; production selector/import не добавлены.
- Challenge + restricted binding + correlation и fetch + certificate + consumed
  proof + receipt атомарны; ACK proof + exact payload тоже. Capacity8 сохраняется.
  Часы повторно проверяются после ожидания транзакции; истёкшие trust/CRL/paid права
  не становятся разрешёнными за счёт старого времени. Wire payload не меняется.
- Owner/device/invite/grant/revision/family, primary/secondary node, publication,
  CRL revoke и paid bounds проверяются прежним алгоритмом. Новая короткая paid
  lease не наследует старый долгий certificate. Offline noncohort остаётся отдельным.
- Receipt retention24h/cap16 и certificate reuse детерминированы при равных timestamps
  (correlation/serial tie-break); это не новый lifetime или продление разрешений.
  Lost commit ACK требует readback/нового proof, не повторного использования старого.
  При rollback старый proof остаётся usable; при доказанном commit replay запрещён.
- 123 restricted +40 enrollment contracts проходят с настоящим PostgreSQL, без
  skips. Проверены конкурентные fetch/ACK/capacity, ошибки после записи, потеря ACK,
  kill backend, paid/node/CRL revoke, strict schema и repeatable readonly snapshot.

Отдельный recovery сохраняет16 synthetic таблиц/36 строк: enrollment/support/admin/
paid + restricted rows. Незавершённые certificate/ACK/proof изменения исчезают после
SIGKILL. Старый pre-issuance dump отвергается сравнением с известным committed
snapshot; актуальный dump точно восстанавливается в другом owned контейнере.
Consumed proofs отвергаются, pending fetch/ACK работают ровно один раз; certificate
reuse, paid bounds, revokes, audit и safe readback сохраняются. **Issuer keys только
ephemeral и удерживаются в памяти между проверками**: это не тест их backup/restore,
не full product recovery, production watermark, replication или RPO0.

FIELD/CRL/file writers, issuer fencing и production wiring остаются pending. Сейчас
откат — остановить только свой стенд; серверы не менялись. После production writes
понадобятся fence + current-state recovery, не замена старой SQLite. Полный cutover
блокируют остальные строки карты и HA-03..05; этот DB slice их не обходит.

## HA-02H — chat and support sender transactions

`ChatTransaction` в существующем bundled `chat.py` переносит SQL для chat identity,
отдельных challenges, service senders, sequence и support binding. SQLite использует
тот же алгоритм; PostgreSQL получает native DDL/FK/unique/check и marker
`family-connect/ha-chat-synthetic/v1/db-only`. Никакого production DSN/selector,
автоматического migration/import или нового сетевого протокола нет.

- Регистрация требует обе подписи и активные device/invite. Bind и расход challenge
  атомарны; повтор нового proof идемпотентен по identity, старый proof одноразовый.
  Конкурентный device/service claim одного public key имеет одного победителя.
  Existing service revoke terminal: повтор регистрации не включает отозванный sender.
  Service identity не создаёт device/invite/VPN grant.
- Sequence продвигается в одной транзакции со snapshot; membership cap550,
  challenge cap8 и lease100s сохраняются. Неизвестный commit sequence нельзя
  трактовать как неслучившийся: readback либо новая, строго большая generation;
  это не доказательство ACK от mailbox и не восстановление старого номера.
- `support.enroll` проверяет активность клиента, binding и sender (schema1/device
  или schema2/service) **в той же writer transaction**, где сохраняет support_sender.
  Прежний промежуток между отдельными configuration/read и enroll/write устранён.
  Менять прежний support_sender на другой по retry нельзя. Configuration/inventory
  остаются read-only и не записывают enrollment, revokes/disabled state не скрываются.
- Часы проверяются после входа в транзакцию; expired chat proof/support role/node
  lease отвергаются. Read-side snapshots используют `Access.read_enrollment`.
  Local policy загружается отдельно: атомарность DB **не** распространяется на
  concurrent policy-file change, SSH/ACK или file replace; это gates HA-03.
- `chat_sync.synchronize`, direct `_synchronize` и `support.publish` отвергают PG
  до lock/key/file/network I/O. Локальный flock не объявлен distributed fence;
  текущий SQLite publication path сохранён. CLI и служба не выбирают новый backend.

114 настоящих SQLite/PG contracts (74 chat/support +40 enrollment),238 consumer/
package regressions и18 окончательных runner guards PASS;23 optional nginx/pinned
archive cases не выполнялись. Closed support kit reproducibility/import проходит.
Recovery совмещает chat/support с enrollment/aliases/paid/audit: SIGKILL откатывает
незавершённые binding/proof/revoke/sequence изменения, актуальный restore совпадает
по всем15 lab таблицам/29 строкам. Старый dump отвергнут; consumed proof не оживает,
pending proof работает один раз, sender revoke/support binding сохраняются, sequence
продолжается. Keys/policy удерживаются в private lab, **не** восстанавливаются.
Не доказаны full product recovery, production high-watermark, replica/RPO0, reverse
import, mailbox ACK/fencing или WAN failover. Откат сейчас — убрать owned стенд;
после live writes нужны fence и current-state recovery, а не старая SQLite.

## HA-02I — gateway routing transactions

Общий `RoutingTransaction` находится в уже упаковываемом `gateway_routing.py`;
`Access.enrollment().routing()` выбирает SQLite или native synthetic PG adapter.
Новый `gateway_routing_postgres.py` содержит отдельные DDL, marker и PL/pgSQL
append-only trigger. Нет SQL string translation, production DSN, automatic import
или переключателя работающего сервиса. Существующие raw SQLite helpers совместимы.

Одна writer transaction включает install/seed существующих устройств, изменение
policy generation, первое sticky assignment либо явный move **вместе с event**.
Selection import создаёт свой journal в той же транзакции; policy digest и generation
проверяются вместе. Status и explicit selection используют read-only snapshot.
Selection не меняет sticky assignment; policy replacement не перемещает устройства.
Revoke устройства/приглашения запрещает новые назначения и выдачу обоих каталогов.

Operation ID связан с payload hash. Retry того же committed запроса — `UNCHANGED`,
конфликт payload отвергается. Старый retry после следующего move/selection не
перематывает state. Assignment и selection sequences монотонны; rollback на прежний
host требует **нового подписанного каталога с большей sequence**, а не старой БД.
SQLite UPDATE/DELETE и PG UPDATE/DELETE/TRUNCATE journals запрещены триггерами;
это не защита от DB-superuser, который способен отключить schema guards.

111 контрактов на настоящих SQLite/PostgreSQL:71 routing +40 enrollment, без skips.
Конкурентные install/first assignment/identical и conflicting moves, selection,
exact predecessor, immutable journals, lost commit ACK, rollback DDL/state/event,
revoke, missing signed files и generation corruption проверены. Отдельно PG schema
marker и termination backend во время install/move/selection. Подписи/права файлов
и public wire format не ослаблены; ephemeral offline signer только в тесте advance.

Owned PostgreSQL17.11 runner принудительно завершает контейнер с незавершёнными
изменениями; после restart и отдельного current restore сверяет **все15 lab таблиц/
28 строк**, включая payment/alias/proof/revoke. Stale pre-routing dump отвергается.
Повтор committed operations не меняет snapshot; pending proof usable once; consumed
proof/revoked device refused; восстановленные append-only triggers остаются active.
Forward catalog rollback и invalidation selection при policy replacement проверены.

Граница: signed files/anchors и synthetic identity keys удерживаются вне dump,
их recovery не доказан. HTTP сначала отдельно потребляет challenge, затем читает/
создаёт assignment, проверяет paid policy и регистрирует на удалённом gateway.
Этот slice **не** делает всё это atomic и не повторяет использованный proof после
потери ответа: нужен новый challenge. All-node membership/deadlines, file publication,
remote ACK, HA-03 fencing, all-table import, replica/RPO0 и full product recovery
остаются обязательными. PG не подключён к production HTTP/CLI. Rollback сейчас —
cleanup собственного lab; после live writes только fenced current-state recovery.

## HA-02J — durable CRL preparation and local recovery

Общий `CRLTransaction` находится в уже упаковываемом `restricted_admin.py`;
`Access.enrollment().crl()` выбирает SQLite/native PG adapter. `crl_postgres.py`
содержит отдельные synthetic DDL/marker и immutable UPDATE/DELETE/TRUNCATE guards.
Нет live initializer, product DB import, production DSN/CLI switch или scheduler.
SQLite outbox schema создаётся только rehearsal. Это не импорт legacy CRL state.

`prepare_crl` сохраняет signed PEM, sequence, operation/request/payload hashes и
validity в одной writer transaction с grant/device/invite/revision/paid snapshot.
Время читается после writer lock. Проверяются signer/delegation, предыдущая подпись,
continuity, целочисленный предел2**53, expiry и reader bound16384 bytes. Operation
retry возвращает прежние bytes без подписи/продления. Даже expired/superseded replay
является **только readback**, не разрешением публикации. `pending_crl` и
`acknowledge_crl` допускают лишь текущий непросроченный candidate с согласованными
sequence/hash. DB `local_receipt` монотонен, но сам по себе не доказывает file durability,
удалённый ACK, epoch или наличие актуального CRL на всех serving nodes.

`scripts/crl_postgres_rehearsal.py` содержит только temporary single-publisher helper:
pending read → file fsync/replace/directory fsync → hash readback → DB receipt.
Между этими действиями нет global fence; concurrent publisher/revoke-after-prepare
и удалённая доставка НЕ квалифицированы. Для production нужны HA-03 epoch/fencing,
node-specific durable ACK, независимый readback и ограниченный recovery deadline.
Нельзя превращать helper в production publisher или считать DB receipt gateway ACK.

Legacy `publish_crl` остаётся SQLite-only и file-before-commit: после ошибки commit
файл может опережать DB. Retry использует max(signed-file floor,DB floor)+1, а не
перематывает номер; exact-byte retry относится к outbox, не legacy-пути. Legacy sync,
check и paid-canary lock отвергают PG/synthetic outbox до key/lock/file/network I/O;
publisher повторяет outbox guard внутри writer transaction. Это защита от случайного
mixed-backend вызова, не fencing уже запущенных старых процессов/CLI/file journals.

128 реальных DB контрактов PASS /0 skips:88 CRL +40 enrollment. Проверены concurrent
identical/conflicting operation IDs, paid/revoke/revision snapshot, immutable bytes,
rollback, backend termination, потеря commit ACK и clock/expiry. Ошибки file fsync,
replace, directory fsync и DB receipt не выдумывают ACK; повтор восстанавливает те
же bytes. Legacy file-ahead/ACK-loss и fresh-clock после writer lock также проверены.

PostgreSQL17.11 actual owned SIGKILL, restart и отдельные stale/current restore
сравнивают все19 лабораторных таблиц/22 строки. Stale snapshot отвергнут; restored
triggers, consumed/revoked proofs, payment replay, pending candidate и sequence
сохраняются. Уже заменённый local file с receipt0 согласуется с DB exact bytes,
последующий candidate получает больший номер. Эфемерные ключи удерживаются в памяти,
не восстановлены из backup. Это не full product backup, replication/RPO0 или reverse
migration. [Evidence/rollback](releases/2026-11-23-control-ha.md#ha-02j--durable-crl-recovery).

## HA-02K — metadata and consent transactions

`MetadataTransaction` находится в уже упаковываемом `technical_metadata.py`;
`Access.enrollment().metadata()` выбирает SQLite либо native `metadata_postgres.py`.
Synthetic schema содержит только current `device_metadata` и marker, без истории
raw reports/IP. PostgreSQL DDL написан отдельно, не SQL string translation. SQLite
canonical schema создаётся только rehearsal; live `technical-metadata.sqlite` не
перемещается, новый DSN/HTTP/CLI selector не добавлен.

`request_repository` требует synthetic marker и в одной writer transaction проверяет
точно подписанный digest, расходует one-use proof, проверяет device/invitation revoke,
сохраняет latest-only report либо пустой revoke tombstone. Любой отказ capacity/rate/
consent либо DB failure откатывает proof и metadata вместе. При потерянном commit ACK
нужен **новый proof с теми же report bytes**, а не новый consent epoch: подтверждённый
report возвращает прежний receipt без обновления received/TTL. Новый opt-in после
отзыва допустим лишь с большим epoch и сохранённым rate limit. Revoke обходит sample
rate limit, но не освобождает slot/floor. Limits6144 bytes/5000 devices/60s/7days и
неизменённая metadata-v1 schema сохранены. Часы проверяются после writer acquisition.

Epoch/sequence/digest и revoked state не сбрасываются при prune. Synthetic DB triggers
блокируют UPDATE regression/DELETE (и PG TRUNCATE); в том же report version разрешено
только удалять целые observation groups, не восстанавливать старые payload/received.
Это guards обычных DB operations, не защита от superuser, отключающего triggers.
Read-only snapshot фильтрует expired groups без записи/writer lock. Prune удаляет
payload groups, но хранит consent floor и digest. SQLite writer использует secure_delete;
PG physical pages/MVCC/WAL/backups и гарантированное физическое стирание НЕ квалифицированы.
Production backup policy должна исключать долгоживущие observation payload histories
и одновременно сохранять актуальные consent floors. Старый backup с enabled вместо
revoke нельзя принимать как безопасное восстановление.

Legacy `request(access,path,...)` остаётся двумя SQLite commits: identity proof раньше
metadata-файла, поэтому при file failure нужен fresh proof. Он отвергает PG либо
synthetic canonical marker до proof/file mutation, но это не distributed fencing.
Общая policy/SQL boundary не требует новых Access APIs в старом overlay; минимальный
legacy API проверен отдельно. GeoIP ephemeral enrichment и panel read-side не перенесены:
multi-store snapshot/import, collectors/retention scheduler и все CLI надо переключать
вместе в будущих gates. Сырые IP, реальные наблюдения и product DB не читались.

120 real SQLite/PG contracts PASS /0 skips (80 metadata +40 enrollment): concurrency,
sample/revoke ordering, one-use/digest, rate/capacity, explicit new epoch, per-group
TTL, clock skew/writer waits, trigger floors, rollback, backend termination, lost ACK,
read-only/legacy guards. Actual PostgreSQL17.11 SIGKILL/current restore сравнивает все
12 lab tables/26 rows; stale pre-revoke snapshot отвергнут. Restored tombstones,
one-use proofs/payment retry и triggers сохранены; delayed reports не оживляют
payload, явный новый epoch позволяет согласие. Identity keys удерживаются в памяти,
не восстановлены. Нет full product/cross-store import, RPO0, replicas или reverse
migration. [Evidence/rollback](releases/2026-11-23-control-ha.md#ha-02k--metadata-and-consent-recovery).

## HA-02L — diagnostics transactions

Synthetic scope extends HA-02A proof transactions and HA-02E stable Support IDs;
no production schema/backend is selected. Shared `DiagnosticsTransaction` stays
in the bundled `diagnostics.py`; native PG has explicit DDL and a synthetic marker.
`request_repository` validates exact signed bytes, consumes proof, checks device/
invitation revoke, resolves Support ID and saves the latest snapshot atomically.
SQLite uses BEGIN IMMEDIATE; PG uses the existing advisory transaction lock.
Timestamp/rate/TTL checks run after writer acquisition. Failed validation, conflict,
rate/capacity, save/prune or transaction commit leaves proof and snapshot unchanged.
An ambiguous committed result needs a fresh proof for the same report, not replay
of its consumed challenge. A duplicate of the retained report preserves receipt/TTL;
same report ID with different parsed content refuses. Signed bytes remain exact,
but idempotency compares parsed report content as in the existing schema1 API.

Unchanged privacy contract:4096 bytes, explicit `consent=true` on each submitted
report, bounded metrics/enums,5000 latest snapshots,60s sampling and7-day retention.
No IP/raw log/arbitrary metrics/history are added. TTL boundary is inclusive at
`received + RETENTION`, then hidden by read-only snapshots and deleted by prune.
Reads do not prune/take writer locks; prune is a separate canonical writer.
This is NOT metadata-v1 consent: no epoch/tombstone or historical report-ID ledger
exists. After expiry/replacement, a fresh signed request can submit the old report
again under the existing rate/capacity rules. No permanent anti-replay claim is made.

Legacy API still uses separate registry/snapshot SQLite commits: a file failure
requires a fresh proof. It refuses PG/canonical-marker stores before proof/file I/O;
its timestamp is now sampled after the snapshot writer lock. Production HTTP,
operator CLI and retention thread are not wired to canonical entrypoints. Closed
HTTP/support packages and old diagnostics/desktop senders pass focused regressions.
No live reports/client keys were read; synthetic keys are retained, NOT restored.

113 real DB contracts /0 skips (73 diagnostics +40 enrollment),217 focused regressions
/16 explicit optional skips. PostgreSQL17.11 SIGKILL and exact12-table/19-row restore
preserve the current snapshot, acknowledged expiry deletion, used/pending challenges,
device revoke, Support IDs and paid state. Stale pre-prune/revoke restore refuses via
exact comparison to externally retained current lab state, not an automatic live
backup freshness oracle. Current restore is not all-product backup/import, replicated
RPO0, physical PG/MVCC/WAL/backup erasure, fencing or reverse migration. Before cutover
abort only the owned lab. After new canonical writes never restore old SQLite;
fence writers and recover current acknowledged state, including retention deletions.
[Reproducer](../deploy/control-ha/README.md#ha-02l-isolated-diagnostics-recovery) ·
[Evidence](releases/2026-11-23-control-ha.md#ha-02l--diagnostics-recovery).

## HA-02M — notice transactions

Common `NoticeTransaction` lives in the already bundled `scripts/service_notices.py`;
legacy `Notices` owns its SQLite transaction/file side effects, canonical adapters
participate only in the outer enrollment transaction. Explicit synthetic schemas
add a marker and stable `events.position`, replacing SQLite-only rowid ordering.
The existing global writer lock serializes position allocation, quota, role revoke,
revision CAS and immutable edit-operation insertion. No all-product import exists.

Synthetic device requests consume action-bound proof with role/list/publish/edit
and device/invitation revoke checks in one transaction. Existing proof protocol
binds `notices-<action>`, NOT the request payload; do not describe it as a new signed
body protocol. Notice ID binds author/content/audience/lifetime; edit request ID
binds full request plus device. Fresh-proof retries preserve receipt/revision and
cannot re-enable roles, refresh expiry or duplicate history. Any publisher may edit
under the existing policy; bearer credentials only publish, never delegate roles.
Operator-only grant/revoke helpers have no new HTTP route. Explicit operator device
regrant remains allowed; these roles are not irreversible device-revoke tombstones.

Original v1 remains immutable; v2 reads latest revision. Append-only event/edit
history and monotonic revision update/delete/TRUNCATE guards survive PG restore.
These guards do not protect against a privileged DB owner disabling them. Feeds use
read-only snapshots without writer locks; proof-bearing list/role requests remain
writers. Pagination orders by stable position within each snapshot, not a pinned
snapshot across multiple requests during concurrent publication.200 active notices,
50-row pages,1MB feeds and existing text/audience/lifetime validation remain.
Expired notices stay archived; fresh retries do not refresh them. No history prune
or consent/metadata policy change is introduced.

Canonical publish returns `status=stored`, not proof of public delivery. Export and
legacy entrypoints refuse canonical marker/PG access before proof/file mutation.
Legacy production still has separate proof, notice DB and v1/v2 file commits; file
failure cannot roll back an already committed notice. Its token-file handling,
schema and CLI remain; no canonical credentials are printed or written to token files.
Two public feed files are not a distributed atomic transaction. Public-file outbox,
receiver ACK/epoch fencing and reconciled export belong to HA-03; no publication
or runtime backend is selected here.

119 real DB contracts /0 skips (79 notices +40 enrollment),118 focused regressions
/16 optional skips. Actual PostgreSQL17.11 SIGKILL discards unfinished revision,
edit journal, role re-enable and proof consumption; exact16-table/26-row current
restore preserves v1/v2, active/revoked publishers, used/pending proofs and paid
state. Stale pre-edit/revoke backup is refused against externally retained current
lab state, not a live freshness oracle. Keys/token/clock are retained, NOT restored.
No full all-store backup/import, replication/RPO0 or reverse migration claim.
[Reproducer](../deploy/control-ha/README.md#ha-02m-isolated-notice-recovery) ·
[Evidence and rollback](releases/2026-11-23-control-ha.md#ha-02m--notice-recovery).

## HA-02O — synthetic all-store shape import

**Ограниченный лабораторный gate, не production importer.**
[`control_ha_import.py`](../scripts/control_ha_import.py) принимает только bytes
четырёх SQLite images: registry, metadata, diagnostics, notices. Явный список30
data tables покрывает A–M; native PostgreSQL DDL создаются существующими factory
в одной внешней транзакции, вместе с12 markers и import receipt. Не переводим
произвольный SQLite DDL, не читаем live paths и не выбираем новый backend в HTTP/CLI.

- Source v1 имеет отдельный purpose `family-connect/ha-all-store-synthetic/v1/not-for-activation`
  и одинаковый checkpoint во всех четырёх images. Schema/columns/object coverage
  сравниваются точно; лишние таблицы, views, indexes, triggers, другой marker или
  частичный набор дают NO_GO. Это **искусственная source schema**, не утверждение
  совместимости с действующими SQLite таблицами/triggers/migration versions.
- Inputs ограничены16MiB каждый,20000 rows/table и SQLite VM budget. Образы
  десериализуются в read-only in-memory connections; исходные bytes не меняются.
  INTEGER сохраняется как signed64, TEXT — Unicode, nullable — явно по контракту.
  FLOAT/BLOB/NUL/non-nullable NULL не приводятся молча. Notices `rowid` переносится
  в `position` с пропусками; audit identity reseed сохраняет следующий ID.
- Восемь внешних ролей: aliases, admission, sender_policy, routing_files,
  issuer_material, maintenance_state, node_allocations, receiver_state. Только
  JSON **декларации ссылок**: pinned bytes/checkpoint/role и требуемые ссылки
  сверяются, отсутствующие/duplicate/неверные inputs отклоняются. Дополнительные
  исторические ссылки разрешены. Hash здесь не подпись и не доказательство
  полноты actual aliases/private profiles/allocator/receiver floors/certificates.
- Fresh schema, rows, native FK/unique/check/triggers, sequence reseed и receipt
  создаются атомарно. Ошибка до commit не оставляет частичную схему. Existing
  unrelated target никогда не очищается. После неоднозначного commit сначала
  readback: тот же fingerprint, полный набор rows, markers, constraints/functions/
  triggers/indexes/sequence definition и текущее identity state дают `EXACT_RETRY`;
  любое обнаруженное изменение — отказ, не повторная перезапись. Advisory lock
  сериализует два lab importer, но не является distributed fencing.
- Receipt/fingerprint приватны; stdout содержит только counts/result/limitations.
  Нет команд активации или разблокирования публичной записи; `activation=FORBIDDEN`.

[`control_ha_import_fixture.py`](../scripts/control_ha_import_fixture.py) генерирует
регистрацию, pending/used proofs, Android Support ID observation и платёж через
реальные helpers. Остальные семьи частично представлены typed storage sentinels:
это не usable certificate/CRL, signed catalog, корректный notice feed или full
semantic acceptance. Поэтому30 непустых data tables/34 rows доказывают **coverage
и storage preservation**, а не единый работающий issuance/renewal flow.

111 real-run contracts PASS /0 skips (71 import +40 enrollment),97 focused
regressions PASS /0 skips. PostgreSQL17.11 abrupt SIGKILL с незавершённой записью
и restore в отдельный owned container сохраняют все43 tables/47 rows. После
restore pending proof работает один раз, next audit ID42; отдельные tests
проверяют все три paid projections, append order, nullable/Unicode/int64,
native guards, rollback, concurrent import, lost reply и отказ при target drift.
Это не encrypted off-host/full external recovery и не strict replica RPO0.

Следующий bounded scope: explicit deployed-schema adapters + семантически валидный
joint synthetic fixture. Отдельно нужны actual external recovery inputs, live
writer census/consistency barrier и production version/row-count coverage.
HA-02O не разрешает переход к репликации или cutover автоматически.
[Команды/rollback](../deploy/control-ha/README.md#ha-02o-synthetic-all-store-shape-import) ·
[Evidence](releases/2026-11-23-control-ha.md#ha-02o--synthetic-all-store-shape-import).

## HA-02P — application SQLite adapters

[`control_ha_sqlite_import.py`](../scripts/control_ha_sqlite_import.py) принимает
четыре согласованных SQLite images, созданных **штатными migrations/операциями**,
а не искусственным source DDL HA-02O. Контракт
[`sqlite-source-v1.json`](../deploy/control-ha/sqlite-source-v1.json) фиксирует
точные table/index/trigger definitions текущего source-кода и отсутствие нового
CRL outbox в legacy SQLite. Это поддержка одного явно рассмотренного schema
варианта, **не доказательство совпадения с установленными RU/NL schemas**.

- Registry22 + metadata1 + diagnostics1 + notices5 =29 исходных таблиц. Все они
  копируются по явному списку колонок; notices rowid становится position.
  Единственная новая пустая data table — `restricted_crl_publications`: старого
  журнала operation IDs нет, его нельзя придумать или пометить доставленным.
  Legacy CRL sequence сохраняется, а не сбрасывается в0. Ни один optional/missing
  source/table не пропускается автоматически: другой вариант требует нового gate.
- До PostgreSQL проверяются точные schema definitions, user_version/application_id0,
  UTF-8, quick_check/FK,16MiB/image,20000 rows/table, typed/null contract HA-02O,
  cross-store device/Support ID references и восемь external-reference manifests.
  Пустой device в global routing event допустим по исходному контракту; pending
  activation challenges могут относиться к ещё не зарегистрированному устройству.
  Source images не изменяются. Их digests, adapter manifest и bootstrap bytes
  привязаны к private import receipt: даже другой image с теми же rows не означает
  тот же retry. Нет подключения к target до завершения preflight.
- Дополнительно обязателен versioned CRL bootstrap: checkpoint, подписанный
  delegation manifest и текущий CRL; доверенный root public anchor передаётся
  **отдельно**, не выбирается из входного bundle. Проверяются delegation/issuer,
  CRL signature/issuer/validity, точное совпадение CRLNumber с legacy DB floor,
  подписи сохранённых сертификатов, их serial/expiry. Смешанные issuer generations
  или file/DB floor mismatch — отказ, не автоматическое исправление.
- Первый canonical CRL не мог продолжиться с legacy nonzero floor и пустым outbox:
  прежний guard правильно ожидал journal predecessor. Теперь в **той же import
  transaction** создаётся immutable `ha_import_crl_anchor` с исходным sequence и
  SHA256 проверенного CRL. Это migration anchor, не publication/remote ACK. Только
  точный predecessor может начать outbox; после первой записи снова требуется
  последний outbox payload/sequence. Повтор старого baseline не разрешается.
  UPDATE/DELETE/TRUNCATE anchor запрещены. Без import anchor прежний guard unchanged.
  Public file export по-прежнему запрещён до HA-03 fencing.

[`control_ha_sqlite_fixture.py`](../scripts/control_ha_sqlite_fixture.py) использует
настоящие activation/referral/payment/support/grant/issuance/ACK/chat/routing/
metadata/diagnostic/notice операции с локально созданными identities и ephemeral
issuer. Сертификаты/CRL и routing catalogs действительно подписаны; notices v1/v2
валидны, metadata содержит sample и revoke tombstone, отдельное устройство revoked.
Нет storage-sentinel credentials. Тестовый root/private key, referral secret,
sender policy и signed routing files **удерживаются в памяти процесса/приватной
fixture directory**, не восстанавливаются из PostgreSQL. Поэтому semantic parity
не равна полному external disaster recovery.

Recovery gate: exact imported DB после SIGKILL/restore, затем business operations
на восстановленной БД и новый backup. Старая pre-operation копия отвергается;
current-state restore сохраняет новые proofs/edits/CRL/audit. Попытка повторить
старый import поверх них отклоняется без записи. Действующие production SQLite,
service selectors, client endpoints и внешние publishers не переключались.
165 contracts /0 skips,128 CRL regression contracts /0 skips и98 focused regressions
/0 skips PASS. Исходные29 таблиц/68 rows становятся44 таблицами/82 rows с markers,
receipt и CRL anchor; после новых операций восстановлены44 таблицы/87 rows.
[Команды](../deploy/control-ha/README.md#ha-02p-application-sqlite-import) ·
[Evidence/rollback](releases/2026-11-23-control-ha.md#ha-02p--application-sqlite-import).

## HA-02Q — encrypted recovery bundle

[Bundle contract](../scripts/control_ha_recovery_bundle.py) и
[owned rehearsal](../scripts/control_ha_bundle_rehearsal.py) добавляют отдельный
version1 recovery capsule, **не production backup/restore command**. Основа —
HA-02P application images и HA-02N external-role inventory. В рабочие Friends/
registry/publisher entrypoints ничего не подключено; activation всегда FORBIDDEN.

- AES-256-GCM с новым96-bit nonce и version/purpose в authenticated data;
  wrapping key32 bytes поступает отдельно, не хранится внутри capsule или в Git.
  Это raw random key, не пароль/KDF и не offline release/root signing key.
- Detached trusted checkpoint связывает точные encrypted bytes, checkpoint ID,
  отдельно полученный public issuer root и import fingerprint. Старый bundle
  против текущего checkpoint отвергается. Сам bundle не доказывает свежесть:
  при утрате/откате checkpoint или wrapping key гарантии восстановления нет.
- Внутри четыре SQLite images, восемь reference manifests, восемь непустых
  artifact roles и signed bootstrap. Каждый artifact hash входит в PG import
  fingerprint; замена только внешнего файла меняет import identity и запрещает
  повторный import поверх прежнего состояния. При этом случайный encryption nonce
  не меняет identity тех же recovery inputs.
- До PG I/O: exact fields/version, duplicate JSON keys/NaN, canonical base64,
  fixed role/store coverage, bounded memory/rows, safe logical artifact names,
  pinned SQLite schema/row references и HA-02P CRL checks. Не используется
  archive extraction; library возвращает bytes в память, не пишет файлы/БД.
  Limits:96MiB plaintext,16MiB/image,1MiB/artifact, максимум64 artifacts;
  ошибки не включают secret bytes, private paths или входной JSON.
- Дополнительно проверяются delegated runtime Ed25519 key против issuer certificate,
  точные CRL/delegation bytes, действующий seed directory и referral secret против
  всех сохранённых link/claim hashes. Несовпадение/истечение — отказ, не reissue.

Fixture содержит19 artifacts: настоящие ephemeral issuer/referral bytes, signed
routing files, sender policy и generated alias manifest/HMAC bytes. **Admission,
maintenance_state, node_allocations, receiver_state — четыре явно маркированных
opaque byte probes, НЕ их runtime formats или восстановленные node authorities.**
Все семь non-issuer roles пока имеют только exact-byte/provenance coverage в
preflight, без полноценного semantic binding к DB/profile/receiver floors. В
частности alias fixture не является полной canonical device/event coverage.
Непустой artifact role не доказывает completeness соответствующей реальной службы.

Rehearsal удаляет только созданный им private synthetic source directory и
отбрасывает исходные service/referral references **до** DB restore. Из encrypted
capsule создаются новые service/key objects, SQLite baseline и routing/sender files
в новом0700 каталоге (файлы0600). PostgreSQL17.11 SIGKILL, exact44-table/82-row
restore, business continuation и44-table/87-row current restore PASS; stale backup
и old import отвергаются. Три paid projections, proofs, referral replay, readiness,
CRL advance, metadata tombstone, diagnostics, notices, routing, Support ID и audit
сохраняются. Это не secure memory erasure: wrapping key/checkpoint/root и client
test drivers остаются в памяти, remote custody/off-host restore не проверены.

154 contracts /0 skips (60 bundle +54 adapter +40 enrollment),31 runner/file guards
/0 skips. No live capture, live schema census, coherent writer barrier, complete
profile/allocator/receiver recovery, strict replication/RPO0 or fencing acceptance.
Следующий scope — заменить probes реальными versioned role adapters и semantic
checks; полный DR и production migration остаются отдельными gates.
[Команды](../deploy/control-ha/README.md#ha-02q-encrypted-recovery-bundle) ·
[Evidence/rollback](releases/2026-11-23-control-ha.md#ha-02q--encrypted-recovery-bundle).

## HA-02R — external-role adapters

[Strict adapter](../scripts/control_ha_external_v1.py) поверх HA-02Q capsule принимает
отдельный versioned profile `family-connect/external-roles/v1/not-for-activation`.
Это source-level формат текущих реализаций, **не автоматически обнаруженная live
схема**. Поддержаны пять non-issuer ролей; неизвестные поля/варианты отклоняются.
Проверка читает SQLite только в памяти, не открывает PG или live filesystem.
Дополнительный profile digest входит в import fingerprint: receipt от generic
byte-only Q нельзя использовать как подтверждение strict R acceptance.

| Роль | Проверяемый формат и связь | Ограничение |
| --- | --- | --- |
| aliases | Настоящий `fc-pseudonym-aliases-v1`, current HMAC key-check, покрытие всех device и paid-event IDs захваченной registry, current generation resolution | Только `manifest` + `current-hmac`; legacy secret не переносится. Исторические entity IDs/handles сохраняются точно, а не генерируются заново. Полный census внешних consumer references ещё нужен. |
| admission | Настоящий FIELD `devices` список до3 IDs; уникальность, активная device/invitation, существующий unrevoked grant, family/minimum revision/expiry | Это explicit FIELD профиль; не `all_activated` и не иной cohort-cap overlay. Допуск может быть уже множества grants. |
| sender_policy | Реальный `support.json` schema2, typed fields/revision, enabled зарегистрированный service sender и согласованные support sender bindings | Schema1 и иной multi-sender вариант требуют отдельного adapter gate; публикация bindings не выполняется. |
| routing_files | Anchor, content-addressed policy/catalog/selection bytes; настоящая signature/schema2/schema3 verification, policy generation, assignment node/sequence, исторические ссылки и selection templates/sequence/current policy | Global install/replace events содержат policy SHA в поле `catalog_sha256`; validator различает их с device assignment. Не подписывает/не переписывает catalogs. |
| node_allocations | По одному `peers.db` image и полному installer settings на каждый из трёх узлов; exact native schema/index, SQLite pragmas/integrity, known registry public keys, row IDs, AUTOINCREMENT floor, network/address и signed-catalog host binding | Закрытый known-peer вариант, nonempty ledger, `/16` networks RU10.84/NL10.83; неизвестные peers/settings требуют census, не удаления. Allocators независимы и не сливаются. |

[Fixture](../scripts/control_ha_external_fixture.py) создаёт файлы через реальные
alias/admission writers и native AWG registration code, но **в собственных temp
каталогах с gateway/TCP/paid-engine/command side effects отключёнными**. Original
capsule содержит23 artifacts; admission и node allocations больше не probes.
Две роли `maintenance_state` и `receiver_state` всё ещё явно opaque probes;
ни профили/журналы, ни prepared/denied/high-water receivers не считаются восстановленными.

[Rehearsal](../scripts/control_ha_external_rehearsal.py) удаляет исходный fixture
до восстановления. После DB SIGKILL/current restore новые service objects и реальные
файлы восстанавливаются из capsule. Alias history расширяется только current key;
FIELD и sender читаются штатными consumers. Для каждого из трёх synthetic peers DB
четыре записи имеют собственный порядок/IDs и сохранённый floor5 после удаления
пятой записи. Обратный registration replay сохраняет адреса, следующая запись
получаетID6, а не переиспользует удалённыйID5. Это isolated allocator continuation,
не применение kernel AWG/TCP и не новый live node checkpoint.

161 contracts /0 skips (61 external +60 bundle +40 enrollment),90 focused consumer/
runner checks /0 skips. Exact44-table/82-row import/restore и44-table/87-row current
restore после новых business writes PASS; stale DB и old import отвергаются.
Семантически валидное пересоздание alias entity IDs всё равно меняет trusted
checkpoint/import identity и не заменяет прежний receipt. Отдельный checksum не
доказывает свежесть/происхождение snapshot: wrapping key/trusted checkpoint/root
пока retained in memory, live node ownership/floors не аттестованы. Подстановка
семантически допустимых bytes при создании нового доверенного checkpoint требует
будущего capture/barrier/ownership gate; validator не угадывает утраченную историю.

Не квалифицированы maintenance/profile journals, receiver state, off-host key/
checkpoint custody, installed versions/writers, coherent live capture, полный DR,
strict replication/RPO0 или HA-03 fencing. Activation остаётся FORBIDDEN.
NEXT: два оставшихся external-role adapters; не переходить к replication/deploy.
[Команды](../deploy/control-ha/README.md#ha-02r-external-role-adapters) ·
[Evidence/rollback](releases/2026-11-23-control-ha.md#ha-02r--external-role-adapters).

## HA-02S — receiver safety adapter

[Receiver-v1](../scripts/control_ha_receiver_v1.py) добавляет ещё один strict
profile поверх Q/R. Это проверка реально используемых форматов до PG/file writes,
не collector и не запуск gateway/mailbox. Восстановление возвращает точные bytes;
оно не обновляет timestamps, boot IDs, leases, sequence или prepared markers.

Поддержан ограниченный согласованный capture:

- Три отдельные пары `transport-enforcement.json`/`transport-state.json`: точный
  node/profile/schema, все captured registry devices, native decision validation
  и canonical snapshot binding на исходном времени; unknown/missing records,
  revoked identity allow и несовместимые paid versions отказываются.
- `prepared` сохраняется независимо от наличия canonical payment. В fixture
  первая подготовка дошла лишь до RU/NL1; NL2 остаётся неподготовленным. Это не
  разрешение исключить RU, очистить pending markers или завершить payment.
- Native applied receipts проверяются по revision/identity/registration и denial.
  Boot/deadline проверяются типами и declared capture clocks; same-boot deadline
  не может быть дальше capture monotonic+120s. Старый boot/истёкшие leases не
  обновляются. Capture metadata прямо помечена synthetic/not-live-attestation.
- Mailbox `members.json` должен иметь точный canonical chat sequence/member set;
  истёкший snapshot сохраняется как anti-replay floor, но не разрешает доступ.
  Settings/static pilot list, bootstrap/destination, controller chat-node,
  private node identity и volume marker согласованы. Static identities вне
  canonical member set, lagging/ahead sequence и неизвестные варианты fail closed.

Receiver роль содержит13 artifacts, весь capsule35. Maintenance/profile state
остаётся **одной** opaque ролью. Adapter version и все artifact digests входят в
import fingerprint; старый R receipt не становится S. Если заново доверить capture
уже с потерянным prepared marker, формат сам не угадает прошлое: независимый
trusted checkpoint и старый import receipt отвергают подмену; custody ещё отдельный gate.

[Fixture/recovery](../scripts/control_ha_receiver_fixture.py) вызывает native
Gateway accept/prepare/readback/load/allowed и mailbox forced-command stale guard
только в temp каталогах. Engine snapshots, clocks и root/SSH entry condition
моделируются; реальные commands запрещены. Native mailbox stale guard вызывается
только до service/publish side effects. Root ownership, mounted volume, RNS config/
spool restoration и живой publisher/receiver handshake этим не квалифицированы.
Ни оплаченный доступ после reboot, ни новые leases не публикуются автоматически.

170 mandatory contracts /0 skips;53 focused checks /0 skips; exact44-table/82-row
import и44-table/87-row current recovery после новых business writes. Source fixture
удалён до восстановления. Older/equal mailbox sequence отклоняются, expired
membership отдаёт пустой список с сохранением файла/floor. Повтор native accept
не меняет caches/lease deadlines; reboot и каждый из двух clocks запрещают paid.
Более широкий routes run имеет одну старую fixture failure; подробности в evidence.
Receiver continuation проверяется на imported checkpoint. Последующее87-row
current DB restore не означает нового согласованного external capture после
business writes: membership/receiver publications для него ещё не квалифицированы.

Следующий ограниченный шаг — maintenance/profile journals. Source inspection
показывает authenticated journal, permit/request/before/target/config hashes,
root-owned locator/metadata и отдельные renewal transaction/owner ledgers.
Pending/unknown нельзя объявить committed или очистить; path/owner revalidation
на другом host — отдельная часть recovery, не копирование inode metadata.
Full DR/live barrier/strict replication/HA-03..05 остаются незакрытыми.
[Runbook](../deploy/control-ha/README.md#ha-02s-receiver-safety-adapter) ·
[Evidence](releases/2026-11-23-control-ha.md#ha-02s--receiver-safety-adapter).

## HA-02T — bounded maintenance journal preflight

[Maintenance-v1](../scripts/control_ha_maintenance_v1.py) добавляет strict,
read-only preflight поверх Q/R/S. Это **ограниченный формат**, не универсальное
восстановление maintenance и не команда resume. В лабораторном capsule последняя
opaque роль заменена четырьмя документами: capture и по одному native journal
на RU/NL1/NL2; всего38 artifacts. Отсутствие opaque probes не означает full DR.

Поддержан canonical locator v1 / configuration v2, один bounded operation на узел,
один publisher contract и явно объявленное отсутствие отдельных renewal ledgers.
Legacy configuration, несколько/ноль операций, неизвестные поля/форматы и любой
coordinator/online-node ledger отказываются; **удалять их ради прохождения нельзя**.
Это pinned synthetic variant, не census фактического содержимого рабочих хостов.

Проверки до любых PostgreSQL или host-material writes:

- HMAC journal, точные permit/request/before/target/configuration hashes, набор
  operation files, attempt budget и согласованность state/replace/commit/receipt.
- Native floor/exact-CRL transformation; signature/issuer/family/gateway/revision,
  leaf/private-key correspondence, validity на исходном capture и revocation.
  Текущий CRL связан с проверенным issuer material capsule. Это не TLS/Go acceptance.
- Абсолютные нормализованные paths без traversal/overlap, раздельные control и
  publisher domains, UID/GID/modes, parent chain, сохранённые inode/lock hashes,
  locator/config contract, publisher digest и directory generation checkpoint.
  Declared metadata проверяется на согласованность, не выдается за live attestation.
- COMMITTED/IDEMPOTENT требуют точного target profile и readback receipt.
  PREPARED/APPLYING/UNKNOWN/CONFLICT/ROLLED_BACK можно аутентифицировать как evidence,
  но они блокируют строгий import. Ни один state не очищается и не повышается в PASS.
  Неизвестное/неполное evidence также блокирует импорт, а не становится empty state.
- Adapter version входит в atomic import identity: прежний S receipt не становится T.
  Изменённый журнал отвергается прежними независимым checkpoint/import receipt.
  Новый доверенный checkpoint не доказывает, что более ранние журналы не потеряны.

[Root fixture](../scripts/control_ha_maintenance_fixture.py) работает в отдельном
networkless read-only контейнере с tmpfs, без host state/docker-socket mount.
Монтируется отдельная копия выбранных tracked Python sources/manifests, не весь
checkout: ignored state, ключи, backups и Git metadata не передаются. Symlink и
traversal в source selection отказываются; эти guards также проверяются тестами.
Настоящие Locator/ProfileStore/Operation создают PREPARED и COMMITTED журналы,
выполняют floor и exact-CRL операции. Native retry идемпотентен; другой owner/mode,
symlink, заменённый lock inode, отсутствующий journal, новый operations inode после
копирования и истёкшая directory отказываются. Подписи и private keys синтетические.
Generated source удаляется до restore; восстановленные документы остаются private
evidence, не устанавливаются на исходные paths и не исполняются.

187 mandatory real-PG contracts /0 skips; PostgreSQL17.11:44 таблицы/82 строки
после import,87 после новых business writes; SIGKILL/current exact/stale refusal
и cleanup PASS. Семантическая проверка maintenance относится к исходному capture;
87-row DB restore не является новым согласованным file capture после business writes.
Wrapping key/checkpoint остаются в памяти; off-host custody/full restore не закрыты.

**Остаток первого из четырёх блоков HA-02:** отдельные renewal coordinator и
online-node ledgers, поддержка установленных вариантов/истории и безопасная
host reconciliation при изменении path/inode. Нельзя переподписать metadata или
очистить неизвестную операцию только для успешного resume. Остальные три блока —
live schema/writer barrier, полный backup/current-state recovery/custody и strict
replication/RPO0 — не выполнялись. Stage2/5, production RU dependency сохраняется.
[Runbook](../deploy/control-ha/README.md#ha-02t-bounded-maintenance-journal-preflight) ·
[Evidence](releases/2026-11-23-control-ha.md#ha-02t--bounded-maintenance-journal-preflight).

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
| `support_admin.py`, `support.py` | Admission-file + grant + audit consistency; support sender bindings | HA-02F admin и HA-02H sender DB synthetic PASS; FIELD/support file publication/fencing pending, PG publication refused before file I/O |
| `referrals.py` | Sponsor-bound request idempotency, pool/daily limits, proof/link и claim/invitation в одной транзакции | HA-02D synthetic PASS; full import/production wiring pending |
| `chat.py`, `chat_service.py`, `chat_sync.py` | Chat identity/proof, directory sequence, service sender revoke; filesystem exports | HA-02H DB synthetic PASS; mailbox/SSH/file publication and HA-03 fencing pending, PG publication refused before I/O |
| `restricted.py`, `restricted_admin.py`, `readiness_receipts.py` | Grants, отдельные restricted challenges, certificates, readiness, CRL sequence | HA-02F/G DB и HA-02J CRL sequence/immutable outbox synthetic PASS; distributed file publication, issuer fencing и production wiring pending |
| `restricted_maintenance.py`, `restricted_sync.py`, `paid_canary_crl.py` | HMAC journal, local flock, signed directory/CRL, publication/receipt ordering | HA-02J local lab file-failure/reconciliation PASS; existing SQLite-only journals unchanged, distributed publication/remote ACK require HA-03 fencing |
| `gateway_routing.py`, `gateway_selection.py` | Assignment versions, operation IDs, append-only events, atomic projections | HA-02I DB synthetic PASS; signed-file recovery, production HTTP/CLI wiring and fencing pending |
| `technical_metadata.py`, `geoip.py` | Отдельная SQLite, consent epoch/sequence/digest, revoke tombstone, retention, no resurrection | HA-02K canonical DB contracts/recovery synthetic PASS; live отдельная SQLite unchanged, multi-store import/collector wiring/physical-erasure policy pending; GeoIP ephemeral read-side не перенесён |
| `diagnostics.py` | Отдельное хранилище snapshots, ограничения данных/retention | HA-02L canonical DB/recovery synthetic PASS; live separate SQLite unchanged, HTTP/CLI/worker wiring, cross-store import and physical-erasure policy pending |
| `notices.py` → `scripts/service_notices.py` | Отдельная notices БД, publisher roles/revisions и exports | HA-02M canonical DB authority/recovery synthetic PASS; live SQLite unchanged, HTTP/CLI/import pending; canonical export refused until HA-03 fenced publication |
| `profile_store.py`, `pseudonyms.py`, generated membership/catalog files | Private authority versus derived copies; atomic file replace/fsync; local locks | HA-02N source inventory +123 focused tests PASS; live writer census/activation/fencing pending; [точные границы](control-ha-files.md) |
| `deploy/friends/awg-gateway.py`: `peers.db`, transport receiver state | Stable public-key/row-ID/IP allocation and allocator sequence; durable prepared/denied/floor state | HA-02N distinguishes node-local authority from cache; remains node-scoped, not imported into the control DB or reconstructed from public keys |

`transport_gateway.py` содержит node-local decision/prepared/denied/receipt state:
это не новый master канонической БД, но его safety state нельзя просто удалить.
Mailbox membership file также хранит receiver sequence. Panel Django/Postgres —
read-side projection, не grant authority; operator queues/cursors нельзя терять. Root/release
signing keys не входят в migration и остаются офлайн.

## HA-02V — combined online renewal capsule

[Combined preflight](../scripts/control_ha_online_capsule.py) combines Q/R/S/T/U,
not a bypass of T's empty-renewal requirement. A new versioned maintenance inventory
contains the four bounded documents, five byte-exact U documents under fixed lowercase
logical names, and a binding manifest. Each bounded capture explicitly declares the
same renewal digest. Native HMAC journals, permits, plans, owners, archives and receipt
bytes remain unchanged; only the synthetic capture inventory declaration is extended.
The manifest pins all four source-store and issuer-part hashes plus the checkpoint ID.
It is not its own trust root: the separately supplied Q checkpoint pins the AEAD
ciphertext, anchor and canonical snapshot; Q validates runtime key, delegation and CRL.

The wrapper requires one fully COMMITTED online operation and settled bounded
journals on every node. U still verifies all-three-node decisions, receipts and archive
ledgers. V then compares the canonical devices, invitations, grants, certificates and
CRL sequence with the native grant-plan after-state, row-for-row, including revoked
and expired records. The current delegation/CRL and primary directory must match the
same native candidate/publication receipt. Matching sequence or issuer name alone is
insufficient. R/S external files and receiver safety remain mandatory. The stronger
adapter identity joins the atomic import provenance; an old weaker receipt cannot
be promoted to a combined qualification by repeating import.

[Fixture](../scripts/control_ha_online_fixture.py) produces a native two-gateway
online renewal using the very same issuer, registry and devices as the four-store
application fixture. Three separately owned root-container bounded profile consumers
are captured against that issuer/CRL. They are synthetic separate paths, not a claim
that these paths or all consumers exist on RU/NL. RPC/readers/barriers remain simulated.
The44-artifact capsule has no opaque probes, but covers only this pinned variant.

[Tests](../tests/test_control_ha_online_capsule.py) and the
[owned rehearsal](../scripts/control_ha_online_rehearsal.py) cover exact encrypted
retention after deleting the original source, native DB/issuer contradictions, pending
state refusal, atomic rollback/retry, real PostgreSQL crash/restore, preserved new
writes and refusal of stale restore or old import after new writes. Private journals
are recovered as evidence in a700/600 directory, never installed into original paths.
The service/keys are reconstructed from the capsule; wrapping key and checkpoint
are still retained in memory, not recovered from an off-host custodian.

Pending evidence can be encrypted and preserved by Q, but V refuses importing it.
Post-renewal DB drift, unsupported history, offline/emergency archives and unknown variants are
not normalized, deleted or re-signed into acceptance. Even a valid standalone U
inspection is insufficient to bypass V. Expiry is never extended for recovery.
No host commands, remote reads, writer barrier, activation or automatic resume occur
in preflight. This is NOT full DR or permission to relocate a lock/journal.

### Retained online history

The explicit `bounded-and-online-renewal-history/v1` inventory and v2 capsule
adapter extend this gate to two through eight fully completed online operations.
The original single-operation path remains strict and rejects this format.
[Native retention](../deploy/friends/restricted/maintenance/online_history.py) saves
the predecessor coordinator's transaction, plan and last receipt as exact bytes in
private `history/<operation>.json`, with content hashes, before replacing the current
transaction. The operation lock covers retention and transition; file and parent
directory fsync precede the transition. Exact retry after interruption is idempotent;
conflicting bytes, unsafe files, reused IDs and capacity exhaustion refuse. A not-due
attempt creates no history. Native history is never pruned automatically (4096 limit).
This is source-only; installing the new packaged module/config hashes is a separate gate.

[History inspection](../scripts/control_ha_renewal_history.py) preserves the entire
five-document capture, including full node ledgers/archives, in the same44-artifact
encrypted capsule. Every operation must occur in all three node completion ledgers
and have its exact coordinator evidence and manifest-verified node archives.
It validates each operation through U, including native signatures, decisions,
private-key/profile binding and runtime/publication receipts. Internal inspection
projections select a single ledger entry and coordinator container; they are NOT
replacement native files or an instruction to recreate historical inodes. Their
metadata comes from the retained container, not a new host attestation. Original
bytes remain unchanged in the capsule and recovered evidence directory.

Historical material is checked at its recorded terminal receipt time, bounded by
the current capture; current material still uses the current capture and Q's current
validity gates. No expiry or signature is rewritten. Strict chronological order,
same gateway cohort, both certificate/authority successor links, nondecreasing CRL
floors and retained revocations are required. Missing middle operations cannot be
hidden by deleting the matching ledger entries. Legitimate intervening registry/CRL
writes are not reconstructed from history: the latest operation still must match
all five current DB projections and issuer/publication bytes exactly. This does not
prove live writer completeness or an independently witnessed history prefix.

Qualification uses three real sequential native operations, two already historical
at final capture, then canonical import/crash/current restore with source removal.
The8-operation and1MiB-per-document bounds are fail-closed import limits, not a
claim that every4096-entry installed history fits. Larger histories, missing old
coordinator records, pending operations and offline/emergency modes refuse without
truncation or guessed reconstruction. A crash after retention but before transition
may leave a duplicate current predecessor; native exact retry is tested, capsule
import of that unresolved shape is not authorized. This closes the selected retained
online-history slice, not the journal block or installed-host recovery.

The following explicit adapter covers three completed native stopped variants;
it does not extend the retained-online-history format to mixed histories.
NEXT within the journal block: actual host reconciliation and installed-shape inventory,
including pre-existing histories without coordinator records. The other three HA-02
blocks and HA-03..05 remain separate gates; no automatic continuation into live work.
[Runbook](../deploy/control-ha/README.md#ha-02v-combined-online-renewal-capsule) ·
[Qualification](releases/2026-11-23-control-ha.md#ha-02v--combined-online-renewal-capsule).

### Completed stopped variants

The explicit `bounded-and-stopped-renewal/v1` declaration and
[capsule adapter](../scripts/control_ha_stopped_capsule.py) cover one completed native
operator-approved stopped renewal, planned offline authority handoff, or completed
online-emergency rollforward after revocation. This is not a generic interpreter or
an installed-host census. The existing single-online and retained-history gates remain
strict and do not silently accept this format. The capsule contains45 private artifacts:
the existing44 plus both published NL directories in `publication.json`. Its manifest
binds both payloads, all five native capture documents, all four stores, issuer material
and independent checkpoint. Both publication hashes must match the RU archive receipt;
each signed directory must belong to the correct family/gateway and be currently valid.
The primary directory, issuer and exact five-table grant-plan after-state must also
match the canonical snapshot, including revoked devices and certificates.

[Native validation](../scripts/control_ha_stopped_v1.py) requires COMMITTED, all three
acquired/quiesced nodes, explicit outage-gate attestation, exact prepared/current plans,
promotion reconciliation, CLEANED ledgers, complete hashed archives and before/staged
material. Native signature, authority/CRL floors, grants, profile/private-key bindings,
path/owner/mode metadata and completion timestamps are checked. Offline mode additionally
binds both authority requests to their previous authority and signed successors.
Emergency mode preserves the immutable parent COMMIT, all three parent archives/owners,
stopped handoff receipts, continuation ID, virtual successor plan and incremented CRL
floor. The parent inspection projection is derived only from retained native bytes;
it is not an invented historical coordinator file and is never installed or executed.

Important custody limit: native archives do not retain the original signed offline
handoff envelope or the original operator-approval object. Candidate authority signatures
and recorded gate/request bindings can be checked, but missing authorization evidence
cannot be fabricated, re-signed or replayed as permission for a new outage. The adapter
explicitly reports `approval_replay=NOT_AUTHORIZED`, `host_resume=NOT_AUTHORIZED` and
`activation=FORBIDDEN`. Declared metadata is not a live-host attestation.

Unfinished operations remain byte-exact authenticated Q evidence but refuse strict
import. Expired recovery, fenced rollback, mixed/multi-operation stopped histories,
scheduled/zero-session gates, service-bearing installed archives and incomplete legacy
history are outside this format and refuse; no ledger is emptied to make them fit.
Existing Q/R/S/T checks still run; import provenance includes this stronger adapter,
so a weaker prior import receipt cannot be upgraded by retrying it as stopped evidence.
The three-mode rehearsal uses native operations, then removes original sources before
canonical import/crash/current-state restore. Captured RPC/readers are simulated and
bounded root operations run in owned containers; no installed runtime is claimed.

NEXT is read-only installed-shape inventory/host reconciliation, not another speculative
variant or deployment. Determine the actual journals and missing custody evidence before
defining a relocation gate. The other three HA-02 blocks remain open. Before cutover,
rollback is disposal of owned lab resources; after canonical writes, fence and recover
current state, never restore an older SQLite/profile snapshot.
[Runbook](../deploy/control-ha/README.md#ha-02v-completed-stopped-variants) ·
[Qualification](releases/2026-11-23-control-ha.md#ha-02v--completed-stopped-variants).

## HA-02U — online renewal evidence

[Renewal-v1](../scripts/control_ha_renewal_v1.py) — отдельный read-only inspector,
не runtime importer и не resume API. Сам U не расширяет T: nonempty renewal ledgers
требуют отдельного совместного V gate с issuer/DB state, описанного выше.
Пять bounded документов содержат capture, coordinator и RU/NL/NL2 state; один
retained online operation. Независимый ожидаемый digest и trust anchor передаются
отдельно. Hash внутри самого архива не заменяет доверенный checkpoint; этот digest
не шифрует private keys и не квалифицирует off-host custody.

Проверяются native transaction/owner, immutable COMMIT/ABORT и fencing counters,
all-three-node cohort, canonical plan, grant plan, подписанные authority/leaf/CRL
двух gateway identities, CRL continuity, key/profile binding, staged/before floors,
prepared/published/delivery/reconciliation receipts, completed ledger и manifest
каждого архива. Mixed active/archive files при прерванном cleanup сохраняются;
collision, missing file, hash/decision mismatch и неизвестные варианты отказывают.
Отсутствие owner/ledger до acquisition помечается `ABSENCE_UNPROVEN`, не «чистый узел».
COMMITTED coordinator без подтверждённых архивов всех трёх узлов не проходит.

Evidence содержит declared state-directory и file device/inode/owner/mode, включая
lock. `compare_same_host` сравнивает **весь** checkpoint без исправлений и возвращает
только `UNCHANGED_EVIDENCE_ONLY`, `host_resume=NOT_AUTHORIZED`. Никакого чтения живого
хоста, SSH, SQL, chmod/chown, re-sign, reload или исполнения операции нет. Даже PASS
не защищает от изменений после capture: настоящая аттестация/locks/barrier и
контролируемый new-host reconciliation остаются отдельным gate.

[Tests](../tests/test_control_ha_renewal_v1.py) используют настоящий ProductionController/
ProductionNode и cryptographic материал, но fixture RPC/readers/barriers вместо SSH,
Go runtime и systemd. На исходных disposable путях проверяются interruption до/после
решения, lost replies, частичное перемещение archive, precommit abort без rollback,
postcommit resume с тем же plan и revocation-triggered emergency/abort refusal.
Перенесённый state directory не считается прежним хостом. После удаления source
пять документов сохраняются byte-exact в700/600 evidence directory; activation
остаётся запрещена. Это не root ownership/runtime acceptance и не full DR.

Limits: one online operation only; retained multi-operation history, offline
maintenance, emergency handoff/rollback archives, installed variants and canonical
profile-locator reconciliation are not accepted by this version. Do not delete
legitimate history to fit it. Capture is synthetic, not a live absence declaration.
No new PostgreSQL gate is claimed: this change neither imports nor changes DB code.
Current capsule remains T's38-artifact fixture. Results, exact source checkpoint
and rollback are in the [dated report](releases/2026-11-23-control-ha.md#ha-02u--online-renewal-evidence).

## Следующие gates

1. Использовать [HA-02N source inventory](control-ha-files.md), HA-02P pinned adapters
   и HA-02Q/R/S/T encrypted bundle/role adapters. T проверяет один canonical bounded
   maintenance journal на узел; U проверяет online-renewal evidence, V связывает
   один completed вариант с canonical capsule/issuer/DB. История/установленные
   offline/emergency варианты и host reconciliation ещё не квалифицированы.
   Незавершённые операции и потерянные floors должны блокировать recovery, не очищаться.
   Отдельно квалифицировать key/checkpoint custody и полный consumer/node census.
   До live cutover отдельно сверить установленные схемы/версии и
   effective writer/CLI/timer census и consistency barrier; live notices/metadata/diagnostics
   остаются отдельными SQLite до согласованного cross-store import/collector/worker cutover.
   Distributed CRL/file publication отдельно зависит от HA-03 fencing. Не допускать mixed backend writers;
   synthetic membership не заменяет production wiring, deadline и package gates.
2. Сопоставить HA-02P поддержанный schema вариант с установленными source schemas;
   неизвестные варианты требуют отдельного adapter gate. Проверить snapshot consistency, nullable и
   INTEGER/TEXT/BLOB типы, sequence reseed, FK/unique/check/trigger parity. Сравнить
   все строки/три paid projections без вывода персональных данных. Не считать
   произвольный перенос SQLite DDL полноценной миграцией PostgreSQL.
3. Отдельный PostgreSQL/Patroni + etcd стенд: synchronous replication, strict
   no-quorum refusal, primary loss, повторное включение старого primary, RPO0 на
   подтверждённых payment/revoke/challenge/tombstone, bounded ACK-loss recovery.
4. Непустой полный backup/isolated restore и current-state recovery. Отдельные
   A–M наборы **лабораторных** таблиц — не backup всей системы; reverse import
   после новых записей не реализован. Старая pre-cutover копия не подходит.
5. После HA-03/04 — production preflight/shadow/sole-writer cutover по HA-05.

Откат текущего checkpoint: остановить только disposable стенд. Рабочие RU/NL,
registry, metadata, ключи и клиентские версии не менялись; восстанавливать их из
старого backup нельзя и не требуется.
