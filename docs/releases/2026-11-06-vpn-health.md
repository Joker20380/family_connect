# VPN health — 6 November 2026

## Live recovery and schedule interlock:6 November14:00UTC

Pinned helper0aaa931/`4f7fa6d3…` dry-run and apply both pass. The original empty
transaction is ABORTED with its OPERATION_BUSY cause/intent preserved and no DB writes.
The first normal repair renewal is **not PASS**: it returns75,
ROLLED_BACK_READERS_STOPPED / DIRECTORY_INVALID, preserving revocations and stopping
expired readers. Its full log remains `live-first-renewal.log`. After schedules were
restored, another empty OPERATION_BUSY attempt appeared; it was separately reconciled
by the same guard after pausing the existing schedules again. No marker was deleted.

The existing bounded publisher worker `f44ace11d7013cdf2908e888a5ed6175a936970ab9c9195ddf9846d77f587995`
was reused on NL1 and copied unchanged to NL2. Each root-bound, short-lived configuration
pins its actual historical canonical profile/locator/publisher contract and directory
inode/UID/GID. With gateway processes stopped, real Telemost room stage returns
STAGED_ROOM_READY, then accepted atomic publication returns DIRECTORY_PUBLISHED on both.
No manual directory or READY flag, new gateway identity, signer or relaxed trust is used.
Original failure state is saved before resetting the systemd failed latch for the bounded
worker's inactive-reader prerequisite. Worker configuration must be retired after recovery.

Ordinary operation `owner-live-mesh-20261106-directory-recovery` returns **COMMITTED,
exit0, first_cause=null**. Current candidate signatures and exact three-node reconciliation
were verified before normal gateway starts, needed because their saved pre-operation state
was inactive. NL1 PID3625967 starts13:59:57UTC; NL2 PID2228070 starts13:59:59UTC, both
NRestarts0. HTTP PID2856504 is restored only after terminal COMMIT/owner cleanup. These
are new connections after an outage, not seamless session renewal or isolated G4 evidence.

The installed directory evaluator holds the RU node operation lock across both SSH reads.
The controller writes ACQUIRING before taking that lock, so a competing publisher can
leave an empty RECOVERY_REQUIRED operation. The historical holder is not retrospectively
identified, but the race is reproduced with a real node lock in the fleet fixture.
`scripts/run_serialized_renewal.py` serializes the existing scheduled service: temporarily
stop only directory-sync.timer, wait at most120s for its existing oneshot to finish, invoke
the unchanged pinned controller, and restore the timer's original active/inactive state
in finally. It does not stop an in-flight directory worker, change intervals/SSH120/TTLs,
abort transactions automatically or create another controller/writer/timer. Unrelated
contention still fails closed for explicit diagnosis.

Qualification:32 PASS/1.32s for the interlock and unacquired guard, including a genuine
held publisher lock followed by successful ordinary three-node renewal, preserved exit
codes, timeout, missing units, cancellation and timer-restore failure. This overlaps20
unacquired cases in the earlier128 suite; counts are not summed. Interlock is not yet
installed at this source checkpoint; final live readiness/stability readback is pending.

## Authorized diagnosis and guarded recovery preparation

The owner subsequently requested diagnosis and repair. Pinned read-only SSH confirms
both canonical gateway leaf and shared CRL expired **5 November11:44:40UTC**,
minimum CRL27273/revision1. AMS2 logs show session shutdown around that bound, then
immediate failed process starts and the systemd restart limit. AMS1 retained no journal
entries for the queried window; its matching canonical expiry and failed state are
separate observations, not an invented identical log.

The earlier causal failure is RU scheduled operation
`scheduled-1793873691-d5a13907e2bb958f`: first OPERATION_BUSY at10:15:12.822953UTC,
RECOVERY_REQUIRED, acquired=[], quiesced=[], commit_decided=false. Current readback
finds no owner or preparation artifacts on any node. Both canonical profiles and all
non-database inspected state match the operation's predecessor. Only RU database digest
differs. The transient lock holder and particular later database row changes are not
attributed. Scheduled recovery retains the original first cause; it cannot adopt a newer
DB or restore expired material merely to recover availability. Ordinary AWG/TCP and the
HTTP candidate are active; no blind restart has been attempted.

`scripts/reconcile_unprepared_renewal.py --abort-unacquired` is a narrow explicit
operator recovery, not a second controller/timer. Under existing coordinator and local
RU locks it requires the exact fleet/RU-first acquisition contract, empty acquired and
quiesced sets, OPERATION_BUSY, no decision/mode, no local owner/staging/completed entry
or plan for this operation, unchanged authority/grants/non-DB state and no pending
revocations. A lost acquisition response leaving an owner is rejected. It preserves the
original record and an observational intent before marking only the empty coordinator
operation ABORTED, with no node/DB/profile/service writes. Replays bind that intent;
another operation or prepared/committed/online state cannot be cleared. Leaf/CRL may be
historical only for this non-activating abort; normal renewal still validates fresh
successors and all current revocations/floors before restarting any reader.

Source checks: **128 PASS/16.30s**, existing unprepared reconciliation + new unacquired
recovery + fleet renewal tests. Includes actual lock contention, subsequent DB drift and
expired predecessor, zero-write abort, normal common renewal, duplicate/crash replay,
pending revoke and ownership/preparation/policy/profile rejection. This is scoped Python
qualification, not full CI or production recovery. Initial test collection/import and
negative-fixture mistakes are retained in local logs, not relabelled PASS.

Private readbacks and logs: `state-client-build/mesh-live-failure-20261106/` (not Git).
Next: independently pinned live dry-run; only after its exact predicate passes, abort
the empty transaction and use the existing installed controller for normal fleet renewal.
Pause/resume existing schedules only for that bounded repair; do not alter timer settings,
admission, grants, boot, artifacts, owner phone or the isolated G4 resources. Recovery
does not roll back the product database or restart expired gateway profiles.

## Original read-only snapshot

Read-only snapshot13:27UTC (14:27 Brussels), followed by bounded diagnosis.

| Metric | RU | AMS1 | AMS2 |
| --- | --- | --- | --- |
| CPU us+sy, three one-second samples | 70–72% | 5–22% | 0–2% |
| Load1/5/15 | 0.97/1.32/1.46 | 0.17/0.29/0.31 | 0.05/0.13/0.17 |
| RAM used/total MiB | 1161/1962 | 828/1914 | 419/1919 |
| Available RAM MiB | 801 | 1085 | 1500 |
| Root disk used/free | 71%/8.4G | 17%/39G | 15%/39G |
| AWG configured peers | 19 | 48 | 5 |
| AWG handshakes180s/24h | 0/2 | 4/18 | 0/2 |
| TCP443/8446 established sockets | 0/0 | 91/0 | 5/0 |

AWG/TCP active on all three, NRestarts0. Both NL MESH bootstrap services FAILED,
NRestarts6, Result exit-code, ExecMainStatus1. Last recorded exit5 November11:47:41UTC
on AMS1 and11:47:42 on AMS2. These timestamps do not establish continuous outage
duration. Root cause unknown: bounded journal keyword scans returned no matching
evidence, not proof of absent errors. RU bootstrap inactive as before.

RU follow-up five two-second CPU samples4–31%, IO wait0–15%, steal2–4%; initial
steal5–7%. Initial spike is not sustained saturation proof. RU swap924MiB, initial
one4KiB/s swap-in, follow-up si/so0. Cleanup gain mostly retained,8.4GiB available.
External RU8443 TLS validates (verify0); HTTP404 at root is not API-health acceptance.
Four recent AWG peers and96 TCP sockets are not unique clients. MESH sessions not
counted; no client end-to-end test. Existing connections do not prove MESH admission.

No restart/repair, deletion, configuration, publication or version change. Rollback
not applicable. Entry documentation retains opt-in118/default113/catalog7; no artifact
readback in this check. Isolated G4 qualification is separate from live service health;
do not interrupt its container or infer production acceptance from it. Next operational
follow-up: diagnose both failed NL bootstrap services before any authorized recovery.
Preserve unrelated working changes. TLS-renewal job/legacy Docker worker not rechecked.
