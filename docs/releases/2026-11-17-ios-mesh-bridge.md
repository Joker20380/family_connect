# 17 November2026 — IOS-MESH-BRIDGE-1

## Source checkpoint — qualification pending

Owner explicitly selected deferred iOS preparation. Separate worktree/branch
`feature/ios-mesh-packet-bridge-20261117` starts from remote main86663dfe; dirty
original main and other worktrees preserved. PR40 exact
3539ebe476545d700fc696bbdd4573bedd4e1a5f has no blocking threads; author's review
records accepted00:05:38 readback. Push43984661863/PR43984770165 phase0 still ran
at entry; no unrelated SHA PASS is substituted. No recovery/observer/host actions.

| Gate | Result |
| --- | --- |
| unsigned iphoneos/arm64 | PENDING macOS CI |
| separate iOS Simulator/arm64 | PENDING macOS CI |
| linked MESH / Swift-C-Go invocation | Implemented; PENDING CI |
| isolated packet lifecycle | Linux7 Go tests ×3 race PASS; existing packet regression PASS |
| Swift asynchronous lifecycle | Implemented; PENDING simulator |
| underlay | IPv4 interface bind/readback implemented; device routing NOT_RUN |
| real TUN / VPN / Telemost / whitelist | NOT_RUN |
| production / catalog / signing | NO CHANGE; public126/catalog9 retained |

Existing MESH packet adapter/wholedevice reused, no JNI copy or transport change.
Live chain preserves signed bootstrap/admission, Family TLS, ReliableStream,
mux/DNS and Telemost VP8/RTP. Fixture DNS does not claim that live chain executed.
An endpoint-only Xray build tag excludes unused platform TUN/dispatcher and its
GPL sing dependency. Actual iOS closure must pass exclusion and notices/source
packaging gates. Android/desktop behavior/source remain unchanged.

Initial saturation test expected ErrNoBufferSpace; pinned gVisor's public
WritePackets returns a short count/nil on full. Corrected test asserts exact zero
admission and full drain, without increasing limits or relaxing waits.

Toolchain: Go1.26.1, Xcode16.4/16F6, iOS18.5 SDKs, macos-15 arm64, minimum iOS16,
laboratory app0.0.1/build1. Exact SHA/host image belong in CI manifest. Procedure
is reproducible; bitwise deterministic binaries are not claimed.
[Build, ABI, underlay and device prerequisites](../../clients/ios/README.md).

Rollback: source revert/disable laboratory workflow. No deployed/installed client,
public artifact/catalog or server policy changes. Signed-device stage remains next,
not selected automatically; no user VPN readiness claim.
