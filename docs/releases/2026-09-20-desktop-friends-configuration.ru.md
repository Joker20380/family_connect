# Desktop Friends configuration — 2026-09-20

Продолжение задачи довести Linux/Windows до текущих пользовательских сценариев Android.
Это промежуточный этап, не готовые новые приложения.

Реализованы Python/C# проверка invite-test schema2, Ed25519 domain/signature,
привязка ответа к устройству/стране, материализация TCP и AWG3.1, общий sequence floor
между RU/NL и отказ изменённого payload при том же sequence. Добавлены HTTP configuration
методы. Linux parser принимает AWG3.1 только с явным allow_awg31; старые вызовы и native
workers не объявлены совместимыми с3.1.

Linux owner сохраняет ответ в0700/0600 POSIX файлах, общий flock, fsync и atomic replace.
Windows vault использует DPAPI владельца, SID entropy, marker и atomic replacement.
Проверенный ответ сохраняется до возврата профиля. Повреждение/частичная потеря cache
не вызывает новый fetch; HTTP denial не подменяется offline cache. Это не VPN apply journal
и не защита от отката всего каталога привилегированным атакующим.

Проверки:36 общих signed-catalog vectors, HTTP assignment/rejection, Linux recovery,
concurrency/global floor, прерывание записи и отказ доступа.81 scoped Python passed;
полный Python604 passed/2 upstream warnings (15.35s). .NET protocol suite passed,
включая36 vectors. Windows app cross-build:0errors/0warnings. DPAPI runtime локально
на Linux явно skipped; новый Windows CI ожидается.

Отдельная ветка desktop/friends-access-20260919, коммит65c3e9d,16 файлов;
main не менялся. Windows control CI35472029602 и Client builds35472029576 в работе.
Предыдущий CI429eb77:Windows/Linux passed, Android SDK setup failed, release skipped.

Версии без изменений: Android0.1.18-beta19/code19, desktop publicv0.2.9.
Ни APK, ни пользовательские установщики, ни gateways, ни signed catalogs не менялись.
Откат разработки — отдельный revert65c3e9d в desktop-ветке; реального rollout нет.
Для будущей установки нельзя удалять marker/ключи ради сброса sequence; нужен согласованный backup/recovery.

Остаются:Windows DPAPI CI, подключение owner к broker/GTK, совместимость nativeAWG3.1
и адресов /16, apply/recovery lifecycle, desktop UI/QR/мессенджер/packaging,
живые Linux/Windows проверки, in-place update и новый immutable release.


## Проверенный следующий checkpoint

После65c3e9d добавлены Windows Friends UI и broker TCP path (1f26ae6),
явные зависимости изолированного native broker (4200535), paired Linux owner
и GTK окно приглашений (e796dbf). Linux пока получает и сохраняет configuration;
подключение VPN из окна Friends ещё не реализовано. Windows использует существующий
TCP lifecycle; native AWG3.1 ещё требует отдельной реализации/проверки.

Python:605 passed,2 upstream warnings. Windows control35472029602 и35472376415
success; DPAPI выполнялся в Windows. Clients35472376423 и35472900915: Windows/Linux
success, Android failed на setup-android до компиляции. Native TCP35472664774
success после исправления explicit source includes. Phase0 наe796dbf: tests success,
failover failed при Build isolated failover stack; причина Docker build не установлена.
GTK окно приглашений: mock activation/referral/configuration passed; paired import
и открытие окна также проверены. .NET protocol suite и app/broker cross-build passed.

Визуальное продолжение описано в [отдельном отчёте](2026-09-20-desktop-terminal.ru.md).
Rollout отсутствует; публичные версии прежние. Откат этих исходников — revert
соответствующих коммитов в desktop-ветке, без удаления identity/cache/marker.
