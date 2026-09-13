# Постоянная регистрация и relay для Linux control pilot — 13.09.2026

По запросу пользователя подготовлены постоянная identity устройства, настоящая
регистрация через deployed HTTP API и доверенный локальный Reticulum relay.
Приватное состояние: `state-enroll/control-linux-pilot` (Git ignored, directory0700,
files0600). Секретные ключи не включены в отчёт, Git или вывод команд.

## Проверки

- Архив accepted preview SHA256
  `390ba9ff24c11ba63ac7b48ec0d7d89a5c623563401a90d25c25d55b81620797` совпал.
  Распаковка с tar data filter, launcher manifest verify exit0.
  Комплект `/tmp/fc-control-resume-dr5uk0p6/FamilyConnect-Control-preview`.
- GitHub API повторно подтвердил phase0 run34722963403 completed/success,
  commit3a28be767bc6a3c8d8e8c77f089f8e49cac60a96. Новая CI suite не запускалась.
- Перед подготовкой: три WG peers, свободный10.77.0.252/32; активного VPN на
  ноутбуке не было (Wi-Fi/bridges/loopback). Сервер только185.251.89.19.
- Постоянное устройство `71a05310177fa445bbe95b2405e650ba` зарегистрировано через
  challenge/proof HTTP API по SSH loopback. Entitlement создан на30 дней,
  gateway lease отдельно ограничен одним часом. SQLite online backup перед
  созданием: `/opt/apps/family_connect/state-product/db/pre-control-pilot-1789285423.sqlite-backup`. Invitation не сохранялся локально.
- Штатный worker подтвердил present и persisted для10.77.0.252/32;
  public key соответствует постоянной device identity. Все три исходных peers
  и их allowed-ips сохранены. Gateway lease до **2026-09-13T08:43:59+00:00**.
- Первоначальный неподписанный черновик отклонён строгим parser: отсутствовал
  обязательный IPv6 default route. До подписания добавлен `::/0`, валидатор
  не ослаблялся. Профиль предусматривает IPv4 адрес устройства и оба default routes;
  работоспособность IPv6 gateway не заявляется.
- Envelope revision1 подписан существующим offline Ed25519 root через
  `scripts.sign_control_config.py`, зашифрован для зарегистрированного устройства.
  SHA256 `7d74144b3d35d65aea4c2f7fe3eccf708df971ebd81cacd72274bd17fd4cec6b`.
  Срок конфигурации до **2026-09-13T08:40:14+00:00**, раньше gateway lease.
- Два реальных процесса с распакованными модулями: relay serve + RNS receive.
  Явный TCP loopback127.0.0.1:42871, share_instance/transport disabled.
  Public identity relay сверена с локально закреплённой, envelope получен побайтно,
  подпись, адресат и WG binding проверены. Никакой mock доставки не использован.
- Journal после receive: IDLE, floor0, committed=null, outbox пуст. Apply не
  вызывался, COMMITTED ACK не заявляется. Relay остановлен после проверки.

## Следующий шаг и возврат

Подготовка входных данных завершена. Далее отдельный короткий paired GUI/control
пилот на реальном профиле: закрыть старый GUI0.2.8, запустить GUI из принятого
комплекта и тот же control journal. До живого запуска проверить срок envelope и
peer, отсутствие чужого активного VPN, затем независимые HTTPS/DNS/маршруты и
cleanup. Для standalone WG backend healthy может означать только active NM;
это не достаточное доказательство доступа в Интернет, нужен отдельный traffic check.

Постоянные пути и команды сохранены в приватном `state-enroll/control-linux-pilot/OPERATIONS.md`.
После expiry stage gateway lease заново и выпустить следующую подписанную revision
с тем же device/journal. Relay publication требует возрастающую sequence даже если
floor клиента ещё0. Не удалять journal/identity и не переиздавать revision1.
Для pending использовать `control recover` с теми же identity/journal/anchor;
при FAILED сохранить marker и повторить восстановление после устранения причины.

Серверные образы и службы не переустанавливались. Добавлены только продуктовые
записи регистрации и один временный peer через штатный worker. По окончании lease
его удаляет периодический worker; фактическое удаление после expiry ещё не наблюдалось.
Для полного отказа от пилота revoke device/entitlement через ProductStore и дождаться
applied=absent; не откатывать БД к backup под работающими API/worker.
Регистрация и ключи сейчас сохранены для следующего запуска.

Installed current0.2.8 (`releases/0.2.8-766194f6f3df-9c6f2e52a84f`), previous0.2.7.
Документированные выпуски desktop0.2.9/catalog8, gateway0.2.1, TCP0.1.0.
Клиентская установка и VPN-профили ноутбука не изменялись. Нет нового release/catalog.
Локальный relay не подтверждает Stage6 independent entry; native Stage5, AWG3.1,
TD-1 и отложенные device/load tests остаются открытыми.
