# Android: подготовка проверки selection на устройстве

24.09.2026, этап5.3а. Собраны локальные debug APK приложения и инструментальных
тестов; установка и device acceptance не выполнены. Версии не изменены:
Android0.1.18-beta50/code50, Linux0.2.10, Windows0.2.13.

## Изменения и границы

`clients/android/chat-python.gradle` принимает необязательное свойство `fcBuildPython`:
путь к host Python, соответствующему target3.10. Без свойства остаётся стандартное
обнаружение Chaquopy. Локальная сборка использовала Python3.10.21 вместо3.14;
предупреждение о невозможности компиляции bytecode3.10 больше не появилось.
Общий Gradle-файл используется также isolated chat app; её сборка здесь не проверялась.

Новый `ControlSelectionRuntimeTest` использует настоящие AndroidKeyStore,
ControlJournalVault/AtomicFile и подписанный corpus `control-selection-v1`.
Проверяет pinned manifest/hash/size fixtures, неэкспортируемость AES wrapping key,
commit → select → повторное открытие journal/core → resume → неуспешный health → rollback.
Выбранный ID должен сохраниться, floor/result/outbox и digest не должны меняться.
VPN Host имитируется: тест не проверяет handshake, маршруты, VpnService, UI permissions
или процессный restart. Identity/anchor — публичные TEST ONLY fixtures, capability3.1
включается только внутри теста. Production capability остаётся false.

Перед записью тест требует эмулятор, аргумент `fc_disposable=true`, idle/off,
отсутствие VPN profiles, managed-файлов (включая .bak/.new) и Keystore aliases.
Предусловия расположены до cleanup, чтобы отказ не удалял существующее состояние.
После работы удаляются только созданные journal и его alias. Identity/enrollment
не записываются, plaintext-профили и ключи не выводятся.

## Выполненные проверки

`adb devices -l`: подключённых устройств нет. В проверенных локальных каталогах
SDK/Android не найден готовый emulator/AVD. Инструментальный тест **не запускался**.

Успешна сборка ARM64 pilot и test APK (70 tasks, BUILD SUCCESSFUL):

```sh
JAVA_HOME=/tmp/fc-chat-tools/jdk/jdk-17.0.20.1+1 ANDROID_HOME=/tmp/fc-chat-tools/sdk GRADLE_USER_HOME=/tmp/fc-chat-tools/gradle-home /tmp/fc-chat-tools/gradle-8.11.1/bin/gradle -p clients/android :app:assembleDebug :app:assembleDebugAndroidTest --offline --no-daemon -PfcTargetAbi=arm64-v8a -PfcBuildPython=/tmp/fc-chat-tools/python310/python/bin/python3.10
```

Gradle/ADB использовали разрешённый запуск вне sandbox для локальных сокетов.
Остались предупреждения SDK XML, watcher, deprecated API/Gradle и не удалённых
debug symbols Python-библиотек. Зависимости Python взяты из cache; `--offline`
ограничивает Gradle, но не является гарантией отсутствия сетевых обращений pip.

Локальные артефакты, не release и не опубликованы:

| Файл под clients/android/app/build/outputs/apk | SHA256 |
| --- | --- |
| debug/app-debug.apk | 22435736509c6fbcf0f07b5607037bde62606318f62eb066fed937cb3f4e30dc |
| androidTest/debug/app-debug-androidTest.apk | 27dae5729ff929b3a57a44c6cb55e058be25f0fbc9165419ee64713b95e6b797 |

Предыдущие124 JVM tests — результат предыдущего checkpoint; новый Android test
туда не входит. На этом шаге проверена его компиляция/упаковка, не исполнение.
`check_public_docs.py --all`: 322 файла,1901 ссылка,0 ошибок; `git diff --check` passed.

## Следующий запуск

Использовать отдельный пустой эмулятор. Для x86_64 сначала пересобрать с
`-PfcTargetAbi=all` (указанная выше сборка только ARM64). После проверки serial,
ABI и отсутствия пользовательских данных установить оба debug APK на этот эмулятор.
Не использовать `pm clear`, удаление пользовательского приложения или Friends APK.
Запускать именно один новый класс, с явным serial, заменив `emulator-5554`
идентификатором проверенного disposable-эмулятора:

```sh
adb -s emulator-5554 shell am instrument -w -e fc_disposable true -e class com.familyconnect.app.ControlSelectionRuntimeTest com.familyconnect.app.pilot.test/androidx.test.runner.AndroidJUnitRunner
```

Затем отдельно проверить настоящий service/UI: отмена VPN permission до отправки
Intent, быстрый повтор выбора, stop во время health, process restart при SWITCHING,
восстановление показанного выбора и полезный трафик после перехода. Для этого нужны
тестовое enrollment и доступный gateway; данный TEST ONLY corpus сеть не предоставляет.
Friends identity integration и включение рабочей capability остаются открытыми.

## Документация, публикация и откат

Обновлены STATUS, PLAN, общая карта клиентов и managed-карта. Проверенный remote main:
`b5f486444c66f3093cdc49ecbd30cc8fcc5da901`; новые изменения этого шага локальные,
commit/push и deployment не выполнялись. Серверы и установленные приложения не менялись.
Для отмены этого шага убрать новый test и настройку host Python; он сам не меняет
производственный journal/schema. Откат уже используемой schema2 понижением reader
недопустим без отдельной миграции; нельзя сбрасывать replay floor ради отката.
