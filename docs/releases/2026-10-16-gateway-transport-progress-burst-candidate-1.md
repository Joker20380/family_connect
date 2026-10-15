# GATEWAY-TRANSPORT-PROGRESS-BURST-CANDIDATE-1

## Result and scope

**RESULT: LOCAL_GATEWAY_CANDIDATE_PREPARED_AND_VERIFIED**, with explicit inherited
server-suite failures and installed-client limitations; not an all-tests-green claim.
**PAIR_LOCAL_ACCEPTANCE=PASS for the required new-pair supported envelope.**
**GATEWAY_FIRST_TRANSITION_READY=YES_FOR_SEPARATELY_AUTHORIZED_CONTROLLED_TRIAL**,
conditional on fresh environment/session/outage checks and acceptance of the
intermediate old-client limits below. No deployment has occurred.

Input review:1521981f2ca6078e468c014507b7d968a8aacbe9.
[Package and commands](../../research/gateway-transport-progress-20261016/README.md),
[source manifest](../../research/gateway-transport-progress-20261016/source-manifest.json),
[three-file patch](../../research/gateway-transport-progress-20261016/source.patch),
[results](../../research/gateway-transport-progress-20261016/results/summary.json),
[observations](../../research/gateway-transport-progress-20261016/results/observations.json),
[resource contract](../../research/gateway-transport-progress-20261016/RESOURCE-CONTRACT.md),
[future rollout/rollback](../../research/gateway-transport-progress-20261016/RUNBOOK.md).

## Exact server derivative, not client NEW/NEW

| Identity | Recorded value |
| --- | --- |
| Preserved production baseline binary |21f0a0fdc27b50c00ea922f0b716516e2422aedf1b3797369718f7d00070509a |
| Baseline source base |a4087e000fdbe674b72ede3a6c8822445c87c654 |
| Baseline source delta |7e7d408670a6ac6afa18e856beb8dcc0ca26a3b6f074e205d4dd25e62d78967b |
| Preserved baseline snapshot |471d1d62e1385a9ffc5ff6a16a5a7e9fe043fae2 |
| Candidate three-file patch SHA256 |36c7c1dfadfbe14f0a92d5755ebae103adbc65f9db988396a893eeb91f35a8d9 |
| Candidate226-file carrier inventory digest |722746429539a1307d693ce6fcc83579a842d3f1c549a626a36676a6d665c42e |
| Candidate executable SHA256 |a537257162348afc35b1ebc08755d8c5dc1cd90e74c49e3987fb3eb81885e61f |
| C_NEW cumulative inventory, unchanged |c2dc3dd860044b31696893244995cbc5cc8eb805ee34319df99cce085cf40d08 |
| C_INSTALLED cumulative inventory |a4d489079e3da0df7fdd01b7977962b20ddbbf8605fbf682a349703a88b916d5 |

The complete published baseline carrier subtree is checked against its retained
source inventory. Only three product files change:

- `carrier/reliablestream/stream.go`: the previously verified bounded async writer.
- `carrier/reliablestream/protocol.go`: its observable ErrBackpressure declaration.
- `carrier/telemost/session.go`: a fixed receiveQueueSize64 instead of16.

Reliable preimages are byte-identical to the pre-async client files (hash guarded).
Telemost is NOT identical: baseline retains its server-specific signalingReadFailure
field. The semantic port preserves that field and every other baseline behavior,
changing only the named constant/channel allocation. No client carrier tree, Android
ownership, JNI/Java, supervisor recovery, seed acceptance bridge, trigger, broker,
lease, management/current4h or security policy is copied into the derivative.

The materializer reproduces all226 final file hashes. Candidate inventory is SHA256
of the canonical sorted compact JSON path→hash map; patch and changed files are
published separately. Publication commit is not an APK source SHA or a frozen binary
identity. Source/build inputs are isolated; previous snapshots and dirty root stay intact.

## Actual four-source tests

The existing test transport is reused after reassembly. Real production deliver/Recv,
Reliable and Family/TLS execute. A fourth independently materialized namespace imports
G_CANDIDATE from its server derivative; it is not two client modules called NEW/NEW.
124 compiler-selected source inputs are byte-compared after reversing only declared
module/import substitutions. The only adapter is the prior tagged post-reassembly
carrier adapter; no behavioural transform of peer algorithms is permitted.

Source pairs: C_NEW/G_CANDIDATE and C_INSTALLED/G_CANDIDATE, in both receiving
directions. Previous unchanged C_NEW/G_BASELINE reverse19/20/40 FAIL and
C_INSTALLED/G_BASELINE normal PASS/large-burst limits remain control receipts in
[the preceding report](2026-10-15-mixed-peer-receive-burst-acceptance-1.md).
They were not rerun wholesale or relabelled as successful overload guards.

Fixed main batch: normal1, race3, multicore1. Real-peer capture max64 messages,
wait max6seconds, case context15seconds; original windows8/16, RTO/retries/timeouts
unchanged. Finite8/16/19/20 are supported;40 is a separate positive stress gate.
Frames include actual ACK/OPEN/DATA and timer retransmissions, <=8 unique outstanding
DATA from each peer. Dense release has no per-frame scheduler yield or ACK wait.
Actual intervals/compositions, queue enqueue/dequeue/HWM and closes are published.
HWM is sampled at adapter delivery and is not an exact scheduler-wide maximum.

| Required/check scope | Observed outcome |
| --- | --- |
| C_NEW receives G_CANDIDATE, normal/8/16/19/20/40 |PASS in normal1/race3/multicore1 |
| G_CANDIDATE receives C_NEW, same envelope |PASS in all fixed modes |
| Actual Family/TLS with C_NEW/G_CANDIDATE |PASS, exact duplex1/4096/16384/65536 bytes |
| C_INSTALLED/G_CANDIDATE normal, exact steady duplex,8/16 |PASS in both directions/all modes |
| Actual Family/TLS with C_INSTALLED/G_CANDIDATE |PASS; not a claim of old-client dense-burst robustness |
| C_INSTALLED receives19/20/40 |KNOWN_OLD_RECEIVER_LIMIT: FAIL RECEIVE_QUEUE_FULL, not positive acceptance |
| G_CANDIDATE receives C_INSTALLED19/20/40 |PASS |
| Candidate outbound SendContext stalled with inbound20 |PASS; processing resumes, exact DATA/window/ACK progress |
| Slow upper consumer, real SACK/gap/order and later duplex |PASS for tested pairs/directions |
| Fresh and A→Close→B, normal/held old cleanup |PASS; old adapter handles/cleanup do not close B |
| Full receive queue Close/cancel, bounded writer cleanup |See resource/extra regression receipts below |

Family/TLS exact duplex and raw Reliable burst cases are separate checks. This is
not execution of the frozen baseline executable and not provider/Pion/TLS end-to-end
burst acceptance. Held cleanup is the adapter endpoint-return gate, not proof of every
real WebRTC worker or JNI lifecycle. Existing actual Telemost/async regressions run
separately; no Android/native/JVM suites are repeated for unchanged client bytes.

## Failures retained and classified

The extended OutboundStall test also gates C_INSTALLED own outgoing SendContext.
Its synchronous old run loop stops dequeue and hits the fixture prefix-dequeued
bound. The aggregate main command therefore returns nonzero in every mode; this
extension is not silently removed or counted PASS. A separate fixed paired control
runs the SAME workload/assertions against G_BASELINE and G_CANDIDATE: both fail
normal1/race3/multicore1 at that boundary. It is the known old-sender progress limit,
not an observed new gateway regression. Ordinary installed-client compatibility and
gateway-side async progress are distinct successful gates.

Sustained overload is separately generated by a real new peer, with its receiving
candidate consumer held; no manually replayed frames.56 real retransmissions fill
queue64, producing RECEIVE_QUEUE_FULL in8.388–8.599seconds. Some immediate peer
snapshots have not yet recorded remote_reset; later cleanup completes. No late
snapshot is used to infer earlier occupancy. This is SUSTAINED_OVERLOAD_GUARD,
not the criterion for passing supported bursts. No ErrBackpressure replaces the
finite-burst overflow under a different terminal label.

### Same server regression selection

Seven full package selections: Reliable, Telemost, Family/TLS, Mux/tcpforward,
bootstrap, roombroker and cmd/bootstrap-broker. Baseline and candidate use the SAME
normal1/race3/multicore1 commands and disposable ProductStore-issued fixtures.
Synthetic keys remain private. Live-test opt-ins are removed from the environment.

| Source/suite | Normal1 pass/fail/skip | Race3 pass/fail/skip | Multicore1 pass/fail/skip |
| --- | --- | --- | --- |
| baseline | 206/3/6 | 613/14/18 | 206/3/6 |
| candidate | 206/3/6 | 615/12/18 | 206/3/6 |
| progress-resource | 12/0/0 | 36/0/0 | 12/0/0 |

Counts are top-level test outcomes; race3 includes all three repetitions. Full
baseline/candidate commands exit1 in every mode. Their failing subtest sets have
NO candidate-only member in the same mode. Race failure frequencies differ; this
is not claimed as a bug fix or deterministic equivalence of those old assertions.
Progress/resource commands all exit0 (12 normal /36 race /12 multicore). No race
detector report or panic/timeout was recorded. Timestamp supplemental1/3/1 passes
on BOTH versions. Positive mixed gates pass; the aggregate mixed command remains
nonzero only for the separately attributed installed-client outbound-stall extension.

Inherited assertion families are preserved: negative-auth exchange diagnostic counts,
seed error-classification expectations, and race-sensitive busy-exchange/Mux deadlines
where recorded. Exact failing subtests/reasons/counts are published; no assertion or
policy was changed to turn the full suites green. A missing relative timestamp vector
in the carrier-only snapshot initially fails on both sides. A separate fixed check
supplies the existing vector SHA256 a542d50e3b3645b9cd1813619ffb075fd3777d2a2473bd079d05ef83a8b2aca2
to isolated overlays of BOTH sources; normal1/race3/multicore1 passes. Initial failures
remain in the receipts. Skipped live/private fixture tests are listed, not counted PASS.

## Resource and security limits

One additional Reliable writer per stream; finite pending34 jobs, no DATA drop,
ACK/OPEN coalescing and explicit ErrBackpressure. Carrier queue64 is4MiB maximum
payload, not total session RSS. The existing send/reassembly/window/trace/TLS/Pion/Mux
buffers remain separate. The detailed resource contract describes their scopes and
what has NOT been bounded by this task.

Broker outstanding32 bounds its setups, including worker-owned closing setups; it
does NOT include seeds/pre-authentication/HTTP. This entrypoint has one seed or two
during existing overlap, with one bootstrap lease/exchange per seed sharing that
carrier.32 dedicated +2 seed queues gives an illustrative136MiB queue-payload maximum
under that topology, not a fleet/process RSS guarantee. Live occupancy is unmeasured.

A direct resource test observes cleanupDone while4MiB remains in a full closed queue
whose Session is still referenced. Close did not promise to drain it in baseline
queue16 either. Finite retained references, object reclamation and actual RSS are
separate facts; no zero-memory-on-Close claim or speculative product drain is added.
Reader/writer joining, bounded cancellation and session-generation isolation are
checked in the fixtures. No new quotas or unbounded worker mechanism is introduced.

Authorization/revocation/expiry/directory, single-holder ChallengeAfterCleanup,
lease security/deadlines and fail-closed code are byte-preserved. Tests cover their
existing valid/negative paths, subject to the explicitly non-green baseline assertions
above. No new security/policy failure family is inferred merely from changed race
frequencies, and source equality is not substituted for live acceptance.

## Real executable build

Entrypoint: `./cmd/bootstrap-broker`, not the mixed test executable.
Command: `go build -trimpath -buildvcs=false -o "$OUT/bootstrap-broker-transport-progress" ./cmd/bootstrap-broker`.
Go1.26.1, linux/amd64 GOAMD64=v1, CGO_ENABLED=1; no research/seedacceptance tags,
no new ldflags, and exact dependency versions/checksums equal the saved baseline.
No test adapters appear in product source/compiler selection.

Explicit build metadata delta: buildvcs=false for the manifest-addressed projection;
baseline metadata records a4087e… with vcs.modified=true. No fake baseline Git identity
is embedded. Baseline flags are recovered from its retained binary build metadata;
its external C compiler version is not recorded. Current gcc15.2 is recorded; both
ELFs require the same libc.so.6 / GLIBC versions through2.34 and interpreter class.
Candidate size17711831 bytes. Build metadata/ABI receipts and source identity bind
this private artifact. The executable is NOT launched with fabricated credentials.
**GATEWAY_BUILD_VERIFIED=PASS; LIVE_GATEWAY_ACCEPTANCE=NOT_RUN.**

## Preserved client and next boundary

C_NEW35-file inventory remains unchanged. The existing unsigned APK
cc5b883395c59d2f76f4cf8ce1d787fa764c1fac2936c9148f9876697d2c5013 and normal native
253e0e15f38223288571d3e682f6876269aa9c6d1c0c5157588ed8287ba6f3a3 are rehashed;
embedded native matches. No rebuild/sign/install. Historically installed signed APK
3c733d2fc3a0ec377143b668244a4c7d6619ff24abe024da4ee9bfe31d140513 is untouched;
no new device readback is claimed.

The future runbook first checks current security/runtime/session state, replaces ONLY
the gateway executable in an approved outage, verifies loaded identity/strict TLS/
seed/current runtime-bound directory, then separately updates the client and performs
owner reconnect acceptance. Management/PKI/configuration are not rollout deltas.
Executable rollback never lowers CRL/floors, restores credentials or copies an old
directory. Intermediate C_INSTALLED limits remain explicit. No automatic rollout.

**LIVE_ACTIONS=0**: no SSH/ADB, provider rooms/probes, renewal/signing, deployments,
service starts/restarts, configuration changes, APK installs, CONNECT or export.
Local builds/tests and safe review Git publication only. No executable/APK/raw owner
export/keys are published. Previous smoke PASS and reconnect acceptance FAIL remain;
DEVICE_ACCEPTANCE=NOT_RUN_FOR_NEW_PAIR, HISTORICAL_B_CAUSAL_BINDING=NOT_PROVEN.
Supervisor acceptance remains open. A local candidate is not updated production.
