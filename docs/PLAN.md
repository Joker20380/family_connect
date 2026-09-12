# Working plan / Рабочий план

## Paired preview acceptance — 2026-09-13

Local409 Python passed, including66 extracted protocol/arbiter scenarios. Scoped
Linux CI34722755860 passed on247d16b; Docker272 tests and full phase034722963403
passed on3a28be7. CI tar.gz SHA256 matches the local preview. Previous Clients
Windows/Linux/Android all passed. Added local-only recover CLI, retaining ACKs
and pending state on failure. Manual paired pilot/return plan prepared.
Observed installed Linux **0.2.8**, previous0.2.7; old GUI has no arbiter. No
installation, profile mutation, release, catalog update or server changes.
Next: separate-directory manual paired preview pilot, then native Stage5 binding.
AWG3.1, TD-1 and Stage6 remain open.
[Acceptance evidence](releases/2026-09-13-linux-control-acceptance.ru.md) ·
[Manual rollout/return](linux-control-preview-rollout.ru.md).


## Paired Linux control preview — 2026-09-12

Operator GUI/core bundle added with an explicit public-file allowlist, integrity
manifest, runtime-only pinned dependencies and extracted launcher. Legacy six-file
desktop archive unchanged. Local405 Python passed; extracted real RNS lifecycle
and GTK smoke passed. Scoped Linux control CI34720569558 passed on source d8aef8a.
AWG/TCP pilot passed. Docker test-stage dependency omission reproduced and fixed
in ac6a22f: complete public desktop bundle + VERSION copied into tests stage only.
Local Docker250 tests passed; phase0 run34720868247 fully passed including build,
failover/auth/offline/revocation/cleanup and Python/Rust. Clients Windows/Linux
passed; Android subsequently passed (see 13.09 acceptance above).
[Docker fix evidence](releases/2026-09-12-control-docker-fix.ru.md).
No release/install/catalog/server changes. CI acceptance completed; manual paired pilot next; native Windows/Android binding, AWG3.1 and TD-1 remain open.
[Preview checkpoint](releases/2026-09-12-control-preview.ru.md).


Общий план и критерии этапов: [ROADMAP](ROADMAP.ru.md). Реализация транспортов Windows/Android завершена и принята в scoped CI. Reference core этапа 5 реализован и проверен локально; далее интеграция/приёмка перед распространением; выпуск и отложенная приёмка этапа4 остаются открытыми.

## Current next work after Linux GUI coordination

Shared GUI/control operation ownership implemented and locally accepted (402 Python,
GTK recovery/24 layouts). [GUI coordination and short network checkpoint](releases/2026-09-12-control-gui-network.ru.md). Coordinated GUI/core packaging and scoped CI,
then native Windows/Android binding remain before background distribution.
Short network tests are now explicitly authorized and resumed: routes/DNS/cleanup
passed, HTTPS4/6 with two timeouts. Matched direct/TUN diagnosis now passed24/24
across Python HTTP1.1 and curl HTTP2; failures did not reproduce, no causal fix.
TD-1 remains open: obtain request-to-flow evidence when a bounded run fails.
Continue coordinated Stage5 GUI/core packaging and scoped CI. No automatic long
load/device campaign. AWG3.1 migration remains TD-2.
Independent entry/alternate gateway acceptance remains Stage6.

## Stage 5 reference protocol/application core — implemented locally

2026-09-12: carrier-independent signed config, journal, apply/health/commit/rollback,
device-signed ACK/outbox and real RNS delivery pass 381 Python tests. [Stage 5 checkpoint](releases/2026-09-12-reticulum-control.ru.md).
Current acceptance is reference Python/Linux; native/background distribution needs
common operation ownership with GUI, native storage/binding, packaging and scoped CI.
AWG3.1 stays a separate migration; Stage5 has explicit transport-version refusal.
Stage6 infrastructure independence and user-deferred device/load tests remain open.

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

## Android WG/AWG/TCP/Auto accepted; next Reticulum

Android WG/AWG passed four-ABI build, 12 unit methods, lint and real API35 x86_64
emulator:24 encrypted UDP,4 stops,cancel,system revoke (clients34660308853).
One runtime fixed WG→AWG→WG crash; profiles remain independent and encrypted.
TCP accepted: clients34676190826/source8d748f5, four ABI,18 unit,18 REALITY HTTP,
3 OS DNS calls,36 WG/AWG UDP and13 cleanup scenarios. Auto accepted in clients34679094884/sourcea51aa52: initial fallback, ongoing health
loss, finite exhaustion, cancellation and revoke. Next stage5 Reticulum.
Device update/testing stays deferred. [TCP report](releases/2026-09-12-android-tcp.ru.md).
See [Android WG/AWG report](releases/2026-09-12-android-awg.ru.md) and [Auto acceptance](releases/2026-09-12-android-auto.ru.md).

## Next, in order

1. Stage5 reference core is implemented locally (381 tests): shared Linux GUI
   operation ownership now passes local checks; native binding, coordinated packaging
   and scoped CI remain before background distribution.
   Android updater/Google Play and user-deferred device/load tests do not gate this work.
2. Before distribution: full-routing/external gateway/REALITY and actual device acceptance,
   Android release signing/versioning. APK updates and extended device/load tests remain deferred;
   short network checks were explicitly resumed and found HTTPS timeouts. Desktop0.2.9/catalogseq8 and TCP Setup0.1.0 remain published.
3. Deferred resilience experiments: concurrency1→4→8, request-to-flow diagnosis and
   second Ubuntu retest. Second independent VPS only when supplied by user; never use
   the test laptop or neighbouring services. Current timeout/stability limits remain open.
4. Native enrollment/storage, signing-root rotation/recovery, then payments/notifications.

Next development stage5; stage4 distribution/device acceptance remains open, not stable multi-platform resilience. Details, results, backups and unfinished
work: [session checkpoint](releases/2026-09-11-session-checkpoint.ru.md).

## Windows и Android реализованы; следующий блок — Reticulum (2026-09-12)

Текущий engine-crash recovery завершён отдельным отчётом; новых подпунктов в него не добавлять.
Мониторинг недоступного соединения при живом процессе завершён и проверен в scoped CI.
Интеграция AWG принята в scoped CI2026-09-12; [результат](releases/2026-09-11-windows-awg-integration.ru.md).
Автоматическое переключение Windows принято в scoped CI2026-09-12:672 макета,7 policy-сценариев,
живой AWG→TCP, отмена, исчерпание и очистка после SCM restart. Android WG/AWG/TCP/Auto также принят; далее Reticulum.
[Отчёт и границы приёмки](releases/2026-09-12-windows-auto.ru.md). Полный маршрут/REALITY требуют отдельной
приёмки до выпуска. Отложенные пользователем испытания на устройствах/под нагрузкой
не возобновлять автоматически и не смешивать с реализацией.
Android WG/AWG/TCP/Auto принят в эмуляторе; следующий шаг — этап5 Reticulum.

Latest bounded network comparison: [Matched HTTPS result](releases/2026-09-12-matched-https.ru.md).
