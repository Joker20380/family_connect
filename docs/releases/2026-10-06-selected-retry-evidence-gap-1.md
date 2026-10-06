# SELECTED-RETRY-EVIDENCE-GAP-1 — PASS

2026-10-06. Offline evidence/instrumentation analysis only. PASS means the evidence
gap is explained, protocol-level conclusions are established, and the minimal local
instrumentation change has deterministic tests. It is NOT a new physical PASS.
OWNER-CONTROLLED-LOSS-1 remains FAIL/UNKNOWN, including its closeout exhaustion.
No ADB/SSH, fault arm, Telemost access, deployment, APK build/install, transport
tuning, credential refresh, publication or tester contact occurred in this task.

Session: `4b0d85ac8060b0e4fbc66c5645a865de7381a08f88794ae8bb715acd3505f3f8`.
Client→gateway DATA19; attempt1 sender3220232525/message842410499/fragment0 of1,
source RTP9063/timestamp1213693474. Attempt0 was dropped before carrier allocation.

## Scope, integrity and inventory

Protected original evidence root:
`state-client-build/field65-export16/owner-controlled-loss-1/`.
Analysis output root: `state-client-build/field65-export16/selected-retry-evidence-gap-1/`.
audit.py inventories all37 original files and validates every manifest-listed hash.
inventory.json contains each file's path, size, SHA256 and exact token matches;
timeline.json preserves timestamps, local event indices and supporting objects.
Original files, including derived boundaries, were not rewritten by this task.

Search included accessible Family Connect state-client-build and /tmp text evidence,
with hidden/ignored files included, plus repository docs. Exact session, sender,
message, timestamp and RTP-sequence searches were performed. Standalone9063 hits
in old September PERF fixtures are unrelated and are not target correlations.
No additional exact session/message evidence was found outside the inventoried
experiment and its derivative documentation/analysis. Permission-denied system
temporary directories and the private daemon directory were not bypassed; they
are not claimed to have been searched. No fresh remote journal or phone export
was requested. Original collector retained only restricted_trace JSON events;
no packet capture, jitter dump or raw VP8 payload exists in these37 artifacts.

| Artifact | Timestamp range (UTC06.10) | Side | Contains exact attempt1? | Contains adjacent evidence? |
|---|---|---|---|---|
| instrumentation.log | 07:27:47.779–07:28:16.020 | Client | YES, native boundaries818–822;68 repeated message-bearing objects, not68 attempts |303 snapshots, fault, ACK, flow, traffic, cleanup |
| gateway.jsonl | 07:27:55.391–07:28:21.116 | Gateway | NO exact target message | Lifecycle1–34, head gap, later DATA and receiver progression |
| gateway-closeout.jsonl | 07:27:55.391–07:28:24.485 | Gateway | NO exact target message | Lifecycle1–54, same gap plus reverse104 terminal/cleanup |
| client-boundaries.json | 07:28:06.197–07:28:15.238 | Client derivative | YES, four message-bearing events819–822 | Actual attempt0/1, ACK progression; not independent evidence |
| gateway-boundaries.json | 07:28:08.006–07:28:24.479 | Gateway derivative | NO | Deduplicated retained windows, adjacent DATA23–26 |
| analysis.txt | Embedded ranges from originals | Both derivative | YES, copied sender evidence only | No extra receiver observations |
| evidence-manifest.json | No independent event interval | Both index | Identifies session/N, not remote attempt | Immutable file checksums and prior conclusion |
| ONE-EXPERIMENT-STARTED.json, instrumentation-exit.json | Harness start/end | Harness | NO | Single execution boundary |
| owner-preflight.json, fault-preflight.txt, identity-preflight.json, immediate-phone.json, immediate/*.json,185.251.89.19.json,186.246.45.246.json,cleanup.json | Preflight07:24/07:27 and later closeout; some identity objects have no event clock | Context | NO | Pair hashes, identity, admission, validity, safe state |
| installed.apk,baseline-helper.apk,helper-signature.json | Build/package artifacts, not session records | Build | NO runtime evidence | Exact artifact bytes/helper provenance |
| helper-build-*.json/.log,helper.init.gradle,testsrc/* and *.py | Source/build records, not independent event clocks | Harness | NO independent traversal proof | Recorder20ms cadence, three requests, explicit cleanup and journal filter |

Rows group supporting files; inventory.json enumerates all37 individually.
The clean preserved source checkout at diag-source-freeze-1/owner-packaging-1/source
has HEAD5327deb414ae8aa77ce2f9490fd99c9485eba740 and a clean worktree. It, not the
newly edited working source, is authoritative for interpreting the physical run.
Sealed APK e1882552, restricted JNI e433a491, gateway6af92aa9 remain the accepted
runtime pair; this task has no newer installed/distributed/invitation version.

## Chronology

UTC merges are for display. Client/gateway clocks are not assumed synchronized.
Repeated ACK base/mask values do not uniquely pair an ACK receive with a particular
generation/send. Local boundary indices/lifecycle sequence numbers and causal
message relationships establish order; no cross-host latency is inferred.
Retry delay1054ms and cleanup-to-terminal8458ms are reported recorded differences;
the latter spans clocks and is not a calibrated one-way timing measurement.

| UTC | Side/local reference | Observation |
|---|---|---|
| 07:28:06.098 /07.113 | Gateway lifecycle21/23 | Family TLS / gateway session established |
| 09.624 /09.625 | Client receipts | Sanity HTTPS200 complete / explicitly DISARMED |
| 09.627 | Client arm receipt | Generationa7c58a19b153daa34011829cc612006c, armedtrue,consumedfalse,count0 |
| 09.632 | Client654/fault receipt | DATA19 attempt0 created and consumed by one-shot drop |
| 09.634 onward | Client655 onward | Later DATA20–26 generated |
| 09.923,09.939,10.038,10.446 | Gateway758,768,786,800 | DATA23,24,25,26 accepted; ACK19 masks30,62,126,254 generated/sent |
| 10.653 | Client817 | ACK19/254 received: head absent, later seven positions SACKed |
| 10.686 | Client818–822 | Attempt1 created, carrier842410499, actual rtp_written/ok9063, timestamp1213693474 |
| UNKNOWN | Gateway selected media callbacks | No exact retry RTP/VP8/carrier/acceptance callback retained |
| 11.115 | Client837 | ACK19/255: head19 now buffered |
| 11.116 | Gateway lifecycle25 | Flow receive_next19,mask254,buffered7; boundaries752–815; asynchronous/cross-clock snapshot, not a contradiction |
| 11.120 | Client844/845 | ACK20/127,21/63: ordered consumption progresses |
| 11.132–11.144 | Client895,914,915,935 | ACK24/7,25/3,26/1,27/0 |
| 11.559 | Client lifecycle23 | send_base34,next42,pending8 |
| 11.377,11.994,12.081 | Client receipts | Three HTTPS200/full577-byte bodies |
| 12.843 | Client receipt | DNS and independent TCP request/response PASS |
| 13.115 | Gateway lifecycle27 | receive_next77,mask0,buffered0; boundaries2358–2421 |
| 15.818 | Last client diagnostic sample | Same session, healthy, terminalNONE; reverse receive_next104/mask124/buffered5 in retained flow |
| 15.845 /15.847 | Client fault receipts | Auto-disarmed/count1 verified, then explicit redundant disarm |
| 16.020 | Client cleanup receipt | Intentional local cleanup complete |
| 24.478 /24.485 | Gateway lifecycle37/45–54 | Reverse104 retry exhaustion / gateway cleanup |

The retry timer's exact scheduled deadline was not exported. Sealed DefaultConfig
uses1s RTO; DATA19 retry was observed1054ms after drop. That does not establish an
exact timer-fire instant or justify changing RTO. Sender base eventually108/next108
is recorded; the selected DATA's raw epoch and payload length remain unexported.

## Evidence-loss classification: RING_EVICTION

Sealed sessiontrace/boundary.go stores one point per increment at
`(index-1)%64`. Snapshot reports latest64 and dropped=next-64. Boundary() does not
stream individual points to the sink. sessiondiag/endpoint.go samples every2s;
trace.go attaches the ring only to CARRIER_ACTIVITY exports.

| Gateway lifecycle export | Last inserted index | Retained range | Dropped counter |
|---|---:|---|---:|
|24 at09.115|324|261–324|260|
|25 at11.116|815|752–815|751|
|27 at13.115|2421|2358–2421|2357|
|28 at15.115|3255|3192–3255|3191|
|50 at24.485|3554|3491–3554|3490|

Between relevant exports,2421−815=1606 insertions occurred. Only the final64
survive: indices816–2357 inclusive,1542 points, were never exported in those
snapshots. Receive flow progresses from missing19 to77 before the next export.
Sealed input/consume/transmit paths require recording DATA acceptance and ACK
boundaries along that progression; those successful-head records are not among
the retained windows. There is positive insertion/eviction math, not a guess
based merely on a small ring. Exact target callback indices cannot be recreated.

The completed stream's required acceptance/ACK events fell into lost coverage.
This does NOT manufacture an exact remote RTP callback: its contents, remote
sequence/timestamp and PictureID remain unknown. Periodic sampling is the
enabling condition (SNAPSHOT_TOO_LATE), not a separate proven packet-loss cause.
Gateway lifecycle numbers1–54 are contiguous, so no missing lifecycle export is
needed to explain the hole. Cleanup happened later; CLEANUP_TRUNCATION is not the
explanation for the11–13s interval. The collection filter discards non-restricted_trace
records, including any session_terminal record that might have existed; that is
an additional collection limitation, not proof that such a record held the target.

EVENT_NOT_RECORDED, receiver instrumentation failure and wrong correlation are
not established as the primary cause. The sealed receiver reads RTP before reorder,
records reconstructed VP8 with carrier header identity, and records successful
carrier completion and Reliable input. No missing stage is reclassified as
RTP_NOT_RECEIVED_REMOTE from these incomplete exports.

## Recovery attempts and exact-correlation limits

All retained sender/message pairs were examined, not just DATA19 text. The exact
sender3220232525/message842410499 occurs only on client metadata. Gateway records
adjacent messages842410492/493/496/498 carrying DATA23–26, but not842410499.
Exact source timestamp1213693474 and RTP9063 likewise do not recover a gateway
event. Nearby RTP is excluded. SFU rewriting is visible on adjacent exact carrier
messages, so source RTP9063 is not assumed to remain9063 at the receiver.
Reverse-direction DATA19 (sender975650243/message3486193000) is excluded.

No retained payload/jitter/depacketizer dump supplies a missing receiver identity.
VP8 PictureID was decoded internally but omitted from the sealed boundary schema.
Client SamplesWritten moves87→88 around the exact emission; this is not enough
to assert PictureID87: unbound WriteSample may return nil and increment that
sample counter without packetization, and the complete early writer history is
not retained. New tests do not relabel old evidence. PictureID remains UNKNOWN.

## ACK proof: acceptance YES, concrete callback recovery NO

Sealed engine.go ack() sets base=receive and mask bits from buffered sequence
offsets. dataFrame input inserts validated bytes into buffer[seq]. stream.go
enables its upward read channel only when buffer[receive] is non-nil. Only
consume() increments receive; it deletes that exact head and returns a new ACK.
Timer refresh, duplicate DATA, opening/heartbeat and reset cannot skip a missing
receive head. The sender validates remote/local epochs and window bounds before
processing ACK; the session did not restart. This is protocol/implementation proof
under the accepted endpoint execution model, not a cryptographic proof against
forged ACKs or arbitrary memory corruption.

*19/255*: all bits0–7 are present, so19–26 are buffered; DATA19 accepted, but not
yet necessarily delivered upward. *20/127*: consume19 has occurred;20–26 remain
buffered. *27/0*:19–26 have been delivered in order, no buffered bits in this ACK.
The gateway's own receive_next19→77 independently supports in-order delivery;
this is stronger than inferring acceptance merely from client send_base.

Thus **DATA19 Reliable acceptance and in-order consumption are now proven at
protocol level**, including release of the later buffered DATA20–26. Another
normal protocol event cannot legitimately advance the receiver base past19
without consuming19. Sender base alone is ACK-driven and is not an independent
receiver callback; the sealed code and matching receiver progress matter.

**ACK generation is also proven at protocol level**: a received valid19/255 or
20/127 frame requires creation of that ACK state on this path. It does not recover
the missing gateway ack_generated/ack_sent boundary index or exact generation time.
Retained gateway ACK19/254 generation/sends prove the gap phase, not healing.
The exact remote RTP/VP8/message callbacks remain unrecovered; protocol recovery
does not satisfy the original requirement for paired per-stage media observations.

## Reverse DATA104: separate issue, no fix here

Classification: **pending reverse send after peer cleanup, with observed cleanup
asymmetry**. Not proven a lifecycle bug or successful close-message propagation.
The gap pre-existed cleanup: final client flow has receive_next104/mask124/buffered5;
gateway terminal has base104,next112,pending8,head_retries8,ACK104/mask124.
Terminal24.478 minus reported age9452ms places initial reverse send near15.026,
before the client's16.020 completion. A blanket assertion that cleanup created
the original reverse gap would be wrong.

Native stop records local close, cancels the owned context, and closes session/
engine/carrier. Reliable close attempts RESET with a100ms background send context,
then cancels/closes the endpoint; it does not wait for remote RESET acknowledgement.
Queued media delivery is not equivalent to successful remote shutdown. A remote
sender with unacknowledged DATA and no observed remote reset can therefore reach
its existing retry limit after the peer leaves. Preserved evidence is consistent
with that behavior, but cannot locate loss of RESET or prove the original104 gap's
cause. Treat this as a separate lifecycle/close-propagation issue, not DATA19
failure and not corruption of its earlier evidence. No lifecycle change is made.

## Minimal local instrumentation patch

No ring-size, retry/RTO, pacing, transport-buffer, FEC, recovery or wire changes.
The ordinary64-point ring remains unchanged. Go test compilation is not a new
gateway/APK release. Current installed/public artifacts remain untouched.

* sessiontrace/watch.go: explicit per-recorder EnableEvidenceWatch target
  (direction, logical sequence, expected attempt1), one subscription per session,
  fixed finite stage-keyed metadata independent of the ordinary ring. Invalid,
  default-build or second arms are rejected. Matching sender carrier identity is
  pinned for MessageAttempt lookup even after unrelated traffic evicts the ring.
* Existing diagnostic one-shot DropDiagnostic automatically starts the sender's
  seqN/attempt1 watch when it selects DATA, unless already explicitly armed.
  Receiver **must be explicitly prearmed** with EnableEvidenceWatch before
  target emission in the future harness; no wildcard session/sequence inference.
  The existing production UI is not a new receiver-watch control endpoint.
* No attempt number is invented at the receiver: the wire does not carry it.
  Receiver exports observed seq/carrier identity; offline pairing must match it
  to sender attempt1 by exact sender/message identity within the same session.
  A second carrier identity for the watched sequence latches AMBIGUOUS rather
  than silently substituting another attempt.
* stream.go adds observations after actual consume and actual sender-base change;
  boundary.go/telemost observer add PictureID metadata. No decision, return value,
  deadline, payload, ACK or transport configuration is changed.
* Collection becomes inactive at complete proof,30s deadline, local close/failure
  or ambiguity; no rearm. Deadline uses monotonic time and is checked on events/
  snapshot, without a transport timer. Finite retained proof remains readable
  until recorder disposal; clearing it at timeout would recreate evidence loss.
* Native Snapshot.evidence_watch and gateway lifecycle delivery.evidence_watch
  republish deep-copied proof independently of ring churn, including cleanup.
  Sink rejection remains counted; subsequent exports repeat pinned proof. This
  does not promise survival if every export fails or the entire process is lost.
  No packet bodies, keys, profiles, URLs, epochs or free-text payload are retained.

Sender COMPLETE requires retry creation, carrier enqueue, actual RTP write,
returned cumulative ACK and actual base advancement. Receiver COMPLETE requires
RTP observed, VP8 reconstructed, carrier completed, Reliable accepted/consumed,
ACK generated/sent. COMPLETE is **local**; paired success additionally requires
the exact cross-peer carrier identity join and the original application/safety gates.

Future activation contract: the owner-only harness must obtain successful paired
watch receipts before stimulus, bind the receiver to the selected logical sequence,
check that the actual fault receipt selected that sequence, and preserve direct
native/gateway watch JSON through terminal state. Mismatched/unarmed/expired/ambiguous
watch is an evidence gate STOP, not permission to repeat a fault. This patch adds
the Go instrumentation API and automatic sender hook, not a new remote management
endpoint, APK UI or accepted deployment. Existing Java/operator projections are
not claimed to preserve the new field; the direct native/gateway collection path
used for this experiment is the specified canonical path for watch evidence.

## Deterministic validation and remaining gate

PASS: TestDATA19ACKProofSemantics reproduces19/254→19/255→20/127→27/0 without
claiming acceptance equals consumption. Watch tests cover1606-event eviction,
deep-copy isolation, sink rejection/re-export, wrong direction/sequence/attempt,
stale ACK rejection, competing-message ambiguity, closure, timeout, one-shot scope,
concurrency and default-build disablement. Existing runtime fault test verifies
automatic selected sender pinning.

PASS: local bound-Pion test exercises real packetization/writer/receive callbacks,
VP8/carrier/reliable/consume/ACK/base with dropped attempt0, for1-byte and16384-byte
DATA using unchanged DefaultConfig. Both peers retain correlated attempt1 after
2000 unrelated boundaries; receiver attempt number remains unknown rather than
fabricated. No real Telemost, signaling provider, phone or external endpoint.
Default sessiontrace/reliablestream/telemost suite and diagnostic-tagged race suite
PASS. Sandbox loopback-listener restriction required normal outside-sandbox local
test execution. This is not permission for a physical experiment.

Another physical test is **not needed to prove DATA19 protocol recovery**. Fresh
paired callback evidence, if still required for the original strict media gate,
cannot be created retroactively; it requires a separately authorized future run
after candidate/harness acceptance. None is requested or started in this task.

Exactly one recommended next step: separate review/candidate preparation of this
local watch patch and its explicit two-sided prearm/collection contract. No soak,
impairment, Krasnodar test, tuning or deployment follows automatically. No rollback
is needed: nothing was deployed. Existing sealed-pair rollback guidance is unchanged.
