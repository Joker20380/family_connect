# HA-02 — reversible old support RNS quiescence, 25 November 2026

Selected CONTROL-HA-20261123 / HA-02, following the
[startup-only runtime candidate](2026-11-25-control-ha-support-runtime.md).
This continuation qualifies the missing **old-process application plus RNS idle boundary**.
It is not final persistence, process termination, candidate activation, external-outcome
settlement or permission to capture. Stage2 remains incomplete.

## Mechanism and rollback

`scripts/control_ha_support_quiesce.py` stages a one-use CPython3.14 callback and observes it from
an independent controller. It checks the existing19-source baseline, process start/boot/command/
cgroup binding, target-visible private namespace, staged code hashes, exact active-main/delivery
ownership and pinned RNS1.5.1 source/critical loaded code. It requires one periodic, jobloop,
traffic and inbound thread in the standalone/non-transport/inbound-only shape.

The old application's serial IPC admission and delivery scheduling pause reversibly. Error/thread
failure observation is installed before the entered receipt and delivery wait; RNS producer parking
is armed only after admitted delivery completes. It never sets the delivery cancellation event.
An already executing persistence operation continues. Scoped clock proxies park producers only at
their pinned idle-sleep call sites; **an existing native sleep is not interrupted**. The old300s
periodic sleep may therefore dominate the probe duration. No vendor/dependency file changes.

The existing inbound condition is awakened and observed without inserting a sentinel, clearing a
queue or replacing its priority ordering. Once producers are parked, interfaces/links and queues
are empty, all asynchronous descendants/children have finished and Python/native thread coverage
matches, the inbound drainer parks too. A quiesced receipt explicitly retains
`exit_persisted=false`, `external_settlement_proven=false`, `capture_permitted=false`.
Logged errors, unknown continuing workers, changed code, lost jobs or incomplete writes refuse.
Observation cannot retroactively settle errors or external outcomes from before entry.

Requests expire within360s, with at most10s of post-drain observation. Expiry is a probe rollback,
not a worker kill deadline. Parked loops have their own expiry/release checks; the callback restores
all hooks and online admission in `finally`, including controller death, receipt failure and
refusal. Original remaining sleep time is preserved. Queue-lock acquisition is bounded. There is
no stop, process-kill, queue-discard, database rewind, uncertainty-clear or auto-retry operation.
The CLI checks the restored receipt, unchanged process binding and baseline sources independently;
missing final evidence is an unknown/refused outcome, not PASS. Do not repeat an unknown request.

The new runtime candidate still refuses an existing RNS instance. Its source verifier is factored
from startup ownership checks and can be loaded independently by the probe; startup ownership
requirements are unchanged. The lifecycle import is deferred until managed close so the verifier
does not import an uninstalled control package into the old worker. The archive contract is updated.

## Qualification

The source tests cover all-thread idle pause/resume and blocked IPC, native asynchronous ratchet
and queued/descendant writes, delivery commit without cancellation, late old sleeps, uncertain
persistence, unknown threads, source/loaded-code drift, request deadlines/binding/hash refusal,
failed receipt publication, controller death and independent process/source readback. Test stores,
identities, queue callbacks and faults are synthetic; this is not an external-network E2E test.

An additional actual system-level unit runs under `fc-support`/`fc-support-ipc` and the installed
Python3.14.4, with PrivateTmp, ProtectSystem=strict, ProtectHome, NoNewPrivileges and UMask0077.
A genuine asynchronous RNS ratchet writer remains blocked beyond41s: no quiesced/restored receipt
is accepted prematurely. Release allows persistence, all-runtime idle pause and hook/admission
restoration; a fresh process as the same UID reads the saved ratchet. At17:30:30UTC this fixture
passes in42.515s, with the working process, sources and units unchanged. Only the synthetic unit
is stopped afterward. This fixture tests a reversible pause, **not a systemd stop of old support**.

Initial19-case run:14 PASS/5 failures retained. Four deadline tests expired during the old serial
loop's normal1s dispatch delay, before entry; their budgets now allow entry and test timeout inside
the pause. A fifth exposed a real observation race: releasing the failing writer immediately after
the entered receipt could precede error-hook installation. Hooks now precede that receipt while
producer parking remains unarmed until delivery completion. The corrected19-case run passes.
Final **120 checks PASS/0 skips in266.13s**:22 new quiescence,37 legacy application-probe,
19 managed-runtime,13 worker-lifecycle,25 installed-shape packaging and4 commissioning-kit cases.
Runtime/lifecycle cases use the rebuilt candidate archive outside checkout; both prior actual
user-systemd stop/persistence fixtures also pass. These120 do not include the separate system-level
fixture or working probe, and do not add the preliminary runs again.

```sh
FC_TEST_SUPPORT_BASELINE=/opt/family-connect-support/app \
FC_TEST_SUPPORT_PYTHON=/opt/family-connect-support/venv/bin/python \
FC_TEST_SUPPORT_ARCHIVE=/private/candidate/candidate.pyz \
FC_TEST_SYSTEMD_SUPPORT_DRAIN=1 python -m pytest -q -ra \
  tests/test_control_ha_support_quiesce.py tests/test_control_ha_legacy_support.py \
  tests/test_support_runtime.py tests/test_support_lifecycle.py \
  tests/test_package_support_capture.py tests/test_support_package.py
```

Private evidence: `/tmp/fc-ha-rns-quiesce-20261125`; no raw service argv, keys, stores, archives or
private operational receipts enter Git. The source-only candidate still changes3/adds4/preserves16
baseline modules, no removals, and is not installed:

- Baseline archive SHA256: `3aeb6f2badd3172e1e8d9417df77d7c097bb822153dc65b18a8318a097f6dd28`.
- Updated candidate SHA256: `9d7bf840f3455d0ef2e7653dc9289aac2f0d77c9f2a0a8e305c786f7ddb80489`.
- Previous candidate `b930197d315f5081ebc1b274e50f499622f11f200b08789957d511e5c53f5a8f`
  remains historical/retained, not silently overwritten.

| Evidence | SHA-256 |
| --- | --- |
| Initial19,14 PASS/5 failures | `21105b107d2ab8cf25d1232bbbbda6d6c8970600e3fa58a974b9af5c03a6a16b` |
| Corrected19 | `f9110da378a4bbe6cbcc1d5bada4eaf179d0ed25f1a31b5bd5edde70d5f45bb6` |
| Final120 JUnit | `192e7efe7e591a02fd858ef9dc893343c9df08667b2ffa9a80d27db26ca9969b` |
| Installed-UID system fixture | `9dee6a48110e39fa8b9482f553d55ebaab6a99e9fbe824320c03b21941586983` |
| Working probe/readback | `1db740e403eafe0dbc07aacbc6ba9a5d3dd75c2811f5618f0734fceccf639b5d` |

## Working result — 17:32:19UTC

Owner GUI sudo authentication succeeds; password goes directly to sudo, not chat, files or logs.
No sudoers/polkit changes, permanent privilege or timestamp keepalive. The authenticated terminal
is closed and its sudo timestamp invalidated after observation; ordinary future authentication is
not an engineering blocker or a missing owner authorization.

The one-use working probe completes in51.464s with3 producer loops and1 inbound drainer parked
together after application/descendant completion. It does not interrupt the old periodic sleep,
run exit persistence or cancel delivery. Online admission and all scoped hooks restore. A separate
post-return injected readback confirms the original clock/sleep/log/exception/condition hooks and
six live Python threads. Malformed IPC returns its expected rejection before/after without sending
chat messages or accessing a valid send operation.

Independent controller checks retain PID2022541/start/boot/command/cgroup,19 source hashes,
3 unit-file hashes,15 effective unit fields and interpreter executable digest. The working unit
remains active/running with0 restarts/no reload warning and the old40s/control-group/SIGKILL policy.
No working source/unit installation, stop/restart/signal, product-store copy/rewind, key handling,
container/RU/NL contact or public version/signing change. The temporary in-memory pause is restored;
it is not a standing capture barrier. Private staged code/receipts remain retained for diagnosis.

## Remaining acceptance boundary

Next is a separately qualified, independently supervised **irreversible commit** from this idle
boundary through explicit RNS final persistence/fsync, encrypted-store closure, old-process exit
and source/unit replacement, with code/config-only rollback preserving current data and unresolved
outcomes. The reversible probe does not supply that operation and its deadline must never become
a forced old-process stop. Preserve original unit/source prestate and the no-cancellation/no-SIGKILL
requirements; do not install only a kill-policy override. Current legacy errors/outbox outcomes
still require independent settlement before activation and coherent capture.

Then installed UID/source/gate/sandbox readback, remaining manual/OWNER writers, coherent fleet
capture and independent current-input trust/custody/approval/full post-ACK recovery remain.
Same three HA-02 gates partial; isolated replication PASS. No HA-03, automatic failover, product
version/public installer/catalog/signing change or new ETA.
