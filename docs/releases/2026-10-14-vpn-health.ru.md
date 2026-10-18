# VPN: read-only проверка14.10.2026

## Повтор18:43–18:44UTC /20:44 Brussels

Те же разрешённые RU/NL, read-only.41 активированное/37 действующих/4 отозванных
устройства;95 приглашений/41 использовано. +1 активированное и действующее с утра.
Это не уникальные люди.15.001с ресурсные окна,peer windows15.024с RU/15.208с NL.

| Метрика | NL | RU |
|---|---:|---:|
| Friends AWG configured |33|11|
| Handshake<5мин / <24ч |9 /20|0 /1|
| Peers с ростом transfer |9|1|
| Friends TCP established |0|0|
| CPU busy / iowait,% |14.74 /0|27.30 /2.09|
| RAM available/total,MiB |421/955|951/1962|
| Disk used/free |34% /13GiB|72% /8GiB|
| Disk busy,% /await,ms |0.01 /0.38|6.06 /32.18|
| External RX/TX,Mbit/s |3.2887/3.3202|0.0300/0.0416|

Основные AWG/TCP active. NL restricted-bootstrap **active since18:31:23UTC**,
NRestarts0. Три новейших observer receipts:16:01:06,16:16:09,18:31:14UTC,
RUN/CANCELLED; они не доказывают новые provider failures или устранение причины4008.
RU HTTP candidate active since18:31:27UTC. Кто/почему менял процессы — не выяснялось;
аудит ничего не перезапускал. Клиентский E2E и formal readiness NOT_RUN.

Internal gateway leaf16:16:06–20:16:06UTC14.10; issuer до15.10 11:01:34UTC;
CRL18:31:11–22:31:11UTC14.10. Credentials обновлены вне этой проверки.
HTTPS8443/status/server-load.json200 с TLS validation, оба gateway присутствуют;
публичный сертификат до19.10 12:07:37UTC. Peer-worker всё ещё unhealthy,
product/control/data-control healthy. RU latency32.18ms, сатурации в снимке нет.

Ни deploy/renewal/restart/reset-failed, ни room creation не выполнялись. Версии
построенных/установленных/публичных/invitation-page клиентов не перепроверены и не
менялись. Source-only gates неизменны. Только STATUS/PLAN/отчёт, diff whitespace
проверен; rollback не требуется. Дальше: worker/outbox, I/O history, restricted E2E
и своевременное обновление внутренних credentials. Утренняя причинная цепочка
остаётся историческим доказательством, не описанием текущего состояния.

## Утренний снимок (история)

Снимок10:24UTC /12:24 Brussels. Только разрешённые185.251.89.19 и186.246.45.246.
HEAD8d04632, входные незакоммиченные изменения сохранены. Ключи, профили,
идентификаторы устройств и IP клиентов не выводились. Основная SQLite прочитана mode=ro.

## Пользователи и нагрузка

40 активированных устройств,36 действующих,4 отозванных;94 приглашения,40 использовано.
С13.10 17:37UTC +3 активированных/+3 действующих устройства. Это не уникальные люди.

| Показатель | NL | RU |
|---|---:|---:|
| Friends AWG configured |32|11|
| Handshake<5мин / <24ч |8 /18|1 /1|
| Peers с ростом transfer |8|1|
| Peers без handshake за всё время |10|8|
| Friends TCP established443 /8446 соответственно |0|0|
| vCPU |1|2|
| CPU busy / iowait,% |10.66 /0|18.26 /1.41|
| Load1/5/15min |0.73/0.56/0.46|0.70/0.69/0.76|
| RAM available/total,MiB |438/955|916/1962|
| Swap used,MiB |0|541|
| Диск занято / свободно |34% /13GiB|72% /8GiB|
| vda busy,% / await,ms |0.03 /0.40|3.93 /16.55|
| External RX/TX,Mbit/s |6.1107/6.0404|0.0358/0.0617|
| AWG RX/TX,Mbit/s |0.0948/5.5214|0/0 (округлено)|

Окна ресурсов NL15.0006с/RU15.0016с, peers15.637/15.044с. Transfer включает
keepalive; handshake не гарантирует online. Peer counts разных шлюзов не суммируются.
Дополнительные NL pilot fcams4/fcawg31 1 peers без handshakes<24ч.
CPU/RAM/диск не насыщены в этом снимке; прежняя RU latency уменьшилась,
но это не доказательство устранения причины прошлых всплесков или capacity benchmark.

## Службы и TLS

Основные Friends AWG/TCP active на обоих узлах. RU product API/control/data-control
healthy, peer-worker Up2weeks(unhealthy); reconciliation/outbox не проверены.
RU HTTP candidate active since13.10 21:02:19UTC,NRestarts0; старый access inactive.
NL restricted-bootstrap **failed**,Result=exit-code,ExecMainStatus1,NRestarts9.
Последний запуск14.10 08:32:54UTC, выход08:33:09UTC. Повторный targeted systemd read
подтвердил failed при active AWG/TCP. Restart=always/30s не означает, что процесс
работает сейчас. Причина exit1/доступность restricted end-to-end не установлены;
сырой журнал с возможными чувствительными материалами не выводился. Не перезапускали.

Публичный GET HTTPS8443/status/server-load.json:200, TLS validation успешна.
В ответе оба шлюза:RU observed10:24:29/NL10:24:27UTC (11/13с на момент запроса).
Capacity200Mbit/s — provider-default-estimate, не измеренная пропускная способность.
Cert-renew success/exit0, завершён14.10 09:16:52UTC;
следующий timer14.10 21:12:36UTC. Сертификат notBefore12.10 20:07:38UTC,
notAfter19.10 12:07:37UTC, неизменный относительно вчерашней проверки.

## Проверки и оставшаяся работа

Изменена только документация STATUS/PLAN/этот отчёт; git diff --check без замечаний.
Read-only SSH/SQLite/systemd/proc/Docker/TLS; кодовые тесты и клиентский E2E NOT_RUN.
Нет deploy/restart/renewal/commit/push, rollback не требуется. Построенные,
установленные, публичные и invitation-page версии не изменялись и не перепроверялись.
Верхний engineering result остаётся source-only CRL barrier PARTIAL, writer deployment
readinessNO; этот аудит не выдаёт разрешение на rollout и не подтверждает его.
Осталось: диагностировать NL restricted-bootstrap exit1, peer-worker health/outbox,
наблюдать RU I/O, следующий TLS renewal и проверить клиентский end-to-end отдельно.
