# CONTROL-HA · systemd lifecycle veto · 24 November 2026

Selected task: **CONTROL-HA-20261123 / HA-02**. Source-only change plus strictly read-only NL
observations. No RU access, production service dispatch/start/stop/reload, unit/key/environment
change, product database access, deployment, signing, release tag or public artifact update.
Client/build/installed/public-installer/catalog/invitation versions remain unchanged. The native
test creates only random, test-owned **local user-systemd** services; none on the gateways.

## Change and boundaries

`control/capture_systemd.py` adds a conservative lifecycle veto. Schema3 guardian bindings carry
an optional `systemd` object containing `scope` and an exact `units` name-to-snapshot-SHA256 map.
System scope permits only Family Connect AWG, TCP and paid-watch services and requires a root
guardian; user scope permits only the disposable `fc-ha-lifecycle-<16 hex>.service` test namespace.
The existing sealed-source/private-binding/native-runtime/namespace checks still apply. Duplicate
unit bindings and unknown fields are rejected. Schemas1/2 remain supported without implicit
activation. The closed guardian package includes the new module; old packages/pins are not repinned.

Before DRAINED and again immediately before HELD, the opted-in guardian requires:

- The exact approved active/running unit and invocation, no queued job, no ControlPID, successful
  service/reload result and no NeedDaemonReload. Restart/state/start epochs are included.
- MainPID inside the named cgroup, recursive child-group membership, non-zombie process start
  identities, executable device/inode and command-line hashes. No raw command lines are emitted.
- Stable selected unit properties around the process-tree read; the complete snapshot must match
  the explicitly supplied digest, including boot identity. It is never automatically re-approved.
- Read-only bus queries with a fixed executable, sanitized environment, bounded output and a
  shared0.75s verification budget. Existing guardian drain/hold/alarm limits are unchanged.

Any refusal prevents the interval receipt. Gates release through the existing failure/timeout
path; no pending marker is cleared, no service job is canceled, retried or waited into apparent
success. Normal emergency `systemctl --no-block stop` and paid-watch are **unchanged**. The prior
[owned-engine cleanup fix](2026-11-24-control-ha-awg-cleanup.md) is retained, not reimplemented.

**This is a veto, not a systemd lock or an all-writer fence.** Matching endpoints cannot rule out
all transient activity between observations. Stable process identity does not prove a worker is
idle, a kernel network operation completed or the installed code participates in admission.
Uncooperative/manual writers and external dispatch still need explicit coverage. A successful
local interval receipt continues to say `capture_permitted=false`; an installed baseline is not
independent approval. The guard deliberately requires running services, not stopping VPN to make
capture quiet. Pending jobs already known from ambiguous native operations remain a separate
durable uncertainty condition, even after systemd itself becomes stable.

## Native verification

Python3.14.4, local systemd259.5;27 distinct installed packages checked against control, identity,
provisioning and messenger lockfiles. **223 focused tests PASS/0 skips /27.35s**,43 new cases:

```sh
FC_HA_SYSTEMD_NATIVE=1 /tmp/fc-control-ha-20261123/venv/bin/python -m pytest -q \
  tests/test_capture_systemd.py tests/test_capture_launch.py tests/test_capture_group.py \
  tests/test_capture_gate.py tests/test_capture_renewal_state.py
```

Three native cases use real user-systemd, cgroups and sealed packaged guardians, not substituted
bus output. Each service has an owned Python parent and a SIGTERM-ignoring Python child, plus a
one-second ExecStopPost. KillMode=control-group and a two-second test-only stop timeout are set
only on these random disposable services, not on any Family Connect production unit.

1. An unchanged running service passes the local interval check; it remains running during capture.
2. A zero exit from `systemctl --no-block stop` leaves the child alive. The lifecycle check refuses;
   the packaged guardian cannot send a successful final ACK and the coordinator gets no receipt.
3. During actual `stop-post`, MainPID is already0 but ControlPID and the systemd job remain nonzero.
   Completion is still refused. Main-process exit alone is not teardown completion.

Fixture finalizers stop only their exact random unit, reset its failed status and verify owned
children are gone. Final matching user-unit listing is empty. Other tests cover job/type/epoch/
reload failures, changed cgroups, zombie/PID reuse/executable replacement, unsafe bindings and
schema3 source closure/aliases. Existing gate, guardian launch and renewal settlement tests pass.
An initial invocation named nonexistent `test_capture_renewal_settlement.py`: pytest ran no tests;
the corrected selection above uses the existing `test_capture_renewal_state.py`. Earlier narrower
selection passed144 cases. Neither result is called a full-suite or whole-recovery qualification.
Prior unrelated legacy packaging/announcement-pin failures and GUI limits are not cleared or
hidden by this focused selection; no old acceptance hashes are weakened.
Documentation check:4 files/1069 link targets/zero errors; staged whitespace check PASS.
This validates local links/content, not external artifact availability. Private closed guardian
capsule SHA256: `12e83c6596c9416cd6fcfff8e01b584c48078641d7653d678b309ca4da410d21`;
it is a source qualification artifact, not a deployed or public client release.

## Installed observations — no activation

Strict existing SSH pins; source sent on stdin, no remote installation. NL1 observation:
22:06:44.576–22:06:45.031UTC. NL2:22:06:45.783–22:06:45.911UTC. Scoped result:

| Host | AWG / TCP / paid-watch | Job / ControlPID | NeedDaemonReload | Lifecycle result |
| --- | --- | --- | --- | --- |
| NL1 | All active/running, Result=success | None /0 for all | no for all | Two matching snapshots per unit |
| NL2 | All active/running, Result=success | None /0 for all | yes for all | All three refused |

Both hosts expose KillMode=control-group and TimeoutStopUSec=5s for these units. This does not
prove installed teardown within five seconds; no installed stop/restart experiment was attempted.
No data-plane, whole-fleet health, no-RU-dependency or present-time availability claim follows
from these bounded observations. NL2's earlier restricted-bootstrap reload warning is not
silently resolved: the same flag is now observed for these three transport units. Its underlying
loaded/disk discrepancy remains to be diagnosed; it is not evidence of the earlier RU failures.
Do not use daemon-reload to suppress the flag without qualifying and authorizing the actual change.

Installed gateway SHA256 is identical on NL1/NL2:
`69f32dbfdf0db5f57fb598d58935b5f2b098e53d0c0e2ac24517ad299ced26bf`.
Candidate gateway remains
`be41604367998baf159f50c799cda35b7a00e3b76ab85c1737b32a17f8ce8402`.
The previous cleanup/source changes are therefore **not** asserted to be installed. This turn
does not patch/repackage that gateway or change the five-second production stop budget.

Private evidence pointer: `/tmp/fc-ha-systemd-lifecycle-current`; probe source SHA256:
`b086de2b47a1157e2bb58ad91605e669857136816289be5a0ddad13c951d0e00`.
Raw receipts, process-bound snapshots, test output and source capsule stay outside Git. No client
keys, profiles, product records, environment values or binary output are staged.

## Remaining work and rollback

The [original four gates](2026-11-24-control-ha-support-admission.md#fixed-ha-02-completion-map)
remain fixed: replication PASS in isolation; current-input/trust, coherent all-writer capture and
independent custody/final recovery remain partial. No new stage, percentage or calendar promise.

Next selected work: read-only diagnosis of NL2's loaded/disk discrepancy, actual writer/lifecycle
and collector/manual admission bindings, and an explicit activation/capture proposal identifying
exact candidate and rollback bytes, source/runtime identities, participating writers, watchdog
budget and abort conditions. Working-NL activation is not implied by this commit. Only after
that scope is approved and qualified can the joint interval/current inputs be independently
approved and used for combined recovery. Do not repeat the completed queued-stop, stop-post,
owned-child cleanup or cold-runtime checks as new gates. Do not stop/disable paid-watch for capture.

Rollback now: no production change to undo. Omit schema3 lifecycle configuration or revert the
source/test change before a future approved build; old installed packages are untouched. For a
future activated candidate, abort the capture first, preserve all pending/private evidence and
restore the approved prior package/binding without changing product state or emergency SSH.
Never drop a configured veto or regenerate its approved digest just to turn a refused capture green.

Source/tests/docs are committed together and pushed non-force on the agreed feature branch;
main receives navigation only after the exact remote feature SHA is verified.
