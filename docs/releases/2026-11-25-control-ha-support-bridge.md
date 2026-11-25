# HA-02 — reversible legacy support admission, 25 November 2026

Selected CONTROL-HA-20261123 / HA-02; continuation of the
[exact installed-shape candidate](2026-11-25-control-ha-support-overlay.md).
This closes a bounded source/qualification slice, **not the production transition, full runtime
writer boundary, coherent capture or stage2 acceptance**. No new numbered task is selected.

## Mechanism and scope

`scripts/control_ha_legacy_support.py` prepares an exclusive private one-use CPython3.14 remote-exec
request. It binds PID/start/boot/command/cgroup, the bridge bytes, all19 exact installed Python
sources and the closed baseline manifest. Inside the target it checks critical loaded main,
handler/server-constructor and delivery method code against those sources. It only proceeds while
the main thread is in the idle serial `handle_request` loop, not a partly accepted connection,
running handler, periodic update, startup or shutdown. Changed bytes/code and expired/replayed/
unknown requests refuse before changing admission.

The bridge temporarily clears only delivery's online admission under its own condition. It does
not call `update`, cancel the current attempt, change its generation/result, discard pending work,
close the controller/store/listener or send a signal. The main loop is paused by the same-thread
callback. Existing delivery is allowed to finish; leftover `chat-route` readers must join within
the request's remaining budget, and unrecognized threads/native tasks/remaining children refuse.
Known Reticulum background threads are counted, **not drained**. The temporary online value is
restored in `finally`, notifying the worker even after a failed receipt or deadline. Restoration
does not depend on the submitting controller surviving. Requests have a finite monotonic budget
of at most15s; this bounds waits, not arbitrary OS filesystem scheduling latency.

There is deliberately no stop/commit option. `drained.json` describes only the checked serial IPC/
delivery/route-reader scope. Every result has `capture_permitted=false`; runtime drain and old
external-outcome settlement remain false. The main loop resumes on callback return; an external
readback must verify actual restoration, not infer it solely from a prepared/restored receipt.
This is not a full in-memory module attestation or a supervisor for unexpected external SIGTERM.
Do not submit a stop concurrently or use the probe to approve the unsafe old shutdown policy.

The isolated RNS1.5.1 runtime exposes four persistent jobs: Reticulum jobs, transport jobloop,
traffic counting and inbound dispatch. Periodic/cache/identity persistence, queued asynchronous
work and exit handlers still need closure. Source inspection confirms that some loops have no
ordinary stop flag; setting Transport's flag or joining only chat delivery is not sufficient.

## Qualification

Final **55 checks PASS/0 skips**,67.31s:30 new bridge cases and25 existing packaging regressions.
The bridge cases launch the actual installed interpreter with `-I -B` and copies of the19 unchanged
installed sources; only mailbox test inputs use synthetic hooks. The service UID is the owner in
these tests, not `fc-support`. No live keys, product data, external destinations or working IPC are
used. Real RNS threads and a real loopback TCP route reader participate.

```sh
FC_TEST_SUPPORT_BASELINE=/opt/family-connect-support/app \
FC_TEST_SUPPORT_PYTHON=/opt/family-connect-support/venv/bin/python \
python -m pytest -q -ra tests/test_control_ha_legacy_support.py \
  tests/test_package_support_capture.py
```

Coverage includes idle admission hold/resume, delivery completion with an encrypted commit,
post-commit lost acknowledgement, child completion, blocked reader, unfinished delivery timeout,
unknown worker/remaining child, changed loaded code, serial IPC/incomplete header, request/source
drift, replay, receipt failure and controller exit. Fresh interpreter readback follows the owned
synthetic worker's normal exit after its delivery has completed. It does not bypass the store's
exclusive ownership lock or imply remote settlement. Synthetic process groups are cleaned up;
all private evidence remains outside Git.

Earlier attempts are retained, not added to the55 unique tests: first21 PASS/4 failures included
three readbacks incorrectly attempting a second owner of an open encrypted store, and a deadline
shorter than the idle selector wakeup. Second29 PASS/1 failure expected an incomplete IPC header to
remain writable after its original5s read timeout. Tests now respect actual store ownership and
the original socket timeout; the bridge still refuses a partial accept. The TCP reader fixture
also supplies its peer address, as real routed transport does, avoiding unrelated teardown noise.
No production check was bypassed to make the tests pass.
Four changed documentation files/1123 local-link targets and whitespace checks PASS.

## Actual working state and access

Read-only16:22:44UTC: `family-connect-support.service` active/running PID2022541,0 restarts,
no daemon-reload warning. All19 source hashes match the retained baseline. Effective policy is
still control-group/SIGKILL/40s, with no installed gate or candidate. No live bridge was submitted;
no service/unit/source/container change, product/public version change or RU/NL connection occurred.
OWNER containers were not requalified in this slice; their earlier observation is historical.

The authenticated terminal's normal sudo timestamp expired. A new GUI password dialog was opened
as already requested, but authentication did not complete (`Authentication required but not
attempted`). No password was captured and no alternate privilege route was attempted. Re-reading
the private HMAC unit drop-in also fails with PermissionError, so this checkpoint does not claim
a new byte-for-byte observation of all original unit files. Their previous privileged copies
remain private. Authorization still stands; technical authentication is required for a live probe.

Private locator: `/tmp/fc-ha-support-bridge-20261125`.

| Evidence | SHA-256 |
| --- | --- |
| Final55 JUnit | `e371a5e525ab4132a31dbacb03b6460a2be6b28f00ff1947229abe0aad25394b` |
| Working readback | `df95c5a1bcc024f46fd109c12be67b198947661848c3f7bb36ef8a302eeb2d4a` |
| Initial25-case attempt | `1214096bc4442268524e70d2e5e9790a02bc6da79a7f47a03dfb9b0e7013dd0b` |
| Second30-case attempt | `b83c1940023a77b72590ed538d6537fa12117717667920b28c69dc61160fcea6` |

## Rollback and next boundary

No production rollback is needed. Source revert removes only the optional bridge and its fixtures;
the candidate/source contract is unchanged. A later live probe must bind fresh privileged prestate,
stage private files for the actual service UID, use a bounded request and independently verify the
same process/source/unit and resumed malformed-request handling without sending chat messages.
Unexpected context/thread/source refusal is an abort, not permission to loosen the checks.

Next remains authenticated live probe, RNS periodic/queued/exit persistence closure and independently
supervised safe stop/replacement/rollback. Never use ordinary old TERM/40s shutdown, install only
the new kill policy, rewind product stores or clear uncertain markers. Installed manual/OWNER
coverage, coherent fleet capture, independent current trust/custody/approval and full post-ACK
recovery remain. Isolated replication PASS; same three HA-02 gates partial. No HA-03, automatic
failover, release claim or new completion ETA.
