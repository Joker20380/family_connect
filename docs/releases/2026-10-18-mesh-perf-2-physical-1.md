# MESH-PERF-2 — UI84 physical continuation / PARTIAL

18 October 2026, UTC. Linked continuation of [PERF-2](2026-10-18-mesh-perf-2.md),
[root-cause investigation](2026-10-18-mesh-perf-rootcause-1.md) and
[APPLY-1](2026-10-18-mesh-nl-recovery-apply-1.md). Their uncommitted reports/evidence
were read locally and preserved, not replaced from GitHub. Recovery and architectural
audit were not restarted. [Sanitized evidence](2026-10-18-mesh-perf-2-physical-1-evidence.json)
SHA256 `0ce3f815965ed1db21d28d5a4e84ad2ea481c43ea7c22308bc893e78289a323c`.

## FINAL_RESULT

| Required result | Status |
|---|---|
| EXACT_PHYSICAL_BASELINE | **PARTIAL** — unchanged real pair, functional path and nominal-idle timings measured; sustained bulk absent |
| MESH_ROUTE_CONFIRMED | **PASS, process-correlated control request** — phone VPN route, NL egress and matching origin socket in the accepted MESH PID; not egress-IP-only inference |
| UI84_DNS_HTTPS | **PASS** — two functional checks and120 complete, certificate-verified HTTP200 responses |
| APPLICATION_GOODPUT | **BLOCKED / NOT_RUN** — existing bulk fixture and discard-upload contracts were not supplied/verified in the prepared run card |
| IDLE_AND_LOADED_LATENCY | **PARTIAL** —120 nominal-idle full-HTTPS timings; loaded latency NOT_RUN |
| SMALL_RECORD_HYPOTHESIS | **INCONCLUSIVE** — no DATA-length histogram and no sustained bulk window observation; light samples do not disprove it |
| MISSING_OBSERVABILITY | Exact current-build/public-interface and access limits below; no new build requested |
| NEXT_ENGINEERING_ACTION | Verify an existing approved bulk origin contract, then execute the prepared unchanged-pair single-stream download/upload cell with existing trace |
| FINAL_RESULT | **PARTIAL**, not a solved throughput problem or completed optimization |

## EXACT_PHYSICAL_BASELINE

Read-only phone preflight11:36:44; RU/NL11:39:12–14; final server readback11:56:10–11.
Same locally attached owner phone as APPLY-1, compared privately by ADB identity;
no serial/Device Identity/credentials published. Access is **cellular LTE**, unchanged
underlay network throughout the probes. Existing phone process14226 remains in use.

| Component | Exact identity / state |
|---|---|
| Repository HEAD, not deployed-build equivalence | `7656f2c65ea2928b71a928c12ee65a2f47f8ac4f`; prior dirty work preserved |
| Installed Friends UI84 | code84, `0.1.18-research84-ui60-4-batch1` |
| Installed APK SHA256 | `697f9c244b67f75e7e3e612dbcd91a48891d32ee77e23fd9bce173a5f049233f` |
| Installed restricted native file SHA256 | `dd722eada0da7c890a8d71a72099cba5d0bbac1ce73377bbdbc8e7b85d820c23`; freshly read from current package nativeLibraryDir, not just inferred from main |
| Other native bytes | Same exact APK that PERF-2 independently checked against all12 retained libraries; no APK/native replacement |
| Loaded NL executable SHA256 | `4b722d2d7f2159b96953e27777494bf596768f860ee8da7e634fb1100b08fab7` |
| NL runtime | PID2094910, invocation`e9cedbb2fb9d45a2ba0aefd9f211bcb6`, active/running, NRestarts0; unchanged at final readback |
| Protected gateway profile SHA256 | `64870fac58ec25d593837f0cfe7ecc6b2b58411adb03da396122f7c7b2f4bf8d` |
| Authority/checkpoint |17; committed plan`4ed8dd3c86f5dd2c6c1124dadf175a6269dabc390561d85b22519848049a14cf`, unchanged |
| RU/NL directory SHA256 | `4cbab5fe8a6856310b501380b45952acdd14d7488e41ae87cb5bdf1b32e5cf7b`, equal before/after |
| Leaf and CRL expiry |18 October14:49:14; CRL27120; signature/current validity rechecked |
| CA/authority expiry |19 October09:33:41; no change or extension |
| Request client | Existing Android curl7.73.0, BoringSSL; no helper/app installation |

Initial limiting credential headroom11399.5s exceeds the60min campaign plus10min
reserve. Same directory bytes retain APPLY-1's validated runtime binding and expiry;
new import READY ACKs from that task are context, not this task's traffic acceptance.
No bundle apply, signer, vault, controller/renewal invocation, reset/start/reload,
timer pause or gateway replacement. Normal renewal remained active/waiting; its last
recorded automatic trigger was11:43:20. No credential/process generation change was
observed over this measurement interval. Future13:19:14 renewal threshold and
19 October02:33:41 operator target remain unchanged; lifecycle is not declared closed.

## MESH_ROUTE_CONFIRMED

Owner's manual Connect had already created ConnectionService/TcpVpnService around
11:28. No Connect/disconnect tap, UI dump, screen-unlock attempt or UI repair was
performed. Android's actual NetworkAgent is connected VPN over CELLULAR, owned by
the Friends package, interface`tun1`, default IPv4/IPv6 capture routes and existing
DNS`10.79.0.1`. Shell UID2000 is inside its UID range; ordinary `ip route get` uses
`tun1`/`10.79.0.2`. These capture routes are existing configuration, **not IPv6
functionality or a new advertisement**. Requests explicitly use IPv4.

An ordinary GET to the **already implemented app check-IP endpoint**,
`https://www.cloudflare.com/cdn-cgi/trace`, returned the expected NL egress and
complete fields. Egress alone would not distinguish MESH from NL AWG/TCP. Therefore
a second GET was correlated with18 one-second read-only socket/process samples:

- Request11:45:23.612602→11:45:26.708936; full216B HTTP200 response, TLS verify0.
- Origin peer address from curl exactly matches TCP443 sockets owned by the loaded
  **MESH gateway PID2094910** at11:45:25.360607 and11:45:26.359567.
- Phone routing, matching peer/time/process and NL response egress jointly support
  the MESH path, rather than an unrelated direct diagnostic or other NL transport.
- Limit: this is process/socket/time correlation, not an origin nonce logged inside
  the encrypted gateway stream. It does not prove every other device flow's path.
  Requested UI selection was not read from private preferences. Existing SessionTrace
  was observed independently; no fake client export or per-request Mux counter was
  invented. System notification text is redacted and was not used as transport proof.

The same VPN interface/network/underlay tuple was checked every10 latency probes and
at completion. No topology change, deliberate reconnect or network switch occurred.

## UI84_DNS_HTTPS

Requests use ordinary routing, valid public certificate verification, IPv4 HTTP/1.1,
no proxy/redirect/compression, no retries;4KiB response cap,15s connect/30s total cap.
This endpoint is present in the accepted `FriendsActivity.checkIp`; it was **not**
silently promoted to a bulk download/upload service.

| Probe | UTC start | DNS time | TLS complete from start | Full-body time | Payload / result |
|---|---|---:|---:|---:|---|
| Initial functional check |11:42:09.709292 |1672.759ms |3705.712ms |3974.997ms |211B, HTTP200, complete body, NL egress |
| Socket-correlated route check |11:45:23.612602 |1.578ms |2104.766ms |3064.733ms |216B, HTTP200, complete body, NL egress |

Initial body's SHA256:
`fe7393d97207b52ae0a505f60ec5b6b16b2ca2795b3a658aacc0e00c44bf209f`;
correlated body:
`0d8dca6a986cc8d22c28a20de86fba339bb9204db207f421b323c4ab217abb81`.
These hash **received dynamic echo bodies**, not a fixed throughput fixture.
DNS resolution is demonstrated by the initial ordinary hostname request through
the captured VPN resolver path and subsequent TLS/HTTP success. Later1–5ms lookup
times are cache-warm observations, not repeated uncached DNS round trips.

All120 subsequent latency probes also completed HTTP200, TLS verify0, expected
body fields, matching curl/body byte count and NL egress. No failed HTTP requests,
timeouts or partial bodies were dropped. Initial probes are separate from the
120-probe latency set; they are not mixed into its percentiles.

## APPLICATION_GOODPUT

| Workload | Result |
|---|---|
| One-stream sustained download | NOT_RUN |
| One-stream sustained upload | NOT_RUN |
| Four-stream download | NOT_RUN |
| Loaded latency during those transfers | NOT_RUN |

**Specific missing prerequisite, not a measurement-instrumentation excuse:** PERF-2's
bounded run card explicitly says that no existing origin/fixture/receipt contract
was verified. No download URL with fixed1MiB non-compressible bytes/SHA256, nor
authorized discard-only upload URL with byte/hash acknowledgment, is supplied there
or in the current task. Targeted inspection found the existing short check-IP
endpoint, not a bulk contract. An arbitrary speed-test API, APK download, new origin
or POST endpoint was not substituted; no server/proxy was created.

Total controlled response payload was26059B across122 functional/timing requests;
the120 timing responses account for25632B over251.828s. **Do not divide these paced
tiny transactions into a sustained download-goodput claim.** Upload headers are
not uploaded application payload. There is no measured download/upload Mbit/s value
and no current0.30/1/2Mbit/s acceptance claim. The eventual calculation remains
`payload_bytes * 8 / monotonic_elapsed_seconds / 1_000_000`, using byte-exact
completed application payload and common wall time for concurrent flows.

## IDLE_AND_LOADED_LATENCY

120 sequential, fresh TCP/TLS full-HTTPS requests11:49:14.592963→11:53:26.378133,
no harness bulk load, at most one start/s; slow requests do not create catch-up
concurrency. Actual campaign251.828s, zero failures. Existing MESH session stayed
warm; HTTPS connections were fresh by design. Background application traffic was
not suppressed or proven absent: call this **nominal-idle application timing**,
not a controlled empty-link baseline or pure network RTT.

Nearest-rank percentiles, n=120; tails have limited precision:

| Metric | p50 | p95 | p99 | Maximum |
|---|---:|---:|---:|---:|
| DNS lookup |1.551ms |4.522ms |5.660ms |1088.702ms |
| TLS completion, cumulative from request start |1348.956ms |2172.828ms |2263.346ms |2322.225ms |
| TLS phase after curl connect |1332.722ms |2159.820ms |2227.815ms |2320.132ms |
| Request→first byte after TLS |636.186ms |1305.787ms |1548.264ms |1854.251ms |
| Complete HTTPS response |**1973.500ms** |**3124.664ms** |**3263.099ms** |3313.958ms |

Do not sum independent percentiles. Curl's sub-millisecond-to-few-ms connect phase
on this userspace TUN/proxy is not remote TCP network RTT. DNS/TLS/application
processing, Family/Mux/media progress and origin behavior are included in these
timings. No ICMP assumption, no loaded-vs-idle inflation ratio, no causal attribution
to DPI/provider/credentials. Measured ACK samples below are a different metric.

### Endpoint resources, not saturation proof

- Android Friends process:252 one-second `/proc` samples over251.03s,99.07CPU-s,
  **39.47% of one core** mean; sample p95≈54.55%, maximum≈73.27%. RSS100.83–170.17MiB,
  76–84threads. This includes UI/chat/background, not isolated native-worker CPU.
- NL accepted gateway:18 samples over16.992s around route proof,1.02CPU-s,
  **6.00% of one core** mean, RSS49.16MiB,7threads. Not the same whole interval as
  Android and not a loaded profile. No lock/goroutine/allocation profiling was added.
- Android thermal status0 before, every10 latency requests and after; no override.
  No CPU saturation is demonstrated here; bulk saturation cannot be excluded.
- Existing tracing stays as compiled. Read-only sampling overhead was not A/B
  validated against a≤5% threshold; no claim of universally negligible tracing cost.

## SMALL_RECORD_HYPOTHESIS

**INCONCLUSIVE.** The synthetic384B/eight slots/80ms reproduction remains a model,
not a measured Android record size or current feedback interval. This task obtains
actual gateway-side existing diagnostics, but only during light/background traffic
and the route-check request, **not sustained application download**.

97 CARRIER_ACTIVITY samples11:44:09.348→11:47:21.347 (191.999s), spacing p50=2000ms,
maximum2005ms. One trace session; gateway send-window occupancy is `send_next-send_base`:

| Occupied slots | Sample count |
|---:|---:|
|0 |79 |
|1 |11 |
|2 |3 |
|3 |2 |
|4 |1 |
|6 |1 |
|8 |**0** |

No sampled full-window state in this interval; send_base advanced191, send_next190
and receive_next191. This does **not** rule out sub-2s stalls or window exhaustion
under a different/bulk workload. Observed slot count is not exact bytes in flight.

Existing bounded boundary rings were deduplicated by index.3849 unique records,
3004 missing indexes between first/last retained: neither continuous coverage nor
a complete retransmission distribution. Only pairs with a complete intervening
boundary-index interval were used; retransmitted sends excluded from ACK timing.

| Existing metric, NL side | n | p50 | p95 | p99 / max |
|---|---:|---:|---:|---:|
| reliable_send completion→first covering ACK |46 |354ms |850ms |1033/1033ms |
| completion→cumulative ACK progress |45 |363ms |996ms |1620/1620ms |
| carrier_queued→rtp_written, matching sender/message/fragment |349 |0ms |4ms |6/9ms |

ACK timing includes carrier and remote processing/consumption, not clean network RTT.
Queue timing begins **after enqueue** at millisecond resolution;0ms does not mean
zero delay, and these samples omit pre-enqueue/window/send-gate waits. Small local
post-enqueue waits in light traffic are not evidence against loaded HOL.

At least3 retransmission-send attempts were retained, although sampled head_retries
was always0: a concrete reason not to treat sparse snapshots as complete history.
NL receive counters advance778RTP packets/677VP8 frames/677 completed carrier
messages; cumulative RTP-gap, assembly-expiry, malformed/CRC/conflict counters
do not advance in this interval. Historical totals18RTP gaps/4expired assemblies
are not new losses. No retained frame_discard result; packet-loss percentage and
total retransmission amplification remain unknown.

Carrier payload counters advance136432B sent/76073B received; these include
transport/control/framing and possible retries. They are **not** application goodput
or full RTP/SRTP wire bitrate. No byte-loss budget explaining1.8→0.3Mbit/s is measured.

## MISSING_OBSERVABILITY

| Quantity | Exact boundary |
|---|---|
| DATA payload histogram / exact flight bytes | **NOT_OBSERVABLE_WITH_CURRENT_BUILD** public schema; Fragment.total is fragment count, not byte length; buffered is not flight bytes |
| Continuous window stall time / pre-enqueue wait / queue depth distribution | **NOT_OBSERVABLE_WITH_CURRENT_BUILD** public schema; only2s Flow and bounded post-enqueue pairs |
| Complete ACK/retry history | Partial retained pairs only; explicit index gaps above |
| RTP/SRTP wire bitrate and loss percentage | **NOT_OBSERVABLE_WITH_CURRENT_BUILD** public interface; numeric PerformanceSnapshot not exposed here; packet count is not byte/loss rate |
| Client-direction detailed SessionTrace | Existing owner support export not supplied; use normal UI share, not run-as/raw private files/owner instrumentation |
| Bulk resource saturation / loaded RTT | NOT_MEASURED — no authorized verified bulk endpoint contract |
| Batching on/off | No supported diagnostic switch; no A/B performed or added |

Important collector correction: ordinary `journalctl -o json` substitutes **null**
for long fields.370/600 initial MESSAGE fields were null, hiding delivery records.
A bounded160-entry read with existing `--all` returned97 complete delivery records
(max message14339B, zero JSON decode errors). This fixes observation, **not runtime
logging or protocol**. Initial sparse output was not treated as absent diagnostics.
Likewise a literal `Transports: VPN` count missed `CELLULAR|VPN`; actual NetworkAgent
parsing established the live VPN. Failed/limited collector outputs are retained.

## NEXT_ENGINEERING_ACTION

One minimal next experiment: supply/verify the **existing approved** HTTPS bulk
fixture URL, fixed1MiB length/SHA256 and discard-only upload URL/byte-hash receipt
contract; then run the prepared single-stream download and upload cells on the same
UI84/gateway, with simultaneous existing Flow/ACK/carrier observations. Missing DATA
lengths must not block those application-goodput runs. Use the existing caps:30s
warm-up separate from120s launch window,≤16MiB/cell,≤256MiB/60min campaign, bounded
requests, no retry masking; preserve failures and automatic renewal boundaries.

Do not choose another public speed-test endpoint or create a server silently.
Only after actual bulk occupancy and carrier/ACK behavior are observed decide
whether an additional bounded DATA-length observation needs separate approval.
No optimization is selected, implemented or deployed from these light-load samples.

## SAFETY_AND_RETAINED_EVIDENCE

Private captures live under Git-ignored
`state-client-build/mesh-perf-2-physical-1/private/`, directory0700/files0600.
Public JSON contains allowlisted summaries and hashes, not device IDs, profile/key
contents, echo IP bodies or raw session records. All122 test-body files on the phone
were removed **only after matching their recorded SHA256**; application data and
security state were untouched. Raw measurements, collector errors and limitations
remain local. Original PERF-2/root-cause/APPLY reports are unchanged.

Final local evidence validation PASS:53 retained-file hashes,4 historical report/
evidence hashes,120 response records and cumulative timing percentiles independently
recomputed; all9 required report sections and relative links checked. Two derived
analysis files were tightened to0600 inside the already0700 private directory;
their bytes/hashes did not change. `git diff --check` PASS. These are evidence and
documentation checks, not additional physical traffic or a software test campaign.

No recovery/apply, signer/vault, service reset/restart/reload, timer pause, APK/native
build/install/sign, fault injection, intentional disconnect, identity/admission/floor,
IPv6, MTU, batching/window/ACK/RTO/pacing/timeout configuration change. No commit/push
or publication. The owner's working session is left connected. STATUS/PLAN now
distinguish working physical DNS/HTTPS from the still-missing sustained bulk baseline.
