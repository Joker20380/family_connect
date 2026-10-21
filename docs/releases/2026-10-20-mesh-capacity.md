# MESH capacity investigation — phases1–3, TLS→RS packing and P interaction,20–21 October2026

Phase3 follow-up is appended below with its own budget and fresh production readback.
The following original sections retain the closed phases1–2 history and P816 warning.
The21October TLS→RS packing result preserves stronger T/slot efficiency and no
repeated P32 gain. Its P-stack interaction follow-up is the final section: credit
constraint established, no repeatable material added packing benefit; no product admission.

**COMPLETED WITH P816 PROTOCOL WARNING: bounded Linux findings; NOT product admission.**
19 independent NL sessions,38 closed peers. No live Android interaction, production
binary/configuration/identity/credentials/floors/directory/routing mutation, push,
publication or RU matrix. The previous host-comparison budget remains closed.

## Conclusions, individually classified

| Question | Classification | Finding |
|---|---|---|
| CARRIER_DELIVERY_ENVELOPE | CONFIRMED at tested points; higher raw rates NOT_CHECKED | C0.5 delivers70/75; two C1 runs134/151 and133/151 after32s. No corruption. Partial-message delivery is not reliable VPN capacity. Rates2/4/8 were not escalated after repeated incomplete delivery. |
| RELIABLESTREAM_COST | CONFIRMED recovery/wait cost; exact causal layer percentage LIMITED by sessions/shape | At matched carrier DATA size and nominal new-DATA rate, Rmatch delivers151/151 with606304 retry bytes; C1b loses18/151. Default full-record R8/16 delivers1.258819Mbit/s completely. This is not a simple “RS subtracts X%” result. |
| TLS_MUX_INCREMENTAL_EFFECT | CONFIRMED record-shape effect; one clean P pair only; pure TLS CPU overhead NOT_ESTABLISHED | T8/16=0.498142; clean P8 single0.584762. Earlier P816 has a protocol warning and is excluded. T creates many22/34-byte RS DATA blocks; P has its existing loopback TCP/Mux batching shape. P32 single0.764793, two-stream aggregate1.367101: not the~3x R-layer gain. |
| WINDOW8_16_32_EFFECT | CONFIRMED in bounded repeated R comparison | Effective8:1.262439/1.331633;16:2.245900/1.607627;32:3.642117/3.643658Mbit/s, all256/256. Same payload/RTO/retry/framing;8/32 is an experimental receive-cap control, not production8/16. |
| REASSEMBLY_CAPACITY_INTERACTION | CONFIRMED local overlap hazard; overflow NOT_OBSERVED physically | Ordered32 messages complete with cap16.32 deliberately incomplete overlapping messages produce32 capacity-rejected fragments and only16 completions. Every physical capacity counter remains0; caps were not raised. |
| CPU_OR_SCHEDULER_LIMIT | NOT_SUPPORTED in tested conditions | Generator/verifier22Gbit/s; full copy/read/verify/counter calibration2.07Gbit/s under race. Owned process CPU, GC and cgroup throttling are small relative to window waits; no basis for blaming1vCPU or moving to RU. |
| BEST_RELIABLE_RESULT | CONFIRMED for the finite tested transfer, not a technology ceiling | R32sustain: 1280/1280, 20930560 useful bytes in29.935790s = **5.593455Mbit/s**, no corruption/capacity overflow. |
| PRODUCTION_UNCHANGED | CONFIRMED gateway readbacks; phone not operated | Same734b6ca6…/PID4126720/invocationc24eee95…/profile hash/OFF/LEGACY64/export-OFF throughout and postflight. No product artifact was installed or distributed. |

The unused-capacity hypothesis has a **specific supported component**: the shared
RS slot window and record shape limit this workload before all available delivery
in the tested media path is used. This does **not** measure a universal carrier
maximum, a precise percentage of unused bandwidth, or Android speedup.

## A — independent carrier messages

C input is16448bytes/message, including32-byte diagnostic envelope. Target rates
are **carrier-input**, not RTP/UDP wire rates. Send schedules last19.738/19.475/
19.738s for finite151/75/151 messages; declared offered observation interval20s.
Local write columns are **whole-peer** WriteSample/RTP-attempt counters including
controls, keepalives and lower retransmits, not falsely relabeled useful messages.

| Phase | Target Mbit/s | Offered carrier B | Enqueued messages | Samples/RTP writes | TX RTP B | Unique messages | Useful received B | Useful by20s Mbit/s | Whole32s observation Mbit/s |
|---|---|---|---|---|---|---|---|---|---|
| C1 | 1.0 | 2483648 | 151 | 500/2313 | 2540831 | 134/151 | 2199744 | 0.827366 | 0.549923 |
| C05 | 0.5 | 1233600 | 75 | 275/1176 | 1263327 | 70/75 | 1149120 | 0.413683 | 0.287271 |
| C1b | 1.0 | 2483648 | 151 | 500/2313 | 2540825 | 133/151 | 2183328 | 0.833933 | 0.545828 |

All C source/receiver sampled queues end empty, sampled send/receive queue peaks0;
duplicates0, corruption0, CRC failures0, capacity rejects0. Final count uses the
sender's predetermined total, not merely a receiver-reported denominator.

| Phase | RTP reader packets | Sequence-gap events | VP8 frames | Carrier fragments | All complete carrier msgs | Expired partials | Capacity rejects | Late after20s msgs | Last arrival / observation s | Loaded32B RTT median s |
|---|---|---|---|---|---|---|---|---|---|---|
| C1 | 2122 | 6 | 453 | 430 | 157 | 5 | 0 | 8 | 21.887599/32.000732 | 1.190 |
| C05 | 1127 | 4 | 260 | 234 | 92 | 2 | 0 | 7 | 21.864078/32.000975 | 1.123 |
| C1b | 2115 | 6 | 452 | 429 | 156 | 6 | 0 | 6 | 21.768369/32.000230 | 1.184 |

Gap events are not lost-packet counts. Carrier totals include32-byte diagnostic
controls; useful-message counts come from independent ID/content validation.
TX/RX differences cannot localize loss to wire versus SFU versus unexported reader/
reorder/VP8 categories. Absence in bounded metadata is not a network-loss verdict.
The12s raw drain exceeds the10s reassembly lifetime; missing IDs mean **not delivered
within this observation contract**, not a claim about arbitrarily late network data.
Late bytes are never added to the20s numerator. Last-arrival goodputs are separately
0.804015/0.420460/0.802386Mbit/s, not reliable completion rates.

C1 missing-group starts on the **planned sender schedule** are0.395,2.369,4.342,
6.316,8.290,10.264s; C1b starts0.526,2.500,4.605,6.579,8.553,10.527s.
Repeated spacing is~1.974–2.105s. Source also emits a decodable keepalive every2s.
This is a discriminating **phase3 hypothesis**, not proof that keepalives cause loss:
exact per-frame send/receive timebase correlation was not exported in this phase.

## B — reliable completion, TLS and product-like workload

R/T goodput uses useful bytes excluding32-byte envelope and receiver-monotonic
start-request→last verified byte. Full controller elapsed times including setup,
drain, confirmation and cleanup are retained below. No clocks of different machines
are subtracted.32-byte probes measure the entire stack round trip, not pure wire RTT.
Retry and ready-full counters are **whole-peer lifetime** counters, including setup
and final control; they are not request-local allocations or additive wall times.

| Phase | Mode | Useful B | Verified messages | Receiver s | Mbit/s | RS retry B | Ready/full s | Loaded32B RTT median s |
|---|---|---|---|---|---|---|---|---|
| R816a | R | 4186112 | 256/256 | 26.603424 | 1.258819 | 884864 | 26.093466 | 0.772 |
| T816 | T | 4186112 | 256/256 | 67.227667 | 0.498142 | 839738 | 65.260306 | 0.579 |
| R832a | R | 4186112 | 256/256 | 26.527134 | 1.262439 | 966752 | 24.637705 | 0.650 |
| R1632a | R | 4186112 | 256/256 | 14.911126 | 2.245900 | 934112 | 13.677300 | 0.764 |
| R3232a | R | 4186112 | 256/256 | 9.194898 | 3.642117 | 1196096 | 7.500440 | 0.973 |
| R3232b | R | 4186112 | 256/256 | 9.191010 | 3.643658 | 950336 | 7.460003 | 0.882 |
| R1632b | R | 4186112 | 256/256 | 20.831266 | 1.607627 | 1327296 | 19.949789 | 0.600 |
| R832b | R | 4186112 | 256/256 | 25.148739 | 1.331633 | 655456 | 24.373672 | 0.553 |
| Rmatch | R | 2469152 | 151/151 | 22.263173 | 0.887260 | 606304 | 15.890164 | 0.805 |
| Rmix | R | 4181200 | 700/700 | 66.577367 | 0.502417 | 854612 | 64.857982 | 0.434 |
| Reverse | R | 65408 | 4/4 | 1.384758 | 0.377874 | 160 | 0.000000 | - |
| R32long | R | 10465280 | 640/640 | 16.994586 | 4.926407 | 2572384 | 16.064217 | 0.680 |
| R32sustain | R | 20930560 | 1280/1280 | 29.935790 | 5.593455 | 4407488 | 29.140041 | 0.700 |

Rmatch uses151×16384-byte inputs at124513B/s, yielding151×16448-byte original
carrier DATA at nominal1Mbit/s, matching C1b's carrier work. R's32-byte envelope
leaves16352 useful bytes versus C's16416; reported numerators account for this.
Retransmissions/ACKs are extra wire work, not hidden in original offered rate.
Initial C1→R816a is followed by the **reverse-order** matched Rmatch→C1b contrast;
R816a is uncapped and is not falsely described as the matched offered-rate run.

Rmix repeats[88,556,556,7980,7980,8492,16384]100times, representative of actual
P816 DATA sizes rather than only full16KiB blocks. Its4,181,200 useful bytes take
66.577367s (0.502417Mbit/s); sampled retained peak58420B versus131072B for full
R8. These are representative weights, not an exact replay of P's frequency histogram.
Reverse is a64KiB **direction/correctness control**, not sustained upstream capacity.

### P: Mux64 + Family TLS + ReliableStream

Every phase has complete64KiB echo,4MiB download,2×2MiB parallel download,64KiB
reverse upload plus verified digest receipt. Echo is bidirectional application
latency, **not network RTT**. Main throughput rows are pure NL→client downloads.

| Phase | RS S/R both ends | Single4MiB s | Single Mbit/s | Parallel4MiB common s | Aggregate Mbit/s | Phase ready/full s | Phase RS retry B | Bodies | Max client protocol errors |
|---|---|---|---|---|---|---|---|---|---|
| P816 | 8/16 | 46.235310 | 0.725732 | 31.846122 | 1.053643 | 68.797008 | 1495864 | 5/5 | 1 |
| P3232 | 32/32 | 43.873895 | 0.764793 | 24.544228 | 1.367101 | 13.866379 | 1729382 | 5/5 | 0 |
| P816b | 8/16 | 57.381376 | 0.584762 | 29.845379 | 1.124276 | 79.989847 | 1339828 | 5/5 | 0 |

**P816 is excluded from the clean comparison.** Postflight found its client counter
0 at echo completion,1 before the single download, then1 throughout bulk/reverse.
All bodies match, but that does not erase a protocol warning. Exact error category
is not exported; neither a harmless close race nor network loss is established.
The new wrapper omitted the previous operator's protocol stop gate, so discovery
was late, after subsequent independent sessions. This workflow failure is retained
in `P816/postflight-protocol-warning.json`; the original operator is preserved in
`operator-used/run.py`. Future runs now fail on any nonzero P counter and this
experiment is closed. No binary/transport fix, hidden rerun or counter reset occurs.

Clean P3232→P816b gives single+30.79%, aggregate+21.60%, with0 throughout both.
This is one bounded clean pair, not a repeated3x single-flow claim or Android
admission. The contaminated earlier comparison is visible but not acceptance.
Ready/full falls markedly at P32,
while application goodput does not follow R32 proportionally: limitation remains
above/alongside the larger RS window. **Server Mux zero-credit counters were not
exported by this adapter**, so pure Mux-credit attribution is not claimed.

### Record and packetization accounting

Exact defaults: Payload16384, SendWindow8, ReceiveWindow16, MaxWindow32, SACK32bits,
RTO1s, MaxRetries8, MaxAge20s. Carrier payload fragment8192B +24B header;
maxPendingMessages16, receive queue64, sendQueue256, reassembly lifetime10s.
No framing/packetizer/timebase/cap/RTO/retry/A0/pacer changes.

Pion4.2.15 actually uses MTU1200: RAW16384 →2 fragments/2 VP8 frames/**14 RTP**;
FRS DATA16384+64 or RAW16448 →3/3/**15 RTP** before lower retransmits.
The previous local framed-loss helper uses payloader1100 and yields16/17; that is
**not** the physical packetization. `actual-packetization.log` verifies real Pion.

T816's outbound unique TLS histogram includes251×16406B and251×34B records.
The large TLS record crosses RS as16384+22; the small remaining record consumes
another34-byte RS DATA slot. All-attempt RS histogram includes302×16384,290×22,
279×34. Sampled retained peak62410B despite eight occupied slots. P816's actual
DATA distribution includes556,88,7980,8492,16384 and many intermediate sizes.
Full TLS/RS/carrier histograms and actual RTP counters are preserved per endpoint.
Therefore T/P differences cannot be called pure cryptographic CPU overhead.

## C — effective windows, not Mux credit

Notation S/R = configured local send / advertised local receive. The other end's
receive32 permits effective32; no32/16 case is misrepresented as window32.
Configuration is emitted at both ends; unchanged OPEN code advertises that receive
cap and live Performance.EffectiveWindow confirms the negotiated send limit.
All rows below deliver256/256,4,186,112 useful bytes, same fixed full DATA size.

| Phase | NL S/R | Client S/R | Effective NL | Mbit/s | Sampled retained/unconfirmed/SACKed B | Sampled max head age s | RX sampled pending/capacity rejects |
|---|---|---|---|---|---|---|---|
| R816a | 8/16 | 8/16 | 8 | 1.258819 | 131072/131072/81920 | 2.006 | 5/0 |
| R832a | 8/32 | 8/32 | 8 | 1.262439 | 131072/131072/98304 | 1.471 | 6/0 |
| R1632a | 16/32 | 16/32 | 16 | 2.245900 | 262144/262144/163840 | 2.011 | 3/0 |
| R3232a | 32/32 | 32/32 | 32 | 3.642117 | 524288/524288/376832 | 1.851 | 5/0 |
| R3232b | 32/32 | 32/32 | 32 | 3.643658 | 524288/524288/409600 | 2.004 | 5/0 |
| R1632b | 16/32 | 16/32 | 16 | 1.607627 | 262144/262144/229408 | 4.430 | 7/0 |
| R832b | 8/32 | 8/32 | 8 | 1.331633 | 131072/131072/98304 | 1.537 | 3/0 |

Order8→16→32 then32→16→8.32/8 gains+188.50% and+173.62%;16 gains vary materially
with path/recovery. Exact8/16 versus8/32 control1.258819 versus1.262439 does not
show a meaningful receive-cap-only speed change in this one comparison.
4MiB R32 runs are~9.2s, **not sustained capacity claims**. Additional10MiB completes
in16.994586s; the final20MiB control above extends the observation, separately scoped.
Retained/unconfirmed/SACKed bytes are overlapping sampled states, **not physical
bytes in flight**. Head ages are sampled lower bounds; engine MaxRecoveryMS and
head-blocked counters are retained in raw data. Overlapping waits must not be summed.

Local fault checks cover loss/reorder/duplicates/head gaps/late recovery/ACK loss,
slow consumer/backpressure/cancel/close and bitmap bit31 for all four pairs. Actual
RTP→reorder→VP8→reassembly→RS recovery delivers64/64 at each pair after two missing
head attempts, capacity rejects0. Deliberately interleaving32 incomplete assemblies
produces16/32 completions,32 rejected fragments,16 pending; contiguous32 completes
32/32. That controlled hazard is real but is not observed in these physical runs.
Memory/waits stay bounded; validation and limits remain enabled.

## Resources and measurement calibration

NL remains1logical CPU with the existing test-only50%-of-one-core quota,
MemoryMax220MiB/no swap/TasksMax96/Nice10; no assumption that1vCPU is insufficient.
The previous Linux client remains on its Wi-Fi path; no RU control is warranted by
the observed compute utilization. Whole-host counters include unrelated work and
are not attributed to this test. Local cgroup is shared; owned PID/thread counters
and getrusage, not its aggregate cgroup usage, establish test-process CPU.

| Phase | NL process CPU / sampled lifetime s | Peak thread % one core | Cgroup throttled ms | Host steal % | NL max RSS KiB | GC pause ms through last sample | Sampled server send/client receive queue |
|---|---|---|---|---|---|---|---|
| C1 | 2.078/49.090 | 2.52 | 5.729 | 0.436 | 31556 | 9.809 | 0/0 |
| R816a | 2.009/44.086 | 2.41 | 16.963 | 0.498 | 30944 | 13.956 | 12/0 |
| T816 | 3.561/84.136 | 2.27 | 0.000 | 0.374 | 32336 | 15.556 | 3/0 |
| P816 | 4.445/98.198 | 2.66 | 20.293 | 0.340 | 40876 | 16.536 | 1/0 |
| C05 | 2.167/55.101 | 2.15 | 0.000 | 0.270 | 31204 | 10.783 | 0/0 |
| R832a | 1.875/41.102 | 2.81 | 12.940 | 0.301 | 30740 | 17.580 | 2/0 |
| R1632a | 1.357/33.054 | 2.03 | 19.207 | 0.344 | 30420 | 10.070 | 7/0 |
| R3232a | 1.021/25.041 | 2.34 | 0.000 | 0.237 | 31636 | 10.996 | 0/0 |
| R3232b | 1.017/24.041 | 2.42 | 0.000 | 0.198 | 32460 | 7.388 | 70/0 |
| R1632b | 1.579/36.072 | 2.65 | 8.548 | 0.347 | 31648 | 12.946 | 2/0 |
| R832b | 1.715/40.067 | 2.49 | 8.752 | 0.340 | 31536 | 8.826 | 8/0 |
| P3232 | 4.909/92.167 | 2.48 | 32.103 | 0.335 | 41168 | 15.516 | 6/5 |
| P816b | 5.163/112.245 | 2.83 | 17.348 | 0.303 | 41816 | 10.609 | 6/0 |
| Rmatch | 1.653/37.078 | 3.82 | 21.178 | 0.295 | 31248 | 9.952 | 1/0 |
| C1b | 2.055/49.078 | 2.28 | 12.896 | 0.258 | 30940 | 8.852 | 0/0 |
| Rmix | 3.492/82.308 | 2.45 | 0.000 | 0.319 | 31584 | 25.614 | 7/0 |
| Reverse | 0.565/15.030 | 1.88 | 0.000 | 0.262 | 27056 | 3.871 | 0/0 |
| R32long | 1.806/32.074 | 3.15 | 0.000 | 0.399 | 32236 | 15.355 | 49/0 |
| R32sustain | 2.766/45.277 | 3.20 | 0.000 | 0.262 | 33148 | 25.489 | 68/0 |

Per-core `/proc/stat`, per-owned-thread schedstat, scheduler wait, cgroup counters,
memory and GC samples are retained. No profiler touches production. Independent
generator/full-byte verifier calibration before media:22,003.62Mbit/s under race;
additional generation/copy/read/verify/counters calibration after the window round:
2,068.97Mbit/s. The latter is not falsely described as pre-matrix. Neither supports
a generator bottleneck. Initial lab-only compile/type errors and an OS-suffix test
filename omission were repaired and rerun **before any media**; failure logs remain.
The missing-callable test was renamed before all four pairs passed. This is not a
production MESH fix. One local packetization validation compile overlapped T's run;
owned test CPU is separate, but the machine was not an exclusive benchmark host.

## Session comparability and budgets

One source capsule and one test binary for every endpoint. Separate fresh media
sessions, no runtime switching protocol and no reused user/bootstrap room. Each
phase fully closes before the next. All use VP8/RTP/IPv4 with unchanged Pion lower
NACK/retransmission. SFU differences limit precise causal percentages; repetitions
support only the stated bounded comparisons, not a universal host/channel maximum.
Per-phase client network/rules/routes and nominated local/remote ICE candidates are
in the raw kit; postflight route readbacks are in verification.json.

| Phase | Selected SFU IPs | Controller total s incl setup/drain/confirm/cleanup | Source reserved B | Conservative outgoing media charge B |
|---|---|---|---|---|
| C1 | 77.88.43.30 | 71.774 | 2549184 | 2922976 |
| R816a | 37.9.127.76 | 60.628 | 4259840 | 5870419 |
| T816 | 37.9.127.114 | 101.068 | 4259840 | 6192795 |
| P816 | 5.255.254.88 | 110.759 | 8585273 | 12326938 |
| C05 | 37.9.100.208 | 70.091 | 1299136 | 1595100 |
| R832a | 77.88.42.13 | 60.538 | 4259840 | 5956781 |
| R1632a | 77.88.42.99 | 49.418 | 4259840 | 5870289 |
| R3232a | 5.255.254.119 | 41.540 | 4259840 | 6119947 |
| R3232b | 77.88.42.51 | 37.705 | 4259840 | 5852879 |
| R1632b | 37.9.69.219 | 51.710 | 4259840 | 6323949 |
| R832b | 37.9.69.188 | 53.268 | 4259840 | 5605900 |
| P3232 | 37.9.69.155 | 101.919 | 8585273 | 13618139 |
| P816b | 37.9.73.129 | 122.583 | 8585273 | 12271899 |
| Rmatch | 5.255.252.106 | 51.621 | 2539520 | 3648030 |
| C1b | 77.88.42.173 | 62.214 | 2549184 | 2922966 |
| Rmix | 5.255.254.74 | 98.167 | 4269136 | 6166947 |
| Reverse | 77.88.43.33 | 29.290 | 131072 | 249473 |
| R32long | 77.88.43.66 | 46.957 | 10551296 | 14567370 |
| R32sustain | 37.9.69.136 | 56.596 | 21037056 | 28156794 |

Source reservation **104760123B = 99.907039/128MiB**.
Outgoing RTP+RTCP attempts **132837735B**;
conservative wire charge **146239591B = 139.464942/256MiB**.
The first Pion interceptor counts **both processes' outgoing packets only**, including
NACK retransmits; no receiver-RX double counting. Guard reserves RTP/RTCP length+64B
per packet/compound for IPv4/UDP/SRTP/SRTCP. Closed endpoints also retain64KiB tail
margin; unclosed ones would charge their full reservation. Every write is guarded
atomically before emission; no budget stop occurred. Signaling/SSH/source uploads
are administrative traffic outside this explicitly defined media boundary.

## Provenance, cleanup and rollout/rollback

- Production gateway SHA256 `734b6ca6eb42be0367b703b657be87c624f3500ae408bbd771309ffaeb86128e`.
- Last accepted product remains beta96-bootstrap/A0/LEGACY64/65536/OFF/Q0;
  bootstrap96/gateway1011 retained. Prior manifest APK07a90f03… /native66a9d18d…;
  no phone read/write/reconnect was performed in this experiment.
- **Different test binary** SHA256 `d0cb384d047e94a154df51c9537a7d6c3dd06215fa7c03b700e0652120977187`;
  Go1.26.1 linux/amd64,fc_perf_diagnostic, pinned dependencies, no upgrades.
- Parent host-comparison build manifest SHA256 `c37d6b10964079e76052d340b897b25d4e1be9c2641ac7fc793247e187a8cc5d`.
- Current build manifest SHA256 `9bb9cb3416628711e803a8cd16b579cd4937f2d9048000debc61f287470bebf8`;
  canonical source inventory SHA256 `fc50d787b6b30e774d51b86bf9fb6c972a7a05b998fdc54b0e9610203a5fc9c6`.
- Test-only patch SHA256 `49959ad0be7612b3e26e8878b661aaa8d55c99b82c1fa120c961730d698003dd`: workload adapters, read-only
  histograms/candidate projection, outgoing budget guard; no accepted transport
  optimization and no production file edits. No reset to old main or push.
- Built and run: this isolated laboratory executable only. Installed product,
  public installer/APK/catalog/invitation-page versions: **unchanged**. No release
  signing, public distribution, routing, authority, floors or credential operations.
- All38 peers closed; owned local/remote processes and NL
  stages absent; fresh test identities/DB/profile/room inputs removed. Normal leave
  is confirmed; provider-side conference metadata deletion is **not established**.
- Production rollback is neither needed nor invoked. Test rollback is stopping only
  `family-connect-capacity-20261020-<phase>` and its owned worker, then removing only
  its isolated stage after process exit; RuntimeMax510s also bounds abandoned units.
  Never replace production with this binary or restore an obsolete gateway/main.

Reproducible source/binary/raw logs/configurations/calculations/manifests:
`state-client-build/mesh-capacity-20261020/`.
Kit `mesh-capacity-kit.tar.gz`, SHA256 `af445732fe4ed342e470ebc988c6636abcf0501a04b0a11921d59a35e243d293`.
[Operator scope](../../tests/fixtures/mesh_capacity/README.md),
[machine-readable public projection](2026-10-20-mesh-capacity.evidence.json).

## Parent handoff — historical, superseded by phase3 below

Phase3 first: record RTP/RTCP timebase and actual data/keepalive frame cadence,
correlate the~2s missing-message groups across reader/reorder/VP8/reassembly, and
measure the cost of losing one fragment of a message. Keep a known baseline;
timestamp changes and packetization changes must be separate experiments.
Exact provider/SFU discard classification remains missing, not assumed network loss.

Phase4 separately: alternate fragmentation **without FEC**, then the same choice
with bounded FEC at equal total sending budget including parity, group delay and
burst losses; no assumption of arbitrary SFU FEC support. Phase5 separately: QUIC
over carrier datagrams, not ReliableStream; check MTU, queues and lower carrier HOL,
and do not collapse all independent flows into a single QUIC stream. Prototypes
still need compatible Family identity/authorization/revocation integration and
must never create a plaintext fallback. None of these mechanisms is implemented here.

Remaining product checks: Android/mobile/TUN and window32 production admission are
**NOT_RUN**; CPU-host migration is not indicated; raw rates above1Mbit/s remain
unmeasured. No further load, phone action or deployment is pending in this task.

## Phase3 — media timebase and periodic loss,20–21 October2026

**COMPLETED:14 isolated NL→Linux sessions,28 closed peers. B is a validated laboratory
clock correction, NOT an accepted speed fix or production configuration.** Main C,
R32 and P32 comparisons all use one binary
`b95110c5413d5af7e99a25072a2bb655775d159c0092aad69d4efc990061e3ce`.
CA1 is a retained instrumentation pilot with an earlier trace-label revision, not a
clean paired acceptance row. No production binary/config/APK, authority, credentials,
floors, revocation, routing, directory, release, push or RU migration was performed.

### Phase3 decisions, separately classified

| Question | Classification | Finding |
|---|---|---|
| PERIODICITY_REAL_OR_SAMPLING_ARTIFACT | CONFIRMED transient periodic structure, not an export artefact | Known missing IDs form groups~2s apart; packet-level monotonic observations place losses near the end of actual media-keepalive cycles. Main C losses occur in the first~11s of20s input, not indefinitely throughout a steady channel. |
| KEEPALIVE_CAUSAL_EVIDENCE | Phase coupling observed; exclusive causal attribution LIMITED | A+1s first-keepalive shift moves missing ID groups while the2s interval remains. All main missing-message first writes occur about1.61–1.98s after the previous actual keepalive. Different rooms/SFUs and load-start phase prevent an exact causal percentage; ICE consent also has a2s timer and is not in the media trace. Do not call keepalive suppression a fix. |
| RTP_RTCP_TIMEBASE | CONFIRMED inconsistency in A; corrected in B | A advances2970 ticks per sample regardless of idle/burst timing. Outgoing SR mapping has backwards steps and large jumps. B uses monotonic elapsed-before-sample; observed SR interval error is~0.07–1.03ms, with no backwards step. |
| FRAME_BOUNDARY_OR_REASSEMBLY_DEFECT | Local keepalive corruption hypothesis REFUTED in tested cases | Complete packet sets reassemble byte-exactly. Main C has40–42 bulk fragments without a first packet at the reader and5–6 partial frames; none has an equal complete payload packet multiset but fails assembly. The confirmed gap is after local RTP writes and before complete valid-RTP input, not a demonstrated local frame reset. |
| ONE_TARGETED_FIX | Correctness validated; NOT_ACCEPTED as speed fix | B changes only sample timestamp advancement using the same Pion packetizer. Keepalive2s, packetization, sequence/PictureID, NACK, A0, Q0, TLS, CRC and windows are unchanged. No second mechanism is combined with it. |
| C_AND_R32_EFFECT | C loss-fix hypothesis REFUTED; reliable speed attribution LIMITED | C A/B/B/A=134/133/133/133 of151. R32 delivers256/256 in every row; B/A gains+15.423% then+0.469%, with different SFUs. No repeatable sizeable R gain is established. |
| P_STACK_EFFECT | Repeatable application speedup REFUTED in these pairs | Single B/A +3.652% then−3.954%; parallel +3.770% then−6.659%.20/20 bodies byte-exact, both-end ProtocolErrors0 from creation through final close. |
| SHORT_RS_DATA_ORIGIN | CONFIRMED by byte-exact local boundary correlation | Application16384 + Family frame12 → TLS plaintext16396 → records16406 and34 → RS DATA16384,22,34.195/200 steady-state writes reproduce this in each direction; old T8 has251 such record pairs. No packing patch implemented. |
| PRODUCTION_UNCHANGED | CONFIRMED fresh gateway readbacks; phone not operated | Binary734b6ca6…/PID47501/invocation27e2c972…/profileabda003f… and OFF/LEGACY64/export-OFF are constant throughout this task. This process/profile already differed from the previous task before testing and was not rolled back. |

### Parent results rechecked, not rerun or overwritten

All19 original attempts remain in `parent-recalculation.json`, including excluded
P816 (client0→1 between echo and bulk, category unavailable). The clean original
P3232/P816b pair remains separate; phase3 does not relabel P816 as clean or invent its
error category. Original window experiments and promising RS32 are not production
admission. The10MiB `R32long` and20MiB `R32sustain` retain their exact distinct names.

| Parent phase | Verified useful B | Receiver monotonic s | Recomputed Mbit/s |
| --- | --- | --- | --- |
| R816a | 4186112 | 26.603424358 | 1.258818998 |
| R832a | 4186112 | 26.527133817 | 1.262439291 |
| R1632a | 4186112 | 14.911126223 | 2.245899840 |
| R3232a | 4186112 | 9.194897920 | 3.642117214 |
| R3232b | 4186112 | 9.191010456 | 3.643657698 |
| R1632b | 4186112 | 20.831266271 | 1.607626515 |
| R832b | 4186112 | 25.148739492 | 1.331633182 |
| T816 | 4186112 | 67.227667328 | 0.498141574 |
| R32long | 10465280 | 16.994586025 | 4.926406555 |
| R32sustain | 20930560 | 29.935789880 | 5.593454546 |

The20MiB source run is1280/1280; its useful20930560B excludes32B diagnostic envelopes.
Its29.935789880s and5.593454546Mbit/s are not directly compared with a short4MiB A/B.

### Timers, observation boundaries and source audit

Exact dependencies: Pion WebRTC4.2.15, RTP1.10.2, interceptor0.1.45, ICE4.2.7;
individual relevant file hashes are in `dependency-audit.json`.

| Event | Exact configured timing | Evidence / limitation |
|---|---|---|
| VP8 media keyframe keepalive |2s; diagnostic first deadline+1s only in CShift | Actual TX/RX frames recorded, no application ID assigned to keepalive. |
| ICE selected-pair consent |2s, connecting checks200ms | `checkKeepalive` actually calls PingCandidate; do not rely on its stale idle-only comment. STUN not captured by RTP/RTCP interceptor. |
| RTCP SR/RR |1s per interceptor/stream | Outgoing SR and available incoming/outgoing RR retained. Incoming subscriber/SFU SR is not exported here; absence is not proof that SFU sends none. |
| NACK feedback / configured TWCC |100ms | Actual feedback packet types retained; configured TWCC is not proof of negotiated or emitted feedback. |
| Reassembly prune / lifetime |1s cleanup plus ingest-triggered prune /10s TTL | Expiry is later detection/cleanup, not the instant a fragment disappears. Exact expiry event times were not separately instrumented. |
| A0 reorder deadline |100ms checked on new packet arrival | Unchanged; no finite-deadline candidate enabled. |
| Capacity/resource sampler; CLI metrics |1s /1s;5s | These export counters, not packet-loss instants. |
| Signaling JSON ping / WebSocket control ping |5s /20s | Distinct from VP8 keepalive and ICE consent. |

Prior C1/C1b group intervals1.973760/2.105344s came from missing IDs and the offer
schedule, not2s snapshots. Their original trace did not identify individual RTP
packets: no retrospective exact loss boundary is invented. New media events have
`entry.ns`, a process-local monotonic timestamp. The outer JSON `utc` is **post-run
export time**, not packet time. Endpoint clocks are never subtracted for one-way
latency. Up to100000 metadata events stay in memory; every physical trace reports
overflow0. No per-packet disk logging occurs during the transfer.

`media-analysis.json` correlates sender/message/fragment headers and payload-body
hashes. SFU changes SSRC, sequence and timestamps: constant rewrite offsets are
learned from matching fragments within each session, not assumed. Timestamp-only
joins for missing first fragments are explicitly labelled inferred. Successful local
writes do not establish remote delivery; absence before the valid-RTP reader does
not locate the loss specifically inside SFU, network, SRTP or an unexported lower
boundary. All parsed incoming RTP, ordered RTP and assembled frames are retained.

### A/B implementation and correctness

A/0 keeps the exact33ms sample policy and2s ticker. Pion `WriteSample` ignores sample
wall time and passes duration ticks to `Packetize`; that packetizer assigns its
**current** timestamp to all packets of this frame, then advances the next timestamp.
Thus an idle2s still advances only2970 ticks; bursts can advance media time faster
than real time. Pion SR extrapolates from the first packet of the last new timestamp
at90000Hz, so the next synthetic sample can reset that mapping backwards. Merely
comparing33ms duration with2ms writer sleep was not used as proof of delivery loss.

B advances an empty sample by elapsed monotonic time before the actual zero-duration
sample. Empty packetization consumes neither RTP sequence nor PictureID and emits
no packet. Long elapsed intervals are split into safe1h clock advances; fractional
tick remainder remains Pion-owned. All fragments of one VP8 frame retain one timestamp.
Cached NACK retransmissions keep original headers; RS retransmission remains a new
carrier message as before. One writer serializes data and keepalive complete samples.
Insertion between fragments of a carrier message is legal and locally tested.

Local race checks cover byte-exact fragmented delivery with interleaved keepalives,
loss/reorder/duplicate/late retry, partial close, cancel, slow consumer, actual bound
Pion/RS32 with pacing OFF, fresh/rebound tracks, fractional ticks and25h simulated
clock wrap, sequence wrap, and PictureID wrap. Exact Pion omits optional PictureID
when its value is0, including wrap; it is not a new defect or a reason to change
packetization. The final local suite passes outside the sandbox where loopback TCP
is allowed. Initial wrong test assumptions (one TLS record per handshake Write,
mandatory PictureID at0) and a local observation-hook compile error are retained
with corrected retests. Sandbox socket-denial logs remain too. No media implementation
change was needed for these corrected test assumptions.

### C — same16448B carrier input,20s at target1Mbit/s

Each row offers/enqueues151 messages,2483648B including32B diagnostic envelope per
message. All151 are locally written as3 VP8 frames and15 unique RTP packets each:
2265 bulk RTP packets. No offered-rate escalation. Receive observation32s includes
12s drain; late bytes are **not** added to the20s numerator. No corruption/duplicate
application delivery. RX/ordered/assembled counts below are bulk fragments out of453,
not all controls/keepalives. Queue is the sampled sender depth, not an exact peak.

| Phase | Policy | Local full msgs | Unique full msgs | Useful received B | By20s Mbit/s | Full observation Mbit/s | RX/ordered/assembled frags | Expired builds | Loaded32B RTT p50 s | Sample queue |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CA1 | A | 151/151 | 130/151 | 2134080 | 0.774835 | 0.533509 | 404/404/397 | 7 | 1.584 | 0 |
| CShift | A/phase+1s | 151/151 | 141/151 | 2314656 | 0.893030 | 0.578648 | 431/431/425 | 2 | 1.185 | 0 |
| CA2 | A | 151/151 | 134/151 | 2199744 | 0.827366 | 0.549924 | 413/413/407 | 5 | 1.216 | 0 |
| CB1 | B | 151/151 | 133/151 | 2183328 | 0.827366 | 0.545827 | 411/411/406 | 6 | 1.184 | 2 |
| CB2 | B | 151/151 | 133/151 | 2183328 | 0.820800 | 0.545829 | 411/411/406 | 6 | 1.187 | 2 |
| CA3 | A | 151/151 | 133/151 | 2183328 | 0.827366 | 0.545823 | 411/411/406 | 6 | 1.304 | 0 |

CA1 is a pilot: optional RS trace-label discriminator was corrected before all main
pairs (no C payload effect), and local TLS-test compilation overlapped its tail.
CShift is diagnostic, not a capacity fix. Its actual first-bulk-write phase after
keepalive is1064ms versus CA1=1782ms and CA2=1531ms; the requested first-ticker+1s
does not imply an exactly1s shift relative to load, because probes/startup also vary.
Separate sessions/SFUs limit exclusive causal attribution; no runtime switch was added.

In CA2,40 bulk fragments have no first packet at the valid-RTP reader and6 have only
a partial frame. B1/B2/A3 have42 and5. Inferred complete-window RTP counts are2077,
2074,2074,2074 of2265 locally written packets. No complete matched payload packet
multiset fails local assembly. Consequently the missing messages are not invented
by reassembly TTL or a statistics sampler. Partial assembly expiry6 per main row is
not the same as17–18 missing messages: entire missing messages never create a build.

For complete multi-packet fragments in the first30 source messages, median local TX
span is0.11–0.16ms while raw-reader span is60.64–62.63ms across the main pairs. In the
last30 it is14.11–27.45ms at the reader. These are within-endpoint durations for
matched packets, **not one-way delay**; survivor-only samples are labelled as such.
This locates substantial spacing before reorder/reassembly and shows startup/path
service evolution. It does not prove a specific proprietary SFU discard algorithm.
The corrected B clock leaves both this pattern and periodic missing groups intact.

### R32 — same4MiB source in A/B/B/A

Both ends are Send32/Receive32; effective32 is observed, not32 against peer16.
Payload16384, RTO1s, retries8, age20s, SACK32, A0, Q0 and carrier limits stay fixed.
Every row delivers256/256,4186112 useful bytes, without corruption or duplicate
application data. These8–11s transfers are not sustained-capacity ceilings.

| Phase | Policy | Messages | Receiver s | Mbit/s | NL retry B | Ready-window s | Peak retained B | Peak SACKed B | Sample head age s | 32B RTT p50 s | Final pending/cap rejects |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| RA1 | A | 256 | 11.009673928 | 3.041770 | 1523840 | 9.156716 | 524288 | 294944 | 1.885 | 1.194 | 4/0 |
| RB1 | B | 256 | 9.538560826 | 3.510896 | 1605824 | 8.719644 | 524288 | 229376 | 2.005 | 0.986 | 4/0 |
| RB2 | B | 256 | 8.228303615 | 4.069964 | 458848 | 6.636626 | 524288 | 442368 | 1.531 | 0.672 | 1/0 |
| RA2 | A | 256 | 8.266898642 | 4.050962 | 524416 | 6.921363 | 524288 | 344096 | 2.004 | 0.640 | 1/0 |

Forward B/A +15.422799%; reverse +0.469052%. Different SFUs and startup/path evolution
prevent claiming the first percentage as a reproducible clock speedup. Retained,
unconfirmed and SACKed bytes are not physical bytes in flight; overlapping wait
counters are not summed. Retained/SACKed maxima and head ages in this table are
sampled observations, not continuous high-water measurements. The source inventory
retains all original RS32 work.

### P — Mux64 + Family TLS + RS32 only

Same single4MiB, parallel2×2MiB,64KiB echo and64KiB reverse-upload controls. Echo is
not pure network RTT; reverse time includes the verified32B hash acknowledgment.
All20 bodies match. Both endpoints export Mux counters at creation,100ms samples
and after Close; every counter remains0, including all six diagnostic error categories.
Any new error would cancel the phase rather than accepting a partial goodput result.

| Phase | Policy | Single s | Single Mbit/s | Parallel common s | Parallel Mbit/s | 64KiB echo s | Reverse control s | Bodies; errors C/S | NL retry B | Ready-window s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PA1 | A | 40.053940138 | 0.837731 | 20.063294021 | 1.672429 | 3.506 | 1.275 | 5/5;0/0 | 971504 | 5.330 |
| PB1 | B | 38.642618818 | 0.868327 | 19.334317116 | 1.735486 | 5.171 | 1.943 | 5/5;0/0 | 991234 | 6.527 |
| PB2 | B | 41.500717594 | 0.808527 | 23.887467366 | 1.404688 | 4.157 | 2.083 | 5/5;0/0 | 1853698 | 15.702 |
| PA2 | A | 39.859682965 | 0.841814 | 22.296837942 | 1.504896 | 5.865 | 2.163 | 5/5;0/0 | 1559024 | 15.458 |

Paired B/A single +3.652% /−3.954%, parallel +3.770% /−6.659%: signs reverse.
No repeatable P speed or latency gain is accepted. P/RS8 remains the separate parent
control, not a simultaneous8→32 plus clock change. Mux128 is absent. Actual TLS/RS
size histograms are saved; record-shape differences are not renamed TLS CPU overhead.

### Outgoing SR consistency, resources and budget

SR interval error is `RTP delta/90000 − local monotonic report interval`, wrap-aware.
It is not a cross-host latency estimate. Available NTP/RR values remain in raw events.

| Phase | Policy | Backwards SR steps | Max absolute interval error s |
| --- | --- | --- | --- |
| CA1 | A | 14 | 1.967603 |
| CShift | A | 12 | 2.681607 |
| CA2 | A | 13 | 1.967615 |
| CB1 | B | 0 | 0.000736 |
| CB2 | B | 0 | 0.000432 |
| CA3 | A | 12 | 1.967680 |
| RA1 | A | 5 | 3.520349 |
| RB1 | B | 0 | 0.000159 |
| RB2 | B | 0 | 0.000072 |
| RA2 | A | 5 | 5.758876 |
| PA1 | A | 6 | 7.948154 |
| PB1 | B | 0 | 0.000275 |
| PB2 | B | 0 | 0.001028 |
| PA2 | A | 10 | 7.247967 |

| Phase | CPU NL/client s | Max RSS NL/client MiB | NL sampled peak thread % core | NL throttle ms | NL steal % | Sample send/recv queue | Sample pending assemblies |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CA1 | 2.074/2.903 | 42.5/37.5 | 2.04 | 0.000 | 0.196 | 0/0 | 6 |
| CShift | 1.946/2.679 | 43.0/35.9 | 2.45 | 21.941 | 0.169 | 0/0 | 3 |
| CA2 | 1.794/3.047 | 42.9/36.5 | 1.85 | 8.480 | 0.188 | 0/0 | 5 |
| CB1 | 1.906/2.783 | 43.9/37.7 | 2.67 | 0.000 | 0.200 | 2/0 | 6 |
| CB2 | 1.874/2.847 | 42.7/38.1 | 2.93 | 20.630 | 0.178 | 2/0 | 6 |
| CA3 | 2.021/3.192 | 42.2/38.6 | 1.94 | 20.047 | 0.199 | 0/0 | 6 |
| RA1 | 1.266/1.551 | 44.2/39.8 | 2.64 | 0.000 | 0.185 | 5/0 | 4 |
| RB1 | 1.146/1.450 | 44.3/40.2 | 2.53 | 16.358 | 0.162 | 16/0 | 7 |
| RB2 | 1.123/1.722 | 44.2/40.1 | 3.31 | 0.000 | 0.227 | 66/0 | 2 |
| RA2 | 1.035/1.459 | 44.4/39.1 | 2.61 | 11.131 | 0.271 | 0/0 | 2 |
| PA1 | 4.342/5.484 | 57.2/63.8 | 2.93 | 3.600 | 0.218 | 4/1 | 4 |
| PB1 | 4.452/5.503 | 59.1/65.1 | 3.24 | 38.311 | 0.294 | 8/0 | 7 |
| PB2 | 4.670/6.611 | 62.0/64.4 | 3.05 | 24.992 | 0.187 | 14/0 | 4 |
| PA2 | 4.901/6.346 | 61.7/66.9 | 2.68 | 19.992 | 0.214 | 3/0 | 3 |

CPU values cover the whole test process, including setup/drain/post-run trace export,
not pure encryption cost. Thread scheduling waits are nonzero and retained in raw
resources; sparse cgroup throttle intervals are not hidden. No evidence supports a
compute ceiling requiring RU/2vCPU. GC, per-core load and per-thread scheduling are
saved; only test processes are sampled. Trace+hash calibration measured877Mbit/s in
the initial race check and842Mbit/s in the final retest, with bounded100000 records
and explicit overflow. Local memory-only regression
and calibration loops are separate from the network-source budget and emit no media.

| Phase | Selected SFU IPv4 | Controller total s incl setup/drain/cleanup | Source reserved B | Conservative outgoing media B |
| --- | --- | --- | --- | --- |
| CA1 | 37.9.73.77 | 69.414 | 2549184 | 2925082 |
| CShift | 37.9.69.114 | 62.369 | 2549184 | 2918413 |
| CA2 | 5.255.254.98 | 64.362 | 2549184 | 2900398 |
| CB1 | 5.255.254.229 | 62.650 | 2549184 | 2922896 |
| CB2 | 77.88.42.48 | 62.454 | 2549184 | 2921919 |
| CA3 | 37.9.127.38 | 64.394 | 2549184 | 2934640 |
| RA1 | 5.255.254.112 | 46.691 | 4259840 | 6489952 |
| RB1 | 5.255.254.87 | 40.424 | 4259840 | 6576766 |
| RB2 | 37.9.127.50 | 38.594 | 4259840 | 5324774 |
| RA2 | 77.88.42.246 | 40.353 | 4259840 | 5386414 |
| PA1 | 77.88.42.57 | 93.105 | 8585273 | 12157658 |
| PB1 | 5.255.254.190 | 97.902 | 8585273 | 12397261 |
| PB2 | 77.88.42.253 | 102.291 | 8585273 | 13528125 |
| PA2 | 5.255.254.252 | 103.572 | 8585273 | 13389451 |

New phase3 total **66675556B = 63.586765/128MiB** source;
**92773749B = 88.475942/256MiB** outgoing-media charge.
The first interceptor counts outgoing RTP/RTCP attempts at both test endpoints,
including NACK retransmissions, plus64B per packet and a bounded final tail allowance.
Receiver RX is not counted again. STUN/signaling are not media bytes. Reservations
include controls and all attempts, including CA1; no failed attempt is deleted to
restore budget. Per-phase limits, both configurations, session scope, IPv4 paths and
source/binary hashes are retained. No user room, production private key or public
proxy was used. Every next phase started after prior owned processes were closed.

### Short RS DATA22/34 — proved origin, no packing patch

The local observation-only copy uses the exact Family implementation and in-memory
test certificates. Both directions perform200 application Writes of16384B without
echo or benchmark envelopes. A Family Send builds one16396B plaintext Write including
its12B prefix. After TLS dynamic-record warmup (first5 writes),195/200 calls each
produce ciphertext Writes16406 and34B. Bridge `net.Pipe.Read` preserves those writes
with its65536B buffer; RS segmentation produces16384+22 and34. Concatenated ciphertext
is byte-exact across TLS Write → bridge Read → unique ordered RS DATA in each direction.
TLS1.3 AES128-GCM record overhead is22B. The34B record holds the **last12 application
bytes** of the16396B plaintext, not a standalone Family header. The22B RS tail contains
required encrypted bytes/type/authentication data; neither block is disposable.

Handshake is analysed separately: one underlying Write may contain several TLS
records, which caused the retained first local-test assertion failure. Controls in
old T8 include66B records; the client-to-NL control direction has no22/34 steady bulk
pair. Old NL→client T8 has251×16406 and251×34 unique records. Its all-attempt RS DATA
counts22=290,34=279: **569/925=61.514%** of
DATA attempts but **15866/5053318=0.314%** of DATA payload bytes.
Retries are included in those historical attempt fractions; unique TLS record counts
are separate. In steady local bulk, two of three RS slots carry only56 of16440
ciphertext bytes. This is structural slot pressure, not a measured pure CPU tax.

This is not the rejected socket read-alignment patch and not the existing batching
before TLS: the reproduced boundary is TLS ciphertext Write → RS segmentation.
No ciphertext is removed/reordered or acknowledged early. A packing fix is a new,
separate experiment, including finite flush/control-latency and integrity checks.

### Cleanup, provenance and next decision

Final readback: `2026-10-20T22:11:15.923579+00:00`; production equality confirmed. Baseline binary
`734b6ca6eb42be0367b703b657be87c624f3500ae408bbd771309ffaeb86128e`, profile hash
`abda003f81f75b9bb249c62972e7e2660e0910dfb00c2bdac91621f32ebd5805`, PID47501,
invocation`27e2c972a69f4527a454cbfd95e5bf50`. All28 peers, collectors and
owned systemd units are gone; remote stages and local ephemeral issuer/room/credential
files are removed. Provider room-metadata deletion is not supported by this workflow:
normal media closure is verified, not an unperformed metadata deletion. Phone/beta96,
directory/floors/revocations were not operated. No production rollback is needed.
Client IPv4 addresses/rules/routes match across all phases; postflight routes to
every selected SFU use `wlp0s20f3`.

Capsule: `state-client-build/mesh-capacity-phase3-20261020/`; exact inventories,
bounded raw traces, per-phase manifests, resources, calculations, failure logs and
cleanup receipts retained. Private kit `mesh-capacity-phase3-kit.tar.gz` SHA256
`3fa88e70d19b6c67e380fc21c2b5f7eb3d3b1dcf3c7ada8b6b2fcec96e18b903`. The operator refuses further load after final verification.
Parent kit and source inventory are unchanged, including the P816 warning.

**Next:** close this media speed experiment and separately test TLS→RS block
formation, keeping one known A0/OFF/Q0/Mux64 baseline and RS32 only as a lab choice.
Test exact ciphertext concatenation, bounded buffering/flush, small-control latency,
then T and P; do not promise that a gain below Mux improves a single application flow.
Fragmentation without FEC, then equal-wire-budget bounded FEC, remains conditional on
remaining burst-loss evidence. QUIC later, if needed, must run over carrier datagrams,
not ReliableStream or one re-collapsed Mux stream, with compatible Family admission.
No FEC, new fragmentation, QUIC, Android rollout or migration is implemented here.

## TLS→RS packing — 21 October2026

**COMPLETED LABORATORY COMPARISON; no production admission or deployment.**
16 isolated attempts, including retained failed attempts; all owned peers
and collectors closed. Source reservations106.260309/128MiB, conservative outgoing
media130.582132/256MiB. Failed attempts are not removed or refunded from this ledger.
Original phase1–3 results, long R32 controls and excluded old P816 remain unchanged.

### Contract, provenance and common controls

Pinned parent is phase3 exact source/binaryb95110c5…; original media A/phase0 in every
packing run. The monotonic timebase B remains separate and disabled. No pacer,
SACK-hole, queue-retry, read-alignment, finite-deadline, fragmentation, FEC, QUIC,
Mux128, hosting or library change. FRS1, Family prefix, TLS configuration, AEAD and
ALPN unchanged. 8 means both ends S8/R16, effective8;32 means both ends S32/R32,
effective32. Payload16384, RTO1s, MaxRetries8, MaxAge20s and SACK32 remain unchanged.

Packing is in the existing outbound Family TLS byte-stream adapter, before
ReliableStream.SendContext and before sequence/pending/window allocation. It never
combines already encoded FRS1 messages. The receiving ordered pipe is unchanged.
A uses the old net.Pipe reader→RS boundary. B0 copies into a finite FIFO and sends
available bytes without a coalescing timer. Selected B2 adds at most2ms intentional
tail waiting, timed from its oldest byte, not reset by later arrivals. Full blocks
have no intentional delay. The deadline fires without another Write. A blocked RS
window can delay actual dispatch beyond2ms; this is explicitly NOT a2ms network
timeout. No priority inference from22/34 and no ciphertext deletion/reordering.

One existing outbound worker plus the unchanged inbound worker, no per-Write worker.
Four16KiB copied FIFO blocks + one16KiB worker buffer =81920B owned payload storage;
the replaced A reader buffer is65536B, so data-buffer increment is16384B/session.
Only the active Write copies bytes; blocked caller slices remain caller-owned until
their Write returns, with no additional per-call payload copy or internal job queue.
Caller goroutines/stacks and one timer per waiting caller are not disguised as free
memory; the adapter cannot bound the number of concurrent callers created externally.
In the actual Family TLS path, Go TLS serializes ciphertext Write/alerts with its
outbound mutex, so only one such adapter writer is active; no new internal workers
are created for application writers waiting on the existing Family/TLS locks.
Three diagnostic histograms have at most256 distinct keys plus overflow(-1), three
incremental SHA256 states, four ages/lengths, mutex/channels and fixed connection
metadata. Metadata/map/runtime overhead is additional, not included in81920B;
the post-local report records the concrete connection struct size. Shared media
trace storage is unchanged A/B and is reported separately from coalescer memory.

Write success is local copied acceptance, not a carrier write or ACK. FIFO-full
writers wait on deadlines/cancellation; terminal send failures wake waiting calls.
No common lock spans RS SendContext. Explicit LabDrain(ctx) flushes accepted bytes
and waits for existing RS send depth zero, with a finite caller deadline; it is not
proof of application consumption. Ordinary Close is abortive, as in the old bridge.
Application completion is established by receiver counts/body hashes and the
within-run accepted→submitted→opposite ordered-receive SHA256 equality, not Close.
Explicit drain is the end-of-workload flush; shutdown itself performs no hidden
flush. Handshake and close_notify are covered locally, with dynamic TLS sizing on.

T pairs share binary`de3afb2c9b75373fe36f23c6cdc60e01382d42452b096b524d1d144cf4b1163c`.
Initial P pairs share binary`f8a36e614b459ec23ac7576a5ead0a5ed3b154e0a4a716c932ffc985ad3d321e`. The only non-test v1→v2 source change
allows32B E in the already loopback-only synthetic fixture; packing/Family/RS/media
sources are byte-identical. P32A1(v1) rejected the new32B idle probe before any bulk:
CLIENT_FAILED,0/32B, TCP reset, both ProtocolErrors0. It is excluded, retained with
its reservation, and repeated as P32A1r(v2). No successful T trial was substituted.

Common P harness uses FIN/EOF/Close and includes completion in full_seconds, with
32B idle and one32B concurrent-single control. Both A/B use exactly this workflow.
An initial local abrupt-close test saw a late ProtocolErrors increment; it remains
in local-6.log. It was not classified as a clean pass or hidden by counter reset.
The fixed orderly test passes with both endpoint counters0. The first snapshot did
not retain that failed local increment's category, so exact category is not invented.
Local-2 loopback restriction and build-8 duplicate instrumentation insertion are
also retained; corrected race/loopback tests and successful build-10 precede v2 live.

P8A(v2, unpacked baseline) is separately excluded: after complete64KiB echo body,
NL RS terminated recovery_exhausted. Sequence22/DATA44 had retries1..8, nine local
RTP writes, no matching carrier identity at the client's valid-RTP input; head age
~9.1s. Both Mux ProtocolErrors stayed0. No encrypted Mux kind is inferred from44B
and no exact SFU/lower-path drop owner is claimed. This is NOT the32B fixture bug
or a clean baseline. One fixed-parameter retry P8Ar is retained alongside it, not
used to erase the failed session or restore its budget. No retry/age limits changed.

Late review also found shutdown warnings in P32B1 and P8Ar: all seven bodies and
ALL accepted ciphertext bytes reached the opposite ordered bridge, but NL retained
its last DATA awaiting ACK and later reached recovery_exhausted during teardown.
P32B1 sent882/released881; P8Ar sent1161/released1160. Each last DATA has nine local
writes and one matching received/ordered/assembled frame; this is unlike P8A's
absent data. These are body-complete performance observations, NOT clean shutdown
acceptance; the table retains them explicitly rather than silently selecting them.

The helper LabDrain incorrectly treated terminal-reset SendDepth0 as successful
drain. A local regression reproduced this false success. V3 checks terminal status
even at depth0, drains before (not after) P abort and gives BOTH A/B a fixed finite2s
passive ACK settlement with the reader alive. It does not change the coalescer
worker, RS limits, media policy, ALPN or ciphertext. New clean P8A3/P8B3 use binary
`4e1ff73f20b03c3576944b2ca7cdffbe14bea6b7f6c77376e822f852e0dc4a87`; both policies use this same common teardown.
Final gates check ReleasedBlocks==DataSent on both peers, not just empty reset
state. These2s are in the controller's complete-phase duration, not smuggled into
per-request useful bytes. Request timing already includes body/FIN/EOF/stream Close.
The v3 strict-helper test and physical P8 pair validate the repair; old outcomes
and hashes remain unchanged. No application speed claim is based on this helper fix.

### Local correctness and formation

Real Family TLS tests: A/B0/B2 with8/16 and32/32,200 sequential16KiB application
Writes each direction plus mixed1/22/34/16383/16384/16385/32768/65536/7B bodies.
Each body is byte-exact and SHA256 checked; concatenated TLS input is compared to
unique ordered RS payload and opposite bridge bytes inside the SAME session.
No deterministic TLS randomness or comparison between independent ciphertexts.
Local full pattern: A~627–628 DATA versus B0~211–213 and B2~211–212, including
handshake/mixed tails; B2 chosen for the bounded lone-tail guarantee with repeatable
full-block formation, not selected from a live timer sweep. B0 also flushes a lone
tail without a future Write. Local legacy B2↔A passes both directions at both windows.
Loss/reorder/duplicate, ACK loss, slow consumer/full window, copied slice ownership,
partial n/deadline, late underlying failure, close/cancel/write/timer races, idle
request-response, handshake failure and bidirectional TLS close_notify pass.
Real authenticated Mux WINDOW_UPDATE releases a stopped bulk producer with no new
application Write; exact body and small subsequent response pass, counters0.
In-memory small idle request→response medians under race: A0.335289ms,
B0=1.363090ms, B2=4.807704ms (eight per policy, local-10.log). B2 costs
about4.472415ms versus A here, consistent with two directions of bounded tail
coalescing, not evidence of a zero-latency optimization. These are not live RTTs.

| Policy | Effective window | Legacy peer | Direction | TLS Writes | TLS records | Unique DATA | B/slot | DATA<16KiB | Flush causes |
|---|---|---|---|---|---|---|---|---|---|
| A | 8 | False | 0 | 424 | 427 | 628 | 5475.257962 | 424 | {} |
| A | 8 | False | 1 | 423 | 429 | 627 | 5483.792663 | 423 | {} |
| B0 | 8 | False | 0 | 424 | 427 | 213 | 16143.014085 | 5 | {'deadline': 5, 'full': 208} |
| B0 | 8 | False | 1 | 423 | 429 | 212 | 16218.575472 | 3 | {'deadline': 3, 'full': 209} |
| B2 | 8 | False | 0 | 424 | 427 | 212 | 16219.160377 | 3 | {'deadline': 3, 'full': 209} |
| B2 | 8 | False | 1 | 423 | 429 | 211 | 16295.440758 | 2 | {'deadline': 2, 'full': 209} |
| B2 | 8 | True | 0 | 424 | 427 | 212 | 16219.160377 | 3 | {'deadline': 3, 'full': 209} |
| B2 | 8 | True | 1 | 423 | 429 | 627 | 5483.792663 | 423 | {} |
| A | 32 | False | 0 | 424 | 427 | 628 | 5475.257962 | 424 | {} |
| A | 32 | False | 1 | 423 | 429 | 627 | 5483.792663 | 423 | {} |
| B0 | 32 | False | 0 | 424 | 427 | 214 | 16067.579439 | 6 | {'deadline': 6, 'full': 208} |
| B0 | 32 | False | 1 | 423 | 429 | 212 | 16218.575472 | 3 | {'deadline': 3, 'full': 209} |
| B2 | 32 | False | 0 | 424 | 427 | 212 | 16219.160377 | 3 | {'deadline': 3, 'full': 209} |
| B2 | 32 | False | 1 | 423 | 429 | 211 | 16295.440758 | 2 | {'deadline': 2, 'full': 209} |
| B2 | 32 | True | 0 | 424 | 427 | 212 | 16219.160377 | 3 | {'deadline': 3, 'full': 209} |
| B2 | 32 | True | 1 | 423 | 429 | 627 | 5483.792663 | 423 | {} |

### Local post-enqueue stall, calibration and memory

The first post-local fixture wrongly blocked SendContext for2.2s, exceeding the existing2s enqueue deadline; all four cases failed, retained in post-local-1.log/post-local-source.v1. It was repaired to model a bounded256-message queue accepting immediately, then pause its first bulk **actual write** for2.2s. This is a controlled post-enqueue boundary, not a complete RTP/fragment-queue emulator. Corrected post-local-2/3 pass with byte-exact delivery and bounded staging at both windows. No queue-retry patch was added.

| Policy | Window | Retained slots | Retained B | Retries before first bulk write | Retry payload B | FIFO max B | Exact completion |
|---|---|---|---|---|---|---|---|
| A | 8 | 8 | 32968 | 16 | 65936 | 0 | True |
| B2 | 8 | 8 | 131072 | 16 | 262144 | 65536 | True |
| A | 32 | 32 | 180928 | 64 | 361856 | 0 | True |
| B2 | 32 | 32 | 524288 | 64 | 1048576 | 65536 | True |

**A real remaining risk:** packing does not increase the observed pre-write retry attempts (16 at window8,64 at32), but larger occupied slots multiply queued retry bytes. Thus the requested no-amplification condition is NOT confirmed for bytes. Per-message retries/age and queues remain bounded, but this is a product-admission blocker, not a hidden queue-retry fix. The controlled2.2s pause is longer than normal dispatch and does not establish physical-loss causality.

| Calibration policy | TLS-shaped input B | Seconds | Mbit/s |
|---|---|---|---|
| A | 8417280 | 0.063361 | 1062.773370 |
| B0 | 8417280 | 0.072695 | 926.308359 |
| B2 | 8417280 | 0.075779 | 888.608649 |

Calibration includes incremental SHA256/counters and512 repetitions of16406+34B, no per-block disk logging; these in-memory figures are not network throughput.

| Policy | Owned payload B | Conn struct B | Three SHA states B | Measured retained heap B/session |
|---|---|---|---|---|
| A | 65536 | 680 | 360 | 97744.625000 |
| B2 | 81920 | 680 | 360 | 113900.750000 |

Memory accounting models128 simultaneously retained sessions, all three diagnostic histograms at cap, both pipe ends and two timers/session (coalescing plus one waiting writer), after GC. It includes allocated metadata and map overhead, not just payload; B−A is about16KiB/session. It is a measured retained Go heap model, not a hard RSS bound: existing worker stacks, allocator/GC transient space, unchanged inbound bridge/RS/carrier storage and caller-owned waiting input must also fit the process budget. Actual TLS serializes the adapter Write; arbitrary externally-created waiting callers are not bounded by this adapter. Physical RSS and retained-RS observations below include those broader effects.

### T — reliable application delivery and slot use

Each successful T trial has256/256 messages,4186112 useful B excluding the32B
diagnostic envelope per message, no corruption. Timing is receiver-monotonic from
requesting the transfer to the final useful message; whole controller duration is
recorded separately and includes setup, drain, confirmation and cleanup.
DATA counts below are whole-session unique DATA, including handshake/control, not
ACK/OPEN/RESET or retransmission attempts. A counts are derived by exact16384-byte
segmentation of successful bridge submissions; B submissions already fit one slot.

| Phase | Packing | Effective | Seconds | Mbit/s | TLS Writes | TLS records | Unique DATA | B/slot | DATA<16KiB | DATA≤256B | Retry payload B | Ready-full s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T8A | A | 8 | 53.771057 | 0.622805 | 556 | 561 | 806 | 5227.848635 | 555 | 543 | 737626 | 53.053973 |
| T8B | B2 | 8 | 27.612931 | 1.212798 | 539 | 545 | 262 | 16078.587786 | 6 | 4 | 978112 | 26.939623 |
| T32A1 | A | 32 | 18.947604 | 1.767448 | 534 | 540 | 785 | 5365.936306 | 534 | 522 | 1051978 | 18.167099 |
| T32B1 | B2 | 32 | 8.614834 | 3.887353 | 525 | 531 | 262 | 16075.061069 | 6 | 4 | 1032324 | 6.868933 |
| T32B2 | B2 | 32 | 10.863671 | 3.082650 | 526 | 532 | 263 | 16014.190114 | 7 | 5 | 1214958 | 8.113084 |
| T32A2 | A | 32 | 20.248767 | 1.653873 | 536 | 541 | 786 | 5359.193384 | 535 | 523 | 1168368 | 18.961954 |

| Contrast | B/A goodput change % |
|---|---|
| T8 | 94.731434 |
| T32 forward | 119.941611 |
| T32 reverse | 86.389730 |

### P — Mux64 + Family TLS, separate windows

Each body-complete P trial: single4MiB download, parallel2×2MiB download,64KiB echo,64KiB reverse and two32B controls; all seven bodies/checks complete. P32B1/P8Ar retain shutdown warnings and are excluded from clean completion acceptance. Parallel time is the union from first start to last completion, not summed per-stream time. Every endpoint is monitored from Mux creation through final Close; Mux ProtocolErrors stay0.

| Phase | Packing | Effective | Single s | Single Mbit/s | Parallel s | Aggregate Mbit/s | NL unique DATA | B/slot | DATA<16KiB | DATA≤256B |
|---|---|---|---|---|---|---|---|---|---|---|
| P32A1r | A | 32 | 48.497222 | 0.691884 | 25.523223 | 1.314663 | 2211 | 3869.809136 | 2171 | 111 |
| P32B1 | B2 | 32 | 45.796007 | 0.732693 | 25.350637 | 1.323613 | 882 | 9647.501134 | 589 | 187 |
| P32B2 | B2 | 32 | 51.210404 | 0.655227 | 26.870017 | 1.248769 | 865 | 9836.876301 | 572 | 173 |
| P32A2 | A | 32 | 49.040681 | 0.684216 | 24.953968 | 1.344653 | 1683 | 5069.866904 | 1589 | 208 |
| P8Ar | A | 8 | 53.795692 | 0.623738 | 27.185553 | 1.234274 | 1161 | 7331.931094 | 1091 | 94 |
| P8B | B2 | 8 | 49.180449 | 0.682272 | 25.469032 | 1.317460 | 773 | 11007.681759 | 512 | 108 |
| P8A3 | A | 8 | 53.354035 | 0.628901 | 34.360206 | 0.976549 | 1228 | 6933.328990 | 1105 | 95 |
| P8B3 | B2 | 8 | 48.730231 | 0.688575 | 25.268479 | 1.327917 | 781 | 10897.500640 | 517 | 93 |

| Contrast | Single B/A % | Aggregate B/A % |
|---|---|---|
| P32 forward (shutdown warning) | 5.898363 | 0.680799 |
| P32 reverse | -4.236879 | -7.130806 |
| P8 v2 (shutdown warning) | 9.384303 | 6.739637 |
| P8 v3 clean | 9.488575 | 35.980510 |

| Phase | Client terminal/sent/released | NL terminal/sent/released | Final ACK proof |
|---|---|---|---|
| T8A | {'terminal': '', 'sent': 44, 'released': 44} | {'terminal': '', 'sent': 806, 'released': 806} | True |
| T8B | {'terminal': '', 'sent': 27, 'released': 27} | {'terminal': '', 'sent': 262, 'released': 261} | False |
| T32A1 | {'terminal': '', 'sent': 23, 'released': 23} | {'terminal': '', 'sent': 785, 'released': 784} | False |
| T32B1 | {'terminal': '', 'sent': 13, 'released': 13} | {'terminal': '', 'sent': 262, 'released': 262} | True |
| T32B2 | {'terminal': '', 'sent': 14, 'released': 14} | {'terminal': '', 'sent': 263, 'released': 262} | False |
| T32A2 | {'terminal': '', 'sent': 24, 'released': 24} | {'terminal': '', 'sent': 786, 'released': 786} | True |
| P32A1r | {'terminal': 'cancelled', 'sent': 1995, 'released': 1995} | {'terminal': 'cancelled', 'sent': 2211, 'released': 2211} | True |
| P32B1 | {'terminal': 'cancelled', 'sent': 608, 'released': 608} | {'terminal': 'recovery_exhausted', 'sent': 882, 'released': 881} | False |
| P32B2 | {'terminal': 'cancelled', 'sent': 603, 'released': 603} | {'terminal': 'cancelled', 'sent': 865, 'released': 865} | True |
| P32A2 | {'terminal': 'cancelled', 'sent': 1512, 'released': 1512} | {'terminal': 'cancelled', 'sent': 1683, 'released': 1682} | False |
| P8Ar | {'terminal': 'cancelled', 'sent': 1113, 'released': 1113} | {'terminal': 'recovery_exhausted', 'sent': 1161, 'released': 1160} | False |
| P8B | {'terminal': 'cancelled', 'sent': 594, 'released': 594} | {'terminal': 'cancelled', 'sent': 773, 'released': 772} | False |
| P8A3 | {'terminal': 'cancelled', 'sent': 1166, 'released': 1166} | {'terminal': 'cancelled', 'sent': 1228, 'released': 1228} | True |
| P8B3 | {'terminal': 'cancelled', 'sent': 603, 'released': 603} | {'terminal': 'cancelled', 'sent': 781, 'released': 781} | True |

Rows cancelled with outstanding ACKs prove peer byte receipt through matching ordered-stream hashes, but not full sender acknowledgement before abort. Recovery-exhausted rows additionally fail clean session completion. Only the v3 P8 pair is claimed as validation of the repaired explicit-drain/ACK gate. P32 performance is not repeated after that repair; it already showed no repeated gain.

Final clean P8 single/aggregate improves in one matched pair, but the aggregate baseline also varies substantially between v2 and v3 sessions. It is an observation, not repeatable product acceptance. P32 ready-window pressure falls sharply while application throughput barely improves or regresses; Mux64/product-like supply/credit is the next distinguishing boundary. Exact per-stream credit-ready duration is not exported, so no precise fraction of time is assigned to it.

T is intentionally a different source shape from the product-like P writer, which already batches plaintext. Gains are not transferred between these tables and are not claimed as TLS CPU savings. No A8→B32 comparison is used as a packing-only effect.

### Small-message latency and queues

| T phase | Idle RTT s | Loaded RTT s | Outstanding at end | Boundary |
|---|---|---|---|---|
| T8A | 1.963290 | 0.517946 | 2 | 32B probe medians; no one-way inference |
| T8B | 0.749550 | 1.632135 | 0 | 32B probe medians; no one-way inference |
| T32A1 | 1.273159 | 0.639840 | 1 | 32B probe medians; no one-way inference |
| T32B1 | 1.358574 | 1.208363 | 1 | 32B probe medians; no one-way inference |
| T32B2 | 1.075533 | 1.290473 | 2 | 32B probe medians; no one-way inference |
| T32A2 | 1.451777 | 1.031457 | 1 | 32B probe medians; no one-way inference |

| P phase | Idle first B s | Idle completion s | Loaded first B s | Loaded completion s |
|---|---|---|---|---|
| P32A1r | 2.844883 | 4.181527 | 2.510650 | 2.909384 |
| P32B1 | 3.258457 | 4.399188 | 0.996607 | 1.659881 |
| P32B2 | 3.664998 | 5.041917 | 0.991289 | 1.648717 |
| P32A2 | 1.901065 | 3.898400 | 2.152187 | 2.737100 |
| P8Ar | 1.812106 | 2.878066 | 1.284634 | 1.924301 |
| P8B | 1.911135 | 3.270975 | 1.364695 | 3.047374 |
| P8A3 | 3.628332 | 5.171240 | 2.073339 | 2.657853 |
| P8B3 | 6.256165 | 8.513073 | 1.717973 | 2.344047 |

P has one idle and one loaded small request per phase, not a latency distribution. Separate SFU sessions and startup effects limit attribution of these differences to2ms alone.64KiB echo is retained as a workload/control, never renamed pure network RTT.

| Phase | FIFO max B | Oldest max ms | Timer wait s | RS call wait s | FIFO Write wait s | Eligible dispatch max ms | Carrier sampled queue | Assemblies sampled | Flush causes |
|---|---|---|---|---|---|---|---|---|---|
| T8A | 0 | 0.000000 | 0.000000 | 53.114096 | 0.000000 | 0.000000 | 6 | 0 | {} |
| T8B | 65536 | 1659.384647 | 0.011239 | 26.995067 | 26.780426 | 0.622588 | 8 | 0 | {'deadline': 6, 'full': 256} |
| T32A1 | 0 | 0.000000 | 0.000000 | 18.261414 | 0.000000 | 0.000000 | 22 | 0 | {} |
| T32B1 | 65536 | 960.958789 | 0.011731 | 6.905271 | 6.782695 | 0.361040 | 3 | 0 | {'deadline': 6, 'full': 256} |
| T32B2 | 65536 | 1478.006575 | 0.013612 | 8.140071 | 7.987783 | 0.358424 | 19 | 0 | {'deadline': 7, 'full': 256} |
| T32A2 | 0 | 0.000000 | 0.000000 | 19.025961 | 0.000000 | 0.000000 | 1 | 0 | {} |
| P32A1r | 0 | 0.000000 | 0.000000 | 13.658676 | 0.000000 | 0.000000 | 15 | 1 | {} |
| P32B1 | 65536 | 10.069489 | 1.326732 | 0.065662 | 0.002373 | 2.723811 | 4 | 1 | {'deadline': 589, 'full': 293} |
| P32B2 | 65536 | 8.043402 | 1.294467 | 0.071599 | 0.002185 | 1.886895 | 4 | 1 | {'deadline': 572, 'full': 293} |
| P32A2 | 0 | 0.000000 | 0.000000 | 14.865621 | 0.000000 | 0.000000 | 17 | 1 | {} |
| P8Ar | 0 | 0.000000 | 0.000000 | 71.935258 | 0.000000 | 0.000000 | 3 | 1 | {} |
| P8B | 65536 | 938.124047 | 0.779876 | 21.988970 | 0.001183 | 2.237181 | 5 | 1 | {'deadline': 512, 'full': 261} |
| P8A3 | 0 | 0.000000 | 0.000000 | 80.644643 | 0.000000 | 0.000000 | 6 | 2 | {} |
| P8B3 | 65536 | 902.716410 | 0.835118 | 22.924470 | 0.005088 | 8.334594 | 18 | 1 | {'deadline': 517, 'full': 264} |

Oldest age can include earlier RS backpressure. DeadlineOvershoot is NOT pure scheduler delay. Eligible-dispatch delay excludes the preceding blocked RS call. Different waits overlap and must not be added. Retained/SACKed bytes are not physical bytes in flight. Queue/assembly maxima are sampled, not asserted continuous maxima. Limits256 carrier send queue/16 incomplete assemblies are unchanged.

| Phase | Sampled retained B | Unconfirmed B | SACKed B | RS buffer high-water B | Retry payload B | RS ready-full s | NL Mux flow-stall count |
|---|---|---|---|---|---|---|---|
| T8A | 62410 | 62410 | 32880 | 65770 | 737626 | 53.053973 | — |
| T8B | 131072 | 131072 | 81920 | 131138 | 978112 | 26.939623 | — |
| T32A1 | 180850 | 180806 | 115080 | 208920 | 1051978 | 18.167099 | — |
| T32B1 | 524288 | 524288 | 229376 | 524354 | 1032324 | 6.868933 | — |
| T32B2 | 524288 | 524288 | 327680 | 524354 | 1214958 | 8.113084 | — |
| T32A2 | 197302 | 180818 | 121824 | 208920 | 1168368 | 18.961954 | — |
| P32A1r | 132480 | 132458 | 67692 | 132502 | 2002737 | 13.560760 | 6123 |
| P32B1 | 131952 | 131864 | 66040 | 132040 | 1445286 | 0.000000 | 2149 |
| P32B2 | 131930 | 127940 | 73956 | 132018 | 1413490 | 0.000000 | 2171 |
| P32A2 | 131908 | 131821 | 110120 | 132612 | 1530998 | 14.756654 | 5111 |
| P8Ar | 94798 | 94798 | 40946 | 106772 | 1256816 | 71.851992 | 3283 |
| P8B | 115816 | 115816 | 53476 | 131072 | 1462752 | 21.928425 | 2144 |
| P8A3 | 98832 | 94176 | 47430 | 98880 | 1474072 | 80.515960 | 3361 |
| P8B3 | 131072 | 114784 | 57996 | 131072 | 1408292 | 22.849143 | 2208 |

Packing can increase actual retained/retry BYTES per slot even with unchanged slot and retry limits. Existing RS maxima remain S8×16384=128KiB/R16×16384=256KiB, or S32/R32×16384=512KiB each; these are additional existing transport bounds, not included in the80KiB coalescer storage. The table exposes observed buffering rather than calling the buffer increase free. Mux flow-stall counts are exported; precise NL per-stream credit-ready duration was not exported in this harness and is not invented. The separate controlled pre-local-write stall test is retained in post-local logs; queue-retry semantics were not changed.

### Resources, paths and limits

| Phase | Linux selected SFU IP | NL user CPU s | NL sys CPU s | NL max RSS KiB | Peak thread %core | Cgroup throttle µs | Host steal % |
|---|---|---|---|---|---|---|---|
| T8A | 5.255.254.152 | 1.461374 | 1.457585 | 46400 | 2.374418 | 8102 | 0.183616 |
| T8B | 5.255.254.76 | 1.149277 | 1.119532 | 47504 | 3.024821 | 22136 | 0.233418 |
| T32A1 | 77.88.42.170 | 0.866406 | 0.881732 | 46344 | 2.994239 | 9164 | 0.284018 |
| T32B1 | 5.255.227.23 | 0.517872 | 0.540526 | 46352 | 2.786068 | 9754 | 0.155400 |
| T32B2 | 5.255.254.29 | 0.646130 | 0.770482 | 45960 | 2.352441 | 14559 | 0.129912 |
| T32A2 | 5.255.254.84 | 0.806682 | 0.743461 | 45000 | 2.591354 | 0 | 0.140174 |
| P32A1r | 37.9.118.221 | 2.773262 | 2.471363 | 64140 | 2.943055 | 7791 | 0.169036 |
| P32B1 | 37.9.127.112 | 2.557990 | 2.355574 | 60996 | 2.311159 | 0 | 0.189054 |
| P32B2 | 37.9.118.150 | 2.620349 | 2.451290 | 59968 | 2.343204 | 22640 | 0.184128 |
| P32A2 | 77.88.42.22 | 2.672945 | 2.351407 | 61380 | 2.765846 | 38075 | 0.138710 |
| P8Ar | 5.255.254.208 | 2.736160 | 2.290472 | 61708 | 7.207331 | 101837 | 0.176777 |
| P8B | 77.88.43.81 | 2.538534 | 2.213465 | 61332 | 2.462513 | 7673 | 0.188305 |
| P8A3 | 5.255.254.62 | 2.940845 | 2.445299 | 60940 | 3.640789 | 22061 | 0.161840 |
| P8B3 | 77.88.42.92 | 2.586169 | 2.654236 | 57996 | 2.739464 | 31994 | 0.181127 |

Same NL host and Linux network; every phase has its own media session/room. Full selected publisher/subscriber ICE paths, both configurations, source inventory, hashes, resources and monotonic boundaries are retained. CPU includes setup/drain/export, not pure TLS processing. No RU migration or host CPU ceiling is inferred. The wire ledger counts each peer outgoing RTP/RTCP including retransmits plus conservative packet/tail allowance, not receiver RX again; STUN/signaling are not media bytes.

### Decisions and next product gate

| Criterion | Classification | Evidence / limit |
|---|---|---|
| BYTE_STREAM_PRESERVED | CONFIRMED for completed bodies / local fault tests | Both-direction same-session SHA256 accepted=submitted=ordered peer; failed attempts remain separate. |
| BOUNDED_FLUSH_AND_BACKPRESSURE | CONFIRMED within tested contract; retry-byte risk remains | 64KiB FIFO +16KiB worker; finite lone-tail flush, deadlines/cancel/failure;2ms coalescing only. |
| RS_SLOT_EFFICIENCY | CONFIRMED | Measured whole-session DATA/bytes per slot, including new small tails; no deletion of22/34. |
| T_STACK_GAIN | CONFIRMED in tested pairs | {'T8': 94.731, 'T32 forward': 119.942, 'T32 reverse': 86.39} |
| P_SINGLE_AND_AGGREGATE_GAIN | NOT_CONFIRMED as repeatable P32 gain; one positive clean P8 pair | {'P32 forward (shutdown warning)': {'single': 5.898, 'parallel': 0.681}, 'P32 reverse': {'single': -4.237, 'parallel': -7.131}, 'P8 v2 (shutdown warning)': {'single': 9.384, 'parallel': 6.74}, 'P8 v3 clean': {'single': 9.489, 'parallel': 35.981}} |
| SMALL_REQUEST_LATENCY | LOCAL cost confirmed; LIVE attribution limited | Local B2 RTT median +4.472415ms. Sparse separate-SFU idle/loaded controls do not prove non-regression. |
| LEGACY_COMPATIBILITY | CONFIRMED local protocol/byte-stream interop | B2↔unpacked A,8/16 and32/32, both directions; no new FRS1/ALPN. Installed Android interop NOT_RUN. |
| PRE_WRITE_RETRY_AMPLIFICATION | CONFIRMED for bytes, not attempt count | At2.2s post-enqueue stall, denser slots increase queued retry bytes; product gate remains blocked. |
| PRODUCTION_UNCHANGED | BINARY/FLAGS confirmed; whole-run runtime/profile equality NOT confirmed | No lab production mutation. Each phase stable, but process/invocation/profile hash changed between v2 and v3; cause not established. |

**Not ready for product admission.** The adapter is usable for the next isolated P-writer/credit and latency experiment; slot efficiency and T gain alone do not justify enabling it. Before product integration: (1) establish graceful admission-stop/drain/error and net.Conn conformance gates; (2) resolve or explicitly bound the observed pre-write retry-byte amplification in a separate one-mechanism experiment; (3) repeat P single/parallel and enough small controls with strict final ACK/protocol checks, synchronized ready-data/credit observations and a prespecified latency threshold. Only after those gates, factor this as per-session policy selected before TLS, default OFF, unchanged peer/ALPN/FRS1 and RS8 defaults. Android/native/mobile interop and revocation/expiry require separate authorization. RS32 remains independently lab-only. No APK, production binary/config or public release is produced here.

### Production readback and all-attempt ledger

| First phase | First observed UTC | Last phase | Last observed UTC | PID | Invocation | Profile SHA256 |
|---|---|---|---|---|---|---|
| T8A | 2026-10-20T22:38:41.119082+00:00 | P8B | 2026-10-20T23:03:29.806788+00:00 | 47501 | 27e2c972a69f4527a454cbfd95e5bf50 | abda003f81f75b9bb249c62972e7e2660e0910dfb00c2bdac91621f32ebd5805 |
| P8A3 | 2026-10-20T23:09:45.627691+00:00 | P8B3 | 2026-10-20T23:15:43.853599+00:00 | 160591 | b329a63bc3894b5cbc75ab288cba0d16 | 58643bc58f0e84bba790d01451c942acac1377a76733edce4249af3a1df2401c |

Fresh full preflight/final equality is **False**; binary/flags equality is true, every phase start/end equality is true, and each displayed A/B pair stays within one observed production epoch. The runtime/profile transition happened between series, outside an active lab phase. Its cause is not established by this evidence; the profile was hashed on its host only; its contents were not inspected/exported, and keys, identity or security state were not copied/reverted. The operator only reads production metadata and starts/stops its namespaced test units. The task made no production deployment, restart or config change; it cannot claim external global state stayed unchanged. Do not compare v2/v3 as if runtime background and teardown were identical.

| Attempt | Result/error | Shutdown outcome | Whole controller s | Source reserved B | Media charged B |
|---|---|---|---|---|---|
| T8A | bodies completed | all DATA ACKed | 89.018712 | 4259840 | 6047616 |
| T8B | bodies completed | unconfirmed_at_cancel | 64.375972 | 4259840 | 6009430 |
| T32A1 | bodies completed | unconfirmed_at_cancel | 51.066581 | 4259840 | 6258478 |
| T32B1 | bodies completed | all DATA ACKed | 42.564573 | 4259840 | 5973675 |
| T32B2 | bodies completed | unconfirmed_at_cancel | 43.351484 | 4259840 | 6195056 |
| T32A2 | bodies completed | all DATA ACKed | 50.096665 | 4259840 | 6391958 |
| P32A1 | CLIENT_FAILED | all DATA ACKed | 27.510507 | 8586297 | 173793 |
| P32A1r | bodies completed | all DATA ACKed | 115.876898 | 8586297 | 13914139 |
| P32B1 | bodies completed | recovery_exhausted | 121.644899 | 8586297 | 11992780 |
| P32B2 | bodies completed | all DATA ACKed | 128.311575 | 8586297 | 11949820 |
| P32A2 | bodies completed | unconfirmed_at_cancel | 123.953715 | 8586297 | 12867122 |
| P8A | CLIENT_FAILED | recovery_exhausted | 59.700028 | 8586297 | 546008 |
| P8Ar | bodies completed | recovery_exhausted | 126.031487 | 8586297 | 12186307 |
| P8B | bodies completed | unconfirmed_at_cancel | 117.821269 | 8586297 | 11993529 |
| P8A3 | bodies completed | all DATA ACKed | 136.631929 | 8586297 | 12499727 |
| P8B3 | bodies completed | all DATA ACKed | 137.848265 | 8586297 | 11925852 |

Final readback `2026-10-20T23:25:00.300712+00:00`: production binary/flags equality; local/remote owned peers,
collectors, units and stages absent; isolated keys/room inputs removed. Provider room
metadata deletion is not supported by this workflow; normal media closure verified.
Client network equality: `True`. Full raw results,
failed attempts, all three source revisions, patches, calculations and local tests:
`state-client-build/tls-rs-packing-20261021/`. Private kit SHA256
`b598d894bde864a81cc7d15f94f6050534b39eb510f9fbe54ef788febde6e267`. No push, publication, purchase, migration or user switching.
FEC, carrier fragmentation and QUIC remain later conditional work, not this candidate.

## P-stack bottleneck and packing interaction — 21 October2026

**CLOSED LABORATORY EXPERIMENT; no product admission, deployment or new APK.**
The earlier T_GAIN remains confirmed in its comparisons; P32_GAIN was not
established there; P8_GAIN remains one positive clean pair. This task does not
repeat those T/window matrices or substitute T goodput for P. Six new clean P
phases plus one retained controller-completion failure use the same lab binary.
Packing alone still has no repeatable material single+parallel benefit in P.

[Machine-readable evidence](2026-10-21-p-stack-interaction.evidence.json) ·
[Replay/measurement contract](../../tests/fixtures/tls_rs_packing/interaction/README.md).
Private capsule: `state-client-build/p-stack-interaction-20261021/`.

### Exact base, changes and limits

Parent is the complete local strict-drain v3 inventory, binary
`4e1ff73f20b03c3576944b2ca7cdffbe14bea6b7f6c77376e822f852e0dc4a87`, not an older
pushed checkout. All live attempts use
`c97d4192f3c54396677da09896cd16784c60445ebd9ada633713787eb595148a`.
The fresh-copy replay reproduces its entire source inventory exactly. Kit SHA256:
`46fe0948d114bff237825ff27c69eb100a155a472136473f7486b97be25e2a9e`.
No push is required or performed. Uncommitted prior work and old capsules remain.

B2 and `packing.go` are unchanged: copy ciphertext into bounded64KiB FIFO plus
16KiB worker **before** RS sequence allocation, full blocks immediate, oldest-tail
intentional wait at most2ms. Ciphertext/order/FRS1/TLS and existing ALPN preserved.
The only new execution paths are lab observations, access to the already-existing
negotiated64/128 profile with lab RS32, and the harness completion barrier.
No writer scheduling patch, new ALPN, pacer, timebase fix, FEC or payload/RTO change.
The parent already contains dormant Q1/pacing/timebase candidate code: **Q0 and
original media A/phase0 remain selected in every A/B/C/D phase**. Q1 is explicitly
tested separately, never silently enabled in D or reapplied as another patch.

| Mode | Packing | Negotiated Mux at both ends | Effective RS |
|---|---|---|---|
| A | OFF | LEGACY64 /65536 |32/32|
| B | B2 | LEGACY64 /65536 |32/32|
| C | OFF | CREDIT128 /131072 |32/32|
| D | B2 | CREDIT128 /131072 |32/32|

**A is a lab RS32 control, not current production RS8.** Payload16384, RTO1s,
MaxRetries8, MaxAge20s, receiver policy, frame/source sizes and media/timebase are
fixed. Profile selection uses existing authenticated negotiation, not a global
default change. Credit never exceeds128KiB and flow control is never disabled.

New live ledger:60,130,560B =57.344971/64MiB source reservations,90,499,447B =
86.306998/128MiB conservative outgoing media, including the failed A1. Local matrix
bulk is separately6MiB, all in-memory/loopback, no external media. No further load
is pending. Actual transfer context180s, final drain10s, worker250s and owned
systemd unit280s; stricter individual request150s remains. Raw reservation metadata
inherited `runtime=510`, but the executed unit command was280s in every attempt;
`manifest-corrections.json` retains this explicit metadata correction, not a
retroactive runtime change. Pre-execution Python import failure consumed0 bytes.

### External state change: bounded investigation, uncertainty retained

The changed process was **the same** NL
`family-connect-restricted-bootstrap.service`: PID47501/invocation27e2c972… to
PID160591/invocationb329a63b… between
`2026-10-20T23:03:29.806788Z` and `23:09:45.627691Z`. Those are exact observation
bounds, **not an invented exact restart timestamp**. P8B had finished before this
gap; P8A3 began afterwards. No active old lab phase or displayed A/B pair spans it.

The old hash is SHA256 of the **whole**
`friends-restricted/gateway.json` file, including whitespace. Its accepted schema
contains `authority`, `certificate`, `private_key`, `revocations`, `family`,
`gateway`, `minimum_revision`, `minimum_crl`. It is not a transport-settings hash
and contains no directory publication or pacing/Mux setting. There are no retained
old/new per-field fingerprints: certificate, key, CRL, identity/floor or formatting
changes cannot be distinguished. Binary/flag equality does not prove every other
directory/credential field stayed unchanged. No renewal cause is asserted.

Existing local receipts establish isolation. Bounded remote historical journal
reads timed out (including the final60s exact-unit query); no usable historical
event was recovered. This remains PARTIAL/CAUSE_UNRESOLVED, not an excuse to erase
measurements or stop local tests. No timers/renewal/reset/restart/rollback were used.
The lab does **not** connect to this production process: its own fresh room,
disposable authority/profiles, CLI binary, loopback fixture and namespaced unit
serve each phase. The common host/SFU/provider/background can still vary.

New live pre/post readbacks,06:54:14–07:09:52UTC, and final07:11:11UTC all agree:
PID429617, invocation9922c6ee79f64e94aa87e8ec47313f5c,
binary734b6ca6eb42be0367b703b657be87c624f3500ae408bbd771309ffaeb86128e,
profile660960483c01476e99a9306591796f2ee190f8c2df1aa61b0efa09576eff8642,
OFF/Q0/LEGACY64. This is a new pinned epoch, not equality with last night's profile.
No current lab influence on production was observed; no production traffic path
or identities were used. Bootstrap96/gateway1011/A0 remains the actual baseline.

### Why P is different: common intervals and the real writer

`writer-lineage.json` proves byte-identical `Mux.forward`, `MuxStream.Write`,
`pickLocked/nextLocked`, `writeLoop`, and Family `SendBatchContext` functions against
the pinned product-lineage source. The generator precomputes deterministic bytes,
then TCP→the **real**16KiB forwarder→MuxStream.Write supplies data. It is not T's
repeated independent Family plaintext Write loop. P already limits DATA to16340B
and batches ready plaintext within the existing16362B Family/TLS batch budget.

The observed/code-verified chain is:

1. TCP source read supplies ready bytes. MuxStream.Write reserves send credit and
   one queued DATA; ready data waits if credit is zero or that queue is occupied.
2. The real writer selects ready frames, including creditPending/WINDOW_UPDATE,
   and forms only an **immediately available** plaintext batch. It does not wait
   for bulk to fill a batch. Control priority is already bounded to8 selections.
3. It releases the common Mux mutex **before** blocking Family/TLS Write. The
   independent reader can continue receiving and applying WINDOW_UPDATE. The
   per-stream write mutex preserves DATA/FIN ordering; it is not the shared lock.
4. TLS ciphertext enters the unchanged A adapter or B2 FIFO, then RS submission,
   local carrier enqueue/write and remote ordered receipt. B2 never reorders
   encrypted control by length. RS ACK releases reliability slots/retention,
   **not** Mux send credit.
5. Remote Family/Mux must receive a complete frame. Application Mux.Read copies
   bytes out and frees receive memory, then adds creditPending; only this consumed
   memory is credited. The writer selects WINDOW_UPDATE and the sender's reader
   applies it. Stream IDs and cumulative byte/credit totals link both hosts;
   no subtraction of unsynchronized host clocks gives a one-way latency.

Old P32 had only100ms aggregate Mux Stats, not sender stream-ready/credit lifecycle.
Its disappearing RS ReadyFull wait (13.561/14.757s→0) did not identify a whole
critical path by itself. New metadata-only observations cap at32768 events, with
zero overflow in every new phase, plus existing bounded retired-stream counters.
Live samples are100ms, local10ms. Table samples use the **same sender-side active
stream interval**; no sum or independence assumption for overlapping waits.

| Clean phase / single stream15 | Active samples | Ready + zero credit | Also RS depth<32 AND not RS-ready | Stream ZeroCreditReady s | Stream QueueReady s |
|---|---:|---:|---:|---:|---:|
| A1r |354|345|345|34.344100|0.017229|
| B1 |487|464|464|46.531476|0.007488|
| C1 |257|183|93|18.578522|11.611351|
| D1 |235|215|215|21.510515|0.005674|
| D2 |241|217|217|21.705266|0.008149|
| C2 |234|110|21|11.540090|16.154164|

These are not fractions obtained by adding waits to receiver request duration.
Per-stream durations span its sender lifetime; sample counts use its active sampled
interval; RS and writer totals below are **whole-session**. At64KiB, ready data is
present while RS is not requesting another slot in almost every selected active
sample. Packing empties RS pressure but cannot bypass the64KiB Mux credit-return
cycle. At128KiB without packing, more data reaches RS and RS/queue blocking becomes
visible. Packing removes that blocking, but often merely moves backpressure back
to Mux credit rather than shortening the application completion path.

For example C1/C2 NL whole-session Family-writer waits22.231/28.989s and RS
ReadyFull23.238/29.631s become D1/D2 writer0.039/0.052s and RS ReadyFull0s. Yet the
reverse pair's single/parallel completion is practically unchanged. These waits
overlap and **must not be added** or treated as independently recovered time.

Linux receiver WINDOW_UPDATE pending→selection medians0.0022–0.0051ms, maxima
0.69–20.65ms. Selection→Family-write-return has rare A/C maxima38.52/731.57/28.73ms,
versus B/D1/D2 maxima1.34/1.28/1.26ms. Those are local acceptance boundaries, not
remote receipt. Control can wait for an already-blocked ordered Family write; no
avoidable bulk-batch-fill wait or shared-lock-held-across-I/O defect is established.
Observed writer-lock maxima across clean peers are≤1.028ms. The old aggregate
SchedulerWaitMaxMS includes stale/control enqueue ages and is not used as lock time.

A partial B2 tail can be necessary to decode the last Mux frame at exhausted
credit. Its independent deadline flushes without another producer Write; real
TLS/Mux tests and slow consumers complete. There is no demonstrated cyclic
credit/tail deadlock. Intentional2ms is not a network deadline: live NL B2 maximum
accepted-byte ages8.23–15.54ms and eligible-dispatch delays1.85–6.23ms include
runtime/worker delay. Small-message cost remains explicit. Fast fixture consumers
do not intentionally stall; the slow local consumer is a separate control.
**No writer patch is justified or implemented.**

### Local interaction: unchanged source/receiver/fault policy

16/16 real TLS/Mux/loopback cases pass under race: one512KiB stream, two256KiB
streams, one256KiB slow consumer, one256KiB fault case, each A/B/C/D. Effective
32/32 and negotiated65536/131072 are asserted on both ends. Exact bytes/SHA256,
FIN/EOF, terminal-free drain, both-end ACK/ciphertext, and protocol counters through
close pass.13 focused race tests additionally cover bounds/overflow, unknown-profile
rejection, immediate/bounded batch scheduling and terminal ordering, packing
deadlines/copy/close, ACK loss and terminal-reset drain rejection. A separate
`TestMuxALPNProfiles` race run passes all11 legacy/mixed-peer/negotiation/security
subcases (`legacy-profiles.log`). Three controller
proof tests reject missing ACK, wrong hash/window, terminal reset and pending tail.

The existing measured-model fixture supplies156345875ns delay per direction and
the same8KiB/2ms serialization in all modes. This is a symmetric transport-delay
proxy, not measured one-way SFU delay. Faults drop first-attempt DATA overlapping
fixed ciphertext byte bands16KiB wide every128KiB, starting at64KiB, and reorder
across32KiB. A DATA sequence number is **not** the fault target. Actual affected
ranges/collateral bytes are retained; different segmentation is not called equal
application-byte or RTP loss. The old retry-density proxy is not proof of loss.
Slow consumer sleeps80ms/16KiB; source, RTO/retries and all other policies stay fixed.

| Local workload | A Mbit/s (s) | B Mbit/s (s) | C Mbit/s (s) | D Mbit/s (s) |
|---|---|---|---|---|
| single512KiB |1.249 (3.358)|1.262 (3.325)|1.842 (2.277)|2.046 (2.050)|
| parallel2×256KiB |2.026 (2.070)|2.048 (2.048)|2.577 (1.627)|2.875 (1.459)|
| slow256KiB |0.867 (2.419)|0.833 (2.519)|0.890 (2.357)|0.925 (2.268)|
| byte-band loss/reorder256KiB |0.517 (4.059)|0.519 (4.044)|0.611 (3.433)|0.719 (2.918)|

The model selected D−C as the live distinguishing contrast, not another Mux128-only
trial. Main contrasts are all kept: B−A/D−C packing, C−A/D−B credit, D−A combined.
Four local idle and four concurrent-start32B controls accompany each case; short
bulk can end before every control, so only actually overlapping starts are called
loaded. No local results are promoted to physical goodput or a latency p99.

### Physical results: all attempts, no best-old-run comparison

Each phase: single4MiB, parallel2×2MiB,64KiB echo/reverse, six32B idle echoes and
six sequential32B echoes from1s into single bulk with100ms gaps. All six loaded
probes in **each** phase fit wholly within its single transfer. Goodput uses full
receiver request completion including open/body/FIN/EOF/stream Close; parallel
duration is the union, not sum. Common predeclared order A/B/C/D/D/C; A1r repeats
only the failed controller attempt, not a selected faster candidate.

| Attempt | Outcome | Single s | Single Mbit/s | Parallel s | Aggregate Mbit/s | Controller s | Charged media MiB |
|---|---|---:|---:|---:|---:|---:|---:|
| A1 | body/drain complete; controller gate failed, EXCLUDED |40.390188|0.830757|24.351851|1.377901|124.754|13.021716|
| A1r | CLEAN |35.997502|0.932132|21.738075|1.543579|117.179|12.768290|
| B1 | CLEAN |49.595127|0.676567|25.379258|1.322120|137.696|11.746649|
| C1 | CLEAN |26.949524|1.245084|13.979968|2.400180|98.822|12.417256|
| D1 | CLEAN |24.195031|1.386832|14.682008|2.285412|97.734|11.831882|
| D2 | CLEAN |24.996235|1.342379|12.857159|2.609786|100.758|11.989206|
| C2 | CLEAN |25.174358|1.332881|12.809124|2.619573|95.810|12.532000|

| Matched contrast | Single goodput change | Aggregate change |
|---|---:|---:|
| B1−A1r: packing at64 |−27.417%|−14.347%|
| D1−C1: packing at128 |+11.385%|−4.782%|
| D2−C2: reverse packing at128 |+0.713%|−0.374%|
| C1−A1r: credit without packing |+33.574%|+55.494%|
| D1−B1: credit with packing |+104.981%|+72.860%|
| D1−A1r: combined |+48.781%|+48.059%|

The combined mode is faster than A here, but **packing is not a necessary component
of that gain**: C already achieves2.400/2.620Mbit/s aggregate. The reverse contrast
reduces the single increment to0.713% and keeps aggregate slightly negative.
Thus no repeatable material additional packing benefit is accepted; this is not
a claim that both single signs are negative. Every fresh phase selected a different
SFU; same-phase publisher/subscriber endpoints agree, but no SFU-fixed causality or
universal credit gain is claimed. The return pair is fresh C2, not the old best C.

### Small responses, resource and wire cost

All entries below are full small-request seconds; n=6 per cell, errors/timeouts0.
They are observations, **not p99 or latency non-regression acceptance**.

| Attempt | Idle median / max s | Loaded median / max s |
|---|---|---|
| A1 excluded |3.093733 /3.669928|2.057489 /3.146059|
| A1r |2.271779 /4.196584|1.894300 /3.106026|
| B1 |3.144655 /3.543560|2.427291 /3.271907|
| C1 |3.168486 /3.542306|2.386688 /3.519482|
| D1 |3.147076 /3.385841|2.170501 /3.099177|
| D2 |3.092718 /3.908624|2.270202 /3.266219|
| C2 |2.994200 /4.199706|2.268163 /3.255707|

B1's slower median at64 and mixed128 controls do not establish a universal
non-regression. Earlier local B2 +4.472ms remains a real separate result.

| Clean phase | Outgoing RTP+RTCP both ends B | NL retry attempts / payload B | Mean retry DATA B | Retry B / unique NL ciphertext B | RSS MiB Linux/NL | CPU seconds Linux/NL |
|---|---:|---:|---:|---:|---|---|
| A1r |11875306|376 /1415794|3765.4|0.165367|62.31 /73.65|7.892 /5.915|
| B1 |11157574|186 /1671954|8989.0|0.196431|65.12 /61.66|8.325 /5.513|
| C1 |11687061|356 /1706217|4792.7|0.199979|65.94 /67.93|6.605 /4.725|
| D1 |11310563|204 /1850377|9070.5|0.217381|63.31 /62.16|6.508 /4.594|
| D2 |11459850|216 /1947839|9017.8|0.228837|64.40 /62.79|6.362 /4.348|
| C2 |11799186|362 /1776431|4907.3|0.208133|65.50 /68.66|6.192 /4.732|

RTP+RTCP includes retransmissions, both peers' outbound bytes, never receiver RX
counted again. Conservative charges additionally reserve64B/packet/write and
64KiB final allowance per peer; STUN/signaling are not media. At128, packing reduces
the conservative media charge about4–5% while increasing NL retry payload bytes
about8–10%, despite **fewer** retry attempts. Larger blocks, not measured increased
packet loss, explain this accounting. The complete local media trace observes
unique retried nonzero sequences376/185/355/203/215/360 respectively; sequence0 is
not identified by the original `omitempty` trace, so these are explicitly partial
unique counts. Aggregate attempt/byte counters are complete. Observed per-sequence
sizes and counter/ring coverage are in the evidence, not asserted to be exhaustive.

NL host busy22.2–28.1%, steal0.217–0.261%; whole-session cgroup throttle totals
7.4–91.4ms for clean phases, not an observed sustained CPU ceiling. Separate SFUs,
local host activity and scheduler noise remain confounders. RS retained high-water
samples roughly128–264kB and Mux retained bound roughly147–295kB increase with
credit; SACKed/unconfirmed/head-stall counters remain separate in the evidence.
B2 adds16KiB owned payload over A, independently of Mux credit. Existing trace
memory and new bounded observations are included in measured RSS, not called free.

### Retry classification and the separate correctness delta

The exact old65936→262144B and361856→1048576B values come from
`tls-rs-packing-20261021/post-local-3.log`,
`TestPackingPreWriteRetryControl`, **local** client→server Family transfers,
64×16384=1048576 application bytes each, byte-exact after release. Every comparison
has the same2.2s first-bulk actual-writer hold, immediate acceptance into the
bounded256-message mock queue, and no injected forward network loss. Numerators
are retry payload **before first actual bulk write**, not whole-transfer media.

| Policy/window | Retry attempts | Unique retried DATA | Attempts incl. first, before write | Retry B | Retry B / final1MiB app body |
|---|---:|---:|---:|---:|---:|
| A/8 |16|8|24|65936|0.062881|
| B2/8 |16|8|24|262144|0.250000|
| A/32 |64|32|96|361856|0.345093|
| B2/32 |64|32|96|1048576|1.000000|

Each retained block is repeated twice. A/8 repeated sizes are1000,1208,2394,3580,
4558,4766,7138,8324B; B2/8 is eight16384B blocks. A/32's complete32-block size
histogram and B2/32's32×16384B are retained in the evidence. There is no RTP media
writer in this mock, so its full outgoing **media** overhead is N/A, not zero or a
fabricated RTP estimate. Bulk ACK cannot arrive before the held write; its later
ACK-processing latency was not recorded.

Unnecessary pre-local-write attempts **are proved**, not merely possible. Reusing
the saved real bound-Pion queue-retry reproducer with lab RTO30ms/hold340ms gives:
Q0 nine attempts/eight retries/zero local writes before release, recovery_exhausted;
Q1 one attempt/zero retries, byte-exact completion. Existing Q1 local-send/attempt
generation, ACK-independent receive, obsolete queued ACK, partial-fragment finish,
finite queue/write deadlines, cancellation and genuine-loss regression tests pass
under race. **This revalidates an existing separate correctness candidate; it does
not change or explain A/B/C/D goodput.** No new patch is required or hidden in D.

The old2.2s hold exceeds Q1's preserved2s local-send deadline: it must fail boundedly,
not be advertised as a successful zero-retry transfer under identical conditions.
Q1 does not remove legitimate retransmission of larger immutable DATA after real
loss, and payload for an assigned sequence is never altered. No retry limit was
lowered and no data discarded to improve counters. The price of retrying denser
blocks remains a trade-off rather than an unreported blocker to all research.

Live bounded RS event rings have gaps (coverage is exported). No retry scheduled
after observed `first_ack` is present in the captured subset, but that does **not**
prove absence of stale queued physical sends, nor measure ingress→ACK-processing
delay. The existing local correctness tests cover that race; a comprehensive
live post-SACK/ACK attribution is **UNDETERMINED**, not NOT_FOUND. No per-host clock
offset is guessed to join RS timestamps to media timestamps or the other host.

### Completion, cleanup and decision

The controller accepts only17 exact application results/SHA256/FIN/EOF/Close,
both ends'17 completed Mux streams with matching8454560B downstream/131541B
upstream counts, empty tails/queues/receive memory, no terminal error, every DATA
ACKed and accepted=submitted=opposite ordered ciphertext SHA256. Both endpoints
publish drain proofs **before** the controller authorizes their final close.
All new phases retain ProtocolErrors0 through final closure. LabDrain's terminal
reset guard remains intact; an empty reset send-depth is never success.

A1 already had exact bodies, both drain proofs and ACK/ciphertext agreement, but
its controller expected17 callback rows that the inherited fixture deliberately
suppresses. This is a **post-delivery measurement gate error**, not a download
failure. The fixed controller validates real Mux/application/ACK ledgers instead;
three negative-proof tests pass. A1 remains charged and excluded, A1r uses the
same binary. An earlier Python filename/stdlib collision was pre-execution/0B;
the sandbox loopback-denied local attempt and pre-live superseded build are also
retained. No protocol-error attempt is silently used for acceptance. Ordinary
abortive/double-close warnings after confirmed completion are preserved separately
from data or recovery failure, not hidden as clean transfer evidence by themselves.

All14 owned peers and seven stages/units/collectors/ephemeral identity sets are
gone. Provider room-metadata deletion is not claimed. Client rules/routes and
addresses/prefixes are identical; raw address JSON differs only in decreasing DHCP
valid/preferred remaining lifetimes5866→4850s, explicitly normalized separately.
Production current epoch/hash/flags remain equal to every phase start/end and final
readback. No rollback is needed: stop/cleanup owned lab resources only; do not
restore an obsolete production profile. APK96, gateway1011 and invitation/public
versions/catalogs are unchanged; no product build/install/publication/push/user migration.

| Requested decision | Result |
|---|---|
| EXTERNAL_STATE_CHANGE_EXPLAINED | PARTIAL: exact service/observation interval/hash scope/isolation known; historical cause/changed fields unresolved. |
| P_WRITER_CRITICAL_PATH |64KiB credit-return cycle with ready source and idle RS established;128 OFF exposes RS/queue pressure. No scheduling/lock/flush defect proved. |
| MUX_CREDIT_PACKING_INTERACTION | Local residual benefit; live D−C +11.385/+0.713% single, −4.782/−0.374% aggregate. No repeatable material added packing benefit. |
| RETRY_ATTEMPTS_VS_BYTES | Larger DATA explains local same-count byte amplification and live fewer-attempt/larger-byte cost. Not a packet-loss measurement. |
| UNNECESSARY_RETRIES_FIXED_OR_NOT_FOUND | FOUND locally; saved Q1 fix revalidated separately, not enabled here. Full live post-ACK classification unresolved. |
| P_ABSOLUTE_GOODPUT | Clean table above; joint gain mainly credit. Do not transfer T gains or compare to production RS8. |
| SMALL_RESPONSE_LATENCY |6 idle+6 loaded per phase, all errors0; medians/maxima mixed, no p99/non-regression acceptance. |
| RESOURCE_AND_WIRE_COST | Lower whole outgoing media with packing; greater retry payload cost per attempt, bounded additional buffers/observations. |
| PRODUCT_ADMISSION | NOT_ACCEPTED: RS32/Mux128/B2/Q1 are separate lab gates; no Android/product admission implied. |

**Close this tested interaction; no endless flush/credit/RTO search.** Return to
the agreed next stage: controlled carrier fragmentation without FEC, then bounded
FEC with equal total sending budget including parity/delay/burst loss; QUIC over
carrier datagrams only if subsequently needed. No new load or prototype is started
automatically in this task. Preserve the code and negative physical result.


## Carrier fragmentation and FEC — 21 October 2026

**Closed isolated lab: S and SF implemented and physically tested; neither is a
product speed fix.** No further size/k/r/window sweep. The next separate stage is
QUIC **instead of the common ReliableStream**, not over it; no QUIC code here.
Prior T packing gains, non-repeatable additional P packing benefit, credit result
and separate dormant Q1 correctness candidate remain unchanged.

### Exact base, implementation and budget

Parent P-interaction binary `c97d4192f3c54396677da09896cd16784c60445ebd9ada633713787eb595148a`;
new lab binary `cdb583b6076016d95d2de0640f13ec25ea5abdf8a35a1c78ebe5a35a43c42cce`.
One binary for all12 physical sessions, no in-series transport patch. Exact source
replay including final gofmt matches the frozen inventory. Source/patch/config,
raw events and receipts: `state-client-build/carrier-fec-20261021/`.
Replay code: [carrier_fec](../../tests/fixtures/carrier_fec/README.md);
kit SHA256 `fa4969e5292494e0cffb189e1c1759e03589a3160f736c4a6898b1d338ce7635`.
[Machine evidence](2026-10-21-carrier-fec.evidence.json) preserves every attempt.

Both peers' emitted configs are SendWindow32/ReceiveWindow32; the pinned OPEN
advertises that receive window and checks peer consistency, so effective window
is min(32,32)=32, not a send-only32 claim. P is Family TLS/Mux128, packing OFF,
Q0, payload16384, RTO1s, retries8, MaxAge20s. Existing negotiated CREDIT128 and
plaintext batching are unchanged. This is **not production RS8/LEGACY64**.
No Q1, timebase fix, rejected FIXED4M, new ALPN or provider is silently activated.

Live source reservations **52715264B / 50.273193MiB**,
outgoing media charge **86721758B / 82.704313MiB**.
Including conservative local reservations64MiB source/128MiB in-memory media gives
114.273193/128MiB source and210.704313/256MiB media. Known newly generated local
test source upper bound57.274865MiB including the extra three-erasure RS fallback;
the local reservation also covers inherited small regressions. Verification copies
are not additional transmitted source.
48MiB P-bulk was reserved before smoke; all six main phases ran without expansion.
Per-transfer180s, request150s, final RS drain10s, worker250s/unit280s limits remain.

### FRAGMENT_WIRE_AND_PACKETIZATION

L retains original24B carrier header and8192B parts. S/SF use explicit incompatible
FCF2 v1:64B header,1024B source symbols. Header contains16B per-phase epoch,
direction, sender/message IDs, original length/CRC, group/symbol position, actual
source count, fixed symbol size and symbol/header CRC. Every part is independently
locatable without part0 or RTP SSRC/sequence stability. No new RS DATA sequence;
only a fully assembled, whole-CRC-checked original message reaches RS/TLS.

Pinned Pion outbound clear-RTP MTU1200; fixed RTP header12, VP8 descriptor1/3/4B,
fake VP8 interframe17B. Payload capacity is1188 before descriptor,1184 at the
largest descriptor. Live observed RTP header12 (no extensions), S/SF full packet
1121B including descriptor4; L max1200B. A16448B RS carrier message produces:

| Variant | Source/repair parts | RTP count | Carrier bytes before VP8 | Mandatory frame pauses |
|---|---:|---:|---:|---:|
| L |3/0|15 =7+7+1|16520|6ms|
| S |17/0|17|17536|34ms|
| SF |17/6|23|24064|46ms|

The exact negotiated SRTP cipher is **not exposed/populated** by pinned Pion
transport stats. Supported profiles use10B SHA1-80 or16B AEAD tags; no cipher is
invented. Size/budget safety uses16B. With observed no RTP extensions, IPv4/UDP
sizes are at most1165B S/SF and1244B L; IPv6 bounds1185/1264B. SRTCP adds its4B
explicit index. Post-series route/link readback for every selected IPv4 SFU shows
MTU1500 at both ends. This establishes packet-size margin, not a claim of measured
path-MTU discovery or a kernel IP-fragmentation trace. RTP MTU was not raised.

### FRAME_RATE_AND_ARTIFICIAL_LIMITS

Original2ms sleep after **every** frame and33ms nominal RTP duration (2970 ticks)
remain in all modes. No S-only pause removal. Thus500 frames/s is an ideal ceiling,
before scheduler/write/queue overhead: full1024B S symbols imply at most4.096Mbit/s
source; full8+2 groups at most3.277Mbit/s, worse for short final groups. S/SF also
advance the nominal timestamp more times per original message. These are explicit
construction limitations, not proof of an optimized fragmentation/FEC transport.

All main L/S/SF additionally share a conservative outgoing byte-service ceiling
1,048,576B/s, including repair, RTP retries and RTCP. This is not FIXED4M. Existing
2ms frame pacing remains the tighter S/SF limiter. R0 disables only this new
ceiling to retain a short original-L bridge.128KiB R0/RL complete8/8, receiver
last-byte times1.214118/1.239959s; sender-confirmed intervals1.640424/2.869691s on
their own clocks. Different SFUs and one pair preclude attributing all difference
to this ceiling. Do not subtract inter-host timestamps or compare to an old best P.

### S_CORRECTNESS and FEC_PROFILE_AND_RECOVERY_BOUNDS

Local real Pion packetization proves one RTP/part for S/SF. Tests cover byte-exact
0..65536B boundary/sample sizes, with allocation-free geometry checked for **every
one of65537 lengths**; no unsupported giant payload. First/middle/last loss,
reorder, identical/conflicting duplicates, invalid length/index/profile, corrupt
symbol/whole CRC, wrong epoch/direction, silence/expiry, cancel/close and race pass.
The legacy duplicate-poisons-build behavior is unchanged in L. S's separate
duplicate-idempotence rule is explicit, tested, and not credited as a size-only
speed improvement; live duplicate-conflict counters are zero.

Bounds:16 pending messages,80 symbols/message,1,310,720 held symbol bytes,4096
recent/pending IDs,10s lifetime; no legacy bitmap used for S completion. Max-size
pressure test holds16 incomplete messages at1,032,192B S /917,504B SF, refuses the
17th, and releases all on expiry/close. Header validation/CRC are bounded before
large allocations/decode. No memory credit or flow control is disabled.

SF uses verified MIT `klauspost/reedsolomon v1.12.4` plus cpuid/v2 v2.2.8, not custom
cryptography. [License/sums](../legal/DEPENDENCY_LICENSE_AUDIT.md#isolated-carrier-fec-laboratory--2026-10-21).
One shortened systematic up-to8+2 profile, one codec worker. Groups never cross
messages/epochs/directions or wait for future input. Last group uses its actual
1..8 source count plus2 repairs, with zero-padding only for coding. Messages of
0..1024B bypass repair, so small ACK/control never waits for group fill. Source
delivery does not wait for repair once complete. All one/two erasure combinations
of10-symbol groups,0..2 erasures at multiple message sizes,3+ erasures, repair
loss, whole absent groups, short tails and corrupt reconstruction are tested.
Insufficient FEC leaves normal RS recovery; CRC does not replace Family TLS.

Nine bound-Pion RS32 tests (L/S/SF × fast/one-RTP-loss/slow consumer) pass under
race with196608B each. One-loss retries are12/1/0 for L/S/SF in that fixture,
not claimed comparable live loss probabilities. A separate frozen-copy SF test
drops three consecutive source RTP packets (beyond r=2), then verifies ordinary
RS recovery,196608B byte-exact and terminal-free drain (`fec-rs-fallback.log`;
`fallback-test.patch`). It changes no runtime binary or live matrix. Independent seeded model uses
seeds11/29/47,1.5% packet Bernoulli loss and a separately named packet-triggered
6ms burst model, common1MiB/s serialization plus2ms/frame.24 messages/mode/seed:
iid L19/18/22, S18/16/21, SF24/24/24 completed; burst L16/14/16, S16/14/16,
SF22/22/23. SF consumes more modeled time/media. These are recovery-model results,
not an SFU replay or P speedup. Raw loss and residual missing messages are retained.

### Physical attempts: smoke, R32 and P

Pre-execution CL argument error created no room/process and sent0B; retained as
`CL-operator.log.preexec`. Actual C smoke L18/20, S19/20 complete bodies, corrupt0;
missing IDs L[10,11], S[7]. Observation deadline expires normally, but these are
**partial raw delivery**, not clean full-message acceptance. S showed141/141
identified outgoing parts in one RTP each. R0/RL/RS/RSF all deliver8/8 exact128KiB;
S/SF receiver last-byte times2.217346/2.677176s, sender confirmed2.975111/2.254888s.
Repair transport via ordinary VP8 is observed, not assumed from local tests.

Main order L→S→SF→SF→S→L, one4MiB stream and two2MiB streams per phase:

| Phase | Mode | Single s | Single Mbit/s | Parallel s | Aggregate Mbit/s | Whole phase s |
|---|---|---:|---:|---:|---:|---:|
| PL1 | L | 25.296009 | 1.326471 | 12.585233 | 2.666175 | 95.687 |
| PS1 | S | 26.748180 | 1.254457 | 17.656337 | 1.900419 | 113.528 |
| PSF1 | SF | 27.496655 | 1.220310 | 16.515125 | 2.031740 | 110.786 |
| PSF2 | SF | 27.591373 | 1.216120 | 16.784747 | 1.999103 | 109.718 |
| PS2 | S | 26.546690 | 1.263978 | 15.679603 | 2.140005 | 106.764 |
| PL2 | L | 23.117348 | 1.451483 | 14.781790 | 2.269984 | 97.931 |

| Paired contrast | Single | Aggregate |
|---|---:|---:|
| PS1-vs-PL1 | -5.429% | -28.721% |
| PS2-vs-PL2 | -12.918% | -5.726% |
| PSF1-vs-PS1 | -2.722% | +6.910% |
| PSF2-vs-PS2 | -3.786% | -6.584% |
| PSF1-vs-PL1 | -8.003% | -23.796% |
| PSF2-vs-PL2 | -16.215% | -11.933% |

**S loses to L in both orders. SF single is lower than S in both orders; its
aggregate sign reverses. No repeatable useful P benefit is established.**

### P_SINGLE_AGGREGATE_AND_LATENCY

Identical six32B idle and six32B loaded sequential echoes,100ms gaps, loaded start
1s into single bulk. All six loaded probes are wholly inside bulk in every phase.
All72 small responses succeed. Median / observed maximum, seconds; **not p99**:

| Phase | Idle median/max | Loaded median/max | Errors idle/loaded |
|---|---:|---:|---:|
| PL1 | 3.120987 / 3.560290 | 2.370877 / 3.312849 | 0 / 0 |
| PS1 | 3.770649 / 5.494429 | 2.063614 / 3.605103 | 0 / 0 |
| PSF1 | 3.225412 / 3.458328 | 2.527211 / 3.654545 | 0 / 0 |
| PSF2 | 3.193793 / 3.455001 | 2.571310 / 3.350046 | 0 / 0 |
| PS2 | 3.242527 / 4.296799 | 2.574301 / 3.510538 | 0 / 0 |
| PL2 | 2.739717 / 3.195869 | 1.997756 / 3.163152 | 0 / 0 |

Latency is mixed; non-regression is not accepted. All17 application operations
per P phase have exact sizes/SHA256 and corresponding both-end stream byte counts.
Both RS drains have empty terminal state, all DATA acknowledged, matching ordered
ciphertext, Mux128 on both ends, no protocol errors through final closure.

### MEDIA_COST_AND_RAW_LOSS; resources

Whole-phase outgoing charge includes both directions, controls, repair and all
retries, not equal source-rate plus unbudgeted parity. Complete rings permit
independent full clear RTP/RTCP sums and IPv6+SRTP16/SRTCP20 upper bounds; each is
below the charged value. The inherited64B allowance slightly undercounts individual
AEAD SRTCP by4B, but explicit recomputation fits the reserved closing margin by
over60kB/endpoint in P; no budget overrun or hidden zero overhead. Logical coding
padding is reported separately, not added again to repair-inclusive wire bytes.

| Phase | Charged media B | NL RS retries / bytes | NL repair / coding padding B | Peak queue frames / max age ms | RSS Linux/NL MiB |
|---|---:|---:|---:|---:|---:|
| PL1 | 12249547 | 215 / 970591 | 0 / 0 | 80 / not instrumented | 66.93 / 70.21 |
| PS1 | 13310969 | 199 / 911242 | 0 / 0 | 226 / 613.528 | 67.43 / 66.09 |
| PSF1 | 17079789 | 116 / 439865 | 3688448 / 756866 | 256 / 659.998 | 70.68 / 69.09 |
| PSF2 | 16762053 | 108 / 430790 | 3506176 / 505168 | 256 / 664.345 | 69.93 / 71.46 |
| PS2 | 12851743 | 151 / 552737 | 0 / 0 | 251 / 656.976 | 67.55 / 68.02 |
| PL2 | 12259402 | 197 / 995817 | 0 / 0 | 67 / not instrumented | 68.18 / 68.09 |

SF sends3,688,448/3,506,176B repair from NL, plus reverse-direction repair, while
recovering only2 missing source symbols in each P phase (1/2 groups). Shortened
tails make real parity overhead materially greater than a blanket25% assumption.
For example16448B needs6144 repair bytes (37.35%) plus headers and960 coding-pad
bytes. No changing source rate is disguised as equal bandwidth.

| Phase | NL source/repair parts not assembled at Linux | Recovered source symbols/groups | Linux expired partial messages |
|---|---:|---:|---:|
| PL1 | 525 / 0 | 0 / 0 | 5 |
| PS1 | 1099 / 0 | 0 / 0 | 28 |
| PSF1 | 614 / 177 | 2 / 1 | 6 |
| PSF2 | 606 / 179 | 2 / 2 | 6 |
| PS2 | 761 / 0 | 0 / 0 | 13 |
| PL2 | 502 / 0 | 0 / 0 | 3 |

These are whole-session endpoint-ID matches, including shutdown tails, not a
claim that a physical network dropped that many packets. For S/SF one part maps
to one RTP. L part loss may follow any one of several RTP losses. All media trace
overflows are0; no clock subtraction used. In each SF phase **90 fully transmitted
protected groups with missing source exceeded two absent symbols**; only1/2
source-missing groups fit the two-erasure budget. Complete group histograms are
retained. This explains why local erasure repair is real but has little useful
opportunity under these observed clustered erasures. No reordering/interleaving,
larger r, or alternate size is silently tried.

Instrumented NL encode elapsed time is50.7–58.0ms per S/SF whole phase; recovered
decode elapsed time is21.9/26.3 microseconds at Linux. These are timed code regions,
not thread-CPU measurements. Whole-process CPU Linux/NL: PL1 5.299/5.649s,
PS1 5.792/6.275s, PSF1 6.748/6.912s, PSF2 6.031/6.693s, PS2 6.021/6.280s,
PL2 4.921/5.953s. NL queue peaks hit256 frames in SF, age660/664ms; finite and
drained, not a reason to increase offered load. Ready-window waits and head stalls
remain in evidence and overlap other waits; they are not summed as elapsed time.
NL background busy28.18–34.63%, steal0.219–0.312%, throttling0–57.4ms. Each phase
uses another SFU; selected UDP/host paths and resource samples are retained.

### RETRY_ACCOUNTING and closure

Q0 stays common throughout. No Q1 correctness transition was needed/activated.
Repair overhead is explicit, and NL RS attempts/bytes decrease in SF, but **lower
retries with lower goodput is not a speed fix**. Only2 repaired symbols/phase do
not causally explain the entire retry-count difference across independent SFUs.
Maximum observed S/SF frame queue age remains below1s RTO; this alone is not proof
of no premature retries. Incomplete RS rings and missing FCF2 physical-to-RS
sequence export prevent exhaustive pre-first-write/post-ACK attribution. Retained
subsets show no retry scheduled after first ACK; early-local/late-ACK causes remain
unknown where unobserved. No retry limit or payload of assigned RS sequences changed.
Actual repeated RTP identities are1 per endpoint in P except PL1 NL3, separate
from RS re-encodings and FEC repair. Their timestamps/body hashes match.

At the two-end completion barrier PS1 Linux still held2 obsolete partial carrier
attempts/7168B and PSF1 NL1/13312B; all application/RS contracts were already
confirmed. They are reported, not silently called zero, and normal final close
purges them; final S/SF Held/Pending0 and Closed=true. All carrier send queues0.
All P `packing_closed: use of closed network connection` warnings occur **after**
the valid two-end barrier; no terminal reset is turned into LabDrain success.
No protocol-error attempt is used for acceptance, and raw partial smokes remain
partial in the common table/evidence rather than disappearing from statistics.

Final readback `2026-10-21T08:17:22.744678+00:00`:24 owned peers,12 isolated units/stages/
collectors and ephemeral identity sets removed. Normal peer/WebSocket closure;
provider room-metadata deletion is not supported/claimed. Addresses/rules/routes
match after removing only DHCP lifetime countdowns. Production PID429617,
invocation9922c6ee79f64e94aa87e8ec47313f5c, binary734b6ca6…/profile66096048… and
OFF/LEGACY64 flags match every before/after readback. No renewal/timer action,
reset, rollback, production keys/floors/routing edit, APK, publication or push.
Bootstrap96/gateway1011/A0 and public/invitation/catalog versions remain unchanged.

| Requested decision | Result |
|---|---|
| FRAGMENT_WIRE_AND_PACKETIZATION | Explicit FCF2,1024B S, one RTP/part locally and live; exact clear sizes, bounded encrypted/IP sizes; negotiated cipher unknown. |
| FRAME_RATE_AND_ARTIFICIAL_LIMITS | Same2ms/frame,33ms nominal clock and common1MiB/s ceiling; original-L bridge separate. |
| S_CORRECTNESS | Local bounds/race/byte-exact PASS; physical R/P complete; raw C partial preserved. |
| FEC_PROFILE_AND_RECOVERY_BOUNDS | Shortened up-to8+2 RS verified; all two-erasure combinations; beyond-r falls back to RS. |
| S_VS_L_EFFECT | P single and aggregate lower in both orders. |
| SF_VS_S_EFFECT | Tiny real live recovery; single lower, aggregate sign mixed; higher wire cost. |
| P_SINGLE_AGGREGATE_AND_LATENCY | Six complete P phases;72 small responses; no P speed or latency non-regression admission. |
| MEDIA_COST_AND_RAW_LOSS | Repair/padding/headers/retries separate; erasures preserved; clustered groups mostly exceed r. |
| RETRY_ACCOUNTING | Q0 unchanged; full attempts/bytes known, complete causal timing unavailable; no hidden Q1. |
| PRODUCTION_UNCHANGED | Verified read-only snapshots and cleanup; no product admission. |

**Close this size/profile, preserve the negative result.** Next separate stage:
QUIC replacing the common ReliableStream, not layered on it. Do not implement it,
expand hosting, change Android/users or tune RS/Mux windows in this task.

## QUIC over existing media — 21 October 2026

This is the subsequent authorized isolated architecture experiment, not a product
migration. The earlier S/FCF2 and SF/8+2 result remains closed. Implementation,
local admission, and actual NL→Linux Telemost measurements are retained in
`state-client-build/quic-carrier-20261021/`; reproducible source transforms and
tests are in `tests/fixtures/quic_carrier/`. See the
[lab ADR](../adr/2026-10-21-quic-media-lab.md). No production module is modified.

### Exact architecture and laboratory admission

- A: **L, effective RS32/32, Family TLS, Mux128, packing OFF, Q0**. This is the
  improved laboratory baseline, not production RS8/LEGACY64. Both endpoint
  configurations are recorded; no smaller peer receive window is called32.
- QN: one QUIC connection, one reliable bidirectional stream per application
  connection. No Mux credit, Family TLS record stream, RS/FRS1, TCP, new ordered
  adapter, fragment ARQ or direct UDP path below QUIC. Existing WebRTC/NACK and
  VP8/RTP whole-message assembly remain. Inherited RS/Mux config fields in QN's
  harness are inactive; emitted reliability configuration is null.
- QS: diagnostic existing Mux128 over one bounded length-framed QUIC stream.
  No second Family TLS. A→QS changes TLS integration as well as transport;
  QS→QN also removes Mux credit/common-stream ordering. QS is a short diagnostic,
  not a full-size product-speed control or a new production Session API.
- quic-go **v0.54.1, MIT**, minimum Go1.23; inherited isolated module directive
  Go1.24, actual toolchain **Go1.26.1**. go.mod/go.sum and license notices are
  pinned; `go mod verify` passes. Existing production dependency pins are intact.
  Default **Reno** congestion controller and pacer are retained, no library patch.
- Fixed QUIC receive limits: stream128KiB, connection512KiB,24 incoming
  bidirectional streams, no incoming unidirectional streams. This is bounded,
  not an assertion that its total allocation layout equals RS/Mux/TLS. No larger
  BDP profile or congestion/window sweep was introduced. Test source/sink body
  buffers are included in process RSS, not attributed to transport alone.

Adapter WriteTo/ReadFrom preserve one complete1…1200B datagram. Oversize and short
read buffers cannot report partial success. Synthetic198.18.0.1/2:4443 addresses
are phase-local labels, not authentication or a UDP socket. One serialized adapter
write waits for actual carrier localwrite completion; no extra receive queue,
retry or ordering mechanism. Writes have finite5s limits plus dynamic deadlines;
close cancels waiting reads/writes. quic-go's own eight-entry send queue remains
bounded. No fabricated ECN/GSO/offload or UDP buffer semantics.

Local race admission covers ownership/boundaries, changing deadlines, concurrent
close, finite queues, partial application reads, byte-exact bodies, lost Initial
and Handshake, duplicates/reorder, a six-consecutive-datagram burst, ten reverse
path drops, slow reader and stream-count limits. These are explicit faults at the
whole-datagram boundary, not a claim to replay identical RTP losses from another
segmentation. A targeted missing-prefix test delivers independent stream4 before
stream0 recovery; the same-stream control blocks later bytes until recovery.
Reset of a slow stream does not abort another. Congestion control and lower media
assembly are still shared. Bound real-Pion packetization/QUIC delivery and existing
legacy/Mux128/strict terminal LabDrain checks pass under race.

Fresh ephemeral Ed25519 CA and one-hour certificates are verified mutually by
root and expected DNS role, TLS1.3 and `family-connect-quic-lab-v1`. No
InsecureSkipVerify, production identity, TLS key log, anonymous relay or0-RTT.
Ordinary Dial/Accept start workload only after handshake. An initial local
SessionTicketsDisabled configuration triggered a quic-go ticket-event assertion;
ordinary unused tickets with nil client session cache and Allow0RTT=false fix
that compatibility issue without library changes. Failed local logs are retained.
This mTLS is not Family identity/admission, floors, leases or revocation support.

QN success additionally requires a40B receiver receipt (length/SHA256) checked by
the sender, matching17 client operations and17 server receipts by stream ID before
the controller permits connection close. QS requires conserved both-end Mux bytes
and closed streams; A retains strict terminal-error LabDrain. Write/FIN/connection
close is never remote-delivery proof. Final sampled QUIC counters precede local
deferred transport close; process exits and cleanup are separate evidence, not an
invented post-close zero-error snapshot.

### Packetization and the cadence control

One1200B QUIC datagram becomes one legacy carrier message/part, with24B carrier
header and17B VP8 interframe prefix, not a1024B FCF2 part. RTP MTU remains1200;
with observed12B RTP header, no RTP extensions, and1/3/4B VP8 descriptor
(Pion enables PictureID), each packet carries1187/1185/1184B of the1241B frame.
Thus it takes **two RTP
packets**, not one; smaller datagrams can fit one. Clear RTP sizes are verified
locally and live. SRTP authentication tag is bounded by16B, not asserted negotiated:
maximum IP size1244B IPv4 /1264B IPv6 including UDP, under ordinary1500B MTU.
The virtual QUIC maximum and Initial size are1200; PMTU discovery is disabled,
not patched below QUIC's required minimum. Whole-message loss remains datagram
loss, and incomplete carrier data is never handed to QUIC.

Original controls retain2ms per frame, imposing an ideal≤500 datagrams/s for
1200B datagrams before all other costs:≤4.8Mbit/s QUIC bytes, not application
goodput. Actual local bound-Pion adapter:300 datagrams/360000B,600 RTP,0.731018s,
410.39 datagrams/s,3.940Mbit/s datagram bytes. The single common normalized
policy removes fixed frame sleep and caps conservative RTP/RTCP service at
1,048,576B/s with at most2ms earned burst credit. Both A and QUIC use it. Local
result0.399566s,750.81 datagrams/s,7.208Mbit/s datagram bytes, still600 RTP.
An initial per-packet timer-rounding implementation was corrected before live;
its failed ceiling observation remains. This is not the rejected FIXED4M policy.

L framing, keepalive and nominal33ms timestamp progression are unchanged in all
contrasts. Therefore more small frames still advance nominal RTP time faster;
this experiment does not admit that inherited timebase for arbitrary sustained
frame rates. No candidate-only timebase fix or packing/Q1/FEC is hidden here.
The local adapter gain removes a known artificial limit; different live sessions
and SFUs prevent attributing a live rate change to normalization alone.

### Preserved failures and common start gate

The first AO guard detected a production epoch change before creating a room,
identity or process:0B. Read-only service metadata shows a new process start at
09:10:19UTC, same binary/flags but changed whole-profile hash. Journal reads timed
out; cause and changed fields remain unknown, not “renewal”. The actual live
series binds a fresh explicit stable epoch, without reset/restart or rollback.

Two early full-size baseline attempts are excluded from clean speed acceptance:
A1 parsed an unfinished JSONL line during parallel; it had delivered single4MiB
but lacks full completion. The operator now defers incomplete LF/UTF8 tails and
still rejects corrupt complete records. A1R sent no application data: the server's
20s RS startup expired during21.153s client media setup. Neither is discarded.

Common v2 adds a≤45s both-media-ready gate **before** transport startup and the
180s phase timer. Transport timers/configuration are unchanged; v1 source/binary,
gate-only delta, local gate/race tests and both inventories are retained. All
primary A1G/QN1/QN2/A2 phases use v2. A1G then had a genuine data-path failure:
server RS `recovery_exhausted`, client reset, both processes exiting1 themselves
before cleanup. Single4MiB SHA passed, parallel opens failed; not a clean phase.
A concurrent35s readback timeout is the controller error, not a replacement for
that transport cause. Final readback succeeds unchanged. Average host busy was
8.77% Linux/18.72% NL, with only one15.82ms NL cgroup throttle and no demonstrated
production influence. No RS retry/window correction or A1G rerun is used to hide
the negative result; only the three remaining preplanned contrasts continue.

### All physical attempts and completion outcomes

All eleven sessions use isolated rooms/processes/credentials, NL source and Linux
receiver. v1 binary `fb685dde1d1ba11ed91ca0c7bbf9f8f14b7c3ec98d1d26dc73c069549ee73003`
covers short controls/A1/A1R. Common gated v2
`d2e7fe2dafca8d28f141e7f4eea9d86b711b0d66baf05d2f9ffd8cf44d5de012`
covers A1G/QN1/QN2/A2; source replay is exact. Gate-only delta has three files,
68 added lines; no data-path change. Operator amendments have separate hashes.

Short =256KiB single +2×128KiB parallel; main =4MiB single +2×2MiB parallel.
Aggregate duration is the union of the two parallel intervals, not their sum.
Values below are application Mbit/s and seconds, not IP/QUIC throughput. Dashes
mean not completed, not zero performance. A partial failed transfer's instantaneous
rate is not promoted into completed aggregate goodput.

| Phase / mode | Cadence / load | Single Mbit/s / s | Aggregate Mbit/s / s | Outcome | Charged media MiB |
|---|---|---:|---:|---|---:|
| AO / A | original / short |0.730 /2.873|0.843 /2.488|clean17/17|1.185544|
| QO / QN | original / short |0.432 /4.856|0.544 /3.857|clean17/17|1.238784|
| AN / A | normalized / short |0.437 /4.798|0.719 /2.915|clean17/17|1.290944|
| QNsmoke / QN | normalized / short |0.323 /6.485|0.482 /4.350|clean17/17|1.203132|
| QS / QS | normalized / short |0.262 /8.002|0.194 /10.824|clean17/17|1.539603|
| A1 / A | normalized / main |1.223 /27.447|—|14/16; partial-line controller abort during parallel|7.741982|
| A1R / A | normalized / main |—|—|0 requests; startup race|0.162732|
| A1G / A | normalized / main |0.549 /61.166|—|14/16; RS recovery exhausted before completion|9.824717|
| QN1 / QN | normalized / main |0.469 /71.552|0.524 /64.052|17/17 + remote receipts; post-delivery finish timeout, **not clean**|11.707965|
| QN2 / QN | normalized / main |—|—|2/3; publisher disconnected before bulk|0.444094|
| A2 / A | normalized / main |1.080 /31.058|1.813 /18.506|clean17/17|12.949406|

The initial AO production-epoch preflight is additional,0B, no session created.
All eleven actual sessions and five failed phases remain in statistics:6 clean,
7 with full17-operation two-end delivery proof (QN1 is the seventh),149 passed
of154 attempted application operations;33 planned operations were not started.
These are observed laboratory counts, not a product reliability probability.

QN1 delivered and verified every body/receiver receipt before the late failure.
Client workload complete09:58:36.799UTC; both proofs exist by09:58:41.904UTC.
The controller then transferred the whole14MiB remote log; local finish marker
was not written until09:59:11.459UTC, after QUIC idle timeout/server phase deadline.
Both processes exited1. This is **post-delivery completion failure**, not download
failure and not clean acceptance. `proof_snapshot.py` fixes the measurement path:
select one complete proof remotely, bounded32MiB input/4MiB selected line/12s
command, tested against saved A/QS/QN proofs. Fetch full logs after closure.
No QUIC timeout increase, keepalive insertion, binary change or QN1 rerun.

QN2 subsequently fails on `quic: transport closed: telemost: publisher disconnected`
before bulk; the generic request `transfer_or_integrity` label is not evidence of
corrupted bytes. Server reports carrier closed. This candidate is stopped, not
retried until a better room appears. Only the already planned A2 remains and
finishes cleanly with the optimized common proof path. No extra live phase.

All sessions have different observed SFUs (AO37.9.73.146; QO77.88.43.11;
AN37.9.69.109; QNsmoke5.255.227.23; QS37.9.73.125; A1 37.9.100.83;
A1G5.255.254.139; QN1 5.255.254.131; QN2 77.88.42.234; A2 37.9.73.25).
A1R has no final selected-path sample; do not fill it from another phase.
Observed paths use UDP to provider SFU host candidates, not direct peer QUIC UDP.
Per-phase manifests preserve media and QUIC setup separately from request time;
no one-way latency is computed by subtracting host clocks.

### Small responses, recovery and resource cost

Each scheduled probe body is32B echo. Six idle requests run sequentially without
extra gaps; six loaded requests begin1s into single with100ms inter-request gaps.
Results are median/observed maximum seconds, **not p99**. Counts are successful
probes; errors/missing attempts are recorded separately.

| Phase | Idle n, median / max | Loaded n, median / max | Loaded fully inside single |
|---|---|---|---:|
| AO |6,3.099 /3.502|6,3.098 /4.086|0/6|
| QO |6,1.522 /1.591|6,0.548 /1.040|5/6|
| AN |6,3.194 /3.801|6,3.095 /3.320|1/6|
| QNsmoke |6,1.702 /2.036|6,0.537 /0.780|6/6|
| QS |6,5.947 /5.998|6,4.807 /6.759|2/6|
| A1 |6,3.063 /3.879|6,2.701 /3.342|6/6|
| A1R |0, not started|0, not started|—|
| A1G |6,3.199 /5.843|6,4.426 /7.308|6/6|
| QN1 |6,1.428 /1.946|6,0.522 /0.974|6/6|
| QN2 |1,6.411 /6.411; one error|0, not started|—|
| A2 |6,3.104 /3.379|6,2.642 /3.461|6/6|

Total109 successful small probes, one failed,22 not started. The short-control
“loaded” label alone is insufficient: some probes outlasted the short bulk.
QN's lower observed response times are promising separately from bulk speed, but
failure/session variation and sparse samples prevent latency or stability admission.

For QN1's NL sender:7900 QUIC packets declared sent,403 declared lost,509917
repeated STREAM bytes /8454560 unique stream-response bytes (6.03%); these are
not RS retries or physical packet loss. Peak cwnd/inflight74400B; sampled median
cwnd22748B/inflight18000B, sampled median smoothed RTT322.580ms; final smoothed
RTT855.482ms and variation835.285ms. PTO max3,48 update callbacks (including
resets, **not48 PTO firings**). No emitted STREAM_DATA_BLOCKED/DATA_BLOCKED frames.
Per-stream repeated-byte accounting remained complete. Reverse direction had
19 loss declarations/24613 repeated STREAM bytes. Lower retransmission/probe
necessity and exact ACK delay are not inferred solely from those counters.

For clean A2, RS counters are separate: NL379 retry attempts/2212077B, relative
to8527669 unique ciphertext bytes; Linux50/102382B relative to203293B. Q0 is
unchanged. Bounded RS event history is incomplete; observed zero post-first-ACK
retry events is not proof of no stale queued writes or timely ACK handling.
NL sampled retained/SACKed/unconfirmed peaks263538/202114/263538B; head age peak
1.911s, ready-full wait22.992s and head-unconfirmed/later-SACKed wait11.969s.
These intervals overlap and are not added into a synthetic total. Mux/queue
counters and no-protocol-error closure are preserved in the endpoint evidence.

| Whole-session cost | QN1 Linux / NL | A2 Linux / NL |
|---|---:|---:|
| User+system CPU seconds |7.553 /10.532|4.528 /5.470|
| Sampled peak RSS KiB |69572 /62948|69956 /68708|
| Mean host busy % |10.29 /25.89|10.97 /26.38|
| Max carrier queue age ms |1.076 /0.757|66.772 /330.837|
| Serialized adapter I/O maximum ms (after gate) |3.190 /14.930|not this adapter|
| Outgoing RTP count |4001 /15681|4106 /12399|
| Identified repeated RTP |16 /1|18 /1|
| Identified transmitted parts not assembled remotely |32/3752 /432/7899|31/3873 /858/4546|

The final row uses complete bounded media traces and endpoint carrier IDs over
the whole session including shutdown tails; it is not a raw IP-loss rate. Local
RTP continuation grouping uses the sender's own SSRC/timestamp only, never an
assumption SFU preserves them across hosts. QN1 NL has7688 two-RTP and211 one-RTP
identified complete parts, maximum clear RTP1200B. Packet/part/message distinctions
are retained. Full media charge includes RTP/RTCP, bounded SRTP/IP overhead,
retransmissions and shutdown allowance; no FEC/repair bytes. Resource totals
include control/proof/idle time and fixture bodies, so unequal duration is not
called equal CPU efficiency. NL CPU throttling is0 for QN1,30.116ms once for A2;
no sustained CPU saturation or accumulating QN media queue was observed.

Adapter WriteNS starts after acquiring its serialized slot and ends at actual
local media completion. It therefore excludes contention before that slot and
quic-go's earlier eight-entry send queue residence. These are finite bounds, not
an exact measured end-to-end QUIC scheduling delay. Do not use the I/O maximum
as a bound on all local waiting or classify every QUIC loss declaration as a
necessary physical retransmission. More precise pre-send/ACK causal attribution
remains unavailable in this trace; no unobserved interval is silently set to zero.

The QN1 send cwnd is well below the128KiB stream window, and its sampled
RTT/loss response is compatible with limited delivery rate. There is no evidence
to justify a larger flow-control profile. Nor is the known2ms frame ceiling the
explanation for normalized QN1's0.469Mbit/s: local normalized capacity is far above
that and measured enqueue-to-write residence stays small. The evidence instead
implicates carrier delay/loss/disconnection plus the shared Reno recovery response;
it does **not** isolate their causal shares or clear the inherited RTP timebase.
Insufficient clean repeated full-size comparison is an additional measurement
limit, not proof that QUIC in general is ineffective.

### Final decision and production readback

| Requested decision | Result |
|---|---|
| DATAGRAM_ADAPTER_CORRECTNESS |Implemented; local/race/bound-Pion and live body/receipt gates pass; no lower reliable adapter or UDP fallback.|
| MINIMUM_DATAGRAM_AND_PACKETIZATION |1200B cap/Initial, actual one/two RTP per datagram; L/MTU unchanged, bounded SRTP/IP accounting.|
| CARRIER_CADENCE_LIMIT |Original artificial ceiling demonstrated locally; common bounded normalization improves local capacity, not established live speed.|
| LAB_AUTHENTICATION |Mutual ephemeral CA/role/TLS1.3/ALPN verified; no0-RTT; not Family admission.|
| A_VS_QS_VS_QN |Short QN better than QS but below A; full A/QN/QN/A not clean/repeatable. No transport-only causal gain claim.|
| ABSOLUTE_SPEED_AND_LATENCY |Clean A2 single1.080/aggregate1.813Mbit/s; fully delivered but late-failed QN1 0.469/0.524. Lower observed QN small latency separate; no2× gain.|
| LOSS_RECOVERY_AND_FLOW_CONTROL |Local independent-stream gap/reset behavior confirmed; shared loss/congestion/carrier remain. No demonstrated flow-window bottleneck, no sweep.|
| MEMORY_CPU_WIRE_COST |Finite windows/queues, measured cost above; no measured CPU saturation. Lower retries/wire alone are not speed acceptance.|
| PRODUCTION_UNCHANGED |All live pre/post snapshots and final new epoch agree; no production mutation or product admission.|

Source reservation upper bound **55169280B =52.613525MiB/64MiB**, including full
reservations for failed/never-started workload portions; it is not a claim all
those bytes were delivered. Conservative outgoing media charge both ends
**51683159B =49.288901MiB/128MiB**, including64KiB/end/session tail allowance.
Local tests are separate, not invented Telemost traffic. No budget expansion.

Final10:16:52UTC readback: PID555883, invocation31ee59ae99c84bafa3be5402d784efce,
binary `734b6ca6eb42be0367b703b657be87c624f3500ae408bbd771309ffaeb86128e`, profile
`55b508c213ab279e95b4f30c9d165eed4c9281adc6c3ff9f2cbaee111eb7d2c6`, flags
OFF/LEGACY64/mux-countersOFF. Bootstrap96/gateway1011/A0 remain as accepted;
no authority/credentials/floors/routes or timers were changed. The earlier epoch
change is explicitly not overwritten with the old profile hash. All22 lab peers,
11 units/stages, collectors and temporary identities are gone; no owned leftover
journal collector. Client network is unchanged after excluding DHCP lifetimes.
Normal peer/WebSocket closure is confirmed, not deletion of provider room metadata.
Post-live local deadline-extension/stale-callback/lifetime test passes under race:
five complete lifetimes, goroutines2→2. Source reconstruction exact.

**Close this bounded experiment; retain prototype and negative/inconclusive evidence.**
No repeatable substantial P speed gain and no clean full-size QN stability
admission. The full delivery contract works, but both carrier instability and
measurement closure issues must remain visible. Product identity/revocations/
floors/lease/resource/legacy compatibility gates remain separate; no automatic
new benchmark/tuning, Android change, APK, deployment, push, release, migration
or purchases. [Machine evidence](2026-10-21-quic-carrier.evidence.json).

## Consolidated Android candidate — 21 October 2026

The subsequent authorized product-path integration is saved in a
[separate report](2026-10-21-android-speed-candidate.md) and
[all-attempt evidence](2026-10-21-android-speed-candidate.evidence.json).
Exact96/734 sources produce compatible97/P0/P1/P2: existing RS8/16/effective8
+LEGACY64; effective32/32+CREDIT128; separately gated Q1. RS OPEN and Mux ALPN
remain independent. CarrierL/A0, packing/pacing/FEC/timebase candidate/QUIC OFF.
Seven actual old/new cases, concurrent32-stream/head/security/recovery and190 JVM
checks retained; Q1 early attempts9→1. Known baseline bootstrap assertions stay
non-green. No transport-research rerun, product admission or tester/public rollout.

Owner97 signed APK `d7c02ef5…` installed same-key/in-place; approved shared gateway
transition to `ae527cbd…` at12:30:28UTC. Bootstrap96/1011, identity and renewal
preserved; global P0 unchanged. Do not call this phase production unchanged:
it includes the explicitly approved executable change. External11:41 epoch event
remains separate and unexplained. First unused signed UI build and helper failures
are saved; no hidden replacement of a published release.

Original96/734 P0:0.811277 single/1.591011 aggregate Mbit/s,41.36/21.09s.
New97 P0a:0.661693/1.192411,50.71/28.14s.15/15 bodies each. Frozen consistency
threshold exceeded (−18.44%/−25.05%); static P0 integration review finds unchanged
limits/wire/Mux/cadence/recovery policy, but speed cause unresolved. Distinct
sessions and observed head retries prevent an isolated code-causality claim.
No original/new equivalence or clean speed acceptance. Original late exhaustion/
expiry is after measured delivery and has uncertain owner/counter scope, not lost
HTTP bodies. New P0 Android post-export remains connected, errors0→0.

16.0234375/64MiB synthetic delivered; P1/P2 forward/reverse and final P0 remain.
13:02UTC owner applied P0 last verified; owner-only gateway NEXT P1 prepared,
no restart, manual profile switch/export required before actual32/32/Mux128 load.
Whole-gateway CPU/RSS and small n6 medians/max are reported separately; Android
CPU/full media bytes unknown. P0 collectors closed, manifests/negative evidence
preserved. No push, public release, purchase or tester migration.

Continuation13:11UTC: P1a actual32/32/peer32/effective32+CREDIT128/Q0 at both ends,
15/15 bodies,1.400435/2.290405Mbit/s,23.96/14.65s; positive single observation only.
Android P1 post0→0 errors, closure/reverse pending. P0a later Android4 errors and
gateway whole-session3/RS exhaustion are retained; completed downloads remain
completed but P0a is excluded from clean acceptance.24.03515625/64MiB delivered.
Owner applied P1; owner-only next P2 prepared, manual switch and Q1 receipts pending.

Continuation13:22UTC: P2a actual both-end32/32/peer32/effective32, Mux128 and Q1;
15/15 delivered,1.348109/2.291969Mbit/s (24.89/14.64s). Versus P1a single−3.74%,
aggregate+0.068%; no added Q1 speed gain or repeatability established. Android1
protocol error already before load; post-export pending. Late P1 gateway terminal
has3 whole-session protocol errors/RS exhaustion after bodies; not clean acceptance,
not lost downloads. Total32.046875/64MiB. All four collectors stopped. Same installed97,
gateway epoch/binary/profile, no profile restart. Post-P2a export then fresh-session
P2b/P1b/P0b remain; no product admission, global default/tester changes or new research.

Continuation13:27UTC: P2a post-export connected in the same session, errors1→10
(+9) over664.356s including load/background. Exact onset and Mux counter branch
unknown; not nine download failures or proven Q1 defect. +89 retries/+555804retryB
cannot be compared directly with shorter P1/P0 export windows. No terminal/fallback
observed; server final counter still unavailable. P2a excluded from clean acceptance.
Only the predeclared fresh-session P2b observation remains allowed after ordinary
manual reconnect/new-tag gate, then P1b/P0b; no new load/profile change/restart here.
Budget unchanged32.046875MiB, current owner P2; final verified P0 still required.

Continuation13:34UTC: fresh P2b both-end32/32/Mux128/Q1, Android/server initial
errors0.15/15 bodies,1.245062/2.545860Mbit/s (26.95/13.18s); post-export pending,
not clean acceptance or completed reverse Q1 contrast. P2a late gateway terminal1/
RS exhaustion after delivery retained separately. Same binary/profile/epoch,
no restart/policy change. Five collectors stopped,40.05859375/64MiB delivered.
Post-P2b diagnostics then prepare owner next P1 and finish P1b/P0b; no extra P2 runs.

Continuation13:40UTC: P2b Android post errors0→0 in313.623s, no terminal error;
same-session limits/Q1 confirmed. +48 retries/+403405retryB includes background,
not comparable loss/early-retry classification; final server closure review pending.
Owner-only next P1 prepared/read back without restart, same gateway epoch/binary/
profile JSON and installed97; active P2 remains unchanged until manual reconnect.
Next Disconnect → Settings P1 → Connect → fresh export, then P1b/P0b.
No new payload here;40.05859375MiB used, collectors off, no product admission.

Continuation13:48UTC: P1b fresh actual both-end32/32/Mux128/Q0, initial errors0,
15/15 bodies,1.324169/2.583097Mbit/s (25.34/12.99s); post-export pending. P2b later
Android2 (after post0), gateway terminal1/exhaustion retained: not clean acceptance,
not lost downloads. Q1 effects in forward/reverse: single−3.736%/−5.974%,
aggregate+0.068%/−1.442%; no added speed gain, local correctness result separate.
48.0703125/64MiB delivered, all six collectors stopped. Same gateway binary/process/
profile and Android97; supplementary journal SSH timeout30s retained with one
read-only retry, not a transport failure. Post-P1b then prepare P0/final P0b remain.

Continuation14:05UTC: P1b post Android errors0→1 over831.678s including load/background;
exact onset/branch unknown, no terminal at snapshot. Not clean acceptance, not
a lost HTTP body. +95 retries/+534387retryB cannot be assigned solely to bulk or
classified as early/network losses from totals. No gateway final receipt yet.
Owner-only next P0 prepared14:04:55UTC without restart; active P1 unchanged until
manual reconnect. Same installed97, gateway binary/process/profile JSON and identity;
global/default/tester profiles unchanged. No new payload,48.0703125/64MiB used.
Next Disconnect → Settings P0 → Connect → fresh diagnostics, then actual both-end
P0 gate and final P0b. No new tuning or product admission; final return not yet verified.

Continuation14:20UTC: final P0b actual both-end8/16/peer16/effective8/LEGACY64/Q0;
single4MiB51.29s/0.654210Mbit/s and12 small responses complete. Both parallel2MiB
responses truncate (855726/790208B, curl18); then TUN-route guard fails, no rerun.
Existing scheduled renewal is proven by COMMITTED operation
scheduled-1792591872-28bb9be0fa02eed7 and journals: gateway stop14:11:24/restart
14:11:33UTC during parallel. Terminal0 protocol errors/RS cancelled is not success.
Same ae527cbd… binary, new PID775194/invocationa5b5909d…/profile738e5f52…; exact
archived comparison changes certificate/revocations only, keys/authority/floors
unchanged. No task restart/forced renewal/timer disable/rollback.11:41 remains unknown.
All seven phases attempted:103/105 complete,52.08203125MiB complete plus1.569685MiB
partial received; full56.08203125/64MiB reservation retained. All collectors stopped.
Windows raw single2.116×/2.024×; cumulative2.037×/1.903×; reverse aggregate unavailable,
no partial denominator or clean admission. Q1 no added speed gain; P0b single−19.36%
versus original, original/new cause unresolved. P1b later gateway3/exhaustion retained.
New gateway P0 session observed14:12:41UTC, current Android export still required;
no more load/profile switch, no automatic recovery/admission claim without receipts.
Nine helper tests pass; only offline accounting/parser changed, not the meter/product.

Closure14:30UTC: final `(14)` matches new P0 sessiond0ca9226… on both ends,
actual8/16/peer16/effective8/LEGACY64/Q0, Android CONNECTED/READY/capture open.
Current Android17 protocol errors belong to this new session, not interrupted P0b
or17 failed downloads; cause unknown. P0b history errors0/RS exhaustion/IO_CLOSED
and gateway0/cancelled remain a failed interrupted phase, not success. Same installed
artifacts/current renewed profile and preserved identity. No post-renewal active
route/DNS/HTTPS check or more load. Cycle closed with limitations, keep P0; no more
owner exports/actions, automatic repeat, product admission or distribution. Remaining
error/root-cause work is a separate decision, not an implicitly started new branch.
