# GATEWAY-SEED-READ-CAUSE-1 — PARTIAL

**Offline/source/evidence only,12.10.2026.** Historical underlying error remains
UNKNOWN; local classification improvement and two-phase operator fixtures PASS.
No gateway/phone contact, SSH/ADB/instrumentation, CONNECT/reconnect, refresh,
room, gate arm, renewal, restart/deployment, APK install/build, push or FIELD.

Evidence/candidate:
`state-client-build/field65-export16/gateway-seed-read-cause-1/` — `RESULT.json`,
`SOURCE_MANIFEST.json`, `historical-attribution.json`, `timeline.json`,
`observability.diff`, `tests.diff`, `observer-schema-delta.json`, `receipts/`,
`harness/`, `SHA256SUMS`. Original warm-start157 + observer65 sealed entries
verified unchanged. Original receipts are neither regenerated nor edited.

## Decision and attribution

| Field | Result |
|---|---|
| SEED_READ_CALL_PATH | PROVEN in exact loaded source: shared seed PacketEndpoint.Recv, before FCB1 decode |
| FIRST_TYPED_ERROR_AVAILABLE | YES at reproducible typed I/O/Telemost lifecycle sites; exact historical object UNAVAILABLE |
| UNKNOWN_MAPPING_LOCATION | fatal safeCause allowlist fallback; some lower Telemost errors already replaced by generic errors.New |
| PER_EXCHANGE_VS_PROCESS_FATAL_CONTRACT | Exchange failures isolated; loss of current shared seed carrier process-fatal |
| RELATION_TO_LATE_CONNECT | NOT_ESTABLISHED; temporal overlap possible, no exchange correlation |
| HISTORICAL_ROOT_CAUSE | UNKNOWN; only first failing shared-seed stage proved |
| LOCAL_REPRODUCTION | PASS for boundary injections and separate per-peer/auth/malformed fixtures |
| OBSERVABILITY_PATCH | Prepared/tested locally; NOT_DEPLOYED; two production files only |
| INDEPENDENT_BEHAVIOURAL_DEFECT | NOT_PROVEN; no behavioral patch |
| OPERATOR_GATE_RACE_CAUSE | Host90s window started without explicit operator ACK; late physical action after cleanup |
| TWO_PHASE_OPERATOR_PROTOCOL | Offline adapter +22 deterministic fixtures PASS |
| FIXTURE_RESULTS | Targeted race/security checks PASS; whole legacy suite NOT_GREEN |
| LIVE_RUNBOOK_UPDATED | Prepared, not executed; linked below |

`TEST_WINDOW_CONNECTS=0`, `LATE_PHYSICAL_CONNECTS=1`, `FULL_PHASE_REQUESTS=0`,
`GATE_STATE_AT_LATE_CONNECT=CLEANED`. `WARM_START_WITH_PROVISIONING_BLOCKED=NOT_TESTED`.
Prior physical budget **ATTEMPT_CONSUMED=YES**; new task actions/attempts0.
No relabeling of the late action as warm acceptance or product failure.

## Exact base, not current-runtime claims

Source is an isolated archive of the clean observer checkout commit
`abc604b0f8ce431174f260ff41ef9b3b6455ba0c`, not the dirty main tree or research84
Android source. Historical loaded/next gateway SHA256:
`0ccaaf81666f0873253e95d1532e89d7203677f675efc6f2627dbcd03882667a`.
No new commit/branch created; candidate identity is base commit **plus exact diff**.
SOURCE_MANIFEST records base tree, minimal diff digest, unchanged source count,
Go1.26.1 and compile-only SHA. Local `go build -trimpath -buildvcs=false` PASS;
temporary executable is not a deployable/published release, not copied to server.

Research84 historical identity preserved: version84,
`0.1.18-research84-provisioning-seam`, package`com.familyconnect.app.friends`,
UID10283, APK`fd3106170ceeb1e24dad6c8eacda4107b1ab09a6ee120ccf495d92d96841aa48`,
signer`67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`,
native`cb3af31f62fdc1339df5f03374652ef6c62c4382ed10ef2d314bd6b610c989e2`.
These were read from preserved evidence, **not remeasured on owner** in this task.

## UTC chronology and evidence limits

All12.10.2026; full source/timestamp/correlation/confidence rows in `timeline.json`.
Device/host/server wall clocks are retained separately; no cross-host monotonic
subtraction or unproved subsecond causal ordering. Systemd MSK converted to UTC.

| UTC | Event / source | Correlation / confidence |
|---|---|---|
|09:43:01 | Old invocation start, systemd receipt | `26e8634a47e24d60b6f7f55a58f7282a`, PID1168539, NRestarts0; seconds precision |
|12:04:07.154 | Gate arm, signed helper receipt/log | nonce`7874c78a…9fddb`;900s/32; device wall |
|12:05:10.240 | Physical listener ready | host receipt; actual chat READY display timestamp not separately captured |
|12:06:40.240 |90s CONNECT deadline | derived host bound; no operator ACK contract |
|12:06:49.633 | OPERATOR_GATE_TIMEOUT result saved | physical0; requests0; original window-only record unchanged |
|12:07:03.704/.898 | Two global provisioning403 records | unattributed; after operator window, not proof of owner requests |
|12:10:44.541 | Gate CLEANUP | same nonce, CLEANED, blocked_calls0; host receipt12:10:45.421 |
|12:12:25 | Restored app/chat; VPN OFF snapshot | latest observed OFF before late action; not an exact button boundary |
|12:12:25/26/27 | Background challenge/fetch/ACK | saved owner-readiness DB metadata; outside test, not seed exchange |
|12:14:37 | Background challenge/fetch | ACK not captured for this row; not a native/seed-start proof |
|≤12:16:49.425 | User-reported late physical CONNECT, VPN ON snapshot | TcpVpnService; exact press timestamp/selected carrier NOT_CAPTURED |
|12:17:02.367 | Application fatal receipt | same old invocation, generation1; SEED_READ/UNKNOWN; read failure occurred by receipt write |
|12:17:02 | Process exit1 | same invocation/PID, seconds precision; NRestarts0 at exit |
|12:17:02.442 | Systemd exit receipt | exit-code / exited / status1, invocation match |
|12:17:32 | Automatic restart | `853bf7d3d15b4194b19629d546eaf92b`, PID1255784, NRestarts1 |
|12:19:07.154 | Original arm absolute expiry | policy deadline only; already CLEANED, no rearm |
|12:20:24/25 | Background fetch/ACK after new publication | separate ordinary background activity |
|12:23:09 | Last saved owner closeout | VPN OFF / app ON / ChatDeliveryService ON; historical |

SEED_READ iteration **start not recorded**; do not equate invocation start/READY
with the start of the failing read. Exact exchange/setup ID, owner seed exchange,
admission/HELLO/cancel/disconnect/native-start events in the late interval are
**NOT_OBSERVED**, not proved absent. Saved client listener ended before that action;
gateway bounded session query timed out; no repeat or broader journal query made.
Empty/TRACE_READY-only collection files do not establish that no clients existed.

The VPN ON snapshot precedes fatal by about13 seconds, so the late action cannot
be excluded merely as post-restart. Conversely there is no client↔seed correlation
to assign causality. No claim of independent-of-clients, owner fault, call, DPI or
Reliable root cause. `RELATION_TO_LATE_CONNECT=NOT_ESTABLISHED`.

Verbatim application SHA`2b699ad0dc63d6ebb17b37a14831dcc13cac091debaf2de6b1614a32525c67de`;
systemd SHA`3abeb9ca17ff739887a49ea11932645c36f31f6792b7280758d5274c0ddadd4e`.
Application: elapsed9240512ms, returned_error, lastSEED_RUN, firstSEED_READ/UNKNOWN,
parent_context_at_failure empty, SEED_PUBLISHED, cleanup started/completed.
Credential limiting expiry13:36:04/headroom4741s; fatal before3h rotation and4h
planned lifetime. This receipt does not support planned lifetime or the separate
earlier PROFILE/CREDENTIALS_REJECTED failures. Older pre-observer causes remain UNKNOWN.

## Actual call path and loss of detail

Paths below relative to **isolated source/**; do not substitute dirty root code.

1. `carrier/cmd/bootstrap-broker/main.go`: main→runObserved. Validated credentials,
   broker, signal/4h context, HTTP mTLS listener and SeedManager with3h rotation.
   manager.Run feeds seedDone; HTTP Serve is a separate sibling. Seed callback
   calls `bootstrap.OpenServer` but returns no error to manager.
2. `carrier/bootstrap/seed.go`: room provider→creation budget→lifetime→45s ready
   connector→TelemostSeed. Shared Telemost VP8 PacketEndpoint, publish Directory
   only after READY. `serveCarrier` reads shared endpoint, not one owner's TLS
   socket and not provisioning. TelemostSeed uses no Reliable stream here.
3. `carrier/bootstrap/carrier.go:162`: `carrier.Recv(ctx)` BEFORE decodePacket.
   Shared read error calls observer with original error then returns
   `roombroker.Code("seed_closed")`. FCB1 has69-byte envelope/max33000-byte data;
   malformed/short/oversized/unknown-kind packets are ignored. No length-stream
   `ReadFull` on this boundary: partial FCB1 packet is not automatically io.ErrUnexpectedEOF.
4. Valid OPEN creates one bounded lease/exchange,120s context. Family admission30s,
   TLS/auth/exchange handling in OpenServer. Per-exchange errors close lease/setup,
   emit existing rejection diagnostics, and shared reader keeps running. Queue
   overflow also closes only current lease. New peer can be accepted after release.
5. `carrier/bootstrap/seed_overlap.go`: only active current-generation failure
   propagated to manager observer/return; superseded seed retirement/failed optional
   replacement do not become arbitrary current fatal. Process restart does not
   retain prior seeds; in-process overlap is a different contract.
6. `carrier/telemost/session.go:247`: Recv returns received packet, callerctx.Err
   or first stored Session.failure(). `signaling.go:172` uses closeOnce, existing
   allowlisted close source, stores first connectErr, closes channel and cancels.
7. One concrete loss boundary: `signaling.go:118` ReadJSON error first goes to
   `recordSignalingReadFailure` (existing timeout/WS close/JSON diagnostic mapping),
   then is **replaced** with generic `errors.New` atline121, sourceSIGNAL_READ.
   Other known closure sites use generic errors with RECEIVE_QUEUE_FULL,
   CONFERENCE_ENDED, negotiation/ICE codes. Historical seed had no recorder/sink
   retaining these codes. No evidence selects one of them for the actual fatal.
8. Original SeedFailure observation carries the raw object before seed_closed;
   it is not lost by `fmt.Errorf` wrapping there. `fatal_receipt.go:safeCause`
   reuses startupdiag; known context/x509/Telemost/EOF/roombroker cases map safely.
   Plain errors.New, network timeout/reset/closed not in that mapping become
   **UNKNOWN**. EOF and unexpectedEOF were already mapped EOF, not UNKNOWN.
9. seedDone branch records fallbackSEED_RUN only if no first cause, cancels sibling
   HTTP, waits cleanup, returns error; main writes application receipt and generic
   stderr, exits1. Generic stderr is not the only original observer path. Shared
   listener no longer usable → process-fatal by current contract. Routine peer EOF
   does **not** by itself take this path. Requested parent cancellation normally
   selects controlled nil-return; competing cancellation paths keep legacy results.

No behavioral violation established. Not treating every context.Canceled as fatal,
not changing deadlines/retries/process-exit policy to keep a dead listener alive.

## Minimal observation delta and privacy

Only production `bootstrap/seed.go` and `cmd/bootstrap-broker/fatal_receipt.go` differ
from exact base. `SOURCE_MANIFEST.json` verifies every other tracked file unchanged.

- Seed connector supplies an existing bounded192-event `sessiontrace.Recorder`
  with nil sink and valid constant nonsecret diagnostic tag. Tag is internal, not
  owner/exchange identity. Embedded endpoint wrapper changes neither Recv nor Close.
- At fatal shared SEED_READ retain `FirstClose.CloseSource` alongside original
  error; allowlist before serializing optional `seed_close_source`. FirstClose is
  set before closeCh, so later local cleanup does not replace it.
- Extend safe typed network mapping via errors.Is/As: NET_CLOSED, CONNECTION_RESET,
  IO_TIMEOUT. Existing typed cause takes precedence. Only UNKNOWN can fall back
  to existing non-UNKNOWN lifecycle code, safe class`sessiontrace.FirstClose`.
- Schema1 gets one optional field; existing receipt consumers ignore additional
  JSON keys. Existing first/sealed guard, generation filtering, atomic0600 receipt,
 0700 directory,32-file retention and systemd layer remain unchanged.
- No raw error string/stack/close text/payload/profile/token/room URL/device ID or
  full trace written. Privacy canaries survive neither before/after receipts nor
  operator fixture output. Generic unknown still safely remains UNKNOWN.

Limit: SIGNAL_READ identifies terminal path, not the discarded websocket/JSON
subtype. Earlier nonterminal FirstFailure is deliberately **not** substituted for
terminal cause. No claim that observation restores lost historical information.

Observer effect is not literally zero: bounded in-memory tracing/locks and one
snapshot at read failure. No network/disk sink in network loop; receipt still
written by existing exit path outside broker/session locks. No changes to packet
framing/media, deadlines, retries, provider decisions, ownership, directory
generation, TTL/security checks or restart policy; identical legacy return
objects/exit classification asserted. No throughput/no-overhead claim.

## Local before/after and suite limitations

| Injected boundary | Original observation → candidate | Scope / legacy outcome |
|---|---|---|
| Shared Recv EOF/unexpectedEOF | EOF → EOF | seed_closed; fatal if parent active |
| Shared Recv net timeout | UNKNOWN → IO_TIMEOUT | same seed_closed |
| Shared Recv wrapped reset | UNKNOWN → CONNECTION_RESET | same seed_closed; no raw wrapper text |
| Shared Recv net.ErrClosed | UNKNOWN → NET_CLOSED | same seed_closed |
| Shared generic signaling/queue/conference error + retained source | UNKNOWN → SIGNAL_READ / RECEIVE_QUEUE_FULL / CONFERENCE_ENDED | same error object/seed_closed |
| Shared caller deadline/cancel | DEADLINE/CANCELLED unchanged | actual parent cause retained; controlled cancellation not relabeled fatal |
| Unknown / forged close source | UNKNOWN → UNKNOWN | fail-safe sanitization |
| Provider failure | provider_timeout unchanged, SEED_CREATE | seed_creation_failed; connector not called |
| Per-peer EOF/partial read/timeout/deadline/cancel/reset | bootstrap_protocol_rejected, before=after | only exchange release; next admission works, provider calls0 |
|128 malformed seed packets (short/oversized/bad kind/bad OPEN data) | ignored before=after | next valid OPEN works; bounded allocation, no fabricated auth success |
| Real synthetic Family auth rejection then valid peer | reject then authenticated success, before=after | same shared seed alive; no dedicated room on rejected peer |
| Listener/service shutdown and prior observer regressions | existing classification unchanged | parent cancellation, SIGTERM, normalstop/panic/writefailure, stale callback/retention |

Fault injection is at actual SeedManager/serveCarrier/Exchange boundary with
in-memory packet endpoints and synthetic credentials; no real Telemost room,
owner identity, remote reset packet or historical network replay. These tests
establish local behavior, not attribution of production failure.

Logs: `seed-matrix-before.log`, `targeted-race-expanded.log`,
`peer-contract-before-expanded.log`, `telemost-lifecycle-race.log`,
`before-after.json`, `operator-fixture-accepted.log`, `operator-fixtures.json`.
Targeted `-race` PASS including overlap/old cleanup, fatal subprocess tests,
mandatory negative-auth rejection, actual Telemost lifecycle/first-cause privacy.

**Whole suite is NOT green.** Final full race run fails the same six historical
negative-auth *diagnostic* assertions at auth_test.go:86; mandatory rejection
checks PASS. Baseline full run also observed existing
TestAuthenticatedBusyExchangeReportsChallengeReason failure (client
bootstrap_protocol_rejected); untouched, not used as attribution. No assertions
weakened. Final full race has no data-race warning. Earlier new fixture failures
(empty diagnostic tag; next peer before holder release; non-atomic fake Close
counter) were fixed, logs retained. Product behavior was not changed to satisfy them.

Reproduction commands/tool/fixtures are in bundle `REPRODUCE.md`. Synthetic fixture
issuance is local, uses no production keys/renewal. Loopback httptest tests ran
outside sandbox with approval; no external service access.

## Operator protocol correction

The original host started90s wait immediately after MANUAL_LISTENER_READY,
without any operator ACK. Saved timeout and later CLEANUP are valid, but the
human-visible request did not form an acknowledged active window. Exact delivery
time of READY is unavailable; do not claim a particular UI transport delay.

New offline state machine:
`PREPARED → ARMED → WAITING_FOR_OPERATOR_ACK → CONNECT_WINDOW_ACTIVE → CONNECT_OBSERVED → TEST_RUNNING → CLEANUP → CLOSED`.
900s/32 app contract unchanged; separate finite ACK120s/CONNECT90s budgets. Recheck
gate/generation/TTL/invocation/headroom after ACK before authorizing physical press.
Only fresh orchestrator connection accepted; late/pre-ACK events OUTSIDE_TEST_WINDOW,
never product PASS/FAIL. Once real physical action occurs, budget consumed even
outside acceptance window. Old generation/connection events ignored.

22 controlled-clock fixtures: on-time; missing ACK/CONNECT; early/late action;
expiry; changed gateway/headroom; crash; duplicate ACK; stale generation/connection/
timestamp; cancel/max32; stale checkpoint; fatal after CONNECT; collector loss; event-driven driver.
Every exit attempts cleanup once; valid fixture cache unchanged. SIGKILL/lost
cleanup cannot guarantee immediate disarm: mark UNCONFIRMED, original app900s TTL
remains final bound, no automatic rearm. Driver clearly emits TEST_WINDOW_CLOSED.

This does not physically disable the product button. That would require forbidden
UI/permission changes. It prevents false acceptance and makes the closed window
explicit. Live adapter attachment remains a fresh-preflight step, not a claim of
owner execution. No new telemetry framework/remote-control API created.

[Future A–L live runbook](../whitelist-warm-start-two-phase-runbook.md): fresh
gateway/chain/directory, exact client selection,84 verification, collectors,
ARM, explicit ACK, re-check, manual window, observed event, startup, egress, cleanup.
Invocation change before physical action aborts unconsumed; after action consumed.

## Closeout and one next operation

No phone/server mutation or new runtime snapshot. **Last known** owner12:23:09:
VPN OFF / app ON / ChatDeliveryService ON / gate CLEANED. Last saved gateway:
PID1255784 / invocation853bf7d3d15b4194b19629d546eaf92b / NRestarts1,
observer armed, loaded=next0ccaaf81…2667a; not asserted current now. Cache, keys,
history/publisher/AWG, receipts/rollback and dirty main checkout preserved.
Current chain/readiness not inferred from expired historical evidence.

`READY_FOR_CLEAN_RETRY=NO`; `HISTORICAL_ROOT_CAUSE=UNKNOWN`.
`CONNECT=0`, `RECONNECT=0`, `NATIVE_STARTUP=0`, `TUN=0`, `TELEMOST_LIVE=0`,
`PROVISIONING_REFRESH=0`, `GATE_ARM=0`, `GATEWAY_ACTIONS=0` in this task.
PUBLIC_RELEASE/FIELD/DEPLOYMENT=NOT_RUN.

**Exactly one next operation:** a separately authorized controlled
**observation-only deployment task** for the tested minimal delta (not a transport
fix), with its own fresh safeguards; no CONNECT as part of this closeout. A new
readiness decision belongs after that task, not to this offline report.
