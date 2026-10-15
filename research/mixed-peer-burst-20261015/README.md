# Mixed peer receive burst acceptance — local only

See the [report](../../docs/releases/2026-10-15-mixed-peer-receive-burst-acceptance-1.md),
[predeclared contract](CONTRACT.md), [product delta](source.patch),
[source manifest](source-manifest.json), [compiled inputs](compiled-source-bindings.json)
and [results](results/summary.json).

RESULT: PARTIAL. NEW_CLIENT receiving OLD_GATEWAY passes finite burst acceptance
after one client-side capacity correction, preserving the async writer. The reverse
positive gate still FAILS19/20/40 at unchanged OLD_GATEWAY recvQueue16. Therefore
CLIENT_ONLY_DEVICE_TRIAL_READY=NO for the planned bidirectional burst envelope;
NEW/NEW success does not justify a client-only rollout.
OLD_CLIENT / OLD_GATEWAY still fails19/20/40 in this fixture. Its guard outcomes
are negative control observations, NOT a successful supported-burst acceptance.
No frozen gateway executable or Android device is executed.

## Reproduce from retained inputs

Use the existing exact research84 retained source and cached Go1.26.1 tools. The
required private retained base is not replaced with root main or assumed available
from a GitHub clone. The old gateway source is the published immutable baseline
snapshot. All output directories must be new. Use disk-backed temporary storage.

```sh
export TMPDIR="$WORK/tmp"
mkdir -p "$TMPDIR"
python3 research/startup-cause-fidelity-20261015/apply.py --retained "$RESEARCH84_SOURCE" --out "$WORK/old-client"
python3 research/receive-queue-stall-20261015/apply.py --retained "$RESEARCH84_SOURCE" --out "$WORK/before"
python3 research/mixed-peer-burst-20261015/apply.py --retained "$RESEARCH84_SOURCE" --out "$WORK/after"
python3 research/mixed-peer-burst-20261015/prepare.py --source "$WORK/before" --old-client "$WORK/old-client" --out "$WORK/before-mixed"
python3 research/mixed-peer-burst-20261015/prepare.py --source "$WORK/after" --old-client "$WORK/old-client" --out "$WORK/after-mixed"
CORE="^TestMixed(Supported|OutboundStall|Lifecycle|SACKReorder|OverloadAndCancel|FamilyTLS)$"
python3 research/mixed-peer-burst-20261015/run.py --prepared "$WORK/before-mixed" --tools "$TOOLS" --out "$WORK/before-results" --modes normal,race --match "$CORE"
# Expected nonzero for before: supported real-peer burst closes the carrier.
python3 research/mixed-peer-burst-20261015/run.py --prepared "$WORK/after-mixed" --tools "$TOOLS" --out "$WORK/after-results" --match "$CORE"
python3 research/mixed-peer-burst-20261015/run.py --prepared "$WORK/after-mixed" --tools "$TOOLS" --out "$WORK/sustained-results" --match "^TestMixedSustainedRealPeerOverload$"
python3 research/mixed-peer-burst-20261015/run.py --prepared "$WORK/after-mixed" --tools "$TOOLS" --out "$WORK/reverse-results" --match "^TestMixedReverseSupported$"
# Expected nonzero remains a required positive-gate failure, NOT an accepted guard.
```

Fixed after repetitions: normal1/race3 with GOMAXPROCS1; multicore normal1 with4.
The same core before/after load/assertions are retained. SACK and held-close cases
were added after the initial before/after run, then both final suites were recorded.
Sustained real-peer overload is a separate supplemental batch, not a supported
burst PASS. No retry-until-pass. The guard-only duplicate replay remains separate.

The default runner selection includes the reverse gate and therefore currently
returns nonzero; use the explicit batches above to reproduce the recorded matrix.

`prepare.py` copies three complete modules into different namespaces. Old module
changes are only import/module-path substitution plus the tagged test adapter.
`compiled-source-bindings.json` verifies93 actually selected module source files
against original inputs after reversing that namespace substitution. The old
gateway is not a rewritten generator and old client is pinned to a4d48907…b916d5.

The adapter invokes actual telemost.New/deliver/Recv, using a bounded post-reassembly
wire fixture instead of provider/Pion. Captured messages come only from the peer
SendContext; no positive-case FRS1 frame headers are fabricated. Release is a tight
loop without per-frame ACK waits or Gosched. Full Family/TLS opens are separate
tests using disposable synthetic credentials generated in memory, never exported.

The carrier snapshot reports direct queue len/cap, observed enqueue return and
dequeue counts, sampled high-water and first close. Sampled high-water is not a
claim to observe every interleaving. Flow.buffered is not used as queue occupancy.

## Existing regression and build commands

```sh
python3 research/receive-queue-stall-20261015/run.py --source "$WORK/after/carrier" --tools "$TOOLS" --out "$WORK/regressions"
python3 research/startup-cause-fidelity-20261015/run_host.py --source "$WORK/after" --review "$REVIEW" --tools "$TOOLS" --out "$WORK/combined-host"
python3 research/chat-vpn-handoff-20261015/build_check.py --source "$WORK/after" --tools "$TOOLS" --xray "$XRAY" --reference-classes "$REFERENCE_CLASSES" --out "$WORK/native-build"
export JAVA_TOOL_OPTIONS="-Djava.io.tmpdir=$WORK/tmp"
python3 research/startup-cause-fidelity-20261015/build_gradle.py --source "$WORK/after" --retained "$RESEARCH84_SOURCE" --tools "$TOOLS" --native "$WORK/native-build" --out "$WORK/gradle-build" --awg "$AWG" --radio "$RADIO" --python "$BUILD_PYTHON"
```

Reuse the prior task cached inputs; do not download/build a replacement runtime.
The existing async regression changes only two literal capacity expectations16→64,
not its DATA/ACK/progress/timeout/worker assertions or traffic. An additional test
fills64 maximum-size carrier messages and verifies the65th fail-closed boundary;
Close and parent cancellation of a full live queue are tested separately.

Public logs contain synthetic test output only; synthetic trace tags are aliased.
Raw and public hashes are recorded. Original logs, unsigned APK/native and temporary
synthetic key objects stay local. Installed APK, gateway, frozen snapshots, prior
reports and dirty root checkout are not changed. Signing/install/live actions0.
