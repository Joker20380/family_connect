# Windows TCP: сетевая сессия в LocalSystem broker

Дата: 2026-09-11. Этап4, продолжение после process-lifetime приёмки.

Добавлены TcpSession, встроенный TcpNetwork.ps1 и общий ProcessJob. Broker получил
`connect-tcp`, асинхронный startup/cancel, transport status, контроль SID, запрет
совместного WG/TCP и замены активного профиля. Сетевая сессия использует ранее
проверенные DPAPI-профиль, подпись/sequence и закреплённые Xray/Wintun hashes.

Журнал до изменений, собственные IPv4/IPv6 routes/DNS/NRPT, завершение дочерних
процессов через job, очистка на disconnect/crash/SCM restart реализованы.
SCM recovery настроен на restart1/5/10s, startup очищает старый журнал до открытия
IPC. Полный [runbook и ограничения](../windows-tcp-session.ru.md).

Проверки выполняются на disposable Windows runner. Отдельная сборка реальной службы
под LocalSystem меняет только фиксированные тестовые маршруты/домен и локальный VLESS.
Проверяется работа OS resolver через UDP, HTTP через IPv4 и IPv6, запрет действий
другой обычной учётной записи, остановка/сбой/перезапуск/отмена и восстановление настроек.
Стандартная сборка включает REALITY и split-default routes; этот полный внешний путь
здесь не проверяется. Пользовательские сетевые/нагрузочные тесты остаются отложенными.

Первый exact CI9f32b0c: все client platforms и phase0 прошли; native lifecycle прошёл,
но новый session-test остановился до подключения при создании второй тестовой учётной
записи через PowerShell. В6d207a2 подготовка заменена прямыми NetUserAdd/
NetLocalGroupAddMembers/NetUserDel API; пароль не передаётся в argv/логи.
Причина первоначального PowerShell-сбоя не установлена: stderr не был сохранён.

## Подтверждённый итог

Реализация9f32b0c, исправленный тест6d207a2:
[Windows native/session CI34639769072](https://github.com/Joker20380/family_connect/actions/runs/34639769072)
и [phase0 CI34639769135](https://github.com/Joker20380/family_connect/actions/runs/34639769135) — success.
[Client CI34639148397](https://github.com/Joker20380/family_connect/actions/runs/34639148397)
для реализации9f32b0c: Windows, Linux, Android success; после него изменялся только
изолированный Python test harness. C# profile/uplink serialization, установка,
реальная служба/DPAPI, UI/layout и uninstall прошли. Release job не запускался.

| Сценарий службы | HTTP IPv4 | HTTP IPv6 | Системный DNS | Чужой SID заблокирован | Очистка |
|---|---|---|---|---|---|
| Disconnect | 3/3 | 3/3 | Да | Да | Да |
| Xray crash | 3/3 | 3/3 | Да | Да | Да |
| Broker crash + SCM restart | 3/3 | 3/3 | Да | Да | Да |
| Service stop/start | 3/3 | 3/3 | Да | Да | Да |
| Cancel startup | Не запускался | Не запускался | Не проверялся | Не проверялся | Да |

Итого24/24 HTTP-запроса, четыре DNS-проверки через Windows resolver; во всех пяти
сценариях сохранены default routes/DNS/NRPT, отсутствуют TUN/тестовые маршруты,
дочерний Xray и журнал. После падения Xray возвращается ожидаемый tcp-engine-exited.
После смерти брокера cleanup выполнен до открытия IPC новой службой. Пользовательские
профили/ключи не использовались; тестовая учётная запись и служба удалены.

Предыдущая native lifecycle приёмка тоже прошла18/18, включая tamper rejection.
Native artifact скачан, SHA256 обоих бинарников повторно сверен с manifest.
[Машиночитаемые результаты](2026-09-11-windows-tcp-session-result.json).
Операторский архив: ignored `state-client-build/session-2026-09-11-windows-tcp-session`.

## Версии и продолжение

Desktop published0.2.9, installed Linux0.2.7, Windows last reported0.2.7;
server0.2.1, TCP component/Setup0.1.0. Релиза, установки на устройство или серверного
развёртывания не выполнялось. CI installer с номером0.2.9 не заменяет immutable release.

В обычном installer пока нет каталога tcp с движком; API в таком случае отвечает
`tcp-engine-missing`. Дальше упаковка/UI/восстановление соединения и Windows AWG;
REALITY/full-routing platform acceptance до распространения. Затем Android и Reticulum.

Откат на устройствах не нужен. При отмене разработки убрать новую session integration
из будущего клиента. Существующие WG-профили, TCP DPAPI-профили и private keys сохранены.
Тестовая служба и учётная запись удаляются; тестовый журнал исчезает после очистки.
Операторские результаты архивируются локально в ignored state-client-build.
