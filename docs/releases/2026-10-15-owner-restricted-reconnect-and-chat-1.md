# OWNER-RESTRICTED-RECONNECT-AND-CHAT-1

**RESULT: FAIL — B completed restricted startup, then suffered a runtime/traffic
failure. No third CONNECT. Previous CLIENT_DEVICE_SMOKE=PASS remains unchanged.**

Input publication: 0b371946e63e1e3eea0dd80e71a772a0c5e735de. This is a new episode;
the old CONNECT2 remains NOT_RUN. Its [smoke report](2026-10-15-owner-cumulative-client-acceptance-1-resume.md)
and [receipt](evidence/2026-10-15-owner-cumulative-client-resume-attempt-1.json) are unchanged.
Supervisor PRODUCTION_ACCEPTANCE=FAIL and historical C1/I1 causal binding NOT_PROVEN.

The [sanitized A/B receipt](evidence/2026-10-15-owner-restricted-reconnect-and-chat-1.json)
contains exact export/journal hashes, source record indexes, distinct attempt aliases,
per-session counters and selected client/server timelines. Raw exports and journal
rows remain private. No new runtime observer, native poller, test or patch was added.

## Outcome and attempt matrix

| Boundary | A | B |
| --- | --- | --- |
| Intentional CONNECT, UTC | 19:40:52.738 | 19:52:42.526 |
| Restricted descriptor / dedicated readiness | BROKER_DESCRIPTOR_READY and SESSION_READY recorded19:41:22.638 | BROKER_DESCRIPTOR_READY and SESSION_READY recorded19:53:08.303; native GATEWAY_SESSION ESTABLISHED19:53:08.234 |
| Startup record | Archived startup object NOT_EXPORTED; readiness retained separately | Native attempt3, SUCCEEDED/STARTUP/NONE, complete=true,23791ms; started19:52:44.443 |
| Native/attach | Archived session native_state2 observed19:52:38.071; successful restricted connection | Successful attach follows the exact engine contract before CONNECTED; final native_state3. An earlier state2 scalar sample is NOT_RETAINED in this export |
| App CONNECTED | 19:41:22.778 | 19:53:08.446 |
| Owner VPN-bound HTTPS | Owner reports same expected NL egress | Owner reports external-IP check unsuccessful, then tunnel stopped; no successful B HTTPS response established |
| DNS | Matched archived session18 responses,0 errors; original packet-query count NOT_EXPORTED | Current ring6 DNS queries; same-session6 responses,0 errors before termination. This does not make B a successful traffic session |
| TCP/Mux |48 opens OK,0 open errors,5 protocol errors |4 opens OK,0 open errors,0 protocol errors; owner HTTPS still failed |
| Chat | Owner reports На связи; completed mailbox transaction and route not independently proven | NOT_MEASURED after failure |
| First local recorded failure | None in last archived snapshot; incomplete lifecycle tail |19:53:16.918 CARRIER/CLOSED/CARRIER_ERROR, close_source RECEIVE_QUEUE_FULL |
| Local cleanup / final OFF | cleanup_completed19:52:38.164; DISCONNECTED19:52:38.368 | cleanup_completed19:53:18.644; FAILED19:53:18.651; DISCONNECTED19:54:38.454 |

A readiness events sharing one observation timestamp are not exact timestamps of every
underlying native operation. Native B lifecycle timestamps and later snapshot receipt
are likewise distinguished. Current ring readiness READY / transport outcome SUCCESS
refer to startup: final ring DISCONNECTED and a native terminal are not contradictory.
The exact engine checks phase1, creates/replaces the TUN, requires successful attach,
then calls state.accept(true). This source-contract inference is not an independently
retained B phase2 sample. Neither system VPN presence nor an UI label alone is used
as proof of dedicated readiness.

## Reconnect timing and session correlation

- Local A OFF19:52:38.368 → B CONNECT19:52:42.526: **4.158seconds**.
- Fast reconnect was actually exercised without an intentional server-slot-free gate.
  Owner was instructed to wait only for local OFF/enabled CONNECT, not an agent reply.
- Same app PID26459 before A, during A, after B failure and after export. No intentional
  app restart/force-stop. Two distinct connection IDs, incident IDs and session tags
  match the corresponding full server tags privately; public aliases are SESSION_A/B.
- B started before recorded server A terminal19:52:47.584, yet obtained its own
  descriptor, Family TLS and dedicated session. This is not a self-blocking HELLO
  failure in the recorded B startup. No exact server holder release/grant receipt is
  present: CLEANUP/COMPLETED is not treated as broker-holder removal.
- A server terminal RELIABLE_RETRY_EXHAUSTED occurs after local A DISCONNECT/OFF.
  It is retained as POST_DISCONNECT_TERMINAL, not reassigned to B.
- B server session established19:53:08.000; its RELIABLE_RETRY_EXHAUSTED is recorded
 19:53:25.631, Family TLS error19:53:25.637 and gateway close19:53:25.639.
  These are later recorded server events, not the initial client startup failure.
- **OLD_CLEANUP_DOES_NOT_CLOSE_NEW_SESSION=NOT_PROVEN.** Distinct tags and B READY prove
  separation and startup progress, not why B subsequently lost its receive path.

Cross-host timestamps are recorded clocks, not a sub-millisecond synchronization or
causality proof. The4.158s interval uses one client clock. New sequence A CONNECT→final
local OFF lasted825.716s (13m45.716s), within1080s. No repeated240s stability wait was
required. Final export and offline analysis occurred after VPN OFF; no device test was
continued to fill missing chat observations or obtain a more convenient retry.

## First failure, preserved diagnostic semantics

The earliest B client first_failure and first_close are the same lifecycle record:

```json
{"session_alias":"SESSION_B","sequence":28,"utc":"2026-10-15T19:53:16.918Z","stage":"CARRIER","state":"CLOSED","reason":"CARRIER_ERROR","close_source":"RECEIVE_QUEUE_FULL"}
```

This is8.472s after app CONNECTED, not bootstrap failure. Retained cumulative
telemost/session.go deliverObserved records this bounded source on its nonblocking
receive-queue enqueue default branch. It identifies the local recorded queue-overflow
boundary, **not the cause of queue saturation** (consumer stall, burst or lifecycle
interaction are not established here). No source change or new experiment follows.

Client terminal IO_CLOSED/carrier_closed is stamped19:53:16.927, captured by a native
snapshot19:53:18.488 and observed by Java19:53:18.492. The orchestrator records
CARRIER_ERROR19:53:18.505 and restoration_failed19:53:18.651. Later CANCELLED/OFF at
19:54:38 does not overwrite or explain that initial failure. Server B diagnostic says
IO_CLOSED/recovery_exhausted,71 retransmissions,6 DNS responses/0 errors,5 TCP opens/0
errors,0 protocol errors; these are **server counters**, not substitutes for client4
opens/6 retransmissions. Neither side maps the failed owner IP request to a specific
stream. No data-corruption or harmlessness claim is made from aggregate counters.

Startup remains SUCCEEDED/STARTUP/NONE after cleanup/export. The startup-failure-only
observation/context/local_stop fields are not applicable to a successful startup and
are absent here; no fake startup failure is synthesized to exercise them. The preserved
runtime lifecycle supplies first_failure/close_source. This verifies normal export of
this actual failure, not every diagnostic-fidelity scenario or automatic recovery.

## Chat coverage and remaining uncertainty

CHAT_FIRST_PRECONDITION=NOT_PROVEN. Before A and on A, owner reports На связи.
ChatDeliveryService remains present, but this does not identify a live independent
restricted holder, a completed mailbox operation or borrowing through the VPN.
CHAT_WHILE_VPN_A=OWNER_REPORTED_ON_LINE_UI; CHAT_WHILE_VPN_B=NOT_MEASURED;
CHAT_AFTER_DISCONNECT=NOT_MEASURED. BORROWING and HANDOFF_ON_DEVICE=NOT_PROVEN.
No messages, contacts, vault or unrelated app data were read. No messages were sent
to third parties. A/B tags are separated; the role of stale chat handles in B failure
is not proven or ruled out. A successful local handoff implementation and previous
smoke remain evidence of their own scope, not a full lifecycle PASS.

## Normal export, completeness and privacy

One owner-provided normal share JSON was copied privately before analysis:
SHA2563e830cfe8850aa4129da0c41e116ddba23a9aedbf40123d67a5dd54de5a49104,
156569bytes, received2026-10-15T19:59:32.702305Z. Export receipt time is not event time.
The expected app/version schema is present. restricted_history[0] is the prior smoke,
[1] is A; current restricted_session/startup/counters bind to B. Current ring contains
exactly two new DISCONNECTED→CONNECTING transitions. All retained new retry_count
values are0; one restoration_failed is recorded, no further new CONNECT transition.
This is bounded observation, not a claim that ordinary protocol retries were zero.

The separate FAILED incident is an older attempt with events14Oct18:36:36.664 through
15Oct13:23:42.694UTC and different IDs. It is excluded, not labeled as the B incident.
Normal export includes the new failed session in ring; it does not refresh every
persisted historical incident. No new native stats poll was performed to obtain data.

| Coverage limitation | A | B |
| --- | --- | --- |
| Client lifecycle retained trace / source trace_dropped |32 /372 |43 /0 |
| delivery_dropped / archive_dropped |329 /160 |0 /not applicable |
| Boundary tail retained / dropped |64 /28993 |64 /1225 |
| Projection/export drop values |Recorded0; does not undo source/archive losses |Recorded0; boundary tail still incomplete |

The A-ready server window contains109 JSON rows. The post-B window reaches its320-row
cap; two MESSAGE JSON values are unparseable and excluded without guessing. Windows
are attributed to the actual invocation, deduplicated by session/sequence/timestamp,
and are not a complete journal. Their raw hashes are in the safe receipt. Raw JSON,
server rows, source-origin path and real client/session/support IDs remain private.
Normal Share cache rotation is authorized; exact old-cache deletion count was not
measured. Primary diagnostics/app data were not cleared. NORMAL_EXPORT=PASS within
these bounded schema/retention limits.

## Residual observations from the previous smoke

Scope is only the already saved export/journal and bound sources. No new historical
journal query, private JSONL search, native poll or diagnostic patch was performed.
Installed cumulative source inventory is
a4d489079e3da0df7fdd01b7977962b20ddbbf8605fbf682a349703a88b916d5;
baseline binding is the preserved471d1d62e1385a9ffc5ff6a16a5a7e9fe043fae2
snapshot described in the publication index. The tcpforward/mux.go and mux_dns.go
files are byte-identical between these two retained source slices.

| Exported counter | Actual increment branches, not a causal diagnosis |
| --- | --- |
| protocol_errors5 | Mux TCP: server receives a reused/non-increasing stream ID; frame for an absent stream; invalid frame/state/flow-control/FIN/CLOSE transition. Mux DNS: server receives a reused/non-increasing query ID or an invalid server-side frame kind; client receives a frame for an absent/already-completed DNS call. |
| tcp_open_errors1 | Client Mux accepts a valid openError for a not-yet-opened stream. Other Mux branches on the server count stream/job-capacity rejection or failed forwarding/dial (unknown error mapped to connect_failed). |

The exported fields come from sessiondiag.Capture with MuxStats. The separate
single-stream gateway Stats.OpenErrors counter is not substituted for them. Relevant
published baseline source: [mux.go](../../research/supervisor-20261015/baseline/carrier/tcpforward/mux.go),
[mux_dns.go](../../research/supervisor-20261015/baseline/carrier/tcpforward/mux_dns.go),
[report.go](../../research/supervisor-20261015/baseline/carrier/sessiondiag/report.go).
No saved per-stream/query failure code or timestamp identifies which branch produced
the aggregate5/1. The recent retained boundary tail does not attribute those increments.
Thus **UNATTRIBUTED_COUNTERS**, not proven corruption, owner HTTPS failure or harmlessness.

| Previous episode boundary | UTC15Oct2026 |
| --- | --- |
| Client DISCONNECT transition | 18:54:50.950 |
| Last native/session snapshot, terminal NONE | 18:54:50.998 |
| Local cleanup_completed, same session tag | 18:54:51.114 |
| VPN_RELEASED / DISCONNECTED | 18:54:51.238 /18:54:51.301 |
| Same-session server RELIABLE_RETRY_EXHAUSTED | 18:55:00.225 |
| Server FAMILY_TLS_ERROR / GATEWAY_CLOSE | 18:55:00.235 /18:55:00.238 |
| Available server CLEANUP/COMPLETED observations | 18:55:00.234–18:55:00.238 |

This is **POST_DISCONNECT_TERMINAL**, not a startup failure. Temporal order is retained;
the exact causal mechanism is not inferred. Saved windows contain no explicit broker
ownership release/grant receipt. CLEANUP/COMPLETED and dedicated_resources_closed do
not prove holder removal. No new broad query was used to fill that gap.

Prior client trace retained192 entries with trace_dropped472 and delivery_dropped392;
boundary tail retained64 with dropped40913. Projection drop counters0 do not make the
original trace complete. Server windows were bounded, overlapping and deduplicated;
two unparseable JSON MESSAGE values and an earlier host-quota partial save remain
private/excluded. Cumulative counters do not date their increments. No specifically
proven dangerous regression/session mixing/security violation emerged from this narrow
review; these unattributed aggregates alone do not block the new lifecycle test.

## Fresh prerequisites and unchanged artifacts

Read-only preflight19:30:05–19:30:16UTC; narrow seed/writer query and review completed
19:33:49UTC. No old expiry was accepted without fresh collection.

| Item | Fresh result |
| --- | --- |
| Installed APK SHA256 | 3c733d2fc3a0ec377143b668244a4c7d6619ff24abe024da4ee9bfe31d140513 |
| Embedded native binding | 2a974350c168913ca8a217d3fc73f452fdd709c3619d0c690abd5d884c54b88c; fresh installed APK hash equals previously pulled/verified exact bytes, no new rebuild/extraction |
| Owner | Authorized saved ADB selector, package com.familyconnect.app.friends, UID10283, versionCode84, app PID26459, FriendsActivity focused, VPN OFF |
| Baseline loaded SHA256 | 21f0a0fdc27b50c00ea922f0b716516e2422aedf1b3797369718f7d00070509a |
| Gateway | PID3903125, invocation c11ce23c7d124f2790fa9f35f13f5693, active/running, listener18444; loaded/next argv agree and have no acceptance flag |
| Served chain / seed | Strict chain and expected leaf PASS; same-invocation bootstrap_seed_ready record, running process; no new provider probe |
| Current directory | RU/NL agree on d4fa4a8b785e2d677006c02c5f2cca66e220405c4f44dd726d084d690db4e280; delegation signature/directory binding valid |
| Maintenance/writers | No pending node owner; coordinator COMMITTED; RU HTTP active; current4h timer enabled/active, service inactive/success; scoped process query contains only its own query processes |
| Leaf / CRL bound | 2026-10-15 21:37:06UTC |
| Directory expiry | 2026-10-15 21:37:17.752732812UTC |
| Conservative process lifetime boundary | 2026-10-15 21:37:17.622UTC |
| Authority/grants expiry | 2026-10-16 17:34:58UTC |

The remaining window supports the agreed18-minute sequence at check, not indefinitely.
Preparation occurs before CONNECT. Existing current4h scheduling remains untouched;
natural changes will be recorded rather than administratively reverted. No installation,
app start/restart, signer operation, manual credential renewal or server mutation.

## Final state, identities and actions

| Item | Final observation / count |
| --- | --- |
| Installed APK SHA256 |3c733d2fc3a0ec377143b668244a4c7d6619ff24abe024da4ee9bfe31d140513 |
| Native SHA256 |2a974350c168913ca8a217d3fc73f452fdd709c3619d0c690abd5d884c54b88c |
| Signer SHA256 |67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a |
| Identity basis |Fresh preflight APK equals previously pulled verified bytes/native; package/UID10283 preserved; no install in this task |
| Device state |VPN OFF19:56:04 and20:06:39UTC readbacks, same app PID26459; final ring DISCONNECTED/vpn_capture_open=false |
| Gateway |Same baseline/PID3903125/invocation c11ce23c7d124f2790fa9f35f13f5693, active/running/NRestarts0 at19:56:04; no gateway deployment, restart, config or manual credential action |
| Intentional CONNECT |2; third0 |
| Local DISCONNECT transitions |2. A follows requested normal owner action; B final CANCELLED origin is not independently identified as an owner button press |
| Runtime terminal/restoration_failed |1 new B runtime failure; ordinary app/protocol retries not disabled |
| Normal support export |1; normal cache/URI rotation allowed, exact mutations not enumerated |
| APK build/sign/install/downgrade/rollback |0 |
| App force-stop/restart, clear data/cache, enrollment |0 |
| Extra native polls/helper/instrumentation/fault injection |0 |
| Server administrative / manual credential mutations |0; ordinary app/provider/provisioning/ACK/lease activity not asserted zero |

The cumulative APK remains installed privately. No speculative rollback/rebuild is
permitted in this task. Existing baseline and scheduling were not administratively
changed. Selected UID crash/linkage log checks found0 new matching lines, not a claim
of complete Android logs. No full post-test PKI/current4h audit was repeated; no
invocation change was observed in the bounded episode.

## Conclusion and publication scope

RECONNECT_WITHOUT_APP_RESTART and FAST_RECONNECT_BOUNDARY_EXERCISED are exercised,
but the runtime/traffic requirement **fails on B**. SESSION_A_B_BINDING is proven;
DNS activity before failure is observed separately, not used to override failed HTTPS.
Previous CLIENT_DEVICE_SMOKE=PASS is preserved; this new lifecycle result is FAIL.
HANDOFF_ON_DEVICE stays NOT_PROVEN; full client/supervisor acceptance is not promoted.
Historical C1/I1 root cause is not established by this new episode.

Remaining exact question is why the B local receive queue reached RECEIVE_QUEUE_FULL
after successful startup. This task ends with evidence preservation, not a product
patch, extra CONNECT, reinstall or server intervention. Only this report, its safe
receipt, STATUS/PLAN and publication index change. Prior smoke documents, frozen
sources/binaries, workflows, main and original dirty worktree remain unchanged.
