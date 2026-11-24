# 24 November 2026 — joint drain without changing service identities

Selected task: CONTROL-HA-20261123 / HA-02, continuing the
[installed OWNER binding observation](2026-11-24-control-ha-owner-admission-binding.md).
The proposed separate-gate design is now implemented and qualified in isolation with
real UID10001 and UID1000 processes. It does not deploy the source, configure the installed
containers or complete HA-02. Replication remains PASS; the same three blocks are partial.

## Identity-preserving boundary

`control/capture_group.py` coordinates two to eight separate local gates. Each guardian
runs as its existing service identity and holds only that identity's gate. The coordinator
does not open another UID's gate, switch users, chown/chmod state, spawn programs, invoke
Docker/SSH or install a launcher. Existing0700 directories and0600 lock files stay strict.
No change to `control/capture_gate.py` or default application admission is required.

The trusted caller supplies already launched guardians, inherited Unix `SOCK_SEQPACKET`
channels, exact expected PID/UID/GID and gate device/inode pins. Both channel ends must
enable `SO_PASSCRED` before first use (`channel_pair()` does this). Each packet is checked
against kernel-supplied `SCM_CREDENTIALS`, not a UID claimed in JSON or Docker configuration.
Real/effective/saved guardian identities must agree; accidental setuid identities refuse.
Unexpected descriptors are closed and rejected, oversized/truncated/duplicate messages
refuse, and every exchange binds a fresh nonce. Gate/participant aliases are rejected.

This is a **same-kernel, same-time-namespace** protocol, not a fleet/SSH protocol. Peers
must match the coordinator's time-namespace device/inode and use the common monotonic
clock. The guardian verifies expected gate pins before drain and revalidates paths/inodes
before its final acknowledgement. Expected identities/pins must come from the approved
launcher/binding, not be approved by accepting whatever a peer reports.

## Interval and failure semantics

1. Send BEGIN to every participant; each independently closes new admission and drains
   existing admitted operations. Pending ambiguity markers still refuse admission to capture.
2. Require DRAINED from every pinned guardian, compatible deadlines and at least the
   requested remaining interval (default100ms). A late second drain is not added to an
   already expired first interval. Different-time readiness is refused before the body.
3. Yield a `Window` for the caller's bounded snapshot reads. Writers using either gate
   are refused throughout the jointly held interval; the caller must not dispatch writes
   back through those gates from inside the body.
4. After the body completes, require HELD acknowledgements from **every** same guardian
   with unchanged nonce/clock/pins/hold times and acknowledgement time after body completion.
   Only then set `window.receipt` to `LOCAL_INTERVAL_CONFIRMED`. It is `None` while the
   body runs and stays unset after any error, expiry, lost final acknowledgement or death.
5. Release only this group's channels/boundaries. Each guardian independently limits
   drain to at most5s, hold to at most2s and its total process protocol to at most7s using
   an exclusive kernel alarm. Coordinator EOF, SIGKILL or SIGSTOP does not depend on the
   coordinator running cleanup; inherited-channel leaks are still deadline-bounded.

These bounds assume normal scheduling and interruptible kernel I/O. Suspending a guardian
itself, uninterruptible filesystem stalls, real host load/flush latency and production
supervision are not qualified by this stand. The limits must not be presented as hard
real-time guarantees on the impaired RU host.

The caller must check successful context exit and the final receipt **after** its read
body; a partial copy produced before an exception must not be used as a coherent checkpoint.
The module does not collect/delete user files or remove uncertainty markers. A receipt
confirms only the participating local interval and always says `capture_permitted=false`
and `all_writers_qualified=false`. It is not independent approval, source attestation,
proof of external operation completion, a signed portable checkpoint or an HA-02 PASS.

## Validation

120 focused tests PASS /0 skips:47 new joint-drain tests,31 existing gate tests and42
OWNER binding-preflight tests. Coverage includes both gates being closed, drain of an
already admitted writer, retained uncertainty, wrong PID/UID/GID/inode, duplicate domains,
nonoverlapping/too-short intervals, changed clock, oversized/malformed packets, received
descriptor cleanup, replaced gate files, altered final ACKs, guard death, channel loss,
deadline/body failure and preservation of another operation's already held boundary.

At17:07:50–17:08:00UTC the final source also passes
`tests/fixtures/capture_group/native.py` in a disposable root container:

- Real guardians/writers run as10001:10001 and1000:1000, not mocked identity fields.
  The root coordinator cannot use their private gate through the ordinary Gate API.
- Two synthetic SQLite stores read `[1,1]` under the jointly held interval; both writers
  return BUSY during it and succeed afterwards, yielding `[2,2]`.
- Wrong identity and an unsettled operation refuse; the uncertainty marker remains.
  Per-UID ownership and0700/0600 modes are checked, not relaxed for the test.
- Killing the coordinator releases both domains; observed release/write/reap time0.288s.
  Stopping the coordinator releases through guardian deadlines; observed time1.873s.
  Resuming it produces REFUSED, never a stale successful receipt.

The runtime is the cached Python3.13 image pinned at
`sha256:d98cc29d3266e535dd9da1099688d9cb3ca4753813571e071763d17725460962`.
The stand has no network, read-only root/source, private tmpfs state,192MiB memory,
one CPU and48 PID limit; capabilities are dropped except CHOWN/SETUID/SETGID/KILL for
synthetic identities and owned-process cleanup. A fixture-only child subreaper reaps
orphaned guardians. Both owned labelled containers are removed and absence checked.
No host product state, keys, tokens, Docker socket or live DB is mounted in the stand.
This is not a native Django/PostgreSQL/publisher full-store capture or fleet recovery test.

Private evidence is retained outside Git under
`~/.local/share/family-connect/control-ha/20261124-joint-drain-dWEi57/` (private parent0700,
receipts0600; the source-only mount copies are readable within that private parent).
`control/capture_group.py` SHA256:
`57859b458a712d44dce4e70b48d44ad98460893064d19c32daafd3d631c42c19`.
The native fixture SHA256 is
`6313f77787c38b1e8b2d2470ac825dacb3aaf29815a2eafb89e68b677294232a`.
The earlier native pass is retained separately; test counts/runs are not added together.
Four changed documentation files/1032 local-link targets and whitespace checks PASS;
external URLs are enumerated, not qualified as live HTTP resources.

## Installed state, rollback and next gate

No installed service identity, image, environment, mount, SSH route, watchdog, version,
catalog or policy is changed. Last observed console/publisher images5ce82415/50de6f25
remain the installed reference, not this source or an automatically updated deployment.
No RU/NL connection or service operation occurs. There is no production change to roll
back. An isolated failed group closes its channels, waits for owned guardians to exit
and discards the unaccepted snapshot; never erase pending markers or start old failed units.

The distinct-UID joint-interval mechanism is no longer an unimplemented design gap.
Next finish approved effective source/config/argv/UID/mount/namespace/inode bindings and
actual/manual/SSH writer coverage, including the trusted guardian launch boundary.
Independently settle remote/asynchronous operations and qualify real capture/flush latency
before the overlapping all-store/fleet capture. Then obtain independent current approval
and off-laptop key/access custody and run final combined current/post-ACK/stale recovery.
Do not repeat this synthetic joint-drain qualification or accepted NL2 recovery. Current
NL scope still excludes working-service changes; paid-watch/deny enforcement stays on.
These remain the same three partial HA-02 gates; no HA-03/cutover or additional stage.
