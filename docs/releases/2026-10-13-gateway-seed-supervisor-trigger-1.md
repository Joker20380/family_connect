# GATEWAY-SEED-SUPERVISOR-TRIGGER-1 — PASS (local research candidate)

PRODUCTION_PATCH_ACCEPTED = YES **for the sealed source-only research candidate**.
DEPLOYMENT = NOT_RUN. READY_FOR_CONTROLLED_DEPLOYMENT = NO until the separate
operational-readiness gates below. No production, phone or live Telemost actions.

## Exact identity and scope

Artifact root: `state-client-build/field65-export16/gateway-seed-supervisor-trigger-1/`.
Authority: `manifest.json`, `SHA256SUMS`, `candidate.bundle`, `scope.txt`.

| Identity | Exact value |
|---|---|
| Accepted supervisor parent | `c9d75db6020f9f605e891036cbb9b68cebede708` |
| Parent gateway SHA256 | `d6875817cf33fdd85c6ad78a342fc93afd16864293e94a6e5b7136eec5125765` |
| Last sealed deployed observation binary SHA256, historical, not a fresh server read | `21f0a0fdc27b50c00ea922f0b716516e2422aedf1b3797369718f7d00070509a` |
| New isolated validation source | `134083d87773dacc038c9593afdaff0c57ea951d` |
| Frozen research gateway SHA256 | `53beb661cab014c32494fa8d7384f9565300311ef467e62ae9f8c20201e5138f` |
| Binary | `build/bootstrap-broker-seed-acceptance` |
| Toolchain | Go1.26.1, Linux/amd64, CGO_ENABLED=0, trimpath, buildvcs=true, `seedacceptance` |
| Preserved separate API archive SHA256 | `12ca0c72a89ff20c1b3c70a1182a2d5d98d4d78d25e7a079bb4d75bdf34060ed` |

All1,239 entries of the accepted supervisor capsule reverified. Production source was
not reconstructed from narrative or taken from the main dirty checkout. The unchanged
API archive is a separate component, not the obsolete Python files in gateway Git
history. AKI, validity/skew, ACK, publisher/Store and provisioning were not packaged,
replaced or reverted. No dependency changes. No public version/tag/push.

The implementation was first locally sealed as73700a60…; the final child commit only
strengthens the valid-command/non-root negative test. Production code is byte-identical
between these two local seals. The intermediate build is explicitly retained under
`intermediate-before-nonroot-test-hardening/`, **not** the candidate. Root real-stack
and security evidence source-equivalence is recorded in
`receipts/final-source-equivalence.json`; final non-root and full research tests were rerun.

## Trigger, not a second supervisor

EXACT_BASELINE = PASS. SUPERVISOR_PRESERVATION = PASS.
The sole supervisor edit is a nonblocking current-generation registration hook.
Removing that hook reproduces the accepted file byte-for-byte. Recoverability, three
attempts,45s budget,1/2/4s backoff, security deadlines, atomic swap, room creation,
directory and dedicated contexts remain unchanged. Family/Reliable/Mux/lease,
admission/revocation/floors, classifier and fatal-observer files retain their hashes.

TRIGGER_DESIGN = PASS, research-only. With no explicit root policy, the original
upstream connection is returned unchanged: no bridge, socket, timer or writer starts.
The default/public build has compile-time stubs; the command/config option/socket
marker is absent from its executable. No new TCP/HTTP/gRPC/public debug endpoint.

When explicitly enabled, only `TelemostSeed` gets a generation-local context marker.
After the original authenticated upstream Gorilla dial, an in-process `net.Pipe`
Gorilla pair forwards signaling and ping/pong. It has no routable address/listener.
Dedicated connectors do not receive the marker. On one accepted command, the bridge
**first closes that actual upstream seed WebSocket**, then writes an empty-reason
WebSocket close frame1011 to the production reader. The unchanged `ReadJSON` and
classifier produce a genuine `*websocket.CloseError`; recovery follows the ordinary
supervisor path. No constructed error, direct classifier call or recovery invocation
supplies the production failure. The supplemental unit test inspects the real error.

REAL_GORILLA_BOUNDARY = PASS:
SIGNAL_READ / WS_CLOSE /1011 / ACTIVE / local_close_requested=false.
Separate trigger receipt: test_triggered=true, provider_generated=false.
PROVIDER_GENERATED_WS1011 = NOT_PROVEN by this injection; the earlier natural
production1011 receipt remains independent. Provider internal reason remains UNKNOWN.
Earlier UNKNOWN exits are not reattributed.

## Binding, security and lifetime

TRIGGER_BINDING / TRIGGER_SECURITY / TRIGGER_STATE_MACHINE = PASS.

- Explicit root-owned regular policy, trusted ancestry, no symlinks;0600, or0640
  root:service read-only for a non-root service. Runtime directory service-owned0700;
  AF_UNIX filesystem socket0600. Production entry hardcodes kernel SO_PEERCRED UID0.
- Exact executable hash, PID, proc start ticks, InvocationID if available, current
  ACTIVE generation and SHA256(room.ID), random256-bit nonce, armed_at/expires_at.
  Invalid/stale binding rejects before action. No IP/NAT or approximate-time targeting.
- One command per invocation, consumed before action; duplicate/replay/restart/stale
  generation cannot rearm. A race lost to natural close remains consumed with
  action_applied=false, never a reason to issue another fault.
- Strict2048-byte JSON, duplicate/unknown/case-variant keys rejected, one-second bounded
  request read, serial handler, no polling. Command TTL≤60s; provided root helper uses15s.
- Enablement expires absolutely within25min, based on the accepted future23min
  trigger/recovery schedule plus2min coordination. It is not a renewable armed TTL.
  DISABLED/enabled-unarmed → ARMED → READY → CONSUMED → CLEANED; unused → EXPIRED → CLEANED.
  Target-available metadata is not an armed command.
- Invalid/missing/expired startup policy disables only the seam, emits a safe diagnostic
  and does not make the gateway fail/restart. Service context survives control expiry.
  Helper crash/partial input is bounded; there is no persistent automatic command.

The full root entry and real media test passed using polkit and temporary `/run`
paths. A **fully valid bound command** from the actual non-root peer is rejected;
this is not merely rejection of malformed JSON. Positive non-root fixture factories
are private test machinery, not a config/wire override of UID0.

## Receipts and cleanup semantics

Async32-slot queue, one writer, max4096B, atomic non-overwriting link, file0600;
retention64 matching regular receipt files ordered by mtime. Foreign files are not
removed. No I/O under seed/broker locks, no network export. State, process/generation/
room safe hashes, nonce hash, prior ACTIVE state, action, independent reader1011,
recovery and cleanup outcomes only. No raw URL, SDP, ICE candidates, token, identity,
payload, close reason or arbitrary error. Schema files are under `schemas/`.

Write failure/drop is missing evidence, not protocol failure or inferred PASS. The
permission-failure real-stack fixture continued recovery/TCP/old-cache despite failed
receipt writes and socket unlink; after evidence it restored test permissions and
removed the socket explicitly. Normal root cleanup removed the socket automatically.
`CONSUMED` alone is never acceptance: actual action, reader, supervisor and media evidence
must all corroborate it.

The control listener/old target references are cleaned. The current generation's
bounded in-memory bridge remains until normal generation cleanup: detaching it by a
second socket disruption is forbidden. Later generations after expiry use the direct
path. This research instrumentation has bounded overhead, not a claim of zero cost.

## Local acceptance and differential

LOCAL_REAL_STACK_ACCEPTANCE / SAME_ROOM_RECOVERY / DIRECTORY_CONTINUITY /
DEDICATED_SESSION_CONTINUITY / OLD_CACHE_BOOTSTRAP / STALE_CALLBACK_ISOLATION = PASS.

Local SFU uses real Gorilla/WSS, Pion publisher/subscriber, SDP/ICE, RTP/VP8, Family TLS,
Reliable, Mux and persistent TCP. Production trigger/supervisor code is exact in the
test overlay. Only the accepted local-provider routing/trust/instrumentation fixture
is overlaid; `validation/` is NEVER_DEPLOY and is absent from the frozen binary.
This does not claim a real-provider canary with that executable has already run.

Each of six final race episodes: one local seed room, two local dedicated rooms,
three seed generations; one AF_UNIX trigger followed by one local-provider close to
exercise a second recovery. Directory bytes/hash unchanged; old serialized D reaches
new authenticated bootstrap/dedicated READY. Same original dedicated tag, Mux stream,
single accepted TCP socket;270–348 numbered frames, no reopen. Authenticated renewal
and traffic after old deadline pass using the controlled **lease-only clock**, not a
claim of twelve minutes elapsed live traffic. Root-positive episode also passes.

| Gate | Fresh result |
|---|---|
| Final trigger/security unit race×3 |114 test/subtest PASS;3 root-only skips covered by independent root run |
| Real-stack race×3, normal plus receipt-write-failure variants |6 PASS |
| Exact accepted baseline security/lease/supervisor race×3 |447 PASS |
| Candidate security/lease/supervisor race×3 |447 PASS |
| Root policy entry + real-stack |2 PASS |
| Baseline/default-public full suite |632 PASS each; same15 failed test nodes +2 package failures |
| Final research full suite |670 PASS; identical failure set, no new failure |
| Unchanged API regression |329 PASS,70 skipped,5 existing failures identical to sealed API baseline |
| Publisher Store/client compatibility |19 PASS |
| Reproducible research build twice; public absence; privacy |PASS |

Full suite is **NOT_GREEN**. Failure details in `receipts/differential.json`: six
bootstrap auth diagnostic assertions and their parent; six seed-read diagnostic
assertions and their parent; Go-only shared-timestamp source guard. API's four stale
time-expectation assertions and Android source guard also persist. Busy-wire flake
was not observed in the fresh comparison; it was not fixed. Security rejection tests
remain passing. NO_NEW_FAILURES_RELATIVE_TO_EXACT_BASELINE = PASS.

Earlier `final-*` logs are retained, not overwritten: local disposable credentials
had insufficient remaining validity for accelerated lease clocks, producing matching
baseline/candidate failures. New disposable fixtures used the same short-lived policy;
fresh `sealed-*`/`hardened-*` results above pass. No product timeouts, TTL or tests were
relaxed and no production credentials were renewed.

RESOURCE_BOUNDS = PASS_LOCAL: final WebSockets/PeerConnections/retained peers0 in all
six race episodes; goroutines2→2; FDs6→8 on first initialization, then8→8, no linear
growth. Old generation pumps/cleanup do not touch current or dedicated sessions.
PUBLIC_BUILD_ABSENCE = PASS. API/wire schemas and old-client requirements unchanged.

## Artifacts and operational blockers

Frozen source/binary, duplicate reproducibility build, buildinfo, full diff, separate
`acceptance-trigger.diff` and `observability.diff`, schemas, source inventory, sanitized
media/trigger receipts, tests and checksums are in the capsule. Inherited
`seed-supervisor-behaviour.diff` and previous observability diff are preserved separately
as already-applied provenance, not reapplied to c9d75db. `rollback/` contains the exact
historical deployed observation binary and accepted supervisor without trigger.
Historical unit/config references require a fresh snapshot/valid-credential check.

EXACT_BINARY_CANARY_RUNBOOK = READY_AS_PLAN (`CANARY_RUNBOOK.md`).
PRODUCTION_DEPLOYMENT_RUNBOOK = READY_AS_PLAN (`DEPLOYMENT_RUNBOOK.md`).
One frozen binary for both future contexts, no special canary rebuild/fixture tags.
Future acceptance window2710s plus180s safety, trigger/recovery by process-start+23min;
process lifetime and credential expiry are independent gates. No canary run here.

SYNTHETIC_IDENTITY_REQUIREMENTS = DOCUMENTED.
SYNTHETIC_IDENTITY_PRODUCTION = NOT_CREATED.
PREDEPLOY_BLOCKERS_REMAINING:

1. Authorized production synthetic identity/custody, no owner/tester overlap.
2. Fresh served-chain validation and required same-key credential renewal.
3. Fresh active restricted-session inventory/safe maintenance window.
4. Current collector/capture compatibility and fresh rollback/configuration readiness.
5. Exact frozen-binary real-provider canary with one narrow trigger.
6. Fresh process-lifetime and security-headroom calculation.

These are not performed or presumed solved by local source acceptance. The historical
served-certificate expiry and UNKNOWN session count are not presented as fresh state.

## Counters and next operation

PRODUCTION_DEPLOYMENT=0; PRODUCTION_RESTART=0; PRODUCTION_RENEWAL=0;
PRODUCTION_PUBLICATION_CHANGE=0; OWNER_INSTALL=0; OWNER_INSTRUMENTATION=0;
OWNER_REFRESH=0; OWNER_CONNECT=0; PROVISIONING_GATE_ARM=0; LIVE_TELEMOST_ROOM=0.
Temporary local credentials/test executables/root-control state are cleaned;
sanitized receipts, exact source/binaries/rollback are retained. Main dirty worktree,
historical evidence, owner data and running gateway are untouched.

Exactly next operation: **separate operational readiness — authorized synthetic
identity + credential renewal + active-session inventory + exact-binary canary**.
Do not run it automatically; no production deployment or owner acceptance now.

FUNCTIONAL_WARM_START=PASS_IN_TESTED_SCENARIO remains historical.
WHITELIST_WARM_START_READY=NO; ATTEMPT_CONSUMED=NO.
PUBLIC_RELEASE=NOT_RUN. REAL_RESTRICTED_NETWORK_FIELD=NOT_RUN.
