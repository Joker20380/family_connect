# CONTROL-HA — AWG owned-engine teardown, 24 November 2026

## Scope and reproduced fault

Selected CONTROL-HA-20261123 / HA-02 continuation after
[service-environment qualification](2026-11-24-control-ha-service-environment.md).
`deploy/friends/awg-gateway.py:run` previously performed teardown as a straight-line `finally`:
an exception while removing a firewall rule/chain skipped all later actions, including stopping
the owned engine and deleting its interface. The ten-second terminate/wait could also time out
without attempting kill/reap or interface deletion. Signal-handler setup occurred outside the
cleanup scope after the child had already started.

Three fault-injection cases fail on based76df5cf: rule removal, chain flush and chain deletion
each leave the simulated engine unstopped. They pass after the patch. This proves a source
defect, not that a specific installed host has encountered it or that it caused earlier RU outages.

No RU/NL connection, working-service/unit/policy/environment/key change, deployment or cutover.
Client/build/installed/public-installer/catalog/invitation versions and immutable artifacts remain
unchanged; no signing, release tag or public build. Isolated test databases/processes only.

## Change

- `cleanup` registers every teardown action with `ExitStack`. It preserves reverse firewall-rule
  order, then flush/delete-chain, owned engine stop/reap and interface deletion. An exception
  does not skip later callbacks; errors propagate rather than becoming success.
- `stop_engine` retains the existing ten-second graceful wait. If signal/wait fails, it attempts
  kill when the owned child is still alive and always attempts a bounded two-second reap. The
  original error remains a failure even if fallback succeeds; an unsuccessful reap also raises.
  Already exited children are reaped without sending a signal.
- Signal-handler installation is inside the `try/finally` owning that child. A setup failure
  therefore still attempts teardown. No unrelated process group is signalled.
- No gate is implicitly enabled. When the tested caller explicitly holds a capture operation,
  pending remains until normal cleanup finishes; an escaping timeout retains uncertainty even
  after a later successful operation. This is not a claim that installed AWG lifecycle calls
  currently participate in such admission.
- `Gateway.stop_all` still submits `systemctl --no-block stop`. Paid-watch, subscription expiry,
  operation deadlines, systemd stop/watchdog settings and service policy are unchanged. The
  regression test explicitly preserves asynchronous emergency dispatch, not a completion ACK.

Gateway SHA256 before:
`9023d2c3f7c3a5127d67c509a16eb2d974810ff54d5b76cc225cd9b93e0b4234`.
Candidate source SHA256 after:
`be41604367998baf159f50c799cda35b7a00e3b76ab85c1737b32a17f8ce8402`.
These are source identities, not installed-package or release assertions.

## Verification

Python3.14.4;27 distinct installed package versions match the control, identity, provisioning
and messenger lockfiles. New test file has17 cases. The focused selection reports
**169 PASS/1 skip /18.40s**:

```sh
/tmp/fc-control-ha-20261123/venv/bin/python -m pytest -q \
  tests/test_awg_gateway_cleanup.py tests/test_friends_gateway.py \
  tests/test_transport_application_regressions.py tests/test_transport_enforcement.py \
  tests/test_control_ha_file_boundaries.py tests/test_capture_gate.py \
  tests/test_capture_receivers.py tests/test_control_ha_joint_nodes.py \
  tests/test_control_ha_node_custody.py
```

The single skip is `test_postgres_native_parity_revocation_and_restart`, which requires a
dedicated PostgreSQL fixture. It is rerun alone through the existing owned `Rehearsal.contracts`
with `CONTRACT_FILES` set to that exact test: **1 PASS/0 skips** on pinned PostgreSQL17.11,
21:52:33.768–21:52:40.490UTC, owned-container cleanup verified. Thus all170 distinct selected
cases have passed across the two environments; no generic full-suite PASS is claimed. No crash
or whole-recovery rehearsal is implied by this targeted parity test. Private receipt/logs and
test-only DB credentials remain outside Git via `/tmp/fc-ha-awg-cleanup-current`.

Three new native cases launch owned local Python children, not the real AWG binary: ordinary
SIGTERM/reap, ignored SIGTERM with kill/reap and pending retained through retry, and combined
network-cleanup error plus ignored SIGTERM while later cleanup still runs. Network commands
are substituted throughout; no iptables/interface/systemctl call executes. Other cases cover
each of the three reverse rule deletions, both chain operations, signal setup, signal failure,
grace timeout, kill/reap failure, already-exited children and unchanged emergency dispatch.

Additional legacy packaging selection: **2 PASS/4 FAIL /0.42s**. The failures are visible, not
fixed by weakening historical input validation:

- `test_closed_overlay_modules_and_tamper`: `UNRELATED_PAID_DELTA`.
- Diagnostic overlay, PR15 lifecycle and V2 forward-package tests: `POLICY_CHANGE_FORBIDDEN`.

All four fail before reading the modified gateway. Nine relevant test/builder/policy/paid/API
files are byte-identical to based76df5cf. No historical accepted input SHA is changed. The old
diagnostic/lifecycle builders also intentionally forbid a changed gateway; this source delta
must not be smuggled through those old module-only release paths. Any future package needs its
own exact candidate/rollback validation. Existing unrelated announcement-pin and GUI/device
limits are likewise not cleared by this focused run.
Changed documentation:4 files/1068 link targets/zero errors; whitespace check PASS. External
release artifacts are not part of this check and no publication is inferred.

## Remaining acceptance and rollback

Owned-child exit is not full cgroup or network settlement. Existing best-effort nonzero network
command handling is unchanged, and no kernel/rule readback is added. The callbacks can require
multiple existing command timeouts; this is not a new total teardown deadline. A real systemd
stop budget can expire before Python's graceful/fallback waits finish, including the existing
five-second dependency setting. Installed unit/cgroup/job behavior therefore still needs exact
qualification; do not extend that budget or stop paid-watch merely to obtain a quiet capture.

Remaining selected work is actual AWG/systemd queued-stop completion, lifecycle admission and
runtime bindings, collector/manual coverage, concrete approved joint activation/capture proposal,
real coherent interval and independently approved current inputs/custody/final recovery. The
[four original gates](2026-11-24-control-ha-support-admission.md#fixed-ha-02-completion-map) are
unchanged: replication PASS in isolation; the same three gates partial. This source fix does not
authorize working-NL deployment or advance to HA-03. Do not repeat the completed teardown slice
as a new gate or assign a completion date from its test count.

No production rollback is needed: nothing is deployed. Revert this source/test delta before
building a future candidate if required; keep the preceding approved runtime package unchanged.
On a later approved activation failure, abort capture first, preserve admission uncertainty and
committed state, then use that activation's approved package/configuration rollback. Never clear
pending markers or kill unrelated processes to force a successful capture. All test-owned
children are reaped and the disposable PostgreSQL container is removed.
