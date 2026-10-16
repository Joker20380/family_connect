# UI60 throughput follow-up — retained evidence and optimization candidates

Owner reports that installed UI60-4 looks acceptable but throughput remains inadequate.
This is a read-only source/evidence review, not a benchmark, product patch or field trial.
UI60-4 signed/installed APK remains the last verified
`1bf56c381e76913d77c4dc518961020d82d2bfec33da69777a504b7569be15ef`;
native remains `be70a66ccc2bcbf0478915fd414c32de3bedb2a0ae0c3222a53e65eebd0a92b2`.
No fresh phone/server query or present VPN-state assertion is made here.

## Observed versus inferred

[Export9](2026-10-16-ui60-owner-slowness-export9.md) establishes exact-session downlink
ACK-window pressure:8 outstanding blocks in147/197 snapshots,43 with later blocks
selectively acknowledged while the oldest remains unacknowledged. Client receive
assembly has114 expired incomplete messages. These are delivery-impairment signals,
not a loss percentage or proof of one particular physical-link/provider fault.
The measured0.246Mbit/s average/1.045Mbit/s highest2s carrier interval includes idle
time and overhead; neither is a download benchmark or measured capacity ceiling.
No new throughput measurement is inferred from the owner's subjective observation.

The exact retained modern source used by UI60-4, not root main, confirms:

- `carrier/familysession/session.go:254` uses ReliableStream's default configuration.
- `carrier/reliablestream/protocol.go:37`: maximum configured payload16KiB, send
  window8, receive window16, fixed RTO1s. At full payload, up to128KiB can be in the
  send sequence window. This is not a configured bit-rate cap; actual throughput
  also depends on RTT, payload occupancy, loss/reordering and consumer progress.
- `carrier/reliablestream/engine.go:236` gates new sends by the cumulative ACK base.
  SACK marks later blocks received but does not independently slide that base.
  `engine.go:319` waits for the existing RTO before retransmitting an unsacked block;
  the ACK handler has no SACK-triggered fast retransmission. A missing early block
  can therefore hold ordered delivery/window progress until recovery.
- `carrier/telemost/session.go:34` retains2ms frame pacing. Reducing it blindly may
  increase bursts and loss. The existing receiveQueue64 is a different buffer,
  not the reliable send window; increasing it alone does not establish more capacity.

## Proposed next engineering scope, not executed

First compare retained-baseline versus a narrowly isolated loss-recovery candidate
using the existing local adapters, fixed normal/race repeats, and delayed/lost/reordered
data versus reverse ACK delay as separate cases. SACK-informed early retransmission
is a candidate, not a proved fix; protect against reordering-induced duplicate storms.
Measure useful bytes/time and stall duration, not just carrier counters. Only if
window/RTT is then limiting should a bounded window/pacing comparison follow; do not
simultaneously change queues, admission, ownership, security policy or deadlines.
No gain factor or Mbps target is promised before measurements.

The [maintenance interruption and stale-directory recovery](2026-10-16-ui60-owner-call-drop-export10.md)
remain separate: speeding packet recovery does not repair a deliberately stopped
gateway or obsolete runtime binding. Generic UDP/QUIC support is also a separate
policy/product question, not silently added as a speed tweak.

Actions: source/report reads only; product changes/builds/tests/ADB/SSH/CONNECT/
sign/install/restart0. Existing installed/backup artifacts remain unchanged. Local
comparison and any future device rollout remain pending; no UI transport acceptance,
historical causality, handoff, supervisor, field or release status is promoted.
