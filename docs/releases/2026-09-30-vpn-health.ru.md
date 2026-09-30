# VPN: состояние30.09.2026

Read-only audit10:44–10:46UTC (12:44–12:46 Brussels), разрешённые RU/NL шлюзы.
Первый SSH к обоим получил No route to host; повтор успешен, HTTPS доступен.
Это не доказывает отказ самих VPN-шлюзов; причина краткого сбоя маршрута не выяснена.
Незакоммиченная работа сохранена; серверные настройки/данные не менялись.

## Пользователи и нагрузка

SQLite mode=ro:25 устройств,21 не отозвано,4 отозвано;79 приглашений/25 использовано.
NL20 peers:5 handshake<5мин,9<24ч,4 передавали за10с,3 никогда не подключались.
RU10 peers:0/0/0,9 без handshake. Это не уникальные люди/DAU; peers между
шлюзами не суммируются, keepalive входит в передачи. TCP отдельно не подсчитан.

| Метрика | NL | RU |
|---|---:|---:|
| CPU busy10с |4.14%|13.11%|
| iowait10с |0%|2.66%|
| AWG RX/TX,Mbit/s10с |0.0262/1.6951|0/0|
| RAM available/total,MiB |566/955|1086/1962|
| Диск занят/свободно |24%/14GiB|69%/8.7GiB|

Отдельный NL sar10×6: AWG RX2.96/TX220.56KiB/s (0.024/1.807Mbit/s),
CPU user2.22%+system3.23%+steal0.10%=busy5.55%,iowait1.18%,idle93.27%.
Это ниже29.09 вечерних17.19Mbit/s10с и9.03Mbit/s60с; перегрузки CPU/RAM
в замерах нет. Минутный vda await96.92ms,util2.36% — задержка сохраняется.
sar30 до13:40MSK: vda await NL138.56ms/RU38.86ms; не полные сутки.
Пропускная способность/причина задержек/качество физического клиента не измерены.

## Службы и HTTPS

AWG/TCP active,starts прежние. RU friends-access active, но start теперь
30.09 03:28:04UTC вместо25.09 03:56:22UTC; NRestarts0 относится только к
текущему состоянию и не отменяет факт нового запуска. Причина пока не установлена.
Ограниченный journal только systemd для этой службы06:25–06:30MSK показал
`Stopping ... device invitation API` в06:28:04MSK. Есть событие штатной остановки,
но инициатор/причина не установлены; аварийное падение этим не подтверждается.
Product API/control containers healthy; peer worker active, Docker unhealthy
сохраняется. Известное несоответствие healthcheck роли описано в отчёте29.09;
его циклы и outbox сейчас отдельно не проверялись.
Chat-sync повторно проверен: success10:45:31UTC (первый снимок застал запуск).
Cert-renew success30.09 09:02:48UTC, timer active/next30.09 21:26:35UTC.
Публичный HTTPS8443/status/server-load.json TLS PASS, snapshots обоих свежие;
served notAfter05.10 12:25:56UTC. Ночное автоматическое обслуживание успешно.

## Проверки и оставшаяся работа

SSH aggregates,/proc/sysfs10с,sar60с и sa30,systemd/container metadata,
SQLite mode=ro,curl TLS,openssl certificate dates; git diff --check.
Кодовые тесты не запускались: в репозитории изменена только документация.
Последний deployment по STATUS — disk mitigation29.09; новый rollout не выполнялся.
Версии ранее документированные: Android0.1.18-beta51/code51,Linux0.2.11,
Windows0.2.15; публичные бинарники/установки/invitation повторно не проверялись.
Rollback этого аудита не требуется; откат прежнего deployment —
2026-09-29-disk-io-recovery.ru.md.5N STOP не изменён.
Осталось: причина нового запуска access API, длительная дисковая latency,
worker healthcheck/outbox, история TCP/активности и физический клиент end-to-end.
