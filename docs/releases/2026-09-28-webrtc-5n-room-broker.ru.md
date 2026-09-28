# 5N-RB-1 — Automatic Telemost Room Broker

## Результат

**5N-RB-1 = PASS**, в изолированных границах acceptance ниже.
Один short live run, **одна новая PUBLIC conference через официальный API**,
без заранее созданной комнаты и без передачи оператором room URL.
Physical Redmi Note 9 Pro/Android12/cellular сам выполняет authenticated control
request; Amsterdam подключается первым; только затем Android получает descriptor.
Existing Family TLS1.3 admission + setup/device binding + существующий короткий
5N.5 public Mux proof: **4 verified end-site HTTPS200**, Family DNS A/AAAA/NXDOMAIN,
native post-admission DNS guard0, штатный Android exit0. PERF-2 не запускался.

Это **не production rollout** и не доказательство доступности нового control
endpoint через restricted cellular Internet: для временного control ingress
использованы SSH forwarding + `adb reverse`. HTTPS mTLS запросы формирует native
Core на физическом Android; runner не получает/не подставляет Telemost descriptor.
Media/data идут через настоящий Telemost SFU в Amsterdam, не через этот forwarding.

## Starting state / commits / версии

Starting HEAD: `8d899abb06d0baf3f67071441e633eb8e5eda4fe`.
До правок: чужие VPN audit additions STATUS15/PLAN9 lines, untracked
`2026-09-27-vpn-health.ru.md`, `2026-09-27-vpn-load.json`. Сохранены byte-for-byte;
не входят в Room Broker commits. Последний проверенный external CI:
`36268143806`, commit `8e368585`, completed/failure — старый26.09, **не этот код**.
Remote HEAD `8e3685854f3beea07aea573fa775e97a6220a70d`; push не выполнялся.

| Изменение | Commit |
|---|---|
| RoomProvider + bounded broker + deterministic core tests | `ff25246` |
| mTLS control, gateway/Android adapters, binding/HTTP tests, short runner | `398df6459b10c65782105e5726c36bc01fad0ed5` |

Runtime acceptance собран из398df64. `dirty=true` честно сохранён: оставались
чужие documentation hunks; source рабочего runtime соответствует commit.
Версии не увеличивались: локальный непубликуемый diagnostic **code4/name5N.5-test-only**
с новым native adapter, идентифицируется commit/hash, не version label.
APK built → installed только для этого smoke → uninstalled. Public/invitation/
signed catalogs/production не менялись: Android beta51/code51, Linux0.2.11,
Windows0.2.15. Новых download links/public checksums нет.

| Проверенный artifact | SHA256 |
|---|---|
| Amsterdam broker executable | `7532388665b4772910516dfe2efffb4ad60ccb4d580122a0d8386d7b2897e40b` |
| Android native arm64 | `ece9c59830f2425359ede26fb9d07e911823221ee2ef0b871744c53c0fa0acae` |
| Diagnostic APK | `7bb111c1be8d0bdbac10ff14aff0c3b2d222ee7d68ea6f16607922e62f41e94b` |

## Архитектура / integration point

Исходный manual path: `FC_TELEMOST_ROOM` в `cmd/telemost-binary`, Android
`files/room.input`, injection в `pilot/android-telemost/live.py`. Existing
`telemost.Session.Connect` уже даёт deterministic carrier readiness.
ProductStore `/v2/registration` и `/v2/provisioning` остаются существующим
identity/provisioning backend; не добавляется вторая identity database.
Изолированный issuer использует его реальные enroll/authorization/revoke APIs.

Новый `carrier/roombroker`: `RoomProvider.CreateRoom(ctx)` и
`TelemostRoomProvider`; bounded Broker; HTTP mTLS control facade;
`TelemostGateway` adapter к прежним Connect/Open/Mux. Standalone opt-in
`cmd/room-broker` colocated с Amsterdam gateway; production services не меняются.
`FamilySession != TelemostRoom`: комната лишь ephemeral carrier infrastructure.
Yandex HTTP logic сосредоточена в `provider.go`, отсутствует в Android, Family
Session, gateway media, ReliableStream, Mux и DNS.

```text
Android --broker-url + existing private Family profile
  → admitted device mTLS control request/challenge
  → RoomProvider → official CREATE PUBLIC, HTTP201
  → Amsterdam TelemostGateway.Start → existing Connect → READY
  → ephemeral descriptor issued and claimed once by same Family/device
  → Android Telemost join → existing Family TLS/ReliableStream
  → bound setup proof → existing Mux → Family DNS/TCP → Internet
```

Нижние слои **не менялись**: Family TLS/admission implementation, ReliableStream,
VP8/RTP, Telemost signaling/media, Mux scheduling, DNS, TCP forwarding.
CLI/Android Service/control-plane adapters — единственные integration changes.

## Official API / secret boundary

POST `https://cloud-api.yandex.net/v1/telemost-api/conferences`, JSON
`{"waiting_room_level":"PUBLIC"}`, OAuth scheme. Credential source:
**`YANDEX_TELEMOST_OAUTH_TOKEN`, env only**. Eligibility/Yandex360 не исследовались.
Из локального environment токен передан disposable server через encrypted SSH
stdin, установлен только в environment remote process; не записан в файл.
Нет credential в аргументах процесса, Git, CI, APK, Android descriptor или reports.
Android build helper явно удаляет переменную из child build environment.

Provider принимает только HTTP201; parses id/join_url, reject empty/missing/wrong
types, malformed/trailing/duplicate-key JSON, oversized body, неожиданный status.
Response≤16KiB; id≤256B printable; join URL≤2048B, HTTPS, exact Telemost host,
валидный `/j/` identifier, без userinfo/port/query/fragment/encoded path.
Redirects запрещены. No application retries. Timeout/cancel/400/401/403/429/5xx
имеют разные safe error codes. Ни response body, ни Authorization не возвращаются
в ошибках. Room/descriptor/provider formatting redacted; normal events без room
URL, provider ID или device identity. OAuth exact-byte scan tracked sources,
smoke logs и **распакованных APK entries** PASS; значения не выводились.

## Lifecycle / timeouts / abuse

`AUTHORIZED → CREATING → CREATED → GATEWAY_JOINING → READY → CLIENT_ISSUED →
ACTIVE → CLOSED`; terminal alternatives FAILED, EXPIRED, CANCELLED.
Creation timeout **15s**; READY timeout **45s**; unused challenge/descriptor TTL
**60s**; maximum accepted setup/session **10min**. Standalone live server hard
lifetime3min; runner native-flow deadline150s. Authorization recheck every1s.

Maximum **one outstanding per Family/device**, **32 globally**, включая unused
authorizations и active sessions. Random256-bit server setup authorization bound
to authenticated identity. Duplicate creation/claim rejected; no second room.
Unknown/expired ID не оживает после удаления. State removed only after gateway
cleanup; terminal reason передаётся safe response/event. No unbounded tombstones.
Cancellation propagates through provider HTTP, gateway join and running carrier;
Close waits for owned work. No invented Telemost deletion: expiration прекращает
Family use/admission, **не обещает удаление conference у Yandex**.

## Authentication / descriptor / gateway-first

Control TLS1.3 reuses `familysession.Configuration`: authority chain, Family,
identity public key/role/revision, gateway pin, signed CRL, expiry; no resumption.
HTTP/1.1 ALPN adapter явно проверяет свой protocol перед вызовом существующего
Family claim verifier, не отключая certificate validation. Gateway profile
reload при handshake/request и periodic recheck; invalid/revoked/expired profile
terminates setup. Production distribution of fresh signed CRLs не добавлялась.

POST challenge/create/claim/cancel routes получают identity **из mTLS**, не из
request JSON. Request body≤256B. No unauthenticated room creation. Descriptor:
`transport`, `setup_id`, `join_url`, `expires_at` — без provider credentials;
response no-store. Gateway получает room внутри adapter, Connect success означает
READY; arbitrary sleep не используется для выдачи descriptor.

После existing Family TLS gateway sends fresh32-byte challenge. Existing device
Ed25519 key signs purpose-separated setup ID+challenge. Verification against key
from authenticated control request precedes Mux activation. Это control binding
adapter внутри уже encrypted session, **не замена TLS/новый cipher или key exchange**.
Другой device key, другой setup ID и replay old proof отвергаются. TTL проверяется
на claim/activation; claim сам по себе не продлевает время и не означает ACTIVE.

## Focused deterministic tests / regression

- Provider local HTTP mocks: method/path/OAuth application/PUBLIC body/201; timeout,
  cancellation,400/401/403/429/503/unexpected200, malformed/trailing/duplicate JSON,
  missing/empty id, missing/bad URL, oversize, redirects, missing env, redaction.
- Broker: authenticated create, denied identity, wrong Family, duplicate
  authorization/create/claim, one fresh room, withheld descriptor until READY,
  gateway receives binding, provider/gateway failures and deadlines, cancellation,
  authorization change, unused expiry, active-vs-unused lifetime, outstanding
  bound, concurrent duplicate challenge, stale ID and released retained resources.
- ProductStore-issued **real mTLS** profiles: valid works; unknown authority,
  wrong Family, revoked device and missing TLS rejected before provider call.
  Client descriptor does not include provider token/private key.
- Existing Family TLS paired-endpoint tests for new control binding: valid,
  other setup, other device and replayed proof. No data-plane implementation change.
- Go1.27.1 `go test -race -count=1 -timeout60s`:
  roombroker, familysession, telemost, cmd/telemost-binary **PASS**.
  `FC_FAMILY_TEST_FIXTURES` supplied: profile/binding tests **not skipped**.
  `go vet` roombroker/cmd-room-broker/cmd-telemost-binary **PASS**.
- Python focused control/provisioning/issuer/runner **57 passed**,2 existing
  dependency deprecation warnings; runner validator subset8 passed locally.
- Android arm64 CGO build, assembleDebug, **6 JVM tests**, lintDebug **PASS**.
  Existing manifest/native-library/deprecated-API warnings retained; no Windows/
  Linux UI builds or full matrix, fuzz campaigns, PERF-2 or30min carrier run.

Pre-live deterministic corrections: HTTP mock waiting on an unread request body
stalled cleanup; draining body and bounded mock wait fixed it. First mTLS mock
exposed generic HTTP server rejecting data-plane ALPN; explicit control HTTP/1.1
adapter fixed it. Neither failure used real provider API; no live retries-to-green.

## One real automatic smoke / evidence

Only live attempt: **28.09.2026,13:56 UTC**. Official provider success inferred
unambiguously from strict HTTP201-only CreateRoom return and CREATED transition;
raw response/room identifiers intentionally not retained in report.

| Gateway event | UTC |
|---|---|
| CREATING | 13:56:11.950321431 |
| CREATED — fresh API201 | 13:56:13.196593731 |
| GATEWAY_JOINING | 13:56:13.196626491 |
| READY — physical Amsterdam Connect success | 13:56:14.882831909 |
| CLIENT_ISSUED | 13:56:14.882987757 |
| family_auth | 13:56:23.686787024 |
| ACTIVE — device/setup proof accepted | 13:56:24.812156225 |
| CANCELLED — client cleanup | 13:56:33.277456019 |

Creation1.246s, gateway join1.686s; no operator room. Android start metadata
`authenticated automatic broker`, Redmi Note9 Pro/Android12/arm64/cellular,
Wi-Fi off/no VPN. End-to-end native run**21.922s**, Mux public proof**7.498935205s**.
Four independent stream IDs1/3/5/7: verified end-site TLS, HTTP200, passed=true.
Family A/AAAA rcodes0/0 and `.invalid` NXDOMAIN rcode3; native DNS guard enabled
negative probe blocked, final post_probe_calls0. Android Family protocol
`family-connect-5n3-test-v1`, accepted=true; Android exit0, cancelled=false.
Этот существующий canonical5N.5 connection достаточен для gate; дополнительный
длинный canonical echo/PERF-2 не запускался.

## Cleanup / rollout / remaining limits

Runner cancel завершил gateway setup; broker shutdown и временный каталог удалены.
Read-only проверка: task-owned Amsterdam dirs0/processes0, diagnostic APK отсутствует,
native PID1780 отсутствует, task adb reverse removed, radios restored, cleanup errors[].
Disposable local credentials/DB, broker binary и private smoke logs **удалены** после
фиксации allowlisted evidence. Пять APK/native outputs удалены только после
совпадения task SHA256. Shared toolchain/Gradle caches и обычные непубличные
build intermediates без credentials не удаляются.

Production rollout отсутствует. Rollback изолированной проверки — stop task-owned
broker, uninstall diagnostic APK, remove private inputs/SSH+ADB forwarding,
restore radios; existing manual developer/emergency room path остаётся рабочим.
No signed catalog/invitation/public artifact mutation. No push.

MVP limitations: **no TUN/VpnService, no generic UDP, no room pooling/sharing/reuse,
no HA broker, no provider-account rotation, no seamless Family Session migration,
no production load/capacity claim**. No DataChannel substitution. No durable setup
recovery or distributed leases. Sequential admitted setups have no long-term quota;
only bounded outstanding state. Current profile reload assumes signed CRL publication,
not instantaneous ProductStore revocation propagation. Production identity distribution
and deployable restricted-network control ingress were not rolled out or claimed.

Gate checks complete within these limits. **STOP** after5N-RB-1. 5N.6, Transport
Orchestrator, performance tuning, multi-user load and production rollout не начаты.

[API/lifecycle/run guide (EN)](../../carrier/roombroker/README.md)
