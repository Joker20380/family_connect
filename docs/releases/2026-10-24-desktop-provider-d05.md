# D05 — внутренняя Linux selection/provider/application граница

24.10.2026. Вход: чистая `main`, HEAD = проверенный `origin/main`
`3f9854a681beaf35dcb05bdfdc5d7a87b2beb72c`. Review D03/D04 принят.
D01/общая CI-приёмка открыта; D02.1-R PARTIAL/исторический replay NOT_RUN.
**DONE в согласованном локальном Linux scope; NEXT — review D05.**

## Что используется в действующем пути

- [auto_configuration.py](../../clients/linux/auto_configuration.py): отдельные Target,
  Preference/TargetChoices, Assignment и AppliedSession без секретных profile bytes.
  Локальные legacy-ru/legacy-nl — не gateway identity; gateway_id остаётся None.
  NormalOwner выдаёт assignment лишь для собственного результата свежего resolve после
  floor commit, byte readback, native inspect и сравнения. Stamp нельзя переназначить
  другой generation или получить из offline verified/VALIDATED_MATERIAL.
- [auto_platform.py](../../clients/linux/auto_platform.py): connection preference фиксируется
  при создании Runtime. Configure использует legacy target mapping, prepare требует
  assignment соответствующего owner. Selected/preferred по-прежнему транспорт.
- [auto_policy.py](../../clients/linux/auto_policy.py): внутренний metadata hook после
  open/context check/guard.ready. Applied означает применение владельцем, не новый
  policy CONNECTED и не live delivery. Ошибка после ready/publication также снимает metadata.
  Отдельного owner, retry loop или lifecycle не добавлено.
- [auto_service.py](../../clients/linux/auto_service.py): передаёт прежний preferred в
  модель Platform; D04 Controller/lifecycle не менялся. Нового IPC нет.

Refresh/select-next — только память модели. Они не закрывают кандидатов, не вызывают
configure/fetch/apply/reconnect, не меняют текущую generation и storage. Отдельный
selection_snapshot не добавлен в IPC. GUI wiring — L07/W09; постоянные настройки/
миграция — L08/W12. Existing storage, identity/WG keys/activation/Support ID/history,
floors/anti-rollback и accepted106 pins неизменны; floors не разделены по target IDs.

Legacy trust path остаётся прежним: fresh authenticated fetch → полный персональный
profile/binding check → signed floor write → bytes readback → native inspect → equality
→ готовность к platform apply. Ровно RU/NL, два уникальных gateways, exact keys, bounds,
подсети, подписи и ошибки не ослаблены. Новый wire provider потребует отдельной версии.
MESH applied не наследует normal assignment; native profile context и chat borrowing
не менялись. Нет нового произвольного DIRECT/service-only доступа.

## Адресные критерии и evidence

| Критерий | Проверка / уровень доказательства |
|---|---|
| Stable ID 2×NL + DE | TargetChoices и настоящий Platform: reorder/load refresh сохраняют nl-b; два NL не сливаются; удаление ID не выбирает другой молча. Model fixture, не доверенный assignment. |
| Next отдельно от applied | На настоящем Platform/NormalOwner/GuardedHost, с синтетическими transport/guard: events/calls/floor bytes неизменны после refresh/select-next, active generation/assignment прежние. |
| Apply не prepare | Внутри guard.ready applied ещё отсутствует; появляется только после успешного ready. Ошибки ready/close, cancellation и deadline после publication снимают metadata. |
| Fencing | Удерживаемый fetch после cancel, смена guard generation во время inspect, callback released owner и команда старого policy generation не применяются и не меняют новую сессию. Events без sleeps. |
| Strict legacy | Прежние positive RU/NL и negative vectors PASS. Подпись синтетического 2×NL+DE catalog корректна; Python signature verification доходит до _catalog/list rejection. Настоящий normal-stdio сначала принимает positive two-node response, затем отвергает three-node с sequence3 выше floor2. |
| Capabilities | Прежние missing engine/AWG31 component checks сохранены. Model-only список не меняет разрешённые transports; dynamic_fleet=False. Windows broker/Auto/MESH integration не заявлена. |
| Privacy | Новый snapshot/repr не содержит TCP credential, WG private key, identity или tcp/awg profile bytes. MESH native context не заменяется совпадением страны/target. |

Чистый `git archive` экспорт вне checkout, без state-client-build; поверх него только
изменённые source/tests. D01 `family-connect-d01-2:preflight`, неизменённый
`bash scripts/ci_python313_env.sh /tmp/test-venv`: Python3.13.15 и strict imports PASS.
Existing locks не обновлялись. Эфемерные git и Go1.26.1 нужны только для локальной
сборки неизменённого native worker существующим `scripts/build_desktop_mesh.py`:
public Xray `d2758a023cd7f4174a5a5fa4ff66e487d4342ba0`, прежняя pinned packet patch.
Worker SHA256 `367731b066b24be4fa68369c3cb6ea64af059d3e42235f75a5fbbd458f24c19b`;
это локальный test artifact, не новый accepted pin, installer или публикация.

Обе команды запускались `/tmp/test-venv/bin/python` с
`FC_TEST_MESH_WORKER=/checks/native-out/worker/fc-mesh`:

```sh
python -m pytest -q clients/desktop/tests/test_auto_targets.py \
  clients/desktop/tests/test_auto_configuration.py clients/desktop/tests/test_auto_configuration_native.py \
  clients/desktop/tests/test_auto_platform.py clients/desktop/tests/test_auto_policy.py \
  tests/test_friends_catalog.py --tb=short -rs
python -m pytest -q clients/desktop/tests/test_auto_service.py clients/desktop/tests/test_auto_guard.py \
  clients/desktop/tests/test_auto_normal.py clients/desktop/tests/test_auto_mesh.py \
  clients/desktop/tests/test_mesh_intent.py tests/test_friends_auto_owner.py \
  clients/desktop/tests/test_mesh_chat_host.py clients/desktop/tests/test_chat_host_registration.py --tb=short -rs
```

Результаты: **162 passed**, затем **213 passed**, failures/errors/skips = 0.
Старые test functions/assertions сохранены; изменён только fake owner test fixture для
нового metadata hook. Public `python scripts/verify_desktop_reference.py` PASS;
настоящая private capsule в D05 не проверялась. Полный исторический pytest локально не запускался.

## CI и передача

Code **`c53265d257b94c7e59e42fe45908f3e2b030eaf1`** pushed/remote-verified обычным
push в `main`. Tested source/test bytes совпадают с commit. Следующий docs-only checkpoint
записывает эти результаты, не наследует CI PASS от code SHA.

| Job на code SHA | Фактический результат |
|---|---|
| [Control](https://github.com/Joker20380/family_connect/actions/runs/40094649612/job/120874250998) | FAIL: 2930 passed / 54 failed / 0 errors / 107 skipped; GUI/render/package/extracted gates skipped |
| [Phase0/tests](https://github.com/Joker20380/family_connect/actions/runs/40094649648/job/120874251235) | FAIL: 2930 passed / 54 failed / 0 errors / 107 skipped; cargo skipped |
| [Docker tests-stage/failover](https://github.com/Joker20380/family_connect/actions/runs/40094649648/job/120874251378) | FAIL: 2929 passed / 53 failed / 0 errors / 109 skipped; tests-passed/runtime image не созданы, provision/failover/auth/offline/revocation skipped |
| [Client/Linux](https://github.com/Joker20380/family_connect/actions/runs/40094649694/job/120874251704) | Job IN_PROGRESS по API; desktop pytest, GUI/layout, package/extracted smoke и upload steps success. Job/workflow PASS не предполагается |
| [AWG](https://github.com/Joker20380/family_connect/actions/runs/40094649601/job/120874251292) / [TCP build](https://github.com/Joker20380/family_connect/actions/runs/40094649607/job/120874251021) | PASS; существующие gates сохранены, TCP release jobs skipped |
| [Auto bridge / Ubuntu protocol](https://github.com/Joker20380/family_connect/actions/runs/40094649633/job/120874251449) / [isolated-linux](https://github.com/Joker20380/family_connect/actions/runs/40094649633/job/120874251196) | PASS, включая actual native configuration regression и isolated kernel guard |
| [Linux voice](https://github.com/Joker20380/family_connect/actions/runs/40094649611/job/120874251163) | FAIL: `chat_voice_check.py:124`, после Return ожидание `voice.state == 'locked'`; `voice operation did not reach expected state`. Actual codec/mailbox gates PASS |

Control/phase0/Docker full pytest exit1, по 7 passed subtests / 2 warnings. Docker root
22 PASS, адресные dependency tests 59 PASS; full suite от non-root runner.
Artifact `12560417892` / `phase0-failover/build.log`: Auto-тестов в FAILED list нет;
53 failed case IDs совпадают с D04 Docker за исключением
`test_readiness_adapter_packaging.py::test_exact_candidate_mode_with_local_fixture_only`,
который на этом запуске не упал. Его код не менялся, устранение socket failure D05 не заявляется.
Дополнительный native
three-gateway case использует прежний fixture gate и входит в skip без FC_TEST_MESH_WORKER
в full suites; с реальным worker локально и в Auto bridge native gate он проходит.
Остаточные capsule/HTTP/nginx/expiry/privacy/socket groups не чинятся этим checkpoint.
Voice GTK failure записан отдельно, не скрыт retry или изменением gate; его причина не
исследуется в D05. Android/Windows jobs не ожидались. Installed/live acceptance не следует
из автоматических synthetic/native/packaged smoke. Общий D01 остаётся открыт.

Workflows, обязательные suites/команды и release-fixture policy не менялись.
Остальные 54 CI failures не включены в scope и не подавлялись.
Уточнение D04: на `b41e1ad` набор 54 failures одинаков в Control/Phase0/Docker;
docs-only [phase0 `3f9854a`](https://github.com/Joker20380/family_connect/actions/runs/40091312005)
завершился FAILURE. Эти результаты не переносятся на D05.

W01/W02 — Windows broker/native и общий Auto; L07/W09 — GUI выбора/active;
L08/W12 — persistent migration; L03/W10 — согласованные installers/capabilities;
L04/W11/R01 — обязательная установленная приёмка. Их gates не закрыты D05.
Installed/live/F-01, production fleet, leases/renewal/signing/VPS, Telemost multi-gateway,
Django/iOS NOT_RUN. Dynamic fleet не поддерживается по результатам этой модели.
Версии Linux0.2.11/Windows0.2.15, каталоги и установки не менялись; rollout/rollback не выполнялся.
NEXT — review D05; STOP без автоматического начала Linux/Windows задач.
