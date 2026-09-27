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

### Real Telemost

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

## Metrics

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

## Result

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

Runbook: [carrier/README.md](../../carrier/README.md). Для будущего теста —
только временный binary + notices на EU, без systemd/install/VPN изменений.
Rollback: SIGTERM временных процессов, закрыть disposable room, убрать только
свои временные файлы при необходимости, unset room env. В текущей задаче
production rollback не требуется. Исходная работа DeepSeek всегда доступна в
отдельном recovery commit, без reset текущего worktree.
