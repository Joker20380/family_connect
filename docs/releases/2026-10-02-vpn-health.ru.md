# VPN: read-only аудит02.10.2026

Проверка18:05–18:06UTC /20:05–20:06 Europe/Brussels. HEAD a24f090;
существующие незакоммиченные изменения сохранены. SSH только на разрешённые
RU185.251.89.19 и NL186.246.45.246. Серверы, службы, конфиги и записи БД не менялись.
Агрегаты SQLite и AWG вычислялись на сервере: без вывода ключей, профилей,
идентификаторов устройств или клиентских адресов. Начальный sandbox SSH отказал
на проверке прав системного ssh config; дальнейшие проверки выполнены с разрешением.

## Пользователи и подключения

Friends access:28 активированных устройств,24 не отозвано,4 отозвано;
82 приглашения,28 использовано. Относительно01.10 17:43UTC добавлено одно устройство
и одно приглашение. Это не число уникальных людей; отдельные pilot DB сюда не входят.

| Метрика | NL | RU |
|---|---:|---:|
| AWG configured peers |22|10|
| Последний handshake<5мин / <24ч |3 /11|0 /0|
| Peers с передачей за15с |3|0|
| Никогда не было handshake |3|9|
| Friends TCP established inbound |0 на443|0 на8446|

Peers разных серверов не суммируются. Handshake не равен точному online/DAU,
передача включает keepalive;24ч означает возраст последнего handshake, не журнал
всех сессий. Отсутствие текущих TCP соединений не доказывает отсутствия за сутки.

## Ресурсы

Параллельные15.01/15.03с выборки18:05:19–18:05:35UTC:

| Метрика | NL | RU |
|---|---:|---:|
| vCPU |1|2|
| CPU busy / iowait |6.80% /0.07%|22.03% /1.34%|
| Load average1/5/15мин |0.11/0.20/0.18|0.61/0.83/0.93|
| Available / total RAM,MiB |555.4 /955.3|1093.6 /1962.5|
| Диск занят / свободно |26.1% /13.46GiB|69.3% /8.56GiB|
| External RX/TX,Mbit/s |1.4556 /0.4223|0.0240 /0.0164|
| AWG RX/TX,Mbit/s |0.1027 /0.2559|0 /0|
| vda await / utilization |1.08ms /0.11%|3.41ms /3.02%|

Повторная10с выборка до18:06:02UTC: CPU NL8.43%,RU26.67%; NL external
RX/TX3.9895/3.3960Mbit/s,AWG0.1388/2.9892Mbit/s. RU AWG по-прежнему0.
Доступная RAM RU1063MiB, swap занят около637.5MiB; активный swapping не измерялся.
Uptime NL19д8ч,RU31д5ч; NTP synchronized на обоих.

Sar02.10 с00:00 до примерно21:00 серверного MSK (не полные сутки Brussels):
RU CPU user+nice+system20.42%,iowait1.57%; NL4.86%,iowait2.34%.
NL AWG средние RX/TX8.32/252.35KiB/s; максимум среди126 интервальных samples
135.54/1294.71KiB/s, не мгновенный пик. RU AWG в этих samples0.
NL vda средний await138.83ms,%util3.34%: короткий хороший снимок не доказывает
устранения ранее наблюдавшейся задержки диска. Причина здесь не установлена.

## Службы и ограничения

- Обычные AWG/TCP active,NRestarts0; start dates прежние: RU AWG26.09,
  NL AWG25.09, TCP обоих24.09. Это не доказательство отсутствия всех сбоев.
- RU access API active, start02.10 09:33:26UTC; отличается от вчерашнего снимка.
  Причина и длительность возможного перерыва не исследованы; NRestarts0
  не исключает ручной restart.
- Product API/control Docker healthy. Peer-worker systemd active, Docker unhealthy,
  failing streak9669, последние5 healthchecks exit1. В последних15мин tail100
  обнаружено50 событий peer-reconcile-cycle, все exit0. Это не проверка outbox
  и не основание объявлять healthcheck ложным.
- Chat-sync и cert-renew oneshot завершились exit0; cert-renew timer ожидает.
  Fail2ban active на обоих. Access/worker на NL не установлены по архитектуре.
- GET HTTPS8443/status/server-load.json успешен с проверкой TLS. Отдельный
  monitor sample NL CPU13.1%,RX/TX7.883/7.364Mbit/s,RU22%,0.024/0.022Mbit/s.
  Заявленные200Mbit/s — provider-default-estimate, не измеренная ёмкость.
- Client E2E, браузер/DNS, потери/скорость, outbox, история TCP и уникальные люди
  не проверены. Короткие снимки не измеряют capacity/SLO.

## Версии, rollout и оставшаяся работа

Последний документированный restricted attempt14 FAILED/ROLLED BACK; этот аудит
не повторяет его и не проверяет restricted readiness. Последние документированные
версии: private canary55/code55 built/signed only; installed canary54/code54;
public Android0.1.18-beta51/code51,Linux0.2.11,Windows0.2.15. Установки,
public/invitation binaries, подписи и каталоги этим аудитом не перепроверялись.

Изменена только документация STATUS/PLAN/этот отчёт. Кодовые тесты не запускались,
для документации выполнен git diff --check. Rollout/rollback отсутствуют:
производственные изменения не выполнялись. Ранее применённый disk mitigation
и его rollback описаны в [отчёте29.09](2026-09-29-disk-io-recovery.ru.md).
Остаются диагностика NL disk latency, worker healthcheck/outbox, причины изменения
start API и client E2E. Нет commit/push/автоматического исправления или attempt15.
