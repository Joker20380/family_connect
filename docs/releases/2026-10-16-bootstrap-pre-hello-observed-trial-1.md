# BOOTSTRAP-PRE-HELLO-OBSERVED-TRIAL-1

16 October2026. **RESULT=SUCCESS_NOT_REPRODUCED**.
One restricted CONNECT succeeds; exact lease-derived requester tag matches server
authenticated → grant → hello_sent. Client HELLO validation is independently confirmed
by its subsequent DESCRIPTOR/STARTED trace. New connection ends normally OFF; one
normal support export received. Historical failure is **NOT_REPRODUCED**, not fixed.
**ADMISSION_PATH=MATCHED_GRANT_AND_HELLO_SENT**; HELLO receipt/validation also proven.
Capture has a valid18-event footer but its planned15-minute window ended49.725s early
during a separately observed scheduled current4h restart. The positive matched path
through actual release is retained; full planned-window completeness is NOT claimed.
Final device VPN OFF/diagnostic APK retained; gateway same executable, ordinary argv,
new scheduled invocation ready. No re-arm, restoration restart or client rollback.
[Safe selected evidence](evidence/2026-10-16-bootstrap-pre-hello-observed-trial-1.json).

### Retained activation checkpoint,11:03UTC

Fresh device OFF observation:11:03:02UTC.
One controlled activation restart occurred; same executable verified by readback,
new seed/TLS/runtime-bound RU directory PASS. Capture header valid until11:15:13.730UTC;
footer not yet expected or collected. Own temporary next-start drop-in already removed;
running process retains its diagnostic argument. Fresh post-install owner readiness
received; one CONNECT instruction issued. Actual owner attempt/result/export pending.

### Retained installation checkpoint,10:49UTC

The diagnostic APK is signed and installed privately; ordinary launch succeeds,
VPN OFF. **OWNER_CONNECT_COUNT=0; gateway controlled restarts=0; capture activation=0.**
No post-install owner readiness confirmation has been received at this checkpoint.
Signing interaction is not that confirmation. Do not sign or install again on resume.

Input review: `53c2eecfe63b5fe5226d4323f536e46dabd875e7`.
[Diagnostic source/build result](2026-10-16-bootstrap-pre-hello-correlation-1.md),
[existing runbook](../../research/bootstrap-pre-hello-20261016/RUNBOOK.md),
[correlation helper](../../research/bootstrap-pre-hello-20261016/correlate.py).
This task authorizes one future observed restricted CONNECT, not A→B acceptance,
a startup fix, a public release, or supervisor promotion.

## Signed and installed identities

| Item | SHA256 |
|---|---|
| Retained diagnostic unsigned APK | `b2a4b76b3218ec06f3409154a1a14f71bf4feff3206be3282c25852eabdd35ca` |
| **Signed and installed diagnostic APK** | `8e5579f04de91e4ec00e3e79271dbb0f380b1ed91945ff89016aa50d274a8845` |
| **Installed embedded native** | `be70a66ccc2bcbf0478915fd414c32de3bedb2a0ae0c3222a53e65eebd0a92b2` |
| Cumulative source inventory, NOT a Git commit | `b36c4a21ee6cf04acb192a0e6d140fa565b3e5ae75f6fc8d028d029c3152781d` |
| Retained build receipt | `98ad43326e31ad4c3f7311f6c1f6a998dbc71a3bba6db183219df681a75ba356` |
| Previous installed APK / available rollback artifact | `3c733d2fc3a0ec377143b668244a4c7d6619ff24abe024da4ee9bfe31d140513` |
| Previous embedded native | `2a974350c168913ca8a217d3fc73f452fdd709c3619d0c690abd5d884c54b88c` |
| Same verified signing certificate | `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a` |
| Required gateway executable; fresh live readback still pending | `a537257162348afc35b1ebc08755d8c5dc1cd90e74c49e3987fb3eb81885e61f` |

Package `com.familyconnect.app.friends`, versionCode84,
versionName `0.1.18-research84-provisioning-seam`, non-debuggable.
Signing used the existing vault workflow and previous key; no plaintext key/password
export to argv, logs, Git or chat. Signed APK56,007,571 bytes; hash differs from both
unsigned and previous installed artifacts. Signature and16KiB alignment verified.
All unsigned non-signature ZIP entries are preserved, including DEX/native/manifest;
no rebuild, versionCode workaround, permissions change or product patch.

One ordinary `install -r`, no `-d`, uninstall, data/cache clear or re-enrollment.
Actual installed public APK was read back, hashed and signature/native verified.
Actual UID10283 before and after; package/version/signer unchanged. This supports
ordinary replace-install data preservation, not a private identity/database audit:
no private identity/database reads were performed. Previous signed APK is retained
and verified; matching package/signer/code and the unchanged-storage diagnostic delta
permit an ordinary compatible replacement if a newly serious usability regression
requires it. No rollback has been performed in this task.

## Preparation timeline (UTC,16October)

| Time | Observation/action |
|---|---|
|10:45:16|Retained build/APK/native checked; previous signed APK copied privately and verified.|
|10:45:27|One authorized Android device; actual previous APK matches expectation, UID10283, PID4826, VPN OFF.|
|10:46:01|Existing-workflow signing finishes; signature/alignment/payload checks PASS.|
|10:48:51.861|Immediate installed hash/UID/version/OFF guards pass; one replace-install begins.|
|10:48:57.055|ADB install returns Success.|
|10:48:59.737|Installed APK readback/signature/native match; UID10283; VPN OFF.|
|10:49:01.083|Ordinary launcher returns Status:ok, new PID12008; VPN OFF; zero recent matching error lines in one bounded UID-filtered logcat sample.|

The logcat sample covers AndroidRuntime/linker/libc errors after install, not a long
startup stability or exhaustive ANR check. No observed startup failure in this sample;
no claim of successful restricted transport or network restoration. Installation may
replace the old process; there has been no CONNECT in the new process.
Private receipts and APKs remain in the ignored task directory; none is published.

## Resume gate and prepared scope

1. Obtain fresh **post-install** owner confirmation of readiness for one CONNECT and
   VPN OFF. Until then do not activate capture/restart or spend its15-minute window.
   On resume use the installed artifact and existing receipts; no repeat signing/install.
2. Perform short fresh bounded server/device prerequisites, not historical journal
   searches or suites: actual loaded SHA, invocation, seed/strict served chain,
   current runtime-bound RU directory, material/process validity and ordinary
   scheduling, no pending recovery/maintenance/quiescence. Current values are not
   yet read in this task; old expiry/PID/directory values are not guarantees.
3. Save bounded pre-restart observations using existing sources. Active restricted
   session count may remain UNKNOWN; authorized interruption is not zero outage.
   Prepare exact removal of only this task's temporary startup delta, preserving
   foreign changes, before applying it under existing current4h/service coordination.
4. Only then add existing `--research-admission-evidence` with a fresh absolute
   private path and required directory permissions. Do not precreate its exclusive
   output file or add other flags. One coordinated restart of the same executable
   is authorized. This is an argv/config mutation, NOT read-only observation.
5. Restart destroys prior in-memory Broker holders. Record old/new invocation and
   state loss; it does not continue historical A. Recheck loaded SHA, seed/TLS/RU
   runtime publication and readable capture header schema/PID/invocation/enabled,
   until_ms/event_limit512. Capture lasts15minutes from process start. Require enough
   remaining time for normal startup budget, outcome, OFF and event preservation;
   otherwise no CONNECT and no automatic re-arm/restart.
6. Give the owner the complete one-shot sequence before CONNECT: one ordinary
   restricted CONNECT; if failure, no retry and normal OFF without waiting for agent;
   if success, dedicated/app readiness and one VPN-bound HTTPS/IP check, then OFF.
   One normal support export afterwards; retrieve the newly generated file, not a
   previous export. No second CONNECT, reconnect,240s stability or burst workload.
7. Preserve raw export/capture privately with hashes, receipt time and provenance;
   analyze copies. Prefer bounded waiting to the collector's known natural expiry.
   Missing footer while running is IN_PROGRESS, not write failure. No footer-only
   restart. Remove this task's temporary next-start configuration without another
   process restart where supported; do not claim the running argv lost its flag.

Fresh owner confirmation and subsequent gates remain outstanding, not presumed PASS.
No server SSH/readback, config write or restart has occurred in this checkpoint.
No future capture file exists yet; there is no temporary delta to remove at present.

## Correlation and limits to retain

Match server Exchange exactly to the new startup's `bootstrap_exchanges[]`, keeping
Family authentication separate. Consider `bootstrap_exchanges_dropped` and the
independently retained `observation.bootstrap_exchange_tag`, including a tag omitted
from the capped array. Dedicated session_tag is a different identifier. Publish only
consistent requester/holder aliases, never real tags, nonce, identities or room URLs.

For matched wait, bind holder generation/exchange/state/same_identity; generation
also joins existing dedicated traces. Empty-Exchange release/cleanup events join by
holder generation/exchange, not nearest timestamp. Role may remain UNKNOWN; ACTIVE
is not remote health. Local cleanup is not server slot removal. Late cancellation
or exchange_end must not replace first failure. HELLO send completion is not receive.

Check header/footer, sequence/written/limited, invocation/PID and actual event-window
coverage. The helper's COMPLETE_WINDOW tests startup inclusion only; it does not by
itself establish coverage of the whole significant wait. Incomplete traces support
positive retained facts with scope, never negative "holder absent" conclusions.
No observed chat-first premise yet; ChatDeliveryService/online alone cannot prove it.
Success in the restarted environment without that premise means NOT_REPRODUCED,
not a repaired or retrospectively explained historical failure.

## Requested result fields at this checkpoint

The following table records the installation checkpoint. The later activation
checkpoint below supersedes its gateway/owner-readiness fields, not its history.

| Field | State |
|---|---|
| RESULT | WAITING_FOR_OWNER_ACTION; experiment not yet started |
| SIGNED_AND_INSTALLED_APK / NATIVE | Exact hashes above; verified |
| GATEWAY_EXECUTABLE_UNCHANGED | No gateway mutation by task; fresh loaded identity pending |
| OLD_TO_NEW_INVOCATION_AND_STATE_LOSS | NOT_RUN; no controlled restart |
| CAPTURE_HEADER_FOOTER_COMPLETENESS | NOT_ACTIVATED; no capture claim |
| OWNER_CONNECT_COUNT | 0 |
| CLIENT_EARLY_TAG_TO_SERVER_EXCHANGE | NOT_MEASURED on device |
| MATCHED_ADMISSION_SEQUENCE | NOT_MEASURED |
| REQUESTER_TO_HOLDER / HOLDER_ROLE | NOT_MEASURED / UNKNOWN |
| HELLO_SENT / HELLO_RECEIVED | NOT_MEASURED / NOT_MEASURED |
| FIRST_FAILURE_OR_SUCCESS | No trial attempt; ordinary app launch succeeds |
| OBSERVED_PREMISE / NOT_REPRODUCED_LIMITS | Premise not observed; no trial outcome yet |
| NORMAL_EXPORT_ON_DEVICE | NOT_REQUESTED;0 new exports |
| FINAL_VPN_APP_GATEWAY_STATE | Checkpoint VPN OFF/PID12008/diagnostic APK retained; gateway not touched |
| TEMPORARY_CAPTURE_CONFIG_CLEANUP | NOT_APPLICABLE_YET; no delta applied |
| ACTION_COUNTS | signing1, install1, ordinary launch1, CONNECT0, task DISCONNECT0, HTTPS0, export0, rollback0, SSH0, controlled restart0, config mutation0, rebuild0, extra native readers0 |

Review-only checkpoint publication; remote HEAD/readback belongs to the publication
receipt, not the source-inventory identity. No APK/key/raw logs/export/JSONL published.
**HISTORICAL_A_CAUSE=NOT_PROVEN; HISTORICAL_B_CAUSAL_BINDING=NOT_PROVEN.**
Historical A/B/smoke/reconnect reports remain unchanged. Full device/supervisor
acceptance stays open; this diagnostic build is not a startup fix or public release.

## Activation checkpoint,11:03UTC

After the fresh post-install owner message, existing bounded collectors verify the
same installed app PID12008/VPN OFF, candidate executable, strict served TLS, listener,
matching current NL/RU directory, signed current security material and no pending
owner/recovery/writer. Earliest inspected gateway leaf/CRL expiry12:43:43UTC; RU
delegation/authority17:34:58UTC. These do not pre-validate uninspected client grants.
At10:55 the ordinary directory-sync oneshot was failed; a narrow readback at10:59:23
finds its subsequent scheduled invocation successful/DIRECTORY_SYNCED. No manual
sync, renewal, scheduler stop or repair was performed. A first generic journal query
timed out; the existing explicit system-journal-file bounded query succeeds. No
active restricted-session count is available: UNKNOWN, not zero.

-11:00:06–11:00:09UTC: existing RU coordinator/node and NL node locks acquired;
  COMMITTED/no pending owner checked. No current4h configuration changed.
-11:00:09.957: one new private directory for exclusive collector output and own
  runtime drop-in created. Only argv addition is `--research-admission-evidence`
  with a new absolute private path. Output file was not precreated.
-11:00:12.989: one controlled restart requested. Old invocation alias **INV_PRE**,
  PID265201, becomes **INV_OBS**, PID347659. Old in-memory holders are lost; restricted
  session interruption is authorized but its user/session count remains UNKNOWN.
-11:00:13.730: capture header starts the15-minute/512-event window, schema
  admission-ownership-v1, enabled=true, bound to INV_OBS/PID347659, mode0600.
-11:00:14.234: own exact-hash drop-in removed and daemon-reload completed, without
  restoration restart. Next-start argv returns to the original ordinary arguments;
  original drop-ins remain. The running process still has the capture flag.
-The immediate post-restart executable assertion failed; its transient observed
  hash was not retained, so the reason is UNKNOWN, not asserted to be a race or a
  binary replacement. Subsequent bounded readback of the **same PID/invocation**
  verifies actual loadeda5372571…885e61f and exact ordinary argv plus that one flag.
  Header independently matches PID/invocation. No retry/re-arm/restart was performed.
  Control channels close with locks released; later readiness has no pending owner.
-11:01:32–11:01:39: strict served-chain/expected-leaf match, fresh same-invocation
  bootstrap_seed_ready, directory issued after process start and identical on RU,
  executable/hash/security/maintenance checks PASS. No live mTLS/owner traffic claim.
-11:02:35 readiness receipt: capture has757.99seconds remaining, exceeding the
  conservative420-second start/observation/cleanup gate. This does not alter any
  production timeout or extend capture.11:03:02 device remains OFF/PID12008, no new
  bounded UID error lines; ChatDeliveryService alone does not prove a chat holder.

Owner instructed once: one restricted CONNECT now; failure → normal OFF/no retry;
success → one normal VPN-bound HTTPS/IP check then OFF; one normal support export.
No A→B, second CONNECT,240-second interval, fallback substitution or extra native
reader. Actual owner action count is **pending confirmation**, not inferred from
the instruction. No raw export is received yet and no requester/holder join exists.

Capture expires normally at11:15:13.730UTC (13:15:13.730 Brussels); no automatic
re-arm. Current header-only observation is **IN_PROGRESS**, not complete and not an
output-failure claim. Final footer/event retention, significant-event coverage,
client exchange correlation, HELLO/result and final OFF must still be collected.
Scheduling continues normally; any natural renewal/process change must be recorded
separately, not prevented or attributed automatically to the client. No future
startup retains this task's exclusive output path. Additional controlled restarts0,
client rollback0, product builds/patches0. Historical A/B conclusions stay unchanged.

## Observed owner result and exact correlation

Owner reports "все успешно" after the one-shot CONNECT/IP/OFF/export instruction.
The normal exported **ring** contains exactly one new DISCONNECTED→CONNECTING
transition in the capture window, native startup attempt1 SUCCEEDED, app restricted
CONNECTED, then one ordinary disconnect. All retained retry_count fields are0;
no second intentional CONNECT or observed retry. No AWG/TCP fallback success is used.
The retained **incident** is historical A at09:23UTC, not a failure of this new trial.

Consistent public aliases, with the raw mapping retained only privately:

| Alias | Meaning and exact binding |
|---|---|
| INV_PRE → INV_OBS | Pre/post controlled restart; old holders lost |
| CONN_OBS / INC_OBS / attempt1 | New ring/root/startup IDs agree; distinct from historical incident IDs |
| REQ_1 | Client bootstrap_exchanges[0].bootstrap_exchange_tag equals server Exchange byte-for-byte |
| GEN_1 | Client dedicated session_tag equals native lifecycle tag and server holder generation |
| HIST_A | Old incident HELLO_RECEIVE/IO_DEADLINE without early exchange tag; not backfilled |

Client `family_authenticated=true` is separately retained; server authenticated/ok
matches REQ_1. `bootstrap_exchanges_dropped=0`, one retained exchange. No primary
failure observation is required for this successful startup; its observation field
is absent. REQ_1 and GEN_1 are different identifiers. The successful grant creates
GEN_1 with holder_exchange=REQ_1/state AUTHORIZED, not a different pre-existing holder.
Worker transitions and release have empty Exchange but match GEN_1/REQ_1 exactly.
GEN_1 is associated with this observed VPN by the client dedicated tag; a previous
CHAT holder role or chat-first premise is **NOT_PROVEN**. Same_identity on this grant
is not proof of a prior holder conflict. Bootstrap handoff/ok is not chat/VPN handoff.

### Timeline (UTC,16October; event time, not copy time)

| Time | Client/server observation |
|---|---|
|11:04:10.067|One owner CONNECT: app DISCONNECTED→CONNECTING.|
|11:04:12.122|Native startup attempt1 begins.|
|11:04:22.717|Server seq1 authenticated/ok, exact REQ_1.|
|11:04:22.720|Seq2 grant/acquired, creates GEN_1; seq3 hello_sent/ok for REQ_1.|
|11:04:23.060|Client GEN_1 DESCRIPTOR/STARTED: HELLO has already been received and strictly validated.|
|11:04:23.428–23.994|GEN_1 CREATING→CREATED→GATEWAY_JOINING.|
|11:04:26.368|Server GEN_1 READY→CLIENT_ISSUED.|
|11:04:26.370–26.372|Matching descriptor claim and descriptor_sent/ok.|
|11:04:27.753|Bootstrap handoff/ok; client DESCRIPTOR/ISSUED at27.981.|
|11:04:30.756|REQ_1 exchange_end/ok, not cancellation or deadline.|
|11:04:34.864|Client dedicated FAMILY_TLS/ESTABLISHED.|
|11:04:38.310|Server GEN_1 ACTIVE.|
|11:04:39.135|Client GATEWAY_SESSION/ESTABLISHED; startup completes SUCCEEDED/NONE in27013ms.|
|11:04:39.208–39.362|Normal SESSION_READY projection, then app restricted CONNECTED.|
|11:04:39.362–11:05:08.831|Connected interval29.469s; requested single VPN-bound IP check owner-reported successful, exact check timestamp/HTTP response not exported.|
|11:05:08.831|Owner DISCONNECT starts.|
|11:05:08.972|Local cleanup_completed.|
|11:05:09.087–09.122|VPN_RELEASED, then DISCONNECTED/OFF;59.055s from CONNECT.|
|11:05:19.086–19.092|Later exact GEN_1 server terminal IO_CLOSED/recovery_exhausted; gateway_run_end/error→FAILED→worker cleanup→release.|
|11:07:13.909|Owner export copied privately; this is receipt time, not an event timestamp.|
|11:07:21|Bounded ADB confirms VPN OFF, same app PID12008, no new matching UID error lines.|

The retained client's DESCRIPTOR/STARTED trace follows successful `Recv` and strict
HELLO validation in the exact retained `bootstrap/protocol.go:137` requestTransport
implementation; receive is proven **by**23.060, not assigned a fabricated receive
timestamp. It is separate evidence from server hello_sent. Startup success survives
normal cleanup. The later server terminal is9.964s after app OFF and10.114s after
local cleanup; it does not replace a first startup failure (none in this trial).
Its precise reason is retained rather than declared universally benign. No claim
that local cleanup immediately removed the server slot: actual release is seq18.

### Traffic, export and retained limits

HTTPS/IP result is **owner-reported UI success**, in response to the requested single
VPN-bound check. No response receipt, destination/IP value or independent HTTP status
is in this export; no host curl/ADB-shell traffic is substituted. Restricted session
observations show DNS responses6/errors0, TCP open_ok9/errors0, protocol_errors0,
received_frames259/sent_frames254, sent_bytes10575/received_bytes29544. These are this
exported session's counters, not byte-exact totals for all app traffic. Client
retransmissions6/recovery_timeouts6 are retained, not concealed as zero. No pre-OFF
terminal is exported; native snapshot terminal_reason NONE, signaling/ICE failure NONE.
DNS proof here comes from those linked session fields, not merely HTTPS success.

One ordinary43,961-byte export, SHA256
`8cea458960c0d4e28b31bb7b38284be6147f1246d6a88629db6485df88532e53`, preserved
privately as original plus analysis copy. No extra export or manual cache rotation.
Normal export retains new ring and old cached incident separately. No private
identity/database/message read, chat send, synthetic mailbox request or native poll.

| Surface | Retained / dropped evidence |
|---|---|
| New ring |23 events; current successful startup/session; history0; no top-level ring drop counter exported (UNKNOWN, not0) |
| Historical incident |17 events; old A failed attempt1; history0; archive drop counters not exported |
| New startup |1 exchange, bootstrap_exchanges_dropped0; complete/SUCCEEDED; no failure observation required |
| Native session |evidence_dropped0; VALID dedicated correlation |
| Native lifecycle trace |43 events; trace_dropped0, export_dropped0, projection_dropped0 |
| Delivery evidence |delivery_dropped6, delivery_projection_dropped0; not inferred traffic loss |
| Transport boundaries |64 retained, indexes2304–2367; dropped2303; not whole-lifetime packet coverage |
| Bounded server journal |94 retained rows within requested current invocation/window, cap320; no independent journal drop counter |
| Later server terminal snapshot |73 trace events, trace_dropped0/export_dropped0;64 boundaries/dropped2495;delivery_dropped13; not a full packet trace |
| Admission capture (intermediate) |18 events seq1–18, no footer yet; IN_PROGRESS, not write failure or final completeness |

Old incident started09:23:50.402, HELLO_RECEIVE/IO_DEADLINE at120005ms, cleanup120008ms;
its UNKNOWN/IO_DEADLINE values remain unchanged and have no new tag. This retained
historical record must not be counted as a new CONNECT/failure. Normal app launch,
disconnect and export work; no serious new usability regression justifies rollback.
Chat operation/borrowing and HANDOFF_ON_DEVICE remain NOT_PROVEN. No240s stability,
burst envelope, second CONNECT or full device/supervisor acceptance was attempted.

## Capture closure and separate natural environment change

The first private capture snapshot contains a header plus18 events, no footer:
7,644 bytes, SHA256
`809b9eb04310947dedbd05bd1565aaf3da7106416c3ee0e8b9371a716f1b721b`.
It was correctly treated as IN_PROGRESS. The task waits only to the original known
until_ms plus3seconds, not indefinitely and not by repeating CONNECT or restart.
Final copy received11:15:17.090UTC:7,724 bytes, SHA256
`d74a6e523e904dd8852f51ce3881bad0c7153be7fb622ff593a7160e8f679d9a`.
Original and analysis copies, receipt timestamps/provenance and private alias mapping
are retained locally; no raw JSON/JSONL or real exchange/identity/room data published.

Final header is identical to the initial header, bound to INV_OBS/PID347659; footer
schema matches, stopped=true, written18, limited=false; sequence1–18 contiguous,
18<512. No output failure or event-limit truncation is observed in this retained file.
There is no separate exact server dropped-event count. However, file mtime is
**11:14:24.005UTC**, not the advertised11:15:13.730 timer endpoint. The process is
subsequently **INV_POST_SCHEDULED/PID356992**, started11:14:33UTC, and RU reports a new
scheduled transaction COMMITTED with no pending owner or writer. This is a natural
current4h operation, not another task-controlled restart or a client-caused change.
The scheduled operation changed current material/runtime; it was neither stopped
nor reversed. Old capture closes on that process shutdown, **49.725s early**.

Therefore **CAPTURE_INCOMPLETE_PLANNED_WINDOW**, despite a valid footer and the
helper's COMPLETE_WINDOW value. The helper alone only checks startup inclusion;
manual checks also verify every matched event and the significant client interval:
CONNECT11:04:10, startup/HELLO/dedicated progression, OFF11:05:09, actual server
release11:05:19, all inside the recorded interval and before early closure. This
supports the positive REQ_1 authenticated/grant/HELLO/GEN_1/cleanup join, not a global
"holder absent" conclusion. No busy/wait/wait_end is retained for REQ_1. The previous
chat/holder premise remains unproven; no statement about lost pre-restart holders
is inferred from this file. No second capture activation or test was attempted.

Own startup delta was already removed at11:00:14, before the natural restart; the
new process has exactly the original ordinary argv, **no admission capture flag**
and no reused exclusive path. At11:17–11:19, existing bounded readbacks verify the
same loadeda5372571…885e61f, INV_POST_SCHEDULED/PID356992, new same-invocation seed READY,
strict served-chain/expected-leaf PASS, new directory issued11:14:35.917 and identical
on RU, gateway leaf/CRL expiry15:14:20UTC. These are actual observations after renewal,
not reliance on a predicted future renewal. No owner CONNECT is performed against
this subsequent invocation. A final collector filename guard preserved an existing
receipt; only missing RU metadata/new seed window was read afterwards, with no
mutation. No server suites/full audit or long server-only stability was repeated.

## Final state and requested result fields

11:18:29UTC final scoped device readback: exact diagnostic APK8e5579f0…4a8845,
nativebe70a66c…0a92b2 bound by that previously native/signature-verified APK hash,
same signer/code84/UID10283, same app PID12008, VPN OFF. App process is continuous
from ordinary post-install launch through CONNECT/disconnect/export/final readback.
Diagnostic APK stays installed privately; previous signed APK remains available,
but rollback count is0. Ordinary launch/OFF/export remain usable. This is not a
release or a claim that startup policy was fixed.

| Requested field | Final result |
|---|---|
| RESULT | SUCCESS_NOT_REPRODUCED; exact observed admission path established |
| SIGNED_AND_INSTALLED_APK / NATIVE |8e5579f0…4a8845 / be70a66c…0a92b2; full identities above; final installed hash verified |
| GATEWAY_EXECUTABLE_UNCHANGED |a5372571…885e61f before activation, in capture runtime and after natural renewal |
| OLD_TO_NEW_INVOCATION_AND_STATE_LOSS |INV_PRE/PID265201→INV_OBS/PID347659 by one task restart; old in-memory holders lost; later INV_POST_SCHEDULED/PID356992 separately observed |
| CAPTURE_HEADER_FOOTER_COMPLETENESS |Valid bound header/footer,18 contiguous events, limited=false; planned window early-closed49.725s; positive request-through-release events retained |
| OWNER_CONNECT_COUNT |1; new native attempt1; no observed retries or second CONNECT |
| CLIENT_EARLY_TAG_TO_SERVER_EXCHANGE |REQ_1 exact; separate client and server Family-authentication facts; GEN_1 separate dedicated tag |
| MATCHED_ADMISSION_SEQUENCE |authenticated→grant/acquired→hello_sent→descriptor claim/send→bootstrap handoff→exchange_end/ok; GEN_1 READY/ACTIVE and later release |
| REQUESTER_TO_HOLDER / HOLDER_ROLE |REQ_1 creates GEN_1, correlated to this VPN; wait on another holder NOT_OBSERVED; previous CHAT/VPN holder role UNKNOWN |
| HELLO_SENT / HELLO_RECEIVED |Sent11:04:22.720; received/validated by client trace11:04:23.060, not inferred from send alone |
| FIRST_FAILURE_OR_SUCCESS |Startup SUCCEEDED/NONE and restricted CONNECTED; later server IO_CLOSED/recovery_exhausted after owner OFF kept separate |
| OBSERVED_PREMISE / NOT_REPRODUCED_LIMITS |Original chat-first/ACTIVE-holder premise not established; success after new process does not explain or fix historical A |
| NORMAL_EXPORT_ON_DEVICE |One normal export; new ring and historical incident separated; retention/drop limits above |
| FINAL_VPN_APP_GATEWAY_STATE |VPN OFF, diagnostic APK/PID12008 retained; gateway active, unchanged executable, ordinary argv/new scheduled invocation ready |
| TEMPORARY_CAPTURE_CONFIG_CLEANUP |Own drop-in removed/daemon-reload; next-start restored before natural restart; final running process has no flag; old capture stopped; no re-arm |
| ACTION_COUNTS |Signing1, replace-install1, ordinary launch1, owner CONNECT1/DISCONNECT1, VPN-bound IP check1 owner-reported, normal export1; task capture restart1, separately observed scheduled start1; restoration restart0, re-arm0, rollback0, manual renewal/recovery0, product patch/rebuild0, extra native poll0, uninstall/clear0 |
| REMOTE_HEAD_SHA / REPORT_URL |Final review publication/readback receipt records exact commit; not source-inventory identity |

**HISTORICAL_A_CAUSE=NOT_PROVEN; HISTORICAL_B_CAUSAL_BINDING=NOT_PROVEN;
HANDOFF_ON_DEVICE=NOT_PROVEN; LIVE_BURST_ENVELOPE=NOT_DIRECTLY_EXERCISED;
SUPERVISOR_ACCEPTANCE=NOT_PROMOTED; FULL_DEVICE_ACCEPTANCE=NOT_PERFORMED.**
Prior smoke PASS, reconnect FAIL and historical A/B reports are unchanged. This task
finishes its one-shot diagnostic trial, not NEW_PAIR_DEVICE_ACCEPTED or a release.
