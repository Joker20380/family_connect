# Первый ноутбук: pinned-control TSO/GSO A/B/A — 11.09.2026

Выполнен следующий пункт PLAN. VPN исходно off, joker-XPS/wlp0s20f3,
существующий профиль fctcp75850269. TSO/GSO исходно on/on, mangleid off.
Все HTTPS-цели закреплены:1.1.1.1, три прежних ipify IP и example.com104.20.23.154
(получен до VPN). DNS не участвует в запросах. Четыре раунда×пять целей,
connect budget3s/max6s, четыре параллельных worker. Direct привязан к Wi-Fi.

## Итоговый цикл с точным восстановлением

| Фаза | VPN HTTP200 | Direct HTTP200 |
|---|---:|---:|
| До VPN |—|20/20|
| A, исходные TSO/GSO |16/20|20/20|
| B, TSO/GSO off/off |18/20|20/20|
| A, все исходные флаги восстановлены |14/20|20/20|
| После VPN |—|20/20|

VPN48/60, direct100/100 с учётом off-фаз. Все12 VPN отказов — TCP connect timeout~3s,
time_connect/time_appconnect0; DNS исключён pinned-адресами. Отключение TSO/GSO не
устранило сбои. Маленькая последовательная выборка, изменение нагрузки/времени и
сохранение одной VPN-сессии ограничивают причинный вывод; умеренное влияние offload
не исключено. Постоянно отключать offload оснований нет.

Снимки к gateway/443 после A/B/A: sockets68→103→190, send queue18400→30609→65758B;
retrans-field22→32→79 (показатель ss, не число потерянных пакетов). Xray FD64→89→157
при soft/hard limits524287/524288. Исчерпание FD в этих снимках не наблюдается;
не исключены другие ограничения TUN/движка. Снимки включают фоновые full-tunnel
подключения, не дают соответствие каждого curl конкретной внешней REALITY-сессии.
После stop Xray отсутствует;122 сокета остаются в FIN/LAST-ACK/CLOSING, не ESTAB.
Они не означают работающий VPN и не были принудительно удалены.

## Промежуточные попытки и исправление диагностики

1. Первая серия VPN14/20→16/20→18/20, direct20/20 во всех пяти фазах.
   Был post-TLS HTTP timeout и11 TCP-connect timeouts. Независимая проверка обнаружила:
   возврат TSO через ethtool включил tx-tcp-mangleid-segmentation, исходно off.
   Поэтому последняя A не совпадала с первой по всем флагам. Зависимый флаг восстановлен.
2. Вторая серия A20/20, B20/20, direct20/20 до/в обеих/после. Проверка полного
   набора флагов отказала до последней A: передача TSO и mangleid в одном вызове
   ethtool всё равно оставила mangleid on. VPN очищен; это незавершённый A/B/A,
   не положительная проверка offload-причины.
3. Операторский controller исправлен: TSO/GSO и mangleid восстанавливаются двумя
   последовательными вызовами. Независимый restore timer делает ту же последовательность.
   Остаточный timer второй попытки остановлен при восстановлении. Итоговый цикл выше
   прошёл: полные feature dictionaries original==A_before==A_restored==final.

Исходные JSON сохранены отдельно: result.json, result-exact.json, result-final.json.
Для выводов использовать итоговую таблицу и учитывать непостоянство сбоев между сериями.

## Очистка, версии, откат

Аварийный service-stop timer240s, отдельный restore timer120s до изменения offload.
Восстановление finally и независимая проверка прошли: TSO/GSO on/on, mangleid off,
полный набор исходных flags совпадает. IPv4/IPv6 policy rules совпали с baseline,
TUN/active marker отсутствуют; service inactive, fc-first-offload timers отсутствуют.
VPN оставлен off. Системные MTU, checksum/GRO и product timeouts намеренно не менялись.
Связанные TSO subfeatures временно менялись вместе с TSO, затем полностью восстановлены.

Stable Linux0.2.7, published desktop0.2.8, TCP0.1.0, server0.2.1 unchanged.
Сервер не изменялся, root components не обновлялись, пять прежних клиентских правок
сохранены. Новый CI/deployment/release не запускались; release state проверен ранее
в first-laptop-resume. Product code не менялся; operator py_compile и doc diff check
прошли, unit suite не повторяли. Установочного отката нет; временные изменения отменены.

Scripts/results хранятся в ignored state-client-build/session-2026-09-11-first-offload,
рабочие файлы /tmp/fc-first-offload. Private profiles/keys не копировались и не выводились.

## Дальше

Сравнить TUN, SOCKS и pinned direct в изолированном тесте с тем же Xray/REALITY endpoint,
свежим процессом и ограниченным трафиком без перенаправления фоновых приложений.
Записать точные времена запросов, local TCP handshake на TUN и внешние socket counters.
Если SOCKS стабилен при TUN connect-failures — исследовать TUN/локальную маршрутизацию;
если оба ломаются — продолжить внешний paired-header path с привязкой к запросам.
Исторические SOCKS проверки не заменяют текущую сопоставимую серию.
Настройки offload оставлять исходными, второго ноутбука пока не касаться.
После воспроизводимого исправления — второй Ubuntu, review/setup integration/CI/release;
этап4 остаётся открытым, native Windows/Android и Reticulum впереди.
