# SUBSCRIPTION-NOTIFICATIONS-1

## Final production acceptance — 14 November13:05UTC

**DEPLOYED_VERIFIED; new real automatic receipt NOT_OBSERVED.** Subsequent committed
APPLIED payment/renewal, grace, expire and revoke operations, and valid future paid/
grace boundaries, now produce addressed official-support messages on public beta125.
This is not a new APK/catalog release or automatic refresh of the subscription card.
Card opening/Refresh still reads the existing authenticated subscription endpoint.

PR26 merged normally as `fe6a317c2ee115b2bc3c3f5e9d65fb119d43fa07`, retaining ACK
commit0950bba030cb376b01e4d5a17dc355ead53dee67 and reference/source commit
ac3479bfa4f8b190826182fb9633d78a7fdfb993. PR27 documentation merged023dcd92; the
production executable source remainsac3479bf, not the later documentation head.
Review is author-side, not an independent approval claim. The original dirty checkout
and its untracked work remain untouched; deployment/readback used the existing worktree.

### Actual activation and component identity

The owner executed the pinned helper on **joker-XPS**. It finished12:53:21UTC with
`installed_baseline_observed` and `cycles_restart_acceptance=PASS`. Helper SHA256
4bf466a3f802462e5a297f2d7eb51c5dcd800cff853996141c2c68e187a040a6 and bundle
16284251df81423d772f0b808ad89cd7863924239eb50d7e7cd230c0422e6313 are unchanged.
Support modules are under `/opt/family-connect-support/app/provisioning`; service/
timer and the worker drop-in are under `/etc/systemd/system`:

| Component | Installed SHA256 |
| --- | --- |
| subscription_notifications.py | 3792bbbc37ace2188f04148e936bf44acb2fdd992285d134448e7be173ae839e |
| subscription_collector.py | 6bfe32119ecfcfe40212c1bf3d588495dac9cf82671faf7beb182537add50955 |
| support_bindings.py | e7c3e0733ae4f9520bf3530e6b8d73f4f7934294f157170f547c88f06de471a7 |
| support_worker.py | d72aa7ecae3896c90ba636762ddfb9f9d147622fa11a8b1a8fbcc14f23261b19 |
| family-connect-subscription-notifications.service | be933a37a1ed37e9a2bc21ccfa213b9459a84493e339f3ae029ac109724b7a1b |
| family-connect-subscription-notifications.timer | c6a6a36b170d3186cdfbf2b47a555c7874493707c7a60c036dfdddbdf48e4192 |
| subscription-notifications.conf worker drop-in | 0b3f772532b7792f84b783634e146b6e8dd85f0ad1dae3f1d2a0da3511f2fac9 |

The root helper read back all installed hashes; the unprivileged independent check
also reads the four modules/units/overlay. The root0700 drop-in directory is not
bypassed: its loaded DropInPaths/ExecStart and process `--subscription-feed` are
independently verified instead. The main worker unit remains unchanged,
RuntimeDirectoryPreserve=yes, runtime inode333786, socket group980/mode0660.

Console runs `sha256:61e4df54f1e1b83011b03427ec96e8941f9060173f7f756cbb4f1979fac81ad7`;
all five delta files match accepted source. The publisher retains50de6f25; original
commands/environment/mounts/users/settings/volumes are retained. No migration source
changed. On **box-932982 /185.251.89.19**, only the two root0644 reader helpers listed
in the earlier checkpoint are installed; final13:05:47UTC hashes match. The restricted
collector SSH key remains read-only. No full HTTP commissioning archive was installed.

### Baseline, cycles, restart and preservation

- Atomic baseline **12:48:20UTC**: position4, actual excluded event count4, status
  `baseline_excluded`. This count was read from the consistent source, not hardcoded.
  Cursor/highwater remain4. No historical event is labelled delivered.
- Three steady observations12:49:25,12:50:30,12:52:07UTC and one controlled restart
  observed12:53:12UTC retain the same baseline/cursor and zero jobs/messages. One
  future subscription boundary is visible throughout, also in final fresh source.
- Worker PID2639328 becomes2651059 only at the deliberate restart; NRestarts0.
  Independent13:03:17UTC readback sees that same PID, enabled/active new timer,
  successful collectors, current source and unchanged baseline. Both existing binding
  and new notification collectors continue successful ticks beyond installation.
- Actual console IPC and rendered notification section PASS:2 existing conversations,
  3 inspected device histories,5 messages,1 existing panel user, no source error.
  The isolated regression, not production data fabrication, proves the new-event UI.
- Encrypted sender records15→17 are the baseline and cursor only. Installer verifies
  unchanged sender identity, all existing immutable message/request fingerprints and
  any existing job IDs. No automatic message/outbox mapping was created by historical
  ingestion. No new real payment or receipt occurred; no test message was sent.
- Fresh consistent canonical snapshot:64 devices/118 invites/1 subscription/4 events.
  All19 protected groups, bindings and exact paid125 HTTP/operator/reconciler archive
  bytes/configuration/unit definitions match preactivation evidence. Actual archive
  policy remains `android-paid-108-119-123-125-v1`; RU reconciliation is fresh/applied.
  AWG/TCP/watch PIDs remain unchanged. HTTP PID changed3916809→178722 at12:52:41UTC,
  but is active with the same archive/configuration/unit and NRestarts0. This task's
  installers do not restart RU HTTP; cause/attribution is not inferred or investigated.

Consistent panel dump/isolated PostgreSQL restore, read-only canonical backup/isolated
restore, and stopped-worker encrypted-history SQLite integrity/every-record decryption
PASS before switching. Local root0700 backup:
`/var/backups/family-connect-subscription-notifications/20261114T124724Z-ac3479bf`.
Keys are stored separately; no live database was restored. Sanitized installer receipt
at `/opt/family-connect-support/notification-install-receipt.json` has SHA256
9a7f7692cc091ecb043ebbc956c949ad22bbed7f051aaf2ea8282e6b0a334d60.
Private independent readback digest:
fb21d89abf042909eac3856a8af0b4625b68dc60b342e47d547fd934bcb6cbd7.
Raw history, identities, snapshots, helper/bundle, images and backups remain outside Git.

### Separate validation outcomes

Collection **6164 PASS**. Final source: **422 core**, **48 panel**, **25 reference/
package PASS** (overlapping selections, not an aggregate count). Late mailbox→terminal
job→valid stored ACK regressions preserve superseded/expired processing state, show
recipient_stored separately in the actual panel route, prohibit further sends and
leave subscription authority unchanged. A late explicit expire aliases an already
terminal natural-boundary job without a second message, even if never delivered.
Reference tests reverse the explicit accepted support delta, then119/platform delta,
and restore all original106 sources/dependencies; historical hashes/inventory unchanged.

Hosted route43591863039, messenger43591863077, panel43591863067, paid43591863176,
readiness43591863215, Linux voice43591863049 and candidate43591863079 PASS. Actual
phase0 failover job132438099607 **PASS**, including failover/auth/offline/revocation
steps, not merely Docker build. Its Docker-enforced full-suite command also passed.
Client builds43591863044 now PASS; no new APK was signed, installed or published.

**Overall hosted CI is NOT PASS.** Linux control43591863123/job132438784552 failed:
`The action 'Protocol, crash recovery, arbiter and packaging regression' has timed out after 25 minutes.`
Artifact14115080706 (SHA2560964cb46ce98c3bfb5cac44ca5b31dcf68edd70c343621221f688f78a0e74f98)
nevertheless records all contexts completed/returncode0: standard5532 passed/276 skipped
(5808 selected), root258 passed, snapshot31498 passed; coverage PASS, no failed/error
test IDs. The enclosing action failure and skipped subsequent GTK/build steps remain
failures, not converted to PASS by this artifact. Why the action exceeded its limit
is not established; no failing notification/reference assertion is identified.
The artifact's PR test-merge906b46538a6ee1cd51c5a39f4a5cd3afdf0ce793 has exactly the
same tree0e2adfbfd058a4b4fdbf9027a91aeda51177812c asac3479bf. Independent phase0
tests132438099847 still IN_PROGRESS at this readback; no completed full-CI claim.
No gate was removed, timeout increased, test excluded or workflow cancelled.

No deployment blocker remains. Real automatic user storage remains **NOT_OBSERVED**
because no postbaseline event/boundary has occurred; the mechanism's installation and
isolated end-to-end acceptance are complete independently. Keep the current guarded
worker on safe disable; preserve baseline/cursor/jobs/request mappings/dedup/history.
Never restore old databases or the old unguarded worker. Exact safe-disable command is
in the [operator runbook](../operators/subscription-notifications.md). Payment provider,
client-card auto-refresh and RU-cause investigation remain separate, not started here.

## Historical checkpoints

The following timed entries record earlier states, not remaining production gates.

## 12:37UTC — partial deployment and concrete owner handoff

PR26 ordinary mergefe6a317c2ee115b2bc3c3f5e9d65fb119d43fa07 completed and remote
main verified. Separate ACK commit0950bba030cb376b01e4d5a17dc355ead53dee67 and
reference commitac3479bfa4f8b190826182fb9633d78a7fdfb993 are retained. Documentation
headb4c082b0 contains no non-doc delta overac3479bf. No history rewrite or original
dirty-worktree overwrite (same4 modified files/123 additions and untracked work).

Using the existing authorized administrative SSH path, installed only these RU
root0644 helpers in `/opt/apps/family_connect/friends-access`:

- `support-bindings-read.py`: c49202036b1b2750312c71531906529c4bea7cf5742b0c415c097dccc9a9f125
- `subscription_events.py`: 585f84a46dfc1c289e9e2830a8f18eaad4bee09410746a7a45c4d90975462016

Fresh consistent canonical backup/isolated restore passed before replacement.
Actual installed isolated-Python reader handles both support-bindings and canonical
subscription feed, saved anchor/resume and rejects arbitrary command injection.
Private before/after comparison passes all19 protected groups, exact accepted
HTTP/operator/reconciler archives, configuration and units, unchanged HTTP/transport
PIDs; paid125 policy/leases remain current. Current counts64/118/1/4 unchanged.
No full HTTP kit, DB migration/restore, key/identity/binding edit or transport restart.
RU backups/helper/source receipt remain privately under
`/opt/apps/family_connect/private-subscription-notifications-20261114`.

Local actual support still runs pre-notification worker SHA256
3efb9b5bf3ebeb4885b75755b6f455b191ffa3c19ad5cafeae4fe7698334ee36,
PID1285950/NRestarts0; RuntimeDirectoryPreserve=yes/inode333786 retained. Existing
binding collector completes successfully after RU replacement. Real running console
image50de6f25 is healthy; actual IPC reads2 existing conversations/5 messages.
No new local modules/unit/drop-in/timer/panel delta have been activated. Their
encrypted-history backup, atomic first-enable baseline, cycles/restart acceptance
are pending the prepared privileged phase; do not confuse panel/canonical backup
rehearsals with that unexecuted phase. Historical events have NOT been labelled
delivered; no notification baseline exists yet and no automatic message was sent.

Remaining required owner action: on **joker-XPS**, run the exact operator-runbook
sudo command for the prepared local helper (final SHA2564bf466a3f802462e5a297f2d7eb51c5dcd800cff853996141c2c68e187a040a6).
Password only in the normal OS prompt; arbitrary-terminal sudo-v is not assumed.
After its roughly6-minute run, read `/opt/family-connect-support/notification-install-receipt.json`
and continue independent production acceptance. Safe disable retains the new guard;
no old database or unguarded worker may replace the current queue. Real new automatic
user receipt stays a separate NOT_OBSERVED unless a real stored ACK is subsequently
seen. No synthetic payment/deadline/test message/public announcement is authorized.

Final hosted readback: dedicated gates and actual failover remain PASS; standalone
phase043591863104 tests, Linux control43591863123 and Android in43591863044 remain
IN_PROGRESS with no completed failure diagnosis. Overall hosted CI is NOT declared
successful. These running checks were not cancelled, weakened or replaced with an
APK release; reconcile their eventual results during the activation follow-up.

## 12:34UTC — applicable gate disposition

All dedicated server route/reference/package/panel/paid/messenger gates and real
failover/auth/offline/revocation are completed PASS onac3479bf. Docker's enforced
full-suite command completed successfully before its tests-passed marker/runtime
image and integration steps; no test was excluded to obtain that result. This is
not a claim that every independently running hosted workflow has completed.
Standalone phase0 job132438099847 still reports its full step IN_PROGRESS from
11:57:41UTC; log download returns BlobNotFound and no full-suite receipt exists yet.
Linux control and automatically triggered Android CI also remain independently
unaccepted. Do not invent a failing test/root cause or report general CI PASS.
The applicable backend gates permit ordinary source merge; preserve all outstanding
CI runs/checks and report their actual status on subsequent readback. No Android
artifact is signed, published or needed for server activation.

Private installer review additionally checks resolved runtime Compose values before
switching, stable worker PID/no automatic restarts for three cycles, a changed PID
after the intentional restart, fresh source and successful real console IPC/history.
Final helper SHA2564bf466a3f802462e5a297f2d7eb51c5dcd800cff853996141c2c68e187a040a6;
four isolated tests and resolved-current-configuration check PASS. Source remains
ac3479bf; subsequent commits only update documentation, not the qualified bundle.

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

## Historical remaining gates — before continuation

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
