# RTP packet pacing — CLOSED / NOT_ACCEPTED; OFF/Q0 return confirmed

## Final manual return20.10 — confirmed, no new load

After the owner's ordinary reconnect, new VPN342 created17:50:03.626UTC,
cellular underlay327, session tag
`7e12971a537b7b41c1c831fda221839f75280cd2b336d3d31518ea2cd36f87e9`.
Old A2 Family TLS closes17:50:07.197810UTC; new authorization established
17:50:12.506089, Family TLS established17:50:24.594754 and gateway session
established17:50:25.943179. This is a new session, not reinterpretation of A2.

Eleven complete existing bounded snapshots17:53:13.944209–17:53:33.943953UTC
confirm **LEGACY64/65536** and absent `PacketPacing`, protocol errors **1→1**.
Distinct process-monotonic snapshot times3527866557051–3547866278743ns;
two journal records share wall-clock receipt time but are different snapshots.
Initial error cause/establishment value remains unknown; no load was run here.
The authenticated TLS result and exact Android/NL source mapping establish
65536-byte send/receive credit and ring on both endpoints; this is **not** an
independent live Android Mux counter export. Legacy ALPN is
`family-connect-5n3-test-v1`; the certificate authorization contract is unchanged.

The pinned exporter preserves nonnil PacketPacing; its absence means no pacer.
Pinned `gateway.Run` enables actual-write completion only with that nonnil
snapshot, so the active policy is **OFF/Q0**, not OBSERVE/Q1 at zero rate.
Final readback17:58:33.832473UTC confirms beta96/A0 APK/native, UID10283/PID30172,
gateway734b6ca6… PID4079583/invocation321b697f…, credentials hash and expiry unchanged.
All268 sealed source files still match the inventory; no source/build/install or
gateway restart.1011/Mux compatibility and beta96 bootstrap remain intact.
Phone interface tun0 at first readback becomes tun1 at final readback with the
same VPN342 creation and underlay327; exact transition cause/time unobserved.
Do not claim no TUN gaps across this return interval.

Existing bounded export was enabled17:53:12.638006–17:53:35.180956UTC
(22.543s including the read), then disabled in `finally`; no per-packet trace or
new collector daemon. First journal projection omitted long MESSAGE values;
one broader read with `--all` timed out15s. Both failures are retained, not counted
as transport failures. A bounded read of the **already recorded** same window
with `--all` and continuation reassembly recovered33 rows/11 snapshots with no
projection errors; no re-enable or repeated measurement traffic.
Final CHECK is read-only: `rtp-pacing=OFF`, `mux-profile=LEGACY64`,
`mux-counters=OFF`. Identity/Support ID bindings remain equal and owner not revoked.
Local/remote collectors, journal followers and phone meter absent at17:59:27UTC.

**Return COMPLETE; experiment CLOSED / NOT_ACCEPTED.** No manual action remains.
No bulk, speedtest, control request or added application measurement bytes;
total remains **33816576B /32.25MiB**, not a fresh speed result.
Private receipts under `state-client-build/rtp-pacing-20261020/`:
`manual-return-result.json`, `return-off-contract-proof.json`,
`return-off-runtime-proof-complete.json`, `return-off-closed-readback.json`,
`policy-ReturnClosed.json` and both return worker audits. Earlier failed projection,
preparation and `physical-final-result.json` remain immutable historical evidence.

## Final physical decision20.10 — all four phases complete

**NOT_ACCEPTED for the tested fixed4Mbit/s owner candidate.** This is a deployment
decision for this bounded experiment, not proof that every pacer is ineffective or
identification of a faulty external hop. Physical series is finished; no extra pairs,
rates, windows, receiver patches or bulk. Baseline-policy return is now
**confirmed OFF/Q0** in the new session documented above; A2 OBSERVE/Q1 is history.

### BEFORE_AFTER_SPEED_LATENCY_FAILURES

Same beta96/A0, LEGACY64, gateway process, IPv4 HTTP/1.1 Android-TUN meter/endpoint,
request order/instrumentation. A=OBSERVE/Q1; B=FIXED4M/Q1. Separate manual media
sessions, same cellular327, not a guarantee of identical SFU/ACK/network conditions.

| Phase / VPN | Mode | Single4MiB full / goodput | Parallel2×2MiB common / aggregate | Control64KiB full | Completed | Protocol errors observed |
|---|---|---|---|---:|---|---|
| A1 /338 | OBSERVE |49.567418s /0.676945Mbit/s|29.600s /1.133596Mbit/s|5.958610s|4/4|1→1 |
| B1 /339 | FIXED4M |51.545594s /0.650966Mbit/s|27.950s /1.200516Mbit/s|3.629614s|4/4|1→1 |
| B2 /340 | FIXED4M |53.901942s /0.622509Mbit/s|30.180s /1.111810Mbit/s|4.974325s|4/4|1→1 |
| A2 /341 | OBSERVE |49.597861s /0.676530Mbit/s|25.660s /1.307655Mbit/s|4.625676s|4/4|1→1 |

| Paired order | B/A single goodput | B/A aggregate goodput | B/A control full latency |
|---|---:|---:|---:|
| A1/B1 |−3.84%|+5.90%|−39.09% |
| B2/A2 |−7.99%|−14.98%|+7.54% |

No repeatable speed gain: single is lower in both B observations; aggregate changes
direction. Latency improvement also does not repeat and is not obtained without
observed single-speed loss. Thus neither speed nor latency-only acceptance passes.
All16 requests completed; no excluded failed request/retry of a failed request,
local write/admission errors or measured protocol-error increments. Each session
already had1 error at its first observation; establishment and cause are unknown,
not silently reset/inherited or automatically attributed to pacing. Full control
HTTPS duration is application latency, not RTT. No observed **in-load** media/VPN
reconnect; sub-sample gaps are not excluded. B2 and A2 pre-load tun0→tun1 transitions
at unchanged VPN identity/underlay are retained, not called absence of TUN changes.

### BURST_EVIDENCE / ACTUAL_PACER_AND_CC

Accepted source has no effective packet pacer/GCC;2ms pause follows a whole frame.
RegisterDefaultInterceptors and announced feedback do not establish adaptive CC.
Tested fixed500000 RTP B/s pacing smooths actual **local** writes:

| Phase | Lifetime peak packets per1/5/20ms fixed bins | Source queue max / lifetime age | Shared process CPU(one core) / max RSS |
|---|---|---|---|
| A1 |8 /15 /44|3frames /19.232378ms|6.475% /49128KiB |
| B1 |2 /3 /8|3frames /52.936181ms|7.572% /51620KiB |
| B2 |2 /3 /8|3frames /55.295645ms|7.682% /51852KiB |
| A2 |7 /15 /38|3frames /14.513871ms|7.166% /51680KiB |

Fixed bins are not sliding windows; lifetime maxima are not request-local peak
deltas. B increases source queue age despite smaller packet bursts. Average RTP
offered single A1/B1/B2/A2=0.806122/0.805861/0.774588/0.833430Mbit/s;
parallel=1.305894/1.332712/1.221036/1.393005Mbit/s. Local SRTP write-byte counters
and RTCP are saved, but total UDP/IP wire overhead and SFU/Android receipt are not
measured by these counters. Publisher↔SFU NACK is observed, TWCC feedback0 across
captures despite negotiated support; no REMB/GCC/end-to-end capacity estimate.
No new Android per-frame gap/drop export: smoothing is proven locally, receiver
loss-mechanism reduction is not established. Do not equate NACK with any late packet.

### CREDIT / RS / BACKGROUND — scoped counter comparison

| Phase | Single credit / RS ready-full | Parallel stream credit / shared RS ready-full | RS retry bytes single / parallel | Other handed download bytes single / parallel |
|---|---|---|---|---|
| A1 |89.21% /25.92%|52.75%,53.63% /86.07%|700061 /652370|30384 /112532 |
| B1 |84.59% /25.59%|39.88%,37.98% /50.81%|741642 /520038|208428 /51021 |
| B2 |84.01% /30.79%|51.69%,38.13% /49.28%|844466 /659943|90289 /87729 |
| A2 |83.18% /41.43%|65.01%,57.80% /78.60%|680162 /429575|231653 /4894 |

Percentages use each exact process-monotonic before/after bracket in the phase
receipts, not request time or unrelated lifetime intervals. Parallel credit/RS
can be lower with pacing without better delivery. Single retries do not improve
in either pair; parallel reduction does not repeat. Counter brackets include
background/snapshot edges and can overlap; never sum overlapping Mux/RS waits.
Background counts/bytes differ; bytes are other handed download DATA including
TLS overhead, not all bidirectional activity. No causal claim from stream counts.

### ONE_TARGETED_CHANGE / QUEUE_RETRY_SAFETY

One fixed-rate synchronous packet pacer at the bound Pion RTP writer, including
ordinary RTP retransmission path; RTCP bypass and finite capacity/deadline preserved.
Common actual-local-write completion prerequisite Q1 was explicit in **both** A/B,
not hidden only in B. Exact Q0, OFF/Q0, OBSERVE/Q1 and FIXED4M/Q1 local fixtures
remain separately saved.613 local cases/subtests, pinned race/close/recovery tests
reused unchanged; no new code delta/tests required for these physical phases.
Pending max1/1200B observed in every phase, final0; all measured streams closed/
empty, sampled RS local queue0B, no new write/recovery failure observed. These
snapshots do not replace local theoretical bounds or prove whole-process boundedness.
Q1 itself is not independently speed-accepted by this comparison; OFF restores Q0.
The patch and exact source/test evidence remain separate from accepted baseline.

### CURRENT_RUNTIME / RETURN

Owner beta96-bootstrap/A0 APK
`07a90f03269e1df683289bc1fbe7fa7e88647c5629f71db1f784d6566aa9228d`,
native66a9d18d… unchanged, same package/signer/UID/identity/Support ID.
Loaded gateway `734b6ca6eb42be0367b703b657be87c624f3500ae408bbd771309ffaeb86128e`,
PID4079583/invocation321b697f… unchanged throughout all four phases, retaining1011
and Mux compatibility. Sealed source inventory
`faf60996252fdb09ddf4890dbe82c04d5a0212418b488d6459003a3898ea720b`;
patch `tests/fixtures/rtp_pacing/packet-pacing.patch` SHA256
`15b98c41b0c569ffe1775f34391b7b8dd8b7e530ef4056fdaf10d03cea99ff17`.
Exact272bbc… compatible rollback remains available but is **not** performed;
no old b9 binary, downgrade, new APK, identity/credential/floor changes or push.

Post-return readback17:58:33UTC confirms same device/gateway/current credentials,
new VPN342. Active **OFF/Q0, LEGACY64/65536**, receiverA0; protected next-session
OFF/Q0, CREDIT128 OFF, bounded export OFF. No active session was reinterpreted.
All collectors joined, no background waiting. Total **32.25/64MiB**
(32MiB bulk +0.25MiB controls), no additional speed/control traffic.
Physical result is closed as NOT_ACCEPTED; return is complete through actual
authenticated runtime/source proof, not just the operator file or CONNECTED.
No new load, build, install, restart or remaining manual action.

Receipts: `state-client-build/rtp-pacing-20261020/physical-final-result.json`,
`manual-return-result.json`, `manual-a2-result.json`, historical
`manual-return-preparation.json`, all four `normalized.json`
captures and exact request timestamps. Historical phase/preparation entries below
are retained, not instructions to replay them. Tester cellular bootstrap is not
validated by this owner speed comparison.

One **future distinguishing test**, not started: compare the same accepted OFF/Q0
code/meter over IPv4 at another explicitly authorized placement. No purchase,
production migration, IPv6, new pacing rate, FEC or RS-window experiment here.

## A2 final control20.10,17:41:47–17:43:07UTC

Manual VPN341 created17:36:50.066UTC, owner tag
`cf6d17acc8a36e1e05f41710973cddc486bfa63db5c9589e95f8a03f9e73a0b2`.
Actual rate0/LEGACY64/65536 verified before load through authenticated runtime and
pinned shared ALPN mapping; not an independent Android live-counter read. Initial
readback tun0, preflight17:41:39.885771UTC and load tun1; same VPN341/underlay327,
exact transition time/cause unknown, as in B2. Gate and all existing load checks
remain on tun1; source/meter unchanged.4/4 HTTP200, TLS/full length verified.

| Request | curl full | TTFB | Body interval | Goodput |
|---|---:|---:|---:|---:|
| Control64KiB |4.625676s|3.712491s|0.913185s|0.113343Mbit/s |
| Single4MiB |49.597861s|2.220854s|47.377007s|0.676530Mbit/s |
| Parallel2MiB #0 |25.360459s|0.993598s|24.366861s|0.661550Mbit/s |
| Parallel2MiB #1 |25.625154s|1.293612s|24.331542s|0.654717Mbit/s |

Single phone wall49.620s, parallel common25.660s/aggregate1.307655Mbit/s. Real
stream sets49/51/{65,67}, endpoint sockets1/1/2, all closed/empty finally. Parallel
request-to-ID mapping unresolved. Full-body hash observed, not origin byte-exact proof.

| Scope | Monotonic counter bracket | Credit ready-zero waits | RS ready-full | Other handed download / background streams |
|---|---:|---|---|---|
| Control |8.000189084s|49:0.241026239s /3.01%|4.68%|2863B /5–6 |
| Single |52.000036512s|51:43.251934151s /83.18%|21.542021304s /41.43%|231653B /4–7 |
| Parallel |27.999333261s|65:18.201889887s /65.01%;67:16.184064552s /57.80%|22.006325103s /78.60%|4894B /5–6 |

Stream counters wholly inside their brackets (absent in before-snapshot). Single
RS new/retry4465137/680162B, parallel4238711/429575B; head-unconfirmed/later-SACKed
wait21.65%/37.07%, overlapping other waits. Exact node/UTC bounds, packet spacing/
queue histograms, RTP/local-write byte rates and stage timings in `A2/normalized.json`.
Scheduler-lateness0 for uncapped A2, no local write/rejection increments. Publisher
RTCP RR277→369,NACK1→1,TWCC0→0,REMB0→0,PLI13→19.47 snapshots, no other performance
tag or journal parse/cap/partial errors. Sampled retained Mux491432/RS98612B,
RS local queued0; whole-process CPU7.166%, RSS51680KiB. Protocol errors first/
pre-control/pre-bulk/after1/1/1/1; establishment unknown. Collector joined/export OFF.

## B2 physical repeat20.10,17:29:33–17:31:03UTC — retained preceding result

Owner manually reconnected: VPN340 created17:28:44.386UTC, cellular underlay327.
Fresh owner tag `e2d021e8914bc5d045c17831700dbb25a4e3fdb76b5e76209911a3fa9e1e19fd`
passed the pre-load gate: **FIXED4M/rate500000 RTP B/s, LEGACY64/65536**.
Both endpoint window contracts follow the actual authenticated Family TLS/Mux
selection and pinned shared ALPN mapping, not an independent Android live counter.
Same96/A0 APK/native and gateway734b6ca6…/PID4079583/invocation321b697f…/credentials.
No implementation/build/install/deployment/restart change or repeat of prior phases.

**Pre-load topology qualification:** `btwo-readback.json` reports tun0; existing
measurement preflight17:29:25.963736UTC and gate/load report tun1. VPN340/handle,
creation time, owner UID and underlying327 remain the same. Exact interface-transition
time/cause are unknown. Readback also changes a nominal LinkDnBandwidth estimate,
which is not a throughput measurement. The initial whole-VPN-string equality check
correctly rejected this difference during receipt assembly; evidence is retained,
identity/creation/underlay and the limited changed fields verified instead. No
instrumentation/gate modification or extra traffic to make the check pass.
Do not claim no TUN changes throughout the whole turn. **During the measured load**,
existing checks observe tun1/same VPN and one media tag, no reconnect; sub-sample
gaps are not excluded.

Same accepted HTTP/1.1 Android-TUN endpoint/meter/order/instrumentation,150s ceiling,
no request retries. **4/4 complete**, HTTP200/TLS verification/full body lengths;
observed body hashes are not origin byte-exact checksums.

| Request | Complete | curl full time | TTFB | Body interval | Goodput |
|---|---|---:|---:|---:|---:|
| Control64KiB | yes |4.974325s|4.109294s|0.865031s|0.105399Mbit/s |
| Single4MiB | yes |53.901942s|1.946837s|51.955105s|0.622509Mbit/s |
| Parallel2MiB #0 | yes |29.783513s|0.963258s|28.820255s|0.563305Mbit/s |
| Parallel2MiB #1 | yes |30.154302s|1.203112s|28.951190s|0.556379Mbit/s |

Aggregate **1.111810Mbit/s /30.180s** common phone-uptime interval; single phone
wall53.920s. Real matching stream sets17/19/{29,31}, observed endpoint sockets1/1/2.
Equal parallel request↔stream mapping not independently resolved. All four measured
streams closed/empty by the final snapshot;17/19 were still open in their immediate
after-bracket samples. Control is full application latency, not RTT.

| Scope | Exact monotonic counter bracket | Credit ready-zero waits | RS ready-full | Other handed download DATA / background streams |
|---|---:|---|---|---|
| Control |5.999747143s|17:0.082818141s /1.38%|2.43%|0B /6–7 |
| Single |55.999950239s|19:47.043785914s /84.01%|17.242991156s /30.79%|90289B /6–7 |
| Parallel |33.999687486s|29:17.575860202s /51.69%;31:12.963515853s /38.13%|16.756705317s /49.28%|87729B /6–7 |

New streams absent in before-snapshots; their waits are within these process-monotonic
brackets. Exact timestamps retained in `B2/normalized.json`. Brackets include edges
and background and overlap one another; neither brackets nor overlapping Mux/RS
waits are added. Background is other handed download DATA including TLS overhead,
not all bidirectional traffic; open stream counts alone do not establish load.
Single RS new/retry4323526/844466B, parallel4323310/659943B. Head-unconfirmed/
later-SACKed blocked fractions16.26%/27.23%, overlapping ready-full/credit waits.

Local RTP offered single0.774588/parallel1.221036Mbit/s,5690/5175 packet writes;
local write rate0.787593/1.240518Mbit/s, not total UDP/IP wire overhead or receipt.
Lifetime peaks by phase end2packets/1236B per1ms,3/3545B per5ms,8/9545B per20ms.
Source queue lifetime max3frames/55.295645ms age, sampled max2/3frames in bulk
brackets; pending max1/1200B and final0. No local write/admission error or rejection.
Pacing wait sums11.085776s/10.762977s; scheduler-lateness sums separately2.117320s/
2.071849s, lifetime max8.349495ms. These are per-write local observations, not
end-to-end delays to add to Mux/RS; peaks are lifetime, not request-local differences.
Negotiated NACK/TWCC=true, REMB=false; actual publisher RTCP RR31→131, NACK1→1,
TWCC0→0, REMB0→0, PLI3→7. No Android per-frame loss proof or adaptive CC claim.

Protocol errors establishment unknown; first/pre-control/pre-bulk/after **1/1/1/1**.
No measured increment; initial error source remains unknown. Whole-process CPU
7.682% of one core, RSS max51852KiB; sampled retained Mux622504/RS99690B and
RS local queue0B, not total process-memory bounds.51 snapshots, no other observed
performance tag, parse errors/cap/partial fragments0; collector joined/export OFF.

| Phase | Mode | Single Mbit/s | Aggregate Mbit/s | Control full seconds | Completed |
|---|---|---:|---:|---:|---|
| A1 | OBSERVE |0.676945|1.133596|5.958610|4/4 |
| B1 | FIXED4M |0.650966|1.200516|3.629614|4/4 |
| B2 | FIXED4M |0.622509|1.111810|4.974325|4/4 |
| A2 | OBSERVE |NOT_RUN|NOT_RUN|NOT_RUN|NOT_RUN |

**INCONCLUSIVE; second pair incomplete.** B1/B2 variation is not a second paired
gain, and smoother writes alone are not acceptance. Same common Q1 correctness
prerequisite in A/B; A is not exact accepted Q0. Background/media conditions differ.
Budget **24.1875/64MiB**,39.8125MiB left; A2 needs8.0625MiB, no extra probes/repeats.

Post-readback17:31:57UTC: unchanged96/gateway/credentials/VPN340, export OFF.
Existing protected owner-only selector now prepares **OBSERVE/rate0 only for NEXT
A2 session**; current last observed B2 remains FIXED4M, never reinterpreted in place.
LEGACY64/CREDIT128 OFF throughout. No collector or background wait. Receipts:
`state-client-build/rtp-pacing-20261020/manual-b2-result.json`,
`manual-a2-preparation.json`, `policy-prepareAtwo.json`; source hashes match A1/B1.
Next: ordinary owner Disconnect→Connect, verify fresh OBSERVE/65536, run A2 only,
then decide the bounded result/return. Do not add more phases, rates or transport changes.

## B1 physical fixed pacing20.10,17:18–17:19UTC — retained preceding result

Manual reconnect created VPN339 at17:15:08.306UTC, same cellular327/tun1.
New authenticated owner tag
`0dc4f581545d976c1ccf5835ba41710f9f8f8733323836b404d1607133aa0738`
passed the pre-load gate: **FIXED4M/rate500000 RTP B/s, LEGACY64/65536**.
The actual Family TLS/Mux selection and exact pinned shared ALPN mapping bind
both endpoint windows to65536; this is not an independent Android live-counter
read. Same96/A0 APK/native, gateway734b6ca6… PID4079583/invocation321b697f… and
credential profile before/after. No new build, install, deployment or restart.

Same unmodified meter/instrumentation/order as A1; **4/4 complete**, HTTP200,
complete HTTPS body lengths and TLS verification, no retries of failed requests.

| Request | Complete | curl full time | TTFB | Body interval | Goodput |
|---|---|---:|---:|---:|---:|
| Control64KiB | yes |3.629614s|2.727245s|0.902369s|0.144447Mbit/s |
| Single4MiB | yes |51.545594s|2.160921s|49.384673s|0.650966Mbit/s |
| Parallel2MiB #0 | yes |27.540923s|0.591163s|26.949760s|0.609174Mbit/s |
| Parallel2MiB #1 | yes |27.930981s|0.858252s|27.072729s|0.600667Mbit/s |

Parallel aggregate **1.200516Mbit/s /27.950s** common phone-uptime interval;
single phone wall51.570s. Stream sets41/43/{53,55}, observed endpoint sockets1/1/2;
parallel request↔ID mapping remains unresolved. All four streams closed/empty
by final snapshot. No observed VPN/media reconnect or TUN gap; sampling cannot
exclude sub-sample gaps. Control full HTTPS time is application latency, not RTT.

| Scope | Exact monotonic counter bracket | Credit ready-zero waits | RS ready-full | Other handed download DATA / background streams |
|---|---:|---|---|---|
| Control |5.999811542s|41:0.044403502s /0.74%|1.88%|2863B /12 |
| Single |53.999828642s|43:45.680567465s /84.59%|13.818961297s /25.59%|208428B /11–13 |
| Parallel |29.999838953s|53:11.962657022s /39.88%;55:11.393163543s /37.98%|15.243384072s /50.81%|51021B /11–13 |

Each stream is new/absent in the before-snapshot. Exact process node_ns and UTC
request/counter bounds are in `B1/normalized.json`; waits are normalized to those
counter brackets, not request durations. Adjacent brackets overlap; do not sum
them or overlapping Mux/RS waits. Background bytes include other handed download
DATA/TLS overhead, not all bidirectional traffic; stream counts alone are not load.
RS new/retry bytes single4443203/741642, parallel4285613/520038. Head-unconfirmed/
later-SACKed wait14.35%/36.83% overlaps ready-full and credit wait.

**Local burst smoothing observed, not speed acceptance:** RTP offered rates
single0.805861/parallel1.332712Mbit/s versus A1 0.806122/1.305894. Packet writes
5679/4933. By capture end, lifetime fixed-bin maxima2packets/1200B per1ms,
3/2521B per5ms,8/9545B per20ms (A1 8/8620,15/16965,44/50530). Lifetime maxima
are not request-local peaks. Carrier queue max3frames and52.936181ms lifetime
age versus A1 19.232378ms; sample max1frame. Pending packet max1/1200B, final0.
Local admission/write errors and rejections remain0. Packet pacing wait sums
11.147434s/10.432517s within the single/parallel brackets; scheduler-lateness
sums separately2.172149s/2.051857s, lifetime max10.157692ms. These are local
per-write observations, not additional end-to-end waits to add to Mux/RS.
No promise of millisecond-exact scheduling or total UDP/IP wire-overhead accounting.

Publisher feedback negotiated NACK/TWCC=true, REMB=false; actual lifetime
RR154→248, NACK1→2, TWCC0→0, REMB0→0, PLI11→15. This is the publisher↔SFU
leg, not receiver-loss proof, NACK source attribution or adaptive congestion control.
Fresh Android per-frame drop/gap evidence is still unavailable.
Protocol errors establishment unknown; first/pre-control/pre-bulk/after1/1/1/1,
no measured increment. The initial error cannot be attributed to fixed pacing
from these observations. Whole-process CPU7.572% of one core, RSS max51620KiB;
sampled Mux/RS retained936360/98612B, RS local queue0B. No unbounded accumulation
observed; these are sampled retained values, not full process memory bounds.

### First pair A1/B1 — not an acceptance decision

| Metric | A1 OBSERVE | B1 FIXED4M | B/A change |
|---|---:|---:|---:|
| Single full goodput |0.676945Mbit/s|0.650966Mbit/s|−3.84% |
| Parallel aggregate |1.133596Mbit/s|1.200516Mbit/s|+5.90% |
| Control full latency |5.958610s|3.629614s|−39.09% |
| Complete requests |4/4|4/4|no transfer failures |
| Protocol errors during observation |1→1|1→1|no increment |

Single credit89.21→84.59%, RS ready-full25.92→25.59%; parallel credit52.75/53.63→
39.88/37.98%, RS86.07→50.81%. Single retry bytes increased700061→741642;
parallel decreased652370→520038. Different media sessions and background bytes
(single30384→208428B, parallel112532→51021B) prevent causal attribution of the
small goodput changes. A uses the explicit shared Q1 local-write-completion
prerequisite, not accepted Q0; this comparison isolates incremental pacing over Q1.
**Speed INCONCLUSIVE**, no serious correctness/regression stop observed in B1.

Budget **16.125/64MiB**,47.875MiB remaining; no additional probes.48 snapshots,
no journal parse errors/cap/partial fragment. Collector joined and temporary export
OFF. Post-readback17:19:51UTC confirms unchanged phone/gateway/session/credentials.
Existing owner-only setting remains FIXED4M for the **next new B2 session**;
LEGACY64/CREDIT128 OFF. No new setting, active-session reinterpretation or background
wait. B2 then A2 provides the opposite order; do not repeat A1/B1 or add more rates.
Receipts: `state-client-build/rtp-pacing-20261020/manual-b1-result.json`,
`manual-b2-preparation.json`, `B1/normalized.json`; source hashes match A1.
Next: owner ordinary Disconnect→Connect, then verify fresh rate500000/65536 before
B2 only. Safe OFF/new-session return remains available if regression appears.

## A1 physical control20.10,17:04–17:06UTC — retained preceding result

Owner's manual reconnect created VPN338 at16:59:37.833UTC, cellular327/tun1.
Actual dedicated session `81425f7f2d62cff77ccdd5275997a9f12b1d68255628bc1dd59f9542063962ba`
exports **OBSERVE/rate0 and LEGACY64/65536**. Authenticated TLS→Mux construction
and exact shared ALPN mapping in pinned Android/server bind both endpoints to65536;
not merely CONNECTED/preference, and not an independent Android live-counter read.
Only the authenticated owner is selected for PacketPacing. No other performance
session tag in this capture. Same96/A0 APK/native and gateway734b6ca6…,
PID4079583/invocation321b697f… throughout. No observed VPN/media reconnect or TUN
gap in the sampled interval; short gaps below sampling are not excluded.

Existing phone HTTP/1.1 TUN meter, same endpoint/no retries/150s request ceiling;
control64KiB → single4MiB → parallel2×2MiB. **4/4 complete, no transfer errors**,
full HTTPS bodies/lengths verified. Body hash is observed, not an origin checksum.

| Request | Complete | curl full time | TTFB | Body interval | Goodput |
|---|---|---:|---:|---:|---:|
| Control64KiB | yes |5.958610s|4.288470s|1.670140s|0.087988Mbit/s |
| Single4MiB | yes |49.567418s|2.218735s|47.348683s|0.676945Mbit/s |
| Parallel2MiB #0 | yes |29.206603s|0.633502s|28.573101s|0.574432Mbit/s |
| Parallel2MiB #1 | yes |29.572035s|0.914337s|28.657698s|0.567334Mbit/s |

Parallel aggregate **1.133596Mbit/s over29.600s** common phone-uptime interval;
single phone wall49.590s. Do not call control HTTPS full time an RTT. All requests
open one real connection; observed gateway endpoint sockets1/1/2. New matching
Mux stream sets: control51, single55, parallel{65,67}. Equal parallel requests are
not independently mapped one-to-one to those IDs. Every measured stream is closed
and empty in the final capture (67 was still open in the earlier bracketing snapshot).

| Scope | Exact counter interval | Credit ready-zero waits | RS ready-full | Other handed download DATA / active background streams |
|---|---|---|---|---|
| Control |8.002174419s|51:0.112052496s /1.40%|18.56%|4846B /7 |
| Single |51.999562925s|55:46.388786222s /89.21%|13.477621286s /25.92%|30384B /6–8 |
| Parallel |32.000172511s|65:16.880610165s /52.75%;67:17.161791632s /53.63%|27.542713262s /86.07%|112532B /7–8 |

Each measured stream was absent in its before-snapshot, so its lifetime wait is
wholly within the stated bracket. Percentages use that **process-monotonic bracket**,
not curl/request time. Exact node/UTC bounds in `A1/normalized.json`. Neighboring
brackets overlap: do not sum them or sum overlapping credit/RS waits. Background
counts are not load estimates; bytes are other Mux handed download DATA including
TLS overhead, not all bidirectional traffic. RS new/retry bytes within single bracket
4279394/700061; parallel4348396/652370. RS head-unconfirmed/later-SACKed blocked
fractions14.55%/42.00%, overlap with the ready-full/credit waits retained.

**Actual burst evidence, local NL write boundary:** single RTP offered0.806122Mbit/s,
parallel1.305894Mbit/s over matching brackets,5603/5306 packet writes. By phase end
fixed-bin lifetime maxima are8 packets/8620B per1ms,15/16965B per5ms,44/50530B
per20ms; not subtractable per-request peaks. Source queue lifetime max3frames and
19.232378ms age; sampled queue max2frames, pending packet lifetime max1/1200B.
No local write errors/rejections0→0. These are local writes, not SFU/Android receipt.
Do not infer total UDP/IP wire overhead from the recorded RTP/SRTP return-byte counts.

Negotiated publisher feedback flags NACK=true,TWCC=true,REMB=false. Actual received
RTCP lifetime before→after: RR268→366, NACK1→3, TWCC0→0, REMB0→0, PLI6→12.
Two NACK messages observed in the capture, not proof of particular Android gap
recovery. RTX SSRC counter alone cannot identify same-SSRC retransmissions. No GCC
or end-to-end capacity estimate follows from announced TWCC. Fresh Android per-frame
loss/discard export remains unavailable, explicitly limiting mechanism attribution.

Protocol errors: establishment **unknown**, first observed/pre-control/pre-bulk/
after **1/1/1/1**. The error belongs to this session before load; its cause is unknown,
not assumed inherited from an old session and not attributed to untested FIXED4M.
Shared gateway CPU6.475% of one core over capture; RSS max49128KiB; sampled Mux/RS
retained688040/98612B, local RS queued0B. This is process/snapshot scope, not a whole
system bound or a per-user memory allocation estimate.

**A1 saved, B1 NOT_RUN.** Budget8.0625/64MiB,55.9375MiB remaining. Capture ended
normally, no cap/partial journal fragment;50 performance snapshots, parser errors0.
Temporary export OFF; no collector/background wait. Post-readback17:08:13UTC
same96/gateway/VPN338. Existing protected policy prepares **FIXED4M only for the
next owner session**; last observed current session stays OBSERVE. LEGACY64/128 OFF.
OFF here is the `mux-counters` export switch: bounded in-memory OBSERVE counters
remain part of the current session until it closes; no background journal collector
or extended recording is left running.
Next manual action: Disconnect→Connect, reply connected; verify a new session with
**65536** and RateBytesPerSecond500000 before B1. Window never changes in this experiment.
Continuation `manual-b1-preparation.json`; full data `A1/normalized.json` and
`manual-a1-result.json` in the existing capsule. Six offline mode/window/tag/staleness
gate checks PASS. No binary/APK/security change in this phase. Speed acceptance
remains **INCONCLUSIVE** until paired results, not inferred from this control alone.

## Authorized rollout20.10,16:54UTC — retained deployment receipt

Owner explicitly confirmed no tester was active and authorized the switch. Exactly
one successful ordinary gateway restart loaded candidate
`734b6ca6eb42be0367b703b657be87c624f3500ae408bbd771309ffaeb86128e` at16:54:26UTC.
PID4079583, invocation `321b697f7a6b4db6920aa51267d762b6`, NRestarts0.
Current executable/argv/systemd configuration verified; unchanged credential-profile
SHA `fb3f2341a3fcb359f90838a83daa1583625d37b63459907e14f6f4bd7058e016`.
Fresh pre/post Family TLS/runtime binding, authority/leaf/CRL validity and RU/NL
directory publication checks PASS. Post-start directory SHA
`b5614eedec328d9f6e6a51960e854df819f9a0875560d210f799443f6c7c8f9c`;
existing credential expiry19:36:22UTC, no renewal/identity/floor rollback.

First transition invocation failed during RU SSH banner exchange through NL, before
remote transition. Durable NL readback proved no deploy-intent, same running
baseline/PID/invocation/profile. Only then a separately recorded resumed attempt
used ordinary direct SSH to the same authorized RU host; original RU/NL lock,
credential and hash barriers were preserved. No blind replay or extra restart.
Both locks released. Failed attempt and readback retained under `transitions/`.

Readback16:56:18UTC confirms unchanged owner96 APK/native/UID10283/PID30172,
same VPN337 (not a new owner session). **No APK build/install was necessary**:
this is a server-side download experiment. Protected selector now targets only the
existing owner's authenticated Ed25519 public-key hash, derived from current
read-only identity data and matched to the saved owner binding/Support-ID hashes.
No grant/authentication rule changed; other peers/default seed stay OFF.
Prepared **OBSERVE for the next owner session**, LEGACY64 preference unchanged,
CREDIT128 OFF, `mux-counters` OFF. Active session mode/window were not reinterpreted
or inferred from CONNECTED. The32-byte selector is stored without a newline to
respect the existing parser's32-byte limit.

**A1 is not measured.** Physical speed INCONCLUSIVE/NOT_RUN,0/64MiB. No collector,
phone input injection, background wait or measurement request. Next action: owner
normally Disconnect→Connect, then replies connected. Verify a new session,
actual LEGACY64/65536 both endpoint contracts and actual OBSERVE snapshot before
any A1 bulk. A remains the common Q1 correctness control described below, not Q0.
Use the same existing TUN meter for A1/B1/B2/A2; never turn CREDIT128 on.

Saved continuation: `state-client-build/rtp-pacing-20261020/manual-a1-preparation.json`.
New adapters `tests/fixtures/rtp_pacing/{rollout,policy}.py` reuse the ordinary
transition and existing protected operator files, not a new remote API/exporter.
Rollback copy remains exact272bbc… under
`/opt/apps/family_connect/friends-restricted/bin/.rtp-pacing-20261020-stage/baseline`.
OFF + ordinary new owner session restores Q0 policy without another restart;
binary rollback only if necessary, serialized/coordinated, retaining current
credentials and directory lifecycle. Never restore a pre-restart directory snapshot.

## Historical local preparation — unchanged test evidence

20.10.2026. **INCONCLUSIVE for speed; local implementation/validation complete.**
No live deployment, restart, profile change, APK build/install, public release or push.
The tester's beta96 cellular/bootstrap attempt is independent. A shared restart to
load this candidate must be coordinated after that attempt, not performed silently.
Measurement traffic in this task: **0/64MiB**. No collector/background wait remains.

## Current runtime and exact artifacts

Readbacks15:50:53 and16:26:17UTC match: owner beta96-bootstrap, UID10283/PID30172,
APK `07a90f03269e1df683289bc1fbe7fa7e88647c5629f71db1f784d6566aa9228d`,
native `66a9d18d04ff71100df0144228db05decb970aea71b6d277ec321b1c6c240c63`.
VPN337 exists over cellular327; this is not fresh proof of media-session ALPN,
actual65536 windows or bootstrap field acceptance. Last confirmed window contract
is LEGACY64; current protected preference LEGACY64, CREDIT128/counters OFF.
Before future bulk, verify actual session/profile/mode on both endpoints again.

NL service `family-connect-restricted-bootstrap.service`, PID4030121,
invocation `6679479d4fee495bb7e39e65c88a7aa2`, NRestarts0; exact current binary:
`272bbc3fed90bbcf740a58f812e93511c976c114e2190f2c8711b55fa0dfb0c4`.
Its15:36:33UTC start predates this task; do not attribute that change from the old
Mux-return receipt to pacing. Credential expiry19:36:22UTC is a readback, not a
deployment authorization; use fresh credentials/readback at any later switch.
No identity, authority, CRL, revocation, floor, renewal or registration mutation.

| Artifact | Exact reference / SHA256 |
|---|---|
| Accepted source | `state-client-build/mux-profile-20261020/gateway-source/carrier`, every file verified against `negotiated-build.json` |
| Candidate source | `state-client-build/rtp-pacing-20261020/candidate` |
| Tracked patch | `tests/fixtures/rtp_pacing/packet-pacing.patch` |
| Patch SHA256 | `15b98c41b0c569ffe1775f34391b7b8dd8b7e530ef4056fdaf10d03cea99ff17` |
| Source inventory SHA256 | `faf60996252fdb09ddf4890dbe82c04d5a0212418b488d6459003a3898ea720b` |
| Built server binary — NOT installed | `state-client-build/rtp-pacing-20261020/gateway-pacing` |
| Binary SHA256 | `734b6ca6eb42be0367b703b657be87c624f3500ae408bbd771309ffaeb86128e` |

Full22-file delta, protected-file hashes, test logs and data:
[evidence](2026-10-20-rtp-packet-pacing.evidence.json), local capsule
`state-client-build/rtp-pacing-20261020/`. Frozen patch reapplies to all268 inventory
files exactly; repeat race checks passed. No published-main substitution.
Pinned dependencies, A0 `telemost/rtp.go`, VP8, Mux64, RS protocol/engine,
bootstrap-broker main/seed recovery and beta96 native remain unchanged.
Prior deadline, SACK/read-alignment, Mux128 and cleanup experiments stay separate.

## ACTUAL_PACER_AND_CC

Exact `telemost/signaling.go`: bounded256-frame queue → writerLoop → WriteSample →
pinned Pion packetizer → consecutive WriteRTP calls. The2ms sleep is **between
frames**, not packets. An8192B carrier fragment +24B header +17B VP8 framing is
8233B and normally7 RTP packets at the current MTU. Keepalive keyframes every2s
use the same writer. Nominal33ms sample duration/timestamps are not changed.

Pinned webrtc/v4 v4.2.15, interceptor v0.1.45, rtp v1.10.2:
RegisterDefaultInterceptors installs NACK, SR/RR, stats and TWCC feedback reporting,
**not a packet pacer or GCC/BWE controller**. Outbound TWCC header stamping is a
separate configuration, not enabled by that call. Discarding sender.Read's result
does not bypass interceptors: NACK can already have been processed and retransmitted.
No existing active rate adaptation was found in this exact send path.

Queues: RS retained/window → carrier256 frames → immediate packet writes → NACK
cache1024 packets/local stream → unchanged SRTP/ICE/UDP/kernel. Original NACK
responder creates workers for NACK feedback; it retains the inner RTP writer.
The candidate interceptor is inside that responder, so retransmissions share its
budget with new DATA, RS retry frames and keepalives. Incoming ACK processing and
RTCP read/write do not wait for its RTP permit.

Current-session negotiated feedback and actual RTCP traffic are **NOT_SAVED** in
the available baseline receipts. No claim that late9909 was NACK, no inference that
feedback was absent. New bounded counters distinguish negotiated feedback flags
from received RR/NACK/TWCC/REMB/PLI. Publisher↔SFU is not the full path to Android.

## BURST_EVIDENCE / equal-budget local results

Actual bound Pion WriteSample, local sink, not network:32 identical frames/224 RTP
packets/266802B in the same2.24s offered budget (70ms scheduling, retained2ms pause).
Peak fixed1ms bin falls **7 packets/8338B →1 packet/1200B**;5ms peak7→2;20ms7→7.
Average offered bytes are identical. This proves local burst formation/smoothing,
not loss at SFU or delivery to Android. Maximum observed scheduler lateness1.134313ms;
this is a host result, not a promise of exact millisecond deadlines.

Deterministic model: actual packetizer sizes, synthetic payload,64 frames/448
packets/533618 RTP bytes in both arms. Primary input75ms,4.8s common budget;
payload rate≈0.874Mbit/s is anchored to historical A3 handed carrier≈0.878Mbit/s,
not a fresh beta96 wire rate. Link/queue capacities below are **model assumptions**,
not measured external-network parameters. The slow case uses100ms input/consumer
service and6.4s budget. Independent bound-Pion/RS tests cover actual adjacent reorder.

| Scenario | Burst full frames / drops | Paced full frames / drops | Last useful frame, burst → paced |
|---|---:|---:|---|
| Sufficient8Mbit/s link | 64 /0 | 64 /0 | 4.753338 →4.760538s |
| 4Mbit/s link,2-packet queue | 0 /320 | 64 /0 | none →4.761676s |
|3ms reorder/delay perturbation | 64 /0 | 64 /0 | 4.756338 →4.763538s |
| Slow consumer | 64 /0 | 64 /0 | 6.428338 →6.435538s |

Smoothing helps the explicitly shallow-queue model but adds7.2ms in the no-loss
case. Consumer queue≤2frames; link bounds respected. This is not a complete SFU/RS
model, a physical byte-exact acceptance, or evidence of doubled tunnel throughput.

## ONE_TARGETED_CHANGE and QUEUE_RETRY_SAFETY

One fixed packet-pacing candidate: **500000 RTP bytes/s (4Mbit/s)**, not adaptive CC.
Cap chosen above observed application average to test smoothing first; it is not a
capacity estimate. Synchronous writes, monotonic spacing from actual local completion,
no accumulated idle credit/catch-up burst, no new per-packet goroutine or copied queue.
Pion's supplied pacing implementations return before write and accumulate an
unbounded slice/list; directly using them would violate completion/boundedness.

Bounds:16 admitted calls,1500 logical RTP bytes each,1s admission/pacing wait.
Capacity/timeout/short writes report errors rather than silently losing fragments.
Actual underlying I/O remains subject to Pion/transport shutdown; the pacer does not
claim to cancel an arbitrary blocked external Write. Session close cancels pacing
before closing transport, and full-queue writer shutdown was tested repeatedly.
RTCP bypasses media pacing. Queued ACK/control traffic keeps existing frame FIFO;
there is no new priority bypass. The cap can add FIFO latency; local admission has
a deadline but this is not an end-to-end control-delivery latency guarantee.

New retained packet data≤24000 logical bytes across admitted calls, not total
process memory. Existing256×8233B carrier frame data bound=2107648B; retained
caller buffers/backing storage, TLS/RS buffers, NACK cache, socket buffers and worker
metadata are additional. Saturation fails explicitly; it does not grow another queue.

**Mandatory, explicit prerequisite:** reuse the separately preserved queue-completion
correctness patch, rebased onto compatible sources without changing its old artifact.
Only selected dedicated sessions opt in. RS retry accounting waits for actual local
write completion; input ACK loop remains independent; stale unstarted retries cancel.
No RS window/RTO/retry-limit change. A and B both use this prerequisite; it is not
silently added only to paced B. Local controls separate its effect:

| Local hold fixture (RTO30ms/hold340ms, not production settings) | Attempts before write | Retries | Queued fragments | Result |
|---|---:|---:|---:|---|
| Exact accepted A0/Q0 |9|8|36|recovery_exhausted |
| New binary OFF/Q0 |9|8|35|same exhaustion (scheduling-dependent depth) |
| OBSERVE/Q1 |1|0|2|byte-exact,0.345883661s |
| FIXED4M/Q1 |1|0|2|byte-exact,0.384572138s |

Future live **A=OBSERVE/Q1, B=FIXED4M/Q1**. A is a common correctness control, not
bit-for-bit accepted Q0 behavior; A/B isolates pacing over Q1, not total gain versus
the currently installed binary. OFF preserves Q0; default/seed/unselected peers do
not opt into either pacing or completion. This separation is a limitation of acceptance.

## Counters, correctness and overhead

Same OBSERVE/FIXED4M bounded stats in existing TransportPerformance/export path:
1/5/20ms peak bins; spacing/wait/scheduler lateness; queue age/depth; pending packets/
bytes; RTP and local-write bytes; RTCP classes/bytes and negotiated flags. Histogram
thresholds≤10/50/100/500µs,1/5/20/100ms,overflow. Bins are fixed-origin, non-sliding:
a burst crossing a boundary can be understated. Spacing is between local successful
write completions. Wait durations sample calls reaching the writer; cancelled earlier
waits count errors, not complete wait-time integrals. Elapsed time brackets each
session snapshot; use deltas over the matching request interval, not lifetime totals.
Frame packet histogram counts write groups including repeats, not recovered frames.
RTX SSRC count does not identify every ordinary same-SSRC retransmission. Local write
bytes may include SRTP expansion, not all UDP/IP/ICE wire overhead or proof of delivery.
No payload, proof, secrets, room URLs or synchronous per-packet journal is exported.

PASS:613 candidate tests/subtests in the retained union,11 affected package suites
with race; real Pion+RS no-loss/loss/reorder/slow consumer, byte-exact/legacy,
overflow/admission, partial write, late ACK/cancel, idle→burst, actual NACK responder,
RTCP while RTP waits, track generation/wrap, close and stale completions. Frozen
patch reproduction +5× targeted race and10× full256-frame queue Session.Close PASS.
Actual existing exporter verified both modes. These counts are not speed acceptance.
Unchanged beta96 checks175 JVM/6 Python/8 focused native reused; no old Mux/deadline
acceptance rerun. Gateway1011/recovery paths retained and relevant suites passed.

Retained setup failures: sandbox loopback denial → normal outside-sandbox test;
missing capsule-relative bootstrap vector → correct fixture link; three queue-patch
overlaps → explicit merge preserving existing counters. No weakening validation or
arbitrary sleep increase. Initial logs retained alongside successful reruns.

Non-race local microbenchmark,3 repeats: plain4.247–4.980ns/op; OBSERVE1016–1062ns/op,
384B/5alloc per call. Includes gate/context + counters, not only histograms. Same
cost in A/B; not a production CPU result. Default OFF creates no pacer.

## BEFORE_AFTER_SPEED_LATENCY_FAILURES / guarded continuation

| Physical phase | Single / aggregate / control | Failures / protocol_errors / retries | Status |
|---|---|---|---|
| A1 |0.676945 /1.133596Mbit/s; control5.958610s|4/4 complete, errors1→1; detailed normalized evidence above|COMPLETE |
| B1 | not measured | not measured | NOT_RUN |
| B2 / A2 | not measured | not measured | NOT_RUN |

No historical beta94/95 speeds are used as current A. No physical receiver-loss,
protocol-error, resource or reconnect conclusion is possible before these phases.
Instrumentation startup must be verified before sending bulk; existing phone96
export may not expose fine per-frame old_rtp counters, which remains a limit.

At the local-only checkpoint, the next action was **coordination**, not another implementation/search branch:
after the beta96 tester attempt finishes, authorize one ordinary shared gateway
switch. Fresh state/credentials/hash guards; exact272bbc… rollback retained.
Default remains OFF. Existing protected operator files select authenticated owner
public-key hash and OBSERVE/FIXED4M for **new sessions only**; selector does not grant
authorization. Same permissions/ownership/no-symlink parser, no remote API/new UI.
Do not touch Support IDs, grants, all_activated or active-session policy.

After coordinated load, owner ordinary reconnect; verify actual LEGACY64/65536,
A0/96, new mode/session, gateway PID and genuine counter export. A/B then B/A:
each single4MiB + parallel2×2MiB + existing64KiB control, planned32.25MiB, ≤64MiB
total/180s per request (stricter limits win). Retain failed requests and background
bytes, normalize matching intervals, do not add overlapping Mux/RS stalls.
Mode changes use manual reconnect, not INJECT_EVENTS or a background waiting task.
Off/next-session reconnect restores baseline semantics without APK downgrade;
binary rollback only if required and coordinated, always exact272bbc…/1011.

Decision now: **INCONCLUSIVE; not accepted or deployed**. Local results justify
one controlled candidate, not an external-network diagnosis. If the eventual
software hypothesis fails, the next discriminating comparison is the same code
over IPv4 on another authorized placement, not automatic migration/purchase now.
