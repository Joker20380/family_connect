# Ready-write batching — local candidate,17 October 2026

Narrow derivative of the exact installed `admission1` source, not root main.
The [report](../../docs/releases/2026-10-17-transport-write-batching-1.md) and
[receipts](../../docs/releases/evidence/2026-10-17-transport-write-batching-1.json)
distinguish synthetic transfer timings, build evidence and absent phone acceptance.

## Product boundary

Apply `candidate.patch` only to retained client source inventory
`c1eade0110278827c1681438a80c0509f352e2c9174badef0d3b228cc7161e9c`.
Copy its five carrier files to retained gateway inventory
`0742212c5ebe38f9673dc53321d3af56c14b978e1080cbe104216ac21b40293f`;
do not replace gateway go.mod/dependencies with the client's tree.
`seal.py` asserts exactly six changed client files and five matching gateway files.
Two new test files are included in those counts; three carrier files change runtime.
The client build-version change keeps code84 and changes only the private name.
Full cumulative manifests preserve earlier native/recovery/admission/diagnostic work.

The Family method encodes existing length/sequence/payload messages consecutively,
under the same send lock, expiry, context and first-failure handling. No wire version
or peer capability negotiation changes. Legacy Recv parses each message separately.
At most32 already-ready messages and16,362 plaintext bytes are written together.
With TLS1.3 overhead22B this fits the default16KiB reliable payload; startup dynamic
TLS record sizing or smaller negotiated reliable payloads may still split records.
Mux data chunks become at most16,340B on a batch-capable local endpoint.

No aggregation timer, extra producer queue, intentional latency or raw-data bypass.
Existing control/data scheduling order is retained for the selected frames. A single
already-selected frame that does not fit is carried to the next write; new arrivals
do not jump ahead of it. Temporary encoded batch storage and one carried frame are
bounded; existing retained-byte counters are not redefined as allocator measurements.
Terminal removal waits for the actual terminal frame, not an earlier data frame when
its reset is carried to the next write. No stream-ID reuse or admission bypass.

## Reproduction and limits

Scripts are retained-workspace runners, not standalone production installers.
Set up their exact retained parent sources and offline tools first. `check.py` and
`verify.py` import the accepted bounded-runner functions from
`state-client-build/reliable-full-stack-1/run.py`; scripts fail rather than fetch
dependencies or contact a provider. Local loopback sockets require the normal test
sandbox permission. Every output directory is new; no retry-until-pass.

- `check.py OUTPUT baseline|candidate`: three Family-envelope samples, then selected
  candidate normal/race regressions. The initial wide race run failed an inherited
 15s fixture bound, preserved in `candidate-1`; do not call that run green.
- `verify.py OUTPUT baseline|candidate|gateway focused`: three real Family/TLS/mux/TCP
  latency and64-slot lifecycle fixtures; candidate/server targeted normal/race checks.
  Latency is synthetic40ms each way, reliable defaults unchanged, four concurrent
 64KiB streams echoed byte-exact. This is not RTP/provider/mobile throughput.
- `verify.py OUTPUT baseline|candidate heavy`: unchanged32-stream race fixture.
  The parent also fails its15s wall-clock bound at50% CPU quota.
- `verify.py OUTPUT baseline|candidate heavy-long`: one bounded comparison per side,
  changing only two test fixture clocks to60s via Go overlay. Both pass. Product
  deadlines and socket policy are untouched; original failed logs are retained.
- `verify.py OUTPUT candidate|gateway loss`: exactly two normal and two race runs of
  real Family/TLS + new mux with deterministic local packet loss/duplication. Three
 32KiB streams, byte-exact and positive retransmissions. No external fault injection.

Use `systemd-run --user --scope -p CPUQuota=50% -p MemoryMax=2G` for tests;
build uses4G, the same50% CPU cap, start<75°C and stop>=85°C. No emulator.
`seal.py`, then `bounded.py` run local native/JNI/Gradle/gateway builds with offline
dependencies; `check_artifact.py` checks unsigned APK metadata/alignment/payload.
`postcheck.py` preserves Gradle's regenerated HTML report outside the source copy and
restores the inherited nonproduct report before strict post-build inventory checking.
The initial rejection and failed missing-report check remain recorded; no input guard
is disabled and the built source inventory remains unchanged.
`publish_safe.py` copies source/tests and synthetic logs, not APKs, credentials or
raw owner data. Thermal samples and retained failures are part of the result.

This does not make idle64-slot saturation disappear. The fixture proves normal
half-close/reset release, not that all owner-browser keepalive states are harmless.
No claim about the causes of all37 overnight mux errors or all reconnects.
Next live step, if approved: verify exact installed pair, fresh material/runtime
readiness and ordinary-compatible backups, then coordinate a private paired rollout
and a small timed owner transfer. No automatic deployment, CONNECT, re-enrollment,
security maintenance, field trial, supervisor acceptance or public release.
