# Friends Android 0.1.8-beta09 — сборка 2026-09-19

Пользователь явно разрешил APK-сборку после прежней паузы. Цель: универсальный
`com.familyconnect.app.friends`, versionCode9/versionName0.1.8-beta09,
Family Connect Test с терминальным UI, мессенджером и QR-приглашениями.
Старый `com.familyconnect.app.pilot` не удаляется и не подменяется.

## Текущий результат

Универсальная подписанная APK собрана и установлена на Redmi Note9 Pro/Android12.
Файл: `state-client-build/android-pilots/beta09/FamilyConnect-Test-0.1.8-beta09.apk`,
240443312 bytes; SHA256 `bf8dc6116cdcf272e88928cd2ab58adf50f68a1c9966c75ab889728196ca15ce`.
Подпись постоянным beta-v1 certificate SHA256
`67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
Хеш установленного APK совпадает; главный экран запускается.
[Машинный отчёт и хеши исходников](2026-09-19-android-beta09.json).

JVM conformance108 и Friends unit136 passed; lintFriends — 0errors/11warnings.
Payload, четыре ABI, chat modules/LXMF/licenses, zipalign16KB и подпись verified.
На Redmi прошли4 локальных chatchecks и2 prepare/force-stop/resume проверки.
Исправлены AndroidX-настройка отдельного chat-runtime project и ожидаемый count4.

После замены кабеля телефон доступен. MIUI запрещает автоматические нажатия
(`INJECT_EVENTS`), поэтому активация не завершена; пользователю предложен ручной
ввод первого кода. Последняя серверная проверка: все50 прямых кодов свободны,
первый не активирован, referral pool500. Никаких кодов этот smoke не израсходовал.
Четыре VPN сочетания, native chat exchange и QR камерой ещё не приняты.
GitHub Release/download и изменения серверов в этом этапе не выполнялись.

После установки пользователь запросил следующий UI этап: главный экран без
прокрутки, выраженный оранжевый акцент, близость к трём исходным изображениям,
изучение экранной графики «Бункера», анимация и цветные переключатели.
Beta09 сохраняется как выданный артефакт; следующие APK должны иметь новую версию.

## Состав и воспроизводимость

- Java17, Gradle8.11.1, AGP8.9.2, Android compile/target35, min26.
- Chaquopy16.1.0/Python3.10, RNS1.5.1, LXMF1.1.1, ZXing3.5.3.
- Go1.26.1, NDK28.2.13676358, закреплённые revisions/patches из
  `pilot/android-awg/build.py`; четыре ABI без изменения протоколов.
- Новые зависимости сопровождаются лицензиями в `assets/control-licenses`.
- `verify-apk.py` принимает явный путь APK и проверяет наличие chat/carrier/
  admission, LXMF, bootstrap, лицензий и соответствие native manifest.
- Python3.10 compileall прошёл. Локальные build logs и снимок входных SHA256
  находятся в игнорируемом `state-client-build/android-pilots/beta09/`.
- Beta signing key остаётся в локальном `android-signing/beta-v1`; содержимое
  ключа/пароля, DB, device profiles и 50 кодов в APK/Git/CI не включать.

## Дальнейшие проверки и установка

До выдачи файла: assembleFriends, unit tests, lintFriends, packaged payload,
zip alignment и подпись. После этого нужна физическая приёмка двух телефонов:
активация, четыре сочетания RU/NL × AWG/TCP, chat exchange/restart/network lifecycle,
QR камерой другого телефона и реферальная активация. APK сам по себе не является
подтверждением этой приёмки.

Откат: не удалять старый Pilot. Friends хранит независимую identity; при проблеме
отключить его VPN, сохранить приложение/данные для диагностики. Удаление теряет
ключи и требует нового инвайта; downgrade поверх versionCode9 не обещается.
Исправления выпускать с новым versionCode, не заменять опубликованный APK
другими байтами под прежним именем/версией. Серверы этой сборкой не изменяются.
