# Актуальные исходники beta49 / desktop0.2.10 — 23.09.2026

Готовится отдельный source checkpoint поверх main57eb721: Android0.1.18-beta49/code49,
Linux APP_VERSION0.2.10, Windows csproj/setup0.2.10 и общий VERSION0.2.10.
APK49 остаётся ранее опубликованным неизменяемым файлом. CI-сборки не заменяют его:
подпись beta-ключом не выполняется в CI, побайтовая воспроизводимость APK не заявляется.
Публичные desktop загрузки пока0.2.9, страница приглашения покаbeta35.

## Состав и проверки

Включены накопленные публичные исходники: Android messenger/voice/edit/notifications,
Friends activation/UI/update; desktop invitation/identity/storage/AWG3.1/TCP/GUI;
серверная регистрация, relay/admission и объявления; тесты и pinned build workflows.
Runtime state, профили, базы, ключи подписи и локальные SDK/артефакты не включаются.
Базовые файлы взяты через git public-file inventory в отдельную копию; грязная исходная
рабочая копия сохранена. Изменение файлов сервера в Git не означает live deployment.

Локально:811 Python tests passed (основные, desktop, messenger); Docker tests image:
498 passed. Android ARM64 Friends153 unit/lint/build и compile instrumentation passed.
GTK24 layout cases, Friends UI и доставка URI существующему процессу passed.
Полный remote CI нового snapshot ещё не завершён.

## Исправления подготовки

Docker tests image дополнен messenger.service_events для тестов объявлений.
Friends UI tests ограничены Friends variant; технический pilot использует другой launcher.
Живые updater/device checks требуют явных аргументов fcLiveUpdateCheck/fcActiveDeviceCheck;
администратор/объявления/диагностика по-прежнему opt-in. Эти проверки не объявляются
пройденными на пустом эмуляторе. Детерминированные Friends UI/notification/voice/scroll
тесты запускаются отдельным шагом после VPN runtime на том же disposable эмуляторе.
fcFriendsCi=true и fcTargetAbi=x86_64 создают компактный тестовый APK с debug signing;
обычная платформа CI сначала собирает/проверяет все4 ABI. Runner отказывается работать на
физическом устройстве. Обычная beta-сборка без этого флага не меняет подписанта.

SDK platform-tools явно задан и для изолированного messenger harness. Старый pinned
preview publishing workflow теперь только workflow_dispatch: source push не должен
повторно публиковать существующий immutable preview. Windows ordinary-user acceptance
больше не ограничен прежней временной веткой и проверяется на новом кандидате.

## Rollout / rollback

Сначала source-ветка release/source-beta49-desktop0210 и её platform/native CI,
затем публикация проверенного source checkpoint в main. Новых публичных APK,
установщиков, подписанных каталогов и страницы приглашения на этом шаге нет.
Откат исходников — git revert соответствующего checkpoint с сохранением runtime state;
не переиздавать существующую beta49 другим бинарным файлом.
Следом: неизменяемые кандидаты клиентов, приёмка URI/обновления, согласованный rollout
страницы и загрузок. Doze/OEM/Android13+/Windows-ПК/российская сеть остаются отдельно.
