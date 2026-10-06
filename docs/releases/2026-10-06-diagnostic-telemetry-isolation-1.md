# DIAGNOSTIC-TELEMETRY-ISOLATION-1 — PASS

06.10.2026. Локальное source-only исправление default/public telemetry.
Нет freeze-коммита, сборок beta67/APK/JNI/gateway, подписи, CI, install/deploy,
renew/READY/physical arm/Telemost/soak/impairment/контакта с тестером.
Unit/local Pion synthetic watches — только исполняемые регрессии, не runtime arm.
Версии не менялись; sealed beta66 сохранён. DATA104 не исправлялся.

## Root cause и точные пути

Отключение control API не изолировало общий Recorder.Boundary и общие JSON-типы.
Stages были разрешены в общем BoundaryStages; обычный rtp observer заполнял
PictureID независимо от correlationOnly. Ring и export принимали новые данные.
Watch API был отключён, но его schema/тип хранения оставались в default binary.

| Field/event | Producer | Storage | Exporter | Default visible: до → после |
|---|---|---|---|---|
| reliable_consumed | reliablestream/stream.go consume → RecordConsumed | Recorder.boundaries, diagnostic watch.Events | boundarySnapshot → Snapshot / sink Event.Delivery | да → нет; default no-op, stage запрещён |
| base_advanced | stream.go ACK input → RecordBaseAdvanced | те же ring/watch | те же JSON paths | да → нет; default no-op, stage запрещён |
| picture_known, picture_id | telemost/boundary.go rtpBoundary.packet → RecordPicture | Boundary и диагностические copies/watch | Boundary JSON вложенно в Snapshot/Delivery/watch | да → нет; default Boundary без полей |
| evidence_watch / target/state/timestamps/events | fault_selected auto-pin / explicit local watch API | watchControl | Snapshot.Watch; sink Delivery.Watch; CloneDelivery | API не активировался, но schema существовала → полей/хранилища нет |
| rtp_correlated | signaling reorder observer, correlationOnly | tagged provisional candidates | CorrelationCommand receipt | нет → нет; default CorrelationMedia stub |
| generation/nonce, descriptor, candidates, expires_at_ms и correlation state | tagged prearm/bind/status и media callbacks | tagged correlationControl,4×8,TTL30s | отдельный tagged control JSON | нет → нет; контракт неизменен |
| session_tag, correlation_status, существующие carrier/RTP/ACK metadata | существующие trace/boundary producers | прежние bounded rings | прежние Snapshot/Event/Delivery | да → да, точная old/public schema сохранена |

Все пути указаны относительно carrier/. Default schema не переименовывает и не
удаляет ранее существовавшие поля: в частности correlation_status/session_tag остаются.
Control endpoint/Android receiver не используется как средство фильтрации exports.

## Исправленные файлы

- sessiontrace/schema_default.go и schema_diagnostic.go: mutually exclusive определения
  Boundary, Snapshot, Delivery и BoundaryStages. Default поля forensic отсутствуют
  физически в Go type, не только omitempty/runtime filtering.
- sessiontrace/forensics_default.go и forensics_diagnostic.go: compile-time hooks
  RecordPicture/RecordConsumed/RecordBaseAdvanced, selected-attempt lookup,
  snapshot/sink decoration и copy; default no-op, watchControl пустой.
- sessiontrace/watch.go теперь fc_owner_diagnostic-only; watch_target.go сохраняет
  совместимую сигнатуру отвергающего default API без storage/export.
- sessiontrace/boundary.go, trace.go, delivery.go: общая логика ring/export/copy вызывает
  build-specific hooks; определения schema перенесены без diagnostic format изменений.
- telemost/boundary.go и reliablestream/stream.go: точечная замена forensic assignments/
  calls на hooks. Correlation алгоритм и все его файлы остаются byte-identical до задачи.
- sessiontrace/watch_disabled_test.go: disabled API проверяется без отсутствующего
  default Watch field; schema защищена отдельной более сильной golden regression.
- Новые schema_default_test.go, schema_diagnostic_test.go,
  testdata/public-schema-beta66.json; telemost/forensics_bytes_test.go и
  reliablestream/forensics_bytes_test.go.

## Исполняемый контракт / T1–T11

Golden извлечён из source `5327deb414ae8aa77ce2f9490fd99c9485eba740`, а не сгенерирован
из исправленного default типа. Сравниваются полный набор JSON tags8 структур и
полный BoundaryStages, включая omitempty. Регрессия не зависит от endpoint availability.

- T1/T2: direct и helper consume/base callbacks после2100 вставок не меняют public
  snapshot bytes, ring counters или retention. Новые stages отбрасываются.
- T3/T4: PictureID, pinned watch, generation/nonce/descriptor/candidates отсутствуют
  в public schema и actual Snapshot/sink/CloneDelivery exports; hostile JSON additions
  не восстанавливают отсутствующие forensic поля. Default control по-прежнему disabled.
- T5: diagnostic actual Snapshot/sink/CloneDelivery содержит PictureID, consume/base,
  evidence_watch. Старые trace/delivery поля сохраняются.
- T6/T7/T8: прежняя matrix late attempt0 before/after, duplicate original/retry,
  attempt2, fragment mixing, wrong PictureID/timestamp/range, stale/replayed descriptor,
  session/generation/direction, cleanup/timeout/new recorder и retention2100 PASS.
  Local Pion single/multi fragments, reorder/duplicates и2000 unrelated events PASS.
- T9: default command/watch/socket controls unavailable, прежние тесты PASS.
- T10: bounded/privacy tests Go и Python PASS; новых payload/destination/credential/
  key/private-identity полей не добавлено. Descriptor/control semantics не менялись.
- T11: git diff --check PASS.

Команды и логи находятся в
`state-client-build/field65-export16/diagnostic-telemetry-isolation-1/`:

| Проверка | Результат |
|---|---|
| Go1.26.1 go test -count=1 ./... | PASS |
| go test -count=1 -race -tags=fc_owner_diagnostic ./... | PASS |
| fresh verbose sessiontrace/telemost/reliablestream diagnostic | PASS |
| default/diagnostic schema tests | PASS |
| RTP observer + Reliable DATA/ACK golden/config, default и tagged race | PASS |
| pinned correlation / boundaries / owner packaging Python | 13 passed |
| telemetry privacy / restricted correlation / Android source contract Python | 52 passed |

Первый diagnostic sessiontrace запуск внутри sandbox не смог открыть Unix socket;
вне sandbox повтор PASS. Live/provider tests намеренно SKIP. Full Python не запускался.
Android runtime/NDK/package acceptance не подменяется Python Android source guards.

## Байты и поведение

RTP packet маршалится до/после ordinary/correlation observer в tx/rx; bytes равны
в default и diagnostic тестах. Reliable DATA19/ACK20 golden wire bytes и DefaultConfig
совпадают в обоих вариантах. Старые ACK/retry tests остаются PASS.
protocol.go, engine.go, vp8.go, rtp.go, msg.go побайтно равны sealed5327deb4:
хэши в verification.json. Следовательно wire codec, retry/RTO, packetization,
fragment layout и pacing алгоритмы не изменялись. Это локальная byte/behavior
проверка, не заявление о binary reproducibility APK или физическом качестве связи.

## Python: авторитетное окружение следующего freeze

Предыдущие6 failures/25 errors не являются product failures: bare pytest запускался
без release-fixture/toolchain env. Тесты не ослаблялись, readiness/control dirty overlays
в acceptance не добавлялись. Для полного прогона использовать clean scoped source,
workflow `.github/workflows/test.yml` / control.yml и `scripts/ci_release_fixtures.py`.

- Python3.13, control/requirements.lock + device_identity/requirements.lock.
- Python full-suite fixture toolchain Go1.26.0 согласно этим workflow; native/owner
  gate отдельно Go1.26.1. Не смешивать pin без явного обновления authoritative policy.
- GOTOOLCHAIN=local, выделенные GOPATH/GOCACHE; локальные nginx/iproute2/keepassxc.
- Полная Git history/historical commit `4bb53b0605c2c898b6a3feca6ee15fd34b943a94`.
- В новом clean frozen checkout: `ci_release_fixtures.py prepare --output <fresh>
  --go <pinned-go>`; затем `ci_release_fixtures.py run --fixtures <fresh>
  --go <pinned-go> --nginx <nginx> -- python -m pytest -q`.
- Wrapper проверяет source_commit==HEAD, inventory hashes и historical pin, затем
  задаёт FC_TEST_HTTP_ARTIFACT/SHA256, FC_TEST_SYNC_ARTIFACT/SHA256,
  FC_TEST_READINESS_ARTIFACT, FC_TEST_HISTORICAL_HTTP_ARTIFACT, FC_TEST_GO,
  FC_TEST_NGINX. Нельзя указывать выдуманные пути/хэши или fixtures от чужого commit.
- Для Java gates: JDK17, JAVA_HOME/PATH, FC_JAVA/FC_TEST_JAVA по local runbook;
  Android golden gate отдельно получает FC_ANDROID_GOLDEN_CLASSPATH после
  Gradle control-tests test/goldenClasspath. Fixture preparation здесь НЕ запускалась.

## Сохранность и следующий шаг

HEAD `8d046321039d0bd1e18ecc1af979ff90f591e029` неизменен. Before inventory, scoped
allowlist, final-source hashes и verification.json подтверждают сохранность unrelated
dirty work, неизменность correlation implementation и всех5 sealed beta66 файлов.
STATUS/PLAN и этот отчёт обновлены; версии/public catalogs/invitation channels нетронуты.
Runtime rollback не нужен; возможный откат — только scoped patch, никогда reset dirty tree.
Предыдущий freeze FAIL остаётся историческим результатом; полные native/Android/CI/
signing/provenance gates ещё необходимы. Отдельный freeze теперь можно повторить.

Единственный рекомендуемый следующий шаг: повторить PINNED-EVIDENCE-FREEZE-1 с
правильным source-bound Python окружением и всеми ранее обязательными gates.
