# D04 — Auto stop/start lifecycle, 24.10.2026

## Scope и исходное состояние

Вход: чистая `main`, HEAD и проверенный `origin/main`
`64ecba67825b3036425b5d7a4afa64002cec235d`. D03 review accepted;
D02.1 collection/import isolation и D02.2 public-reference приняты.
D01/общая CI-приёмка открыта, D02.1-R PARTIAL/исторический replay NOT_RUN.
D05 QUEUED, [fleet-контракт](../desktop-architecture.md#desktop-fleet-boundary) неизменён.
Изменены только [Controller](../../clients/linux/auto_service.py),
[адресные тесты](../../clients/desktop/tests/test_auto_service.py), STATUS/PLAN и этот отчёт.

## Доказанная последовательность и исправление

Новые проверки запускают настоящий Controller, не копию его метода, с управляемыми
Runtime и Events. Сначала те же тесты с исходным `auto_service.py` из входного HEAD:
**8 failed / 1 passed / 46 deselected**, exit1. Доказаны:

- DISCONNECTED виден при удерживаемом финальном dispose и ещё живом owner.
- Завершённый, но не reaped поток отвергает единственный непосредственный start.
- Повторный stop после завершения/на удерживаемом хвосте owner теряет завершение.
- Stop/reap после ошибки close/dispose может затереть FAILED успешным состоянием.

Это детерминированные локальные последовательности, **не доказанная причина конкретного
прошлого AWG CI assertion**. Таймауты Events/join только обнаруживают зависание;
новые тесты не используют sleeps, polling или повторные start для достижения успеха.

Публикация DISCONNECTED перенесена из run перед finally.dispose в reap **фактически
завершённого** owner. Start/stop/status вызывают reap под тем же RLock, что проверка
состояния/допуск. Живой поток не обнуляется; join под lock только для уже мёртвого потока.
До завершения cleanup состояние DISCONNECTING, второго runtime нет. После завершения
прямой start сам убирает старый поток и создаёт новую generation без status/повтора команды.
Fatal блокирует start и не стирается повторным stop/reap. Завершённый stop идемпотентен
по ресурсам, но повторяет revocation journal write, если предыдущая запись не удалась.

Lifetime terminal callback: он синхронен в Coordinator.tick; Controller ждёт
Coordinator.close/abort, Runtime.dispose требует мёртвый coordinator. Настоящие
Coordinator/Runtime с синтетическим Process подтверждают удерживаемый callback,
затем process.close, затем освобождение guard и лишь после этого нового owner.
В production PolicyProcess.close также ограниченно join-ит reader/operator; отказ
close/join/dispose оставляет fatal, не открывает передачу владения. Дополнительное
callback fencing не требуется на этом пути. Старый generation stop отвергается;
существующие Coordinator.accept и GuardedHost проверки позднего CONNECTED/операций сохранены.

## Адресная проверка

Чистый `git archive` экспорт вне checkout, без `state-client-build`, в локальном
`family-connect-d01-2:preflight`; неизменённый
`bash scripts/ci_python313_env.sh /tmp/test-venv` — strict imports PASS,
executable `/tmp/test-venv/bin/python`, Python3.13.15, существующие D01 locks.
В экспорт скопированы только изменённые source/test; baseline run использовал старый source.
Для воспроизведения до исправления в этот экспорт помещён
`git show 64ecba67825b3036425b5d7a4afa64002cec235d:clients/linux/auto_service.py`,
затем выполнен следующий адресный выбор (после него возвращены исправленные bytes):

```sh
python -m pytest -q clients/desktop/tests/test_auto_service.py --tb=short \
  -k 'disconnected_is_not_published or start_reaps_finished or repeated_stop_after_owner or completed_stop_can_retry or owner_tail or lifecycle_failure or real_coordinator_callback'
```

```sh
python -m pytest -q clients/desktop/tests/test_auto_service.py --tb=short -rs
python -m pytest -q clients/desktop/tests/test_auto_platform.py \
  clients/desktop/tests/test_auto_policy.py clients/desktop/tests/test_auto_guard.py \
  clients/desktop/tests/test_mesh_intent.py clients/desktop/tests/test_auto_mesh.py \
  clients/desktop/tests/test_auto_normal.py tests/test_friends_auto_owner.py --tb=short -rs
```

Команды выполнялись указанным venv Python: **55 passed**, затем **180 passed / 6 skipped**;
failures/errors = 0. Шесть существующих skips требуют `FC_TEST_MESH_WORKER`;
бинарник не подменялся. Сохранены все прежние assertions, включая revoke до cleanup,
cancel при journal error, stop при factory init, manager shutdown с intent/guard,
persistence/unexpected native exit, generation ownership и late CONNECTED после stop.
Новые проверки дополнительно покрывают retry journal после завершения без второго cleanup.

## CI и границы приёмки

Code **`b41e1ad8e6b49b89881cd06747addd8f2ce76fb5`** обычным push отправлен в `main`,
`git ls-remote origin refs/heads/main` подтвердил этот SHA. Tested source/test bytes совпадают
с commit; прежние test functions/assertions сохранены (AST comparison). Следующий
docs-only checkpoint записывает эти результаты, не получает CI PASS от code SHA автоматически.

| Job на code SHA | Результат | Последующие этапы |
|---|---|---|
| [control](https://github.com/Joker20380/family_connect/actions/runs/40090712538/job/120862614779) | FAIL: 2919 passed / 54 failed / 0 errors / 106 skipped | GUI/render, упаковка, extracted-package/recovery skipped |
| [phase0/tests](https://github.com/Joker20380/family_connect/actions/runs/40090712491/job/120862614474) | FAIL: 2919 passed / 54 failed / 0 errors / 106 skipped | cargo skipped |
| [Docker tests-stage / failover](https://github.com/Joker20380/family_connect/actions/runs/40090712491/job/120862614633) | FAIL: 2917 passed / 54 failed / 0 errors / 108 skipped | tests-passed/runtime image не созданы; provision/failover/auth/offline/revocation skipped |
| [Client builds / linux](https://github.com/Joker20380/family_connect/actions/runs/40090712498/job/120862614999) | PASS, включая обязательный desktop pytest | GUI/layout, сборка и extracted DEB/AppImage smoke PASS |
| [AmneziaWG / awg](https://github.com/Joker20380/family_connect/actions/runs/40090712573/job/120862614785) | PASS | Существующие этапы job сохранены |
| [TCP / build](https://github.com/Joker20380/family_connect/actions/runs/40090712508/job/120862614778) | PASS | Изолированные routing/component checks PASS; release jobs skipped |
| [Linux voice](https://github.com/Joker20380/family_connect/actions/runs/40090712519/job/120862614561) | PASS | Не новая полная аудиоприёмка |
| [Auto bridge / Ubuntu protocol](https://github.com/Joker20380/family_connect/actions/runs/40090712514/job/120862614679) | PASS | Protocol/controller, race/cancel, signed floors |
| [Auto bridge / isolated-linux](https://github.com/Joker20380/family_connect/actions/runs/40090712514/job/120862614776) | PASS | Service/runtime/ownership pytest, native compatibility и root guard в isolated kernel |

Control/phase0 dependency imports и адресные gates PASS. Docker root 22 passed,
адресные 59 passed, full suite от non-root runner: exit1, 7 passed subtests, 2 warnings;
те же exit1/subtests/warnings в control/phase0. Artifact `12558373440`,
`phase0-failover/build.log`: в FAILED list нет Auto-тестов. Остаточные группы —
приватные mobile-bootstrap/owner-deadline/tunnel-restart capsules; HTTP/nginx contract;
expiry, private-storage/evidence validation и socket address-in-use, включая
`test_device_identity.py::test_unsafe_directory_rejected`. Уточнение review: на `b41e1ad`
набор 54 failures одинаков в control/phase0/Docker; это не отдельный Docker-only failure.
Counts сняты с этого SHA, а не перенесены из D03. Несвязанные Android/Windows jobs
не ожидались; PASS отдельных Linux jobs не равен PASS всего workflow/общего D01.

Review D04 принят перед D05. Docs-only SHA `3f9854a681beaf35dcb05bdfdc5d7a87b2beb72c`:
[phase0](https://github.com/Joker20380/family_connect/actions/runs/40091312005) завершился
**FAILURE**; проверено отдельно при входе D05, не IN_PROGRESS и не результат code SHA.

Обязательные workflow/pytest команды не менялись. Полные suites локально не повторялись.
Остаточные failures не исправлялись и не подавлялись. Автоматические native/package CI
checks не заменяют protected DIRECT/service-only, полный parity installer, installed/live
delivery или OS acceptance; локальный детерминированный transport/runtime синтетический.
Версии Linux0.2.11/Windows0.2.15, каталоги, deployment и установки не менялись;
runtime rollout/rollback не выполнялся. Новые IPC/сетевые полномочия не добавлены.
NEXT — review D04. После отчёта STOP; D05 и последующие задачи не начинать.
