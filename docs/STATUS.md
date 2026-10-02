# Текущее состояние / Current state

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
