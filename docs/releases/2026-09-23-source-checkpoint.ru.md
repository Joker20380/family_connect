# Актуальные исходники beta49 / desktop0.2.10 — 23.09.2026

Опубликован source checkpoint поверх main57eb721: Android0.1.18-beta49/code49,
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
GTK24 layout cases, Friends UI, доставка URI существующему процессу и recovery passed.
Синтетический render встроенного Friends-экрана просмотрен. TCP installer UI passed
после адаптации проверки к встроенной панели подтверждения вместо прежнего диалога.
Исходный snapshot `ccb5257` опубликован в source-ветке; основной Windows client build,
phase0, messenger, desktop visual, control conformance, Linux AWG/TCP passed.
Client builds35898024283: Android и Windows jobs passed; Android runtime summary:
49 instrumentation cases (включая opt-in/variant skips),0 failures;
control conformance и storage restart passed.
Windows AWG35898024318 и TCP35898024406 passed. Первый общий Client builds завершился failure
из-за Linux-теста. Первая Linux-проверка выявила устаревший вызов
`response` на встроенной Gtk.Box: тест исправлен и локально повторён.
Windows ordinary-user upgrade: первый run35898024390 завершился без подробного
сообщения об ошибке; после добавления диагностики (`ef5af30`) run35898759903 passed
без изменения кода клиента. Причина первого отказа не установлена; исправление
runtime-дефекта этим повторным запуском не заявляется.

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

Повторная проверка `8627d55`: Linux control35899784727 и Linux job
Client builds35899784973 passed, включая исправленный TCP UI-тест, упаковку и
запуск извлечённого preview вне checkout. TCP pilot35899784891 passed.
Полный повтор Client builds35899784973 — success: Android, Windows и Linux.
Phase0 35899784729 — success. Android runtime повторно49 cases (включая skips),
0 failures; control conformance/storage restart passed. Код после8627d55 не менялся;
финальная документация обновлена по этим результатам.

[Client builds](https://github.com/Joker20380/family_connect/actions/runs/35899784973) ·
[Linux control](https://github.com/Joker20380/family_connect/actions/runs/35899784727) ·
[phase0](https://github.com/Joker20380/family_connect/actions/runs/35899784729) ·
[Windows ordinary user](https://github.com/Joker20380/family_connect/actions/runs/35898759903) ·
[Windows AWG](https://github.com/Joker20380/family_connect/actions/runs/35898024318) ·
[Windows TCP](https://github.com/Joker20380/family_connect/actions/runs/35898024406).

Windows rendering: native layout acceptance passed. Из аннотаций job107306747949
получены лишь первые10 частей preview (22500байт PNG без окончания); визуальная
приёмка нового Windows-рендера по этому файлу не засчитывается. Перед выпуском
установщика нужен полный CI artifact и его просмотр. Локальный Linux render просмотрен.

## Rollout / rollback

Source-ветка release/source-beta49-desktop0210 прошла platform/native CI;
проверенные исходники и итоговая документация опубликованы в main. Новых публичных APK,
установщиков, подписанных каталогов и страницы приглашения на этом шаге нет.
Откат исходников — git revert соответствующего checkpoint с сохранением runtime state;
не переиздавать существующую beta49 другим бинарным файлом.
Следом: неизменяемые кандидаты клиентов, приёмка URI/обновления, согласованный rollout
страницы и загрузок. Doze/OEM/Android13+/Windows-ПК/российская сеть остаются отдельно.
