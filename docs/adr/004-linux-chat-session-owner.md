# ADR004 — Linux user-session chat owner

Status: implemented in the working tree; isolated runtime checks passed;
installed/AppImage/upgrade acceptance pending. Product versions are unchanged.

## Decision

Keep the accepted Python messenger/RNS/store implementation behind a single
unprivileged `ChatOwner`, in `clients/desktop/chat_daemon.py`. GTK uses
`provisioning/chat_client.py`, not another crypto implementation or a root helper.
The fixed transient `family-connect-chat.service` runs under `systemd --user`,
Type=dbus, with the session name `com.familyconnect.Chat1`. No TCP listener,
boot-wide service, root GUI, arbitrary command execution or operator grant.
The existing Secret Service entry, computer binding, exclusive store lock and
encrypted database are reused without migration/recreation. The GUI receives
public profile/history data, never the storage key or private chat identity.

## IPC and lifecycle bounds

- One Request method at `/com/familyconnect/Chat1`; same UID verified by D-Bus.
  Explicit operations/argument shapes, duplicate-field rejection,262144-byte
  requests,1048576-byte responses, no server/key/route/shell arguments.
- One command worker and one network worker, at most8 queued commands and4 UI
  connections. Each client owns its connection and15s visibility lease. Bus
  disconnect removes only that caller; old callbacks cannot detach a replacement.
- Mutations carry a128-bit request ID and120s freshness. Up to64 live encrypted
  replay tickets retain request digest and result, not an unencrypted request log.
  Pending is committed before mutation; same completed request returns its saved
  result. Crash between mutation and result commit returns `operation_outcome_unknown`,
  never reruns the mutation. Live tickets are not evicted to admit another write.
  The UI instructs users to check history after an ambiguous send.
- Background/notification preferences remain encrypted. Mailbox leases and accepted
  protocol/cadence are unchanged. Six-second owner polling cannot start overlapping
  registration/exchange work. Notification content is still omitted; notices/history
  are paged, while inbox summaries omit message bodies.
- GUI Quit detaches. Enabled background delivery continues within the user session;
  disabled background and no attached UI stops the service after30s idle, observed
  at the next6s poll. A missing/locked store with no UI stops after60s idle; no
  key creation or store reset. Session bus loss terminates the owner.
- Production systemd restarts failures after5s, at most3 starts per120s. A40s stop
  deadline and whole-cgroup termination bound shutdown. No plaintext diagnostics
  are sent to the service journal. GUI initialization retries only startup/read
  paths; ambiguous mutations are not silently retried.

## Online diagnostic ownership

The same user service also owns optional106 diagnostic consent and collection.
`support_daemon.py` reads existing identity-bound consent and readonly Auto/MESH/
normal VPN status; it cannot create identity, start VPN or request a route bypass.
`provisioning/support_client.py` only projects status and explicit consent changes
into GTK. GUI shutdown closes its connection, not the uploader or saved consent.
One uploader is shared for the session; enabling again does not renew the seven-day
expiry. Valid consent keeps the service alive even with chat background disabled
or the chat keyring locked. Consent expiry/revoke restores ordinary idle shutdown.

Same-UID RPC admits `support_status` with no arguments and `support_consent` with
only a boolean and the observed128-bit revision. A dedicated single-worker control
lane admits one mutation independently of the bounded chat queue. Each accepted
change rotates the revision; restart also invalidates previous revisions. Lost
mutation replies require readback, never automatic replay or a false success.
No caller-provided snapshot, URL, path, key or executable crosses this interface.
Existing4096-byte allowlist, proof binding,60/300-second completion cadence,
deadline and expiry rules are unchanged. Collector failures report UNKNOWN rather
than inventing MESH readiness; terminal native data remains historical until a
new connection attempt, never proof of a currently working VPN.

Actual GTK/private D-Bus/user-systemd checks cover GUI exit, fresh collection,
service SIGKILL/restart, identity/consent continuity, stale control rejection and
revoke/idle exit. They use synthetic VPN and local API handlers, not live traffic.
Production Type=dbus, installed package, cold-login/autostart and logout remain
separate acceptance gates; no boot-wide service or new privileged owner is added.

## Launch and update boundaries

The full-bundle launcher handles `--chat-service` before GTK window setup. For
AppImage, the service reopens the original image, rather than inheriting a GUI-owned
FUSE mount. A verified notification peer opens `familyconnect://chat/<opaque-peer>`
in a separate user unit, retaining GApplication single-instance handling. Invitations
remain on their existing separate64-hex route. No notification can grant contact trust.

Installed production Type=dbus, fresh-window activation, mount retention and
logout need exact-package acceptance. A tested upgrade handoff must stop the old
chat unit after verifying the new bundle, wait for the store lock, then activate
the new code; keep old runtime/state for rollback. Neither this handoff nor the
six-file legacy-updater transition is implemented by this ADR. Do not remove user
history or Secret Service entries. No installer/catalog is signed or published.

## Evidence and limits

The root VPN worker now has a separate bounded private chat lane, documented in
[ADR003](003-desktop-mesh-bridge.md#accepted-restricted-chat-adaptation). ChatOwner
now uses `ChatBridge` for an existing authenticated MESH exit. A separate0600 socket
in the existing root-owned runtime directory checks SO_PEERCRED and this computer's
device reference against validated active readiness; API payload public identity
must match too. The client verifies the root peer. No root key, executable, resolver,
underlying interface or arbitrary destination can be supplied by the user process.

Four public operations at most use32KiB frames, fixed API paths and30s budgets.
Mailbox opens transfer one CLOEXEC AF_UNIX socket with SCM_RIGHTS; the root parent
pumps bounded16KiB chunks through the existing native lane, preserving half-close.
Caller cancellation, session retirement and shutdown dispose only chat resources.
Read-only probes precede a mutation; ambiguous dual owners fail closed, and a lost
mutation reply is not replayed. Direct HTTP TLS/auth/conflict rejection is terminal.
Phase22 used SYSTEM first, not protected-underlying DIRECT. [L01](../desktop-architecture.md#linux-protected-chat-direct)
now connects the Linux daemon to independent root DIRECT admission and native protection;
SYSTEM remains only in standalone/legacy consumers. Linux service-only orchestration
and Windows admission remain missing. No installed/live acceptance is inferred from local
Unix-socket, disposable-identity proof and byte-exact forwarding tests.

The continuing parity report records actual private D-Bus, Secret Service,
user-systemd and loopback RNS tests: GUI close → delivery/notification, SIGKILL →
same identity/history, crash after queue commit → no duplicate on replay, and
background off → service exit. The isolated bus uses Type=exec because the real
user manager watches its own bus, not the fixture bus; production Type=dbus is
not inferred from this check. Fixed launch arguments/UID/limits are separately tested.
No external traffic, user keyring, gateway, Android or server policy was changed.
This does not establish installed MESH, full visual/messaging parity or Windows parity.
