# VPN — проверка 08.10.2026

Read-only SSH двух разрешённых шлюзов и публичный HTTPS,08:06–08:07UTC
(10:06–10:07 Europe/Brussels). HEAD8d04632, незакоммиченная работа сохранена.
Ключи, профили, строки БД и идентификаторы клиентов не выводились.

## Клиенты и ресурсы

Friends DB:31 активированное устройство,27 неотозванных,4 отозванных;
85 приглашений,31 использовано. К снимку07.10:+1 устройство/+1 приглашение.
Это устройства, не уникальные люди. Peers разных шлюзов не суммируются.

| Метрика | NL | RU |
|---|---:|---:|
| Open AWG peers |25|10|
| Handshake за5мин/24ч |5/12|0/0|
| Рост transfer за15с |4|0|
| Никогда не было handshake |3|8|
| Friends TCP established443/8446 |0|0|
| CPU busy/iowait,% |7.92/4.67|18.56/2.18|
| RAM available/total,MiB |499/955.3|1024.8/1962.5|
| Swap used,MiB |0|514.2|
| Disk used,% / free,GiB |29.9/12.78|71.2/8.04|
| External RX/TX,Mbit/s |0.0813/0.0196|0.0255/0.0166|
| AWG RX/TX,Mbit/s |0.0010/0.0015|0/0|
| Disk await,ms |11.14|32.87|

Handshake/transfer включает keepalive, не точный online людей. Короткий15с
снимок не capacity benchmark; CPU/RAM/диск относятся ко всему хосту.
Отдельные legacy/pilot WG интерфейсы не входят в счётчик open AWG.

## Службы

AWG/TCP обоих шлюзов active,Result success,NRestarts0. RU HTTP candidate active.
Public HTTPS8443/status/server-load.json HTTP200 с проверкой TLS.
Product API и control Docker healthy. Peer-worker Docker unhealthy,
failing_streak25614 при active systemd: причина и фактический outbox не проверены.
RU restricted-sync последний exit08:07:02UTC success,таймер active waiting.
NL restricted-bootstrap active,NRestarts5,последний старт06:40:21UTC;
причины перезапусков не установлены. Это не доказательство restricted E2E.
RU cert-renew последний exit07.10 21:08:11UTC success,таймер active.

## Версии и границы

Последний прочитанный deployment receipt:owner Android0.1.18-beta69/code69
и соответствующий NL gateway установлены, deployment gates PASS07.10;
последующий selected-retry FAIL остаётся отдельным результатом. Это история,
не свежая проверка APK/хеша процесса. Public/default версии и артефакты сегодня
не перепроверялись. Новых версий,сборок,публикации,signing,deploy,renewal,
изменений конфигурации или перезапусков нет. Rollback аудита не требуется;
существующий owner-pair rollback см.2026-10-07-rtp-identity-deploy-1.md,не выполнялся.
Кодовые тесты и физический client E2E не запускались. Осталось проверить worker,
причины restricted перезапусков,длительную RU disk latency и отдельно client E2E.
