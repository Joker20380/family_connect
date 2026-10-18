# WARM-START-FORMAL-ACCEPTANCE-1

## Result: PARTIAL — deployment stopped by scope review

**FIRST_BLOCKER = SCOPE_VIOLATION_API_BASELINE_MISMATCH.**
**DEPLOYMENT = NOT_RUN. READY_FOR_LIVE = NO. ATTEMPT_CONSUMED = NO for this task.**

The previous functional warm-start remains **PASS_IN_TESTED_SCENARIO**. Its NL
egress, controlled DNS, authenticated client renewal and post-deadline traffic
remain proven. Historical formal acceptance remains PARTIAL. No new live episode
was attempted, so this report does not claim functionality failed or was proved again.

The saved collector diff is observability-only relative to its archived source.
However, the **HTTP companion artifact built from that source is not
observability-only relative to the actual deployed HTTP API**. Shipping it unchanged
would remove existing credential and publisher behavior. The explicit scope-violation
stop condition was applied before any server or owner mutation. The candidate was
not silently rebased and was not deployed under the old acceptance receipts.

## Exact scope violation

The current RU service executes the closed artifact
`/opt/apps/family_connect/friends-access/http-publisher-research74-20261010.pyz`.
Its bytes were copied read-only and all 23 non-directory member hashes verified.
Unchanged neighboring API modules match the archived baseline; the following do not:

| File / contract | Deployed behavior | Saved candidate effect | BEHAVIOUR_CHANGED |
|---|---|---|---|
| `control/friends/restricted.py` | Issued leaf includes issuer AKI; existing clock-skew-aware validity/delivery policy | Omits AKI and reverts validity/issued-at handling | YES |
| `control/friends/readiness_receipts.py` | Existing five-second clock-skew contract for ACK observation | Reverts lower observation bound | YES |
| `deploy/friends/access-api.py` | Chat registration can return configured publisher information | Removes `publisher_configuration` response integration | YES |
| HTTP runtime manifest | Includes both publisher modules | Omits `control/friends/chat_publishers.py` and `provisioning/chat_publishers.py` | YES |

These are existing production differences, **not defects introduced by the collector
hooks themselves**. The archived baseline omitted them before collector work began.
Local exact packaged-byte comparison and four AST contract guards independently
detect their absence. No owner profiles, payloads or secrets were read to establish
this result. It does not require an owner CONNECT or an attempted bad deployment.

The Go gateway candidate was not independently found to contain these API rollbacks;
the unsafe combined deployment is stopped nonetheless. No partial deployment of only
the lease collector was performed.

## Identities and sealed evidence

Protected capsule:
`state-client-build/field65-export16/warm-start-formal-acceptance-1/`.

| Artifact | SHA256 / identity |
|---|---|
| Verified deployed HTTP artifact | `12ca0c72a89ff20c1b3c70a1182a2d5d98d4d78d25e7a079bb4d75bdf34060ed` |
| Rejected locally packaged HTTP candidate | `0f58d22a2011732b9bce9cc1a1be9252229e6d7ad73f972f203bb5e0e74f353e` |
| Preserved collector diff | `0cb0e59da551a2291be0225a8ef885fea6d3a3e1441e9dc09952071387fec22a` |
| Prior local Go collector candidate; not rebuilt/deployed here | `972613a702f1e32a673cebed4cdee3c4dabfd474c44bc14e9c3616734d68a9c1` |
| Current gateway loaded and next | `21f0a0fdc27b50c00ea922f0b716516e2422aedf1b3797369718f7d00070509a` |
| Base source commit | `a4087e000fdbe674b72ede3a6c8822445c87c654` |
| Preserved SIGNAL_READ source delta | `7e7d408670a6ac6afa18e856beb8dcc0ca26a3b6f074e205d4dd25e62d78967b` |
| Prior collector source-tree digest, not a new commit | `c774f04dad946b8500668269aa3ed6b9e33b4319d6fd2afeb377a05880545fab` |
| This capsule `SHA256SUMS`, 4117 files | `1fa405b38105c64f2e1684c7e63f12b3252a396c9f07ba1148b2cf80f77907e1` |

The prior attribution capsule's 4133 entries, historical episode's 1616 entries and
classifier capsule's 122 entries verified before review. The attribution capsule
verified again at closeout. No prior receipt, RESULT, manifest or source patch was
rewritten. Main dirty product worktree was preserved; only documentation is updated
outside this new ignored capsule. No commit, branch, tag, push or public artifact.

Retained outputs include `scope.txt`, `source.diff`, `archived-api-to-deployed.diff`,
`deployed-api-to-candidate.diff`, `receipts/scope-review.json`, the exact source-only
deployed pyz, the explicitly NOT-DEPLOYABLE local pyz, source/baseline copies,
schemas, evaluator, `RESULT.json`, `manifest.json` and snapshots. `scope_review.py`
contains the reproducible source/packaging assertions; it refuses receipt overwrite.

## Fresh read-only gateway preflight

Entry observer snapshot: **19:02:53 UTC, 12 October**. Final observer snapshot:
**19:12:30 UTC**; final NL chain snapshot started **19:12:31 UTC**, RU metadata
snapshot **19:12:41 UTC**. These are bounded snapshots, not the requested ten-minute
post-deployment observation: there was no deployment.

- Gateway active/running, PID **1415977**, InvocationID
  `1613fa1ce16d4ea5a649255ddf76829f`, start **16:52:44 UTC**, NRestarts **0**.
- Loaded/next hashes and argv agree. Existing four-hour duration, three-hour seed
  rotation option, chat services and listener `127.0.0.1:18444` unchanged.
- Observer remains ARMED. Application receipts10 / systemd receipts11, directory
  modes0700 and file modes0600, retention32 each; entry/final records identical.
  No receipt for the current invocation and no new natural fatal receipt observed.
- Directory and RU/NL publication fingerprint:
  `252c3535d2217e5cf5e2e14264625191e19d7b0dd95625c595426e92ca9e4341`.
  Valid until **20:52:44.204501704 UTC**. Existing current-seed-only contract unchanged;
  no new invocation or overlap claim.
- Strict served chain and expected served DER match **PASS**. Limiting observed
  server leaf expiry **20:48:29 UTC**, headroom **5757 seconds** at final NL read.
  Authority/leaf signatures, AKI match, profile directory binding and non-revocation
  pass the existing read-only checks. No client mTLS admission attempted.
- Authority and directory match RU/NL. Entry CRL snapshots matched23473. Final
  sequential reads saw NL23488/RU23489 while the existing background sync continued;
  whole-state atomic equality is **not claimed** for that final pair. No task renewal,
  sync/publication command or server file write occurred.
- RU HTTP service also remained active, PID414703, invocation
  `e9618550d9624ce887a2c392c4eb3e3f`; existing publisher artifact preserved.

No journal query was made; previous TIMEOUT queries were not repeated. SSH reads,
read-only metadata queries and local server-certificate probes are the only remote
actions. No synthetic owner authentication, Telemost room or native startup.

## Acceptance and test accounting

| Requested stage | Result in this task |
|---|---|
| COLLECTOR_DEPLOYMENT | NOT_RUN — SCOPE_VIOLATION |
| GATEWAY_PRELIVE_STABILITY | NOT_RUN after deployment; baseline unchanged in bounded snapshots |
| CACHE_PREPARATION / EXACT_SELECTION | NOT_RUN; phone not accessed |
| TWO_PHASE_OPERATOR_PROTOCOL | NOT_ENTERED; new ACK before arm still mandatory |
| CLIENT_PROVISIONING_BLOCK | Historical PASS preserved; no new gate |
| SERVER_OWNER_ATTRIBUTION / HTTP403_ATTRIBUTION | Historical PARTIAL / ATTRIBUTION_NOT_RETAINED; no new capture |
| TELEMOST_STARTUP / FULL_TUNNEL_EGRESS / DNS_EGRESS | No new test; historical PASS preserved |
| CLIENT_LEASE_RENEWAL / TRAFFIC_AFTER_DEADLINE | Historical PASS preserved |
| SERVER_LEASE_RECEIPT | Historical independent receipt NOT_RETAINED; new collector not deployed |
| UNEXPECTED_CLOSES | No new session test; no new gateway fatal receipt in snapshots |
| GATE_CLEANUP | NOT_NEEDED — gate never armed |
| OWNER_PRESERVATION | No ADB, instrumentation, APK/cache/vault access or lifecycle action |
| FORMAL_ACCEPTANCE / READY_FOR_LIVE | PARTIAL / NO |

Prior sealed HTTP13 / evaluator9 / lease and observer race×3 results remain valid
for their tested archived baseline. They are **not** renamed a differential PASS
against the actual deployed API. Fresh runtime/race suites and Go build were stopped
at the earlier scope gate. No old assertion was modified. The known diagnostic
assertions and busy-wire issue are not addressed or declared fixed.

This task's counters: operator ACK0; physical CONNECT0; manual reconnect0; gate arm0;
blocked operations induced by task0; native attempts0; task-created Telemost sessions0;
lease renewals0; post-deadline requests0; full-phase requests0; controlled restarts0;
new natural fatal receipts0; owner install/instrumentation/refresh0; renewal0.
**Owner-specific server receipt count and unrelated403 count are NOT_COLLECTED,
not zero.** Background traffic was not captured or attributed to this task.

The new authorized attempt remains **unconsumed**. The prior historical attempt's
consumed status is unchanged. No READY/CONNECT instruction was issued; old ACKs were
not reused. Phone's last known VPN OFF / app ON / ChatDeliveryService ON / gate CLEANED
state is historical, not freshly verified. Research84 and owner data were not touched.
Rollback was unnecessary; current binaries/configuration and prior rollback artifacts
remain in place. No cosmetic restart or cleanup of preserved operational receipts.

## One next operation

**Rebase only the preserved collector patch onto the exact deployed HTTP API,
preserving AKI, clock-skew and publisher behavior, and repeat differential acceptance
before any deployment.** No CONNECT or deployment is part of this next source step.

WHITELIST_WARM_START_READY = NO.
WHITELIST_COLD_START_READY = NO.
REAL_RESTRICTED_NETWORK_FIELD = NOT_RUN.
PUBLIC_RELEASE = NOT_RUN.
