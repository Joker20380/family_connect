# Текущее состояние / Current state

**CHAT-UX-2 — implemented checkpoint / REVIEW REQUIRED; validation PARTIAL.**
Owner decisions: мессенджер внутри единственного главного окна; exact Android106
ICQ-classic49 GIF вместо системного picker. CHAT-UX-1 technically completed в
reviewed source/UI/package scope, но product design superseded; исходное evidence
и residual failures сохранены, не превращены в PASS нового дизайна.
На owner workstation временно установлен internal **0.2.12~l03.2.8**, candidate
`0bf09cee08e27014f27e96abbd219ce3e31a1cf8eb1f8e906434d807f0577a87`;
system `43266d97c6a9f8d4e7026727cbb4b5cb6aeea49db799f93bd798b67a8135198c` READY.
OWNER-CHAT-UX-INSTALL: dpkg/package/import checks PASS; installed UX acceptance
PARTIAL. Пользователь подтвердил ручную отправку наблюдавшегося сообщения.
CHAT-UX-2 source: embedded Stack, прежние RPC/drafts/bubbles/voice,49-face manifest,
Android aliases/boundaries, literal copy, один visibility-bound GIF clock.
Full desktop1272 PASS/84 SKIP; messenger222 PASS; parser/picker/UX72 PASS;
exact DEB/AppImage/integrity/AWG/TCP gates и14 synthetic GTK captures PASS.
Full local3353 PASS/36 прежних FAIL/101 SKIP/1 отдельная новая FD teardown ERROR
(22 vs24 descriptors, повторилась на final source); общий full-suite PASS не заявлен.
CI full suites54/54/53 FAIL без suppression. Failure IDs/ограничения сохранены в отчёте.
Собран exact Ubuntu26.04/Python3.14 **0.2.12~l03.2.9**, source `cb81cd5`,
candidate `6f312d1e7c783ea42a39ca164d93d74b0ec4faf5bac53e24c12551cedd052a5b`;
прежний system build byte-identical, .7/.8 immutable.
[CHAT-UX-2 report, hashes/screenshots/gates](releases/2026-10-26-chat-ux-2.md).
Owner .9 install / L04.2 / full L05 / TCP HTTPS diagnosis / signing / publication **NOT_RUN**.
**STOP после CHAT-UX-2. NEXT — review перед установкой .9 владельцу.**

### Предыдущий compatibility checkpoint — историческая граница

**U2604-COMPAT — CHECKPOINT PASS, только Ubuntu26.04/CPython3.14 compatibility.**
LOCAL-OWNER-UPGRADE **BLOCKED на ABI**: workstation Ubuntu26.04/system Python3.14.4,
frozen .5 требует3.12. До установки/backup/launcher migration не дошли; workstation unchanged.
Новая disposable Ubuntu26.04.1/systemd259/Python3.14.4: exact provisioning/messenger
locks,630 RECORD/hash-verified runtime members, strict imports всех17 distributions,
GTK/Adw/cairo/Secret Service/GStreamer/codec2 и129 адресных tests **PASS** без source edits.
Начальная test-runner ошибка3 imports из-за отсутствия explicit public source path
сохранена; исправлен только invocation, все129 PASS. Pins/hashes не менялись.
Собран отдельный **0.2.12~l03.2.7 / Ubuntu26.04 / Python3.14**, internal/unpublished:
candidate `c79b4feb…` / source `3df82b4` / system `43266d97…`.
Exact DEB/AppImage, strict user/system imports, real pkexec/READY, rollback,
tamper/mixed-build/locks, synthetic state и URI/user-service gates **PASS**.
Full desktop1199 PASS/83 SKIP; native144, Auto18 checks, DIRECT, lifetime15,
combined3 и AWG/TCP prestart PASS. Full suite3257 PASS/**55 FAIL**/104 SKIP без suppression;
extra root lock/umask observation воспроизводится на3.12 и3.14, isolated runtime6 PASS.
Общего CI/release PASS нет; residual failures — отдельный technical debt.
Frozen .5/3.12 hashes/IDs повторно сверены, immutable; L04.1 не переоткрывается.
Production VPN/GUI/helper/protocol/identity/cache logic не меняется. Private identity,
activation/cache/gateway не использованы. Publication/L04.2/L05/teardown/live VPN **NOT_RUN**.
[U2604-COMPAT report](releases/2026-10-26-linux-ubuntu2604-python314-compat.md).
Прежний STOP U2604-COMPAT сохранён в отчёте; установленная .7 подтверждена выше.

### Frozen Linux AWG/TCP Beta baseline — сохранён, не активный NEXT

**L04.1-LIVE-2 DONE / review accepted; L04.1 DONE — installed Linux AWG/TCP,25.10.**
Владелец принял E, F1 и F2. P1/P2 и A–D на .4 не повторялись; E/F1/F2 на .5
приняты без нового live-run. **Linux AWG/TCP Beta candidate frozen:
exact 0.2.12~l03.2.5**, candidate f0ee1760…/source1c2beb6/system8d7d78ec….
AppImage/DEB bytes неизменны; hashes/размеры повторно сверены локально, без запуска.
Candidate **internal/unpublished**, ранее установлен только в disposable guest;
не установлен на workstation, public/invitation versions и каталоги не менялись.
Поддерживаемый beta scope: activation, AWG/TCP, Connect/Disconnect, DNS/HTTPS,
state preservation и diagnostics. MESH/Auto и messenger в него не входят.
Registry restart F2 остаётся отдельным **operational observation**: первый readback
FAIL сохранён, **uninterrupted continuity NOT_PROVEN**, причина неизвестна;
assignment/configuration не изменились, registry service identity изменился.
Клиентский F2 не повторять; R3 не создавать. Это не блокер принятого client scope.
Parent **L04 IN_PROGRESS только из-за L04.2**; L04.2/L05/test-device teardown **NOT_RUN**.
Full-suite residual54/54/54 failures (historical Docker53) — отдельный technical debt,
общего CI PASS нет. Original protected state/teardown receipt сохранены.
Signing/upload/catalog update/publication **NOT_RUN**; никаких новых live/source/server
операций. [Итоговый отчёт](releases/2026-10-25-linux-installed-awg-tcp-l04-1-final.md),
[единый beta-freeze manifest](releases/2026-10-25-linux-awg-tcp-beta-freeze.json).
**STOP. NEXT — решение владельца о signing и ограниченной публикации Linux AWG/TCP Beta.**

### Исторические checkpoints — не текущие статусы или NEXT

**L04.1-LIVE-2-R2 DONE / review accepted — source/package scope.**
На exact .4 review принимает P1/P2, B1/B2/C1/C2/D PASS; E FAIL/review accepted,
F1/F2 NOT_RUN. E доказывает queued Future/busy/open/CONNECTING, не late VPN start:
helper/TUN0, generation0/pending null; fixture отменил Future до освобождения worker.
R2 явно отслеживает только normal Connect/Disconnect; успешный cancel снимает busy
и fencing запрещает старый callback. Running/done-undelivered mutation блокирует Close.
Deterministic prior-source overlay4 FAIL → targeted197 PASS, full desktop1191/84.
Новый internal .5/source1c2beb6/candidate f0ee1760…: exact integrity и оба offline
systemd255/pkexec package gate PASS. System8d7d78ec… byte/contract verified unchanged;
.4 immutable. Linux/AWG/TCP/package CI PASS; isolated root→UID/native179,
Auto18/DIRECT/lifetime15/combined3 PASS. Full CI54/54/54 failures (Docker раньше53;
дополнительный readiness-receipt assertion, причина не установлена), без fixes/retries.
Общего CI PASS нет. В самом R2 private identity/gateway/live E/F не использовались.
Source/package checkpoint принят; последующий live checkpoint указан выше.
L04.1 IN_PROGRESS; L04.2/L05/test-device teardown NOT_RUN.
[R2 report](releases/2026-10-25-linux-queued-connect-close-l04-1-live-2-r2.md).

Исторические этапы25.10.2026 (текущий итог и NEXT выше):
**L04.1-LIVE-1-RETEST DONE / review accepted**.
Review принимает fresh DNS matching request/reply на actual AWG/TCP TUN после flush,
включая валидный terminal **NODATA**; positive installed gate завершён без повтора.
Exact **0.2.12~l03.2.2**, source `57f8eff`, candidate `d9c0d07f…`, system build-9
не меняются. [Исторический RETEST и решение review](releases/2026-10-25-linux-installed-awg-tcp-l04-1-retest.md).
**L04.1-LIVE-2 PARTIAL / review accepted**: actual installed tamper/reinstall A PASS;
B1 первый отказ — root lock блокирует transport, но AWG helper up1 и pending/APPLYING
сохраняется после освобождения lock (generation0→1). Сеть/identity/cache/floors
сохранены, guest уничтожен; journal не объявлен восстановленным. B2–F NOT_RUN.
Product source/artifact bytes immutable; никаких повторов/исправлений.
FC-3YSQ-BE2D/nl сохраняются, новый issuance/provisioning/manual fetch запрещён.
L04/L04.1 IN_PROGRESS до LIVE-2 review; L04.2/L05/teardown NOT_RUN.
[LIVE-2 checkpoint](releases/2026-10-25-linux-installed-awg-tcp-l04-1-live-2.md).
D01/full suites54/54/53 failures и voice/Windows observations сохраняются.
**L04.1-LIVE-2-RESUME PARTIAL / review accepted, STOP на E** (тот же ID). Exact .4 A/B1 review
accepted; без повтора. P1/P2 continuity, B2, C1/C2 и D recovery PASS.
E: один queued Connect + Close — GUI остаётся busy/open, Future не отменён;
helper/TUN0, generation0/pending null. Только fixture cleanup, без повторного action.
F1/F2 NOT_RUN. Сеть/state/server readback сохранены; KVM/secret copies уничтожены,
original FC-3YSQ-BE2D/nl сохранён. Source/candidate immutable. L04.1 IN_PROGRESS;
L04.2/L05/teardown NOT_RUN. Review E принят; correction только R2 выше.
[Продолжение того же checkpoint](releases/2026-10-25-linux-installed-awg-tcp-l04-1-live-2-continuation.md).
**L04.1-LIVE-2-R1 DONE / review accepted (source/system/package).**
Final internal **0.2.12~l03.2.4**, source053c4e5, candidate42ea0699…,
новый system8d7d78ec…/authorization2 (не build-9). .3 — intermediate immutable.
Actual AWG/TCP red→green: up1/start0, IDLE/generation2/pending null, poll PASS;
unknown outcome сохраняет pending до same-owner recovery и первую причину ошибки.
Exact integrity/systemd255/pkexec/rollback/DEB/AppImage/coherence/old-build refusal
PASS; desktop1195 PASS/96 SKIP. Linux/AWG/TCP/package CI PASS; native/DIRECT
первый отказ сохранён, один unchanged rerun PASS. Full CI54/54/53 failures;
общего CI PASS нет.
В самом R1 live B1/B2–F NOT_RUN; private state/gateway не использовались.
Последующий installed результат — RESUME выше, не перенос evidence между scopes.
[R1](releases/2026-10-25-linux-prestart-journal-l04-1-live-2-r1.md).
**Граница завершения — STOP; NEXT review PARTIAL L04.1-LIVE-2 (E).**

Предыдущий **L04.1-LIVE-1 PARTIAL принят review**; final-2 больше не candidate
для завершения L04.1. Его положительное live evidence ниже сохраняется исторически.
L03.1/L03.2 **DONE (review accepted)**; parent L03 **DONE** в scope внутреннего
Linux-кандидата. AUTH/PROVISION **DONE, review accepted**. L04/L04.1 **IN_PROGRESS**;
LIVE-2 теперь PARTIAL (см. текущий checkpoint); L04.2 **QUEUED / NOT_RUN**.
Exact final-2 не изменён.
Реальная KVM Ubuntu24.04/systemd255: DEB/GUI/pkexec/READY PASS; AWG×3 и TCP×1,
DNS/HTTPS/64KiB download+upload, reconnect/handoff и network cleanup PASS.
Original AppImage AWG/traffic и single-owner/confirmed GUI close PASS; после reopen
Disconnect отказал: «Connection settings are being updated», actual tunnel остался.
STOP: без новых connect/исправлений. Cleanup-only GUI Disconnect после освобождения
lock восстановил baseline; guest/временные secret copies уничтожены. FC-3YSQ-BE2D,
nl bindings, исходный protected state/cache/floors и teardown receipt сохранены.
Device-scoped gateway cleanup → readback → registry revoke остаётся NOT_RUN.
D01 открыт:54 residual failures; D02.1-R PARTIAL/NOT_RUN; Windows/voice сохранены.
[Отчёт LIVE-1 и точная граница отказа](releases/2026-10-25-linux-installed-awg-tcp-l04-1-live-1.md).
LIVE-1 — исторический checkpoint, не активный NEXT. L04.1-LIVE-2/L04.2/L05/teardown NOT_RUN.

### Принятый checkpoint L03.1

Срез **L03.1**, 25.10.2026: внутренний system/runtime build-9; review accepted.
D01.3/D01.3-R приняты в public completion/admission scope; L01/L01-R,
локальные L02/L02.2, D03/D04/D05 и native границы сохранены. D01 открыт,
D02.1-R PARTIAL/NOT_RUN. [Отчёт L03.1](releases/2026-10-25-linux-system-runtime-l03-1.md).
758 payload files: manual/Auto/chat, native/RNS/Python3.12, anchor, AWG3.1/TCP.
94 финальных адресных PASS (umask077); desktop1120 PASS/24 SKIP. Systemd255 PASS:
imports, реальный polkit/UID IPC, idle units, install exclusion, rollback/capabilities.
Rollback повторно маскирует службы до восстановления old source; actual start refusal PASS.
Source `f826dbd`: Client Linux и isolated native/root→UID/Auto/DIRECT CI PASS.
После обрыва25.10: неизменный build-9 повторно проверен в disposable systemd255;
package/system smoke и94 адресных PASS; исходники/публичная поставка не менялись.
Control/phase0/Docker: по54 failures, errors0; voice observation сохранён. Не общий CI PASS.
Review L03.2 теперь принят; родительский L03 DONE только в scope внутреннего кандидата.
Ни public versions/catalogs, ни установка на рабочую машину не разрешены.
Review L03.1 принят; это предыдущий, не активный NEXT.

### Предыдущий checkpoint D01.3-R (review принят 25.10)

Срез **D01.3-R**, 24.10.2026: DIRECT completion/admission contract исправлен;
**source gate PASS, review pending**.
Review D01.3 принял ChatBridge и Host/ServiceHost; D01.3 **PARTIAL по review**
из-за оставшегося close→active.pop окна DirectHost. Только эта коррекция;
**NEXT — review D01.3-R**, без автоматического L03.
Вход: чистая актуальная `main` = remote `68e4029f58d54384471576c623b08e89752f2c94`.
[Отчёт D01.3-R](releases/2026-10-24-desktop-chat-direct-completion-d01-3-r.md):
actual DirectHost/DirectBridge/Authority, Unix IPC и барьер после фактического close/EOF.
До: **1 failed**, active4/native opens3/API sends2, dependent open ConnectionResetError.
После: close и active.pop под одним admission lock после прежнего cleanup;
четвёртый mailbox проходит, пятый отклонён, закрытие возвращает capacity.
**30 PASS**: пять новых DIRECT + прежние24 completion + исходный bounded-mailbox.
Cancel/deadline/shutdown bounded; descriptors/handlers/DIRECT monitors учтены;
synthetic socketpair backing не заменяет native/installed acceptance.
Зависимые DIRECT/public IPC/error/lifecycle **326 PASS**, root→UID/process **13 PASS**.
Production source `050f06baef8b94e81d1bd4becb7f4fc38d1a6744`; final test source
`b910edbd108fc5e146792b6db966d6f8daf53b1a` pushed/remote-verified. Follow-up только
согласует post-close Event с EOF observer: **5 PASS**, old-host overlay red1 без rollback.
На финальном source Client Linux **40134155274/120992056110 PASS**, включая
mandatory desktop pytest. Isolated-linux **40134155291/120991993095 PASS**:
прежние15 authenticated, combined3, root→UID/process, Auto/DIRECT kernel и race.
Full suites отдельно: control **3061/54/138**, phase0/tests **3061/54/138**,
Docker **3059/54/140**, errors0 (passed/failed/skipped). Voice/AWG/TCP PASS;
Windows protocol job того же Auto workflow FAIL, вне scope/без разбора и перезапуска.
Это не общий CI PASS. Точные SHA/jobs в отчёте; прежние54 failures/voice не исправлялись.
Принятые L01/L01-R, локальные L02/L02.2, D03/D04/D05/native semantics сохранены.
D01 открыт, D02.1-R PARTIAL/NOT_RUN. Версии/identity/keys/history/settings/floors/
reference pins неизменны. L03/install/live/publication/Windows/fleet/iOS NOT_RUN.
**STOP. NEXT — review D01.3-R.**

### Предыдущий checkpoint D01.3 (evidence до DIRECT review correction)

Срез **D01.3**, 24.10.2026: public chat IPC completion/admission race исправлена;
**source gate PASS, review pending. NEXT — review D01.3.**
Вход: чистая актуальная `main` = remote `d448e99b55e594522c02234ac2a87575603a6bbb`.
Review L02.2 принят в local source/native scope; исходный локальный критерий
L02 (authenticated OFF→ON/publication→EXISTING_EXIT→OFF через Manual и Auto) выполнен.
Это не installed/live/F-01 и не общий CI PASS. D01 открыт, D02.1-R PARTIAL/NOT_RUN.
[Отчёт D01.3](releases/2026-10-24-desktop-chat-admission-d01-3.md): actual Host/
ServiceHost/ChatBridge, Unix IPC и event barriers; synthetic native lane только
для адресного public admission evidence. До: probe и prepare допускают следующий
open до cleanup, **2 failed**, ConnectionResetError. Это та же выявленная гонка,
но точная причинность исторического CI BrokenPipeError не установлена.
После: EOF управляющего обмена ждёт завершения cleanup в пределах исходного
deadline, максимум4s; EOF/removal сериализованы с admission. Caps4/native caps,
handler/monitor accounting, typed errors/cancellation и no-replay сохранены.
Локально **266 passed** (24 новых + зависимые Python/IPC/error/lifecycle).
Source `23e3c5513ab9c37e919f228066c0e23f733a997e` pushed/remote-verified:
Client Linux (включая mandatory desktop pytest) и isolated-linux PASS; локально
прежние15 authenticated, combined3 и13 root→UID/process PASS. Follow-up
`f258c17007102634fead9894bcfe9a82f6db44cf` публикует тестовый handler до ответа
(24 PASS); mandatory desktop pytest **40132223364/120986275264 PASS** на этом SHA.
Весь Client Linux job PASS. Завершившиеся full suites на `f258c17`: control
**3056/54/138**, phase0/tests **3056/54/138**, Docker **3054/54/140**, errors0
(passed/failed/skipped); точные jobs в отчёте, не общий CI PASS. Voice PASS без
изменений voice-кода; прежний holding-state failure сохранён отдельным результатом.
Production-код после `23e3c55` не менялся. Общий D01 остаётся открыт;
54 residual failures и voice failure не исправлялись в этом scope. Прежние15 authenticated,
combined3, root→UID/process, Auto/DIRECT и full suites не отключены.
Identity/history/settings/keys/floors/reference pins и установленный baseline
не менялись. L03/установка/live/publication/Windows/fleet/iOS NOT_RUN.
**STOP. NEXT — review D01.3.**

### Предыдущий checkpoint L02.2 (evidence до принятия review)

Срез **L02.2**, 24.10.2026: локальная authenticated цепочка
**SERVICE_ONLY → VPN CONNECTED/publication → EXISTING_EXIT → новый SERVICE_ONLY**
прошла отдельно через настоящий manual Supervisor и Auto/MESH.
**Review pending; родительский L02 PARTIAL. NEXT — review L02.2.**
Вход: чистая актуальная `main` = remote `9d472e96b6854f26053ca8d797d2c73aad18b0ef`.
Review L02.1-R2 принят. [Текущий отчёт](releases/2026-10-24-linux-chat-mesh-l02-2.md):
UID1000 IPC, настоящие native owners/FamilyTLS/Mux, TUN, private D-Bus/resolved,
kernel route/DNS readback, native health/publication, broker bind/renewal и cleanup.
На каждом участке challenge/register/duplex fixed-mailbox; три последовательных
transport opens, generation/operation lease accounting, held cleanup/late acquire,
profile mismatch, active-mailbox cancellation, signed expiry/revocation, DENIED/no replay.
Исправлены потеря release при CONTROL4 и выявленная race-инициализация packet RX;
caps/reference pins и порядок drain→worker exit→admission сохранены.
Локально 242 адресных Python, 13 root→UID/process, прежние15 authenticated,
combined gate, native/race, оба Auto/DIRECT kernel gates и 175 pins PASS.
Source **`dac0f6b45be6ed8703d3de93ff5fdbc67462eabe`** pushed/remote-verified.
CI20:29UTC: isolated-linux **40129362252/120977564710 PASS**, включая прежние15,
новый combined **3 passed / 79.04s**, оба kernel gates и native race. AWG/TCP PASS.
Control **3032/54/138**, phase0/tests **3032/54/138**, Docker **3030/54/140**,
errors0. Client Linux **1003/1/94**: bounded-mailbox BrokenPipeError;
voice: pointer/holding-state failure. Причины этих двух failures не установлены,
тесты не отключались/не исправлялись; не общий CI PASS. Точные jobs в отчёте.
Завершившийся R2 source `89e20a3437b2ba1b02f7d1649487579678158373`:
control **3030/54/135**, phase0/tests **3030/54/135**, Docker **3028/54/137**
(passed/failed/skipped), errors0; phase0/tests перепроверен по собственному логу.
Isolated-linux с15 authenticated, Client Linux, AWG/TCP/voice PASS; не общий CI PASS.
Внешние rendezvous/media и room provider заменены fixture; mailbox — byte relay,
не LXMF/node (L05), не live Telemost/installed/F-01. Сеть/DNS рабочего хоста не менялись.
D01 открыт; D02.1-R PARTIAL/NOT_RUN; L01/L01-R/D03/D04/D05 сохранены.
Identity/history/settings/keys/floors, версии и установленный baseline не менялись.
L03/установка/live/publication/Windows/fleet/iOS NOT_RUN. **STOP перед review L02.2.**

### Предыдущий checkpoint L02.1-R2 (историческое evidence)

Срез **L02.1-R2**, 24.10.2026: native status classification исправлена;
**review pending; родительский L02 PARTIAL. NEXT — review L02.1-R2.**
Вход: чистая актуальная `main` = remote
`323d49b09af57a809ba467f27e9c4650a97d7844`; checkout не откатывался.
[Текущий отчёт](releases/2026-10-24-linux-chat-mesh-l02-1-r2.md): настоящий
CONTROL4 limiter воспроизвёл отмену исправного поколения; malformed native route
терял DENIED до ChatBridge/ChatHTTP. Теперь BUSY — ограниченный отказ/перенос
проверки watcher, не healthy и не terminal; после освобождения очереди тот же
authenticated transport/lease. DENIED сохраняется до `access_rejected`, без HTTP
send/replay; terminal/protocol failure закрывает допуск и запускает прежний cleanup.
Review L02.1-R atomic RetainChat и обоих terminal-generation исправлений принят;
generation pin/refcount/drain→worker exit→flock ordering и IPC caps не менялись.
Локально 117 адресных Python/IPC, 66 dependent error/lifecycle, 13 root→UID/process
и 15 authenticated (включая прежние 13) PASS; native Go/race и 175 reference pins
PASS. R2 source **`89e20a3437b2ba1b02f7d1649487579678158373`** committed/pushed,
remote SHA проверен равным. CI19:17UTC: Auto/isolated-linux, Client Linux,
control/phase0/Docker, AWG/TCP/voice IN_PROGRESS, не общий PASS;
точные новые jobs — отдельно в текущем отчёте.
Завершившийся CI **предыдущего** source `6556a902c723a3ef73486733f090cea6f388d099`:
control **3015 passed / 54 failed / 133 skipped**, phase0/tests **3015 / 54 / 133**,
Docker **3014 / 53 / 135**, errors0; isolated-linux с13 authenticated,
Client Linux, AWG/TCP и voice PASS. Это не общее CI acceptance.
Mandatory suites и Auto/DIRECT kernel gates сохранены; full suites/неизменённые
kernel scripts локально NOT_RERUN. Посторонние failures не исправлялись.
Combined VPN publication→EXISTING_EXIT→OFF **NOT_RUN**, отдельный этап, не расширен.
D01 открыт; D02.1-R PARTIAL/NOT_RUN; L01/L01-R/D03/D04/D05 сохранены.
Identity/history/settings/keys/floors/reference pins и версии не менялись;
установка/live/publication/L03/Windows/fleet/iOS NOT_RUN. **STOP перед review L02.1-R2.**

### Предыдущий checkpoint L02.1-R (историческое evidence)

Срез **L02.1-R**, 24.10.2026: terminal native generation fencing/recovery исправлен;
**review pending; родительский L02 PARTIAL. NEXT — review L02.1-R.**
Вход: чистая актуальная `main` = remote
`878d2918ce4ba014bd7fe73a1f223753ce18748b`; checkout не откатывался.
[Текущий отчёт](releases/2026-10-24-linux-chat-mesh-l02-1-r.md): оба actual-native
отказа воспроизведены до исправления; после peer/Mux failure и asynchronous
bootstrap failure новый demand восстанавливает authenticated challenge/register/
duplex fixed-mailbox на одном новом транспорте, без idle45s/readiness expiry.
Проверяется native route; operation acquire атомарно удерживает только указанное
поколение через `RetainChat`, а не создаёт новое владение за старой lease.
Accepted Coordinator/refcount и все 175 Android106/reference pins не изменены.
Локально 580 Python/native/owner/mailbox, 13 root→UID/process и 13 authenticated
проверок PASS; Go/race и Auto/DIRECT isolated-kernel PASS. Точные source SHA,
повторные проверки и CI receipt фиксируются в текущем отчёте отдельно от L02.1.
Source **`6556a902c723a3ef73486733f090cea6f388d099`** committed/pushed,
remote SHA проверен равным. CI **18:42 UTC**: Client Linux, Auto protocol matrix,
TCP и readiness golden PASS; isolated-linux/authenticated gate, control,
phase0/tests/Docker, AWG и voice ещё IN_PROGRESS, не общее CI acceptance.
Законченный CI L02.1 `a2b105de49391928d4bb9c15c4d5ee2305085918`: control
**3015 passed / 54 failed / 127 skipped**, phase0/tests **3014 / 55 / 127**,
Docker **3013 / 54 / 129**, errors0. Дополнительный phase0 failure:
`test_ui_unavailable_server_ack_is_authoritative`, причина не установлена.
Mandatory suites сохранены; эти failures не исправлялись в L02.1-R.
Combined VPN publication→EXISTING_EXIT→OFF **NOT_RUN**, отдельный следующий этап,
не начат. D01 открыт; D02.1-R PARTIAL/NOT_RUN. L01/L01-R, D03/D04/D05 сохранены.
Identity/history/settings/keys/floors и версии не менялись; installation/live/
publication/L03/Windows/fleet/iOS не выполнялись. **STOP перед review L02.1-R.**

### Предыдущий checkpoint L02.1 (историческое evidence)

Срез **L02.1**, 24.10.2026: lifetime исправлен; **комбинированная приёмка PARTIAL**.
Вход: чистая актуальная `main`, remote проверен
`9b7418e2675d1e30787f491f8c924467835e7b05`; checkout не откатывался.
**Родительский L02 остаётся PARTIAL. NEXT — review L02.1.**
[Отчёт L02.1](releases/2026-10-24-linux-chat-mesh-l02-1.md): отдельная native lease
поколения плюс operation leases; idle45s/expiry/preemption/cancel/shutdown сохраняют
drain→worker exit→flock release. Исправлена typed-nil ошибка native IPC при отказе
Acquire. Старый host: authenticated challenge200 → leases0 → удержанный cleanup →
register UNAVAILABLE; новый: challenge/register/duplex fixed-mailbox, один transport.
Локально 556 Python/native + 24 owner/mailbox, 13 root→UID/process; native/race и 7
authenticated fixture checks; точные результаты и ограничения — в отчёте.
Fixture изолирован Go overlay: реальные native owner/IPC/FamilyTLS/Mux и Linux
lifecycle, но внешние rendezvous/carrier/broker и readiness-fetch заменены;
mailbox peer — байтовый relay, не установленный LXMF/node.
Полный VPN ON/publication/EXISTING_EXIT/OFF gate **NOT_RUN**: peer ещё не обслуживает
generic packet/DNS/owned-TUN health и broker lease lifecycle. Это не требование
live/private capsule. D01 открыт; D02.1-R PARTIAL/NOT_RUN; L01/L01-R/D03/D04/D05
сохранены. Версии/установка/публикация не менялись; L03 не начат.
Source `a2b105de49391928d4bb9c15c4d5ee2305085918` committed/pushed, remote SHA
проверен равным. CI срез **18:07 UTC**: новый authenticated gate, Auto/protocol,
root→UID/оба kernel gates, Client Linux, AWG/TCP, voice PASS. Mandatory control,
phase0/tests и phase0/Docker ещё **IN_PROGRESS**, не PASS; прежние failures не
объявляются исправленными. Точные source jobs — в отчёте L02.1.

### Предыдущий checkpoint L02 (историческое evidence)

Срез L02, 24.10.2026. Вход: чистая актуальная `main`, HEAD = проверенный `origin/main`
`b3301d07cb6e06f3c032b31a99f39e9535d3b21d`; checkout не откатывался.
**Review L01/L01-R принят пользователем в Linux source/native/root→UID/isolated-kernel scope.**
**L02 PARTIAL; NEXT — review L02.** [Отчёт](releases/2026-10-24-linux-chat-mesh-l02.md):
demand SERVICE_ONLY host, межпроцессный flock admission, manual/Auto drain→cleanup
и происхождение регистрации подключены в source. Полный authenticated native
API/mailbox OFF→ON→OFF через реальные Linux services ещё не доказан: положительные
host fixtures используют synthetic lane; отдельный process gate — реальные idle workers.
Это не L02 DONE, не установленная функция и не разрешение начать L03.
Source `383ef3606aaa4dbd29f0c7c0f755e6faec6e309f` pushed/remote-verified.
Локально 354 + 82 адресных Python/native и 13 root/process/UID PASS; Go/race и
DIRECT/Auto isolated kernel PASS. CI Auto/new gates/Client Linux/AWG/TCP/voice PASS;
полные control и phase0/tests FAIL (каждый 3015 passed / 54 failed / 120 skipped),
Docker FAIL (3013 passed / 54 failed / 122 skipped). Точные CI jobs/статусы —
в [L02](releases/2026-10-24-linux-chat-mesh-l02.md), не перенос с прежнего SHA.

Принятое evidence L01-R (точные SHA не заменяются новым checkpoint):
[L01-R](releases/2026-10-24-linux-chat-direct-l01-r.md): runtime0711 при unit umask0077,
проверенный registration route без импорта EXIT response в root authority, настоящий
TCP/TLS fatal alert остаётся DENIED до ChatHTTP, без fallback. Before/after записаны.
Локально: 145 Python/native + 49 mailbox/owner, 6 root→UID checks, шесть Go/race
packages и isolated DIRECT kernel PASS. Root→UID не является installed acceptance.
Source `4fab7b66d27d8a0a5306a6a923c120f023389218` pushed/remote-verified:
Client Linux, Auto/protocol/root→UID/оба kernel gates, AWG/TCP PASS. Текущий voice job
PASS, но прежние GTK failures не исследовались и не объявлены исправленными/flaky.
Control/phase0 full pytest FAIL; Docker: 2980 passed / 53 failed / 115 skipped, exit1.
Обязательные suites/negative gates сохранены; точные jobs и SHA — в отчёте L01-R.
D01 открыт, D02.1-R PARTIAL; full-suite/GTK voice failures вне scope.

Историческое положительное evidence L01 ниже сохранено только для своих SHA:
[L01](releases/2026-10-24-linux-chat-direct-l01.md): ChatOwner/daemon используют отдельный
root DIRECT endpoint, fixed chat API и mailbox только из root-проверенной регистрации.
Native underlay bind/mark до connect; SYSTEM fallback отсутствует в этом пути.
UID/device/chat-key/sequence/expiry и AF_UNIX relay ограничены; VPN owner не создаётся.
Локально: 141 chat/admission/D03/package + 49 mailbox/owner PASS; Go/race и isolated
kernel с synthetic TLS peer PASS. Installed/live, L02 и полные установщики NOT_RUN.
`bff34eb` CI: Client Linux/Auto protocol/AWG/TCP PASS; full control/phase0/Docker и voice FAIL.
Первый новый kernel gate FAIL; harness-only `edc79c2` переносит test-worker из writable
`/opt` под trusted `/root`, не ослабляя admission: Auto bridge/isolated DIRECT kernel CI **PASS**.
На `edc79c2` phase0/tests FAIL; Docker: 2976 passed / 53 failed / 109 skipped,
exit1; другие filtered jobs NOT_RUN.
Evidence и разные SHA — в отчёте; старые counts не переносятся.
[D03](releases/2026-10-24-chat-http-terminal-d03.md) и [D04](releases/2026-10-24-auto-lifecycle-d04.md) review accepted; D02.1 collection/import
isolation и D02.2 public-reference приняты. Dependency-части D01.1/D01.2 приняты;
их PARTIAL и общая CI-приёмка D01 не закрыты.
[D05 review accepted](releases/2026-10-24-desktop-provider-d05.md): target/selected-next, проверенное
assignment и applied metadata используются Linux NormalOwner/Platform/GuardedHost.
Legacy gateway_id неизвестен; assignment только после fresh fetch/floor/readback/inspect,
applied только после guard.ready. Refresh не вызывает configure/apply/close; IPC не расширен.
Clean export: provider/model/platform/native/catalog 162 PASS, ownership/service/chat 213 PASS,
0 failures/errors/skips. Native normal-stdio проверен с синтетическими материалами;
installed/live/F-01 и dynamic fleet не приняты. Code `c53265d` pushed/remote-verified:
Auto bridge Linux/AWG/TCP PASS, Client Linux job завершён PASS (перепроверен в L01).
Control/phase0: каждый 2930 passed / 54 failed / 0 errors / 107 skipped, exit1;
Docker: 2929 passed / 53 failed / 0 errors / 109 skipped. Voice GTK Return gate FAIL, причина неизвестна; не исправлялся и не объявляется flaky.
D04 evidence уточнён: на `b41e1ad` одинаковый набор 54 failures в control/phase0/Docker;
docs-only phase0 `3f9854a` завершился FAILURE отдельно от code SHA. D01 остаётся открыт.
Review коррекции D02.1-R и [fleet-документации `1725656`](releases/2026-10-24-desktop-fleet-boundary.md)
завершён. [Граница desktop/fleet](desktop-architecture.md#desktop-fleet-boundary) сохраняется:
D05 реализует только внутреннюю Linux-границу; W01/W02, UI/миграция и fleet gates остаются отдельными.
[D02.2 DONE, review принят](releases/2026-10-24-rns-reference-d02-2.md): public mappings
с прежними accepted pins; clean export 49 passed / 1 прежний skip, collection 3051/0 errors;
public verifier и настоящий `--capsule` (2073 files + APK/native hashes) PASS.
Исторические CI counts `da8670e` сохранены в отчёте, не переносятся на D05.
[D02.1-R PARTIAL, коррекция принята review](releases/2026-10-24-historical-runner-d02-1-r.md): bootstrap vector и original API
добавлены; retained inputs явно перечислены, preflight/snapshot fail-closed. Чистая collection
3031/0 errors, адресные 110 passed. Полный исторический запуск **NOT_RUN**: у delivery-check,
Java runtime/classes и трёх JARs нет подтверждённых artifact pins; существование файлов не PASS.
Collection/import isolation D02.1 подтверждено review. Комплектность исторического replay ещё
не закрыта. Полные suites локально не запускались; старые CI counts ниже — только `6a0a982`.
Code `85b29da` pushed/remote-verified; по отчёту D02.1-R control/phase0/tests/Docker build
были IN_PROGRESS без full pytest counts; в документационном checkpoint CI не перепроверялся.
[D02.1 DONE](releases/2026-10-24-fixture-boundaries-d02-1.md), code `6a0a982`: чистый export —
collection 2977 + 9 errors → 2996 / 0 errors; helpers/import/runner — 75 passed.
В трёх CI окружениях collection errors = 0; полный pytest остаётся FAIL (56 failures):
control/phase0 2834 passed, 106 skipped; Docker 2832 passed, 108 skipped. Остались capsule/
reference, nginx contract, expiry, privacy и socket failures; не исправлялись.
Шесть исторических overlay-файлов сохранены и отделены; исторический runner в D02.2 не менялся.
[D01.2 PARTIAL](releases/2026-10-24-control-ci-d01-2.md): на pushed `07b52e3` Python3.13
strict imports и адресные gates PASS в control/phase0/tests/Docker tests-stage;
Docker root 22 passed, адресные 59 passed. Каждый полный suite прерван: 9 collection
errors owner_handoff/prepare, exit 2 (D02). Общий CI FAIL; последующие GUI/package/cargo/
failover проверки не выполнены. Runtime/fixtures/collection policy не менялись.
[D01.1](releases/2026-10-24-desktop-ci-d01-1.md): локальные реальные импорты PASS,
адресные 59 passed; локальный desktop 877 passed / 64 skips / 0 failures/errors.
На pushed `26f71d6` imports/адресные CI PASS; полный suite FAIL: отсутствующая RNS capsule,
в AWG также Auto lifecycle assertion. Подробности и точные counts — в отчёте; продукт/fixtures не исправлялись.

## Цель и порядок работы

Довести существующие Linux GTK4/libadwaita и Windows WinForms до функционального
и визуального соответствия принятой Android beta106-recovery, включая мессенджер,
голос, уведомления, объявления, настройки, приглашения, диагностику и обновление.
Сохранить полезные desktop-функции, модель привилегий и пользовательские данные.
Общий PARITY PASS не достигнут; процент по объёму исходников не является приёмкой.
Работа идёт отдельными ограниченными задачами из [PLAN](PLAN.md), без автоперехода.

## Android reference / exact pins

- APK: `FamilyConnect-0.1.18-beta106-recovery.apk`, принятый native105.
- APK SHA256: `242855c43e889e708234ce2f687fa02d37bccb1eee408904f09216b6abd8f020`.
- Signer SHA256: `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
- native105 SHA256: `37ba4fac656811dd979688a274f45aed85a3aa567f1fafb3987a81c020fa91f1`.
- Точные APK/source/native inventories и 175 общих pins: [reference manifest](../clients/shared/android106-reference.json).
- Source capsule: `state-client-build/owner-diagnostic106-20261022/android-source`;
  delivery: `state-client-build/owner-diagnostic106-20261022/delivery/`.
  Inventory 2073 файлов: `8574228fc809fdbd67b3d92680e09c979fe930599a47e4ed1b47fd30f872ed0c`.
- [Chat pins](../clients/shared/android106-chat.json), [UI contract](../clients/shared/android106-ui.json),
  [feature matrix и исходные наблюдения](releases/2026-10-23-desktop-parity106.md#desktop_feature_parity).
  Android-код в корне и лабораторные fixtures не заменяют принятую source capsule.
- Принятая база: P1 effective RS32/32 + согласованный CREDIT128, P0/LEGACY64,
  health102, cancel/timeout103, reorder104, pressure105, bounded JSON-export106.
  RS согласуется до Family TLS, Mux ALPN не подменяет RS; профиль зависит от обоих концов.

## Состояния поставки — не смешивать

| Уровень | Подтверждённое состояние |
|---|---|
| SOURCE | Frozen Linux candidate source `1c2beb6`, system source `053c4e5`; R2 принят. Freeze не меняет product source. |
| LOCAL TESTS | R2 targeted197 PASS, desktop1191 PASS/84 SKIP; isolated root→UID/native179, Auto18/DIRECT/lifetime15/combined3 PASS. Это прежние receipts, не новый запуск. |
| CI | R2 Linux/AWG/TCP/package PASS; control/phase0/Docker54/54/54 failures — отдельный долг, не общий CI PASS. [Точные jobs](releases/2026-10-25-linux-queued-connect-close-l04-1-live-2-r2.md). |
| BUILT | Exact internal Linux `0.2.12~l03.2.5` AppImage/DEB frozen без rebuild/repack; IDs/hashes в [manifest](releases/2026-10-25-linux-awg-tcp-beta-freeze.json). Не полный parity release. |
| INSTALLED | L04.1 DONE/review accepted в installed Linux AWG/TCP scope; disposable guest удалён, workstation rollout NOT_RUN. L04 IN_PROGRESS только из-за L04.2; MESH/Auto/messenger NOT_RUN. Windows runtime не принят. |
| PUBLISHED | Candidate internal/unpublished; signing/publication NOT_RUN. Последние документированные public Linux0.2.11 / Windows0.2.15 и invitation/download/catalog links не менялись; в freeze не перепроверялись по сети. |

## Продуктовый baseline: phase22

[Phase22, 24.10 08:53 CEST и остановка 08:55](releases/2026-10-23-desktop-parity106.md#linux-user-chat-admission-and-existing-exit-handoff-2410-phase22).
Linux ChatOwner подключён к **EXISTING_EXIT** через отдельный UID/device-bound root
chat endpoint; fixed API/mailbox используют существующего MESH owner, не второй VPN worker.
**SYSTEM — обычная маршрутизация ОС, НЕ protected-underlying DIRECT.**
Общий Go service-only adapter существует; **Linux host lifecycle ещё NOT_INTEGRATED**.
Требуется **одно активное владение транспортом**, не вечный PID: worker имеет свой lifecycle.
**Windows public/native chat endpoint на baseline — NOT_INTEGRATED.**

Границы доказательств phase22:
- Реальные Unix framing/SO_PEERCRED/SCM_RIGHTS, 64KiB duplex/half-close, cancel,
  deadlines, capacity и FD cleanup проверены в изолированном same-user fixture.
  Ожидаемый root UID заменён UID fixture; установленная root/user граница NOT_RUN.
- Native lane/session в host fixture синтетические: это не media/TUN/gateway egress PASS.
- Реальные ChatOwner/encrypted store, disposable identity proofs и локальные ChatAccess
  handlers: register/revoke/reopen. Pending node не выдавался за доставку сообщений.
- 175 общих / 2073 capsule checks и шесть chat pins — исторический PASS phase22;
  в D00 они не запускались. Наборы PASS перекрываются, их числа не суммируются.
- Phase22 не снимала новые UI screenshots. Имеющиеся Android GPU/GTK captures —
  частичные доказательства, не полный visual parity и не Windows runtime acceptance.
- [Source checkpoint](releases/2026-10-24-source-checkpoint.md) отдельно описывает
  последующую EOF/whitespace подготовку; старые hashes не выданы за тест нового исходника.

## Артефакты и ограничения обновления

Текущий Linux AWG/TCP Beta — exact .5 в [freeze manifest](releases/2026-10-25-linux-awg-tcp-beta-freeze.json).
Ни установки, ни rollback в freeze нет; matching full pair/root reinstall допустим
только отдельным решением при idle/confirmed cleanup, с сохранением state/floors.
L08 upgrade не принят; legacy updater не объявляется full-bundle updater.

Исторический phase22 component-r18 (не текущий beta candidate): все три файла в
`state-client-build/desktop-parity106-20261024/`:
`bridge-linux-r18/fc-mesh`, `bridge-windows-r14/fc-mesh.exe`,
`mesh-system-r18/FamilyConnect-MESH-system-amd64.tar.gz`.
[Точные SHA256, inventory и требования](releases/2026-10-23-desktop-parity106.md#internal-artifacts-and-upgrade-boundary).
Component-r18: 98 members, 22 root / 4 common modules; Linux x86_64 systemd254+,
resolved/iproute2/polkit/TUN/Python3 и согласованный GUI. Это НЕ полный AppImage/DEB.
Новых update-manifest/Authenticode/driver signatures нет; подписи не взаимозаменяемы.
Linux updater принимает **legacy six-file archive**; переход на полный bundle ещё
требует реализации (L08). Полный внутренний пакет (L03/W10) предшествует установленной приёмке.
Identity/history/settings сохранены в локальных fixtures, но installed upgrade ещё не принят.
D00 ничего не устанавливает: runtime rollback не нужен; прежние установки/state сохраняются.

## Блокеры / оставшаяся реализация

- D01.1/D01.2 PARTIAL, dependency gates приняты; review D02.1 collection/import isolation и D02.2 public-reference принят. D02.1-R historical replay PARTIAL/NOT_RUN. Остальные CI failures требуют отдельной оценки, не расширяют L01 автоматически. Общий D01/CI acceptance открыт до полного PASS.
- D03/D04/D05, L01/L01-R, local L02/L02.2 и L03 review accepted. W01/W02, L07/W09, L08/W12 не закрыты; очередь не запускается автоматически.
- D03: [исправление и детерминированные регрессии](releases/2026-10-24-chat-http-terminal-d03.md)
  сохраняют HTTP/TLS/invalid_response/timeout/cancellation при ошибке teardown.
  Это локальная логика с synthetic transport, НЕ installed/live delivery PASS;
  review D03/D04 принят; D05 не расширяет fixed chat DIRECT/service-only scope.
- L04.1 DONE только в installed AWG/TCP scope. Parent L04 IN_PROGRESS только из-за L04.2;
  L04.2 MESH/Auto, L05 messenger и test-device teardown NOT_RUN; recovery/visual/upgrade остаются gates.
- W01–W12: Windows native↔broker, Auto/recovery и продуктовые функции, затем полный installer,
  installed runtime и upgrade. Cross-build/Wine/headless не заменяют Windows TUN/driver acceptance.
- R01: конечные точные пакеты и проверки их установки/обновления; публикация отдельно.

## Неизменные ограничения

- Не пересобирать/публиковать Android106, не трогать активные MESH-сессии и общий gateway ради desktop.
- P1 разрешён только трём согласованным Android-устройствам; desktop identities не считаются
  разрешёнными автоматически. Точечная политика требует отдельного операторского решения, не global/FIELD grants.
- Не копировать Android identity/Support ID на ПК; сохранять старые ключи, историю, настройки,
  активацию и `familyconnect://`. Не ослаблять TLS/Family/roles/revocation/expiry/floors/directory.
- Не включать Q1/TLS packing/FEC/QUIC/FIXED4M или исследовательские SACK/timebase patches.
  Не выпускать неподдерживаемый пользовательский трафик напрямую ради smoke.
- Live-бюджет при отдельной приёмке: до32MiB прикладных данных на ОС, нормальный Wi-Fi/Ethernet;
  media overhead/фон учитывать отдельно. Android field check не блокирует локальную desktop-разработку.
- Будущие emulator checks: KVM + подтверждённый host NVIDIA GPU, 2 cores, CPUQuota150%,
  максимум180s, stop85°C CPU/80°C GPU; без SwiftShader fallback/idle emulator.
  [Тепловой инцидент и ограниченный GPU capture](releases/2026-10-23-laptop-thermal-diagnostic.md).
- Проверки выбирать по изменённому риску и обязательному gate; не повторять весь исторический набор
  без причины. Source push ≠ CI PASS ≠ installation ≠ publication. [Правила](../AGENTS.md).
- Capsules, приватные доказательства, бинарники, ключи и state остаются локально, вне Git.

## Другие незакрытые обязательства — не текущие задания

- Закрытая Android-группа: физические tester updates106/P1 и cold-bootstrap ещё не подтверждены;
  Volgograd96 положителен, но не равен106/P1/Краснодар. [Cohort report](releases/2026-10-23-tester-p1-cohort.md).
- RU SSH banner timeout / legacy Docker peer-worker unhealthy и неизвестные RU live counters:
  [операционный follow-up](releases/2026-10-23-vpn-health.md), без диагностических рестартов.
- Local storage: сохранить symlinks; оставшаяся миграция live project/Codex и reboot automount —
  отдельное maintenance после остановки writers. [Receipt](releases/2026-10-07-local-storage-migration.md).
- Fleet/control5.2–5.6, длинная AWG/TCP/Android приёмка, vault signing/consumer audit/external backup/full DR,
  gateway recovery6, Home Gateway, multi-carrier после FIELD-1, Django7.1/payments,
  licensing/private reporting/Windows publisher signing/iOS/macOS — [отложенные обязательства](PLAN.md#other-obligations).
  Они не закрыты D00 и не добавлены в desktop scope.

## История и один следующий шаг

[STATUS до D00](STATUS.history-2026-10-24.md) и [PLAN до D00](PLAN.history-2026-10-24.md)
сохранены целиком; старые NEXT/ACTIVE/checkpoints — история, не параллельные задания.
[Отчёт D00](releases/2026-10-24-desktop-parity106-d00.md) фиксирует сохранность и границы.
**STOP после CHAT-UX-1. NEXT — review CHAT-UX-1 перед установкой нового UI-кандидата владельцу.
L04.2/full L05/TCP HTTPS diagnosis/teardown/signing/publication не начинать.**
