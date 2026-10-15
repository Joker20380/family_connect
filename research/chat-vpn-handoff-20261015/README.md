# Restricted chat → VPN handoff (local source implementation)

Status: **KNOWN_CALLER_CONFLICT_FIXED_LOCALLY**, not a release/candidate acceptance.
[Report](../../docs/releases/2026-10-15-restricted-chat-vpn-handoff-1.md) contains
the contract, before/after distinction, results, identities and coverage limits.

- `source.patch`: product/test patch relative to retained research84, not root main.
- `before/`, `changed/`: exact affected old/new files; `source-manifest.json` hashes.
- `base-identity.json`: original Git base and eight research84 overlay hashes.
- `tests/handoff_test.go`: production coordinator + real Broker/Family-TLS fixture.
- `changed/carrier/restrictedowner/owner_test.go`: races, cleanup, refs/generations,
  cancellation, borrowing compatibility and expiry cases.
- `contract.py`: same source-level caller contract before and after, not JNI execution.
- `results/`: bounded full test logs, source/executable hashes, build/JNI receipts and
  preliminary setup failures. No raw owner diagnostics or binary artifacts.

## Host reproduction

From this review checkout, with Go 1.26.1 and already-cached module dependencies:

```sh
python3 research/chat-vpn-handoff-20261015/run.py \
  --go "$TOOLS/go/bin/go" --gopath "$TOOLS/gopath" \
  --work /tmp/fc-handoff-fresh-matrix
```

The output directory must be new. Fixed 1 normal + 3 race suite repetitions,
40 concurrent schedules per ownership suite. No automatic retry; any build/test
failure stops the runner and retains logs. Network module downloads disabled;
provider credentials/fixture environment are removed. Uses the published baseline
carrier snapshot with previous admission/TLS fixtures and actual new coordinator.
No repository product source or snapshot is modified by the runner.

## Exact Android derivative (retained inputs required)

```sh
python3 research/chat-vpn-handoff-20261015/apply.py \
  --retained "$RESEARCH84/source" --out /tmp/fc-handoff-fresh-source
python3 research/chat-vpn-handoff-20261015/contract.py "$RESEARCH84/source"
# Expected nonzero: old caller lacks the ownership gate.
python3 research/chat-vpn-handoff-20261015/contract.py /tmp/fc-handoff-fresh-source
python3 research/chat-vpn-handoff-20261015/build_check.py \
  --source /tmp/fc-handoff-fresh-source --tools "$TOOLS" \
  --xray "$PATCHED_XRAY" --reference-classes "$RESEARCH84_CLASSES" \
  --out /tmp/fc-handoff-fresh-build
```

`apply.py` verifies affected base and research-overlay hashes, archives exact
f5240994869826c6a28f59e58e38256c688cf6eb into a new directory, copies only the eight
recorded research overlays, then applies the declared changed files. It does not
copy arbitrary untracked files or mutate the retained source. The equivalent
`git apply --check source.patch` passes on the reconstructed research84 tree.

`TOOLS`: retained Go/NDK28.2/SDK35/JDK/GOPATH/Gradle dependency cache.
`PATCHED_XRAY`: previously cached `native-packet-tests/xray` packet-engine source.
`RESEARCH84_CLASSES`: retained researchProvisioning javac output, not root checkout.
These build inputs are not all published; this limitation is explicit. The script
compiles/links three native modes and compiles four affected/related Java classes,
generating JNI headers and verifying C prototypes. It does not execute JNI, build
or sign an APK, install, start a provider, or run emulator acceptance.

No server admission/timeout/framing, Mux/DNS, supervisor or diagnostic classification
changes. The process-wide gate serializes all independent opens, while borrowing
still requires the entire validated profile hash; it is not device-ID-only sharing.
