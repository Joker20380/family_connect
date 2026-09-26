# 5.3а: согласование Java/C#/Python verifier AWG3.1

24.09.2026. Локальный исходный checkpoint; не выпуск приложений и не production rollout.
Версии остаются Android0.1.18-beta50/code50, Linux0.2.10, Windows0.2.13.

## Реализация

Android `ControlProtocol.verifyConfiguration` получил overload с явным
`supportsAwg31`; прежняя сигнатура вызывает его с false. C# `VerifyConfiguration`
получил необязательный bool с default false. Это доверенная способность вызывающего
приложения, не значение из полученной конфигурации. Номер версии сам её не включает.

Java/C# `ControlProfiles` принимают AWG3.1 с обязательными HeaderProtectionKey,
ContentPaddingAddition, RandomTrailers и DisableCookies. Проверяются ненулевой
канонический ключ32 bytes, padding0..256 и порядок диапазона, флаги true/false,
S1..S4 не менее12 для защищённых заголовков, H1..H4 равные1..4, одинаковые S при
RandomTrailers=true. Профиль с этими полями под меткой2.0 отвергается.
Сохранены строгие поля, запрет hooks, привязка gateway ID/endpoint/port и local key.

Добавлены Java/C# runners общего immutable corpus `control-awg31-v1`, с закреплённым
SHA256 manifest51a0e53434e46876212a09945762a970c2943020220250f219042b12c71f7039
и проверкой hashes всех файлов. Восемь примеров проходят с capability=true/false;
положительный результат сравнивается с полным ожидаемым plaintext. Тесты не выводят
конфигурации/ключи. Старый corpus не изменён. C# csproj копирует новый corpus только
в test output; Android получает его из существующего test resources каталога.

На обеих платформах добавлены десять отказов для неполных/испорченных параметров,
нулевого protection key и hooks. Java дополнительно материализует тестовый локальный
ключ и проверяет сохранение строк профиля существующим Android ProfileValidator.
Это не вызов AWG engine и не изменение VPN на устройстве.

## Проверки и воспроизведение

- Java17/BouncyCastle1.85.2/Gson2.13.2:109 JUnit tests,0 failures/errors/skipped.
  `JAVA_HOME=/tmp/fc-chat-tools/jdk/jdk-17.0.20.1+1 GRADLE_USER_HOME=/tmp/fc-chat-tools/gradle-home /tmp/fc-chat-tools/gradle-8.11.1/bin/gradle -p clients/android/control-tests test --offline --no-daemon`
  Первый запуск sandbox запретил daemon socket; повтор с разрешением вне sandbox прошёл.
- C#/.NET10.0.401: `dotnet run --project clients/windows/Tests/Tests.csproj --no-restore`
  через локальный `/tmp/fc-desktop-dotnet/dotnet` завершился0. Новый corpus16 проверок,
  десять protection refusals, прежние30 config/15 ACK/31 structure checks и остальные
  тесты этого runner прошли. Windows DPAPI runtime явно SKIP на Linux. Это исполнение
  C# на Linux, не Windows UI/broker/DPAPI acceptance. NuGet вывел NU1900 о недоступных
  данных vulnerability audit из кэшированных restore metadata; актуальный аудит
  зависимостей этим запуском не подтверждён.
- Python: `tests/test_awg31_vectors.py tests/test_fleet_awg31.py tests/test_control_vectors.py`
  через `/tmp/fc-desktop-current-venv/bin/python -m pytest -q`:86 passed за0.76с.
- `git diff --check` прошёл. Production keys не читались; серверы не изменялись.

## Следующая работа и откат

5.3а ещё открыт. Java ControlIdentity/managed journal не включает новую способность;
Linux runner и Windows production caller также не включены. Следом — передача
capability через защищённую application boundary, проверка native materialization,
health/rollback/restart и существующей Friends identity. Windows managed journal/broker
интеграция остаётся незавершённой. Выпуск только после platform release gates.

Новый сервер сейчас не нужен: conformance и локальное применение проверяются на
имеющемся стенде. Перед этапом независимого восстановления понадобится доступная
точка входа вне отказавшего пути; требования/размещение определяются в
[проекте восстановления](../reticulum-recovery-design.ru.md). Аренда в этой работе
не выполнялась и новый провайдер не выбирался. Число IP само по себе независимости
не доказывает; нужны разные failure domains и приёмка из целевой сети.

Runtime default остаётся false, так что откат серверов/БД не требуется.
Не снижать revision floors и не перезаписывать подписанные конфигурации при будущем
пилоте; capability включать только вместе с проверенной application boundary.
