# 5N-STAGING-TRANSFER-RELIABILITY — 2026-10-02 UTC

**5N-STAGING-TRANSFER-RELIABILITY = FAIL** against the complete requested gate:
the exact historical RU/NL timeout layers cannot be established from retained evidence.
This is **not** a failure of the new transfer: local regressions PASS and both authorized
inert production bundles are READY, independently rehashed after transfer. Do not replace
the missing historical evidence with a network-slowness or timeout-budget assumption.

Starting HEAD: `9b3ec45e83ccb226ec4373087329cfdc218b0fac`.
Implementation: `5b59461af9003204829158ddeed155443bd6b922` (operator-only code/tests/runbook).
Runtime artifacts and their accepted source inventories were not rebuilt or altered.
Documentation is committed separately; this report's containing commit records its revision.

[Sanitized inventories, phase timings and receipts](2026-10-02-5n-staging-transfer-reliability-evidence.json).
[Permanent staging contract](../../deploy/friends/restricted/STAGING.md).
Protected raw observations remain under `state-client-build/staging-transfer-reliability/`,
outside Git. No authority contents, credentials, application DB or device identifiers are published.

## Historical command reconstruction

Both operations used `subprocess.run` around SSH with a complete Python program on stdin,
not scp/rsync/tar. Redacted argv shape:

```text
ssh -o BatchMode=yes -o StrictHostKeyChecking=yes -o UpdateHostKeys=no
    -o ConnectTimeout=10 root@<authorized-role-host>
    env PYTHONDONTWRITEBYTECODE=1
    /opt/apps/family_connect/friends-access/venv/bin/python -
```

The wrapper's single wall-clock timeout included authentication, stdin transmission,
Python source ingestion/parsing, remote work and the final JSON response. There were no
explicit ServerAlive settings, compression flag, connection reuse or phase deadlines.
Inherited SSH compression was not changed or assumed. Each bundle used one connection;
other preparation commands used separate connections.

| Property | RU operator | NL checker/authority command |
|---|---|---|
| Timeout | 45s | 50s |
| Failure timestamp, UTC | 21:08:39.197644 | 21:09:34.485577 |
| Artifact files | 9 | 3 |
| Raw artifact bytes | 7,806,192 | 5,683,055 |
| Entire reconstructed stdin program | 10,410,219 bytes | 7,586,727 bytes |
| Large artifact assignment | 10,409,322-byte FILES line | 7,577,775-byte CHECKER assignment |
| Historical auth completed | Unknown | Unknown |
| Historical remote command began | Unknown | Unknown |
| Transfer progress preserved | No | No |
| Exact historical A–G layer | Unresolved inside opaque SSH subprocess | Unresolved inside opaque SSH subprocess |

NL additionally included a 3,823-byte public signed authority-bundle representation and
remote authority/native-validation logic. Its bytes were measured read-only, not exposed
or renewed. This task stages only its three immutable checker files, **not authority**.

Destination parent, both hosts:
`/opt/apps/family_connect/restricted-materials-stage-20261001/canary-rollout-attempt16-9b3ec45`.
RU subdirectory: `http-operator`; NL subdirectory: `native-checker`.
The evidence JSON lists every exact filename, bytes, hash and safe local source path.
RU sources are accepted scripts/service template, the attempt16 operator and reconstructed
unchanged nginx template, plus the accepted readiness bundle. NL sources are the accepted
attempt13 native checker/provenance bundle. No signing or private-key path is needed.

Timeline correction to the earlier attempt16 narrative: RU staging ended at21:08:39;
RU authority completion was21:08:44, preceding the NL50s command. The two **bulk artifact
transfers did not overlap** on this retained timeline. RU staging overlapped other JIT
preparation, not the later NL bulk transfer. No causal claim about concurrency follows.

## Read-only inspection and localization limits

Before writing, both target subdirectories and all12 expected files were **ABSENT**.
No related partial/temp staging entries were found. There was no stale or wrong-hash
file to repair, overwrite or delete. This observation does not establish how far a
historical SSH process got; attempt16 also retained no completed staging/native receipt.

Bounded read-only SSH journal queries for the failure interval themselves exceeded5s
on both hosts. No historical authentication event was recovered. That is unavailable
evidence, not proof of an authentication failure or an empty journal.

Controlled, mutation-free probes emitted a remote-start marker and observed child
read progress/CPU/wait channel. Both source ingestion and raw streaming were making
progress; short12s probes hit their deliberately short bound. Subsequently the **exact
original public FILES/CHECKER assignments**, replacing mutations with a parse marker,
completed within the original45/50s limits:

| Current no-write probe | RU | NL |
|---|---:|---:|
| Assignment plus harmless marker bytes | 10,409,350 | 7,577,803 |
| Total elapsed | 27.456s | 16.689s |
| Remote receive/parse elapsed | 25.214s | 15.942s |
| Result | PARSED / exit0 | PARSED / exit0 |

These probes do not execute the historical remote staging/validation body and cannot
retroactively rule out any uninstrumented historical phase. They **do not reproduce**
the old timeout. No evidence proves45/50s inherently inadequate, network slowness,
Python parsing as the historical cause, or an RU/NL deadlock.

## Proven reliability defects and minimal correction

The source visibly embedded binary artifacts as base64 literals in multi-megabyte
Python source. Reception/parsing must finish before its first receipt can execute;
payload size expands about4/3. A single TimeoutExpired loses the phase. RU decoded and
checked hashes in memory, wrote directly to final paths with file/directory fsync,
then printed its one completion response. Fsync existed, but there was no quarantined
bundle promotion or durable READY protocol. A partial bundle could occupy final names.

The new stdlib operator `scripts/friends_staging.py` plus isolated receiver fixes those
**proven structural deficiencies**, without claiming a proven historical timeout cause:

- Verify accepted local pins before connecting; send a bounded receiver in the SSH
  command and raw binary stdin, never artifact bytes as executable source.
- Emit CONNECTED before artifact reception; separate connect, transfer, fsync,
  remote hash validation, atomic promotion and receipt phases.
- Hold a per-destination flock; receive into a unique0700 quarantine directory under
  the existing inert parent. Never overwrite an existing destination or failed partial.
- Receive exact lengths, fsync, reread SHA256, verify inventory, atomically rename the
  entire directory, fsync parent, persist READY receipt, then emit READY.
- Missing receipt after complete promotion is PARTIAL/COMPLETE_BUT_UNACCEPTED, not READY.
  Retry uses a new quarantine; already accepted state is reused only after reinspection.
- Persist safe per-item local/remote timestamps, confirmed byte counts, hashes, mode,
  phase durations, promote result, timeout stage and exception class. Fsync local event
  snapshots and remote intent/final receipts; do not log stderr or sensitive payloads.

No production trust/authentication model changed. No staged script/checker was executed.
A later authorized deployment must use the runbook's READY reinspection rather than
the legacy source-literal upload path. Native authority validation is a separate future
operation, not implied by a checksum-valid checker binary.

## Derived bounds and measured live results

Measured short probes showed roughly0.35–0.55MB/s reception; default lower bound is
256KiB/s, with a factor2 transfer margin and5s fixed allowance. For file size `n`:
transfer=`5+2*n/262144`; hash=`5+2*n/(8MiB/s)` (conservative verification floor with margin).
Connect/receiver startup15s (SSH ConnectTimeout10s); keepalive5s/count2; manifest10s;
file fsync5s; final promotion/receipt5s. Local phase slack2s cannot extend the aggregate
absolute deadline. Per-phase cap300s, aggregate transfer/fsync/hash cap600s, overall cap660s.
No progress-reset deadline, unbounded timeout extension or automatic retry was added.

| Live staging, UTC02 October | RU | NL |
|---|---:|---:|
| Start | 21:50:37.339 | 21:55:39.011 |
| Files / bytes | 9 / 7,806,192 | 3 / 5,683,055 |
| Connect + receiver startup | 2.538s | 0.933s |
| Largest file bytes | 7,652,032 | 5,674,189 |
| Largest-file transfer budget | 63.380s | 48.291s |
| Largest-file transfer actual | 13.049s | 11.853s |
| Largest-file fsync actual | 0.050s | 1.160s |
| Largest-file hash actual | 0.071s | 0.050s |
| Aggregate budget | 226.417s | 119.713s |
| Entire invocation actual | 17.858s | 14.332s |
| Final result | READY / exit0 | READY / exit0 |
| Independent read-only reinspection | READY / 2.007s | READY / 0.929s |

All12 remote hashes/sizes/modes and inventory/READY receipts matched. No timeout or
exception occurred. Per-file measurements and exact hashes are in the evidence JSON.
Reported durations are measured within each process; cross-host wall clocks are not
used to derive transfer duration. Sequential live staging needs no timeout attribution
from the historical attempt. Only inert directories, lock files and receipt metadata
were added to production storage.

## Regression, runtime boundary and remaining work

Focused tests: **19 PASS** (`tests/test_friends_staging.py`,1.54s). Covers all requested
A–I: normal/slow success, connect/mid-transfer/validation timeouts, quarantined partial,
hash mismatch, process exit before READY receipt, safe retry/idempotence, simultaneous
attempt isolation. Also local pin failure, unsafe paths/manifests, multi-file framing,
read-only absent inspection and post-READY tampering. Existing control CI includes them.

Broader tests:60 PASS /13 SKIP /2 FAIL in8.40s. The two existing
`test_http_transition.py::test_exact_attempt9_cadence_reproduces_shared_per_ip_limit`
matrix/observer assertions hard-code old HTTP SHA `460e752...` rather than accepted
`ad71cad...`; unrelated and not changed. Task-file source/secret guard and
`git diff --check` PASS. The existing whole-index private-key-PEM test-fixture finding
in `tests/test_readiness_adapter_packaging.py` remains; no whole-repository clean claim.

Before/after service ActiveState/SubState/PID/restart/starttime snapshots match exactly.
Ordinary RU Friends access and RU/NL AWG/TCP remain active, unchanged. RU restricted
sync/candidate and NL bootstrap remain inactive; timer/bootstrap disabled. RU ingress
SHA remains `4426bfa9b589fcca124aed99daaaa9dedcf04cbd2c385a322d9fd92ead925267`.
This is a scoped runtime-state check, not a fresh end-to-end product acceptance or
continuous zero-interruption proof.

No services started, routes enabled, ingress reload, DB migration, authority refresh,
Redmi access, FIELD-1/DIAG-1/OPS-1/beta, runtime deployment or git push. The previously
observed `chat_sequence` change remains unrelated concurrent application activity;
this task did not inspect, restore or modify it. Historical attempt15 cause stays unknown.

Preexisting dirty/untracked work is preserved; only task-owned additions are committed.
The accepted HTTP/readiness/sync artifacts and canary55 are unchanged. Stage5N stays OPEN.
Historical localization remains unresolved, while reliable transfer is now evidenced.
STOP: no full PROV-1 retry. A future explicitly authorized retry must revalidate current
authority and all existing production/product criteria; these READY receipts waive none.
