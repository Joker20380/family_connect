# Beta88 continuation — targeted throughput and concrete IPv6 resolution

## Checkpoint —19 October2026 UTC

FINAL_RESULT=PARTIAL. One targeted server correction was implemented, locally
tested and physically compared; **not accepted for delivery** because repeatable
speed improvement was not established. Original accepted gateway is restored,
production Android-TUN DNS/HTTPS passes. Existing beta88 recovery remains the
baseline; no PERF-3B/handoff, new APK or speculative second optimization.
Installed APK SHA256 `968a61724f4e71ac0335e330960eb9b54e5ede59bae81df0b6e8499e4ce6c2ce`.
Accepted loaded NL gateway `4b722d2d7f2159b96953e27777494bf596768f860ee8da7e634fb1100b08fab7`.
Previous physical comparison and one automatic recovery are preserved in
[beta87 product-fix](2026-10-19-beta87-product-fix.md); no speed fix was in88.

Fresh readback12:35UTC: same APK/gateway, CRL27130 and16:01:16Z leaf/CRL expiry,
same RU/NL directory, no unfinished handoff. Native/identity/recovery unchanged.
NL gateway network namespace has no usable global IPv6/default route; outbound
IPv6 exits7. Host virtualization is KVM; account tariff is not established by this.

Existing accepted gateway source inventory is
`aeeb6755bd235160127cfed67da4a870ae340cfebe89fc6d0f937908607d9483`.
Reusable observation-only overlay source inventory
`bc3721ec8c30c6fb304c478b22398926fe3bfc0c576216c49ed53809d78c3051`, binary
`04886384ce0bfa80568aea7e6d6fd2fec6ee0ed300a071ea806a8ef6a29a033b`,
Go1.26.1/linux-amd64, only fc_perf_diagnostic. This is the PERF-3 pre-owner-guard
counter candidate, not PERF-3B. Exact unchanged source/receipts are checked before
reuse; no all_activated/credential/protocol/transport-setting delta is included.
Existing402 race pass records/16 opt-in skips and paced overhead receipts are
reused, not presented as new tests. Two non-race stream_limit fixture failures
remain a documented admission-test limitation, not proof that a live failure is
safe. Metadata-only delta does not change admission or queue/credit bounds.

Private work and immutable receipts:
`state-client-build/beta88-throughput-20261019/`. No push/public release.
Production application and physical measurement results must be recorded here
after readback; this checkpoint alone does not assert either.

## Observation rollout —12:56 UTC

One ordinary controlled stop/atomic replacement/start of the existing NL unit,
under its existing RU coordinator and NL node locks. Loaded process3043619,
binary04886384…a033b; exact argv/unit files/profile unchanged. No owner guard,
new room selector, admission, API, Android, timing or transport changes. Immutable
baseline binary retained in protected NL staging directory and locally. Existing
READY/runtime-binding collector independently validates served TLS chain and
leaf, directory binding and RU/NL publication. Directory now
`f62954b2e722d78b4b928a14e5c7f33f25aa3d625a0d2274306e75a8cd191dae`.
Leaf/CRL still expire16:01:16Z; no credential issuance/rollback requested.
Readback receipt `receipts/observation-readiness.json`; transition receipts are
under the private work directory. This is observation, **not a speed fix**.

## IPv6 infrastructure decision and ready-to-send request

Fresh inspection uses the actual gateway network namespace (same as host).
KVM, interfaceens3: link-local only; no public global IPv6 and no default IPv6
route. Two existing tunnel interfaces have **ULA** addresses reported by Linux
as scope global; these are not Internet allocations. `ip6tables-save` is empty
in this namespace; this alone does not establish provider firewall policy.
Direct IPv6 HTTPS failscurl7. No addresses/routes/firewall changed.

HOSTKEY's [network FAQ](https://hostkey.com/documentation/faq/network_settings/#is-ipv6-available-for-vps-servers),
retrieved19 October2026 (page updated16 October2026), says IPv6 is not provided
for VPS; dedicated availability is limited to NL/US. KVM detection does not
establish this account's product contract. Therefore **A (just configure supplied
parameters) is not established**. Required next infrastructure action is B:
provider confirmation for this specific service. If it is the documented VPS
offering, C applies: an IPv6-capable **Netherlands** egress service/migration is
needed, separately approved; no software route can invent an allocation.

### Draft for the owner's existing HOSTKEY support account — NOT SENT

Subject: Native IPv6 availability for existing Netherlands server186.246.45.246

Please identify the exact product/tariff of our existing Netherlands server with
IPv4 address186.246.45.246. It reports KVM virtualization. Your network FAQ says
VPS has no IPv6, whereas NL dedicated servers may have it. Please confirm whether
native public IPv6 is available for **this existing service**, included or as an
option, without changing its current IPv4 or Netherlands exit location.

If available, please provide the allocated IPv6 address/prefix, routed prefix if
different, next-hop/gateway and any on-link requirement, assignment method
(static/SLAAC/DHCPv6), interface requirements and MTU. Please specify outbound and
inbound filtering/source-address validation, TCP443 availability, and required
ICMPv6/neighbor discovery/Packet Too Big behavior. What operator activation is
needed, what is its price, and does activation require downtime or a reboot?

If unavailable on this tariff, please confirm that explicitly and quote the
smallest supported Netherlands option with native IPv6, migration/downtime and
IPv4-preservation constraints. This is an information request, **not authorization
to order, migrate or interrupt the current server**.

The billing/service identifier must be selected by the owner in the existing
account, not guessed from an IP. No support message/order has been sent.

### Client boundary

Beta88 retains the accepted native transport. Its TUN captures IPv6 to prevent
bypass, but wholedevice rejects IPv6 destinations; adding NL IPv6 alone is not
end-to-end support. Existing opt-in dual-stack prototype and local race/AAAA/
destination-policy fixtures are preserved, not included in88. Once allocation is
confirmed: verify real NL outbound IPv6, then wire the bounded TCP/DNS opt-in into
a compatible signed client update, validate leaks/recovery and perform IPv6-only
HTTPS through Android TUN with a matching IPv6 gateway socket. No UDP/QUIC/ICMP
coverage or production IPv6 PASS is claimed. This does not hold back beta88.

## First physical observations and one correction under test

Observed-baseline13:00:47–13:02:52UTC, unchanged beta88 through its installed
TUN/cellular underlay, HTTP/1.1 fresh connections, Cloudflare agreed endpoints.
Single2MiB0.544186 /1.010375Mbit/s (curl full request time); parallel pairs
1.127705 /1.443950Mbit/s (sum delivered bytes/shared wall interval). Two actual
bulk Mux streams in each parallel cell; one in each single cell.62 snapshots,
one gateway session, PID3043619. Synthetic results are reported separately.

Journald splits messages at49,152bytes. Initial grep collector could not parse
split JSON and retained only7 complete snapshots. A bounded readback of the
**same completed invocation/time interval**, preserving stream identity and
`line-max` continuations, reconstructs all62 without parsing errors.59 split
records recovered; raw private journal and initial incomplete capture retained.
No extra network test or instrumentation restart was needed. Retained byte/block
partition equals SACKed+unconfirmed in every recovered snapshot.

|Cell|Sender waiting on window, no local writer/queue|Head unconfirmed with later SACKs|Median retained bytes|Bulk Mux zero-credit ready time|
|---|---:|---:|---:|---|
|Single1|68.9%|32.1%|57,522|25.23s of30.00s observed|
|Parallel1|95.2%|40.4%|81,408|12.68/15.22s per stream of28.00s|
|Single2|37.7%|11.9%|49,526|12.87s of14.00s observed|
|Parallel2|96.3%|35.9%|78,186|7.67/6.77s per stream of22.00s|

These clocks overlap across layers/streams, not additive causal shares. Sampled
window-full frequency is not used as blocked time. NewDATA bytes are89–97% in
the8–16KiB range, but single-stream DATA **count** is43–49%≤512bytes. Thus neither
“all records384bytes” nor “all bytes fit an ideal128KiB flight” describes this
connection. No-retry first-ACK mean242–380ms includes local path and ACK return,
not HTTPS latency. Submission-to-carrier-enqueue mean30–49µs; local queued bytes
median0. Retained/SACKed bytes are not physical in-flight bytes. Retry traffic
and head gaps coexist with per-stream64KiB credit exhaustion.

### Reproduced exact write-path mismatch

Gateway target reads use16,384bytes, but the existing batch fits only
16,362plaintext −12Family header −10Mux header = **16,340TCP bytes**. A full
read therefore sends16,340 then44TCP bytes; separate framing/TLS makes RS DATA
16,384 then **88bytes**. The recovered bounded event rings show111 occurrences
of88bytes versus113 of16,384 in single1,76 versus80 in single2 (ring samples,
not exhaustive counts). Parallel scheduling can combine some small tails.

One candidate aligns **only target socket read-buffer size** with the existing
Mux batch payload limit, using the same helper in the unchanged writer formula.
No change to MaxData protocol bound,64KiB credit,8-slot window, ACK/consume,
RTO, pacing, buffering policy, TLS, admission or Android. Nonbatch endpoints
continue using16,384bytes. Server-only, wire-compatible, smaller read buffer.

Synthetic exact segmentation fixture:130,720bytes, previous15Mux frames with
seven44-byte tails; candidate8frames, no44-byte tails, byte-exact. Five race
repeats of two new cases PASS. Affected dependency race suite:300 test pass
records,11opt-in skips, six packages PASS. Existing recovery135+34 receipt and
exact unchanged APK/native remain baseline; no new overnight claim.

The separate512KiB/240ms synthetic no-loss benchmark does **not** show speedup:
baseline1.309/1.410/1.418 versus candidate1.306/1.299/1.305Mbit/s. This negative
result is retained, not dismissed or merged with physical performance. It proves
that removing tails alone need not remove per-stream credit/path limitations.

Candidate source inventory
`41838a1c8435d108dc06adf60cca4d49eb7beafbca4810784897aa094c684a6d`;
binary`0eb38db8e1ec95ce67a358de2aaf910d4aa666fe9a80ee349d26a601aef734e6`.
One controlled comparative rollout13:12:09UTC, PID3053841; strict TLS/binding
and RU/NL directory readback PASS13:12:30. Directory
`c7d6b398abc08dd7324997650db280df45cf9fc049b86a22ac430a0ef7780aa0`.
Source differs from observation baseline in two runtime files plus one test file.
No improvement acceptance yet. If physical gain is absent/ambiguous, restore the
original accepted4b722d…8fab7 binary through the existing guarded transaction,
publish forward runtime binding normally, and preserve credentials/floors.

## Physical comparison and acceptance decision

|Alternating cell|Observed baseline Mbit/s|Read-alignment candidate Mbit/s|Actual bulk Mux/TCP streams|
|---|---:|---:|---:|
|Single1,2MiB|0.544186|0.551600|1/1|
|Parallel1,2×2MiB aggregate|1.127705|1.224761|2/2|
|Single2,2MiB|1.010375|1.675445|1/1|
|Parallel2,2×2MiB aggregate|1.443950|1.451542|2/2|

Baseline124.075s and12,652,917response-body bytes; candidate119.129s and
12,652,720bytes including control/probe bodies. No failed/incomplete HTTP
responses, no endpoint refusal/retry. Both phone temporary directories and local
samplers cleaned. Request deadline150s; each phase cap600s; no additional bulk
series was run to chase acceptance. Same beta88/underlay/endpoint/HTTP1.1 method,
different gateway/media sessions due required binary transitions. Each parallel
pair's requests have different local TCP ports; corresponding actual bulk Mux IDs
and gateway PID socket matches are retained. Bulk IDs are private correlation
data in the safe evidence, not authentication identities.

Single uses `body_bytes*8/curl.time_total/1e6`, including setup/TTFB. Parallel uses
sum bytes divided by the shared measurement wall interval (including small ADB
invocation overhead), not a sum of individual speeds. Bodies read continuously
on phone; only compact results cross ADB. HTTP200, TLS verification0, identity
encoding, no cache-hit/age in successful records. Observed body SHA256 values
record only these responses; independent origin digests are unavailable, so
BYTE_EXACT_ACCEPTANCE=NOT_VERIFIED_PHYSICAL. Local fixtures are byte-exact PASS.

|Response latency, seconds|Baseline|Candidate|
|---|---|---|
|Idle HTTPS,3samples|1.803–4.624|1.783–3.239|
|Loaded HTTPS|18samples,1.087–3.262|17samples,1.368–3.782|
|Errors/timeouts|0|0|

These are full application HTTPS response times, not ICMP/media RTT. Loaded
probes start while bulk is active, at most one outstanding and no more frequent
than every5s. They may finish after bulk ends; exact overlap can be calculated
from retained request intervals. No stable p99 claimed. Gateway CPU6.61% versus
6.30% of one core; phone33.31% versus14.66% (screen/app work not controlled).
Carrier send queue sampled0–1 versus0–4frames. These observations do not show
gateway CPU saturation and do not establish a physical off/on tracing overhead.
The separate1MiB direct-NL control completes in0.228879s,36.65Mbit/s, inside the
gateway network namespace; this is a short external-path control, not sustained
capacity or Android throughput.

### What the candidate changed in the measurements

|Cell|Tiny DATA count≤512B, before→after|Ready sender window-blocked before→after|No-retry first-ACK mean ms, before→after|Retries before→after|
|---|---|---|---|---|
|Single1|48.8%→26.6%|68.9%→88.9%|380→381|51→49|
|Parallel1|22.4%→9.0%|95.2%→95.9%|297→316|42→39|
|Single2|43.4%→24.3%|37.7%→99.2%|262→171|8→1|
|Parallel2|37.2%→9.9%|96.3%→88.8%|242→250|19→25|

Counters are differences over interior snapshot intervals, not the full request;
all exact intervals/counts/byte fractions are in the linked evidence. Candidate
has59reconstructed snapshots,31journal continuations, no parse/partition errors.
The recurring88-byte tail disappears from the captured submissions. New small
220/396/572-byte records occur as unchanged64KiB credit boundaries split reads;
fixed socket alignment alone cannot remove this credit interaction. No counters
were relabeled as physical bytes in flight. Received RTP/assembly counters on NL
describe the **reverse** direction, not proof of Android download packet loss.

**Decision: NOT_ACCEPTED_AS_THROUGHPUT_FIX.** One single improves, the other is
essentially unchanged; parallel change is within observed variability. The best
candidate single also has a much shorter first-ACK interval and fewer retries.
Changed media sessions prevent attributing that gain to this patch. The no-loss
local benchmark is negative. Therefore neither a promised speed increase nor an
APK release is justified; no second parameter/credit/window change is attempted.

## Bottleneck classification and exact missing observation

- VERIFIED source+fixture+physical:16KiB socket-read/batch-envelope mismatch creates
  small88-byte RS records and uses extra slots. The candidate removes that exact
  mismatch, but does not establish a repeatable physical speed benefit.
- VERIFIED physical: ready sender is blocked by retained ReliableStream slots;
  all effective windows are8. Significant head-unconfirmed/later-SACKed intervals,
  retransmissions and cumulative-release delay coexist. SACKed-head blocking is
  smaller but nonzero; do not assign it to an Android component without evidence.
- VERIFIED physical: single stream has ready data and zero64KiB Mux credit for
  most baseline observed time. Two real streams provide separate credit and more
  retained data. This is backpressure evidence, **not proof that enlarging credit
  would cure the underlying ACK/recovery delay**.
- NOT ESTABLISHED: carrier loss versus lost/delayed ACK versus receiver consumption
  as the initiating cause. Short direct NL and low gateway CPU do not locate it.

One next missing measurement: for a **specific retransmitted NL DATA sequence**,
correlate Android's first receive, consume and ACK-emission events with the
already observed NL submission/first-ACK/cumulative-release timeline. Record
monotonic intervals per endpoint, not unsynchronised one-way latency. This
distinguishes a missing head at Android from ACK-return delay or held consumption.
The installed beta88 export does not expose that correlated receiver timeline.
No new instrumentation platform, canary routing, tuning or new live test is started.

## Final state, artifacts and rollback

Candidate rolled back13:18:43UTC by the same guarded short transaction directly
to original accepted gateway
`4b722d2d7f2159b96953e27777494bf596768f860ee8da7e634fb1100b08fab7`, PID3058625,
NRestarts0. Unit/argv/profile unchanged, new forward runtime-bound directory
`04e1610454ad8fb6a5589b741aec0b2d04548c5bc168e6502de0e22ad4a3ed96` verified
on RU/NL with strict served TLS13:19:45. Phone DNS/HTTPS13:19:48 passes,216bytes,
19matching production PID socket samples; no manual Connect requested by this
task. This is restored traffic, not a timed overnight/reconnect acceptance.

No background sampler, canary, owner override, pending handoff or retained lock.
Original API/management packages, all_activated,authority18 and Schema2/CLEANED
history unchanged. Renewal timer remains active/waiting, service inactive,
no pending renewal owner. No credential/floor rollback or manual renewal. Staged
binary copies/receipts remain protected as evidence, not running services.
Observation counters are **no longer active** after accepted-binary restoration.

Preserved private artifacts:
- Accepted beta88:
  `state-client-build/beta87-product-fix-20261019/delivery/FamilyConnect-0.1.18-beta88-recovery.apk`,
  SHA256`968a61724f4e71ac0335e330960eb9b54e5ede59bae81df0b6e8499e4ce6c2ce`.
- Rejected server candidate:
  `state-client-build/beta88-throughput-20261019/gateway-aligned-read`,
  SHA256`0eb38db8e1ec95ce67a358de2aaf910d4aa666fe9a80ee349d26a601aef734e6`.
- Reproducible delta and synthetic test:
  `tests/fixtures/beta88_throughput/gateway-read-alignment.patch` (not a release),
  SHA256`08a4cd06115fd9570d0c51791fc8eed5e28feda1f7f0f23ad595c8072460eed9`.
- Exact build/test/deployment receipts, source inventories and raw measurements
  remain under the private work directory; sanitized aggregate
  [evidence](2026-10-19-beta88-throughput-ipv6-1-evidence.json).

Safe evidence SHA256
`3b75b1f9894afeb03f1754aa2cba40782aaaf79e1bb23e9ebb401c09a4687231`;
final RU/NL deployment readback receipt SHA256
`c282064b2da8788ad60fbd52a0f4b1c3d47e214ef4e2de9653b3f5d4b3dffe5b`.

|Requested result|Final status|
|---|---|
|RECOVERY_BASELINE_PRESERVED|PASS unchanged88 APK/native, existing135+34 local checks and one natural physical recovery retained; no new overnight claim|
|THROUGHPUT_BOTTLENECK|PARTIAL: slots/head/credit waits measured; initiating receive/ACK cause unresolved|
|TARGETED_CHANGE|Implemented/tested/physically compared; rejected for delivery and rolled back|
|BEFORE_AFTER_WITH_VARIABILITY|PASS bounded physical comparison, not a speed-improvement claim|
|IPv6_CLIENT_READINESS|Existing local TCP/DNS prototype only; beta88 still blocks IPv6 safely|
|IPv6_INFRASTRUCTURE_ACTION|Ready-to-send specific HOSTKEY request; VPS service unsupported per current FAQ pending account confirmation; no purchase/migration|
|IPv6_END_TO_END|BLOCKED, not tested; allocation/route and enabled client both required|
|SIGNED_APK_OR_SERVER_ONLY_UPDATE|No new accepted update; distribute unchanged signed beta88 recovery APK only|
|IDENTITY_PRESERVED|PASS same APK/UID, same server identity/key bindings/Support ID, no re-enrollment|
|REMAINING_LIMITATIONS|Receiver receive/consume/ACK correlation absent; changed media sessions; no new overnight acceptance or production IPv6|
|FINAL_RESULT|PARTIAL, safe production restored; no accepted throughput fix or IPv6 PASS|

No commit/push/public release, mass distribution, FIELD stage or entitlement change.

## Subsequent source-control checkpoint

After the experiment, the owner separately authorized a local commit so the
accumulated source deltas, regression fixtures and sanitized reports can be retained
in Git. This does not accept the rejected throughput candidate or change the
installed beta88/gateway. Private build trees, APKs, raw exports, credentials and
databases remain excluded. No new runtime tests, deployment, push or public release
are part of this source-control operation. Existing test receipts retain their
original scope; a local commit needs a separately authorized push before GitHub
and its ChatGPT connection can see it.
