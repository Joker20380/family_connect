# Список серверов с флагом и нагрузкой (Android Friends) — 26.09.2026

На главном экране Android (FriendsActivity, сборка friends) выбор сервера стал
информативнее: в раскрывающемся списке каждый сервер показывает флаг страны,
название и текущую нагрузку на момент выбора. Нагрузка читается из существующего
`https://185.251.89.19:8443/status/server-load.json` одним запросом для обеих стран
и обновляется с кэшем15с; отсутствие свежих данных показывается как «Нет данных»,
а не как 0%. Индикатор под кругом по-прежнему показывает нагрузку выбранного сервера.

Изменения:
- `clients/android/app/src/main/res/drawable/ic_flag_ru.xml`, `ic_flag_nl.xml` — векторные флаги.
- `clients/android/app/src/main/java/com/familyconnect/app/ServerLoad.java` — `fetchAll()` (один запрос, оба gateway), разбор вынесен в `gateway()`.
- `clients/android/app/src/main/java/com/familyconnect/app/FriendsActivity.java` — кастомный `ServerAdapter` для выбора страны; опрос нагрузки переведён на обе страны.

Проверка:
- `ServerLoad.java` собран отдельно через `javac` с gson — успешно.
- Полная сборка Android и UI-приёмка не выполнялись: в этой среде нет SDK/эмулятора.
- Существующие `ServerLoadTest` и `DashboardLayoutRuntimeTest` не прогонялись.

Версии/APK/production не менялись; публикация не выполнялась.

Откат: `git revert` соответствующих коммитов; вернуть `TerminalUi.inlinePicker` для
`countries` и прежний `ServerLoad.fetch(target)`.
