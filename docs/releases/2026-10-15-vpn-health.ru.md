# VPN: read-only проверка15.10.2026

06:13–06:14UTC /08:14 Brussels. Только разрешённые RU185.251.89.19/NL186.246.45.246.
HEAD8d04632; входные незакоммиченные изменения сохранены. Агрегаты SQLite mode=ro,
без вывода ключей/профилей/IP клиентов.41 активированное устройство,37 действующих,
4 отозванных;95 приглашений,41 использовано — без изменений с14.10 вечером.
Это не уникальные люди; peers разных шлюзов не суммируются.

| Метрика | NL | RU |
|---|---:|---:|
| Friends AWG configured |33|11|
| Handshake<5мин / <24ч |4 /20|0 /1|
| Peers с ростом transfer |3|0|
| Friends TCP established443 /8446 соответственно |0|0|
| CPU busy /iowait,% |12.35 /0|21.80 /1.51|
| Load1/5/15min |0.40/0.47/0.41|0.89/0.80/0.94|
| RAM available/total,MiB |396/955|1007/1962|
| Swap used,MiB |0|586|
| Disk used/free |35% /13GiB|72% /7.9GiB|
| Disk busy,% /await,ms |0.05 /0.51|4.30 /4.68|
| External RX/TX,Mbit/s |2.2398/0.7154|0.0312/0.0523|
| AWG RX/TX,Mbit/s |0.1815/0.4252|0/0 округлено|

Ресурсные окна15.002с NL/15.001с RU; peer windows15.276/15.033с.
Transfer включает keepalive; handshake не гарантирует online/DAU.
Сатурация ресурсов не наблюдается, но snapshot не доказывает устранение I/O spikes.

## Службы и restricted

AWG/TCP active оба узла; RU product/control/data-control healthy,
peer-worker Up2weeks(unhealthy), reconciliation/outbox не проверены.
NL restricted active since04:47:47UTC,NRestarts0; RU HTTP candidate04:47:50UTC.
В штатном обезличенном observer receipt03:36:55.545UTC новый fatal:
SEED_READ/HEARTBEAT_WRITE,exit_path=returned_error,elapsed4762719ms,cleanup completed.
Нельзя приписывать его прежнему WS_CLOSE4008: signaling_read отсутствует.
Последующие записи04:32:38/04:47:39UTC RUN/CANCELLED. Текущий active не означает
отсутствие ночного сбоя, полное восстановление или успешный клиентский E2E.

Internal leaf15.10 04:47:36–08:47:36UTC;issuer до15.10 11:01:34UTC;
CRL04:32:34–08:32:34UTC. Ближайшая граница проверенных материалов — CRL08:32:34UTC
(10:32 Brussels), затем leaf10:47 Brussels и issuer13:01 Brussels. Directory,
grants и полный readiness minimum не проверялись; сроки не гарантируют E2E окно.

HTTPS8443/status/server-load.json200 с TLS validation, оба gateway присутствуют.
Public TLS notAfter19.10 12:07:37UTC. Cert-renew Result=success; отдельный timestamp
последнего renewal в этой проверке не запрашивался. Capacity200Mbit/s в telemetry —
provider-default-estimate, не измеренная полоса.

## Изменения и оставшиеся проверки

Только STATUS/PLAN/этот отчёт; whitespace diff проверен. Никаких restart/reset-failed,
renewal/deploy/provider room creation/commit/push; rollback не нужен. Версии
построенных/установленных/публичных/invitation-page клиентов не менялись и не
перепроверялись. Верхний CRL engineering gate source-only/PARTIAL сохранён.
Кодовые тесты/клиентский E2E NOT_RUN. Остались worker health/outbox,
restricted HEARTBEAT_WRITE/stability, обновление credentials и история I/O.
