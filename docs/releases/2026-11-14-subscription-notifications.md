# SUBSCRIPTION-NOTIFICATIONS-1

## Continuation — qualified preparation, awaiting final gate/merge

Executable/reference headac3479bfa4f8b190826182fb9633d78a7fdfb993 pushed; remote SHA
verified. Local exact-lock core/messenger/paid/subscription422 PASS, panel48 PASS,
reference/package25 PASS and root collection6164 PASS (overlapping selections).
Hosted route43591863039, messenger43591863077, panel43591863067, paid43591863176,
readiness43591863215, Linux voice43591863049 and candidate43591863079 PASS.
Phase043591863104 failover job132438099607 completes **all** build/provision,
failover/auth/offline/revocation steps successfully. Artifact14112893152 SHA256
507e001ecc5df5aea75586df0cf6c8ed4a9843f23d453d1884ed7a60b936d8e0 retained privately;
failover1 switch/16MiB, offline16MiB, unauthorized denied, revocation1.115s.
Its build log is rate-clipped during inventory output; step success is not used as
a substitute for completed standalone full-suite results, which are still pending.
Author-side continuation review5904249423 is recorded; no independent approval claimed.

Actual preflight: local joker-XPS/joker, support userfc-support, accepted main unit
RuntimeDirectoryPreserve=yes and mounted directory inode333786. Existing console
image50de6f25a04c and separate publisher retained. Root sudo still requires an OS
interactive prompt. Authorized RU admin connection independently confirms root on
box-932982; the restricted collector credential is not repurposed for administration.
Canonical SQLite backup and isolated integrity/full-table restore comparison PASS.
Panel pg_dump/isolated PostgreSQL17 restore PASS (nonempty auth_user), no live restore.
Current canonical source read:4 events,1 subscription/1 future boundary,0 expired
boundaries. This is a read-only preflight, **not** a production notification baseline.

Prepared kitac3479bf:73-file manifest PASS, tar SHA256
a80846f6b4b9961d06251c13fdd50046f9b7bf3e450652a54b0b362fd975634e.
Only four app modules differ from installed support. Minimal install bundle SHA256
16284251df81423d772f0b808ad89cd7863924239eb50d7e7cd230c0422e6313;
no HTTP archive installation. Prepared five-file panel overlay image
sha256:61e4df54f1e1b83011b03427ec96e8941f9060173f7f756cbb4f1979fac81ad7,
actual source hashes/syntax PASS; resolved Compose differs only in console image and
pull policy. Existing commands/environment/volumes match the running container.
Both panel images saved privately; archive SHA256
ae77042cc9330672aba57097a951e048ac600afa6bece9c31cd2fb8523e8fb53.

Fixed-host helper and exact sudo command/checksum are in the operator runbook.
Four isolated helper checks cover pinned-bundle tampering, every-record decryption
and unchanged backup bytes, baseline/cursor/job/history preservation and actual IPC
request framing. Root stop/backup/install/enable/multicycle/restart phase is **not
executed** yet. No production baseline, retrospective message or real automatic ACK.
Helper/source capsules, credentials and raw private evidence remain outside Git.

## Continuation — reference contract

Historical support commit10d353d8 changes chat/local/store and introduces support.py;
all four are pinned in a separate support1 delta, including patch checksum and
before/after hashes. Both106 manifests reference it; accepted106 hashes/inventory,
119 intermediate hashes and subscription119 patch are byte-for-byte preserved.
Tests reverse support, then subscription119, then platform routing and check every
accepted module against106. Parameterized checks report each module/dependency;
AST closure verifies relative imports including the new support dependency.
Reference/package25 PASS; collection6164 PASS in exact core environment with system
GI appended via local .pth (also inherited by package subprocess). Initial package
attempt lacked GI in its child process; corrected environment, no skipped check.
Late-ACK commit0950bba0 pushed and remote SHA verified. Final hosted/full runtime
gates and administrative installation are still pending; no full-CI PASS claimed.

## Continuation — late stored ACK

Preserve superseded/expired processing states; reconcile persisted delivery status
even for terminal jobs. IPC reflects the actual linked message immediately, before
the next dispatch. Panel distinguishes delivery from cancellation/expiry. Valid
late ACKs cannot revive attempts, enqueue a second message or mutate entitlement.
Real mailbox→terminal job→client storage→signed ACK→IPC/panel tests PASS for both
terminal states; isolated second recipient stays empty. Existing Store receipt
validation is unchanged. Late explicit expire aliases terminal natural jobs only;
original text/request/message IDs stay fixed (all terminal states covered).
Exact-lock scoped support50 PASS; panel48 PASS. Still source-only, no installation
or production baseline. Host joker-XPS, user joker: sudo still requires interactive
authentication; a fixed-path verified installer must be prepared before owner action.

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
