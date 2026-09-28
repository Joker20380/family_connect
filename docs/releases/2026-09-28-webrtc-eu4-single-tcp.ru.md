# WEBRTC-EU-4 / 5N.4 — один TCP stream поверх Family Session

Статус: **WEBRTC-EU-4 / 5N.4 = PASS**,28.09. Авторизован пользователем27–28.09.
Starting HEAD `5ff09e2`; core `2b977da`, initial harness/APK `2e81984`,
telemetry/fault harness `554acbb`, RST fix `fa3c027`, observer `2c5c63e`,
HTTPS close-order test fix/clean CLI+APK `63f6bde`. Чужой VPN audit в STATUS/PLAN и два файла
`2026-09-27-vpn-*` сохранены отдельно, не входят в commits5N.4.

Production, публичные installers/catalogs/invitation versions не меняются:
Android beta51/code51, Linux0.2.11, Windows0.2.15. Только disposable diagnostic
APK `com.familyconnect.telemosttest`, `5N.4-test-only`/code3; без публикации.

Final CLI/APK построены из clean `63f6bde337fb3cdfcd514cf02f37ca26000cef32`,
этот APK установлен только для acceptance и удалён при cleanup. Intermediate
`554acbb` build не устанавливался. SHA256 final artifacts:
- APK: `40022c00fcc0848a559ba3021f0a487eb2a8457dca5fdb2929c24d022ae606f7`.
- Linux CLI: `eab2bfeea111f5452ceb749aa3830e342aed7510870659d468917e216a363a33`.
- Android arm64 native: `253e70647e73f8330887650633255bd2388fa078e84c1f0f6a00e884b6ef097e`.

[Sanitized evidence](2026-09-28-webrtc-eu4-single-tcp-evidence.json) сохраняет24
attempts, включая13 финальных TCP scenarios, failures,60 samples на сторону long
run, независимые resource snapshots и regression outcomes. Raw private logs и
disposable credentials не публикуются. Docs commit — commit, содержащий этот отчёт.

## Architecture

`Application TCP → Family TCP forwarding → Family TLS1.3 → ReliableStream
→ VP8/RTP → Telemost real SFU → Amsterdam → Internet TCP`.

Core API `tcpforward.OpenTCP(ctx, session, request)` предоставляет Read/Write,
CloseWrite/Close/Reset. Gateway `tcpforward.Serve` создаёт настоящий TCP socket.
Нижние reliable/VP8 defaults не менялись. Android использует тот же Go CLI в
isolated foreground test Service, не UI/browser/proxy и не VpnService.

## Protocol

Версия1, opcode, big-endian stream_id=1 и длина; 10-byte header. OPEN JSON ≤512B,
DATA1–16384B; OPEN_OK, OPEN_ERROR, DATA, FIN, RESET, CLOSE. CLOSE после обоих FIN
подтверждает получение EOF и закрытие gateway socket. IDs зарезервированы,
но только один одноразовый stream на admitted session; нет mux/reuse/scheduler.
Произвольная сегментация допустима. TCP read/write и Family DATA не взаимно-однозначны.
Подробности/границы: [wire/API](../../carrier/tcpforward/README.md).

## Security

Handler принимает concrete admitted Family Session правильной роли; второй claim
отклоняется. Existing device identity, family entitlement, CRL/revocation, replay
protection и TLS не заменены новой auth-системой. Production authority не развёрнут.
Hostname resolve на gateway; все ответы проверяются, dialing по validated literal
без второго DNS lookup. Port1–65535, host≤253 ASCII, default connect10s/max30s,
OPEN exchange≤40s. Forbidden loopback/private/link-local/metadata/CGNAT/reserved/
IPv6 tunnel/special destinations. Не production ACL и не unauthenticated relay.

Explicit test override разрешает только127.0.0.1:exact-port. Controlled fixtures
не proxy, ограничены одним потоком,96MiB и900s; public fixture дополнительно
проверяет source IP Amsterdam. Public HTTPS использует default policy без override.

## Deterministic tests

Real loopback:1B/32B/1KiB/16KiB/64KiB/3MiB, произвольные writes и777B fixture
reads, binary exact, duplex, local FIN с response-after-EOF, remote FIN с
write-after-EOF, immediate close, RST, cancel/session close, actual refused.
Injected DNS/refused/timeout/unreachable; DNS pinning и mixed-address rejection;
malformed frames/request, forbidden addresses, partial/zero TCP writes, two-way
backpressure, premature CLOSE, rejected second stream и unauthenticated API.
Real Family TLS+ReliableStream fault test переносит1MiB byte-for-byte, при drop и
duplicate carrier blocks; duplicate retransmissions не попадают в target TCP.

Первый race-run обнаружил гонку только в test-fixture bytes.Buffer и transport EOF,
ошибочно воспринимавшийся io.ReadAll как clean EOF. Fixture синхронизирован;
transport EOF теперь terminal ErrReset, только FIN даёт io.EOF. Повтор race×3 PASS.

## Physical live path

Redmi Note9 Pro / Android12 / arm64, cellular, test APK → Family TLS1.3 → reliable
VP8/RTP → real Telemost SFU → disposable nobody gateway на186.246.45.246.
TUN отсутствует; DataChannel substitution отсутствует. Radio baseline wifi1/data1.
URL комнаты получен от оператора и передаётся только stdin/env; не в argv/Git/report.
Наличие SFU signaling DataChannel в Pion counters не означает перенос app DATA по DC.

Initial local fixture:65536B в каждом направлении, exact SHA256
`3dcea1e1a0f4b3488ecb5b90375d9d9534cc24997424331bb0059aef8ba78844`, clean FIN/CLOSE.
Gateway actual outbound socket к loopback — deterministic live fixture, **не Internet proof**.

## HTTPS proof

`example.com:443`: physical OPEN, separate end-site TLS certificate/hostname
verification PASS, HTTP200,559 response bytes. Family TLS и end-site TLS — разные
уровни. End-site TLS завершается на Android и сайте, не на Amsterdam.
Final63f6bde recheck PASS; `speed.cloudflare.com:443 /__down?bytes=10485760`:
end-site TLS verified, HTTP200, exactly10,485,760B, clean FIN/CLOSE PASS.
Это реальный public Internet download, не loopback/SSH bypass.

## Transfer proof

Accepted clean63f6bde:

| Scenario | Application bytes | Duration | Useful throughput |
| --- | --- | --- | --- |
| Public Cloudflare HTTPS | 10,485,760 download | 53.433180970s OPEN→clean close | ~1.570Mbit/s inclusive of setup/close |
| Controlled Amsterdam duplex | 10,485,760 each direction | 58.997831853s transfer | 2.843700416Mbit/s aggregate;1.421850208 one-way |
| Sustained controlled duplex | 22,511,616 each direction | **300.820842906s** transfer | **1.197343416Mbit/s aggregate**,0.598671708 one-way |
| Fresh session after network loss | 65,536 each direction | 1.781236874s transfer | 0.588678463Mbit/s aggregate |

Controlled fixture hash совпадает с Android upload/download; arbitrary777B fixture
reads против16KiB Family DATA, независимое чтение/запись одновременно. Не stop-and-wait.
SHA256 controlled10MiB:
`d8438d6a17b94669aebb5946ec4e31768a562cef21b9c555415d316be07bc512`.
Sustained:
`b69fe01bfd2d9d729c9c5f3337739a3cab8b2b89cb4d3215803dc011918feaaf`.
Public download:
`6464e8e3cec2549d8f95050208627a8de55e4a4189e2da36896ba4c44ce298a5`.
Для Cloudflare заранее известен размер, не hash; hash — полученные проверенным HTTPS
байты, а не независимый origin-file checksum. Transfer не ищет новый carrier ceiling.
Initial2e81984 controlled10MiB/55.952612895s также exact, но final numbers выше.

## Half-close / close

Local deterministic и physical echo local FIN → remaining response → remote FIN →
CLOSE/ack PASS. Physical remote-half-close PASS: Android после EOF отправил9B
`after FIN`, fixture подтвердил точные bytes/hash. Immediate clean-close PASS.
Close до обоих FIN — явная отмена; transport death не маскируется как clean EOF.
Gateway closes socket and joins reverse worker on cancellation/failure.

## Fault handling

Первый public controlled fixture на185.251.89.19:ephemeral-port получил structured
OPEN_ERROR timeout за3s connect budget. Сохранён как failed transfer attempt;
firewall/production services не менялись; причина внешней недоступности порта не
доказана. Это не byte corruption и не auth failure. Controlled data fixtures
перенесены на явно разрешённый Amsterdam loopback; Internet proof проверяется HTTPS.
Physical refused и controlled connect timeout PASS: structured connection_refused /
timeout, последний с3s connect deadline и controlled full listen backlog. Никаких
firewall rules. RST during transfer: fixture получил777B до RST, Android deterministic
ErrReset; gateway socket/task cleanup подтверждён. Explicit cancellation, gateway
exit и отключение cellular дают ожидаемый terminal stream failure; свежая отдельная
session после восстановления cellular снова переносит65,536B exact.
Полностью потерянный Family Session не сохраняет TCP socket и не мигрирует stream.
В трёх intentionally interrupted transfers byte_equal=false/неполные счётчики
ожидаемы и сохранены; это **не** accepted complete transfers и не migration proof.

Два дополнительных failed attempts сохранены:
- Immediate target RST на2e81984: reverse worker отменял Family endpoint до доставки
  queued OPEN_OK/RESET. `fa3c027` закрывает socket сразу, но даёт peer наблюдать RESET
  до10s; authenticated regression и race×10 PASS. Physical reset-during-transfer PASS.
- Первый Cloudflare download наfa3c027: TLS/HTTP200 и10MiB уже получены, но harness
  отправлял поздний TLS close-notify после полного close сайта; gateway честно вернул
  shutdown ENOTCONN и gate FAIL. `63f6bde` завершает чтение close сайта и отправляет
  только TCP FIN, без позднего TLS DATA. Core ENOTCONN не подавляется; added end-site
  TLS closure regression/race×3 и повторный physical download PASS.
Ранние complete payloads не используются для переименования failed attempts в PASS.

## Reliability / resources

TCP DATA staging bound gateway49172B (16KiB read buffer +2 frames with headers),
никаких data queues поверх existing ReliableStream. Metrics staging high-water
отделены от TLS/reliable/OS buffers и caller-owned memory. Malformed Family message
может выделить bounded64KiB до TCP rejection. Reliable defaults16KiB/sender8/receiver16.
Final sustained:60 TCP snapshots per side, queues sampled every5s. Carrier queue
sampled max Android4 / Amsterdam7 (capacity256); native buffer high-water
Android32011B / gateway42956B <49172B. Reliable send high-water8/8, reorder5/3;
max reliable retained76656/80718B; final retained/depths0. Native sampling cannot
claim an exact between-sample carrier queue maximum; bounded capacity is a code limit.
No sustained queue/buffer growth observed. RTT per TCP byte stream не измерялся;
OPEN round-trip1146.432ms, gateway connect0.258ms — не TCP packet RTT.

RTP gaps **0**, reliable gaps/recoveries **0/0** в accepted sustained run.
Android retransmissions0; gateway lifetime3 /132B — повторы последнего44B CLOSE ACK
на teardown, не DATA interval. First/last active snapshots оба показывают0 retries.
Accepted exact transfers: TLS bad-MAC/plaintext corruption/duplicate delivery/missing0.
Carrier/reliable reordering counters не являются delivered application reorder.
Session teardown Resets1/side и terminal=cancelled нормальны после clean CLOSE.
Отдельный physical native ReliableStream regression намеренно теряет sequence2:
1/1 gap recovered за1264.113ms,8/8 exact echoes, TLS survived; retries client2 /
gateway1, carrier duplicate1 на gateway не доставлен приложению повторно.
Это controlled reliable-block loss, не natural RTP gap и не sustained TCP interval.

Sustained lifecycle на обеих сторонах: OPEN1/OK1/ERROR0, local FIN1/remote FIN1,
EOF1, clean CLOSE, TCP-layer RESET0. Gateway DATA sent5254/received1374,
TCP reads5255/writes1374, observed partial writes0 (partial writes отдельно
deterministic tested). Target sockets1 during flow,0 after close.

| Sustained resource metric | Android native | Amsterdam native |
| --- | --- | --- |
| Go heap sampled peak | 10,477,888B | 11,646,640B |
| RSS sampled peak | 15,036,416B | 31,010,816B |
| Rusage maxRSS | 112,128KiB | 30,376KiB |
| CPU sampled mean / peak, % of one core | 5.791 /6.189 | 4.184 /4.723 |
| Goroutine sampled peak | 167 | 226 |
| OS threads observed max | 15 | 7 |
| Total sockets observed max, including carrier | 49 | 73 |

28 independent thread/socket snapshots; gateway forwarded target socket count≤1,
final0. Counts include many unchanged Pion/ICE sockets, not73 forwarded streams.
Android UI/service PSS sampled peak191,908KiB; Java used peak6,286,936B; sampled CPU
mean9.940%, peak12.394%. PSS rises during initial rendering, then ~181–187MiB plateau;
this debug JSON/UI observer is not a production memory/performance claim. Android
child rusage HWM can include pre-exec inherited memory and is not its sampled RSS.
Reliable delivered TLS-byte goodput from first/last samples:0.609195Mbit/s Android
receive /0.604915 Amsterdam receive; includes framing/crypto, not useful app goodput.
USB charging/battery100% is not an energy-efficiency measurement.

## Regression

- Final clean63f6bde: Go race×3 all6 packages, ProductStore fixture integration,
  existing reliable/fault/auth/admission/revocation/replay tests, vet и modules PASS.
  Five fuzz targets по5s PASS: TCP frame123341, reliable frame381543/engine377323,
  binary frame374136, VP8 reassembler53127 executions. RST-specific race×10 PASS.
- Python exact control/identity/messenger lockfiles:984 PASS,3 optional/environment
  skips,2 existing deprecation warnings. Первый image без curl дал1 environment
  failure; image затем дополнен curl/LXMF/git/KeePassXC/QR. Final skips: optional APK
  signing1 и installer TUN device2. TUN не создаётся ради обхода skip.
- Final Android63f6bde: assemble/6 JVM tests/lint PASS (0 errors,6 existing warnings).
  ARM64 native all6 suites PASS; PASS counts including nested/subtests:
  CLI19,telemost28,frame11,reliable29,family21,TCP39. Four optional Telemost live
  tests skipped in generic run, затем physical live checks ниже PASS; native
  ProductStore host fixture skip covered by Go host integration.
- Final physical canonical suite: **518/518 exact echoes**,7 sizes,100×1KiB,
  100×16KiB,29 echoes/30.532828634s,282 echoes/300.777411084s. No byte mismatch.
  Wrong-family/revoked/unknown: gateway rejected, no application echo. Client-side
  TLS establishment alone не считается admission; проверен server verdict.
- Physical native WS-close,PeerConnection-close,handshake replay rejection,
  reliable injected-gap recovery PASS. TCP cancellation/remote-exit/network-loss
  и fresh-session recovery проверены отдельно в13 final TCP scenarios.

Transient install step: final debug signer отличался от предыдущего одноразового
container signer, поэтому Android отклонил update-in-place. Удалён и заново установлен
**только** diagnostic package; production beta/signing/identity не затронуты.

## Rollout / rollback / cleanup

Только temp nobody processes, app-private credentials и test APK; services/routes/
firewall/production DB не менялись. Rollback: cancel test, reap exact owned PIDs,
удалить test APK/disposable credentials/artifacts и восстановить radios1/1.
Final cleanup PASS: diagnostic APK удалён;28 recorded Android native PIDs и33
gateway PIDs отсутствуют, нет owned процессов или temporary carrier/fixture
каталогов на Amsterdam и185.251.89.19; app-private/native test directories удалены.
Все13 final TCP cases имеют target sockets0/retained staging0 при завершении.
Wi-Fi1/mobile-data1 восстановлены, TUN отсутствует (Android shell netlink запрещён,
проверено через `/sys/class/net`). Four owned worktrees, disposable credentials,
issuer DB, private raw logs/APK/native builds и test image tag удалены; pre-existing
shared SDK/Go/Gradle caches сохранены без disposable credentials. Container-owned
Gradle output удалён через тот же Docker runtime после обычного Permission denied;
это cleanup environment issue, не live TCP failure. Чужие VPN audit hunks STATUS/
PLAN и два untracked VPN report files сохранены и исключены из commits5N.4.
Push не выполнялся. Rollout/rollback production не требуется; published artifacts
не менялись, новый public release не заявляется.

## Limitations

Only one logical TCP stream; no production mux, dedicated DNS transport, UDP,
QUIC, TUN, VpnService routing, Orchestrator, FEC/codec redesign или multi-user test.
No seamless TCP migration after full Family Session loss. Not production readiness.
Нет незавершённых5N.4 acceptance checks;3 Python skips перечислены выше, не скрыты.
5N.5 не начат. **STOP после отчёта**; не запускать следующий stage автоматически.
