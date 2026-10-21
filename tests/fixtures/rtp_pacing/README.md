# RTP packet-pacing fixture (offline by default)

See `docs/releases/2026-10-20-rtp-packet-pacing.md` for the decision and limits.
Local tests do not deploy, sign/install an APK, start collectors or run bulk.
`readback.py` performs bounded read-only ADB/SSH checks; optional `candidate` selects
the sealed candidate hash. Do not run it as a speed measurement.
`rollout.py` now wraps the existing serialized ordinary gateway transition with fresh
receipts and exact source/binary pins. Owner-authorized deployment completed once;
do not replay its stage/deploy intents. `policy.py` uses the existing protected
operator directory for owner-only new-session modes; CHECK is read-only. Neither
helper injects phone input or waits for manual action. Runtime checks require normal
host/network permissions. No APK operation or load generator is added.

## Source and reproduction

- Accepted compatible source: `state-client-build/mux-profile-20261020/gateway-source/carrier`;
  full `negotiated-build.json` inventory, not current GitHub/main.
- `prepare.py`: verifies exact96 APK/Android inventory and compatible gateway
  inventory; creates baseline/candidate capsules once; refuses existing destination.
- `queue_prerequisite.py`: explicit rebase of separately preserved completion patch;
  handles three instrumentation conflicts, saves resolution evidence. Not a live fix.
- `packet-pacing.patch`: **final complete delta**, including scoped prerequisite,
  new pacer, actual integration, exporter and negative tests. Apply this to the
  accepted source directly, not after applying the prerequisite a second time.
- `reapply.py`: copies accepted source to a new capsule, checks/applies the final
  patch, verifies all268 source files against sealed inventory and repeats targeted
  race tests five times. Refuses an existing `reapplied` directory.
- `run.py`: pinned Go/dependency caches, `-race -tags=fc_perf_diagnostic`, unique
  JSON logs; uses local bootstrap test vectors. Loopback test restrictions require
  normal outside-sandbox execution, not altered transport tests.
- `benchmark.py`: unique non-race observation-overhead log.
- `seal_build.py`: validates final logs/protected sources, freezes patch/inventory
  and builds gateway with `-trimpath -buildvcs=false -tags=fc_perf_diagnostic`.
  Already completed; do not overwrite its sealed receipt or binary.
- `close_test.go`: extra full256-frame Session.Close test injected into reproduced
  source after inventory equality check, then run ten times with race. This fixture
  does not change the sealed candidate binary. Its retained log is separately hashed.

All outputs: `state-client-build/rtp-pacing-20261020/`; exact artifact references
in `build-result.json`, plus entry/final readbacks and `reapplied-result.json`.
The original queue patch/manifests and earlier failed setup logs remain intact.

## Scope of modes

OFF retains old completion behavior; no pacer or new histograms. OBSERVE and
FIXED4M both use scoped actual-local-write completion and identical counters.
FIXED4M alone adds500000 RTP bytes/s pacing. Thus new A is not the exact old Q0:
local Q0/Q1/P1 fixtures distinguish the mandatory prerequisite from smoothing.
Unselected/seed sessions remain OFF. No packet/window/RTO/codec/receiver changes.

The candidate uses existing protected operator-directory parsing for `rtp-pacing`
and `rtp-pacing-target`. Target is the first16 SHA256 bytes of the **authenticated**
identity public key, lowercase hex; not a grant or Support-ID authentication.
Files are operator-owned, permission/size/symlink checked, read at session creation.
After explicit owner coordination, candidate loaded once; all A1/B1/B2/A2 phases
are now complete. Fixed4Mbit/s NOT_ACCEPTED; manual return confirmed in new VPN342:
OFF/Q0, LEGACY64/65536, counters OFF. Target has32 bytes with no newline. Do not
change a live session's interpretation. See `manual-return-result.json` and its
runtime/source proof; no repeated load, build/deploy or old transition-intent replay.
No further manual action remains.

`measure.py PHASE READBACK_NAME` adapts the unchanged accepted phone HTTP/1.1
request and bounded Mux/RS collector to control64KiB/single4MiB/parallel2×2MiB.
It requires a fresh exact-binary readback/new VPN, gates actual owner rate/profile
before requests, reserves the phase against64MiB, and disables export in finally.
`summarize.py PHASE` is offline: raw phone times, bracketing monotonic counters,
stream-set attribution, background bytes, RTP/RTCP and resource scopes retained.
`test_phase.py` checks wrong mode/window/tag and stale-snapshot rejection offline.
All four phases complete,32.25MiB. Do not run `measure.py` again for return. Latest
receipts are `manual-return-result.json`, `return-off-contract-proof.json` and
`return-off-runtime-proof-complete.json`; pre-return receipts remain historical.
New VPN342 actual OFF/Q0/LEGACY64 is confirmed without bulk/control requests.
Export/collectors OFF; no INJECT_EVENTS or waiting for an unannounced tap.
Bounded journal reassembly requires `--all` to preserve long MESSAGE values; a
default projection omission and broad-query timeout were repaired by reading
the existing short window, not by re-enabling export or repeating traffic.

## Evidence limits

Synthetic payload and real bound Pion tests establish byte exactness locally;
they do not establish physical delivery or a particular SFU queue capacity.
Fixed bins are not sliding windows. Local WriteRTP/Write bytes are not SFU receipts.
The modeled shallow queue is an assumption. Local fixed cap is not adaptive CC.
Do not compare lifetime stats to request-local stats, count same-SSRC retransmissions
as necessarily RTX, or claim all external wire overhead from RTP counters.
No payload, keys, proof, signed credential contents or room URL should enter logs.
