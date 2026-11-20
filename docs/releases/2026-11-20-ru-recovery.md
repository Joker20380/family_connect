# 20 November 2026 — RU recurrence and guarded restoration

## Scope and result

The owner reports stopped RU services again, asks whether this affects other
servers because RU provides control, and authorizes restoration. This task restores
only RU watcher/AWG/TCP. Server-validation gates PASS; owner/device reconnect and
real tunneled DNS/HTTPS are NOT_RUN. No new client version, installer, catalog,
release tag, runtime deployment, timeout change or permanent root-cause fix.
All times below are UTC; RU systemd displays MSK, three hours ahead.

## Failure and actual fleet impact

- At01:50:47.458, first failure is `TRANSPORT_OPERATION_DEADLINE`, watch mode,
  `persist_file`, boundary `after`. Total8.679693s exceeds budget8s. Decision-state
  `file_fsync` takes8.629093s and `replace_completed=false`; the preceding native
  AWG/TCP/AWG queries take approximately3.33/30.59/3.38ms.
- At22:36:22 RU AWG is failed/timeout with PID0, TCP inactive with PID0; watcher
  has2095 automatic retries. A running retrying watcher is not restored transport.
  Paid reconciliation has failed; its timer is still active. Disk has6.80GB free,
  usage78%; this is not evidence of an out-of-space event.
- The prior bounded observer captured this exact failure, not just a different
  daytime slow write: repeated `folio_wait_writeback`/`ext4_sync_file`, followed by
  `jbd2_log_wait_commit`. Sampled residence ends at8.6815s; this is not an exact
  syscall-duration measurement. The application's8.629093s measurement remains
  separate. Capture stops at01:50:47.554 on the new failure; it is not rearmed.
- All2,106,071 observer bytes are retained privately off-host. SHA256:
  `007f927b01e043ee8881523b9eecbc013558b93a61355133a8c2bceafb0778fb`.
  This establishes waiting in the guest persistence path, not the provider-host
  cause of the delay. No initiating-watchdog claim is made without a journal check.
- At entry shared RU HTTP is active, invocation starting20:01:51. Both Amsterdam
  watcher/AWG/TCP/MESH services are active with NRestarts0 and fresh `applied`
  attempts. Current MESH transaction is `COMMITTED`, first cause null; credential
  renewal last succeeds22:30:54–22:31:04. These are current observations, not a
  claim that every service remained available throughout the preceding night.
- RU transport failure does not itself mean that NL forwarding has stopped.
  Nevertheless, RU provides configuration delivery and central authorization/
  renewal; a failure of those control functions can affect NL onboarding,
  reconnects and renewed access. Do not claim that other gateways are independent.
  RU MESH bootstrap `not_found` is normal for its control role, not a missing
  service to install. Healthy completed oneshots are normally `inactive`.

## Recovery sequence and safety gates

1.22:37:20: verify existing runtime pins, command map and first-failure digest;
create a new private27-table registry backup. Integrity/foreign keys, isolated
restore fingerprints and paid projections for every node PASS. Transfer a locally
AES-GCM-encrypted off-host backup and verify decrypt roundtrip. No live DB restore.

2.22:38:18: apply only the RU command-map fence, retain exact NL command entries,
drain the reconciler and stop RU watcher/AWG/TCP. All MainPID/ControlPID0, no matching
jobs or gateway handlers. Preserve20 peers,68 cached records, deny/decision state,
bindings and configs privately; validate retained TCP bindings and unchanged state.

3.22:38:51–52: preserve the original first-failure inode via hard link as
`transport-failure.20261120-015047.preserved.json`, remove only the active latch
under stopped guards, and start watcher, AWG and TCP. Restore the exact original
command map. HTTP and peer-worker keep their original PIDs/invocations.

4.22:39:12: strict original-start continuity PASS, all three NRestarts0; exact
20 AWG and20 TCP entries, all68 revisions applied, attempt age1.385s. All eight
protected tables, transport identity/membership/terms/prepared state, generation2
material, original command map and effective units remain unchanged.

5.22:39:34–38: existing test identity obtains signed configurations over public TLS
for RU, Amsterdam1 and Amsterdam2. All challenge/configuration responses200 and
all signatures verified against the client anchor. Identity keys unchanged;
no new identity, invitation or user profile is printed or committed.

6.22:40:40–44: direct readback confirms active RU and unchanged NL service
invocations, no jobs or active failure latch. Scheduled paid reconciliation
22:40:20–25 and directory sync22:40:28–33 succeed. Their timers and renewal timer
are active. Panel imports22:39:40/43/46 show RU AWG/TCP/HTTP and both NL AWG/TCP/MESH
active with transport status `ok`, agreeing with direct inspection.

7.22:42:46: repeat the strict full recovery audit after nearly four minutes.
Original RU/HTTP/worker invocations, NRestarts0, exact20/20 sets,68 applied revisions,
all eight protected tables and runtime/unit guards still PASS; attempt age2.388s.
No new active failure file. This short observation is not an overnight stability test.

## Exact runtime and evidence

| Unchanged RU artifact | SHA256 |
| --- | --- |
| `friends-awg/paid-transport.pyz` | `125c796a30c3fba1772c47b96963517350087ad04aad675b6f33a31a5383276c` |
| `friends-awg/awg-gateway.py` | `9023d2c3f7c3a5127d67c509a16eb2d974810ff54d5b76cc225cd9b93e0b4234` |
| `private-paid-transport-v2/paid-reconcile.pyz` | `ff4601aa3bb0990b4f8566aadde1fd6b12120bffbd912b4b901e2d77a114d6aa` |
| `private-paid-transport-v2/friends-http.pyz` | `4e2df679761ba9e7af74128984ef2e19e8e7b228f1cc85b36d50be2b0bc24ce8` |
| Preserved first failure | `3a03c4c7a94a466d658812fda025a394513c2ebbf2c6284017301f3048ac982d` |

RU remains legacy transport; this recovery does not deploy observations-v1/PR45.
Private evidence, local encrypted backup and its separate key remain under ignored
`state-client-build/ops-incident-20261120/` and `state-client-build/ops-recovery-20261120/`.
Remote evidence remains in `/opt/apps/family_connect/private-ru-recovery-20261120-r1`.
No raw DB, identity, profile, command map or private evidence is committed.

## Remaining checks and stop/rollback path

- Ask the owner to reconnect and verify real traffic. Signature/service checks
  do not certify the physical client or the complete transport matrix.
- The repeat slow-fsync trigger is demonstrated; underlying storage/provider
  attribution and a permanent prevention change remain OPEN. Do not relax the
  operation budget/watchdog, bypass fsync, reset deny state or schedule auto-restarts.
- On a new failure, preserve the new receipt, apply the same RU-only fence, drain
  handlers, and stop the RU trio safely. Do not overwrite the preserved first failure,
  restore an old registry/decision cache, or stop NL/HTTP as a generic rollback.
  No package rollback is required: installed bytes were never replaced.
- Source documentation is checkpointed on the existing branch only. At entry,
  local `main` and tracked `origin/main` diverge20/300 commits. No force push,
  reset, unrelated merge or published-history rewrite is performed to hide this.
  A local checkpoint does not imply successful remote publication; the actual
  ordinary-push outcome is reported separately.

Related: [18 November guarded recovery](2026-11-18-guarded-recovery.md).
