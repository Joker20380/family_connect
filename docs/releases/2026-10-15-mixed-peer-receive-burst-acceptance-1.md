# MIXED-PEER-RECEIVE-BURST-ACCEPTANCE-1

**RESULT: PARTIAL — CLIENT_RECEIVE_BURST_FIXED_LOCALLY;
MIXED_BIDIRECTIONAL_BURST_ACCEPTANCE=FAIL.**

The new client with async writer is wire-compatible with the exact old gateway
source. However, a correct old peer produces finite19/20-message bursts which
closed the new client receive queue16. A minimal64-message bounded receive reserve
fixes that client-side defect, including the40-message stress case, without losing
the async writer, changing timers/windows or dropping frames.

Before declaring client-only readiness, a separate positive reverse gate was
declared and run. The real new peer also produces valid19/20/40-message batches
that close the **unchanged old gateway receiver queue16**. This remains a failed
supported-load gate, not an accepted overload guard. NEW/NEW PASS does not remove
this dependency. **CLIENT_ONLY_DEVICE_TRIAL_READY=NO** for this complete envelope.
No gateway change, signing, installation or live action is performed.

## Source identities and scope

Input review: ba89a5fcdd3442474ae900abe63050e365f2f3d2.
[Package / reproduction](../../research/mixed-peer-burst-20261015/README.md),
[source manifest](../../research/mixed-peer-burst-20261015/source-manifest.json),
[actual compiled inputs](../../research/mixed-peer-burst-20261015/compiled-source-bindings.json),
[source delta](../../research/mixed-peer-burst-20261015/source.patch),
[results](../../research/mixed-peer-burst-20261015/results/summary.json).

| Side / artifact | Identity |
| --- | --- |
| OLD_GATEWAY source |a4087e000fdbe674b72ede3a6c8822445c87c654 + delta7e7d408670a6ac6afa18e856beb8dcc0ca26a3b6f074e205d4dd25e62d78967b; preserved snapshot471d1d62e1385a9ffc5ff6a16a5a7e9fe043fae2 |
| Bound baseline binary, not executed here |21f0a0fdc27b50c00ea922f0b716516e2422aedf1b3797369718f7d00070509a |
| OLD_CLIENT cumulative inventory |a4d489079e3da0df7fdd01b7977962b20ddbbf8605fbf682a349703a88b916d5 |
| NEW before this correction |af315dce15e16c3b5d372dee4294192339443ac0cd79364748bd2f53c156be61 |
| NEW after,35-file Git-base-relative inventory |c2dc3dd860044b31696893244995cbc5cc8eb805ee34319df99cce085cf40d08 |
| Installed APK, not changed by this task |3c733d2fc3a0ec377143b668244a4c7d6619ff24abe024da4ee9bfe31d140513 |

Actual old/new Reliable and Family implementations compile in three independent
module namespaces in the same test executable. The only old-module source transform
is import/module-path substitution and a tagged test adapter.93 selected dependency
files are reverse-normalized and byte-compared with original inputs. OLD_GATEWAY
uses the published baseline, not root main, a generator, or a client-file replacement.
OLD_CLIENT is the retained a4d inventory; the final materializer verifies its recorded
overlay. NEW/NEW is explicitly the new shared carrier/Family implementation at both
ends, not a claim that a new gateway executable has been built or deployed.

This is source-level acceptance, **not FROZEN_BINARY_ACCEPTED**. No full seal audit,
historical B re-investigation, bootstrap/PKI redesign or production preflight.

## Supported envelope and real frame generation

The [contract](../../research/mixed-peer-burst-20261015/CONTRACT.md) was fixed before
the primary run: supported bursts8/16/19/20; a separate40-message stress case must
also resume. The reverse positive gate applies that same contract, declared before
its execution rather than reclassifying a failure afterwards.

The fixture performs a normal handshake and warm bidirectional exchange. It then
captures one direction of the real peer SendContext, while the opposite direction
continues. Each peer sends at most8 outstanding unique DATA, using unchanged default
send/receive windows8/16, payload16384, RTO1s, retries8, MaxAge20s and2s send budget.
ACKs are emitted by actual receive/consume processing. Larger groups include actual
timer retransmissions, never invented headers or unsupported unique DATA beyond
the window. Captured frame lists are bounded to64; capture wait is bounded to6s
and the whole case context to15s. No provider connection or room is opened.

The adapter calls production telemost.New/deliver/Recv after the reassembly boundary.
It replaces only provider/wire delivery with bounded accumulation. Selected frames
are released in one tight loop, without Gosched, per-frame ACK waits or consumer
gates in the principal burst. Remaining frames form a separately recorded batch
after the first queue drains. This is a bounded jitter/coalescing model, not a
claim to reproduce Pion/SFU timing or historical B payloads.

Example primary before composition:19 =6 DATA +13 ACK,20 =6 DATA +14 ACK;
40 =16 DATA transmissions +24 ACK, with8 repeated DATA from actual peer retries.
Reverse19 also arises as7 DATA +12 ACK (some race runs8+11); all from the actual
new sender. No mixed epochs or cross-session frame synthesis. Exact compositions,
epoch-pair counts, unique DATA, durations and queue snapshots are published in
[observations](../../research/mixed-peer-burst-20261015/results/observations.json).

Primary after release durations across normal/race/multicore observations were
1,728–268,453 ns; no assertion requires precisely2ms. GOMAXPROCS1 deliberately
exercises coalesced scheduling; a fixed GOMAXPROCS4 run is separate. The old queue
fails even on the measured multicore runs. Sampled queue high-water is direct
len/cap observation, not Flow.buffered or a post-cleanup inference. Enqueue-return,
Recv-return, close and progress facts are distinguished; sampled high-water is not
claimed to capture every transient interleaving.

## Before / after matrix

Each final core matrix runs normal1 and race3. After also runs multicore normal1.
No retry-until-pass. Initial before/after logs remain private with hashes in the
summary; SACK/held-cleanup strengthening was then run on both versions. The later
sustained and reverse gates are separate fixed batches, not replacement workloads.

| Version pair / receiver | Normal + real Family/TLS | Before8/16 | Before19/20/40 | After8/16/19/20/40 |
| --- | --- | --- | --- | --- |
| NEW_CLIENT receives OLD_GATEWAY |PASS |PASS |FAIL RECEIVE_QUEUE_FULL |PASS |
| OLD_CLIENT receives OLD_GATEWAY |PASS |PASS |FAIL RECEIVE_QUEUE_FULL |8/16 PASS;19/20/40 FAIL; unchanged control |
| NEW_CLIENT receives NEW_GATEWAY |PASS |PASS |FAIL RECEIVE_QUEUE_FULL |PASS |
| OLD_GATEWAY receives NEW_CLIENT, reverse positive gate |Normal/TLS PASS separately |— |— |8/16 PASS;19/20/40 FAIL RECEIVE_QUEUE_FULL |

The OLD/OLD characterization branch records its carrier failure rather than
failing the entire harness invocation. It does **not** count as a successful burst.
The reverse positive gate genuinely returns nonzero in normal, race and multicore.
All three race repetitions with19/20/40 failures are retained. No ErrBackpressure replaces
the carrier terminal in these failing cases; the close source is RECEIVE_QUEUE_FULL.

For the corrected client receive direction, success requires exact payload/order,
ACK/control advancement, full peer-window release and subsequent duplex exchanges.
Slow upper consumption is delayed until a whole peer window has arrived, then
resumes. A separate short outgoing SendContext gate confirms receive progress while
the writer is blocked. An actual reordered peer DATA produces SACK, gap closure,
ordered delivery and a reopened sender window for all three version pairs.

Fresh and A→Close→B cases pass on the corrected receiving client. The held A-close
case keeps the old endpoint cleanup return blocked while B works. The mixed adapter
rejects calls against a closed A; releasing A cleanup does not terminate B. This
adapter check is not evidence that every late production callback is refused.
The unchanged earlier async regression separately invokes actual old Session.deliver
after close and verifies isolation from the new queue. These are real carrier/
Reliable objects, not Android JNI callbacks. Existing production ownership/handoff
fixtures run separately. Adapter calls return to zero after bounded cleanup.

## Minimal correction and resource contract

Only **carrier/telemost/session.go** changes product bytes: a named fixed
receiveQueueSize64 replaces16. The already implemented async writer is byte-preserved.
The64 bound covers the tested40-message finite batch plus24 slots of transient
reserve; this is an explicit tested envelope, not a proof of arbitrary traffic
admission. It is not a16→256 guess or a protocol/window/timeout increase.

At most64 complete messages ×64KiB =4MiB retained payload per carrier queue,
compared with the previous1MiB bound. Slice/channel/diagnostic metadata and existing
reassembly, Reliable, TLS and WebRTC buffers are additional, not hidden in this
number. No extra workers, per-frame goroutines, callback waits, silent drops or
unbounded queue growth are introduced. Existing max-message/reassembly checks
remain. This capacity applies to each newly constructed carrier, including bootstrap/
seed and dedicated callers; it increases their per-session reserve too. Global
concurrency policy is unchanged; Android peak RSS is not measured here.

A unit test admits64 distinct maximum-sized messages and confirms observable
failure on the65th. Close and parent cancellation of a full, still-live queue finish
through cleanupDone. Existing first-failure/overflow tests still fail closed.
The old unpaced ACK-replay characterization remains separate from positive load.

**Sustained real-peer overload is separate:** block the receiving consumer beyond
the finite hold envelope, leave the old sender on its normal timers, and inject no
replays. Across normal1/race3/multicore1,56 actual retransmissions accumulate until
queue64 closes with RECEIVE_QUEUE_FULL at8.302–8.695s; the peer records remote_reset.
Bounded cleanup completes. This is the allowed sustained-overload guard, not the
criterion used to pass19/20/40 with an active consumer.

The only old async regression edits are two exact capacity assertions16→64. Its
DATA/ACK progress, workload, deadline, coalescing and worker assertions are unchanged.
No ownership, generation, authentication, revocation, Family/TLS wire, Mux, retry,
timer or server-policy implementation is modified. The source README is brought
in line with64 carrier messages and the already present three-worker async design.

## Why client-only readiness remains blocked

Correct new-client output can be accumulated by the transport into19/20 messages
before the old gateway consumer runs. OLD_GATEWAY has its own independent queue16;
enlarging the client receive reserve cannot change that remote allocation. Its
source-level release test fails before the upper consumer can recover the overflow.
The sender has no protocol credit for remote carrier queue slots: Reliability ACKs
describe its own DATA window, not a promise that all queued ACK/DATA/retransmission
carrier messages fit the remote16-slot callback queue.

Guaranteeing this reverse supported envelope therefore needs an old-receiver-side
correction or another explicitly designed/verified constraint. It cannot be inferred
from NEW/NEW or achieved by the client receive fix alone. Pacing/window/protocol
changes to conceal the boundary are not introduced. No baseline executable/config
is changed or rebuilt here. The local client patch is retained, but a client-only
device trial is **not promoted to ready** on this acceptance result.

## Regression and local build evidence

| Check | Observed result |
| --- | --- |
| Existing seven-package async/Reliable/Family/Mux/ownership/diagnostics suites |154 normal PASS;462 race PASS;0 race reports |
| Existing real Broker/Family-TLS handoff + diagnostic runner |20 normal /60 race PASS |
| Supplemental max-size/full-live-queue Close/cancel tests |2 normal /6 race PASS |
| JNI/native build |normal,fc_owner_diagnostic,fc_messenger_lab arm64 PASS; Java/JNI signatures PASS |
| Full researchProvisioning assemble/JVM |PASS, newly built normal library embedded;5+3+2 JVM tests,0 failures |
| DEVICE_TESTS / FROZEN_BINARY_ACCEPTED |NOT_RUN / NOT_CLAIMED |

Full regression logs predate the supplemental full-live-queue cancellation function;
that function and max-size test are additionally run in their own normal1/race3 batch.
The final published test source contains both. Product bytes do not change between
these batches. No build failure or runtime failure is hidden by repeating a suite.
Disk-backed TMPDIR and Java tmpdir are used from the start; no old capsules removed.

| New local artifact | SHA256 |
| --- | --- |
| Normal arm64 native |253e0e15f38223288571d3e682f6876269aa9c6d1c0c5157588ed8287ba6f3a3 |
| Unsigned researchProvisioning APK |cc5b883395c59d2f76f4cf8ce1d787fa764c1fac2936c9148f9876697d2c5013 |
| Embedded native |Exact match to the newly compiled normal library |

These are private unsigned build outputs, not release/accepted artifacts. The
previous unsigned async-writer artifact and installed signed APK are preserved.
The publication commit SHA is not a frozen source SHA or an installed build identity.

## End state

LIVE_ACTIONS=0: no device/gateway SSH/ADB, CONNECT, export, native poll, provider,
room, credential maintenance, signing, install, deployment, restart or release.
Only local tests/builds and GitHub review publication occur. Frozen snapshots,
earlier reports and original dirty worktree remain unchanged. No raw owner evidence,
real identifiers, private keys or APK are published; test trace tags are aliased.

HISTORICAL_B_CAUSAL_BINDING remains NOT_PROVEN. The finite burst is not a replay B.
The old single smoke remains PASS; latest reconnect acceptance remains FAIL.
Supervisor acceptance is not closed. Remaining boundaries are the old gateway
reverse receive guard, real provider/Pion scheduling and device/native runtime.
No live retry or server update follows this report automatically.
