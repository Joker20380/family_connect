# 25 November 2026 — legacy support final persistence and exit

Selected CONTROL-HA-20261123 / HA-02 stage2 continuation, on the implementation branch
`feature/device-technical-metadata-20261115`. **Old-process exit mechanism qualified in isolation;
working support is not stopped or upgraded.** This is not HA-02 acceptance, coherent capture,
external-delivery settlement or HA-03. No version, dependency, signed artifact or catalog changes.

## Boundary and mechanism

`scripts/control_ha_support_exit.py` adds a two-phase exit protocol around the already qualified
legacy application/RNS idle pause. It exposes preparation and authorization functions for an
independent supervisor, not an automatic production installation command. Exact19-source baseline,
loaded main/delivery/store-close code, RNS1.5.1, PID/start/boot/argv/cgroup, file pins, namespace and
store/runtime ownership are checked. The loaded SQLite filename must match the requested store;
no transaction may remain open. Receipts contain bindings/hashes, not messages, keys or private argv.

Before commit, the original serial main loop remains inside the callback, delivery is offline
without cancellation,3 producer loops and1 inbound drainer park after pending work finishes.
The controller must return an immutable commit matching the ready receipt and exact request hash.
Missing, expired or mismatched authorization restores admission/hooks without stopping the process.
The maximum360s precommit budget is **not a final persistence/termination timeout**.

At the commit boundary, queue/producer state is checked together under the existing locks; an
irreversible latch precedes the committed receipt. From this point no error or elapsed deadline
can restore admission. Idle native loops retire cooperatively at the pinned pause checkpoints;
the idle delivery thread closes without setting an active exchange's cancellation event. All are
joined. Unexpected Python/native workers or children refuse successful completion.

The RNS atexit callback is unregistered and run explicitly exactly once. Library error logging and
thread failures remain latched, including exceptions swallowed by native persistence. Native state
files/directories are fsynced, the encrypted SQLite store closes, its tree is fsynced, the bound
socket closes/unlinks and its parent is fsynced. Only after no writers/children remain and a durable
success receipt exists does the callback call `os._exit(0)`. It deliberately does not return into
the old pending IPC dispatch/periodic notification tick or execute the final RNS handler twice.
This is not a timeout kill of writers and is restricted to the qualified source/runtime shape.

Any failure after the latch parks the process indefinitely with admission closed and an error
receipt where publication is possible. It does not retry final persistence, return to old main,
force-stop, auto-rollback or report a successful exit. An independent supervisor must observe the
actual process/cgroup and systemd exit status; `exited.json` alone is not proof that exit happened.
The durable legacy-outcome uncertainty receipt remains: successful local fsync does not prove
remote delivery outcomes or authorize clearing a capture gate's pending markers.

## Qualification and retained failures

Final **82 checks PASS/0 skips in284.27s**:23 two-phase exit,22 reversible runtime pause and37 legacy
application-probe cases. These counts exclude preliminary runs and the additional system fixture.

```sh
FC_TEST_SUPPORT_BASELINE=/opt/family-connect-support/app \
FC_TEST_SUPPORT_PYTHON=/opt/family-connect-support/venv/bin/python \
python -m pytest -q -ra tests/test_control_ha_support_exit.py \
  tests/test_control_ha_support_quiesce.py tests/test_control_ha_legacy_support.py
```

The first run has9 PASS/1 failure: the synthetic final-write fault targeted an obsolete `.out`
filename rather than RNS1.5.1's `known_destinations.tmp.*`. It did not inject the intended failure;
the process correctly persisted and exited. The fixture target is corrected, then14 tests pass.
Subsequent coverage adds commit-receipt failure, controller death before commit, duplicate remote
invocation and tampering of each of the six staged source/request files. Synthetic tests also cover
pending delivery/queues/descendants/ratchet writes, malformed IPC waiting at exit, precommit expiry,
bad commit bindings, final write/fsync/store-close/success-receipt faults, SIGTERM during final
persistence and persistence continuing beyond the precommit deadline. Fresh processes decrypt the
stored data and read native known-destination/ratchet state.

At17:52:34UTC an additional actual system-level fixture passes under `fc-support`/`fc-support-ipc`,
the installed Python3.14.4, PrivateTmp, ProtectHome, ProtectSystem=strict, NoNewPrivileges and0077.
Its final native known-destination write stays blocked beyond41s, after the8s precommit budget and
old40s stop deadline. No systemd stop is submitted to the writing process. After release, the old
process exits0, NRestarts stays0, its cgroup is empty and a fresh process under the same UID decrypts
the store and reads native state. Observation takes41.400s after the writer enters final persistence.

The initial system fixture exited but was garbage-collected before independent ExecMainCode readback;
that attempt is **not** counted as a qualified systemd exit. The corrected fixture uses
`RemainAfterExit=yes` solely to retain the completed unit's status. Restart=on-failure and the old
control-group/SIGKILL/40s settings remain in the fixture. The active/exited empty unit is stopped only
after successful readback. This observation setting is not installed on the working service.

Private evidence remains in `/tmp/fc-ha-support-exit-20261125`; synthetic state remains under its
private `/run/fc-ha02-support-exit-*` paths. No state, archives, raw unit/argv evidence or keys enter Git.

| Evidence | SHA-256 |
| --- | --- |
| Initial9 PASS/1 failed fault injection | `7789a558e403597000e99fa7d72977339ecccda6d52360b64996f5fe0f586007` |
| Corrected14 | `9570d449ebd029ae76bae02d33351b602ee80989ac07683eabd73018cd3a2590` |
| Final82 JUnit | `e3c025cf8c4c1de6d9ebd67979d629102ba8a40a7d8aae6eb24114f508ba21ee` |
| Initial unretained systemd observation | `04d63d08d73be1f1868437ed9d88264f43926a9321406009711454a9e984bd3c` |
| Retained systemd exit/readback PASS | `d9cca15f63e5226120d8eb1e94e548e1bb8821b37395c9a09234788a84750e69` |

## Working state, rollback and next gate

Privileged pre/post checks retain working PID2022541/start/boot/command/cgroup,19 source hashes,
3 unit-file hashes,15 effective unit fields and interpreter digest. Support remains active/running
with0 restarts and the old40s/control-group/SIGKILL policy. No callback, stop, signal or replacement
is applied to working support in this continuation. No container, RU or NL operations occur.
The owner authenticates in the GUI dialog; the password is not captured. No sudoers/polkit changes,
permanent privilege or keepalive. The retained terminal is closed and `sudo -k` invalidates its timestamp.

The23-source support candidate remains `9d7bf840f3455d0ef2e7653dc9289aac2f0d77c9f2a0a8e305c786f7ddb80489`,
not rebuilt or installed here; its startup-only managed runtime is unchanged. Before commit, timeout
rollback restores only the old process's hooks/admission. **After commit there is no in-process
rollback.** A failed final write needs supervised reconciliation, not a new attempt or forced exit.

Next: qualify the resumable independent replacement supervisor, including transfer/preservation of
legacy uncertainty into the installed gate, actual empty-cgroup/exit observation, paired source plus
kill-policy installation, candidate startup/readback and code/config-only rollback using current
data. Do not deploy a kill-policy change alone, restore an old database, clear uncertain outcomes or
repeat the completed working reversible probe. Then installed UID/source/gate/sandbox and remaining
manual/OWNER writer coverage, coherent fleet capture and independent current trust/custody/approval/
full post-ACK recovery. Same three HA-02 acceptance gates remain partial; isolated replication PASS.
