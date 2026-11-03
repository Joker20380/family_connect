# MESH-SLOW-LINK-1 — slow-link stability candidate

## Scope and state

Owner reports that MESH repeatedly disconnects at low speed. This selects link quality
ahead of the authorized but unfinished MESH2 integration. **SOURCE CHECKED; NOT RELEASED
OR DEPLOYED.** No handset trace was supplied, so these reproduced defects are plausible
contributors, not a proven explanation of every reported field disconnect.

Base source: `6afe7587c2ffe8795ffc59ce16a5103188df205e`.
Public Android remains `0.1.18-beta111`/code111/catalog6; Windows0.2.16/catalog12;
Linux public0.2.11 and owner0.2.12~l03.2.13. No keys, profiles, certificates, credentials,
assignments, product database, server policy, invitation pages or update catalogs changed.

## Reproduction and correction

- Pion `disconnected` previously immediately closed the entire carrier, even though
  Pion can recover the existing ICE connection. Both subscriber and publisher paths
  now retain an already-established session until actual `failed`/`closed`, cancellation
  or another existing terminal boundary. Before first establishment both peers must
  still be ready. Sends remain queue/deadline bounded, not a direct-network fallback.
- Explicit ICE5s disconnected/additional25s failed/2s keepalive settings preserve the
  dependency defaults. Transient state stays observable but does not become a false
  first failure. No provider reconnect or new conference is required for recovery.
- Fixed1s retransmissions previously exhausted eight retries at9s and repeatedly queued
  duplicate data behind slow useful traffic. ReliableStream now samples unambiguous
  negotiation/new DATA acknowledgements, applies smoothed RTT/variation and bounded
  per-block timeout backoff. Retransmitted/already-SACKed/duplicate/stale/invalid ACK
  observations cannot train RTT. Existing fast head-gap recovery and ACK refresh remain.
- Large configured windows begin with at most8 in-flight blocks, grow gradually on
  cumulative consumption, and halve once per timed-out flight. SACK does not free slots;
  shrinking never deletes outstanding bytes or restarts their age deadline. Original
  wire format, advertised window ceilings, buffer limits,20s default MaxAge and eight
  retry maximum remain. This is not unlimited waiting or a bandwidth guarantee.
- Android classifies correlated DATA-age exhaustion and either callback ordering of
  terminal peer failure as recoverable network failure. Authentication/revocation,
  malformed or uncorrelated diagnostics, protocol failures and cancellation retain
  their stricter handling. Recovery still uses the existing fail-closed orchestrator.

## Checks

Private local evidence: `state-client-build/mesh-slow-link-20261103/` (not committed).
All traffic and data used for these checks are synthetic; no provider token or live
user identity was used.

- Initial regression tests RED: transient subscriber/publisher/both teardown and
  a delayed ACK terminating at9s. Preserved in `red.log`.
- Identical serialized-link model against baseline engine and candidate:256/512/1000
  kbit/s forward, reverse one-quarter as fast,600ms propagation RTT,15% modeled framing
  overhead,1MiB deterministic payload,8/32 negotiated windows, with/without initial
  loss of every17th DATA block. Baseline fails12/12; candidate completes12/12 exactly.
  Baseline overlay includes both logical and physical checkout aliases. Candidate
  no-loss cases retransmit0 blocks; lossy cases retransmit4. This is a deterministic
  queue model, not a claimed Telemost bitrate or real-device benchmark.
- Backoff-only and RTT-only intermediate candidates did not pass all low-rate cases;
  their failed logs remain. Adding bounded initial/ACK-driven admission closes those
  model failures rather than merely extending deadlines or removing test cases.
- Actual Pion VP8 over an isolated virtual UDP router: byte-exact bidirectional media
  before/after two blackouts, real disconnected→connected transitions, then persistent
  loss→failed/closed. Uses accelerated500ms/3s/100ms ICE timers, not a production
  timeout-duration or external-provider qualification. No OS network/firewall changes.
- Exact dependency-selected Android carrier race command:669 test/subtest passes,
  45 explicit optional fixture/live skips, zero failures. Covers ReliableStream,
  Family TLS/auth/expiry, mux/stream quotas, whole-device, protected underlay, owner
  lifecycle, bootstrap/broker and cancellation. Also includes new estimator, congestion,
  hard-deadline, stale/invalid ACK, framing, persistent-loss and trace tests.
- Android411 debug +406 Friends JVM tests PASS; lint0 errors/56 existing warnings.
  Recovery rejects unrelated reasons and preserves first-failure/cancellation/auth guards.
- 66 focused Python product/correlation/boundary/Android/orchestrator/gap checks PASS.
- Existing retry-limit tests now advance by the backoff interval with a bounded custom
  age budget, still proving all eight retries. Actual framing uses100ms RTO/4s MaxAge
  to exercise the entire retry budget; separate default-config tests retain the20s
  absolute dead-path/unconsumed-data limit. No security gate or failed case was skipped.

## Native build and CI integration checkpoint

Source correction committed/pushed as
`55e872c161b0e95c9b7eb7290aae6ab8d0538e1c`; remote main matched that SHA.
Build source tree: `b0b9ba430a1ef5ff271eca80e058483a3a83506b`.

- ARM64 native library built with the existing Android builder, Go1.26.1/NDK28.2,
  approved Xray pin `d2758a023cd7f4174a5a5fa4ff66e487d4342ba0` and unchanged pinned
  gVisor. Manifest source revision/tree match; production tags, not diagnostic-only.
  SHA256 `10c6b7820675610003ff01135c74ec16d09cfb83f6dfc8bc13a4ba26c597264b`;
  all ELF PT_LOAD segments align to0x4000. Not packaged into a public APK or installed.
- Linux amd64 static `bootstrap-broker` built from the same source;
  SHA256 `289c351fb4bcc35e0d87947cc7d2a1d8ee5783677f363f42c4e6add507f7fe5f`.
  No server copy, service restart or profile-control pin change.
- Exact-source Readiness wire41659881609 and Client builds41659881608 FAILED in
  standalone JVM compilation: its explicit source list omitted `RestrictedGateway`
  and its `ReadinessBootstrapRoute` dependency introduced by the prior Android slice.
  Android native/API27/API35/release gates were NOT_REACHED, not accepted or skipped
  as successful. Windows and Windows compatibility jobs passed; the Linux job failed
  at deterministic normal-poll versus Disconnect interaction after earlier checks passed.
- phase0 run41659881651 FAILED in source-pinned release fixture provisioning and
  isolated failover stack build. Downstream tests were NOT_REACHED. These separate
  Linux/phase0 failures are retained; no unrelated code or mandatory gates were weakened.
- Added both missing JVM sources and their existing tests to the standalone module.
  Its187 tests and golden classpath generation PASS. Wire checking then exposed a
  stale two-argument ACK assertion; it now requires the selected gateway in both
  fresh-import and restored-import publication paths. No production ACK logic changed.
  With the locked Go toolchain and generated Java classpath,119 Python wire/handler/
  receipt checks PASS with zero skips. Initial failed logs remain in private evidence.
  This locally repairs the CI prerequisites; a new exact-source CI run is still required.

### Follow-up contract qualification

Standalone source-list/ACK-guard repair committed/pushed as
`ed54f3311930bc822489f4597f7d53f17bc28beb`; remote main SHA verified.
Readiness wire41668105208 PASS. Client builds41668105524 passes JVM/native race,
then stops in `Restricted diagnostic and readiness contracts`: the exact-hash guard
still expects six handlers before the node-scoped readiness change and recovery before
the low-link correction. The reviewed deltas retain primary storage/wire compatibility,
gateway-bound acknowledgements and protected readiness, and add narrow network recovery.
The guard now pins these seven exact reviewed source hashes instead of excluding files
or computing expected hashes dynamically.260 matching diagnostic/readiness/release
checks PASS;2 Windows-only tests deselected exactly as in Android CI. No UI/runtime
acceptance is inferred from this reference update; API27/API35 are still pending.

Stronger bidirectional wall-clock Family TLS qualification is in progress. The first
256/64kbit/s run exposes a remaining startup-flight failure not covered by the earlier
one-way rate model. Its failures remain evidence; no new gateway/client runtime is
qualified for rollout while that correction is under test.

## Remaining gates, rollout and rollback

1. Local source-pinned Android ARM64 and gateway builds passed as recorded above.
   Run mandatory exact-source platform CI, including API27/API35,
   native alignment/provenance and existing identity/storage/lifecycle checks.
2. Exercise mixed deployed/candidate peers, real Family TLS/DNS/HTTPS at bounded low
   rate/loss/latency and normal throughput. Check repeated loss, cancellation, lifetime,
   revocation and cleanup; preserve evidence for failures. Rates below256kbit/s, long
   outages and the affected handset/provider path are not qualified here.
3. Promote the gateway candidate only with source/profile-control pins and a retained
   accepted binary/manifest rollback. Both endpoints benefit from their own sender
   correction; a new client alone does not repair an old gateway's downstream sender.
   Do not alter renewal authority or service users to get a binary accepted.
4. Deliver a new immutable Android version above111 with the existing offline signer,
   catalog sequence above6 and verified APK/catalog/invitation bytes. Never replace111.
   No production mutation has occurred, so no runtime rollback is currently required.
   A source rollback can revert this logical change without touching user data; after
   a release, restore accepted gateway artifacts and use a new signed forward version,
   not re-signed/replaced historical APKs.

MESH2 production renewal/runtime remains deferred, not accepted or silently resumed.
