# Клиенты по платформам

[Paired delivery diagnostics04.10](../releases/2026-10-04-paired-delivery-diagnostics.md),
source-only: `carrier/sessiontrace/delivery.go` задаёт bounded flow/fragment schema,
`reliablestream` и `telemost` собирают состояния, `sessiondiag.Sample` передаёт их
из `wholedevice`/`roombroker`. Android `RestrictedDelivery`/`RestrictedTrace` сохраняют
last8+first_failure через существующий `DiagnosticRing`; `scripts/correlate_restricted.py`
сопоставляет flow и message IDs без утверждения одновременности/причины потери.
Тесты: `delivery_test.go`, `diagnostic_test.go`, `reliable_framing_test.go`,
`RestrictedDeliveryTest`, `RestrictedTraceTest`, `test_restricted_correlation.py`.
Старые экспорты совместимы; новая диагностика ещё не установлена на owner63/gateway.

[Restricted session terminal diagnostics03.10](../testing/restricted-session-diagnostics.ru.md):
локальный patch, не rollout; общая safe-проекция Go/native/Android, первая причина
разрыва и session tag, без изменения transport/auth/retry policy.

[Общая карта](README.ru.md). Платформы используют общие форматы, но не один общий runtime.
Положительный Python/C# тест не доказывает работу Android VPN или Windows broker.

## Android

Private58 hook fix03.10 supersedes the earlier build-only notes: debug-source
`DiagnosticLauncher` resolves the installed package launch Intent and bounds missing
launcher/start exceptions. `OrchestratorDiagnosticActivity` checks durable deny-flag
commit/readback and writes fsynced ON/OFF evidence. No main transport source changes.
`src/testDebug/.../DiagnosticLauncherTest` has5 JVM cases; Python source/manifest
contracts and opt-in `test_android_acceptance_hook_device.py` verify private58 ON/OFF
and fresh-process OFF. Public Friends manifest has no diagnostic Activities.
Private58 installed; READY persisted. Physical CONNECT blocked on MIUI input permission,
not hook navigation; override OFF. [Current evidence](../releases/2026-10-03-5n-physical-hook-fix-and-rehearsal.ru.md).

Physical acceptance03.10: private57 is built/signed only from exact committed0615953
source with an isolated Gradle init overlay: Friends debuggable and existing
`src/debug` Activities/manifest. `OrchestratorDiagnosticActivity` sets existing
`deny_awg/deny_wg/deny_tcp`; `AutomaticConnection` emits structured events and treats
those normal candidates as unavailable. Restricted implementation remains unchanged.
No tracked public build/runtime source change. Not installed/enabled; Redmi still55
because credential reload prerequisite failed and was rolled back before Android work.
218 unit tests/lint/APK checks PASS. [Current checkpoint](../releases/2026-10-03-5n-physical-restricted-rehearsal.ru.md).

Attempt15,02.10: same-source private canary55 installed in place over54 and final
hash/package/signer verified; no Android source change/reset. App challenge503,
no authoritative READY/ACK observed; restricted server rollout rolled back. UI
gestures did not gate acceptance. Phone remains55; no public/FIELD release.
[Attempt15](../releases/2026-10-02-5n-prov1-attempt15.ru.md) supersedes older installation
checkpoints below; restart/rehearsal/user-traffic acceptance remains unperformed.

5N-DEVICE-READINESS-RECEIPT,02.10: `ReadinessProduct` separates import/evaluate/publish;
`RestrictedCache.importProduct/evaluate` validates native credentials/directory, atomic
vault readback and the same `usable()` used by `RestrictedTunnelEngine`. Safe v1
`ReadinessImportResult` goes to private AtomicFile `ReadinessReceiptStore`, then the
existing `FriendsAccessAndroid`/`FriendsReadinessProtocol` HTTPS proof/ACK path.
`FriendsRestricted` revalidates encrypted state once per process before normal prewarm;
previous receipt is never a readiness authority. BuildConfig supplies the app version.
`control/friends/readiness_receipts.py` binds challenge/fetch/ACK, and packaged
`--readiness-ack` read-only server inspection feeds `OwnerProduct.observe`; UI is
supplemental. No exported component, signing API or app private-state dump.
Private canary55 built/signed only, not installed; [evidence/schema](../releases/2026-10-02-5n-device-readiness-receipt.ru.md).

Attempt14,02.10: private canary54 installed in place on owner Redmi, APK/signature
verified; no Android source change. Server gates PASS, but owner readiness UI
observation failed (ADB input255); correlated import/cache acceptance unverified.
Server restricted stack rolled back, phone stays54; no public/FIELD release.
[Exact outcome](../releases/2026-10-02-5n-prov1-attempt14.ru.md).

5N-ANDROID-CANARY-BUILD,02.10: clean-source `4bb53b0` now packaged as private
canary54/code54 with the product helper/diagnostics below. Full Gradle PASS,
204 app JVM tests,149 separate overlapping control JVM tests, lint0errors/37warnings;
fresh exact arm64 JNI and existing beta signature. At build gate: not installed/distributed.
No Android source changes in this build gate. Stale ignored Chaquopy venv repaired,
not a build-script defect. [Artifact and setup](../releases/2026-10-02-5n-android-canary-build.ru.md).

5N-OWNER-PROOF-HANDOFF,02.10: normal product prewarm remains in `FriendsRestricted`.
`FriendsReadinessProtocol` holds the unchanged challenge/sign/fetch sequence for
JVM testing; `FriendsAccessAndroid` remains its normal HTTPS transport. The
package-private `OwnerPrewarmReceipt` adds random request correlation IDs and
allowlisted result/revision/expiry diagnostics, never a signing/export endpoint.
Native validation plus `RestrictedCache.accept` still precedes import success.
[Server/product acceptance split](../../deploy/friends/restricted/OWNER_PROOF_HANDOFF.md).
Source only: no new APK/version/install; physical proof is not supplied by local tests.

Попытка №2,01.10: приватный `0.1.18-canary53-prov1`/53 из `e808f50` полностью
собран: fresh arm64 JNI,194 JVM tests PASS, lint0errors/36warnings. `.friends`,
non-debuggable, прежняя beta-подпись; совместимость с установленным field52
проверена. Установки/публикации нет, это не финальный FIELD artifact. Physical
prewarm не начат из-за RU runtime import failure; restricted stack откачен.
[Хэши и provenance](../releases/2026-10-01-5n-prov1-production-restricted-provisioning.ru.md).

5N-PROV-1 local-only: `FriendsAccessAndroid.restrictedReadiness` authenticates with
existing `ControlIdentity` proof, no pre-existing Family TLS. `FriendsRestricted`
provides single-flight bounded prewarm; `RestrictedCache` validates/rejects replay
and retains old state on failure; `RestrictedVault` commits one Keystore-encrypted
AtomicFile. `FriendsReadiness` exposes only redacted production state.
The04.10 local early-refresh patch keeps the persisted300s attempt cooldown but no
longer suppresses foreground refresh merely because cached credentials are unexpired.
`ReadinessRefreshTest` covers scheduled challenge/fetch/import/ACK from retained valid
old state; native/Keystore/physical acceptance is a separate release gate.
[Scope and rollout status](../releases/2026-10-04-readiness-early-refresh.md).
`NativeRestricted.validateDelivery/beginReady` bridge to
`carrier/wholedevice/provisioning.go`: root delegation/X509/CRL/BOOT-1 checks and
in-memory TLS key from existing identity. `RestrictedTunnelEngine` uses that bundle
for real `.friends`; legacy fixture-file path remains diagnostic-only.
JVM tests: `RestrictedCacheTest`; native tests: `wholedevice/provisioning_test.go`.
5N-TIME-COMPAT: shared `tests/vectors/bootstrap-timestamps.json` exercises native
directory parsing and JVM `Instant` replay ordering; Go canonical UTC serializers
are in `carrier/bootstrap/directory.go`. Java equal-issued conflict guards unchanged.
Real Keystore/process-restart/production-control validation still requires the
authorized deployment and in-place private APK; no new APK shipped in this gate.

MVP Auto: `ConnectivityOrchestrator` — pure deterministic policy/tests;
`RestrictedRecovery` — pure allowlisted native first-failure classification;
`RestrictedRecoveryTest` + `ConnectivityOrchestratorTest` cover retry exhaustion,
one fresh attempt, cleanup/denial/cancellation and owner AUTH race. Unknown causes
stay terminal; runtime adapter samples evidence once before cleanup.
`AutomaticConnection` — adapter/lifecycle host на existing ConnectionService worker;
`AutomaticVpnOwner` — full-route guard и TUN handover в existing TcpVpnService;
`AutomaticNormalEngine` — existing AWG JNI/NativeTcp без второго service owner.
`RestrictedTunnelEngine` поддерживает shared-owner mode; native → `wholedevice.OpenCached`
получает свежий BOOT-1 descriptor без fake control probe. Main/Friends default Auto,
manual diagnostics и managed recovery сохранены. Private bounded events не содержат
URL/destination. [Точный scope/physical ledger](../releases/2026-09-30-mvp-connectivity-orchestrator.ru.md).

5N.6 diagnostic binding: `ConnectionService` → `RestrictedTunnelEngine` → existing
`TcpVpnService` → `NativeRestricted` → `pilot/android-restricted/packet` (existing
Xray/gVisor TUN engine) → shared `carrier/wholedevice` → existing Mux/Family DNS.
`carrier/underlay` защищает HTTPS/WebSocket/ICE/media/provider DNS до TUN через
тот же VpnService.protect. Dedicated readiness предшествует TUN capture; failure
держит TUN и не включает direct fallback. Debug-only activity использует реальный
permission flow, отдельного VPN owner нет. Normal AWG/TCP factory не заменена.
Физический результат/ограничения — [EU-6 report](../releases/2026-09-30-webrtc-eu6-android-full-device.ru.md),
сборка/entry points — [runbook](../../pilot/android-restricted/README.md).

5N-BOOT-1: `carrier/bootstrap` — directory/cache, one-lease carrier envelope,
Family-authenticated control-only protocol и separate seed manager.
`carrier/cmd/bootstrap-broker` — disposable mTLS preparation + seed process;
`carrier/cmd/telemost-binary/bootstrap.go` — explicit refresh/recover diagnostic
path, затем existing dedicated Family binding/Mux. `BootstrapMode`/`ProbeService`
дают только mode, guarded control endpoint и no-backup cache path; второй Java
network stack не создаётся. [Runbook](../../carrier/bootstrap/README.md) ·
[Report/physical PASS](../releases/2026-09-30-webrtc-5n-boot1-bootstrap.ru.md).

Изолированный **5N.2 test endpoint** находится отдельно:
`clients/android/telemost-runtime` (`ProbeActivity` → `ProbeService` → `NativeRun`),
`pilot/android-telemost/{build,live}.py` — только build/operator wrappers.
Он запускает **тот же** `carrier/cmd/telemost-binary` как Android PIE из nativeLibraryDir,
а не новый Java WebRTC/JNI stack. Не импортирует `FriendsActivity`/`ConnectionService`,
не меняет production Transport selection, `pilot/android-{tcp,awg}` или Chaquopy.
Текущий product TCP protect hook остаётся в `NativeTcp`/`TcpVpnService` и Go TCP runtime;
test carrier sockets **не protected**, будущий bridge описан в
[отдельном runbook](../../clients/android/telemost-runtime/README.md).

5N.4 single TCP: `carrier/tcpforward` содержит wire/policy/client/gateway; concrete
`familysession.Session.ClaimTCP` допускает одну сессию правильной роли после auth.
`carrier/cmd/telemost-binary/tcp.go` — echo/HTTPS/fault test client и5s telemetry;
`pilot/android-telemost/tcp_acceptance.py`/`tcp_fixture.py` — disposable fixtures,
exact validation и cleanup. APK code3/5N.4-test-only, app-private tcp.input; product
UI/VPN runtime не меняются. [Evidence](../releases/2026-09-28-webrtc-eu4-single-tcp.ru.md).

Корень: [clients/android](../../clients/android/). Основные Java-файлы в
`app/src/main/java/com/familyconnect/app/`; ресурсы в `app/src/main/res/`, Python bridge
в `app/src/main/python/`. Gradle `app/build.gradle` определяет variant/ABI/version.

| Группа | Главные файлы | Роль |
| --- | --- | --- |
| UI/вход | FriendsActivity, MainActivity, FamilyApplication | Friends UI и отдельный managed/pilot экран, lifecycle |
| Friends | FriendsAccessAndroid, FriendsIdentityVault | API/доступ и защищённая identity; не подменять ControlIdentityVault |
| VPN | ConnectionService, TunnelEngine, Transport, ProfileStore | Один service worker/engine, профили, старт/остановка |
| Проверка профиля | ProfileValidator, AwgParameters, TcpProfile | Строгий разбор, ограничения, AWG/REALITY параметры |
| TCP и health | TcpVpnService, VpnHealth, ControlTrafficHealth | Туннель и проверка связи; connect не равен полезному трафику |
| Managed protocol | ControlProtocol, ControlProfiles, ControlIdentity | Signature/decrypt/schema и локальные ключи |
| Managed state | ControlJournal, ControlJournalVault, ControlTransaction | Durable state, apply/rollback/recovery, local selection |
| Managed boundary | ControlApplication, ControlOperations, ControlMutationGate, ControlStartup | Owner, недопуск параллельных ручных мутаций, восстановление |
| Managed ingress | ControlEnrollment*, ControlRnsAndroid, ControlTrust | Enrollment, RNS carrier и закреплённое доверие |
| Обновления | AppUpdate, AppUpdateUi, UpdateApkProvider | Проверка/получение APK, интерфейс установки |
| Chat | ChatActivity, ChatDeliveryService, Chat* | См. отдельную карту мессенджера |

MainActivity/ConnectionService теперь подключены в исходниках к selectGateway через
ControlSelection (admission/recovery/reconnect); JVM tests и Java compile прошли,
device acceptance ещё нет. Preferences — кэш выбранного ID, journal authoritative.
AWG3.1 managed capability default false. Local journal schema2 не равен wire schema2.
Friends/native AWG3.1 уже существовал отдельно. Детали — [managed map](../managed-control-code-map.ru.md).

Проверки: `app/src/test` (JVM), `control-tests` (изолированная Java suite),
`app/src/controlTest` (общие runners), `app/src/androidTest` (устройство/эмулятор).
`ControlSelectionRuntimeTest` проверяет selection/reopen/rollback на настоящем
encrypted journal, но с имитацией VPN; только пустой debug pilot с явным
`fc_disposable=true`. Тест прошёл на Redmi Note 9 Pro/API31; также прошли protocol/JSON
и Python/RNS tests. [Результат](../releases/2026-09-24-android-selection-device.ru.md). `chat-python.gradle` принимает
`-PfcBuildPython=/path/to/python3.10` для сборки совместимого Python payload.
[Сборка, ограничения и порядок запуска](../releases/2026-09-24-android-selection-runtime-preparation.ru.md).
Использовать соответствующий Gradle variant; не устанавливать test-signing APK поверх
пользовательской установки с другой подписью. Engine/dependency payload в generated
каталогах не редактировать как собственный Java-код.

## Linux/desktop Python

| Модуль | Входы/файлы | Граница |
| --- | --- | --- |
| GTK UI | clients/desktop/app.py, friends_ui.py, friends_qr.py | GTK4/libadwaita, UI события и отображение |
| Backend | clients/desktop/backend.py | Profile/import/connect/disconnect, shared operation ownership |
| Профили | clients/desktop/profile_config.py | WG/AWG/REALITY parser, strict fields и локальная материализация |
| Friends owner | provisioning/friends_owner.py, friends_application.py | Сеть/хранилище/применение вне UI thread |
| Обновления | clients/desktop/updates.py | Signature/version/floor отдельно от VPN config |
| Привилегированный слой | clients/linux/awg-helper.py, tcp-helper.py, control-route-helper.py | Root-side проверка операций и маршрутов |
| Установка | clients/desktop/install-linux.sh, clients/linux/install-*.py и install-*.sh | Изменяет host; не запускать как unit-test |

Checks: `clients/desktop/tests`, `layout_check.py`, `friends_ui_check.py`,
`recovery_check.py`; окружение GTK/display и необходимые команды описаны в
[clients workflow](../../.github/workflows/clients.yml). GUI CI overrides не переносить
в настройки установленного приложения. Reference managed runner — `provisioning/runtime.py`.

## Windows

Корень: [clients/windows](../../clients/windows/).

| Слой | Файлы | Ответственность |
| --- | --- | --- |
| Вход/экран | Program.cs, MainForm.cs, SingleWindowApplication.cs | CLI режимы, WinForms, одна пользовательская сессия |
| Broker | Broker.cs, Wire.cs, Native.cs | Привилегированные операции, named pipe и проверка доверенной службы |
| Защищённое состояние | Store.cs, FriendsIdentityVault.cs, FriendsConfigurationVault.cs | Права/DPAPI/platform storage |
| Общие форматы | Core/Activation.cs, FriendsAccessClient.cs, FriendsCatalog.cs | Активация, HTTP proof, каталоги |
| Managed verifier | Core/ControlProtocol.cs, ControlProfiles.cs, ControlIdentity.cs | Проверка конфигурации; не готовый Windows managed journal |
| VPN | Core/AwgProfile.cs, Core/TcpProfile.cs, Core/TransportSequence.cs | Профили и порядок попыток |
| TCP runtime | TcpEngine.cs, TcpSession.cs, TcpNetwork.cs/.ps1, TcpHealth.cs | Процесс/сессия/маршруты/health |
| Updates/installer | Updates.cs, build.ps1, setup.iss | Подписанный отдельный каталог Windows и immutable installer |

Checks: `Tests` для контрактов, `BrokerTests` для broker и native workflows
`windows-control.yml`, `windows-awg.yml`, `windows-tcp.yml`. C# Tests запускаются и
на Linux, но DPAPI/Windows runtime там пропускаются. Native установку/права/откат
подтверждать на Windows. Не обходить broker прямым вызовом процесса из GUI.

## Перед изменением общего формата

Сначала изменить контракт и подписанные test vectors, затем все три verifier/parser,
добавить capability/version gate и native application tests. Не считать одинаковые
имена полей доказательством одинаковой поддержки. Старые версии должны отказывать
без частичного применения и без молчаливого удаления параметров защиты.

`ControlServiceAdmissionRuntimeTest` — три подготовленных проверки реальной Android-службы:
invalid gateway, отсутствие enrollment/повтор, отмена permission callback в MainActivity.
Только пустой debug `.pilot` с `fc_disposable=true`; проверяет отсутствие новых
managed secrets/profiles и освобождение owner/завершение службы. Сборка прошла,
выполнение на устройстве пока не подтверждено; системный VPN dialog и туннель не проверяются.
[Состояние и запуск](../releases/2026-09-24-android-service-admission.ru.md).

## XHTTP/TLS: checkpoint5.3в

[Полная карта и ограничения](../xhttp-implementation.ru.md).
Python `profile_config.py` и Android `TcpProfile`/`pilot/android-tcp/tcp-android.go`
понимают строгий XHTTP/TLS профиль; Windows `TcpProfile` — activation version2,
issuer `scripts/activate_windows_tcp.py`. Shared fixture `windows-xhttp-v2.json`.
Origin/Nginx renderer: `scripts/xhttp_gateway_config.py`; сетевые проверки:
`scripts/check_xhttp.py`, `pilot/android-tcp/host-check/`, workflow `xhttp.yml`.
Friends catalog и managed vless-reality schema явно не допускают подмену новым типом;
выдача, UI, fleet и реальные белые списки ещё не интегрированы. Локальные тесты
не означают rollout; версии публичных приложений прежние.
