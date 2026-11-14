# Subscription notifications: authority, rollout and rollback

See the [dated receipt](../releases/2026-11-14-subscription-notifications.md) for
actual installation. Source availability is not deployment. Android remains public
beta125/catalog8; ordinary signed text arrives in the official private chat. The
subscription card uses its authenticated endpoint only on opening/Refresh.

## Authority and durability

The forced reader uses SQLite `mode=ro`, `query_only`, one read transaction and
pages of128 committed APPLIED events in immutable ledger rowid order. It does not
use timestamps, last-snapshot events or the1000-entry panel history. Each position
includes the exact row hash; changed/missing anchors fail closed. Equal timestamps
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
