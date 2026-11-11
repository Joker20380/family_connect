# System messages from the panel

Enabled on the working panel11 November2026. Open
`http://127.0.0.1:8765/system-messages/` using the existing panel login. Separate
`console.view_system_messages` and `console.send_system_message` permissions control
reading and publication; existing superusers have both. No ordinary account gains
permissions automatically and no phone identity is copied.

Open `/system-messages/`, compose a title/body, choose platforms/type/lifetime, then
preview. Preview saves an immutable request but does not send it. Explicitly confirm
the **public audience** before queueing. This is a public feed, not an owner-only
test message or a private support conversation. Never include personal data/secrets.
Title/body limits are160/4000 UTF-16 units; lifetime is1–365 days. Platform selection
filters clients, not access to the public feed. The last100 panel requests are shown;
existing announcements published from Android/CLI are not imported.

The external publisher reads the durable queue, rechecks the operator's rights and
uses the existing scoped HTTPS notice API. Only an exact, unexpired public-feed
readback marks a request published. Publication is not a delivery/read receipt.
Clients fetch on their next successful feed refresh; offline immediate delivery and
private replies are not supported. No new Android version is required by this change.
The client-visible author is the server publisher grant's name; the panel audit
separately records the confirming account and payload digest, never the body.

Unknown results require an explicit retry of the **same ID and unchanged content**,
not a new draft. Duplicate confirmation/retry cannot create another notice. Queued
requests remain local when no publisher is running. Revoked permissions block execution.
Process crashes roll back the queue transaction; a later run retains the original ID.
Independent workers skip locked rows rather than executing the same request concurrently.

Before commissioning: review/merge/scoped CI, disk headroom, fresh consistent backup
and separate restore verification; additive migration0013 preserves existing users.
Create a separately revocable announcements-only grant with the existing operator
CLI `scripts.service_notices grant`. Keep its token in an owner-only0600 regular file,
outside Git/CI, the web container and the panel `.env`. An external trusted process
with access to the local queue database runs from `control_plane/`:

```sh
python manage.py publish_system_messages \
  --origin https://185.251.89.19:8443 \
  --token-file /private/system-publisher.token --limit 1
```

Paths above are examples, not provisioned credentials. Use the qualified runtime and
private local PostgreSQL settings. Certificate verification stays enabled; redirects
and proxies are disabled, public readback receives no bearer token, batch size is1–20.
This installation's separate publisher is enabled with explicit owner authorization;
other installations do not gain a credential automatically. Inspect the queue before
enabling any schedule. Disable by stopping external runs/revoking the grant; UI rollback
uses the previous image without restoring an old database or deleting tables/volumes.
Already published notices remain public until expiry or a separately authorized existing
administrator action. Use an isolated test feed for owner-only verification.

For an explicitly authorized permanent enablement, overlay
`deploy/system-messages/compose.publisher.yaml` on the existing Compose project.
The separate `system_publisher` processes one queued request every10 seconds and
uses `unless-stopped`. Only that process receives the read-only token mount and runs
as its file-owner UID/GID. Pin `FC_PANEL_IMAGE` to the immutable qualified image ID;
keep other deployment variables private, preserving PostgreSQL/secrets/volumes.
Update only console first, verify health/login/empty queue, then start the publisher.
Publisher health means its processing loop is alive, never client delivery.
This existing-install overlay deliberately omits `seed_demo`: migrations run, but
existing group permissions and member projections are not reset by fixture seeding.
