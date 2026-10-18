# FIELD65-DATA-HOLE-1 — source audit before instrumentation

Date: 2026-10-06. Baseline HEAD `8d04632` with pre-existing uncommitted
control/docs/tests changes preserved. No production connection, restart, renewal,
deployment, publication, APK installation or Krasnodar test authorized/performed.
Recorded latest deployment: gateway `7c6e1e11`, exact-source CI phase0
`37329376362` / Clients `37329375594` PASS; export16 readback on October 5
20:19:41 UTC, PID652351/NRestarts0. This is historical evidence, not current
runtime verification. Installed field client `0.1.18-beta65`; no version change.

## Audit (recorded before code changes)

Root-cause status **STILL UNKNOWN**. Earliest proven *observation* is a hole at
ReliableStream receiver sampling, not a proven first missing transport stage.
`not_buffered_at_sample` is NOT “never arrived”. Samples are not simultaneous.
`server_sequence_gaps=false` concerns trace event continuity, not RTP continuity.

Source chain:

1. `carrier/reliablestream/engine.go`: `send` stores bytes in `sent[seq]`.
   `tick` creates a fresh DATA frame for each unsacked retry, with the same
   source/target epochs, sequence and payload, increments `pending.retries`.
   `carrier/reliablestream/stream.go:transmit` calls endpoint.SendContext again;
   retry attempt is not encoded in FRS1. Attempt0 is original; retries1..8.
2. `carrier/telemost/session.go:SendContext`: every call increments atomic
   `msgID`, including ACK/control calls. `encodeFragments(senderID,msgID,payload)`
   generates fresh message identity; senderID is session-local and unchanged.
   Fragment index starts at0 for EACH message. Same DATA has identical length,
   fragment count, payload CRC and bytes, but different message ID. Enqueue
   success is NOT writer completion. The queue is bounded at256 frames.
3. `msg.go` splits at8192 bytes, maximum8 fragments/64KiB message. Default
   Reliable DATA16KiB +64-byte FRS1 header occupies THREE carrier fragments.
   Each fragment becomes a separate VP8 sample via `encodeVP8DataFrame`.
   `vp8.go` uses a fixed17-byte interframe prefix; these bytes are not a unique
   frame identifier. Do not interpret prefix/CRC equality as media identity reuse.
4. `signaling.go:writerLoop/writeVP8Sample`: single writer uses WriteSample with
   33ms duration, also emits keepalives. Pinned Pion webrtc/v4 v4.2.15
   `track_local_static.go` and rtp v1.10.2 `packetizer.go`: bound packetizer
   advances RTP timestamp by2970 ticks/sample at90kHz, advances16-bit sequence
   for EVERY packet, and sets marker on last packet. Each retry therefore uses
   new timestamps and sequence ranges (modulo wrap), NOT old sequence positions.
   These are publisher-local identities; SFU rewrite must not be assumed absent.
5. **H4 caveat proven in dependency source**: WriteSample returns nil when the
   packetizer is nil; TrackLocalStaticRTP.writeRTP returns nil with no bindings.
   Session also silently returns if track is nil. Existing SamplesWritten and
   delivery.written are post-WriteSample counters, NOT proof of actual RTP write.
   This does not prove these cases happened during either field session.
6. `signaling.go:readVP8Track`: TrackRemote.Read → RTP.Unmarshal → aggregate
   RTPReceived → reorderBuffer → vp8FrameState → decodeVP8Frame → reassembler.
   Pion SRTP/interceptor processing precedes TrackRemote.Read. No field evidence
   currently discriminates loss before/inside that boundary.
7. `rtp.go`: reorder uses16-bit serial arithmetic,256-packet window and100ms
   gap timeout evaluated on push; old packets are dropped, far-ahead packets
   discard queued packets, duplicate queued RTP sequence replaces its entry.
   A genuinely new retry has NEW RTP sequence, so “old Reliable sequence” does
   not put it outside this window. A late ORIGINAL can be dropped safely if
   the retry is delivered. `vp8FrameState` rejects sequence gaps, malformed VP8,
   mixed timestamps, no partition-start, oversize (>32768) frames; marker
   completes a frame. No completed-timestamp cache or Reliable-sequence dedup.
8. `msg.go`: assembly/recent key is (senderID,messageID), never Reliable seq.
   Pending≤16, recent+pending≤4096,10s assembly lifetime; completed/CRC-failed
   IDs remain recent10s; expired builds are protected for another10s.
   Duplicate fragment or incompatible total/length/CRC aborts that assembly
   and makes its key recent until its deadline. This can suppress the original
   message, but a retry with a NEW message ID is not the same cache key.
   Capacity drops remain possible even with distinct IDs. No unbounded ID map.
9. Reliable input checks epochs/window; buffered equal DATA or seq below receive
   base is a duplicate and generates ACK, not an upper-layer delivery. Different
   bytes for an already buffered sequence are protocol corruption. ACK base
   advances on consume; SACK describes buffered DATA, including the head.

H1/H2/H3: source does not reuse carrier ID or RTP position for Reliable retries;
must verify actual bound writes, not only a hand-written packetizer simulation.
H5: per-message suppression/capacity is real, but cannot equate different retry
IDs without evidence. H6 is NOT established. Pion NACK retransmission of an old
RTP packet is distinct from Reliable retransmission producing fresh samples.
32-bit message ID and timestamp/16-bit RTP sequence wrap are finite counters;
cross-session numeric equality alone is not a correlation key.

## Saved paired evidence

Inputs: local `state-client-build/field65-export16/{summary,correlation,pair-output}.json`.
Session1 `657e5f21150e5ce89100a8ac9ac65ef874238f7ef65383415327dcb07bdb4d5a`;
session2 `27af3c64f6c27cc3d08be29e63ffe1e76704d2c564f7ac609636dd6addd8a825`.
No matching head fragment identities in either delivery_comparison.

| Reliable seq | Attempt | Client carrier queued | Client RTP written | Server RTP seen | Server carrier completed | Server Reliable accepted | ACK generated | Client ACK seen |
|---|---|---|---|---|---|---|---|---|
|48|0|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|
|48|1|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|
|48|2|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|
|48|3|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|
|48|4|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|
|48|5|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|
|48|6|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|
|48|7|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|
|48|8|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|
|58|0|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|
|58|1|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|
|58|2|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|
|58|3|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|
|58|4|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|
|58|5|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|
|58|6|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|
|58|7|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|
|58|8|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|

Aggregate, NOT per-attempt evidence: session1 sender50/receiver101 samples show
send_base48/send_next56/ACK48:254/retries8 and receive_next48/mask254/buffered7.
Session2 sender50/receiver53: send_base58/send_next66/ACK58:70/retries8 and
receive_next58/mask70/buffered3. Both heads not buffered at sampled receiver.
Reverse head52 also not buffered; reverse59 consumed at a non-simultaneous
sample. None proves the first missing layer. Bidirectional activity and complete
traces do not fill any UNKNOWN table cell.

## Implementation/acceptance checkpoint

Audit complete; local diagnostics/regressions implemented. **STILL UNKNOWN** for
FIELD root cause; no first-missing-layer evidence was retroactively invented.
No internal transport fix is claimed. The proven WriteSample observability
blind spot now has a negative regression and `no_rtp` metadata.

### Additional pinned-source identity verification

Pion `mediaengine.go:payloaderForCodec` enables VP8 PictureID. The pinned RTP
payloader increments it per sample modulo32768 (PictureID0 has no optional ID
bytes). Bound-track tests verify that a three-fragment Reliable DATA retry
advances PictureID by3 as well as allocating new timestamps and packet ranges.
The old synthetic framing harness used a bare VP8Payloader without this option;
it remains unchanged, and is supplemented rather than substituted for this test.

| Identity | Retransmission semantics |
|---|---|
| Reliable DATA sequence, epochs, data bytes | Same logical frame; epochs never logged |
| Local diagnostic attempt | Original0, engine retry count1..8; not on wire |
| Carrier sender ID | Same per carrier session |
| Carrier message ID | Atomic increment per Send, including other/control messages |
| Fragment index/count, CRC | Index restarts; same count/CRC for identical DATA; CRC not logged |
| VP8 encoded17-byte prefix | Identical; not a dedup identity |
| VP8 PictureID | Advances per fragment/sample,15-bit wrap |
| RTP timestamp | New per fragment/sample, +2970 ticks at33ms/90kHz,32-bit wrap |
| RTP sequence | New per packet,16-bit wrap; all packets of a frame share timestamp |
| Diagnostic media_track | Local stream binding/receive-track counter, not a peer ID |

Publisher and subscriber RTP numbers/PictureIDs MUST NOT be equated across an
SFU without evidence that it preserves them. Shared carrier sender/message IDs
survive in the carrier fragment header and are the cross-endpoint join key.

### Bounded diagnostics and interpretation

`carrier/sessiontrace/boundary.go` retains the last64 scalar-only boundary
records in a fixed array per session, with monotonic index and eviction count.
The outer lifecycle/sink event supplies the validated session_tag. Direction
`tx`/`rx` is endpoint-relative; client tx is client→server, gateway tx is reverse.
`data_sequence`/`attempt` mean reliable_data_sequence/send_attempt. Explicit
`data_known`, `attempt_known`, `message_known`, `frame_known` distinguish zero
from unknown; absent false flags never mean a known attempt0.

The original256-frame queue now transports scalar metadata with its unchanged
payload bytes; this prevents enqueue/writer scheduling races or queue residence
from losing the local retry ordinal. No Endpoint interface or wire API changed.
Each frame's writer-start record uses `carrier_written/incomplete`; only the
later result describes WriteSample completion. All stage results must be read,
not just the stage name. `ack_generated` is a generated ACK selected for sending;
`ack_sent` means endpoint enqueue returned, NOT acknowledged media transmission.

The first registered Pion interceptor observes the inner RTP writer return
after other outbound interceptors, including NACK processing. It preserves
bytes and return values. `rtp_written/ok` requires positive writer bytes and nil
error, with metadata from the actual VP8 packet header. Per-frame observations
aggregate first/last RTP sequence, count and timestamp; no payload is retained.
It proves local writer completion, not delivery by the remote SFU. In particular,
`carrier_written/ok` alone is NOT proof that this logical DATA reached RTP: use
the matching `rtp_written` message/fragment evidence, not a concurrent total.

Receiver observations are **after Pion/SRTP TrackRemote.Read but before custom
reorder**, not NIC capture. Grouped receipt is not proof of a complete VP8 frame:
reordering can split timestamp groups; a marker can arrive before missing packets.
`vp8_reassembled/ok` and `carrier_message_completed/ok` are separate boundaries.
Recent/duplicate/conflict/capacity/CRC/expiry and reorder old/window drops are
recorded where known. RTP groups without fragment0 may not know the Reliable seq.
Receiver Reliable acceptance and ACKs contain logical sequence/base/mask, but
do NOT invent a remote retry ordinal: pair carrier completion with sender IDs,
and retain ambiguity when multiple identical deliveries could explain acceptance.

No unbounded sequence→attempt map is introduced. One current RTP summary exists
per bound/received track. The existing carrier/session track limits are unchanged.
Sender lookup after eviction returns attempt UNKNOWN. Continuous throughput can
evict evidence; missing/evicted events NEVER prove loss. Owner rehearsal must
demonstrate retention of its selected dropped/retried head before any FIELD plan.

The native snapshot holds one ring, not64 entries multiplied across192 events.
The existing bounded gateway sink receives ring samples in CARRIER_ACTIVITY
delivery records. Android and Python use numeric/enum allowlists and≤64 records;
Android keeps its existing4-session archive and256KiB/513KiB record/export limits.
Tests exercise malicious extra strings, invalid numbers/flags, deep-copy/race
safety, ring eviction and full archived Android export size. No raw exception,
payload, destination, URL/IP, room identifier, token/cookie, TLS plaintext,
DTLS/ICE credential, epoch or key is added. These are diagnostics, not capture.

### Deterministic tests

All cases target both DATA48 and DATA58; the harness warms through earlier seqs,
uses real Session.SendContext/fragmentation/bound TrackLocalStaticSample/Pion
packetization and the production receiver reorder/VP8/message primitives.
Default Reliable retry/RTO/window/payload values remain unchanged.

| Case | Injection and assertions | Result |
|---|---|---|
| A | Drop head at completed-message delivery; later7 buffered, SACK254, one retry, ordered byte-exact release, base+8 | PASS |
| B | Discard all queued media fragments of original head before RTP write; retry gets new ID and15 RTP packets | PASS |
| C | Discard first head VP8 frame after real packetization; later fragments/DATA survive; retry fills head | PASS |
| D | Accept original; drop its ACKs before carrier; fresh-media retry is safely duplicate, no double delivery | PASS |
| E1 | Hold original completed message; deliver retry then original; Reliable duplicate ACK semantics preserved | PASS |
| E2 | Hold original RTP; deliver retry then old RTP; safe old-RTP suppression, no permanent gap | PASS |
| F | Existing healed/persistent-gap, timer, reorder and framing assertions retained | PASS |
| Attempts0..8 | Same DATA, nine fresh carrier identities, three new PictureIDs/timestamps per attempt, contiguous fresh RTP ranges | PASS |
| Virtual clock | DATA48/58 head/SACK recovery; both buffered and consumed duplicates, late original, no exhaustion | PASS |
| Unbound sample | WriteSample nil/SamplesWritten increments, zero RTP writer calls; diagnostic says no_rtp | PASS |
| Real PeerConnection | Existing two-process207 byte-exact checks over Pion DTLS/RTP plus actual writer/reader boundary evidence | PASS |

For C/E2, the fault harness explicitly advances the receiver gap deadline before
later DATA; it does not wait for a periodic ACK and accidentally race the head
retry. This is test-only clock control, not a production reorder/timer change.
First harness failures are preserved: r1 C/E2 missed transient SACK observation;
initial D dropped ACK RTP after packetization and created a second reverse gap,
therefore needing two retries. D now drops ACK before carrier to isolate its
intended fault; the original exactly-one-retry assertion remains intact and
passes five repeats under race detection.

### Test/build receipts (local, not release acceptance)

All logs/binaries below are ignored local files under
`state-client-build/field65-export16/`, not public artifacts:

- `carrier-final-full.log`: `go test ./... -count=1`,14 tested packages PASS.
- `carrier-final-race.log`: `go test -race ./... -count=1`,14 packages PASS.
- `duplicate-accepted.log`: both D cases ×5, race PASS.
- `real-peer-boundaries.log`: additional real PeerConnection observer assertions,
  race PASS; full207 byte checks retained. Not Telemost or Android acceptance.
- `android-jvm-tests-final.log`:11 JVM tests PASS, including native projection
  and archived export budget. `privacy-python-tests-final.log`:32 PASS.
- `native-packet-tests-r2.log`: isolated pinned Xray patch, native packet race PASS.
- `android-native-build-accepted.log`: Android ARM64 JNI built with Go1.26,
  pinned Xray d2758a023cd7f4174a5a5fa4ff66e487d4342ba0 and installed NDK27.2.12479018.
  SHA256 `49406ddb8a6672804bf97b75a13131d1c830219791650e1247973d629ab5f6bc`.
- `bootstrap-broker-accepted`: Linux gateway built locally, SHA256
  `ce017d8fd5b3fa9c7c11597d7002dd6904eccc9b0431445fae07c6af941fc426`.
- `android-gradle-product.log`: offline isolated Friends Gradle unit/lint/unsigned
  APK build PASS,66 tasks executed;258 tests in41 suites,0 failures/errors/skips;
  lint0 errors/37 warnings. Existing product build.gradle/version/generated assets
  untouched; local init overlay selects the new JNI and a separate build directory.
  `android-product-build/app/outputs/apk/friends/app-friends-unsigned.apk` SHA256
  `f686988d8da15b4ffced81efc6d8e9e9041286b65543bb5e884f7af0419f1d6e`.
  APK metadata still beta65; **internal unsigned diagnostic build, NOT a replacement
  published beta65**. Packaged `libfc_restricted.so` SHA256 equals the JNI hash
  above (Gradle packages it unstripped); no signing key was used.
- `working-copy-privacy.json`: existing source-guard patterns applied to the23
  actual changed task files,0 blocked. This is not an index/history-wide claim.
  `data-hole-docs-check.json`:3 changed docs/409 local links,0 errors.

Early attempts failed on /tmp disk quota, incomplete manual JVM sourcepath/old
Gson, wrong module cache, and Git parent discovery in the standalone native
fixture. Retained logs distinguish these from product failures. Final runs use
local disk scratch/cache, Gson2.13.2 and GIT_CEILING_DIRECTORIES for Xray patching.
Opt-in remote/live tests are not evidence of acceptance when skipped.

### Changes, remaining gates and rollback

Files for this task (pre-existing unrelated changes are not included):

- `carrier/reliablestream/{stream.go,head_loss_test.go}`
- `carrier/sessiontrace/{boundary.go,boundary_test.go,delivery.go,trace.go}`
- `carrier/telemost/{boundary.go,head_loss_test.go,msg.go,rtp.go,session.go,signaling.go}`
- `carrier/telemost/{local_process_test.go,performance_test.go,session_test.go}`
- `clients/android/app/src/main/java/com/familyconnect/app/{RestrictedDelivery.java,RestrictedTrace.java}`
- `clients/android/app/src/test/java/com/familyconnect/app/RestrictedBoundaryTest.java`
- `scripts/correlate_restricted.py`, `tests/test_restricted_boundaries.py`
- `docs/STATUS.md`, `docs/PLAN.md`, this report.

No version bump, signed catalog, invitation/download link, public checksum,
Family TLS, Mux, Android VPN/TUN, retry budget, RTO, pacing, FEC or transport buffer
change. Additive diagnostic JSON is the only exported schema extension. No new
third-party dependency. Matching new APK/native gateway are needed to collect
these boundaries at both ends; old beta65 cannot manufacture missing history.
Local artifacts are diagnostic-only from an uncommitted worktree, NOT an
immutable successor, accepted CI release or permission to install/distribute65
with different bytes. Platform CI/artifact/security/signing gates remain required.

**Owner-device one-head drop → same seq/new attempt → remote acceptance → ACK →
base progression → HTTPS without session restart: NOT PERFORMED.** No device
installation, new room, remote gateway change or Krasnodar test was made.
No claim of external media loss: paired new sender/receiver field RTP evidence
does not yet exist. Single recommended next step, after local product checks:
separately authorize the owner-only controlled-loss acceptance of the diagnostic
pair, with exact artifacts and bounded target-attempt retention; not another
Krasnodar trial. Stop at proven first missing boundary, not timer/reconnect tuning.

No deployment rollback is needed. Previous operational rollback remains
`/opt/apps/family_connect/restricted-materials-stage-20261001/rtp-gap-8d04632-20261005/bootstrap-broker.previous`
(accepted05571644) as recorded in export16; neither executable was changed.
Never restore expired material. Local rollback is a scoped reversal of only
this task's edits, preserving all previously uncommitted control/docs/tests work.

Input SHA256: summary.json and pair-output.json both
`a10a7f4919ce750e9878c7a883422131094d45ac22323eb8900a94d9f6850787`;
correlation.json `0b3f0a9fd34f2af0d2e925831d8bf012729dd1ff642c8fa9530dec438af4d2e0`.
