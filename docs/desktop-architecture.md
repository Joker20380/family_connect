# Desktop parity106 architecture — implementation in progress

The normative reference is `clients/shared/android106-reference.json`, not root
Android sources. The supported shared carrier is the dependency closure of
`wholedevice` and `restrictedowner` from the verified106 capsule (native105).
Only default-build Go library sources and their tests were consolidated. No
Android application, experimental commands, laboratory catalogs or assets were
copied. See [the parity report](releases/2026-10-23-desktop-parity106.md).

## Current implementation

Restricted chat now has a private multiplexed Linux parent/native lane sharing the
VPN worker's existing owner; bounded duplex mailbox/API calls do not use the4s VPN
control queue. See [bridge IPC bounds](adr/003-desktop-mesh-bridge.md#accepted-restricted-chat-adaptation).
Authenticated user/root existing-exit admission and the L01 protected DIRECT source
path now exist and L01/L01-R review is accepted in source/native/root→UID/kernel scope.
L02.2/local L02 review is accepted: local authenticated
cross-process handoff evidence for both manual and Auto/MESH owners, not live or
installed acceptance. No new GUI route selector is
introduced. Windows's native shared code builds, but its broker endpoint remains absent.

Linux AWG now journals exact platform resources before setup and reconciles them
after userspace TUN death; the inherited broad `awg-quick` policy-rule deletion
loop is not used. Manual/Auto transitions and component setup refuse pending
cleanup. See [AWG lifecycle and acceptance boundaries](clients/DESKTOP_AUTO_NORMAL.md#awg-ownership-and-userspace-process-death-phase17).

`carrier/desktopmesh` adapts accepted transport semantics without duplicating
ReliableStream, VP8/RTP, Family TLS or Mux in Python/C#:

- `Dial`: identity-bound readiness validation, signed directory/bootstrap,
  protected underlying sockets, authenticated dedicated media and Family TLS/Mux.
- P0/P1 only at the desktop boundary. RS32/32 is offered before Family TLS;
  effective peer limits and CREDIT128/LEGACY64 remain the negotiated core result,
  never inferred from the selected label.
- `TRANSPORT_READY` is not `CONNECTED`. `Activate` requires a successful platform
  packet/routing owner. The native worker now supplies Linux TUN and Windows
  Wintun/gVisor attachments; routing remains owned by the supervising service.
- Cancel precedes timeout; close cancels before waiting for attachment and waits
  for its own cleanup. Each connection owns its resources; stale close cannot
  close another connection. Linux service recovery now refreshes/validates materials
  before each replacement session, sharing its startup budget. Persistent-intent
  restart is implemented through the Linux systemd memory-only intent owner;
  installed root-service recovery remains unverified. The native worker owns health scheduling.
- Health102 allows a failed DNS probe only when the same authorized, ready session
  has increasing authenticated RX **and** TX within45s; three failed samples
  request recovery. The worker probes immediately after routing confirmation, then
  30s after each completed probe, with a5s total/2.5s per-target deadline. Fixed
  DNS targets1.1.1.1/9.9.9.9 and source10.79.1.2 use the current TUN, not the protected
  underlying socket path; Linux clears the underlay mark, Windows binds its TUN
  interface. Cancellation/interface replacement cannot produce a positive sample.
  Linux treats HEALTH_UNAVAILABLE as transient. Windows service wiring is still open.
- The106 record budget operates on a copy, retains first/latest detail and
  first-cause/counter summaries, counts every omitted middle detail, fails rather
  than returning truncated JSON. It is **not** a privacy filter. Its input must
  come from the typed/sanitized diagnostic collector. GTK bounded export is wired;
  native106 projection is source-compared; installed collection remains open.

The generic Unix bootstrap cache retains0600/no-follow/nonblocking flock.
Windows explicitly rejects that filesystem cache instead of pretending mode0600
is DPAPI/ACL protection. Windows must supply validated readiness from its existing
broker-owned protected vault to the in-memory provisioned path.

GTK's MESH option is gated by the installed, root-owned component capability check.
It calls FriendsOwner.connect_mesh with this computer's existing identity; a
temporary registration refresh failure does not prevent native validation of valid
cached materials. Local identity presence is not an entitlement or a bypass of
native authorization. No Auto-to-TCP relabel was added. The UI polls service states,
not process liveness; it does not run a second MESH recovery loop. Disconnect remains
available during restore and guard-preserving failure. A cancel during initial setup
is queued behind the bounded start operation, including an ambiguous/lost start reply.
Late polls cannot overwrite that explicit intent. Closing the window requires the
existing confirmation and explains that the system MESH service continues.

Selected next-session P0/P1 is distinct from the active session's requested profile
and measured RS effective-send/local-receive plus negotiated CREDIT128/LEGACY64.
No effective value is inferred from P1 selection. Route settings preserve unknown
fields with the existing atomic writer. Manual IP checking uses fixed bounded HTTPS
bound to fcmesh0, with no proxy, DNS lookup or fallback interface.

## Integration boundary / ADR

The common Auto selection/retry policy now lives in `carrier/desktopauto`; its
accepted sources, parameters and host obligations are pinned in
`clients/shared/android106-auto.json`.17 synthetic scenarios/160 trace records
match the exact accepted Java controller. Native private-pipe IPC, the Linux
guarded host/coordinator, root service and authorized GTK client are implemented;
installed VPN acceptance and Windows broker/GUI integration remain open. The host keeps a
verified guard across configuration, attempts and recovery; candidate close must
block before teardown. READY requires real packet/routing/DNS/health, not process
spawn. Explicit disconnect interrupts and serially drains the old attempt;
generation checks reject late callbacks. Generation/ownership continuity across
service restarts uses a journal and systemd-held sealed descriptor, not only an
in-process counter. DesiredConnected=false does not imply a failed guard is gone.

Current Linux manual helpers cannot simply be chained into this host: their
routing/cleanup are independent and MESH reserves an exclusive namespace. Service
underlying sockets need an authenticated, narrow bypass; permitting all traffic
to a server/DNS address or dropping the guard while switching is not equivalent.
This remaining integration is a delivery gate, not a reason to expose a fake Auto.

The cross-transport firewall component is now implemented in
`clients/linux/auto_guard.py`, with real isolated nftables/TUN packet checks.
It retains an owned blocking table between candidates, validates complete
readback, journals uncertain operations and refuses unsafe release or interface
reuse. [Guard contract and test scope](clients/DESKTOP_AUTO_GUARD.md).
`clients/linux/auto_policy.py` now invokes it from typed Go host calls; actual
native-process/isolated-kernel checks cover cancellation, late completion,
recovery and child death. Those checks use a synthetic platform, not a live VPN.
The root coordinator now joins these adapters. The guard itself does not create
protected bootstrap sockets, routes, capabilities or full health.

The native worker's separate `--auto-stdio` entry point has a32KiB exact-key,
null-rejecting schema and typed commands/callbacks, with no keys or configuration
payload. Shared Go policy owns timers and recovery; Linux owns privileged actions.
Cancellation waits for the one host operation to drain, then cleanup proceeds;
missing ACK terminates rather than overlapping callbacks. EOF retains containment.
`auto_mesh.MeshCandidate` supplies the actual single-attempt MESH path, sharing
`mesh_service.PacketSession` with the manual supervisor. The latter retains its
existing loop/timing; the Auto adapter has none. Both require native packet ready,
route/DNS readback, routed acknowledgement and native health, not process startup.
Protected normal configuration now uses the native `--normal-stdio` boundary,
the existing proof signer and shared profile grammar. Linux one-attempt AWG/TCP
adapters invoke the existing helpers under a private inherited guard lease and
retain exact cleanup intent across failure. Capability selection, coordinator
wiring, service ownership, root/user floor synchronization and GUI/service
authorization now have implementations and local tests. Installed handoff,
TUN/DNS/IPv6, crash/recovery and upgrade checks are still delivery gates. See the
[normal candidate contract](clients/DESKTOP_AUTO_NORMAL.md); local component
tests are not installed/live VPN acceptance.

See [ADR003](adr/003-desktop-mesh-bridge.md). GTK4/libadwaita and WinForms remain.
Linux helper and Windows broker/service retain their privilege boundaries. A
service-owned, packaged native child and private inherited pipes are the selected
adapter, not a new public network listener, shell command service or GUI-as-root.
Implemented source is distinguished from installed-product acceptance below.

## Native packet worker

`clients/mesh` builds `fc-mesh[.exe]`, not an Android shared-library copy. It uses
the accepted Xray revision/packet patch and gVisor pin recorded in the report.
Production entry points are version metadata, service-owned session stdio and
one-operation `--materials-stdio` and `--normal-stdio`, plus policy-only `--auto-stdio`;
none opens a public control listener. The following packet limits apply to
`--stdio`, not the smaller Auto schema.
Big-endian length-prefixed JSON has schema1,96KiB requests/512KiB replies,
duplicate/unknown-field rejection and monotonic IDs. Only start/status/routed/stop
are accepted; a process can start one session. No caller-selected executable,
shell, filesystem path, fixture, SOCKS listener or echo mode is shipped.

States are CONNECTING → TRANSPORT_READY → PACKET_READY → ROUTE_CONFIRMING →
CONNECTED. The service must install and verify routing/DNS before acknowledging
`routed`; process launch alone cannot yield CONNECTED. EOF/cancel ends the child;
packet-device failure cannot remain CONNECTED. Keys/readiness use private pipes,
are redacted in formatting and never placed on argv or written by this worker.

Linux sockets use SO_BINDTODEVICE + SO_MARK64640. Windows uses IP_UNICAST_IF in
network byte order, not an Android protect() stub. Windows has bounded Wintun
rings/channel queues and explicit read/write cancellation before adapter teardown.
Its code cross-builds, but driver/SCM/runtime are not accepted yet.

## Linux service source

`clients/linux/mesh-helper.py` extends the existing explicit pkexec authorization
boundary; the GTK GUI is never root. Authorization starts the fixed systemd unit
for the authenticated UID. Its socket is under a root-owned0711 directory,0600
owned by that UID; every connection checks SO_PEERCRED. The service accepts only
start/status/stop, strict bounded material fields, P0/P1; not network commands or
arbitrary paths. Existing Linux user-owned identity material may traverse this
private local IPC. Windows must instead retain broker-owned DPAPI extraction.

`mesh_service.py` runs one worker at a time and retains desired-connected intent
while that service lives. Transient failures use bounded backoff; explicit Stop
interrupts it, auth/protocol rejection never triggers weaker fallback. Failed
setup/auth remains guarded until explicit Stop. Restart intent is retained in
systemd-owned anonymous memory; isolated restart checks do not prove installed
root-service recovery. `mesh_system.py` journals only resource
ownership, never keys/readiness, and uses exact cleanup plus interface-generation
checks. ExecStopPost can replay that bounded journal after service failure.

`mesh_network.py` owns table64640/priorities10637/10638/10640 and fcmesh0 only.
Marked native IPv4 sockets use main with a prohibit fallback. Unmarked traffic
uses the dedicated table, with a low-metric TUN route and a persistent high-metric
unreachable default; IPv6 is unreachable. Losing the TUN therefore does not fall
through to main. No general server-address bypass, firewall flush or global DNS
rewrite. Per-link DNS uses resolvectl and requires readback. Existing nonstandard
policy routing/active VPNs are rejected, not overwritten. Updated AWG/TCP helpers
share a root startup exclusion lock and refuse startup while the MESH journal
exists; installation must update those helper copies together.

Desktop unit/regression checks and earlier isolated kernel TUN/rule tests pass;
current counts and source-specific receipts are in the continuing parity report.
The latter verifies capture, marked bypass, IPv6 rejection, TUN-crash containment
and exact route cleanup without touching the host namespace. It does **not** test
resolved, full native media VPN, helper installation or UI operation. These remain
release gates; production network state is unchanged.

## Readiness transaction / Linux component

`clients/shared/desktop-readiness106.json` maps exact accepted Java sources to the
common Go semantic port. Challenge/fetch proof, transient-only valid-cache use,
revocation/expiry/floors, issuer/directory equivocation and strict bounded JSON are
checked centrally, not reimplemented in Python/C#. TLS/protection/auth rejection
never becomes an availability fallback. The native materials adapter now lazily
starts the RNS byte worker only under the accepted challenge-network-failure policy;
it never replays an authenticated fetch over another route. Missing packaged runtime
still reports `relay_available:false`, not a simulated bootstrap path.

The RNS worker reuses the byte-exact106 Python channel and unmodified official
RNS1.5.1/pyserial3.5 sources. It owns only an ephemeral RNS identity, never the product
private keys. Its fixed provider and four readiness paths cannot be changed by IPC.
Device proof generation, envelope/status validation and all cache authorization
remain in Go. Requests carry at most8192B, responses at most90000B before private
framing; at most four exchanges share the bounded startup deadline. Cancellation
closes pipes and stops/reaps the child. Linux additionally cancels the materials
process group, covering its RNS descendant. Native and Linux owners each bound
temporary files to a private per-operation directory and remove it after process
termination, including forced child termination; no product identity lives there.

`scripts/build_desktop_rns.py` verifies installed dependency RECORD hashes and pins
the accepted channel before creating a deterministic zipapp with notices/inventory.
RNS discovers interface modules through filesystem globbing: the loader therefore
extracts bounded, validated members into a private0700 temporary directory, runs
the unchanged sources and removes them on normal exit/cancel. Direct zipimport
failed the actual-link test and is not the selected packaging model. Linux uses
fixed `/usr/bin/python3 -I -S`; the isolated runtime uses RNS's existing internal
crypto provider, not a new crypto implementation. Windows requires a bundled
`rns/python.exe`; that embedded runtime is not yet packaged or accepted. No host
site-packages, caller-supplied executable or external Python path is used.

Before its fixed IPv4 relay TCP connection, the worker binds the underlying device
and mark64640 on Linux, or IP_UNICAST_IF on Windows, with option readback. Changed
interface identity, loopback/self-TUN, IPv6 and cancellation fail closed. Actual
loopback RNS link tests do not substitute for installed protected-network acceptance.

Native preparation returns a byte-exact base64 storage proposal and SHA256 through
private IPC, always `durable:false`. Linux `MaterialOwner` persists even denial
proposals, using root0700 `/var/lib/family-connect-mesh` and per-UID0600 cache files,
fsync/atomic replace/byte readback. A second offline native cryptographic check of
the disk contents must succeed before the packet session starts. Keys are not
written there. A failed/torn transaction poisons its current storage owner.
Windows must implement the same transaction using its existing DPAPI broker vault;
the Linux cache is not a Windows storage substitute.

The service-owned materials IPC also has offline `receipt` and protected-underlay
`ack` operations. Receipt JSON has exactly the accepted17 typed fields. The native
code generates/signs/verifies protocol data but never reports storage durability.
Linux persists `{payload,ack_state}` in a separate root-owned0600
`<uid>.receipt.json` (maximum4096B) using the same fsync/replace/readback boundary;
the existing cache/identity formats are unchanged. It stores ACK_PENDING before
the independent challenge/proof exchange, then ACK_RECEIVED only after a matching
server response. Disk success is reported separately from server acknowledgment.
An ACK timeout or failed receipt write does not invalidate usable material.

On first use after service restart, the owner re-evaluates current cache and its
stored correlation context rather than retransmitting a potentially stale READY.
Without previous context it records UNKNOWN locally, with no ACK request. A failed
refresh that selects valid cached materials produces FETCH_FAILED for that import,
not a false fresh READY; cooldown-only reuse produces no new import receipt.
ACK gets at most15s within the existing startup deadline, shares explicit cancel,
uses fixed HTTPS/protected underlay and never enables weaker auth fallback.
Current developmental receipt version is `linux-0.2.11`, numeric2011
(major×1000000 + minor×1000 + patch); this is not Android versionCode106 and does
not change updater catalog sequencing. Windows will supply its own product metadata.

The existing user's identity is loaded without creation by `FriendsOwner.connect_mesh`;
only the private service request contains its seed. `LinuxMesh` authenticates root
SO_PEERCRED, exact UID socket permissions and root-installed protocol components.
It never silently disconnects another VPN or creates a second GUI reconnect loop.
Manual MESH is wired into GTK; the full reference interface/product is still incomplete.

`scripts/package_mesh_component.py` makes an offline unsigned private system-component
bundle from a race-tested native build plus `--rns` runtime build. Installation locks existing AWG/TCP/MESH
owners, refuses active services/resources, atomically replaces only known files,
keeps a root-owned rollback backup, verifies native and isolated RNS metadata and publishes its
capability marker last. Existing AWG/TCP helpers/modules are updated together;
their binaries/profiles and all user identity stores are untouched. No service is
started. The built archive has not been installed/accepted on the host.

The platform attachment must own packet engine, TUN, DNS and routes as one cleanup
unit, verify the path before reporting connected, and delete only its resources.
Bootstrap/media DNS, signaling and ICE sockets need per-socket underlying routing,
not broad address bypasses. Unsupported UDP/IPv6 must remain contained, not leak.
P1 access remains server-authorized for each computer's own Device Identity.

## Linux restart intent and user diagnostics

The existing unit now requires systemd254+, Type=notify and a one-descriptor FD
store retained across restart. `mesh_intent.py` keeps validated private startup
material in an anonymous0600 memfd, not a new disk key file. A root-owned `/run`
record stores only UID/generation/desired/recovery count. Explicit Disconnect
revokes memory before cleanup; the helper also revokes the disk fence when the
private socket is lost. Only a matching inherited descriptor may restart. This
does not implement cold-reboot autoconnect. Failed/absent credentials cannot create
a replacement identity or authorize a connection. Owned route guards remain during
backend restart; explicit stop removes only owned resources. The isolated actual
user-systemd test is not installed root-service/network acceptance.

`DesktopDiagnostics` lives in the existing `backend.py`, preserving the six-file
archive layout. It projects typed public counters/codes, session/startup facts,
bounded session history and lifecycle losses; it never exports raw logs, private
material, URLs, message contents or arbitrary exception strings. Records are at
most262144B and a ring/incident bundle525312B; size trimming preserves first/latest
detail and counts omissions instead of slicing serialized JSON. Atomic0600 files
are stored under `$XDG_STATE_HOME/family-connect/diagnostics/` (default
`~/.local/state/...`). Storage failure is reported separately and cannot disconnect
the VPN. `NativeDiagnostics106` now retains validated RS receipts, delivery/assembly,
boundary and Mux numeric arrays, correlation and complete startup fields. The
41-vector comparison uses the accepted five pure-Java projectors; terminal samples,
first failures and cached history are generation-fenced. Live collection remains
an installed acceptance gate.

`FriendsOwner` obtains this computer's Support ID through the existing authenticated
`support` proof and endpoint. It caches only schema/registration/Support ID in
`support.json` beside the existing identity, mode0600; mismatched identities and
corrupt metadata are rejected without key regeneration. GTK offers explicit refresh,
copy, privacy confirmation and a native JSON save chooser. Saving does not upload;
online support now has a separate explicit seven-day consent switch, identity-bound
private metadata, small allowlisted reports, authenticated digest-bound proofs,
completion-based60/300-second cadence and bounded cancellation. It runs only for
the GTK process lifetime; independent-service ownership and Windows remain open.
See [RU/EN support guide and exact limits](clients/DESKTOP_DIAGNOSTICS106.md).
No update catalog or product version is changed.

## Linux messenger owner

`clients/shared/android106-messenger.json` pins the accepted Python messaging
closure separately from the Go transport. The only shared platform delta permits
a trusted mailbox subclass to name normal OS routing `SYSTEM`; the default
DIRECT/EXISTING_EXIT/SERVICE_ONLY order and crypto/wire behavior are unchanged.
The exact patch is retained alongside the manifest. Android files are untouched.

`provisioning/chat_owner.py` owns one serialized LocalChat store and a process
lock, bound to the existing computer's Friends reference. Creating a chat account
is explicit. Resume never creates keys or replaces a failed/missing store. Data
is under `~/.local/share/family-connect/chat/`, with0700 directories and0600 files;
SQLite rows including the separate chat identity use accepted AES-GCM storage.
The32-byte storage key is in the user's Secret Service, not a file beside SQLite,
not derived by new cryptography and not copied from Android. Keyring requests have
a15s cancellation bound. No root GUI or server policy change is needed.

`chat_transport.py` retains SYSTEM for existing standalone consumers, but the Linux
daemon now creates DirectBridge + ProtectedMailbox: DIRECT, then authenticated
EXISTING_EXIT on permitted transient failure, never ordinary OS-route fallback.
The RNS/LXMF framing, public node identity and encrypted store remain unchanged.

<a id="linux-protected-chat-direct"></a>
### L01: fixed protected DIRECT (source/native/kernel, not installed/live)

`chat_direct_host.py` / `family-connect-chat-direct@.service` have an independent
per-UID lifetime: no Auto/MESH owner, TUN or route is created. The root-owned0711
directory contains a0600 UID-owned Unix endpoint; peer UID/device and exact bounded
messages admit only challenge/register or an authority-digest mailbox open.
No public request can choose origin, endpoint, resolver/interface, keys, commands or paths.
Root accepts mailbox authority only from the fixed HTTPS registration, matching
device/chat-public and positive bounded sequence/expiry (≤120s). Pending/denied,
expired, changed or equivocal authority cannot authorize a privileged open.
The digest selects that root-retained result; it is not a new server identity or grant.

The private root/native `--chat-direct-fd` adapter reuses `underlay.Network` and
`platform.Native.Protect`: bind/mark before connect, literal IPv4 destinations
(no DNS), strict HTTP bounds/identity encoding/no redirects/proxy environment.
Python reuses `Underlying` and rejects/cancels changed paths; protection failure
never opens an ordinary socket. API terminal/deadline/cancel and complete-response
no-replay semantics survive cleanup. User mailbox receives only the existing
CLOEXEC AF_UNIX proxy, with bounded duplex/half-close, capacity and expiry/cancel cleanup.
Fresh registration replaces the authority event; late cancelled results do not
publish it. Existing-exit native profile binding and VPN resources are untouched.

[L01 evidence](releases/2026-10-24-linux-chat-direct-l01.md): real owner/proofs,
disposable encrypted-store reopen, local TLS peer, native/kernel bind/mark and
guarded route verified. Full root/user component installation/dependency closure
and activation belong to L03; installed VPN and messenger acceptance to L04/L05.
The new user Python dependency is included in the existing bundle source list,
without a version/installer/catalog change. L02 service-only/handoff, Windows and
live gateway delivery are not accepted by this checkpoint.

### L02: service-only and process admission (local review accepted)

`mesh_chat_service` owns only a demand chat worker and verified Friends material,
not a VPN PacketSession or the user's connection intent. Root pins the trust anchor,
profile and resolver; public preparation cannot supply endpoint/key/command/path or
network overrides. Existing native refresh/inspect, cache floors/readback and
DeliveryMaterial validation are reused. A SERVICE_ONLY registration carries its
actual trusted route to ChatOwner/ProtectedMailbox, never root DIRECT authority.

The Go coordinator remains process-local. `mesh_ownership` supplies the missing
cross-process admission: root-only reservation and transport flock, inherited by
the worker; an unconfirmed-cleanup marker survives owner FD loss. Manual Supervisor
and Auto MeshCandidate reserve before bootstrap, cancel/drain the old generation,
and retain admission through native process exit and network cleanup. A chat host
observing VPN reservation closes its binding/worker before releasing admission.
Late generation results cannot republish the closed binding. A matching verified
VPN context can then be borrowed through the existing root endpoint/native owner;
country matching is never used. After VPN cleanup, a new authorized chat request
may prepare service-only again. Cleanup uncertainty deliberately blocks replacement.

The source service unit is not enabled or included as a complete chat component;
L03 must supply a coherent gated bundle, packaged anchor/dependencies and recovery
policy. Do not combine this service with an older ungated VPN owner. See the
[original L02 report](releases/2026-10-24-linux-chat-mesh-l02.md) for its earlier
synthetic-lane/idle-process limitations. The
[L02.2 gate](releases/2026-10-24-linux-chat-mesh-l02-2.md) now drives actual manual
Supervisor and Auto Coordinator/Guard/Platform/MeshCandidate through authenticated
OFF→ON→OFF with owned TUN, real private resolver/readback, native health and VPN
publication. Real broker binding/renewal extends the paired TLS/Mux fixture;
external rendezvous/media, room provider and DNS/fixed-service backing endpoints
remain local test replacements. Mailbox is a byte relay, not L05 LXMF/node.
No installed/live/F-01 claim follows. NEXT review D01.3, not automatic L03.

The public Host/ServiceHost cap stays at four live operations/mailboxes. A successful
probe/prepare reply is not yet a free slot: ChatBridge waits for EOF of that control
exchange, bounded by the original deadline and at most4s, with cancellation/close.
Host finishes monitor/lease cleanup first, then closes the control connection and
removes its active entry under the same admission lock. A dependent accept cannot
observe EOF yet charge the retired operation against capacity. Shutdown may close
connections earlier but also stops admission. Terminal replies stay typed without
waiting for EOF; trailing bytes fail DENIED. This is not a reservation against other
clients, a retry or an HTTP/open replay. The [D01.3 report](releases/2026-10-24-desktop-chat-admission-d01-3.md)
separates real public Unix IPC evidence from its synthetic native lane.

ServiceOwner retains one generation lease while authorized demand remains; each
operation atomically retains that specific native generation. Terminal status
fences admission and drains before replacement. Local CONTROL contention is
unknown availability, not terminal or proven healthy status; watcher defers it.
Protocol DENIED remains typed through cleanup. Release now waits for CONTROL
capacity within the existing4s submit deadline (still four CONTROL slots); a
timeout closes the lane fail-closed rather than silently losing a lease. A closed
lane/process alone never proves native cleanup or permits flock handoff.

Owned-TUN ingress is fenced during packet-stack initialization: incoming packets
are dropped until the actual Xray Start installs handlers, without buffering or
changing the accepted reference patch. Close fences/drains ingress before stack
teardown. This fixes the actual fdbased RX/handler-initialization race exposed by
the combined race-built gate; Attach/Probe/CONNECTED are not simulated.

GTK's bounded session client exposes profile/contact verification, rename, text queue,
edit, history, unread counts and stored-recipient receipts. Controls use accepted
RU/EN strings; clipboard copies only the public key. A separate non-root user-session
owner now continues enabled background delivery after the GUI quits. The GUI owns
neither the history key nor the live mailbox and detaches without closing the store.
The service serializes commands separately from registration/network work and joins
both before its own shutdown. See [ADR004](adr/004-linux-chat-session-owner.md).
Slow registration does not disable the composer or prevent committing an offline
message. Notification actions and service notices are implemented below; complete
reference thread composition remains open. Do not infer full messenger parity
from the working text path or local exchange tests.

Linux voice now uses `provisioning/chat_audio.py` and `chat_voice.py`. The accepted
source hashes/modes/limits are pinned in `clients/shared/android106-voice.json`.
Fixed GStreamer capture yields bounded mono S16LE PCM in memory (16kHz Opus,
8kHz Codec2); encoding/finalization/decoding runs off the GTK thread. Opus is
12kbit/s Ogg, Codec2 uses the public dynamically linked library (1600/2400/3200).
Captured PCM is at most60s, encoded audio131072B; playback decode is independently
bounded. No command/pipeline string, filename or network endpoint comes from UI.

One capture/playback owner, generation-guarded callbacks, explicit preview/send,
cancel/navigation cleanup and shutdown join keep old callbacks from reusing a
conversation. Audio draft/PCM buffers are cleared best-effort; Python/GStreamer
copies cannot be promised cryptographically erased. Audio is persisted only by
the accepted encrypted queue. The additive `desktop-voice-v1` encrypted record
stores selected mode/per-contact Codec2 confirmation without schema replacement.
Playback monitors sink removal/change and stops rather than intentionally
rerouting to a speaker. Real hardware/PulseAudio/PipeWire acceptance is separate.
The UI now has functional voice controls, not full accepted composer/menu geometry.

### Linux notification and service-event adapter

`android106-notifications.json` pins the accepted runtime/notification/service
handlers and shared validators; none of those shared files were changed.
`ChatOwner.tick` separates visible UI from enabled background delivery, preserving
lease expiry/denial and15s success/60s error mailbox cadence. Existing stores resume
without implicit recreation. The encrypted additive `desktop-delivery-v1` record
stores two booleans; no identity/schema replacement or plaintext history key.

`provisioning/chat_events.py` fetches only the fixed existing HTTPS feed path,
without credentials/redirects, using identity encoding and a1,000,000-byte bound.
Existing validation selects Linux notices;30s refresh cadence,8s socket timeouts
and16s chunk-loop deadline bound attempts. Invalid refresh retains valid cached
history. Signed LXMF notices still require separately pinned publisher authority;
neither contact trust nor a downloaded public feed grants it. There is no new
publisher-key configuration or operator grant in this work.

`chat_notifications.py` uses the user's session D-Bus, not the privileged VPN
helper. At most8 pending posts and64 tracked OS notifications; per-peer grouping,
finite3s calls and opaque action mapping. Notify reply success commits notified
flags; absence/error leaves them pending. The OS can still suppress presentation.
Unlike Android, desktop has no portable private lock-screen notification view, so
all content/contact names/service titles are omitted. Session daemon replacement,
late replies/close, event/message revisions and focused-view reads are fenced.
Displayed service history is newest first,50 notices/page, never silently dropped.
The GUI reads/marks only displayed revisions; neither messages nor notices execute
commands. Public update notices navigate to the existing Settings screen.

Independent user-service/closed-app delivery is implemented and checked against
isolated real systemd/Secret Service/RNS. Production Type=dbus, exact installed
bundle/upgrade/notification activation, host notification-daemon acceptance,
exact reference layout and installed acceptance remain unfinished.

### Announcement administration

`chat_announcements.py` implements the accepted service-notices toolbar, fresh
permission-checked list, compose, explicit preview and publish/edit sequence.
`chat_admin.py` reuses the existing device challenge/proof and HTTPS client;
each operation is authorized by the server, not a cached local role. The typed
same-UID D-Bus surface accepts only list offset and validated notice fields.
Publication retains the accepted all-platform/30-day default; edits cannot alter
author, created date, expiry, audience or kind. UTF-16 title/body limits match
Android160/4000 units. List50/page,1MiB response,32KiB write requests and16KiB write
responses are bounded; proof responses use the accepted16KiB limit.
Accept-Encoding is identity and encoded responses fail before decompression.

A new composition retains one publication ID across preview/back/explicit retry.
An edit retains revision and request ID;409 requires reopening the latest edit.
Unknown replies never trigger automatic retries. The encrypted D-Bus mutation
fence prevents re-execution after an ambiguous IPC interruption; semantic IDs
also protect a later explicit server retry. Page-generation fencing discards old
list callbacks after navigation. Revoking the role between preview and submission
is checked by the server. Tests use the actual accepted server authorization code
with synthetic identities/MockTransport, not production grants or publications.
Exact Android administration screenshots, installed acceptance and Windows port
remain open; four local GTK scales do not close those gates.

<a id="desktop-fleet-boundary"></a>
## Desktop fleet boundary / D05

**Статус: минимальная внутренняя Linux-граница D05 реализована; review accepted.**
[D05 evidence](releases/2026-10-24-desktop-provider-d05.md). Это подготовка Linux/Windows
parity106, не заявление поддержки dynamic fleet или завершения Windows-интеграции.
Единственная очередь — [PLAN / D05](PLAN.md#d05), после D03/D04. D05 не зависит от
production fleet, новых VPS или F-01 live; W01/W02 используют её модель, а не являются
предварительным условием D05. [Серверный fleet-контракт](stage5-fleet-contract.ru.md)
остаётся отдельным: операторский реестр не становится доверенным wire-каталогом desktop.

### Сущности и уровни доказательств

| Сущность | Значение и запрет подмены |
|---|---|
| Страна | Пользовательский фильтр, не уникальный сервер и не gateway identity. |
| Локальный ID варианта / target reference | Устойчивый идентификатор выбора внутри provider; не серверная криптографическая идентичность. |
| Подтверждённый `gateway_id` | Только явно полученный и проверенный по соответствующему протоколу ID. В старом Friends API отсутствует; модель должна представлять отсутствие, а не выдумывать значение. |
| Транспорт | AWG/TCP/MESH и выбор Auto — не server ID. Существующие `selected`/`preferred`, обозначающие транспорт, сохраняют смысл. |
| Requested P0/P1 | Намерение относительно профиля; отдельно от фактически согласованных native RS/CREDIT и profile context. |
| Активная сессия / generation | Фактически применённая конфигурация и владелец ресурсов конкретного поколения, не следующий выбор GUI. |

Предпочтение пользователя (selected-next), проверенное назначение и фактически
применённая конфигурация текущей generation хранятся и отображаются раздельно.
UI/model fixture не является новым доверенным assignment. Страна, endpoint, подпись
общего каталога или локальная legacy-ссылка не дают основания выводить `gateway_id`.
Новая внутренняя модель не меняет семантику действующих протокольных полей.

| Операция / evidence | Что подтверждается, чего недостаточно |
|---|---|
| Свежий authenticated fetch | Назначение только в пределах реально проверенного персонального ответа, identity/WG binding, trust/floors и действующей авторизации; не факт применения к сессии. |
| Offline inspect | Проверка уже предоставленных материалов по действующему контракту; не новый fetch, не новая персональная выдача и не доказательство актуальности серверного назначения. |
| Validate / `VALIDATED_MATERIAL` | Соответствие проверяемого материала условиям операции; не получение конфигурации и не разрешение normal-access fallback без свежего fetch. |

Проверка общего подписанного каталога сама по себе также не создаёт персональный
assignment. Offline inspect/validate нельзя превратить в offline normal-access
fallback. Это не отменяет отдельно предусмотренную принятой readiness-семантикой
проверку пригодного MESH cache: её условия не расширяются и не переносятся на normal.

### Provider, привилегии и lifecycle

Получение/проверка конфигурации отделяются от применения через существующие точки:
[`auto_configuration.py`](../clients/linux/auto_configuration.py),
[`auto_platform.py`](../clients/linux/auto_platform.py), native `--normal-stdio` и
Windows [`FriendsOwner`](../clients/windows/FriendsOwner.cs)/
[`broker`](../clients/windows/Broker.cs). Переиспользуются transport adapters,
общий Go Auto, проверки доверия и платформенные владельцы ресурсов; D05 не требует
переписать owners. Windows-подключение общего Go Auto остаётся W02, не готовой функцией.

Friends остаётся строгим legacy-provider adapter: RU/NL, **ровно два gateways**,
точные подсети/поля схемы, подписи, sequence/hash/floors, readback и действующая
семантика ошибок сохраняются. Новые серверные форматы подключаются позднее отдельным
явно версированным контрактом. Нельзя «поддержать fleet» удалением проверок legacy
wire schema или IPC, расширением RU/NL либо принятием третьего gateway этим verifier.

Новый GUI target-selection передаёт только допустимое пользовательское намерение.
Произвольные endpoints, server keys, команды и пути не становятся доверенными
параметрами privileged service. Это не утверждение об отсутствии передачи материалов:
действующая авторизованная, ограниченная и проверяемая передача материалов через IPC
сохраняется; D05 не меняет wire/IPC schemas и её проверки.

Refresh списка/нагрузки не вызывает apply/reconnect и не меняет работающую сессию.
`Platform.configure()` **не безопасный обработчик refresh**: участвует в lifecycle,
вызывает закрытие normal candidate и подготовку конфигурации. Изменение подключения
идёт только через существующего owner с отменой, завершённой cleanup и generation
fencing; поздний результат старой generation не применяется. D03 сохраняет окончательные
ошибки; review D04 stop/start/cleanup принят, его гарантии сохранены.
UI показывает фактическую активную сессию отдельно от выбора для следующего подключения.

Для MESH и заимствования VPN чатами сохраняется проверенный native profile context.
Совпадение страны или локального target reference не доказывает совпадения gateway/
profile и не разрешает заимствование чужой сессии. L01/L02/W04 остаются фиксированным
chat DIRECT/service-only, не произвольным служебным сетевым доступом.

### Совместимость и фактическая готовность платформ

Identity, WG keys, активация, Support ID, история и настройки сохраняются. Существующие
signed floors и счётчики нельзя разделять по новым локальным target IDs без отдельного
протокольного основания; выбор нового ID не сбрасывает anti-rollback. Android106,
accepted reference pins и действующие пользовательские подключения не меняются.

| Платформа | Уже имеющаяся граница и оставшийся gate |
|---|---|
| Linux | D05 использует target/assignment/applied модель в NormalOwner/Platform и hook после guard.ready. Native normal fetch/inspect, storage readback и transport owners сохранены; internal snapshot не расширяет IPC. Это не установленная fleet-приёмка. |
| Windows | Есть FriendsOwner/broker, существующая identity/vault и проверки Friends-конфигурации. Общий Go Auto интегрируется в W02, broker/native — W01. Linux readback не доказывает эквивалентный Windows runtime/readback; нужна собственная проверка на Windows. |

Capabilities объявляются только по реально интегрированным и согласованно упакованным
компонентам. Наличие общей библиотеки, fixture или cross-build не означает наличие
функции в установленном клиенте.

### Реализованная Linux-граница D05

В `auto_configuration.py` находятся `Target`, `Preference`, `TargetChoices`, `Assignment`
и `AppliedSession`. Legacy references `friends-legacy-v1:legacy-ru/legacy-nl` — только
локальные варианты. `NormalOwner.assignment()` принимает лишь объект, возвращённый
его успешным resolve после durable floor/readback/native inspect; offline verified/validate
такого права не дают. Assignment закреплён за owner generation, gateway_id остаётся None.

`Platform` фиксирует connection preference при создании существующего Runtime; configure
получает страну через строгий legacy target mapping, prepare требует assignment текущего
владельца. `GuardedHost` публикует applied metadata через `Platform.applied()` только
после open, проверки cancellation и guard.ready. Это подтверждение платформенного
применения, не самостоятельный признак CONNECTED/успешного live delivery: состояние
политики остаётся у существующего Coordinator. Ошибки/отмена/close/release снимают metadata.

`refresh_targets()` и `select_next()` меняют только память модели, не вызывают configure,
fetch, apply/reconnect/close или запись floors. `selection_snapshot()` — отдельный внутренний
read-only снимок без credentials/keys/profile bytes; существующий IPC snapshot не расширен.
В D05 нет GUI-команды или нового persistent формата: применение следующего выбора к новому
подключению через действующего owner, UI и миграция остаются L07/W09 и L08/W12.
Для MESH applied не подставляет normal assignment: точный native profile context и
правила chat borrowing остаются у существующего MeshCandidate, без равенства по стране/ID.
Новый provider/wire version требует отдельной интеграции; model-only варианты не добавляют
capabilities, `dynamic_fleet=False`. Windows использует эти понятия в W01/W02, не Linux evidence.

<a id="desktop-fleet-acceptance"></a>
### Проверяемый результат D05 и последующие gates

Адресная приёмка D05 должна доказать:

1. Модель различает все сущности и три состояния preference/assignment/active,
   оставляет неизвестный legacy `gateway_id` неизвестным и использует существующих owners.
2. Синтетический список из **двух NL-узлов и одного DE-узла** сохраняет выбор по ID
   при refresh и перестановке элементов, а не по позиции или одной стране.
3. Refresh списка/нагрузки не меняет active session и не вызывает apply/reconnect.
4. Callback прежней generation не применяется; смена соединения сохраняет owner,
   отмену и завершённую cleanup, а не вводит второй lifecycle.
5. Прежние RU/NL, точные legacy schema limits и отрицательные проверки сохраняются;
   тот же трёхузловой UI/model fixture **отвергается legacy verifier** как wire-каталог.
6. Capabilities соответствуют реально интегрированным компонентам, а отсутствующая
   Windows-интеграция не маскируется наличием общего Go-кода.

Модель/строгий adapter и эти адресные проверки — D05; реальное подключение Windows
broker/native/Auto — W01/W02. Список вариантов и selected-next/active UI — L07/W09;
согласованная упаковка и capabilities — L03/W10. Миграция с сохранением identity/history/
settings остаётся обязательной L08/W12. Полная установленная приёмка и точное описание
поддерживаемых возможностей — L04/W11/R01, не результат модельных тестов D05.

Адресные критерии D05 проверены в Linux source: 162 model/provider/platform/native/catalog
и 213 ownership/service/chat PASS, без skips/errors; native --normal-stdio использует
реальный worker и синтетические подписанные материалы. Installed/live/F-01 **NOT_RUN**.
Локальная подготовка D05 не является
F-01 live; dynamic fleet нельзя объявлять поддерживаемым до соответствующих интеграции
и приёмки. Серверные leases/renewal, production fleet/F-01, новый signing workflow,
новые VPS, Telemost multi-gateway и Django остаются отдельными задачами. Их проверки
также NOT_RUN; этот раздел не разрешает операции с ними.

## Reference checks

`python3 scripts/verify_desktop_reference.py` verifies supported source hashes.
`--capsule` also checks all2073 reference files, APK and restricted native bytes.
It does not claim signer verification or runtime acceptance. APK signer is checked
separately with `apksigner verify --print-certs`; its public result is in evidence.
`python3 -m scripts.extract_desktop_contract` reproduces the UI data from the
hash-checked capsule. Platform adaptations are explicitly recorded; hashes are
not silently updated to conceal drift. Default build tags must remain empty.
