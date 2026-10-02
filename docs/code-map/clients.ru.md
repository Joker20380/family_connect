# Клиенты по платформам

[Общая карта](README.ru.md). Платформы используют общие форматы, но не один общий runtime.
Положительный Python/C# тест не доказывает работу Android VPN или Windows broker.

## Android

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
