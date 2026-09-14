# Android: автоматический RNS carrier и ACK — 2026-09-14

После регистрации кнопка «Подключить через Reticulum» запускает recovery и отдельный
RNS worker. Challenge подписывается purpose-separated fetch proof ключом устройства
в Java. Encrypted signed envelope проходит существующий ControlIntake/verifier,
service owner, apply/health/rollback и durable journal. ACK удаляется из outbox только
после ACK_STORED. Повторы выполняются через60 секунд после предыдущего обмена;
недоступность relay не выключает работающий VPN. Disconnect/revoke/lease expiry
отменяют carrier. Автостарт после OS boot/убийства процесса не добавлен.

TCP socket до connect привязывается к Android network с NOT_VPN/INTERNET; bootstrap
содержит literal IP. Private device/WG keys остаются в Java vault. Python получает
публичные данные, proof, encrypted envelope и подписанный ACK. Отдельная внутренняя
RNS transport identity находится в noBackup/rns-control. Нет shared instance,
listener или transport mode. Link/interface закрываются после обмена; runtime
остаётся singleton процесса, RNS signal handlers не меняют Android lifecycle.

## Версии и bootstrap

Chaquopy16.1.0, Python3.10, RNS1.5.1, pyserial3.5, AGP8.9.2, Android compile/target35,
min26. Pip --no-deps использует internal crypto без PyCA Android wheels. Выбраны
armeabi-v7a/arm64-v8a/x86/x86_64. CI получает Python3.10. Лицензии Reticulum, PySerial,
Chaquopy добавлены в assets/control-licenses.

Public rns-relay.json указывает Amsterdam pilot186.246.45.246:4242 и pinned provider
public key, отдельный от config signing root. Provider reference:
e504e0ef76a2b3bcc3f0c5add0760ff3. SHA256 asset:
9305cd3486e4e7c5a7fc881a292d3824653a0d6d5c4a5559272baa98c275b7bb.
Product enrollment не публикует envelope в отдельное состояние ControlRelay:
оператору ещё нужно зарегистрировать Android recipient и выдать конфигурацию.
Это не готовая доставка на любой Android.

[Chaquopy versions](https://chaquo.com/chaquopy/doc/current/versions.html),
[Reticulum usage](https://reticulum.network/manual/using.html).

## Проверки

- aapt2 resources и javac main sources с реальным Chaquopy API jar passed;
  использованы cached engine classes, Android35/Java17, не полный native build.
- 98 Java tests passed: прежние91 плюс7 carrier tests, включая proof vector,
  challenge audience/TTL, commit/ACK, отказ ACK с сохранением outbox/VPN,
  outage, cancel и размеры сообщений.
- tests/test_android_rns_transport.py:2 passed за2.87s. Настоящие loopback RNS peers:
  fetch revision1, signed ACK/duplicate, отмена, новое соединение и revision2.
  Envelopes проверены reference Python ConfigVerifier. Второй сценарий использует
  internal crypto как APK; первый — обычный provider. Только disposable test keys.
- Gradle generateDebugPythonRequirementsAssets, generateDebugPythonSourceAssets,
  generateDebugPythonMiscAssets: BUILD SUCCESSFUL за28s,6 tasks. Упакованы Python
  source, requirements и runtime assets выбранных ABI. Контейнер gradle8.11.1-jdk17,
  Python3.10.12 + python3-distutils; пакеты host не менялись.
- Добавлен ControlRnsRuntimeTest (import/version/internal provider/init), пока без
  запуска Android instrumentation.

Проверки выявили и исправили регистрацию TCP interface/IFAC и stale path при
reconnect: удаляется только path pinned destination под RNS lock. Первый packaging
запуск выявил отсутствие distutils; после установки в контейнер и выбора отдельных
asset tasks сборка прошла.

Воспроизведение RNS в provisioning environment с RNS1.5.1:
`python -m pytest -q -p no:cacheprovider tests/test_android_rns_transport.py`.
Требуются loopback sockets. Для Python assets выполнить три Gradle задачи выше.

## Применение и остаток

Изменения исходников локальные: commit/push, CI, APK, установка, live enrollment и
relay publication в этом шаге не выполнялись. Версия0.1.2-beta03/code3 сохранена;
серверы и release signing root не менялись.

Следующее: полный native APK build, ABI/16KB/lint, instrumentation на Android,
embedded runtime cold start, Network.bindSocket при активном VPN, смена сети,
process-death и durable ACK recovery. Затем опубликовать конфигурацию именно для
зарегистрированного тестового Android и проверить receive/apply/health/ACK/reconnect.
Minimum client version должна соответствовать выпускаемой версии: обхода нет.
После acceptance — новая неизменяемая версия и существующий подписанный release.

Rollback до выпуска: отменить только изменения этого шага, сохранив предыдущие
intake/enrollment/journal изменения. Carrier останавливается отключением. Не удалять
app data/vault/outbox. Downgrade APK требует проверки совместимости состояния и
anti-rollback policy; готовый безопасный downgrade не заявлен.
