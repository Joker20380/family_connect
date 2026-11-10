# Отдельная среда RU AWG/TCP — подготовка, не переключение

Дата:10 ноября2026. Выбранная задача: **RU-TRANSPORT-REPLACEMENT-PREP**.
PR17/comment6765941574 остаётся **DEPLOYMENT_FAILED_ROLLED_BACK_VERIFIED**.
Серия повторных поставок на старый RU закрыта. Причина исторических задержек
не установлена; этот документ не разрешает очередной rollout или исследование.

## Граница и источники

Использованы сохранённые inventory PR17, итоговый rollback receipt, штатные
`install-awg.py` / `install-tcp.py`, принятый real-systemd/native fixture.
Последний использованный serving-снимок:10 ноября11:10:17–11:14:04UTC.
Это **не свежий live-readback**. В этой задаче SSH к production не выполнялся.
Последняя подтверждённая комбинация: RU node125c796a, старый watcher
Restart=on-failure, gateway9023d2c3; центральная политика108/119.

| Контур | Что относится к переносу транспорта | Что остаётся |
|---|---|---|
| AWG | `friends-awg`: native binaries, gateway, settings, server key/config, peer mappings; обычный AWG service | Registry, identity keys клиентов, оплаченные сроки |
| TCP | `friends-tcp`: Xray, VLESS/Reality server key/config, API127.0.0.1:18085, service `fc-friends` | HTTP/control endpoint и issuer trust |
| Paid application | Node pyz, watcher, BindsTo/drop-ins, root-only TCP preflight; retained decisions/prepared/deny и привязки | Канонический ledger и весь enrollment-набор из трёх логических узлов |
| Центральные зависимости на прежнем RU | Нужна будущая адресная настройка регистрации и команд **только gateway-ru** | `friends-http-candidate`, registry/issuer, paid operator current, единственный reconciler/timer; leases NL продолжаются |
| Наблюдение | Будущие RU SSH host-key/endpoint и per-node source/unit pin, ресурсный inventory | HMAC, subscription/NL pins, PostgreSQL, история и пользователи панели |
| Остальное | Не входит | NL engines, MESH/cert/CRL, mailbox/chat, renewal, directory-sync, updater, APK и чужие службы |

**Важный блок переключения, не блок подготовки стенда:** текущий HTTP
`deploy/friends/access-api.py` для `country == 'ru'` запускает **локальный**
`awg-gateway.py register`. Замены IP в каталоге недостаточно. До canary-перевода
нужен отдельно проверенный узкий маршрут authenticated registration к новому
хосту (с pinned SSH/ограниченной командой, по существующему NL-контракту), без
замены всего HTTP текущей веткой. В этом комплекте HTTP не меняется.

`transport-enforcement.json` сопоставляет адрес с `gateway-ru`;
`transport-commands.json` рядом с registry используется первым enrollment;
reconciler имеет свой полный commands map. Все три требуют согласованного
будущего изменения RU-назначения. Логическое имя **gateway-ru сохраняется**,
его нельзя временно удалить, переименовать в четвёртый узел или дать двум
writer одновременно управлять одной службой. Стенд к этим maps не подключать.

## Неизменные входы проверочного узла

| Вход | Точное значение |
|---|---|
| Runtime source | `377cfe8a7a53ce0edc9d6691992ef97c1af5209c` |
| Принятый архив | `ru-command-budget-377cfe8a.tar.gz` |
| SHA256 архива | `bd4a48d3624618e974e3a7a28f4ebbfcd06fcf17c525c59a079658729e6ebef2` |
| Полный inventory | `3880cc50219846334923244613accce774c5790e42cf3c7db953503c9f433217` |
| Node | `b0d4e5096e3b40529a99de6841a80301c5c9b2845c6e7e3903c366a534211a45` |
| Watcher unit | `1887854790a4dcc2d6aee06e575c7f5311468304b3ff7e73d72e4bfb98f72e21` |
| Gateway | `9023d2c3f7c3a5127d67c509a16eb2d974810ff54d5b76cc225cd9b93e0b4234` |
| Xray26.3.27 | `4f7a4436f86798bbb5c875014e352021a1673710a45e170ccc507c5f59341940` |
| Xray upstream | `d2758a023cd7f4174a5a5fa4ff66e487d4342ba0` |
| AWG tool | `906d6795af1dd4adee7b11bf1e7fa133d4795c8a8d6e2099b34a026f810a3278` |
| amneziawg-go | `e7f00e47d6df853ade5dcd2fe79240f01ff897d75088c768316a444c27c87e0f` |
| Неизменный native/base image | `sha256:af9c993c2fcd60804ef576e2190dee88699830624ec74317a91eb6d9855284e9` |

Локально проверенный image: Ubuntu24.04.5, glibc2.39,
`/usr/bin/python3`3.12.3. Это выбранный воспроизводимый Python **стенда**, не
новое утверждение о Python на production. Native image экспортируется без
пересборки; fixture overlay добавляет только уже проверенные runtime bytes и
исполнитель испытаний. Нет скачивания `latest` на узле.

Штатные base units включены целиком. Xray main остаётся `fc-friends`,
MemoryMax256MiB/TasksMax128, NoNewPrivileges, ProtectSystem=strict,
ProtectHome/PrivateTmp, только NET_BIND_SERVICE, AF_INET/INET6/UNIX.
AWG main — root, MemoryMax256MiB/TasksMax128, ProtectSystem=full.
Watcher — Type=notify, **Restart=no**, Watchdog12s, Start45s, Stop5s.
Engines BindsTo/After watcher, KillMode=control-group/Stop5s.
TCP `ExecStartPre=+/usr/bin/python3 …/awg-gateway.py paid-preflight` выполняется
с root-доступом к состоянию, но не расширяет права основного Xray.
Operation8s / watchdog12s / lease120s и durability не изменены.

Существующий Docker/systemd fixture ограничивает каждый контейнер0.6CPU,
448MiB и192tasks; GOMAXPROCS2. Его SYS_ADMIN/NET_ADMIN и unconfined
seccomp/AppArmor нужны для вложенного systemd/cgroup, **не являются требованием
ослабить native production service**. Нет privileged/host-network/host-PID,
host mounts/socket/публичных портов внутри тестовых контейнеров. Docker socket
доступен только локальному операторскому harness, не gateway/web процессу.
Host/cgroup окружение записывается отдельно; оно не тождественно старому RU.

## Один handoff для выделения ресурса

**Отсутствует ровно один ресурс: отдельно разрешённый независимый Linux-хост.**
Не NL и не контейнер/VM на прежнем RU. Нужен disposable x86_64 VM/host с KVM/TUN,
systemd/cgroupv2, синхронизированными часами, Docker Engine29.1.3 с containerd
image store (`io.containerd.snapshotter.v1`) и Python3.12+venv. Это контекст
сохранённого OCI image:af9c993c — manifest digest, не digest JSON config;
обычный classic-store нельзя считать эквивалентным без проверки загрузки.
Практический запас:4vCPU/4GiB RAM/15GiB свободного диска; это вместимость пяти
ограниченных fixture-контейнеров, не вывод о причине старого отказа.
Потребуются root или sudo для Docker/TUN, отдельный операторский SSH public key
и подтверждённый fingerprint host-key. Передать адрес/идентификатор хоста,
разрешение на этот синтетический тест и способ доступа; **не пароль/ключ в чат**.
Отпечаток `/etc/machine-id` закрепляется перед запуском. Аккаунт/VPS не покупать.

Изменения на выделенном хосте: загрузка неизменного image, локальный venv,
закрытый рабочий каталог, временные private networks и пять собственных
контейнеров. Синтетические NL-роли — не рабочие Amsterdam1/2. Новые ключи,
63 identity, local registry и TLS fixture CA создаются только внутри испытания.
Production DB, client keys, host credentials, issuer/signing keys не копируются.
Стендовый CA используется через `curl --cacert`, не устанавливается в системный
trust store. Конечные receipts приватные; generated state не источник миграции.

### Локальная сборка обвязки, не пересборка runtime

```sh
python3 -m scripts.prepare_ru_replacement --accepted "$ACCEPTED_PR17" --destination "$NEW_KIT"
```

Проверяются SHA архива, полного inventory, оригинального qualification receipt,
каждый вложенный member, module inventory node, квалифицированная пара и
allowlist файлов. Произвольные соседние state/ключи не включаются. Затем
добавляются `native-image.tar` (docker save точного image), offline wheels с
закреплёнными hashes и общий `distribution-inventory.json`. Полный tar/digest и
provenance обвязки записаны в закрытом preparation receipt, отдельно от PR17 source.

### На отдельно разрешённом хосте

После внешней проверки SHA всего подготовленного tar, распаковать в новый0700
каталог. Внешний digest обязателен: внутренний inventory не подписывает сам себя.
Проверить свободные ресурсы, отсутствие product services/production credentials,
`/dev/net/tun`, cgroupv2, часы и host-key. Ничего не менять в сетях production.

```sh
cd "$KIT_ROOT"
sha256sum -c SHA256SUMS
docker load -i native-image.tar
python3.12 -m venv "$WORK/venv"
"$WORK/venv/bin/python" -m pip install --no-index --find-links wheels --require-hashes -r wheels/requirements.txt
mkdir -m 700 "$WORK/results" "$WORK/tmp"
cd source
TMPDIR="$WORK/tmp" PYTHONPATH="$KIT_ROOT/source" "$WORK/venv/bin/python" -m scripts.run_ru_replacement \
  --authorized-machine-id "$APPROVED_MACHINE_ID" --kit-root "$KIT_ROOT" \
  --report "$WORK/results/replacement.private.json"
```

Запуск не является bare-host installer. Штатные `install-awg.py`/`install-tcp.py`
в комплекте сохранены для следующей адресной операции; они делают enable/start,
поэтому запускать их неподготовленными нельзя. Перед будущим первым native start
нужны временная маска, точные paid dependency/preflight, синтетическое состояние
и проверенные права. `prepare_paid_transport.py` допускается только на **новой**
среде, отвергает существующий fence; он не средство сброса прежнего retained state.

## Конечная квалификация нового окружения

Новый профиль существующего fixture, не новая система deployment:

- 63 canonical records на каждом синтетическом узле, registered20/49/5,
  один paid. Это датированные количества из последнего receipt, не live inventory.
- 600s обычного watcher/reconciler исполнения, циклы примерно20s; реальные
  продления120s через исходный deadline, без неожиданных restart.
- Полные AWG allowed-IP и Xray id/email/flow сопоставляются с persisted и
  решениями; foreign synthetic TCP user не удаляется. Counts без сравнения наборов
  не PASS. Успешные apply/progress и per-call времена сохраняются приватно.
- AWG DNS через настоящий TUN, Xray remote DNS; HTTPS с проверкой fixture
  сертификата и ожидаемым node egress на обоих путях. Не host curl в обход VPN.
- Естественный paid expiry, прекращение обновления lease, noncohort continuity,
  свежая lease/восстановление, terminal revoke; затем один stop→PID0/ControlPID0/
  no jobs→последовательный start с packaged preflight; retained deny проверяется
  реальным отрицательным потоком и положительным noncohort.
- После первого failure нет retry-серии: receipt FAIL, собственные контейнеры,
  сети и overlay image удаляются. Общий watchdog harness1500s; это предел всего
  теста, **не изменение8s операции**. При forced host shutdown отдельно проверить
  остатки по точному run_id label, без global prune.

Результат сейчас: **NEW_HOST_QUALIFICATION=NOT_RUN**. Проверка планирования с
fake clock и валидация bytes — только local preparation, не native acceptance.
Будущий PASS относится к private IPv4 fixture, не к публичному IP/провайдеру,
IPv6, Android, реальному клиенту или долговременной стабильности. Вложенные
timings не суммировать. Повтор аналогичного отказа здесь — основание остановиться
для отдельного решения о модели контроля/восстановления, не нового diagnostic PR.

## Будущее переключение — план, не разрешение выполнять

1. Выделить независимый хост; пройти указанный профиль. Не подключать его как
   второго writer production. Синтетические ключи/registry не использовать позже.
2. Отдельно согласовать native installation и addressing: внешний IP, AWG UDP
   listen port, TCP443/8446, уникальная туннельная сеть без route conflict,
   firewall/NAT, API толькоloopback. Принять fresh node WG/Reality keys либо
   **отдельно разрешённый** перенос прежних; никаких ключей в этой подготовке.
3. До canary согласовать узкую HTTP RU-registration дельту, signed catalogs,
   endpoint-to-node map и pinned command maps. RU row обязана совпадать во всех
   NL-вариантах signed catalog (`gateway_routing.py`); нужны новые sequence/floors,
   не переписывание прежнего signed payload под прежним sequence.
4. Одного отдельно разрешённого тестового клиента перевести через изолированный
   адресный canary-путь, без общей публикации каталога/переключения maps остальных.
   Этот путь ещё не предоставлен: без него не обещать canary при прежнем глобальном
   `/configuration/ru`. Проверить authenticated registration, DNS/TLS/egress,
   решения, точныеbindings, lease/deny и возврат клиента.
5. После отдельного разрешения cutover: сохранить latest fingerprints/state,
   остановить новые регистрации RU/paid enrollment на короткий интервал, оградить
   старый RU apply, не останавливая NL. Перенести только разрешённые mappings и
   membership/prepared/deny под тем же `gateway-ru` по проверенной процедуре;
   свежие сроки принять от canonical, **не переносить boot/monotonic deadline**
   между хостами и не делать initial preparation поверх retained state.
   Затем один writer/новый registration route, согласованные maps/catalog и RU
   collector pins; проверить actual sets и завершить переключение остальных.
6. При отказе прекратить expansion. Вернуть согласованный старый routing/catalog
   с новым sequence, pins и кодовую комбинацию; перед старым start принять **свежие**
   canonical решения и все появившиеся deny/membership, не восстанавливать старую
   БД или старые leases. Нет безопасного readback — старые engines не открывать.

Уже выданные endpoint/server-public-key/Reality profiles и кеши автоматически не
меняются. Fresh keys требуют новых проверенных профилей; смена IP рвёт действующие
туннели, TCP reconnect ожидаем. DNS TTL не обновляет pinned ключи/литеральные IP.
Старые каталоги могут сохраняться у offline клиентов. Прозрачная миграция **не
доказана**. Production, paid/cohort/периоды, registry/issuer, APK, updater и NL
не изменялись; продолжение ограничено выделением одного указанного ресурса.
