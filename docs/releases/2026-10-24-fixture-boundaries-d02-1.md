# D02.1 — collection/import boundaries, 24.10.2026

Статус: IN_PROGRESS, CI на code SHA ожидается. Вход: чистая `main`, HEAD и remote
`01f67d4a7daac22c0d35753c8b9a13e15d4feb1d`; релевантной дельты не было.
Dependency-часть D01.2 принята review, общая CI-приёмка D01/D01.1/D01.2 не закрывается.

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
CI evidence PENDING; remaining RNS/Auto/ChatHTTP failures не исправляются этим шагом.

Source-only; Linux0.2.11 / Windows0.2.15 / Android beta106-recovery без изменений.
Нет deployment/installation/release; отмена только обычным revert, не runtime rollback.
NEXT D02.2 после review D02.1; D03/D04/iOS не начаты.
