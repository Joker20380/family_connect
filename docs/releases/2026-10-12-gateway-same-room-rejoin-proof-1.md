# GATEWAY-SAME-ROOM-REJOIN-PROOF-1 — PARTIAL

**LOCAL_CLIENT_STACK_CAPABILITY = PROVEN_UNDER_EXPLICIT_ROOM_PERSISTENCE_MODEL.**
**SAME_ROOM_REJOIN_CAPABILITY = UNKNOWN.**

На локальном SFU настоящий production client прошёл новый WSS/SDP/ICE/Pion/RTP join
в прежнюю room после двух WS1011. Прежние bytes D обеспечили новый authenticated
bootstrap и dedicated READY. Другой dedicated Family/Mux/TCP stream не прервался.
Это больше, чем metadata GET, но **не доказательство поведения реального provider**.

**FIRST_BLOCKER = REAL_PROVIDER_ROOM_RETENTION_AND_FULL_REJOIN_AFTER_1011_NOT_EVIDENCED.**
Fixture сама сохраняет room после1011 и разрешает новый полный join. В запечатанных
материалах нет независимого provider contract/evidence, подтверждающего это для
реального Telemost. Невозможность rejoin также не доказана. Production supervisor
patch/implementation plan не создавались; deployment/owner/live действия отсутствуют.

## Исходная база

Проверены все4054 SHA256 entries предыдущего capsule, включая exact source,
classifier, natural application/systemd receipts, chronology, directory identities,
предыдущую matrix и dedicated-isolation fixture. При закрытии исходные inputs и
все2004 baseline files проверены повторно. Исходные evidence не переписаны.

- Baseline: `a4087e000fdbe674b72ede3a6c8822445c87c654` + classifier diff
  `7e7d408670a6ac6afa18e856beb8dcc0ca26a3b6f074e205d4dd25e62d78967b`.
- Сохранённая deployed binary identity:
  `21f0a0fdc27b50c00ea922f0b716516e2422aedf1b3797369718f7d00070509a`.
  Это provenance, не свежий runtime snapshot: SSH/journal/ADB не запускались.
- Experimental tree identity:
  `617c7a81f37d16ed26c664dfa15d36bafbccf7ab974951badc281a9e56bfbddc`.
- Experimental diff:
  `c52d5052fd92b99bd8999b20f2e24c8bd470338183ef5eb882a99050874cb564`.
- Pinned Go1.26.1/linux-amd64; Gorilla WebSocket1.5.3; Pion WebRTC4.2.15.
  Module/sum/toolchain hashes и command/source input receipts сохранены.

Historical classification неизменна: **WS1011 boundary PROVEN; provider internal
reason UNKNOWN**. Owner full CONNECT/Telemost at that fatal0; relation EXCLUDED
только для этого fatal. Более ранние UNKNOWN exits не переатрибутированы.

Capsule: `state-client-build/field65-export16/gateway-same-room-rejoin-proof-1/`.
Содержит exact `baseline/`, isolated `source/`, `experiment.diff`, `scope.txt`,
`DESIGN.md`, `REPRODUCE.md`, `RESULT.json`, `manifest.json`, receipts, SHA256SUMS.
Пустые production-behaviour/production-observability diffs означают отсутствие
production patch, а не отсутствие test-only изменений.

## Топология и реальная production boundary

`source/carrier/internal/rejoinfixture/provider.go` реализует локальные TLS metadata
и WSS, реальные message names/offer-answer/trickle ICE и две Pion PCs на participant.
Room содержит до4 media slots; RTP/VP8 направляется только другим peers той же room.
Join credential случайная, новая на participant, ограничена room lifetime и проверена
при hello вместе с room/participant. Raw credential/SDP/payload в receipts не пишутся.

Использованы реальные:

1. `telemost.New/Session.Connect` → `Auth.FetchConnection` → Gorilla WSS →
   subscriber offer/answer → publisher offer/answer → ICE → PC connected.
2. `Session.writerLoop/readVP8Track` и production framing/reassembly, не packet-pair.
3. Первый `SeedManager.Run/TelemostSeed/ServeCarrier`, production `Publish` создаёт D.
4. `ParseDirectory` и `Recover`, читающие исходный committed cache file D →
   admission → Family TLS/Reliable → broker challenge/create/claim/handoff.
5. `TelemostGateway.Start/Run` → отдельная real-Pion room → Family auth/BindClient →
   Mux → однократно открытый TCP echo socket.

Только три network substitutions в **isolated experimental source**:
metadata base локальный; внешний STUN отключён для host-ICE; WSS fixture hostname
направлен на локальный TLS socket с pinned disposable CA и hostname validation.
Production URL/schema validation, signaling/SDP/ICE logic, Connect/readiness, carrier,
Family authentication, Reliable, broker, Mux и renewal decisions не заменены.
READY вручную не выставляется. Нет TLS interception, DNS rewrite или live provider.

Tagged adapters требуют `sameroomfixture`. Это **не deployable gateway source**:
обычная production сборка не предлагается, публичного endpoint/control нет.
Synthetic issuer дополнен второй valid identity в существующем test entitlement;
owner identity/cache/enrollment не читались. Service alias остаётся существующим
разрешённым `chat-api.family-connect.invalid`, направленным на disposable echo,
без вызовов реального chat API или чтения сообщений.

## Полный положительный эпизод

- До failure: seed signaling/subscriber/publisher connected; через его RTP прошёл
  authenticated bootstrap первого synthetic client; получен descriptor и отдельный
  dedicated Family/Mux READY. Открыт один TCP socket, начата серия numbered frames.
- Provider отправил настоящий Gorilla close frame1011 только seed. Сохранено
  `SEED_READ / SIGNAL_READ / WS_CLOSE / 1011 / ACTIVE / local_close=false`.
  Первый production SeedManager вернул ошибку — exit policy не исправлялась.
- Experimental driver **не вызывает broker.Close** при этой ошибке. Он закрывает
  старый carrier, ждёт его retirement и вызывает новый `TelemostSeed` с прежним Room
  и исходным expiry. Новый WebSocket, новые publisher/subscriber PCs и ICE — реальные.
- Повторяется второй1011; ещё один fresh full join возвращает seed media readiness.
  Conference ID hash совпадает. Seed CreateRoom count остаётся1, peak seed owners1.
- Новый synthetic client снова читает exact cache file D, проходит новый Family
  bootstrap, descriptor, новую dedicated room и dedicated READY. Cache не записывался.
- Старая dedicated session продолжает тот же Mux stream и TCP socket. Authenticated
  lease exchange принимает sequence1 для того же holder/setup; после старого deadline
  проходят новые полные frames. **Только lease clock контролируемый**, не реальное
  десятиминутное ожидание и не renewal production credentials.
- Revoked bootstrap после rejoin отклонён; дополнительная room не выделена. Parser
  отвергает D на её обычном expiry. Trust/floors/lease policy не ослаблялись.

Отдельно: driver не восстанавливает private `SeedManager.directory`/HTTP publication
после завершения Run. Он доказывает возможность bootstrap по сохранённому D при
живом восстановленном endpoint. Это capability experiment, не скрытый service fix.

## Media, cache и session receipts — race×3

Каждая строка — отдельный disposable эпизод с собственной исходной D; внутри эпизода
serialized bytes и hash неизменны. Разные хэши между эпизодами ожидаемы.

| Run | Directory SHA256 | Numbered frames / TCP accepts | Recovered seed RTP RX / binary frames | SFU RTP RX / forwarded |
|---|---|---:|---:|---:|
| 1 | `e81f34fe3144bb2e8ee7c01e4c9b985b6a25b5f25f4b607394a80f9a41f5ad64` | 256 / 1 | 19 / 18 | 3347 / 3344 |
| 2 | `b00b6d14fc339c9e81078d4dacdad48d98855571914a221937e089d4890d1a18` | 256 / 1 | 19 / 18 | 3337 / 3336 |
| 3 | `2f4187e204d9cbb36d43352d95643153ccbe7e9af06b30d4518d9fc532765aea` | 175 / 1 | 34 / 31 | 2371 / 2367 |

Во всех: три seed media generations, одна seed room, две dedicated rooms всего;
один holder/session tag и stream ID для продолжающегося TCP; renewal sequence1.
Это application-level frame/Family proof, не сравнение RTP sequence между PCs.
Не заявляется Android TUN/Internet egress — эта задача полностью локальная.

## Failure matrix, generation и ресурсы

`TestLocalRejoinFailureMatrix`:15 cases×3. Один1011; два1011 внутри reconnect;
исчерпание трёх attempts; service stop во время backoff; room deleted; room expired;
join credential expired; metadata unavailable; bad SDP; ICE failure; отсутствующий
subscriber offer/media readiness;1008;1002; malformed JSON; parent security-bound expiry.

Только typed1011/ACTIVE/not locally closed разрешён к повтору в experimental driver.
Остальные ошибки terminal. Budget3 под исходным ConnectTimeout45s; attempt≤15s,
wait300/600ms остаётся внутри parent bound. Это локальные settings, **не утверждённая
production retry policy**. Negative ICE/offer tests сокращают только test parent.
После каждого исхода WS/PC/retained peers0, room count1, повторного CreateRoom нет.

После нового ACTIVE и во время cached bootstrap вызваны старые ICE/write/PC-state
handlers, old cancel/Close и delayed old callback. New generation продолжила media
и bootstrap; first1011 не заменён cleanup. Старые reader/writer и Pion close завершены.
Нет доказательства для будущего supervisor, которого пока нет; не все мыслимые
callback orderings исчерпаны локальной матрицей.

Full episodes после cleanup: WS0, PC0, retained peers0; goroutines2→2; FD6→8
(включая одноразовую инициализацию runtime). Нет линейного роста при×3. ICE teardown
связан с PC.Close; отдельный счётчик всех внутренних Pion timers/buffer bytes не снят.

## Acceptance и ограничения

| Gate | Result |
|---|---|
| PRODUCTION_SIGNALING_PATH / FIXTURE_TOPOLOGY | Real client operations + explicit local network/SFU model |
| REAL_WS1011_INJECTION / SAME_ROOM_IDENTITY | PASS_LOCAL |
| SIGNALING_RECONNECT / SDP_ICE_RENEGOTIATION | PASS_LOCAL |
| PION_MEDIA_RECOVERY / RTP_VP8_DATA_AFTER_REJOIN | PASS_LOCAL, actual packets/frames |
| DIRECTORY_BYTES_UNCHANGED / CACHED_BOOTSTRAP_AFTER_REJOIN | PASS_LOCAL |
| DEDICATED_SESSION_CONTINUITY | PASS_LOCAL, real Pion/Family/Mux, same TCP |
| LEASE_RENEWAL_CONTINUITY | PASS_LOCAL_AUTHENTICATED, controlled lease clock |
| GENERATION_ISOLATION / STALE_CALLBACK_CLEANUP | PASS_LOCAL tested orderings |
| RESOURCE_BOUNDS | PASS_LOCAL measured WS/PC/peers/FD/goroutine bounds |
| SECURITY_INVARIANTS | Revoked bootstrap/rejection/lease gates PASS; no production change |
| SAME_ROOM_REJOIN_CAPABILITY | UNKNOWN at actual provider eligibility boundary |
| PROVIDER_CONTRACT_LIMITATION | Real room retention + fresh complete media rejoin after1011 not evidenced |
| PRODUCTION_IMPLEMENTATION_PLAN | NOT_CREATED; capability gate remains open |
| DEPLOYMENT / OWNER_CONNECT | NOT_RUN / NOT_RUN |

- Final media/matrix race×3: **54 test PASS events,0SKIP,0FAIL**, no DATA RACE.
- Baseline and experimental security/lease race×3: **129PASS/0SKIP/0FAIL each**.
- Full legacy suite **not rerun**, not claimed green. Earlier six diagnostic
  assertions/busy-wire issues remain historical; this task does not fix or reclassify them.
- Privacy scan: no raw SDP, join URL, credentials, private key or payload in final
  structured logs. Transcripts retain message kind, synthetic generation, PC/ICE state.
- Room retention/rejoin permission and SFU routing are explicitly fixture policies.
  Real TURN/NAT/WAN, provider decoder/slot migration and remote credential lifetime
  after1011 are not tested. Repeated metadata GET is not provider capability evidence.
- The parent-expiry case is **not** a real X.509/CRL expiry during SDP negotiation;
  that specific combined timing remains untested. Existing security rejection gates
  and unchanged credential deadlines must not be confused with such a test.

Ранние fixture ошибки сохранены: sandbox socket denial; compile service field;
недопустимый test service alias (production policy правильно отклонила его);
fixture cleanup measurement race и неверно выбранный truncated JSON input. Они
исправлены только в fixture, исходные logs не переписаны. Protocol assertions не ослаблены.

## Финальное состояние

Все production/owner counters0: deployments, gateway restarts, credential renewals,
owner installs/instrumentation/refresh/CONNECT, live Telemost rooms, gate arm.
Remote commands0. Current runtime/lifecycle не опрашивались. Dirty worktree сохранён;
main product source не менялся, эксперимент — только в capsule. Временные synthetic
profiles удалены после тестов; source/logs/evidence сохранены. Commit/push/release нет.

Historical FUNCTIONAL_WARM_START=PASS_IN_TESTED_SCENARIO сохранён.
ATTEMPT_CONSUMED=NO; readiness не повышена.
PUBLIC_RELEASE=NOT_RUN; REAL_RESTRICTED_NETWORK_FIELD=NOT_RUN.

**Единственная недоказанная provider boundary:** сохраняет ли реальный Telemost
room после seed WS1011 и допускает ли **полный новый publisher/subscriber media join
по прежнему cached join identity**. Нужен независимый contract/evidence именно этой
границы, не ещё один metadata GET. До этого ни production supervisor, ни successor
design как «доказанно необходимый», ни deployment/live test не запускаются.
