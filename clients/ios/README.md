# iOS MESH development candidate

Selected **IOS-DEVELOPMENT-HANDOFF-1**,17 November2026,0.0.1/build2 (not a public
release). [New-stage receipt](../../docs/releases/2026-11-17-ios-development-handoff.md).
Base [PR41 final d02fce99 acceptance](https://github.com/Joker20380/family_connect/pull/41#issuecomment-6935466490),
merge `bda954fb27ad7115b8c373929cf3e80e84992175`; the earlier receipts below remain evidence.

Latest verified unsigned source `47e894163d3c6cfcb3036b74813d466d13c31313`:
[macOS44038770792 artifact14309286227](https://github.com/Joker20380/family_connect/actions/runs/44038770792/artifacts/14309286227),
device/simulator and nine isolated groups PASS, handles0, all208 file hashes matched.
ZIP SHA256 `97bd109492a734f8d716bd0f0244feae855fb180990dfaad6c59d40501cc1232`.
Source integration is still blocked by a separate mandatory Linux desktop teardown
failure; no signed installation or device traffic is inferred. The final receipt
below tracks the documentation checkpoint's own gates and integration decision.

Earlier development source `fb13d23b138ca16ce969ad24d1f3d093ba641f0a`: macOS44032183193
and44032176415 PASS device/simulator, nine isolated groups and zero handles;
[verified unsigned artifact](https://github.com/Joker20380/family_connect/actions/runs/44032183193/artifacts/14305768210),
all208 file hashes matched. ZIP SHA256
`5363ef4dd9511615bfcf4c192289cd6b9f956f97fbc0504a524bb67028feee89`.
[Final exact-head CI and integration receipt](https://github.com/Joker20380/family_connect/pull/42#issuecomment-6940824604)
tracks later documentation heads and ordinary merge; pending is not PASS.
No signed installation, system VPN or provisioned Keychain sharing is claimed.

Selected task **IOS-MESH-BRIDGE-1**,17 November2026. This is an unsigned technical
prototype, not a distributed VPN. [Current results](../../docs/releases/2026-11-17-ios-mesh-bridge.md).
Qualified source `fc08a50ecec45ea94e9ab27b1a9cfe28d507dc5d`: macOS CI43991766964
builds both targets and runs the simulator boundary suite. The receipt includes
verified artifact hashes; it is not an installed-device or Telemost result.

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
grants**; `CODE_SIGNING_ALLOWED=NO`. Development0.0.1/build2 is not a product version
or catalog change. No installer is published.

Artifacts: unsigned app/embedded extension, native archives/headers, link maps,
Mach-O platform/symbol inventories, exact package/module closure, source archives,
original notices, toolchain/SHA manifest, logs and simulator receipt/screenshot.
Hashes identify artifacts; procedural reproducibility is not bitwise determinism.
Swift/C/Go tests execute in the iOS simulator app, not a macOS binary substitute.
For runtime only, a temporary simulator copy is ad-hoc signed locally (no account
or certificate); the device and retained simulator artifacts remain unsigned.

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
transport-7, underlay-8, material-validation-9. First failure survives stop; stop drains resources/removes
handles. Cancellation unblocks startup/read. Late callbacks cannot restart a pump.
The iOS-only stack wrapper also joins gVisor workers after close; pending Swift
flow callbacks hold the pump weakly and path-monitor handlers are released on stop.

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
The prototype rejects `includeAllNetworks`/`enforceRoutes`: Apple documents that
enforced routing can supersede interface scoping. Default routes alone also do not
override more specific/local routes or other apps' interface scoping. This is not
a leak-proof system policy. The signed-device gate must qualify those distinctions.

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

## Development configuration and secret handoff

The app now uses public NETunnelProviderManager/NETunnelProviderProtocol and
NETunnelProviderSession. Load all **own provider** configurations, select a stable
configuration UUID, create only when absent, save, reload, verify opaque handoff,
then request start. Duplicate IDs fail for manual inspection, never bulk deletion.
Repeated Connect is guarded; Disconnect invalidates an in-flight save/reload/start
operation. NEVPNStatus notifications are the only connection-status source; a
successful start call is not Connected. Disconnection errors use public
fetchLastDisconnectError, preserving native NSError codes without raw material.
External Settings can race app operations:
this is not a system-wide transaction or instant revocation mechanism.

Import one UTF-8 JSON object (maximum96KiB), version1, with `profile` and `directory`
as base64 of the existing JSON formats and a numeric IPv4 `resolver` ending `:53`.
No sample real profile is shipped. Existing Family TLS certificate/key/CA/CRL
signature, validity, identity/family/role/revision checks are reused offline and on
live startup; bootstrap directory family/gateway/expiry/parser checks also apply.
The directory is a seed locator, not an independently signed object. The importer
does not establish that a supplied self-signed CA belongs to the owner: authenticate
the agreed test material out of band. Live admission and peer authentication remain
mandatory; local validation does not establish fresh server revocation state.

The linked bundle is a single immutable Keychain generic-password item. App and
extension use `$(AppIdentifierPrefix)<app-bundle-id>.materials`; never the special
`com.apple.managed.vpn.shared`. Provider preferences contain **only** version,
configurationID and materialReference UUID. No UserDefaults/preferences/profile
fallback. On each launch the extension reads and validates the item, then gives a
copied in-memory snapshot to Go. Missing/revoked/corrupt/inaccessible items fail
closed without their contents in errors. Material is never a launch option.

Accessibility is **AfterFirstUnlockThisDeviceOnly**, nonsynchronizable: background
use after first unlock is possible; before first unlock after reboot it fails
explicitly. This trades unlocked-only confidentiality for background extension
availability; not a promise that a provisioned extension can access the item.
No migration to another device through backups. Swift/Data/JSON/Go APIs can leave
copies in memory; guaranteed erasure of all copies is **not claimed**. The source
file selected by the owner also remains theirs to manage outside the repository.

Replacement imports a new reference; it never edits a live session's snapshot.
Disconnect all own sessions and wait for system inactive status before selecting
replacement/save or revoking/deleting old references. A referenced tombstone or
missing item makes future starts fail. Existing VPN configurations are not deleted.
Settings/another process may race this local guard; stop and verify the physical
session before destructive material operations. Retained memory is not remotely
revoked by deleting an item.

Startup admission linearizes at native `CommitStart`, **after** network settings
completion, serialized with native Cancel/first-error. Worker snapshots cannot
authorize startup. Errors after admission are runtime failures, not a retroactive
startup result. Provider generation ownership joins the worker and clears bridge,
monitor, interface and callbacks before reporting cleanup. Late old callbacks are
ignored. An outstanding setTunnelNetworkSettings operation prevents another run
on that owner until its callback arrives; public API has no cancellation handle.
Stop still frees native handles without waiting forever on that callback. A fresh
path has a new10s eligibility deadline (separate from unchanged180s native startup
budget). The shared paired-DNS positive fixture now has a declared3s rather than
1s completion budget with exact payload/count assertions and timing diagnostics.
The local-write fixture isolates its peer's idle timer at1s; sender150ms deadline,
500ms assertion and cancellation budgets are unchanged. See retained failures and
reasoning in the new-stage receipt. No transport runtime changed. Reuse on one provider object is
isolated robustness coverage, **not** a claim about Apple's instance reuse policy.

Official references: [manager](https://developer.apple.com/documentation/networkextension/netunnelprovidermanager),
[Keychain sharing](https://developer.apple.com/documentation/security/sharing-access-to-keychain-items-among-a-collection-of-apps),
[AfterFirstUnlockThisDeviceOnly](https://developer.apple.com/documentation/security/ksecattraccessibleafterfirstunlockthisdeviceonly).

## Development signing and installation — owner Mac only

Unsigned CI remains account/secret-free. First verify the **actual phone model and
iOS build** are supported by the chosen Xcode/device support. Xcode16.4/SDK18.5 CI
does not prove debugging support for every newer iPhone/iOS. A newer Xcode pairing
needs its own build/launch acceptance; do not disable version checks in unsigned CI.

On an authorized Mac, use a clean exact-source checkout and matching verified
unsigned output. Register app ID `<bundle>` and extension ID `<bundle>.tunnel`,
enable Network Extension packet-tunnel and Keychain sharing for both, obtain two
**development** profiles for the same App ID prefix/Team and registered device.
Install those profiles and the Apple Development identity in the local Xcode/login
Keychain using Apple's UI. Keep certificates/keys/profiles outside Git and CI; no
passwords or private material in chat. Entitlement declarations do not grant access.

```sh
export DEVELOPER_DIR=/Applications/Xcode_16.4.app/Contents/Developer
python3 clients/ios/development.py --unsigned /private/tmp/fc-ios-result \
  --out /private/tmp/fc-ios-development --team "$APPLE_TEAM_ID" \
  --bundle "$APP_BUNDLE_ID" --app-profile "$LOCAL_APP_PROFILE" \
  --tunnel-profile "$LOCAL_TUNNEL_PROFILE"
xcrun devicectl device install app --device "$TEST_DEVICE_ID" \
  /private/tmp/fc-ios-development/products/FamilyConnect.app
```

The helper verifies source/hash provenance, Team, app IDs, actual App ID prefixes,
development/device/expiry/NE/Keychain grants; it generates manual signing settings,
builds app+extension, verifies codesign and the shared signed group. It reads local
profiles without printing their contents; Xcode logs must remain local and be
reviewed before sharing. Development Mode/device trust and a supported host/phone
pair are required. Installation command is explicit, not performed by the helper.

## First signed-iPhone acceptance (NOT_RUN)

Developer Program Network Extension capability for both app IDs, development
signing/provisioning, registered iPhone and operator consent; disposable agreed
test Family identity/admission/directory material, not production identity. First
test denied permission/save/reload and repeated app open/Connect/Disconnect; verify
only one own system configuration. Separately prove extension launch and shared
Keychain access, first-unlock behavior, missing/revoked/corrupt item rejection.

Verify real extension launch/memory budget, packet families, IPv4/IPv6/default/DNS
routes, absence of signaling/DNS/ICE/STUN/TURN/media from captured tunnel traffic,
trust/CRL/expiry rejection, TCP/DNS and UDP/IPv6 containment, cancel/stop/restart,
process death, sleep and Wi-Fi/cellular changes. `cancelTunnelWithError` can restore
ordinary OS routing; no always-on/kill-switch claim. Simulator is not physical VPN proof.

Bounded first trial, separately authorized by the owner:
1. Record phone model/iOS build, compatible Xcode, Team/capability grants and local
   development provisioning. Install; deny/allow VPN consent, reopen app, check
   unique own configuration and Disconnect during startup.
2. Confirm extension launch and shared Keychain with missing/revoked/expired
   **synthetic** items (expected failures), reboot-before-unlock denial and
   after-unlock accessibility. Do not inject a fixture as a successful VPN.
3. On controlled IPv4 Wi-Fi with disposable authorized test identity/directory,
   allow one bounded **real MESH/Telemost** startup. Live MESH admission precedes
   network settings, so successful system startup and route checks cannot be
   performed as if this were a transport-free phase. Correlate system status,
   extension lifecycle and gateway-side test observations; never log identities.
4. Separately measure captured packets, external underlay sockets, DNS/ICE/STUN/
   TURN/media recursion, TCP/DNS success and disallowed UDP/IPv6 containment; stop
   immediately on loop/leak/error. Check Stop frees resources and ordinary OS
   routing restoration. Then bounded restart/background/path-change/memory tests.
5. Only after these gates select a whitelist-network trial. IPv6-only/NAT64 and
   enforced routes remain unsupported; no includeAllNetworks/enforceRoutes policy.
