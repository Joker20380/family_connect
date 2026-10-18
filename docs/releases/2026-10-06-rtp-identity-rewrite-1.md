# RTP-IDENTITY-REWRITE-1 — PASS (local diagnostic correction)

No physical experiment, arm/prearm, install, deployment, authority operation or
transport modification was performed. Deployed/sealed beta68 remains unchanged.
The original OWNER-SELECTED-RETRY-BETA68-1 overall FAIL is not upgraded to PASS.

## Attribution and limits

Audited frozen source `1abaa3a8a9ba8ad9fa2a71c126620175b713c321`, not an assumed
deployed working-tree revision. The pre-change correlation implementation equals
the frozen file. Pinned dependencies inspected locally: Pion WebRTC v4.2.15 and RTP
v1.10.2. No public internet probe or new Telemost session was used.
All208 files in the preserved single-experiment evidence hash inventory verified.
Private ACK tokens remain unexported; no timestamp-only ACK correlation introduced.

RTP sequence/timestamp are leg-local observations across this SFU path. They need
not change in every deployment: a transparent forwarder can preserve them. They
are not guaranteed end-to-end identifiers. This run directly demonstrates different
headers for the same carrier message/frame. Telemost's server implementation is
not vendored/pinned here: the precise internal server component/algorithm responsible
is UNKNOWN. We do not claim to have audited its source or proven a universal SFU
rewrite rule. The client/dependency audit and preserved matching payload identities
are sufficient to reject a required cross-leg numeric equality contract.

## Frozen code path

1. `carrier/reliablestream/stream.go` carries seq/attempt in diagnostic context;
   attempt0 fault precedes encode/carrier allocation. Attempt is not a wire field.
2. `carrier/telemost/session.go` SendContext allocates `msgID.Add(1)` per send;
   retries of the same Reliable seq therefore have distinct carrier message IDs.
3. `carrier/telemost/msg.go` encodes sender/message/fragment index/count/length/CRC
   in the24-byte fragment header. `vp8.go` appends it to the VP8 carrier frame.
4. `signaling.go:writeVP8Sample` submits the sample. Pion `mediaengine.go` enables
   VP8 PictureID; `codecs/vp8_packet.go` increments a15-bit PictureID per frame.
   It wraps and is not independently unique or cryptographically authenticated.
5. Pion `track_local_static.go` initializes a random RTP sequencer;
   `rtp/packetizer.go` initializes a random timestamp and advances it by samples.
   Packets receive sequence numbers from that sequencer, not Reliable/carrier IDs.
6. `telemost/boundary.go` records actual publisher writer outcome and header after
   invoking the downstream RTP writer. It does not manufacture receiver headers.
7. `session.go:setupPeerConnections` creates separate publisher/subscriber PCs.
   Media traverses the external Telemost SFU; there is no client contract mapping
   subscriber header numbers back to publisher numbers.
8. Pion TrackRemote reads/unmarshals received RTP. `signaling.go:onSubscriberTrack`
   reads packets, records raw/reordered subscriber headers, reassembles VP8, then
   extracts the carrier fragment. The reorder/frame parser consumes header values;
   it does not renumber them. Diagnostic byte-preservation regressions cover this.
9. `msg.go` keys reconstruction by sender/message, verifies fragment structure and
   CRC, and reports complete carrier message. `receive_diagnostic.go` preserves
   identity into Reliable acceptance. `receiver_diagnostic.go` pins acceptance,
   consumption and private-token-matched actual ACK carrier-write outcome.

## Identifier hierarchy

| Identifier | Classification / constraint |
|---|---|
| Reliable seq | Logical end-to-end within session/direction; shared by retries |
| Attempt | Sender-local diagnostic label, bound to end-to-end carrier message by trusted descriptor; not independently decoded from wire |
| Carrier sender ID | End-to-end payload identity within session;32-bit, not globally collision-proof |
| Carrier message ID | End-to-end payload identity; monotonic per sender/send, distinguishes retries within the bounded window |
| Fragment index/count | End-to-end carrier payload identity and reconstruction structure |
| PictureID | VP8/frame identity observed stable for this selected frame; conditional constraint, not universal SFU invariant; wraps15bits |
| RTP timestamp | Publisher-leg or subscriber-leg local clock domain; equality not required |
| RTP sequence | Publisher-leg or subscriber-leg local packet numbering; equality not required |
| Session/direction/generation | Trusted local correlation scope; fresh generation prevents watch/descriptor replay |

PictureID214 is directly present at both endpoints with identical carrier
sender433208471/message2855051861 and fragment0/total1. It is proven stable for this
observation, not all future SFU paths. The correction still rejects a changed
PictureID; it does not silently relax that additional constraint.

## Chronology of the existing experiment (UTC)

| Time | Endpoint | Pinned observation |
|---|---|---|
|20:57:30.801|sender|DATA60 attempt0 consumed one-shot drop, count1, auto-disarmed|
|20:57:31.839|sender|attempt1 Reliable send/carrier queued, message2855051861|
|20:57:31.840|sender|actual RTP write ok; PictureID214; timestamp1671731102; seq20994; one packet|
|20:57:32.003|receiver|same sender/message/PictureID, fragment0/1 reconstructed and carrier complete; timestamp635613; seq220; one packet|
|20:57:32.023|sender|ACK base61/mask3 received; send-base advancement; watch COMPLETE|
|20:57:32.177 receipt|receiver|BOUND; selected candidate sequence_known=true; exact descriptor still present|
|20:57:32.513 receipt|receiver|OVERFLOW; candidates purged, no exported Reliable callback evidence|

Cross-host timestamp ordering is descriptive, not the identity criterion or a
clock-synchronization proof. Exact per-file references and full session binding are
in local `rtp-identity-rewrite-1/physical-audit.json`.

The frozen `SequenceKnown` flag is set for the watched seq60, not any DATA. Under
the trusted-operator, non-adversarial bounded-session model this combination uniquely
selects attempt1, not attempt0/2. Another attempt allocates another carrier message.
A duplicated copy of attempt1 remains the same logical retry; we cannot distinguish
which duplicated network packet instance was received.32-bit wrap/collision, malicious
forgery or arbitrary SFU payload rewriting are not ruled out globally by these IDs;
this is diagnostic correlation, not a new authentication primitive. No alternate
selected identity is supported by the retained candidate receipts.

## Corrected diagnostic contract

Publisher evidence (`publisher_rtp_seq/timestamp`) remains stored in
`descriptor.media[].first/last/timestamp/packets`. Subscriber evidence
(`subscriber_rtp_seq/timestamp`) remains separately stored in
`candidates[].media[fragment].first/last/timestamp/packets`. These are semantic
names for the existing export paths, not renamed JSON keys. Export shape remains
schema1; this is an unreleased semantic correction, not a change to beta68's sealed
contract or manifest. No descriptor/control parser expansion or wire-byte change.

Cross-peer matching requires exact session/direction/generation/selected descriptor,
carrier sender/message, selected seq, fragment index/count and PictureID, complete
reconstruction, and a valid bounded local RTP range. Publisher/subscriber timestamp,
sequence range and packet count need not equal: re-packetization can differ too.
Sender-side descriptor construction still requires its exact local media evidence.
Raw values on both legs remain retained, never normalized to pretend equality.
Each leg still requires actual emission/reception; matching RTP numbers alone fails.

Only `carrier/sessiontrace/correlation.go` diagnostic build-tagged matcher changed.
Other changed Go files are tests: sessiontrace correlation_test.go/rtp_leg_test.go,
telemost correlation_test.go/head_loss_test.go. Transport, ReliableStream, wire,
pacing/retry/RTO/buffer/FEC and private ACK-token matching code are unchanged.
Four-candidate/eight-fragment limits and fail-closed overflow are unchanged.
The patch removes the bad completion equality gate, not the overflow safety bound.

## Local regressions and acceptance

- I1: rewritten header ranges/timestamps and differing packet counts correlate;
  local bound-Pion packetization→header-rewrite→VP8/carrier reconstruction PASS.
- I2: equal RTP numbers with wrong stable identity rejected.
- I3/I4: wrong carrier message or wrong PictureID rejected.
- I5/I6: late-original/attempt2/replay matrix and fragment mixing rejection PASS.
- I7: rewritten-media lifecycle stays nonterminal until selected acceptance,
  consumption and private-token-matched actual ACK write; wrong-token callback
  cannot finish it. Existing2101-event retention/cleanup/timeout tests PASS.
- I8: full default suite including beta66 schema golden/privacy PASS; no default
  telemetry additions. Existing observer byte-preservation tests PASS.
- Full diagnostic race suite PASS with Go1.26.1 using `-p 1`; initial parallel
  compilation hit disk quota, not a test failure, and its log is retained.
- Final sessiontrace race rerun PASS after adding exact DATA60 offline replay;
  replay reaches CARRIER_COMPLETE only, with nil Reliable evidence.
-43 Python source guards PASS. Documentation links and diff whitespace checked.

Initial local test-fixture corrections are retained in execution history: publisher
first VP8 frame lacks PictureID, so the Pion fixture uses an ordinary initial attempt
before selecting attempt1; replay uses a fresh recorder, not forbidden reuse of a
cleaned generation. No production rule was weakened to accommodate either fixture.

Evidence/logs: `state-client-build/field65-export16/rtp-identity-rewrite-1/`:
`physical-audit.json`, `source-scope.json`, `go-default.log`,
`go-diagnostic-race.log`, `go-diagnostic-race-serial.log`,
`sessiontrace-final.log`, `source-guards.log`.

## Reclassification (preserved evidence only)

| Required proof | Result |
|---|---|
| Sender retry actual emission | Proven |
| Selected remote media reception | Proven under corrected scoped identity model |
| Selected carrier reconstruction | Proven |
| Exact Reliable acceptance before/after state | Not proven; callbacks were not exported |
| Selected consumption/order transition | Not proven directly at receiver |
| Selected ACK generation/actual-write callback | Not proven; sender ACK is not a substitute |
| Sender ACK/base progression | Proven, base61/mask3 |
| Application continuity | Proven within captured session window |

Overall physical experiment remains FAIL against its full pinned-chain criteria.
No missing callback is inferred from application success or replay of synthetic
events. A source correction is necessary before another physical run, and the
working-tree patch is not yet frozen/released/deployed. Existing beta68 rollback
assets and runtime remain untouched; this task needed no rollback.

**One next step:** review and freeze the diagnostic-only correction through the
normal source-bound acceptance process before seeking any new physical-run authorization.
