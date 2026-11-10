# RU recurrence —11 November2026

Status: **RECOVERED_CAUSE_OPEN**. Date is the operator's Brussels calendar date;
incident timestamps below are UTC on10 November. This is an availability recovery,
not a software release, migration, successful user-traffic test or permanent fix.

## Scope and installed state

The owner interrupted SUPPORT-CHAT-1 after another RU outage. The chat worktree
and its unfinished changes were preserved. This report uses a separate branch
from main87fbe744. No additional Android/VPN/G4/transport suites were run.

The latest preceding PR17 deployment was
[DEPLOYMENT_FAILED_ROLLED_BACK_VERIFIED](https://github.com/Joker20380/family_connect/pull/17#issuecomment-6765941574),
not a successful installation of the candidate now present in main.
The installed hashes were checked before and after this recovery:

| Component | SHA256 / value |
| --- | --- |
| RU node archive | `125c796a30c3fba1772c47b96963517350087ad04aad675b6f33a31a5383276c` |
| Gateway | `9023d2c3f7c3a5127d67c509a16eb2d974810ff54d5b76cc225cd9b93e0b4234` |
| Watcher unit | `e9a9d82841d0d5aa257780660107d9588af80a24b32d604dccf9c81c2730523a` |
| Watcher restart policy | `on-failure`, unchanged |
| Central admission policy | `android-paid-108-119-v1`, unchanged |
| Local panel console image | `sha256:c179d1aea89821c9386909d6bfed3face29391e3d8e8e590c2328d7dffc5eead`, unchanged |

No node/unit/HTTP code, source pin, credential, subscription, APK or catalog was
deployed. No action on NL engines, the owner's phone or neighbouring services.
No disk cleanup, volume recreation or database rollback.

## Original failure, not a synthetic explanation

The first record at23:13:41.903 has invocation193f5df0585741b785baf659e5fbda48,
modewatch, phaseengine_query, boundarybody, reasonCOMMAND_TIMEOUT,
exceptionTimeoutExpired. Total elapsed8.363s for an8s operation.

| Recorded call | Duration | Remaining at entry | Result | Parent major faults |
| --- | --- | --- | --- | --- |
| AWG query | 7.608885s | 7.989567s | completed | 9 |
| TCP query | 0.742131s | 0.379196s | timed out | 10 |

The final TCP timeout is not evidence of an independent TCP handler hang: most
of this operation's budget was already spent on the preceding AWG query.
The installed diagnostic version does not split its time into spawn, child work
and output draining. These timings do not identify the exact blocked kernel call.

TCP stopped23:13:43; AWG stopped with timeout/KILL23:13:48. The watcher restarted
repeatedly without restoring the stopped engines:23 restarts at the initial
23:27 observation,30 by23:32. Its active/success status alone was not VPN health.
This is consistent with the previously demonstrated watcher-only lifecycle issue;
reinstalling the previously failed candidate is not an accepted cure.

Read-only sysstat from the existing archive adds historical evidence, rather than
substituting a healthy later sample. Server timestamps are MSK; the following
ten-minute intervals are converted to UTC:

| Interval ending | CPU I/O wait | Swap in/out, pages/s | Major faults/s | vda await | Memory full-pressure interval |
| --- | --- | --- | --- | --- | --- |
| 23:10 | 3.20% | 0.03 / 0.00 | 0.11 | 41.24ms | 0.00% |
| 23:20, contains failure | 15.24% | 31.54 / 50.60 | 32.39 | 148.83ms | 10.35% |
| 23:30:02 | 21.68% | 27.48 / 44.22 | 29.53 | 212.25ms | 16.14% |

This supports shared memory/I/O pressure as a contributor worth isolating. It does
**not** prove a specific workload, OOM, provider defect or uninterrupted pressure
at the exact failure microsecond. The host has2vCPU and1962MiB RAM; swap occupancy
alone is not proof of exhaustion. Bounded first-invocation/kernel journal reads
timed out with no output; no claim that the missing logs contain no errors.

## Recovery and verification

1. Saved the original first-failure bytes and pre-mutation service/configuration,
   policy and protected canonical database fingerprints privately.
2. Atomically fenced only the RU entry of the existing reconciler command map.
   The central timer stayed enabled; NL destinations were not altered.
3. Stopped watcher/AWG/TCP; verified MainPID/ControlPID0, no pending service jobs
   and no remaining gateway handlers. Backed up retained state and peer mappings.
4. Validated the retained state with the installed engine under its ordinary
   lock/operation. No ledger, deny, prepared decision, expiry or cache reset.
   Archived the original failure without overwriting an earlier incident.
5. Sequentially started the same watcher/AWG/TCP bytes. All start operations
   completed23:34:07.633; restored the exact original command map23:34:09.022.

Six samples over196.687s show the same healthy processes, zero new restarts,
no new first-failure file,63 records and20 allowed. Normal watcher committed
strict live AWG/TCP readback remains fresh; persisted full TCP id/email/flow sets
match the decisions. This uses actual normal readback, not config counts alone
or a newly introduced series of production CLI probes. The one cohort lease
crosses its old expiry and is renewed by at least120s.

Post-recovery comparisons pass for canonical devices/invites/subscriptions/events,
operator policy/current, source files, effective units, command maps and metadata.
HTTP and central timer invocations remain unchanged throughout the recovery.
Panel health200 and its normal collector show fresh RU/NL statusok with the
installed hashes; RU observation23:39:26. The panel application was not updated.
No authenticated browser interaction or new end-to-end client traffic was tested
in this incident. A short recovery window is not a long-term stability guarantee.

## Remaining action and rollback boundary

The existing independent-RU qualification package remains **WAITING_FOR_HOST**.
One explicitly authorized independent Linux resource is needed, not another VM
or container on this same overloaded environment. Its existing handoff requests
4vCPU/4GiB/15GiB free for the synthetic fixture, verified host identity and operator
access; these are test-capacity requirements, not a proven production sizing cure.
No purchase, secret discovery, host migration, registration-map/catalog change or
production cutover is authorized by this report. Qualify that resource first and
then handle migration as a separate addressed operation.

Do not retry PR16/17/paid123 deployment, weaken8/12/120s, disable fail-closed checks,
extend deadlines manually or add an unattended restart loop to hide recurrence.
If RU fails again, retain the new first failure and make a separate bounded
recovery decision. There is no code rollback in this operation: no code changed.
Never restore the saved database/state over newer decisions. Only the exact
temporarily fenced command map was restored, with a concurrent-drift guard.

Private evidence/backups stay outside Git under the incident workspace and the
RU private recovery directory. First-failure byte digest:
`1bd6af6bbe4ab9aa81bf85fc6aa9114df80b2ae5e50177efb92adec302809cd0`.
This source checkpoint contains only sanitized documentation; content/links and
whitespace are checked. SUPPORT-CHAT-1 remains incomplete, not installed or accepted.
