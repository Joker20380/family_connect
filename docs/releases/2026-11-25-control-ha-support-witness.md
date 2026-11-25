# 25 November 2026 — independent OWNER replacement witness

## Result and scope

The selected HA-02 settlement gate now has an independently sampled OWNER replacement result bound
to a mailbox startup ticket. This is a source/lab checkpoint, **not working installation or a mailbox
opening permit**. It builds on [replacement supervision](2026-11-25-control-ha-support-replacement.md)
and [default-closed mailbox startup](2026-11-25-control-ha-mailbox-startup.md).

**57 distinct local cases and3 actual-root/fc-support cases pass across scoped runs,0 skips. One failed
root attempt remains retained and unexplained; this is not an all-attempts PASS or activation gate.**
The initial54 combined cases, expanded15-case witness run and final4-case lock regression overlap.
The actual root runs at20:31:08–20:31:36UTC and20:38:02–20:38:29UTC verify the working OWNER prestate before and after;
it changes only uniquely named synthetic fixture services. GUI authentication succeeds, the password
is not captured, and the sudo timestamp is invalidated after the bounded command.

The exact candidate remains
`9d7bf840f3455d0ef2e7653dc9289aac2f0d77c9f2a0a8e305c786f7ddb80489`, unchanged and NOT installed.
Seven real historical UNKNOWN outcomes are neither cleared nor relabelled. No working process is
injected, signalled, stopped or replaced; no product state, RU/NL2/container, MicroTrader, HA-03 or
public version changes. NL1 is contacted only for a read-only service observation in this turn.

## Independently checked OWNER sample

`scripts/control_ha_support_witness.py` checks the private replacement plan and root-owned journal
under the same exclusive controller lock used by replacement/recovery. Production sampling requires
root; user-systemd and actual system fixtures are explicitly marked as fixtures. It checks:

- Exact plan bytes/hash, old process binding and the support identity used by the pinned worker argv.
  Mailbox tickets now also carry the support-public SHA256; a ticket for another sender refuses.
- Matching quiescent READY, commit and irreversible committed receipts; final persistence/store-close
  receipt; unchanged staged drain source; no restored/error receipt.
- The independent supervisor's old-exited manager observation: MainPID=0, **ControlPID=0**, clean
  exit0 and unchanged restart count. The supervisor already checks empty original/current cgroups
  before recording that observation; the witness does not mistake the candidate's occupied cgroup
  for an empty old runtime. Same boot and current absence of the old PID are also required.
- Exact accepted candidate binding, native argv/source/runtime/gate/IPC readback, safe paired kill
  settings, legacy uncertainty marker and unchanged unit/restart state. A pidfd brackets the sample;
  evidence/plan/process/manager state are rechecked before returning.

A stale accepted file without the matching live runtime is insufficient. Even an otherwise healthy
restarted candidate is not implicitly adopted. PID reuse/boot change refuses conservatively. This is
a point-in-time OWNER sample, not an eternal liveness proof, signed cross-host certificate or independent
verification of the ticket's remote mailbox process.

## Durable reservation and rollback

Before returning, the witness durably records `handoff-reserved.json` in the private controller root,
binding ticket, plan and accepted-record digests. A repeated sample must match this reservation and
repeat live validation. The shared flock excludes concurrent replacement/recovery. Controller death
after the durable reservation cannot make it disappear; replay with another mailbox challenge refuses.

Both ordinary recovery and direct rollback refuse with `MAILBOX_RECLOSURE_REQUIRED` after reservation,
before writing rollback-intent or restarting a legacy writer. Dangling reservation symlinks also refuse.
This prevents an issued sample from silently outliving a code rollback to the old writer. Before any
reservation, the previously qualified code/config-only rollback remains available and preserves data.

**There is intentionally no reservation-delete/release or mailbox-reclosure executor yet.** Retain the
reservation and private evidence on failure; do not remove it or manually use an older controller to
bypass the guard. Combined recovery must first independently close and drain the remote admission
generation, invalidate outstanding opening requests and only then enable bounded rollback. That
coordinator and its failure qualification remain selected implementation, not an extra numbered gate.

## Wire and system qualification

- User-systemd uses the pinned installed Python3.14.4, copied legacy source and exact candidate.
  It exercises real old-process quiescence/exit, candidate installation/readback and code-only recovery.
- Wrong schema/fields/digests/process/plan/OWNER/sender bindings, missing or forged persistence/exit
  records, source drift, unsafe receipt modes and concurrent controllers refuse without a reservation.
- A separate controller exits71 immediately after durable reservation. A new independent verifier can
  revalidate the same ticket, but rollback remains blocked. Candidate stop/restart cannot reuse acceptance.
- An isolated native encrypted/authenticated RNS mailbox uses the same synthetic support identity as
  the real fixture OWNER. A valid OWNER sample is refused as an opening request; support remains denied,
  another sender commits, mailbox SIGKILL/restart retains the row and defaults closed. Its new ticket
  cannot reuse the reserved OWNER sample. No native production opening path is added.
- Actual root tests use fc-support/fc-support-ipc, PrivateTmp, ProtectSystem=strict, ProtectHome and
  NoNewPrivileges with RemainAfterExit=no. The service UID cannot write the controller directory.
  Root sampling and rollback refusal pass, alongside the two prior actual-root replacement/recovery cases.
- Root prestate verification checks working OWNER PID2022541,19 pinned sources, retained unit files/
  effective settings, process binding and interpreter digest before/after. OWNER remains active/running,
  NRestarts=0. Read-only NL1 observation retains PID3705, active/running, NRestarts=0, NeedDaemonReload=no.
  No fresh full NL1 source/unit audit or actual-NL1 witness deployment is claimed.

The first11-test witness pass takes76.77s; the combined54-test pass takes258.24s; the expanded15-test
witness pass takes82.00s. Final review finds that the public direct rollback method could race a witness
without acquiring the lock itself; it now acquires that same lock and the already-locked controller uses
an internal method. Four targeted lock/install/rollback tests pass in19.72s, including direct rollback
lock contention. Actual-root3-test passes take27.47s initially and26.22s on the final source recheck.
The union is57 local cases plus3 root cases; preliminary/overlapping runs are not added to inflate it.
Raw synthetic stores, identities, root evidence and JUnit outputs remain outside Git.

### Retained native exit failure

The intervening root attempt at20:35:51–20:36:35UTC fails1 case in43.04s while waiting for acceptance.
The retained old bridge has READY, commit and irreversible committed receipts, then
`error.json: reason=WORKERS_REMAIN, irreversible=true, capture_permitted=false`; no clean-exit receipt
exists. The independent controller returns WAITING_OLD_EXIT until systemd's start-rate limit stops it.
It does not install the candidate, issue a witness or clear uncertainty. The synthetic fixture's bounded
teardown uses SIGKILL only on its uniquely scoped lab unit; this is **not** a safe production rollback.
Working OWNER prestate still matches after this failed attempt, and the later retry passes all3 cases.

The receipt does not retain a thread/native-task census, so the specific extra worker and cause are
not proven. Do not label this a scheduling flake, enlarge timeouts or weaken `only_main()` to get PASS.
Retain the failed fixture under `/run/fc-ha-support-replace-fixture-27462b4c862c4082915fdae6553da22e`,
its private receipts and JUnit, and diagnose it before working activation. The failed unit is removed;
all scoped user/system fixture units are absent at20:39UTC. No product data is restored or replayed.

## Evidence checksums

| Evidence | SHA256 |
| --- | --- |
| OWNER witness source | `0f2ad862c042eee6efc07afaa0835e9e5d8de6d83cd2a5453697df9e0d512c7e` |
| Replacement supervisor source | `872d1dd6954188e7462b1d7909ef670909c1fa04eafe391d666d647e31e1bdf9` |
| Mailbox startup source | `d020fb409f3f942bc2e997ded282419e60f12c5dc88c46556a24dbc5d956117c` |
| Initial11-test JUnit | `52fbfe2ed03774c693d29c1468aafe9e99aa00773fe2afba937642040675de9e` |
| Combined54-test JUnit | `e8cac06875b4ce1fd55522f05ed8463974f0be3f07fcddf01ea44f27d24ef3df` |
| Actual-root3-test JUnit | `6feaa8165fbf1c330a77b287c92ccd6b0fc030391a9545d6ba17f51a650e7f59` |
| Expanded15-test witness JUnit | `01b7d05bd9608718598ac30a13e744aebf85e8b63e1c45c0340a00dfad72fa7d` |
| Final4-test lock JUnit | `49c4fed1da202613b44cd06363d709744a45573c3b41dc93c4e1b4b349b5a50a` |
| Retained failed root JUnit | `40fe8c267b11496ea2d85a4d66745015888a5f95b19b24c3b7afbf28d6d77c78` |
| Final3-test root recheck JUnit | `a11a7a4269114bc452033d745fd82070fd70fdfac547e3809efad1b527b1e744` |

## Remaining selected work

The result explicitly retains `mailbox_live_verified=false`, `opening_permitted=false` and
`capture_permitted=false`. Expected mailbox ticket fields and a root-owned local file alone are not
independent proof of a live closed/drained NL1 participant. The current supervisor's legacy READY
authorization is not yet wired to a fresh remote hold; no production handoff must use it alone.

Next: diagnose the retained native worker-exit refusal with evidence, then paired NL1 startup-unit/
manifest installation and existing-PID hold adoption, authenticated
transport/consumption of the OWNER sample with independent live mailbox verification, and combined
opening/reclosure/controller/deployment/crash recovery. Then authorized OWNER activation/readback,
remaining manual/OWNER writers, coherent capture and independent trust/custody/approval/full recovery.
The same three HA-02 gates remain partial; isolated replication PASS. No HA-03 or fleet-onboarding
implementation starts, and no additional owner input is required at this source/lab checkpoint.
