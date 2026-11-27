# HA-02 continuation and separate basic metadata candidate

Entry: feature/device-technical-metadata-20261115, local/remote
fa27314589a8c1ce611913dedbaa7e4da421aa02; no newer change at entry.
Main remains da94566acb770dc758a1e057f02bfef784585a75. Accepted installed components
and source-only Docker111866ae are not reinstalled. A has production priority;
B changes are separate source/candidate work, never a production binding change during A.

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
