# Android selection: проверка на физическом устройстве

24.09.2026, этап5.3а. Redmi Note 9 Pro, Android12/API31, ARM64.

## Установка и изоляция

До установки на телефоне имелся Friends0.1.18-beta50/code50, пакета pilot не было.
Установлены отдельные `com.familyconnect.app.pilot` и `.pilot.test`, debug signing.
Версия pilot0.1.18-beta50/code50. Friends не обновлялся, его данные не очищались;
после тестов его версия повторно подтверждена. Production и каталоги обновлений прежние.

`ControlSelectionRuntimeTest` теперь допускает физический телефон в пустом debug pilot.
Вместо проверки модели эмулятора требуется точный package `com.familyconnect.app.pilot`
и FLAG_DEBUGGABLE. Сохранены явный `fc_disposable=true`, idle/off, отсутствие profiles,
managed-файлов/.bak/.new и aliases до начала теста. Все эти проверки предшествуют
cleanup. Это ограничение тестового кода; рабочие проверки/production capability не менялись.
Другие storage tests по-прежнему emulator-only и на телефоне не запускались.

Сборка `assembleDebug assembleDebugAndroidTest` прошла с параметрами предыдущего
[отчёта](2026-09-24-android-selection-runtime-preparation.ru.md): ARM64, host Python3.10.21.
70 tasks:4 выполнены,66 up-to-date. SHA256 локальных установленных APK:

| APK | SHA256 |
| --- | --- |
| app-debug.apk | 22435736509c6fbcf0f07b5607037bde62606318f62eb066fed937cb3f4e30dc |
| app-debug-androidTest.apk | 571d52df6524c21ac90516fd0a68ab6e5ff6cf39d38136e078f5d9eb7593acbe |

## Исполненные проверки

Первый запуск AndroidJUnitRunner: `ControlProtocolRuntimeTest,ControlSelectionRuntimeTest`,
аргумент `fc_disposable=true`: **OK (3 tests),3.181s**.

- Неизменяемый corpus подписанных конфигураций и строгий JSON parser.
- Настоящие AndroidKeyStore/ControlJournalVault/AtomicFile: неэкспортируемый wrapping key,
  commit, выбор второго gateway, повторное открытие journal/core, resume и rollback
  после неуспешного health. Выбор остаётся сохранённым, floor/outbox/result/digest прежние.

Второй запуск: `ControlRnsRuntimeTest`: **OK (1 test),0.717s**.
Упакованный Python загружает RNS1.5.1/internal crypto и инициализирует Reticulum
без interfaces/discovery/listener и без загрузки device keys. Это не тест доставки
конфигурации по сети. В pilot остаётся служебный каталог `no_backup/rns-runtime-test`.
Проверка имён файлов после тестов подтвердила отсутствие control-journal/identity/enrollment
в no_backup; значения пользовательских ключей/профилей не читались и не выводились.

Для повторения использовать явный проверенный serial телефона в `adb -s SERIAL`:

```sh
adb -s SERIAL shell am instrument -w -e fc_disposable true -e class com.familyconnect.app.ControlProtocolRuntimeTest,com.familyconnect.app.ControlSelectionRuntimeTest com.familyconnect.app.pilot.test/androidx.test.runner.AndroidJUnitRunner
adb -s SERIAL shell am instrument -w -e class com.familyconnect.app.ControlRnsRuntimeTest com.familyconnect.app.pilot.test/androidx.test.runner.AndroidJUnitRunner
```

Не запускать всю instrumented suite на личном телефоне: остальные классы могут
требовать отдельного стенда или менять VPN. При отказе предусловий не очищать данные
для обхода проверки. Установленные pilot/test пакеты оставлены для продолжения работы.

## Что ещё не подтверждено

Host VPN в selection test имитируется, clock и identity/anchor — TEST ONLY.
Проверено повторное создание объектов, не смерть процесса. Не выполнены service/UI
permission/cancel, stop во время health, process restart при SWITCHING, handshake,
полезный трафик и восстановление через независимый RNS ingress. Pilot пока не enrolled;
синтетические адреса corpus не являются рабочими gateway. Следом нужны тестовое
enrollment/конфигурация и service/UI acceptance. AWG3.1 capability рабочих callers
остаётся false; перенос Friends identity не выполнен. Этап5.3а целиком не закрыт.

## Документация и откат

STATUS, PLAN, обе карты обновлены. Remote main проверен:
`b5f486444c66f3093cdc49ecbd30cc8fcc5da901`. Изменения этого шага локальные;
commit/push, публичный выпуск и серверный deployment не выполнялись.
Рабочий APK байт-в-байт прежний относительно предыдущего локального build;
изменён только guard в test APK. Для возврата к emulator-only guard откатить это
изменение теста и пересобрать test APK; пользовательская схема журнала не менялась.
