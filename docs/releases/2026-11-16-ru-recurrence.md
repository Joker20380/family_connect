# RU recurrence — 16 November 2026

**Current outcome17 November00:02UTC: RECOVERED_CAUSE_OPEN.** The owner separately
authorizes restoration of the22:07 recurrence. Fresh backup/isolated restore and
unchanged-runtime recovery pass, followed by six strict observations and preservation
checks. The initiating cause remains open. See the [new recovery receipt](2026-11-17-ru-recovery.md);
the earlier unavailable observations below remain historical evidence.

## New recurrence — 16 November22:07UTC

**OPEN / RU AWG down, TCP down; initiating stall still CAUSE_OPEN.** A fresh readback
during final source qualification discovers a new failure at22:31UTC. This checkpoint
is bounded read-only diagnosis, not another recovery or observer deployment. Public126
was accepted/published20:42UTC while the previous recovered transport guard passed;
later source integration does not change production or imply healthy RU.

### Observed sequence

A single observed active journal file, the22:06–22:09UTC window and four exact
Family Connect units produce21,179bytes of selected records. The diagnostic runs with
20s wall/128MiB/no-swap/10% CPU/1MB/s disk-read limits and finishes exit0; its unit is
then not-found/inactive/PID0. No whole-journal scan, deletion, vacuum or overload test.

| UTC | Observed event |
| --- | --- |
|22:07:31.837827 | scheduled paid reconciler starts |
|22:07:37.828226 | paid-watch watchdog timeout; systemd begins killing watcher |
|22:07:37.831940–.833648 | dependent AWG/TCP stops begin |
|22:07:40.384016 | TCP exits successfully |
|22:07:43.604546–.609046 | AWG stop times out, SIGKILL, result timeout |
|22:07:48.829789–49.928537 | watcher-only automatic restart, without engine restart |
|22:07:54.317494 | secondary register/engine_query COMMAND_FAILED record |
|22:08:04.028113 | reconciler exits1 after the engine failure |

The initial blocked operation is not in the retained failure record. Its SHA256 is
`80639df0b1666340813885ccf92ccb10ed435291088bab6d6ad1b1e2c5c1531b`:
register/engine_query, CalledProcessError/awg-query, returncode1, elapsed5.055984s,
budget8. Do not call this record the initiating watchdog stack. At22:31 watcher
NRestarts40; at22:33 it is44. Six bounded current-process samples show polling/sleep
and another restart, not a surviving initiating blocked syscall.

### Resource evidence and exclusions

Existing sysstat's68,148byte daily file provides ten-minute samples; these are
interval aggregates, not per-process or instantaneous attribution:

| Interval ending UTC | CPU iowait | vda read KiB/s | vda await ms | Average queue | IO PSI full | Memory PSI full |
| --- | --- | --- | --- | --- | --- | --- |
|22:00:01 |4.34% |0.06 |44.54 |1.42 |4.93% |0.00% |
|22:10:00 |8.93% |1565.42 |160.97 |9.71 |9.37% |2.65% |

The failure interval also has7.08/17.22 swap-in/out pages/s,303.01 kswapd and29.45
direct-reclaim scanned pages/s. This supports a recurring I/O/reclaim-pressure
condition, not a proved OOM, provider fault, specific process or filesystem syscall.
The same bounded kernel window has18 records and no matching OOM/hung/I/O-error
category. No existing atop history is available. Checked standard apt/man-db/logrotate/
fstrim/dpkg-backup/tmpfiles jobs do not start in this interval; that is not an exclusion
of all possible host workload. Neighbouring application data/services are untouched.

**No journal scan from this task runs near22:07.** Thus earlier broad operator scans
cannot be the sufficient general explanation for the recurrences. They remain an
avoidable load, not a proven sole root cause. Metadata has only one retained device
row, revoked epoch6/sequence116, with zero enabled/eligible GeoIP rows. The collector's
no-eligible branch returns before opening/hashing MMDB; no diagnostic hashes the
126,873,350byte City or9,648,279byte ASN files. Do not attribute this event to a GeoIP
lookup without actual eligible-input evidence.

### Preserved state and remaining scope

Node SHA125c796a30c3fba1772c47b96963517350087ad04aad675b6f33a31a5383276c,
gateway9023d2c3f7c3a5127d67c509a16eb2d974810ff54d5b76cc225cd9b93e0b4234 and
effective watcher unit659b954beb67d1e23c0cea45ffda62704f48dc2fb0b1f5bd30d0ae733760bd4e
remain accepted. The standalone unit file has a different hash from `systemctl cat`
including drop-ins; that distinction is verified, not treated as unknown runtime drift.
Loaded watchdog12s/stop5s/restart-on-failure5s and stdout journal/stderr null are
unchanged. No timeout, dependency, persistence guarantee or policy is weakened.

HTTP2394053 and peer3967036 remain active. At22:30 HMAC2/manifest, canonical/panel
revocation with zero groups/no geography, support IPC, original baseline/cursor4,
baseline time1794660500, anchor and four excluded events pass. No selected-device
jobs/source error or new real notification delivery. No recovery, stop/start,
reset-failed, reconciler/timer change, new backup/restore or observer deployment is
performed for this new incident. An unchanged recovery can restore availability but
cannot establish the initiating cause; do not report it as a recurrence fix. Keep
fresh incident evidence separate from the successful earlier recovery below.

## Watchdog cascade and guarded recovery — 16 November evening

**RECOVERED_CAUSE_OPEN; cascade established, initiating stall not conclusively
attributed.** The owner's request to find why the processes stop explicitly selects
this separate RU investigation/restoration. It does not authorize a new APK, HMAC
rotation, publication, relaxed paid deadlines or deployment of the unqualified
recorder. Entry source/remote feature is
`2ec88d3656fef70210667a9c885af4f4b1ac17cb`; main remains
`53a780d9ccfcdb2c3ec6141a197917190f9be7a5`. The dirty primary checkout is untouched.

### What actually stops the services

The corrected, bounded manager timeline attributes events using `UNIT`, not the
manager process's `_SYSTEMD_UNIT=init.scope`:

| UTC | Observed event |
| --- | --- |
|17:38:50.578553 | paid-watch watchdog timeout; systemd sends SIGABRT |
|17:38:50.594249 | AWG stop begins through the dependency/fail-closed boundary |
|17:38:50.599222 | TCP stop begins; it exits successfully at17:38:50.736201 |
|17:38:55.892582 | AWG exceeds its5s SIGTERM stop window |
|17:38:55.896649–.897600 | systemd sends SIGKILL to AWG and watcher |
|17:38:56.007452–.008763 | AWG result timeout; watcher result watchdog |
|17:39:01.087305 | automatic watcher restart scheduled |

These are not two independent transport crashes, a metadata revoke, an expired
user subscription or an HMAC-generation switch. Losing the local paid controller
intentionally closes both ordinary transports, including noncohort clients. Restarting
only the watcher does not start the engines again. Subsequent queries against stopped
engines fail, explaining the growing restart counter without restored connectivity.
At19:21:16UTC the counter is172 while both engines are still down.

The retained first-failure file is **secondary**, not the initiating watchdog stack:
register/engine_query, COMMAND_FAILED, elapsed1.89077s, recorded17:39:09.859747UTC
after the engine stops. Its unchanged SHA256 is
`5ad8504e02f4924df2e8f252e07dfc12b2cb3704549b2bc3d4944b67bc406d90`.
Do not relabel this as an8s persistence failure or blame registration for17:38:50.

### Resource evidence and limits of attribution

Existing sysstat samples cover the failure, but their ten-minute resolution cannot
identify the process or syscall stalled at the watchdog instant:

| Interval ending UTC | CPU iowait | vda read KiB/s | vda await ms | Average queue | IO PSI full | Memory PSI full |
| --- | --- | --- | --- | --- | --- | --- |
|17:30 |5.40% |979.63 |52.95 |1.83 |5.91% |0.04% |
|17:40 |20.19% |5779.53 |129.21 |17.52 |21.10% |8.36% |
|17:50 |3.55% |49.50 |50.85 |1.50 |3.97% |0.03% |

The middle interval also has26.89 swap-in/58.56 swap-out pages per second,
1696.87 kswapd-scanned pages/s and48.40 direct-reclaim-scanned pages/s. This supports
an I/O/reclaim-pressure hypothesis on the approximately2GiB guest, not a claim of
OOM, exhausted disk space, a provider fault or CPU throttling. The bounded kernel
window has no matching OOM/hung/I/O-error records; that is not a whole-host historical
exclusion. Current post-failure free memory does not disprove transient pressure.

Our operator diagnostics are a possible contributor and are not exempt merely
because they are read-only. Broad journal-query receipts finish at17:37:41 and
17:39:22, bracketing the watchdog in that workflow. The25 system journal files total
1,560,281,088 bytes. A bounded footprint check of the same broad credential-renewal
query, while the engines were already down, reads19,030,016 bytes before its20s
limit. Its cgroup peak is29,966,336 bytes and CPU time47.129ms. Limits are128MiB
memory/no swap,10% CPU and1MB/s vda reads; output goes to null. It exits on the
configured timeout/SIGTERM, and the transient diagnostic unit is subsequently
not-found/inactive/PID0. This demonstrates nontrivial read I/O, **not reproduction
of a watcher failure**, nor proof that this reader alone caused the incident. File
receipt times are not a complete process start/end/I/O trace.

The accepted controller's8s operation checks cannot preempt a blocking filesystem
call; systemd's independent12s watchdog can terminate it before another Python
deadline check. Earlier14November evidence actually measured6.51–7.43s in fsync
chains in8.65–9.26s failed operations. That remains specific earlier evidence, not
a recovered stack for this watchdog. See the
[persistence-pressure report](2026-11-14-ru-persistence-pressure.md).

For this failure the effective watcher `StandardError=null` discards its progress
diagnostics. No matching systemd coredump, working-directory core or relevant
time-matching Python/Family apport file is found; the configured handler is apport.
SIGABRT followed by SIGKILL alone does not prove an uninterruptible I/O stack, since
core handling/termination can also delay exit. A complete initiating syscall/off-CPU
trace is unavailable. No journaling/persistence guarantee, timeout, BindsTo rule or
stderr configuration is changed to manufacture a fix. No stress reproduction is
attempted on a live restored gateway.

### Fresh recovery and preservation

At19:21:16UTC current archive/owner/private-parent/effective-unit guards pass, with
7,498,117,120 bytes free. All pins in the16:08 table below remain accepted, including
HTTP4e2df679, operator19efd0b4, reconcilerff4601aa and node125c796a. Generation2 manifest
8602e652 is unchanged and both active key copies agree inside the process.

At19:21:43UTC a new consistent canonical backup restores all27 tables with identical
fingerprints, integrity/FK checks and all three exact-runtime paid projections.
Backup SHA256:
`7eaf94b7d2cada61442154a8804bd0eda39042c1ee368e53e4343a65d132c005`.
The paused backup is encrypted off-host,194,871 bytes, SHA256
`7605ca66985815cf0b2fb312471a5715f261eb429630afed408a850a6ad77e00`;
decryption/digest roundtrip passes. No old DB is restored over live events.

At19:22:23UTC the RU-only command fence/drain/grouped stop proves PID/control PID0,
no relevant jobs and zero gateway handlers. NL commands remain unchanged. Retained
66 records/20 peers and bindings pass preflight. The original failure is preserved
while stopped. Unchanged watcher/AWG/TCP start19:23:40–41; original three-node commands
are restored. HTTP PID1866519 and peer PID3967036 are not restarted, nor are panel,
support, reconciler timer or NL services. This does not reverse the earlier normal
17:10 HTTP credential-renewal restart.

The first post-start continuity assertion **fails**, and is retained, because TCP
changes process. Investigation, not an assertion bypass, establishes this sequence:
the retained allowed cohort lease ends19:23:57, after startup but before the first
fresh renewal. TCP stops/restarts19:23:58.051302 and19:24:14.668115 as membership closes
then returns. The exact decision/binding/terms/revision/prepared/boot fields remain;
only observation/lease clocks advance. Watcher/AWG/HTTP/peer keep their original
invocations; no new failure file exists. At19:32:10 an explicit post-convergence
anchor passes actual AWG/TCP set, persisted readback and applied-revision assertions
for66 records and20/20 allowed bindings. Original start and failed continuity receipts
remain; the later stable window is not backdated across those TCP restarts.

Six unchanged strict observations at19:33:21,19:33:59,19:34:36,19:35:15,19:35:52 and
19:37:05UTC span223.969s and cross the initial observed cohort deadline. That deadline
advances1794857719→1794857921 through normal reconciliation. Every sample has66 applied
records and exact20 AWG/20 TCP bindings, with stable watcher2287887/AWG2287942/TCP2289844
and NRestarts0. HTTP/peer remain their original processes. At19:41:06UTC the final
readback again passes exact actual/persisted state, transport identity/membership/
terms/prepared-state preservation, all protected canonical fingerprints, unchanged
effective units, restored command map and the archived original failure digest.
Protected counts are devices66, invitations121, subscriptions/events1/4, chat bindings/
service senders53/1 and referral links/claims19/59. Counts are accompanied by exact
fingerprints, not substituted for them. The final checker first rejected a stale
previous-incident failure-archive filename; that reader failure is retained. Correcting
only its archive selector verifies this incident's unchanged5ad8504e bytes. No runtime
file, historical failure, acceptance assertion or protected data is changed to pass.
The reconciler finishes inactive/success and its timer remains active/waiting.

At19:33:54 support IPC and original notification baseline/cursor position4, baseline
time14November12:48:20UTC, excluded count4 and matching anchor pass; source_error is
null. No test payment, term change or message is created. New real notification
delivery remains NOT_OBSERVED. Normal19:34:21–32 imports show all three current
transport sources ok/66, RU inventory ok/66 and canonical subscriptions ok/66 on
HTTP4e2df679. NL registry not_collected and the old gateway-nl unavailable record are
existing source boundaries, not new canonical data loss. Metadata source is ok;
panel image5ae92f8c remains unchanged.

### Operational correction and remaining boundary

Do not perform unrestricted whole-journal scans on this gateway during acceptance
or recovery. Select the observed journal file and a short time/unit window; bound
runtime, memory, I/O and output. A narrow query still needs an execution limit.
Preserve logs; do not vacuum/delete evidence or bypass permissions. The bounded
read procedure and uncertainty are now explicit in the operator runbook.

This removes an avoidable diagnostic load, not a proven durable repair of the
initiating stall. Closing the cause requires a time-aligned initiating operation,
blocked syscall/scheduler interval and I/O/reclaim attribution; later engine errors
or another successful recovery cannot supply it. Unqualified observer/recorder
deployment remains outside this change. Metadata/public126 delivery is not performed
by this incident task; its existing installed/paid/HMAC2/device acceptance is retained.
Documentation checks cover6 changed files/874 local links with zero errors, plus
whitespace and scoped known-private-value review. This is the author's own scoped
review, not independent review, a runtime patch or a new full Android qualification.

## Authorized recovery — 16 November16:08UTC

**RECOVERED_CAUSE_OPEN.** After the15:34 outage diagnosis, the owner explicitly
authorizes separate controlled RU restoration on the existing runbook, with backup
and isolated restore, without changing runtime code, subscriptions or HMAC2. Entry
source is21fc927fcc59ed391a38721b6832de266562ed0a; remote feature matches and main is
53a780d9ccfcdb2c3ec6141a197917190f9be7a5. The dirty primary checkout is untouched.
This section supersedes current-health claims below, not their historical evidence.

### Current foundation and backups

At15:57:45UTC all accepted hashes, runtime ownership/private parents and effective
watcher unit match. RU/operator HMAC keys agree in-process; generation2 manifest
8602e6526ca1ec0e408c99a7ca37aedc4413b417f392e32096d5167517fcdcb8 is unchanged.
Free space is7,518,609,408 bytes. HTTP remains PID1325435 and peer PID3967036.
AWG/TCP are still stopped and the watcher restart counter is39, not healthy VPN.

| Preserved runtime | SHA256 |
| --- | --- |
| RU node | `125c796a30c3fba1772c47b96963517350087ad04aad675b6f33a31a5383276c` |
| Gateway | `9023d2c3f7c3a5127d67c509a16eb2d974810ff54d5b76cc225cd9b93e0b4234` |
| Effective watcher unit | `659b954beb67d1e23c0cea45ffda62704f48dc2fb0b1f5bd30d0ae733760bd4e` |
| Current metadata HTTP | `4e2df679761ba9e7af74128984ef2e19e8e7b228f1cc85b36d50be2b0bc24ce8` |
| Current paid operator | `19efd0b46fb145dcef06a9a092ee0d8ee4d062d09d99b1b0e0065425be02d90f` |
| Current paid reconciler | `ff4601aa3bb0990b4f8566aadde1fd6b12120bffbd912b4b901e2d77a114d6aa` |
| Unchanged panel image | `5ae92f8c7775d2ff0ad26627f6cdfcda53a3d4193a08b9fe1de1e89f32c432da` |

The qualified recovery driver is adapted only to this current foundation and a new
private evidence/failure-archive location. No old pre-paid archive is installed.
An initial preflight reader used stdlib Python and failed to import RNS before any
fence/stop. Its partial backup/error remain separate, not PASS. Repeating with the
existing accepted `/opt/apps/family_connect/friends-access/venv/bin/python` and a new
snapshot location passes at15:59:24UTC: SQLite integrity/FK checks, equality of all27
table fingerprints and all three exact-runtime paid projections at the same clock.
No dependency or runtime installation is performed to repair that reader.

Fresh canonical backup SHA256:
`7c93fd3234753a5a713bf95a0d8a57b68e0df14536b52783755fe8dd56921eb8`.
The paused state/config/peer backup is retained off-host encrypted with AES-256-GCM:
198,075 bytes, SHA256
`8b6a3594bd47f03aae23324963cfde8589c28cfa996c802585b57df9add92b93`.
Decryption/digest roundtrip passes. Keys, raw identifiers, state and backup contents
remain private; nothing is restored over the live registry.

### Pause, unchanged start and normal renewal

At15:59:59UTC the RU-only command fence is applied with NL command entries unchanged.
The in-flight reconciler drains; grouped watcher/AWG/TCP stop leaves all PID/control
PID0, no relevant jobs and zero gateway handlers. Retained-state validation passes:
66 records and20 existing peers, with no conflicting TCP bindings or state rewrite.

The15:35 first-failure bytes are archived unchanged while stopped, retaining SHA256
950ed783f48bdfc289343abffe5c98b3750901d223233e48caeee8f2334fa2f5. Sequential unchanged
watcher, AWG and TCP start completes16:00:48UTC. The exact original three-node command
map returns, SHA256 d07803df7c82d4dfabd6eb1131d8c9132a1df8f1a84f2103ca33fe13a5d48b11.
No fence remains. HTTP, peer/MESH, panel, support owner and paid reconcile timer are
not restarted. No timeout, guard, BindsTo, engine config or access policy is changed.

| Ordinary strict sample, UTC | Applied records | Actual AWG / TCP | Result |
| --- | --- | --- | --- |
| 16:01:12 |66 |20 /20 | PASS |
| 16:02:27 |66 |20 /20 | PASS |
| 16:03:03 |66 |20 /20 | PASS |
| 16:03:42 |66 |20 /20 | PASS |
| 16:04:18 |66 |20 /20 | PASS |
| 16:04:57 |66 |20 /20 | PASS |

These samples span224.856s, exceed120s and cross the first observed cohort deadline.
The deadline advances1794844983→1794845188 through normal reconciliation. Every
actual peer/user set and binding matches expectations and persisted applied revisions.
PIDs/invocations remain continuous from start: watcher1635653, AWG1635657, TCP1635667;
all NRestarts0. HTTP/peer retain their original processes. No convergence-anchor
replacement or discarded continuity failure is needed in this recovery.

### Preservation and operator readback

Final16:07:01UTC strict engine/continuity readback passes again. All protected
canonical table fingerprints, not just counts, match the fresh baseline:

| Protected domain | Rows | Exact fingerprint |
| --- | --- | --- |
| Devices |66 | unchanged |
| Invitations |121 | unchanged |
| Paid subscriptions / events |1 /4 | unchanged |
| Chat bindings / service senders |53 /1 | unchanged |
| Referral links / claims |19 /59 | unchanged |

Transport identity, membership, revision, terms, identity/access decisions and
prepared state match the paused snapshot; observation/renewal clocks are compared
separately. Effective units and HMAC2 guard files remain equal. Reconciler is an
inactive/success completed oneshot with its timer active/waiting, not failed.
Exact paid108/119/123/125/126-v2 stays on the same accepted bytes.
The final16:12:32UTC readback repeats all these assertions successfully with the
same watcher/AWG/TCP/HTTP/peer processes and no new first-failure record.

At16:05:50UTC existing read-only support IPC works. Original cursor/baseline position4,
baseline time14November12:48:20UTC and excluded count4 remain; baseline hash equals
cursor anchor and source_error is null. The selected existing device has zero jobs.
This is not a full encrypted support-history/global-job comparison or proof of new
notification delivery; no test payment, term operation or message is created.

Normal imports at16:07:41–16:07:52UTC show RU/NL1/NL2 transport status ok with66
records each. RU inventory status ok/66 and subscriptions status ok/66 on HTTP4e2df679
are current; metadata source is ok. NL inventory registry not_collected is its
existing source boundary, not lost canonical rows. The panel image and read-only
generation2 alias mount are unchanged. No stale pre-paid collector pin is restored.

A separate read-only metadata check sees a newer enabled epoch5/sequence104 received
15:56:54UTC, **before** the recovery fence, and matching canonical/panel values. Earlier
epoch4 OFF/tombstone acceptance remains history, not the phone's current state. This
operation does not touch the phone, change consent or identify the actor. Recheck
the intended final consent/country/network state in the metadata task.

### Remaining boundary

The recurring watchdog/latency cause is still open. This is controlled restoration,
not a durable fix, automatic restart policy, new observer or physical client traffic
test. The existing guarded runbook still applies to any new failure. Retain first
failure evidence; never restore an old DB over live events or reactivate the old key.
Public126/catalog9 are not activated; metadata publication/CI/integration remain
separate. No APK, source/audio artifact or release-signing material is changed.
Documentation qualification:6 changed files/864 local links, zero errors; staged
whitespace and known-private-value checks pass. This is the author's own scoped
review, not independent review or a new runtime/full-Android-CI qualification.

## New outage — 16 November15:34UTC

**Historical outcome at15:48UTC: NOT_RECOVERED / CAUSE_OPEN.** The owner reports another
outage during the metadata-release continuation. This section supersedes current-health
inferences from the earlier successful recovery; it does not erase its acceptance.
Only bounded read-only checks are performed. No fence, stop/start, reset-failed,
configuration/timeout change, database restoration or new observer is authorized or
performed by this diagnostic checkpoint.

| Observed at15:43:45UTC | Result |
| --- | --- |
| AWG | failed / timeout / PID0, inactive since15:34:43UTC |
| TCP | inactive / success / PID0, inactive since15:34:36UTC |
| Watcher | transiently active, NRestarts16; restarting is not healthy VPN |
| Paid reconcile | failed / exit1; timer active/waiting |
| HTTP | active/success; accepted archive, separate14:25:14UTC start |
| Public HTTPS |200; beta125 remains advertised |
| Monitor | inventory/metadata IMPORTED15:44:04UTC; not VPN/reconcile acceptance |

A single current journal file yields43 selected records in the bounded15:32–15:36UTC
window. The private original records and failure bytes are retained locally, without
printing request identities, IPs, keys, configuration or message content.

| UTC | Recorded ordering |
| --- | --- |
| 15:34:36.622163–.622307 | Paid reconcile exits; systemd result timeout. |
| 15:34:36.968379 | Watcher watchdog timeout. |
| 15:34:36.969224–.970888 | AWG/TCP stopping; TCP stops. |
| 15:34:43.020721–.031913 | AWG stop-sigterm timeout, failed/timeout, stopped. |
| 15:34:43.050430–.050879 | Watcher exits, failed/watchdog. |
| 15:34:48.080202 onward | Watcher restarts, followed by further exit-code failures. |
| 15:35:08.189397 | Retained failure: register/engine_query/body, COMMAND_FAILED. |

The2,105-byte retained failure has SHA256
`950ed783f48bdfc289343abffe5c98b3750901d223233e48caeee8f2334fa2f5`.
It records CalledProcessError,0.065945s elapsed/8s budget, four calls, no dropped calls.
Its timestamp follows the initial watchdog and engine stops; it is not proof that
registration or persistence initiated the outage. Effective watcher unit SHA256
`659b954beb67d1e23c0cea45ffda62704f48dc2fb0b1f5bd30d0ae733760bd4e`
and gateway SHA256
`9023d2c3f7c3a5127d67c509a16eb2d974810ff54d5b76cc225cd9b93e0b4234`
match the accepted foundation. The later resource sample has7,519,301,632 free bytes
and1,289,424KiB MemAvailable; this does not reconstruct resource conditions at failure.

Metadata work's last short health sample15:33:19UTC still showed the old watcher/AWG/TCP
PIDs active with zero restarts. Candidate nginx syntax checking completes15:38:07UTC,
after the recorded transport failure, without HUP/container restart or live-file
replacement. No new release asset, catalog, paid policy or server runtime is activated
in this interval. The evidence does not establish the cause of the initiating delay.

Public metadata delivery is held. Installed126's completed offline/online revocation
and original-card cleanup remain valid earlier observations; no fresh broad protected-
data equality or restored VPN is claimed. Resume recovery only as the separately
coordinated [guarded procedure](../operators/subscriptions.ru.md), preserving accepted
paid-v2/metadata/HMAC2 and current user data. Do not simply restart the watcher.

## Earlier outcome at12:06UTC: RECOVERED_CAUSE_OPEN

After the read-only diagnosis, the owner explicitly confirmed a separate controlled
RU recovery on the existing runbook, without new runtime code, HMAC2 changes or
subscription/user-data changes. Recovery runs from source documentation checkpoint
26b267625a52781fe1589b15703500b81e5b3786; the dirty primary checkout is untouched.
This is service restoration on accepted bytes, not a permanent watchdog/latency fix.

### Fresh guards, backup and recovery

At11:51:57UTC accepted runtime hashes listed below, effective units, ownership and
private-parent permissions match. Root free space is7.02GiB; MemAvailable1,211,020KiB.
RU/operator generation2 key agreement is checked in-process without exporting keys.
HTTP remains active from11:40:07 and its process/invocation stays unchanged throughout
recovery; no further concurrent HTTP action is observed. Peer service also remains.

A fresh consistent canonical SQLite backup is restored in isolation: integrity,
foreign keys, all27 table fingerprints and exact-runtime paid projections for all
three nodes at the same clock pass. Backup SHA256:
`f3e9240de5939d0c81e3b376f4bd1dbf9e62fae143504f92492a3f4d369e7bd4`.
The pre-start native state/config/peer backup is copied offline with AES-256-GCM;
203,650 encrypted bytes, SHA256:
`8f8da951cb6d208b65ecddcf789a03782051e1110778d5dc0ff82f39b97ced0f`.
Decryption/digest roundtrip passes; key and raw evidence stay in the protected local
contour. No backup is restored over live data.

At11:52:56UTC the RU-only command fence is in place, NL entries are unchanged and
central reconciliation continues. Current work is drained; grouped watcher/AWG/TCP
stop reaches PID0, no jobs and zero gateway handlers. Retained-state validation
passes with66 records/20 peers before startup. The first-failure bytes are preserved
without overwrite. At11:54:45UTC the unchanged watcher, AWG and TCP are started
sequentially; original three-node command-map bytes are restored. No HTTP, peer,
paid-reconciler timer, local support worker or panel restart is issued by recovery.

### Initial continuity failure and separate convergence anchor

The first continuity check **fails**: TCP changes PID after the startup receipt.
That failure and the original receipt remain retained, not relabelled PASS.
The paused cohort deadline was11:54:26UTC, before the11:54:45 start. The ordinary
11:55:12–18 reconciliation renews admission; TCP restarts at11:55:14. Accepted
`Gateway.plan()` excludes expired admission at startup and `apply_serialized()`
restarts TCP when configuration changes. The paused and post-renewal20-client
id/email/flow dictionaries match exactly. The intermediate configuration was not
sampled: no claim of an observed19-client intermediate set is made.

Watcher/AWG/HTTP/peer process and invocation remain unchanged, no new failure record
appears, and subsequent reconciliation applies all three nodes. Only after those
checks a separate post-convergence anchor is recorded. All original continuity,
actual/persisted, identity, protected-data and lease assertions are rerun against
that anchor; none is removed. This is not an unbroken startup or a restart retry.

### Six strict observations and preservation

| UTC | Records / AWG / TCP | Attempt age, seconds | Cohort deadline UTC |
| --- | --- | --- | --- |
| 12:00:31.247 | 66 / 20 / 20 | 1.247 | 12:02:17 |
| 12:01:35.178 | 66 / 20 / 20 | 1.179 | 12:03:25 |
| 12:02:11.968 | 66 / 20 / 20 | 0.968 | 12:03:59 |
| 12:02:48.562 | 66 / 20 / 20 | 1.562 | 12:04:33 |
| 12:03:25.041 | 66 / 20 / 20 | 1.041 | 12:05:07 |
| 12:04:01.731 | 66 / 20 / 20 | 1.731 | 12:05:40 |

The210.483s window crosses the first observed deadline and exceeds120s. All revisions
are applied; actual AWG/TCP sets and TCP bindings match persisted decisions. Watcher,
AWG and TCP remain active with stable processes/invocations and NRestarts0 throughout
this window. Original command map and generation2 files remain unchanged.

Fresh12:06:35UTC preservation readback compares full table fingerprints, not only
historical counts:

| Protected canonical domain | Before | After | Fingerprint |
| --- | --- | --- | --- |
| devices | 66 | 66 | unchanged |
| invites | 121 | 121 | unchanged |
| paid_beta_subscriptions | 1 | 1 | unchanged |
| paid_beta_events | 4 | 4 | unchanged |
| chat_bindings | 53 | 53 | unchanged |
| chat_service_senders | 1 | 1 | unchanged |
| referral_links | 19 | 19 | unchanged |
| referral_claims | 59 | 59 | unchanged |

All66 retained transport identities, membership, terms and prepared state match;
normal renewal/observation timestamps are compared separately, not mistaken for
data loss. Six effective unit definitions are unchanged. Original command-map SHA:
`d07803df7c82d4dfabd6eb1131d8c9132a1df8f1a84f2103ca33fe13a5d48b11`.
Generation2 manifest digest:
`8602e6526ca1ec0e408c99a7ca37aedc4413b417f392e32096d5167517fcdcb8`.
RU/operator active keys agree inside the protected process. Archived first-failure
hash remains83daf777; no replacement failure appears. No old key, database, timeout
or policy is installed. Public125/catalog8 and paid108/119/123/125 are unchanged.

### Support, panel and a separate existing projection gap

Local support worker stays active without restart. Read-only support IPC confirms
cursor4, baseline position4, excluded-events4, original baseline time14November
12:48:20UTC and baseline-position hash equal to cursor anchor; source_error is null.
The selected existing device has no notification jobs. This is not a full encrypted
message-history comparison or global-job-count proof. No test payment, term change,
support message or notification is created; new notification delivery is NOT_OBSERVED.

Panel stays on image5ae92f8c with generation2/manifest8602e652. Normal RU transport
observation12:02:08/import12:02:09 reports ok/66 records on node125c796a; inventory
and metadata imports are fresh. Both NL transport sources report ok/66 records.

However, subscriptions snapshots are **unavailable**, last success15November
13:47:21UTC/66 devices. Structured read of the existing source configuration finds
its expected archive SHA still
`617c7d752a20631d624b301c59142af34f3624483a5d2d5adc2a7c7722dd74b1`,
while installed metadata HTTP is70a924db. The collector rejects that mismatch before
canonical import. This is a pre-existing stale producer pin, not erased subscriptions
or a recovery-induced change. The earlier broad metadata receipt claim of fresh
subscription imports is corrected by this readback. Canonical data/enforcement and
notification cursor remain preserved. No source pin is changed in this RU-only task.
Metadata follow-up must validate provenance, atomically update this exact pin while
preserving other fields/permissions, then verify normal import and fail-closed pins.

### Limits and recovery posture

Root cause remains open: the incident evidence below shows watchdog ordering and
concurrent I/O delay, not causal attribution. No observer, pressure workload, runtime
fix or restart loop is introduced. Physical client traffic and RU/AWG geography are
NOT_RUN here. No phone/network/consent setting changes; no APK or paid126 publication.
There is no active fence left to undo. On a new incident use fresh guarded recovery,
not a stale DB restore or automatic old-key rollback. Metadata release does not
resume automatically from this incident closeout.

Closeout qualification: documentation checker passes6 files/851 links with zero
errors; whitespace and staged secret/raw-identifier checks pass. Review is the
author's own. No new runtime source or full CI qualification is claimed by this
documentation-only change; operational checks are the separate receipts above.

## Historical diagnosis: NOT_RECOVERED / CAUSE_OPEN at11:42UTC

The owner's new report is confirmed by read-only checks at11:32–11:42UTC.
AWG is failed/PID0/result timeout; TCP is inactive/PID0. Watcher is intermittently
active but its restart counter rises335→349; this is not working VPN. Reconciler
fails with exit1 while its timer remains active. No recovery or production mutation
is performed. The preceding release scope expressly excluded repeating RU recovery;
this diagnostic receipt does not silently override that operational boundary.

Primary dirty checkout is untouched. Evidence and bounded original journal/first-
failure bytes are retained privately, not committed. Worktree source at entry is
ba3e93703d407c945350c1187e3738d25a3c9eab; remote feature matches. Remote main remains
53a780d9ccfcdb2c3ec6141a197917190f9be7a5. This is documentation, not a runtime fix.

## Ordering matters

| UTC | Observed event |
| --- | --- |
| 08:12:36.327610 | Systemd records watcher watchdog timeout. |
| 08:12:36.330884–.341113 | AWG/TCP stopping; TCP deactivates and stops. |
| 08:12:41.578648–.585350 | Watcher and AWG stop timeouts; kill actions recorded. |
| 08:12:57.078839–.080652 | Watcher and AWG fail; AWG stop completes. |
| 08:13:02.335036 | Watcher restarts. |
| 08:13:10.462999 | Retained failure: watch/lock/body, TRANSPORT_OPERATION_DEADLINE,8.000265s against8s; one lock stage, no recorded calls. |
| 08:14:45.194377–.543380 | TCP briefly starts and stops again. |
| 11:32:25 | AWG/TCP unavailable; watcher NRestarts335. |
| 11:40 readback | AWG/TCP still unavailable; watcher NRestarts349. |

The retained first-failure file SHA256 is
`83daf7773ed5e6687c11252a3ec71753afbdb4c67de05deb2ddfcc4aeb716fbc`.
Its error occurs **after** the initiating watchdog and transport stops. It does not
identify what delayed the original watcher, the holder of its lock, a persistence
call, or a particular engine query. No weakening of8/12/120s or BindsTo is proposed.

The initial bounded multi-file journal read timed out; a narrower read also timed
out. Reading the single relevant archived journal instead returns61 records for
08:11–08:15:30. The current journal alone has no records for that window. A separate
54-record kernel window08:10–08:16 has no matched OOM/blocked-task/I/O-error markers;
this limited search does not establish that no kernel/resource problem occurred.

## Resource observations, not root-cause proof

The599s sysstat interval ending08:20UTC contains vda await406.32ms, average queue7.78,
CPU iowait18.01%, steal1.75%, I/O full pressure18.51% and memory full pressure6.93%.
The preceding600s interval ending08:10 had await20.40ms, queue0.58 and iowait4.61%.
This supports substantial concurrent I/O delay, not attribution to a process,
storage provider, metadata collection, HMAC rotation or the Android native defect.

At11:32 root has7.02GiB free and uptime exceeds75 days. At11:34 four Python tasks
are in D/folio_wait_bit_common; the subsequent11:36 snapshot has no D-state tasks
or holders on registration.lock/application.lock. These later samples do not
reconstruct the original lock holder or prove a permanent resource recovery.

## Accepted bytes and separate HTTP activity

| Component | SHA256 |
| --- | --- |
| Transport node | `125c796a30c3fba1772c47b96963517350087ad04aad675b6f33a31a5383276c` |
| Gateway | `9023d2c3f7c3a5127d67c509a16eb2d974810ff54d5b76cc225cd9b93e0b4234` |
| Effective watcher unit | `659b954beb67d1e23c0cea45ffda62704f48dc2fb0b1f5bd30d0ae733760bd4e` |
| Serving metadata HTTP | `70a924dbc02c4ebdb15fe2b935f29070bda0a5fa37f140ac2d35765b34500614` |
| Operator archive | `a7c801dba6a09e35c9ca7a6e6d816bbb57bc4f483404d44b5ee7f641e70cac15` |
| Reconciler archive | `40e1d7212b158fa01e4e4a92c0b635a910ae05b8b350840c07629629108b7aeb` |
| Running panel image | `5ae92f8c7775d2ff0ad26627f6cdfcda53a3d4193a08b9fe1de1e89f32c432da` |

HTTP candidate stops/starts at08:54:17–08:54:57, then again at11:39:28–11:40:07
while this read-only check is running. Its configured Restart=no, PartOf/TriggeredBy
empty and current NRestarts0 do not identify who initiated these actions. Hash stays
70a924db; final PID775862 is active. These restarts were not issued by this diagnostic
run. Reconcile concurrent operational activity before any subsequent mutation.

The local panel remains running. Normal monitor receipt11:41:17.954223UTC reports
metadata IMPORTED and production_writes0. This is not proof of VPN, successful
subscription reconciliation or actual notification delivery. No keys, aliases,
identities, messages, canonical data, paid terms, baseline/cursor or phone settings
are changed by this diagnosis. No new full preservation comparison is claimed.

## Historical recovery boundary before owner confirmation

Metadata release/physical acceptance is interrupted. The signed candidate stays
immutable and unpublished; exact paid126 remains unloaded. The independent native
race gate remains open. No observer, pressure workload or automatic recovery loop
is introduced, and no old database or disclosed key is restored.

A separately coordinated RU recovery must use the existing
[guarded procedure](../operators/subscriptions.ru.md): fresh accepted-pin/ownership/
resource readback and consistent backup/isolated restore; RU-only central fence
while NL refresh continues; drain, grouped stop and PID0/no-jobs/zero handlers;
retained-state validation; preserve this failure without overwrite; sequential
unchanged-runtime start; restore the exact command map; several ordinary actual/
persisted readbacks and lease renewal across120s. Do not simply restart the watcher.
If drain/preflight fails, keep the safe fence and diagnose rather than retry-loop.
Recovery preserves generation2 and all current user data; it would not close the
cause of recurring latency or substitute for physical client acceptance.

Initial diagnosis documentation checks:6 changed files/849 links, zero errors; whitespace and staged
secret/raw-device-ID pattern checks pass. Review is the author's own; no runtime
or independent review PASS is claimed by this documentation checkpoint.
