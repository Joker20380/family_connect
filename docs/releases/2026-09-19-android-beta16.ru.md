# Friends 0.1.15-beta16 — анимация и входящие без ответа

2026-09-19. Пользователь уточнил, что смайлики должны двигаться. В beta15
проверялись GIF assets и spans на статическом рендере; это не подтверждало
воспроизведение анимации во времени.

## Исправление

В панели выбора ChatSmileyTextView оставался с foreground=false — анимация
не включалась. Теперь owner включает её для показанного окна, учитывает общую
настройку движения, выключает при паузе и закрытии. При detach переписки
открытая панель выбора закрывается, callbacks изображений освобождаются.

Текстовые сообщения со встроенными GIF рисуются на отдельном software layer,
чтобы selectable TextView не удерживал аппаратный кэш текста с одним кадром.
Остальное приложение остаётся hardware accelerated. При clearMessage слой
сбрасывается. GIF, исходные текстовые коды, хранилище и доставка не менялись.
Неподвижный PNG-рендер сам по себе не демонстрирует движение.

## Входящие без набора ответа

Пользователь дополнительно сообщил: смайлики приходят лишь при наборе ответа.
В Android был опрос delivery_state, но не было периодического request_sync.
DeliveryController намеренно не делает idle polling: обмен запускается событиями
queue/lifecycle/manual refresh. Входящего hint в текущем Android carrier нет.

Добавлен Android ChatPollPolicy: request_sync не чаще1раза/6сек, только пока
мессенджер видим, сеть доступна, нет running/pending и ошибки. Обмен выполняется
существующим controller, его cooldown/backoff/retry budget не сбрасывается.
После исчерпания повторов/ошибки нужна прежняя ручная попытка или изменение сети.
Это foreground polling, не фоновые push-уведомления. Задержка включает интервал
и время сетевого обмена. Общий Python controller/протокол/сервер не изменены.

## Проверки

Добавлена физическая regression-проверка на attached/focused selectable TextView:
таймер продвигается без внешнего рисования; пиксели меняются между кадрами;
foreground=false останавливает таймер, true возобновляет. Проверка использует
синтетический текст, без изменения пользовательских сообщений/контактов.
Сохраняются предыдущие проверки viewport, ввода, курсора и ICQ spans.
Две unit-проверки ChatPollPolicy: периодический запрос без исходящего сообщения,
интервал6сек и запрет для background/offline/running/pending/error.

Сборка: `gradle --no-daemon :app:testFriendsUnitTest :app:lintFriends :app:assembleFriends -PfcTestBuildType=friends -PfcTargetAbi=arm64-v8a :app:assembleFriendsAndroidTest`.
138 unit passed, lint0errors/16warnings,2 native UI tests passed на Redmi Note9 Pro/Android12.
GIF clock/смена пикселей/пауза/возобновление проверены на реальном focused View.
Установлена поверх beta15; versionCode16 и SHA256 сверены.
Пользователь подтвердил: входящий смайлик появился без набора ответа и двигается.
Затем сообщил о белых краях GIF — отдельное исправление следующей версии.

APK36386892bytes; SHA256 `15686db5aa3eb28c630164f63e3b9e0f2be5e0c9a0e86c1e386b47ac4440a60d`.
Публичное полное скачивание проверено по SHA256, HTML /invite/ совпал с исходником.
[Скачать beta16](https://185.251.89.19:8443/downloads/FamilyConnect-Test-0.1.15-beta16.apk).

## Выпуск и rollback

Выпущена: versionCode16, `com.familyconnect.app.friends`, ARM64/Android8.0+,
постоянный beta-v1 сертификат, установка поверх без удаления данных.
После физической проверки опубликован отдельный неизменяемый URL beta16,
обновлена основная кнопка на странице /invite/. Nginx -t и HUP passed. Beta15/14/13 не заменяются.
Откат APK — следующей версией code>16 с прежним ключом; не удалять историю.
Откат страницы — before-beta16-download backups nginx.conf/nginx-final.conf/
invite.html в /opt/apps/family_connect/state-product-https/config, nginx -t и HUP
только family-connect-product-https (учесть последующие изменения).

Пользовательская оценка движения в переписке/панели выбора, сообщения между
телефонами, offline/restart и другие устройства остаются отдельной приёмкой.
