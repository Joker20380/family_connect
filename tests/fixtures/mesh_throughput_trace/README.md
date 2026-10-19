# MESH receiver / sender correlation — 19 October 2026

Scope: the owner's ordinary production-compatible observation authorization,
starting at pushed `76df691` and accepted beta88. No PERF-3B, owner guard,
diagnostic enrollment, new identity, canary routing, authority/admission migration
or intentional production fault. Amsterdam IPv6 is DEFERRED_BY_OWNER; SPb NOT_RUN.
See [results](../../../docs/releases/2026-10-19-mesh-throughput-trace.md).

## Exact sources, not a main checkout

- `prepare.py` exclusively copies the sealed accepted gateway inventory, checks
  the previous `mesh_perf3/accepted-overlay.patch` inventory, then applies
  `receiver-trace.patch` with input/output hashes and zero fuzz.
- `prepare_android.py` exclusively copies sealed beta88 and its build ancestry,
  then applies `android-trace.patch`. Android-specific native differences are
  preserved. `source-inputs.json` pins the inputs, outputs and immutable artifacts.
- `MESH_TRACE_OUT=/tmp/<new-directory>` selects an exclusive reproduction area.
  Neither preparer patches the working main tree, installed binary, or an already
  modified source capsule. Missing sealed sources are an explicit prerequisite.
- `build.py` uses retained offline Go/NDK/JDK/Gradle dependencies. The private
  research gate permits only `fc_perf_diagnostic`; ordinary public builds and
  owner/fault-injection tag restrictions remain intact. This is not CI acceptance.
- Code89 is already built, signed and installed. **Do not replace its APK with
  different bytes.** `sign.py` uses the existing local vault workflow, never
  prints secrets, and verifies the same package/signer. `upgrade.py` uses only
  `adb install -r`; it never disconnects, uninstalls, clears data or enrolls.

## Observation and interpretation

The bounded512-point ring uses an actual Go monotonic origin and a separate wall
anchor. Correlation is `(session_tag, hash(ordered RS epochs), sequence)`; ordered
epochs encode direction and distinguish reused sequence numbers. Initial send,
all observed retry attempts, receive result/head/buffer, ready head, consume,
ACK reason/enqueue/local media-write, accepted ACK/base/released bytes are distinct.
Local ACK tokens never become cross-node identifiers. ACK base/mask can match
several generation events. No cross-node clock subtraction or RTP/SSRC equality.

`PerformanceExportProbe.java` exercises native JSON -> the actual compiled Java
projection -> ordinary DiagnosticRing export -> chunks. It also checks full512
points, retained histories and ring+incident export bounds. The live path uses
existing JNI health snapshots and `FamilyConnectPerf` logcat chunks, outside
transport/state locks. Legacy `restricted_trace` events remain separate.

`capture.py` binds NL journald to one invocation and captures Android's perf tag.
Checksum-bound1800-byte chunks avoid journald's49152-byte fragmentation. The first
captures used32MiB/node; the return capture uses64MiB/node, still bounded, with
cap checks before starting another request. Raw logs/errors stay protected locally.
One truncated **legacy** diagnostic record in the rejected candidate capture is
retained as a parser error; its70 perf snapshots reconstruct completely. Do not
hide this error or claim all legacy trace context is complete.

`correlate.py` preserves overwrite/prefix/interior gaps, initial sends and ACK
local-write events. Missing events are not packet loss or zero delay.
`analyze.py` summarizes local intervals, overlapping window/Mux counters, and
distinct observed streams. Missing counters remain unknown, not zero.
`localize.py` extracts conservative same-node evidence that non-head holes met the
existing three-later-SACK and RTO/4 guards before their timeout retry.

```sh
python3 -m unittest discover -s tests/fixtures/mesh_throughput_trace -p 'test_*.py' -v
python3 tests/fixtures/mesh_throughput_trace/correlate.py \
  --nl /private/capture/NL-raw.jsonl --android /private/capture/Android-raw.jsonl \
  --output /private/new-correlation.json
```

## Physical method and rejected candidate

`measure.py small` gates bulk on one valid64KiB Android-TUN request, same logical
DATA on both sides, process-attributed NL socket, intact export and stable TUN.
`baseline` alternates single2MiB / parallel2×2MiB twice, with phone-side curl body
read/hash, HTTP/1.1, fresh connections, identity encoding, no endpoint retries and
150s/request. Parallel uses the shared phone uptime interval. First endpoint or
request failure stops further cells; no rate-limit bypass. Observed Cloudflare
hashes are not independent origin hashes. Background phone flows remain possible.

The single functional candidate is **REJECTED**, not part of baseline:
`sack-holes.patch` removes only the head-only fast-retransmit guard. It preserves
three later SACKs, RTO/4 age, one fast retry, all protocol/settings/memory/consume
bounds. `prepare_candidate.py` reproduces its exact inventory from the observation
tree and `candidate-source.json`; `sack_holes_test.go` fails on baseline and passes
after the change. Deterministic local checks are not physical acceptance.

Its physical single slowed and parallel ended with retry exhaustion; the return
baseline passed all six requests. Different media sessions prevent attributing
the whole difference uniquely to the patch. There is no accepted throughput fix.
Do not automatically apply this patch, or the earlier rejected read-alignment patch.

## Rollout, rollback and private artifacts

`rollout.py` and `candidate_rollout.py` reuse hash-pinned ordinary19October guarded
switches: fresh TLS/runtime/expiry/floors, RU coordinator/NL node locks, exact unit,
argv/profile, backup, atomic replace, same-service restart. They preserve renewal
and credential history. A restart can interrupt sessions. A guard refusal or
unknown result requires readback, not blind replay or disabling the guard.
The candidate's first attempt stopped during normal renewal before any NL mutation;
the recorded resumed attempt followed unchanged PID/hash/profile/no-intent readback.

The candidate was rolled back to observation, then observation to original4b722d.
Those transitions are already recorded and must not be blindly repeated. New work
requires fresh scoped staging/receipts and current runtime checks, not reuse of old
credentials or reset of security history. `final_control.py` checks the accepted
gateway/beta89 identity and one ordinary process-attributed DNS/HTTPS probe.

The private APK is **observation-only**, not an accelerated release:
`state-client-build/mesh-throughput-trace-20261019/delivery/FamilyConnect-0.1.18-beta89-mesh-trace.apk`.
Its SHA256 is `b6ab744740726676dca8f51a73460db82b435c719828af14e6564c764ed11856`.
No public release, push, mass distribution or updater-catalog change. Existing
beta88 delivery is not held for this investigation. Android observation can be
removed by a normal same-signer/package build with code>=90; never downgrade89 or
clear app data. Keep all source capsules, raw exports, profiles, DB and keys private.
