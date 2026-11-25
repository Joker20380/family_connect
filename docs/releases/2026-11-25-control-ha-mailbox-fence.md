# Support-scoped mailbox hold/drain — 25 November 2026

Selected task: CONTROL-HA-20261123 / HA-02, the existing old-support external-work settlement
boundary. Owner authorization covers bounded OWNER/RU/NL operational work; missing permission is
not the blocker. This checkpoint qualifies a process-local primitive in isolation, **not a working
installation, cross-host handoff, settled historical delivery, coherent capture or HA-02 completion**.

## Mechanism and scope

`scripts/control_ha_mailbox_fence.py` pins the installed native relay source to
`2108e024353158b271ccce9289c3755a4b64f5f9d130d1e55ec79dac6bdff4ac`, checks loaded class methods,
the exact request-handler registry, concrete relay/spool objects and the CPython3.14 GIL/process
binding. It patches the existing function objects' code, rather than replacing a class attribute
while previously registered/captured bound methods still point to the old function.

The selected support identity's relay callbacks, its direct spool PUTs and its recipient GET/purge
calls are refused while HELD. Other identities and other spool instances continue through the
original methods. Already entered old native frames are counted for that exact relay/spool/scope;
SQLite transactions are neither canceled nor rolled back. A drain deadline returns a still-held,
not-drained observation if old work remains. Controller exit/SIGKILL is not a release trigger.

Explicit abort requires the matching generation of the same one-use instance, restores the original code and retains
the dispatcher until any already entered wrapper has returned. This avoids a stale wrapper losing
its global dispatch reference during restoration. Source/object/registry/generation drift refuses
qualification; no replacement supervisor, service unit, paid-watch or deny policy is changed.

**Limits are executable:** every observation reports `cross_host_bound=false`,
`restart_protected=false`, `external_settlement_proven=false`, `activation_ready=false` and
`capture_permitted=false`. The caller-supplied generation is not independent OWNER evidence.
There is no successful commit/open transition or durable mailbox-restart protection here.
An explicit abort restores the old service semantics: a queued old callback can then write again.
Retention, other recipients' purge activity and other writers are outside this scoped hold; it
does not freeze a complete mailbox/database snapshot. The seven earlier unknown outcomes remain.

## Qualification

Final **64 tests PASS/0 skips in1.51s**:26 new mailbox-fence contracts,22 outcome-observer tests,
4 native relay tests,4 server checks and8 membership checks. Run with the existing locked control/
identity environment, CPython3.14.4, RNS1.5.1 and LXMF1.1.1:

```sh
/tmp/fc-control-ha-20261123/venv/bin/python -m pytest -q \
  messenger/tests/test_control_ha_mailbox_fence.py tests/test_control_ha_support_outcomes.py \
  messenger/tests/test_relay.py messenger/tests/test_server.py messenger/tests/test_membership.py
```

Checks cover saved bound callbacks and spool methods, delayed TCP work after sender disconnect,
native RNS `Link.handle_request` after it has captured the response generator, and a link becoming
CLOSED before that already admitted callback runs. New work is refused while HELD; already entered
PUT/purge transactions finish and only then drain. Timeout, stale generation, source/loaded-code/
registry drift, unrelated identities, exact restoration and a paused wrapper during abort are tested.
The RNS dispatch case uses a synthetic link identity and intercepts response packet send: it tests
the native dispatch implementation, **not an authenticated RNS wire exchange or whole-transport drain**.

A separate native mailbox process survives a controller subprocess's SIGKILL while still refusing
support and accepting a different sender. An independent matching abort restores support delivery;
freshly reopened native SQLite retains both synthetic rows. No production state is copied into tests.

Retained failures are not counted as passes: the first expanded run had25 passes/one fixture error
(synthetic Link lacked negotiated `mdu`); it was corrected and the targeted test passed. A combined
run then had63 passes/one setup error because importing the session RNS fixture from outside its
directory created two singleton fixtures. The new tests now live under `messenger/tests`, using
its existing canonical fixture. Final64 includes all of these cases; no skip/filter hides them.
The preliminary21-pass run is retained and not added to64.

## Actual isolated NL1 result

At19:04:22–19:04:30UTC the same public source and synthetic fixture run on NL1 using its installed
`/opt/apps/family_connect/mailbox-pilot/venv/bin/python` and installed messenger modules. Actual
fc-mailbox **UID996/GID982**, CPython3.14.4/RNS1.5.1/LXMF1.1.1; native relay/server/membership and
the separately pinned older codec are unchanged. No node/private identity or working spool is read.

The transient systemd test uses PrivateTmp/PrivateNetwork, ProtectHome, ProtectSystem=strict,
NoNewPrivileges, a dedicated writable synthetic runtime,256MiB/64-task/30%-CPU limits and no
forced-kill stop policy. A repeat retains an exited oneshot for independent effective-property
readback; UID/GID are also observed inside the fixture. Controller death, unrelated-client
continuity, stale-generation refusal, matching abort and two-row fresh reopen all pass.

The first root readback verifier wrongly treated an empty `ControlGroup` as a host-root path,
so its emptiness assertion failed. This was a verifier error, not mailbox failure; only a read
occurred, with no host-process signal. Corrected verification at19:07:58UTC checks MainPID/ControlPID0,
exit0 and the removed exact lab cgroup, then stops only the exited lab unit. Both lab units finish;
the original failed readback and successful corrected receipt are retained, not reclassified.

Working NL1 mailbox remains active/running **PID3705/0 restarts**. Before/after checks preserve its
process start/command/cgroup binding,17 effective fields, original unit-file hashes and four source
hashes. OWNER support is observed active/running **PID2022541/0 restarts**, no pending daemon reload;
no new full OWNER source/custody audit is claimed. Candidate
`9d7bf840f3455d0ef2e7653dc9289aac2f0d77c9f2a0a8e305c786f7ddb80489` is not rebuilt or installed.

## Evidence, rollback and next boundary

Private/synthetic artifacts stay outside Git in local `/tmp/fc-ha-mailbox-fence-20261125` and
remote `/run/fc-ha-mailbox-fence-20261125`; raw source capsule, runtime DBs and root manifests are
not committed. The XML failure/final receipts also remain in local `/tmp`.

| Evidence | SHA-256 |
| --- | --- |
| Qualified fence source | `6bac997f0cbc21c8ed67fca15a8c7659e3dfdaea1d5c592f6aef7ac845a54c12` |
| Final64 JUnit | `d50446dde711be2c347effe9c6a5dd75a1b335c5f1038d7202882c9deac5b380` |
| Failed synthetic-link fixture run | `2e281c68e507cee629ec8eb3437a5b0a08c822c126f91164772f5fb9f7759312` |
| Failed duplicate-singleton setup run | `9a126c102a08b187f4876d80b685a7d673827fe962993272d1b1f1cf870a3f64` |
| Independent corrected NL1 result | `b0c308ec123e9af37c6c6ab82d00add2a63639968b5d52f670d8461157213a45` |
| Retained effective sandbox readback | `f3244973d08f0dc8077c2964ff593b3df9c1b0668fa895218445b46b1939b8bb` |

No working injection, stop, deployment, policy/data write or replay occurs; no production rollback
is needed. Lab abort changes code only, not data. No RU/NL2/container/MicroTrader operation, retired
host, HA-03/public-version change or persistent privilege change. No additional owner input now.

Next, within the **same settlement gate**: bind the remote hold to independently checked OWNER
quiescent/exit generation and replacement commit, prevent late old RNS links/callbacks from writing
after reopening, and qualify independent restart/controller-death/abort recovery. Do not wire the
current abort or local drained flag as a successful handoff. Then authorized activation/readback,
remaining manual/OWNER writer coverage, coherent capture, independent current trust/custody/approval
and full recovery remain. The same three HA-02 gates are partial; replication passes in isolation.
