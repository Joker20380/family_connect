# VPN: состояние01.10.2026

## Повторный снимок17:43UTC / 19:43 Brussels

Read-only SSH на RU185.251.89.19 и NL186.246.45.246: параллельные15.01с выборки
17:43:34–17:43:50UTC. Агрегаты SQLite/peers вычислены на сервере без вывода
ключей, профилей, идентификаторов устройств или клиентских IP. Входной worktree
содержал чужие незакоммиченные изменения; они сохранены. HEAD при проверке29d15d7.

Friends access:27 активированных устройств,23 не отозвано,4 отозвано;
81 приглашение,27 использовано. Прироста с13:39UTC нет. Это не уникальные люди;
отдельные pilot DB не входят в этот счётчик.

| Метрика | NL | RU |
|---|---:|---:|
| AWG configured peers |22|10|
| Handshake<5мин / <24ч |5 / 12|0 / 0|
| Peers с передачей за15с |4|0|
| Никогда не было handshake |3|9|
| Friends TCP established inbound |0 (443)|0 (8446)|
| vCPU |1|2|
| CPU busy / iowait |9.92% / 5.26%|11.54% / 2.21%|
| Load average1/5/15min |0.26/0.35/0.35|0.89/0.98/0.84|
| Available / total RAM,MiB |532.6 / 955.3|1102.0 / 1962.5|
| Диск занят / свободно |24.9% / 13.69GiB|69.1% / 8.61GiB|
| External RX/TX,Mbit/s |5.0391 / 3.3859|0.0224 / 0.0200|
| AWG RX/TX,Mbit/s |0.1301 / 3.0046|0 / 0|
| vda await / utilization |144.26ms / 7.40%|34.33ms / 5.62%|

Признаков насыщения CPU/RAM нет; короткий снимок не измеряет capacity/SLO.
NL disk latency выше предыдущей выборки, причина не установлена. На RU621.9MiB
swap занято, активный swapping не измерен. Peers разных серверов не суммируются;
handshake не равен точному online/DAU, transfer может включать keepalive.
TCP — только моментальный счётчик Friends listeners, не уникальные пользователи.

AWG/TCP обоих шлюзов active,NRestarts0, даты старта прежние. RU access API active,
NRestarts0, current ActiveEnterTimestamp01.10 17:40:45MSK =14:40:45UTC: отличается
от13:39 снимка с30.09 03:28:04UTC. Причина/продолжительность возможного перерыва
здесь не исследовалась; NRestarts0 не доказывает отсутствие ручного restart.
Product API/control containers healthy; peer-worker systemd active, Docker unhealthy.
Не проверялись worker cycles/outbox, restricted units, HTTPS/TLS и client E2E.

Только документация: STATUS/PLAN/этот отчёт, git diff --check; кодовые тесты не нужны
и не запускались. Последний документированный restricted deployment attempt#4
17:13–17:15UTC завершился rollback; этот аудит его не повторял и не менял.
Обычный VPN не перезапускался. Rollout/rollback для read-only аудита не требуются;
путь прежней disk mitigation rollback — [отчёт29.09](2026-09-29-disk-io-recovery.ru.md).
Версии без изменений: последний документированный public Android0.1.18-beta51/code51,
Linux0.2.11,Windows0.2.15; private canary53 previously built, не новая установка.
Бинарники, установки, public/invitation links и каталоги здесь не перепроверялись.
Остались disk latency, worker healthcheck/outbox, причина изменения API start,
TLS/client E2E и измерение уникальных пользователей. Commit/push/FIELD-1 не выполнялись.

## Повторный снимок13:39UTC / 15:39 Brussels

Read-only SSH на двух разрешённых шлюзах, параллельные15с выборки с13:39:02
и13:39:04UTC. Агрегация peers/SQLite на сервере; ключи, профили, идентификаторы
устройств и IP клиентов не выводились. Входной git status чистый, HEAD e808f50.

Friends access:27 активированных устройств,23 не отозвано,4 отозвано;
81 приглашение,27 использовано. С утреннего снимка прироста нет. Это устройства,
не уникальные люди; отдельные pilot DB не включены.

| Метрика | NL | RU |
|---|---:|---:|
| AWG configured peers |22|10|
| Handshake<5мин / <24ч |4 / 12|0 / 0|
| Peers с передачей за15с |4|0|
| Никогда не было handshake |3|9|
| Friends TCP credentials / established |22 / 0|10 / 0|
| CPU busy / iowait |7.87% / 8.68%|25.16% / 2.96%|
| Load average1/5/15min |0.16/0.33/0.30|1.35/0.88/0.77|
| Available / total RAM,MiB |530.3 / 955.3|1107.3 / 1962.5|
| Диск занят / свободно |24.6% / 13.74GiB|69.1% / 8.62GiB|
| External RX/TX,Mbit/s |0.8703 / 0.8822|0.0221 / 0.0131|
| AWG RX/TX,Mbit/s |0.0307 / 0.7709|0 / 0|
| vda await / utilization |25.33ms / 9.38%|30.47ms / 6.95%|
| Uptime,дней |18.17|30.06|

CPU/RAM без признаков насыщения в этом коротком снимке; сетевой capacity benchmark
не проводился. RU swap занят638.8MiB, активный swapping не измерен. Disk latency
остаётся заметной, но ниже утренней выборки; это не доказательство исправления.
Peers разных серверов не суммируются; handshake не равен online/DAU,
transfer может включать keepalive. TCP только Friends443/8446, не все pilot listeners.

Обычные AWG/TCP и RU access API active,NRestarts0, даты старта прежние;
API30.09 03:28:04UTC. Product API/control healthy. Worker systemd active, Docker
unhealthy/restarts0 — ранее известное замечание, cycles/outbox не проверялись.
Дополнительно RU family-connect-restricted-sync.service failed/exit-code:
не сбрасывался и не перезапускался, причины новым аудитом не исследовались.
Последний документированный deployment01.10 — restricted canary FAILED/ROLLED BACK;
локальная timestamp repair не развёрнута. Этот статус не подменяется здоровьем
обычного VPN. [Deployment boundary](2026-10-01-5n-prov1-production-restricted-provisioning.ru.md).

Публичный GET /status/server-load.json на HTTPS8443 успешен с проверкой TLS;
snapshot timestamps RU13:39:33UTC/NL13:39:22UTC. В отдельном monitor sample
NL RX/TX2.613/2.752Mbit/s — трафик меняется между выборками. Configured200Mbit/s
остаётся provider-default-estimate, не подтверждённой ёмкостью канала.

Изменена только документация; серверы/службы/конфиги/БД не изменялись, rollback
этого аудита не требуется. Версии остаются ранее документированными:
Android0.1.18-beta51/code51,Linux0.2.11,Windows0.2.15; binaries, установка,
public catalogs и invitation page повторно не проверялись. Кодовые тесты и
client E2E не запускались. Остались disk latency, worker healthcheck/outbox,
причина прежнего API restart, история активности и клиентская E2E-проверка.
Restricted retry только отдельной авторизованной задачей; FIELD-1 не начат.

## Утренний снимок — сохранённая история

Read-only audit05:29–05:31UTC (07:29–07:31 Brussels), два разрешённых RU/NL
шлюза. Основной одновременный снимок05:31UTC,15с. SSH, /proc/sysfs,
AWG latest-handshakes/transfer с агрегацией на сервере, systemd/container
metadata, SQLite mode=ro/query_only, TCP established count и публичный HTTPS.
Не выводились ключи, профили, идентификаторы устройств, IP клиентов или browsing.

## Устройства и активность

Основная friends-access/access.db:27 активированных устройств,23 не отозвано,
4 отозвано;81 приглашение,27 использовано. По сравнению с30.09: +2 устройства,
+2 неотозванных устройства и +2 приглашения; прирост уникальных людей не доказан.
Отдельные pilot product DB не включены в эти числа. В основной схеме нет
времени регистрации устройства, поэтому суточные регистрации не заявляются.

| Метрика | NL | RU |
|---|---:|---:|
| AWG настроенных peers |22|10|
| Последний handshake<5мин |5|0|
| Последний handshake<24ч |11|0|
| Peers с передачей за15с |5|0|
| Никогда не было handshake |3|9|
| Friends TCP настроенных credentials |22|10|
| Friends TCP established inbound |0 (443)|0 (8446)|

Peers разных шлюзов не суммируются. Handshake — признак недавней активности,
не точное количество людей online/DAU; transfer включает keepalive. TCP —
моментальный счётчик входящих соединений указанных friends endpoints, не история
пользователей и не аудит всех legacy/pilot transport listeners.

## Ресурсы и службы

| Метрика15с | NL | RU |
|---|---:|---:|
| vCPU |1|2|
| CPU busy |4.75%|22.93%|
| iowait |1.34%|8.26%|
| Load average1/5/15min |0.18/0.18/0.18|0.71/0.69/0.65|
| RAM available/total,MiB |553.5/955.3|1091.1/1962.5|
| Диск занят/свободно |23.8%/13.90GiB|69.1%/8.63GiB|
| External RX/TX,Mbit/s |0.0298/0.0225|0.0242/0.0074|
| AWG RX/TX,Mbit/s |0.0093/0.0015|0/0|
| vda await/utilization |107.95ms/4.86%|71.73ms/17.27%|

CPU/RAM не перегружены в этом снимке; это не capacity benchmark/SLO.
На RU около618.3MiB swap занято; сам факт не доказывает активный swapping.
Высокая disk latency сохраняется при несатурированном диске; причина не установлена.
Первый RU15с в05:29UTC: CPU13.43%,iowait2.14%,await43.91ms — нагрузка меняется.
Первый NL аудит прерван отсутствием Docker; исправлен только временный локальный
сборщик, повтор успешен. Это не сбой NL VPN. Uptime RU29.72/NL17.83 суток.

AWG/TCP обоих шлюзов и RU access API active,NRestarts0; access API start
30.09 03:28:04UTC не изменился относительно предыдущего аудита. Product API/control
containers healthy. Peer-worker systemd active, Docker unhealthy, restart count0;
известный healthcheck mismatch не исправлялся, worker cycles/outbox не проверены.
Chat-sync/cert-renew oneshot inactive/Result=success; свежесть последнего запуска
и timers в этом аудите отдельно не проверены. Не считать inactive остановкой daemon.

HTTPS8443/status/server-load.json:200 с проверкой TLS. В05:31:28UTC snapshots
RU4.4с/NL17.4с, served certificate notAfter05.10 12:25:56UTC. Configured200Mbit/s
в мониторинге — provider-default-estimate, не измеренная пропускная способность.

## Проверки и дальнейшие действия

Изменена только документация: docs/public-source guard и git diff --check.
Кодовые тесты, performance/physical acceptance не запускались. Последний
документированный operational deployment — disk mitigation29.09; текущим аудитом
ничего не устанавливалось/не перезапускалось, rollback не требуется. Откат прежней
mitigation: [отчёт29.09](2026-09-29-disk-io-recovery.ru.md).
Ранее документированные версии Android0.1.18-beta51/code51,Linux0.2.11,
Windows0.2.15: binaries/installations/catalogs повторно не проверялись и не менялись.
Orchestrator PASS/history сохранены, repository HEAD/origin/main2644790 ранее
синхронизированы. Этот аудит не делает commit/push/deploy и не начинает FIELD-1.
Остались disk latency, healthcheck/outbox, причина прежнего access API restart,
история активности/TCP и client end-to-end. Уникальные люди/DAU/retention не измерены.
