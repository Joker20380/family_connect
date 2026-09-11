# Windows AWG: профиль, служба и интерфейс — 2026-09-11

После успешного [движка](2026-09-11-windows-awg-engine.ru.md) AWG включён в код
Windows приложения и installer. Подписанная .fcawgactivation привязана к FC1-коду,
отдельный Ed25519 domain windows-awg-activation/v1, последовательность запрещает
rollback/изменение на прежнем sequence, повтор идентичного профиля допускает иной
порядок параметров JSON. Дубликаты/неизвестные поля отвергаются. Срок — дедлайн
импорта; уже принятый профиль работает офлайн. Закрытый ключ генерируется на
Windows и не включается в активацию. Профиль хранится в LocalSystem DPAPI, доступ
по аутентифицированному SID. Issuer: scripts/activate_windows_awg.py.

Broker activate-awg/connect-awg/status.awgReady, общий владелец/блокировка WG/TCP,
проверка закреплённых hashes worker/Wintun, JobObject до stdin EOF, запуск bound UDP.
Общая с TCP сессия создаёт fcawg-адаптер, адреса10.78.0.N/fd78:92::N, split defaults,
DNS1.1.1.1 и собственное NRPT. В журнал добавлен необязательный AWG number;
старый TCP journal читается как прежде. Cleanup, crash recovery, отмена, health и
три повтора15/30/60s используют существующий механизм. Код ошибок tcp-* пока общий
для обоих движков; пользовательские тексты сделаны общими для VPN.

GUI: выбор WireGuard/TCP/AWG, отдельный файл активации, AWG без WG-профиля,
отмена pending, блокировка смены транспорта до остановки. Переключение явное:
отключить → выбрать транспорт → подключить. Автоматического WG→AWG→TCP пока нет.
Installer содержит только принятый worker/Wintun и лицензии/manifest, без CI peer.

## Проверки

25 Python issuer checks прошли локально. Windows/platform/TCP regression CI ожидается.
Добавлены C# shared fixture,16 отказов, порядок replacement и UAPI serialization;
504 GUI layouts и AWG-only/cancel interaction. Installer checks проверяют hashes,
лицензии, отсутствие peer fixture и удаление worker. Actual LocalSystem AWG CI:
подписанный импорт/rollback, передача IPv4/IPv6 через memory-TUN peer, чужой SID,
запрет одновременных транспортов, crash recovery, restart cleanup и отмена запуска.
Синтетический peer отвечает только UDP echo: AWG HTTPS health/full routing этим
стендом не принимаются. TCP regression проверяет общий механизм отдельно.

## Ограничения и версии

Внешний AWG/REALITY, полный маршрут и production HTTPS health требуют отдельной
приёмки до выпуска. Это implementation/CI preview, не установленный стабильный VPN.
PSK-профили не поддержаны этой схемой; поддержаны проверенные AWG2 J/S/H/I-параметры,
Jc/Jmin/Jmax положительные (ограничение закреплённого engine), номер4..254.
Kill switch отсутствует; при очистке/ожидании могут использоваться обычные маршруты.
User-device/load тесты и Android APK update отложены.

Desktop0.2.9/source42f9d32/catalogseq8 опубликован без этой интеграции. Linux0.2.7,
последний подтверждённый Windows0.2.7; server0.2.1, TCP component/Setup0.1.0.
Нового релиза, установки на устройства, изменения gateway/пиров/подписей нет.
Выпуск: полная приёмка, новая версия, platform CI и сверка скачанных артефактов,
подпись каталога офлайн. Откат: Disconnect, предыдущий проверенный installer;
DPAPI-профили сохраняются. При cleanup-required сначала восстановить службу/сеть,
не удалять журнал вручную.

Остаток Windows: автоматическая политика переключения и её приёмка. Далее Android
AWG/TCP, затем этап5 Reticulum. Отложенные физические тесты не запускаются автоматически.
