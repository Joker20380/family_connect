# Documentation

[MESH product integration,18.10](releases/2026-10-18-mesh-product-integration.md):
MESH is the product transport, VP8/RTP its carrier, Telemost its provider.
[Transport contract](../carrier/README.md#mesh-product-contract),
[architecture](architecture.md#mesh-product-model), [ADR002](adr/002-mesh-product-name.md).
Android naming is local-only; Windows/Linux media integration is not implemented.

[Telemost activated access v2,18.10](releases/2026-10-18-telemost-all-activated-preflight.md):
local HTTP rewrite and packaged-loopback checks; no per-tester grant, ordinary
activation is entitlement and short-lived crypto remains separate. NOT_DEPLOYED:
current4h management/planner/checkpoint integration still required; current CRL
evaluation fails. [Candidate contract](../deploy/friends/restricted/ACTIVATED_ACCESS_V2.md).
No server mutation or APK publication; do not switch the policy file alone.

[CRL commit/read barrier13.10](releases/2026-10-13-crl-commit-read-barrier-1.md):
PARTIAL. Exact frozen gateway accepts restored old profile N: local reload is not an
authoritative barrier or durable floor.941 sealed inputs and38 model tests×3 checked;
model is not a deployable distributed service. Common coordination/fencing infrastructure
and a future gateway reader rebase are required. Exactly next: coordination/commit-ledger
design acceptance. Writer not deployment-ready; canary policy blocked; production0.

[CRL writer safety13.10](releases/2026-10-13-crl-writer-safety-1.md):
PARTIAL, isolated unaccepted source. Exact baseline reproduced; issuer-key mismatch
now rejects before mutation/NL request.30 local tests×3 and exact frozen TLS probe
pass. RU/NL commit still lacks common reader-visible barrier; rollforward is not
distributed atomicity. Next: source-only committed-state/reader-barrier acceptance,
not canary policy or deployment. Production/owner/live actions0.

[CRL writer provenance13.10](releases/2026-10-13-crl-writer-provenance-1.md):
EXACT deployed RU/NL source recovered and byte-rebuilt; narrow independent-profile revoke
and frozen gateway rejection proved. Full acceptance FAIL: wrong local issuer-key fixture
replaces valid CRL before NL rejects the signature.19 characterization tests×3; no production
mutation. Exactly next: separate source-only writer safety acceptance, not canary issuance.

[Restricted canary identity policy13.10](releases/2026-10-13-restricted-canary-identity-policy-1.md):
PARTIAL, no issuance candidate. Exact HTTP bundle resolved; deployed CRL-writer source
provenance unresolved.23 API,10 frozen-binary TLS and6 evaluator checks PASS; TLS-only
evidence is not seed/Mux/lease acceptance. Separate-policy design retained, frozen gateway
unchanged. Next: recover the exact revocation-writer source capsule; no production actions.

[Seed-supervisor operational readiness13.10](releases/2026-10-13-gateway-seed-supervisor-op-readiness-1.md):
PARTIAL / READY=NO. Frozen bytes/baseline verified; fresh runtime stable, leaf expired,
active restricted sessions UNKNOWN. Exact API policy probe cannot establish the required
test-only identity without ordinary activation/chat eligibility. No grant, renewal,
canary, restart or owner action. Next: separately accepted test-only issuance policy.

[Seed-supervisor root-local research trigger13.10](releases/2026-10-13-gateway-seed-supervisor-trigger-1.md):
local acceptance PASS; frozen source134083d8 / binary53beb661…5138f. Default-disabled,
public-build-absent one-shot actual-Gorilla1011 control; same room/D/stream/old-cache
continuity and race/security acceptance. No deployment/owner/live actions. Exactly next:
separate operational readiness and exact-binary canary, not automatic deployment.

[Seed-supervisor predeployment readiness13.10](releases/2026-10-13-gateway-seed-supervisor-predeploy-1.md):
PARTIAL / READY=NO. Same runtime/baseline, no new fatal; process window fits, served
Family certificate expired. Permitted synthetic identity unavailable; historical trigger
requires a test binary, no compatible exact-binary one-shot control proven. No canary,
renewal, restart or owner action. Next: source-only trigger candidate/local acceptance.

[Seed-supervisor deployment entry13.10](releases/2026-10-13-gateway-seed-supervisor-deploy-1.md):
PARTIAL / PRELIVE_SERVER_CHANGED before deployment. Fresh baseline hashes match;
two normal duration-DEADLINE/exit0 completions, not new fatal1011. No restart/renewal,
owner action or test disconnect. Next is a separate readiness gate with verified
synthetic identity and exact-binary seed-only trigger; local candidate PASS preserved.

[Seed-supervisor local candidate13.10](releases/2026-10-13-gateway-seed-supervisor-1.md):
PASS local production supervisor acceptance; exact candidate sealed, not deployed.

[Real-provider same-room rejoin12.10](releases/2026-10-12-telemost-real-same-room-rejoin-1.md):
PASS isolated Telemost API/WSS/Pion/SFU episode. One seed create, real socket disconnect,
fresh full-media rejoin, unchanged old D bootstrap, original dedicated Mux/TCP stream
preserved. Code1011 test-injected, not provider-generated. No production/owner changes.
Next is a minimal supervisor source patch/local acceptance only, not deployment.

[Same-room rejoin capability12.10](releases/2026-10-12-gateway-same-room-rejoin-proof-1.md):
PARTIAL. Real local WSS/Pion/RTP, unchanged-cache authenticated bootstrap, dedicated
Family/Mux/TCP continuity and lease control passed. Actual Telemost room retention/full
rejoin after1011 remains UNKNOWN: fixture persistence is not provider evidence. No
production supervisor/deployment/owner action; exact experiment and race receipts sealed.

[Gateway WS1011 continuity12.10](releases/2026-10-12-gateway-ws-1011-continuity-1.md):
offline PARTIAL. Real close-frame→seed fatal reproduced; dedicated Family/Mux/lease
isolation demonstrated locally. Same-room fresh Pion/media and old-cache bootstrap
remain unproved; no speculative recovery patch or deployment. Race/differential
receipts sealed; owner untouched. Next is that specific local continuity proof.

[Warm-start formal acceptance2 — prelive abort12.10](releases/2026-10-12-warm-start-formal-acceptance-2.md):
PARTIAL; one authorized same-key renewal, then natural SEED_READ/SIGNAL_READ
WS_CLOSE1011 before collector deployment. Exact receipts preserved; automatic
restart/new directory. Owner untouched and attempt unconsumed; historical functional
PASS remains. Next is separate offline fatal analysis, not automatic live acceptance.

[Warm-start collector rebase12.10](releases/2026-10-12-warm-start-collector-rebase-1.md):
PASS local candidate; exact deployed API baseline recovered, AKI/skew/ACK/publisher
preserved. Isolated collector source, reproducible gateway/API builds, differential
tests and rollback sealed. Full legacy suite remains non-green with no new failures.
No deployment or owner action; next is separate controlled collector deployment and
formal evidence run. Functional PASS preserved; warm readiness remainsNO.

[Warm-start formal acceptance12.10](releases/2026-10-12-warm-start-formal-acceptance-1.md):
PARTIAL; deployment stopped by scope review. Archived HTTP collector candidate would
revert deployed AKI/clock-skew/publisher behavior. Fresh source/byte diff retained;
gateway and owner unchanged, new attempt unconsumed. Rebase collectors on the actual
API and repeat differential acceptance first. Historical functional PASS preserved.

[Warm-start evidence attribution12.10](releases/2026-10-12-warm-start-evidence-attribution-1.md):
offline PARTIAL, functional warm-start/egress/client renewal remain PASS. Two403 lack
principal attribution; independent server lease receipt not retained. Source-only
bounded collectors, differential/race/privacy fixtures and conservative evaluator
prepared; no deployment or owner action. Strict formal gate needs a separately
authorized collector-backed evidence run, not automatic CONNECT or FIELD.

[Telemost workability12.10](releases/2026-10-12-telemost-workability-proof-1.md):
live core PASS / formal evidence PARTIAL. One ACK-before-arm physical CONNECT,
cached native input, dedicated READY,7 ordinary HTTPS nonces via NL and controlled
DNS proven;723.814s same-session observation, renewal1 and subsequent traffic PASS.
Owner accepted provisioning rows0, but2 shared403 entries lack owner attribution;
independent server lease journal timed out. Do not claim complete formal PASS.
Attempt consumedYES; gate CLEANED, VPN OFF/app+chat ON, research84 unchanged.
Next is offline collector-evidence readiness, not an automatic CONNECT or FIELD.

[Signal-read cause12.10](releases/2026-10-12-gateway-signal-read-cause-1.md): offline
PARTIAL; exact ReadJSON loss point established, historical low-level causeUNKNOWN.
Local immutable typed-classifier candidate; real WS/WSS fixtures/race×3 PASS,
legacy six diagnostic failures and baseline busy-wire flake remain. No behavioral
fix, deployment or owner action. Next: separate observation-update acceptance/
deployment and natural trigger, not CONNECT. Two-phase operator fixtures22 PASS.

[Seed-read observability12.10](releases/2026-10-12-gateway-seed-read-observability-1.md):
observation binary deployed once; natural SEED_READ/SIGNAL_READ captured, automatic
restart only. PARTIAL: immediate postcheck incomplete, planned30m collector not run;
later chain/loaded-next/publication checks pass. Lower-level signaling cause remains
unknown. That next localization step is recorded above; no CONNECT/transport fix.

[Seed-read cause12.10](releases/2026-10-12-gateway-seed-read-cause-1.md): offline
PARTIAL; shared-seed failure boundary established, historical underlying cause
UNKNOWN/no client attribution. Observation-only local delta and two-phase operator
fixtures PASS; no independent behavioral defect, deployment or owner action.
Full legacy suite remains non-green. [Future manual ACK/CONNECT runbook](whitelist-warm-start-two-phase-runbook.md)
is prepared only; that historical next deployment step is now recorded above.

[Warm-start attempt12.10](releases/2026-10-12-whitelist-warm-start-1.md):
PARTIAL; research84 installed in place, exact cached selection/native offline PASS.
Operator window timed out; gate cleaned before later physical CONNECT, so blocked
warm-start/egress NOT_RUN. Natural gateway SEED_READ/UNKNOWN exit1 captured,
automatic restart/new directory; readinessNO, one physical attempt consumed late.
Final VPN OFF/app+chat ON; no second CONNECT, agent restart/renewal or public release.
[Private research84 RU](releases/research84.ru.md) / [EN](releases/research84.en.md).

[Provisioning-only seam12.10](releases/2026-10-12-whitelist-provisioning-block-seam-1.md):
local PASS/condition READY; API31/API35 real-path fixtures, zero armed provisioning
requests, cache preserved, chat/ordinary controls unaffected, bounded cleanup.
Research84 signed but NOT installed/distributed; owner and gateway untouched.
Fresh live preflight remains separate; clean CONNECT attempt unused.

[Gateway recovery12.10](releases/2026-10-12-whitelist-gateway-recovery-2.md):
PARTIAL; one same-key renewal/one start, strict chain/current publication PASS;
observer bytes unchanged. Current cache refreshed by existing background activity,
one offline exact production/native validation PASS. ReadinessNO: compliant owner-role
provisioning denial not prepared; old source-IP503 forbidden by new scope. Collector
bundle also remains unaccepted despite local binding fixtures. Attempt unused,
research83 unchanged, final VPN/app/chat OFF; leaf expires13:36:04UTC12.10.

[Exact selection12.10](releases/2026-10-12-whitelist-exact-selection-1.md):
PARTIAL; one owner production identity-bound offline selection/native validation PASS.
Cache unchanged during reader; later independent Activity/background refresh recorded.
Gateway observer captured normal4h exit0 then PROFILE/CREDENTIALS_REJECTED exit1
startups; current failed/PID0, readinessNO, clean CONNECT unused. No product patch,
renewal or agent restart. Final VPN OFF/app+chat ON, no forced user-process stop.

[Cache metadata11.10](releases/2026-10-11-whitelist-cache-metadata-1.md):
PARTIAL; one authorized reader, six disposable fixtures PASS, cache unchanged.
Actualbb5c8eb0…d8959 equals current seed; full identity-bound exact selection remains
unproved, readinessNO. Helper removed; VPN OFF, app/chat OFF. Background refreshes
before interruption explicitly recorded; CONNECT attempt unused, observer unchanged.

[Cache readiness11.10](releases/2026-10-11-whitelist-cache-readiness-2.md):
PARTIAL/NO; current observer/runtime/chain verified, exact owner cache inaccessible
without separately authorized lifecycle interruption. No refresh/CONNECT/restart.

[Gateway fatal observer11.10](releases/2026-10-11-gateway-fatal-cause-1.md):
PARTIAL/ARMED_NOT_TRIGGERED after900s; safe gateway-only receipt sourceabc604b0,
loaded/next0ccaaf81…2667a. One same-key renewal/controlled restart; strict served
chain/publication verified. Historical fatal cause UNKNOWN, research83 unchanged,
CONNECT0/attempt UNUSED. READY_FOR_CLEAN_RETRY=NO until separate cache/runtime
preflight. No owner startup, transport fix, APK publication or FIELD.

[Gateway readiness, read-only11.10](releases/2026-10-11-whitelist-gateway-readiness-1.md):
READY_FOR_CLEAN_RETRY=NO; CONNECT0, clean attempt UNUSED. Historical exit cause
UNKNOWN after bounded journal timeouts; another automatic restart observed during
preflight, same product bytes/new publication. Served chain expired; current client
cache digest unverified, seed overlap not restart-safe. No renewal/restart by agent,
owner lifecycle or product patch; last18:46:28UTC VPN OFF/app+chat ON. No FIELD.

[Dedicated-join review and pre-CONNECT abort11.10](releases/2026-10-11-whitelist-dedicated-join-1.md):
call ended, but clean preparation stopped before the physical gate: gateway exited
and automatically restarted with unchanged bytes/new directory. CONNECT0, clean
attempt NOT_RUN/not consumed; no product patch or agent gateway restart. Harness
gate10PASS; cleanup verified15:19:53UTC, not a current-state claim after late logs.
Old call causation remains unestablished; CELLULAR_CALL_RESILIENCE separate. Fresh
coherent trust/cache/server prerequisites required; no silent provisioning renewal.

[Whitelist bootstrap research83,11.10](releases/2026-10-11-whitelist-bootstrap-1.md):
private owner update/source f5240994 and matching gateway deployed; targeted local
gates PASS, baseline lint failure retained. One physical CONNECT with scoped
provisioning503 selects valid cache and passes seed Family auth, but dedicated
carrier fails before client READY. No full-phase app request or repeat CONNECT.
Warm/cold readiness NO; cleanup complete, VPN OFF/app+chat ON. No public rollout/FIELD.
[Private build RU](releases/research83.ru.md) / [EN](releases/research83.en.md).

[Full-tunnel physical-operator acceptance11.10](releases/2026-10-11-full-tunnel-egress-verify-1-manual.md):
unchanged research82; ordinary test-app IPv4 HTTPS → TUN/Telemost/Mux → NL gateway
→ controlled endpoint PROVEN, controlled DNS gateway PASS. Browser NOT_RUN, IPv6
unavailable, failover leak not tested. Two later unexpected closes automatically
recover; root cause OPEN. VPN OFF/app+chat ON; no product update/restart/uninstall.
Direct provisioning still blocks warm/cold starts in the stated whitelist model.

[Full-tunnel harness continuation11.10](releases/2026-10-11-full-tunnel-egress-verify-1-continuation.md):
request A/B lifecycle PASS and observer startup fixed; Android denies ADB input
before CONNECT. HARNESS_FAILURE, actual CONNECT0/full requests0. Product unchanged,
cleanup complete. Requires a real operator trigger, not automatic retries.

[Full-tunnel egress verification11.10](releases/2026-10-11-full-tunnel-egress-verify-1.md):
research82 unchanged; VPN-OFF Orange baseline and actual Telemost TUN verified,
but full-phase ordinary-app probe did not run. Egress UNKNOWN, not acceptance PASS.
Required direct refresh blocks whitelist warm/cold startup. Evidence/cleanup complete;
no automatic second CONNECT, product routing patch or public rollout.

[TELEMOST-LEASE-CONTINUITY-1 candidate11.10](releases/2026-10-11-telemost-lease-continuity-1.md):
authenticated same-holder renewal; controlled-clock real Family/Mux/TCP continuity
locally verified. Private research82 live: two renewals and HTTPS across deadlines;
persistent TCP only first boundary, full continuity PARTIAL. Cleanup complete,
VPN OFF/chat ON; no public rollout or repeated trial.

[Telemost lease/continuation observation11.10](releases/2026-10-11-telemost-stability-1-continuation.md):
12min after READY; expected lease expiry, exact release, real automatic open and
new full response; no behavioral patch, bounded diagnostic limitations explicit.

[TELEMOST admission ownership10.10](releases/2026-10-10-telemost-admission-ownership-1.md):
exact server capture loaded, one correlated diagnostic grant/HELLO/READY/release;
historical holder UNKNOWN, no behavioral fix or stability-closure claim.

[Field export16 / post-fix paired Telemost failure05.10](releases/2026-10-05-field-export16-beta65.md):
two authenticated cellular sessions carry data; first recovery succeeds84.446s,
both fail after about20s. Client DATA48/58 absent at gateway; RTP timer correction
insufficient. No new readiness/retry exercise; next media-boundary investigation.
This supersedes the pending trial in earlier checkpoints below.

[Field export15 / fresh tester readiness05.10](releases/2026-10-05-field-export15-beta65.md):
failed attempt19:40–19:41UTC predates renewal and never starts Telemost. Tester65
fresh native READY ACK20:00UTC confirmed20:03:32; next one mobile Auto traffic trial.
No new APK/runtime change; field stability still unproven. Supersedes pending ACK below.

[Field export14 / paired Telemost evidence05.10](releases/2026-10-05-field-export14-beta65.md):
two real tester65 sessions carry DNS/TCP data; automatic recovery now works, but
both sessions fail after roughly20s. Client→gateway DATA holes confirmed. RTP
reorder deadline defect reproduced; exact-source CI/artifact PASS, corrected gateway
deployed15:22UTC. Owner65 imports15:23:05; tester65 imports15:31:34, no mobile trial yet.
After the interruption the evening window had expired; credential-only renewal19:53
covers through06.10 02:53:04 Krasnodar. Next fresh tester fetch/ACK for the renewed
directory and one mobile trial; field resolution unproven, no APK replacement.

[05.10 server-only readiness correction](releases/2026-10-05-readiness-clock-skew.md):
HTTP/sync deployed, issuer5 renewed, unchanged owner65 fresh native READY/ACK PASS.
No separate/new APK; tester65 fresh READY/ACK confirmed14:09:44UTC. Mobile result: export14 above.
Latest gateway ceiling05.10 23:53:04UTC/06.10 02:53:04 Krasnodar after late renewal;
earlier windows below are history.

[Field export13 / mobile Auto05.10](releases/2026-10-05-field-export13-beta65.md):
current tester65 mobile attempt fails in52.244s: FETCH_FAILED, AWG/TCP NETWORK,
restricted NOT_READY before native startup. Earlier AWG worked, separately. No new
runtime fix or further identical test requested; preserve working VPN for coordination.

[Field export12 / beta65 readiness05.10](releases/2026-10-05-field-export12-beta65.md):
tester65 confirmed; native import/ACK clock sensitivity correlated with server times.
Older retained incident is beta64. Time-independence fix explicitly deferred by user;
no manual-clock instructions or new trial, preserve working VPN for communication.

[Bootstrap cleanup race correction05.10](releases/2026-10-05-bootstrap-cleanup-race.md):
source-only bounded cleanup wait and safe rejection diagnostics; fresh-fixture50
repeats/full local Go race PASS. CI blocked twice by existing TCP reset tests,
reproduced on prior accepted source. Authorized fixture-only correction passes1500
repeats per reset test; pusheda813dc5 passes both CI workflows on attempt1. Gateway
artifact11337447479/hash05571644 verified. Local full rebuild quota failure retained.
Gateway deployed05.10 10:13UTC; unchanged owner65 recovery, AUTH/cancel/AWG/TCP/privacy
and paired59/67 gap-free server events PASS. Targeted immutable65 published/downloaded
SHA/signer verified10:27UTC. Current material bound13:28:47UTC; tester fresh READY/ACK
still gates Krasnodar. Original field DATA/ACK loss not localized.

[Beta65 retained-cache refresh candidate04.10](releases/2026-10-04-beta65-readiness-candidate.md):
source86fa1ba/four CI/signing/in-place owner65 and ordinary physical refresh PASS.
Earlier bootstrap recovery failure resolved by gateway correction above. Targeted65
now published; tester last confirmed64, default60 unchanged.

[Early readiness refresh correction04.10](releases/2026-10-04-readiness-early-refresh.md):
valid old-directory cache refresh correction; persisted300s cadence and validation
preserved. Installed65 ordinary prewarm PASS; bootstrap recovery gate now PASS above.

[Beta64 paired-diagnostics candidate04.10](releases/2026-10-04-beta64-paired-candidate.md):
source ce73ddf pushed, all four CI workflows and downloaded artifact/offline signing PASS.
Owner64 installed in place and matching gateway deployed; native exhaustion→poll recovery,
real saved diagnostics/four-ID paired correlation and AUTH/cancel/privacy PASS. Effective
material bound04.10 22:57:31UTC. Separate APK64 published/verified19:14UTC; default60
unchanged. One Krasnodar trial authorized after tester update and fresh current-directory
fetch/native READY/ACK; cached READY is insufficient, tester completion still pending.

[Paired DATA/ACK/fragment diagnostics04.10](releases/2026-10-04-paired-delivery-diagnostics.md):
source-only implementation and local tests PASS; bounded endpoint samples, Android
export and offline comparison. Subsequently accepted on owner64/gateway above; field DATA loss remains open.

[Beta63 genuine native exhaustion04.10](releases/2026-10-04-beta63-native-exhaustion.md):
real8-retry native failure→production poll→new session/HTTPS PASS; process-local RTP
fault only, unchanged product/server. Original field DATA loss remains unlocalized.

[Beta63 recovery release/owner acceptance04.10](releases/2026-10-04-beta63-recovery-candidate.md):
exact-source CI/signing/in-place Redmi63 PASS; real native reconnect with injected policy
cause, bounded guard and AUTH/cancellation PASS. Targeted download SHA/signer PASS; default60,
tester last receipt62. Later native exhaustion→poll acceptance is above; field DATA stall remains open.

[Beta62 mobile export(11),04.10](releases/2026-10-04-field-export11-beta62.md):
real tester/server correlation, precise retry exhaustion with continuing ACK traffic,
and independently proven INTERNAL recovery-policy stop. No further tester repetition
needed now. [Local recovery classification fix](releases/2026-10-04-restricted-recovery-classification.md)
passes Android243/lint, Python100 and targeted Go race checks; delivered to owner in63 above.
Original transport cause remains unproven.

[Beta62 four-hour server rollout04.10](releases/2026-10-04-beta62-four-hour-rollout.md):
tester upgrade confirmed, compatible policies/full material chain/owner long import,
real correlation and tester long READY/ACK PASS. One mobile reproduction next within
the recorded actual validity window; no original disconnect-fix claim.

[Beta62 owner acceptance and targeted download04.10](releases/2026-10-04-beta62-recovery-candidate.md):
exact-source CI/signature/in-place Redmi acceptance, real four-ID correlation and
downloaded SHA/signer PASS. Subsequent server activation is recorded above; next
Russian mobile reproduction pending. Default/updater remain60; no transport-fix claim.

[Restricted session terminal diagnostics03.10](testing/restricted-session-diagnostics.ru.md):
targeted beta61 r2 owner update and diagnostic gateway deployed/accepted: real
four-ID correlation, lifecycle and privacy PASS. [Separate diagnostic download04.10](releases/2026-10-04-beta61-r2-direct-delivery.md)
verified; beta60 remains production/default/updater, no FIELD expansion. Russian
reproduction and root cause remain open.

**Current product critical path — 30.09.2026:**
[5N-BOOT-1 → 5N.6 → MVP Orchestrator → Krasnodar FIELD-1 → 50–100-user beta](PLAN.md).
Начните с [CURRENT PRODUCT STATE](STATUS.md), затем [продуктовой архитектуры](architecture.md):
implemented beta / proven experimental / planned разделены явно.
[MVP Orchestrator implementation / текущая acceptance](releases/2026-09-30-mvp-connectivity-orchestrator.ru.md):
одно CONNECT, bounded normal fallback/BOOT-1, existing VPN owner и fail-closed guard;
isolated physical PASS01.10 с сохранённым initial FAIL; не public rollout/не FIELD-1.
5N.1–5N.5, ReliableStream/DNS containment и automatic Room Broker приняты;
Whole-device path принят isolated; production rollout ещё не выполнен.
[5N-PROV-1 authorized deployment FAILED / ROLLED BACK](releases/2026-10-01-5n-prov1-production-restricted-provisioning.ru.md):
existing Friends identity → restricted provisioning/BOOT-1 → secure Android cache;
[owner-only deployment, migration, secrets и rollback](../deploy/friends/restricted/README.md).
В попытке №1 NL offset expiry был отклонён Python; в попытке №2 исправление
timestamps уже прошло живую NL READY/UTC `Z` проверку. RU sync затем не импортировал
`clients`, rollout снова откачен до API activation. Локальный packaging fix:
явный source manifest, isolated zipapp и fixture-only pre-network CLI smoke;
production не изменён. Authority требует свежего JIT renewal только перед новым
отдельно разрешённым rollout. Это integration gate перед actual-Friends
readiness/rehearsal и final FIELD APK.
Попытка №3 из `2705db4`: closed-runtime `--check`/live sync, NL READY и UTC-Z PASS;
после API activation normal HTTP smoke failed, выполнен rollback. API/ingress
восстановлены, AWG/TCP без restart, Redmi не трогали. CRL/DB sequence11 сохранён;
точный HTTP downtime не доказан. Следующий шаг локальный: crash-safe probe receipt
и воспроизведение API/ingress transition; без автоматического retry.
[Historical material-only preflight READY](releases/2026-10-01-5n-prod-deploy-preflight.ru.md):
same authority, CRL refreshed to3, owner-installed provider config schema PASS;
no token value/hash/size exposed. Recheck expiry before separately authorized use.
[5N-PROD-AUTHORITY READY / staged only](releases/2026-10-01-5n-prod-authority.ru.md):
explicitly authorized first Family, sole owner grant, existing NL identity binding,
signed delegated issuer/real CRL and native validation. No service/API deployment;
provider-token phase excluded. Refresh short-lived CRL before future use.
[Historical material inventory / initial BLOCKED audit](releases/2026-10-01-5n-prod-materials.ru.md).
[5N-BOOT-1 PASS / isolated physical cached-state acceptance](releases/2026-09-30-webrtc-5n-boot1-bootstrap.ru.md):
[cached directory, rendezvous, bounds и isolated runbook](../carrier/bootstrap/README.md).
[5N.5 evidence](releases/2026-09-28-webrtc-eu5-mux-dns.ru.md) ·
[Room Broker PASS и temporary ingress](releases/2026-09-28-webrtc-5n-room-broker.ru.md) ·
[Rebaseline report](releases/2026-09-30-product-engineering-rebaseline.ru.md).
Второй restricted carrier, Home Gateway и RNS-over-WebRTC — backlog.

Следующие датированные priority notes — историческая навигация, не текущий порядок.

**Приоритет25.09 уточнён:** [Restricted Android→Telemost VP8→Linux EU](PLAN.md)
без обязательного Windows Home Gateway/IP-over-RNS. Reticulum control/recovery
сохраняется. [Решение в существующем дизайне](reticulum/HOME_GATEWAY_DESIGN.md).
Добавлены WEBRTC-EU-1–6/5N; сначала binary/auth, затем TCP+DNS/full-device.
Preparation-only относилось к25.09; текущие runtime/gates — в STATUS/PLAN.
Существующие AWG/TCP/XHTTP не заменяются.

**WebRTC underlay — подготовка25.09 (backlog):** [существующий Home Gateway design](reticulum/HOME_GATEWAY_DESIGN.md)
расширен path manager/provider/IPC contracts, исследованием WB/Telemost и gates
WEBRTC-1–5. [План5H–5M](PLAN.md) · [Лицензии](legal/DEPENDENCY_LICENSE_AUDIT.md).
Реализация и устройства пока отложены; новый статус — подготовка5A/5H.

**Стратегия25.09 уточнена (backlog):** [Home Gateway](reticulum/HOME_GATEWAY_DESIGN.md) —
Reticulum для control/discovery/negotiation, выбранный защищённый transport для IP.
Сейчас этап5/начало5A: доказать достижимый control и data ingress при активных
мобильных белых списках; затем телефон↔домашний ПК. [Глобальный план](ROADMAP.ru.md).

**Новый приоритет25.09: [Personal/Home Gateway over Reticulum (backlog)](reticulum/HOME_GATEWAY_DESIGN.md)**
— требования, integration points, threat model, Stage5A–5G и gates RNS-1–RNS-5.
[PLAN](PLAN.md) · [Статус](STATUS.md) · [Лицензионный аудит](legal/DEPENDENCY_LICENSE_AUDIT.md)
· [Third-Party Notices](../THIRD_PARTY_NOTICES.md). Дизайн зафиксирован; рабочий
Home Gateway и приёмка RNS-2 пока отсутствуют.

[XHTTP/TLS: исследование, реализация и границы5.3в](xhttp-implementation.ru.md).

[Режим сетей с белыми списками: требования и план5.3в](allowlist-connectivity.ru.md).

[Android: подключение выбора gateway к службе/UI](releases/2026-09-24-android-selection-service.ru.md).

**Новому разработчику: [общая карта кода по модулям](code-map/README.ru.md)** —
сервер, клиенты, мессенджер, эксплуатация, зависимости и границы готовности.

[Android: транзакционная смена gateway и восстановление](releases/2026-09-24-android-gateway-transaction.ru.md).

Разработчику: [карта managed-кода, проверки и восстановление](managed-control-code-map.ru.md).

[Android AWG3.1 journal и фактический статус публикации документации](releases/2026-09-24-awg31-android-journal.ru.md).

[AWG3.1: согласование Java/C#/Python и границы проверки](releases/2026-09-24-managed-awg31-native-verifiers.ru.md).

[Защита от блокировок: требования и приёмка](blocking-resilience.ru.md) ·
[Managed AWG3.1: локальный checkpoint5.3а](releases/2026-09-24-managed-awg31.ru.md).

[Как другие проекты восстанавливают доступ и доставляют адреса](releases/2026-09-24-competitor-recovery.ru.md).

Этап4 принят пользователем как пилотный выпуск. Этап5 начат: независимый служебный
канал и расширяемый парк серверов. [Контракт](stage5-fleet-contract.ru.md) ·
[Аудит5.1 и первые компоненты](releases/2026-09-24-stage5-audit.ru.md).
[Текущий план](PLAN.md) · [Основание приёмки](STATUS.md).
[Приоритет AWG3.1 и исследование третьего транспорта](releases/2026-09-24-transport-priorities.ru.md).

Последние доработки: [голосовые beta50: жесты, прокрутка и фон](releases/2026-09-23-switch-colors-beta50.ru.md) · [мессенджер и уведомления](testing/messenger-notices.ru.md).

- [family_connect: обновления Android, язык, бренд и карта](releases/2026-09-20-updater-language-brand.ru.md).

- [Native Friends AWG 3.1 на Linux/Windows: проверки и rollout](releases/2026-09-20-desktop-awg31.ru.md).

[Product introduction](../README.md) · [Русская версия](../README.ru.md)

Updated03 October2026. Verified Android distribution: beta60/code60,
Linux0.2.11 / Windows0.2.15; Windows0.2.14 compatibility fallback retained.
Android public bytes, signer, catalogs and invitation routes verified03.10; desktop links unchanged.
[Current distribution](releases.md) · [Documentation required with every version](releases.md#documentation-with-every-version).

Start with the guide for your role. [STATUS](STATUS.md) is the source of truth for
installed/deployed versions; dated reports preserve what was checked at that time.

[Windows0.2.14: интерфейс, ключ и приглашение](releases/2026-09-24-windows0214-installer.ru.md) · [English](releases/0.2.14.en.md).

## Users

- Getting started and troubleshooting: [English](getting-started.en.md) / [Русский](getting-started.ru.md).
- Client installation: [English](clients.en.md) / [Русский](clients.ru.md).
- [Detailed Android friends walkthrough](testing/friends-quickstart.ru.md).
- Desktop updates: [English](updates.en.md) / [Русский](updates.ru.md).
- [Security](../SECURITY.md) and [privacy](privacy.md).

## Operators

- [Friends deployment](../deploy/friends/README.md).
- [Fleet leases/IPAM: хранение, API и recovery](fleet-leases.ru.md).
- [Fleet proof авторизация и scheduler](fleet-access-scheduler.ru.md).
- [Fleet offline publication: подпись, доступ и схема3](fleet-publication.ru.md).
- [Checkpoint5.2:269 тестов signed publication](releases/2026-09-24-fleet-publication.ru.md).
- [Checkpoint5.2:201 тест и миграция](releases/2026-09-24-fleet-services.ru.md).
- [Fleet gateway fencing и worker](fleet-gateway-fencing.ru.md).
- [Fleet WG/AWG и SSH: контракт, установка и границы](fleet-wg-ssh.ru.md).
- [Native fleet-приёмка:12 сценариев WG/AWG+SSH](releases/2026-09-24-fleet-native.ru.md).
- [Повторяемый изолированный стенд](../pilot/fleet-native/README.ru.md).
- [Этап5.2: WG/SSH checkpoint,163 теста](releases/2026-09-24-fleet-wg-ssh.ru.md).
- [7.1: единая Django-админка серверов, доступа и платежей](PLAN.md#django-admin).
- [Этап5.2: проверки постоянных выдач](releases/2026-09-24-fleet-leases.ru.md).
- Registration: [English](registration.en.md) / [Русский](registration.ru.md).
- Gateway reconciliation: [English](gateway-reconciliation.en.md) / [Русский](gateway-reconciliation.ru.md).
- [Persistent peer worker: deployment/rollback](../deploy/product-peer-worker/README.md)
  and [RU/NL disk I/O diagnosis](releases/2026-09-29-disk-io-recovery.ru.md).
- [Paired Linux control rollout](linux-control-preview-rollout.ru.md).
- [Linux AppImage + .deb packaging design](linux-appimage-deb.ru.md).
- Operations/diagnostics for the original lab: [English](operations.en.md) / [Русский](operations.ru.md).
- [Release distribution and signing](releases.md).

## Developers

- [5N-OWNER-PROOF-HANDOFF](releases/2026-10-02-5n-owner-proof-handoff.ru.md): local
  acceptance split; controlled server F/G is not real-owner proof. Real F/G stays
  inside Friends product prewarm, with old generation retained for rollback.

- [5N.5: bounded TCP mux + Family DNS](releases/2026-09-28-webrtc-eu5-mux-dns.ru.md):
  **PASS**, physical4 simultaneous public HTTPS,304.138s mixed5 TCP+171 DNS,
  exact/fair/bounded, native local destination DNS denied, independent lifecycle.
  [DNS dependency audit/manual procedure](testing/webrtc-dns-containment.ru.md).
  No TUN/full-device DNS/Room Broker/production rollout; STOP after5N.5.

- [5N.4: single admitted TCP stream](releases/2026-09-28-webrtc-eu4-single-tcp.ru.md):
  **PASS**, physical public HTTPS10MiB, controlled exact duplex300.821s,
  half-close/errors/security/regressions/cleanup; failed attempts preserved.
  No mux/TUN/production rollout; STOP before5N.5.

- [5N-PERF-2: reliable long-duration operating envelope](releases/2026-09-27-webrtc-5n-perf2-reliable-envelope.ru.md):
  **PASS**, physical Android/Telemost/Amsterdam, fixed reliable defaults;
  1.742311Mbit/s/30min, conservative1.480531Mbit/s/15min; ceiling not established,
  cleanup/regressions complete, no5N.4.

- [5N-REL-1: reliable ordered bytes before Family TLS](releases/2026-09-27-webrtc-5n-rel1-reliable-stream.ru.md):
  bounded selective repeat/SACK, deterministic fault matrix, natural/injected live
  gap recovery and300s physical Android validation, **PASS**; cleanup complete.
  [Wire format, limits and threat boundary](../carrier/reliablestream/README.md).

- [5N-PERF-1: physical VP8 capacity measurements](releases/2026-09-27-webrtc-5n-perf1-carrier-capacity.ru.md):
  window/offered-load/payload sweeps, timing and raw media evidence; long-run
  integrity failures prevent accepting a sustainable carrier ceiling. No5N.4/rollout.

- [Telemost5N.1 carrier: build и live runbook](../carrier/README.md),
  [recovery/results27.09](releases/2026-09-27-webrtc-eu1-telemost-binary.ru.md):
  real Linux↔Telemost VP8↔Amsterdam PASS27.09 (291 checks +30s/5min);
  production/версии не менялись.
- [Android5N.2: standalone APK и operator runbook](../clients/android/telemost-runtime/README.md),
  [physical-device results27.09](releases/2026-09-27-webrtc-eu2-android-binary.ru.md).

- [Contribution and build checks](../CONTRIBUTING.md).
- [Architecture map](architecture.md): current product versus experimental relay paths.
- Device identity: [English ADR](adr/001-identity-provisioning.en.md) / [Русский ADR](adr/001-identity-provisioning.ru.md).
- Provisioning: [English](provisioning-provider.en.md) / [Русский](provisioning-provider.ru.md).
- [Stage 5 control protocol](stage5-architecture.ru.md), [native binding](stage5-native-binding.ru.md).
- [Messenger design](reticulum-messenger.ru.md) and [core](../messenger/README.ru.md).
- [Android runtime acceptance](testing/android-stage5-live.ru.md).
- Lab testing: [English](testing.en.md) / [Русский](testing.ru.md).

## Project

- [Current state](STATUS.md) and [working plan](PLAN.md).
- [Desktop Friends TCP recovery and refined Linux UI](releases/2026-09-20-desktop-friends-apply.ru.md).
- [Desktop identity storage and recovery checks](releases/2026-09-19-desktop-identity-storage.ru.md).
- [Desktop modernization](desktop-modernization.ru.md) and [first integration checks](releases/2026-09-19-desktop-friends-foundation.ru.md).
- [Roadmap](ROADMAP.ru.md); historical plans are linked separately.
- [Release model](releases.md) and [GitHub Releases](https://github.com/Joker20380/family_connect/releases).
- [Three-platform download verification](releases/2026-09-20-three-platform-downloads.ru.md).
- [Licensing gaps](licensing.md).
- [Public presentation audit](releases/2026-09-19-github-presentation.ru.md).

## Engineering history

All detailed reports remain available in [releases](releases/) and the
[preserved session index](history-index.md). Implementation logs:
[English](implementation-log.en.md) / [Русский](implementation-log.ru.md).
Older instructions may name retired hosts or superseded interfaces; follow current
runbooks and STATUS before operating anything.

- [Коммерческая гипотеза: восстановление после блокировок и конкуренты](releases/2026-09-24-vpn-market-assessment.ru.md).

- [Reticulum: перенос службы, discovery и границы восстановления](reticulum-recovery-design.ru.md).

- [Критические секреты и аварийное восстановление](secrets-and-recovery.ru.md).

- [Локальная подпись с ключом из KeePassXC](vault-signing.ru.md).

- [Закрытые серверные копии и проверка восстановления](server-secret-backup.ru.md).

- [Время серверов и диагностика chat-sync](server-time-and-chat-sync.ru.md).

- [Изолированная проверка восстановления KeePassXC](vault-restore-rehearsal.ru.md).

- [Потребители секретов и состояние миграции](secret-consumer-register.ru.md).

- [Подпись Android APK из KeePassXC](android-vault-signing.ru.md).

- [Актуальность локальных SQLite и границы классификации](local-sqlite-backup-review.ru.md).
