# UI60 owner call interruption — export10, read-only diagnosis

**Result: maintenance cutover interrupted the exact active session; automatic
restoration reused the pre-cutover directory and failed at SEED_ADMISSION/DEADLINE.**
This is not a new device acceptance or FIELD-1. No product/configuration changes,
CONNECT, ADB, native poller, build, installation or task-controlled restart occurred.
The separate slow-loading complaint is still not a measured bandwidth result.

## Inputs, identities and correlation

Owner reports a tunnel interruption after approximately ten minutes of a call and
unsuccessful reconnection. The call start is not recorded. The tunnel had been
CONNECTED since17:16:06.556UTC, approximately31m50.646s before its first failure;
these are different durations, not evidence against the owner's call observation.
All times below are **16Oct2026 UTC**; no precise cross-host clock-offset measurement
is available. Client-local ordering and server-local ordering are independently retained.

- Owner-provided normal export10: SHA256
  `804d0fdf604b2142cec8e537416bbad2835b5f739f3d9f8405d013088392113c`,87,843bytes.
  An unchanged private copy, acquisition receipt and private server captures are retained.
- Export identifies `0.1.18-research84-ui60-3`, code84/API31, CELLULAR. Last verified
  installed APK is `e6c9dce07520abb40ce29e7bfc7e39e2483db0572d22c31ab27931478da4b00f`;
  no fresh phone/APK hash read is claimed. Its retained native is
  `be70a66ccc2bcbf0478915fd414c32de3bedb2a0ae0c3222a53e65eebd0a92b2`, UI inventory
  `7f8fd0dd8498c61c4f182b1f3322d9c2d38d17dc4f30ff9e06cef0b733d9c39d`.
- Archived dedicated tag in export10 exactly equals the active tag in
  [export9](2026-10-16-ui60-owner-slowness-export9.md): retain aliases **SESSION_S9**,
  **CONN_S9**, original **INC_S9**, **INV_S9**. This is the same session, not a
  temporally adjacent server exchange or a historical acceptance incident.
- Export10's current incident is **INC_RESTORE_S10**, a failed automatic native
  startup attempt2 on CONN_S9. It has no dedicated tag or early bootstrap exchange
  tag. The archived original session and current restoration failure are kept separate.
- Fresh18:30:59UTC loaded `/proc/MainPID/exe` hash is unchanged:
  `a537257162348afc35b1ebc08755d8c5dc1cd90e74c49e3987fb3eb81885e61f`.
  This readback is not a retroactive hash measurement of every prior process.

## Exact interruption and restoration sequence

| UTC | Surface | Observation |
|---|---|---|
|17:47:34.835|RU service journal|Credential-renewal service starts the operation aliased OP_RENEW_S10.|
|17:47:47.629|NL systemd|Gateway service **Stopping**, while SESSION_S9 is active.|
|17:47:48.529|Matched server trace|SESSION_S9 carrier still established; downlink pending8.|
|17:47:48.585–.592|Matched server trace|Local close; broker cancellation; Family parent cancellation/upper close; ICE cleanup.|
|17:47:48.979|NL systemd|Gateway **Stopped**.|
|17:47:50.343–56.343|Client archive|Reliable send base remains32194, pending8; head retries2→4→6→8; carrier received-byte counter stops advancing.|
|17:47:55.941|Client archive|Signaling WebSocket heartbeat received despite the stalled data path.|
|17:47:57.143|NL systemd|Gateway starts a new process/invocation INV_RENEW_S10.|
|17:47:57.202|Client first failure|CARRIER/FAILED, **RELIABLE_RETRY_EXHAUSTED**, close source RELIABLE_EXHAUSTION.|
|17:47:59.251–.259|Client app|Transport lost NETWORK; CONNECTED→RESTORING, automatic retry_count1.|
|17:48:01.045|Client readiness|FETCH_FAILED.|
|17:48:01.156|NL new process|`bootstrap_seed_ready` on INV_RENEW_S10.|
|17:48:01.434–.469|Client|Readiness READY; native startup attempt2 begins with the same directory fingerprint as export9.|
|17:48:02 /03|RU/NL operation archives|OP_RENEW_S10 protected cleanup recorded CLEANED on both nodes.|
|17:48:03.223|RU service journal|OP_RENEW_S10 COMMITTED, first_cause=null, receipt_written=true.|
|17:48:34.216|Client startup record|Derived observation time: started_unix_ms +32747ms; SEED_ADMISSION/DEADLINE.|
|17:48:34.328–.461|Client app|BOOTSTRAP_UNAVAILABLE; cleanup; restoration_failed and FAILED.|
|17:48:38.160–.387|Client app|Normal disconnect sequence; VPN_RELEASED at.252; DISCONNECTED at.387.|
|18:22:35.943|Latest retained app event|Readiness READY while DISCONNECTED; not a new CONNECT.|

The server closure precedes the client first failure by approximately8.6s in recorded
wall-clock time. Server terminal is therefore **not** a late consequence of the owner's
final OFF. The exact session's server terminal is `IO_CLOSED`/reliable `cancelled`,
first_close `LOCAL_CLOSE/FAMILY_UPPER_CLOSE`; no server first_failure is exported in
that terminal. Its lease deadline was still in the future,17:49:50.984UTC.
The scheduled operation, deliberate systemd stop, exact-session cancellation and
successful committed cutover establish an external maintenance interruption,
not evidence of a gateway crash caused by the call or a ten-minute tunnel limit.

Client first_failure and first_close preserve the same original event: reliable
age9721ms, retries8, pending8, ACK age8614ms, progress age9587ms. Later `IO_CLOSED`,
local cleanup, restoration deadline and final CANCELLED are separate observations.
At the server's close it had advanced receive_next to32202, while the client later
still awaited acknowledgement from send_base32194. This does not prove why every
ACK was absent, but it rules out treating all outstanding data as definitely never
received by the server. A signaling heartbeat is not proof of a usable tunnel.

## Why automatic restoration did not recover

Exact-operation archived **metadata only** was read on RU and NL; no credentials,
grant lists, profile/database contents or room URLs were read. Both completion-ledger
manifest hashes and the selected metadata-file hashes agree with their archives.

- Client failed-startup directory fingerprint **equals NL `directory-before.json`**
  for OP_RENEW_S10 and also equals the successful original export9 fingerprint.
- It **differs from RU `directory-accepted.json`** for the same committed operation.
  The operation binding in that receipt agrees. The new runtime-bound directory was
  accepted before operation cleanup/COMMITTED, but its precise publication instant
  is not inferred from copy time or archive time.
- Thus restoration selected the **pre-cutover directory**, not the newly accepted
  runtime binding. Its brief READY state is not proof of a live seed reachable through
  that selected directory. This is concrete stale-directory evidence, not a claim that
  every possible cause of the missing lease response has been excluded.

Exact retained modern client source, not dirty root main, explains the boundaries:

- `RestrictedBootstrap.refresh` can retain a usable cached selection after temporary
  readiness fetch failure (`CACHED_VALID_REFRESH_UNAVAILABLE`). Cryptographic/cache
  validity alone does not establish that the selected runtime survived a cutover.
- `carrier/bootstrap/protocol.go:286` applies the existing30s seed-admission budget;
  `connectLease` waits for a matching lease response. The recorded total startup
  observation32747ms includes setup; it is **not the120s HELLO timeout**.
- The early tag is recorded only after successful lease admission, at
  `carrier/bootstrap/protocol.go:294`. Missing tag here is expected for a failure
  before a shared server nonce is obtained; it does not indicate Java dropped it.
- `ConnectivityOrchestrator.retryable` includes NETWORK and TRANSPORT_UNAVAILABLE,
  **not BOOTSTRAP_UNAVAILABLE**. This automatic restoration consequently ends FAILED
  rather than scheduling another recovery_wait. One automatic restoration is retained;
  a second intentional owner CONNECT is not evidenced and is not invented.

No ownership capture was activated. This failure cannot be assigned to a particular
broker holder, authenticated exchange, challenge or HELLO send. Do not substitute the
historical HELLO_RECEIVE/IO_DEADLINE investigation for this earlier failure stage.
The next engineering follow-up is cutover-aware freshness/recovery using the existing
security model, plus focused local tests; no timer disabling, deadline extension,
authorization bypass or speculative retry/window patch is made in this analysis.

## Speed, DNS and retention limits

The prior slow-loading observations predate this cutover and are not explained away
by it. Export10 still has cumulative recovery counters: client retransmissions272,
recovery_timeouts273; server terminal1253/1253. Their values are not speed, loss rate
or a capacity estimate. No download size/time, isolated call traffic, application
attribution or matched direct-network throughput measurement exists.

SESSION_S9 exports DNS responses429/errors0, TCP opens225/errors3. These are scoped
counters, not proof that all applications/DNS were healthy. Ring policy counters are
non-DNS UDP denied1197 and IPv6/non-IPv4 denied2498 under the existing TCP + DNS policy;
they do not identify the call protocol or prove the cause of slow loading. No policy
is changed. Primary throughput bottleneck remains **NOT_PROVEN**.

- App ring38 events; current failure incident34; each has one archived session.
  App event-drop counts are NOT_EXPORTED. Current incident captures FAILED/TUN still
  open; later ring captures DISCONNECTED/TUN closed. Do not use the incident to claim
  VPN remained stuck on after normal cleanup.
- Archived client lifecycle32 events; trace_dropped1384, archive_dropped160,
  delivery_dropped949, export_dropped0, projection_dropped0,
  delivery_projection_dropped0. Boundaries64, dropped835210, projection_dropped0.
  Native evidence_dropped0 is a different retention surface. Telemetry drops are
  not network packet drops. Original startup scalar is absent from this archive;
  original success/correlation also has the separately preserved export9 evidence.
- Exact-session journal selection17:46:30–17:48:40:85 rows, cap320 not reached.
  Service selection17:46:30–17:49:00:55 rows, cap120 not reached; renewal selection
  same window:5 rows, cap120 not reached. These filtered windows are not all logs.
- Terminal JSON was split by journald:49152-byte `line-max` fragment followed by
  11372 bytes on the same stream/PID/invocation. Sorting by journal time and joining
  yields one valid exact-session terminal; do not discard it as malformed JSON or
  count the chunks as two terminals. Server trace/boundary retention remains bounded.
- Acquisition18:30–18:38UTC is later than the events. Raw hashes and safe selected
  fields are in [evidence](evidence/2026-10-16-ui60-owner-call-drop-export10.json).
  New restoration has no exact server exchange binding; no negative ownership claim.

## Final state and actions

Latest provided phone evidence is **VPN OFF**, app code84 unchanged by this task;
no live ADB verification is claimed. At18:30:59UTC the gateway is active/running with
the exact expected executable, PID624562/INV_READBACK_S10, started18:17:52UTC:
another natural start occurred after INV_RENEW_S10/PID605596. This later readback
does not overwrite the failure timeline or establish current full security readiness.
Systemd NRestarts0 does not mean no deliberate service stops/starts occurred.

Actions: one supplied export privately preserved/analyzed; six bounded read-only
SSH calls (three NL journal/runtime, one RU renewal journal, two exact-operation
metadata reads);0 ADB, native polls, agent CONNECT/DISCONNECT, restart, build, signing,
install, rollback, configuration or credential writes. No new export was requested.
No device/network performance suite was run; evidence joins, hashes and chronology
were checked locally. Product binaries and phone were untouched by this investigation;
the scheduler's real operational changes are explicitly recorded, not called unchanged.

FIELD-1 remains NOT_STARTED. Previous exact-pair PASS_BOUNDED is preserved for its
completed interval, not extended to this UI APK or this longer interrupted session.
Historical A/B causes, chat handoff, supervisor and release are not promoted.
