# CONTROL-HA — отказоустойчивое управление

## Разрешение и текущая граница

23 ноября 2026 владелец поручил реализовать распределённое управление и
документировать весь переход. Это выбранная задача, не старая очередь ремонта RU.
Миграция поэтапная: пока её ворота не пройдены, RU остаётся каноническим источником.
Стенд, backup и успешный выбор лидера **не означают** готовность продукта HA.

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

## Откат

До cutover останавливается только стенд/shadow; RU/NL не перезапускаются, БД из
старой копии не восстанавливается. После записей в новом хранилище возврат старого
SQLite запрещён: fence writers, сохранить/сверить новые подтверждённые операции,
затем forward recovery либо проверенная обратная миграция. RPO0 проверяется на
ledger, отзывах и challenge, не только числе устройств. После HA-05 нужен runbook
потери quorum, ремонта узла, CA renewal, backup restore и независимый мониторинг.
HA не устраняет причину локальных зависаний RU.

HA-02A/B: enrollment, paid ledger/subscription и настоящий PostgreSQL crash/restore
стенд реализованы. HA-02B отвергает stale backup после новых payment/revoke/proof
записей и проверяет актуальный restore всех девяти лабораторных таблиц. Это не
production reverse migration: transport membership, остальные canonical writers,
полный import/recovery и репликация остаются pending и блокируют cutover.
[Точная граница и карта writers](control-ha-storage.md).

Результаты: [checkpoint 23 ноября](releases/2026-11-23-control-ha.md).
