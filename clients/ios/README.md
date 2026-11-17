# iOS MESH packet-boundary laboratory

Selected task **IOS-MESH-BRIDGE-1**,17 November2026. This is an unsigned technical
prototype, not a distributed VPN. [Current results](../../docs/releases/2026-11-17-ios-mesh-bridge.md).

## Reproduce from Linux through macOS CI

Push the branch/open its PR: `iOS MESH unsigned boundary` runs for applicable paths.
After the workflow is on main, use `gh workflow run ios-mesh.yml --ref <branch>`
for an explicit run. PR CI checks out the exact head, not a synthetic merge commit.
No Apple account, device, certificate, signing key or profile is consumed.

Pins: macos-15 **arm64** runner, Xcode **16.4/16F6**, both iOS SDKs **18.5**,
minimum iOS16.0, Go **1.26.1** (existing Android CI pin). The hosted image is rolling;
actual OS/image versions are recorded, not claimed immutable. Both native targets
are **GOOS=ios/GOARCH=arm64** with distinct clang triples `arm64-apple-ios16.0` and
`arm64-apple-ios16.0-simulator`. Simulator: iPhone16/iOS18.5/arm64.

On the matching Mac, from a clean committed checkout:

```sh
export DEVELOPER_DIR=/Applications/Xcode_16.4.app/Contents/Developer
python3 clients/ios/build.py --out /tmp/fc-ios-result
python3 clients/ios/simulator.py --out /tmp/fc-ios-result
```

Linux host-only checks: `python3 clients/ios/build.py --go /path/to/go1.26.1/bin/go --out /tmp/fc-ios-host --host-only`.
Use fresh output directories. `project.py` generates an ordinary Xcode app/extension
project and plists/entitlement declarations. Declarations are **not entitlement
grants**; `CODE_SIGNING_ALLOWED=NO`. Laboratory0.0.1/build1 is not a product version
or catalog change. No installer is published.

Artifacts: unsigned app/embedded extension, native archives/headers, link maps,
Mach-O platform/symbol inventories, exact package/module closure, source archives,
original notices, toolchain/SHA manifest, logs and simulator receipt/screenshot.
Hashes identify artifacts; procedural reproducibility is not bitwise determinism.
Swift/C/Go tests execute in the iOS simulator app, not a macOS binary substitute.

## Reuse and dependency closure

The existing `restrictedandroid/packet` package has no JNI dependency. Its adapter
still calls `wholedevice.Session` via Xray `NewEndpointStack(stack.LinkEndpoint)`.
A bounded gVisor channel endpoint replaces the OS fd. No JNI wrapper or packet
engine is copied. Live mode calls `wholedevice.OpenProvisioned`: signed bootstrap,
Room Broker admission, dedicated Family TLS, ReliableStream, mux/DNS and Telemost
VP8/RTP remain unchanged. No DataChannel or HTTP-proxy fallback is introduced.

Xray pin `d2758a023cd7f4174a5a5fa4ff66e487d4342ba0`; gVisor pin
`v0.0.0-20260122175437-89a5d21be8f0`. Existing Android packet patch unchanged;
`xray-endpoint-only.patch` adds `fc_packet_endpoint` to exclude unused dispatcher
and platform TUN constructors, supplying the identical handler interface. Without
this isolation the full dispatcher imports **GPL-3.0-or-later sing**. iOS's closure
check rejects it. Android/desktop never select this tag; CI tests both tagged and
original untagged packet engine. The selected closure retains Xray MPL-2.0, gVisor
Apache-2.0, permissive transitives and Go runtime notices. CI supplies complete
included dependency sources (modified Xray included), both patches and repository
sources at the exact SHA. MPL modifications are not relicensed as proprietary.
Pion datachannel is a WebRTC transitive, not the selected carrier mode. This is
not re-approval of historical product distributions or provider API permission.

## ABI and lifecycle

`Shared/Bridge.h`: fixed-width integers, monotonic handles, copy-in/copy-out, no
retained Go/Swift pointer. Write copies before return; read copies into caller-owned
1280-byte storage. Swift translates Darwin `AF_INET`/`AF_INET6` to ABI **4/6**;
Linux AF numbers are never assumed. Existing IPv4 TCP/Family DNS policy remains;
IPv6 explicitly rejects, unsupported UDP has no direct fallback.

Limits: MTU1280,64 input packets,64 output packets,4 handles. Input-full returns-3;
gVisor output-full reports a short count with nil error and releases the unadmitted
reference. This is bounded loss, not lossless backpressure. Swift arms one read at
a time and synchronously drains each output callback, avoiding dispatch backlog.
States1/2/3/4: starting/packet-engine-ready/failed/stopped, **not** generic CONNECTED.
Errors: invalid-1, closed-2, full-3, unsupported-4, wait-timeout-5, startup-6,
transport-7, underlay-8. First failure survives stop; stop drains resources/removes
handles. Cancellation unblocks startup/read. Late callbacks cannot restart a pump.

App-only diagnostic modes1/2 use synthetic DNS/cancelled startup. Real gVisor and
wholedevice execute, but no Family authentication/ReliableStream/Telemost exchange
is claimed for that fixture. Extension always selects mode0 and requires material.
Its only packet API is public `NEPacketTunnelFlow.readPackets/writePackets`.

## Underlay boundary

Public `NWPathMonitor` selects Wi-Fi/cellular. Existing Go/Pion socket factories
still pass through `underlay.New` before bind/connect. The iOS-specific hook requires
an up non-loopback en*/pdp_ip* interface with IPv4, applies public SDK `IP_BOUND_IF`
with setsockopt, and checks getsockopt's returned index. Invalid fd/interface,
missing IPv4, changed index or syscall failure denies access. No unconditional
successful protect, KVC, hidden TUN fd or private utun constructor is used.

This physical-interface scoping is the concrete anti-recursion path, **not** proof
of installed-provider routing. macOS checks real unconnected socket bind/readback;
device routing still requires an iPhone. Path change/loss cancels, not silently
migrates. Context cancellation and session cleanup close mux/TLS/carrier, engine
and packet buffers; `underlay.Close` alone only forbids new sockets.

Numeric IPv4 DNS, tcp4/udp4, ip4 resolution/route discovery remain. IPv6-only,
DNS64/NAT64 and general IPv6 Internet are unsupported, not automatically repaired
by the bridge. No fixed NAT64 prefix synthesis. If BSD interface scoping proves
inadequate, the public alternative is a deliberate Network.framework/NWConnection
factory adapter plus system DNS/dual-stack, including replacement of concrete
UDPConn assertions; never return fake protect success.

Official references: [NEPacketTunnelProvider](https://developer.apple.com/documentation/networkextension/nepackettunnelprovider),
[routing](https://developer.apple.com/documentation/networkextension/routing-your-vpn-network-traffic),
[NEProvider](https://developer.apple.com/documentation/networkextension/neprovider),
[IPv6/DNS64/NAT64](https://developer.apple.com/library/archive/documentation/NetworkingInternetWeb/Conceptual/NetworkingOverview/UnderstandingandPreparingfortheIPv6Transition/UnderstandingandPreparingfortheIPv6Transition.html).
Apple's NEProvider connection APIs recommend Network.framework; IP_BOUND_IF is
public in SDK netinet/in.h. A successful bind is weaker than routing acceptance.

## Next signed-iPhone prerequisites

Developer Program Network Extension capability for both app IDs, development
signing/provisioning, registered iPhone and operator consent. Add a reviewed secure
device-only configuration/keychain handoff and disposable authorized Family
identity/admission/room material; no production profiles or secrets in CI/Git.
The laboratory app intentionally installs no VPN configuration/Connect button.

Verify real extension launch/memory budget, packet families, IPv4/IPv6/default/DNS
routes, absence of signaling/DNS/ICE/STUN/TURN/media from captured tunnel traffic,
trust/CRL/expiry rejection, TCP/DNS and UDP/IPv6 containment, cancel/stop/restart,
process death, sleep and Wi-Fi/cellular changes. `cancelTunnelWithError` can restore
ordinary OS routing; no always-on/kill-switch claim. Only after this gate authorize
real Telemost and whitelist-network trials. Simulator is not physical VPN proof.
