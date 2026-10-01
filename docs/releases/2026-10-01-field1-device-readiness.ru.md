# LOCAL FIELD-1 device readiness — 01.10.2026

## Subsequent local implementation — deployment authorization required

После user clarification 5N-PROV-1 implemented locally; existing identity proof
может получить public Family TLS/BOOT-1 через production Friends API после rollout.
См. [реализацию/tests/controlled deployment](2026-10-01-5n-prov1-production-restricted-provisioning.ru.md).
Python95/JVM193/Go race+vet/fresh JNI PASS; это **не** новое physical evidence.
Телефон/API production не изменялись, APK не собирался/не устанавливался.
Last-observed actual Friends: Identity PRESENT, normal PRESENT_VALID,
restricted/BOOT-1 ABSENT; READY/restart/rehearsal pending authorization.
Field52 остаётся readiness-only, не final FIELD artifact. Вся история ниже сохранена.

## Subsequent 5N-PROV-1 audit — evidence preserved

Отдельный [production integration audit](2026-10-01-5n-prov1-production-restricted-provisioning.ru.md)
подтвердил gap Friends versus ProductStore и конфликт literal room-URL запрета с
BOOT-1 v1 live seed. Результат **BLOCKED до runtime implementation**, не новый
physical test и не deployable change. Телефон не трогали, prewarm/rehearsal не
выполнены. Следующее историческое evidence остаётся без переоценки.

Starting HEAD: `26447902137735ac7633f92ba6673395bae078fa`.
Это LOCAL readiness, не Krasnodar FIELD-1. Предыдущий
[BLOCKED preflight](2026-10-01-field1-local-preflight.ru.md) сохранён: update PASS,
private identity/cache UNKNOWN. Повторного расследования установки нет.

## Найденная граница продукта

Friends activation использует существующий `FriendsIdentityVault` (AndroidKeyStore,
encrypted AtomicFile в no-backup) и authenticated `/friends/device/status`.
Normal provisioning хранится отдельно в `FriendsConfigurationVault`: signed
normal catalog, device binding, AWG/TCP materialization. Readiness читает и проверяет
существующие записи, не создаёт identity и не вызывает activate/configuration.

BOOT-1 `wholedevice.OpenCached` требует private Family TLS profile
`no_backup/restricted/family.json` и `bootstrap.json`. `wholedevice.Refresh`
уже существует: mTLS GET `/v1/bootstrap/directory`, strict validation, atomic
0600 write/fsync/rename, max TTL1h, max4 seeds, Family/gateway binding.
Rejected refresh сохраняет valid cache, identical refresh ничего не переписывает.
Directory **не подписан отдельно**: trust = authenticated Family TLS delivery
и private filesystem; новый signing root не добавлен. Cache содержит bootstrap
seed rendezvous, не live dedicated room descriptor.

Friends `/friends/configuration/{ru,nl}` не выдаёт Family TLS certificate/CRL,
broker endpoint либо BOOT-1 directory; `/friends` API не имеет BOOT-1 delivery.
Предыдущая isolated acceptance использовала ProductStore-derived disposable
Family credentials; это не provisioning production Friends installation.
Нет подтверждённого production bridge между Friends identity и этой выдачей.
Добавление UI refresh без такого trust/provisioning не исправляет проблему.
Копирование diagnostic profile, mint второй identity или production deployment
не выполняются. OAuth не нужен для read-only readiness и в APK не включается.

## Минимальная диагностика

Internal Settings → «Готовность подключения»: decrypted Device Identity presence,
validated normal provisioning, restricted provisioning/cache metadata через JNI
и те же BOOT-1 validators. Metadata-only output, отсутствие поля не означает
ABSENT; read/validation errors остаются UNKNOWN/UNAVAILABLE/INVALID.
Отдельная explicit кнопка проверяет normal Family access существующим bounded
authenticated status request. Это не доказательство restricted entitlement.
Никаких новых exported components, logcat dumps, raw proofs/keys/URLs, фоновых
refresh retries, room creation или сетевых изменений. Refresh честно
NOT_ATTEMPTED: production delivery не настроен.

## Результат: FIELD-1 DEVICE READINESS = BLOCKED

Readiness code commit/source: `9c821520f27111c637221b05a25d079e2b4c177e`.
Redmi Note9Pro, Android12, arm64-v8a; единственный authorized USB device.
Normal environment: Wi-Fi OFF, cellular ON, validated cellular network, VPN нет.

| Проверка actual non-debuggable Friends | Результат |
| --- | --- |
| In-place beta51 → private field52 | PASS; только `adb install -r` |
| Activation/UID/firstInstallTime | сохранены, reactivation не было |
| Decrypted Device Identity | PRESENT |
| Normal provisioning | PRESENT_VALID (existing signed catalog/device binding/TCP profile) |
| Normal live entitlement status | UNKNOWN; bounded authenticated status не подтвердил ACTIVE, причина не установлена |
| Restricted Family TLS provisioning | ABSENT |
| BOOT-1 first in-app observation | ABSENT; ранее было UNKNOWN, не ретроактивный ABSENT |
| BOOT-1 final | ABSENT |
| Structural validity / expired | N/A — файла нет (UI UNKNOWN), seeds/TTL unavailable |
| Locally usable by Orchestrator | false |
| Refresh/prewarm needed | yes; NOT_ATTEMPTED: отсутствуют restricted provisioning и production delivery |
| Process stop/reopen | PASS, Identity/normal provisioning/activation остаются; cache остаётся ABSENT |
| Ready-cache restart persistence | NOT PROVEN: нет READY cache |
| Local automatic restricted rehearsal | NOT RUN / BLOCKED prerequisite; не failed network attempt |
| Restricted Chrome/DNS/concurrency/leaks/UDP/IPv6/underlay | NOT RUN; leak counts не измерены, не заявляются нулевыми |

Normal entitlement UNKNOWN не превращается ни в revoked, ни в ACTIVE на основании
local activated preference. Процесс запускается штатно; startup crash не наблюдался.
No uninstall, pm clear, reset, reactivation, new identity, cache manufacture или
diagnostic-package migration. BOOT-1 store не создавался даже при inspection.
Его отсутствие теперь установлено кодом самого production package, не root/run-as.

## Private APK (readiness, НЕ принятый FIELD-ready artifact)

- Path: `/tmp/fc-readiness-9c82152/artifacts/FamilyConnect-readiness-field52-9c82152-arm64.apk`.
- SHA256: `604f06722a702475a03dd5aec8bff1f99c82706c65dc5fb0e92e400f45a0756a`.
- Size: 49564539 bytes.
- applicationId: `com.familyconnect.app.friends`, non-debuggable.
- versionName/code: `0.1.18-field52-readiness` / 52; external field Gradle init
  override only, repository/public beta51/code51/catalog/invitation page unchanged.
- Certificate SHA256: `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
- Existing beta signer/memfd flow; signing secrets не выводились/экспортировались.
- Update-compatible with published beta51: yes, физически установлен поверх
  activated FIELD beta51 той же подписью. Uninstall required/performed: no/no.
- Installed APK readback SHA равен artifact SHA, package/version/certificate verified.
- Readiness included: yes. Product prewarm included: **no** — нет доверенного
  production issuance/delivery; не добавлена ложная кнопка refresh.

Fresh source native builds повторены, старые JNI blobs не использовались.
Go1.26.1, NDK27.2.12479018; pinned
Xray`d2758a023cd7f4174a5a5fa4ff66e487d4342ba0`.
Compiler/module cache переиспользован, `.so` заново получены existing builders
из code commit9c82152; normal manifest фиксирует source revision.

- `libfc-awg.so`: `ca54c9638ef4632e4f5bc935f48b4a585e42b67f4878e61135915db038d574b8`.
- `libfc_restricted.so`: `81cdb878cc8c543db75e828ded3dfc3d978d4732a8151ae8ec938a0a1258ac7f`.

Actual APK native hashes совпадают с fresh outputs и manifests. Arm64 only;
restricted manifest по-прежнему diagnostic_only (не public rollout claim).
Package parse, zip integrity/alignment16K, v2/v3 signature и recursive artifact/
secret scan PASS. OAuth exact-value check и token/URL/private-key patterns:
0 findings. Единственный старый bytecode false-positive — pinned trusted beta51
stdlib `Basic ` scheme, не credential (та же narrow path/hash exception).
No OAuth, live room URL, private fixture, forced-failure default, adb-reverse proxy.

## Tests / cleanup / remaining work

- `go test -race ./bootstrap ./wholedevice`: PASS; cache expiry/future issuance,
  rejected refresh preservation, no inspection writes и metadata redaction.
- `go vet ./bootstrap ./wholedevice`: PASS. Android JNI compile PASS.
- `:app:testFriendsUnitTest`: 188 tests, 0 failures/errors/skips, включая
  Orchestrator/lifecycle и3 новых readiness redaction tests.
- Focused Python contracts/provenance/bootstrap/public-source/signing:50 PASS,
  1 optional vault integration SKIP. Lint0 errors/37 existing warnings.
- Первый packaging attempt обнаружил duplicate old generated Java classes;
  external init исправлен на exact fresh sourceDirs. Final assemble/tests/lint PASS.
- Docs/public-source guard, targeted secret scan, `git diff --check`: PASS.
- PERF и long physical acceptance не запускались.

Temporary UI-only probe читал Accessibility tree только в памяти, выводил
whitelisted metadata; raw XML, credentials, files и room URLs не сохранялись.
Probe удалён с устройства. MIUI отказал Back injection; dialog закрыт обычным
process restart, launch PASS, оставлен главный экран. VPN не запускался;
forced-failure state не добавлялся; Wi-Fi0/cellular1 не менялись. APK/activation/
normal provisioning сохранены. Private runtime artifacts на laptop не извлекались;
только public APK/build outputs и sanitized receipts в указанном `/tmp` каталоге.

Для продолжения требуется отдельный production integration gate: authenticated
issuance/provisioning Family TLS и trusted broker/bootstrap delivery для **existing**
Friends identity, существующий BOOT-1 seed service, затем normal prewarm/restart
и local rehearsal. Просто CONNECT/переустановка не заполняют cache. TTL максимум
1h и lifetime seed важны: сохранение файла не гарантирует readiness после shipment.
В этой задаче production deployment запрещён, такой gate не запускался.

Rollback: не uninstall/downgrade/clear. При необходимости собрать отдельно
авторизованный same-signature corrective APK с code>52; старый public beta51
не является обычным installer downgrade поверх52. Public metadata не менялась.
Существующая исходная FAIL/последующая PASS Orchestrator история не изменена.
Push: no. Production configuration/deployment changed: no. FIELD-1 started: no.
