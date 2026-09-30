# MVP Connectivity Orchestrator — 30.09.2026

**MVP CONNECTIVITY ORCHESTRATOR = PASS**, final isolated physical follow-up01.10.2026
(30.09 UTC). Normal Chrome исправлен, fresh automatic BOOT-1/restricted acceptance,
602.6s smoke и cleanup завершены. Не public rollout; Krasnodar FIELD-1 не запускать.

**Исходный результат30.09: MVP CONNECTIVITY ORCHESTRATOR = FAIL.** Implementation
complete; normal Chrome acceptance FAIL, restricted live BLOCKED. Этот результат,
его evidence и commits сохранены ниже, а не переписаны в исторический PASS.

Starting HEAD/main/origin: `8886fd03398ffecd82ab4f66ff6d9884846e628c`, clean.
Работа только Family Connect. No push, production deployment, version/catalog/public
artifact changes. FIELD-1 не начат. Этот отчёт не переносит предыдущие physical PASS
BOOT-1/5N.6 на новый Orchestrator автоматически.

## Follow-up 01.10.2026 — два acceptance blockers

Исходные FAIL attempts ниже сохранены. Продолжение начато с clean
`a00fe8a80f313e8770c1a0dbf26bf85c464a3c72`; `ac2dc65`, `c863ead`, `a00fe8a`
не переписываются и не публикуются. Время новых live runs —30.09 UTC /01.10 Brussels.

### Native provenance и воспроизведение

Cached `libfc-awg.so` действительно имеет SHA256
`9d20e5312e4d22c3c3d650513e82a43ec5c37a472810eb5e3acf206713023fbb` и старый
TCP source hash. Это acceptance provenance defect, **но не причина Chrome failure**:
полный fresh arm64 build текущего normal source воспроизводит тот же отказ.
Другие ABI/платформы не пересобирались; four-ABI validation не заявляется.

- Normal native SHA256: `960896a89bc108d07ff9ab518637acc76b9eec9bf36175fa07baeac8f52d03bd`.
- Native source revision: `a00fe8a80f313e8770c1a0dbf26bf85c464a3c72`;
  TCP source SHA256 `be122bb32c4ecf59a6c3d49aaa2a8015e61562cd4123ef65b0278974dc05d988`.
- Builder SHA256 `61036e9f70ac5cdb8ac654bb3c88423d0bcf3306e5b0244a4b3dbd6b22fb826d`;
  Go1.26.1, NDK27.2.12479018, pinned Xray `d2758a023cd7f4174a5a5fa4ff66e487d4342ba0`.
- Fresh pre-fix APK SHA256 `d8e37e272e4312161dde5db3fe288eb9f6152478822edc12bdfe580f210bd47b`.
- Post-fix APK SHA256 `711c4df8fa47561b8bfe9dca6ede7ff5a01b2bd8314ad2bda3d708c4553569f2`;
  **тот же normal JNI**, изменена только Java automatic TCP address declaration.
- Fresh restricted JNI SHA256 `5428ddf110f4abcd34087f79d6f8a1d92920e5e610dfe809583801723f6a3de0`;
  current source, Go1.26.0/NDK27.2.12479018.

APK verifier сверяет embedded bytes с manifest; physical runner дополнительно
отвергает несовпадение current TCP Go/JNI/builder hashes и отсутствие source revision.
Детерминированные positive/negative tests проверяют stale source, builder и binary.
Новые output/ABI flags builder сохраняют four-ABI CI default; временная Gradle
sourceSets override использует fresh assets/JNI без замены исходных ignored caches.
Дополнительно SHA256 **установленного** `/data/app` APK и extracted
`libfc-awg.so` на Redmi совпали с post-fix APK и fresh native hashes выше.

### Доказанная причина и минимальная правка

Normal-live1 с fresh JNI: TCP692ms, Java HTTPS200/TLS×2, Chrome
ERR_CONNECTION_CLOSED×2; alternate2616ms и bounded restoration работают.
Normal-live2 с ограниченным sanitized fixture trace: две IPv4 probe flows получают
OPEN/OPEN_OK и TLS1.3; затем18 controlled IPv6 attempts получают **network is
unreachable** на gateway, без OPEN_OK. На Amsterdam отсутствует IPv6 default route.
Закрытие инициирует backend после failed IPv6 dial, не Chrome и не Orchestrator.
TUN принимает локальный TCP handshake раньше remote connect: Chrome выбирает
объявленный IPv6 path и уже не получает своевременный connect-failure для Happy
Eyeballs. Java probes выбирают IPv4. Неподтверждённый IPv6 source address в
automatic TCP Builder делает этот mismatch видимым обычному браузеру.

Normal-live3 — дополнительная попытка того же APK на approved primary gateway с
IPv6 route: diagnostic port18445 закрыт существующим INPUT firewall; candidates
exhausted22492ms, Chrome не запускался. Firewall/production не менялись, cleanup PASS.

Fix `afb6c1b`: удалить только `.addAddress("fd79:fc::2",128)` из automatic TCP
Builder; сохранить IPv4 address, **обе capture routes** `0.0.0.0/0` и `::/0`,
DNS, protected underlay, single owner и все budgets/policy. Без объявления
непроверенной IPv6 source connectivity Chrome выбирает рабочий IPv4 normal path.
Ни native TCP/half-close/RST, ни HTTP/2, QUIC policy, restricted carrier или
Orchestrator ordering не менялись. Manual TCP IPv6 contract не изменён.
Это не обещание IPv6 Internet на IPv4-only gateway: synthetic TCP connect само по
себе не доказывает remote IPv6 data, и normal IPv6 socket probe не используется как
restricted fail-closed evidence.

Normal-live4 на **исходном Amsterdam fixture**, post-fix APK и том же fresh JNI:
Chrome example.com/example.org PASS, Java HTTPS200/TLS×2 PASS, normal572ms,
forced AWG→TCP alternate3525ms, controlled loss/restoration и second-loss FAILED
с retained full-route VPN/blocked ordinary TCP PASS. Controlled fixture trace:
четыре IPv4 OPEN_OK, controlled IPv6 unreachable0. Во всех проверках owner1,
`bypassable=false`; после cleanup owner0. Live AWG не повторялся: только forced
unavailable AWG + deterministic regression, не live AWG success.

### Fresh automatic restricted follow-up

OAuth доступен только в новом operator process; значение не выводится, не
записывается в файлы/Git/CI. Build/test/ADB subprocess environment очищается от
OAuth; final isolated bootstrap-broker получает его через stdin только в memory.
Новая disposable Family activation создана; expired fixtures не переиспользуются.
**Restricted-live1 = PASS**, не перенос старой EU-6 acceptance. Redmi Note9 Pro,
Android12/arm64, Wi-Fi OFF/cellular ON/no other VPN, no adb reverse/SSH forwarding.
Refresh/cache/restart — предварительная activation; затем действие пользователя
**только CONNECT**, без выбора транспорта/manual room URL.

| Критерий | Final live evidence |
| --- | --- |
| Normal exhaustion | `deny_normal` делает все configured approved AWG/WG/TCP unavailable. AWG attempt247/failure251ms; WG2271/2279ms; TCP6293/6301ms. Это diagnostic simulation, не ISP/Краснодар claim. |
| Automatic restricted | Restricted attempt10308ms → CONNECTED32615ms / time-to-connected32621ms. Ровно4 attempts, restricted success1; no manual recover Intent. |
| Cached BOOT-1 | Official seed READY22:27:53.861 UTC; authenticated cache сохранён, process restart проверен, native cache loaded без повторного refresh/normal control fallback. |
| Real bootstrap / Family / broker | Bootstrap Family auth22:28:41.255 UTC; fresh dedicated READY22:28:44.135131, CLIENT_ISSUED22:28:44.135599; handoff22:28:45.351; separate dedicated Family auth22:28:53.253, ACTIVE22:28:54.138. Bootstrap закрыт до dedicated data/VPN packet readiness. Эти UTC — server clock; durations — local monotonic counters. |
| Chrome / end-site TLS | example.com/example.org по3 ordinary Chrome visits:6/6 content PASS, VPN active, no browser errors. Дополнительные ordinary Android HttpsURLConnection2×HTTP200 с обычной TLS verification; не замена browser proof. |
| Family DNS / concurrency |125 Family DNS requests,115 responses,8 timeouts,0 DNS errors; уникальный NXDOMAIN PASS.33 successful TCP,18 concurrent TCP/Mux streams; all admission peak25. |
| Underlay |116 protected sockets,0 protect failures; provider DNS16→16 весь active smoke. App DNS растёт независимо. No recursion/direct destination fallback. |
| Unsupported traffic |UDP rejected184, IPv6 rejected22; ordinary UDP443 probe отправлена в TUN, IPv6 connect failed-closed. Generic UDP/QUIC и IPv6 не обходят VPN. |
| Active failure | Owned dedicated gateway SIGTERM после smoke; `transport_lost` → RESTORING → FAILED138ms, no candidate retry. Full routes/Family DNS/VPN owner сохранены, health unavailable; ordinary TCP1.1.1.1:443 и Chrome blocked. |
| Cleanup |Failed candidate: active TCP/streams/sockets/retained bytes/carrier queues0, goroutines18. Explicit DISCONNECT снял VPN; APK/cache и isolated server dirs/processes удалены. |

**Direct destination DNS leak count=0; direct protected TCP bypass count=0 в принятом
primary-user route/backend/app scope.** Live default IPv4+IPv6 routes,
DNS10.79.0.1, UIDs0–99999/no exclusions/`bypassable=false`; Family DNS при неизменном
protected provider DNS, existing backend без destination dial, reject counters и
negative ordinary TCP после failure. Не root modem-wide pcap и не аудит других
Android users/work profiles. Provider signaling/media/DNS — разрешённый underlay.
Private DNS/DoT специально не проверен; special support не заявляется.

### Smoke, ресурсы и неидеальные счётчики

**602.6s light smoke**, без throughput benchmark/PERF-2. No crash, transport flapping
или retry storm; bounded event log остаётся CONNECTED без restoration до injection.
Native121 samples/601.545s: PSS peak120019KiB, Go heap12641024bytes, goroutines175;
12 OS samples: RSS194792KiB, VmHWM194992KiB, threads40. CPU average5.72% одного ядра
(app Java+JNI, не Chrome), не instantaneous CPU peak. Battery31.3→32.3°C,
100→100%, FULL/USB; battery drain без зарядки не измерялся.
Mux retained HWM1180165bytes, receive/send16384/16384bytes, queue HWM8;
carrier send/receive sampled peak5/0, reliable retained peak29096bytes/depth8.
Никакого resource tuning не сделано.

Не скрывать: mux OpenErrors1, ProtocolErrors7, DNSTimeouts8;125 requests/115 responses
не называются125 успешными DNS. Эти bounded counters не вызвали crash/flapping,
ordinary browser6/6 и explicit HTTPS2/2 успешны; причины отдельных фоновых/late
flow errors не локализовывались, browsing content не собирался. Это не zero-error
network/performance guarantee и не основание начинать tuning вне двух blockers.

### Final regression, commits и rollback

- Python98 focused PASS: orchestrator/owner, provenance mismatch, bounded trace,
  BOOT-1/5N.6/automatic runner, AWG vectors/recovery, public source contracts.
- Android JVM185/27 suites PASS, debug APK + androidTest APK compile PASS;
  lint0 errors/35 existing warnings. Full emulator/native instrumentation suite
  не запускался; real JNI runtime принят physical Redmi run. Mid-phase cancellation
  остаётся deterministic regression; physical stop/cleanup bounded, не новая полная
  cancellation matrix. Live AWG не повторялся.
- Current normal host Go tests + race/vet PASS; carrier wholedevice/underlay/
  bootstrap/roombroker/familysession/tcpforward race/vet PASS; packet adapter race/vet
  PASS. Sandbox socket failures повторены вне sandbox успешно. Host driver build
  сначала упёрся в VCS stamping временной directory; повтор с `-buildvcs=false`
  PASS, как и host unit/race/vet и fresh native build.
- Source guard0 blocked files, OAuth literal persistence guard0 matches,
  documentation/link checks и `git diff --check` PASS. No token value в output,
  files, commits, CI или server files; disposable private activation удалена.
- New local commits: `afb6c1b` focused runtime/test fix; `87272e1` fresh provenance;
  `12d4f40` bounded physical diagnostics/automatic restricted runner/tests/runbook.
  Reviewed source HEAD `12d4f40`; final STATUS/PLAN/report сохранены отдельным docs commit.

Independent cleanup: `.orchestrator` absent, VPN owners0, adb reverse empty,
Wi-Fi0/cellular1; оба authorized gateway не имеют task directories/listeners18444/
18445. Исходные ignored normal/restricted generated caches не подменялись.
Sanitized attempt evidence и fresh local build artifacts оставлены в
`/tmp/fc-orchestrator-final/` для audit; disposable private Family fixture удалён.
Public Android beta51/code51, Linux0.2.11, Windows0.2.15, catalogs и invitation pages
не изменялись/не публиковались. Diagnostic APK built/installed/removed, не release.
Rollback — stop/uninstall только `.orchestrator`, terminate только owned isolated
fixture PID/path; production profiles/DB/services не затрагивать. Все эти шаги
выполнены. Public artifacts повторно не проверялись, rollout не заявляется.
Оставшиеся проверки вне этого gate: live AWG rerun, full four-ABI/native emulator
CI, production packaging/distribution и field evidence. **No push, no production
deployment; FIELD-1 NOT STARTED. STOP.**

## Политика и lifecycle

`ConnectivityOrchestrator` — deterministic Java core, без Android/network dependency.
Состояния: DISCONNECTED → CONNECTING → CONNECTED; loss → RESTORING → CONNECTED
либо FAILED. User cancellation → DISCONNECTING → DISCONNECTED. FAILED сохраняет
блокирующий VPN до явного DISCONNECT; очистка нативных ресурсов не снимает routes.

В одном проходе каждый configured normal candidate используется один раз: безопасный
last-known-good transport ID, затем preferred ID, затем оставшиеся **фактически
настроенные** транспорты. Duplicates/неактуальные hints исключаются. После normal
списка ровно один restricted candidate: cached directory → BOOT-1 → fresh Room Broker
descriptor → separate dedicated Family session → existing whole-device Mux/DNS.
Automatic path больше не делает диагностический запрос к loopback control endpoint.
Диагностический5N.6 entry point сохранён отдельно.

Friends использует существующий signed configuration/identity verifier и approved
catalog templates. Provisioning HTTP ограничен существующим fixed Family endpoint,
использует существующий explicit physical-network binding; не destination bypass.
Managed-journal recovery/resume не обходится этим legacy/Friends Auto mode.

Bounds: configuration30s, каждый normal20s, restricted200s, общий CONNECT300s;
backoff между кандидатами2/4/4s, при первом restoration candidate1s. Per-candidate
retry0, автоматическое восстановление **один проход на пользовательский CONNECT**.
Таймеры monotonic, health sockets bounded до оставшегося candidate budget. Native
stop обязан завершиться перед следующим backend; cleanup error terminal. Healthy
path не получает faster-path probes и не мигрирует. Active-flow survival не обещан.

Категории: CANCELLED, AUTH, CONFIGURATION, NETWORK, TRANSPORT_UNAVAILABLE,
BOOTSTRAP_UNAVAILABLE, INTERNAL. Explicit auth/revocation/configuration/internal
terminal, без cycling. Silent normal transport rejection неотличим от network outage;
при явном denial Family control cache fallback не выполняется. При потере restricted
session текущий native boundary не различает remote revocation и network failure:
консервативно RESTORING → FAILED/INTERNAL без повторного admission.

## Один Android VPN owner / fail-closed

`ConnectionService` сохраняет operation owner, worker, cancellation и generation.
Auto использует существующий `TcpVpnService` для guard и всех backend adapters.
`AutomaticNormalEngine` переиспользует existing AWG JNI и NativeTcp, не запускает
GoBackend VpnService параллельно. Manual normal factory не меняется.

Сначала full-route IPv4+IPv6 guard, затем configuration/transport work. При смене
сначала establish нового guard в **том же** VpnService, затем закрытие предыдущего
Java fd и backend cleanup. Guard route удерживается и при FAILED. AWG получает dup
fd; native close не освобождает последний owner-held fd. Нельзя запускать следующий
backend после неуспешного cleanup. Protection существующих underlay sockets сохранена.

Restricted backend использует существующий gVisor/Xray packet adapter, Family DNS
и Mux. Generic UDP и IPv6 Internet не добавлены. Никакого второго carrier или нового
packet stack. Android permission revocation/process death снимают OS authority:
always-on/lockdown guarantee **не добавлен**. Service START_NOT_STICKY, новое явное
CONNECT начинает новую сессию; live room/session/CONNECTED не восстанавливаются из
preferences. BOOT-1 сам проверяет cache TTL и получает новый dedicated descriptor.

## UI и diagnostics

Main/Friends default Auto, primary CONNECT/DISCONNECT. Existing explicit manual
selection остаётся diagnostic/advanced opt-out; выбранный ранее manual preference
не переименовывается в Auto. Status Connecting / Connected / Restoring / Unable.
FAILED удерживает VPN: для остановки пользователь нажимает DISCONNECT.

Private atomic `files/connectivity-events.json`: максимум128 allowlisted records,
только event/state/candidate/category/elapsed_ms. CONNECT, попытка, failure, fallback,
success/TTC, restoration и disconnect; нет payload, URL, destination, DNS query или
history. Preferences хранят лишь normal transport ID; AUTH/config error удаляет hint.
Производственного telemetry backend нет.

Debug-only `OrchestratorDiagnosticActivity`: импорт disposable normal profiles
из no-backup files (raw удаляется после encrypted import), forced deny_normal/
deny_primary и controlled fail_active. Release manifest не экспортирует эти controls.
Diagnostic normal failure **не доказывает реальный ISP allowlist**.

## Проверки / physical ledger

Deterministic validation:

- Android JVM:185 tests /27 suites,0 failures/errors/skips;18 новых state-machine
  cases. A/B/C/D, cancellation primary/alternate/bootstrap/broker/dedicated,
  auth/config/internal terminal, sticky/LKG, один restoration budget, restart,
  single-backend/cleanup, monotonic deadline и128-event bound. Restricted success
  в этих тестах — fake Host, **не physical BOOT-1 acceptance**.
- Focused Python76 PASS: Android identity/control, AWG31 vectors, normal/restricted
  ownership contracts, BOOT-1/5N.6 runner parsers, current runner schema/localization.
- Go race/vet: `wholedevice`, `underlay`, `bootstrap`, `roombroker`, `familysession`,
  `tcpforward`; packet adapter race/vet PASS с существующим Xray local replacement.
- arm64 restricted JNI, Android debug APK и androidTest APK build PASS; lint0 errors,
  35 warnings. Emulator/native instrumentation suite **не запущен**, только compile.
- Local sandbox не разрешил Gradle sockets / Go network tests; повтор вне sandbox
  PASS. Это environment failure, не product regression.

Artifact provenance:

- Final APK SHA256 `c5db0a6760d74f23af693fb03d482426b0952c3e666aae3d47ac36a75f10b7d8`.
  Live6–10 использовали `e0e6951ffecb676dd5c0ce642ac258be988e89a940327f880eed4617e61b1358`;
  после них усилены provisioning read deadline и best-effort diagnostic write перед
  native stop (ошибка записи evidence не должна мешать cleanup).
- Restricted JNI SHA256 `664be59d6e7d157ff70c421e845fe1b913ee5e16c7a3a2110ccfe152922973bc`;
  новый source build с Go1.26.0/NDK27.2.12479018, arm64.
- Normal JNI — existing cached artifact, SHA256
  `9d20e5312e4d22c3c3d650513e82a43ec5c37a472810eb5e3acf206713023fbb`.
  Его TCP source hash `f5ec5e4908e56ebd595f1b96bf5d83fafad996105a75a73f9bbd4ee469eec1a6`
  соответствует f42afb5; более поздняя XHTTP branch e168283 отсутствует. REALITY branch
  не менялась. Полный current-source four-ABI normal rebuild/XHTTP regression
  **не заявлен**; public installed beta не обновлялась.

Physical ledger (санитизированные local `/tmp/fc-orchestrator-normal-live*/` JSON,
без profiles/room URLs/traffic content; значения перенесены сюда перед cleanup):

- Первый preflight: Redmi отсутствовал; затем пользователь подключил Redmi Note9 Pro,
  Android12/arm64. Wi-Fi0/cellular1/no other VPN/no adb reverse подтверждены.
- `YANDEX_TELEMOST_OAUTH_TOKEN` отсутствует в текущем окружении (проверен только
  boolean, значение не выводилось). Fresh restricted live acceptance пока BLOCKED.
- Normal live1: временный isolated `/tmp` REALITY process на Amsterdam, diagnostic
  package `.orchestrator` установлен. MIUI отказал ADB input с INJECT_EVENTS; CONNECT
  не выполнен, событий Orchestrator нет, PASS не заявлен. APK/server cleanup PASS.
- Дальнейшая проверка использует **ручное** нажатие CONNECT/Android permission,
  а не обход MIUI permissions. Production beta package/credentials не используются.
- live2: ожидание CONNECT истекло без событий; cleanup PASS.
- live3/4: внешний camouflage не дал usable fixture; TCP deadline20.165/20.221s,
  automatic restricted attempt22.318/22.364s, отсутствующая activation →
  BOOTSTRAP_UNAVAILABLE/FAILED22.476/22.503s. Не доказательство real ISP restriction.
- live5/6: fixture переведён на CI-style local TLS camouflage в owned `/tmp` process;
  Auto TCP CONNECTED570/562ms, один VPN owner/full routes. Chrome parser не подтвердил
  страницы; это **не browser PASS**, все artifacts/processes удалены.
- live7: Auto TCP530ms; ordinary Java HTTPS к двум контрольным public sites
  HTTP200/TLS verified, NXDOMAIN expected, VPN active. Normal IPv6 может работать:
  restricted IPv6 fail-closed сюда не переносится. Chrome parser ограничивался `text`,
  затем добавлен accessibility `content-desc`; отсутствовал RESTORING после injection.
  Один снимок PSS133241KiB/RSS245624KiB — **не peak**.
  После cleanup battery100%,30.7°C, thermal status0 — не ten-minute smoke metrics.
- live8/9: Auto545/523ms. Причина отсутствия injected loss установлена: `am start`
  возвращал Status OK + Warning и доставлял Intent в **MainActivity**, не debug
  Activity; failure flag не выставлялся. Исправлен runner: NEW_TASK|MULTIPLE_TASK,
  сохранение sanitized receipt, без обхода Android/MIUI permission. Это не transport
  failure. live8 ordinary HTTPS2×200/TLS PASS; Chrome остаётся не подтверждён.
- live10: lifecycle-only physical partial PASS. TCP568ms, BOOT-1 не вызывался.
  Controlled NETWORK loss → RESTORING → same TCP1390ms; второй loss → FAILED125ms,
  больше candidate retries нет. В CONNECTED/FAILED один VPN, routes0/0 и::/0,
  bypassable=false; negative ordinary literal-IP TCP443 probe: vpn_before/after=true,
  ordinary_tcp_failed=true. Затем fresh CONNECT: forced AWG unavailable → TCP2428ms,
  без BOOT-1; ещё fresh CONNECT с deny_normal: AWG→TCP→restricted6144ms →
  BOOTSTRAP_UNAVAILABLE/FAILED6290ms. Не было cache/Telemost/broker exchange.
  Runner live9/10 ошибочно выводил browser_pass=true для пустого browser list;
  **browser NOT RUN** в lifecycle-only, исправлено через non-empty check.
- live11, final source APK: TCP723ms, alternate forced AWG→TCP2457ms;
  controlled loss → RESTORING → TCP1427ms; второй loss → FAILED120ms;
  all-normal exhaustion → restricted attempt6131ms → FAILED6245ms.
  Ordinary Java HTTPS2×200/TLS verified; **Chrome2 sites FAIL/ERR_CONNECTION_CLOSED**,
  host виден, owner1/full IPv4+IPv6 routes/bypassable=false. Это уже не parser-only
  limitation. Root cause между cached normal JNI/REALITY fixture/Chrome не локализован;
  unchanged manual TCP factory сам по себе не доказывает отсутствие регрессии.
  Read-only gateway sanity: оба контрольных HTTPS HTTP200/TLS verification0.
  Negative ordinary TCP после second loss остаётся blocked с VPN до/после;
  fixture incoming established peak27 — не число доказанных application TCP flows.
  Auto не просил protocol/room URL. Cleanup APK/server PASS.

Acceptance interpretation: primary/alternate selection, one-owner restoration budget,
terminal guard и automatic restricted **attempt** физически подтверждены. Browser
criterion normal не пройден; fresh restricted criteria не запускались. Поэтому
aggregate **FAIL**, а не условный PASS из unit tests или предыдущего EU-6 отчёта.

### Что ещё не доказано этим gate

Fresh automatic restricted success, ordinary Chrome через этот restricted path,
Family DNS из ordinary applications, concurrent restricted TCP, zero direct DNS/TCP
leak counters и restricted UDP/IPv6 containment в **Auto**, physical cancellation
в bootstrap/broker/dedicated, physical process death/restart, примерно10-minute
restricted smoke/queue-memory peaks — **NOT RUN / LIVE BLOCKED**, не PASS.
Отсутствует OAuth для task-owned seed/broker; не извлекался из чужих credentials,
не предлагалось передавать его в чат. Normal DNS/NXDOMAIN probe — не Family DNS proof.
AWG regression: focused existing vectors/JVM + unchanged manual factory; live AWG
success и emulator native suite не повторялись. Live alternate использует forced
AWG unavailable, а не недоступный реальный AWG server.

Cancellation всех phases и restart consistency подтверждены deterministic tests,
не новой full physical cancellation matrix. No retry storm/flapping в ограниченных
lifecycle runs; long smoke **0min / NOT RUN**. Resource peaks/thermal trend restricted
Auto не измерены. DNS/TCP direct-leak=0 не заявляется по одним route/negative probes:
полного capture/counters evidence для этого gate нет.

## Commits и завершение

- `ac2dc65` — core, single-owner adapters, UI, cached BOOT-1 integration,18 JVM cases.
- `c863ead` — isolated runner, Python contracts, diagnostic runbook.
- Отдельный documentation commit содержит финальные STATUS/PLAN/architecture/code map
  и этот ledger, без фиктивного PASS. Source publication guard0 blocked files;
  docs403 files/2427 links/0 errors; git diff whitespace check PASS.
- Final device cleanup: `.orchestrator` отсутствует, active VPN owners0, adb reverse
  empty, Wi-Fi0/cellular1. Amsterdam owned fixture dirs0, listeners18444/18445=0.
  Private profiles/keys удалены вместе с isolated APK/server directories; beta и
  Chrome data не очищались. Исходные ignored restricted JNI/manifest восстановлены
  и directory diff совпал с backup. Temporary task build/JNI/cache/evidence files
  удалены после фиксации ledger; общие pre-existing toolchains/cache не удалялись.
- No push; no production/public release/catalog/version change. FIELD-1 NOT STARTED.

## Версии, rollout и rollback

Public Android beta51/code51, Linux0.2.11, Windows0.2.15 не изменяются. Новый isolated
debug suffix `.orchestrator`, тот же code51/name0.1.18-beta51, не distribution/release.
Restricted native library остаётся opt-in generated debug artifact; production
provisioning BootstrapDirectory/Family activation и release ABI packaging не
объявляются выпущенными. Public artifacts/invitation pages заново не проверялись.

Rollback isolated: stop connection → stop/force-stop/uninstall только `.orchestrator`;
terminate только проверенный owned `/tmp/fc-orchestrator-normal-*` xray PID в Amsterdam,
удалить принадлежащий run directory. Runner имеет600s supervisor и finally cleanup.
Не трогать beta APK, production profiles/DB, gateway services или signed catalogs.

Ограничения сохраняются: deterministic MVP, не ML/scoring; no seamless migration;
no restricted generic UDP; IPv6 restricted fail-closed; один доказанный carrier;
no iOS/production capacity claim; не Краснодар FIELD-1. FIELD-1 только после полного
physical PASS Orchestrator, в этой задаче **не запускать**.
