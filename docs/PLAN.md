# План / Android controlled beta and paused desktop queue

## Current engineering priority / Текущий critical path

### Authorized operational exception — NL-REPLACEMENT-20261030

**NL-REPLACEMENT-20261030 / READY_FOR_OWNER_NL_SMOKE.**
Owner-executed Sprintbox console checks at11:52UTC confirm the RU host, synchronized clock,
database integrity, unchanged API/SSH processes and real local backend/proxy challenges PASS.
The diagnostic timeout is localized to journalctl, not the challenge endpoint. A bounded
kernel-ring follow-up at11:54UTC covers the last hour: no OOM, storage, conntrack-full or
lockup match. No service restart/reload, host reboot or product configuration change.
Three consecutive samples from each of operator and new NL at11:54–11:55UTC pass SSH,
verified TLS, real challenge and signed device-status; no504. Current control-plane gates
PASS. The earlier intermittent stall's root cause remains NOT_PROVEN, not declared repaired.
Catalog4/signature/new NL endpoint and unchanged RU entry are reconciled read-only at
11:55:13UTC. No republication or sequence5. Owner subsequently reports AWG/internet working;
owner now confirms the HTTPS egress address matches185.10.158.212 and reports Disconnect.
This is owner-reported AWG egress PASS; resource cleanup is not yet verified. TCP/Auto-MESH not run.
The missing NL load percentage is localized: fresh metrics, but the replacement provider's
channel capacity is unverified. Android intentionally displays No data rather than treating
CPU alone as total load. No guessed capacity, source/configuration change or APK update.
Owner authorizes a general MESH-capable Android update: the no-build restriction is lifted,
not the release gates. Candidate107 is built from all2073 hash-verified accepted106 source
members plus three bounded changes: version, quiet notification updates and explicit microphone
permission-denial handling required by lint. All12 native libraries including MESH are unchanged.
219 JVM tests/33 suites and lint PASS;15 source/delta and4 publication tests PASS. APK unsigned,
not installed or published. Owner explicitly accepts Android12+/ARM64 as the general-release
target; Android below12 is unsupported, not a pending compatibility gate. Public-source
integration now preserves the accepted106 Android UI/MESH code with the notification fix.
All376 canonical JVM tests/63 suites and lint PASS;34 focused release/source checks PASS.
CI rebuilds Android JNI from public source with provenance and Codec2 corresponding-source
materials; no gateway rebuild/deployment or unrelated desktop job for this Android-only change.
Initial hosted CI41207389926 passes Android control JVM checks but stops on an unrelated
server publisher root-only fixture. Android carrier regression now selects the JNI transitive
dependencies with race checks; server validators/tests are unchanged. Hosted platform CI retry,
downloaded artifact qualification, offline signing and owner runtime remain required before
optional publication. The earlier private unsigned candidate is not the release.
Fresh HTTPS/signature readback: public Android beta60/update sequence1, optional policy unchanged.
Gateway catalog4 is separate and unchanged. No server/registry/admission change or mandatory update.
Owner says an older version is quiet; notification regression cause remains unproven without
phone evidence. Panel1000GB is traffic volume, not Mbps. Canary stays PAUSED.

New NL **185.10.158.212** has accepted AWG/TCP and now real production-bound MESH
DNS/HTTPS/egress acceptance. Reused **FLEET_MESH_PROBE_1**; no second identity/invitation,
owner identity, paid event or APK build. Probe retained non-revoked in encrypted custody.

Join cause: **PRE_CONNECT_OPERATOR_CONTROL_MISSING**. The relative operator-control
boundary was absent in the replacement service working directory. Restoring the exact
retained seven-file boundary fixed pre-Connect configuration rejection; gateway source,
binary, trust, signaling and service environment are unchanged. Direct Telemost join PASS,
then the sole full MESH retry PASS: registration, Family TLS, three DNS queries, four
verified HTTPS streams, new NL egress and bounded cleanup. Three stable samples, zero restarts.

Signed catalog **4** was published; initial authenticated NL readback returned the new endpoint,
RU entry and probe assignment remain unchanged. Actual Android catalog parser PASS without
APK update; Android106 owner AWG smoke is **IN_PROGRESS**, not completed by parser
acceptance. Owner-reported HTTPS egress now matches the new NL; cleanup is still unverified.
Prepared routing artifact and mailbox/monitoring target updates are deployed.
Fresh11:55:13UTC readback validates canonical profile/certificate/CRL, floor **27226**,
RU/NL directory equality and actual SSH snapshot. Renewal evaluates NOOP; no material refresh
is needed at that observation. Normal renewal/read-only sync timers are active/waiting,
last workers succeeded, controller COMMITTED and neither node has an active operation owner.
New NL remains active with integrated publisher rotation; no separate publisher timer.
Old NL remains **FENCED**. No rollback/catalog rewrite or RU reboot was attempted.
Paid ledger **0/0**, payments/revenue0, cohort0/10. **BETA-0-CANARY-1 PAUSED**;
paid-canary, subscription events and Android stage0 stay off. Complete the current owner
notification installed-runtime and AWG cleanup checks, then TCP and Auto/MESH once each in this
same operation. No further publication. Not NL_REPLACEMENT_LIVE until all owner gates PASS.

NEXT within this same operation: run exact-source public platform CI for canonical107;
then downloaded artifact qualification, offline signing and owner in-place runtime acceptance
before optional publication. No ADB device is connected. The former65-source discrepancy
is corrected by canonical integration of accepted106 Android members; qualify those public sources.
Local build/tests/lint are not installed acceptance. Keep public beta60 and gateway catalog4
unchanged until their separate gates pass. Owner reports new NL HTTPS egress and Disconnect;
resource cleanup remains unverified. No new identity, paid action or admission expansion.
After notification/runtime and cleanup acceptance, test TCP once and Auto/MESH once with current readiness
import/ACK. Keep normal freshness monitoring active while waiting. Only all owner/server
gates permit NL_REPLACEMENT_LIVE. No new PLAN ID, probe identity, owner-canary use or
automatic product-queue advance. On a post-publication failure, stop failed NL admission
through the supported catalog route; never reactivate the fenced old node automatically.
[Current evidence and rollback](releases/2026-10-30-nl-gateway-replacement.md).
Earlier provider/network observations below are retained context, not the restoration path.

**ANDROID-CONTROLLED-BETA — единственный текущий critical path (owner decision27.10).**
**Current substep BETA-0-CANARY-1 — PAUSED_BY_OWNER / LIVE_WRITES_NOT_RUN.**
Owner subsequently authorized availability restoration, not canary resumption.
Fresh09:11–09:16UTC comparison finds accepted snapshot/maintenance/gateway hashes,
renewal helper, launcher and base gateway unit unchanged. Paired header-only capture:
19 matching RU outbound SYNs, zero matching packets at NL; no capture drops. Reverse
NL→RU HTTPS connects, while new RU→NL SSH/HTTPS still time out. NL has no attached XDP
or tc ingress/egress filters in this readback. Blocking network hop remains unknown;
no evidence supports an application-code rollback. Recovery is blocked on RU→NL
connection establishment. No production changes/restarts; expired material retained,
not accepted or substituted. Provider network investigation is required; canary paused.
Post-provider boot readback30.10 08:55–09:04UTC: NL administrative SSH restored;
ordinary AWG/TCP, mailbox, Reticulum and monitoring units active. Memory29.19–31.12%,
load0.14–0.25, no swap; this short observation does not resolve the earlier memory rise.
Service recovery is PARTIAL: restricted gateway inactive/disabled, its listener absent;
canonical gateway certificate and CRL expired29.10 11:42:38UTC, directory expired13:04:25UTC.
Floor remains aligned27224; canonical boundary/configuration and accepted snapshot/gateway
artifact hashes retained. Actual RU-origin SSH snapshot times out; direct RU→NL TCP22/443
also time out while local→NL succeeds. Renewal timer waiting, last worker failed.
RU Friends HTTP dispatch responds as expected; paid ledger freshly0/0. No operator
restart, refresh, route/source change or canary action. No full VPN/client acceptance;
46 AWG peers loaded but no recent handshake/traffic in the bounded sample. Canary paused.
This fresh observation supersedes the earlier total-inaccessibility observations below.
Memory retrospective:1282 stored NL samples. Observed post-cutover28.10 median60.10%;
29.10 08:23–08:30UTC58.81–60.90%, rising to87.52% at08:42 and89.92% at09:03.
Metric uses MemAvailable, not merely free memory. Overnight and pre-failure gaps exist.
Per-process RSS/OOM evidence is absent; our application/background workload is not ruled
out. No process attribution or proven causal link to the separate boot panic yet.
Provider screenshot supplied29.10 now identifies a boot-time kernel panic:
VFS unable to mount root filesystem on unknown-block(0,0). This is provider evidence,
not a successful remote readback. Underlying cause and original pre-reboot stall remain
unknown; it does not prove lost data or implicate the application migration. No OS repair
performed. Need full boot log, attached-disk/initramfs/root-target checks and safe recovery.
Owner paused the canary29.10 and requested read-only NL diagnosis. No automatic resume.
NL IP responds, but SSH banner exchange times out from both local and RU vantage points.
Last successful monitor09:03:55UTC: RAM89.92%, disk50.42%; earlier load peak15.55.
Resource/IO stall is a hypothesis, not confirmed OOM or storage failure; console needed.
Owner subsequently requested availability recovery and reported pressing the provider
reboot control. Completion is unconfirmed:09:35–09:37UTC SSH still gives no banner;
ICMP3/3 and TCP22/443 were then reachable. Owner subsequently reported boot completion;
at09:40UTC TCP22/443 time out and ICMP0/3; RU also cannot reach SSH. OS/service startup
is unverified. Owner subsequently reported Running with an empty connected console,
and announced another reboot at10:06UTC. Seven bounded checks through10:09UTC show
no ICMP reply and TCP22/443 timeouts; RU independently confirms both port timeouts.
Reboot mode/completion and OS startup remain unverified. No further power action sent.
No canary resume or application/config change.
Prior live-entry preflight failure follows.
Owner decision29.10: former zero-certificate gate is
**SUPERSEDED_BY_PRODUCT_CONTRACT_REVIEW**. No wait for zero certificates before stage0.
Fresh09:14:18UTC binding/exact Android106/device-invite PASS, ledger0/0, cohort0/10;
baseline safe certificate token dc6b3aa3b462 retained unchanged as evidence.
Actual09:17:07UTC failure: existing forced-command SSH snapshot exits255 with banner
exchange timeout. Renewal timer active, worker not running, last result exit-code/1.
Direct administrative SSH also times out; cause not established. This is failure of
the already-required live route, not a new certificate/infrastructure/source gate.
Canonical migration acceptance retained; no redesign, reconciliation or restart.
Fresh backup/permit/activation NOT_RUN; no paid/readiness/Android/CRL writes.
Parameters fixed: natural600s, Connect90s, post-expiry120s, CRL phase900s,
post-CRL180s, final recovery2592000s; internal_canary/amount0/revenue0.
Future canary continuation requires owner resume first, then the listed minimal
preflight/backup and fresh ГОТОВ before stage0. No automatic repair or resume.
[Current canary evidence](releases/2026-10-27-android106-beta-0-canary-1.md).

**Accepted migration milestone at3996fa0 — READY_FOR_OWNER_LIVE / LIVE_CANARY_WRITES_NOT_RUN.**
PINNED_VENV_RUNTIME_PASS / SNAPSHOT_LAUNCHER_ACCOUNT_REHEARSAL_PASS /
CANONICAL_PROFILE_MIGRATED / RENEWAL_GATEWAY_SNAPSHOT_ALIGNED / CRL_FLOOR_ALIGNED.
Same checkpoint; previous rollback is historical and remains accepted.
Source fix5cc52f6bf967174bdfa34ba89436c4ad3b13ca60 pushed, remote SHA verified.
262 focused launcher/runtime/snapshot/canonical/package/authorization/parser/directory
checks PASS; retained coherent artifacts remain exact and unchanged fromc9c0a4d.
Real temporary-key SSH rehearsal PASS on a fresh secure non-authoritative copy;
cleanup PASS, original authorization bytes restored, removed key rejected.
Fresh private coordinated backups and a separate fresh canonical copy from current
live bytes verified. Only its floor changed27088→27219; CRL bytes/number unchanged.
Actual canonical snapshot PASS **before** the sole gateway restart, again afterward,
and after old-profile retirement. TLS/listener/publisher PASS; accepted renewal evaluate
NOOP with zero writes/promotions, including after retirement. Renewal timer active.
One authoritative canonical profile; all five profile routes and shared root-controlled
lock aligned. Publisher directory route/configuration unchanged, valid rotation accepted.
Old profile and rehearsal copy private/inactive; temporary credentials0.
New continuation budgets: rehearsal credential1/1, timer cycle1/1, offline floor1/1,
gateway cutover restart1/1, emergency rollback0/1. No automatic second cutover.
Final20:20:38UTC28.10: embedded CRL/floor27219, material headroom10170s;
ledger0/0, cohort0/10, owner certificates0, binding/exact Android106 unchanged.
No paid/readiness/Android/stage0 action, RU CRL/sequence mutation or Friends HTTP restart.
Historical NEXT at3996fa0 was owner ГОТОВ; that reply is now received.
The current live-entry certificate-horizon gate above supersedes that pending handoff.
[Canonical-profile receipt](releases/2026-10-28-android106-beta-0-canary-canonical-profile.json).

**Historical entry BETA-0-CANARY-1 — OWNER_CANARY_BOUND_READONLY /
BLOCKED_PROFILE_WRITER_CONFLICT / LIVE_WRITES_NOT_RUN.**
Read-only continuation from9205588 stopped at the required pre-source writer gate.
The active approved credential-renewal schedule reaches the existing root RPC;
its exact pinned NL node stages and atomically replaces the same live profile.
All13 deployed source-member hashes match controller/node pins. This is a legitimate
non-maintenance profile writer, not merely unused code. The running gateway also
references that profile. Moving only snapshot/maintenance would leave them detached
from the renewal-updated profile. Layout separability is not qualified; no source
redesign or package build. Shared publisher parent/group-write, directory, profile,
lock, snapshot route and services remain unchanged. No layout migration, backup,
permit, credential, maintenance operation, restart or canary action; budget0/1.
Fresh signed RU/NL CRL/sequence27216 already observed at entry; floor27088 remains.
No CRL generated by this checkpoint. Final material headroom13266s at readback;
ledger0/0, cohort0/10, owner certificates0, binding/exact106 retained. No-write PASS.
STOP. NEXT — separately authorize a coordinated profile-path/ownership design that
includes the existing renewal writer and gateway reader. Do not migrate only the
snapshot route, change renewal/publisher permissions or begin live canary automatically.
[Split-boundary receipt](releases/2026-10-28-android106-beta-0-canary-split-boundary.json).

**Historical read-only input — BETA-0-CANARY-1 / OWNER_CANARY_BOUND_READONLY /
BLOCKED_CRL_PROFILE_COMPATIBILITY / LIVE_WRITES_NOT_RUN.**
Dependency: CP2 accepted DONE / PAID-AWARE EMPTY-COHORT BACKEND SERVING, publisher
capability preserved, real payment/enrollment NOT_RUN. No CP2 redeployment/restart/
migration/source-package gates. Same ANDROID-CONTROLLED-BETA root, no CP3.
Scope: only OWNER_CANARY_1; planned permanent1/10 internal slot and9 customer slots.
No slot occupied/reserved in the backend yet. No substitute production identity.
Progress: purpose customer_payment/internal_canary in control-plane operational
metadata only; existing payments default customer, zero-value canary, immutable
purpose, separate counters and explicit UI/audit/admin receipt classification.
Local PG+synthetic-volume backup/disposable restore PASS; running console rebuilt,
migration0006 installed,50 bindings/3 old customer records/operations/prior audit and
credentials preserved.118 PostgreSQL console +76 affected backend tests PASS.
Source-only context permissions corrected for restrictive umask (2 tests).
Bounded HMAC-token-only canary wrapper and committed-source packaging implemented:
Normal four-stage path unchanged; emergency recover added only for versions1/2
after natural expiry with no valid certificate, exact30 days from permit.period_start
and execution window<=300s. Bounded dispatch permits server delay0..299s without
rebasing the payload; future/closed dispatch fails RECOVERY_DISPATCH_WINDOW_CLOSED.
Terminal reference_hash marker prohibits new operations
after recovery; identical backend-payload replay alone remains allowed.79 canary
tests PASS; existing backend remains sole authority. No new schema/CRL action or
generic Django production write. Source packaging is lookup_only; see report receipt.
Exact-payload CRL source gate complete: pure builder reused by publish_crl, immutable
private payload/request, one-generation journal, proven-NOT_SENT-only retry (max2
attempts), exact trusted gateway readback, post-acceptance commit/recovery A–E.
98 new tests PASS;206 existing restricted/sync/directory PASS with29 optional native
skips/4 native deselections.118 console/79 canary/76 backend/2 preparation PASS;
Django system/drift PASS. Unbound source package only, no transport/config/permit.
Those source gates performed no production lookup/registry access/mutation, Android
interaction, CRL or CP2 restart.
Read-only continuation from6dff337: exact lookup artifact verified; one owner lookup
and one bound status PASS. OWNER_CANARY_1=`dev_fa4f7e03ca04`, authenticated Android106
observation PASS; ledger0/0, cohort0/10. Private status-only artifact fromad086c0:
two byte-identical builds, permit=null,4 synthetic status/negative-guard checks PASS.
No valid owner certificates; CERTIFICATE_HORIZON_CLEAR. RU material validation PASS.
That initial parser observation is superseded by the read-only f499bdf provenance
review: NL_VALIDATOR_ONLY_DRIFT. Old auxiliary parser maximum3600s; actual forced
command maximum14400s, matching current directory/timestamp function hashes. Same
exact bytes/lifetime13401.739755428s PASS on actual gateway; no precision mismatch.
96 affected tests,48 synthetic parser and18 gateway/floor checks PASS; no correction
package built because runtime parser drift was not proven.
Separate live-entry blocker: the actual forced command is a read-only security snapshot
endpoint; incoming CRL payloads fail MAINTENANCE_TRANSACTION_REQUIRED. Embedded and RU
CRL27211 match, minimum_crl27088, guard=max(embedded,minimum). No next-payload/floor
update path is established on this command: CRL_FLOOR_UNRESOLVED, not accepted as
CRL_FLOOR_LAG_NONBLOCKING. This is a delivery-contract gap, not proven numeric corruption.
No lookup/status repeat or binding change. Owner certificates remain0, ledger0/0.
Local read-only monitoring active/fresh, NL registry UNAVAILABLE, production writes
disabled. Protected ledger/identity/policy, owner certificate/readiness scope and
service/material/profile state unchanged; concurrent unrelated certificate/readiness/
chat activity disclosed, no whole-DB equality claim. Materials exceed720s at readback.
Completion gate: exact authorized-device binding; live activation/paid certificate
boundary/MESH Connect; natural expiry and new challenge/fetch/reconnect denial;
active-session behavior; CRL generation/propagation; recovery/reconciliation and
reactivation on the same identity; Android state preservation. All live stages NOT_RUN.
Emergency recovery source gate complete; binding is read-only, paid/live acceptance
remains NOT_RUN. Historical review proposed bounded maintenance/delivery and
floor-contract reconciliation. Source is ready; production continuation is blocked by
the fresh preflight above. Preserve the snapshot. Do not
enable generic writes or substitute the old mutating archive. No repair, refresh,
phone opening/Connect or request for ГОТОВ while live entry is blocked. No bound
write permit, canary write credential or CRL transport is installed.
Final same-identity30-day active
recovery is a future live gate, not synthetic acceptance transferred to the phone.
[Bounded checkpoint](releases/2026-10-27-android106-beta-0-canary-1.md).

**Accepted input CONTROL-PLANE-2 — DONE / PAID-AWARE EMPTY-COHORT BACKEND SERVING.**
Dependency: accepted CONTROL-PLANE-1 at21dd8d72ad5505cd82631856083694729d292c8b.
Gate: exact paid-aware bundle; read-only preflight; consistent private backup/recovery;
existing paid schema PRESENT_EMPTY, no repeat migration; guarded Friends restart;
unchanged non-cohort access;
read-only local bridge/continuous collection; synthetic production-identical expiry/
revoke/CRL/recovery. No real subscriptions/events, client/gateway changes or public console.
Current continuation from90ad148: typed D-Bus observer53 +existing ExecStart8 tests
PASS,9 private runner-flow tests PASS. Live empty/nonempty jobs readback confirmed.
Fresh20:09 preflight/PRESENT_EMPTY backupff9d0c50…/isolated restore PASS. Own drop-in,
effective full argv guard and one actual rollout restart PASS at20:10:09UTC.
New PID486622/NRestarts0 serves exact HTTPdcd76998…; three post-start observations
plus independent listener/health/inventory/empty-cohort readback PASS. Critical
registry/admission/publisher fingerprints unchanged. Consumed1 rollout/0 emergency;
no second candidate restart. Pre-start harness stop spent no restart; historical
receipts preserved. No migration, rebuild, real paid/client/gateway mutation.
Historical NEXT was CP2 rollout review; the owner has accepted it. Live paid
CRL/session/recovery acceptance remains open under the canary gate, not a CP2 retry.
Previous attempt evidence: exact publisher-preserving bundle6ea4ef3a…/source8b4177d unchanged;
fresh baseline/empty-schema/NTP gate and backup643fe650…/isolated restore PASS.
New ordered drop-in selected exact candidate; effective ExecStart guard PASS.
Subsequent pre-start observation raised JSONDecodeError; no restart requested.
Only own drop-in removed; independent final readback confirms original unit/PID,
healthy old runtime21d64558…, paid rows/events0 and unchanged non-cohort/publisher
fingerprints. That attempt consumed0/0; the owner now permits the continuation above.
8 guard tests rerun PASS,192 prior acceptance retained. Historical evidence
preserved, no migration/rebuild/client/gateway/real paid mutation. Live CRL/session
acceptance remains open. Stale Linux active blocks removed, no desktop task resumed.
[Exact evidence and finite next gate](releases/2026-10-27-android106-control-plane-2.md).

**Принятый вход CONTROL-PLANE-1 — DONE / LOCAL SYNTHETIC + PRODUCTION-READONLY.**
Dependency: accepted CONTROL-PLANE-0 at `a948d2328b5bd419b7d88be04b719c1dc6e16646`.
Gate: русский Admin/UI; 50 synthetic identities без изменения paid cap10/authority;
раздельный production-readonly inventory/fleet snapshots; technical telemetry models,
charts/filters/drill-down с явными unknown/stale boundaries; no production writes.
Gate met:95 PostgreSQL console +76 existing backend tests PASS, Chromium desktop/mobile
PASS. RU54 устройств наблюдались; NL registry недоступен; server stats read-only.
Client production telemetry/continuous alerts не собираются; production deployment,
real payments/enrollment NOT_RUN. Android106/backend/catalog unchanged.
[Checkpoint](releases/2026-10-27-android106-control-plane-1.md),
[runbook](../control_plane/README.md). Не новый PLAN root и не paid launch acceptance.

**Принятый вход CONTROL-PLANE-0: DONE / LOCAL SYNTHETIC ONLY.** Dependency —
accepted PAID-ENTITLEMENT-MVP at `ac90a2ac2f9e053b367bc3f7dde1711e94fd24a6`.
Django/PostgreSQL console, not a new product/PLAN root. Source of truth remains
Friends registry/paid_beta; no subscription ORM/state-machine duplication.
Completion gate: local Compose/PostgreSQL + customized Admin/dashboard/charts,
device lookup/readbacks, immutable intent/preview/confirm/reconcile, payment/cohort/
incident/audit/release metadata; actual synthetic backend integration, permission/
CSRF/concurrency/uncertainty tests and visual QA. Gate met:57 console+76 backend
PASS, desktop/mobile browser5 synthetic operations PASS. Production registry,
deployment, real payment/enrollment NOT_RUN; Android106/client/catalog unchanged.
[Checkpoint](releases/2026-10-27-android106-control-plane-0.md),
[local runbook](../control_plane/README.md). This is local implementation acceptance,
not approval of live billing or production console security.

Preparation и **PAID-ENTITLEMENT-MVP source checkpoint DONE** (originally NOT_DEPLOYED;
now CP2 DEPLOYED_EMPTY_COHORT);
controlled paid launch **BLOCKED** только на фактических Beta-0 gates в
[MVP report](releases/2026-10-27-android106-paid-entitlement-mvp.md).
Dependencies: exact accepted signed106/reference, owner-accepted
**ANDROID106-MESH-FIELD-1 PASS**, read-only canonical activation/admission lookup.
Положительный field result: real external user/whitelist network/ordinary app/MESH;
не Windows/Linux PASS. Desktop parity не prerequisite Android beta.

Exact106 APK manifest/signature/source inventory verified; one accepted hash,
unsigned106 builds не кандидаты.49 locked backend +20 JVM tests PASS; synthetic
vault/identity reload×3 не заменяет full installed APK upgrade и три запуска.
Новый authenticated106 READY ACK отделён от stale support84; production device
не менялся. Никаких Android source changes/rebuild/signing/publication автоматически.

Owner Beta-0 scope: максимум10 existing activated Friends devices, new106 installs
или already106, exact accepted APK без rebuild; older-version users исключены.
Private verified handoff, manual payments/operator events; external acquiring API
и older-version upgrade не Beta-0 prerequisites (не PASS). Новый top-level ID нет.

Bounded PAID-ENTITLEMENT-MVP: отдельные мигрируемые subscription/event tables,
atomic paid opt-in/cap10/idempotency, server effective state и private operator CLI
DONE. Non-cohort admission unchanged; paid state rechecked challenge/fetch,
certificate/readiness capped by entitlement/material expiry.243 targeted PASS,
10 nginx skips/8 external-integration deselections; no general CI claim. No live
migration/deployment/payment/cohort mutation, no Android source/APK/wire changes.
[Runbook](paid-beta.md) separates private receipts/operator attestation from remote
signer proof and documents existing-cache/CRL revocation bounds.

Completion gate: applicable14 launch rows under Beta-0 scope need exact evidence.
Remaining: review CP2 deployed-empty-cohort evidence and live paid CRL/session/
recovery acceptance (retained synthetic tests are not live acceptance); approved
private handoff/opt-in roster/operator, legal/subscription text, monitoring/stop
ownership. Source tests do not prove live paid enforcement. No pre-paid backend
rollback with nonempty cohort; saved105 does not authorize downgrade/uninstall/
reset. Public updater60/catalog unchanged; no launch or payment collection yet.

**Linux L04.2 PAUSED / NON-BLOCKING DESKTOP ENGINEERING, не DONE.**
R3 SOURCE GATE DONE/review accepted; .11 CONSTRUCTION DONE/frozen internal candidate,
exact0.2.12~l03.2.11/candidate570a5515…/system34b27cb9… read-only. Source/native/
system/reference/46 tests/embedded equality PASS; inner exit0, outer exit1 только
root-owned `embedded.json` collision. Installed package/live P0/P1/Auto NOT_RUN;
product defect не установлен, overall CI PASS нет. Collision — existing D02/CI
debt, не Android launch blocker. Linux installed acceptance только отдельным
потоком после controlled beta; не повторять harness, не переименовывать receipt,
не чинить launcher, не rebuild/install/rollback, не использовать retained identity,
не запускать P0/P1/Auto/AppImage lifecycle/L05/L06 и не публиковать Linux artifacts.

**STOP. NEXT — закрыть только фактические Android controlled-beta launch blockers.**
Следующий конечный этап — production read-only owner lookup/binding в BETA-0-CANARY-1,
не автоматически. CRL helper source gate завершён, пакет только unbound.
Live procedure не начинать до owner ГОТОВ.
Только OWNER_CANARY_1; customer payments/
enrollment не разрешены. Ни одного live canary stage пока не выполнено. CP2 принят,
бюджет consumed1 rollout/0 emergency; его deployment/migration/restart/gates не повторять.
Terminal scripts не запускать, paid schema не удалять. Read-only monitoring продолжается.
Новый top-level PLAN ID и CONTROL-PLANE-3 не создаются.

### Предыдущие priority/ops records — исторические, не активные NEXT

Ни один сохранённый ниже Linux NEXT не переопределяет owner decision27.10.

**Текущий bounded task — L04.2; R3 PARTIAL / PACKAGE_GATE_FAILED (environment harness finalization).**
R2 FINAL PARTIAL / READINESS_CAUSE_UNRESOLVED accepted; original typed fetch
cause was masked by expired cache. Live .10 Connect is prohibited. R3 adds no
new top-level ID. Required sequence: deterministic old-red → exact-error and
bounded-cooldown source correction → complete source gate → new matching system
and internal .11/package gates → one corrected P0; P1/Auto/lifecycle/AppImage only
after preceding PASS. First new affected/package/live failure stops progression.
Exact Go race/native15/combined3/MESH157/cleanup32/desktop1317+82skip PASS.
Source2d125137 review accepted in affected scope; runtime/tests/locks unchanged.
Gson and missing Go-cache failures reviewed as environment-only. Retained
Gradle171/classpath/JAR/javap PASS, no Gradle replay. Offline cache closure PASS;
one authorized Android/Python selection143 PASS. Bounded readiness workflow paths
committed e93bf7d; canonical run40491350035 SUCCESS. Raw full suite remains FAIL:55 FAIL/3373 PASS/105 SKIP/0 ERROR; no overall CI PASS.
Review normalization: common35 + local-only1 + fixture-absent19 = exact union55,
new/missing IDs relative to union0. ENVIRONMENT_FIXTURE_INPUT_ABSENT19 is existing
D02.1-R/CI debt, not a product regression. After separating it, exact accepted
local36 remains. Union55 is NOT a newly adopted permanent baseline. Full suite
will not be rerun; no historical capsules fabricated, tests suppressed or changed.
Source gate DONE/review accepted; continue new native/system, bounded reference
advancement and internal .11 package gates, then one corrected P0 only after PASS.
New native/system34b27cb9 construction/readback and reference gates PASS;
reference/candidate tests46 PASS. .11 candidate570a5515/system34b27cb9 built and sealed, source_dirty=false;
embedded candidate/system equality PASS/container exit0; launcher exit1 on
root-owned receipt overwrite (ENVIRONMENT_HARNESS_FINALIZATION). No product defect
established; no replay/harness patch. Remaining installed package/live gates
NOT_RUN. Containers removed; .10/.11/READY/protected seven byte-identical. R1/R2 primary/
cleanup/containment/drain semantics unchanged. Exact sealed .10 candidate remains
4264406722f6dd3efb83e9d9666e67180ce4f950333bb3e711bcbb4f5068b55a,
sourceb8e9196/system8ab7f298; Phase B/setup/GUI authorization retained.
No server/material/policy changes, manual fetch/cache deletion, owner-workstation
use, messages, voice acceptance, signing or publication. Relay probe correlation
gap is L06 observability debt, not a reason to expand RNS/public protocols here.
[Current R3 report](releases/2026-10-27-linux-readiness-cause-preservation-l04-2-r3.md).
L04 IN_PROGRESS; L05 NOT_RUN/delivery_unavailable backlog; L06/L07/L08 queued.
**STOP. NEXT — review L04.2-R3 package-harness finalization.**

**OWNER-CHAT-UX-2-INSTALL — PARTIAL / owner-use accepted.** По owner review exact
0.2.12~l03.2.9 установлен, candidate/package/system PASS, одно main window/embedded
chat, один ChatClient/D-Bus owner. Две unknown queue events исключены из acceptance
evidence, product defect не установлен. Не продолжать этот task; owner workstation
не использовался для L04.2, дополнительных messages/smiley/composer/visual checks нет.
Это не full L05 и не publication PASS.

[CHAT-UX-2](releases/2026-10-26-chat-ux-2.md) source/package DONE; .9/sourcecb81cd5/
candidate6f312d1e…/system43266d97… immutable. Прежние local3353 PASS/36 FAIL/101 SKIP/
1 FD teardown ERROR и CI full54/54/53 FAIL не скрыты; overall full-suite PASS нет.
CHAT-UX-1 product design superseded; historical evidence .7/.8 сохранено.

### Предыдущий compatibility checkpoint — не активный NEXT

**U2604-COMPAT — CHECKPOINT PASS в compatibility scope.**
LOCAL-OWNER-UPGRADE **BLOCKED на ABI**: Ubuntu26.04/Python3.14.4 не поддерживается
frozen .5/Python3.12. Workstation/launchers/private state unchanged.
Read-only source probe в disposable Ubuntu26.04.1/systemd259/Python3.14.4 **PASS**:
exact locks, RECORD630/strict imports17 distributions, platform libraries и129 tests.
Отдельный exact internal .7: candidate c79b4feb…/source3df82b4/system43266d97…;
packaging/runtime metadata/tests only. DEB/AppImage/imports/pkexec/READY, rollback,
tamper/locks/state, native/Auto/DIRECT и AWG/TCP prestart gates PASS.
Full desktop1199/83/0; full suite3257 PASS/55 FAIL/104 SKIP, без suppression;
отдельный technical debt, не общий CI PASS. Старые .5 hashes/IDs immutable.
[Report](releases/2026-10-26-linux-ubuntu2604-python314-compat.md).
L04.1 DONE сохраняется; L04 только L04.2. Publication/L04.2/L05/teardown/live VPN NOT_RUN.
Исторический STOP сохранён в U2604-COMPAT report; установленная .7 подтверждена выше.

### Frozen baseline — не текущая задача

**L04.1-LIVE-2 DONE / review accepted; L04.1 DONE в installed Linux AWG/TCP scope.**
Review принимает E/F1/F2; принятые P1/P2/A–D и клиентский F2 не повторять.
Exact **0.2.12~l03.2.5** frozen как **Linux AWG/TCP Beta candidate**, internal/unpublished;
candidate/source/system и artifact bytes неизменны. Signing/publication NOT_RUN.
Registry restart во время F2 — отдельное operational observation: первый readback
FAIL сохранён, uninterrupted continuity **NOT_PROVEN**, причина неизвестна,
assignment/configuration не изменились. Это не новый client defect или задача R3.
Parent **L04 IN_PROGRESS только из-за L04.2**. L04.2/L05/device teardown **NOT_RUN**.
Full-suite residual54/54/54 failures остаются отдельным техническим долгом; не общий CI PASS.
[Final installed report](releases/2026-10-25-linux-installed-awg-tcp-l04-1-final.md),
[единственный beta-freeze manifest](releases/2026-10-25-linux-awg-tcp-beta-freeze.json).
**STOP. NEXT — решение владельца о signing и ограниченной публикации Linux AWG/TCP Beta.**
Никакого автоматического L04.2/L05/teardown, F2 replay, R3, rebuild или публикации.

### Исторические checkpoints — не текущие статусы или NEXT

**L04.1-LIVE-2-R2 DONE / review accepted (source/package).**
Review exact .4: P1/P2/B1/B2/C1/C2/D PASS, E FAIL/review accepted, F1/F2 NOT_RUN.
Normal queued Connect/Close: deterministic overlay4 FAIL → targeted197 PASS.
Новый .5/source1c2beb6/candidate f0ee1760…: exact offline systemd255 DEB/AppImage
package/integrity PASS; system8d7d78ec… byte/contract verified unchanged, .4 immutable.
Full desktop1191/84; Linux/AWG/TCP/package CI PASS, isolated root→UID/Auto/DIRECT
и combined/lifetime PASS. Full CI54/54/54 failures: Docker readiness-receipt assertion
дополнительно к historical53, без исправления/повтора; общего CI PASS нет.
В самом R2 private identity/gateway/live E/F не использовались; последующий live
checkpoint указан выше. L04.1 IN_PROGRESS; L04.2/L05/teardown NOT_RUN.
[Source/package report](releases/2026-10-25-linux-queued-connect-close-l04-1-live-2-r2.md).

Цель — тот же Family Connect на Linux/Windows, что принятая Android beta106-recovery,
а не отдельные реализации продукта. [Текущий срез](STATUS.md) — источник текущего состояния.
Продуктовый checkpoint: phase22, source baseline `664342a6566792a4ea621274a369bcd6b6012143`.
D00 — организация документации; следующие строки являются очередью, не разрешением на автозапуск.
L03.1/L03.2 **DONE (review accepted)**; parent **L03 DONE** в scope полного
внутреннего Linux-кандидата. Исторически **L04.1-LIVE-2: PARTIAL / review accepted**, STOP на B1.
**L04.1-LIVE-2-RESUME PARTIAL / review accepted**, тот же ID; STOP на первом новом дефекте E.
P1/P2 continuity, B2, C1/C2 unavailable и D channel-loss/recovery PASS.
Queued Connect не отменяется при Close: busy/open, Future queued; helper/TUN0,
generation0/null. Только безопасный fixture cleanup; F1/F2 NOT_RUN.
Exact .4 A/B1 review accepted, не повторялись. Три stable pre-action reads,
структурный firewall/readback/state PASS; KVM/secret copies уничтожены.
Product/candidate и original FC-3YSQ-BE2D/nl сохранены. Review E принят;
R2 correction принят; текущий installed итог и единственный NEXT указаны выше.
L04.1 IN_PROGRESS, L04.2/L05/teardown NOT_RUN.
**L04.1-LIVE-2-R1 DONE / review accepted (source/system/package).**
Final internal0.2.12~l03.2.4/source053c4e5/candidate42ea0699…/system8d7d78ec…,
authorization2; .3 — immutable intermediate. Actual AWG/TCP up1/start0,
IDLE/generation2/pending null/poll PASS; unknown outcome fail-closed, первая
diagnostic category сохраняется через recovery. Exact system/package/rollback/
coherence/actual old-build refusal PASS; desktop1195/96. Linux/AWG/TCP/package CI
PASS; native/DIRECT initial FAIL, один unchanged rerun PASS (оба receipt сохранены).
Full CI54/54/53 failures, общего CI PASS нет. В самом R1 live B1/B2–F NOT_RUN;
private state/gateway не тронуты; последующий installed RESUME указан выше.
LIVE-1 PARTIAL принят review; final-2 retired для завершения L04.1, прежние PASS
сохраняются только за этим exact build. Red actual backend/GTK race подтверждён;
generation-fenced unlocked poll и queued Disconnect cancellation: адресные229 PASS.
Source57f8eff, internal0.2.12~l03.2.2/candidate d9c0d07f…; unchanged build-9.
Desktop1121 PASS/85 SKIP, integrity и оба systemd255/pkexec package gates PASS;
Client Linux/AWG/TCP/native/root→UID/Auto/DIRECT/package CI PASS;
control/phase0/Docker54/54/53 failures и voice FAILURE сохранены.
L04.1-LIVE-1-R **DONE / review accepted** в source/package scope.
[Correction report](releases/2026-10-25-linux-poll-disconnect-l04-1-live-1-r.md).
Новый exact candidate установлен в новой KVM Ubuntu24.04/systemd255:
DEB/setup/AWG/TCP/HTTPS/64KiB↓/↑/single Disconnect PASS. Original AppImage
close/reopen → один Disconnect PASS; поздние polls25s не возвращают CONNECTED.
Review принимает fresh nonce DNS на actual TUN с matching request/reply после flush:
валидный terminal positive/NXDOMAIN/NODATA contract, не только exit0.
RETEST **DONE / review accepted**, positive installed AWG/TCP gate завершён.
Network/DNS/IP cleanup и state preservation PASS; предыдущий guest уничтожен.
[RETEST evidence](releases/2026-10-25-linux-installed-awg-tcp-l04-1-retest.md).
AUTH/PROVISION **DONE, review accepted**; существующая FC-3YSQ-BE2D/nl, без новых
identity/invite/assignment. Parents **L04/L04.1 IN_PROGRESS**; LIVE-2 PARTIAL, L04.2 NOT_RUN.
Exact final-2 source `cf66532`, candidate `9d4b13cc…`, AppImage/DEB0.2.12~l03.2.1
не пересобраны: real KVM Ubuntu24.04/systemd255, DEB/pkexec/READY, AWG×3/TCP×1,
DNS/HTTPS/transfers, handoff/cleanup PASS. AppImage AWG/traffic/single-owner PASS;
после confirmed GUI close/reopen Disconnect отказал на connection-operation lock.
Это first-failure STOP, не полный LIVE-1 PASS. Cleanup-only после освобождения lock
восстановил baseline; guest уничтожен, исходный state/cache/floors/receipt сохранены.
[Отчёт LIVE-1](releases/2026-10-25-linux-installed-awg-tcp-l04-1-live-1.md).
LIVE-2: A actual installed tamper/reinstall PASS; B1 root lock не допускает transport,
но helper up1 и pending/APPLYING остаются после освобождения lock (generation0→1).
Network/state сохранены; pending не очищен вручную, guest уничтожен. B2–F NOT_RUN
по first-failure STOP. Никакого rebuild/source fix; [отчёт](releases/2026-10-25-linux-installed-awg-tcp-l04-1-live-2.md).
Исторический first-failure STOP; continuation exact .4 принимает P1/P2/B1/B2/C1/C2/D.
E FAIL/review accepted; F1/F2 и device teardown NOT_RUN. NEXT только review R2.
**L01/L01-R review принят в Linux source/native/root→UID/isolated-kernel scope. Review L02.2 принят: локальный критерий L02 authenticated OFF→ON→OFF через Manual и Auto/MESH выполнен. L02.1-R atomic RetainChat/terminal recovery и L02.1-R2 status classification приняты. D01.3/D01.3-R приняты в public completion/admission scope. L03.1/L03.2 и parent L03 приняты; correction L04.1-LIVE-1-R и RETEST приняты, NEXT только review LIVE-2-R2. Review D03/D04/D05, D02.1 collection/import isolation и D02.2 public-reference принят.
Review D02.1-R и fleet-документации `1725656` принят;
D02.1-R остаётся PARTIAL/NOT_RUN; D01 открыт. Дальнейшие L04.2/L05 и Windows задачи не начинаются.**

Порядок по умолчанию: D01.1 → D01.2 → D02.1 / принятый review D02.1-R → D02.2 / review → D03 → D04 → D05 → Linux → Windows → R01.
Зависимости в таблицах — необходимые результаты, а не требование заново выполнять завершённые фазы.
Каждый ID — отдельный ограниченный пользовательский результат, отдельные проверки и commit/push.
`DONE` = выполнен указанный критерий, `NEXT` = ещё не начат, `QUEUED` = не начат как отдельная задача.
Это не означает отсутствия всего кода в QUEUED: существующие части переиспользуются и проверяются.
Отсутствие физической ОС не закрывает её gate и не блокирует доступную другую ОС;
фиксировать точный NOT_RUN и короткую инструкцию, согласовывая следующий ограниченный шаг.

## Подготовка и известный дефект

| ID | Результат | Зависимость | Статус | Критерий завершения |
|---|---|---|---|---|
| ANDROID-CONTROLLED-BETA | Controlled paid Android beta readiness | exact signed106/reference; owner FIELD-1 PASS; canonical read-only lookup | PREPARATION DONE / LAUNCH BLOCKED | [14 launch gates](releases/2026-10-27-android106-controlled-beta-readiness.md): full in-place preservation/three launches, paid state/payment/expiry, delivery/recovery, legal/opt-in cohort/monitoring/stop evidence.49 backend +20 JVM PASS bounded; not full upgrade or paid-launch PASS. No desktop/full-green-CI dependency; no automatic source edits/deployment. |
| CHAT-UX-1 | Первый продуктовый desktop messenger UX checkpoint | explicit owner request; installed Ubuntu26.04 .7; штатный prepare-chat | IMPLEMENTED / REVIEW; validation PARTIAL | [Report](releases/2026-10-26-chat-ux-1.md). Одно GTK окно/ChatClient, adaptive dialogs/bubbles, fixed4096-byte composer/native emoji, bounded onboarding; backend unchanged. GTK27, desktop1226, exact package/AWG/TCP/integrity/12 screenshots PASS; mandatory full57 FAIL unsuppressed, no overall acceptance PASS. Built .8 sourceb094595/candidate0bf09cee…, system43266d97… unchanged; owner install/publication/L04.2/full L05 NOT_RUN. STOP for review. |
| U2604-COMPAT | Отдельный Ubuntu26.04/CPython3.14 source/system/package candidate | exact lock compatibility probe; explicit owner request; frozen .5 immutable | CHECKPOINT PASS (compatibility scope; review pending) | [Report](releases/2026-10-26-linux-ubuntu2604-python314-compat.md). Exact .7 candidate c79b4feb…/system43266d97…, manifests [3,14], imports/DEB/AppImage/pkexec/READY/rollback/tamper/barriers/state PASS. Full suites executed unsuppressed: local3257/55/104; general CI not PASS, residual debt retained. No workstation/private identity/gateway/live VPN. STOP for review. |
| LOCAL-OWNER-UPGRADE | Установка совместимого candidate на workstation владельца | отдельный review U2604-COMPAT и разрешение владельца | Исторический ABI blocker .5; установленная .7 теперь read-only verified | CHAT-UX-1 подтверждает только installed .7 manifest/dpkg и owner context prepare-chat, не воспроизводит acceptance/upgrade. Новая .8 владельцу NOT_RUN; сначала review CHAT-UX-1. Остальные installed checks не объявлены выполненными и не запускаются автоматически. |
| D00 | Компактное состояние и последовательный план | phase22 / baseline | DONE | Новый сеанс читает STATUS + выбранный ID; история сохранена побайтно, ссылки и diff проверены; commit/push с remote SHA отражён в итоговом ответе. |
| D01 | Зависимости Linux/desktop CI | D00 | IN_PROGRESS | Dependency gates D01.1/D01.2 отдельно от общей CI-приёмки; закрытие требует полного PASS обязательных suites после устранения остаточных blockers, без скрытия тестов. |
| D01.1 | Client builds/linux, AmneziaWG pilot, TCP pilot | D00 | PARTIAL | Dependency gates `26f71d6` приняты review; реальные Python3.12 imports/адресные CI PASS. Полный desktop FAIL: RNS capsule, AWG Auto lifecycle assertion; PARTIAL сохранён. |
| D01.2 | Linux control, phase0, Dockerfile.control test-stage | принята dependency-часть D01.1 | PARTIAL | На pushed `07b52e3` Python3.13 imports/адресные gates PASS ×3; Docker root 22 passed. Каждый full suite: 9 owner_handoff/prepare collection errors, exit 2 (D02); обязательные gates сохранены. |
| D01.3 | Public chat probe/prepare completion и следующий admission | L02.2/local L02 review принят; D03/D04/D05, L01/L01-R сохранены | DONE (review D01.3-R accepted; public completion/admission) | [Отчёт](releases/2026-10-24-desktop-chat-admission-d01-3.md): actual Host/ServiceHost/ChatBridge и Unix IPC, event-barrier red2/green; EOF после cleanup сериализован с admission, bounded client wait без open/HTTP retry. Public4/native caps и drain/accounting сохранены. 266 адресных + финальные24, прежние15/combined3/root→UID PASS. Production `23e3c5513ab9c37e919f228066c0e23f733a997e`: Client Linux и isolated gates PASS. Финальный test source `f258c17007102634fead9894bcfe9a82f6db44cf`: mandatory desktop pytest 40132223364/120986275264 PASS; общий D01 открыт. |
| D01.3-R | DIRECT close/active removal под admission lock | D01.3 accepted subset; без переработки native | DONE (review accepted; bounded scope) | [Отчёт](releases/2026-10-24-desktop-chat-direct-completion-d01-3-r.md): actual DirectHost/DirectBridge/Authority и Unix IPC, post-close/EOF barrier; red1/green30, зависимые326/root→UID13 PASS. Production `050f06baef8b94e81d1bd4becb7f4fc38d1a6744`; final barrier5 PASS/red1 на old-host overlay. Final source `b910edbd108fc5e146792b6db966d6f8daf53b1a`: mandatory Client Linux desktop pytest и весь linux job40134155274/120992056110 PASS; isolated-linux15/combined3/root→UID/Auto/DIRECT/race PASS. Full suites54 failures отдельно, не общий CI PASS. Review принят; разрешён только L03.1. |
| D02 | Сбор и импорты исследовательских fixtures | dependency-части D01.1/D01.2 приняты | IN_PROGRESS | Review D02.1 collection/import isolation и D02.2 принят; зависимости D03 готовы. D02.1-R PARTIAL/NOT_RUN. Не ждёт полного зелёного CI, который сам должен разблокировать; общая CI-приёмка D01 остаётся отдельным gate. |
| D02.1 | Девять collection errors, историческая overlay-suite, изоляция импортов | окружения D01.1/D01.2 готовы | DONE (collection/import isolation) | Review подтвердил границы; `6a0a982`: clean collection 2996/0 errors, helpers/import/runner 75 PASS; три CI full suites с 56 residual failures. Историческая воспроизводимость отдельно в D02.1-R. |
| D02.1-R | Комплектность исторического runner | review D02.1 | PARTIAL | Коррекция принята review. Vector/original API, явные retained inputs, preflight до pytest; 110 адресных PASS. Historical suite NOT_RUN: нет anchored pins delivery-check, Java runtime/classes и 3 JARs; полный replay не обеспечен и в D02.2 не выполняется. R3 review:19 historical capsule-input FileNotFoundError IDs classified ENVIRONMENT_FIXTURE_INPUT_ABSENT before product assertions; existing CI debt, not a new permanent union55 baseline. |
| D02.2 | RNS/reference checks без локальной capsule в обычном CI | review коррекции D02.1-R принят | DONE (review accepted) | [Evidence `da8670e`](releases/2026-10-24-rns-reference-d02-2.md): public mappings, прежние pins, APK/inventory linkage, строгий --capsule. Clean export: 49 passed/1 прежний skip, collection 3051/0 errors; real capsule 2073 PASS. CI control/phase0/Docker: 55/54/54 residual failures, 0 errors; полные команды сохранены. |
| D03 | Окончательные ошибки ChatHTTP | приняты D02.1 collection/import isolation и D02.2 | DONE (review accepted) | [Evidence `290d430`](releases/2026-10-24-chat-http-terminal-d03.md): до 15 failed/18 passed, после 33 passed; зависимые 63+24 passed. Terminal-причина сохранена при cleanup, полный 200/consumer error без повторов, transient fallback сохранён. CI control/phase0/Docker: 54/54/53 residual failures, 0 errors; общий D01 открыт. |
| D04 | Auto stop/start lifecycle | приняты D03, D02.1 collection/import isolation и D02.2 | DONE (review accepted) | [Evidence `b41e1ad`](releases/2026-10-24-auto-lifecycle-d04.md): прежний Controller 8 failed/1 passed; service 55 PASS, зависимые 180 PASS/6 прежних skips. Публикация завершения owner и admission согласованы, fatal не сбрасывается; callback/process close до передачи владения. Linux desktop/Auto bridge CI PASS; одинаковые 54 residual failures в control/phase0/Docker. Docs-only `3f9854a` phase0 FAILURE отдельно. |
| D05 | Минимальная внутренняя модель выбора/назначения/активной сессии и граница существующего provider | review D03/D04 принят | DONE (local Linux boundary; review accepted) | [Evidence `c53265d`](releases/2026-10-24-desktop-provider-d05.md): модель используется NormalOwner/Platform/GuardedHost; 162 provider/model/native + 213 ownership/service/chat PASS. [Критерии](desktop-architecture.md#desktop-fleet-acceptance): stable ID 2×NL+DE, refresh без apply, fencing, signed legacy rejection, безопасные metadata. Linux Auto CI PASS; общий CI остаётся красным. Не Windows-интеграция/production fleet/F-01. |

<a id="ci-evidence"></a>
### D01/D02: наблюдавшиеся ошибки после baseline push

**PACKAGE_HARNESS_EMBEDDED_RECEIPT_FILENAME_COLLISION — OPEN technical debt.**
R3 inner `embedded.json` root-owned receipt уже содержит PASS/container exit0;
outer summary пытается перезаписать тот же path и получает PermissionError/exit1.
Product defect не установлен. Future correction: разные filenames для inner и
outer либо outer summary в отдельном user-owned evidence directory. В этом
checkpoint нет rename/repair/replay; не launch blocker Android. L04.2 PAUSED.

Эти ссылки — исходные наблюдения, не CI-проверки D00 и не автоматическое заключение
о причине каждого job. Разделить dependency/collection и fixture-import failures по фактическим logs.
1218 PASS phase22 относятся только к описанному локальному набору, не ко всему CI.

- [Client builds / Linux](https://github.com/Joker20380/family_connect/actions/runs/40073089239/job/120810560761).
- [AWG](https://github.com/Joker20380/family_connect/actions/runs/40073089248/job/120810560564).
- [TCP](https://github.com/Joker20380/family_connect/actions/runs/40073089297/job/120810560697).
- [Linux control](https://github.com/Joker20380/family_connect/actions/runs/40073089380/job/120810561183).
- [phase0](https://github.com/Joker20380/family_connect/actions/runs/40073089270).

D01.1: [итог PARTIAL, точные failures и CI](releases/2026-10-24-desktop-ci-d01-1.md).
D01.2: [окружение и evidence](releases/2026-10-24-control-ci-d01-2.md).
D02.1: [границы collection/imports и evidence](releases/2026-10-24-fixture-boundaries-d02-1.md).
D02.1-R: [комплектность runner и незакрытые pins](releases/2026-10-24-historical-runner-d02-1-r.md).
D02.2: [public RNS/reference и полный capsule gate](releases/2026-10-24-rns-reference-d02-2.md).
D01 сначала читает соответствующие workflows/lockfiles и эти ошибки; не переносит
лабораторный каталог целиком и не отключает обязательные suites ради зелёного CI.
D02 явно отделяет поддерживаемые проверки от архивных опытов; их source push не делает их release core.

<a id="d03"></a>
### D03: точка воспроизведения и требуемое сохранение ошибки

[provisioning/chat_bridge.py](../provisioning/chat_bridge.py), `ChatHTTP.stream`;
[tests/test_chat_bridge_http.py](../tests/test_chat_bridge_http.py).
[Детерминированное воспроизведение и исправление](releases/2026-10-24-chat-http-terminal-d03.md):
фактические ChatHTTP/FriendsClient, независимо управляемые read/close и clock без sleeps.
До исправления 15 failures, включая HTTP400/401/403/409 → ошибочный fallback;
после — первая terminal-причина сохранена независимо от cause cleanup, close выполняется.
Полный 200 и исключение потребителя после единственного yield не повторяют запрос.
Transient ConnectError/ReadTimeout/503, partial-read fallback и BridgeError mapping сохранены.
Это synthetic transport, не installed/live/protected DIRECT/service-only acceptance.
Review D03 принят; открытый historical replay D02.1-R не выдаётся за завершённый.

### D04: детерминированное завершение владельца

`clients/linux/auto_service.py`: Events на настоящем Controller воспроизвели ранний
DISCONNECTED, отказ start после завершённого потока и гонку повторного stop.
Теперь reap завершённого owner, публикация состояния и start/status/stop согласованы
одним lock; живой owner не обнуляется, FAILED/fatal не разрешает start.
Revocation до cleanup, retry записи journal без повторного cleanup, shutdown retain intent,
старые generation и поздний CONNECTED покрыты адресно. Реальный Coordinator завершает
terminal callback и process close до Runtime.dispose/передачи владения; native process
в этом тесте синтетический. [До/после и ограничения](releases/2026-10-24-auto-lifecycle-d04.md).
Связь с конкретным прошлым CI assertion из D01.1 не доказана; review D04 принят.

<a id="d05"></a>
### D05: локальная подготовка к расширяемому парку, не fleet-приёмка

[Основной контракт](desktop-architecture.md#desktop-fleet-boundary) — **минимальная Linux-граница реализована;
review D05 принят**. После принятых D03/D04, без зависимости от production fleet,
новых VPS или F-01 live. D05 задаёт общую модель/provider boundary; W01/W02 используют
её при продуктовой Windows-интеграции, обратной зависимости D05 → W01/W02 нет.
Модельные/отрицательные проверки выполняются адресно в D05; миграция — L08/W12,
полная установленная приёмка — L04/W11/R01. UI/model fixture не доверенный assignment.
L01/L02/W04 не расширяются за пределы fixed chat DIRECT/service-only.
Адресные model/provider/native проверки D05 выполнены; F-01/installed/live NOT_RUN.
Это не закрывает D01/D02 и не разрешает автоматически начинать Linux/Windows-интеграцию.

## Linux: интеграция, полный кандидат, затем установленная приёмка

| ID | Результат | Зависимость | Статус | Критерий завершения |
|---|---|---|---|---|
| L01 | Защищённый DIRECT для чатов | D03, D04; D05 review принят | DONE (review L01-R accepted) | Linux source/native/root→UID/isolated-kernel, не installed/live. [Исходное evidence](releases/2026-10-24-linux-chat-direct-l01.md) и [коррекция](releases/2026-10-24-linux-chat-direct-l01-r.md) сохранены с точными SHA; runtime umask, provenance и real TLS fatal исправлены и приняты. |
| L01-R | Исправления review protected Linux chat DIRECT | L01 review; принятые D03/D04/D05 | DONE (review accepted) | [Before/after и точные CI jobs](releases/2026-10-24-linux-chat-direct-l01-r.md): unit umask0077 + настоящий UID, DIRECT→EXIT registration→ProtectedMailbox→DIRECT с expiry/metadata, real TCP/TLS fatal без fallback. 145 + 49 Python/native, 6 root/UID, Go/race и оба isolated kernel gates PASS. Source `4fab7b6`: Client Linux/Auto/root→UID/kernel/AWG/TCP/voice CI PASS, control/phase0/Docker FAIL. Ни установка, ни live, ни закрытие D01/D02.1-R. |
| L02 | MESH service-only и передача владения | L01 (принят) | DONE (local source/native, review accepted) | [Начальный checkpoint](releases/2026-10-24-linux-chat-mesh-l02.md), source `383ef3606aaa4dbd29f0c7c0f755e6faec6e309f`, был PARTIAL. [L02.2](releases/2026-10-24-linux-chat-mesh-l02-2.md), source `dac0f6b45be6ed8703d3de93ff5fdbc67462eabe`, выполнил исходный authenticated API/mailbox OFF→ON/publication→EXISTING_EXIT→OFF через реальные Manual/Auto owners, drain/expiry/cancel/late results. Не installed/live/F-01; full-suite D01 остаётся открыт. |
| L02.1 | Lifetime поколения и комбинированная native/process приёмка | L02 partial; L01/L01-R, D03/D04/D05 приняты | HISTORICAL PARTIAL (completed by R/R2/L02.2) | [Отчёт](releases/2026-10-24-linux-chat-mesh-l02-1.md): bounded generation lease и typed-nil IPC исправлены; red/green на actual native owner, authenticated service-only/API/duplex-byte-mailbox/cleanup. На том checkpoint полный VPN publication→EXISTING_EXIT→OFF был NOT_RUN: отсутствовали generic packet/DNS/TUN health и broker lease lifecycle. Этот оставшийся gate выполнен отдельно в L02.2, не приписывается старому evidence. |
| L02.1-R | Terminal native generation: fencing и recovery | L02.1; L01/L01-R, D03/D04/D05 сохранены | REVIEW ACCEPTED (bounded scope) | [Отчёт](releases/2026-10-24-linux-chat-mesh-l02-1-r.md): peer/Mux failure и async bootstrap failure red/green на actual native owner; atomic generation pin закрывает acquire/use race; late HTTP/acquire, held/sticky cleanup, concurrent demand/VPN reservation проверены. Review RetainChat и terminal fixes принят; status-result correction выделена в L02.1-R2. На том checkpoint combined gate ещё был открыт; его завершение — отдельное evidence L02.2. |
| L02.1-R2 | Классификация native status и сохранение typed errors | L02.1-R review принят | REVIEW ACCEPTED (bounded scope) | [Отчёт](releases/2026-10-24-linux-chat-mesh-l02-1-r2.md): actual CONTROL4 contention и malformed IPC red/green. BUSY не отменяет healthy generation; DENIED до ChatBridge/ChatHTTP без replay. Atomic pin/refcount/cleanup/caps сохранены; прежние15 authenticated остаются обязательными. |
| L02.2 | Комбинированная local authenticated MESH OFF→ON→OFF приёмка | L02 partial; L02.1-R2 принят | DONE (review accepted, local source/native) | [Отчёт](releases/2026-10-24-linux-chat-mesh-l02-2.md): manual Supervisor и Auto/MESH отдельно; реальные UID IPC/native owner, TUN/private DNS/readback/health/publication, EXISTING_EXIT и новый SERVICE_ONLY; API/duplex byte-mailbox на каждом участке. Broker bind/renewal, lease/open/resource accounting, held cleanup/late result/profile mismatch/expiry/revocation/DENIED-no-replay; release CONTROL4 и packet RX fence приняты. Bounded CI gate сохраняет прежние15 и обязательные suites. Не live/installed/LXMF/F-01; исходный локальный L02 выполнен. |
| L03 | Полный внутренний Linux-кандидат | L02, D05, D01.3; L03.1 + L03.2 | DONE (review accepted; internal candidate scope) | Согласованы GUI, пользовательские службы, root-helper, native/RNS, зависимости и установка; capabilities соответствуют точному составу реально интегрированного пакета. Exact final-2 AppImage/DEB L03.2 проверены, review принят. Это не installed live acceptance L04/L05 и не public release. |
| L03.1 | Согласованный system/runtime payload, безопасная установка и ограниченный chat setup | принятые L01/L01-R, local L02/L02.2, D03/D04/D05, D01.3/D01.3-R | DONE (review accepted; exact build-9) | [Отчёт](releases/2026-10-25-linux-system-runtime-l03-1.md): полный hash/member/import closure, native/RNS/anchor; install exclusion/rollback и точные capabilities; fixed UID setup без VPN. Build-9,758 files;94 финальных адресных (umask077), desktop1120/24; actual disposable systemd255 install/polkit/UID/rollback/capability smoke PASS, private network/D-Bus/resolver. Source f826dbd: Client Linux и isolated native/root→UID/Auto/DIRECT CI PASS; rollback re-mask/start refusal PASS. Control/phase0/Docker по54 failures/errors0; voice observation сохранён, не общий CI PASS. Собственный system-only gate не равен L04/L05 PASS; review принят, включение в полный кандидат завершено в L03.2. |
| L03.2 | Включение принятого состава в AppImage/DEB | review L03.1 принят | DONE (review accepted; exact final-2) | Sourcecf66532, candidate9d4b13cc…, внутренние0.2.12~l03.2.1 AppImage/DEB с exact build-9; inventory/import/реальные polkit/setup/background/removal и rollback/barrier PASS в disposable Ubuntu24.04/systemd255. Desktop1146/24, адресные62 PASS; Client Linux/isolated native и final package CI40184803906 PASS. CI rebuildf7f6e765… не заменяет final-2. Full suites по54 failures отдельно. [Evidence](releases/2026-10-25-linux-candidate-l03-2.md). Legacy six-file/updater сохранён; не L04/L05 PASS. |
| L04 | Установленный Linux VPN | L03; L04.1 + L04.2 | PAUSED / NON-BLOCKING DESKTOP ENGINEERING | L04.1 DONE; L04.2 paused by owner27.10, not DONE. R3 source gate accepted, .11 construction frozen; installed MESH/Auto gates remain open in a separate stream after controlled beta. Not an Android launch prerequisite; no automatic retry, install or publication. |
| L04.1 | Установленная приёмка exact Linux candidate: AWG/TCP | review L03/AUTH/PROVISION/LIVE-1-R/RETEST/R2 и final LIVE-2 принят | DONE (review accepted; installed Linux AWG/TCP) | [RETEST](releases/2026-10-25-linux-installed-awg-tcp-l04-1-retest.md) и [final E/F1/F2](releases/2026-10-25-linux-installed-awg-tcp-l04-1-final.md) accepted. Exact .5 frozen/internal/unpublished. Registry restart — отдельное ops observation, continuity NOT_PROVEN/cause unknown; assignment/configuration unchanged. F2 не повторять; R3 не создавать. |
| L04.1-AUTH | Одна отдельная test identity/activation | explicit owner authorization25.10; fbb1732 accepted; L04.1-AUTH-PROVISION | DONE (review accepted) | [Activation](releases/2026-10-25-linux-test-activation-l04-1-auth.md) и [provisioning](releases/2026-10-25-linux-test-provisioning-l04-1-auth.md): одна FC-3YSQ-BE2D; registry/replay/resume и verified nl AWG/TCP assignment PASS. Outside-checkout state UID1000/0700/0600, private teardown receipt. Issuance не повторять; последующий guest-only handoff проверен в LIVE-1, original state сохранён. |
| L04.1-AUTH-PROVISION | Один штатный per-device nl assignment | accepted AUTH identity/activation subset; explicit owner authorization25.10 | DONE (review accepted) | Один FriendsOwner.configuration("nl") из exact final-2 Python3.12/vendor, без driver/retry: один AWG row/live peer и один persisted/runtime Xray user; чужие bindings и global settings сохранены. Signature/device/cache/floor/readback PASS, apply в этом checkpoint NOT_RUN. [Evidence и ограничения](releases/2026-10-25-linux-test-provisioning-l04-1-auth.md). Не повторять provisioning отдельно от разрешённого product connect. |
| L04.1-LIVE-1 | Положительная installed AWG/TCP приёмка exact final-2 | accepted AUTH/PROVISION; isolated Ubuntu24.04/systemd255 | PARTIAL (review accepted; historical final-2) | [Evidence](releases/2026-10-25-linux-installed-awg-tcp-l04-1-live-1.md): DEB/setup/READY, AWG×3/TCP×1 и transfers/cleanup PASS. Original AppImage AWG/traffic, second launch/confirmed GUI close сохраняют single owner; после reopen Disconnect отказал «Connection settings are being updated». Cleanup-only GUI Disconnect после освобождения lock PASS. Final-2 не изменён, больше не кандидат для завершения L04.1; PASS не переносится на новый build. |
| L04.1-LIVE-1-R | Poll/Disconnect race correction и новый internal candidate | LIVE-1 PARTIAL accepted; source/package only | DONE (review accepted; source/package scope) | [Report](releases/2026-10-25-linux-poll-disconnect-l04-1-live-1-r.md): deterministic red/green, generation fencing, pending/foreign fail-closed, stale callback/queued close. Source57f8eff, internal0.2.12~l03.2.2/d9c0d07f…; build-9 unchanged, exact pair integrity/real package gates PASS. Linux/AWG/TCP/native/package CI PASS; full suites54/54/53 failures, voice FAILURE. Live приёмка не входит в принятие source/package correction. |
| L04.1-LIVE-1-RETEST | Короткая installed приёмка exact corrected candidate | accepted LIVE-1-R; существующая FC-3YSQ-BE2D/nl; новая KVM | DONE (review accepted) | [Report](releases/2026-10-25-linux-installed-awg-tcp-l04-1-retest.md): exact DEB/setup/READY, AWG/TCP/HTTPS/64KiB↓/↑, single Disconnect и AppImage close/reopen PASS. Review принимает matching fresh-DNS request/reply с valid terminal NODATA. Cleanup/state PASS; positive gate не повторять. |
| L04.1-LIVE-2 | Bounded negative installed AWG/TCP gates | accepted RETEST/R1/R2; final owner review | DONE (review accepted; installed Linux AWG/TCP) | [Final receipt](releases/2026-10-25-linux-installed-awg-tcp-l04-1-final.md): .4 P1/P2/A–D accepted, not repeated; exact .5 E/F1/F2 accepted. F2 original AppImage local PASS; first registry readback failure retained as separate operational observation, uninterrupted continuity NOT_PROVEN, cause unknown, assignment/configuration unchanged. No replay/R3/source change. STOP → owner signing/limited-publication decision. |
| L04.1-LIVE-2-R1 | Terminal pre-start refusal / unknown outcome; новый system/user candidate | review LIVE-2 PARTIAL accepted; source/package only | DONE (review accepted; source/system/package) | [Report](releases/2026-10-25-linux-prestart-journal-l04-1-live-2-r1.md): actual AWG/TCP red→green, same-owner terminalization/recovery, generation fencing; final .4/source053c4e5/candidate42ea0699…/system8d7d78ec…. Exact systemd/polkit/import/rollback, DEB/AppImage/coherence и actual old-build refusal PASS. Full CI не зелёный; live B1 retest/B2–F отдельно. |
| L04.1-LIVE-2-RESUME | Installed negative acceptance exact .4, continuation | A/B1 review PASS; existing test identity/nl; fresh KVM | PARTIAL (STOP E; review accepted) | [Continuation](releases/2026-10-25-linux-installed-awg-tcp-l04-1-live-2-continuation.md). P1/P2/B1/B2/C1/C2/D PASS on exact .4. E FAIL: queued Future/busy/open/CONNECTING; no late VPN start proven, helper/TUN0/generation0/null. Fixture cancels before worker release; F1/F2 NOT_RUN. Source/candidate unchanged; L04.2/L05/teardown NOT_RUN. |
| L04.1-LIVE-2-R2 | Normal queued Connect/Close ownership; new internal .5 | LIVE-2 PARTIAL/review accepted, E defect; source/package only | DONE (review accepted; source/package) | [Report](releases/2026-10-25-linux-queued-connect-close-l04-1-live-2-r2.md): source1c2beb6/candidate f0ee1760…, unchanged verified system8d7d78ec…. Red4/targeted197/full1191 PASS; normal mutation Future/revision fence, running/done-undelivered blocks Close. Exact .5 package/integrity and Linux/AWG/TCP/package CI PASS; local isolated gates PASS. Full CI54/54/54 failures retained, no overall PASS. R2 used no private state/gateway/live E/F; later LIVE-2 result above. |
| L04.1-AUTH-TEARDOWN | Обязательная очистка отдельного test device | после L04/L05 или завершения test campaign; отдельное разрешение/review | QUEUED / NOT_RUN | Device-scoped gateway cleanup → readback отсутствия только test peer/user при сохранении чужих ресурсов → registry revoke. Private receipt содержит exact binding hashes/row/address/read-only checks и дополнен L04.2 test chat/store/keyring, certificate issuance/expiry и registration. Revoke/teardown не выполнялись. Штатного unregister сейчас нет; не восстанавливать целиком старые DB/server.json и не начинать cleanup автоматически. |
| L04.2 | Installed Linux MESH/Auto | L04.1; accepted R3 source gate; separate future owner authorization | PAUSED / NON-BLOCKING DESKTOP ENGINEERING | SOURCE GATE DONE/review accepted; .11 CONSTRUCTION DONE/frozen internal candidate570a5515/system34b27cb9.46 tests/embedded equality PASS, inner exit0; outer exit1 only receipt collision, existing D02/CI debt. No established product defect; installed package/live P0/P1/Auto NOT_RUN, not L04.2 DONE or overall CI PASS. No harness/launcher/rebuild/install/rollback/identity/lifecycle/L05/L06/publication. [Owner decision](releases/2026-10-27-android106-controlled-beta-readiness.md), [historical R3 evidence](releases/2026-10-27-linux-readiness-cause-preservation-l04-2-r3.md). |
| L05 | Установленный Linux-мессенджер | L03, L04 | QUEUED / NOT_RUN | DIRECT/MESH-доставка без VPN и с VPN, контакты/текст/голос, история и фоновые события — completion gate на реальных компонентах. Backlog: L04.2 observation registration_error=delivery_unavailable; причина не локализована, client defect/gateway outage не заявлены. Исключён из L04.2 core prerequisites final review-решением; диагностика/repair здесь NOT_RUN. Вне Linux AWG/TCP Beta scope; автоматически не начинать. |
| L06 | Linux recovery | L04, L05 | QUEUED | Loss/return, sleep/resume, restart/cancel, bounded recovery and one reconnect owner. READINESS_RELAY_PROBE_CORRELATION_GAP: validated Post probe is not forwarded through relayProcess/RNS/Channel/provider; zero direct rows cannot count relay calls. No wire expansion in R3. R2 cooldown-only retry mechanism reproduced deterministically in R3; original live exact network counts remain unknown. Automatically do not start. |
| L07 | Linux visual parity | L03, L06 | QUEUED | Реальные окна: согласованные экраны/состояния, список вариантов и отдельные selected-next/active state по D05, RU/EN, DPI100/125/150/200%, resize/focus/Tab/Enter/Escape; сопоставление с точным Android-эталоном без изменения Android106. |
| L08 | Linux updater и сохранение данных | L03, L07 | QUEUED | Переход со старого поддерживаемого клиента на полный bundle и совместимая миграция настроек выбора D05; identity/WG keys, активация, Support ID, история, настройки, ссылки и signed floors/счётчики сохранены. |

Продолжение после обрыва25.10: неизменный L03.1/build-9 повторно прошёл hash/member/source
verification, actual disposable systemd255 smoke и94 адресных проверки (umask077).
Новый runtime/build не создавался; затем review L03.1 принят и отдельно разрешён L03.2.

Phase22 подключила Linux ChatOwner к EXISTING_EXIT. L01 добавляет protected DIRECT;
старый SYSTEM не переименован в DIRECT и не используется fallback этого нового пути.
Локальный host lifecycle принят по L02.2; DIRECT public admission завершается в D01.3-R. Одно активное владение
не означает вечный PID: текущий worker имеет собственный жизненный цикл.
Полный внутренний пакет L03 обязателен перед закрытием L04–L08; system-only component-r18 недостаточен.

L02.1 source `a2b105de49391928d4bb9c15c4d5ee2305085918` pushed/remote-verified:
600 адресных Python/native/process checks, Go/race и isolated kernel PASS.
Завершившийся CI: authenticated service-only и прежние Auto/root→UID/DIRECT,
Client Linux/AWG/TCP/voice PASS; control 3015 passed/54 failed/127 skipped,
phase0/tests 3014/55/127, Docker 3013/54/129, errors0. Дополнительный phase0 failure
`test_ui_unavailable_server_ack_is_authoritative` — причина не установлена.
Это не общее CI acceptance. Новые L02.1-R результаты и SHA отдельно в
[текущем отчёте](releases/2026-10-24-linux-chat-mesh-l02-1-r.md); mandatory suites
не отключены, посторонние failures не исправлялись.
L02.1-R source **`6556a902c723a3ef73486733f090cea6f388d099`** pushed/remote-verified:
606 distinct local checks, native/race/reference и isolated kernel PASS. Завершившийся
CI: control 3015 passed/54 failed/133 skipped; phase0/tests 3015/54/133;
Docker 3014/53/135, errors0; isolated-linux с13 authenticated, Client Linux,
AWG/TCP и voice PASS. Эти результаты не переносятся на R2.
L02.1-R2 source **`89e20a3437b2ba1b02f7d1649487579678158373`** pushed/remote-verified:
211 distinct local Python/native/process checks, native/race/reference PASS;
завершившийся CI: control **3030/54/135**, phase0/tests **3030/54/135**,
Docker **3028/54/137** (passed/failed/skipped), errors0; phase0/tests перепроверен
по собственному логу. Isolated-linux с15 authenticated, Client Linux, AWG/TCP/voice
PASS. Точные R2 jobs и новые L02.2 source/jobs разделены в
[отчёте L02.2](releases/2026-10-24-linux-chat-mesh-l02-2.md).
L02.2 source **`dac0f6b45be6ed8703d3de93ff5fdbc67462eabe`** pushed/remote-verified:
isolated-linux **40129362252/120977564710 PASS**, включая original15, combined3,
root→UID, оба kernel gates и race. Новый CI: control **3032/54/138**,
phase0/tests **3032/54/138**, Docker **3030/54/140**, errors0; AWG/TCP PASS.
Client Linux **1003/1/94** (bounded-mailbox BrokenPipeError) и voice pointer/holding
FAIL, причины не установлены; не общий CI PASS. Никаких unrelated fixes или bypass.
Mandatory full suites и Auto/DIRECT/root→UID gates сохранены; локальный L02 принят review.
Новый D01.3 source/CI учитывается отдельно в [отчёте](releases/2026-10-24-desktop-chat-admission-d01-3.md).
Linux updater пока принимает legacy six-file archive; не объявлять полный bundle обновляемым до L08.

## Windows: платформенная и продуктовая интеграция

| ID | Результат | Зависимость | Статус | Критерий завершения |
|---|---|---|---|---|
| W01 | Windows native ↔ broker | D03, D05 / общий core | QUEUED | Модель/provider boundary D05 и MESH/P0/P1 подключены через защищённый broker/FriendsOwner IPC; собственные Windows runtime/readback проверки, не перенос Linux evidence; GUI без постоянного admin. |
| W02 | Windows Auto и recovery | W01 | QUEUED | Общий Go Auto интегрирован с платформенными службами и моделью D05; проверены выбор транспорта, отмена, cleanup/generation fencing и восстановление. Эта интеграция ещё не завершена. |
| W03 | Windows контакты, текст и история | W01, W02 | QUEUED | Пользовательская служба и WinForms выполняют базовый чатовый цикл с существующей identity. |
| W04 | Windows DIRECT/service-only | W03, L01/L02 contract | QUEUED | Чаты при VPN OFF и переходы владения работают на Windows с необходимыми проверками доступа и underlying routing. |
| W05 | Windows голосовые сообщения | W04 | QUEUED | Реализованы принятые запись, отправка, воспроизведение и существующие voice/radio режимы. |
| W06 | Windows фон и уведомления | W05 | QUEUED | Закрытие GUI, уведомления и восстановление пользовательской службы сохраняют принятую семантику. |
| W07 | Windows диагностика и online support | W06 | QUEUED | Экспорт, opt-in согласие, срок действия, отзыв и фоновая отправка соответствуют принятой модели; без автоматического opt-in. |
| W08 | Windows объявления | W07 | QUEUED | Реализованы существующие операции и проверки ролей без изменения прав пользователей. |
| W09 | Windows UI и остальные пользовательские сценарии | W03–W08 | QUEUED | Реальные visual comparisons, список вариантов с отдельными selected-next/active state D05, настройки, активация, приглашения/QR/deep links и согласованные элементы интерфейса. |
| W10 | Полный внутренний Windows installer | W01–W09 | QUEUED | Согласованные GUI, broker/native/RNS и зависимости с достоверными capabilities; сохранены SCM/driver paths и privilege boundary. |
| W11 | Установленная Windows-приёмка | W10 | QUEUED | На установленном кандидате проверены VPN, чаты, фон, recovery, переходы сети и применённый target/profile с заявленными capabilities; cross-build/Wine/headless/model fixture не засчитываются. |
| W12 | Windows обновление | W10, W11 | QUEUED | Совместимая миграция настроек выбора D05 при обновлении; identity/WG keys, активация, Support ID, история, настройки, ссылки и signed floors/счётчики сохранены. |

Windows chat endpoint на проверенном SHA — NOT_INTEGRATED. W10 предшествует завершению
установленной приёмки, даже если отдельные W01–W09 уже проверены в dev environment.
Нет разрешённой Windows-машины/VM/runner — runtime NOT_RUN с точной инструкцией,
а не PASS по Linux cross-build; доступные исходники/пакеты доводятся отдельно.

<a id="release-gates-three-platforms"></a>
## Финальные артефакты и границы выпуска

| ID | Результат | Зависимость | Статус | Критерий завершения |
|---|---|---|---|---|
| R01 | Финальная проверка поставки | L04–L08, W11/W12 | QUEUED | Точные AppImage/DEB/Windows installer, обновления и заявленные возможности согласованы; проверки относятся к финальным артефактам; SHA256/manifests/RU/EN инструкции готовы. Dynamic fleet не заявляется по D05 без отдельной интеграции/приёмки. |

AppImage — основной Linux artifact, DEB дополнительный; legacy archive сохраняется для совместимости.
Windows сохраняет действующий installer/broker/service/driver workflow, не новый формат ради parity.
Обновления сохраняют signed catalogs, digest, anti-rollback, permitted upgrade paths и identity.
Подписи update manifest, installer/Authenticode и driver перечислять отдельно; отсутствующие не выдумывать.
Версии выбирать по desktop-линейке; Android106 соответствие фиксировать feature/core manifest, не номером.
Полный parity installer сейчас0/2, завершённая установленная приёмка0/2.
Source/local tests/CI/build/install/private-test readiness/publication — отдельные состояния.
R01 готовит release/catalog/landing изменения, но НЕ разрешает публичную публикацию.
Исторические [three-platform gates](PLAN.history-2026-10-24.md#release-gates-three-platforms)
сохранены как прошлые обязательства, не как альтернативный текущий NEXT.

## Общие обязательные ограничения и выбор проверок

- Читаем STATUS, выбранный ID и только релевантные исходники/доказательства через [docs map](README.md).
  Исторические NEXT/ACTIVE в архивах и release reports не запускают другую задачу.
- Проверки выбирать по изменённому риску и обязательному gate; сначала адресные проверки,
  шире — при общей зависимости/регрессии/перед приёмкой. Не гонять весь исторический набор после мелкой правки.
- Сохранять точную связь source/artifact/evidence; старые PASS и hashes не переписывать для нового исходника.
- Для D00 только documentary consistency, byte-exact history, новые ссылки и `git diff --check`;
  никаких сборок, pytest, эмулятора, capsule sweep или live-трафика.
- Не менять Android106, действующие пользовательские MESH-сессии, gateway или чужую policy.
  Desktop P1 identities проверять отдельно; точечное операторское решение не блокирует создание installer.
- Native общий, не отдельные Python/C# RS/crypto реализации. Сохранять AWG/TCP, identity/roles/
  certs/revocation/expiry/floors/signed directory, accepted cache semantics и fail-closed traffic policy.
- На целевой ОС проверять TUN/DNS/IPv6/underlying service routes, cleanup при error/cancel/crash,
  negotiated P0/P1, HTTPS, single4MiB + parallel2×2MiB, idle/recovery и export.
  Первичный live-бюджет до32MiB прикладных данных на ОС; не тратить его на ограниченном мобильном тарифе.
- GUI обычного пользователя, ограниченные helper/broker IPC; не ослаблять key storage или защиту ОС.
- Реальные screenshots, а не наличие CSS/строк, закрывают visual gate. Для emulator retain KVM/host GPU,
  2 cores, CPUQuota150%, max180s, stop85°C CPU/80°C GPU; никаких idle/SwiftShader fallback.
- Commit/push каждого завершённого шага по [AGENTS](../AGENTS.md), без force/reset/clean.
  Проверять remote SHA; push не равен CI success, установке или публикации. Секреты/state/capsules/binaries вне Git.

<a id="other-obligations"></a>
## Другие обязательства — HOLD, вне текущей desktop-очереди

Ниже сохранены незакрытые направления, не разрешение начать их или расширить parity106.
Перед возобновлением сверить релевантную дельту, а не принимать старый NEXT за действующий.

| Направление | Что остаётся / источник |
|---|---|
| Android field / P1 cohort | Физические updates106/P1 и cold-bootstrap; Volgograd96 не закрывает Краснодар FIELD-1. [Cohort](releases/2026-10-23-tester-p1-cohort.md). |
| Fleet/control5.2–5.6, gateway recovery6 | Native/Friends/device integration, долговременная AWG/TCP/Android приёмка, independent ingress/recovery. [Исходные обязательства](PLAN.history-2026-10-24.md#глобальные-этапы), [recovery design](reticulum-recovery-design.ru.md). |
| Secrets / disaster recovery | Consumer audit перед удалением originals, production signing acceptance, внешний носитель и восстановление чистого хоста; не считать закрытым по локальным backup. [Архив](PLAN.history-2026-10-24.md#глобальные-этапы). |
| Операции RU/NL | RU SSH timeout, legacy Docker peer-worker unhealthy, RU counters неизвестны. [Snapshot](releases/2026-10-23-vpn-health.md); без рестартов ради диагностики. |
| Local storage / thermal | Сохранить symlinks; live project/Codex migration и reboot automount отдельно. [Migration](releases/2026-10-07-local-storage-migration.md), [GPU/thermal limits](releases/2026-10-23-laptop-thermal-diagnostic.md). |
| Остальной продукт | Doze/OEM/boot/Android13+, iOS/macOS, лицензирование, private security reporting, Windows publisher signing, коммерческий запуск. [Deferred backlog](PLAN.history-2026-10-24.md#отложенные-задачи). Новые VPS/покупки не разрешены. |

<a id="mesh-roadmap"></a>
Home Gateway (phone↔home PC, LAN/NAS/RDP/residential egress) остаётся отдельным design/backlog;
[5A–5G/RNS gates](reticulum/HOME_GATEWAY_DESIGN.md) не закрыты desktop MESH exit.
<a id="multi-carrier-roadmap"></a>
Multi-carrier: после авторизованного Краснодар FIELD-1 и разбора Telemost path;
[Carrier API → WB → VK → failover](PLAN.history-2026-10-24.md#multi-carrier-roadmap).
Ни новые carriers, ни MESH2/MESH3 не входят в parity106.
<a id="django-admin"></a>
Django7.1 (servers/access/payments) зависит от backend/fencing и recovery; нет второй writable
копии leases, платежи идемпотентны, migration/provider/secret store — отдельные решения.
[Сохранённый контракт7.1](PLAN.history-2026-10-24.md#django-admin), [design](design/django-product-plane.ru.md).

## История и завершение шага

[Полный прежний PLAN](PLAN.history-2026-10-24.md), [STATUS](STATUS.history-2026-10-24.md),
[phase22](releases/2026-10-23-desktop-parity106.md#linux-user-chat-admission-and-existing-exit-handoff-2410-phase22),
[отчёт D00](releases/2026-10-24-desktop-parity106-d00.md).
**STOP после CHAT-UX-1. NEXT — review CHAT-UX-1 перед установкой нового UI-кандидата владельцу;
L04.2/full L05/TCP HTTPS diagnosis/teardown/signing/publication NOT_RUN.**

Этот прежний STOP сохранён как история. **Текущий STOP27.10: readiness checkpoint
завершён; NEXT — закрыть только фактические ANDROID-CONTROLLED-BETA launch blockers.
Linux L04.2 PAUSED / NON-BLOCKING DESKTOP ENGINEERING, не DONE.**
