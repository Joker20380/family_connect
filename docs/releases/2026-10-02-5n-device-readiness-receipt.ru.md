# 5N-DEVICE-READINESS-RECEIPT — локальный product gate, 02.10.2026

**5N-DEVICE-READINESS-RECEIPT = PASS.** Это локальная реализация/проверка продукта,
не повтор PROV-1, не подтверждение production owner readiness и не FIELD-1.

## Источник и границы

- Starting HEAD: `d5105e8c4f44aa4dac2153370800d98a229bc7d1`.
- Implementation/build source: `e81738083457912da5b1032c45cfbe92bad112cc`,
  `feat(diagnostics): add restricted readiness product receipt`.
- Последующая task-owned запись меняет только packaging assertion и документацию;
  Android/native/server implementation соответствует build source выше.
- Production/RU/NL/Redmi не опрашивались и не менялись; SSH/ADB/install не выполнялись.
  Authority не обновлялась; restricted services не запускались. Локальные тесты
  используют синтетические ключи/authority и loopback, не production credentials.
- Attempt14 остаётся DEPLOYMENT FAILED / ROLLED BACK. Последнее документированное
  состояние — обычные18084/18085 живы, restricted выключен, CRL25 сохранён;
  здесь это не новая live-проверка. Установленный canary54 и public beta51 не менялись.
- Восемь исходных dirty tracked файлов и девять untracked отчётов сохранены.
  Только новые task-owned вставки staged в пересекающихся документах; чужие изменения
  не включены в коммиты. Push: no. DIAG-1/OPS-1/FIELD-1: not started.

## Авторитетный момент READY

Реальный `FriendsReadinessProtocol.fetch` по-прежнему выполняет challenge → in-app
Device Identity proof → fetch. HTTP200 недостаточно. `ReadinessProduct.imported`
вызывает `RestrictedCache.importProduct`: native `ValidateDelivery` для credential,
CRL/device binding/BootstrapDirectory; monotonic checks; Keystore-encrypted AtomicFile
replacement и readback сравнение. Correlation сохраняется внутри того же encrypted
state. Затем `RestrictedCache.evaluate` повторно читает/валидирует persisted bundle,
проверяет актуальную expiry и вызывает **тот же `usable()`**, которым пользуется
`RestrictedTunnelEngine` через Orchestrator. Только после этого создаётся READY.
Время для post-import проверки обновляется, expiry во время записи не даёт READY.

Это доказательство пригодности credential/bootstrap для recovery, **не** утверждение,
что уже созданы provider session/VPN или пройдены браузерные/traffic gates.

## Схема и безопасная доставка

`READINESS_IMPORT_RESULT`, `version=1`, exact allowlist, payload≤2048bytes:
`correlation_id`, `challenge_id`, `fetch_id`, `result`, `failure_reason`,
`provisioning`, `bootstrap`, `orchestrator_usable`, `revision`, `minimum_crl`,
`expires_at`, `observed_at`, `phase`, `app_version`, `version_code`, `type`, `version`.
IDs — random32hex; correlation=challenge ID, fetch ID отличается. Никаких Device
Identity, proof/crypto bytes, bundle, join_url, OAuth, room URL, traffic/user data
или exception strings. Numbers bounded≤2^53−1; app_version≤64ASCII characters.

Stable codes: `READY`, `NATIVE_VALIDATION_FAILED`, `BOOTSTRAP_VALIDATION_FAILED`,
`ATOMIC_IMPORT_FAILED`, `PERSISTENCE_FAILED`, `EXPIRED_ON_IMPORT`,
`ORCHESTRATOR_NOT_USABLE`, `INTERNAL_ERROR`, `STALE_STATE`,
`AUTHORIZATION_REJECTED`, `FETCH_FAILED`, `MISSING`.

Локально `ReadinessReceiptStore` пишет `{payload,ack_state}` в private
`getNoBackupFilesDir()/restricted-readiness-result-v1.json`,≤4096bytes,
AtomicFile+fsync+readback. Файл не экспортируется/логируется/бэкапится. Credential
по-прежнему только в существующем encrypted vault. Нет shell dump, ContentProvider,
debug bypass, exported signer или remote command API.

ACK использует существующий trusted Friends control HTTPS, не новый transport:
`/friends/restricted-readiness/ack-challenge` → обычный in-app proof → `/ack`.
Сервер связывает одноразовый120s nonce с SHA256 канонического safe payload,
purpose/device/key/current grant/admission/authority/CRL. Проверяет digest/replay,
successful fetch metadata и revoked/superseded state перед durable ACK.
Public/admin notices не подходят для приватного device ACK и не используются.
Additive DB table `restricted_readiness_results` ограничена16 попытками/device,
24h pruned при новой попытке; raw private device reference не попадает в safe readback.

ACK/receipt-write failure после успешного import **не уничтожает local READY**.
Сначала пишется локальная квитанция, затем ACK, затем delivery state. ACK_PENDING
или UNKNOWN — не ошибка credential. Если сама запись receipt не удалась,
durability не заявляется; ACK всё ещё может доставить результат. Если недоступны оба
канала, acceptance UNKNOWN, не сфабрикованный PASS.

## Restart и acceptance без UI

Первый foreground prewarm каждого нового процесса читает настоящий encrypted bundle,
не прошлую квитанцию: native credential/directory validation, expiry/floors/denial,
пересчёт usable, новая phase=restart receipt. Existing denied tombstone/expired/
stale/crypto-invalid state не даёт READY. Offline revocation visibility ограничена
существующим signed CRL TTL; мгновенное знание неопубликованной revocation не обещано.
Legacy cache без encrypted correlation не создаёт выдуманный historical ACK;
следующий обычный refresh запишет IDs. Нет нового polling/retry worker.

Новый packaged HTTP CLI `--readiness-ack CORRELATION --material PRIVATE_PATH`
(с обычным `--root`) читает серверную DB **read-only**, связывает ACK с sole admitted
owner, повторно проверяет актуальные authorization/expiry, выдаёт только safe fields.
`OwnerProduct.observe` принимает generation-scoped server challenge/fetch receipts
плюс этот authenticated owner-bound readback. Старый UI-only формат отвергается.
ADB swipe/tap не участвует в доказательстве, safe UI остаётся supplemental.
Это authenticated product statement, не hardware remote attestation.

Схема payload transport-neutral; будущий DIAG-1 может использовать её для incident/
support, OPS-1 для service delivery/Reticulum. Эти системы/Reticulum не реализованы.
[Полный текущий контракт и read-only CLI](../../deploy/friends/restricted/DEVICE_READINESS_RECEIPT.md).

## Canary55 — built/signed, NOT installed

- Clean export1626 файлов из `e81738083457912da5b1032c45cfbe92bad112cc` проверен
  против git blobs; ignored stale generated outputs не копировались.
- Local APK: `state-client-build/android-canary55-receipt-e817380/artifacts/FamilyConnect-canary55-receipt-e817380-arm64.apk`.
- SHA256: `680a21f60e69cb62d2c7a70be07234b34196e178f0207ed69cb4b422b7bc6247`.
- Size49,597,307bytes; applicationId `com.familyconnect.app.friends`;
  versionName `0.1.18-canary55-receipt`, versionCode55; arm64-v8a only.
- Signing SHA256: `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
  Same existing private beta signer; APK v2 signature PASS,55>54: update-compatible.
  No uninstall/data clear/reactivation/install. Public default version51 unchanged;
  private55 packaging override recorded in ignored `packaging.gradle`.
- Fresh normal JNI SHA256 `d9272cb6546b2d737aea63d999ef9f5993edf53e06f83b515c6ebc519f3a5c5e`;
  restricted JNI `c82770421b9373a16f8730481c2e0ce2d0788d2c5e3a571e8b2d1b38b0da3f74`.
  Go1.26.1 normal/1.26.0 restricted; NDK27.2.12479018; pinned Xray
  `d2758a023cd7f4174a5a5fa4ff66e487d4342ba0`. Native outputs match APK entries.
- Nondebuggable; backup/cleartext disabled; no diagnostic exported activity.
  Nested archive scan1074 entries, zero secret findings. One hash-pinned known
  stdlib bytecode Basic-scheme false positive reviewed; no actual OAuth token was
  loaded for an exact-token search. Signing private material not printed/exported.

## Tests и воспроизводимость

- Control JVM `gradle -p clients/android/control-tests test`:160 passed,0 skipped/failures; Android clean export
  `:app:testFriendsUnitTest`:215 passed,0 skipped/failures. Suites overlap; не375
  независимых тестов. `:app:assembleFriends :app:lintFriends`:PASS,0errors/37warnings.
- 187 Python tests PASS: readiness receipts, owner handoff, restricted service,
  HTTP transition/runtime, restricted runtime; native fixtures и реальный локальный
  isolated HTTP challenge/fetch/signed ACK/read-only CLI включены. Два historical
  exact-attempt9 nginx tests запущены отдельно с исходным pinned HTTP:2 PASS.
- Readiness adapter packaging/closure/secret guards/clean committed export/repeat
  determinism:31 PASS. Новый обязательный receipt-модуль учтён точным сравнением
  inventory с manifest, не старым hardcoded count13.
- Native `go test ./wholedevice ./bootstrap ./familysession`:PASS.
- Deterministic A–J: native/bootstrap negatives; atomic-write failure preserves old
  state; corrupted persistence readback; receipt/ACK failure leaves READY credentials;
  restart ignores old receipt and revalidates; expiry/denial/stale/current revoked
  grant/certificate reject; unavailable UI does not affect ACK acceptance; exact
  payload redaction. Replay, altered result, wrong owner/fetch/floor/revision,
  ACK_PENDING and expiry-during-import дополнительно проверены.
- Android storage/prewarm tests use injected deterministic storage; реальные
  Android Keystore/filesystem crash/power-loss/device instrumentation **не запускались**.
  Это local implementation PASS, не physical persistence/rehearsal acceptance.
- Sandbox socket denial resolved by approved host execution. `/tmp` quota broke
  initial Gradle/adapter execution; task temporary data moved without deleting
  unrelated data. Gradle used workspace TMPDIR; adapter uses outside-checkout
  task cache. No product workaround. Initial outside-checkout guard failure was
  corrected by moving test location, not weakening the guard.
- Local evidence: `state-client-build/device-readiness-receipt/` (JUnit XML/logs,
  entry hashes/diff, task doc additions) and `state-client-build/android-canary55-receipt-e817380/`
  (clean source inventory, build logs, unsigned/signed verification, APK).
- Source/secret guards and `git diff --check`:PASS. No keys, private state, APK or
  local evidence committed. Existing attempt14 artifact pins unchanged.

## Что дальше — только отдельно разрешённая работа

Не устанавливать автоматически и не повторять PROV-1. Старые accepted HTTP/sync/
readiness archives не содержат новый API; нужны отдельно построенные, проверенные
и pinned совместимые bundles/nginx/migration перед будущим deployment. Старая
server API даст ACK404/UNKNOWN, не разрушая local readiness, но это не acceptance.
В будущем old18084 сохраняется до настоящего app READY ACK; rollback routing
должен быть доказан перед остановкой candidate, authority history сохраняется.
Этот task ничего не разворачивал, поэтому production rollback не требовался.
Отдельно остаются physical in-place install55, real owner import ACK, restart,
restricted rehearsal, Chrome/TLS/DNS/TCP/leak/fail-closed и fresh normal health.
Никакие прежние production gates/expired authority не считаются свежими.
