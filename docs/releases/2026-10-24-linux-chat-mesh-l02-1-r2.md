# L02.1-R2 — native status result classification

Date: **2026-10-24**. Bounded source checkpoint, **review pending**.
**Parent L02 PARTIAL. STOP. NEXT — review L02.1-R2.**

Entry: clean current `main`, remote verified at
`323d49b09af57a809ba467f27e9c4650a97d7844`; no checkout rollback.
Review of [L02.1-R](2026-10-24-linux-chat-mesh-l02-1-r.md) atomic `RetainChat`
and both terminal-generation corrections is accepted. L01/L01-R, D03/D04/D05
remain accepted; D01 open, D02.1-R PARTIAL/NOT_RUN.

## Before / after

Before tests used unchanged production Python from the entry SHA, the actual
bounded `ChatLane`, and the unchanged L02.1-R native binaries. Explicit events
hold replies; no fake that unconditionally raises BUSY, no native failure via
`owner.cancel.set()`. Local evidence stays under `/tmp/fc-l021-r2/`;
previous `/tmp/fc-l021-r/` and L02.1 evidence are preserved.

| Boundary | Before | After |
|---|---|---|
| Four real pending CONTROL commands, then fifth route check | `native_alive=False`, cancelled=True, lane_closed=False; native route still SERVICE_ONLY | ChatError BUSY_OR_UNAVAILABLE, neither True nor terminal; same generation retained |
| Authenticated actual owner under that contention | Healthy transport cancelled, opens=1, route SERVICE_ONLY | Generation lease survives; second challenge/register/duplex fixed-mailbox on same worker/lease/transport, opens=1, never leases0 |
| Malformed framed route reply, Host→ChatBridge | Parser DENIED becomes UNAVAILABLE | DENIED preserved; admission fenced |
| Same reply through ChatHTTP | `service_unavailable` | `access_rejected`; zero native HTTP sends/replays |

Verified red logs: `red-boundary-verified.log` **3 expected failures/0.61s**;
`red-native-verified.log` **1 expected failure/4.47s**. Exploratory logs are retained
but not counted as defect evidence. The unit malformed reply is sent over a real
AF_UNIX framed stream into the normal ChatLane parser. Its DIRECT mock fails
before send, exactly once. No fallback/replay follows DENIED.

Sanitized evidence SHA256 (raw test logs remain local):

| Log | SHA256 |
|---|---|
| `red-boundary-verified.log` | `8703e893dce9413d41fda8a2f880a12e2ee8e50a866d146cf0fee15240826b88` |
| `red-native-verified.log` | `493a645de4b6f5d4dff8dff5ddbe6aa490919f46459fe895fa58e274dd647aa8` |
| `green-boundary-final.log` | `e13955cd9610e1a6f638d733f390fa3ae1d79ef5907078773f314441101d2b01` |
| `green-authenticated.log` | `9c3ed179597f945e8801c77dd19803f314feeae95744c66a0426c8863e1a5f5b` |
| `green-native-final.log` | `3561bde139815e1a1dca6c078341da4bd53b0efa0034093968db5bcd2d559fd2` |

## Correction and ownership

Only production Python `Binding`/Host and `ServiceOwner` status handling changes:

- A missing CONTROL slot is unknown availability, not healthy status and not
  terminal evidence. Prepare/probe/binding/acquire reject that operation without
  touching demand time or cancelling the held generation. Watcher explicitly
  catches/defer BUSY, continues expiry/underlay checks and remains alive.
- Terminal route/closed lane fence the Binding. Protocol DENIED and applicable
  typed final reasons are retained on that **Binding**, not a global latch.
  Cleanup/cancellation cannot replace a known DENIED with UNAVAILABLE/CANCELLED.
  Watcher handles final ChatError and enters existing cleanup, not thread escape.
- Acquire checks status **before** acquiring the operation resource. Afterwards
  the unchanged atomic generation-pinned native acquire and its route reply,
  together with local fence/cancel checks, determine admission. A second status
  RPC after acquiring would risk BUSY followed by another BUSY on release.
  No unobserved status is accepted as healthy; the native pin still forbids
  creating owner B under generation A. Late acquire/HTTP results are rejected;
  already-sent HTTP is not replayed.
- Ownership remains generation lease + separate operation leases. Fence/cancel
  precedes release/drain, confirmed native cleanup, worker exit, then process
  admission release. Unconfirmed cleanup still holds flock/admission/marker.
  Nothing changes native Coordinator/refcount, IPC limits (CONTROL4/jobs12),
  readiness/idle deadlines, fixed paths, UID/device/profile checks or trust roots.

Tests cover all five status call sites, watcher survival, typed
DENIED/CONFLICT/DEADLINE/CANCELLED after cleanup, and held late acquire/request
results. The unit lifecycle peer models replies only; it is not native acceptance.
The supplementary actual-owner malformed test corrupts a decoded route reply
**before the real ChatLane validator**, only in the test. It observes leases0,
holds actual native cleanup and admission, checks OWNER_BUSY, then confirms
cleanup/worker exit and authenticates a new generation. An old Binding's late
DENIED does not mutate that new generation.

## Local checks for the R2 source

Commands use the existing locked `fc-l01-kernel:check` environment, Python3.13.15,
network-none containers, unchanged current native inventory. Authenticated tests
use an isolated root NET_ADMIN namespace with dummy eth0, never host routing.

| Check | Result |
|---|---|
| `test_mesh_chat_status.py`, chat lane/host/service, `test_chat_bridge_http.py` | **117 passed / 9.20s** |
| DIRECT/registration provenance, friends mesh/Auto/owner error-lifecycle tests | **66 passed / 13.46s** |
| Actual root→UID runtime + process ownership | **13 passed / 0.89s** |
| Original lifetime/terminal authenticated regressions plus R2 status tests | **15 passed / 108.99s**, includes all original **13**, not substitutes |
| `go test -race -count=1` desktop `./chatipc ./worker` | PASS (1.182s / 1.028s) |
| `python -m scripts.verify_desktop_reference` | **175 pins PASS**, unchanged |

211 distinct Python/native/process checks; repeats are not added to this count.
Final R2-only authenticated repeat, including explicit post-contention lease
accounting: **2 passed / 12.48s** (`green-native-final.log`). Source/CI receipt
and documentation checks are recorded below.
Existing healthy-lifetime, preemption, expiry, cancellation, shutdown,
active-mailbox, failed-bootstrap/acquire race, late results, concurrent demand/
VPN reservation and sticky cleanup regressions all remain in the executed 13.

No Go/source-inventory changes: verified against the prior build inventory,
SHA256 `d65e0425d92a30d60973b9b792b8991bf5318a6862666f01db9265c28e115626`.
Standard worker SHA256
`7f9907f96012d745a4c9bec3956c34876ce1a77b6a5cd946c7b7219ff015a45e`;
authenticated **race** fixture SHA256
`95678e5c680ede60d37aa32510f661409b4bc7a5f59c3509ff500127e70ce160`.
No new build/install/distribution is implied. Only isolated-linux test selections
are extended; all mandatory full suites and existing root→UID/Auto/DIRECT kernel
gates stay enabled. Full suites and unchanged Auto/DIRECT kernel scripts were
**NOT_RERUN locally** in this Python-only checkpoint; prior PASS is not transferred.

## Completed prior CI — distinct source

Final **L02.1-R** source `6556a902c723a3ef73486733f090cea6f388d099`:

| Suite | Passed / failed / skipped |
|---|---|
| control | **3015 / 54 / 133** |
| phase0/tests | **3015 / 54 / 133** |
| Docker | **3014 / 53 / 135** |

**errors0**. isolated-linux with **13 authenticated**, Client Linux, AWG/TCP and
voice **PASS**. This supersedes the earlier IN_PROGRESS observation, not the
failures themselves. No unrelated full-suite failure is fixed, disabled or
represented as PASS. These counts must not be attributed to the new R2 source.

## R2 source / CI receipt

Source/tests/docs **`89e20a3437b2ba1b02f7d1649487579678158373`** ordinarily committed
and pushed to existing `main`; remote branch SHA verified equal. All R2 local
results above refer to this source. Documentation-only receipt commits do not
change the tested source. No native build, version or release was changed.
Pre-commit content checks, **350 local documentation links** and
`git diff --check` PASS. Staged files contain only source/tests/workflow/docs,
not local binaries, synthetic runtime keys, product state or raw private logs.

New-source CI observation **2026-10-24 19:17 UTC**, not prior-source results:

| Job | Observed state |
|---|---|
| [Auto isolated-linux120963186437](https://github.com/Joker20380/family_connect/actions/runs/40124588213/job/120963186437) | IN_PROGRESS; root→UID/kernel/15 authenticated not yet CI PASS |
| [Auto protocol40124588213](https://github.com/Joker20380/family_connect/actions/runs/40124588213) | Linux/Windows protocol jobs IN_PROGRESS, not Windows feature acceptance |
| [Client Linux120963186543](https://github.com/Joker20380/family_connect/actions/runs/40124588212/job/120963186543) | IN_PROGRESS, not installed |
| [Control120963186558](https://github.com/Joker20380/family_connect/actions/runs/40124588227/job/120963186558) | IN_PROGRESS, full suite retained |
| [phase0/tests120963186536](https://github.com/Joker20380/family_connect/actions/runs/40124588219/job/120963186536) | IN_PROGRESS, full suite retained |
| [phase0/Docker120963186307](https://github.com/Joker20380/family_connect/actions/runs/40124588219/job/120963186307) | IN_PROGRESS, Docker/failover retained |
| [AWG120963186495](https://github.com/Joker20380/family_connect/actions/runs/40124588222/job/120963186495), [TCP120963186500](https://github.com/Joker20380/family_connect/actions/runs/40124588218/job/120963186500), [voice120963186475](https://github.com/Joker20380/family_connect/actions/runs/40124588221/job/120963186475) | IN_PROGRESS |

Public metadata receipt: `/tmp/fc-l021-r2/ci-source-initial.json`. No new full-suite
counts are available at this observation; none are inferred from local subsets.
This checkpoint is not overall CI/release acceptance. Reconcile these exact
source/job IDs in review, without starting the separate combined VPN gate.

## Boundaries and rollback

Fixture still replaces external readiness fetch (validated pre-issued cache),
rendezvous/Telemost signaling/ICE/media, broker and lease maintenance (paired
carrier channels), and remote services (loopback ChatAccess HTTPS/byte mailbox).
Material validation, FamilyTLS/Mux, native owners/leases/IPC and Linux lifecycle
are real. No production endpoint/trust bypass or fault switch was added.
Authenticated local PASS is neither live Telemost nor installed LXMF/node acceptance.

Combined VPN publication→verified-profile EXISTING_EXIT→OFF remains **NOT_RUN**, a
separate next stage, not expanded here. L03/install/live/publication/Windows/fleet/
iOS **NOT_RUN**. Versions remain Linux0.2.11/Windows0.2.15, accepted
Android106/native105; identity/WG keys/activation/Support ID/history/settings/
signed floors unchanged. No deployment/runtime rollback required. Source rollback
is ordinary revert/new commit, never reset/force-push; private state and sticky
admission markers must be preserved. **STOP. NEXT — review L02.1-R2.**
