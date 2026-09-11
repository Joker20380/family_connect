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

1. User deferred further network/load testing. Functionality demonstrated, stability
   remains open; do not resume concurrency/second-laptop experiments automatically.
   Standalone setup integrated into main; existing prompt/recovery patch reviewed,
   273 tests + GTK recovery passed, setup hash equals previously VM-tested artifact.
2. Desktop0.2.9/catalogseq8 and standalone TCP Setup0.1.0 published. Setup source7eee3c3,
   all CI passed, downloaded archive matches trusted build, detached signature published.
   Initial verifier/anchor must still be trusted independently. Next: native Windows
   AWG/TCP integration, then Android transports/device acceptance. Android manual APK
   update deferred by user; do not prioritize in-app updater/Google Play distribution.
   Windows TCP engine foundation now passed: pinned build, actual TUN/VLESS 12/12,
   forced cleanup and default routes/DNS preservation (Windows CI34629412460).
   Signed REALITY profile + device binding/sequence floor/LocalSystem DPAPI import now
   passed:300 Python tests, C# fixture +29 rejection cases,18 real Windows broker checks;
   all platform CI34633788708 and phase0 passed (profile milestone).
   Process ownership primitive now passed18/18 local requests across explicit/owner-crash/
   engine-crash stop, binary tamper rejection and cleanup; native/platform/phase0 CI passed.
   Broker IPC/SCM session now implemented: async connect/cancel, SID ownership,
   routes/DNS/NRPT journal and cleanup/restart. Scoped LocalSystem acceptance passed24/24
   IPv4/IPv6 HTTP,4 OS DNS checks and5 cleanup scenarios; other account actions refused.
   CI34639769072/phase0/platform passed. External REALITY/full default routing remains
   unaccepted; installer payload and TCP GUI passed platform CI34641891335, 288 layouts,
   installed hash checks and uninstall; native/session and phase0 also passed.
   Engine-crash recovery passed (3 retries, 15/30/60s), source7de6e69; clients/native/phase0 green.
   Health monitor passed Windows/platform/native CI, source9863427. Next implementation: Windows AWG
   and transport switching; AWG worker passed CI12/12; signed profile/DPAPI, broker/installer/UI now implemented,
   integration CI passed2026-09-12 (24/24 LocalSystem UDP,504 layouts; TCP regression green). Next: automatic transport policy/acceptance. Full-routing/production probe acceptance before distribution. [UI checkpoint](releases/2026-09-11-windows-tcp-ui.ru.md).
   Finish Windows before moving to Android, per user.
   [Session checkpoint](releases/2026-09-11-windows-tcp-session.ru.md).
   [Lifecycle checkpoint](releases/2026-09-11-windows-tcp-lifecycle.ru.md) ·
   [Profile checkpoint](releases/2026-09-11-windows-tcp-profile.ru.md).
   This preview is not in stable installer; physical/network acceptance remains open.
   See [Windows evidence](releases/2026-09-11-windows-tcp-engine.ru.md) and
   [setup evidence](releases/2026-09-11-tcp-setup-release.ru.md).
3. Deferred backlog: isolated concurrency1→4→8/request-to-flow diagnosis, then repeat
   confirmed correction on second Ubuntu. Current timeouts are known pilot limitations,
   not a completed stability gate. Resume these tests later per user direction.
   See [integration checkpoint](releases/2026-09-11-setup-integration.ru.md).
4. Native Windows/Android transport integration and device acceptance.
5. After Windows and Android transport integration, stage5 Reticulum: provisioning/runtime/ACK
   and actual service-message delivery, with alternate
   reachable entrypoints. Independent second VPS only when supplied by user; not the test laptop.
   Android updater/Google Play and deferred load experiments do not gate Reticulum implementation.
6. Native enrollment/storage, signing-root rotation/recovery, then payments/notifications.

Current stage4, not stable multi-platform resilience. Details, results, backups and unfinished
work: [session checkpoint](releases/2026-09-11-session-checkpoint.ru.md).

## Оставшийся объём до Android (уточнено 2026-09-11)

Текущий engine-crash recovery завершён отдельным отчётом; новых подпунктов в него не добавлять.
Мониторинг недоступного соединения при живом процессе завершён и проверен в scoped CI.
Интеграция AWG принята в scoped CI2026-09-12; [результат](releases/2026-09-11-windows-awg-integration.ru.md).
Оставшаяся реализация Windows: автоматическое переключение транспортов. Полный маршрут/REALITY требуют отдельной
приёмки до выпуска. Отложенные пользователем испытания на устройствах/под нагрузкой
не возобновлять автоматически и не смешивать с реализацией.
Следующий платформенный блок — Android AWG/TCP; затем этап5 Reticulum.
