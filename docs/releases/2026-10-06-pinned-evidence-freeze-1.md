# PINNED-EVIDENCE-FREEZE-1 — PASS

06.10.2026, resume после принятого DIAGNOSTIC-TELEMETRY-ISOLATION-1.
Итог — только immutable диагностическая пара beta67. Не публичный релиз и не rollout.
Создание UTC: `2026-10-06T13:51:48.931669+00:00`.

## Source freeze / scoped attribution

- Frozen commit: `ffd27988468fba427aaba6213b862dca01020972`.
- CI-only tag: `diag-owner-beta67-ci1`; отправлен только этот tag, не main/release branch.
- Base: `5327deb414ae8aa77ce2f9490fd99c9485eba740` из sealed beta66 source.
- Пользователь отдельно разрешил локальный validation-коммит до gates, необходимый
  для git archive HEAD/source-bound fixtures. После всех local gates PASS тот же SHA
  признан frozen source, без нового source drift. Затем hosted CI и signing.
- Изолированный checkout `/tmp/fc-freeze67-validation2`, clean status;
  исходная dirty-ветка остаётся на8d046321. Readiness/control dirty overlays исключены.
- Before inventory, allowlist, SHA256 source-inputs, incremental source bundle и receipts:
  `state-client-build/field65-export16/pinned-evidence-freeze-1/resume2/`.
  Bundle требует base5327deb4; независимое восстановление возможно через CI-only tag.
- Изменена только ownerDiagnostic version override67; Friends/default остаётся beta65.
- Никакого unresolved vcs.modified=true: restricted JNI и gateway checked false;
  normal native связывается через authoritative builder/source/input hashes.

Точный allowlist наложения на base (документация STATUS/PLAN — scoped note, не копия
всего dirty содержимого):

- `carrier/reliablestream/ack_proof_test.go`
- `carrier/reliablestream/fault_runtime_test.go`
- `carrier/reliablestream/forensics_bytes_test.go`
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
- `carrier/sessiontrace/forensics_default.go`
- `carrier/sessiontrace/forensics_diagnostic.go`
- `carrier/sessiontrace/schema_default.go`
- `carrier/sessiontrace/schema_default_test.go`
- `carrier/sessiontrace/schema_diagnostic.go`
- `carrier/sessiontrace/schema_diagnostic_test.go`
- `carrier/sessiontrace/testdata/public-schema-beta66.json`
- `carrier/sessiontrace/trace.go`
- `carrier/sessiontrace/watch.go`
- `carrier/sessiontrace/watch_disabled_test.go`
- `carrier/sessiontrace/watch_target.go`
- `carrier/sessiontrace/watch_test.go`
- `carrier/telemost/boundary.go`
- `carrier/telemost/correlation_test.go`
- `carrier/telemost/forensics_bytes_test.go`
- `carrier/telemost/head_loss_test.go`
- `carrier/telemost/signaling.go`
- `carrier/telemost/watch_test.go`
- `carrier/wholedevice/session.go`
- `clients/android/app/build.gradle`
- `clients/android/app/src/ownerDiagnostic/java/com/familyconnect/app/OwnerFaultReceiver.java`
- `docs/PLAN.md`
- `docs/STATUS.md`
- `docs/releases/2026-10-06-diagnostic-telemetry-isolation-1.md`
- `docs/releases/2026-10-06-pinned-evidence-candidate-1.md`
- `docs/releases/2026-10-06-pinned-evidence-correlation-1.md`
- `docs/releases/2026-10-06-pinned-evidence-freeze-1.md`
- `docs/releases/2026-10-06-selected-retry-evidence-gap-1.md`
- `pilot/android-restricted/native/fault.go`
- `tests/test_pinned_correlation.py`

## Local acceptance

| Gate | Результат |
|---|---|
| Go1.26.1 default ./... | PASS |
| Full diagnostic tagged race ./... | PASS |
| Correlation/Pion/ACK/late attempt0/retries/duplicates/reorder/fragment mixing | PASS |
| Cleanup/timeout/replay/session/generation/direction,retention2000+ | PASS |
| Public beta66 schema golden + diagnostic forensic schema | PASS |
| RTP/Reliable DATA/ACK bytes и transport defaults | PASS |
| Python3.13.16 + Go1.26.0 source-bound prepare/run | 1804 passed,26 skipped,2 warnings |
| Fixture source_commit/inventory hashes/historical pin | PASS |
| NDK28.2.13676358/Go1.26.1 arm64 restricted owner+Friends/normal AWG/TCP | PASS |
| ELF64/AArch64/16KiB LOAD alignment/native JNI exports | PASS |
| Native metadata/source guards/stale metadata rejection | PASS |
| Host-cgo default/race, Java receiver routing, standalone JVM | PASS |
| Host TCP bridge / pinned AWG suite count3 | PASS |
| OwnerDiagnostic unit / Friends unit | 258/258 PASS,0 failures/errors/skips each |
| OwnerDiagnostic lint / Friends lint | PASS,0 Error/Fatal |
| Package/version/non-debuggable/arm64-only/DUMP/receiver isolation | PASS |
| APK native bytes equal corresponding accepted outputs | PASS |
| Public source secret guard | 1810 entries,0 blocked |
| Scoped documentation links / git diff --check | PASS |

Fixture receipt binds the exact frozen SHA; full Python is not a bare pytest invocation.
Python3.13.16 standalone archive SHA256:
`0a0272910b10417c659a9312fb3f2d7a6d774da7bd510999be7a3ba83273dc1f`.
Lockfiles: control/requirements.lock + device_identity/requirements.lock.
The first locally compiled Python3.13.12 lacked SSL/sqlite headers and was rejected
before fixture acceptance; accepted run used complete3.13.16 runtime, no test weakening.
The26 skips are reported, not promoted to executed tests; no live/provider/device run.
Native owner workflow pin is Go1.26.1, distinct from Python fixture pin1.26.0.

## Control trust boundary / isolation

Контракт не перерабатывался: session/direction/seq/attempt/fresh128-bit generation;
max4 provisional identities ×8 fragments; descriptor exact carrier/PictureID/RTP;
TTL30s, one-shot binding, stale/replay/late-original rejection.
Trusted operator переносит descriptor out-of-band. Отдельной подписи descriptor нет.
Unix0700/0600+SO_PEERCRED: same UID1000 получает control response; foreign UID0
получает close без response (синтетический helper, status-only, без arm/prearm).
Android owner receiver защищён DUMP; routing/JNI проверены локально, настоящий
телефон не использовался. Default controls недоступны; default telemetry совпадает
с pre-beta67 golden. Diagnostic forensic stages/PictureID/correlation сохраняются.
Transport wire/RTO/pacing/ACK не менялись. DATA104 не исправлялся.

## Hosted CI — 17/17 PASS

- Windows ordinary user access: [37447305239](https://github.com/Joker20380/family_connect/actions/runs/37447305239) — success.
- Owner diagnostic pair acceptance: [37447305340](https://github.com/Joker20380/family_connect/actions/runs/37447305340) — success.
- Linux control preview: [37447305392](https://github.com/Joker20380/family_connect/actions/runs/37447305392) — success.
- phase0: [37447305289](https://github.com/Joker20380/family_connect/actions/runs/37447305289) — success.
- Windows AWG native pilot: [37447305237](https://github.com/Joker20380/family_connect/actions/runs/37447305237) — success.
- Android diagnostic acceptance: [37447305375](https://github.com/Joker20380/family_connect/actions/runs/37447305375) — success.
- Windows TCP native pilot: [37447305238](https://github.com/Joker20380/family_connect/actions/runs/37447305238) — success.
- Client builds: [37447305373](https://github.com/Joker20380/family_connect/actions/runs/37447305373) — success.
- Review Windows TCP acceptance: [37447305417](https://github.com/Joker20380/family_connect/actions/runs/37447305417) — success.
- Desktop render review: [37447305411](https://github.com/Joker20380/family_connect/actions/runs/37447305411) — success.
- Windows control conformance: [37447305256](https://github.com/Joker20380/family_connect/actions/runs/37447305256) — success.
- Android Friends readiness wire contract: [37447305244](https://github.com/Joker20380/family_connect/actions/runs/37447305244) — success.
- TCP pilot: [37447305415](https://github.com/Joker20380/family_connect/actions/runs/37447305415) — success.
- XHTTP local transport acceptance: [37447305386](https://github.com/Joker20380/family_connect/actions/runs/37447305386) — success.
- AmneziaWG pilot: [37447305489](https://github.com/Joker20380/family_connect/actions/runs/37447305489) — success.
- Messenger prototype: [37447305363](https://github.com/Joker20380/family_connect/actions/runs/37447305363) — success.
- Desktop visual checks: [37447305313](https://github.com/Joker20380/family_connect/actions/runs/37447305313) — success.

Client release и TCP release/setup_release jobs проверены как skipped.
Distribution workflows не запускались. Без unsafe v-tag selector.
Owner artifact ID `11403883147`, run `37447305340`.
ZIP SHA256 `795398b08f2ea831395f5165e1187a127273c53b2aee87f5e5640a656a0ee477` совпал с GitHub digest.
Первая временная ссылка истекла во время ожидания разрешения; повторная выдача
того же artifact ID успешно скачана, без rebuild/relabel. Временные URL не входят в manifest.
CI pair проверена отдельно от local pair: одинаковый source SHA, но normal native
может отличаться bytes из-за build paths; local hashes не подменяют CI hashes.
Подпись выполнялась только после17/17 CI PASS, artifact/source/native/package/privacy checks.

## Immutable beta67 artifacts / signing

Package `com.familyconnect.app.friends`, version `0.1.18-beta67`, code67,
non-debuggable, arm64-v8a. APK signed совместимым PKCS12 signer; сертификат проверен
до подписи, apksigner после подписи подтвердил единственного signer и v2 signature.
Zipalign16KiB PASS; все исходные APK entries остались byte-identical после подписи.
Signer SHA256: `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
Ключ/пароль не выводились, не копировались в Git/CI/manifest.

Pair directory:
`state-client-build/field65-export16/pinned-evidence-freeze-1/immutable-ownerDiagnostic-beta67/`.
Новый отдельный каталог, файлы read-only; существующая beta66 пара не заменялась.

| File | SHA256 |
|---|---|
| `libfc-awg.so` | `15f1da2ea95957cdba28806b23b3ca7d698b35b2d8cb835d4ce97285270a6e6a` |
| `FamilyConnect-OwnerDiagnostic-0.1.18-beta67.apk` | `8ef45ca26917227e64079cdd49d35f133a03617300b8446f1a476a5d7a69822f` |
| `libfc_restricted.so` | `4a7b6bc17c8e7cb704d3cdfdcfc9aec9333dd17d5d17ba46dbe5d435f805fa81` |
| `restricted-build.json` | `ffbf2c033464e15f47b4e4fc54197e9991158e061612758dcee63068d0f7d5b3` |
| `awg-build.json` | `cc5bea67ec7523a9fbb26a00e6bb9868bf1027a2b5d2abe15fa3bc5ed7810185` |
| `bootstrap-broker` | `c1370f58dead852efeb21d7b1d8c20e5eabcf333c7df7ec8dd258d5c26bc4143` |
| `diagnostic-contract.json` | `0551d1b5ec14a1d07f0eceefd2f60c755dce0643c17cc6ef9ace3aa3c2631ec7` |
| `pair-manifest.json` | `98dabfa38cb2cd437b5ec45700e936da3ae0b94ef47f11b8904a90faa472fc77` |

Manifest binds commit, tag/run IDs, artifact archive, APK/JNI/normal/gateway hashes,
signer, versions, toolchain pins and creation UTC. Correlation schema1;
prearm/descriptor pinned-correlation-v1; owner control schema1;
telemetry golden public-beta66-golden-v1 (SHA2564c262cc8…e902).
Diagnostic contract also shipped as diagnostic-contract.json.
APK privacy scanner: bounded private-container/complete private PEM/token scan PASS;
не заявляется универсальным доказательством отсутствия любого возможного секрета.

## Сохранность, rollout/rollback и ограничения

Все5 sealed beta66 files совпали before/after SHA256; receipts beta66-before/after.json.
Исходная dirty-ветка и excluded work сохранены. Root docs обновлены после acceptance;
artifact source — исключительно frozen SHA, не текущий dirty root checkout.
Ничего не installed/deployed/renewed/READY/armed. Не запускались физический Telemost,
soak/impairment/Краснодар; public/default/catalog/invitation channels не менялись.
Нового runtime rollout нет, поэтому runtime rollback сейчас не требуется.
Для отдельного deploy использовать только эту immutable pair после проверки manifest;
sealed beta66 остаётся сохранённой предыдущей парой, не перезаписывать её.
Local/CI success не является физическим callback-level proof. OWNER-CONTROLLED-LOSS-1
остаётся FAIL/UNKNOWN, DATA19 protocol healing не переоценивается.

Отдельная owner-only deploy-задача теперь может начинаться с отдельным разрешением.
Единственный рекомендуемый следующий шаг: выполнить такую deploy-задачу по immutable
manifest, без автоматического разрешения physical run в рамках этого freeze.

---

## История первого заблокированного запуска

### PINNED-EVIDENCE-FREEZE-1 — FAIL (исторический результат до isolation fix)

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
