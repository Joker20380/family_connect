# HA-02 continuation and separate basic metadata candidate

Entry: feature/device-technical-metadata-20261115, local/remote
fa27314589a8c1ce611913dedbaa7e4da421aa02; no newer change at entry.
Main remains da94566acb770dc758a1e057f02bfef784585a75. Accepted installed components
and source-only Docker111866ae are not reinstalled. A has production priority;
B changes are separate source/candidate work, never a production binding change during A.

## Current outcome —27 November23:20UTC

A is **not complete**: no installed OWNER executor adapter, common held interval, new stopped-support
snapshot, encrypted fleet kit, independent kit verification or linked normal resume. The concrete
unclosed channel is create/start already accepted before first AuthZ attachment, with downstream
containerd/shim work outside the mandatory parent. Online reload is disproved by the native test;
finite old-generation retirement/recovery is not qualified. A shared-window proposal affects14
excluded neighboring containers and cannot be executed under project-only authorization. Next step
is that isolated generation-retirement/recovery qualification, not another census or production stop.
Existing HA AES key native read/preservation/real consumer now pass; it is not the current blocker.
Normal baseline is preserved: fresh authenticated NL1/NL2 HTTPS/DNS/egress, panel login/pages and
collector/timer cycles pass; support PID/archive/authority/generation and marker history remain.
No own production restrictions remain because none were acquired. No reboot-startup claim.

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
