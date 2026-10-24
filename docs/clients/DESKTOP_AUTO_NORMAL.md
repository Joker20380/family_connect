# Linux normal Auto candidates / Обычные попытки Auto

24.10: source/component implementation with local tests, not an installed Auto VPN.
GTK exposes Auto only after verifying its separate root-owned capability marker.
Existing Linux0.2.11 and
Windows0.2.15 installations, identities, invitations and public catalogs remain
unchanged. No privilege elevation or network operation runs on importing modules.

## Protected configuration

`FriendsOwner.connect_auto` reads the computer's existing identity and verifies
both saved country catalogs while holding the existing state lock. It hands
identity/key material and signed floors to the authorized service boundary,
without issuing unprotected user-context HTTP, recreating identity or changing
the existing identity files. `LinuxAuto.start_auto` validates the exact request,
uses the existing polkit helper and UID-bound service socket, and records a public
pending receipt before submission. An unknown reply is never replayed. No
unauthenticated/new external listener is introduced.

The [native normal protocol](../../clients/mesh/normal/README.md) provides fresh
protected configuration and signed-floor checking. Shared Python profile grammar
is reused, not copied. The root owner atomically retains the common signed floor;
readback and native revalidation precede returning a usable platform profile.
Catalog-only inspect is not authorization. Failures never fall back to a saved
personal normal profile. Before manual configuration, the client reads the root
signed floor and merges it into a separate private `friends.catalog-floor.json`
under the existing identity lock. The full catalog signature/template grammar is
verified; this is not an access grant. Initialized missing/damaged floors fail
closed. Existing identity, WG key and per-country profile cache are unchanged.

## Real helper adapter, not another transport implementation

`clients/linux/auto_normal.py` implements one AWG/TCP attempt for the shared Go
controller. `auto_normal_worker.py` loads only the installed fixed root-owned
helpers and uses their existing profile parser, engine invocation, health check,
routes, DNS and teardown. No AWG/TCP/crypto implementation or executable selector
is exposed through IPC. The short-lived helper child is a privileged service
implementation detail, never a user-facing root GUI or general command runner.

Prepare journals the exact generated interface, endpoint, uid and generation
before importing a profile. Credentials are absent from the Auto journal. Private
profiles use the existing root0600 layout and metadata carries an Auto-generation
ownership claim. Atomic temporary names derive from that claim, so interrupted
writes can be removed without scanning/deleting another VPN's temporary files.
Only verified own metadata/profile files are forgotten after teardown.

The worker requires the actual inherited root-private guard lock description,
not merely a claimed PID, environment token, same filename or independent fd.
Requests have exact schema1 operation/profile fields; install/up require PROBE,
health requires READY, and down/forget require BLOCKED. Endpoint/port must match
the guard's plan. Existing manual starts refuse a present Auto ownership journal.
The internal MESH network owner can receive the same checked guard; ordinary
manual service calls cannot silently adopt it.

Component setup refuses pending Auto journals, including broken symlinks, even
when no TUN exists. Existing manual starts also refuse residual normal ownership;
only the checked root service may reconcile it before another transport starts.

The parent never treats process launch as CONNECTED. Original helper health must
pass, followed by actual interface/index/type readback and the outer guard's
ready transition. Auto still requires the coordinator's capability/route/DNS
acceptance and lifecycle integration. IPv6 is not claimed ready by this adapter;
the guard continues to block it rather than silently bypass the VPN.

The parent enforces the controller deadline, terminates/reaps its own subprocess
group on cancel/timeout and retains cleanup intent. Close blocks traffic first,
stops the original helper/service, checks interface absence and removes only its
own profile/temporaries/journal. Cleanup failure retains containment and prevents
release/new attempts. No second retry/backoff loop is added in Python.

## Проверено и не проверено / Verification boundary

46 local candidate tests cover existing profile grammar, typed commands, lock-fd
ownership, context/deadline, actual child reaping, partial-write recovery, foreign
state preservation and manual-start exclusion. Helper OS operations in these
unit tests are synthetic; no real AWG/TCP gateway or installed service PASS is
claimed. Full desktop/reference/configuration regression:744 PASS, no skips;
four setup checks additionally reject pending Auto guard/normal files or symlinks.
The actual compiled native process additionally covers36 catalog vectors.

The subsequent host/coordinator and root-service layers are described below.
Authorized GTK launch/activation and root/user floor synchronization were added in
phase16. Remaining: real installed AWG/TCP/MESH handoffs and per-OS
network/sleep/recovery/upgrade acceptance. No live user session,
server grant, production route, public package or Android build was changed.

## Root host and coordinator continuation

### AWG ownership and userspace-process death, phase17

`awg_lifecycle.py` keeps the pinned AWG engine/tools and existing validated profile;
it does not reimplement AWG. The root-only `/run/family-connect-awg/active.json`
journals generation, interface index/alias, exact resolver entry, sysctl baseline
and unrelated-rule fingerprint before mutation. Fixed table64620 and priorities
10619/10620 are reserved only if free. IPv4/IPv6 unreachable backup defaults stay
installed when the userspace TUN dies, preventing policy lookup from falling through
to the physical default. This preserves normal connected routes; it is not a new
arbitrary traffic bypass or a claim about MESH's IPv6 support.

The reviewed quick script is transformed in memory with exact source anchors. It
creates generation-marked nft tables/chains and interface aliases, but cannot run
the upstream broad loop deleting other VPNs' main-suppression rules. Cleanup uses
only journaled resources, including when the link has disappeared. nft1.0.6 omits
table comments in JSON, so a matching generation-named chain is mandatory; comments
are additionally checked when present. iproute2 string tables, null `not` flags and
`suppress_prefixlen` are handled explicitly, not by dropping selector validation.

Normal Auto cannot forget its profile while the AWG journal remains. Manual
Disconnect also calls AWG teardown for an absent TUN before another transport
starts; cleanup failure stops the transition. Setup refuses active/pending AWG
ownership. Unknown alias/index/marker/rule ownership retains the journal instead
of deleting unrelated resources. The creation-to-alias crash window deliberately
requires reconciliation if identity cannot be proved; it is not covered by the
successful userspace-daemon crash test. A changed unrelated policy prevents
resetting a previously-zero global `src_valid_mark` automatically.

Isolated acceptance installs the helper and pinned AWG3.1 engine in a disposable
network namespace, exercises real TUN/handshake/internal HTTP, kills only that
namespace's exact AWG daemon, verifies unreachable IPv4/IPv6 routing, then compares
routes/rules/resolver bytes/nft state with the baseline. A foreign suppression rule
and nft table must survive. This is not host installation, public-gateway MESH/P1,
sleep/resume or physical Windows acceptance. No host VPN resources are changed.

`auto_platform.Platform` now joins normal configuration and both candidate types
to `GuardedHost`. It reconciles only the matching normal and MESH journals before
fresh configuration. Native offline material validation runs first, including when
there is no physical route. Only a transient NETWORK configuration failure yields
no normal candidates and permits the shared controller to try restricted MESH;
AUTH/CONFIGURATION/INTERNAL/cancel remain terminal. This follows the accepted
AutomaticConnection.configure handler, not a weaker cached-profile fallback.

`Underlying` inspects the main routing table, live non-tunnel links and usable
IPv4 addresses. It does not mistake the client's own policy-routed TUN for the
physical path. Missing/down/VPN/ambiguous paths fail; index, gateway and address
changes invalidate the current path, including DHCP changes on the same interface.
The native underlay still protects actual sockets; this inventory is not a DNS or
application-traffic bypass. Native MESH rechecks its own protected routing too.

`Capabilities` checks trusted installed helper/engine/module files, the setup
marker, TUN device, TCP unit and required pinned AWG3.1 support. Missing runtimes
are not offered as available; an old AWG engine does not accept a3.1 profile.
This is capability filtering, not readiness: normal helper HTTPS/egress and packet
readback, or MESH native/TUN/routing/DNS/health, are still required before CONNECTED.
Normal-success hints contain only uid/country/transport, never credentials or a
restricted-mode authorization; the hint store cannot accept MESH as last-good normal.

`auto_runtime.Coordinator` owns one native policy process and one bounded monitor,
not another reconnect algorithm. It reports actual network availability, polls
the controller's own retry deadline, and uses the existing desktop15s health
cadence. Backoff and immediate restoration remain in shared Go. It serializes
attempts and cancels health before close; a close arriving just before health
registration also cancels that probe. Late CONNECTED replies cannot re-enable
intent after explicit Disconnect. Rejected native commands fail closed, rather
than being counted as progress. Terminal policy failure can revoke the service
intent through a supplied callback. It does not itself provide a public listener.

Local tests exercise this coordinator with the actual compiled policy process,
including success, AUTH-terminal behavior, transient normal→MESH, address-change
restoration without guard release and cancellation of offline recovery. Network,
helpers and guard operations in these tests are synthetic. No physical recovery
duration or real gateway acceptance is inferred. The service integration below
still requires installed resource/network acceptance and authorized GUI activation
before enabling the UI.

## Root service and IPC / Служба и IPC

`auto_service.py` and `family-connect-auto@.service` now join these real adapters.
The GUI remains unprivileged. The unit is packaged but not started or enabled by
component setup; the ordinary GUI authorization/launch adapter is still pending.
Do not infer an enabled Auto product feature from this service's presence.

The single-owner service uses `/run/family-connect-auto-runtime.lock`; it reserves
its guard under the existing global transport lock and refuses active manual VPNs
before applying new containment. Matching crash journals are reconciled under the
same uid/generation; normal/MESH cleanup precedes any explicit guard release.
It never executes a caller-selected command, path, gateway or interface.

`/run/family-connect-auto-ipc` is root-owned0711. Its `<uid>.sock` is0600 and owned
by that user; each accepted connection independently checks SO_PEERCRED. One exact
schema1 frame per connection,32KiB requests, four-second I/O deadlines and backlog4
bound the listener. `start` accepts only the seven validated material fields and
an optional normal-transport preference; `status` is read-only; `stop` requires
the exact32-hex public intent generation. Stale callbacks cannot stop a later
session. Status returns no credentials or catalog bodies. A successful start
receipt means durable intent/accepted work, not CONNECTED; readiness remains with
the real adapter and shared native policy.

`AutoIntent` reuses the manual-MESH sealed memfd machinery, with a distinct
`fc-auto-intent-v1` name and32KiB bound for two signed normal catalog floors.
Journal fields remain only schema/uid/generation/desired/recoveries. The private
identity and WG key stay in the systemd-held descriptor; they are not copied into
a new disk file. The manual MESH4KiB contract is unchanged and cannot consume an
Auto descriptor. Explicit Disconnect revokes the memory fence before cleanup,
including when writing the disk journal fails. An owner/service restart instead
closes the attempt while retaining containment and desired intent. Missing memory
cannot become CONNECTED or silently authorize a replacement identity.

The service's bounded shutdown uses native cancellation; an unreaped/failed owner
is fatal and the unit's control-group cleanup applies. The unit retains strict
filesystem/home protection, no core dumps and limited network capabilities. Only
the existing normal profile directories are added to writable paths. Installed
crash cleanup, including userspace AWG process death and residual route/DNS rules,
still requires actual OS verification; local mocks do not prove that gate.

Local combined regression:818 PASS/no skips; actual user-systemd tests exercise
both manual and Auto memfd recovery after SIGKILL and revocation before a second
restart. Actual Unix socketpair tests verify peer UID rejection and typed frames.
The policy process is real in coordinator tests; gateway, helper and guard calls
there are synthetic. The packaged root network service itself is NOT_RUN on the
installed OS. Root/user floor synchronization and authorized GUI launch are now
implemented. GTK uses the service generation to stop, shows actual transport and
only displays MESH negotiation from a live MESH snapshot. Old poll callbacks
cannot replace a newer action. Explicit cancel after an uncertain start resolves
status first, without replaying the start or blindly stopping another generation.
Closing the window explicitly tells the user the service continues; reopening
reads its state. Auto does not arm the old GUI-only TCP recovery loop.

`auto-capabilities.json` is separate from the legacy exact-key MESH marker. The
installer removes both markers before mutation and publishes them only after
verification; rollback preserves previous component files. Setup/start/stop share
a root command lock. IPC directory mode is explicitly set despite systemd's0077
umask; migration from a root-only directory rejects foreign entries.

No new user activation is needed or requested by this source work; no existing
identity was modified. Installed root socket ACL, TUN/driver, normal↔MESH handoffs,
network/sleep/crash recovery and upgrade acceptance remain mandatory. See report
phase16 for exact local tests, captured windows and private component hashes.
