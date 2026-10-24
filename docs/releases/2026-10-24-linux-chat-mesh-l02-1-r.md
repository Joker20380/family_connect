# L02.1-R — terminal native generation reconciliation

Date: 2026-10-24. **CHECKPOINT, review pending. Parent L02 PARTIAL.**
**STOP. NEXT — review L02.1-R.** No combined VPN gate expansion or release.

## Input and scope

Clean current `main` and observed remote were
`878d2918ce4ba014bd7fe73a1f223753ce18748b`; no checkout rollback. Preserve
[L02.1 evidence](2026-10-24-linux-chat-mesh-l02-1.md), L01/L01-R route provenance,
D03 terminal/no-replay, D04/D05, device/UID admission, verified profile context,
fixed chat services and no SYSTEM fallback. D01 remains open, D02.1-R PARTIAL/NOT_RUN.
Original `restrictedowner/owner.go` and all 175 accepted Android106/reference source
pins are unchanged. No production endpoint/trust/fault-injection switches added.

## Before: actual native failures, not Python cancellation

Disposable authenticated fixture, real Linux owners/IPC/native sessions; explicit
bootstrap, peer/Mux, terminal, drained and cleanup events. Baseline worker built
before product changes. Both expected regressions failed: **2 failed in 8.80s**;
repeat with a fully valid register proof: **2 failed / 3 deselected in 8.91s**.

- **A:** challenge/register succeed, native leases 1→2→1 per operation. Close peer
  Mux while underlay/readiness remain valid. Native route becomes UNAVAILABLE;
  `binding()` and repeated `prepare()` still return the old Binding and renew
  `touched`. Retained generation lease remains; opens=1, no healthy replacement.
- **B:** hold bootstrap after retained lease A returns CONNECTING; return native
  opening error, wait actual drain. Old Binding/lease A survive. New challenge
  opens owner B using only its operation lease: aggregate leases 1→2→1, but B's
  last reference drops to zero. Challenge200→held cleanup→register UNAVAILABLE;
  old generation route stays UNAVAILABLE; opens=2 in the same worker.

Local preserved evidence: `/tmp/fc-l021-r/red.log`, SHA256
`a3e85a789619b7b79acb5825f86066cb3ab1c2515366cce448c7b288e06a9479`;
baseline fixture binary SHA256
`4a4601ecbecaabe51eb367412592593e21d104f6b1a194803e135a0e26695764`.
The first run's register body was malformed, so its error alone was not proof of
the transport failure. The corrected repeat explicitly records valid register
**UNAVAILABLE**: `/tmp/fc-l021-r/red-verified.log`, SHA256
`7e49de243cbaf1f317f9e1ea05b777026879d89eafc4be3287e7a8385951eb97`.
It mounts saved baseline ServiceOwner/Binding read-only in the disposable
container with the baseline native binary; the working checkout is never reset.
No private fixture keys/profiles/database or binaries are committed.

## Fix and ordering

`ServiceOwner` installs its held generation lease on Binding. Prepare/probe,
binding lookup and watcher query that lease's native route. CONNECTING is live;
terminal/unknown route fences this Binding, closes new admission, cancels its
generation and does not renew demand. A broken lane is a reason to stop, **not**
proof of cleanup.

Private acquisition now optionally supplies a generation lease ID. IPC resolves
the exact retained Client; validated readiness/device/profile materials still pass
through `Owner.AcquireGeneration`. New `Coordinator.RetainChat`, in a separate
source file, checks identity/context/profile and increments the existing owner's
refcount under the coordinator mutex. It has **no open callback** and cannot
bootstrap or switch owners. Original AcquireChat/Release/refcount semantics and
MaxLeases/jobs/streams/timeouts remain intact. Release cancels pending pinned jobs.

After acquire, Binding checks cancellation/local fencing and native route before
use; rejected/late results release only their old lease. HTTP errors are never
replayed. Cleanup retains the established ordering: fence/cancel → release
operation/generation leases → native stop/drain confirmation → worker exit →
process admission release. Missing confirmation leaves the lock/marker sticky.

## After and validation levels

- **13 authenticated process checks PASS:** existing healthy lifetime, preemption,
  expiry, cancellation, shutdown, active mailbox and sticky cleanup; both A/B
  recover on explicit new demand, same readiness/underlay, fresh worker/generation,
  one new transport for challenge/register/duplex fixed mailbox. No idle45s wait.
- Separate acquire barrier crosses failed bootstrap/drain after a live check:
  stale pinned acquire returns UNAVAILABLE, opens remains1, no operation lease2,
  no HTTP. This proves more than background polling.
- Late acquire and already-completed HTTP results are held across peer failure,
  real cleanup, worker exit and replacement. Neither changes the new generation;
  API call counts prove no replay. Held cleanup blocks concurrent demand and VPN
  reservation; terminal unconfirmed cleanup preserves admission/marker.
- **580** selected Python/native + messenger owner/mailbox checks PASS; **13**
  separate root→UID/process checks PASS. D03 typed failures, identity/material,
  admission, L01-R provenance and Auto/DIRECT checks retained.
- Go race PASS: `restrictedowner`, `restrictedchat`, `familysession`, `roombroker`;
  native `chatipc`, `worker`, `direct`. Standard Linux native build/test PASS.
  Accepted reference verification **175 PASS**. No acceptance is inferred from PID.
- Actual isolated-kernel Auto guard **44** and native Auto policy **18** checks
  PASS; DIRECT fixed HTTPS/mailbox/TLS-fatal/no-fallback gate PASS. Host networking
  unchanged. Runs use disposable Docker/network namespaces and locked Python deps.

Commands/recipe: [fixture README](../../tests/fixtures/mesh_lifetime/README.md),
`test_mesh_chat_lifetime_native.py` plus `test_mesh_chat_terminal_native.py` under
`FC_L021_WORKER`; retained CI recipe in `desktop-auto-bridge.yml` now runs both.
Local logs/builds live under `/tmp/fc-l021-r/`; previous `/tmp/fc-l021` is preserved.
There are **606 distinct local checks** (580+13+13); the A/B recovery tests were
also repeated with explicit unchanged-readiness/underlay assertions: 2 PASS,
3 deselected. Repeats are not counted as additional coverage.
Initial fixture-only test adjustments (event observations, reused chat identity,
explicit VPN reservation barrier) were corrected, not skipped. An initial race
command used nonexistent `./chatdirect`; corrected `./direct` passed. Initial
source verifier rejected editing pinned `owner.go`; it was restored byte-for-byte
and the new retain method isolated. No reference hash was changed to bypass it.

Standard worker: Go1.26.1, Linux amd64, source inventory SHA256
`d65e0425d92a30d60973b9b792b8991bf5318a6862666f01db9265c28e115626`, binary SHA256
`7f9907f96012d745a4c9bec3956c34876ce1a77b6a5cd946c7b7219ff015a45e`.
Authenticated race fixture binary SHA256
`95678e5c680ede60d37aa32510f661409b4bc7a5f59c3509ff500127e70ce160`.
Xray revision/patch and accepted anchors remain unchanged. These are local test
builds, neither installed nor distributed.

## CI source separation

Completed **previous** source `a2b105de49391928d4bb9c15c4d5ee2305085918`:

| Mandatory suite | Final passed / failed / skipped |
|---|---|
| control | 3015 / 54 / 127 |
| phase0/tests | 3014 / 55 / 127 |
| phase0/Docker | 3013 / 54 / 129 |

Errors0 in all three. Additional phase0 failure:
`test_ui_unavailable_server_ack_is_authoritative`; cause **not established**.
Previous Auto/root→UID/kernel/Client Linux/AWG/TCP/voice PASS remain historical,
not transferred to new source. Mandatory full suites are retained; unrelated
failures are not fixed, disabled or represented as PASS in this checkpoint.
The current source/remote SHA and new CI observation are recorded in the receipt
below after ordinary source commit/push, separately from those final counts.

## Trust boundary and remaining work

Fixture still replaces external readiness refresh with a pre-issued validated
cache; external rendezvous/Telemost signaling/ICE/media, room broker and lease
maintenance with bounded paired carrier channels; remote fixed services with
loopback ChatAccess HTTPS and a byte-mailbox peer. Materials validation, FamilyTLS/
Mux, actual native owners/IPC and Linux lifecycle remain real. Temporary TLS roots
exist only in fixture subprocesses. This is neither live Telemost nor installed
LXMF/node acceptance. Fault controls exist solely in the disposable Go overlay.

**Combined VPN publication→verified-profile EXISTING_EXIT→OFF NOT_RUN**, separate
next stage, not started: fixture still lacks generic packet/DNS/TUN health and
broker lease lifecycle. This is not evidence that live access/private capsules
are required. L03/install/live/publication/Windows/fleet/iOS NOT_RUN. Versions
remain public Linux0.2.11/Windows0.2.15, accepted Android106/native105; identity,
WG keys, activation, Support ID, history/settings and signed floors unchanged.
No deployment or runtime rollback needed. Source rollback: ordinary revert/new
commit, never reset/force-push; preserve existing private state/admission markers.
