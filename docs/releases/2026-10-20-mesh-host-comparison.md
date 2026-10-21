# Same transport / different host — bounded Linux comparison,20.10.2026

**Result: REPEATABLE_B_ADVANTAGE_ON_ISOLATED_LINUX_HARNESS.** RU is faster in both
paired download comparisons; host-only causal attribution remains **INCONCLUSIVE**
because the four fresh rooms select different SFUs. This is not Android acceptance,
a production migration, or proof of a faulty provider. Pacing stays closed:
NOT_ACCEPTED applies to the tested fixed4M candidate, not all congestion control.

## SECOND_HOST_AVAILABLE

A = authorized NL186.246.45.246, existing Amsterdam Family gateway host.
B = authorized RU185.251.89.19, existing Family control/API/gateway host; **city
unverified**, not called Saint Petersburg.186.246.51.201 is excluded and untouched.
Authority comes from repository host scope and this explicit bounded-test request,
not merely working SSH. No third host, purchase or new cloud resource.

| Read-only preflight18:27–18:28UTC | NL A | RU B |
|---|---:|---:|
| Architecture / logical CPUs |x86_64 /1|x86_64 /2|
| Available memory |421224KiB|925320KiB|
| Free project disk |10.94GB|8.10GB|
| CPU busy / steal,1s sample |21% /1%|58.97% /0%|

Not exclusive machines. Same separate nobody test process on each, bounded by
50% of one CPU,220MiB memory/no swap,96 tasks and510s runtime; no production
services/firewall/routes altered. Loopback fixture only, no public proxy listener.
Actual authorized media connectivity and exact transfers were exercised on both.

## EXACT_SHARED_IMPLEMENTATION

Production gateway remains
`734b6ca6eb42be0367b703b657be87c624f3500ae408bbd771309ffaeb86128e`;
do not confuse it with older272bbc3f… or the separate test binary.
Sealed current source inventory:
`faf60996252fdb09ddf4890dbe82c04d5a0212418b488d6459003a3898ea720b`.
Same test executable on both hosts **and the client**:
`6496b6666f316b23426ecc86a449388535907e644bcda3d346f011c592779411`.
Workload/observability-only patch:
`20f2922a01be544c60483c384362eb561bf9f86e439b709f140d9b0584f619dd`.

Go1.26.1 linux/amd64, `-p=1 -trimpath -buildvcs=false -tags=fc_perf_diagnostic`;
pion/interceptor0.1.45, webrtc/v4.2.15 unchanged. All product transport source files
remain byte-identical except **read-only candidate metadata projection** in
`telemost/performance.go`. Existing CLI Mux probe gets a finite synthetic workload;
no new mux, packetization, pacing, retry/window/receiver algorithm or dependency.
`OFF/Q0`, A0, LEGACY64/65536 both directions, VP8/RTP/UDP4 throughout. No Q1
completion context or pacer is enabled. Same writes/backpressure on A and B.

## TEST_STACK_AND_EXCLUDED_PRODUCT_LAYERS

Existing `cmd/telemost-binary` live harness:
Linux client → Mux64 → Family TLS → ReliableStream → VP8/RTP → Telemost SFU →
matching server peer → bounded synthetic loopback TCP fixture. No Android/TUN,
mobile radio, product startup/bootstrap/admission or external HTTP/HTTPS endpoint.
These rates must **not** be compared directly to earlier phone0.5–0.8Mbit/s as
proof of product improvement. No public benchmark relay, owner-only handoff or API.

Existing `pilot.telemost_family_fixture` enrolls disposable identities into a new
temporary test ProductStore and CA, untrusted by production. No production private
keys, authority/grants or provider OAuth copied to B. OAuth stays on NL; each phase
gets a fresh isolated room, never the owner or bootstrap room. Test keys/room URLs
stay in private files/environment, not argv/public evidence. No production renewal
or security floor changes. Authentication succeeded independently on all8 peers.

Client stays on the same Linux/Wi-Fi machine. Main-table route/rule readbacks to
the actual media endpoints use `wlp0s20f3`, not TUN/WG. A1 publisher ICE nominated
local docker bridge172.17.0.1; its route also uses that Wi-Fi, with no VPN policy
rule. Later local nominees use192.168.129.37. ICE source/path selection is a
recorded difference; no network settings were changed to force a prettier result.

## GOODPUT_LATENCY_FAILURES

Order A1→B1→B2→A2, independent rooms, same binary/configuration. Each phase:
64KiB echo control → single4MiB download → parallel2×2MiB →64KiB reverse upload
with32-byte digest acknowledgement. Echo includes **both** directions. Every body
is byte-compared and SHA256-checked; no body failure omitted or live phase repeated.

| Phase | Single4MiB time / Mbit/s | Parallel common time / aggregate Mbit/s |64KiB echo full |64KiB upload+ack full | Complete |
|---|---|---|---:|---:|---|
|A1 NL|60.484965971s /0.554757|37.220728633s /0.901499|4.430892680s|1.525804718s|5/5|
|B1 RU|51.447866202s /0.652203|30.449734698s /1.101961|4.485578489s|3.282623623s|5/5|
|B2 RU|45.020820806s /0.745309|27.910271667s /1.202225|4.290256017s|1.706177790s|5/5|
|A2 NL|56.568747980s /0.593162|33.369854363s /1.005531|5.619669410s|1.648084651s|5/5|

| Pair | B/A single | B/A aggregate | B/A echo latency | B/A reverse control latency |
|---|---:|---:|---:|---:|
|A1/B1|+17.57%|+22.24%|+1.23%|+115.14%|
|B2/A2|+25.65%|+19.56%|−23.66%|+3.52%|

No blanket latency improvement: B1 reverse-control completion is distinctly slower.
These64KiB application controls are **not ping RTT or one-way latency**. No subtraction
of clocks on different machines. Per-request and common parallel intervals use the
same client process monotonic clock, not rounded speeds. Client media setup is
1.972/2.243/1.949/2.399s; Family setup separately includes the same fixed3s settle.
Single first-byte time2.231/2.313/1.975/1.829s, already included in full durations.
Full per-request open/body timestamps and both parallel results are in evidence.

Real Mux streams in each phase: control1, single3, concurrent5/7, reverse9; named
parallel request↔ID mapping retained, not inferred from HTTP request count.
Every Mux snapshot/error bracket on both sides is0→0; no counter reset. No observed
in-load reconnect, all20 synthetic checks exact. Four server CLIs exit1 with
`io: read/write on closed pipe` during controlled teardown **after** successful
requests; these exit codes are retained, not disguised as four clean process exits
or misclassified as four failed downloads. All client CLIs exit0.

Payload: fixed SHA256(counter) bytes,4MiB SHA
`70d1d2a245e130fe843df98783941d7f770618d4a70489bc7e9ca518089467f8`;
zlib size/input ratio1.0003066. No compressible repeating zero pattern.
Budget **34341092 bytes =32.750217MiB /64MiB**, including echo both directions,
reverse uploads, fixture request headers and digest acknowledgements; no live
retry/smoke beyond the four phases. SSH/artifact/log bytes are administrative
overhead, not useful application data. RTP/RS retransmissions are separately
accounted overhead, not claimed absent or included in useful goodput.

## ACTUAL_MEDIA_PATH

| Phase | Actual remote SFU IPv4, all four PC legs | Client pub/sub ICE RTT last sample | Server pub/sub ICE RTT last sample |
|---|---|---:|---:|
|A1|37.140.143.183|79.25 /51.13ms|40.71 /42.59ms|
|B1|5.255.254.22|422.95 /350.00ms|11.80 /11.62ms|
|B2|5.255.254.131|167.79 /80.95ms|12.26 /12.13ms|
|A2|37.9.73.8|86.12 /157.07ms|61.31 /49.47ms|

Nominated candidate IDs, endpoints/ports and observation timestamps preserved from
the latest **pre-close** snapshots on both peers. UDP4 host candidates on each leg;
no TURN relay candidate observed. This is still SFU-mediated, **not peer-to-peer**.
ICE RTT measures each peer↔SFU segment, not complete NL/RU↔client Family latency.
Result applies to **placement plus assigned media route**, not a provider indictment.

## RESOURCE_CONFOUNDERS

| Phase | Server RS snapshot interval | Retry bytes delta | RS ready-full / head-unconfirmed-later-SACKed | Client RTP discontinuity events | Server max RSS |
|---|---:|---:|---:|---:|---:|
|A1|104.716s|1782028|84.63% /38.85%|49|41592KiB|
|B1|89.012s|1523832|82.19% /34.19%|42|51032KiB|
|B2|75.080s|955152|85.36% /30.85%|32|50628KiB|
|A2|94.798s|1531224|87.39% /36.54%|45|41896KiB|

Counter differences use each endpoint's own first/last snapshot interval, including
close tail, **not request-local** counters. Overlapping Mux/RS waits are not summed.
Server single stream3 lifetime zero-credit-ready waits34.757/35.120/30.884/40.682s;
not divided by an unrelated request duration. Parallel stream/retired counters are
retained where sampled; late-retiring streams can be absent, not assumed zero.

Lower RU retry bytes/discontinuities support a path-sensitive effect, not a proven
causal packet-loss location. Discontinuity events are not lost-packet/frame totals.
No exhaustive old_rtp/VP8 discard accounting. B1/B2 server bounded evidence ring
omits79/91 entries; this means diagnostic truncation, not79/91 lost packets.

Whole-host CPU busy NL24.99/24.55%, RU28.34/32.03% (different CPU counts);
steal0.49/0.445% NL,0.246/0.538% RU. Equal test cgroup quotas throttle by
8.869/348.225/337.001/0ms across A1/B1/B2/A2, preserved as a confounder, not hidden.
No memory limit/OOM events. Raw whole-interface byte deltas, process CPU/RSS,
schedstat and host load are saved. Other traffic cannot be cleanly separated from
test/admin bytes; no claim of identical background load or exclusive machines.

## PRODUCTION_UNCHANGED

Owner remains beta96-bootstrap/A0, APK
`07a90f03269e1df683289bc1fbe7fa7e88647c5629f71db1f784d6566aa9228d`,
native `66a9d18d04ff71100df0144228db05decb970aea71b6d277ec321b1c6c240c63`,
UID10283/PID30172/VPN342. Gateway734b6ca6… retains1011 and Mux compatibility;
protected settings OFF/Q0, LEGACY64,128 OFF, counter export OFF. No owner reconnect,
control request, APK, build/install of production, directory/API/firewall mutation,
country-of-exit change, new production authorization or push.

Preflight discovered a **pre-task** process/credential change since the earlier
17:58 receipt: PID4079583→4126720, current invocationc24eee95… started18:07:08UTC,
same binary; new leaf expiry22:06:56UTC. Its cause is not established by this test.
We did not restore stale credentials or claim the old PID was still live.
Current PID/invocation/profile hash/flags stay equal before, through and after
the experiment. Final Android/gateway readback18:49:05UTC matches its task-start
readback, including APK/native and current credential hash.

All8 peer summaries show publisher/subscriber **closed**. Transient test units,
owned workers/stages absent; room/profile files and temporary test identities/DB
removed; no background collector or wait. Standard close leaves the fresh rooms.
The existing provider abstraction has no conference-delete method: provider-side
room metadata deletion/retention is **not verified**. No unbounded authenticated
test peer remains that can serve traffic in those rooms.

## HOST_OR_PATH_EFFECT / NEXT_DECISION

Repeatable **bounded B download advantage**, not universal evidence or a2× promise.
Host-only attribution and Android benefit remain unproven; the shared RS still
spends much of its observed interval ready/full. This does not establish Telemost
as the bottleneck or a technology ceiling. No software tuning follows this result.

Next prepared decision: a **separate product Android comparison** on the same96/A0,
LEGACY64/OFF baseline, with explicit approved gateway authorization/selection and
return procedure first. Do not copy production private keys, change production
directory or route owner traffic automatically. Its field acceptance is NOT_RUN;
no third placement, new profiles, purchases or migration in this task.

## Artifacts and validation

`state-client-build/host-compare-20261020/`: build/source inventory and harness-only
patch, A1/B1/B2/A2 raw JSONL/resources/results/cleanup, `summary.json`, `result.json`,
`verification.json`, pre/postflight and immutable failed preparation receipts.
Repro kit `host-compare-kit.tar.gz`, SHA256
`7febd1212d51126703cf6eb03432df528c2cb32df7b60951a1a7870f2c91f0c3`.
Contains source/binary/operator scripts, **no runtime/production credentials**;
requires the repository's existing isolated issuer and pinned build environment.
[Operator/workload scope](../../tests/fixtures/host_compare/README.md) and
[sanitized evidence](2026-10-20-mesh-host-comparison.evidence.json).

Focused CLI/fixture race checks PASS outside sandbox; initial local socket denial
preserved. Initial issuer venv lacked pydantic; repaired using the existing complete
admission-test environment, same issuer/no upgrade. No room or measured byte was
created by that failed preparation. Unchanged transport/recovery tests reused;
byte-exact body/hash, source pins, zero Mux errors and owned-process cleanup verified.
