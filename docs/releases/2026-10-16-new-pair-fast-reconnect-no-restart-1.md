# NEW-PAIR-FAST-RECONNECT-NO-RESTART-1

## Final result —16Oct2026, PASS_BOUNDED

**NEW_PAIR_FAST_RECONNECT=PASS_BOUNDED.** Two new intentional restricted CONNECTs,
ordinary DISCONNECTs, **OFF_A→CONNECT_B=3431ms** on the same client clock, same app
PID12008 and gateway PID356992/invocation INV_FAST throughout. Owner explicitly
confirms successful VPN-bound IP checks showing NL on A, B initially and B after
four minutes. These are **owner-reported UI results**, not saved HTTP response receipts.
B remains app-CONNECTED270.203s before DISCONNECT, with native successful startup
270.421s before DISCONNECT. Total A CONNECT→final OFF334.941s, within18min.

[Safe selected evidence](evidence/2026-10-16-new-pair-fast-reconnect-no-restart-1.json).
No install/sign/rebuild, app/gateway restart, configuration change, admission capture,
new native reader, manual renewal/recovery or rollback. This is one bounded lifecycle
episode, not full device/supervisor acceptance, a release or a historical-cause finding.

### Identities and continuity

Installed/final APK SHA256:
`8e5579f04de91e4ec00e3e79271dbb0f380b1ed91945ff89016aa50d274a8845`.
Native SHA256:
`be70a66ccc2bcbf0478915fd414c32de3bedb2a0ae0c3222a53e65eebd0a92b2`.
Retained source inventory, not a Git commit or a new inventory:
`b36c4a21ee6cf04acb192a0e6d140fa565b3e5ae75f6fc8d028d029c3152781d`.
Package `com.familyconnect.app.friends`, code84/name
`0.1.18-research84-provisioning-seam`, actual UID10283; signer
`67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
Final12:14:19UTC on-device APK hash/UID/PID readback matches preparation. Native/signer
identity follows exact APK equality to the retained verified artifact, with its embedded
native hash independently rechecked locally; no private identity/database inspection.

Gateway loaded executable remains
`a537257162348afc35b1ebc08755d8c5dc1cd90e74c49e3987fb3eb81885e61f`.
Pre-A, all bounded server windows and final readback retain PID356992/INV_FAST;
all362 distinct journal records have that PID/invocation. Ordinary argv, no admission
capture flag. App snapshots before A, during B and after OFF retain PID12008, no
recent matching scoped AndroidRuntime/linker/libc errors. Same-process ring history
also retains the earlier observed trial separately. No observed process interruption.
This is bounded observation, not a continuously instrumented process watchdog.

### A/B timeline and exact correlation

All times UTC16Oct; client milliseconds are the single clock for OFF→CONNECT and
episode durations. Server timestamps below are server observations, not client timings.

| Boundary | A | B |
|---|---|---|
| Client CONNECT |12:02:46.558|12:03:22.428|
| Server dedicated READY / descriptor issued, exact dedicated tag |12:02:59.753|12:03:38.789|
| Server gateway session established |12:03:10.081|12:03:50.319|
| Native session established / successful startup |12:03:10.386 GATEWAY_SESSION ESTABLISHED|12:03:50.728 startup SUCCEEDED|
| App SESSION_READY |12:03:10.468|12:03:50.802|
| App restricted CONNECTED |12:03:10.619|12:03:50.946|
| Owner DISCONNECT |12:03:18.705|12:08:21.149|
| Local cleanup notification |12:03:18.862|12:08:21.323|
| VPN_RELEASED |12:03:18.953|12:08:21.432|
| Local OFF |12:03:18.997|12:08:21.499|
| Later server terminal |12:03:28.769|12:08:31.202|

CONN_A/INC_A/SESSION_A and CONN_B/INC_B/SESSION_B are distinct. Client archived A and
current B each have VALID correlation/native_state2, matching lifecycle tag and exact
server dedicated tag. Server union retains contiguous trace sequences1–63 for A and
1–272 for B, including dedicated readiness, authenticated session and cleanup boundaries.
Native/app readiness is established by these native session records, SESSION_READY,
VPN capture and restricted CONNECTED boundaries—not by a UI label alone. No AWG/TCP
fallback counts as this success; all new app retry_count values are0.

B startup attempt3 starts12:03:24.532, completes in26196ms with SUCCEEDED/NONE. Its
single early REQ_B is family_authenticated=true, dropped0, separate from SESSION_B;
its directory fingerprint exactly matches the fresh NL/RU runtime-bound directory.
A's archived session retains lifecycle evidence but **not its startup scalar/attempt
number, directory fingerprint or early bootstrap tag**. These are NOT_EXPORTED, not
invented attempt2/tag values or a startup failure. Fresh A bootstrap/lifecycle and
connection boundaries are separate from B and the prior trial.

No new ownership capture exists. REQ_B alone does not prove server wait/grant/HELLO
send; no nearest-time challenge attribution is made. The105s journal sample retained
A creation/start evidence before B; the extra early window saved A READY/ACTIVE/terminal
and the next bootstrap-open at12:03:31, **after B's client CONNECT**, not before it.
Exact A correlation remains available without another native reader/export. The
archive's missing early A tag is an explicit limitation of this collection arrangement.

B was requested3431ms after local OFF, before A's later server terminal; no agent
reply, holder-free gate or manual release was inserted. Local fast reconnect therefore
does not demonstrate a same-identity ACTIVE admission wait: B's observed server
bootstrap-open/auth are after that terminal, and ownership removal itself is not captured.

### Traffic, DNS and240s scope

Owner responded that all went well/IP NL, then explicitly confirmed **all three**
requested checks (A, B immediately, B after four minutes) showed NL. No request/body/IP
address receipt or exact check timestamp is exported. The after240s check is owner-
reported, supported by B's270.203s connected interval and ongoing native/server events;
it is not inferred solely from CONNECTED, byte counters or elapsed time. No host curl
or adb-shell traffic is used as owner TUN proof.

| Client session counters | A | B |
|---|---:|---:|
| DNS responses / errors |0 /0|12 /0|
| TCP open success / errors |4 /0|26 /0|
| Protocol errors |0|0|
| Sent / received bytes |3215 /5648|34860 /103589|
| Sent / received frames |95 /83|1125 /1126|
| Retransmissions / recovery_timeouts |8 /8|16 /16|

DNS_A: no fresh DNS transaction is demonstrated; recorded0/0 is not proof of tested
DNS success. DNS_B:12 responses/0 errors in the exact B native and server session.
The aggregate app ring counters are not substituted for per-session counters.
Retransmission/recovery counters are nonzero; no claim of lossless or byte-exact traffic.
B_STABILITY_240S=PASS_BOUNDED with owner-reported initial and after240s HTTPS/IP,
not a multi-hour soak, statistical guarantee, whitelist field test or burst matrix.

### First failure, late terminals and environment

No unexpected client startup/traffic failure is observed or owner-reported in A/B.
Both final native session records have terminal NONE; B startup remains SUCCEEDED
after cleanup. The cached incident is the old historical HELLO_RECEIVE/IO_DEADLINE
failure, not a failure in this episode; the earlier successful observed session is a
separate history entry, not A. No RECEIVE_QUEUE_FULL is observed in the retained data.

Exact server sessions A/B later report IO_CLOSED / reliable recovery_exhausted,
**9772ms /9703ms after their respective client OFF**, followed by server cleanup.
These are not substituted for a primary startup failure or a failed HTTPS check,
and are not declared universally harmless. For B the terminal JSON is split by
journald at49152 bytes; its adjacent13613-byte continuation shares stream/PID/invocation,
has consecutive journal sequence, and concatenates to valid JSON with exact SESSION_B.
No missing bytes were invented; originals and reconstruction provenance remain private.

No observed gateway restart/current4h material change during the episode. The pre-A
MAINTENANCE_REQUIRED warning is separate from active outage/expiry (details below).
Scheduler remains running; no future renewal was assumed or driven manually.
Known nominal renewal/rotation bounds were outside this episode; no arbitrary
multi-hour gate was imposed and no maintenance warning was silently erased.

### Export, retention and chat coverage

One normal owner support export, received12:10:58.937UTC,141437 bytes, SHA256
`d7d0ed64f32ccd26821171eebd621501c8ff7f330a373ec879ae3536c737db50`.
Receipt/copy time is not event time. Original and analysis copy, device metadata and
raw journal windows are private and hashed; no raw JSON/JSONL, real identifiers,
room URLs, APKs or keys are published.

| Surface | Retained | Exported drops / limitations |
|---|---|---|
| App ring / cached incident |73 /17 events|Top-level drop counters NOT_EXPORTED; incident historical|
| Session history |2 entries|Earlier observed trial and A; not two new failures|
| Client A lifecycle |27 trace, seq1–27|trace/export/projection/archive/delivery/delivery_projection all0|
| Client A boundaries |64|dropped773; projection0; native evidence_dropped0|
| Client B lifecycle |192 trace, seq45–236|trace44, export0, projection0, delivery127, delivery_projection0|
| Client B boundaries |64|dropped9955; projection0; native evidence_dropped0|
| Current B startup |1 early exchange|bootstrap_exchanges_dropped0; A startup scalar/tag not archived|
| Older observed-trial archive |32 trace, seq12–43;64 boundaries|archive11, delivery6, trace/export/projection0; boundary2303; separate historical scope|
| Server A terminal snapshot |56 trace;64 boundaries|trace0, export0, delivery2, boundary995; evidence0|
| Server B terminal snapshot |192 trace;64 boundaries|trace73, export0, delivery133, boundary10158; evidence0; split-message reconstruction above|
| Existing journal collectors |13 windows≤320 rows;362-row exact-cursor union|2 windows hit row cap; no numeric journal drop counter; per-session trace union contiguous, not global completeness|

Missing server projection/drop fields are NOT_EXPORTED, not zeros. A/B startup success
does not require failure-only fields. Native counters reflect the retained snapshots,
not guaranteed continuous accounting of every user byte. Ordinary DISCONNECT/CANCELLED
events do not overwrite successful startup. No additional native-stats reader was used.

CHAT_UI_ONLINE / CHAT_OPERATION_COMPLETED / BORROWING / HANDOFF_ON_DEVICE:
**NOT_PROVEN separately**. ChatDeliveryService exists before/after, but there is no
operation-specific owner confirmation/export receipt or independent restricted chat
premise. No chat content read, messages sent, DIRECT blocking or artificial holder.
Bootstrap handoff is not chat→VPN handoff; this missing optional coverage does not
negate the successful VPN reconnect criteria.

### Final requested result fields

| Field | Result |
|---|---|
| RESULT |NEW_PAIR_FAST_RECONNECT=PASS_BOUNDED|
| INSTALLED_APK_NATIVE_UNCHANGED |PASS; exact identities above, diagnostic APK retained privately|
| GATEWAY_EXECUTABLE_AND_INVOCATION |a5372571…885e61f / PID356992 / INV_FAST unchanged; ordinary argv|
| CONNECT_A / CONNECT_B |restricted SUCCESS / SUCCESS; distinct connections and sessions|
| OFF_A_TO_CONNECT_B_MS / FAST_RECONNECT_BOUNDARY |3431 / EXERCISED≤5000|
| APP_AND_GATEWAY_PROCESS_CONTINUITY |PASS_BOUNDED; app12008/gateway356992/INV_FAST|
| DEDICATED_NATIVE_APP_READY_A_B |PASS via matched dedicated/native/app boundaries|
| SESSION_A_B_CORRELATION |Exact dedicated tags; A early/scalar absent; B REQ_B retained, ownership capture off|
| HTTPS_A / HTTPS_B_INITIAL / HTTPS_B_AFTER_240S |SUCCESS_NL / SUCCESS_NL / SUCCESS_NL, owner-reported UI|
| DNS_A / DNS_B |NOT_DIRECTLY_EXERCISED (0/0) /12 responses,0 errors|
| B_STABILITY_240S |PASS_BOUNDED;270.203s CONNECTED before DISCONNECT, after240s check owner-confirmed|
| CHAT_OPERATION / BORROWING / HANDOFF |NOT_PROVEN / NOT_PROVEN / NOT_PROVEN|
| FIRST_FAILURE / ENVIRONMENT_INTERRUPTION |No unexpected client failure observed / none observed; late server terminals retained|
| EXPORT_AND_RETENTION_LIMITS |One normal export; exact per-surface limits above|
| FINAL_VPN_APP_GATEWAY_STATE |VPN OFF; same installed app/PID; gateway active, same executable/invocation/ordinary argv|
| ACTION_COUNTS |CONNECT2, DISCONNECT2, export1, app retries observed0; all install/sign/build/rollback/restart/re-arm/manual recovery/config changes0|
| REMOTE_HEAD_SHA / REPORT_URL |Review commit and immutable report link supplied after push/readback in completion; no main/workflow/catalog change|

HISTORICAL_A_CAUSE=NOT_PROVEN; HISTORICAL_B_CAUSAL_BINDING=NOT_PROVEN;
LIVE_BURST_ENVELOPE=NOT_DIRECTLY_EXERCISED; HANDOFF_ON_DEVICE=NOT_PROVEN;
SUPERVISOR_ACCEPTANCE=NOT_PROMOTED. Previous smoke PASS/reconnect FAIL and historical
A/B conclusions remain unchanged. This success neither makes all server suites green
nor authorizes public release. Preparatory checkpoints below are superseded only for
this new episode; earlier task reports are not edited.

## Active checkpoint —16Oct2026,12:01UTC

**RESULT=IN_PROGRESS / awaiting owner timeline and export.** Owner freshly confirms
availability in this continuation. Full uninterrupted A→OFF→B≤5s→240s→OFF/export
instructions were issued after readiness and arming the existing bounded collector.
First CONNECT time and actual action count are not inferred from that instruction
or collector start. No result from the earlier single trial is reused as A or B.

Fresh read-only readiness11:53–12:00UTC confirms loaded executable
`a537257162348afc35b1ebc08755d8c5dc1cd90e74c49e3987fb3eb81885e61f`,
gateway PID356992/invocation alias INV_FAST, ordinary argv/no admission capture,
listener/strict served TLS, current-invocation seed-ready record and equal runtime-bound
NL/RU directory. A first last30min seed query had no entry because this process started
11:14:33; one bounded current-invocation startup read finds its seed-ready record.
Directory issuance11:14:35, expiry15:14:33; leaf/CRL expiry15:14:20;
authority/delegation expiry17:34:58UTC. No pending owner/writer or nonterminal recovery;
last transaction COMMITTED. Actual restricted session/holder count remains UNKNOWN.

The latest scheduled evaluation reported MAINTENANCE_REQUIRED /
MAINTENANCE_BLOCKED_BY_SESSION_UNCERTAINTY, exit75, mutations0. Its existing six-hour
authority/grant threshold is a maintenance warning, not expired material or active
quiescence. Selected existing policy confirms non-leaf/CRL maintenance is gated;
no approval/override/repair is performed. The next nominal leaf/CRL threshold is
13:44:20UTC, seed rotation14:14:33, process duration bound15:14:33; no known disruptive
scheduled boundary falls within this18min episode. Natural unexpected changes must
still be detected/reported, not excluded by this readiness snapshot.

The read-only observer arms12:01:13.658UTC: at most520s,11 journal windows (≤320 rows
each),5 scoped device snapshots, no native-stats reads. Fresh pre-arm state confirms
the same gateway invocation/directory and no active maintenance; device checks confirm
APK equality/UID10283/PID12008/VPN OFF. The observer does not issue CONNECT or taps.
Its duration is not the owner's18min budget and is not a completed stability result.
Private active checkpoint retains the observer session and precise receipt paths.
Support export, traffic results, actual OFF→B timing and final OFF remain pending.

## Preparation checkpoint —16Oct2026,11:48UTC

**RESULT=WAITING_FOR_OWNER_ACTION.** This is a new, not-yet-started lifecycle
episode, based on review `40c5d1f050fc88f0a1f4c287d115d8753f3d98b8`.
The earlier owner-ready messages and successful single observed CONNECT belong to
the [completed observed trial](2026-10-16-bootstrap-pre-hello-observed-trial-1.md),
not permission to assume current availability. No new CONNECT has been requested.

Short scoped device reads at11:47:48–11:48:49UTC confirm:

| Identity/state | Observation |
|---|---|
| Installed APK SHA256 | `8e5579f04de91e4ec00e3e79271dbb0f380b1ed91945ff89016aa50d274a8845` |
| Native SHA256 | `be70a66ccc2bcbf0478915fd414c32de3bedb2a0ae0c3222a53e65eebd0a92b2` |
| Signer SHA256 | `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a` |
| Package/version | `com.familyconnect.app.friends`, code84, `0.1.18-research84-provisioning-seam` |
| Actual UID/PID | 10283 /12008 |
| VPN / foreground | OFF / ordinary Friends activity focused |
| Bounded app error observation | No recent matching AndroidRuntime/linker/libc error lines; not an exhaustive crash/ANR audit |

Native/signer binding uses exact on-device APK hash equality to the retained,
previously signature-verified installed APK; its local embedded native hash was
rechecked. No signing, installation, launch, restart or private identity/database
read occurred. Data preservation here means no modifying action, not a database audit.
Source inventory `b36c4a21ee6cf04acb192a0e6d140fa565b3e5ae75f6fc8d028d029c3152781d`
is the retained build identity, not a fresh inventory or Git commit.

## Remaining pre-A gate and prepared collection

The existing bounded journal/device collectors have task-local path/UID bindings;
no native reader, instrumentation or device/server helper was added. They are not
armed for an owner sequence. The prepared owner instructions cover A IP success,
normal OFF, immediate B without waiting for an agent reply, B initial IP, a repeat
after240s, final OFF and one normal export. Target OFF_A→CONNECT_B is≤5000ms;
overall A CONNECT→final OFF is≤1080s. First A startup/traffic failure skips B.

After fresh owner confirmation, perform the short pre-A server/device readiness
check and bind actual PID/invocation before arming the existing bounded windows.
Expected gateway SHA256 is
`a537257162348afc35b1ebc08755d8c5dc1cd90e74c49e3987fb3eb81885e61f`;
**no fresh gateway readiness or invocation is claimed at this checkpoint**.
Check strict served TLS/seed/runtime-bound RU directory, actual material and runtime
deadlines, pending maintenance/recovery and upcoming scheduled operations against
the bounded episode. Do not assume future renewal or impose a multi-hour gate.
The previous admission capture remains closed; no re-arm/restart is permitted.
This limits attribution of a possible new HELLO wait, but does not block lifecycle testing.

## Result fields at this checkpoint

| Field | Status |
|---|---|
| INSTALLED_APK_NATIVE_UNCHANGED | CONFIRMED at preparation readback |
| GATEWAY_EXECUTABLE_AND_INVOCATION | FRESH_PRE_A_CHECK_PENDING |
| CONNECT_A / CONNECT_B | NOT_STARTED / NOT_STARTED |
| OFF_A_TO_CONNECT_B_MS / FAST_RECONNECT_BOUNDARY | NOT_MEASURED / NOT_EXERCISED |
| APP_AND_GATEWAY_PROCESS_CONTINUITY | NOT_TESTED; app preparation PID12008 only |
| DEDICATED_NATIVE_APP_READY_A_B / SESSION_A_B_CORRELATION | NOT_TESTED |
| HTTPS_A / HTTPS_B_INITIAL / HTTPS_B_AFTER_240S | NOT_TESTED |
| DNS_A / DNS_B / B_STABILITY_240S | NOT_TESTED |
| CHAT_OPERATION / BORROWING / HANDOFF | NOT_TESTED / NOT_PROVEN / NOT_PROVEN |
| FIRST_FAILURE / ENVIRONMENT_INTERRUPTION | NO_EPISODE_STARTED / NOT_OBSERVED |
| EXPORT_AND_RETENTION_LIMITS | No new export; old export is not new-episode evidence |
| FINAL_VPN_APP_GATEWAY_STATE | Preparation VPN OFF/app PID12008; gateway not touched or freshly assessed |
| ACTION_COUNTS | CONNECT0, DISCONNECT0, export0, install/sign/build/rollback0, app launch/restart0, SSH0, gateway mutations0, native polls0 |
| REMOTE_HEAD_SHA / REPORT_URL | Publication pending; input review SHA above |

`NEW_PAIR_FAST_RECONNECT=NOT_TESTED`. Historical A cause and historical B causal
binding remain NOT_PROVEN; previous smoke/reconnect results are not rewritten.
No supervisor acceptance, live burst acceptance, whitelist field test or release claim.
Resume this checkpoint using the same installed APK; no signing/reinstallation.
