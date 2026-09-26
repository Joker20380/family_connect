# Android SDK CI — 23.09.2026

**Завершено:** SDK исправлен и опубликован в main. Все четыре Client builds/Android
diagnostic прогона main и кандидата — success. Дополнительный Docker-дефект
кандидата исправлен,448 локальных тестов и удалённый phase0/tests+failover passed.
Публичные версии приложений не менялись.

Client builds35861515927/source54506d8 остановился на setup-android@v3.
Linux/Windows jobs и отдельные Windows AWG/TCP/UI/broker прошли; release skipped.
Полный job log API возвращает403; annotations не содержат подробной ошибки SDK.

В setup-android v3 default packages=`tools platform-tools`. Maintainer сообщает,
что Google больше не распространяет `tools`. Это подтверждённая несовместимость
конфигурации, а связь с прежним отказом проверяется новым CI.
Источники: [v3 action.yml](https://github.com/android-actions/setup-android/blob/v3/action.yml),
[upstream documentation](https://github.com/android-actions/setup-android#the-deprecated-tools-package).

В clients.yml и android-diagnostic.yml явно задан `packages: platform-tools`.
JDK17, cmdline-tools12266719, Gradle8.11.1, API35/build-tools35/NDK28.2.13676358,
сборка и runtime проверки сохранены. Ошибки не игнорируются, release gates сохранены.
Исправление ce6fb11 в отдельной ветке fix/android-sdk-20260923 поверх54506d8.
Это проверка кандидата существующей ветки, не воспроизводимая сборка APK49.
Публичные beta49/Linux0.2.9/Windows0.2.9 и страница beta35 не менялись.

Откат исправления: revert ce6fb11, без изменения установленных приложений/данных.
Итог: main patch e900cfa опубликован вместе с документацией в6299cea; полный CI ниже завершён.

## Первый результат

На ce6fb11 шаг setup-android завершился success в обоих workflow:
[Client builds35890871305](https://github.com/Joker20380/family_connect/actions/runs/35890871305),
[Android diagnostic35890871337](https://github.com/Joker20380/family_connect/actions/runs/35890871337).
После него начались conformance/native build. YAML разбор и diff --check прошли.
Отдельный phase0 failover остановился на Build isolated failover stack;
исправление SDK не закрывает этот другой дефект и не объявляет весь выпуск принятым.
Тот же узкий patch перенесён в main как e900cfa; обновление main не включает
накопленные исходники клиентов. Новые APK/установщики не публикуются.

## Отдельный дефект Docker-кандидата

Локально воспроизведён failure Dockerfile.control на source ce6fb11: при сборе тестов
отсутствует /app/deploy/server-load/monitor.py. После его добавления:446 passed,
2 failed из-за отсутствия clients/desktop/friends_qr.py в allowlist упаковки.
В tests stage добавлены monitor.py и Friends UI/QR modules; runtime stage и
шестифайловый desktop контракт не меняются. Финальный Docker build passed:448 tests passed,2 existing deprecation warnings,25.32s.
Эти файлы ещё отсутствуют в старом main source, поэтому Docker-поправка относится
к ветке кандидата и должна войти вместе с соответствующим source checkpoint.

Docker patch опубликован только в ветке кандидата как aa0b0a7.
[Phase0 run35891724967](https://github.com/Joker20380/family_connect/actions/runs/35891724967)
завершился success: tests и failover прошли. Это закрывает воспроизведённый сбой
состава tests image для этого checkpoint. В основной рабочей копии поправка сохранена.
Версии исходной CI-ветки: Android0.1.7-beta08/code8, Windows csproj0.2.10,
общий VERSION0.2.9. Поэтому эти CI assets нельзя выдавать за согласованный новый
релиз или заменять ими установленную beta49. Версии предстоит согласовать в новом
проверенном source checkpoint, сохранив неизменяемость уже опубликованных артефактов.

## Завершённые проверки ветки кандидата

Client builds35890871305 — success (Android/Linux/Windows), Android diagnostic
35890871337 — success. Build, unit/lint, emulator WG/AWG/TCP/Auto и control/storage
acceptance прошли без удаления проверок. Release job не выпускает артефакты из
обычной fix-ветки; этот success не означает новую публичную версию.
Main6299cea: [Client builds35891111532](https://github.com/Joker20380/family_connect/actions/runs/35891111532)
и [Android diagnostic35891111340](https://github.com/Joker20380/family_connect/actions/runs/35891111340)
оба завершились success. Отдельный main phase0 также success.

Read-only inventory для следующего checkpoint:136 public-source files отличаются
между рабочей копией и CI-кандидатом, включая83 Android и23 messenger файла.
Это перечень для последующего review, не подтверждение их готовности к публикации.

Следующий шаг: согласовать VERSION/Windows/Android в актуальном source checkpoint,
провести его собственные проверки и только затем выпускать новые неизменяемые файлы.
Откат main SDK patch: revert e900cfa; откат Docker-кандидата: revert aa0b0a7.
