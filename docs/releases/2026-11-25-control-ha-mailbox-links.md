# Support mailbox link generations — 25 November 2026

Selected: CONTROL-HA-20261123 / HA-02, the existing external-work settlement gate.
This extends the [scoped hold/drain](2026-11-25-control-ha-mailbox-fence.md); it is **qualified in
isolation, not installed, not a cross-host commit or HA-02 completion**. Owner permission is already
present. No password, extra permission or other owner action is needed for this checkpoint.

## What changes

`scripts/control_ha_mailbox_links.py` extends the pinned native relay fence with a process-lifetime
RNS Link constructor guard. It checks the exact RNS1.5.1 Link source and loaded class functions.
Incoming links born before local opening, including unidentified links and constructors already in
progress, cannot acquire the new generation later. Unmarked pre-injection links default to refusal.
The constructor epoch is sampled before native key generation; completion after opening does not
promote an old constructor. RNS still generates the native ephemeral handshake keys and verifies
identity proofs; no custom transport, cryptography or rewritten request-handler registry is introduced.

The captured five-argument relay callback must run in the exact native `Link.handle_request` frame,
for the exact incoming destination, fresh link generation, active link and same remote identity/
request. Thread-local write admission exists only inside that native callback and is cleared on
success or exception. Saved/direct support spool methods remain refused after opening; native
membership, deny/rate/quota checks remain in the original relay code. Other clients continue.

Local opening refuses stale generations, loaded/source drift and still-running native support
transactions. After opening the guard must stay installed for the process lifetime: removing it
would allow a queued old callback to write again. Abort therefore refuses after opening. Before
opening, matching abort restores the native functions, retaining dispatch globals until already
entered wrapper frames have returned. This preserves the earlier abort semantics, not a successful
cross-host handoff or settlement proof.

**A fresh link is not proof of a fresh OWNER process.** The wire fixture deliberately uses the same
still-running client to establish a new link. Independent OWNER exit/commit attestation is still
required before this mechanism can safely open in production. Every observation retains
`cross_host_bound=false`, `restart_protected=false`, `external_settlement_proven=false`,
`activation_ready=false`, `capture_permitted=false`. `OPEN_LOCAL_ONLY` is not a deployment permit.
The inherited `HELD` phase means the wrappers remain installed, not that fresh-link work is frozen.
No expiry or controller disappearance automatically opens the fence. A mailbox restart currently
loses the in-memory guard; durable startup refusal/recovery is required before activation.

## Qualification

Final **78 tests PASS/0 skips in20.42s**:13 lineage contracts,1 authenticated native wire scenario,
26 earlier fence checks,22 outcome checks and16 native relay/server/membership regressions.

```sh
/tmp/fc-control-ha-20261123/venv/bin/python -m pytest -q \
  messenger/tests/test_control_ha_mailbox_links.py \
  messenger/tests/test_control_ha_mailbox_links_wire.py \
  messenger/tests/test_control_ha_mailbox_fence.py tests/test_control_ha_support_outcomes.py \
  messenger/tests/test_relay.py messenger/tests/test_server.py messenger/tests/test_membership.py
```

The wire fixture runs three real processes with native RNS TCP interfaces bound only to loopback,
synthetic identities and authenticated/encrypted links. It pauses native dispatch after capturing
the response generator; a separate RPC controller installs the hold and is then SIGKILLed. An
independent controller observes the surviving hold and opens locally. The queued old PUT, old-link
purge and identification of a pre-open anonymous link remain refused. An unrelated existing client
continues; a fresh support link PUTs/purges successfully. Refused post-open abort leaves exclusion
intact. Fresh native SQLite reopening verifies three committed synthetic rows. In-process tests
also cover in-progress constructors, already entered SQLite transactions, stale/source/code drift,
callback exceptions/context cleanup, native membership refusal and paused-wrapper abort recovery.

Retained initial failure:9 passed/2 failed because the test imported the `LXMF.LXMPeer` module
instead of its class. Corrected import; the subsequent12-test run passed. A later76-test combined
run passed; two extra membership/context contracts bring the final complete selection to78.
These earlier runs are not added to78; no skip/filter conceals a failure.

Actual NL1 qualification: **19:38:52.206713–19:39:09.881841UTC**, installed Python3.14.4/RNS1.5.1/
LXMF1.1.1 and native installed relay/codec, under **fc-mailbox UID996/GID982**. Only the five public
fixture/bridge source files were transferred; no production DB, identity or private capsule was read.
`fc-ha-mailbox-links-lab-20261125.service` had independently read-back PrivateNetwork/PrivateTmp,
ProtectHome, ProtectSystem=strict, NoNewPrivileges, UMask0077, writable isolated runtime only,
MemoryMax512MiB, TasksMax96, CPU quota400ms/s, SendSIGKILL=no and infinite stop timeout. Native
loopback exchange runs inside its private network namespace, not the working network service.

The oneshot finished exit0 with MainPID/ControlPID0 and absent exact lab cgroup. After reading its
effective settings, only this exited lab unit was stopped; final LoadState=not-found, inactive,
MainPID0. Working NL1's17 effective fields, unit hashes, process start/cmdline/cgroup binding,
four native source pins and RNS Link hash match before/after. PID3705/NRestarts0/NeedDaemonReload=no
are unchanged. OWNER was read-only observed active PID2022541/NRestarts0/NeedDaemonReload=no at
19:40UTC; this is not a new full19-source OWNER attestation. No RU/NL2/container operation occurred.

## Retained evidence

Private/synthetic evidence remains outside Git, locally under `/tmp/fc-ha-mailbox-links-20261125`
and on NL1 under `/run/fc-ha-mailbox-links-20261125`; no keys, databases or raw state are committed.

| Item | SHA-256 |
| --- | --- |
| Lineage guard source | `86c1c33601719dcd87e06ece333f7f885e2e45acae73609d77feb4d19ee9202a` |
| Pinned RNS Link source | `d1ffccda72963bfe910799b62e363fecdbd45bb5038c81ee857beccdcf3c2da1` |
| Public five-file source archive | `d8cae5b847495ed123b359968d31159a502ac757c097dae7b0f00b9fd73856f4` |
| Native wire peer fixture | `4633ffbfabba95737e9837305be5a4ee0d51cafa19d3db977362fac9c1882247` |
| UID/system wire qualification | `3960035cdb76ec922a8dd1c2247c50c189ea1821639b8b3bf5716b92281f776a` |
| Independent NL1 result/readback | `8fe7d06ed9922fd4cc1c4d5762424d188e2cbe4f13414d10337594b08902e660` |
| Initial failed JUnit | `445f3dead2019f47345d8d0fecbe3f6c0300828e15906835ddcdb3355d1959f9` |
| Subsequent12-pass JUnit | `95606d71bbc62772beda17f02c056ec97a65ed7b46b4dabd24e5c2964840e73d` |
| Intermediate76-pass JUnit | `3760d34a064221129ab893a44ce5cf2a0d5b831e9adcf2d24d9d5317f7e86dbd` |
| Final78-pass JUnit | `c5eabd11ab66610010e50cca607eda3fdd9893b752d702bd3e120e9d7dddb0f5` |

Final78-pass JUnit is `/tmp/fc-ha-mailbox-links-regression-20261125.xml`.
Source/module AST and whitespace checks also pass.

## Rollout, rollback and remaining gate

No working injection, stop, restart, unit/policy change, product write, release/tag/catalog or
version change. OWNER candidate `9d7bf840f3455d0ef2e7653dc9289aac2f0d77c9f2a0a8e305c786f7ddb80489`
remains unchanged and **NOT installed**. There is no production rollback to perform for this lab.
Do not restore unguarded methods after local opening as a supposed rollback. Qualify durable
mailbox restart/fail-closed recovery and independent OWNER quiescent/exit/replacement-commit binding
with the replacement supervisor before working activation, including combined controller failure
paths. A caller-supplied generation or same-client fresh connection is not that independent proof.

All seven historical unknown delivery outcomes remain; no replay/purge/status rewriting is used
to make absence look settled. Retention and other-recipient activity remain outside the complete
snapshot barrier. After authorized activation/readback: finish remaining manual/OWNER writers,
coherent fleet capture, independent current trust/custody/approval and complete recovery. The same
three HA-02 gates remain partial; isolated replication PASS. No HA-03 or automatic next task starts.
