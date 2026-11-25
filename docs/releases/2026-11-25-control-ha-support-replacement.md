# 25 November 2026 — resumable support replacement qualification

## Result and scope

At18:24UTC the independent replacement/rollback controller is qualified in isolation:
**16 user-systemd tests plus2 actual-root/fc-support systemd tests PASS,0 skips**.
This completes the selected supervisor component, not working installation, external-outcome
settlement or HA-02 acceptance. Working support remains PID2022541, active/running,0 restarts,
with the original19 sources/3 unit files/15 effective fields/interpreter digest. No working
injection, signal, stop, upgrade, data restore or uncertainty clearing occurs in this continuation.
No RU/NL/container, MicroTrader, HA-03 or public-version operation is performed.

The exact23-source candidate remains
`9d7bf840f3455d0ef2e7653dc9289aac2f0d77c9f2a0a8e305c786f7ddb80489`, unchanged and NOT installed.
The [previous two-phase exit](2026-11-25-control-ha-support-exit.md) and startup-only managed runtime
are unchanged. All new network identities, records and credentials in the tests are synthetic.

## Controller and retained state

`scripts/control_ha_support_replace.py` retains a private immutable plan, original unit bytes,
baseline/interpreter/environment-file/source hashes, exact process binding and one-use receipts.
The staged runner imports retained sources, not a mutable working tree. Original unit/drop-in,
environment, archive, gate inode or staged-code drift refuses before another operational step;
foreign unloaded drop-ins are neither overwritten nor silently reloaded.

Preparation initializes the participant gate under its actual service UID and creates a durable
legacy-uncertainty marker before any old-process drain. This is deliberately not an empty-gate
workaround. Pending legacy uncertainty survives acceptance and rollback; no success receipt grants
capture permission or claims that old remote effects are settled.

The independent supervisor executes the one-use old bridge and commits only its matching READY
receipt. A lost controller does not resubmit remote execution. Precommit expiry restores old
admission; after commit, unresolved persistence parks indefinitely. MainPID/start/boot/command/
cgroup binding, final receipt, exit0, unchanged restart count and empty cgroup are all required.
The paired drop-in is installed only afterward: exact archive ExecStart plus KillMode=mixed,
SendSIGKILL=no and infinite TimeoutStopSec. Original Restart=on-failure and sandbox stay intact.

The generated supervisor unit uses `After=` without Wants/Requires: it retains the target's exit
status without starting or restarting it. This closes the earlier garbage-collection observation
gap. Actual system tests use the old target's **RemainAfterExit=no**, not the earlier observation
workaround. The supervisor itself retains its result, restarts after an ordinary crash/WAIT75,
and prevents automatic restart after a manual-reconciliation78 refusal. It must be launched as
an independent systemd unit, not as an owner-terminal background command.

Candidate acceptance verifies the effective paired settings, actual argv, socket, UID, mounted
gate identity, loaded archive/main/gate/close code and held lifetime operation lock. A per-process
readback is one-use. A missing start after a crash at start-intent rolls back, rather than blindly
replaying an uncertain start. Unknown/new runtime binding is not adopted implicitly.

## Rollback and failure behavior

Rollback never signals the legacy writer as a shortcut. Before its commit it waits for reversible
restoration; after commit it waits for durable exit. A running candidate is stopped only with its
qualified mixed/no-SIGKILL/infinite policy; deactivating writers remain awaited across resumptions.
Auto-restart is canceled before restoring the original command. Only an empty cgroup permits
removing this controller's exact hash-checked drop-in, daemon-reload and original-source restart.
Restarted-original detection handles controller loss before the final rollback receipt.

No database, runtime tree, profile, queue or gate is restored from an older copy. Tests write a new
encrypted record after candidate activation, force acceptance failure, then read/decrypt that
same new record after old-code restart. Native asynchronous persistence remains alive beyond41s
and completes before rollback; a fresh process reads the retained ratchet. There is no deadline
kill, delivery cancellation, old final-write replay or operation-marker deletion.

For a prepared retained run, operational resume is its pinned `runner.py --run PRIVATE_RUN`;
explicit recovery adds `--recover` through the same independent supervisor. WAIT means unfinished
drain, not failure permission to kill. A78 refusal requires reconciliation of the retained plan/
receipts/runtime, never a fresh plan over uncertain state. Initial partial staging is retained,
not automatically overwritten. Do not copy synthetic test wrappers into production.

## Qualification and observed failed attempts

- Final16 user-systemd tests:186.58s. Six controller-death boundaries, two independent systemd
  supervisor restarts, staged/foreign-drop-in refusals, candidate start failure, current-data
  rollback, repeated acceptance/recovery and native persistence beyond the old40s limit.
- Actual-root2 system tests:34.20s. Installed CPython3.14.4, fc-support/fc-support-ipc,
  PrivateTmp, ProtectHome, ProtectSystem=strict, NoNewPrivileges and0077; unwrapped candidate
  argv. Both successful replacement and supervisor death after old exit complete, followed by
  independently supervised code/config rollback and fresh encrypted-data readback.
- User-systemd fixtures alone grant ptrace access to synthetic processes (fixture prctl and
  test-only setpriv candidate wrapper). Actual-root fixtures need neither. No working process's
  ptrace policy is changed. System fixtures and supervisor units are removed after the tests;
  private synthetic state and receipts are retained.
- Initial setup error: fixture passed arguments to the old zero-argument main; empty systemd
  EnvironmentFiles was also absent from show output. Both corrected. Next attempt safely rolled
  back because Yama denied user-runner candidate attestation; test-only access was corrected.
- Preliminary11 pass predates the full fault matrix and is not added to the final18 count.
  Subsequent13 pass/1 failure reached successful native drain/rollback, but the synthetic ratchet
  lacked a known destination and normal RNS startup cleanup removed it. The fixture now remembers
  the synthetic destination before persistence; no product cleanup rule was weakened.

Private evidence is under `/tmp/fc-ha-support-replace-20261125`; system synthetic state is under
`/run/fc-ha-support-replace-fixture-*`. No raw plans/argv/environment, state, archives or keys enter Git.

| Evidence | SHA-256 |
| --- | --- |
| Initial setup error | `1a7f2902a04cdf185fa3553f719cff3733e41a5976bd86335272917acc63e868` |
| User ptrace refusal/rollback | `c9b4d2b54e932f748a697218bc9d558ad14dfc1c9d0cb6ebf2d3d2fd0d24bcff` |
| Preliminary11 | `178a41920487d6ed996ff8e530a7caefc94e158bda23ba69d15840a9f162b09e` |
| Native synthetic-readback failure | `a5cde6c0fb22938c495928dfb037f720a7f5187c6e17aa4f071270b06d1225b4` |
| Final16 JUnit | `9a9ebabc31bebd480cd1b496a5dc87a139f3aef82116f0047ae72e0a13720c4b` |
| Actual-root2 JUnit | `c1d64ca5d9f452fef98a03f2a3fc6b26007baa6a778b93f63b38653513e2bd2d` |
| Root pre/post working-invariance receipt | `d22d36dfefa9acd201f014546932da77f54ea1de99977e7c4f43bcde7a02fa87` |
| Qualified controller source | `3af60636bf262cf72765110c30615f63ef1fb1ec3fea76ffc08e4903757126ed` |

## Remaining gate

GUI sudo authentication succeeds; no password is captured, no sudoers/polkit change or permanent
privilege is installed. The retained terminal is closed and its sudo timestamp invalidated.
Technical access is not the current blocker. No additional owner input is requested here.

Next: independent reconciliation of old support external outcomes and fresh working prestate,
then the authorized OWNER activation with this retained supervisor and independent installed
UID/source/gate/sandbox readback. The existing activation/settlement gate is not waived by synthetic
tests, local exit0, an idle queue, a source push or a preserved uncertainty marker. Do not repeat
the already completed working reversible probe or install kill-policy changes alone. Remaining
manual/OWNER writer coverage, coherent fleet capture and independent current trust/custody/approval/
full post-ACK recovery follow. Same three HA-02 acceptance gates partial; isolated replication PASS.
