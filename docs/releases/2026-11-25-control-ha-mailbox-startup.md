# Mailbox fail-closed startup and restart — 25 November 2026

Selected: CONTROL-HA-20261123 / HA-02, the existing support external-work settlement boundary.
This qualifies a restart prerequisite for the [link-generation fence](2026-11-25-control-ha-mailbox-links.md),
**not a working installation, independently verified OWNER exit, cross-host commit or HA-02 completion**.
Operational permission is already present; no additional owner input/password is needed for this work.

## Mechanism

`scripts/control_ha_mailbox_startup.py` requires an operator-owned manifest before starting the native
server. Missing/malformed/duplicate-field/symlink/hardlink/unsafe-owner/writable-control inputs refuse;
there is no unfenced fallback. Production entry uses UID0 ownership; the explicit nonroot owner option
is exercised only through the Python API in disposable local fixtures. Parent directories are checked,
reads are bounded and stable, and manifest byte drift is refused at control boundaries.

The manifest names the support public identity, generation, expected OWNER-binding digest and expected
replacement-plan digest. A startup ticket adds the exact PID/start/boot/command/cgroup binding, manifest
digest and a fresh random challenge. Tickets are not recovered from old receipt files after restart.
The explicitly named `LOCAL_QUALIFICATION_ONLY` operation accepts only a safe operator-owned file with
the exact canonical ticket. Reused process IDs, changed generations/plans/manifests and prior process
opening files do not grant admission. Canonical comparison distinguishes JSON booleans from integers.
**Expected OWNER/plan hashes are not an independent attestation that OWNER exited.**

Installing a fence after `ClosedRelay.__init__` would leave an admission window because RNS publishes
the destination during its constructor. The startup factory instead defers that exact incoming native
registration, constructs the real relay/request handlers, installs `PersistentLinkFence`, verifies closed
admission and only then invokes the original native registration. Relay, spool, RNS Destination/Link and
Transport registration code/source are pinned. Other destination registrations are not substituted.
Failed guard installation or source validation leaves the new destination unpublished. The production
wrapper delegates to the pinned existing `messenger.server.main`; it does not copy or rewrite that server.

Every new process starts closed even if an old opening file is still present. A service-UID process cannot
rewrite root-owned control files. A fresh local qualification ticket admits only post-opening native links;
the prior old-link/direct-spool protections remain. A startup fence cannot be removed with `abort`, even
before opening, because that would violate the required-manifest startup contract. No timer opens it.
The operator manifest is not a hot-reload/revocation interface: drift is rejected by control operations;
changing its bytes does not itself revoke already admitted work. A new qualified hold/recovery transition
is required, rather than mutating files and assuming all writers stopped.

Observations explicitly retain `owner_exit_verified=false`, `installed_unit_verified=false`,
`activation_ready=false`, `capture_permitted=false`, and the underlying cross-host/restart permit flags
remain false. `restart_defaults_closed=true` describes this startup path, not installation into the
working unit. The root verifier separately qualifies the **isolated** systemd unit. The actual mounted-
volume server CLI/preflight and production unit adoption are not newly accepted by this fixture.

## Qualification

Final **104 tests PASS/0 skips**:25 startup/control contracts,1 native authenticated crash/restart scenario,
and the preceding78 link/fence/outcome/native relay/server/membership checks. No test failure occurred
in this continuation. Earlier23-contract,1-restart and102-combined runs are retained, not added to104.

```sh
/tmp/fc-control-ha-20261123/venv/bin/python -m pytest -q \
  messenger/tests/test_control_ha_mailbox_startup.py messenger/tests/test_control_ha_mailbox_restart.py \
  messenger/tests/test_control_ha_mailbox_links.py messenger/tests/test_control_ha_mailbox_links_wire.py \
  messenger/tests/test_control_ha_mailbox_fence.py tests/test_control_ha_support_outcomes.py \
  messenger/tests/test_relay.py messenger/tests/test_server.py messenger/tests/test_membership.py
```

The native fixture uses real RNS TCP loopback interfaces, identity proofs and encrypted requests with
synthetic identities. It starts closed, opens only with the exact local ticket, commits a support row,
is killed, and starts a fresh process against the same synthetic store. The old ticket is rejected;
support remains closed while an unrelated identity commits. A fresh local ticket allows another support
commit. Fresh native/read-only SQLite reopening verifies all three rows. No production state is copied.

Actual NL1 run: **20:08:21.019038–20:08:53.426832UTC**, installed Python3.14.4/RNS1.5.1/LXMF1.1.1 and
native installed relay/codec, **fc-mailbox UID996/GID982**, with root-owned manifest/request files.
`fc-ha-mailbox-startup-lab-20261125.service` uses Restart=on-failure/1s. Before deliberately killing its
main process, the root verifier checks exact lab unit/PID/start/UID/command/cgroup and uses a pidfd for
SIGKILL. **Only this synthetic lab process is killed.** Systemd automatically restarts it once; a new
ticket and closed admission are independently observed. The service UID cannot write the manifest.

Independent effective readback verifies PrivateNetwork/PrivateTmp, ProtectHome, ProtectSystem=strict,
NoNewPrivileges, UMask0077, only the isolated runtime writable,512MiB,96 tasks,400ms/s CPU quota,
SendSIGKILL=no and infinite stop timeout. Native clients inherit the lab's private network namespace.
After the second process exits normally: ExecMainCode1/ExecMainStatus0, MainPID/ControlPID0, NRestarts1,
empty ControlGroup and absent exact lab cgroup. Only this exited unit is stopped; final unit state is
not-found/inactive/PID0. A separate read-only SQLite query returns3 retained rows.

Working NL1 remains PID3705/NRestarts0/NeedDaemonReload=no, with17 effective fields, original unit hashes,
four native source hashes, three RNS source hashes and process start/command/cgroup binding unchanged
before/after. OWNER is read-only observed active/running PID2022541/NRestarts0/no pending reload at
20:10UTC; no new full19-source OWNER audit is claimed. No working service is injected, stopped or restarted.

## Evidence and rollback

Private/synthetic artifacts remain outside Git under `/tmp/fc-ha-mailbox-startup-20261125` locally and
`/run/fc-ha-mailbox-startup-20261125` on NL1. Only seven public source/fixture files were transferred.
No production DB, node/client private key, profile, backup or signing secret was read or committed.

| Item | SHA-256 |
| --- | --- |
| Startup module | `23109a63064cf3aacf1419b56cf176b5d4a771da2a1f23112bc1af139e39b553` |
| Native restart fixture | `d78a28ab963041c0477bbac8eeef5116efe988ec974af9b2c985d5f8bba60070` |
| Seven-source archive | `d987de3907690ded2ebe8fa715e0b0c25738cd7642a272d5bc639add60fb4388` |
| Independent actual NL1 result | `269c580471cda9cc614323d41fd2d73b824a3adbef6dd1a90f1d332243ed7aa5` |
| Preliminary23-contract JUnit | `ca146cc0cc95af630a06403b240f73af8e37d9138573c26f0398815ca62171c2` |
| Native local restart JUnit | `03dc2ce9e6094db168e9ba056ed4f0dc9f4b6a02b07dabf1e81210ce5c139305` |
| Intermediate102-check JUnit | `1d1e11ffe59dab4910905400e34f470dbbb2140f31c82da9690f64dc42ea453b` |
| Final104-check JUnit | `3cb5bf336ae09298dfd58a2b2a2820089810df87fac909094628ae1c1f8ffe93` |

Final104-check receipt: `/tmp/fc-ha-mailbox-startup-regression-20261125.xml`,57.94s.
Source AST/whitespace and added documentation links are checked before push.

Candidate `9d7bf840f3455d0ef2e7653dc9289aac2f0d77c9f2a0a8e305c786f7ddb80489` is unchanged and **NOT installed**.
No working unit/configuration/policy/product-data change, RU/NL2/container/MicroTrader operation,
public version/tag/catalog change or production rollback occurs. Do not remove a startup guard or replay
an old opening file as rollback; recover through an independently qualified paired control transition.

Next within the same settlement gate: paired NL1 startup-unit/manifest installation and existing-process
hold adoption, independent OWNER quiescence/exit/replacement-commit proof bound to the exact live mailbox
ticket, and combined deployment/controller crash recovery. Only then authorized activation/readback.
The seven historical unknowns remain untouched. Remaining manual/OWNER writers, coherent fleet capture,
current independent trust/custody/approval and full recovery keep three HA-02 gates partial; isolated
replication PASS. No new numbered gate, HA-03 or automatic next task is started.
