# BOOTSTRAP-PRIMARY-CAUSE-1 — 08.10.2026

**PASS — только сохранение диагностической причины, не reconnect.**
База: `7b27d79c08b133e595fe0a1ebf5a3a4af2602662`, beta70/code70, interframe.
Изменения находятся в отдельной копии; основной dirty worktree не редактировался.
Нет нового commit/version/tag, APK, подписи, установки или deployment.

Потеря: первичный HELLO Recv error заменялся bootstrap_protocol_rejected;
Go/native сохранял startup_failed/state3, Java — только BOOTSTRAP_UNAVAILABLE.
Теперь наблюдение до generic mapping удерживается в owner-only записи schema1:
attempt (существующий native sequence), started/observed/completed time, фиксированные
stage/cause/status и complete. Первый опубликованный результат сохраняется при
cleanup; завершение запечатывает запись. Новый startup не принимает старые callbacks.
Неизвестная/уже стёртая нижним слоем причина остаётся UNKNOWN, не raw err.Error().

JNI ABI/bridge неизменны. Additive owner_startup проходит через существующий stats;
owner-only StartupDiagnostics сохраняет последний результат независимо от ring и
добавляет безопасную typed cause к прежнему пользовательскому enum. Существующий
DUMP-protected OwnerFaultReceiver получает только read-only command startup.
Public/debug/release/friends используют no-op shim. Pre-handle validation не является
частью нового positive-handle startup record; её старый контракт не меняется.

Проверки: исходный неизменённый RED стал GREEN; Go default/owner affected-package
race PASS; настоящий host Go/native/JNI/Java PASS с заменой только внешней bootstrap
границы и session plane; Android arm64 NDK compile PASS; focused Android JVM66,
Python30, exporter и прежние TCP cleanup7 PASS. Новые зависимости/lockfiles отсутствуют.
Host Context/VpnService/AtomicFile — явно тестовые stubs, Android ART/VPN/service и
настоящая AtomicFile реализация не исполнялись. Это не release acceptance.

Объектные события exporter распознаются; неподдержанный формат, ошибка чтения,
отсутствующее поле, ограничение выдачи и неизвестная история вытеснения различаются.
Историческая потеря object-events и последующее обновление ring не отменяются.

Полный scope, patch, hashes, исходники, local build provenance и все receipts,
включая ошибки подготовки тестов: `state-client-build/bootstrap-primary-cause-1/`.
Rollback/deployment не применимы: installed beta70, gateway, sealed pairs67/68/69,
targeted-arm и A/B evidence не изменены, новых процессов на endpoints нет.

Историческая причина reconnect — UNKNOWN.
Реальное исправление reconnect не доказано.
Physical selected-retry не выполнялся; preparations/arms/drops0.

Следующий отдельный gate: immutable diagnostic-successor acceptance без изменения
транспорта. Перед будущей runtime-проверкой нужны свежие restricted chain/readiness,
leaf validity и gateway lifecycle; старые RU/NL health snapshots не являются причиной
reconnect. Peer-worker связывается с bootstrap только при доказанной зависимости.
Никакая упаковка/live-проверка не запускается автоматически.
