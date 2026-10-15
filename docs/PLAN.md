# Рабочий план / Working plan

Local storage follow-up07.10: preserve old-path symlinks for migrated data; moving
the remaining active project tree/Codex requires a separate maintenance session
after writers stop. Do not migrate live Docker databases or MicroTrader services.
Verify reboot automount separately; no engineering release gate changes.
[Migration receipt](releases/2026-10-07-local-storage-migration.md).

## Current engineering priority / Текущий critical path

### OWNER-SUPPORT-EXPORT-AND-TRIAGE-1 — terminal EVIDENCE_RECOVERED (15.10)

- Read the [completed support-export triage](releases/2026-10-15-owner-support-export-and-triage-1.md):
  matching C1/I1 startup failed at HELLO_RECEIVE before descriptor/dedicated startup;
  source-gated non-entry into native attach is now proven. Cause remains UNKNOWN.
- Keep ring/incident distinct: incident READY versus later FETCH_FAILED; preserve
  missing counters as NOT_RECORDED, not zero, and raw JSONL as NOT_EXPORTED.
- Do not require an unissued session tag to recognize this early failure. Directory
  hash matches saved context but is not a unique server-session binding; S1 stays unbound.
- Export retrieval/triage is complete. Do not repeat export, broad search, run-as/cat,
  sealed audit or empty journal query. Raw payload and alias mapping remain private.
- Production FAIL and root cause NOT_PROVEN remain; this is not candidate-regression
  proof or DNS-only defect evidence. Await a separately authorized next task; do not
  start CONNECT, A/B/C, product patches/builds, deployment or recovery acceptance.

### OWNER-EPISODE-RETAINED-DIAGNOSTICS-1 — terminal ACCESS_BLOCKED (15.10)

- Read the [retained-diagnostics result](releases/2026-10-15-owner-episode-retained-diagnostics-1.md)
  and updated [publication index](releases/2026-10-15-supervisor-publication-index.md)
  before deciding a separate next task. No new engineering work is authorized here.
- Retained local sources yielded no matching owner-native diagnostic record;
  ordinary ADB app-private access is denied. Exact installed research84 is confirmed.
- Do not use the existing export UI under the no-deletion constraint: exact source
  deletes earlier exports and does not export restricted-evidence.jsonl.
- Historical invocation journal returned no rows; neither missing events nor
  rotation is proven. Dedicated READY/session binding/counters/first failure remain
  unresolved; root cause NOT_PROVEN and production acceptance FAIL are preserved.
- Retrieval is stopped; do not repeat this evidence audit or automatically begin
  CONNECT, EXACT-LOCAL-TESTABILITY, A/B/C, recovery, patch/build or deployment.
- Keep raw supplemental evidence private; publish only the report and these
  documentation pointers. No changes to main, workflows or frozen snapshots.

### PUBLISH-SUPERVISOR-RESEARCH-STATE-1 — reading branch, no engineering continuation (15.10)

- Publish already completed reports and exact source-file snapshots on
  `review/supervisor-state-20261015`; publication source commit
  b896f63da15e1ae6b8eef35aadcba1090d6c8baf is not a frozen/accepted candidate SHA.
- Read the [publication index](releases/2026-10-15-supervisor-publication-index.md)
  and retained FAIL/PARTIAL before deciding any next engineering task.
- Do not resume EXACT-LOCAL-TESTABILITY, A/B/C, diagnostics or production acceptance.
  No product patches, binaries, new credentials, owner actions or release in this task.
- Frozen commit objects and raw evidence remain local; published source snapshots
  and small result projections do not manufacture missing owner READY/packet evidence.

### SUPERVISOR-CANDIDATE-DATAPLANE-ROOTCAUSE-1 — terminal PARTIAL (15.10)

- Bounded offline analysis stopped at
  **EVIDENCE_INSUFFICIENT_AT_OWNER_DEDICATED_SESSION_READY**; production acceptance
  remains FAIL, not a demonstrated DNS defect or supervisor-recovery failure.
- Full Android TUN is created by AutomaticVpnOwner before dedicated readiness.
  Saved system VPN CONNECTED is not an orchestrator transition. The sole server
  tag lacks an owner/native binding; absent packet/DNS/TCP receipts are not zeros.
- Exact hashes and1,899 sealed entries verified;221/226 inherited carrier files
  unchanged. Preserve the CGO1→0 build difference and flag-on pre-trigger signaling
  bridge as untested differences, not proven causes or exonerations.
- A/B/C exact-binary matrix NOT_RUN: accepted local Pion fixture recompiles an
  overlay. Do not substitute its historical PASS for immutable-executable DNS/HTTPS.
  No new helper/adapter, live provider action or source modification in this task.
- Patch gate CLOSED; no new candidate/freeze. Reconsider only with already-saved
  owner-bound native READY/packet evidence and an accepted exact-binary isolated
  route. Missing evidence does not authorize owner instrumentation/CONNECT, gateway
  restart/deploy, credential work, Android changes or a PKI follow-up here.
- Historical rollback restored21f0a0fd…70509a once; this task changes no production
  state. Existing CRL/design work below is not implicitly resumed by this stop.
  [Terminal report and precise unproved boundary](releases/2026-10-15-supervisor-candidate-dataplane-rootcause-1.md).

### CRL-COMMIT-READ-BARRIER-1 — PARTIAL / coordination and frozen-reader gates (13.10)

- Exact source and executable show frozen53beb661…5138f has local profile reload
  but no common barrier/durable epoch. Restored old N authenticates after revoked
  N+1 was rejected. Frozen gateway not changed or rebuilt.
- **Exactly next operation:** separate coordination/commit-ledger design acceptance,
  including fresh authoritative decisions, durable antirollback, old-effect fencing
  and complete reader membership. A signed copied head alone is not sufficient.
- Gateway semantic rebase with read-barrier support is independently required after
  that contract; exact file/function delta plan retained, not implemented implicitly.
  Preserve supervisor/trigger/lease/security acceptance in any future candidate.
- 38 cryptographic model tests×3 PASS, not real distributed RPC/crash/fencing proof.
  Existing readers cannot enforce the model; full deployed-fleet inventory still open.
  CRL writer deployment readiness NO; canary policy continuation NO. No production,
  owner or live action; no accepted source candidate/validation commit.
  [Results, consistency definitions and limits](releases/2026-10-13-crl-commit-read-barrier-1.md).

### CRL-WRITER-SAFETY-1 — PARTIAL / distributed commit boundary (13.10)

- Exact source and baseline defect resolved; key mismatch now fails before active
  mutation and before NL request.30 focused tests×3 and frozen TLS probe pass locally.
- **Exactly next operation:** source-only RU/NL committed-state publication and
  reader-barrier design with fault acceptance. Current independent RU/NL switches
  expose a valid-but-divergent N+1/N interval on NL promote failure. Rollforward is
  not global atomic visibility. Do not mark writer accepted from key preflight alone.
- Experimental54c9715c…b61b archive/source retained, not accepted, not deployed;
  validation commit deferred until full PASS. Frozen supervisor unchanged.
- No canary-policy implementation, production identity, CRL write, renewal, restart,
  owner or live action follows this PARTIAL. Full suite/external Store not claimed.
  [Evidence, transaction contract and remaining boundary](releases/2026-10-13-crl-writer-safety-1.md).

### CRL-WRITER-PROVENANCE-1 — source resolved / safety gate FAIL (13.10)

- Deployed RU/NL writer9faaa1c2…64d1 is EXACT: configured archive, historical build/
  deployment hashes and byte-reproducible twelve-member source closure. The earlier
  unresolved-provenance gate below is superseded, not a reason to repeat discovery.
- Tracked non-activated device revoke works and frozen gateway TLS rejects it; unchanged
  grant reconciliation also revokes it automatically. Untracked issuance is not a workaround.
  Narrow revocation support does not accept the pending canary lifecycle/policy.
- **Exactly next operation:** separate source-only CRL-writer safety acceptance, starting
  with issuer-key validation before CRL mutation. Retained exact-code fixture publishes
  invalidly signed RU CRL for wrong configured key; NL rejects it. Do not fix/deploy implicitly.
- 19 characterization tests×3, frozen TLS and local API chat negatives PASS; full security
  acceptance FAIL, external Store/mailbox and full seed/Mux/lease remain untested here.
  No production identity, CRL write, restart, renewal, canary or owner action authorized by
  this result. Frozen supervisor bytes remain unchanged; policy candidate not created.
  [Exact source, failure evidence and next gate](releases/2026-10-13-crl-writer-provenance-1.md).

### RESTRICTED-CANARY-IDENTITY-POLICY-1 — PARTIAL / source gate (13.10)

- First unclosed boundary: exact **deployed revocation/CRL writer** source/provenance;
  the verified HTTP archive does not contain that writer. Do not use an old checkout
  as deployed authority source or issue a certificate outside tracked revocation.
- Exactly next operation: recover/verify its deployment capsule and import closure,
  then resume the source-only restricted-canary policy task. No production grant,
  credential staging, live canary or deployment follows this PARTIAL automatically.
- Local progress:10056 hash checks;23 API checks;10 exact frozen executable TLS checks;
  6 evidence-evaluator tests PASS. Full seed/dedicated/Mux/DNS/lease and external
  Store/mailbox negatives NOT_RUN. TLS-only compatibility does not satisfy acceptance.
- Policy draft: separate operator namespace, unchanged four-claim Family wire role,
  permanent reservation against ordinary activation, existing CRL integration.
  Frozen broker's one-holder-per-identity and absence of per-run quota enforcement
  remain explicit constraints, not silently relaxed. No product candidate created.
- Frozen gateway/source preserved; production/owner/live counters0. Historical
  functional warm-start and local supervisor acceptance remain unchanged.
  [Evidence and exact boundary](releases/2026-10-13-restricted-canary-identity-policy-1.md).

### Operational follow-up — VPN audit15.10 (earlier snapshots retained below)

- Latest06:14UTC:41/37 devices unchanged;NL4 recent handshakes/RU0;AWG/TCP active.
  RU disk4.30%/await4.68ms,worker still unhealthy. No E2E acceptance.
- Restricted active since04:47:47UTC, but overnight03:36:55 fatal
  SEED_READ/HEARTBEAT_WRITE confirmed. Investigate stability without attributing to4008.
- Monitor internal CRL08:32:34UTC,leaf08:47:36UTC,issuer11:01:34UTC15.10;
  expiry checks unchanged. No renewal/restart/deployment authorized by this read-only audit.
  [Latest report](releases/2026-10-15-vpn-health.ru.md).

- Evening18:44UTC supersedes morning failed state: NL restricted active since18:31:23,
  NRestarts0,leaf renewed through20:16:06UTC by actions outside this audit. Latest three
  observer records RUN/CANCELLED; provider4008 underlying cause/fix still unproven.
  Validate E2E and credential lifecycle without assuming active means ready.
- Devices now41/37 non-revoked (+1 morning),NL9 recent handshakes/RU0;
  RU iowait2.09%,disk6.06%/await32.18ms. Worker still unhealthy.

- NL failure diagnosed:08:29:23UTC WS_CLOSE4008/SIGNAL_READ, then five15s
  SEED_CREATE/provider_timeout exits;08:33:39UTC systemd start-limit stops recovery.
  Provider-internal4008/timeout cause remains UNKNOWN. Independently gateway leaf
  expired00:46:05UTC; renew through accepted publication only as controlled recovery,
  then provider/start/readiness checks. No blind restart/security/start-limit bypass.
  [Evidence](releases/2026-10-14-restricted-failure-diagnosis.ru.md).
- 14.10 10:24UTC RU disk busy3.93%/iowait1.41%/await16.55ms; prior saturation not
  reproduced. Monitor historical I/O spikes, no unrequested restarts.
- Renewal success14.10 09:16:52UTC; served TLS expires19.10 12:07:37UTC.
  Continue monitoring; next timer14.10 21:12:36UTC. No manual renewal in this audit.
- Public telemetry now includes fresh RU/NL; prior omission not reproduced.
- 40 activated/36 non-revoked devices (+3); NL8 recent AWG handshakes, RU1.
  Client end-to-end and unique-human/DAU counts are not established.
- Read-only audit does not authorize supervisor deployment or change release gates.
  Product/control containers healthy; investigate peer-worker unhealthy/outbox.
  [Snapshot and limits](releases/2026-10-14-vpn-health.ru.md).

### GATEWAY-SEED-SUPERVISOR-OP-READINESS-1 — PARTIAL / READY=NO (13.10)

- Exact frozen candidate/baseline PASS; no rebuild or production changes.07:35–07:48UTC
  PID1864957/invocation41b2f937…3b850/NRestarts5 stable; served leaf expired, active real
  restricted sessions UNKNOWN. Two05:56 historical non-1011 fatal episodes preserved,
  not new failures during this task and not reclassified as planned DEADLINE.
- FIRST_BLOCKER=SYNTHETIC_TEST_ONLY_ISSUANCE_PATH_UNSUPPORTED. Existing exact API binds
  restricted grants to ordinary activation that also passes chat eligibility; no enforced
  test-only exclusion.11 local policy checks and6 readiness evaluator tests PASS.
- **Exactly next operation:** separately authorize and locally accept a test-only
  issuance/admission policy excluding ordinary activation/chat privileges, without
  changing/deploying the frozen gateway. Do not bypass grant/CRL tracking or create a
  parallel PKI. Synthetic identity and bounded issuance remain NOT_CREATED/NOT_RUN.
- Downstream gates remain: next credentials, real-session safety, exact-binary canary,
  full collectors, healthy rollback; future2710s+180s window fits a fresh4h invocation
  but is not operational readiness. No automatic canary/restart/owner CONNECT/FIELD.
  [Snapshot, policy evidence and plan](releases/2026-10-13-gateway-seed-supervisor-op-readiness-1.md).

### GATEWAY-SEED-SUPERVISOR-TRIGGER-1 — source-only PASS (13.10)

- Accepted local research candidate134083d8 /53beb661…5138f preserves c9d75db supervisor.
  Root-only exact-bound one-shot AF_UNIX seam defaults off; public build has no activation.
  Real upstream seed WS closes; actual Gorilla1011 frame reaches original reader/classifier.
  This is test-triggered, not evidence that Telemost generated1011 in that episode.
- Real-stack/race/root/privacy/retention PASS; unchanged directory, persistent dedicated
  TCP/Mux, old-cache bootstrap and lease continuity; bounded cleanup. No new baseline
  failures; existing diagnostic/source-guard/API assertion failures explicitly retained.
- **Exactly next operation:** separate operational readiness: authorized synthetic identity,
  fresh credential renewal, active-session inventory, exact frozen-binary real-provider
  canary. Also fresh rollback/collector compatibility and independent lifetime/headroom.
  No automatic grant/deploy/renewal/live-room/owner CONNECT. Current readiness remains NO.
- Frozen binary is identical for that future canary and deployment; never deploy the local
  fixture overlay. Supervisor trigger task performed no production/owner/live actions.
  [Report/artifacts](releases/2026-10-13-gateway-seed-supervisor-trigger-1.md).

### GATEWAY-SEED-SUPERVISOR-PREDEPLOY-1 — readiness NO (13.10)

- Fresh baseline/candidate hashes match; invocation stable, no new fatal. Process budget
  sufficient (future2710s +180s margin), but served Family leaf expired00:09:41UTC. No renewal.
- FIRST_BLOCKER=SYNTHETIC_IDENTITY_UNAVAILABLE; known approved disposable profiles were
  removed and no accepted production synthetic grant/custody reference is available.
  Active real restricted sessions UNKNOWN; do not infer zero from absent ownership output.
- Historical trigger is an in-process tagged test adapter, not in the sealed production
  binary. Raw transport cuts do not produce1011; no accepted external proxy/control with
  required trust, exact targeting and removal. TRIGGER_REQUIRES_NEW_CANDIDATE=YES.
- **Exactly next operation:** separately scoped source-only acceptance-trigger candidate
  and full local acceptance. Do not alter current c9d75db6 artifact, deploy, renew or add
  production grants implicitly. Future canary/deployment must still close identity,
  credentials, session-safety, complete collectors and rollback gates.
- No canary/live rooms, production restart, owner action or consumed attempt. Existing
  functional warm-start and local supervisor PASS retained. [Result](releases/2026-10-13-gateway-seed-supervisor-predeploy-1.md).

### GATEWAY-SEED-SUPERVISOR-DEPLOY-1 — stopped before deployment (13.10)

- PRELIVE_SERVER_CHANGED: fresh invocation00d21e8d81a549f0aa9df8a2714f9ea6,
  PID1807869,NRestarts3. Two normal four-hour DEADLINE/exit0 completions since saved
  reference, not new WS1011/fatal. Exact baseline binary remains loaded/next.
- Candidate c9d75db6 / d6875817…5765 and local acceptance remain valid; no deployment,
  renewal, controlled restart, synthetic room, owner action or consumed attempt.
- **Exactly next operation:** separate predeployment-readiness gate for current
  invocation, including accepted synthetic identity and verified seed-only trigger
  compatible with the sealed binary. Historical tagged adapter is not in production.
  Establish these before any restart; do not silently rebuild/add a fault endpoint.
- This supersedes the immediate-deployment next step below. Final owner warm-start,
  FIELD and public release remain deferred. No automatic next operation.
- [Read-only abort and immutable receipts](releases/2026-10-13-gateway-seed-supervisor-deploy-1.md).

### GATEWAY-SEED-SUPERVISOR-1 — local candidate accepted; deployment remains separate (13.10)

- Source-only production supervisor acceptance PASS. Validation commit
  `c9d75db6020f9f605e891036cbb9b68cebede708`, gateway binary
  `d6875817cf33fdd85c6ad78a342fc93afd16864293e94a6e5b7136eec5125765`.
- Narrow1011 recovery in the same room preserves directory and existing dedicated
  Family/Mux/TCP/lease. Three rejoin attempts per room lifetime, existing45s budget,
  expiry/fail-closed security, isolated generations and immutable first-close receipts.
  No new wire fields, room creation on recovery, API replacement or systemd policy.
- **Exactly next operation:** controlled production gateway continuity deployment/
  acceptance, fresh exact baseline and credential preflight, one controlled restart,
  one real isolated signaling disconnect, old-cache synthetic bootstrap and dedicated
  continuity,30-minute observation, bounded rollback. Run only as a separate task.
- Do not combine that first deployment with owner formal warm-start, real whitelist
  FIELD, Telegram/application compatibility, APK work or public release. Accepted
  structured collectors remain separate and require their own composed acceptance.
- No deployment/renewal/owner/live-room actions in this source task. Historical
  functional warm-start PASS persists; WHITELIST_WARM_START_READY remains NO.
[Result, exact baseline, tests and deployment gate](releases/2026-10-13-gateway-seed-supervisor-1.md).

### TELEMOST-REAL-SAME-ROOM-REJOIN-1 — capability passed; supervisor remains local next (12.10)

- Actual Telemost same-room full Pion/SDP/ICE/RTP rejoin passed after one real upstream
  signaling socket disconnect. One seed create, unchanged D, new authenticated cached
  bootstrap/dedicated READY; original dedicated Mux/TCP stream remained open.
- Close1011 was injected only at the test classifier boundary after actual disconnect:
  provider-generated1011/internal reason are not proven by this experiment. Recovery
  must still validate room/security/expiry and terminate within finite budgets.
- **Exactly next operation:** minimal production seed-supervisor source patch and
  controlled local acceptance. No automatic deployment/restart/formal warm-start run.
  Separate observability/behaviour diffs; generation-scoped lifecycle, old cleanup
  isolation, dedicated continuity, same-D reuse, finite backoff, stop cancellation,
  auth/protocol/expiry fail-closed. Do not retry every UNKNOWN.
- Exact harness/matrix race×3:54PASS. Live61.2sec, original28frames; real lease boundary
  not reached. All test processes/private state removed; provider object TTL/delete
  not exposed by inspected API. Production/owner counters0; FIELD/releaseNOT_RUN.
[Exact capability proof, source/binary and cleanup](releases/2026-10-12-telemost-real-same-room-rejoin-1.md).

### GATEWAY-SAME-ROOM-REJOIN-PROOF-1 — remaining provider contract boundary (12.10)

- Local real-Pion same-room rejoin, old-cache authenticated bootstrap and dedicated
  Family/Mux/TCP continuity PASS; no fake READY/packet-pair. Authenticated lease control
  passed with test clock. Race×3 and unchanged baseline security gates PASS.
- **One remaining capability blocker:** real Telemost room retention and permission
  for a complete fresh publisher/subscriber media join after seed1011 are not evidenced.
  Local SFU persistence is an explicit model assumption, not a provider guarantee.
  SAME_ROOM_REJOIN_CAPABILITY=UNKNOWN; no impossibility/successor claim either.
- Establish that exact provider contract boundary independently; metadata GET alone
  is insufficient. Do not automatically implement/deploy a production recovery loop.
  Keep experimental source separate: network adapters, SFU and driver are not a
  deployable gateway candidate. Full suite not rerun; known baseline issues untouched.
- Gateway/API/owner not accessed; restart/renewal/CONNECT/live room/gate all0. Prior
  functional warm-start PASS preserved; formal readiness unchanged; attempt unconsumed.
[Local media proof, model limitations and sealed artifacts](releases/2026-10-12-gateway-same-room-rejoin-proof-1.md).

### GATEWAY-WS-1011-CONTINUITY-1 — recovery proof incomplete; no deployment (12.10)

- Historical WS1011/ACTIVE proven; provider internal reason remains UNKNOWN.
  Real Gorilla→shared seed→fatal observer reproduced; documented current policy
  returns seed_closed and service cleanup closes the independent dedicated broker.
- Dedicated Family/Mux/TCP+lease local fixture proves it can survive seed subtree
  loss while the process/broker lives. It does NOT prove provider same-room media
  reconstruction or unchanged-cache bootstrap. Do not substitute metadata GET for READY.
- **First blocker:** SAME_ROOM_POST_1011_MEDIA_AND_CACHED_BOOTSTRAP_UNPROVEN.
  **One next operation:** local complete same-room fresh join → Pion media → packet
  readiness → authenticated bootstrap with unchanged cache, including stale generation,
  security and bounded-failure gates. Only then select/implement a recovery policy.
- OptionA provisionally preferred; B overlap cannot serve a dead old route; C restart
  still kills active dedicated sessions; D remains unchanged fail-closed behavior.
  No speculative retries, behavioural patch, production candidate or deployment.
- Fixture race×3 and independent rejection gates PASS; exact baseline full-suite
  failures unchanged, not green. Source test bridge is excluded from ordinary builds.
  No owner action/restart/renewal/room/gate/CONNECT; no new attempt consumed. Preserve
  historical functional warm-start PASS and formal PARTIAL. No automatic live task.
[Reproduction, remaining boundary, non-executable acceptance checklist](releases/2026-10-12-gateway-ws-1011-continuity-1.md).

### WARM-START-FORMAL-ACCEPTANCE-2 — stopped before deployment / owner (12.10)

- Accepted rebase/source473ebe57…badc unchanged; gateway/API baseline matched at entry.
  One same-key renewal passed strict/native gates; TTL/keys/trust/bindings unchanged.
  No candidate deployment, controlled restart, owner action or operator ACK.
- Mandatory PRELIVE_SERVER_CHANGED stop:20:12:48UTC natural SEED_READ/SIGNAL_READ,
  safe WS_CLOSE code1011, active context; exit1. Immutable raw application/systemd
  receipts preserved. Underlying provider reason and relation to renewal remain
  unknown; do not reinterpret old SEED_READ/UNKNOWN episodes.
- Automatic replacement invocation4fafa22a…855c7/PID1540161/NRestarts1 with new
  directory4d722bad…15424. Existing classifier21f0a0fd…509a remains loaded/next;
  accepted collectors remain local only. New owner cache compatibility NOT_CHECKED.
- **One next operation:** offline analysis of this exact sealed1011 fatal and shared
  seed lifecycle; no automatic live continuation. A new deployment/readiness decision
  must not reuse the aborted preflight or old user ACKs.
- Functional historical warm-start PASS preserved; formal PARTIAL, readinessNO.
  ATTEMPT_CONSUMED=NO for this task. Phone untouched; public release/FIELD NOT_RUN.
[Abort evidence, renewal and runtime snapshots](releases/2026-10-12-warm-start-formal-acceptance-2.md).

### WARM-START-COLLECTOR-REBASE-1 — local candidate accepted; no rollout (12.10)

- Exact deployed Python source archive, build/deployment chain and gateway baseline
  verified. Collector-only semantic port preserves AKI, time/ACK policy and publisher;
  closed runtime member superset, canonical responses/dispatch equal to deployed.
- REBASED_COLLECTOR_ACCEPTED=YES; source473ebe57…badc, gateway406a5ca4…dfe2,
  API78bfc20f…45fc6. Local commits/artifacts/rollback only; no root-worktree source
  replacement, push, server mutation or owner access.
- Differential/targeted/race/privacy/retention accepted. Full suite remains NOT_GREEN:
  five identical deployed Python assertions, six Go diagnostic assertions; busy-wire
  remains known. Independent security checks PASS; no new failures in tested scope.
- **One next operation:** controlled collector deployment, fresh preflight and one
  final formal warm-start run. Use capsule deployment plan, research84, existing
  exact-selection/egress harness and ACK-before-arm operator protocol. Nothing live
  runs automatically. Do not mistake current local candidate acceptance for formal
  warm-start readiness or reuse expiring credential/directory snapshots.
- Functional warm-start PASS and historical formal PARTIAL preserved. Warm/cold
  readinessNO; new attempt unconsumed; owner/gate/restart/renewal0, FIELD/publicNOT_RUN.
[Rebased source, acceptance and deployment plan](releases/2026-10-12-warm-start-collector-rebase-1.md).

### WARM-START-FORMAL-ACCEPTANCE-1 — deployment blocked by actual API baseline (12.10)

- Exact saved candidate verified; fresh deployed API byte comparison exposes rollback
  of AKI issuance, clock-skew validation and publisher integration/dependencies.
  SCOPE_VIOLATION_API_BASELINE_MISMATCH; no deployment/owner action or new CONNECT.
- Preserve historical functional PASS and formal PARTIAL. Prior local collector test
  PASS was against archived baseline, not the current HTTP artifact; do not relabel it.
- **One next operation:** rebase only the preserved collector diff on exact deployed
  HTTP source, retain AKI/skew/publisher and repeat differential acceptance before any
  deployment. Do not silently change protocol semantics while adding observability.
- Gateway observer/binary unchanged,19:12UTC bounded snapshot active PID1415977 /
  invocation1613fa1c…6829f / NRestarts0, strict chain PASS. Fresh preflight will still
  be required later; these short-lived credentials are not a future readiness grant.
- New attempt remains unconsumed. No gate/ACK prompt; old ACKs cannot authorize arm.
  Research84/cache/data untouched; no public release or FIELD.
[Scope evidence and exact hashes](releases/2026-10-12-warm-start-formal-acceptance-1.md).

### WARM-START-EVIDENCE-ATTRIBUTION-1 — functional PASS, strict evidence gate PARTIAL (12.10)

- Offline integrity/timeline/403 attribution complete. Two403 have no retained principal;
  selective nginx probe log and accepted DB rows cannot prove zero owner attempts.
- Authenticated client renewal and post-deadline egress PASS; independent server
  renewal receipt NOT_RETAINED. Never repeat the two timed-out historical queries.
- Source-only structured provisioning/lease collectors + conservative evaluator ready
  for separate review/deployment. Targeted HTTP13, lease/observer race×3, privacy and
  evaluator9 PASS; existing Python source-guard failure identical baseline/patched.
  Legacy bootstrap six assertions/busy-wire remain open; no full-suite PASS claim.
- Keep original B+D criterion, formal PARTIAL; WHITELIST_WARM_START_READY remainsNO.
  NEW_LIVE_RUN_REQUIRED=YES; previous physical attempt remains consumedYES.
- **One next operation:** separately authorized collector-backed evidence-completion
  run, including controlled deployment/fresh preflight; reuse research84 cache/gate,
  ACK-before-arm protocol and ordinary Android harness. No new CONNECT authorized here.
- No live actions this task. Reconcile actual API source before deploying archived-source
  patch; unknown/pre-HTTP attribution must not be converted to zero by the evaluator.
[Detailed report](releases/2026-10-12-warm-start-evidence-attribution-1.md).

### TELEMOST-WORKABILITY-PROOF-1 — core proven, evidence closeout PARTIAL (12.10)

- One physical CONNECT inside the ACK-before-arm window; cached native input,
  dedicated READY,7 correlated ordinary HTTPS responses via NL and controlled DNS PASS.
- Same session maintained723.814s after READY; authenticated renewal1, traffic after
  old deadline and renewal PASS. Reconnect/recovery0, no unexpected close observed.
- Formal first blocker: owner-scoped server attempt attribution. Accepted owner
  provisioning rows0 does not classify2 shared403 probe records; never rewrite them0.
  Client role gate blocked2 operations, cache unchanged, no owner direct call proved.
- Server journal collection for distinct startup/episode windows timed out; do not
  repeat those queries. Independent server lease receipt not available. Parallel
  probe series NOT_RUN; do not describe the complete proposed load matrix as PASS.
- **One next operation:** offline collector-attribution and bounded server-lease-evidence
  readiness. No new CONNECT, restart, renewal, APK change or product patch implicitly
  authorized. ATTEMPT_CONSUMED=YES. Keep current gateway observer/rollback and receipts.
- Final research84 preserved; gate CLEANED, VPN OFF, app/chat ON. Temporary collectors
  and test rules removed after idempotent cleanup reconciliation. Strict formal warm
  readinessNO until evidence gap closed; cold startNO, FIELD/public releaseNOT_RUN.
[Measured results / exact artifacts](releases/2026-10-12-telemost-workability-proof-1.md).

### GATEWAY-SIGNAL-READ-CAUSE-1 — offline classified boundary / no behavioral fix (12.10)

- PARTIAL: original low-level14:22 error not retained; historical causeUNKNOWN.
  Exact Gorilla ReadJSON→generic SIGNAL_READ→shared SEED_READ fatal path established;
  ordinary owner CONNECT excluded for this fatal, earlier12:17 remains separate.
- Observation-only local candidate retains typed immutable low-level metadata.
  Real WS/WSS fixtures and targeted race×3 PASS; full suiteNOT_GREEN, known six
  diagnostics + independently baseline-reproduced busy-wire flake. No new failure
  class; neither assertions nor transport behavior changed.
- No proved behavioral violation of documented sole-seed fail-closed contract.
  Same-room recovery/provider rotation not authorized by present API contract;
  planned bounded overlap cannot revive a dead seed. No blanket UNKNOWN retry.
- Main dirty worktree/old evidence/owner remain preserved. One read-only14:55:43
  snapshot retains deployedfa4cf867…733eea/PID1328380/e24e32cf…9362b/NRestarts1;
  observer armed, no new receipt. No fresh closeout chain/cache readiness claim.
- **One next operation:** separate controlled observation-update acceptance/deployment,
  then capture a natural trigger. No automatic deployment, renewal, owner access,
  cache refresh or CONNECT now. READY_FOR_CLEAN_RETRY staysNO.
- Future authorized warm-start still requires ACK→fresh gate/invocation check→active
  window; late CONNECT OUTSIDE_TEST_WINDOW. All22 offline operator fixtures PASS;
  real adapter wiring is not claimed completed. Prior physical attempt consumedYES.
[Report, matrix, options and limitations](releases/2026-10-12-gateway-signal-read-cause-1.md).

### GATEWAY-SEED-READ-OBSERVABILITY-1 — deployed / new SIGNAL_READ evidence (12.10)

Historical checkpoint; next operation superseded by the offline result above.

- PARTIAL: exact observation-only sourcea4087e00/binaryfa4cf867…733eea loaded;
  differential/race×3 PASS with no new failures; legacy suite remainsNOT_GREEN.
- Same-key leaf renewal1, controlled restart1. Immediate postcheck asserted;
  no mutation replay/rollback. Original process start later independently confirmed.
  Planned30m collector not started; do not infer continuous observation from uptime.
- Natural14:22:01SEED_READ/SIGNAL_READ/exit1 captured by both immutable receipts;
  ReadJSON failure boundary proven, lower-level cause and historical12:17 UNKNOWN.
  No behavioral patch, artificial fatal, manual retry or client attribution.
- Final PID1328380/invocatione24e32cf…9362b/NRestarts1 after automatic restart;
  loaded=next observation, strict chainPASS, directory631ad219…35664, RU/NL equal.
  Observer/rollback retained; owner/cache untouched, readinessNO.
- **One next operation:** separate GATEWAY-SIGNAL-READ-CAUSE remediation/localization
  from the new typed receipt. No automatic behavioral deployment or warm-start.
  Keep accepted ACK→recheck→CONNECT-window runbook for a later authorized test.
[Deployment/evidence report](releases/2026-10-12-gateway-seed-read-observability-1.md).

### GATEWAY-SEED-READ-CAUSE-1 — observation-only candidate, no live action (12.10)

Historical checkpoint; next operation superseded by deployed result above.

- Offline PARTIAL: exact abc604b0 source traced,222 original sealed entries intact.
  Shared seed Recv loss is fatal; per-exchange peer/auth/malformed failures remain
  isolated in before/after fixtures. No proven behavioral defect/behavioral patch.
- Historical SEED_READ/UNKNOWN cause and relation to late CONNECT remain UNKNOWN /
  NOT_ESTABLISHED. Valid-window0, late physical1, gateCLEANED; no warm product verdict.
- Two-file safe observation delta prepared locally (existing close-source retention,
  typed net errors), targeted race/negative-rejection PASS; full suite not green.
  No main APK/transport/timers/admission/exit-policy or loaded server change.
- Two-phase ACK/recheck/active-window protocol and22 fixtures PASS; future runbook
  closes window explicitly, classifies late CONNECT OUTSIDE_TEST_WINDOW. Research84
  900s/32 unchanged. Host crash has bounded TTL fallback, not guaranteed immediate disarm.
- **One next operation:** separate controlled observation-only deployment task.
  Then a later fresh readiness decision; no CONNECT/rearm/restart/renewal now.
  Prior physical attempt consumedYES; no new attempt authorized by this report.
- READY_FOR_CLEAN_RETRY remainsNO. Do not retry historical timed-out queries,
  retroactively attribute owner/DPI/phone call, or claim FIELD/cold-start readiness.
[Report/artifact index](releases/2026-10-12-gateway-seed-read-cause-1.md) /
[unexecuted two-phase live runbook](whitelist-warm-start-two-phase-runbook.md).

### WHITELIST-WARM-START-1 — natural SEED_READ fatal evidence gate (12.10)

Historical checkpoint; next operation superseded by the offline result above.

- PARTIAL. Research84 installed/verified in place; exact retained-cache production
  selection and native offline validation PASS. Native/gateway bytes unchanged.
- Bounded provisioning gate armed then CLEANED after90s operator timeout; no
  CONNECT/native/full-phase request in that window. Late user CONNECT occurred
  after cleanup: physical attempt consumed once, no blocked-warm PASS/no retry.
- Final owner12:23:09UTC VPN OFF/app+ChatDeliveryService ON. Gate/helpers/temporary
  endpoint/collectors cleaned, cache/vault unchanged through cleanup read; later
  ordinary background refresh is separate and final exact cache hash not asserted.
- Natural gateway fatal12:17:02UTC: SEED_READ/UNKNOWN, returned_error/exit1,
  limiting expiry still in future, no parent-context cause. Both receipts preserved. No evidence
  establishing late CONNECT, voice call, DPI, expiry or retry settings as cause.
- Automatic restart only: PID1255784/invocation853bf7d3…f92b/NRestarts1, observer
  sourceabc604b0/loaded+next0ccaaf81…2667a. Directory5d3bc057…71316 replaces old
  9c84fc89…9a51 seed; strict served chain PASS at12:22, expiry13:36:04UTC.
- READY_FOR_CLEAN_RETRY=NO; first blocker GATEWAY_NATURAL_FATAL_SEED_READ_UNKNOWN.
  Exactly one next operation: offline localization using preserved first-cause
  receipts and exact observer source; no CONNECT or behavioral deployment.
- Do not reuse old cache acceptance after invocation change, retry the timed-out
  journal query, auto-renew/restart, claim whitelist FIELD, or repeat CONNECT.
  Any later live attempt needs separately authorized fresh preflight/operator window.
[Acceptance and limitations](releases/2026-10-12-whitelist-warm-start-1.md).

### WHITELIST-PROVISIONING-BLOCK-SEAM-1 — local gate accepted (12.10)

Historical local-only checkpoint; subsequent live preparation/outcome is above.

- PASS / PROVISIONING_BLOCK_CONDITION=READY, local only. Research84/code84
  signed with previous signer; package unchanged; APK fd310617…1aa48, native reused.
  No owner install/instrumentation/refresh/arm/CONNECT and no gateway action.
- Isolated source f5240994 + delta d7907697…481e7. Role-specific fetch/ACK permit,
  private binding, 900s/32-entry bound, cleanup/crash/reboot handling; public build inert.
- 45 Java and14 operator/credential guards PASS; disposable API31/API35 request
  counters prove provisioning0 while ordinary/underlay/chat remain usable, cache
  unchanged and production cached selection/native offline validation succeed.
- Local collector fixtures PASS, but no current runtime/chain/cache/remote attach
  verification. READY_FOR_CLEAN_RETRY is not automatically raised; attempt unused.
- Exactly one next operation: separate fresh gateway/credential/cache preflight;
  if valid, controlled owner in-place update/arm and one physical manual warm-start
  CONNECT. Do not auto-run it or consume the clean attempt on stale prerequisites.
- Preserve observer/receipts, research83 user data, proven egress harness, prior
  Reliable OPEN issues and six negative-auth diagnostic assertions. No FIELD/public
  distribution or cold-start claim. Local teardown completed; owner state not touched.
[Detailed acceptance](releases/2026-10-12-whitelist-provisioning-block-seam-1.md).

### WHITELIST-GATEWAY-RECOVERY-2 — scoped test-condition gate (12.10)

Historical checkpoint; the compliant local seam is accepted above, not live-tested.

- PARTIAL: same-key renewal and one logical start PASS; observer binary unchanged,
  PID1168539/invocation26e8634a…282a/NRestarts0, bounded610.324s stability PASS.
  Current directory9c84fc89…9a51, strict served chain and RU/NL publication PASS.
- Existing background refresh reused, no extra request. One unchanged accepted
  helper proves identity-bound production selection and installed native validator
  PASS;3301byte cache SHA66e31bed…33ed unchanged, selected canonical4f587526…aa85.
  Helper removed; final VPN/app/chat OFF. Research83/enrollment/AWG/history preserved.
- READY_FOR_CLEAN_RETRY=NO; first blocker PROVISIONING_BLOCK_CONDITION_NOT_READY.
  Existing source-IP503 is NOT allowed under current scope. Do not activate it or
  claim a shared-endpoint block is provisioning-role-only. No owner CONNECT consumed.
- Exactly one next operation: design/fixture-validate compliant owner-role network
  denial without CONNECT. Full collector bundle remains unaccepted despite local
  current-ABI/generator/gate PASS; narrow journal timeout not repeated. Later gates
  still require fresh chain/cache/invocation/headroom and explicit manual CONNECT scope.
- Current leaf expiry13:36:04UTC12.10,1200s cutoff13:16:04, process deadline13:43.
  Manual renewal remains an operational requirement; finite local preflight is not
  an armed alert. Do not reuse this snapshot after expiry or assume next restart covered.
- Preserve718 prior sealed entries/13 old fatal receipts. PROFILE rejection on the
  old auto-starts is proved; pre-observer historical exits UNKNOWN. No transport fix,
  APK build/distribution, automatic CONNECT, cold-start claim or FIELD.
[Recovery report](releases/2026-10-12-whitelist-gateway-recovery-2.md).

### WHITELIST-EXACT-SELECTION-1 — natural-exit prerequisite gate (12.10)

Historical checkpoint; recovery and current critical path are above.

- PARTIAL: one owner offline run proves exact identity-bound production selection
  at11.10 21:27:13UTC. Native validator0; selectedbb5c…d8959/current seed matched;
  raw cache unchanged, canonical input exactly equal. Previous selection blocker
  CLOSED for capture. Twelve disposable cases/15 guards PASS; no product patch.
- Later external/platform-origin Activity resumption (caller unknown) produced two
  background provisioning imports. Not initiated by harness, not zeroed in report.
  Last12.10 09:12UTC app/chat ON, VPN OFF; ordinary user process not force-stopped.
  No second instrumentation, refresh, launcher, CONNECT or automatic restoration.
- Observer captured normal4h deadline exit0, then five automatic PROFILE /
  CREDENTIALS_REJECTED exit1 startups with expired credentials. Preserve13 exact
  receipts; historical pre-observer exit cause remains UNKNOWN. Final failed,
  PID0/NRestarts6/last invocationc1ad4d44…80d7d, next observer bytes unchanged.
- READY_FOR_CLEAN_RETRY=NO; single first blocker GATEWAY_INVOCATION_CHANGED.
  Current accepted set empty despite unchanged on-disk directory. No preparation
  continued after natural-exit discovery; clean CONNECT attempt still UNUSED.
- Exactly one next operation: separately scoped operational gateway credential-
  recovery preflight using accepted same-key runbook for proved PROFILE rejection.
  No transport/retry/TTL changes or automatic restart/CONNECT in this task.
- Block role fixtures and current-binary ABI binding pass locally, but source scope
  exclusivity and executable collector bundle not ready. Reassess only in later
  readiness work; no gate shown, no owner block activated, no FIELD/APK release.
[Selection, lifecycle and fatal receipts](releases/2026-10-12-whitelist-exact-selection-1.md).

### WHITELIST-CACHE-METADATA-1 — exact-selection evidence gate (11.10)

Historical checkpoint; the separately authorized validation and later fatal state are above.

- PARTIAL; one permitted owner instrumentation consumed, clean CONNECT attempt
  still UNUSED. No second instrumentation under this authorization; no Activity,
  native startup, CONNECT, refresh, cache write or product deployment.
- Cache read PASS/unchanged. Directorybb5c8eb0…d8959 is current and accepted by
  invocationdd70fcd8…3384a/PID788144/NRestarts0. Full identity-bound validator result
  is not reproduced: native candidate B known, exact usable selection UNKNOWN.
  READY_FOR_CLEAN_RETRY=NO; single first blocker EXACT_CONNECT_SELECTION_UNVERIFIED.
- Exactly one next operation: a separately scoped metadata-only proof of full
  identity-bound cache validation/exact selection, without CONNECT or refresh.
  Do not refresh just because the old historical cache was expired: actual cache
  was updated by existing background work and expires21:37:28UTC. Recheck time.
- Background provisioning20:20/20:25 is recorded separately, not hidden under
  task refresh0. Block source exclusivity and current observer collector binding
  remain later unpassed gates; role-only fixtures do not establish live readiness.
- Final20:37UTC VPN OFF, app/ChatDeliveryService OFF; helper removed. No unproved
  networking restart for cosmetic app ON. Preserve cache/enrollment/AWG/history,
  research83 and observer. No APK publication, FIELD or automatic CONNECT.
[Metadata reader / exact limits](releases/2026-10-11-whitelist-cache-metadata-1.md).

### WHITELIST-CACHE-READINESS-2 — exact cache access gate (11.10)

Historical checkpoint; lifecycle permission and its one reader run are recorded above.

- PARTIAL; READY_FOR_CLEAN_RETRY=NO. Single first blocker:
  CLIENT_CACHE_ACCESS_REQUIRES_LIFECYCLE_PERMISSION. No safe non-lifecycle live
  cache export on installed83; do not invoke instrumentation/Activity implicitly.
- Current observer/runtime/chain/publication verified without mutation. Current
  invocation accepts its seed1, not old-process directories. Client cache digest,
  validity, exact selection and effective headroom remain UNKNOWN. Do not refresh
  blindly or equate last fingerprint-less ACK with current cache.
- Local guards/condition fixtures5 PASS; existing1200s server headroom guard met.
  Block source exclusivity and collector binding to observer binary still need
  later validation; no blanket collectors/Telemost reachability PASS.
- Exactly one next operation: obtain explicit permission for metadata-only cache
  instrumentation with controlled target interruption/restoration, no Activity,
  prewarm, refresh, native beginReady or CONNECT. Existing observer wrapper is not
  suitable unchanged. Preserve observer/rollback/research83/cache and sole attempt.
- No CONNECT/FIELD/APK distribution. Cold start remainsNO; warm start not staged.
[Readiness/cache evidence](releases/2026-10-11-whitelist-cache-readiness-2.md).

### GATEWAY-FATAL-CAUSE-1 — bounded observation complete, no trigger (11.10)

- PARTIAL/ARMED_NOT_TRIGGERED: isolated sourceabc604b0; gateway loaded/next
  0ccaaf81…2667a. Gateway observer only, no transport/lease/Android change. Typed
  receipts and root systemd exit layer installed; targeted local/race/privacy PASS.
- One standard same-key renewal + one controlled restart; no rollback. Strict
  chain/served DER and synchronized publication PASS at19:37UTC, limiting security
  expiry21:37:28UTC, not directory23:19 expiry. No owner mTLS/CONNECT/cache import.
- Natural fatal did not occur in900.025s (19:22–19:37UTC). Historical cause UNKNOWN;
  do not manufacture a failure or infer cause from controlled exit0. Preserve new
  bounded receipts and earlier failure evidence; no repeated broad journal query.
- Research83 unchanged; final VPN OFF/app+ChatDeliveryService ON. CONNECT0 and sole
  clean attempt UNUSED. READY_FOR_CLEAN_RETRY remains NO, not raised by observer.
- Exactly one next operation: separate readiness preflight in an agreed window,
  checking current client cache against actual gateway accepted publication. No
  CONNECT, FIELD, transport patch or APK distribution authorized by this result.
[Observer closeout](releases/2026-10-11-gateway-fatal-cause-1.md).

### WHITELIST-GATEWAY-READINESS-1 — gateway/cache prerequisite gate CLOSED (11.10)

- Read-only assessment complete with explicit limits: READY_FOR_CLEAN_RETRY=NO,
  CONNECT0/full-phase0, clean attempt UNUSED. Preserve installed83 and same gateway
  bytes; no owner lifecycle, enrollment/cache modification or manual carrier open.
- Old15:09 process exit cause remains UNKNOWN; main discarded its typed run error.
  Bounded unit/kernel window queries timed out, no repeat. Duration/then-valid trust
  do not establish expiry as cause. Do not tune handshake/Reliable or blame the call.
- Additional automatic restart observed during this task: NRestarts1→2, latest
  invocation78333d45…1485/PID768197/start18:45:56UTC; publicationa20c2622…820cd.
  Do not turn short8s stable snapshots into an overall stability PASS. Agent did
  not restart, renew, publish or create a room; runtime background changes recorded.
- Served-chain expired17:49:16UTC; directory/runtime lifetimes do not extend it.
  Owner grant/authority and synchronized CRL do not prove client admission. Current
  client cache digest UNKNOWN; last historical ACK18:08:32 has no snapshot digest.
  Existing overlap does not survive process restart; no manual directory import.
- One next operation: separately design safe typed-cause capture for a future fatal
  exit without transport timeout changes or owner startup. No logging change can
  reconstruct the unavailable historical cause. Keep same-key renewal and restart-
  safe cache/seed contract as prerequisites, not a silent readiness workaround.
- Local guard5 methods/60 rejection subcases PASS. All10 preflight criteria must be
  true before any later physical gate. Current gate remains NO. Last app/VPN/chat
  observation18:46:28UTC: app ON/VPN OFF/chat ON; no server/phone cleanup mutation.
[Readiness result and bounded evidence](releases/2026-10-11-whitelist-gateway-readiness-1.md).

### WHITELIST-DEDICATED-JOIN-1 — pre-CONNECT gateway blocker (11.10)

Historical preparation checkpoint; latest gateway/cache assessment is above.

- Offline correlation complete: descriptor14:03:59.563 → join59.574 → client failure
 14:04:14.576 → server timeout18.656UTC. No call/network-change telemetry in that
 window; CELLULAR is insufficient. Potential confounding remains OPEN, no defect
 conclusion or transport timeout increase. Prior157 sealed entries unchanged.
- Operator confirmed call ended; clean preparation stopped before displaying the
 physical CONNECT gate. Entry subject83/gateway bytes unchanged, existing valid
 cache fallback observed under scoped503. Armed preflight15:09:08UTC BLOCKED:
 gateway exited1/auto-restart, served-chain connection refused. Automatic restart
15:09:37 retained binary but changed invocation and directory. CONNECT0, full-phase
 requests0; clean live attempt NOT_RUN/not consumed. Do not re-arm automatically.
- Next localize the generic `bootstrap broker stopped` process exit using bounded
 saved evidence; concrete run error was not emitted. Other gateway sessions are not
 this owner trial. No timeout increase, speculative transport fix or extra restart.
- Before a future gate require fresh coherent gateway/publication/served-chain and
 existing-cache viability. Last verified bound17:49:15UTC is historical, not current
 headroom. Do not obtain new provisioning/import/AKI renewal to manufacture this
 unchanged-cache scenario; stop if its original prerequisites no longer hold.
- Harness fast-click gate7PASS; final preflight-rejection tests10PASS after abort.
 Internal OPERATORGATETIMEOUT was not an operator failure: inherited runner waited
 after BLOCKED without displaying a physical gate. Guard corrected, no second live
 preparation. Test-app lifecycle/product unchanged. Preserve new168-entry evidence.
- Cleanup verified15:19:53UTC: VPN OFF/app+chat ON, exact ingress restored, owned
 collectors/endpoints/firewall/timers removed; no owner reset or agent gateway
 restart. This timestamp is not a current device-state claim after late log reads.
- One authorized physical clean attempt remains conditional on safe prerequisites:
 prepare collectors and scoped denial first, then dedicated READY and ordinary-app
 nonce correlation. No automatic CONNECT, repeat-to-success or call-log access.
- Keep CELLULAR_CALL_RESILIENCE separate: handover → recovery/RESTORING, truthful
 connection state, no user-traffic fail-open; not the primary dedicated acceptance
 gate and not an inferred explanation of the old timeout.
[Offline review, pre-CONNECT abort and next prerequisites](releases/2026-10-11-whitelist-dedicated-join-1.md).

### WHITELIST-BOOTSTRAP-1 — one live attempt consumed; localize saved failure (11.10)

- Preserve installed research83/code83/source f5240994, gateway5e877eb1 loaded/next,
  protected cache/floors and original research82 egress/lease evidence. No TUN,
  protect/bind, framing/Reliable, UI/messenger or lease changes in this episode.
- Local safe-cache/overlap/negative gates PASS; actual provisioning503 fallback and
  seed Family authentication observed. Dedicated client carrier fails before READY;
  no full-phase egress requests. Warm ready NO, cold ready NO, architecture PARTIAL.
- Keep client RECOVERY_JOIN_FAILED at14:04:14.576 and later server handshake timeout
  at14:04:18.656 as correlated observations, not a proven first-divergence cause.
  Next separately scoped work: saved-evidence startup/RELIABLE-FIRST-DIVERGENCE;
  do not tune RTO/retries or claim the new cache policy caused the carrier failure.
- Operator-gate fast-click regression is now fixed/tested in the isolated harness;
  latest preparation and remaining preflight blocker are recorded above. Test app
  lifecycle remains unchanged/proven. No retry was authorized by that episode
  itself; the voice-call clarification separately authorizes one clean attempt.
- Cold bootstrap and in-tunnel refresh remain unimplemented separate work; expiry,
  revocation, current server admission and finite overlap must remain fail closed.
- That episode's14:15UTC cleanup: VPN OFF/app+chat ON, original ingress restored,
  temporary resources removed; later automatic gateway restart is recorded above. No public
  APK/catalog update, tester delivery or real restricted FIELD. Full suite is not
  green: baseline lint and historical diagnostic assertions remain explicitly OPEN.
[Current result, immutable research manifest and exact failure boundary](releases/2026-10-11-whitelist-bootstrap-1.md).

### FULL-TUNNEL-EGRESS-VERIFY-1 manual — egress proved; separate remaining gates (11.10)

Completed one operator-only CONNECT on unchanged research82/gateway. Two ordinary
test-app HTTPS responses have TUN/Mux/session/NL wire-tuple/endpoint nonce correlation;
controlled DNS follows gateway. Preserve this evidence, not merely READY/counters.
No routing defect established; do not modify routes/protect/Telemost/renewal on this
result. Browser NOT_RUN, IPv6 unavailable, failover leak not tested during two natural
recoveries. No automatic repeat CONNECT or extra live fault injection authorized.
Separate next work: direct-provisioning startup dependency under whitelist model;
diagnose two saved RELIABLE_EXHAUSTION first-closes without assuming lease expiry.
Historical unexpected closes and six negative-auth diagnostic assertions remain OPEN.
Optional browser/IPv6/recovery-egress acceptance requires a separately scoped episode.
Current cleanup complete: VPN OFF/app+chat ON, unchanged product bytes, no restart;
read-only instrumentation stopped, test packages retained idle without uninstall.
No public release, APK distribution or restricted FIELD.
[Completed proof and retained manual regression workflow](releases/2026-10-11-full-tunnel-egress-verify-1-manual.md).

### FULL-TUNNEL-EGRESS-VERIFY-1 continuation — operator trigger prerequisite (11.10)

Keep research82/gateway bytes unchanged. A/B ordinary-request lifecycle and bounded
read-only observer startup pass; one short new Socket/TLS baseline succeeds.
Single ADB input attempt denied INJECT_EVENTS before CONNECT; actual connections0,
full requests0, all full runs remain ARMED. Episode stopped as HARNESS_FAILURE with
evidence/cleanup complete; do not repeat automatically or substitute another input
mechanism after the denial. Product route is not newly measured or diagnosed.
Next separately authorized attempt needs a real operator button press within the
prepared window (or an explicitly resolved interaction prerequisite), not late
startActivitySync or assumed ADB input permission. Keep mandatory ordinary-app
nonce, TUN-source-address and gateway/session/outbound correlation gates; collector
syntax/attachment readiness alone is not a successful correlation test.
Direct provisioning whitelist blocker remains a separate unchanged task. No routing,
Telemost, lease, UI or provisioning patch, no public release/FIELD. Current state:
VPN OFF/app+ChatDeliveryService ON; no extra gateway restart.
[Retained regression tool, exact acceptance scope and blocked gate](releases/2026-10-11-full-tunnel-egress-verify-1-continuation.md).

### FULL-TUNNEL-EGRESS-VERIFY-1 — incomplete acceptance; no automatic retry (11.10)

Preserve installed research82/source fbbecb81 and gateway34704e26, same-holder lease
renewal and previous evidence. One bounded UI CONNECT consumed; no end-to-end
full-phase nonce because of test-harness lifecycle failures. Do not turn TUN/READY
or background packet counters into ordinary-app egress PASS, nor call this a
product routing defect. Baseline Orange source IP/ASN is established only VPN OFF.
Next: validate UI-helper startup, finite cancellation and process/service cleanup
without CONNECT; retain verified fresh-task ordinary probe launch. Only then seek
separate authorization for a new nonce-correlated ordinary-app/browser episode,
including IPv6/DNS and a safe per-session recovery test. No unchanged retry-until-green.
Separate architectural blocker: required direct authenticated directory refresh
prevents both warm new connections and cold starts when provisioning is blocked;
cache is not a supported fallback. Design any bootstrap change under the existing
trust/revocation/floors contract, not by disabling refresh or inventing cached auth.
No product patch, rebuild, deployment, public release or FIELD in this task.
VPN OFF/app+chat ON; evidence/cleanup complete, no gateway restart.
[Exact matrix, verified local tests and remaining gates](releases/2026-10-11-full-tunnel-egress-verify-1.md).

### TELEMOST-LEASE-CONTINUITY-1 — local candidate → immutable build → one live (11.10)

Use isolated `state-client-build/field65-export16/telemost-lease-continuity-1/source`,
not main dirty code. New requirement makes the600s permission renewable without
relaxing trust or security expiry. Local authenticated Family/Mux persistent-TCP
continuity tested with controlled clocks; no live claim, no repeat of old episode.
Source fbbecb81 committed locally with explicit permission, no push. Research82
built/signed/installed in place; matching gateway deployed once; same-policy leaf
renewal and served-chain/directory preflight PASS. Exactly one bounded trial done:
two matched renewals, same live carrier and11 full HTTPS replies after both prior
deadlines. Persistent stream passes first boundary only; assertion170 failure
UNKNOWN, no socket reopen or second attempt. Next separate work: preserve/diagnose
that application-stream evidence gap with safe error codes before considering a
separately authorized trial. Do not call overall continuity complete or rerun until
green. VPN OFF/chat ON, cleanup complete, no extra gateway restart.
Six historical diagnostic failures stay separate; no UI rollback/public/FIELD.
[Candidate contract, exact local gates and unfinished work](releases/2026-10-11-telemost-lease-continuity-1.md).

### TELEMOST-STABILITY-1 — bounded lease observation completed (11.10)

One720s-after-READY episode proves expected600s acquisition-based expiry, exact
release, automatic new native/server session and new verified traffic. No behavioral
patch or control trial justified; no repeated CONNECT. Global stability and old
DATA/carrier incidents remain open, historical admission attribution search closed.
Retain research81 and gatewayc101…cc54c7; preserve same-policy authority10/floors.
Separate open work: DIAG-AUTH-REJECTION-1 diagnostic assertions (mandatory rejection
passes); peer streaming STOP_TIMEOUT / second-session capture and persisted-incident
matching limitations. Do not convert these into a speculative network patch or rerun
the same general logs. Final observers stopped,loaded/next match,cleanup restart0.
[Evidence and acceptance boundaries](releases/2026-10-11-telemost-stability-1-continuation.md).

### TELEMOST-ADMISSION-OWNERSHIP-1 — bounded pass, no behavior fix (10.10)

Exact ownership observation implemented/tested/loaded on NL; one diagnostic maps
client tag→exchange→real holder→Close/release. Fresh grant2ms/HELLO/READY/DNS/4HTTPS
responses PASS,120s without unexpected client loss. Historical20:03 holder UNKNOWN:
old records lack the join; new clean runtime is not retrospective proof. Preserve
admission/identity/trust/lifetime contracts; no evidence justifies eviction, arbitrary
limits or unconditional release. Chat DIRECT in this episode; integrated chat-first/
VPN contention not exercised or blamed. Full authenticated suite negative-auth
diagnostic assertion also fails on unchanged baseline, independently of capture.
Bounded observer expired;21:57:14UTC loaded/next/security checks PASS,18 events.
Own helpers/fixtures removed without restart; authority10/floors and APK81 retained.
No further CONNECT/control/general journal collection in this task; root-cause fix
and TELEMOST-STABILITY-1 closure not claimed. Public/FIELD/UI rollback excluded.
[Exact unresolved boundaries and rollback](releases/2026-10-10-telemost-admission-ownership-1.md).

### Local storage move completed — 10.10

Use `/mnt/data/PycharmProjects/family_connect` as project root. The old location is
a compatibility symlink; full content/metadata and Git preservation checks passed
before removing the old duplicate. Reopen stale terminals/Codex sessions; no build,
installation, network experiment or server mutation was performed. Technical
priorities and research81 failure statuses are unchanged. External build caches
and vault remain at their original locations. Do not remove the old-path symlink
as incidental cleanup: scripts and cloned Git repositories can reference it.
Report: releases/2026-10-10-project-storage-move.md.

VPN read-only follow-up10.10 (09.10 23:44–23:47UTC):34 enrolled/30 nonrevoked;
NL1 transfer-active peer,RU0. Worker unhealthy traced to inherited API8080 probe
on worker-only command;5/5 recent checks connection refused,34 recent cycles exit0,
outbox3/3matched/0errors. Separate maintenance: design worker-specific healthcheck,
not a blind restart. Monitor disk latency: minute NL157.09ms/RU29.01ms; investigate
new HTTP/restricted process starts (NL current NRestarts0 does not erase prior8).
Actual client E2E still required. No remediation/restart/deploy/renewal performed
by this health check; engineering critical path unchanged.
[Measurements](releases/2026-10-10-vpn-health.ru.md).

### Owner selection safety — decision reached; no physical run (07.10)

Exact beta69 writer audit complete: sources YES, exclusive helper ownership NO,
safe requested test-send scenario on existing controls NO. Real TUN and reactive/
queued Mux/TLS/bridge writes defeat sampled-next selection; watch expiry also does
not atomically disarm generic fault. No polling/sleep/assertion relaxation proposed.
Compare targeted compare-next (logical-N only) vs owned allocation lease vs parked
candidate with changed ordering; full original order needs runtime contract scope,
not another test-only launch. Design only; sealed runtime unchanged.
Prepared bounded read-only invocation observer for future operator harness, not run;
12 mock/source checks PASS. Gateway historical exit still UNKNOWN and separate.
NEXT: user decision/authorization for minimal diagnostic-contract work before any
new owner-run request. No implicit release/freeze/build/sign/CI/deploy or live prearm.
[Decision report](releases/2026-10-07-owner-retry-selection-audit-1.md).

### OWNER-RETRY-PREP-REVIEW-1 — completed; no live replay authorized (07.10)

Bounded review PASS, not selected-retry PASS. Causes of historical quiescence failure
and old gateway exit UNKNOWN; relationship NOT_ESTABLISHED. Historical samples absent,
bounded journals unavailable; do not keep searching indefinitely or infer packet loss.
Effective service lifetime4h confirmed; old process replacement occurred before its
20:53UTC deadline, not established normal lifetime completion. Same-PID FAIL retained.
Prepared test-controller-only patch with failure-only bounded metadata and fail-closed
session/sample checks; 12 local tests PASS, original polling cadence/predicate retained.
Before separately authorized owner run: address exclusive-writer/reservation gap between
sampled next and receiver prearm/generic fault arm; candidate alone does not solve it.
If runtime reservation is necessary, present minimal scope for separate authorization,
do not implement it in this task. Fresh existing preflight/lifetime budget and cleanup
remain required for any future run, without new acceptance endpoints or owner soak.
No new build/install/session/prearm/fault/restart/renewal/CI/publication performed.
[Review](releases/2026-10-07-owner-retry-prep-review-1.md); prior FAIL and receipts retained.

### OWNER-SELECTED-RETRY-BETA69-1 — FAIL / no further live attempt (07.10)

One prepared physical session, zero receiver/sender prearms, arms, drops or binds.
Restricted initial traffic PASS; stable quiescent DATA selection unavailable within
accepted window. First error preserved; no selected attempt1/pinned chain evidence.
Post-cleanup automatic gateway restart observed: PID1943512→1992456, NRestarts1,
new process18:26:59UTC after helper finished18:25:25UTC. Cause and old exit timestamp
UNKNOWN; bounded journal reads timed out. Existing same-PID cleanup criterion FAIL.
Safe cleanup and owner/sealed artifact preservation verified; test helper removed.
No manual restart/renewal, runtime fix/build, second experiment or publication.
NEXT: separately investigate retained selection failure and new automatic restart;
no blind physical replay. Freeze/deployment PASS remain historical accepted receipts,
not evidence that selected-retry passed or that Krasnodar is now ready.
Evidence: field65-export16/owner-selected-retry-beta69-1/resume1/FAIL.json.

### RTP-IDENTITY-DEPLOY-1 — PASS / next separate owner experiment (07.10)

Exact immutable beta69 installed/loaded and preserved. Authorized helper-only
code69 adaptation built/signed; five contract tests PASS, no production rebuild.
Two restricted cellular DNS/full HTTPS/TCP cycles with reconnect/cleanup PASS;
active unarmed controls/no watches, socket access and DUMP permission PASS.
Restart fresh authenticated fetch→READY→ACK PASS (not merely restored readiness).
Final chain/RU-NL checks17:56:20UTC PASS; limiting expiry20:13:53UTC/headroom8252s.
Owner preserved, temporary helpers removed, sealed67/68/69 unchanged, rollback ready.
One tooling permission-runner launch error retained/corrected via accepted standalone
probe, no failed product baseline/retry. Historical first gateway cause stays UNKNOWN.
NEXT: separate owner selected-retry with accepted complete pinned-chain criterion,
fresh time-dependent preflight and separate authorization. Do not execute automatically.
No publication/Krasnodar/soak/impairment. Receipt: field65-export16/
rtp-identity-deploy-1/helper69/PASS.json; prior PARTIAL receipts retained.

### Historical RTP-IDENTITY-DEPLOY-1 — PARTIAL / baseline helper mismatch (superseded)

Existing beta68 startup blocker proven: expired authority/CRL in effective profile;
historical first stop cause UNKNOWN. Authorized standard renewal and one controlled
beta68 recovery PASS. Exact sealed beta69 now installed on owner and loaded on NL;
owner preservation, fresh authenticated READY/ACK and restored restart READY/ACK PASS.
Actual served chain/RU-NL consistency PASS at17:26:27UTC; limiting expiry20:13:53UTC,
headroom10045s. Unit/sandbox/diag67 unchanged; rollback binary verified, retain renewed
credentials/floors. All sealed67/68/69 unchanged; no source/build/CI/publication changes.
Remaining existing gates: restricted cellular DNS/full HTTPS/TCP, reconnect and
active controls. Accepted restricted-only helper hardcodes68, incompatible with69;
do not spoof version or substitute normal/fallback traffic. Provide/authorize a
beta69-compatible test-only helper, then finish those gates without changing runtime.
No selected-retry until deployment PASS; no new experiment started.
Receipt: field65-export16/rtp-identity-deploy-1/resume/PARTIAL.json.

### Historical RTP-IDENTITY-DEPLOY-1 — PARTIAL / existing NL failure STOP (superseded)

Before changes, NL bootstrap already failed exit1/NRestarts11/MainPID0, no18444
listener; generic `bootstrap broker stopped` retained, cause not established.
Expiry is confirmed but not proven causal. Standard renewal is already authorized;
no additional permission gate added. No restart/deployment/renewal attempted.
Owner remains68, exact APK/signer/UID/data/Support ID/enrollment/identity/activation
preserved; accepted snapshot helper removed. Sealed67/68/69 unchanged.
RU/NL expired directory hashes match, admission/bindings/revisions/revocation
unchanged; live served TLS,69READY/ACK and cellular acceptance unavailable.
NEXT: causally resolve preserved existing startup failure, then resume the existing
authorized deployment/renewal. Selected-retry remains a separate unstarted task.
Evidence: field65-export16/rtp-identity-deploy-1/PARTIAL.json and dated report.

### RTP-IDENTITY-FREEZE-1 — PASS / immutable signed pair (07.10)

Exact SHA986323ecef112fcc421a22263e6fbfc9d6cf1922 and diag-owner-beta69-ci2
remain unchanged. Existing vault signer produced beta69/code69 with compatible
certificate; signature/package/ABI/non-debuggable/native/gateway verification PASS.
Final pair manifest SHA256:
`e039486c269b5fe1b99b51583bb155c540a32ca46dc49f8b96eb8431741189d9`.
Location: field65-export16/rtp-identity-freeze-1/immutable-ownerDiagnostic-beta69/.
Android37635226335, Client37635226241 and owner-pair37635226230 accepted receipts
bound; publication skipped. Beta67/beta68 sealed pairs unchanged before/after.
No source changes, rebuild, CI rerun, install/deploy/arm/renew/physical test/publication.
NEXT: separate beta69 owner deployment authorization/review using this sealed pair;
do not mutate frozen artifacts or treat this freeze as deployment authorization.

### Historical RTP-IDENTITY-FREEZE-1 — PARTIAL / signing input pending (superseded)

Keep accepted SHA `986323ecef112fcc421a22263e6fbfc9d6cf1922` and tag
`diag-owner-beta69-ci2` immutable. Android37635226335, Client37635226241 and
owner-pair37635226230 freshly reconfirmed PASS; publication jobs skipped.
Exact-SHA unsigned CI APK/JNI/gateway downloaded and provenance verified;
beta67/beta68 seals rehashed unchanged. No new commit or CI rerun required.
User authorizes local signing, but the mandatory vault-backed signer needs the
operator's non-secret vault path/entry/member identifiers and local password dialog.
NEXT: finish vault signing, signed-APK lineage/provenance verification and final
immutable pair seal. Current pair-manifest-DRAFT.json is not deployment authority.
Do not install/deploy/arm/renew/test physically/publish during this freeze.
Historical TCP remains NON_REPRODUCED_HISTORICAL_FAILURE, not a blocker.
Evidence: field65-export16/rtp-identity-freeze-1/resume4/PARTIAL.json.

## ANDROID-HARNESS-ACCEPTANCE-1 — PASS / exact-SHA local and hosted acceptance (07.10)

Replacement validation 986323ecef112fcc421a22263e6fbfc9d6cf1922, new CI-only tag diag-owner-beta69-ci2.
Exactly six androidTest files added to accepted beta69 + deterministic Go mux
correction; runtime/version/protocol/RTP/Reliable/ACK/transport source unchanged.
Complete local acceptance PASS: Python1809/26 skips, Go default/diagnostic race,
callback matrices, mux50/20/10,43 source guards,7 JVM +7 Android cleanup tests,
network/readiness/binding/forced-ENETUNREACH regressions, native provenance and
Android258 unit tests per owner/Friends variant with zero lint errors.
Full emulator48 reported/28 executed/20 existing skips, zero failures; storage
process restart and post-instrumentation control/RNS conformance PASS.
All17 hosted workflows PASS on attempt1. Complete Android diagnostic
run37635226335 and Client builds run37635226241 PASS, including
post-instrumentation, native/release payload verification and artifact steps.
Client release and TCP release/setup_release SKIPPED; no distribution run.
Historical TCP stays NON_REPRODUCED_HISTORICAL_FAILURE; beta69 unimplicated.
No release signing, physical-device install, gateway deployment, arming or field
experiment. Built unsigned is not installed/public/invitation-page rollout.
NEXT: resume RTP-IDENTITY-FREEZE-1 from this accepted replacement SHA; no implied
permission to sign or deploy. Existing deployed versions/rollback paths unchanged.
[Complete evidence](releases/2026-10-07-android-harness-acceptance-1.md).

Historical execution checkpoint (superseded by PASS): six-file scope authorized; replacement validation
986323ecef112fcc421a22263e6fbfc9d6cf1922 created, runtime unchanged. Full core
local acceptance passes, including Python1809/26 skips and Android258 per variant.
NEXT: finish exact-SHA emulator lifecycle/cleanup/post-instrumentation gates,
then require both complete hosted workflows plus the retained17-workflow CI gate
under a new non-publication tag. Never rerun a failed lifecycle/workflow blindly.
Preserve historical TCP non-reproduction disposition; freeze/signing still gated.
This supersedes the scope-clarification STOP below, not its historical evidence.

Historical scope checkpoint (superseded): ANDROID-HARNESS-ACCEPTANCE-1 PARTIAL, pending source-scope
clarification, not TCP reproduction. Exactly AutoRuntimeTest/AwgRuntimeTest/
TcpRuntimeTest cannot form the current accepted patch alone: Auto/TCP depend on
untracked TcpTrafficDiagnostics and TcpNetworkEvidence; cleanup regressions live
in TcpTrafficDiagnosticsTest. All three additional files are androidTest-only and
absent from6d1bddaa. Do not silently include them or refactor accepted corrections.
NEXT: authorize these existing helper/regression files in the narrow allowlist.
Then create the replacement SHA, repeat complete mandatory local exact-SHA
acceptance, and only on PASS select a new CI-only tag for BOTH complete workflows.
No new commit/tag/CI or runtime/version/sign/install/deploy/physical action in
this review. Historical TCP remains NON_REPRODUCED_HISTORICAL_FAILURE; do not
replay unless it newly fails. RTP-IDENTITY-FREEZE-1 remains gated by acceptance.
[Current review](releases/2026-10-07-android-harness-acceptance-1.md).

VPN audit07.10 follow-up (read-only snapshot; does not supersede engineering STOP):
investigate failed RU restricted-sync/NL restricted-bootstrap, distinguish worker
healthcheck from actual reconciliation/outbox progress, monitor RU disk latency
and growth, then validate client E2E separately. Basic AWG traffic is present on NL;
no restart/deploy/renewal performed. Public HTTPS certificate valid through12.10.
[Evidence and remaining checks](releases/2026-10-07-vpn-health.ru.md).

## TCP-LOW-PERTURBATION-REPLAY-1 — PASS / resume harness review (07.10)

Fixed60-trial comparison completes with0 failures: minimal/rich/original-like20
each, same installed runtime. Historical lifecycle and final-TCP default-network
transition reproduced; minimal/original-like have no hot-path route polling or
success logging. No observed observer-effect failure-rate difference; rare failures
are not excluded. Old assertion remains unexplained but is now classified as
NON_REPRODUCED_HISTORICAL_FAILURE, not causal evidence against beta69.
NEXT: resume ANDROID-HARNESS-ACCEPTANCE-1 from test-only source review, carrying
forward all receipts. Its source-bound local and BOTH complete hosted workflow
gates remain mandatory; no freeze/signing shortcut. No replacement SHA/tag/push/CI
or runtime deployment here. Older STOPs below are superseded only for this specific
historical-TCP blocker; unrelated VPN audit findings are unchanged.
[Evidence and explicit NO-block decision](releases/2026-10-07-tcp-low-perturbation-replay-1.md).

## TCP-INSTRUMENTATION-PRIMARY-1 — PARTIAL / initiating failure still unknown (07.10)

The bounded diagnostic experiment completed: exact TCP method48/48 PASS,
no-prior-switch probe3/3 PASS, preceding lifecycle order checks PASS, seven cleanup/
observability regressions PASS on both JVM and Android. HTTP fixture audit24/24
PASS. Status/body predicates are separate without weakening either; primary
traffic errors survive Auto/TCP stop/reset/finish errors and self-suppression.
Only androidTest source changed; no production or fixture behavior change.
The old failure did not reproduce, so neither its predicate nor its cause is
known. Diagnostic snapshot overhead may perturb the race; repeated success is
NOT a causal resolution or permission to resume harness/freeze acceptance.
NEXT: lower-perturbation capture of the preserved failing network/lifecycle state.
No replacement SHA/tag/push/hosted CI/sign/install/deploy until that blocker is
resolved. Existing reports below remain historical, not current acceptance.
[Full receipt](releases/2026-10-07-tcp-instrumentation-primary-1.md).

## ANDROID-HARNESS-ACCEPTANCE-1 — FAIL / mandatory TCP STOP (07.10)

Precommit repeats on the already-corrected harness produced PASS/PASS/FAIL.
The third run preserves `AssertionError` at TcpRuntimeTest.traffic:26 (HTTP200 /
body-suffix assertions), lifecycle caller:43. Historical TCP failure is no longer
non-blocking merely because earlier repeats passed; whether the cause matches the
older masked failure is unknown. No new TCP/harness/runtime change was made.
Review also found primary-preservation gaps in activity-finish and Auto duplicate
cleanup-exception handling; regression receipts retained, correction deferred.
NEXT: investigate the captured TCP primary before revising the harness or creating
a replacement validation SHA. No commit/tag/push/hosted rerun/sign/install/deploy.
RTP-IDENTITY-FREEZE-1 cannot resume acceptance or signing.
[Exact STOP and regression evidence](releases/2026-10-07-android-harness-acceptance-1.md).

## ANDROID-EMULATOR-NETWORK-1 — PARTIAL / hosted gate still closed (07.10)

Investigation of6d1bddaa recovered both artifacts and distinguished pre-test
emulator Wi-Fi routing failure from a first-packet VPN-readiness race. Beta68 and
beta69 normal Android/runtime/harness inputs are identical. Three test-only changes
pass forced control3/3 and final full instrumentation2/2 (41 reported,21 executed,
20 existing assumption skips each); no production behavior or release mutation.
Do not treat local overlay receipts as clean exact-SHA hosted acceptance.
NEXT: review the bounded test patch, establish a separately authorized validation
anchor and repeat BOTH original hosted lifecycle workflows including storage-restart,
control reporting and Client Friends acceptance. Preserve the earlier local TCP
cleanup-masked failure; it was not independently reproduced with primary reporting.
No sign/install/deploy/arm/physical run; RTP-IDENTITY-FREEZE-1 remains blocked for
promotion until those gates pass. No new commit/tag/push performed here.
[Evidence and remaining limits](releases/2026-10-07-android-emulator-network-1.md).

## RTP-IDENTITY-FREEZE-1 — PARTIAL / hosted Android lifecycle STOP (07.10)

Exact eleven-file replacement validation6d1bddaa passes all local/source-bound
gates, including the corrected mux on one core, RTP hop-local model and private
Reliable→ACK callback chain. Tagdiag-owner-beta69-ci1 targets that unchanged SHA.
Hosted15/17 PASS; Android diagnostic37597746736 and Client builds37597746771
fail at the emulator WG/AWG/TCP/Auto lifecycle step. Publication jobs skipped.
Do not sign, accept final freeze, install or deploy; no automatic CI retry.
NEXT: investigate those two failures using preserved job/step receipts and hosted
runtime artifacts. Artifact retrieval currently returnedHTTP403; root cause unknown.
Old763c3b3 remains historical; beta67/beta68 sealed pairs verified unchanged.
[Replacement scope, exact-SHA results and limitations](releases/2026-10-06-rtp-identity-freeze-1.md).

## TCP-MUX-SCHEDULING-1 — PASS / next exact-SHA anchor required (07.10)

TCP mux STOP diagnosed as a pre-existing single-core-sensitive test fixture,
reproduced on beta68 and beta69. Deterministic test-only slow socket correction
passes repeated CPU1/2/12 checks, race and full default Go suites; no production
source or beta69 RTP/callback changes. Existing validation SHA763c3b3 remains
unchanged but does not contain the fix. Do not promote it using overlay receipts.
NEXT: prepare a new narrowly scoped validation SHA with the accepted beta69 delta
plus this test-only correction, then repeat exact-SHA freeze acceptance.
No new commit/version/tag/push/artifact signing or runtime action in this task.
[Investigation and complete receipts](releases/2026-10-07-tcp-mux-scheduling-1.md).

## RTP-IDENTITY-FREEZE-1 — PARTIAL / Go acceptance STOP (06.10)

Storage recovery accepted; same SHA763c3b326c5710c39a7cbd681f4160d9ce8fb1f8 remains
clean/unpromoted. Fresh fixtures and full Python workflow PASS (1809/26 skipped).
Go default gate failed TestMuxSlowConsumerAndInteractive at mux_test.go212; no source
cause established and no source correction made. Later diagnostic/native/Android/CI
gates remain blocked. No tag/push/sign/runtime action; beta67/beta68 seals unchanged.
NEXT: offline investigation of this TCP mux assertion, including GOMAXPROCS=1
scheduling, before deciding whether the same SHA can resume acceptance.
[Exact receipt](releases/2026-10-06-rtp-identity-freeze-1.md).

## RTP-IDENTITY-FREEZE-1 — PARTIAL / fixture quota STOP (06.10)

Beta69/code69 isolated validation SHA763c3b326c5710c39a7cbd681f4160d9ce8fb1f8 exists;
not frozen/promoted. Exact ten-file scope excludes unrelated work. Required fresh
Go1.26.0 source-bound fixture build failed on disk quota after serial retry; default
Go/public golden and43 source guards PASS, diagnostic race build blocked by storage.
Beta68 final rehash PASS; exact callback matrix remains pending. Full
Python/native/Android/hosted CI/signing remain gated. No tag or push; no runtime action.
NEXT: restore build quota/storage and rerun fresh fixtures on this same clean SHA,
then complete every remaining acceptance gate before promotion/signing/deployment.
[Exact STOP](releases/2026-10-06-rtp-identity-freeze-1.md).

## RTP-IDENTITY-REWRITE-1 — PASS / local only (06.10)

Diagnostic-only cross-leg matcher correction and I1–I8 local regressions complete;
full default/public golden, diagnostic race, final sessiontrace race and43 source
guards PASS. RTP headers are retained separately per leg; stable carrier/frame
identity still strict, private ACK-token/write gate unchanged. DATA60 remote media
and carrier reconstruction now established offline, but missing receiver callbacks
cannot be reconstructed. Original physical task remains FAIL; no second run.
NEXT: review/freeze this scoped source correction through normal source-bound gates;
no deployment or new physical experiment is authorized by this local PASS.
[Exact results](releases/2026-10-06-rtp-identity-rewrite-1.md).

## OWNER-SELECTED-RETRY-BETA68-1 — FAIL / one authorized experiment consumed (06.10)

Fresh exact-byte/identity/authority/READY/unarmed preflight PASS. Exactly one owner
DATA60 attempt0 dropped; attempt1 actual RTP write and sender ACK/base61 pinned
COMPLETE, three modest DNS/full HTTPS/TCP requests passed without sampled session
change or terminal failure. Receiver carrier/PictureID matched, but remote RTP
timestamp/sequence differed from sender descriptor; BOUND→OVERFLOW prevented the
mandatory pinned receiver Reliable→ACK callback completion. Do not rerun this task.
Cleanup PASS: Android unarmed/no active generation, both watches CLEANED, gateway
directory empty, beta68 runtime/identity/config and beta67/beta68 seals unchanged.
NEXT: offline review of retained RTP-identity mismatch/overflow; no new physical test
or source mutation is authorized by this result.
[Exact evidence](releases/2026-10-06-owner-selected-retry-beta68-1.md).

### Historical pre-arm pause — resolved by user clarification

Zero experiments, fault arms or prearms. Deployed beta68 acceptance remains PASS.
Exact frozen source confirms ACK correlation token is private/unexported; pinned JSON
exports base/mask/created_ns/sent_ns/result, with exact private-token matching inside
the actual carrier-write callback. User asks for unique ACK token in mandatory pinned
evidence; no substitution of timestamps for token uniqueness made. Clarify whether
token-matched callback proof plus accepted source/CI is sufficient without token export
before consuming the one physical experiment. No runtime mutation or fresh full
runtime preflight yet; prior headroom is not treated as current.
NEXT: confirm that the private ACK token need not be exported for this physical task.
[Exact evidence-contract question](releases/2026-10-06-owner-selected-retry-beta68-1.md).

## PINNED-EVIDENCE-DEPLOY-2 — PASS / owner-only beta68 (06.10)

Resumed existing task under explicit loaded-bytes→sealed-manifest callback-schema
evidence clarification. Exact sealed beta68 installed in place and gateway loaded;
APK signer/JNI/normal native, gateway SHA/revision1abaa3a8 and manifest binding PASS.
UID10283/inode601521/Support ID/encrypted identity/enrollment/activation preserved.
Fresh beta68 READY/ACK plus two cellular restricted DNS/HTTPS/TCP/reconnect/cleanup
cycles PASS; app restart READY/ACK PASS. Android DUMP protection/status unarmed,
gateway UID/socket isolation and final empty directory PASS; no stale watch/generation.
Live credentials/RU-NL equality PASS; expiry 2026-10-06T23:48:47+00:00, headroom 12133s at
2026-10-06T20:26:33.437015+00:00. Gateway PID1401423/NRestarts0, config unchanged.
Beta67 rollback binary/APK and both sealed pairs retained unchanged. No public
publication, selected-retry experiment, intentional drop, fault/prearm or impairment.
NEXT: separately authorize the owner beta68 physical selected-retry task with fresh
headroom/control preflight; technically unblocked, not executed or armed here.
[Exact deployment, attribution and rollback receipts](releases/2026-10-06-pinned-evidence-deploy-2.md).

## PINNED-EVIDENCE-DEPLOY-2 — PARTIAL / runtime capability-reporting gate (06.10)

Resumed existing task after credential renewal; prior STOP/evidence retained.
Fresh sealed beta67/beta68 hashes PASS; Redmi remains beta67/code67, exact APK hash,
UID10283/inode601521, Wi-Fi OFF/cellular ON, status unarmed/count0. Credentials PASS:
served leaf expires23:48:47UTC, headroom 13732s at 2026-10-06T19:59:54.606516+00:00;
exact RU/NL directory/authority/CRL equality and unchanged grants/admission PASS.
Pre-install acceptance feasibility blocker: frozen beta68 has the accepted callback
implementation, but no read-only runtime report advertising pinned-reliable-callbacks-v1.
That label is a sealed artifact contract only. Fault status reports control schema1;
correlation status rejects without an existing prearm watch. No prearm used as a probe.
No beta68 installation/gateway replacement or baseline attempted with this unresolved
mandatory reporting gate. Freeze remains PASS; runtime callback inactivity is NOT claimed.
NEXT: obtain explicit acceptance of exact loaded-binary-to-manifest attribution as
callback-schema evidence, instead of the unavailable runtime capability report.
[Resumption evidence and remaining gates](releases/2026-10-06-pinned-evidence-deploy-2.md).

## GATEWAY-CREDENTIAL-RENEWAL-2 — PASS (06.10, credentials only)

Renewed expired gateway leaf/profile through accepted issuer/publication/bootstrap
procedure; issuer6 and owner3/tester1 grants unchanged and valid until07.10 14:45:31UTC.
Actual served leaf matches profile, signature/hostname/validity/non-revocation PASS;
limiting expiry 2026-10-06T23:48:47+00:00, headroom 13943s at 2026-10-06T19:56:23.678871+00:00.
RU/NL generation 2026-10-06T19:49:15.595849272Z and exact directory/authority/CRL match.
Fresh unchanged beta67 authenticated fetch 2026-10-06T19:55:09+00:00 → native READY →
ACK 2026-10-06T19:55:10+00:00. APK/UID/inode, gateway beta67 binary, diagnostic config,
admission/revisions/revocation/identity bindings and beta67/beta68 seals preserved.
No beta68 install/deploy, fault/prearm or physical experiment. Deploy2 remains PARTIAL.
NEXT: resume PINNED-EVIDENCE-DEPLOY-2 with fresh headroom/preflight checks, separately.
[Credential renewal and bounded evidence](releases/2026-10-06-gateway-credential-renewal-2.md).

VPN read-only checkpoint06.10 19:52–19:53UTC:7 transferring NL AWG devices,
0 RU;25 non-revoked devices in Friends DB. No CPU/RAM saturation in short samples.
Follow-up: investigate RU disk await70–105ms and peer-worker unhealthy/cycles/outbox;
longer monitoring and client E2E remain unverified. Public HTTPS renewal service
last completed successfully09:19:01UTC; served TLS not rechecked. This does not
clear restricted gateway credential STOP or authorize renewal/deployment/experiments.
No versions/configuration changed; no rollback needed for this audit.
[Metrics](releases/2026-10-06-vpn-health.ru.md#вечерняя-проверка-19521953utc).

## PINNED-EVIDENCE-DEPLOY-2 — PARTIAL / credential STOP (06.10 19:10UTC)

Sealed beta68 manifest/all members/package/signer/native provenance PASS; beta67
seals unchanged. Intended owner Redmi remains beta67/code67, UID10283/inode601521,
exact installed beta67 APK hash; Wi-Fi OFF/mobile data ON. No beta68 installation.
NL still loads exact beta67 gateway ffd27988, PID1266691/NRestarts0; accepted diagnostic
config unchanged, service-owned0700 directory empty. RU/NL directory hashes match.
STOP: actually served/profile gateway leaf expired18:47:30UTC; at19:10:52UTC effective
headroom was -1402 seconds. Issuer/grants/CRL remain future-dated, but do not rescue
the expired leaf. Existing beta67 READY/ACK is not beta68 readiness or valid TLS proof.
No renewal/install/deploy/arming/physical experiment; remaining deployment gates NOT RUN.
NEXT: perform a separate authority-runbook gateway credential renewal and verify the
actually served valid chain before resuming beta68 deployment.
[Preflight evidence and pending gates](releases/2026-10-06-pinned-evidence-deploy-2.md).

## PINNED-EVIDENCE-FREEZE-2 — PASS (06.10, test-only correction / ci2)

New exact validation source `1abaa3a8a9ba8ad9fa2a71c126620175b713c321`, parent46c9c77, changes only the profile
test to parse INI directives; no runtime/profile-generation/crypto/transport changes.
Ten8-test suites,1000 repeated generated-profile checks and28 orchestrator tests PASS.
Fresh source-bound Python/native/Android/Go/forensic/default-isolation acceptance
rerun on the new SHA; see report for exact results. New CI-only tag diag-owner-beta68-ci2;
ci1/failed receipts remain unchanged. Hosted CI 17/17 success.
Signed immutable beta68 pair: created after full CI and artifact verification.
Beta67 eight seals and unrelated work preserved. No install/deploy/renew/READY/arming.
NEXT: Start a separately authorized beta68 owner-only pair deployment using the sealed manifest; do not run a physical selected-retry experiment in that step.
[Final receipts, scope, hashes and limitations](releases/2026-10-06-pinned-evidence-freeze-2.md).

## PINNED-EVIDENCE-FREEZE-2 — FAIL (06.10, authorized validation checkpoint)

Single isolated validation commit `46c9c77e3f1dbed684d8a2d6c395030696deab09` contains only the accepted23 Go files
plus ownerDiagnostic beta68/code68 version override. Baseline ffd27988468fba427aaba6213b862dca01020972;
unrelated dirty/untracked work preserved. Exact-SHA fixtures and full Python1804 PASS/
26 skipped; Go default/diagnostic-race and full Reliable-to-actual-ACK chain PASS.
Native provenance/arm64/NDK PASS; Android258+258 tests, both lints, standalone JVM,
package/native hashes and DUMP/default isolation PASS. Unchanged SHA promoted only
after all local gates, CI-only tag diag-owner-beta68-ci1 pushed, no release branch.
Hosted CI: 12/17 success; final result FAIL.
STOP: phase0/failover Docker pytest failed on the profile test's arbitrary Jc substring
check (random synthetic PrivateKey collision), not the pinned callback regression.
No signing, immutable pair or automatic CI rerun; exact frozen source/tag retained.
Sealed beta67 eight files unchanged; nothing installed/deployed/renewed/READY/armed.
NEXT: Authorize a narrow correction to the randomized-profile Jc assertion in test_orchestrator_restricted_acceptance.py, followed by a newly reviewed exact-SHA validation cycle; no automatic source change or additional commit.
[Exact scope, CI, provenance, artifacts and limitations](releases/2026-10-06-pinned-evidence-freeze-2.md).

## PINNED-EVIDENCE-FREEZE-2 — PARTIAL / validation-commit ordering blocker

Fresh exact-handoff default/diagnostic-race, full Reliable-to-actual-ACK-write receiver
regression, local Pion/ACK matrices,43 source guards and host JNI/Java routing PASS.
Scope is exactly23 accepted Go files on ffd27988468fba427aaba6213b862dca01020972;
1818-file source inventory and explicit future version/docs allowlist retained.
Beta67 eight seals unchanged; beta68/code68 remains requested only, not a build.
Before proceeding, authorize an isolated validation commit before full local gates:
the mandatory Python fixture procedure archives HEAD and binds fixtures to that SHA.
Current all-gates-before-commit order cannot produce exact candidate fixtures.
Then rerun source-bound Python and native/Android gates, freeze only on PASS,
use a new CI-only tag, require hosted CI, and sign/seal a new pair. No deployment,
publication, credential renewal, READY, arming or physical experiment in this task.
[Freeze2 evidence and limitations](releases/2026-10-06-pinned-evidence-freeze-2.md).

## PINNED-RELIABLE-CALLBACKS-1 — PASS / ready for separate source freeze

Receiver media completion and full forensic completion are distinct. Exact carrier
identity survives Recv into Reliable callbacks; before/after receive state and first
selected consumption ACK are pinned. ACK completion requires actual carrier-written
RTP success, not SendContext queue acceptance. No wire/retry/pacing/buffer policy change.
Full default and diagnostic race, local Pion/ACK, R1–R14, public beta66 golden,
43 source guards and JNI/Android control routing checks PASS. Clean23-file source
delta and unsigned1818-file source archive retained; sealed beta67 unchanged.
NEXT: freeze a new immutable candidate separately (new version/tag, not beta67 reuse).
No automatic install/deploy/physical run; deployed beta67 retains the old limitation.
[Source acceptance handoff](releases/2026-10-06-pinned-reliable-callbacks-1.md).

## OWNER-PINNED-EVIDENCE-1 — PARTIAL / receiver retention blocker

Authorization received, fresh owner/gateway/authority/readiness/unarmed preflight PASS.
No physical run consumed. Frozen beta67 correlation receipt retains media identity,
not exact receiver Reliable/ACK callbacks; legacy rx watch deliberately rejected.
Do not substitute ordinary ring samples or media COMPLETE for full callback proof.
Deployment acceptance remains intact but does not establish this stronger evidence gate.
NEXT: separately authorize diagnostic-only receiver callback pinning/export and a new
immutable acceptance; do not modify sealed beta67 or execute the one fault run now.
[OWNER-PINNED-EVIDENCE-1 STOP](releases/2026-10-06-owner-pinned-evidence-1.md).

## PINNED-EVIDENCE-DEPLOY-1 — PASS (06.10, remaining gates complete)

Owner-only exact beta67 installed and gateway deployed; UID/data/Support/identity/
enrollment preserved. Authorized config change limited to diagnostic directory env;
all other effective/static service settings unchanged. Runtime directory0700/socket0600
UID/GID979, wrong-UID rejection and status-only access verified; cleanup empty/unarmed.
Fresh beta67 authenticated READY15:59:16UTC/ACK15:59:17UTC, normal cellular restricted
DNS/HTTPS/TCP/reconnect/cleanup and restart PASS. RU/NL generation15:53:17.577994843UTC,
hash0c160f8b… equal, actual TLS effective bound18:47:30UTC; final measured headroom
9961s at16:01:28UTC. Beta66 rollback retained; public/default channels unchanged.
No remaining deployment gate; no physical evidence/fault/prearm/impairment performed.
NEXT: obtain separate owner physical-evidence authorization, with fresh headroom and
empty/unarmed preflight before that task; do not automatically arm or begin impairment.
[Deployment evidence and limits](releases/2026-10-06-pinned-evidence-deploy-1.md).

Earlier STOP/PARTIAL sections below are historical, superseded by this acceptance.

## PINNED-EVIDENCE-DEPLOY-1 — PARTIAL (06.10, diagnostic configuration conflict)

Fresh post-renewal owner preservation/exact beta66 and sealed beta67 checks PASS.
Credentials/RU-NL PASS15:11:54UTC, headroom12935s until18:47:30UTC, CRL9368.
Live gateway environment lacks FC_DIAGNOSTIC_CONTROL_DIR; exact frozen beta67 code
returns without creating any control socket when unset. Cannot meet socket readiness
while also preserving all service configuration unchanged. No beta67/runtime changes.
NEXT obtain narrow exception for this ownerDiagnostic environment variable and its
service-owned0700 directory, then resume remaining deployment gates with fresh guards.
Do not treat idle UNAVAILABLE or missing socket as full safe-control/stale-state PASS;
do not run a physical evidence/impairment task. No fault/prearm was sent.
[Resumption details](releases/2026-10-06-pinned-evidence-deploy-1.md).

## AUTHORITY-RENEWAL-1 — PASS (06.10, beta66 retained)

Accepted expired-parent recovery завершён: same-key issuer6 signed offline under
existing control root, grants3/1 сохранены, minimum revision1, CRL floor9323→9330.
RU/NL exact directory SHA256303ac422…; served leaf verified through18:47:30UTC.
Headroom14211s at14:50:38UTC. Owner beta66 ordinary fresh READY14:49:38/ACK14:49:39UTC.
No APK/binary deployment, no security relaxation, no fault/prearm/physical experiment.
NEXT resume only PINNED-EVIDENCE-DEPLOY-1 with fresh owner/headroom/control preflight
and all remaining deployment gates. Do not treat renewal as beta67 deployment PASS
or permission to begin owner physical evidence/impairment. No automatic continuation.
[Authority chain, rollback boundaries and evidence](releases/2026-10-06-authority-renewal-1.md).

## PINNED-EVIDENCE-DEPLOY-1 — FAIL / STOP credentials invalid (06.10, resumed)

ADB prerequisite resolved and mandatory owner preservation preflight PASS:
beta66/code66, exact accepted APK/signer, UID10283/inode601521, Support/identity/
enrollment/activation unchanged; RU admission non-revoked/revision3. Sealed beta67
recheck PASS. New STOP: issuer/grants/CRL expired13:51:23UTC, NL profile leaf
expired11:03:25UTC; actual TLS probe returned no chain. Equal RU/NL directory does
not establish valid authority. No beta67 install or gateway replacement occurred.
NEXT restore valid authority/grants/CRL/gateway credentials through the accepted
renewal procedure, then resume deployment with fresh preflight; never bypass issuer
validation for leaf-only renewal. Existing credential-only operator requires valid
issuer/grants and cannot safely cover this expired-authority state.
READY/ACK, cellular baseline, control/stale-state and live rollback acceptance remain
open. Separate physical evidence/impairment task NOT allowed.
[Resumed evidence](releases/2026-10-06-pinned-evidence-deploy-1.md).

## PINNED-EVIDENCE-DEPLOY-1 — PARTIAL (06.10, owner ADB unavailable)

Immutable beta67/code67 local verification PASS at14:12:04UTC: manifest/all7 files,
signer, embedded JNI/AWG, revisionffd27988468fba427aaba6213b862dca01020972,
schemas/non-debuggable/arm64-only. beta66 rollback APK/gateway retained locally.
At14:12:18UTC approved outside-sandbox ADB reports zero devices. No owner preflight,
install, gateway replacement, renewal, fresh READY/ACK, restricted baseline or
runtime control/stale-state acceptance. No physical experiment or public changes.
NEXT: reconnect/authorize owner31ce63ba in ADB, then resume this deploy from owner
preflight with fresh immutable checks. Remaining gates and rollback constraints:
[PINNED-EVIDENCE-DEPLOY-1](releases/2026-10-06-pinned-evidence-deploy-1.md).
Do not start a separate evidence/impairment task until deployment acceptance PASS.

## PINNED-EVIDENCE-FREEZE-1 — PASS (06.10, beta67 candidate only)

После принятого DIAGNOSTIC-TELEMETRY-ISOLATION-1 выполнен полный повтор freeze.
Чистый scoped source `ffd27988468fba427aaba6213b862dca01020972`; CI-only tag `diag-owner-beta67-ci1`.
Source-bound Python3.13.16/Go1.26.0:1804 passed,26 skipped; fixtures exact HEAD PASS.
Go default/diagnostic race, correlation/Pion/late-original/retention2000+/isolation,
arm64 NDK28.2/Go1.26.1 JNI+AWG/TCP, host-cgo/JVM, Android258+258 unit/lint,
privacy/source/provenance gates PASS. Все17 hosted workflows PASS; publication jobs
skipped. Скачана/проверена CI-пара и подписан ownerDiagnostic0.1.18-beta67/code67,
package com.familyconnect.app.friends, совместимый signer, non-debuggable,arm64-only.
Immutable manifest SHA256 `98dabfa38cb2cd437b5ec45700e936da3ae0b94ef47f11b8904a90faa472fc77`.
Pair: state-client-build/field65-export16/pinned-evidence-freeze-1/immutable-ownerDiagnostic-beta67/.
Sealed beta66:5/5 SHA256 unchanged. Root HEAD8d046321/посторонняя dirty-работа сохранены.
Ничего не installed/deployed/READY/renewed/armed; Telemost/soak/impairment/Краснодар
не запускались. Default/catalog/invitation channels нетронуты. DATA104 не исправлялся.
NEXT отдельная owner-only deploy-задача из immutable manifest; не автоматический запуск.
Физический OWNER-CONTROLLED-LOSS-1 остаётся FAIL/UNKNOWN; DATA19 recovery не перепроверяется.
[Source, CI, hashes, signing, rollback и ограничения](releases/2026-10-06-pinned-evidence-freeze-1.md).

## DIAGNOSTIC-TELEMETRY-ISOLATION-1 — PASS (06.10, только исходники/локальные тесты)

Закрыт default telemetry blocker freeze: Boundary/Snapshot/Delivery и список stages
разделены compile-time по fc_owner_diagnostic. Default JSON surface совпадает с golden
из sealed beta66; PictureID/watch-полей в default типах нет. Новые consume/base hooks
и PictureID setter имеют no-op stubs; watch storage/default hooks пустые.
Diagnostic сохраняет forensic stages, PictureID, watch/provisional/descriptor evidence.
Go default ./..., diagnostic race ./..., Pion/correlation/late-original/retention2000+,
двойные schema/byte regressions и65 scoped Python privacy/source tests PASS.
Correlation implementation, Reliable/VP8/RTP algorithms не менялись; DATA104 не тронут.
HEAD8d046321 и sealed beta66 неизменны, посторонняя dirty-работа сохранена.
Версии/артефакты/подпись/CI/freeze/install/deploy/credentials/physical arm отсутствуют.
NEXT: отдельный повтор PINNED-EVIDENCE-FREEZE-1 с source-bound Python fixtures,
полными NDK/Android/CI/signing gates. Сам freeze пока остаётся FAIL исторического
запуска, не принят автоматически. Runtime rollback не требуется; физический gate
OWNER-CONTROLLED-LOSS-1 остаётся FAIL/UNKNOWN, DATA19 recovery не перепроверяется.
[Таблица путей, контракты, тесты и Python environment](releases/2026-10-06-diagnostic-telemetry-isolation-1.md).

## PINNED-EVIDENCE-FREEZE-1 — FAIL (06.10, STOP до freeze/build)

Предварительная проверка чисто выделенного scope обнаружила нарушение default/public
isolation: `reliable_consumed`, `base_advanced` и PictureID metadata добавлены в
обычный boundary export без diagnostic build gate. Новый executable default-тест
подтвердил все три случая; прежняя проверка no-default-endpoint этого не покрывала.
Утверждение предыдущего gate «нет дополнительной default telemetry» опровергнуто.
Корреляция late-original/attempt1, Pion, retention2000+ и tagged Go race проходят;
это не устраняет блокер изоляции. Согласно stop condition исправление/выпуск здесь
не продолжены. HEAD8d046321 неизменен; изолированная копия от5327deb4 содержит только
allowlist и тесты. beta67/code67 — лишь неподписанная настройка исходника, не артефакт.
Freeze-коммита, тега, новых APK/JNI/gateway, CI, подписи и pair manifest нет.
Sealed beta66: все пять файлов повторно проверены SHA256, без изменений.
Ничего не установлено/развёрнуто/armed, credentials не обновлялись; DATA104 не менялся.
NEXT: отдельное scoped исправление diagnostic-only gating новых boundary stages и
PictureID с регрессией default telemetry; затем повторная полная freeze-приёмка.
Развёртывание нового кандидата запрещено. Runtime rollback не требуется.
[Доказательства, исходники и результаты](releases/2026-10-06-pinned-evidence-freeze-1.md).

## PINNED-EVIDENCE-CORRELATION-1 — PASS (06.10, исходники/локальные тесты)

Закрыта ambiguity late attempt0: receiver больше не завершает watch по одному seq.
Новый schema1: bounded provisional capture4 identities×8 fragments, затем один
OS-authenticated descriptor с session/direction/seq/attempt/128-bit generation и
точными carrier/PictureID/RTP полями всех fragments. Legacy rx API отвергается.
Gateway control — opt-in diagnostic Unix socket0700/0600+SO_PEERCRED; Android —
существующий ownerDiagnostic DUMP receiver/JNI. Default arm/bind/endpoint отключены,
дополнительной default telemetry нет. TTL30s/cleanup/close очищают evidence;
stale/replay/wrong-key и смешивание fragments отвергаются. Reverse104 не исправлялся.
Default Go, diagnostic race, local Pion single/multi/reorder/duplicates, ACK и
retention2000+,13 Python privacy/bounds/source guards, JVM и host-cgo routing PASS.
Host tests не являются Android/NDK runtime acceptance. RTP/wire/retry/ACK/Family TLS
semantics не изменены. Нового commit/source freeze/APK/JNI/gateway/signing/CI rollout
нет; sealed beta66 не тронут, credentials/физический fault/Telemost не запускались.
OWNER-CONTROLLED-LOSS-1 остаётся FAIL/UNKNOWN; DATA19 recovery не перепроверяется.
NEXT отдельная задача чистого scoped candidate freeze и полной приёмки; не
автоматическое разрешение сборки/развёртывания/физического эксперимента здесь.
Предыдущий полный candidate gate остаётся PARTIAL до отдельной приёмки всех stages.
Runtime rollback не требуется; откат только scoped source delta, не всего dirty tree.
[Контракт, threat boundary, матрица C1–C13 и ограничения](releases/2026-10-06-pinned-evidence-correlation-1.md).

## PINNED-EVIDENCE-CANDIDATE-1 — PARTIAL (06.10, preparation only)

Read-only inventory classified82 dirty files against sealed5327deb4; existing
implementation/unrelated work preserved. Default Go, diagnostic race, local Pion
single/multi-fragment retention after2000 boundaries and10 privacy/bounds/packaging
checks PASS. Exact receiver prearm acceptance FAIL: only an in-process API exists,
no session/generation-bound runtime endpoint; receiver binds first carrier identity.
Executable local counterexample: attempt1 watch completes on late attempt0 and
ignores the selected retry after COMPLETE. No complete per-fragment stage chain,
explicit purge/generation lifecycle or separate reverse104 evidence channel yet.
STOP before freeze/build: requires reviewed diagnostic-only prearm/descriptor design,
not a production payload/Family TLS change. No candidate commit/artifacts/version,
CI publication, install, deployment, credential renewal or physical experiment.
Sealed beta66 pair untouched; original physical FAIL/UNKNOWN unchanged; DATA19
protocol recovery is established and was not re-proved. No runtime rollback needed.
NEXT review/authorize bounded provisional matching and authenticated prearm design;
future physical experiment is NOT evidence-ready.
[Inventory, contracts, test limits and smallest required design](releases/2026-10-06-pinned-evidence-candidate-1.md).

Operational audit06.10 08:05–08:07UTC completed without service changes:
29 activated/25 non-revoked devices;5 recently active NL AWG peers; no snapshot
CPU/RAM saturation. Follow up cert-renew timeout before public TLS expiry
09.10 00:25:32UTC, peer-worker unhealthy/outbox and later SSH banner timeout.
HTTPS8443 monitor200/TLS valid; no claim of client E2E or new release acceptance.
No rollback needed; existing restricted priority/gates below are unchanged.
[VPN health report](releases/2026-10-06-vpn-health.ru.md).

**06.10 SELECTED-RETRY-EVIDENCE-GAP-1 PASS; offline investigation complete.**
1. DONE inventory/hash-check37 preserved experiment files and reconstruct local-index/
   UTC chronology. Exact selected remote RTP record remains unrecovered.
2. DONE prove DATA19 acceptance/ordered consumption and ACK generation by protocol
   semantics; distinguish proof from missing concrete receiver callbacks/timestamps.
3. DONE quantify RING_EVICTION:64-slot receiver ring,1606 insertions between exports,
   1542 unseen indices. No transport-loss inference from absent snapshots.
4. DONE separate reverse104 pre-cleanup gap/post-cleanup exhaustion; no lifecycle fix
   or attribution to DATA19. Original physical FAIL/UNKNOWN remains unchanged.
5. DONE local opt-in pinned-watch metadata patch, actual consume/base boundaries,
   PictureID capture, default-disabled tests, local bound-Pion single/multi-fragment
   chain with2000 later events, ACK proof and tagged race regressions.
6. NEXT separate review/candidate preparation of the two-sided watch prearm/export
   contract. No current physical rerun, fault arm, deployment, tuning or tester contact.
[Analysis and minimal patch](releases/2026-10-06-selected-retry-evidence-gap-1.md).

**06.10 OWNER-CONTROLLED-LOSS-1 FAIL / UNKNOWN; supersedes experiment-next below.**
1. DONE fresh exact-pair/identity/admission/TLS/directory/READY/cellular/unarmed
   preflight; one real owner session, one outbound DATA19 attempt0 drop only.
2. DONE remote head gap19/mask254/buffered7, attempt1 creation/carrier/RTP writer,
   returned cumulative ACK/base progression and HTTPS/DNS/TCP continuity proven.
3. NOT PROVEN selected attempt1 remote RTP/VP8/carrier/Reliable boundaries and
   healing ACK generation: bounded gateway rings are incomplete, not packet-loss proof.
4. FAIL strict no-exhaustion condition: gateway reverse head104 retry exhaustion
   at07:28:24.478UTC, after explicit client cleanup07:28:16.020UTC. Classification
   UNKNOWN; no earliest missing DATA19 transport stage is proven.
5. DONE auto-disarm/count1, cleanup/restart unarmed, helper removal, identity and
   exact APK retained; gateway PID1000816/NRestarts0, no restart/rebuild/tuning.
6. NEXT separate investigation of selected retry remote receive-boundary evidence
   gap only. No repeat fault, soak, impairment, Krasnodar or public beta66 promotion.
[Single-experiment report](releases/2026-10-06-owner-controlled-loss-1.md).

**06.10 DIAG-PAIR-DEPLOY-1 PASS; supersedes the deployment-next-step below.**
1. DONE exact sealed beta66 installed in place; UID10283/Support/identity/enrollment
   retained, no owner uninstall/data clear/reactivation; exact matching NL gateway loaded.
2. DONE bounded JIT renewal, unchanged issuer5/grants/admission; actual TLS readback,
   native validation, RU/NL equality and fresh beta66 READY/ACK accepted.
3. DONE short cellular real restricted DNS/HTTPS/TCP sessions ×2, reconnect/cleanup,
   restart and schema1 DISARMED receipts; no injected loss or policy change.
4. DONE rollback binary and beta65 preserved, downgrade limitations documented;
   only temporary instrumentation removed, production unit/public channels unchanged.
5. NEXT OWNER-CONTROLLED-LOSS-1 is allowed separately, not executed. Recheck live
   READY, effective headroom and DISARMED before any later authorized arm. Current
   hard bound06.10 11:03:25UTC; no indefinite READY/window guarantee.
[Deployment report and exact receipts](releases/2026-10-06-diag-pair-deploy-1.md).

**06.10 DIAG-SOURCE-FREEZE-1 PASS; previous STOPs below are superseded.**
1. DONE fresh pinned normal AWG/TCP build, exact be122bb3 source hash, complete
   normal/restricted APK provenance and P1–P7 acceptance without verifier changes.
2. DONE clean scoped commit5327deb414ae8aa77ce2f9490fd99c9485eba740;
   diag-owner-beta66-ci2, all17 hosted workflows PASS; main/excluded work preserved.
3. DONE downloaded/verified CI native/gateway/APK, offline existing compatible signer,
   immutable beta66/code66 pair manifest; no install/deploy or public distribution.
4. NEXT DIAG-PAIR-DEPLOY-1 is allowed to START separately with sealed-manifest review.
   This source-freeze task performs no credentials/READY/arming/physical/soak/tester action.
5. Preserve public beta65/default/catalog/invitation. Raw native bit-reproducibility
   limitation is documented; no hash relabeling or security/runtime changes.
[Final pair and acceptance receipts](releases/2026-10-06-normal-native-provenance-1.md).

**Previous06.10 OWNER-DIAGNOSTIC-PACKAGING-1 FAIL (superseded).**
1. DONE owner-only JNI/assets composition, independent generated directory and byte
   preservation; no default/public source-set change.
2. DONE clean local candidate02f7eb9, fresh owner/default JNI, unsigned APK builds,
   both258 unit tests/lint, merged-manifest isolation, restricted P1–P7 PASS.
3. STOP mandatory normal-native APK verifier: tcp_source_sha256 mismatch between
   reused AWG metadata f5ec5e49 and exact scoped TCP source be122bb3. Do not freeze,
   sign, publish or promote these artifacts; candidate is not accepted release source.
4. NEXT fresh authoritative normal AWG/TCP generation from exact scoped source;
   rerun complete APK provenance without weakening checks, then resume freeze gates.
5. DIAG-SOURCE-FREEZE-1 PARTIAL; no pair manifest. DIAG-PAIR-DEPLOY-1 NOT allowed.
   Preserve all prior source inventory, timing PASS, unaffected Go/Python receipts,
   excluded work, public bytes and all no-runtime-operation restrictions.
[Packaging report and precise input table](releases/2026-10-06-owner-diagnostic-packaging-1.md).

**Previous06.10 checkpoint: PARTIAL; superseded above.**
1. DONE NATIVE-AUTHORITY-TIME-1 PASS: mixed isolated20/20 delta-4s; delayed5/5
   delta-4s; module isolation proves excluded restricted.py issuance cap. JSON/native
   retain exact absolute expiry, rejecting at expiry; no new tolerance or runtime fix.
2. DONE isolated baseline8d04632 +32 allowlisted diagnostic files, excluded control
   work untouched: unchanged failing test20/20 PASS, compatibility19 PASS ×3,
   full Python1793 PASS/26 skipped. No blanket Android/Go/race rerun needed.
3. NOT_READY next packaging preflight: Gradle ownerDiagnostic JNI/assets inputs omit
   Friends restricted-generated paths; no restricted library/build metadata in its
   resolved inputs. initWith does not copy source sets. No APK build attempted here.
4. NEXT explicitly integrate newly built owner-tagged JNI/schema1/source-revision
   metadata with ownerDiagnostic, preserving default Friends inputs. Verify affected
   Android/packaging gates; then guarded scoped freeze, hosted CI, accepted native/
   gateway/APK, offline signer verification and immutable pair manifest.
5. Draft beta66/code66 only; no commit/push/candidate build/signing/install/deploy,
   credentials/READY/phone arming/physical Telemost/soak/tester contact/public change.
   DIAG-PAIR-DEPLOY-1 is NOT allowed. Do not merge excluded control changes to make
   the mixed workspace green; its compatibility file still has2 deterministic failures.
[Timing contract, trace and source isolation](releases/2026-10-06-native-authority-time-1.md).

Previous04:52UTC checkpoint, superseded by the result above:
1. DONE pre-edit53-path hash inventory and21-path existing diagnostic allowlist;
   resumed scoped hashes match STOP, unrelated work preserved, no staging/commit/push.
   Mixed docs still need hunk selection; previous inventory and receipts retained.
2. DONE restored removed toolchains after quota cleanup. Fresh ownerDiagnostic258
   tests/lint, default Friends258 tests/lint, JVM171, native packet race, Go full/default
   race/diagnostic race, F1–F6/runtime retry, A–E and default-disabled regression PASS.
3. STOP correctly provisioned Python full gate:905 passed/26 skipped/1 failed,
   test_long_testing_window_preserves_native_expiry_checks, now+3595 != now+3599.
   Mixed working-tree execution includes excluded readiness/control edits; not a
   clean-scoped acceptance result. Do not weaken assertions or absorb unrelated work.
4. NEXT resolve failure/source-scope attribution, then rerun required acceptance on
   isolated allowlisted source; verify privacy/default binary/packaging, guarded scoped
   commit, exact-source hosted CI, accepted JNI/gateway and offline-signed matching APK.
   No freeze/CI/candidate builds/signing undertaken after the assertion STOP.
5. Generated ownerDiagnostic manifest/BuildConfig confirm beta66/code66; default65.
   No accepted immutable successor, artifact hashes or pair manifest. Preserve required
   signer67a90d1b; pair must bind commit/APK/signer/JNI/gateway/schema1/test-CI receipts.
   DIAG-PAIR-DEPLOY-1 is NOT allowed to start. No deployment/renewal/READY/phone fault,
   physical Telemost/soak/Krasnodar contact or public-channel change in this task.
[Scope, receipts and remaining checks](releases/2026-10-06-diag-source-freeze-1.md).

**06.10 DIAG-PAIR-PREP-1: PARTIAL; supersedes the NEXT authorization below.**
1. DONE read-only installed APK/signer/JNI and diagnostic artifact hash checks;
   observed NL served TLS, PID/restarts, RU/NL generation and owner receipt.
2. STOP artifact gate: unsigned diagnostic APK; dirty-source exact CI provenance
   not established, no accepted install-compatible signed diagnostic artifact.
   Existing physical one-shot control not demonstrated (only unit-test fixtures).
3. NEXT freeze/reconcile exact diagnostic source and obtain required artifact
   acceptance/signing gates without replacing public beta65. No commit/publication
   was made by prep. Implement/accept any missing disabled test-only control in
   that exact source; do not silently mix it with the old accepted artifact hashes.
4. Only after those gates: preserve owner UID/data/identity in-place, verify matching
   NL loaded binary and rollback, JIT renew under the existing runbook, compare
   RU/NL and full effective bound, obtain fresh ordinary fetch/import/READY/ACK.
5. Then security/normal-path and preservation checks; no fault/soak/FIELD within prep.
   OWNER-CONTROLLED-LOSS-1 cannot start on current evidence.
[DIAG-PAIR-PREP-1 evidence and unperformed gates](releases/2026-10-06-diag-pair-prep-1.md).

**06.10 OWNER-CONTROLLED-LOSS-1 supersedes the authorization NEXT below.**
1. DONE owner-only authorization and read-only preflight: owner65/UID10283 on
   cellular, admitted/non-revoked; local diagnostic hashes verified.
2. STOP before runtime changes: actual NL leaf expired05.10 23:53:04UTC,
   headroom-13282s at03:34:25UTC; owner READY receipt expired. RU/NL directory
   equal is insufficient. Current PID779376/NRestarts1, intervening cause unknown.
3. NEXT finish safe diagnostic-pair preparation: durable scratch/evidence despite
   observed /tmp quota errors, exact dirty-source provenance, separate diagnostic
   build, installed signer compatibility and UID/data preservation, bounded
   one-shot attempt0-only injection/evidence retention, required regressions.
4. Then existing runbook JIT renewal without floor/admission/TTL weakening, actual
   loaded chain/readiness and RU/NL generation verification; only then owner
   real-Telemost physical gate. No remote missing transport stage proven yet.
5. Only after controlled-loss PASS:15-minute owner cellular soak without faults;
   stop on spontaneous hole with paired evidence, never mask with reconnect.
No runtime/code change, no renewal, no publication, no Krasnodar trial.
Result PARTIAL/preflight STOP; root cause STILL UNKNOWN.
[Exact evidence and remaining checks](releases/2026-10-06-owner-controlled-loss-1.md).

**06.10 FIELD65-DATA-HOLE-1 supersedes the NEXT actions in the history below.**
1. DONE audit before code edits; retry preserves FRS1 sequence/epochs/bytes but
   allocates new carrier ID, VP8 PictureID/timestamps and RTP sequence ranges.
   Old export16 per-attempt rows stay UNKNOWN; no network/SFU/DPI verdict.
2. DONE A–E local regressions for DATA48/58 and attempts0..8, including bound
   Pion packetization, missing head/later SACK, carrier/frame loss, duplicate and
   late original, byte-exact release/ACK/base progression without restart.
   Existing healed-gap assertions unchanged. Full Go/race14 packages PASS;
   actual local PeerConnection interceptor/207 byte-exact checks PASS.
3. DONE bounded privacy-safe stage ring and sender attempt propagation; Android
   projection/JVM11 and Python32 checks PASS; native packet race PASS.
   Local ARM64 JNI/gateway builds PASS, no install/publication. Isolated Friends
   Gradle258 tests PASS, lint0 errors/37 warnings, unsigned ARM64 APK PASS;
   packaged JNI hash verified, scoped source secret scan23 files PASS.
4. NOT DONE owner-device controlled one-head loss with preserved HTTPS and no
   session restart. This requires separately authorized diagnostic client/gateway
   use; do not consume another Krasnodar window or treat reconnect as a fix.
5. BLOCKED FROM RELEASE by remaining owner acceptance and subsequent ordinary
   exact-source CI/artifact/security gates. No immutable successor/tag/catalog
   changes, production deployment, retry/RTO/pacing tuning or TLS/Mux/TUN edits.
Root cause **STILL UNKNOWN**. Single next step: authorize owner-only controlled
loss acceptance after local product gates; capture target attempt without ring
eviction and pair it by session/message/fragment, not cross-host RTP numbers.
[Audit, implementation and exact receipts](releases/2026-10-06-field65-data-hole-1.md).

**Resumed05.10: finish on the existing Family Connect app.** Separate diagnostic APK
cancelled; no tracked changes remain from that branch. Server clock-skew correction
passes131 source/native checks against unchanged beta65 validation. Current progress:
1. DONE exact package295 and actual HTTP artifact2 checks; failed mixed-fixture run retained.
2. DONE renew expired issuer4 to same-key/root-authorized issuer5; preserve admission,
   owner3/tester1 revisions, CRL floors, ordinary services and valid rollback.
3. DONE activate HTTP43b99783/sync9faaa1c2 and verify actual runtime/TLS/materials.
   Unchanged owner65 gets fresh native READY/ACK13:56:08 from ordinary foreground;
   no APK of any kind installed. Gateway05571644 and ordinary AWG/TCP unchanged.
4. DONE tester65 fresh READY/ACK14:09:44UTC (fetch14:09:43), verified14:11:35.
5. DONE export14 mobile attempt: two Telemost sessions carry DNS/TCP bytes;
   automatic restoration succeeds in73.657s after the first genuine exhaustion.
   Both sessions still fail after roughly20s. Matched complete gateway traces
   show client DATA62/117 missing at receive_next, with later packets buffered.
6. DONE local RTP reorder regression/fix: new gap must not inherit an expired
   earlier gap timer. Baseline four ordering cases and carrier-byte test RED;
   fixed100 repeats/full native race PASS (395 passes,13 opt-in/helper skips).
   This is a proven local defect, NOT proof of field causality or a deployed fix.
7. DONE scoped RTPd678773/non-forced roadmap merge8d04632; exact-source
   phase037329376362/Clients37329375594 PASS; artifact/source/ELF/hash accepted.
   Gateway7c6e1e11 deployed15:22UTC; bootstrap READY, loaded bytes/chain, RU/NL
   directory32fdb3ef and unchanged ordinary services/admission/catalogs verified.
   Same installed owner65 native READY/ACK15:23:05 for new directory PASS; no test
   APK or product APK installed. Previous05571644 executable preserved for rollback.
8. FIELD TRIAL COMPLETE, stability FAIL (export16): two post-fix Telemost sessions
   carry traffic, then fail after about20s; first restoration succeeds84.446s.
   Paired105+57 gateway traces confirm client DATA48/58 missing with later DATA
   buffered; 8 retries, ACKs still received,8s no progress. RTP timer fix insufficient.
   NEXT local packetization/reorder/VP8 reproduction and bounded pre-reorder versus
   frame-discard evidence; no identical field retry or guessed timeout increase.
   Exact-candidate acceptance before another tester trial. No source/runtime change
   in export16 analysis; accepted7c6e1e11/PID652351 remains loaded, no restart.
   Preparation history: tester65 fresh fetch19:59:59/native READY ACK20:00:00UTC
   confirms renewed post19:53 directory (grant1/CRL7360), verified20:03:32.
   This enabled the trial now captured in export16, not a new pending readiness gate.
   Export15 failure19:40–19:41 predates renewal: expired-material local NOT_READY,
   no Telemost session. Earlier AWG/DNS success is not restricted acceptance.
   Tester did obtain fresh post-deploy READY/ACK15:31:34, before deferring again;
   no mobile trial started. That ACK predates the evening renewal and is not current.
   No reinstall, manual clocks, separate test APK or retry loop. Native/CI and owner
   import acceptance do not prove restricted field stability; no new forced owner
   restricted session/instrumentation trial was performed. Target uplink receiver first.
   DONE credential-only four-hour renewal15:38, same issuer5/grants/keys/binary;
   native/ownership/loaded TLS/stability/RU-NL generation and ordinary invariants PASS.
   That window expired before resumed19:44UTC checks. Tester READY19:36:49 also
   expired; do not reuse it. DONE credential-only renewal19:53UTC, CRL7347;
   native/loaded TLS/35s stability PASS, PID652351/NRestarts0, RU/NL4aa5ff38 equal.
   New actual gateway ceiling05.10 23:53:04UTC/06.10 02:53:04 Krasnodar.
   Final runtime readback19:54:12 PASS; bounded tester observation ended19:56:11
   without a new fetch/ACK. Observer exited; later20:00 ACK now closes this gate.
   No automatic renewal/future observation scheduled. Keep unchanged65;
   do not consume the tester's next window with another build or reinstall.
[Export14 and RTP correction/remaining gates](releases/2026-10-05-field-export14-beta65.md).
[Export15 and fresh tester readiness](releases/2026-10-05-field-export15-beta65.md).
[Export16 paired failure and next engineering gate](releases/2026-10-05-field-export16-beta65.md).
[Implementation, packages, tests and rollback](releases/2026-10-05-readiness-clock-skew.md).

### Earlier current-system check (before resumed implementation)

**Current-system mobile check complete — export13 negative.** User interrupted renewed
implementation planning to test existing beta65. No source/runtime fix was made.
Auto13:03–13:04UTC fails in52.244s: FETCH_FAILED, AWG/TCP NETWORK, restricted blocked
locally before native startup by NOT_READY. Earlier AWG/DNS success is a separate
connection, not success of this mobile attempt. RU13:07 latest fetch12:45/no ACK.
Do not ask for an identical retry, clock adjustment, screenshot or VPN-off coordination.
Next engineering gate, when resumed: verified clock-sensitive issuance/ACK correction
without weakening expiry/security, ready material over a working connection, actual
authority/leaf renewal for the later window. Then one coordinated mobile trial.
[Export13 and evidence limits](releases/2026-10-05-field-export13-beta65.md).

### Historical export12 decision and preparation

**Export12 / explicit user deferral:** installed tester65 confirmed. Two native import
failures temporally match server responses whose issued_at is ahead of the phone;
the strict ACK lower bound also explains missing failure receipts. Do not interpret
the older beta64 incident as a new65 transport failure. Native reproduction blocked
by local disk quota, no PASS. [Evidence](releases/2026-10-05-field-export12-beta65.md).
1. DEFERRED per user: remove dependence on manually correct phone wall clocks using
   authenticated time/monotonic lifetime design, including safe HTTPS bootstrap,
   restart/offline handling and expiration/revocation/replay/anti-rollback tests.
2. Do not ask for clock changes, another install or repeated mobile trials now;
   keep the working VPN available for communication and use JSON, not screenshots.
3. Before a later field attempt: revalidate/renew material, obtain actual fresh
   native READY/ACK, pre-agree the full brief trial and return-to-working-VPN steps.
   No relaxed validation, source patch, new APK or server mutation in this diagnosis.

### Earlier checkpoints (superseded by export12 and user deferral)

**Krasnodar available05.10; read-only preflight12:26UTC PASS.** Gateway05571644 remains
stable, actual leaf valid until13:28:47UTC/16:28:47 Krasnodar, RU/NL directory equal.
Tester fresh fetch12:22:14UTC has no ACK. NEXT confirm installed65/open over Wi-Fi
with VPN off, verify fresh native READY/ACK, then one mobile Auto attempt and export
before manual reconnect on failure. Do not confuse user availability with native
readiness or infer tester version from an unacknowledged fetch. No mobile test yet.

**Follow-up12:38UTC:** user reports setup done, but latest tester fetch still12:22:14
without ACK. Server stable, directory equal, headroom3006s. NEXT read the tester's
Settings → Connection readiness screenshot before another action; keep Wi-Fi/VPN-off,
do not loop update/refresh or begin the mobile trial without resolving this evidence gap.

**05.10 server execution checkpoint — owner65 acceptance PASS.**
1. DONE renew same-key gateway credential within unchanged issuer4 bound13:28:47UTC,
   native/permission/actual-loaded-chain verification, sync timer restoration.
2. DONE deploy accepted a813dc5/05571644 gateway only; bounded READY, PID353567,
   NRestarts0, old f71b7e7b backed up; ordinary services/admission/grants preserved.
3. DONE RU/NL generation equality, ordinary owner65 fresh READY/ACK, previously
   failing policy-loss recovery with paired59/67 gap-free server events, AUTH/cancel,
   AWG/TCP/security/privacy; unchanged installed65/identity verified, tests removed.
4. DONE targeted immutable65 publication10:25UTC and downloaded HTTPS200/hash/original
   signer verification10:27UTC; no rebuild/resign, defaults/catalog/invitation60 intact.
5. NEXT tester in-place update65 over Wi-Fi and fresh native READY/ACK65 for the current
   directory, then one Krasnodar mobile Auto trial and export before manual reconnect
   on failure. Tester last confirmed64; no fresh ACK yet. Actual credential bound
   05.10 13:28:47UTC/16:28:47 Krasnodar; revalidate/renew for later testing.
   Original field loss unlocalized; no RKN attribution or transport-timeout increase.
6. User confirmed availability no earlier than14:00 Brussels/15:00 Krasnodar on05.10
   (12:00UTC); do not request earlier tester action. Recheck real credential
   headroom/READY when available; no automatic scheduled test or contact configured.
   [Receipts and rollback](releases/2026-10-05-bootstrap-cleanup-race.md).

**Historical CI-only checkpoint — a813dc5 CI/artifact PASS05.10.**
1. DONE synchronize successful TCP dial → target RST/close → return socket to
   unchanged forwarding code, before server OPEN_OK. No post-OPEN sleep or weaker
   assertion; keep real Family TLS, policy and ClaimTCP in authenticated case.
2. DONE race stress500 repeats per scheduler1/2/4 (1500 per reset test) PASS.
   Full fresh-fixture race suite BLOCKED by disk quota: parallel/serial runs passed
   tcpforward but could not link telemost-binary; approved build-cache cleanup did
   not resolve quota and clean-cache build failed before tests. No full PASS claim.
3. DONE scoped commit/pusha813dc5, source guard1761/0 blocked; phase037291210868
   and Clients37291211020 PASS attempt1. Full carrier race/Android emulator/native
   and platform checks PASS. Artifact11337447479 downloaded/verified; gateway05571644
   source/ELF/hash verified. Failed3ba5270/quota receipts retained, not erased.
4. NEXT fresh actual gateway credentials, verified binary deployment and owner65
   recovery/security gates before targeted65 delivery/tester READY/Krasnodar trial.
   Live read-only09:47UTC: ADB connected, old gateway f71b7e7b/expired leaf still loaded,
   both admissions intact but no current usable readiness. Issuer headroom must be
   checked too; last issuer4 bound05.10 13:28:47UTC. No production mutation here.

**Bootstrap cleanup race — source3ba5270; CI blocked by baseline reset tests05.10.**
Historical blocker checkpoint; fixture correction is tracked above.
1. DONE correlate67 gap-free old-session server events: server cleanup18.482s after
   local cleanup and10.386s after next bootstrap rejection. Original rejection code
   was not logged; active-slot `device_busy` mechanism reproduced by a red test.
2. DONE wait for actual matching server cleanup within existing120s BOOT-1 budget;
   retain auth/identity rechecks, cancellation, single-device/global limits and
   immediate HTTP/unfinished-setup refusal. Add closed-enum server rejection reasons.
3. DONE final fresh-fixture50-repeat regression and full uncached Go race suite;
   Python94 PASS. Preserve deadline-race and overnight expired-fixture failures in
   the report; no timer increase, revocation bypass or original DATA-stall fix claim.
4. DONE scoped commit/push3ba5270; source guard1761/0 blocked, committed docs476/2883.
   phase037284062182 PASS; Clients37284062212 FAIL twice on two existing TCP reset
   tests before gateway build. Bootstrap/room-broker tests PASS in both attempts.
   GOMAXPROCS=1/200 reproduced failures on candidate and prior86fa1ba; no TCP source
   edits or third rerun. NEXT separately scoped fixture synchronization preserving
   OPEN_OK/reset assertions, then exact-source CI/artifact acceptance. Other workflows
   do not trigger for this path set. Only then matching gateway deployment with actual
   loaded-chain/RU-NL generation verification. Last verified leaf expired04.10
   22:57:31UTC. No production changes or new APK made by this local patch.
5. THEN owner65 recovery/security/ordinary-VPN acceptance before targeted immutable65
   delivery, tester fresh fetch/native READY/ACK and one Krasnodar mobile trial.
   Preserve owner65/tester/public64/default60 and data; do not replace APK65 bytes.
   [Exact checkpoint and rollback](releases/2026-10-05-bootstrap-cleanup-race.md).

**Beta65 — ordinary cache refresh PASS; bootstrap recovery gate failed04.10.**
Historical checkpoint; the current source correction and next gates are above.
1. DONE scoped source86fa1ba push, four exact-source CI PASS, artifact verification,
   offline original-signer signing; Python119/Android254/lint/JVM171 and docs PASS.
2. DONE owner64→65 preserving data, ordinary foreground fetch/native READY/ACK with
   valid retained cache (9576s remaining), no forced fetch. AWG/TCP/auth/cancel/privacy
   and final installed-byte/identity checks PASS; private test APK removed.
3. NEXT diagnose saved20:21UTC recovery failure: old cleanup/new attempt occurred,
   bootstrap family auth succeeded, exchange failed before descriptor. Exact rejection
   unknown; inspect/instrument bounded admission reason without relaxing security.
   No timeout increase, blind rerun, publication or claim that field DATA loss is fixed.
4. THEN pass owner recovery/security gate and revalidate actual credential headroom,
   targeted65 delivery/download verification, tester fresh READY/ACK and one mobile
   trial. Owner65, tester/public64, default/catalog/invitation60; gateway f71b7e7b
   unchanged, current loaded leaf bound04.10 22:57:31UTC. Publication is held.
   [Release gates/rollback](releases/2026-10-04-beta65-readiness-candidate.md).

**Early readiness refresh correction — historical source checkpoint04.10.**
1. DONE reproduce long-valid retained-cache suppression (13 tests/5 failures on old code).
2. DONE remove expiry suppression only; retain persisted300s cooldown, single-flight,
   native/authority validation, atomic cache, anti-rollback and AUTH handling.
3. DONE Android254/lint, standalone JVM171 and Python117 including Java HTTP and
   native Go compatibility. Initial Java-PATH failure retained; corrected environment PASS.
   Scheduled authenticated fetch/import/ACK regression is now in the CI source set.
4. NEXT immutable successor/exact-source CI and offline signing, then owner upgrade
   with **ordinary prewarm over retained valid old cache** and preservation/security gates.
   Source commit/push authorization required; no release version changed in this patch.
5. THEN targeted delivery/tester fresh current-directory READY/ACK and one mobile trial.
   Current installed/public64 is unchanged. Do not replace its immutable binary.
   [Patch and acceptance limits](releases/2026-10-04-readiness-early-refresh.md).

**Beta64 source/CI/signing and paired owner/gateway acceptance DONE04.10.**
1. DONE main/last release CI readback; same owner Redmi connected, beta64 URL404/no tag.
2. DONE local version64/documentation, Android246/lint, Python52 and docs checks.
3. DONE scoped commit/push ce73ddf, four exact-source CI workflows, downloaded artifact
   verification and offline signing: APK b1a9f621, matching gateway f71b7e7b. Readiness
   attempt1 failed; unchanged attempt2 PASS. Initial failure retained, not declared fixed.
4. DONE in-place owner64/identity preservation, matching gateway f71b7e7b deployment,
   credential renewal and loaded TLS validation; issuer4/admission/grants unchanged.
   Actual minimum bound04.10 22:57:31UTC; client/directory22:59:29 is not the full bound.
5. DONE genuine native8-retry exhaustion→poll NETWORK→new session/HTTPS200; saved
   ring/incident and paired original32/55, restored28/58 events, four-ID lookup/privacy,
   gap-free server cleanup. Local AUTH/cancel, AWG/TCP, export/restart/Support PASS.
   Private test APK removed. First stale-directory setup failure retained; synchronized
   authenticated refresh passed. No injected policy cause, no real server revocation.
6. DONE targeted64 publication19:13UTC/downloaded SHA/signer/HTTPS20019:14UTC.
   DONE tester64 authenticated ACK19:21:49UTC/same Support; readback19:23UTC.
   NEXT safe early-refresh fix/acceptance or verified ordinary current-directory
   fetch/native READY/ACK, then authorized single Krasnodar mobile attempt/export.
   No fragment-ID match in these asynchronous samples: do not localize field loss from
   it. Enforce RU/NL generation equality before client refresh after reload; automatic
   gateway-leaf renewal remains absent. Revalidate full chain before later work.
   Owner64/tester64/default/catalog/invitation60. Old tester directory
   expires21:32:03UTC; normal cache refresh waits until<=300s remaining. Cached READY
   or its re-ACK by64 does not meet the fresh-fetch gate: latest fetch still17:39:16UTC.
   Ordinary threshold21:27:03UTC/05.10 00:27:03 Moscow is not guaranteed readiness.
   No mobile attempt yet; do not reset identity/security floors or device clock.
   [Candidate checkpoint](releases/2026-10-04-beta64-paired-candidate.md).

**Paired delivery diagnostics implementation checkpoint (runtime gate now passed above).**
1. DONE bounded flow/ACK/SACK, queued/written/CRC-complete/oldest-partial fragment
   snapshots on both endpoints; Android projection and paired offline comparison.
2. DONE full Go suite, race for six affected packages, Android246/lint, Python52;
   max-value export budget, immutable snapshots, missing-head RTP and healed controls.
3. NEXT release a fresh immutable Android successor and matching gateway only after
   exact-source CI/artifact checks; owner paired runtime gate, same identity/admission,
   AUTH/revoke/cancel preservation and actual refreshed material headroom required.
4. THEN inspect paired evidence before deciding whether another tester attempt adds
   information. Last samples are not simultaneous; missing matching fragment evidence
   is unknown, not a localized drop or RKN verdict. No retry/RTO tuning.
   No version/deployment change in this source task; owner63/tester62/default60 unchanged.
   [Source report and remaining gates](releases/2026-10-04-paired-delivery-diagnostics.md).

**Native exhaustion→production poll physical gate PASS04.10; DATA loss still open.**
1. DONE real process-local RTP receive loss on installed63: native8-retry exhaustion,
   production poll NETWORK, old cleanup/fresh BOOT-1/session/HTTPS200; no synthetic cause.
2. DONE server original/restored tags53/56 gap-free, filters/library/test APK removed,
   identity/enrollment/Support preserved; no server or product binary mutation.
3. DONE cross-layer ReliableStream/fragment/VP8/RTP regression with fresh ACK,
   missing head DATA and healed-gap control; four-package race and three repeated runs
   PASS. Compilation moved off quota-limited `/tmp`; no timer or runtime code changes.
4. DONE local bounded paired per-sequence ACK/SACK/reassembly instrumentation (above);
   NEXT deployed paired acceptance before field-loss investigation. No blind tuning or
   repeat mobile test; material expiry must be rechecked.
   [Exact native evidence](releases/2026-10-04-beta63-native-exhaustion.md).

**Beta63 source/CI/signing/owner policy acceptance and targeted delivery DONE04.10.**
1. DONE remote/device preflight: main cb76f115, no beta63 tag, owner installed62/UID10283.
2. DONE de7cacd/0.1.18-beta63/code63, all four exact-source CI PASS (client attempt2;
   initial invitation runtime failure retained), downloaded artifact/provenance/offline signing.
3. DONE owner in-place preservation and final installed SHA ce81216a; AWG/TCP HTTPS200,
   diagnostics/privacy/Support/restart and test-package removal. Injected policy cause
   drives real native cleanup/new descriptor/session/HTTPS200; one-restoration guard,
   injected local AUTH and cancellation PASS. Test-only restricted selection, not a
   genuine exhaustion→native poll physical test. Server two tags56/132 gap-free events.
4. DONE targeted publication16:56UTC, verified HTTP200/downloaded SHA/signer16:57UTC.
   Initial partial upload reconciled/resumed before route activation; default60, immutable
   older downloads, admission/identity and normal services unchanged. Only HTTPS nginx
   reloaded. Tester last receipt62; no repeat or broad rollout.
5. DONE subsequent genuine native exhaustion→poll physical gate (see above); NEXT DATA/ACK loss investigation.
   Original stall/setup reliability is not fixed by this policy patch. Recorded material
   bound17:30:19UTC is not a fresh four-hour window; revalidate/renew before later testing.
   [Exact release state](releases/2026-10-04-beta63-recovery-candidate.md).

**Current export(11): mobile reproduction received and correlated.**
1. DONE four retained sessions/four-ID lookups; gap-free server evidence and privacy PASS.
2. DONE exact new established-session failure: retry budget8, outstanding8, recent ACK
   without cumulative progress; TLS errors follow cleanup. Expiry is not this blocker.
3. DONE recovery code/evidence match: unhealthy restricted→INTERNAL→terminal finish,
   cleanup completed/new descriptor NOT_ATTEMPTED. Original DATA-stall cause still open.
4. DONE local bounded recovery classification fix: only correlated retry exhaustion
   is NETWORK; unknown/auth/protocol remain terminal. Native/cache expiry validation,
   cleanup guard and one-restoration limit preserved; owner AUTH race and pre-start
   denial checked. Android243/lint, Python100 and four Go race packages PASS; real
   export replay PASS. Subsequent beta63 delivery/owner state recorded above; no gateway change.
5. DONE deterministic missing-head-DATA + fresh ACK reproduction and healed-gap control.
   NEXT targeted framing/loss investigation: this proves neither field drop location
   nor RKN involvement; no blind retry/RTO increases.
   No more field repeats now. Any changed APK requires fresh immutable release/platform
   and owner gates. Next delivery must verify actual validity headroom and physical
   cleanup/new-descriptor/reconnect/security behavior before tester distribution.
   [Local patch/checks](releases/2026-10-04-restricted-recovery-classification.md) ·
   [Export(11)](releases/2026-10-04-field-export11-beta62.md).

**Prior readiness sequence below: mobile reproduction gate now satisfied by export(11).**

**Current04.10: beta62 tester upgrade confirmed; long server/owner window accepted.**
1. DONE source42a5e59 exact-source four CI workflows, artifact verification/offline
   signing, in-place owner update and UID/identity/enrollment/activation/Support checks.
   AWG/export/privacy PASS;182 Python/full Go race and Android233/lint PASS.
2. DONE matching diagnostic gateway deployed; real controlled restricted session has
   non-empty matching tag,48 client/75 server events, all four lookups and lifecycle PASS.
   Server retry exhaustion after intentional close is not the Russian failure.
3. DONE separate beta62 download: HTTP200, downloaded APK/signer verified. Default,
   updater/invitation remain60; no FIELD expansion or old artifact replacement.
4. DONE tester62/code62 authenticated receipt, same Support/admission, normal short
   READY13:16 after initial native import failure. That receipt expired13:23.
5. DONE compatible RU/NL policy/issuer/grants/gateway/CRL/real4h seed;197 exact overlay
   tests PASS. Owner long native import/ACK and controlled healthy session PASS,
   headroom3h52m56s. Actual earliest server bound17:30:19UTC/20:30:19 Moscow.
6. DONE tester long READY/ACK13:39UTC, initial headroom3h51m15s; resumed14:55 readback
   still usable with2h34m59s remaining, same gateway/restarts0. Owner correlation48/88
   events/lifecycle/privacy PASS; archive reader scoped to actual current journal file.
7. NEXT exactly one mobile reproduction/immediate export inside the verified window;
   if delayed past expiry renew full chain/readiness first. Correlate first failure and
   ACK/progress evidence, fix only the proven cause with regression. No RKN/fix claim.
   [Four-hour rollout and remaining gate](releases/2026-10-04-beta62-four-hour-rollout.md) ·
   [APK/source acceptance](releases/2026-10-04-beta62-recovery-candidate.md).

**Historical source checkpoint04.10 — superseded by the current sequence above.**
1. DONE verify exact installed r2 bytes/signer, UID/activation/identity/Support and
   private encrypted-state baseline on Redmi; temporary test harness removed.
2. DONE local first-failure-before-cleanup fix and exact exhaustion branch/ACK evidence;
   retain retry/timer/wire semantics. This fixes an observability gap, not packet loss.
   Python171, Android233/lint, full Go and focused race/repeated-ordering checks PASS.
3. IN PROGRESS corrected sourceb04f5c2 pushed: directory contracts99 local PASS;
   phase0/Linux control/readiness CI PASS. Android runtime PASS, later Go race step
   failed; retry/full local/25 repeated core race PASS. Retry then exposed missingRNS
   in new Python CI contract environment, reproduced cleanly. Add pinned identity
   lockfile/log capture. CI902e4db logs then proved Python3.10 fractional timestamp
   incompatibility; fix exact-nanosecond parsing and27 regression cases, rerun full
   gates, then verify/sign and perform in-place acceptance. No transport change.
   Do not sign/publish unverified/stale native code with new Java.
4. THEN coordinated long-material activation/owner proof, targeted tester delivery,
   one reproduction to distinguish missing ACK, retry budget, age and SACK backpressure.
   Fix proven cause with regression; no arbitrary timeout increase or RKN claim.
   [Exact status](releases/2026-10-04-beta62-recovery-candidate.md).

**Historical export(10) checkpoint: failure evidence remains valid; build/device gates superseded above.**
1. DONE match two real tester session tags to server lifecycle; Family TLS, gateway
   and bidirectional traffic precede IO_CLOSED/recovery_exhausted before expiry.
2. NEXT identify the exact ReliableStream exhaustion branch and missing ACK/progress
   evidence without raising retry limits by guesswork. Structured first_failure is
   absent; later TLS/gateway cleanup errors are not the proven initiating cause.
3. OPEN recovery: cleanup completes but new descriptor NOT_ATTEMPTED. Original
   disconnect and failed restoration remain unresolved; no RKN or transport-fix claim.
4. DONE local four-hour lifetime chain and short-certificate refresh regression;
   Python168, three Go packages, focused JVM4 PASS. NOT built/installed/deployed.
5. BLOCKED owner acceptance: no attached Redmi. Next immutable diagnostic APK must
   pass platform checks and in-place acceptance before long server material activation.
   Renew the complete chain and verify substantial remaining time, not only a gateway
   certificate. Preserve beta60, exact two-device admission and accepted r2 bytes.
   [Diagnostics](releases/2026-10-04-field-export10-reliable.md) ·
   [Four-hour candidate](releases/2026-10-04-four-hour-readiness.md).

**Latest04.10 export(9): fresh tester READY/ACK now confirmed; restricted test pending.**
1. DONE correlate client READY10:05:15.521UTC with server fetch10:05:15/ACK10:05:16,
   expires10:34:57UTC; read-only10:17 check confirms usability and live hour policy.
2. DONE distinguish preceding failed attempts from post-READY state: both restricted
   gates NOT_READY; no restricted session/tag. Latest Wi-Fi/AWG connected. Diagnostic
   UNKNOWN resets on connect and is not cache invalidation evidence.
3. NEXT coordinate exactly one mobile attempt within verified lifetime including
   ~52s fallback, export immediately; renew readiness/check again if the window passes.
4. OPEN native-import failure10:00:12UTC and original established-session disconnect;
   neither fixed nor attributed to filtering. No rebuild, admission or beta60 changes.
   [Read-only report](releases/2026-10-04-field-export9-readiness.md).
5. OPEN practical long test window: four-hour gateway certificate is not four-hour
   client readiness. Directory renewal/fetch headroom needs addressing; true four-hour
   offline acceptance also needs client policy changes and renewed APK acceptance.

**Latest04.10: authorized longer testing window deployed; phone refresh still pending.**
1. DONE opt-in3600s CRL, default900 retained; invalid lifetime/expiry/issuer cap/revocation
   tests, native30-minute delivery and4-hour gateway compatibility PASS (138 tests).
2. DONE exact deployed-baseline overlay with only two modules changed, archive1bfa085b;
   isolated artifact66 tests PASS, source inventory/pins and dependencies checked.
3. DONE protected4-hour gateway renewal; RU sync drop-in activated, background hour-long
   CRL proved on RU/NL; beta60 catalogs/landing/HTTP/AWG/TCP/admission/Support preserved.
4. NEXT fresh ordinary tester Wi-Fi READY/ACK, then coordinate one mobile attempt within
   actual cached/room validity. No APK rebuild, security bypass or transport fix claim.
5. Remaining intermittent native-import/original session-loss investigation unchanged;
   issuer still expires14:13:53UTC. Follow documented policy rollback, never lower floors.

**Latest04.10: user requests longer validity, beyond certificate-only renewal.**
1. DONE source audit: CRL900s caps readiness; native delivery/CRL/directory ceiling3600s.
2. NEXT confirm up-to60-minute readiness/CRL policy including older accepted revocation
   information, then implement/test and deploy through accepted server release process.
   Gateway-only renewal is insufficient; do not silently weaken expiry/signature checks.
3. No runtime TTL change yet; preserve enrollment/FIELD/beta60 and exact accepted APK.

**Latest04.10 export(8): new mobile attempt missed the verified readiness window.**
1. DONE timeline: last READY expires09:12:39UTC; refresh FETCH_FAILED09:12:43UTC;
   new connect09:15:18UTC, restricted gate09:16:10UTC NOT_READY. No restricted session.
2. DONE live09:23 checks: no newer tester challenge/fetch/ACK; loaded gateway valid,
   same binary/PID/restarts0, matching RU/NL directory/CRL, unchanged exact2 admission.
3. NEXT restore working Wi-Fi, obtain fresh ordinary READY/ACK, check lease headroom
   including ~52s Auto fallback, then separately coordinate a new mobile attempt.
   Do not repeat on expired readiness, bypass checks, clear data or expand FIELD.
4. FETCH_FAILED network/HTTP cause, intermittent native-import failures and original
   session loss remain unresolved. No restricted-path/RKN attribution from this run.

**Latest04.10 export(7): post-renewal tester readiness gate passes, not FIELD success.**
1. DONE export timeline/privacy: two native-import failures followed by READY08:58:11UTC;
   preserved incident from export(6), no new mobile/restricted session.
2. DONE read-only server confirmation09:01UTC: fresh tester READY/ACK, same Support/
   revision1, expires09:12:39UTC. Actual gateway certificate and RU/NL signed CRL/
   directory agree; same accepted binary, exact2 admission, beta60 default unchanged.
3. NEXT one coordinated mobile Auto attempt while leases/readiness remain fresh;
   immediate export on failure/disconnect, bounded server trace and four-ID join.
   If delayed past the accepted window, check fresh readiness before testing.
4. Native-validation failure branch/clock offset and original disconnect remain open;
   no transport/auth change, data clear, FIELD expansion or production promotion.

**Latest04.10 export(6): mobile attempt blocked before restricted session creation.**
1. DONE client timeline/privacy/empty-session correlation analysis; beta61/code61,
   same tester Support ID; CELLULAR bootstrap unavailable, later WIFI/AWG connected.
2. DONE read-only checks: no fresh tester READY/ACK; loaded gateway certificate
   expired03.10 21:18:57UTC despite new directory. Admission/revocation unchanged.
3. DONE protected gateway renewal04.10 08:39UTC and actual loaded-certificate check;
   RU/NL directory/CRL agree08:42, same binary/admission/ordinary services. Certificate
   expires09:39:30UTC, directory09:34:32UTC; issuer14:13:53UTC. TTL policy unchanged.
4. BLOCKED post-renewal tester fetches08:44:56/08:49:56UTC both have authenticated
   ACK=NATIVE_VALIDATION_FAILED; no post-renewal READY. Final08:51 gateway/sync PASS.
   NEXT fresh client diagnostics on Wi-Fi and native-import/time evidence; no exact
   native branch or clock offset proved. Polling stopped; do not bypass validation,
   clear cache, shorten backoff or fabricate ACK.
5. Only after prerequisites pass, coordinate one mobile attempt with immediate
   export/server window. Do not repeat now, clear data, bypass expiry or widen FIELD.
   No transport fix/RKN conclusion from export(6); original session-loss remains open.

**Latest04.10: BETA61 R2 DIRECT DELIVERY PASS; no GitHub release.**
1. DONE exact accepted APK published at separate diagnostic download URL; no rebuild
   or resign. Public HTTP200 readback SHA4297ea1a and production signer67a90d1 PASS.
2. DONE beta60 public bytes/default invitation and signed/legacy update catalogs
   verified unchanged; desktop downloads, FIELD/Support/enrollment preserved.
3. DONE delivery/rollback report and RU/EN diagnostic links updated; no landing edit,
   production promotion, automatic/mandatory update or tester installation.
4. NEXT separately coordinate tester in-place update over60, unchanged Support ID,
   fresh gateway leases/READY/ACK, one mobile attempt and immediate diagnostic export.
   Do not infer original transport fix; no Russian reproduction in this delivery task.

**Historical04.10 GitHub route: superseded; do not pursue GitHub Releases.**
1. DONE local APK SHA4297ea1a and production signer67a90d1 verified, exact beta60
   signer match; no rebuild/resign. Single-asset notes/request prepared locally.
2. BLOCKED release creation/upload: connected GitHub tools lack those actions and
   local authenticated GitHub CLI is unavailable. No remote release write attempted.
3. NEXT authenticated release upload capability; recheck tag/release before creating
   `android-beta61-r2-diagnostic` at64849e8, prerelease=true, make_latest=false.
4. Upload exactly the accepted APK; download from GitHub and independently verify
   SHA256/signature. Only then report delivery PASS and the real URLs.
5. Do not touch production beta60/catalog/landing/FIELD/Support IDs. No Russian test
   in this publication task; fresh leases/READY/ACK required before that later test.

**Latest03.10: BETA61 RUSSIAN DIAGNOSTIC READY; stop before Russian reproduction.**
1. DONE final64849e8 CI all applicable workflows PASS, immutable targeted signing,
   exact beta60 signer and APK privacy/alignment verification (SHA4297ea1a).
2. DONE owner in-place continuity, enrollment/Support, AWG/HTTPS, export/runtime UI.
3. DONE protected gateway-only renewal and CI executableb9b7d542 deployment/readback;
   exact2 admission/grants and ordinary services preserved, rollback executable only.
4. DONE fresh ordinary READY/ACK and real owner restricted session: matching full
   tag,48 client/75 server events, no gaps, four-ID join, lifecycle/privacy PASS.
   Final installed APK/identity readback PASS; separate test package removed.
5. DONE local verified signed handoff for existing FC-YHQB-9VJN; not uploaded/sent.
   NEXT separately coordinate fresh gateway leases/tester READY/ACK, in-place update
   over60 and exactly one mobile attempt with immediate export. Do not run now.
   No broad publication, FIELD expansion, transport change or original-defect fix claim.

**Latest03.10: diagnostic r2 implemented locally; acceptance still BLOCKED.**
1. Implemented full32-byte ID digest, real producer/bootstrap regression, bounded
   server/native lifecycle and first-observed failure, Android four-ID correlation.
2. Local gates PASS: full carrier race,230 Friends JVM/lint,pytest17/17,diff-check.
   Final gateway shutdown/detail race regression also PASS; use fresh hosted CI
   for the final checkpoint, not superseded source621468e artifacts.
   Export provider/persistence bounds aligned; full-history regression231 JVM PASS.
   Use latest checkpoint CI, not intermediate4c68c77/6585559 artifacts.
3. Sign distinct targeted beta61/code61 artifact with the same production key after
   accepted CI; retain original c98852b3 and record exact new source/APK/signer hashes.
4. Owner in-place UID/identity/enrollment/Support/AWG/export/privacy acceptance.
5. Controlled gateway binary update/rollback and fresh leases; prove a real owner
   restricted session with identical client/server tags and complete lifecycle.
   NL19:43UTC actually served expired16:22:33UTC certificate; renew through protected
   procedure, preserving exact2-device admission. Do not reuse stale owner receipts.
6. Only then supply existing tester. No FIELD/publication expansion or Russian retry
   yet; no transport-fix or RKN attribution claim.

**Latest03.10: BETA61 BLOCKED after targeted owner acceptance; no broad release.**
1. DONE sign existing CI APK without rebuilding; exact beta60 signer match. Owner
   in-place preservation, startup/restart, baseline AWG/HTTPS and privacy checks PASS.
2. DONE typed-fixture diagnostic export; NOT live correlation acceptance. Confirmed
   blocker: real broker64-hex SetupID rejected by16-byte sessiondiag gate, empty tag.
3. NEXT fix contract with production-length regression and independently gated
   artifact. Preserve signed c98852b3; no silent rebuild/overwrite or broad catalog.
4. NEXT complete tagged server lifecycle/heartbeat/recovery trace and exact
   Support ID/connection ID/incident ID join. Deployed gateway still old e17e1fe7.
5. Only after diagnostic/owner/server acceptance: targeted existing tester delivery,
   fresh READY/ACK/leases, one mobile attempt and immediate export. Attempts so far0.
   No admission/enrollment/Support change. No transport-fix or RKN attribution claim.
   [Acceptance and blocking evidence](releases/2026-10-03-beta61-targeted-acceptance.md).

The publication step in the earlier preparation plan below is superseded by the
user's targeted-only instruction; public catalogs/invitation must remain unchanged.

**Latest03.10: commit/push authorized; preparing diagnostic beta61/code61.**
1. DONE focused diagnostics/CI/version/documentation committed/pushed as `d93a01d`;
   unrelated VPN docs preserved. Local payload/field pytest9/9 PASS.
2. DONE all Client builds `37138322487` gates, phase0, Linux control and readiness
   PASS; unsigned ARM64 artifact11279129098 downloaded and source/hash/16KiB/privacy
   verified. APK7e3fb204 remains unsigned and must not be handed to the tester.
3. NEXT offline signature and owner in-place acceptance before tester delivery;
   maintain package/signer/identity. No CI signing keys or beta60 replacement.
4. Narrow gateway rollout with executable rollback and freshly validated leases;
   exact two-device cohort remains unchanged. No normal-service restart.
5. Publish verified immutable update/catalog/docs, then one tester Auto attempt and
   correlated export. Public links remain beta60 until acceptance/publication.

The previous local-only checkpoint follows; commit authorization is now granted.

**Latest FIELD-1 engineering03.10: terminal diagnostics locally implemented/tested.**
1. DONE bounded enum-only gateway/native/Android report with session tag, first
   Mux reason/time, reliable/ICE/signaling evidence, preserved incident and separate
   authorization_denied. No policy/TTL/security/fallback change; root cause still open.
2. DONE full carrier race regression;228 Friends JVM tests/lint;pytest4/4; gateway,
   Android arm64 native and unsigned compile-only APK builds. Packaging/hash checked.
3. PENDING explicit commit/push authorization for source checkpoint and hosted CI.
   Do not publish/install the local metadata60 unsigned APK or overwrite public60.
   New immutable version, accepted platform CI, native+Java parity, signer/catalog,
   owner in-place preservation and real-device diagnostics acceptance remain required.
4. PENDING controlled gateway diagnostic rollout/rollback and one real tester run.
   Revalidate/renew expired prior leases and obtain fresh ordinary READY/ACK first.
   Keep exact2/3 cohort, no normal HTTP/AWG/TCP restart or identity reset.
5. THEN correlate terminal causes by session tag; fix reproduced cause with regression
   tests and validate sustained/lifecycle operation. No FIELD completion/RKN claim.
   [Detailed runbook](testing/restricted-session-diagnostics.ru.md).

Previous observations below motivated the patch; they are not evidence of its rollout.

**Latest FIELD-1 export03.10 16:05UTC: second post-connect loss reproduced.**
Fifth export: local READY16:02:19, restricted CONNECTED16:04:05.758UTC after84.449s;
INTERNAL15.143s later, retained capture, failed restoration114ms. Previous session
lasted30.227s. Pattern reproduced, fixed30s cutoff not established. No new exported
AUTH/import failure; local fresh READY does not substitute for current server ACK.
Keep terminal-reason diagnostics as next engineering action; no RKN attribution,
blind timeout/security-policy change, further tester retry or cohort expansion.
Read-only gateway correlation complete16:08UTC: ACTIVE16:04:04.634 followed by
resources-closed/FAILED16:05:19.694, same PID/zero restarts; terminal cause absent.

**Latest FIELD-1 check03.10 15:54UTC: gateway correlation complete, reason missing.**
1. DONE read-only gateway journal: ACTIVE15:34:13.488UTC → resources closed/FAILED
   15:34:52.10UTC; same process/PID3231001 since15:22:36UTC, zero restarts.
2. DONE exact accepted gateway binary/source mapping and unchanged2/3 admission,
   inventory28/24/4, registration/invitation/Support/owner-grant/audit invariants.
3. NEXT preserve bounded enum-only terminal reasons across Mux/Family/transport,
   gateway broker event and Android diagnostics; test privacy/failure propagation.
   Existing server drops Code and native drops Mux terminal reason; no raw error
   strings, room URLs, destination data or credentials in shared output.
4. THEN one controlled retry after fresh ordinary readiness and gateway/CRL checks;
   both receipts expired at15:54:27UTC. Certificate expiry16:22:33UTC and directory
   expiry16:17:36.983UTC remain unchanged. Do not change TTLs/auth/retry safety
   based on timing alone. No diagnostic implementation/deployment performed yet.
5. FIELD remains BLOCKED on unclassified session loss; no blind repeated tests,
   cohort expansion, new milestone, APK/catalog publication or server restart.

Previous export analysis and observation checkpoints follow.

**Latest FIELD-1 evidence03.10 15:36UTC: restricted connects, then loses session.**
1. DONE fourth tester export + server readback: post-renewal READY/ACK15:27:38UTC,
   expiry15:42:05UTC; normal CELLULAR Auto reached restricted CONNECTED15:34:13.877UTC.
   Family auth/broker/SESSION_READY passed; startup AUTH no longer reproduces here.
2. OPEN loss30.227s later at15:34:44.104UTC, generic INTERNAL; terminal recovery
   reaches FAILED117ms after RESTORING without retrying a transport. Capture retained.
   Source explains generic classification, not the underlying Mux/native failure.
3. NEXT correlate bounded gateway/native termination evidence15:34:13–15:34:44UTC;
   distinguish session loss from denied readiness. Do not classify from elapsed30s
   alone, change terminal safety policy blindly, or claim completed data transfers.
4. Owner receipt remains expired. Revalidate all leases before further live use;
   exact owner+tester2/3 only. No new build/release/admission in this analysis.
   FIELD completion/expansion blocked on unresolved session loss and lifecycle tests.

The previous retry-pending checkpoint below is superseded by this export.

**Latest FIELD-1 observation03.10 15:23UTC: gateway expiry blocker repaired; retry pending.**
1. DONE tester third export: four full connection starts, two AWG CONNECTED, two
   restricted STARTUP_FAILED/AUTH after AWG/TCP NETWORK outcomes; incident retained VPN.
2. DONE existing gateway credential-only renewal after confirmed15:14:31UTC expiry;
   native/TLS/loaded certificate/fresh directory/stability PASS, no normal-service or
   enrollment/admission changes. Certificate now expires16:22:33UTC; directory16:17:36UTC.
3. PENDING fresh normal foreground provisioning for owner and tester after renewal,
   then normal Auto retry and DIAG outcome. Last tester ACK is pre-renewal; owner
   receipt expired. Do not claim restricted success or bypass expiry based on process state.
4. Continue only exact2/3 cohort; no widening. Investigate remaining transport failures
   if retry fails; do not equate broad AUTH mapping with a proven TLS error trace.

Earlier readiness and clock-skew evidence follows; current session gate is above.

**Latest FIELD-1 result03.10 15:11UTC: FC-YHQB-9VJN READY / ACK_RECEIVED.**
Normal retry after tester clock synchronization succeeded15:10:07UTC, valid until
15:25:02UTC. No code/policy change, registration reset or additional admission.
Exact2/3 cohort preserved, owner + tester, no wildcard. Readiness blocker resolved;
earlier investigation below is evidence, not a request for further blind exports.
Next: verify currently valid gateway/directory leases before real restricted use,
then continue authorized normal-Auto FIELD observation; do not force Telemost.
Last gateway certificate expiry15:14:31UTC requires existing renewal if testing later.
Do not claim completed FIELD transport acceptance from a readiness receipt alone.

**FIELD-1 real-device observation authorized03.10; same milestone.**
1. DONE existing provisioning renewal; owner FC-4D8Q-REEG fresh native READY /
   ACK_RECEIVED14:40:34UTC, valid until14:55:27UTC. Identity/enrollment/auth unchanged.
   Revalidate current leases before restricted use; no expiry bypass. Gateway
   credential currently expires15:14:31UTC; existing renewal remains required.
2. DONE explicit admission FC-YHQB-9VJN, audit0→1/APPLIED14:38:02UTC. Preserve owner,
   exact2/3 cohort, no wildcard, no additional selection. Inventory28/24/4 unchanged.
3. BLOCKED tester readiness: normal challenge/fetch succeeded, but no accepted ACK
   by14:54:35UTC; its last fetched material expired14:54:23UTC, no newer attempt.
   Owner refreshed READY/ACK14:53:09UTC, valid until15:08:03UTC.
   Obtain tester privacy-safe diagnostic export; do not infer local import
   success or network failure from missing ACK. No new registration/replacement ID.
   Export received: NATIVE_VALIDATION_FAILED14:55:44UTC, ordinary AWG CONNECTED and
   DNS probes passing. Exact native predicate/ACK failure not included. New fetch
   14:55:47UTC is after export's last event; no ACK14:58:23UTC. Next: correlate newer
   device receipt/native validation evidence without weakening checks or resetting state.
   Second export repeats failure15:01:05.578UTC versus server fetch15:01:08UTC;
   investigate device clock lag first. Server NTP yes; strict issued_at and ACK
   observed_at checks explain both symptoms if lag is confirmed. Ask tester to
   verify automatic date/time, then use ordinary foreground refresh; no expiry bypass.
4. PENDING owner repeated Auto/lifecycle/Wi-Fi/mobile/transition observations with
   DIAG correlations; exercise tester only after fresh READY/ACK. Classify failures;
   UNKNOWN critical failures block completion. Stop expansion on a production defect.
5. No new build/catalog/publication/transport changes. Service notice capability is
   a public platform-filtered feed, not Support-ID-targeted delivery; do not broadcast
   a device-specific admission notification without explicit audience authorization.

The publication checkpoint below is historical; observation supersedes its stop point.

**FIELD-1 beta60 publication authorized and completed03.10; stop, no new milestone.**
1. DONE exact accepted60 bytes published and independently downloaded/hash/signer checked;
   source5c740f2/SHA8ee59352, beta59 unpublished. No public APK rebuild/resign.
2. DONE existing offline root signs Android v2 sequence1; optional/minimum1; client
   verifier expiry/replay/signature checks PASS. Renew before2027-01-01 13:34:01UTC
   with a higher sequence; never overwrite immutable APK content.
3. DONE legacy checker receives60 on Android; owner60 UI says latest; original
   identity/enrollment/Support auth/copy/restart PASS, temporary tests removed.
4. DONE invitation Android60/CSP; Windows/Linux links unchanged.28 registrations,
   24 non-revoked,4 revoked;1 known Android60,27 unknown. No all-user adoption claim.
5. STOP owner1/no wildcard/cap3, no admission/audit/grant changes or FIELD widening.
   Last readiness EXPIRED_ON_IMPORT; fresh accepted readiness via existing provisioning
   is required before any later restricted field test, without expiry bypass.
6. DONE task-owned publication checkpoint741aac3 pushed; unrelated VPN-health work
   remains local. No new development task or FIELD expansion authorized here.

The following acceptance-only checkpoint is historical and superseded by publication.

**FIELD-1 beta60 continuation authorized03.10; same milestone.**
1. DONE Auto TCP dual-stack fix, focused builder coverage and unchanged traffic
   acceptance; Manual AWG primary/cleanup PASS with stale prior-failure race fixed.
2. DONE Windows2022 SCM Start Pending observed after installer exit0; new PID and
   authenticated broker readiness PASS with bounded polling, no fixed sleep.
3. DONE clean source5c740f2 signed beta60/code60 SHA8ee59352; historical59 preserved.
4. DONE owner59→60 preservation/Support/Auto/AWG/TCP/HTTPS/DIAG/share/privacy acceptance.
   Readiness decrypted/preserved; later server-material expiry is not fresh READY.
5. DONE required hosted gates at4963c7c; Windows control rerun on identical scoped
   source ef554e7. STOP: publication gate READY is not permission to sign a catalog,
   publish, edit landing or widen FIELD. One-owner/no-wildcard/cap3 unchanged.
   Before any future restricted field use, confirm current valid readiness through
   existing provisioning; no expiry bypass or new Stage5N gate.

Previous checkpoints below remain historical evidence.

**FIELD-1-RELEASE-FINAL authorized03.10; Stage5N remains CLOSED.**
1. DONE existing APK5abc2da/beta59 SHA6d13720, no rebuild. Prior JVM/native/lint and
   owner Auto/AWG/TCP accepted.518 focused Python now PASS; index guard repaired
   by splitting the negative-test literal, not weakening secret detection.
2. DONE authorized Support HTTP source5e0008c/ef9f2faf deployed09:52UTC; status route
   restored. Retrieval only returns the backfilled alias; missing mapping fails closed.
   Registration/invitation/alias/grant/admission/audit fingerprints unchanged.
3. DONE owner existing-ID retrieval/visible/Copy/restart/status authentication;
   unchanged installed APK/signer/UID/data/identity. DIAG snapshot/share/privacy PASS
   with non-null alias. Inventory28/24 active/4 revoked;1 known Android59,27 unknown.
4. DONE original hosted fixture/collection failures: source2b3c997,
   phase0/full Docker failover/index guard37120492530 PASS; Linux-control37120091177,
   Windows control37120091189, Android wire37120091156 PASS at ef554e7.
   BLOCKED terminal client37120091287: Linux/Windows main PASS, Android emulator
   Auto IPv6 bind EADDRNOTAVAIL and manual AWG teardown refusal FAIL; Windows2022
   upgrade broker-restart FAIL. Sequential Auto diagnosis now confirms production
   TCP TUN missing fd79:fc::2, with hosted address/route evidence and same-emulator
   manual dual-stack PASS. STOP at the explicit accepted-APK identity boundary:
   correcting AutomaticNormalEngine requires a changed Android binary. No production
   fix/rebuild performed. Resume only with authorization for changed candidate and
   renewed acceptance; then preserve/report Manual AWG primary+cleanup results and
   diagnose Windows2022 restart using bounded authoritative readiness, in that order.
   Existing IPv6 assertions remain intact; no all-green claim or new milestone.
   Unsigned min1/non-mandatory production59 payload prepared; offline signing only
   after accepted CI/downloads. Public APK/catalog/landing publication remains
   explicitly prohibited. Public51 bytes verified; no all-users-updated claim.
5. Retain owner; select only1–2 additional devices by Support ID. Never wildcard.
[Final task report](releases/2026-10-03-field1-release-final.md).

Previous foundation checkpoint (historical):
**FIELD-1-RELEASE + DIAG-1A authorized03.10; Stage5N remains CLOSED.**
1. DONE local source `b952c3b`: signed59,224/163 JVM,249 Python/1 skip, native race/vet,
   lint/build/package/privacy checks. Whole-index negative-test guard finding and
   hosted platform CI remain unresolved; no public59 catalog signed.
2. Owner in-place58→59/UID/identity/enrollment/readiness/Auto acceptance; no connected
   Redmi now. No diagnostic exhaustion in FIELD.
3. After acceptance only: immutable59, signed+legacy discovery, Android-only landing
   update, RU/EN hashes; no push before acceptance.
4. Select1–2 more trusted devices for2–3 total; current admission1 owner/no wildcard.
5. Observe receipts/incidents, no invented adoption or automatic widening/DIAG-1B.
[Current report](releases/2026-10-03-field1-release-diag1a.md). Below is history.

**5N-PHYSICAL-RESTRICTED-REHEARSAL = PASS; STAGE 5N = CLOSED,03.10.2026.**
Физический ручной CONNECT на private58 прошёл существующий production BOOT-1,
Family auth/Room Broker/dedicated restricted session и whole-device VPN.
Chrome/TLS, Family DNS, параллельный TCP и fail-closed измерены в Android user0;
границы доказательства и контролируемый RESTORING→FAILED сохранены в отчёте.
Override OFF подтверждён новым процессом, Auto восстановлен, READY/ACK сохранены.
Код/APK/server binaries не менялись; renewal в этой задаче не выполнялся; push нет.
**Дополнительного Stage5N gate нет. Следующая проектная фаза:**
1. 2–3 доверенных реальных field-canary.
2. DIAG-1A параллельно.
Эти работы не запущены автоматически; FIELD-1/DIAG-1/OPS-1/beta не начаты.
Короткоживущие credentials требуют обычной свежей проверки перед будущим запуском,
а не повторного развёртывания или открытия Stage5N.
[Финальное физическое доказательство](releases/2026-10-03-5n-physical-manual-rehearsal.ru.md).
Все следующие записи FAIL/BLOCKED и OPEN — сохранённая история, не текущий приоритет.

**5N-PHYSICAL-RESTRICTED-REHEARSAL = BLOCKED,03.10.2026; private hook FIX PASS.**
Canary58 privately installed in place; launcher resolved from package, checked durable
ON/OFF and fresh-process cleanup tests PASS.223 JVM/4 Python contracts, lint/build/APK
checks PASS; real encrypted restart READY/ACK_RECEIVED. No transport implementation change.
Actual remaining boundary is attended physical CONNECT: MIUI rejects ADB touch injection,
and no manual action occurred during120-second observation. No restricted CONNECT ran.
Override now OFF, Auto retained, app disconnected. Do not change security settings or
silently bypass the normal product action; no automatic retry/next phase in this task.
One credential-only renewal: gateway expires03.10 01:57:34UTC/directory01:52:37UTC;
NL READY/RU consistent, HTTP/AWG/TCP unchanged. Fresh checks remain necessary later.
Stage5N OPEN, same physical acceptance remains; no additional Stage5N gate is created.
No push/FIELD-1/DIAG-1/OPS-1/beta. Source fix/tests/docs remain uncommitted at911fea5.
[Current exact evidence](releases/2026-10-03-5n-physical-hook-fix-and-rehearsal.ru.md).

**5N-PHYSICAL-RESTRICTED-REHEARSAL = FAIL, final attempt03.10.2026.** Stop boundary:
private diagnostic Activity navigates to undeclared MainActivity in the Friends APK.
No restricted CONNECT was attempted; this is not evidence of transport failure.
Provenance committed as911fea5, exact57 now privately installed in place; real encrypted
restart READY/ACK_RECEIVED survives update. Override OFF in fresh process, Auto retained,
app disconnected. No automatic retry or live hotfix. Same physical acceptance remains
uncompleted; do not create another Stage5N gate or close Stage5N without measurements.
One accepted renewal gave gateway expiry03.10 01:27:17UTC/directory01:22:20UTC,
NL READY/RU consistent, HTTP/AWG/TCP unchanged. Do not use these historical windows
without fresh checks. No server redeployment/restaging, push or next-phase start.
[Current exact failure and evidence](releases/2026-10-03-5n-physical-restricted-rehearsal-final.ru.md).

Earlier checkpoints below are historical; their installed/version/expiry statements
do not override this result.

**5N-GATEWAY-RENEWAL-PUBLICATION = PASS,03.10.2026.** Ownership-loss operation
reproduced and fixed in a focused privileged publisher; 95 local tests PASS and all41
isolated root/DAC regressions PASS. One live accepted-policy renewal with Python/native
validation and service-owned0600 publication before rename; independent readback PASS.
NL READY/stable PID2771523/restarts0, actual served certificate matches; RU authority,
CRL/floor201 and directory consistent at00:09:45UTC. HTTP/AWG/TCP unchanged.
Fresh gateway expires03.10 00:54:48UTC; directory expires00:49:51UTC. Keep these bounded
lifetimes and fresh state checks; never reuse historical READY beyond expiry.
Private57 artifact reverified; **no install or physical rehearsal in this task**.
Stage5N stays OPEN; only the existing physical gate remains, under a separate task.
No new Stage5N milestone, full deployment, artifact staging or automatic continuation.
No push/FIELD-1/DIAG-1/OPS-1/beta.
[Current proof and operator procedure](releases/2026-10-03-5n-gateway-renewal-publication.ru.md).

Previous physical-task boundary (its publication blocker is resolved above):

**5N-PHYSICAL-RESTRICTED-REHEARSAL = BLOCKED,03.10.2026 (live02.10UTC).**
The final physical gate remains the only unproven Stage5N acceptance; no replacement
milestone. Exact HEAD0615953 private57 built/signed,218 tests/lint/APK checks PASS,
existing diagnostic exhaustion hook packaged privately; not installed or enabled.
Credential-only renewal Python/native PASS, but this session's publication adapter
lost live gateway profile service ownership; NL reload exited1 before READY.
Failure persisted, previous certificate/service ownership restored with new CRL floors
retained; bootstrap active/restarts0, ordinary HTTP/AWG/TCP unchanged. Redmi stays55.
Gateway expiry02.10 23:37:09UTC; next separately authorized continuation must use the
already accepted owner-preserving JIT publication, not a full redeployment or stale
authority/ACK. Do not automatically retry. No new source/runtime fix or gate here.
Still required: in-place57/persisted READY, normal Auto diagnostic exhaustion,
real BOOT-1→restricted whole-device VPN, Chrome/TLS/DNS/concurrentTCP, measured
fail-closed and safe controlled failure, then disable override. No physical checks run.
Stage5N OPEN; no push/FIELD-1/DIAG-1/OPS-1/beta.
[Evidence and rollback boundary](releases/2026-10-03-5n-physical-restricted-rehearsal.ru.md).

Prior accepted deployment checkpoint (not repeated in the physical task):

**5N-PROV-1 attempt17 = DEPLOYED / PHYSICAL BLOCKED,03.10.2026 (live02.10UTC).**
At `0615953`, accepted artifacts/source and exact installed55 PASS; hardened READY
staging verified/reused, schema14 present, same sole-owner authority Python/native PASS.
NL authoritative bootstrap and RU full sync PASS; closed HTTP/direct/fixture and
external ingress PASS. Actual owner challenge/fetch200/200 → authenticated READY ACK;
fresh encrypted persisted-state restart READY ACK PASS. HTTP committed only afterward;
old18084 retired,18086+NL+sync timer active,18085/AWG/TCP unchanged, floors preserved.
**Do not close Stage5N yet:** physical normal exhaustion and full restricted BOOT-1→
dedicated VPN→Chrome/TLS/DNS/TCP/fail-closed criteria remain unproven. Cellular-only
Friends VPN observed but not restricted; immutable non-debuggable55 lacks the debug
exhaustion entrypoint. No new gate/version/injection/shared gateway disruption. Keep
the accepted deployment/product evidence; later physical work must use fresh current
authority/directory/ACKs (gateway expiry02.10 23:37:09UTC), not replay old READY.
Post-use RU staging diagnostic found only generated bytecode; original9pins unchanged,
but strict inventory now rejects further reuse. Pre-consumption READY was PASS;
no cache cleanup, blind restage or post-hoc acceptance gate. See exact receipts.
No rollback or automatic retry; no push/FIELD-1/DIAG-1/OPS-1/beta. Next phases only
after existing5N closure:2–3trusted field canaries and DIAG-1A, not started here.
[Attempt17 evidence, remaining checks and committed-state rollback](releases/2026-10-03-5n-prov1-attempt17.ru.md).

**5N-STAGING-TRANSFER-RELIABILITY = FAIL (historical localization criterion),02.10.2026 UTC.**
Reliable staging implementation/regressions and controlled RU/NL inert staging PASS;
both READY with exact remote inventories/receipts. The historical45/50s layers remain
unresolvable from retained phase-less evidence; harmless exact source ingestion now
passes within those bounds, so no speculative cause/fix is asserted. Operator-only
`5b59461` replaces embedded binary source with bounded raw streaming, quarantine,
fsync/hash verification, atomic promotion and durable phase receipts. Runtime/ingress,
authority, DB and Redmi unchanged; no push. [Report/contract](releases/2026-10-02-5n-staging-transfer-reliability.md).
STOP here: Stage5N OPEN, no automatic PROV-1/FIELD-1/DIAG-1/OPS-1/beta. Future explicitly
authorized retry must consume receipt-verified staging, separately validate fresh
authority and complete the same existing real-owner/persistence/traffic criteria.

**5N-PROV-1 attempt16 = DEPLOYMENT FAILED / ROLLED BACK,02.10.2026.** Authorized9b3ec45
and exact current three pins/inventories plus installed55 verification PASS. Migrated
schema retained; RU Python JIT authority PASS, same sole owner/identities/delegation2/
grant2, CRL27→28. SSH command timeouts: operator staging45s, NL native-checker transfer50s;
read-only reconciliation found no completion artifacts. No native PASS, service startup,
ingress switch or owner request. Failure durable before rollback; normal services/config/
ports unchanged, final200/400/400/404, restricted RU/NL inactive. Stage5N stays OPEN.
Remaining: resolve pinned operator/native-checker delivery under explicit scope, then
the same existing end-to-end criteria, not a new gate or architecture. No automatic
retry, FIELD-1/DIAG-1/OPS-1/beta or push. Migration prerequisite remains satisfied;
historical attempt15 cause UNKNOWN. [Report/evidence](releases/2026-10-02-5n-prov1-attempt16.ru.md).

**5N-PROD-READINESS-SCHEMA = PASS,02.10.2026.** Explicit migration-only authorization
completed20:48:50UTC: protected online backup, one exact pinned receipts migration,
COMMITTED35.893ms. Required table present/empty; cookie14, user_version0. Existing
rows/schema unchanged; ordinary200/400/400/404, normal API/AWG/TCP unchanged, restricted
RU/NL inactive and route404. Local rollback/idempotence PASS,125 focused tests/6skip,
JVM↔Python23 PASS. No runtime deployment, authority refresh, ingress/device action or push.
Current schema prerequisite is satisfied; retain additive table on runtime rollback,
do not restore old full DB. Historical attempt15 cause remains unresolved. STOP: no
automatic PROV-1 retry, FIELD-1/DIAG-1/OPS-1/beta. A future explicitly scoped retry still
needs its own runtime/authority/server/real-owner acceptance; canary55 wire-compatible,
canary56 not required for functionality. [Evidence and limits](releases/2026-10-02-5n-prod-readiness-schema.md).
Earlier forensics authorization/missing-current-schema statements below are historical,
superseded by this completed migration only; no wider production authorization is implied.

**5N-PROD-SCHEMA-FORENSICS = HISTORICAL CAUSE UNRESOLVED,02.10.2026.** Read-only RU
confirms missing receipts table now and in18:40:27 pre-attempt15 backup; no migration
ledger/failure-time snapshot proves its18:45:03.869 state. Existing unnumbered migration
is additive; exact observed-schema local503→migration→200,99 regressions PASS/4skip.
Current schema upgrade remains required before any retry, but needs separate migration-only
authorization. Do not promote historical attribution or run a migration/authority refresh,
service/deploy/ingress/Redmi action, signing, push or PROV-1 retry. Canary55 remains wire
compatible;56 is not required for functionality. [Forensics/safety/next boundary](releases/2026-10-02-5n-prod-schema-forensics.md).

**5N-REAL-OWNER-CHALLENGE-503 = BLOCKED (local investigation),02.10.2026.** Actual
Android-generated bytes pass200 on current synthetic state; legacy missing receipts
schema deterministically yields503 at correlation_store/CORRELATION_SCHEMA_UNAVAILABLE,
then200 after existing explicit migration. Production attribution remains unknown;
do not infer it from this reproduction. No wire mismatch or circular ACK dependency.
Safe reason codes/golden regression added; [tests, builds and evidence limits](releases/2026-10-02-5n-real-owner-challenge-503.md).
Three local server artifacts rebuilt/pinned from `ad17db7`; unsigned code56 APK built
from `a10a9c4`, SHA256 `5ca1d29101df529cce197e5eeb82f231b50e3f4fc76c8835ba12fdad0c2122b0`.
App218/control163 JVM, assemble/lint and171 artifact/native tests PASS; existing whole-index guard finding remains.
These are diagnostic candidates only, not accepted production replacements.
Next: obtain already retained sanitized attempt15 backend/schema evidence and fix only
the proven cause. No production access/refresh/retry/service/ingress/push authorization
is implied. Prior rollout remains rolled back, installed55/public51 unchanged/unverified.

**5N-PROV-1 attempt15 = DEPLOYMENT FAILED / ROLLED BACK,02.10.2026.** Authorized
`014e6f9`/fresh exact pins: preflight, Python/native authority, NL, RU, candidate
and external server gates PASS; canary55 installed in place over54. Real Friends
restricted challenge503 prevents real-owner fetch/import/ACK/READY acceptance.
Failure persisted, routing restored/proved/drained before candidate stop, restricted
runtime rolled back. Ordinary18084/18085/AWG retained; delegation2/grant2/CRL27 retained.
No429/502 in scoped probes. [Full attempt15 record](releases/2026-10-02-5n-prov1-attempt15.ru.md).

STOP after this attempt; no automatic retry/live hotfix/push/DIAG-1/OPS-1/FIELD-1/beta.
Stage5N production provisioning/recovery line is **not closed**: actual product
challenge503 remains unresolved, not a new acceptance requirement. Existing remaining
checks are real-owner fetch/native encrypted import/READY/ACK, restart persistence,
local restricted rehearsal and browser/TLS/DNS/TCP/leak/fail-closed acceptance.
No root cause or pass is inferred from fixture F/G. Phone stays private55; no downgrade,
data reset, new release or public link changes. Any later work requires new scope;
do not execute it as continuation of this failed production transaction.

**5N-READINESS-ACK-ARTIFACT-REFRESH = PASS locally,02.10.2026.** HTTP, candidate adapter
and sync all required refresh; exact clean `a24f090` artifacts/source inventories are
now pinned, tested together and ready for a separately authorized deployment.
[Hashes/paths/acceptance contract](releases/2026-10-02-5n-readiness-ack-artifact-refresh.ru.md). Canary55 unchanged,
not installed; production/authority/Redmi untouched by this task. No runtime change.

STOP: no automatic PROV-1 retry, authority refresh, services, FIELD-1, DIAG-1 or OPS-1.
Future authorization must name these fresh pins, preserve existing transaction/admission
policies and establish real app post-import READY evidence, not fixture F/G or HTTP200.
Authenticated ACK correlates server challenge/fetch to device result; failed delivery
keeps local READY and server UNKNOWN. UI gestures are supplemental, never authoritative.
Prepared artifacts do not waive physical owner import/restart/rehearsal/traffic gates.

Read-only VPN audit02.10 18:05–18:06UTC complete:28 activated/24 non-revoked devices,
3 recent NL AWG peers,0 RU; no observed CPU/RAM saturation. Follow-up observations:
NL daily disk latency138.83ms; worker Docker unhealthy despite50 successful recent
cycles (outbox unverified); access API start changed. No repair/deploy/retry authority
or critical-path change. [Snapshot, limits and remaining checks](releases/2026-10-02-vpn-health.ru.md).

**5N-DEVICE-READINESS-RECEIPT = PASS locally,02.10.2026.** Post-validation/post-atomic
import product receipt v1 and authenticated ACK now replace UI-only owner acceptance.
Restart revalidates the actual encrypted bundle; expired/denied/stale state is not
READY. ACK failure is delivery UNKNOWN, not local readiness failure. Implementation
`e817380`; private canary55/code55 built/signed, NOT installed/distributed; beta51 and
installed54 are not changed. Tests/build/lint complete; [exact evidence](releases/2026-10-02-5n-device-readiness-receipt.ru.md).

STOP after this local gate. No authority refresh, services, production deployment,
FIELD-1, DIAG-1, OPS-1 or automatic attempt15. Remaining physical install/persistence,
real owner ACK and restricted traffic acceptance require separate authorization and
fresh production gates. Old attempt14 archives cannot serve the new ACK endpoints;
build/review/pin compatible server/runtime bundles first in a future authorized task.
No owner key export or UI automation prerequisite may replace the new product receipt.
Historical deployment checkpoints below are preserved, not new execution authority.

**Attempt #14,02.10.2026 — DEPLOYMENT FAILED / ROLLED BACK.** Accepted `d5105e8`
and pinned sync/HTTP/closed-readiness/APK inventories PASS. Actual JIT Python/native,
NL authoritative READY, full RU sync, direct candidate B–E plus controlled fixture
F/G, ingress switch and external A–E all PASS. No new acceptance requirement/source
change. Sole owner unchanged; delegation2/grant2/CRL25 retained.

Canary54 installed in place over field52; exact final APK/signature verified.
Server challenge/readiness200/200 observed during app launch, but owner UI receipt/
encrypted import/readiness was not collected: ADB input swipe failed255. These
server traces alone do not establish OWNER_PRODUCT_READY. Failure persisted, old
ingress restored/proved/drained before candidate stop; restricted stack rolled back.
Normal18084/18085/AWG/TCP unchanged; no commit or old retirement. Installed54 is
private, not a public/FIELD release; no downgrade/data clear.

STOP after this authorized attempt. No retry, live hotfix, attempt15, DIAG-1, OPS-1,
regional beta or FIELD-1. Remaining owner readiness/correlation, persistence,
restricted rehearsal, browser/DNS/concurrent-TCP and fail-closed checks are NOT RUN
or unverified, not waived. Any separately authorized execution must read actual
state, preserve monotonic25 (stage24 is historical), and refresh expired authority
through accepted machinery; old server PASS does not substitute fresh gates.
[Attempt14 evidence and rollback paths](releases/2026-10-02-5n-prov1-attempt14.ru.md).
Earlier checkpoints below remain historical and do not authorize further work.

**5N-HTTP-READINESS-ADAPTER-PACKAGING = PASS locally,02.10.2026.** Exact attempt13
transitive `provisioning` import failure reproduced before edits; the accepted HTTP
archive was complete, but the unclosed outer adapter lost its temporary ZIP search
root. Supported closed runtime replaces extracted test helpers; guarded bootstrap
persists missing-module/importer/stack metadata without secrets. Clean committed
export/repeat build and final-artifact outside-checkout B–G/current-authority/callback
smoke PASS;74 focused tests PASS. All accepted sync/HTTP/APK pins remain unchanged.

This closes the local packaging gate, **not PROV-1 deployment/owner acceptance**.
Only a separately authorized attempt may stage the pinned adapter/native/lock bundle
and use `Candidate.ready_with_adapter` after owned18086 verification. Reconcile live
state and validity afresh; repeat all accepted NL/RU/server gates. Keep old18084
through actual in-app F/G/import, then persistence/rehearsal/traffic acceptance.
Do not reuse old authority or treat controlled fixtures as owner evidence. No
automatic attempt14, DIAG-1, distributed beta, FIELD-1, Android release or push.
[Exact local report](releases/2026-10-02-5n-http-readiness-adapter-packaging.ru.md).
Earlier deployment observations below are historical, not renewed by this task.

**Resumed attempt #13,02.10.2026 — DEPLOYMENT FAILED / ROLLED BACK.** The earlier
no-device stop was pre-production only, not a production failure. Owner-authorized
resume verifies one Redmi/Android12/arm64 and field52 signature/in-place compatibility.
Accepted HEAD/APK/server pins/current native provenance PASS; no artifact rebuild
or application/committed-harness source change. JIT Python/native, NL authoritative
acceptance and RU --check/full acceptance PASS; retained history2/2/23.

HTTP candidate18086 starts with verified owned loopback PID, but the operator's
readiness callback raises `ModuleNotFoundError` before any controlled F/G/direct B–E
receipts. Exact module/traceback not captured. Ingress untouched, candidate stopped,
restricted rollback confirmed; old18084/18085 and normal product metadata unchanged.
Baseline/final ordinary200/400/400/404 PASS; no429/502 in8 resumed checks. Device
remains field52; canary54 uninstalled, no actual owner proof/import evidence.

STOP: investigate the scoped readiness adapter offline under separate authorization;
do not diagnose this as a proven HTTP server failure or change accepted source live.
No automatic retry. A future authorized execution must reconcile23 (stage22 is old),
check fresh validity/ports/pins, repeat NL/RU/complete candidate/external gates, then
install canary54 in place and require actual OWNER_PRODUCT_READY before retirement.
Restart/rehearsal/browser/DNS/TCP/fail-closed acceptance remains NOT RUN. No final
FIELD APK/public Android release, DIAG-1, distributed beta, FIELD-1 or push.
[Exact attempt13 evidence, failure boundary and rollback](releases/2026-10-02-5n-prov1-attempt13.ru.md).
Earlier entries below are historical checkpoints, not later live observations.

**5N-ANDROID-CANARY-BUILD = PASS locally.** Private canary54/code54 now contains
the accepted owner-proof handoff at `4bb53b0605c2c898b6a3feca6ee15fd34b943a94`.
Clean export, fresh arm64 JNI, full Gradle assembly/tests/lint and beta signing
completed; stale generated Python venv repaired through existing configuration.
No source fix/commit, installation, public distribution or production change.
Use only the exact [canary54 artifact/provenance](releases/2026-10-02-5n-android-canary-build.ru.md)
for a separately authorized attempt; canary53 lacks the new diagnostics.
Still pending: live prerequisites/server transaction, in-place installation at
post-switch product phase, real owner F/G, restart persistence and physical gates.
Local tests are not owner-device acceptance. No automatic attempt13 or FIELD-1.

**5N-OWNER-PROOF-HANDOFF = PASS locally.** The attempt12 acceptance boundary is
corrected: controlled isolated F/G plus live B–E/authority before switch; external
server A–E after switch; real F/G belongs exclusively to the Friends app during
product prewarm. No real-owner proof callback in operator HTTP paths. Old18084
remains available through product acceptance; only then commit/drain/retire.
Missing/failed product observations trigger safe rollback, not a credential export.
197 Python+38 source/acceptance guards and149 JVM tests PASS without skips;
112 Android Java sources compile. No production/device operation.

For a **separately authorized** rollout, stage the new standalone harness/trace
contract, prepare a verified same-signature canary with safe observation hooks,
recheck current authority and artifact provenance, then execute every server and
physical gate. Install/prewarm only at the post-switch product phase; keep normal
cache/cooldown/activation policy. Never count controlled F/G as physical owner proof.
The previously built canary53 lacks this hook and is not implicitly upgraded.
No app version/public distribution changed. See
[accepted contract](../deploy/friends/restricted/OWNER_PROOF_HANDOFF.md) and
[local gate report](releases/2026-10-02-5n-owner-proof-handoff.ru.md).
STOP after task-owned commit; no push or automatic attempt13/DIAG-1/beta/FIELD-1.
Entries below describe earlier checkpoints, including the now-resolved proof blocker.

**Attempt #12,02.10.2026 — DEPLOYMENT FAILED / ROLLED BACK.** Current source
`a02b82ec70269cd1e5486a26172b7a04d347cb7a`; fixed checker clean-export rebuild and
40 focused tests PASS. Python/native live authority, NL authoritative READY/BOOT-1
and RU isolated --check/full acceptance (including both negatives) PASS. History
advanced CRL19→20→21, delegation2/grant2 unchanged. Normal service metadata and
ingress18084 unchanged;18085 forbidden/untouched;18086 never started and free.

The remaining blocker is **accepted real-owner proof integration for HTTP G**:
the generic `Session.matrix` requires proof and cryptographic readiness callbacks,
but no real-owner signing bridge was available to this operator. The Android app
signs its own readiness request internally; do not extract keys, use a diagnostic
identity, skip G, or move physical work before server PASS without a new explicit
contract. Redmi connected (user report) is not equivalent to that proof integration.
This prerequisite should be resolved and checked offline **before** any next
authority refresh/runtime startup, not by another live attempt or hotfix.

Failure receipts preceded restricted-only rollback; current DB/runtime/NL CRL21
retained, RU stage20 historical. Full direct B–G/external A–G and all device gates
remain NOT RUN; no final FIELD APK. No commit/push/version change. STOP after
[attempt12 report](releases/2026-10-02-5n-prov1-attempt12.ru.md); no automatic retry,
DIAG-1, regional beta or FIELD-1. Earlier entries below are historical checkpoints.

**5N-NATIVE-AUTHORITY-COMPAT = PASS offline.** Exact #11 binary/material replay
proves the failed predicate: negative floor1+1 equals signed owner revision2,
so native admission succeeds and the old operator reports failure. Native runtime
semantics are correct; no stale binary (byte-identical rebuild), no producer/native
contract mismatch. [Reproduction and compatibility matrix](releases/2026-10-02-5n-native-authority-compat.ru.md).

Local code commit `8b829971…` adds the tracked checker, safe durable standalone
adapter, clean-export builder and tests. Checker SHA256 `a1df5f88…`, exact full pin
in the report, is **built/tested, not installed**. Existing sync/HTTP pins and all
runtime validation/security policy remain unchanged. Original #11 failure remains
historical; current production was not redeployed or refreshed by this task.

STOP after task-only commits/documentation; no automatic attempt #12 or physical
work. A separately authorized rollout must accept/pin and install the new checker
and receipt adapter per [runbook](../deploy/friends/restricted/NATIVE_AUTHORITY.md),
reconcile delegation2/grant2/CRL19 without resetting history, check current validity,
then repeat every NL/RU/HTTP/device gate. Do not use historical debugger clock replay
for acceptance of expired live authority; production tools have no clock override.
No source/authority workaround, skipped negative, Python-only fallback, beta or FIELD-1.

**Attempt #11,02.10.2026 — DEPLOYMENT FAILED / ROLLED BACK before runtime startup.**
Accepted HEAD `4f482027…`, sync `9d965b95…`, HTTP `460e7520…`: exact source/inventory
and isolated artifact gates PASS; live18086 ss+bind availability PASS,18084/18085
owners untouched. Same-key24h authority renewal completed: delegation2, sole-owner
grant revision2, minimum revision1, expiry03.10 11:54:56UTC. CRL19 expires02.10
12:12:08UTC; gateway leaf12:57:08UTC. Existing native authority checker exit1 at
11:57:10UTC is a mandatory prerequisite FAIL, not permission to weaken a negative
check. [Attempt #11 result and exact limits](releases/2026-10-02-5n-prov1-attempt11.ru.md).

STOP after scoped rollback/state confirmation; no automatic retry, DIAG-1, beta or
FIELD-1. Do not reset delegation/grant/CRL history or use expired reservation1 as
current authority. Fresh inspection must reconcile manifest2, renewal reservation,
grant2 and floor19 on RU DB/runtime/stage and NL. Static retained checker source
uses minimum_revision+1 as its negative threshold, which is no longer necessarily
above renewed owner revision2; actual failure branch is suppressed/unobserved.
This is a separately scoped review candidate, not a confirmed live TLS root cause
or an implemented fix. No runtime/harness source or security policy changed here.

NL authoritative bootstrap, RU live --check/full sync including both negatives,
HTTP direct B–G/ingress A–G and commit remain NOT RUN. So do Redmi prewarm/restart,
local restricted rehearsal/user-level traffic and final private FIELD APK. Final
ordinary200/400/400/restricted404 and unchanged normal service metadata PASS;
AWG/TCP active, no new dataplane validation. Retain new authority/floors, protected
rollback inputs and all receipts; any later authorized attempt needs sufficient
fresh validity and complete gates. No commit/push/version change; unrelated work
and #3 UNKNOWN/#9 incomplete attribution preserved.

**5N-HTTP-CANDIDATE-PREFLIGHT = PASS locally, no deployment.**118 focused tests pass
without skips; actual isolated nginx and unchanged pinned archives are used. Use the guarded
public `transaction`/`Candidate` contract, not the old port18085 assumption or the
internal rollback primitive. Candidate18086 is a singleton allowlist, not a fresh
availability claim; source/evidence identify18085 as Friends TCP/Xray. Collision,
unknown owner, failed bind, changed generation/artifact or non-loopback binding STOP
before ingress change. Direct matrix is application B–G; external matrix is nginx
static A plus proxied B–G. Never add handler GET support just to satisfy ingress A.
[Local gate and test evidence](releases/2026-10-02-5n-http-candidate-preflight.ru.md).

Next deployment requires separate authorization, fresh host port/generation readback,
all NL/RU/HTTP gates and JIT renewal checks for **delegation/issuer, owner grant,
CRL and gateway credential**. Preserve Family/issuer/gateway/sole owner,0 other
admissions, TTL policy and floors; staged16 must not replace authoritative18.
No refresh/deployment/phone/build/push in this task; no automatic attempt #11.
Retain all #10/#9 evidence and unrelated work; local task-only commit is authorized.

**Attempt #10,02.10.2026 — pre-deployment STOP; production unchanged.** Explicit
authorization does not make candidate18085 available: live RU readback identifies
that socket as the existing Friends TCP/Xray API, PID1908885. Never stop/rebind it
for HTTP. Exact pins/source inventories/imports PASS; paced ordinary baseline
200/400/400/restricted404 PASS. Independent exact-archive localhost check finds
direct A/status501: status200 belongs to static nginx, whereas prior local
candidate tests exercised direct B–G only.
[Attempt #10 report](releases/2026-10-02-5n-prov1-attempt10.ru.md).

Next requires an explicitly accepted transition contract with an unused candidate
listener and clarified direct/ingress status gates, not a silent port substitution,
weakened acceptance or live handler hotfix. No automatic attempt #11. Authority
refresh was not performed: delegation/issuer/owner grant expired10:44:11UTC;
runtime/DB/NL floor18 must not be reset to staged16. Keep the same Family/issuer/
gateway/owner and TTL policy during any future authorized renewal. NL/RU acceptance,
candidate/ingress A–G, physical prewarm/restart/rehearsal and final private FIELD APK
remain NOT RUN for #10. Runtime/ingress/services/registration and grant rows remain
in #9 rollback state; old18084 stays alive, AWG/TCP not restarted. No code/version
change, commit, push, beta or FIELD-1; existing dirty work/history preserved.

**5N-HTTP-TRANSITION-DIAG: BLOCKED only on exact historical attribution.** Actual
nginx1.30.4 reproduces #9's429 schedule through unchanged shared `per_ip` policy;
stop-before-start reproduces a socket-refused502 window. #9 lacked upstream/rule/
errno telemetry, ingress logs were disabled/crit, journal reads bounded-unavailable.
Do not call replay evidence a captured production root cause; #3 remains UNKNOWN.
[Separate diagnosis and tested local contract](releases/2026-10-02-5n-http-transition-diag.ru.md).

Local future operator uses one paced stream, durable correlated receipts and
readiness-first second listener; original listener survives switch/commit, rollback
restores/drains before candidate stop. Limits/ordinary semantics remain intact.
Three complete A–G matrices and three additional paced live switches pass in
isolation, not production. Any exact historical attribution needs retained
contemporary evidence if available; no automatic rollout can reconstruct it.
STOP: no attempt #10, phone, Android build, authority/admission change, push, beta
or FIELD-1. A future deployment still requires explicit authorization and all gates.

**Attempt #9,02.10.2026 — DEPLOYMENT FAILED / ROLLED BACK.** Authorized source
`028300e…` and exact sync/HTTP pins PASS. Corrected committed NL operator now
passes live authoritative READY/directory/stability even with diagnostic journal
timeout. RU `--check` and complete committed sync/negatives/final readback PASS.
HTTP activation still fails the hard ordinary-route gate: transition429/502;
matrix A–D PASS individually, non-canary loop6×403 then429, F/G not reached.
[Separate #9 report and evidence](releases/2026-10-02-5n-prov1-attempt9.ru.md).
Scoped rollback complete; ordinary200/400/400/restricted404 restored, AWG/TCP
unrestarted, normal registrations/grants preserved, sole owner and27 denied.
Authoritative final floor18 retained on RU DB/runtime and NL; staged16 is stale.
Delegation/grant expiry10:44:11UTC, gateway10:31:33UTC, final CRL09:48:20UTC.

**STOP after #9, no automatic production retry or hotfix.** Next separately scoped
work should explain the durable HTTP transition429/502 and non-canary429, including
probe cadence/ingress behavior, without assuming that it explains historical #3
(still UNKNOWN). Any future attempt needs explicit authorization, current-source
pins, fresh authority/JIT and complete gates again. Owner HTTP F/G, normal product
regression completion, Redmi product prewarm/restart, local restricted rehearsal,
browser/DNS/leak/fail-closed/underlay checks and final private FIELD APK remain
unperformed. No protocol/admission change, public release, push, beta or FIELD-1.
The earlier STOP notes below describe their own historical task boundaries.

**5N-NL-ACCEPTANCE = PASS,02.10 — local operator correction.** Authoritative NL acceptance
now uses fresh READY-only export plus valid directory, same gateway profile and
healthy stable service; fsynced authoritative verdict comes before optional journal.
Journal5s timeout/nonzero exit is diagnostic only, while real service/deadline/
directory failures remain FAIL. Exact attempt-#8 replay: old FAIL → corrected
PASS+diagnostic_timeout. [Local test/receipt proof and commit scope](releases/2026-10-02-5n-nl-acceptance.ru.md).
RU acceptance policy/operator and both runtime artifacts remain unchanged.

**STOP after local correction/finalization.** No deployment attempt #9 is authorized
by this fix. Any future explicit rollout still requires fresh source/artifact pins,
current authority/JIT, baseline, new NL operator, complete RU sync/negative gates,
HTTP A–G and all physical gates. Attempt #8 remains a rollback caused by the old
operator's diagnostic gate, not a bootstrap/provider defect. No credentials,
production operations, Redmi, Android build, push, beta or FIELD-1 in this task.

**Attempt #8,02.10.2026 — DEPLOYMENT FAILED / ROLLED BACK.** Exact accepted HEAD,
new sync `9d965b95…` and unchanged HTTP `460e7520…` pass source/inventory/isolated
checks. JIT CRL15 and gateway renewal PASS; one NL seed/live directory validation
PASS. The NL operator then incorrectly gated acceptance on diagnostic journal
collection;5s timeout caused rollback before RU precheck/full sync and HTTP.
This is an operator error, not evidence of a broken pinned artifact or provider.
[Exact timestamps, acceptance limits and rollback](releases/2026-10-02-5n-prov1-attempt8.ru.md).
Baseline/final ordinary200/400/400, restricted404; normal PIDs and registration/
grant rows unchanged. Actual registry28 total/27 restricted-denied, sole owner
canary unchanged. Authority expiry02.10 10:44:11UTC; CRL15 expiry08:51:45UTC and
gateway expiry09:36:45UTC. RU DB/stage and NL floor15 must be preserved; inactive
RU runtime14 is not authoritative. No Redmi/APK/commit/push/beta/FIELD-1.

**STOP after attempt #8; no automatic retry or production repair.** A subsequent
separately authorized task must make NL journal diagnostics non-gating and retain
the exact failed-command category before verdict/rollback, without changing runtime
architecture. Then a newly authorized rollout must recheck current pins/authority,
reconcile monotonic floors, JIT refresh and repeat every live and physical gate in
order. The committed RU sync operator was not reached and must not be replaced by
the historical inline/journal-gated flow. Real owner HTTP G/readiness, restart,
local restricted rehearsal and final private FIELD APK remain unperformed.
Historical #3 UNKNOWN and #6/#7 pre-production stops remain unchanged.

**5N-SYNC-ARTIFACT-REFRESH = PASS locally, 01.10.2026.** Exact clean source
`f4c06df…` now has a matching sync candidate `9d965b95…`, not an exception to the
source pin. `restricted.py` is required by sync and CRL publication; preserve the
existing minimal explicit manifest.17-entry inventory/all source bytes match HEAD;
194 committed regressions +7 exact-archive checks PASS, no skips, including local
complete operator/negative sequence and new-sync→unchanged-HTTP signed readiness.
Old sync `cb6f050e…` retired as a deployment input, kept unchanged as evidence;
HTTP `460e7520…` unchanged/not rebuilt. [New pin, dependency proof and test limits](releases/2026-10-01-5n-sync-artifact-refresh.ru.md).
Attempt #7 history remains a pre-production STOP; no rollback required. Its local
artifact blocker is resolved, but no production gate is thereby accepted. Only a
separately authorized attempt may consume the new exact pin after fresh baseline,
JIT authority, NL READY/live directory, RU precheck/full sync negatives, HTTP A–G,
normal regression and physical gates. No credentials/services/Redmi/APK/push here.
STOP; do not automatically start attempt #8, beta or Krasnodar FIELD-1.

**Attempt #7 STOP — exact-source/pinned-sync conflict, 01.10.2026 19:55UTC.**
HEAD `f4c06df…` and both requested hashes PASS; full17/25-entry inventories and
embedded bytes PASS. HTTP matches accepted HEAD. Pinned sync's shared
`control/friends/restricted.py` differs only in the documented HTTP challenge
input-validation hunk (`9b5d5ce2…` versus HEAD `ab3542b9…`); its accepted precise
directory code is not the mismatch. Followed the explicit any-mismatch STOP rule
before production access, without declaring the known difference exempt. No
refresh/deployment/live gates/Redmi/APK/rollback/retry/commit/push. [Attempt #7
receipt, source diff and remaining checks](releases/2026-10-01-5n-prov1-attempt7.ru.md).
Next needs a separately explicit decision accepting that exact sync-source
difference, or a separately accepted matching artifact/source checkpoint and
updated pins. Do not rebuild/substitute under attempt #7. After resolution, a new
authorized attempt must repeat fresh baseline/JIT/NL/RU/full negative/HTTP/physical
gates in order. Attempts #1–#6 preserved; #3 remains UNKNOWN. No beta/FIELD-1.

**New-session recheck01.10:** actual entry `d8624dea2cffe3c41d9d136a6f93ee527b8f3812`
already includes both requested HTTP commits. Fresh clean export rebuilt the same
`460e7520…` HTTP artifact;274 tests PASS, no skips, plus old/new embedded timestamp
regression including malformed timestamps. No runtime source changes needed.
Recheck final source pin/inventory/tests are in
`state-client-build/http-packaging-git-recheck/`; preserve all four unrelated diffs.
Only separately authorized rollout may consume the clean candidate; production
credentials, services, Redmi, push, attempt #7, FIELD-1 and beta remain out of scope.

**5N-HTTP-PACKAGING-GIT: local source checkpoint created (01.10.2026).**
Code/tests/HTTP CI commit `f7b3b6c29526fb600990f60d57449571a8538f22` closes the
missing tracked-builder/entrypoint/manifest/harness gap; clean source builds the
precise-directory HTTP candidate `460e7520…`, not retired `eb9eb06f…`.274 targeted
working-source checks PASS. Exact clean-HEAD inventory/startup/A–G/precision/
receipts/sync fixture must remain verified in the [handoff evidence](releases/2026-10-01-5n-http-packaging-git.ru.md).
Only separately authorized attempt #7 may consume this candidate, after all
production pinning/JIT/baseline/NL/RU/negative/HTTP/physical gates in order.
No refresh or rollout is implied; source acceptance is not owner readiness.
Keep unrelated VPN-health/attempt-#5 evidence outside the HTTP commits. STOP.

**5N-HTTP-ARTIFACT-REFRESH = FAIL, local-only clean-source audit (01.10.2026).**
Exact HEAD8663128 contains the accepted precision fix but not the HTTP packaging
prerequisites: builder, manifest/drop-in, durable harness, matrix tests and handler
`main()` changes remain uncommitted. No dirty overlay, new archive or source edits
were made.59 committed precision tests PASS; old embedded HTTP consumer rejection
reproduced; sync pin unchanged. Old HTTP `eb9eb06f…` is retired as a rollout input,
not deleted or replaced. [Full evidence](releases/2026-10-01-5n-http-artifact-refresh.ru.md).
Next requires separately reviewed/accepted packaging prerequisites in a new source
commit and an updated explicit source pin; do not claim those changes belong to
8663128 or include retained work without review/authorization. Then rebuild from
that clean source and run all ten artifact gates. No automatic implementation,
deployment attempt #7, refresh, services, Redmi, push or FIELD-1.

**Attempt #6 STOP — deployment input source mismatch, 01.10.2026 18:31UTC.**
Both requested pins and internal inventories pass, but immutable HTTP archive
`eb9eb06f…` predates the accepted nanosecond validation/delivery fix in HEAD
`8663128…`; its shared restricted module differs from both HEAD and retained
worktree. Sync archive `cb6f050e…` matches committed source. No production access,
refresh, deployment, rollback, Redmi, APK, retry, commit or push in attempt #6.
Before any separately authorized new attempt, reconcile/accept a current-source
HTTP artifact and its route/readiness tests and new immutable pin offline; do not
silently rebuild/replace this attempt's pinned artifact or consume unrelated work.
Then reverify all gates/JIT floors from live authority, not old staging or expired
receipts. This note authorizes neither preparation changes nor another deployment.
[Attempt #6 evidence and remaining gates](releases/2026-10-01-5n-prov1-attempt6.ru.md).

**5N-SYNC-ACCEPTANCE = PASS locally after attempt #5.** Воспроизведён timeout
чтения journal10s до negative checks; synchronous runtime не переделан в async.
Новый bounded operator проверяет authoritative unit/result/CRL/directory и обе
negative gates; безопасные step/timeout/state/readback receipts fsync до возврата
ошибки. Историческая №5 остаётся FAILED/ROLLED BACK; журнал/I/O latency root cause
не установлен. Никаких production операций в этой задаче. После локальных проверок
STOP; возможный новый rollout требует отдельного разрешения, повторного pinning и
актуальных monotonic floors (последний live readback14), а не повторения №5.
[Контракт и доказательства](releases/2026-10-01-5n-prov1-production-restricted-provisioning.ru.md).

### История до исправления RU acceptance

**5N-DIRECTORY-VALIDATION = PASS locally (01.10); production unchanged.**
Attempt #4 reproduced from unchanged private evidence/exact old Python archive:
valid fractional `issued_at` compared against a truncated integer-second clock,
safe predicate `time/issued_in_future/issued_at`. Source fix `29d15d7` retains
nanosecond current time in operator validation, gateway sync, RU sync and delivery;
no BOOT-1 schema/producer/native change, tolerance or TTL extension. Strict
negative matrix, live-shape/real producer cross-component tests, private old FAIL/
new PASS replay and durable classified receipt checks pass.

**STOP after local commits/documentation.** No deployment/credential refresh,
services/Redmi/APK/push/FIELD-1. Attempt #3 HTTP cause remains UNKNOWN. Any separately
authorized attempt #5 must use the pinned corrected closed validator and
`directory-check` receipts, not archived `int(time.time())` operator snippets;
reconcile then-current authority floors before JIT refresh and revalidate all
server/physical gates. Local PASS is not production acceptance.
[Exact artifact and root-cause evidence](releases/2026-10-01-5n-prov1-production-restricted-provisioning.ru.md).

### Historical checkpoints — before offline reproduction

**Attempt #4: 5N-PROV-1 = DEPLOYMENT FAILED / ROLLED BACK (01.10,17:13–17:15UTC).**
Explicit authorization used only for this attempt. Source HEAD and accepted HTTP
archive/all25 entries unchanged. JIT CRL11→12/native authority PASS, same single
owner/Family/issuer/gateway/TTLs. NL native READY/one canonical UTC-Z seed, but
Python live-directory validation raised `ValueError`; full NL acceptance failed.
Rolled back before RU `--check`/sync/API activation; ordinary HTTP200/400/400,
restricted404, normal API/AWG/TCP unchanged. No Redmi or client-level acceptance.
Exact rejected predicate is not established; do not infer it or retrospectively
diagnose attempt #3, whose historical cause remains **UNKNOWN**.

**STOP after rollback.** Preserve quarantined NL directory and safe receipts for
separately scoped local reproduction. No live fix/automatic retry. Any future
authorized deployment must refresh from authoritative DB/staged CRL12/NL floor12,
not expired inactive RU CRL11; gateway leaf expires18:13:46UTC, CRL17:28:46UTC.
No DB/serial/revocation-floor rollback, identity changes or TTL extension. Physical
readiness/restart/local rehearsal/browser/DNS/fail-closed gates remain unperformed.
No commits/push/public release/FIELD-1. [Attempt #4 evidence](releases/2026-10-01-5n-prov1-production-restricted-provisioning.ru.md).

### Historical local revalidation — before explicit attempt #4 authorization

**5N-HTTP-LIVE-REVALIDATION = READY FOR DEPLOYMENT AUTHORIZATION (01.10,16:59UTC).**
Exact retained HTTP archive and source inventory match; restricted-enabled local
nginx/HTTPS matrix PASS,188 tests PASS/4 optional Go checks skipped. Packaged
operator receipts are durable before verdict/rollback, including shell EXIT trap
and upstream-failure/recovery simulation. Attempt #3 historical cause **UNKNOWN**;
local success does not retrospectively diagnose its lost HTTP evidence.

**STOP at authorization boundary.** No explicit separate authorization for attempt
#4 in this conversation; do not infer it from the gate title or earlier attempts.
Next authorized scope: recheck/pin the tested HTTP archive/config/harness; back up
only relevant RU/NL state; JIT refresh CRL/gateway certificate from authoritative
monotonic floors (last recorded11, not staging6), preserving Family/issuer/gateway/
owner-only admission and TTLs. NL bootstrap READY/UTC-Z; exact closed RU sync
`python -I --check`, live sync, stale-CRL/shell rejection must pass before API
activation. Then six durable live HTTP receipts; any ordinary regression requires
rollback before Redmi. Only after HTTP PASS: real owner in-place prewarm, restart,
local cellular Auto rehearsal, Chrome≥2 sites/Family DNS/concurrent TCP/leak and
fail-closed/underlay proof. No final FIELD APK, push or FIELD-1 in this gate.
[Exact evidence and remaining work](releases/2026-10-01-5n-prov1-production-restricted-provisioning.ru.md).

### Historical attempt #2 checkpoint — superseded by #3 and local revalidation

**Попытка №2: DEPLOYMENT FAILED / ROLLED BACK (01.10 13:39UTC).**
Полная Android canary53 сборка/194 tests/lint PASS; подпись field52 совместима,
установки нет. NL живой UTC-каталог/READY/Python interoperability PASS.
RU sync завершился до publisher/SSH: `ModuleNotFoundError: clients` через
`provisioning.friends_catalog` → `clients.desktop.profile_config`.
Полный source checkout/authority staging скрывали runtime packaging dependency.
[Доказательства](releases/2026-10-01-5n-prov1-production-restricted-provisioning.ru.md).
**STOP после отката.** Далее только локальное уточнение минимального runtime
manifest и isolated import/CLI smoke точного RU/NL deployment bundle без checkout
на sys.path; затем исправление runbook. Не добавлять случайные файлы на live-хост.
Новый rollout — только после отдельного разрешения и JIT refresh после sequence5,
с прежними TTL/Family/issuer/owner-only admission. Без auto-retry/push/FIELD-1.

### Исторический checkpoint перед попыткой №2

**5N-TIME-COMPAT: local PASS (01.10).** Producer canonical UTC output + strict
offset-aware Python/native input implemented; shared Z/positive/negative/actual
failure fixtures, nanosecond bounds and replay checks pass. Python91, JVM6,
Go race/vet4 packages and local builds PASS. [Evidence](releases/2026-10-01-5n-prov1-production-restricted-provisioning.ru.md).
**STOP before deployment.** Production remains rolled back. A separately
authorized retry must rebuild/re-stage fixed Go/Python, refresh short-lived material
without resetting floors/extending TTLs, then revalidate seed/sync/API before phone
prewarm. No auto-retry, physical testing, final FIELD APK, push or FIELD-1 here.

### Historical deployment failure and repair prerequisite

**5N-PROV-1: DEPLOYMENT FAILED / ROLLED BACK (01.10 11:48UTC).** Authorized
NL seed reached READY, but offset `ExpiresAt` from context deadline is rejected by
the Python `Z`-only directory parser. New NL service/auth disabled, snapshot
quarantined; RU runtime/routes/sync unchanged. Normal production healthy;
owner-only admission preserved. [Evidence/rollback](releases/2026-10-01-5n-prov1-production-restricted-provisioning.ru.md).
**STOP.** Next engineering task: local producer/consumer RFC3339 compatibility
fix with non-UTC regression coverage and unchanged BOOT-1 validity/trust semantics.
Then new JIT CRL/gateway refresh and separately authorized controlled retry. Do not
work around by live JSON/timezone edits, extend TTLs, start phone acceptance or
produce final FIELD APK before infrastructure passes. No automatic rollout/push/FIELD-1.

### Historical material-only preflight

**5N-PROD-DEPLOY-PREFLIGHT: READY / no deployment (01.10 11:21UTC).** Owner input
confirmed; provider metadata/schema PASS without value/hash/size disclosure.
Publisher CRL3 expires11:35:38UTC; gateway leaf12:20:38; unchanged sole-canary
authority/issuer/grant/delegation. Actual material/native/sync validation PASS.
[Current inventory/evidence](releases/2026-10-01-5n-prod-deploy-preflight.ru.md).
**STOP.** No services/API/routes/ingress/prewarm/FIELD-1 or push. Separately
authorized rollout must recheck freshness and refresh again if needed, preserving
floors/TTL; staged runtime/account/venv installation is not yet performed.

### Historical owner-input blocker — resolved by owner input and fresh validation

**5N-PROD-DEPLOY-PREFLIGHT: BLOCKED at owner hidden token input (01.10).**
Authorized staged refresh complete: same authority/canary, CRL2 expires11:26:23UTC,
gateway leaf12:11:23; no TTL changes, no runtime activation.32 tests/native PASS.
Next: owner runs the [single secure SSH procedure](releases/2026-10-01-5n-prod-deploy-preflight.ru.md),
confirms without sending token; validate only file metadata/nonempty/schema and
revalidate/refresh certificate/CRL freshness before any later deployment window.
Do not unlock KeePass, create rooms, start/reload services, enable routes, prewarm
phone or retry full deployment. No FIELD-1/push. Provider configuration is the
remaining preflight blocker, not permission to deploy once entered.

### Historical authority checkpoint — before refresh/input authorization

**5N-PROD-AUTHORITY: READY / staged only (01.10).** Explicit first-Family/gateway
designation authorization executed: one existing Owner grant, other admissions0,
same NL control-provider identity, local offline-root delegation, real initial CRL.
Additive four-table result/backup and18 tests/actual native validation PASS; no
normal runtime changes. [Exact evidence](releases/2026-10-01-5n-prod-authority.ru.md).
**STOP before provider-token phase**; do not access KeePass or retry deployment.
Next separately authorized actions must renew short-lived CRL (initial expiry
01.10 11:02:45UTC), leaves/delegation as needed; install staged account/helper/venv,
then provider config/seed/sync/API only under appropriate deployment authorization.
Phone READY/restart/rehearsal/final FIELD APK still not proven. No FIELD-1/push.

### Historical Phase A authority blocker — superseded by explicit creation authorization

**5N-PROD-MATERIALS: BLOCKED at Phase A (01.10, entry9340931).** Protected operator
state resolves one active Owner device administrator, but no existing ProductStore
Family/entitlement for that identity; cross-store identity overlap0. Existing NL
control-provider/mailbox identities have no accepted restricted-gateway binding.
Owner must identify the protected authoritative assignment/binding, not paste
private identifiers or create replacement roots/identities. Only after resolution:
derive legal floors, apply the now-authorized additive migration, initialize CRL
through the real publisher, sign delegation locally, prepare gateway/canary state.
Do not reuse unrelated relay sequence9 as restricted issuer/peer revision.
Then reach the owner-interactive provider token step; token remains absent.
Inert staging/deny-all policy preserved; no migration/signature/service change in
this continuation. No automatic deployment retry, broad admission or FIELD-1.
[Exact inventory/status/owner actions](releases/2026-10-01-5n-prod-materials.ru.md).
TLS renewal inspection found active timer/latest successful no-op and valid cert;
no certificate infrastructure change. Phone/rehearsal/final FIELD APK remain pending.

### Historical controlled-deployment preflight

**5N-PROV-1: controlled deployment authorized, preflight STOP (01.10 09:32UTC).**
Required `friends-restricted/` отсутствует на обоих hosts: RU issuer/delegation/
anchor/admission/CRL/sync material; NL gateway profile/provider OAuth configuration.
По explicit user stop rule никакие материалы не генерировались, partial deploy
не начинался. Нужно сначала подготовить/указать authoritative production material
по [runbook](../deploy/friends/restricted/README.md), не заменяя его diagnostic
fixtures, и повторить preflight. This attempt is stopped; deployment authorization
не является доказательством готовности secrets. До успешного preflight: no API/DB/
ingress changes, phone install/prewarm/rehearsal/final FIELD APK. Existing production
service snapshot healthy кроме прежнего peer-worker healthcheck; no rollout.
[Audit и remaining gates](releases/2026-10-01-5n-prov1-production-restricted-provisioning.ru.md).

### Historical implementation checkpoint — ff9fb09

**5N-PROV-1 (01.10): IMPLEMENTED / DEPLOYMENT AUTHORIZATION REQUIRED.**
Уточнение принято: BOOT-1 v1 содержит bootstrap seed `join_url`, не dedicated
descriptor, без новой standalone directory signature. Initial delivery через
existing activated Friends proof/HTTPS, без circular Family mTLS prerequisite.
Local server issuance, same-DB grants/CRL sync, root-delegated issuer, Android
validated atomic encrypted import/prewarm и deterministic tests реализованы.
Python95/JVM193/Go race+vet/fresh JNI PASS; hardware validation ещё не выполнялась.
Следующий шаг **только после отдельной deployment authorization**: owner-only
RU API/issuer/sync + NL production seed/broker по
[runbook](../deploy/friends/restricted/README.md). Затем same-signature private
validation update, actual-Friends READY/restart, local restricted rehearsal
(browser/DNS/fail-closed). Лишь после live PASS — final shareable FIELD APK.
Directory≤1h; CRL15min может сокращать окно. Prewarm перед тестом, не обещать
offline readiness спустя часы. Public beta51/private field52 не менялись.
Historical BLOCKED audit `a88b104` сохранён в
[отчёте](releases/2026-10-01-5n-prov1-production-restricted-provisioning.ru.md).

LOCAL readiness01.10 **BLOCKED**: actual Friends field52/code52 in-place/restart
PASS, Identity PRESENT/normal provisioning PRESENT_VALID, restricted Family TLS
profile и BOOT-1 cache ABSENT. Нужен отдельно разрешённый production integration
existing Friends identity→Family TLS provisioning→authenticated directory delivery;
до него нет безопасного normal prewarm или actual-Friends restricted rehearsal.
Не подменять identity/cache isolated fixtures. Field52 APK только readiness,
не accepted FIELD-ready; public beta51/catalog неизменны. Предыдущий BLOCKED
preflight сохранён. [Readiness gate](releases/2026-10-01-field1-device-readiness.ru.md).

### CURRENT PRODUCT CRITICAL PATH — 30.09.2026

1. **5N-BOOT-1 — restricted bootstrap (PASS, isolated physical30.09).** Cached directory
   survives restart; diagnostic normal endpoint deliberately unavailable; real
   Telemost/Family auth → broker READY → dedicated descriptor through bootstrap →
   separate dedicated DNS/HTTPS proof без manual URL или forwarding. Gate завершён,
   STOP; [отчёт](releases/2026-09-30-webrtc-5n-boot1-bootstrap.ru.md).
2. **WEBRTC-EU-6 / 5N.6 — PASS, isolated physical30.09.** Existing VPN owner/packet
   engine → cached BOOT-1/dedicated Family Mux/DNS; Chrome2 sites,14 concurrent TCP,
   98 DNS,543.7s smoke, protected underlay, UDP/IPv6 fail-closed, controlled session
   failure с сохранением TUN, cleanup. [Отчёт/scope](releases/2026-09-30-webrtc-eu6-android-full-device.ru.md).
3. **Minimum viable Connectivity / Transport Orchestrator — PASS, isolated physical01.10.**
   Одна кнопка, bounded deterministic state machine, same-owner guard/handover,
   normal preference/LKG → alternate normal → BOOT-1/fresh dedicated whole-device,
   sticky healthy path, один restoration pass. Redmi normal/alternate/restoration/
   bounded exhaustion проверены. Follow-up01.10: fresh current-source JNI исключил
   stale binary как причину Chrome failure. Исправлено неподтверждённое IPv6 source
   advertisement automatic TCP при IPv4-only gateway; Chrome2/HTTPS/alternate/
   restoration PASS. Fresh activation/OAuth: automatic restricted32621ms, Chrome6/6,
   HTTPS/TLS2×200, Family DNS/concurrency/underlay/UDP/IPv6 fail-closed PASS.
   Smoke602.6s без crash/flapping/retry storm; controlled loss RESTORING→FAILED138ms,
   retained VPN и blocked ordinary TCP. Final cleanup PASS, OAuth не persisted.
   Исходный FAIL сохранён; no public rollout/push/production changes. STOP, не FIELD-1;
   [отчёт, blockers и оставшиеся physical checks](releases/2026-09-30-mvp-connectivity-orchestrator.ru.md).
4. **Krasnodar FIELD-1 (NOT RUN).** Реальная ограниченная мобильная сеть,
   обычное устройство и приложения, без engineering harness.
5. **Product beta — 50–100 реальных пользователей (PLANNED).** Проверить
   успешность подключения, восстановление, стабильность и семейный invitation UX.

Это авторитетный порядок; нижние хронологические записи и STOP относятся к своим
датам/gates, не являются актуальным заданием на выполнение. 5N.1–5N.5, REL-1,
PERF-2 и **automatic Room Broker = PASS** в изолированной physical acceptance.
**Bootstrap PASS в isolated cached-state core/diagnostic path;
full-device restricted VPN не выпущен.** OAuth был только в runner/server memory;
Redmi cellular/Wi-Fi OFF/no VPN. Первая live попытка выявила только premature
cleanup validation в runner; focused fix, Python20 и повторный live run PASS.
Cleanup BOOT-1 завершён, production не менялся. EU-6 завершён; текущая отдельная
авторизация — только MVP Orchestrator/integration/tests/physical acceptance.
FIELD-1, второй carrier, performance tuning и production rollout не разрешены.
STOP после текущего gate; отсутствие live evidence не считать PASS.
[Архитектура и продуктовые принципы](architecture.md) ·
[Фактический статус](STATUS.md) · [Отчёт rebaseline](releases/2026-09-30-product-engineering-rebaseline.ru.md).

### Product phases — без перенумерации исторических gates

| Phase | Состояние | Цель / граница |
| --- | --- | --- |
| A — Foundation | DONE / existing | Device Identity, FAMILY admission, invitations/provisioning, Android/Linux/Windows base. Не обещание завершённого family dashboard. |
| B — Normal connectivity | WORKING beta | AWG/TCP уже используются; существующий Android VpnService/VPN lifecycle. |
| C — Restricted data plane + setup proof | TECHNICALLY PROVEN, isolated physical acceptance | 5N.1–5N.5, ReliableStream, DNS containment и Room Broker. Broker — control-plane proof, не production bootstrap. |
| D — Restricted bootstrap | PASS / 5N-BOOT-1, isolated physical | Cached authenticated directory/restart → bounded seed → Family TLS → broker READY → separate dedicated session; no control forwarding. Diagnostic endpoint-denial, не FIELD-1/production. |
| E — Android full-device | PASS / isolated physical5N.6 | Existing OS lifecycle/packet path ↔ existing 5N core; ordinary Chrome/TCP/Family DNS, protected underlay, fail-closed failure и UDP/IPv6, bounded cleanup. Diagnostic opt-in, не public release/iOS. |
| F — Minimum viable Orchestrator | PASS / isolated physical01.10 | Fresh native; normal Chrome IPv6-advertisement fix; automatic normal exhaustion→BOOT-1/restricted, browser/DNS/concurrency/containment,602.6s smoke/restoration/cleanup. Original FAIL retained; no public rollout. FIELD-1 не запускать. |
| G — FIELD-1 | AFTER F / NOT RUN | Реальный restricted/allowlist mobile field, сначала Краснодар; не лабораторный echo. |
| H — Product beta | AFTER G / PLANNED | 50–100 пользователей: reliability, battery/heat, support и invitation UX. |
| I — Scale / iOS / carriers | LATER, после beta evidence | iOS, multi-user load, дополнительные gateways/carriers, масштабирование инфраструктуры, monetization/referrals. |

**D implementation:** cached authenticated bootstrap directory → bootstrap rendezvous carrier →
Family authentication → `REQUEST_TRANSPORT` → existing Room Broker → fresh dedicated
room → dedicated Family Session. Bootstrap — control-only/rendezvous, не постоянный
bulk VPN. [Код/лимиты/runbook](../carrier/bootstrap/README.md): существующий mTLS,
protected atomic cache, одна активная exchange, server challenge/setup binding,
без нового signing root. Старый Room Broker PASS использовал forwarding; BOOT-1
runner использует direct mTLS только для prior cache, затем запрещённый normal
endpoint и исключительно Telemost rendezvous. Physical phases A–E и cleanup PASS30.09.
Deterministic checkpoint: focused Go/race x10/vet, Python118, Android native/APK/
JVM9/lint, docs/source guard PASS. Live runner fix: focused Python20 PASS.
Следующих действий внутри BOOT-1 нет;5N.6 завершён по отдельной авторизации.
Подробные timestamps, первая failed acceptance и artifact hashes в датированном отчёте.
Fresh install уже внутри completely restricted сети вне scope. Rollback — остановить
только task-owned процесс/удалить diagnostic APK/cache; production не изменяется.

**E acceptance PASS:** existing ConnectionService/TcpVpnService/Xray сохранены,
shared packet/session boundary и protect bridge подключены. Physical primary-user
VPN routes + ordinary app/browser + counters доказали TCP/DNS и отсутствие direct
bypass в принятом scope (не root modem pcap/другие user profiles). Session failure
держит TUN; stop/cleanup PASS. Go/packet race/vet, Python50, Android JVM172/build/
lint PASS. Normal factories/owner regression сохранена, normal physical path не
перетестирован; старый CI emulator failure остаётся отдельным. Generic UDP и IPv6
Internet не поддержаны; global ReliableStream HOL остаётся, seamless migration,
always-on process-death lockdown, iOS/capacity/production rollout не доказаны.

**G acceptance:** то же обычное устройство без engineering harness; в наблюдаемом
ограниченном состоянии normal transports недоступны, Family автоматически
проходит restricted bootstrap и подключается. Browser/DNS/обычные приложения
работают; разумная длительность сессии и восстановление проверяются по заранее
заданным условиям. Пока **NOT RUN**, критерии длительности/восстановления ещё надо
зафиксировать до field run. Один пользовательский случай AWG3.1/TCP unavailable,
Telemost available в Краснодаре не обобщается на всех операторов/регионы/времена.

### Product metrics — будущие, не уже собираемые

North star: **Successful connection without user intervention** — успешное
подключение без действий пользователя сверх CONNECT. До beta определить denominator,
окно наблюдения и допустимое время соединения; измеренных product SLO пока нет.
Supporting metrics: connection success rate; time-to-connected; automatic recovery
rate / reconnect success; disconnect rate; crash-free sessions; battery/thermal
behaviour; transport success by coarse network context; support requests / 100 users;
invitation conversion; retention. Это план измерений, не утверждение о deployed telemetry.
**Не собирать содержимое трафика или историю просмотров** ради этих метрик;
network context только укрупнённый, с минимизацией данных.

### Operational / later / backlog — вне product critical path

- LOCAL FIELD-APK preflight01.10: USB Redmi получил in-place private APK2644790,
  activation UI/UID сохранены, Auto/launch PASS; без CONNECT или forced failure.
  **BLOCKED:** non-debuggable Friends не предоставляет проверенный read-only
  private-state/BOOT-1 diagnostic; presence/validity/usability UNKNOWN. Не считать
  это отсутствием cache или готовностью к field; не создавать cache неявно.
  [Отчёт](releases/2026-10-01-field1-local-preflight.ru.md). FIELD-1 не начат.
- FIELD-1 packaging01.10: private arm64 APK2644790 собран/подписан beta-ключом,
  package/signature/version совместим с beta51; runtime не менялся. Установка,
  наличие/валидность existing BOOT-1 activation/cache на field device не проверены.
  [Build receipt](releases/2026-10-01-field1-apk.ru.md). **FIELD-1 NOT STARTED**;
  сборка не закрывает field gate и не выполняет provisioning отсутствующего cache.
- Read-only audit01.10,17:43UTC:27 устройств/23 не отозвано, без прироста с13:39;
  NL5 свежих AWG peers/12 с handshake<24ч,4 с transfer за15с;RU0,TCP0 обоих gateways.
  CPU NL9.92%/RU11.54%, CPU/RAM без перегрузки в15с снимке; HTTPS не перепроверен.
  Disk await NL144.26/RU34.33ms и worker healthcheck/outbox остаются открытыми;
  RU API start01.10 14:40:45UTC изменился с прошлого аудита, причина не проверена.
  Restricted services не перепроверялись; никаких restart/deploy, capacity/DAU не измерены.
  [Снимок и границы](releases/2026-10-01-vpn-health.ru.md). FIELD-1 не начат.
- CI после sync: phase0 failover-stack build и Android emulator lifecycle FAIL;
  исправление отдельно, без переоценки принятых isolated gates. [Статус](STATUS.md).
- Ops: NL disk latency, RU API restart, worker healthcheck/outbox, TLS monitoring
  и client E2E follow-ups. Поддержка работающей beta не подменяет gates D–H.
- **Второй restricted carrier — backlog.** Telemost уже доказал архитектуру;
  VK/WB/другие нужны только при meaningful coverage/reliability gap по field/telemetry,
  не автоматически «следом за Telemost».
- Home Gateway / RNS-over-WebRTC — secondary/backlog. FEC/HOL optimisation и
  performance tuning — позже по evidence, не текущий blocker. Не обещать production
  capacity до отдельной load acceptance. iOS и scale — phase I.

## Historical gate ledger / Сохранённая история до rebaseline

Записи ниже сохранены без перенумерации. Их слова «current», «next», «STOP»,
старый sync push и preparation-only относятся к указанным checkpoint, а не к
нынешней задаче. Source of truth для нового порядка — секция наверху.

- 30.09 repository sync only: preserve completed worker, disk/TLS/VPN audits and
  existing58-commit history; focused32 tests/unit verification/publication scan PASS.
  Push main to origin/main without force, then fetch and verify exact HEAD equality.
  [Sync checkpoint/inventory](releases/2026-09-30-repository-sync.ru.md).
  Older no-push notes are historical for this authorized synchronization only.
  No BOOT-1/TUN/Orchestrator/new development or production work; stop after sync.
  Existing pre-sync CI failover-build failure and operational follow-ups remain open.

- 30.09 10:44–10:46UTC VPN audit: traffic lower than last evening, devices25/21
  unchanged, VPN services active. Follow up RU access API restart03:28:04UTC,
  NL disk await96.92ms60s, worker healthcheck/outbox and client end-to-end.
  HTTPS/cert-renew PASS; no deployment/version/5N gate changes.
  [Report](releases/2026-09-30-vpn-health.ru.md).

- 29.09 19:39–19:41UTC repeat load check confirms increased NL VPN traffic:
  AWG TX17.19Mbit/s10s,9.03Mbit/s60s; no CPU/RAM saturation in samples.
  Devices25/valid21 unchanged. Keep NL disk latency (minute await95.78ms),
  worker healthcheck/outbox and client acceptance open. No rollout/version/5N change.

- 29.09 17:51–17:52UTC read-only VPN snapshot:25 devices/21 valid unchanged;
  NL4 recent handshakes/3 transferring, RU0; CPU4.01%/12.93% NL/RU.
  HTTPS:8443 PASS, service starts unchanged. Keep worker healthcheck/outbox,
  sustained NL disk latency and physical-client checks open; no deployment,
  version change or change to5N STOP. See evening section in VPN health report29.09.

- 29.09 12:32–12:35UTC read-only follow-up: VPN traffic and :8443 TLS PASS;
  automatic certificate service09:04:21UTC success. Devices25/valid21 unchanged.
  Follow up worker Docker unhealthy (inherited API healthcheck,17 recent cycles0),
  sustained NL disk latency and physical-client acceptance; no changes authorized
  or performed by this audit. Versions/rollout/5N gates unchanged.

- 29.09 authorized [disk mitigation](releases/2026-09-29-disk-io-recovery.ru.md)
  deployed: RU persistent reconciler (same15s/60s semantics), NL SSH Fail2ban.
  ~45% fewer disk writes in short samples, live checks/32 tests PASS; no VPN restarts.
  Subsequent3min sampling confirms lower writes, but NL write-await117ms remains;
  next operational check is daily sampling
  after SSH protection warms up, then VPS IOPS/latency investigation if reproduced.
  No claim of full disk repair, no change to client versions or5N gates.

- 29.09 [VPN audit and authorized TLS recovery](releases/2026-09-29-vpn-health.ru.md):
  manual service run08:32:25UTC success; nginx now serves existing renewed IP cert
  through05.10 12:25:56UTC, VPN/API starts unchanged. Timer active, next observed
 29.09 09:18:29UTC; monitor that cycle and diagnose earlier timeout if repeated.
  Retain disk-latency diagnosis, privacy-safe usage history/alerts
  and client end-to-end checks as follow-ups. No version/rollout/5N gate changes.

- **5N-RB-1 = PASS**, authorized28.09, core ff25246/integration398df64:
  one fresh official PUBLIC room per admitted bounded setup; gateway READY before
  Android descriptor; expiry/replay/device binding and cleanup. Physical Redmi→
  Telemost→Amsterdam Family TLS +4 HTTPS200/DNS PASS without manual room URL.
  Focused tests/race/vet/Android PASS; control ingress isolated SSH+adb reverse,
  no production bootstrap/rollout/capacity claim. Foreign VPN changes preserved.
  [Report](releases/2026-09-28-webrtc-5n-room-broker.ru.md). Gate checks complete.
  **STOP**; no5N.6/TUN/UDP/Orchestrator/performance/load/production work or push.
  Previous Room Broker STOP entries below are historical and superseded only
  by this explicitly authorized isolated gate.

- **WEBRTC-EU-5 / 5N.5 = PASS**, explicitly authorized28.09:
  bounded mux + wire DNS over one admitted TLS/reliable/VP8 session; default16/max32,
  fixed64KiB credit/16KiB DATA, fair RR. Final clean native/APK `c26c2b7`.
  Physical4 public HTTPS/TLS200,304.138s mixed5 persistent TCP +171 Family DNS;
  exact18.75MB duplex,915 interactive replies; client destination DNS guard0 calls.
  Host/native/race×3/fuzz/build/Python1004, security/legacy TCP/lifecycle/fresh-session
  regressions and cleanup PASS; early attempts and shutdown correction retained.
  [Report/evidence](releases/2026-09-28-webrtc-eu5-mux-dns.ru.md).
  No unfinished acceptance checks. **STOP after5N.5**, no automatic Room Broker,
  5N.6/TUN/UDP/Orchestrator/production rollout/push. Full-device DNS not claimed.

- **WEBRTC-EU-4 / 5N.4 = PASS**, explicitly authorized: single admitted TCP stream,
  core `2b977da`/RST fix `fa3c027`, final clean tested CLI/APK `63f6bde`.
  Physical Redmi→Family TLS→ReliableStream→Telemost→Amsterdam→public HTTPS200,
  verified end-site TLS,10MiB public download; controlled10MiB duplex exact and
  22,511,616B each direction/300.820842906s/1.197343416Mbit/s aggregate.
  FIN/half-close/structured errors/RST/cancellation/fresh-session recovery PASS.
  Bounded buffers,0 bad-MAC/corruption/duplicate/missing on completed transfers;
  regressions (including518 canonical exact and controlled gap1/1) and cleanup PASS.
  Initial public-fixture timeout/RST/HTTPS-close failures retained; no firewall or
  production changes. [Report/evidence](releases/2026-09-28-webrtc-eu4-single-tcp.ru.md).
  **STOP after5N.4**; no unfinished acceptance checks. No automatic5N.5/mux/TUN,
  production rollout or push. Further work requires separate authorization.
  Earlier STOPs below are historical gate boundaries, not current pending work.

- **5N-PERF-2 = PASS**, explicitly authorized on27.09 after REL-1.
  Baseline cap2/300s reproduced; six120s discovery points0.5/1/1.5/2/2.5/3.
  Highest accepted reliable goodput1.742311Mbit/s at cap3/1800s; conservative
  demonstrated1.480531Mbit/s at cap1.5/900s. Defaults16KiB/sender8/receiver16/RTO1s
  unchanged. No sustained overload threshold/hard carrier ceiling established;
  cap2.5 transient warning does not prove a rate-specific ceiling. Queues/resources
  bounded; exact/auth/lifecycle/fault/local+Android regressions and cleanup PASS.
  No unfinished PERF-2 checks; foreign concurrent VPN work preserved separately.
  [Report](releases/2026-09-27-webrtc-5n-perf2-reliable-envelope.ru.md).
  **STOP** after PERF-2; no automatic5N.4, production default, rollout or push.

- **5N-REL-1 = PASS**, explicitly authorized
  successor to PERF-1 investigation. TLS → bounded selective-repeat ReliableStream
  → unchanged VP8/RTP; sender8/receiver16,16KiB. Physical300s accepted data run:
  4315 exact echoes, delivered1.883505Mbit/s at offered cap2; no bad MAC/corruption.
  Natural29/29 gaps and controlled seq2 recovered with TLS survival. Deterministic
  faults/security/native/physical checks PASS; canonical500 exact echoes, live
  admission negatives/lifecycle/network-loss/fresh recovery PASS. Go race×3/vet/
  modules/fuzz,153 Python, Android build/6 JVM/lint/ARM suites PASS. APK/private
  artifacts removed; own PIDs/remote dirs0, radios1/1 restored. Three failed/incomplete
  harness attempts preserved; sanitized20-run evidence verified. Runtime `ecc884c`,
  clean build `d14a92f`, final tests/observer `bbcea5e`. No rollout/push.
  [Report](releases/2026-09-27-webrtc-5n-rel1-reliable-stream.ru.md).
  **STOP**, no automatic5N-PERF-2 or5N.4; no unfinished REL-1 checks.

- **5N-PERF-1 = FAIL — измерения завершены, sustainable ceiling NOT ACCEPTED**.
  Historical raw-TLS/VP8 boundary; loss recovery is addressed by REL-1 above,
  without retroactively promoting this old capacity gate or claiming a ceiling.
  Canonical baseline reproduced; все7 windows,6 offered rates и5 payload sizes
  проверены. Error-free60s peak1.992294Mbit/s (paced2), completed300s
  0.130635Mbit/s (16KiB/window2); high-load long checks FAIL with TLS/RTP gaps.
  No retries-to-green, failed points retained. Final canonical370 checks/300s и
  lifecycle regression PASS; APK/remote/local private artifact cleanup завершены,
  sanitized29-run evidence проверен. [Capacity report](releases/2026-09-27-webrtc-5n-perf1-carrier-capacity.ru.md).
  После отчёта **STOP**, не запускать5N.4 или transport redesign автоматически.
  Remaining engineering questions: causal RTP-gap/stream rejection diagnosis,
  reproducible high-load300s stability, synchronized finer stage timings/true ceiling.
  Это не authorization на исправление carrier или новый production rollout.

- current: **5N — Restricted WebRTC Android→EU** (Telemost VP8 carrier → authenticated
  Family session → headless Linux EU gateway → TCP+DNS → Internet).
- **WEBRTC-EU-1 / 5N.1 = PASS**,27.09, runtime `a13068e` (clean): настоящий
  Linux dev ↔ Telemost VP8 ↔ Amsterdam,7 размеров +100×1/16KiB +30s +5min,
  **291 byte-for-byte echo**, без corruption/timeout/disconnect/reconnect.
  5min useful roundtrip0.065538Mbit/s, RTT≈4s; это baseline, ceiling не установлен.
  Waiting room не потребовался; application heartbeat устранил live WS4008.
  Race×3/fuzz/vet/modules и live WS-close/SIGTERM/remote exit PASS; temporary
  EU process/artifacts удалены, production/версии/каталоги не менялись.
  **WEBRTC-EU-2 / 5N.2 = PASS**: clean `3f65346`, physical Redmi Note9 Pro/
  Android12/arm64 ordinary cellular↔Telemost VP8↔Amsterdam.372 exact echoes,
  30s/5min, no corruption/timeout/unexpected disconnect; RTT≈2s, aggregate0.131069Mbit/s.
  Первый full run RTT≈4s/0.065536Mbit/s тоже PASS; performance не production-ready.
  Isolated APK/shared Go core, lifecycle/cancellation/network-loss/WS-close tested,
  Linux regression и Android checks PASS, temporary processes/artifacts cleaned.
  Wi-Fi handoff/deep Doze/protected sockets/restricted5M не заявляются.
  **WEBRTC-EU-3 / 5N.3 = PASS27.09**: isolated Family TLS1.3 admission,
  runtime `5dd8b49`,374 exact echoes/302.001s sustained, valid/negative/replay и
  lifecycle/cellular-loss/explicit recovery PASS. Avg RTT1999.914ms,
  useful aggregate0.131071665Mbit/s; ceiling неизвестен. Два ранних SSH-lifetime
  FAIL сохранены; accepted run использует independent observer, unchanged runtime.
  Diagnostic APK удалён, credentials/test processes0; no rollout/push.
  [Отчёт/evidence/rollback](releases/2026-09-27-webrtc-eu3-family-session.ru.md).
  TUN/TCP/WB не начинались; последующий5N-PERF-1 приведён выше, затем STOP.
  [Отчёт/оставшиеся проверки](releases/2026-09-27-webrtc-eu1-telemost-binary.ru.md).
  [Android5N.2 checkpoint](releases/2026-09-27-webrtc-eu2-android-binary.ru.md).
- после accepted5N.5: отдельное решение о Room Broker и затем5N.6; автоматически не начинать.
- после этого: restricted-mobile acceptance **5M**.
- **WB fallback** — только после подтверждения Telemost на реальной сети.
- **5.3a / 5.3в** и **Home Gateway (5A–5M secondary track)** — backlog, не запускаются автоматически.
- Параллельно (WIP, не блокирует 5N): упрощение invitation/activation — server-side
  authenticated recovery `POST /friends/device/status`, canonical URL `/i/`, smart landing
  page, QR=canonical URL. Fresh-install sideload **не** заявляется fully automatic:
  Flow A (приложение установлено, 1 действие), Flow B (sideload: возврат на landing +
  «Открыть», 3–4 действия). Real-device Android E2E ещё не пройден.
- Параллельно (завершено, не блокирует 5N): Linux-дистрибуция — AppImage + .deb как
  основной публичный артефакт вместо operator preview tar.gz. Packaging реализован
  (`scripts/package_linux.py`, `packaging/linux/*`, CI linux/release jobs), собран в CI,
  принят на чистой Ubuntu 24.04, опубликован на HTTPS; invitation landing отдаёт
  AppImage (`.deb`/`.tar.gz` secondary). AppImage не self-contained по GTK-стеку.
  [report](linux-appimage-deb.ru.md).
- Backlog (не реализуется сейчас, требует Friends DB/API/schema): product split
  «Personal Invitation» (один получатель → одно Device Identity → consumed) vs
  «Referral Link» (sponsor capability → N получателей, quota/TTL/revoke). Текущий UI
  описывает ссылку нейтрально — «Отправьте эту ссылку человеку, которого хотите
  подключить», без утверждения «строго одно устройство».

Gate-таблица и порядок — ниже в секции `DECISION25.09 — Restricted WebRTC → Linux EU`.

27.09: [read-only аудит VPN за26–27.09](releases/2026-09-27-vpn-health.ru.md).
23 устройства/19 действующих; NL минимум9 сегодня, полный DAU неизвестен.
AWG NL19.143/13.764ГиБ (Brussels, сегодня до23:10); RU почти без трафика.
CPU среднее NL5.68/6.02%, RU20.31/20.19%; AWG/TCP active, версий/rollout нет.
Journal reads timed out, дисковое давление после чтения прошло: NL iowait1.96%
к21:14UTC, RU6.38% к21:17UTC, RU sync success. Отдельный ops backlog: мягкая диагностика
диска без тяжёлых journal scans, обезличенная история DAU/одновременности/TCP,
alerts и E2E. Не меняет порядок5N-PERF-2 и не разрешает production changes.

26.09: [аудит использования и сбоев VPN](releases/2026-09-26-vpn-health.ru.md).
22 устройства/18 действующих (+4 с24.09); NL12 с handshake<24ч,4 свежих,
3–4 передают трафик; RU0. Найдена история sysstat: AWG около26.7ГиБ с24.09
до26.09 08:40UTC, в основном NL; средний CPU25.09 RU20.3%/NL5.2%.
25.09 AWG restart NL7с/RU20с; RU снова stop-sigterm timeout, оба после
unattended-upgrade libexpat1. Во время чтения журналов высокий iowait и
тайм-ауты chat-sync; затем sync success, к08:50UTC iowait снизился на обоих: RU6.1%/NL5.8%.
Открыты: дисковые задержки (отдельная диагностика), alerts sync/HTTP, история
устройств/TCP, сквозная клиентская проверка. 26.09 исправлено завершение RU AWG
по SIGTERM: TimeoutStopSec=20→90 (шаблон install-awg.py + drop-in на RU),
чистая остановка1с вместо timeout20с/SIGKILL; rollback — удалить drop-in.
Production/версии не менялись.
26.09 Android: в исходники главного экрана Friends добавлен выбор сервера
с флагом и нагрузкой на момент выбора (RU/NL, `server-load.json`, кэш15с).
Android beta51/code51, Linux0.2.11 и Windows0.2.15 собраны и опубликованы
(APK/discovery/invite, desktop GitHub/HTTPS, Windows catalog sequence11) —
см. [отчёт](releases/2026-09-26-server-list-crossplatform.ru.md).

25.09: лицензирование опубликовано в GitHub main, commit
`aa3ed9f801a83a4808df3352abc300d235a7c42c`: LICENSE, notices, audit и README RU/EN.
Публичный LICENSE скачан по immutable commit и побайтно совпал с проверенным
локальным текстом. Push выполнен из отдельного checkout поверх139f7da; текущая
локальная ветка разработки не перебазирована, незавершённые изменения сохранены.
[Отчёт](releases/2026-09-25-license-publication.ru.md). Версии/production не менялись.

## DECISION25.09 — Restricted WebRTC → Linux EU: новый критический путь

**Для ограниченной мобильной сети приоритет — Android → Telemost VP8 → Linux EU
Gateway → Internet. Windows Home PC и IP-over-Reticulum не prerequisites.**
Основание: пользовательский видеозвонок Telemost Краснодар→Бельгия прошёл при
недоступном прямом Family VPN. Community-код показывает binary/media реализации,
но наши headless/binary/Family tests пока не выполнены. Убираем зависимость от
home IP/NAT, Windows routing, включённого ПК и лишнего домашнего hop.

[Решение в существующем дизайне](reticulum/HOME_GATEWAY_DESIGN.md#decision-restricted-webrtc-to-eu-gateway-first--2026-09-25)
· [Checkpoint](releases/2026-09-25-webrtc-eu-priority.ru.md).
**Мы на глобальном этапе5: restricted Android→EU track.** 27.09 пользователь
разрешил восстановить и продолжить только5N.1 transport PoC; carrier реализован
локально; последующая live-проверка27.09 закрыла5N.1 (см. current priority).
Прежний preparation-only scope
относился к25.09; после5N.1 PASS пользователь отдельно разрешил5N.2 Android.
Старые немедленные планы через Windows/RNS ниже — история прежнего приоритета,
а не условия начала нового track. Существующие номера5A–5M не переиспользовать.

Добавлен **5N — Restricted WebRTC Android→EU**, со стадиями:

| Gate / подэтап | Результат | Статус |
| --- | --- | --- |
| WEBRTC-EU-1 / 5N.1 | Два независимых Linux через настоящий Telemost VP8: byte-for-byte binary echo нескольких размеров | PASS27.09:291 checks,30s/5min и live failure cleanup; source a13068e |
| WEBRTC-EU-2 / 5N.2 | Android↔EU Linux binary round trip без TUN | PASS27.09: physical Redmi/Telemost VP8/Amsterdam,372 exact echoes,30s/5min; runtime3f65346 |
| WEBRTC-EU-3 / 5N.3 | E2E Family session с existing Device Identity/FAMILY; wrong/revoked/replay rejected | PASS27.09: physical Android,374 exact echoes/302.001s; isolated runtime5dd8b49; no production authority rollout |
| WEBRTC-EU-4 / 5N.4 | Один TCP stream: реальный HTTPS response через EU | **PASS28.09**: physical HTTPS200/public10MiB, exact duplex300.821s, half-close/faults/security/cleanup; [evidence/limits](releases/2026-09-28-webrtc-eu4-single-tcp.ru.md) |
| WEBRTC-EU-5 / 5N.5 | Core-level multiplexed TCP + DNS, bounded fairness/flow control | **PASS28.09**: physical4 public HTTPS,304.138s mixed5 TCP+171 DNS, exact/fair/bounded; [evidence/limits](releases/2026-09-28-webrtc-eu5-mux-dns.ru.md); no OS/browser interception |
| WEBRTC-EU-6 / 5N.6 | Full-device Android TCP+DNS, EU exit, fail-closed unsupported traffic | **PASS30.09**, isolated physical primary-user VPN/Chrome;543.7s,14 TCP/98 Family DNS, controlled failure/cleanup; [scope/limits](releases/2026-09-30-webrtc-eu6-android-full-device.ru.md) |

Порядок: reuse generic5H/5I contracts →5N.1–3 на целевой мобильной сети →5N.4–6 →
5M реальная30–60min приёмка (связана с5F) →5L WB fallback. Telemost первый,
WB только после Telemost validation, VK/future позже.5J/5K RNS-over-WebRTC/Home
Gateway и Home5B–5E сохраняются вторичными; NAT traversal/direct home paths и
Meshtastic emergency bootstrap не блокируют5N. Старые numeric5.1–5.6 control/fleet
задачи также не объявлены завершёнными и не возобновляются автоматически.

Data-plane: existing VpnService/TUN conversion → Family stream mux → authenticated
E2E session → opaque VP8 carrier → headless family-restricted-gateway → egress.
Проверить reuse Xray TUN inbound из pilot/android-tcp/tcp-android.go до введения
второго tun2socks. Existing Transport/ConnectionService/selection/provisioning
расширять новым WebRtcRestrictedTransport, не создавать второй TransportManager.
Изолированный carrier ничего не знает о Family auth, DNS/destinations и routing.
Linux gateway интегрируется с existing entitlement/revoke/provisioning и server
infrastructure. Выбор audited session/mux/reliability libraries — до реализации.

Phase1 TCP+DNS; phase2 UDP. Mux: OPEN/DATA/CLOSE/RESET с bounded flow control,
half-close, quotas и reserved datagram framing; одна conference на session, не
на запрос браузера. DNS внутри E2E session; неподдерживаемые UDP/IPv6 блокировать
без direct fallback. Сохранить socket protection, kill switch, auth/replay/expiry,
provider isolation/TLS verification. Повторное создание carrier не должно повторять
старые application writes. Service SFU не является доверенной Family стороной.

Reticulum сохраняется для identity binding, provisioning/control/recovery,
emergency messaging/discovery и future Personal Gateway/Meshtastic. Весь high-bandwidth
VPN не помещать в RNS без результатов сравнительных benchmarks. AWG/TCP/XHTTP
остаются first-class; будущий auto-select идёт от доступных existing transports к
Telemost при ограничениях. Пока новые flags OFF, production/defaults неизменны,
UI CONNECT без настройки протоколов. Providers remotely disableable через verified
config с TTL/revision/offline ограничениями. Telemost API failure не ломает другие paths.

Краснодар — решающая среда: Android cellular only, Wi-Fi OFF. В одном тестовом окне
сравнить ordinary FC FAIL / Telemost video PASS / Family Telemost PASS. Замеры:
setup,5/30/60min,RTT,throughput,CPU,memory,battery,reconnect count/time. Сценарии:
screen off/on,data off/on,airplane on/off,cellular reconnect,room recreation,EU
restart; browsing,large file,video,many HTTP streams. >5Mbit/s stable PoC,
>10–20 good,>30 strong — цели без текущих измерений. Stability важнее peak.
Ближайший engineering milestone после возобновления — **authenticated Family data
Android Краснодар → Telemost VP8 → EU Linux**, потом full-device Internet. UI polish
и Windows gateway до этого не требуются. WEBRTC-EU-1 PASS27.09; gates2–6 open.

## 25.09.2026 — Telemost: полевое подтверждение пользователя

Android в ограниченной сотовой сети Краснодара успешно завершил видеозвонок
Yandex Telemost с Бельгией, при этом прямое подключение Family Connect VPN
недоступно. **Источник — сообщение пользователя; это не инструментальный тест
нашего carrier.** [Запись и границы](releases/2026-09-25-telemost-cellular-evidence.ru.md).

Приоритет первого carrier PoC изменён: **Telemost первым, WB резервным**.
Подтверждён один штатный видеозвонок, а не headless API, произвольные binary frames,
RNS Link или Home Gateway. Все WEBRTC-1–5 остаются открытыми. Данные об операторе,
версиях клиентов, длительности/скорости, ICE/TURN/SFU path и ОС в Бельгии не получены.
Этап5/подготовка5A–5H продолжается; по прежнему уточнению пользователя пока только
документация и подготовка. Код/версии/production не менялись.

Следующий шаг после возобновления реализации: Telemost headless join → desktop
binary round trip → Android↔Windows → RNS announces/Link. Проверять именно тот
carrier/media путь, который использует PoC; работа штатного видеоклиента не
доказывает достижимость всех API/серверов. Не запрашивать/хранить cookies в документации.

## WebRTC extension25.09 — superseded immediate ordering (backlog: RNS-over-WebRTC / Windows path)

> Superseded immediate ordering. Эта секция описывает прежний путь WebRTC underlay →
> Windows Home Gateway / RNS-over-WebRTC. Текущий critical path — 5N (см. Current
> engineering priority выше). Сохранена как backlog / secondary track.

**По последнему уточнению пользователя сейчас только документация и подготовка
к реализации.** Carrier-код, сборки, провайдерские сессии и device tests отложены.
[Delta и контракт в существующем дизайне](reticulum/HOME_GATEWAY_DESIGN.md#whitelisted-webrtc-carrier--extension-2026-09-25)
· [Аудит источников](legal/DEPENDENCY_LICENSE_AUDIT.md)
· [Checkpoint](releases/2026-09-25-webrtc-carrier-preparation.ru.md).

Прежняя схема Home Gateway + WebRTC underlay = ReticulumOverlay →
UnderlayPathManager → direct IPv6 / direct IPv4 / WebRtcPathProvider → Windows.
Внутри carrier — сменные WB/Telemost/VK adapters. Reticulum сохраняет overlay
identity/Link encryption/routing; WebRTC переносит непрозрачные RNS frames.
Свобода отдельного data transport сохраняется; IP-over-RNS-over-WebRTC становится
явной тестовой веткой, а не требованием переписать все существующие VPN-транспорты.

Существующие5A–5G не перенумерованы. Добавлено:

| Подэтап | Результат | Статус |
| --- | --- | --- |
| 5H UnderlayPathManager | Path API, bounded lifecycle, custom RNS Interface, isolated carrier IPC | Контракт спроектирован, кода нет |
| 5I WebRTC carrier PoC | WEBRTC-1 desktop binary round trip → WEBRTC-2 Android↔Windows | Telemost первым после полевого видеозвонка; carrier-тестов нет |
| 5J Reticulum-over-WebRTC | WEBRTC-3: announces в обе стороны и authenticated RNS Link | Не реализовано |
| 5K Home Gateway over WebRTC | WEBRTC-4 IP/TCP/UDP → WEBRTC-5 browser/DNS/FC exit/no leaks; связано с5C–5E | Следующий этап |
| 5L multi-provider WebRTC | Telemost/VK после WB; независимое отключение verified config | Запланировано |
| 5M restricted-mobile validation | Дополнение5F: обычный VPN не работает, новый путь работает на той же SIM при ограничениях | Краснодар; не проверено |

Порядок после возобновления реализации:5A reachability →5H →5I →5J; перед5K
зафиксировать blockers/results. Сейчас глобальный этап5, подготовка5A/5H, а не
завершённые5B–5G. Без реальных Android/Windows и целевой сети gates не засчитывать.

Первоначально WB выбирался по guest-join/LiveKit reference; теперь Telemost первым
по полевому видеозвонку25.09, WB резервный.
Гостевой join не доказывает создание комнаты без входа: whitelist creator требует
cookie bearer; olcrtc использует готовую room. PoC допускает manual disposable room
через session API. Финальный UX — ephemeral rendezvous через provisioning/другой
достижимый control; room не Device Identity. Нельзя предположить, что ещё не поднятый
RNS-over-WebRTC сам доставит свои начальные credentials.

Для подготовки следующей реализации зафиксированы: stdio framed IPC, mode
capabilities DC/VP8/TCP fallback/TURN с unknown, bounded queues/cancel/backoff,
проверка всех Android signaling/ICE/media sockets, independent provider flags OFF,
no secrets/logging/TLS downgrade и provider-unavailable без падения приложения.
Производительность DC/VP8 измерять отдельно: >5Mbit/s полезная цель,20+ сильный
результат, не текущие замеры. Достижимость видеосервиса в белых списках не доказана.

## Home Gateway (secondary track / backlog) — Reticulum control, selectable data transport

> Superseded immediate ordering. Home Gateway — secondary LAN/NAS/RDP/residential-egress
> track, не немедленный следующий шаг. Текущий critical path — 5N (см. Current
> engineering priority выше).

**Уточнение пользователя: главная задача — установить защищённое соединение
телефон ↔ домашний компьютер в мобильной сети с белыми списками.** Reticulum
используется для discovery, аутентификации и согласования/восстановления пути;
гнать пользовательские IP-пакеты через RNS необязательно. Это заменяет прежнее
требование обязательного IP-over-Reticulum, не отменяя Device Identity/FAMILY,
fail-closed и минимальную приёмку реальных IP-пакетов Android↔Windows.

[Дизайн](reticulum/HOME_GATEWAY_DESIGN.md) · [Белые списки](allowlist-connectivity.ru.md)
· [Статус](STATUS.md) · [Отчёт об изменении](releases/2026-09-25-home-gateway-strategy.ru.md).

**Текущее положение: глобальный этап5, начало5A — дизайн и проверка достижимости.**
Документация/обследование есть; Home Gateway не реализован, RNS-1–RNS-5 не пройдены.
Старая нумерация5.1–5.6 относится к control/fleet; новая5A–5G — к Home Gateway.
Это две связанные части этапа5, а не заявление о завершении прежних задач.

| Подэтап | Результат и критерий | Статус |
| --- | --- | --- |
| 5A Control/discovery и достижимость входа | Existing Device Identity/FAMILY, RNS adapter и signed transport negotiation; измерить достижимость control/bootstrap и data ingress в целевой мобильной сети | Дизайн; полевые проверки впереди |
| 5B Android ↔ Windows encrypted session | RNS-1: согласование через RNS, взаимная аутентификация выбранного data channel, обе Device Identity, reconnect; сначала через достижимый relay | Не реализовано |
| 5C IP tunnel over selected transport | RNS-2: реальные Android TUN → выбранный защищённый transport → Windows packets и reply; IPv4 ping/deterministic test | Не реализовано |
| 5D Windows Personal Gateway | RNS-3: app-managed direct diagnostic egress; HTTP/HTTPS, DNS, UDP/TCP; без ручного ICS | Не реализовано |
| 5E existing VPN upstream integration | RNS-4: existing Windows engine, IP телефона = VPN exit; нет fallback на ISP | Не реализовано |
| 5F real mobile-network validation | RNS-5 Краснодар: работа при активных белых списках, establishment/throughput/RTT/loss, 30–60 min, смена сетей/IP | Не проверено |
| 5G direct paths / zero-config optimisation | Direct IPv6/IPv4, NAT traversal, multiple paths; relay остаётся резервным | После измерений |

Ближайший проверяемый результат: определить достижимый разрешённый ingress на
тестовой SIM при активных ограничениях, отдельно проверить control и data path,
затем установить authenticated телефон↔ПК session через него. Проверка через Wi-Fi
или мобильную сеть без активных ограничений не доказывает решение основной задачи.
Reticulum identity и обмен endpoint не создают доступ к заблокированному адресу.
Если control/bootstrap недоступен, требуется доступный carrier/bootstrap; если
control работает, а data path заблокирован, session не считать установленной.

Первый PoC: оба устройства подключаются исходящими соединениями к доступному
relay, который переносит end-to-end encrypted data и не является Internet exit.
Статический IP/DDNS/проброс портов на домашнем ПК не требуются. Прямой путь —
следующая оптимизация, не prerequisite. AWG/WG — кандидаты при доступном UDP;
существующий TCP/XHTTP/TLS и другие варианты оцениваются по reachability, наличию
authenticated reverse/relay path и скорости. Наличие runtime не означает готовый
reverse tunnel. Конкретный data transport ещё не выбран, новые зависимости не добавлены.

Согласование подписывает обе identity, transport public keys, роли, session nonce,
параметры/срок пути и FAMILY grant. Data handshake отдельно доказывает владение
ключами; контрольный успех не заменяет handshake. Потеря RNS не обязана рвать
здоровый data tunnel до истечения grant; для восстановления нужны доступный control
или заранее разрешённые актуальные пути. При expiry — fail closed.

Обязательные gates: DNS/IPv6 fail-closed, Android socket protection каждого
underlay/reconnect, anti-replay/downgrade, bounded buffers, route ownership,
Windows upstream failure, clean shutdown и recovery. Existing tests не ослаблять.
Feature OFF по умолчанию, default transports неизменны; no public proxy/cleartext/
shared credentials. RNS-2 сохраняет имя для continuity, но больше не требует IP-over-RNS.

Делить commits по legal/design/core/control/platform/data/tests/docs; RNS-3/RNS-4
отдельно. Лицензионные ограничения и audit сохраняются. Предыдущие5.2/5.3а и прочий
migration/test debt не возобновлять автоматически. Из5.3в переиспользовать только
нужное для текущей проверки ingress; остальные критерии не считать закрытыми.
Старые датированные «ближайшие шаги» ниже не перекрывают этот приоритет.

24.09: [Windows0.2.14 опубликован](releases/2026-09-24-windows0214-installer.ru.md), source6eed30c.
GitHub/HTTPS installer и страница обновлены; отдельный подписанный Windows-каталог
schema2/sequence10. CET отключён только для процессов приложения для совместимости
со старыми патчами Win10; системные настройки защиты не меняются. Повторная установка
не запускает старый EXE, данные сохраняются. Native CI: Server2025/2022, recovery/upgrade,
UI/user/AWG/TCP passed. Физический проблемный Win10 ПК ещё требует приёмки.
Windows10 1809+ /11 x64 — целевые версии, не гарантия всех сборок Windows.


24.09: [разбор сбоя первой установки Windows0.2.13 на Windows10](releases/2026-09-24-windows10-install-audit.ru.md).
На ПК Windows10 Pro22H2/19045.2364 служба не создана; причина ещё не установлена.
Хеш локального release EXE совпал, Windows CI success повторно подтверждён;
отдельного Win10 job нет. Полученные setup/host журналы: admin/x64, повтор
останавливается на remove-service; trace обрывается после загрузки coreclr.dll.
Crash TXT подтвердил CLR0x80131506 на i5-11300H; основная гипотеза — CET
на старых патчах Win10 (аналог dotnet/runtime108589). Следом обновление Win10,
перезагрузка и повторная установка; CET на этом ПК ещё не доказан.
Версии/публикация не менялись.

24.09: [XHTTP/TLS реализован в исходниках и проверен локально](releases/2026-09-24-xhttp-local.ru.md).
Этап5.3в теперь в работе по прямому запросу пользователя: Python/Linux, Android
Java/Go и Windows activation v2; двусторонний loopback, TLS/credential refusals.
Публичный режим белых списков пока не готов: DNS/CDN ingress, Friends/capability,
fleet и реальные сети открыты. Домен предоставлен, DNS не менялся. Краснодар —
первый регион приёмки; номер абонента не сохраняется.5.3а остаётся открытым.

24.09: в план добавлен **5.3в — реализация режима для сетей с белыми списками**
по ориентиру Shuka: обследование→ingress/транспорт→клиенты→восстановление→операторская
приёмка и Django7.1. [Требования](allowlist-connectivity.ru.md). Пока это план;
текущий5.3а и отложенная проверка Android на телефоне сохраняются.

24.09: [подготовлены проверки admission Android-службы](releases/2026-09-24-android-service-admission.ru.md).
Три instrumented сценария для пустого debug pilot: неверный gateway, выбор без
managed enrollment с повтором, отмена callback разрешения VPN. Сборка прошла;
первый запуск на телефоне завершился тайм-аутом, runtime acceptance не засчитана.
По просьбе пользователя дальнейшая работа пока без телефона. Следующий шаг5.3а:
повторить эти проверки, затем реальный enrollment/permission/restart/rollback/трафик.

Обновлён 24.09.2026. Факты и версии: [STATUS](STATUS.md).
История сохранена в [прежнем журнале](PLAN.before-beta49-2026-09-23.md).

## Текущий приоритет (исторический журнал 24.09, superseded ordering)

> Исторический журнал24.09; immediate ordering superseded. Текущий critical path — 5N
> (см. Current engineering priority выше). Содержимое ниже сохранено как backlog/история.

24.09: [уточнение AWG на Wi-Fi](releases/2026-09-24-awg-wifi-followup.ru.md):
пользователь пробовал AWG до исправления выдачи конфигурации; повтор ещё ожидается.
NL AWG работает и имеет свежие handshake. Отдельная проблема UDP не подтверждена;
код и серверные настройки не менялись, план5.3а сохраняется.

24.09: [актуальность3 локальных SQLite подтверждена](releases/2026-09-24-local-sqlite-review.ru.md).
Все3 совпали логически с backup; свежие encrypted snapshots сохранены и извлечены.
14 targeted tests passed. Классификация: локальное pilot state, сохранять;
наблюдение потребителей неполное. Следующая разработка5.3а — Android device acceptance.
Внешняя копия, full DR и production signing acceptance остаются открытыми.

24.09: [Android signing consumer из KeePassXC реализован](releases/2026-09-24-android-vault-signing.ru.md).
65 targeted tests passed, включая реальный synthetic KDBX→apksigner→verify.
Настоящий keystore проверен по сертификату beta50 без подписи; новых релизов нет.
Следом свежесть3 локальных SQLite/active-legacy state; внешний носитель и production
signing acceptance остаются открытыми. Рабочие оригиналы сохранены.

24.09: [закрытый реестр локальных потребителей сохранён в KeePassXC](releases/2026-09-24-local-secret-consumer-audit.ru.md).
204 файла:200 совпадают с прежними backups,3 SQLite требуют проверки актуальности,
ещё1 административный credential добавлен и проверен.7 modes сужены до0600.
Следом Android signing consumer из vault; внешний носитель и full clean-machine DR
остаются открытыми. Рабочие оригиналы сохранены, production не менялся.

24.09: [исправлен нулевой запас challenge на расхождение часов](releases/2026-09-24-friends-challenge-clock.ru.md).
RU API выдаёт challenge100с вместо120с; клиентская граница120с сохранена.
45 tests passed, HTTPS200/TTL100, службы active. APK friends beta50 проверен по
хешу/package; пользователь подтвердил: новый клиент подключился.
Следом возврат к аудиту оставшихся plaintext секретов и их потребителей.

24.09: [изолированное восстановление из KeePassXC прошло](releases/2026-09-24-vault-restore-rehearsal.ru.md).
89 файлов/7 SQLite, Access/referral identity и реальный mailbox startup/shutdown
проверены в контейнере без сети;12 tests passed. Live state и vault не изменялись.
Следом аудит plaintext/потребителей; полный clean-machine DR, VPN/HTTPS acceptance
и внешний носитель остаются открытыми.

24.09: [синхронизация участников чата восстановлена](releases/2026-09-24-chat-clock-recovery.ru.md).
Причина — часы NL отставали примерно24с; добавлен рабочий NTS-источник chrony.
RU/NL synchronized, timer успешен, membership актуален и совпадает с RU;21 tests passed.
Далее clean-machine restore/внешний носитель/аудит plaintext; alerts времени ещё открыты.

24.09: [TLS/SSH/mailbox: ещё42 файла в KeePassXC](releases/2026-09-24-infrastructure-secret-backup.ru.md).
Binary export/SHA256 и1 SQLite restore прошли;10 targeted tests passed.
Обнаружены failed RU chat-sync и просроченный NL membership lease: диагностика и
исправление — следующий шаг. Затем clean-machine restore/внешний носитель;
рабочие plaintext originals пока сохранены. Версии клиентов не менялись.

24.09: [47 серверных файлов/6 SQLite сохранены в KeePassXC](releases/2026-09-24-server-secret-backup.ru.md).
Извлечение/hashes/in-memory SQLite restore прошли, VPN службы active.7 targeted tests passed.
Следом — TLS/system SSH/messenger-node, clean-machine restore и внешний носитель.
Это не единый образ всех серверов; работающие plaintext originals пока сохранены.


24.09: [TCP-службы NL и RU перезапущены по разрешению пользователя](releases/2026-09-24-tcp-private-umask-restart.ru.md).
Runtime Umask0077 подтверждён на обоих узлах; службы active/NRestarts0, TCP-порты
доступны локально и с ноутбука. AWG PID сохранены. Отложенный TCP restart закрыт;
полный клиентский VPN-трафик этим запуском не проверен. Следом — server backup/recovery.


24.09: [аудит серверных прав и5 vault issuers](releases/2026-09-24-secret-consumers.ru.md).
40 targeted tests passed; основные секреты RU/NL имеют ожидаемые600/640 и закрытые
каталоги. Drop-in UMask0077 установлен без restart; AWG runtime0077, TCP runtime0022
до планового restart. Далее — server backup/реестр потребителей; plaintext оригиналы пока сохранены.


24.09: [подпись из KeePassXC](releases/2026-09-24-vault-signing.ru.md) подключена к3 issuers.
896 Python tests passed; рабочий ключ прочитан из vault и проверен по public anchor
без подписи/экспорта. Далее — проверка остальных потребителей/серверных credentials,
внешний backup и устранение ненужных plaintext копий. Старые файлы пока сохранены.


24.09: [203 локальных файла скопированы в KeePassXC](releases/2026-09-24-vault-import.ru.md),
2 encrypted attachments проверены бинарным извлечением/SHA256. Исходники сохранены,
внешней копии ещё нет. Далее — [перевод потребителей секретов](secrets-and-recovery.ru.md),
серверные credentials и устранение лишних plaintext копий после проверки восстановления.


24.09: [локальное KeePassXC-хранилище создано](releases/2026-09-24-local-vault.ru.md),
проверено открытие повторно введённым паролем.5 разделов пока пустые; рабочие секреты
не переносились. Внешняя копия отложена пользователем. KDBX/keyx блокируются в Git.


24.09: добавлен [guard публикуемых исходников](releases/2026-09-24-public-source-guard.ru.md)
и CI-проверка индекса.2 новых теста passed. Хранилище/офлайн-копия пока не созданы:
носитель не подключён. Предыдущие Linux control/Windows conformance/phase0/messenger/
desktop visual/user access CI прошли; Android/Windows builds и native AWG/TCP ещё выполнялись.


24.09: [source checkpoint и правила секретов](releases/2026-09-24-source-checkpoint.ru.md)
опубликованы в GitHub main: `86eb24e`.890 Python/124 Java tests и C# runner passed.
GitHub Actions для этого коммита поставлен в очередь; результат ещё не подтверждён.
Публикация Git не означает rollout. Исторические пометки «локально» ниже описывают
состояние на момент соответствующей проверки.


24.09: принята [схема хранения секретов](secrets-and-recovery.ru.md). Выбраны компьютер
и отдельный офлайн-носитель. Настройка шифрования и проверка восстановления ещё открыты; секреты не перемещались.

На подключённом Redmi Note 9 Pro выполнены [4 instrumented tests](releases/2026-09-24-android-selection-device.ru.md)
в отдельном debug pilot: encrypted journal selection/reopen/rollback, protocol/JSON и
Python/RNS. Следующий шаг — service/UI acceptance с тестовым enrollment и настоящим
VPN gateway: permission/cancel, stop во время health, process restart и трафик.
Пустой pilot пока не имеет enrollment/managed configuration; TEST ONLY corpus не
предоставляет рабочие серверы. Friends identity integration остаётся отдельной задачей.
Изменения и карты пока локальные.

Android selectGateway service/UI wiring готов в исходниках;124 JVM tests и debug Java
compile passed. [Отчёт](releases/2026-09-24-android-selection-service.ru.md).
Следом — instrumented/device acceptance (permission/cancel/restart/rollback/UI selection),
оставшаяся native/Friends identity интеграция. buildPython для локальной APK исправлен выше.
Рабочая capability3.1 пока выключена. Обе карты кода актуализированы.

По просьбе пользователя24.09 подготовлена [карта всего проекта по модулям](code-map/README.ru.md)
для подключения новых разработчиков. При изменении ответственности/границ модуля
обновлять соответствующую страницу вместе с кодом (правило добавлено в CONTRIBUTING).
Порядок разработки5.3а→оставшиеся5.2/6 сохраняется.

Следующий шаг5.3а: подключить selectGateway к единому Android service worker/UI,
согласовать selection из journal и провести device acceptance. Локальная операция
с schema2/SWITCHING и recovery готова:120 Java tests passed.
[Контракт и границы](releases/2026-09-24-android-gateway-transaction.ru.md).
Это не завершение native/Friends интеграции и не закрытие5.2/6.

24.09: ControlApplication materialize учитывает явно выбранный gateway;111 Java tests
passed. [Отчёт](releases/2026-09-24-android-gateway-selection.ru.md) и
[карта кода](managed-control-code-map.ru.md). Переход между gateway одного транспорта
в уже committed envelope пока требует отдельной операции: resume не переписывает
слоты, replay не вызывает apply. Это входит в remaining5.3а/Android application gates.

Android identity/journal opt-in для managed AWG3.1 готов локально;110 Java tests passed
с apply/reopen/rollback на имитации службы. [Отчёт](releases/2026-09-24-awg31-android-journal.ru.md).
Далее native service/device integration и remaining Linux/Windows application gates.
Документация24.09 пока не отправлена на GitHub: remote main b5f4864 содержит статус23.09.
Отдельный docs checkpoint требует согласования с актуальным remote tree без потери
существующей незакоммиченной работы; force push/reset не применять.

Последний checkpoint5.3а: Java/C# verifier и parser согласованы с Python на общем
AWG3.1 corpus, defaults сохраняют отказ. [Результаты](releases/2026-09-24-managed-awg31-native-verifiers.ru.md).
Следом — capability через identity/journal/application boundary и native apply,
health/rollback/restart на устройствах; Windows C# тесты на Linux не закрывают OS gates.
Аренда сервера для текущих проверок не требуется; независимый ingress понадобится
на сетевом этапе5.2/6 согласно проекту recovery.

24.09: начат5.3а — schema/issuer/Python verifier AWG3.1 и отдельный shared corpus
готовы локально; следующий шаг — native conformance/capability/apply на трёх платформах.
[Checkpoint и тесты](releases/2026-09-24-managed-awg31.ru.md).
Пользователь поручил усилить защиту всеми доступными способами:
[матрица мер/приёмки](blocking-resilience.ru.md) обязательна для5/6. Independent ingress,
сегментация, внешнее восстановление и дополнительные транспорты ещё не реализованы.

По просьбе пользователя24.09: начать этап5 и включить расширяемый парк серверов,
распределение нагрузки и управление IP. Предыдущая сверка документации сохранена ниже.
**После каждого изменения версии обновлять документацию в той же работе.** Отдельно
указывать локальную сборку, установленную, публичную и версию на странице приглашения.
[Процедура](releases.md#documentation-with-every-version).

1. Выполнено: RU/EN инструкции, загрузки и статус сверены, история сохранена;
   274 Markdown-файла/1586 ссылок проверены. Документация опубликована в GitHub
   коммитом b8d51bf;9 основных файлов скачаны и совпали побайтно.
2. Выполнено: актуальный source checkpoint Android49 / Linux/Windows0.2.10 опубликован
   в main, версии согласованы. Код8627d55: Client builds35899784973, Linux control,
   phase0 и TCP — success; native Windows AWG/TCP и ordinary-user acceptance также passed.
   На момент этого checkpoint приёмка этапа4 ещё не была завершена; итог ниже.
3. Выполнено: интерактивная страница, Android beta50 и desktop0.2.10 manual preview
   опубликованы согласованно. URI/UI проверки и SHA256 публичных файлов подтверждены.
   Переключатели всех клиентов: оранжевые OFF, бирюзовые ON. Документация обновлена.
4. Выполнено: 23.09.2026 пользователь принял перечисленные проверки словами
   «считай подтвердили». Этап4 закрыт в объёме пилотного выпуска: Windows0.2.13
   (интерфейс, приглашение, подключение, проверка обновлений), базовый сценарий Linux,
   ранее подтверждённые сценарии Android. Это пользовательская приёмка, не новый тестовый прогон.
5. Начат этап5: независимый служебный канал и, по уточнению пользователя24.09,
   расширяемый парк серверов, распределение новых подключений и IP-адреса. Аудит5.1
   завершён; реестр/планировщик и durable leases/IPAM5.2 реализованы локально.
   Резервирование, конкуренция, crash/recovery и Friends regression:112 passed.
   Добавлены локальный шлюзовой fencing-прототип и worker: общий прогон139 passed.
   Добавлены WG/AWG backend и SSH adapter в исходниках:163 passed.
   Изолированная native/SSH приёмка пройдена:12 сценариев на WG/AWG2/AWG3.1.
   Добавлены локальные proof авторизация и durable scheduler:201 passed.
   Добавлена локальная offline signed выдача WG/AWG2:269 passed, fleet schema3.
   Следом — verified ACK и перенос offline→online, привязка действующего доступа/API.
   HTTPS Friends сам по себе независимость не обеспечивает.
6. Длительные сетевые испытания, российская сеть, смена сети и точная задержка Doze
   остаются отдельными задачами устойчивости; они не переоткрывают пилотный этап4.

## Глобальные этапы

| Этап | Состояние / следующий результат |
| --- | --- |
| 1. Продукт, WG, идентичности | Работает в пилоте; сохранить выдачу/отзыв и ключи |
| 2. AWG и восстановление | AWG3.1 реализован; длительная и российская приёмка открыты |
| 3. TCP REALITY | Реализован; общая сетевая приёмка открыта |
| 4. Три клиента и выпуск | Закрыт как пилотный выпуск по приёмке пользователя 23.09.2026 |
| 5. Служебный канал и парк серверов | В работе:5.1 завершён;5.2 backend/SSH/scheduler/offline publish подготовлены;5.3а managed AWG3.1 требует native/Friends integration и device acceptance. Сейчас —5.3а, Android service/UI acceptance |
| 6. Недоступный gateway | Нужна сквозная смена endpoint через независимый канал |
| 5N-MC. Multi-carrier restricted path | **После Краснодар FIELD-1:** Carrier API v1 → WB как второй provider → VK → bounded automatic failover; DION/Bitrix только по field evidence |
| 7. Сервис и коммерческая версия | Согласована7.1 — единая Django-админка; оплата/подписки не реализованы |

**Текущая точка (superseded immediate ordering / backlog):** этап5.3в, локальная реализация XHTTP/TLS по новому прямому запросу;
5.3а Android service/UI acceptance остаётся открытым, телефон отложен пользователем.
Обеспечивающие задачи секретов/recovery для5/6 продолжаются отдельно.
Хранилище, пять vault issuers, server backups и контейнерное восстановление готовы;
реестр потребителей начат. Android vault entry point готов; не закрыты production signing acceptance, внешний носитель
и восстановление на чистом хосте. Безопасность — не отдельный завершённый этап.

**Очередь:** выбранные3 SQLite сверены, fresh snapshots проверены. Ближайшая
разработка возвращается к5.3а: Android service/UI acceptance с реальным
enrollment, разрешением VPN, restart/rollback и трафиком. Далее remaining5.2/5.4–5.6,
сквозной этап6 и только затем Django7.1. Проверка всех потребителей перед удалением
originals, внешний носитель и full DR остаются отдельными обязательными пунктами. Исследование третьего транспорта5.3б остаётся
согласованным, но отдельный production transport ещё не выбран. Новый сервер для
текущей локальной работы не нужен; независимый ingress нужен для сетевой приёмки6.

<a id="multi-carrier-roadmap"></a>
## После Краснодар FIELD-1: multi-carrier restricted path

**Порядок зафиксирован 05.10.2026. Не начинать реализацию до завершения и разбора
одного авторизованного Краснодар FIELD-1 на текущем Telemost path.** FIELD-1 должен
сохранить точную версию клиента/gateway, оператор/тип сети/время, readiness,
session diagnostics и результат полезного HTTPS/DNS трафика. Не приписывать сбой
DPI/оператору/provider без доказательств. Успешный Telemost FIELD-1 не отменяет
multi-carrier roadmap, но определяет его срочность и критерии failover.

Цель следующего блока — не добавить пользователю выбор ещё нескольких протоколов,
а превратить restricted transport в заменяемую платформу. Обычный пользователь
видит только CONNECTING / CONNECTED / RESTORING; Telemost/WB/VK и конкретный media
transport остаются в diagnostics. Device Identity, Family admission, Family TLS,
ReliableStream, Mux, DNS/TCP policy, whole-device/TUN и privacy boundaries должны
оставаться общими и не дублироваться под каждого provider.

### 5N-MC0 — FIELD-1 decision gate

1. DONE только после фактического Краснодар FIELD-1: зафиксировать PASS/FAIL и
   первую доказанную причину/стадию отказа текущего Telemost пути.
2. Сравнить, нужен ли второй carrier прежде всего для coverage, reliability,
   capacity или provider-independence. Не подменять измерение количеством transports.
3. Сохранить текущий Telemost implementation как regression baseline; новые
   abstractions сначала обязаны прогнать его старые live/unit acceptance без
   ослабления timeout/replay/admission/privacy контрактов.
4. До закрытия MC0 не менять FIELD-1 APK/gateway ради WB/VK и не смешивать
   multi-carrier refactor с расследованием текущего Telemost DATA/recovery дефекта.

### 5N-MC1 — Carrier API v1 / разделение provider и media transport

Сделать provider-independent boundary вместо прямых вызовов telemost.New из
bootstrap/whole-device кода.

Целевая модель:

    WholeDevice / Connectivity Orchestrator
                  |
            Family TLS 1.3
                  |
            ReliableStream
                  |
           CarrierTransport
            /            \
          VP8         DataChannel
            \            /
             ProviderEngine
           /      |       \
     Telemost   WB       VK

Требования:

- общий bounded Carrier/session contract: connect, send, receive, close, stats,
  cancellation и terminal failure; без provider URL/token/cookie в верхних слоях;
- отдельный ProviderEngine/factory registry по стабильному transport/provider ID;
- разделить media encapsulation (сначала VP8; DataChannel только где доказан) и
  provider signaling/SFU/session lifecycle;
- provider-neutral descriptor/bootstrap schema с versioning и строгой allowlist
  известных provider/transport combinations; старый Telemost snapshot должен
  мигрировать явно, а не приниматься эвристикой;
- RoomProvider расширить до provider-neutral setup lifecycle без передачи OAuth,
  cookies или CAPTCHA material на Android;
- Telemost первым перевести на новый API **без изменения wire semantics**;
  прежние Family TLS/ReliableStream/Mux/whole-device gates должны пройти повторно;
- dependency/license/security audit обязателен до копирования или адаптации
  upstream кода whitelist-bypass/olcRTC; не импортировать чужой код только
  потому, что live feasibility уже показана upstream.

**MC1 PASS:** один и тот же существующий Telemost restricted path проходит старый
live acceptance через новый interface; верхний Family/TUN stack не импортирует
Telemost package напрямую, кроме provider registration/composition root.

### 5N-MC2 — WB Stream как второй независимый carrier

WB выбирается первым вторым provider-кандидатом после MC1, потому что upstream
показывает headless LiveKit/VP8 path и guest-oriented session flow; это только
feasibility evidence, не наша acceptance.

Порядок:

1. Реализовать isolated ProviderEngine для WB и минимальный server-side
   session/bootstrap lifecycle; Android не должен получать provider secrets.
2. Первый gate — Linux↔real WB service/SFU↔Linux exact-byte VP8 carrier:
   1B, 1KiB, 64KiB, batch traffic, bounded teardown/cancel и controlled loss.
3. Второй gate — запустить **неизменённые** Family TLS + ReliableStream поверх WB;
   replay/admission/identity/privacy negative cases обязательны.
4. Третий gate — неизменённый Mux/DNS/TCP: несколько HTTPS streams, Family DNS,
   destination TLS verification, bounded buffers/resources.
5. Четвёртый gate — physical Android whole-device/TUN через WB на обычной сети;
   restricted/allowlist mobile acceptance — отдельно и только при наличии
   наблюдаемого подходящего режима сети.
6. Добавить WB stats/error categories в существующий privacy-safe diagnostics,
   не логировать room/token/guest credentials/media payload.

**MC2 PASS:** Telemost и WB независимо несут один Family session stack и одинаковый
Mux/DNS/TCP contract; отказ одного provider не требует новой APK или смены
пользовательской конфигурации.

### 5N-MC3 — VK Calls как третий carrier

VK добавлять после подтверждения MC2, чтобы третий provider проверял масштабируемость
абстракции, а не становился ещё одним special case.

- использовать официальный/допустимый auth/session path где возможно;
- **никакого AI/автоматического обхода CAPTCHA**: CAPTCHA считается auth lifecycle
  gate; допустим manual/operator bootstrap и bounded сохранённая сессия;
- provider cookies/tokens хранятся server-side и не входят в Family provisioning,
  Android APK, diagnostics или room descriptor;
- сначала Linux real-service VP8 exact-byte gate, затем Family TLS/ReliableStream,
  затем Mux/DNS/TCP и только после этого Android whole-device;
- DataChannel можно исследовать отдельно, но он не заменяет VP8 acceptance и не
  должен усложнять общий API до появления измеримого выигрыша;
- account/session expiry, captcha-required, rate-limit/provider rejection должны
  иметь отдельные bounded reason codes и не маскироваться как generic network loss.

**MC3 PASS:** Telemost/WB/VK работают через один Carrier API; добавление VK не
требует правок Family TLS, Mux, DNS/TCP или Android packet engine.

### 5N-MC4 — автоматический multi-carrier policy и failover

После минимум двух наших физически принятых restricted carriers подключить их к
Connectivity Orchestrator.

- policy выбирает capability, а не бренд: normal AWG/TCP остаются предпочтительными
  на обычной сети; restricted carriers — recovery/fallback;
- health score учитывает setup success, time-to-ready, recent terminal category,
  bounded cooldown и provider/session availability; содержимое пользовательского
  трафика и destination history не собирать;
- один terminal provider failure может вызвать ограниченный переход на другой
  provider только после cleanup/security gates; никаких бесконечных циклов;
- auth/policy/revocation failure не должен обходиться переключением provider;
- сохранять VPN guard/TUN ownership во время восстановления согласно действующему
  fail-closed contract; не допускать direct traffic leak между попытками;
- deterministic tests: provider A unavailable → B succeeds; A+B unavailable →
  bounded user-visible failure; auth/revoked → no fallback bypass; cancellation →
  все owned sessions закрыты;
- physical acceptance: Telemost→WB и WB→Telemost recovery, затем VK как дополнительный
  candidate; измерять restoration time и ручные действия, а не только throughput.

**MC4 PASS:** пользователь нажимает CONNECT один раз; смена restricted provider не
требует выбора комнаты/provider/transport и происходит bounded/fail-closed.

### 5N-MC5 — расширение парка providers только по данным

DION, Bitrix, Jitsi и другие upstream-доказанные сервисы остаются кандидатами, а
не обязательным чек-листом. Новый provider добавлять только если он даёт измеримый
выигрыш хотя бы по одному критерию: coverage другого оператора/региона, независимость
от одного vendor, capacity, setup reliability или recovery time.

Для каждого нового provider минимальный шаблон одинаков:
real service carrier → Family TLS → ReliableStream → Mux/DNS/TCP → Android TUN →
target field acceptance. Нельзя объявлять provider готовым только по upstream
README, локальному WebRTC/DataChannel или созданию комнаты.

### Выход multi-carrier блока в продукт

До targeted beta для обычных пользователей требуется минимум:

- два независимых restricted provider прошли наши physical end-to-end gates;
- Orchestrator умеет bounded automatic fallback и fail-closed cancellation/revocation;
- provider credentials/session renewal обслуживаются server-side;
- Telemost/WB/VK названия скрыты из основного UX и остаются в advanced diagnostics;
- privacy scan, resource bounds, dependency/license audit и rollback выполнены;
- immutable Android build проходит owner preservation/security gates и один
  контролируемый restricted field trial после exact-source CI/artifact verification.

Оценка не является deadline: после FIELD-1 сначала MC1, затем WB MC2; VK MC3 —
следом. DION/Bitrix не делать параллельно без evidence. При чистом abstraction
target engineering budget для Telemost+WB+VK+orchestrator — ориентировочно
7–15 рабочих дней, но каждый live gate может остановить оценку и потребовать
перепланирования.

<a id="release-gates-three-platforms"></a>
## Условия выпуска трёх платформ

- Android: совпадение версии/ABI/сертификата/хеша, unit/lint/build, native UI и VPN,
  обновление без потери идентичности, приглашение по ссылке и фон на доступных устройствах.
- Linux: извлечённый пакет, зависимости/helpers, обычный пользователь, GTK rendering
  и взаимодействия, установка/обновление, приглашение и реальные транспорты.
- Windows: native CI UI/broker/installer/AWG/TCP, обычный пользователь, URI handler;
  физическую проверку отмечать отдельно, не заменять Linux cross-build.
- Публиковать неизменяемые файлы; каталог подписывать offline только после проверки
  скачанных platform CI artifacts. Не заменять прежний APK другой сборкой.
- Согласовать загрузки/страницу/документацию; проверить внешнее скачивание и предусмотреть
  откат метаданных. Не удалять данные устройств при обновлении или откате.

## Отложенные задачи

Долгий Doze/OEM/boot/Android13+, desktop messenger, iOS/macOS, полный gateway failover,
лицензирование, private security reporting, Windows publisher signing и коммерческий
запуск не закрываются успешной сборкой. Новые VPS не заказаны.

[Текущая приёмка, артефакты и откат](releases/2026-09-23-switch-colors-beta50.ru.md).
Этап4 закрыт по решению пользователя; это не утверждение о коммерческой готовности.
Новые функции и desktop messenger ведутся отдельно от завершённого пилотного выпуска.

Windows0.2.13 и отдельный подписанный канал опубликованы; пользователь принял проверки
переходной установки, интерфейса, приглашения, подключения и кнопки обновления.
Schema2/sequence9 отделён от прежнего общего schema1/sequence8. Подробные новые замеры
на ПК не предоставлялись. [Выпуск и запись приёмки](releases/2026-09-23-windows0213-updater.ru.md).

## Разбиение этапа5

[Подэтапы5.1–5.6, сроки и критерии завершения](releases/2026-09-23-stage5-plan.ru.md).
5.1 завершён24.09. [Аудит и результаты тестов](releases/2026-09-24-stage5-audit.ru.md).
[Дополненный контракт](stage5-fleet-contract.ru.md): несколько узлов одной страны,
реестр endpoints, IPAM, capacity admission, drain и добавление сервера без новой сборки.
В5.2 готовы локальный реестр/валидатор и постоянное атомарное резервирование
IP/мест. [Отчёт:112 tests passed](releases/2026-09-24-fleet-leases.ru.md) ·
[Схема хранения и recovery](fleet-leases.ru.md). Следующий конечный результат —
единая авторизация и remote adapter с fencing, затем идемпотентный
provision → ready → signed publish. До включения обязателен импорт старых адресов;
локальная generation не подменяет защиту от задержанных команд на gateway.
Шлюзовой журнал и worker теперь реализованы как локальный прототип:139 checks passed.
[Контракт fencing](fleet-gateway-fencing.ru.md) ·
[Отчёт и согласование Django7.1](releases/2026-09-24-fleet-fencing-admin-plan.ru.md).
Добавлены WG/AWG peer backend, bounded subprocess и SSH forced-command adapter:
163 tests passed. [Отчёт](releases/2026-09-24-fleet-wg-ssh.ru.md) ·
[Контракт/установка](fleet-wg-ssh.ru.md). Изолированная native WG/AWG
и SSH приёмка пройдена:12 сценариев,163 regression tests.
[Native-отчёт](releases/2026-09-24-fleet-native.ru.md) ·
[Повторяемый стенд](../pilot/fleet-native/README.ru.md).
Добавлены FleetAccess и FleetScheduler:201 tests passed; схема2 с явной миграцией.
[Контракт](fleet-access-scheduler.ru.md) · [Отчёт](releases/2026-09-24-fleet-services.ru.md).
Добавлен локальный offline publish после ready, WG/AWG2/schema2:269 passed.
[Контракт](fleet-publication.ru.md) · [Отчёт](releases/2026-09-24-fleet-publication.ru.md).
Далее verified ACK/previous hash и перенос offline→online с повторной авторизацией;
интеграция с рабочими Friends правами/API ещё впереди. По решению пользователя
приоритет изменён: ближайший шаг5.3а — managed AWG3.1, затем продолжение5.2 relay.
Код ещё не установлен на рабочие шлюзы; автономный TTL и TCP backend не реализованы.
5.3а — AWG3.1/dynamic IDs теперь выполняется первым;5.4/5.5 — Android/Linux/Windows;
5.6 — live failure gates. WG/AWG2 остаются для совместимости/регрессии без отдельного развития.
С расширением fleet предварительно14–22 рабочих дня; уточнить после leases/reconciliation.
Полный gateway failover остаётся этапом6; покупка VPS не запланирована.

## Снимок нагрузки24.09.2026

Read-only аудит: Friends18 устройств,14 не отозваны;5 устройств передавали
трафик через NL в20-секундном замере. CPU RU≈19%, NL6%; на RU iowait5–10%.
Число людей и суточные пики не установлены; текущий этап и версии не менялись.
[Метрики, границы измерения и оставшиеся проверки](releases/2026-09-24-server-usage.ru.md).

<a id="django-admin"></a>
## 7.1 Единая Django-админка: серверы, доступ и платежи

Согласовано пользователем24.09.2026. Одна панель для Family Connect:

- Серверы: карточка ID/страна/provider/IP, порты/транспорты, VPN-пул и capacity;
  provisioning → проверки → active → draining → disabled.
- Устройства и доступ: public bindings, leases, отзыв/срок доступа; без смены ключей.
- Подписки и платежи: тарифы, платёжные события и сроки доступа; повторные webhook
  не продлевают доступ повторно. Платёж меняет entitlement, не вызывает SSH напрямую.
- Операции: durable очередь, прогресс/ошибки/повторы, журнал действий и роли операторов.

Добавление сервера: карточка → проверка IP/пула → подготовка служб/firewall/monitoring
→ тестовый peer и проверка трафика → явное включение новых назначений. Удаление
карточки не освобождает IP: сначала draining, подтверждённая очистка, затем disabled.
Секреты подключения хранятся отдельно; private keys не попадают в обычные формы/логи.

Зависимость от5.2: админка вызывает общие сервисные операции и фоновые workers.
HTTP-запрос Django не держит SSH/настройку узла и не изменяет SQLite-таблицы в обход
инвариантов. Повторное нажатие и restart worker должны быть идемпотентны.
Разделение ролей платежей/инфраструктуры и история действий входят в приёмку7.1.

Порядок работ сохраняется:5.2 backend/fencing → оставшиеся5.3–5.6 → этап6 →7.1 UI.
Проектирование контрактов7.1 ведётся сейчас; сама Django-панель ещё не реализована.
Перенос authoritative fleet/access store в Django/PostgreSQL потребует явной миграции;
вторую независимо изменяемую копию leases или access создавать нельзя.
Критерий7.1: оператор через панель добавляет тестовый узел и выводит его в draining,
видит результат фоновых операций и платежи/доступ, а повторы и ошибки не теряют
leases, не дублируют оплату и не раскрывают секреты. Выбор платёжного провайдера
и конкретного хранилища секретов остаётся отдельным решением перед реализацией.

## Уточнение приоритетов24.09: Россия и третий транспорт

Пользователь согласовал перенос managed AWG3.1 в ближайшую работу.
Текущая позиция —5.2 ещё открыт; начинаем необходимую часть5.3 раньше остальных
задач5.2. Это смена порядка, не закрытие предыдущих критериев.

- **5.3а, ближайший шаг:** AWG3.1 в control schema/issuer/verifier, общие vectors,
  dynamic gateway IDs, проверка совместимости и отказа старых клиентов; далее
  native применение и российская сетевая приёмка. Совместимость нельзя включить
  одним удалением UNSUPPORTED_TRANSPORT_VERSION.
- AWG3.1 — приоритетный кандидат для основного UDP-подключения; VLESS/REALITY —
  альтернативный TCP-путь. Работоспособность проверять по конкретным сетям.
- WG/AWG2 — только совместимость, диагностика и регрессия; новые отдельные функции
  под них не развивать, действующие назначения автоматически не удалять.
- **5.3б, исследование дополнительного транспорта:** первый кандидат NaïveProxy
  HTTPS/HTTP2; сравнительный кандидат Hysteria2/QUIC. Это исследование, не решение
  включить оба runtime и не гарантия обхода российских блокировок.
- Для5.3б: стоимость сборок/обновлений Android/Linux/Windows, DNS/UDP/full-device
  routing, размер/CPU/RAM, revoke/секреты и совместимость с нашим lifecycle;
  российские домашняя и мобильная сети, UDP blocked, loss, смена сети и блок IP.
  Внедрять кандидат только при измеримом выигрыше относительно AWG3.1+REALITY.

## 5.3в — режим подключения в сетях с белыми списками (backlog)

> Backlog / secondary. Задача сохранена, но не является немедленным engineering step;
> текущий critical path — 5N (см. Current engineering priority выше).

Добавлен24.09 по прямому запросу пользователя; ориентир — продуктовый режим
«Белые списки» у Shuka. Задача включает исследование, реализацию и сетевую приёмку,
а не только изучение конкурента. [Требования и границы](allowlist-connectivity.ru.md).

- **5.3в.1 — обследование и выбор схемы:** определить доступные входные узлы на
  тестовых SIM/операторах; разделить фильтрацию IP/маршрутов, DNS, TLS и UDP.
  Выбрать транспорт и инфраструктуру по измерениям; не считать смену SNI или
  протокола доказательством доступности IP. Описать стоимость и пределы ёмкости.
- **5.3в.2 — стенд и реализация:** отдельный пул ingress и путь ingress→egress,
  интеграция с fleet/IPAM/доступом, signed profiles, ограниченная выдача адресов,
  клиентский режим и ограниченные повторы/переключение. Сохранять identity,
  проверку подписи, revision floor и rollback. Секреты — через действующее хранилище.
- **5.3в.3 — обновление и восстановление:** доставка свежих назначений при
  недоступном основном API, заранее сохранённые резервные точки, TTL/revoke;
  проверить достижимость самого канала Reticulum в ограниченной сети.
- **5.3в.4 — приёмка:** реальные мобильные сети минимум двух операторов с
  наблюдаемым режимом белых списков; первый вход, полезный трафик, DNS,
  длительное соединение, смена сети, блокировка ingress и получение замены.
  Фиксировать оператор/регион/время и ограничения. При отсутствии достижимого
  входа показывать понятный отказ, не бесконечное «подключение».
- **5.3в.5 — эксплуатация:** ёмкость/стоимость и health отдельно по ingress/egress,
  вывод узла из работы и замена адресов через fleet; отображение и управление
  режимом в будущей Django-админке7.1, без отдельного реестра назначений.

По следующему прямому запросу пользователя5.3в переведён в реализацию: выбран
XHTTP/TLS для первого стенда, код/локальные проверки готовы (см. checkpoint выше).
5.3а не закрыт и сохраняется в очереди; его проверка на телефоне отложена. Реализация5.3в.2 зависит от выбора проверенного входа,
5.2 и клиентского lifecycle;5.3в.3–4 связаны с этапом6. Выбор NaïveProxy/Hysteria2
в5.3б сам по себе не закрывает5.3в. Закупка нового узла — после выбора стенда.
Работоспособность Shuka у наших операторов не проверена; их протокол не установлен.

После5.3а продолжить5.2: verified ACK, offline→online/relay, доступ/migration.
5.3б не задерживает основную цепочку; не покупать серверы/домены до выбора стенда.
[Обоснование и первичные источники](releases/2026-09-24-transport-priorities.ru.md).

## Проверка продуктовой гипотезы

[Сравнение других проектов](releases/2026-09-24-competitor-recovery.ru.md)
уточняет5.2/6: независимая доставка, ограниченная выдача адресов и измеримое восстановление.
Это исследование, не реализованные функции и не изменение приоритета5.3а.

[Анализ конкурентного преимущества](releases/2026-09-24-vpn-market-assessment.ru.md):
проверять время восстановления и ручные действия, а не число транспортов.
Критический открытый вопрос — автоматический failover при offline signing и
недоступном основном API. Предложенные метрики/платный пилот — рекомендации,
не принятые SLA или новая смена очередности5.3а→продолжение5.2.

## Reticulum recovery: уточнение требований5.2/6

[Проект переноса службы по постоянному destination](reticulum-recovery-design.ru.md):
разделить service identity и transport ingress; multi-ingress/discovery, согласованный
backup/fencing, pull/ACK и тест миграции при блокировке прежних IP. Полная потеря
всех carrier paths требует внешнего bootstrap. Это дизайн, не выполненная приёмка;
ближайший согласованный кодовый шаг5.3а сохраняется.

В приёмку Reticulum включить [модель обнаружения](releases/2026-09-24-reticulum-threat-model.ru.md):
публичный peer, обычный подписчик и наблюдатель на сетевом пути клиента.
Приватный discovery/сегментация пока проектные меры; секретность выданных IP не гарантируется.
