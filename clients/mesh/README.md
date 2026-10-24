# Service-owned desktop MESH bridge

**Development component, not an installer or standalone accepted VPN.**
GTK/WinForms integration and real-system route/DNS acceptance are still pending.
`--version` is read-only. `--stdio` is for the existing privileged service only;
do not run the GUI as root/admin or feed keys on the command line.

## Source and build

Carrier code is pinned by `../shared/android106-reference.json`. This module
reuses the accepted Xray/gVisor packet boundary; the local patch is the exact106
patch, not the older root Android build patch. Original notices accompany builds.
No Android binary is bundled; desktop targets compile their own native code.

```
python3 -m scripts.build_desktop_mesh --go /path/to/go --xray /path/to/pinned/Xray-core --os linux --out /fresh/output --test
python3 -m scripts.build_desktop_mesh --go /path/to/go --xray /path/to/pinned/Xray-core --os windows --out /another/fresh/output
```

The builder requires Xray commit `d2758a023cd7f4174a5a5fa4ff66e487d4342ba0`,
uses Go1.26+ and gVisor `v0.0.0-20260122175437-89a5d21be8f0`, rejects experimental
build tags and records source/module/license/binary hashes. Sources must remain
unchanged during a build. `--test` cannot execute a foreign-OS binary.
Windows requires the existing verified official `wintun.dll` packaging workflow;
the builder does not invent or download a replacement driver. Expected existing
driver SHA256: `e5da8447dc2c320edc0fc52fa01885c103de8c118481f683643cacc3220dafce`.
Neither the worker nor a successful cross-build establishes Authenticode trust.

## Private pipe protocol v1

Each frame is a four-byte unsigned **big-endian** length followed by UTF-8 JSON.
Requests:1..98304 bytes; replies at most524288 bytes. Unknown fields, duplicate
object keys, nesting beyond16 and invalid schemas/actions are rejected. Secrets
are never put in replies or formatting/log output. EOF stops the connection.
The broker owns both pipes and the child's executable; no TCP listener, shell,
caller-selected executable, file path or arbitrary route command exists.

Every command has `schema:1`, a strictly increasing positive `id`, and `action`:

- `start`: exactly once per process; `start` object with `attempt`, `budget_ms`
  (1..200000), `profile` (P0/P1), numeric IPv4 `resolver:53`, `underlying_index`,
  raw JSON `readiness`, base64 `identity` (64 private bytes from **this computer**)
  and `anchor` (32 packaged public bytes). The broker, not the GUI, supplies these.
- `status`: bounded metadata/sanitized native snapshot; no credentials/room URLs.
- `routed`: only accepted after `PACKET_READY`. The service must first install and
  read back its own TUN address/MTU/routes/DNS/leak-containment policy. This is an
  authenticated service assertion, not permission for an arbitrary GUI to assert it.
- `stop`: cancel any startup/route wait/session, drain owned packet resources, then
  acknowledge `DISCONNECTED` and exit. A second `start` cannot replace a session.

Stages: `CONNECTING` → `TRANSPORT_READY` → `PACKET_READY` → `ROUTE_CONFIRMING` →
`CONNECTED`. No packet interface or native process alone is CONNECTED. The service
has30s to acknowledge routing; failure closes its packet path. A new process is
required for a new session, so old callbacks cannot mutate a replacement worker.
The service owns route/DNS cleanup, including ExecStopPost/crash cleanup; this
worker cannot claim those service integrations are complete yet.

## Platform packet/protection mechanisms

- Linux: exclusive nonpersistent `fcmesh0` TUN,1280 MTU gVisor endpoint; refuses to
  adopt an existing interface. Every underlying socket gets SO_BINDTODEVICE and
  SO_MARK64640. The service must reserve an exact mark/rule/table policy; no global
  endpoint-address bypass is used. GUI remains unprivileged.
- Windows: exclusive owned Wintun adapter `fcmesh0`,1280 MTU endpoint, bounded
  channel and8MiB Wintun ring. Reader/writer ownership stops before teardown.
  IP_UNICAST_IF (WinSock option31, index in network byte order) binds service
  connections to the selected underlying interface. No Android protect stub.
- Core policy permits IPv4 TCP and DNS, rejects other UDP/IPv6. OS-level capture
  must still contain unsupported traffic; packet filtering alone is **not** a
  DNS/IPv6 leakage test. Windows driver, socket-binding and physical TUN acceptance
  are NOT_RUN until tested on actual Windows.

Tests with an injected data plane are explicit library/packet tests, not a hidden
runtime fallback. The shipped entrypoint always uses real `desktopmesh.Dial` and
real platform attachment; it has no fixture/echo/SOCKS mode.
