# AWG 3.1: первый эксперимент и исправление первого пакета — 13.09.2026

Собран отдельный Linux engine/tools, локально исправлена воспроизводимая потеря
первого пакета при настройке S4. Виртуальный сетевой стенд прошёл12 прогонов.
Это эксперимент с локальным patch поверх upstream, не официальный исправленный
релиз Amnezia и не готовая миграция приложения. На Амстердаме остаются native WG
и Reticulum; сервер, installed desktop, release catalog и main в этой сессии не менялись.

## Версии и артефакты

- [Engine v3.1.20260828](https://github.com/amnezia-vpn/amneziawg-go/tree/b5928efb6ca19f0153958460c3d141f04abc5c2e), commit `b5928efb6ca19f0153958460c3d141f04abc5c2e`.
- [Tools v3.1.20260812](https://github.com/amnezia-vpn/amneziawg-tools/tree/ee0f0a9aa34ff0a0da4b3433b9512781cfe02843), commit `ee0f0a9aa34ff0a0da4b3433b9512781cfe02843`.
- Builder Go1.26.1/bookworm; engine module имеет суффикс `/v3`, minimum Go1.25.
- Image `family-connect-awg31:experiment1`; локальный [Dockerfile](../../pilot/awg31/Dockerfile)
  применяет явный [patch](../../pilot/awg31/patches/0001-refresh-s4-after-tun-read.patch),
  добавляет regression test, проверяет выбранные upstream packages три раза,
  затем собирает оба бинарника и включает исходные лицензии.
- amneziawg-go SHA256 `e7f00e47d6df853ade5dcd2fe79240f01ff897d75088c768316a444c27c87e0f`.
- awg SHA256 `5eb2eca206cd7e2afbe21b02b6def2347b003f3a7d4cf5e622cd56b21b6d379a`.
- Бинарники `/tmp/fc-awg31/bin`; образ и recipe позволяют повторить сборку.
  Base image tags и apt/make environment не закреплены digest: побитовая
  воспроизводимость на другом хосте пока не заявляется.

## Найденная ошибка и границы исправления

Неизменённый pinned engine дважды провалил TestAWGDevicePing: handshake проходит,
но ping/pong не доходят. Новый детерминированный тест дожидается входа в TUN Read
до IpcSet, задаёт S4=25 и также воспроизводит потерю обоих первых пакетов.
Причина: Read уже ожидал данные со старым offset/S4; после конфигурации очередь
сохраняла старую величину padding, хотя получатель ожидал новую.

Patch перечитывает S4 после возврата Read, проверяет доступное место и переносит
plaintext на актуальное смещение до постановки в очередь. Криптографические
примитивы и формат протокола не меняются. Это исправление startup interleaving;
оно не делает все настройки UAPI атомарными относительно уже летящих пакетов.
Для живой смены параметров нужен отдельный lifecycle/rollback сценарий.

[Regression test](../../pilot/awg31/regression_test.go) проверяет первый пакет в обе
стороны: WG defaults, S4, header protection, content padding, random trailers.
Все5 вариантов прошли по3 раза вместе с исходными device tests. Выбранный набор:
conn, device, ipc, ratelimiter, replay, rwcancel, tai64n, tun (с подкаталогами).
Некоторые upstream tests уже имеют Skip; они не объявляются принятыми.

Дополнительный `go test -count=1 ./...` **не прошёл полностью**: единственный failing
package outline, Test_outlineIntegration, `could not find a working fallback`.
Upstream fixture использует внешний endpoint123.123.123.123:51820 и example.com;
соответствующий gateway в нашем стенде не подготовлен. Это внешний integration
сценарий, а не доказательство поломки/приёмки Outline. Он сохранён как открытый
результат; тест не удалён и не переписан ради зелёного полного suite.

## Сетевой стенд и измерения

[lab.py](../../pilot/awg31/lab.py) запускается root внутри свежего unshare --net,
создаёт второй netns, veth и два отдельных tunnel interfaces. На каждой стороне
netem35ms/20mbit; TSO/GSO/GRO выключены, MTU1280. На AWG engine GOMAXPROCS=1,
но общей квоты1CPU для пары нет: это не симуляция процессора Amsterdam VPS.
Свежие синтетические ключи и конфиги удаляются вместе с приватным временным каталогом;
stdout содержит только метрики. Host routes/default/DNS не настраиваются.

На каждом из3 повторов каждого варианта: первый ping,10 измерительных ping,
8MiB TCP download с проверкой содержимого/размера, заключительный ping.
Порядок вариантов ротируется. Всего12 успешных прогонов,96MiB полезных данных.
Первый запуск самого harness остановился после WG: ожидал IPC в неверном каталоге;
исправлено на официальный `/var/run/amneziawg`, затем полный запуск прошёл.
Имена namespace/interface уникальны; процессы и server namespace очищены.

Общие AWG параметры: S1–S4=16, H1–H4=1,2,3,4, одинаковый новый HeaderProtectionKey
на концах. J/I поля и интервалы оставлены default, cookies не отключались.
Варианты отличаются только ContentPaddingAddition=0-32 либо RandomTrailers=on.

Медианы трёх запусков:

| Вариант | TCP, Мбит/с | RTT, мс | Байт underlay / байт payload |
|---|---:|---:|---:|
| Kernel WG |16.583|71.078|1.1644|
| AWG3.1 + startup patch |16.411|70.707|1.1599|
| AWG + padding0–32 |16.404|70.815|1.1615|
| AWG + trailers |16.406|70.819|1.2346|

Во всех120 измерительных ping потерь0%; первый и заключительный ping также успешны.
RSS **двух** AWG процессов в конце download не превышал14.59MiB в этих прогонах;
это не peak RSS, не память всей службы и не оценка многих клиентов. CPU ticks
измерены для двух процессов и сохранены в JSON; разброс не позволяет делать
сильный вывод о сравнении CPU. Kernel WG CPU/RSS этим способом не измерены.

Underlay bytes — сумма RX+TX счётчиков одного veth за окно TCP download. Она
включает TCP/IP, ACK и накладные расходы канала; это не чистый размер AWG padding.
Trailers увеличили этот показатель примерно на6.4% относительно AWG base.
Padding0–32 дал малую разницу на объёмном TCP; для коротких сообщений результат
может быть другим. Не следует трактовать небольшую разницу WG/AWG как доказанную
экономию: TCP segmentation/ACK и offload поведение различаются.

[Машиночитаемые версии, отказы и все12 измерений](2026-09-13-awg31-experiment.json).

Регрессионный набор Family Connect:478 passed,2 прежних warnings,9.89с.
Python syntax и git diff --check также прошли.

## Вывод и следующий шаг

Для первого живого AWG пилота кандидат — base с header protection и включённой
защитой cookies. Trailers пока оставить экспериментальным переключателем:
измерена цена, но нет измеренного выигрыша против DPI. Нулевые потери в коротком
стенде не закрывают TD-1 и не доказывают устойчивость к блокировкам.

Далее: отрицательные проверки несовместимого HeaderProtectionKey/профилей,
потери/MTU/reconnect/rekey и нагрузка с реальной квотой1CPU. Затем отдельный
AWG3.1 interface/порт в Амстердаме, измерения CPU/RAM/HTTPS на реальном маршруте.
Работающий WG используется как контроль и путь возврата. Подтверждений, что сейчас
нужен более мощный VPS, эти данные не дают; предел производительности ещё не измерен.

Для приложения нужна явная схема3.1, capability-aware native verifiers и runtime,
signed revision с health/ACK/rollback, Windows/Android platform acceptance.
Существующая строгая схема2.0 и прежний conformance corpus сохранены.

Rollback эксперимента: завершить harness штатно (finally удаляет процессы/interface/netns),
не использовать experimental binaries/image. На сервере и в installed app откат
не требуется, поскольку они не изменялись. SIGKILL/power loss recovery harness
отдельно не проверены; перед повтором после аварии оператор проверяет остатки
fc31lab-* namespace и соответствующих процессов, не удаляя чужие namespace.

## Сохранение и CI

Реализация86eb784, patch whitespace attributes b90e39a6de92f19cd4f03e9b881c11ab9bec4179,
ветка stage5-linux-control-preview.14 публичных файлов перенесены в основной
каталог с проверкой preimage07dd413; остальные незакоммиченные изменения сохранены.
[phase0 CI34759917018](https://github.com/Joker20380/family_connect/actions/runs/34759917018)
на b90e39a: tests103730824181 и failover103730824332 success. Этот общий workflow
не запускает новый AWG3.1 стенд: его приёмка в этой сессии локальная, с рецептами выше.
