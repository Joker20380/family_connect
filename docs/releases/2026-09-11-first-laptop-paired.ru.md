# Первый ноутбук: сопоставленные TCP headers — 11.09.2026

Этап4: Linux/platform acceptance перед стабильным выпуском. Функциональные WG/AWG/TCP
пилоты не означают устранение сетевых тайм-аутов или готовность Windows/Android.

## Проверка и результаты

Первый ноутбук joker-XPS, существующий TCP profile fctcp75850269. Перед тестом VPN off;
актуальные интерфейсы проверены: wlp0s20f3 / сервер ens3. Внешний адрес получен заново
прямым запросом; серверный фильтр ограничен этим peer/443, клиентский — gateway/443.
Сервер только185.251.89.19, TCP container family-connect-tcp-gateway-1 работает.

Те же пять целей,4 раунда на серию, connect budget3s/max6s,4 parallel workers.
Cloudflare numeric IP, три pinned ipify IP, example.com через системный DNS.

| Фаза | VPN HTTP200 | Прямой Wi-Fi HTTP200 |
|---|---:|---:|
| До подключения |—|20/20|
| VPN серия1 |20/20|20/20|
| VPN серия2 |15/20|19/20|
| После отключения |—|20/20|

VPN итого35/40, direct во включённой фазе39/40. Четыре TUN отказа — TCP connect
timeout3s (time_connect/time_appconnect0), один — DNS resolving timeout.
Прямой отказ тоже DNS resolving timeout к example.com. Успешный DNS resolve в части
connect-failures и pinned Cloudflare/ipify показывают, что DNS не объясняет всё.
В этот раз не наблюдались TLS-setup timeout или прежний post-TLS HTTP timeout.

Важное ограничение direct: --interface закрепляет сокет HTTPS, но системный resolver
во время VPN использует настроенный туннелем DNS. Поэтому example.com здесь не является
полностью независимым direct-контролем. Numeric/pinned direct запросы прошли32/32;
следующая матрица должна закрепить IP и у example.com до подключения.

## Сопоставление заголовков

AF_PACKET ETH_P_ALL, только TCP metadata; payload/credentials не сохранялись.
75 секунд на каждой стороне, начало окон различается~0.069s по часам машин
(синхронность часов отдельно не измерялась). Ноутбук25212 записей, сервер23792;
inbound/outbound присутствуют, socket_dropped0 с обеих сторон, лимит50000 не достигнут.
Server socket_received69102/client26947 включает отфильтрованный трафик интерфейса.

723 новых client SYN,576 сопоставленных ранних flow (client start не позднее12s до конца).
Matching учитывает initial sequence/NAT port rewrite, следующий SYN ограничивает reuse;
диапазоны sequence объединяются для GSO/GRO. В агрегате246 flow с client→server byte gap,
10 с обратным gap; эти числа сами по себе не доказывают потери из-за границ окон/завершения.

Более сильный отбор:78 flow с непрерывным принятым префиксом и повторами отсутствующего
остатка не менее10s. В53 из них server получил1327 байт и не отправил payload response.
Пример local47004/NAT7659:1728 unique bytes отправлены в client capture,1327 приняты server;
ACK1327 виден на клиенте. Остаток401 байт повторяется через0.495/0.807/1.447/2.727/
5.223/10.471/20.711/40.679s, но на сервере в окне отсутствует.
Этот признак повторяет наблюдение второго ноутбука. Клиентский AF_PACKET видит пакет
до NIC; фактический выход сегментов в эфир, конкретный узел потери и offload-причина
не установлены. Возврат ACK подтверждает доставку префикса, не остатка.

Capture охватывает также фоновые подключения через full tunnel. Нет точного отображения
каждого curl на отдельную внешнюю REALITY-сессию; нельзя приписать выбранный flow
конкретному curl timeout. Снимки socket queue/FD limits в этой серии не собирались.

## Выполнение, очистка и версии

Первая попытка остановилась до VPN: серверный collector не подтвердил READY после
pkexec→runuser SSH. Повтор сохранил SSH_AUTH_SOCK текущего пользователя и прошёл;
отдельный stderr первой попытки не сохранён, поэтому точная причина первого отказа
не доказана. First-attempt before/after direct20/20, cleanup passed; исходный JSON сохранён.

Рабочий запуск имел независимый systemd stop timer150s, ожидание TUN public route и DNS,
проверку gateway bypass. В finally служба остановлена. Полные IPv4/IPv6 rules совпали
с baseline, TUN/active marker отсутствуют, timer отключён. Дополнительная проверка
подтвердила inactive service и отсутствие fc-first-paired timers. Оба collector завершились.
Серверный Python запускался через SSH без записи файлов/изменения конфигурации.
TCP container остался запущен без restart. VPN ноутбука оставлен выключенным.

Stable Linux0.2.7, published desktop0.2.8, TCP0.1.0, server0.2.1 unchanged.
Бинарники/root helpers, MTU/offloads, полkit и product timeouts не менялись.
Пять существующих незакоммиченных клиентских файлов сохранены. CI/новый релиз не запускались;
последняя проверка GitHub остаётся в предыдущем first-laptop report. Продуктовых правок нет,
unit suite не повторяли; operator scripts py_compile passed, documentation diff check passed.
Откат установки не требуется, временное включение VPN уже отменено.

Scripts/raw metadata/results сохранены локально в ignored
state-client-build/session-2026-09-11-first-paired, исходники /tmp/fc-first-paired.
Не публиковать исходные сетевые metadata как общедоступные журналы.

## Следующий шаг

Bounded offload A/B/A на первом ноутбуке с pinned адресами ВСЕХ контрольных целей;
baseline до VPN и после, snapshots числа sockets/очередей и Xray FD до каждой фазы.
Изменять только TSO/GSO, запоминать фактические исходные значения и восстанавливать
через finally плюс независимый timer. При деградации pinned direct остановить причинные
выводы и сначала исследовать общий путь. Не переносить вывод второго inconclusive A/B/A
на первый. Повтор воспроизводимого исправления на втором остаётся следующим gate.
Далее review client patch, standalone setup integration, platform CI и signed release;
native Windows/Android, Reticulum и независимый gateway ещё впереди.
