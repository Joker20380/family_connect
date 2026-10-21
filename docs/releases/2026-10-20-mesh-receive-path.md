# MESH receive-path localization —20 October2026

## Finite-deadline experiment — completed20 October, final readback09:44UTC

**FINITE_DEADLINE_CORRECTNESS: PASS. LATE_ARRIVAL_RECOVERY: conditional synthetic
1294 only. PHYSICAL_SPEED_ACCEPTANCE: NOT ACCEPTED.** Implementation, local
validation and one fresh physical A1/B/A2 are finished. B is numerically faster,
but one B cell without matched Android loss/recovery counters does not establish
repeatable, mechanism-supported improvement. Current owner is forward-update
**beta94, exact accepted A0 arrival-driven100ms policy/native**; not candidate93.
This closes this bounded experiment, not an attribution of external-network fault
or proof that the measured difference is zero. No further budget sweep is running.
Earlier partial checkpoints below are historical, superseded by this section.
[Machine-readable final evidence](2026-10-20-mesh-receive-path.deadline.json).

### Exact source and finite-deadline correctness

Patch: `tests/fixtures/mesh_receive_path/finite-deadline.patch`, SHA256
`7055282b78759c6eda10bc7cac0f938ae1d2b896a02c414b85e97807524e084d`.
Deployable candidate source: `state-client-build/rtp-deadline-20261020/android-source/`.
It starts from the sealed normal92 source, not main: only `telemost/rtp.go`, new
`telemost/rtp_reader.go`, `telemost/signaling.go`, one gap-test expectation and
Android version change. Full before/after source pins are in final evidence.
Read-alignment, SACK-hole, queue-retry and cleanup changes remain separate.

The existing track reader owns reorder/VP8 state serially. Monotonic
`gapSince + gapBudget` becomes Pion's `SetReadDeadline`; an actual read timeout
services the gap without another arrival. No additional packet queue, supervisor,
per-packet goroutine, polling or second NACK generator. Deadline changes only when
the gap changes, not for each out-of-order packet; it is cleared on reader exit.
At/after the deadline, expiry wins before insertion, including equality. A packet
already below `nextSeq` stays rejected. Late packets are not fed into another
frame and `nextSeq` is not rolled back. The existing payload clone prevents the
reused65536-byte read buffer from corrupting retained packets.

Track/epoch state is local to each reader; there is no application timer callback
that can touch a replacement track. Existing Session.Close closes the Pion
receiver/PeerConnection to unblock Read, then joins the reader. Close checks also
surround Read. Deadline release/change-only arming is covered by real Pion
packetio tests. The production consumer remains bounded/nonblocking with its
existing fail-closed queue contract; an artificially blocked callback cannot
promise deadline punctuality until released. Tests explicitly release/join it.

The256-position/count window,2048-byte packet payload limit, bounded reusable
packet pool,32768-byte VP8 frame cap, carrier limits/CRC/SRTP/wire protocol and
ReliableStream parameters are unchanged. Window pressure can still skip before
time. Each *successive* gap may need its own budget: three genuine holes finish
in300/375ms, not necessarily100/125ms for the whole queue. A static retained queue
drains in at most its bounded number of gaps (conservative256×budget=25.6/32s),
plus scheduler/consumer work; no claim that all possible packet residence is125ms.
The40 real timer wakes in the repeated race run measured scheduler lateness
0.211–1.212ms on this host, separately from the100/125ms budget, not a guarantee
for Android or exact millisecond firing.

Validation retained under `state-client-build/rtp-deadline-20261020/`:

- `delta-6.jsonl`:38 cases PASS; `stress-1.jsonl`:760 cases PASS (20 repeats), race
  enabled. Controlled clocks cover silence, before/after/equal deadline, repeated
  holes and stale deadlines; independent ACK/control, window256, wraps,
  duplicate/conflict/CRC, replacement, arrival/close/timer and backpressure cases.
- `integration-3.jsonl`:170 affected integration cases PASS,6 opt-in skips, three
  packages; includes actual local-process Pion byte-exact transport/recovery.
  No replacement of physical acceptance with this synthetic test result.
- A clean patch application in `/tmp/fc-rtp-deadline-20261020-clean` passes38 delta
  cases. `a0-tradeoff.jsonl`:8 PASS against the unchanged arrival-driven source.
  Earlier450 unchanged-input race checks are reused, including177 b9/1011 cases.
- Both93 and94 normal Android builds pass169 JVM checks each. No performance
  build tags/owner fault schema; no `FamilyConnectPerf` logger in either APK.
- Initial too-short synthetic VP8 payloads, a tombstoned-corrupt-ID test assumption,
  obsolete expired-gap-heal expectation and sandbox socket/build failures are
  retained in earlier logs, corrected and rerun. No arbitrary sleep increase.

Important tradeoff: exact A0 can heal even a126/500ms late hole if no intervening
arrival caused a skip; it can also retain the subsequent packet indefinitely in
silence. A100/B125 intentionally reject that overdue hole. Thus finite servicing
is a correctness result for the new contract, **not universal better recovery**.

### RTP_SKIP_TRIGGER / NACK_NEGOTIATION_AND_TIMING

The retained614/1127/1294 episodes establish time-triggered skip, not window256
or track reset. DATA597 remains trigger-unknown with its final6s absent. No new
assembly-capacity/slow-consumer explanation replaces this evidence.1294's9909
returns~109.864ms after reconstructed enqueue,0.417ms after the original discard.
Exact native pins remain interceptor0.1.45/webrtc4.2.15, default NACK interval100ms
and RegisterDefaultInterceptors without frequency/retry override. Negotiated
NACK/RTX, actual feedback and the origin of9909 remain unknown; it is not labelled
a NACK response. Subscriber–SFU recovery is not equated to NL–Android RTT.

### REPLAY_RESULTS: exact A0 versus autonomous A100/B125

Same retained process-local arrivals and synthetic payload structure; no invented
real payload or physical byte-exact claim.1294 has reconstructed enqueue times
and seeded prefix; orphan/truncated frame tails are not completed by assumption.
Counts include subsequent complete frames/messages, not just the selected head.
Delay ranges compare the same subsequent messages to A0; negative means earlier.

| Episode/policy | Full VP8 / carrier messages | Selected head recovered | Following-message delay vs A0,ms | Peak packets / payload bytes / capacity bytes |
|---|---:|---|---:|---:|
|614 A0|6 /5|No|0|4 /1200 /2572|
|614 A100|6 /5|No|−68.239…0|3 /1200 /2486|
|614 B125|6 /5|No|−43.239…0|3 /1200 /2486|
|1127 A0|11 /6|No|0|19 /15872 /18184|
|1127 A100|11 /6|No|−2.164…0|18 /15786 /18098|
|1127 B125|11 /6|No|0…+22.836|29 /26598 /27796|
|1294 A0|20 /12|No|0|35 /33562 /33722|
|1294 A100|20 /12|No|−9.416…0|34 /32522 /32522|
|1294 B125|21 /13|Yes, conditional|0…+0.448|36 /34602 /34762|

1294's carrier message2969335140 becomes useful at monotonic475454674558ns
under B125; A0/A100 never complete it in the retained window. A100 advances at
475444810495ns instead. B125 keeps the rescue with an **autonomous** timer;
old9909/frame-discard1 becomes0/0 in this model.614/1127 still lack the requisite
41/43 skipped positions. B125 can delay following DATA/ACK by25ms versus A100
under true loss; the independent ACK-behind-incomplete-DATA case delivers the
intact ACK at100/125ms during silence, never the incomplete DATA.

After finite servicing every replay has **zero RTP reorder packets**, not a timer
that leaves the same queue stuck. This does not mean zero partial frame state:
614 retains one8192-byte carrier partial and3597 VP8 bytes;1127 two carrier
partials totalling8236 bytes and zero VP8 bytes;1294 A100 one8236-byte carrier
partial, B125 none, both have4796 VP8 bytes from the truncated next frame.
Existing carrier10s expiry removes all remaining partial messages when serviced;
the bounded VP8 tail waits for a known boundary/track close, never emitted as full.
All delivered synthetic data are byte-exact. These counts do not imply2× speed.

### CHOSEN_RECEIVER_POLICY / physical procedure

B125 was the one local candidate because the rescue survives finite servicing;
A100 is only an experimental control, never the accepted production baseline.
No safe pre-existing normal-build policy selector was found. Rather than create
UI/API/provisioning overrides, install93 B125, then forward94 with exact A0 native.
94 exists for **policy rollback**, not mandatory trace removal. Extended recording
was already OFF throughout. No protected Android input bypass: ordinary owner
Connect/Disconnect was used. Updates preserve data and require new media sessions;
one session across native replacement was neither promised nor required.

One cycle per phase:64KiB application control, single2MiB then two parallel2MiB,
HTTP/1.1, continuous full-body reading on phone, no request retries,150s cap.
Total18MiB bulk +192KiB control =19070976 bytes (18.1875MiB), below64MiB.
9/9 bulk and3/3 controls complete, HTTP200/curl0, correct lengths; all bulk bodies
have SHA256 `c72cdb288c75ffdf478ce2e5b855b428491f9d9298deca11457e14c2e2c41419`.
This is the observed phone-side body hash, not independent origin byte-exact
acceptance (`observed_hash_not_origin_acceptance` remains true in the receipts).
No aborted request omitted. No second cell or adaptive budget series was run.

### PHYSICAL_GOODPUT_AND_LATENCY

|Phase / actual APK / policy|Single Mbit/s (s)|Parallel aggregate Mbit/s (wall s)|Bulk complete|64KiB TTFB / full body,s|
|---|---:|---:|---:|---:|
|A1 /92 /A0|0.567613 (29.557)|1.275349 (26.31)|3/3|3.366 /4.727|
|B /93 /B125|0.630563 (26.607)|1.321561 (25.39)|3/3|3.146 /4.100|
|A2 /94 /A0|0.566537 (29.614)|1.253903 (26.76)|3/3|4.212 /5.770|

Control timings are application TTFB/full64KiB transfer, **not RTT**. B versus mean
A1/A2 is+11.20% single/+4.50% aggregate. This is a small positive observation,
not repeatable speed acceptance: one B cell, different media sessions and missing
paired Android mechanism counters. No serious bulk regression or request failure
observed; no claim that every lifecycle/latency failure is ruled out.

All phases use `tun1`, underlying network327, `CELLULAR|VPN`; actual Android-TUN
MESH route,3/3 bulk NL TCP socket matches per phase, no AWG/TCP fallback observed.
NL PID3747077/invocationb9772ef231f045aa8952565ab2ffbac2/NRestarts0 unchanged.
Media-session tags: A1 `e242f8d092eaa9389ca1ed5efe330682ebd5cd44635180dda9969b837d73b64c`,
B `8b0bcfe9b37dd6965423d81c8e55701fb4496ce612b847ce548c7c2b10d62d6b`,
A2 `3764fad4178474445df7618390c612a49ea317a73b0264bac38e34c524b7b6a0`.
Actual Mux stream IDs are not exposed in ordinary captures; TCP matches are not
renamed Mux attribution. Session changes between updates limit comparison.

Ordinary NL trace, identical instrumentation in all phases:

|Metric, A1 /B /A2|Observed values|Coverage limitation|
|---|---|---|
|Snapshots / span,s|55/68;52/64;58/70|one session per bulk capture; no observed terminal trace|
|Max pending / max head retries|8/1;8/0;8/1|sampled, not exact RS stall duration|
|Retained retry submissions|30;0;1|lower bounds, not retry bytes or totals|
|Missing boundary indexes|18646;19161;19654|large gaps; zero observed old/drop is not zero actual|
|NL carrier TX bytes delta|7443744;7464996;7427699|includes other traffic/overhead, not RS retry/new bytes|
|NL reverse receive RTP gaps|1;0;2|reverse direction, not Android candidate recovery|

Sampled final NL pending/buffered are0/0 for each bulk capture; no captured
unchanged pending head spans adjacent snapshots, not proof of zero short stalls.
Exact forward retry/new bytes, Android hold maxima and per-DATA/ACK useful latency
are **unavailable**, not zero. The earlier PERF parser's `small_gate_pass=false`
is retained: no performance snapshots. This authorized experiment used the
ordinary HTTP/topology/socket gate, not a falsely claimed two-sided PERF PASS.

Owner's post-A2 export SHA256
`a1d9514197ec0496bf158e0583b1d21986cd4461fb3fc61fee36c6bfe249421d`
confirms94/CONNECTED, same A2 session, subscriber/publisher connected, no terminal
reason or recorded reconnect. It contains **no A1/B history**; its incident is
historical90, not a new93/94 failure. Cumulative current-session counters at
09:37:58UTC include27 Android retransmissions,25 RS timeout events, **1 Mux protocol
error**,0 TCP-open/DNS-response errors and16 carrier partial expiries/33 RTP gaps.
`recovery_timeouts` maps to ReliableStream timeouts, not25 reconnects. One
DNS_PROBE_FAILED occurs09:33:24UTC and later probes succeed without leaving
CONNECTED. Its cause and the Mux error are not identified by retained evidence;
do not claim error-free baseline or attribute them to removed B125. Only the last
eight delivery snapshots09:37:43–09:37:57 survive, outside the full measured bulk
coverage; these cumulative counters cannot supply the missing A/B loss comparison.

### RECOVERY_AND_IDENTITY_PRESERVED / CURRENT_APK_AND_GATEWAY

93 installed92→93 at09:24:19UTC;94 installed93→94 at09:30:02UTC. Same package
`com.familyconnect.app.friends`, UID10283 and signer
`67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
Identity/key-binding/Support-ID digests, owner count and handoff phases agree
before/after; owner not revoked. Fresh93 and94 READY confirms unchanged revision9,
minimum_crl27138 and usable credentials. No uninstall, data clear, reactivation,
old transition/security snapshot restore, all_activated/authority/floor/revocation
change. Final read-only09:44:01–02UTC confirms94/native/VPN and exact b9 active.

- **Current94** file: `state-client-build/rtp-deadline-20261020/normal94/delivery/FamilyConnect-0.1.18-beta94-stability.apk`.
  APK SHA256 `fe32f36d0705d83705e549f598512305d63fd942a415f71afaebfd91534f8e13`.
  Native `dd722eada0da7c890a8d71a72099cba5d0bbac1ce73377bbdbc8e7b85d820c23`,
  exact baseline92; all12 native libraries equal baseline. Source inventory
  `ee4332e048fc85f26ebbfdb47cfd675ad582b647fbe97ef5fd352f8ba4c7e840`.
- **Archived93 candidate**, not current/accepted: `state-client-build/rtp-deadline-20261020/delivery/FamilyConnect-0.1.18-beta93-rtp-deadline.apk`.
  APK SHA256 `bbccadac19b7470891189393e8382246ba9343ba3e288386e557770380f4887a`.
  Native `aaabadc3269608ec88dcb83c40b9e7a35a1c5dbbee2a8e5c7efebd0a12019f8d`,
  source inventory `2b09ed0d60fd730e2e7b9dbf20210776d1cf14975490e4c36a7fbcd57de1240e`.
- **Unchanged gateway b9/1011**:
  `b9ae880731517753e456637e52dcc421b9f7d7b881b400c856989ae93193e9ba`.
  No gateway restart or functional server update for this Android-only experiment.
  Signing receipts describe pre-install state; separate upgrade/final-readback
  receipts establish actual installation. No push, catalog/invitation/public
  distribution change; existing tester88 remains separate and untested here.

### REMAINING_LIMITATION / decision

The finite serialized mechanism is implemented and locally validated, and B125's
conditional1294 rescue is real **within the structural model**. Physical mechanism
acceptance remains unestablished. Keep94/A0; do not promote93 or rerun100→110→125→150
without new evidence. No remote tester, whitelist, overnight recovery, exact
external-network fault or NACK-origin conclusion follows from this comparison.
If a separately justified next distinguishing test is requested, one specific
option is **sender VP8 packet pacing on the same gateway/route with receiver A0**;
it was not started, bundled or made a dependency of this completed experiment.

## RTP late-arrival continuation —20 October,08:16–08:38UTC

**PARTIAL / offline replay complete; no receiver implementation or physical
A/B/A completed.** This continuation does not accept a speed fix or claim that
increasing the gap budget cannot help. It establishes a conditional recovery of
one frame, costs to other messages, and an unsatisfied finite-retention gate for
a budget-only change. Keep ordinary92/exactb9; do not deploy the test-clock tree.
[Machine-readable replay, source pins, test receipts and current readback](2026-10-20-mesh-receive-path.late-arrival.json).
The previous localization/rollout below remains historical evidence, not a new
measurement in this continuation. No new sender-only PERF or diagnostic capture.

### RTP_SKIP_TRIGGER

The sealed beta92 source is verified against its inventory and the native
binary's actual build-source capsule, not against current main. `rtp.go` has
three advancement conditions: incoming sequence distance>=256 (flush/rebase),
buffer count>=256, and an elapsed gap>100ms checked **on another arrival**.
`old_rtp` is a consequence, not the trigger. The reader creates independent
reorder/VP8 state per track; no track/epoch change appears in these selected
fresh intervals.

| DATA | Gap / advancement / discard / late arrival | Trigger confidence |
|---|---|---|
|614|next2364; first later packet2405 at416.631190101s; first queue record416.631197445s;2408 arrives416.799428955s and releases the gap; fragment1 discarded at416.799449007s|**time**; gap41 positions, buffer4 at release, not256. Missing2364–2404 do not return inside the retained interval; a late head614 packet is **not** established by these events.|
|1127|next7900;7943 arrives464.495548104s;7961 arrives464.597711749s, then fragment1 discard|**time**, about102.16ms; gap43 positions, buffer19, not256. Missing7900–7942 do not return in this interval. Later fate remains unknown.|
|1294|next9909; oldest buffered9910 has reconstructed enqueue475.344810495s;9944 arrives475.454226693s;9910 released475.454254766s; fragment0 discard475.454257110s;9909 reader475.454674558s and old_rtp475.454678308s|**time**, not distance/count: at most35 buffered positions. Oldest packet wait109.444271ms; late9909 about109.864063ms after reconstructed enqueue,0.417448ms after discard.|
|597/retry2|Preserved5973–5979 complete,5980–5986 has6 packets, fragment2 at5987; discard after5980, then old5981|**not uniquely identifiable** from saved aggregate wall-time boundaries. Compatible with time expiry, but no per-arrival monotonic clock, gapSince or queue snapshot. Do not label it a measured100ms expiry. Final6s/later retries still absent.|

Fresh source records are the same process-local origin; no Android↔NL clock
subtraction.614 and1127 use contiguous saved reader ranges;1294's retained ring
starts after gap formation. Its26 earlier queued arrivals are reconstructed from
`reorder_released.ns - wait_ns`, not presented as captured reader calls. Those
differences include the small observer-call timing uncertainty. The baseline
replay's three advancing arrivals precede the saved discards by<50µs, with the
same skipped sequence and reason. This is a structural policy check, not a
reproduction of callback execution time.

### NACK_NEGOTIATION_AND_TIMING

Actual native `dd722ead…` build info confirms `pion/interceptor v0.1.45` and
`pion/webrtc/v4 v4.2.15`, no performance build tag. Relevant `go.mod`, `go.sum`,
RTP/session/signaling/framing sources match its original native-build capsule.
Family calls `RegisterDefaultInterceptors`; Pion installs one generator and one
responder and registers video `nack`/`nack pli`. The generator default interval is
100ms; no Family interval/retry override or second generator was found or added.
This is a periodic schedule, **not** a100ms delay measured from each detected gap.

Saved90/91 exports and paired raw logs contain no negotiated `a=rtcp-fb`/`a=rtpmap`,
NACK count, RTCP NACK or RTX record. Thus actual NACK negotiation for this incoming
VP8 track, whether9909 was RTX/ordinary retransmission/original delayed RTP, NACK
send time and SFU response delay are **unknown**, not zero. Pion's TrackRemote can
return decapsulated RTX through the same reader; the saved observer discarded
attributes. Do not identify9909 as a NACK response. Subscriber↔SFU recovery is not
end-to-end NL↔Android RTT. This metadata limit does not block arrival replay.

### REPLAY_RESULTS

`tests/fixtures/mesh_receive_path/late_arrival.py prepare/run` makes a verified
private copy of exact92 and changes only test clock, budget and a read-only queue
observer. It executes the actual reorder/VP8/carrier code, not a replacement
Python algorithm. Test source and sanitized input are retained beside the
existing fixture. `RTP_LATE_OUT` selects a fresh replay directory. No main/native
production source is modified.

Payload was **not captured**. The model uses accepted encoding/CRC and packetizer,
observed sender/message/fragment IDs, RTP sequence/timestamps and available frame
boundaries. Known16KiB RS DATA uses16428 synthetic carrier bytes; complete full
fragments have7 RTP packets. Sizes of other/control payloads are synthetic, chosen
to preserve available packet counts, not claimed observed bytes. Unknown orphan
tails stay non-starting and cannot become invented complete frames.1294 seeds
synthetic already-consumed9903–9908 in the frame state implied by the saved discard;
it does not invent reader times for that prefix.597 retains the earlier labelled
structural model; **no synthetic per-packet clock is relabelled a597 capture**.

| Budget, arrival-driven |614|1127|1294|
|---|---|---|---|
|100ms, exact A|head incomplete;5 following complete messages|head incomplete;6 complete messages|head incomplete;12 other complete messages;9909 old|
|200ms, B|head still incomplete;4 following messages delayed up to392.972969ms|head still incomplete;5 delayed up to160.562761ms|conditional head recovery at475.454674558s;6 other messages delayed0.447865ms|
|350/500ms, C/D|same observed result as200|no release by last recorded arrival;35 packets retained;6 formerly complete messages withheld|same conditional recovery as200; no extra recovery|
|110ms, additional smaller check|same as100|head incomplete;5 delayed up to12.166250ms|same conditional head recovery|
|125ms, additional smaller check|same as100|head incomplete;5 delayed up to24.901198ms|same conditional head recovery|

For614 the200/350/500 gap lasts561.211823ms in the replay because there is no
arrival to service the threshold between416.799615466s and417.192401924s. For1127,
200 releases after262.726406ms;350/500 have no release despite the retained ring
extending to465.152156280s, since its last RTP reader event is464.758274510s.
The six missing terminal seconds of597 are not part of any sweep or conclusion.

These are idealized local delivery times, **not physical ACK latency**. The
following-message column is not labelled all ACKs: those rings often do not
identify their RS type. An independent synthetic ACK/control-after-incomplete-DATA
test shows the same head-of-line cost and byte-exact control release on genuine
loss. Existing physical controls649/741 still show40–49µs consume and~0.5ms local
ACK write; no slow-consumer or window-release defect is inferred here.

Peak queued packets A/B: DATA614:4/6, DATA1127:19/35, DATA1294:35/36.
Synthetic queued payload peaks: DATA614:1200/1200 bytes (including the initial
full-size arriving packet), DATA1127:15872/32524, DATA1294:33562/34602.
Maximum retained payload capacity including the recycle
pool is34762 bytes/36 packet objects across these replays. These are synthetic
payload/pool values, not captured packet sizes, total Go heap or RSS. Negative
checks preserve the256-position/2048-byte-payload bound; frame assembly, CRC and
carrier message bounds stay unchanged. Window distance can force discard before
**any** chosen time budget. No assembly-capacity explanation is substituted for
these gaps; the previous fresh session's cumulative capacity count remains zero.

### CHOSEN_RECEIVER_POLICY

**Operational policy stays100ms/256, unchanged.**125ms is a concrete local
hypothesis, not a chosen installed policy or a proven speed improvement.110ms
has only~0.136ms margin over the reconstructed late9909 timing;200–500 add no
recovery over125 and impose larger delays. However a constant-only125 change
still has **no finite silence deadline**: advancing the test clock by an hour
without another arrival leaves the complete following frame queued, for every
tested budget including baseline100. A fixed threshold is not a wall-clock upper
bound. This is a **pre-existing limitation**, not a new regression of125.

Therefore no budget-only patch is shipped as satisfying the requested bounded
retention. A serialized deadline service has **not** been implemented or tested
in this continuation; its concurrency and timing effects must not be silently
folded into the rescue claim. The remaining narrow implementation gate is to
separate100ms+deadline from125ms+deadline on these same arrivals and silence/
close/arrival cases before selecting one physical candidate. This is unfinished
receiver work, not a finding that increased waiting has no useful effect. No
new adaptive algorithm, second NACK generator, window, RTO, credit, batching,
pacing, assembly cleanup or hosting change is included.

### PHYSICAL_GOODPUT_AND_LATENCY

**NOT_RUN**, new application load0 bytes. No A/B/A throughput, retry/new-byte,
RS stall, reconnect or useful DATA/ACK latency delta exists for these policies.
The previous0.452548 single/1.132448 parallel Mbit/s values belong to the earlier
observation cell and are **not** a new A control. Saving one conditional synthetic
DATA does not establish a speed factor or repeated speed acceptance. Owner-device
was available and read back; tester availability was not used as a blocker.
No tester or whitelist acceptance is claimed.

### RECOVERY_AND_IDENTITY_PRESERVED / validation

- 50 replay/matrix checks PASS under `-race`: small reorder, later-than-old-budget
  arrival, true loss, multiple holes in successive frames, control behind data,
  distance256 before timer, duplicate, conflicting fragment, sequence/timestamp
  wrap, isolated epoch state and silence. Byte-exact means **synthetic** payload.
- Exact ordinary Android native source:223 checks PASS/6 explicit live opt-in
  skips under race; exactb9:177 PASS/6 skips, including bootstrap1011 recovery,
  cancellation and ordinary close/readiness races. No new timer exists, so these
  are not a validation of future timer/arrival/close concurrency.
- First replay failed because the test observer labelled initial nextSeq=0 as a
  skip. Fixed by retaining pre-push `started`; failures and reruns preserved.
- Sandbox regression attempt had local-network/process failures; normal
  outside-sandbox rerun passes. First b9 run omitted the existing
  `FC_EXPECT_SEED_OBSERVABILITY=1` test expectation and failed6 matrix cases plus
  their parent. Corrected the harness flag, not b9 code; affected suite rerun PASS.
- No install, uninstall, clear data, enrollment, recovery-source edit, identity/
  key/Support ID change or writes to all_activated, credentials, revocations or
  floors. Previous92 identity/READY evidence remains; this is **not a fresh
  comprehensive identity/security audit**. No old security snapshot or transition
  intent replay. No changes to rejected read-alignment/SACK-hole/queue-retry/
  cleanup patches. Raw logs and exact sources remain ignored under
  `state-client-build/rtp-late-arrival-20261020/`.

### CURRENT_APK_AND_GATEWAY / REMAINING_LIMITATION

Read-only08:37:44–45UTC20.10: installed92, UID10283, VPN/service present;
APK `1e73167c8bfdba68f96249088cf08ea3dfb9d3614d5bedb8a0a7bdd8716e4e7b`, native
`dd722eada0da7c890a8d71a72099cba5d0bbac1ce73377bbdbc8e7b85d820c23`.
NL loaded `b9ae880731517753e456637e52dcc421b9f7d7b881b400c856989ae93193e9ba`,
PID3747077/invocation `b9772ef231f045aa8952565ab2ffbac2`, active/NRestarts0.
No new APK/binary built, signed, installed or distributed. No runtime rollback
needed; future Android rollback is a forward same-signer build, never downgrade;
gateway fallback remains exactb9 with **current** materials/floors, never old4b.
Public/tester88/catalog/invitation versions not changed or newly reverified.
No push, IPv6, placement/migration, purchases or public release.

Remaining: incomplete597 clock/tail, reconstructed1294 prefix and absent NACK
metadata; more importantly, **finite-deadline implementation and one bounded
physical A/B/A remain unperformed**. The next step stays that specific125ms
receiver hypothesis with independently checked serialized deadline service, not
another general audit, sender-only PERF, pacing or placement branch.

Local work from `dddc3347db5b02896c123488f2e5e0292ff2b7a7`, main, unchanged origin.
No push/reset/merge; earlier local work preserved. Times are UTC19 October unless
specified. Localization is recorded below; no physical speed fix is accepted.
Temporary observation removed: ordinary92 installed, exactb9/1011 restored,
final identity/readiness and small Android-TUN HTTPS control PASS.
Sanitized [machine-readable evidence](2026-10-20-mesh-receive-path.evidence.json)
records hashes, measured results, coverage limitations and final runtime.

## Exact baseline

Readback22:36:55 confirms beta90/code90, UID10283/PID19388, one VPN, APK
`68cbcccfb5adf8656e8203436126330e780de099670ee2031d71019baadc3e9a`, restricted native
`dd722eada0da7c890a8d71a72099cba5d0bbac1ce73377bbdbc8e7b85d820c23`.
NL `/proc/3393714/exe` is
`b9ae880731517753e456637e52dcc421b9f7d7b881b400c856989ae93193e9ba`, invocation
`6a5fc20d6b5b43de82d0612f7c5ccb01`, active/NRestarts0. Current material expiry
02:02:34UTC20.10. Accepted source inventory
`4722b7353ba93209657f66b45c47874915362f1fbe732845ec61745abdb673e6` verified filewise.
Exact sources/receipts/private raw evidence are preserved under
`state-client-build/mesh-receive-path-20261020/`; parent immutable90 APK remains at
`state-client-build/tunnel-restart-20261019/delivery/FamilyConnect-0.1.18-beta90-stability.apk`.
Old4b is not rollback. Read-alignment, SACK-hole and queue-retry are excluded.

## Saved physical DATA_HEAD

Before any new bulk, inspected40 existing exports (versions60–89) and sparse
saved90 logcat; no matching export there. The owner then supplied a normal export
of **beta90**, copied privately as `owner-beta90-export.json`,366939bytes,
SHA256 `65a482a02f53c4f8e5ef542e1340f5c00f0c9570571bee918437e1f82f9ee0f3`.
Its incident history **does retain** session
`2219e060af8bc8a0532e29b7e55e5e2bda5eb68f592264d98400d174de714b5c`.
`saved_episode.py` joins its ordinary lifecycle boundaries with saved A1 NL
performance and reconstructed journal records; no new journal scan/bulk/Connect.

NL DATA597 initial submission and attempts0–8 have confirmed local carrier writes
(see prior queue/retry report). In particular retry2 has carrier sender752154365,
message4260144682,3 fragments, written locally21:53:31.746/.749/.751.
This identifies the same message on Android despite different SFU RTP numbering.

| Android boundary | Local wall time21:53 | Evidence |
|---|---|---|
|Fragment0 RTP5973–5979,7 packets; VP8 assembled|31.828|DATA597 known, same sender/message|
|Fragment1 RTP5980–5986,6 packets|31.924|One packet absent from aggregate; not a complete frame|
|Fragment2 RTP5987,1 packet|31.935|Same message/fragment2|
|Fragment1 frame_discard; fragment2 assembled|31.992|Timestamp7463643, previous consumed RTP5980|
|Late RTP5981 dropped old_rtp|31.992|Explicit local discard, not inferred from ring absence|
|Following DATA598 also frame_discard/late5991|32.108|Repeated adjacent gap/late pattern|
|DATA602 fragment0, message4260144684, capacity|32.236|VP8 assembled, carrier admission rejected|

These are node-local wall anchors, **not monotonic latency or one-way RTT**.
The pre-reorder observer is after Pion/SRTP/UDP, not the physical NIC. Provider,
operator and OS/library queue responsibility cannot be separated by these events.

Android generated ACK(base597,mask220); NL accepted that same base/mask (possibly
multiple matching ACK generations). It does **not** acknowledge/consume head597.
No unique shared ACK token is invented. Normal603/604 are accepted and reflected
in SACK while head remains unavailable. The archive does not contain a complete
consume chain or terminal receiver snapshot. At saved observed_at21:53:32.731,
both Android PCs still connected; NL exhausts at21:53:39.146.

Coverage: Android64 boundaries,18805 overwritten; trace92 dropped, delivery157
dropped, archive160 removed, projection/export errors0. NL52 performance snapshots
reconstruct with no performance parser error; one incomplete legacy continuation
is retained. Later retry fates are **unknown**, not negative observations.

## Local localization, not physical acceptance

Exact accepted Android native has the arrival-driven100ms gap: no new arrival
means no timer release. `TestSavedGapWithoutArrivalDoesNotRelease` reproduces it.
The selected physical interval has continuing RTP and explicit release/discard;
the no-arrival mechanism is **not established as its cause**. Deadline unchanged.

`TestSavedHead597PartialFrameRetainsAssembly` reproduces the observed fragment
shape and late5981 order on unchanged source: frame1 discarded, carrier mask101
remains incomplete until10s expiry. A separately labelled full-pool model shows
16 partial assemblies reject all3 fragments of a complete fresh attempt; expiry
restores exact delivery. This models capacity amplification, not a claim that the
unrecorded later physical597 attempts arrived intact. Both tests PASS under race.

## Observation work / application status

Reused exact accepted performance+receiver patches on fresh beta90/b9 sources,
excluding the old version89 change and all rejected functional patches. Added
monotonic pre-reorder packet, queued/released wait, identified frame-discard and
fragment-mask events; bounded256-point receive ring and128-point first-capacity
context, explicit overwrite/later-capacity counters. No payload/I/O under mutex,
new UI, canary, admission, protocol/deadline, crypto or recovery change.

Normal392/observation402 affected Go cases pass under race (9/8 opt-in skips);
standalone Java export initially failed because its classpath omitted dependent
compiled classes. Corrected classpath/rerun PASS, failure retained. Go-native JSON
passes actual Java projection/DiagnosticRing/chunks and the existing correlator;
full receive record213515bytes and ring+incident export427051bytes fit existing
limits. Received context/count/overwrite and pinned128 events survive end-to-end.
Existing11 parser/analyzer,2 continuation and5 new receive-correlator tests PASS.
Incremental receive-ring call benchmark: off0.25–0.32ns,on67.5–68.1ns,0alloc/op;
this excludes serialization/JNI/logcat and is not whole-client overhead acceptance.

Observation91 builds with169 JVM checks PASS; all other11 native libraries and
eight recovery source files remain byte-identical. Same-signer90→91 upgrade
verified23:02:52UTC after ordinary owner Disconnect, UID10283 unchanged:

- APK path `state-client-build/mesh-receive-path-20261020/delivery/FamilyConnect-0.1.18-beta91-receive-trace.apk`.
- SHA256 `6f4724ce31ec3ed99a209e8fb673bb6c0d15b0433df60850292aec8bd65cf490`.
- Native SHA256 `f257616827ad70cfaff8fbca3f080ce54e8c5abde973ebdec370c3a919d9fcab`.
- Same signer `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
- Android source inventory `2d1008b85b0b4827e6ce373d896f9e610576bc43ec44cd4202bddd37fd4b3422`.
- Paired gateway observation `cdbc59746ca1433e955a356ed227934e0aed48c31de824b41c7351a1e18d5c13`,
  inventory `fccf97f7ed22b7cf19fc3f671d17613ab47b9ae69385ade04e571ef220946554`.

Read-only22:59 and23:04:49 strict TLS/runtime/current material/publication PASS.
Observation gateway deployed23:03:27, PID3424571, invocation
`e20cb4ea67204500867d1554b8db9615`, active/NRestarts0. Fresh scoped stage pins exactb9
rollback; no old transition replay. Public release/CI/catalog/invitation unchanged.
Removal requires normal code>91, not downgrade.

One local candidate clears only an irrecoverably discarded, identified VP8 frame's
carrier assembly and fences late fragments with the existing bounded recent-message
history. It does not modify gap timer/RTO/windows/credit or release/consume early.
Local tests cover repeated partial-frame loss, fresh intact retry, duplicate-frame
discard not invalidating a valid fragment, bounded4096 history/expiry/concurrent
prune; affected local regressions pass. It is **not** in91 or the observation server,
and no physical gain is claimed. Missing first header remains unidentified.

## Physical gate and bounded baseline

Both captures are from the same media session `fc2fd498cf36cb207c231cf2b7d61efbf166b1f408d9749594a006a9634d7ff4`.
NL origin `b3f961e2dcf02e6d2c97615eeed93ea9`; Android origin
`5cda84b35fb001f0ff3bbb882309d14a`. Origins are process-local, never subtracted.

First64KiB request23:06:32 succeeds,39 DATA/consume/NL-release joins, but the meter's
preflight saw tun0 and postflight tun1. **Its stability gate remains failed.**
Fresh ordinary91 export SHA256 `c3dc2a3052886d25de97f8a0a1aacbfe0dfe55f272769c1162bf119004ff1b3b`
shows one connection: CONNECTING23:06:01.792; blocking VPN_CAPTURE_READY01.826;
SESSION_READY29.788; working VPN_CAPTURE_READY29.881; CONNECTED30.106. No recovery,
retry or failed-health series; subsequent DNS probes succeed. Exact unchanged
AutomaticVpnOwner.open/RestrictedTunnelEngine.up establish those two TUNs. Thus
this change is the initial blocking→working TUN transition, not a recurrent close.
Interface mapping is inferred from export plus topology, not a kernel event trace.
This does **not** reclassify the older unexplained22:14–22:21 TUN gap.

Initial local analysis failed on Go's omitted zero sequence despite `known:true`.
Raw capture preserved; parser corrected/tested, saved capture reanalysed without
another request. Unknown capture exit codes were not invented. Independent small
gate23:12:14:64KiB/HTTP200/4.408247s,57 DATA/consume/NL-release joins, zero parser or
correlation errors, stable tun1/cellular underlay321, exact gateway-PID attribution.
Only then one6MiB baseline cell ran23:12:49–23:13:56:

| Request | Body | TTFB(s) | Full request(s) | Goodput(Mbit/s) | Result |
|---|---:|---:|---:|---:|---|
|single|2097152|5.339693|37.072815|0.452548|200, complete|
|parallel0|2097152|0.823221|29.452626|0.569634|200, complete|
|parallel1|2097152|1.137066|29.616801|0.566476|200, complete|
|parallel aggregate|4194304|not combined|29.630000 common wall|1.132448|both complete|

Same HTTP1.1 endpoint, fresh connections, identity encoding, phone-side continuous
body reads. All3 requests attributed to gateway PID3424571; actual bulk Mux streams
97/107/109 each hand>1MiB, not merely three HTTP requests. Stable tun1/underlay321;
no reconnect/session change in this cell. No failed HTTP omitted. New total6.125MiB
including both small gates, not64MiB. Observed hashes are response evidence, not
independent origin digests. No body-only speed or cross-node RTT is asserted.

## New receiver localization and decision

41 NL/15 Android complete performance snapshots; parser/correlation errors0,
260 complete DATA/consume/NL-release chains. Receive events are sampled bounded
rings, not a full packet capture: Android3746 distinct events through71460,
27553 pre-capture/unobserved prefix and40161 interior missing events. The selected
local index ranges below are nevertheless contiguous in saved snapshots.

| DATA / carrier message | Confirmed Android boundary | NL outcome |
|---|---|---|
|614 /2969333433|RTP2352–2358 forms fragment0/mask1; fragment1 has2359–2363, then sequence_gap discard; retained indices28672–28732 contiguous|initial write completes9.95ms after submission; one retry; release after1.558s|
|1127 /2969334733|fragment0 RTP7890–7896/mask1; fragment1 only7897–7899 before gap discard; indices57963–58047 contiguous|initial local write9.28ms; one retry; release after1.252s|
|1294 /2969335140|gap skip discards fragment0 at last9908; fragments1/2 form mask110; RTP9909 enters reader0.417ms **after** discard and is old_rtp; indices68500–68567 contiguous|initial local write10.75ms; one fast retry; release after0.680s|

All three show incomplete/late forward RTP at our reader, followed by the existing
local frame-integrity decision. Other RTP continues. For1294 an already buffered
packet waits109.444ms for the gap; this is not a no-new-arrival deadlock. Do not
change100ms merely to rescue that one late packet. Source/OS/UDP/SRTP/Pion/SFU or
operator attribution remains unresolved; reader entry is not physical NIC entry.
There is also a bounded arrival-only deadline overshoot near614: RTP2405 queues
at Android416.631197s and releases416.799447s (168.250ms). Following complete
one-fragment messages2969333449/3450 wait168.238/162.418ms; no RTP reader event is
recorded between416.637115 and416.799429 in that contiguous ring interval. Thus
about68.25ms beyond the nominal100ms is observed locally, **not denied**. Those
messages have no observed DATA identity; the missing614 frame cannot be repaired
by releasing them earlier. Its relation to average throughput is not established;
the timer is not changed or advertised as a speed fix on this limited evidence.
NL RS local-write completion is observed for initial/retry attempts; complete
carrier-fragment records for every attempt are not retained. The consume of these
three sequences is outside the retained RS rings, **not zero or proven absent**.

Two slower controls do preserve the complete upper receive/ACK boundary:
- DATA649: two retries, initial-submission→release2.668195s; Android ready→consume
  48.333µs, once; ACK650/127 generation→local-write0.504ms. NL accepts it, base649→650,
  releases1 slot/16384bytes. Earlier attempts' Android RTP fate is not retained.
- DATA741: two retries, release2.319697s; ready→consume40.104µs, once;
  ACK742/127 generation→local-write0.515ms. NL accepts it, base741→742,
  releases1 slot/88bytes. Sender bookkeeping/consumer delay is not the observed
  failure for these controls. Matching generations remain possible matches, not
  globally unique ACK tokens or measured reverse one-way latency.

NL80.000s sampled interval has40.475s ready-window blocking,17.763s head-unconfirmed/
later-SACKed blocking; the latter overlaps the former. Android cumulative ready-
head wait increases0.193s. Observed bulk Mux zero-credit-ready waits are28.842s,
20.461s,15.515s for97/107/109; they can overlap ReliableStream stalls and each other,
and do not establish an independent credit bottleneck. They are not added together.

**Current receiver capacity counter is zero for the entire captured session**:
first-capacity incident remains unset and later_capacity=0 in every snapshot.
The discarded-frame cleanup candidate therefore has no demonstrated current
throughput constraint to remove. Its local171-case/5-skip regression and3 targeted
tests pass, but it is **not built/deployed**, not a failed live B trial and not an
accepted speed fix. The older capacity amplification evidence remains valid.
No arrival-timer, window, RTO, credit, batching, SACK or pacing change is shipped.
The evidence now localizes concrete forward frame losses and normal upper-layer
recovery; it does not prove one cause for every second of average throughput.

## Ordinary trace-off update and safe return

Normal beta92/code92 is built and signed from exact beta90 source, only version
metadata changed; all12 native libraries and recovery Java unchanged. Native
`dd722eada0da7c890a8d71a72099cba5d0bbac1ce73377bbdbc8e7b85d820c23`, no performance tag
or FamilyConnectPerf emitter,169 JVM tests PASS,16KiB alignment, same signer/package.
First build correctly stopped because the copied tree lacked its accepted Git
provenance metadata. Preserved failure; restored exact private build metadata,
left provenance checks intact, rerun PASS. This is not a runtime failure.

- Path `state-client-build/mesh-receive-path-20261020/normal92/delivery/FamilyConnect-0.1.18-beta92-stability.apk`.
- SHA256 `1e73167c8bfdba68f96249088cf08ea3dfb9d3614d5bedb8a0a7bdd8716e4e7b`.
- Source inventory `5ed7d2363bed681b4f073989841703dbfd7953f8b81fa8aa0f1e8b7acbca4c67`.
- Installed91→92 at23:23:16.841UTC after ordinary owner Disconnect, UID10283 retained.
  APK/native readback matches exactly; no uninstall, data clearing or downgrade.

23:17:54 strict current credentials/floors/TLS/publication readback PASS. Exactb9
returned23:24:06.746UTC, PID3437300/invocation`eb82442af5b84f52b4ac18d88af984b6`,
active/NRestarts0. Profile hash remains`3bce05fc3f1aa40b3f173332ffc76c65acd06b0231f4d8eb72196c8e59f91f31`;
ordinary forward publication readback23:25:09 has directory
`00767f5ba9f630137a9907f82e965ed0f3c1aea2834b3e4e69247767481ccf1f`, current material
expiry02:02:34UTC20.10. No rollback of floors/revocations or old transition replay.
Fresh92 READY preserves identity/key-binding/Support ID hashes. After manual
Connect and a bounded passive stable-TUN watch,23:26:36 control verifies DNS,
HTTPS200/210bytes/3.005787s, NL exit and20 current-PID socket observations. Extended
performance trace is OFF on both nodes. This is not overnight/repeated-fault or
speed acceptance. New application bytes total6422738 including this control.
No claim
that trace caused loss: only incremental ring cost was measured locally, not whole
client off/on throughput. Public/tester88/catalog/invitation artifacts unchanged.

Next distinguishing test inputs are frozen: normal92 APK/native above + exactb9
binary/source inventory, same owner cellular network and IPv4 Cloudflare HTTP1.1
single2MiB→parallel2×2MiB, bounded A/B/A with all failures counted. Compare only
with an explicitly selected, already authorized alternative placement, using the
same code and current credentials/floors. No alternative is selected/deployed;
do not repurpose a RU node or change exit country silently, buy hosting or alter
production routing. A placement comparison is not permission for another SACK fix.

## Current result

- DATA_HEAD: retry2 reached Android; partial VP8 discarded; head not covered by ACK597/220.
- CLASSIFICATION: forward RTP gap/late arrival → local frame discard, with bounded
  coverage; no confirmed consumer/reverse-ACK/bookkeeping defect in the controls.
- FIX: instrumentation verified end-to-end; cleanup candidate local-only; no physical
  speed improvement established and no functional candidate accepted/deployed.
- STATE: ordinary92 installed, exactb9/1011 restored, trace OFF; identity/READY and
  final small Android-TUN HTTPS PASS. No accepted functional throughput change.
- Prior unexplained TUN gap remains separate; it is not erased by later HTTPS success.
- IPv6/hosting/PERF-3B are out of scope. No purchases, migration, push or release.
