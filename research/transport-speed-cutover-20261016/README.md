# Combined speed/restoration candidate — reproducible local scope

See [report](../../docs/releases/2026-10-16-transport-speed-cutover-candidate-1.md).
No APK, executable, signing key, real credentials or raw device evidence is published.
Publication Git SHA, cumulative inventories and binary hashes are different identities.

## Sources and fixtures

`candidate.patch` applies to retained UI60-4 inventorye90893ae, not root main. It
combines the previously verified Java recovery and ReliableStream engine changes,
their existing tests and a distinct versionName/code84. `seal.py` verifies the exact
changed-file set, unchanged remaining sources and a patch round-trip. The source
base remainsf5240994869826c6a28f59e58e38256c688cf6eb; the cumulative inventory lists
the retained deltas relative to that base. Never replace the source with beta60.

Gateway source is independently derived from retained inventory72274642. Only its
`reliablestream/engine.go` is replaced by the exact tested client engine. The result
is enumerated in `gateway-source.json`. No client-only bootstrap diagnostics or UI
files are transplanted to the gateway.

`full-stack/prepare.py` copies the previous private baseline/candidate carrier trees
and extracts the existing `testCredentials` fixture from `tcpforward/integration_test.go`.
It adds only the three listed test/adapter files. `full_stack_test.go` uses the existing
local Pion adapter pattern; `fixture_dns.go` substitutes only the local DNS upstream.
It is never copied into either final product tree. Source boundaries are checked by
the summarizers, not assumed from test results.

`run.py run-2` compiles separate baseline/candidate peers, runs four combinations and
three scenarios, normal count2/race count1. `prepare_gateway.py` checks the retained
gateway manifest before adding the same adapters to baseline/engine-only copies.
`run_gateway.py run-gateway-1` reuses client binaries fromrun-2 but compiles actual
gateway-derived peers. Both sides differ genuinely by compiled engine bytes; a test
boolean is not used to emulate an old peer. This supplement has normal1/race1.

`summarize.py` and `summarize_gateway.py` verify byte-checked completion, exercised
faults, real RTP evidence, eight matched synthetic DNS replies per side, no mux
protocol/DNS errors and unchanged original product sources. Final results contain
36+24 successful cases. The earlier fixture-context failure is retained separately
in `validation-history.json` and `full-stack/run-1-receipts.json`.

The final runner stops after the first failing command; repetitions are fixed in
advance. Original failed run1 used two scheduled repetitions before command exit,
not an unbounded retry loop. Its failure did not trigger a product policy change.

## Bounded execution

Stage scripts beneath the original private task directories (`reliable-full-stack-1`
and `transport-speed-cutover-1`) next to their retained inputs. `prepare.py` in the
combined task copies the verified recovery source and engine/tests; apply the
versionName delta from `candidate.patch` before running `seal.py`/`build.py`. No old
artifact is overwritten. Existing directories/output logs fail exclusive creation.

Use the retained Go1.26.1/JDK17/NDK28.2/Gradle8.11.1 toolchains and offline caches.
The runner uses GOMAXPROCS1 and serial builds. Launch one runner at a time under a
user systemd scope with CPUQuota50%, MemoryMax3G and TasksMax160. It refuses a start
at75°C, terminates its process group at85°C, and enforces finite time limits.
No emulator, privileged network change, provider session, SSH or ADB is involved.

`build.py` performs normal ARM64 native compilation, full researchProvisioning
assemble and the97 targeted JVM checks from the recovery candidate, then generates
JNI headers/checks the C bridge and builds the separate Linux gateway candidate.
It retains the existing cumulative-source/provenance guards. The native build uses
the accepted pinned Xray patch and existing gVisor dependency; no diagnostic build
tags or new dependencies. The manifest contains the actual runner digest/receipt
as well as the unchanged product producer identity. A legacy verifier output named
`native_reused` must not be read as proof of unchanged bytes: this candidate rebuilds
the engine and records its new embedded native SHA explicitly.

`check_artifact.py` checks package/code/API/ABI, non-debuggable state, permissions,
alignment, unsigned status, embedded provenance and exactly one changed shared
library. The other11 libraries remain byte-identical to UI60-4. Gateway dependency
versions/compiler/CGO/tags are compared with the retained exact a5372571 binary;
the new gateway executable is not run or deployed by these scripts.

## Interpretation and next step

These are controlled local loss/reordering cases, not measured phone speed or
provider/mobile acceptance. DNS uses the real mux but a synthetic upstream.
Fast retransmit accelerates the sender only: Android-only installation does not
update the gateway's download sender. Delayed-but-not-lost frames can cause one
redundant retry; persistent loss may consume its retry budget earlier.

Preserve previous signed artifacts. Installation requires actual phone metadata and
VPN OFF, previous-key signing of the verified bytes, compatible replace-install and
readback. Server deployment additionally needs fresh operational readiness and the
accepted coordinated outage procedure. Never recover stale credentials/floors as a
binary rollback. No automatic owner CONNECT, field trial or public release.
