# L04.2-R3 — readiness cause preservation and bounded retry

Status: **IN_PROGRESS / source gate continuation**. Same PLAN L04.2; no new top-level ID.
Input main `70b919bba0aac1249c6d2c5a6e220e1ee0ae058d`.
Accepted R2 runtime `169aa687f497f8be690be5331879f994636135e1`.

Latest continuation input `0a37d23177d6aa10c0e38fd52a45a652f4e60615`: runtime
source2d125137 remains review accepted in affected scope, unchanged. The reviewed
Go-cache environment blocker is closed and Android/Python143 PASS; canonical
readiness CI and full-suite comparison still gate progression. The earlier evidence below
is preserved, not presented as a second active task or a current product defect.

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

The targeted correction passes, but the mandatory gate below stops progression.
No package progression is authorized by targeted-test results alone.

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
workflow result is PENDING; full-suite failure-ID comparison is NOT_RUN until it
succeeds. No overall CI/source gate PASS is claimed yet.

Exact .10/system, read-only READY base and protected seven files remain unchanged;
owner workstation NOT_USED. New system/.11/package/live, L05/messages/voice
acceptance/signing/publication remain NOT_RUN. No server/material/policy changes.

**NEXT — canonical readiness workflow SUCCESS, then full-suite comparison.**
Only complete source gate PASS permits the already-authorized .11/package/live
continuation; the same L04.2-R3 task remains active.
