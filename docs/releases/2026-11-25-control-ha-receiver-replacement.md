# HA-02 — paired RU receiver replacement and data-preserving rollback

25 November2026. Selected task:CONTROL-HA-20261123 / HA-02, not HA-03 cutover.
[PLAN](../PLAN.md) · [STATUS](../STATUS.md) ·
[Pinned installed-shape archive](2026-11-25-control-ha-receiver-overlay.md) ·
[Legacy admission bridge](2026-11-25-control-ha-legacy-http-bridge.md).

## Scope and invariants

`scripts/control_ha_receiver_replace.py` replaces only the existing
`family-connect-friends-http-candidate.service` receiver. It accepts the pinned old archive
`4e2df679761ba9e7af74128984ef2e19e8e7b228f1cc85b36d50be2b0bc24ce8` and qualified maintenance
archive `58c5fde9b91a8997a2ebe2c881c43d8032eb82899d1d3c510390dd61efdab627`. It does not build
a different runtime, rewrite an in-use archive, change product schema or introduce a second
serving process. Production scope is fixed to this unit and loopback port18086; tests use
explicitly isolated user-unit names and synthetic data only.

Preparation copies the exact original unit fragment and14 existing drop-ins into private
evidence and binds their bytes, effective configuration, original argv and PID/start/boot/
command/cgroup. The original archive stays untouched. A new private gate starts with one
durable **legacy external-outcome uncertainty** marker. This is not an empty-gate workaround:
the marker remains across activation, controller death, candidate failure and rollback.

The old main-thread bridge closes application admission, joins admitted local handlers and
both retention workers, then returns through the existing native loop. The controller separately
observes actual process exit, successful exit status and the original unit cgroup being empty;
`RETURN_TO_EXIT` alone is insufficient. It never sends TERM to the old ungated receiver.
Before irreversible retention shutdown, an expired/unfinished request aborts and preserves the
original receiver. After that boundary, stalled work remains stopped-admission/pending rather
than being force-killed or declared settled.

Only after attested exit does the controller add one last-sorting owned drop-in,
`zzzzzzzzzzzzzzzz-ha02-receiver-capture.conf`, pairing the new archive/gate argv with
`KillMode=mixed`, SIGTERM, `SendSIGKILL=no` and `TimeoutStopSec=infinity`. Existing drop-ins
are not edited. Unknown or changed files refuse the operation. Verification uses an invalid
non-mutating HTTP request:400 normally,503 `capture-busy` while gate admission is held,
then400 again. These are process/admission probes, not an end-to-end user-operation test.

## Independent recovery

An independent transient systemd controller uses `Type=exec`, `Restart=on-failure`,
`RestartPreventExitStatus=78`, `StartLimitIntervalSec=0` and `RemainAfterExit=yes`.
Exit75 means a pending drain and is retried; exit78 means a safety mismatch requiring
reconciliation, not an infinite restart loop. Successful completion remains observable as
active/exited. This is a bounded deployment controller, not a new permanent HA authority or
an ongoing receiver watchdog. Host reboot recovery is not attested by controller-death tests.

Private durable intents plus an exclusive controller lock permit resume after process death.
Candidate failure triggers code/settings rollback: gracefully drain the exact candidate PID
through a pidfd, remove only the owned byte-matching drop-in, reload, restart the original
argv and verify HTTP. **Never restore a previous product database/feed**: successful newer
writes survive rollback. The staged gate, pending marker, originals and audit receipts remain.
Recovery requested during an earlier old-process drain first reconciles that drain; it cannot
report rollback while a submitted hook can still stop the original receiver.

Manual recovery uses the retained private activation root, without editing the plan or files:

```sh
python3.14 "$ACTIVATION/controller.py" --run "$ACTIVATION" --recover
```

Do not run it concurrently with a live controller. Observe/reconcile the existing controller
first; for an independent recovery invocation use the same supervised properties under a
fresh explicitly owned controller unit. Stop neither the receiver nor its children by default
systemd TERM/KILL. Source-only rollback is an ordinary revert and does not undo an installed
runtime; operational rollback uses the retained plan. Never remove the uncertainty marker.

## Qualification and execution record

Combined qualification:88 PASS/0 skips,170.32s, using CPython3.14.4 and pytest9.1.1;
all26 control/identity dependency pins match. It selects `tests/test_control_ha_receiver_replace.py`,
`tests/test_control_ha_legacy_http.py`, `tests/test_friends_http_lifecycle.py` and
`tests/test_package_receiver_capture.py`, with the private baseline/candidate archives and
`FC_TEST_SYSTEMD_HTTP_DRAIN=1`. After the final exit-observation refinement, the complete
controller suite is rerun:24 PASS/0 skips,133.20s. No owned fixture units remain. This is24
distinct new cases, not112 distinct cases obtained by double-counting the rerun.

The24 new cases cover five actual activations; candidate startup failure/ineffective gate;
post-acceptance rollback; submitted/unsubmitted prior-drain reconciliation; four controller
death boundaries; four staged-source tamper refusals; owned/foreign drop-in refusal; three
independent systemd crash/recovery boundaries; and incomplete-header abort preserving service.
The systemd guard cases kill the real controller after old exit, before candidate start, and
between rollback drop-in removal and daemon reload. A successful restart with exit0, exactly
one observed guard restart, correct single receiver and retained synthetic data is required.

RU preparation succeeds against the unchanged PID43082 and15 original unit files. It only
stages private source/candidate/activation plan and a gate with one legacy pending marker;
no receiver stop, serving archive/unit edit or new serving process has occurred at preparation.
The private activation root is
`/opt/apps/family_connect/private-ha02-receiver-0d181404201b8d27/activation`.
Local private evidence locator: `/tmp/fc-ha-receiver-replacement-current`.

| Artifact | SHA256 |
| --- | --- |
| Replacement controller | `0d181404201b8d273546b8934c67c9628fb27c29502979f4d04820bc2c8f6590` |
| Bridge with explicit startup/refusal diagnostics | `4498f0f82df93cd20c383455dea6c6d20edd91dfdfd79222f3b973f442f0b87e` |
| Prepared private RU plan | `f2244aea12259ef28b4406fee931086d70f443c4893ca7390ce5b53a4ba076c2` |
| Combined88-case JUnit | `0b3c686e4c6bbc0262e11e6aaa7d2aac96c07c8f806f9269a5ac1a4379c119a8` |
| Final24-case controller JUnit | `9a66f50cc3033d9c2720d1242b4ad064410cc492b8aec6ba259c5b864941e88f` |
| Independent RU verification response | `257575f49b69a5fb66a0a1b6b28b41325911b1a61bbcefdee944deb4b56cade0` |

No product version, public installer/catalog, invitation page or client download is changed by
this maintenance overlay. Raw unit environment, argv, receipts and databases remain private;
only sanitized results/checksums belong in Git.

Initial native qualification exposed optional empty systemd-property serialization, volatile
`ExecStart` timestamps, Type=simple pre-exec observation and the old-process exit/PID-read race,
including the short exit interval with an already empty `/proc` command line. An empty command
is only a reason to keep waiting for attested exit, never acceptance or permission to restart.
The original fixed-sleep fixture also raced a module still importing; it now waits for actual
HTTP readiness, and preparation checks that readiness before staging any replacement state.
These are handled explicitly rather than weakening source/argv/cgroup checks. Independent
controller deaths are tested under real systemd, not a mocked restart. The bridge now records
only exception class and source function/line for unexpected refusal, not exception text,
request contents or private values.

## Actual RU activation — 15:08UTC

Qualified source commit `05edd4beeb8265a1cd786b2a73a1e548fb87f6c6` is pushed and remote-SHA
verified before activation. A fresh preflight rechecks the exact prepared plan, original
process binding/configuration and HTTP readiness. The independently supervised controller
`fc-ha02-receiver-replace-0d181404201b8d27.service` is then submitted once, using2s restart delay
and the qualified restart/terminal-status policy. No repeated launch or ordinary receiver
restart command is used.

Observed old exit: **15:07:58.460300UTC**, PID43082; bridge receipts attest zero admitted local
handlers, retention workers and children before natural exit. Acceptance: **15:08:03.236579UTC**,
new PID476518. The4.776s between these observations is not an independently measured client
outage. Guard is active/exited, `Result=success`, exit0,0 restarts. Receiver is active/running,
0 restarts, `NeedDaemonReload=no`, new archive/gate argv and all four paired kill settings.
No rollback intent is present: production rollback was not needed or claimed exercised.

Independent readback at **15:09:39.619113UTC** uses direct process/unit/file inspection and HTTP/
flock calls, not the controller's success receipt alone. It verifies the exact candidate and
old archive hashes, disappearance of the old PID, all15 original unit-file hashes, owned
drop-in hash, preserved marker, and invalid-request responses400/503/400 across gate hold/
release. After30s the entire selected unit snapshot is unchanged and HTTP still responds400.
There is exactly one pending marker: the original legacy uncertainty. No historical remote
effect is inferred settled. No product database/feed is restored and no schema is migrated.

The new installed runtime is the already reviewed maintenance overlay, not the canonical
storage adapter migration or a public application release. Original private configuration,
archive and guarded rollback remain available at the retained activation root. Native rollback
tests demonstrate newer synthetic writes survive; no intentional production rollback/re-upgrade
cycle was added. User-device mutations/client end-to-end operation and full-host reboot recovery
are **not** tested by these probes. NL and neighbouring services are not contacted or changed.

Private audit receipts/preimages are also copied to local protected evidence, excluding the
active gate directory; this audit copy is not a coherent product-data backup. Never commit raw
unit environment, private plan/preimages, audit tar or gate state. Source rollback alone does
not revert the serving archive: use the retained operational plan and documented recovery.

## Fixed remaining stage2 work

Receiver adoption does not prove historical remote effect settlement. Support/manual writers,
guarded OWNER integration, complete fleet participation/coherent capture, independent
custody/trust/approval and final current/post-ACK recovery remain. Replication PASS is still
isolated rehearsal; the same three HA-02 acceptance gates remain partial. No HA-03 fencing,
API/client failover or automatic RU-independent management is enabled here. The previous
1–2-day estimate is not a validated completion schedule.
