# VPN — проверка 10.10.2026

Read-only SSH разрешённых RU185.251.89.19/NL186.246.45.246 и публичный HTTPS.
Время:10.10 01:44–01:47 Europe/Brussels, то есть09.10 23:44–23:47UTC.
Локальный HEAD8d04632; существующие незакоммиченные изменения сохранены.
Секреты,профили,ключи,идентификаторы клиентов и строки БД не выводились:
только агрегаты,состояния служб и классификация ошибок healthcheck.

## Клиенты

- 34 активированных устройства:30 неотозванных,4 отозванных.
- 88 приглашений,34 использовано. К предыдущему замеру09.10:+1 устройство/+1 приглашение.
- NL open AWG27 peers:1 handshake за5мин,15 за24ч,3 никогда не подключались.
- RU open AWG10 peers:0 handshakes за5мин/24ч,8 никогда не подключались.
- Рост transfer:NL1 peer и за15с,и в повторном60с окне;RU0. Friends TCP established0
  на обоих шлюзах (NL443/RU8446).

Устройства не равны уникальным людям. Handshake/transfer может включать keepalive;
точный online людей из этого не следует. Peers разных шлюзов не суммируются.
Отдельные legacy/pilot WG в эти показатели не включены.

## Нагрузка

Первичный замер15с,затем повтор60с на каждом хосте. Таблица — повторный замер,
NL завершён23:47:04UTC,RU23:47:11UTC. Ресурсы/внешний трафик относятся ко всему
хосту,не только VPN; это не нагрузочный тест и не оценка максимального числа клиентов.

| Метрика | NL | RU |
|---|---:|---:|
| vCPU |1|2|
| CPU busy / iowait,% |7.76/5.13|23.15/2.00|
| Load1/5/15 |0.58/0.48/0.39|0.87/1.04/1.09|
| RAM available/total,MiB |454.4/955.3|981.8/1962.5|
| Swap used,MiB |0|503.9|
| Disk used /free,GiB |31.6%/12.47|71.4%/7.98|
| External RX/TX,Mbit/s |0.7625/0.0245|0.0239/0.0182|
| AWG RX/TX,Mbit/s |0.0016/0.0054|0/0|
| Disk await,ms |157.09|29.01|
| Disk utilization,% |7.77|4.70|

В первом15с окне CPU busy NL10.88%/RU14.35%,disk await208.87/63.98ms,
iowait9.40/1.95%;NL AWG RX/TX0.0276/0.4757Mbit/s. Задержка диска NL остаётся
высокой и в минутном повторе; причина,физическое здоровье и влияние на клиентские
запросы не установлены. Насыщения CPU/RAM в этих окнах нет. RU vmstat текущий
интервал si/so0/0; занятый swap сам по себе не означает текущий swapping.

## Службы и уточнение worker unhealthy

- AWG/TCP обоих шлюзов active/running,Result success,NRestarts0. RU HTTP active.
- Публичный HTTPS8443/status/server-load.json:HTTP200,TLS verify0,0.278с.
- RU product API/control Docker healthy. Peer-worker active,running10дней,
  Docker unhealthy,failing streak30329,последние5 healthchecks exit1.
- Уточнение23:47:47UTC:у worker image `family-connect-product:0.2.1`,команда
  `deploy/product-peer-worker/worker.py`,но healthcheck проверяет API
  `http://127.0.0.1:8080/healthz`;5/5 последних ошибок содержат Connection refused.
  Это несовпадение назначения проверки с worker,не доказательство отказа очереди.
- Последние10мин:34 распознанных цикла peer-reconcile-cycle,все exit0.
  Read-only outbox:3 записи,3 applied=desired,0errors,0unchecked,
  самый старый checked_at5.8с. Предыдущий агрегат:33 exit0,3/3matched,0errors,18.5с.
  Проверка ограничена этими окнами; worker-specific healthcheck не исправлялся.
- Restricted sync:последний exit09.10 23:45:12UTC success,таймер active/waiting.
  Cert-renew:последний exit09.10 21:19:26UTC success,таймер active/waiting.
- NL restricted-bootstrap active/running,NRestarts0,process start09.10 20:44:25UTC.
  RU HTTP process start20:37:52UTC. Эти lifecycle изменения произошли до аудита;
  текущий счётчик0 не опровергает ранее записанный8 и не доказывает исправление.
  Причина изменений/перезапусков и restricted E2E не проверялись.

## Версии,границы и оставшиеся действия

Последний прочитанный локальный deployment receipt:owner Android0.1.18-beta69/code69
и парный NL gateway установлены,deploy gates PASS07.10; последующий selected-retry
FAIL остаётся отдельным результатом. Это историческая запись,не свежая проверка
APK/хеша процесса. Документированные public/default:Android beta60/code60,
Linux0.2.11,Windows0.2.15 (fallback0.2.14); публичные бинарники,каталоги и
invitation-page версии в этом аудите не перепроверялись,rollout не заявляется.

Новых версий,сборок,signing,публикации,deploy,renewal,изменений конфигурации или
перезапусков в этой задаче нет. Кодовые тесты,нагрузочные тесты и физический client
E2E не запускались. Rollback read-only аудита не нужен; существующий owner-pair
rollback см.2026-10-07-rtp-identity-deploy-1.md,worker rollback —
../../deploy/product-peer-worker/README.md; никакой откат не выполнялся.

Осталось:отдельно согласовать корректную worker-specific проверку здоровья,
наблюдать дисковую latency дольше,уточнить lifecycle HTTP/restricted и выполнить
client E2E. Изменять службы или увеличивать аудит до owner experiment не требуется.
