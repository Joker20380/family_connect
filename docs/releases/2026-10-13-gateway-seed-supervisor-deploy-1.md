# GATEWAY-SEED-SUPERVISOR-DEPLOY-1 — PARTIAL

**PRELIVE_SERVER_CHANGED. DEPLOYMENT = NOT_RUN. OWNER_CONNECT = NOT_RUN.**

The mandatory entry gate stopped this task before staging, renewal, restart or any
Telemost test. The previously saved invocation has ended. Importantly, the new receipts
show **two normal four-hour duration completions, not another WS1011 or fatal failure**:
`RUN / DEADLINE`, `normal_stop`, `fatal=false`, systemd `exited/0`. Existing `Restart=always`
created successor invocations. This is not a failed supervisor recovery: the candidate
was never loaded. Local supervisor PASS and historical functional warm-start PASS remain.

## Exact candidate and fresh runtime

Authority: `state-client-build/field65-export16/gateway-seed-supervisor-1/manifest.json`.
All 1,239 sealed candidate files, 4,046 real-provider proof files and 52 formal-acceptance-2
files were rehashed: **5,337 checks PASS**. No candidate rebuild or source reconstruction.
The behavior/observability diffs, scope, build/test/resource/security receipts, binary,
rollback binary and historical unit reference match the accepted capsule.

| Identity | Value |
|---|---|
| Accepted source | `c9d75db6020f9f605e891036cbb9b68cebede708` |
| Candidate SHA256 | `d6875817cf33fdd85c6ad78a342fc93afd16864293e94a6e5b7136eec5125765` |
| Baseline SHA256 | `21f0a0fdc27b50c00ea922f0b716516e2422aedf1b3797369718f7d00070509a` |
| Fresh loaded / next SHA256 | Both equal the baseline SHA256 above, **not candidate** |
| Fresh snapshot UTC | `2026-10-13T05:06:15.023150+00:00` |
| Service | `family-connect-restricted-bootstrap.service`, active/running |
| PID / InvocationID | `1807869` / `00d21e8d81a549f0aa9df8a2714f9ea6` |
| Process start UTC | `2026-10-13T04:14:19Z` (systemd reports 07:14:19 MSK) |
| NRestarts | `3`; historical reference was `1` |
| Current directory SHA256 | `f00b1da7e5720b25944676fab483eeb2350034d477b2fdf4aae3134db5f84920` |
| Seed room safe hash | `46ab82ff03200f237f8a9e9ee101865ea48801f910b28e329eff422f26390ebd` |
| Recovery old/new generation | NOT_OBSERVED / NOT_CREATED; no recovery episode |

Loaded and configured argv agree. Executable path is the existing
`friends-restricted/bin/bootstrap-broker-signal-observation-20261012`; effective flags
remain `--duration 4h --chat-services --seed-rotate-after 3h`, the existing profile/export
paths and `--listen 127.0.0.1:18444`. Full safe argv and per-unit/drop-in hashes are in
the private snapshot. Baseline remains a4087e source **plus** its sealed classifier diff,
not bare a4087e. API/issuer/publisher/AKI/skew/ACK files were not deployed or touched.

## UTC chronology and immutable receipt classification

| UTC | Invocation / PID | Evidence and classification |
|---|---|---|
| 2026-10-12 20:13:18 | `4fafa22abf6c4bcbbc137375472855c7` / 1540161 | Previous task's saved successor start; historical reference |
| 2026-10-13 00:13:18.554739708 | same | Application: RUN/DEADLINE, normal_stop, fatal=false, elapsed 14,400,092 ms |
| 00:13:18.626995 | same | Systemd: exited/0, success, exact invocation match; NRestarts=1 |
| 00:13:48 | `90183ec068c34217b4ad4f06518cffb8` / 1677547 | Next start retained in matching systemd receipt |
| 04:13:48.882969966 | same | Application: RUN/DEADLINE, normal_stop, fatal=false, elapsed 14,400,169 ms |
| 04:13:48.985889 | same | Systemd: exited/0, success, exact invocation match; NRestarts=2 |
| 04:14:19 | `00d21e8d81a549f0aa9df8a2714f9ea6` / 1807869 | Current start; fresh NRestarts=3 |
| 05:06:15.023150 | same | Read-only snapshot, identical invocation/state before and after read |

Correlation uses matching application/systemd invocation IDs, not cross-host monotonic
clock comparison. The current `Restart=always`/30s policy and receipts corroborate two
automatic restarts since the reference. **No new natural fatal exit is evidenced.**
Older natural WS1011 and UNKNOWN receipts retain their original classifications.

27 application/systemd receipts were copied byte-for-byte into the new private capsule:
23 previous receipts are byte-identical, four are new (two matched pairs). Source files
were not edited, regenerated or removed. New application receipt hashes:

- `9e25b8fbc6208c9b23954144b51398dd9c467fbe5043e896972abd01323e277a`
- `688a2590b630f37118b244e4a0497bc3edf12b52b25ba0ac2dacb4a17bcfb6ad`

Matching systemd hashes:

- `79f6b3067e06e9d698fac3c473bf5c05dfef9462e76098f66d91279848be0099`
- `06e7f64f5d31ee4dffd87da2c20b3eb24fdf47e53f2413f1c0c7fe887777aefa`

## Preflight boundary and limitations

Read-only listener check found 127.0.0.1:18444. Observer environment and ExecStopPost
are present; receipt directories are 0700, receipts 0600, counts 13 application/14
systemd within each 32-file bound. Helper/unit/drop-in identities were saved. A single
resource sample: 76 FDs, RSS 33,052 kB, seven OS threads. This is **not** 15-minute
stability, active media readiness, goroutine count or proof of a leak-free runtime.

The directory file records validity until 08:14:19.35394087Z (11,284 seconds remaining
at this snapshot). **Directory headroom is not credential/served-chain headroom.**
Receipts contain startup credential snapshots, explicitly not fresh authorization;
their negative headroom is not reused as a current profile/served-chain result.

After PRELIVE_SERVER_CHANGED, credential/strict served-chain/RU-NL equality/API and
active-user-session preflight were not completed. No renewal, TLS/admission probe,
product database read, owner inspection or journal query followed. Active real full-VPN
sessions are **UNKNOWN**, never asserted zero. No maintenance restart was attempted.

Independent offline trigger check: the real-provider proof's
`Session.RejoinDisconnectUpstream` lives in a `sameroomfixture`-tagged test binary and
requires its in-process Session object. The accepted production build explicitly says
`test_adapter_included=false`. That method is not an external control attachable to
the sealed running candidate. No compatible approved production proxy/control was
established. No substitute drop rule, kill, debugger injection, new endpoint or rebuilt
candidate was attempted. Suitable production-admitted synthetic identity was not
inspected after the entry abort; the old isolated proof used separate synthetic trust.

## Requested acceptance fields

| Field | Result |
|---|---|
| CANDIDATE_IDENTITY | PASS; sealed candidate and runtime baseline bytes match |
| CREDENTIAL_PREFLIGHT | ABORTED_NOT_COMPLETE; renewal=0 |
| ACTIVE_USER_SESSION_SAFETY | NOT_CHECKED; no restart/session interference |
| DEPLOYMENT | NOT_RUN — PRELIVE_SERVER_CHANGED |
| POST_DEPLOY_PRESERVATION | NOT_RUN; API and product state untouched |
| PRELIVE_STABILITY | NOT_RUN |
| SYNTHETIC_BASELINE_BOOTSTRAP / DEDICATED_TEST_SESSION | NOT_RUN |
| CONTROLLED_SIGNALING_DISCONNECT | NOT_RUN; exact-binary trigger not established |
| FIRST_CAUSE_RECEIPT | New normal-DEADLINE receipt pairs preserved; no new fatal |
| SEED_SUPERVISOR_RECOVERY | NOT_LIVE_TESTED |
| PROCESS_AND_INVOCATION_CONTINUITY | PRELIVE_SERVER_CHANGED; stable only during snapshot |
| SAME_ROOM_CONTINUITY / PION_MEDIA_RECOVERY | NOT_TESTED |
| RTP_VP8_DATA_AFTER_RECOVERY / DIRECTORY_CONTINUITY | NOT_TESTED |
| EXISTING_DEDICATED_CONTINUITY / OLD_DIRECTORY_NEW_BOOTSTRAP | NOT_TESTED |
| LEASE_CONTINUITY | NOT_LIVE_EXERCISED |
| STALE_CALLBACK_ISOLATION | Sealed local acceptance preserved; no live check |
| RESOURCE_BOUNDS | One read-only sample; live stability not proven |
| SECURITY_FAIL_CLOSED | Sealed local acceptance preserved; no live negatives |
| POST_RECOVERY_STABILITY | NOT_RUN |
| CLEANUP | PASS — no remote test resources created |
| ROLLBACK_STATE | NOT_NEEDED; unchanged baseline loaded/next; sealed rollback verified |
| OWNER_UNCHANGED | No actions or lifecycle probes; current phone state NOT_OBSERVED |

No directory before/after recovery comparison exists: current directory above is an
entry snapshot only. No new seed generation, test media, lease or TCP continuity is
claimed. The candidate's local acceptance and known unchanged baseline suite failures
were verified by their sealed receipts, not rerun or described as a green full suite.

## Counters, artifacts and next operation

| Counter | Value |
|---|---|
| Controlled gateway restarts / deployments / renewal | 0 / 0 / 0 |
| New natural fatal exits since historical reference | 0 |
| Normal deadline exits / automatic restarts since reference | 2 / 2 (predate this task's snapshot) |
| Test signaling disconnects / supervisor attempts by task | 0 / 0 |
| Seed rooms / dedicated rooms created by task | 0 / 0 |
| Process restarts caused by task / test TCP stream reopens | 0 / 0 |
| Owner install / instrumentation / refresh / CONNECT / TUN | 0 / 0 / 0 / 0 / 0 |
| Provisioning gate arm / live Telemost test sessions | 0 / 0 |

Production service startups created successor seed state independently; task room-count
zeros do not assert no background rooms or user sessions. `ATTEMPT_CONSUMED=NO`.

New capsule: `state-client-build/field65-export16/gateway-seed-supervisor-deploy-1/`:
`RESULT.json`, `manifest.json`, `SHA256SUMS`, verification/classification/trigger receipts,
fresh read-only snapshot, exact original receipts and auditable read-only collection
scripts. Main dirty tree and all prior evidence preserved. No Git commit/push/tag/release.

**Human result:** live acceptance was not run. First established stop boundary is a
changed invocation after normal scheduled duration completion, not a supervisor product
failure. No new WS1011 is inferred.

**Exactly next operation:** a separate predeployment-readiness gate for the current
invocation, with an approved production-admitted synthetic identity and verified
exact-binary seed-only trigger established before any restart. Do not execute automatically.

```
PRODUCTION_PATCH_ACCEPTED = YES (local result preserved)
FUNCTIONAL_WARM_START = PASS_IN_TESTED_SCENARIO (historical, preserved)
READY_FOR_FINAL_WARM_START_PREFLIGHT = NO
WHITELIST_WARM_START_READY = NO
PUBLIC_RELEASE = NOT_RUN
REAL_RESTRICTED_NETWORK_FIELD = NOT_RUN
```
