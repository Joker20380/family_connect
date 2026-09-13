# Linux paired control pilot: живой цикл принят — 13.09.2026

## Результат

Исправленный комплект66152538ee2a4f3e прошёл живой цикл: Reticulum delivery →
реальный NetworkManager apply → interface-bound HTTPS/ACK → синхронизация GUI,
затем остановка процесса после следующего apply → durable ownership → recover
предыдущего профиля → HTTPS → ACK/replay → GUI Disconnect/close → cleanup.
Это короткая локальная Linux-приёмка. Relay работает через явный loopback TCP;
независимая инфраструктура Stage6, native Stage5 и длительная стабильность не заявлены.

## Диагностика прежнего отказа

Сняты только IPv4/TCP метаданные потока1.1.1.1:443 в течение45 секунд на ноутбуке
и в network namespace контейнера family-connect-pilot-gateway-1 на185.251.89.19.
Содержимое пакетов и pcap не сохранялись. Capture socket SOCK_DGRAM/ETH_P_IP
зафиксировал входящие пакеты; отсутствующие исходящие записи не трактуются как потеря.

Direct HTTPS прошёл: HTTP200, TCP0.059s, TLS0.136s, total0.176s. Оба VPN запроса
(bound и default routing) завершились curl28 около3.00s. По времени/портам/seq/ack
зафиксированы отдельные пары53272 и53286:

- SYN с10.77.0.252 достиг wg0, SYN-ACK дошёл до ноутбука, ACK вернулся на wg0.
- За ACK последовал клиентский payload1551 bytes. Следовательно, прежний вывод
  «TCP не устанавливается» из нулевых timing полей неуспешного curl был неверен.
  Установление TCP подтверждено пакетами; TLS-продолжение следует из HTTPS сценария.
- На eth0 gateway видны крупные диапазоны ответа1368+1368 bytes (в одном случае
  GRO aggregate2736). На ноутбук эти диапазоны не пришли, но хвост977/978 bytes
  получен. Клиент продолжал ACK начального server sequence, gateway видел повторные
  передачи отсутствующих диапазонов.
- Это локализует наблюдение между входом ответа в gateway namespace и приёмом
  расшифрованного сегмента на ноутбуке. Где именно теряются большие пакеты
  (gateway forwarding/encapsulation, underlay или приём), ещё не доказано.

Следующая проверка меняла только wireguard.mtu пилотного NM-профиля, с одинаковым
URL/таймаутами, последовательность0(auto1420)→1280→0(auto1420)→1280:

| MTU | HTTPS | total |
|---|---|---|
| auto1420 | timeout |3.002s|
|1280|HTTP200, egress185.251.89.19|0.415s|
|auto1420 повтор|HTTP200, egress185.251.89.19|0.383s|
|1280 повтор|HTTP200, egress185.251.89.19|0.386s|

Таким образом,1280 пригоден для текущего пилота, но строгого A/B/A воспроизведения
нет: возврат1420 тоже прошёл. Кэширование/path learning или временное изменение
сети не исключены. Не объявлять причинный MTU fix или общую стабильность.
По окончании сравнения исходный MTU0 восстановлен, VPN отключён, rules восстановлены.

## Исправленный живой комплект

`/tmp/fc-live-control/fixed/FamilyConnect-Control-preview`.
Archive `FamilyConnect-Control-Linux-preview-66152538ee2a4f3e.tar.gz`, SHA256
`9c827f86f03d27705c46830758e114b3f7ef9796320d9e46f09672363de076f3`.
Это комплект с control_healthy из предыдущего шага: проверяется HTTPS через NM WG
и совпадение egress с gateway подписанного профиля перед выбором/commit.
Локальные412 Python tests и package manifest прошли предыдущим шагом; исходники
этого комплекта в текущем шаге не менялись. Новую suite без изменений не повторяли.
Remote CI этого исправления остаётся следующим шагом до распространения.

Существующий offline signing root, постоянная device identity и journal сохранены.
Издана config2 с MTU1280 и previous hash config1. Она доставлена через RNS,
импортирована в NM, traffic health прошёл, commit/ACK доставлены. GTK автоматически
выбрал новый активный профиль; независимые HTTPS egress и interface DNS прошли.

Затем издана config3 с тем же MTU и previous hash config2. Проверочный harness
выполнил настоящую BackendApplication.apply, затем намеренно завершил процесс
через os._exit(77) до записи APPLIED_PENDING. Это явная fault injection после
реального переключения профиля, не случайный crash приложения.

Journal остался APPLYING/floor3; попытка backend disconnect получила ConnectionBusy,
подтверждая durable ownership. Штатный CLI recover восстановил config2, выключил
кандидата и вернул ROLLED_BACK. Независимая HTTPS проверка восстановленного профиля
подтвердила gateway egress. Повтор once(config3) вернул ROLLED_BACK и доставил
сохранённые ACK; floor3 и committed config2 сохранены.

Реальный GTK обработчик toggle_vpn отключил соединение, UI показал inactive,
затем окно штатно закрыто. Это дополняет автоматическую cleanup проверку реальным
GUI Disconnect/close. Не доказывает все возможные rollback failures или общий
traffic-health критерий rollback: здесь восстановленный профиль проверен отдельно.

## Состояние, возврат и следующий шаг

- Journal: IDLE, floor3, committed config2, outbox пуст; operation pending=null.
- Config2 SHA256:31eeed4a5b8fa32e732f4c7fb95896008c62f35fcd3e70c09045d9646e1fe99a.
- Config3 SHA256:0dc9c078f909d1210b71a90de3b8472677f7e72d5344b6f6bc5a89553a4cb83d.
- После всех запусков VPN не активен, исходные профили сохранены, полные IPv4/IPv6
  policy rules совпали с baseline. Последний harness сохранил2 новых неактивных
  импорта; всего с прежним pilot config1 —3. Autoconnect=no, профили не удаляются
  из-под journal. Committed runtime отражает прежнее подключение, не текущее active.
- Relay/GUI/capture остановлены. Server gateway не менялся; временный peer создан
  предыдущим шагом и действует до08:43:59Z, конфигурации до08:40:14Z13.09.
  Удаление peer после истечения lease ещё не наблюдалось.
- Installed Linux0.2.8/current, previous0.2.7 не переключались. Ранее опубликованные
  desktop0.2.9/catalog8, gateway0.2.1, TCP0.1.0 без изменений. Нет release/install/merge.

Обычный GUI можно использовать после этого cleanup. Для следующей control-конфигурации
нужна revision≥4 с previous hash committed config2; после expiry продлить gateway
lease штатным worker и подписать новую конфигурацию. Не сбрасывать identity/journal
или floor. Прежний bundlebc908a5f084a8bb6 для live apply не использовать.

Следующий этап — scoped CI исправленного комплекта, затем native Windows/Android
Stage5 binding. TD-1 size-sensitive/intermittent loss, AWG3.1 и Stage6 остаются открытыми.
Длительные и отложенные device/load tests автоматически не запускались.
