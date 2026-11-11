# SYSTEM-MESSAGES-1 · 11 November2026

Owner-selected continuation: implement system-message sending from the operator panel
under the existing account. **SOURCE CANDIDATE; NOT INSTALLED / NOT PUBLICLY SENT.**

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
