# OWNER-CUMULATIVE-CLIENT-ACCEPTANCE-1-RESUME

**RESULT: PARTIAL — one restricted device smoke PASS; normal export PASS;
chat handoff and reconnect acceptance remain unproven.**

This is the authorized continuation of the previously environment-blocked client
acceptance, not a retry of a failed CONNECT. The earlier
[ENVIRONMENT_BLOCKED report](2026-10-15-owner-cumulative-client-acceptance-1.md)
and [server recovery report](2026-10-15-current4h-expired-recovery-deploy-and-restore-1.md)
remain historical. Input review: 7e93a596ef2d0e919485f94d8378f5e07f55e8c4.
The installed/waiting checkpoint is retained in commit
21d226a3f92c39d67199b4b2000423af19157590 and its
[safe receipt](evidence/2026-10-15-owner-cumulative-client-resume-checkpoint.json).

## Outcome matrix

| Field | Result and evidence |
| --- | --- |
| CLIENT_DEVICE_SMOKE | **PASS**, limited to one real restricted connection, DNS/HTTPS, bounded stability and disconnect |
| CONNECT_1 | PASS; one intentional owner CONNECT; restricted SUCCESS, no AWG/TCP fallback result substituted |
| CONNECT_2 | NOT_RUN_SEQUENCE_BUDGET_RESERVED_FOR_CLEANUP; no reconnect acceptance claim |
| DEDICATED_READY | PROVEN: current client SESSION_READY plus exact matching gateway session tag, descriptor and Family TLS/session establishment |
| NATIVE_ATTACH | PROVEN: exported native_state2, successful restricted startup and actual packet/Mux traffic; not merely Android VALIDATED |
| APP_CONNECTED | PROVEN: current ring CONNECTING→CONNECTED18:41:31.141UTC |
| OWNER_HTTPS_EGRESS | PASS: owner reports expected NL egress twice using the normal VPN-bound external-IP control, including after the fixed observation interval |
| OWNER_DNS_PATH | PASS at matched-session counter level: packet dns42, Mux dns_responses42/dns_errors0; no inference from HTTPS alone |
| STABILITY_240S | PASS for bounded observations and repeated traffic; no claim of a complete lossless lifecycle trace |
| CHAT_FIRST_PRECONDITION | NOT_PROVEN; ChatDeliveryService is not proof of an independent restricted holder |
| CHAT_RECOVERY / BORROWING | NOT_MEASURED / NOT_PROVEN; no mailbox/sync or borrowed-owner evidence was obtained |
| HANDOFF_ON_DEVICE | NOT_PROVEN; successful VPN startup alone does not establish the required ownership transfer |
| NORMAL_EXPORT_ON_DEVICE | PASS for this successful attempt: ring/startup/session/counters/cleanup survive ordinary share serialization |
| Diagnostic failure fidelity on device | NOT_EXERCISED: no injected receive/startup failure; optional observation/context/local_stop absent, not required for SUCCEEDED |
| Full device acceptance | PARTIAL, not promoted to full PASS |
| SUPERVISOR_PRODUCTION_ACCEPTANCE | FAIL, unchanged |
| HISTORICAL_CAUSAL_BINDING | NOT_PROVEN, unchanged; old C1/I1 is not explained by this successful connection |

## Installed identity and data preservation

| Item | Verified identity |
| --- | --- |
| Signed and installed cumulative APK SHA256 | 3c733d2fc3a0ec377143b668244a4c7d6619ff24abe024da4ee9bfe31d140513 |
| Embedded native SHA256 | 2a974350c168913ca8a217d3fc73f452fdd709c3619d0c690abd5d884c54b88c |
| Original/rollback APK SHA256 | fd3106170ceeb1e24dad6c8eacda4107b1ab09a6ee120ccf495d92d96841aa48 |
| Same signer SHA256 | 67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a |
| Package / UID | com.familyconnect.app.friends / 10283 before and after |
| Both version labels | versionCode84; 0.1.18-research84-provisioning-seam |
| Existing cumulative source inventory | a4d489079e3da0df7fdd01b7977962b20ddbbf8605fbf682a349703a88b916d5 |

One ordinary replace-install succeeded18:21:58UTC. Actual installed bytes were pulled
and verified18:24:01UTC, including signer and embedded library, not identified by the
unchanged research84 label. One normal launcher start succeeded. No rebuild, resign,
version change, uninstall, data/cache clear, downgrade flag, permission change or
re-enrollment. No vault, keys, messages or app database were read to prove preservation.
Package/signer/UID and nondestructive replacement are proven; byte-for-byte private
data equivalence is not claimed. Normal provisioning/ACK/session/lease behavior was
allowed; the provisioning-block seam was not enabled.

The prior process was terminated by installation (Android installPackageLI exit
metadata); process changes are therefore not zero. After launch the observed app PID
remained26459 through cleanup. Selected UID-filtered AndroidRuntime/linker/libc error
readbacks contained no new matching errors; this is bounded evidence, not a full ANR audit.
The original signed APK remains private and available. No regression requiring rollback
was established; rollback was not exercised or promised merely from backup existence.

## Fresh server check, before CONNECT

Fresh read-only collectors18:17UTC, refreshed before the owner CONNECT at18:38UTC,
confirmed loaded baseline SHA256
21f0a0fdc27b50c00ea922f0b716516e2422aedf1b3797369718f7d00070509a,
PID3903125 / invocation c11ce23c7d124f2790fa9f35f13f5693, active listener18444,
ordinary argv without acceptance flag, strict served chain/expected leaf PASS.
Seed-ready record17:37:22.264648 belongs to this invocation. No owner marker/pending
recovery; coordinator COMMITTED; RU HTTP active. Current4h timer enabled/active,
last service inactive/success/exit0; no conflicting writer in the scoped observation.
No renewal/evaluate/sign/apply/recovery was invoked by this task.

The export directory_fingerprint exactly equals the fresh publication file digest
d4fa4a8b785e2d677006c02c5f2cca66e220405c4f44dd726d084d690db4e280.
RU binding, CRL signatures/number27096 and current aggregate grant revisions4/6 were
validated by the existing collectors; private grant lists/profiles are not published.

| Bound at preflight | Absolute UTC |
| --- | --- |
| Authority/grants expiry | 2026-10-16 17:34:58 |
| Leaf expiry / CRL nextUpdate, earliest bound | 2026-10-15 21:37:06 |
| Directory expiry | 2026-10-15 21:37:17.752732812 |
| Process lifetime boundary | approximately2026-10-15 21:37:17.622 |
| Next required operator threshold | 2026-10-16 11:34:58 |

These were sufficient for the agreed18-minute sequence after preparation. They are
not a current or permanent readiness promise. Final gateway state readback18:56:37UTC
remained active/running with the same PID/invocation, NRestarts0 and successful process
state. No server code/configuration/credential administrative changes occurred in this
client task; ordinary background protocol operations must not be counted as zero.

## New attempt timeline and binding

All times below are **2026-10-15 UTC**. Aliases CURRENT_CONNECTION,
CURRENT_INCIDENT, SESSION_A and DIRECTORY_A refer to one consistent private mapping,
not raw device/session identifiers. Startup attempt1 is process-local, not a global ID.
The [safe attempt receipt](evidence/2026-10-15-owner-cumulative-client-resume-attempt-1.json)
includes exact JSON paths, bounded selected records and source digests.

| UTC | Source / observation |
| --- | --- |
| 18:40:57.555 | ring.events[4]: DISCONNECTED→CONNECTING, current connection/incident; application CONNECT timestamp, not a physical-button sensor |
| 18:40:57.601–.602 | Android TUN creation and ring VPN_CAPTURE_READY; initial shared-owner TUN, not proof of native attachment yet |
| 18:40:59.706 | restricted_startup.started_unix_ms; native startup attempt1 begins |
| 18:41:13.522 | Matching SESSION_A gateway trace: DESCRIPTOR/ISSUED |
| 18:41:28.692 | Matching gateway FAMILY_TLS/ESTABLISHED |
| 18:41:30.727 | Matching gateway GATEWAY_SESSION/ESTABLISHED |
| 18:41:30.918 | Native completion time derived from started_unix_ms + completed_ms31212; status SUCCEEDED, stage STARTUP, cause NONE, complete true |
| 18:41:30.992 | ring.events[9–14] batch: BOOT_CACHE_READY, BOOT_CARRIER_READY, FAMILY_AUTH_READY, BROKER_DESCRIPTOR_READY, BOOT_CLOSED, SESSION_READY |
| 18:41:31.030 | Post-ready VPN capture replacement observation; successful attach is additionally supported by native_state2 and packet traffic |
| 18:41:31.141 | ring.events[16]: restricted CONNECTED; all recorded current orchestrator retry_count values0 |
| Before18:49:42.903 | Owner reports first successful normal external-IP check, expected NL egress |
| 18:49:42.902770–18:53:42.947690 | Fixed240.044920seconds between device readbacks; VPN present, same app PID and gateway invocation, no new selected error-log lines |
| After the interval, before DISCONNECT | Owner repeats external-IP check and reports same expected egress |
| 18:54:50.950 | ring.events[20]: owner DISCONNECT reflected as CONNECTED→DISCONNECTING/CANCELLED |
| 18:54:50.998 | Last exported session observation before native stop: native_state2, terminal_reason NONE, same SESSION_A; counters below |
| 18:54:51.114 | ring.events[22]: cleanup_completed, explicitly linked to SESSION_A |
| 18:54:51.238 / .301 | VPN_RELEASED, then DISCONNECTED |
| 18:55:00.225–.238 | Same-session server close/failure and CLEANUP/COMPLETED records, after client disconnect; see qualifications below |
| 18:56:01.716 | System readback confirms VPN OFF, app process present, only ChatDeliveryService among queried app services |
| 18:56:37.921 | Gateway final bounded readback active/running, same invocation |
| 19:03:54.020715 | Owner-supplied export copied privately; receipt time is not event time |

The grouped native event timestamps are Java snapshot-observation times, not precise
timestamps of each accumulated native event. Phase1 is supported by dedicated READY
and the exact caller contract (phase must equal1 before attach); phase2 by native_state2
and actual traffic. Literal vpn_packet_ready is NOT_EXPORTED by this projection and is
not demanded as a separate PASS condition. TcpVpnService is also the shared TUN owner
for restricted mode; its service name is not evidence of TCP fallback.

Exact session_tag matches were found in294 deduplicated records across the three
saved server windows. Startup/session connection and incident IDs match the current
ring subset; directory fingerprint matches preflight; installed hash and timestamps
place this attempt after the cumulative install. This is not time-only attribution.
Four earlier readiness-only ring entries18:24–18:37 have different IDs and are excluded
from the attempt. The initial host parser correctly stopped on its overbroad all-ring
single-attempt assertion; selection was corrected before producing the public receipt.

CONNECT→DISCONNECTED lasted833.746seconds, under18minutes. CONNECTED→owner DISCONNECT
lasted799.809seconds, beyond startup completion and the requested240seconds.
Before export supplied exact timestamps, we used conservative18:56:40UTC cleanup guard
from the18:38:40 pre-CONNECT OFF readback. CONNECT2 was deliberately skipped to leave
cleanup margin, not performed later after the actual timestamps became available.

## Traffic, counters and limits

The ordinary route-page external-IP control in exact FriendsActivity.checkIp uses the
actual VPN Network.openConnection, HTTPS Cloudflare trace, expects HTTP200, parses
ip/loc, and checks session/network validity. The owner reports the expected configured
NL egress on two requested checks. No adb-shell/host curl, cached browser page, arbitrary
206/Content-Length contract or direct provisioning probe is substituted for owner TUN
egress. Raw HTTP headers/body were not separately captured; this is owner-reported UI
success under the existing source contract, reinforced by matched native/Mux traffic.

| Counter in exported current snapshot | Value |
| --- | ---: |
| protect_ok / protect_denied | 148 / 0 |
| dns / Mux dns_responses / dns_errors | 42 / 42 / 0 |
| tcp / tcp_active / tcp_peak | 74 / 12 / 17 |
| udp_denied / ipv6_denied | 83 / 20 |
| Mux tcp_open_ok / tcp_open_errors | 76 / 1 |
| Mux sent_bytes / received_bytes | 164261 / 1244879 |
| retransmissions / recovery_timeouts | 30 / 30 |
| Mux protocol_errors | 5 |
| received_frames / sent_frames | 4470 / 4524 |

These are real cumulative values, not zeros inferred from missing fields. DNS is
supported independently of HTTPS by packet DNS input and successful Mux responses in
the same native session. Individual query names, answers, TCP destinations and external
dial receipts are not exported; per-request DNS correctness is not separately measured.
Packet TCP count and Mux Open counts have different scopes and are not equated. The
nonzero Open error, protocol errors and retransmission/timeout counters are retained,
not hidden or attributed to a causal mechanism. They do not identify a failed owner
HTTPS check or startup failure. No zero-error-all-traffic claim is made.

tcp_active12 is from the pre-stop snapshot, not a post-cleanup leak count. Actual local
cleanup is supported by cleanup_completed and VPN_RELEASED plus system VPN OFF; a
zero-fd/zero-worker inventory is not exported. Remaining ChatDeliveryService is only
service presence, not proof of successful chat sync, recovery or VPN borrowing.

## First failure, retained history and export fidelity

No unexpected startup or requested HTTPS failure is recorded for this new attempt.
Startup stays SUCCEEDED/NONE after ordinary disconnect/export; late CANCELLED in the
orchestrator is the observed owner stop, not a rewritten startup cause. Last pre-stop
session terminal_reason is NONE, signaling_failure/ice_failure NONE, authorization_denied
false. There is no new first-failure observation/context/local_stop to validate: their
absence is NOT_APPLICABLE for this success, not proof of a broken allowlist. Fault-path
diagnostic fidelity remains locally tested but not exercised on this device run.

The same-session server trace does record CARRIER/FAILED/RELIABLE_RETRY_EXHAUSTED at
18:55:00.225, FAMILY_TLS_ERROR at18:55:00.235 and GATEWAY_CLOSE at18:55:00.238, followed
by CLEANUP/COMPLETED. They occur after the recorded owner DISCONNECT and client cleanup,
not before successful startup/traffic. Keep these literal server codes; do not relabel
them as a startup fault, claim a proven causal mechanism, or claim an error-free server
session. Gateway process remains healthy. No extra restart or CONNECT was attempted.

Export root ring has27 events: four preparation events plus23 current-ID events;
restricted_history is empty. The separate incident contains128 earlier events spanning
2026-10-14 18:36:36.664 through2026-10-15 13:23:42.694UTC, state FAILED and restricted
BOOTSTRAP_UNAVAILABLE, different connection/incident IDs and no startup/session/counters.
It predates the cumulative install and must not supply the new attempt's failure or
DNS probe result. Same version label/support identity alone does not bind attempts.
Historical UNKNOWN and the earlier incident are not rewritten.

Exact researchProvisioning uses the publicStartup shim, not ownerDiagnostic code.
The actual normal pipeline is native stats → Diagnostics.nativeStats →
DiagnosticRing.startupStats / RestrictedStartup.project and restricted-session projection
→ persisted ring/incident → DiagnosticRing.exportRecord/exportBytes → Diagnostics.share.
The new schema-compatible SUCCEEDED record and counters survived that real path.
Optional failure facts are supported by the shared projector but not generated by
this success. restricted-evidence.jsonl is NOT_EXPORTED; no private-file read or new
native poll was attempted. Export/cache rotation is a permitted mutation, not read-only.

## Completeness and private provenance

The new supplied JSON is118484bytes, SHA256
374c1551b6b0d458bcd587ea1efbfc467374248e03fdcb41b9765cb3646c2932.
It was copied before analysis into a separate private supplemental capsule; source path,
copy time, size/hash and transfer description are retained privately. Local file mtime
19:02:51UTC is not an event timestamp. One normal export was requested and received;
the chosen recipient/transport was owner-controlled, not inspected or sent by the agent.
Old historical export and original evidence capsules were not replaced.

Lifecycle is bounded:192 trace entries18:50:51.408–18:54:50.919, same session throughout,
trace_dropped472, delivery_dropped392;64 boundary entries with dropped40913. Projection
drop counters are0. Successful heartbeats/carrier activity in this retained tail are
not a lossless record of the entire connection. No automatic recovery transition or
new startup appears in the current ring; individual reliable retransmissions occurred.
This is not proof that no low-level recovery ever happened.

Server windows are bounded journal reads, not a complete log. Two MESSAGE values at
18:55:00 could not be parsed as JSON; they are preserved raw/private and excluded from
structured conclusions, not treated as absent events. Host /tmp quota also interrupted
an earlier server-save attempt; the partial file/error is preserved and excluded. The
fixed observation continued on disk-backed private storage without restarting its timer.
Earlier APK readback pulls encountered the same host quota, resolved without reinstall.
No old capsule/app data was deleted to recover capacity.

## Final state and action accounting

| Action | Actual count / scope |
| --- | --- |
| Normal replace-install / launcher start | 1 / 1; install terminates the old process |
| Intentional owner CONNECT / DISCONNECT | 1 / 1 |
| CONNECT2 / client rollback | 0 / 0 |
| Requested normal VPN-bound HTTPS checks | 2, owner-reported success |
| Normal support export | 1 received; one authorized share/cache-rotation cycle; exact count of old files deleted/URI revocations NOT_MEASURED |
| Extra native stats pollers / new instrumentation / helper APK | 0 / 0 / 0 |
| Rebuild / resign / public APK distribution | 0 / 0 / 0 |
| Uninstall / clear data/cache / re-enrollment / permission bypass | 0 / 0 / 0 / 0 |
| Gateway or management deployment/config changes/restart/reset | 0 |
| Manual renewal/sign/apply/recovery / fault injection / WS1011 | 0 / 0 / 0 |
| Normal provisioning, credentials delivery/ACK, rooms/sessions/leases | Allowed runtime activity; not asserted zero or fully enumerated |

Final device: VPN OFF, cumulative APK remains privately installed, no rollback.
Final gateway: same baseline executable/invocation, active; no administrative changes
in this task. Current4h was not stopped or manually invoked. Owner/client/runtime did
change, so this report deliberately does not claim general PRODUCTION_UNCHANGED.

Only this report, STATUS, PLAN, publication index and the bounded safe attempt receipt
are included in the review documentation delta. Raw JSON/journals, APKs, private alias
mapping and collector/parser files remain local; no main, workflows, catalogs, frozen
snapshots or product sources change. Original dirty checkout and earlier review edits
are preserved. The publication SHA is not a new APK source SHA or release candidate.

Remaining limits: reconnect not run; independent chat precondition/borrowing/recovery
unproven; nonzero per-stream/Mux counters lack individual causal evidence; complete
failure-only diagnostic behavior not tested on device. No further CONNECT/export,
server recovery or patch is initiated automatically. Supervisor acceptance and historical
causal binding remain separate unresolved tasks.
