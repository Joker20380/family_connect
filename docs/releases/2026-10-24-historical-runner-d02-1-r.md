# D02.1-R — historical runner completeness, 24.10.2026

**PARTIAL.** Collection/import isolation D02.1 подтверждено review, не переделывалось.
Вход: чистая `main`, HEAD = origin/main `2ee2b06d536d1302f84f9e6ce54fd16f7350ceeb`.
Исторический шестифайловый набор **NOT_RUN**; полная воспроизводимость ещё не обеспечена.

## Исправленные входы и граница

- Публичный `tests/vectors/bootstrap-timestamps.json` извлечён из уже закреплённого
  `76df691961aa88a46b73e7a355687fa6f9a3c457`; SHA256
  `a542d50e3b3645b9cd1813619ffb075fd3777d2a2473bd079d05ef83a8b2aca2`.
  Включён в manifest, проверку bytes, настоящий snapshot и команду git archive.
- Original `deployed-api.pyz` проверяется по прежнему `12ca0c72…`, включая ZIP members,
  и попадает по пути, используемому lifecycle и migration tests. Owner API `78a69db8…`
  и 13 публичных файлов проверены по прежним pins/источнику; новых artifact pins нет.
- Delivery-check, JDK tree, compiled classes и Gson/JUnit/Hamcrest — отдельные CLI inputs
  с exact destinations/required_by. Отсутствие, mismatch, неизвестный pin, неполная
  структура, отсутствие execute bit или непригодный executable дают BLOCKED/NOT_RUN,
  exit2 до pytest. Нет запуска неполного выбранного набора.
- Snapshot использует проверенные bytes/modes, package directories, bin/lib и ровно
  один JAR на versioned glob. Перед pytest — isolated Python API/helper imports,
  native invalid-input и Java `--dry-run` probes; ненулевой pytest exit сохраняется.
  [Команды и dependency closure каждого файла](../../tests/fixtures/mesh_perf3b/README.md#d021-explicit-local-historical-suite).

## Незакрытое условие происхождения

Локальные retained paths существуют. Проверка всех явно переданных входов с настоящим
manifest завершилась **BLOCKED/NOT_RUN, exit2**, без child pytest: нет anchored hashes/
inventories для delivery-check, Java runtime, java-floors-final-classes и трёх JARs.
Значения manifest намеренно `null`, это не wildcard/разрешение принять любые bytes.
Существующие native-validator.json и java-floors-final.json совпали с hashes публичного
evidence, но первый фиксирует команду/exit/log, второй sources/log, не binary/class outputs.
Незакреплённый локальный JDK metadata и номера версий JARs недостаточны. Нужен независимо
подтверждённый исторический inventory; ничего не пересобиралось и не «принималось» из main.

## Адресные проверки

Чистые `git archive` before/after+patch, без локального state; non-root Python3.13.15,
неизменённое окружение D01.2 (`scripts/ci_python313_env.sh`).

- `python -m pytest --collect-only -q`: **2996 → 3031 collected, 0 errors**.
  Per-file counts прежнего набора сохранены; +35 только runner regressions.
  Шесть исторических файлов побайтно совпали с pins, collection policy не менялась.
- `python -m pytest -q tests/test_fixture_import_boundaries.py` плюс прежний адресный
  набор canary_environment/prestart/timing_preflight, queue_retry/test_journal,
  speed_candidate/phase_results_test и scope_test, p1_owner/lifecycle101/test_audit,
  p1_owner/test_classify, mux_profile/test_session_scope:
  **110 passed, 5 subtests passed; 0 failed/errors/skipped** (runner/import tests: 49).
  Первый ввод команды с неверным путём lifecycle101 дал exit4/no tests, исправленный
  путь проверен; это не тестовый PASS. Raw logs только `/tmp/fc-d02.1-r/evidence/`.
- Реальные pinned public source/vector читаются в настоящем snapshot отдельным Python
  через неизменённое AST-присваивание TIME_CONTRACT из baseline helper. Проверены bytes
  после изменения исходных inputs, executable modes, Java layout/JAR glob. Runtime,
  classes, JARs и native executable в этих регрессиях **синтетические**, не historical PASS.
  Каждый класс входа проверен на missing/changed/unpinned до subprocess; сохранены
  обе import-order регрессии, body accounting/journal parsing/validation и exit propagation.

## CI и поставка

До push автоматический CI этой коррекции NOT_RUN; результаты pushed SHA фиксируются
отдельно. Полные suites вручную не запускались. Прежние 56 failures относятся только
к `6a0a982`: 2 RNS/reference (D02.2), ещё 54 — 19 capsule fixtures, 29 nginx assertions,
2 expiry, 3 privacy, 1 socket. D03 ChatHTTP и D04 Auto остаются отдельными задачами;
причина прежнего Auto failure не доказана. Общий D01 и CI-приёмка не закрыты.

Продукт, D01 environments, pytest.ini, release-fixture gates/export/historical pins,
accepted106, авторизация и исторические receipts неизменны. Приватные артефакты не
попадают в Git/CI. Live/seal/stage/deploy/readback не запускались. Версии и rollout
не менялись; deployment/rollback не выполнялись. NEXT: D02.2 после проверки коррекции;
автоматический переход запрещён.
