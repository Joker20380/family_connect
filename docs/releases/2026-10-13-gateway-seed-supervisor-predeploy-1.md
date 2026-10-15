# GATEWAY-SEED-SUPERVISOR-PREDEPLOY-1 — PARTIAL

**READY_FOR_CONTROLLED_DEPLOYMENT = NO. ATTEMPT_CONSUMED = NO.**

Read-only production readiness and local trigger-boundary checks completed. No candidate
bytes, production configuration, credentials, directory or owner state were changed by
this task. No canary was launched. This is not a supervisor recovery failure.

**FIRST_BLOCKER = SYNTHETIC_IDENTITY_UNAVAILABLE**, as required by the synthetic-identity
gate: permitted prior materials contain disposable independent-trust identities whose
private state was removed, not an available accepted production synthetic grant/profile.
No owner/tester/publisher identity was substituted and no grant was created. This does
not assert that every production database identity was inventoried.

Independent hard gates also remain: expired served gateway certificate; no verified
exact-binary1011 trigger; unknown active restricted-session census; incomplete live
collectors. The accepted historical adapter requires a modified test binary:
**TRIGGER_REQUIRES_NEW_CANDIDATE = YES** for that mechanism. Candidate unchanged.

## Fresh runtime and independent deadlines

Entry read: **2026-10-13 05:20:32.135666 UTC**. Final NL read:
**05:25:20.966439 UTC**; final RU read05:25:23.713524 UTC. These are snapshots, not a
claim that state cannot change after the report.

| Field | Fresh result |
|---|---|
| Gateway state | active/running |
| PID | `1807869` |
| InvocationID | `00d21e8d81a549f0aa9df8a2714f9ea6` |
| NRestarts | `3`, unchanged between snapshots and previous task |
| Process start | 2026-10-13 04:14:19 UTC, systemd07:14:19 MSK |
| Monotonic process start / final sample | 2572578.06s / 2576839.945438269s |
| Process uptime at final sample | 4261.885s (1h11m01.885s) |
| Effective duration / rotation | `--duration 4h` / `--seed-rotate-after 3h` |
| RuntimeMaxUSec / WatchdogUSec | infinity / 0 |
| TimeoutStartUSec / TimeoutStopUSec | 90s / 20s |
| Planned process deadline | approximately08:14:19 UTC; conservative process-start bound |
| PROCESS_LIFETIME_REMAINING | **10138.115s (2h48m58.115s)** |
| Credential limiting expiry | **2026-10-13 00:09:41 UTC**, gateway leaf |
| CREDENTIAL_HEADROOM_REMAINING | **−18939.966s** at final snapshot (already expired) |
| Strict Family chain | **FAIL: CERTIFICATE_EXPIRED**, verify_code10 |
| Served leaf vs profile DER | Exact match by separate certificate-only diagnostic |

The application starts its duration context after initial setup. The monotonic
process-start estimate is deliberately conservative, not a fabricated exact internal
timer reading. No comparison of monotonic clocks across hosts is made.

Normal four-hour exits retained from the preceding task remain **PLANNED_DEADLINE**:
RUN/DEADLINE, fatal=false, exit0. There were **no new application/systemd receipts**
or natural fatal exits in this task. The 27 files match the preceding capsule exactly:
13 application and14 systemd, all protected and within32-per-directory retention.
Schema1 has no universal numeric receipt sequence; the baseline is file-name/hash sets
plus invocation IDs. Observer environment/helper/ExecStopPost are present; no trigger
was generated just to exercise them. No journal queries were made.

## Exact artifacts and current baseline

5,324 sealed entries verified across the accepted supervisor, preceding deployment
readiness and real-provider proof capsules. The accepted feature inventory's API archive
was checked separately. Build, diff, scope, race/security/resource receipts and rollback
artifact were not reconstructed, modified or rerun over the sealed directory.

| Identity | SHA / result |
|---|---|
| Accepted source | `c9d75db6020f9f605e891036cbb9b68cebede708` |
| Accepted gateway candidate | `d6875817cf33fdd85c6ad78a342fc93afd16864293e94a6e5b7136eec5125765` |
| Baseline / current loaded / current next | `21f0a0fdc27b50c00ea922f0b716516e2422aedf1b3797369718f7d00070509a` |
| Current API argv archive | `12ca0c72a89ff20c1b3c70a1182a2d5d98d4d78d25e7a079bb4d75bdf34060ed` |
| API PID / InvocationID / NRestarts | 414703 / `e9618550d9624ce887a2c392c4eb3e3f` / 0 |
| Current directory, NL and RU | `f00b1da7e5720b25944676fab483eeb2350034d477b2fdf4aae3134db5f84920` |
| Safe seed room hash | `46ab82ff03200f237f8a9e9ee101865ea48801f910b28e329eff422f26390ebd` |
| Served leaf DER | `78f2b6bcdba298ab0c2633b976d7d755bb7a64e1bc6ebf639591fac5afe01fb3` |
| Authority DER | `ccb6eb4acf5695c73065953686a5b528e6b06788127971b05d7cfb8c940ac6e1` |

**CANDIDATE_BASELINE_MATCH = PASS** for exact gateway executable and configured API
archive. Python's live imported modules are not independently memory-attested; the
archive is identified from current process argv/cwd and hashed on disk. The API is
excluded from the gateway candidate, not replaced with a stale source archive.

The gateway baseline is a4087e source **plus** its sealed SIGNAL_READ classifier delta.
Narrow1011-only recovery, immutable first cause, generation/dedicated isolation and
unchanged directory/security/wire contracts are preserved in the accepted manifest.
AKI/skew/ACK/publisher API archive matches the protected inventory. No API/provisioning,
lease/admission/revocation/floor behavior was changed. Combined structured collector
deployment is not implied by patch-application compatibility.

Loaded/configured argv agree. Current binary path remains
`friends-restricted/bin/bootstrap-broker-signal-observation-20261012`; listener18444
exists. Unit and each drop-in hashes are preserved in the private snapshots. No new
ports, endpoint, unit, proxy/trust environment or candidate process was created.

## Credentials and publication

Gateway leaf signature, authority SKI→leaf AKI, non-critical AKI, profile/directory binding
and CRL signatures validate. This does **not** overcome leaf expiry. Authority/delegation
expire09:33:59UTC; gateway leaf expired00:09:41UTC. Revision floor remains1; current profile
CRL floor and CRL metadata are recorded without private material or certificates.

Strict server-only TLS verification failed at both reads. A separate diagnostic then
retrieved only served DER without verification to determine which certificate is loaded.
That diagnostic sent **no application payload or client certificate** and is explicitly
not authorization, mTLS admission or chain PASS. It matched the expired profile leaf.

RU/NL directory and authority equality PASS. At entry both CRL snapshots had number24601
and equal DER. At final read NL held24609 and RU24610, both validly signed: aggregate
publication equality is **PARTIAL at those final snapshots**, not falsely asserted PASS.
Existing background publication advanced between reads; this task performed no renewal,
sync, publication operation or repeated polling to manufacture equality.

## Acceptance window

The future runbook derives caps from current systemd20s/90s stop/start, existing
bootstrap120s exchange/45s connect/15s room-create bounds, supervisor45s total recovery,
and user-required two15min observations. Operator/evidence operations have explicit
bounded caps, not protocol/TTL changes.

```
REQUIRED_ACCEPTANCE_WINDOW = 2710 seconds (45m10s), including rollback margin
SAFETY_MARGIN = 180 seconds (3m)
TOTAL_REQUIRED_HEADROOM = 2890 seconds (48m10s)
PROCESS_HEADROOM_SUFFICIENT = YES
CREDENTIAL_HEADROOM_SUFFICIENT = NO
RUNBOOK_HEADROOM_INVALID = NO (process schedule only; credentials still block)
```

From future candidate process startT0, trigger/recovery completion is capped at
**T0+1380s (23min)** and synthetic evidence/cleanup atT0+2580s (43min). This fits4h lifetime
and does not cross3h seed rotation. Preparation and waiting occur before T0; the future
one controlled deployment restart establishes it. No preparatory restart here, no TTL
increase, no renewal here. Full phase table is in capsule `DEPLOYMENT_RUNBOOK.md`.

## Active sessions and synthetic identity

**ACTIVE_REAL_RESTRICTED_SESSIONS = UNKNOWN**, not zero. Current argv enables neither
ownership nor peer evidence output. Production `SeedManager.Handler` exposes only the
authenticated directory GET, not a live holder census. Optional ownership capture has
a15-minute/512-event limit; stale/absent capture cannot prove no current holders.
TCP sockets are not owner/tester/synthetic identity evidence. Active seed exchanges,
rooms/holders and owner/tester subsets consequently remain UNKNOWN. DIRECT chat is not
classified as restricted full-VPN. Require a proven zero-session inventory or agreed
maintenance window before any future restart; no real session was interrupted.

Known synthetic material from the live capability proof used an independent disposable
Family trust and was removed according to sealed local/remote cleanup receipts. Its
known local private directory and all three supervisor fixture directories are absent.
No accepted reference to a currently available production synthetic grant/profile was
found in these scoped materials. Do not infer a research identity from a device name,
copy an owner profile, revive deleted credentials or add a production grant. Production
DB/owner identity/history/contacts were not read for an unbound identity search.

`SYNTHETIC_IDENTITY_READY=NO`: grant/admission/revocation/validity/private custody and
endpoint authorization for an identified permitted participant cannot be verified.
An independently generated canary identity would not prove permission to join production
later. None was created to bypass this gate.

## Trigger proof and canary decision

Historical `Session.RejoinDisconnectUpstream` is compiled under `sameroomfixture`; it
closes its real upstream WebSocket and substitutes Gorilla CloseError1011 in that test
Session's read adapter. It is not an external control usable on the accepted untagged
binary. The production CLI/handler has no equivalent seed-only generation-bound control.

`ProxyFromEnvironment` is present, but an opaque CONNECT proxy cannot inject a1011 frame
inside authenticated TLS. Real local socket EOF/partial frame/TLS close_notify yield
WS_ABNORMAL_CLOSE1006; TCP reset yields CONNECTION_RESET. These do not enter the narrow
supervisor1011 path. TLS-terminating interception would require a separate, unaccepted
provider-trust/configuration/targeting/cleanup contract; no proxy or custom trust root was
installed. Current proxy/trust environment variables are absent. No broad firewall,
RST injection, process kill, context cancel or synthetic classifier call was used as
canary evidence.

The existing adapter approach therefore requires a **new separately accepted candidate**.
There is no claim that all imaginable external mechanisms are impossible; none in the
accepted artifacts satisfies exact process/seed generation/room binding, one-shot nonce,
TTL, root-only access and complete removal. These security properties are **NOT_PROVEN**.

**EXACT_BINARY_CANARY = NOT_RUN.** Creating a real room without a valid identity/trigger
would not establish the requested capability. All canary media/recovery/directory/stream/
old-cache assertions remain NOT_TESTED, not provider FAIL. Historical real-provider and
local supervisor PASS results retain their original boundaries and are not upgraded.

## Collectors, rollback and local validation

Full `COLLECTORS_READY=NO`. Existing safe recovery receipts provide first cause,
generations/attempt/backoff, endpoint/PC readiness and sample/RTP counters. Promotion may
have zero RX; it does not establish exact nonce delivery, same TCP socket or current
holders. A compatible external synthetic client/endpoint and complete generation/resource
correlation are not yet accepted against the exact binary. The old in-process test driver
is not an external production client/collector simply because its tests passed.

Collector field-by-field mapping, strict bounded file collection contract and trigger
security requirements are in `TRIGGER_AND_COLLECTORS.md`. `evaluate.py` indexes bounded
local receipt files and denies YES unless all16 readiness gates are explicit true.
No broad journal query is needed or performed. No historical receipt was modified.

Rollback binary hash matches current loaded/next; unit/drop-in/config identities are
recorded. However **ROLLBACK_READY=NO** for a healthy operational rollback because current
chain is expired. Historical unit reference predates the signal-observation drop-in:
do not overwrite current configuration with it. Future rollback must preserve current
security floors/profile and recover valid chain, not restore old credentials/DB. At most
one authorized rollback after evidence; none now.

Local unchanged-source tests: **162 test PASS events, race×3, zero failures** for actual
Gorilla WS/TLS boundary classification, first-cause immutability/local shutdown and narrow
supervisor classification. These are local loopback tests, **not** a candidate binary
canary or fresh full Pion live acceptance. Five additional readiness/file-boundary tests
PASS, including missing/unknown gates, retention/size/symlink limits and no mutation.
An offline analysis reader was corrected to handle the schema's absent `close_code` for
CONNECTION_RESET; WS1006 assertions remained exact. No production assertion changed.
Full historical suite is not rerun or claimed green; prior baseline issues remain.

## Requested results

| Field | Result |
|---|---|
| CURRENT_INVOCATION | Fresh, unchanged during two bounded snapshots |
| PLANNED_PROCESS_DEADLINE | Approximately08:14:19UTC; PLANNED_DEADLINE not fatal |
| PROCESS_HEADROOM | YES,10138.115s at final read vs2890s required |
| CREDENTIAL_HEADROOM | NO, expired served leaf; strict chain FAIL |
| CANDIDATE_BASELINE_MATCH / CANDIDATE_IDENTITY | PASS / PASS |
| ACTIVE_SESSION_INVENTORY | UNKNOWN, no safe zero assertion |
| SYNTHETIC_IDENTITY_READY | NO — FIRST_BLOCKER |
| TRIGGER_MECHANISM | Accepted adapter needs new candidate; no approved external substitute |
| TRIGGER_SECURITY | NOT_PROVEN |
| EXACT_BINARY_CANARY / CANARY_REAL_TELEMOST | NOT_RUN / NOT_RUN |
| CANARY_WS1011_CLASSIFICATION / CANARY_SUPERVISOR_RECOVERY | NOT_RUN / NOT_RUN |
| CANARY_DIRECTORY_CONTINUITY / CANARY_DEDICATED_CONTINUITY | NOT_TESTED / NOT_TESTED |
| CANARY_OLD_CACHE_BOOTSTRAP | NOT_TESTED |
| COLLECTORS_READY | NO; compatibility/gaps documented |
| ROLLBACK_READY | NO operationally; exact binary artifact PASS |
| DEPLOYMENT_RUNBOOK | Prepared, process budget valid, execution blocked |
| CANARY_CLEANUP | PASS — no canary resources created |
| READY_FOR_CONTROLLED_DEPLOYMENT | **NO** |

## Artifacts and counters

Capsule: `state-client-build/field65-export16/gateway-seed-supervisor-predeploy-1/`.
`manifest.json`, `RESULT.json`, `SHA256SUMS`; safe entry/final NL/RU snapshots, immutable
receipt copies, input/provenance checks, calculated headroom, identity/trigger assessment,
local source-copy manifest, race logs, privacy checks, evaluator/tests and future runbook.
No secrets or raw room URLs/SDP/private identities were exported into receipts. Snapshot
TLS diagnostic did not send application data or a client certificate. Temporary local
test sockets/processes closed; no canary credential/state/rooms/listeners were created.

```
PRODUCTION_GATEWAY_DEPLOYMENT = 0
PRODUCTION_GATEWAY_RESTART = 0
PRODUCTION_RENEWAL = 0
OWNER_INSTALL = 0
OWNER_INSTRUMENTATION = 0
OWNER_REFRESH = 0
OWNER_CONNECT = 0
PROVISIONING_GATE_ARM = 0
CANARY_ROOMS_CREATED = 0
CANARY_DEDICATED_ROOMS_CREATED = 0
CANARY_SIGNALING_DISCONNECTS = 0
CANARY_SUPERVISOR_RECOVERIES = 0
CANARY_PROCESS_RESTARTS = 0
CANARY_STREAM_REOPENS = 0
NATURAL_FATAL_EXITS_DURING_TASK = 0
ATTEMPT_CONSUMED = NO
PUBLIC_RELEASE = NOT_RUN
REAL_RESTRICTED_NETWORK_FIELD = NOT_RUN
```

**Exactly next operation:** a separate **source-only acceptance-trigger candidate with
full local acceptance**, as required when the accepted mechanism needs a compiled hook.
No deployment, new production grant, renewal or owner action is authorized by that next
step. Current c9d75db6 candidate remains unchanged; credentials/identity/session/collector
gates must not be silently waived. Nothing is launched automatically.

Historical FUNCTIONAL_WARM_START=PASS_IN_TESTED_SCENARIO and local
PRODUCTION_PATCH_ACCEPTED=YES remain unchanged. Deployment readiness is a separate gate.
