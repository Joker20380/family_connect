# ADMISSION-OVERNIGHT-EXPORT12-1

**RESULT=PARTIAL_CAUSE_IDENTIFIED: ADMISSION_DELAYS_AND_EXTERNAL_INTERRUPTION.**
The owner confirms mobile data and supplies overnight normal export12 after reporting
that pages now open but remain extremely slow. New admission counters demonstrate
slot waiting/timeouts; bounded exact-session server records separately identify two
gateway transitions. Neither all slow sites nor all overnight interruptions have one
proven cause. No product/security change or new owner trial occurs in this analysis.

Input review: `a4759da01a707e0a01fb72618b7817e854ea9a61`.
[Previous qualitative observation](2026-10-17-admission-owner-browsing-slow-1.md) and
[private rollout](2026-10-17-browser-admission-owner-install-1.md) remain historical.
[Sanitized evidence and aliases](evidence/2026-10-17-admission-overnight-export12-1.json).
All event times below are17 October2026 UTC; add two hours for Europe/Brussels.

## Inputs and separate surfaces

Raw export:251,985 bytes, SHA256
`9a222d91bc4ebf941dac531d76cf20c6d3bbd25dfe041512521d25bb38dbe2dc`.
Private analysis copy retained07:49:39UTC; copy/source-file times are not event times.
No raw export, journal, room/profile, user ID or actual session tag is published.

- Ring identifies `0.1.18-research84-ui60-4-admission1`, code84, CELLULAR;
  last native sample07:45:22.067, app CONNECTED and VPN capture open.
- The separate saved incident is **old speed-recovery1**, FAILED at DEDICATED_AUTH
  with UNKNOWN. It is not a new admission1 startup failure and is not relabeled.
- Last verified installed APK remains
  `761430c0989fd2443cebad39f6cf972d21ef25123114e118ee841029c2149b1f`, native
  `6d41518ffbe2b10c767552dbb4c1bc732911fb8439a525215c353541ca41cfab`;
  cumulative source `c1eade0110278827c1681438a80c0509f352e2c9174badef0d3b228cc7161e9c`.
  Export version is consistent, but no fresh APK/native byte readback is performed.
- Read-only gateway observation07:54:43UTC confirms loaded
  `079729e4de680cb416c55c2b9b592c6450e4254a306a6960b087930cc549639d`, active/running,
  PID1077679, invocation alias G5, start06:51:42UTC. This is not the deployment PID.

## Current N5: a concrete admission delay, not a measured bandwidth ceiling

N5 startup attempt9 succeeded in27.331s. App CONNECTED06:53:50.147;
the last native sample is51m31.920s later. Attempt9 is not nine manual CONNECTs.
This is not continuous byte-exact traffic or a controlled download benchmark.

| Exported current observation | Value |
|---|---:|
| TCP active / peak |18 /64 |
| Admission waits / admission timeouts |29 /9 |
| Admission rejected / cancelled / currently waiting |0 /0 /0 |
| Wholedevice `limit_denied` / lease admission rejected |0 /0 |
| Mux TCP opens / open errors |287 /2 |
| Wholedevice TCP count |278 |
| Mux protocol errors |37 |
| DNS responses / exported DNS errors |397 /0 |
| Reliable retransmissions / recovery timeouts |96 /82 |
| Mux received / sent bytes |10,023,143 /1,168,472 |

These counters are distinct surfaces, not interchangeable totals. In particular,
zero wholedevice refusals does **not** cancel nine mux admission timeouts.
`carrier/tcpforward/mux_stream.go` starts the unchanged40s timer before admission;
`admission.go` increments `AdmissionTimeouts` on that deadline while waiting for a
slot. Thus nine opens consumed that admission budget without a slot. This is a
demonstrated long-wait mechanism in the current session, not only a hypothetical
32/64-stream cap. Which domains/assets waited, when they waited, and whether the
holders were busy, idle keepalives or incorrectly retained are **NOT_EXPORTED**.
Do not infer a leak or cure by increasing the cap again or arbitrarily evicting sockets.

The earlier change allows bounded waiting rather than immediate rejection. It does
not increase carrier bandwidth. This evidence can explain some page-loading delays,
but cannot attribute every slow page or establish a before/after speed regression.
37 protocol errors remain aggregate observations: the source includes several
different counter sites; no offending-frame subtype is exported here.

N5 retains39 expired carrier assemblies and92 RTP gaps on the client, with no
exported malformed/conflict/CRC/capacity errors in that last assembly snapshot.
These are cumulative, not a packet-loss percentage or proof of mobile-operator DPI.
Only the last eight detailed client flow samples survive, covering07:45:07–07:45:21.
One sample has receive buffering behind a gap; later samples progress. They do not
prove sustained sender-window saturation or measure the speed of a particular site.

Exact N5 server tag matching yields260 retained trace rows07:40:41–07:45:59 in G5.
Among160 periodic flow samples,134 have sender pending0, one pending8, and no sampled
head retry count exceeds0. Sampling can miss short stalls; this is **not** evidence
for blindly enlarging the reliable window as the primary fix. Some rows are after
the phone export and are not presented as simultaneous client/server snapshots.
Dividing10MB by51minutes, or short carrier byte deltas by elapsed time, is not a
saturated download-capacity measurement. DNS aggregates do not prove every domain.
UDP135/IPv6335 denials are existing restricted-path counters, not a newly established
DNS defect or permission to change routing/security policy.

## Overnight restoration and server transitions are a separate issue

The retained application ring contains six CONNECTED→RESTORING→CONNECTED cycles:

| RESTORING | Return CONNECTED | Recorded elapsed, rounded |
|---|---|---:|
|01:20:30.101 |01:21:03.431 |33.3s |
|01:50:32.743 |01:52:04.410 |91.7s |
|03:52:11.464 |03:53:12.993 |61.5s |
|04:20:54.827 |04:22:00.507 |65.7s |
|06:21:35.583 |06:22:36.171 |60.6s |
|06:52:49.582 |06:53:50.147 |60.6s |

They are automatic restoration transitions, not six requested owner actions.
The overnight path is not uninterrupted; recovery did work in these retained cycles.
The four retained prior sessions N1–N4 preserve first_failure=first_close:
`RELIABLE_RETRY_EXHAUSTED`, one pending unsacked head, eight retries, head age about
9.5–9.6s. Later aggregate IO_CLOSED does not replace that first failure. Those head
ages are retry durations, not a ten-minute session lifetime.

For N3 and N4, exact dedicated tags bind the client to server G3/G4 respectively:

- N3 server begins stopping06:21:23.176, with matching orderly session close;
  stopped06:21:24.012, new G4 starts06:21:31.574. Client first failure06:21:33.704.
- N4 server begins stopping06:51:31.388, with matching orderly session close;
  stopped06:51:31.515, new G5 starts06:51:42.911. Client first failure06:52:48.552.

These are observed external gateway transitions on the matching sessions, not proof
that mobile loss alone caused the later client terminals. No new clock calibration
was performed; cross-host wall-clock differences are not precise network latencies.
Why those operational transitions were scheduled is not audited or changed here.
They must not be used as the cause of every browsing delay or historical failure.

N1/N2 have no match in the bounded current-journal query. One bounded follow-up of
existing rotated journals hits15s limits for both sessions and its service query;
no retry-until-success is performed. Their server causes, and the two earlier
evicted sessions, remain unresolved. Absence from these queries proves no absence
of server activity, restart or holder.

N5 positively matches a lease offer→request→accepted→applied sequence6 at07:41:40–42,
extending its recorded deadline to07:51:41.475. Thus this session did renew beyond
ten minutes; there is no evidence here of an unconditional ten-minute cutoff.
This does not establish future expiry/readiness or close historical cutoff causality.

## Retention and completion boundary

App ring128 events is at its cap; event drops are not counted in the bundle.
Historical incident17 events remains separate. Only four prior sessions are retained;
no session-eviction counter is exported. Each archive has32 trace events after160
additional archive removals. Native trace drops N1–N5:5637/1179/5613/1302/2316;
delivery drops3596/823/3580/899/1538. N5 trace retains192 events. Each session retains
64 boundary events; boundary drops103291/31996/112407/60181/157560 respectively.
Export/projection/delivery-projection/boundary-projection drops are0 on those surfaces;
that does not restore already discarded history. Failure scalars survive separately.

First server query has per-tag row caps80/80/80/80/260. N3/N4 return78 exact trace
rows each among80 matched journal rows; N5 returns260 exact trace rows. All successful
tag queries hit their row caps; this is not complete overnight capture. Current-file
service query returns8 rows. Archived follow-up exit124 means timeout/incomplete,
not no events. Raw receipts and SHA256s remain private; selected digests are published.

No new product patch, test/build, signing/install/rollback, ADB, CONNECT, maintenance,
restart or additional native reader. Two read-only SSH invocations, nine bounded
journal subqueries, one owner-supplied normal export. User action count is not inferred
from startup attempt numbers. Final phone state is only the export's CONNECTED/VPN
open snapshot, **not** a new OFF observation. Current gateway is left untouched/running.

Next: local browser-shaped slot-retention/release and admission-latency reproduction,
separating active data from idle/closing flows, before selecting a product fix. A
small explicitly timed transfer can later distinguish capacity from request-start
delay; no new live benchmark is run here. Do not raise limits/window, change timeouts,
idle/security policy or restart to make the symptom disappear. Field, supervisor,
handoff, historical causality and release remain open.
