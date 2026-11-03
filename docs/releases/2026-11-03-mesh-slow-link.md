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

## Remaining gates, rollout and rollback

1. Build source-pinned Android ARM64 and gateway native artifacts with the existing
   pinned toolchains; run mandatory exact-source platform CI, including API27/API35,
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
