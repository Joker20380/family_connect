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

## Active Android step — WG/AWG accepted

Android WG/AWG passed four-ABI build, 12 unit methods, lint and real API35 x86_64
emulator:24 encrypted UDP,4 stops,cancel,system revoke (clients34660308853).
One runtime fixed WG→AWG→WG crash; profiles remain independent and encrypted.
Next: Android TCP and Auto, then stage5 Reticulum. Device update/testing stays deferred.
See [Android report](releases/2026-09-12-android-awg.ru.md).

## Next, in order

1. Implement Android TCP: native engine/VpnService integration, separate protected
   profile, explicit selection, startup cancellation and cleanup. Accept on isolated CI.
   Windows WG/AWG/TCP/Auto is accepted in scoped CI; Android WG/AWG is accepted in
   the emulator. Do not restart completed Windows implementation as the next task.
2. Android Auto WG→AWG→TCP: health checks, cleanup before transitions, cancellation
   and bounded recovery. Keep existing WG/AWG profiles intact.
3. After Android transport integration, stage5 Reticulum: signed provisioning delivery,
   verification/application/ACK/rollback and replay protection. Android updater/Google Play
   and user-deferred device/load tests do not gate this implementation.
4. Before distribution: full-routing/external gateway/REALITY and actual device acceptance,
   Android release signing/versioning. User deferred APK updates and real/load tests;
   do not resume them automatically. Desktop0.2.9/catalogseq8 and TCP Setup0.1.0 remain published.
5. Deferred resilience experiments: concurrency1→4→8, request-to-flow diagnosis and
   second Ubuntu retest. Second independent VPS only when supplied by user; never use
   the test laptop or neighbouring services. Current timeout/stability limits remain open.
6. Native enrollment/storage, signing-root rotation/recovery, then payments/notifications.

Current stage4, not stable multi-platform resilience. Details, results, backups and unfinished
work: [session checkpoint](releases/2026-09-11-session-checkpoint.ru.md).

## Windows реализован; следующий блок — Android (2026-09-12)

Текущий engine-crash recovery завершён отдельным отчётом; новых подпунктов в него не добавлять.
Мониторинг недоступного соединения при живом процессе завершён и проверен в scoped CI.
Интеграция AWG принята в scoped CI2026-09-12; [результат](releases/2026-09-11-windows-awg-integration.ru.md).
Автоматическое переключение Windows принято в scoped CI2026-09-12:672 макета,7 policy-сценариев,
живой AWG→TCP, отмена, исчерпание и очистка после SCM restart. Android WG/AWG также принят; далее TCP/Auto.
[Отчёт и границы приёмки](releases/2026-09-12-windows-auto.ru.md). Полный маршрут/REALITY требуют отдельной
приёмки до выпуска. Отложенные пользователем испытания на устройствах/под нагрузкой
не возобновлять автоматически и не смешивать с реализацией.
Android WG/AWG принят в эмуляторе; следующий шаг — Android TCP и Auto, затем этап5 Reticulum.
