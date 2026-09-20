# Android beta23: карта и круг по референсу — 2026-09-20

Пользователь заменил задачу простого удвоения точек визуальным референсом:
`ChatGPT Image 19 сент. 2026 г., 14_56_02 (3).png`, SHA256
`5ceb62734869354f9c5ad844263120767f16158e403c3894a1509e82203036eb`.

RouteMapView показывает мир (-180…180°, -60…85°), сушу из точек диаметром
0.65dp со средним шагом 1.84dp: примерно 2× плотность beta21. Независимые
фиксированные смещения по двум осям сохраняют нерегулярность без дрожания геометрии.
Grid 16dp/0.4dp, alpha45; мерцание точек 5.2s. Clip, pinch/pan и выбор узла сохранены.
Реальные узлы NL/RU; промежуточные узлы из картинки не выдуманы.

TerminalUi.Dial: четыре тонких кольца, 64 сегмента, 120 рисок, перекрестие,
три орбитальных маркера и мягкое свечение. Период движения 9s; учитываются настройка
движения, системный animator, видимость и фокус окна. OFF/ON/… соответствуют состоянию
приложения; замок закрыт только при подтверждённом healthy. Процент из картинки
не имитируется. FriendsActivity подключает круг на главной и в «Маршрут» к существующим
действиям подключения/отключения; busy блокирует повторные нажатия. Круг доступен как
Button, реагирует на нажатие/фокус, не принимает касания внешних углов.

Промежуточная beta22/code22 была установлена и прошла 140 unit и 4 native tests
(12.831s). На рендере обнаружен зазор дужки закрытого замка. Beta23 добавляет её
вертикальные стороны. Beta22 APK не заменён: SHA256
`2dcd5e9a78d8058a779e5c335bf24753a387aee682564b977807e5e6f13e15aa`.

Финальная beta23: Gradle testFriendsUnitTest/lintFriends/assembleFriends/
assembleFriendsAndroidTest successful; 140 tests, 0 failures/errors/skipped.
Lint 0 errors, 18 warnings, включая два DrawAllocation в отрисовке Dial.
На Android12/Redmi Note9 Pro: install-r success, 4 instrumentation tests passed,
12.799s. RouteMapRuntimeTest проверяет 27 width/zoom/pan комбинаций, отсутствие
выхода ниже рамки, мерцание без location и reduced-motion. DialRuntimeTest проверяет
click/corner/disabled/accessibility, разные состояния и стабильность без движения.
DashboardLayoutRuntimeTest проверяет размещение элементов, включая компактный экран.
Синтетические [карта](../assets/android-map-beta23.png) и
[круг ON](../assets/android-dial-beta23.png) просмотрены; ON — тестовое состояние,
не свидетельство живого VPN. Рендеры реального экрана сохранены только локально.

APK: `state-client-build/android-pilots/beta23/FamilyConnect-Test-0.1.18-beta23.apk`,
36395084 bytes, versionCode23/versionName0.1.18-beta23, SHA256
`ea87115affd4d9cc827f4af847ae6271470344fe992e10d2133402bbb7726e31`.
Certificate SHA256:
`67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
Подпись, zipalign, ABI/libraries, nondebuggable проверены; версия и SHA256 именно
установленного APK совпали. Перед установкой в Current Networks отсутствовал VPN.
Установка поверх beta22 без uninstall/clear, главный экран открыт для оценки.

Рабочие Android исходники остаются в root main3f6f662 с накопленными изменениями;
точный snapshot трёх production Java, трёх instrumentation Java и build.gradle
сохранён в ignored `state-client-build/android-pilots/beta23/source/`.
В desktop-ветку переносится только этот отчёт и безопасные синтетические рендеры;
консолидация Android исходников в отдельный коммит остаётся открытой.

Public download/gateway по-прежнему beta19; публикации не было. Rollback:
собрать прежний интерфейс с code>23 и прежним signing key, установить поверх,
без удаления данных и без перезаписи старых APK/тегов. Живое VPN-подключение новым
кругом, пользовательская оценка и дальнейшая художественная анимация остаются
открытыми. Linux bundle5a9ca444046993a7/helpers7a8036a не менялись; QR source5002579,
preview9c4fb610ef3153ec не установлен. Windows live отложен по просьбе пользователя.
