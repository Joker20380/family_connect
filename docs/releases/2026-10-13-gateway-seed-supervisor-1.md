# GATEWAY-SEED-SUPERVISOR-1 — PASS (local acceptance only)

**PRODUCTION_PATCH_ACCEPTED = YES. DEPLOYMENT = NOT_RUN. OWNER_CONNECT = NOT_RUN.**

Minimal same-room production seed supervisor implemented in an isolated exact-source
capsule, not in the dirty working product tree. Candidate built and locally committed;
not installed, deployed, pushed, tagged or published. No SSH/ADB or live provider actions.

## Identities and evidence authority

- Capsule: `state-client-build/field65-export16/gateway-seed-supervisor-1/`.
- Saved deployed gateway binary: `21f0a0fdc27b50c00ea922f0b716516e2422aedf1b3797369718f7d00070509a`.
- Exact source: `a4087e000fdbe674b72ede3a6c8822445c87c654` **plus** classifier diff
  `7e7d408670a6ac6afa18e856beb8dcc0ca26a3b6f074e205d4dd25e62d78967b`.
- Chain: formal-acceptance-2 saved loaded/next snapshot → workability-proof build receipt
  → exact preserved binary/source. `receipts/entry.json` seals individual source files
  and20,355 checked entries from five immutable prior capsules. These are saved provenance,
  **not fresh runtime PID/InvocationID/headroom claims**.
- Candidate validation source: `c9d75db6020f9f605e891036cbb9b68cebede708`.
- Candidate binary: `d6875817cf33fdd85c6ad78a342fc93afd16864293e94a6e5b7136eec5125765`.
- Binary path: capsule `build/bootstrap-broker-seed-supervisor`; clean VCS provenance,
  Linux/amd64, CGO disabled, pinned Go1.26.1, no sameroomfixture build tag/dependency.

Historical WS1011 remote-close boundary remains PROVEN; provider internal reason remains
UNKNOWN. Previous UNKNOWN exits are not reattributed. The prior live capability episode
really disconnected a provider socket but injected1011 at its test classifier boundary;
this is not a claim that every provider1011 leaves a reusable room.

## Acceptance result

| Requested boundary | Result |
|---|---|
| EXACT_BASELINE | PASS — saved deployed manifest/binary/source chain, not Git HEAD |
| FEATURE_INVENTORY | PASS — per-file protected hashes; API explicitly excluded |
| CURRENT_FATAL_FLOW | PROVEN — seed return → main teardown/Broker.Close → process exit |
| SELECTED_REMEDIATION | SAME_ROOM_IN_PROCESS_SEED_RECOVERY |
| SEED_SUPERVISOR_STATE_MACHINE | STARTING → ACTIVE → RECOVERING → ACTIVE / TERMINAL |
| RECOVERABLE_CLASSIFICATION | PASS — only SIGNAL_READ/WS_CLOSE1011/ACTIVE/non-local |
| GENERATION_CONTEXTS | PASS — service-scoped owner with independent generation contexts |
| SAME_ROOM_REJOIN | PASS_LOCAL_REAL_STACK; existing real-provider capability reused |
| DIRECTORY_CONTINUITY | PASS — room/create/publication count and exact D unchanged |
| DEDICATED_SESSION_ISOLATION | PASS — no global Broker.Close on successful recovery |
| RECOVERY_BUDGET | PASS — ≤3 joins per room lifetime;45s episode;1/2/4s backoffs |
| STALE_CALLBACK_ISOLATION | PASS — object-local callbacks, pointer compare, cleanup-once |
| SECURITY_FAIL_CLOSED | PASS — protocol/policy/unknown/expiry rejected; existing auth intact |
| LOCAL_BEFORE_AFTER | PASS — baseline gateway TCP socket closes; candidate retains it |
| REAL_PION_MEDIA_TESTS | PASS — actual Gorilla/WSS, SDP/ICE, Pion, RTP/VP8 |
| OLD_CACHE_BOOTSTRAP | PASS — original serialized D → authenticated bootstrap → READY |
| PERSISTENT_TCP_CONTINUITY | PASS — same session/stream/socket, numbered traffic across recovery |
| LEASE_CONTINUITY | PASS — authenticated renewal during recovery; controlled lease clock |
| RESOURCE_BOUNDS | PASS — WS/PC/peers0, goroutines2→2, FD6→8; repeated terminal matrix bounded |
| BASELINE_DIFFERENTIAL | PASS — no new failures; full suite explicitly NOT_GREEN |
| BACKWARD_COMPATIBILITY | PASS — directory/bootstrap/Family/lease/API wire unchanged |
| PATCH_SCOPE | Gateway Go only; explicit behavioral stack plus separate receipt persistence |
| LOCAL_CANDIDATE | BUILT_AND_SEALED, NOT_DEPLOYED |
| DEPLOYMENT_PLAN | PREPARED_NOT_EXECUTED; separate synthetic continuity acceptance |

## Lifecycle and security details

Production paths: `cmd/bootstrap-broker/main.go:runObserved` → `bootstrap.SeedManager.Run`
(or existing `runOverlap`) → provider CreateRoom once → `TelemostSeed` →
`telemost.Session.Connect`/FetchConnection/dialWebSocket/Pion → signalingLoop/ReadJSON →
PacketEndpoint.Recv → `serveCarrier` SEED_READ. Previously every shared-seed failure
returned to main, which canceled SERVICE and deferred Broker.Close. Dedicated holders
were already independent before that global teardown; they are not reparented here.

The supervisor consumes only the narrow recoverable class. It rejoins the retained
Room, never calls CreateRoom or Publish on recovery, and keeps original D. Fresh ephemeral
connection metadata/WS/Pion generations are allowed; expired D/profile are not extended.
Protocol1002, policy1008, malformed signaling, unknown classes and security rejection
remain terminal. Resource, callback and admission limits are unchanged.

The three-attempt limit is **per logical room lifetime**, not reset after each success.
Recovery uses the existing45s ConnectTimeout, clipped to directory/SERVICE/security
deadlines; the one-second existing admission poll supplies the backoff base. No new
unbounded reconnect loop/jitter framework. A slow first join can consume the whole budget.
Explicit cancellation in the new recovery flow returns normally; expiry/exhaustion
still reaches the existing terminal service path. No systemd change.

Security checks reread the current private profile before recovery, after backoff and
before promotion, applying existing Family validation plus strict local gateway chain/
role/binding/CRL/floor verification. Security expiry clips join contexts. No independent
live trust-file watcher is claimed. Existing per-bootstrap fresh validation remains.

Failed transport quiescence happens in the existing serveCarrier cleanup **before**
rejoin, preventing duplicate publishers. The failed logical generation stays inactive
until compare/swap with a ready replacement. Old cleanup cannot clear/close the successor.
No lock is held over metadata/WebSocket/SDP/ICE/media waits or disk I/O.

Connected subscriber/publisher states come from production Connect, not a test READY
assignment. Promotion receipts report actual media counters; zero received RTP at that
instant is not claimed as payload proof. Subsequent real RTP/authenticated bootstrap
and byte-exact traffic establish usable media. Planned room rotation and ordinary
directory validity remain in force; this is not permanent-cache support.

## Tests and preserved limitations

Final logs use fresh synthetic credentials generated **after approval**, identical
unchanged TTL policy. Earlier runs crossed their one-hour synthetic certificate expiry
while waiting and correctly failed auth. Their logs/expiry receipt are retained;
neither production credentials nor validation rules were changed to make tests pass.

| Gate | Result |
|---|---|
| `accepted-media-race3` |135PASS,0FAIL,0SKIP |
| `accepted-security-race3` |366PASS,0FAIL,0SKIP |
| `accepted-baseline-security-race3` |357PASS,0FAIL,0SKIP |
| `baseline-confirm-race3` |3PASS — direct gateway TCP close measurement |
| `storage-race3` |9PASS — retention/write failure/permissions/concurrent sink |
| Full baseline / candidate |602 /631PASS; identical15 failed tests/parents;10SKIP each |

Full-suite failures remain: six old bootstrap diagnostic assertions plus parent,
six old seed-read diagnostic assertions plus parent, and the shared timestamp source
guard in the deliberately Go-only snapshot. Real mandatory security rejection tests
pass separately. Busy-wire failure was not reproduced and is not claimed fixed.
No existing failing assertions were changed. One newly authored before-fixture initially
assumed client EOF within5s; that measurement was flaky. It now directly measures the
gateway TCP socket closure and reports client EOF latency NOT_ASSERTED, rather than
changing product behavior or masking a baseline failure.

Real-media tests exercise two successful recoveries,1011 during rejoin, exhaustion,
stop/backoff, policy/protocol, malformed signaling, metadata/room/credential/SDP/ICE/media
failures, expiry/late ready, stale cleanup, concurrent unavailable-window bootstrap,
new old-cache authenticated bootstrap and dedicated continuity. TCP stays on one socket
and Mux stream. Lease alone uses a controlled clock; no12-minute live episode is claimed.
Selected ICE/media failure fixtures use a declared500ms test limit, not a product change.

Protected Family/Telemost/Reliable/Mux/admission/lease source files remain byte-identical.
AKI/skew/ACK/publisher API archive is outside the candidate entirely. Its accepted inventory
is linked, not replaced with stale source. Accepted collector Go patch apply-check passes;
this does **not** claim combined collector+supervisor runtime acceptance or deploy it.

## Artifacts

In the capsule:

- `manifest.json`, `RESULT.json`, `SHA256SUMS`, `feature-inventory.json`, `scope.txt`.
- `source/carrier/`, `candidate.bundle`, `candidate-repo/` (isolated local commit stack).
- `seed-supervisor-behaviour.diff`, `observability.diff`, `full.diff`; apply in that order.
  Behavioral diff contains lifecycle safe-event hooks; separate observability diff owns
  asynchronous persistence/wiring. No hidden test fault adapter in either production diff.
- `receipts/differential.json`, test JSONL/command/source hashes, privacy/build metadata,
  collector compatibility and synthetic-expiry receipts.
- `validation/carrier/` and `baseline-validation/carrier/`: test-only local-provider
  overlays, explicitly **not deployable**. Topology and model boundary in `DESIGN.md`.
- `recovery-schema.json`, `rollback.json`, `baseline-gateway`, `DEPLOYMENT_PLAN.md`.

Recovery receipts: dedicated0700 subdirectory,0600 atomic non-overwriting files,
≤4KiB each,64-file retention and32-slot bounded nonblocking queue. No raw cause text,
SDP/URL/token/payload/device identity. Original safe first cause immutable. Receipt
failure cannot change protocol result; missing receipts are not proof of no events.

Only synthetic test resources are cleaned. Original binary/receipts/source/cache/owner
artifacts are preserved. Main dirty worktree was not reset or committed.

## Counters and next operation

```
GATEWAY_DEPLOYMENT = 0
GATEWAY_RESTART = 0
RENEWAL = 0
OWNER_INSTALL = 0
OWNER_INSTRUMENTATION = 0
OWNER_REFRESH = 0
OWNER_CONNECT = 0
PROVISIONING_GATE_ARM = 0
LIVE_TELEMOST_ROOM = 0
ATTEMPT_CONSUMED = NO
PUBLIC_RELEASE = NOT_RUN
REAL_RESTRICTED_NETWORK_FIELD = NOT_RUN
WHITELIST_WARM_START_READY = NO
FUNCTIONAL_WARM_START = PASS_IN_TESTED_SCENARIO (historical, preserved)
```

**Exactly next operation:** controlled production gateway continuity deployment/
acceptance with fresh baseline/credential preflight, one real isolated signaling
disconnect, same-room/media/D and dedicated continuity checks,30-minute observation,
bounded rollback. No owner whitelist run in that first deployment task. Not started.
