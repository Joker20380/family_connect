# RECEIVE-QUEUE-STALL-REPRO-AND-FIX-1

**RESULT: REPRODUCED_PROGRESS_DEFECT_FIXED_LOCALLY.** A bounded outgoing-send stall
can stop incoming Reliable processing in the installed cumulative source. The same
regression passes after a two-file bounded writer correction. This occurs on fresh
sessions too, not only reconnect. **HISTORICAL_B_CAUSAL_BINDING=NOT_PROVEN**: the owner
trace lacks worker/queue observations and also contains an unpaced receive burst.
The patch is not presented as a proven cure for that historical burst or device B.

LIVE_ACTIONS=0. No SSH/ADB, CONNECT/export/native poll, signing/install, provider/room,
credential/server/current4h action, WS1011, deployment or release in this task.
Previous single-session smoke PASS remains; reconnect acceptance remains FAIL until
separately authorized device verification. Supervisor FAIL and C1/I1 NOT_PROVEN stay.

## Exact input and published delta

Input review: da8cd59cc910be13fe48931284ff6d19e75626cd.
[Research package / commands](../../research/receive-queue-stall-20261015/README.md),
[manifest](../../research/receive-queue-stall-20261015/source-manifest.json),
[patch](../../research/receive-queue-stall-20261015/source.patch),
[results](../../research/receive-queue-stall-20261015/results/summary.json).

| Identity | Value |
| --- | --- |
| Installed client APK, unchanged |3c733d2fc3a0ec377143b668244a4c7d6619ff24abe024da4ee9bfe31d140513 |
| Installed native, unchanged |2a974350c168913ca8a217d3fc73f452fdd709c3619d0c690abd5d884c54b88c |
| Input cumulative inventory |a4d489079e3da0df7fdd01b7977962b20ddbbf8605fbf682a349703a88b916d5 |
| Retained Git base |f5240994869826c6a28f59e58e38256c688cf6eb plus research84/handoff/diagnostic overlays |
| Baseline gateway, untouched |21f0a0fdc27b50c00ea922f0b716516e2422aedf1b3797369718f7d00070509a |
| New local cumulative inventory |af315dce15e16c3b5d372dee4294192339443ac0cd79364748bd2f53c156be61 |

The retained29-file cumulative overlay inventory was checked against its recorded
digest;12 receive-path/ownership files were bound to that overlay or exact base Git
objects. No1899-entry capsule audit or root-main substitution. Work is in a separate
derivative. The new hash-guarded apply.py invokes the existing cumulative materializer
and applies only declared files. Fresh reconstruction matches every32-file entry of
the new Git-base-relative inventory. These inventory digests are not Git source SHAs,
release identities, APK hashes or accepted candidates.

Product delta is only carrier/reliablestream/stream.go and protocol.go. One new
telemost/receive_stall_test.go is test-only. before/changed copies and source.patch
make review possible without editing frozen snapshots. Handoff/diagnostic patches,
old reports, signed APK, baseline executable and original dirty worktree are preserved.

## Retained B only: evidence and limits

The already copied support export has SHA256
3e830cfe8850aa4129da0c41e116ddba23a9aedbf40123d67a5dd54de5a49104.
Only ring.restricted_session for B and its previously matched server window are used.
The old incident, A snapshot and A server terminal are excluded. No new log query.
[Small safe projection](../../research/receive-queue-stall-20261015/results/b-retained-projection.json)
removes sender/message/user/support identifiers but retains bounded sequence/Flow data.

| Recorded B fact | Scope / interpretation |
| --- | --- |
| Startup |SUCCEEDED; dedicated READY and app CONNECTED before runtime failure |
| First local failure |19:53:16.918UTC, CARRIER/CLOSED/CARRIER_ERROR, RECEIVE_QUEUE_FULL |
| Last pre-failure Flow |19:53:16.236: send_base20/send_next28, receive_next29, pending8, buffered0, ACK base20/mask126, head_retries1 |
| Last pre-failure queued/written references |Both DATA sequence27 in that periodic snapshot; not a sendQueue depth or worker-state sample |
| Boundary tail |64 retained;1225 dropped;19:53:16.301–16.920UTC |
| Retained producer completions |19 carrier_message_completed:11 at16.917 and8 at16.918; matching reassembly events. DATA sequences32–38 appear among these control/data completions |
| Latest retained control |ACK received base28/mask1 at16.920, after the first close timestamp |
| Later Flow |19:53:18.236: send_base28/next34, receive_next31, pending6, buffered0; post-failure, not queue state at overflow |
| Server B |Previously bound session reached READY; RELIABLE_RETRY_EXHAUSTED19:53:25.631 is later recorded server termination, not initial client failure |

trace_dropped=0 applies to that lifecycle trace, not all surfaces. No queue depth,
run-stack or sendQueue blocked-duration snapshot exists at the failure. Flow.buffered
is the Reliable reorder buffer, not telemost.recvQueue. Missing consume/dequeue/DATA
acceptance in an incomplete boundary tail does not prove it never occurred. The
bunched completions are evidence of a burst, not proof that SendContext was blocked.
No historical error/category is rewritten; the old reconnect report remains intact.

## Real receive and reverse paths

1. telemost/msg.go reassembler.ingest completes a carrier message; callback reaches
   session.go deliverObserved. Its nonblocking enqueue targets a **per-Session**
   recvQueue(cap16); unavailable capacity emits RECEIVE_QUEUE_FULL and closes carrier.
2. ReliableStream.run reader goroutine calls endpoint.Recv, here real Session.Recv.
   It forwards to local incoming(cap1). One already-dequeued record can additionally
   be held in that reader while it waits for incoming capacity.
3. Main Reliable run decodes frames and invokes engine.input under its mutex. It
   processes ACK/SACK, bounded DATA windows and emits unbuffered stream.output only
   when a consumer is ready. A slow upper reader alone does not disable the select
   branches for incoming/control; finite windows eventually apply backpressure.
4. familysession.bridge has separate net.Pipe reader/writer workers. Receive writes
   can block on TLS consumer progress. TLS/Family Recv framing and then Mux.recvLoop
   consume the bytes; Mux stream writes have their own flow-control/consumer waits.
5. Reverse: engine ACK/DATA generation → transmit → endpoint.SendContext. Telemost
   encodes fragments/VP8 then enqueues sendQueue(cap256). Its writerLoop performs
   actual media/data-channel writes and pacing. A full sendQueue blocks SendContext
   until capacity, close or its supplied context ends.
6. **Before:** main Reliable run calls transmit synchronously for DATA, ACK and tick
   output. While SendContext waits, run cannot handle incoming or upper reads. Reader
   fills incoming, retains one record, then stops draining recvQueue. A bounded burst
   can hit the carrier overflow guard although a legitimate consumer exists.

Both carrier queues, Reliable engine/incoming/output, epochs and Mux session belong
to one constructed session. New does not inherit recvQueue. Process-wide native
ownerMu/chatMu/maps/coordinator manage leases/ownership, not a global receive queue.
The shared coordinator generation guards are unchanged. Low-level A→B tests show
late A delivery/Close cannot mutate the new queue; separate actual coordinator tests
cover handoff/security/stale leases. This is not execution of JNI callbacks on Android
or proof that every possible historical chat callback was harmless.

## Fixture, observed mechanism and before/after

The new fixture calls **production telemost.New/deliver/Recv and ReliableStream**.
Only the provider/wire layer is replaced after reassembly by an in-memory endpoint
with a channel gate around outgoing SendContext. It does not claim to execute the
production Pion writer, Family TLS or Mux in this particular regression. A separate
case fills real production SendContext/sendQueue256 and proves its cancellation.
Existing Family/TLS/Mux suites and actual Broker/coordinator fixtures run separately.

All original capacities/windows/timeouts are retained in before: recvQueue16,
incoming1, sendQueue256, Reliable windows8/16, payload16384, RTO1s, retries8,
MaxAge20s, per-send min(MaxAge,2s). No queue reduction, fake clock or new timeout.
Gates prove entry into outgoing SendContext; real Recv-return count, queue depth and
Reliable DATA/ACK counters demonstrate the downstream progress loss. Predicate waits
are bounded failure gates with scheduler yields, not sleeps assumed to mean progress.

| Case | Before | After |
| --- | --- | --- |
| Fresh bidirectional control |PASS |PASS |
| Slow upper consumer,8 DATA then resume |PASS: incoming continues |PASS, byte exact/in order |
| Gated outgoing send plus inbound DATA |FAIL: DataReceived does not advance despite real Recv returns |PASS: inbound DATA accepted/delivered while writer gated |
| Scheduled valid ACK/control bursts8/20/40 |8 stops ACK progress;20/40 reach recvQueue16 and RECEIVE_QUEUE_FULL |All processed, no receive overflow; same assertions/load |
| A close→B, ordinary and held A cleanup |B shows same progress defect as fresh session |B progresses; late A callback/cleanup does not change B queue |
| Actual production sendQueue256 blocked |Cancellation PASS |Cancellation PASS; capacities unchanged |
| Writer unblocked and repeated duplex payloads |Original failing progress gate retained |PASS:32 bidirectional rounds, sizes13/4096/16384, exact content/order |
| Persistent outgoing stall with128 bounded controls |Original progress assertion fails |Control progresses; existing2s send deadline terminates, workers joined |
| Eight-frame window consumed under gated writer |Supplemental test |Coalesced cumulative ACK frees entire peer window; byte order preserved |
| Unpaced8/20/40 completions |Not used as sole defect proof |Scheduling-dependent drain or observable RECEIVE_QUEUE_FULL; guard remains |

Before final normal1:2 top-level tests PASS,5 FAIL; race3:6 PASS,15 FAIL. After full
seven-package normal1:151 top-level PASS; race3:453 PASS,0 race reports. Two later
supplementary tests run normal1/race3 separately and PASS; their unchanged core
assertions are not used to replace a failing workload. Initial before/first-after
logs and final fixed logs are retained. No retry-until-pass or desired race proportion.
Public full-suite logs alias one address literal in an existing SSRF negative fixture
subtest name; no results are removed. Raw/private and published hashes are both
recorded in summary.json. The safety check caught this before staging/push.

The unpaced cases intentionally give no per-message consumer scheduling opportunity.
For20/40 a finite guard failure remains an allowed observed outcome, including on
corrected source. Such a burst is not unlimited flood, but can exceed the existing
carrier queue without any blocked transmit. **The correction therefore does not
establish that historical B is fixed.** It establishes a distinct, reproducible
progress defect under bounded outgoing backpressure, independent of reconnect.

## Minimal correction and resource contract

A single dedicated writer owns endpoint.SendContext. Main run dispatches bounded
immutable frame jobs and receives completion/error; incoming and upper delivery remain
selectable while a write blocks. DATA request completion still waits for actual
endpoint send completion, not merely enqueue. The attempt stamp is captured in the
main loop before asynchronous dispatch, avoiding access to an ACK-retired sent entry.

| Resource / invariant | Bound or preserved behavior |
| --- | --- |
| Additional workers |One writer per Stream, not one goroutine per frame |
| Writer channels |Unbuffered dispatch, one result slot, one active write |
| Pending jobs |Fixed capacity MaxWindow+2 =34; no growth/reallocation beyond it |
| Payload ownership |Existing bounded copies/immutable references; conservative pending payload ceiling34×32768 bytes, plus one active encode; no unlimited buffering |
| Controls |Latest ACK for same target supersedes older pending cumulative ACK; same-target OPEN is idempotently coalesced. DATA is never silently dropped/coalesced |
| Wire/order |Same framing, epochs, payloads and DATA order; newest cumulative ACK/SACK preserves advancement; dedicated regression checks window reopening |
| Saturation |Local ErrBackpressure if bounded pending queue cannot accept; existing carrier RECEIVE_QUEUE_FULL remains unchanged and tested |
| Timers |No duration/retry/window change. Tick generation and new DATA requests remain gated while writes are pending, as synchronous transmit previously prevented them |
| Close/cancel |Cancel writer context, join writer, then existing bounded best-effort RESET/endpoint close and reader join; no concurrent RESET and DATA sender |
| Diagnostics/policy |Primary carrier trace unchanged, no suppression of overflow; startup diagnostic, authorization, credential/revocation and ownership policy untouched |

The timeout/cancellation guarantees rely on the existing Endpoint.SendContext context
contract; the real telemost implementation is checked on its full-queue path. No new
cleanup RPC, writer service, protocol, telemetry platform, queue-size increase or
security/deadline exception is introduced. ACK supersession is explicit tested control
coalescing, not silent DATA loss. Pending-frame memory remains finite even when ACKs
release engine payload references before the writer drains its queue.

## Compatibility and Android build

Combined existing handoff/diagnostic/real Broker-Family-TLS runner: normal1 and race3
PASS (20/60 top-level tests). Server admission A–D invariants, chat-first/VPN-first,
opening/cancel/cleanup/stale generation/security cases and diagnostic receive/deadline
facts are preserved. Existing Reliable, telemost, Family session, Mux, trace, ownership
and startupdiag package tests pass. No host result is Android acceptance.

Native/JNI: normal, fc_owner_diagnostic and fc_messenger_lab arm64 libraries compile;
Java signatures and native bridge prototypes PASS. Full researchProvisioning assemble
and selected real variant JVM suites are checked with the newly built normal library.

| Local build identity | Result |
| --- | --- |
| Normal native SHA256 |1d80aa445c60453a5b38cb00eb71801b5340670fda4956cf846873efc93b24b5 |
| Unsigned researchProvisioning APK SHA256 |bba6a8fb3275f8d5a0b9a7f05d3bf1a4deb47ef4cac88c9d580b152b83656c76 |
| Embedded native |Exact match to the newly built normal library |
| Final Gradle / JVM |Assemble PASS; DiagnosticRing5 + RestrictedStartup3 + StartupFidelity2 =10/10 |
| DEVICE_TESTS / FROZEN_BINARY_ACCEPTED |NOT_RUN / NOT_CLAIMED |

Unexpected environment failure is preserved: initial Gradle assembled the APK, but
one synthetic export JVM test failed before its assertion with IOException: Disk
quota exceeded in /tmp. The same command was rerun once with only
JAVA_TOOL_OPTIONS=-Djava.io.tmpdir pointing to the private disk-backed fixture temp.
No source/test assertion/product settings changed. Final command PASS; APK hash stays
identical. No old capsules were removed to free quota. Initial log hash and repair
receipt are in results/summary.json. A README shell-quoting authoring error was repaired
before publication; no product execution resulted from those invalid command names.

## End state and remaining uncertainty

EXPECTED_BOUNDED_OVERLOAD_GUARD is preserved; REPRODUCED_PROGRESS_OR_LIFECYCLE_DEFECT
is the synchronous transmit progress defect, now fixed locally in fresh and reconnect
fixtures. HISTORICAL_B_CAUSAL_BINDING stays NOT_PROVEN. Specifically absent is a B
observation of main-run blocking location / outbound queue occupancy at overflow;
post-cleanup Flow does not supply it. The observed unpaced burst remains an alternative
mechanism not eliminated by this correction. No new live observer is installed here.

New artifacts are local unsigned build outputs only, not release/accepted candidates.
Previous installed client, baseline, dirty root worktree, archived source snapshots
and reports remain unchanged. Publication contains only source/test projection,
commands, safe evidence and docs. No automatic signing, installation, CONNECT, server
change or acceptance follows this local implementation result.
