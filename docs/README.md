# Documentation

## Current operational restoration

[NL gateway replacement — 30 October](releases/2026-10-30-nl-gateway-replacement.md)
and [sanitized receipt](releases/2026-10-30-nl-gateway-replacement.json):
**BLOCKED_NL_REPLACEMENT / DIRECTORY_INVALID**: exact renewal rejects the expired publisher
directory before canonical promotion. RU/NL rollback readbacks PASS; journal preserved,
restricted inactive, renewal paused. RU ordinary HTTP restored and public HTTPS dispatch
verified. Old NL FENCED; new `185.10.158.212` AWG/TCP synthetic DNS/HTTPS/egress/cleanup PASS,
46 peers/46 credentials, three stable samples/0 restarts. Final coordinated backup verified.
Ubuntu26.04.1/kernel7.0.0-42, exact runtime/artifacts, about2GiB swap and RU ingress verified.
Paid ledger0/0, signed catalog sequence3 unchanged; no publication or owner smoke.
Endpoint-routing source checkpoint has43 passing tests/14 optional skips and reproducible
builds, but is NOT_DEPLOYED. Next: accepted expired-directory recovery, then remaining
server and client acceptance. No bypass or automatic transaction replay. This operational
exception does not advance the paused product queue.
**BETA-0-CANARY-1 remains PAUSED; paid events and Android stage0 remain off.**

[BETA-0-CANARY-1 — owner canary preparation](releases/2026-10-27-android106-beta-0-canary-1.md):
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

Historical entry: **OWNER_CANARY_BOUND_READONLY / BLOCKED_PROFILE_WRITER_CONFLICT.**
Pre-source read-only inventory proves an active approved credential-renewal writer
of the exact live profile;13 source hashes and controller/node pins match. The running
gateway also reads that profile. Snapshot-only migration would detach its view from
renewal. Shared publisher directory/group-write, source and production are unchanged.
No split/package/permit/credential/transaction; ledger0/0, CRL27216/floor27088 unchanged
within this checkpoint. NEXT: separately authorize a coordinated profile-path design
including renewal and gateway readers. No phone instruction or live canary action.
[Split-boundary receipt](releases/2026-10-28-android106-beta-0-canary-split-boundary.json).
[Parent hardening receipt](releases/2026-10-28-android106-beta-0-canary-parent-hardening.json).
[Ownership maintenance receipt](releases/2026-10-28-android106-beta-0-canary-ownership-maintenance.json).
[Fresh baseline/route receipt](releases/2026-10-28-android106-beta-0-canary-maintenance-baseline.json).
[Historical PID stop](releases/2026-10-28-android106-beta-0-canary-maintenance.json).

Historical read-only input: **BLOCKED_CRL_PROFILE_COMPATIBILITY.**
Read-only provenance review proves NL_VALIDATOR_ONLY_DRIFT: actual gateway parser
accepts14400s, stale auxiliary validator3600s. No precision mismatch or parser repair.
Actual forced command accepts read-only snapshots, rejects CRL writes; the lagging
floor cannot yet satisfy the required next-payload/update guarantee (CRL_FLOOR_UNRESOLVED).
96 affected +48 parser-boundary +18 gateway/floor checks PASS. Existing binding/exact106
retained, ledger0/0, owner certificates0; no lookup/status repeat or live write.
[Sanitized review receipt](releases/2026-10-28-android106-beta-0-canary-nl-readonly.json).
Historical review proposed bounded maintenance/delivery and floor-contract reconciliation.
Source is ready; production continuation is blocked by the fresh preflight above.
No generic writes, snapshot replacement or phone instruction.
Historical source gate: pure paid-aware CRL builder,
one-generation private journal, exact-byte retry after proven NOT_SENT only and
remote/local crash recovery;98 new tests PASS. Existing restricted/sync/directory206
PASS (29 optional native skips/4 native deselections). Its production lookup was
NOT_RUN; lookup/binding are now recorded above. Live writes remain NOT_RUN; unbound
CRL package has no operational config/credential.
Running local console upgraded through migration0006 after paired private backups
and disposable restores;118 console +76 backend tests PASS. Single-token canary
operator now SOURCE_READY_WITH_EMERGENCY_RECOVERY (79 tests); source-context umask
regressions2 PASS. Internal canary remains zero-value and outside customer revenue.
Recovery from versions1/2 is exact30 days from permit start, permits dispatch delay
0..299s, is certificate-guarded and terminal via an existing reference_hash marker;
normal path unchanged. Enrollment/expiry/CRL/recovery remain NOT_RUN.
CRL source gate is complete; owner binding is read-only, phone entry blocked.
Live operations require READY_FOR_OWNER_LIVE and owner ГОТОВ. No production mutation;
transient selector unlinked after its single lookup, absent from retained evidence.

[CONTROL-PLANE-2 — paid-aware production boundary](releases/2026-10-27-android106-control-plane-2.md):
owner accepted **DONE / PAID-AWARE EMPTY-COHORT BACKEND SERVING**, не paid launch.
Exact candidate unchanged; typed D-Bus observer, fresh PRESENT_EMPTY backup/restore,
effective ExecStart guard and post-start inventory/liveness PASS. One rollout restart,
zero emergency restarts; paid rows/events0, critical non-cohort/publisher fingerprints
unchanged.61 committed focused tests +9 private runner-flow tests PASS. No second
rollout, real enrollment/payment or desktop work; read-only monitoring continues.

[CONTROL-PLANE-1 — русская панель и read-only observability](releases/2026-10-27-android106-control-plane-1.md):
50 demo identities, production-readonly inventory двух шлюзов (RU54, NL registry
недоступен), fleet snapshots/technical models, charts/filters/drill-down, emergency
stop;95 console+76 backend tests и desktop/mobile PASS. Без реальных оплат,
enrollment/deployment; live client telemetry/alerts не собираются. Sole entitlement
authority — Friends paid_beta. [Локальный runbook](../control_plane/README.md).

Start with the compact [current STATUS](STATUS.md) and [selected PLAN task](PLAN.md).
STATUS/PLAN define the current bounded task and next review gate, not an automatic
continuation. Phase22 is the product baseline; D03–D05 source checkpoints are not new releases.
Entries below are an evidence/runbook index; historical NEXTs are not current assignments.

## Current priority — Android controlled paid beta

[CONTROL-PLANE-0 local checkpoint](releases/2026-10-27-android106-control-plane-0.md):
Django/PostgreSQL console over the accepted paid backend, **LOCAL SYNTHETIC ONLY**.
Custom Admin/dashboard/charts, lookup/read-only projections, preview/confirm/
reconcile, payment/cohort/incident/audit/release metadata; no second subscription
state machine.57 console+76 focused backend PASS; desktop/mobile browser workflow
PASS. Production registry/deployment/real payment/enrollment NOT_RUN. [Run locally](../control_plane/README.md).

[27.10 owner decision and Android106 readiness](releases/2026-10-27-android106-controlled-beta-readiness.md):
**ANDROID-CONTROLLED-BETA** replaces Linux as critical path. FIELD-1 owner PASS
covers real external whitelist-network MESH use, not desktop parity. Exact signed
APK/reference/metadata verified; read-only activation/admission active, newer106
READY ACK distinguished from stale support84.49 backend +20 JVM PASS historical;
[PAID-ENTITLEMENT-MVP](releases/2026-10-27-android106-paid-entitlement-mvp.md) now
implements atomic paid cohort/model/audit/operator and challenge/fetch expiry caps:
243 targeted PASS,10 skips/8 deselections, **originally NOT_DEPLOYED; CP2 now deployed empty**. [Private operator
runbook](paid-beta.md). Owner Beta-0: cap10 existing activated identities on exact106,
private handoff/manual payments; older-version upgrade and external acquiring are
out of first-beta scope, not newly PASS. Paid-aware live/synthetic106 acceptance,
safe recovery, delivery/opt-in, legal and monitoring/stop gates remain BLOCKED.
No Android source change, APK rebuild or real paid enrollment; only CP2 empty-cohort server rollout.
Linux L04.2 **PAUSED / NON-BLOCKING DESKTOP ENGINEERING**, not DONE: R3 source
gate accepted, .11 construction frozen/read-only; installed package/live acceptance
NOT_RUN. Receipt filename collision is existing D02/CI debt, not an Android blocker.
**STOP. NEXT: close only actual Android controlled-beta launch blockers.**

## Historical engineering index — not active NEXTs

The earlier progression instructions below are retained evidence, superseded by
the27.10 owner decision. They do not authorize a Linux retry or another task.

[L04.2-R3 readiness cause preservation](releases/2026-10-27-linux-readiness-cause-preservation-l04-2-r3.md)
continues existing PLAN L04.2. R2 is FINAL PARTIAL / READINESS_CAUSE_UNRESOLVED;
its Phase B/setup/GUI authorization and immutable .10 evidence remain accepted.
No further live Connect on .10. R3 source gate DONE / review accepted for package progression: preserve typed
availability failure independently of FETCH_FAILED receipt, preserve validated
cache fallback, bound cooldown-only supervisor retry. Exact Go/native/MESH/cleanup
and desktop1317+82skip pass; reviewed Gson/cache harness blockers resolved. Retained
Gradle171 is not rerun; offline Go cache closure and Android/Python143 PASS.
Canonical readiness run40491350035 SUCCESS. Raw full suite55/3373/105 remains FAIL, not overall CI PASS. Review separates
local36 from historical fixture-absent19 (D02.1-R/CI debt); union55 is not a new
permanent baseline. Internal .11 candidate570a5515/system34b27cb9 constructed and sealed;
embedded integrity PASS/container exit0, outer receipt-name/ownership collision
FAIL_ENVIRONMENT/exit1. R3 PARTIAL/PACKAGE_GATE_FAILED; no installed/live gate
after stop, no replay or product patch. No full-suite replay. READINESS_RELAY_PROBE_CORRELATION_GAP is L06 debt; no server,
material, policy or wire changes. Owner workstation NOT_USED; L05/messages/voice
acceptance/signing/publication NOT_RUN. STOP. NEXT: review R3 package-harness finalization.
The accepted
[core P0 failure](releases/2026-10-26-linux-installed-mesh-auto-l04-2-core.md)
is not replayed on .9. Historical reports and .9/system bytes remain immutable.
Chat delivery_unavailable stays in L05 backlog, not a VPN prerequisite; no chat
diagnosis, owner-workstation use, signing or publication. Expected messenger/support
proxies remain distinct; the earlier literal singleton gate was corrected by review.
[CHAT-UX-2](releases/2026-10-26-chat-ux-2.md) source/package is DONE:
one main-window messenger and the exact49-face Android106 ICQ-classic GIF/token pack.
[CHAT-UX-1](releases/2026-10-26-chat-ux-1.md) is technically completed in reviewed
source/UI/package scope, but its product design is superseded by owner decision.
Its historical screenshots, .8 artifacts and unsuppressed failures remain intact.
Owner review accepts installed internal .9 as PARTIAL / owner-use accepted;
two queue events of unknown origin are excluded, no product defect established.
OWNER-CHAT-UX-2-INSTALL is not continued; no additional owner UX checks.
The .9 source/UI/package checkpoint is implemented; full-suite acceptance remains
PARTIAL with unsuppressed residuals and a separate FD teardown observation.
Full L05/signing/publication remain NOT_RUN, not implied by owner-use acceptance.
[Ubuntu26.04/Python3.14 compatibility](releases/2026-10-26-linux-ubuntu2604-python314-compat.md)
remains historical compatibility evidence; frozen .5/.7/.8 are not rebuilt.

[L04.1 final installed receipt](releases/2026-10-25-linux-installed-awg-tcp-l04-1-final.md)
closes LIVE-2 and L04.1 as DONE/review accepted in installed Linux AWG/TCP scope:
E/F1/F2 accepted. [Single beta-freeze manifest](releases/2026-10-25-linux-awg-tcp-beta-freeze.json)
pins exact .5, internal/unpublished, unchanged bytes. Registry restart remains a
separate operational observation: uninterrupted continuity NOT_PROVEN, cause unknown,
assignment/configuration unchanged. No F2 replay or R3. Parent L04 remains IN_PROGRESS
only because of L04.2; P0 core failure is recorded above, P1/Auto, L05 and device
teardown remain NOT_RUN.
MESH/Auto and messenger are outside the historical beta scope;
its signing/publication decision is not the current NEXT.
[R2 queued Connect/Close](releases/2026-10-25-linux-queued-connect-close-l04-1-live-2-r2.md)
is DONE/review accepted in source/package scope. Linux/AWG/TCP/package CI PASS,
full suites54/54/54 failures retained; no new general CI PASS claim.

The entries below describe historical scopes and receipts, not parallel current NEXTs.

[Desktop parity with accepted106 — active, not released](releases/2026-10-23-desktop-parity106.md):
full feature matrix, exact source manifest, both native worker builds, Linux
isolated kernel TUN/routing evidence and explicit remaining
Linux/Windows UI/MESH/messenger/package gates. [Architecture](desktop-architecture.md)
and [shared bridge ADR](adr/003-desktop-mesh-bridge.md),
[Linux session chat owner](adr/004-linux-chat-session-owner.md).
[Desktop/provider boundary — D05 Linux source, review accepted](desktop-architecture.md#desktop-fleet-boundary):
separate target/assignment/applied session, strict legacy provider and later platform gates;
[D05 evidence](releases/2026-10-24-desktop-provider-d05.md), not dynamic fleet acceptance.
[Accepted restricted-chat core contract](../clients/shared/android106-chat.json)
now has a shared Go API/mailbox adapter, native VPN ownership and a bounded separate
Linux parent/native IPC lane. UID/device-bound user-service admission now forwards
API/mailbox requests through an existing MESH exit. [L01 protected DIRECT](releases/2026-10-24-linux-chat-direct-l01.md)
now connects the Linux ChatOwner to independent fixed root admission and native protected sockets;
local synthetic-peer kernel acceptance is separate from installed/live gates.
[L01-R review corrections](releases/2026-10-24-linux-chat-direct-l01-r.md) cover unit umask,
registration provenance and real TCP/TLS fatal alerts; L01/L01-R review is accepted
in Linux source/native/root→UID/isolated-kernel scope.
[Initial L02 service-only/ownership](releases/2026-10-24-linux-chat-mesh-l02.md) was PARTIAL:
source demand host and process admission exist. [L02.1 lifetime checkpoint](releases/2026-10-24-linux-chat-mesh-l02-1.md)
adds a generation lease and authenticated service-only fixture, not VPN publication
acceptance. [L02.1-R terminal-generation recovery](releases/2026-10-24-linux-chat-mesh-l02-1-r.md)
adds native generation-pinned operations and authenticated failure/recovery barriers.
Its atomic pin/terminal recovery review is accepted. [L02.1-R2 status classification](releases/2026-10-24-linux-chat-mesh-l02-1-r2.md)
separates CONTROL contention from terminal evidence and preserves DENIED to the UI.
R2 review is accepted. [L02.2 combined gate](releases/2026-10-24-linux-chat-mesh-l02-2.md)
adds local authenticated OFF→ON→OFF through real manual and Auto owners,
TUN/private DNS/publication, broker leases and bounded release accounting.
L02.2/local L02 review is accepted. [D01.3 public IPC completion](releases/2026-10-24-desktop-chat-admission-d01-3.md)
and its [D01.3-R correction](releases/2026-10-24-desktop-chat-direct-completion-d01-3-r.md)
are accepted in the public completion/admission scope.
[L03.1 system/runtime component](releases/2026-10-25-linux-system-runtime-l03-1.md)
and [L03.2 full internal candidate](releases/2026-10-25-linux-candidate-l03-2.md)
are review accepted; parent L03 is DONE in that internal package scope.
[L04.1 initial blocked checkpoint](releases/2026-10-25-linux-installed-awg-tcp-l04-1.md)
is historical. [L04.1-AUTH](releases/2026-10-25-linux-test-activation-l04-1-auth.md)
created one dedicated active test identity; activation and
[L04.1-AUTH-PROVISION](releases/2026-10-25-linux-test-provisioning-l04-1-auth.md)
are DONE/review accepted. [L04.1-LIVE-1](releases/2026-10-25-linux-installed-awg-tcp-l04-1-live-1.md)
is PARTIAL: exact DEB setup and real AWG/TCP transfers/cleanup pass in a disposable
Ubuntu24.04 VM; original AppImage Disconnect against the retained owner fails after
GUI reopen with connection-operation contention. No reconnect after failure; cleanup-only
GUI Disconnect restores baseline, guest copies are destroyed, original test state is retained.
L04/L04.1 remain IN_PROGRESS; LIVE-2/L04.2 and device teardown remain NOT_RUN.
LIVE-1 PARTIAL is review accepted; final-2 is retained only as historical evidence.
[L04.1-LIVE-1-R](releases/2026-10-25-linux-poll-disconnect-l04-1-live-1-r.md)
is DONE/review accepted in source/package scope: deterministic poll/Disconnect fencing,
source57f8eff/internal0.2.12~l03.2.2/candidate d9c0d07f…, unchanged system build-9.
Exact inventory and both real systemd255/pkexec package gates PASS; Linux/AWG/TCP/
native/package CI PASS, full suites remain red (54/54/53 failures), voice FAILURE.
[L04.1-LIVE-1-RETEST](releases/2026-10-25-linux-installed-awg-tcp-l04-1-retest.md)
is DONE/review accepted: new KVM exact DEB/setup, AWG/TCP transfers, single Disconnect and
original AppImage close/reopen PASS. Fresh nonce DNS reaches the actual TUN but
returns valid terminal NOERROR/NODATA, accepted by review alongside positive/NXDOMAIN.
Cleanup and state preservation PASS; guest copies destroyed. No product changes.
[LIVE-2](releases/2026-10-25-linux-installed-awg-tcp-l04-1-live-2.md) is PARTIAL/review accepted:
A installed tamper/reinstall PASS; B1 stops transport but leaves pending/APPLYING after
root-lock release. First-failure STOP; B2–F NOT_RUN, no product changes/retries.
Guest destroyed, original state retained. Its later exact .4 continuation accepts
P1/P2/B1/B2/C1/C2/D, stops at E FAIL/review accepted; F1/F2 NOT_RUN. R2 above is
source/package only. L04.2/L05/device teardown remain NOT_RUN.
Windows broker IPC remains NOT_INTEGRATED;
installed restricted-message acceptance is NOT_RUN, not a completed fallback.
[Shared Auto policy and accepted-Java trace checks](../carrier/desktopauto/README.md)
are implemented locally and included in the native worker's bounded private-pipe
[Auto protocol](../clients/mesh/automatic/README.md). Linux guarded-parent IPC and
single-attempt MESH source exist. [Protected normal configuration and AWG/TCP
helper adapters](clients/DESKTOP_AUTO_NORMAL.md) now join the root coordinator and
authorized GTK Auto client, with local tests and private components. Installed
VPN/upgrade acceptance and Windows broker remain open.
[Private-candidate Auto user/support notes, RU/EN](clients/DESKTOP_AUTO_USER.md).
No public links changed.
Phase17 adds isolated installed-AWG3.1 crash/teardown checks and strict resource
ownership, with925 local regressions and internal component-r13. Host and Windows
acceptance remain open; the component is not a complete desktop installer.
[Linux Auto traffic guard](clients/DESKTOP_AUTO_GUARD.md) now has isolated real
kernel/nftables/TUN checks; coordinator, installed and Windows gates stay open.

[Closed P1 cohort and Volgograd field result,23.10](releases/2026-10-23-tester-p1-cohort.md):
**PRIVATE_FIELD_READY** for the confirmed three devices. Unchanged signed106;
gatewaya515 exact-group policy deployed, post-deploy owner Wi-Fi/P1/small HTTPS PASS.
Export21 and tester testimony establish a positive cellular MESH result on96,
not106/P1/cold-bootstrap acceptance. RU/EN handoff instructions and rollback ready;
owner distributes manually, no public release. Earlier checkpoints follow.

[Reboot continuation / signed106,23.10](releases/2026-10-23-wifi-resume.md): actual105
Wi-Fi/off, consent active but full JSON blocked; diagnostic106 final219 tests/replay
PASS, same native transport, signed/installed same-key. Fresh JSON/Support ID and
ordinary both-end P1/TUN verified; body/recovery and tester policy still separate.
Fresh Wi-Fi19/19 bodies, ordinary Disconnect/Connect and automatic Wi-Fi-loss return
pass. New P1 session and one full1KiB HTTPS verified; Wi-Fi creation→CONNECTED106.578s.
Same32MiB budget used8,407,040 bytes; next boundary is closed tester P1 membership/
single-target server policy, not another owner outage or bulk series. No rollout.

[Owner Wi-Fi rebaseline and beta105 reconciliation,22.10](releases/2026-10-22-owner-disconnections.md):
owner reports exhausted mobile allowance/throttling; retained105 install receipt
and online Wi-Fi/P1 readback supersede the paused summary. Signed APK verified;
USB verifies installed105; received normal export15 is stale19:43UTC history.
Aggregate record overflow reproduced locally; latest USB consent now disabled.
Normal consent/live readback, diagnostic correctness, body/recovery and tester P1 remain open.
The following older summary is retained as a historical checkpoint:
fresh101/P1 readback, RS failures retained before/after102, separate health and
deadline-bridge corrections;213 JVM/12 bridge checks for103. NOT_PRIVATE_FIELD_READY;
actual HTTPS, controlled network return and tester P1 delivery remain gates.
[RU/EN candidate instructions](clients/OWNER_RECOVERY_CANDIDATE.md).

[New owner P1 acceptance,21.10](releases/2026-10-21-p1-owner-acceptance.md): exact99→100 bounded lifecycle observation installed, P0/TUN smoke verified; P1 acceptance still pending. Separate new budget/criteria, no other-user rollout.

[Owner support automation98→99,21.10](releases/2026-10-21-owner-support-automation.md): owner-only99 installed, unchanged native; automated P0 restore verified at both ends, real online99 reports62/69s apart after completion-based cooldown fix. Owner CONNECTED/READY, current-session errors0; historical errors unresolved. No speed/fleet rollout. [Replay/operator instructions](../tests/fixtures/support_automation/README.md).

[Android consolidated speed candidate,21.10](releases/2026-10-21-android-speed-candidate.md):
same-key97 installed owner-only, compatible gateway transition explicitly approved.
Original/new P0 each15/15 delivered; new P0 single/aggregate−18.44%/−25.05% triggers
frozen consistency review, cause unresolved, no speed/product acceptance. Both-end
P1 applied32/32/Mux128 verified, first1.400435/2.290405Mbit/s observation. P0a
later errors exclude clean acceptance; later P1 gateway3/exhaustion also retained.
P2a actual both-end32/32/Mux128/Q1,15/15 bodies,1.348109/2.291969Mbit/s;
Android errors1→10 over664.356s including load/background, no terminal error;
exact stage/branch unknown; later gateway1/exhaustion, not clean acceptance.
P2b15/15 delivered,1.245062/2.545860Mbit/s; Android post0 then later2, server1/exhaustion,
not clean acceptance. P1b15/15,1.324169/2.583097Mbit/s; Android post0→1 over831.678s
including background, exact stage unknown; not clean acceptance or a failed download.
Later P1b gateway3/exhaustion retained. Final P0b actual8/16/effective8/LEGACY64:
single0.654210Mbit/s and12 small complete, parallel two partial/curl18 after proven
scheduled renewal stops gateway.103/105 complete responses across seven phases;
56.08203125/64MiB reserved. Windows raw single2.116×/2.024×, reverse aggregate
unavailable; Q1 adds no speed gain. No clean admission or automatic repeat.
Final `(14)` confirms P0 at both ends after renewal, Android CONNECTED/READY with17
protocol errors in the new session (not P0b's counter). Cause unknown; keep P0.
Cycle closed with limitations, no more owner exports/load and no product admission.
Same binary, profile certificate/revocations renewed; no task restart/timer change.
No tester/public rollout/push. Local tests and all exceptions retained.
[Evidence](releases/2026-10-21-android-speed-candidate.evidence.json),
[replay/runbook](../tests/fixtures/speed_candidate/README.md).

[QUIC over existing media,21.10](releases/2026-10-20-mesh-capacity.md#quic-over-existing-media--21-october-2026): implemented native streams and QS diagnostic, local race/fault gates and11 isolated live sessions; no repeatable clean P speed gain. All failures/receipts/costs retained, production unchanged and resources cleaned. [ADR](adr/2026-10-21-quic-media-lab.md), [evidence](releases/2026-10-21-quic-carrier.evidence.json).

[Carrier fragmentation/FEC,21.10](releases/2026-10-20-mesh-capacity.md#carrier-fragmentation-and-fec--21-october-2026): implemented L/S/SF, local and forward/reverse NL→Linux P completed; no repeatable useful speed gain, production unchanged; next separate QUIC replacement.

[P-stack × packing interaction,21.10](releases/2026-10-20-mesh-capacity.md#p-stack-bottleneck-and-packing-interaction--21-october2026):
closed A/B/C/D/D/C lab at RS32; credit-return bottleneck established, no writer
defect/patch or repeatable material packing addition. Six clean phases plus one
retained post-delivery controller failure,57.345MiB source/86.307MiB media. Q1 retry
correctness revalidated separately, never mixed into variants. Full small-response,
wire/resource cost and historical-state uncertainty retained. All owned lab resources
closed; production96/1011/A0/LEGACY64/OFF unchanged. Next fragmentation/FEC, then
QUIC only if needed; no product admission/APK/deployment/push.
[Replay contract](../tests/fixtures/tls_rs_packing/interaction/README.md).

[TLS→RS packing,21.10](releases/2026-10-20-mesh-capacity.md#tlsrs-packing--21-october2026):
implemented/tested bounded B2 before RS allocation, unchanged media A/0;16 isolated
attempts closed,106.260MiB source/130.582MiB media. T8 +94.731%, T32 +119.942/+86.390%,
but P32 gains do not repeat. One clean P8 pair +9.489% single/+35.981% aggregate.
Local small RTT +4.472ms; denser slots amplify pre-write retry bytes under a controlled
stall. No product admission. Failed attempts/late shutdown warnings and fixed drain
helper are retained. Production binary/flags unchanged, but unexplained process/
profile change BETWEEN series prevents a whole-run profile-equality claim. No
deployment, phone or security-state operation. Its P writer/credit/latency/retry
follow-up is now closed above; RS32 remains lab-only. Exact sources/tests in private kit.

[MESH capacity phases1–3,20–21.10](releases/2026-10-20-mesh-capacity.md): original19
NL sessions/window findings retained, including excluded P816 warning and long R32
20930560 useful B/29.935790s=5.593455Mbit/s. Phase3 adds14 isolated sessions: periodic
C gaps are real, before complete valid-RTP input; monotonic clock B repairs RTP/SR
but not C loss. Matched R32 completes; P32 B/A effects change sign, all20 bodies and
both-end protocol counters clean. No accepted application speed fix. Local byte-exact
test proves22/34 RS block origin at TLS record segmentation, not a new packing patch.
Phase3 budgets63.587/128MiB source and88.476/256MiB media, all28 peers/collectors/stages
closed; gateway734b…/beta96 unchanged during phase3. TLS→RS follow-up now completed above;
fragmentation/FEC/QUIC conditional later, no automatic admission or migration.

[Same transport / different host20.10](releases/2026-10-20-mesh-host-comparison.md):
isolated Linux NL/RU A/B/B/A complete,20/20 byte-exact,Mux64 errors0,32.750217MiB.
Same current OFF/Q0/A0 transport; bounded RU single gain+17.57/+25.65%, aggregate
+22.24/+19.56%, latency mixed. Four different SFUs: placement+path result, not
host-only causality or Android product acceptance. Production96/gateway734b… unchanged,
all test peers/stages/identities closed/removed, collectors OFF. Separate Android
comparison is the next decision, not automatic migration/new tuning.

[RTP packet pacing20.10](releases/2026-10-20-rtp-packet-pacing.md): after owner confirmed
no tester active, one guarded restart16:54UTC loads734b6ca6…; TLS/CRL/runtime directory
PASS, current credentials and96/A0 unchanged. Local fixed4Mbit/s implementation,
equal-budget burst/model, shared completion prerequisite and race/close tests PASS.
All A1/B1/B2/A2 complete,16/16 requests,32.25/64MiB. **NOT_ACCEPTED** for tested
fixed4M owner pacing: paired single−3.84%/−7.99%, aggregate+5.90%/−14.98%, control
latency−39.09%/+7.54%. Bursts smaller, no repeatable useful gain; media/background
and pre-load TUN qualifications retained. Errors1→1 each, no observed in-load reconnect.
Same96/A0/gateway/process/credentials, LEGACY64/128 OFF. Collectors/export OFF.
Manual return **confirmed17:58:33UTC**: new VPN342/tag7e12971a…, authenticated
LEGACY64/65536 via runtime/exact shared ALPN mapping, no pacer → **OFF/Q0**.
Errors1→1 in passive observation; initial cause unknown. Export/workers OFF,
no additional load or manual action. No new phases/rates/build/restart;
exact272bbc… rollback retained, not applied. Experiment closed NOT_ACCEPTED.

[Volgograd mobile bootstrap20.10](releases/2026-10-20-volgograd-mobile-bootstrap.md):
verified94 exports and READY ACKs; historical transport class unknown. Reproduced
Python RNS availability classification defect; narrow96 candidate + bounded JSON
diagnostics built,175 JVM/6 Python/8 focused native race tests PASS. Same-key signed96
installed over owner95, UID/server identity bindings preserved; manual Connect/new96
READY pending. Private tester file handoff requested, receipt/installation unconfirmed,
cellular FIELD NOT_RUN. A0/native and compatible gateway1011 unchanged,128 OFF;
last negotiated LEGACY64, no active VPN after update. Mux experiment remains closed.

[Negotiated Mux64/128,20.10](releases/2026-10-20-mesh-mux-credit.md) ·
[ALPN/resource contract](adr/2026-10-20-negotiated-mux-credit.md): implemented,
actual old/new matrix PASS, owner95 installed, compatible gateway retains b9/1011.
All three pairs completed,24/24 requests. Single gains+24.93/+89.32/+3.65%; aggregate
+8.68/+21.30/−13.61%; control latency mixed. **INCONCLUSIVE**, not accepted for owner
default128; shared RS/background/media differences and pre-A3 external restart retained.
Manual return confirmed13:39:52UTC: new VPN336, actual LEGACY64/65536 both endpoint
contracts via authenticated ALPN/runtime/pinned binaries; next-session128 OFF.
Counters OFF, no collectors/wait or more bulk; tester94 unchanged;48.5625MiB total.
Exact hashes, session scopes and final closure receipt are recorded in the report.

[Historical single-flow / Mux credit investigation,20.10](releases/2026-10-20-mesh-mux-credit.md):
completed24MiB equal-volume1/2/4-flow matrix,14/14 complete in one media session.
Single0.587/0.851;2-flow1.059/0.979;4-flow1.322/1.132Mbit/s. Local credit gate
observed with spare senderRS, but end-to-end independence remains unproven.
Matched128KiB model improves single; no safe current window negotiation, so no
functional production patch or speed acceptance. Exact b9/1011 restored10:24UTC,
ordinary94 unchanged, counters off,28.0625MiB total. User reports sending a version
to tester; exact sent APK/installation/whitelist unverified. Compatibility delta retained.

[MESH receive-path localization,20.10](releases/2026-10-20-mesh-receive-path.md):
completed serialized finite-deadline implementation and fresh physical A1/B/A2.
A100/B125 tests PASS; B125 conditionally rescues1294, not614/1127.9/9 bulk complete,
single0.568/0.631/0.567 and aggregate1.275/1.322/1.254Mbit/s. Positive B difference
is not repeatable mechanism-supported acceptance; current owner is forward94,
exact baseline92 native/A0 policy, same-key/data/identity preserved. Exactb9/1011
unchanged, trace OFF, no public release/push. New38+760+170 local checks PASS,
450 unchanged reused. Missing paired Android counters and597 final6s remain
explicit; latest94 export is A2 only, old incident90 not a new failure.

[MESH queue/retry control,19–20.10](releases/2026-10-20-mesh-queue-retry.md):
current completed result. Exact current1011 local-writer reproduction confirms
retry accumulation; one compatible server candidate is tested in A/B/A but not
accepted for repeatable speed. Current1011/beta90 restored, temporary performance
trace off, no new APK or public release. Preserve this baseline, not old4b.

[Recurrent tunnel closures / beta90,19.10](releases/2026-10-19-tunnel-restart-fix.md):
preceding stability task. Preserved89 evidence separates real media/signaling loss
from a seed1011 whole-gateway teardown cascade. Exact-base bounded seed containment
deployed; normal same-key90 removes extended trace and retains88 recovery. No
false health cause established, no claim all disconnects cured. Separate committed
renewal I/O interruption reconciled forward. Local regressions/readiness pass;
bounded physical scope and remaining acceptance facts are explicit. No push/public
release, hosting migration or resurrection of rejected throughput patches.

[MESH two-sided throughput trace / beta89,19.10](releases/2026-10-19-mesh-throughput-trace.md):
historical result: receiver→JNI→export correlation verified physically; one minimal
SACK-hole candidate tested and rejected, A1/B/A2 retained. Original NL gateway
restored and MESH/identity checks pass. Owner keeps observation-only beta89, not a
speed release; beta88 delivery/public versions unchanged. Amsterdam IPv6 deferred
by owner, SPb not run. Local source checkpoint8da6fd5, no push.

[Beta88 targeted throughput / IPv6,19.10](releases/2026-10-19-beta88-throughput-ipv6-1.md):
physical DATA/window/Mux comparison, rejected read-alignment candidate, accepted
gateway restored at that checkpoint; historical unsent HOSTKEY request superseded
by the owner's deferral. Beta88 artifact remains unchanged.

[Beta87→beta88 recovery candidate,19.10](releases/2026-10-19-beta87-product-fix.md):
current product-fix priority; exact night failure reproduced. Signed same-key/native88,
135+34 JVM checks PASS. Owner87→88 upgrade/readback and same-identity READY pass;
fresh88 export proves one automatic recovery29.083s around normal rotation, followed
by production DNS/HTTPS and bounded bulk. Single median87→88:0.528→0.500Mbit/s;
parallel1.146→0.913Mbit/s, no improvement established or optimization shipped.
Repeated recovery/overnight remains unaccepted. Independent IPv6
local prototype tested, NL global allocation/default route absent. No server
deployment, canary or public distribution.

[Existing-users private beta delivery,19.10](releases/2026-10-19-existing-users-private-beta-1.md):
Current priority, superseding PERF continuation. Exact-base all_activated management/API
and finite90-day authority18 applied; no new user registration or FIELD grants.
Beta85 physical failure localized to a research-only version gate; corrected beta86
signed and installed on owner, native unchanged; initial READY/DNS/HTTPS pass.
Scheduled renewal commits. Fresh export proves successful post-rotation restoration,
then another carrier loss and terminal authenticated HELLO_RECEIVE/CLOSED_PIPE.
Beta87 narrowly fixes that bounded-recovery classification:125 local tests PASS,
same-key signed and installed over86. Owner87 same-identity READY and production
Android-TUN DNS/full HTTPS pass23:48UTC. Automatic87 recovery is not yet observed;
private delivery is not yet accepted. Underlying carrier cause remains unknown.
[Private upgrade instructions](clients/EXISTING_USERS_PRIVATE_BETA.md).
Not a public
release or a performance claim. [Access/lifecycle](../deploy/friends/restricted/EXISTING_USERS_LIFECYCLE.md).

[MESH-PERF-3B timing preflight,18.10](releases/2026-10-18-mesh-perf-3b.md):
Conditional time-only intersection exists, but exact sealed operator cannot allocate
a fresh operation while the preserved CLEANED audit row remains.23 local checks
pass; no new canary/API/owner handoff. Production TUN DNS/HTTPS control passes,
not a canary/performance result. Current result BLOCKED before live start;
no background schedule. Historical retry evidence below is preserved.

[MESH-PERF-3B authorized launcher retry and safe cleanup,18.10](releases/2026-10-18-mesh-perf-3b.md):
Actual systemd environment/pre-start checks and one isolated seed READY pass.
Physical BLOCKED at C→R: current production publication is older; normal rotation
is later than this canary's valid arming window. No API/owner handoff or bulk;
canary stopped, production/UI84 preserved.20 focused checks plus real-directory
local rollback rejection pass. After owner Connect, fresh TUN DNS/HTTPS214bytes
and production-PID attribution pass. UI84's actual mode label is Telemost.
No APK update/optimization or further live retry.

[MESH-PERF-2 explicit-endpoint bulk baseline,18.10](releases/2026-10-18-mesh-perf-2-bulk-1.md):
PASS for bounded performance measurements, not a transport fix. Same UI84/TUN/MESH:
single-download median0.625820Mbit/s, two-TCP aggregate1.124855Mbit/s; upload estimate
median0.474360Mbit/s with server count header but no verified digest/read contract.
Loaded HTTPS timings and gateway window pressure measured; small-record cause
INCONCLUSIVE. No runtime changes. Supersedes the prior missing-endpoint bulk gate.

[MESH-PERF-2 physical continuation,18.10](releases/2026-10-18-mesh-perf-2-physical-1.md):
PARTIAL. Unchanged UI84/batch1 over LTE; VPN/egress/MESH-PID socket correlation and
DNS/full HTTPS PASS.120/120 nominal-idle full-response timings measured, not network
RTT. Sustained download/upload and loaded latency NOT_RUN pending verified existing
bulk endpoint contracts; small-record hypothesis INCONCLUSIVE. Existing bounded
SessionTrace observations and exact missing fields retained. No runtime changes.

[MESH-NL-RECOVERY-APPLY-1,18.10](releases/2026-10-18-mesh-nl-recovery-apply-1.md):
PARTIAL overall; exact recovery COMMITTED/CLEANED, authority17/CRL27120, accepted
NL gateway restored and bounded TLS/seed/directory checks PASS. UI84 import READY
observed; physical MESH DNS/HTTPS was NOT_RUN at that checkpoint, now superseded by
the physical continuation above. Existing
renewal scheduled service succeeds; next actual rotation not observed, external alerts
still unavailable. Operator target before19 October02:33:41UTC. No software/policy
or transport changes. This report supersedes older application/failed-NL statuses.

[MESH-NL-RECOVERY-SIGN-1,18.10](releases/2026-10-18-mesh-nl-recovery-sign-1.md):
PASS for exact-request offline-root vault signing and independent verification only.
Local candidate16→17, hashes/safe receipt, unchanged production; APPLICATION NOT RUN.
New validity finding: grant-plan gate requires>6h, stricter than4h parent headroom;
initial apply before19 October03:33:41UTC, operational target before02:33:41.
Separate application/outage authorization and physical acceptance remain required.

[MESH-NL-RECOVERY-PREP-1,18.10](releases/2026-10-18-mesh-nl-recovery-prep-1.md):
PASS for explicitly authorized request preparation only. Exact request/CA hashes,
deployed-validator checks,13 negative cases and unchanged active-state readback.
Private materials retained for operator review; no offline-root signing, credential
installation or gateway start/reset. Time/headroom deadlines and next permissions
documented; STOP GATE respected, performance still blocked.

[MESH-NL-CREDENTIAL-LIFECYCLE-1,18.10](releases/2026-10-18-mesh-nl-credential-lifecycle-1.md):
Renewal root cause VERIFIED; recovery BLOCKED pending explicit authorization.
Working leaf/CRL schedule reached authority/grant operator gate03:11; offline-root
handoff did not complete, alerts were local-only. Authority/grants now expired too.
Exact deployed legacy source, timeline, bounded tests and expired-recovery plan;
no signing, restart, installation or policy change. UI84/performance gate preserved.

[MESH-PERF-2,18.10](releases/2026-10-18-mesh-perf-2.md):
BLOCKED physical baseline. Attached phone's UI84/native hashes verified; existing
pre-window batching reconciled. NL4h exit followed by expired leaf/CRL startup
rejections and systemd start limit; no restart. Includes metric coverage, bounded
physical run card and provider-aware IPv6 plan. No runtime tuning or claimed fix.

[MESH-PERF-ROOTCAUSE-1,18.10](releases/2026-10-18-mesh-perf-rootcause-1.md):
PARTIAL. Exact source/deployment audit, offline layer/window/TLS measurements,
IPv6 policy and NL egress blockers; no production tuning or claimed speed fix.
Includes reproduction and the gated physical experiment still required.

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
