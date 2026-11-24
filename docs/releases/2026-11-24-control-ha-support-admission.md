# CONTROL-HA — support-worker admission, 24 November 2026

## Scope and decision

Selected CONTROL-HA-20261123 / HA-02 continuation. The earlier
[OWNER IPC admission](2026-11-24-control-ha-admission-drain.md#owner-panel-and-publisher-continuation)
guards the panel request but does not guard asynchronous work after the support worker accepts
that request. This change adds the missing **opt-in worker-side source integration**. It does not
claim installed support-runtime qualification, coherent capture or HA-02 completion.

No RU/NL connection, production database/profile/key access, service/image/unit/environment
change or deployment occurred. Client/build/public installer/catalog/invitation versions and
signatures are unchanged. No live gate was created or enabled. Existing receiver/guardian/OWNER
candidates remain unapproved and uninstalled; there is no new public release.

## Implemented boundary

`provisioning/support_worker.py` accepts optional `--capture-gate`. The directory must already
exist with the existing gate's0700/0600 ownership and identity checks; the worker never creates
it automatically or silently falls back to an unguarded path. Omitting the flag preserves the
existing behavior. A worker with a different UID needs its own gate and independently approved
joint participant; do not share the panel's directory by weakening permissions.

The shared admission decorator wraps the existing gate plus external-operation uncertainty:

- Store open, owner/inbox initialization and store close are admitted. CLI admission precedes
  private-key reads and database/runtime initialization. A refused startup does not open state.
- Binding updates, enqueue/send and validated IPC invocation are admitted. The handler covers
  binding refresh, dispatch and scheduling together. Nested work uses one durable marker through
  commit. A closed gate returns bounded `capture_busy`, without refreshing or scheduling work.
- Each background mailbox exchange independently enters the worker gate before refresh/network
  construction and remains inside through the transport's `close()` return. It is not covered
  merely because an earlier panel RPC completed. Admission refusal becomes the existing delivery
  controller's transient `busy`; periodic scheduling can retry after admission reopens.
- Notification ingest, dispatch and refresh, periodic scheduling and outbox expiry/retry mutation
  are admitted. A nested failure caught by notification code still retains uncertainty.
- Exchange/cleanup failure or process death leaves a durable pending marker. A later success
  cannot remove the earlier marker or make drain pass. Queue acceptance is not delivery ACK;
  queued messages retain their IDs/status and may be included in an otherwise qualified snapshot.

`scripts/package_support_chat.py` includes the admission helper and the existing shared gate in
the closed commissioning kit. Its reproducibility and imports outside the checkout are checked.
No existing service unit, schema, message format, retry policy, cryptographic identity, consent,
recipient binding or UNKNOWN-operation reconciliation rule is changed.

## Verification and limits

Focused verification uses Python3.14.4 with all17 installed packages matching the provisioning
and messenger lockfile version pins. Synthetic encrypted stores, keys, identities, Unix sockets
and owned child processes stay in test temporary directories, not product storage or Git.

**123 tests PASS /0 skips**,12.08s;20 new support-admission cases. The focused suite covers
`messenger/tests/test_support_capture.py`, `test_support.py`,
`test_support_security.py`, `test_subscription_notifications.py`, `test_delivery.py` in that
directory, plus `tests/test_support_package.py` and `tests/test_capture_gate.py`.
New tests exercise actual SQLite commit under one marker, real Unix IPC refusal before work,
background retry after reopening, drain refusal during blocked cleanup, swallowed notification
failure, changed gate-inode refusal, preserved queue/idempotency and an owned subprocess killed
inside the worker exchange. Death leaves pending and subsequent drain refuses. No skipped test
is used as a passing gate. The final suite also covers existing support, notifications, delivery,
closed package and gate contracts; earlier focused55/18-test runs overlap, not additional totals.
Documentation: four changed documents/1058 link targets, zero local-link errors; whitespace
checks pass. External URLs are not claimed as HTTP-verified release artifacts.

The transport in the new exchange/death cases is a synthetic adapter. Waiting for `close()` does
not independently prove all installed Reticulum threads or remote effects have completed. The
installed support executable/dependencies/runtime/environment, collectors/feed writers, actual
transport cleanup, manual/raw Store access and joint-gate bindings still require qualification.
Existing `RoutedMailbox` reader joins are bounded; this source checkpoint does not turn a join
timeout into proof that every thread stopped. An explicit shutdown encountering a closed or
invalid gate refuses store close rather than bypassing admission; operational lifecycle handling
must be included in activation qualification. No marker is automatically deleted to recover.

## Fixed HA-02 completion map

These are the existing acceptance gates, not additional stages. Test totals or source pushes
do not measure percentage completion. Previously quoted1–2 and2–4 day estimates were withdrawn:
they did not account reliably for the remaining integrated work and independent participation.
No replacement calendar promise or unattended background execution is implied.

| Existing acceptance gate | Current result | Evidence still required for completion |
| --- | --- | --- |
| Replication and failure behavior | PASS in isolation | Retain the accepted evidence; no repeat or production cutover is required by this checkpoint. |
| Current inputs/trust | Partial | Independent approval of the actual current authorities, checkpoint and exact source/runtime/gate configuration; local self-generated receipts are not independent approval. |
| Coherent all-writer/in-flight capture | Partial | Finish helper/environment/stop-post and AWG/mailbox/support native completion; bind collectors and manual writes; approve any required activation, measure the real joint interval and capture all scoped stores/files/operations at one point. |
| Independent custody/final recovery | Partial | Independent off-laptop key/access availability and one combined recovery from that approved coherent point, with post-ACK readback, stale-copy refusal and verified cleanup/rollback. Earlier cold-runtime and retained-state rehearsals are not repeated as new tasks. |

Source admission now covers the support-worker entrypoints identified here; do not reimplement
or repeatedly retest that same slice as a new acceptance gate. Next work remains **native
completion/runtime bindings and the concrete joint activation/capture proposal**, not another
cache/census repeat. The current NL authorization still excludes changes to working services;
any proposal needing that change must expose the actual scope rather than infer deployment
permission from a source push. Owner's existing bounded management-write-capture permission
does not need to be requested again merely because a runbook describes that operation.

## Rollback and publication

This is a source-only checkpoint: omit/revert the worker admission changes and kit source update
without restoring product databases or changing SSH. No live rollback is needed. For any future
approved activation, retain the prior kit/unit argv and gate evidence; abort the joint capture
before reverting worker configuration. Preserve durable pending markers for independent
reconciliation, never erase them or disable the gate to make a capture pass. Normal service
resumption after an aborted capture is not acceptance of that capture.

Source/tests/documentation are committed together on the existing feature branch and pushed
non-force; main contains navigation only. Raw private state, test keys and built capsules are
not staged. Remote commit identity is recorded in the main navigation after verification.
