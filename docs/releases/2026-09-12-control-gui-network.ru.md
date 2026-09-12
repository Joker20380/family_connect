# Linux GUI/control coordination and short network test — 2026-09-12

Baseline: `4cb1423` plus the uncommitted Stage5 reference implementation from the
previous checkpoint. This change remains local/uncommitted; no release, remote CI,
helper upgrade or server mutation. Desktop0.2.9/catalog8, installed Linux0.2.7,
TCP Setup0.1.0 and gateway0.2.1 versions remain unchanged.

## Closed locally: shared Linux GUI/control operation ownership

- Self-contained backend arbiter preserves the six-file Linux archive. Nonblocking
  flock serializes processes; reentrant thread exclusion covers nested driver calls.
- GUI connect/disconnect/import/recover and TCP component installation participate.
  Provisioning holds the same lease across snapshot/stage/apply/health/commit/rollback.
  Fetch and ACK networking remain outside that connection lease.
- Atomic pending owner is persisted before stage/system mutation. Process death
  releases the OS lock but does not release durable ownership. Ordinary GUI operations
  and a different journal are refused until recovery with the same local journal.
- Journal IDLE/commit/finished rollback clears ownership; failed rollback or unreadable
  journal does not. Lost/corrupt/symlink/hardlink/unsafe coordination state fails closed.
- GUI polling takes a coherent snapshot, refreshes inventory/selection after external
  generation changes and cancels stale recovery intent. Recovery rechecks generation
  under the lock immediately before mutation. Automatic recovery preserves generation,
  so the existing finite retry budget cannot reset on every recovery attempt.

This closes the source-level sole-owner gap for the **updated Linux GUI and core**.
Older installed applications and manual NetworkManager/root commands do not honor
this lock. Coordinated distribution is still required; no unattended background
scheduler or Windows/Android native binding is claimed.

## Validation

- **402 Python tests passed**, two existing FastAPI/Starlette deprecation warnings.
  Previous Stage5 suite381 preserved; 21 new coordination checks include process/thread
  exclusion, actual `os._exit` crash, wrong-owner refusal, dangerous/missing state,
  all GUI mutation entry points, stale recovery/generation and STAGED/APPLYING/
  APPLIED_PENDING core crashes followed by GUI refusal and deterministic recovery.
- GTK recovery including new-generation selection and busy-control behavior passed
  on the current Wayland display with a test driver. No VPN operations in GUI tests.
- GTK state/poll/confirmation checks and **24 layouts** at 100/150/200/250% passed.
  An initial fixed-80-ms geometry assertion failed on both old and modified source.
  Harness now waits for stable initial Wayland size (bounded3s), then asserts unchanged
  redraw behavior. No product window geometry was changed. Portal session warnings
  occurred after the isolated dbus session ended; assertions passed.
- Full suite includes real two-process RNS commit/ACK/rollback regression. Native
  Windows/Android sources untouched; remote/native CI not rerun or claimed here.

## Reopened by explicit user decision: short installed-network acceptance

User confirmed short route/DNS/HTTPS/cleanup tests after GUI integration. No long
load test, additional device campaign, UDP blocking, second VPS or server change.
Existing installed TCP `fctcp75850269` to Family Connect gateway185.251.89.19 only.
Preflight refused existing WG/AWG/TCP sessions and routing ownership conflicts.
An independent systemd watchdog limited the test to120s; exact cleanup checked.

First harness called probes immediately after `systemctl start` on a Type=simple
unit. TUN was not ready, curl45 and DNS failures followed. The test stopped and
restored baseline state. This is a harness startup race, not evidence of a gateway
failure. [Initial record](2026-09-12-short-network-startup-race.json).

Second run waits up to12s for TUN, public route and per-interface DNS readiness:

| Check | Result |
|---|---|
| Direct HTTPS before VPN | 2/2 |
| Direct DNS before VPN | 1/1 |
| Service/TUN readiness | active/running, exit0 |
| Gateway bypass outside TUN | passed |
| Public route through TUN | passed |
| Per-interface DNS and ~. domain | passed |
| DNS through VPN | 3/3 |
| HTTPS through VPN | **4/6**, two curl28 timeouts |
| Correct egress on successful VPN HTTPS | 4/4 |
| Stop/interface/marker cleanup | passed |
| Full IPv4/IPv6 policy-rule restoration | passed |
| Table64630 empty and gateway route restored | passed |

[Ready-TUN record](2026-09-12-short-network-result.json). The run lasted17s; no
profile/key/binary was rewritten. Script exit0 signifies completed cleanup, not
that all connectivity probes passed. Watchdog timer stopped after successful cleanup.
Direct probes were a pre-test baseline, not simultaneous matched controls; these
results do not establish the origin of the timeouts or prove protocol blocking.

**TD-1 remains open:** short routing/DNS/cleanup coverage is positive, HTTPS stability
is not accepted. Next is bounded matched direct/TUN timing diagnosis. Prolonged load
and device tests remain deferred. AWG3.1 migration (TD-2) and Stage6 remain open.

## Files / rollout / rollback

Changed: `clients/desktop/backend.py`, `app.py`, `layout_check.py`, `recovery_check.py`;
`provisioning/application.py`, `transaction.py`, `runtime.py`;
`tests/test_control_channel.py`; `docs/STATUS.md`, `PLAN.md`, `ROADMAP.ru.md`,
`README.md`, `stage5-architecture.ru.md`, `reticulum-control.ru.md`.
New: `clients/desktop/tests/conftest.py`, `test_operations.py`; this report and its
two sanitized network result JSON files.

Coordination state: `~/.local/state/family-connect-operations/state.json`, mode0600
inside mode0700 directory. Pending value is a SHA256 of the canonical local journal
path, never a profile/path supplied by Reticulum. Do not delete state to bypass
pending recovery. Resume the same journal; after successful cleanup/IDLE the marker
clears. Rolling back code while a transaction is pending must wait for recovery.
No installed code was updated, so there is no binary rollback in this session.

Short test scripts retained locally at `/tmp/fc-control-gui/network-smoke.py` and
`network-ready.py`; they operate the existing installed component. They are not
production provisioning code. No secret profiles, private keys or raw credential
contents are present in these result files.

Local implementation SHA256 (no commit identifier yet):

- `clients/desktop/backend.py`: `f96852365d3c1725656eace52dfe81b5256b7acffb75a287d730285fe90d94de`
- `clients/desktop/app.py`: `889c015346b576bff402f239dc1d1dac74c1e1250d97d2e55e4999aa5b294177`
- `provisioning/application.py`: `ad73fcf01bd306480890ba482894ce3c2caab07c685451750664b72de52aa458`
- `provisioning/transaction.py`: `0b59d9b9e741ab81f246c69bfd6fbf69078df08487df943f81f4d4526abc57a3`
