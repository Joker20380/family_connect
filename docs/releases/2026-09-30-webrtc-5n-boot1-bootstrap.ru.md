# 5N-BOOT-1 — Restricted-network bootstrap / rendezvous

## Результат и границы

**5N-BOOT-1 = IMPLEMENTED / LIVE BLOCKED. Не PASS.**
Starting clean `main` = свежий `origin/main` =
`51d0ad788b651f47ba22e33b4a9991a1283661ce`.
Работа только в Family Connect, без subagents и соседних сервисов.

Причина live blocker: `YANDEX_TELEMOST_OAUTH_TOKEN` отсутствует в окружении
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

## Physical acceptance: NOT RUN

| Обязательное свидетельство | Фактический результат |
| --- | --- |
| Phase A: direct authenticated control → seed READY → Android cache → app restart | NOT RUN; deterministic mTLS/cache tests PASS |
| Phase B: ordinary control unavailable на physical Android | NOT RUN; guarded diagnostic endpoint implemented |
| Phase C: real Telemost bootstrap, Family auth, existing broker creation/READY, descriptor via seed | NOT RUN |
| Phase D: separate dedicated room / Family TLS + setup binding | NOT RUN |
| Phase E: dedicated A/AAAA/NXDOMAIN + four HTTPS200 | NOT RUN |
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
Live cleanup **NOT RUN**, так как ни gateway test process, ни APK на устройстве
не запускались; детерминированные cancellation/worker/broker cleanup tests PASS.
Isolated rollback: stop exact task-owned bootstrap-broker, wait child exit,
remove disposable remote directory, uninstall diagnostic APK/cache и удалить
task-owned local profiles после фиксации только sanitized evidence.

Открыто: предоставить provider credential безопасно в server/runner environment,
завершить physical phases A–E строго новым runner и сохранить cleanup evidence.
Fresh install уже restricted, Android whole-device/TUN, automatic Orchestrator,
generic UDP, seamless existing TCP migration, HA/seed pool, второй carrier, iOS,
production rollout и универсальные/capacity claims **не доказаны и не начаты**.
5N.6 NOT STARTED. После этого checkpoint STOP; push не выполнялся.
