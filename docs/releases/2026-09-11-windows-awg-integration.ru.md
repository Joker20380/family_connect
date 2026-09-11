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

Завершено 2026-09-12. Приложение/source ad30827; исправление стенда/source53fe266.
Локально:325 Python tests passed (включая25 issuer),2 dependency deprecation warnings.
[Client CI](https://github.com/Joker20380/family_connect/actions/runs/34652500879) прошёл
Windows/Linux/Android,504 Windows layouts, AWG-only/cancel interaction, установку,
проверку payload/hash/license/отсутствия CI peer и удаление.
C# shared fixture и16 rejection checks прошли. [phase0](https://github.com/Joker20380/family_connect/actions/runs/34652500921) прошёл.
[AWG CI](https://github.com/Joker20380/family_connect/actions/runs/34652500922): native12/12 UDP,
4 negative probes,4 cleanup; actual LocalSystem24/24 UDP IPv4/IPv6 за24 отправок,
4 cleanup scenarios: disconnect, engine crash/recovery, broker crash/SCM cleanup,
cancel-start. Подпись/DPAPI/replacement/rollback, SID ownership и взаимное исключение
транспортов проверены. Успешное переключение нескольких реальных профилей и auto fallback
этот стенд не проверяет.
[TCP regression](https://github.com/Joker20380/family_connect/actions/runs/34650231930) на том же
production-коде ad30827:84/84 HTTP,14 DNS,10 cleanup scenarios; health recovery/cancel passed.
После ad30827 менялись только AWG CI fixture/harness и документация.
Скачанные AWG/Wintun сверены; installer SHA256: `1fc8686373fa822fc44e142ec8730cfc1816b4c59b9a761563e1a87c30fd47bb`.
[Машинные результаты](2026-09-12-windows-awg-result.json),
[инструкция](../windows-awg.ru.md). Превью интерфейса просмотрено.

Первоначальные AWG runs34650232595/34650685249/34651112753/34651674223 провалили
обмен после engine crash. Повторы UDP не исправили сбой. Счётчики показали остановку
приёма синтетического Windows RIO peer: Failed to receive, handshake count остаётся2,
при корректных новых адресах/маршрутах клиента. Попытка заменить backend на StdNetBind не прошла базовую native-проверку
(CI34652257938) и убрана. Исходный RIO оставлен, CI peer теперь продолжает приём
после конкретного WSAECONNRESET и считает такие события. Успешный run зафиксировал
5 таких ошибок; число принятых handshake выросло с2 до3 после восстановления,
все24 UDP-проверки прошли с первой отправки. Клиентский worker и его hash
не менялись. Предполагаемый сетевой триггер — ICMP закрытого порта; пакет ICMP не снимался.
[Неудачные результаты сохранены](2026-09-12-windows-awg-diagnostics.json).
Это исправление Windows-стенда, действующий Linux gateway не менялся.

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
