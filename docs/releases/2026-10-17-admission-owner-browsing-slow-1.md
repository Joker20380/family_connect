# ADMISSION-OWNER-BROWSING-SLOW-1

**RESULT=OWNER_REPORTED_SITES_OPEN_BUT_SLOW; THROUGHPUT_CAUSE_NOT_PROVEN.**
Following the [private pair rollout](2026-10-17-browser-admission-owner-install-1.md),
the owner reports that the sites now open, but loading remains very slow and seems
slower on some sites. This is a qualitative owner observation, not a timed download,
saved HTTPS response receipt, universal compatibility result or new acceptance PASS.
The earlier browsing failure is not rewritten. Date:17 October2026 local.

## Artifact and evidence boundary

Last verified installed version: `0.1.18-research84-ui60-4-admission1`, code84.
Signed APK `761430c0989fd2443cebad39f6cf972d21ef25123114e118ee841029c2149b1f`;
native `6d41518ffbe2b10c767552dbb4c1bc732911fb8439a525215c353541ca41cfab`;
client source inventory `c1eade0110278827c1681438a80c0509f352e2c9174badef0d3b228cc7161e9c`.
Last verified gateway `079729e4de680cb416c55c2b9b592c6450e4254a306a6960b087930cc549639d`;
gateway source inventory `0742212c5ebe38f9673dc53321d3af56c14b978e1080cbe104216ac21b40293f`.
Input review publication: `86ce95d10d462bb841f7179bc495686a23749329`.
These identities come from the rollout receipts, not a fresh phone/server poll.
Current incident, session tag, underlay, process continuity and final VPN state have
not been independently observed. The last VPN OFF receipt predates this browsing.
No new export has been supplied; export11 belongs to the previous installed pair
and cannot establish current admission counters or current throughput.

## Narrow source readback, not another root-cause claim

The retained client source confirms:

- The admission fix changes connection admission, reserved control/DNS capacity
  and SYN-forwarder lifecycle. It does not enlarge the carrier bandwidth or tune
  reliable window/pacing. Earlier fast retransmit remains present.
- `carrier/wholedevice/session.go` opens the shared Family session;
  `carrier/familysession/session.go` uses `reliablestream.DefaultConfig()`.
- `carrier/reliablestream/protocol.go` retains a sender window of8 frames,
  maximum16KiB payload per default frame, receiver window16 and base RTO1s.
  The nominal full-payload sender window is128KiB, not a measured speed limit;
  actual payload size, acknowledgement timing, peer limits and loss matter.
- `carrier/reliablestream/engine.go` gates new frames on advancement of the
  cumulative base. SACKed later frames do not eliminate a missing head's ordered
  delivery stall. The existing early retransmission requires a head at least
  RTO/4 old and at least3 later acknowledged frames; it is not adaptive RTT tuning.
- `carrier/telemost/session.go` retains2ms VP8 send pacing and receiveQueue64.
  No new transport/native/Java edit is made in this follow-up.

Several admitted browser connections still share the underlying ordered path.
More simultaneously admitted transfers can share its capacity rather than increase
it. Loss/recovery stalls, acknowledgement delay, admission waiting, underlay/provider
limits and destination latency remain alternatives, not a diagnosis of this session.
Neither a blind limit increase nor another reinstall follows from this observation.

## Next bounded evidence step

Obtain one ordinary support export immediately after the reported slow browsing,
with the owner's Wi-Fi/mobile underlay confirmation. No extra CONNECT, speed-test
app, native-stats reader or provider load is requested. Preserve the raw export
privately; use the new incident/session rather than a nearby historical record.

Inspect only fields actually retained by the normal export: new admission/refusal
counters, packet/DNS/TCP observations, reliable delivery/recovery evidence and any
available byte/time samples. Missing fields are NOT_EXPORTED, not zero. Aggregate
session bytes divided by session age are not a controlled download-rate measurement.
Correlate server observations by exact session tag if available; a current server
load or nearest timestamp alone does not explain the slow phone request.

If the ordinary evidence is insufficient, define a small agreed timed transfer
before changing window/pacing. No such transfer or benchmark runs in this follow-up.
Ten-minute continuity, field/handoff/supervisor, historical causes and release remain
open. No rollback performed or prescribed; retained prior APK/gateway have known
browsing limitations and are not promised to improve speed.

Actions in this follow-up: source/document reads and documentation update only.
Product edits, tests/builds, emulator, signing/install, SSH/ADB, restart, maintenance,
agent-triggered CONNECT and export:0. Owner action count/timing not independently
recorded. **WAITING_FOR_FRESH_NORMAL_EXPORT; NO_MEASURED_SPEED_IMPROVEMENT.**
