# L04.1-LIVE-2-R2 — queued normal Connect / Linux Close

**CHECKPOINT: source/exact-package/isolated gates PASS; review pending.**
Mandatory CI completed for product source1c2beb6; overall CI is **not green**.
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

GTK regression entry point in a supported synthetic test environment:
`dbus-run-session -- xvfb-run -a python -m pytest -q clients/desktop/tests/test_poll_disconnect_gui.py`.
The red run overlays only `git show 053c4e5:clients/desktop/app.py` read-only at
the import path, while retaining the new tests; green removes that overlay.

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

## Scope and source checks

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

Source checkpoint **`1c2beb6bc687c94d2a9312da0545b6e985749752`** committed and
ordinarily pushed to main; remote SHA matched. Staged source/docs/CI-version diff,
links and whitespace checked; public-source guard2925 index entries/0 blocked.
Parallel ops STATUS/PLAN additions and both VPN-health reports remain uncommitted
and outside this task's staged scope. No private state/capsules/build output in Git.

## Exact new internal candidate

Built from clean product sources at1c2beb6, not a repack of .4. Only builder's
public AppImage runtime download used networking; installed gates were offline.
Appimagetool SHA256 `95cbe7cce9717fce90c484e34052ee7c7f1d7635b33c12525b4776826a7d29b6`.

| Identity/artifact | Exact value |
| --- | --- |
| Version | `0.2.12~l03.2.5` |
| Candidate ID | `f0ee17609cfc8dbaf48edfa0f33b417754f9674d578168fa4cbb1c47d51d3f95` |
| Source SHA | `1c2beb6bc687c94d2a9312da0545b6e985749752` |
| AppImage | `FamilyConnect-0.2.12~l03.2.5-x86_64.AppImage`,57928184 bytes |
| AppImage SHA256 | `dd013ce6be2a93be817b38aac9632e5b51b00419fbbc4da154d7e0b8b0f9db32` |
| DEB | `FamilyConnect_0.2.12~l03.2.5_amd64.deb`,55987676 bytes |
| DEB SHA256 | `3b583fbdb69e726357d3b5d707629dd5dbe502078c1735cb9899de2dfb46d9ab` |
| Legacy six-file archive | `FamilyConnect-Linux-0.2.12~l03.2.5.tar.gz`,114494 bytes |
| Legacy SHA256 | `d15c7bd1c96e64921f3f511133f67665f6360762b9945d4cda1ce37bafac804a` |
| Unchanged system build | `8d7d78ec06fc897fa7e94d21f208b08b31d6c6c3e33eaad19a262705117c8f9d` |
| System archive | 49250848 bytes, SHA256 `ddd74c2132a76ac833b587d9df6409d779ce6afcdaa45fafd23faa86d7817726` |
| System installer SHA256 | `ce9acb1f363b0fafffb11c44097901a7871c28fbf0e6b9c2c5c3eaba9ef7bfb5` |
| System source | `053c4e5f9532ca927f49a78f9c0ed17903375baf` |
| Contracts/inventory | runtime2, authorization2, Python3.12;707 user/759 system archive members |

Artifacts are local under ignored
`state-client-build/linux-queued-connect-l041r2-20261025/build/`.
All .4 artifact hashes/sizes, retained system archive/installer and113 pinned
source-contract members verified; system/native/backend source diff from053c4e5
is empty. Thus old system identity names **identical bytes**, not a rebuilt system.
`verify_linux_candidate` exact extracted inventory/hash/shared-ID/six-file gate PASS.
[Sanitized manifest/receipts](2026-10-25-linux-queued-connect-close-l04-1-live-2-r2.evidence.json).

## Actual package gate

Original .5 DEB and AppImage each PASS in a fresh Ubuntu24.04/systemd255 container,
private PID/cgroup/mount/network namespaces, `--network none`, private D-Bus,
resolved and executable tmpfs. No protected identity or workstation services.
Both real GTK launches/imports, explicit pkexec setup/reinstall, matching READY,
wrong UID/path refusal, no silent VPN, tampered embedded payload/missing candidate,
wrong build/schema/modified system-module rejection PASS. Synthetic encrypted state,
background owner after GUI exit, uninstall/reinstall preservation and independent
root runtime PASS. Original AppImage and DEB use the same UID/HOME/state/system
without a second setup. Both disposable containers stopped and removed.
This is installed **package** evidence, not live E/F or protected-device acceptance.
No workstation install or public download/catalog/signature/tag change;
public source VERSION stays0.2.11. Build-time delivery flags remain the original
build receipt; this report separately records subsequent disposable installations.

## Isolated normal/native boundaries

Unchanged-source native/root→UID selection179 PASS; Auto real-kernel18 checks PASS;
protected DIRECT synthetic-TLS-peer gate PASS (no fallback, no host network change).
Authenticated combined Manual/Auto OFF→ON→OFF/terminal release3 PASS.
Standard worker hash `a63cac0491887e6a2393a034442eb093f2e2b16ae140e710794eace3265eced8`
and race fixture `12d32026aae224ac2e9d62f3a48955966e29ec8a0a3c5dc6d1d773530618bf40`
match the retained L02.2 receipts; native/carrier/fixture source is unchanged.
These are fresh local executions of existing isolated gates, not borrowed PASS.
Native bridge CI path filter does not match app.py; no native CI run is claimed.
The first local native invocation had129 PASS/50 FAIL because `/root` tmpfs was
noexec (PermissionError launching worker). Its log is retained; corrected executable
private tmpfs reruns the unchanged selection without relaxing a product check.
Additional authenticated lifetime/status/terminal cases: **15 PASS**.

## Completed CI — exact1c2beb6

| Gate | Run/job | Result |
| --- | --- | --- |
| Client Linux | [40228994481/121276468428](https://github.com/Joker20380/family_connect/actions/runs/40228994481/job/121276468428) | PASS, including full desktop, actual GTK queue tests, layout/map/Friends/recovery and both extracted formats |
| AWG | [40228994427/121276468197](https://github.com/Joker20380/family_connect/actions/runs/40228994427/job/121276468197) | PASS |
| TCP | [40228994413/121276468241](https://github.com/Joker20380/family_connect/actions/runs/40228994413/job/121276468241) | PASS; release jobs skipped |
| Standard-source system/package | [40228994396/121276467932](https://github.com/Joker20380/family_connect/actions/runs/40228994396/job/121276467932) | PASS, including actual isolated system/package and pre-start AWG/TCP gates |
| Control full suite | [40228994415/121276468372](https://github.com/Joker20380/family_connect/actions/runs/40228994415/job/121276468372) | 3165 PASS/54 FAIL/190 SKIP |
| Phase0 full suite | [40228994539/121276468155](https://github.com/Joker20380/family_connect/actions/runs/40228994539/job/121276468155) | 3165 PASS/54 FAIL/190 SKIP |
| Docker full suite | [40228994539/121276468300](https://github.com/Joker20380/family_connect/actions/runs/40228994539/job/121276468300) | 3163 PASS/54 FAIL/192 SKIP |

All three full suites actually ran; errors0,7 subtests passed in each. The extra34
headless skips are the new display-required cases, executed separately in GTK CI.
Control/phase0 retain the observed readiness-adapter local-port collision.
Docker now has54 failures versus historical53; the additionally observed
`tests/test_readiness_receipts.py::test_ui_unavailable_server_ack_is_authoritative`
fails at line130 (`observe(...)` is False despite `ACK_RECEIVED`). Cause is not
established; no fix, rerun, xfail or suppression. The preserved Docker artifact
12612094100 has ZIP SHA256
`44d68e48092a6dc2aed940b5192f8dfe52e73141826c7fdf833d59ca2c401ce0`.

Current voice job121276468063 PASS is not resolution of historical voice/Windows
observations. Native/Auto/DIRECT gates above were local, not an untriggered CI job.
CI package artifact12612004320 (ZIP SHA256
`b91871f3dffee27b23132cadc17175860ae43bfd7f298c08e2ac62c2d8000487`)
is a separate standard system rebuild with its own identity, **not** the exact
local candidate hashes above. No acceptance transfer or system-ID reuse for its
new bytes. Automatic documentation-only CI is not a new product candidate.

Existing control/phase0/Docker residual54/54/53 failures and voice/Windows
observations remain open; mandatory suites are not disabled or repaired here.
Package/evidence commit `c32e728bdbc8cdd493a629c5c3de4bf540814cef` was also pushed
normally and remote main matched. Final local artifact/system/.4 hashes rechecked,
source scope unchanged, JSON/local links/shell syntax/whitespace/secret-pattern
and staged-scope checks PASS; public-source guard2926 index entries/0 blocked.
All task containers exited/removed; synthetic fixtures only. Parallel ops edits
remain preserved outside these commits. Overall CI is **not green**.

Rollback stays explicit matching system reinstall only when idle/cleanup confirmed;
user uninstall preserves state and the independent root runtime. Historical .4 is
retained as evidence, not rewritten or re-labelled. No deployment is authorized.
No unfinished R2 source/package work remains; review is the next gate, not live
E/F. L04.1 **IN_PROGRESS**. STOP after source/package checkpoint.
NEXT — **review L04.1-LIVE-2-R2**.
