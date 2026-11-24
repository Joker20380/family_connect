# CONTROL-HA — installed profile wrapper binding, 24 November 2026

Selected task: CONTROL-HA-20261123 / HA-02, installed receiver bindings following the
[SSH observation](2026-11-24-control-ha-ssh-binding.md). Source-only implementation and
isolated qualification, not deployment or a coherent-capture permit. Replication remains
PASS; the same three other HA-02 gates remain partial. No new numbered stage/version.

## Installed routes resolved without dispatch

Read-only probes reuse existing strict SSH pins/agent authentication. The previously
observed authorized-key contents and forced-command hashes bind the source lookup; command
arguments, key material and target data are not printed. Only identified source files are
read. No forced command, receiver import, database query, helper execution, SSH edit/reload,
lock acquisition or working-service action occurs. In particular, no gate is installed.

| Route | Observed entry | Finding |
| --- | --- | --- |
| RU root support reader | `friends-access/support-bindings-read.py` | source hash matches the repository reader; exact dependency closure still needs review |
| NL1/NL2 root registration | `friends-awg/awg-gateway.py register` | both installed entry hashes match each other, not the current opt-in repository file; do not replace them implicitly |
| NL1 root membership | `mailbox-pilot/accept_membership.py` | existing venv Python with `-B`; retain runtime/dependency bindings |
| NL1/NL2 restricted profile | generated snapshot launcher, not the archive itself | wrapper fixes its own Python, `-I -B`, request guard, cwd and environment before exec |
| Shared extra NL root route | command hash `7af31e3d…` | exact literal `/usr/bin/cat` plus one canonical absolute filename; no shell operators, target contents not read; not a Python receiver |

The cat classification is lexical dispatch evidence, not a blanket statement about all
root work, the daemon's loaded policy or source immutability. Do not install a Python
launcher over that route. Unrestricted/manual root writes still need explicit coordination.
The existing four Python receiver adapters do not automatically cover every shell command.

Installed entry hashes (private source copies remain outside Git):

- RU reader: `6ff3e2517267292c72e42d157dce3acb1f8d992c7cb1b2771b638e430511cdff`.
- NL AWG, both nodes: `69f32dbfdf0db5f57fb598d58935b5f2b098e53d0c0e2ac24517ad299ced26bf`.
- NL1 membership: `7e575dd6d3f030b1fc5e6398491088ad5e5a29a99331c14afa99f0d20f2d0023`.

At18:45:54.540410/18:45:55.073796UTC, two reads of each actual profile wrapper/archive
agree. Files are root-owned, single-link, regular, non-symlink, not group/other-writable;
wrappers are0755, archives0644. Both wrappers exactly match the existing renderer with
`READ_ONLY=False`. This preserves existing routing; it does not add a new renewal permission.

| Node/account UID | Wrapper SHA256 | Existing snapshot archive SHA256 |
| --- | --- | --- |
| NL1 /979 | `8bcb1b606ffd8e87c263694b70a22da6b2f392cdb7386e059f06186bdb6ce7c3` | `6dd51ead36a977abd4e6afee978d81df229ac767a6315bc4b2347328bde60c84` |
| NL2 /993 | `703c5653a2931dac1df773f4b87f7dd53fd1e3b3695fce26a61c21b071a8cbbc` | `4373585a7a16499ee0cae95fca2beb644f799153345ab4677ae0f2a927e18657` |

## Implemented binding

New opt-in `profile-launcher` kind in `control.capture_receiver` accepts the same six-field
private binding schema as existing receivers. `entry_path`/`entry_sha256` refer to the
**installed wrapper**, and `libraries` must contain exactly its one snapshot archive path/pin.
`capture_profile.command` extracts only literal COMMAND/READ_ONLY values and requires complete
byte equality with `build_profile_snapshot_launcher.render_argv`. Modified code, duplicate
fields, nonboolean mode, wrong flags/runtime, extra/missing/wrong archive all refuse before
admission. The command's Python path must equal the invoking `sys.executable`; this is a
path check, not an independent version/dependency/runtime-binary approval.

The existing wrapper is executed unchanged from sealed bytes after admission. Its native
SSH original-command/argument and optional read-only request guards still run; its chdir
and clean PATH/LANG/SSH environment remain effective. Only the expected `os.execve` transition
is intercepted. The original executable, argv, environment and cwd must match; then the
archive operand is replaced by its sealed `/proc/self/fd` descriptor. This deliberate pathname
change prevents reopening a replaced archive. No library is injected into the wrapper's import
path. The same child PID re-execs the native Python; the parent holds admission until final exit,
not the first ACK. No helper/Docker cancellation or independent external settlement is inferred.

Wrong input/native failure after admission conservatively keeps pending, even if the wrapper
rejected the request before any native effect. Parent death and broken replies keep uncertainty;
late child success cannot clear it. Tests verify that replacing wrapper/archive paths after load
does not change executed bytes. Existing raw `profile-snapshot` and other kinds remain available,
but are not substitutes for preserving these installed wrappers.

The closed deterministic receiver capsule now includes the profile validator and the existing
stdlib-only launcher renderer, plus its explicit `scripts/` namespace. New local artifact:
`4e9ab90f70e6353b20b73a232aba933efaa2d15204a7f80690d3cdeeb2f4fabe`.
The previous `41558e80…` artifact is not replaced in place or deployed. No application version,
public installer, update catalog or signing sequence changes.

## Qualification and exact limits

**186 tests PASS /0 skips** on Python3.14.4:
`test_capture_receivers.py`, `test_capture_profile.py`, `test_profile_snapshot_launcher.py`,
`test_capture_gate.py`, `test_package_profile_snapshot.py`. This covers the new chain and old
receiver behavior, canonical rendering, sealed execution, clean environment/cwd/UID, both
read-only modes, busy-before-input, malformed requests, pin/config refusal, ACK-before-exit,
parent death after re-exec, broken replies and retained pending. The fixture refuses host use.
Four changed documentation files/1046 local-link targets and whitespace checks pass; listed
external URLs are not claimed as HTTP-verified artifacts.

**Actual installed-wrapper stand PASS18:50:08.407583–18:50:12.369093UTC.**
`tests/fixtures/capture_profile/native.py` uses both exact collected wrappers and actual
UID979/993 in an owned disposable container. Python3.13.15 image is pinned at
`sha256:9d2e5553305c7c7b0097999bb17187c69b921ccd6bc9d40e4bb5ebe652c00285`.
Network is disabled, rootfs read-only, no Docker socket/live mounts; only fresh tmpfs targets
are writable. Caps are CHOWN/SETUID/SETGID, no DAC override. Native processes run under their
separate UIDs; gates/bindings stay0700/0600. Private inventory enters through stdin rather than
weakening a host file's permissions. Only closed public source files/capsule are mounted.

Both wrappers preserve their source bytes, runtime path, flags, clean environment, cwd and UID.
Both refuse busy admission and changed archive bytes. All owned containers are removed.
**Snapshot payloads are synthetic stdlib probes**, not the installed archive implementations;
the container's Python version/dependencies are not the installed Python environment. This
qualifies the wrapper/exec/admission mechanism, not actual profile data, privileged helpers,
package-relative pathname behavior, production runtime/configuration or in-flight settlement.
Those remain mandatory before activation. No live read/write request is used as a shortcut.

Initial fixture attempts fail on the intentionally protected host inventory and on root access
to another UID's0700 directory with DAC capabilities dropped. The corrected fixture streams
inventory and performs gate creation/readback as its owner. No permission widening was used;
failed receipts are retained. An initial unit run found a closed-FD cleanup bug, corrected
before the successful tests/stand; a reserved pytest parameter name was corrected as well.

## Evidence, rollback and next gate

Private evidence: `~/.local/share/family-connect/control-ha/20261124-receiver-binding-2h0m08r0/`,
root directory0700, reports/inventory0600, with earlier scoped path probes separately retained.
Closed stand source copies remain beneath private attempt directories, not in Git. Hashes:

- NL1 dependency receipt: `e907552c9eee47f68d49e03099fc95078ff6b25b26727d1f3a8199fca7e80471`.
- NL2 dependency receipt: `a1a947d7e5d80ae79483468a34cbbf46e8ec87e4b428049f054406e6e867387d`.
- Private inventory: `643f4cdfcd364192505411be7729b0ff409a6d123e9bd226a039811fbff311a3`.
- Native success receipt: `cf68e25c81c7e568ede3f53601864811ee0ec6fecbd0f9b117460e001e94c726`.
- Native fixture: `5b686a68a2d5c7aadae2eb4baec3e1982d6b477f0859e1c1aff7bb8588b75f85`.

No installed rollback is needed: only observation processes and owned isolated resources ran.
Retain installed wrapper/archive/command pins and current product data. A future approved
transition must preserve the old effective command and undo only its launcher/gate binding;
never restore an old DB, erase pending markers, delete root recovery keys or stop paid-watch.
Reverting to an ungated route invalidates capture readiness; source push is not activation.

Next selected work is the **remaining actual dependency/config/helper and external-completion
closure** for these resolved routes, plus the explicit bounded manual-write/deployment pause.
Do not redo the SSH census or this wrapper bridge/stand. Current NL scope still excludes
working-service deployment. Independently approve actual runtime/source/gate bindings before
activation, then qualify real flush/capture latency and overlap; current trust/key/access
custody and final combined recovery remain the other existing gates, not additional stages.
