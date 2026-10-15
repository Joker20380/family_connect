# Receive queue progress regression — local only

Read the [report](../../docs/releases/2026-10-15-receive-queue-stall-repro-and-fix-1.md).
This is a correction above research84 + chat/VPN handoff + cause fidelity, not a
signed/installed APK or a claim to have explained historical owner B.

## Reproduce

Use retained research84 and cached Go1.26.1/NDK/SDK inputs from the prior task.
No real provider, room, identity, key or external service is used by the new fixture.
Use a disk-backed TMPDIR if the host /tmp quota is exhausted.

```sh
export TMPDIR=/absolute/private/work/tmp
python3 research/receive-queue-stall-20261015/apply.py --retained "$RESEARCH84_SOURCE" --out "$WORK/before" --before
python3 research/receive-queue-stall-20261015/run.py --source "$WORK/before/carrier" --tools "$TOOLS" --out "$WORK/before-tests" --before
# Expected nonzero: original product progress defect.
python3 research/receive-queue-stall-20261015/apply.py --retained "$RESEARCH84_SOURCE" --out "$WORK/after"
python3 research/receive-queue-stall-20261015/run.py --source "$WORK/after/carrier" --tools "$TOOLS" --out "$WORK/after-tests"
```

Every output directory must be new. Fixed normal1/race3; no retry-until-pass.
The published runner includes the final two supplementary cases; original full-suite
logs predate those additions, so their separate normal1/race3 logs are retained too.
The same original failing assertions and workload pass after the product change.
The before tree receives the same test file but neither product edit.

The fixture executes real telemost.New/deliver/Recv and ReliableStream with defaults:
receive queue16, Reliable incoming1, send/receive windows8/16, payload16384,
RTO1s/retries8/MaxAge20s and the existing transmit deadline min(MaxAge,2s).
Only the wire/provider layer is replaced by a post-reassembly in-memory adapter with
an explicit cancellable outgoing gate. It does not execute Pion/Telemost networking,
Family TLS, Mux or JNI in that regression. A separate test fills the real production
SendContext/sendQueue256 and verifies cancellation. Existing Family/TLS/Mux suites
and actual coordinator/admission fixtures cover those layers separately.

Unpaced20/40-frame local bursts can still reach RECEIVE_QUEUE_FULL; the guard is
preserved and not hidden. Their scheduling-dependent outcome is reported, not fitted
to a desired proportion. This patch removes synchronous transmit starvation, not
every possible producer overload. No queue depth at the owner B failure was recorded.

## Source and build

- source-manifest.json: installed cumulative input identity,12 narrow file bindings,
  changed/before file hashes, patch hash and new cumulative inventory.
- source.patch and changed/: two product Go files plus one test-only file. Frozen
  snapshots and previous handoff/diagnostic namespaces are not edited.
- results/: expected before failures, after/supplement/combined regressions, sanitized
  B tail, build summary and full Git-base-relative cumulative inventory.

For combined regressions use the unchanged prior run_host.py with --source pointing
at the new derivative. Native/JNI uses the prior handoff build_check.py. Full Gradle
uses the prior diagnostic build_gradle.py and the newly built normal native library:

```sh
python3 research/startup-cause-fidelity-20261015/run_host.py --source "$WORK/after" --review "$REVIEW" --tools "$TOOLS" --out "$WORK/combined"
python3 research/chat-vpn-handoff-20261015/build_check.py --source "$WORK/after" --tools "$TOOLS" --xray "$XRAY" --reference-classes "$RESEARCH84_CLASSES" --out "$WORK/native"
JAVA_TOOL_OPTIONS="-Djava.io.tmpdir=$TMPDIR" python3 research/startup-cause-fidelity-20261015/build_gradle.py --source "$WORK/after" --retained "$RESEARCH84_SOURCE" --tools "$TOOLS" --native "$WORK/native" --out "$WORK/gradle" --awg "$AWG" --radio "$RADIO" --python "$PYTHON310"
```

Private retained full source and native build dependencies remain necessary; this
does not pretend the selected published slice alone builds the APK. Local unsigned
APK/native files are not published. No signing/install/device acceptance occurred.

## Publication log projection

The full-suite logs mask one gateway-address literal used as an existing SSRF
negative fixture subtest name with GATEWAY_DESTINATION_FIXTURE. Counts, outcomes,
timings and failures are unchanged. summary.json records both private raw and
published log hashes; original logs stay private. This is not a live connection.
