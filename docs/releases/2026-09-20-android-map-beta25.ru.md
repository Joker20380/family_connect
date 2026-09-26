# Android beta25: точки карты по референсу — 2026-09-20

Пользователь отметил светлые и тёмные точки в beta24, затем прямо попросил точки
как в предоставленном референсе. Эта новая инструкция заменяет прежнее требование
нерегулярного распределения. RouteMapView теперь использует шаг2.3dp и смещение
соседних рядов на полшага; высота ряда spacing×sqrt(3)/2. Диаметр0.65dp округлён
до целого физического пикселя (минимум1px), центры согласованы с чётностью диаметра.
Это выравнивает растровое покрытие точек. Вместо восьми фаз яркости используется
общая alpha120±6, период5.2s; reduced-motion — постоянная120. Решётка карты,
clip, маршрут и интерактивный круг beta24 не менялись.

Первый локальный вариант beta25 с нерегулярными точками не подписывался и
не устанавливался. Итоговая сборка — gradle-reference25-final.log.
140 unit tests, 0 failures/errors/skipped. Lint0errors/18warnings.
На Redmi Note9 Pro/Android12 четыре native UI tests passed: RouteMapRuntimeTest2,
DialRuntimeTest1, DashboardLayoutRuntimeTest#viewportHasNoScrollAndAllControlsFit1.
Проверяются 27 сочетаний width/zoom/pan, shimmer/reduced-motion, действия круга и
компоновка. [Native рендер карты](../assets/android-map-beta25.png) просмотрен.

APK `state-client-build/android-pilots/beta25/FamilyConnect-Test-0.1.18-beta25.apk`,
36395084bytes, versionCode25,
SHA256 `8d350572bfca0d955f37858d2c957e379f04d93762a3a3355b21d673d8f1cb3b`.
Certificate SHA256 прежний:
`67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
Подпись, zipalign, ABI/libraries, nondebuggable проверены; установленная версия и
SHA256 сверены. Перед install-r Current Networks без VPN. Данные не удалялись.
Живое VPN-подключение тестами не запускалось. Public download остаётсяbeta19.
Rollback: прежняя реализация с code>25 и прежним ключом, установка поверх без
uninstall/clear; старые APK/теги не заменять.

Source snapshot сохранён в ignored beta25/source. Android исходники остаются
в накопленном root working tree; их отдельная консолидация открыта. В desktop-ветку
перенесены только документация и синтетический рендер. Пользовательская визуальная
оценка и дальнейшая анимация открыты. Linux5a9ca444046993a7/helpers7a8036a прежние,
QR preview не установлен. Windows live ждёт доступного компьютера.
