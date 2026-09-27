# 27.09.2026 — WEBRTC-EU-1: recovery и Telemost binary PoC

## Recovery

Исходное состояние: `/home/joker/PycharmProjects/family_connect`, `main`,
`HEAD == origin/main == 8e3685854f3beea07aea573fa775e97a6220a70d`.
Выполнены все запрошенные `pwd`, status, diff/stat/cached, log/reflog15,
branch-vv и rev-parse; tracked/staged diff пуст, только untracked `carrier/`.
Никакие reset/restore/checkout/clean/stash/rebase/pull не выполнялись.
Merge/rebase/cherry-pick state, swap/tmp файлы и оставшийся carrier не найдены;
`git fsck --connectivity-only --no-dangling` PASS. Unrelated работа не изменена.

Сохранились 10 файлов; все добавлены исходными байтами отдельным коммитом
`ee3a830cdef7776f565645ad22baa1199c2662c4`
(`wip(webrtc): recover interrupted Telemost carrier implementation`).
Дополнительная копия: `/tmp/fc-eu1-recovery/deepseek-carrier-original.tar.gz`;
она временная, долговременный recovery anchor — Git commit, не `/tmp`.
Перед сохранением проверены contents/секретные паттерны: cookies, room URL,
bearer/private keys не найдены. Ничего из первоначальных файлов не выброшено.

| Найдено у DeepSeek | Состояние после выключения |
| --- | --- |
| `carrier/go.mod` | 1,046 bytes: сохранились module path + `go 1.24`, остальные985 bytes — NUL. SHA256 `ad92b6adfea747c330885e38c4249ee93da213575592706312690efd2fa1080c` |
| `carrier/go.sum` | Нулевой файл; original dependency pins/checksums восстановить из него нельзя |
| `carrier/frame/frame.go`, `frame_test.go` | Private framed IPC codec и8 тестов; body limit64KiB не вмещал payload64KiB |
| `carrier/telemost/auth.go` | HTTP connection GET, headers, response parser; waiting-room poll отсутствовал |
| `carrier/telemost/session.go` | New/Connect/Send/OnMessage/Close, stats, bounded send queue; publisher/subscriber Pion PC и native DC scaffolding |
| `carrier/telemost/signaling.go` | WebSocket hello/capabilities/serverHello, subscriber offer/answer, publisher offer/answer, slots, ICE/trickle, writer loop |
| `carrier/telemost/vp8.go` | VP8 keepalive/interframe constants и wrapping/decoding |
| `carrier/telemost/rtp.go` | RTP reorder и VP8 assembly scaffolding |
| `carrier/telemost/msg.go` | sender/message/sequence/count fragmentation, но без total length/global incomplete bound и completed duplicate rejection |
| CLI / test harness | Не найдены; кроме IPC codec тестов ничего не было |

Импорты `pion/webrtc/v4`, `gorilla/websocket`, interceptor/RTP уже были в Go-коде.
Их версии **не** удалось прочитать из повреждённого manifest; текущие pins выбраны
заново для существующей реализации, не приписываются исходному агенту.
Восемь `.go` файлов не содержали NUL и не были оборваны посреди синтаксиса.
Помимо manifest повреждения найден неиспользуемый `media` import, а также
незавершённые lifecycle/validation части (ошибочное ready condition, закрытие
ready channel при signaling failure, конкурирующее закрытие channel, скрытые
ошибки SDP/media). Это незавершённый полезный checkpoint, не повод переписывать
архитектуру с нуля.

## Implementation

Сохранены модуль и границы DeepSeek: один `telemost.Session`, два Pion
PeerConnections, тот же Telemost HTTP/WebSocket adapter и VP8/RTP path.
API теперь `New(ctx)` → `Connect(ctx)` → `SendContext/Recv(ctx)` → `Close()`;
callback заменён bounded receive queue, чтобы пользовательский callback не мог
заблокировать RTP reader/teardown. Private frame codec сохранён, отдельный IPC
command server пока не реализован. CLI — только synthetic echo/probe harness.

Изменения по reviewable checkpoints:

- `08f5360`: module repair, pinned graph/notices, IPC/fragments bounds.
- `cb0819d`: HTTP/WS sanitation, lifecycle, cancellation, pending ICE и tests.
- `d72819d`: VP8 prefix checks, RTP loss/reorder/timestamp bounds и tests.
- `6dd5eeb`: CLI metrics + настоящий локальный двухпроцессный Pion VP8 smoke.
- `7aed1a8`: закрытие собственных HTTP idle connections и дополнительные
  CRC/recent-ID/timestamp regression tests; итоговый runtime source checkpoint.

Архитектура/протокол и команды подробно в [runbook](../../carrier/README.md).
Dependencies: Pion `v4.2.15`, Gorilla `v1.5.3`, interceptor `v0.1.45`, RTP
`v1.10.2`, logging `v0.2.4`; Go `1.27.1 linux/amd64`, minimum module Go1.24.
23 действительно linked modules: [versions/licenses/SHA256](../../carrier/DEPENDENCIES.md).
`go.sum` получен через Go module checksum verification, `go mod verify` PASS.
Go toolchain установлен только в `/tmp`, официальный archive SHA256
`63d339f0da5ab53635a56f2490a7984dfe12dfcff22ad749f63edaf590168445` проверен.
No headless fork/LiveKit/KCP/whole reference project. Реальные overlap constants/
protocol maps отражены в [legal audit](../legal/DEPENDENCY_LICENSE_AUDIT.md),
оба reference notices сохранены, root LICENSE не менялся.

Framing: payload0..65,536 bytes, 8KiB fragment, header6×u32be — sender/message ID,
sequence, count, total length, CRC32 whole message. CRC — не криптография.
8 fragments/message,16 incomplete messages,4,096 recent IDs,10s expiry;
duplicate/conflicting fragments и corruption не доставляются, expiry работает
без нового входящего трафика. IPC body65,542/control16KiB, unknown opcode/version,
truncation/oversize/short write rejected. Outbound queue256 fragments, inbound16
messages; receive overflow fail-closed. Нет application retransmission/TCP layer.

Signaling: bounded HTTP/WS, TLS verification и allowlisted WSS hostname/scheme,
без redirects/error bodies/credentials/SDP в логах. Subscriber pcSeq берётся из
offer; pending trickle ICE до SDP ограничен128/PC. Ошибки SDP, WS и media terminal,
не превращаются в CONNECTED. Идемпотентный Close, отмена и ожидание workers;
reconnect отсутствует (=0). Поведение настоящего waiting room ещё не реализовано
и требует подтверждённой схемы ответа, не выдуманного polling protocol.

Основной `--mode vp8`: publish `video/VP8`, periodic keyframes и arbitrary fragment
bytes за interframe prefix. Incoming DC **отвергается** в VP8 mode (отдельный
regression test), поэтому DC не может создать ложный VP8 PASS.
`--mode datachannel` оставлен диагностическим; native SFU DC/TO_RTP mapping не
подтверждены. Prefix не доказывает полноценную VP8 decoder conformance или
прохождение SFU inspection. Ни одного реального user/VPN payload не передано.

## Tests

### Unit / local preliminary

- Build: PASS; `go test -race -count=3 -timeout 120s ./...`: PASS.
- `go vet ./...`, `go mod verify`, `git diff --check`: PASS.
- HTTP success/error/timeout, invalid room/WSS, no body/URL leakage; successful
  hello/SDP serialization и pcSeq; malformed JSON/SDP, signaling close, end-state
  parser, pending ICE bound, ready/close concurrency, saturated queues: PASS.
- Framing: all sizes, CRC/length/count checks, duplicates, timeout, bounds,
  malformed/oversized/truncated local frames и short writes: PASS.
- RTP: loss, wraparound/reorder, gap/timestamp bounds, wrong VP8 prefix: PASS.
- `FuzzDecode`: 5s,391,968 executions; `FuzzReassembler`: 5s,60,876 executions;
  crash/panic не обнаружены. Это ограниченный fuzz run, не доказательство всех случаев.
- `TestLocalTwoProcessVP8`: **два процесса**, parent-owned pipes только для SDP,
  настоящий локальный Pion RTP/DTLS VP8 media. 1/32/256B,1/4/16/64KiB,
  затем100×1KiB и100×16KiB = **207 byte-for-byte checks**, PASS в каждом из3 запусков.
  Процессы завершились, включая отмену активного echo. Это не Telemost и не EU.
- Sandbox сначала запретил socket() у httptest; повтор выполнен разрешённо вне
  sandbox. Это не было ошибкой провайдера. Регрессию ErrClosed/context.Canceled,
  найденную race-suite после изменения cancellation, исправили и suite повторили.

### Real Telemost — recovery checkpoint (до предоставления room)

27.09,09:13:14–09:13:15 UTC: единственный negative join к настоящему HTTPS API
с заведомо несуществующим synthetic room ID. Получен **HTTP404**, exit1,
payload TX/RX0, PCs closed. Ответ API/URL/секреты не напечатаны. Этот negative test
запущен на рабочем checkpoint `ee3a830 + dirty recovery changes`; он не является
положительным session/ICE/media результатом и не закрывает gate.

Валидная disposable room не передана; `FC_TELEMOST_ROOM` при восстановлении
отсутствовал. Browser cookies/аккаунты не читались; комнаты не создавались.
По существующему SSH безопасно прочитаны только OS/arch и наличие проекта на
разрешённом Amsterdam endpoint. Carrier на VPS не установлен/не запускался.
Host `186.246.51.201` и соседние сервисы не затрагивались.

## Metrics — recovery checkpoint

| Поле | Фактическое значение / отсутствие измерения |
| --- | --- |
| Итоговый runtime source | `7aed1a8df9aa7af49e7e82d78fd07fa83367fd7e`; recovery `ee3a830cdef7776f565645ad22baa1199c2662c4` |
| Endpoint A | Ubuntu26.04 LTS, Linux7.0.0-31-generic, x86_64; developer machine |
| Endpoint B | Ubuntu26.04 LTS, Linux7.0.0-30-generic, x86_64; authorized Amsterdam186.246.45.246; read-only SSH проверен |
| Go / Pion | Go1.27.1 / Pion4.2.15; бинарник собран только на A, runtime на B не проверен |
| Carrier mode | VP8 primary; DC diagnostic NOT RUN |
| Room creation method | План: вручную в официальном UI; фактически валидная room отсутствует |
| Setup / RTT / useful throughput | Для real VP8 не измерены |
| Payload sizes / equality | Local207 checks PASS; real sizes/equality NOT RUN |
| TX/RX / disconnect / reconnect | Real positive session не было; negative API process:0/0 bytes,0/0; это не stability metric |
| CPU / memory | Только negative API process:0.011058s user +0.007372s system, peak RSS16,196KiB, heap2,004,144B; media нагрузка НЕ измерена |
| 30s / 5min sustained | Real NOT RUN; harness поддерживает последовательный запуск после baseline |
| Remote leaves / signaling loss / active shutdown | Local closure/cancellation PASS; real NOT RUN |

Временный binary checkpoint7aed1a8: SHA256
`f420534fb46f9700ac6badfdcb4f03ed9b2b81acf274e149a8596c48dbffc2b6`;
файл в `/tmp/fc-eu1-recovery/telemost-binary`, не release. `vcs.revision` точно
`7aed1a8df9aa7af49e7e82d78fd07fa83367fd7e`, `vcs.modified=true`: на момент сборки
оставались **только документационные** изменения этого отчёта/STATUS/PLAN/legal;
runtime source и tests уже полностью закоммичены. Перед real acceptance собрать
бинарник из окончательного clean checkout и заново записать его metadata/checksum.
Metrics harness не пишет payload/hash/URL/token; счётчики TX — принятые application
bytes, не packet-capture wire bytes. Throughput — сумма обеих полезных сторон
round trip. Gate не переключается автоматически по JSON `suite_complete`.

## Result — recovery checkpoint (superseded следующей live-сессией)

```text
WEBRTC-EU-1 = BLOCKED
WEBRTC-EU-1 / 5N.1 = OPEN
NEXT = завершить real Linux A ↔ Telemost VP8 ↔ Linux B acceptance
```

**Точный внешний blocker:** нет предоставленной disposable Telemost room URL /
разрешённой live conference для двух endpoints. Доступ к Linux B есть, но не
заменяет room. Нельзя объявить gate PASS по local PeerConnection или HTTP404.

После предоставления room: проверить real join/admission (при waiting room сначала
подтвердить и реализовать bounded poll), hello/server ICE, slots/pub-sub SDP,
VP8 SFU forwarding. Затем все sizes → batches →30s →5min, оба конца с matching
source/binary и JSONL, live remote exit/signaling close/SIGTERM. API/media
совместимость не гарантируется reference-кодом или локальным тестом; могут
потребоваться адресные исправления adapter. Не переходить к5N.2/Android.

## Live continuation — настоящая Telemost room, 27.09

Room предоставлена оператором **только через `FC_TELEMOST_ROOM`**; URL/identifier
не сохранялись в Git, fixtures, скриптах, аргументах процессов или отчёте. Способ
создания комнаты извне не наблюдался; cookies/аккаунт/owner API не использованы.
Первый немодифицированный join (`75841f0`, clean)09:32:26–09:33:46 UTC: оба PC
connected, setup1993ms, завершение по80s deadline, exit0. **waiting_room_required=no**:
connection API сразу вернул пригодные данные, admission/pending не встретились.
Waiting-room poll намеренно НЕ реализован; другие комнаты могут требовать его.

### Endpoints / artifact

- A: текущая developer Linux machine, Ubuntu26.04 LTS,
  Linux7.0.0-31-generic, amd64, обычный пользователь.
- B: разрешённый Amsterdam186.246.45.246, Ubuntu26.04 LTS,
  Linux7.0.0-30-generic, amd64; существующий SSH/operator path. Root использован
  только для создания/уборки собственного временного каталога; carrier выполняется
  как **nobody, uid65534**, не service. Production routing/firewall/VPN не менялись.
- Передавались только executable + `carrier/licenses/`; room передавалась SSH stdin
  в память процесса и environment, не в файл или command line. Product secrets,
  profiles, DB, signing keys не читались/не копировались. Public proxy/listener нет.
- Acceptance runtime: **`a13068e74f8a1ceef4e5d9d659622eb70710aac0`**, clean build,
  Go1.27.1/Pion4.2.15; оба endpoint сообщают `vcs.modified=false` и одинаковый SHA.
  Binary SHA256: `758bffe3c9f62192dd9887a2858af048a0a3386fa2b36e74ff388308a5d25061`.
  Это временный PoC artifact, не установленный/подписанный/public product release.

### Найденная граница сбоя и исправление

1. `4c1407613d084b7614db3cf500d3e14119e22531`: bounded sanitized evidence;
   09:37:00–09:38:04 UTC — все7 размеров VP8 PASS, затем batch прервался после7
   успешных1KiB echo. Старый harness не различал timeout/closed: точный тип этой
   первой ошибки **не установлен**, не приписывается ICE или corruption.
2. Повтор09:40:28–09:42:13 UTC: опять7/7 размеров, затем39 успешных1KiB;
   B сообщил signaling closed. Диагностический keyframe-prefix trial
   09:45:39–09:47:13 UTC сохранил проблему: после33 успешных1KiB **оба endpoint
   получили `WS_FAIL / close_code_4008`**. Прямой server reason не логировался;
   значение4008 само по себе не объявляется подтверждённым provider reason enum.
   Keyframe-prefix не помог и **полностью отменён**, в принятом коде остаётся
   исходный interframe envelope. DC не запускался и не подставлялся вместо VP8.
3. `55f2561`: добавлен application `ping` каждые5s и ACK для incoming `pong`,
   кроме уже существующего WebSocket control ping. Loop завершается при cancellation;
   нет reconnect, retry или бесконечного ожидания. Предварительный heartbeat run
   прошёл100×1KiB без разрыва, затем намеренно остановлен SIGTERM ради clean rerun.
   Live наблюдаются generic ACK: `ApplicationPongs=0`, нельзя заявлять полученный
   application pong. Устранение наблюдаемого разрыва проверяется полным rerun, а
   не только существованием heartbeat-кода. Counters отделяют pings/ACKs/pongs.
4. `a13068e`: opt-in live signaling-close test и runbook; общий deadline25min
   вместо10min для наблюдаемого RTT2–4s. **Per-echo timeout всё ещё10s**, никаких
   скрытых повторов, снижения byte equality или смены carrier mode нет.

### Real signaling / ICE / media

На A и B зафиксированы `ROOM_RESOLVED`, `SIGNALING_CONNECTED`, `SERVER_HELLO`,
`ICE_CONFIGURED`, `SUBSCRIBER_CONNECTED`, `PUBLISHER_CONNECTED`, `VP8_MEDIA_ACTIVE`.
Setup acceptance A1751ms/B1826ms. PC states: connecting → connected.
Local candidate types: host/srflx/relay, protocol UDP; **выбранные пары обоих PC
на обоих endpoint: host → host, UDP, `turn_used=false` по Pion**. Наличие relay
candidate не означает использование TURN. Это не доказательство отсутствия NAT,
VPN или иных промежуточных hop; точный внешний network path не заявляется.
VP8 OnTrack отдельно от CRC/framing/byte-equality: track activity не выдаётся за
успешный binary echo. Peer A и B не обмениваются локальным SDP или прямым IPC:
HTTP connection → provider WebSocket/hello → ICE/SFU → VP8 RTP/DTLS.

### Acceptance payload matrix (carrier_mode=vp8)

| Payload | sent | received | byte_equal | RTT, ms |
| --- | ---: | ---: | --- | ---: |
| 1B | 1 | 1 | true | 3776.282 |
| 32B | 1 | 1 | true | 4012.535 |
| 256B | 1 | 1 | true | 3986.051 |
| 1KiB | 1 | 1 | true | 3999.261 |
| 4KiB | 1 | 1 | true | 4058.627 |
| 16KiB | 1 | 1 | true | 4124.831 |
| 64KiB | 1 | 1 | true | 3993.250 |

| Phase | Count | Actual duration, s | Mean / max RTT, ms | Useful roundtrip Mbit/s | Equality |
| --- | ---: | ---: | --- | ---: | --- |
| 100×1KiB | 100 | 401.139 | 4011.386 / 5316.705 | 0.004084 | PASS |
| 100×16KiB | 100 | 398.853 | 3988.463 / 4432.499 | 0.065724 | PASS |
| 30s sustained,16KiB | 8 | 32.010 | 4001.212 / 4016.141 | 0.065515 | PASS |
| 5min sustained,16KiB | 76 | 303.990 | 3999.807 / 4094.470 | 0.065538 | PASS |

Итог09:56:49.749–10:16:18.448 UTC: **291 настоящий byte-for-byte round trip**,
A TX=RX3,204,385B,483 binary fragments decoded. Main suite exit0;
disconnect/reconnect/sequence-gap counters0, corruption/echo timeout не было,
evidence overflow0. Время A1168.699s включает setup, settle и все фазы; это не
20min отдельного sustained. Продолжительности30s/5min превышены на время
завершения последнего echo, без сокращения обязательных интервалов.
Throughput считает **обе полезные стороны** (`2 × bytes / elapsed`), без RTP,
DTLS/ICE/keepalive overhead. One-direction useful rate — половина этого значения.
В5min:0.065538Mbit/s roundtrip, около0.032769Mbit/s в каждом направлении.
Observed RTT — application echo RTT, не чистая задержка сети. Производительность
низкая; production/VPN throughput или restricted-mobile acceptance не заявляются.

### Resource / shutdown / fault evidence

- A main: CPU14.167106s user +8.122725s system; peak RSS29,808KiB,
  heap9,914,152B; final goroutines3, оба PC closed.
- B echo09:56:47.755–10:16:42.889 UTC, включая последующие fault prerequisites:
 294 messages, TX=RX3,205,411B; CPU16.359885s user +10.107996s system,
 peak RSS28,800KiB, heap7,586,048B; final goroutines4, оба PC closed.
 Дополнительные3 сообщения =1KiB перед WS-close +1B перед SIGTERM +1B перед
 remote exit; B summary не выдаётся за снимок строго в конце main suite.
- Application pings A233/B238; generic ACKs A283/B301; application pongs0.
  Ни одной самопроизвольной WS4008/ICE/session ошибки в полном acceptance run.
- **Live signaling closure PASS**: отдельная реальная session +1KiB exact VP8 echo,
  затем закрыт только собственный WS. Recv terminal, Send rejected, Close завершён
  за1ms; opt-in Go test exit0. Это инъекция отказа уже установленного signaling,
  не утверждение об отключении provider инфраструктуры.
- **SIGTERM during traffic PASS**,10:16:34 UTC: после1B equality отменён активный
 32B probe, `CANCELED`, процесс вышел за0.003214s. Exit1 намеренный: прерванный
 probe не должен выдавать `suite_complete`.
- **Remote exit PASS**,10:16:42–10:16:52 UTC: B получил SIGTERM и вышел0;
  A после подтверждённого1B echo ожидал32B и завершился с `ECHO_TIMEOUT`, exit1,
  за9.784969s от начала инъекции (10s request deadline). SFU connection могла
  оставаться connected; это не маскируется как надёжный membership/liveness event.
- Принудительный SIGKILL не понадобился. Все созданные remote tmp directories
  удалены; дополнительный read-only SSH check: `TEMP_DIRS=0`, `TEST_PROCESSES=0`.
  Локальные live/keyframe/heartbeat test executables и transfer archive также
  удалены; сохранены sanitized evidence/logs и исходный recovery checkpoint.
  Ни systemd, ни production VPN routing/services не устанавливались/не менялись.

Постоянное [sanitized evidence](2026-09-27-webrtc-eu1-live.sanitized.json) содержит
build revisions/dirty flags, phases, counters, timestamps, candidate **types**,
close4008 и fault outcomes. Перед сохранением проверено отсутствие room/identifier,
URL-encoded room, HTTP/WSS URLs; SDP, credentials и payload bytes не собирались.
Полные sanitized JSONL временно находятся в `/tmp/fc-eu1-live/`; room в них нет.

### Regression at live checkpoint

`go test -race -count=3 -timeout 120s ./...`, `go vet ./...`, `go mod verify`,
build и `git diff --check`: PASS. Local two-process VP8 снова207 checks ×3;
теперь проверяются и media counters. WS fixture проверяет application ping,
pong ACK, cancellation/teardown; evidence fixtures — bound128, defensive copies,
no addresses/tokens/close reason, timeout/JSON/close-code classification.
FuzzDecode5s:1,076,354 executions; FuzzReassembler5s:3,443; PASS без crash/panic.
Live fault checks выполнены после successful suite, не заменяют его.

## Final result

```text
WEBRTC-EU-1 / 5N.1 = PASS
NEXT = WEBRTC-EU-2 / 5N.2
5N.2 = NOT STARTED
```

Доказан **Linux A → настоящий Telemost signaling/ICE/SFU → Amsterdam Linux B →
VP8 binary echo → Telemost → A**, а не local Pion/DC substitute. Blocker отсутствия
room снят; встреченный signaling close4008 устранён в проверенном пути application
heartbeat. Без raw server reason не утверждается формальная семантика close code.
Исходный framing/VP8 media envelope не переписан, waiting-room scope не расширен.

Осталось вне этой приёмки: waiting-room admission для других rooms, причины высокого
RTT/оптимизация useful rate, автоматический reconnect, длительные/mobile/RF tests.
Android, TUN, Family auth, TCP streams и WB fallback **не начинались**. Следующий
gate записан, но запуск5N.2 в этой сессии не выполняется.

## Поставка / откат

Нет нового product version, release tag, signatures, catalog или публичной
дистрибуции. Android beta51/code51, Linux0.2.11, Windows0.2.15 и invitation-page
versions оставлены без изменений; текущие public artifacts в этой задаче повторно
не проверялись и новая поставка не заявляется. Production defaults/routing/AWG/
TCP/XHTTP/Home Gateway/messenger не менялись. Push не выполнялся.

При входе перепроверен ранее упомянутый workflow36261639780: Linux и Windows
jobs success; Android runtime и Windows compatibility failure, release job
skipped. Это не “весь run green”; независимые ошибки прошлой задачи не исправлялись.
У исходного HEAD8e36858 связанных PR workflow runs не найдено. Никакой из этих
результатов не считается deployment нового carrier.

При входе в live continuation read-only GitHub API: latest release `v0.2.11`,
published2026-09-26T14:25:28Z, prerelease=true; latest `phase0` для8e36858 —
completed/failure. Это прежний CI, не deployment PoC; unrelated CI не исправлялся.

Runbook: [carrier/README.md](../../carrier/README.md). Временный binary + notices
действительно запускались на EU и затем удалены, без install/systemd/VPN изменений.
Rollback уже выполнен: temporary processes остановлены, remote artifacts удалены.
Для повторения собрать указанный source checkpoint и снова использовать только
environment room, private tmp directory и runbook. Закрытие самой комнаты/отзыв
room остаётся у оператора; owner API не вызывался. Локальная environment пользователя
не изменялась. Production rollback не требуется; released/installed/invitation
versions и каталоги остались прежними. Исходный DeepSeek recovery commit сохранён,
reset/rebase/push не выполнялись.
