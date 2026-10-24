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

Новый code SHA и его CI будут зафиксированы после обычного push; сейчас NOT_RUN.
Обязательные workflow/pytest команды не менялись, прежние CI counts не приписываются D04.
Полные suites локально не повторялись. Прочие capsule/HTTP/nginx/expiry/privacy/socket
failures не исправлялись и не подавлялись. Это не protected DIRECT/service-only,
полный native runtime, упаковка, installed/live delivery или OS acceptance.
Версии Linux0.2.11/Windows0.2.15, каталоги, deployment и установки не менялись;
runtime rollout/rollback не выполнялся. Новые IPC/сетевые полномочия не добавлены.
NEXT — review D04. После отчёта STOP; D05 и последующие задачи не начинать.
