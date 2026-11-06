# VPN health — 6 November 2026

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
