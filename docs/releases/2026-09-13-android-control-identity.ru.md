# Android Stage 5: защищённая identity — 13.09.2026

Продолжение существующего рабочего дерева `family_connect`, базовый HEAD
`4cb1423`. Перед работой проверены status, diff, staged diff и STATUS/PLAN.
Большой незакоммиченный Stage 5, Linux-пилот, native verifier и messenger сохранены.
По уточнению пользователя продолжена Android-часть Stage 5, не messenger bridge.

## Реализация

- `ControlIdentity`: независимые X25519/Ed25519 ключи Reticulum и отдельный
  X25519 ключ WireGuard. Формат private material: 64 RNS + 32 WG bytes.
  Public identity, reference и enrollment proof совместимы с Python reference.
  Подпись связывает публичные ключи с challenge в существующем enrollment domain.
  Invitation, entitlement и одноразовость challenge по-прежнему проверяет сервер.
- `ControlIdentityEnvelope`: локальный version1 AES-256-GCM envelope,125 bytes,
  собственный AAD `family-connect/control-identity/v1`; случайный nonce создаёт
  криптопровайдер. Это не новая wire schema подписанной конфигурации.
- `ControlIdentityVault`: отдельный AndroidKeyStore alias
  `family-connect-control-identity-v1`, AtomicFile `control-identity.enc`
  в noBackupFilesDir. `create` вызывается только при явной первичной регистрации;
  `load` никогда не создаёт identity. Существующий alias/base/bak/new запрещает
  повторное создание. Потеря ключа/файла, повреждение или незавершённое создание
  требуют явного восстановления, а не автоматической смены identity.
- После записи файл повторно читается и обе публичные identity сверяются до возврата
  нового объекта. Это обнаруживает ошибки записи/rename, которые AtomicFile может
  только записать в log. Orphan alias сохраняется как запрет неявной регистрации.
- Полученные временные массивы private material очищаются; close запрещает дальнейшее
  использование объекта. Полное стирание всех внутренних копий JVM/BC не заявляется.
- Standalone Java control-tests исключает Android-only vault; envelope/identity
  проверяются на JDK, vault дополнительно компилируется против Android SDK35.

## Проверки

Локальный контейнер `gradle:8.11.1-jdk17`, сеть выключена, существующие зависимости
BC1.85.2/Gson2.13.2/JUnit4.13.2. `javac` с Android35 android.jar компилирует все
Control classes, включая vault. JUnit: **8 tests passed** — прежние2 и новые6.
Существующий набор:30 конфигураций,15 ACK,32 structural refusals и4 authenticated
cipher refusals. Manifest SHA256 остаётся
`c97e00ccff7440b09a636a792557c0602aba5eb63815cdc8fefe7755711ac3cd`.

Новые проверки: совместимость публичных ключей/reference и расшифровки; точное
совпадение enrollment proof с Python; независимость WG/RNS ключей; encrypted
round-trip; случайность nonce; изменение каждого из125 bytes; неверный wrapping
key/длина/версия; отказ при другом AAD; закрытая identity и неверный challenge.

Python: `python -m pytest -q -p no:cacheprovider tests/test_android_control_identity.py tests/test_control_vectors.py`
— **51 passed**,0.63s. Новый публичный fixture вынесен в
`tests/vectors/control-identity-v1`, immutable control-v1 не перегенерирован.
Java: `gradle -p clients/android/control-tests test`; в этой сессии те же классы
запускались напрямую через javac/JUnitCore с указанными cached dependencies.

## Границы и следующий шаг

Это библиотечный блок, пока не вызванный Activity/service. Журнал операций/outbox,
единый владелец ручных и автоматических VPN-операций, recovery после process death,
native apply/health/rollback и RNS carrier ещё не реализованы. Stage 5 Android
целиком не принят. Android Keystore/AtomicFile проверены только компиляцией:
нужны emulator/runtime сценарии create→process restart→load, corruption,
потеря alias/файла и сбой записи. Проверки реальных устройств/нагрузки не запускались.
Не удалять потерявший ключ journal/identity для обхода recovery.

Следующий блок: durable journal/outbox и operation ownership, затем recovery до
любых ручных/service mutations. Подключать регистрацию/identity к UI только после
этого; существующие импортированные профили не становятся RNS identity автоматически.

## Выпуск и возврат

Новых APK, server deployment, CI run, commit/tag/catalog нет. VersionCode3 /
`0.1.2-beta03` в существующем Android build.gradle не менялись. Подключения и
установленные приложения не трогались. Rollout пока только исходники; возможный
откат — убрать добавленные ControlIdentity* и тесты, вернуть исключение standalone
source set, сохранив весь предыдущий незакоммиченный Stage 5. На будущем устройстве
не удалять encrypted identity или Keystore alias для отката кода.
