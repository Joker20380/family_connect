# Personal/Home Gateway — Reticulum control, selectable data transport

Engineering decision and implementation requirements, 2026-09-25.
**Stage 5 / Reticulum — active development; design recorded, RNS-1–RNS-5 open.**
This document specifies work to implement; it is not evidence of a working tunnel.
Current execution order lives in [PLAN](../PLAN.md), measured results in
[STATUS](../STATUS.md). The project has working pilot clients and VPN transports;
it is no longer only an isolated research laboratory, nor production-ready.

## Strategy revision — owner decision, 2026-09-25

The primary objective is establishing a secure phone↔home-PC connection while
mobile allowlist restrictions are active. Reticulum is the control/discovery,
authentication and negotiation/recovery channel; carrying all IP traffic over RNS
is no longer required. This supersedes the original mandatory IP-over-Reticulum
strategy. Milestone names RNS-1–RNS-5 are retained for continuity, with updated
acceptance below. No milestone has passed. Current position: global stage5,
start of5A (design and reachability validation); no Home Gateway runtime yet.

First validate reachable authorized infrastructure on the target mobile network:
control/bootstrap AND data ingress. A successful RNS exchange is not evidence of
a reachable data endpoint; a known destination is not a firewall bypass. If the
RNS carrier is blocked, it also needs a reachable bootstrap/carrier. Shared
operator infrastructure is allowed; per-user home DDNS/static IP is not required.

Relay-first PoC: both endpoints establish outbound connections to a reachable
relay; user traffic remains encrypted end-to-end to the home PC. The relay is not
an Internet exit. Direct IPv6/IPv4 and NAT traversal come later as optimisation.
AWG/WG with reachable UDP and existing TCP/XHTTP/TLS are candidates, not validated
solutions for this mobile network. Existing runtimes do not automatically provide
a reverse/relay tunnel. Choose the data adapter after measurement and license audit;
no new implementation or dependency is selected by this strategy change.

## Goal and scope

Android on a mobile network establishes an authenticated connection to its owner's
Windows Home PC using Reticulum control and a selected encrypted data channel.
Windows provides diagnostic direct Internet (A) or existing Family Connect VPN / EU
exit (B). No per-user static IPv4, domain/DDNS, manually entered home endpoint,
key transfer or reconfiguration after home-IP changes. Device Identity → RNS
Destination → signed negotiation → currently reachable data path. IP addresses
belong to the mutable underlay, never permanent identity.

```text
Family Control / Device Identity / FAMILY authorization
                         │
        Reticulum: discovery + signed negotiation
                         │
           Android Phone ↔ Windows Home PC
                         │
Data: Android TUN ══ encrypted selected transport ══ Windows Gateway
                        direct OR relay                    │
                                               diagnostic Internet
                                                OR existing FC VPN
                                                           │
                                                        Internet
```

Direct Internet is an explicit diagnostic mode, never a fallback from mode B.
Home Gateway serves only explicitly authorized devices of the same FAMILY.
This is a personal gateway, not a public relay or arbitrary public proxy.

## Inspection and minimal integration points

| Existing component | Integration decision |
| --- | --- |
| `device_identity/device.py`, Android `ControlIdentity.java`, Windows `Core/ControlIdentity.cs` | Existing Device Identity already has RNS-compatible X25519/Ed25519 keys and stable public reference; reuse secure storage and enrollment, no second identity/account system. Messenger identity is not device authorization. |
| `control/product/store.py` | Existing `devices`, `device_entitlements`, `entitlements.family_id`, expiry/revision/revoke are authoritative. Issue Home Gateway authorization from this store, not from peer self-assertion. Friends integration remains an explicit mapping task, not a second membership database. |
| `provisioning/models.py`, `envelope.py`, `cache.py` | `NetworkProvisioningState` currently accepts only WG gateway candidates. Add a separately versioned, capability-gated Home Gateway grant using existing signing/verification/revision rules; do not silently broaden old schema-1 acceptance. |
| `provisioning/configuration.py`, Android `ControlSelection.java`, `ConnectionService.java`, Windows `Core/TransportSequence.cs` | Add explicit experimental selection after platform integration. Preserve existing default WG/AWG/TCP selection and reconnect; no automatic Home Gateway promotion. |
| Android `TcpVpnService.java`, `ControlRnsAndroid.java`, `fc_rns_transport.py` | Reuse VpnService ownership, existing Python runtime and underlay binding pattern. Current RNS carrier is bounded control exchange, not an IP tunnel; add a separate adapter/lifecycle without changing its protocol. |
| Windows `Broker.cs`, `BrokerIdentity.cs`, `TcpEngine.cs`, `TcpNetwork.cs`, `TcpSession.cs`, `TcpHealth.cs` | Broker owns privileges, identity and route lifecycle. Reuse existing networking facilities; current outbound VPN engine does not yet implement LAN/tunnel forwarding or NAT. Add gateway adapter explicitly. |
| Android `VpnHealth.java` / service generation tokens; Windows health/session; control journals | Extend bounded health/reconnect and cancellation contracts. Retain stale-callback protection and transaction recovery; keep payloads out of telemetry. |

No broad refactor, replacement of WG/AWG/TCP/WebRTC, or automatic resumption of
unrelated migration/test debt. Changes must preserve existing security tests.

## Implementation choice and boundary

Use the **official Python reference implementation, `rns==1.5.1`**, already pinned
in Device Identity and bundled by Android's Chaquopy configuration. Android can
reuse the existing embedded runtime. Windows initially needs an isolated broker-owned
worker with bounded private IPC and runtime packaging; that worker is not yet present.
No public localhost SOCKS/HTTP interface, command-line secrets, or extra VPN stack.
The IPC must authenticate its owner and reject unrelated local processes; named-pipe
ACLs/parent-owned handles, bounded messages and child cleanup are acceptance gates.

`HomeGatewaySession` is the proposed orchestration boundary: existing identity/FAMILY
policy, a `ReticulumControlAdapter`, replaceable `DataTransportAdapter`, Android TUN
and Windows gateway adapters, health/reconnect and diagnostics. These are design
names, not implemented classes. The former `ReticulumHomeGatewayTransport` name
must not require RNS packet carriage. Control handles destination/discovery and
signed negotiation; data handles peer handshake, bounded packet I/O and close.
Business logic depends on these contracts, not RNS objects. Both peers use the
reference RNS stack for control; IP-over-RNS remains an optional future data adapter.

[rns-vpn-rs](https://github.com/BeechatNetworkSystemsLtd/rns-vpn-rs) is a reference
for TUN packets over links, destination-based peer lookup and nonce/signature peer
authentication. Its source uses a TUN interface, MTU 1500, announce-driven links,
and peer authorization before forwarding. Its Rust dependency is Reticulum-rs;
these choices do not establish Android/Windows support or reference wire compatibility.
No code is copied, bundled or added as a dependency in this documentation change.
Do not adopt its permissive `allow_all` option. An alternative implementation must
pass bidirectional interoperability tests against the pinned Python reference before
adoption; do not implement the Reticulum protocol from scratch.

The reference implementation's Reticulum License differs from MIT and from the
authors' public-domain protocol statement. See [dependency audit](../legal/DEPENDENCY_LICENSE_AUDIT.md).

## Identity, signed binding and threat model

Reuse the device's existing RNS-compatible identity; derive a distinct application
destination using a versioned Home Gateway aspect, separate from control and chat.
Do not generate or manually copy another permanent credential. Where a worker
requires access to private material, use existing native vault ownership and a
private process boundary; never persist it in a public config or log it.

Specify a canonical, domain-separated device-signed binding of device reference,
RNS public identity, derived destination, protocol version and role. Verify the
reference from the public key, signature and destination derivation. Even when
the keys coincide, include these fields in the signed authorization transcript to
prevent cross-protocol or role confusion. Control countersigns a bounded grant
binding both device identities, FAMILY/entitlement and revision, roles, virtual
addresses, allowed mode, gateway consent, issue/expiry and audience. Signed negotiation
also binds data transport keys, both identities, roles, selected protocol/version,
path parameters, session nonce and expiry. The data handshake must independently
prove possession of the bound keys; reject relay substitution, replay and downgrade. A device
signature proves possession, **not entitlement**. Both peers validate the existing
Control trust anchor and revision floor; no TOFU and no shared family password.

Use RNS's destination proof and client identification plus fresh challenge/response
bound to the link/session, both peers, roles, grant digest and protocol domain.
No IP frame is admitted before mutual authentication and authorization. Retire
old-session replay state on reconnect; reject late callbacks and duplicate frames.
Re-check expiry/revocation while connected; authority unavailability must not renew
an expired grant. Pin the chosen gateway identity, not merely a matching family name.
Final wire format, maximum grant TTL and revocation convergence bound require tests
and review before RNS-1; they are not existing provisioning guarantees.

Threats: hostile bootstrap/transport node, Internet scanner, wrong-family member,
revoked device, replayed grant/frame, local unprivileged process, spoofed virtual IP,
resource exhaustion, network change and compromised authorized endpoint. Encrypt
end-to-end, authenticate and bound allocations/queues, enforce assigned source IPs,
expire stale sessions and deny arbitrary routing. A transport node can still observe
timing/volume and disrupt service; compromised endpoints can see their own traffic.
Reticulum alone does not guarantee reachability through CGNAT or allowlist filtering.

## Data plane and routing safety

Android: applications → VpnService → TUN → selected encrypted data transport → Windows.
Start with IPv4; preserve future IPv6 support. Reuse existing packet/framing/MTU
handling when suitable, with strict bounds, source validation and backpressure.
Specify extra framing only where the selected adapter requires it. Do not build
RNS IP fragmentation as a prerequisite; if that optional adapter is later selected,
validate its packet limits and bounded fragment reassembly separately.

Before any underlay connect or reconnect, Android must `VpnService.protect(fd)`
and bind the socket to a validated non-VPN `Network` as needed. Fail closed if
protection/binding fails. Bootstrap DNS must use that explicit network or pinned
numeric bootstrap addresses; application DNS stays in the tunnel. Library-created
reconnect sockets must use the same factory/guard, never bypass it. Guard against
selecting the VPN network itself and test Wi-Fi/LTE replacement.

Full-traffic Home Gateway captures `0.0.0.0/0`; route IPv6 into a blocked/captured
path until supported, so IPv6 cannot escape. DNS points to a resolver reachable
through the gateway. Keep the TUN and capture routes alive during tunnel loss;
drop/limit queued traffic and reconnect without silent direct fallback. Android
always-on/lockdown is required for protection across service death/reboot; ordinary
VpnService alone cannot guarantee OS-wide blocking after its process disappears.
Document that distinction and test both cases before advertising fail-closed.

Windows: broker-owned private gateway adapter injects/receives packets with source
validation, bounded forwarding and return-path state. Mode A explicitly selects
normal Windows egress. Mode B pins the existing Family Connect VPN interface and
blocks forwarding if upstream VPN fails. No second VPN stack or mandatory manual
Internet Connection Sharing. Select and validate application-managed forwarding/NAT
and narrow firewall rules before RNS-3; do not claim existing Wintun alone supplies NAT.
Use idempotent route/rule ownership and crash journal; remove only application-owned
state. Prevent routing control or data underlay recursively through this tunnel. No automatic
WAN port exposure, global firewall disable, or public SOCKS/HTTP listeners.

## Discovery and lifecycle

First PoC may use an explicit shared bootstrap RNS node for control and a
reachable data relay (possibly colocated, but separate roles). Both devices
make outbound connections; home address changes never edit device identity or user
configuration. Announce/path rediscovery follows underlay reconnection. Adapter
configuration supports a list of bootstrap paths and future direct IPv6, direct IPv4,
NAT traversal and RNS transport nodes; full NAT traversal is out of initial scope.

```text
DISABLED → DISCOVERING → CONNECTING → AUTHENTICATING → CONNECTED
                             ↑                          ↓
                             └── RECONNECTING ← DEGRADED
```

Use bounded connection/auth deadlines, health probes and exponential backoff with
jitter and a maximum delay; reset retries only after stable success. No busy loops.
Track control and data health separately. Loss of control need not interrupt a
healthy data session while its bounded authorization remains valid. Reconnect uses
reachable control or preauthorized unexpired paths; grant expiry fails closed.
On Android/Windows network change close stale sockets, cancel old generation work,
rediscover and reauthenticate; preserve capture policy. Persist only approved
configuration/identity, not ephemeral endpoints as identity. PC restart restores
explicit opt-in from protected state, obtains a valid grant and re-announces.
Mobile reconnect and home DHCP/router/ISP-prefix changes follow the same flow.
Shutdown cancels timers, closes links/IPC/TUN in policy order, joins workers and
removes owned routes; deliberate user disable must be distinguishable from failure.

## Feature gate and diagnostics

Proposed configuration: `home_gateway.enabled=false`, `experimental=true`, label
**Home Gateway Experimental**, explicit `direct_diagnostic` or `family_connect`
egress. One config switch disables the feature. These are planned names, not
currently accepted client options. Existing transport defaults stay unchanged until
real-world acceptance. Avoid UI polish until the data path is proven.

Record `mode=home_gateway`, `control_transport=reticulum`, actual `data_transport`,
`path_kind=direct|relay`, separate control/data states and ingress reachability, local Device Identity,
`gateway_device_id`, `rns_destination`, `path_state`, `connection_state`,
`session_age`, `rx_bytes`, `tx_bytes`, `rx_packets`, `tx_packets`,
`reconnect_count`, sanitized `last_error`, RTT/loss only when actually measured
(otherwise unavailable). Never log private keys, complete authentication tokens,
user packets or production DNS queries. Diagnostic exports need the same filtering.

## Milestones, test gates and delivery

| Gate | Required evidence | Current status |
| --- | --- | --- |
| RNS-1 / 5A–5B | Reachable control and data ingress under active target mobile restrictions; RNS negotiation and authenticated selected data session Android ↔ Windows; both identities; reconnect | Not run |
| RNS-2 / 5C | Real IP packets from Android TUN over the selected encrypted transport to Windows; virtual-IP ping or deterministic packet test, with return path | Not run; minimum implementation success gate |
| RNS-3 / 5D | Explicit direct-Internet gateway: HTTP/HTTPS, DNS, UDP and TCP | Not run |
| RNS-4 / 5E | Existing Windows VPN upstream; phone public IP equals VPN exit, not home ISP/mobile carrier | Not run |
| RNS-5 / 5F | Краснодар with active allowlist restrictions: mobile→home Windows→Family Connect; measurements below | Not run |
| 5G | Direct paths/NAT traversal and zero-config optimisation, informed by measurements | Planned |

Required unit/integration coverage: control reachable/data blocked and control blocked;
relay end-to-end identity/key binding, negotiation replay/downgrade; framing and malformed/oversized packets;
authentication/wrong-family/revoked/expired-grant rejection; replay/duplicates;
state-machine backoff and cancellation; route install/remove/rollback; tunnel/DNS
leaks including unsupported IPv6; loop prevention and unprotected reconnect sockets;
shutdown, gateway disappearance, endpoint change and upstream failure in mode B.
Existing tests must continue passing without weakening security assertions.
Mock tests, Linux loopback and cross-compilation are not Android/Windows acceptance.

Start reachability measurements at5A; repeat full acceptance at RNS-5. Record
evidence that allowlist restrictions are active, and test control and data separately.
For RNS-5 record device/OS/build/commit, operator and network type (no subscriber
number), bootstrap path, connection establishment time, throughput, latency, packet
loss, 30–60 minute stability, mobile-data off/on, Wi-Fi↔LTE and home-IP change where
practically possible. Explicitly mark untested scenarios. Optimise after measurements.

Implementation delivery must include changed-file list, design and library/license
decision, exact third-party portions if any, Windows gateway and Android PoC launch
instructions, automated tests with exact local commands/results, device evidence,
limitations, next steps and commit hashes. Launch commands do not yet exist; do
not invent runnable configuration for an unimplemented gateway. Real-device access
is a prerequisite for acceptance, not for writing implementation/tests.

Keep reviewable commits: (1) docs/legal licensing, (2) docs/rns design,
(3) core/rns abstraction, (4) windows/rns endpoint, (5) android/rns TUN,
(6) core/rns IP routing, (7) tests/rns security/reconnect, (8) docs/rns validation.
RNS-3 and RNS-4 should remain independently bisectable/revertible. Do not declare
the implementation task complete before at least RNS-2 passes on real devices.
