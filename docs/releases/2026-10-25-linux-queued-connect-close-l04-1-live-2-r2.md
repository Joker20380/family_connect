# L04.1-LIVE-2-R2 — queued normal Connect / Linux Close

**IN_PROGRESS: source correction verified; exact candidate/package/CI pending.**
Entry main `912624211dbc176ea388efb6375fda984205db70`; affected app baseline
`053c4e5f9532ca927f49a78f9c0ed17903375baf`. Only R2 is authorized.

## Review boundary

L04.1-LIVE-2 PARTIAL/review accepted. On exact internal .4, P1/P2, B1/B2/C1/C2/D
are PASS; E FAIL/review accepted; F1/F2 NOT_RUN. The E evidence establishes a
queued normal Friends Connect Future left uncancelled by one Close, with the GUI
busy/open/CONNECTING. It does **not** establish late VPN start: helper/TUN0,
generation0/pending null, and the fixture cancelled before releasing the worker.
Historical .4 artifacts are immutable; no private identity, gateway, live VPN,
live E/F, L04.2/L05 or test-device teardown is used by R2.

## Deterministic red/green and contract

Real `App(smoke=True)`, its original single-worker `self.pool`, actual
`toggle_vpn()` normal Friends AWG/TCP path. A synthetic Friends boundary invokes
the real Linux/LinuxTCP backend with its actual durable operation journal and a
synthetic helper; no profile/identity/network is imported. Event barriers hold the
executor or running helper; Queue captures actual `GLib.idle_add` completions.
There are no sleeps, retries or manually completed Futures in the new cases.

Read-only overlay of exact prior app053c4e5: **4 deterministic FAIL**. Both one-Close
cases observe `(cancelled=False, closed=False, busy=True, action=CONNECTING)`;
both old-completion fencing cases also fail. Cleanup cancels queued work before
worker release. This is a test overlay, never a patch to a historical package.
Initial exact reproduction alone: **2 FAIL** (AWG/TCP). Green targeted selection:
**197 PASS** (including50 real-GTK cases), with only the existing GTK deprecation warning.

`connection_future` replaces `disconnect_future`. Only normal Connect/Disconnect
call sites explicitly opt into tracking; `initialized` alone is not ownership.
Close proceeds only after `Future.cancel()` succeeds, clears busy/action/initializing,
and increments the revision. Cancelled/closed callbacks do nothing; old normal
result revisions cannot replace a newer action. Running and done-but-undelivered
Futures remain busy/open until terminal GUI completion. No helper termination,
second Disconnect or manual journal/pending cleanup. Existing executor shutdown
is not used as the cancellation decision. Auto/MESH lifecycle is unchanged.

Regression coverage includes queued AWG/TCP, post-release non-execution and inert
callback, existing queued Disconnect, running Connect/Disconnect, done-undelivered
completion, two Close actions, initialization/non-connection submit, established
VPN confirmation/preservation, stale callback while open and after Disconnect,
manual-profile ownership, and generation/pending changes only after backend entry.
The non-connection cases also exclude profiles/IP/update/setup/recovery/Auto/MESH
from this narrowly owned Future; support/load/poll keep their existing lanes.

## Scope, tests and delivery in progress

Product runtime diff: **only `clients/desktop/app.py`**. Tests extend
`clients/desktop/tests/test_poll_disconnect_gui.py` (already in the real-GTK CI
step). `scripts/ci_linux_candidate.sh` advances only artifact version/path literals
to .5 so CI cannot issue new bytes under .4. No backend, helper, authorization or
system runtime change. Documentation records this checkpoint, not a public release.

Targeted tests: real GTK queue/Close + poll fencing, operations/generation,
normal Auto backend boundaries, presentation, Friends application/owner:197 PASS.
One initial command named a nonexistent test file: collection failed/no tests ran;
the corrected selection above ran in full. Full desktop with real GTK:
**1191 PASS/84 SKIP**, no failures/errors (native/isolated gates remain separate).
The first slim test-image full run:1129 PASS/133 SKIP/6 FAIL/7 ERROR; all failures
and errors are writes to read-only `/run`, not product assertion changes.
The first slim test-image Friends UI check lacked QR support and
failed waiting for the QR window; this environment failure is retained, not hidden.
The supported complete image with writable private `/run` and HOME runs Friends
UI/application, recovery/normal presentation/stale selection/close and App smoke
successfully. Full pytest completed there without excluding tests or failures.

Planned reserved version **0.2.12~l03.2.5**, new candidate ID and all three new
artifact hashes. Expected retained system build
`8d7d78ec06fc897fa7e94d21f208b08b31d6c6c3e33eaad19a262705117c8f9d`
requires exact archive/installer/source-contract verification first. Package gate
must run original DEB/AppImage in disposable offline Ubuntu24.04/systemd255 with
explicit pkexec, READY, no silent VPN, shared runtime, synthetic state preservation
and tamper/mismatch refusal. No workstation install or public download/catalog,
signature/tag/version change; public source VERSION remains0.2.11.

Existing control/phase0/Docker residual54/54/53 failures and voice/Windows
observations remain open; mandatory suites are not disabled or repaired here.
CI, exact candidate identities, package receipts, source SHA and final secret/link/
staged-scope checks will be recorded in this report after they finish.

Rollback stays explicit matching system reinstall only when idle/cleanup confirmed;
user uninstall preserves state and the independent root runtime. Historical .4 is
retained as evidence, not rewritten or re-labelled. No deployment is authorized.
L04.1 **IN_PROGRESS**. STOP after source/package checkpoint.
NEXT — **review L04.1-LIVE-2-R2**.
