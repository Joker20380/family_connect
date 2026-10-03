# Текущее состояние / Current state

## Android beta61 preparation — authorized source publication03.10.2026

Source commit `d93a01d` pushed to main. Local payload/field pytest9/9 and diff-check
PASS. Hosted Client builds [37138322487](https://github.com/Joker20380/family_connect/actions/runs/37138322487):
Linux, Windows, Windows compatibility and Android PASS, including emulator/runtime,
full carrier race, fresh restricted native/gateway and final ARM64 artifact gates.
phase0 `37138322534`, Linux control `37138322506`, Android readiness `37138322507`
PASS. Artifact11279129098 downloaded: archive SHA11adb429 matches GitHub digest.
Unsigned APK SHA7e3fb204 /49,604,500bytes; native bffb7c4d; gateway aca7c13a.
Local source/package/code61/ABI/native parity/16KiB alignment/privacy checks PASS
(1071 entries, no findings); expected unsigned rejection verified. Receipts are in
ignored `state-client-build/field61-ci/`; full hashes in dated report. No signed61,
owner installation, gateway rollout or public/invitation/catalog switch yet.
Public API watcher stopped after HTTP errors; final CI authenticated readback PASS.

User authorized commit/push and asked how to update the tester. Source metadata is
now beta61/code61; it is not yet signed, installed, deployed or publicly available.
Client CI now builds the pinned restricted arm64 native and gateway from the same
source, runs carrier race regression and packages an unsigned Friends artifact with
source/version/hash/native verification for offline signing. Existing Android
runtime and desktop gates remain enabled. Signing secrets stay off CI/server.
Previous metadata60 unsigned compile-only artifact must never be installed/published.
Public/invitation/catalog remains beta60; Linux0.2.11/Windows0.2.15 unchanged.
Next: offline signature, owner in-place acceptance,
controlled gateway deployment/fresh leases, then tester in-place update and one retry.
Do not uninstall/clear data or re-enroll; retain tester Support ID FC-YHQB-9VJN.
This release diagnoses session loss; no claim that the transport failure is fixed.

## FIELD terminal diagnostics — local implementation03.10.2026, no rollout

Implemented privacy-safe sessiondiag projection shared by gateway/native: first Mux
failure code/time, pseudonymous per-session tag, reliable terminal/retry counters,
ICE/signaling enums and Mux activity. Gateway now retains allowlisted broker reasons
and emits session_terminal; wholedevice no longer discards plane terminal category.
Android retains an allowlisted restricted_session snapshot, native state and separate
authorization_denied flag; first failure survives cleanup, new CONNECT resets it.
Polling updates native health before evidence. No auth/expiry/CRL/admission/retry-policy
weakening, new transport or lifetime changes. This fixes diagnostic loss, not yet the
underlying real-network session failure; FIELD remains BLOCKED.

Local checks PASS: full carrier `go test -race ./...` with live gates disabled;
228 Friends JVM tests/36 suites, lintFriends, focused field-release pytest4/4;
Android arm64 native build, gateway build and unsigned compile-only APK packaging.
Packaged native hash8771739a matches fresh output; DEX contains restricted_session.
Host binary SHA62e8de71; unsigned APK SHA488689f8. Unsigned APK deliberately retains
unchanged source metadata beta60/code60: not an install/update/release candidate,
never publish over accepted60. Full hashes/checks in dated report.
Native build first hit /tmp quota (including outside-sandbox retry), then PASS with
TMPDIR/output on project disk. No source/private artifacts removed. Gradle Python3.14
bytecode warning remains; proper release tooling/CI still required before delivery.

Nothing installed, signed, deployed or published; public/invitation/catalog beta60,
Linux0.2.11/Windows0.2.15 unchanged. No server/device mutation, commit or push.
Next: authorize source commit/push, fresh immutable release version and platform CI,
owner in-place continuity acceptance, narrow gateway deployment with executable-only
rollback, then one tester retry/correlated export. Previous lease deadlines now past;
revalidate/renew through existing mechanism immediately before live work, no bypass.
[Diagnostic contract, limitations and live procedure](testing/restricted-session-diagnostics.ru.md).

## FIELD second post-renewal attempt / fifth export — 03.10.2026 16:05UTC evidence

FC-YHQB-9VJN beta60/code60 repeated normal CELLULAR Auto: fresh local READY16:02:19,
connect start16:02:41.309UTC, AWG/TCP NETWORK, restricted CONNECTED16:04:05.758UTC
after84.449s with Family auth/broker/SESSION_READY. Lost16:04:20.901UTC after15.143s,
then INTERNAL/RESTORING→FAILED114ms. Capture retained until explicit disconnect;
latest ring WIFI/AWG CONNECTED16:05:15UTC. Counters DNS20/TCP4/peak3/protect145,
protect_denied0; activity counts do not prove completed destination traffic.
Same failure pattern twice, but durations30.227s then15.143s: no fixed30s-from-CONNECTED
cutoff demonstrated, nor attribution to RKN/provider/network/client. No new exported
AUTH/startup/import failure. Fresh local READY is not a new server ACK verification.
Prior diagnostic gap remains; no runtime fix/release or further blind retry requested.
Same exact2/3 policy; no admission/service/credential change. FIELD remains BLOCKED.
Gateway read-only16:08:37UTC: same PID3231001/NRestarts0; bounded11-event journal
confirms ACTIVE16:04:04.633890 and resources-closed/FAILED16:05:19.694063UTC.
The later gateway record is not the precise loss time or proof of initiator.
Both endpoints still omit terminal cause; no process restart observed.

## FIELD session-loss gateway correlation — 03.10.2026 15:54UTC

Read-only Amsterdam journal15:32–15:36UTC confirms bootstrap auth/room handoff,
dedicated family_auth15:34:12.378907UTC, ACTIVE15:34:13.488299UTC, then
dedicated_resources_closed15:34:52.100812UTC and FAILED15:34:52.103185UTC.
This correlates with tester CONNECTED15:34:13.877 and INTERNAL15:34:44.104;
cross-device timestamps alone do not prove which endpoint initiated failure.
Gateway still active/running, same PID3231001 since15:22:36UTC, NRestarts0.
Binary SHAe17e1fe7 matches accepted e808f50 build; broker entry/lifecycle/gateway
sources unchanged through HEAD9fde56d. Cleanup→FAILED order is consistent with
Mux session error, not process restart; exact lower-layer cause remains unavailable.
Confirmed diagnostic gap: bootstrap-broker discards the broker Code; gateway Run
returns Mux.Wait error without recording its category. Android also discards plane
termination reason and maps unhealthy state to generic INTERNAL. Existing logs
cannot distinguish transport loss, reliability exhaustion, protocol error or other
session failure. No evidence warrants timeout changes or weakened auth/retry policy.
15:54:24UTC file readback: gateway certificate expires16:22:33UTC, directory
16:17:36.983UTC, issuer04.10 14:13:53UTC; not a new loaded-TLS/CRL validation.
15:54:27UTC both device receipts expired; tester still last ACK15:27:38UTC.
Exact cohort2/3, inventory28/24/4, registration/invitation/Support/owner-grant/audit
fingerprints unchanged. No service restart, renewal, deployment, app or catalog change.
Next: bounded privacy-safe terminal-reason diagnostics at gateway/native/client,
targeted tests, then one controlled retry with fresh leases/receipts. Blind retries
not requested. FIELD remains BLOCKED; beta60/code60 unchanged.

## FIELD tester post-renewal restricted session — 03.10.2026 15:36UTC evidence

Fourth FC-YHQB-9VJN diagnostic export supersedes the pending post-renewal retry:
normal provisioning READY/ACK_RECEIVED15:27:38UTC, valid until15:42:05UTC
(server readback15:36:47UTC). Owner's last receipt remains expired; no owner refresh.
Tester normal Auto on CELLULAR started15:32:55.942UTC; AWG/TCP returned NETWORK.
At15:34:13.877UTC restricted reached CONNECTED after77.935s, with Family auth,
broker descriptor and SESSION_READY evidence. This proves post-renewal session
establishment, not sustained FIELD acceptance or successful destination transfers.
At15:34:44.104UTC,30.227s later, transport loss mapped to INTERNAL; RESTORING→FAILED
took117ms without another candidate attempt. VPN capture stayed open until explicit
disconnect15:35:16UTC. Snapshot counters: DNS44/TCP9/peak8, protect145/denied0;
these are activity counts, not proof of completed queries/downloads. Last snapshot
WIFI/AWG CONNECTED15:35:26UTC with DNS_PROBE_OK through15:36:42UTC.
Source inspection: AutomaticConnection.poll maps any unhealthy restricted engine
to INTERNAL; this is terminal in ConnectivityOrchestrator. Native session failure
or FriendsRestricted.denied can trigger it; export omits the distinguishing native
state/Mux terminal error. No new AUTH/startup/import failure in this export.
Cause of loss remains unresolved; do not infer a30s timeout, certificate expiry,
carrier block or crash. Next: privacy-safe gateway/native termination correlation
for15:34:13–15:34:44UTC; retain exact2/3 cohort, no expansion. FIELD remains BLOCKED.
Published/installed tester beta60/code60 unchanged; no runtime, service, catalog,
admission or security-policy changes. No additional host operation in this analysis.

## FIELD tester session failures / gateway renewal — 03.10.2026 15:23UTC

Third FC-YHQB-9VJN export confirms actual restricted attempts after normal AWG/TCP
NETWORK outcomes: READY, BOOT_CACHE_READY/BOOT_CARRIER_READY, then STARTUP_FAILED/AUTH.
Two failed connections15:15:35/15:16:54UTC, VPN capture retained in incident snapshot.
Four fully observed connection starts: two AWG connected (~7s), two failed (~62s);
last snapshot CONNECTED/AWG. No new NATIVE_VALIDATION_FAILED in this export.
Confirmed operational blocker: gateway certificate expired15:14:31UTC although
bootstrap process remained active. Exact per-handshake cause is not exposed by DIAG;
expiry is consistent with AUTH, not evidence that enrollment was revoked.
Existing credential-only renewal PASS15:22UTC: same keys/issuer/Family, native checks,
0600/service ownership, fresh bootstrap directory, actual loaded TLS certificate and
35s stable PID verified. New certificate expires16:22:33UTC, directory16:17:36UTC.
Ordinary sync delivered new directory; HTTP/AWG/TCP processes unchanged. No APK/code,
catalog, admission or grant change; exact2/3/no wildcard, inventory28/24/4 preserved.
At15:23:56UTC tester's last READY/ACK still predates renewal (expires15:25:02UTC);
owner's previous receipt expired. Both need normal fresh provisioning before further
restricted validation. Post-renewal tester retry/real restricted success not yet proven.
No third device/expansion; FIELD completion BLOCKED pending fresh receipts and retry.

## FIELD tester FC-YHQB-9VJN — READY,03.10.2026 15:11UTC

After tester-reported automatic clock synchronization, normal provisioning fetched
15:10:06UTC and server accepted the signed READY receipt15:10:07UTC. Readback15:11:19UTC:
READY / ACK_RECEIVED, provisioning/bootstrap PRESENT_VALID, orchestrator_usable=true,
failure_reason NONE, beta60/code60, revision1/minimum_crl1597, expiry15:25:02UTC.
No production/code/security-policy change was needed; clock correction followed by
successful retry supports the clock-skew diagnosis, without claiming measured offset.
Exact admission remains owner FC-4D8Q-REEG + FC-YHQB-9VJN,2/3, no wildcard.
Registration/invitation/Support mapping/owner grant/audit fingerprints unchanged;
inventory28/24 non-revoked/4 revoked. Owner also currently READY/ACK_RECEIVED.
Tester readiness blocker resolved; no actual restricted transport session proven yet.
Before real restricted testing, revalidate gateway credential/directory leases (last
recorded gateway certificate expiry15:14:31UTC), not just the client's readiness.
Published beta60 unchanged; DIAG-1A PASS. Broader FIELD lifecycle/network tests pending.

## FIELD-1 observation / exact tester admission — 03.10.2026

Earlier investigation below is historical; tester READY result above supersedes its blocker.

Same milestone; Stage5N CLOSED, DIAG-1A PASS. Published beta60/code60 unchanged
(source5c740f2, SHA8ee59352, signer67a90d1); beta59 remains unpublished.
Expired restricted authority/gateway material renewed through the existing protected
mechanism, without expiry bypass: delegation3, owner grant3, existing keys/identity.
Owner FC-4D8Q-REEG native import READY / ACK_RECEIVED at14:40:34UTC, valid until
14:55:27UTC; bootstrap/provisioning PRESENT_VALID, orchestrator usable. Subsequent
owner snapshot/authentication PASS: UID10283, identity/enrollment/activation/Support
unchanged. This is time-bounded readiness evidence, not completed FIELD transport use.
Explicit user-requested FC-YHQB-9VJN admission APPLIED at14:38:02UTC, audited0→1.
Exact cohort2/3: owner + this tester; no wildcard or other device. Inventory28/24
non-revoked/4 revoked unchanged; registration/invitation/Support mapping and owner
grant fingerprints unchanged by tester admission. Tester is active Android beta60;
existing identity/enrollment binding valid. Challenge/fetch succeeded14:39:42UTC,
but no accepted ACK at latest14:54:35UTC readback; fetched material expired14:54:23UTC
without a newer attempt. Owner independently refreshed READY/ACK14:53:09UTC, valid
until15:08:03UTC. Tester READY unconfirmed;
obtain tester diagnostics before claiming restricted runtime eligibility/success.
No forced Telemost, app/transport/catalog changes, new registration or expansion.
Real lifecycle/network cycles and failure classification remain pending.
Temporary owner instrumentation removed; installed production beta60/data untouched.
Tester-provided diagnostic export now identifies NATIVE_VALIDATION_FAILED at
14:55:44.414UTC; bootstrap NOT_USABLE. Same snapshot records CONNECTED/WIFI,
AWG SUCCESS and DNS_PROBE_OK, not a failed ordinary VPN session. New server
challenge/fetch14:55:46–47UTC follows the last exported event; ACK still absent
at14:58:23UTC. Do not conflate that new attempt with the earlier diagnostic event.
Native rejection predicate and missing negative-receipt delivery remain unresolved;
no production fix/expansion authorized by this evidence. Export privacy checks PASS.
Second tester export repeats NATIVE_VALIDATION_FAILED15:01:05.578UTC, AWG still
CONNECTED; server fetch15:01:08UTC, no ACK15:04:09UTC. Both observed pairs suggest
device clock lag (~2–3s); native rejects issued_at in the future, ACK validation
rejects observed_at before challenge_at. Server NTP synchronized. Clock skew is a
leading hypothesis, not yet a measured device offset/proven final root cause.
Next: verify/correct tester automatic date/time, retry normal provisioning and
confirm fresh READY/ACK; no validation relaxation or production code change.
[Current evidence and remaining work](releases/2026-10-03-field1-release-final.md#field-observation-and-explicit-tester-admission--2026-10-03).

## FIELD-1 beta60 — PUBLICATION PASS,03.10.2026

Same milestone; Stage5N CLOSED, DIAG-1A PASS. Exact accepted beta60/code60 published,
not rebuilt/resigned: source5c740f2, SHA8ee59352, signer67a90d1, Friends package.
Independent public download and owner Android download/hash/signer/reinstall checks
PASS. Signed v2 android-field/schema1/sequence1 catalog SHAf042beca: minimum1,
mandatory_after0, expires2027-01-01 13:34:01UTC. Client signature/expiry/replay negatives
PASS. Legacy v1 also offers60; unchanged beta51 checker executed on Android receives60
(not a downgraded installation). Owner60 Settings reports latest; locale-corrected
private instrumentation passes, removed afterward. Existing identity/auth/enrollment/
Support FC-4D8Q-REEG/copy/restart unchanged. Both invitation routes select60 with
matching CSP; desktop links and invitation logic unchanged. beta59 remains404.
Inventory28/24 non-revoked/4 revoked/28 Support IDs;1 known Android60,27 unknown.
Registration/invitation/mapping/grants/admission/audit fingerprints unchanged.
Owner-only1/no-wildcard/cap3; no FIELD widening or operator action. No claim all users
updated; unknown legacy/manual count. Readiness remains last-observed EXPIRED_ON_IMPORT,
not fresh READY; renew through existing provisioning before restricted FIELD tests.
Stop here; no next milestone. [Publication/rollback/evidence](releases/2026-10-03-field1-release-final.md#beta60-publication--2026-10-03).
Publication checkpoint741aac3 pushed to origin/main; no tag or unrelated changes.

## FIELD-1 beta60 publication gate — READY,03.10.2026

Same milestone; Stage5N CLOSED, DIAG-1A PASS on60. Signed ARM64 beta60/code60,
package com.familyconnect.app.friends, clean source5c740f2, SHA8ee59352, signer67a90d1.
Owner59→60 in-place PASS:UID10283/inode601521/identity/enrollment/activation/encrypted
readiness preserved; Support ID FC-4D8Q-REEG visible/copy/restart PASS. Auto→AWG7.265s,
AWG1.509s,TCP1.259s; HTTPS200 each. DIAG both failure snapshots/share/privacy PASS,
4719-byte export/0 findings; temporary instrumentation removed. Current readiness
receipt later EXPIRED_ON_IMPORT/ACK_PENDING after ordinary refresh; encrypted state
and decryption were preserved. No claim of fresh restricted READY or renewal.
Auto TCP production address omission corrected; existing dual-stack runtime PASS.
AWG scenario/cleanup PASS after correcting stale off-session failure observation;
profile-edit guard unchanged. Windows2022 Start Pending race confirmed; new-PID/
authenticated API bounded readiness passes without changing Windows production.
Final hosted source4963c7c: clients37123699385 ALL required jobs/steps PASS, including
Android runtime-control; Linux-control37123699363, wire37123699362, phase0/Docker/
index guard37123699367 PASS. Windows control37120091189 rerun PASS; its scoped
inputs unchanged from ef554e7. No newly skipped/waived release failure.
Public Android remains51;59/60 and signed-v2 remain unpublished. No catalog signing,
landing/deployment/admission/FIELD widening. One-owner/no-wildcard/cap3 not changed.
[Exact identities, runtime evidence and release boundary](releases/2026-10-03-field1-release-final.md#beta60-final-acceptance--publication-gate-ready).

## FIELD-1 platform diagnosis — artifact stop boundary,03.10.2026

Same milestone; Stage5N CLOSED and DIAG-1A PASS. Sequential investigation of the
Android Auto failure confirms a **production TUN address omission**, not an invalid
dual-stack emulator assumption. Hosted37120091287 log: Auto TCP replaces dual-stack
tun0 with tun1 containing only10.79.0.2/32 at11:43:38UTC; ::/0 remains routed but
fd79:fc::2 is no longer assigned. Socket.bind fails EADDRNOTAVAIL before IPv6 connect.
Manual TCP assigns both addresses and passes dual-stack traffic in the same run.
Required correction is in shared production AutomaticNormalEngine TCP setup, so
the accepted signed APK cannot remain the final release artifact after that fix.
Per explicit stop-on-artifact-change instruction, no source fix/rebuild/CI push was
performed; Manual AWG teardown and Windows2022 upgrade remain unresolved, not waived.
Existing59 SHA6d13720/signer67a90d1 and package/version reverified unchanged; prior
owner acceptance is retained evidence, not a substitute for this missing gate.
No production/admission changes, catalog signing, publication, landing edit or FIELD
widening. Required next decision: permit a changed Android candidate and renewed
acceptance, then resume the remaining sequential platform gates.
[Runtime evidence and exact stop boundary](releases/2026-10-03-field1-release-final.md#android-auto-runtime-diagnosis--artifact-stop-boundary).

## FIELD-1 fixture repair — PASS; release BLOCKED,03.10.2026

Same milestone, Stage5N CLOSED; owner and DIAG-1A acceptance remain PASS. Source-only
CI checkpoints pushed through2b3c997; no tags or release trigger. Explicit pinned
HTTP/sync/readiness/historical fixtures, complete public Docker source context,
Go1.26.0/module cache, system tools, isolated root-DAC plus unprivileged test runner
and Python3.13 operator ZIP namespace entries repair the original failures.
phase0 pytest+cargo, full Docker build/failover/auth/offline/revocation and index guard
PASS at2b3c997/run37120492530. Linux-control including full pytest/GTK/extracted bundles
PASS at ef554e7/run37120091177; Windows control37120091189 and Android wire37120091156
PASS. Client run37120091287 is **terminal**, not partially accepted: Linux/Windows
main jobs PASS, Android emulator FAIL, Windows2022 compatibility upgrade FAIL.
Android: Auto test binds an unassigned IPv6 address (EADDRNOTAVAIL); manual AWG reports
a profile-edit refusal during teardown. Windows: broker not Running after upgrade.
No assertion waived, skip added or production networking changed to obtain green CI.
Local full pytest1691 PASS/26 existing skips; root-DAC22 PASS; operator/provisioner21
PASS. beta59/code59 SHA6d13720/signer67a90d1 unchanged, no signed APK rebuild.
Read-only production verification:28/24 non-revoked/4 revoked,28 aliases,1 known59;
all registration/invitation/mapping/grant/admission/audit/HTTP/nginx fingerprints
unchanged; owner1/no wildcard/cap3 retained. Final publication gate **NOT READY**.
No catalog signing, public59 publication, landing change or FIELD widening.
[Repair evidence](releases/2026-10-03-field1-release-final.md#hosted-fixture-repair--2026-10-03).

## FIELD-1 Support delivery / owner acceptance — PASS,03.10.2026

Same milestone; Stage5N remains CLOSED. Explicitly authorized prerequisite deployed
09:52:52UTC: lookup-only HTTP source5e0008c, artifactef9f2faf; existing18086 service,
ordinary nginx device/status+support routes restored. No Android rebuild/networking
change. Owner receives the existing backfilled alias; visible/Copy/authenticated
device-status/process-restart stability PASS. Pulled installed59 still SHA6d13720,
same signer/UID10283/inode601521/identity/enrollment; READY/ACK and Auto preserved.
DIAG typed failure snapshots + MIUI share/export PASS;4695-byte bundle includes the
same alias, closed-schema/privacy0 findings. Test artifacts/helper removed.
Registration/invitation/alias/grant/admission/audit fingerprints unchanged;28 records,
24 non-revoked/4 revoked,28 aliases,1 known Android59/27 platform+version unknown.
16 live negative probes PASS; signed unknown status remains inactive200/no enrollment
by existing contract; Support access denied403. Owner1/no wildcard/cap3 unchanged.
518 focused Python PASS/0 skipped; whole-index guard repaired without weakening it.
FIELD-1-RELEASE BLOCKED by hosted CI; DIAG-1A PASS. Source-only checkpoint1b791c2
pushed after owner acceptance; no tags/release trigger/unrelated health work.
Index guard passes locally and hosted. Windows control/Android wire contract/Linux
client job PASS; phase0 and Linux-control broad pytest FAIL (missing artifact fixture
environment;7 failed/25 errors each), failover image14 collection errors. Remaining
Android/Windows client jobs still running at inspection; not claimed PASS. No CI
failure waived, no signing/publication. Public51 full-download SHA79a2d286 verified;
beta59/signed-v2 routes404. Unsigned min1/non-mandatory payload prepared only.
Final CI observations recorded locally; no FIELD widening.
[Delivery, owner checks, recovery and remaining gates](releases/2026-10-03-field1-release-final.md#support-http-delivery-and-owner-completion--2026-10-03).

## FIELD-1 owner acceptance continuation — PARTIAL,03.10.2026

Historical checkpoint; superseded by the completed prerequisite/owner checks above.

Same milestone; Stage5N CLOSED. Owner Redmi31ce63ba authorized. Existing signed
beta59/code59 SHA6d13720 installed **in place over private58 at09:14UTC**, no rebuild.
UID10283, firstInstallTime and ceDataInode601521 unchanged. Encrypted identity,
configuration/readiness bytes unchanged immediately after update; Keystore decrypts,
activation retained. Final identity still unchanged; normal product readiness refresh
on59 produced READY/PRESENT_VALID/ACK_RECEIVED, observed09:34:12UTC, expires09:47:58UTC.
Auto→AWG7.275s, AWG1.260s, TCP1.258s: connected, VPN present, test HTTPS200 each.
Five previously compiled owner-safe instrumentation tests PASS. On-device typed
CONNECTING/RESTORING→FAILED diagnostic snapshot tests and real MIUI share chooser
PASS;4675-byte bounded export passes closed-schema/privacy scan, no recipient/upload.
Test-generated diagnostics and separate instrumentation package removed; app kept,
Auto/disconnected, private acceptance components absent; pulled APK matches exact pin.
**Blocking:** Support ID unavailable, Copy disabled, stability cannot be verified;
Support HTTP delivery still undeployed. Existing device-status verification also
fails: route404, not proof of lost identity/enrollment. No server changes/deployment,
publication, CI advancement, admission widening, commit or push. Public catalog51.
FIELD-1-RELEASE BLOCKED; DIAG-1A PARTIAL (Support ID integration remains outstanding).
[Exact commands, failures and evidence](releases/2026-10-03-field1-release-final.md#owner-device-continuation--2026-10-03).

## FIELD-1-RELEASE-FINAL — Support ID candidate,03.10.2026

Previous preparation checkpoint; owner installation status is superseded above.

Stage5N CLOSED. Starting HEAD1790793; Support IDs are random registration aliases,
not credentials. Additive backfill/operator lookup and capped explicit FIELD actions
implemented locally; Android Settings shows/copies the bound alias, not Device Identity.
Unpublished beta59/code59 may be rebuilt; prior8229a36 candidate retained unchanged.
No connected owner Redmi; no install, identity reset, public catalog, landing switch
or push. Owner acceptance remains a release gate, not a new Stage5N gate.
Clean source5abc2da produces revised signed59 SHA256
`6d13720bc8cff25d51d95ff7453127577890bee881685a4a66c86fae163f2148`.
226/163 JVM,510 Python(0 skipped), lint0 errors/36 warnings, five native race/vet
packages PASS; APK nested scan1074 entries/0 findings,27 changed-source files clean.
RU backfill08:50UTC:28 aliases,24 non-revoked/4 revoked; platforms0 known/28 unknown,
versions1 known58/27 unknown; all13 preexisting table rows/admission bytes preserved.
HTTP Support delivery NOT deployed. Final owner ADB check still empty; runtime
copy/Auto/AWG/TCP/DIAG/share and identity preservation NOT RUN. Public51 unchanged,
admission1 owner/no wildcard, no publication/push. Whole-index negative PEM assertion
guard finding/hosted CI remain open. FIELD BLOCKED; DIAG-1A PARTIAL.
[Final evidence and remaining work](releases/2026-10-03-field1-release-final.md).

## FIELD-1-RELEASE + DIAG-1A — local foundation,03.10.2026

Stage5N CLOSED. Candidate source beta59/code59, not installed/published. Stage5N
checkpoint `ea25a5e`, no push. Signed Android discovery/private bounded diagnostics
added for validation. Live07:34UTC: public51,28 activated(24 non-revoked), one known
Android receipt(private58), other27 platform/version unknown; admission1/no wildcard.
Redmi disconnected; in-place59/identity/readiness/Auto/UX acceptance pending.
No server change or data reset; unrelated VPN-health work preserved.
[Release policy and remaining gates](releases/2026-10-03-field1-release-diag1a.md).

Final local59 source `b952c3b`, signed APK SHA256
`8229a36e8b176aa49346f3bf106f4f1229cb492a47c1c50e86593ddcb4c85a3b`, same beta signer.
224 app/163 overlapping control JVM PASS,249 Python PASS/1 fixture skip; five Go
race packages/vet PASS, lint0 errors/36 warnings; instrumented tests compile only.
Public manifest/DEX contain no private controls; nested APK scan0 findings.
Whole-index guard still flags unchanged negative PEM-header test literal;62 changed
files clean. Extra server-packaging test run lacks its required fixtures/Git context,
not a claimed pass. No connected Redmi: UID/identity/enrollment/readiness/Auto/export
runtime acceptance and hosted platform CI remain pending. Local manifest verifier,
foreground notice, ring/snapshot/export implemented; signed public59 catalog not issued.
FIELD-1-RELEASE PARTIAL; DIAG-1A PARTIAL. Primary public51/admission1 owner unchanged.

## 5N-PHYSICAL-RESTRICTED-REHEARSAL — PASS; STAGE 5N CLOSED, 03.10.2026

Финальная физическая проверка завершена на установленном private canary58, без
изменения кода, новой сборки/установки APK, ADB touch/key injection или redeploy.
HEAD до/после `911fea59e08e5ee8844852ae1e2834812632fbde`; ранее незакоммиченные
исправления hook/tests/docs и посторонние файлы сохранены. Нового commit/push нет.
Ручной CONNECT после подтверждённого override ON: AWG/TCP исчерпаны диагностикой,
BOOT-1/Family auth/Room Broker/dedicated session → restricted whole-device VPN →
CONNECTED за30.704s. Chrome: два HTTPS-сайта, четыре загрузки; TLS200/200;
Family DNS44/44, пик14 TCP-потоков. Маршруты всего Android user0 принадлежат Friends.
В измеренной области: дополнительных instrumented underlay DNS запросов0;
успешных TCP-соединений в одном корректном failure-probe0/1; UDP denied93,
IPv6 denied18, protect_ok148/protect_denied0. Это не глобальный packet capture.
Один контролируемый сбой: RESTORING→FAILED(BOOTSTRAP_UNAVAILABLE), VPN/маршруты
сохранены во всех17 наблюдениях, TCP-probe заблокирован. Позднее зарегистрирован
новый CONNECT и здоровая restricted-сессия; инициатор не установлен. Дополнительный
probe на этой здоровой сессии исключён из измерения fail-closed, не скрыт.
Очистка01:45UTC: override OFF в новом процессе, Auto, READY/PRESENT_VALID/usable,
ACK_RECEIVED; приложение отключено от VPN. Wi-Fi OFF, cellular ON.
Renewal не потребовался: gateway до01:57:34UTC, directory до01:52:37.529101038UTC;
проверка завершена внутри окна. NL READY/PID2804597/restarts0, RU/NL согласованы,
финальный CRL floor384; один owner. HTTP generation17/AWG/TCP неизменны,
финальные внешние200/400/400/400 PASS. Эти сроки не означают бессрочную готовность.
**Stage5N закрыт; дополнительных Stage5N gates нет.** Следующая фаза — 2–3 доверенных
field-canary и DIAG-1A параллельно; FIELD-1/DIAG-1/OPS-1/beta автоматически не начаты.
[Точные измерения, ограничения и очистка](releases/2026-10-03-5n-physical-manual-rehearsal.ru.md).
Ниже сохранены исторические результаты, включая прежние FAIL/BLOCKED.

## 5N-PHYSICAL-HOOK-FIX-AND-REHEARSAL — BLOCKED,03.10.2026

HEAD911fea5 unchanged; private hook fix/tests/docs uncommitted, unrelated work preserved.
Hook57 defect fixed privately: resolve actual package launcher, bound missing/start
failure, synchronously persist/read back deny flags, fsync ON/OFF receipt. No transport
or server-policy change.223 JVM tests PASS, lint PASS(0errors/37warnings), build/APK
checks and4 Python contracts PASS; live ON/OFF/fresh-process-OFF regression PASS.
Exact private **canary58 installed over57**, same signer/package/UID/data/identity;
real encrypted restart READY, both PRESENT_VALID, usable YES, ACK_RECEIVED.
One hardened credential renewal PASS: gateway expires03.10 **01:57:34UTC**, directory
**01:52:37.529101038UTC**; NL READY2804597/restarts0, RU consistent, normal services unchanged.
Override ON proved. Normal CONNECT tap denied by MIUI INJECT_EVENTS permission;
no manual CONNECT observed in announced120-second window. No restricted attempt,
transport-failure inference, injection bypass or retry. Final **override OFF** in fresh
process, Auto retained, app disconnected. Physical traffic/fail-closed checks NOT RUN;
no zero claims. Stage5N OPEN; same uncompleted physical acceptance, no new gate.
No deployment/restaging/migration/push/FIELD-1/DIAG-1/OPS-1/beta.
[Installed58 pins, regression coverage, exact input blocker and cleanup](releases/2026-10-03-5n-physical-hook-fix-and-rehearsal.ru.md).
Earlier installed-version/expiry checkpoints below are historical.

## 5N-PHYSICAL-RESTRICTED-REHEARSAL — FAIL, final attempt03.10.2026

Current checkpoint supersedes earlier installed-version/credential/uncommitted notes.
Task-only provenance commit `911fea59e08e5ee8844852ae1e2834812632fbde` from0615953;
unrelated dirty/untracked bytes preserved, no push. Exact private57 installed in place
over55; package/signer/UID/data inode unchanged. Real encrypted restart READY, TLS and
BootstrapDirectory PRESENT_VALID, usable YES, later ACK_RECEIVED.
One hardened credential renewal PASS; gateway expiry03.10 **01:27:17UTC**, directory
**01:22:20.767877784UTC**. NL READY2788718/restarts0, RU consistency PASS; HTTP/AWG/TCP
unchanged. No full deployment, migration, restaging or HTTP rollout.
Physical work stopped before CONNECT: existing private hook tries MainActivity, absent
from Friends manifest, causing ActivityNotFoundException at00:36:15UTC. Prepared=true
is not proof the override activated. Fresh process shows diagnostic preferences absent,
deny flags false, Auto retained; app disconnected. No hotfix/retry or identity reset.
Restricted path, Chrome/network/fail-closed and controlled-failure checks NOT RUN;
no zero-leak/bypass claim. Stage5N **OPEN**, no new gate or next phase started.
[Exact failure, installed pins, renewal and persistence evidence](releases/2026-10-03-5n-physical-restricted-rehearsal-final.ru.md).

## 5N-GATEWAY-RENEWAL-PUBLICATION — PASS, 03.10.2026

Starting/final HEAD `061595376fa65ae38725ed75baac769d71623d92`, unchanged; focused
publisher/tests/runbook edits remain uncommitted. Exact defect reproduced with real
isolated DAC: root's `restricted_sync.atomic` creates root:root0600 temp; rename
replaces the service-owned inode without inheriting its ownership. New privileged
publisher applies observed UID/GID/mode, fsync and service-user read-open **before**
rename; independent final readback and durable safe receipt. Ordinary sync unchanged.
95 local tests PASS/26skip; all41 isolated root/DAC tests PASS, including the22
root-only cases skipped locally; actual pinned native crypto publication check PASS.
One live renewal02.10 23:54:48UTC: Python/native PASS; gateway.json remains
family-restricted:family-restricted (979:979),0600, parent root:family-restricted01770.
Same Family/issuer/gateway/sole owner; no new admissions or floor reset.
**Gateway expiry03.10 00:54:48UTC**, fresh directory expiry00:49:51.385316605UTC.
NL READY, stable PID2771523/restarts0 and served certificate exact-match PASS;
unit remains active/disabled. Initial read-only observer used data ALPN; corrected to
existing control `http/1.1`, with no repeat issuance/publication/restart.
Minimum RU sync PASS;00:09:45UTC RU/NL authority/CRL/floor201/directory consistent.
HTTP generation17/nginx/AWG/TCP unchanged; external200/400/400/400 PASS.
Canary57 hash/version/signer reverified unchanged, **not installed**; no Android or
physical rehearsal action, server binary redeployment/restaging, push or next phase.
Stage5N remains OPEN pending the existing physical gate in a separate task.
[Exact contract, regressions, live evidence and expiry](releases/2026-10-03-5n-gateway-renewal-publication.ru.md).

## 5N-PHYSICAL-RESTRICTED-REHEARSAL — BLOCKED, 03.10.2026

HEAD `061595376fa65ae38725ed75baac769d71623d92`, live02.10 23:12–23:29UTC.
Existing production/readiness acceptance from attempt17 remains historical PASS;
no full deployment, migration, HTTP switch or server artifact staging was repeated.
Private same-package/signer `0.1.18-canary57-physical`/57 built from exact committed
export with packaging-only debug overlay: existing exhaustion Activities/hook, no
transport/BOOT-1/TLS/TUN changes. 218 unit tests, lint and APK checks PASS; signed,
**not installed/published**. Redmi remains55; identity/data untouched; override never enabled.
Short-lived gateway renewal required: Python/native authority PASS, same sole owner,
delegation2/grant2/identities. This session's refresh adapter omitted the accepted
service-owner-preserving publish step: live gateway.json became root:root0600 while
bootstrap runs as family-restricted. Reload exited1 before READY (`service_unhealthy`).
Evidence persisted; stopped failing unit and rolled back previous certificate with
correct service ownership, retaining advanced CRL history. Restoration bootstrap
active PID2757605/restarts0 and fresh directory; RU/NL floor125 at23:29UTC. HTTP18086,
nginx generation attempt17, AWG/TCP PIDs unchanged; external200/400/400/400 PASS.
**Restored gateway expires02.10 23:37:09UTC**; active PID is not proof of later validity.
NL unit is active but **disabled**, not enabled. Physical acceptance NOT RUN, no zero
leak/bypass claim. Stage5N OPEN; no new gate, automatic retry, push or next phase.
[Build pins, exact failure/rollback and remaining physical checks](releases/2026-10-03-5n-physical-restricted-rehearsal.ru.md).

## 5N-PROV-1 attempt17 — DEPLOYED / PHYSICAL BLOCKED, 03.10.2026

Authorized HEAD `061595376fa65ae38725ed75baac769d71623d92`; live02.10UTC.
Current accepted pins/source inventories/isolated checks and installed canary55 PASS.
Existing RU9files/7,806,192B and NL3files/5,683,055B READY freshly verified and reused;
additional runtime/operator inputs staged with hardened receipts only. Schema14 retained.
Same sole owner/Family/identities, delegation2/grant2; Python/native authority PASS,
CRL28→29→30 at full committed NL/RU acceptance. Direct B–E and fixture F/G PASS;
external200/400/400/400/403 PASS. Real app challenge/fetch200/200, READY/PRESENT_VALID/
usable and authenticated ACK_RECEIVED; fresh encrypted-state restart receipt PASS.
Only after OWNER_PRODUCT_READY did HTTP commit and old18084 retire. Current18086
generation`attempt17-0615953`, sync timer and NL bootstrap active;18085/AWG/TCP unchanged.
22:55UTC RU floor60; fresh valid NL directory, latest actual app READY ACK retained.
Wi-Fi OFF/cellular ON; Friends VPN observed, but not restricted TUN. Normal exhaustion
and BOOT-1→dedicated whole-device flow unproven; accepted55 has no debug exhaustion
Activity. No APK/private-state workaround or shared-normal-path disruption. Restricted
Chrome/TLS/DNS/TCP/leak/fail-closed acceptance NOT RUN. No required deployment/product
gate failure or rollback; **Stage5N OPEN**, not closed by readiness alone.
Post-use extra diagnostic: RU operator staging now contains generated `__pycache__`;
strict inventory inspect rejects it, while all9 original pins/modes are unchanged.
Pre-use READY remains valid evidence; do not claim that consumed directory is currently
reusable READY. No cleanup/restage or new acceptance gate. Historical15/16 causes UNKNOWN.
No version/public distribution change, push, FIELD-1/DIAG-1/OPS-1/beta. Gateway expires
02.10 23:37:09UTC; later continuation requires fresh existing-policy state, not stale ACKs.
[Exact pins, timestamps, physical boundary, receipts and rollback path](releases/2026-10-03-5n-prov1-attempt17.ru.md).

## 5N-STAGING-TRANSFER-RELIABILITY — historical localization unresolved, 02.10.2026 UTC

Full requested gate **FAIL** only because attempt16's exact RU/NL timeout layers remain
unproven: old opaque SSH receipts do not distinguish authentication/reception/remote work.
No-write exact source-assignment probes completed within45/50s; no causal claim of slow
network, inadequate timeout or overlapping bulk transfers. New operator-only atomic
staging commit `5b59461` has19 focused tests PASS; both authorized inert bundles READY:
RU9 files/7,806,192B/17.858s; NL3 files/5,683,055B/14.332s. Independent remote hash,
inventory and durable receipt reinspection PASS. Services/PIDs/restarts and RU ingress
unchanged; restricted inactive, authority/DB/Redmi untouched. Existing artifact pins unchanged.
Broader60pass/13skip/2preexisting pin failures; task guard/diff check PASS. No push.
Stage5N stays OPEN. STOP; no full retry/FIELD-1/DIAG-1/OPS-1/beta. Use the new receipt-gated
staging contract in any separately authorized future retry; do not resend artifacts as
Python source literals. [Evidence, limitations and runbook](releases/2026-10-02-5n-staging-transfer-reliability.md).

## 5N-PROV-1 attempt16 — DEPLOYMENT FAILED / ROLLED BACK, 02.10.2026

Authorized9b3ec45 retry: current HTTP/readiness/sync pins+inventories PASS, exact installed
canary55/package/signer PASS; receipts schema14 retained, sole owner/free18086/baseline
200/400/400/404 PASS. Protected RU/NL backups prepared. RU JIT Python validation PASS,
same delegation2/grant2/identities; CRL27→28 retained. Operator staging45s and NL native-
checker transfer50s SSH timeouts; readback found no staged operator or native acceptance
receipts. No replay/hotfix, restricted startup, ingress switch or real-owner request.
Failure fsynced before21:13 rollback; restricted RU/NL inactive/disabled, original
normal services/handler/nginx/ports unchanged, final200/400/400/404. Receipts table stays
empty/present; grants/devices/invites unchanged. Live chat_sequence changed, not attributed
or restored. Phone only package/APK verified; no install/launch/restart/rehearsal/traffic.
Stage5N remains OPEN; native/NL/RU/HTTP/product/persistence/physical acceptance not reached.
Historical attempt15 cause still UNKNOWN; no push/FIELD-1/DIAG-1/OPS-1/beta.
[Exact pins, failure/rollback evidence and remaining checks](releases/2026-10-02-5n-prov1-attempt16.ru.md).

## 5N-PROD-READINESS-SCHEMA — PASS, 02.10.2026

Explicit migration-only authorization executed on RU Friends `friends-access/access.db`:
one pinned `control.friends.readiness_receipts.migrate` call,20:48:50UTC, COMMITTED35.893ms;
online SQLite backup retained0600 on RU. Receipts table absent→present/empty; schema
cookie13→14, user_version0 unchanged. Exact11columns/two unique indexes validated;
all existing rows/schema unchanged within transaction, final counts match baseline.
Ordinary external baseline/post200/400/400/404; API/AWG/TCP PIDs/restarts and handler/
nginx hashes unchanged, restricted RU/NL inactive, routes404. No observed probe failure;
no sample overlaps the35.893ms transaction, so zero downtime is not claimed.
Local commit/rollback/idempotence checks PASS; focused125 PASS/6skip, configured JVM↔Python23 PASS.
No runtime/authority/ingress/Redmi/sign/install/commit/push. Additive table is forward
production state: do not restore old full DB merely to remove it. Schema prerequisite
now satisfied; attempt15 historical cause still unresolved and PROV-1 stays stopped/open.
Canary55 remains compatible;56 not required for functionality. Earlier forensics absence
below is a historical observation, superseded only for current schema state.
[Backup, exact timing/schema and rollback boundary](releases/2026-10-02-5n-prod-readiness-schema.md).

## 5N-PROD-SCHEMA-FORENSICS — HISTORICAL CAUSE UNRESOLVED, 02.10.2026

Read-only RU schema20:13:28UTC: user_version0, SQLite schema cookie13, no migration
ledger; `restricted_readiness_results` absent. Existing attempt15 pre-backup18:40:27UTC
also lacks it, with identical relevant schema. This is not a failure-time snapshot;
18:45:03.869 historical absence remains unproven. Required migration is unnumbered
`readiness_receipts.migrate`, introduced by `e817380`; explicit runner exists in pinned
sync archive but is absent from the reused attempt15 activation sequence. Generic
runbook already calls migrate; upgrade/preflight enforcement was missed.
Observed-prerequisite-schema synthetic proof:503/CORRELATION_SCHEMA_UNAVAILABLE→exact
existing migration→200; repeated migration preserves rows/schema, replay403.99 tests
PASS/4 optional native skips. Additive migration reviewed, NOT applied; current missing
schema remains a prerequisite for any future retry. Canary55 compatible;56 not needed
for functionality. No production changes, authority/runtime/ingress/service/device action,
sign/install, commit or push. [Evidence, safety/locking and bounded future scope](releases/2026-10-02-5n-prod-schema-forensics.md).

## 5N-REAL-OWNER-CHALLENGE-503 — BLOCKED, local only, 02.10.2026

Android-generated exact wire reaches the real Python HTTP handler: current synthetic
schema200; missing receipt table503 (`correlation_store/CORRELATION_SCHEMA_UNAVAILABLE`);
existing explicit migration restores200. This does NOT establish attempt15's cause:
retained local evidence lacks its backend reason/schema snapshot. No wire mismatch or
circular ACK dependency found. Safe server/client classification and permanent JVM↔Python
golden regression added; no speculative authorization/schema behavior fix. Clean-source
artifact/test results are tracked in the [task report](releases/2026-10-02-5n-real-owner-challenge-503.md).
Clean server builds from `ad17db7` and unsigned local Android56 from `a10a9c4` are
[pinned with inventories](releases/2026-10-02-5n-real-owner-challenge-503-pins.json), not deployed/signed/installed.
APK SHA256 `5ca1d29101df529cce197e5eeb82f231b50e3f4fc76c8835ba12fdad0c2122b0`.
App218/control163 JVM PASS; assemble/lint PASS (0errors/37warnings); focused Python151
PASS/12skip; final three-artifact/native regression171 PASS. Whole-index source guard retains one unchanged pre-existing test-fixture
finding; task files pass. Production503 remains unproven, no speculative cause fix.
No production/device access, authority refresh, deployment, ingress change or push.
Installed55/public51 remain last documented, not reverified. PROV-1 remains stopped;
FIELD-1/DIAG-1/OPS-1/beta are not started. Need retained sanitized failure-time evidence,
not another production attempt, before claiming a proven cause/fix or PASS.

## 5N-PROV-1 attempt15 — DEPLOYMENT FAILED / ROLLED BACK, 02.10.2026

Explicitly authorized retry of exact HEAD `014e6f945cce2d9956423d285492c8e315840d29`
and all four accepted pins. Fresh source/inventory/device/port preflight PASS;
Python/native authority, durable normal baseline, NL authoritative READY, full RU
sync, direct candidate B–G (F/G fixture only), ingress/external A–E all PASS.
Delegation2/grant2 unchanged, same sole owner; CRL25→26→27 retained, no TTL change.

Private canary55 installed over54 at18:45UTC; final APK/hash/package/signer verified.
Real app restricted challenge returned503 at18:45:03.869UTC; readiness fetch and
authoritative device READY/ACK were not established. No UI gesture gate, owner key
access, hotfix or retry. Failure fsynced before rollback; old ingress restored/proved
and drained before candidate stop18:47:56UTC. Restricted RU/NL stopped/disabled;
final18:48 readback proves ordinary200/400/400/404, original18084/18085 PIDs,
unchanged normal services/handler/nginx/ledger, free18086. No429/502 in scoped checks.

Stage5N production provisioning/recovery remains **OPEN**, not closed: concrete app
challenge503 blocks existing acceptance; cause not established and no new gate added.
Device provisioning/bootstrap/effective expiry, restart, local rehearsal and user
traffic/fail-closed checks remain unverified or NOT RUN. Public beta51/invitation
artifacts not changed or reverified. STOP; no push, FIELD-1, DIAG-1, OPS-1 or beta.
[Exact pins, evidence, rollback paths and remaining checks](releases/2026-10-02-5n-prov1-attempt15.ru.md).
Earlier build-only/attempt14 checkpoints below are historical, superseded here.

## 5N-READINESS-ACK-ARTIFACT-REFRESH — PASS local, 02.10.2026

Clean exact source `a24f090d7468dce6183122616117a4e1edaadd3f`; all three old server
artifacts classified A (bundled source changed), rebuilt with unchanged builders
and explicit manifests. Every bundled tracked/native input equals HEAD; no waiver.
New HTTP SHA256 `7ef821a824914b35490d3d371ae4b1722a8900d99cf7b16dbacdd3c5c0af105a`;
readiness `45d35703edeea3cbb1cedcd472ad3b009f15888a6a94c83453e06fce1bd57c96`;
sync `0237527cc0fbe6ea5498b0f1d2025894ae3f347c4bb26b4da9f702bfc25f4f1c`.
HTTP/adapter repeat builds byte-identical; sync exact retained bytes pinned.
366 focused tests +2 historical pinned regressions PASS. Exact offline sync→directory
→HTTP→native validated simulated result→authenticated ACK→read-only inspection PASS,
**server_contract_fixture only**, not physical owner evidence. ACK schema errors use
existing bounded503; unauthorized/replay/stale use403. No production code change.

Canary55 APK/hash/package/code55/signature unchanged and verified; no rebuild/install
or Redmi access. No production access, authority refresh, service deployment, push,
PROV-1 retry, FIELD-1, DIAG-1 or OPS-1 by this task. New pins are prepared, NOT deployed.
Safe real device READY + correlated server evidence remains the next owner gate;
ACK_PENDING preserves local READY but cannot invent owner acceptance. UI supplemental.
[Full paths, inventories, contract and tests](releases/2026-10-02-5n-readiness-ack-artifact-refresh.ru.md) ·
[Machine pins](releases/2026-10-02-5n-readiness-ack-artifact-pins.json).

## VPN read-only snapshot — 02.10.2026,18:05–18:06UTC

Friends access:28 activated devices/24 non-revoked/4 revoked;82 invitations/28 used.
Compared with01.10 17:43UTC:+1 device/+1 non-revoked. NL AWG:22 peers,3 recent
handshakes/transferring,11 handshakes<24h; RU10 peers,0 recent/transferring/24h.
Friends TCP established0 on both. These are devices/peer observations, not people/DAU.
CPU short samples NL6.8–8.43%,RU22.03–26.67%; available RAM555/1063–1094MiB;
disk used26.1/69.3%. No short-sample CPU/RAM saturation. NL daily sar vda await
138.83ms remains a concern despite1.08ms in the15s sample. Worker Docker unhealthy,
but50 observed cycles in last15min exited0; outbox not verified. Ordinary AWG/TCP
active with unchanged start dates; access API start02.10 09:33:26UTC, cause not
investigated. Public monitor HTTPS/TLS PASS. No service/version/deployment changes.
Latest documented restricted attempt14 remains rolled back; canary55 built only,
installed54/public51 not reverified. [Evidence and remaining checks](releases/2026-10-02-vpn-health.ru.md).

## 5N-DEVICE-READINESS-RECEIPT — PASS local, 02.10.2026

Starting HEAD `d5105e8c4f44aa4dac2153370800d98a229bc7d1`; implementation/build source
`e81738083457912da5b1032c45cfbe92bad112cc`. Real product READY now follows native
credential/directory validation, atomic encrypted import/readback and the actual
Orchestrator credential-usability predicate. Versioned safe private durable receipt,
authenticated control HTTPS ACK, owner-bound server readback and restart revalidation
replace critical UI-swipe acceptance. HTTP200 or a saved old receipt alone is not READY.
ACK failure leaves local readiness intact and server evidence ACK_PENDING/UNKNOWN.

Private `0.1.18-canary55-receipt`/55 arm64 is **built and signed only, NOT installed or
published**. Same Friends package/beta signer; update-compatible with installed54.
APK SHA256 `680a21f60e69cb62d2c7a70be07234b34196e178f0207ed69cb4b422b7bc6247`.
215 app JVM +160 overlapping control JVM tests PASS;187 Python integration tests,
2 historical pinned regressions,31 adapter packaging tests PASS; native tests and
fresh JNI build PASS; Gradle assemble/test/lint PASS (0 errors/37 existing warnings).
No physical/Keystore instrumentation or device installation in this local gate.

Production/authority/services unchanged and not accessed; attempt14 remains rolled
back, installed54/public51 remain last documented states, not reverified here. Existing
four attempt14 artifacts remain immutable. New ACK API needs separately reviewed/pinned
server bundles before any future authorized deployment. No automatic PROV-1 retry,
FIELD-1, DIAG-1, OPS-1 or push. [Contract, artifact, tests and remaining acceptance](releases/2026-10-02-5n-device-readiness-receipt.ru.md).

## 5N-PROV-1 — attempt #14: owner observation failed / rolled back, 02.10.2026

**5N-PROV-1 = DEPLOYMENT FAILED / ROLLED BACK.** Explicitly authorized attempt14
used accepted HEAD `d5105e8c4f44aa4dac2153370800d98a229bc7d1`; all four requested
artifact hashes and source inventories PASS. No rebuild, source/harness hotfix,
additional admission, identity-key access, commit or push. Retained dirty work preserved.

One physical Redmi Note9Pro/Android12/arm64 and field52→canary54 signature compatibility
verified before production. JIT16:41UTC keeps delegation2/grant2/same issuer/gateway/
sole owner; CRL23→24→25. Python/fixed native authority, authoritative NL READY/stable
PID/directory, RU isolated --check/full sync including negatives and final readback PASS.
Pinned closed adapter PASS: direct B–E400/400/400/403; controlled F/G200/200 with native
validation, **server_contract_fixture only**. Candidate18086/PID2847336 owned loopback;
nginx switched16:42:32UTC with old18084 alive; external A–E200/400/400/400/403 PASS.

Accepted private canary54 installed in place16:43:11UTC, no uninstall/data clear.
App launch is followed by server-side challenge/readiness200/200, but the readiness
dialog/real-owner correlation and atomic cache import were **not observed**. ADB
`input swipe` returned255 during UI collection; no retry or cause/crypto-defect claim.
OWNER_PRODUCT_READY not established. Failure persisted; old routing proved200/400/
400/404 and drained before candidate stop16:44:01UTC. Restricted RU/NL stopped by
16:45:45UTC. Original18084/PID1566654 and18085/PID1908885 remain; normal services,
handler/nginx and ordinary registration/grant ledger unchanged. No429/502 in17
serialized public operator probes; no broad availability claim.

Final Redmi readback16:47:47UTC confirms installed canary54 exact hash/signature and
running Friends; activation/identity/cache readiness not separately verified. No
restart/rehearsal/Chrome/DNS/TCP/leak/fail-closed acceptance. CRL25 history retained,
expiry16:56:38UTC; gateway leaf17:41:06UTC, delegation/grant03.10 11:54:56UTC. Expiries
are evidence, not renewed readiness; after rollback cached restricted seed is unusable.
Public beta51/invitation downloads unchanged, not reverified. No FIELD-1, DIAG-1,
OPS-1 or beta rollout. STOP; no automatic attempt15.
[Exact pins, chronology, rollback and remaining checks](releases/2026-10-02-5n-prov1-attempt14.ru.md).

## 5N-HTTP-READINESS-ADAPTER-PACKAGING — PASS local, 02.10.2026

Attempt13 reproduced before source edits: missing `provisioning`, transitive importer
`control.friends.restricted:21`. The HTTP archive contains the module; the outer
operator incorrectly relied on `runpy`'s temporary archive search path and an
extracted test recipe. No backend/service defect or main-artifact rebuild required.

Closed13-source adapter + pinned native delivery checker built twice from clean
commit `037331f8aee029e22312b565f5d025d50f284e0b`; all four bundle files identical.
Isolated outside-checkout startup/config, controlled B–G400/400/400/403/200/200,
local candidate B–E/current authority --check and existing transaction callback PASS.
74 focused tests PASS,9 unrelated integration cases explicitly deselected, no skips.
Each manifest dependency removal fails; missing-module/importer/stack classification
is now durably redacted before adapter failure. No PYTHONPATH/sys.path workaround.

Accepted sync/HTTP17/25 inventories remain byte-compatible; original sync/HTTP/APK
hashes unchanged. No production, authority refresh, Redmi, Telemost, Android build,
install/distribution or push. Last production state remains the documented resumed
attempt13 rollback, not freshly observed. Actual owner F/G and physical gates remain
NOT RUN. [Adapter report and pins](releases/2026-10-02-5n-http-readiness-adapter-packaging.ru.md)
and [supported runtime/runbook](../deploy/friends/restricted/READINESS_ADAPTER.md).
STOP: no automatic attempt14, DIAG-1, regional beta or FIELD-1.

## 5N-PROV-1 — resumed attempt #13: readiness adapter failure / rolled back, 02.10.2026

**5N-PROV-1 = DEPLOYMENT FAILED / ROLLED BACK.** This verdict concerns the
explicitly resumed production execution only. The earlier15:05 no-device stop
was solely a pre-production block: no production failure or rollback then.

Exactly one authorized physical Redmi Note9Pro/Android12/arm64 verified. Installed
field52/code52 signer matches accepted canary54; in-place upgrade needs no uninstall
or data clear. Fresh HEAD/APK/JNI/signer and sync/HTTP17/25 inventory/source checks
PASS at `4bb53b0605c2c898b6a3feca6ee15fd34b943a94`. Reused verified current native
checker; no accepted artifact rebuild or application/committed harness source edit.

JIT15:31:32UTC preserves delegation2/grant2/same identities/sole owner and renews
CRL21→22/gateway leaf. Live Python/native prerequisites PASS. NL authoritative
READY/directory/stable-process gate PASS; journal timeout non-gating. RU isolated
--check and full committed acceptance PASS, including both negatives; CRL22→23.

Candidate18086 fresh free/bind gate PASS; owned loopback PID2638484 verified at
15:32:49UTC. The scoped operator's readiness callback raised `ModuleNotFoundError`
before controlled F/G or direct B–E probe receipts. Exact missing module/traceback
was not captured: not a proven backend HTTP/TLS failure. Failure fsynced before
candidate stop; ingress never switched. No live hotfix or retry.

Restricted rollback confirmed15:35UTC; candidate unit removed/preserved as evidence,
NL seed/export/authorization disabled, RU sync disabled. Original18084/PID1566654,
18085/PID1908885, normal service metadata, handler/nginx and ordinary ledger unchanged.
Baseline/final200/400/400/404 PASS; no429/502 in those8 resumed ordinary requests.
DB/runtime/NL CRL23 retained (expiry15:47:17UTC), RU stage22 historical. No reset.
Redmi remains field52 at15:36:45UTC; canary54 not installed/publicly distributed.
Owner F/G/import/restart/rehearsal/traffic/fail-closed gates NOT RUN; no FIELD APK.

[Exact resumed evidence, pins and remaining gates](releases/2026-10-02-5n-prov1-attempt13.ru.md).
STOP: separately scoped offline readiness-adapter investigation before another
authorized production execution. No push, DIAG-1, distributed beta or FIELD-1.

## 5N-ANDROID-CANARY-BUILD — PASS local, 02.10.2026

Private **0.1.18-canary54-prov1 / code54**, `com.familyconnect.app.friends`, built
and beta-signed from clean Git export `4bb53b0605c2c898b6a3feca6ee15fd34b943a94`.
Includes the accepted product-prewarm protocol helper and safe diagnostics.
Actual Gradle `assembleFriends`, `testFriendsUnitTest`, `lintFriends` PASS:
204 app JVM tests; separate control suite149 (overlapping, not353 distinct tests);
lint0errors/37warnings. Fresh arm64 AWG/TCP and restricted JNI match APK bytes.
The broken Python symlink was stale ignored Chaquopy venv state targeting a removed
temporary Python3.10, not a source defect. Preserved it and regenerated via the
existing `fcBuildPython` contract; no runtime/build-source change or new commit.

APK SHA256 `f81920412089bd87950d8055daf883b754fea3323b412ccb28b0c092b9a909c6`.
Same beta signer and higher version establish in-place compatibility against the
retained field52 inventory, **not a fresh device observation**. No install, device
access, authority renewal, production service operation, public release or push.
Public beta51/download links remain unchanged and unqueried. Production remains
the last documented attempt12 rollback, not rechecked. This is not a FIELD APK.
[Exact artifact, provenance, tests and reproducible setup](releases/2026-10-02-5n-android-canary-build.ru.md).
STOP: deployment attempt13/physical acceptance needs a separate authorization.

## 5N-OWNER-PROOF-HANDOFF — PASS local, 02.10.2026

The attempt12 operator-proof blocker is resolved by an acceptance-phase split,
not credential access. Pre-switch: isolated exact-archive synthetic F/G crypto
fixtures plus live candidate B–E/current authority. Post-switch: external server
A–E, then **actual Friends product prewarm F/G/native validation/atomic import**.
`SERVER_CANDIDATE_READY` is not `OWNER_PRODUCT_READY`; commit/old-generation
retirement requires correlated product acceptance. Owner failure persists safe
evidence and restores routing before stopping the candidate; old18084 is retained.
No operator-owned real Device Identity proof, export or signing oracle exists.

Android retains the normal protocol and cache policy; a package-private protocol
extraction enables JVM tests. Minimal support-safe observation adds per-request
random IDs, fixed outcome categories and revision/expiry metadata to existing
readiness diagnostics. No manifest/API signing endpoint, forced refresh, reenrollment
or cache injection. Fixture receipts and actual-product receipts have distinct
classes; native delivery validation and backend invalid/revoked/non-canary rejection
remain intact.197 focused Python tests,38 additional source/acceptance guards and
149 JVM tests PASS, no skips;112 current Android Java sources compile with SDK35.

Source-only local gate from `a02b82ec70269cd1e5486a26172b7a04d347cb7a`; unchanged
accepted HTTP/sync archives tested, not redeployed. No authority refresh, service
operation, live Telemost, Redmi access, APK version/build/install/distribution or
push. Production remains the last documented attempt12 rollback, **not rechecked**
here; history2/2/21 is historical state, not a current validity claim. A future
authorized rollout needs an in-place canary containing the new observation hook;
previously built canary53 does not contain it. No new FIELD APK.
[Contract](../deploy/friends/restricted/OWNER_PROOF_HANDOFF.md) and
[local evidence/limits](releases/2026-10-02-5n-owner-proof-handoff.ru.md).
STOP: no automatic attempt13, DIAG-1, regional beta or FIELD-1.

## 5N-PROV-1 — attempt #12: prerequisites PASS, HTTP proof unavailable, 02.10.2026

**5N-PROV-1 = DEPLOYMENT FAILED / ROLLED BACK.** Source
`a02b82ec70269cd1e5486a26172b7a04d347cb7a`; committed checker fix rebuilt from that
clean Git export, SHA256 `a1df5f88a103340a6ba9d67ae8842147afd99d430fba6b30b8ba7b212373ce90`.
40 focused Python/native compatibility and receipt tests PASS, no skips; exact
sync/HTTP inventories17/25 and isolated imports remain compatible. No runtime fix.

Live Python and fixed native authority prerequisites PASS. Still-valid same-key
delegation2/owner grant2 retained, expiry03.10 11:54:56UTC; JIT CRL19→20 and gateway
leaf renewal, then accepted RU sync20→21. NL authoritative bootstrap PASS: provider
READY, stable PID, gateway-bound valid BOOT-1/current timestamps/final readback.
Journal timeout is non-gating. RU isolated --check, blocking oneshot, fresh CRL/DB
floor21/current directory, generic-shell and stale-CRL rejection all PASS.

Stopped before HTTP candidate: required real-owner signing callback for mandatory
direct/external G was not available to this operator. Accepted `Session.matrix`
requires that callback; existing Android proof stays inside the app. No key
extraction, synthetic identity, skipped G or live proof-bridge hotfix. This is an
operator integration prerequisite failure, **not an observed HTTP/provider/TLS
failure**. Redmi connection was reported by the user after rollback was initiated;
USB availability does not supply that callback. No phone operation was performed.

Durable failure receipts precede restricted-only rollback13:25:19–22UTC. RU sync
and NL bootstrap disabled/inactive, NL authorization/export removed. Normal handler,
ingress18084, registrations/invitations/grants and normal service metadata unchanged;
AWG/TCP active/unrestarted.18085 untouched;18086 free at entry/final ss+bind checks,
never started. Baseline and final200/400/400/restricted404 PASS at1.1s pacing; no429
or502 in those eight responses. Direct B–G/external A–G, owner fetch, physical
readiness/restart/rehearsal/traffic/leak gates NOT RUN; no FIELD APK produced.

Final authority history: RU DB/runtime and NL signed/profile CRL21, RU historical
stage CRL20 (not current); delegation2/grant2 unchanged. CRL21 expires02.10
13:37:13UTC, gateway leaf14:21:26UTC. Never restore stage20 over current21.
[Exact result, protected evidence and remaining prerequisite](releases/2026-10-02-5n-prov1-attempt12.ru.md).
No app version/install/distribution change, commit or push. STOP: no automatic
retry, DIAG-1, regional beta or FIELD-1; future work needs separate authorization.

## 5N-NATIVE-AUTHORITY-COMPAT — PASS offline, 02.10.2026

Exact #11 checker/snapshot reproduces exit1 at the historical attempt time. An
observability-only local copy identifies `negative_revision_unexpected_acceptance`:
profile floor1 was incremented to2, equal to the valid signed owner revision2.
The native authorization callback correctly accepted it; the operator's negative
assertion was wrong. **Class D: checker negative-fixture bug, not stale binary or
Python/native contract disagreement.** Original binary `8f59485f…` rebuilds
byte-identically from retained main + accepted4f48202 libraries with Go1.26.0.

Tracked checker now derives negative floors from validated signed revision/CRL
claims, with genuinely different Family and safe JSON failures. Existing Family
TLS, Python authority, delivery/cache runtime, TTLs and floors remain unchanged.
Standalone pinned adapter fsyncs an allowlisted receipt before verdict/rollback.
Exact #11 snapshot now PASSes locally at attempt time; actual-time expired snapshot
still FAILs. Synthetic delegation2/grant2/CRL19,1→2 renewal, future revisions and
stale/revoked/rollback/conflict negatives pass across producer/native/delivery/cache.

Code checkpoint `8b829971f4e75a1a584cebf9867eb0ae5d256129`. Two clean Git exports,
14 inventoried inputs, produce identical native artifact SHA256
`a1df5f88a103340a6ba9d67ae8842147afd99d430fba6b30b8ba7b212373ce90`.
Local artifact only: not installed, deployed, signed for release or distributed.
Python82 PASS/no skips; shared native/CLI tests and JVM cache7 PASS. See
[exact replay, semantics, provenance and limits](releases/2026-10-02-5n-native-authority-compat.ru.md)
and [future operator contract](../deploy/friends/restricted/NATIVE_AUTHORITY.md).

Production untouched except approved read-only material/artifact retrieval; no
authority refresh, remote checker execution, NL/RU start, HTTP change, Redmi or
Android build. #11 remains FAILED / ROLLED BACK; its security history remains2/2/19
and short-lived credentials require fresh checks in a separately authorized task.
Pre-existing dirty/untracked work is preserved; task-only local commits, no push.
STOP: no automatic attempt #12, DIAG-1, distributed beta or Krasnodar FIELD-1.

## 5N-PROV-1 — attempt #11: authority prerequisite FAIL, 02.10.2026

**5N-PROV-1 = DEPLOYMENT FAILED / ROLLED BACK.** Single authorized attempt from
`4f482027d739b52bfab11ff0a796e9dd0dec692f`; exact sync `9d965b95…` and HTTP
`460e7520…`, inventories17/25, bundled source alignment, isolated imports/startup
and two focused artifact tests PASS. RU18084 ordinary HTTP and18085 TCP/Xray retain
their original owners.18086 has no listener and passes loopback bind preflight;
candidate never started. Direct static status remains excluded by contract.

Same Family/issuer key/gateway/sole owner renewed: offline-signed delegation1→2,
issuer certificate reissued with the same key and24h policy, owner grant revision1→2;
issuer/delegation/grant expiry03.10 11:54:56UTC. Global minimum revision remains1.
CRL floor18→19, issued02.10 11:57:08UTC, expires12:12:08UTC; same-key gateway leaf
expires12:57:08UTC. Exactly one owner remains admitted;27 others denied. Python
signature/binding/admission checks pass, but existing NL native authority checker
returns exit1 at11:57:10UTC. **Native compatibility is not accepted.** Failure
receipt persisted; no retry, repair, NL/RU runtime startup, candidate or ingress change.
[Exact receipts, native-check limitation and remaining gates](releases/2026-10-02-5n-prov1-attempt11.ru.md).

Restricted-only rollback/state confirmation11:57:58–59UTC leaves RU sync/timer and
NL bootstrap inactive, authorization/directory absent. Renewed authority and floor19
are retained, never restored to old snapshots. Original authority reservation1 is
historical; the protected #11 renewal reservation and signed manifest2 are current.
Final12:00:31–40UTC readback: ordinary handler/ingress byte-identical, routing18084,
all normal service PID/start metadata unchanged, registrations/invitations preserved,
AWG/TCP active/unrestarted. Paced baseline and final200/400/400/restricted404 PASS;
no429/502 in eight valid external responses; limiter/upstream attribution UNKNOWN
without trace installation. No new VPN dataplane acceptance claimed.

NL bootstrap/RU live --check/sync negatives/direct B–G/external A–G and all physical
gates NOT RUN. Redmi untouched; no final FIELD APK, version/install/public/invitation
change, commit or push. Entry dirty/untracked work preserved. STOP: no automatic
attempt #12, DIAG-1, beta or Krasnodar FIELD-1. Separate authorization/acceptance is
needed to resolve the native gate; any later rollout must inspect current floors,
refresh short-lived materials safely and repeat every unpassed gate.

## 5N-HTTP-CANDIDATE-PREFLIGHT — PASS locally, 02.10.2026

Local harness/config correction separates direct application B–G from external
nginx A–G.18085 is explicitly forbidden as Friends TCP/Xray's existing API.
The new explicit singleton candidate policy allows127.0.0.1:18086 only after fresh
unused-port preflight; it does not claim production availability. Collision is STOP,
including a previous candidate; no process is replaced. PID/start/argv/archive and
exclusive IPv4-loopback ownership are rechecked before direct probes and switch.
Only complete direct readiness unlocks verified-port ingress rendering; full
correlated external acceptance precedes commit and old-worker drain/retirement.
[Contract, validation and Git preservation](releases/2026-10-02-5n-http-candidate-preflight.ru.md).

Focused localhost suite:118 PASS,0 skips,128.55s, including exact accepted archives,
real isolated nginx direct/external matrices, collision/TOCTOU/binding guards and
rollback. This is not production/systemd acceptance or proof that18086 is free there.

Authority remains untouched. Any separately authorized attempt #11 must check and
renew delegation/issuer, owner grant, CRL and gateway credential as needed, preserving
identities/TTL policy/monotonic floors. No production access or service management,
Redmi, APK, release/version change or push. Accepted HTTP460e7520… and sync9d965b95…
are unchanged. Historical #10 remains a pre-deployment STOP and #9 attribution
partially UNKNOWN. STOP after focused tests/documentation and task-only local commit;
no automatic attempt #11, DIAG-1, beta or FIELD-1.

## 5N-PROV-1 — attempt #10: pre-deployment STOP, 02.10.2026

**5N-PROV-1 = DEPLOYMENT FAILED / ROLLED BACK** — no production mutation or
rollback operation was needed. Authorized HEAD `57206fe8…`, exact sync `9d965b95…`
and HTTP `460e7520…`,17/25 inventories, bundled tracked sources and isolated imports
PASS. Paced external baseline10:57:47–50UTC is200/400/400/404, fsynced before verdict.

Two prerequisites prevent executing the requested transaction unchanged. RU
**127.0.0.1:18085 is already the active Friends TCP/Xray API**, PID1908885; confirmed
read-only11:01:32UTC. Do not stop it or repurpose its port for the candidate. Also,
exact HTTP archive direct `GET /status/server-load.json` returns501 locally;
status200 is nginx's static endpoint, not a handler route. Prior local switch tests
checked status through nginx and B–G directly, not direct A=status200.
[Attempt #10 receipts, limits and remaining contract decisions](releases/2026-10-02-5n-prov1-attempt10.ru.md).

No JIT/signing, NL/RU start, candidate install, ingress switch, phone or APK work.
Authority/grant expired10:44:11UTC; gateway10:31:33UTC, runtime CRL18 at09:48:20UTC;
staged CRL16 remains stale. Same sole configured owner/27 policy-denied; expired
owner grant is not usable admission. DB/grant/registration rows match #9 final
ledger. Ordinary handler/ingress match #9 rollback; RU/NL service states/PIDs/start
times unchanged, AWG/TCP active; no new dataplane acceptance claimed. STOP: agree
an unused candidate listener and clarify ingress-only A versus direct B–G before
a separately authorized new attempt; then fresh JIT and all gates are still needed.
No hotfix/retry, version change, commit, push, beta or FIELD-1. Historical #9 exact
429/502 attribution stays partially UNKNOWN; all entry dirty work is preserved.

## 5N-HTTP-TRANSITION-DIAG — historical attribution BLOCKED, 02.10.2026

Read-only RU audit confirms the original shared nginx2r/s+burst8 per-IP and10r/s+
burst20 global policies, access logging off/error level crit. No ingress log events
retained for #9; bounded service-journal queries unavailable. Historical exact bucket
and502 errno therefore remain unproven; no retrospective root-cause claim or PASS.
[Diagnosis, actual timeline and limits](releases/2026-10-02-5n-http-transition-diag.ru.md).

Exact production nginx1.30.4 plus unchanged accepted HTTP archive reproduce the
recorded cadence: seven observer429 and seventh non-canary429 from `per_ip`; direct
upstream remains expected400/403. Stop-before-start independently reproduces direct
ECONNREFUSED/nginx502. Minimal local operator correction: serialized1s pacing,
correlated redacted receipts, candidate18085 readiness before ingress switch while
old18084 stays alive, restore/drain before candidate stop. A–G repeated three times
and three additional switch-overlap checks pass locally; no production install.
Runtime/authority/admission/CRL/BOOT-1/sync/versions unchanged, all #9 evidence and
entry dirty work preserved. No Redmi/Android build/push/deployment #10. STOP.

## 5N-PROV-1 — attempt #9: DEPLOYMENT FAILED / ROLLED BACK, 02.10.2026

Explicitly authorized single attempt from `028300e009007e78401cc2431989c18e0810d5f9`.
Exact sync `9d965b95…` / HTTP `460e7520…`:17/25 inventories, every bundled tracked
source against HEAD, isolated startup/import origins and two exact-artifact local
fixtures PASS; no rebuild or build-commit-string exception. Sole owner/27 denied,
delegation1/grant1/issuer valid until10:44:11UTC; planned60min acceptance window.
JIT CRL15→16, gateway expiry10:31:33UTC; native authority validation PASS.

**NL committed authoritative acceptance PASS09:31:41UTC**: fresh READY-path seed,
canonical precise timestamps, binding/directory and stable PID/NRestarts0. Optional
journal timed out5s **without changing PASS**. RU isolated `--check` PASS; complete
committed sync acceptance PASS09:31:58UTC, CRL17/DB agreement, generic-shell and
stale-CRL rejection plus final monotonic readback; no mandatory negative skipped.

**HTTP hard server STOP:** accepted artifact activated; ordinary transition receipts
contain429 and502 instead of baseline200/400/400. RU matrix A–D200/400/400/400;
six real non-canaries403, seventh429 → ProbeFailed. F/G not reached, not PASS.
All failure receipts preceded rollback09:33:22–29UTC. No HTTP cause inferred from
status alone; no retry/hotfix/Redmi. Ordinary routes restored200/400/400, restricted404;
HTTP drop-ins removed, sync/timer/bootstrap off, NL authorization removed/directory
quarantined. RU DB/runtime and NL preserve CRL18, expiry09:48:20UTC; stage16 is older,
never use it to lower the floor. Registrations/invites/grants unchanged; AWG/TCP and
NL normal service PIDs/start times unchanged. Friends API restarted and restored.
[Attempt #9 exact receipts, limitations and rollback](releases/2026-10-02-5n-prov1-attempt9.ru.md).
Attempts #1–#8 and unrelated work preserved. Versions/public artifacts unchanged;
no FIELD APK, commits or push. STOP; no automatic retry, beta or Krasnodar FIELD-1.

## 5N-NL-ACCEPTANCE — PASS, local harness correction, 02.10.2026

Standalone `scripts/restricted_bootstrap_acceptance.py` replaces the historical
NL journal-gated wrapper for a future separately authorized attempt. Authoritative
service/start/fresh READY-only seed/precise directory/final same-process checks and
their fsynced verdict precede optional5s diagnostics. Journal timeout/failure is a
warning, never runtime FAIL; real service/restart/deadline/directory failures still
fail closed. Separate immutable authoritative/diagnostic receipts; no raw logs or
private state. Exact attempt-#8 flow fixture reproduces old FAIL and corrected
PASS+diagnostic_timeout. [Contract, bounds, tests and selective Git finalization](releases/2026-10-02-5n-nl-acceptance.ru.md).
191 focused Python tests PASS, no skips; offline Go bootstrap tests PASS, broker
command compiles. Docs419/links2558/errors0; targeted source guard/diff check PASS.

Attempt #8 remains DEPLOYMENT FAILED / ROLLED BACK due to an operator error, **not**
bootstrap/provider failure. Historical authority/CRL timestamps below were not
refreshed or rechecked here. RU operator, runtime artifacts, architecture/admission
and versions unchanged. Local-only tests; no production access/change, credentials,
service start, Redmi/APK or push. Retained dirty work preserved; only task-owned
code/tests/docs are committed. STOP: no automatic attempt #9, beta or FIELD-1.

## 5N-PROV-1 — attempt #8: DEPLOYMENT FAILED / ROLLED BACK, 02.10.2026

Exact HEAD `f4c06df5f16593273b4c8bffa75646f1df17c2fb`, sync `9d965b95…`
and HTTP `460e7520…`: hash,17/25-entry inventory, all tracked-source comparisons
and isolated startup PASS. Fresh synthetic exact-sync `--check` and exact-HTTP
signed-readiness fixture PASS. No rebuild or source exception. Durable ordinary
baseline08:26UTC and post-rollback08:37UTC both200/400/400; restricted404.

Delegation1, issuer and sole owner grant1 remain valid through02.10 10:44:11UTC;
no renewal/TTL extension needed at entry. Actual live registry contains28 devices:
one restricted owner canary and27 denied, not the historical27-total/26-denied
snapshot. No admissions added. JIT CRL14→15 at08:36:45UTC, expiry08:51:45UTC;
same-identity gateway credential expiry09:36:45UTC. Native authority checks PASS.
NL exported one canonical UTC-Z seed; live directory validation PASS08:36:53.695Z,
no issued_in_future, process active/NRestarts0 at failure observation.

**Operator error, not a demonstrated runtime/provider failure:** the attempt's NL
wrapper incorrectly made non-authoritative `journalctl` collection a required gate.
Its5s timeout caused the fsynced NL failure08:36:58UTC. This is not compliant with
the requested non-gating journal rule. Attribution follows executed source ordering
and retained timestamps, not a captured failing argv. No retry or live hotfix.
RU production `--check`, committed full sync operator/negatives and HTTP activation
were **not reached**; neither artifact is thereby rejected as faulty.

Scoped rollback08:37:04–07UTC: restricted bootstrap/sync/timer off, NL forced SSH
authorization removed and directory quarantined, HTTP drop-ins absent. Ordinary
handler/ingress, normal service PIDs/start times and devices/invites/grants unchanged.
RU DB/stage and NL profile preserve CRL15; inactive RU runtime remains on expired
CRL14, never use it to reset the authoritative floor. NL retains inert new sync;
RU retains old sync; neither is running. No Redmi, APK, versions, commit or push.
[Attempt #8 evidence, exact gate matrix and remaining checks](releases/2026-10-02-5n-prov1-attempt8.ru.md).
Prior dirty work preserved; STATUS/PLAN additions only plus this new report.
Attempt #3 cause UNKNOWN; #6/#7 remain pre-production stops with no production changes.
STOP: no automatic retry, distributed beta or Krasnodar FIELD-1.

## 5N-SYNC-ARTIFACT-REFRESH — PASS, local only, 01.10.2026

Fresh isolated1578-file export of exact accepted HEAD
`f4c06df5f16593273b4c8bffa75646f1df17c2fb`, no dirty overlay. Real `python -I`
entrypoint tracing and seven missing-module negatives prove `restricted.py` is
required (classification A); all10 manifest modules load from the archive. Manifest
unchanged. New sync SHA256
`9d965b955cbd5375c82adadb3f25736d1cca3fe86ab477ea73269ef1499a5a2d`, path
`state-client-build/sync-artifact-refresh/bundle/restricted-sync.pyz`.
All17 inventory entries verified; every bundled tracked input matches HEAD.
194 committed sync/runtime/directory/native/receipt regressions PASS, no skips;
7 exact old/new archive and unchanged-HTTP interoperability checks PASS, no skips.
Isolated precheck, complete local operator sequence, actual stale-CRL rejection,
forced-wrapper shell rejection, precise live-shape directory and signed synthetic
HTTP readiness delivery PASS. No false issued_in_future for valid subsecond input.
Systemd state/SSH transport simulated locally, not a live service/network gate.

Old `cb6f050e…` sync is retired as a deployment candidate but retained byte-identical
as evidence. HTTP `460e7520…` remains unchanged and was not rebuilt. Only bundled
`restricted.py` source changed (HTTP request-validation hunk); tested sync behavior
is unchanged, not an unqualified whole-module behavior-identity claim. Secret/content
scan PASS. [Full provenance, exact modules and limits](releases/2026-10-01-5n-sync-artifact-refresh.ru.md).
Attempt #7 remains stopped before production, with no rollback required; #3 UNKNOWN.
All five pre-existing dirty files/hunks preserved; only additive task documentation.
No source/manifest/version/credential/production/Redmi changes, commit, push, beta or
FIELD-1. STOP: no automatic attempt #8; any rollout needs separate authorization.

## 5N-PROV-1 — attempt #7: pre-production source gate STOP, 01.10.2026

At19:55:41UTC the explicitly authorized attempt confirmed HEAD
`f4c06df5f16593273b4c8bffa75646f1df17c2fb` and both requested artifact hashes.
Sync17/HTTP25 inventory entries and embedded bytes are intact. HTTP matches HEAD;
sync has one current-source mismatch: bundled `control/friends/restricted.py`
`9b5d5ce2…` versus HEAD `ab3542b9…`. The difference is the already documented
HTTP challenge input-validation hunk, **not** a nanosecond-directory regression
or evidence of sync runtime failure. The explicit any-mismatch STOP rule does not
authorize treating this known difference as an exception. No rebuild/substitution,
production access/change, JIT refresh, activation, Redmi, APK or automatic retry.
No rollback needed/performed; live health/authority remain unverified this attempt.
Durable file+directory-fsynced input receipt and source diff:
`state-client-build/prov1-attempt7/`. [Separate attempt #7 report and all unperformed
gates](releases/2026-10-01-5n-prov1-attempt7.ru.md). Attempts #1–#6 unchanged;
#3 cause UNKNOWN. Four pre-existing dirty files/hunks preserved, with additive
STATUS/PLAN notes only and a new report. No versions, commits, push, beta or FIELD-1.
Next requires explicit resolution of the exact-source/pinned-sync conflict before
any newly authorized rollout; no production acceptance is claimed.

## 5N-HTTP-PACKAGING-GIT — new-session revalidation, 01.10.2026

Actual entry HEAD was `d8624dea2cffe3c41d9d136a6f93ee527b8f3812`, not8663128:
the requested source and documentation commits already existed in local history.
No duplicate implementation commit or history rewrite. Fresh1578-file Git export
reproduces HTTP `460e75205eb9baff313dc7dd963cdb7bceddf2d1e13405a71686f9ec6c976d71`;
274 clean-source tests PASS, no skips (48.72s). Embedded old/new fixture confirms
old rejection, new acceptance, future+1ns and four malformed-timestamp rejections,
offset normalization to UTC Z. No false issued_in_future. Sync pin unchanged.
Only this revalidation documentation is new; all four retained unrelated diffs
remain outside the index. Final post-documentation clean-source rebuild, exact
HEAD and tests: `state-client-build/http-packaging-git-recheck/final-artifact.json`
and `final-tests.log`; [report](releases/2026-10-01-5n-http-packaging-git.ru.md).
No production access/change, credentials, service activation, Redmi, push or
attempt #7. Existing rollout/rollback boundary and unperformed physical gates
are unchanged. STOP; neither FIELD-1 nor beta starts here.

## 5N-HTTP-PACKAGING-GIT — committed local HTTP checkpoint, 01.10.2026

Reviewed missing HTTP packaging/runtime/receipt implementation is committed in
`f7b3b6c29526fb600990f60d57449571a8538f22`. Explicit25-entry bundle; packaged
`main()` without external-source fallback, deterministic ZIP metadata, precise
directory delivery, durable redacted receipts and A–G local tests. Working-source
candidate SHA256 `460e75205eb9baff313dc7dd963cdb7bceddf2d1e13405a71686f9ec6c976d71`;
clean source rebuild has identical bytes.274 targeted tests PASS, including native
contracts;45 clean-commit HTTP matrix/receipt checks PASS (22.20s).
[Final clean-HEAD evidence and preservation ledger](releases/2026-10-01-5n-http-packaging-git.ru.md).
Old HTTP `eb9eb06f…` stays retired; sync `cb6f050e…` unchanged. This is local build
acceptance, not deployment. Attempts #1–#6/history unchanged; #3 cause UNKNOWN.
No production/credential/service/Redmi/APK change, no push, beta or FIELD-1.
Unrelated VPN-health and historical attempt-#5 additions remain unstaged. STOP;
no automatic attempt #7.

## 5N-HTTP-ARTIFACT-REFRESH — FAIL: clean-HEAD packaging gap, 01.10.2026

Local-only exact `8663128a4ee433c29adb90340b8d4573ac2ba161` export verified:
all1569 tracked blobs/modes match, no extra files or dirty-worktree overlay.
The accepted nanosecond consumer/delivery fix is present;59 targeted source
precision/offset/security tests PASS. Existing sync archive remains `cb6f050e…`,
matches HEAD's shared module and accepts the synthetic subsecond fixture.
Old HTTP `eb9eb06f…` reproduces rejection from its embedded consumer and is
**retired as a deployment candidate**, retained unchanged for historical evidence.

No replacement was built: this HEAD lacks the HTTP builder/manifest/drop-in,
receipt harness and HTTP matrix tests; its handler lacks packaged `main()` and
unconditionally prepends the external app directory. Those prerequisites exist
only as retained uncommitted work, which was not imported or committed. Exact-HEAD
and no-overlay requirements therefore prevent using the accepted packaging flow.
No new archive/hash, startup, A–G matrix, artifact regression, receipt-harness,
sync→new-HTTP delivery or new-artifact secret-scan PASS is claimed.
[Evidence and prerequisite boundary](releases/2026-10-01-5n-http-artifact-refresh.ru.md).
Attempt #6 remains a pre-production stop; no production access/change, credentials,
services, Redmi, APK, source edit, commit, push or attempt #7. STOP.

## 5N-PROV-1 — attempt #6: pre-production input gate FAIL, 01.10.2026

Explicitly authorized attempt #6 stopped at18:31UTC before any production access
or change. HEAD `8663128a4ee433c29adb90340b8d4573ac2ba161` confirmed; committed
sync acceptance operator unchanged. Both requested archive hashes and their full
17/25-entry inventories pass, but pinned HTTP contains the old
`control/friends/restricted.py`, without the accepted nanosecond directory/delivery
fix. It matches neither current HEAD nor the retained HTTP worktree source.
The corrected sync archive does match HEAD; its worktree difference is the preserved
unrelated HTTP challenge hunk. This is a source-consistency failure, not corrupt
archive bytes. Per the explicit mismatch STOP rule, no rebuild, JIT refresh,
SSH, baseline/live gates, activation, Redmi operation or retry was performed.
Rollback not needed/performed; production current health/state not freshly verified.
Last documented state remains attempt #5 rollback, not a new acceptance.
Existing8 modified/6 untracked files preserved; STATUS/PLAN receive only additive
task notes. [Separate attempt #6 report](releases/2026-10-01-5n-prov1-attempt6.ru.md).
Attempt #3 cause UNKNOWN; no commit/push/public release/beta/FIELD-1.

## 5N-SYNC-ACCEPTANCE — PASS локально после №5, 01.10.2026

Таймаут №5 реконструирован в `journalctl` (10s), после синхронного start и до
service-observation/readback/negative gates. Исходный flow воспроизведён изолированно;
причина задержки самого production journal остаётся неизвестной. Поздний success
unit/CRL14 **не закрывает** историческую RU acceptance: №5 остаётся FAILED/ROLLED BACK.
Новый оператор `scripts/restricted_sync_acceptance.py`: fsynced step receipts,
командные deadlines, authoritative oneshot/result + свежий signed CRL/валидный
directory + обязательные generic-shell/stale-CRL negatives. Journal исключён из
обязательного success path; таймаут обязательной команды не превращается в PASS
при позднем completion. Runtime/TTL/authority не изменены. Только offline fixtures;
без production, служб, refresh, Redmi, APK, push. Подробности и тесты — в
[отчёте](releases/2026-10-01-5n-prov1-production-restricted-provisioning.ru.md).
STOP; автоматического deployment retry нет. Причина №3 остаётся UNKNOWN.

## VPN read-only snapshot — 01.10.2026,17:43UTC

Friends:27 activated devices/23 not revoked/4 revoked,81 invitations/27 used;
unchanged since13:39UTC. NL5 AWG peers with handshake<5min,4 transferring in15s,
12 with handshake<24h; RU0/0/0. Friends TCP established0 on both gateways.
CPU busy NL9.92%/RU11.54%, available RAM532.6/1102.0MiB; no CPU/RAM saturation
in this sample. External RX/TX NL5.0391/3.3859Mbit/s,RU0.0224/0.0200Mbit/s.
Disk await NL144.26/RU34.33ms; worker Docker unhealthy remains. Normal AWG/TCP
and RU access API active. API current start01.10 14:40:45UTC differs from the
13:39 audit; cause not investigated here. No restart/deployment/version change
by this audit; HTTPS/client E2E and restricted services not rechecked. Devices
are not unique people/DAU. [Details](releases/2026-10-01-vpn-health.ru.md).

## 5N-DIRECTORY-VALIDATION — PASS locally, no deployment, 01.10.2026

Attempt #4's unchanged private directory and exact deployed Python source reproduce
`ValueError`: `stage=time predicate=issued_in_future field=issued_at`. The valid
Go producer issued17:13:53.532852358Z; the operator supplied
`int(time.time()) == 17:13:53Z`. The strict nanosecond comparison therefore rejected
a directory already published in that same second. Identical bytes pass at the
next second and at the actual subsecond observation with native validation.
This is a **consumer/caller clock-precision mismatch**, not invalid UTC-Z or URL.

Minimal fix/source commit `29d15d73dae52ac8a1079c52dd349b5b21045742`: Python
validation/sync/delivery preserve current nanoseconds; no rounding of directory
timestamps, grace period, trust bypass or TTL extension. Producer and native
consumer unchanged. Closed runtime now provides `directory-check` with bounded
stage/predicate/field and fsynced receipts before nonzero exit/rollback handling.
Synthetic291-byte live-shape fixture, old FAIL/new PASS private replay, strict
negative/nanosecond edges and Go producer→Python→Android/native contract PASS.
Python306 regressions PASS; directory68 PASS; Go race/vet four packages PASS.

Final committed-source `restricted-sync.pyz`:
`cb6f050ec49ee4b65fa65c5327e32d6271d714ef6f8e695f16cb3c85b60f386f`.
Built/isolated-tested only, not installed. Production remains last documented
attempt #4 rollback; no authority refresh, service start, Redmi, APK, push or
FIELD-1. Attempt #3 HTTP cause remains **UNKNOWN**. Existing HTTP/workflow/VPN
work preserved. **STOP: no automatic attempt #5.**
[Reproduction, field audit, test gap, artifact and limitations](releases/2026-10-01-5n-prov1-production-restricted-provisioning.ru.md).

## 5N-PROV-1 — попытка №4: DEPLOYMENT FAILED / ROLLED BACK, 01.10.2026

Explicitly authorized attempt from `d27156d92fdb829fdc82471b05074270b54cd1a9`.
Pinned HTTP archive `eb9eb06fd38a0ec498445877fcfb5908a8566b96c7a25f44e2a4619170743a2f`
and all25 inventory/source entries unchanged; no rebuild. Baseline17:09UTC:
ordinary HTTPS200/challenge400/chat400, restricted404; RU/NL AWG/TCP active,
restricted units inactive, sole owner admitted/26 others rejected.

JIT17:13:46UTC: CRL11→12, expiry17:28:46UTC; gateway certificate18:13:46UTC.
Same Family/owner/issuer/gateway,0 other admissions; grant/delegation1 unchanged,
expiry02.10 10:44:11UTC, TTLs unchanged. Native certificate/negative checks PASS.
NL started17:13:49UTC, native `bootstrap_seed_ready` once/NRestarts0, one seed,
canonical UTC-Z directory. **NL Python live-directory acceptance failed with
`ValueError`**; exact failed predicate is not established by this receipt. STOP:
RU `--check`/sync and HTTP activation not reached. No live workaround/retry.

Rollback completed RU17:13:57/NL17:13:58UTC. Readback17:15UTC:
ordinary200/400/400, restricted404; API handler/app/ingress unchanged, no new
drop-ins, API/AWG/TCP PIDs/start times unchanged. NL seed/sync authorization off,
directory quarantined; RU sync/timer inactive. DB normal rows/grants unchanged;
**authoritative DB/staged CRL12 and NL floor12 retained; inactive RU runtime CRL11**.
Do not treat that expired inactive CRL11 as the next publisher floor or restore DB.
No Friends API restart/observed outage; continuous downtime not measured.

Attempt #3 root cause remains **UNKNOWN** because decisive HTTP evidence was lost.
Redmi, provisioning/readiness/restart/rehearsal/Chrome/DNS/leak/fail-closed proof
not run. No APK install/build/version/public/invitation change; canary53 remains
previously built only. No commits/push/FIELD-1; unrelated VPN-health work preserved.
Next work requires a separate local investigation of the retained NL rejection;
deployment authorization for this attempt is consumed, no automatic retry.
[Exact receipts, rollback and remaining checks](releases/2026-10-01-5n-prov1-production-restricted-provisioning.ru.md).

## 5N-HTTP-LIVE-REVALIDATION — READY FOR DEPLOYMENT AUTHORIZATION, 01.10.2026

Local revalidation16:59UTC from HEAD `d27156d92fdb829fdc82471b05074270b54cd1a9`
plus the retained uncommitted HTTP changes: exact closed Friends HTTP artifact
`eb9eb06fd38a0ec498445877fcfb5908a8566b96c7a25f44e2a4619170743a2f`
passes isolated restricted-enabled nginx/HTTP/verified HTTPS acceptance. Status200,
ordinary malformed challenge400, safe chat challenge400, restricted malformed400,
synthetic non-canary403, synthetic canary challenge200 and readiness fetch200;
ordinary activation and route boundaries unchanged. **188 PASS /4 optional Go
compatibility checks skipped**; focused HTTP/evidence suite first39 PASS, then
included with an additional packaged-CLI shell EXIT-trap test in the larger run.
Receipts fsync before acceptance/rollback and survive nonzero exit, process exit,
catchable termination, upstream failure and local rollback/recovery simulation.

**Attempt #3 root cause remains unknown because decisive HTTP evidence was lost.**
Attempt #4 has no separate explicit deployment authorization in this conversation:
no SSH, authority refresh, deployment, API activation, phone action or rollback here.
Last documented production state is attempt #3 rolled back, ordinary200/400,
restricted404; not a fresh live observation. Last recorded CRL11 expired14:55:41UTC,
gateway certificate15:37:13UTC; both need JIT refresh from authoritative floors,
not staging6. Same Family/owner/issuer/gateway,0 other admissions and TTL policy.
Versions unchanged: canary53 remains a previously built private artifact, not an
installation/publication claim. Redmi readiness/restart/rehearsal/browser/DNS/
fail-closed acceptance remain unperformed. No new commits;18 unpushed retained;
push/FIELD-1:no. Existing VPN-health work preserved.
[Exact artifact, receipts, rollout/rollback boundary and remaining checks](releases/2026-10-01-5n-prov1-production-restricted-provisioning.ru.md).

## VPN read-only snapshot — 01.10.2026,13:39UTC

Friends:27 activated devices/23 not revoked/4 revoked,81 invitations/27 used;
unchanged since the morning. NL4 AWG peers with handshake<5min and transfer
in15s,12 with handshake<24h; RU0/0. Friends TCP established0 on both gateways.
CPU busy NL7.87%/RU25.16%, available RAM530.3/1107.3MiB; no CPU/RAM saturation
in this sample. External RX/TX NL0.8703/0.8822Mbit/s,RU0.0221/0.0131Mbit/s.
Disk await NL25.33/RU30.47ms; worker Docker unhealthy remains. RU restricted-sync
unit failed; no reset/retry, restricted rollout remains rolled back. Normal AWG/TCP
and RU access API active, start timestamps unchanged; public HTTPS status TLS PASS.
No deployment/restart/version change or client E2E. Device counts are not unique
people/DAU. [Details and remaining checks](releases/2026-10-01-vpn-health.ru.md).

## 5N-PROV-1 — попытка №2: DEPLOYMENT FAILED / ROLLED BACK, 01.10.2026

Разрешённая попытка из `e808f50` остановлена на RU sync, до активации API.
NL READY и живой UTC `Z` каталог → Python PASS. Новый блокер: минимальный RU
runtime не содержит `clients.desktop.profile_config`, импортируемый
`provisioning.friends_catalog`; ошибка воспроизведена изолированно локально.
Live-исправления/повторного запуска нет. NL stopped/disabled, sync-доступ отключён;
RU API/ingress восстановлены без restart, timer disabled, sync failed/PID0.
Normal PIDs/start times и devices/invites/grants неизменны; HTTPS200, обычный
challenge400, restricted404. Admission: owner1,26 остальных rejected, других0.
JIT CRL4→5, expiry13:46:55UTC; gateway14:31:55UTC, прежние authority/TTL.

Место освобождено штатной очисткой только task-owned Go cache. Полная canary53
`0.1.18-canary53-prov1` сборка PASS:194 JVM tests, lint0errors/36warnings,
fresh arm64 JNI, подпись совместима с установленным Redmi field52.
APK не установлен/не опубликован и не является финальным FIELD APK.
Prewarm/restart/rehearsal/browser/leak proof не запускались. Следующий шаг:
локальный dependency-closure/import smoke точного runtime bundle, затем новое
разрешение на retry и JIT refresh после sequence5. Без push/FIELD-1.
[Хронология, хэши, downtime и откат](releases/2026-10-01-5n-prov1-production-restricted-provisioning.ru.md).

### Исторические checkpoint до попытки №2

## 5N-TIME-COMPAT — PASS locally, production unchanged, 01.10.2026

Local repair from `e77aea8`: Go seed/Directory serializers emit UTC `Z`; strict
Python/native parsing accepts valid RFC3339 offsets as the same absolute instant.
Nanosecond expiry/lifetime comparisons, unchanged1h bound, shared actual-failure
timestamp fixture and cross-language sync/delivery/native proof. Python91 PASS;
Go race/vet4 packages PASS; local broker/helper build PASS; Friends cache JVM6 PASS.
No full Android APK/physical/PERF run. Original deployment failure and rollback
remain below: production still runs no restricted service/routes. No SSH, material
refresh, token access, deployment, service start, public release, push or FIELD-1.
Next authorized rollout must rebuild/re-stage fixed artifacts and refresh expired
authority; never restart the inert old NL binary as if this local fix were deployed.
[Contract audit, tests and preserved failure](releases/2026-10-01-5n-prov1-production-restricted-provisioning.ru.md).

## 5N-PROV-1 — DEPLOYMENT FAILED / ROLLED BACK, 01.10.2026

Authorized canary attempt from `33255fe`,11:39–11:48UTC: JIT CRL3→4
(expiry11:54:06UTC), gateway leaf12:39:06UTC; authority/canary unchanged,0 other
admissions. New NL bootstrap installed/started and joined one seed READY, but
exported expiry uses `+03:00`; accepted Python directory parser requires `Z`.
**STOP before RU rollout.** NL service stopped/disabled, sync key authorization
disabled, directory quarantined; installed components remain inert. Normal API/
ingress byte-identical; RU/NL AWG/TCP PIDs/start times unchanged, HTTP status200,
ordinary malformed challenge400, restricted challenge404. Sole owner admitted,
all26 non-canaries denied by actual authority check. No API restart/observed outage.
Phone prewarm/restart/rehearsal, final FIELD APK and leak/fail-closed acceptance
**not run**. No push/public rollout/FIELD-1. Next: local non-UTC timestamp
compatibility fix/tests, then separately authorized fresh rollout; no live workaround.
[Exact order, failure, rollback and acceptance scope](releases/2026-10-01-5n-prov1-production-restricted-provisioning.ru.md).

### Historical material-only READY checkpoint

## 5N-PROD-DEPLOY-PREFLIGHT — READY, no deployment, 01.10.2026

Owner confirmed token input; NL provider.env exists/root:root0600/schema PASS,
validated server-side with boolean-only output, no token value/hash/size exposed.
Same Family/Owner canary/gateway/issuer; other admissions0. Publisher CRL **2→3**,
expires **01.10 11:35:38UTC**; renewed gateway leaf **12:20:38UTC**. Delegation/grant
unchanged through02.10 10:44:11UTC, sequence/revision1. Actual crypto/native/sync/
permissions checks PASS. All material ready within expiry, runtime files remain
staged except owner-installed provider.env; account/units not installed/activated.
No policy extension, service/API/ingress change, provider request, room or phone
prewarm. Revalidate/refresh if later deployment misses the short validity window.
**STOP before deployment.** No FIELD-1/push.
[Current complete inventory and evidence](releases/2026-10-01-5n-prod-deploy-preflight.ru.md).

## 5N-PROD-DEPLOY-PREFLIGHT — BLOCKED on owner input, 01.10.2026

Same Family/Owner canary/gateway/issuer; other admissions0. Accepted publisher
advanced CRL1→2, expires **01.10 11:26:23UTC**; renewed gateway leaf expires12:11:23.
Delegation/grant unchanged through02.10 10:44:11UTC, sequence/revision1 retained.
32 tests + actual native/authority/sync/permissions checks PASS; no TTL extension.
NL hidden-input helper staged/tested; **provider.env missing, token not accessed
or installed**. Owner runs the protected SSH prompt in their own terminal, never
pastes token into chat. Stop here, recheck/refresh expiry after input if needed.
No services/runtime/API routes/ingress changed; no room, phone prewarm/push/FIELD-1.
[Exact secure procedure, inventory and evidence](releases/2026-10-01-5n-prod-deploy-preflight.ru.md).

## 5N-PROD-AUTHORITY — READY, staged only, 01.10.2026

User-authorized first Friends restricted Family created under the existing signed
issuer/grant namespace; only resolved Owner canary bound (other admissions0).
Existing NL control-provider identity designated as gateway, original key retained;
no ProductStore changes/new device/root. Additive restricted migration23.883ms,
private on-host backup; existing normal rows/services/API/ingress unchanged.
Offline ControlTrust delegation signed locally, RU issuer/private key0600, genuine
publisher CRL sequence1, canary revision/delegation sequence1 from empty namespace.
RU security files and NL gateway/binary/sync/account templates staged root-only;
no new account/units/runtime installed or started. **Provider token excluded**;
KeePass not accessed.18 contract tests + actual native/crypto validation PASS.
Initial CRL/effective validation expiry **01.10 11:02:45UTC**, gateway leaf11:47:45,
delegation/canary grant **02.10 10:44:11UTC**; refresh before later authorized use,
never extend directory TTL/reset floors. No real-phone delivery/rehearsal/FIELD APK.
No token phase, automatic deployment, push or FIELD-1.
[Exact authority, inventory, validation and rollback](releases/2026-10-01-5n-prod-authority.ru.md).

## 5N-PROD-MATERIALS — BLOCKED at authority resolution, 01.10.2026

Continuation from `9340931`, read-only audit completed10:28UTC. Existing protected
Friends notice registry resolves one active `Owner` device administrator and its
active invitation/device; no raw device identifiers exported. However, it has
**zero ProductStore Family/entitlement matches**; Friends↔ProductStore identity
overlap is0. Friends schema has no Family assignment and restricted tables remain0.
Existing NL identities resolve to control-provider and mailbox roles, not an
authoritative Family-bound restricted gateway. Neither identity was repurposed.
Migration/root signing are now explicitly authorized **only after unambiguous
Phase A**; that condition is unmet, so no migration/signature/grant/admission edit.
Need protected authoritative existing-Family assignment and accepted NL gateway
binding before deriving delegation/revision floors. Do not guess from relay max9.
Root↔packaged↔staged anchor and inert staging permissions PASS; API/AWG/TCP PIDs
unchanged. OAuth absent; token-input phase not reached. No runtime/phone actions,
new material, push or FIELD-1. [Exact evidence and owner action](releases/2026-10-01-5n-prod-materials.ru.md).

### Historical initial preparation — OWNER ACTION REQUIRED

Preparation only, source `ff9fb09`/entry `f082c10`: staged root-only0700 directory
`/opt/apps/family_connect/restricted-materials-stage-20261001` on RU/NL; files0600.
RU: exact public anchor, deny-all admission, dedicated Ed25519 SSH sync key and
pre-existing verified NL pins. NL: public sync key/restricted authorization fragment
and exact bootstrap service template, **not installed/activated**. Existing offline
root available/matches ControlTrust; no new root or delegation signature generated.
Need authoritative Family/gateway identity binding, owner canary selection and
server-only Yandex token (unavailable). Issuer/key/gateway/CRL not prepared with
invented identities; CRL publisher requires migrated DB, prohibited in this task.
Must resolve that sequencing before retry, no automatic deployment.
Permissions/SSH configuration validation +18 backend/native contract tests PASS;
actual missing production delegation/CRL/gateway validation not claimed.
HTTPS renewal timer active, latest01.10 09:07UTC success/no-op, next21:16:13UTC;
verified cert expires05.10 12:25:56UTC (~4d2h26 at09:59UTC). No manual renewal
currently indicated; previous28.09 failures preserved in report.
Existing API/AWG/TCP unchanged, restricted tables0, no service/reload/migration/
public release/catalog/push/FIELD-1. No new secrets under repo; existing ignored
offline key remains in its documented location, not moved/copied.
[Full material inventory, validation and owner actions](releases/2026-10-01-5n-prod-materials.ru.md).

## 5N-PROV-1 — authorized deployment preflight STOP, 01.10.2026 09:32–09:33 UTC

**DEPLOYMENT FAILED / ROLLED BACK — prerequisite failure до deployment; rollback
не требовался и не выполнялся.** Authorization получена для source `ff9fb09`, но
новое условие пользователя требует STOP при отсутствии обязательных материалов.
Read-only SSH подтвердил оба разрешённых IP/host keys. На RU и NL отсутствует
`/opt/apps/family_connect/friends-restricted/`: RU issuer/delegation/anchor,
admission/CRL/sync credentials не подготовлены; NL gateway profile/provider.env
не подготовлены, OAuth не configured для required нового сервиса. Другие private
stores/diagnostic credentials не искались и не подставлялись.
Никакого partial rollout: no upload, key generation, migration, service/ingress
change или device action. Existing RU Friends API + RU/NL AWG/TCP active,
NRestarts0; TLS1.3 verified, public status HTTP200, certificate до05.10 12:25:56UTC.
Known peer-worker Docker unhealthy сохраняется, unrelated fixes не выполнялись.
Deployment-induced API interruption0s (no transitions), не continuous SLA test.
Redmi READY/restart/rehearsal и final FIELD APK не выполнялись; prior field52
BLOCKED evidence сохранён. Public remote main проверен: `2644790`, без изменений.
[Точный audit, missing material, health и stop boundary](releases/2026-10-01-5n-prov1-production-restricted-provisioning.ru.md).
Production/code/catalogs unchanged; no push, no Krasnodar FIELD-1.

## Historical implementation checkpoint — ff9fb09, deployment authorization then pending

После уточнения BOOT-1 contract реализован **локально**, не deployed:
activated Friends proof → existing HTTPS `/friends/restricted-readiness` →
active device/invitation/grant/revision/CRL checks → public-only Family certificate
на existing Ed25519 identity + BOOT-1 v1. Online issuer делегирован existing offline
control root; root не переносится на сервер, directory standalone signature нет.
Bootstrap seed `join_url` разрешён, только server READY; dedicated rooms не prewarm.
Android native validation + единый Keystore/AtomicFile bundle, replay floors,
persisted300s cooldown, bounded foreground prewarm, valid-cache CONNECT без refresh
wait. Private key остаётся existing Device Identity, TLS assembly только в памяти.
Directory≤1h неизменён; текущий CRL15min дополнительно ограничивает readiness.
Python95/JVM193/Go race+vet/fresh arm64 JNI PASS; lint0errors37warnings.
APK не собран/не установлен; real phone всё ещё имеет last-observed BLOCKED state
ниже. Historical audit `a88b104` и unpushed `9c82152`/`3d9fd7c` сохранены.
Нужна отдельная authorization: owner-only RU Friends API/issuer/sync + новый NL
seed/broker, затем in-place private validation и local rehearsal. No production
deployment, push, final FIELD artifact или Krasnodar FIELD-1.
[Реализация/evidence](releases/2026-10-01-5n-prov1-production-restricted-provisioning.ru.md),
[точный controlled rollout/rollback](../deploy/friends/restricted/README.md).

### Исторический docs-only audit — BLOCKED до уточнения, a88b104

Source audit: Friends `/friends/*` не выдаёт Family TLS/BOOT-1; ProductStore
`/v2/*` — другой контур, fixture issuer не production. Accepted BOOT-1 v1 требует
**live seed join_url**, заранее созданный сервером, и mTLS authentication без
standalone signature. Запрет всех live room URLs несовместим с reuse v1: уточнить
bootstrap seed versus dedicated URL и signing contract. Runtime/API/Android
integration **не реализована**, deployment gate не достигнут. Physical BLOCKED
ниже сохранён. Docs-only, без production/device changes, APK, push или FIELD-1.
[Gap, key model, TTL и условия продолжения](releases/2026-10-01-5n-prov1-production-restricted-provisioning.ru.md).

## LOCAL device readiness — 01.10.2026, BLOCKED

Private `.friends` field52/code52 (source9c82152) установлен IN PLACE на Redmi,
beta signature, activation/UID сохранены. Internal view: Device Identity PRESENT,
normal provisioning PRESENT_VALID; **restricted provisioning и BOOT-1 ABSENT**.
После process restart то же состояние, launch PASS; normal live entitlement
UNKNOWN. Это первое private-state evidence, прежний UNKNOWN не переписан.
Production Friends API не выдаёт Family TLS/BOOT-1 provisioning; existing mTLS
refresh требует уже provisioned profile. Поэтому prewarm/restricted rehearsal
BLOCKED, fixture identity не подставлялась. APK — readiness-only, не FIELD-ready.
Fresh arm64 native/APK/signature/scan, JVM188/Python50(+1skip), Go race/vet,
lint0errors37warnings PASS. APK SHA
`604f06722a702475a03dd5aec8bff1f99c82706c65dc5fb0e92e400f45a0756a`.
Phone normal/idle, без VPN/forced failure, UI probe удалён. Public beta51/catalog
не менялись; no push/production deployment/Krasnodar FIELD-1.
[Lifecycle, artifact и точный blocker](releases/2026-10-01-field1-device-readiness.ru.md).

## LOCAL FIELD-APK PREFLIGHT — 01.10.2026

**BLOCKED по private-state/BOOT-1 verification; in-place install и UI smoke PASS.**
USB Redmi Note9Pro/Android12/arm64: установленный exact public beta51 подтверждён
по SHA/certificate, обновлён только `adb install -r` до private FIELD APK2644790.
Installed SHA`f0a625c8e8485980cf2f9bc1d5577881b5e59393c86cedfdc92f4e3c7d994f41`,
beta certificate прежний; package/code51, UID/firstInstallTime сохранены.
До/после UI activated («Пригласить друга»), без reactivation prompt, launch PASS;
Auto подтверждён в dropdown, режим не менялся, CONNECT не выполнялся.
Non-debuggable/run-as denied, target instrumentation отсутствует: private Device
Identity/provisioning и BOOT-1 presence/validity/usability **UNKNOWN**, не ABSENT.
Cache не создавался/не переносился; raw private files/XML не сохранялись.
FIELD APK оставлен на телефоне; Wi-Fi OFF/cellular ON как до проверки, VPN не
запускался. Временный UI-only shell probe удалён, uninstall/pm clear/reset не было.
Production/public artifacts/catalogs не менялись; **Krasnodar FIELD-1 NOT STARTED**.
[Локальный отчёт и точная граница доказательства](releases/2026-10-01-field1-local-preflight.ru.md).

## FIELD-1 APK packaging — 01.10.2026

**BUILD PASS; FIELD-1 NOT RUN.** Из чистого detached worktree2644790 (origin/main,
ahead/behind0/0) собран private arm64 Friends APK без runtime/source changes.
Основное дерево уже имело документы ops-аудита: сохранены, в сборку не включены.
Fresh normal/restricted JNI, Go1.26.1/NDK27.2, non-debug `.friends`, beta51/code51;
persistent beta certificate совпадает с проверенным публичным beta51. APK SHA256
`f0a625c8e8485980cf2f9bc1d5577881b5e59393c86cedfdc92f4e3c7d994f41`.
Package/signature/version update compatibility PASS, без uninstall; подключённый
телефон недоступен, actual install/private-state survival не проверялись.
BOOT-1 Family activation/cache должны уже существовать: APK их не создаёт и
не переносит из diagnostic package. Auto доступен, прошлый transport preference
сохраняется. JVM185/Python19(+1skip)/lint0errors37warnings/provenance/signature/
alignment/secret scan PASS. APK только в `/tmp/fc-field1-build-2644790/artifacts/`;
public artifacts/catalogs/версии/production не менялись; no push, no FIELD-1.
[Полный build receipt и ограничения](releases/2026-10-01-field1-apk.ru.md).

## Operational snapshot — 01.10.2026, 05:29–05:31 UTC

Read-only audit RU/NL:27 устройств,23 не отозвано,4 отозвано;
81 приглашение/27 использовано. NL22 AWG peers:5 handshake<5мин,11<24ч,
5 с передачей за15с; RU10 peers:0/0/0. Это устройства/peers, не уникальные
люди или DAU; friends TCP established inbound0 на обоих в снимке.
CPU busy RU22.93%/NL4.75%, available RAM1091/553MiB; перегрузки CPU/RAM
в снимке нет. Диск RU69.1%/8.63GiB свободно, NL23.8%/13.90GiB;
vda await71.73/107.95ms — задержки сохраняются, причина этим аудитом не установлена.
AWG/TCP/API active, product/control healthy; peer-worker systemd active,
Docker unhealthy сохраняется. HTTPS8443/TLS PASS, snapshots свежие,
served certificate до05.10 12:25:56UTC. Настройки/службы/версии не менялись.
Repository finalization завершена ранее: HEAD/origin/main2644790; этот
аудит не запускает новый rollout, push или FIELD-1.
[Методика, сравнение и ограничения](releases/2026-10-01-vpn-health.ru.md).

## CURRENT PRODUCT STATE — 01.10.2026 / MVP Connectivity Orchestrator

**MVP CONNECTIVITY ORCHESTRATOR = PASS — isolated physical follow-up.**
Исходный FAIL ниже сохранён. Fresh current-source arm64 normal JNI воспроизвёл отказ:
Chrome выбирал объявленный IPv6 address, а isolated Amsterdam не имеет IPv6 egress;
backend `network is unreachable` закрывал поток после локального TUN handshake.
Fix `afb6c1b` убирает только неподтверждённый IPv6 source address automatic TCP,
сохраняя обе capture routes и policy. Тот же JNI: Chrome2/TLS200×2 PASS,
normal572ms, alternate3525ms, restoration1414ms/retained FAILED PASS. Fresh BOOT-1
AWG→WG→TCP diagnostic exhaustion → restricted32621ms, Chrome6/6 и HTTPS/TLS2×200,
Family DNS125 requests/115 responses,18 concurrent TCP PASS. Smoke602.6s без
crash/flapping/retry storm; injected loss → RESTORING→FAILED138ms с retained VPN
и blocked ordinary TCP. DNS/TCP bypass0 в принятом primary-user route/backend/app
scope, не modem-wide pcap; UDP/IPv6 fail-closed, protect116/denied0, underlay DNS16
без роста. PSS peak120019KiB, RSS194792KiB; battery31.3→32.3°C USB. Не скрыты
mux ProtocolErrors7/DNSTimeouts8/OpenErrors1, без browser failure; не zero-error SLA.
JVM185/Python98/race/vet/native/APK/lint PASS; live AWG/full four-ABI/emulator matrix
не повторялись. Current reviewed source `12d4f40`, fix `afb6c1b`, provenance `87272e1`.
Diagnostic APK/cache/remote fixtures/private activation удалены; VPN owners0.
OAuth только в process memory для final live run; never persisted. Public versions,
catalogs/invitation pages/production неизменны; no push. **FIELD-1 NOT STARTED; STOP.**
Подробности и native/APK hashes — [follow-up ledger](releases/2026-09-30-mvp-connectivity-orchestrator.ru.md#follow-up-01102026--два-acceptance-blockers).

### Исходная acceptance 30.09 (исторический FAIL)

**MVP Connectivity Orchestrator = FAIL acceptance; implementation complete, restricted live BLOCKED.**
Starting/main/origin HEAD8886fd03398ffecd82ab4f66ff6d9884846e628c, clean.
Pure deterministic core + existing ConnectionService worker, single TcpVpnService
guard для automatic AWG JNI/TCP/restricted adapters. Normal configured preference/LKG
→ alternate normals → cached BOOT-1/fresh dedicated whole-device; no manual room.
Healthy path sticky, per-candidate retry0, один restoration pass;20s/200s candidates,
300s CONNECT, bounded backoff, local128-event diagnostics, cancellation/auth terminal.
Main/Friends default Auto, explicit manual/managed behavior сохранён.
Restricted library/activation пока opt-in diagnostic, не public rollout.
Final Redmi/cellular: automatic TCP723ms, forced AWG→TCP2457ms; controlled loss →
RESTORING → TCP1427ms, второй loss → FAILED с VPN/full routes и blocked ordinary TCP.
Java ordinary HTTPS2×200/TLS verified, но Chrome на двух контрольных public sites
даёт ERR_CONNECTION_CLOSED при активном VPN: **normal browser FAIL**, причина ещё
не локализована между existing cached JNI/REALITY fixture/Chrome; не списывать на parser.
Exhaustion автоматически вызывает restricted candidate; без activation → bounded
BOOTSTRAP_UNAVAILABLE/FAILED6245ms. Fresh BOOT-1/Room Broker live заблокирован:
нет `YANDEX_TELEMOST_OAUTH_TOKEN`/новой isolated activation. Не переносить старый
5N.6 PASS на Auto. JVM185/Python76/race/vet/build/lint PASS; native instrumentation
не запускался, полный current-source normal four-ABI rebuild не заявлен.
Текущий gate и failed attempts/remaining physical checks:
[отчёт Orchestrator](releases/2026-09-30-mvp-connectivity-orchestrator.ru.md).
FIELD-1 **NOT STARTED**, только после полного PASS; production/версии не менялись.

**Family Connect = resilient connectivity for families**, не protocol picker.
Приоритет — непрерывность связи и автоматическое восстановление, с быстрыми
обычными транспортами в нормальной сети и restricted carrier как резервом.
Исходный UX одной кнопки реализован; полная physical acceptance не завершена;
детали — [architecture](architecture.md).

**WEBRTC-EU-6 / 5N.6 = PASS**, isolated physical30.09,18:53–19:04 UTC. Existing
ConnectionService/TcpVpnService/Xray packet engine подключены к shared Family
Mux/DNS через opt-in restricted backend. Redmi cellular/Wi-Fi OFF: cached BOOT-1
→ fresh dedicated READY/Family TLS → real TUN → Chrome2 sites/6 successful visits,
14 concurrent TCP,98 Family DNS, Android verified end-site TLS/HTTP200×2.
Smoke543.7s; controlled gateway failure оставляет VPN/routes и блокирует обычный
TCP/browser, owner health unavailable. Destination DNS/TCP bypass=0 в принятом
primary-user route/backend/app scope, не modem-wide pcap; UDP/IPv6 fail-closed.
Underlay85 protected sockets, provider DNS16 без роста после TUN; cleanup PASS.
Focused JNI string lifetime и gateway16/client32 fixes приняты повторным run;
все неуспешные попытки сохранены. Go/packet race/vet, Python50, Android JVM172,
native/build/lint0 errors/36 warnings, docs/source guards PASS. PSS peak82195KiB.
Отдельный diagnostic `.eu6` built/installed/removed, public beta51/code51/production
не меняются. Normal AWG/TCP owner сохранён; повторный physical normal-path test
не проводился в EU-6. Тогда Orchestrator **NOT STARTED**; текущая отдельная задача выше.
[Отчёт EU-6, hashes/metrics/leak scope/rollback](releases/2026-09-30-webrtc-eu6-android-full-device.ru.md).

**5N-BOOT-1 = PASS**, isolated physical acceptance30.09, 15:37–15:38 UTC.
HEAD `f487a429141da64297038e8a96237205fd1ac060` + focused runner cleanup-order fix;
исходная implementation base `51d0ad788b651f47ba22e33b4a9991a1283661ce`.
Real automatic Telemost seed READY → direct cellular mTLS directory/cache → restart →
deliberately unavailable diagnostic control endpoint → cached bootstrap/Family TLS →
existing Room Broker/fresh dedicated READY → descriptor через bootstrap → отдельная
dedicated Family TLS/setup binding → A/AAAA/NXDOMAIN + four verified HTTPS200.
Redmi Note9 Pro / Android12 / arm64, Wi-Fi OFF/no VPN; no adb reverse, SSH forwarding
или manual room URL. No bootstrap data-plane/Mux. Первый live run прошёл data proof,
но runner преждевременно проверял cleanup event; исправлен только порядок проверки,
20 focused Python tests PASS, повторный physical run и cleanup PASS.
Diagnostic APK code4/name5N.5-test-only установлен и удалён; runtime binaries не менялись.
Private fixtures/test processes BOOT-1 удалены; port18444 освобождён тогда.
Исторический STOP BOOT-1 superseded отдельной авторизацией задачи EU-6 ниже.
Предыдущие focused Go/race (bootstrap x10)/vet, Python118, Android native/APK/JVM9/lint,
docs/source guard — PASS; lint содержит только existing manifest/UI warnings.
Нет production deployment, version bump, public release/catalog changes или push.
[Отчёт BOOT-1](releases/2026-09-30-webrtc-5n-boot1-bootstrap.ru.md) ·
[Контракт/runbook](../carrier/bootstrap/README.md). Исторический ledger ниже сохранён.

| Уровень | Фактическое состояние |
| --- | --- |
| IMPLEMENTED IN CURRENT BETA | Device Identity, FAMILY admission, invitations/provisioning; Android/Linux/Windows; normal AWG/TCP используются beta-пользователями. Android VpnService/VPN lifecycle уже существует. |
| PROVEN IN ISOLATED ACCEPTANCE | 5N.1–5N.5, Family TLS1.3, selective-repeat ReliableStream/real RTP gap recovery, long-duration goodput, Internet TCP/end-site HTTPS TLS, mux/Family DNS/containment, automatic Room Broker **PASS**. Physical Redmi → real Telemost VP8/RTP → Amsterdam. |
| PROVEN IN ISOLATED ACCEPTANCE | **5N-BOOT-1 PASS**: cached mTLS directory/restart, control-only real seed, Family auth, broker READY-before-descriptor through bootstrap, separate dedicated session/DNS/HTTPS and cleanup. Diagnostic unreachable-endpoint fault, not a carrier-wide block/field claim. |
| PROVEN IN ISOLATED ACCEPTANCE | **5N.6 PASS**: existing Android VPN/packet engine → dedicated Family Mux TCP/DNS, ordinary Chrome, protected underlay, captured/rejected UDP/IPv6, session-loss fail-closed, bounded cleanup. |
| IMPLEMENTED / ACCEPTANCE FAIL | Minimum viable Connectivity Orchestrator: normal lifecycle partial PASS, Chrome normal FAIL, fresh restricted Auto acceptance BLOCKED. Затем только после полного PASS — Krasnodar FIELD-1 (NOT STARTED), затем50–100-user beta. |

5N.5 доказал simultaneous public HTTPS, mixed TCP + DNS, exact delivery и
fairness/bounded buffers. Room Broker доказал official Telemost API, server-only
OAuth, gateway-first READY и automatic Android descriptor/join без manual URL,
Family TLS + multiple HTTPS200. **Это принятые факты, не preparation-only.**
Но broker acceptance использовала temporary control ingress (SSH forwarding +
adb reverse). **Production restricted bootstrap нет:** при недоступном ordinary
Family API получение initial dedicated room физически доказано без forwarding
в diagnostic cached-state path; production путь не выпущен. В тесте normal endpoint
заменён на недоступный `https://127.0.0.1:1`, а не заблокирована вся сеть оператора.
5N mux/DNS подключён к diagnostic TUN; EU-6 isolated physical acceptance PASS,
Krasnodar FIELD-1 NOT RUN;
restricted rollout beta-пользователям и product-complete orchestration отсутствуют.
Нет generic UDP в restricted path; global ReliableStream HOL остаётся; production
capacity и iOS client не заявляются. Telemost — заменяемый недоверенный carrier;
security boundary — Device Identity / Family admission / Family TLS.

### Версии — последний документированный выпуск, не новый rollout audit

| Платформа | Собрано / принято ранее | Public / invitation | Установка / ограничения |
| --- | --- | --- | --- |
| Android | 0.1.18-beta51 / code51 | APK/updater/invitation beta51 | Redmi обновлён поверх beta50 по release report; заново не проверялось. |
| Linux | 0.2.11, legacy preview5b02e8cb9fde119f; AppImage/DEB | HTTPS AppImage/DEB, invitation AppImage; legacy updater sequence9 | Clean Ubuntu24.04 install/URI/upgrade/reinstall принят ранее; текущие установки не опрашивались. |
| Windows | 0.2.15, source2ffba77; native/compat CI | GitHub/HTTPS, invitation; windows catalog sequence11; 0.2.14 compatibility fallback | Проблемный Windows10 device acceptance остаётся открытым; publisher signature нет. |

[Cross-platform release](releases/2026-09-26-server-list-crossplatform.ru.md) ·
[Linux packaging](linux-appimage-deb.ru.md) · [Downloads/checksums](releases.md).
Diagnostic APK code4/name5N.5-test-only для mux/broker был built/test-installed,
затем удалён; никогда не public beta. Public artifacts/install/invitation page
в этой задаче повторно не проверялись. Каталоги и checksums не менялись.

### Operational state — отдельно от product critical path

После sync на исходном HEAD: [Linux control preview](https://github.com/Joker20380/family_connect/actions/runs/36718292459)
PASS; [phase0](https://github.com/Joker20380/family_connect/actions/runs/36718292492)
tests PASS, failover FAIL на Build isolated failover stack;
[Client builds](https://github.com/Joker20380/family_connect/actions/runs/36718292488)
Linux/Windows/Windows compatibility PASS, Android build/unit/lint PASS, emulator
WG/AWG/TCP/Auto lifecycle FAIL, release SKIPPED. Причины здесь не диагностировались;
это отдельные открытые CI issues, не отмена isolated 5N/Room Broker acceptance.
Последний документированный production deployment — disk mitigation29.09;
30.09 read-only audit: NL disk latency, RU API restart cause, worker unhealthy/
outbox и client end-to-end остаются открыты. TLS renewal тогда PASS, мониторинг
продолжается; новых production checks/deployments здесь нет. Изолированная EU-6
приёмка описана выше и не закрывает эти operational issues.

**NEXT = MVP Connectivity Orchestrator (NOT STARTED).** BOOT-1 и5N.6 PASS в
изолированном scope; текущая задача здесь останавливается. Второй carrier/Home Gateway —
backlog; performance/FEC/HOL — later evidence-driven work.
[Authoritative plan](PLAN.md) · [Rebaseline: docs checks, boundaries, rollback](releases/2026-09-30-product-engineering-rebaseline.ru.md).

## Historical checkpoints — preserved evidence

Все записи ниже сохраняют контекст своих дат. Их STOP/current/next и старые
версии не переопределяют CURRENT PRODUCT STATE; завершённый sync не разрешает
push в этой задаче. Runtime/production rollout не выполнялся и откатывать нечего.

## 30.09.2026 — repository synchronization checkpoint

User-authorized main→origin/main sync only; no development or deployment.
Starting HEAD `a8961e8`, fetched origin `8e36858`:58 existing outgoing commits,
all26 supplied milestone IDs are ancestors. Completed operational worker and
sanitized VPN/disk/TLS reports preserved in separate commits; original work retained.
Focused reconciliation suite32 PASS, unit verify PASS, publication/history scan PASS.
Latest pre-sync remote phase0 run36268143806 had tests PASS but failover build FAIL;
this sync does not claim green full CI or repair that existing failure.
Versions remain Android0.1.18-beta51/code51,Linux0.2.11,Windows0.2.15;
no public artifact/install/invitation revalidation. No production changes.
[Audit, commit inventory and verification procedure](releases/2026-09-30-repository-sync.ru.md).
Push authorization supersedes older no-push notes only; all development STOP gates
and operational follow-ups below remain unchanged. Post-push SHA equality is checked
after this checkpoint commit and reported in the task result.

## 30.09.2026 — read-only VPN audit, 10:44–10:46 UTC

Devices25/valid21/revoked4 unchanged. NL5 handshakes<5min/9<24h/4 transferring
in10s; RU0. NL AWG TX1.70Mbit/s10s,1.81Mbit/s60s; CPU4.14%/5.55%.
RU CPU13.11%,AWG idle. AWG/TCP starts unchanged; access API active but its
start changed to30.09 03:28:04UTC; cause not yet established.
HTTPS:8443 TLS PASS/cert until05.10 12:25:56UTC; renewal09:02:48UTC success.
NL disk await96.92ms60s/138.56ms today remains high; worker Docker unhealthy.
First SSH attempt failed No route to host on both, retries successful.
No deployment/version change. [Evidence/remaining checks](releases/2026-09-30-vpn-health.ru.md).

## 29.09.2026 — load increase confirmed, 19:39–19:41 UTC

Read-only recheck: NL AWG TX17.19Mbit/s over10s (previous0.0065),
subsequent60s average9.03Mbit/s; CPU busy18.39%/11.68% respectively.
NL4 recent handshakes/3 transferring, devices25/valid21 unchanged; RU AWG idle.
NL available RAM487MiB, minute disk await95.78ms: latency remains open.
Services active/starts unchanged; HTTPS:8443 PASS; worker still unhealthy.
No rollout/version change; see [repeat audit](releases/2026-09-29-vpn-health.ru.md#повторный-замер-19391941utc).

## 29.09.2026 — read-only VPN snapshot, 17:51–17:52 UTC

Devices25/non-revoked21/revoked4; invites79/used25. NL20 peers,
4 latest-handshake<5min/11<24h/3 transferring in10s; RU10/0/0/0.
CPU10s NL4.01%/RU12.93%; available RAM512/1087MiB; disk24%/69%.
AWG/TCP/API active, starts unchanged; verified public HTTPS:8443 PASS.
NL daily-to20:50MSK disk await144.30ms remains elevated (mixed pre/post mitigation).
Peer worker active but Docker unhealthy; outbox/worker cycles not rechecked.
No versions, deployment or services changed; previous uncommitted work preserved.
Details/checks/remaining work: [evening audit](releases/2026-09-29-vpn-health.ru.md#вечерняя-проверка-17511752utc).

## 29.09.2026 — повторный read-only VPN audit, 12:32–12:35 UTC

25 activated devices/21 non-revoked/4 revoked, unchanged; NL20 peers,
11 latest-handshake<24h/3<5min/3 transferring in10s; RU10/0/0.
AWG/TCP/API active, starts unchanged. HTTPS **:8443** verified, cert until
05.10 12:25:56UTC; automatic renewal service09:04:21UTC success.
Peer worker running,17 recent cycles exit0, but Docker unhealthy: inherited
HTTP API healthcheck does not match worker role. No repair in this read-only task.
Disk await today-to15:30MSK NL144.63ms/RU33.34ms, not a post-mitigation-only sample.
Versions unchanged; no rollout/restart. Details and remaining checks:
[audit follow-up](releases/2026-09-29-vpn-health.ru.md#повторная-проверка-12321235utc).

## 29.09.2026 — disk I/O mitigation deployed, residual NL latency open

[Diagnosis/results/rollback](releases/2026-09-29-disk-io-recovery.ru.md).
RU persistent peer supervisor deployed (existing image0.2.1), old timer disabled;
same15s post-cycle/60s timeout, fresh child processes, sanitized bounded logs.
NL Fail2ban1.1.0-9 SSH-only22, control/operator exclusions;9 banned in final sample.
Final comparable ~minute writes RU17.83→9.79MiB,NL3.40→1.87MiB;
io.full stall RU3.20→1.48s,NL2.22→1.29s. Subsequent3min writes8.47/2.32MiB/min,
write-await14.77/117.31ms RU/NL. **Residual NL latency remains**;
short varying-load samples do not prove full repair or a provider fault.
32 tests PASS;36 observed live cycles0failures/outbox3matched0errors/oldest10s;
chat-sync/HTTPS PASS, VPN/API/mailbox start times unchanged. No client version change.
Monitor sustained behaviour/remaining NL latency and automatic TLS renewal.

## 29.09.2026 — TLS renewal/reload recovery PASS, 08:32 UTC

User-authorized start of `family-connect-product-cert-renew` completed08:32:25UTC,
Result=success/ExecMainStatus0. Certbot reported not yet due; existing renewed
certificate was applied by nginx validation/reload. Public verified HTTPS now serves
IP185.251.89.19 certificate valid through05.10 12:25:56UTC (previously01.10).
Certificate symlink mtime28.09 21:24:29UTC coincides with prior timeout;
issuance was already on disk, but public ingress still served the old certificate.
AWG/TCP/API starts unchanged, timer active/next29.09 09:18:29UTC.
No client/version/config change. Monitor next scheduled cycle; timeout cause not
established. [Recovery details](releases/2026-09-29-vpn-health.ru.md#tls-recovery-29-сентября-0832utc).

## 29.09.2026 — read-only VPN health, 08:15–08:18 UTC

[Аудит](releases/2026-09-29-vpn-health.ru.md):25 activated devices/21 non-revoked/4 revoked;
NL20 AWG peers/12 last-handshake<24h/3 transferring in10s, RU10/0/0.
28.09 server-local MSK: NL AWG≈13.784GiB, CPU user+system5.41%, RU19.95%;
disk await NL159.09ms/RU37.70ms remains a risk, not diagnosed cause.
AWG/TCP/API active; public HTTPS TLS verified. **RU cert renewal failed(timeout)**
28.09 21:24:29UTC; live certificate expires01.10 12:19:14UTC; next timer
29.09 09:26:17UTC. Renewal success must be checked; no repair/restart performed.
Versions unchanged: Android0.1.18-beta51/code51, Linux0.2.11, Windows0.2.15
(last documented release, not a fresh artifact/install audit). No rollout/rollback.
Full outage history and end-to-end client acceptance remain unverified.

## 28.09.2026 — 5N-RB-1 = PASS: automatic Telemost room broker

Authorized isolated gate starts8d899ab; core ff25246, adapters/tests398df64.
Official PUBLIC create HTTP201, env-only server credential, bounded lifecycle:
15s creation/45s READY/60s unused TTL,1 outstanding/device/32 global.
Existing Family admission gates control API; gateway-first descriptor plus one-time
device/setup binding over unchanged Family TLS. One physical Redmi/cellular→
Amsterdam smoke: automatic fresh room, READY before issue, Family TLS,4 verified
HTTPS200 + A/AAAA/NXDOMAIN, DNS guard0; native21.922s, mux7.499s, exit0.
Focused race/vet, ProductStore-backed mTLS/binding, Python57, Android build/6JVM/lint
PASS. No manual room URL. Control ingress uses disposable SSH+adb reverse, not a
claim of production restricted-network bootstrap. Diagnostic code4 test install
removed; public/installed production/invitation versions unchanged, no rollout/push.
Foreign VPN work preserved separately. [Report/limits](releases/2026-09-28-webrtc-5n-room-broker.ru.md).
**STOP after5N-RB-1**; no5N.6/TUN/UDP/Orchestrator/performance or production work.

## 28.09.2026 — WEBRTC-EU-5 / 5N.5 = PASS: mux TCP + Family DNS

Authorized mux TCP+DNS task starts at `812f4cb5913cad412d29f2f4f605c55327ce7d25`.
Foreign VPN audit hunks/reports preserved. Core `a22742a`, DNS hardening `0014fd2`,
final clean tested CLI/APK `c26c2b7` (late DNS-cancel retention corrected),
harness `03582fb`/`4687c3d`/`bb867a0`/`083763d`. Default16/max32 logical streams;
one admitted TLS/reliable/Telemost path. Physical4 concurrent public verified
HTTPS200; mixed304.137659s,5 persistent streams,18,751,488B each way exact bulk,
0.997222Mbit/s bulk aggregate,915 interactive replies and171 Family DNS responses.
Native DNS guard proves zero destination lookups after admission (bootstrap separate).
Final A/AAAA/NXDOMAIN PASS, bad-MAC/corruption/duplicate/missing/cross-stream0.
Fair scheduling/isolation/credit bounds PASS; global ReliableStream HOL remains.
Final mux HWM401664/475136B, sockets/retained0. Natural gap1 recovered in earlier
accepted mixed session; final mixed gaps0, retransmissions2/1. No capacity claim.
Go race×3/vet/modules/8 fuzz,Python1004+3 documented skips,Android build/6JVM/lint/
6 native suites PASS;507 canonical exact, live auth/replay/legacy TCP/lifecycle/
network-loss and fresh-session regression PASS (exact revision scope in report).
Diagnostic code4 installed then removed;42 Android/52 gateway recorded IDs absent,
private artifacts/worktree/test images removed, radios1/1 restored. No production,
public/invitation version change or push. No unfinished5N.5 acceptance checks.
[Report/evidence/limits](releases/2026-09-28-webrtc-eu5-mux-dns.ru.md).
**STOP after5N.5**; Room Broker/5N.6/TUN/UDP/Orchestrator require separate work.

- production и current released versions этой задачей не менялись
  (Android beta51/code51, Linux0.2.11, Windows0.2.15).
- active engineering critical path — **5N: Restricted WebRTC Android→EU**
  (Telemost VP8 → Linux EU gateway → TCP+DNS → Internet).
- **WEBRTC-EU-1 / 5N.1 = PASS**: настоящий local Linux ↔ Telemost VP8 ↔ Amsterdam.
- **WEBRTC-EU-2 / 5N.2 = PASS**: physical Android↔Telemost VP8↔Amsterdam,
  372 exact echoes,7 sizes/100×1/16KiB/30s/5min, без TUN/DataChannel substitution.
- **WEBRTC-EU-3 / 5N.3 = PASS**: physical Android Family E2E over VP8,
  374 exact echoes,302.001s sustained.
- **WEBRTC-EU-4 / 5N.4 = PASS**: single TCP, physical HTTPS/public10MiB,
  controlled full-duplex300.821s;5N.5 PASS above,5N.6 NOT RUN.

## 28.09.2026 — WEBRTC-EU-4 / 5N.4 = PASS: one admitted TCP stream

Explicitly authorized single-stream forwarding above existing Family TLS/reliable
VP8. Core2b977da/RST fixfa3c027; initial harness2e81984, telemetry554acbb,
observer2c5c63e, final tested clean CLI/APK63f6bde. Physical Redmi Note9 Pro/Android12
cellular→Family TLS→ReliableStream→Telemost real SFU→Amsterdam→public TCP:
example.com443/Cloudflare443 verified end-site TLS,HTTP200; public10,485,760B download.
Controlled Amsterdam TCP fixture10MiB each direction exact; sustained22,511,616B
each direction/300.820842906s/1.197343416Mbit/s aggregate. Public download and
controlled-loopback upload/duplex are distinct proofs, not a public-fixture claim.
FIN/half-close/refused/timeout/RST/session loss/fresh recovery PASS;13 final cases.
Sustained RTP gaps0/recovered0; data retries0,teardown3; exact accepted transfers
bad-MAC/corruption/duplicates/missing0. CarrierQ sampled4/7, staging32011/42956B
<49172B bound, reliable retained76656/80718B, final sockets/buffers0.
Go race×3/vet/modules/five fuzz,Python984+3 documented skips,Android build/6JVM/
lint/native PASS; physical canonical518 exact, auth negatives/replay/lifecycle PASS,
controlled reliable gap1/1 recovered with8 exact echoes. Earlier failed attempts
retained, no production/firewall changes. [Report/evidence](releases/2026-09-28-webrtc-eu4-single-tcp.ru.md).
Only isolated APK5N.4-test-only/code3 was installed, then removed.28 Android/33
gateway recorded PIDs absent, temp fixtures/worktrees/private credentials/logs/builds
removed; radios1/1 restored. Production/public/invitation versions unchanged.
No unfinished5N.4 acceptance checks; no TUN/mux/5N.5/rollout/push or production-ready
claim. Foreign VPN audit changes retained separately. **STOP after5N.4.**

## 27.09.2026 — использование VPN за26–27.09

[Read-only аудит](releases/2026-09-27-vpn-health.ru.md), сутки Europe/Brussels,
27.09 до23:10: Friends23 устройства/19 действующих (+1 к утру26.09).
NL минимум9 устройств сегодня,3 свежих handshake/рост счётчиков в коротком замере;
RU0 за24ч. Полного DAU/истории TCP нет. AWG NL19.143ГиБ вчера/13.764ГиБ сегодня,
RU≈1.2МиБ вчера/ниже точности сегодня. CPU среднее NL5.68%/6.02%, RU20.31%/20.19%.
AWG/TCP active, сегодня без restart по current start; RU вчерашний restart связан
с SIGTERM fix. Journal reads timed out и совпали с дисковым давлением;
NL iowait1.96% к21:14UTC, RU6.38% к21:17UTC, RU sync success; всплеск закончился.
Историческое отсутствие ошибок
не доказано; остаются мягкая диагностика диска, история устройств/TCP и E2E.
Версии beta51/code51, Linux0.2.11, Windows0.2.15 и production не менялись;
rollout/rollback нет, проверки агрегатов PASS, platform tests не требовались.

## 27.09.2026 — 5N-PERF-2 = PASS: reliable operating envelope

Fixed16KiB/sender8/receiver16/RTO1s; no protocol/default changes, TCP/TUN or5N.4.
Starting clean `ca4f9e7`; runtime telemetry `df6149e`, tested CLI/APK `04f39f2`,
final harness `4475560`. Baseline cap2/300s reproduced:3935 exact,1.716169Mbit/s.
Sweep0.5/1/1.5/2/2.5/3,120s each. Highest long reliable goodput **1.742311Mbit/s**
at cap3,1800s,23935 exact echoes; conservative demonstrated **1.480531Mbit/s**
at cap1.5,900s,10169 exact. Highest short1.795686Mbit/s. No sustained overload
threshold/hard carrier ceiling established; cap2.5 severe transient is not a
rate-specific threshold. Across9 sessions45452 exact,29/29 block gaps recovered;
accepted TLS bad-MAC/corruption/duplicate/reorder/missing/unexpected closure0.
Highest long RTT avg/p50/p95/p99=599.271/570.229/756.025/1010.886ms,carrierQmax9,
send/reorder8/8; queues/resources bounded. Full canonical516 exact, live/native
auth/lifecycle/fault regression PASS; Go race×3/vet/modules/fuzz,Python982+1optional
skip,Android build/6JVM/lint PASS. Observer failures/post-exit teardown preserved.
APK/private artifacts removed;20 Android/25 Amsterdam known IDs checked, owned
processes0 (one Android ID reused by unrelated thread); radios1/1 restored.
Sanitized metrics/timing audit PASS. No unfinished PERF-2 checks; concurrent
foreign VPN edits preserved, not included. Public versions/production unchanged;
no push. [Report/evidence/limits](releases/2026-09-27-webrtc-5n-perf2-reliable-envelope.ru.md).
**STOP**: planning region1.4–1.5 useful Mbit/s, no automatic default or5N.4.

## 27.09.2026 — 5N-REL-1 = PASS: reliable bytes before TLS

Architecture: Family TLS1.3 → bounded ReliableStream → unchanged Telemost VP8/RTP.
Core `ecc884c`, actual clean CLI/APK build `d14a92f`; test/observer `bbcea5e`.
Selective repeat: cumulative ACK +32-bit SACK, sender8/receiver16, DATA16KiB,
RTO1s/retries8/MaxAge20s, bounded memory and producer backpressure.
Deterministic faults, TLS recovery/exhaustion, Go race×3/vet/modules/fuzz PASS.
Physical Redmi→real SFU→Amsterdam300s PASS: offered cap2Mbit/s, delivered1.883505,
4315/4315 exact echoes, bad-MAC/corruption/duplicate/reorder/unexpected close0.
Accepted60s runs recovered29/29 natural block gaps (25 RTP gap events), max1578.496ms;
controlled seq2 also recovered874.979ms with surviving TLS. No TUN/DC substitution.
Final canonical500 exact echoes/300.439s sustained PASS. Native auth/WS/PC/replay,
live admission negatives, cancel/activity/force-stop/remote-exit/network-loss and
explicit fresh recovery PASS. Go race×3/vet/modules/fuzz,153 Python, Android build/
6 JVM/lint and ARM11 reliability/7 carrier/9 CLI/7 Family groups PASS.
Three incomplete/failed harness/observer attempts retained separately, no core
tuning/retries-to-green. APK uninstalled;15 Android/22 Amsterdam known PIDs gone,
temporary remote/native dirs0; local private fixtures/builds/logs/helpers removed.
Radios1/1 restored; sanitized20-run evidence verified. No unfinished REL-1 checks.
No public versions/catalogs/production/push. [Report/protocol/limits](releases/2026-09-27-webrtc-5n-rel1-reliable-stream.ru.md).
**STOP**; no automatic5N-PERF-2/5N.4. Capacity ceiling/production readiness not claimed.

## 27.09.2026 — 5N-PERF-1 = FAIL: sustainable ceiling NOT ACCEPTED

Baseline воспроизведён на неизменном runtime:301.991478843s,151×16KiB,
one-way0.065537849Mbit/s, avgRTT1999.843ms. Все окна1/2/4/8/16/32/64,
offered0.1/0.25/0.5/1/2/4Mbit/s и payload1/4/16/32/64KiB проверены;
failed/warm-up точки не считаются успешными60s measurements.
Highest error-free60s: paced2Mbit/s →1.992294Mbit/s delivered, avgRTT317.584ms.
Highest completed300s:16KiB/window2 →0.130635Mbit/s, avg/p95/p99
1999.765/2046.538/2128.154ms. Long window8, paced2 и64KiB/window2 FAIL;
TLS bad-record-MAC после return RTP gap. Всего5 failed performance points,
35 sent-but-unconfirmed echoes,4 classified TLS rejects; no accepted unequal bytes.
Старые0.131Mbit/s aggregate подтверждены как stop-and-wait limitation, не ceiling;
2s RTT не константа carrier. Window-sweep latency/queue growth не равны универсальной
capacity: paced2Mbit/s быстрее closed-loop plateau. Sustainable ceiling неизвестен.
Core/auth/wire/pacing/production не менялись; final test binary/harness `f1a211a`.
Go race×3/vet/modules/fuzz,95 Python, Android build/6 JVM/lint PASS;
physical native tests PASS. Final canonical/lifecycle regression PASS:370 exact
checks,300.000378s,0.064662Mbit/s one-way, avgRTT2026.944ms; running hashes matched.
Diagnostic APK удалён;28 Android/29 Amsterdam known native PIDs gone, remote dirs0,
radios1/1 unchanged. Own local APK/native/private fixtures/DBs/logs/helpers удалены;
sanitized29-run evidence сохранён и проверен. Production/каталоги/push не менялись.
Remaining: причинная диагностика RTP gaps/TLS rejection и устойчивый ceiling,
не автоматическое продолжение разработки.
[Отчёт / точные results / limitations / rollback](releases/2026-09-27-webrtc-5n-perf1-carrier-capacity.ru.md).
**5N.4 не начинать; после отчёта остановиться.**

## 27.09.2026 — Family E2E gate PASS

Scope5N.3 сохранён: existing Device Identity/FAMILY admission, не повтор plaintext
echo. Clean runtime `5dd8b49`: isolated TLS1.3/mutual identity certificates поверх
неизменного VP8, disposable authority на existing ProductStore, без production DB/
provisioning изменений. Diagnostic APK `5N.3-test-only`/code2 собран, временно
установлен на Redmi, затем удалён; не опубликован. Sustained151×16KiB/302.000773s:
avg1999.913819ms, p50/p95/p99=2000.067656/2013.326301/2044.018489ms;
useful aggregate(TX+RX)0.131071665Mbit/s, one-way0.065535832. Ceiling не установлен.
Accepted full run374 exact echoes/TX=RX4,564,257B, corruption/timeout/disconnect0.
Unknown/wrong/revoked и old TLS handshake rejected на real carrier; native replay,
ctx/SIGTERM/activity/force-stop/remote-exit/WS-close/PC-close/network-loss/explicit
fresh recovery PASS. Wi-Fi handoff NOT TESTED: сеть не connected.
Два предыдущих full runs FAIL после150/153 checks: старые SSH parent sessions
закрылись на320s до echo timeout. Test-only independent observer устранил lifetime
dependency, **без изменения runtime/retries/deadlines**; точный OS signal неизвестен.
Оба FAIL сохранены, не включены в zero-error accepted window. Harness `e4b67f8`.
Race×3/vet/modules/fuzz PASS;91 Python tests,6 JVM tests/build/lint PASS.
Own test PIDs/remote dirs0; APK/private inputs и local disposable artifacts удалены.
No production rollout/push. [Отчёт/evidence/rollback](releases/2026-09-27-webrtc-eu3-family-session.ru.md).
**Следующий выполненный запрос —5N-PERF-1 выше;5N.4 не начат.** TUN/full VPN/Device Core,
protected sockets, performance ceiling и production readiness не доказаны.

## 27.09.2026 — physical Android binary gate PASS (checkpoint до5N.3)

Отдельный `com.familyconnect.telemosttest`, debug version1/5N.2-test-only,
переиспользует тот же `carrier/cmd/telemost-binary` как Android PIE child process.
Не копирует Go core, не использует JNI/Chaquopy/production AWG runtime и не
меняет beta51/Transport selection. No TUN/FAMILY auth, sockets НЕ protected.
Clean runtime `3f65346a02d621c0843975cbe84173d23ebba91f`, physical Redmi Note9 Pro,
Android12/API31/arm64, ordinary cellular. A/B каждый TX=RX4,531,489B,372 exact echoes;
5min150 echoes/300.006638s, mean RTT1999.844ms, useful aggregate0.131069Mbit/s.
Corruption/timeout/unexpected disconnect/reconnect0. Первый full run c3a874d тоже PASS
(290 checks,RTT≈4s/0.065536Mbit/s); не приписываем вариативность shutdown fix.
Waiting room не нужен; оба selected PC pair host/host UDP, TURN не выбран по Pion.
Foreground/background/recreation/screen, disconnect/finish/force-stop, network-loss
и explicit recovery, remote exit, physical native WS-close16ms проверены.
Android Process.destroy pipe race устранён bounded wait + owned-PID SIGTERM;
final summary сохраняется. Native RSS samples12.582MiB, heap3.19–9.69MiB;
Java heap2.46–5.05MiB, app PSS≤138.34MiB; no unbounded growth observed in window.
Linux race/local207-check/vet/fuzz/modules PASS; Android build/6 JVM tests/lint PASS,
physical native7 framing/bounds tests + live signaling-close PASS.
[Отчёт/точные hashes/evidence](releases/2026-09-27-webrtc-eu2-android-binary.ru.md)
· [Build/operator runbook](../clients/android/telemost-runtime/README.md).
Test APK установлен, stopped, не опубликован; production rollout/push отсутствуют.
Amsterdam temporary processes/directories0, Android native PID/room.input0.
Wi-Fi не был connected: handoff не проверен; no deep Doze/restricted-mobile/protection
claim. Fine-grained queue/allocation gauges не снимались; bounds проверены тестами.
Rollback: удалить только diagnostic APK; B temporary artifacts уже удалены.
Остановились после5N.2; FAMILY auth/TUN/5N.3 не начаты.

## 27.09.2026 — real Telemost VP8 acceptance PASS

Clean runtime `a13068e74f8a1ceef4e5d9d659622eb70710aac0`, Go1.27.1/Pion4.2.15,
одинаковый binary на A(dev Ubuntu26.04) и B(Amsterdam186.246.45.246, nobody).
Все7 размеров1B–64KiB,100×1KiB,100×16KiB,30s(actual32.010s) и5min(actual303.990s)
прошли: **291 byte-for-byte echo**, A TX=RX3,204,385B. Main window
09:56:49–10:16:18 UTC; disconnect/reconnect/corruption/timeout0.
5min useful roundtrip0.065538Mbit/s (≈0.032769 в одну сторону), mean RTT3999.807ms;
скорость низкая, это transport PoC, не production/VPN performance acceptance.

Room использована только из `FC_TELEMOST_ROOM`, URL/секреты не документируются.
`waiting_room_required=no`; poll не добавлялся. HTTP/WS/serverHello/ICE/pub/sub/VP8
активны. Pion selected pairs обоих PC на обоих endpoint: host/host UDP,
TURN не выбран; конкретные промежуточные network hops не утверждаются.
Наблюдавшийся WS close4008 устранён добавлением application heartbeat (`55f2561`);
keyframe-prefix experiment не помог и отменён, исходный VP8 envelope сохранён.

Race suite×3/local207 checks×3, vet, module verification, build/fuzz PASS.
Live WS-close после echo, active SIGTERM и remote exit PASS (terminal timeout≤10s).
Temporary processes/artifacts на Amsterdam удалены, проверено0/0; production
services/routing, installed/public/invitation versions и каталоги не менялись.
PoC не опубликован/не подписан; push отсутствует. Rollback — temporary cleanup,
уже выполнен; production откатывать нечего.

Остаются: waiting-room на других rooms, высокий RTT/throughput, auto-reconnect и
mobile validation. **Не начинались Android/TUN/Family auth/TCP/WB**; следующий
gate5N.2 только записан. [Полный отчёт](releases/2026-09-27-webrtc-eu1-telemost-binary.ru.md)
· [sanitized evidence](releases/2026-09-27-webrtc-eu1-live.sanitized.json).

## 27.09.2026 — recovery checkpoint до live acceptance (superseded)

Сохранён оригинальный DeepSeek checkpoint `ee3a830` поверх `8e36858`, без reset,
stash или удаления незакоммиченной работы. Найдены 10 untracked файлов `carrier/`;
`go.mod` содержал 985 NUL-байтов, `go.sum` был пуст. Восстановлены module pins,
bounded framing/reassembly, Telemost session/signaling, VP8 lifecycle и synthetic
harness. Source checkpoint `7aed1a8df9aa7af49e7e82d78fd07fa83367fd7e`.
Go1.27.1 / Pion4.2.15; build, race suite ×3, vet, module verification и fuzz PASS.
Два локальных Pion процесса: 7 размеров до64KiB +100×1KiB +100×16KiB,
207 byte-for-byte checks; **это не Telemost acceptance**. VP8 mode отвергает DC.
Настоящий negative HTTP join вернул404; валидная room/session/ICE/SFU не проверены.

**WEBRTC-EU-1 = BLOCKED**: disposable room URL не предоставлен и
`FC_TELEMOST_ROOM` не задан. Amsterdam `186.246.45.246` read-only SSH доступен,
но carrier туда не установлен. Следующий шаг: ручная ephemeral room → A(dev)
↔ Telemost ↔ B(EU), все размеры/30s/5min и live failure checks. Waiting-room poll
пока не реализован; текущая схема admission/signaling требует live-проверки.
Android/5N.2 не начинать до настоящего VP8 PASS. Production, routing и версии
Android beta51/code51, Linux0.2.11, Windows0.2.15 не менялись; PoC только локально,
не опубликован/не подписан. Rollback — остановить временный процесс; production
откатывать нечего. [Отчёт](releases/2026-09-27-webrtc-eu1-telemost-binary.ru.md),
[build/live runbook](../carrier/README.md), [dependency inventory](../carrier/DEPENDENCIES.md).

## Предыдущие checkpoints

26.09 активация (WIP): начато упрощение invitation/activation. Сервер Friends:
read-only authenticated recovery `POST /friends/device/status` и purpose `status`
(не расходует приглашение), canonical URL `/i/` (redirect совместимость с
`/invite/`), smart landing page с одним primary CTA и без checkbox/инструкций,
QR = canonical URL; клиенты: `FriendsAccessAndroid.deviceStatus()` + recovery при
старте, Python `FriendsClient.device_status()`; тесты server/client (65+5 passed).
Fresh-install sideload активация **не** заявляется fully automatic: Flow A
(приложение установлено, 1 действие) и Flow B (sideload: возврат на landing +
«Открыть», 3–4 действия). Real-device Android E2E acceptance ещё НЕ пройден;
версии/production/WEBRTC gates не менялись.
UI-текст «Приглашение предназначено для одного устройства» заменён на нейтральный
«Отправьте эту ссылку человеку, которого хотите подключить» (referral link —
bounded capability, не строго одноразовая ссылка). Future product split
Personal Invitation vs Referral Link зафиксирован в design/PLAN как backlog;
backend semantics и версии не менялись.
[design](design/activation-simplification-design.ru.md),
[android note](design/android-sideload-deferred-bootstrap.ru.md).

26.09 Linux packaging (опубликовано): operator preview tar.gz заменён на
пользовательские артефакты `FamilyConnect-0.2.11-x86_64.AppImage` и
`FamilyConnect_0.2.11_amd64.deb` (legacy preview tar.gz сохранён как advanced/manual
и для подписанного updater). Реализованы `scripts/package_linux.py`,
`packaging/linux/*` (launcher, desktop entry, icon, postinst/prerm, AppRun +
`--integrate`), CI linux/release jobs и package-content audit (нет
identity/token/WG private/.env/DB). CI green (`36261639780`), чистая Ubuntu 24.04
acceptance пройдена (AppImage smoke/restart/`--integrate`/URI; DEB install/smoke/URI/
upgrade/reinstall/remove), артефакты опубликованы на HTTPS, invitation landing
переключена на AppImage (`.deb`/`.tar.gz` secondary). AppImage не self-contained по
GTK-стеку — host prerequisites задокументированы. Friends/VPN/версии не менялись.
[report](linux-appimage-deb.ru.md).

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
26.09 Linux: подписанный updater-канал поднят до 0.2.11 (`updates/pilot.json`
sequence9, release `v0.2.11`); ранее клиент показывал «последняя версия», потому
что каталог указывал на 0.2.9. Сборка Linux-архива сделана воспроизводимой.
26.09 Linux UI: в исходниках вкладка «Маршрут» заменена на «Статистика»
(трафик сессии, суммарные байты/длительность, нагрузка NL/RU), профиль и
«Проверить IP» перенесены на «Статус»; версия0.2.11 и каталоги не менялись —
см. [отчёт](releases/2026-09-26-linux-stats-tab.ru.md).

25.09: лицензирование опубликовано в GitHub main, commit
`aa3ed9f801a83a4808df3352abc300d235a7c42c`: LICENSE, notices, audit и README RU/EN.
Публичный LICENSE скачан по immutable commit и побайтно совпал с проверенным
локальным текстом. Push выполнен из отдельного checkout поверх139f7da; текущая
локальная ветка разработки не перебазирована, незавершённые изменения сохранены.
[Отчёт](releases/2026-09-25-license-publication.ru.md). Версии/production не менялись.

## 25.09.2026 — критический путь теперь Android → Telemost → Linux EU

Пользователь изменил приоритет на прямой restricted transport в EU Gateway без
Windows Home PC и без обязательного IP-over-Reticulum. Основание — успешный
штатный Telemost видеозвонок Краснодар→Бельгия при недоступном прямом Family VPN;
headless Family carrier этим не проверен. **Этап5, подготовка нового track5N.**
[План и WEBRTC-EU-1–6](PLAN.md) · [Архитектурное решение](reticulum/HOME_GATEWAY_DESIGN.md)
· [Отчёт](releases/2026-09-25-webrtc-eu-priority.ru.md).

Reticulum control/recovery/identity/provisioning/messaging сохранён. Home Gateway
остаётся вторичной функцией для LAN/NAS/RDP/residential exit. Нумерация5A–5M и
старые gates сохранены; новые5N.1–6 пока NOT RUN. Приоритет Telemost/VP8 → EU
Family auth → single TCP → mux → Android TCP+DNS; UDP позже, без direct leaks.
Все existing transports остаются, код и dependencies не менялись. Текущий scope
по прежнему уточнению — документация/preparation. APK/builds/production/версии
прежние по release checkpoint (Android beta50/code50, Linux0.2.10, Windows0.2.14),
нового rollout/rollback нет. Предыдущие записи ниже описывают историю приоритетов.

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

## 25.09.2026 — Whitelisted WebRTC Carrier: подготовка

**Глобально этап5; сейчас подготовка5A/5H, реализации Home Gateway/carrier ещё нет.**
По уточнению пользователя эта итерация ограничена документацией и подготовкой.
ReticulumOverlay → UnderlayPathManager → direct IPv6/IPv4 либо WebRTC underlay;
Reticulum отвечает за identity/Link encryption, провайдер переносит opaque frames.
[План](PLAN.md) · [Delta/design](reticulum/HOME_GATEWAY_DESIGN.md)
· [Отчёт](releases/2026-09-25-webrtc-carrier-preparation.ru.md).

Исследованы pinned whitelist-bypass (MIT) и olcrtc (WTFPL v2), без копирования кода.
Первый кандидат — WB/VP8; guest joining найден, создание room без login и реальные
media capabilities не проверены. Подготовлены contracts IPC/path/provider/rendezvous,
тестовые gates WEBRTC-1–5 и стадии5H–5M без перенумерации5A–5G.
Все WEBRTC gates открыты; ни desktop service round trip, ни Android↔Windows/RNS,
ни Краснодар не проверялись. Code/dependencies/runtime/production не менялись;
Android beta50/code50, Linux0.2.10, Windows0.2.14 по предыдущему checkpoint прежние.
Новых artifacts/rollout нет. Предыдущие решения ниже сохраняют историю уточнений.

## 25.09.2026 — стратегия Home Gateway уточнена

**Мы на глобальном этапе5, в начале5A Home Gateway: дизайн и проверка достижимости.**
Цель — соединить телефон с домашним Windows при активных белых списках мобильной
сети. Reticulum — control/discovery/auth/negotiation/recovery; IP-трафик — через
выбранный защищённый data transport, напрямую либо через достижимый relay.
Обязательный IP-over-Reticulum отменён пользователем. Relay не подменяет домашний exit.

[Текущий план5A–5G](PLAN.md) · [Обновлённый дизайн](reticulum/HOME_GATEWAY_DESIGN.md)
· [Отчёт](releases/2026-09-25-home-gateway-strategy.ru.md).
Home Gateway ещё не реализован; RNS-1–RNS-5 не пройдены. Сначала подтвердить
доступность control/bootstrap **и** data ingress на целевой SIM при ограничениях;
наличие RNS identity/сессии само по себе не доказывает обход белых списков.
Имеющийся XHTTP/TLS проверялся локально, не на таком мобильном пути.
Документация/лицензирование есть, transport/runtime код и production не менялись.
Android beta50/code50, Linux0.2.10, Windows0.2.14 остаются прежними по предыдущему
release checkpoint; новых сборок/публикаций и rollout/rollback нет.
Прежние5.2/5.3а и независимые test/migration задачи остаются открытыми.

Предыдущий checkpoint25.09: добавлены LICENSE, third-party inventory и
[аудит](legal/DEPENDENCY_LICENSE_AUDIT.md). Его первоначальное требование вести
все пакеты через RNS заменено текущей стратегией; legal-решения сохранены.

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

Обновлено 24.09.2026. Это актуальный статус; датированные отчёты сохраняют историю.

24.09: [сравнение восстановления у Proton, Mullvad, Amnezia, Psiphon и Tor](releases/2026-09-24-competitor-recovery.ru.md).
Анализ публичных источников, не проверка доступности в России. Код/production не
менялись; следующий шаг5.3а и открытые критерии5.2/6 сохраняются.

## Положение в общем плане

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


Текущий checkpoint5.3а: [проверки на Redmi Note 9 Pro](releases/2026-09-24-android-selection-device.ru.md).
В отдельном debug pilot прошли4 instrumented tests: protocol/JSON, selection с настоящим
Keystore/journal и запуск Python/RNS. Friends beta50 сохранён. VPN Host в selection
имитируется: service/UI/handshake, process restart и Friends integration ещё открыты.
Документация локальная, APK не опубликованы.

Предыдущий checkpoint5.3а: [подготовка instrumented selection](releases/2026-09-24-android-selection-runtime-preparation.ru.md).
Собраны ARM64 debug pilot APK и test APK с Python3.10; новый тест реального encrypted
journal с имитацией VPN скомпилирован. ADB не видит устройств: исполнение теста,
service/UI/native acceptance ещё не выполнены. APK не установлены/не опубликованы.
Документация и изменения локальные; capability/Friends integration остаются открытыми.

Предыдущий checkpoint5.3а: [Android selection service/UI](releases/2026-09-24-android-selection-service.ru.md).
MainActivity→ConnectionService worker→ControlSelection→journal подключены в исходниках.
124 Java tests и Android debug Java compile passed; APK не устанавливалась/не публиковалась.
Capability AWG3.1/Friends integration и device acceptance ещё открыты. Карта кода обновлена.

24.09: составлена [общая карта кода по модулям](code-map/README.ru.md): серверные
контуры, платформы, messaging, эксплуатация/CI и лаборатория. Это документация,
runtime/версии не менялись. Карта дополняет подробную managed-карту и остаётся локальной.

Последний checkpoint5.3а: [локальная транзакционная смена Android gateway](releases/2026-09-24-android-gateway-transaction.ru.md).
120 Java tests passed. Journal schema2 появляется только при явном selectGateway;
сохранение выбора/rollback/restart проверены с имитацией Host/storage. Service/UI
ещё не подключены, APK/production прежние. Документация пока локальная.

24.09: [исправлен выбор Android gateway при нескольких профилях одного транспорта](releases/2026-09-24-android-gateway-selection.ru.md).
111 Java tests passed; Host имитируется, native rollout отсутствует. Добавлена
[карта managed-кода](managed-control-code-map.ru.md) с границами authority/recovery.
Следом — транзакционная смена gateway/действующая identity и device acceptance.

Последний checkpoint: [Android AWG3.1 identity/journal](releases/2026-09-24-awg31-android-journal.ru.md),
110 Java tests passed; application Host/storage имитируются, production caller выключен.
GitHub main проверен: b5f4864, STATUS23.09. Последние документы24.09 пока локальные,
commit/push не выполнены; не путать их с опубликованной документацией.

Последнее продолжение5.3а: [Java/C#/Python conformance AWG3.1](releases/2026-09-24-managed-awg31-native-verifiers.ru.md).
Java109 tests, Python86 tests и .NET runner прошли локально; общий corpus8×2 и
дополнительные проверки защиты. Рабочие capability callers ещё не включены;
Windows OS/Android device acceptance впереди. Production/версии не менялись.

24.09, последний кодовый checkpoint: [5.3а managed AWG3.1](releases/2026-09-24-managed-awg31.ru.md)
в schema/issuer/Python verifier с явным capability. Добавлен отдельный общий corpus;
360 уникальных локальных сценариев прошли по совокупности запусков (детали в отчёте).
Native managed клиенты/runner ещё не включены,5.3а не закрыт. Production и версии прежние.
Поручение усилить защиту принято в [требованиях устойчивости](blocking-resilience.ru.md).

Этап4 закрыт как выпуск пилотных приложений 23.09.2026. После перечисления критериев
Windows0.2.13 (интерфейс, приглашение, подключение, обновления) и базового сценария Linux
пользователь сообщил: «считай подтвердили». Это основание пользовательской приёмки;
новых инструментальных прогонов и подробных замеров эта запись не добавляет.
Начат этап5: независимый служебный канал и расширяемый парк серверов. Коммерческая готовность,
длительная сетевая устойчивость и новые функции остаются отдельными открытыми задачами.

## Версии и распространение

| Платформа | Собрано | Установлено / опубликовано |
| --- | --- | --- |
| Android ARM64 | 0.1.18-beta51 / code51 | Redmi Note 9 Pro обновлён поверх50; HTTPS APK, updater и страница —51 |
| Linux | 0.2.11 AppImage + .deb (+ preview5b02e8cb9fde119f) | HTTPS AppImage/DEB published; clean Ubuntu 24.04 install/URI/upgrade/reinstall passed; CI GTK/map/link/friends/recovery/install passed |
| Windows x64 | 0.2.15 / source2ffba77 (+ 0.2.14 compatibility fallback) | GitHub/HTTPS installer + catalog sequence11; native/compat CI passed; 0.2.14 kept on landing for old Windows 10; affected Win10 device acceptance pending |

[Интерактивная страница](https://185.251.89.19:8443/invite/) принимает исходную ссылку
приглашения: установка → возврат к ссылке → открытие приложения. Вкладки, выбор платформы
и переключатели работают в браузере; VPN подключается самим приложением. Во всех клиентах
и на странице OFF оранжевый, ON бирюзовый. Старые файлы и автоматические desktop-каталоги
сохранены; Linux0.2.10 остаётся manual preview. Windows0.2.14 опубликован и включён
в отдельный подписанный updates/windows.json (schema2, sequence10). С0.2.12 и старше нужна
одна ручная установка переходной версии; затем работает встроенная проверка Windows.

[Версии и хеши](releases.md) · [Windows: приёмка и откат](releases/2026-09-23-windows0213-updater.ru.md) · [Android/Linux](releases/2026-09-23-switch-colors-beta50.ru.md).

## Подтверждено

Android: VPN пилот, обмен текстом и голосовыми между двумя телефонами, редактирование,
запись удержанием/фиксация вверх, прокрутка к новым сообщениям и уведомление с выключенным
экраном подтверждены ранее. Beta50 сохраняет эти функции и меняет оформление переключателей.
153 unit tests, lint, ARM64 build и проверка payload/подписи. CI и точные проверки текущего
выпуска приведены в отчёте. Публичные загрузки проверены по полному SHA256.
Linux GTK rendering, взаимодействия, запуск распакованного архива и URI checks passed в CI.
Windows native installer/broker/UI/URI, ordinary-user и AWG/TCP проверки passed.

## Следующая приёмка

- Долгий фон, перезапуск/OEM, Android13+ и Doze с точным временем доставки.
- Российская сеть, смена сети и длительная устойчивость (отдельная полевая приёмка).
- Полная недоступность gateway и восстановление через независимый служебный канал.
- Desktop messenger не имеет подтверждённого равенства возможностей с Android.
- Подписки/оплата, publisher signing Windows, лицензия и независимый аудит не завершены.

Доступ только по приглашению; личные ключи и данные при обновлении сохранены. Лимиты
20 referral claims за24ч и500 мест — параметры, а не текущий остаток. Прямые приглашения
имеют отдельный запас. CI использует тестовую подпись, ключ выпуска остаётся offline.
[Рабочий план](PLAN.md) · [Карта документации](README.md).

Windows0.2.11 исправил разметку, логотип и активацию;0.2.12 — причины лишней перерисовки.
В0.2.13 добавлен отдельный Windows updater после обнаружения устаревшего общего каталога0.2.9.
Пользователь выбрал одну ручную установку переходной версии. Native CI пройден;
пилотные проверки приняты пользователем 23.09.2026, см. запись выше. [Артефакт, канал и откат](releases/2026-09-23-windows0213-updater.ru.md).

Этап5 начат24.09: аудит5.1 завершён, подготовлены контракт приёмки и локальная
основа реестра серверов/планировщика5.2. По просьбе пользователя добавлены новые
серверы, распределение новых подключений и управление IP. Production-балансировщик
ещё не включён. Локально добавлены durable leases/IPAM: резервирование, revoke,
expiry и подтверждённое освобождение;112 checks passed. Следом — интеграция доступа
и удалённый reconciler с fencing. [Отчёт хранения](releases/2026-09-24-fleet-leases.ru.md).
[Аудит, тесты и границы готовности](releases/2026-09-24-stage5-audit.ru.md) ·
[Контракт](stage5-fleet-contract.ru.md).

## Снимок нагрузки24.09.2026

Read-only аудит: Friends18 устройств,14 не отозваны;5 устройств передавали
трафик через NL в20-секундном замере. CPU RU≈19%, NL6%; на RU iowait5–10%.
Число людей и суточные пики не установлены; текущий этап и версии не менялись.
[Метрики, границы измерения и оставшиеся проверки](releases/2026-09-24-server-usage.ru.md).

## Продолжение5.2 и согласование7.1

24.09 добавлены локальный шлюзовой журнал fencing и worker:139 tests passed
включая реальное падение процесса с дочерним эффектом. Это предыдущий checkpoint локального прототипа; live rollout не выполнялся.
Последующее добавление WG/AWG и SSH описано ниже.
[Подробный отчёт](releases/2026-09-24-fleet-fencing-admin-plan.ru.md).
Согласован [7.1 — единая Django-админка серверов, доступа и платежей](PLAN.md#django-admin).
UI запланирован после5/6; общие операции5.2 готовятся сейчас. Клиентские версии прежние.

## Текущий шаг5.2: WG/AWG и SSH

24.09 реализованы точечный WG/AWG backend, SSH adapter с закреплённым host key
и агент с фиксированной командой; общий локальный прогон163 passed. Проверены
subprocess fixture и SSH argv/receipt, native VPN/SSH приёмка ещё впереди.
[Отчёт](releases/2026-09-24-fleet-wg-ssh.ru.md) · [Runbook](fleet-wg-ssh.ru.md).
Нет установки на RU/NL и изменений клиентских версий.5.2 остаётся открыт:
native приёмка → общая авторизация/scheduler/signed publish; также нужны
автономный TTL, TCP и миграция существующих IP.7.1 Django остаётся после5/6.

## Последний checkpoint5.2: native-приёмка завершена

24.09,10:39–10:40 UTC:12 сценариев WG/AWG2/AWG3.1 с настоящим SSH и VPN-трафиком
passed; отдельно163 regression tests passed. Проверены crash после peer effect,
повтор SSH, restart/recover, revoke, повторное использование IP и fencing старой команды.
[Отчёт/границы](releases/2026-09-24-fleet-native.ru.md) ·
[Запуск стенда](../pilot/fleet-native/README.ru.md). Тестовые контейнеры/сети удалены.
После server restart клиентский handshake инициировался явно; автоматический
client recovery и межсерверная SSH-сеть здесь не приняты. Production rollout отсутствует.
Следом в5.2 — единая авторизация и bounded scheduler, затем signed publish;
TTL, TCP, миграция действующих IP и установка/recovery services ещё открыты.
Клиентские версии и согласованный пункт7.1 не изменились.

## Последний checkpoint5.2: proof авторизация и scheduler

24.09: FleetAccess проверяет подпись/актуальные права и резервирует одной транзакцией;
FleetScheduler сохраняет claims/backoff, ограничивает проход и приоритетно удаляет
отозванные подключения.201 tests passed. Схема fleet DB2, явный upgrade1→2;
production DB не менялись. [Отчёт](releases/2026-09-24-fleet-services.ru.md) ·
[Контракт/миграция](fleet-access-scheduler.ru.md).
Следом — signed publish после ready. Подключение к действующим Friends правам/API,
TTL/TCP, supervisor и импорт старых выдач ещё открыты. Это локальный service backend,
не опубликованный endpoint. Клиентские версии и пункт7.1 прежние.

## Последний checkpoint5.2: offline signed publication

24.09: локальный issuer подписывает/шифрует существующий control-config/schema2
для ready WG/AWG2 lease; повтор возвращает те же bytes. Отдельный published()
проверяет текущие права и выдаёт ciphertext без signing key.269 tests passed,
fleet schema3, явная миграция1/2→3. [Отчёт](releases/2026-09-24-fleet-publication.ru.md) ·
[Контракт](fleet-publication.ru.md). Offline production key не читался.
Далее verified ACK и безопасный перенос offline→online/relay; действующий Friends
доступ, импорт старых floors/IP, TTL/TCP и production deployment ещё не подключены.
Managed AWG3.1 остаётся5.3. Клиентские версии и план7.1 не менялись.

## Последнее решение: приоритет managed AWG3.1

24.09 пользователь согласовал: ближайшим шагом становится5.3а managed AWG3.1;
5.2 не закрыт, оставшиеся relay/ACK/миграции сохраняются. WG/AWG2 — только
совместимость/регрессия. VLESS/REALITY остаётся альтернативным TCP-путём.
В5.3б записано исследование третьего транспорта: NaïveProxy HTTPS/HTTP2 первым,
Hysteria2 как сравнительный кандидат. Выбор для production ещё не сделан.
[План](PLAN.md) · [Обоснование](releases/2026-09-24-transport-priorities.ru.md).
Код/серверы/клиентские версии не менялись; новых runtime и сетевых тестов нет.

24.09 подготовлен [анализ рынка и устойчивости](releases/2026-09-24-vpn-market-assessment.ru.md).
Автопереключение и несколько протоколов уже есть у конкурентов; преимущество
Family Connect ещё требует российских сравнительных испытаний и платного пилота.
Код/версии/серверы не менялись, порядок работ сохраняется.

24.09 описана [архитектура восстановления Reticulum](reticulum-recovery-design.ru.md).
Криптографический destination сохраняется при переносе службы; независимая связность
входов, discovery и восстановление состояния ещё требуют реализации/приёмки.
Текущий single-bootstrap не заменён; код/версии/серверы прежние.

24.09 дополнена [модель обнаружения Reticulum/endpoints](releases/2026-09-24-reticulum-threat-model.ru.md).
Защита подписью/шифрованием не равна невидимости IP для подписчика или сетевого наблюдателя.
Только документация, поведение сервиса не менялось.
