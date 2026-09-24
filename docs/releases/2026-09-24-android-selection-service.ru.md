# Android managed gateway: service/UI entry point

24.09.2026. Исходный checkpoint5.3а, без публикации/установки APK.
Версии прежние: Android0.1.18-beta50/code50, Linux0.2.10, Windows0.2.13.

## Изменения

`MainActivity.chooseGateway` больше не записывает желаемый ID в preferences и не
делает disconnect→connect для выбора. После системного VPN permission и при необходимости
запроса notification permission отправляется явный Intent `select-gateway` с ID.
Отмена VPN permission не отправляет запрос. В UI добавлен результат SELECTED на RU/EN.
Это MainActivity managed/pilot, не FriendsActivity коммерческий путь.

`ConnectionService` (exported=false) принимает ID формата Identifier и выполняет
переключение через существующий worker/operationOwner. Рабочая служба может принять
запрос без предварительного disconnect. Для работающей службы AtomicBoolean ограничивает
повторное помещение selection в очередь; stopping/closing не допускают новую операцию.
При ошибке служебного выполнения используется существующий fail-closed shutdown;
успешный rollback восстанавливает baseline через transaction, не через UI.

Новый `ControlSelection` отделяет проверяемую policy от Android Intent:
authorize существующего enrollment/identity → recover → selectGateway → при SELECTED
и отсутствующем engine выполнить проверяемый resume. Повторный выбор сам по себе не
переприменяет профиль; resume при reconnect обязательно проходит health.
Проверка enrollment выделена из ControlIntake в общий authorize без ослабления правил.

После служебной операции preferences обновляются из journal.selected_gateway как
кэш отображения. При открытии выбора и onResume экран перечитывает журнал на своём
worker под OWNER и исправляет кэш. Журнал остаётся authoritative; при отсутствии
ключа/ошибке чтения UI не создаёт identity/journal заново. Schema1/legacy preferences
остаются fallback существующего пути; новая selection сохраняется только через journal.

## Проверки

124 Java tests passed,0 failures/errors/skipped. Новые4 теста ControlSelectionAdmissionTest:
active switch/disconnected retry без повторной записи, неверный enrollment/identity/origin
без мутаций, запрет выбора при неуспешном recovery, health failure при повторном reconnect.
Host/storage имитируются; Android Intent/Keystore/VpnService этими тестами не исполняются.

Изолированный JVM прогон:

```sh
JAVA_HOME=/tmp/fc-chat-tools/jdk/jdk-17.0.20.1+1 GRADLE_USER_HOME=/tmp/fc-chat-tools/gradle-home /tmp/fc-chat-tools/gradle-8.11.1/bin/gradle -p clients/android/control-tests test --offline --no-daemon
```

Дважды успешна compileDebugJavaWithJavac с ARM64 configuration, последний запуск после
изменения onResume/cancel guard:

```sh
JAVA_HOME=/tmp/fc-chat-tools/jdk/jdk-17.0.20.1+1 ANDROID_HOME=/tmp/fc-chat-tools/sdk GRADLE_USER_HOME=/tmp/fc-chat-tools/gradle-home /tmp/fc-chat-tools/gradle-8.11.1/bin/gradle -p clients/android :app:compileDebugJavaWithJavac --offline --no-daemon -PfcTargetAbi=arm64-v8a
```

Gradle запускался с разрешением вне sandbox для локального сокета. Компиляция успешна,
но не является release build/runtime acceptance. Выведены предупреждения SDK XML,
deprecated API/Gradle, watcher и Chaquopy: host Python3.14 не соответствует bytecode3.10;
зависимости Python взяты из cache. Перед сборкой/выпуском необходимо корректное buildPython
и полные APK/lint/native проверки. Этот запуск не подтверждает работоспособность Python
payload или туннеля. Рабочие ключи/серверы не изменялись.

## Остаток и откат

AWG3.1 managed capability production callers всё ещё false; Friends identity binding
не подключён. Нельзя считать новое UI готовым Friends failover или выпускать3.1
конфигурации действующим клиентам по одному факту компиляции.
Следующий шаг — instrumented/device проверка service/UI, permission cancellation,
повторных taps, restart во время SWITCHING, health/rollback и сверка отображения с journal.
Далее native/Friends integration и соответствующие Linux/Windows gates.

Никакой schema2 migration на телефоне не выполнялась. После будущего selectGateway
возврат к старому reader schema1 без отдельной миграции недопустим; не удалять journal
и не обнулять floor. Сейчас deployment/rollback не требуются. Документы обновлены
локально; commit/push не выполнялись.
