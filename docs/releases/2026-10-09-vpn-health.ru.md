# VPN — проверка 09.10.2026

Read-only SSH разрешённых RU185.251.89.19/NL186.246.45.246 и публичный HTTPS,
06:24–06:25UTC (08:24–08:25 Europe/Brussels). HEAD8d04632; существующие
незакоммиченные работы сохранены. Секреты,профили,ключи,идентификаторы клиентов
и строки БД не выводились: только агрегаты,состояния служб и коды healthcheck.

## Клиенты и нагрузка

33 активированных устройства:29 неотозванных,4 отозванных.87 приглашений,
33 использовано. К08.10:+2 устройства/+2 приглашения. Это не уникальные люди;
peers двух шлюзов не суммируются. Основной замер15с,NL повторно15с.

| Метрика | NL | RU |
|---|---:|---:|
| Open AWG peers |26|10|
| Handshake за5мин /24ч |4/14|0/0|
| Рост transfer за15с |5;повтор3|0|
| Никогда не было handshake |3|8|
| Friends TCP established443/8446 |0|0|
| vCPU |1|2|
| CPU busy / iowait,% |7.57/13.25;повтор10.05/0|23.60/1.18|
| Load1/5/15 |0.38/0.35/0.36|0.82/0.89/0.92|
| RAM available/total,MiB |474.4/955.3;повтор448.7|1011.8/1962.5|
| Swap used,MiB |0|511.5|
| Disk used /free,GiB |30.6%/12.65|71.3%/8.01|
| External RX/TX,Mbit/s |0.7538/0.0273|0.0216/0.0266|
| AWG RX/TX,Mbit/s |0.0024/0.0037|0/0|
| Disk await,ms |204.17;повтор0.5|34.03|
| Disk utilization,% |15.86;повтор0.03|5.97|

Handshake/transfer включает keepalive: это не точный online людей. Отдельные
legacy/pilot WG не включены. Ресурсы/внешний трафик относятся ко всему хосту;
это не измерение максимальной ёмкости VPN. RU vmstat текущий интервал si/so0/0;
первая строка со средним с загрузки не доказывает текущий swapping.
NL всплеск disk latency не повторился,но длительное здоровье диска не установлено.

## Службы и риски

- AWG/TCP обоих шлюзов active/running,Result success,NRestarts0; RU HTTP active.
- Публичный HTTPS8443/status/server-load.json HTTP200,TLS verify0.
- RU product API/control Docker healthy; peer-worker unhealthy,failing streak28268,
  последние5 healthchecks exit1. Причина и фактическая обработка outbox не проверены.
- RU restricted-sync последний exit06:24:10UTC success,таймер active/waiting.
- NL restricted-bootstrap active,NRestarts8 (08.10 было5),старт05:32:19UTC.
  Причины перезапусков не установлены; это не доказательство restricted E2E.
- RU cert-renew последний exit08.10 21:11:46UTC success,таймер active/waiting.

## Версии,границы и завершение

Последний прочитанный deployment receipt:owner Android0.1.18-beta69/code69 и
парный NL gateway установлены,deploy gates PASS07.10; последующий selected-retry
FAIL остаётся отдельным результатом. Это историческая запись,не свежая проверка
APK/хеша процесса. Public/default версии,каталоги и артефакты не перепроверялись.
Новых версий,сборок,signing,публикации,deploy,renewal,конфигурационных изменений
или перезапусков нет. Rollback аудита не нужен; существующий owner-pair rollback
см.2026-10-07-rtp-identity-deploy-1.md,не выполнялся. Кодовые тесты,нагрузочное
испытание и физический client E2E не запускались. Осталось расследовать worker,
restricted restarts,наблюдать disk latency на обоих хостах и проверить client E2E.
