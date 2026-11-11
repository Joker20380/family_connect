# SYSTEM-MESSAGES-1 · 11 November2026

Owner-selected continuation: implement system-message sending from the operator panel
under the existing account. **ENABLED13:17 UTC; NO PUBLIC ANNOUNCEMENT SENT.**
The sections before the activation receipt retain the earlier qualification checkpoints.

## Scope

Reuse `/friends/notices/publish`, its existing stable-ID/dedup authorization and
`/downloads/family-connect-events-v2.json`. New panel route `/system-messages/`
provides compose, immutable preview, explicit public-audience confirmation, a durable
queue and history. Additive migration0013, separate view/send permissions, actor/content
bound signed confirmation, CSRF and escaped output. No text bodies/credentials in audit.
The external publisher alone receives the announcements-only credential file; no SSH,
production registry or phone private key enters the web process. HTTPS certificate
checks remain enabled, redirects/proxies are disabled, responses are bounded, and a
matching live public-feed readback is required. Concurrent workers skip locked requests;
crash rollback and explicit unknown-outcome retries retain the same ID/content.

This is a **public** feed, not a targeted message to the owner's phone, not subscription
events and not the addressed SUPPORT-CHAT-1. Public author comes from the existing
publisher grant; the logged-in panel operator is separately audited. No new chat sender
is required. No release version/source changes in Android or VPN/transport code.
Existing123 remains immutable; downloaded unsigned124 still belongs to26727eb7 and
hosted run43008983724, not the new panel source. No artifact/catalog/link is replaced.

## Qualification

- Final local full panel regression:295 PASS, including44 new system-message checks.
  Earlier pre-hardening run287 PASS is retained, not summed into the final total.
- Existing device-announcement and messenger announcement contracts plus scoped-CI
  trigger guard:38 PASS,1 unrelated closed-support-kit packaging check deselected.
- Additive migration drift check: no changes detected.
- Actual Chromium1440px preview/confirmation → durable queue → external management
  command → local certificate-verified HTTPS → unchanged canonical Notices registry
  andv2 export → public readback PASS. First POST commits but deliberately loses the
  HTTP response; UI shows unknown. Actual second-button retry sends the same ID:
  two POSTs, exactly one server event and one panel request. Public GET has no token.
  Published390px screenshot inspected, no horizontal overflow; no send button remains.
- The existing encrypted messenger Store ingests the Android-filtered feed twice,
  then reopens with exactly one event and `read=false`. This exercises shared storage,
  **not an Android device/runtime notification**; physical Android/production NOT_RUN.
- Private synthetic receipt/screenshots/logs remain under
  `state-client-build/system-messages-20261111/`; no raw DB, key or credential enters Git.
  RAM-only PostgreSQL on127.0.0.1:15433 is separate from the installed panel's database;
  local HTTPS and panel test processes terminate after acceptance.
- Hosted owner-only review command `/qualify-system-messages` runs just the existing
  source-bound panel job (tests, migrations, allowlisted image). It cannot start the
  Android/VPN/G4 jobs or deploy. The ordinary support qualification command is unchanged.
- **Hosted PASS:** [run43020554360](https://github.com/Joker20380/family_connect/actions/runs/43020554360),
  panel job130522389829, exact runtime source19b6ab37808b9899a2df0de32e5e9754f331ed51.
  Migration/system checks, console/fleet regression, existing browser-form retry checks,
  allowlisted container build and packaged Django check all pass. Support-contracts and
  support-android are skipped by the panel-only command, not newly qualified artifacts.
  Source was committed/pushed and remote SHA verified; this later receipt is docs-only.

## Deployment boundary / rollback

Installed panel remains imagec179d1ae and DB migration0011 from the prior receipt.
This turn does not mutate that runtime, RU, NL, owner phone or public notices. Prior
36-table/929830-row backup/isolated restore belongs to earlier preflight and is not a
fresh deployment backup. Root disk was227MiB free at entry and204MiB at final readback:
no local image build/update or unsolicited cleanup is attempted. Final exact installed
image remainsc179d1ae and both panel containers are healthy; HTTP health200. Only the
temporary RAM test container is stopped/removed. Hosted CI passed; review/ordinary merge, sufficient disk space,
fresh consistent backup/isolated restore and a separately provisioned publisher remain
gates. No production text/audience was approved, so no test announcement is broadcast.

Rollback: stop external publisher runs/revoke its scoped grant, restore previous UI
image while retaining additive tables and all existing volumes/users/history. Do not
restore an old DB over current observations or claim an already public message is
retracted by stopping the queue. Existing server notice expiry/edit rules still apply.
Operator guides: [RU](../operators/system-messages.ru.md), [EN](../operators/system-messages.en.md).

## Owner-authorized enablement — in progress

Owner explicitly requested activation, not a public test message. Add a permanent
Compose overlay: same immutable image for web/publisher, token only in a nonroot
read-only publisher, bounded resources/logs, restart policy and loop-only health.
The existing-install console startup skips `seed_demo` to preserve group permissions
and projections; additive migrations/collectstatic still run. New Compose merge test
checks these boundaries; hosted panel-only CI now runs it as well.

Only stopped `fc-beta109-smiley-ci` was exported (374265397-byte compressed archive,
32592 members, gzip/SHA verified) and removed with approval, retaining its image,
bind sources and all volumes. Private archive/receipt stay ignored under
`state-client-build/system-enable-20261111/`. Root available space became1.1GiB;
no generic Docker prune or neighbouring-service cleanup occurred.
RU bounded readback: HTTP candidate, paid watch, AWG and TCP units active; installed
notice modules match reviewed source; public HTTPS feed has3 events. No RU restart,
phone role change, announcement or token grant yet. Existing panel image remains
c179d1ae pending fresh backup/isolated restore and final source qualification.
PR18 is mergeable/unprotected with no independent approval; the owner's enablement
instruction and source-readiness review are not an independent reviewer approval.
No repository protection or review rule is changed.

## Activation receipt

Enabled11 November2026,13:17 UTC.

- Source4c85cecb88d587ceb50162005604cf3c64f6e648; final scoped hosted
  [run43023898059](https://github.com/Joker20380/family_connect/actions/runs/43023898059),
  panel job130533616267 PASS: migrations/regression, browser request identity,
  Compose isolation/no-seed check and allowlisted image build. Local focused3 PASS,
  1 unrelated closed-kit test deselected. Android/support jobs intentionally skipped.
- [PR18](https://github.com/Joker20380/family_connect/pull/18) ordinarily merged at
  b896b38a4c098f6c2623601330ef43fc95bd779f. Merged runtime/source matches qualified
  head. Readiness review and explicit owner enablement authorize this operation;
  no independent approval is claimed, repository protection unchanged.
- Installed console/publisher image:
  `sha256:50de6f25a04c1127b127b3278314619c69eddeec229d0d4ad9b7e67c1d2ffeab`.
  All237 packaged source/lock hashes match. An initial verification looked for the
  lockfile in the source path; corrected to the Dockerfile's `/tmp/requirements.lock`
  destination, then passed. Actual build and original rollback image are retained.
- Before upgrade, monitoring timers were paused and active jobs allowed to finish.
  Fresh repeatable-read PostgreSQL dump plus existing configuration/synthetic-volume
  backup; separate networkless RAM-backed PostgreSQL restore matches all36 tables,
  939954 rows. Dump SHA256:
  `37264aefdf397c29d4149327d4e9cfc1b4af2604195d60ab142de6eb512f872f`.
  Verification container removed; live DB never restored. Console alone updated
  without dependencies/build/pull; original DB container, volumes and environment stay.
- Additive migrations0012/0013 installed. No `seed_demo`, password reset, account
  replacement or group permission assignment. Initial strict post-upgrade comparison
  stopped at `auth_user`; investigation confirms only `last_login` changed. Monitoring
  resumed on that stop, adding observations/audit rows. Subsequent row-level check
  proves23 protected tables identical and every original row retained in10 active
  tables (938254 original rows, ignoring only `auth_user.last_login`). User identity,
  password hash and permissions unchanged; session changes are additive.
- Existing sole active owner account: actual authenticated HTTP200 on list and compose
  form, no POST. Short-lived verification session deleted; existing sessions/password
  untouched. Queue asserted empty before starting publisher and at final readback.
- Server notices SQLite backed up/`integrity_check`/table comparison before granting
  the separate `Family Connect · панель` announcements-only publisher. One admin added;
  existing admins, device roles, events/revisions/edit operations preserved.0600 token
  transferred privately, mounted read-only only in nonroot publisher, never web/Git/CI.
  `unless-stopped`,10-second loop, one request per cycle, bounded logs/resources.
- Console/publisher/PostgreSQL healthy; panel HTTP200. Publisher's own certificate-
  verified HTTPS public-feed GET matches the host readback. Public feed hash unchanged,
  3 events, queue0, publications0. Publisher health is a loop check, not delivery proof.
  No public POST or physical Android/client-delivery acceptance is claimed.
- Monitoring timers restored; both monitor/probe services subsequently succeed.
  RU HTTP/watch/AWG/TCP active. AWG/TCP/watch PIDs and restart counters unchanged;
  HTTP MainPID changed during the window outside this operation's commands, so the
  initial strict all-unit equality check correctly failed. Follow-up checks active
  state, unchanged notice modules/HTTP archive and functioning HTTPS feed. No service
  restart or policy/VPN/phone/NL change was performed here; prior RU cause remains open.
- Root available988MiB, data volume2.8GiB at readback: still a capacity warning.
  Only the separately approved, fully archived stopped beta109 container was removed.
  No client version, signing key, release installer, invitation link or catalog changed.

Private deployment bundle remains under
`state-client-build/system-enable-20261111/`: `publisher.private.env`, runtime overlay,
token, `panel-backup/`, sanitized-in-console/private-on-disk verification receipts,
and `runtime-control.sh`. It is ignored by Git. Status:
`sh state-client-build/system-enable-20261111/runtime-control.sh status`.
Disable processing with its `stop-publisher` argument. `rollback-ui` stops publisher
and restores original imagec179d1ae with the no-seed startup while retaining additive
tables/users/history/volumes. Old tag `fc-panel-rollback:pre-system-20261111` is kept.
Do not restore the old DB over current observations. A separate grant revocation can
use the existing notices CLI/name; stopping UI/publisher does not retract public events.
Normal administration must use the retained overlay/env pair, not rebuild the old
base Compose console. Remaining acceptance: explicitly approved public text and
actual real-client receipt; no unsolicited broadcast is part of enabling the feature.
