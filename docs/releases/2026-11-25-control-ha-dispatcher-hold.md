# 25 November 2026 — bounded OWNER publisher dispatcher hold

Selected task: CONTROL-HA-20261123 / HA-02. This implements the publisher **new-dispatch
inhibition** part of the controlled OWNER drain, not another acceptance stage. The earlier
[stopped replacement executor](2026-11-25-control-ha-owner-replacement.md) and installed
[collector participation](2026-11-25-control-ha-collector-activation.md) are not reimplemented.

## Operating contract

`scripts/control_ha_dispatcher_hold.py` binds the existing original publisher image, exact
Compose role/name/startup command, healthy running container and its sole init child. The
target is the scheduler shell, not docker-init, the container, Python publication process,
process group, database backend or console. Kernel identity includes start ticks, parent,
all UIDs, command/cgroup digests, PID namespace and single-thread shape. Signals use pidfds;
the implementation does not signal a recycled numeric PID or require root/extra capabilities.

Only the shell receives SIGSTOP/SIGCONT. Its already dispatched child continues independently.
This prevents another shell iteration while held; it does not cancel HTTP, PostgreSQL commits
or support IPC. A child exit, zombie, empty queue or returned HTTP ACK is **not** settlement.
The earlier [late-commit publication proof](2026-11-25-control-ha-publication-settlement.md)
remains applicable; `work_settlement_proven` and `capture_permitted` remain false.

The single-threaded launcher creates two separate-session helpers before arming the stop:

- Guardian confirms the rescue lifeline, exact target identity and deadline, stops the shell,
  confirms kernel state T, then holds until release, controller pipe EOF, rescue loss, target
  death or the deadline. Its finally path resumes the same pinned process.
- Rescue independently observes the guardian pidfd. On its deadline it kills **only this
  owned guardian**, waits for confirmed exit, then resumes the scheduler. Killing a stuck
  guardian before SIGCONT prevents a delayed guardian from subsequently stopping the target.
- Guardian death causes rescue to resume; rescue death closes its lifeline and guardian resumes.
  A surviving controller also resumes after both helpers have been confirmed exited. No helper
  signals a child workload. Both helpers inherit the private nonblocking exclusive lock, so a
  controller crash does not release it prematurely. Concurrent normal CLI holds are refused.

There is no renewal, permanent maintenance flag or unit/config modification. The library lease
is bounded to0.2–15s; the working CLI probes0.1–2s with an independent5s deadline. Loss of all
three processes, both helpers without a responsive controller, a host/OS scheduling failure,
another privileged actor or concurrent unreviewed signals is outside the guarantee. This is
not a kernel-enforced fleet fence. Do not use another
lock root to bypass a held lock, combine this with Compose lifecycle commands, or extend the
probe into a service stop without the separate settlement protocol.

## Verification

Final targeted command:

```sh
python -m pytest -q tests/test_control_ha_dispatcher_hold.py \
  tests/test_control_ha_owner_replacement.py tests/test_control_ha_owner_upgrade.py
```

**159 tests PASS /0 skips**,8.61s,47 new. New tests use real child processes for in-flight
completion, preserved dispatch inhibition, explicit abort, controller SIGKILL, guardian SIGKILL,
rescue SIGKILL, frozen guardian, deadline release and both-helper death with surviving controller.
They cover PID/start/UID/command/cgroup/namespace mismatches, pre-existing stopped target
preservation, concurrent refusal, unsafe/symlink/hardlink lock paths, fork/pidfd allocation
failures, dead processes and fixed production role/image/command/health selection. The first
run found only a fixture teardown attempting to signal an already exited process; it was fixed.

`tests/fixtures/owner_upgrade/dispatcher.py` runs a fresh owned Docker container using the
original publisher image and exact shell command. Only its manage.py is replaced by a synthetic
SQLite workload. UID1000, init, read-only root, no capabilities, no-new-privileges, resource
limits, network none and private fixture binds are used; no product token/database is loaded.
At **07:48:48.046141–07:49:02.492794UTC**, four cases pass: normal hold/release, guardian death,
rescue death and guardian stall. A child commits during hold; no second cycle starts until
release, then a second commit occurs. Container identity/runtime/config remain unchanged.
Owned test container removed, scoped label inventory empty; synthetic data retained privately.
Test cleanup may forcibly remove only its label-checked synthetic container, never production.

## Working result and rollback

At **07:49:02.726787–07:49:03.731041UTC**, the working publisher scheduler is held for one
second and resumes. Both helpers exit0 and are reaped. Full effective configuration readback
matches; original container ID, PID/start identity and restart count are unchanged. Console
is not signalled. At07:49:03.811538 both original OWNER roles are healthy, restart counts0,
and both installed collector timers remain active. An earlier one-second working probe also
succeeded; the final receipt binds the final source including surviving-controller fallback.

Working invocation (requires a new existing empty0700 private journal):

```sh
python -m scripts.control_ha_dispatcher_hold --journal /absolute/private/journal --hold-seconds 1
```

The CLI records private prestate before signalling and a receipt only after confirmed resume
and runtime/config readback. Failure means refusal/unconfirmed outcome, not a successful drain;
retain the journal. Normal rollback is controller pipe closure followed by helper completion
and confirmed resume. There is no installed artifact to uninstall or old DB to restore.
For simultaneous loss of controller and both helpers, do not blindly kill/restart the service:
independently verify the retained scheduler start/UID/command/namespace identity, exclude another
active hold and use a freshly verified pidfd to resume only that scheduler. If identity changed,
stop and reconcile instead of signalling a reused PID. Keep current data and unknown markers.

No container stop/start, working image build/install, gate mount, service/unit change, remote
SSH operation, database rewrite, client version, installer, catalog or release is performed.
This does not settle old publication/support/manual operations or close console ingress.

## Evidence and remaining work

Raw configs, process bindings, synthetic SQLite files, prior runs and final receipts are retained
in the owner-only local control-ha evidence directory, located by `/tmp/fc-ha-dispatcher-current`.
The `final/` subdirectory is authoritative. Directories0700/files0600, not Git or CI.

| Final artifact | SHA256 |
| --- | --- |
| Source | `fa03cb5d1df57e45abbc3f5f6f847f04919c17e3be997f07060830dd2cf1aa80` |
| Tests | `766a30eca0964d78fc6cff6cab98b029961d74858291be07e82ad9e83880e95d` |
| Native fixture | `111d9cdbd0845afe680cefae261ecca9f535cfd620c1b2e1bf782dbe08ed7355` |
| JUnit XML | `eb1743d53943820dc5b10c67a4e3c212d13b02686375cc71ab50f255f9e0c6f7` |
| Native receipt | `21b04953f1c26353ebb9c76b3f288bbbe4a2006fe9fc0cdd421a1e991ab755d7` |
| Working prestate | `b31fdfdb51c40a8eee3b6782d860fceab6e01a9aacb53eabe7434df69b5fcf90` |
| Working receipt | `1b377b2230282a82356ef680b7dd056397aea0845c7ccd56b3f81bd2ca4e7d41` |
| Final health | `9dfa98275caecdb9c6398e552f6209770e1db824ce233fb0d55edb2d95f4d728` |

Next is console ingress closure and independently confirmed publication/support/manual
completion, then gate/runtime attestation and guarded candidate startup/abort integration.
The panel is currently loopback-published on8765 with two Gunicorn workers; the publisher
dispatcher hold does not block that ingress. Do not infer it is drained from current health
or an empty DB sample. Keep the already qualified stopped-replacement executor and rollback.

The fixed remaining acceptance sequence is real participant/settlement coverage on OWNER and
RU/NL, coherent all-store capture, independently approved checkpoint/key/access custody, then
one combined current-state recovery with post-ACK/stale-copy checks. Replication PASS in
isolation; the same other three HA-02 gates remain partial. No new stage, percentage, ETA,
HA-03 cutover or automatic RU-independent failover is asserted.
