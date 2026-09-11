# Windows TCP: обнаружение потери связи — 2026-09-11

Добавлен монитор установленной сессии: через 15 секунд после настройки и затем
через 15 секунд после каждого цикла выполняются две параллельные проверки с
тайм-аутом 8 секунд. Успех любой сбрасывает счётчик; два подряд неуспешных цикла
запускают существующее восстановление (cleanup → 15/30/60s, максимум три повтора
на явное Connect). Общий бюджет используется и для падения Xray, и для health failure.
Монитор отменяется и ожидается перед удалением адаптера. Stop/Disconnect прекращают
также DNS/connect/чтение текущей пробы. UI использует существующий статус восстановления.

Production: HTTPS https://1.1.1.1/cdn-cgi/trace (200 + корректное ip= в теле до4096байт)
и https://www.gstatic.com/generate_204 (204). Стандартная TLS-проверка сохраняется,
redirect/proxy/cookies выключены, адреса фиксированы в коде. Сокет IPv4 привязан к
исходному адресу TUN и его IP_UNICAST_IF, без fallback на другой адаптер. DNS имени
использует системный resolver/NRPT. Успех IP-пробы не доказывает исправность DNS
или IPv6; это ограниченная проверка достижимости, не гарантия всего интернета.
Основания: [Microsoft ConnectCallback](https://learn.microsoft.com/en-us/dotnet/api/system.net.http.socketshttphandler.connectcallback?view=net-10.0),
[Microsoft IP_UNICAST_IF](https://learn.microsoft.com/en-us/windows/win32/winsock/ipproto-ip-socket-options).

## Проверки

Локально Python harness компилируется, git diff --check прошёл. Первый Windows CI34645816684 остановился при компиляции: .NET enum SocketOptionName
не содержит UnicastInterface. Исправлено на Windows IP_UNICAST_IF=31 с прежним
network-byte-order индексом; политика binding не ослаблялась. Повторный CI исходника **9863427** прошёл:
- [Client builds34646258699](https://github.com/Joker20380/family_connect/actions/runs/34646258699): Windows/Linux/Android success, release skipped; установленный payload/broker, UI336 layouts и uninstall.
- [Native/session34646258684](https://github.com/Joker20380/family_connect/actions/runs/34646258684): lifecycle18/18, session 84/84 HTTP, 14 OS DNS, 10 cleanup scenarios, health recovery и отмена текущих проб success.
- [phase0 34646258740](https://github.com/Joker20380/family_connect/actions/runs/34646258740): success.

Артефакты скачаны, engine сверён с manifest; installer SHA256SUMS проверен:
`f5df2ff522cbb476dacf2e16b27d7510ddc482b4fe036e74f5d831cc51080f29`. CI-снимок окна просмотрен.
[Машинный результат](2026-09-11-windows-tcp-health-result.json).

Синтетический TCP_SESSION_TEST использует два локальных HTTP пути через scoped TUN/VLESS,
тот же binding/timer/retry код. Не подменяет production TLS-проверку. Добавлены сценарии:
отказ одной цели не перезапускает сессию, отказ обеих при живом Xray вызывает
восстановление с новым адаптером и передачей IPv4/IPv6/DNS; отмена при зависших пробах
останавливает монитор без последующего фонового опроса. Прежние lifecycle/ownership/
retry exhaustion и default-route/DNS cleanup проверки сохранены. User-device/load
тесты остаются отложены, gateway не менялся.

## Дальше и выпуск

Следующая реализация — Windows AWG и переключение транспортов, затем Android AWG/TCP,
после интеграции Android — этап5 Reticulum. Внешний REALITY/полный маршрут/production
HTTPS probes ещё требуют отдельной приёмки до распространения. Kill switch нет;
во время очистки и пауз работают обычные маршруты. Status on означает настроенный
туннель, первый health цикл ещё может не завершиться.

Версии не менялись: published desktop0.2.9/source42f9d32/catalogseq8, установленный
Linux0.2.7/последний подтверждённый Windows0.2.7; server0.2.1, TCP component/Setup0.1.0.
Нового релиза/установки на устройства нет. CI installer0.2.9 не должен заменять
опубликованный0.2.9. Выпуск: приёмка полного маршрута, новая версия, CI и проверка
скачанных артефактов, подпись каталога офлайн. Возврат: Disconnect и предыдущий
проверенный installer, профили сохраняются; при cleanup-required сначала восстановление
по [журналу](../windows-tcp-session.ru.md), журнал не удалять вручную.
