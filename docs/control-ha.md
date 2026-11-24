# CONTROL-HA — отказоустойчивое управление

## Разрешение и текущая граница

23 ноября 2026 владелец поручил реализовать распределённое управление и
документировать весь переход. Это выбранная задача, не старая очередь ремонта RU.
Миграция поэтапная: пока её ворота не пройдены, RU остаётся каноническим источником.
Стенд, backup и успешный выбор лидера **не означают** готовность продукта HA.

24 ноября владелец расширил задачу: «дальше. работай до завершения 2 этапа».
Выбраны все четыре критерия HA-02, а не только очередной фрагмент журнала.
Это не переход к HA-03..05 и не разрешение скрыто переключить production backend.

База: существующая ветка `feature/device-technical-metadata-20261115`, checkpoint
`33b9cbdc`; основной checkout старый, с чужими изменениями и разошедшимся main.
Не переносить старый main на серверы, не делать force push. Принятые runtime-пакеты
сверяются отдельно перед любой установкой.

## Что переносится

| Область | Сейчас | Цель / обязательная проверка |
| --- | --- | --- |
| Идентичности, приглашения, challenge/proof | SQLite на RU; даже challenge пишет в БД | Согласованный журнал; proof нельзя использовать на двух API |
| Подписки, события, отзыв | SQLite, неизменяемые события | Нет потерянных подтверждённых событий; идемпотентный повтор |
| AWG/TCP | Локальные engines/watchers; RU рассылает решения | Решения только от действующего координатора |
| MESH, сертификаты, CRL, directory | Файловый журнал и flock координатора | Один fenced writer; сохранение floors, expiry и recovery |
| Клиентское API / bootstrap | Общий управляющий маршрут | Несколько доверенных endpoint без обхода проверки подписи |
| Метаданные устройств | Отдельный SQLite, добровольное согласие | Tombstone/revoke не теряется, старый payload не воскресает |
| Панель, мониторинг, уведомления | Проекции и отдельные процессы | Не источник разрешений; отказ панели не блокирует VPN |

`control/friends/access.py`, `paid_beta.py`, `transport_policy.py`,
`transport_reconcile.py`, `restricted_maintenance.py`, `technical_metadata.py`
содержат разные транзакционные/файловые границы. Копирование `access.db` и запуск
нескольких писателей запрещены. PostgreSQL панели не является канонической базой.

## Целевая архитектура

- Локальный агент каждого gateway управляет только своими transports.
- Три управляющих API без обязательного проксирования через RU.
- Отдельный канонический PostgreSQL: primary и две replicas. Patroni и трёхузловой
  etcd — кандидат переключения, не самописный consensus. Это не БД веб-панели.
  Synchronous commit/quorum и RPO0 проверяются отказами до cutover.
- etcd хранит координацию, не продуктовые SQL-таблицы. Потеря большинства запрещает
  новые управляющие записи. Minority/старый лидер не публикует разрешения/CRL.
- Получатели проверяют монотонную эпоху и revision при каждом изменении. Одной
  lease координатора недостаточно: старый процесс может ожить после сетевой паузы.
- Корневые/release signing keys остаются офлайн; серверные делегации ограничены.
  Продуктовые данные, backup, ключи и raw receipts вне Git/CI.
- Начальные роли RU/NL1/NL2 требуют проверки failure domains. Два NL в одном ЦОД
  не защищают от отказа этого ЦОД; нестабильный RU впоследствии можно заменить.

Сохраняем 8s operation / 12s watchdog / до120s paid AWG/TCP lease. Noncohort имеет
иной cache-контракт; не менять его молча. Долгая автономность изолированного узла
и немедленное применение глобальных блокировок одновременно невозможны.

## Этапы и ворота

1. **HA-01 — quorum/shadow стенд.** Три настоящих etcd процесса, тестовая CA/mTLS,
   loopback, синтетические данные. Потеря лидера, работа двух узлов, отказ записи
   и linearizable read без большинства, возврат без потери подтверждённых данных.
   Read-only SQLite fingerprints сравнивают snapshot и paid decisions при одном
   времени; это не replica/допуск и не вход production reconciler.
2. **HA-02 — каноническое хранилище.** Repository API для всех writers, миграция
   SQLite семантики/триггеров/идемпотентности/challenge; отдельная metadata БД и
   файловые журналы. PostgreSQL/Patroni стенд, shadow-import, сравнение всех таблиц
   и решений, concurrent-write/crash tests, непустой backup и isolated restore.
3. **HA-03 — fenced coordinator/receivers.** Epoch/revision, отказ старого лидера,
   отзыв/expiry, CRL/directory maintenance. ACK loss, disk-full/fsync stalls,
   clock skew, network partition. Никакого оживления старых файлов/ключей.
4. **HA-04 — API/клиенты.** Идемпотентные операции, multi-endpoint discovery,
   проверки подписи/сроков, enrollment/reconnect/subscription/support. Android и
   применимые desktop gates, совместимость старых клиентов и период перехода.
5. **HA-05 — production shadow/cutover.** Runtime/pins, ресурсы/порты/firewall,
   backup/restore каждого хоста. Сначала shadow без изменения допусков. Fenced
   перенос writer; отказ RU, старые/новые подключения, платеж/отзыв/renewal,
   возврат старого лидера. Измерить RTO меньше оставшегося lease.

Каждый завершённый этап: source/tests/docs commit, обычный push, проверка SHA.
Непройденный gate блокирует зависимый production шаг, не независимые тесты.

## Стадия внедрения на 23 ноября

**Сейчас HA-02, этап2 из5. Это подготовка исходников и изолированные проверки,
а не уже работающее распределённое управление.** Нумерация этапов не означает40%
готовности: интеграция, репликация, fencing и production acceptance ещё впереди.

| Этап | Состояние | Что остаётся до перехода дальше |
| --- | --- | --- |
| HA-01: quorum/shadow foundation | Лабораторный gate завершён | Не считать стенд установленным production quorum |
| HA-02: общее хранилище | В работе; A–T и отдельный U online-renewal evidence checkpoint проверены на стенде | Renewal capsule/history/host reconciliation; installed-schema/writer barrier; полный recovery/custody; strict replication/RPO0 |
| HA-03: единственный уполномоченный writer | Не внедрён | Epoch/fencing на принимающих узлах, запрет действий старого лидера и безопасная публикация файлов |
| HA-04: API/клиентский failover | Не внедрён | Несколько API endpoints, безопасные retries и клиентские compatibility/acceptance gates |
| HA-05: production shadow/cutover | Не начат | Актуальные backup/restore, guarded sole-writer switch, отказ RU/возврат узла, RTO и rollback |

Уведомления HA-02M имеют119 real DB contracts и exact16-table/26-row crash/restore.
Это лишь DB authority: публичные v1/v2 файлы не публикуются из нового backend.
Рабочие console5ce82415, Android126/catalog9 и отдельные SQLite остаются прежними.
RU пока остаётся точкой зависимости; восстанавливать/перенастраивать серверы этим
checkpoint нельзя. [HA-02N inventory](control-ha-files.md) различает DB authority,
private aliases/profiles, node-local allocator/receiver safety state и derived
leases/exports;123 focused tests PASS /0 skips. Это не live process census.
[HA-02O](control-ha-storage.md#ha-02o--synthetic-all-store-shape-import) переносит
четыре **лабораторных** SQLite образа в одной транзакции:30 data tables/34 rows,
43 таблицы/47 строк с markers/receipt.111 contracts /0 skips и97 regressions /0 skips;
SIGKILL/current restore и безопасный повтор PASS. Это storage-shape gate, не
адаптер реальных схем: часть данных — sentinels, внешние файлы — только декларации
ссылок. Следующий выполненный slice —
[HA-02P](control-ha-storage.md#ha-02p--application-sqlite-adapters):29 штатных source
таблиц и валидный совместный fixture без credential-sentinels;165 import contracts,
128 CRL regressions и98 consumers/runner checks, все без skips. Exact44-table
recovery сохраняет82 строки после импорта и87 после новых операций. Это один
поддержанный source schema вариант, не live census установленных схем.
[HA-02Q](control-ha-storage.md#ha-02q--encrypted-recovery-bundle) добавляет
зашифрованный комплект и проверку до записи:154 contracts и31 runner/file checks,
все без skips. После удаления исходного fixture новые issuer/referral objects
восстанавливаются из комплекта;44-table crash/current/stale recovery PASS.
Это ещё не полный внешний recovery: четыре роли — явно обозначенные byte probes,
остальные требуют дополнительных semantic bindings; wrapping key/checkpoint
пока сохранены в памяти стенда. Следующий ограниченный шаг — настоящие role adapters
и cross-authority проверки, а не включение PostgreSQL на серверах. Внешние ключи/
файлы нельзя восстановить из DB-only dump; fencing и client failover не установлены.

[HA-02R](control-ha-storage.md#ha-02r--external-role-adapters) закрывает следующий
ограниченный slice:161 contracts /0 skips и90 consumer/runner checks /0 skips.
Пять реальных форматов проверяются вместе с БД: aliases/HMAC, FIELD, sender,
signed routing и peers.db/settings трёх узлов. После аварии и удаления исходного
fixture сохранены история aliases, IP/ID и allocator high-water. Заменены две
из четырёх заглушек Q; maintenance/profile и receiver safety всё ещё не квалифицированы.
Ни полного DR, ни автоматического отказоустойчивого управления в production пока нет.
Следующий scope — эти два оставшихся формата, не установка PostgreSQL.

[HA-02S](control-ha-storage.md#ha-02s--receiver-safety-adapter) дополнительно
проверяет receiver safety:170 contracts и53 native transport/runner checks без skips.
Подготовка только на двух из трёх узлов, terminal denies и mailbox sequence floor
сохраняются после восстановления. Повтор/перезагрузка не продлевают paid lease;
истёкшая membership не даёт доступ и не удаляет floor. Это native file consumers
на стенде с моделируемыми clocks/engines, не применение на серверах. Журналы
maintenance/profile в S ещё не восстановлены; activation по-прежнему FORBIDDEN.

[HA-02T](control-ha-storage.md#ha-02t--bounded-maintenance-journal-preflight) проверяет
canonical bounded journal каждого узла:187 mandatory contracts без skips, HMAC,
profile/CRL floors, metadata/path/config bindings и запрет импорта pending/unknown.
Настоящий root-container доказывает отказ при потере journal, изменении owner,
lock/operations inode или symlink. Из capsule возвращается evidence, не host resume.

[HA-02U](control-ha-storage.md#ha-02u--online-renewal-evidence) отдельно проверяет
online-renewal coordinator и три node ledger/archive, включая потерянный ответ,
частичную очистку, precommit abort и postcommit resume на исходном стенде.
Сам U не importer; совместная capsule привязка реализована отдельным V ниже.
Сравнение точных bytes/path/inode само по себе не разрешает продолжение операции.

[HA-02V](control-ha-storage.md#ha-02v--combined-online-renewal-capsule) объединяет
bounded и online evidence с четырьмя БД и issuer в одной encrypted capsule.
Проверяются не только hashes: пять native DB projections, подписанный issuer/CRL
и опубликованный directory должны соответствовать той же завершённой операции.
Продолжение V добавляет сохранение coordinator history до замены текущей операции
и проверку цепочки completed online renewals; стенд выполняет три операции подряд.
Это synthetic qualification, не live inventory и не разрешение исполнить журналы.
Следующий V-adapter включает три completed native варианта: остановленное обновление,
плановую офлайн-смену authority и аварийный rollforward после отзыва устройства.
Оба опубликованных NL directory и parent emergency archive сохраняются целиком;
старое согласие на остановку не превращается в новое разрешение.

Оставшийся HA-02 учитывается четырьмя крупными блоками, не количеством букв:

1. **Журналы — частично:** bounded и retained completed online-history объединены
   с canonical capsule/issuer/DB; три completed stopped/offline/emergency варианта
   добавлены отдельно. Фактический census и opaque custody выполнены; проверка
   содержимого scheduled/service-bearing current operation добавлена на стенде.
   Read-only проверка трёх рабочих узлов связала config hashes/unit order с текущей
   операцией и подтвердила active RU API/NL gateway services. Обнаружено реальное
   расхождение: клиентские сертификаты обновились после renewal, старый baseline
   не является текущим снимком БД. Последующая read-only проверка подтверждает подписи,
   device/key/revision/expiry/CRL и привязку действующей all_activated policy для новой
   записи; удалённые сертификаты истекли. Это content compatibility, не восстановление
   использованного challenge/proof или истории оплаты. Строгое recovery equality
   не изменено. [Evidence](releases/2026-11-24-control-ha-certificate-delta.md).
   Исходное разрешение, согласованный installed capture
   и post-renewal recovery/host bindings ещё не закрыты.
   Целиком блок не завершён; результат content audit всегда BLOCKED для recovery.
2. **Рабочие схемы и writers:** live census и согласованный capture barrier не выполнены.
3. **Полное восстановление:** off-host key/checkpoint custody и актуальное recovery
   всей системы после новых записей не квалифицированы.
4. **Репликация:** PostgreSQL/Patroni strict quorum, primary loss/return и RPO0 впереди.

T не закрывает первый блок целиком и не меняет установленную архитектуру.

### Решение по исходному разрешению

24 ноября сверена именно установленная версияfcb31164:14-module digest совпадает
с наблюдением всех трёх узлов. Она принимает boolean schedule flag и сохраняет
вычисленный gate, а не исходный approval/config artifact. Проверенные семь сохранённых
материалов также не устанавливают это происхождение. Это ограниченный поиск, не
доказательство отсутствия любого внешнего backup. Без нового источника повторять
тот же поиск и добавлять тесты для восстановления отсутствующих bytes не следует.

Владелец явно одобрил второй вариант: разработку новой forward-only точки для
**текущего** состояния, пока без остановки служб и изменений серверов. Реализован
отдельный offline contract: Ed25519-подпись с отдельным domain, независимый request pin,
sequence/CRL floors, точные hashes нового recovery bundle и полного opaque custody,
идентичности issuer/source/config и обе публикации. Подпись разрешает только локальную
квалификацию; реальный signer/trust registry или production approval не создавались.

Старые журналы не переписываются и не исполняются; их исходный approval остаётся
NOT_ESTABLISHED. Существующий importer по-прежнему отвергает отличие от старого
renewal baseline. Новый тип результата не является import/resume permit. Pending
маркеры текущих операций блокируют квалификацию, а старые unknown/pending архивы
сохраняются без интерпретации. Отсутствие маркеров не доказывает остановку writers.

Проверены новый native certificate после renewal, точное чтение после удаления
источника, отказ повторного proof и свежая выдача из изолированной копии registry.
Это не полное восстановление всех installed stores. Последующее изменение закрывает
offline-проверку **обеих** публикаций: подписанные gateway/delegation bindings,
native directory validation на момент capture и проверки, общий CA/family/revision
и независимые floors последовательностей допуска. Свежее согласие не разрешает
перепутанный узел, просрочку или откат допуска; старый неполный request отвергается.
Теперь также обязательны сохранённые bytes node config и всех объявленных renewal
модулей RU/NL1/NL2: проверяются каждый hash, aggregate, slot/role, gateway IDs и anchor.
Один переданный вызывающим кодом hash больше не даёт source qualification. Локальный
сборщик не выполняет исходники и не следует путям из config; symlink/hardlink/FIFO,
лишние `.py` и наблюдаемая смена файлов отвергаются. Это узкая source-custody проверка,
не проверка полного runtime: controller config, API/binaries, зависимости и фактически
запущенный процесс не покрыты. Сохранённый fcb31164 проверен с synthetic configs.
Переносимый AES-256-GCM комплект объединяет точный подписанный request, обе уже
зашифрованные капсулы и public/source sidecars; ключи, trusted signer/anchor, pins,
время проверки и floors остаются снаружи. Чтение в новом процессе после удаления
исходников сверяет все bytes и повторяет forward-проверки. Native post-renewal тест
сохраняет отказ использованного proof и свежую выдачу. Упаковка не является approval:
срок действия не продлевается, никаких extract/import/resume-команд нет. Это ещё не
независимый off-host backup или долгосрочный production recovery.
Coherent capture, реальное происхождение source/config/живых публикаций, полный набор
gateway leaf/private keys и независимое off-host custody всё ещё не квалифицированы.
Следующий блок автоматически не выбран; maintenance/cutover требуют отдельного scope.
[Актуальный переносимый комплект и тесты](releases/2026-11-24-control-ha-forward-archive.md).
[Квалификация source custody](releases/2026-11-24-control-ha-forward-sources.md).
[Предыдущая квалификация публикаций](releases/2026-11-24-control-ha-forward-publications.md).
[Исходный контракт](releases/2026-11-24-control-ha-forward-checkpoint.md).
[Предшествующие доказательства](releases/2026-11-24-control-ha-provenance-decision.md).

### Когда заканчивается этап 2

На24 ноября календарный срок не подтверждён: журнальный блок, установленный capture
и полное независимое восстановление ещё открыты. Репликационный стенд квалифицирован.
Нельзя обещать «ещё один подпункт»,
выводить процент из числа букв A–V или считать количество тестов оценкой срока.
Остаток учитывается следующими четырьмя приёмочными результатами, без новых этапов:

| Блок | Условие закрытия | Состояние |
| --- | --- | --- |
| Журналы | Проверены фактические текущие inputs и основание доверия: исходное разрешение для старого пути либо отдельное явное разрешение на новый текущий checkpoint; legacy bytes сохранены без исполнения/выдуманной истории | Частично: opaque custody, signed forward contract и семантика обеих публикаций проверены offline; фактические authorization/source/capture bindings и coherent current-state recovery ещё не приняты |
| Схемы и writers | Сверены установленные схемы и все реальные writers/CLI/timers; получен согласованный cross-store снимок с проверяемым барьером, без смешанных писателей | Схемы34 живых таблиц сверены; отдельный адаптер сохраняет закрытую handoff-историю и floors. Полный census writers и live-барьер не квалифицированы |
| Полное восстановление | Все обязательные stores/files/ключи/checkpoints сохранены вне исходного узла; после новых подтверждённых записей выполнено изолированное восстановление актуального состояния и проверены rollback/отказ от старой копии | Не квалифицировано |
| Репликация | Стенд PostgreSQL/Patroni выдерживает потерю/возврат primary и кворума; без кворума записи запрещены, подтверждённые события не теряются (RPO0) | PASS в изолированном стенде: strict synchronous quorum, потеря/возврат primary, DCS minority/majority, запрет записи после истечения lease, блокировка без реплик; отменённый sync COMMIT не выдаёт ложный ACK. Не production/WAN qualification |

HA-02 COMPLETE — только совместный PASS этих четырёх результатов с точными evidence
и версией источника. По последнему запросу выбраны все четыре блока;
остаток — **журналы/фактическое состояние, установленный capture, полное восстановление**, не ещё
одна-две небольшие правки. Дата окончания не установлена: она зависит от реальных
схем/writers, проверенного recovery и отдельно согласованного окна capture. Одобрение
разработки нового пути не разрешает остановку writers. Недостающее старое разрешение
не надо заново искать для нового пути; его доверие устанавливается отдельно.
Новая обнаруженная проблема относится к соответствующему блоку, а не скрывается
новой буквой или ослаблением проверки. Разрешение завершить HA-02 не выбирает
последующие этапы. После HA-02 ещё нужны HA-03 fencing, HA-04 API/client failover и
HA-05 shadow/cutover; завершение этапа2 само по себе не убирает зависимость от RU.

[Репликационный стенд, найденная ошибка ACK, тесты и откат](releases/2026-11-24-control-ha-replication.md).
[Расширение до49 таблиц с сохранением handoff-истории и floors](releases/2026-11-24-control-ha-handoff-retention.md).
Этот же строгий профиль включён в зашифрованное восстановление и подписанный portable
forward archive:555 проверок без пропусков, импорт49 таблиц отдельным процессом после
удаления исходного синтетического каталога. [Evidence и границы](releases/2026-11-24-control-ha-handoff-recovery.md).
Это не заменяет согласованный live capture, независимое хранение реальных ключей и
полное восстановление фактического состояния; три открытых блока HA-02 не закрыты.

## Откат

До cutover останавливается только стенд/shadow; RU/NL не перезапускаются, БД из
старой копии не восстанавливается. После записей в новом хранилище возврат старого
SQLite запрещён: fence writers, сохранить/сверить новые подтверждённые операции,
затем forward recovery либо проверенная обратная миграция. RPO0 проверяется на
ledger, отзывах и challenge, не только числе устройств. После HA-05 нужен runbook
потери quorum, ремонта узла, CA renewal, backup restore и независимый мониторинг.
HA не устраняет причину локальных зависаний RU.

HA-02A/B/C/D/E/F/G/H/I: enrollment, paid ledger/subscription, synthetic all-node membership,
referral, Support ID, grant/audit, issuance/readiness и chat/support DB transactions, PostgreSQL crash/restore
стенд реализованы. HA-02B отвергает stale backup после новых payment/revoke/proof
записей и проверяет актуальный restore всех девяти лабораторных таблиц. Это не
production reverse migration: serving-set fencing, production wiring/deadlines,
остальные canonical writers, полный import/recovery и репликация остаются pending
и блокируют cutover. Частичный prepare сохраняет target deny после DB rollback;
обратное снятие fence не реализовано и не должно имитироваться старым cache.
HA-02D отдельно проверяет referral restore девяти лабораторных таблиц/18 строк,
сохранение подтверждённых приглашений/отзывов и отказ stale pre-claim backup.
Оба набора из девяти таблиц относятся к разным стендам, не к полному product backup.
HA-02E отдельно проверяет Support ID/наблюдения вместе с paid state:12 синтетических
таблиц/19 строк. Restricted grants/readiness — только read-side fixtures; перенос
FIELD grant/audit/CRL/admission-file writers этим не выполнен. PostgreSQL FIELD
операции явно запрещены до файловых побочных эффектов. Это не новый CLI backend.
HA-02F переносит grant/revoke/audit DB boundary:176 contracts,264 focused regressions,
точный restore12 лабораторных таблиц/20 строк. Pending audit не становится APPLIED
автоматически; потеря подтверждения grant требует readback, не слепого renewal.
На этом этапе FIELD file/CRL publication и certificate/readiness writers ещё не перенесены.
HA-02G отдельно переносит restricted challenge/certificate/auto-enroll и readiness
ACK/readback:163 contracts, точный restore16 лабораторных таблиц/36 строк. Одноразовые
proofs, paid expiry, owner/node binding и receipt retention сохраняются. Readback
использует read-only snapshot без writer lock. Ephemeral issuer keys при restore
сохранены в памяти, не восстановлены из backup: secret/authority recovery не доказан.
FIELD/CRL/file publication и replication остаются pending; backend для production нет.
HA-02H переносит chat identity/proof, service sender revoke, sequence и support binding:
114 contracts,238 regressions,18 final runner guards; exact restore15 lab таблиц/29 строк.
Support sender проверяется и привязывается в одной транзакции. Lease100s/cap120s,
membership550 и challenge8 не расширяются. Номера продолжаются, отозванный sender
не оживает после restore/replay. Политика и ephemeral keys удерживаются вне БД,
их recovery не проверен. PG mailbox/support-file публикация запрещена до I/O;
policy-file race, external ACK и общий publisher lock требуют HA-03 fencing.
HA-02I переносит sticky assignments, policy generation и explicit selection с общими
операциями SQLite/PG.111 contracts PASS; SIGKILL и current restore15 таблиц/28 строк,
stale restore refusal, append-only triggers и forward-only catalog rollback проверены.
Status/selection читаются без writer lock; потеря ACK не дублирует operation journal.
Это DB-only: подписанные файлы сохранены, а не восстановлены; HTTP proof consumption,
paid decision и SSH registration не стали одной транзакцией. Их failures/fencing и
production wiring остаются следующими gates; старый proof после commit не переигрывается.
HA-02J переносит CRL sequence и неизменяемый signed candidate в одну DB-транзакцию:
128 contracts PASS; SIGKILL/current restore19 таблиц/22 строки, stale backup refused.
После замены файла без DB receipt повтор использует ровно сохранённые bytes; потеря
commit ACK не дублирует кандидат. Expired/superseded candidate нельзя публиковать через
локальный lab-helper. Это не распределённая атомарная публикация: helper лишь для
одного lab writer, local receipt не доказывает удалённый ACK или epoch. Legacy SQLite
путь остаётся отдельно, PG/synthetic outbox запрещены в legacy sync/canary до I/O.
Issuer keys удерживаются, не восстановлены. Migration должна отдельно fence старые
writers; эта проверка marker не заменяет fencing, remote readback или HA-03.
HA-02K выделяет latest-only metadata, consent floors и retention в общий SQLite/PG
adapter. В canonical rehearsal proof consumption и запись теперь атомарны; legacy
двухфайловый путь не выдаётся за общую транзакцию.120 contracts PASS; SIGKILL/current
restore12 таблиц/26 строк, stale pre-revoke backup refused. Revoke tombstone остаётся
после TTL; старый duplicate не обновляет наблюдения, новый opt-in требует нового epoch.
Это logical retention, не доказанное физическое удаление из PG pages/WAL/backups.
Multi-DB snapshot/import, collector wiring и secret recovery остаются gates; никакие
клиентские метаданные/IP не читались, политика согласия и GeoIP collectors не менялись.
HA-02L переносит diagnostics proof/Support ID/latest snapshot в одну canonical
SQLite/PG транзакцию:113 contracts и217 focused regressions PASS,16 optional skips.
SIGKILL/current restore12 лабораторных таблиц/19 строк сохраняет подтверждённый prune,
report, used/pending proofs, revoke и paid state; stale pre-prune/revoke refused.
Legacy отдельная SQLite остаётся отдельной. Это per-report opt-in, не consent epoch:
duplicate текущего report не продлевает TTL, но новый signed request после expiry
по существующему контракту допустим. Не заявляется вечная deduplication/tombstone
или физическое удаление PG/WAL/backups. Notices/остальные writers и полный import,
privacy-aware backup/recovery, replication и HA-03..05 ещё не квалифицированы.
Ни один из этих стендов не включает replicated writer, epoch fencing или live failover.
[Точная граница и карта writers](control-ha-storage.md).

Результаты: [checkpoint 23 ноября](releases/2026-11-23-control-ha.md).
