# WEBRTC-EU-5 / 5N.5 — multiplexed TCP + DNS

## Result

**WEBRTC-EU-5 /5N.5 = PASS**, в границах Core-level TCP+DNS ниже.
Предыдущий5N.4 PASS не заменяет новое mux acceptance. Production не меняется.
[Sanitized numeric evidence, per-stream results and bounded samples](2026-09-28-webrtc-eu5-mux-dns-evidence.json).

Физически доказано: **одна authenticated Family TLS + ReliableStream + Telemost
session одновременно несёт независимые Internet TCP streams и Family DNS с
bounded buffers, fair scheduling, exact delivery и без cross-stream corruption**.

## Starting state / provenance

Старт `812f4cb5913cad412d29f2f4f605c55327ce7d25`. Чужие VPN hunks в STATUS/PLAN
и untracked `2026-09-27-vpn-health.ru.md`, `2026-09-27-vpn-load.json` сохранены,
не включаются в5N.5 commits. Baseline Go race×3/6 packages PASS. Первый sandbox
запуск не мог bind loopback; повтор вне sandbox с разрешением. Последний
просмотренный external CI phase0 `36268143806`, `8e368585`, failure26.09 — не CI
этой unpushed работы.

| Слой | Commit |
|---|---|
| Mux/core/state/credit/scheduler + wire DNS + deterministic tests | `a22742a` |
| Gateway hostname hardening + DNS containment proof | `0014fd2` |
| Android/CLI/live/native DNS guard/harness | `03582fb` |
| NXDOMAIN fixture/provenance, первый accepted native/APK | `4687c3d0370e9e123f123109a72cbe54a0d3e409` |
| Bounded upload instrumentation, physical observer | `bb867a0` |
| Final strict evidence validator/tests, replayed on accepted logs | `083763d` |
| **Final tested core/native/APK**, shutdown correction + DNS N+1/parser/state tests | `c26c2b741a2ab71ac4df8ac3c831bb66b83134c6` |

Чистый temporary worktreec26c2b7, live `vcs.modified=false`, revision/SHA256
совпали на endpoints. Diagnostic **code4 /5N.5-test-only**, только test install.

| Artifact | SHA256 |
|---|---|
| Linux CLI | `b2d19c1f614e5394d377f4a83274543352c3bcd8a16fd6b767453123d334b88d` |
| Android native arm64 | `a86dc6cd5cd8731baa357de166c5c3fd5b47b1e9edcd10c3ae96965f52fcde0a` |
| Diagnostic APK | `73380c120c9699326b40fb8f052eaa9ba1a2ed2eacef70e25ef61f36b624be7a` |

## Architecture

```text
Before: one TCP → v1 Family TCP → Family TLS1.3 → ReliableStream → VP8/RTP
        → real Telemost SFU → Amsterdam → one outbound TCP
After:  N TCP streams + DNS wire queries → one v2 Family Mux
        → one admitted Family TLS1.3 → one unchanged ReliableStream
        → one existing VP8/RTP/Telemost path → Amsterdam
        → N policy-validated TCP sockets + configured DNS resolver
```

Прежняя Telemost publisher/subscriber topology сохранена; не новая связь/TLS
на каждый TCP. Native DataChannel не заменяет media carrier. Security boundary —
Family auth/TLS, не Telemost. Signaling/VP8/Pion/ARQ/TLS/admission wire не менялись.
API `NewMux/OpenTCP/QueryDNS`, stream `Read/Write/CloseWrite/Close/Reset`.

## Mux protocol / states

[Полная спецификация](../../carrier/tcpforward/MUX.md). Opt-in version2,
header10B: version/type/uint32 stream_id/uint32 exact length. OPEN(1), OPEN_OK(2),
OPEN_ERROR(3), DATA(4), FIN(5), RESET(6), CLOSE(7), WINDOW_UPDATE(8), DNS_QUERY(9),
DNS_RESPONSE(10), DNS_ERROR(11), DNS_CANCEL(12). Старый single-TCP API/v1 сохранён,
silent downgrade нет. OPEN hostname/IP+port representation прежняя; v2 для mux,
не для hostname support.

TCP IDs odd1..2147483647;0 DNS/control, even reserved/rejected. Monotonic, no
wrap/reuse; exhaustion требует новой сессии. Gateway high-water ID вместо
unbounded tombstones. Default **16**, configurable **1..32**. Worker slot до
socket cleanup. N+1→stream_limit, existing unaffected; stale ID не создаёт map.

opening→open→local-half-closed/remote-half-closed→both-half-closed→closed;
OPEN_ERROR→failed; cancel/RESET→reset. Duplicate active OPEN, DATA до OPEN_OK/
после FIN, duplicate received FIN, invalid credit/premature CLOSE reset только
stream. Terminal frames не оживляют stream. Local CloseWrite idempotent;
clean CLOSE ACK после drain/half-close, timeout10s. Wire corruption length/type/
impossible ID fail-closes session; обычные state errors изолированы.

## Flow control / bounds

На direction/stream receive ring/credit **64KiB**, DATA≤**16KiB**, один pending
DATA, queue≤3 frames. Read возвращает/coalesces WINDOW_UPDATE, DATA тратит credit;
overflow/>64KiB rejected. Reader не ждёт slow socket/consumer. TCP staging ещё
2×16KiB/stream, partial write полностью обрабатывается.

Global:96 control frames,16 DNS calls/workers,32 stream workers maximum.
Консервативный payload budget при32:32×80KiB mux +32×32KiB TCP staging +96×4100B
control +16×2×4096B DNS +3×16394B scratch = **4,243,870B**, плюс fixed metadata и
bounded DNS worker message buffers. Не heap/RSS cap: kernel sockets/Go stacks/TLS
отдельно. Default16 уменьшает линейные stream части вдвое. Нет роста с transferred
bytes. `RetainedBytes` — mux rings/queued payload/DNS callers, не весь staging.
Reliable retained bound393216B неизменён; carrier queue capacity256.
Per-stream payload+gateway staging≤112KiB. Отдельно bounded DNS worker: encoded
request≤4098B/response≤4096B, system resolver file read≤65536B, parsed≤128 RRs на
message. Эти transient parsing/config allocations не выдаются за mux payload HWM.

| Mixed HWM / sampled metric | Android | Amsterdam |
|---|---:|---:|
| Per-stream send, B |8192|16384|
| Per-stream receive, B |16384|8192|
| Mux retained, B |401664|475136|
| Scheduler queue, frames |5|5|
| Flow-control stalls |755|1749|
| Reliable retained, B |66020|66276|
| Carrier send queue sampled max |2|4|
| Final active streams/sockets/retained |0/0/0|0/0/0|

Fixed bounds дополнительно forced slow-consumer/global-blocked tests; queues не
растут с18.75MB transfer. DNS message4096B,16 outstanding, query+response131072B
(без уже указанного worker/control overhead).

## Scheduler / fairness

Один writer, round-robin ready stream heads; control/DNS priority максимум8
consecutive перед ready DATA. Backpressured skipped; FIN не обгоняет свой DATA.
In-flight lower-layer send не preempt. Tests проверяют RR order, priority quota,
full64KiB slow consumer и interactive response<1s, bulk+small/DNS progress.

Live915 small responses, все4 streams прогрессируют рядом с bulk/171 DNS.
RTT avg/p50/p95/p99/max **313.904/245.220/789.055/1508.584/1880.618ms**,
intentional1s pause между requests. No starvation observed.
SchedulerWaitMaxMS1891.284/1840.459 включает возраст lifecycle head относительно
queued DATA: **не** maximum starvation interval/SLA. Отдельного wall starvation
counter нет; bounded RR proof детерминированный. Lower ordered transport HOL остаётся.

## DNS / audit / negative condition

[Полный audit и manual verification](../testing/webrtc-dns-containment.ru.md):
Android/Linux/Windows/shared core/proxy/TUN/health/provisioning/bootstrap.
Finding: **5N.4 OpenTCP уже отправлял hostname без client resolve**. Нет фиктивного
«переноса DNS»: добавлены hardening/negative proof и wire RPC для5N.5/future adapter.

OpenTCP(hostname)→encrypted OPEN→gateway canonicalize→DNS→validate ALL IPs→dial
validated literal. Original hostname остаётся client TLS SNI/certificate check;
gateway не MITM. IP OPEN не требует DNS. Wire DNS stream0 + Family uint32 ID,
отдельно от DNS16-bit ID, match ID+question. Standard wire12..4096B, one IN question,
opcode0,≤128 RRs,16 calls,5s timeout/cancel/cleanup. A/AAAA/CNAME/NXDOMAIN/TTL.
Upstream — gateway-configured literal IP:53 или first bounded system nameserver,
TCP DNS length prefix; client не выбирает resolver, нет UDP relay/fallback.

Application cache не добавлен: LookupNetIP не возвращает TTL; fixed fake TTL
некорректен. System resolver может иметь cache; hit/miss/expiry **N/A**, не PASS.
Wire RR TTL сохраняется. Carrier API/signaling/STUN/TURN/SFU bootstrap DNS —
категория A, прежний mechanism; не tunnel внутри ещё не установленного tunnel.

Physical public-4: getaddrinfo guard после carrier+admission. Обязательный negative
lookup получает EAI_AGAIN **до сети**, counter подтверждён/обнулён. Затем4 HTTPS
и Family DNS работают при **post_probe_calls0**. Gateway hostname requests4,
DNS success4, IPv4 selected4, failures0. Mixed guard тоже0. Реальная process-scoped
недоступность libc DNS, не просто HTTP200; OS Private DNS settings не подменялись.
No client public resolver/DoH. Нет whole-phone/browser/WebView interception:
Family пока Core path. Non-root pcap не снимался; rooted/emulator procedure есть,
но capture PASS не заявлен.

## Security

Только admitted Family ownership. Canonical ASCII/A-label lower-case/root-dot,
≤253B/label63; U-label явно rejected как прежде, IDNA conversion caller без DNS.
Malformed URLs/zones/ports rejected. ALL≤32 resolved candidates проверяются до
первого dial; mixed public/private denied целиком. Loopback/unspecified/multicast/
link-local/RFC1918/CGNAT/ULA/metadata/reserved и gateway interface addresses denied.
Test-only exact loopback:port override. NAT public alias вне interfaces требует
deployment policy. Rebinding: dial только checked literal, второго lookup нет.
IPv4/IPv6, resolver order, per-address≤3s в overall default10/max30s, IPv6 failure
допускает IPv4. DNS≤3s/context cancellation. Compatible dns_failure/timeout/
policy_rejected/cancelled/connection_refused без infrastructure text. Metrics без
hostname labels/history; diagnostic targets только explicit test.

## Deterministic test matrix

| Требование | Tests / PASS |
|---|---|
| 1/4/8/16/32 streams, duplex, segmentation, stream identity | MuxConcurrentExactSegmentation |
| OPEN/OPEN_ERROR, capN+1, independent RESET | MuxLimitAndIndependentReset |
| refuse/timeout/cancel не убивают sibling | MuxConnectFailuresDoNotKillSibling |
| FIN/оба half-close/drain/close | MuxHalfCloseAndOpenErrors + legacy TCP |
| collision/stale/unknown/exhausted ID | MuxCollisionStaleAndExhaustion |
| slow consumer64KiB/backpressure + interactive<1s | MuxSlowConsumerAndInteractive |
| global backpressure + shutdown | MuxGlobalBlockedWriterShutdown |
| RR/control quota/bulk+small | MuxSchedulerRoundRobinAndPriority |
| bulk+DNS/concurrent/matching/duplicate/cancel/shutdown | MuxDNSConcurrentBulkAndMatching, AnswersDuplicateAndMismatch, CancellationAndShutdown |
| DNS A/AAAA/CNAME/TTL/NXDOMAIN/timeout/malformed/oversize/outstanding | DNS fixture/parser/state tests |
| DNS client/gateway N+1,16 pending callers release | MuxDNSOutstandingLimitAndRelease (stress×20) |
| malformed length/ID/type/DATA/DNS/credit; post-FIN/terminal isolation | MuxMalformedWireBounds/MuxTerminalTransitionsIsolated |
| DATA-before-open/after-FIN, repeated FIN/OPEN/terminal, huge credit | MuxMalformedStateIsolation + fuzz |
| partial TCP write | MuxPartialSocketWriter + legacy writer |
| many-stream cancel/open-close-reset concurrency | MuxSessionCancellationManyStreams/OpenCloseCancellationStress |
| admitted TLS/reliable loss/reorder/duplicate, exact delivery | MuxAuthenticatedLossReorderDuplicate |
| pinned literal/IPv6/IPv4 fallback/SSRF all candidates | DestinationCanonicalPinnedDualStack/ResolvedSSRFAllCandidates |
| DNS errors/timeout/cancel/IDNA/bounds/concurrent resolution | Destination tests |
| poisoned client resolver + admitted HTTPS200/cert validation | HostnameHTTPSWithBrokenClientDNS |
| actual libc denial | NativeDNSGuard on Linux and Android |
| legacy single TCP/auth/revoked/wrong/unknown/replay/TLS/lifecycle | Existing Go suites |

Go1.27.1 full race×3/vet/modules PASS. Eight fuzz targets ×5s: tcpforward
FuzzFrame/FuzzMuxFrame/FuzzMuxCreditAndState/FuzzMuxDNS; reliablestream
FuzzFrame/FuzzEngine; frame FuzzDecode; telemost FuzzReassembler. No crash/race;
finite smoke не proof всех возможных inputs. Linux CLI build PASS. Windows/amd64
shared tcpforward test executable cross-build PASS, **не native Windows UI/runtime**,
UI не менялся. Android CGO/assembleDebug/6 JVM/lint PASS;6 native package suites
на Redmi PASS. Optional native ProductStore fixture covered by host fixture test;
live optional tests выполняются отдельно с room. Python final **1004 passed,
3 skipped,2 existing warnings**: optional Android public signing fixture1 и no-TUN
installer preflight2; не skip security/TCP/DNS tests. Final observer subset38 PASS.
После c26c2b7 full Go race×3/vet/modules/eight fuzz и Android build/JVM/lint/native
повторены. ProductStore fixture дополнительно race×3 с правильным
FC_FAMILY_TEST_FIXTURES (не skipped из-за отсутствующей переменной).

Physical canonical regression: **507 exact echoes**,7 sizes1..65536B,
100×1KiB/100×16KiB,30.553s и301.020s sustained, admitted suite_complete PASS.
Unknown/wrong-family/revoked — gateway explicit admission rejection; live old
transcript replay rejected на fresh server. Native WS/peer close PASS. Controlled
seq2 gap1/recovered1, retransmissions2,8 exact TLS echoes, TLS survives.
Physical legacy single TCP: HTTPS/local exact64KiB/remote-half-close/remote-reset/
refused/timeout/cancel/remote-exit/network-loss PASS; fresh-session64KiB transfer
после re-enable cellular PASS. Activity-close/process-death PASS. Эти legacy/
auth/canonical physical regressions использовали4687c3d; lower layers идентичны
финальномуc26c2b7. После точечной mux-only shutdown правки повторены full host/
native suites и обе главные physical mux acceptance, не заявляется повтор всех
старых physical сценариев на новом executable.

## Physical path / public Internet

Redmi Note9 Pro Android12/arm64 **cellular**, Wi-Fi off → shared Go Core/Mux →
Family TLS1.3 → ReliableStream → VP8/RTP → real Telemost SFU → Amsterdam
186.246.45.246 → outbound TCP/configured resolver. Одна family_auth на endpoint
каждой попытки. Public/mixed — две отдельные сессии, каждая multiplexed.

Public-4: **4 simultaneous OPEN**, IDs1/3/5/7,2×example.com:443 и
2×speed.cloudflare.com:443. Все end-site TLS1.3 verified/HTTP200, bodies559/559/
1024/2048B. No gateway MITM. Family A/AAAA example.com + random `.invalid.`
NXDOMAIN:3/3, rcodes0/0/3. DNS avg482.793/max926.608ms; n3 слишком мало для tail.

## Mixed workload

Mixed-2 **304.137659s**, bulk300.859731s:1 bulk +4 interactive +DNS triples≈5s.
На10s independent reset/cancel и denied metadata OPEN_ERROR;5 основных работают.
Total8 OPEN,7 OPEN_OK,1 OPEN_ERROR,2 RESET; MaxActiveStreams7 включает временно
перекрытые terminal/opening states, не7 sustained bulk connections.

Exact bulk **18,751,488B each direction**, endpoint SHA256:
`13c095ef5dd8824cce89d9c8e8682d1d8447ee206b9e4ce1c36098fa026afa33`.
Bulk aggregate **0.997222Mbit/s**, one-way0.498611 при cap0.5; не ceiling test.
TotalTCP18,868,864B each direction including small/isolation, ID/offset-specific
bytes. Overall mux probe309.007686s включая OPEN/setup, total TCP aggregate
**0.977004Mbit/s** на этом интервале (не только bulk).915 exact interactive
responses,4 clean FIN/close, bulk оба FIN.
DNS171/171:57 A/57 AAAA/57 NXDOMAIN; avg/p50/p95/p99/max
**294.902/236.611/581.711/1247.084/1310.580ms**. Quantiles sorted index
floor((n−1)×percent/100), diagnostic, не SLA.

## Reliability / lifecycle

Final mixed RTP/Reliable gaps Android/Amsterdam **0/0**, unrecovered0;
retransmissions **2/1**, bytes8284/2290; public retransmissions1/0.
Pre-correction mixed-1 имел real RTP gap1/0, recovered1/0, max1278.086ms;
этот natural-loss proof сохранён отдельно, не приписан финальному run.
Final mixed Reliable filtered duplicates1/2 и reorder202/150 —
не app delivery. Application corruption/duplicate/missing/reorder/cross-stream
**0** на accepted exact payloads; TLS bad-MAC0, unexpected Family closure0.
Final reliable `cancelled`/Reset — intentional teardown после proof. Public
gateway B_EXIT1 после owned cleanup, не in-workload failure.

Live independent reset/cancel/policy-error/FIN/close PASS; refuse/timeout/malformed
state native deterministic. Session shutdown closes sockets/fails DNS waiters/
joins workers, final streams/sockets/retained0. Дополнительный live controlled
gap recovered с8 exact encrypted echoes; replay/WS/PC closure отдельно. Seamless
migration нет, новая сессия должна открыть новые TCP.

## Resources / methodology

Mixed sampled peaks, не inherited pre-exec Android ru_maxrss:

| Metric | Android native PID6264 | Amsterdam native PID415501 |
|---|---:|---:|
| /proc/self/statm RSS, B |16564224|31928320|
| Go HeapAlloc, B |10510912|11590448|
| Go HeapSys, B |19496960|19693568|
| Goroutines |188|239|
| /proc/self/task threads |14|7|
| /proc/self/fd socket descriptors |49|78|
| runtime.NumCPU |8|1|
| Wall interval, s |299.999706|309.999925|
| Δprocess CPU user+system, s |48.329428|13.164463|
| CPU%, one-core normalized |16.109825|4.246602|

Source `getrusage(RUSAGE_SELF)` **все threads точного PID**, не host/cgroup/fixture/
другие VPN. Formula100×Δ(user_s+system_s)/Δwall_s, без деления на CPU count.
Android11:26:53.896473147Z→11:31:53.896179074Z; gateway11:26:49.603700211Z→
11:31:59.603625823Z. Poll10s, между samples peaks могут быть выше.
Android parent app PID6238: Debug.MemoryInfo PSS182943KiB, Java-used5364416B;
Process.getElapsedCpuTime Δ33617ms / elapsedRealtime311162ms ×100 =10.803697%
одного core, **не native child**. PSS/RSS нельзя складывать без shared-page учёта.
SocketFD count включает carrier, не только outbound TCP. Production VPN workloads
не тронуты. **4.25% не cost per user, не capacity extrapolation/incremental audit.**

## Failed attempts / reproducibility

- Public-1/03582fb:4 HTTPS/guard/A/AAAA PASS, **overall FAIL**: random example.com
  subdomain NOERROR/NODATA вместо NXDOMAIN. Fixture изменён на reserved `.invalid.`,
  не resolver/protocol. Старый failed attempt не переименован PASS.
- Public-2/4687c3d **preflight FAIL**: upload exceeded45s до session; temp удалён.
  Причина slowdown неизвестна. bb867a0 ограничивает upload180s и измеряет size/time,
  не меняет runtime timeouts/queues/retries. Public-3 upload9170106B/16.006s,
  mixed9.988s. Нет retry-until-green loop.
- Первый Python Docker tmpfs noexec дал environment failures; tmpfs:exec исправил
  среду. QR decoder установлен для full suite. Sandbox bind и intermediate unused
  import compile failure исправлены, не подавлены.
- Дополнительный deterministic DNS N+1/shutdown test выявил поздний DNS_CANCEL:
  caller мог добавить4B control frame уже после очистки mux. Это bounded retention,
  не corruption/SSRF, но нарушало cleanup contract. `c26c2b7` запрещает enqueue
  control после cancellation; lower layers не изменены. Новый test воспроизвёл
  failure×3 до fix, затем stress/race×20 и full race×3 PASS. Добавлены explicit
  malformed wire/oversized DNS/credit и terminal FIN/DATA isolation cases. Прежние
  public-3/mixed-1 PASS на4687c3d сохранены, но final build acceptance повторяется
  отдельно (public-4/mixed-2), не подмена provenance и не retry loop.
  Оба final runs PASS; uploads9170031B/17.499s и23.616s соответственно.

## Rollout / cleanup / remaining

Public/installed product/invitation versions не менялись: Android beta51/code51,
Linux0.2.11, Windows0.2.15; catalogs неизменны. No production deployment/firewall
changes/rollback. Diagnostic rollback выполнен: APK удалён;42 записанных Android
и52 gateway PID/parent IDs отсутствуют, owned process names0, remote test dirs0.
Native test directory удалён, `/sys/class/net` без tun/wg/awg; ip netlink non-root
Android не разрешил, это не выдаётся за успешный packet capture. Wi-Fi1/data1
восстановлены. Private credentials/raw logs/binaries/Go build cache, temporary
worktree и два собственных Docker test image удалены; shared SDK/cache сохранены.
Sanitized evidence остаётся в Git. Foreign VPN hunks/reports сохранены побайтно,
не входят в5N.5 commits. Documentation — отдельный commit с этим report.
Незавершённых checks данного gate нет. Manual rooted pcap/full-device adapter и
native Windows UI validation вне изменённого Core scope, не скрытые PASS.
Push performed: **no**.

## Limitations / STOP

No TUN/VpnService integration, generic UDP/QUIC/ICMP, Room Broker, reverse TCP,
seamless migration. **Global ReliableStream HOL остаётся**: fair application
scheduling не independent loss domains. Single-device cellular, не multi-operator
whitelist certification, multi-user capacity или production-readiness claim.
Product browser/OS DNS требует будущего adapter, подтверждён текущий Core path.
После завершения STOP: не начинать Room Broker/5N.6/TUN/Orchestrator/rollout.
