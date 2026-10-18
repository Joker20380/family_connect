# PINNED-EVIDENCE-CANDIDATE-1 — PARTIAL

2026-10-06. Candidate preparation only; STOP before source freeze/build.
The previous SELECTED-RETRY-EVIDENCE-GAP-1 PASS remains an offline analysis result.
OWNER-CONTROLLED-LOSS-1 remains FAIL / UNKNOWN. DATA19 recovery is not re-tested
or reinterpreted here. No phone, gateway, credentials, Telemost, tester or public
release was touched. No physical fault was armed. Fault tests use local fixtures.

## Source inventory and allowlist

Read-only inventory preceded modifications. Repository root is two directories
above the session working directory; it is not the working directory itself.
Current repository HEAD is `8d046321039d0bd1e18ecc1af979ff90f591e029`,
not a candidate commit.
The clean sealed baseline is `5327deb414ae8aa77ce2f9490fd99c9485eba740`, verified
with an empty git status in `diag-source-freeze-1/owner-packaging-1/source`.
Its accepted ownerDiagnostic beta66/code66 artifacts are historical installed-pair
evidence, NOT artifacts of this candidate. No fresh deployment/release query was
needed: current STATUS and DIAG-PAIR-DEPLOY-1 record the latest accepted pair.
Public/invitation channels have not been verified or changed by this task.

Local audit root: `state-client-build/field65-export16/pinned-evidence-candidate-1/`.
`initial-status.txt` and `inventory.json` enumerate all 82 initially dirty files,
including full SHA256 and sealed-baseline comparisons where the file exists.
This is a read-only attribution aid, not proof that every dirty hunk originated
in the preceding task. Git HEAD differs from the sealed baseline; staging whole
dirty files against HEAD would absorb older diagnostic work.

Review allowlist, **delta against sealed baseline only**:

| Category | Paths |
| --- | --- |
| Pinned implementation | `carrier/reliablestream/stream.go`; `carrier/sessiontrace/{boundary,delivery,trace,watch}.go`; `carrier/telemost/boundary.go` |
| Tests | `carrier/reliablestream/{ack_proof,fault_runtime}_test.go`; `carrier/sessiontrace/{watch,watch_disabled}_test.go`; `carrier/telemost/watch_test.go` |
| Diagnostic control | `carrier/sessiontrace/{fault_enabled,fault_disabled}.go` — auto-pin/build-tag hooks only; not a receiver endpoint |
| Prior task documentation | Selected-retry sections of `docs/STATUS.md`, `docs/PLAN.md`; `docs/releases/2026-10-06-selected-retry-evidence-gap-1.md` |
| This task documentation | New candidate sections of STATUS/PLAN; this report |

Everything else in the inventory is excluded. This includes readiness/control
changes, Android Gradle/JNI/Java/ownerDiagnostic packaging, workflows, presentation
and client guides, unrelated reports and tests, signaling/reorder/boundary base
instrumentation already in the sealed baseline. Some excluded files are necessary
baseline dependencies, not changes to import from the dirty tree. Preserve them.
Ignored experiment evidence, credentials, keys, profiles and binaries are not
candidate sources. Only local audit/test outputs and documentation were added
in this task; existing implementation, index, sealed source and binaries unchanged.

## Blocking receiver/correlation finding

`EnableEvidenceWatch(WatchTarget)` is an in-process Go API used in tests. Search of
carrier, native bridge and ownerDiagnostic source finds no runtime receiver-prearm
control endpoint. JNI `fcRestrictedFault` exposes fault commands, not watch targets.
The watch target contains direction/sequence/attempt, but no explicit session tag,
generation, nonce or expected carrier identity. Recorder ownership supplies implicit
session scope only. Fault-receipt generation is NOT a watch generation.

Reliable wire DATA identifies sequence, not attempt. Carrier headers identify
sender/message/fragment, not Reliable attempt. Receiver matching ignores attempt
even when an input Boundary has AttemptKnown. It attaches the first message for
the selected sequence; competing messages mark AMBIGUOUS only while ACTIVE.
After COMPLETE, later messages are ignored. Consequently a late original can
complete an attempt1-target watch, excluding the desired retry before export.

Executable counterexample: `repro/candidate_gap_test.go` in the local audit root,
run against a byte-for-byte copy of the sessiontrace source. It prearms attempt1,
supplies attempt0 stages and ACK, then selected attempt1 with another carrier ID.
The retained watch stays COMPLETE with attempt0's message. PASS of this audit test
means the defect is reproduced, **not** acceptance. Real wire callbacks have an
unknown attempt; explicitly supplying attempt0 makes the ignored filter visible.
The existing unknown-attempt test independently demonstrates the same first-message
binding policy. No production tests were weakened or replaced.

The local Pion test drops attempt0 before carrier allocation; therefore it cannot
expose late-original competition. Its successful exact offline join is narrower
than the requested general receiver-prearm contract. RTP timestamp/sequence equality
in local Pion also does not establish equality through a remote media relay.

STOP: an executable remote prearm requires a new diagnostic runtime control surface
and a reviewed identity-handshake/collection design. No accepted watch descriptor
channel was found in the inspected runtime. Do not add attempt bytes to Reliable,
carrier payload, VP8 or Family TLS, and do not wait/block media to exchange metadata.
No source freeze, CI publishing, successor version allocation or binaries follow.

## Smallest required design — proposed, not implemented

Proposed contract `pinned-watch-v1`, export schema1, not an accepted schema today:

* Logical key: opaque existing session tag, canonical direction `client_to_gateway`
  or `gateway_to_client`, uint64 Reliable sequence, bounded attempt number, random
  128-bit watch generation. Map canonical direction to peer-local tx/rx explicitly.
  Validate session/generation against the live recorder, never by sequence alone.
* Prearm both peers before stimulus. Owner-only diagnostic control sends that key,
  fixed TTL and optional carrier sender/message constraints; both return an
  authenticated arm receipt. Use a separately reviewed process-local authenticated
  admin interface and existing authorized operator access, not production payload.
  This is a design requirement, not an existing interface or authorization to deploy.
* Sender selects exactly the logical key and exports a generation-bound descriptor
  as soon as carrier identity exists. Descriptor adds sender/message and per-fragment
  index/count, VP8 PictureID, RTP timestamp and sequence range as observed. Never
  serialize payload, addresses, credentials, stable device identities or secrets.
* Receiver must start recording before media. Preserve a tiny bounded set of
  provisional identities for the prearmed sequence until the authenticated sender
  descriptor binds the exact attempt. Unknown attempt must never mean COMPLETE.
  Delayed descriptor must join pinned storage, never the ordinary ring. Conflicting
  descriptor or provisional capacity overflow terminates INCOMPLETE/AMBIGUOUS;
  never evict the selected proof or infer which attempt arrived first.
* Suggested reviewed bound: one active watch per direction/session, two provisional
  carrier identities, fragment slots capped by the existing carrier maximum plus
  a small fixed stage set. Overflow fails evidence collection without changing
  transport. Capacity is a proposed tradeoff, not a guarantee against arbitrary
  reordering/retries. Test delayed identity, reordered fragment0 and identity conflicts.
* Release active matching at terminal proof, timeout, explicit cleanup or close;
  retain one immutable bounded receipt for delayed export until explicit purge or
  recorder disposal. Restart starts empty with a fresh nonce. Closing a session
  invalidates its generation. No persistence of live watches and no transport timer
  changes. An idle deadline may use lazy checking if every export/match checks it.
* Define relay invariants explicitly: join primarily on preserved carrier identity
  plus fragment index; record both RTP namespaces if relay rewrites sequence/time.
  Verify whether VP8 PictureID survives that path; do not assume local equality.

If prearrival exact carrier binding is required rather than bounded provisional
capture, sender allocation/descriptor delivery would need synchronization before
emission. That must NOT be added in this task; it risks timing/transport changes.

## Stage, retention and cleanup review

Current sender auto-pin occurs when diagnostic DropDiagnostic selects attempt0,
targets the same sequence's attempt1 once, and does not overwrite an existing watch.
It does not validate that an already armed sender watch matches the selected event.
Current terminal set: reliable_send, carrier_queued, rtp_written, ack_received,
base_advanced. Event timestamps are milliseconds. DATA creation, attempt creation,
fault selection, carrier allocation, VP8 allocation and packetization are not all
separate pinned stages; fault receipt is separate. Full sender contract incomplete.

Receiver currently retains rtp_received, vp8_reassembled, carrier_message_completed,
reliable_data_accepted, reliable_consumed, ack_generated, ack_sent. RTP observer
emits a frame aggregate at marker/flush, not a per-packet receipt. `Events[stage]`
retains only the first event per stage. Only fragment0 carries the parsed Reliable
sequence; later fragments are not a complete pinned per-fragment chain. Before/after
receive_next, buffered count and mask are not present as complete transitions.
Actual consume/base boundaries exist but do not solve those omissions. These
stages are instrumentable locally; they are missing, not fundamentally unavailable.

Storage is independent of the 64-entry ring, stage-enum bounded and single-watch
per recorder. Current 30-second monotonic deadline is checked on events/snapshots.
Complete receipt survives churn; timeout/close stops active collection and retains
receipt until recorder disposal. Explicit purge is absent. Closing STATE=CLOSED
alone is not a watchEvent close trigger (LOCAL_CLOSE/CLEANUP/FAILED are). Nonce-based
stale-session rejection, explicit client/gateway purge, restart and idle/export-delay
matrix are not accepted. No unbounded logging was added.

PictureID is observed from Pion VP8 descriptors on both peers, with carrier/RTP
metadata. Existing single/multi-fragment tests compare the first pinned RTP frame.
Existing identity tests exercise PictureID advancement, but this does not certify
all fragment PictureIDs or a late-original/duplicate exact-attempt pinned chain.

Reverse DATA104: no fix and no new lifecycle channel. Existing general lifecycle
and flow evidence is insufficient for E12. Proposed separate bounded channel should
record pending-send-before-cleanup, local/remote-close observation (or UNKNOWN),
carrier close, subsequent retry, terminal reason and suppression decision, without
assuming ACK impossibility merely from absent packets. Keep it independent from
forward watch capacity/selection. Remote cleanup knowledge needs explicit evidence;
no new peer-close protocol is authorized here.

## Acceptance matrix and validation

Fresh commands/results are in local `checks.json` and named logs. Sandbox loopback
restriction required the approved outside-sandbox local test rerun; preserved
`default-sandbox.log` is not a transport failure. These are regression checks of
the audited dirty source, not tests of a clean frozen candidate.

Fresh results: Go default sessiontrace/reliablestream/telemost PASS; diagnostic-tagged
race for those three packages PASS; bound-Pion selected-watch single/multi-fragment
tests PASS (2,000 later boundaries each); privacy/bounds and owner packaging source
isolation 10 tests PASS; audit counterexample PASS (confirms blocker); git diff
--check PASS. The prior task's temporary Python venv is absent, so these two stdlib/
pytest-only suites used system Python, not control/identity integration lockfiles.
An initial Python collection attempt from the session directory lacked repository
PYTHONPATH; corrected repository-root invocation passes. No control/identity suite
acceptance is claimed.

| Gate | Result and limitation |
| --- | --- |
| E1 retention | Local Pion test verifies both watch receipts after 2,000 boundaries, one- and multi-fragment payloads; not every fragment/stage |
| E2 sender auto-pin | Existing local fault-runtime test covers selected one-shot auto-pin; no fully selected two-peer control handshake |
| E3 receiver prearm | In-process API works before local media; remote endpoint/generation missing |
| E4 exact cross-peer | Narrow local offline join works; general late-original counterexample reproduced; acceptance FAIL |
| E5 retransmit identity | Existing lower-layer identity tests; full pinned attempt/fragment coverage incomplete |
| E6/E7 fragments | Local Pion tests pass their current first-stage assertions; requested full chain incomplete |
| E8 cleanup | Close disables ACTIVE; explicit purge/restart/generation matrix missing |
| E9 timeout | Existing timeout test passes; idle/export-delay matrix incomplete |
| E10 default disabled | Default-build arm rejection regression; full public-byte-identical proof not established |
| E11 privacy | Existing enum/numeric bounds, metadata-only watch and packaging/source isolation checks; not complete new schema review |
| E12 reverse lifecycle | Separate channel not implemented; NOT READY |

Default watch activation is build-tag gated. Additional consume/base/PictureID
observations are not all build-tag gated, so claiming literally no extra default
telemetry would be wrong. No evidence of intentional wire changes in the watch
delta, but byte-identical transport acceptance is not established by inspection.
Current watch boundaries have enum/numeric metadata only; the implicit recorder
session tag is not a new credential. Expanded control/privacy tests remain required.

No JNI/control surface was modified: fresh Android/JNI binary tests not run.
No new required-contract regressions were claimed complete beyond the audit
counterexample. Full source guard for a future watch endpoint remains pending.

## Provenance, rollout and next step

Candidate commit: NONE. Candidate APK version/code, signer, APK/JNI/normal-native/
gateway hashes: NOT PRODUCED. Existing sealed beta66 pair preserved byte-for-byte
by not writing to it. No successor build or hosted CI was launched, because local
acceptance did not pass. Schema/prearm contract above is proposed only.

Rollout path: none authorized. Rollback: no runtime rollback needed; this task
only adds documentation and ignored local audit/test outputs. To undo documentation,
remove only the new candidate sections/report, preserving all prior dirty content.
Do not git-reset the repository or overwrite the sealed pair.

Future owner impairment/physical run is **not evidence-ready**. Recommended next
step: review and authorize the diagnostic-only prearm/descriptor design, including
bounded provisional matching and stale-generation rejection, before implementation
and another candidate acceptance. No physical run is needed to re-prove DATA19.
