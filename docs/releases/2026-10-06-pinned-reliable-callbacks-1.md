# PINNED-RELIABLE-CALLBACKS-1 — PASS

Date: 2026-10-06. **Source-level acceptance only.** No physical Telemost experiment,
owner-device access, live fault/prearm, impairment, soak or runtime deployment in
this task. Sealed/deployed beta67 is not overwritten or relabeled as fixed.

## Previous gap and preserved contract

Frozen beta67 pinned exact receiver RTP/PictureID/fragments/carrier reconstruction,
but receiver correlation COMPLETE did not require Reliable acceptance/consumption
or ACK callbacks. Ordinary64-entry boundaries could not meet ring-independent proof.
Legacy rx evidence watch was intentionally rejected and remains rejected.

Preserved: receiver prearm, key/session/direction/sequence/attempt, fresh128-bit nonce,
sender descriptor shape, late-original discrimination, exact fragment/PictureID/RTP
identity, replay checks, bounded4 provisional candidates ×8 fragments,30-second TTL,
control operations, Unix/DUMP authorization, and public-beta66-golden-v1.
Only diagnostic receipt fields are extended: media_complete and selected reliable
proof. CorrelationSchema remains1; no new JNI signature or control operation.

## New receiver lifecycle

```text
ARMED (bounded provisional identity and callback capture, before descriptor)
  -> BOUND
  -> CARRIER_COMPLETE / media_complete=true
  -> RELIABLE_ACCEPTED
  -> CONSUMED + ACK_GENERATED
  -> COMPLETE only after successful actual carrier ACK write
```

Consumption and ACK creation are one synchronous engine operation and their records
can become visible together. No requirement to sample an intermediate state: the
separate transition and ACK records preserve both observations. Missing/failed ACK
write remains incomplete, then expires/closes; it never yields COMPLETE. Existing
sender descriptor/media completion semantics are unchanged.

Provisional per-carrier callbacks can arrive before authenticated descriptor bind.
The exported selected proof is attached only after exact descriptor identity matches.
Late attempt0 or attempt2 acceptance cannot fill attempt1's proof, even for the same
logical sequence. Once selected media matches, unrelated media cannot evict that proof.

## Exact callback wiring

- `telemost/receive_diagnostic.go`: carries only known/sender/message provenance with
  the existing receive-queue payload into the exact Recv invocation. No payload
  hashing, ring lookup or "last seen message" inference. Default receiveMessage is
  still the existing []byte alias; queue capacity/order and payload bytes unchanged.
- `reliablestream/stream.go`: captures authoritative receive state around input and
  consume while holding the existing state lock, then records observations. Identity
  follows the received message; accepted result must be ok and insert one buffer entry.
  Duplicate/already-consumed/error inputs cannot create a selected acceptance record.
- Accepted proof: selected seq, callback timestamp, receive_next/mask/buffered counts
  before/after; parent receipt binds session/direction/attempt/nonce and exact media.
- Consumption proof: exact selected seq, transition timestamp and before/after state,
  receive_next advancing exactly past the selected head, and buffered_successor_ready.
  The existing consume operation releases one DATA at a time: successor_ready proves
  buffered successors become eligible, not that every successor was delivered at that
  instant. Local Pion test additionally consumes successors and proves sender base27.
- ACK creation timestamp is stamped inside existing engine.ack(), after the actual
  ACK base/mask are set. The selected consumption ACK is retained with its exact
  base/mask. A private process-local monotonic token distinguishes separate ACKs
  even if their clock timestamps/base/mask coincide. This token is not on wire/export.
- Telemost SendContext **only enqueues**. Its ordinary ack_sent boundary is therefore
  insufficient for new forensic completion. ACK context provenance travels with the
  queued fragment to the existing carrier_written callback. Only actual bound-RTP
  write result ok completes the proof; no_rtp/write_error are retained as failures.
  Generation, write timestamp and write result are distinct. No extra ACK is sent.

No retransmission, RTO, pacing, ACK calculation, ordering, window, buffer-capacity,
FEC or close/recovery policy was changed. engine.go changes only observation stamping
at ACK creation; observation fields are not encoded. Reverse DATA104 remains untouched.

## Retention, isolation, privacy and cleanup

Storage is bounded by the existing2-direction/4-candidate/8-fragment contract, with
one fixed-size acceptance transition, consumption transition and ACK record per
candidate. No event list grows with traffic. Proof is independent of the ordinary64
ring, survives2101 unrelated events, later retries, unrelated ACK/consumption, and
descriptor/export delay **within the unchanged30-second TTL**. No indefinite retention
is claimed. Returned records are deep copies; export mutation cannot alter storage.

Explicit cleanup, normal session close and timeout purge selected callbacks together
with descriptor/candidates; new Recorder/process state cannot reuse a previous watch.
Incomplete proof never becomes terminal success. Completed proof must be exported
before cleanup/TTL, as under the existing contract.

Without fc_owner_diagnostic, observation types are empty/no-op; receive queue remains
[]byte, no callback metadata is serialized and public stages/schema remain unchanged.
Golden tests were extended to exercise all new no-op callbacks and reject new
forensic fields in public exports. Control endpoints/commands are unchanged.
Only bounded protocol IDs, counters, timestamps and result states are exported:
no payload, destination, credentials, keys or identity material.

## Required regressions

| Requirement | Evidence / result |
|---|---|
| R1 carrier alone not complete | TestReceiverCallbackLifecycle: CARRIER_COMPLETE only; media matrix separately asserts media_complete |
| R2 exact acceptance | Exact message identity/seq advances RELIABLE_ACCEPTED with before/after state |
| R3 wrong acceptance seq | TestReceiverWrongCallbacks: ignored |
| R4 selected consumption | Exact19 transition19→20 and buffered successor readiness retained |
| R5 other consumption | Wrong seq cannot satisfy selected consumption |
| R6 healed ACK generated | Exact consumption ACK20/mask1 retained, no write yet |
| R7 unrelated ACK | Wrong base/mask/token, including equal timestamps, cannot satisfy proof |
| R8 actual ACK write | TestReceiverACKRequiresActualWrite rejects queued/ordinary ack_sent; ok/no_rtp/write_error distinguished |
| R9 retention |2101 unrelated events, later retries, delayed bind/export and deep-copy mutation checks |
| R10 late0/attempt2 | TestReceiverLateBindingAndAttemptIdentity plus existing six-case correlation and local Pion matrices |
| R11 wrong direction | Receiver-only hooks, reverse boundary rejection, existing concurrent-direction and Pion identity checks |
| R12 cleanup/timeout/restart | TestReceiverCleanupIncompleteAndRestart; no retained callback/descriptor/nonce |
| R13 default isolation | PublicSchemaGolden/PublicForensicsCannotEnterExport against unchanged beta66 golden |
| R14 privacy/bounds | Bounded structs/maps/export size, forbidden-field guards and existing overflow tests |

`TestSelectedRetryPinnedAcrossBoundPionAndRingFlood` now requires actual receiver
Reliable/ACK proof, not merely media COMPLETE. Both1-byte and max-configured-payload
cases use local Pion packetization/receive, exact attempt1 binding, state19→20,
successful ACK RTP write, sender base27 and2000 subsequent boundaries. These are
local synthetic regressions, not an owner physical run. Local test-only fault
fixtures do not arm any installed owner or gateway.

## Executed validation

Final source-fingerprinted run on Go1.26.1 / Python3.13.16:

- `go test -count=1 -p=1 ./...` in carrier: PASS, full default suite.
- `go test -count=1 -p=1 -race -tags=fc_owner_diagnostic ./...`: PASS, full diagnostic race suite.
- Race callback/correlation/legacy-rejection matrix: PASS.
- Bound-Pion retry/pinned-proof/correlation matrix and ACK semantics selection: PASS.
- Python pinned correlation, restricted boundaries/correlation and owner packaging
  source guards: **43 passed**.
- Existing host-cgo default and diagnostic-race JNI command harness: PASS; final
  diagnostic host-cgo rerun PASS. Android OwnerFaultReceiver Java routing compile/run:
  PASS. No APK/JNI product rebuild; no Android ABI/signature change.
- `TestACKObservationDoesNotChangeWire`: PASS; metadata absent from encoded/decoded ACK.
- `git diff --check`: PASS. Tested source fingerprints unchanged across final run;
  handoff checks verify integrated23-file worktree delta equals tested source exactly.

Retained non-final failures: sandbox initially blocked loopback sockets; approved
outside-sandbox tests used thereafter. A carrier-only initial copy lacked shared
timestamp fixtures; clean full frozen source restored those fixtures. One initial
local-two-process VP8 test reported subscriber disconnect; later full default and
diagnostic-race runs passed without changing that test or transport. A new wire test
initially constructed an invalid ACK (open-only fields/empty epochs); only its fixture
was corrected to a valid ACK. Final complete source-fingerprinted suites pass; these
earlier failures are not hidden or counted as successful acceptance.

## Clean scoped candidate handoff

Base frozen source: `ffd27988468fba427aaba6213b862dca01020972`.
Clean candidate tree prepared separately from the dirty repository, using that exact
base plus only23 reviewed Go files. Every other tracked file equals the base; existing
unrelated worktree changes preserved. No new Git commit/branch/tag was created.

- Source archive: `state-client-build/field65-export16/pinned-reliable-callbacks-1/source-candidate.tar.gz`
- Archive SHA256: `092e63c043b4eafff495b3276b9e5e837b63b66f87efd89f2490e440e85ec941`
- Scoped delta SHA256: `05a7d156e987c6a1baf2e3629ec0963d77d63db98cfc89e7826315ab68fdb937`
-1818 source files; manifest `source-manifest.json`, provenance `source-handoff.json`,
  final tests `accepted-acceptance.json` / `accepted-tested-source.json` and logs in
  that evidence directory. Handoff has no product binaries/signatures/secrets.
- Sealed beta67 pair manifest SHA25698dabfa3… and all seven members rehashed unchanged.

This is an **unsigned, unversioned source handoff**, not a new immutable binary freeze,
installed build or public release. Runtime owner/gateway beta67 remains unchanged and
still has its original evidence limitation. No public/download/catalog/invitation or
RU/EN rollout links changed because nothing was published.

**A new immutable candidate freeze may begin.** It must use a new identity/version,
not overwrite beta67, and obtain its own build/CI/artifact acceptance before any
subsequent deployment or physical experiment.

**Exactly one recommended next step:** perform the separate new immutable-candidate
freeze from this accepted scoped source handoff.
