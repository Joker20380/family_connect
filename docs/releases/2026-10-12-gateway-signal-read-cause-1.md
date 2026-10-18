# GATEWAY-SIGNAL-READ-CAUSE-1 — PARTIAL

12.10.2026. Offline/source/local-fixture work; one bounded read-only gateway
snapshot. **No deployment, restart, renewal, publication change or owner action.**

## Result

| Requested result | Outcome |
| --- | --- |
| SIGNALING_READ_CALL_PATH | Established on exact deployed source `a4087e000fdbe674b72ede3a6c8822445c87c654` |
| CONNECTION_AGE_AND_DEADLINES | Process age known; exact signaling age/last RX/TX/ping/pong NOT_RETAINED |
| LOW_LEVEL_ERROR_CHAIN | Original object was available at `ReadJSON`; replaced before shared-seed return and not retained in fatal receipt |
| SAFE_ERROR_CLASSIFIER | Local observation-only candidate; typed/allowlisted, no error-text matching |
| LOCAL_FAILURE_MATRIX | Real loopback Gorilla WS/WSS boundary + composed seed/fatal bridge; targeted race×3 PASS |
| CURRENT_BEHAVIOURAL_CONTRACT | Shared sole-seed loss fails closed; peer failures isolated; requested service stop remains controlled |
| HISTORICAL_ROOT_CAUSE | **UNKNOWN** at low-level; `SEED_READ / SIGNAL_READ` boundary remains proven |
| INDEPENDENT_REPRODUCIBLE_DEFECT | **NOT_PROVEN**; reconnect/periodic provider rotation policy is not established by current protocol |
| WHITELIST_WARM_START_IMPACT | Restart changes seed/directory; old cached route no longer served, regardless of its cryptographic validity |
| REMEDIATION_OPTIONS | A–D evaluated below; no recovery design silently selected |
| SELECTED_REMEDIATION | Retain the first low-level signaling class for a future natural trigger |
| BEHAVIOURAL_PATCH | **NONE** |
| LOCAL_BEFORE_AFTER | Same terminal/cleanup behavior; more precise optional fatal metadata |
| SECURITY_AND_RESOURCE_INVARIANTS | No auth/admission/expiry/ownership/room/retry change; constant-size immutable metadata |
| DEPLOYMENT | NOT_RUN |
| OWNER_CONNECT | NOT_RUN |

`READY_FOR_CLEAN_RETRY=NO` is not promoted by this investigation. Earlier late
physical attempt remains consumed; no new attempt was used or authorized here.

## Immutable evidence and scope

Inputs: [observation deployment](2026-10-12-gateway-seed-read-observability-1.md),
[seed-read analysis](2026-10-12-gateway-seed-read-cause-1.md),
[warm-start episode](2026-10-12-whitelist-warm-start-1.md).
All **85** entries of the observation task's `SHA256SUMS` verified before analysis
and at packaging. Original application/systemd receipts were not edited or regenerated.

Evidence root:
`state-client-build/field65-export16/gateway-signal-read-cause-1/`.
Exact source is an isolated checkout of the deployed commit, **not** the dirty main
worktree. `source.diff` includes five production observation files and four new test
files. `scope.txt` identifies each change. `manifest.json` records base commit,
diff/file hashes, local binary/toolchain and truthful `vcs.modified=true` provenance;
no new commit, branch, tag, push or public artifact. Existing APK research84 untouched.

Deployed input binary:
`fa4cf8672c3606c1b6d4d665a6944b4ebe8661076a19a6d2187909263f733eea`.
Earlier baseline retained:
`0ccaaf81666f0873253e95d1532e89d7203677f675efc6f2627dbcd03882667a`.
Local candidate identity is in the manifest; it is **not** loaded/next on the server.

Local candidate binary SHA256:
`21f0a0fdc27b50c00ea922f0b716516e2422aedf1b3797369718f7d00070509a`.
Complete source/test diff SHA256:
`7e7d408670a6ac6afa18e856beb8dcc0ca26a3b6f074e205d4dd25e62d78967b`.
Patched source identity is **base commit + exact diff**, not an invented clean SHA.

One read-only SSH snapshot at **14:55:43.566 UTC** found active/running
PID **1328380**, invocation **e24e32cf8121436ca6ab772f7779362b**, `NRestarts=1`.
Loaded/next both match deployed `fa4cf867…733eea`. Observer configured; application
directory service-owned 0700, systemd directory root-owned 0700, receipts 0600,
counts 9/10 within bound32. No new invocation receipt beyond the preserved set.
This is a bounded snapshot, **not** continuous monitoring or a fresh chain/cache
readiness check. No journal/kernel retry, remote write or phone lifecycle call.

## UTC chronology / attribution

| Event | Timestamp / source | Correlation / confidence |
| --- | --- | --- |
| Gateway invocation started | 13:42:14 UTC, matching systemd receipt (`16:42:14 MSK`) | `e5b8e21cb95440ce890062bede9ea6fa`, PID1305534; direct evidence |
| Shared seed creation / signaling connected | Exact timestamps NOT_RETAINED | Published lifecycle + seed generation1 prove a seed existed, not its precise age |
| Last JSON RX / TX / ping / pong | NOT_RETAINED | No surviving event-level shared-seed trace |
| First immutable failure recorded | Application receipt 14:22:01.363107849 UTC | Same invocation; `SEED_READ / SIGNAL_READ`, fatal=true, returned_error |
| Process exited | Systemd exit timestamp 14:22:01 UTC | Same invocation/PID, exit1, service_result=exit-code |
| Service-manager receipt | 14:22:01.450482 UTC | Invocation match=true; original bytes retained |
| Automatic restart | 14:22:31 UTC | New invocation `e24e32cf…9362b`, PID1328380, NRestarts1 |
| New directory issued | 14:22:33.825470806 UTC, previous post-restart evidence | `631ad219…35664`; expires18:22:31.743955333 UTC |
| This task's read-only snapshot | 14:55:43.566 UTC | Same new invocation; no manual restart |

Original fatal files are under the previous task's
`preserved/receipts/fatal-{application,systemd}/`, named by the old invocation.
Application elapsed time **2,386,358ms** is process-observer elapsed, not a measured
WebSocket connection lifetime. Host monotonic clocks are not compared across hosts.
Receipt timestamp follows cleanup; it is not an exact timestamp of the first failed
byte read. Old directory:
`c55d9c7790fecb3373dda92f3ac1ac3fa5bb1334e9907d3be80e288c6f0afd33`.
Post-restart directory:
`631ad2197c567f8c109f6807c3afdc6596fbdcbd1af76389314d29de0b235664`.

For **this 14:22 fatal**: `OWNER_CONNECTS_AT_FATAL=0`,
`OWNER_TELEMOST_SESSIONS_AT_FATAL=0`,
`RELATION_TO_OWNER_CONNECT=EXCLUDED_FOR_THIS_FATAL`, as established by the preceding
episode and task. Background server/client activity is not thereby excluded.
The separate 12:17 `SEED_READ/UNKNOWN` remains UNKNOWN; its relationship to the late
physical CONNECT remains NOT_ESTABLISHED. No retrospective reassignment to timeout,
DPI, caller, expired credentials or provider rotation.

## Exact signaling read path

Paths below refer to the isolated exact source, not current dirty root code.

1. `cmd/bootstrap-broker/main.go:153`: service signal context + `--duration 4h`;
   `SeedManager{RotateAfter:3h, Observe:observer.failure}`. Shared broker and profile
   are constructed before starting seed and HTTP serving goroutines.
2. `bootstrap/seed_overlap.go:36` runs child `SeedManager.Run` generations.
   `bootstrap/seed.go:81` calls `RoomProvider.CreateRoom`, then `TelemostSeed` with
   separate finite lifetime and readiness contexts. Provider room creation is the
   existing authenticated API call, bounded15s; no provider-room TTL contract is
   returned by `roombroker.Room` (`ID`, `JoinURL`).
3. `bootstrap/seed.go:42` creates `telemost.Session` with VP8 and a bounded
   `sessiontrace.Recorder` whose external sink is nil. `Session.Connect` fetches room
   connection metadata (`telemost/auth.go:116`, bounded15s), sets up Pion, dials WSS,
   starts signaling/writer/heartbeat/pruning workers, sends hello and awaits READY.
   Outer seed readiness uses `bootstrap.ConnectTimeout=45s`; Session's internal
   default60s is additionally bounded by that parent. Neither becomes the established
   seed lifetime. These constants are unchanged.
4. `telemost/signaling.go:20` uses **github.com/gorilla/websocket v1.5.3**
   (`carrier/go.mod`), not nhooyr. Dial handshake15s; read limit8MiB. Read deadline
   now+60s at dial, on each pong and after each successful `ReadJSON`. JSON writes15s;
   WS ping every20s with1s control write deadline, application heartbeat every5s.
5. `Session.signalingLoop`, `signaling.go:110`: `conn.ReadJSON(&msg)` reads one JSON
   object from the shared signaling connection, before dispatch/ACK/conference
   state and SDP handling. Gorilla `json.go:50` calls `NextReader`, then JSON decode.
   Gorilla caches terminal `readErr`: continuing reads/resetting a deadline does not
   safely revive the same WebSocket after a terminal read/timeout.
6. On read error, if carrier not already marked closed:
   `recordSignalingReadFailure(err)` then
   `signalClosedAt(errors.New("telemost: signaling closed or invalid JSON"), "SIGNAL_READ")`.
   **This is the lossy boundary** (`signaling.go:118`). The newly allocated error
   does not wrap the original. `errors.Is/As` on the later generic error cannot
   recover the network/WebSocket/JSON type.
7. `signalClosedAt` (`:172`) records immutable first carrier close via `closeOnce`,
   stores generic `connectErr`, closes `closeCh`, and cancels lifetime.
   `Session.Recv` (`session.go:248`) unblocks and returns that generic failure.
   Shared `serveCarrier` reports `SEED_READ`; `SeedManager` returns `seed_closed`.
   Overlap coordinator forwards first generation failure; loss of the current sole
   published seed terminates the service path. `main.go:201` cancels/cleans HTTP and
   returns error; main prints generic broker-stopped text and exits1.
8. Session parent-context goroutine invokes `closeFrom`; `cleanupOnce` closes WSS,
   Pion/media resources and waits for workers. Later cleanup cancellation/EOF must
   not replace first cause. Normal service context branch (`main.go:191`) cancels,
   joins workers and returns nil. Per-exchange `OpenServer` rejection is separate.

The old `recordSignalingReadFailure` already used `errors.As` for timeout, close code
and JSON syntax in bounded transient evidence/trace. That trace had no shared-seed
export sink; fatal schema1 copied only first carrier source. Its timeout label
`HEARTBEAT_TIMEOUT` is a diagnostic mapping, not proof a distinct pong watchdog fired.
The new classifier deliberately calls the actual typed timeout `IO_TIMEOUT`.

## Connection age and deadline conclusions

- Fatal generation1 was published; no surviving indication of replacement generation.
- Process4h deadline and configured one-off3h seed rotation were later than fatal
  process age39m46s. `parent_context_at_failure` was empty. These do not support a
  planned process expiry/rotation attribution.
- Receipt limiting expiry17:39:22UTC, remaining11,840s at finish, is from credentials
  inspected at startup; **not** current peer authorization or proof of provider OAuth
  validity. No credential renewal/authority inspection was performed in this task.
- Actual last deadline-extension/RX/pong times and exact room/signaling connect times
  NOT_RETAINED. Cannot distinguish read deadline, remote close, reset, bad JSON etc.
- Cleanup started/completed=true in final receipt describes exit cleanup; it does
  not establish that local Close initiated the read failure. The SIGNAL_READ branch
  checks `closed` before recording, but concurrent cancellation remains possible.
- Provider lifetime/rotation policy not specified by returned connection metadata.
  No numeric coincidence alone identifies any timer. Historical low-level UNKNOWN.

## Local observation-only patch

`telemost/signaling_failure.go` uses `errors.Is/As`, `net.Error`, exported Gorilla
and JSON types, context state and errno. No raw `err.Error()`, close reason, keyword
inference, peer address, URL, headers, cookies, JSON, tokens or identity exported.
The first scalar snapshot is immutable under the existing short `errMu`; it retains
no error object. Reads return value copies. No I/O under that lock. No extra worker,
polling, timer, retry, reconnect or listen endpoint.

Only optional schema1 field `signaling_read` is added to fatal receipt:

```json
{"error_kind":"WS_ABNORMAL_CLOSE","close_code":1006,"context_state":"ACTIVE","carrier_closed_at_observation":false}
```

Allowlist: WS_NORMAL_CLOSE / WS_ABNORMAL_CLOSE / WS_CLOSE / WS_READ_LIMIT /
JSON_SYNTAX / JSON_TYPE / EOF / UNEXPECTED_EOF / CONTEXT_CANCELLED /
CONTEXT_DEADLINE / NET_CLOSED / CONNECTION_RESET / BROKEN_PIPE / IO_TIMEOUT /
NET_IO / UNKNOWN. Close code numeric1000–4999 only for WS close categories;
context ACTIVE/CANCELLED/DEADLINE/UNAVAILABLE. The carrier flag is **not** a claimed
local-requested-close or cleanup-origin flag. No fabricated RX/TX/ping ages, byte
counts, auth states or read-deadline remaining values.

`SeedFailure`/`observedSeed` forward the optional immutable value. Fatal observer
sanitizes again and copies only when the winning first close is SIGNAL_READ. Existing
stage/cause/error return/exit policy remains unchanged, including UNKNOWN cases.
Unchanged schema1 receipt file modes/atomic writer/retention32/write-failure behavior
are exercised by existing tests. Late cleanup and unrelated first-close categories
cannot acquire or overwrite a signaling root cause.

## Local failure matrix / limitations

Same common fixture on baseline and patched sources uses actual Gorilla loopback
WS and trusted fixture WSS, then **actual `Session.signalingLoop`/`Recv`/cleanup**.
No `Session.Connect`, external Telemost room/provider or owner identity.
Fatal bridge separately replays each captured value through real SeedManager
`runOverlap` and fatal observer with a synthetic PacketEndpoint. This composition
tests forwarding/service policy, not a live or full-provider end-to-end test.

| Case | Actual boundary result | New safe receipt | Behavior before/after |
| --- | --- | --- | --- |
| A normal JSON | ACK dispatch | no signaling error | Carrier remains open until explicit fixture close |
| B clean remote close1000 | `*websocket.CloseError` | WS_NORMAL_CLOSE/1000 | Shared carrier still terminal/fatal seed loss |
| C abnormal close without close frame | `*websocket.CloseError` | WS_ABNORMAL_CLOSE/1006 | Same terminal behavior |
| D remote EOF | Gorilla converts EOF to close1006 | WS_ABNORMAL_CLOSE/1006 | Raw EOF versus other abnormal close not recoverable here |
| E partial WebSocket frame | close1006 | WS_ABNORMAL_CLOSE/1006 | No fabricated partial-byte count |
| F malformed JSON / wrong JSON type / empty message | `*json.SyntaxError` / `*json.UnmarshalTypeError` / unexpected EOF | JSON_SYNTAX / JSON_TYPE / UNEXPECTED_EOF | Same terminal behavior |
| G oversized / invalid frame | ErrReadLimit / unexported generic error | WS_READ_LIMIT / UNKNOWN | Neither becomes retry/success |
| H read deadline | `*websocket.netError` timeout | IO_TIMEOUT | Same terminal behavior |
| I ping, peer sends no pong | Same read deadline timeout | IO_TIMEOUT | No independent PONG_TIMEOUT invented |
| J caller deadline | Parent-context close | PARENT_DEADLINE, no SIGNAL_READ detail | Existing controlled parent path |
| K caller cancellation | Parent-context close | PARENT_CANCELLED, no SIGNAL_READ detail | Existing controlled parent path |
| L local requested close | Explicit Session.Close | UPPER_CLOSE, no SIGNAL_READ detail | Same cleanup; no new fatal promotion |
| M TCP reset | `*net.OpError` wrapping reset | CONNECTION_RESET | Same shared loss |
| N real WSS TLS close_notify | Gorilla close1006 | WS_ABNORMAL_CLOSE/1006 | Cannot identify TLS close_notify from retained Gorilla error alone |
| O conference ended JSON / provider-related close codes | Parsed message / close1012,1008 | CONFERENCE_ENDED separately / WS_CLOSE numeric code | No claim that1012 proves planned provider rotation or1008 proves auth rejection |
| P controlled service shutdown | Existing main/fatal/subprocess tests | Controlled, not new SIGNAL_READ fatal | Exit/cleanup unchanged |

16 real boundary cases plus3 local shutdown cases. Pure classifier tests cover
wrapped/unwrapped typed EOF, unexpected EOF, cancel/deadline, closed, reset, pipe,
timeout, network error, JSON errors, read limit and close codes (including4008).
Public TLS AlertError/RecordHeaderError are tested as **UNKNOWN type-only inputs**;
no real TLS alert injected on this TCP/WSS boundary and no invented TLS_ALERT cause.
Gorilla's unexported invalid-frame error remains UNKNOWN rather than text-matched.
TLS alert subtyping and fine-grained EOF distinctions therefore remain limitations.

Three repetitions with race detector: signaling/classifier/immutability, seed
forwarding/overlap, fatal bridge/privacy/retention/write-failure/stale callbacks/
subprocess and mandatory negative-auth rejection PASS; no race report.
64 concurrent late callback attempts cannot overwrite first snapshot; value-copy
mutation cannot change stored state. Existing consecutive-invocation/retention tests
preserve separate receipts. No arbitrary payload/error strings in new receipts.

**Full suite NOT_GREEN.** Six previous product-identity diagnostic assertions remain.
Busy-wire assertion is separately flaky on both sources: isolated20-repeat run
baseline **8 failures/12 passes**, patched **9 failures/11 passes**. Initial full×3
baseline did not hit it, patched hit it once; do not call that first comparison equal.
Combined full/stress failure-name sets match baseline; no new failing assertion name
or race detected. Assertions are unchanged; neither diagnostics nor busy-wire fixed.
Exact final full-run counts and matrix are in `receipts/local-acceptance.json`.
Final full×3 hit the busy-wire assertion twice; this is not an equality of failure
frequencies or a statistical stability claim. Original six diagnostic failures each
occurred three times on both sources. The separately mandatory rejection gates pass.

## Shared seed policy and remediation choices

`bootstrap/README.md:63` explicitly says loss of the sole seed fails closed and that
persistent restart recovery is not claimed. Shared seed is intended to last until
finite rotation/lifetime, but durable availability is not guaranteed. Periodic provider
disconnect/rejoin guarantees are not documented by current API/code. Session.Connect
is single-use; closed WSS/Pion/Session cannot simply be retried as the same object.

| Option | Assessment / security and continuity constraints |
| --- | --- |
| A — in-process reconnect same seed | Potentially smallest continuity design, **not proved safe here**. Requires fresh permitted signaling negotiation for same room, bounded attempts/backoff, no retry of auth/protocol/UNKNOWN, one seed owner/generation, stale callback isolation, cancelable recovery, admission/replay continuity and same-directory acceptance proof. Existing API does not provide this recovery contract. |
| B — new seed + bounded overlap | Existing planned3h replacement permits at most2 live seeds, READY-before-publication and original finite old TTL. It does not recover a seed already dead: advertising overlap cannot make the old cached room reachable. Must first solve how old-cache clients reach a living seed; never extend stale trust/expiry or confuse holders. |
| C — restart with stable seed/directory | Not implemented; needs secure route/session persistence, provider reuse/rejoin permission, fresh auth without replay, revision/revocation checks, bounded generation cleanup and publication atomicity. A cached room URL is not proof it remains serviceable. No new persistent credentials/keys introduced. |
| D — existing restart without overlap | Current safe fail-closed behavior; no parallel seed/admission weakening. New invocation makes old route unusable; ordinary authenticated refresh required. Does **not** solve restricted-network cached warm-start across restart. |

No current claim of cross-restart old-directory acceptance was found to violate.
The architectural availability gap is real, but is not proof of erroneous process-fatal
policy for this unidentified error. **No independent behavioral defect or behavioral
patch**. Do not change TTL, systemd delay, signaling timeout, RTO/retries or classify
all UNKNOWN/1000/1012 as safe recovery. First improve observation at the proven lossy
boundary; product continuity policy/implementation remains a separate decision.

## Operator protocol, actions and remaining state

[Two-phase runbook](../whitelist-warm-start-two-phase-runbook.md) unchanged and not
executed. All22 operator fixtures rerun PASS: prepared/armed → ACK-required READY →
operator ACK → fresh gate/invocation/headroom recheck → active physical CONNECT
window → observed event. Fatal/invocation change before CONNECT aborts without
consuming a new attempt; late CONNECT after cleanup is OUTSIDE_TEST_WINDOW, not a
PASS/FAIL. Gate remains900s/32; no rearm. Host crash has finite-TTL fallback, not an
unproven guarantee of immediate disarm. Live adapter wiring remains future work.

Task counters: owner CONNECT0; instrumentation0; refresh0; APK install0; native/TUN0;
Telemost rooms/sessions created0; gateway restart/deployment0; renewal/publication0;
owner gate arm0. Only external action: one bounded read-only NL metadata snapshot.
Loopback fixture networking is separate and not product/owner traffic.

Owner not queried or touched. Last saved owner12:23:09UTC VPN OFF/app ON/
ChatDeliveryService ON/gate CLEANED is **historical**, not a new lifecycle measurement.
No cache/vault/history/key reads; no AWG/TCP/API/mailbox modifications. Deployed
observer and rollback retained unchanged. No new claim about current chain validity
at closeout; previous expiry17:39:22UTC is historical and must be rechecked later.
Temporary synthetic credential fixtures removed after validation; local source,
candidate, test receipts and original sealed evidence retained. Nothing pushed.

**Exactly one next operation:** separate controlled acceptance/deployment of the
observation update, then await a natural trigger. No automatic deployment, CONNECT,
warm-start retry, FIELD, APK distribution or application-compatibility work here.
