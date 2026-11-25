# HA-02 — support writer graceful termination, 25 November 2026

Selected CONTROL-HA-20261123 / HA-02 continuation after the
[installed RU receiver](2026-11-25-control-ha-receiver-replacement.md). This is a support
source/qualification checkpoint, **not a working support deployment or coherent capture**.
The existing [support admission](2026-11-24-control-ha-support-admission.md) remains in use;
no new acceptance stage is introduced. Product/client/public installer/catalog/invitation
versions and signatures do not change. No production database, profile or key is modified.

## Actual installed prestate and technical access

Read-only OWNER observation at15:23:44.676804UTC finds `family-connect-support.service`
active/running, PID2022541,0 automatic restarts, no daemon-reload warning. It runs as
`fc-support`, group `fc-support-ipc`, from `/opt/family-connect-support/app`, without a
`--capture-gate` argument. Effective `KillMode=control-group`, SIGTERM, `SendSIGKILL=yes`,
`TimeoutStopSec=40s`, `Restart=on-failure` remain installed. Both existing drop-ins are retained.
The configured interpreter reports Python3.14.4; reading the other UID's `/proc/PID/exe` is
denied, so this is not an attestation of the running interpreter/in-memory code.

The installed application has19 readable Python source files. Three differ from the current
checkout: support worker, subscription notifications and routed mailbox. Missing admission/
lifecycle modules are not counted as unchanged. Do not deploy the broad commissioning kit
over this installed shape or infer that file hashes attest already imported code.

`sudo -n true` fails with `sudo: interactive authentication is required`. This is a concrete
technical-access blocker for installing/reconfiguring the root-owned system service, not a
request for the owner's already granted HA-02 permission. No password is collected, security
policy weakened, alternate escalation attempted or service stopped. Restore approved privileged
execution before the guarded installed-shape support transition; do not install its unit policy
alone over the old worker. Source qualification below does not require that access.

All three existing OWNER containers remain running/healthy with0 restarts. RU readback at
15:25:19UTC still shows the accepted receiver PID476518, active/running,0 restarts and no reload
warning. RU is not redeployed; no NL host is contacted. These are liveness observations, not
client E2E or settlement evidence.

## Fixed termination boundary

Previously the worker called `delivery.close(timeout=31)` once. A false return skipped store
close but allowed normal process exit, terminating a still-running daemon delivery thread.
The installed systemd policy can also signal its children and force termination after40s.
The general routed transport's bounded reader join could return a cleanup error while its
daemon reader still existed. A pending marker rejects capture but does not itself stop that
process exit from interrupting work.

- New `provisioning/support_lifecycle.py` installs idempotent TERM/INT handlers before private
  store initialization and restores them only after cleanup. Handlers set a main-thread flag
  without taking a potentially reentered lock. A startup stop finishes initialization
  and closes storage without opening the listener. No periodic work is scheduled after the loop
  observes the stop request.
- The existing serial IPC handler finishes before listener close. Delivery cancellation is
  requested repeatedly through the existing API until its actual worker thread exits; a false
  close result is never success and31 seconds is no longer a process-exit deadline.
- Support-only `SupportTransport` joins its owned routed reader to completion inside admission.
  A stalled reader keeps both the operation and delivery alive; no timeout silently transfers it
  outside the gate. Desktop/general routed transport behavior is unchanged. Detach/exchange
  failures still retain their durable uncertainty markers.
- Store close follows delivery completion. A busy capture gate delays close until admission
  reopens instead of bypassing it. Invalid gate/other cleanup errors propagate, never become
  a successful close. Only the original socket inode is removed; replacement paths are preserved.
- The commissioning unit is paired with `KillMode=mixed`, main SIGTERM, `SendSIGKILL=no` and
  `TimeoutStopSec=infinity`. Stalled work deliberately leaves stop pending for diagnosis, rather
  than killing it. This is not protection from OOM, explicit SIGKILL or host/provider failure.
- The closed commissioning package includes the new lifecycle module. None of these source or
  unit changes is copied into the working support installation in this checkpoint.

## Qualification

Python3.14.4/pytest9.1.1, existing control/identity environment. **106 focused tests PASS,
0 skips**,68.38s on final source. Eleven new lifecycle cases cover real CLI/startup/IPC/SQLite, repeated
termination, gate-held close, partial requests, child completion, failed external ACK retention,
socket identity and handler restoration. Existing native RNS tests now verify that a deliberately
stalled TCP reader retains admission/delivery until released, successful recipient ACK behavior,
and durable detach-failure refusal. Synthetic identities, plaintext and encrypted stores stay
only in disposable fixture directories, not production or Git.

```sh
FC_TEST_SYSTEMD_SUPPORT_DRAIN=1 /tmp/fc-control-ha-20261123/venv/bin/python -m pytest -q -ra \
  tests/test_support_lifecycle.py messenger/tests/test_support_capture.py \
  messenger/tests/test_support.py messenger/tests/test_support_security.py \
  messenger/tests/test_delivery.py tests/test_support_package.py tests/test_capture_gate.py
```

The actual user-systemd case leaves a delivery-owned subprocess blocked for41 seconds after
`stop --no-block`, beyond both old deadlines. Main and child remain alive, store remains open,
and state remains `deactivating/stop-sigterm`. Releasing the synthetic child permits its commit,
store close and exit0 without killing it. The final fixture uses a retained owned unit file,
not an unloaded transient unit's default fields, and independently reopens the encrypted store
to read back its committed record. Persistent-fixture rerun: **11 PASS/0 skips**,54.93s, followed
by the final106-case rerun after removing locks from signal handlers. All owned
test units are removed. A final readback confirms all19 installed support source hashes and
its PID/restart/state/reload fields unchanged from preflight.

The initial focused attempt had2 failures/8 passes: its synthetic transport constructed an
invalid empty `ExchangeResult`, correctly retaining uncertainty. Fixed the fixture's result
shape; no gate weakening or pending-marker deletion. Failed evidence remains private. The earlier
106-case run65.12s,11-case run and final106-case run overlap; they are not additional distinct tests.
Four changed documentation files/1115 local-link targets pass; whitespace checks pass.

## Evidence, rollback and remaining work

Private locator `/tmp/fc-ha-support-lifecycle-current` points to the retained source preflight,
test logs/XML and sanitized source bindings outside Git. No product database/key was copied.

| Item | SHA-256 |
| --- | --- |
| Read-only installed preflight | `3ef0c884bde96e982d29008d1892f0ca7fc194e55fc2d9b20258ae8b0300e9ca` |
| Lifecycle source | `00807e80958986a3fe13a3419f44f38c09d76a2962f0746dfd9f3358cb35dc57` |
| Worker source | `c9227a9fe267cd5aaf28e55b6582629bd630b2cfee4135df565cedc384f92a02` |
| Paired commissioning unit | `7414090f676eb1e181d5c7c0690d2624c91bce41c17d5954f9f1156252908054` |
| Earlier106 JUnit | `e321868cc89483a2d9c78664620c967c183285e517a2e8886da81f761774113a` |
| Persistent-fixture11 JUnit | `84e25e7ea8b54f13f7f8a3814937771280b25625a0428cb58cb7fd0ecaba5ad3` |
| Final-source106 JUnit | `77f1caab105864c638a5c2d0eaba01b81a397473acf774c6827b5185ff6b3b75` |

No production rollback is necessary. Source rollback must revert the worker/lifecycle/package/
unit changes together, never just a kill-policy setting over an unqualified worker. A future
installed transition must retain exact old source/unit/argv, preserve encrypted state and every
uncertainty marker, drain old work before switching, and have an independently supervised
code/config-only recovery. Do not rewind history, replay old notifications, clear pending
operations or force-stop the original service to manufacture a stopped prestate.

This proves the managed worker/reader stop slice, **not all Reticulum background persistence or
remote side effects**. Those still require exact installed runtime/closure binding and independent
old-outcome reconciliation before capture. Remaining selected work: privileged installed-shape
support transition, manual writer closure and guarded OWNER replacement; complete fleet joint
capture, independently approved trust/custody and combined recovery. Replication remains PASS
in isolation; the same three HA-02 gates remain partial. No HA-03 or automatic failover claim,
and no new unsupported calendar estimate. Do not repeat this source slice as another open task.
