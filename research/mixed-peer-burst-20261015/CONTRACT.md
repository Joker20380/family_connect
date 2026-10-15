# Predeclared local acceptance contract

Input: review ba89a5fcdd3442474ae900abe63050e365f2f3d2; new client inventory
af315dce15e16c3b5d372dee4294192339443ac0cd79364748bd2f53c156be61.
No live activity. Historical B is not replayed or causally attributed.

- Required supported finite bursts: 8, 16, 19, 20 complete carrier messages.
- Separate stress: 40 real-peer frames, also required to recover in this fixture.
- One bounded capture of at most 64 frames, each at most the existing 64 KiB
  carrier limit. Hold at most 6 seconds, unchanged default protocol timers/windows.
- Producer is a real Reliable peer: at most 8 outstanding unique DATA per direction;
  accumulation includes actual ACKs and actual timer retransmissions. No crafted
  headers or injected duplicate ACKs in positive cases.
- Release the selected prefix in one loop, no per-message wait/yield; remaining
  captured frames released as another group. Record actual duration/composition.
- Exact payload/order, cumulative window reopening and subsequent bidirectional
  traffic must survive. RECEIVE_QUEUE_FULL and ErrBackpressure are failures here.
- Slow upper consumer and short outbound stall are separate gates. Close/cancel
  and eventual zero active adapter calls are bounded. Session A cannot affect B.
- Sustained overload guard is separate, using repeated captured wire frames with
  the receive consumer held: finite queue, observable close, no claim of positive
  traffic acceptance. A replayed frame is not counted as a real peer retransmission.
- Fixed acceptance repetitions: normal1 and race3, GOMAXPROCS=1 for deliberately
  coalesced scheduling. An additional GOMAXPROCS=4 normal1 checks multicore scheduling.
  No requirement on an exact 2 ms host interval or a proportion of race outcomes.
- Separate Family/TLS handshake and byte-exact exchanges for NEW/OLD, OLD/OLD,
  NEW/NEW use disposable synthetic keys in memory. No provider or frozen executable.
- Any capacity correction must be bounded, justified against this envelope and
  leave an explicit overload guard. Existing async progress assertions remain.

## Reverse-direction gate declared before its execution

After client-inbound acceptance, the same finite load must also be checked with
the real NEW_CLIENT as sender and OLD_GATEWAY as receiver before calling the
planned client-only combination ready. This is a positive required robustness
gate, not the negative OLD/OLD control or sustained-overload characterization.
The receiver label changes; frames/windows/load/assertions do not. A reverse
failure must remain a failure and cannot be masked by NEW/NEW or by changing the
remote baseline. No production action follows either result.
