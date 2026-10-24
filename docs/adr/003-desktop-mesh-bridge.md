# ADR003 — one shared MESH core, service-owned desktop bridge

Date:2026-10-23. Status: selected for implementation, not runtime-accepted.

## Context

Android106 contains native105 plus102 health,103 deadline/cancel and106 export.
Root desktop0.2.11/0.2.15 has real AWG/TCP but no media VPN or messenger backend.
An Android ARM64 shared library cannot be shipped as a desktop implementation.
Reimplementing the carrier or cryptography in Python/C# would create divergence.

## Decision

Consolidate the exact default-build Go dependency closure into `carrier/`, with
an inventory linking each file to the accepted capsule. Build native desktop
binaries for their target architecture. Keep the accepted packet/netstack
boundary, dependency pins and notices; audit any platform adaptation separately.

Integrate a managed native child under the existing Linux helper / Windows broker.
Use private inherited pipes with a versioned, size-bounded, strict schema. The
broker obtains its caller's own protected identity/readiness; the GUI cannot
submit arbitrary executables, paths, shell fragments or routing rules. Linux's
existing user-owned identity can be handed over through UID-authenticated private
IPC; the Windows GUI does not extract the broker's DPAPI-protected identity.
Material is transient in protected IPC/process memory, never argv, logs, a
plaintext Windows configuration file or CI. EOF and service cancellation must
stop the child and restore only its own network resources.

For Auto, share the accepted selection/retry policy in `carrier/desktopauto`, not
separate Python/C# reinterpretations. The platform service/broker implements its
typed host boundary: guard before configuration, real capability filtering,
verified-ready open, block-before-close and explicit release. Keep monotonic
session generations across all callbacks. The policy is implemented/tested as a
library and native private-pipe protocol. Linux guard invocation and a real
single-attempt MESH adapter are implemented. Normal configuration now shares the
existing native proof signer/protected sockets and Python profile grammar; Linux
AWG/TCP attempts wrap the original helpers using an inherited private lock and
generation-owned cleanup journal. Product coordinator/capabilities/handoff wiring,
root/user floor synchronization and persistent Auto service ownership remain
incomplete. The [normal adapter contract](../clients/DESKTOP_AUTO_NORMAL.md)
distinguishes local checks from installed/live acceptance.
Do not expose Auto in the product merely because this library passes tests.

The current Linux helpers are not a sufficient host by simple chaining: MESH owns
an exclusive policy-routing namespace, while AWG/TCP have independent cleanup and
routing. A handoff must retain a cross-transport fail-closed guard, preserve each
helper's protections and allow only service-owned underlying sockets. Removing
the guard between candidates or permitting user-wide endpoint/DNS bypass would
not implement the accepted contract. This integration remains required before
Auto activation; existing manual transports must not be weakened to make it work.

Linux now has a root-internal nftables guard in `clients/linux/auto_guard.py`:
an owned table, serialized private journal, atomic handoffs, exact root service
exemptions and name/index-pinned TUN allowances. Actual isolated kernel packets
exercise it, including calls from the native policy through the root adapter.
It is included in the private component workflow, not installed or integrated
into a complete product Auto coordinator or full desktop installer.
See the [guard contract](../clients/DESKTOP_AUTO_GUARD.md). Firewall permission
does not supply the still-required protected underlying route/socket path.

The protocol will distinguish validated material, authenticated transport ready,
packet path ready and installed routing. GUI `CONNECTED` requires the final
usable path. A failed authorization is terminal and must not trigger a weaker
fallback. Auto owns capability checks, attempts and recovery; manual MESH cannot
silently succeed through AWG/TCP. Persist user intent without cloning identities.

## Current code versus remaining work

Implemented: source manifest, supported shared core, narrow desktop session/
health/export adapters; both native worker builds with strict IPC and target TUN
adapters. Linux service source has authenticated control, staged routing/readback,
bounded recovery and journaled cleanup; real isolated kernel routing checks pass.
Shared readiness/cache/floors and receipt wire are implemented; Linux native proposal
→atomic storage→crypto readback is connected to service startup/recovery. Backend
identity/IPC adapter and offline component installation/rollback source exist, not
installed acceptance. Windows Unix plaintext cache remains fail-closed. Shared
health102 scheduling and GTK manual-MESH integration now exist. Linux receipt
storage and independently authenticated ACK are connected, with exact-schema
native generation and restart revalidation; acknowledgment is not disk durability.
RNS now uses a lazy bounded child with the exact106 channel and official1.5.1
library. A deterministic zipapp is extracted privately because upstream interface
discovery requires filesystem paths; upstream transport/crypto sources are unchanged.
Linux uses its existing system Python in isolated/no-site mode. The separate
Windows embedded runtime remains packaging work, not a user prerequisite.
Local actual RNS exchange is distinct from pinned-provider/system-VPN acceptance.
Not complete: installed RNS acceptance, Windows protected receipt owner/broker integration,
messenger, full diagnostics, actual OS/visual/upgrade acceptance and installers.
The Linux namespace check and Windows cross-build are not live MESH acceptance.
This ADR authorizes no server rollout or public catalog changes.

## Recovery and diagnostics checkpoint

Linux recovery implementation now uses the existing systemd manager's bounded FD
store (systemd254+) rather than persisting another private-key copy or running the
GUI as root. An explicit revocation fence prevents a stopped intent from returning
after backend failure. Root installed-service/TUN acceptance remains open despite
the passing actual user-systemd crash/revoke test. GTK now has a bounded offline
diagnostic export and own-device Support ID controls. Native106 projections and
explicit online consent are now implemented locally, with the independent non-root
[session owner](004-linux-chat-session-owner.md) collecting after GUI exit.
Installed Linux collection and Windows parity remain unfinished. See the continuing
report for exact source, package and rendered-check evidence.

## Auto ownership continuation

Linux Auto now hosts the shared native policy in one root service, with real
normal/MESH adapters, installed-capability filtering and physical-network
fingerprinting. Its user command socket is UID-bound and generation-fenced;
credentials remain in a separate sealed systemd memfd, not another private file.
Explicit Disconnect revokes intent before asynchronous teardown; daemon shutdown
retains intent and blocks/closes the attempt without releasing traffic protection.
The unit is included in the internal component, not installed or started here.
Actual user-systemd crash/revocation tests and native policy/Unix socket tests do
not substitute for root installed-TUN recovery. The ordinary GTK client now uses
the existing polkit session to start the fixed UID unit and validates root peer
credentials for its typed socket. Root/user signed-floor synchronization precedes
manual configuration. A separate verified Auto marker gates the UI; requested
Auto never substitutes for an actual MESH success. Windows
still needs its own broker boundary around the same native policy, not a C# fork.

## Messaging boundary

Linux now wraps the accepted Python RNS/LXMF owner instead of reimplementing
message formats or cryptography in GTK. A private Secret Service entry protects
the separate encrypted chat store; the existing Friends identity authenticates
normal chat enrollment but is never replaced or cloned. The initial mailbox uses
OS routing (SYSTEM), not an unverified protected-underlay/service-only claim.
Restricted delivery and Windows key protection/runtime are still required.
This separate user-context message owner does not expand privileged MESH IPC to
arbitrary destinations or execution commands. Background delivery and voice are
not implied by a working text queue.

## Accepted restricted-chat adaptation

`carrier/restrictedchat` now adapts accepted native105 `chat.go` and the106 Java
caller semantics into portable Go. Exact sources/limits are pinned in
`clients/shared/android106-chat.json`, checked against the complete accepted
capsule inventory. It reuses unchanged Family provisioning, TLS/Mux, service-stream
quotas and `restrictedowner.Coordinator`; no Python/C# transport or crypto copy.

One native owner validates cached delivery against this computer's64-byte identity
and32-byte public trust anchor before opening any network. Only a matching validated
profile can borrow an existing VPN. Otherwise the accepted service-only open uses
protected underlay, default P0 and a30s startup budget. There are at most8 leases
and4 service streams per authenticated session. Explicit VPN reservation cancels
and drains the former service-only owner before the new session is published.
Releasing chat never closes a borrowed VPN; expired/revoked/invalid material is
not rescued by a weaker connection. Parent IPC must enforce signed cache/floors
and single process ownership; creating another Owner per request is not valid.

The native VPN worker now uses `DialWithOwner`, reserves after material validation,
publishes its authenticated session/profile hash, and drains/releases its own
reservation on teardown. An old Close cannot remove a replacement reservation.
The Linux root parent now supplies a separate inherited Unix stream to that worker
(`--stdio-chat-fd`). The same owner serves VPN control and restricted chat; no second
transport process/coordinator is created. The child checks stream type and peer EUID.
This private channel is not a public GUI authorization boundary. A separate Linux
host endpoint now binds the user's UID/device to validated active readiness; the
ordinary-user ChatOwner can borrow only an existing exit. Its fixed32KiB/4-operation
API and real SCM_RIGHTS mailbox handoff are described in ADR004. Phase22 used SYSTEM
first; [L01](../desktop-architecture.md#linux-protected-chat-direct) now adds a separate protected
DIRECT root/native source path without extending this VPN-owned lane. Windows advertises
its endpoint as NOT_INTEGRATED; Linux service-only orchestration is still absent.

`clients/mesh/chatipc` uses strict length-framed JSON, monotonic request IDs and
out-of-order replies. At most12 jobs,8 leases and4 mailbox handles exist per channel;
frames are96KiB, mailbox chunks16KiB, operations at most30s. A stream admits one read
and one write concurrently. Cancel/release/close/status are handled outside the job
queue. Replies have a4s write deadline and retain their job slot while blocked, so a
non-reading parent cannot accumulate reply goroutines. IDs are channel-local and
never reused. Unknown/duplicate fields, incompatible arguments and arbitrary paths
fail closed. Release and channel shutdown invalidate outstanding work and dispose
late acquisitions/opens. API authorization/conflict remain terminal categories.

The Python `mesh_chat.ChatLane` has one reader, serialized writes and bounded pending
operations with reserved control capacity. It rejects unknown/duplicate/malformed
replies and never retries ambiguous writes. Native channel failure releases only
chat-owned resources, not the borrowed VPN. VPN stdin/stdout remains independently
responsive. Component packaging/install validation requires the new native protocol
capability; an older native executable is not accepted with the new parent sources.

Only `chat-api` and `chat-mailbox` virtual services exist. API allows POST to the
fixed accepted origin and challenge/register paths,8192-byte input,16384-byte
response/header bounds and30s operation budget. Redirects, proxy environment and
arbitrary URLs are excluded. HTTP400/401/403 and TLS certificate failure are terminal
denials;409 is terminal conflict, even when an error body is missing or oversized.
These status rules implement the accepted Java caller, not a new authorization
scheme. Raw replies/configuration redact their ordinary diagnostic formatting.

Portable `net.Conn` replaces Android JNI/socketpair. Explicit operation context
is separate from HTTP transport teardown so a TLS rejection remains a rejection,
not a cancellation or retryable failure. Stream cancellation, deadlines, half-close
and replaced-timer fences affect only that stream/lease. No routes or TUN are
created by the chat adapter. Local tests exercise real loopback HTTPS and stream
bytes with synthetic authenticated-session data; they are not media/provider,
installed Linux or Windows acceptance. Linux existing-exit public admission and the
separate L01 DIRECT source path are wired; service-only orchestration and the Windows
endpoint remain subsequent integration work.

## Rejected alternatives

- Standalone Linux echo/SOCKS benchmark as the desktop VPN: no system capture.
- Python/C# carrier forks: duplicate security/protocol state machines.
- Permanent elevated GUI: breaks the existing service trust boundary.
- Broad host-route exemptions or disabling containment: user traffic can bypass.
- Plaintext Windows cache for Unix API compatibility: loses protected ownership.
- Electron/Flutter/Avalonia migration: unnecessary and not requested.
