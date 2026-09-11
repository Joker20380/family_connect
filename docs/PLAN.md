# Working plan / Рабочий план

Общий план и критерии этапов: [ROADMAP](ROADMAP.ru.md). Сейчас этап 4 — упаковка, платформы и стабильный выпуск.

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

## Completed: 0.2.7 native Linux frontend

User reports sequential redraw and wants a finished visual design. GTK 4/libadwaita
implementation passed local, real-Wayland and platform CI checks. Immutable release
published, catalog sequence 6 signed, Linux upgraded through the 0.2.6 updater with
rollback retained. Tk is no longer the Linux frontend. One-column, narrow/content-sized
layout and backend behavior preserved. User explicitly approved its appearance and behavior; see STATUS for measured evidence.

## Completed: Windows 0.2.8 visual alignment

User approved Linux 0.2.7 appearance and behavior. Windows now follows its compact composition. Runtime layout/interaction checks passed;
immutable release and signed catalog sequence 7 published. Next: user updates Windows
and confirms its appearance (currently reports 0.2.7). Main catalog propagation verified.
User still needs to import the Windows activation and Android profile and test connectivity.
Linux 0.2.7 remains installed; server unchanged.

## Completed: live product enrollment/revoke smoke

2026-09-10: isolated test identity enrolled through the deployed HTTP API, staged,
installed by the periodic worker, provisioning published/fetched and verified locally.
Replay and post-revoke fetch rejected; worker removed the live and persisted test peer.
All three legacy peers preserved; test entitlement/device revoked, audit/reservation kept.
No client runtime application or real handshake claimed. See [report](live-product-smoke.ru.md).

## User priority: resilience against blocked servers/protocols

2026-09-10: AWG 2.0 added alongside WG on separate UDP/51821. Linux helper/profile
installed, actual host connection and blocked-WG → AWG fallback passed. Original WG
peers preserved. Working-tree client pilot available separately from stable releases.
See [rollout and remaining checks](releases/2026-09-10-awg.ru.md).

## Next, in order

1. Continue diagnosis on FIRST laptop, per user decision. Second-laptop work paused.
   Read actual first-laptop active state/interfaces before any test; preserve current connection.
   Compare identical direct probes in normal-user and sudo→runuser contexts without VPN;
   then bounded off→on→off with first-laptop profile,20 probes per phase and direct control.
   If direct control degrades with VPN, inspect routing/filtering/socket accumulation;
   if direct stable and TUN fails, resume paired headers/offload hypothesis testing;
   if direct fails without VPN, diagnose external network first. No permanent MTU/timeout changes.
2. Repeat confirmed correction on second Ubuntu. Offload A/B/A already executed and restored;
   failed direct control makes it inconclusive. Do not ask to rerun the old pending capture
   blindly: old scripts contain device-specific interfaces/profile ids and peer filters.
3. Preserve/review main client fix (264 tests, GTK passed), integrate standalone setup work
   from /tmp/fc-tcp-bootstrap/local archive, then platform CI and trusted immutable release.
   No new remote CI/release for current changes yet. Keep six-file desktop update compatibility.
4. Native Windows/Android transport integration and device acceptance.
5. Provisioning/runtime/ACK and actual Reticulum service-message delivery, with alternate
   reachable entrypoints. Independent second VPS only when supplied by user; not the test laptop.
6. Native enrollment/storage, signing-root rotation/recovery, then payments/notifications.

Current stage4, not stable multi-platform resilience. Details, results, backups and unfinished
work: [session checkpoint](releases/2026-09-11-session-checkpoint.ru.md).
