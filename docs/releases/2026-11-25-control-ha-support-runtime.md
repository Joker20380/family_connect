# HA-02 — support RNS lifecycle candidate, 25 November 2026

Selected CONTROL-HA-20261123 / HA-02, after the
[successful working application probe](2026-11-25-control-ha-support-live-probe.md).
**Pinned standalone runtime shutdown and the rebuilt source candidate are qualified in isolation.
The working service is not upgraded, stopped or newly capture-ready. Stage2 remains incomplete.**

## Runtime boundary

`provisioning.support_runtime.ManagedRuntime` owns a new standalone RNS instance, not an existing
one. It checks four exact RNS1.5.1 source files and critical loaded code, main-thread/native-thread
ownership and the supported inbound-enabled/outbound-disabled queue shape. No dependency or vendor
file is modified; runtime hooks are scoped and restored. This is not attestation of every wheel
byte or arbitrary plugin/transport configuration. Reticulum's existing license still applies;
no vendor source is copied into the adapter or public artifact published.

Configured `support_worker --capture-gate` now holds its operation for the entire worker lifetime,
from before private store access until final store close. Reticulum initialization, periodic
writers, asynchronous descendants and exit persistence are inside that boundary even when their
threads do not inherit Python context variables. Application operations keep their existing guards.
An idle worker cannot pass `Gate.drain`: this candidate uses a managed stopped capture interval,
not an idle-service snapshot. Omitting the option preserves the ungated legacy behavior.

Shutdown proceeds without cancelling admitted work or applying a forced deadline:

1. Existing support lifecycle stops IPC admission and waits for admitted delivery/route cleanup.
2. Runtime shutdown waits for active interfaces/links to finish, rather than tearing down a live
   exchange. Producer stop requests are observed only at the exact pinned periodic/job/traffic
   loop idle sleeps; sleeps inside an ongoing cache/persistence operation remain untouched.
3. Inbound processing preserves the original priority queues. It drains queued work and waits for
   asynchronous descendants, including actual ratchet persistence. Queue workers finish only after
   producers/descendants have completed and all queue workers are idle. No queue-clearing shortcut
   is used to establish that condition. Python/native task coverage and absence of children are
   required; unknown continuing work prevents successful closure.
4. With workers gone, validate the retained runtime directory identity and private no-link file
   tree, then run the pinned native exit handler once. Its ordinary interpreter-exit registration
   is removed so a failed explicit flush is not silently retried after admission is released.
   Restore application stdout/stderr, which Reticulum otherwise redirects to `/dev/null`.
5. Join any final workers, check native task coverage, fsync runtime files/directories, close the
   encrypted support store and only then release the outer operation. Repeated TERM/INT during
   draining do not interrupt these steps. This has no guaranteed completion time for a stuck I/O
   operation; the paired main-only/no-SIGKILL/infinite-stop policy remains mandatory.

RNS error/critical logs and uncaught worker exceptions latch uncertainty, including asynchronous
failures that do not propagate to the caller. Failed flush/fsync, unsafe or replaced state and
application failure also preserve the gate marker. Catching a close error and trying again cannot
settle it. Successful local persistence is **not** proof of an external delivery/ACK outcome;
existing pending/outbox records and independent settlement requirements remain.

## Candidate and qualification

The exact installed-shape builder now produces23 source modules from the19-source baseline:
3 changed,4 added,16 preserved, no removals. The general commissioning kit includes the new module
too; no private state, compiled output, dependency wheel or signing key enters either archive.

- Baseline archive SHA256: `3aeb6f2badd3172e1e8d9417df77d7c097bb822153dc65b18a8318a097f6dd28`.
- Final candidate SHA256: `b930197d315f5081ebc1b274e50f499622f11f200b08789957d511e5c53f5a8f`.
- The preceding candidate `ae30efc5271f53d1bbcfa49097f899831c31deb37a8bdabc536d19490f7765e6`
  remains historical and retained; it is not the new runtime-qualified candidate.

Final **169 tests PASS/0 skips**:165 in133.35s plus4 commissioning-kit regressions in0.58s.
The165 comprise19 runtime cases,13 worker-lifecycle cases,25 installed-shape packaging cases,
19 dispatcher regressions and89 operator-admission regressions. Native runtime/worker cases use
the installed Python3.14.4 interpreter and the final archive outside the checkout, with synthetic
stores, identities, queue inputs and faults. RNS known-destination/ratchet writers are real;
synthetic inbound callbacks are not an end-to-end network-delivery test.

Two **actual user-systemd** fixtures use the paired stop policy: one preserves an admitted delivery
child beyond41s, the other preserves a blocked native asynchronous ratchet writer beyond41s.
Both remain deactivating until release, then exit0 with fresh encrypted-store/RNS readback and
clean gate drain. The full runtime leaves one main Python/native thread before exit. Additional
cases cover descendant enqueue after stop, periodic writes, final exit writes, process death,
source/loaded-code drift, unsafe/replaced state, caught-close errors and persistence failures.
These are owned user units, **not new fc-support-UID or complete production-sandbox qualification**.
Only synthetic units/process groups are stopped; the working system unit is untouched.

```sh
FC_TEST_SUPPORT_BASELINE=/opt/family-connect-support/app \
FC_TEST_SUPPORT_PYTHON=/opt/family-connect-support/venv/bin/python \
FC_TEST_SUPPORT_ARCHIVE=/private/final-candidate/candidate.pyz \
FC_TEST_SYSTEMD_SUPPORT_DRAIN=1 \
python -m pytest -q -ra tests/test_support_runtime.py tests/test_support_lifecycle.py \
  tests/test_package_support_capture.py tests/test_capture_dispatchers.py tests/test_operator_capture.py
python -m pytest -q -ra tests/test_support_package.py
```

Failed attempts remain evidence, not additional successful tests. Initial6 PASS/10 failures used
the shell's002 umask, producing group-writable synthetic RNS files; the actual service has0077.
Fixtures now use0077; private-state validation was not relaxed. A later integration case exposed
Reticulum swallowing the application's stderr after finalization: exit failure and uncertainty
were present, but its diagnostic was hidden. The adapter now restores application streams and the
final full run passes. Intermediate51-case/161-pass-one-skip/163-pass runs are superseded by the
final archive-bound165, not silently counted as final qualification.

Private evidence locator: `/tmp/fc-ha-rns-lifecycle-20261125`.

| Evidence | SHA-256 |
| --- | --- |
| Final165 JUnit | `2f8cf693f916b787f1db4fd77877fbad62ac5353ffac27e19cf3e4bb8308afbc` |
| Commissioning-kit4 JUnit | `405496ad7c8602c9bb92cac32607bc891d79ea456ca9efe76142e09d639d9863` |
| Working readback | `71c9d6b716f9db6dfef15bc00c9f916bbb7ad8e7d97b45ab86b4f2403bfa2839` |
| Initial permissions-fixture failures | `e1917783b03c1305ede6f8a63491f7cfb388ad79f96f44ab4928da6c5727479e` |
| Hidden-error integration failure | `16fe23f1a153569e8a3e48995b7fdfcb1d88c2625d456e1adbaea419f6238f35` |

## Working state, rollback and next

At17:07:01UTC support is active/running PID2022541,0 restarts/no reload warning. All19 installed
source hashes still match baseline; UMask0077 and the old control-group/SIGKILL/40s policy remain.
This is fresh source/unit-field observation, not a new privileged comparison of private unit-file
contents or full interpreter/in-memory attestation. No working runtime hook, signal, installation,
unit/policy change, container/RU/NL contact, product data or public version/signing change occurred.
The16:40 working reversible application probe remains accepted within its original scope.

There is no production deployment to roll back. Source rollback returns the optional candidate/
builder changes only; never restore an old store or clear uncertainty. Preserve failed archives
and receipts privately. This new owner deliberately refuses an existing RNS instance, so it must
not be injected as though it could adopt all already-running jobs. The old periodic loop can be
inside its300s sleep; the earlier15s application probe is not a full runtime drain/stop mechanism.

Next: independently supervised old-process drain/transition/rollback, with application and RNS
writer completion and independent remote-outcome settlement before candidate activation. Then
actual installed UID/source/gate/sandbox readback, remaining manual/OWNER coverage, coherent fleet
capture and independent current-input trust/custody/approval/full post-ACK recovery. No ordinary
old TERM/40s force-stop or kill-policy-only deployment. Same three HA-02 gates partial, isolated
replication PASS; no HA-03, automatic failover, release acceptance, new numbered stage or ETA.
