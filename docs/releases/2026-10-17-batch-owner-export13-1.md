# BATCH-OWNER-EXPORT13-1 — browsing failure, partial cause

**RESULT=OWNER_BROWSING_FAIL_PARTIAL_CAUSE_ADMISSION_AND_RELIABLE_RECOVERY.**
The owner reports that some sites again fail and speed has not subjectively improved
after the batching pair rollout. This does **not** pass the mobile browsing/performance
check. The current tunnel did start and carries traffic; neither universal failure nor
a measured before/after throughput regression is established.

Input review `8fde9476d813d938e887a8729ba12105be6cfa9f`;
[installation and maintenance](2026-10-17-transport-batch-maintenance-and-rollout-1.md),
[safe evidence](evidence/2026-10-17-batch-owner-export13-1.json).
All event times below are17 October2026 UTC unless explicitly historical.

## Inputs, identity and successful startup

Owner-supplied export13:99,735 bytes, SHA256
`104248487c972db0931d6e8ed45cc74308266543d4977f647d1d50c6cf7f171b`.
Private copy received09:15:36.316UTC; source mtime09:14:16.617 is not an event timestamp.
Raw export, actual session/connection/device identifiers and server journals stay private.
Alias N1 identifies only this new dedicated session; B1 its separate early bootstrap tag.

Ring version `0.1.18-research84-ui60-4-batch1`, code84, CELLULAR matches the installed
candidate. Last installed APK697f9c24…49233f and native dd722ead…20c23 are the previous
verified installation receipts, not a new ADB byte readback. Source inventory remains
`cdd089478624ff5113d14590a340092684127a674565c3acfe6750aa76a17790`.

- One retained DISCONNECTED→CONNECTING transition at09:06:57.023; this analysis
  initiated no CONNECT and does not infer user tap counts from internal retries.
- Startup attempt1 SUCCEEDED in24,385ms; B1 Family authentication recorded separately.
  App becomes restricted CONNECTED at09:07:23.603, not merely TUN creation.
- Exact dedicated tag matches server descriptor09:07:11.690, Family TLS
  established09:07:20.680 and gateway session established09:07:22.560.
- Last native observation09:14:00.817 is397.214s after app CONNECTED. Terminal NONE,
  publisher/subscriber connected, no current first_failure/first_close exported.
  These facts do not turn failing individual page requests into a traffic PASS.
- The saved **incident** is historical `ui60-4-speed-recovery1`, DEDICATED_AUTH/UNKNOWN,
  ending16Oct21:43:02.997. It is not a new batch1 startup failure or N1 terminal.

## What the new export actually demonstrates

| N1 observation | Value |
| --- | ---: |
| TCP active / peak |26 /64 |
| Mux admission waits / expired admission budgets |104 /5 |
| Admission rejected / cancelled / still waiting |0 /0 /0 |
| Wholedevice limit_denied / lease admission rejected |0 /0 |
| Successful mux TCP opens / open errors |237 /1 |
| Wholedevice TCP count |235 |
| Mux protocol_errors |50 |
| DNS responses / exported DNS errors |306 /0 |
| Reliable retransmissions / RTO timeout counter |180 /170 |
| Mux received / sent bytes |14,831,264 /1,943,417 |

**Admission waiting is still a real failure mechanism.** In the exact retained batch1
source, `tcpforward/mux_stream.go` starts40s before admission; `admission.go` increments
AdmissionTimeouts when this budget expires while queued. Five opens failed there, not
just an immediate rejection or a successful but slow DNS lookup.104 waits do not mean
that all104 opens exhausted40 seconds. No per-domain/time/holder-lifetime attribution is exported, so
these five cannot be assigned to specific sites or declared a socket leak. Peak64 and
zero wholedevice refusals do not negate mux waiting. Increasing caps blindly is not a fix.

**Reliable delivery also shows head-of-line pressure.** Seven of eight retained client
samples09:13:45.387–09:13:59.387 have all8 sender slots pending; head retry count reaches2.
The last sample has receive_next3914, mask62 and five buffered later blocks: a gap is
present in that observation. Last assembly snapshot has32 expired assemblies and95 RTP
sequence gaps, with exported malformed/conflict/capacity/CRC counters0. Gaps are not a
packet-loss percentage or proof of the exact mobile/SFU fault location.

The matching server tail has90/161 periodic samples with pending8 at or before the
client observation; sampled head retries reach3. Client/server sample times differ and
are not treated as simultaneous. The source maps recovery_timeouts to per-block RTO
events, **not170 session failures**. Retries/head gaps consume the shared ordered
channel used by multiple streams; the observations support investigating recovery and
backpressure, not changing production RTO/window values without local evidence.

Carrier RX increases1,415,369 bytes over the last14s, about0.809Mbit/s **aggregate carrier
activity**. This includes transport overhead/recovery and potentially multiple apps;
it is not an HTTP download measurement, available capacity or a site-specific speed.
Prior export12 and this export have different traffic/exposure, so their cumulative
counts cannot establish a normalized regression or batching causality.

`protocol_errors=50` is a multiplexing-layer aggregate. Source increments include
unknown/already-removed stream IDs, invalid state/credit transitions and DNS framing
paths. The export lacks the subtype/offending stream. Do not relabel it as TLS damage,
RECEIVE_QUEUE_FULL, DNS failure or prove that batching caused it.306 responses/0 errors
does not prove resolution of each failing site's domains. UDP282/IPv6335 denials remain
existing restricted-path observations, not permission to alter routing/security.

## Exact server match, no gateway restart explanation here

Two bounded read-only SSH collections at09:16:34–09:16:36 and09:17:51–09:17:55 confirm
loaded gateway `4b722d2d7f2159b96953e27777494bf596768f860ee8da7e634fb1100b08fab7`,
PID1162821, invocation `e1a7f717217a4132b5f5a4b81b10e95d`, active/running, NRestarts0.
It is the rollout invocation, unchanged across this episode. No service transitions
were returned in the episode window (journal no-match exit1), and exact session traces
remain in that invocation. The earlier planned maintenance/rollout was before N1;
it is not an observed restart cause for the reported browsing failure.

The first last260 query reached its cap, covering09:08:40.495–09:14:04.562 and omitting
startup. One initial-window query09:06:50–09:08:41 returned88/120 rows. Deduplicating
the two exact-tag results yields346 records, sequences1–346 without gaps. This is
continuity of the **emitted trace**, not complete coverage of every packet, mux error
or website request. No terminal/error reason occurs in these trace rows. Last server
records extend3.745s beyond the phone sample; they are not earlier client evidence.
No new ownership capture was armed. B1 alone does not bind a broker holder or HELLO send.

## Retention, next step and final state

- Client ring retains17 events, no archived N1 predecessors; ring event-drop count
  NOT_EXPORTED. Native trace192 retained/147 dropped; delivery8 retained/190 dropped.
  export_dropped, delivery_projection_dropped and projection_dropped are0.
- Client boundaries64 retained/101,640 dropped; surviving range is only
  09:14:00.703–09:14:00.767, not the whole episode. Boundary projection drop0.
  Media evidence_dropped0 is a different surface, not evidence of no other truncation.
- Last retained server boundary snapshot64/109,443 dropped.346 trace records do not
  restore those evicted low-level boundaries. Success has no required failure-only fields.
- Two read-only SSH calls; ADB/install/rollback/restart/CONNECT/export request/build/
  suites/product patch/credential change/native poller0. Private raw receipts hashed.
  Phone not touched: **last export CONNECTED**, not claimed OFF. Gateway left running.

Next engineering step: a bounded local parent-admission1 versus batch1 comparison
combining browser-like concurrent/idle/closing streams with directional loss and delayed
ACK/reassembly, recording slot release/admission completion and mux error subtypes.
The prior four-flow clean-latency win is insufficient. Do not just raise64, enlarge
queues, force-close holders or deploy another unmeasured candidate. This task performs
analysis only; the local reproduction and any fix remain pending.

Ask the owner for2–3 failing URLs without personal parameters, whether the main page
or assets fail, and whether the same URLs work without VPN. No new CONNECT is required
just to supply already observed examples. First preserve this episode; do not auto-rollback
or restart to erase it. Batch1 is **not accepted as the browsing/speed solution**;
historical bounded acceptance, handoff, supervisor and release remain unchanged.
