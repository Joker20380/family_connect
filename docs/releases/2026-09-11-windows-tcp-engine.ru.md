# Windows TCP: нативный движок и изолированная приёмка

Дата: 2026-09-11. Этап 4, первая часть Windows TCP.

Добавлены `pilot/windows-tcp/build.ps1`, `check.py` и отдельный Windows workflow.
Сборка фиксирует Xray `d2758a023cd7f4174a5a5fa4ff66e487d4342ba0`, Go 1.26.1,
Windows amd64 и официальный Wintun 0.14.1. SHA256 ZIP проверяется до распаковки,
Authenticode DLL — до упаковки. Лицензии и manifest включены в CI artifact.

Проверка создаёт настоящий Wintun и маршрут только к `198.18.0.1/32`.
Локальный VLESS передаёт синтетические HTTP-запросы локальному HTTP-серверу;
два новых запуска, по шесть запросов с проверкой содержимого ответа.
После принудительной остановки проверяются удаление адаптера/тестового маршрута,
сохранность основных IPv4/IPv6 маршрутов и DNS.

Первый CI `34623409778` собрал движок, но проверка завершилась до сохранения отчёта.
В `13441d8` исправлена обработка ожидаемого пустого PowerShell-запроса и добавлено
сохранение traceback/acceptance.log. Второй CI `34629087507` дошёл до адаптера,
но bind завершился WinError 10049; очистка, DNS и основные маршруты прошли.
В `ba929a0` фиксированная пауза заменена ожиданием AddressState=Preferred.
Windows допускает использование нового адреса только после завершения DAD:
[Microsoft New-NetIPAddress](https://learn.microsoft.com/en-us/powershell/module/nettcpip/new-netipaddress).

## Подтверждённый результат

Source `ba929a07` (полный SHA доступен в CI),
[Windows native CI 34629412460](https://github.com/Joker20380/family_connect/actions/runs/34629412460)
и [phase0 34629412479](https://github.com/Joker20380/family_connect/actions/runs/34629412479)
завершились успешно. Скачан artifact `FamilyConnect-Windows-TCP-engine-preview`;
хеши обоих бинарников проверены повторно локально по manifest.

- Два запуска, 12/12 локальных HTTP-запросов через TUN/VLESS.
- В обоих запусках адрес Preferred; принудительная остановка и удаление адаптера прошли.
- Основные IPv4/IPv6 маршруты и DNS не изменились, тестовый маршрут отсутствует.
- Xray SHA256: `74475d8c4f68dd07bef754e56778eb2a9061e4dfcc954fa008b912a989bd848a`.
- Wintun DLL SHA256: `e5da8447dc2c320edc0fc52fa01885c103de8c118481f683643cacc3220dafce`.
- Синтаксис Python и `git diff --check` прошли. Общие platform jobs не запускались:
  стабильные клиенты этим шагом не изменены.

[Сохранённый результат CI](2026-09-11-windows-tcp-engine-result.json).
Операторский архив: ignored `state-client-build/session-2026-09-11-windows-tcp-engine`.

## Границы и продолжение

Это проверка Windows TUN/VLESS на изолированном CI runner. REALITY, внешний VPN,
AWG для Windows, брокер LocalSystem, импорт/защита профиля, общий маршрут/DNS,
автоматическое переключение и физическое устройство здесь не проверены.
Следующий шаг: управление TCP через Windows broker с защищённым хранением
и проверкой REALITY-профиля, владением процессом и восстановлением сетевых настроек.

Стабильный installer и подписанные каталоги не менялись, нового релиза нет.
Published desktop 0.2.9, TCP component 0.1.0, TCP Setup 0.1.0; установленный Linux
0.2.7, Windows последний раз сообщён 0.2.7. Сервер 0.2.1 без изменений.
Пользовательские сетевые/нагрузочные проверки и обновление Android отложены.
CI preview не устанавливается через updater; откат на устройствах не требуется.
Для отмены этого шага исключить новый workflow/pilot из будущей сборки;
установленные версии и существующие immutable releases сохраняются.

Источники: [Wintun](https://www.wintun.net/),
[Xray Windows TUN, фиксированная ревизия](https://github.com/XTLS/Xray-core/blob/d2758a023cd7f4174a5a5fa4ff66e487d4342ba0/proxy/tun/tun_windows.go).
