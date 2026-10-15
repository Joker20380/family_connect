# Gateway transport-progress candidate, 16 October 2026

This package creates a separate server derivative of the preserved production
baseline, not the failed supervisor or a copy of the client carrier tree.
Only three product files change. See [report](../../docs/releases/2026-10-16-gateway-transport-progress-burst-candidate-1.md),
[manifest](source-manifest.json), [patch](source.patch), [resources](RESOURCE-CONTRACT.md)
and [future-only rollout](RUNBOOK.md). No binaries or credentials are published.

## Reproduction

Use disk-backed WORK and retained Go1.26.1 tool directory TOOLS (go/bin/go + gopath).
C_NEW is the unchanged c2dc3dd8…5cf40d08 materialization from the previous package;
C_INSTALLED is the retained a4d48907…b916d5 cumulative source, not an APK decompilation.
Scripts verify the supplied inventories. Paths are arguments, not production defaults.
No SSH, ADB, provider credentials or production profiles are needed.

```sh
PKG=research/gateway-transport-progress-20261016
python3 "$PKG/apply.py" --out "$WORK/source"
python3 "$PKG/prepare.py" --candidate "$WORK/source" --client "$C_NEW" \
  --installed "$C_INSTALLED" --out "$WORK/mixed"
python3 research/mixed-peer-burst-20261015/run.py --prepared "$WORK/mixed" \
  --tools "$TOOLS" --out "$WORK/mixed-results" \
  --match "^TestGateway(Supported|OutboundStall|Lifecycle|SACKReorder|OverloadAndCancel|FamilyTLS|SustainedRealPeerOverload)$"
python3 research/mixed-peer-burst-20261015/run.py --prepared "$WORK/mixed" \
  --tools "$TOOLS" --out "$WORK/installed-stall-control" \
  --match "^TestGatewayInstalledOutboundStallDifferential$"
python3 "$PKG/bind.py" --prepared "$WORK/mixed" --candidate "$WORK/source" \
  --client "$C_NEW" --installed "$C_INSTALLED" --tools "$TOOLS" \
  --out "$WORK/compiled-source-bindings.json"
```

Fixed normal1/race3/multicore1; never rerun until pass. The aggregate mixed command
returns nonzero for the extended installed-client outbound-stall test; the paired
control also fails with baseline. Neither failure is suppressed. Mandatory new-pair
bursts must pass; old-client19/20/40 are recorded KNOWN_OLD_RECEIVER_LIMIT rather
than counted as positive acceptance. For8/16 the old-client branch cannot swallow
failure. No main burst assertion, generated load, timeout/window or release pacing
was relaxed. Tests include old-server receive controls from the previous package,
but the anchored command selects only the separately declared current task matrix.

`prepare.py` reuses the prior adapter/generator and compiles a FOURTH actual module
from the new server source. `tests/mixed_test.go` retains the old test logic, adding
candidate constructors, pair selection, both-direction stall/lifecycle coverage and
strict old-client8/16 handling. Namespace transforms are verified against originals
for124 compiler-selected inputs. The adapter replaces provider/wire after reassembly;
actual carrier deliver/Recv, Reliable and Family/TLS execute. Family/TLS exact duplex
is separate from raw Reliable burst cases, not an end-to-end Pion/TLS replay.

The generator captures at most64 actual outgoing frames, waits at most6s, and
releases8/16/19/20 or40 in a tight loop. Default8 unique outstanding DATA per peer,
real ACK and timer retransmission generation, same epochs, no invented headers,
per-frame Gosched or ACK waits. Case context15s. Exact8/16/19/20 is supported and40
is separate positive stress; sustained blocked-reader overload is a different gate.

## Existing server regression and extra resource checks

FIXTURE_SOURCE is the retained gateway-same-room source containing the existing
`pilot/telemost_family_fixture.py`, control ProductStore and device_identity modules.
PYTHON is its retained compatible Python environment. It generates disposable keys
and profiles only beneath the new private output directory, never accepts a live DB.

```sh
python3 "$PKG/regressions.py" --candidate "$WORK/source" --tools "$TOOLS" \
  --fixture-source "$FIXTURE_SOURCE" --python "$PYTHON" --out "$WORK/regressions"
python3 "$PKG/timestamp_check.py" --candidate "$WORK/source" --tools "$TOOLS" \
  --out "$WORK/timestamp-fixture"
```

The same seven packages and normal1/race3/multicore1 run on baseline and candidate.
The historical full suites are not asserted green. All exits/failures/skips are kept.
The carrier-only source snapshot lacks the relative timestamp test-vector path;
the supplemental command supplies the existing hash-guarded vector to isolated test
overlays on BOTH versions, without changing the earlier logs or product source.

The extra candidate test overlay copies the existing receive_stall and receive_burst
tests byte-for-byte from the previous package and adds gateway_resource_test.go.
It does not enter the product build. Synthetic generated credentials stay private.
`regressions.py` returns after recording all batches; inspect every runs.json exit
and the differential, not just the Python process exit status.

## Product build, no execution

```sh
python3 "$PKG/build.py" --source "$WORK/source" --tools "$TOOLS" \
  --baseline-binary "$BASELINE_ROLLBACK" --out "$WORK/build"
```

Entrypoint `./cmd/bootstrap-broker`; Go1.26.1 linux/amd64 v1, CGO=1, trimpath,
no tags or ldflags. Dependency identities match the actual saved baseline binary.
Explicit metadata delta: buildvcs=false because this source is a manifest-addressed
projection rather than its original dirty Git checkout. No stale baseline Git SHA
is injected as the candidate identity. Source inventory and binary hash are the binding.
The build runner verifies all226 source files and excludes test adapters. No gateway
process is launched. No client native/JNI/Gradle rebuild, signing or installation.

## Evidence categories

POSITIVE_SUPPORTED_LOAD, KNOWN_OLD_RECEIVER_LIMIT, SUSTAINED_OVERLOAD_GUARD and
UNEXPECTED_REGRESSION are separate. The additional old-client synchronous-transmit
stall is a known old-sender progress limit only after its paired baseline control.
A test command containing that extension is not described as all-green. Full raw
synthetic logs remain private with hashes; safe selected observations and result
counts are published. Historical B remains NOT_PROVEN; previous smoke PASS and
owner reconnect FAIL are not upgraded. Source acceptance is not live/device acceptance.
