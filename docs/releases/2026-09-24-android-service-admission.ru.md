# Android service admission: подготовка проверок

24.09.2026, этап5.3а. Добавлен `ControlServiceAdmissionRuntimeTest` в
`clients/android/app/src/androidTest/java/com/familyconnect/app/`.

## Покрытие и ограничения

Три сценария: неверный gateway ID отвергается до создания identity; выбор без
managed enrollment возвращает FAILED, освобождает owner и допускает повтор;
callback отмены разрешения VPN очищает pendingGateway без запуска selection.
Это реальная ConnectionService/MainActivity, но без enrollment, профилей и туннеля.
Последний сценарий вызывает callback напрямую, не нажимает системный dialog.

Предусловия: точный package `com.familyconnect.app.pilot`, debug flag,
`fc_disposable=true`, отсутствие службы, owner, профилей и managed encrypted
identity/journal/enrollment (включая .bak/.new и Keystore aliases). Cleanup
допускается только после прохождения предусловий. После отказов ожидаются
завершение службы, off и свободный owner; это исключает повторный запрос в ещё
завершающуюся службу. Секретные fixtures не создаются. Не запускать весь набор
instrumentation на личном телефоне: другие классы имеют отдельные ограничения.

## Что проверено

`:app:assembleDebugAndroidTest --offline --no-daemon -PfcTargetAbi=arm64-v8a`
с JDK17, Gradle8.11.1 и Python3.10: BUILD SUCCESSFUL,49 tasks (4 executed).
Использована существующая локальная сборка основного workspace; production Java
sources и Gradle inputs предварительно сравнены с чистым worktree, различий нет.
Копирование generated inputs в /tmp остановилось по квоте; неполная копия удалена.
Финальный test APK SHA256: `a49bb25c875c9f6d34aab6b5d435c2717b638a7b1946465f974a0321dd1d163f` (собран, не установлен).

Предыдущая редакция test APK `e3562637215aaf50d38ff2074bc1fd1dc692d43b7e659d3af524a09c0e20bf44`
установлена только как `.pilot.test`. Перед установкой pilot main APK подтверждён:
`22435736509c6fbcf0f07b5607037bde62606318f62eb066fed937cb3f4e30dc`.
Запуск instrumented класса не вернул результат за120с. Причина не установлена;
тайм-аут не считается ни успешным тестом, ни доказательством дефекта службы.
При последующей read-only проверке процесс pilot отсутствовал. Пользователь
попросил продолжить без телефона; повторный запуск и установка финальной редакции
отложены. Проверка APK hashes после запуска не выполнена из-за тайм-аута.

## Продолжение и откат

На свободном разблокированном тестовом устройстве установить финальный test APK
с совместимой подписью и запустить только этот класс:

```sh
adb shell am instrument -w -e fc_disposable true \
  -e class com.familyconnect.app.ControlServiceAdmissionRuntimeTest \
  com.familyconnect.app.pilot.test/androidx.test.runner.AndroidJUnitRunner
```

Ожидается `OK (3 tests)`. При зависании сначала исследовать runner/Activity startup;
не увеличивать timeout и не объявлять runtime acceptance по одной сборке.
Затем отдельный стенд с реальным enrollment: системное VPN permission/cancel,
выбор gateway, process restart, rollback и полезный трафик. Managed AWG3.1 capability
по умолчанию всё ещё false; существующий Friends AWG3.1 от этого не зависит.

Production код/серверные настройки/публичные APK не менялись. Android beta50/code50,
Linux0.2.10, Windows0.2.13 сохранены. Откат — убрать новый test source и при
необходимости только `.pilot.test`; не удалять pilot/Friends или их данные.
План, статус и обе карты кода обновлены. Runtime gates этапа5.3а открыты.
