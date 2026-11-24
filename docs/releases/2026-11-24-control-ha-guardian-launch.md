# 24 November 2026 — pinned launch for separate-UID guardians

Selected task: CONTROL-HA-20261123 / HA-02. This closes the local launch implementation
left by the [joint interval](2026-11-24-control-ha-joint-drain.md), not production enablement
or the all-writer capture gate. Replication remains PASS; the same three HA-02 blocks remain
partial. No version, installed image, catalog, service, host policy or deployment changes.

## Launch contract

`scripts/package_capture_guardians.py` creates a deterministic, exclusive-create0600 zip
containing only the gate, group protocol, launcher, fixed entrypoint and package directory.
No application source, user configuration, DB, profile, key or binding is packaged. There
is no `control/__init__.py`, site hook, arbitrary entrypoint or extra archive member.

`control/capture_launch.py:launch` accepts an absolute private0600 binding path, its
independently supplied SHA256 and a source package path. It never creates a gate, changes
its ownership/mode, chooses an account or invents an approval. The exact schema1 binding
contains source/runtime SHA256, coordinator UID/GID, mnt/pid/user/time namespace device/
inode pins, uid_map/gid_map hashes and two to eight explicit guardian specifications.
Each specification binds positive UID/GID, sorted supplementary groups, absolute gate path
and all four gate device/inode pairs. Root guardians, aliases, unexpected fields, duplicate
JSON keys, invalid IDs, incomplete namespace pins and wrong hashes refuse. All guardians
are validated before spawning; each verifies its real/effective/saved IDs, groups, mappings,
namespaces, loaded interpreter hash and gate inode/mode/ownership before sending READY.

Source and request bytes are sealed memfds before spawning. Children execute the pinned
already-open interpreter with fixed `-I -S -B`, cwd `/`, only LANG in the environment, null
standard streams, close_fds and an explicit descriptor allowlist. The root caller drops to
each approved service identity **before exec**, not in an imported application hook.
Non-root callers may only retain their exact current UID/GID/groups. Unix packet channels
verify READY using kernel PID/UID/GID, followed by the already qualified group protocol.
Replacing the source pathname after launch cannot change the executing sealed sources.

Startup has a three-second coordinator deadline and a child startup alarm. The existing
guardian drain/hold deadlines apply after READY. Cleanup closes channels and terminates/
reaps only Popen-owned children, including partial spawn, malformed READY, lost peer and
body failure. No PID discovery, kill-by-name, Docker stop, remote command or service restart
is used. Scheduling/uninterruptible-I/O limitations of the prior interval remain; this is
not a hard-real-time guarantee on an impaired host. Partial work is never a valid snapshot.

## Trusted bootstrap and explicit limits

`scripts/control_ha_guardian_probe.py` is a standalone **stdlib-only trusted entrypoint**.
It requires isolated Python without site loading, verifies independently supplied source
SHA256 before importing any package code, seals it and imports from that descriptor. Root
launch additionally requires gate/group/launch imports all to originate from that same
sealed approved archive; an ordinary checkout import is refused. The bootstrap accepts no
arbitrary command, callback, code string, environment override or identity-changing option.
It only launches guardians, confirms a local joint interval and exits with a redacted JSON
receipt. Its successful output still has `capture_permitted=false` and
`all_writers_qualified=false`. No live snapshot or new writer admission setting is made.

The bootstrap itself and the interpreter/stdlib are a **prior trusted installation/input**,
not self-authenticated by this tool. A privileged operator must independently verify the
bootstrap before executing it from protected trusted storage. Never run `sudo python`
against a mutable worktree as a shortcut. The runtime executable hash does not attest all
stdlib/shared-library files. An operator must approve that runtime separately. The package
and binding digests must come from independent approval, not be silently computed and
accepted from the same untrusted input. The fixture generates its own synthetic approval
only to qualify mechanism; it is not production approval or a signed recovery checkpoint.

Namespace/map/inode agreement here binds **guardian launch**, not installed application
source/config/environment, loaded workload bytes, every mount or every writer. No namespace
entry, Docker exec or file-descriptor transport across SSH is attempted. This remains a
same-kernel protocol. Docker user-namespace mapping, bind-mount topology and actual service
participation must be approved before any production use. Existing manual ORM, direct SSH,
unadmitted shell writers and outstanding remote/asynchronous operations remain gaps.

## Validation

179 focused tests PASS /0 skips:59 launch/bootstrap tests,47 group,31 gate and42 OWNER
preflight tests. They cover successful real subprocesses, closed writers and later release,
source pathname replacement, preserved environment isolation, invalid hashes/IDs/namespace/
map/group bindings, duplicate fields, symlink/hardlink/FIFO/oversize inputs, archive closure,
sealed-source mutation refusal, wrong gate, child death, partial spawn, wrong READY and
startup failure cleanup. Standalone cold-process bootstrap passes; wrong source/binding or
missing interpreter isolation refuses. An unverified package is not executed.

At17:29:37–17:29:42UTC the final native fixture
`tests/fixtures/capture_launch/native.py` passes inside a disposable root container:

- Sealed verified root imports and the standalone trusted probe both work.
- Actual guardians and writers run as10001:10001 and1000:1000, with empty supplementary
  groups. Both writers refuse under the joint interval and work after release.
- Source pathname replacement cannot affect launched children; a fresh launch refuses it.
- Wrong gate pins refuse; launched children are reaped and no gate is left held.
- Per-UID0700/0600 ownership/modes remain intact. Permission inspection runs as each owner,
  not by weakening permissions or giving the root coordinator DAC override.

Pinned cached runtime:
`python:3.13-slim-trixie@sha256:d98cc29d3266e535dd9da1099688d9cb3ca4753813571e071763d17725460962`.
No network; read-only root/source, private tmpfs,192MiB/one CPU/48PID limit; all capabilities
dropped except CHOWN/SETUID/SETGID/KILL for synthetic identities and owned-child cleanup.
No host product state, secrets, DB, Docker socket or service mounts. All owned labelled
test containers are removed; absence checked. Earlier fixture failures were source mount
traversal and root permission inspection without DAC override, not production failures.
They are retained separately and not counted as accepted runs. The earlier group death/
deadline tests are reused, not represented as a new production latency measurement.

Private evidence outside Git:
`~/.local/share/family-connect/control-ha/20261124-guardian-launch-IzbDJU/`.
Parent0700; source-only mount copies readable within it; receipts0600. Final native receipt:
`final-accepted.log`; focused test receipt: `final-tests.xml`.
Source SHA256 `control/capture_launch.py`:
`1c11ee5a95c048b8bfe3dc16608ae84de5a4132e90a23cc9ba4878c3a65275c0`.
Bootstrap SHA256:
`46d2f9b410291f3870655b876a8ba15689d5674294e9ddeed560633d2770de78`.
Native fixture SHA256:
`b2e4af05197045997892aa87b325d293108bca5822f051dd743f9c534684908c`.
Four changed documentation files/1035 local-link targets and whitespace checks PASS;
external URLs are listed, not qualified as live HTTP resources.

## Installed state, rollback and remaining gate

There is no production change to roll back. Last observed installed OWNER images remain
console5ce82415/publisher50de6f25 without configured gates; no new installed observation
or automatic rollout is claimed. RU/NL are not contacted. No watchdog/deny enforcement,
working service, existing failed unit, UID, token ownership, SSH route or public artifact
is changed. Source/package/probe availability does not authorize deployment.

On failed isolated use, close owned channels, reap owned children and discard the incomplete
copy/receipt. Never erase pending uncertainty markers, restore user state automatically or
start previously failed/stopped services as rollback. Future integration must keep this
probe disabled until independently approved binding and rollback criteria are satisfied.

The local guardian launch gap is now implemented and qualified; do not rebuild it or repeat
accepted NL2 recovery. Next bind **actual workloads and manual/SSH routes**, settle external
operations independently and measure real flush/capture latency. Then qualify a coherent
all-store/fleet interval, independently approved current trust/off-laptop key/access custody
and final combined current/post-ACK/stale recovery. No new lettered stage or HA-03/cutover.
