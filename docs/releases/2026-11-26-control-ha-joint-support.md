# HA-02 — joint support handoff qualification, not working acceptance

Local date26 November; observations below use UTC25–26 November. This is a source/qualification
checkpoint, not a release, deployed result, capture authorization or HA-02 completion.

## One selected result

Finish the coupled OWNER ↔ NL1 handoff/reclosure/recovery, resolve applicable exact-SHA CI,
qualify actual cross-host/root/service-UID boundaries, then perform the already authorized working
installation and independent readback. A helper PASS or successful local run is insufficient.

## Shutdown evidence and limits

The original WORKERS_REMAIN receipts and JUnit remain preserved, including original JUnit SHA256
`40fe8c267b11496ea2d85a4d66745015888a5f95b19b24c3b7afbf28d6d77c78`.
They cannot identify the historical remaining task. **That historical cause remains unproven.**
The earlier controlled native-tail scenario demonstrates that Python enumeration/join alone does
not establish kernel task retirement; owned thread-pidfds now require POLLHUP. Three bounded
censuses include phase, known owners, Python/native IDs, set differences and last completed step;
incomplete/non-atomic snapshots are marked. No messages, keys, thread names, frames or locals.

A separate exacteb86e856 Linux CI failure now establishes an additional concrete scenario:
`test_stop_waits_for_admitted_and_descendant_writes[queue]` refused with
`cannot join thread before it is started`. The controlled regression holds a real thread in
CPython's start/limbo transition using events, proves that it remains in enumeration while join
raises, then verifies waiting for its start-publication event before joining. No retry-to-PASS,
additional pre-check sleep, ignored native tasks or increased shutdown deadline is used.
This explains that CI failure class, **not** the original WORKERS_REMAIN receipt.

The immutable v1 manifest and all19 installed baseline pins remain unchanged. A separate
`support-capture-v2.json` changes only the candidate's `provisioning/support_runtime.py` digest.
The reproducible candidate is `621009b8df9baffb81e0d9069cfa52b3781e7dd7bf4e435dd89740e38cae5739`;
baseline archive remains `3aeb6f2badd3172e1e8d9417df77d7c097bb822153dc65b18a8318a097f6dd28`.
The prior9d7bf840 archive is retained, not overwritten or republished. No public version/tag/catalog
changes. Contract tests enforce the unchanged baseline and exactly one reviewed candidate-source delta.

## Terminal and systemd outcomes

Irreversible bridge failure retains original cause/evidence in
`MANUAL_RECONCILIATION_REQUIRED`, exit78, with RestartPreventExitStatus78. It cannot issue witness,
opening/capture permission, install a candidate, restart the old writer or enter the exit75 retry loop.
Real pending work remains WAITING/75.

A new actual-fc-support fixture failed OLD_EXIT_NOT_ATTESTED, not WORKERS_REMAIN. Both failed
runs are retained. The second adds a bounded manager snapshot: inactive/dead, MainPID/ControlPID0,
ExecMainCode0/Status0/restarts0, marked incomplete, while exited.json matches and the process is gone.
The controlled root regression proves systemd retains Code1/Status0 while a live After-reference
exists, then clears accounting to Code0 when that reference is removed and the unit is collected.
The direct fixture omitted the existing supervisor; using the real supervisor retains accounting.
The verifier still requires Code1, unchanged restart count and empty cgroup: no assertion was removed
and Code0 was not reclassified as successful exit or endless waiting. The joint supervisor also
retains the unit reference and terminal78 behavior.

## Coupled implementation

`scripts/control_ha_handoff.py` owns one resumable transaction. It independently observes the actual
root-controlled closed/drained mailbox, binds the old-owner exit and candidate to the exact ticket,
persists reservation before witness use, authenticates consumption over the existing pinned SSH
channel, then independently confirms opening and candidate liveness. No new listener or generic
coordination platform is introduced.

Reclosure first persists an irreversible generation seal, then closes selected-identity admission,
drains accepted work and old frames, invalidates prior permits and supplies a fresh independent proof
under the existing replacement lock. Only then may code-only rollback proceed. Reservation and
UNKNOWN history remain; current stores are never restored from old copies. The old controller and
private rollback entry cannot bypass the reclosure gate. A PID/start-bound root-owned startup authority
prevents a restarted candidate from reusing the previous writer permit.

Selected-identity pause keeps the subscription notification job/cursor and other-client operation.
It intentionally seals that generation; resumption requires a new qualified generation, not old
witness replay. Tests cover lost consume/reclose replies, controller death at durable boundaries,
mailbox/candidate restart, terminal failure, current-data recovery and two independent systemd processes.
Live adoption is truthfully marked as adoption, not closed-before-publication; independent verification
of the installed closed-on-restart guard is mandatory before it is accepted.

## Qualification and CI

Counts are overlapping selections, not additive:

| Selection | Result | Scope |
| --- | --- | --- |
| Joint full native before v2 delta |248 PASS/0 skips,968.02s|Actual local user-systemd and native mailbox; not working installation|
| v2 contract/runtime |47 PASS/2 explicit skips,22.68s|The separate mandatory systemd run is not credited by these skips|
| actual root/fc-support v2 |5 PASS/0 skips,61.95s|Includes controlled manager accounting and startup-authority refusal; working OWNER unchanged|
| CI diagnostic UID correction |23 PASS,2.07s|Private per-UID directories; bounded nested log emission|
| v2 joint/native runtime |42 PASS/0 skips,303.95s|Includes systemd stop, joint recovery, two-process readback and pause; not cross-host working acceptance|
| v2 CI/package contracts |51 PASS/1 explicit skip,2.73s|Overlaps contract/UID selections; does not waive native gates|

Exact `eb86e8560eec6092d2451b2dbf2abe2c0710cce5`: native45717115840 and readiness45717116039 PASS;
phase045717115877 host tests PASS but Docker failover FAIL; Linux control45717115845 FAIL on the
limbo-thread scenario. Docker stderr retention itself failed with PermissionError because the root
orchestrator's diagnostic directory was not writable by the unprivileged context. The correction
preallocates private UID-specific directories and preserves the environment into root contexts.
That masked native failure's original stderr is not recoverable from this artifact; the corrected
exact-SHA Docker execution must expose and resolve it before CI can be called agreed/PASS.
New source has not yet passed its exact-SHA workflows. NOT_RUN/PENDING are not success.

Retained CI archives (private `/tmp/fc-ha02-stabilize-20261125/ci`):

| Item | SHA256 |
| --- | --- |
| eb86-control.zip |e61bce2aa993e02a2591759791c9fc7a251482bb014145d1cf75acdefd770867|
| eb86-failover.zip |ebb84937fbf5f07df0ed79032cdf8cbdf037ba9f8bb52e1f3e874bb8c317a27a|
| joint-full-native.xml |ecdd2c3716045767acf3a39b86ff775b99201dbe41ff19cc0d3a113b6311a8b8|
| actual-root-entry-v2.xml |7701589cc44744ac9003dae4671eae84ba7e99318c908806f2f65fbdf4330354|
| v2-contract-runtime.xml |f80e563953c70a1a2c7d4d3694b8441475be9270bc9204aafa8e8a422c2b246c|

## Cross-host qualification and CI follow-up,26 November00:07UTC

Exact `c4cc510f83e3ae3d3dc667c307dabebed150b5f1`: Linux-control45722668604 PASS;
native45722668667 FAIL (17 handoff failures/252 passes), Docker in phase045722668631 FAIL
(18 failures/8943 passes/891 skips/521 setup errors). Other completed applicable workflows pass;
explicitly skipped jobs are not acceptance. Native failed artifact did not retain the candidate's
underlying reason, so that historical failure is not assigned a proven unique cause.

Controlled Type=simple exec publication exposes a concrete handoff defect: manager start returns while
the fixture exec shim still owns argv. Candidate authority was attempted outside the existing5s verification
loop and prematurely rolled back. Admission now occurs inside that same bounded loop with all PID/argv/
executable assertions intact; no timeout increases. A FIFO holds the pre-exec boundary, proves no authority
or rollback yet, then releases exec (1 PASS9.64s). First bounded candidate refusal and original safe rollback
reason are retained; private native diagnostic logs no longer hide the inner failure.

Corrected diagnostic custody reveals Docker's original `PROFILE_PARENT_METADATA`: root umask077 reduced
the newly created material directory from0750 to0700. Explicit chmod restores the required contract before
ownership/reader validation.32 scoped tests PASS2.45s; an actual root networkless maintenance container with
umask077 passes settled/pending refusal and native behavior checks. No assertion/contract hash is weakened.
New exact-SHA CI must still pass before working installation.

Actual-root trusted-channel qualification PASS at00:07:28UTC:1 test77.14s, actual fc-support OWNER and
fc-mailbox NL1 synthetic services. It verifies closed/drained mailbox, old exit, candidate binding,
reservation/witness consumption/open, real RNS stored work, selected-identity pause with notice queue/cursor
retained, other-client traffic, mailbox restart sealed, reclosure/code-only recovery, reservation unchanged,
UNKNOWN preserved and4 current mailbox rows. Capture remains false. Original working services are unchanged.
SSH uses the existing owner's UID/pins; root credentials are not copied and no new trust anchor is installed.

Failed attempts remain private and intact: `actual-root-nl1.xml` (AF_UNIX path119 bytes; controlled bind
reproduces the limit), `actual-root-nl1-short-path.xml` (canonical interpreter NOFOLLOW refusal),
`actual-root-nl1-canonical-exe.xml` (transient unit reload-state refusal). Corrections use a short runtime
path, canonical executable with independent /proc/exe check, and a pinned file-backed synthetic unit.
No failure is hidden by retry-to-PASS; working unit-state and source assertions remain strict.
Final receipt/JUnit: `actual-root-nl1-loaded-unit.json/xml` under the private qualification directory.

At00:03:49UTC an authorized NL1 daemon-reload cleared NeedDaemonReload=yes after every configured Service
directive was verified equivalent to its loaded value. Exact3 unit hashes, all settings, PID3705/start/
command/cgroup and zero restarts remain unchanged afterward. No working code, service restart or data change.
Receipt: private `nl1-reload-result.json`, remote root-only `state-ha02/nl1-reload-20261126.json`.

CI archives retained: c4cc-native.zip SHA256
`c00a184400c3e694da9770cbe462eea1b50d164831cb5296576bb5e2d1d43740`;
c4cc-failover.zip SHA256 `163365d6f9210a1dd275f6370ae9201bfed76f402a1b8e0e1f9a74aa585928f7`.

## Working namespace and main-loop qualification,00:22UTC

Exact `9a1a5509cbded1f075763922918732b4528dbf2c` native CI45726816731 PASS; Linux-control/phase0
are still pending at this observation. Their success is not inferred from native PASS.

Working NL1 remains PID3705. A bounded read-only probe records only UID/known-relay count and timing:
one expected relay, unchanged command/cgroup, callback latency54.483s while the original main thread
waits in the60s server loop. This is a separate proven mailbox-control scheduling gap, not WORKERS_REMAIN.
The existing5s control deadline is unchanged. A dedicated caught SIGUSR1 handler enables a safe point;
the root endpoint requires service-owned PID/start/boot/command/cgroup readiness, checks the caught bit,
revalidates identity after pidfd_open and signals only that pidfd. Missing/stale/uncaught readiness refuses.
The controlled child remains blocked in its original Event.wait(60) after its remote callback completes;
two native checks PASS0.88s. No service stop, arbitrary thread cancellation or added network listener.

Root-owned requests/code remain outside the service-writable state. Responses use an explicitly named
service-owned0700 directory in the existing ReadWritePaths, with unchanged ownership/symlink/read checks.
No writable-root relaxation or service restart is needed. Cross-host separated-response procedure:
1 PASS82.49s; final root/actual-UID wakeup + restart + handoff/reclosure/recovery:1 PASS78.50s,
finished00:22:09UTC, working OWNER/NL1 unchanged. Receipts are privately retained as
`actual-root-nl1-separated-response.*`, `actual-root-nl1-wakeup.*`, `mailbox-wakeup-native.*`.
These counts overlap and do not substitute for final exact-SHA CI or working installation.

## Earlier installed-state observation (superseded only by manager reload above)

OWNER23:28:31UTC: original PID2022541/0 restarts, original19 sources, unit/process/interpreter pins
unchanged before/after actual-root qualification. Neither candidate was installed in the working service.
NL1 read-only23:31–23:32UTC: PID3705/0 restarts and original three unit-file hashes unchanged.
NeedDaemonReload=yes is now observed. Every configured Service directive matches its loaded value
after systemd unit/time normalization; there is no demonstrated configuration delta. No reload,
working injection, fence/open, stop/restart or data rollback was performed. Recheck before operations.

Remaining before the selected result: pass new exact-SHA CI; install the guarded working participants with checked
prestate/rollback, then independent readback. No additional owner permission is needed, but actual
system authentication and acceptance gates still apply.

The same three HA-02 criteria remain partial: (1) current actual inputs and independent trust/custody/
authorization/journal evidence; (2) installed schemas/all writers and coherent capture; (3) independent
machine-loss custody and complete current-state post-ACK recovery. Isolated replication remains PASS.
Seven prior UNKNOWN outcomes remain. No HA-03 cutover or paid-watch/deny relaxation.
FLEET-PRODUCTION-ONBOARDING-1 remains separate and open: VPS → IP/access/roles → normal enrollment →
verified active node. Support migration alone closes neither that requirement nor all HA-02.
