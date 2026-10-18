# VPN: read-only проверка 07.10.2026

## Область

Разрешённые RU185.251.89.19 и NL186.246.45.246; SSH/HTTPS13:13–13:15UTC
(15:13–15:15 Europe/Brussels). По15с измерения, завершены13:14:56/13:15:04UTC.
HEAD8d04632; существующие незакоммиченные работы сохранены. Ключи, профили,
идентификаторы/IP клиентов и строки БД не выводились, только агрегаты на сервере.
Соседние сервисы не изменялись; нагрузка CPU/диска относится к хосту целиком.

## Устройства и нагрузка

Friends DB:30 активированных устройств,26 неотозванных,4 отозванных;
84 приглашения,30 использовано. К вечеру06.10:+1 устройство и+1 приглашение.
Это не количество уникальных людей; peers разных шлюзов не суммируются.

| Метрика | NL | RU |
|---|---:|---:|
| AWG настроенные peers |24|10|
| Handshake <5мин / <24ч |3 / 15|0 / 0|
| Рост transfer за15с |3|0|
| Никогда не было handshake |3|8|
| Friends TCP established443/8446 |0|0|
| vCPU |1|2|
| CPU busy / iowait |7.97% / 0%|17.09% / 2.25%|
| Load1/5/15 |0.33/0.31/0.31|0.56/0.55/0.63|
| RAM available/total,MiB |503.1/955.3|1047.9/1962.5|
| Swap used,MiB |0|507.3|
| Disk used/free,GiB |29.6% / 12.84|71.8% / 7.86|
| External RX/TX,Mbit/s |0.4138/0.4153|0.0272/0.0204|
| AWG RX/TX,Mbit/s |0.0201/0.3490|0/0|
| vda await / utilization |0.44ms / 0.01%|17.66ms / 5.56%|

Handshake/transfer — признаки активности устройств, включая keepalive, не точный
online людей. TCP охватывает только Friends endpoints. Кратковременный снимок
не является capacity benchmark. Оценка200Mbit/s в публичной сводке провайдерская,
не измеренная. RU два текущих интервала vmstat:si/so=0; первая строка со средними
с загрузки не использована для вывода о текущем swapping.

## Службы и риски

- AWG/TCP на обоих шлюзах active,Result=success,NRestarts0.
- RU friends-http-candidate active; прежний friends-access inactive не означает
  отказ замещающего API. Protected API отдельно не проверен.
- RU product API/control Docker healthy. Peer-worker Docker unhealthy при active
  systemd: фактические cycles/outbox и причина healthcheck не проверены.
- RU restricted-sync failed,exit-code,последний exit13:14:56UTC;
  NL restricted-bootstrap failed,exit-code,NRestarts11,exit04:07:38UTC.
  Это отдельные restricted-компоненты; отсутствие отказа обычного AWG не доказывает
  работоспособность restricted пути. Корневая причина текущих ошибок не установлена.
- RU product-cert-renew success,exit07.10 09:15:22UTC; следующий timer21:08:02UTC.
  Публичный HTTPS8443/status/server-load.json успешно получен с проверкой TLS;
  served certificate05.10 20:11:01UTC—12.10 12:11:00UTC. Это не сертификат restricted.
- RU disk await17.66ms ниже вчерашних70–105ms, но проблема не признана исправленной;
  свободно7.86GiB против8.10GiB вечером06.10. Нужен длительный мониторинг.

## Версии, проверки и завершение

Последний проверенный документированный deployment PINNED-EVIDENCE-DEPLOY-2:
owner Android0.1.18-beta68/code68 установлен; NL gateway SHA3038888a,source1abaa3a8.
Public/default beta65 сохранён; beta69 остаётся CI/engineering STOP по STATUS.
Это чтение deployment receipt, не свежая проверка установленного APK/бинарника.
Документированные Linux0.2.11/Windows0.2.15 и публичные артефакты не перепроверялись.
Новых версий, signing/catalog/invitation/deploy/restart/config changes нет.
Rollback аудита не требуется; существующий owner pair rollback указан в
2026-10-06-pinned-evidence-deploy-2.md, не выполнялся. Кодовые тесты, физический
client E2E и нагрузочные испытания не запускались. Осталось расследовать restricted
ошибки и worker/outbox, наблюдать RU диск и отдельно проверить клиентский E2E.
