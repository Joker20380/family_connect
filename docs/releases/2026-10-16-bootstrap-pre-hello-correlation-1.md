# BOOTSTRAP-PRE-HELLO-CORRELATION-1

16 October2026. **RESULT=LOCAL_DIAGNOSTICS_READY**.
Implemented diagnostic derivative of retained C_NEW; locally checked through real
lease/Family/TLS/Broker, native stats and ordinary Java bundle serialization.
Unsigned APK only. **LIVE_ACTIONS=0; HISTORICAL_A_CAUSE=NOT_PROVEN**.
This is neither a startup fix nor NEW_PAIR_DEVICE_ACCEPTED.

Input review: `a63d446acc788d791d76fa938a8575d115b5e411`.
[Historical device result](2026-10-16-new-pair-owner-reconnect-acceptance-1.md)
is unchanged: A HELLO_RECEIVE/IO_DEADLINE preceded cleanup; server challenge timeout
was temporally aligned only. No exact historical owner/server binding is manufactured.
[Source/tests/results](../../research/bootstrap-pre-hello-20261016/README.md),
[separate-trial runbook](../../research/bootstrap-pre-hello-20261016/RUNBOOK.md).

## Exact inputs and outputs

| Identity | SHA256 |
|---|---|
| Investigated signed C_NEW, not final phone APK | `28772ccb111623741dc12f14e387f1535095502748165ab87d51fdde751c004b` |
| C_NEW native | `253e0e15f38223288571d3e682f6876269aa9c6d1c0c5157588ed8287ba6f3a3` |
| C_NEW cumulative source inventory | `c2dc3dd860044b31696893244995cbc5cc8eb805ee34319df99cce085cf40d08` |
| Last observed phone after prior rollback; not re-read here | `3c733d2fc3a0ec377143b668244a4c7d6619ff24abe024da4ee9bfe31d140513` |
| Existing gateway executable, unchanged retained bytes | `a537257162348afc35b1ebc08755d8c5dc1cd90e74c49e3987fb3eb81885e61f` |
| **Final diagnostic unsigned APK**,55,986,124 bytes | `b2a4b76b3218ec06f3409154a1a14f71bf4feff3206be3282c25852eabdd35ca` |
| **Final normal/embedded native** | `be70a66ccc2bcbf0478915fd414c32de3bedb2a0ae0c3222a53e65eebd0a92b2` |
| **Final cumulative source inventory** | `b36c4a21ee6cf04acb192a0e6d140fa565b3e5ae75f6fc8d028d029c3152781d` |

Local final APK:
`state-client-build/bootstrap-pre-hello-correlation-1/gradle-native-export-final/android/app/outputs/apk/researchProvisioning/app-researchProvisioning-unsigned.apk`.
Not uploaded, signed, installed or released. Existing signed APKs remain preserved.
Package `com.familyconnect.app.friends`, versionCode84,
versionName `0.1.18-research84-provisioning-seam`, minSDK31/target35 unchanged.
AndroidManifest.xml is byte-identical to C_NEW unsigned APK, including permissions;
alignment16KiB passes. Signature verification fails as expected for an unsigned APK
(`Missing META-INF/MANIFEST.MF`), not a new signing key. Both embedded provenance
assets contain the final cumulative inventory; embedded native matches the build.
No release assets/catalog/version workaround.

## Necessary source binding, not a new global audit

Retained C_NEW full source is the parent, not dirty root main or the rolled-back
client. Its existing35-file inventory remains the base; final inventory has39 files
(protocol.go now differs from the original base, plus three newly added test/resource files).
Eight-file delta: five diagnostic runtime files, two tests and one local fixture
resource. All other cumulative entries retain their previous hashes. `apply.py`
successfully reconstructs the derivative with guarded input/output hashes.

[Exact bindings](../../research/bootstrap-pre-hello-20261016/exact-bindings.json)
cover client `bootstrap/carrier.go`, `bootstrap/protocol.go`, startup recorder,
native main/bridge/startup_owner/chat_owner, actual Java Diagnostics/RestrictedStartup/
DiagnosticRing, native caller and researchProvisioning configuration. Server
`roombroker/ownership.go`, `cmd/bootstrap-broker/ownership.go` and flag entrypoint
are bound to the retained actual gateway derivative. Client/server protocol.go is
identical before this client diagnostic delta; carrier/Family source differences
are retained, not silently replaced with a common baseline.

Local integration uses two module namespaces, each copied from its own retained
source. Only gateway imports are renamed for simultaneous linking. Real server
ServeCarrier/OpenServer, Family TLS and Broker execute from that gateway derivative.
The unmodified gateway executable is hash-checked locally, **not rebuilt/deployed**;
`cmd/bootstrap-broker` is compiled only as a local test program. No fresh live
invocation/readiness claim is made; the previous report's invocation is historical.

## Early exchange record and export

After successful `connectLease`, before Family open and requestTransport/HELLO:
`startupdiag.Bootstrap(ctx, hex.EncodeToString(session.server[:]))` records the
existing `sessiontrace.Tag` transformation. Server OpenServer passes that same
server lease nonce to `roombroker.WithExchange`. The real-lease tests prove equality;
they do not assign the same synthetic tag to both endpoints.

`bootstrap_exchanges[]` retains at most4 entries with `bootstrap_exchange_tag` and
separate `family_authenticated`. The latter is set only after successful client
Family open, not by obtaining a nonce. Neither field proves authorization or a
healthy dedicated session. No raw nonce, key, profile, room URL or personal identity
is exported. Dedicated `session_tag` remains a separate, unchanged field.

An exchange context handle contains its recorder owner/index/tag; concurrent
exchanges have distinct entries, chat/new attempts have distinct recorders.
`bootstrap_exchanges_dropped` counts overflow; a first failure's
`observation.bootstrap_exchange_tag` remains available independently of that list.
Snapshots deep-copy it. Late auth, completion or cleanup cannot replace another
attempt's tag or the original failure/observation. Legacy missing fields and
historical UNKNOWN/IO_DEADLINE remain unchanged.

Actual native `retainStartup`/`startupStats` is exercised in a local package-name-only
adapter against the real failed bootstrap context, including rejection of a wrong
attempt number. Its resulting JSON becomes the Java test resource. The runtime
chain is `startupStats` → existing JNI stats JSON → `Diagnostics.nativeStats` →
shared `nativeStartup` parsing branch → startupStats/project → ring/incident →
ordinary exportRecord/exportBytes. The only Diagnostics refactor extracts its
existing parsing branch for direct JVM coverage; no second exporter/reader exists.
The same normal native is linked into the assembled researchProvisioning APK.

Java retains only validated64-hex tags and boolean auth facts, caps entries at4,
counts omitted projection entries, rejects arbitrary strings/extra private fields,
and preserves observation/local_stop. Existing limits remain256KiB per record,
525312 bytes per bundle. Incident and later connection ring remain separate; old
attempts and late cancellation cannot replace the saved failed attempt.
Device AtomicFile/share UI and live support export are **NOT_RUN**; this task tests
their ordinary projection/serialization path locally, not an Android live episode.

## Local cases and results

Final correlation matrix: fixed normal1 + race3, all pass.17 leaf cases per execution:
nine lease scenarios, real concurrent exchanges, recorder isolation/bound, five
capture lifecycle modes, actual asynchronous output failure. Deadline2s is a test
context only; production ExchangeTimeout remains120s.

| Case | Observed assertion |
|---|---|
| A no holder | Real lease/TLS → authenticated → grant/HELLO; early tag equals Exchange, dedicated tag differs |
| B same-identity ACTIVE | Real first bootstrap creates/claims holder, gateway active callback; requester RUNNING with early tag before HELLO; deadline/failure matches wait and holder generation |
| C holder exits before deadline | Real gateway Run returns, cleanup/release; wait_end then new grant/HELLO; generation changes, old release belongs to old holder |
| D other identity / multiple | Independently authenticated other device is not linked to old holder; two concurrent real leases in one recorder retain distinct tags/grants/generations |
| E invalid Family auth | Actual unrelated CA fails TLS; early tag remains, auth=false and no matching server authenticated event |
| F cancel/cleanup | First pre-HELLO observation/exchange unchanged after cleanup; late stop leaves success SUCCEEDED; nested/new attempts and snapshot copies isolated |
| G Java bundle | Actual native B JSON → normal parsing/projection → persisted incident/current ring → ordinary bundle; correct server wait/generation still join after serialization |
| H collector bounds/output | Disabled/expired do not record; limit marks Limited; admission unchanged; open failure and actual EFBIG flush failure retain no false complete footer |

Supplemental **only B** normal1/race3 executes the actual native export boundary
and native attempt guard; full old matrices are not repeated. Latest real fixture
receipt feeds the final assemble. Separate offline completeness test covers six
statuses; missing evidence never produces a "holder absent" conclusion.

Native normal, fc_owner_diagnostic and fc_messenger_lab compile/link pass, Java JNI
headers and C signature checks pass. Full researchProvisioning assemble passes with
the new normal library.12 targeted JVM tests pass: BootstrapCorrelation2,
StartupFidelity2, RestrictedStartup3, DiagnosticRing5. Not a full-suite-green claim.
No host/race old burst/13-module seal audit or hundreds of characterization repeats.

Preserved development outcomes, not hidden retries: first fixture used Exchange
for release and failed C; corrected to actual holder_exchange/generation (server
unchanged). A fixed normal1/race3 intermediate run then passed; subsequent final
matrix adds real parallel exchanges/output-failure coverage. Initial Gradle sandbox
socket denial is retained; authorized outside-sandbox run exposed Files.writeString
unavailable in Android's test compile surface. Only test code changed to Files.write.
Successful intermediate assemble remains local; the final rebuild packages the
actual-native-export receipt. No retry-until-pass or product-policy workaround.

## Safe end-to-end pre-HELLO example

From generated local fixtures only, not the owner export:

```text
client attempt=2 stage=HELLO_RECEIVE status=FAILED
bootstrap_exchange_tag=b21696d18cd0756ce7b577b1d95f466b904603720c93fafc98446b07691b2db9
family_authenticated=true
server wait Exchange=b21696d18cd0756ce7b577b1d95f466b904603720c93fafc98446b07691b2db9
holder_exchange=489d6b6f6d228b7a8c3ba965fac72c3c7bce42c8c4b300b49cc85f8f23351494
generation=677b0ea21122aa036630b482e450c827619778ed30e48c0e8384183931202956
holder_state=ACTIVE same_identity=true
holder dedicated trace session_tag=677b0ea21122aa036630b482e450c827619778ed30e48c0e8384183931202956
observation=FAMILY_RECEIVE/CLOSED_PIPE context=DEADLINE stop_at_observation=NONE
later local_stop=CLEANUP; wait_end=context_cancelled
holder_role=UNKNOWN
```

The latest race sample is CLOSED_PIPE with DEADLINE context; earlier samples include
IO_DEADLINE. Existing cause fidelity is preserved, not normalized to a preferred
code. This is a deadline-bounded HELLO wait, not a reproduction of historical A's
exact cause. Later server cancellation is not promoted to the first failure.
Exact waiting-on-holder evidence is established without guessing CHAT versus VPN.
ACTIVE does not prove a healthy remote client. Release events may lack Exchange
and instead carry holder_exchange/generation; local completion is not slot removal.

## Existing collector and observer limits

Unchanged `CaptureOwnership`/`OwnershipSnapshot`/`ExchangeEvent` and startup flag
`--research-admission-evidence` are reused. Maximum15min/512 events,250ms file flush,
new absolute exclusive0600 output. No new endpoint or live observer is created.
Disabled/expired snapshot may be empty and Limited=false; no exact dropped count
exists. Missing footer/gaps/written mismatch or asynchronous write error makes
capture incomplete even if events were retained in memory. Offline correlation
reports this explicitly and never concludes holder absence from missing trace.

Enabling this startup-only flag may require a new gateway process, destroying old
in-memory Broker state. Future trial must preserve accessible prior state, document
new invocation/conditions and independently establish the chat/holder premise.
No arbitrary DIRECT blocking/new identity. Success without the original premise
means NOT_REPRODUCED, not root cause or repair proven. The runbook authorizes no
observer activation, restart, signing, install, CONNECT or export now.

## Final result / publication

| Requested field | Result |
|---|---|
| RESULT | LOCAL_DIAGNOSTICS_READY |
| EXACT_CLIENT_AND_SERVER_BINDING | Retained C_NEW + actual gateway derivative; exact local lease join PASS |
| EARLY_EXCHANGE_TAG_BEFORE_HELLO | PASS, recorded before Family open/requestTransport; auth separately recorded |
| NORMAL_SUPPORT_EXPORT | PASS_LOCAL native-stats → real Java projection/incident/bundle; no live export |
| REQUESTER_TO_HOLDER_CORRELATION | PASS_LOCAL Exchange → wait → holder_exchange/generation → dedicated trace; role UNKNOWN |
| FIRST_FAILURE_PRESERVED | PASS_LOCAL before/after cancel and cleanup; old causes unchanged |
| SERVER_EXISTING_CAPTURE_REUSED | YES; zero server product byte/config changes; not assumed active in production |
| OBSERVER_LIMITS_AND_RESTART_EFFECT | Explicit15min/512, incomplete-output handling, new-process state loss |
| RUNTIME_POLICY_UNCHANGED | YES:120s, admission/ownership/wire/errors/retries/async writer/queue64/handoff unchanged |
| LOCAL_TESTS / BUILD_IDENTITIES | Fixed normal/race, JNI/native,12 JVM and full unsigned assemble PASS; hashes above |
| READY_FOR_SEPARATE_OBSERVED_TRIAL | Diagnostic prerequisite READY; live readiness/permissions/premise still required |
| HISTORICAL_A_CAUSE | NOT_PROVEN |
| LIVE_ACTIONS | 0 |

No fresh device state read: last observed rollback APK remains the recorded state,
not a claim of current connectivity. No historical A/B result, supervisor acceptance,
release/main/workflow/catalog or installed artifact is changed. No SSH/ADB, provider
session, credential maintenance, signing/install/rollback, CONNECT/export or gateway
restart/deployment/configuration operation occurred.

Review publication: `review/supervisor-state-20261015`, source/tests/results and
report/STATUS/PLAN/publication index only. Commit/push remote readback is recorded
in the task's final response; this report's Git commit identifies its exact contents.
APKs, private device exports and signing material are not published.
