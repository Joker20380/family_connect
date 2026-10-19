# MESH-PERF-ROOTCAUSE-1 — PARTIAL

18 October 2026. Read-only production audit and offline, test-only investigation.
**No production optimization selected, no release, no deployment, no restart.**
The approximately 300 Kbit/s application observation is the owner's report, not
a newly measured physical result. Units below are decimal Mbit/s unless stated.

## EXACT_BASELINE

- Initial worktree clean; local HEAD and GitHub `main` both
  `7656f2c65ea2928b71a928c12ee65a2f47f8ac4f`. Its parent/source checkpoint is
  `edca5447418141cb44c0706e26d1973d7defd397`. No checkout, branch, commit or push.
- This broad source checkpoint is **not** the installed UI84 source. The newer
  cumulative Android source remains in
  `state-client-build/transport-write-batching-1/source`, base
  `f5240994869826c6a28f59e58e38256c688cf6eb`, delta inventory
  `cdd089478624ff5113d14590a340092684127a674565c3acfe6750aa76a17790`.
  Freshly verified all 73 listed delta files; this is a delta manifest, not a
  claim that it inventories every inherited file.
- Gateway source inventory
  `aeeb6755bd235160127cfed67da4a870ae340cfebe89fc6d0f937908607d9483`:
  all 231 listed files rehashed successfully in the preserved gateway source.
  Its local executable matches the configured NL executable below.
- Root-source and preserved-UI84 experiments are separate. UI84 includes an async
  Reliable writer, bounded ACK/open coalescing, head fast-retransmission eligibility,
  additional receive diagnostics and TLS/Mux write batching absent from root main.
  Testing root main alone would misdiagnose the deployed candidate.
- The October RTP reorder correction is present **byte-identically** in root,
  UI84 and gateway `telemost/rtp.go`. It is not a missing deployment fix here.

GitHub readback, not inferred from a push:

| SHA / workflow | Observed result |
|---|---|
| edca544 phase0, run 39110077526 | tests FAILURE at full pytest; failover FAILURE building isolated stack |
| 7656f2c phase0, run 39110172718 | same two failed job stages; Rust/test_failover follow-on steps skipped |
| edca544 clients, run 39110077439 | Final readback: Android, Linux, Windows, Windows compatibility SUCCESS; release job SKIPPED. Initial Android read was IN_PROGRESS. This is root-source CI, not UI84 installation acceptance. |
| edca544 golden, run 39110077459 | SUCCESS |

These observations do not establish full-CI acceptance. Empty legacy commit-status
lists are not successful check runs. CI failures were not repaired or rerun here.
GitHub `/releases/latest` returns 404; the first entry from `/releases?per_page=1`
is prerelease `v0.2.11` (26 September). That listing is not an Android installation
or a three-platform public-download audit. No public asset bytes were downloaded.

Relevant prior evidence reviewed, with scope retained:

- [PERF-1 carrier capacity](2026-09-27-webrtc-5n-perf1-carrier-capacity.ru.md),
  [PERF-2 envelope](2026-09-27-webrtc-5n-perf2-reliable-envelope.ru.md),
  [5N.4 TCP](2026-09-28-webrtc-eu4-single-tcp.ru.md),
  [5N.5 mux/DNS](2026-09-28-webrtc-eu5-mux-dns.ru.md).
- [RTP identity correction](2026-10-06-rtp-identity-rewrite-1.md) and
  [beta69 acceptance](2026-10-07-rtp-identity-deploy-1.md): SFU publisher/subscriber
  RTP numbers are different domains. Preserve carrier identity correlation.
- [Mux scheduling](2026-10-07-tcp-mux-scheduling-1.md): the historical single-core
  fixture sensitivity is not evidence of current runtime starvation.
- [Supervisor deployment gate](2026-10-13-gateway-seed-supervisor-deploy-1.md),
  [candidate dataplane uncertainty](2026-10-15-supervisor-candidate-dataplane-rootcause-1.md),
  [17 October operational snapshot](2026-10-17-vpn-health.ru.md),
  [activated-access preflight](2026-10-18-telemost-all-activated-preflight.md),
  [MESH source checkpoint](2026-10-18-mesh-product-integration.md).
  No old failed experiment was relabelled as a new performance result.

## CURRENT_DEPLOYMENT_ATTESTATION

Read-only SSH used only the two authorized Family Connect hosts. No service change,
profile/key readback, DB mutation, renewal, credential issuance or active media probe.

| Object | Identity and classification |
|---|---|
| NL configured executable | `/opt/apps/family_connect/friends-restricted/bin/bootstrap-broker-signal-observation-20261012`; SHA256 `4b722d2d7f2159b96953e27777494bf596768f860ee8da7e634fb1100b08fab7` |
| NL process, 08:15:19 and 08:26:55 UTC | `family-connect-restricted-bootstrap.service` FAILED, MainPID=0, NRestarts=6, ExecMainStatus=1; last start 06:44:21 UTC. **No running /proc executable identity available**. The filename is not the old 21f0a0fd binary. |
| NL configured flags | `--listen 127.0.0.1:18444 --duration 4h --chat-services --seed-rotate-after 3h`; no transport-window override in these flags |
| Prior accepted deployment receipt | 17 October 09:01:38 UTC `PASS_BOUNDED_READINESS`, same 4b722d2d hash, served-chain PASS; active restricted sessions UNKNOWN. Not a present-day traffic or performance result. |
| RU HTTP process | Active PID1921548, NRestarts=0, start 18 October 02:41:52 UTC; `friends-access/http-publisher-research74-20261010.pyz` SHA256 `12ca0c72a89ff20c1b3c70a1182a2d5d98d4d78d25e7a079bb4d75bdf34060ed` on disk |
| Retained signed Android artifact | `0.1.18-research84-ui60-4-batch1`, code84; SHA256 `697f9c244b67f75e7e3e612dbcd91a48891d32ee77e23fd9bce173a5f049233f`, freshly rehashed locally |
| Restricted Android native library | arm64 `libfc_restricted.so`: `dd722eada0da7c890a8d71a72099cba5d0bbac1ce73377bbdbc8e7b85d820c23`; all 12 native library hashes retained in companion evidence |
| Installed Android | Prior 17 October receipt reports code84/API31 owner installation; separate tester evidence reports API34. **Fresh installed APK/native attestation unavailable: ADB discovery returned no devices**. These are not interchangeable devices. |
| MESH naming APK | Unsigned code84 artifact `2af685e5a60667af4cfedc1b997714cc2fa038d9976d5385fb0abe044f2e4a35`, freshly rehashed locally; not an installation or distribution |
| Old failed supervisor candidate | Historical binary `53beb661cab014c32494fa8d7384f9565300311ef467e62ae9f8c20201e5138f`, source134083d; not the configured binary and not performance evidence |

The current admission/API v2 work remains NOT_DEPLOYED. UI84 source consolidation,
gateway supervisor acceptance, credential readiness and desktop MESH availability
are independent gates, not waived by this investigation. Service failure is a live
measurement prerequisite failure, **not proof of the cause of earlier low speed**.
No claim that all other user sessions are absent is made.

## EXISTING_DIAGNOSTIC_CAPABILITIES

| Existing mechanism | What it proves / limitations |
|---|---|
| `sessiontrace` | Session/direction-bound Reliable sequence/attempt, carrier fragment identity, publisher and subscriber RTP observations; bounded rings. Diagnostic-tag receiver acceptance/consumption and ACK-write observations. No new schema or identifiers added. |
| Reliable `Stats` / `Flow` | DATA/ACK/retry/duplicate/reorder counts, send base/next, SACK mask, receiver buffer, high-water marks, bounded first/recent recovery events. ACK receipt alone is not consumption/base advancement. |
| `telemost.PerformanceSnapshot` | Queue depths/capacity, media counters and selected numeric/bool Pion statistics; identifiers/address strings excluded. Snapshot is not a queue-residence histogram or proof of SFU delivery. |
| Mux stats | Flow stalls, per-stream credit/buffers, scheduler frames/max wait, DNS and destination counters. These are not application RTT percentiles. |
| Existing local Pion/loss tests | Byte-exact framing, reorder/deadline, fresh retry identity, duplicate and loss recovery. No external SFU capacity claim. |
| New test-only probes | `tcpforward/mesh_performance_test.go` and `telemost/mesh_performance_test.go`; no production Go edits. Fixed bounds, opt-in performance matrix, bounded timing samples, existing Stats and SessionTrace reused. |

Only test binaries, logs/profiles and documentation were generated. No diagnostic
code was added to a normal production build. Physical packet loss, actual media
fps/bitrate and receiver-consumption latency distributions remain unmeasured today.

## PERFORMANCE_LAYER_MODEL

Application HTTPS/TCP → Android VPN TUN/gVisor TCP termination → wholedevice copy
→ TCP Mux → Family messages/TLS1.3 → net.Pipe bridge → ReliableStream → carrier
fragments/VP8 → Pion RTP/SRTP → Telemost SFU → reverse stack → gateway TCP socket
→ HTTPS origin. DNS uses encrypted Mux requests, not direct client resolution.

This is not simply an end-to-end TCP connection carried inside another TCP
connection: TUN TCP is terminated, and the gateway opens a separate TCP socket.
Reliable ordered delivery below one TLS connection still creates shared HOL across
Mux streams. RTP NACK/RTX and Reliable retries can duplicate recovery work. TCP
backpressure/retransmission at the two edges can compound delay without making the
media transport itself TCP. QUIC/general UDP are unsupported on this path.

### Reproducible offline matrix

Linux/amd64 Go1.26.1, GOMAXPROCS=4, cached locked modules, GOPROXY=off. Synthetic
paired FIFO endpoints, 256-message bounded channels, 40ms one-way propagation,
2ms serialization per modeled 8192-byte carrier fragment, zero injected loss.
This is a **model**, not Telemost and not the production 256-frame queue. It omits
SRTP/UDP/IP, SFU scheduling, real bandwidth limits, NACK, Android and application
HTTPS. No synthetic rate below is a physical capacity measurement.

- Carrier-model / Reliable / Family: 128 payloads of 384,1024,16336,16384 bytes,
  each direction, one ordered lane, byte-exact aggregate verification.
- Mux over authenticated Family TLS/Reliable: real loopback TCP origin, one and
  four concurrent flows, upload and download, 128KiB per flow. Separate 1-byte
  echo flow measures 8 idle RTTs and loaded RTTs on the **same** mux/carrier.
- Additional 100ms one-way test isolates the BDP effect for 1024-byte writes.
- Additional diagnostic-tag trace on/off repetitions use larger TCP bodies.
- Credentials are freshly generated synthetic identities from existing fixtures.
  No live identities or authentication bypasses.

Run from repository root (set GO and GOPATH to the existing toolchain/cache):

```sh
export GO="$PWD/state-client-build/field65-export16/diag-source-freeze-1/resume-tools/go/bin/go"
export GOPATH="$PWD/state-client-build/field65-export16/diag-source-freeze-1/resume-tools/gopath"
export GOCACHE=/tmp/mesh-go-cache GOTOOLCHAIN=local GOPROXY=off GOMAXPROCS=4
MESH_PERF=1 MESH_PERF_SOURCE=7656f2c "$GO" -C carrier test ./tcpforward \
  -run '^TestMeshPerformanceMatrix$' -count=1 -v -timeout=4m
MESH_PERF=1 MESH_PERF_DELAY_MS=100 "$GO" -C carrier test ./tcpforward \
  -run '^TestMeshPerformanceMatrix$/reliable/1024' -count=1 -v
"$GO" -C carrier test ./telemost -run 'TestMesh|TestRTPReorder' -count=1 -v
```

For UI84 use Go's `-overlay` to map the preserved source's virtual
`carrier/tcpforward/mesh_performance_test.go` to this test file, and run from its
`carrier` directory. **Do not copy over accepted source or rebuild/install UI84.**
The private snapshot/inventory is required to reproduce that comparison; it is
not equivalent to checking out root HEAD. For tracing use `-tags=fc_owner_diagnostic`,
`MESH_PERF_TRACE=1` versus unset, and `MESH_PERF_TCP_KIB=1024`.

Metrics use end-to-end receiver completion, not sender-queue completion. TCP tests
also wait for target verification and the in-progress probe, conservatively
including its final RTT. Handshake/warm-up/idle probes are outside the timed bulk
window. Ten-ms Stats samples estimate pending slots/full-window time. ACK interval
is **all ACK arrivals**, including redundant ACKs, not RTT. Timing samples are
bounded at4096; p99 from a handful of probes is descriptive, not a tail SLA.
`endpoint_bytes` includes FRS/control bytes but **not wire bitrate**; wire bitrate
is explicitly null. Modeled frame count/residency must not be relabelled actual RTP.

## MEASURED_BOTTLENECKS

The final numeric matrix and trace comparison are recorded in the companion
`2026-10-18-mesh-perf-rootcause-1-evidence.json`. All results are separated by
source, layer, direction, size, flow count and diagnostic mode.
Evidence SHA256: `0bc146300ccedddeaee08260a644337cf448cd922c923b4a64afdb5a593a96a3`.
It includes the exact test-source hashes, endpoint source hashes, all native-library
hashes, CI observations and separate offline profile identities. Logs/profiles
remain locally under `/tmp/mesh-perf-results/`; no executable or credential is
added to Git. The reproducible fixture and sanitized numerical evidence are the
durable deliverables, not the transient `/tmp` files.

Primary unprofiled results (modeled link,80ms propagation RTT, default windows):

| Layer / workload | Main upload | Main download | UI84 upload | UI84 download |
|---|---:|---:|---:|---:|
| Carrier model,16384B,1 lane | 30.428 | 30.426 | 30.449 | 30.423 |
| Reliable,384B,1 lane | 0.297 | 0.297 | 0.300 | 0.299 |
| Reliable,1024B,1 lane | 0.792 | 0.792 | 0.801 | 0.798 |
| Family,16336B,1 lane | 11.284 | 11.271 | 11.359 | 11.374 |
| Family,16384B,1 lane | 4.135 | 4.133 | 4.170 | 4.168 |
| TCP Mux,1 flow | 2.662 | 2.829 | 3.747 | 3.793 |
| TCP Mux,4 flows,aggregate payload | 3.474 | 3.267 | 7.529 | 6.616 |

The high carrier-model number is a configured synthetic ceiling, **not** available
Telemost bandwidth. The16KiB TLS/Reliable boundaries, ACK traffic and shared credit make
the rows non-additive. Main→UI84 is a cumulative source comparison with multiple
differences, not a controlled one-patch batching attribution. No new correction
was applied between these source runs.

At200ms modeled propagation RTT, Reliable1024B gives0.329/0.329Mbit/s main
upload/download and0.330/0.331 UI84. In the80ms384B main upload run, sampled mean
pending is effectively8 and the window is full for almost every sample. All80
published measurement rows (60 primary/delay,20 longer tracing) are byte-exact;
all have zero injected loss and zero observed FRS retransmissions. Each row records
duration, queue bound/high-water, bounded residence/ACK intervals, allocations,
CPU and pending/full-window samples. Primary timed transfer totals are33.930s
main and32.192s UI84; these are collections of short tests, not sustained trials.

Diagnostic-tag tracing control, five alternating on/off pairs per flow count,
1MiB per flow, no profiler, separate recorder per endpoint:

| Download flows | Trace-off goodput median [min,max] | Trace-on median [min,max] | Change | Loaded RTT p50 median off→on |
|---|---|---|---:|---|
| 1 | 3.914 [3.826,4.246] | 3.843 [3.808,3.943] | −1.8% | 118.51→126.89ms |
| 4 | 8.204 [7.934,8.524] | 7.949 [7.715,8.265] | −3.1% | 170.98→169.11ms |

No large goodput tracing penalty is demonstrated in this model, but single-flow
RTT shifts+7.1% and intervals are short (10.5–10.8s summed bulk per single-flow
mode,20.4–21.1s per four-flow mode). **The≤5% latency perturbation gate is not
passed**, and real RTP/receiver diagnostic cost remains unmeasured. Do not call
tracing universally negligible or use the small apparent improvements as a fix.

| Rank / classification | Evidence and reproduction | Impact / confidence | Correction decision / regression risk |
|---|---|---|---|
| 1 VERIFIED in local model; UNKNOWN contribution to owner's session | Segment-count window wastes capacity on small records; matrix Reliable/384 and /1024, default config, no loss | ~0.30Mbit/s with384B at80ms RTT; ~0.33Mbit/s with1KiB at200ms; almost all samples have8 slots occupied. High confidence in mechanism, not in current workload distribution | Measure deployed record histogram first; bounded batching already exists in84. Do not blindly increase windows. Wrong coalescing risks delay, ordering and cancellation. |
| 2 VERIFIED in root/local Family stack | 16384-byte Family payload crosses TLS/FRS boundaries; /family/16336 vs /16384 | 136 vs382 DATA segments for128 messages, about11.3 vs4.1Mbit/s in the model; plaintext size, not expensive encryption alone. High local confidence | Existing batch1 is designed around this boundary; do not replace84 with root. Exact comparative physical gate still required. |
| 3 VERIFIED structural HOL; LIKELY field latency contributor | One ordered Reliable/TLS lane; consumption advances cumulative base; Mux shares it | Loaded local probe RTT rises versus idle without packet loss. Physical delay allocation UNKNOWN | Measure queue/consume/base advancement per endpoint; never weaken correctness or split authenticated streams speculatively. |
| 4 VERIFIED arrival-driven RTP deadline; UNKNOWN frequency/impact | Gap fixture holds102 after100 for150ms, only103 arrival releases it. Both deployed snapshots include October fresh-gap fix | 100ms is not a hard wall-clock upper bound; sparse traffic can wait longer, then FRS recovery compounds it | First measure persistent-gap ages and data vsACK losses. No timeout/reorder change selected. Premature discard can amplify loss. |
| 5 UNKNOWN external carrier / RTP adaptation | 2ms application pacing is not remote delivery; no current live SFU session | Cannot assign the missing1.5Mbit/s to SFU, cellular or loss. Current fps/wire efficiency/loss unavailable | Exact paired real-media measurement below; no pacing/nominal-clock tuning. |
| 6 NOT DEMONSTRATED CPU/lock/egress bottleneck | Offline CPU/allocation/block profiles; NL service has no PID, Android absent | Local model CPU is far below one core; not transferable to phone/SFU/gateway. No current endpoint CPU claim | Independent loaded profiles required; no buffer-pool/worker/GC tuning justified. |

No measured physical loss budget sums to the reported1.8→0.3Mbit/s difference.
We have demonstrated an internal **possible** mechanism, not the dominant cause
of that specific deployed connection. ACK serialization-to-remote is disproved.

## RTP_VP8_ANALYSIS

Source: `telemost/session.go`, `signaling.go:writerLoop/writeVP8Sample`, `msg.go`,
`rtp.go`, plus the pinned Pion v4.2.15 packetizer/default interceptors.

- Constants match both preserved endpoint sources: 2ms data-frame sleep,33ms sample
  duration,2s keepalive,256 send frames. Frames are dequeued and passed to
  `TrackLocalStaticSample.WriteSample`, **then** the writer sleeps. Actual ceiling
  is below500 frames/s once write/scheduler time is included.
- Pion packetizes a sample synchronously into RTP writes; Duration advances the
  90kHz RTP clock by2970 ticks, it does not impose a33ms wall-clock wait. At500
  samples/s this represents16.5 media seconds per wall second. SFU interpretation,
  timestamp rewriting and forwarding adaptation require measurement; no causal
  speed limit follows just from these constants. Default NACK/report/stats/TWCC
  interceptors do not establish a custom adaptive bitrate/pacing controller here.
- A full16KiB FRS payload plus64-byte header is16448 bytes, therefore **three**
  carrier fragments, not two. Each fragment has24-byte carrier header and17-byte
  VP8 interframe prefix. Bound-Pion test (no network):384 useful bytes→502 RTP
  bytes/1 frame/1 packet;1024→1142/1/1;16384→16782/3/15. These exclude SRTP,
  UDP/IP, RTCP, ACKs and retransmissions. Useful/RTP efficiencies:76.5%,89.7%,97.6%.
- Nominal pacing envelope for full FRS payloads is about21.85Mbit/s
  (`16384*8/(3*.002)`), not a guarantee. For384-byte DATA alone it is1.536Mbit/s;
  shared ACKs/keepalives, consumption and propagation reduce that. A full256-frame
  local queue represents at least512ms of serialization, but no present live full
  queue was observed.
- Reorder window256, gap100ms; deadline is evaluated in `push`, not by a timer.
  New-gap deadlines reset on receive-head advancement. The October bug is already
  corrected; do not restore the old behavior. VP8 rejects discontinuous/incomplete
  frames and carrier assembly verifies length/CRC before Reliable accepts them.
  Missing any of15 RTP packets can lose a full16KiB FRS segment absent RTP repair:
  at independent1% packet loss, `1-.99^15≈14%` frame-group exposure, **an illustration**,
  not today's loss estimate. RTX correlation is required before counting retries twice.

## RELIABLESTREAM_ANALYSIS

`SendContext` serializes callers via `sendGate`. Each chunk waits for `op.done`.
In root `run`, `op.done` follows `endpoint.SendContext(encode(packet))`; in84 it
follows the async writer result. Telemost `SendContext` returns after enqueueing
all fragments. Neither waits for remote ACK, RTP transmission or receiver delivery.
The new test submits eight 1-byte sends without any receiver consumption and
observes eight outstanding segments. Existing backpressure tests verify ninth-send
blocking/cancellation. Increasing concurrent callers does not create independent
Reliable windows because of the common send gate.

Default and preserved-source config: payload16384, send8, receive16, RTO1s,
retries8, max-age20s, protocol maximum window32. No deployed live negotiated
window is asserted while MainPID=0. Source callers use `familysession.Open` and
its default config. Sender budget is `min(localSend,remoteReceive)` slots.

`writable = next-base < min(sendWindow,remoteWindow)`. SACK suppresses retransmission
but does not free window slots. The cumulative ACK is receiver `receive`, advanced
by `consume` only after delivery to the consumer. Thus blocked TLS/Mux consumption
can hold eight SACKed segments without any network packet loss.

Nominal capacity:8×16384=131072B; actual capacity is the sum of the eight record
sizes. Eight384B records carry3072B; eight1024B records8192B. No fill/coalescing is
performed by Reliable. At80ms,3072×8/.08=0.3072Mbit/s; at200ms,8192×8/.2=
0.32768Mbit/s, matching the local experiment closely. This is **not** an8×16KiB
window in those workloads.

Conversely, a fully packed131072B window sustaining only0.3Mbit/s would need an
effective feedback/consumption cycle near3.50s, or non-window stalls. At500ms,
mean useful records of about2344B already give0.3Mbit/s. These two alternatives
are distinguishable with the missing deployed segment histogram and ACK/consume
timings; nominal payload size is not sufficient evidence.

| Target rate | BDP at100ms | at500ms | at1s |
|---|---:|---:|---:|
| 0.3Mbit/s | 3750B | 18750B | 37500B |
| 1Mbit/s | 12500B | 62500B | 125000B |
| 2Mbit/s | 25000B | 125000B | 250000B |
| 5Mbit/s | 62500B | 312500B | 625000B |

At500ms and fully packed records, default131072B is sufficient in principle for
~2.10Mbit/s. At1s it allows~1.05Mbit/s. Small records can reduce that by orders of
magnitude without changing the advertised window. The historical application
echo RTT is not a substitute for today's Reliable ACK/consumption RTT.

Root retries are RTO-driven with tick≤100ms;84 additionally permits first head
retry after RTO/4 when≥3 later segments are SACKed (still subject to tick/write
scheduling). Constants alone do not describe this behavioral difference. No
reliability parameter or recovery behavior was changed by this investigation.

## TCP_MUX_ANALYSIS

Root `MaxData=16384`, Mux window65536B per stream,10-byte Mux header,12-byte Family
message header. TLS1.3 adds5-byte record header plus content-type/tag (typically22B
total). A full Mux DATA message does not fit into one16KiB Reliable chunk. TLS
dynamic record sizing and tiny trailing chunks can consume additional slots.
Small window-update/control writes also consume records. The two net.Pipe bridge
goroutines do not turn individual TLS writes into full Reliable payloads.

UI84 already implements bounded `SendBatchContext`, at most32 messages,
`MaxBatchPlaintext=16362`, Mux DATA cap16340 when batching is available. This
preserves the legacy receive framing. Batch1 cannot be diagnosed by assuming these
changes are absent. Its direct single-message Family API still exposes the
16384-byte boundary effect; the Mux path uses the batch API instead.

One blocked lower lane affects every Mux flow. Multiplexing improves application
concurrency/packing but does not give each TCP flow its own Reliable window.
The four-flow local test exercises real TCP sockets over the synthetic lower lane,
not full-device HTTPS. No claim of a production Mux scheduling failure follows
from the old single-core test flake.

Why a speed test may report1Mbit/s while downloads sustain0.3Mbit/s: multiple
parallel transfers can improve packing; short averaging intervals may count
initial buffered bytes; DNS/TCP/TLS setup and idle gaps affect whole-download
averages; payload sizes, direction, origin and loss/RTT vary. Historical PERF-2
already included **Family TLS1.3 over ReliableStream**, with eight application
echo requests and large16KiB payloads. It was not bare Reliable throughput and
did not include TUN/browser/TCP mux. Its1.742311Mbit/s/30min and1.883505Mbit/s
earlier echo result cannot be subtracted directly from today's browser speed.
Also verify Kbit/s versus KiB/s:300KiB/s would be2.46Mbit/s, a different problem.

Historical TCP evidence is not uniformly0.3Mbit/s either:5N.4's accepted public
HTTPS10MiB took53.433s (~1.570Mbit/s including OPEN/close), controlled10MiB duplex
was1.422Mbit/s per direction, while the300.821s sustained duplex was0.599Mbit/s
per direction. These used a separate diagnostic CLI, not Android TUN/browser.
5N.5's0.499Mbit/s one-way bulk was deliberately capped at0.5; its roughly1Mbit/s
**aggregate duplex** is not1Mbit/s download and is not a measured ceiling.
PERF-2's own cap2→3 sweep increased goodput only1.48% while application outstanding
rose6.574→7.955 of8 and RTT485.831→579.499ms; that report already classified a
window/RTT region, not proven carrier saturation. No resolved experiment is reopened.

## RTT_ANALYSIS

Local paired idle/loaded RTTs are in evidence; loaded bulk raises same-mux probe
delay even with zero loss. Decompose future physical latency into sender queue,
RTP transit/reorder, carrier assembly, Reliable accept→consume, ACK queue/transit,
TLS/Mux scheduling and gateway origin-connect/read time. Use endpoint-local
monotonic intervals; do not subtract unsynchronized cross-host wall clocks.

Primary download idle→loaded p50: main1-flow96.56→169.93ms, main4-flow97.19→273.39ms;
UI84 1-flow90.40→96.78ms,4-flow90.36→110.15ms. Only2 or5 loaded probes occur in
these short cases; their p95/p99 are **not** credible sustained tail estimates.
Longer trace controls retain89/89 single-flow loaded samples and122/129 four-flow
samples across their five runs, still not a physical jitter/latency SLA.

Historical PERF-2 baseline had application RTT median554.731ms, p95 819.938ms,
p99 1375.918ms, with7 retransmissions. These are historical bidirectional echo
measurements, not current idle network RTT. Current physical idle/loaded RTT,
send-window stall durations and receiver-consumption percentiles are UNKNOWN.

Offline profile (separate profiled run, not a phone or gateway profile):48.58s
wall time,3.55s sampled CPU (~7.31% of one core). memmove0.22s; sampled allocations
189MB, of which63.95MB bytes.Clone,24.40MB Reliable encode, substantial test
payload construction/copying. Mutex blocked aggregate109ms; channel/select wait
dominates block profile (summed over goroutines, **not wall time**). No local CPU
saturation is demonstrated. This does not clear Android thermal throttling,
gateway I/O pressure, actual WebRTC workers or provider egress.

Reproduce the separate profile with the same opt-in command plus
`-cpuprofile=/tmp/mesh-cpu.pprof -memprofile=/tmp/mesh-mem.pprof
-blockprofile=/tmp/mesh-block.pprof -mutexprofile=/tmp/mesh-mutex.pprof
-o /tmp/mesh-matrix.test`. This cached Go installation lacked the prebuilt pprof
tool; `go build -o /tmp/mesh-pprof cmd/pprof` built its matching local standard
tool, with no dependency download. Keep profiler-enabled numbers separate from
the primary unprofiled matrix and trace cost comparison.

## IPV6_ROOT_CAUSE

**Two independent blockers verified; not a cosmetic detection failure.**

| Layer | Capability / evidence | Classification |
|---|---|---|
| Android VPN Builder | MTU1280, IPv4 and IPv6 addresses, routes `0.0.0.0/0` and `::/0`, IPv4 virtual DNS; both root and84 | Capture configured, not missing IPv6 route; installed route table unavailable today |
| Native TUN | fdbased MTU1280 → Xray/gVisor endpoint; preserved patched stack registers IPv4+IPv6 and both default subnets | Parser/stack dual-stack; no new route advertised |
| wholedevice destination policy | `Allow` rejects nil IP or `ip.To4()==nil`, increments IPv6Denied; same in84 | **Explicit IPv6 TCP denial before OpenTCP**; capture prevents underlay leak |
| DNS AAAA | UDP/TCP DNS requests framed unchanged through Mux; existing AAAA round-trip test | AAAA supported by protocol; fresh resolver/provider answers not measured |
| Mux/OpenTCP | Host string, canonical IPv6, bracketed `net.JoinHostPort`, `LookupNetIP("ip")` | IPv6 destination representation supported |
| Gateway destination policy/socket | Public2000::/3 subject to SSRF exclusions; `DialContext("tcp",...)`, sequential bounded address attempts | IPv6 socket API supported; loopback/private/link-local/metadata remain denied |
| NL OS egress | No IPv6 default, only ULA global-scope addresses in observed output; `ip -6 route get 2606:4700:4700::1111` → **Network is unreachable** at08:26:55UTC | **No current public IPv6 egress route**; not proof of provider's permanent capability |
| RU OS | IPv6 default route exists | Control host is not a substitute for NL egress; no external-connectivity proof |
| Outer WebRTC | `NetworkTypeUDP4` and IPv4 filter | IPv4-only underlay today; an IPv4 outer carrier could still carry IPv6 destinations if inner policy/egress supported |
| External IPv6 test site | Not contacted through MESH | Browser/test-site failure cannot identify the individual blocker |

IPv6 forwarding=0 is **not** the explanation for a user-space TCP proxy: gateway
TCP sockets need an IPv6 route/source address, not kernel packet forwarding.
AAAA suppression is not evidenced. Neither synthetic route advertisements nor
loosening destination policy would repair the missing NL route safely.

Safe migration design, **not implemented**: first establish real provider IPv6
allocation/source/default route and gateway socket egress; test AAAA, literal and
dual-stack fallback with the current SSRF policy. Then separately add explicitly
reviewed IPv6 support to wholedevice policy and packet-level tests, preserving
capture/drop on unsupported paths, DNS containment, cancellation and quotas.
Verify native library/APK provenance, IPv6 leaks, PMTU1280 and upgrade/reconnect
on physical Android before enabling. Keep existing IPv6 fail-closed behavior until
all layers pass; changing only the client would still fail on NL.

## OPTIMIZATION_CANDIDATES

**No new deployed-path candidate is selected.** The defensible decision is to
measure the already-installed batch1 path before another optimization. Two of
the apparent root-main deficits (blocking writer, unbatched Mux) are already
addressed in the preserved endpoint source, without an end-to-end speed proof.

One locally justified correction strategy, not an implementation authorization:

| Item | Bounded record packing / existing batch1 evaluation |
|---|---|
| Exact source scope | Existing `familysession/batch.go`, `tcpforward/mux.go` scheduler and `mux_stream.go` chunk bound in84. Root lacks them; do not silently transplant them or replace UI84. A further change requires measured small-record/window loss **on84**. |
| Mechanism | More useful bytes per Reliable slot; avoid TLS record/chunk boundary tail fragments; no increase to advertised windows |
| Expected effect | Local layer model demonstrates mechanism and source-dependent Mux gains; no promised field factor,1/2/3–5Mbit/s or RTT target. Extra batching delay must be bounded. |
| Tests | Exact legacy/batch receive compatibility; byte-exact single/multi flow upload/download; half-close/reset/cancel, admission and revocation, bounded memory, stalled reader, asymmetric loss, reconnect, representative physical HTTPS and loaded RTT; identical-source trace A/B |
| Endpoint coordination | Sender-only encoding/packing can interoperate with legacy receiver; benefits are directional. Both endpoint identities must be pinned for a bilateral claim. Existing API does not permit arbitrary wire changes. |
| Security | Preserve TLS1.3, Family sequence/identity/proof, message/credit bounds, destination policy and expiry. No new plaintext or keys in diagnostics. |
| Risk | Added buffering/delay, scheduler fairness, cancellation/FIN ordering, memory pressure; stable reconnect must remain unchanged |
| Rollback | This task has no runtime patch to roll back. Any future experiment uses an isolated executable; retain original binary/hash and unchanged current credentials/floors. No APK downgrade/data clear or production binary swap in this task. |

No pacing/RTO/window/IPv6 optimization is proposed for immediate implementation.
Timer-driven gap handling and larger windows are questions gated by measured
gap ages/BDP respectively, not additional selected candidates.

## SAFETY_AND_ROLLBACK

Production reads only; no gateway restart/deployment, live VPN action, package
installation, accepted-source edit, signing, tag, release, push, admission bypass
or secret publication. ADB server discovery ran, but there was no attached device
and no application/VPN command. No neighboring services or excluded host used.
No product version, public distribution, catalog or invitation-page version changed.

Local rollback is removal of this task's two test files and documentation additions
only; preserve pre-existing snapshots and evidence. Do not reset/rebuild installed
UI84 or restore old credential material. Re-running the matrix is opt-in and needs
loopback permissions; normal CI skips its performance loop.

Validation: six transport packages pass `go test -race` (Reliable, Family TLS,
Telemost including two-process local Pion, SessionTrace, TCP forward/Mux,
wholedevice); all live tests explicitly excluded. New accounting/deadline tests
and existing reorder deadline tests pass. Matrix payloads are byte-exact with
zero injected loss and zero observed Reliable retransmissions in reported runs.
Selected diagnostic-tag race checks also pass for Reliable, Telemost,
SessionTrace and TCP Mux, including new probes and existing correlation/loss tests.
Whitespace checks pass; the existing public-source guard reports1942 indexed files,
zero blocked. That guard does not cover unstaged/untracked additions; the new
evidence is explicitly limited to synthetic counters and public artifact identities.
No claim of full repository pytest/native Android runtime acceptance.

## NEXT_EXPERIMENT

### Minimum evidence to settle the current throughput cause

1. **Entry gate:** independent operational owner restores normal readiness under
   the already accepted maintenance procedure, outside this no-restart task.
   Attach the intended test phone; read installed APK/native hashes, exact loaded
   gateway `/proc/PID/exe`, source inventory, negotiated defaults and session tag.
   Do not treat all-activated or supervisor work as implicitly accepted.
2. Use an already admitted **isolated test identity/room**, not the owner's active
   VPN. Confirm no shared-user disruption and bound traffic, lifetime and CPU.
   No verified usable real-media resource exists at this task's entry state.
3. Same physical route/time window, both directions,1 and4 streams: carrier-only
   byte-exact received goodput; Reliable; Family; Mux/TCP; HTTPS via an unchanged
   test TUN/client against a controlled known-size origin.30s warm-up,≥120s bulk,
   ≥3 paired repeats; record startup separately and a sustained10MiB download.
4. Record actual RTP/RTCP/SRTP byte/packet deltas, frames written/received/discarded,
   NACK/RTX and FRS retry bytes, packet loss, ACK base/mask intervals, effective
   bytes and slots in flight, queue depth and residence, accept→consume latency,
   idle/loaded RTT p50/p95/p99 with sample counts and source/build identities.
   Use existing SessionTrace receiver/ACK correlation; do not compare raw RTP
   sequence numbers across the SFU or export payloads, rooms, credentials or IPs.
5. Independent Android and gateway process CPU/thread/RSS/allocations/GC and
   bounded goroutine/block/mutex profiles **only in isolated diagnostic processes**;
   record host contention/thermal conditions and gateway origin TCP/egress rates.
   Do not attach a debugger or enable pprof on production. Trace off/on randomized
   paired controls must show≤5% median goodput/RTT shift, or use untraced timing
   plus a separate diagnosis session instead of claiming negligible overhead.
6. Decision: low carrier-only rate with empty local queues → external-path limit;
   carrier has headroom but small segments/full slot window → packing/BDP;
   discard/retry/gap correlation → media recovery; accepted-but-unconsumed data
   → receiver/upper-layer HOL; loaded CPU/queues → endpoint scheduling. Otherwise
   retain UNKNOWN, not an aggregate speed-test explanation.

### Coverage boundary

| Requested dimension | This task | Missing |
|---|---|---|
| Carrier-only | Synthetic queue model + real bound-Pion packet accounting + existing local Pion regression | Actual SFU bitrate/fps/loss/queue residence |
| Reliable / Family | Byte-exact modeled link, sizes and both directions, default windows | Same physical path and loaded ACK/consume timing |
| TCP Mux | Actual local TCP+Family+Reliable,1/4 flows, both directions | Android TUN and real gateway load |
| HTTPS over MESH | Historical evidence reviewed only | Present pinned-version comparative measurement |
| RTT | Same-mux idle/loaded local probes with sample counts | Physical local/media/gateway decomposition |
| IPv6 | Implementation + fresh NL route attestation | Admitted live DNS/socket/TUN end-to-end migration tests |

## FINAL_RESULT

**PARTIAL.** Verified send completion semantics, reproduced a segment-size/window
bottleneck and TLS boundary amplification, distinguished root from actual batch1
source, confirmed corrected-but-arrival-driven reorder timing, and identified
two concrete IPv6 blockers. Production state and CI are explicitly not assumed
healthy/accepted. Current300Kbit/s dominant cause and external carrier capacity
remain unresolved because the intended gateway service is failed and no physical
Android is attached. The minimum resolving experiment is specified above
(acceptance outcome C; local evidence also supports A as a mechanism, not a field fix).

The performance problem is **not solved**. No end-to-end improvement, current
stable-session latency reduction or1/2/3–5Mbit/s target is claimed. No selected
optimization was implemented.
