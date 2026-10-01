# LOCAL FIELD-APK PREFLIGHT — 01.10.2026

**LOCAL FIELD-APK PREFLIGHT = BLOCKED.** Установка поверх beta51 и базовый UI smoke
успешны. Блокер — невозможно подтвердить private Identity/provisioning и usable
BOOT-1 cache доступными read-only средствами недебажного production Friends APK.
Это не Krasnodar FIELD-1, не restricted acceptance и не networking development.

## Устройство и состояние до обновления

Первый ADB опрос не видел телефон; повтор обнаружил ровно один авторизованный
USB Xiaomi Redmi Note9Pro, Android12, arm64-v8a. Серийный номер не выводился.
Приложение `com.familyconnect.app.friends`, versionName`0.1.18-beta51`, code51.
Прочитанный installed APK побайтно совпал с immutable публичным beta51:
SHA256`79a2d28667332ea442eae1b895b4fc632b52734cbed1e75bd95f32b7175ad366`.
Сертификат проверен apksigner, совпадает с FIELD APK. Активного TcpVpnService
не было. Wi-Fi0/cellular1/airplane0 оставлены без изменения.

Штатный экран настроек до обновления показывает «Пригласить друга», а не
«Получить доступ»; запроса исходного приглашения нет. По текущему коду это
подтверждает сохранённый local activated preference, не новый server-side auth.
Private state в части application-visible activation/preferences существует.
Наличие private Device Identity, provisioning/entitlement и bootstrap cache
напрямую не установлено. `run-as` отклонён как non-debuggable; существующей
target instrumentation нет. Root/debug доступ не включался, test APK не ставился.

## Проверка APK и in-place update

FIELD APK не пересобирался:
`/tmp/fc-field1-build-2644790/artifacts/FamilyConnect-FIELD1-2644790-arm64-beta51.apk`.

- Source:`26447902137735ac7633f92ba6673395bae078fa`.
- APK SHA256:`f0a625c8e8485980cf2f9bc1d5577881b5e59393c86cedfdc92f4e3c7d994f41`.
- Certificate SHA256:`67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
- aapt package/version/non-debug/manifest checks PASS; signature v2/v3 PASS.
- Arm64 normal JNI:`3ce14114902356f796017b2557ef6991543a8e53b664c6143f9c6382a4a969c5`.
- Arm64 restricted JNI:`81f6c071f5a1e177287bafd80f949975d4a3f74fd5c91d9e626a6321b2a3130c`.
- Packaged bytes совпадают с fresh build; secret/artifact scan PASS.

Выполнен только `adb -d install -r <FIELD APK>` (`-d` здесь selector USB device
перед install, не downgrade flag). Android ответил Success. Signature/version
ошибок нет; uninstall, pm clear, reset, enrollment и diagnostic-state migration
не выполнялись. Installed APK повторно считан: exact FIELD SHA и certificate PASS.
UID и firstInstallTime сохранились; lastUpdateTime изменился. Package/version
остались `.friends`/beta51/code51. APK оставлен установленным.

## После обновления и границы сохранения

| Проверка | Результат |
|---|---|
| In-place install |PASS|
| UID/firstInstallTime |сохранены|
| Local activated state UI |yes, до/после «Пригласить друга»|
| Reactivation prompt / новая активация |нет / не выполнялась|
| Полное содержимое private stores сохранено |UNKNOWN; недоступно для прямого сравнения|
| Private Device Identity сохранена |UNKNOWN|
| Provisioning/Family entitlement сохранены |UNKNOWN|
| BOOT-1 cache до / после |UNKNOWN / UNKNOWN|
| BOOT-1 structurally valid / expired |UNKNOWN / UNKNOWN|
| BOOT-1 usable by current Orchestrator |UNKNOWN|
| App launch / startup crash observed |PASS / no|
| Auto в штатном dropdown |PASS, без выбора/смены режима|

Нет оснований превращать UNKNOWN в ABSENT либо заявлять cache валидным.
Seed count/age/expiry/provenance не получены; приватные profile/cache не извлекались.
Установка `-r` и retained activated UI подтверждают package continuity и сохранение
наблюдаемого состояния, но не заменяют проверку ключа и BOOT-1 cache. Local UI не
просит reactivation; fresh activation в restricted сети не проверялась и не нужна
для выполненного обновления. Никакой cache не создавался и не подменялся.

Штатный Friends UI текущего source не показывает BOOT-1 cache health и не имеет
user-facing cache-import/refresh flow. Существующий isolated operator runbook
описывает prior authorized Family activation, authenticated normal mTLS
BootstrapDirectory refresh и сохранение cache в private no-backup directory,
после чего cache переживает restart. Он не даёт права переносить diagnostic
`.orchestrator`/`.eu6` state в production `.friends` или генерировать новый profile
в этой задаче. Перед field нужен отдельно согласованный безопасный способ проверить
и при необходимости provision/refresh именно Friends state при обычной связи.

## UI diagnostics и cleanup

Обычный UIAutomator dump не дождался idle на обновляющемся dashboard. Settings tab
дал safe activation snapshot. Для проверки Auto использован временный UI-only
shell DEX probe через штатный UiAutomationShellWrapper: только accessibility
дерево своего приложения и открытие dropdown, без выбора, app-private files,
network calls или установки дополнительного APK. Первые попытки не разрешили
имя wrapper; после проверки имени в public system jar финальный probe PASS.
Dropdown закрыт Back, temporary jar удалён и отсутствие проверено. Raw XML,
скриншоты, private keys/proofs/room URLs/credentials не записывались и не выводились.

Main process стабилен в ограниченных startup snapshots; launch/settings/home PASS,
crash не наблюдался. CONNECT/DISCONNECT, forced failures, BOOT refresh, VPN/field
acceptance не запускались. Исходные Wi-Fi OFF/cellular ON/airplane OFF сохранены,
TcpVpnService не запущен, телефон оставлен с работающим Friends FIELD APK.
Локальные копии before/after APK удалены после проверки хэшей; original FIELD APK
сохранён. На ноутбуке только sanitized metadata/receipt и публичный UI helper;
private diagnostic artifacts не создавались. Receipt:
`/tmp/fc-local-field-preflight-20261001/receipt.json`.

Изменена только документация. Docs/public-source guard и git diff --check;
никаких runtime rebuild/code tests или production operations. Предыдущие local
ops/build docs сохранены, no commit/push. Public beta51/catalogs/другие платформы
не менялись. Откат не требовался; не удалять активированное приложение.
**MVP Orchestrator PASS не пересматривался; Krasnodar FIELD-1 NOT STARTED.**
