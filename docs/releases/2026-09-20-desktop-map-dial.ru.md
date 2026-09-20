# Карта и круг Android на Linux/Windows — 2026-09-20

Итог: Linux0.2.9 preview cce586a74c391108 установлен, включая новый интерактивный
круг и карту. Windows финальная отрисовка21b740a прошла native UI CI35501348376,
изображения обеих платформ просмотрены. Полный installer CI35501348219 завершает
layout; Windows-компьютер пользователя недоступен, ручная установка отложена.
Androidbeta25 и публичные релизы не менялись.

Основа — принятый пользователем Android0.1.18-beta25/code25. На desktop до этого
в «Маршрут» не было географической карты; на Linux круг был старым статичным.
Изменения:1ba7269 (карта), f2c7d94 (Cairo CI), c75f563 (интерактивный круг).

Карта: одинаковые Natural Earth exterior rings, longitude−180…180/latitude−60…85,
шаг2.3 logical units, высота ряда×0.8660254, нечётные ряды смещены на полшага.
Диаметр round(0.65×device scale), минимум1physical px; центры привязаны к чётности
диаметра. Mint#98f7d8, общая alpha120±6, период5.2s; grid16/.4/alpha45.
Linux Cairo и Windows GDI+ рисуют и кешируют геометрию в физических пикселях,
восстанавливают cache при resize/DPI. При скрытой вкладке анимация останавливается;
учитывается системная настройка движения. GPU/OS rasterization может отличаться
на границе берегов/точек. Полная карта без выдуманной позиции пользователя или hops;
desktop zoom/pan и настоящий маршрут пока не добавлены.

Круг:64 сегмента,120 рисок,4 кольца, перекрестие,3 медленных маркера (9s), ON/OFF/…,
прикреплённая дужка открытого/закрытого замка. Нажатие вызывает существующий toggle,
busy/readiness наследуется от кнопки. GTK Button и WinForms Button сохраняют
клавиатуру/accessibility; область мыши ограничена кругом. ON означает существующее
состояние туннеля desktop; это не новая независимая проверка доступности интернета.
Android health model не подменён выдуманной desktop-проверкой.

Локальная проверка:GTK state/poll/confirmation passed;24 layout cases (RU/EN,
360/420/680,scale1/1.5/2/2.5). Первоначально transient allocation на250% дал clipped
button; повтор на250% passed, после ожидания .2s при смене страницы весь прогон passed.
Cairo map_check:3 scales, равное покрытие точек, land/ocean, shimmer/static, общий
geography hash; dial callback, enabled-state, ON/OFF renders passed. Рендеры просмотрены:
[главная](../assets/desktop-map-dial/linux-status.png),
[карта](../assets/desktop-map-dial/linux-route.png),
[круг ON — синтетика](../assets/desktop-map-dial/linux-dial-on.png).
8 packaging/QR tests passed, включая extracted RNS lifecycle: в sandbox socket
запрещён, стандартный outside-sandbox прогон passed. .NET10.0.401 Release cross-build
0errors/0warnings; это не замена Windows runtime.

CI f2c7d94: Linux client job106050001875 в run35500009763 success, включая native
map,24 layouts, Friends QR, recovery, TCP installer, archive. Первое падение Linux
в1ba7269 устранено явным python3-gi-cairo. Windows1ba7269 отменён новым запуском.
CI c75f563 run35500441063: Linux client job106051148589 success; Linux control
run35500440984/job106051148539 success. Windows job106051148717 **success**, включая
install/service/driver/broker/UI/layout/circle callback/busy disable/uninstall.
[Платформенный CI](https://github.com/Joker20380/family_connect/actions/runs/35500441063).
Windows artifact10602077203,49494918bytes, ZIP SHA256
`479253b259ae0c8cd65ff9110405f6a58dcb2650cce15a3b2486917eca2628a2`,
expires2026-12-19; внутренний unsigned installer0.2.9, пользовательскому ПК не установлен. Android setup-android failure прежний, Androidbeta25
на телефоне не менялся. Public release не публиковался.

Установленный Linux paired bundle:
`cce586a74c3911083b3df7c6e5ac31bd1aeac480563a082ddbb98a0463745a81`,
archive `/tmp/fc-dial-preview/artifacts/FamilyConnect-Control-Linux-preview-cce586a74c391108.tar.gz`,
SHA256 `9d52304fa105978aaa1b93abfd0af450b04a963dd83f3c4418744f3564053c7f`.
Launcher: `~/.local/share/family-connect/control-previews/cce586a74c391108/FamilyConnect-Control-preview/scripts/run_control_preview.py`.
Существующий venv `control-previews/5a9ca444046993a7/venv/bin/python` используется
GUI и core; requirements.lock побайтно совпал. Manifest и import GI/Cairo/httpx/RNS
проверены. Оба ярлыка family-connect.desktop и скрытый com.familyconnect.Client.desktop переключены, systemd user unit
family-connect-dial-20260920 active. Runtime renderer env overrides не задавались.
Перед обновлением не было активного VPN; keys/profiles/state/helpers не менялись.

Предыдущий map-only bundle aa45ec3b42b8a11a (source1ba7269) был установлен в этой
сессии; затем заменён circle bundle. SHA256 map-only archive
`28f2bdf7f3416b9b8a555695a3a17f347b8246174e40ba0f95e3e86de193d004`.
Предыдущее окно уже закрыли до второго запуска, systemctl stop returned5 (unit gone);
это проверено, установленный комплект не пересобирался, новый GUI запущен отдельно.
Rollback: закрыть GUI штатно, восстановить ярлык из
`state-client-build/desktop-dial-20260920/family-connect.desktop.previous` для map-only,
или `state-client-build/desktop-map-20260920/family-connect.desktop.previous` для
5a9ca444046993a7. Скрытый ярлык панели задач также восстановить из
`state-client-build/desktop-dial-20260920/com.familyconnect.Client.desktop.previous`. Все прежние bundle и venv сохранены. Не удалять application journal.
Проверенная ранее QR5002579 впервые доставлена с этими bundle; six-file standalone
контракт сохранён — Linux geography встроена в app.py. Windows geography embedded
resource clients/assets/land.json; NOTICE рядом. Cairo добавлен в список зависимостей
инструкций, installer preflight и paired launcher.

Открыто: ручной Windows-пилот (ПК пользователя недоступен),
пользовательская оценка Linux, desktop zoom/pan/реальный маршрут, отдельная доработка
анимации. Live VPN через новый круг не запускался. Публичные Linux/Windows/Android
релизы неизменны; новый offline-signed update catalog не создавался.

Cairo preflight/installer и control CI обновлены в96016ee; это не меняет
установленный c75f563 UI. Windows код также прежний. Полные PNG проверяются
отдельным Desktop render review: стандартные мелкие notice-части были обрезаны
лимитом аннотаций GitHub, прямой artifact API вернул401. Review скачивает готовый
артефакт с read-only Actions token и читает только PNG, ничего из installer не исполняет.

Полные PNG исходника c75f563 восстановлены из Desktop render review35501080216
(job106052845837), просмотрены. [Круг Windows](../assets/desktop-map-dial/windows-status.png).
Просмотр карты выявил GDI+ смещение сглаживания мелких точек. Исправление0f12923:
PixelOffsetMode.Half для cached dot bitmap, новый native pixel-coverage check при
scale1/2/3. Запущен отдельный Desktop visual checks без сборки VPN-драйверов;
Windows код до этого прошёл полный installer/service/UI CI c75f563.

Windows0f12923 native coverage check в run35501211259/job106053180401 выявил,
что PixelOffsetMode.Half недостаточно: peak alpha<180. Исправление21b740a:
единый supersampled8×8 круговой stamp для каждого физического диаметра,
SetPixel вместо GDI+ FillEllipse, NearestNeighbor при переносе cache1:1.
Проверка3scale сохраняется; opacity/spacing/география не менялись.
Final native Windows UI run35501348376/job106053540123 **success**; полный
installer run35501348219 также запущен. Ранее успешный installer c75f563 содержит
предыдущую отрисовку точек и не должен выдаваться за финальный21b740a.

Итоговые native Windows рендеры21b740a просмотрены: точки чёткие и одинаковые,
штрихи устранены; главный круг соответствует принятой сегментной геометрии.
[Windows карта](../assets/desktop-map-dial/windows-route.png),
[Windows круг](../assets/desktop-map-dial/windows-status.png).
[Финальный нативный UI CI](https://github.com/Joker20380/family_connect/actions/runs/35501348376):
проверка pixel coverage1/2/3, layout1/1.5/2/2.5, circle callback/busy disable,
Friends UI и state/polling passed. PNG восстановлены полностью (37403/20758bytes).
На компьютере пользователя Windows не установлен: он недоступен; следующая ручная
приёмка и получение финального installer21b740a остаются открыты. Linux уже установлен
cce586a74c391108, оба ярлыка обновлены, прежний комплект сохранён для отката.
