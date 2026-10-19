# BETA87 PRODUCT FIX — recovery candidate88, throughput and IPv6

RESULT: **PARTIAL — recovery update88 installed on owner; same-identity proof,
READY and production DNS/HTTPS verified before and after scheduled rotation.**
Repeated automatic recovery and overnight acceptance remain separate gates.
Observations on19 October2026 UTC;
Brussels = UTC+2. No PERF-3B/handoff, production restart, server deployment,
credential/policy mutation, public updater, distribution or push in this task.

## Exact baseline and artifacts

Latest source remains the retained installed87 tree, not main or UI84. Repo HEAD
7656f2c65ea2928b71a928c12ee65a2f47f8ac4f is not a deployment assertion.
All84 entries in the accepted87 inventory were rehashed before changes. Unrelated
dirty work, Schema2/two CLEANED histories and floors are preserved.

| Item | Exact identity |
|---|---|
| Installed87 APK | `2a45f9672bdf76de8358859be58ad4bbf37c92ffd0a551693690b9f19e604c11` |
| Accepted87 source inventory | `5e78b4612ae5a648a19337d6b89292c37023ce1b720f8c2da6e1fdde3b1ebaf0` |
| Restricted native | `dd722eada0da7c890a8d71a72099cba5d0bbac1ce73377bbdbc8e7b85d820c23` |
| Loaded NL gateway | `4b722d2d7f2159b96953e27777494bf596768f860ee8da7e634fb1100b08fab7` |
| Deployed RU API | `e986f98e70ff7f1abc2678566dd360bb6555583f2e1744ea985c63699bcb3ef7` |
| Deployed RU/NL management | `c67332cfff9aeafd90690c13518f55a75ef9687ceadb464624263657ff005ff2` |
| Candidate88 source inventory | `12f55c029c11687c54c4bef2d6ebe07fdf5e70519e6cd0d6fbf2c85037b675b3` |
| Recovery parent87 overlay | `abfee769d191548ffc2df2b4ab885aeadd77fa46846d53613b7ac631717961bc` |
| Unsigned88 APK | `1d96994ea1ea195524f464f23ed51fe42dfb6c52e324d691b008acf3c7d75c37` |
| Signed88 APK | `968a61724f4e71ac0335e330960eb9b54e5ede59bae81df0b6e8499e4ce6c2ce` |
| Existing signer | `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a` |

All12 native libraries in88 are byte-identical to87/accepted batch1. The APK is
`0.1.18-beta88-recovery`, code88, package `com.familyconnect.app.friends`, Android12+
(minSdk31), arm64-v8a, 16KiB alignment verified. No per-user secrets or canary guard.

Signed file,56028128bytes:
`state-client-build/beta87-product-fix-20261019/delivery/FamilyConnect-0.1.18-beta88-recovery.apk`.
It is a private update candidate, **installed on owner11:55:55UTC, not distributed**.
Exact APK/code88, same UID and native hash independently read back after `adb install -r`.
The original
87 APK and manifests are untouched. Existing vault/memfd signing, independent
apksigner certificate pin and unsigned/signed member equality passed. No new key.
Toolchain: retained Temurin17.0.20.1+1, Gradle8.11.1, AGP8.9.2, SDK35,
Chaquopy16.1.0. No native rebuild. New remote CI was NOT_RUN; local Android/JVM
results below are not a claim of platform CI or overnight acceptance.

Safe structured evidence: [JSON](2026-10-19-beta87-product-fix-evidence.json).
Final private acceptance receipt: `delivery/acceptance88-receipt.json` under the
work directory, SHA256
`b1097ce73eeea1374163e875f8e920202fe34ca9ff6b45427031e63cd274fdff`.
It verifies the immutable signed/installed APK, source evidence hashes, same-identity
readbacks, one correlated recovery, all complete requests and measurement cleanup.
Measured response-body total across both phases:21113477bytes; active measurement
time289.541905seconds. This receipt does not certify overnight or remote FIELD use.
Private raw files, test logs, exact sources and signing receipt remain under
`state-client-build/beta87-product-fix-20261019/`, not Git. Reproducible public deltas:
`pilot/android-restricted/beta88-recovery.patch`, build guard
`pilot/android-restricted/check_beta88_recovery.py`; independent **unshipped** IPv6
delta `pilot/android-restricted/beta88-ipv6-local-only.patch`.

## NIGHT_DISCONNECT_CAUSE / MISSING_RECOVERY_CAUSE

Original supplied export copied before measurements, SHA256
`1b875b5e07df866e5fb6ffb8b7fd38b1533f70893a9abf54e88fa608f6595a96`.
The `ring` is beta87; the embedded `incident` is an older beta86 snapshot. They are
not interchangeable. Ring history contains two relevant closed87 sessions and a
later connected87 session. This is not a complete record of every overnight event.

| UTC | Android observation | Interpretation |
|---|---|---|
|00:00:24.456|First failure WEBSOCKET/CLOSED/SIGNAL_WS_CLOSE, READ_ERROR; first carrier close SIGNAL_READ|Proven signal-read closure; why the peer/path closed is UNKNOWN.|
|00:00:24.470|Phase3, authorization_denied=false, IO_CLOSED, reliable_terminal=carrier_closed|Not a recorded authorization denial or explicit Disconnect.|
|00:00:26.935|transport_lost SIGNAL_WS_CLOSE|Polling observed the closed native session.|
|00:00:27.130|FAILED/restoration_failed, retry_count0|No replacement attempt started for this failure.|
|09:19:07.544|CANCELLED → DISCONNECTING → DISCONNECTED|Separate later cancellation; not the cause of the midnight closure. Exact UI action is not recorded.|
|09:32:04.712|CARRIER FAILED / RELIABLE_RETRY_EXHAUSTED|Different later loss after a manual connection.|
|09:32:18.488|NETWORK → RESTORING|The existing retry-exhaustion classifier permits recovery.|
|09:32:46.244|restoration_succeeded; subsequent native session connected|One real beta87 automatic restoration, not proof all later losses recover.|

**Verified code defect:**87 only allows the correlated retry-exhaustion path.
The recorded `carrier_closed`/signal-read shape becomes INTERNAL, which is terminal.
`NightClassifierProbe.java` against the exact compiled87 classes returns INTERNAL;
the same synthetic, identity-free shape against88 returns NETWORK. This directly
explains why recovery did not start for the midnight event; it does not explain
the provider/socket closure itself.

Latest Android exit record is the18Oct23:46:41UTC installPackageLI replacement,
not a recorded overnight kill. A live service/process and CELLULAR at export do
not prove uninterrupted reachability or absence of Doze at the failure time.
Bounded RU/NL journal reads for23:59:49–00:01:39 and09:31:29–09:33:19 timed out
after18seconds each. Four failures retained as a limitation; no broad scan/retry.
No evidence attributes these incidents to DPI, gateway renewal or CPU saturation.

## Recovery delta and local verification

1. `RestrictedRecovery`: classify strictly correlated signal read/write closures
   (and constrained ICE loss/renewable credential expiry) as temporary. Unknown,
   policy close1008, protocol failures, invalid signatures, explicit denial and
   cancellation remain terminal. No catch-all INTERNAL→NETWORK conversion.
2. Requested connection survives temporary initial/reconnect failure. Backoff
   30/60/120seconds plus bounded jitter; repeated bootstrap failures enter a
   five-minute cooldown and later retry without another Connect. No retry storm
   or lifetime cap after the first reconnect. Counters reset only after120seconds
   of successful traffic-health observations, not a brief CONNECTED transition.
3. Missing underlying Internet-capable network does not create another room.
   Existing five-second connected/restoring poll remains the wake mechanism;
   Doze may defer execution. No always-held wake lock or periodic background room
   creation while no connection is requested.
4. Valid-cache warm start remains possible. API unavailable with empty/expired
   cache can wait for a new verified response; it never imports expired bytes.
   Explicitly denied or invalid cache does not become a retryable authorization.
5. Reuse existing VPN-bound DNS health check for restricted sessions:30second
   cadence, three failures trigger recovery; never use a direct network fallback.
   Blocking TUN is retained between candidates. Existing sockets are not promised
   continuity when a media session is replaced.
6. Persist only requested Auto/Telemost intent, transport/country, not live handles
   or credentials. Null-intent recreation requires saved request and VPN permission,
   then runs normal guarded startup. Disconnect/onRevoke/terminal rejection clears
   it. START_STICKY is conditional, not the whole fix; force-stop is not bypassed.
   Existing generation/lease fences remain. No identity/storage schema migration.

Important baseline correction:87 already polled RESTORING (`needsPolling`), and its
restoration counter led to bounded delayed recovery in some paths. It was not simply
the old `connected()` polling defect, nor proof of one reconnect per app lifetime.

**REPEATED_RECOVERY_LOCAL=PASS at state-machine/JVM scope.**135 tests in19 suites,
including three stable loss/recovery cycles in both Auto and explicit MESH,
missing/restored network, cooldown exhaustion/resumption, unavailable API/cache,
short-lived success, auth/protocol rejection, Disconnect/cancel, simulated long
pause and null-intent eligibility. An additional34 exact-classpath existing
ControlOperations/ControlStartup/ControlTransaction tests pass: old callback/cleanup
cannot release new owner, interrupted persistence/floors and startup barriers.
One active fixture candidate and correct release are checked. These fixtures do
not establish physical media/TCP recovery after three losses.

Initial six old tests expected permanent failure/reset-on-brief-success; their
failed XML is retained. Tests were changed to the specified bounded cooldown
contract, retaining revoked/invalid-cache terminal negatives. A separate first
JUnit launcher used the wrong Gson classpath (Strictness missing); failed logs
are retained, final extra run uses actual Gson2.13.2/bcprov1.85.2. Sandbox socket
errors were rerun under normal local permissions; no production workaround.

**RECOVERY_PHYSICAL=PASS_ONE_AUTOMATIC_EPISODE for88, not endurance acceptance.**
The fresh owner export below explicitly correlates the old session, automatic
RESTORING and new established session after the natural12:01 rotation. New proof,
import READY, DNS and process-attributed HTTPS/bulk succeed. This is one physical
retry-exhaustion recovery, a class87 already sometimes recovered; it is not a
physical reproduction of the midnight SIGNAL_READ classification fix or three
independent losses. OS process recreation, actual Doze, standby, underlying-network
replacement and overnight endurance remain unaccepted.
The simulated12hour pause tests scheduling, not Android power management. A sole
successful initial Connect would not close this gate. No intentional owner
network interruption or gateway outage was performed.

## THROUGHPUT_BEFORE_AFTER

Physical87 baseline19Oct11:23:40–11:26:01UTC: unchanged installed Android TUN,
same underlying network throughout, shellUID2000 explicitly covered by the VPN
UID range, route via TUN, strict HTTPS, and140 socket observations attributed to
the accepted NL gateway PID. Every request consumes the body on the phone, not
block-by-block over ADB. HTTP/1.1, fresh curl connections, identity encoding,
no cache-hit/compression, Cloudflare `__down`. Max150seconds/request and420seconds
per phase, below the existing limits. No upload/new benchmark server.

| Download87 | Delivered bytes | Full request seconds | Application Mbit/s |
|---|---:|---:|---:|
|Contract|65536|5.016689|0.104509|
|Single1|2097152|31.755839|0.528319|
|Single2|2097152|25.440598|0.659466|
|Single3|2097152|31.841126|0.526904|
|Parallel request1|2097152|28.088368|0.597301|
|Parallel request2|2097152|29.264504|0.573296|
|Parallel aggregate|4194304|29.290 device wall-clock|**1.145593**|

Single median **0.528319Mbit/s**. Formula includes DNS/connect/TLS/setup/TTFB.
Parallel aggregate uses total bytes over the shared device interval, not sum of
unrelated speeds. Two distinct client TCP ports and one new HTTP/1.1 connection
per request are observed. Actual native Mux stream IDs/counts were not exported;
two requests alone are not that measurement. No request failed or was truncated.
Observed body SHA256 per request is evidence, not an independent origin digest.
BYTE_EXACT_ACCEPTANCE=NOT_VERIFIED for this external endpoint.

Application HTTPS full-response times, not media/ICMP RTT:
- Idle3 observations:3.663270,2.772522,2.502466seconds.
- Under bulk22 observations, all overlapping:0.944696–4.745448seconds; no errors
  or timeouts. Individual values and TTFB are in the safe JSON. No stable p99 claim.
- NL CPU averaged6.17% of one core, peakRSS52645888bytes over this sample; Android
  CPU averaged11.78% of one core (CLK_TCK100 read back), thermal status0. This
  does not exclude short lock/scheduling stalls or constrain other devices.

### After88 physical comparison

**After88=PASS_MEASUREMENT**,19Oct12:07:14–12:09:43UTC,148.581seconds. Same phone,
underlying network identity/transports, endpoint, HTTP/1.1 fresh connection per
request, continuous phone-side reads and accounting as87. Both phases together
use289.542seconds of measurement load and about20.13MiB plus small probes, below
15minutes/32MiB. The upgrade and normal production rotation separate the phases;
this is not a continuous same-media-session or randomized causal A/B experiment.

| Download88 | Delivered bytes | Full request seconds | TTFB seconds | Application Mbit/s |
|---|---:|---:|---:|---:|
|Contract|65536|5.677139|See raw receipt|0.092351|
|Single1|2097152|33.711980|3.513264|0.497663|
|Single2|2097152|23.022642|1.925190|0.728727|
|Single3|2097152|33.553847|2.442417|0.500009|
|Parallel request1|2097152|36.214328|0.813582|0.463276|
|Parallel request2|2097152|36.743463|1.343672|0.456604|
|Parallel aggregate|4194304|36.760 device wall-clock|Not summed|**0.912797**|

Every body completed at the requested size, HTTP200/TLS verified, identity encoding,
no observed cache HIT, zero failed/time-limited requests. Two parallel requests use
two distinct client TCP ports and one new connection each; actual Mux stream IDs
are **NOT_OBSERVED**, not inferred from the number of HTTP requests.149 bounded
samples attribute outbound sockets to productionPID3007847, with no sampler errors.
Observed body SHA256 is retained per request; it is not an independent origin digest.
**BYTE_EXACT_ACCEPTANCE=NOT_VERIFIED**, despite complete successful performance runs.

| Comparison | Beta87 | Beta88 |
|---|---:|---:|
|Single median, Mbit/s|0.528319|0.500009|
|Two-TCP aggregate, Mbit/s|1.145593|0.912797|
|Idle HTTPS response, n / range seconds|3 /2.502466–3.663270|3 /1.402046–3.388730|
|Loaded HTTPS response, n / range seconds|22 /0.944696–4.745448|23 /1.154968–5.255031|
|Idle / loaded median response seconds|2.772522 /2.511873|2.588941 /2.679161|
|Failed probes / timeouts|0 /0|0 /0|
|NL CPU, percent of one core|6.165|6.161|
|Phone process CPU, percent of one core|11.784|40.547|
|NL peak sampled RSS, bytes|52645888|47050752|

All23 loaded88 probes overlap a transfer; three idle probes do not. These are full
HTTPS response times with fresh connections, not ICMP/media/ACK RTT. Tiny idle
sample sizes do not support a stable tail percentile. Raw observations, including
TTFB and body hashes, remain in the per-request receipts and safe evidence JSON.

**No speed improvement established.** Single median is about5.4% lower and parallel
aggregate about20.3% lower in this sample. Different time/media session and normal
gateway rotation prevent attributing that difference to the recovery patch. Phone
CPU is materially higher in the88 sample; UI/screen/other app-worker activity was
not matched between phases, and no thread-level profile was captured during bulk.
Do not claim negligible recovery overhead or a CPU root cause from this aggregate.
NL average CPU does not show sustained one-core saturation; it cannot exclude
short scheduling/lock stalls. A five-second post-bulk idle readback gives8.752%
phone-process CPU, app not resumed at that readback; it does not reconstruct the
screen/UI state during bulk. No failed throughput optimization was shipped.

The final readback checks the same phone process/topology, APK88, NL PID/binary,
RU/NL generation/source pins and absence of the measurement temporary directory.
Only measurement workers/files are cleaned up; the owner VPN remains connected.

**Performance optimization NOT applied.** Native and transport settings are unchanged;
this update is not advertised as faster. DATA-size, retained/SACKed/unconfirmed bytes,
true sender-blocked duration, ACK latency and per-stream credit waits are
NOT_OBSERVABLE from the accepted build's available export. SendDepth is not bytes
in flight. The two-stream advantage reproduces physically, but does not choose
small records, Mux credit or consumption/head blocking as a cause. An enlarged
window/credit/batching change would still be speculative. Existing PERF counters
remain reusable; no owner-only provisioning or new canary was started.

**SMALL_RECORD_HYPOTHESIS=INCONCLUSIVE.** Parallelism still helps application
throughput (88 aggregate about1.83× single median), but there is no time-correlated
DATA/window/SACK/Mux-credit evidence for this physical connection. The specific
missing performance measurement is sender-ready blocked time with retained-byte
and Mux-credit state on the ordinary compatible gateway path, correlated to one
single download. It is not a reason to enlarge windows or restart PERF-3B.

### Fresh88 export: recovery correlation and available internal counters

Owner supplied `FamilyConnect-diagnostics (1) (3).json`; preserved privately as
`recovery88-export.json`, SHA256
`f9bc9e2c09f5ce6146f8696a173c63cd4f9f82248898b4e65f5ca2d51e120b03`.
Copy hash equals source. `ring` is88/CELLULAR/CONNECTED with VPN capture open;
embedded `incident` is still stale86/FAILED and is excluded from88 conclusions.
Acquisition receipt and safe projection are retained; no identity/session tokens,
room credentials or payloads are included in the public projection.

| Phone-reported UTC | Evidence | Meaning |
|---|---|---|
|12:01:30.647|CARRIER/FAILED/RELIABLE_RETRY_EXHAUSTED, close source RELIABLE_EXHAUSTION|First recorded old-session failure; no authorization denial|
|12:01:33.603|restoration_attempted, NETWORK, CONNECTED→RESTORING|Automatic recovery, retry1; links exact old native session|
|12:01:33.707|cleanup_completed|Old-session cleanup; not user Disconnect|
|12:01:35.781–36.556|READINESS/READY while RESTORING|Strict refresh/import succeeds; server ACK separately recordsCRL27130|
|12:02:02.530|FAMILY_AUTH_READY, SESSION_READY|New native session authenticated/established|
|12:02:02.686|restoration_succeeded|Same application connection, different native session;29.083seconds from attempt on the same phone clock|
|12:02:08.752 onward|DNS_PROBE_OK repeatedly|Traffic-health resumes; later external HTTPS and bulk independently succeed|

No CONNECTING, DISCONNECTING or DISCONNECTED transition occurs between the
correlated attempt and success. `previous_session_tag` is read from the currently
stored session at each event by DiagnosticRing: at attempt it is the old tag,
at success it is the **new** tag. Do not require that misleadingly named field
to remain old across success. Underlying PHONE clock determines29.083seconds;
this is detection-to-establishment, not exact outage duration or one-way latency.
Production material/PID change is independently observed around the same interval;
exact cross-node timing or provider cause is not inferred.

At12:10:25 the new-session lifetime snapshot reports28 local ReliableStream
retransmissions,26 recovery timeouts,6374 media received frames,5788 written samples,
54 DNS responses/0 DNS errors,85 TCP opens/0 open errors, and0 admission waits or
rejections. Mux sent/received bytes are107403/10950330; **not wire bitrate**.
Mux `protocol_errors=6` is retained, not hidden. Exact source increments it for
several cases, including frames for a missing stream and unknown/completed DNS
calls, as well as protocol-invalid transitions. This snapshot has no per-error
cause; it does not establish six corrupted application bodies or explain speed.

The eight retained current delivery snapshots cover12:10:10–24 (reported UTC),
after the bulk interval. Last assembly counters: RTP14783, RTP gap events67,
VP8/binary fragments6117, completed carrier messages5004, expired message
assemblies29, malformed/CRC/conflict/duplicate0. `expired` is carrier-message
reassembly timeout, **not a count of VP8 frame discards**. These are lifetime
receiver observations, not run-specific loss percentages or NL retransmissions.
Local outgoing `pending` ranges0–3, head_sacked=false in those tail snapshots;
`buffered` is the receive-map block count, **not bytes**. They do not observe the
NL download sender window during load. Current lifecycle trace_dropped233 and
delivery_dropped243 show bounded eviction; missing bulk snapshots are not proof
of no stall. Old-session delivery/archive drops73/135 are also retained.
No DATA-size distribution, sender retained-byte partition or Mux-credit wait
duration is available. **Performance root cause remains INCONCLUSIVE.**

## IPv6_CLIENT / IPv6_GATEWAY / IPv6_END_TO_END

Read-only namespace probes11:24:20–22UTC establish:
- **NL actual gateway netns:** zero global IPv6 addresses, zero default IPv6 routes,
  `curl -6` outbound fails with exit7. Same netns as host. Link-local is insufficient.
- **RU actual API netns:** one global IPv6 address/default route and outbound IPv6
  succeeds. RU is not an NL exit and was not substituted for it.
- Android already captures `::/0` with a private TUN address and MTU1280. Exact87
  `wholedevice.Allow` explicitly rejects IPv6. No `allowFamily` bypass was added.

Independent local-only opt-in implementation shares tcpforward's public destination
policy, permits IPv6 TCP and existing DNS path while leaving `Attach` default
IPv4-only. No change to wire encoding, admission, crypto or server DNS policy.
IPv6 literals, public AAAA destination selection and actual local tcp6 socket echo,
byte-exact wholedevice echo, AAAA query forwarding, private/link-local/metadata,
transition/documentation ranges, mixed DNS rejection, UDP/QUIC rejection and closed
session behavior are covered by local tests. `go test -race ./wholedevice
./tcpforward` passes; new AAAA check also passes. These are distinct fixtures, not
a physical Android-TUN→Mux→NL IPv6-only HTTPS test. The explicit opt-in is **not wired
into the shipped native bridge or APK** while the required NL path is absent.
No claimed general UDP/QUIC/ICMP support; full packet-stack/MTU physical acceptance
remains pending.

Provider documentation rechecked:
<https://hostkey.com/documentation/faq/network_settings/#is-ipv6-available-for-vps-servers>
says VPS IPv6 is unavailable and dedicated IPv6 currently available only NL/US.
That public FAQ is not an attestation of this account's exact tariff. Required
infrastructure action: obtain provider-confirmed global IPv6 allocation/prefix,
gateway/route/interface and MTU for **this NL server**, or owner-approved supported
NL service if its tariff cannot supply IPv6. No address invented, service purchased,
country changed, public route advertised, or IPv4 configuration changed.

Statuses: IPv6_CLIENT=LOCAL_PROTOTYPE/PASS_LOCAL_ONLY;
IPv6_GATEWAY=BLOCKED_NL_ALLOCATION_ROUTE;
IPv6_END_TO_END=NOT_RUN. This blocker does not withhold the recovery APK.

## Identity, server state and rollback

Server readback11:21 and owner identity readback11:43:54 retain all_activated,
authority18 (expires16Jan2027 22:36:48Z), matching management source pins,
Schema2/two CLEANED histories/zero unfinished operations. Current sampledCRL27129,
leaf/CRL expiry13:31:06Z and directory expiry13:31:18.457925935Z; RU/NL directory
hashes match. These are observation times, not constants for a later install.
Automatic renewal remained enabled and was not forced. No new authority/grants,
manual entitlement, revocation, floor or gateway binary change.

Owner device still has one non-revoked registration; pre-upgrade identity/key-binding
and Support ID digests retained privately. **IDENTITY_PRESERVED after88=PASS**:
12:00:23 and12:06:31 readbacks match the pre-upgrade canonical binding and Support
ID digests, with fresh code88 proof/import/READY ACK under the same server record.
This is not inferred solely from matching package/signer. Authorized installer requires
ordinary Disconnect, then `adb install -r`, no uninstall/data clear, exact installed
APK/UID/native readback, same-identity proof/import READY and production DNS/HTTPS.
Two earlier guard checks returned WAIT_FOR_ORDINARY_DISCONNECT without writing an
install intent or changing runtime. Owner subsequently confirmed ordinary Disconnect.
At11:55:55.783334UTC the single `adb install -r` succeeded; exact installed88 APK,
same UID and restricted-native hash read back. VPN/service absent after update.
Private `upgrade88-intent.json`, command, installed readback and durable receipt
preserve the sequence. No uninstall/data clear or artificial network outage.
No task-triggered server mutation. No bulk started on a disconnected phone.
Do not rerun install using the consumed intent.

### Owner Connect and normal rotation observation

-12:00:26UTC: shellUID2000 is explicitly covered by VPN0–99999, route via tun1,
  MESH DNS; complete HTTPS200/TLS verified,211bytes,3.536980seconds,25 matching
  productionPID2918811 socket samples. Same installed88 APK verified first.
-The first after88 measurement stopped at remote preflight before its manifest,
  phone temporary directory, samplers or requests were created. Remote exit1 is
  retained; its original stderr was not captured. Therefore the exact failed
  predicate is UNKNOWN, not retrospectively attributed to credentials.
-A narrow readback12:02:27 passes: ordinary renewal changed productionPID to
  3007847, binary unchanged, NRestarts0, leaf/CRL now expire16:01:16UTC. No restart
  or renewal was requested by this task.
-12:06 readback: CRL27130, authority18 unchanged; RU/NL directory SHA256
  `125c1d4bb3221d4e52bcc6c3870df0d360bf8fe267b28fb741a397bae5ee6e0e`,
  issued12:01:31.820333729Z, expires16:01:29.030477434Z, identical on both nodes.
  Existing identity submits fresh88 READY with minimum_crl27130 at12:01:36Z
  (server timestamp; no precise cross-node latency inferred).
-12:06:32UTC: full HTTPS200/TLS verified,215bytes,3.280477seconds,16 matching
  new productionPID3007847 socket samples. UID/TUN/egress checked again. Both
  controls clean their own temporary files and sampler; neither is a bulk result.
-Read-only reconciliation and a new successful MESH control permit resuming the
  **not-yet-started** after88 measurement. An explicit guard rejects resumption if
  any request/manifest or other unexpected contents exist; the failed preflight
  and its receipt are preserved, not erased or counted as a successful transfer.

Known87 signed APK remains immutable evidence/rollback source. Do not bypass Android
version protection or uninstall to downgrade; if88 fails, keep data/floors and issue
a same-key higher-code forward correction after diagnosis. No server rollback is
needed because no server change was applied. Do not restore old databases or
expired credentials. Signing and build receipts remain distinct from installation,
post-upgrade acceptance and tester distribution.

## Final status / next action

| Required result | Status |
|---|---|
|NIGHT_DISCONNECT_CAUSE|Signal-read closure proven; initiating network/provider cause UNKNOWN|
|MISSING_RECOVERY_CAUSE|VERIFIED: correlated carrier_closed misclassified INTERNAL in87|
|REPEATED_RECOVERY_LOCAL|PASS_JVM,135+34 checks; not physical traffic cycles|
|RECOVERY_PHYSICAL|PASS_ONE_AUTOMATIC_EPISODE: correlated88 RESTORING→CONNECTED29.083s, then traffic; not repeated/overnight acceptance|
|THROUGHPUT_BEFORE_AFTER|PASS_MEASUREMENT both versions; improvement NOT_ESTABLISHED; no optimization applied|
|IPv6_CLIENT / GATEWAY / END_TO_END|Local prototype / NL infrastructure blocked / NOT_RUN|
|IDENTITY_PRESERVED|PASS: same registration/key bindings/Support ID and fresh88 proof/import READY|
|SIGNED_APK_PATH / VERSION / SHA256|Available above; code88, same signer/native|
|SERVER_CHANGES|NONE in this task|
|FINAL_RESULT|PARTIAL; owner upgrade/identity/DNS/HTTPS and bounded comparison complete; recovery endurance/performance cause/IPv6 open|

**Owner handoff:** the signed88 recovery update is available at the exact path
above, and upgrade/identity plus one real automatic recovery and subsequent traffic
are verified on owner. The supplied export closes the transition-correlation gate;
no further manual action or reconnect is needed now. It remains a limited private
recovery candidate, not a speed/IPv6/overnight fix claim. No reactivation, invitation,
profile import or FIELD enable is needed. No further load or automatic PERF stage
is scheduled. The next performance step is the one missing sender-side correlated
measurement above, not speculative transport tuning.

User instruction for the APK: «Установите APK поверх текущего Family Connect,
выбрав “Обновить”. Откройте приложение и подключитесь. Регистрация и ваш ID
сохраняются». Do not remove the app or clear storage. New Android permissions, if
actually requested, are confirmed by the owner; they are not Family registration.

Remaining explicit limitations: no88 overnight/real Doze/process-recreation evidence,
only one client-correlated physical recovery, no measured speed improvement, no production
IPv6, and no remote testers' physical acceptance. Missing overnight journals do not
invalidate the reproduced recovery defect; local tests do not prove the missing
physical outcomes.
