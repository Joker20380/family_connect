# OWNER-RETRY-PREP-REVIEW-1 — PASS

Completed bounded review and local regressions, **not** selected-retry acceptance.
OWNER-SELECTED-RETRY-BETA69-1 remains FAIL. Freeze/deployment receipts are not reopened.

## Classification

- A, historical selection failure: **UNKNOWN**. Exhaustion of the original predicate
  is proven; which conjunct prevented selection is not recoverable from saved samples.
- B, old gateway exit: **UNKNOWN**. Automatic replacement is observed, but no old
  exit status/signal or lifecycle journal record was recovered. Neither crash, OOM,
  dependency failure nor external termination is proven.
- C, causal relationship: **NOT_ESTABLISHED**. Gateway loss could prevent a healthy
  idle selection, but neither its timing nor its occurrence during polling is proven.
- Proven controller weaknesses described below are not proven causes of A.

## Evidence and immutable scope

Evidence root: `state-client-build/field65-export16/owner-retry-prep-review-1/`.
Original evidence: `owner-selected-retry-beta69-1/resume1/` (untouched).
All 50 files in its evidence index match; sealed beta67/beta68/beta69 match their
existing preservation receipt. New `REVIEW.json` and `review-sha256.json` retain results.

Exact runtime source examined: `986323ecef112fcc421a22263e6fbfc9d6cf1922`, clean
validation checkout. Loaded gateway SHA256:
`edf60a6e345e1c64fdb48162ede04f3955da6f7f0b86e53c35448bce61e7182c`.
Historical controller `run.py` SHA256:
`8f645fe8c0fdb01625cf84bddd16fb7c3f74a3b4cf2c677e8d9be752d4b3b775`.
Historical helper SHA256:
`7120e394dfa19e8b8bb55da76fd7566cf917bfa4395910a6bc4ca3924f982fa0`.
Exact helper source is in the original receipt's `testsrc`, not a newly built helper.

## Chronology — 2026-10-07 UTC

| Event | Evidence/time and limitation |
|---|---|
| Deployment before beta69 start | `gateway-before-beta69.json` saved16:52:47.586373; host file mtime, not process clock |
| PID1943512 first recorded active | `gateway-beta69.json` saved16:53:16.296823; actual start lies within the deployment bracket, exact timestamp UNKNOWN |
| Old context deadline | Directory expiry20:53:05.603575967; effective4h implies context initialization16:53:05.603575967, **not** exact OS process start |
| Old directory issued |16:53:08.106470682, from saved served directory |
| Old PID checked | Served receipt18:17:34.708724; immediate preflight re-read the same PID before its aggregate receipt18:23:37.012598; individual later PID-read timestamp not recorded |
| Helper/session launch |18:24:37.716589, ONE-EXPERIMENT-STARTED receipt |
| Session established |18:24:58.657, GATEWAY_SESSION trace |
| Last saved pre-poll Flow |18:25:00.658, pending2/base6/next8; baseline only, not one of ten polling samples |
| Selection wait | Begins after baseline persistence18:25:02.284906; ends before failure persistence18:25:24.002210; exact endpoints UNKNOWN |
| First controller failure | `No stable quiescent selection point`, before18:25:24.002210; original10 status calls/2.1s sleep policy |
| Final disarm persisted |18:25:24.004762; not exact command execution time |
| Helper cleanup completion observed |18:25:25.194009, instrumentation exit host observation; not exact engine-down timestamp |
| Old PID actual exit |UNKNOWN; after last live PID observation and before new process start. Conservative timestamp bracket18:17:34.708724–18:26:59; later preflight re-read narrows it logically but has no individual clock |
| PID1992456 start |18:26:59, ExecMainStartTimestamp/ActiveEnterTimestamp21:26:59MSK |

Host file mtimes are persistence bounds, not reconstructed application events.
No subtraction of RestartSec from new-start time is presented as an observed exit.
The new start follows cleanup observation; this does **not** prove the old exit did.
No saved selected DATA, prearm, arm, bind or drop exists: all those counts remain zero.

## Exact selection predicate

Controller `run.py:94` reads owner helper `operation=status`; Java calls
`NativeRestricted.stats(handle)` and `engine.healthy()`. `latest_flow` takes the last
nonempty `delivery.flow` in `stats.packet.diagnostic.lifecycle.trace`.

| Condition | Meaning and selection purpose | Historical observation |
|---|---|---|
| At least one Flow exists | A Reliable sender snapshot exists, rather than an invented N | Baseline has Flow; missing polling Flow would have raised a different error |
| `current.healthy` | Owner engine still healthy | Original execution reached exhaustion rather than this assertion; values not retained |
| `!diagnostic.reliable_terminal` | No recorded Reliable terminal state | Same indirect control-flow evidence; samples absent |
| A prior Flow exists | A comparison point for stability | Iteration0 cannot select |
| `flow.pending == 0` | `len(state.sent)` is zero: no outstanding DATA retained for ACK/retry | Baseline2; ten poll values UNKNOWN |
| `flow.send_base == flow.send_next` | Sender acknowledged window caught up to next sequence | Baseline6!=8; poll values UNKNOWN |
| `flow.send_next == previous.send_next` | No newly allocated DATA between sampled points; choose next N | Baseline next8 only; poll pairs UNKNOWN |

`engine.flow()` defines these fields coherently within one Reliable state snapshot.
They are sender-side client_to_gateway fields because the queried endpoint is the
owner; `receive_next`/mask/buffered describe its opposite receive side and are not
selection conjuncts. A receiver status is not compared in this loop.

Schema path is correct for beta69. Missing fields are not zero: an absent nonempty
Flow raises assertion; missing pending/base/next raises KeyError when evaluated.
Short-circuiting can leave later fields unexamined if an earlier conjunct is false.
No fallback `get(field, 0)` exists. However the original loop does not revalidate
session_tag on each response/event, event sequence/timestamp, or freshness.

Flow is sampled by `sessiondiag.Sample` every2s. Status returns retained trace events,
not an atomic new send-queue measurement; repeated polls can return the same event.
Thus stale pending can falsely impede selection, stale idle can falsely appear stable.
These are code possibilities, not findings that either occurred in the physical run.
Individual snapshots are coherent, but the pair is not synchronized with live writes.

The predicate does not demand constant RTP/media/heartbeat counters. Telemost heartbeat
writes signaling traffic; Reliable ACK refresh does not advance send_next. Actual DATA
does advance it, including possible asynchronous stream-close/mux traffic. Requiring
whole-session silence would be excessive; this predicate instead requires sender-window
quiescence, but does not isolate a chosen application flow from other VPN writers.

The helper completes synchronous DNS/HTTPS/TCP and closes connections before returning
baseline. Post-arm traffic workers are not started yet. Asynchronous teardown or other
VPN writers may still produce DATA; historical persistence is not observed. Polling
calls stats/health and fault status, not traffic: it does not directly send Reliable DATA.
Native stats drains its pending event list and takes locks/ReadMemStats, so it has some
observer cost; it is not established to alter the tested send counters here.

Source anchors: `carrier/reliablestream/engine.go` flow/send/tick;
`carrier/sessiondiag/endpoint.go` Sample; `carrier/wholedevice/session.go` Capture/Snapshot;
`carrier/sessiontrace/trace.go` Record/Snapshot; `pilot/android-restricted/native/main.go`
fcRestrictedStats; exact helper traffic/status branches.

## Gateway lifecycle

`service-configuration.json` was observed18:56:30.447235UTC. Current unit bytes match
preserved old unit.before (SHA2563249833ca83f2f38d10f5ca9e2f22c6c0e436f94de18e7db60e2d60cdd2daec7).
The preliminary first-match parser's `preserved_old_unit_parameters.duration=55m`
is **not effective configuration**: `unit-layers-resource-check.json` resolves main
ExecStart55m followed by `62-four-hour.conf` reset and ExecStart4h.
Effective/preserved duration is **4h**, Restartalways, RestartUSec30s, RuntimeMax infinity,
Watchdog0, MemoryMax infinity, OOMPolicy stop. The old argv itself is no longer readable;
preserved/current effective config and directory deadline corroborate its4h lifetime.

Exact beta69 main uses signal context plus WithTimeout, then selects ctx/seed/http
termination. It can return nil at normal cancellation or return a dependency/server
error. The generic `bootstrap broker stopped` alone would not distinguish causes.
Restartalways can replace even an exit0 process. Current ExecMainStatus0/Resultsuccess
and current invocation ID are **not** old exit metadata.

Replacement18:26:59 is well before old deadline20:53:05; normal configured4h expiry
does not explain this event on the available clocks. RuntimeMax/Watchdog are not
configured triggers. External signals, resource failure, seed/carrier/http failure
remain unclassified, not affirmatively observed. Unexpected lifetime changes or clock
jumps are not invented as explanations.

Two additional service-wide (not application-PID-only) queries:18:24–18:28 and
16:52–16:54, each bounded15s, both TIMEOUT. Kernel bounded query exit1, unavailable,
not proof that OOM was absent. No old manager stop/exit record, broker primary message,
session_terminal or retry-exhaustion event was recovered. No further repeated queries.
Same-PID assertion remains valid for uninterrupted selected-retry continuity, even
though the service eventually expires/restarts by design. Budget a future scenario
within that lifetime; an expected restart would still invalidate active continuity.

## Prepared test-only change and local proof

`selection_probe.py` plus `controller-candidate.patch` are an uninstalled candidate.
`prepare_candidate.py` verifies the original controller hash and creates a patch only;
it never imports/executes the live controller. Original sources/receipts untouched.
No Java helper rebuild, signing, package changes, runtime dependency or production
packaging: all new Python/patch/tests are solely in the local review evidence directory.

- Retains pending0, base==next, stable next; unchanged max10 polls and2.1s sleeps.
- Adds fail-closed session/field checks; repeated/regressing sampled events cannot
  constitute a stable pair. No invented sequence or relaxed transport assertion.
- In-memory deque capped10, whitelist of scalar metadata, one export on failure only.
  No extra network requests, polling frequency increase or successful-sample disk writes.
- Failure export cannot replace the original exception. No payload/keys/URLs exported.
- Receiver-prearm → sender-prearm → arm → traffic and all following checks remain
  byte-identical in the patch. Actual polling failures were not retrospectively fabricated.

`python3 -m unittest discover -s owner-retry-prep-review-1 -p test_selection_probe.py -v`:
**12 PASS**. Fixtures cover fresh idle, pending DATA, advancing signaling counters,
new DATA then settlement, foreign status/event sessions, repeated stale event, missing
field, endpoint loss, export failure/primary preservation and private-value exclusion.
AST test demonstrates historical predicate accepts a repeated idle Flow; baseline
fixture confirms saved pending2/base6/next8. These are local proofs, not a reproduction
of the physical timeout or gateway failure. Source/hash and patch checks also pass.

## Unresolved safety boundary before any separately authorized owner run

Even validated fresh samples do **not** reserve N. `FaultCommand("arm")` arms the next
outbound DATA attempt0; `DropDiagnostic` captures its actual sequence. Correlation
prearm does not fence other writes. Between sampled next=N and receiver prearm/arm,
another producer can allocate N. The candidate does not solve or conceal this race.
Retaining/rechecking assertions after the drop can reject wrong selection, but cannot
undo premature transmission. Do not install/run this candidate as proof of safe selection.

First establish that the accepted helper controls all DATA writers through the entire
selection/prearm interval, or document why that cannot be achieved test-only. If not,
the minimal separate scope is an atomic expected-sequence reservation/hold coordinated
with the existing sender control and send queue until receiver readiness. That would
touch runtime/API and requires separate authorization; none was implemented here.
This is a concrete contract gap, not a new endpoint/export-field acceptance demand.

Any future run still needs explicit authorization and the existing fresh identity,
credentials/headroom, process-lifetime, unarmed-controls preflight plus prepared export
and cleanup. No second physical run, restart, renewal, prearm, bind, fault, owner-soak,
Krasnodar or publication occurred in this review. Runtime pair/rollback unchanged.
