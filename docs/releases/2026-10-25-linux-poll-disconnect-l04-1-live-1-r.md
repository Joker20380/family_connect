# L04.1-LIVE-1-R — normal poll / Disconnect correction

25.10.2026. **ACTIVE / source checkpoint**, не live acceptance и не public release.
Вход main/remote `96f90bdff72603efec27ebda8cf6a948c4202ad3`.
LIVE-1 PARTIAL принят review. Exact final-2 `9d4b13cc…` неизменен, но больше не
кандидат для завершения L04.1. Его [положительное evidence и first failure](2026-10-25-linux-installed-awg-tcp-l04-1-live-1.md)
сохраняются только за прежними bytes. L04.1 IN_PROGRESS; LIVE-2/L04.2/L05/teardown NOT_RUN.

## Детерминированное воспроизведение

Actual `Linux`/`LinuxTCP.poll_state`, `profiles`, `active`, health probe и decorated
`disconnect`; mock только IO/helper boundary и synthetic owned profile. Event barrier
в slow profiles/active/curl после чтения generation. Один вызов Disconnect, без
sleeps/retries/repeated clicks. Прежний код: poll держит operation lease,
ConnectionBusy, helper down0, active owner сохранён.

Отдельно настоящий GTK App(smoke=True), actual initialize с уже active profile,
refresh/submit/complete/toggle_vpn и отдельные executors. Только dispatch callback
очереди контролируется тестом; нет fake backend disconnect. Прежний GUI показывает
`Operation failed … Connection settings are being updated`, owner не отключён.
Initial red: **12 failed,30 passed** (6 backend,4 GUI race,2 queued-close).
Это доказывает саму гонку, **не точную причину всех75s live-наблюдения**.

## Изменённый contract

- Generation читается под кратким `connection_operation`; медленные read-only
  profiles/active/health выполняются без mutation lock. В `finally` повторная
  `connection_operation(expected=generation)` проверяет также read-error path.
- Mutation/decorators/authorization/control_transaction bounded wait неизменны.
  Pending durable owner, unsafe state и foreign process lock остаются fail-closed;
  mutation не переигрывается, generation меняется по прежнему contract.
- `StaleConnection` от poll/health не становится health failure/recovery или UI
  CONNECTED. Local revision/busy fencing сохраняется; STOPPING немедленен, новые
  polls при busy не запускаются, double-click не запускает второй helper down.
- Только queued normal Disconnect можно отменить Future.cancel при закрытии.
  Уже running mutation не отменяется/не переигрывается; прежний busy-close guard
  остаётся. Auto/MESH/Connect/recovery функционально не переработаны.

## Проверки source checkpoint

Python3.12.3/pytest9.1.1, disposable `fc-l031-tests:check`, network none, real
GTK4/Adw под private D-Bus/Xvfb. Focused first green50 PASS; расширенная selection
operations/AWG/TCP/GUI/recovery/presentation/Friends/candidate: **229 PASS,2 SKIP**.
Включает read exceptions during mutation, pending revalidation, foreign process,
normal+health poll, consistent snapshot, stale callback, true owner error, queued
window close и generation assertions. Полный desktop: **1121 PASS,85 SKIP**,
9 warnings; skips включают отсутствующие в этом image native workers и отдельные
systemd fixtures, не считаются native PASS. Обязательные CI gates ещё в работе.
Новый real-GTK regression step добавлен в Client Linux, существующие gates не удалены.
Control/phase0/Docker full suites и прежние54 residual failures остаются видимыми;
Windows/voice observations не исправляются в этом scope.

## Новый кандидат / дальнейший bounded gate

Reserved internal version **0.2.12~l03.2.2** по существующей internal policy;
source/public VERSION0.2.11 неизменен. Стандартный L03.2 package path, новый source
SHA/candidate ID/AppImage/DEB/legacy hashes будут записаны после сборки.
Предполагается exact accepted system build-9 без изменения bytes/contract; перед
embedding проверяются SHA/manifest. CI standard rebuild остаётся отдельным ID,
не подменяет точную локальную пару. Package gate: disposable Ubuntu24.04/systemd255,
synthetic state only, реальные systemd/pkexec/readback, без gateway/test identity.

Private FC_L04_TEST_STATE/receipt/credentials не открывались и не переносились;
server operations/configuration fetch/connect NOT_RUN. Live retest нового кандидата
NOT_RUN; device assignment сохранить. Никаких public release/catalog/landing/signing changes.

**STOP после source/package gate. NEXT — review L04.1-LIVE-1-R.**
