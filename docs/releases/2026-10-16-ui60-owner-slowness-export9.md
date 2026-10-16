# UI60 owner-reported slowness — export9 read-only analysis

## Result and scope

**DELIVERY_IMPAIRMENT_OBSERVED; THROUGHPUT_ROOT_CAUSE_NOT_PROVEN.**
The owner reports subjectively slow loading after installing UI60-3 and supplies one
normal support export. This is ordinary owner use, not FIELD-1, a speed benchmark,
new A→B acceptance or a UI regression proved by comparison. No product change is made.

The current ring describes UI60-3 on CELLULAR, restricted CONNECTED/native2/READY.
Its session, startup, connection and incident bindings agree. The separate saved
incident is an **older** provisioning-seam APK's HELLO_RECEIVE/IO_DEADLINE, with a
different connection. That old failure is not assigned to this download complaint.

UI60-3 signed APK was last verified on installation as
`e6c9dce07520abb40ce29e7bfc7e39e2483db0572d22c31ab27931478da4b00f`;
native remains the retained `be70a66ccc2bcbf0478915fd414c32de3bedb2a0ae0c3222a53e65eebd0a92b2`.
This analysis checks the export's versionName/code84, not a new installed-APK readback.
See the [installation record](2026-10-16-ui60-layout-current-style-1.md) for source,
signature and binary checks. Current loaded gateway bytes are not freshly audited here.

## Current session, UTC

Aliases: `CONN_S9`, `INC_S9`, `REQ_S9`, `SESSION_S9`, `INV_S9`. Real identifiers stay
private. Server matching uses exact dedicated session_tag, never nearest timestamps.

| Observation | Time/result |
|---|---|
| Owner-initiated CONNECT in app ring | 17:15:33.839 |
| Native startup | 17:15:35.693; SUCCEEDED after30.648s, one authenticated early exchange |
| App CONNECTED | 17:16:06.556; restricted, no fallback success substituted |
| Export native observation | 17:28:09.516; still CONNECTED, no terminal recorded |
| Connected interval to observation | 722.960s; no new acceptance or uninterrupted-process assertion |
| Existing server journal selection | 17:15:30–17:28:10, exact session/service filter,320 rows/20s bound |
| Retained server trace | sequence292–611,320 unique contiguous records, one invocation; earliest retained event17:21:37.516 |

The server selection reached its320-row cap: it does **not** cover startup or the
whole session. Positive matching events remain valid. There is no new ownership
capture or pre-HELLO server-admission conclusion. Ordinary lease offer/request/
accepted/applied events at17:23:49.233–17:23:52.367 are successful observations, not
evidence that renewal caused this complaint.

## What the evidence shows

- Current client cumulative counters:224 DNS responses/0 DNS errors;117 successful
  TCP opens/3 errors;34,619,324 mux payload bytes received;2,128,799 sent. A zero DNS
  error count does not measure DNS latency or every application's DNS path.
-119 client retransmissions and119 recovery timeouts. The exact source increments
  these when a locally sent reliable block reaches its retransmission timeout:
  these are **client→server** recovery counters, not119 failed downloads or119 VPN
  reconnects. The pair uses the retained one-second default RTO; no timeout is changed.
- Client receive assembly reports114 expired incomplete messages and218 RTP sequence
  discontinuity observations. Gaps are events, not a count/percentage of lost packets.
  These cumulative counts show delivery impairment, but the export does not date
  every occurrence or localize it to the mobile link/provider/receiver scheduling.
- Exact server downlink snapshots show8 outstanding reliable blocks in147 of197
  activity samples.43 samples have selective acknowledgements for later blocks while
  the earliest outstanding block is unacknowledged. One sample has head_retries=1.
  This establishes observed acknowledgement-window pressure and holes in ordered
  delivery. A full window alone is not proof of pathological congestion: it can also
  be normal under load. Adjacent2s samples with pending data do not retain the same
  send base; no multi-second persistent stall of that base is proved by those samples.
-21 mux protocol-error increments are exported without per-error cause. The exact
  source includes both unknown/removed-stream frames and invalid live-stream frames
  in this counter; do not assign all21 to data corruption or a new UI regression.
- Existing policy counters:366 non-DNS UDP denials and2363 IPv6/non-IPv4 denials.
  Source permits IPv4 TCP and UDP DNS only. These can be relevant to application
  fallback delays, but the counts identify neither QUIC nor particular URLs and
  do not prove which denial caused the owner's slowness. No policy is changed.

The retained client carrier-activity tail contains120 samples over237.999s,
17:24:10.344–17:28:08.343. Received-carrier-byte delta7,311,107 gives approximately
**0.246Mbit/s averaged over that whole window**, with the highest retained2s interval
approximately **1.045Mbit/s**. These are observed carrier traffic rates, including
idle time/protocol overhead, **not speed-test results, file goodput or link capacity**.
No download start/end/expected size or simultaneous non-VPN baseline is available.

## Retention and interpretation limits

- App ring18 events; historical incident17; restricted history0. App ring/incident
  drop counts are not exported, not assumed zero. Startup scalar and early exchange
  list are present; bootstrap_exchanges_dropped=0.
- Client lifecycle retains192 events; trace_dropped=409; export_dropped=0;
  projection_dropped=0. Delivery retains8 snapshots, only17:27:54.343–17:28:08.343;
  delivery_dropped=353, delivery_projection_dropped=0. In this short tail client
  pending≤4, buffered=0, head_retries=0; expiry/gap counters do not grow there.
  These late snapshots do not rule out earlier pressure during downloads.
- Client boundaries retain64 events spanning only17:28:08.443–17:28:09.446;
  dropped=212359, projection_dropped=0. Native evidence_dropped=0 is a different
  surface, not a claim of complete session retention. Boundary result `incomplete`
  can precede `ok` for the same write; it is not automatically an error.
- Server journal cap320 was reached. Its197 delivery snapshots contain bounded
  boundary tails, with cumulative boundary dropped counts94244–222582. These are
  telemetry retention drops, **not network packet drops**. One invocation is observed
  in the retained subset; whole-session gateway continuity is not asserted.
- No current terminal/RECEIVE_QUEUE_FULL/authorization failure is recorded. This does
  not prove their absence outside the retained scope. No continuous RTT, mux flow-stall
  timing, CPU attribution, resource-request timing or controlled bandwidth test exists.

## Conclusion and next step

The report is consistent with slow delivery inside the tunnel: recovery and
acknowledgement-window pressure are observable on the exact session. It does not
establish the primary bottleneck, prove a fixed speed ceiling, blame the carrier/DPI,
or exonerate UI/CPU scheduling merely because native bytes are unchanged. A targeted
performance follow-up should distinguish forward-path delivery, reverse-path ACK
delay and receiver consumption before proposing any policy/window/queue change.
No such experiment or patch starts automatically from this export analysis.

Raw export and exact-match journal remain private with acquisition timestamps and
hashes. [Safe selected evidence](evidence/2026-10-16-ui60-owner-slowness-export9.json)
contains no real session/room/user identifiers. Current-turn actions: one supplied
export analyzed, one bounded SSH journal read,0 ADB/native-stats polls,0 agent CONNECT,
DISCONNECT/restart/install/build/signing/config changes. At export the VPN is ON;
it is left untouched, and a later live OFF state is not claimed.

Prior exact-pair reconnect PASS_BOUNDED remains historical and closed in its scope.
Historical causes, handoff, supervisor, field acceptance and release are not promoted.
