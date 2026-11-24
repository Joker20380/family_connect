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
silently resolved: the same flag is observed for these three transport units. At22:06 its cause
was still unqualified. The later diagnosis below identifies the manager-wide condition, not an
established per-unit content mismatch. It is not evidence of the earlier RU failures.
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

## NL2 manager-wide reload cause — read-only

Continuation of the same HA-02 task, not a new gate. `scripts/control_ha_reload_diagnosis.py`
provides a conservative read-only witness for the **reviewed** systemd255.4-1ubuntu8.18 version.
Other versions or unsupported observations refuse diagnosis rather than inherit this conclusion.
No deployment, host changes, package install, unit start/stop/reload, product database access,
key/environment changes, client/catalog/invitation version change or RU/NL1 access occurs here.

Final native NL2 observation: **22:23:59.926–22:23:59.980UTC**, strict existing SSH host pin,
source on stdin, no remote file installation. Twice, the built-in `-.slice` is loaded, has only
its own name, empty FragmentPath/SourcePath/DropInPaths, and NeedDaemonReload=true. Across the12
manager lookup directories, all36 `-.slice`, `-.slice.d` and `slice.d` candidates are absent,
including dangling symlinks. The observer and PID1 have identical mount namespaces and filesystem
roots. Namespace/root and observations must remain equal; access failure is not treated as absence.

The reviewed source's `unit_need_daemon_reload()` first checks the manager-wide
`unit_file_state_outdated` flag. For this fileless, aliasless sentinel, all other supported paths
to true have been excluded at the observation points. This supplies a **manager-wide outdated
witness**, not evidence that each Family Connect unit file changed. The earlier wording
"NL2 loaded/disk mismatch" was an unproven interpretation and is corrected by this finding.
It remains possible for a particular unit also to have changed; full loaded/disk equivalence
was not established here. Stable endpoints are not a continuous filesystem/admission fence.

The package's Ubuntu patch sets the global flag when unit-file installation changes actually
succeed, including enable/disable/preset/revert/dependency/default-target operations. It need
not mean modified service command lines. A manager reload clears/rebuilds this state. This
observation does **not** establish which prior operation, actor, unit or timestamp set it. That
unattributed history is not a new acceptance gate or a reason for endless additional census.
The flag itself neither stops the services nor diagnoses RU's earlier outages or a hosting fault.

AWG, TCP, paid-watch and restricted-bootstrap are active/running immediately around the final
observation, with no current job, ControlPID=0 and unchanged MainPID/invocation identities. This
is not a VPN/data-plane test or a whole-fleet/current-time availability guarantee. All four still
report NeedDaemonReload=yes. The existing capture lifecycle veto is **unchanged** and still refuses
them; the new classifier never grants capture, changes a baseline or suppresses the warning.

### Source review and validation

The official [Ubuntu source descriptor](https://security.ubuntu.com/ubuntu/pool/main/s/systemd/systemd_255.4-1ubuntu8.18.dsc)
was fetched over HTTPS. Both downloaded archive SHA256 values match its Checksums-Sha256 entries:

- Original255.4 archive: `96e75bd08c57ad401677456fb88ef54a9f05bb1695693013bc6ecce839640fd5`.
- Ubuntu8.18 patch archive: `ec3ce620c3e072d34bbeaf9a4155cd91b5bee94eb412071bf81182f230ae2657`.

Seven relevant patches from the85-entry series were applied locally, in series order, to six
selected source files. The resulting reload function SHA256 is
`474ba13deeb7c41a24b2a823de58aa4e805b5b47641f55d27e2d27d45e757e56`; its manager-wide first branch
remains intact. The relevant Ubuntu patch is
`lp2055239-core-dbus-manager-mark-unit-file-state-as-outdated-only-i.patch`. Drop-in lookup also
confirms that the leading-dash sentinel has no additional truncated-name prefix directories.
No upstream code is executed or copied into the repository. This is a version-specific source
explanation, not an independently authenticated binary build/provenance attestation; no DSC GPG
verification or reproducible binary build is claimed.

Observed manager executable SHA256:
`9a813714ffd4dadb692afe44384c9c5b334fa323a4ec1dd5157aebdcbbb0667a`.
Final observer source SHA256:
`0a5c87cc7013c8de75f69efd217a06de320ce420127f2c6faa1e0df846a8b2b5`.
Private evidence pointer: `/tmp/fc-ha-systemd-reload-current`. Scoped unit dumps, source archives,
patched review files, intermediate failures and final receipts stay outside Git. Discovery used
only the four exact Family Connect units, not a whole-manager dump containing neighbouring services.
The final witness reads only manager metadata and the built-in sentinel, never another application.

**44 focused tests PASS/0 skips /0.20s**, Python3.14.4, existing pinned control test environment:

```sh
/tmp/fc-control-ha-20261123/venv/bin/python -m pytest -q tests/test_control_ha_reload_diagnosis.py
```

Tests cover true/false flags without a capture grant, nonempty/aliased sentinels, unsupported
versions, invalid/duplicate lookup paths, files/directories/dangling symlinks, permission and
query failures, changed observations, mismatched manager mount/root views and sanitized failures.
Documentation:4 files/1070 link targets/zero errors; whitespace PASS. External-link inventory
is not a general availability check; only the source archives described here were fetched.
The new script has no mutation command. This is not another full guardian or recovery rehearsal.
Initial discovery refused a nonexistent Manager.Reloading property and then an unescaped leading
dash passed to busctl. Both were read-only failures; the final bounded observer uses fixed typed
properties and the exact sentinel D-Bus object. No production remediation was attempted.

### NL2 reload disposition — not ready for execution

The next capture proposal must explicitly separate diagnosis from the host-wide action:

1. Finish the actual writer/lifecycle/collector/manual admission bindings and approve the exact
   candidate/source/runtime/gate configuration. This witness does not replace any of that work.
2. Do **not** execute `systemctl daemon-reload` as a diagnostic or a per-service operation. It
   rereads manager configuration, may run generators and rebuilds dependencies for the host, not
   only Family Connect. It does not itself request a service restart, but its wider scope still
   needs separate host-level authorization/coordination; neighbouring MicroTrader services must
   not be operated. Current NL authorization excludes working-service changes.
3. A future authorized proposal must retain the approved pre-change unit/drop-in/config bytes,
   live identities/jobs and recovery access before any reload. Unknown pending on-disk changes
   and generators must not be blindly adopted. This checkpoint has not qualified that global scope.
4. After such an approved operation, require fresh loaded/source/gate checks, stable service
   identities/no jobs and clearance of the warning before a new independently approved capture
   binding. A persisting flag, changed process or failed read aborts capture; no repeated reloads,
   automatic restart, weakened veto, journal deletion or regenerated approval to force success.
5. A manager reload has no universal inverse. Restoring previously approved files and reloading
   again would itself need the approved rollback scope; do not promise "undo reload" from this
   observation. There is currently nothing to roll back on production. Reverting/removing this
   diagnostic source does not alter the existing lifecycle gate or installed services.

## Remaining work and rollback

The [original four gates](2026-11-24-control-ha-support-admission.md#fixed-ha-02-completion-map)
remain fixed: replication PASS in isolation; current-input/trust, coherent all-writer capture and
independent custody/final recovery remain partial. No new stage, percentage or calendar promise.

NL2 manager-wide reload-cause diagnosis is complete; it is not a pending per-unit drift claim.
Next selected work: actual writer/lifecycle and collector/manual admission bindings, and an
explicit activation/capture proposal (including the host-wide flag's disposition) identifying
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
