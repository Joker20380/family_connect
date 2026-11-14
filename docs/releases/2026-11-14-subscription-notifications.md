# SUBSCRIPTION-NOTIFICATIONS-1

## 14 November10:57UTC — source qualified, deployment still pending

Code head `6cd2771f26cafd104997f8a0178ce7df48207c71`, ordinary push and remote SHA
verified. Hosted route43587126587, messenger43587126573, panel43587126690,
paid43587126669 and readiness43587126622 PASS. PR26 is ready for review, not merged;
author-side review5903950020 is not independent human approval. No new production
component is installed or enabled; administrative execution remains unavailable.

Fresh isolated core/identity/provisioning/messenger lockfile environment verifies
every installed pinned version and pip check:193 focused checks PASS;6150 root
tests collect successfully with system GI appended after locked packages. Separate
panel-lockfile environment verifies its pins:46 tests PASS, including the full new
mailbox/stored-ACK/IPC/device-card chain. Profiles are intentionally separate: the
panel lock pins newer iniconfig/pluggy/pycparser than the core lock. Initial shared
environment results below are retained, not used as exact-core-lock acceptance.

Reviewed73-file kit SHA256
`fdbc4b8394f05bb570c5341a3c3a4a4ac96b6063879174e55404707c70a51f98`;
unit syntax and documentation links/whitespace PASS. Kit is built, NOT installed.

Collection prerequisite source21cfe5e5 hosted phase0/failover43585268077 provides
the retained full Docker log (artifact14111040417): standard5793 tests,5510 PASS /
3 FAIL /280 skipped; root258 return0; snapshot31498 PASS. The three failures are
exactly the unchanged messenger-reference failures reproduced on entry main, listed
below. The Docker build therefore exits1 and actual failover/auth/offline/revocation
integration steps do not run. This is NOT full CI/failover PASS. Long general runs
for the backend head remain separately pending; no historical suite repair begun.

Still required: merge disposition, administrative host execution, consistent private
backup/restore rehearsal, installed component/pin checks, first-enable baseline and
multicycle/restart readback. Real-user receipt remains unobserved. The last production
readback has the same4 prior events; no synthetic payment, deadline change, message,
announcement, APK/release or production database mutation was performed.

## Entry and collection prerequisite

Remote main verified `1b186e15cc88302807a7927776b9a5ad1f428149`.
The original checkout and its uncommitted work are preserved; work continues in the
clean existing paid125 worktree fast-forwarded to main, on its existing upstream.
PR23/24/25, public beta125/catalog8, tablet109→125 and paid125/support acceptance
are retained. No APK, deployment, subscription or real message changed here.

Reproduction: collecting `tests/test_chat_service.py` alongside
`clients/desktop/tests/test_chat_service.py` exits2 with `import file mismatch`.
Rename only the server file to `tests/test_chat_service_sender.py`, update its
workflow reference, keep all three pytest testpaths and all tests. The inventory
subprocess inherits stdout/stderr; a subprocess regression verifies the original
failure detail is emitted before the nonzero launcher result.

Initial shared support environment: pip check PASS. With system GI appended after
the virtualenv packages, full collection6149 PASS; targeted sender/desktop/context
checks24 PASS. Initial collection without GI failed on desktop support-service;
prepending system packages instead caused five typing_extensions import failures.
These were environment ordering failures, not removed or skipped tests. Full hosted
CI and backend notification gates are NOT claimed from collection success.

## Source checkpoint and isolated acceptance

Read-only cursor/anchor feed pages128 APPLIED ledger records; events with identical
timestamps and backwards time are covered, including1005 committed records. It does
not consume the last-event endpoint or truncated panel history. Origin version and
actual deadlines derive the natural-ending key. A separate later canonical read is
required before enqueue; renewal/grace supersede stale endings. Explicit expiry
deduplicates that same boundary. No payment/schema/entitlement writer was added.

The existing encrypted sender store holds baseline, jobs, frozen identity/text/UUID,
cursor, outbox and request mappings transactionally. No automatic producer IPC is
exposed; the panel cannot substitute a service actor. Quota/TTL/source/binding errors
remain visible. The production device card and conversation distinguish jobs,
queued/relayed/stored messages and reasons. Stored ACK is never read status.

Local gates:317 support regressions PASS;46 panel checks PASS, including canonical
commit → producer → durable job → real support worker/mailbox → intended client →
stored ACK → actual panel IPC/device card.165 notification/paid/subscription checks
PASS. These overlap, not additive counts. Collection6150 PASS; new messenger cases
also run explicitly in their dedicated hosted workflow (outside root testpaths).
Existing beta125 protocol/upgrade tests remain unchanged; no emulator or phone rerun.

Tests cover first payment/extension/grace/expire/revoke, paid/grace natural expiry,
renewal/grace before enqueue, two recipients,1005 records, uncommitted rollback,
cursor/job rollback, enqueue crash before/after insert, committed unknown outcome,
lost read-only IPC response, restart, offline mailbox storage then client ACK,
missing/expired/revoked/changed binding, initial baseline atomicity/no historical
send, new events after restart, quota/backoff/TTL, late wording, source permissions
and no canonical change from incoming text. Raw evidence stays outside Git under
`/mnt/data/fc-subscription-notifications-20261114/`.

## Production preflight, not rollout

Fresh read-only gateway observation: loaded policy
`android-paid-108-119-123-125-v1`;64 devices/118 invites/1 subscription/4 events;
RU reconciliation applied, observed state age2.512s. Actual support worker active,
NRestarts0; installed source SHA256
`3efb9b5bf3ebeb4885b75755b6f455b191ffa3c19ad5cafeae4fe7698334ee36`;
installed unit SHA256
`6bf8cc2222c22981321c8bf2a7fd47af7306834979e5d10ded8ca59d7a176849`,
`RuntimeDirectoryPreserve=yes`. Existing panel image50de6f25 retained. No archives,
HTTP pins, services, subscriptions, bindings, history, keys or APKs changed.

Host administrative execution is unavailable to this process: `sudo -n true`
returns `sudo: interactive authentication is required`; no permission bypass or
alternate privileged-container host mutation attempted. Installation is NOT done.
The production notification baseline does not yet exist; no retrospective sends
or new real automatic receipts were produced. The four existing events are not
used to trigger acceptance messages.

## Remaining gates

Source checkpoint `a63e4d29c93a97d239e7245a0d9d97431160a8c9` pushed and remote SHA
verified. PR26 is not yet merged. Hosted route43586664982, panel43586665041,
paid43586664957 and readiness43586664978 PASS on that source. Code review adds a
saved maximum observed highwater, so source rollback cannot silently discard even
unprocessed records seen on a preceding page; explicit auto/manual request conflict
is also qualified. No production changes from this follow-up.

Linux voice43586664962 reports104 PASS /3 FAIL after collection. Exact failures in
`tests/test_messenger_reference.py`: `test_accepted_messenger_closure_and_explicit_platform_delta`,
`test_subscription_adaptation_reverses_to_unchanged_accepted106_sources`, and
`test_notification_reference_preserves_shared_sources_and_records_platform_limits`.
All three are reproduced independently from archived entry main1b186e15 (3 FAIL /
3 PASS); their tests, shared manifests and referenced messenger source are unchanged
in this task. The initial baseline reproduction missed one fixture dependency; after
including all declared manifest inputs, only the same three failures remain. No pins
are relaxed to turn them green. Full phase0/Linux suites remain separate from the
successful notification route and panel gates.

Final general-CI disposition and merge; administrative support-host execution;
consistent nonempty backup and restore rehearsal; guarded source/panel installation,
actual first baseline, multiple steady cycles, restart and protected-state readback.
See [operator procedure and rollback](../operators/subscription-notifications.md).
Rollback preserves the new automatic-outbox guard and all state; old unguarded worker
must not dispatch pending automatic endings. Never restore an old registry/history
over new events. No payment-provider integration, client-card polling or RU repair.
