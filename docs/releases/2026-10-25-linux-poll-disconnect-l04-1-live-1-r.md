# L04.1-LIVE-1-R — normal poll / Disconnect correction

25.10.2026. **Source/package CHECKPOINT / review pending**, не live acceptance и не public release.
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
systemd fixtures, не считаются native PASS. Отдельные обязательные CI gates ниже.
Новый real-GTK regression step добавлен в Client Linux, существующие gates не удалены.
GTK `recovery_check.py` PASS: threshold/reconnect/explicit disconnect/stale selection/close.
Control/phase0/Docker full suites и прежние54 residual failures остаются видимыми;
Windows/voice observations не исправляются в этом scope.

### Regression coverage

Все новые concurrency tests используют Events/queues с bounded timeout, без sleeps,
random retries или повторного Disconnect. Fixtures находятся в
`clients/desktop/tests/test_operations.py` и `test_poll_disconnect_gui.py`.

| Требование | Actual regression |
|---|---|
| Slow normal poll + один Disconnect | profiles/active barriers × AWG/TCP; down1, owner OFF |
| Slow health poll + один Disconnect | curl barrier × AWG/TCP; down1 |
| Late poll после mutation | StaleConnection, включая read exception; GUI не возвращает CONNECTED |
| Poll без mutation | согласованный snapshot/health, generation не увеличивается |
| Pending durable owner | decorated disconnect ConnectionBusy, down0; revalidation также refused |
| Foreign process mutation | отдельный процесс держит actual lock; disconnect refused, down0 |
| Два клика | actual toggle дважды, helper down1, STOPPING/busy suppresses poll |
| Close queued work | оба close paths отменяют normal Disconnect future, down0 |
| Reopened active GUI | actual initialize → refresh → toggle → complete; normal/health × AWG/TCP |
| Generation contract | ровно +1 для mutation; прежние ownership/control bounded-wait assertions сохранены |

## Точный новый кандидат

Product source/проверенный remote после source push:
`57f8eff8b291062d69248ac46413f8c9fc0f561d`, source_dirty=false.
Internal **0.2.12~l03.2.2**; source/public VERSION0.2.11 неизменен.
Стандартный `scripts.package_linux` с exact retained system build-9, без rebuild
системного компонента. Локальная директория (не Git/не public release):
`state-client-build/linux-poll-disconnect-l041r-20261025/build-1/`.

- Candidate ID: `d9c0d07f93542a633b5563757f0c5aa0d4f0c37410b3b884ba8b67db01c484ef`.
- Runtime contract2, Python3.12, 707 user inventory members; одинаковый `candidate.json`
  в AppImage/DEB, SHA256 `a6de4eb94788eeb8b1bb550057ab65d8d7922d450eb9f2d9c34e1351938b1470`.
- System build-9: `8708ba6d5e218f86b42d862dd5a66237e974a03d5434e8f1c30524b16720e2da`.
- Embedded archive:49247776 bytes, SHA256
  `bdd7e04b8ca78a232acccd881004cfb3b6c96b13dc3c608d0b919f53f40f02d9`;
  accepted system source `f826dbdfb562541bde95d2fcbecc1d944d15da3d`.
  Bytes, contract и native/RNS/AWG/Xray provenance неизменны.
- Appimagetool SHA256 `95cbe7cce9717fce90c484e34052ee7c7f1d7635b33c12525b4776826a7d29b6`.

| Exact artifact | Bytes | SHA256 |
|---|---:|---|
| FamilyConnect-0.2.12~l03.2.2-x86_64.AppImage | 57924088 | `33537e451ab39010b70c989604477fc73c86f6b88f7f5d7d4c5a50dd07887a8a` |
| FamilyConnect_0.2.12~l03.2.2_amd64.deb | 55951452 | `c806ed9fac2466772042cde6c84a59b7bd86172cd3d91dee724449de78f77dda` |
| FamilyConnect-Linux-0.2.12~l03.2.2.tar.gz | 112344 | `79a2c8d7961d49e3b3c0240c259352c7bd426cdf98f260037cc6eaa98d13f4f2` |

`scripts.verify_linux_candidate` PASS для извлечённых bytes: delivery hashes,
exact inventories, common candidate identity, integration/maintainer scripts,
audit и legacy six-file shape/source parity. Полный user inventory находится в
обоих артефактах; legacy updater contract не изменён. Ничего не опубликовано.

## Actual package gate

Два новых offline disposable containers: Ubuntu24.04.5, настоящий PID1 systemd255
(255.4-1ubuntu8.18), kernel7.0.0-38-generic; private PID/mount/cgroup/network,
network none/только lo, private D-Bus/resolved/Secret Service/polkit/Xvfb.
Image `fc-l032-system:check` SHA256
`6705fc0e0b9a4c83fa3710e45f2b54a27c80cd49b27dbfe7db213d946f5b9dce`.
В mounts только точные новые артефакты и существующий fixture
`tests/fixtures/linux_candidate/smoke.py`; checkout/venv/real identity не монтируются.

Оба формата **PASS**:
- Clean UID1000 imports/GUI smoke, до setup root runtime отсутствует, нет silent VPN.
- Реальный pkexec fixed bootstrap, UID/path denial, explicit setup и bounded reinstall;
  installed inventory/capabilities READY exact build-9, temporary payload cleanup.
- Missing manifest/tampered embedded archive/mixed system build/schema1/modified
  installed module fail closed; после восстановления readback READY.
- Fixed idle DIRECT/service-only chat prepare без VPN, настоящий user D-Bus daemon,
  background owner переживает GUI exit; никакого gateway connect.
- DEB reinstall/remove/reinstall сохраняет synthetic identity/encrypted store/background setting,
  root inventory и backups; user service останавливается, dangling package unit удалён.
- AppImage service reopen использует original image, не временный mount;
  explicit remove-integration сохраняет synthetic state и independent root runtime.

Дополнительно оба launcher в одном DEB guest, UID1000/HOME и installed runtime:
candidate-check равен, READY равен, второй setup не выполнялся; installed.json SHA256
до/после `aabcce5e4baf25db37f05cd43d0ef4ab8a1ae83a622f30f05438c3f0c1c77b31`.
Это shared runtime package check, не cross-format upgrade/live owner acceptance.
Оба guest после PASS остановлены/удалены вместе с synthetic state.
Host services/routes/DNS не менялись. Existing rollback fencing/backup contract
не изменён; failure-injected rollback этого unchanged build не повторялся локально,
его real L03.1 smoke сохраняется в mandatory CI standard-rebuild gate.

## CI exact product source57f8eff

| Gate | Run/job evidence | Result |
|---|---|---|
| Client Linux | [40201296971 /121192844593](https://github.com/Joker20380/family_connect/actions/runs/40201296971/job/121192844593) | PASS: full desktop, новый real GTK race step, layout/Friends/recovery, packaged launch |
| AWG | [40201297005 /121192844341](https://github.com/Joker20380/family_connect/actions/runs/40201297005/job/121192844341) | PASS: full desktop + isolated AWG2/3.1 |
| TCP | [40201297002 /121192844984](https://github.com/Joker20380/family_connect/actions/runs/40201297002/job/121192844984) | PASS: full desktop + isolated routes + setup/package; старый component rollback использует stub и не считается real systemd gate |
| Isolated native/root→UID/Auto/DIRECT | [40201297010 /121192844514](https://github.com/Joker20380/family_connect/actions/runs/40201297010/job/121192844514) | PASS: actual kernel/native/root guard, UID umask/runtime, chat/direct, existing synthetic lifetime/combined gates |
| Protocol Linux / Windows | [40201297010](https://github.com/Joker20380/family_connect/actions/runs/40201297010) jobs121192844663 /121192844723 | PASS; не installed Windows acceptance |
| Standard system rebuild + candidate integrity/package | [40201296910 /121192843831](https://github.com/Joker20380/family_connect/actions/runs/40201296910/job/121192843831) | PASS: standard accepted-source system rebuild, real L03.1 smoke/rollback, exact CI pair verification, both systemd255 package gates |
| Control full suite | [40201297046 /121192844656](https://github.com/Joker20380/family_connect/actions/runs/40201297046/job/121192844656) | FAILURE:54 failed/3124 passed/154 skipped,7 subtests |
| phase0 full suite | [40201296976 /121192844332](https://github.com/Joker20380/family_connect/actions/runs/40201296976/job/121192844332) | FAILURE:54 failed/3124 passed/154 skipped,7 subtests |
| Docker full suite | [40201296976 /121192844475](https://github.com/Joker20380/family_connect/actions/runs/40201296976/job/121192844475) | FAILURE:53 failed/3123 passed/156 skipped,7 subtests; failover stages после build NOT_RUN |
| Existing voice check | [40201297057 /121192844607](https://github.com/Joker20380/family_connect/actions/runs/40201297057/job/121192844607) | FAILURE: `voice operation did not reach expected state`, вне correction scope |

Full suites выполнялись без отключений/xfail; D01 residual debt не исправлялся.
Количество Docker53 не объявляется устранением прежних54: это другой environment,
другие skips и существующие нестабильные tests. **Общий CI не зелёный.**
CI standard rebuild и его pair — отдельные bytes/identity, artifact12601984617;
это не local `d9c0d07f…`/build-9 и не замена exact пары в таблице выше.
Дополнительные existing synthetic native gates не являются запуском L04.2/L05.

## Checkpoint / ограничения

Source57f8eff и package-documentation `da5d65a0a200ef00c1314313993336a2c37023c6`
отправлены ordinary push; remote SHA каждого checkpoint проверен. Documentation
continuation не меняет product source/artifact bytes. Финальный docs commit содержит
CI receipts и статусы, не новый build. Staged allowlist/secret-pattern scan/local links/
whitespace PASS; ops-hunks STATUS/PLAN и отдельный ops report оставлены вне commits.
Build output и logs остаются только ignored local evidence, не в Git.

Private FC_L04_TEST_STATE/receipt/credentials не открывались и не переносились;
server operations/configuration fetch/connect NOT_RUN. Live retest нового кандидата
NOT_RUN; device assignment сохранить. Никаких public release/catalog/landing/signing changes.

L04.1-LIVE-1 остаётся historical PARTIAL; L04.1 IN_PROGRESS. Новый кандидат ещё
не установлен с test identity и не проходил live AWG/TCP retest. Никакие прежние
live PASS final-2 на него не переносятся. LIVE-2/L04.2/L05/teardown QUEUED/NOT_RUN.

**STOP. NEXT — review L04.1-LIVE-1-R.**
