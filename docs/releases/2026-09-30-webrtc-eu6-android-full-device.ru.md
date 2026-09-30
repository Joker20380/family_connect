# WEBRTC-EU-6 / 5N.6 — Android whole-device restricted path

Дата:30.09.2026. **WEBRTC-EU-6 / 5N.6 = PASS**, isolated physical acceptance.
Starting HEAD `f487a429141da64297038e8a96237205fd1ac060`; перед EU-6 сохранены
существовавшие BOOT-1 acceptance changes отдельным commit `6e0e58f`.
BOOT-1 остаётся PASS в своём принятом scope. Ни Orchestrator, ни public rollout
эта задача не реализует. Public Android beta51/code51 и каталоги не меняются.

## Реализация

- Один authoritative `ConnectionService`, прежние worker/ControlOperations/
  generation/permission/foreground notification/stop. Restricted — explicit
  debug-only backend, не глобальная замена normal AWG/TCP.
- Прежний `TcpVpnService` и pinned Xray/gVisor packet stack. Новый JNI adapter,
  но **не новый VPN owner и не новый userspace TCP/IP stack**.
- Shared `carrier/wholedevice`: TCP streams/half-close/reset/cancellation через
  Mux.OpenTCP; UDP53/TCP53 через Family QueryDNS, без host dial/fallback.
  Android-specific только TUN fd/protect/permission/service lifetime.
- Underlay net adapter защищает HTTPS, WebSocket, ICE/STUN/TURN/media и provider
  DNS **до connect/bind**; pre-TUN physical resolver, proxy/default resolver
  fallback отсутствует. Closing owner блокирует JNI callbacks.
- Cache refresh по normal mTLS → app force-stop/restart → diagnostic negative
  endpoint `https://127.0.0.1:1` → cached BOOT-1 → dedicated READY/descriptor →
  bootstrap close → dedicated Family TLS/binding/Mux → только затем TUN routes.
- IPv4 default captured, DNS10.79.0.1; IPv6 default captured/rejected, generic UDP
  включая QUIC rejected. Нет excluded apps/allowBypass. Private DNS/DoT — обычный
  TCP при попадании в TUN, специальная поддержка не принята.
- Session failure закрывает app flows, но **не TUN**: owner on/health unavailable,
  без direct cellular fallback/reconnect loop. Explicit stop закрывает native
  engine/session перед TUN/service. Process death не превращён в always-on lockdown.
- Bounds: TCP32/DNS16 admissions, Mux32, DNS4096bytes/10s, copy2×16KiB/flow;
  existing packet engine TCP default64/max128KiB, pending64, UDP16;
  bounded numeric evidence1MiB, native events32. Никакого capacity extrapolation.

[Runbook/build/entry points](../../pilot/android-restricted/README.md) ·
[Android code map](../code-map/clients.ru.md) ·
[MPL reuse obligations](../legal/DEPENDENCY_LICENSE_AUDIT.md#eu-6-diagnostic-packet-reuse--2026-09-30).

## Честный журнал попыток

1. Packet fixture сначала отклонял все TCP: Xray Network.String() возвращает
   uppercase. Исправлено преобразование protocol; real gVisor packet regression
   проверяет несколько flows, echo isolation, half-close, DNS, unsupported UDP.
2. Native build потребовал существующий для Pion Android `-checklinkname=0`.
   Chaquopy требовал Python3.10; использована отдельная build directory/toolchain,
   beta/version/signing/catalog не затронуты.
3. Live1: official seed READY, но APK Activity не запускалась. Runner ошибочно
   подставлял applicationId suffix в Java class namespace; Android `am start`
   возвращал Error type3 с exit0. Timeout/cleanup записаны, PASS не заявлен.
4. После паузы live2/live3 остановились до seed READY: использовался уже истёкший
   disposable CRL; старый binary выдаёт только generic stop, точный внутренний
   code не получен. Свежий test-only набор восстановил READY; production identities
   не использованы.
5. Live4 повторил Activity timeout до диагностики причины; исправлены полный
   component name и проверка stdout Error type3, добавлена focused regression.
6. Live5 достиг native startup, refresh отказал до первого protect/socket.
   Обнаружен JNI lifetime defect: borrowed UTF строки использовались goroutine
   после ReleaseStringUTFChars. Исправлено ownership через strings.Clone всех
   трёх входов до async start; regression guard и redacted error evidence добавлены.
7. Live6: cache/restart/real BOOT-1/dedicated/TUN PASS, Android HTTPS TLS200×2 и
   Family DNS/NXDOMAIN PASS. За305.384s достигнут gateway default16,259 OpenErrors;
   Chrome получил ERR_CONNECTION_RESET. Попытка остановлена, **не PASS**.
   Dedicated gateway/client теперь используют один существующий `MuxMaxStreams=32`,
   не новый protocol или performance tuning. Existing32-flow exact/race regression
   и source contract на одинаковый bound PASS. Старый parser также не распознавал
   `CELLULAR|VPN` и не читал XML через `/dev/tty`; исправлен active NetworkAgentInfo
   parser и bounded temporary UI XML с немедленным удалением.
8. Live7 после stream-limit fix: Chrome отображает контрольные страницы, но runner
   первоначально ищет только английский `Example Domain`. Фактический текст —
   испанский `Este dominio está destinado...`; обновлён parser с обязательным
   совпадением контрольного host и запретом ERR_. В **той же** работающей VPN-сессии
   отдельно повторены оба URL:18:38:27/18:38:45 UTC, controlled content=true,
   browser_error=false, active VPN/default IPv4+IPv6/Family DNS/no-bypass/all UIDs=true.
   Исходные результаты parser не переписаны. Это дополнение доказательства, не
   подмена failed native/network результата и не новый APK.
   Smoke541.6s завершён, forced gateway stop оставил VPN active и owner unavailable;
   native active flows/retained bytes/queues обнулились, goroutines снизились до16.
   Однако browser failure check через новое имя успел только ждать DNS за12s,
   явный negative connection не был подтверждён. **Live7 итоговый gate не PASS**:
   добавлена обычная Android TCP connect probe к literal public IPv4 после failure,
   без protect/proxy/bindNetwork; полностью повторяется bounded physical run.
9. Live8: seed READY, bounded UI command отказал до cache preparation. При
   последующей проверке телефон был заблокирован, screen OFF/offReason USER;
   точная исходная команда не была сохранена старым redacted error wrapper.
   Cleanup PASS. Пользователь разблокировал телефон; добавлена preflight проверка
   unlocked/awake до создания seed и allowlisted operation tags ошибок. PIN/lock
   не обходились. Live9 — новый полный запуск, не продолжение неуспешной попытки.

## Принятая physical acceptance — Live9

30.09,18:53–19:04 UTC; Redmi Note9 Pro / Android12 / arm64-v8a,
Wi-Fi OFF, cellular ON, перед запуском другой VPN нет. Debug package `.eu6`,
настоящий Android VPN permission и существующий VpnService, не Core-only harness.
Local sanitized evidence: `/tmp/fc-eu6-live-9/` (`summary.json`, `refresh.jsonl`,
`recover.jsonl`, `gateway.jsonl`, `probes.json`, `failure.jsonl`, `failure.json`,
`process-samples.json`, `metrics.json`, `cleanup-verification.json`). В Git только
отчёт/код; private profile, OAuth, room URL, browsing payload не сохраняются в отчёте.

| Критерий | Принятое доказательство |
| --- | --- |
| Cache/restart | Official API seed READY18:53:46.308 UTC; normal authenticated mTLS cache refresh; force-stop/restart, `cache_survived_restart=true`. |
| Control negative | До bootstrap подтверждён отказ diagnostic endpoint `https://127.0.0.1:1`; recover читает только cache, повторного refresh нет. Это принятый BOOT-1 guard, **не carrier-wide firewall/ISP block**. |
| Bootstrap/Family auth | Real Telemost bootstrap, server Family auth18:54:09.252; существующий Room Broker CREATING/CREATED/GATEWAY_JOINING. |
| READY до descriptor | Fresh dedicated READY18:54:12.435226, CLIENT_ISSUED18:54:12.435401; descriptor через bootstrap, handoff18:54:13.376. Bootstrap control-only, без TCP/DNS Mux. |
| Dedicated → VPN | Bootstrap закрыт до отдельного dedicated join; dedicated Family auth18:54:19.462/ACTIVE18:54:20.337; `dedicated_data_ready` строго до `vpn_packet_ready`. |
| Реальный VPN | Android `VPN CONNECTED`, session Family restricted diagnostic; default IPv4+IPv6 routes, DNS10.79.0.1, UIDs0–99999, bypassable=false. |
| Обычный Chrome | example.com и example.org по3 загрузки,6/6 controlled content=true, VPN=true, browser_error=false; без proxy config. |
| End-site HTTPS | Дополнительные обычные Android HttpsURLConnection: оба сайта HTTP200, стандартная end-site TLS verification, без proxy/protect/bindNetwork. Это не вместо Chrome. |
| Concurrent app TCP |21 успешное TCP-открытие, максимум14 одновременно через TUN/Mux; фоновые и browser flows изолированы. Diagnostic HTTPS probe последовательная, сама не создаёт такой concurrency. |
| Family DNS |98 запросов/98 ответов через existing Mux DNS,0 DNS errors/timeouts; обычное hostname resolution и уникальный NXDOMAIN PASS. |
| Underlay protection |85 successful protect,0 denied; provider DNS16. Оба счётчика постоянны после TUN, несмотря на98 app DNS. Нет carrier recursion; HTTPS/WS/ICE/STUN/TURN/media factories закрыты protected adapter. |
| Unsupported traffic | До injection UDP rejected163, IPv6 rejected25; UDP443 probe отправлена в TUN, IPv6 connect отказал. После failure UDP rejected168. UDP/IPv6 Internet не заявлены. |
| Failure | Owned gateway SIGTERM19:03:31.508; resources closed19:03:31.517. Native state3, owner on/health unavailable, VPN/default routes сохранены; обычный TCP connect1.1.1.1:443 отказал; Chrome тоже показывает ошибку, direct fallback нет. |
| Cleanup | После failure app flows/TCP/Mux streams/retained bytes/carrier queues=0, goroutines16. Explicit owner stop снял VPN, package/cache удалены; remote process/directory удалены,18444 свободен. |

**Leak count в принятом scope:** direct destination DNS=0, direct protected TCP
bypass=0, generic UDP/IPv6 bypass=0. Основание: Android default routes на primary
user UID range без app exclusions/allowBypass, Family DNS counters при неизменном
protected provider DNS, shared backend без destination dial/fallback, packet reject
counters и отрицательный connect после gateway failure при удержании TUN.
Это bounded route/backend/app evidence, **не root cellular pcap, не аудит каждого
байта модема/другого Android user/work profile**. Provider signaling/media/DNS —
разрешённый protected underlay, не destination leak. Private DNS/DoT специально
не проверен; special DoT support не заявляется. Normal API guard не снимался.
Manual room URL, adb reverse и SSH forwarding для control/data: **нет**.
Независимая final cleanup verification: `.eu6` отсутствует, VPN отсутствует,
`adb reverse --list` пуст, Amsterdam task directories0,18444 свободен;
удалены4 локальных disposable private fixture sets и временный controlled screenshot.

### Устойчивость и ресурсы

Light browsing smoke **543.7s (9min03.7s)**, не throughput benchmark. Service не
упал; no growing queues/recursive loop по bounded samples.37 native snapshots,
CPU measured как delta Android process CPU time / elapsed wall time530.484s:
**12.21% одного ядра**, включает Java+JNI/Go этого процесса, не Chrome и не gateway.
Это среднее окна, не instantaneous peak или battery-drain measurement.

| Метрика | Наблюдаемый максимум |
| --- | --- |
| Android app PSS |82195KiB |
| Process RSS / VmHWM |163324 /164816KiB;6 samples18:58:30–18:59:21 UTC; JNI in-process, отдельного native RSS нет |
| OS threads / Go goroutines |35 /157; после failure goroutines16 |
| Go heap |11167488bytes |
| TCP / all TCP+DNS admissions |14 /27; bounds32 /48 |
| Mux active streams / retained HWM |14 /924963bytes |
| Mux receive/send HWM |7000 /16384bytes |
| Carrier send/receive sampled queue |1 /0; bounds256 /16 |
| Reliable retained peak / send depth |25546bytes /8 |
| Mux errors |0 protocol errors,1 OpenError,0 local limit denials; controlled HTTPS6/6 и Java2/2 успешны. Destination этого единичного отказа не записывался. |

Battery temperature29.9→31.2°C, charge100→100%, status FULL/USB-connected.
No crash/runaway memory observed; расход батареи без зарядки не измерен, thermal
stress/capacity/долговременная стабильность этим коротким smoke не доказаны.

## Focused regression и артефакты

- Go race/vet PASS: `carrier/{underlay,wholedevice,bootstrap,roombroker,tcpforward,telemost,familysession}`;
  vet также `cmd/bootstrap-broker`. BOOT-1 unauthorized/replay и Room Broker
  lifecycle/security regression сохранены; existing32-flow exact/race PASS.
- Real gVisor packet fixtures (`pilot/android-restricted/packet`) race/vet PASS:
  concurrent TCP/half-close/isolation, Family DNS, unsupported UDP, cancellation.
  Wholedevice tests:8 flows,32-flow bound, session/parent cancellation, stale use,
  UDP/IPv6 rejection, DNS no fallback; HTTP/WS and socket factory protect negatives.
- Python focused **50 PASS**: Android owner/source contracts, acceptance validator,
  BOOT-1 runner. Source contracts не выдаются за JVM/device execution.
- Android arm64 native/build PASS; `testDebugUnitTest` **172 PASS**,27 suites,
 0 failures/errors/skips; `lintDebug` **0 errors/36 existing warnings**;
  `assembleDebug` PASS. Normal AWG/TCP factory/owner regression не заменена,
  существующий отдельный CI emulator failure не исправлялся и не объявлен PASS;
  normal AWG/TCP повторно физически не прогонялись.
- Docs link/source guards и `git diff --check` PASS. PERF-2 не запускался.

Принятые SHA256:

| Артефакт | SHA256 |
| --- | --- |
| Diagnostic APK | `af8c9fbea0388553bec72e25e4575d0a976b9c8ef9c353846c6d5a953a5facdf` |
| arm64 JNI libfc_restricted.so | `244df28163c5006a78f5a9300a71204f19f36f3da675fccceac8edf5bb8cb4c9` |
| Amsterdam bootstrap-broker | `96bb51d5a0ec6a2254cba56df748a804927c5ac79b5c9363c11de7f80e7872df` |

Logical commits: `6e0e58f` — сохранение исходных BOOT-1 acceptance changes;
`ec3ce42` — shared/Android integration и focused fixes/tests;
`da8c7b2` — physical runner, fail-closed probe и acceptance regressions;
следующий docs commit фиксирует этот отчёт. Ни один не push в этой задаче.
**NEXT = MVP Connectivity Orchestrator; NOT STARTED. STOP после EU-6.**

## Ограничения, rollout и rollback

- Нет automatic Connectivity Orchestrator; следующий gate только после PASS EU-6.
- Нет generic UDP; IPv6 fail-closed, не IPv6 Internet support.
- Нет seamless migration активных flows; нет always-on process-death guarantee.
- Нет fresh-install-in-already-restricted guarantee сверх BOOT-1 cached-state scope.
- Нет второго carrier, iOS, production rollout или production capacity claim.
- Diagnostic package `com.familyconnect.app.eu6`, code51/version beta51,
  отдельная debug signature; не public artifact и не обновление beta package.
- Rollback: explicit owner stop, force-stop/uninstall только `.eu6`, terminate
  только принадлежащий run процесс `/tmp/fc-eu6-*` на Amsterdam, удалить disposable
  private fixtures. Public APK/catalog/prod data не трогать.
- Как и BOOT-1, runner не предоставляет API удаления provider conference metadata;
  cleanup закрывает участников/сессии/сокеты/gateway processes, не обещает удаление
  уже созданных записей конференций у Telemost.
- Push: no. Production changed: no. STOP после этого gate.
