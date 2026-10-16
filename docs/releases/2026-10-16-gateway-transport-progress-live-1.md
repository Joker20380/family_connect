# GATEWAY-TRANSPORT-PROGRESS-LIVE-1

## Result and acceptance boundaries

**RESULT: GATEWAY_CANDIDATE_DEPLOYED_AND_READINESS_VERIFIED.**
GATEWAY_DEPLOYMENT=PASS; LIVE_GATEWAY_READINESS=PASS_BOUNDED;
NEW_PAIR_DEVICE_ACCEPTANCE=NOT_RUN. This is not FULL_PRODUCTION_ACCEPTED.
Candidate remains running. No executable rollback was needed.

Input review: `12e71d72013e0f6ed4d0d599983d10cd7892a546`.
[Safe selected receipts](evidence/2026-10-16-gateway-transport-progress-live-1.json),
[local acceptance](2026-10-16-gateway-transport-progress-burst-candidate-1.md),
[rollout contract](../../research/gateway-transport-progress-20261016/RUNBOOK.md),
[source manifest](../../research/gateway-transport-progress-20261016/source-manifest.json).
The publication commit records this operation; it is not a new binary source commit.

Only the NL restricted gateway executable changed. Management modules, unit/argv,
configuration and security policy were not changed by this task. Phone untouched.
Normal gateway provider/seed/directory activity occurred; provider activity is not zero.

## Artifact and preserved local acceptance

| Identity | Value |
| --- | --- |
| Candidate executable, configured and loaded | `a537257162348afc35b1ebc08755d8c5dc1cd90e74c49e3987fb3eb81885e61f` |
| Candidate source inventory, NOT Git SHA | `722746429539a1307d693ce6fcc83579a842d3f1c549a626a36676a6d665c42e` |
| Preserved baseline executable | `21f0a0fdc27b50c00ea922f0b716516e2422aedf1b3797369718f7d00070509a` |
| Unchanged C_NEW unsigned APK | `cc5b883395c59d2f76f4cf8ce1d787fa764c1fac2936c9148f9876697d2c5013` |
| Unchanged C_NEW native, also verified inside APK | `253e0e15f38223288571d3e682f6876269aa9c6d1c0c5157588ed8287ba6f3a3` |

The existing 17,711,831-byte candidate from its saved build receipt was used without
rebuild. Linux/amd64, Go1.26.1, CGO=1, ordinary tags, no test adapters or research flags.
Host is x86_64 / glibc2.43; recorded candidate requirements reach GLIBC_2.34 with the
normal loader. No ABI/build-class substitution. The baseline backup was checked both
locally and on NL before any stop; new candidate transfer was independently hashed.

Previously accepted C_NEW/G_CANDIDATE supported8/16/19/20 and stress40, both directions,
normal/Family-TLS and fixed normal/race/multicore checks are retained, not rerun.
Ordinary C_INSTALLED/G_CANDIDATE normal/Family-TLS/8/16/reconnect compatibility remains
PASS. Old installed-client queue16 and synchronous-writer limits remain: larger inbound
bursts and the separately characterized outbound stall are not fixed remotely.

Seven-package baseline/candidate suites remain **non-green**. Same-mode comparison
found no candidate-only failing subtests in that checked set; inherited auth/seed
classifier, race busy-exchange/Mux deadline and timestamp-fixture outcomes remain in
prior receipts. No full-suite PASS, assertion changes or live stress on old clients.

## Interruption, guard abort and fresh applicability

Initial read-only preflight on15Oct23:06–23:09UTC found the expected baseline, valid
served chain, seed event and current materials. Candidate and baseline were privately
staged. The first control-channel attempt on15Oct23:13:01UTC acquired the existing RU
locks, but the NL active-state guard failed **before intent, stop, replacement or start**.

Retained application/systemd receipts establish a natural **baseline** exit at
15Oct23:12:52.655923011UTC: SEED_READ / PUBLISHER_DISCONNECTED, fatal returned_error,
cleanup_started/completed=true; systemd exit1. This predates any candidate execution.
It is not a candidate startup failure and does not establish the underlying provider
cause. The control-channel exception and primary baseline receipts were preserved.

After the connection interruption,16Oct08:06UTC durable readback found only the original
stage/backup receipts: no deploy-intent/stopped/replaced/started result. Configured and
loaded bytes were still baseline. No blind replay, repeated start or rollback occurred.
A distinct fresh pretransition receipt was made, retaining the original snapshot.

Fresh preflight found a naturally renewed baseline invocation
`4cbbbb70f5854ec19295b01705ac630c`, active since06:12:57UTC, matching baseline bytes,
strict served TLS and its06:13:00.670757UTC seed event. Directory matched RU and passed
existing scope/binding validation. Last coordinator transaction was COMMITTED; both
node owner markers absent. Existing evaluate returned NOOP, no writes/restarts.

CRL27098 in the pre-interruption snapshot had naturally advanced to27101, with new
leaf/runtime/directory. Authority/grants remained unchanged. These background changes
were not undone or attributed to this task. No credential renewal/recovery was invoked.
Fresh security prerequisites covered the controlled start, bounded readiness,
120-second observation and the prepared one-shot rollback within existing stop/start
bounds; no future renewal was counted as already completed.

Real restricted session/holder count remained **UNKNOWN**: no live holder inventory
endpoint exists; socket counts and PID do not prove no users. The user-approved
maintenance interval explicitly covered restricted sessions interrupted by this gateway
transition. No old-client burst, owner session or canary was generated.

## Executable-only controlled transition

Existing stop → same-filesystem atomic replacement → start procedure was used, with
existing RU coordinator/node and NL node operation locks. Current4h stayed enabled and
active: no timer stop, schedule change, writer kill or new ownership marker. Locks were
held briefly, not during readiness observation or the earlier connection interruption.
Under locks, pending owners/COMMITTED state, idle renewal service, known executable,
current invocation, unchanged profile and exact unit/argv were checked again.

The exact executable path remains
`/opt/apps/family_connect/friends-restricted/bin/bootstrap-broker-signal-observation-20261012`.
Its historical filename is not the code identity. Staged replacement preserved owner,
group and0750 mode; file fsync, atomic rename and directory fsync preceded start.
No daemon-reload, unit edits, new environment, supervisor flag or management deployment.

| Transition event | UTC on16Oct2026 |
| --- | --- |
| RU locks acquired | 08:22:21.968279 |
| NL replacement verified / locks held | 08:22:22.537841 |
| Durable transition intent | 08:22:22.548231 |
| Stop completed, exit0 / PID0 | 08:22:22.667760 |
| Atomic replacement recorded | 08:22:22.708819 |
| Start completed, exit0 | 08:22:22.773725 |
| Loaded executable verified | 08:22:22.830413 |
| NL / RU locks released | 08:22:22.832090 / 08:22:22.874067 |
| New seed READY | 08:22:25.762125 |

Exactly one task-issued service stop/start and one executable replacement occurred.
The earlier guard abort consumed no transition. No restart-until-green. Baseline backup,
original/new metadata and rollback commands remain private; rollback was not executed.
No credential, CRL/floor, grant or old-directory restoration was attempted.

## Live candidate readiness

| Gate | Actual observation |
| --- | --- |
| PID / invocation | `251251` / `f58c3d9428864605adce61854d08b86d` |
| Configured and `/proc/PID/exe` | Exact candidate SHA256 above |
| Unit / argv | Unchanged;4h duration, existing chat services/3h seed rotation; no research flag |
| Listener | Existing loopback18444 present |
| Seed | Real bootstrap_seed_ready event bound to this invocation |
| Served TLS | VERIFY_X509_STRICT + hostname + TLS1.3 minimum PASS; actual leaf DER equals current expected leaf |
| Leaf signature / revocation | Existing collector PASS, expected key/issuer binding retained |
| New directory issued | 08:22:25.759283692UTC, after current start, alongside its seed event |
| Directory SHA256 | `3b40b1f52ffcf04a6005d3f3613fb9c8ae6cc8f650d74683e2662bc307f663fc` |
| Directory / RU | Existing scope validation PASS; NL/RU identical current publication through ordinary directory-sync |
| Pending recovery | None observed; COMMITTED coordinator, both node owners absent |

Matching directory hashes are publication/readback evidence, not a distributed atomicity
claim. No old directory was copied. Served TLS covers the server chain/hostname/leaf,
not owner mTLS, application admission, Android TUN/DNS/HTTPS, borrowing or live bursts.
No device request was initiated.

## Fixed observation and resources

One interval: **08:23:47.488293–08:25:47.488362UTC**,120.000069seconds.
Active/running, PID/invocation and NRestarts0 remained unchanged. No new application
fatal or systemd terminal receipt for this invocation. Bounded same-invocation
fatal/panic/OOM/failed journal query returned no matches (exit1, empty stderr).
No automatic candidate restart was observed. These are bounded observations, not
long-term autonomy, full production load acceptance or proof of absence of every error.

| Point sample | 08:22:49.686887UTC | 08:26:36.193499UTC |
| --- | --- | --- |
| VmRSS / VmHWM | 22,984 /22,984kB | 23,224 /23,224kB |
| cgroup memory.current | 11,767,808bytes | 28,327,936bytes |
| cgroup memory.peak | 11,919,360bytes | 28,585,984bytes |
| Threads / pids.current | 7 /7 | 7 /7 |
| memory.events OOM / OOM kill | 0 /0 | 0 /0 |
| Existing memory.max / pids.max | max /357 | max /357 |

These samples bracket the interval but are not continuous RSS or a filled-queue test.
Memory accounting categories differ; the changes are not presented as a leak diagnosis
or an improvement over baseline with different uptime/workload. No resource limit was
added or loosened. Local receive64/pending34/writer bounds and retained-reference limits
remain in the prior resource contract; broker32 is not an aggregate process/RSS cap.

## Final current4h, security and absolute UTC bounds

Final security/runtime collectors completed08:26:37UTC; final read-only evaluate
completed **08:27:17.655502UTC**. Result NOOP, due=[], files_changed0, remote_writes0,
restarts0. Alerts CRL_T_MINUS_120M / LEAF_T_MINUS_120M were retained, not suppressed.
Timer enabled/active/waiting; renewal service inactive/success/exit0. RU HTTP/readers and
directory timer active. Legacy restricted-sync remains disabled/inactive as before.

The actual08:13 scheduled result was separately read from the active system journal:
NOOP, same time-window alerts, no changes or restart. No scheduled run was observed
inside the120-second interval. A NOOP or active timer is **not** a completed renewal.
Future runs were not awaited or manually triggered. Read-only evaluate is not a writer.

| Boundary | Absolute UTC |
| --- | --- |
| Final check | 2026-10-16 08:27:17.655502 |
| Authority / earliest current grant expiry | 2026-10-16 17:34:58 |
| Leaf expiry / CRL nextUpdate | **2026-10-16 10:12:45** |
| New directory expiry | 2026-10-16 12:22:22.809417585 |
| Conservative process-start lifetime boundary | 2026-10-16 12:22:22.735879 |
| Next current4h run estimated at final timer read | 2026-10-16 08:28:26.833654, subject to timer accuracy |
| Existing leaf/CRL renewal threshold | 2026-10-16 08:42:45 |
| Next mandatory operator-maintenance threshold | **2026-10-16 11:34:58** |
| Earliest observed device boundary | **2026-10-16 10:12:45**, leaf/CRL |
| Latest CONNECT to fit18minutes at unchanged bounds | 2026-10-16 09:54:45 |

At final check6327.34seconds remained:18minutes plus5247.34seconds of remaining
preparation allowance. **READY_FOR_NEW_CLIENT_TRIAL_AT_CHECK=YES, SERVER_PREREQUISITES_ONLY.**
This is not a promise about later state or owner availability. Freshness must be checked
again before a separately authorized client step. Current4h maintains leaf/CRL within
its policy; daily authority/grant operator work remains required. No TTL migration,
autonomous authority signing or new alerting was introduced.

## Scope accounting, preservation and limitations

- Executable uploads1, controlled stops1, starts1, replacements1; rollback0.
- Pretransition guard abort1 before any mutation; no hidden service-control retry.
- Management/config/unit/environment changes0; manual credential operations0;
  current4h stop/schedule changes0; unrelated service restarts0; fault triggers0.
- Gateway normal seed/provider and directory operations did occur. Background renewal
  between original and resumed preflight changed leaf/CRL/runtime, not authority/grants.
- Management source hashes, node/controller configs and captured unit files matched
  before/after the resumed operation on both nodes. Profile/authority/CRL/grants/floors
  were unchanged across the actual transition/final readbacks; CRL27101, policy floors
  minimum_crl27088 and minimum_revision1 retained, not confused with current sequence.
- ADB, owner CONNECT/export, client rebuild/sign/install, canary identities and release0.
  C_NEW APK/native hashes rechecked locally; installed client was not accessed or changed.
- Original dirty worktree and archived source/build/report material preserved. No mixed
  matrix, server suites, APK builds or historical owner-evidence audits repeated.

Collector limitations are explicit: the old transition-window journal returned no rows,
but retained per-invocation fatal receipts establish the baseline failure. An active-file
query missed the pre-resume seed; a scoped all-journal query recovered it. The scheduled
all-journal query timed out; the active-file query recovered that same bounded interval.
Two local wrapper quoting errors occurred before remote execution and were corrected;
they did not execute service control or alter product code. Private raw failures retained.

Safe JSON is an allowlisted projection with hashes of supporting private receipts, not
raw owner data, profiles, keys, rooms or production grant lists. Private capsule and
protected NL staging contain the exact backup, artifacts and full operation receipts;
those local/server paths are not presented as publicly readable evidence. Only this
report, safe receipt, STATUS/PLAN/publication index are published; no binaries/APK.

Candidate remains active. The intermediate G_CANDIDATE/C_INSTALLED state retains known
old-client limitations. Next: separately authorized short environment/owner check,
existing C_NEW signing/replace-install workflow, then bounded new-pair reconnect/device
acceptance. No rebuild is needed and none of those client steps runs automatically.

Previous single smoke PASS and latest reconnect FAIL remain unchanged.
HISTORICAL_B_CAUSAL_BINDING=NOT_PROVEN. Supervisor acceptance remains unclosed.
