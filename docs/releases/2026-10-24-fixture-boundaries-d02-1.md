# D02.1 — collection/import boundaries, 24.10.2026

Review подтвердил collection/import isolation. Комплектность historical runner не была
обеспечена этим checkpoint: пропущенные входы и их отдельная коррекция —
[D02.1-R](2026-10-24-historical-runner-d02-1-r.md). Прежние CI результаты ниже относятся только к `6a0a982`.

Статус: **DONE по collection/import isolation; полный CI FAIL**. Вход: чистая `main`, HEAD и remote
`01f67d4a7daac22c0d35753c8b9a13e15d4feb1d`; релевантной дельты не было.
Dependency-часть D01.2 принята review, общая CI-приёмка D01/D01.1/D01.2 не закрывается.
Code SHA: `6a0a982661a188128b34568c6e4146a494459548`, обычный push и подтверждённый
`origin/main` перед чтением CI. Следующий docs-only commit только фиксирует evidence;
его SHA не подменяет проверенный code SHA.

## Ограниченное изменение состава

- Только шесть `mesh_perf3b/test_{owner_handoff,cleaned_allocation,live_operator,successor_lifecycle,successor_migration,successor_operator}.py`
  отделены от ordinary collection: это исторический API с overlay, не current control.
  Файлы/assertions побайтно сохранены. [Явный набор, происхождение каждого входа и команды](../../tests/fixtures/mesh_perf3b/README.md#d021-explicit-local-historical-suite).
  `historical-suite.json` фиксирует source commit76df691 и hashes; `run_history.py`
  требует sealed API78a69db8 и исторические исходники. Нет поиска local state или
  восстановления кандидата из main; верификация до child process, отдельный temp tree,
  проверка origin импортов, ненулевой BLOCKED/NOT_RUN при отсутствии/несовпадении.
- `queue_retry/local_test.py` остаётся импортируемым CLI с прежним `main()` и argv,
  не содержит Python test-функций. Harness не запускался. Audit101/speed_candidate/
  queue_retry загружают свой prepare по точному sibling path с отдельным именем,
  не через общий `prepare`, без перестановки тестов/очистки sys.modules/sys.path.
- После отделения overlay обнаружено скрытое shadowing product `control` файлами
  `p1_owner/control.py` и `mux_profile/control.py`: раньше его маскировал ранний import
  из overlay-тестов. Два fixture-каталога стали пакетами, два test-imports относительными;
  tests/assertions сохранены. Никаких общих directory ignores или новых skips.

## Проверки до push

Чистые `git archive` baseline и export+patch без state, non-root container,
Python3.13.15, неизменённый `scripts/ci_python313_env.sh`; зависимости как D01.2.

- `python -m pytest --collect-only -q`: **2977 collected + 9 errors → 2996 / 0 errors**.
  Сравнены полные node lists: ни одной потери ранее собираемого case, +5 восстановленных
  speed_candidate cases и +14 новых import/runner regressions. Для сравнения четырёх
  динамических IDs нормализованы clock fields и `next(iter(PATHS))`; multiplicities и
  исходники этих тестов неизменны. Полные списки/delta только `/tmp/fc-d02.1/evidence/`,
  не в STATUS/PLAN. Шесть overlay modules ранее не собирали ни одного case из-за errors.
- Адресная команда: `python -m pytest -q tests/test_fixture_import_boundaries.py`
  плюс canary_environment/canary_prestart/timing_preflight, queue_retry/test_journal,
  speed_candidate/phase_results_test и scope_test, lifecycle101/test_audit,
  p1_owner/test_classify и mux_profile/test_session_scope:
  **75 passed, 5 subtests passed / 0 failed / 0 errors / 0 skipped**.
- Два порядка импортов проверены в свежих процессах, в том числе с реальным чужим
  `prepare` в module cache; product-control shadowing проверено обоими порядками collection.
  Body accounting/journal parsing/validation и audit assertions сохранены.
- Runner: отсутствие аргументов и неверный archive → BLOCKED/NOT_RUN, exit2;
  missing/changed source/archive/member проверены; direct pytest overlay запрещён.
  Snapshot/isolated-child/exit propagation — synthetic unit test, не исторический PASS.
  Реальная историческая suite NOT_RUN: точные приватные входы не предоставлялись runner.
  Закрытые live/seal/stage/deploy/readback операции не запускались.

## Сохранённые gates и поставка

`pytest.ini`, D01 workflows/helpers/locks, `scripts/ci_release_fixtures.py`, public-source
export/historical pins/provenance, root/non-root Docker, marker/runtime COPY, полный
pytest и последующие GUI/package/cargo/failover gates не изменены. Новые helper/runner
пути находятся под существующим `tests/**` filter. Продукт и accepted pins неизменны.
Функции CLI/helpers дополнительно сопоставлены по AST с baseline: тела неизменны.

## CI на pushed code SHA 6a0a982

Полные команды через `scripts/ci_release_fixtures.py run ... -- python -m pytest -q`
сохранены (в workflows оба Python явно указывают на D01.2 venv). Все три окружения
завершили collection и обработали 2996 cases (включая skips), не остановившись на import error.

| Окружение | Passed | Failed | Errors | Skipped | Full pytest / job |
|---|---:|---:|---:|---:|---|
| [control/linux-control](https://github.com/Joker20380/family_connect/actions/runs/40079929587/job/120831170422) | 2834 | 56 | 0 | 106 | exit1, FAIL; 164.38s |
| [phase0/tests](https://github.com/Joker20380/family_connect/actions/runs/40079929634/job/120831170549) | 2834 | 56 | 0 | 106 | exit1, FAIL; 138.37s |
| [Docker tests-stage / phase0/failover](https://github.com/Joker20380/family_connect/actions/runs/40079929634/job/120831170445) | 2832 | 56 | 0 | 108 | pytest exit1, build FAIL; 147.44s |

В каждом full run дополнительно 7 subtests passed и 2 existing deprecation warnings.
D01.2 strict imports/четыре desktop-файла PASS; Docker root gate 22 passed и desktop
адресные 59 passed. CI native/systemd/audio skips сохранены, новых skips нет.

Остаточные failures (полная разбивка прочитана в Docker
[build.log artifact](https://github.com/Joker20380/family_connect/actions/runs/40079929634/artifacts/12555335023)):

- **2 D02.2:** `test_rns_worker_matches_exact_accepted_provider_and_transport_source`
  и `test_readiness_semantic_port_uses_exact_accepted_sources`: нет accepted capsule
  `rns-relay.json` / `fc_rns_transport.py`; pins не изменены.
- **19 других fixture/capsule:** mobile_bootstrap/test_transport_bridge (6),
  owner_disconnect/test_deadline_bridge (12, включая inherited cases),
  tunnel_restart/test_health (1); отсутствуют historical fc_rns_transport.py/VpnHealth.java.
- **29 nginx contract:** test_friends_http_runtime (13), test_http_candidate_preflight (9),
  test_http_transition (7): literal location-route assertion `count(...) == 1` получает 0.
- **2 expiry:** test_native_authority_compat, обе проверки exact expiry расходятся на 4s.
- **3 privacy:** test_device_identity, test_friends_http_evidence, test_product_registration —
  ожидаемые ValueError/RuntimeError не подняты; **1 socket:**
  test_readiness_adapter_packaging::test_exact_candidate_mode_with_local_fixture_only,
  `OSError [Errno 98] Address already in use`.

Это отдельные остаточные gates, не разрешение чинить продукт/окружения/другие fixtures
или расширять D02.2. В Docker failure list нет затронутых независимых helpers и новых
14 regressions. Auto assertion в этом run не наблюдался; D04 не закрывается.
Control job/workflow FAIL: GUI/package/extracted checks и uploads SKIPPED.
Phase0/tests FAIL: cargo SKIPPED. Docker marker не создан, runtime COPY заблокирован;
provision/failover/auth/offline/revocation SKIPPED, build.log upload и compose down PASS.
Phase0 workflow FAIL. Прочитаны только статусы нужного SHA, failure tails и build artifact;
несвязанные jobs не ожидались, повторные full workflow logs не скачивались.

Source-only; Linux0.2.11 / Windows0.2.15 / Android beta106-recovery без изменений.
Нет deployment/installation/release; отмена только обычным revert, не runtime rollback.
NEXT D02.2 после review D02.1; D03/D04/iOS не начаты.
