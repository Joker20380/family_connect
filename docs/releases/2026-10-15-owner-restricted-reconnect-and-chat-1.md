# OWNER-RESTRICTED-RECONNECT-AND-CHAT-1

**RESULT: WAITING_FOR_OWNER_ACTION — fresh prerequisites ready; new CONNECT A/B
have not been performed. Next: ordinary pre-VPN chat synchronization.**

This is a new lifecycle episode, not completion of the old CONNECT2. Input review:
0b371946e63e1e3eea0dd80e71a772a0c5e735de. The
[previous smoke report](2026-10-15-owner-cumulative-client-acceptance-1-resume.md)
and its [receipt](evidence/2026-10-15-owner-cumulative-client-resume-attempt-1.json)
remain unchanged: CLIENT_DEVICE_SMOKE=PASS for one connection; old CONNECT2=NOT_RUN.
Historical supervisor acceptance remains FAIL; C1/I1 causal binding NOT_PROVEN.

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

## Prepared collection and owner sequence

The existing bounded collector is copied into a separate private task capsule and
parameterized with this fresh invocation and start19:30:04UTC, at most320 journal rows
per window, explicit new intentional-CONNECT count and UID10283 error logs. It reads
system metadata and saved gateway events only. There is no additional native stats
reader, Android observer/helper, instrumentation, screenshot or protected UI extraction.
If invocation changes, state readback exposes the mismatch rather than attributing
old-invocation records to the new runtime.

Next owner action: open the normal chat list with VPN OFF, allow ordinary automatic
sync and report only the status text, not contacts or message contents. If a registration
screen appears, stop without registering. Fresh route/service labels alone do not prove
an independent restricted holder. Lack of that proof limits handoff, not reconnect.

Then at most two intentional CONNECT actions, separately labeled A/B. A must reach
restricted READY/CONNECTED, successful VPN-bound HTTPS and ordinary chat operation.
After A succeeds: ordinary DISCONNECT; wait only for local OFF and the enabled CONNECT
button, then B without an intentional server-holder-release wait or app restart. No
CONNECT while local DISCONNECT is ongoing; no hidden retry. B must have distinct
connection/attempt/session binding, traffic and no interference from A cleanup. After
B: ordinary DISCONNECT and available chat sync, then one normal support export. Stop
on first startup/traffic failure without B. No additional240second stability wait.

The18-minute limit begins at actual first CONNECT, includes final cleanup, and is not
extended for diagnostics. Record local-OFF→B interval; a large operator pause means
fast reconnect NOT_EXERCISED, with no third attempt to improve timing. Do not wait for
server slot=free before B. Final export will be interpreted according to its real
archived-session schema, without mixing old counters/startup or assuming missing fields.

## Current matrix and counts

CONNECT_A / CONNECT_B = NOT_RUN / NOT_RUN. RECONNECT_WITHOUT_APP_RESTART,
FAST_RECONNECT_BOUNDARY_EXERCISED, SESSION_A_B_BINDING and
OLD_CLEANUP_DOES_NOT_CLOSE_NEW_SESSION = NOT_TESTED.
HTTPS/DNS per new session = NOT_RUN. CHAT_FIRST_PRECONDITION = NOT_PROVEN.
CHAT_WHILE_VPN / CHAT_AFTER_DISCONNECT = NOT_MEASURED; BORROWING and
HANDOFF_ON_DEVICE = NOT_PROVEN. NORMAL_EXPORT = NOT_RUN for this new episode.
FIRST_FAILURE = none observed in a new connection, because none started.

New-episode intentional CONNECT0; DISCONNECT0; export0; install/rebuild/resign/rollback0;
app force-stop/restart0; extra native polls0; server administrative/credential actions0;
fault triggers0. Normal background app/provider/provisioning/lease activity is not
asserted zero. Final observed device state at this checkpoint is VPN OFF, original
cumulative package and process preserved. Await owner chat observation before A.

Only safe review documents are published; raw preflight/journal data and upcoming
exports remain in the separate private capsule. Previous smoke report/receipt and
frozen/product sources are unchanged. No new acceptance result is claimed yet.
