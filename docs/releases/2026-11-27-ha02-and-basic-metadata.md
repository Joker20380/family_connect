# HA-02 continuation and separate basic metadata candidate

Current entry: feature/device-technical-metadata-20261115, local/remote
8fa79a1307c1332d22560cb2145949402fab56a0; no newer change at entry. Earlier
fa27314589a8c1ce611913dedbaa7e4da421aa02 entry remains historical evidence below.
Main remains da94566acb770dc758a1e057f02bfef784585a75. Accepted installed components
and source-only Docker111866ae are not reinstalled. A has production priority;
B changes are separate source/candidate work, never a production binding change during A.

## Current follow-up —28 November (source-only)

Native inventory follow-up adds207 disposable containers,17 running, to the exact-Engine domain
fixture. It exercises the actual API rather than treating a fake207-row list as latency proof.
Normal setup budget becomes120s solely for206 additional container creates; policy2s/4s and fault
phase45s/<6s bounds remain unchanged. Final acquisition measurement/native CI is pending at commit.
This does not improve initial_admission_coverage_proven or authorize shared-runtime maintenance.
The first native207/17 run46088511450 fails with TimeoutExpired and clean own-process cleanup;
artifact15240022429/fbbc60b7ce0d3528a7c7e282ba049c00dcf5b529ed281ad22f6ab837833cfe11 is retained.
It does not produce a HELD/domain result. The vfs fixture copied the whole Python rootfs for all
206 rows, including190 never-started ones. Use a deterministic empty image only for those stopped
synthetic records, retain the real17 running containers, and record immutable setup milestones.
The120s outer bound and policy2s/4s remain unchanged. This fixture correction needs a new native
result; it is not proof that the historical timeout occurred in a particular API call.

### Native B runtime and disclosure correction

The isolated x86_64 API35 emulator uses KVM and actual guest NVIDIA GTX1650Ti GLES, one emulator
under the shared qualification lock. Storage prepare3/verify1 pass in separate instrumentation
processes with an intervening force-stop; all eight before/after-publication fault states stay
closed on reopening. Existing native API4 tests pass. OldOFF/pending revoke, missing installation
binding, positive initialization and rejection of late sample ACK are exercised on real storage.

A synchronized native UI test waits for notice dismissal and the actual launcher before reentry.
The earlier APK then deterministically fails to show notice again; onPostResume instead of
onCreate-only scheduling fixes this. The final UI test passes: sequence1/NOTICE_PENDING before
and after Back; Understood persists the policy before sequence2, then the real consumer returns
local AUTH_OR_CONTRACT_REFUSED for absent test identity. Another callback respects backoff; VPN
status/health do not change. This does not establish authenticated backend upload or VPN traffic.
Earlier unsynchronized Home/reentry attempts failed on both builds and remain as test evidence,
not a claimed application cause. No timeout was increased or assertion dropped to obtain PASS.

Source-only client change; no owner application/data touched. Public BASIC_METADATA_APPROVED stays
false. Matching production application/signing upgrade, authenticated synthetic backend flow,
legal/store basis and a new HA schema contract remain separate release gates. Final-source APK
is rebound after this commit; ba569748/af113b02 APKs cannot prove the changed UI source.

### 28 November follow-up (source-only qualification)

Entry8fa79a1307c1332d22560cb2145949402fab56a0 equals remote feature SHA; no rollback/newer work lost.
Completed215c7fcb phase046080709385 and Linux46080709373 FAIL, including schema incompatibility;
phase0 failover has a separate build failure, not explained by the schema trace.61537b1f phase0
46081203525 also fails. Client46080709374 carrier failure remains an independent mandatory gate.
No original failure/artifact/UNKNOWN removed or classified as resolved by a retry.

Request/read/retention no longer ALTER the installed SQLite schema. Joint HA fixture loads exact
111866ae metadata source (SHA256 aa9ca52f9d4a36bf0c0dc5740f81cc83cb8a6262a5aefbc1a7862b01abe87205),
not the evolving B implementation; importer contracts/pins unchanged. Disposable B fixture makes
the migration explicit (user_version2, policy/mode columns), with negative A capture/import checks.
Its production installation remains closed until a separate versioned HA capture/restore contract
preserves policy/revoke/floors/expiry. Internal replay reports now include schema1, external validator
unchanged. Panel refuses higher-counter legacy samples after basic and keeps basic floor on revoke.
127 focused schema/protocol/capture/restore checks pass;12 PG-dependent checks skipped locally,
not claimed as native acceptance. Follow-up panel/full CI and carrier/transition/Android remain.
Source rollback only; no installed image, data, schema, key or gate was changed.
Native disposable PG17.11 qualification55/55 passes, including installed-v1 import and continued
business/replay operations; panel34/34 passes including both higher-counter downgrade cases.
Initial lab Docker bridge setup failed (docker0 absent); no host network repair was attempted.
Only the disposable test container was recreated on loopback port53487. The first psql setup used
the wrong default port; retained separately, corrected to53487. Neither is a production outage claim.

### Carrier cancellation correction

Original client artifact15236672338/275a2697 remains unchanged. A deterministic test holds the
context's asynchronous Reset callbacks, cancels at the client-commit Write boundary, and demonstrates
that old MuxStream.Write still admits it. This identifies a transport admission defect, not a claim
that the historical CI scheduler followed that exact interleaving. MuxStream now remembers its
OpenTCP request context and checks cancellation synchronously under its queue lock before enqueue.
No timeout increase, retry, removed assertion or change to renewal commit semantics.
Post-transfer cancellation is not retroactive: another deterministic barrier at server-committed
proves the peer generation advanced, client generation did not, and both sessions close. Existing
corrupt/lost-confirmation and partial-commit runtime tests remain. Focused Go race qualification
passes both tcpforward and roombroker. A broader single go test -race ./... retains separate failures
in publisher-recovery's configuration test and Telemost local process/idle fixtures (including an
unsynchronized diagnostic bytes.Buffer read). These are not silently rerun to PASS or attributed to
the repaired metadata/renewal defect. Exact client workflow remains mandatory.
Phase0 failed artifact15237149062 is retained/read (SHA256
6f3d6b8351817a4b9f7dad84f1a0ed750dfc452532836c66223c5524ca3c20a2), Linux15237569058 retained/read
(414eab843a69484386af903f0ce974aa1fa19eddc58ea9c9a578edd600cde446). Source-only; no carrier installed.

### Historical B native-storage source checkpoint (superseded by native results above)

BasicMetadataStorageRuntimeTest compiles against the actual Android SharedPreferences/AtomicFile
consumer, with test-only Context wrappers. Init/notice/reserve/ACK errors are injected both before
publication and after a real successful write with a lost success result. The existing consumer's
durable fault marker must close sampling; prepare/verify are separate instrumentation invocations
with an intervening process stop. OldOFF/pending revoke, absent installation binding and late sample
ACK are covered. Compilation passes; runtime/device/UI/backend/upgrade acceptance is not inferred.
No production code or public flag changed in this checkpoint. A new source-bound APK is still
required because carrier code changed; the earlier ba569748 APK is not evidence for this source.

### Docker inventory and finite retirement investigation

Full inventory covers207 rows, including a protected unenrolled final row; duplicate/over1024/
changed sets refuse terminally under4MiB/2-second work bounds (the failed8s extension is historical).
Exact-Engine46086314293 SUCCESS, independently checked artifact15239555906 SHA256
0f761c3849cb89c96f3957a8707aeee206d7be593e9043fb097f111ce50ca7e7 and five af113b02 source hashes.
Old shim-owned FD/mmap/rename effects continue after both control processes die: retirement
0.005498427s, disposable API recovery10.115281063s. Initial coverage/maintenance remain false.
Local normal-sudo run exits0, but its root-owned receipt was not independently reread; CI artifact
is the accepted negative evidence. No production daemon touched. Lab API recovery is not panel/IPC
or a replacement controller/application transition proof. No recovery kit was verified.
Finite fallback is cold kernel-generation retirement plus a boot interlock, not an invented narrow
online proof. It needs isolated VM/new-controller/application recovery qualification and explicit
broader scope review before installation. No measured production outage budget is claimed.

### Exact follow-up refusals and corrections

0dc11ad9 broad CI46084776329/46084776392 fails because recovery/native capsules intentionally carry
Python sources, not tests/*.txt: the new frozen fixture was absent after source removal. Artifact
15239067681/adace812745433b59468a7fdef702e849179fde340603005338d0fba16b64ca1 preserves the exact
FileNotFoundError. f3777381 moves the identical aa9ca52f bytes into control/friends/technical_metadata_installed_v1.py,
an existing supported source-root/type; no source/import allowlist is widened. The fixture remains
explicitly loaded under its pinned legacy identity, never the production endpoint.

Native Docker46086314275 fails after the changed12s control timeout violates the existing <6s
enforcer-hang gate. Artifact15239236864/ede5565e9bffbd64319e0c3fbb3d4795bf6e8132a83c26c6e382a86a1b1ef03d
retains the failure and successful normal-domain phase/cleanup. Restore original2s work/4s control
deadlines and retain complete207-row traversal; new real hung-socket regression enforces the bound.
No test deadline is increased or assertion dropped. Follow-up native46087459683 SUCCESS;
independent artifact15240255408 SHA2567580178d660f55469dadfe1a0164f90a20086be3387ba6288e060fe1c22d6235
matches all eight source files atf3777381, domain loss/cleanup receipts and unchanged coverage=false.
56 local closure/domain checks pass. This is CI artifact verification, not recovery-kit verification.
The0dc11ad9 failover build artifact15239267123 SHA256
9e739591141364f6381f9b3a675ff859ba8a286baa587e3fd77604251bc57e7d independently shows the same
missing frozen fixture in its root-owned source capsule. It is not guessed from the ordinary job.

A is **not complete**: no installed OWNER executor adapter, common held interval, new stopped-support
snapshot, encrypted fleet kit, independent kit verification or linked normal resume. The concrete
unclosed channel is create/start already accepted before first AuthZ attachment, with downstream
containerd/shim work outside the mandatory parent. Online reload is disproved by the native test;
finite old-generation retirement/recovery is not qualified. A shared-window proposal affects14
excluded neighboring containers and cannot be executed under project-only authorization. Next step
is that isolated generation-retirement/recovery qualification, not another census or production stop.
Existing HA AES key native read/preservation/real consumer now pass; it is not the current blocker.
Production is untouched in this iteration; no new live-baseline PASS is claimed. The27 November
NL1/NL2/panel/collector observations below are historical, not a fresh maintenance preflight.
No own production restrictions were acquired. Own synthetic PG container/volume and NVIDIA emulator
are stopped/removed (AVD/evidence retained); shared emulator lock is released. No reboot-startup claim.

Current private B candidate: sourceba25c0543afeca81c2a004bc0f1ca54a62443873,
com.familyconnect.app.metadata,126,0.1.18-beta126-basic-candidate,x86_64/debug.
APK SHA2566d99e0d7aea7dcf0a88508c56c3afd6e039c36b8546a2d9ccac541879db81d50;
instrumentation SHA256db872022dd0637f83c30e153ed457f7e297484d64cbbf7c3c882eeee74cb7860.
Independent ZIP/native-library and apksigner readback confirms source closure and debug signer
a159f53e421755eea528fa0af5d5cd34ef39892bf514b237aa65871cf6fffe64. Native restricted/awg closure
at af194acb is unchanged through this UI source. Initial apksigner invocation lacked java in PATH;
correct JDK-path verification is recorded separately, not hidden. Generated friends/release
BuildConfig both retain BASIC_METADATA_APPROVED=false even with the debug-candidate property true.
No public artifact, version catalog, installed client, server schema or binding changed.

## Historical27 November23:20UTC checkpoint

B has actual implementation and a privately retained arm64 debug candidate, **not public rollout
acceptance**. Sourceba56974853b69e37330dc210edb678cd79cd6cb9, candidate SHA256
33e29f759a5740af98d028d15795d3483713931726f7ce11740059e9c1e8730e (52692778 bytes);
a separate reader checks exact bytes, ZIP integrity, package/version and arm64 candidate build.
215c7fcb9174588c4cfa43e9545cd83e9cbf0d97 changes fixtures/docs only;61537b1f5b7df2ecf0faf221a6d2bfedf8521923
adds CI path coverage, not runtime code. Both pushes and remote feature SHA are verified; main remains
da94566acb770dc758a1e057f02bfef784585a75. All actual installed A images/bindings remain unchanged.

| Exact source | Gate | Observed result |
| --- | --- | --- |
| 894ffed3 | native-support46075423497 | SUCCESS; independent362-case artifact, zero skips |
| da551d55 | native pre-hook46076761745 | SUCCESS as counterexample only; five source hashes/cleanup independently checked |
| 274499b7 | Docker46079367737 / phase046079367830 / readiness46079367713 | SUCCESS |
| 274499b7 | Linux46079367749 | FAILURE in root-owned Python3.14 launcher setup; not explained away |
| ba569748 | readiness46079823247 | SUCCESS |
| ba569748 | panel46079823152 / client46079823170 | FAILURE; old installed-fixture/source-guard assumptions corrected separately |
| 215c7fcb | readiness46080709370 | SUCCESS |
| 215c7fcb | client46080709374 | FAILURE: carrier/roombroker TestCredentialExchangeCancelBeforeCommit, cancellation extended the generation |
| 61537b1f | panel46081203523 | SUCCESS, including full corrected installed-custody qualification |
| 215c7fcb / 61537b1f | phase046080709385, Linux46080709373 / phase046081203525 | IN_PROGRESS at23:17 readback, not PASS |

Failed Android artifact15236672338 is downloaded and independently SHA-checked:
275a2697374550995587f0ac9f66c06bd541fb028027407ead55c0d5bd032164. Its actual log reports
TestCredentialExchangeCancelBeforeCommit at credential_exchange_test.go:364, not a guessed cause.
The carrier source is unchanged in B; no retry, skip, timeout increase or unrelated repair is made.
Local candidate compilation/18 JVM checks and96 protocol/collector,32 disposable-panel checks do not
override that full-client gate. Native UI/restore/storage-fault acceptance, per-field processing
basis and store declaration remain open; public BASIC_METADATA_APPROVED stays false. No public
version/catalog/signature changes. External custody, source-host-free restore, reboot-startup and
FLEET-PRODUCTION-ONBOARDING-1 remain separate open criteria.

## A: atomic native fixture receipt

Native-support46072376405 at111866ae failed359/360 in
test_all_staged_sources_and_requests_are_pinned[exit.py], JSONDecodeError char0 in
check_hooks before threads==6. Artifact15234561169 is retained privately; ZIP SHA256
4e8fe8251831cc182017475abbe57037c10be93aa89a66e2c9b5f0d7c3d52c30 matches GitHub.
The preserved artifact proves that failure, not the exact historical scheduler interleaving.
A controlled writer paused after opening/truncating its target reproduces the visibility
window; the same pause while writing a temporary file leaves the receipt absent. Atomic
same-directory replace publishes only the flushed complete JSON. No JSON retry/timeout
increase/skip; the original runtime-hook checks, source/request pins and threads==6 remain.
47 focused CPython3.14 native quiesce/exit checks pass without skips. Exact-source CI follows push.
Only tests/docs changed; rollback is source-only. Production support and all installed images
remain unchanged; no capture or holds were initiated.

At entry,111866ae Docker46072376420 and Android46072376388 succeeded;
native-support46072376405, phase046072376425 and Linux46072376409 failed.
The latter two failures are not explained by the native fixture trace without their evidence.

## A: prestate reconciliation and pre-hook counterexample

Prestate identity is retained privately (306750 bytes, KDBX signature, inode/mode/SHA256).
Original activation records contain no independent prestate digest; this new identity receipt is
not a historical integrity anchor. One fresh local unlock gives PRESTATE_FD_NATIVE_READ exit0;
the existing full staged reconciliation then passes both exports, both real consumers and preservation
comparison. Prestate and working encrypted bytes remain unchanged. The existing journal now contains
reconciled.json, alongside all original failed records. No XML, stderr, record contents or keys are
reported; no new key, activation/import or whole-vault replacement. External custody is not proved.

Isolated stock Engine29.1.3 q4 delays actual pre-hook Create/Mount handlers inside a disposable volume
driver, not an AuthZ proxy. Original containers use empty parent/unless-stopped. After hook/CLOSE,
new protected create gets403, while the two released old handlers complete201/204 with an actual
protected write. Own containers/processes are cleaned up. q1 driver-method parsing failure, q2 probe
timeout against the in-flight container and q3 incorrect reload-log expectation remain preserved.
New native CI records exact source closure; this is a counterexample, not a shared-window PASS.

Read-only daemon prestate shows17 running containers:3 FC plus14 MicroTrader; live-restore=false.
The [concrete proposed transition](../operators/docker-initial-transition.md) needs expanded scope
approval and isolated old runtime-generation/recovery qualification. No shared stop/reload, product
hold or application recreation occurred. Native-support fix894ffed3 is pushed/remote-matched;
run46075423497 is in progress, Android46075423494 SUCCESS, other applicable runs pending.

## B: separate implemented candidate, not public enablement

The prior B prompt was not implemented at entry. This change adds automatic_basic/schema2,
basic-2026-11-v1 across Android, authenticated endpoint, receipt, SQLite store, RU/NL collectors
and console model/projection/template. Console migration0016 is source-only. No working database,
writer closure, image or collector is updated. HA03 canonical PG intentionally refuses schema2;
the actual SQLite endpoint remains the candidate's supported server path.

Ordinary foreground setup presents notice before any sample, without the old support enable Switch.
Acknowledgment records notice, not consent. Privacy objection/offline revoke does not gate VPN,
payment, updates or support. Positive epoch/sequence and installation binding commit before collection;
legacy enabled becomes basic NOTICE_PENDING, absence is explicitly LEGACY_UNDECIDED, prior refusal/
pending revoke survives, failed commits fail closed, restored installation is blocked. A late ACK
cannot clear revoke; no epoch advance bypasses pending revocation. Late/restored v1 samples cannot
downgrade an identity already accepted as basic, including after a payload-free v1 revoke.

Basic fields are OS/version/app, connection type, separate public SIM/registered-network sources,
actual transport/gateway/state and bounded error/time; local ASN/organization only from qualified
ephemeral direct AWG peer observation on RU/NL1/NL2. TCP/MESH intermediary IP is not substituted.
Model/manufacturer/radio/readiness/geography are excluded from automatic payload/enrichment;
ASN-only lookup never queries city records. Latest-only observations expire within7 days, old/future
samples cannot refresh their age; replay floors are payload-free. Panel preserves UNKNOWN/reason,
source and age, policy identity and not_requested instead of consent=enabled.

Local checks:96 Python protocol/collector tests;32 panel tests against disposable PostgreSQL17.11;
18 Android JVM tests (7 policy,11 existing wire/schedule); arm64 debug and instrumentation APK builds
PASS. Real device instrumentation/UI/storage fault/restore acceptance is NOT_RUN. The legacy validator
fixture is the validation prefix of111866ae technical_metadata.py (trailing blank lines removed), SHA256
c0adf82aee5afd4fb71a51ba7b13ebe25f4ccab62eb4ffbde1ae72e59c49734a;
compatibility runs without relying on CI fetching old Git history. Candidate package
com.familyconnect.app.metadata, version0.1.18-beta126-basic-candidate, debug signing only;
APK SHA25633e29f759a5740af98d028d15795d3483713931726f7ce11740059e9c1e8730e.
Native library rebuild was needed because the historical generated GoBackend lacked ownedHandle;
fresh builder closure atda551d55 retains engineb5928efb/Android54200111 pins. Initial stale-library,
offline dependency, Python environment and disposable Docker network failures are retained privately;
successful corrected builds do not erase them. No emulator, phone install or transport release claim.

Public release/friends builds keep BASIC_METADATA_APPROVED=false. Only explicit separate debug
qualification enables it; no new public version/catalog or signing. Per-field necessity/legal basis,
native acceptance and store declaration remain mandatory before public enablement. Rollout/rollback
requires A completion and renewed exact source/image closures, API/collectors/console first; no database
rollback from old bytes or automatic interpretation of basic rows as old consent. See the
[field purposes/sources/retention/basis and migration contract](../operators/basic-metadata-v2.md).

## Outstanding acceptance

### Follow-up: immutable A and accepted Android source fixtures

B ba56974853b69e37330dc210edb678cd79cd6cb9 is pushed/remote-matched; readiness46079823247
SUCCESS. Control panel46079823152 fails specifically in installed-custody fixture setup: it reads
the new B inventory collector (cecc0f9e) against the unchanged installed pin0f0c07e9. Failed artifact
15236991068 is retained and independently read, SHA256
8c728a058a788ff58dc873b6de0a395f7a940aa98675693f079258eccde1123f.
The installed manifest/validator is NOT relaxed. A new fixture retains the exact old collector bytes
from274499b7; substituting real B bytes explicitly raises HOST_SOURCE_CHANGED. Separately, the
Android accepted-source guard failed on the intentional v2 receipt parser delta. It now reverses
only a separately SHA-pinned basic-candidate.patch, then verifies the original unchanged126/125
pins and original reverse patch. Neither fixture adjustment is an installation/public acceptance.
127 relevant custody/source-closure checks PASS, zero skips. The first added negative test's wrong
legacy unpacker (DOCUMENT_SCOPE) is preserved; it now uses the existing current unpacker.

274499b735ef686ba3b8a688f31b98cb0ef755be exact Docker46079367737 and readiness46079367713
SUCCESS. Linux46079367749 failed earlier in isolated root-owned Python3.14 launcher setup;
artifact15236955292 remains separate, not explained by the Docker fixture correction. Its download
attempt failed in connector transport; no local readback of that artifact is claimed. Do not claim
full broad CI success from component passes. Follow-up source215c7fcb preserves all installed pins.
Readiness46080709370 SUCCESS on215c7fcb; the panel workflow previously did not trigger on its own
custody fixtures, so no panel PASS is inferred. Its path coverage now explicitly includes those
fixtures and metadata/GeoIP contracts; the same full panel gate runs on this exact follow-up source.

Independent local reader also checks pre-hook artifact15235576433 SHA256
cbe34fa3c59ece596b24c86b47f422f35f9d801db9c3604ecbf05284b90cd84e,
all five source hashes atda551d55, real pre-hook create201/start204 effects after CLOSE, new create
refusal and own-process cleanup. Both initial_admission_coverage_proven and maintenance_window_qualified
remain false. The shared-generation maintenance plan is still NOT_QUALIFIED and NOT_AUTHORIZED.

Fresh normal service evidence: qualified observer8b9355db22:45 PASS (supportPID240065 and original
archive/authority/NL1 generation/history unchanged); real login/five existing pages/logout22:46
PASS without messages/business mutations. NL1 23:00:55 and NL2 23:02:00 native probes each pass
4HTTPS/3DNS/authentication/expected egress; identities unchanged and own probe children reaped.
An initial local probe launch lacked RNS in system Python; it never reached a network test and is
retained separately from the subsequent correct native-environment runs. No MESH recovery/restart.
Root collector cycles23:01 and user cycles23:04–23:05 complete0; all four timers enabled/active/
waiting. Own root session closed; no production holds, daemon reload/stop, accepted image changes
or linked resume occurred. This is normal baseline preservation, not capture acceptance/reboot proof.

The private B candidate APK and instrumentation APK plus native-build receipt are retained under
/mnt/data/fc-ha02-followup-20261127/basic-candidate-ba569748/, not Git/public downloads. Client source
at215c7fcb is byte-identical toba569748; the follow-up changes only test fixtures and documentation.

### Exact-source follow-up and distinct broad-CI failure

894ffed37d21553dfb508609002227aa3c7949df native-support46075423497 SUCCESS;
independent ZIP reader checks artifact15234942307 SHA256
9595597e7edde17eb7faa9c43ddb1d52e19ad19dffbceaa3d7aa8053329e96b4,
362 tests/zero skips and exact receipt source. Android46075423494 SUCCESS.
da551d55fd3b2289d6b373048f39ef54c47445c5 pushed/remote-matched;
native pre-hook46076761745 and Android46076761677 SUCCESS. Native pre-hook artifact15235576433
is retained by CI with exact source closure; this does not qualify shared generation retirement.

Original111866ae phase0 artifact15233678699 (SHA256
9563fa078cd23a95754dcdd535a18a5f00091d04e787578602cbea0d1ccb0283)
and Linux artifact15234710775 (SHA256
5cc3505a913e047d756f8e75c130e8954cf2ca51e18e99b5efc92266c27c487e)
are independently retained/read. Their14 failures are Docker unit fixtures traversing the host's
root-owned /run/docker/plugins; Python3.13 raises PermissionError, so neighboring/allowed requests
are refused before their expected result. This is separate from the support JSON race and is not
a production AuthZ bypass. Fake Engine fixtures now use disposable control-runtime paths, keeping
/proc,/sys,/dev and testing inaccessible control paths still refuse.37 focused checks PASS on3.14;
exact broad CI on its own3.13 context remains required. No production code or installation changed.

Initial pre-hook create/start outside the enrolled parent remains unclosed. A shared Docker
generation maintenance window is not automatically authorized; first qualify its exact impact,
old runtime completion and bounded recovery. Existing HA key reconciliation now passes;
independent external custody remains open.
No installed OWNER adapter, coherent encrypted kit, independent kit verification or linked resume.
Part B has an implemented/tested source and debug candidate, not native/public rollout acceptance.
External custody, source-host-free restore,
console reboot-startup and FLEET-PRODUCTION-ONBOARDING-1 remain separate and open.
Required product outcome: «Подготовил VPS → указал IP, доступ и роли → запустил ввод →
получил проверенный активный узел».
