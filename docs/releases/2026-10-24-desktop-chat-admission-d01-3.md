# D01.3 — public chat completion/admission

Date: **2026-10-24**. Bounded source checkpoint, **CI pending**.
**STOP. NEXT — review D01.3.** D01 remains open; D02.1-R PARTIAL/NOT_RUN.

Entry: clean current `main` and remote
`d448e99b55e594522c02234ac2a87575603a6bbb`; no checkout rollback.
L02.2 review accepted: the original local L02 authenticated SERVICE_ONLY → VPN
publication → EXISTING_EXIT → new SERVICE_ONLY criterion is complete for both
Manual and Auto, at source `dac0f6b45be6ed8703d3de93ff5fdbc67462eabe`.
Its [historical report](2026-10-24-linux-chat-mesh-l02-2.md) and exact receipts are
preserved, not rewritten as D01.3 evidence. No installed/live/F-01 claim.

## Cause and deterministic red/green

Host wrote a successful probe/prepare reply before monitor cleanup, socket close
and removal from `active`. ChatBridge treated that reply as completion and opened
the next connection. With three live mailboxes, the completed-but-still-active
control operation occupied slot4; Host rejected the dependent open at cap4.
There was also a close→active-removal window outside the admission lock.

[New tests](../../clients/desktop/tests/test_chat_public_completion.py) use actual
Host, ServiceHost, ChatBridge and AF_UNIX/SCM_RIGHTS, with explicit events holding
the successful server response's return and active removal. A client recv barrier
distinguishes waiting for completion from starting another open. No random sleeps,
repeated attempts or HTTP retries. The native lane/material resolver are synthetic;
these tests do not replace the accepted15 authenticated, combined3 or kernel gates.

Before production edits, both probe and prepare cases failed deterministically:
**2 failed / 0.77s**, dependent open raised **ConnectionResetError(104)** with
active4 and only three operation leases (plus the service generation lease).
Red log SHA256: `50d48f976b55f83f4732bb590c9de9b641d98a1c05522854b55099b0a8eabfd1`.
This proves the race class, not the precise scheduling of the historical
[Client Linux failure](https://github.com/Joker20380/family_connect/actions/runs/40129362261/job/120977564976)
on `dac0f6b45be6ed8703d3de93ff5fdbc67462eabe` (BrokenPipeError at sendall).
The original failing test and every assertion remain unchanged.

## Completion contract

- Client waits for control EOF after a validated success, within the original
  deadline and max4s. Cancellation/client close interrupt it; timeout is DEADLINE;
  unexpected bytes are DENIED. Typed terminal replies do not wait or get replaced.
- Server retains active accounting through monitor/lease cleanup. Socket close
  and active removal share the admission lock; the next accept cannot reject for
  the just-completed slot. No early removal of a handler to make room.
- Host shutdown stops admission before early socket shutdown and joins handlers;
  held cleanup stays tracked. Client completion is not a capacity reservation
  against unrelated demand, and no open/request/HTTP retry is introduced.
- Public4, native CONTROL4/MAX_JOBS, generation pin/refcount, UID/device/profile,
  native drain ordering and VPN publication are unchanged. No SYSTEM fallback.

After: fourth mailbox passes, fifth live mailbox rejected, both halves closing
returns capacity; prepare behaves identically. Actual cancel/client-close/deadline/
Host-close during held completion stay bounded; retained handler blocks Host.close.
Tests count native-fixture leases, opens, exactly one HTTP send, connections,
descriptors and live handler/monitor threads. EOF/slot-removal barrier additionally
checks admission-lock ownership while the next request waits.
During test development, two assertions initially awaited mailbox cleanup without
closing the synthetic peer's half; corrected the test to finish both halves, not
product half-close semantics. This intermediate failure is not hidden as a PASS.

## Checks and source receipt

Local locked Python3.13: initial addressed Host/ServiceHost/status/error set
**121 passed / 14.62s**; final24 regressions plus lane/manual/Auto/mailbox/error
dependencies **266 passed / 38.89s**. Native code is unchanged; existing standard
and authenticated workers from L02.2 are reused, not newly claimed builds.
Original15 authenticated and mandatory CI results will be recorded separately.
Client Linux mandatory desktop pytest must PASS on the new source before D01.3
can be complete. Full CI remains enabled; no reruns merely to obtain green.

Previous source `dac0f6b45be6ed8703d3de93ff5fdbc67462eabe`, separate results:
control **3032/54/138**, phase0/tests **3032/54/138**, Docker **3030/54/140**
(passed/failed/skipped), errors0; Client Linux **1003/1/94**; voice pointer/holding
failure. Isolated-linux15+combined3/root→UID/Auto/DIRECT/race and AWG/TCP PASS.
These54 residual failures and voice failure are out of scope, not fixed/disabled.
New source SHA/jobs and content/link/diff checks: pending source commit and CI.

No version/install/deployment change; rollback is an ordinary source revert,
not a catalog or server operation. Identity/WG keys/activation/Support ID/history/
settings/signed floors/Android106 and reference pins remain unchanged.
L03, installation, live, publication, Windows, fleet and iOS **NOT_RUN**.
