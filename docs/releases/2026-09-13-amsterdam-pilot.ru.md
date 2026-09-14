# Амстердам: первый живой VPN-пилот — 13.09.2026

## Результат

Новый сервер `186.246.45.246` явно разрешён пользователем, подтверждён как пустой.
Ubuntu26.04 LTS/kernel7.0.0-30-generic,1 vCPU,955MiB RAM, около17GiB свободного диска.
Установлен native WireGuard без Docker: UDP51820, interfacefcams, MTU1280,
10.79.0.1/24 и fd79:92::1/64. Один Linux peer10.79.0.2/32,fd79:92::2/128.
wg-quick@fcams.service active+enabled; dependent firewall service active. Полная
перезагрузка VPS не выполнялась, проверен restart именно WireGuard service.

Трафик реально прошёл с ноутбука через этот VPS: DNS1.1.1.1, HTTPS Cloudflare trace
и ipify дали186.246.45.246; Cloudflare указал NL. Последний ping3/3, average71.127ms.
Одиночная загрузка1MiB:1.155021s,907841B/s. Это короткая функциональная проба,
не предел скорости, не нагрузочный тест и не обещание пропускной способности.
В конце всего сервер использует179MiB RAM, available776MiB; это память всей VM,
не отдельно измеренный RSS WireGuard и не замер ресурса под длительной нагрузкой.

## Развёртывание и доступ

Код `pilot/amsterdam/install.py`: fixed-host guard, root, отказ при существующей
инсталляции/firewall; client public key из stdin. Приватный серверный ключ создаётся
только на gateway, клиентский — только локально. Никаких signing secrets на сервере.
Remote installer SHA256:212885d636b7597700e5deaadcfb65d4d25e21d2e01237cbe587587499c6004d.
Установлен wireguard-tools1.0.20250521; curl/libcurl обновились как часть apt install.
Полное обновление ОС не выполнялось. Исходный forwardingIPv4/6 был0/0, теперь1/0.

Файлы gateway: `/opt/apps/family_connect/amsterdam/` (key, public key, firewall,
baseline), `/etc/wireguard/fcams.conf`0600, sysctl.d/70-family-connect-ams.conf,
firewall systemd unit и dependency drop-in wg-quick@fcams.service.d/firewall.conf.
NAT и фильтрация затрагивают только fcams/10.79.0.0/24; host input SSH сохранён.
Из VPN запрещены доступ к приватным сетям, TCP25 и IPv6 egress. IPv6 forwarding
выключен; IPv6 probe failed, но counter firewall rule0 — попадание именно в эту
nft rule не утверждается. Private-network drop counter6 подтверждён после трёх runs.

Провайдер принудительно потребовал смену временного root-пароля. Пароль сменён,
сохранён0600 вне проекта; в Git/отчёт не входит. Установлен существующий публичный
SSH key; независимый key-only login без control socket прошёл. Host key сохранён
в known_hosts, fingerprint SHA256:TA7zrfD44kXhvR1k2aW8JHNtWIuLFfP8m6yxzV6+drk.
Смена пароля оставила старый SSH control session с cached expired-password flag;
создание нового SSH session решило вход. SSH/password policies не отключались.

## Проверка сети и сохранённые неудачи

`pilot/amsterdam/check_linux.py` создаёт отдельный network namespace. UDP socket WG
создаётся в исходном namespace, тестовые адреса/полные IPv4/6 routes и DNS находятся
только внутри тестовой сети. После каждого запуска namespace/interface удалены,
host default routes, IPv4/6 rules и resolv.conf проверены как неизменные.
Это реальный Linux kernel WireGuard и внешний VPS, но не проверка GTK-приложения.

1. Первый run: DNS/HTTPS/1MiB/filters passed; HTTPS после service restart не прошёл.
   Первоначальная трактовка как SSH-ошибки не подтвердилась: server journal показал
   успешный restart. stderr первого curl не сохранён; точную причину не заявляем.
2. Добавлено bounded ожидание tunnel readiness35s, HTTP budgets остались5s connect/
   15s total. Server restart восстановился за16.627s, HTTPS passed. Простое client
   link down/up затем дало curl6 DNS failure. В начале ping2/3; это также сохранено.
3. Финальный сценарий: полное удаление/создание клиентского соединения, восстановление
   адресов/routes и bounded readiness. Все9 функциональных проверок прошли;
   server restart readiness16.615s, client reconnect0.078s. HTTPS после обоих passed.

Bare link toggle не принят и отдельно не исправлен; заменён сценарий проверки на
полное переподключение, соответствующее teardown/recreate. Нет доказательства
долговременной стабильности, sleep/handover или устранения прежнего TD-1.
[Все три машинные квитанции](2026-09-13-amsterdam-pilot.json).

## Локальный профиль и следующий шаг

Постоянные приватные файлы0600 в ignored `state-enroll/amsterdam-pilot/`, каталог0700:
`fc-amsterdam-linux.conf`, client key/public, server public, UAPI config и локальная
утилита wg из ранее имевшегося pilot image. Приватные файлы не выводятся и не входят
в Git. Это один Linux peer; для другого устройства нужен отдельный ключ/peer.
Приложение не обновлялось, профиль в GUI пока не импортирован, автоподключения нет.
Следующий шаг — проверить его через paired Linux приложение, затем внешний trusted
Reticulum relay. На VPS пока нет AWG/TCP, product API/registration или RNS carrier.
Это начало внешнего Stage6, не завершённый независимый control/failover.

## Возврат и версии

Для остановки пилота на новом VPS: `systemctl disable --now wg-quick@fcams.service`,
затем `systemctl stop family-connect-ams-firewall.service`. Это удаляет только его
интерфейс и собственные nft tables. Сохранить keys/configs для повторного включения.
Если forwarding больше ничему не нужен: отключить созданный sysctl.d файл и вернуть
исходное net.ipv4.ip_forward=0 из baseline.json; IPv6 остаётся0. Не удалять весь nft ruleset.
Install script повторно не запускать: он намеренно откажет на существующем state.

Старый gateway185.251.89.19 не менялся; excluded186.246.51.201 не использовался.
Desktop0.2.9/catalog8 и Android0.1.0/code1 без изменений; Linux0.2.8 ранее наблюдалась
установленной и в этой сессии не обновлялась. Нет release, main merge или GUI rollout.
Полная Python regression:462 passed,2 прежних deprecation warnings,9.68s.
Оба operator scripts прошли py_compile; nft --check выполнен на gateway до активации.
Новая удалённая CI не заявляется: acceptance — реальный сетевой пилот и локальная regression.

## Git checkpoint

Acceptance source `42350bcc4d722bc0d57c4142993c3d91600ed843`, рабочая ветка stage5-linux-control-preview.
Проверочный harness использует session helper `/tmp/fc-amsterdam-ssh` для
перезапуска сервера через владельца локального state; перед повторным запуском
нужно восстановить этот scoped SSH helper и проверить key-only доступ. Это
operator harness, не установленный клиентский сервис. Его private state и
выходные JSON не следует подменять fixture keys из conformance corpus.
