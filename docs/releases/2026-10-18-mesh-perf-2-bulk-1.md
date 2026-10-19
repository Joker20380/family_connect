# MESH-PERF-2 — explicit-endpoint bulk baseline

18 October 2026, UTC. **PASS for the bounded performance measurement**, not a
transport fix, byte-exact acceptance, sustained capacity guarantee or root-cause closure.
Continuation of [physical-1](2026-10-18-mesh-perf-2-physical-1.md) and the
[PERF-2 run card](2026-10-18-mesh-perf-2.md). The explicit endpoint authorization
supersedes their missing-origin performance gate; it does not supply an independent
origin digest or authorize runtime changes. Original reports/evidence are preserved.

[Sanitized measurement evidence](2026-10-18-mesh-perf-2-bulk-1-evidence.json), SHA256:
`f60ff8ee169f015baa3e0c757caa8202093a3c485ca9aa9d37a5a9e8b8fbe05d`.

## RESULTS

| Required status | Result and exact scope |
|---|---|
| DOWNLOAD_BASELINE | **PASS** — 64KiB contract check, three complete2MiB singles and two complete concurrent2MiB responses |
| UPLOAD_ESTIMATE | **PASS, estimate only** — 64KiB check and three1MiB synthetic POSTs; client counts and full-request timing |
| UPLOAD_SERVER_RECEIPT | **PARTIAL** — `cf-meta-upload-bytes` matches every intended/client count; no digest or independently verified server reader implementation |
| SERVER_RECEIVED_BYTES | **NOT_INDEPENDENTLY_VERIFIED**; server-reported counts are retained, not suppressed |
| LOADED_RESPONSE_LATENCY | **PASS, application timing** —3 nominal-idle,21 download-overlapping,9 upload-overlapping probes; no p99 claim |
| BYTE_EXACT_ACCEPTANCE | **NOT_ESTABLISHED** — observed download hashes are not independent source hashes; count-header read-versus-echo semantics unverified |
| SMALL_RECORD_HYPOTHESIS | **INCONCLUSIVE** — occupied8-slot window observed under bulk; actual DATA lengths/flight bytes absent |
| RUNTIME_UNCHANGED | **PASS** — accepted APK/native/gateway, connection, security/configuration generations preserved |

## EXACT_BASELINE_AND_ROUTE

- Local HEAD remains `7656f2c65ea2928b71a928c12ee65a2f47f8ac4f`, not a claim that
  main contains installed UI84 source. Existing dirty work was preserved.
- Android Friends code84, `0.1.18-research84-ui60-4-batch1`, APK SHA256
  `697f9c244b67f75e7e3e612dbcd91a48891d32ee77e23fd9bce173a5f049233f`;
  installed restricted native SHA256
  `dd722eada0da7c890a8d71a72099cba5d0bbac1ce73377bbdbc8e7b85d820c23`.
  Both freshly checked; final APK unchanged. Existing app process14226 retained.
- NL process2094910, invocation`e9cedbb2fb9d45a2ba0aefd9f211bcb6`, NRestarts0;
  loaded SHA256 `4b722d2d7f2159b96953e27777494bf596768f860ee8da7e634fb1100b08fab7`.
- Gateway profile SHA256
  `64870fac58ec25d593837f0cfe7ecc6b2b58411adb03da396122f7c7b2f4bf8d`;
  equal RU/NL directory SHA256
  `4cbab5fe8a6856310b501380b45952acdd14d7488e41ae87cb5bdf1b32e5cf7b`.
  Authority17/CRL27120, RU authority/admission/checkpoint hashes unchanged.
- Preflight12:27:05–07, post-measurement server readback12:36:10–13. Leaf/CRL
  valid until18 October14:49:14, CA/authority until19 October09:33:41. Initial
  limiting headroom8528.9s exceeds900s budget plus600s reserve. No rotation observed.
- Same **cellular LTE** underlay, owner VPN `tun1`, DNS10.79.0.1. Shell UID2000
  is inside the actual VPN UID range; its ordinary route uses the TUN. This is
  existing Android curl7.73.0/BoringSSL through the installed VPN, **not** a native
  Telemost CLI, browser-only proof or laptop throughput result.
- Each of the eight main bulk requests has15–30 matching destination/time socket
  samples in the accepted MESH PID. Probe bodies confirm NL egress; topology and
  thermal status0 were rechecked between cells and finally. No network switch.
  Correlation is observational, not a nonce-level encrypted packet trace. The pilot
  socket sampler returned no records due to a collector bug; this was corrected
  before the main matrix, not concealed or confused with missing MESH sockets.

The earlier [28 September native single-TCP result](2026-09-28-webrtc-eu4-single-tcp.ru.md)
reported10,485,760 Cloudflare bytes/53.433s (~1.570Mbit/s), on a different native
test path. Its observed SHA256 is **not** an expected hash for this experiment and
its throughput is not merged with current TUN results.

## ENDPOINT_CONTRACT_AND_METHOD

Explicitly authorized GET `https://speed.cloudflare.com/__down?bytes=N` and POST
`https://speed.cloudflare.com/__up`; only locally prepared random synthetic POST
bytes. No credentials, diagnostics, identity or user files were uploaded.

Current [Cloudflare speedtest client](https://github.com/cloudflare/speedtest)
documents these endpoints. Inspected tree`a54f0c94bd40dc04400926777e20fd01dacb64ae`,
README blob`f87605f0716321165e285c630b2483bc7dfec394`, BandwidthEngine blob
`9c7dd37d816c9a52ba8225e737c8c370ed7f06f7`, LoadNetworkEngine blob
`828cfc7b9c93bb469f1fd31d33b20e33b18ed965`. The client checks HTTP success and
consumes response text; upload-rate calculation uses configured bytes/timing,
not a digest validator. This is not an audit of the deployed server reader.
No SDK was invoked, no result telemetry POST or token supplied, no429 retries.

Every request uses IPv4, **HTTP/1.1**, a fresh curl process/connection, normal TLS
verification, `Accept-Encoding: identity`, `Cache-Control: no-cache`, a unique
public test query, no proxy, redirects, retries, decompression or speed limiter.
Download responses: HTTP200, correct Content-Length, `application/octet-stream`,
`Cache-Control: no-store, no-transform`, no Content-Encoding/Age/cache-HIT header.
Curl has no local response cache. Bodies are read continuously into phone-local
files; byte count and SHA256 are computed **on the phone after timing ends**.
ADB carries compact metadata, not each data block. Upload files were generated
before the campaign; the source is a prepared1MiB random file and its64KiB prefix.

Campaign12:29:19.996497→12:35:02.826708: **342.830s**, including the pilot/main
inspection gap. Request cap150s (stricter retained limit), connect15s; probes30s.
Total application response+client-upload payload **13,769,589B**, below32MiB;
43 HTTP requests, all complete200, curl exit0/TLS verify0. No403/429, retry,
timeout, partial response or hidden failed network run. Raw collector failures
are separately retained below. No second120-probe series was run.

Primary download metric: `actual_response_body_bytes * 8 / time_total / 1_000_000`.
It **includes DNS/TCP/TLS setup and TTFB**. All singles use the same fresh-HTTPS /
already-warm-MESH method. No body-only speed or transport-wire speed is claimed.

## DOWNLOAD_BASELINE

| Request | Requested / received bytes | HTTP / new connections | TTFB s | Full request s | Application Mbit/s |
|---|---:|---|---:|---:|---:|
| 64KiB contract check |65,536 /65,536 |200 /1 |2.992872 |4.001270 |0.131030 |
| Single1 |2,097,152 /2,097,152 |200 /1 |2.449394 |31.309618 |**0.535849** |
| Single2 |2,097,152 /2,097,152 |200 /1 |3.615077 |25.335961 |**0.662190** |
| Single3 |2,097,152 /2,097,152 |200 /1 |0.980859 |26.808378 |**0.625820** |
| Parallel A |2,097,152 /2,097,152 |200 /1 |1.047640 |29.812242 |0.562763 individually |
| Parallel B |2,097,152 /2,097,152 |200 /1 |0.872793 |29.364023 |0.571353 individually |

Single-request median **0.625820Mbit/s**, range0.535849–0.662190. Total single payload
divided by sum of their request times: **0.603107Mbit/s**, excluding inter-run gaps;
not a whole-campaign rate. The small cold-DNS contract check is excluded.

Parallel: **4,194,304B /29.83s common phone-clock wall interval =1.124855Mbit/s**.
Both requests overlap for29.37s; two distinct client local ports, HTTP/1.1 and
`num_connects=1` per curl establish two TCP connections, not merely two HTTP calls.
The denominator uses earliest phone `/proc/uptime` start to latest finish (10ms
resolution), before hashing, not the sum of rates or two disjoint intervals.
This one aggregate result is~1.80× the single median, not a repeatability guarantee.

Observed64KiB response SHA256:
`34dd6758c2908cf5be0e411173f61877f8faf2dcdcfed135b5a5fa90577447bc`.
All five2MiB responses have observed SHA256:
`c72cdb288c75ffdf478ce2e5b855b428491f9d9298deca11457e14c2e2c41419`.
Identical generated bodies do not constitute an independently known source digest
or prove a cache hit. No historical hash was used as an acceptance oracle.

## UPLOAD_ESTIMATE_AND_RECEIPT

| Request | Intended / curl size_upload | HTTP / response body | Full request s | Upload estimate Mbit/s | cf-meta-upload-bytes |
|---|---:|---|---:|---:|---:|
| 64KiB contract check |65,536 /65,536 |200 /0B |2.576021 |0.203526 |65,536 |
| Upload1 |1,048,576 /1,048,576 |200 /0B |20.041888 |**0.418554** |1,048,576 |
| Upload2 |1,048,576 /1,048,576 |200 /0B |17.684062 |**0.474360** |1,048,576 |
| Upload3 |1,048,576 /1,048,576 |200 /0B |15.378600 |**0.545473** |1,048,576 |

Median estimate0.474360Mbit/s; numerator is curl's application upload count, not
TCP send/write acceptance promoted to server delivery. All main verbose records
place `We are completely uploaded and fine` **before** the final HTTP200. No early
final-response truncation is observed. Upload curl TTFB is retained but not used
as the final-response/read-completion timestamp; full-request timing is used.

The endpoint does return a **server-reported count header**, even though its body
is empty. This refines the initial pilot message about a missing receipt. Header
counts match intended/client bytes; no received digest is returned. Without a
verified server implementation/contract distinguishing read count from declared
Content-Length, retain **SERVER_RECEIVED_BYTES=NOT_INDEPENDENTLY_VERIFIED** and
**UPLOAD_ESTIMATE**, not byte-exact upload acceptance. This uncertainty did not
block or invalidate download/response measurements.

## LOADED_RESPONSE_LATENCY

Same short `https://www.cloudflare.com/cdn-cgi/trace` probe/method as physical-1:
fresh HTTP/1.1 TCP/TLS, full body, TLS verification, NL egress, no reuse. At most
one probe in flight; nominal5s minimum cadence (observed minimum4.999966s at
recorded command boundaries). Tiny bodies capped4KiB.
Values below are **full HTTPS application response times**, not network/media RTT.
Nominal idle means no harness bulk; background phone traffic was not excluded.

| Condition | n | Full response seconds: min / median / max | Fully / partially overlapping bulk | Failures/timeouts |
|---|---:|---|---:|---:|
| Before bulk |3 |1.754557 /2.169754 /3.001376 |0 /0 |0 /0 |
| During download |21 |1.024010 /2.379294 /4.287828 |19 /2 |0 /0 |
| During upload |9 |1.021458 /2.762603 /3.769312 |7 /2 |0 /0 |

No stable p99 or population latency-inflation claim from these small, unpaired
samples. No unfinished probe was dropped. Four probes extend beyond their bulk
request: loaded6 overlap1.09s, loaded11 overlap0.16s, loaded27 overlap2.57s,
loaded30 overlap0.33s; they remain visible rather than becoming fake full-load samples.
All individual full-response/TTFB values and overlap durations are in evidence.

Idle values (s):3.001376,2.169754,1.754557.
Download-overlapping (s):4.287828,3.245960,2.456071,2.939691,1.940045,1.703391,
1.024010,3.091606,2.053623,1.851875,1.831444,3.266514,2.379294,1.683700,2.098560,
1.535375,2.605419,3.061105,2.388637,2.685649,1.890502.
Upload-overlapping (s):3.745915,3.769312,2.805207,2.762603,2.781646,2.623471,
1.948988,2.357392,1.021458.

## INTERNAL_METRICS_AND_SMALL_RECORD_HYPOTHESIS

208 existing NL CARRIER_ACTIVITY records, one same owner SessionTrace tag;2s
snapshots with last64 boundaries.10,269 unique boundaries survive,50,935 missing
indexes between first/last retained points. These are sampled histories, not a
continuous window-stall/ACK/retransmission histogram. No new runtime instrumentation.

| Cell | Full8 slots / samples | Cumulative send_base advance* | Retained retransmit attempts** | NL incoming RTP gap delta* | Assembly expiry delta* | Mean NL / Android CPU, % one core |
|---|---:|---:|---:|---:|---:|---:|
| Single1 |14 /16 |325 |46 |0 |0 |6.40 /41.62 |
| Single2 |10 /13 |321 |26 |1 |0 |6.48 /41.96 |
| Single3 |13 /13 |299 |32 |0 |0 |6.58 /40.82 |
| Parallel |15 /15 |421 |34 |1 |0 |6.69 /42.59 |
| Upload1 |1 /10 |129 |0 |7 |2 |5.47 /42.47 |
| Upload2 |2 /9 |122 |0 |7 |3 |6.12 /40.28 |
| Upload3 |1 /8 |126 |0 |6 |4 |6.22 /40.62 |

\* First/last snapshots strictly inside each cell: covered30/24/24/28/17.999/16/14s
respectively; includes probe/background traffic, omits edges. Parallel counted once.
\** Retained unique attempts only, a lower bound, not a retry percentage. These are
**gateway-send** metrics; upload's low gateway retries/window occupancy say nothing
about the unseen Android sender's retry/occupancy distribution.

- **VERIFIED window pressure:**37/42 single-download snapshots and15/15 parallel
  snapshots occupy all8 sequence slots (`send_next-send_base`). Most have8 pending
  segments. This is stronger than the earlier unloaded0/97 result, but neither
  continuous stall duration nor proof that record size causes the pressure.
- ACK pairing requires complete boundary-index spans and no retransmission. Only
  seven download first-covering samples survive (164–572ms), two cumulative
  samples (164/587ms); parallel has **none**, not zero ACK latency. Upload gateway
  reverse/control samples are a different direction. Do not infer bulk RTT percentiles.
- Matching queued→RTP-written pairs:331 across singles,134 parallel; single-cell
  medians3/1/0ms, parallel2.5ms, maxima20/11/10/16ms. Timing starts **after enqueue**,
  omitting application/send-gate/window waiting;0ms has millisecond resolution.
  Queue depth distribution is absent: queued/written identities are not counts.
- Incoming NL upload intervals show20 RTP gap events and9 expired assemblies in
  total; these are real observations, not loss percentage or a proven throughput
  cause. Download receiver is Android, so NL incoming counters cannot certify its
  receive path. No retained frame_discard boundary; no complete discard-rate claim.
- NL process means5.47–6.69% one core; whole Android Friends40.28–42.59%, including
  UI/chat/background. Peak sampled RSS≤45.35MiB NL/161.79MiB Android for these cells.
  No whole-process CPU saturation demonstrated; worker/lock/scheduler limits remain
  unmeasured. Existing tracing/sampler perturbation was not independently A/B tested.
- Actual DATA-size histogram, true in-flight DATA bytes, continuous window-stall
  residence and full RTP/SRTP wire byte rates: **NOT_OBSERVABLE_WITH_CURRENT_BUILD**.
  Carrier counter bytes include framing/control/retries, not useful application bytes.

**SMALL_RECORD_HYPOTHESIS=INCONCLUSIVE.** The384B/8slots/80ms synthetic model is
not a measured Android distribution. Full windows also occur with large records,
loss recovery or delayed cumulative consumption. No window/pacing change is justified
from occupancy alone. Parallel aggregate1.125Mbit/s shows this measured path carried
more than0.3Mbit/s of useful traffic; it does not establish an invariant carrier
ceiling or isolate batching from per-TCP behavior/adaptation/temporal variation.

## NEXT_ENGINEERING_ACTION

One targeted next experiment: an **isolated, separately authorized NL-side
diagnostic candidate** from the retained gateway source, adding only bounded
DATA-length buckets and actual outstanding-byte accounting alongside the existing
SessionTrace ACK/Flow observations for the same1/2-stream workload. This distinguishes
small-record slot use from large-record/recovery/consumption stalls; no UI84 rebuild,
wire change, window increase or production deployment is part of this task.
Require byte-exact local tests and a measured tracing-overhead guard before any
physical comparison. No optimization is selected or implemented here.

## SAFETY_AND_EVIDENCE

Bulk ended12:35:02. Subsequent work only read journals/state and analyzed evidence.
The initial broad journal fetch hit a45s collector timeout, **not** a failed bulk
request. On continuation, existing final readback was reused and five bounded90s
filtered reads recovered208 records; no network test was replayed. Preflight field/
node-location parser corrections and the empty pilot sampler are retained as
collector limitations. All main bulk route correlations succeeded.

Private data/tools/raw results: Git-ignored
`state-client-build/mesh-perf-2-bulk-1/private/`, directory0700/files0600.
Public evidence excludes raw device/session IDs, credential contents, echo IP
bodies and raw socket records.88 test-owned phone files were removed only after
matching body/payload hashes; app data/floors untouched. Final read-only check:
no owned sampler process left, same gateway active/NRestarts0, owner VPN present.

Independent local evidence checks PASS:131 retained-file hashes,6 historical
report/evidence hashes,43 complete HTTP records, download/parallel arithmetic,
payload/time caps, no overlapping probes, all8 main bulk route correlations and
phone cleanup receipt. Public evidence checked against private device/session IDs.
`git diff --check` PASS. These are evidence checks, not repeated physical requests.

No recovery/signing/vault/apply, service reset/restart/reload, deployment, APK/native
build/install, transport/MTU/DNS/IPv6/admission/identity/security-floor change, fault
injection, deliberate disconnect, commit/push/release. Normal renewal not paused;
unchanged generation across measurements, no automatic rotation observed. The
existing13:19:14 leaf/CRL renewal threshold,14:49:14 expiry and operator target
before19 October02:33:41UTC remain separate lifecycle obligations. External alerts,
IPv6, all-activated admission and UI84 source consolidation remain unresolved.
