# L04.2-R3 — readiness cause preservation and bounded retry

Status: **PARTIAL / PACKAGE_GATE_FAILED — ENVIRONMENT_HARNESS_FINALIZATION**.
Same PLAN L04.2; no new top-level ID.
Input main `70b919bba0aac1249c6d2c5a6e220e1ee0ae058d`.
Accepted R2 runtime `169aa687f497f8be690be5331879f994636135e1`.

Latest continuation input `623cdb290c23243a69000675c28824e56512bb62`: source gate
DONE/review accepted for package progression; raw full suite remains FAIL, not
overall CI PASS. Review separates local36 from environment fixture-absent19;
union55 is not a new baseline. Runtime2d125137 remains unchanged. New native/
system, bounded reference and exact .11 construction PASS. First embedded
integrity gate assertions/container exit0 PASS, but the outer launcher exits1
when overwriting the root-owned inner receipt. No installed package or live gate
follows. This is an environment/harness failure, not an established product defect.
The earlier evidence below remains historical, not a second active task.

## Review and immutable boundary

[R2](2026-10-26-linux-mesh-failure-preservation-l04-2-r2.md) is **FINAL PARTIAL /
READINESS_CAUSE_UNRESOLVED**: the cache fallback masked the original typed fetch
error. Its construction/package/system setup/GUI authorization evidence remains
accepted. No further live Connect on .10 is performed or permitted here.

Correct sealed internal/unpublished .10 candidate is
`4264406722f6dd3efb83e9d9666e67180ce4f950333bb3e711bcbb4f5068b55a`,
source `b8e9196d205c6810e02a642678517a4fc44b921b`, system source169aa68,
system `8ab7f298df10a89bcd116fbddaa8a23e37ff1581de3a456bb1cce69175ad9120`.
The earlier task-supplied candidate ending `24c12551cedd052a5b` is incorrect and
is not used as artifact identity. No old artifact or failed derivative is modified.

## Minimal source correction

- `carrier/desktopmesh/readiness_fetch.go` retains the exact typed availability
  error locally. Unusable cache cannot replace it; validated READY cache still
  returns VALIDATED_CACHE. Successful Accept/readback, denial persistence and
  trust/protocol fail-closed paths are unchanged. FETCH_FAILED remains the
  independent import/receipt result, not the returned transport cause.
- `clients/linux/mesh_service.py` removes only MISSING and EXPIRED_ON_IMPORT from
  TRANSIENT. An explicitly transient fetch error may lead to one cooldown retry;
  its unusable cache is terminal for that generation. The300-second boundary,
  cancellation and R1/R2 all-stage cleanup/retry fencing remain unchanged.
- `clients/desktop/backend.py` admits existing FETCH_INCOMPATIBLE_RESPONSE in
  strict diagnostics. Other required existing codes were already allowed. No new
  wire code, public schema, RNS command or authorization relaxation is introduced.

## Deterministic old-red / new-green

No private identity, live gateway, server provisioning or owner state participates.
Go tests use real ReadinessClient, signed synthetic ReadinessCache, the real
resolver and direct→relay route with controlled transports/clocks. Materials
tests exercise real prepare/resolver/receipt creation. Python tests exercise real
NativeMaterials framed child IPC, MaterialOwner cache/receipt persistence,
PacketSession and Supervisor, with a synthetic command transport and controlled
retry wait. Supervisor reasons are never assigned by the test.

Old-red records:

- Expired cache masks six availability codes as EXPIRED_ON_IMPORT; missing cache
  masks them as MISSING, while import_result remains FETCH_FAILED.
- Direct challenge timeout selecting a relay masks RNS_UNAVAILABLE as expired.
- Materials prepare masks six availability causes as MISSING.
- Supervisor still RESTORING after the cooldown-only second attempt instead of
  terminal FAILED; diagnostics render FETCH_INCOMPATIBLE_RESPONSE as UNKNOWN.
- Valid signed-cache fallback, durable authorization denial, trust/protocol
  fail-closed and cancellation controls pass without source changes.

Fixture-development failures (missing standalone Python import paths and a
receipt command retaining refresh-only fields) were corrected in the new tests
before the verified old-red record. A later new-test assertion accidentally
observed the old Supervisor during explicit later resolve; the test now starts a
separate actual Supervisor after confirmed cleanup. No existing assertion,
native timing contract or production path was relaxed.

The initial targeted correction alone did not authorize package progression.
The later source-gate review acceptance and package continuation are recorded below.

## Relay observability debt

**READINESS_RELAY_PROBE_CORRELATION_GAP** is assigned to existing L06/recovery.
`ReadinessRelay.Post` validates the probe, but the request callback and subsequent
relayProcess/RNS worker/Channel.readiness_request/provider chain do not propagate
that correlation. Zero direct correlation rows cannot establish the number of
relay calls. R2 attempts1–12 are not relabelled as twelve fetches or exactly one
server fetch. R3 acceptance uses the preserved typed cause; the network/public
protocol is not expanded and this debt does not block the source correction.

## Initial checkpoint — gate and delivery status

| Gate | Status |
|---|---|
| Go desktopmesh and all seven native test packages, exact Go1.26.0/race | PASS; no external network, isolated synthetic non-loopback interface |
| Python targeted material/supervisor/R1/R2 cleanup |136 PASS, development selection |
| Authenticated lifetime/terminal/status, exact Go1.26.0 fixture |15 PASS /108.29s |
| Combined manual/Auto root→UID, exact fixture |3 PASS /79.20s |
| MESH service/network/ownership/chat admission |157 PASS /19.50s |
| R1/R2 cleanup, standalone |32 PASS /4.84s |
| Full desktop |1317 PASS /82 existing SKIP |
| Restricted/readiness/Android/Python contracts |142 PASS /1 FAIL /0 SKIP;10.93s |
| Full repository / historical failure-set equality | NOT_RUN after first affected failure |
| New system/reference advancement/internal .11 | NOT_BUILT |
| Package/install/rollback | NOT_RUN |
| Corrected P0/P1/Auto/lifecycle/AppImage | NOT_RUN |

Test-only binaries are not system/candidate artifacts. Initial Go1.26.1 evidence
is supplementary; exact Go1.26.0 race and native/combined runs subsequently pass.
One fixture preparation used an older Python lacking tar extraction `filter`;
another release-test fixture preparation rejected Go1.26.1 before build because
it requires exact1.26.0. Both are retained infrastructure observations, not PASS
or product failures. No locks/pins were changed to bypass either check.

### First affected-gate failure and STOP

`tests/test_android_challenge_contract.py::test_android_response_parser_and_proof_roundtrip`
fails with Java exit1:
`NoClassDefFoundError: com/google/gson/JsonElement` while loading
`com.familyconnect.app.FriendsReadinessGoldenTest`. The Java readiness assertion
is not reached. The expected Gson dependency hash was checked on the host, but
the generated classpath used `/workspace/state-client-build/...`; its retained
`channel-only-20261005` cache directory is an absolute symlink outside the
isolated container's mounted source tree.
This is fixture classpath availability, **not evidence of an Android/readiness
protocol or R3 runtime defect**. It is still an unpassed mandatory affected gate.

No test replay, classpath repair/run, production source patch or package build is
performed after this failure. Exact failure ID is absent from the accepted local
36-ID residual baseline: observed affected selection has one new failure and zero
errors. This is **not** a fresh full-repository failure-set comparison; that run
is NOT_RUN after STOP. Historical36/phase0-Docker54 remain historical evidence,
not a general CI PASS and not a waiver for this failure.

[Sanitized evidence](2026-10-27-linux-readiness-cause-preservation-l04-2-r3/evidence.json)
records the exact baseline/observed/new IDs, source and private-log SHA256, counts
and preservation checks. Raw logs, synthetic fixture artifacts and private test
state remain outside Git. Source is not marked review accepted. System-reference
pins and package version remain unchanged. New system/candidate IDs and artifact
hashes are **NOT_CREATED**, rather than invented or copied from .10.

CI: no new completed all-green CI result is claimed. Local mandatory source gate
has stopped; historical Control setup timeout/Client Linux setup incompleteness
and36/54 residual receipts do not become a PASS for this checkpoint. Any workflows
triggered by the ordinary source push are separate evidence, not permission to
build or continue live after this STOP.

## State and excluded scope

Read-only hash audit confirms unchanged .10 DEB/AppImage/system, protected
original seven files, retained READY image and failed derivative. READY SHA256:
`47095296a9b4352450c2c5b79a875ea76a5064f1e142bc84e781147b6ce5ac68`.
No VM boot, setup, fetch, registration, Connect/Disconnect, material refresh,
server/policy/grant/device mutation or production deployment occurs. Android106
source/reference, dependency locks and Go/Xray pins remain unchanged.

**Owner workstation NOT_USED. L05/messages/voice acceptance/signing/publication
NOT_RUN.** L04 remains IN_PROGRESS; completion requires all installed gates on
the new exact candidate, not source-only test success.

Checkpoint hygiene: secret-pattern scan plus manual staged review, strict JSON
(duplicate keys/non-finite values rejected), added local links and both staged/
working `git diff --check` pass. Only six runtime/test files, STATUS/PLAN/index,
this report and its sanitized JSON are staged. Pre-existing ops/documentation
edits and all generated/private artifacts remain unstaged. Test containers and
their children have exited; original protected state and .10 hashes still match.

**STOP. NEXT — review L04.2-R3.** Resolve the failed contract fixture/gate through
review before any .11 system/package or installed continuation. No live replay on
.10 is permitted.

## Reviewed same-environment Android/Python continuation

Review accepts source2d125137 for affected scope and classifies the earlier
Gson `NoClassDefFoundError` as a host-classpath/symlink harness failure. The
accepted Go race, cleanup32, native15, combined3, MESH157 and desktop1317/82skip
results are retained, not rerun. No product/runtime/test source, assertion,
Android106 reference, lock, dependency pin or Gradle build file is changed.
No new task ID, R4, runtime checkpoint, version or candidate is created.

### Environment and one authorized gate

- Exact tracked current-main source is exported and its Git tree restored inside
  a fresh Docker named filesystem; unrelated working-tree changes are excluded.
- Java17.0.13+11, Gradle8.11.1 and Python3.13.17; every requirement from the exact
  control/identity locks is checked against installed versions. Synthetic release
  fixtures use exact Go1.26.0 and current source, not retained product artifacts.
- `GRADLE_USER_HOME=/workspace-state/gradle-home` is a fresh real directory.
  Standard unchanged `test goldenClasspath` resolves pinned Gson2.13.2 through
  Gradle. No old golden-classpath, host CLASSPATH, retained symlink cache, manual
  JAR injection, dynamic dependency or unpinned substitution is used.
- Generated classes and dependency JARs remain in the same image/named filesystems
  and absolute paths for Python consumption. Every JAR is present and hashed;
  no classpath parent is a symlink. Source and output are inside this environment.
- Private scripts are complete before execution, syntax-checked, SHA256-recorded,
  mode0555 and mounted read-only; evidence is separate. No running file is edited.

Gradle ran **once:171 PASS /0 FAIL /0 ERROR /0 SKIP**. The assistant's post-Gradle
preflight incorrectly required the optional absent `build/resources/main`
directory even though the project has no main resources. It stopped before
pytest. After that PID exited, a separate immutable Python-only harness accepted
this standard optional directory and consumed the same freshly generated
classpath. Gradle tests/classpath generation were not repeated; no product
assertion or classpath entry was changed or removed.

The one Python selection finishes **139 PASS /4 FAIL /0 ERROR /0 SKIP**, exit1,
11.642s. The original
`tests/test_android_challenge_contract.py::test_android_response_parser_and_proof_roundtrip`
now **PASS**; Gson loading and the Android/Python readiness assertion are reached.

### New environment blocker and STOP

All four failures are in
`tests/test_friends_restricted.py::test_backend_delivery_consumed_by_native_material`:
`[current]`, `[production-offset]`, `[production-utc]`, `[negative-offset]`.
Their Go subprocess exits before delivery validation with
`module lookup disabled by GOPROXY=off`.

The assistant's preparation container mounted/configured the offline Go module
and build caches, but the Python test container did not. Thus fixture construction
passed while its later `go run` could not resolve dependencies. This is a concrete
**harness prerequisite omission**, not evidence of Android106, R3 readiness or
native delivery incompatibility. No cache/pin/source repair or test replay is
performed after this failure.

The four observed IDs are outside the accepted36-ID historical residual set;
they cannot be waived as historical failures. This comparison covers only the
affected143-test selection, **not a fresh full-repository comparison**. The
mandatory source gate remains unclosed. Full-suite comparison, new system/.11,
package gates and corrected P0/P1/Auto/lifecycle/AppImage are **NOT_RUN/NOT_BUILT**.
No general CI PASS is claimed. Runtime source remains exactly2d125137.

[Sanitized continuation receipt](2026-10-27-linux-readiness-cause-preservation-l04-2-r3/same-environment-gate.json)
records exact tools, locks, classpath/JAR hashes,171/139/4 counts, failure IDs and
baseline comparison, immutable harness/log hashes and preservation checks. Raw
logs, source capsule, synthetic fixtures and Docker filesystems remain private.

### Preservation and handoff

Exact .10/system artifact hashes, the read-only READY base, failed derivative and
original protected seven files remain byte-identical. No VM is booted; no install,
setup, Connect, fetch, registration, server/material/policy change or teardown
occurs. **Owner workstation NOT_USED**. Messages, voice acceptance, L05, signing
and publication remain **NOT_RUN**. L04 stays IN_PROGRESS under existing L04.2.

Only STATUS/PLAN, this existing report and sanitized continuation JSON are changed
for this documentation/evidence checkpoint. Secret scan, strict JSON, local links,
staged scope and `git diff --check` PASS before the ordinary commit/push;
unrelated local work remains unstaged. No rollback is required: product bytes and
installed state have not changed.

**STOP. NEXT — review L04.2-R3.** Close the missing Go-cache harness prerequisite
under review before a further mandatory source-gate run; no .10 live replay and
no .11 build while that gate remains open.

## Reviewed Go-cache closure and canonical workflow continuation

Input main `0a37d23177d6aa10c0e38fd52a45a652f4e60615`; accepted product source
`2d125137b28e096187433608022daa1590d7a6f0` remains byte-identical. All intervening
commits are documentation/evidence only. Android source/reference, Gradle build
file/dependency versions, R3 tests, Go locks and runtime files are unchanged.
Current tracked source is exported separately from unrelated local changes.

Retained image `sha256:42071675d572679422f4f937a7eb325da5783d95073a82823f56ed2eb6dcf9ee`
and named filesystems pass read-only provenance checks. Java17.0.13+11,
Gradle8.11.1, Python3.13.17 and exact Python locks are preserved. JAR hashes match
the accepted Gson2.13.2, BouncyCastle1.85.2 and JUnit4.13.2 receipts; canonical
classpath has no host path or symlink dependency. Read-only `javap` resolves both
JsonElement and FriendsReadinessGoldenTest. Gradle171 PASS is retained, **not rerun**.
Generated build files are copied byte-identically to the current clean export at
the same `/workspace` path; dependency cache remains read-only at its original
`/workspace-state/gradle-home` path. No old channel-only cache is used.

Before pytest, the same isolated environment proves **offline Go cache closure**:
exact Go1.26.0, `GOPROXY=off`, `GOTOOLCHAIN=local`, read-only `GOMODCACHE`, shared
writable `GOCACHE`; `go mod verify`, `go list -mod=readonly -deps` and compilation
of the actual delivery-check program PASS. The preflight compiles but does not
execute that validator. Synthetic fixture preparation and the subsequent test
container use those same cache mounts/environment. No external network is needed.

The one authorized exact Android/Python selection now completes **143 PASS /
0 FAIL /0 ERROR /0 SKIP**, exit0,11.17s. All four native delivery cases and the
original Android response/proof case PASS. No assertion, selection, pin, product
code or wire contract was changed. No retries were needed.

[Cache-closure receipt](2026-10-27-linux-readiness-cause-preservation-l04-2-r3/cache-closure.json)
records source/tool/cache provenance, JAR/build inventory hashes,143-test result,
bounded workflow path checks and unchanged protected state.

Only bounded path coverage is added to both push/pull_request triggers of the
existing canonical readiness workflow: readiness Go files/locks, native materials,
Linux material/supervisor boundary, desktop diagnostics/R3 test and control lock.
Jobs, commands, actions, tools, assertions and timeout are unchanged. This is a
CI/evidence commit, **not a new product-source checkpoint**. Canonical GitHub
workflow result was PENDING at the coverage commit; its final SUCCESS and the
subsequent full-suite comparison are recorded below. No overall CI/source gate
PASS is inferred from this targeted workflow.

Exact .10/system, read-only READY base and protected seven files remain unchanged;
owner workstation NOT_USED. New system/.11/package/live, L05/messages/voice
acceptance/signing/publication remain NOT_RUN. No server/material/policy changes.

**NEXT — canonical readiness workflow SUCCESS, then full-suite comparison.**
Only complete source gate PASS permits the already-authorized .11/package/live
continuation; the same L04.2-R3 task remains active.

## Canonical CI SUCCESS; full-suite exact-baseline STOP

Coverage/evidence commit `e93bf7ddc76504e857ffaeffc8558c1a8526e780` was pushed and
the remote main SHA verified. Initial ordinary push encountered transient DNS
resolution failure; the next ordinary non-force push succeeded, without resolver
or workstation-network changes.

Canonical [Android Friends readiness wire contract run40491350035](https://github.com/Joker20380/family_connect/actions/runs/40491350035)
is **completed / SUCCESS**, attempt1, exact commit e93bf7d, golden job122145788727.
All setup, Gradle, Android/Python contract and post-job steps report success. Its
existing commands/tool versions/timeout remain unchanged; only bounded trigger
paths changed. This canonical workflow result is separate from the local exact
143-test selection and is not an overall repository CI PASS.

The full repository then ran once, without selection/deselection, xfail, removed
assertions or suppression, in the retained Ubuntu26.04/Python3.14.4 full-suite
image, private network namespace, exact Go1.26.0/offline caches and Java17.0.13+11.
The source is a clean tracked export of e93bf7d; synthetic release fixtures bind
that same commit. Retained fresh Gradle classes/JARs are reused; Gradle is not
rerun locally. The test image differs from the Python3.13 Android-only gate;
neither result is mislabeled as the other environment.

Full result: **55 FAIL /3373 PASS /105 SKIP /0 ERROR**,7 subtests PASS, exit1,
254.67s. Existing conditional skips remain unsuppressed; their observed count is
105, not the earlier local99. No skip marker or test configuration was changed.

| Comparison | New IDs relative to that baseline | Missing baseline IDs | Exact match |
|---|---|---|---|
| Accepted local36 |19 |0 |NO |
| Accepted phase0/Docker54 |1 |0 |NO |
| Union of historical36 and54 |0 |0 |55-ID union only; **not adopted as a new baseline** |

The19 additional local IDs are six mobile-bootstrap TransportBridgeTest cases,
six owner-disconnect DeadlineBridgeTest cases, six inherited bridge cases and
the tunnel-restart health fixture. All stop with FileNotFoundError on historical
untracked source-capsule paths absent from the clean tracked export, before their
product assertions. All19 IDs already occur in the historical Docker54 receipt.
The single ID additional to Docker54 is
`clients/desktop/tests/test_chat_direct_runtime.py::test_unit_umask_fresh_runtime_and_real_uid[lock]`,
already present in the accepted local36 receipt. Thus **no novel failure/error ID
relative to the historical union and no new product defect are established**.

Nevertheless55 exceeds both historical counts and matches neither exact accepted
environment baseline. The checkpoint does not silently combine them to claim
source-gate PASS. The [updated cache-closure receipt](2026-10-27-linux-readiness-cause-preservation-l04-2-r3/cache-closure.json)
contains both complete baseline ID sets, actual IDs, differences, canonical CI
IDs, counts and log/XML SHA256. No historical fixture tree is fabricated/copied
to hide these failures; full suite is not rerun and no product/test patch follows.

Result remains **PARTIAL / SOURCE_GATE_FAILED** at
`FULL_SUITE_EXACT_BASELINE_MISMATCH`. New native/system/reference advancement/.11,
package gates and corrected P0/P1/Auto/lifecycle/AppImage remain **NOT_BUILT /
NOT_RUN**. No new version, system/candidate ID or artifact hash is invented.
There is no deployment or rollback to perform.

Final readback: tracked tested source unchanged; current product/runtime/tests/
locks still byte-identical to accepted2d125137. Exact .10/system artifacts,
read-only READY base and protected seven files retain their hashes. All test
containers have exited. Owner workstation NOT_USED; no VM boot, live .10 Connect,
server/material/policy change, message, voice acceptance, L05, signing or publication.
STATUS/PLAN/index and this report/evidence are updated under the same L04.2 ID;
unrelated work remains excluded. Secret scan, strict JSON, links, staged scope and
whitespace checks precede the ordinary documentation/evidence commit and push.

**STOP. NEXT — review L04.2-R3 full-suite baseline/environment comparison.**

## Review acceptance — package progression authorized

Input main623cdb290c23243a69000675c28824e56512bb62; accepted product source
2d125137b28e096187433608022daa1590d7a6f0. **R3 SOURCE GATE DONE / review accepted
for package progression**. This supersedes the preceding baseline STOP, not its
raw evidence. Full suite remains **55 FAIL/3373 PASS/105 SKIP/0 ERROR**; no overall
CI PASS. Accepted decomposition: common35, local-only1 known lock/umask case,
Docker-only19 historical fixture-input absences. Actual55 is the exact union,
new/missing IDs0. The19 stop before product assertions and are classified
ENVIRONMENT_FIXTURE_INPUT_ABSENT, existing D02.1-R/CI debt. Separating them leaves
the accepted local36 baseline. Union55 is **not** a new permanent baseline.

Full suite is not rerun; historical capsules are not copied/fabricated, and no
test assertion/skip/xfail or product source is changed for this normalization.
Go race, cleanup32, native15, combined3, MESH157, desktop1317/82 existing skips,
Android/Python143 and canonical workflow40491350035 SUCCESS remain accepted.
Proceed in the same L04.2-R3 task with offline native/system, bounded reference
advancement and internal0.2.12~l03.2.11, package gates, then one corrected live P0
only after package PASS. No separate source checkpoint or review pause.
Historical .10/system and authorized READY/protected state stay immutable;
owner workstation NOT_USED. L05/messages/voice acceptance/signing/publication
remain NOT_RUN. No server/material/policy changes are authorized here.

## R3 native/system construction and bounded reference advancement

Review acceptance commit7983b587f47a2b3c425568949a760da8396c73e5 was pushed;
remote main matched. Build input is its clean tracked export, with no unrelated
worktree changes. Runtime/tests/locks/pins match accepted2d125137. No .10 member,
incomplete native binary or historical fixture capsule is reused as new source.

Offline Ubuntu26.04/Python3.14.4 builder uses exact Go1.26.0, pinned Xray revision
d2758a023cd7f4174a5a5fa4ff66e487d4342ba0 and unchanged patch/Android106/RNS pins.
Private network namespace, `--network none --cap-add NET_ADMIN`, scoped
safe.directory `/workspace` and `/xray.git`, synthetic UP/non-loopback fcbuild0
without addresses, zero default routes and bounded ENETUNREACH probe PASS;
resolver unused. Four exact requirement locks,630 RECORD files,17 distributions,
pip check and reference preflight PASS. Source is read-only; harness is complete,
syntax-checked, hashed and read-only before launch; output is fresh and separate.

Standard native builder completes once: seven native packages PASS with race
detector, including unchanged protection assertions; binary follows test PASS.
Carrier desktopmesh readiness race PASS separately. Dependency/license inventory,
source set before/after equality, RNS packaging and system installer/archive
readback PASS. AWG/TCP pinned inputs come from their retained builder images,
not historical system archives; behavior/pins are unchanged.

| Construction artifact | Exact result |
|---|---|
| Native source digest |2292c24503ed0b275d2c296100dbca4572973cf3dce41d12e22645154ca9c833 |
| Native binary |29018163 bytes; SHA25608314caba221da54c359c9554e365cb5f0ea748c9e3074b245c1821a0f32c718 |
| System build ID |34b27cb97abb149b9a59f7ea4ad2ea2e9b79aab5e4e9345c064b6a98d20e5db8 |
| System archive |49251389 bytes; SHA2564794ae4d8bb0b794aced081b4c330595e18aeaf334ba6b787c248daaa5725ae4 |
| Archive inventory |759 regular members; uid/gid0; no group/world-writable members |
| RNS digest, unchanged |66128235484f01b82bfd2e4ad604a486428706fc48020abbf84211554edef26e |

Reference advancement changes only source_checkpoint, native_source_digest and
two of113 source_files hashes, preserving the complete key set:

| Member | New SHA256 (accepted source = manifest = extracted member) |
|---|---|
| lib/backend.py |12ab9f4b9b3938c652eb58271d126c73509c1f47cd71e44bb4c81bcd68766a0d |
| lib/mesh_service.py |e34d6b1462370dea9d6046ffedc1e6316be4e43e962208065f6fa707aac21bf3 |

mesh_chat_service.py, mesh_materials.py and every other source pin remain exact.
No native binary-derived fields exist in this reference contract; none are added.
Verifier logic/SYSTEM constants and all Go/Xray/RNS/Android pins remain unchanged.
Old reference/new system rejects with `System sources differ from the pinned
candidate contract`; new reference/new system passes actual embed/extract/import
verification. Synthetic self-consistent mutations of changed mesh_service and
unchanged mesh_chat_service reject with the same source-contract error. Historical
.10 system also rejects. Targeted candidate/system tests: **46 PASS**.
[Construction/reference receipt](2026-10-27-linux-readiness-cause-preservation-l04-2-r3/package-progression.json)
records identities, exact hash changes and test log hashes.

This is complete system construction/readback, **not installed acceptance**.
Next: commit/push bounded reference advancement, then offline .11 candidate and
package gates without review pause. No overall CI PASS; full-suite review
normalization and D02.1-R debt remain as recorded. Owner workstation NOT_USED;
no live .10, server/material changes, L05, signing or publication.

## Exact internal .11 construction/delivery

Bounded reference commitadf81057b21798a4041779658a69c57f680cdd68 is pushed and
remote main verified. The package build uses a new clean tracked export of that
commit, Ubuntu26.04/Python3.14.4, network none and the unchanged standard package
builder/verifier. Exact appimagetool854e19e/build313 and official Type-2 runtime
release417724209/targetfedfad51acc2860b2916a1eef32ba4a500ff31ef retain their
accepted sizes/hashes/signature provenance; runtime supplied offline, no fetch.

Version **0.2.12~l03.2.11**, candidate
**570a5515173d66b9a25cd9f01f76e72f492a41acb1f341ee95368aac62e78252**;
sourceadf81057b21798a4041779658a69c57f680cdd68,
system_source2d125137b28e096187433608022daa1590d7a6f0, source_dirty=false.
System34b27cb97abb149b9a59f7ea4ad2ea2e9b79aab5e4e9345c064b6a98d20e5db8,
standard-source-rebuild. No package/application ID or public version changes.

| Internal artifact | Bytes | SHA256 |
|---|---:|---|
| FamilyConnect_0.2.12~l03.2.11_amd64.deb |56148076 |1976d2bfe13cc0efc421e7cfcdf52bd301ed725168e743c0b32d372422ab062f |
| FamilyConnect-0.2.12~l03.2.11-x86_64.AppImage |58116600 |92ff5a79f61d8d29e32596d8333d0880f1fe60803d831de418cad63952517a5d |
| FamilyConnect-Linux-0.2.12~l03.2.11.tar.gz |114647 |8adeda8e6af059100d1254c40db186fd4d8abd7812090c33af38271c575c3a70 |
| FamilyConnect-MESH-system-amd64.tar.gz |49251389 |4794ae4d8bb0b794aced081b4c330595e18aeaf334ba6b787c248daaa5725ae4 |

[Exact delivery manifest](2026-10-27-linux-readiness-cause-preservation-l04-2-r3/candidate-delivery.json).
Legacy remains compatibility shape only. Complete artifacts stay local, sealed
and read-only, with writable evidence separate; no artifacts enter Git. A host
chmod preflight encountered root ownership before any gate; modes were set in
an isolated container without changing artifact bytes, before test execution.
Package/systemd/rollback/live acceptance is still pending, not inferred from
construction. Owner installed/public/invitation versions are unchanged; no public
download/catalog link, signature or rollout. Rollback target for disposable
package gates is the exact immutable .10/system8ab7f298 pair, never a .10 live
Connect. Next: affected package gates, then corrected P0 only after complete PASS.

## Package harness finalization STOP

The first package gate extracts the exact DEB and AppImage, compares embedded
candidate.json bytes and both embedded system archives against the complete
new system artifact. All assertions pass; durable sanitized inner receipt
confirms candidate570a5515/system34b27cb9 equality. The retained Docker terminal
event independently records **container exit0**. No installed system, polkit
setup, VPN action or private identity is used by this extraction-only gate.

The outer launcher then removes the disposable container and attempts to write
its own execution summary to **the same `embedded.json` path** already created
by the inner root process with root:root/mode0644. The ordinary host user cannot
overwrite that file: **PermissionError, errno13**, launcher exit1. This is a
private orchestration receipt-name/ownership collision; it is not an artifact
integrity failure. The original assertion receipt is preserved. No raw secret,
credentials or private state is involved. Outer exit1 is not reported as PASS.

| Gate | Actual outcome |
|---|---|
| Source gate | DONE / review accepted; no full-suite replay |
| Standard native seven packages + carrier readiness race | PASS |
| RNS, dependency/license inventory, system/archive readback | PASS |
| Bounded reference positive/negative gates; candidate/system unit tests | PASS;46 PASS |
| Exact .11 DEB/AppImage/legacy construction and checksums | PASS; source_dirty=false |
| Embedded DEB/AppImage candidate/system equality | PASS; inner container exit0 |
| Package harness finalization | FAIL_ENVIRONMENT; outer exit1; receipt collision |
| Installed system/DEB/AppImage, pkexec, reinstall/remove, rollback, mixed system | NOT_RUN after stop |
| New .11 package AWG/TCP, cleanup/readiness/native/combined/MESH/full-desktop selections | NOT_RUN after stop; prior accepted source evidence retained |
| Corrected live P0/P1/Auto, lifecycle, installed AppImage sharing | NOT_RUN; Connect count0 |

All executed scripts retain their sealed hashes; no running script was edited,
renamed or appended. The launcher hash is
5dde9382f3311431b03367d61d0a4c32905cbeee81c7d29f493ffecb441f1a19.
The failed gate is not replayed, and neither product source nor the harness is
patched after the stop. A separate final accounting receipt records the failure
without overwriting the inner receipt. All task containers are removed; no VM
is created or booted and no privileged product owner/TUN was started. Prepared
remaining scripts are not evidence of execution or PASS.

Final readback: exact .11 artifacts/system and historical .10/system are
byte-identical; .11 delivery files are read-only. The retained READY image remains
read-only and retains SHA25647095296a9b4352450c2c5b79a875ea76a5064f1e142bc84e781147b6ce5ac68;
original protected seven files are byte-identical. Identity/cache/floors/settings/
keyring/store are not opened or changed in this continuation. Product/runtime/
tests/locks/pins remain accepted2d125137; only the authorized reference fields
advance. No server/material/policy change, .10 Connect, owner-workstation action,
message, voice acceptance, L05, signing or publication. Full raw suite remains
55 FAIL/3373 PASS/105 SKIP/0 ERROR; overall CI PASS is not claimed.

**Result: L04.2-R3 PARTIAL / PACKAGE_GATE_FAILED**, typed substage
`ENVIRONMENT_HARNESS_FINALIZATION / EMBEDDED_RECEIPT_FILENAME_COLLISION`.
L04/L04.2 are not DONE. This does not revoke the accepted source gate or invent a
new runtime checkpoint/version. New construction is complete but installed
acceptance remains open. Ordinary commit/push follows secret/JSON/link/scope/
whitespace checks; unrelated work is excluded.

**STOP. NEXT — review L04.2-R3 package-harness finalization.**

## Owner decision — 2026-10-27

**PAUSED / non-blocking desktop engineering.** R3 SOURCE GATE DONE/review accepted;
.11 CONSTRUCTION DONE/frozen internal candidate. L04.2 is not DONE; installed
package/live P0/P1/Auto remain NOT_RUN. No retry, launcher repair or new Linux
checkpoint. Critical path is now ANDROID-CONTROLLED-BETA; receipt collision stays
in existing D02/CI debt, not an Android launch blocker.
[Single owner-decision/readiness report](2026-10-27-android106-controlled-beta-readiness.md).
All earlier results/NEXTs above remain historical evidence, not current permission.
