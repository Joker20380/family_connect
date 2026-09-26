# Android beta24: фактура карты и дужка замка — 2026-09-20

Продолжение [beta23](2026-09-20-android-reference-beta23.ru.md) после замечаний
пользователя: в OFF дужка оставалась оторванной, точки суши выглядели неудачно.
В TerminalUi.Dial полукруг имеет постоянную правую ножку до корпуса в обоих
состояниях. Открытый замок отличается поднятой левой ножкой; закрытый соединён с двух сторон.

RouteMapView: вместо одной случайно сдвинутой точки на ячейку — случайные кандидаты
с минимальным расстоянием 1.30dp. Пространственная сетка используется только для
поиска соседей и не задаёт позиции. Fixed seed сохраняет повторяемость; отбрасывание
близких кандидатов устраняет сгустки. Диаметр 0.58dp, alpha120±12 вместо105±23;
период5.2s прежний. Геометрия кешируется; clip и жесты не менялись.
Синтетические native рендеры:
[карта](../assets/android-map-beta24.png), [открытый замок](../assets/android-dial-off-beta24.png),
[закрытый замок](../assets/android-dial-on-beta24.png).

Gradle testFriendsUnitTest/lintFriends/assembleFriends/assembleFriendsAndroidTest
successful. 140 unit tests, 0 failures/errors/skipped; lint0errors/18warnings.
На Redmi Note9 Pro/Android12 четыре native tests прошли: RouteMapRuntimeTest (2),
DialRuntimeTest (1), DashboardLayoutRuntimeTest#viewportHasNoScrollAndAllControlsFit (1).
Проверены clip при27 width/zoom/pan сочетаниях, мерцание/reduced-motion, hit area,
disabled click/accessibility и компактная компоновка. Рендеры просмотрены.
Фактическое VPN-подключение тестами не запускалось; ON — синтетическая fixture.

APK `state-client-build/android-pilots/beta24/FamilyConnect-Test-0.1.18-beta24.apk`,
36395084bytes, versionCode24/versionName0.1.18-beta24, SHA256
`adf0ae752a7dffddad039f0e649c3a611906e04428e4b3bd13f3dcbc32ad1052`.
Certificate SHA256 прежний:
`67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
Подпись, zipalign, ABI/libraries, nondebuggable проверены. Перед установкой Current
Networks без VPN. install-r успешен, установленная версия и SHA256 сверены.
APK beta22/23 неизменны; public beta19 не заменялась. Rollback — прежняя реализация
с новым code>24 и тем же ключом, установка поверх без uninstall/clear.

Точный snapshot Java/build.gradle сохранён в ignored beta24/source, логи сборки
в android-pilots/map-preview/gradle-reference24.log, native результаты в
beta24/map-runtime.txt. Android исходники остаются в накопленном root working tree;
в desktop-ветке сохраняются только отчёты и синтетические рендеры. Отдельная
консолидация Android исходников ещё нужна. Пользовательская оценка и дальнейшая
анимация открыты. Linux5a9ca444046993a7/helpers7a8036a прежние; QR preview не установлен.
Windows live ждёт доступного компьютера; проверка российской сети не заявляется.
