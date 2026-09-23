# Desktop: восстановление Friends TCP и тонкий Linux UI — 2026-09-20

Пользователь разрешил продолжить основные desktop-задачи. Предыдущий Linux UI
отклонён как грубый и непохожий на Android. Новый ориентир: Android beta19,
тонкие линии и аккуратная композиция. Новая анимация в духе «Бункера» отложена
по прямому указанию пользователя; в этом этапе индикатор статичный.

## Исходники и поставка

Отдельная ветка desktop/friends-access-20260919:
- 6206b60: высота видимой Windows-страницы и контекст layout failures.
- 337b2a0: проверка геометрии по строкам и на заданном размере окна; полный PNG
  CI передаётся в отдельных public annotations без прежнего обрезания.
- f8c10c0: Linux Friends TCP apply/recovery, новая композиция GTK и контроль
  полного текста Windows-навигации.
- b9a2b4a: обязательные Friends-зависимости в paired GUI, проверка извлечённого
  Friends UI и интеграционный тест signed HTTP → cache → apply.

Корневой main остаётся3f6f662 с сохранёнными накопленными изменениями. Public main
по предыдущему опубликованному checkpoint —d87f30d. Android0.1.18-beta19/code19,
public desktopv0.2.9, tcp-v0.1.0/tcp-setup-v0.1.0 остаются прежними.
Новых установок, server changes, GitHub release или signed catalog нет.
Версия0.2.9 на тестовых снимках обозначает source version, не обновлённый релиз.

## Windows

После переноса language в настройки FitWindow прибавлял высоту всей content-панели
вместо нижней навигации. Исправлены ссылка на footer и порядок ApplyPage перед fit;
ширина текстов вторичных страниц теперь также ограничена доступной областью.
Диагностика6206b60 локализовала `Clipped or overlapping content`: settings/RU/100%,
row5 Friends button y135, previousBottom350. Обход Controls шёл не в порядке строк
TableLayoutPanel. Проверка теперь сортирует по строкам, сохраняя запрет пересечений
и выходов за границы. Тест после auto-fit заново выставляет проверяемый viewport.

Полные PNG на337b2a0 иf8c10c0 получены и просмотрены. На нём обнаружен обрезанный текст
«Мессенджер» внутри кнопки. Наf8c10c0 сокращены внутренние отступы навигации,
облегчён шрифт и добавлена проверка измеренной ширины/высоты всего названия.
Финальные Windows build/install/broker/UI/layout — success в35490043368.
[Windows CI-рендер](../assets/desktop-refined/windows-status.png).

## Linux

Главный экран повторяет структуру Android: шапка, крупный круговой VPN-индикатор,
статус и переключатель в одной карточке, нижние вкладки с контурными иконками.
Контуры0.8 logical px, компактные срезы, обычное начертание вместо жирного;
SVG rasterization учитывает scale factor. Индикатор отражает реальное состояние
туннеля и не имеет таймера; это не новая Silo-анимация и не подтверждение Internet health.
Постоянная навигация остаётся внизу при изменении высоты окна.

[Статус](../assets/desktop-refined/linux-status.png) ·
[Настройки](../assets/desktop-refined/linux-settings.png) ·
[Маршрут](../assets/desktop-refined/linux-route.png) ·
[Мессенджер](../assets/desktop-refined/linux-messenger.png).
Снимки настоящего GTK в Xvfb, тестовые данные, без сетевых операций/личных профилей.
Оценка нового внешнего вида пользователем ещё не получена.

Окно Friends теперь подключает TCP выбранной страны. Проверенный ответ сначала
сохраняется с sequence floor, затем выполняются import/connect/Internet health.
FriendsApplication использует существующий backend control_transaction и durable
operation owner. Журнал в0700/0600 identity store содержит только публичные ID
и inventory предыдущего состояния; профили/ключи в него не дублируются.

Перед изменениями сохраняется baseline. Неуспешный apply отключает новый туннель,
восстанавливает предыдущий и проверяет его health. После смерти процесса startup
сначала завершает rollback. Неудачный rollback/повреждённый journal сохраняет блокировку
обычных операций; committed VPN при обычном перезапуске не откатывается.
HTTP denial не приводит к применению cached профиля. Одновременные GUI-операции
заблокированы; закрытие Friends во время работы запрещено. На закрытии main обновляет
список и выбирает активный профиль. Старые неактивные импортированные профили
сохраняются, автоматическая очистка не реализована.

Friends TCP доступен в paired bundle с ядром. Шестифайловый standalone archive
по-прежнему содержит только app/backend/profile_config/updates/update.pub/install-linux;
новое ядро не добавляется незаметно в старый updater. Native AWG3.1 пока недоступен
в Friends desktop — parser acceptance не равна поддержке установленного engine.

Найдена и закрыта ошибка упаковки: прежний launcher запускал GUI системным Python,
где не было httpx/RNS; ImportError скрывал кнопку Friends. Теперь paired launcher
проверяет GI и Friends dependencies до запуска. Runbook и extracted CI используют
venv системного Python с --system-site-packages и provisioning/requirements.lock.
Standalone по-прежнему самодостаточен. [Запуск и recovery](../linux-control-preview-rollout.ru.md).

## Проверки

- Полный Python:620 passed,2 upstream deprecation warnings,14.09s вне песочницы.
  Sandbox RNS sockets запрещены; TestClient был остановлен и набор повторён
  вне sandbox согласно AGENTS.md.
- 16 scoped tests: owner/configuration и15 новых lifecycle-сценариев. Успех,
  import/disconnect/connect/health failures, прерывание процесса на4 стадиях,
  блокировка параллельной операции, HTTP denial, повреждение журнала,
  ошибка commit write и повтор recovery после неудачного rollback.
- GTK/D-Bus/Xvfb, явно GDK_BACKEND=x11:24 layout cases RU/EN,100–250%, state/poll/
  confirmation passed. Первый запуск без явного X11 потерял keyboard focus
  на150%; повтор в изолированном X11 прошёл, проверка фокуса сохранена.
- GTK Friends activation/referral/configuration/TCP, busy-close, parent startup
  recovery/modal lock/active selection passed, synthetic backend/HTTP only.
- GTK recovery threshold/stale intent/disconnect и TCP installer confirmation,
  cancellation, missing bootstrap, connected/busy guards passed.
- .NET10 cross-build:0 errors/0 warnings; Windows runtime проверяется отдельно.
- [Client builds35490043368](https://github.com/Joker20380/family_connect/actions/runs/35490043368):
  Windows и Linux jobs completed/success наf8c10c0, release skipped.
- [Linux control35490344947](https://github.com/Joker20380/family_connect/actions/runs/35490344947)
  completed/success наb9a2b4a, включая финальное окружение/распакованный Friends UI.
- Финальные local package/owner/lifecycle:19 passed; extracted GUI smoke passed.
  Расширенный owner-test проводит реальный подписанный fixture через mocked HTTP,
  durable cache и apply; после HTTP403 повторный import не выполняется.
- AWG native35490043292 и TCP pilot35490043423 наf8c10c0 success.
  Windows native TCP35490043369 также completed/success (проверено перед завершением).
  Phase035490344945: tests success, failover failed на Build isolated failover stack;
  причина Docker build в этой задаче не разбиралась. Общий набор workflows не зелёный.
- Android в общем Client builds снова failed на setup-android до компиляции;
  APK не пересобиралась/не менялась. Весь workflow не объявляется зелёным.
- Source paired archive: FamilyConnect-Control-Linux-preview-d02f1c6f740137d6.tar.gz,
  79881 bytes, SHA256800f28a42e16d1fede433fd875ac7e1b389a4671e3ee1e9ae4be623698472101.
  Название и SHA256 побайтно совпадают с Control preview SHA256 в CI35490344947.
  Standalone archive создан локально; состав ровно6 файлов. Ни один не опубликован.
- git diff --check passed. Сетевой VPN на пользовательском Linux/Windows в этом
  этапе не включался; макеты и fake backend не заменяют такую приёмку.

## Далее и rollback

Windows CI/render наf8c10c0 закрыт. Далее native AWG3.1 и /16, живое Friends TCP на Linux/Windows, desktop messenger/QR/карта,
межплатформенные/restart/update проверки и новая immutable версия с offline signing.
Повторный публичный выпуск v0.2.9 запрещён. Android beta19 и GIF остаются прежними.

Rollout пока отсутствует. Откат source-этапа — reviewed revert указанных коммитов
в desktop-ветке, не reset корневой папки. Если новая версия уже применяла Friends,
сначала закончить её recovery; нельзя удалять friends.application journal,
identity/cache/marker или operation state ради снятия блокировки. Сохранить DB,
ключи и sequence floors. Будущий клиентский откат — штатный previous/новая версия
с повышенным sequence; не подмена опубликованных бинарников.
