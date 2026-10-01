# VPN: состояние01.10.2026

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
