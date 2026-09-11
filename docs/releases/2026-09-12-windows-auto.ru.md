# Windows: автоматический выбор транспорта — 2026-09-12

Выбрать в списке Auto · WG → AWG → TCP и нажать «Подключить».
Закрытие окна не останавливает цепочку: ею управляет служба.
Реализован явный режим Auto: WG → AWG → TCP, только по уже активированным профилям.
Одна попытка каждого доступного транспорта на одно нажатие Connect; работающий
нижестоящий транспорт не прерывается ради возврата к WG. После исчерпания вариантов
нужно новое нажатие Connect. Ручные WG/AWG/TCP и три повтора ручных AWG/TCP сохранены.

Служба удерживает SID на протяжении цепочки. До статуса on проверяется доступность
через выбранный интерфейс: две закреплённые HTTPS-цели, достаточно одной; до двух
проверок с интервалом 5s и дедлайном 8s. Затем обычный health monitor 15s/two failed
cycles. WG использует только fc-native и его адрес 10.77.0.N; AWG/TCP используют
свои адреса и IP_UNICAST_IF. Произвольные URL/интерфейсы не принимаются по IPC.

Смена транспорта разрешена только после очистки предыдущего. При неудачной очистке
цепочка останавливается с auto-cleanup-required и сохраняет владение/журнал.
Отмена действует во время старта, проверки и работы; завершает всю цепочку.
SCM restart очищает auto-session.json, собственный WG и TCP/AWG-журнал без
автоподключения. UI показывает Auto и фактический транспорт; импорт профиля
выполняется после выбора конкретного транспорта. Новое IPC поле Automatic необязательно.

## Приёмка

Source `1e13c74` принят. Все четыре workflow прошли:
[Client builds](https://github.com/Joker20380/family_connect/actions/runs/34654036404),
[AWG/Auto](https://github.com/Joker20380/family_connect/actions/runs/34654036463),
[TCP regression](https://github.com/Joker20380/family_connect/actions/runs/34654036431),
[phase0](https://github.com/Joker20380/family_connect/actions/runs/34654036425).
Локально 325 Python tests passed, 2 dependency warnings. C# 7 async policy-сценариев прошли: порядок, пропуск отсутствующих
профилей, потеря установленного транспорта, отмена до старта/во время старта/после
подключения, запрет следующего транспорта при неудачной очистке. GUI: 672 макета,
Auto readiness, отображение фактического транспорта и отмена WG pending.
Изолированный LocalSystem стенд: недоступная WG-служба → encrypted AWG → VLESS/TUN
TCP после остановки AWG peer; IPv4/IPv6, чужой SID, restart cleanup, исчерпание,
отмена старта и проверки связи. Ручные регрессии прошли: AWG 24/24 UDP и 4 cleanup; TCP 84/84 HTTP,14 DNS и 10 cleanup.
Нативный AWG: 12/12 UDP,4 negative probes и 4 cleanup. Auto: 6/6 UDP через AWG,
затем 6/6 HTTP через TCP; 4 сценария (fallback/restart, exhaustion, cancel, cancel-probe)
завершились точной очисткой. Default routes, DNS/NRPT совпали с исходным состоянием.
Platform CI: Windows/Linux/Android, 672 Windows layouts, установка/payload/uninstall.
Все скачанные engine hashes сверены с закреплёнными; installer SHA256:
`b4aae557757c4e5eed820fd34c0eb4696b1d38e0d354d327649188a428ddaca6`. Превью интерфейса просмотрено.
[Машинные результаты](2026-09-12-windows-auto-result.json).
Локальные артефакты: state-client-build/session-2026-09-12-windows-auto (ignored).

Тестовый SessionHost намеренно не реализует WG tunnel-service: проверяется отказ
старта настоящего SCM service, а не передача WG-пакетов. В CI AWG health использует
nonce UDP echo через TUN (memory peer не реализует HTTP); эта ветка только под
TCP_SESSION_TEST. В режиме Auto сборки installer все протоколы проверяются через production HTTPS.
Полный маршрут, внешний WG/AWG/REALITY и реальные HTTPS probes требуют отдельной
приёмки до выпуска. Изолированная проверка не доказывает устойчивость на всех сетях.

## Версии и остаток

Desktop0.2.9/source42f9d32/catalogseq8 остаётся опубликованным. Linux0.2.7 установлен,
Windows последний отчёт0.2.7; server0.2.1 и TCP Setup/component0.1.0 не меняются.
Нового релиза, установки устройств, изменений gateway/пиров/ключей нет.
Для выпуска нужны полная приёмка, новая неизменяемая версия, сверка platform assets
и офлайн-подпись каталога. Откат: Disconnect, предыдущий проверенный installer;
DPAPI-профили сохраняются. При cleanup-required не удалять журнал вручную.
Kill switch отсутствует. Физические/нагрузочные тесты и Android updater отложены.
Реализация Windows Auto принята в изолированном CI. Следующий блок — Android AWG/TCP; затем этап5 Reticulum.
