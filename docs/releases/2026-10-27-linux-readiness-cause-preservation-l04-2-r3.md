# L04.2-R3 — readiness cause preservation and bounded retry

Status: **PARTIAL / SOURCE_GATE_FAILED**. Same PLAN L04.2; no new top-level ID.
Input main `70b919bba0aac1249c6d2c5a6e220e1ee0ae058d`.
Accepted R2 runtime `169aa687f497f8be690be5331879f994636135e1`.

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

## Gate and delivery status

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
