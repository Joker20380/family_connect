# NEW-PAIR-OWNER-RECONNECT-ACCEPTANCE-1

## Final result — A startup failure, B not run

**RESULT=FAIL_A_STARTUP. NEW_PAIR_DEVICE_RECONNECT=FAIL_A_STARTUP_B_NOT_RUN.**
One new intentional VPN CONNECT is evidenced. A selected restricted, but failed
before dedicated READY/native data-plane attach/app CONNECTED. B was correctly
skipped at the first unexpected failure; no timing retry, third CONNECT or second
export. The initial preparation/publication at81ccf286 remains a historical checkpoint,
not the final outcome. This final report does not rewrite any15October experiment.

The first preserved startup observation is **HELLO_RECEIVE / IO_DEADLINE**, with
observation point **FAMILY_RECEIVE**, context **DEADLINE**, stop-at-observation **NONE**.
It is not an observed RECEIVE_QUEUE_FULL or a late runtime failure after READY.
The deeper reason the receive did not complete is **NOT_PROVEN**. No root-cause
product fix, rebuilt candidate, host/race/JVM rerun or additional device test follows.

### New A timeline and process continuity

All times below are16October2026 UTC. Client intervals use the same device clock;
cross-host alignment is not a precise causality proof.
Native observation/cleanup UTC values are derived from started_unix_ms plus the
exported elapsed_ms, not separate wall-clock fields in the startup record.

| Boundary | Evidence |
| --- | --- |
| Owner availability / pre-A | Explicit ready-now/VPN-OFF report; fresh09:20:24–09:20:50 server checks pass |
| Prepared observations | Read-only windows armed09:22:06.684; APK28772ccb…1c004b, UID10283, PID30105 and OFF rechecked |
| A CONNECT | **09:23:48.498**, one DISCONNECTED→CONNECTING transition, new connection/incident aliases A |
| Android capture created | 09:23:48.557 VPN_CAPTURE_READY; this is a blocking TUN boundary, not dedicated READY |
| Selected transport | restricted09:23:48.563; no successful AWG/TCP fallback |
| Ordinary readiness | READY09:23:49.700 and09:23:50.389, directory USABLE/current fingerprint; not dedicated-session readiness or a separate server ACK receipt |
| Native startup attempt | attempt1 starts **09:23:50.402**; installed C_NEW/current directory |
| First failure observation | **09:25:50.407**, elapsed120005ms, FAMILY_RECEIVE/IO_DEADLINE/context DEADLINE/stop NONE |
| Native cleanup | **09:25:50.410**, elapsed120008ms, local_stop source CLEANUP; later than the observation |
| Java observation / app failure | STARTUP_FAILED09:25:50.502; BOOTSTRAP_UNAVAILABLE09:25:50.508; cleanup_completed09:25:50.626; FAILED09:25:50.629 |
| Owner normal disconnect | FAILED→DISCONNECTING09:26:13.499; VPN_RELEASED09:26:13.628 |
| Final A OFF | **09:26:13.660**, DISCONNECTED; **145.162seconds** from A CONNECT, within1080seconds |
| After failure |09:28:50 scoped readback: VPN OFF, FriendsActivity/PID30105, no recent UID-filtered error lines |

The three BOOT_CACHE_READY/BOOT_CARRIER_READY/FAMILY_AUTH_READY entries share the
09:25:50.502 observation timestamp. They preserve partial startup progress; they
do not establish dedicated READY or the physical time of each earlier boundary.
There is **no CONNECTED transition**. Native summary is closed/native_state3,
authorization_denied=false, correlation_status=MISSING, terminal_reason=UNKNOWN;
generic UNKNOWN does not erase the separately retained precise startup deadline.
No lifecycle first_failure/first_close or session_tag is exported for this attempt.
The startup scalar, observation and local_stop are present in both ring and incident.

The20-event ring and17-event incident have matching new A connection/incident IDs;
they are not an old persisted incident or historical B. Public correlation uses
aliases, not product-user identifiers. Current app PID30105 is unchanged throughout
the sampled A episode and until rollback. A→B continuity is NOT_TESTED because B
does not exist. All retained retry_count values are0 and there is one new CONNECT
transition; this does not assert zero lower-layer/protocol retries.

### Gateway correlation, first cause and collection limits

Current loaded executable remains
`a537257162348afc35b1ebc08755d8c5dc1cd90e74c49e3987fb3eb81885e61f`,
PID265201/invocation`d578312a01514ea98e136a94bae5feec`. Final readback09:33:18UTC:
active/running/NRestarts0, same executable/invocation, no pending owner marker;
cgroup OOM/oom_kill counters0. This is not a new stability/load suite.
Client startup fingerprint equals current NL/RU directory
`90c5bed9e02d93ddf8ee0911b2d7a719f83569897b2efcb206f1d4619716cdbd`.

The scoped server window records bootstrap_family_open09:23:54.499534063 and
bootstrap_family_auth09:23:57.947675782. Later it records
bootstrap_exchange_rejected, stage challenge/reason context_deadline, at
09:25:54.500510981, and bootstrap_exchange_failed09:25:54.500603552.
These are temporally aligned events in the current invocation, **not an exact
owner session binding**: these messages have no owner/client session tag, and A's
client tag is absent. The recorded server rejection is later than the client
observation; neither it nor later owner CANCELLED is assigned as the primary cause.

The183 unique restricted_trace samples belong to one unbound server tag already
present before A, from09:22:01.361 through09:25:49.360. Do not re-label it as A's
dedicated session or use its counters as owner DNS/HTTPS proof. Its latest boundary
tail retains64 events and reports14366 dropped; this is that server surface only.
No backlog or receive-queue overflow is established for A from those unbound traces.

Seven successful existing journal windows retained4/20/39/64/87/137/185 rows, each
below the320-row cap. Samples at offsets285 and345seconds timed out after30seconds;
the first final journal read returned255/SSH banner timeout, while its separate
service-state read succeeded. The observer was stopped after the owner failure,
at09:28:51, with no native polling or UI action. One narrower100-row bootstrap
window then succeeded at09:33:31, retaining four relevant messages. SSH collection
failures are limitations, not proof of the owner transport cause. Journal/runtime
snapshots do not prove absence of every intermediate event or external change.

No gateway executable/management/config/current4h/firewall/DNS mutation or restart
was performed. The scheduled08:43 renewal/new runtime was before A and is recorded
in the preparation evidence below. No runtime change during A is observed; no
background operation is automatically blamed on the client or undone.

### Traffic, chat and the single normal export

OWNER_HTTPS_A=NOT_RUN_STARTUP_FAILED; B_INITIAL/B_AFTER_240S=NOT_RUN.
DNS_A=NOT_MEASURED_NO_SESSION_BOUND_COUNTERS; DNS_B=NOT_RUN. protect_ok58/
protect_denied0 are Android socket-protection counters, not DNS, TCP or successful
VPN traffic proof. B_STABILITY_240S=NOT_RUN; no substitute wait was performed.

CHAT_UI_ONLINE and CHAT_OPERATION_COMPLETED=NOT_MEASURED; DIRECT/BORROWED/
INDEPENDENT_RESTRICTED=NOT_CLASSIFIED; BORROWING and HANDOFF_ON_DEVICE=NOT_PROVEN.
ChatDeliveryService presence is insufficient. No correspondence or private identity/
database was read, and no message was sent. Missing chat coverage is not the reason
for the core FAIL; A's startup failure is.

One owner-supplied normal support export was copied privately before analysis at
09:28:34.903181UTC: **15962bytes**, SHA256
`2ccb7ffeb19cd516ea7e496456b0796cdc83af712c4f2ac94c0f3151fb9c0688`.
Receipt time is not export/event time. Normal export was used; no manual cache clear
or replacement, extra export request, helper or diagnostic failure injection.

| Retention surface | Retained / unavailable |
| --- | --- |
| Current ring |20 events,0 archived sessions; startup scalar/observation/local_stop present |
| Current A incident |17 events,0 archived sessions; same startup and A IDs; ends at FAILED |
| Client lifecycle / boundary tail |Not exported; first_failure/first_close and session tag absent |
| Client source/delivery/archive/projection/export drop counters |Not exported on either surface; **not interpreted as0** |
| Server restricted trace |183 unique samples, unbound to A; latest boundary64 retained/14366 dropped |
| Gateway journal windows |Row counts and caps above; collection timeouts explicitly retained |

No old A/B archive is manufactured from this small export. Failure-only startup
fields actually present are preserved; missing lower-level fields are not invented.
No extra CONNECT or native-stats reader was used to fill the evidence gap.

### Conservative client-only rollback and final state

After sealing the normal export, analysis, current-client observations and gateway
receipts, the authorized single client-only return was used because the new-pair
restricted startup did not work. This is a conservative usability action, **not
proof that C_NEW caused the deadline** or that the previous client fixes it.

Immediately before rollback, current APK28772ccb…1c004b, UID10283/code84 and VPN OFF
were checked again. Preserved APK3c733d2f…140513 passed signature/package checks.
Exactly one ordinary `adb install -r` succeeded, without `-d`, uninstall, data/cache
clear, new signer or re-enrollment. Readback09:36:27UTC and pulled APK verification
confirm the previous exact bytes, same signer/UID/version. One ordinary launcher
start follows; **no post-rollback CONNECT**.

Final **09:36:30.999UTC**: VPN OFF, app PID**4826**, no new sampled UID-filtered
AndroidRuntime/linker/libc error lines. Installed APK is
`3c733d2fc3a0ec377143b668244a4c7d6619ff24abe024da4ee9bfe31d140513`, native
`2a974350c168913ca8a217d3fc73f452fdd709c3619d0c690abd5d884c54b88c`.
UID10283, signer`67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`,
code84/name0.1.18-research84-provisioning-seam remain. Storage preservation is the
compatible in-place boundary, not private byte inspection. The previous version's
transport limitations remain; **NETWORK_RECOVERY_AFTER_ROLLBACK=NOT_TESTED**.
Even this final rollback OFF readback is762.501seconds after A CONNECT, within the
18-minute limit; VPN had already been normally OFF since the A sequence ended.

### Final required result fields

| Field | Final result |
| --- | --- |
| RESULT | FAIL_A_STARTUP |
| SIGNED_C_NEW_SHA256 | `28772ccb111623741dc12f14e387f1535095502748165ab87d51fdde751c004b` |
| INSTALLED_C_NEW_SHA256 / NATIVE_SHA256 during A | `28772ccb111623741dc12f14e387f1535095502748165ab87d51fdde751c004b` / `253e0e15f38223288571d3e682f6876269aa9c6d1c0c5157588ed8287ba6f3a3`; no longer final installed APK after rollback |
| SIGNER_UID_AND_DATA_PRESERVATION |Same package/signer/code84/UID10283 before/after both compatible replacements; no private data read/clear |
| CURRENT_GATEWAY_EXECUTABLE_AND_INVOCATION |a5372571…885e61f / d578312a01514ea98e136a94bae5feec, verified09:33:18UTC |
| CONNECT_A / CONNECT_B |FAIL startup / NOT_RUN after first A failure; one intentional CONNECT total |
| OFF_A_TO_CONNECT_B_INTERVAL |NOT_APPLICABLE; B not started |
| APP_PROCESS_CONTINUITY_A_B |NOT_TESTED; A PID30105 preserved until post-evidence rollback |
| DEDICATED_NATIVE_APP_READY_A_B |A NOT_REACHED / B NOT_RUN |
| SESSION_A_B_CLIENT_SERVER_BINDING |A client connection/incident/startup/current-directory binding confirmed; server session-tag binding NOT_PROVEN; B absent |
| OWNER_HTTPS_A / B_INITIAL / B_AFTER_240S |NOT_RUN_STARTUP_FAILED / NOT_RUN / NOT_RUN |
| DNS_A / DNS_B |NOT_MEASURED / NOT_RUN |
| B_STABILITY_240S |NOT_RUN |
| CHAT_OPERATION / BORROWING / HANDOFF |NOT_MEASURED / NOT_PROVEN / NOT_PROVEN |
| NORMAL_EXPORT_AND_RETENTION_LIMITS |One normal export; exact per-surface limits above |
| FIRST_FAILURE / EXTERNAL_ENVIRONMENT_CHANGE |FAMILY_RECEIVE deadline before cleanup; deeper cause UNKNOWN / no gateway runtime change observed during A; pre-A scheduled renewal separate |
| FINAL_DEVICE_STATE / CLIENT_ROLLBACK |VPN OFF; previous APK3c733d2f…140513/native2a974350…4b88c, PID4826 / one successful compatible client-only rollback |
| ACTION_COUNTS |Signing1, rebuild0, forward replace-install1, rollback1, ordinary launches2, intentional CONNECT1, B0, export1, extra native pollers0 |
| REMOTE_HEAD_SHA / REPORT_URL |Final docs-only remote readback supplied in publication receipt/final response, on existing review branch |

**LIVE_BURST_ENVELOPE=NOT_DIRECTLY_EXERCISED; SUPERVISOR_ACCEPTANCE=UNCHANGED;
HISTORICAL_B_CAUSAL_BINDING=NOT_PROVEN.** Old smoke PASS/reconnect FAIL remain.
The new pair is not device-accepted. Any further HELLO/challenge investigation or
another trial requires a separate scope; no next CONNECT, product fix, deployment,
main/workflow/catalog/release or supervisor promotion is performed here.

## Preparation checkpoint — historical, superseded by the final result above

**PREPARATION_RESULT=WAITING_FOR_OWNER_ACTION.** Existing C_NEW was signed without rebuilding,
verified and installed once over the expected owner application. Ordinary launch
succeeded; final bounded device observation is VPN OFF. **CONNECT_A=NOT_RUN;
CONNECT_B=NOT_RUN; NEW_PAIR_DEVICE_RECONNECT=NOT_RUN**, not PASS or transport FAIL.
The first-CONNECT 18-minute window has not started. Current owner availability for
the complete sequence has not been confirmed; no long wait or automatic CONNECT.

Input review publication: `f6dfd846c25dd94fee14d89e0f14e02c96299dd6`.
This is a new device-acceptance episode. The previous [single smoke PASS](2026-10-15-owner-cumulative-client-acceptance-1-resume.md),
[reconnect FAIL](2026-10-15-owner-restricted-reconnect-and-chat-1.md),
[local new-pair acceptance](2026-10-16-gateway-transport-progress-burst-candidate-1.md)
and [gateway rollout](2026-10-16-gateway-transport-progress-live-1.md) retain their
original scope and outcomes. No historical attempt or failure is rewritten.

## Signed and installed identities

Resumed owner checkpoint **09:22:06UTC**: owner explicitly reports ready now/VPN OFF.
Fresh09:20:24–09:20:50UTC collectors confirm the same required executable/current
invocation, strict served chain, NL/RU directory and valid material, no pending owner
or writer, committed transaction. Seed is outside the new30-minute query window;
the retained08:44:00 current-invocation seed receipt remains applicable, not a new
seed failure. Immediate ADB readback again verifies installed28772ccb…1c004b, UID10283,
PID30105 and VPN OFF. Existing bounded server/device collectors are armed at09:22:06,
maximum520seconds, with no native stats polling or device actions. Full owner A→B
instructions are issued together; actual CONNECT counts/times and results await
owner report and the single normal export. The preparation observations below remain
historical checkpoint values, not an assertion that the owner has already connected.

| Identity | Exact value |
| --- | --- |
| Existing unsigned APK | `cc5b883395c59d2f76f4cf8ce1d787fa764c1fac2936c9148f9876697d2c5013` |
| SIGNED_C_NEW_SHA256 | `28772ccb111623741dc12f14e387f1535095502748165ab87d51fdde751c004b` |
| INSTALLED_C_NEW_SHA256 | `28772ccb111623741dc12f14e387f1535095502748165ab87d51fdde751c004b` |
| C_NEW embedded NATIVE_SHA256 | `253e0e15f38223288571d3e682f6876269aa9c6d1c0c5157588ed8287ba6f3a3` |
| Cumulative source inventory | `c2dc3dd860044b31696893244995cbc5cc8eb805ee34319df99cce085cf40d08` |
| Existing build receipt SHA256 | `e75f67b360b4f05b26bae2760bbef804e4ddd507904af33ff2f581d9bd66a5ab` |
| Immediately previous APK / preserved rollback | `3c733d2fc3a0ec377143b668244a4c7d6619ff24abe024da4ee9bfe31d140513` |
| Previous embedded native | `2a974350c168913ca8a217d3fc73f452fdd709c3619d0c690abd5d884c54b88c` |
| Both signer certificates, SHA256 | `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a` |
| Package / actual Android UID | `com.familyconnect.app.friends` / `10283` |
| Both version codes / names | `84` / `0.1.18-research84-provisioning-seam` |

The retained successful build receipt identifies the exact input APK and native.
The canonical35-file source inventory digest and every retained file hash were
rechecked; the installed provisioning/restricted build assets carry that digest.
The retained standalone native artifact matches the installed embedded native.
No Gradle/native rebuild or host/race/JVM suite was repeated. The existing
`sign_android_vault.credentials/sign` workflow and its signing-only local vault
selection were used. Keystore/password remained in memory/memfd; no new key,
plaintext secret export, argv password or helper APK. Signed size is 56,003,475 bytes.
Its digest differs from both the unsigned artifact and the previous installed APK.

`apksigner verify` and the pinned single signer pass. 16 KiB alignment passes for
unsigned, signed and preserved rollback APKs. Every DEX/native entry and every
unsigned non-signature ZIP entry is byte-identical after signing, including the
manifest and assets. The application remains non-debuggable. A pulled readback of
the actually installed APK matches the new signed digest; its signature and
embedded native digest were independently checked. No APK is published.

## Replacement and preservation boundary

At08:54:59UTC, scoped ADB found exactly one authorized device, the expected previous
APK, UID10283, code84, PID26459 and no VPN transport. The pre-install guard repeated
package/hash/UID and VPN-OFF checks immediately before the single ordinary
`adb install -r`. A different build or active VPN would have stopped replacement.

Replacement succeeded; installed readback completed **09:04:25UTC**. One ordinary
launcher start completed **09:04:26UTC**, producing app PID**30105**. Installation
replaces the earlier process; no claim of continuity across installation is made.
The future same-process requirement applies only to A→B after this point.

At **09:06:21UTC**, FriendsActivity is focused, PID30105 remains present, VPN transport
is absent, and the bounded UID-filtered error sample contains no post-install
AndroidRuntime/linker/libc error lines. At09:07:11UTC, package-scoped exit-info has
no new crash/ANR exit: the latest record is old PID26459, USER REQUESTED, at
09:04:21.149UTC during replacement. This is a bounded startup observation, not proof
of successful restricted JNI attach or future traffic. ChatDeliveryService presence
is not evidence of online UI, mailbox completion or VPN borrowing.

SIGNER_UID_AND_DATA_PRESERVATION: package, signer, versionCode and UID preserved;
no uninstall, `-d`, data/cache clear, root, re-enrollment or identity/database read.
Data preservation is the normal in-place replacement boundary, **not a byte-level
private-storage comparison**. Existing cumulative-change records describe ownership/
diagnostic changes, not identity/database migrations; later transport corrections
change the ReliableStream writer and Telemost receive reserve. No incompatible
storage migration is introduced by those declared deltas. Equal actual package,
signer and versionCode support ordinary replacement in either direction.

The immediately previous signed APK is copied into the protected task capsule and
signature/hash/alignment verified. **CLIENT_ROLLBACK=NOT_PERFORMED.** Availability
of that copy is not a successful rollback test. One compatible client-only return
is reserved for a serious new usability regression after preserving evidence;
never uninstall/downgrade bypass. The old client's known transport limits remain.
No serious new regression requiring rollback was observed in this preparation.

## Fresh gateway readiness and natural changes

The retained bounded read-only collectors were reused; no server suite,
13-module/checkpoint audit or separate120-second stability exercise. The management/
configuration inventory part of the extra collector was omitted. Raw receipts remain
private. The initial sandbox SSH attempt was denied by local SSH configuration access;
an outside-sandbox inline collector timed out after70seconds without a complete
receipt. A narrow runtime readback succeeded, and the retained collector sent through
stdin completed. These are collection limitations, not a proven gateway failure.

Fresh observations **09:00:49–09:01:01UTC** establish:

| Boundary | Observation |
| --- | --- |
| Loaded gateway executable | `a537257162348afc35b1ebc08755d8c5dc1cd90e74c49e3987fb3eb81885e61f` |
| Current process / invocation | PID265201 / `d578312a01514ea98e136a94bae5feec` |
| Service | active/running, NRestarts0, Result success |
| Runtime start / seed READY | 08:43:56UTC / 08:44:00.320891UTC, current invocation |
| Listener / strict served chain | listener18444 present; strict TLS chain and configured served-leaf match PASS |
| Current directory SHA256 | `90c5bed9e02d93ddf8ee0911b2d7a719f83569897b2efcb206f1d4619716cdbd` |
| Runtime/directory/RU binding | issued08:44:00.31830657UTC after current start; current-invocation seed receipt; identical NL/RU digest and scope checks PASS |
| Leaf / CRL | newly issued08:43:43UTC, both expire12:43:43UTC; CRL27102 |
| Authority / RU delegation | valid until17:34:58UTC; signatures and current binding verified |
| Directory / conservative process boundary | 12:43:56.594775648UTC / approximately12:43:56UTC |
| Maintenance / recovery | no pending node-owner marker or matching writer on either host; RU transaction COMMITTED, no first_cause |
| Existing automation | current4h timer active/waiting; last service success/inactive; directory timer active/waiting |

The prior report's08:42:45UTC renewal threshold was **not assumed completed**. The
newly issued material, committed scheduled transaction, new runtime and seed above
are fresh evidence of external scheduled activity. They are not client-caused changes
or changes performed by this task. No old PID/invocation/directory was required.

The existing read-only current4h evaluate completed **09:02:50UTC**: NOOP, due=[],
alerts=[], files_changed0, remote_writes0, restarts0. Reported headroom: leaf/CRL
13,254seconds, authority/grants30,729seconds. The previously documented operator
threshold11:34:58UTC remains earlier than the current leaf/CRL expiry. At this check
an18-minute device sequence plus cleanup fits; this is **not a future readiness
guarantee**. Owner-specific delivery/ACK is not inferred from these server checks.
No active maintenance was observed, so no maintenance wait/recheck was needed.

## Unfinished device acceptance and continuation

Current availability for the owner sequence must be obtained explicitly; interaction
with a signing password dialog is not confirmation of availability for A→B. Resume
with one short fresh environment/device/PID check and rebind the prepared bounded
collector windows to that actual invocation. Do not reinstall or sign again.
Allow normal current delivery and ACK; never enable the provisioning-block seam or
restore stale cache. If environment is unusable, record ENVIRONMENT_BLOCKED without
repairing the gateway in this task. If maintenance is already running, permit its
normal bounded completion and one readiness recheck, not indefinite waiting.

The owner sequence is prepared in advance: restricted CONNECT A → successful ordinary
VPN-bound Check IP → DISCONNECT → **immediately after local OFF, CONNECT B without an
agent-response wait or a server-slot wait** → fresh VPN-bound Check IP → fixed240seconds
after B READY → repeat Check IP → normal DISCONNECT → one ordinary support export.
Maximum two intentional CONNECTs, total18minutes from A CONNECT through final OFF;
no app restart between A and B. On the first unexpected startup/traffic failure, skip
further CONNECTs, preserve first failure, disconnect and export. No timing retry.

Capture A's available short readiness/traffic observations before it becomes an
archive, using the existing bounded sources and owner result, without another native
stats reader. Distinguish UI-reported IP from an actual saved response. Obtain
session-bound DNS evidence independently. Ordinary mailbox/sync while VPN and after
OFF is optional within the remaining window; no correspondence reads or new messages.
Independent chat, borrowing and handoff require their own evidence and do not block
the core sequence when absent. One support export follows the sequence/first failure
through normal cache rotation; raw JSON stays private before analysis.

## Required result fields at this checkpoint

| Field | Result |
| --- | --- |
| RESULT | WAITING_FOR_OWNER_ACTION |
| SIGNED_C_NEW_SHA256 / INSTALLED_C_NEW_SHA256 / NATIVE_SHA256 | Exact verified identities above |
| SIGNER_UID_AND_DATA_PRESERVATION | In-place boundary verified; private storage not read |
| CURRENT_GATEWAY_EXECUTABLE_AND_INVOCATION | Exact current-check values above; refresh before A |
| CONNECT_A / CONNECT_B | NOT_RUN / NOT_RUN |
| OFF_A_TO_CONNECT_B_INTERVAL | NOT_MEASURED |
| APP_PROCESS_CONTINUITY_A_B | NOT_TESTED; post-install PID30105 recorded |
| DEDICATED_NATIVE_APP_READY_A_B | NOT_RUN / NOT_RUN |
| SESSION_A_B_CLIENT_SERVER_BINDING | NOT_AVAILABLE; no new A/B sessions assigned |
| OWNER_HTTPS_A / B_INITIAL / B_AFTER_240S | NOT_RUN / NOT_RUN / NOT_RUN |
| DNS_A / DNS_B | NOT_MEASURED / NOT_MEASURED; absent evidence is not zero errors |
| B_STABILITY_240S | NOT_RUN |
| CHAT_UI_ONLINE / CHAT_OPERATION_COMPLETED | NOT_MEASURED / NOT_MEASURED |
| CHAT_OPERATION / BORROWING / DIRECT-BORROWED-INDEPENDENT_RESTRICTED | NOT_MEASURED / NOT_PROVEN / NOT_CLASSIFIED |
| HANDOFF_ON_DEVICE | NOT_PROVEN |
| NORMAL_EXPORT_AND_RETENTION_LIMITS | No export yet; each surface's retained/drop counters NOT_OBSERVED, not zero |
| FIRST_FAILURE | No new A/B trial; none observed in bounded post-install checks |
| EXTERNAL_ENVIRONMENT_CHANGE | Natural scheduled material/runtime/directory change recorded separately |
| FINAL_DEVICE_STATE / CLIENT_ROLLBACK | New signed APK retained privately; last observed VPN OFF, app30105 / rollback0 |
| ACTION_COUNTS | Signing1; replace-install1; ordinary launch1; intentional CONNECT0/2; export0; rollback0 |
| REMOTE_HEAD_SHA / REPORT_URL | Supplied by verified publication receipt/final response; this report is on the existing review branch, not main |

Additional counts: rebuild0, host/race/JVM reruns0, new native-stats readers0, helper0,
new key0, force-stop0, uninstall/data/cache clear0, manual renewal/recovery0,
gateway/management deployment/restart0, scheduler/config/network/fault changes0,
release/main/catalog changes0. Ordinary background provisioning/chat effects are not
counted as intentional VPN CONNECTs or claimed absent without evidence.

**LIVE_BURST_ENVELOPE=NOT_DIRECTLY_EXERCISED. SUPERVISOR_ACCEPTANCE=UNCHANGED,
not promoted. HISTORICAL_B_CAUSAL_BINDING=NOT_PROVEN.** No all-suite-green or release
authorization follows from this preparation or a possible later bounded PASS.

Only this safe report, STATUS, PLAN and publication index are published. Exact APKs,
rollback, selector, raw device/server receipts and operational wrappers stay in the
protected ignored local task capsule. No room URLs, product-user identifiers,
private logs, keys or databases are included. Public release/catalog/invitation
versions and download links are unchanged; this same-version private replacement
is not a public distribution. Preserve the dirty main checkout; publication uses
the existing clean detached review worktree based on the input SHA.
