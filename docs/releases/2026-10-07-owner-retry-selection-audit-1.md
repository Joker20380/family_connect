# OWNER selected DATA selection audit — completed, existing scenario unsafe

## Decision

| Question | Result |
|---|---|
| All new outbound DATA source classes on the actual helper path identified | YES |
| Existing helper owns the entire selection interval exclusively | NO |
| Existing immutable beta69 supports the requested safely selected test-send scenario through its exposed controls | NO |
| Physical selected-retry acceptance | Previous FAIL unchanged; no new attempt |

YES means coverage of reachable source classes and the allocation boundary, not a claim
to know which Android applications wrote during the historical session. Those historical
writers/samples are unknown and are not needed for the counterexample.
Quiescence failure UNKNOWN, gateway exit UNKNOWN, relationship NOT_ESTABLISHED remain.
The4h deadline still does not explain the historical process change. No old journal query
was repeated. Prior selection_probe validation/diagnostics remain unchanged and uninstalled.

Evidence: `state-client-build/field65-export16/owner-retry-selection-audit-1/`.
Source: clean exact `986323ecef112fcc421a22263e6fbfc9d6cf1922` validation checkout.
Actual helper/controller: prior `owner-selected-retry-beta69-1/resume1/testsrc` and `run.py`.

## Actual stack and allocation boundary

Helper `singleExperiment` calls `AutomaticVpnOwner.open`, `RestrictedTunnelEngine.up("")`.
The engine attaches the real VPN fd, not a detached direct Reliable test endpoint:
`AutomaticVpnOwner.builder` installs IPv4/IPv6 default routes without per-app allowlist;
`RestrictedTunnelEngine.java:89` replaces/attaches it; native `fcRestrictedTun` duplicates
fd and starts gVisor/Xray packet stack. `packet/engine.go:HandleConnection` calls
`wholedevice.Session.Handle` for admitted traffic. IPv4 TCP and UDP DNS are admitted;
IPv6 and non-DNS UDP are rejected before the Mux, not hidden additional DATA writers.

Path: app/TUN → packet adapter → wholedevice handler → Mux Open/Write/Read/Close/DNS
→ Mux writeLoop → Family Session.SendContext → TLS Write → net.Pipe bridge read worker
→ Reliable.SendContext → request rendezvous → engine.send → state.next++.
One TLS byte stream can split/coalesce logical Mux writes; a TCP/HTTP/Mux message is
not one Reliable sequence. Family sendSequence is not Reliable state.next.

`reliablestream/engine.go:239` is the only state.next++ allocation site. `stream.go:74`
serializes each SendContext with sendGate, chunks input, waits op.done per chunk.
`requests` is unbuffered, but callers can be waiting to rendezvous or mid-chunk loop.
op.done follows transmit handling, not end-to-end ACK or ownership of future writes.
Pending0 is only the Reliable sent map, not Mux queues/TLS/pipe/waiting requests.
No public operation acquires a lease on this interval for the test controller.

## Writer inventory

All rows marked DATA can consume new Reliable sequence after a status snapshot.
They converge at the single bridge/engine path above; serialization is not exclusivity.

| Initiator / exact source | Execution/queue | Helper control and completion proof |
|---|---|---|
| Helper DNS/HTTPS/TCP; test Java traffic() | Java test thread before baseline, then3 worker threads; socket/TUN handlers | Can delay its own future requests; synchronous returns/socket close do not drain downstream writers |
| Other IPv4 TCP/DNS consumers on the real TUN | Xray/gVisor callback → separate wholedevice Handle executions,32 TCP/16 DNS slots | No per-app gate or exclusive producer ownership in helper; no API to prevent their starts while retaining this session |
| TCP Open, mux_stream.go:63 | OpenTCP enqueues openFrame in Mux.control; waits open result | Open result is not queue ownership; other handlers can open concurrently |
| TCP payload, mux_stream.go:198 | Per-stream writeMu; stream.send queue, then Mux scheduler | Write returns after enqueue of final chunk, not necessarily allocation/ACK; helper cannot join every packet consumer |
| Receive-driven credit, mux_stream.go:159 | Reverse wholedevice io.Copy reads MuxStream; increments creditPending; pickLocked emits WINDOW_UPDATE | Triggered by old server response even without new helper request; no test API to fence/read-drain this worker |
| Local EOF/FIN, mux_stream.go:239 | wholedevice uplink copy goroutine calls CloseWrite, queues finFrame | CloseWrite acknowledges enqueue only; Java close does not join this goroutine |
| Close handshake, mux_stream.go:268; mux.go dispatchLocked | deferred stream.Close queues closeFrame and waits remote completion; receive loop updates state | Per-stream completion possible internally, but no helper-visible global join/barrier; new writes may start meanwhile |
| Reset/cancel/protocol errors, mux_stream.go:149; mux.go dispatchLocked | context.AfterFunc/OpenTCP, wholedevice cancellation, invalid incoming frame; queues resetFrame | Can occur after earlier request finished; helper cannot disable safely; reset completion is not global drain |
| DNS query/cancel, mux_dns.go:60 | per-Handle loop enqueues muxDNSQuery; timeout/cancellation queues muxDNSCancel | Query success/timeout is not scheduler drain; UDP/TCP53 consumers may initiate further queries |
| Mux scheduler in-flight frame, mux.go:298 | Removes frame while locked; unlocks before endpoint.SendContext | Empty queue/statistics can coexist with a removed frame waiting to write; no exposed in-flight fence |
| Family TLS output, familysession/session.go:257,290,319 | Handshake upfront; application Write under sendMu; Recv can invoke TLS protocol/error processing; transport bridge independent | Healthy baseline excludes initial handshake still pending, not all future TLS output; handshake/TLS control bytes are DATA at Reliable layer. Tickets disabled; no application renegotiation configured. Error/alert output is not a test-owned producer |
| Bridge and Reliable request/chunk continuation, familysession/session.go:180; stream.go:74 | net.Pipe peer.Read can finish before its following SendContext; sendGate/request waiters and continuation chunks | TLS Write return/net.Pipe handoff is not completion of all Reliable allocation; status does not report these waiters |

On this client Mux `server=false`: gateway-only forward/connect workers, openOK/openError,
DNS response upstream workers do not originate owner-side frames directly. Their responses
can cause owner credit/close/reset output as above. Gateway reverse DATA uses a different
Reliable direction/allocator; it cannot itself increment the owner's send_next.
`Session.Close`/Mux.Close join workers only by terminating the session: not a usable
selection fence for a no-restart experiment. No private mutex/field access is proposed.

### Excluded from *new* DATA allocation

- Reliable retransmit uses existing seq from sent map; ACK/ACK refresh, handshake/control
  and reset frames generated by Reliable do not call engine.send/state.next++.
- **Mux** WINDOW/FIN/RESET/DNS control is different: encrypted through Family TLS, it
  **does** become Reliable DATA. Confusing these two control layers is unsafe.
- Telemost WebSocket heartbeat/pong, ICE/DTLS/RTP/VP8/RTCP signaling/packet activity is
  below/outside Reliable DATA allocation. Protected underlay sockets prevent recursive
  TUN routing; no requirement to stop heartbeat or ACK/retry is introduced.
- Operator local socket status/correlation commands and trace sampling do not directly
  send DATA. Stats observer effects remain as recorded in the preceding review.
- Existing readiness/fetch and room establishment are control/bootstrap operations,
  not a second producer into this established session's Reliable stream. Initial Family
  TLS output already passed before the healthy baseline.

## Concrete counterexamples, not historical reconstructions

1. Sample reports next=N/pending0. Prior response bytes reach the reverse copy worker.
   MuxStream.Read adds creditPending. writeLoop emits WINDOW_UPDATE through TLS bridge;
   engine.send allocates/transmits N. Controller later prearms receiver N, generically
   arms, starts test requests; next attempt0 is N+1 and is dropped. Post-drop assertion
   catches mismatch too late. N already passed the receiver before its watch.
2. Even if no new consumer starts, writeLoop may have removed an earlier FIN/control
   frame before snapshot and be waiting on Family TLS/bridge scheduling. Pending0 and
   queue-empty snapshots do not exclude this in-flight frame. Same violation follows.
3. After receiver prearm and arm, before test worker writes, another TUN consumer
   allocates N. Generic hook drops it, possibly satisfying sequence equality while
   failing the promised ownership of the selected test send. No origin ticket exists.
4. Receiver watch expires after last status check. Correlation expire/purge cleans
   watch retention, but generic fault receipt remains armed until explicit disarm or
   terminal lifecycle. DropDiagnostic has no correlation-generation/deadline check.
   A later attempt0 can therefore be intentionally dropped without the required watch.

These schedules follow the code's synchronization and require no abnormal sleep, faulty
runtime or proven historical traffic. They establish lack of guarantee, not that any
one of them occurred on07.10. No synthetic physical replay is claimed.

## Required ordering vs available synchronization

| Transition | Existing beta69 mechanism | Decision |
|---|---|---|
| Own all new DATA producers | Java can gate its own traffic only; real TUN and reactive Mux writers continue | Not provided |
| Drain previous writes | Per-call locks/results; asynchronous scheduler/bridge; sampled Flow | No global barrier; close would terminate session |
| Choose current N | Last retained Flow event | Observation only, not atomic read/reserve |
| Receiver prearm N | Correlation command acknowledgement with session/direction/generation and TTL | Valid watch setup, but does not fence sender |
| Arm hook for that selection | FaultCommand("arm") has no N/correlation key argument | Generic next attempt0, no atomic validation |
| Release selected test send | Java traffic command spawns own workers | Does not exclude queued/reactive/other-app writers |
| Actual dropped sequence=N | Post-drop receipt assertion | Detection after harm, not safe abort-before-drop |

No test-only solution satisfies all transitions on this exposed runtime path. Longer
polling, sleep, one more status, per-call mutex or per-app filtering alone cannot fix
the independent queued/reactive writers. A detached mock/direct transport would change
the physical scenario and is not offered as a substitute. Validation/diagnostics from
the prior review are retained, but no new selection helper build/install is prepared.

## Minimal diagnostic-contract alternatives — design only

| Option | Safety / scope / pinned-chain impact |
|---|---|
| Atomic compare-next + targeted hook | Smallest change for selecting logical N regardless of producer; rejects stale next before arm, skips/aborts wrong seq, binds TTL/generation. Still cannot promise N belongs to the released test request; insufficient for the full requested order |
| Diagnostic allocation lease + selected-writer ticket, fail closed | Satisfies full order without pausing receive/ACK/retry. Requires ownership metadata reaching allocation through Mux/TLS bridge, not just recorder fault state. Retains actual attempt1 descriptor and receiver pinned-chain |
| Park next eligible write before allocation, then receiver prearm and commit | Can safely select an actual candidate even with competing producers, but selected application request must begin into the parked path before prearm; changes requested ordering and needs explicit acceptance. Bounded single-candidate admission, not a transport-wide mutex |
| Global Mux/TUN drain/pause | Broader lifecycle/backpressure scope; misses TLS/bridge unless expanded. Not preferred, and not implementable by current test-only controls |

For the **full stated ordering**, the minimum semantic addition is the fail-closed
allocation lease with writer ownership, not merely an extra recorder assertion:

1. A diagnostic-only request is serialized with the Reliable run loop's allocation
   transition under its existing short state lock. It checks live session/epoch,
   empty required window, and no in-flight *unclassified* write at this boundary;
   establishes an opaque lease for current N and explicit client_to_gateway scope.
   The lock is released immediately, before any remote request.
2. Existing queued/competing writer reaching allocation before selected release
   invalidates the lease **before intentional drop**; ordinary traffic may proceed
   without fault. No silent reassignment of N. Helper receives preparation-aborted.
3. Receiver prearm produces its generation; commit attaches exact receiver key and
   conservative local monotonic deadline to that same lease. Atomic commit rechecks
   N/epoch/lease not invalidated. Generic arm must not coexist or bypass this mode.
4. Selected release carries an opaque writer ticket through a diagnostic sideband to
   the specific TLS/bridge bytes/chunk selected for N. TLS coalescing/chunking must be
   explicitly accounted for: a caller context lost at net.Pipe is **not** sufficient.
   If bytes cannot be unambiguously associated, abort without arming/dropping.
5. The actual attempt0 boundary atomically validates lease, ticket, live epoch,
   session/direction/generation, N, and deadline, then consumes exactly once. Any
   competing writer, expired lease or ambiguity cancels before a drop, never steals N.
6. Cancel, disconnect, session replacement, terminal failure, timeout and cleanup
   retire lease/ticket/fault together, idempotently. No pending fault survives a watch
   expiry. Receiver readiness deadline must be conservatively bounded from prearm
   request start/receipt, not compared using uncalibrated host wall clocks. If freshness
   cannot be guaranteed within accepted clock/TTL bounds, abort before drop.
7. ACK receive/transmit, retry of existing DATA and signaling remain runnable throughout;
   no common transport mutex held across remote prearm. A finite diagnostic lease may
   reject selection on traffic, not suppress user packets or extend accepted TTL.
8. Existing attempt1 trusted descriptor, hop-local mapping, Reliable acceptance,
   token-matched actual ACK-write and sender-base proof remain mandatory. Do not export
   ACK tokens or replace the pinned chain with the new lease receipt.

Likely affected ownerDiagnostic-only boundaries: sessiontrace control/fault contract,
reliablestream allocation command seam, Family TLS bridge ownership handoff, and Mux/
wholedevice selected-writer ingress if retaining this TUN test-send identity. Exact
file implementation requires separate scope approval; no assertion that a one-file
fault-hook patch suffices. Default/public builds must compile the old unmodified path,
with no registered commands, leases, packet marking, waits or diagnostic retention.
No wire/RTP/ACK semantics change is required by the design. No runtime changes made.

Design obligations for later local implementation tests: selected send alone succeeds;
new competitor, queued frame or previous-request completion invalidates before drop;
closed/replaced session and expired prearm cannot commit/consume; ACK/retry continues
while operator is away. These are **not** claimed as implemented runtime tests today.

## Prepared gateway observer — not run

`gateway_exit_observer.py` is import-safe and has no live entry-point or automatic loop.
It exposes snapshot/Observer.observe/finish for the existing operator harness. For a
future separately authorized run, execute its source in memory through that harness's
existing NL SSH transport, never modify gateway/unit or write a server agent:

- Capture initial systemctl PID, InvocationID, lifecycle/result/exit properties with
  remote UTC **and remote monotonic before/after** stamps; retain as original invocation.
- Observe again at existing operator milestones (before selection, failure, cleanup,
  closeout), outside the selection polling hot path; max64 records, max10min window.
  Preserve boot ID when present in journal; never compare host/server monotonic clocks.
- Finish once with unit-wide journal query including manager messages, not old-PID-only:
  window initial→final, max64 records,5s and64KiB cap. No retries. Raw stderr discarded;
  raw MESSAGE is never exported. Only whitelist metadata and parsed PID1 exit-code/
  status/signal are retained. Old-invocation identifiers are matched explicitly;
  missing attribution remains unattributed, not borrowed from new invocation status.
- If a new invocation starts after the last observation, do not invent its time; the
  receipt covers only its measured window. Sampling does not promise to catch every
  transition. Truncation/timeout/nonzero/malformed response is explicit collection error
  or coverage limitation, never “no exit happened”. Persist local receipt before cleanup
  and preserve original failure even when collection fails.

Preparation tests: **12 PASS** (6 mocked observer tests +6 source-contract checks).
Mocks cover old/new attribution, missing attribution, timeout, bounded window, malformed
journal and no repeated finish. Source checks bind TUN attachment, credit writer,
bridge, generic fault, allocation site and expiry separation to exact source.
No actual systemctl/journal/SSH/device call was made by those tests or this task.
No physical concurrency simulation or successful retry is inferred from these tests.

## Next decision and preservation

Current beta69 owner run is **not ready for authorization under the full stated
selection guarantee**. Choose/authorize the minimal diagnostic-contract scope (or
explicitly a different logical-N-only objective); implement and locally prove it in a
separate task before requesting another physical run. This task does not authorize
modifying sealed beta69, new release/freeze, build/signing/CI or deployment.
The unknown gateway exit remains a separate operational risk; observer readiness does
not fix it. A future permitted run retains fresh identity/credentials/lifetime/controls
preflight, first-failure preservation and mandatory cleanup, without new owner soak.
Original physical FAIL, review receipts and sealed67/68/69 remain immutable.
