# CONTROL-HA — mailbox cleanup settlement, 24 November 2026

## Scope and fault

Selected CONTROL-HA-20261123 / HA-02 continuation after
[support-worker admission](2026-11-24-control-ha-support-admission.md). This closes the specific
bounded-reader-join gap documented there, not all installed runtime or fleet completion gates.
Previously `RoutedMailbox._connection` joined its reader for one second but did not check whether
the thread stopped. A successful mailbox exchange could therefore leave the worker's admission
scope while its reader was alive. A detach/remove/join exception could also skip subsequent
cleanup, including session-lock release.

No RU/NL connection, production state/key access, service/unit/environment/image change or
deployment occurred. No client/build/catalog/invitation version or public artifact changed.
Existing guardian/receiver/OWNER candidates remain unapproved and uninstalled. This is a source
checkpoint, not a client release, runtime rollout or HA-02 acceptance.

## Implementation

- `messenger/routed.py` keeps the existing one-second reader-join bound but checks `is_alive()`.
  A live reader raises `MailboxError('cleanup_incomplete')`; it is not a successful close.
- Cleanup callbacks attempt detach, explicit socket close, started-reader join/check, interface
  removal and session-lock release even if an earlier step raises. An unstarted thread is not
  joined; partial interface registration/start failure still closes and releases resources.
- Cleanup exceptions become the same sanitized terminal error. Neither route fallback nor the
  delivery controller's automatic transient retry can turn that failure into success. Existing
  delivery state presents `exchange_failed`; a later explicit/periodic request may retry normally.
- With the existing opt-in support gate, the exception leaves the durable pending marker.
  Already committed relay/outbox state is preserved, not rolled back. Reader exit or a subsequent
  successful exchange does not remove the earlier uncertainty or authorize capture.
- The shared transport fix applies to future support/Linux/Android source builds. Normal routes,
  message formats, identities, consent, ACK semantics, retry limits and dependencies are unchanged.
  It neither kills arbitrary threads nor weakens source/gate permissions to obtain a PASS.

The explicit `clients/shared/control-ha-mailbox.json` and reversible `.patch` record this delta
against sourcea6e8a019. Accepted Android106/subscription119/support1 hashes and patches are not
rewritten. Reference tests reverse this delta first, then all prior adaptations, to recover the
original accepted sources byte-for-byte. This provenance is not platform release acceptance.

## Verification

Python3.14.4; all17 package versions in the provisioning/messenger lockfiles match. Tests use
temporary synthetic encrypted stores, identities and owned local relay processes only.

**153 tests PASS /0 skips,41.24s**, including16 new cases:

```text
/tmp/fc-control-ha-20261123/venv/bin/python -m pytest -q \
  messenger/tests/test_routed_cleanup.py messenger/tests/test_support_capture.py \
  messenger/tests/test_support.py messenger/tests/test_support_security.py \
  messenger/tests/test_subscription_notifications.py messenger/tests/test_delivery.py \
  messenger/tests/test_linux_mailbox.py messenger/tests/test_android_carrier.py \
  tests/test_support_package.py tests/test_capture_gate.py
```

Real localhost TCP/RNS/LXMF support exchange commits one relay message, verifies reader exit
while the gate marker is still present, then verifies the recipient-storage ACK and idempotent
message identity. Separate tests inject a stall after the real TCP reader loop exits or raise
after native detach: committed relay state remains, capture refuses, and later successful native
exchange leaves the original marker intact. Test-owned stalled readers are explicitly released
and joined. All relay processes are closed; native interface registrations return to baseline.

Native Unix socketpair/interface tests cover normal reader teardown, failure after registration
and failure before thread start; only their mailbox handshake is substituted. Fault-injection
unit cases verify every cleanup stage still runs, timeout is not termination, errors are opaque,
route fallback cannot hide cleanup failure and controller automatic retries do not occur.
Existing Linux and Android **Python carrier** tests are not GUI, JNI, device or VPN acceptance.

Additional source-provenance/package run: **19 PASS,2 FAIL /2.86s**. These failures are retained,
not hidden in the focused result:

1. `test_announcement_contract_pins_existing_server_authority_and_exact_actions` fails because
   `control/friends/notices.py` and `scripts/service_notices.py` already differ from the old
   announcement pins in basea6e8a019. Both current files are byte-identical to that base; this
   task changes neither. The new cleanup/module hashes and full reverse-patch checks pass.
   The unrelated announcement baseline remains unresolved; no broad-suite PASS is claimed.
2. The HA virtualenv lacks GI, so Linux package-import checking failed there. Rerunning that
   test with system Python3.14.4/GI and the same pinned dependency directory under
   `dbus-run-session` gives **1 PASS /0.70s**. This is package import only, not rendering or
   interaction qualification. No packages, application environment or GUI settings were changed.

Documentation checks cover changed Markdown/local links and whitespace; external URLs are not
claimed as HTTP-verified releases. Built test kits, private state and raw evidence stay out of Git.

## Remaining gates and rollback

This proves termination of the owned route-reader thread, not every Reticulum watchdog/resource
callback, persistent runtime writer or remote operation after an ambiguous request. Installed
source/runtime/environment/unit/startup/shutdown bindings still need qualification, as do the
remaining native helper/stop-post/AWG, collectors and raw/manual write paths. A released local
session lock is not by itself a coherent-capture permit. The gate marker remains authoritative
for failed guarded work; unguarded clients do not acquire HA coverage from this transport fix.

The [fixed four-gate map](2026-11-24-control-ha-support-admission.md#fixed-ha-02-completion-map)
is unchanged: replication PASS in isolation; current inputs/trust, coherent all-writer capture
and independent custody/final combined recovery remain partial. Next is the remaining runtime
binding/settlement work and concrete joint activation/capture proposal, followed by the real
coherent interval and independently approved current inputs/custody/recovery. No new stage,
percentage or calendar estimate. Existing bounded management-write-capture permission stands;
working-NL deployment and production cutover remain outside current authorization.

No live rollback is needed. Revert this source/provenance delta together before any future build;
do not rewrite accepted client references or published artifacts. If a later approved activation
fails, abort capture before reverting its code/configuration, preserve committed message state
and all pending markers for reconciliation, and retain the previous approved package/argv. Never
restore product databases or delete markers merely to make capture pass. Source/tests/docs are
committed and pushed on the existing feature branch; main receives navigation after SHA readback.
