# VPN: read-only проверка 06.10.2026

## Вечерняя проверка 19:52–19:53UTC

Свежие read-only SSH-замеры обоих разрешённых шлюзов06.10 19:52:32UTC,
по15с; повтор RU19:53:35UTC. Клиентские ключи/IP/идентификаторы и содержимое
БД не выводились: только агрегаты. Существующие незакоммиченные работы сохранены.

Friends DB:29 активированных устройств,25 неотозванных,4 отозванных;
83 приглашения,29 использовано — без изменения относительно утреннего снимка.
Уникальных людей эти счётчики не определяют; peers шлюзов не суммируются.

| Метрика | NL | RU |
|---|---:|---:|
| AWG peers |23|10|
| Handshake <5мин / <24ч |7 / 14|0 / 0|
| Рост transfer за15с |7|0|
| Никогда не было handshake |3|8|
| Friends TCP established443/8446 |0 / 0|0 / 0|
| vCPU |1|2|
| CPU busy |19.30%|24.09%, повтор19.83%|
| Iowait |0.07%|3.66%, повтор3.13%|
| Load1/5/15 |0.26/0.66/0.54|0.66/0.70/0.75|
| RAM available/total,MiB |440/955.3|1059.2/1962.5|
| Swap used,MiB |0|492.9|
| Disk used/free,GiB |29.2% / 12.91|71.0% / 8.10|
| External RX/TX,Mbit/s |8.4000/6.2938|0.0329/0.0207|
| AWG RX/TX,Mbit/s |0.2245/5.6090|0/0|
| vda await |0.78ms|70.44ms, повтор105.25ms|
| vda utilization |0.06%|7.99%, повтор7.73%|

AWG/TCP обоих шлюзов active,NRestarts0; RU friends-http-candidate active.
RU product API/control Docker healthy; peer-worker Docker unhealthy, фактические
cycles/outbox не проверены. В пяти текущих интервалах vmstat si/so=0: занятый
swap не означает текущую подкачку. Повторяемая задержка диска RU требует разбора,
несмотря на отсутствие насыщения CPU/RAM в коротком снимке.

RU product-cert-renew уже Result=success,ExecMainStatus0,
ExecMainExitTimestamp06.10 12:19:01MSK=09:19:01UTC; timer active,
следующий запуск07.10 00:05:46MSK=06.10 21:05:46UTC. Утренний failed не актуален
как последнее состояние. Served HTTPS/TLS сейчас не проверялся; это отдельный
сертификат от restricted gateway leaf, для которого STATUS фиксирует STOP.

Последний просмотренный deployment checkpoint PINNED-EVIDENCE-DEPLOY-2:
beta68 не установлен, owner Android beta67/code67 и NL gateway ffd27988 остаются
по документированным данным; public/default beta65. Этим аудитом версии,
артефакты, каталоги, installed provenance и TLS restricted не перепроверялись.
Новых версий, deploy/restart/renewal/config changes нет; rollback не требуется.
Тесты кода, physical/client E2E и capacity benchmark не запускались. Handshake и
transfer — признаки активности устройств (включая keepalive), не точное число
людей online. TCP учитывает только выбранные Friends endpoints, не все pilots.
Остались: длительный мониторинг, RU disk latency, worker/outbox, served TLS,
отдельный restricted credential STOP и клиентская end-to-end проверка.

## Область и состояние

Авторизованные RU185.251.89.19 и NL186.246.45.246. SSH-снимки15с завершены
08:05:23/08:05:21UTC; внешняя HTTPS-проверка около08:06–08:07UTC.
HEAD8d04632; существующие многочисленные незакоммиченные изменения сохранены.
Обработка ключей peers и SQLite только на сервере; наружу выведены агрегаты,
без клиентских ключей/профилей/IP/идентификаторов и содержимого product DB.

Основная Friends DB:29 активированных устройств,25 не отозвано,4 отозвано;
83 приглашения,29 использовано. Относительно02.10 18:05UTC:+1 устройство,
+1 неотозванное,+1 приглашение. Это не количество уникальных людей.

| Метрика | NL | RU |
|---|---:|---:|
| AWG настроенные peers |23|10|
| Handshake<5мин / <24ч |5 / 12|0 / 0|
| Peers с ростом transfer за15с |4|0|
| Никогда не было handshake |3|8|
| Friends TCP established (443NL/8446RU) |0|0|
| vCPU |1|2|
| CPU busy / iowait |10.42% / 0.07%|23.05% / 1.45%|
| Load1/5/15 |0.41/0.39/0.44|0.72/0.65/0.70|
| RAM available/total,MiB |446.7/955.3|1029.9/1962.5|
| Swap used,MiB |0|469.8|
| Disk used / free,GiB |28.9% / 12.95|70.9% / 8.13|
| External RX/TX,Mbit/s |3.6495/3.0650|0.0223/0.0161|
| AWG interface RX/TX,Mbit/s |0.0086/2.8406|0/0|
| vda await / utilization |0.38ms / 0.02%|4.14ms / 3.19%|

Peers разных шлюзов не суммируются. Недавний handshake не равен точному online,
transfer может включать keepalive. TCP — моментальный счётчик Friends endpoints,
не всех legacy/pilot listeners. CPU/RAM в коротком снимке не насыщены; это не
capacity benchmark, длительный мониторинг или доказательство исправления прежней
disk latency. Занятый swap не доказывает активный swapping.

## Службы и риски

- AWG/TCP обоих шлюзов active,NRestarts0; старты NL25.09/24.09 и RU26.09/24.09.
- RU legacy friends-access inactive/Result=success/ExecMainStatus15. Replacement
  friends-http-candidate active,NRestarts0,start05.10 13:55:53UTC. Перенос на
  loopback18086 документирован в03.10-field1-release-final; inactive старой службы
  сам по себе не означает недоступность API. Protected API отдельно не проверялся.
- Product API/control Docker healthy. Peer-worker Docker unhealthy, systemd active;
  текущие cycles/outbox не проверены, известный healthcheck mismatch не исправлялся.
- RU product-cert-renew failed,Result=timeout,ExecMainStatus15; timer active/waiting.
  Публичный HTTPS8443/status/server-load.json отвечает200 с проверкой TLS.
  Served certificate:02.10 08:25:33UTC—09.10 00:25:32UTC. Требуется расследовать
  renewal до истечения сертификата, а не считать публичный HTTPS уже сломанным.
- Публичная сводка содержит свежие RU/NL timestamps08:06:11/08:06:05UTC;
  capacity200Mbit/s — provider-default-estimate, не измеренная ёмкость канала.
- После успешных первоначальных SSH-снимков дополнительные SSH-проверки зависли;
  ограниченный повтор завершился Connection timed out during banner exchange.
  Причина не установлена. Более ранние задержавшиеся вызовы затем завершились,
  журнал renewal получен: предыдущий запуск05.10 12:07:58MSK успешен; новый
  старт06.10 00:03:23MSK,timeout00:08:24MSK,failed00:09:35MSK
  (05.10 21:03:23/21:08:24/21:09:35UTC). Внутренняя причина зависания не видна.
  Следующий timer06.10 12:18:45MSK=09:18:45UTC. Внешний HTTPS при этом доступен.
  Не трактовать SSH-тайм-аут как доказанный отказ VPN.

## Версии, проверки и завершение

Последний документированный deployment DIAG-PAIR-DEPLOY-1: owner-only
Android0.1.18-beta66/code66,e1882552/JNIe433a491,NL gateway6af92aa9.
Это не новый публичный rollout: public/default beta65 сохранён согласно STATUS;
артефакты/подписи/установки/каталоги этим аудитом не перепроверялись. Документированные
Linux0.2.11/Windows0.2.15 также не перепроверялись. Новых версий нет.
Действия: только read-only SSH/15с агрегаты, systemd/Docker status, внешние HTTPS/TLS.
Кодовые тесты/physical client E2E/throughput acceptance не запускались.
Никаких deploy/restart/renewal/config changes; rollback этой проверки не требуется.
Существующий owner pair rollback остаётся в2026-10-06-diag-pair-deploy-1.md,
не выполнялся. Остались renewal root cause/следующий запуск, SSH, worker/outbox, длительная
нагрузка и end-to-end с клиентом. Restricted experiments не возобновлялись.
