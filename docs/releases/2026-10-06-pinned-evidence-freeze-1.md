# PINNED-EVIDENCE-FREEZE-1 — FAIL

06.10.2026. Выполнение остановлено по обязательному stop condition default/public
isolation. Это не повтор физического DATA19 experiment и не отмена доказанной
protocol recovery. OWNER-CONTROLLED-LOSS-1 остаётся FAIL / UNKNOWN.

## Исходники и границы

HEAD исходного dirty tree: `8d046321039d0bd1e18ecc1af979ff90f591e029`, неизменен.
Инвентаризированы 95 dirty/untracked путей до любых изменений. Точные категории,
исходные SHA256 и status: `state-client-build/field65-export16/pinned-evidence-freeze-1/inventory.json`.
Начальный allowlist:32 пути; `allowlist.json`. Readiness/control source и прочие
посторонние изменения не переносились. Индекс/ветка исходного репозитория не менялись.
Чистый baseline: `5327deb414ae8aa77ce2f9490fd99c9485eba740` из sealed source.
Изолированная рабочая копия: `/tmp/fc-pinned-freeze67-source` (не frozen commit).
В неё применён allowlist, owner-only override67; public/default65 не менялся.
Временная копия Xray клонирована clean на `d2758a023cd7f4174a5a5fa4ff66e487d4342ba0`;
грязный исходный Xray не использован для сборки. Сборок ещё не было.
`reviewed-delta.tar.gz` и `reviewed-source.json` сохраняют проверенные файлы вне /tmp.
Это архив review evidence, НЕ release/pair manifest и НЕ доказательство clean VCS.

### Точный allowlist наложения на baseline

- `carrier/reliablestream/ack_proof_test.go`
- `carrier/reliablestream/fault_runtime_test.go`
- `carrier/reliablestream/stream.go`
- `carrier/roombroker/broker.go`
- `carrier/sessiontrace/boundary.go`
- `carrier/sessiontrace/correlation.go`
- `carrier/sessiontrace/correlation_command.go`
- `carrier/sessiontrace/correlation_disabled.go`
- `carrier/sessiontrace/correlation_linux.go`
- `carrier/sessiontrace/correlation_linux_test.go`
- `carrier/sessiontrace/correlation_other.go`
- `carrier/sessiontrace/correlation_test.go`
- `carrier/sessiontrace/delivery.go`
- `carrier/sessiontrace/fault_disabled.go`
- `carrier/sessiontrace/fault_enabled.go`
- `carrier/sessiontrace/trace.go`
- `carrier/sessiontrace/watch.go`
- `carrier/sessiontrace/watch_disabled_test.go`
- `carrier/sessiontrace/watch_test.go`
- `carrier/telemost/boundary.go`
- `carrier/telemost/correlation_test.go`
- `carrier/telemost/head_loss_test.go`
- `carrier/telemost/signaling.go`
- `carrier/telemost/watch_test.go`
- `carrier/wholedevice/session.go`
- `clients/android/app/build.gradle`
- `clients/android/app/src/ownerDiagnostic/java/com/familyconnect/app/OwnerFaultReceiver.java`
- `docs/releases/2026-10-06-pinned-evidence-candidate-1.md`
- `docs/releases/2026-10-06-pinned-evidence-correlation-1.md`
- `docs/releases/2026-10-06-selected-retry-evidence-gap-1.md`
- `pilot/android-restricted/native/fault.go`
- `tests/test_pinned_correlation.py`

Дополнительно только в изолированной копии: новый
`carrier/sessiontrace/freeze_default_isolation_test.go`; в существующем
`correlation_linux_test.go` добавлен тест чужого UID (требует root, здесь SKIP).
В исходном дереве изменяются только STATUS, PLAN и этот новый release-report.
Все исходные 95 файлов до documentation closeout сохранили свои хэши:
`preservation-before-docs.json`. Регрессия не внедрена в основной dirty tree.

## Обнаруженный блокер

`carrier/sessiontrace/boundary.go` без build tag расширяет `BoundaryStages` новыми
`reliable_consumed|base_advanced` и структуру Boundary JSON-полями
`picture_known|picture_id`. `Recorder.Boundary` сохраняет их в обычном 64-entry ring.
`reliablestream/stream.go` вызывает новые stages без diagnostic gate;
`telemost/boundary.go` извлекает PictureID также для обычного rtp observer.
`CorrelationMedia` disabled stub блокирует отдельный correlation-only observer,
но не эти обычные Boundary вызовы. Старый default-тест проверял только stub/control.

Контрпример `go test -count=1 -v ./sessiontrace -run '^TestFreezeDefault'` (без tag):
- `reliable_consumed`: FAIL, новое событие экспортируется;
- `base_advanced`: FAIL, новое событие экспортируется;
- PictureID metadata: FAIL, новые поля экспортируются.

Полный вывод: `default-isolation-counterexample.log` в evidence directory.
Это не обнаружение payload/credential leak и не изменение RTP/Reliable bytes;
это доказанное нарушение запрета расширять default telemetry.
По stop condition код транспорта/диагностики не исправлялся в этой freeze-задаче.
Прежний общий isolation PASS нельзя использовать для выпуска.

## Контракт и trust boundary

Pinned-correlation/prearm/descriptor: `CorrelationSchema=1`; существующий owner
fault receipt schema1. Legacy EvidenceWatch не имеет собственного поля schema;
единую версию instrumentation manifest до STOP не выпускали. Форматы не повышались.
Session/direction/seq/attempt/128-bit generation связываются с carrier sender/message
и PictureID/RTP timestamp/range каждого fragment. Capture bounded4×8, TTL30s.
Trusted operator переносит descriptor out-of-band; самостоятельной подписи descriptor
нет. Gateway opt-in Unix0700/0600+SO_PEERCRED; Android ownerDiagnostic receiver DUMP.
Descriptor не вкладывается в production traffic. Default control stub отвергает arm/bind,
socket/receiver отсутствуют по source checks; это не означает полной telemetry isolation.
Контракт подходит только доверенному owner operator/локальному OS boundary,
не аутентифицирует descriptor в недоверенном канале доставки.
Wrong-UID acceptance НЕ завершена: новый subprocess-тест пропущен без root.
Android runtime/ABI parity НЕ подтверждена в этой задаче до STOP.
Reverse DATA104 не исправлялся; direction остаётся частью ключа.

## Проверки

- Pinned Go:1.26.1. NDK найден r28c/28.2.13676358, но build/acceptance не запускались.
- Default `go test ./...`: PASS после повторения вне sandbox (в sandbox loopback EPERM).
- Diagnostic `go test -race -tags=fc_owner_diagnostic ./...`: PASS.
- Fresh verbose sessiontrace/telemost/reliablestream: PASS; late original before/after,
  duplicate original/retry, attempt2, fragmented attempts, cross-mix/PictureID/range
  mismatch rejection, Pion reorder/duplicates, replay/session/generation/direction,
  cleanup/expiry/new recorder, retention2100 и local Pion2000+ covered.
- Live tests SKIP намеренно; root-only wrongUID SKIP. Ни одного physical run.
- Эти результаты относятся к изолированному review source, НЕ frozen commit.
- Новая default telemetry regression: FAIL, является причиной STOP.
- Full Python запуск начат до обнаружения STOP:1697 passed,102 skipped,
  6 failed,25 errors. Это слишком широкий, не настроенный как scoped acceptance
  прогон; ошибки относятся к отсутствующим fixture/toolchain переменным
  `FC_TEST_HTTP_ARTIFACT`, `FC_TEST_HTTP_SHA256`, `FC_TEST_HISTORICAL_HTTP_ARTIFACT`,
  `FC_TEST_GO` и locked Go handoff setting. Чужие readiness/control dirty overlays
  не переносились. Не считается принятым scoped Python gate; эти окружения после
  STOP не исправлялись и дополнительные readiness artifacts не собирались.
  Лог `python.log`, receipt `python.json`; privacy/source tests не заменяют
  проваленную executable default regression.
- Native arm64/restricted/normal build, symbol/export/device-compatible JNI, host-cgo
  acceptance этого freeze, Android unit/lint/JVM/package/manifest/JNI-in-APK: NOT RUN.
- Secret scan/docs links как complete acceptance gates: NOT RUN; полный privacy/bounds
  verdict нового кандидата не присваивается. Source review не нашёл новых payload,
  destination или secret полей в descriptor, но default telemetry gate FAIL.
- `git diff --check` isolated source и исходного дерева: PASS.
  Целевая ссылка нового отчёта из STATUS/PLAN существует; полный docs link scan
  не выполнялся. Финальная сохранность фиксируется в `closeout.json`.

## Версия, CI, artifacts, signing

`0.1.18-beta67` /67 только в изолированном build.gradle. Immutable successor НЕ создан.
Удалённая read-only проверка не нашла beta67 tags. Frozen commit отсутствует.
Safe CI-only namespace `diag-owner-*` проверен по workflow source; public release job
в clients.yml выбирается только v-tag либо main+Release message. Ничего не pushed,
не tagged и не запущено в hosted CI. Ни одного publication job.
APK/restricted JNI/normal native/gateway hashes: N/A — новых артефактов нет.
Signer verification для beta67: NOT RUN, ключи не читались и не использовались.
Pair manifest: отсутствует. Нельзя ссылаться на beta66 hashes как beta67 provenance.

## Сохранность и следующий шаг

`beta66-before.json` и `beta66-after.json` совпадают для всех пяти sealed файлов
в `diag-source-freeze-1/immutable-ownerDiagnostic-beta66`. Новая сборка/подпись,
install/deploy/READY/renew/physical arm/Telemost/soak/impairment/Краснодар не выполнялись.
Публичные/default/catalog/invitation версии и каналы не изменялись.
Не нужен runtime rollback: runtime не менялся. Нельзя reset/clean исходный dirty tree.
Отдельная deploy-задача пока НЕ может начинаться.

Единственный рекомендуемый следующий шаг: отдельно исправить diagnostic-only gating
новых stages/PictureID, закрыть сохранённый default-контрпример и затем повторить
полную процедуру freeze/NDK/Android/CI/signing.
