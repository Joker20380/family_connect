# VPN: read-only проверка13.10.2026

## Повтор17:37UTC /19:37 Brussels

Read-only SSH на тех же двух разрешённых узлах;15.002с RU и15.001с NL.
Peer windows15.095/15.063с. HEAD8d04632, входные изменения сохранены.
SQLite:37 активированных,33 действующих,4 отозванных устройств;91 приглашение,
37 использовано — без изменений с утра. Это устройства, не уникальные люди/DAU.

| Показатель | NL | RU |
|---|---:|---:|
| Friends AWG configured |30|10|
| Handshake<5мин / <24ч |6 /14|0 /0|
| Peers с ростом transfer за окно |6|0|
| Friends TCP established443 /8446 соответственно |0|0|
| CPU busy / iowait,% |7.56 /0|24.06 /2.09|
| Load1/5/15min |0.45/0.53/0.53|0.93/0.78/0.75|
| RAM available/total,MiB |409/955|958/1962|
| Swap used,MiB |0|544|
| Диск занято / свободно |34% /13GiB|72% /8GiB|
| vda busy,% / await,ms |0.03 /0.43|5.11 /112.91|
| External RX/TX,Mbit/s |1.7626/1.5168|0.0279/0.0393|
| AWG RX/TX,Mbit/s |0.0671/1.3152|0/0|

AWG/TCP обоих узлов active. RU product/control/data-control healthy,
peer-worker Up2weeks(unhealthy). Утренняя RU сатурация диска не воспроизведена,
но высокая latency сохраняется. Это краткий снимок, не доказательство устранения
первопричины. RAM/CPU не исчерпаны; transfer может включать keepalive.
NL pilot fcams4/fcawg31 1 peers — без handshakes<24ч, отдельно от Friends.

HTTPS8443/status/server-load.json:200 с TLS validation, оба gateway присутствуют.
Observed RU17:37:37/NL17:37:33UTC, свежесть4/8с на момент запроса17:37:41UTC.
Capacity200Mbit/s остаётся provider-default-estimate, не результат benchmark.
Cert-renew Result=success/exit0, завершён13.10 09:11:44UTC;
следующий timer13.10 21:06:17UTC. Публичный сертификат notBefore12.10 20:07:38UTC,
notAfter19.10 12:07:37UTC. Утренний сбой не является текущим результатом службы.

RU HTTP candidate active since15:47:56UTC, NL restricted bootstrap since15:47:46UTC;
оба NRestarts0 текущего состояния. Это отличается от утреннего снимка;
причина/источник изменения и бинарные версии не устанавливались, не приписываются
этому аудиту. Актуальные верхние engineering entries — source-only CRL work,
writer deployment readinessNO; данный аудит не меняет acceptance/release gates.

Изменена только документация STATUS/PLAN/этот отчёт; git diff --check без замечаний.
Нет deploy/restart/renewal/commit/push, rollback не нужен. Версии построенных,
установленных, публичных и invitation-page артефактов не менялись/не перепроверены.
Кодовые тесты и клиентский E2E NOT_RUN. Остались RU I/O latency/history,
peer-worker reconciliation/outbox, E2E и наблюдение следующих renewal.

## Утренний снимок (сохранён как история)

Проверены только185.251.89.19 и186.246.45.246, около05:03–05:08UTC.
HEAD8d04632; многочисленные входные незакоммиченные изменения сохранены.
Агрегаты вычислены на серверах, ключи/профили/IP клиентов не выводились.

## Устройства и активность

Основная friends-access/access.db:37 активированных устройств,33 не отозвано,
4 отозвано;91 приглашение,37 использовано. Относительно01.10: +10 устройств
и +10 неотозванных. Это не уникальные люди; pilot DB не включены.

| Метрика | NL | RU |
|---|---:|---:|
| Friends AWG настроенных peers |30|10|
| Handshake<5мин / <24ч |5 /15|0 /0|
| Peers с ростом transfer |3|0|
| Никогда не было handshake |11|8|
| Friends TCP established (443 /8446 соответственно) |0|0|
| vCPU |1|2|
| Load average1/5/15min |0.24/0.33/0.35|0.73/0.89/0.93|
| RAM available/total,MiB |457/955|978/1962|
| Swap used,MiB |0|542|
| Диск занято / свободно |34% /13GiB|72% /8GiB|

NL выборки: CPU busy12.62% затем8.45%; iowait33.89% затем0%.
NL external RX/TX примерно5.84/5.33Mbit/s во второй выборке, AWG TX4.87Mbit/s.
RU первичный CPU14.66%,iowait79.3%; из-за задержек команд окно этого замера
длиннее15с, сетевую скорость RU из него не публикуем. Это не benchmark capacity.
Handshake не гарантирует online; transfer включает keepalive. Gateways не суммируются.
Дополнительные NL pilot interfaces fcams4 peers/fcawg31 1 peer: свежих handshakes0.

## Службы и проблемы

AWG/TCP обоих узлов active. NL AWG NRestarts1, active с10.10;
restricted bootstrap active,NRestarts3 — это счётчики systemd, не частота сбоев.
RU старый access unit inactive; HTTP candidate active с10.10 21:41:29UTC.
GET https://185.251.89.19:8443/status/server-load.json вернул200 с проверкой TLS;
JSON содержит только RU (observed_at13.10 05:05:18UTC), NL отсутствует.
Значение capacity200Mbit/s — provider-default-estimate, не измерение.

RU cert-renew failed/Result=timeout: запуск12.10 21:00:14UTC, таймаут21:05:14UTC,
окончательный failed21:06:12UTC. Предыдущий запуск12.10 09:22:06UTC renew passed.
SSH banner один раз истёк по10с таймауту; чтение журналов/Docker затягивается.
Высокий I/O wait наблюдался, корневая причина не установлена. Службы соседних
проектов не проверялись и не изменялись.

## Изменения, проверки и дальнейшие действия

Только документация; код, версии, установленное ПО, публичные каталоги и invitation
page не изменялись. Текущие binary/catalog версии в этом аудите не перепроверены.
Последняя верхняя запись STATUS: supervisor candidate локально принят, NOT_DEPLOYED;
не считать его установленным. Нет commit/push/deploy/restart, rollback не требуется.
Проверки: read-only SSH, агрегаты SQLite mode=ro, systemd, /proc, HTTPS/TLS.
Кодовые тесты и физический end-to-end не запускались.
Остались: RU disk latency/I/O причина, Docker health, cert renewal follow-up,
NL telemetry omission, клиентский end-to-end, история DAU/retention.

## Контрольный замер и завершение

Отдельный RU замер с согласованными границами15.0007с: CPU busy28.41%,
iowait68.93%,vda utilization94.00%,средний await67.71ms. Высокая занятость диска
подтверждена; источник I/O и влияние на каждый клиентский запрос не установлены.
Публичный TLS сертификат действует09.10 08:26:52–16.10 00:26:51UTC.
Docker ответил с задержкой: product API/control/data-control healthy;
peer-worker Up13days(unhealthy). Его reconciliation/outbox не проверены.
Повторный ограниченный journal read завершён timeout124; основной read журнала
успешен. Агрегаты SQLite подтверждены отдельным повторным read-only запросом.
Документация проверена git diff --check; никаких исправлений live не выполнялось.
