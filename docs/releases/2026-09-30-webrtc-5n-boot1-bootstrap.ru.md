# 5N-BOOT-1 — Restricted-network bootstrap / rendezvous

## Результат и границы

**5N-BOOT-1 = PASS. Isolated physical acceptance30.09, 15:37–15:38 UTC.**
Текущий HEAD `f487a429141da64297038e8a96237205fd1ac060` + uncommitted focused
runner fix/tests/docs. Новых commits/push нет; gateway/Android runtime не менялся.
Redmi cellular: real automatic seed, authenticated directory/cache/restart,
diagnostic endpoint denial, bootstrap Family auth/broker/READY/descriptor,
separate dedicated Family TLS/binding, DNS A/AAAA/NXDOMAIN и four HTTPS200,
bounded cleanup — PASS. Полные live evidence и ограничения ниже.

### Первоначальный implementation checkpoint — исторический LIVE BLOCKED

Starting clean `main` = свежий `origin/main` =
`51d0ad788b651f47ba22e33b4a9991a1283661ce`.
Работа только в Family Connect, без subagents и соседних сервисов.

Причина первоначального live blocker: `YANDEX_TELEMOST_OAUTH_TOKEN` отсутствует в окружении
задачи и в проверенном окружении одноразового SSH command на авторизованном
Amsterdam `186.246.45.246`. Проверялась только boolean presence, не значение;
секретные файлы серверов не сканировались. Credentials не выдумывались.
Ни новый seed, ни dedicated room у реального провайдера в этой задаче не создавались.
Не было установки diagnostic APK, изменения cellular/Wi-Fi, adb reverse,
SSH forwarding, production services, routes, catalogs или offline signing key.

Предыдущий **Room Broker PASS** остаётся принятым, но его forwarding-based
control ingress не переименован в bootstrap proof. Никакой local/fake-carrier
результат ниже не заменяет обязательные physical phases A–E.

## Реализация

- `carrier/bootstrap/directory.go`: JSON version1, Family, issued_at/expires_at,
  seeds transport/join_url/gateway identity; строгие schema/URL/type/duplicate
  проверки. ≤8192B, ≤4 seeds, validity≤1h. Один seed публикуется в MVP.
- Directory приходит по existing Family TLS1.3/mTLS control trust, не подписывается
  application-update ключом и не вводит online signing root. Gateway identity
  сверяется с existing protected Family profile; room URL не является admission.
- Cache: mode0600, nonblocking cross-process flock, один staging file+fsync+atomic rename+
  directory fsync. Некорректное/expired содержимое не используется; valid cache
  не заменяется older/conflicting equal-issued directory. Same bytes — no-op.
  Android передаёт `getNoBackupFilesDir()`, backup выключен. Кэш переживает
  новый core process и interrupted staging write; physical app restart ещё не принимался.
- `SeedManager` создаёт отдельный seed существующим Telemost RoomProvider и
  публикует только после gateway Connect/READY. Lifetime/withdrawal независимы
  от10min per-device setup. Никакого переиспользования Room Broker state как seed.
- `FCB1` — routing envelope, не криптография: client32B+server32B random lease IDs,
  directions, один active worker. Different leases не смешиваются в ReliableStream.
  Первые OPEN/ACCEPT допускают bounded retransmission; новые rooms это не создаёт.
  Existing Telemost SFU video-slot selection не считается безопасным multi-party
  transport: прочие клиенты получают bounded busy/unavailable timeout. До4 VP8
  readers, без очереди bootstrap клиентов. Злонамеренный SFU всё ещё может дать DoS.
- После existing Family TLS: `HELLO` с existing Broker.Challenge ID →
  `REQUEST_TRANSPORT` → existing Broker.Create → dedicated gateway READY → Claim →
  `TRANSPORT_READY` → BYE/ack/final BYE. Generic ERROR, без provider details.
  Fresh server setup ID, TLS sequences и existing binding отсекают stale/replay.
- `SessionAuthorizer` переиспользует existing control verifier с Family ALPN:
  certificate chain, identity/role/Family, revision, CRL и expiry; provider call
  только после admission. Не дублирует admission DB. Recheck1s — как у брокера.
- Bootstrap **не создаёт Mux**. TCP OPEN, DNS QUERY, DATA, raw Mux/proxy bytes,
  malformed/oversized messages, duplicate REQUEST и wrong-state сообщения
  отвергаются. Descriptor выпускается только после dedicated READY.
- Diagnostic native core закрывает bootstrap, затем использует тот же dedicated
  Telemost/Family TLS/setup binding/Mux, который принят в5N.5/Room Broker.
  Java лишь читает mode и передаёт private cache path. Никакого VpnService/TUN,
  нового network stack или beta UX/transport-selection изменения.

## Лимиты и cleanup

| Ресурс | Настройка |
| --- | --- |
| Seeds в directory / active published seed | ≤4 / 1 |
| Active bootstrap exchanges | 1 на single seed/process, pending queue0 |
| Directory / lifetime | 8KiB / ≤1h |
| Bootstrap Connect / unauthenticated admission | 45s / 30s |
| Общая exchange / final BYE drain | 120s / ≤3s |
| REQUEST / READY JSON | 256B / 4096B |
| Envelope / carrier payload / queue | 69B / 33000B / 16 packets |
| VP8 readers / preparation HTTP sockets | 4 / 8 |
| Existing broker create / gateway READY | 15s / 45s |
| Outstanding dedicated setups | 1/device, 32 globally |
| Existing unused / lifetime / auth recheck | 60s / 10min / 1s |

Failure before confirmed handoff → existing Broker.Cancel. Disconnect/failed join
или failed dedicated admission после handoff → unused TTL cleanup, без hidden
HTTP cancellation через normal API. После accepted binding — existing Mux cleanup;
новый allowlisted `dedicated_resources_closed` означает0 sockets/streams/retained
bytes после Close. Seed shutdown ждёт owned workers; нет unbounded request cache
или tombstones. Expiration не обещает физическое удаление conference у Yandex.

## Проверки

- Go focused tests/race: bootstrap, roombroker, familysession, telemost,
  cmd/bootstrap-broker, cmd/telemost-binary — PASS на финальном source tree.
  Real disposable ProductStore fixture profiles были переданы через
  `FC_FAMILY_TEST_FIXTURES`; auth tests не skipped. Bootstrap race x10 — PASS.
- Directory malformed/expiry/invalid URL/transport/stale replacement/restart,
  atomic concurrent writes, seed READY ordering/withdrawal/provider failure,
  lease isolation/busy/cancellation/parser, application whitelist, duplicate and
  stale setup IDs, global/per-device bound, broker/provider/READY failure,
  descriptor expiry, disconnected/unused handoff cleanup покрыты focused tests.
- Existing Family admission tests включают expired certificate, wrong Family,
  unknown authority, revision/CRL, wrong gateway. New real-TLS path проверяет
  valid/unknown/wrong-Family/revoked/wrong-gateway/stale-CRL/stale-revision;
  existing dedicated binding tests проверяют other-device/setup/replayed proof.
- Python focused checks: **118 PASS**, два existing deprecation warnings;
  bootstrap evidence, Room Broker evidence, fixture issuer, Device Identity,
  product registration/provisioning/security. Использованы обе lockfiles.
  Evidence validator отвергает отсутствующий control-denial/cache/READY,
  неверный порядок, manual room, failed dedicated DNS/HTTPS и отсутствие cleanup.
- Relevant Go vet, Linux bootstrap-broker/telemost-binary build — PASS.
- Android arm64 CGO PIE native build — PASS; diagnostic APK assembleDebug — PASS;
  Gradle JVM **9/9 PASS** (3 bootstrap + 6 existing lifecycle); lintDebug — PASS
  с шестью warnings в existing manifest/UI (DataExtractionRules,
  MissingApplicationIcon, четыре SetTextI18n), без errors.
- Toolchain установлен изолированно в `/tmp`: Go1.26.0, JDK17, Gradle8.11.1,
  Android API35/build-tools35, NDK27.2.12479018. Старые чужие build/cache directories
  не перезаписывались: Gradle использовал временные project-cache/build paths.
- Docs checker `--all`: **400 files / 2409 links / 0 errors**; public-source guard
  и `git diff --check` — PASS. Проверка APK подтвердила точное совпадение native
  binary и отсутствие private profile/cache/key assets по именам ZIP entries.
- Sandbox не разрешал test sockets/Gradle daemon; итоговые checks выполнены
  с разрешённым outside-sandbox запуском. Зависший sandbox TestClient остановлен;
  те же focused Python tests успешно завершились вне sandbox.

Diagnostic артефакты собраны из starting HEAD + текущих изменений (dirty worktree),
не установлены и не опубликованы. SHA256:

- APK: `370e4796beaa2c8910dc896acc148f75b6e6a3a3d80395dea598c4f8b73ef432`.
- Native arm64: `45f7c9b6ec51068e95f4ab700ba96c3d81560066c9c35734f388fdc07905d485`.

Не запускались PERF-2/30min, historical full carrier matrix, Windows/Linux UI
suites или beta release pipeline. Используется Go1.26.0; Python environment
получен из control+device_identity lockfiles; новых production dependencies нет.

## Physical acceptance: PASS (30.09, final rerun)

| Обязательное свидетельство | Фактический результат |
| --- | --- |
| Phase A: direct authenticated control → seed READY → Android cache → app restart | PASS; cellular mTLS/cache, force-stop + process absence + new process/cache load |
| Phase B: ordinary control unavailable на physical Android | PASS; configured normal endpoint replaced with unreachable loopback, actual negative probe before cache load |
| Phase C: real Telemost bootstrap, Family auth, existing broker creation/READY, descriptor via seed | PASS; ordered real Android/server events |
| Phase D: separate dedicated room / Family TLS + setup binding | PASS; bootstrap closed first, dedicated Family admission + ACTIVE |
| Phase E: dedicated A/AAAA/NXDOMAIN + four HTTPS200 | PASS; four distinct streams, verified end-site TLS, exit0 |
| adb reverse / SSH forwarding / manual room input | Не использовались; runner не требует их |
| Bootstrap Internet proxy | Нет такой code path; negative whitelist tests |

[Новый isolated runner и runbook](../../carrier/bootstrap/README.md) запускают
server-only token, disposable `/tmp/fc-boot1-*` process, direct mTLS listener18444
на Amsterdam (не production ingress). Android сначала `refresh`, затем force-stop,
проверка отсутствия process и `recover` с normal endpoint `https://127.0.0.1:1`.
Native probe требует реальный `control_unavailable` перед чтением cache; дальше
только Telemost carrier. Нет operator-supplied seed/dedicated URL.
SDK/APK build сам по себе не означает installation или physical acceptance.

## Версии, rollback и оставшаяся работа

Версии не изменены: public Android0.1.18-beta51/code51; Linux0.2.11;
Windows0.2.15; diagnostic code4/name5N.5-test-only. Состояние public artifacts и
invitation pages повторно не проверялось; distribution/install claims не менялись.
No production deployment; production rollback не требуется.
Локальные logical commits: `f0be326` (directory/rendezvous core), `355b2db`
(Android/core integration), `e385fa2` (isolated runner/validator); документация
сохранена отдельным следующим коммитом. Push не выполнялся.

Local cleanup: два созданных задачей каталога disposable identity fixtures удалены;
task-owned test/Gradle/gateway/native processes после проверок не остаются.
Toolchain/cache и diagnostic build artifacts сохранены в `/tmp`, не в Git.
При первоначальном checkpoint live cleanup был NOT RUN. После двух live attempts
cleanup PASS: APK/cache/native process, remote process/directory и local disposable
profiles удалены; SSH children завершились. Детали повторного run ниже.
Isolated rollback: stop exact task-owned bootstrap-broker, wait child exit,
remove disposable remote directory, uninstall diagnostic APK/cache и удалить
task-owned local profiles после фиксации только sanitized evidence.

BOOT-1 physical phases A–E завершены; незавершённых действий внутри gate нет.
Fresh install уже restricted, Android whole-device/TUN, automatic Orchestrator,
generic UDP, seamless existing TCP migration, HA/seed pool, второй carrier, iOS,
production rollout и универсальные/capacity claims **не доказаны и не начаты**.
5N.6 NOT STARTED. После этого checkpoint STOP; push не выполнялся.

## Повторный physical preflight — 30.09.2026, 15:26–15:30 UTC

- Начальный worktree clean; четыре локальных BOOT-1 commits `f0be326`, `355b2db`,
  `e385fa2`, `f487a42` присутствуют. Ничего не pushed; starting implementation
  base51d0ad7 и предыдущие результаты не переименованы в новую live acceptance.
- OAuth в новом процессе **present**: только boolean проверка; значение не
  печаталось, не сохранялось, не передавалось серверу или устройству.
- Physical Redmi Note9 Pro / Android12 / arm64-v8a доступен по USB ADB.
  `wifi_on=1`, `mobile_data=1`; connected Wi-Fi и cellular, active VPN не обнаружен.
  Diagnostic package отсутствует, список adb reverse пуст. Wi-Fi prerequisite
  не выполнен; пользователю предложено вручную выключить Wi-Fi. ADB radios не менял.
- Sandbox не разрешил ADB listener; повторный preflight выполнен с разрешённым
  outside-sandbox запуском. Первый SSH на Amsterdam186.246.45.246 вернул
  `No route to host`; следующий read-only SSH прошёл, listener18444 отсутствует.
  SSH forwarding не создавался; другие gateway/production services не затронуты.
- Existing APK SHA256 совпадает с указанным выше; embedded arm64 native SHA256
  также совпадает. Existing Linux bootstrap-broker SHA256
  `f1d567240ae477001226b118324bae5c5f0cf4aeb49ff29ddda0ccdeff8c8f89`;
  Go build metadata: base51d0ad7 + dirty implementation tree, как в исходном отчёте.
  Новая сборка/установка/публикация не проводилась; code4/name5N.5-test-only неизменны.
- Созданы только новые disposable local ProductStore fixtures; generator проверил
  enrollment replay/unknown/revoked issuer rejection. Это не live Family auth proof.
  Из-за Wi-Fi preflight runner не запускался: **ни seed, ни dedicated room не созданы**,
  cache/restart, normal-control denial, bootstrap/broker/handoff/DNS/HTTPS NOT RUN.
- No implementation bug exposed, no runtime fix, no new regression run required.
  Ни PERF-2, ни долгий smoke, ни5N.6/TUN/Orchestrator/second carrier не запускались.
- Повторные docs/public-source checks: `check_public_docs.py --all` —
  400 files / 2409 links / 0 errors; `check_public_sources.py` — 1484 index entries /
  0 blocked files; отдельно те же source rules для трёх изменённых working-copy
  документов — PASS; `git diff --check` — PASS. Новых commits нет.
- Cleanup: task-owned disposable local profile directory удалён; серверный process,
  remote directory и diagnostic APK не создавались. Existing build/toolchain
  artifacts сохранены. Production rollback не нужен. Для следующего live run:
  fresh disposable profiles, существующий BOOT-1 runner; stop/remove только его
  процессы, private files и diagnostic APK/cache согласно runbook.
- Ограничения неизменны: no fresh install while already restricted, no whole-device/TUN,
  no Orchestrator, no generic UDP, no HA bootstrap pool, no second carrier,
  no production rollout/capacity claim. Никакое NOT RUN не засчитано как PASS.

## Live acceptance после user ready — PASS

Пользователь выключил Wi-Fi; read-only preflight подтвердил `wifi_on=0`,
`mobile_data=1`, connected cellular, no connected Wi-Fi/no active VPN, diagnostic
package отсутствует, adb reverse list пуст, Amsterdam port18444 свободен.
Использован только existing `pilot/android-telemost/bootstrap_acceptance.py`:
official Telemost provider через `SeedManager`, disposable ProductStore profiles,
те же проверенные Android/gateway binaries. OAuth передан SSH stdin в environment
только test process, не в command arguments/files/logs/Android/Git/CI.
ADB — install/config/start/restart/evidence/uninstall, не transport; SSH — setup,
evidence и cleanup test process на Amsterdam186.246.45.246, без forwarding.

### Первая live попытка: failed acceptance, не скрыта

`/tmp/fc-boot1-live2-evidence`, 15:34:58–15:35:49 UTC:
seed READY, cache/restart, negative control probe, real bootstrap Family auth,
broker READY, descriptor/handoff, dedicated binding, three DNS + four verified
HTTPS200 и Android exit0 прошли. Но runner завершился с
`RuntimeError: missing or duplicate lifecycle event`: он проверял gateway log
до собственного shutdown. `dedicated_resources_closed` появился только в cleanup
на15:35:49.284952225Z. В этом run PASS summary не записан; cleanup errors=[].

Конкретный defect — порядок final evidence validation в **acceptance harness**,
не bootstrap/transport runtime. Удалено преждевременное10s ожидание; после `finally`
(Android uninstall, remote stop/remove, SSH wait, log close, cleanup success)
runner заново читает полный gateway log, проверяет тот же строгий event order и
только тогда пишет PASS. Никакие обязательные events/checks не ослаблены.
Focused regression проверяет close-event только при shutdown, missing close и
cleanup failure (последние два обязаны не создавать PASS). Команда
`/tmp/fc-boot1-venv/bin/python -m pytest -q tests/test_bootstrap_acceptance.py`:
**20 passed**. Gateway, Go/Android code и APK не менялись; широкие suites не запускались.

### Final rerun: ordered physical evidence

`/tmp/fc-boot1-live3-evidence`; новый automatic seed и новый dedicated room.
Ни operator room URL, ни прежний directory/cache не подставлялись. Cache получен
самим Android по direct cellular Family mTLS18444. `getNoBackupFilesDir()` + mode0600,
atomic cache implementation неизменны; force-stop/process-absence check отделяет
refresh от нового Android/native process. Recovery не делает directory refresh.

| UTC30.09.2026 | Allowlisted свидетельство |
| --- | --- |
| 15:37:41.370119490 | Server `bootstrap_seed_ready`: автоматически созданный seed, gateway READY до directory publication |
| 15:37:46.367024979 | Android `bootstrap_cache_stored`, refresh exit0, затем force-stop и отсутствие process |
| 15:37:48.613407009 | Новый Android process: `bootstrap_normal_control_unavailable` |
| 15:37:48.613719926 | `bootstrap_cache_loaded`, ранее сохранённый protected directory |
| 15:37:50.678328831 | `bootstrap_carrier_connected`, real Telemost bootstrap |
| 15:37:54.432318257 / 15:37:55.327179653 | Android/server `bootstrap_family_auth`, existing Family TLS |
| 15:37:56.327601738 / 15:37:56.845711898 | Existing Room Broker `CREATING` / `CREATED` |
| 15:37:58.941756281 / 15:37:58.942106114 | Dedicated gateway `READY` **before** `CLIENT_ISSUED` |
| 15:38:00.409387502 / 15:38:00.799381223 | Server `bootstrap_handoff`; Android `bootstrap_descriptor_received` через bootstrap carrier |
| 15:38:00.802362733 / 15:38:03.133335962 | Bootstrap closed first, затем отдельный dedicated carrier `connected` |
| 15:38:09.340967577 / 15:38:09.657428355 | Dedicated `ACTIVE` / Android `family_auth accepted=true` после setup binding |
| 15:38:14.308530801–15:38:15.205676999 | Four `mux_https`, distinct stream IDs1/3/5/7, end-site TLS verified и HTTP200 |
| 15:38:15.376944447 / .502732415 / .603640019 | Family DNS A / NXDOMAIN / AAAA, все passed |
| 15:38:15.608373197 | `mux_result PASS`, public smoke5.945s; Android exit0, cancelled=false, total27.096s |
| 15:38:17.187004488 | Gateway `dedicated_resources_closed` при bounded shutdown; final cleanup errors=[] |

HTTPS: два запроса example.com и два speed.cloudflare.com; TLS1.3 проверен
самим end-site клиентом, не gateway MITM. DNS A/AAAA: rcode0/two answers each;
NXDOMAIN: rcode3/zero answers. Existing native DNS-denial guard negative probe
blocked=true и final post_probe_calls=0. Client Mux final ActiveSockets=0,
ActiveStreams=0, RetainedBytes=0; gateway close event проверяет те же нулевые
resources. Нет PERF-2, capacity sweep или длинного data test.

### Security и точный scope отрицательного условия

- Normal **configured diagnostic control endpoint** заменён с direct Amsterdam
  URL на `https://127.0.0.1:1` перед recovery. Native actual request вернул
  `control_unavailable` **до** cache load. Этот endpoint не менялся до завершения;
  recovery использовал только cached directory и bootstrap carrier, не HTTP broker.
  Это deliberate endpoint-denial injection, **не firewall/ISP block реального
  production API и не доказательство whole-device restriction**. Preparation
  listener остаётся до cleanup, но не доступен через recovery configuration.
- Bootstrap несёт только lease/Family TLS/HELLO/REQUEST_TRANSPORT/TRANSPORT_READY/BYE;
  `Exchange` не создаёт Mux/TCP/DNS proxy. Dedicated URL обязан отличаться от seed;
  Family TLS/binding precede Mux. Existing whitelist, unauthorized/revoked/wrong-family,
  replay/duplicate/expiry tests исходного checkpoint остаются применимыми:
  соответствующий runtime и его проверенные binaries не менялись. Эти adversarial
  checks **deterministic**, не выдаются за новую live attack campaign.
- Все15 acceptance items покрыты: cache-before-restriction + restart; control
  negative probe; real seed; existing auth/protections; broker/new dedicated/READY;
  descriptor through bootstrap; no bootstrap data plane; separate handoff;
  dedicated binding/DNS/HTTPS; bounded cleanup. Это isolated diagnostic acceptance,
  не production implementation/rollout и не универсальная carrier availability.

### Cleanup, provenance и STOP

Оба test runs: точные task-owned remote executable stopped, remote private
directory удалён, SSH child waited; diagnostic APK/cache/native process удалены.
Независимый read-only check после final run: package/process отсутствуют,
adb reverse list пуст, port18444 не слушает, `/tmp/fc-boot1-*` directories на
Amsterdam отсутствуют. Task-owned local disposable profiles/DB удалены.
Wi-Fi остаётся OFF/cellular ON по выбору пользователя; ADB radios не менял.
Исходные build/toolchain artifacts сохранены, runtime private data в Git не попали.
Provider conference deletion не обещается: gateways вышли, процессы и sockets закрыты;
API удаления конференций этот MVP не предоставляет. Production rollback не нужен.
При повторном isolated run rollback тот же: stop/remove только task-owned
process/directory и diagnostic APK/cache, затем удалить disposable profiles.

Версии неизменны: diagnostic code4/name5N.5-test-only (установлен для двух run,
после каждого удалён, **не опубликован**); public Android0.1.18-beta51/code51,
Linux0.2.11, Windows0.2.15. Public artifacts/invitation pages заново не проверялись,
distribution/catalogs не менялись. Binary hashes — исходные выше; новые builds нет.

Final evidence SHA256 (локальные sanitized файлы, не credentials):

| File в `/tmp/fc-boot1-live3-evidence` | SHA256 |
| --- | --- |
| `evidence.json` | `14335aa5d3e9e92f2ecd452456701d70772044cfe6181f3e8883a08b6f9b8915` |
| `gateway.jsonl` | `aed34f01c5369621dac0d90a7391070f594782a525cea84953e81c16e02026a0` |
| `refresh.jsonl` | `3abc0f5d1af821df3fe88fbcbf6cd984065da023b68d8d209f54c63b16365bf8` |
| `recover.jsonl` | `4dd9ea09a0351d4b248dbb2158c92262f2327ae1b0349f2472a311d6152e3d44` |
| `cleanup.json` | `3d0cc2bf1e46b446640c5e3fcb748dce45ca9e7b63fb4854c6aa7709bdb9416c` |

Final checks: focused Python20 PASS; docs `--all` — 400 files / 2410 links /
0 errors; public-source guard — 1484 index entries / 0 blocked files; дополнительно
все9 modified working-copy files проверены теми же source rules — PASS;
`git diff --check` — PASS. Новых commits нет; HEAD остаётся `f487a42`,
worktree содержит только runner fix, regression и7 documentation files.
Push: no. Production changed: no.

**Точные ограничения:** no fresh install while already restricted; no whole-device/TUN;
no Orchestrator; no generic UDP; no HA bootstrap pool; no second carrier;
no production rollout/capacity claim. 5N.6 NOT STARTED. **STOP после BOOT-1 PASS**.
