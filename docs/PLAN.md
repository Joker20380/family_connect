# Working plan / Рабочий план

## Completed: 0.2.1 rollout

Platform CI and immutable release published; Linux installed with backup; gateway,
product DB/API and periodic worker deployed. Health and preservation of three legacy
peers verified. Signed catalog sequence 1 published. See STATUS for exact evidence.

## Completed user priority: 0.2.2 visual refresh

Desktop artifacts published, platform CI passed, signed catalog sequence 2 published.
Linux installed through the existing 0.2.1 updater; Windows update available in app.
Temporary editable dodecahedron icon; revisit icon design later.

## Completed: 0.2.3 polish and quiet polling

Windows/Linux polling and layout regressions passed. Artifacts and signed catalog
sequence 3 published; Linux installed with previous version retained. Windows update
available through Check for updates; awaiting user confirmation of 0.2.3 behavior.

## Completed: 0.2.5 Linux fit and responsiveness

Platform CI passed; catalog sequence 4 published; Linux upgraded from 0.2.3 with
rollback retained. Real laptop startup visibility and themed-dialog cancellation checked.
Confirm user perception of startup/steady-state responsiveness: a first probe had an
850 ms gap, follow-up warm measurement max 17.9 ms. See STATUS for exact evidence.

## Completed: 0.2.6 narrow window

User preference: narrow window, one action per row at every width, height by content.
Platform CI and real-display checks passed; catalog sequence 5 published; Linux
installed with previous version 0.2.5 retained. Await user visual confirmation.

## Next, in order

1. Run an isolated live product enrollment → stage → reconcile → publish/fetch → revoke
   smoke on the server, cleaning up its test peer and entitlement. Local integration
   passed; do not describe live end-to-end enrollment as already checked.
2. Integrate provisioning into client runtime application and ACK, with known-good VPN
   recovery. Add public HTTPS ingress when the client flow is ready.
3. Reticulum update announcements/catalog delivery through the existing signature verifier.
   Notifications never authorize installation. HTTPS delivers the larger release files.
4. Native secure storage/invitation flow for Windows and Android. User confirmed 0.2.1 works on Windows and Linux; validate future updates there.
5. Signed update root rotation/recovery and stable release channel. Renew the catalog
   before its 90-day expiry even if binaries have not changed (increase sequence).
6. Distributed gateway agents/topology migration and real Reticulum failover.

Accounts, billing, public production ingress and hardware rollback protection remain
outside the current pilot. Unattended updates require a separate explicit policy.
