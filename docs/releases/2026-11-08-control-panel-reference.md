# CONTROL-PANEL-REFERENCE-1 · 8 ноября 2026

## Результат и границы

Задача основана на main `501c94bd19d8039859fcac14940d2a8ebf07f5bb`.
Работа ведётся в отдельной feature-ветке; грязный основной checkout и параллельные
изменения сохранены. Итоговый head/CI/merge, installed image/source inventory,
свежие измерения и проверка сохранности закрепляются финальным receipt PR, без
косметического post-CI commit. Адрес панели: http://127.0.0.1:8765/.

Android121 не изменяется. Его техническое обновление принято владельцем как
исходный контекст; визуальный Android gate не закрывается веб-скриншотами.
Production policy/runtime, paid/cohort/identity/периоды, телефон, G4, renewal,
cold-entry и updater не затрагиваются.

## Карта объектов и данных

| Экран | Реальные источники и смысл |
| --- | --- |
| Обзор | Реестр, каноническая подписка, отдельные node observations; не synthetic/online/выручка |
| Устройство | Full HMAC production → одна устойчивая карточка; source версии, подписка, nodes, трафик, события |
| Сервер | RU/Amsterdam1/Amsterdam2, systemd/ресурсы, независимая TCP-проба, применение и обратные ссылки |
| Подписки | Прежние strict canonical snapshots; ссылки на те же устройства/узлы/события |
| События | Limited canonical APPLIED history и изменения наблюдений; одинаковый event не размножается |

Подписочный статус вычисляет только канонический `paid_beta` из pinned archive,
с одним snapshot/now. PostgreSQL не принимает решения о VPN. Сохранённый ответ,
последняя попытка и свежесть каждого блока независимы. При ошибке старое состояние
остаётся историческим и не превращается в noncohort/ноль. Noncohort — прежняя
политика допуска, не отказ за отсутствие оплаты. Поле activation не имеет даты;
первая запись и версия не объявляются датой активации/установки.

Node RX/TX: default-route Linux interface, не сумма пользователей. CPU: total/idle
ticks, не loadavg. AWG: проверенный node archive + точное retained public-key binding
и read-only transfer/handshake queries, без чтения private key и без вывода raw bindings
в веб-процесс. RX/TX относятся к стороне сервера. Сброс/перезапуск, gap>300s,
неудачная команда и первый снимок дают разрыв/неизвестность, не нули.
Повторный импорт идемпотентен. Схемы metrics1/inventory4/subscription2 сохраняют
прежние форматы. Новые наблюдения и event projection защищены PostgreSQL immutable
triggers; локальные названия — отдельная метадата оператора.

TCP per-user **NOT_COLLECTED**: свежая read-only проверка на всех трёх установленных
узлах подтверждает только Xray HandlerService, отсутствие policy/stats counters;
query статистики возвращает отказ, не пустое успешное измерение. Для отдельного
будущего источника потребуются StatsService, per-user uplink/downlink policy и
квалификация read-only сборщика без изменения транспортного допуска. Сейчас runtime
не меняется. MESH per-user **NOT_COLLECTED**: нет принятого источника с надёжной
device binding; сертификат/CRL и ранее открытые сессии не интерпретируются как трафик.

## Проверки

Референсы Virtualizor просмотрены локально, не публикуются. Перенесены сине-графитовый
каркас, sidebar, компактный header, светлее фон карточек, синие акценты, бирюзовые
линии, текстовые статусы. Не перенесены действия stop/console/payment.

Адресные проверки включают full-HMAC joins/похожий префикс, production/demo,
права/GET/no-store, append-only события и idempotence, проверенный архив canonical,
counter actual interval/reset/restart/gap/duplicates, неверные bindings и отказ query.
Существующие console/fleet workflow и независимая network probe сохраняются.
Обязательные checks: public-docs/source guard, built-panel Django check/migration
drift/locked PostgreSQL tests, hosted Control panel и остальные применимые workflow.

Миграции проверяются на отдельно восстановленной приватной копии панели. Браузер
Chromium после авторизации:1440×1000 и390×844, основные семь экранов, фильтры,
details, графики и реальные переходы устройство→сервер→то же устройство;
event→карточка/anchor; problem metric→отфильтрованный список→объект.
Пустые/stale/collection/import errors и длинные названия проверяются только
изолированными данными. Скриншоты, session cookies, Support ID, HMAC и receipts
сохраняются в закрытом комплекте, не в Git.

## Фактическая локальная приёмка

- Собранный allowlisted image: Django check и migration drift PASS, **248 тестов
  PASS** на PostgreSQL17/Python3.13. Старые synthetic workflow, permissions,
  immutable release/payment records и независимая network probe сохранены.
- Первый общий CI обнаружил неполный standalone fixture в
  `tests/test_control_plane_sources.py`: он копировал transport helper, но не новый
  metrics helper. Fixture теперь включает оба исполняемых источника; assertions
  запрета отправки/создания HMAC на NL сохранены. Все18 адресных source tests PASS.
  Это изменение тестовой упаковки, не panel/runtime payload; итоговый hosted
  результат относится к исправленному head и фиксируется в receipt PR.
- Приватный `pg_dump -Fc` восстановлен в отдельный PostgreSQL. Миграции0010/0011
  применены без переписывания старых наблюдений. Проверены исходные26769 registry
  snapshots и остальные прежние модели по cutoffs/хешам; UUID не используются как
  временной cutoff. Штатный seed обновил только `observed_at` демо-проекций, не
  их readback/идентичности/платежи. Пользователь и private pins/права неизменны.
- Панель установлена через прежний compose project, только console; внешние
  collector sources обновлены отдельно. PostgreSQL/volumes не пересоздавались,
  оба monitoring timers работают. Защищённые production devices/invites/paid
  subscriptions/events совпали по fingerprints до и после read-only работы.
- На14:53:48UTC8 ноября получены свежие canonical/history и три node snapshots;
  RX/TX/CPU уже имеют семь измеренных интервалов каждого узла. AWG привязан к
  реально наблюдаемым peers; количество bindings отдельно и не равно online.
  Точные динамические количества, source pins и installed inventory — в private
  receipt, окончательный source/merge и CI — в PR receipt.
- Авторизованный Chromium: семь страниц на1440×1000 и390×844, поиск, фильтры,
  технические details, hover/клавиатура/период графика. Проверены четыре маршрута:
  найти устройство и понять его доступ; устройство→сервер→то же устройство;
  событие→то же событие карточки; проблема обзора→список→затронутое устройство.
  JS errors/общего горизонтального переполнения нет; широкие таблицы прокручиваются.
- Отдельная копия: empty, active/grace/expired/revoked/noncohort, stale, ошибки
  collection/import, длинные метки и фильтры. Десять сочетаний сценария/ширины
  просмотрены в браузере; синтетические записи не импортировались в рабочую панель.

Визуальное сравнение подтверждает общий каркас и плотность референсов, не точную
копию Virtualizor: Family Connect показывает только доступные наблюдения. Длинные
идентификаторы/JSON спрятаны в details. Bootstrap-процесс MESH подписан именно как
bootstrap; это не проверка MESH-трафика. Первый одиночный rate sample показывается
точкой, пропуски не соединяются; прошлой истории счётчиков до установки нет.

## Эксплуатация

Источник текущих команд и метрик — [README панели](../../control_plane/README.md),
оплаты/точный replay — [операторская инструкция](../operators/subscriptions.ru.md).
Обновляется только локальная console и внешние collector sources. Пользователи,
секреты/HMAC/pins, volumes и наблюдения сохраняются; backup восстанавливается в
отдельной БД. Сбор counters не запускает/перезапускает VPN. Обычный адрес/авторизация
сохраняются. Таймеры зависят от бодрствующего компьютера; внешних alerts нет.

Ограничения: source/version metadata не аттестация; нет имени/модели/даты активации
из canonical registry; наблюдение handshake не online; нет TCP/MESH per-user bytes;
APPLIED не банковское подтверждение и не уведомление клиента. История ограничена
фактически импортированными событиями и явно показанными окнами. Новые клиентские
события по-прежнему обнаруживаются при открытии подписки/Refresh.
