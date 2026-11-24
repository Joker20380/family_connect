# RU: восстановление доступности и lifecycle-кандидат

## Раздельные результаты

Предсуществующий инцидент —
[PR14/comment6751072916](https://github.com/Joker20380/family_connect/pull/14#issuecomment-6751072916).
Установленная диагностическая база —
[PR15/comment6745387406](https://github.com/Joker20380/family_connect/pull/15#issuecomment-6745387406).
Повторная поставка paid123 отменена. Этот этап не меняет её статус и не является
новой пользовательской/Android/платёжной приёмкой.

**RU_RECOVERED,9 ноября2026:** после owner-разрешения сохранены минимальный snapshot,
исходные units, bytes, retained state и вторичная ошибка register19:14:14.
RU-only fence → stop watcher/AWG/TCP → MainPID/ControlPID0/no jobs → проверка
retained state → последовательный штатный start → снятие fence.
Failure-запись архивирована без перезаписи; ledger/state/cache/deny не восстанавливались
из старой копии, deadlines вручную не менялись.

Шесть actual/persisted readback-срезов за183.277s: RU20/20, NL1 49/49, NL2 5/5
AWG/TCP bindings, не количество онлайн-пользователей. Revisions согласованы,
paid leases продлены через исходную границу, PID/NRestarts стабильны. Пять обычных
центральных циклов22:35:43–22:37:57UTC: все три результата `applied`.
Protected identity/invite/cohort/subscription/event/period fingerprints совпали;
current возвращён только для108/119. HTTP/NL/центральные кодовые архивы не менялись.
Панель `/subscriptions/`: authenticated200/no-store, canonical/RU observed22:44:30UTC,
NL1 22:44:33, NL2 22:44:36, все источники `ok`. История ошибок сохранена.
Это конечное окно восстановления, не доказательство исправления причины аварий.

В production сохранены:

| Компонент | SHA256 / политика |
|---|---|
| RU node | `125c796a30c3fba1772c47b96963517350087ad04aad675b6f33a31a5383276c` |
| Gateway | `9023d2c3f7c3a5127d67c509a16eb2d974810ff54d5b76cc225cd9b93e0b4234` |
| Policy | `android-paid-108-119-v1` |

## FIRST_TRIGGER: неизвестен

Узкая выборка исходной invocation вернула последние восемь сообщений. Последний
доступный completed progress принят journal в19:13:50.963812UTC: total0.132590280s,
три engine queries, два file fsync/replace/directory fsync. Последний конкретный
вызов — directory fsync `attempt_result`,0.011315654s, completed, remaining на
входе7.879145960s. Следующий gap принят19:13:50.965493UTC, значение2.133594151s.
`_SOURCE_REALTIME_TIMESTAMP` отсутствует: времена приёма journal не выдаются за
точное время начала/окончания операции. Вложенные stages не суммируются.

Systemd state фиксирует выход engines из active19:14:03 и AWG timeout19:14:08.
Запись register19:14:14 — AWG-query/COMMAND_FAILED, returncode1, total0.050674438s;
это вторичный отказ уже остановленного движка. Исходного primary failure record нет.
Отдельная bounded indexed manager-events выборка достигла4s timeout. Точный
инициатор stop-job и первое watchdog/exit-событие не установлены; BindsTo объясняет
защитную зависимость, но не доказывает исторического инициатора.

HTTP start19:47:09 — последующее событие, не причина19:14 и не действие этой задачи.
В доступных416 верхнеуровневых локальных receipts соответствующая операторская
операция не найдена; это не доказательство отсутствия другой сессии. HTTP не трогали.

## Воспроизведение и выбранный контракт кандидата

1. **Restart-loop подтверждён** на точном PR15 node, реальном systemd/AWG/Xray,
   production base-unit/sandbox/drop-ins, синтетических63 canonical records.
   SIGKILL watcher вызывает зависимую остановку engines. `Restart=on-failure`
   ставит job только watcher; BindsTo/After не создают обратных engine start jobs.
   Новый watcher сообщает READY и ждёт выключенные engines, затем снова завершается.
   Два автоперезапуска воспроизведены за40.686/40.793s для active/terminal-denied
   состояний. Прямой запуск движков вместо systemctl не используется.
2. **Блокирующий diagnostic output подтверждён**: заполненные нечитаемые pipe и
   Unix stream socket удерживают старый `operation()` после завершённого тела,
   до возврата и следующего watchdog. Тест ограничен2s, ребёнок гарантированно
   удаляется. Это показывает возможный дефект, не причину production-инцидента.
   На exact pyz125c796a отдельный real-watch/operation probe с синтетическим
   завершённым apply получил только READY, без WATCHDOG и first-failure file.
   Новый путь возвращает WATCHDOG после завершения и сохраняет последующую ошибку
   до protective stop даже при нечитающем socket. Это не тест native actuation:
   её отдельное доказательство — real-systemd/native fixture.
3. Кандидат выбирает **RECOVERY_REQUIRED с ручным восстановлением**: `Restart=no`
   для watcher, остальные dependency/preflight/engine настройки неизменны.
   Это не автоматическое восстановление VPN. При отказе доступ закрывается;
   оператор после проверки причины выполняет согласованный stop/PID0/preflight/start.
4. Необязательные stderr-диагностики отправляются неблокирующим вызовом в journal
   socket или atomic-sized pipe, без изменения унаследованных blocking flags.
   Неподдерживаемый regular-file sink, переполнение/частичная отправка учитываются
   счётчиком `diagnostic_messages_dropped` на следующем успешном сообщении и в
   долговечном first-failure record. Stream records отделяются переводом строки,
   поэтому после частичного сообщения следующий полный JSON остаётся отделимым.
   Failure record и обязательные state/attempt/config commits остаются синхронными,
   с прежними fsync/replace/directory sync и commit-before-ACK.

Не добавляются cron, supervisor, отдельный heartbeat или новые пользовательские
права. Watchdog сообщается только после действительно завершённого apply;
operation8s/watchdog12s/lease120s, finite admission, expiry/revoke и single-writer
не ослабляются. Полную транспортную/Android/G4 матрицу не повторяем.

## Пакет и точная граница поставки

`scripts/package_ru_lifecycle.py` принимает только точный node125c796a,
gateway9023d2c3 и исходный watcher unit из sourcefa0ec71e. Nested delta — только
`control/friends/transport_gateway.py`; отдельная unit delta — только отказ от
автоматического watcher restart. Gateway, paid policy, остальные archive members,
HTTP/operator/reconciler/NL не входят в поставку. Historical packager PR15 сохранён.

Адресные проверки включают исполнение pyz в свежем isolated subprocess, штатные
unit/security регрессии, реальные positive/deny потоки и manual recovery,
повреждённый retained state без открытия доступа. Candidate systemd/native PASS:
active/terminal cases остаются RECOVERY_REQUIRED без рестартов в12.195/12.021s
контрольных окнах, затем проходят явное последовательное восстановление и реальные
positive/terminal-deny/noncohort HTTPS. Invalid-state preflight доступ не открывает.
Все собственные fixture containers/networks убраны. Итоговые hashes, точный source,
real-systemd результат и CI/merge фиксируются в PR receipt после завершения gates;
исторические результаты не переназначаются новым байтам.

Новый runtime **не установлен**. Для будущей отдельно разрешённой RU-only поставки:
exact pins/effective units → backup кода/units и retained evidence → RU-only fence
с продолжающимися NL leases → stop/PID0/no jobs → заменить node и watcher unit →
daemon-reload/preflight/sequential start → снять fence → actual/persisted/lease/panel
readback. Откат только к сохранённым code/unit/pin через тот же controlled stop;
никакого ledger/state/deny restore. После отказа кандидат сам доступ не восстанавливает.

Телефон, USB и probes не используются. USER_TRAFFIC/REAL_PAID_OPERATION — NOT_RUN
в этой операции; прежние датированные пользовательские PASS сохранены отдельно.
