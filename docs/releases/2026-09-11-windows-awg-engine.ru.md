# Windows AWG: собственный процесс движка — 2026-09-11

Начат следующий блок Windows AWG и переключения транспортов. Закреплён тот же
amneziawg-go `1cc94272ca8e9e223a5fe76382f5880f09d3c12d`, что в Linux/gateway pilot.
[Upstream Windows main](https://github.com/amnezia-vpn/amneziawg-go/blob/1cc94272ca8e9e223a5fe76382f5880f09d3c12d/main_windows.go)
является отладочной программой с отдельным UAPI. Вместо неё реализован worker для
будущего запуска службой: ограниченный stdin JSON, конфигурация только после EOF,
новый TUN, привязка внешнего UDP к uplink перед использованием сокетов, без публичного
UAPI. JobObject назначается до передачи конфигурации. Внешний транспорт IPv4,
внутренние пакеты IPv4/IPv6; IPv6 внешний сокет blackhole. Worker не меняет маршруты/DNS.

Сборка: Go1.26.1 Windows amd64, CGO=0, trimpath/buildvcs=false/пустой buildid;
официальный Wintun0.14.1 с SHA256 ZIP/DLL и проверкой Authenticode издателя.
Манифест содержит revision, hash исходника wrapper и хеши бинарников/лицензии.
CI-only memory-TUN peer возвращает UDP-пакеты через настоящий зашифрованный AWG2;
он не создаёт адреса назначения в Windows и не маршрутизирует трафик наружу.

## Проверки

Локально синтаксис Python и diff --check. Windows native CI ожидается.
Проверки: IPv4/IPv6 echo через AWG2, S1-S4/H1-H4 ranges/I1, неправильный H1 и чужой
server public key не дают ответа; остановка движка и убийство владельца убирают
процесс/адаптер/маршруты; три неверных входа отклоняются; UAPI pipe отсутствует,
default routes/DNS сохраняются. Ключи случайные и не попадают в артефакты.

## Состояние и следующие действия

Это движок и его изолированная приёмка, ещё не AWG в пользовательском Windows GUI.
Следующая часть AWG: подписанный профиль/DPAPI, запуск из broker с журналом сетевых
изменений и health/recovery, включение в installer и выбор/переключение транспортов.
Затем Android AWG/TCP, после платформ — этап5 Reticulum. Внешний gateway/full-route
acceptance остаётся отдельным gate до выпуска. User-device/load тесты отложены.

Версии прежние: desktop0.2.9/source42f9d32/catalogseq8 опубликован; Linux0.2.7,
последний подтверждённый Windows0.2.7; server0.2.1, TCP component/Setup0.1.0.
Нет релиза, установки на устройства или gateway изменений. Откат локального
эксперимента — завершить owner/worker и проверить отсутствие тестового TUN/routes.
Распространение только после broker/profile/installer integration, полной приёмки,
новой версии и проверки артефактов/офлайн-подписи; существующий0.2.9 не заменять.
