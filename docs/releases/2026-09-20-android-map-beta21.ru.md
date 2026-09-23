# Android beta21: тонкие точки без ровных рядов — 2026-09-20

Пользователь счёл точки beta20 второй сеткой. В RouteMapView шаг уменьшен4→2.6dp,
stroke diameter1.15→0.65dp. Каждая позиция получает независимое смещение по x/y
внутри ячейки (15–85% шага), PRNG fixed seed0xFC2021: геометрия не дрожит при
анимации opacity. Cache перестраивается только при изменении viewport. Плотность
примерно(4/2.6)^2=2.37. Grid16dp/0.5dp и общий viewport clip beta20 сохранены.

140 unit tests passed; lint0errors/16warnings; Friends APK и instrumentation собраны.
На Redmi Note9 Pro Android12: install-r beta21/code21 и test APK success;
RouteMapRuntimeTest OK(2tests),3.779s:27 комбинаций width/zoom/pan, land shimmer без
location и static reduced-motion. [Native рендер](../assets/android-map-beta21.png)
просмотрен, ровные ряды точек исчезли. Экран «Маршрут» открыт для пользовательской оценки.
Перед установкой текущая секция Android Current Networks не содержала VPN;
широкий поиск dumpsys давал VPN из истории — он не использовался как active-state.

APK:state-client-build/android-pilots/beta21/FamilyConnect-Test-0.1.18-beta21.apk,
36390988bytes. SHA256 eb3228b91b9de1bb3fbb7d244bc1251da9a7b77ba48adb691e317d9afdabafad.
Установленный package/version/hash проверены. Certificate прежний:
67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a.
zipalign/signature/ABI/library/nondebuggable checks passed. Данные/активация сохранялись.
Source/test snapshot сохранён в закрытом build-каталоге, Android рабочие исходники
не подменены старой desktop-веткой. Root main3f6f662 с накопленными изменениями сохранён.

Beta21 не опубликована на gateway. Public download beta19 неизменен; старые APK/URL
immutable. Rollback: новый code>21 с прежним signing key и прежним map implementation,
без uninstall/clear. Проверка реальной сети не запускалась. Windows live отложен,
Linux5a9ca444046993a7 и helpers7a8036a не менялись; QR исходники5002579 сохранены.
