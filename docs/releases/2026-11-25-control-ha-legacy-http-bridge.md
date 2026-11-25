# HA-02 — legacy HTTP main-thread drain bridge

25 November2026. Selected task:CONTROL-HA-20261123 / HA-02. This is receiving adoption
work, not a new stage or acceptance gate. [PLAN](../PLAN.md) · [STATUS](../STATUS.md) ·
[Qualified installed-shape candidate](2026-11-25-control-ha-receiver-overlay.md).

## Why this approach

Actual RU inspection binds PID43082 to `/usr/bin/python3.14`, the exact legacy archive and
loopback port18086, not the source default18084. CPython3.14 provides `sys.remote_exec`:
its supplied script runs at the next opportunity on the target main thread. Submission alone
does not attest execution. This avoids injecting native code, replacing a running archive,
changing systemd kill policy underneath the legacy process, or killing daemon request threads.

`scripts/control_ha_legacy_http.py` prepares a private exclusive spool containing a source
copy, pinned launcher, short-lived request and durable receipts. PID/start/boot/command/cgroup,
baseline archive SHA, bridge bytes, main-thread identity, exact old main/serve-loop frames,
loopback handler, both native retention targets/events and Python/native thread coverage must
match. An interrupted partial accept or an unknown worker refuses the hook. Neither a thread
count alone nor an empty queue is accepted as settlement.

While the bridge occupies the main thread, the old application cannot accept another request.
The socket remains listening: TCP connections can queue, but no new application handler runs.
Already admitted handlers and their children keep executing. Handler joins are deadline-bounded;
an unfinished handler or partial headers abort before changing retention/listener state, and
returning to the old main loop automatically restores application admission.

Probe mode changes no retention flags and returns to the same loop after those joins. Stop mode
first persists explicit `OLD_EXTERNAL_OUTCOMES_NOT_ATTESTED`, then signals both retention
events, joins their real threads, verifies no local children/other threads, and asks the native
serve loop to return. It does not send TERM/KILL or call `server.shutdown()` from its own main
thread (which would deadlock). A caller must independently observe process exit: the last hook
receipt is only `RETURN_TO_EXIT`, never an invented exit/recovery acknowledgement.

After retention stop begins, a stalled worker or failed durable receipt holds application
admission closed; forced termination is not allowed. There is intentionally no pretend timeout
rollback from an unknown write. This is why the bridge is not a complete unattended deployment
controller. A separately qualified replacement/rollback guard is still needed before production
stop. Preserved legacy uncertainty must carry forward: local thread/child completion cannot
prove every historical remote effect/ACK, authorize coherent capture or clear a gate marker.

All launcher exceptions are contained so replay, missing requests, bad source pins and receipt
failures cannot escape into the product main loop. Receipts are atomically linked without
overwriting prior results, file/directory-fsynced and private. Stale queued execution refuses
before changing service state. No key, database, profile or raw diagnostic data is emitted.

## Qualification

Final focused run at14:25:46UTC: **64 PASS,0 skips**,45.23s pytest wall time:

```sh
FC_TEST_RECEIVER_BASELINE="$BASELINE" \
FC_TEST_HTTP_RUNTIME="$QUALIFIED_CANDIDATE" \
FC_TEST_SYSTEMD_HTTP_DRAIN=1 \
python -m pytest -q -ra tests/test_control_ha_legacy_http.py \
  tests/test_friends_http_lifecycle.py tests/test_package_receiver_capture.py
```

All19 new bridge tests use actual CPython remote execution into an owned process running the
retained installed archive. Coverage: same-process probe return, natural old-loop exit, actual
native feed export and child completion, caught partial export failure, both real retention
workers, handler deadline rollback/retry, queued new HTTP requests, incomplete headers,
unknown threads, stale PID/deadline/source/request fields, replay and launcher failures.
Existing candidate lifecycle cases include real user-systemd stop/child completion. No fixture
systemd units remain after cleanup. Python3.14.4/pytest9.1.1 and all26 control/identity pins match.

The first fixture attempt assumed the new export helper existed in the old archive; it failed
before starting a receiver. The fixture now instruments the actual legacy `Notices.export`
boundary, leaving the old main/handler/retention code in use. It does not substitute the fixed
candidate exporter when qualifying old-process completion. Native partial export still produces
503 and incomplete outputs; the bridge preserves uncertainty instead of falsely accepting them.

## RU execution and reconciliation

Only probe mode was submitted on RU. Source/requests/receipts are staged in a new private
directory under `/opt/apps/family_connect`; they are not a replacement serving archive, unit,
timer, capture gate, public artifact or installed HA backend.

The first precheck attempted source-default18084 and received connection refusal before any
hook submission. Actual command/listener inspection established port18086. The next hook
completed `PROBE_RETURNING` after one admitted handler, but the controller's immediate unit
comparison asserted `RUNTIME_CHANGED` without retaining the differing fields. That attempt is
not claimed fully verified. Subsequent readback confirmed unchanged PID/start/command/cgroup,
active/running with0 restarts and HTTP501; its invocation was not replayed.

A fresh separately named probe retained both unit snapshots and completed at
**14:29:12.380614UTC**,0.331s submission-through-verification (not a measured outage duration).
It observed0 handlers and2 retention workers; application admission resumed naturally. Both
unit snapshots are identical: PID43082, active/running,0 restarts, `Restart=no`,
`KillMode=control-group`, SIGTERM and90s timeout. Process binding and archive SHA also match;
loopback GET `/` returns the expected501 because this endpoint does not support GET. That is
listener/main-loop verification, not an end-to-end client or device-write acceptance test.

No stop/restart, candidate activation, unit policy, product database/feed/version, installer,
catalog or invitation-page change occurred. No NL or neighbouring service was contacted.

| Evidence | SHA256 |
| --- | --- |
| Old archive, unchanged | `4e2df679761ba9e7af74128984ef2e19e8e7b228f1cc85b36d50be2b0bc24ce8` |
| Bridge source | `739f6819fd0288f37acde1463b8426049362021dc3de48700fe0b8d1d63db199` |
| Final JUnit | `62e2abd72c7724bb2437dec986289583f8a4ec0579ff1641c409321941a6405e` |
| Verified RU probe receipt | `0cf2a900003e034974645d681a6d5d7a577772eb75f19a30ba07d4db51158ae0` |

Private evidence locator: `/tmp/fc-ha-legacy-http-current`. Failed attempts, verified result,
tests and native fixture states are retained, not committed. The remote private spool remains
available for audit; never delete a queued script before its execution/expiry is reconciled.

## Rollback and fixed remainder

The live probe rolled back by returning to the original loop; serving artifacts/unit never
changed. Source rollback is an ordinary revert. For future stop, preserve old archive/unit
prestate, use an independently checked exit observation and a rollback-guarded paired archive/
unit activation. Do not stop the service with its current default TERM policy, start a second
writer, install only the drop-in or restore stale DB/feed contents. If a post-retention drain
stalls, retain evidence and keep admission closed until work is independently settled.

Next is that paired replacement/rollback qualification and activation, not another broad source
rebuild. Support/manual writer coverage, guarded OWNER integration, complete fleet coherent
capture, independent custody/trust/approval and final current/post-ACK recovery remain in the
same three partial HA-02 gates. Replication remains PASS in isolated rehearsal. There is no
measured completion date; the old1–2-day estimate is not a validated schedule. HA-03..05 and
automatic RU-independent failover are not enabled by this checkpoint.
