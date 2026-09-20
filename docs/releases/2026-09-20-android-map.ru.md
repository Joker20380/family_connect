# Android beta20: рамка и точечная карта — 2026-09-20

Пользователь заметил выход маршрута вниз за рамку при zoom и попросил точечную
слегка мерцающую сушу и меньшую сетку. Исходный референс в доступных файлах не найден;
реализация следует текстовому описанию, визуальная оценка пользователем впереди.

RouteMapView ранее restore() снимал clip до route/device drawing. Теперь общий
viewport clip действует на land, nodes, route и device label, frame рисуется после
restore в finally. Pinch масштабирует вокруг focus и не дублирует scroll во время
scale. Нижняя область вне mapH не получает маршруты и не выбирает скрытые узлы.

Land fill заменён кэшированными точками с шагом4dp/диаметром1.15dp; screen mask
перестраивается только при viewport/zoom/pan/location.8 групп мерцают с периодом5.2s,
alpha105±23; геолокация не нужна для land animation. Motion=false даёт статичный
результат; hidden/detached view останавливает animator. Grid16dp, stroke0.5dp,
пониженная яркость. Новая анимация главного экрана/«Бункер» не затрагивалась.

Сборка ARM64 Friends beta20/code20,140 unit tests passed, lint0errors/16warnings;
assembleFriends и assembleFriendsAndroidTest success. Новые native Canvas tests:
27 сочетаний width/zoom/pan с проверкой пикселей под mapH; изменение land без location
и стабильность reduced motion. Скомпилированы; runtime пока pending.

APK state-client-build/android-pilots/beta20/FamilyConnect-Test-0.1.18-beta20.apk,
36390988bytes, SHA256 f64235af0e8b1b3147656b9b864d9690cb4bffa6372a24423d6f01f4ddefdd3b.
Прежний локальный Android certificate SHA256
67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a;
zipalign/signature/ABI/library/package/version/nondebuggable checks passed.
Исходники карты и tests сохранены в рабочей Android папке и приватном build snapshot;
накопленные Android-изменения основной папки не включены в desktop-ветку целиком.

Телефон31ce63ba подключён после запроса. Installed beta19 подтверждена; обнаружен
активный VPN. Пользователю предложено штатно отключить VPN перед install-r.
Никакого отключения/удаления данных/обновления телефона пока не выполнено.
После отключения: adb install-r beta20 и подписанный test APK, два native Canvas tests,
просмотр route-map-dots.png, затем ручные pinch/pan и визуальная оценка.
Public invite/download по-прежнему beta19, beta20 не опубликована.

Rollback клиента: не удалять приложение; при необходимости собрать code>20 с прежним
кодом карты и прежним beta signing key. Не заменять APK/URL опубликованной beta19.
Windows live отложен пользователем до доступности Windows-компьютера.
