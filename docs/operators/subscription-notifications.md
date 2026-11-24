# Subscription notifications: authority, rollout and rollback

See the [dated receipt](../releases/2026-11-14-subscription-notifications.md) for
actual installation. Source availability is not deployment. Android remains public
beta125/catalog8; ordinary signed text arrives in the official private chat. The
subscription card uses its authenticated endpoint only on opening/Refresh.

## Installed state — 14 November13:05UTC

Sourceac3479bf is installed, not just built: RU's two read-only helpers and, on
joker-XPS, four support modules, the new systemd collector/timer/worker drop-in,
and console image61e4df54 (publisher remains50de6f25). Baseline created once at
12:48:20UTC: position/highwater4, actual excluded count4, `baseline_excluded`.
No automatic jobs/messages; one future boundary is tracked. Three steady cycles
and a controlled restart passed; independent IPC/render/source/hash checks passed.
Real new automatic storage ACK remains `NOT_OBSERVED`; do not send a test to clear it.

Read the sanitized receipt and service status without repeating installation:

```sh
cat /opt/family-connect-support/notification-install-receipt.json
systemctl show family-connect-support.service -p ActiveState -p MainPID -p NRestarts -p RuntimeDirectoryPreserve
systemctl show family-connect-subscription-notifications.service -p Result -p ExecMainStatus -p ExecMainExitTimestamp
systemctl is-active family-connect-subscription-notifications.timer
```

The collector is a successful inactive oneshot between ticks, not a stopped daemon.
Current backup directory: `/var/backups/family-connect-subscription-notifications/20261114T124724Z-ac3479bf`.
Keys are separate from encrypted history. Retain all state and the guard on disable;
never restore this backup over later live events. Exact hashes/CI caveats are in the
dated receipt. General CI timeout is not a production delivery status.

## Authority and durability

The forced reader uses SQLite `mode=ro`, `query_only`, one read transaction and
pages of128 committed APPLIED events in immutable ledger rowid order. It does not
use timestamps, last-snapshot events or the1000-entry panel history. Each position
includes the exact row hash and maximum observed highwater; changed/missing anchors
or regression of even not-yet-processed source positions fail closed. Equal timestamps
and clock reversal cannot skip events. Never reset the cursor after source damage.

The root collector has only the existing forced SSH reader and read-only cursor
IPC. It atomically installs a private90s projection. The support owner internally
renders text; no automatic enqueue operation is exposed through panel IPC. Manual
requests retain their numeric actor; automatic requests have
`source.service=subscription-notifications-v1` and their canonical origin.

Job, frozen recipient/text/request UUID and cursor commit together in the existing
encrypted FULL-synchronous sender database. Outbox message, request deduplication
and job link also commit together. Payment transactions do not wait for messaging.
Retries retain request IDs and signed bytes. Lost collector IPC replies cannot send
messages. No pruning: quota1000 stays visible as `history_full`, retry backoff is
bounded30s–1h, and seven-day delivery expiry retains the job/history.

First enable atomically saves the excluded ledger range/count/hash, not delivered
messages, plus already-expired boundary exclusions. Existing future active/grace
boundaries remain eligible. Restart/update/rollback must retain these records.

Natural ending keys include device, canonical origin version and deadline. A later
fresh source snapshot must revalidate version/state/deadlines/event before enqueue.
Renewal/grace/later operations supersede stale endings; outbox retries also require
fresh canonical and support projections. Explicit expire aliases the same original
boundary, including repeated expire operations. A new explicit expire after baseline
exclusion is still a new operation notification. No fake ledger event is written.

Capture freezes the canonical chat public identity and confirms support enrollment
against the worker's pinned thread. Missing identity at capture is permanently
visible (`identity_missing_at_capture`), not reassigned to a later identity. Missing
confirmation/expired leases wait; revocation/identity change never redirects jobs.

Payment text says extended only when its paid deadline exceeds the preceding
canonical paid/grace boundary. Messages are dated historical facts, never a claim
of current active access. No amounts/currencies/revocation reasons are invented.
Mailbox-accepted messages cannot be recalled; wording remains about the recorded
period/operation. `recipient_stored` means stored, not read. Chat cannot grant VPN.
Late valid storage ACKs remain visible as a separate delivery fact even when the
job is expired or superseded. They never clear its terminal processing state or
permit another send. IPC reads the linked message immediately; dispatch also
persists the delivery fact without rewriting unchanged records.
An explicit expire for an already terminal natural boundary adds its event ID to
that same job only: frozen text/request/message IDs and terminal state stay intact,
even if the first message was never delivered. It does not automatically resend.
Only the distinct baseline-excluded case creates a new explicit-operation job.

## Operator observation

With `view_support_messages`, the production device card and official conversation
show event/boundary, time, state/reason and the corresponding dialogue/message link.
Saved, queued, mailbox-relayed, recipient-stored, blocked, expired, superseded and
baseline-excluded are separate. Inspect source freshness and both timers when jobs
wait. Do not manufacture payments or send real-user tests to clear warnings.

## Deployment gate

Only deploy reviewed/merged source after applicable isolated and hosted gates.
Keep the accepted HTTP/operator/reconciler archives and paid125 pins unchanged.

1. Inventory actual archive hashes/loaded policy, worker PID/unit/RuntimeDirectory
   inode, panel image/source, event counts and protected identity/binding/history
   fingerprints. Use only the authorized gateway185.251.89.19 and support host.
2. Obtain host administrative execution. Briefly stop only the support worker for
   a consistent encrypted-history backup; retain its key separately/private. Save
   code/configuration; take a read-only SQLite backup of the canonical registry.
   Verify a nonempty isolated restore. Never print private records or keys.
3. Build `python -m scripts.package_support_chat --output PRIVATE_STAGING/kit` and
   verify `sha256.json`. Do NOT install its full HTTP archive over accepted runtime.
4. Install `registry/subscription_events.py` beside the existing forced reader;
   replace only `support-bindings-read.py`. Keep the same restricted SSH key/command.
   Code is root-owned0644; existing HMAC/SSH credentials stay0600. Python `-I` is
   supported through explicit trusted-file import, not ambient module search paths.
5. Install changed support modules, subscription service/timer and the explicit
   worker drop-in `subscription-notifications.conf`. Preserve
   `RuntimeDirectoryPreserve=yes`, socket permissions and mounted directory inode.
   Output stays root:fc-support-read0640 in the existing0750 binding directory,
   inaccessible to Django. Deploy only the reviewed panel delta; retain users/volumes.
6. Start worker/collector, enable the new timer, verify actual panel IPC/history,
   durable baseline and zero historical sends. Observe multiple30/60s cycles and a
   restart, checking protected records and unchanged paid/support/recovery runtime.
7. Report actual component hashes and separate route acceptance from a subsequent
   real user's storage ACK. Do not create a real payment or change deadlines to test.

## Safe disable / rollback

Stop/disable `family-connect-subscription-notifications.timer`, remove its worker
drop-in and restart support with the retained RuntimeDirectory. Keep the automatic
outbox safety guard and notification module: without fresh source, automatic jobs
stay held while manual support continues. Reverting to the unguarded old worker
with new automatic outbox records is **not safe**: it could send superseded endings.

Restore only code/configuration compatible with this guard. Retain current encrypted
history, baseline, positions, jobs, requests and deduplication. Never restore an old
registry or sender database over new events. Reenable at the saved position, never
at a new baseline. This compatibility restriction is part of the deployment gate.

## Prepared administrative action — 14 November

Support and console are on **joker-XPS**, login **joker**, worker **fc-support**.
Do not confuse this host with RU **box-932982 /185.251.89.19**. The existing separate
administrative SSH connection can install RU helpers; the collector key remains a
forced read-only command. No changes on Amsterdam or excluded hosts are needed.

After applicable gates and PR26 merge, the owner successfully ran this local helper
(installation completed12:53:21UTC). Retain it for verified idempotent repair or safe
disable; a routine status check does not need another install:
`/mnt/data/fc-subscription-notifications-20261114/install-ac3479bf/install.py`

SHA256: `4bf466a3f802462e5a297f2d7eb51c5dcd800cff853996141c2c68e187a040a6`.
It pins sourceac3479bf and bundle16284251df81423d772f0b808ad89cd7863924239eb50d7e7cd230c0422e6313.
Run in a normal local terminal on joker-XPS; enter the password only in sudo's OS prompt:

```sh
sudo /usr/bin/python3 /mnt/data/fc-subscription-notifications-20261114/install-ac3479bf/install.py install
```

The helper checks hostname, exact bundle/files, current configuration/image and
mounted runtime inode333786. It takes fresh panel and encrypted sender backups,
revalidates resolved Compose environment/command/IPC group/mount targets,
keeps keys separately, verifies isolated restores before switching, installs only
four support modules and the new units/drop-in, and switches only console's image.
Users/settings/volumes, main unit and existing support-binding timer are retained.
It then enables the collector, waits for the worker's atomic baseline, observes
three65s cycles and one restart/70s observation. Allow roughly6 minutes. It does not
accept an unexpected worker restart, stale notification source or failed panel IPC.
It does not
initialize/reset the baseline itself and never restores a live database. Repeating
install retains baseline/cursor/jobs; unexpected code/configuration drift aborts.

Result: `/opt/family-connect-support/notification-install-receipt.json`, readable
without sudo; expect `state=installed_baseline_observed` and
`cycles_restart_acceptance=PASS`. The receipt records the actual excluded count,
cursor, future-boundary count and separate real stored-ACK observation. Assistant
readback still verifies source/archives/protected data and the running panel.

Safe disable uses the same verified helper with `disable` instead of `install`.

```sh
sudo /usr/bin/python3 /mnt/data/fc-subscription-notifications-20261114/install-ac3479bf/install.py disable
```

It stops the new collector, removes only its worker drop-in and restarts the guarded
worker. The panel's observation delta and all current records remain. Never replace
the worker with its pre-notification version. A failed switch attempts this safe
disable, preserves backups/current data and records a failure receipt, not PASS.
The generated private bundle/helper/tests and raw backups stay outside Git; only
their sanitized hashes and this execution contract are tracked here.
