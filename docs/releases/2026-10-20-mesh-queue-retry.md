# MESH local send completion / retry control — 19–20 October 2026

All operation/measurement times below are UTC19 October; the work crossed local
midnight20 October. Repository checkpoint remains
`dddc3347db5b02896c123488f2e5e0292ff2b7a7`, main, matching the configured Family
Connect origin. Current1011 sources are a separately sealed local delta, not a
clean checkout of that commit. No reset, merge, push, public release or APK change.

**Result: local queue/retry bug confirmed; physical speed fix NOT accepted.**
Explicit independent classifications: **LOCAL_CORRECTNESS_FIX_VALIDATED**;
**PHYSICAL_SPEEDUP_NOT_ESTABLISHED**; **DEPLOYMENT_NOT_ACCEPTED**.
The single candidate completed six bulk bodies, but the return A control does not
show repeatable improvement across both parallel cycles. Exact current1011/beta90
is restored; no functional performance candidate is left in production.

## Current baseline and experiment scope

Owner beta90/code90 remains installed, package `com.familyconnect.app.friends`,
UID10283, same signer/data/identity. APK:
`state-client-build/tunnel-restart-20261019/delivery/FamilyConnect-0.1.18-beta90-stability.apk`

- APK SHA256 `68cbcccfb5adf8656e8203436126330e780de099670ee2031d71019baadc3e9a`.
- Restricted native SHA256 `dd722eada0da7c890a8d71a72099cba5d0bbac1ce73377bbdbc8e7b85d820c23`.
- Existing signer SHA256 `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
- Current1011 gateway SHA256 `b9ae880731517753e456637e52dcc421b9f7d7b881b400c856989ae93193e9ba`.
- Accepted current1011 inventory `4722b7353ba93209657f66b45c47874915362f1fbe732845ec61745abdb673e6`.

Entry readback21:24:39: actual `/proc/3294035/exe` matches b9, invocation
`6a5edd64110544f18124e4d493fad2e3`, active/NRestarts0; phone PID19388/code90 and
APK match. Source, immutable baseline binary and parent receipts copied before
editing. Existing unrelated/local task changes preserved. **Old4b is not rollback
for this task**: it would remove the accepted bootstrap1011 fix.

Temporary observations and functional candidate are server-only. Phone's extended
beta89 performance trace stays OFF. No health/recovery, all_activated, credentials,
authority, admission, floors, window, MaxRetries, RTO, Mux-credit or pacing changes.
No tester dependency, PERF-3B, canary, deliberate production faults or new Connect.
Amsterdam IPv6 stays DEFERRED_BY_OWNER; SPb NOT_RUN; no hosting work.

## Hypothesis and reproducible mechanism

The historical beta87 export18 is preserved privately, SHA256
`e5120b313542f99edb1baacd8b636b6a591577ad22380c8b4327f6973ef3fb76`.
In its d3252d… session, DATA2685 attempt8 was enqueued at1792428473287ms, before
attempt1's successful local write at1792428474821ms. Attempt labels come from the
immutable queued frame, not a later lookup of engine retries. **Attempt1 means
first retry, not the original attempt0**. The old ring alone cannot establish
that all intervening attempts were concurrently pending.

The same mechanism is reproduced on exact current1011 source. `engine.send/tick`
starts/updates timeout and retry accounting before carrier local write.
`Session.SendContext` returns after putting fragments in sendQueue; the existing
separate transmit worker then looks idle while `writerLoop` may still be blocked.
There is no remote-ACK wait in SendContext. Incoming ACK handling was already in
another event loop; a full carrier queue does not directly block its reader.

Actual bound Pion VP8 fixture, local RTO30ms and held RTP writer340ms:

| Before release | Exact baseline | Completion candidate |
|---|---:|---:|
| Attempts for one logical DATA, before any local RTP write |9|1|
| Retries consumed |8|0|
| Queued fragments, including control |35|2|
| Actual RTP writes |0|0|
| Terminal state |recovery_exhausted|none|
| Complete byte-exact delivery in strict counted test |failed|passed|

Baseline strict test times out without complete delivery; the early logical send
return is not successful useful delivery. Candidate completes16KiB in0.348427s
including the synthetic hold (~0.376Mbit/s). Before release both have zero goodput.
This is a local mechanism test, **not a physical speed acceptance**. Neither test
changes production RTO or injects a live fault. Earlier prototype/results retained.

## Targeted candidate

The `localwrite` completion is per context/session/attempt. Carrier registers the
fragment count; writer marks WRITING and completes after the final local write.
ReliableStream waits in its existing transmit worker, leaving ACK input, consume
and cancellation responsive. It updates `last` only if the original pending-block
pointer, sequence and attempt still match and the block is not SACKed/released.

An ACK cancels obsolete not-yet-started work. A started multi-fragment message is
not truncated on ACK; completion or the existing finite queue/write/session limit
ends it. Queue + write is bounded by min(MaxAge,2s) from local submission, rather
than a fresh allowance after arbitrary local waiting. No SACKed positions are
freed early. Memory/backpressure remain bounded. Legacy endpoints still work;
wrappers retain their original SendContext interception. No wire/crypto change.

An initial optional-method prototype was replaced locally because an embedded
method could bypass wrappers' SendContext overrides. It was never deployed.
No read-alignment or SACK-hole patch is included.

## Local checks and evidence handling

- Instrumented A:533 Go race cases PASS,26 opt-in SKIP across7 affected packages.
- Instrumented B:543 Go race cases PASS,26 opt-in SKIP across8 affected packages.
- Default candidate's original full run exposed a missing test-only
  `FC_EXPECT_SEED_OBSERVABILITY=1`, not a changed1011 decision. Failed log retained;
  correct accepted test setting applied, affected seed package rerun PASS.
- Additional default localwrite/reliablestream race suite PASS, including incoming
  real ACK releasing base while the next retry waits locally. Queued copy does not
  start;12 subsequent16KiB bodies are exact; one actual sent-DATA retry remains.
- Existing loss/reorder, slow consumer, bounds, cancellation/exhaustion and1011
  regressions retained. Partial-message, obsolete queued attempt, cancelled/late
  completion, reused registration and legacy endpoint checks PASS.
- A separate test-only copy passes three consecutive stalled partial-write
  deadlines, cancellation/cleanup and late completion into later generations.
  Each uses a150ms deadline/500ms assertion bound without consuming retry budget.
- Three hash-pinned overlays reproduce full target inventories on fresh copies.
  See [fixtures](../../tests/fixtures/queue_retry/README.md). Not patches to main.
- Android source/APK unchanged: prior169 JVM/10 health/6 PC results are inherited
  evidence, **not newly executed physical recovery acceptance**.

The first raw baseline collector failed with an escaped-newline SyntaxError;
request results are retained but have no new server counter attribution. The next
collector's placeholder substitution damaged `_SYSTEMD_INVOCATION_ID`; its
pretraffic check stopped before requests. Both errors were fixed and retained.

A1 then captured52 valid chunked performance snapshots, but the original16MiB
journal cap was exhausted at a large legacy diagnostic message. Collector shutdown
also hit its wait timeout. A single bounded85s journal read around the failure
reassembled that diagnostic by invocation/stream/PID. No broad journal rescan.

Collector now uses compact journal fields, max64MiB/600s, bounded termination,
explicit incomplete/error accounting and checked per-stream continuations. Two
continuation tests PASS. No global journald settings changed. B captures59 complete
performance snapshots without parser errors/cap. Its512-event rings still have
5194 interior missing indices and665 unobserved prefix: missing events are not
zero delay/no loss. Counters and point coverage are reported separately.

## Physical owner comparison

Phone-side HTTP1.1 fresh connections, identity encoding, continuous body read;
Cloudflare2MiB, then two concurrent2MiB requests. Setup/TTFB included. Parallel
uses combined bytes divided by phone common monotonic wall interval. No body
streaming over ADB, no independent origin SHA claim. Same phone underlay321;
media sessions change with binary transitions. Failed requests remain in totals.

| Variant / session | single Mbit/s | parallel aggregate Mbit/s | Result |
|---|---|---|---|
| Current1011 raw baseline |0.592|1.318|all bodies complete; collector failed|
| A1, matched observation |0.222|not complete|both parallel bodies reset|
| B initial pre-READY smoke |not run|not run|DNS failed;0body bytes; bulk NOT run|
| B after confirmed natural READY |0.535 /0.919|1.034 /1.133|six full bulk bodies complete|
| A2 return control |0.526 /0.665|0.977 /1.176|six full bulk bodies complete|

A1 single TTFB2.514s/full75.551s. Failed parallel bodies154,611 and235,740bytes,
curl56 after~69.6s, not successful2MiB samples. Actual gateway Cloudflare TCP
connections are one for single/two for parallel; Mux has additional background
streams, not an assumption that HTTP request count equals all active streams.
B singles TTFB1.811/1.276s, full31.333/18.254s. B parallel wall32.45/29.62s.
The pre-READY failure is not discarded: B's dedicated session is established only
at21:59:15UTC, after the21:58:04 probe. No operator Connect was used.

A2 single TTFB2.048/2.348s, full31.895/25.225s; parallel wall34.33/28.54s.
B vs A2 parallel is +5.8% then −3.6%, not a repeated win. B's two singles are
~+1.8%/+38.2%, but one faster single/new media session is insufficient against
that mixed result and raw-baseline variability. A1's exhaustion is not attributed
to a bug fixed by B merely because B/A2 happened not to exhaust.

B has six distinct large Mux streams13/25/27/33/37/39, each with~2MiB handed;
A2 has31/37/39/43/49/51. Parallel peak observed Cloudflare sockets is two.
Some A2 intervals also see a residual/other socket, so total unique socket tuples
can exceed the two simultaneous test connections. Background flows are not hidden.

## What limits the measured intervals

Local bug is proven, but it is **not observed as the dominant A1 physical cause**:
615 matched attempts have queue→last local write median5.79ms, p95 24.85ms,
max42.23ms, well below the production1s RTO. No overlapping completed attempt
spans for one logical DATA are observed; incomplete rings prevent a universal
absence claim. B's1366 matched attempts: median2.97ms, p95 7.97ms, max12.22ms.
A2's1378: median5.61ms, p95 28.88ms, max61.19ms; again no observed simultaneous
complete attempt spans. A2 has6047 interior trace indices missing/4159 prefix
unobserved, with66 complete snapshots and no parser/cap error. Cumulative counters
remain separate from this bounded per-event loss of coverage.

A1 head DATA597 has original attempt0 plus retries1–8, all with successful local
completion, each before the next retry. Its first close at21:53:39.146UTC is
RELIABLE_RETRY_EXHAUSTED, not queue exhaustion/health1011: base597,next605,
mask220,head not SACKed, age9421ms, ACK age6296ms, no base progress8159ms. Then
FAMILY_TLS_ERROR and gateway-session cleanup. Gateway PID/invocation remain alive.
This local write proves neither SFU delivery nor Android receipt. Exact forward
DATA vs reverse ACK loss remains unknown without receiver evidence.

A1 ready-full stall delta61.51s, head-unconfirmed/later-SACKed53.55s, Mux
zero-credit-ready62.72s. B:74.27s,34.27s,116.51s over a larger completed transfer.
These layer waits overlap; do not sum them. Retry/new DATA byte deltas A1:
2,334,740/2,710,713; B:2,146,162/12,829,472. Background traffic and snapshot edges
are included. Less retry work alone is not speed acceptance.

A2 has73.75s ready-full and33.63s head-unconfirmed/later-SACKed waits, with
125.95s summed per-stream Mux zero-credit-ready time (parallel/overlapping, not wall
delay). Retry/new DATA bytes1,852,414/12,814,717: B does not even consistently lower
retry bytes against the return control. Most missing useful progress is after
local send, not a demonstrated local queued-copy storm in these physical runs.

Server CLK_TCK100. Captured CPU: A1 5.51CPU-s/102.62sample-s (truncated capture),
B 6.91/117.99 (~5.9% of one core), A2 7.54/131.23 (~5.7%). Peak RSS A1/B/A2:
41,484/41,600/43,800KiB. This is not a matched instrumentation off/on overhead
measurement. A/B use identical counters; no evidence attributes the loss to trace.

## Artifacts and current decision

All binaries are under `state-client-build/queue-retry-20261019/`:

| Artifact | SHA256 | Use |
|---|---|---|
| `gateway-baseline` |`b9ae880731517753e456637e52dcc421b9f7d7b881b400c856989ae93193e9ba`|preserved current1011 fallback|
| `gateway-observation-queue` |`79d9c8c58676d5af7ebff78fd780009d98e468e6dcafbdc47e48de755bd16f86`|A temporary matched observation|
| `gateway-candidate-observed` |`55f329b4c144df5390eb1485cec75e808492fb4053319ccc5276fa17a8931b02`|one functional B tested|
| `gateway-candidate` |`fb3f416d9fc2d23bbce949856c3394a70bcc6d2774c74dc0e3d2e28f9c81f958`|normal-tag candidate built, NOT installed|

Inventories A `f83f8c31809f9c05fe3b56fe539d108cac3c25c80265602e523a91e3ddd02831`,
B observed `9a41cabd57298b019a20903dcfdb6eabc00ebe1dd998203e10b908df46155d28`,
B normal `f3c3b3bd6a95387b5549c83609e468cd0a00663870367cd49a64482d5505cf7b`.

Candidate **REJECTED FOR SPEED SHIPMENT / improvement not established**. Keep the
patch/test/evidence as a proven local robustness mechanism, not an accepted speed
fix and not a default overlay on the baseline. The normal-tag candidate is built
but never installed. No APK91 was made or required. No phone data, ID, keys,
Support ID, registration or user access were changed.

## Transitions, restored runtime and remaining fact

- A observation loaded21:46:04UTC, PID3375268/invocationf055d519….
- B loaded21:57:29, PID3382698/invocation2aab99ec…; measured bodies end22:02:00.
- Normal scheduled renewal then restarts B22:02:46 with genuinely new materials,
  transaction `scheduled-1792447349-c585581b1950ca71`. It is not a spontaneous
  candidate crash or a reused deployment intent. No renewal was disabled.
- B→A return22:03:03, PID3387107/invocatione0594752…. First readback catches stale
  publication; a later read-only check times out. No mutation is repeated. Basic
  PID/port remains live; fresh22:08 strict readback passes with current credentials.
- Initial A-return64KiB completes but TUN changes0→1 with unchanged underlay321;
  bulk is stopped. A2 starts on the new stable TUN, not across that boundary.
- A→exactb9 return22:13:17, PID3393714/invocation6a5fc20d6b5b43de82d0612f7c5ccb01,
  NRestarts0.22:14:02 strict TLS/runtime/publication and22:14:04 actual executable,
  APK/native/code90/UID10283/PID19388/VPN readback PASS. New profile hash
  `3bce05fc3f1aa40b3f173332ffc76c65acd06b0231f4d8eb72196c8e59f91f31`, expiry
  02:02:34UTC20 October, is preserved. No security-history rollback.

All operator transitions use fresh ordinary intents, locks, hash guards and short
same-service restarts. These interrupt sessions. Recovery observations/first
successful connection are not repeated-fault or overnight acceptance. Android's
desire-to-connect, cooldown, one-worker discipline, manual Disconnect/revocation,
strict auth and no-leak behavior are not modified. No intentional outage tests.

Requested bulk+smoke caps24.25MiB baseline and12.125MiB candidate,36.375MiB total;
actual body bytes34,272,463 before the final <=4KiB control. All failures count,
including the pre-READY DNS failure. Original150s/request bound retained.

### Final phone control and observed gap

The first final small HTTPS control22:14:50 returns DNS error6/zero body bytes.
The bounded retained server journal shows new dedicated-family READY only at
22:15:14.247; this first probe preceded it. The legacy helper's302 socket-sample
matches with an empty remote IP are **invalid attribution**, not a passed check;
the helper wrapper now rejects an empty destination before matching sockets.

The attempted ready recheck stops **before any HTTP** because Android reports no
VPN/TUN. Seven passive reads22:18:36–22:19:06 all report0 VPN interfaces. No Connect,
uninstall or data clearing is performed. Cause of this final TUN disappearance
(owner action versus another lifecycle event) is not established from available
evidence. That interval is not called successful restoration or blamed on the
removed candidate. Owner was asked to enable MESH normally; no agent Connect.

Fresh22:19:43 readback sees TUN again, same90 APK/native/PID19388/UID10283 and
exactb9/PID3393714. **Final22:21:08 small control PASS**: DNS, verified HTTPS1.1
HTTP200,211bytes/full3.964s, expected NL exit and21 matching current-PID socket
samples. Temporary phone files removed. No further owner action is required.
This proves current small application transfer, not sustained stability or the
cause of the intermediate no-TUN interval. Both earlier failures/gates remain.
Including both final4KiB allowances, conservative comparison cap is36.383MiB;
actual received application body bytes are34,272,674.

## Result fields

| Result | Outcome |
|---|---|
| CURRENT_BASELINE |Exactbeta90/current1011 b9 verified and restored; final small transfer PASS.|
| QUEUE_RETRY_HYPOTHESIS |CONFIRMED locally; NOT observed as dominant physical limit in captured attempts.|
| TARGETED_CHANGE |One server completion/cancellation candidate implemented, tested, compared; NOT shipped.|
| BEFORE_AFTER_GOODPUT_AND_FAILURES |Full A/raw/B/A-return table above; failed bodies, DNS and no-TUN gates retained.|
| STABILITY_AND_IDENTITY_PRESERVED |No client/identity/security mutation;1011 retained. Intermediate no-TUN cause unknown; no overnight stability claim.|
| APK_OR_SERVER_ARTIFACT |No APK. Final b9 plus exact candidate/observation paths and hashes above.|
| REMAINING_EVIDENCE |Receiver-side fate of the same naturally repeated head/return ACK remains unobserved.|
| FINAL_RESULT |No repeatable physical speed acceptance; current1011 restored, temporary performance trace OFF.|

[Sanitized machine-readable evidence](2026-10-20-mesh-queue-retry.evidence.json).

**Remaining distinguishing fact:** did the same natural retried head reach
Android carrier completion/consume, and did its ACK reach NL? Current90 has no
expanded receiver trace. A short paired observation of those particular events,
with current1011 unchanged, distinguishes forward media loss from reverse ACK
loss; this report does not choose one or propose blind window/pacing/SACK changes.
No background experiment remains. No claim of tester-whitelist speed improvement.
